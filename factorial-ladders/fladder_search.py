"""fladder_search.py -- the CPU engine for the factorial ladders.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is independent
in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array over
    the x line and uses no wheel at all.  The GPU engine never materialises
    the x line: it generates only the residues that survive a wheel and
    tests each one against packed forbidden-residue tables, bailing out at
    the first kill.  A wheel bug on the GPU side therefore shows up as a
    parity failure rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(q,n,F) is built here by inverting and
    negating the multipliers; the oracle builds it by walking every residue
    and testing divisibility.  G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (x, off) pairs on
the GPU -- x = base + off with base a host-side big int and off < W, so no
machine word bounds the search (OPTIMIZATION.md 2.7, from the first commit).

WHAT IS SWEPT.  x itself: the published term is x, with no multiplier in
front of it, so ONE x line serves every filter.  A find at filter n is the
floor of filter n + 1 on the same line -- the wheel grows (more killed
residues), the unit does not (6 at every n >= 2, fladder_reference), and
the cursor moves to the find without being re-denominated.

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24, and the largest value at filter n is n!*x + s --
the k = n form.  So the classification is a PROOF below the PROOF CROSSING
k_proof(n, F) = (3.317e24 - 1 - s)/n! + 1 -- 8.3e16 at n = 11, 1.6e13 at
n = 14, 2.5e12 at n = 15, 9.3e9 at n = 17, and x = 1 from n = 25, where
25! alone exceeds the bound -- and above it the same seven-base chain is a
strong probable-prime test: excellent evidence, not a proof.  That is where
the CERTIFICATE takes over, on BOTH signs: every value is V = k!*x + s, so

    V - s = k! * x

is completely factored the moment x is (k! is k-smooth by construction),
and BLS75 Theorem 1 on V - 1 (A177014) or Theorem 15 on V + 1 (A177013)
proves EVERY value of a discovery from ONE factorization of x, at any
height, with a subproof for any prime factor of x above the deterministic
bound.  This is rule 5h's best case: no value size bounds x, and what does
is the COST of that certificate, which huntlib.ceiling measured and pins as
K_CEIL = 1e40 for both families.  G10 pins the crossing per (n, F) and the
ceiling.  The crossing is so low here that the certificate is the normal
path from the first night: the modelled median for a(15) is 7e16 against
a crossing of 2.5e12.

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
from math import factorial

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.ceiling import K_CEIL                             # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from fladder_reference import (FAMILIES, KNOWN, family,        # noqa: E402
                               forbidden_k_residues, forced_primes, mults,
                               run_length as oracle_run_length, rung, sign,
                               w, w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing lemma is searched over.  Only 2 and 3 are
# ever forced here (Wilson: 1! == (q-2)! mod q for q >= 5, so no larger
# prime's kill set can be all of (Z/q)^*), and G2c proves it to q < 200;
# the search still runs, because a unit is derived and never assumed.
UNIT_UPTO = 64


def m_max(fam, n):
    """The largest multiplier at filter n: n!, the k = n form.  What the top
    value -- the thing the proof crossing is measured on -- is made of."""
    family(fam)
    return factorial(int(n))


def m_min(fam, n):
    """The smallest multiplier: 1! = 1, the k = 1 form, at every filter.
    What the sieve's validity floor is measured against."""
    family(fam)
    int(n)
    return 1


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof, for filter n of family
    F -- the deterministic Miller-Rabin bound rearranged.

    The largest value formed is n!*x + s, so below this x every value is
    under MR_VALID_BELOW and every primality decision the hunt makes --
    census, NEAR, discovery -- is a PROOF.  At or above it the same
    seven-base chain is a strong probable-prime test.

    EXCLUSIVE, like every other bound in the engines: k_proof - 1 is the
    largest x whose top value stays under the bound.  G10 pins both halves,
    because a bound derived by formula fails by one or not at all.
    """
    fam = family(fam)
    return (MR_VALID_BELOW - 1 - sign(fam)) // m_max(fam, n) + 1


def k_ceil(n, fam):
    """The enforced ceiling on x: huntlib.ceiling.K_CEIL, the height below
    which a worst-case CERTIFICATE per discovery is measured to cost seconds
    -- the same number for both families and both signs (rule 5h).

    Above the proof crossing a discovery is proved by certificate on its own
    structure: V - s = k!*x is completely factored once x is, because k! is
    k-smooth, so BLS75 Theorem 1 on V - 1 (s = +1) or Theorem 15 on V + 1
    (s = -1) proves every one of the n values from ONE factorization, with a
    subproof for any prime factor of x past the deterministic bound.  `n`
    and `fam` stay in the signature because the ceiling is a property of the
    family's certificate route, which G10 checks per (n, F).

    EXCLUSIVE: k_ceil - 1 is the largest x that may be swept.
    """
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2, n, fam):
    """The smallest x the engines will sweep (EXCLUSIVE).

    A kill by q is only a proof of compositeness when the value EXCEEDS q,
    and the smallest value at every filter is the k = 1 form, x + s, so a
    sieve to q2 is valid exactly from the first x with x + s > q2.  Unlike
    the lcm ladders (whose smallest multiplier was L/n, making the zone a
    handful of x) this floor is q2 itself at EVERY filter, and the oracle
    covers the prefix by brute force.
    """
    fam = family(fam)
    mm = m_min(fam, n)
    return max(0, (int(q2) - sign(fam)) // mm)


def killed_residues(q, n, fam, unit=1):
    """K(q,n,F) = { -s * m^-1 mod q : m in mults(F, n), q not | m }.

    The algebraic construction -- one modular inverse per multiplier -- as
    opposed to the oracle's walk over every residue.  Deduplicated rather
    than counted, because relying on a proof for a data-structure invariant
    is how one gets a silent off-by-one; the size is separately gated (G2b)
    against the count.

    UNIT SPACE.  The forcing lemma makes every candidate a multiple of the
    forced modulus (6 from n = 2), so the GPU engine sweeps x' = x / unit
    with the residues q kills those of x':  q | m*unit*x' + s
    <=> x' == -s * (unit*m)^-1 (mod q), for q not dividing unit*m.  A prime
    OF the unit kills nothing (every value is == s mod q, which is why it
    could be forced) and returns the empty list.  Multiplication by unit^-1
    is a bijection of (Z/q)^*, so the sizes -- hence the survival curve and
    the wheel counts -- are unchanged (G3 pins this against the x-space
    set).  `unit = 1` is x space itself.  Whether a unit is ADMISSIBLE at a
    filter is `assert_unit`'s job, not this function's.
    """
    fam = family(fam)
    s = sign(fam)
    unit = int(unit)
    if unit % q == 0:
        return []
    return sorted({(-s * pow(m * unit, -1, q)) % q
                   for m in mults(fam, n) if (m * unit) % q})


def forced_unit(n, fam, upto=UNIT_UPTO):
    """The product of the primes FORCED at filter n -- those q with
    w(q,n) = q - 1, so that only x == 0 (mod q) survives.

    2 at n = 1 and 6 at every n >= 2 (fladder_reference G2c), and derived
    here rather than stored, because a unit is a coverage claim and the
    cheapest mistake in a copied engine is a unit inherited from a problem
    that forced something else.
    """
    u = 1
    for q in primerange(2, upto):
        if len(killed_residues(q, n, fam)) == q - 1:
            u *= q
    return u


def assert_unit(n, fam, unit):
    """Raise unless `unit` is SQUAREFREE and every prime factor of it is
    forced at filter n.

    A unit that is not forced is a COVERAGE bug, not an inefficiency: an
    engine sweeping x = unit*x' would never look at the x that are not
    multiples of unit, and if some of those survive the sieve it has
    silently thinned the line it claims to have swept.  So the check is
    against the definition (the killed set is all of (Z/q)^*), per prime of
    the unit, and it raises.  Squarefree for the same reason: forcing says
    q | x, never q^2 | x, so a unit of 4 or 12 would skip x == 2 (mod 4).
    """
    fam = family(fam)
    unit = int(unit)
    if unit < 1:
        raise ValueError(f"unit {unit} is not a positive integer")
    for q in primerange(2, UNIT_UPTO):
        if unit % q == 0 and len(killed_residues(q, n, fam)) != q - 1:
            raise ValueError(
                f"unit {unit} is not admissible at filter n = {n} of {fam}: "
                f"{q} kills {len(killed_residues(q, n, fam))} of {q} residues "
                f"there, not {q - 1}, so x need not be a multiple of {q} and "
                f"an engine sweeping x = {unit}*x' would skip line it claims "
                f"to cover; the largest admissible unit here is "
                f"{forced_unit(n, fam)}")
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
        self.s = sign(self.fam)
        self.q2 = q2
        self.primes = list(primerange(2, q2 + 1))
        self.table = {q: killed_residues(q, n, self.fam) for q in self.primes}
        self.marks_per_k = sum(len(v) / q for q, v in self.table.items())

    # ---------------------------------------------------------------- sieve
    def survivors(self, k_lo, k_hi, block=1 << 22):
        """Yield lists of the x in [k_lo, k_hi) that no prime q <= q2 kills.

        The bounds are checked EAGERLY, here, and the generator is a separate
        function -- a `yield` anywhere in this body would defer every check
        to the first `next()`, so a caller that built the generator and never
        iterated it would sail past both ceilings in silence.
        """
        if k_hi > k_ceil(self.n, self.fam):
            raise ValueError(f"x {k_hi} past the enforced ceiling "
                             f"{k_ceil(self.n, self.fam)}")
        if k_lo <= k_floor(self.q2, self.n, self.fam):
            raise ValueError(
                f"engines refuse to run at or below "
                f"{k_floor(self.q2, self.n, self.fam)}: the smallest value is "
                f"x + s and a kill by q <= q2 = {self.q2} is only a proof of "
                f"compositeness once that value exceeds q")
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
                # Python ints, not u64: the sieve's own arithmetic is on
                # OFFSETS into the block and stays small, but the answers are
                # absolute x and this engine is the parity reference for a
                # range that runs past 2^64.
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
        """Largest r <= cap with every form up to index r prime at x = k.

        Capped at the FILTER by default: a filter-n sweep sieved for n
        conditions and this engine speaks about those.  (The oracle's
        run_length runs the chain on, which is how a rider is decided.)  A
        proof below k_proof(n, F) and a seven-base strong probable-prime
        chain above it, where a DISCOVERY is proved by certificate instead
        -- see the module docstring and G10.
        """
        cap = self.n if cap is None else min(int(cap), self.n)
        r = 0
        while r < cap and mr_is_prime(rung(self.n, r + 1) * k + self.s):
            r += 1
        return r

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
    for both families.

    One direction stops the engine emitting a candidate it should have
    killed; the other stops it killing one it should have kept, which is the
    failure a parity gate between two engines sharing the construction could
    never see.
    """
    for fam in FAMILIES:
        s = sign(fam)
        for n in (5, 9, 11, 13, 16, 17, 20):
            ms = mults(fam, n)
            for q in primerange(2, 300):
                built = set(killed_residues(q, n, fam))
                direct = forbidden_k_residues(q, n, fam)
                if built != direct:
                    return False, (f"G3 FAIL: {fam} n={n} q={q} "
                                   f"built={sorted(built)} "
                                   f"direct={sorted(direct)}")
                if len(built) != w_count(q, n) or len(built) != w(q, n, fam):
                    return False, (f"G3 FAIL: {fam} n={n} q={q}: "
                                   f"{len(built)} residues built, w_count "
                                   f"{w_count(q, n)}, w {w(q, n, fam)}")
                for u in built:                 # and the kill is a real kill
                    if not any((m * u + s) % q == 0 for m in ms):
                        return False, (f"G3 FAIL: {fam} n={n} q={q} residue "
                                       f"{u} kills nothing")
    # UNIT SPACE: the x' residues q kills, mapped back through x = unit*x',
    # must be exactly the x residues q kills that are multiples of unit --
    # both directions -- and the same size; a prime of the unit kills no x'
    # at all; and a unit that is not forced is refused.
    checked = 0
    units = {}
    cases = [(fam, n, forced_unit(n, fam))
             for fam in FAMILIES for n in (1, 2, 10, 11, 12, 15, 16, 17, 18,
                                           20, 24)]
    for fam, n, unit in cases:
        assert_unit(n, fam, unit)
        units[n] = unit
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
    if units[1] != 2 or any(units[n] != 6 for n in units if n >= 2):
        return False, f"G3 FAIL: the forced units came out {units}"
    # The traps this project has: a unit inherited from a problem that
    # forced more (30, 30030), a unit with a prime nothing forces here (10,
    # 5 is never forced), and a unit that is not squarefree (4, 12: forcing
    # says 2 | x, never 4 | x).  Each must be refused, at every filter.
    refused = 0
    for fam in FAMILIES:
        for n, unit in ((11, 30), (16, 30030), (17, 10), (15, 4), (18, 12),
                        (1, 6), (20, 42)):
            try:
                assert_unit(n, fam, unit)
                return False, (f"G3 FAIL: unit {unit} accepted at n = {n} of "
                               f"{fam}, where it is not forced")
            except ValueError:
                refused += 1
    return True, ("G3 ok: constructed K(q,n,F) == direct divisibility in both "
                  "directions, every prime q < 300 at n = 5, 9, 11, 13, 16, "
                  "17, 20 and both families, with |K| equal to w_count and "
                  f"to w; in unit space ({checked} (q, n, unit, F) cases at "
                  "n = 1..24) the x' kills map back exactly onto the x kills "
                  "and the unit's own primes kill nothing, with the unit 2 at "
                  f"n = 1 and 6 at every n >= 2; {refused} inadmissible units "
                  "(30, 30030, 10, 42, 6 at n = 1, and the non-squarefree 4 "
                  "and 12) are refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, both families.

    The oracle's notion of a survivor is the definition: no value m*x + s has
    a prime factor q <= q2 (excluding the value that IS q, which
    k_lo > k_floor rules out).
    """
    checks = 0
    for fam, n, q2, k_lo, span in (("A177013", 5, 128, 70_000, 400_000),
                                   ("A177013", 9, 64, 2_000_000, 4_000_000),
                                   ("A177013", 15, 32, 50_000_000, 4_000_000),
                                   ("A177014", 6, 128, 70_000, 400_000),
                                   ("A177014", 16, 32, 30_000_000, 4_000_000),
                                   ("A177014", 17, 32, 30_000_000, 4_000_000),
                                   ("A177013", 18, 32, 30_000_000, 4_000_000)):
        eng = CpuEngine(n, fam, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        s = sign(fam)
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            ks = np.arange(c0, min(c0 + (1 << 22), k_lo + span), dtype=np.int64)
            ok = np.ones(ks.size, dtype=bool)
            for m in mults(fam, n):
                for q in smalls:
                    # q | m*x + s, tested on residues: 18! is a 16-digit
                    # integer and an object-dtype product over the window
                    # took a minute for what is one int64 line per prime
                    ok &= ((ks % q) * (m % q) + s) % q != 0
            want.update(int(x) for x in ks[ok].tolist())
        if got != want:
            bad = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: {fam} n={n} window {k_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {bad}")
        if not want:
            return False, (f"G4 FAIL: {fam} n={n} window is empty -- vacuous "
                           f"check")
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on 7 populated "
                  f"windows ({checks} survivors; both families, n = 5 to 18)")


# The largest knowns of each family that a dense CPU sweep to their x
# affords in a gate, re-derived end to end.
G5_TERMS = {"A177013": (6, 8, 9), "A177014": (6, 7, 8)}


def g5_rederive_knowns():
    """The CPU engine finds published terms of BOTH families end-to-end, and
    FIRST.  The prefix below the engine floor is covered by the oracle, so
    the claim is about the line and not about a window."""
    from fladder_reference import first_x
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
    """huntlib's Miller-Rabin chain == sympy's BPSW, on real candidates --
    capped at the filter in this engine, so the comparison caps the oracle
    the same way; and every frontier term reaches its filter in both."""
    seen = 0
    for fam in FAMILIES:
        for n in (10, 11, 15, 17):
            eng = CpuEngine(n, fam, q2=2048)
            xs = [max(1, KNOWN[fam][10] // 7), 3, 2910, 12345678,
                  10 ** 12 + 39, KNOWN[fam][10]]
            for k in xs:
                a = eng.run_length(k)
                b = min(oracle_run_length(fam, k, cap=n), n)
                if a != b:
                    return False, (f"G6 FAIL: {fam} n={n} x={k} engine run {a} "
                                   f"!= oracle run {b}")
                seen += 1
        # and every frontier term, at its own filter, must reach it
        for n in sorted(KNOWN[fam]):
            if n < 5:
                continue
            eng = CpuEngine(n, fam, q2=64)
            x = KNOWN[fam][n]
            if eng.run_length(x) != n or oracle_run_length(fam, x, cap=n) != n:
                return False, (f"G6 FAIL: {fam} a({n}) does not reach run {n} "
                               f"in both implementations")
            seen += 1
    # the cap is the filter: the rider a(9) = a(10) of A177014 reads 9 at
    # filter 9 and 10 at filter 10 in this engine, and 10 in the oracle
    x = KNOWN["A177014"][9]
    if (CpuEngine(9, "A177014", q2=64).run_length(x) != 9
            or CpuEngine(10, "A177014", q2=64).run_length(x) != 10
            or oracle_run_length("A177014", x, cap=20) != 10):
        return False, ("G6 FAIL: the rider a(9) = a(10) of A177014 is not "
                       "capped at the filter by the engine and read whole by "
                       "the oracle")
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates including every published term at its own "
                  f"filter; the engine caps at the filter and the oracle "
                  f"runs the chain on (A177014's rider reads 9, 10, 10)")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: state the bounds and pin where they are crossed.

    The deterministic Miller-Rabin bound is a property of the VALUES, not of
    x.  Here the largest value is n!*x + s, so the PROOF CROSSING
    k_proof(n, F) is that bound rearranged, and the claim to check is "it is
    exactly as high as the proof allows, and not one x higher" -- both
    halves, per (n, F).

    Then the CEILING.  It is huntlib.ceiling's measured K_CEIL for both
    families and both signs; it sits above every crossing the campaigns can
    reach (so the certificate is load-bearing at the top of the range, not
    decorative), and at the ceiling the largest value is past the
    deterministic bound on both families.

    Note how LOW the crossing is here: m_max is n!, which is 4.0e7 at n = 11
    and 3.6e14 at n = 17, so the campaign crosses into certificate territory
    at x = 8.3e16 (n = 11), 2.5e12 (n = 15) and 9.3e9 (n = 17) -- below the
    modelled median at every filter from n = 14 on -- and from n = 25 the
    crossing is x = 1, because 25! alone exceeds the bound.  The certificate
    is not an edge case in this project, it is the path.
    """
    from fladder_reference import FOUND
    for fam in FAMILIES:
        s = sign(fam)
        for n in range(1, 31):
            c = k_proof(n, fam)
            mm = m_max(fam, n)
            if mm * (c - 1) + s >= MR_VALID_BELOW:
                return False, ("G10 FAIL: the largest deterministic x for "
                               "(n, F) = (%d, %s) is %.4g and its value leaves "
                               "the deterministic MR zone" % (n, fam, c - 1))
            if mm * c + s < MR_VALID_BELOW:
                return False, ("G10 FAIL: the proof crossing for (n, F) = "
                               "(%d, %s) is %.4g but x = %.4g would still be "
                               "deterministic -- the crossing is not the bound"
                               % (n, fam, c, c))
            top = k_ceil(n, fam)
            if top != K_CEIL:
                return False, ("G10 FAIL: the %s ceiling at n = %d is %.4g, "
                               "not huntlib.ceiling.K_CEIL = %.4g"
                               % (fam, n, top, K_CEIL))
            if top <= c:
                return False, ("G10 FAIL: the %s ceiling at n = %d is under "
                               "its proof crossing %.4g -- the certificate "
                               "would be decorative" % (fam, n, c))
            if mm * (top - 1) + s < MR_VALID_BELOW:
                return False, ("G10 FAIL: at the %s ceiling the top value at "
                               "n = %d is still deterministic" % (fam, n))
        if k_proof(25, fam) != 1 or k_proof(24, fam) <= 1:
            return False, (f"G10 FAIL: the {fam} crossing should reach x = 1 "
                           f"exactly at n = 25, where 25! passes the bound")
        if any(K_CEIL <= x for x in FOUND[fam].values()):
            return False, (f"G10 FAIL: a {fam} find sits at or above K_CEIL")
    if K_CEIL - 1 < MR_VALID_BELOW:
        return False, "G10 FAIL: the ceiling is under the deterministic bound"
    # the wall that keeps each frontier open, from the engine's own chain
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        x = KNOWN[fam][top]
        if mr_is_prime(factorial(top + 1) * x + sign(fam)):
            return False, (f"G10 FAIL: {fam}'s frontier term's next value is "
                           f"prime, so a({top + 1}) would not be open")
    return True, ("G10 ok: the proof crossing IS the deterministic MR bound "
                  "(3.317e24) rearranged, tight to one x, for every filter to "
                  "n = 30 of both families -- x < %.4g at n = 11, %.4g at "
                  "n = 15 and %.4g at n = 17 (m_max = n!), and x = 1 from "
                  "n = 25 -- so this project runs on CERTIFICATES over "
                  "essentially its whole range; the ceiling is ONE number for "
                  "both families and both signs, huntlib.ceiling.K_CEIL = "
                  "%.4g, above every crossing, with the top value past the "
                  "bound at it; and each frontier's wall is composite in the "
                  "engine's own chain"
                  % (k_proof(11, "A177013"), k_proof(15, "A177013"),
                     k_proof(17, "A177013"), K_CEIL))


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
