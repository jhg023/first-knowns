"""cyclotomic_search.py -- the CPU engine for the cyclotomic ladders.

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
  * construction: the killed set K(q, S) is built here from a PRIMITIVE
    ROOT -- q | Phi_k(x) exactly when the order of x is k with its q-part
    stripped, so the kills of order m are g^(j (q-1)/m) for the j coprime
    to m -- while the oracle walks every residue and evaluates the
    polynomials, and builds the roots of unity by sympy's nthroot_mod.  G3
    pins the construction against the oracle's walk, and against a
    vectorised evaluation of every polynomial at every residue on primes
    to 2^20 whose q - 1 is as smooth as the sieve will meet.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (x, off) pairs on
the GPU -- x = base + off with base a host-side big int -- so no machine
word bounds the search (OPTIMIZATION.md 2.7, from the first commit).  x is
the engines' name for the term and the letter both entries give it.

WHAT IS SWEPT.  On A070737 ONE line from the frontier term up (the ladder
nests: cyclotomic_reference).  On A072942 one line PER INDEX from x = 3,
each a separate problem.  The forced primes pin x to the CLASS 0 (mod unit)
-- every q <= n + 1 on A070737 (2310 from n = 10, 30030 from n = 12), every
q with (q - 1) | n on A072942 (56,786,730 = 2*3*5*7*11*13*31*61 at n = 60)
-- and the machinery sweeps a general class x = r + u*t while this engine
marks the dense x line knowing nothing of r or u, which is what makes the
parity gate a check of the forcing as well as of the sieve.  u is DERIVED
per filter (`forced_unit`, from the walk, and checked against the
reference's formula), and a unit whose primes are not all forced is refused
(`assert_unit`), because a unit is a coverage claim.

THE EXCEPTION ZONE.  A kill by q proves nothing unless the value exceeds q,
and the smallest value is Phi_1(x) = x - 1, so the engines refuse to run at
or below x = q2 + 1 (k_floor) and the integers below are classified one at
a time (prefix_hits).  A070737's campaign opens far above it; A072942's
every index opens AT x = 3, so every one of its campaigns covers the zone
on the host first -- and most of its small terms live there.

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24, and the values here are POLYNOMIALS in x of
degree up to phi(k): the largest value of index n reaches the bound at the
PROOF CROSSING k_proof(n, F) -- 2.6e2 at n = 11 of A070737 (Phi_11 has
degree 10) -- so every classification a campaign makes is a thirteen-base
strong probable-prime chain, which can only lengthen a run, never hide one.
A discovery is proved by CERTIFICATE on each value's own structure:
Phi_k(x) - 1 = x^a * prod Phi_d(x) * g(x), with the Phi_d(x) proved primes
of the same run (launch.py certify_run); the ceiling on x is huntlib's
K_CEIL = 1e40.  What ends a family is the GPU tail's residue list, which
must hold every residue one prime can kill -- sum of phi(k) over the forms
by the proved bound -- through n_max (20 on A070737, where the sum is
exactly 128; every index of A072942 to 128).

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, every family, in x space and in class space, and == a
vectorised polynomial walk on large primes; a unit that is not forced -- or
not squarefree -- is refused), G4 (CPU survivors == the oracle's definition
of a survivor on populated windows), G5 (the CPU engine finds published
terms of every family end-to-end as FIRST occurrences from their floors,
inclusive), G6 (engine run lengths == sympy BPSW), G10 (numeric hygiene: the
crossing tight to one x at every index, the ceiling from huntlib, the last
index the engine can express).
"""

import math
import pathlib as _pathlib
import sys as _sys
from functools import lru_cache as _lru_cache

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling as _ceiling                        # noqa: E402
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from cyclotomic_reference import (FAMILIES, FOUND, KNOWN,       # noqa: E402
                                  INDEX_TOP, X_MIN, cyclotomic, family,
                                  floor_x, forbidden_k_residues,
                                  forced_formula, forms, frontier,
                                  kind, maxkills, nforms,
                                  run_length as oracle_run_length,
                                  value, values, w, w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing search runs over.  A forced prime is at most
# n + 1 (cyclotomic_reference: the order q - 1 must be a form's reduced
# index), and the last index either family can run is under 128.
UNIT_UPTO = 128

# THE CEILING ON THE TERM: huntlib's, MEASURED for this project's shape (the
# launcher's certificate drill proves values of a term at 1e40 on every
# route the project uses).  EXCLUSIVE.
K_CEIL = _ceiling.K_CEIL

# THE LAST FILTER THE ENGINE CAN EXPRESS.  The GPU tail keeps the killed
# residues of each prime in a list of at most cyclotomic_gpu.NRES_MAX slots,
# and a prime can kill up to maxkills(F, n) = sum of phi(k) over the forms,
# so the last index is the largest n whose proved bound fits (G10 pins the
# constants to each other).  The engine sizes its list from the primes it
# actually holds (cyclotomic_gpu), so the bound is the guarantee and not the
# cost.
NRES_MAX = 128


def n_max(fam):
    """The largest index n whose proved kill bound fits NRES_MAX: the last
    filter the engine can express -- 20 on A070737 (sum phi(k), k <= 20, is
    128 exactly), and NRES_MAX itself on A072942 (the bound is n)."""
    fam = family(fam)
    if kind(fam) == "divisors":
        return NRES_MAX
    n = 1
    while maxkills(fam, n + 1) <= NRES_MAX:
        n += 1
    return n


def _max_value(fam, n, x):
    return max(values(fam, x, n))


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof at index n: the least x
    whose largest value reaches the deterministic Miller-Rabin bound.
    EXCLUSIVE: k_proof - 1 is the largest x whose every value stays under
    it (G10 pins both halves).  Every Phi_k is increasing on x >= 2, so the
    largest value is monotone and a bisection finds the crossing."""
    fam, n = family(fam), max(int(n), 1)
    lo, hi = 2, 2
    while _max_value(fam, n, hi) < MR_VALID_BELOW:
        hi *= 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _max_value(fam, n, mid) < MR_VALID_BELOW:
            lo = mid
        else:
            hi = mid
    return hi


def k_ceil(n, fam):
    """The enforced ceiling on the term, every family: K_CEIL.  EXCLUSIVE."""
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2, n, fam):
    """The largest x the engines will NOT sweep (EXCLUSIVE floor).

    A kill by q is only a proof of compositeness when the value EXCEEDS q.
    The smallest value at x >= 3 is Phi_1(x) = x - 1, so a sieve to q2 is
    valid from the first x with x - 1 > q2: the floor is q2 + 1.
    """
    family(fam)
    int(n)
    return int(q2) + 1


def zone(q2, n, fam):
    """(lo, hi) INCLUSIVE: the integers between the definition's floor and
    the engine's that a sweep at depth q2 must cover by brute force."""
    lo, hi = floor_x(fam, n), k_floor(q2, n, fam)
    return (lo, hi) if lo <= hi else None


# ---------------------------------------------- the killed set, by a root

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


def _phi(m):
    out = m
    for p in _factor_small(m):
        out = out // p * (p - 1)
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


@_lru_cache(maxsize=None)
def _orders(q, n, fam):
    """The orders modulo q the forms of index n ask for: each k with its
    q-part stripped, kept when it divides q - 1 (the only orders that
    exist).  Computed here from the forms alone, not read from the
    oracle's reduced_orders."""
    q = int(q)
    out = set()
    for k in forms(fam, n):
        m = int(k)
        while m % q == 0:
            m //= q
        if (q - 1) % m == 0:
            out.add(m)
    return frozenset(out)


@_lru_cache(maxsize=None)
def _xkills(q, n, fam):
    """K(q, S): the elements of every attainable order, as powers of the
    primitive root -- g^(j (q-1)/m) for gcd(j, m) = 1."""
    q = int(q)
    g, _fac = _proot(q)
    out = set()
    for m in _orders(q, n, fam):
        step = (q - 1) // m
        out.update(pow(g, j * step, q) for j in range(m) if math.gcd(j, m) == 1)
    return frozenset(out)


def w_fast(q, n, fam):
    """|K(q, S)| without building the residues: the sum of phi(m) over the
    distinct attainable orders (the elements of distinct orders are
    disjoint)."""
    q, n, fam = int(q), int(n), family(fam)
    return sum(_phi(m) for m in _orders(q, n, fam))


def killed_residues(q, n, fam, unit=1):
    """K(q, S): the residues of x that some form of index n makes
    divisible by q, from the primitive root (module docstring).

    CLASS SPACE.  The forced primes pin x to ONE class, x == r (mod unit)
    (`unit_residue`; r = 0 here), so the GPU engine sweeps t with x = r +
    unit*t, and the residues of t that q kills are those of x carried
    through the map: t == (k - r) * unit^-1 (mod q) for each killed k, q
    not dividing unit.  A prime OF the unit kills no t at all -- the class
    was chosen so that it cannot -- and returns the empty list.  The map is
    a bijection of Z/q, so the sizes, hence the survival curve and the
    wheel counts, are unchanged (G3 pins this against the x-space set).
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
    exactly one residue class.  Derived per filter from the kill sets and
    never stored (a unit is a coverage claim), and REQUIRED to equal the
    reference's formula (every q <= n + 1 on A070737, every q with (q - 1)
    | n on A072942): a disagreement is an engine bug and raises."""
    u = 1
    got = []
    for q in primerange(2, upto):
        if len(_free(q, n, fam)) == 1:
            u *= q
            got.append(q)
    if got != forced_formula(fam, n, upto=upto):
        raise ArithmeticError(f"the kill sets force {got} at index {n} of "
                              f"{fam}; the theorem says "
                              f"{forced_formula(fam, n, upto=upto)}")
    return u


def unit_residue(n, fam, unit):
    """r with x == r (mod unit) for every x that survives the primes of
    `unit` -- the CRT of their single free classes.  0 <= r < unit (and 0
    here, since the free class of a forced prime is 0)."""
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

def run_length_fast(fam, x, n):
    """The oracle's run_length with huntlib's Miller-Rabin (a strong
    probable-prime chain past the proof crossing): the leading forms of
    index n whose value is prime."""
    fam, x = family(fam), int(x)
    if x < X_MIN:
        return 0
    r = 0
    for k in forms(fam, n):
        v = value(k, x)
        if v < 2 or not mr_is_prime(v):
            break
        r += 1
    return r


def fermat2(N):
    """2^(N-1) == 1 (mod N) for odd N > 2; N == 2 passes, everything else
    fails -- the device Fermat stage's test, in Python ints (G23)."""
    N = int(N)
    if N < 3 or N % 2 == 0:
        return N == 2
    return pow(2, N - 1, N) == 1


def fermat_lead(fam, x, n, T):
    """True when the leading T forms of index n all pass fermat2 at x.
    What the device Fermat stage emits, and a superset of every x whose
    leading T forms are prime (a failed Fermat test is a proof of
    compositeness)."""
    fam, x = family(fam), int(x)
    for k in forms(fam, n)[:int(T)]:
        if not fermat2(value(k, x)):
            return False
    return True


def prefix_hits(fam, n, q2, floor=1, read_n=None):
    """[(x, run)] over the exception zone of index n at depth q2 -- every
    integer between the definition's floor and the engine's with a run of
    at least `floor` -- by huntlib's chain (the oracle's own prefix_hits is
    the sympy version).  The walk is the forced class PLUS the integers
    below the point where the forced primes bind (x - 1 <= the prime), so
    nothing in the zone is skipped: A072942's a(1) = 3 is odd where 2 is
    forced, because Phi_1(3) = 2 is the prime itself."""
    fam = family(fam)
    z = zone(q2, n, fam)
    if z is None:
        return []
    lo, hi = z
    read_n = int(n) if read_n is None or kind(fam) != "ladder" else max(int(read_n), int(n))
    r0, u = forced_class(n, fam)
    out = []
    top_q = max([q for q in primerange(2, UNIT_UPTO) if u % q == 0], default=1)
    for x in range(lo, hi + 1):
        if x - 1 > top_q and x % u != r0:
            continue
        r = run_length_fast(fam, x, read_n)
        if r >= floor:
            out.append((x, r))
    return sorted(out)


class CpuEngine:
    """Segmented sieve over the dense x line, no wheel.

    With `unit` > 1 (the forced unit of the filter, or a divisor of it) the
    dense line is the t line of the class x = r0 + unit*t, marked with the
    CLASS-SPACE kill sets (killed_residues with the unit), and the
    survivors come back as x.  The units here reach 5.7e7 (A072942 n = 60),
    where a window of a few million t is 1e14 of x and no dense x line is
    affordable; G9 compares the GPU's class-space stream against this one
    there, and against the x-space engine (unit 1) everywhere a dense x
    line fits.
    """

    def __init__(self, n, fam, q2=Q2_DEFAULT, unit=1):
        self.n = int(n)
        self.fam = family(fam)
        self.q2 = q2
        self.unit = assert_unit(self.n, self.fam, unit)
        self.r0 = unit_residue(self.n, self.fam, self.unit) if self.unit > 1 else 0
        self.primes = list(primerange(2, q2 + 1))
        self.table = {q: killed_residues(q, n, self.fam, self.unit)
                      for q in self.primes}
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
                f"exceeds q, and the smallest value is Phi_1(x) = x - 1")
        return self._survivors(k_lo, k_hi, block)

    def _survivors(self, k_lo, k_hi, block):
        u, r0 = self.unit, self.r0
        # the t range of the class inside [k_lo, k_hi): the least t with
        # r0 + u*t >= k_lo, up to but excluding the least with r0 + u*t >= k_hi
        t0 = -((r0 - int(k_lo)) // u)
        t_end = -((r0 - int(k_hi)) // u)
        while t0 < t_end:
            t1 = min(t0 + block, t_end)
            alive = np.ones(t1 - t0, dtype=bool)
            for q in self.primes:
                for v in self.table[q]:
                    first = (v - t0) % q
                    if first < alive.size:
                        alive[first::q] = False
            idx = np.nonzero(alive)[0]
            if idx.size:
                # Python ints, not u64: this engine is the parity reference
                # for a range that runs past 2^64.
                yield [r0 + u * (t0 + int(i)) for i in idx]
            t0 = t1

    def survives(self, k):
        """The same decision, one candidate at a time, in Python ints."""
        k = int(k)
        if (k - self.r0) % self.unit:
            return False
        t = (k - self.r0) // self.unit
        return all(t % q not in st for q, st in self._sets().items())

    def _sets(self):
        if not hasattr(self, "_frozen"):
            self._frozen = {q: frozenset(v) for q, v in self.table.items()}
        return self._frozen

    # ------------------------------------------------------------ classify
    def run_length(self, k, read_n=None):
        """The run of x = k against this filter (or against `read_n` on
        the ladder, to read past it), with huntlib's chain."""
        n = self.n if read_n is None else max(int(read_n), self.n)
        if kind(self.fam) != "ladder":
            n = self.n
        return run_length_fast(self.fam, k, n)

    def hunt(self, k_lo, k_hi, read_n=None):
        """[(x, run)] for every survivor whose run reaches the filter's."""
        out = []
        for chunk in self.survivors(k_lo, k_hi):
            for k in chunk:
                r = self.run_length(int(k), read_n=read_n)
                if r >= nforms(self.fam, self.n):
                    out.append((int(k), r))
        return out


# --------------------------------- gates -----------------------------------

def _filters(fam):
    """A spread of filters, always including the open ones."""
    if kind(fam) == "ladder":
        top = frontier(fam) + 1
        return sorted({1, 3, 4, 5, 8, top - 1, top, top + 2})
    return [6, 12, 30, 48, 60, 72, 96]


# Primes in (4096, 2^20] that G3 checks against a vectorised polynomial walk:
# q - 1 a multiple of lcm(1..12) = 27720 (where every order to 12 exists:
# 55441, 110881, 332641, 748441, 1025641; lcm(1..13)*k + 1 is composite for
# both k under 2^20) and a spread of ordinary ones.  G3 checks that each is
# prime.
G3_BIG = (4099, 9241, 55441, 65537, 110881, 131071, 332641, 524287, 748441,
          1025641, 1048573)


def _brute_kills(q, n, fam):
    """K(q, S) by evaluating every form at every residue with numpy (G3's
    large-prime leg): Horner modulo q, no orders, no roots."""
    x = np.arange(q, dtype=np.int64)
    dead = np.zeros(q, dtype=bool)
    for k in forms(fam, n):
        v = np.zeros(q, dtype=np.int64)
        for c in reversed(cyclotomic(k)):
            v = (v * x + (c % q)) % q
        dead |= v == 0
    return set(np.nonzero(dead)[0].tolist())


def g3_table_matches_divisibility():
    """The constructed killed set must equal direct divisibility, BOTH ways,
    for every family; the primitive-root construction must equal a
    vectorised polynomial walk on large primes; and every unit but the
    forced one is refused."""
    checked = 0
    for fam in FAMILIES:
        for n in _filters(fam):
            ks = forms(fam, n)
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
                    if not any(value(k, u) % q == 0 for k in ks):
                        return False, (f"G3 FAIL: {fam} n={n} q={q} residue "
                                       f"{u} kills nothing")
                checked += 1
    big = 0
    most = (0, 0, 0, "")
    if not all(mr_is_prime(q) for q in G3_BIG):
        return False, "G3 FAIL: a large test modulus is not prime"
    for fam in FAMILIES:
        for n in ((frontier(fam) + 1, 13) if kind(fam) == "ladder" else (60, 96)):
            for q in G3_BIG:
                built = set(killed_residues(q, n, fam))
                brute = _brute_kills(q, n, fam)
                if built != brute or w_fast(q, n, fam) != len(brute):
                    return False, (f"G3 FAIL: {fam} n={n} q={q}: the primitive-"
                                   f"root construction holds {len(built)} "
                                   f"residues, the polynomial walk {len(brute)}")
                most = max(most, (len(built), q, n, fam))
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
                for q in primerange(2, UNIT_UPTO) if unit % q == 0)] if unit < 10 ** 6 else [r]
            if free != [r] or r != 0:
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
    want = {"A070737": {(0, 2), (0, 6), (0, 30), (0, 210), (0, 2310), (0, 30030)},
            "A072942": {(0, 2 * 3 * 7), (0, 2 * 3 * 5 * 7 * 13),
                        (0, 2 * 3 * 7 * 11 * 31), (0, 2 * 3 * 5 * 7 * 13 * 17),
                        (0, 2 * 3 * 5 * 7 * 11 * 13 * 31 * 61),
                        (0, 2 * 3 * 5 * 7 * 13 * 19 * 37 * 73),
                        (0, 2 * 3 * 5 * 7 * 13 * 17 * 97)}}
    if classes != want:
        return False, f"G3 FAIL: the forced classes are {classes}, expected {want}"
    refused = 0
    for fam in FAMILIES:
        n = frontier(fam) + 1 if kind(fam) == "ladder" else 60
        u = forced_unit(n, fam)
        for unit in (17 * u, 4, 2 * u, 67, 23 * u, 41):
            try:
                assert_unit(n, fam, unit)
                return False, f"G3 FAIL: unit {unit} accepted for {fam} n={n}"
            except ValueError:
                refused += 1
    opens = "; ".join("%s n = %d x == %d (mod %d)" % ((fam, n) + forced_class(n, fam))
                      for fam, n in (("A070737", frontier("A070737") + 1),
                                     ("A072942", 60), ("A072942", 96)))
    return True, (f"G3 ok: the primitive-root K(q, S) == direct divisibility in "
                  f"both directions at all {checked} (q < 300, index, family), "
                  f"with |K| equal to the walk's, the roots of unity's and the "
                  f"order-sum's; == a vectorised polynomial walk at {big} (q, "
                  f"index, family) on primes to 2^20, five with q - 1 a multiple "
                  f"of lcm(1..12) (the most: {most[0]} residues "
                  f"at q = {most[1]}, {most[3]} n = {most[2]}); in class space "
                  f"({cls} cases) the t kills map back exactly through x = "
                  f"unit*t, the unit's own primes kill nothing, and 0 is the "
                  f"one class the oracle leaves free -- {opens}; {refused} "
                  f"inadmissible units refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, every family,
    from small filters to each open index."""
    checks = 0
    windows = []
    top = frontier("A070737") + 1
    windows += [("A070737", 4, 128, 70_000, 400_000),
                ("A070737", 7, 64, 2_000_000, 2_000_000),
                ("A070737", top, 32, 5 * 10 ** 12, 2_000_000),
                ("A070737", top + 2, 32, 10 ** 15, 2_000_000),
                ("A072942", 12, 128, 70_000, 400_000),
                ("A072942", 60, 32, 10 ** 12, 2_000_000),
                ("A072942", 96, 32, 10 ** 15, 2_000_000)]
    for fam, n, q2, k_lo, span in windows:
        eng = CpuEngine(n, fam, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        ks = forms(fam, n)
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            hi = min(c0 + (1 << 22), k_lo + span)
            idx = np.arange(0, hi - c0, dtype=np.int64)
            ok = np.ones(idx.size, dtype=bool)
            for q in smalls:
                r = (c0 % q + idx) % q
                for k in ks:                    # every value of every form
                    v = np.zeros(idx.size, dtype=np.int64)
                    for c in reversed(cyclotomic(k)):
                        v = (v * r + (c % q)) % q
                    ok &= v != 0
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
                  f"populated windows ({checks} survivors; both families, "
                  f"filters 4 to the open indices, at 7e4 to 1e15)")


# Published terms a dense CPU sweep affords in a gate: A070737's a(7) (3.0e9
# of line above a(6) = 6,770,610) and A072942's a(12), a(20), a(28) and
# a(18) (2.5e7 to 1.1e9 of line from x = 3).  Everything bigger is the GPU
# canaries'.
G5_TERMS = {"A070737": (7,), "A072942": (12, 20, 28, 18)}


def g5_rederive_knowns():
    """The CPU engine finds published terms of EVERY family end-to-end, and
    FIRST: the sweep starts AT the index's floor (a(n - 1) on the nesting
    ladder, x = 3 on A072942), with the exception zone above it covered by
    brute force, so the claim is about the line and not about a window."""
    found = []
    for fam, ns in G5_TERMS.items():
        for n in ns:
            q2 = 1024
            eng = CpuEngine(n, fam, q2=q2)
            target = KNOWN[fam][n]
            lo = floor_x(fam, n)
            pre = [x for x, r in prefix_hits(fam, n, q2, floor=nforms(fam, n))
                   if x >= lo]
            if pre and min(pre) < target:
                return False, (f"G5 FAIL: {fam}: the exception zone holds "
                               f"{min(pre)} below a({n}) = {target}")
            start = max(lo, k_floor(q2, n, fam) + 1)
            hits = eng.hunt(start, target + 1)
            if not hits or min(k for k, _ in hits) != target:
                return False, (f"G5 FAIL: {fam} least solution of index {n} from "
                               f"{lo} came out {min(hits)[0] if hits else None}, "
                               f"expected {target}")
            found.append(f"{fam} a({n})")
    return True, ("G5 ok: CPU engine re-derived " + ", ".join(found) +
                  " end-to-end as FIRST occurrences from each index's floor "
                  "(inclusive; the zone by brute force), each at its OEIS index")


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW on real candidates, and
    every published term reads its full form count in both."""
    seen = 0
    for fam in FAMILIES:
        top = frontier(fam) + 1 if kind(fam) == "ladder" else 60
        xs = [1, 2, 3, 4, 6, 9, 10, 12, 150, 2913, 12345679, 10 ** 12 + 39,
              2 ** 64 + 13, 10 ** 15 + 37, 10 ** 25 + 30030]
        if kind(fam) == "ladder":
            xs += [KNOWN[fam][10], KNOWN[fam][10] + 6, KNOWN[fam][10] - 6]
        else:
            xs += [KNOWN[fam][70], KNOWN[fam][70] + 30, KNOWN[fam][36]]
        for k in xs:
            a = run_length_fast(fam, k, top)
            b = oracle_run_length(fam, k, top)
            if a != b:
                return False, (f"G6 FAIL: {fam} x={k} engine run {a} != "
                               f"oracle run {b}")
            seen += 1
        for n in sorted(KNOWN[fam]):
            x = KNOWN[fam][n]
            want = nforms(fam, n)
            if run_length_fast(fam, x, n) != want or oracle_run_length(fam, x, n) != want:
                return False, (f"G6 FAIL: {fam} a({n}) does not read its full "
                               f"run in both implementations")
            seen += 2
    # the entries' own small cases: 6 runs to 4 on A070737 (a(3) = a(4)),
    # 150 to 4, 2 to 0 (Phi_1(2) = 1), and 62 solves n = 47 and n = 15
    if (run_length_fast("A070737", 6, 8) != 4 or run_length_fast("A070737", 150, 8) != 4
            or run_length_fast("A070737", 2, 3) != 0
            or run_length_fast("A072942", 62, 47) != 2
            or run_length_fast("A072942", 62, 15) != 4
            or run_length_fast("A072942", 61, 15) != 0):
        return False, "G6 FAIL: the small cases read wrong"
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates across both families (2^64 + 13, 10^25 among "
                  f"them, values to hundreds of digits), every published term "
                  f"reads its full form count in both, and the entries' own "
                  f"small cases read as they say (6 runs to 4 on A070737; 62 "
                  f"solves n = 47 and n = 15 on A072942)")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: the proof crossing tight to one x per (n, F), the
    ceiling huntlib's K_CEIL and above every crossing, and the last filter
    the engine can express tight to its residue list (module docstring)."""
    import cyclotomic_gpu as _gpu
    if _gpu.NRES_MAX != NRES_MAX:
        return False, (f"G10 FAIL: NRES_MAX = {NRES_MAX} here but the GPU tail "
                       f"holds {_gpu.NRES_MAX} residues a prime")
    rows = []
    for fam in FAMILIES:
        ns = (range(1, frontier(fam) + 12) if kind(fam) == "ladder"
              else (6, 12, 30, 36, 48, 60, 66, 72, 78, 80, 84, 88, 90, 96))
        for n in ns:
            c = k_proof(n, fam)
            if _max_value(fam, n, c - 1) >= MR_VALID_BELOW:
                return False, (f"G10 FAIL: the largest deterministic x for "
                               f"({n}, {fam}) leaves the deterministic MR zone")
            if _max_value(fam, n, c) < MR_VALID_BELOW:
                return False, (f"G10 FAIL: the proof crossing for ({n}, {fam}) "
                               f"is not tight: x = {c} is still deterministic")
            top = k_ceil(n, fam)
            if top != _ceiling.K_CEIL or top <= c:
                return False, f"G10 FAIL: the {fam} ceiling at n = {n} is {top}"
        if any(K_CEIL <= x for x in FOUND[fam].values()):
            return False, f"G10 FAIL: a {fam} find sits at or above the ceiling"
        nm = n_max(fam)
        if kind(fam) == "ladder":
            if not maxkills(fam, nm) <= NRES_MAX < maxkills(fam, nm + 1):
                return False, f"G10 FAIL: {fam}'s last expressible index is not {nm}"
            if nm <= frontier(fam) + 3:
                return False, f"G10 FAIL: {fam} has too few open indices the engine can express"
            rows.append(f"{fam} n = {frontier(fam) + 1}: crossing x = "
                        f"{k_proof(frontier(fam) + 1, fam)}, last index {nm}")
        else:
            if nm < INDEX_TOP or maxkills(fam, nm) > NRES_MAX:
                return False, f"G10 FAIL: {fam}'s last expressible index is {nm}"
            rows.append(f"{fam} n = 96: crossing x = {k_proof(96, fam)}, every "
                        f"index to {nm} expressible")
    return True, ("G10 ok: the proof crossing is where the largest value of "
                  "the index reaches the deterministic MR bound (3.317e24), "
                  f"tight to one x at every index checked ({'; '.join(rows)}: "
                  "every campaign classifies past it, and every discovery is "
                  "proved by certificate); the ceiling on the term is huntlib's "
                  "K_CEIL = %.4g on every family; and the last filter is the "
                  "one whose proved kill bound (the sum of phi(k) over the "
                  "forms) fills the GPU tail's residue list (NRES_MAX = %d)"
                  % (K_CEIL, NRES_MAX))


GATES = [g3_table_matches_divisibility, g4_cpu_matches_oracle,
         g6_run_length_matches_oracle, g10_values_stay_inside_the_mr_bound,
         g5_rederive_knowns]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        import time as _time
        for g in GATES:
            t0 = _time.time()
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg + " [%.1fs]" % (_time.time() - t0))
    _sys.exit(_shutdown.graceful(_gates) or 0)
