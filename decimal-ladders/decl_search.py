"""decl_search.py -- the CPU engine for the decimal ladders.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is independent
in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array over
    the x line and uses no wheel at all.  The GPU engine never materialises
    the x line: it generates only the residues that survive a wheel and
    tests each one against periodic bit patterns and packed forbidden-residue
    tables.  A wheel bug on the GPU side therefore shows up as a parity
    failure rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(q,n,F) is built here by inverting the
    powers of ten; the oracle builds it by walking every residue and testing
    divisibility.  G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (x, off) pairs on
the GPU -- x = base + off with base a host-side big int and off < W, so no
machine word bounds the search (OPTIMIZATION.md 2.7, from the first commit).

WHAT IS SWEPT.  x itself, the published term (A305740's k, A153431's m), so
ONE x line serves every filter of a family: a find at filter n is the floor
of filter n + 1 on the same line -- the kill sets grow and the forced unit
may grow (7 -> 7*17 -> 7*17*19 for A305740), the cursor moves to the find
without being re-denominated.

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24, and the largest value at filter n is 10^n*x + 1.
So the classification is a PROOF below the PROOF CROSSING
k_proof(n, F) = (3.317e24 - 2)/10^n + 1 -- 3.3e11 at n = 13, 3.3e7 at
n = 17 -- and above it a strong probable-prime test; the crossing is below
every frontier from the first filter, so a DISCOVERY is proved by
CERTIFICATE from the first minute, on the structure every value has:

    V - 1 = 10^j * x

is completely factored the moment x is (10^j = 2^j 5^j), so BLS75 Theorem 1
on V - 1 proves EVERY value of a run from ONE factorization of x, at any
height, with a subproof for any prime factor of x above the deterministic
bound -- A153431's x + 1 included (V - 1 = x).  This is rule 5h's best
case; the ceiling is huntlib.ceiling.K_CEIL = 1e40, where that
certificate's worst case was measured to cost seconds.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, both families, x space and unit space; a unit that is not
forced -- or not squarefree -- is refused), G4 (CPU survivors == the
oracle's definition of a survivor on populated windows), G5 (CPU re-derives
knowns of both families end-to-end as FIRST occurrences), G6 (engine run
lengths == sympy BPSW), G10 (numeric hygiene: where the values pass the
deterministic Miller-Rabin bound, and the one measured ceiling above it).
"""

import pathlib as _pathlib
import sys as _sys
from functools import lru_cache as _lru_cache

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.ceiling import K_CEIL                             # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from decl_reference import (FAMILIES, KNOWN, family,           # noqa: E402
                            forbidden_k_residues, forced_primes, j0, mults,
                            nforms, run_length as oracle_run_length, w,
                            w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing lemma is searched over.  7, 17, 19, 23 (and
# 2 for A153431) are forced at the filters the campaigns reach; 29 needs 28
# forms, past anything reachable.  The search still runs: a unit is derived
# and never assumed.
UNIT_UPTO = 64


def m_max(fam, n):
    """The largest multiplier at filter n: 10^n.  What the top value -- the
    thing the proof crossing is measured on -- is made of."""
    family(fam)
    return 10 ** int(n)


def m_min(fam, n):
    """The smallest multiplier: 10^j0 (10 for A305740, 1 for A153431).  What
    the sieve's validity floor is measured against."""
    int(n)
    return 10 ** j0(fam)


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof, for filter n of family
    F: the deterministic Miller-Rabin bound rearranged.  The largest value
    is 10^n*x + 1, so below this x every primality decision is a PROOF.
    EXCLUSIVE; G10 pins both halves."""
    fam = family(fam)
    return (MR_VALID_BELOW - 1 - 1) // m_max(fam, n) + 1


def k_ceil(n, fam):
    """The enforced ceiling on x: huntlib.ceiling.K_CEIL (rule 5h).  V - 1 =
    10^j*x is factored once x is, so BLS75 Theorem 1 proves a whole run from
    ONE factorization of x at any height; the ceiling is where that
    certificate's worst case was measured to cost seconds.  EXCLUSIVE."""
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2, n, fam):
    """The smallest x the engines will sweep (EXCLUSIVE).  A kill by q is a
    proof of compositeness only when the value EXCEEDS q, and the smallest
    value is 10^j0*x + 1, so a sieve to q2 is valid from the first x with
    10^j0*x + 1 > q2: x > (q2 - 1)/10^j0."""
    fam = family(fam)
    return max(0, (int(q2) - 1) // m_min(fam, n))


def killed_residues(q, n, fam, unit=1):
    """K(q,n,F) = { -(10^j)^-1 mod q : j in J(F, n), q not | 10^j }.

    The algebraic construction -- one modular inverse per exponent -- as
    opposed to the oracle's walk over every residue.  Deduplicated rather
    than counted; the size is separately gated (G2b) against the order
    formula.

    UNIT SPACE.  The forced primes pin x to the class 0 mod the unit
    (every forced prime's one free residue is 0: x == 0 makes every form
    == 1 mod q), so the GPU engine sweeps x' = x / unit and the residues of
    x' that q kills are those of x carried through the map:
    x' == k * unit^-1 (mod q).  A prime OF the unit kills no x' at all and
    returns the empty list.  The map is a bijection of Z/q, so the sizes --
    the survival curve and the wheel counts -- are unchanged (G3 pins this
    against the x-space set).  `unit = 1` is x space itself.
    """
    unit = int(unit)
    q = int(q)
    if unit % q == 0:
        return []
    ks = _xkills(q, int(n), family(fam))
    if unit == 1:
        return sorted(ks)
    r, inv = unit_residue(n, fam, unit), pow(unit, -1, q)
    return sorted({((k - r) * inv) % q for k in ks})


@_lru_cache(maxsize=None)
def _mults(n, fam):
    return tuple(mults(fam, n))


def _xkills(q, n, fam):
    return frozenset((-pow(m, -1, q)) % q for m in _mults(n, fam) if m % q)


def _free(q, n, fam):
    """The residues of x mod q that no form kills."""
    return sorted(set(range(q)) - _xkills(int(q), int(n), family(fam)))


def forced_unit(n, fam, upto=UNIT_UPTO):
    """The product of the primes FORCED at filter n -- those that leave x
    exactly one residue class.  Derived per filter and never stored: it
    GROWS with the filter (7, then 7*17 at n = 16, then 7*17*19 at n = 18
    for A305740; the same times 2, one filter sooner, for A153431)."""
    u = 1
    for q in primerange(2, upto):
        if len(_free(q, n, fam)) == 1:
            u *= q
    return u


def unit_residue(n, fam, unit):
    """r with x == r (mod unit) for every x that survives the primes of
    `unit` -- the CRT of their single free classes.  0 here at every filter
    (a forced prime's free class is 0), derived rather than assumed and
    asserted by G3."""
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


def assert_unit(n, fam, unit):
    """Raise unless `unit` is SQUAREFREE and every prime factor of it is
    forced at filter n.

    A unit that is not forced is a COVERAGE bug, not an inefficiency: an
    engine sweeping x = unit*x' would never look at the x that are not
    multiples of unit, and if some of those survive the sieve it has
    silently thinned the line it claims to have swept.  Squarefree for the
    same reason: forcing says q | x, never q^2 | x.
    """
    fam = family(fam)
    unit = int(unit)
    if unit < 1:
        raise ValueError(f"unit {unit} is not a positive integer")
    for q in primerange(2, UNIT_UPTO):
        if unit % q == 0 and len(_free(q, n, fam)) != 1:
            raise ValueError(
                f"unit {unit} is not admissible at filter n = {n} of {fam}: "
                f"{q} leaves {len(_free(q, n, fam))} of {q} residues there, "
                f"so x need not be a multiple of {q} and an engine sweeping "
                f"x = {unit}*x' would skip line it claims to cover; the "
                f"largest admissible unit here is {forced_unit(n, fam)}")
        if unit % (q * q) == 0:
            raise ValueError(
                f"unit {unit} is not squarefree: forcing says {q} | x, never "
                f"{q}^2 | x, so an engine sweeping x = {unit}*x' would skip "
                f"the x == {q} (mod {q * q}) it claims to cover")
    rest = unit
    for q in primerange(2, UNIT_UPTO):
        while rest % q == 0:
            rest //= q
    if rest != 1:
        raise ValueError(f"unit {unit} has a prime factor above {UNIT_UPTO}, "
                         f"which nothing forces")
    return unit


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
                f"{k_floor(self.q2, self.n, self.fam)}: the smallest value is "
                f"10^j0*x + 1 and a kill by q <= q2 = {self.q2} is only a "
                f"proof of compositeness once that value exceeds q")
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
                # Python ints: the answers are absolute x and this engine is
                # the parity reference for a range that runs past 2^64
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
        """The largest index r <= cap (the filter by default) whose
        condition x = k meets, by huntlib's Miller-Rabin: a proof below
        k_proof(n, F), a thirteen-base strong probable-prime chain above it
        (where a DISCOVERY is proved by certificate instead)."""
        cap = self.n if cap is None else min(int(cap), self.n)
        j = j0(self.fam)
        while j <= cap and mr_is_prime(10 ** j * k + 1):
            j += 1
        return j - 1

    def hunt(self, k_lo, k_hi, cap=None):
        """[(x, run)] for every survivor whose run reaches the filter n."""
        out = []
        for chunk in self.survivors(k_lo, k_hi):
            for k in chunk:
                r = self.run_length(int(k), cap=cap)
                if r >= self.n:
                    out.append((int(k), r))
        return out


# --------------------------------- gates -----------------------------------

def g3_table_matches_divisibility():
    """The constructed killed set must equal direct divisibility, BOTH ways,
    for both families; the unit-space map must carry it exactly; a unit
    that is not forced, or not squarefree, is refused."""
    for fam in FAMILIES:
        for n in (5, 9, 12, 13, 16, 17, 18, 20):
            ms = mults(fam, n)
            for q in primerange(2, 300):
                built = set(killed_residues(q, n, fam))
                direct = forbidden_k_residues(q, n, fam)
                if built != direct:
                    return False, (f"G3 FAIL: {fam} n={n} q={q} "
                                   f"built={sorted(built)} "
                                   f"direct={sorted(direct)}")
                if len(built) != w_count(q, n, fam) or len(built) != w(q, n, fam):
                    return False, (f"G3 FAIL: {fam} n={n} q={q}: "
                                   f"{len(built)} residues built, w_count "
                                   f"{w_count(q, n, fam)}, w {w(q, n, fam)}")
                for u in built:                 # and the kill is a real kill
                    if not any((m * u + 1) % q == 0 for m in ms):
                        return False, (f"G3 FAIL: {fam} n={n} q={q} residue "
                                       f"{u} kills nothing")
    checked = 0
    units = {}
    for fam in FAMILIES:
        for n in (6, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22):
            unit = forced_unit(n, fam)
            assert_unit(n, fam, unit)
            units[(fam, n)] = unit
            if unit_residue(n, fam, unit) != 0:
                return False, (f"G3 FAIL: {fam} n={n}: the forced class is "
                               f"{unit_residue(n, fam, unit)} mod {unit}, "
                               f"not 0")
            for q in primerange(2, 300):
                kp = set(killed_residues(q, n, fam, unit))
                direct = forbidden_k_residues(q, n, fam)
                if unit % q == 0:
                    if kp:
                        return False, (f"G3 FAIL: {fam} n={n} unit {unit}: q={q} "
                                       f"divides the unit but kills {sorted(kp)}")
                    continue
                back = {(unit * u) % q for u in kp}
                if back != direct or len(kp) != len(direct):
                    return False, (f"G3 FAIL: {fam} n={n} unit {unit} q={q}: "
                                   f"unit-space kills map to {sorted(back)}, "
                                   f"x-space kills are {sorted(direct)}")
                checked += 1
    want = {("A305740", 13): 7, ("A305740", 16): 119, ("A305740", 18): 2261,
            ("A305740", 22): 2261 * 23, ("A153431", 14): 14,
            ("A153431", 15): 238, ("A153431", 17): 4522,
            ("A153431", 22): 4522 * 23}
    for key, u in want.items():
        if units[key] != u:
            return False, f"G3 FAIL: the forced unit at {key} is {units[key]}, not {u}"
    refused = 0
    for fam, n, unit in (("A305740", 13, 14), ("A305740", 13, 49),
                         ("A305740", 15, 119), ("A305740", 17, 2261),
                         ("A305740", 18, 10), ("A153431", 14, 28),
                         ("A153431", 14, 238), ("A153431", 16, 4522),
                         ("A153431", 17, 30), ("A305740", 13, 3)):
        try:
            assert_unit(n, fam, unit)
            return False, (f"G3 FAIL: unit {unit} accepted at n = {n} of "
                           f"{fam}, where it is not forced")
        except ValueError:
            refused += 1
    return True, ("G3 ok: constructed K(q,n,F) == direct divisibility in both "
                  "directions, every prime q < 300 at n = 5..20 and both "
                  f"families, sizes equal to the order formula; in unit space "
                  f"({checked} (q, n, unit, F) cases) the x' kills map back "
                  f"exactly onto the x kills, the unit's own primes kill "
                  f"nothing and the forced class is 0 at every filter, with "
                  f"units 7 / 119 / 2261 (A305740) and 14 / 238 / 4522 "
                  f"(A153431) as stated; {refused} inadmissible units (a "
                  f"prime one filter early, a square, 10, 30, 3) are refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, both families.
    The oracle's notion of a survivor is the definition: no value
    10^j*x + 1 has a prime factor q <= q2."""
    checks = 0
    for fam, n, q2, k_lo, span in (("A305740", 6, 128, 70_000, 400_000),
                                   ("A305740", 9, 64, 2_000_000, 4_000_000),
                                   ("A305740", 14, 32, 50_000_000, 4_000_000),
                                   ("A153431", 7, 128, 70_000, 400_000),
                                   ("A153431", 15, 32, 30_000_000, 4_000_000),
                                   ("A305740", 18, 32, 30_000_000, 4_000_000),
                                   ("A153431", 17, 32, 30_000_000, 4_000_000)):
        eng = CpuEngine(n, fam, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            ks = np.arange(c0, min(c0 + (1 << 22), k_lo + span), dtype=np.int64)
            ok = np.ones(ks.size, dtype=bool)
            for m in mults(fam, n):
                for q in smalls:
                    # q | m*x + 1, decided on residues (int64 lines)
                    ok &= ((ks % q) * (m % q) + 1) % q != 0
            want.update(int(x) for x in ks[ok].tolist())
        if got != want:
            bad = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: {fam} n={n} window {k_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {bad}")
        if not want:
            return False, (f"G4 FAIL: {fam} n={n} window is empty -- vacuous")
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on 7 populated "
                  f"windows ({checks} survivors; both families, n = 6 to 18)")


# The largest knowns of each family that a dense CPU sweep to their x
# affords in a gate, re-derived end to end.
G5_TERMS = {"A305740": (6, 7, 8), "A153431": (6, 7)}


def g5_rederive_knowns():
    """The CPU engine finds published terms of BOTH families end-to-end, and
    FIRST.  The prefix below the engine floor is covered by the oracle."""
    from decl_reference import first_x
    found = []
    for fam, ns in G5_TERMS.items():
        for n in ns:
            q2 = 1024
            eng = CpuEngine(n, fam, q2=q2)
            lo = k_floor(q2, n, fam) + 1
            target = KNOWN[fam][n]
            if first_x(fam, n, lo=1, hi=lo - 1) is not None:
                return False, f"G5 FAIL: {fam} a({n}) is below the engine floor"
            hits = eng.hunt(lo, target + 1)
            firsts = [k for k, r in hits if r >= n]
            if not firsts or min(firsts) != target:
                return False, (f"G5 FAIL: {fam} least x with run >= {n} came "
                               f"out {min(firsts) if firsts else None}, "
                               f"expected {target}")
            found.append(f"{fam} a({n})")
    return True, ("G5 ok: CPU engine re-derived " + ", ".join(found) +
                  " end-to-end as FIRST occurrences, with the sub-floor prefix "
                  "cleared by the oracle")


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW on real candidates,
    capped at the filter in this engine; every frontier term reaches its
    filter in both; the riders read whole in the oracle."""
    seen = 0
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        for n in (10, 12, 15, 17):
            eng = CpuEngine(n, fam, q2=2048)
            xs = [max(1, KNOWN[fam][top] // 7), 4, 2910, 12345678,
                  10 ** 12 + 39, KNOWN[fam][top], 170926]
            for k in xs:
                a = eng.run_length(k)
                b = min(oracle_run_length(fam, k, cap=n), n)
                if a != b:
                    return False, (f"G6 FAIL: {fam} n={n} x={k} engine run {a} "
                                   f"!= oracle run {b}")
                seen += 1
        for n in sorted(KNOWN[fam]):
            if n < 6:
                continue
            eng = CpuEngine(n, fam, q2=64)
            x = KNOWN[fam][n]
            if eng.run_length(x) < n or oracle_run_length(fam, x, cap=n) != n:
                return False, (f"G6 FAIL: {fam} a({n}) does not reach run {n} "
                               f"in both implementations")
            seen += 1
    # the rider A153431 a(6) = a(7) = 170926: 6 at filter 6, 7 at 7 and in
    # the oracle; and A153431's run counts x + 1 as index 0 (170716 + 1 is
    # composite, so -1)
    x = KNOWN["A153431"][6]
    if (CpuEngine(6, "A153431", q2=64).run_length(x) != 6
            or CpuEngine(7, "A153431", q2=64).run_length(x) != 7
            or oracle_run_length("A153431", x, cap=20) != 7):
        return False, ("G6 FAIL: the rider a(6) = a(7) of A153431 is not "
                       "capped at the filter by the engine and read whole by "
                       "the oracle")
    if oracle_run_length("A153431", 170716, cap=20) != -1 or \
            oracle_run_length("A305740", 170716, cap=20) != 6:
        return False, ("G6 FAIL: A305740's a(6) = 170716 does not read run 6 "
                       "there and -1 in A153431 (170717 = 43 * 3970 + 7 ...)")
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates including every published term at its own "
                  f"filter; the engine caps at the filter and the oracle "
                  f"runs the chain on (A153431's rider a(6) = a(7) reads 6, "
                  f"7, 7), and A153431's run counts x + 1 as index 0")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: the proof crossing is the deterministic bound
    rearranged, tight to one x, per (n, F); the ceiling is huntlib's
    measured K_CEIL for both families, above every crossing; and each
    frontier's wall is composite in the engine's own chain."""
    from decl_reference import FOUND
    for fam in FAMILIES:
        for n in range(j0(fam), 31):
            c = k_proof(n, fam)
            mm = m_max(fam, n)
            if mm * (c - 1) + 1 >= MR_VALID_BELOW:
                return False, ("G10 FAIL: the largest deterministic x for "
                               "(n, F) = (%d, %s) leaves the deterministic "
                               "MR zone" % (n, fam))
            if mm * c + 1 < MR_VALID_BELOW:
                return False, ("G10 FAIL: the proof crossing for (n, F) = "
                               "(%d, %s) is %.4g but x = %.4g would still be "
                               "deterministic" % (n, fam, c, c))
            top = k_ceil(n, fam)
            if top != K_CEIL:
                return False, f"G10 FAIL: the {fam} ceiling at n = {n} is not K_CEIL"
            if top <= c:
                return False, f"G10 FAIL: the {fam} ceiling at n = {n} is under its crossing"
            if mm * (top - 1) + 1 < MR_VALID_BELOW:
                return False, f"G10 FAIL: at the {fam} ceiling the top value is deterministic"
        if k_proof(25, fam) != 1 or k_proof(24, fam) <= 1:
            return False, (f"G10 FAIL: the {fam} crossing should reach x = 1 "
                           f"exactly at n = 25, where 10^25 passes the bound")
        if any(K_CEIL <= x for x in FOUND[fam].values()):
            return False, f"G10 FAIL: a {fam} find sits at or above K_CEIL"
        top = max(KNOWN[fam])
        x = KNOWN[fam][top]
        if mr_is_prime(10 ** (top + 1) * x + 1):
            return False, (f"G10 FAIL: {fam}'s frontier term's next value is "
                           f"prime, so a({top + 1}) would not be open")
        if k_proof(top + 1, fam) > x:
            return False, (f"G10 FAIL: {fam}'s crossing at the opening filter "
                           f"is above the frontier -- the docstring says the "
                           f"certificate is the path from the first minute")
    return True, ("G10 ok: the proof crossing IS the deterministic MR bound "
                  "(3.317e24) rearranged, tight to one x, for every filter to "
                  "n = 30 of both families -- x < %.4g at n = 13 and %.4g at "
                  "n = 17 (m_max = 10^n), below every frontier, and x = 1 "
                  "from n = 25 -- so a discovery is always a certificate; the "
                  "ceiling is ONE number, huntlib.ceiling.K_CEIL = %.4g, above "
                  "every crossing; each frontier's wall is composite in the "
                  "engine's own chain"
                  % (k_proof(13, "A305740"), k_proof(17, "A305740"), K_CEIL))


GATES = [g3_table_matches_divisibility, g4_cpu_matches_oracle,
         g6_run_length_matches_oracle, g10_values_stay_inside_the_mr_bound,
         g5_rederive_knowns]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
