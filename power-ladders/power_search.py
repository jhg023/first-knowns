"""power_search.py -- the CPU engine for the power ladders.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is independent
in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array over
    the x line and uses no wheel at all.  The GPU engine never materialises
    the x line: it generates only the residues that survive a wheel and
    tests those against packed forbidden-residue tables, bailing out at the
    first kill.  A wheel bug on the GPU side therefore shows up as a parity
    failure rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(l,n,F) is built here by a DISCRETE
    LOGARITHM -- one primitive root g and one logarithm L = log_g(-d/c) per
    prime, after which x = g^t solves x^k == -d/c exactly when k*t == L
    (mod l - 1), a congruence in t with gcd(k, l - 1) solutions or none --
    while the oracle walks every residue and asks sympy's nthroot_mod.  G3
    pins the two against each other, and against a brute-force power walk
    on primes to 2^20 whose l - 1 is as composite as the sieve will meet.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (x, off) pairs on
the GPU -- x = base + off with base a host-side big int -- so no machine
word bounds the search (OPTIMIZATION.md 2.7, from the first commit).  x is
the engines' name for the term: m on A229626, A229630 and A229902, q on
A229627.

WHAT IS SWEPT.  The term, on ONE line per family from the frontier term up
(the ladders nest: power_reference).  The forced primes pin it to a CLASS
on two families: 1 (mod 6) on A229627 and 0 (mod 10) on A229902 (0 (mod 2)
below n = 4); A229626 and A229630 force nothing and sweep the whole line
(unit 1).  The machinery sweeps a general class x = r + u*t and this engine
marks the dense x line knowing nothing of r or u, which is what makes the
parity gate a check of the forcing as well as of the sieve.  u is DERIVED
per filter (`forced_unit`), and a unit whose primes are not all forced is
refused (`assert_unit`), because a unit is a coverage claim.

THE EXCEPTION ZONE.  A kill by l proves nothing unless the value exceeds l,
and the smallest value is the k = 1 form (q itself on A229627), so the
engines refuse to run at or below k_floor and the integers below are
classified one at a time (prefix_hits).  Every campaign's frontier is
past 10^11, far above any zone; the canaries and drills that open low meet
it (A229627's 2 and 3, A229902's 10).

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24, and the values here are POWERS of the term: the
k = n value is c*x^n + d, so the PROOF CROSSING k_proof(n, F) is
((3.317e24 - d)/c)^(1/n) -- 259 at n = 10 -- and every classification a
campaign makes is a thirteen-base strong probable-prime chain, which can
only lengthen a run, never hide one.  A discovery is proved by
CERTIFICATE, and these are rule 5h's best case: every value is
multiplier x term^k +- 1, so N + 1 = 2*m^k (BLS75 Theorem 15) on the three
2*m^k - 1 ladders and N - 1 = 19*m^k (Theorem 1) on A229902 are COMPLETELY
factored by ONE factorization of the term, at any height and for any k.
The ceiling on the term is huntlib's K_CEIL = 1e40.  What ends a family is
the GPU tail's residue list, which must hold every residue one prime can
kill -- n(n+1)/2 by the proved bound -- through n_max.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, every family, in x space and in class space, and == a brute
power walk on large primes; a unit that is not forced -- or not squarefree
-- is refused), G4 (CPU survivors == the oracle's definition of a survivor
on populated windows), G5 (the CPU engine finds published terms of every
family end-to-end as FIRST occurrences from the frontier term, inclusive),
G6 (engine run lengths == sympy BPSW, the domain predicates included), G10
(numeric hygiene: the crossing tight to one x at every index, the ceiling
from huntlib, the last index the engine can express), G24a (the theorems
the GPU's semiprime wheel rests on: above SEMI_FLOOR a semiprime has at
most one prime factor up to 89, and above SEMI_TOP * q2 one with a factor
up to 89 has no other up to q2, on every semiprime to 2e5).
"""

import math
import pathlib as _pathlib
import sys as _sys
from functools import lru_cache as _lru_cache

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling as _ceiling                        # noqa: E402
from huntlib import certificate as _certificate                # noqa: E402
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from power_reference import (FAMILIES, FOUND, KNOWN, coeffs,    # noqa: E402
                             domain, family, floor_x,
                             forbidden_k_residues, forms, frontier,
                             in_domain, maxkills, nforms,
                             run_length as oracle_run_length, w, w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing search runs over (the log and the documents
# name the forced class; nothing in the engines depends on it).
UNIT_UPTO = 64

# THE CEILING ON THE TERM: huntlib's, MEASURED for this project's shape (the
# launcher's certificate drill proves values of a term at 1e40 on both
# routes).  EXCLUSIVE.
K_CEIL = _ceiling.K_CEIL

# THE LAST FILTER THE ENGINE CAN EXPRESS.  The GPU tail keeps the killed
# residues of each prime in a list of at most power_gpu.NRES_MAX slots, and
# a prime can kill up to maxkills(F, n) = n(n+1)/2 (+1) of them, so the last
# index is the largest n whose proved bound fits (G10 pins the constants to
# each other).  The engine sizes its list from the primes it actually holds
# (power_gpu), so the bound is the guarantee and not the cost.
NRES_MAX = 128


def n_max(fam):
    """The largest index n whose proved kill bound fits NRES_MAX: the last
    filter the engine can express, and where that family's campaign ends."""
    fam = family(fam)
    n = 1
    while maxkills(fam, n + 1) <= NRES_MAX:
        n += 1
    return n


def iroot(v, k):
    """floor(v^(1/k)) for v >= 0, exactly."""
    v, k = int(v), int(k)
    if v < 2:
        return v
    x = int(round(v ** (1.0 / k))) if v < 1 << 1000 else 1 << (v.bit_length() // k)
    while x ** k > v:
        x -= 1
    while (x + 1) ** k <= v:
        x += 1
    return x


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof at index n: the least x
    whose largest value c*x^n + d reaches the deterministic Miller-Rabin
    bound.  EXCLUSIVE: k_proof - 1 is the largest x whose every value stays
    under it (G10 pins both halves)."""
    c, d = coeffs(fam)
    n = max(int(n), 1)
    return iroot((MR_VALID_BELOW - 1 - d) // c, n) + 1


def k_ceil(n, fam):
    """The enforced ceiling on the term, every family: K_CEIL.  EXCLUSIVE."""
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2, n, fam):
    """The largest x the engines will NOT sweep (EXCLUSIVE floor).

    A kill by l is only a proof of compositeness when the value EXCEEDS l.
    The smallest value at x >= 1 is the k = 1 form c*x + d -- or x itself
    on A229627, where the term is a form and 2x - 1 >= x -- so a sieve to
    q2 is valid from the first x with that value above q2.

    On A229630 the floor is also at least SEMI_FLOOR, where the GPU
    engine's semiprime wheel becomes a theorem (`semi_wheel_ok`), and at
    least SEMI_TOP * q2, where its cofactor sieve does (`semi_cofactor_ok`);
    the integers below it are the exception zone like any others.
    """
    fam = family(fam)
    int(n)
    if domain(fam) == "prime":
        return int(q2)
    c, d = coeffs(fam)
    floor = (int(q2) - d) // c
    if domain(fam) == "semiprime":
        floor = max(floor, SEMI_FLOOR, SEMI_TOP * int(q2))
    return floor


# THE SEMIPRIME DOMAIN, AS A CONDITION ON RESIDUES (A229630, round 5).  An m
# with exactly two prime factors that is divisible by two distinct primes
# p < q, or by p^2, IS that product -- so above the largest such product of
# the primes a wheel may hold, a semiprime has at most ONE prime factor
# among them, and the GPU engine enumerates only the residue classes that
# say so (power_gpu.SemiprimeEngine).  The wheel's primes are bounded by
# power_gpu.WHEEL_TOP = 89, and 89^2 = 7921 bounds every product of two of
# them (the tightest is 83*89 = 7387; a square p^2 has one zero mod p and is
# kept anyway).  Necessary, never sufficient: the host still decides the
# domain exactly (is_semiprime_fast).  G24a checks the theorem on every
# semiprime to 2e5 and that the floor is needed.
SEMI_FLOOR = 89 * 89
# THE COFACTOR SIEVE (round 6).  A semiprime m with a wheel prime p dividing
# it is p*r' with r' PRIME, so above p*q2 no other prime up to q2 divides it
# either: in the classes with a wheel zero, residue 0 of every sieve prime
# is a kill too (power_gpu.engine_kills).  The products it must clear are
# bounded by SEMI_TOP * q2, SEMI_TOP the largest prime a wheel may hold.
SEMI_TOP = 89


def semi_wheel_ok(x, primes):
    """At most one of `primes` divides x -- what every semiprime x above
    SEMI_FLOOR satisfies for any set of primes up to 89.  Plain `%`: this is
    the CPU side of the parity gate on the GPU's semiprime wheel."""
    x = int(x)
    hits = 0
    for q in primes:
        if x % int(q) == 0:
            hits += 1
            if hits > 1:
                return False
    return True


@_lru_cache(maxsize=None)
def _cofactor_primes(wheel, q2, n, fam):
    return tuple(q for q in primerange(2, int(q2) + 1)
                 if q not in wheel and killed_residues(q, n, fam))


def semi_cofactor_ok(x, wheel, q2, n, fam):
    """When one of the `wheel` primes divides x, no sieve prime does -- the
    primes up to q2 outside the wheel that kill something at index n, the
    set the GPU engine sieves with.  What every semiprime x above
    SEMI_TOP * q2 satisfies: x = p*r' with r' a prime past q2.  Plain `%`:
    the CPU side of the parity gate on the GPU's cofactor sieve."""
    x = int(x)
    ws = frozenset(int(q) for q in wheel)
    if all(x % q for q in ws):
        return True
    return all(x % q for q in _cofactor_primes(ws, int(q2), int(n),
                                                 family(fam)))


def zone(q2, n, fam):
    """(lo, hi) INCLUSIVE: the integers between the definition's floor and
    the engine's that a sweep at depth q2 must cover by brute force."""
    lo, hi = floor_x(fam, n), k_floor(q2, n, fam)
    return (lo, hi) if lo <= hi else None


# ------------------------------------------------- the killed set, by dlog

_SPF = np.zeros(1, dtype=np.int32)


def _spf_upto(m):
    """The smallest-prime-factor table, grown to cover m."""
    global _SPF
    if _SPF.size > m:
        return _SPF
    lim = max(int(m) + 1, 2 * _SPF.size, 1 << 16)
    spf = np.zeros(lim, dtype=np.int32)
    for p in range(2, math.isqrt(lim - 1) + 1):
        if spf[p] == 0:
            blk = spf[p * p::p]
            blk[blk == 0] = p
    _SPF = spf
    return _SPF


def _factor_small(m):
    """{p: e} for a positive m inside the table."""
    spf = _spf_upto(m)
    out = {}
    while m > 1:
        p = int(spf[m]) or m
        out[p] = out.get(p, 0) + 1
        m //= p
    return out


@_lru_cache(maxsize=None)
def _proot(q):
    """(g, {p: e} of q - 1): the least primitive root mod the prime q."""
    fac = _factor_small(q - 1)
    if q == 2:
        return 1, fac
    g = 2
    while any(pow(g, (q - 1) // p, q) == 1 for p in fac):
        g += 1
    return g, fac


def _dlog(q, a):
    """log_g(a) mod q - 1 for the primitive root g = _proot(q)[0], by
    Pohlig-Hellman with a baby-step giant-step in each prime-order
    subgroup.  a must be a unit mod q."""
    g, fac = _proot(q)
    n = q - 1
    if n == 1:
        return 0
    X, M = 0, 1
    for p, e in fac.items():
        pe = p ** e
        gp = pow(g, n // pe, q)            # order p^e
        ap = pow(a, n // pe, q)
        gam = pow(gp, pe // p, q)          # order p
        x = 0
        for i in range(e):
            h = pow(ap * pow(gp, -x, q) % q, pe // p ** (i + 1), q)
            s = math.isqrt(p) + 1
            baby, cur = {}, 1
            for j in range(s):
                baby.setdefault(cur, j)
                cur = cur * gam % q
            giant, cur, dig = pow(gam, -s, q), h, None
            for i2 in range(s + 1):
                if cur in baby:
                    dig = i2 * s + baby[cur]
                    break
                cur = cur * giant % q
            if dig is None:
                raise ArithmeticError(f"no discrete log of {a} mod {q}")
            x += dig * p ** i
        X += M * (((x % pe) - X) * pow(M, -1, pe) % pe)
        M *= pe
    return X % M


@_lru_cache(maxsize=None)
def _log_target(q, fam):
    """L = log_g(-d/c) mod q - 1, or None when q divides c (no power form
    vanishes mod q).  Shared by every index: only the exponents change."""
    c, d = coeffs(fam)
    if c % q == 0:
        return None
    a = (-d) * pow(c, -1, q) % q
    return _dlog(q, a)


@_lru_cache(maxsize=None)
def _exponents(q, n, fam):
    """T = { t in Z/(q - 1) : k*t == L for some k = 1..n } -- the logs of
    the power forms' roots, so that K = { g^t : t in T } (+ {0})."""
    L = _log_target(q, fam)
    if L is None:
        return frozenset()
    m = q - 1
    T = set()
    for k in range(1, n + 1):
        G = math.gcd(k, m)
        if L % G:
            continue
        h = m // G
        t0 = (L // G) * pow(k // G, -1, h) % h if h > 1 else 0
        T.update(t0 + j * h for j in range(G))
    return frozenset(T)


@_lru_cache(maxsize=None)
def _xkills(q, n, fam):
    g, _fac = _proot(q)
    out = {pow(g, t, q) for t in _exponents(q, n, fam)}
    if domain(fam) == "prime":
        out.add(0)
    return frozenset(out)


def w_fast(q, n, fam):
    """|K(q,n,F)| without building the residues: |T| (the map t -> g^t is a
    bijection of Z/(q - 1) onto the units), plus the form q's zero."""
    q, n, fam = int(q), int(n), family(fam)
    return len(_exponents(q, n, fam)) + (1 if domain(fam) == "prime" else 0)


def killed_residues(q, n, fam, unit=1):
    """K(q,n,F): the residues of x that some form of index n makes
    divisible by q, by the discrete logarithm (module docstring).

    CLASS SPACE.  The forced primes pin x to ONE class, x == r (mod unit)
    (`unit_residue`), so the GPU engine sweeps t with x = r + unit*t, and
    the residues of t that q kills are those of x carried through the map:
    t == (k - r) * unit^-1 (mod q) for each killed k, q not dividing unit.
    A prime OF the unit kills no t at all -- the class was chosen so that
    it cannot -- and returns the empty list.  The map is a bijection of
    Z/q, so the sizes, hence the survival curve and the wheel counts, are
    unchanged (G3 pins this against the x-space set).
    """
    unit = int(unit)
    if unit % q == 0:
        return []
    ks = _xkills(int(q), int(n), family(fam))
    if unit == 1:
        return sorted(ks)
    r, inv = unit_residue(n, fam, unit), pow(unit, -1, q)
    return sorted({((k - r) * inv) % q for k in ks})


def _free(q, n, fam):
    """The residues of x mod q that no form kills."""
    return sorted(set(range(q)) - _xkills(int(q), int(n), family(fam)))


def forced_unit(n, fam, upto=UNIT_UPTO):
    """The product of the primes FORCED at index n -- those q that leave x
    exactly one residue class: 6 on A229627, 2 then 10 (from n = 4) on
    A229902, 1 on A229626 and A229630.  Derived per filter and never
    stored: a unit is a coverage claim."""
    u = 1
    for q in primerange(2, upto):
        if len(_free(q, n, fam)) == 1:
            u *= q
    return u


def unit_residue(n, fam, unit):
    """r with x == r (mod unit) for every x that survives the primes of
    `unit` -- the CRT of their single free classes.  0 <= r < unit."""
    return _unit_residue(int(n), family(fam), int(unit))


@_lru_cache(maxsize=None)
def _unit_residue(n, fam, unit):
    unit = assert_unit(n, fam, unit)
    r, m = 0, 1
    for q in primerange(2, UNIT_UPTO):
        if unit % q == 0:
            a = _free(q, n, fam)[0]
            r, m = r + m * (((a - r) * pow(m, -1, q)) % q), m * q
    return r


def forced_class(n, fam, upto=UNIT_UPTO):
    """(r, u): the class x == r (mod u) the forced primes pin x to."""
    u = forced_unit(n, fam, upto)
    return unit_residue(n, fam, u), u


def assert_unit(n, fam, unit):
    """Raise unless `unit` is SQUAREFREE and every prime factor of it is
    forced at index n.

    A unit that is not forced is a COVERAGE bug, not an inefficiency: an
    engine sweeping x = r + unit*t never looks at the other classes, and if
    a prime of the unit leaves two classes free it has silently dropped one
    of them.  So the check is against the definition -- exactly one free
    class per prime of the unit -- and it raises.
    """
    fam = family(fam)
    unit = int(unit)
    if unit < 1:
        raise ValueError(f"unit {unit} is not a positive integer")
    for q in primerange(2, UNIT_UPTO):
        if unit % q == 0 and len(_free(q, n, fam)) != 1:
            raise ValueError(
                f"unit {unit} is not admissible at index {n} of {fam}: {q} "
                f"leaves {len(_free(q, n, fam))} residue classes free there, "
                f"not 1, so an engine sweeping x = r + {unit}*t would skip "
                f"line it claims to cover; the largest admissible unit here "
                f"is {forced_unit(n, fam)}")
        if unit % (q * q) == 0:
            raise ValueError(
                f"unit {unit} is not squarefree: forcing pins x mod {q}, "
                f"never mod {q * q}")
    rest = unit
    for q in primerange(2, UNIT_UPTO):
        while rest % q == 0:
            rest //= q
    if rest != 1:
        raise ValueError(f"unit {unit} has a prime factor above {UNIT_UPTO}, "
                         f"which nothing forces")
    return unit


# ------------------------------------------------------------- classify

# Trial division settles semiprimality outright below (2^17)^3: a composite
# with no prime factor up to the cube root has exactly two.
_SEMI_CUBE = (1 << 17) ** 3


def is_semiprime_fast(x):
    """x is a product of exactly two primes -- decided EXACTLY: huntlib's
    bounded split first (trial division to 2^17, rho, a few ECM curves);
    then, if nothing split, a composite under (2^17)^3 is a semiprime by
    the cube-root argument, and anything else goes to sympy's factorint
    (the one unbounded call, reached only by a value at or past the census
    floor whose term is a hard composite above 2.25e15)."""
    x = int(x)
    if x < 4 or mr_is_prime(x):
        return False
    fac, R = _certificate.factor_partial(x)
    omega = sum(fac.values())
    if R == 1:
        return omega == 2
    if omega >= 1:
        return False                 # a found prime times a composite R
    if x < _SEMI_CUBE:
        return True
    from sympy import factorint
    return sum(int(e) for e in factorint(x).values()) == 2


def in_domain_fast(fam, x):
    """The domain predicate with huntlib's tools."""
    x, dom = int(x), domain(fam)
    if dom == "prime":
        return x >= 2 and mr_is_prime(x)
    if dom == "semiprime":
        return is_semiprime_fast(x)
    return x >= 1


def run_length_fast(fam, x, cap=64):
    """The oracle's run_length with huntlib's Miller-Rabin (a strong
    probable-prime chain past the proof crossing), the powers built
    incrementally."""
    fam, x = family(fam), int(x)
    if not in_domain_fast(fam, x):
        return 0
    c, d = coeffs(fam)
    r, pw = 0, x
    while r < cap:
        v = c * pw + d
        if v < 2 or not mr_is_prime(v):
            break
        r += 1
        pw *= x
    return r


def fermat2(N):
    """2^(N-1) == 1 (mod N) for odd N > 2; N == 2 passes, everything else
    fails -- the device Fermat stage's test, in Python ints (G23)."""
    N = int(N)
    if N < 3 or N % 2 == 0:
        return N == 2
    return pow(2, N - 1, N) == 1


def fermat_lead(fam, x, T):
    """True when x's leading forms all pass fermat2: x itself on A229627,
    then c*x^k + d for k = 1..T.  What the device Fermat stage emits, and
    a superset of every x whose leading T forms are prime (a failed Fermat
    test is a proof of compositeness)."""
    fam, x = family(fam), int(x)
    if domain(fam) == "prime" and not fermat2(x):
        return False
    c, d = coeffs(fam)
    pw = x
    for _ in range(int(T)):
        if not fermat2(c * pw + d):
            return False
        pw *= x
    return True


def prefix_hits(fam, n, q2, floor=1, cap=64):
    """[(x, run)] over the exception zone of index n at depth q2 -- every
    integer between the definition's floor and the engine's with a run of
    at least `floor` -- by huntlib's chain (the oracle's own prefix_hits is
    the sympy version).  The walk is the forced class PLUS the forced
    primes themselves: A229627's 2 and 3 are primes outside the class 1
    (mod 6) that the form q forces, and both are terms."""
    fam = family(fam)
    z = zone(q2, n, fam)
    if z is None:
        return []
    lo, hi = z
    r0, u = forced_class(n, fam)
    out = []
    seen = set()
    for x in sorted(q for q in primerange(2, UNIT_UPTO) if u % q == 0 and lo <= q <= hi):
        r = run_length_fast(fam, x, cap=cap)
        seen.add(x)
        if r >= floor:
            out.append((x, r))
    x = lo + ((r0 - lo) % u)
    while x <= hi:
        if x not in seen:
            r = run_length_fast(fam, x, cap=cap)
            if r >= floor:
                out.append((x, r))
        x += u
    return sorted(out)


class CpuEngine:
    """Segmented sieve over the dense x line, no wheel."""

    def __init__(self, n, fam, q2=Q2_DEFAULT):
        self.n = int(n)
        self.fam = family(fam)
        self.q2 = q2
        self.primes = list(primerange(2, q2 + 1))
        self.table = {q: killed_residues(q, n, self.fam) for q in self.primes}
        self.marks_per_k = sum(len(v) / q for q, v in self.table.items())

    # ---------------------------------------------------------------- sieve
    def survivors(self, k_lo, k_hi, block=1 << 22):
        """Yield lists of the x in [k_lo, k_hi) that no prime q <= q2 kills.

        The bounds are checked EAGERLY, here, and the generator is a separate
        function -- a `yield` anywhere in this body would defer every check
        to the first `next()`.
        """
        if k_hi > k_ceil(self.n, self.fam):
            raise ValueError(f"x {k_hi} past the enforced ceiling "
                             f"{k_ceil(self.n, self.fam)}")
        if k_lo <= k_floor(self.q2, self.n, self.fam):
            raise ValueError(
                f"engines refuse to run at or below "
                f"{k_floor(self.q2, self.n, self.fam)}: a kill by q <= q2 = "
                f"{self.q2} is only a proof of compositeness once the value "
                f"exceeds q, and the smallest value is the k = 1 form")
        return self._survivors(k_lo, k_hi, block)

    def _survivors(self, k_lo, k_hi, block):
        k0 = int(k_lo)
        while k0 < k_hi:
            k1 = min(k0 + block, int(k_hi))
            alive = np.ones(k1 - k0, dtype=bool)
            for q in self.primes:
                for u in self.table[q]:
                    first = (u - k0) % q
                    if first < alive.size:
                        alive[first::q] = False
            idx = np.nonzero(alive)[0]
            if idx.size:
                # Python ints, not u64: this engine is the parity reference
                # for a range that runs past 2^64.
                yield [k0 + int(i) for i in idx]
            k0 = k1

    def survives(self, k):
        """The same decision, one candidate at a time, in Python ints."""
        k = int(k)
        return all(k % q not in st for q, st in self._sets().items())

    def _sets(self):
        if not hasattr(self, "_frozen"):
            self._frozen = {q: frozenset(v) for q, v in self.table.items()}
        return self._frozen

    # ------------------------------------------------------------ classify
    def run_length(self, k, cap=None):
        """The run of x = k (power_reference.run_length, with huntlib's
        chain): 0 outside the domain, else the leading k whose value is
        prime."""
        cap = self.n + 6 if cap is None else int(cap)
        return run_length_fast(self.fam, k, cap=cap)

    def hunt(self, k_lo, k_hi, cap=None):
        """[(x, run)] for every survivor whose run reaches the filter's."""
        out = []
        for chunk in self.survivors(k_lo, k_hi):
            for k in chunk:
                r = self.run_length(int(k), cap=cap)
                if r >= self.n:
                    out.append((int(k), r))
        return out


# --------------------------------- gates -----------------------------------

def _filters(fam):
    """A spread of filters, always including the open one."""
    top = frontier(fam) + 1
    return sorted({1, 3, 4, 5, 8, top - 1, top, top + 2})


# Primes in (4096, 2^20] that G3 checks against a brute-force power walk:
# q - 1 a multiple of lcm(1..12) = 27720, where every k-th root that can
# exist does (55441, 110881, 332641, 748441, 1025641), and a spread of
# ordinary ones.  G3 checks that each is prime.
G3_BIG = (4099, 9241, 55441, 65537, 110881, 131071, 332641, 524287, 748441,
          1025641, 1048573)


def _brute_kills(q, n, fam):
    """K(q,n,F) by a vectorised power walk over every residue (G3's
    large-prime leg): x^k for k = 1..n, compared with -d/c."""
    c, d = coeffs(fam)
    x = np.arange(q, dtype=np.int64)
    dead = np.zeros(q, dtype=bool)
    if c % q:
        a = (-d) * pow(c, -1, q) % q
        cur = np.ones(q, dtype=np.int64)
        for _ in range(n):
            cur = cur * x % q
            dead |= cur == a
    if domain(fam) == "prime":
        dead[0] = True
    return set(np.nonzero(dead)[0].tolist())


def g3_table_matches_divisibility():
    """The constructed killed set must equal direct divisibility, BOTH ways,
    for every family; the discrete-log construction must equal a brute
    power walk on large primes; and every unit but the forced one is
    refused."""
    checked = 0
    for fam in FAMILIES:
        for n in _filters(fam):
            fs = forms(fam, n)
            for q in primerange(2, 300):
                built = set(killed_residues(q, n, fam))
                direct = set(forbidden_k_residues(q, n, fam))
                if built != direct:
                    return False, (f"G3 FAIL: {fam} n={n} q={q} "
                                   f"built={sorted(built)} direct={sorted(direct)}")
                if (len(built) != w_count(q, n, fam) or len(built) != w(q, n, fam)
                        or len(built) != w_fast(q, n, fam)):
                    return False, f"G3 FAIL: {fam} n={n} q={q}: |K| disagrees"
                for u in built:                 # and the kill is a real kill
                    if not any((a * pow(u, e, q) + b) % q == 0
                               for a, b, e in fs):
                        return False, (f"G3 FAIL: {fam} n={n} q={q} residue "
                                       f"{u} kills nothing")
                checked += 1
    big = 0
    most = (0, 0, 0)
    if not all(mr_is_prime(q) for q in G3_BIG):
        return False, "G3 FAIL: a large test modulus is not prime"
    for fam in FAMILIES:
        for n in (frontier(fam) + 1, 14):
            for q in G3_BIG:
                built = set(killed_residues(q, n, fam))
                brute = _brute_kills(q, n, fam)
                if built != brute or w_fast(q, n, fam) != len(brute):
                    return False, (f"G3 FAIL: {fam} n={n} q={q}: the discrete-"
                                   f"log construction holds {len(built)} "
                                   f"residues, the power walk {len(brute)}")
                most = max(most, (len(built), q, n))
                big += 1
    # CLASS SPACE: the t residues q kills, mapped back through
    # x = r + unit*t, must be exactly the x residues q kills -- both
    # directions, same size; a prime of the unit kills no t at all; and the
    # class is what the ORACLE says survives.
    cls, classes = 0, {}
    for fam in FAMILIES:
        for n in _filters(fam):
            unit = forced_unit(n, fam)
            r = unit_residue(n, fam, unit)
            classes.setdefault(fam, set()).add((r, unit))
            free = [x for x in range(unit) if all(
                x % q not in forbidden_k_residues(q, n, fam)
                for q in primerange(2, UNIT_UPTO) if unit % q == 0)]
            if free != [r]:
                return False, (f"G3 FAIL: {fam} n={n}: the oracle leaves the "
                               f"classes {free} mod {unit} free, the engine "
                               f"sweeps {r}")
            for q in primerange(2, 300):
                kt = killed_residues(q, n, fam, unit)
                direct = set(forbidden_k_residues(q, n, fam))
                if unit % q == 0:
                    if kt:
                        return False, (f"G3 FAIL: {fam} n={n}: q={q} divides "
                                       f"the unit but kills {kt}")
                    continue
                back = {(r + unit * t) % q for t in kt}
                if back != direct or len(kt) != len(direct):
                    return False, (f"G3 FAIL: {fam} n={n} unit {unit} q={q}: "
                                   f"class-space kills map to {sorted(back)}, "
                                   f"x-space kills are {sorted(direct)}")
                cls += 1
    want = {"A229626": {(0, 1)}, "A229630": {(0, 1)},
            "A229627": {(1, 6)}, "A229902": {(0, 2), (0, 10)}}
    if classes != want:
        return False, f"G3 FAIL: the forced classes are {classes}, expected {want}"
    refused = 0
    for fam in FAMILIES:
        n = frontier(fam) + 1
        u = forced_unit(n, fam)
        for unit in (7, 3 * u if u % 3 else 7 * u, 4, 2 * u, 30030, 67):
            try:
                assert_unit(n, fam, unit)
                return False, f"G3 FAIL: unit {unit} accepted for {fam} n={n}"
            except ValueError:
                refused += 1
    opens = "; ".join("%s x == %d (mod %d)" % ((fam,) + forced_class(frontier(fam) + 1, fam))
                      for fam in FAMILIES)
    return True, (f"G3 ok: the discrete-log K(q,n,F) == direct divisibility in "
                  f"both directions at all {checked} (q < 300, n, F), with |K| "
                  f"equal to the walk's, nthroot_mod's and the exponent "
                  f"count's; == a brute power walk at {big} (q, n, F) on "
                  f"primes to 2^20, five with q - 1 a multiple of lcm(1..12) "
                  f"(the most: {most[0]} residues at q = {most[1]}, n = "
                  f"{most[2]}); in class space ({cls} cases) the t kills map "
                  f"back exactly through x = r + unit*t, the unit's own "
                  f"primes kill nothing, and r is the one class the oracle "
                  f"leaves free -- {opens} at the open indices; {refused} "
                  f"inadmissible units refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, every family,
    from n = 4 to each open index."""
    checks = 0
    windows = []
    for fam in FAMILIES:
        top = frontier(fam) + 1
        windows += [(fam, 4, 128, 70_000, 400_000),
                    (fam, 7, 64, 2_000_000, 2_000_000),
                    (fam, top, 32, 5 * 10 ** 12, 2_000_000)]
    for fam, n, q2, k_lo, span in windows:
        eng = CpuEngine(n, fam, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        fs = forms(fam, n)
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            hi = min(c0 + (1 << 22), k_lo + span)
            idx = np.arange(0, hi - c0, dtype=np.int64)
            ok = np.ones(idx.size, dtype=bool)
            for q in smalls:
                r = (c0 % q + idx) % q
                pw = {0: np.ones(idx.size, dtype=np.int64)}
                for a, b, e in sorted(fs, key=lambda f: f[2]):
                    for k in range(max(pw) + 1, e + 1):   # r^e, one multiply
                        pw[k] = pw[k - 1] * r % q          # per new exponent
                    ok &= (a % q * pw[e] + b) % q != 0
            want.update(c0 + int(i) for i in idx[ok].tolist())
        if got != want:
            bad = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: {fam} n={n} window {k_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {bad}")
        if not want:
            return False, f"G4 FAIL: {fam} n={n} window is empty -- vacuous"
        checks += len(want)
    return True, (f"G4 ok: engine survivors == the definition's (every value "
                  f"of every form tested for divisibility) on {len(windows)} "
                  f"populated windows ({checks} survivors; every family, from "
                  f"n = 4 to each open index, at 5e12)")


# Published terms a dense CPU sweep from the frontier term affords in a gate:
# A229626's a(7) (4.4e6 of line above a(6)), A229627's a(5) (2.9e5 above
# a(4)), A229902's a(6) (4.2e7 above a(5)).  A229630's a(6) is 1.2e8 of line
# from a(5) = 6, which the GPU canaries take.
G5_TERMS = {"A229626": (7,), "A229627": (5,), "A229902": (6,)}


def g5_rederive_knowns():
    """The CPU engine finds published terms of EVERY family end-to-end, and
    FIRST: the sweep starts AT the frontier term (the ladders nest, so
    a(n) >= a(n - 1)), with any exception zone above it covered by brute
    force, so the claim is about the line and not about a window."""
    found = []
    for fam, ns in G5_TERMS.items():
        for n in ns:
            q2 = 1024
            eng = CpuEngine(n, fam, q2=q2)
            target = KNOWN[fam][n]
            lo = max(KNOWN[fam][n - 1], floor_x(fam, n))
            pre = [x for x, r in prefix_hits(fam, n, q2, floor=n) if x >= lo]
            if pre and min(pre) < target:
                return False, (f"G5 FAIL: {fam}: the exception zone holds "
                               f"{min(pre)} below a({n}) = {target}")
            start = max(lo, k_floor(q2, n, fam) + 1)
            hits = eng.hunt(start, target + 1)
            if not hits or min(k for k, _ in hits) != target:
                return False, (f"G5 FAIL: {fam} least run-{n} from {lo} "
                               f"came out {min(hits)[0] if hits else None}, "
                               f"expected {target}")
            found.append(f"{fam} a({n})")
    return True, ("G5 ok: CPU engine re-derived " + ", ".join(found) +
                  " end-to-end as FIRST occurrences from the frontier term "
                  "(inclusive), each at its OEIS index")


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW on real candidates, the
    domain predicates included: a composite q reads 0 on A229627, a
    non-semiprime m reads 0 on A229630, and every published term reads at
    least its index in both."""
    seen = 0
    for fam in FAMILIES:
        top = frontier(fam)
        xs = [1, 2, 3, 4, 6, 9, 10, 15, 21, 25, 2913, 12345679, 10 ** 12 + 39,
              KNOWN[fam][top], KNOWN[fam][top] + 6, KNOWN[fam][top] - 6,
              KNOWN[fam][min(top, 7)], 2 ** 64 + 13, 10 ** 15 + 37]
        eng = CpuEngine(top + 1, fam, q2=2048)
        for k in xs:
            a = eng.run_length(k, cap=top + 3)
            b = oracle_run_length(fam, k, cap=top + 3)
            if a != b:
                return False, (f"G6 FAIL: {fam} x={k} engine run {a} != "
                               f"oracle run {b}")
            if a > 0 and not in_domain(fam, k):
                return False, f"G6 FAIL: {fam} x={k}: a run outside the domain"
            seen += 1
        for n in sorted(KNOWN[fam]):
            x = KNOWN[fam][n]
            if eng.run_length(x, cap=n + 2) < n or oracle_run_length(fam, x, cap=n + 2) < n:
                return False, (f"G6 FAIL: {fam} a({n}) does not read at least "
                               f"run {n} in both implementations")
            seen += 2
    # the domains, in the entries' own words: 6 = 2*3 has run 5 on A229630
    # (its %e line); 4 is the semiprime a(1..3) = 4; 8 = 2^3 reads 0 there
    # however its powers behave; on A229627 a composite reads 0
    if (run_length_fast("A229630", 6) != 5 or run_length_fast("A229630", 4) != 3
            or run_length_fast("A229630", 8) != 0
            or run_length_fast("A229627", 9) != 0
            or run_length_fast("A229627", 3) != 3
            or not is_semiprime_fast(6) or not is_semiprime_fast(49)
            or is_semiprime_fast(30) or is_semiprime_fast(97)):
        return False, "G6 FAIL: the small cases or the semiprime test read wrong"
    # the semiprime test on its three branches: split, cube-root, factorint
    hard = 1000000007 * 1000000009                 # no small factor, < 2.25e15
    harder = 10000000019 * 10000000033             # past the cube-root bound
    if not (is_semiprime_fast(hard) and is_semiprime_fast(harder)
            and not is_semiprime_fast(hard * 3) and not is_semiprime_fast(1000000007 ** 3)):
        return False, "G6 FAIL: the semiprime test is wrong on a hard case"
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates across every family (2^64 + 13 and 10^15 + 37 "
                  f"among them, values past 10^150), every published term "
                  f"reads at least its index uncapped, the entries' own "
                  f"example reads as it says (6 has run 5 on A229630), and the "
                  f"semiprime test is exact on all three of its branches "
                  f"(split, cube root, factorint) and on cubes and triples")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: the proof crossing tight to one x per (n, F), the
    ceiling huntlib's K_CEIL and above every crossing, and the last filter
    the engine can express tight to its residue list (module docstring)."""
    import power_gpu as _gpu
    if _gpu.NRES_MAX != NRES_MAX:
        return False, (f"G10 FAIL: NRES_MAX = {NRES_MAX} here but the GPU tail "
                       f"holds {_gpu.NRES_MAX} residues a prime")
    for fam in FAMILIES:
        for n in range(1, frontier(fam) + 12):
            c = k_proof(n, fam)
            vs = lambda x: [v for v in (c0 * x ** e + d0 for c0, d0, e in forms(fam, n))]  # noqa: E731
            if max(vs(c - 1)) >= MR_VALID_BELOW:
                return False, (f"G10 FAIL: the largest deterministic x for "
                               f"({n}, {fam}) leaves the deterministic MR zone")
            if max(vs(c)) < MR_VALID_BELOW:
                return False, (f"G10 FAIL: the proof crossing for ({n}, {fam}) "
                               f"is not tight: x = {c} is still deterministic")
            top = k_ceil(n, fam)
            if top != _ceiling.K_CEIL or top <= c:
                return False, f"G10 FAIL: the {fam} ceiling at n = {n} is {top}"
        if any(K_CEIL <= x for x in FOUND[fam].values()):
            return False, f"G10 FAIL: a {fam} find sits at or above the ceiling"
        nm = n_max(fam)
        if not maxkills(fam, nm) <= NRES_MAX < maxkills(fam, nm + 1):
            return False, f"G10 FAIL: {fam}'s last expressible index is not {nm}"
        if nm <= frontier(fam) + 3:
            return False, f"G10 FAIL: {fam} has too few open indices the engine can express"
    rows = "; ".join("%s n = %d: crossing %s = %d, last index %d"
                     % (f, frontier(f) + 1, FAMILIES[f]["term"],
                        k_proof(frontier(f) + 1, f), n_max(f))
                     for f in FAMILIES)
    return True, ("G10 ok: the proof crossing is where c*x^n + d reaches "
                  "the deterministic MR bound (3.317e24), tight to one x at "
                  f"every index to the frontier + 11 of every family ({rows}: "
                  "every campaign classifies past it, and every discovery is "
                  "proved by certificate); the ceiling on the term is huntlib's "
                  "K_CEIL = %.4g on every family; and the last filter is the "
                  "one whose proved kill bound n(n+1)/2 fills the GPU tail's "
                  "residue list (NRES_MAX = %d), tight to one index"
                  % (K_CEIL, NRES_MAX))


def g24a_semiprime_wheel_theorem():
    """The theorem the GPU's semiprime wheel rests on (SEMI_FLOOR): every
    semiprime above the floor has at most one prime factor up to 89, on
    every semiprime to 2e5 (factored here by the smallest-prime-factor
    table, not by sympy); the floor is needed (83*89 is a semiprime below
    it with two); and on A229630 the engines' floor is never under it while
    the other families' floors are untouched."""
    import power_gpu as _gpu
    if _gpu.WHEEL_TOP ** 2 > SEMI_FLOOR:
        return False, (f"G24a FAIL: a wheel may hold primes to "
                       f"{_gpu.WHEEL_TOP}, whose square passes SEMI_FLOOR = "
                       f"{SEMI_FLOOR}")
    small = list(primerange(2, _gpu.WHEEL_TOP + 1))
    top = 200000
    _spf_upto(top)
    semis = 0
    for x in range(SEMI_FLOOR + 1, top + 1):
        f = _factor_small(x)
        if sum(f.values()) != 2:
            continue
        semis += 1
        if not semi_wheel_ok(x, small):
            return False, (f"G24a FAIL: the semiprime {x} = {f} has two prime "
                           f"factors up to {_gpu.WHEEL_TOP}")
    if semi_wheel_ok(83 * 89, small) or sum(_factor_small(83 * 89).values()) != 2:
        return False, "G24a FAIL: 83*89 should be the semiprime the floor excludes"
    if not semi_wheel_ok(89 * 89, small) or not semi_wheel_ok(2 * 97, small):
        return False, "G24a FAIL: a square or a single small factor was rejected"
    # THE COFACTOR SIEVE'S THEOREM (round 6), at a depth whose floor leaves a
    # populated range below `top`: above SEMI_TOP * q2 a semiprime with a
    # wheel factor has no other factor up to q2 -- for the whole of 2..89 as
    # the wheel and for the n = 11 plan's subset of it (the primes it leaves
    # out, 29, 37, ..., 83, are sieve primes there) -- and the floor is
    # needed: 89 * 509 sits just under it with both
    if SEMI_TOP < _gpu.WHEEL_TOP:
        return False, (f"G24a FAIL: SEMI_TOP = {SEMI_TOP} is under the largest "
                       f"wheel prime {_gpu.WHEEL_TOP}")
    q2c, fd = 512, "A229630"
    floor_c = k_floor(q2c, 11, fd)
    subset = (2, 3, 5, 7, 11, 13, 17, 19, 23, 31, 41, 47, 73, 89)
    cof = 0
    for x in range(floor_c + 1, top + 1):
        f = _factor_small(x)
        if sum(f.values()) != 2:
            continue
        cof += 1
        for wl in (small, subset):
            if not semi_cofactor_ok(x, wl, q2c, 11, fd):
                return False, (f"G24a FAIL: the semiprime {x} = {f} above "
                               f"{floor_c} has a wheel factor and a sieve "
                               f"factor up to {q2c}")
    if floor_c != SEMI_TOP * q2c or semi_cofactor_ok(89 * 509, small, q2c, 11, fd):
        return False, (f"G24a FAIL: the cofactor floor at q2 = {q2c} is "
                       f"{floor_c}, or 89*509 below it is not the semiprime "
                       f"it excludes")
    for q2 in (32, 1024, 8192, 65536, 1 << 20):
        for fam in FAMILIES:
            c, d = coeffs(fam)
            base = int(q2) if domain(fam) == "prime" else (int(q2) - d) // c
            want = (max(base, SEMI_FLOOR, SEMI_TOP * q2)
                    if domain(fam) == "semiprime" else base)
            if k_floor(q2, 10, fam) != want:
                return False, (f"G24a FAIL: {fam}'s engine floor at q2 = {q2} is "
                               f"{k_floor(q2, 10, fam)}, not {want}")
    return True, (f"G24a ok: all {semis:,} semiprimes in ({SEMI_FLOOR}, {top:,}] "
                  f"have at most one prime factor up to {_gpu.WHEEL_TOP} (the "
                  f"wheel's largest prime, squared, is the floor), 83*89 = 7387 "
                  f"below it has two; all {cof:,} above {floor_c:,} with a wheel "
                  f"factor have no sieve factor to {q2c} (the cofactor floor "
                  f"{SEMI_TOP}*q2; 89*509 below it has both); and the engines' "
                  f"floor on A229630 is never under either while every other "
                  f"family's is the k = 1 form's")


GATES = [g3_table_matches_divisibility, g4_cpu_matches_oracle,
         g6_run_length_matches_oracle, g10_values_stay_inside_the_mr_bound,
         g5_rederive_knowns, g24a_semiprime_wheel_theorem]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
