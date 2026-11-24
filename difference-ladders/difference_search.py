"""difference_search.py -- the CPU engine for the difference ladders.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is independent
in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array over
    the b line and uses no wheel at all.  The GPU engine never materialises
    the line: it generates only the residues that survive a wheel and tests
    those against packed forbidden-residue tables, bailing out at the first
    kill.  A wheel bug on the GPU side therefore shows up as a parity failure
    rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(q, n) is built here from a PRIMITIVE
    ROOT -- the primitive p-th roots of unity are g^(j (q-1)/p), j = 1..p-1,
    and q | f_p(b) exactly when b = 1/(zeta - 1) -- while the oracle walks
    every residue and reduces the values, and builds the roots of unity by
    sympy's nthroot_mod.  G3 pins the construction against the oracle's
    walk, and against a vectorised evaluation of every form at every residue
    on primes to 2^20 whose q - 1 is as smooth as the sieve will meet.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (x, off) pairs on
the GPU -- x = base + off with base a host-side big int -- so no machine
word bounds the search (OPTIMIZATION.md 2.7).  In the code the swept
integer is called x or k (the engines' names, inherited); it IS the term b
of both entries.

WHAT IS SWEPT.  One line per family from the frontier term up (the ladders
nest: difference_reference).  NOTHING IS FORCED -- every prime leaves 0 and
q - 1 free -- so there is no class and no unit: the line is the whole b
line, and `forced_unit` derives 1 at every filter (and checks the oracle's
theorem that it must).  The class-space machinery of the engine this was
built from (cyclotomic-ladders) is kept, and `assert_unit` refuses every
unit but 1.

THE EXCEPTION ZONE.  A kill by q proves nothing unless the value exceeds q,
and the smallest value is f_2(b) = 2b + 1, so the engines refuse to run at
or below b = q2 (k_floor, cautiously) and the integers below are classified
one at a time (prefix_hits).  Every campaign opens far above it.

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24, and the values here are f_p(b), of degree p - 1:
the largest sieved value of index n reaches the bound at the PROOF CROSSING
k_proof(n, F) -- b = 11 at n = 9 of A216666 -- so every classification a
campaign makes is a thirteen-base strong probable-prime chain.  For a
condition that asks for a PRIME that can only lengthen a run; for one that
asks for a COMPOSITE (A216668's non-Mersenne exponents) a failed base is a
proof and a passed chain stops the run, so a strong pseudoprime to thirteen
bases at hundreds of digits could shorten one -- the launcher re-reads every
narrated run with sympy's BPSW.  A discovery's values are proved by
certificate where their structure allows (launch.py) and otherwise listed
UNPROVED for a general prover; the ceiling on b is huntlib's K_CEIL = 1e40.
What ends a family is the GPU tail's residue list, which must hold every
residue one prime can kill -- the sum of (p - 1) over the sieved forms by
the proved bound -- through n_max (13 on A216666, 27 on A216668, at
NRES_MAX = 256).

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, every family, and == a vectorised walk on large primes; every
unit but 1 refused), G4 (CPU survivors == the oracle's definition of a
survivor on populated windows), G5 (the CPU engine finds published terms of
both families end-to-end as FIRST occurrences from their floors,
inclusive), G6 (engine run lengths == sympy BPSW, both families, the
composite conditions included), G10 (numeric hygiene: the crossing tight to
one b at every index, the ceiling from huntlib, the last index the engine
can express).
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
from difference_reference import (FAMILIES, FOUND, KNOWN,       # noqa: E402
                                  READ_TOP, b_min, conditions, family,
                                  floor_x, forbidden_k_residues,
                                  forced_formula, forms, frontier,
                                  kind, maxkills, nforms,
                                  run_length as oracle_run_length,
                                  value, values, w, w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing search runs over (nothing is forced here;
# the search runs anyway, and the reference's theorem must agree).
UNIT_UPTO = 128

# THE CEILING ON THE TERM: huntlib's (CLAUDE.md 5h; the launcher's
# certificate drill and OPTIMIZATION_LOG.md's proof-cost measurements).
# EXCLUSIVE.
K_CEIL = _ceiling.K_CEIL

# THE LAST FILTER THE ENGINE CAN EXPRESS.  The GPU tail keeps the killed
# residues of each prime in a list of at most difference_gpu.NRES_MAX slots
# (a compile-time loop bound, read only for the rare prime past the mask
# whose mask bit is set), and a prime can kill up to maxkills(F, n) = the
# sum of (p - 1) over the sieved forms, so the last index is the largest n
# whose proved bound fits (G10 pins the constants to each other): 13 on
# A216666 (225), 27 on A216668 (237).  Twice cyclotomic-ladders' 128,
# because A216666's day-long filter n = 11 has a bound of 149 and A216668's
# n = 24 one of 237; the engine sizes its list from the primes it actually
# holds, so the bound is the guarantee and not the cost.
NRES_MAX = 256

# THE LAST INDEX ANY RUN IS READ TO: a run that reaches it HALTS the
# campaign (a run of 40 would be a value of thousands of digits prime at
# every Mersenne exponent to 173 -- an engine bug, not a find).
READ_MAX = READ_TOP


def n_max(fam):
    """The largest index n whose proved kill bound fits NRES_MAX: the last
    filter the engine can express."""
    fam = family(fam)
    n = 1
    while maxkills(fam, n + 1) <= NRES_MAX:
        n += 1
    return n


def read_max(fam):
    """The last index a run is read to (READ_MAX on both families)."""
    family(fam)
    return READ_MAX


def _max_value(fam, n, x):
    return max(values(fam, x, n))


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof at index n: the least b
    whose largest SIEVED value reaches the deterministic Miller-Rabin bound.
    EXCLUSIVE: k_proof - 1 is the largest b whose every value stays under
    it (G10 pins both halves).  Every f_p is increasing in b >= 1, so the
    largest value is monotone and a bisection finds the crossing."""
    fam, n = family(fam), max(int(n), 1)
    lo = b_min(fam)
    if _max_value(fam, n, lo) >= MR_VALID_BELOW:
        return lo                 # no b is deterministic (A216668 from n = 24:
        #                           2^89 - 1 is past the bound at b = 1)
    hi = lo + 1
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
    """The largest b the engines will NOT sweep (EXCLUSIVE floor).

    A kill by q is only a proof of compositeness when the value EXCEEDS q.
    The smallest value is f_2(b) = 2b + 1, so a sieve to q2 is valid from
    b = q2 / 2; the floor is q2 itself, which needs no parity argument.
    """
    family(fam)
    int(n)
    return int(q2)


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
    """The sieved forms p of index n with p | q - 1 -- the only forms q can
    divide (a primitive p-th root of unity exists mod q exactly then).
    Computed here from the forms alone."""
    q = int(q)
    return tuple(p for p in forms(fam, n) if (q - 1) % p == 0)


@_lru_cache(maxsize=None)
def _xkills(q, n, fam):
    """K(q, n): b = 1/(zeta - 1) for every primitive p-th root of unity
    zeta = g^(j (q-1)/p), j = 1..p-1, over the attainable forms p."""
    q = int(q)
    g, _fac = _proot(q)
    out = set()
    for p in _orders(q, n, fam):
        step = (q - 1) // p
        for j in range(1, p):
            z = pow(g, j * step, q)
            out.add(pow(z - 1, q - 2, q))
    return frozenset(out)


def w_fast(q, n, fam):
    """|K(q, n)| without building the residues: the sum of (p - 1) over the
    attainable forms (different orders are disjoint, the map injective)."""
    q, n, fam = int(q), int(n), family(fam)
    return sum(p - 1 for p in _orders(q, n, fam))


# ---------------------------------------- which primes the sieve tests
#
# THE SIEVE SET IS CHOSEN BY WHAT A PRIME'S KILLS ARE WORTH, NOT BY ITS SIZE
# (engine v2, OPTIMIZATION_LOG.md round 1, 2026-11-23).  Both engines sieve
# exactly `select_primes(n, F, q2, tau)`; with tau None that is every prime
# to q2, the set every engine before v2 sieved.  A prime's test costs the
# same per candidate whatever it kills, and what a kill SAVES is the device
# Fermat work the candidate would otherwise cost -- which depends on the
# form that kills it: the stage tests the cheapest forms first, so a b whose
# 2b + 1 a prime divides would have failed the stage's first, cheapest test
# anyway, while a b killed through f_31 (never tested on the device) would
# have run the whole stage.  So a kill through the form of rank i among the
# sieved forms (ascending) counts SELECT_OMEGA[i] -- the stage's measured
# cost up to and including that form, over its whole cost, at A216666
# n = 11 -- and every later form counts 1.  kill_value(q) is the sum of
# those weights over the residues q kills, divided by q, and a prime is
# sieved when it reaches tau (difference_gpu.SIEVE_TAU, the measured test
# cost over the stage's cost per value).  At n = 11 that drops the primes
# past ~600 that kill only 2b + 1's residue (each worth a fifth of a test)
# and admits primes to 32768 with q - 1 rich in the sieved p (30031: 35
# kills, three tests' worth).  Every prime to SELECT_ALL_TO is kept, so the
# wheel's primes are always the CPU engine's too.  A selection can only
# change WHICH candidates reach the Fermat stage: a kill is a proof of
# compositeness either way (the floor is still q2), and a run is decided by
# the host's classification of every value, never by the sieve.
SELECT_OMEGA = (0.18, 0.42, 0.75, 0.82)
SELECT_ALL_TO = 89


def kill_value(q, n, fam):
    """The weighted share of b that q kills at index n (above)."""
    q, n, fam = int(q), int(n), family(fam)
    ranks = {int(p): i for i, p in enumerate(sorted(int(p) for p in
                                                    forms(fam, n)))}
    tot = 0.0
    for p in _orders(q, n, fam):
        i = ranks[int(p)]
        tot += (int(p) - 1) * (SELECT_OMEGA[i] if i < len(SELECT_OMEGA)
                               else 1.0)
    return tot / q


@_lru_cache(maxsize=None)
def select_primes(n, fam, q2, tau=None):
    """The primes both engines sieve with at index n to depth q2: all of
    them when tau is None, else those to SELECT_ALL_TO and those whose
    kill_value reaches tau.  A tuple, ascending."""
    n, fam, q2 = int(n), family(fam), int(q2)
    if tau is None:
        return tuple(int(q) for q in primerange(2, q2 + 1))
    tau = float(tau)
    return tuple(int(q) for q in primerange(2, q2 + 1)
                 if q <= SELECT_ALL_TO or kill_value(q, n, fam) >= tau)


def killed_residues(q, n, fam, unit=1):
    """K(q, n): the residues of b that some sieved form of index n makes
    divisible by q, from the primitive root (module docstring).

    CLASS SPACE (inherited, never used by a campaign here: nothing is
    forced, so the only admissible unit is 1).  For a unit > 1 the residues
    of t with b = r + unit*t would be those of b carried through the map;
    `assert_unit` refuses any such unit before it gets here.
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
    """The residues of b mod q that no form kills."""
    return sorted(set(range(q)) - _xkills(int(q), int(n), family(fam)))


def forced_unit(n, fam, upto=UNIT_UPTO):
    """The product of the primes FORCED at index n -- those q that leave b
    exactly one residue class.  Derived per filter from the kill sets and
    REQUIRED to equal the reference's theorem (none: 0 and q - 1 always
    survive): a disagreement is an engine bug and raises.  Always 1."""
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
    """r with b == r (mod unit) for every b that survives the primes of
    `unit`: 0 for the only admissible unit, 1."""
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
    """(r, u): the class b == r (mod u) the forced primes pin b to -- (0, 1)."""
    u = forced_unit(n, fam, upto)
    return unit_residue(n, fam, u), u


def assert_unit(n, fam, unit):
    """Raise unless `unit` is SQUAREFREE and every prime factor of it is
    forced at index n -- here, unless it is 1.

    A unit that is not forced is a COVERAGE bug, not an inefficiency: an
    engine sweeping b = r + unit*t never looks at the other classes, and if
    a prime of the unit leaves two classes free it has silently dropped one
    of them.  Every prime leaves at least two here.
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
                f"not 1, so an engine sweeping b = r + {unit}*t would skip "
                f"line it claims to cover; nothing is forced on these ladders "
                f"and the only admissible unit is 1")
        if unit % (q * q) == 0:
            raise ValueError(
                f"unit {unit} is not squarefree: forcing pins b mod {q}, "
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
    probable-prime chain past the proof crossing): the leading conditions
    of index n that b = x meets."""
    fam, x = family(fam), int(x)
    if x < b_min(fam):
        return 0
    r = 0
    for p, want in conditions(fam, n):
        v = value(p, x)
        if (v >= 2 and mr_is_prime(v)) != want:
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
    """True when the leading T SIEVED forms of index n all pass fermat2 at
    b = x.  What the device Fermat stage emits, and a superset of every b
    whose leading T sieved values are prime (a failed Fermat test is a proof
    of compositeness)."""
    fam, x = family(fam), int(x)
    for p in forms(fam, n)[:int(T)]:
        if not fermat2(value(p, x)):
            return False
    return True


def prefix_hits(fam, n, q2, floor=1, read_n=None):
    """[(b, run)] over the exception zone of index n at depth q2 -- every
    integer between the definition's floor and the engine's with a run of
    at least `floor` -- by huntlib's chain (the oracle's own prefix_hits is
    the sympy version).  No class: every integer is walked."""
    fam = family(fam)
    z = zone(q2, n, fam)
    if z is None:
        return []
    lo, hi = z
    read_n = int(n) if read_n is None else max(int(read_n), int(n))
    out = []
    for x in range(lo, hi + 1):
        r = run_length_fast(fam, x, read_n)
        if r >= floor:
            out.append((x, r))
    return sorted(out)


class CpuEngine:
    """Segmented sieve over the dense b line, no wheel and no class (the
    only admissible unit is 1)."""

    def __init__(self, n, fam, q2=Q2_DEFAULT, unit=1, select=None):
        self.n = int(n)
        self.fam = family(fam)
        self.q2 = q2
        self.select = select
        self.unit = assert_unit(self.n, self.fam, unit)
        self.r0 = unit_residue(self.n, self.fam, self.unit) if self.unit > 1 else 0
        # the sieve set (select_primes): every prime to q2, or the primes
        # the value rule keeps
        self.primes = list(select_primes(self.n, self.fam, q2, select))
        self.table = {q: killed_residues(q, n, self.fam, self.unit)
                      for q in self.primes}
        self.marks_per_k = sum(len(v) / q for q, v in self.table.items())

    # ---------------------------------------------------------------- sieve
    def survivors(self, k_lo, k_hi, block=1 << 22):
        """Yield lists of the b in [k_lo, k_hi) that no prime q <= q2 kills.

        The bounds are checked EAGERLY, here, and the generator is a separate
        function -- a `yield` anywhere in this body would defer every check
        to the first `next()`.
        """
        if k_hi > k_ceil(self.n, self.fam):
            raise ValueError(f"b {k_hi} past the enforced ceiling "
                             f"{k_ceil(self.n, self.fam)}")
        if k_lo <= k_floor(self.q2, self.n, self.fam):
            raise ValueError(
                f"engines refuse to run at or below "
                f"{k_floor(self.q2, self.n, self.fam)}: a kill by q <= q2 = "
                f"{self.q2} is only a proof of compositeness once the value "
                f"exceeds q, and the smallest value is f_2(b) = 2b + 1")
        return self._survivors(k_lo, k_hi, block)

    def _survivors(self, k_lo, k_hi, block):
        u, r0 = self.unit, self.r0
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
        """The run of b = k against this filter (or against `read_n`, to
        read past it), with huntlib's chain."""
        n = self.n if read_n is None else max(int(read_n), self.n)
        return run_length_fast(self.fam, k, n)

    def hunt(self, k_lo, k_hi, read_n=None):
        """[(b, run)] for every survivor whose run reaches the filter's."""
        out = []
        for chunk in self.survivors(k_lo, k_hi):
            for k in chunk:
                r = self.run_length(int(k), read_n=read_n)
                if r >= self.n:
                    out.append((int(k), r))
        return out


# --------------------------------- gates -----------------------------------

def _filters(fam):
    """A spread of filters, always including the open ones."""
    top = frontier(fam) + 1
    return sorted({1, 3, 4, 5, 8, top - 1, top, min(top + 2, n_max(fam))})


# Primes in (4096, 2^20] that G3 checks against a vectorised walk: q - 1 a
# multiple of many small primes (where several forms attain at once:
# 30030*k + 1 -- 120121, 300301 -- and 2*61*89*k + 1 -- 10859, 173729 --
# and 2*3*61*89*k + 1 -- 390889, 553759 -- A216668's strongest), and a
# spread of ordinary ones.  G3 checks that each is prime.
G3_BIG = (4099, 9241, 10859, 65537, 99991, 120121, 131071, 173729, 300301,
          390889, 524287, 553759, 1048573)


def _vpowmod(r, e, q):
    """r^e mod q elementwise for an int64 array r (q < 2^31): repeated
    squaring, nothing clever."""
    acc = np.ones_like(r)
    base = r % q
    while e:
        if e & 1:
            acc = (acc * base) % q
        base = (base * base) % q
        e >>= 1
    return acc


def _brute_kills(q, n, fam):
    """K(q, n) by evaluating every sieved form at every residue with numpy
    (G3's large-prime leg): (b+1)^p - b^p mod q, no roots, no orders."""
    b = np.arange(q, dtype=np.int64)
    dead = np.zeros(q, dtype=bool)
    for p in forms(fam, n):
        dead |= (_vpowmod(b + 1, p, q) - _vpowmod(b, p, q)) % q == 0
    return set(np.nonzero(dead)[0].tolist())


def g3_table_matches_divisibility():
    """The constructed killed set must equal direct divisibility, BOTH ways,
    for every family; the primitive-root construction must equal a
    vectorised walk on large primes; and every unit but 1 is refused."""
    checked = 0
    for fam in FAMILIES:
        for n in _filters(fam):
            ps = forms(fam, n)
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
                    if not any(value(p, u) % q == 0 for p in ps):
                        return False, (f"G3 FAIL: {fam} n={n} q={q} residue "
                                       f"{u} kills nothing")
                checked += 1
    big = 0
    most = (0, 0, 0, "")
    if not all(mr_is_prime(q) for q in G3_BIG):
        return False, "G3 FAIL: a large test modulus is not prime"
    for fam in FAMILIES:
        for n in (frontier(fam) + 1, n_max(fam)):
            for q in G3_BIG:
                built = set(killed_residues(q, n, fam))
                brute = _brute_kills(q, n, fam)
                if built != brute or w_fast(q, n, fam) != len(brute):
                    return False, (f"G3 FAIL: {fam} n={n} q={q}: the primitive-"
                                   f"root construction holds {len(built)} "
                                   f"residues, the vectorised walk {len(brute)}")
                most = max(most, (len(built), q, n, fam))
                big += 1
    # NOTHING IS FORCED: the derived unit is 1 at every filter, and every
    # other unit is refused
    for fam in FAMILIES:
        for n in _filters(fam):
            if forced_class(n, fam) != (0, 1):
                return False, f"G3 FAIL: {fam} n={n} derives the class {forced_class(n, fam)}"
    refused = 0
    for fam in FAMILIES:
        n = frontier(fam) + 1
        for unit in (2, 3, 6, 30, 67, 2310, 4):
            try:
                assert_unit(n, fam, unit)
                return False, f"G3 FAIL: unit {unit} accepted for {fam} n={n}"
            except ValueError:
                refused += 1
    return True, (f"G3 ok: the primitive-root K(q, n) == direct divisibility in "
                  f"both directions at all {checked} (q < 300, index, family), "
                  f"with |K| equal to the walk's, the roots of unity's and the "
                  f"order-sum's; == a vectorised walk at {big} (q, index, "
                  f"family) on primes to 2^20 (the most: {most[0]} residues at "
                  f"q = {most[1]}, {most[3]} n = {most[2]}); the derived class "
                  f"is (0, 1) at every filter -- nothing is forced -- and "
                  f"{refused} other units refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, both
    families, from small filters to each open index and the day-long ones."""
    checks = 0
    windows = [("A216666", 4, 128, 70_000, 400_000),
               ("A216666", 9, 64, 10 ** 11, 1_000_000),
               ("A216666", 11, 64, 3 * 10 ** 15, 1_000_000),
               ("A216668", 6, 128, 70_000, 400_000),
               ("A216668", 18, 64, 3 * 10 ** 11, 1_000_000),
               ("A216668", 24, 64, 10 ** 16, 1_000_000)]
    for fam, n, q2, k_lo, span in windows:
        eng = CpuEngine(n, fam, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        ps = forms(fam, n)
        # every value of every form tested for divisibility, evaluated once
        # per residue class of q (the value mod q depends on b mod q only)
        dead = {}
        for q in smalls:
            res = np.arange(q, dtype=np.int64)
            d = np.zeros(q, dtype=bool)
            for p in ps:
                d |= (_vpowmod(res + 1, p, q) - _vpowmod(res, p, q)) % q == 0
            dead[q] = d
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            hi = min(c0 + (1 << 22), k_lo + span)
            idx = np.arange(0, hi - c0, dtype=np.int64)
            ok = np.ones(idx.size, dtype=bool)
            for q in smalls:
                ok &= ~dead[q][(c0 % q + idx) % q]
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
                  f"of every sieved form tested for divisibility) on "
                  f"{len(windows)} populated windows ({checks} survivors; both "
                  f"families, filters 4 to the day-long ones, at 7e4 to 1e16)")


# Published terms a dense CPU sweep affords in a gate: A216666's a(5) = 6,524
# from a(4) = 1 (the zone by brute force) and A216668's a(6) = 369,719 and
# a(7) = 457,578 from a(5) = 296 and a(6).  Everything bigger is the GPU
# canaries'.
G5_TERMS = {"A216666": (5,), "A216668": (6, 7)}


def g5_rederive_knowns():
    """The CPU engine finds published terms of BOTH families end-to-end, and
    FIRST: the sweep starts AT the index's floor (a(n - 1), inclusive), with
    the exception zone above it covered by brute force, so the claim is
    about the line and not about a window."""
    found = []
    for fam, ns in G5_TERMS.items():
        for n in ns:
            q2 = 1024
            eng = CpuEngine(n, fam, q2=q2)
            target = KNOWN[fam][n]
            lo = floor_x(fam, n)
            pre = [x for x, r in prefix_hits(fam, n, q2, floor=n) if x >= lo]
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
    """huntlib's Miller-Rabin chain == sympy's BPSW on real candidates, both
    families (A216668's composite conditions included), and every published
    term reads its true run in both."""
    seen = 0
    for fam in FAMILIES:
        top = frontier(fam) + 3
        xs = [1, 2, 3, 4, 6, 9, 10, 12, 150, 296, 2913, 6524, 12345679,
              10 ** 12 + 39, 2 ** 64 + 13, 10 ** 15 + 37, 10 ** 20 + 30030]
        xs += [KNOWN[fam][8], KNOWN[fam][8] + 6, KNOWN[fam][8] - 6]
        for k in xs:
            a = run_length_fast(fam, k, top)
            b = oracle_run_length(fam, k, top)
            if a != b:
                return False, (f"G6 FAIL: {fam} b={k} engine run {a} != "
                               f"oracle run {b}")
            seen += 1
        for n in sorted(KNOWN[fam]):
            x = KNOWN[fam][n]
            if run_length_fast(fam, x, n) != n or oracle_run_length(fam, x, n) != n:
                return False, (f"G6 FAIL: {fam} a({n}) does not read its full "
                               f"run in both implementations")
            seen += 2
    a11 = KNOWN["A216668"][11]
    if run_length_fast("A216668", a11, 24) != 17 or run_length_fast("A216666", 1, 8) != 4 \
            or run_length_fast("A216668", 296, 8) != 5 or run_length_fast("A216668", 1, 3) != 0:
        return False, "G6 FAIL: the plateaus read wrong"
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates across both families (2^64 + 13 and 10^20 "
                  f"among them, A216668's composite conditions read the same "
                  f"way), every published term reads its full run in both, "
                  f"and the plateaus read as the entries show (b = 1 runs to "
                  f"4 on A216666, 296 to 5 and A216668's a(11) to 17)")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: the proof crossing tight to one b per (n, F), the
    ceiling huntlib's K_CEIL and above every crossing, and the last filter
    the engine can express tight to its residue list (module docstring)."""
    import difference_gpu as _gpu
    if _gpu.NRES_MAX != NRES_MAX:
        return False, (f"G10 FAIL: NRES_MAX = {NRES_MAX} here but the GPU tail "
                       f"holds {_gpu.NRES_MAX} residues a prime")
    rows = []
    for fam in FAMILIES:
        for n in range(1, n_max(fam) + 1):
            c = k_proof(n, fam)
            if c - 1 >= b_min(fam) and _max_value(fam, n, c - 1) >= MR_VALID_BELOW:
                return False, (f"G10 FAIL: the largest deterministic b for "
                               f"({n}, {fam}) leaves the deterministic MR zone")
            if _max_value(fam, n, c) < MR_VALID_BELOW:
                return False, (f"G10 FAIL: the proof crossing for ({n}, {fam}) "
                               f"is not tight: b = {c} is still deterministic")
            top = k_ceil(n, fam)
            if top != _ceiling.K_CEIL or top <= c:
                return False, f"G10 FAIL: the {fam} ceiling at n = {n} is {top}"
        if any(K_CEIL <= x for x in FOUND[fam].values()):
            return False, f"G10 FAIL: a {fam} find sits at or above the ceiling"
        nm = n_max(fam)
        if not maxkills(fam, nm) <= NRES_MAX < maxkills(fam, nm + 1):
            return False, f"G10 FAIL: {fam}'s last expressible index is not {nm}"
        if nm <= frontier(fam) + 2:
            return False, f"G10 FAIL: {fam} has too few open indices the engine can express"
        if read_max(fam) <= nm + 6:
            return False, f"G10 FAIL: {fam}'s runs are read no further than its filters"
        rows.append(f"{fam} n = {frontier(fam) + 1}: crossing b = "
                    f"{k_proof(frontier(fam) + 1, fam)}, last index {nm}")
    return True, ("G10 ok: the proof crossing is where the largest sieved "
                  "value of the index reaches the deterministic MR bound "
                  f"(3.317e24), tight to one b at every index ({'; '.join(rows)}: "
                  "every campaign classifies past it); the ceiling on the term "
                  "is huntlib's K_CEIL = %.4g on both families; the last "
                  "filter is the one whose proved kill bound (the sum of "
                  "(p - 1) over the sieved forms) fills the GPU tail's residue "
                  "list (NRES_MAX = %d), and runs are read to index %d"
                  % (K_CEIL, NRES_MAX, READ_MAX))


GATES = [g3_table_matches_divisibility, g4_cpu_matches_oracle,
         g6_run_length_matches_oracle, g10_values_stay_inside_the_mr_bound,
         g5_rederive_knowns]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        import time as _time
        for g in GATES:
            if g is g10_values_stay_inside_the_mr_bound:
                continue                # needs the GPU module
            t0 = _time.time()
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg + " [%.1fs]" % (_time.time() - t0))
    _sys.exit(_shutdown.graceful(_gates) or 0)
