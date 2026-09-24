"""lladder_search.py -- the CPU engine for the linear ladders.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is
independent in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array
    over the k line and uses no wheel at all.  The GPU engine never
    materialises the k line: it generates only the residues that survive a
    wheel and tests each one against packed forbidden-residue tables,
    bailing out at the first kill.  A wheel bug on the GPU side therefore
    shows up as a parity failure rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(q,n,F) is built here by inverting and
    negating the multipliers; the oracle builds it by walking every residue
    and testing divisibility.  G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (k, off) pairs on
the GPU -- k = base + off with base a host-side big int and off < W, so no
machine word bounds the search (OPTIMIZATION.md 2.7, from the first
commit).

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24, and the largest value a family forms at filter
n is m_max*k + s with m_max the largest multiplier -- n for the 1..n
families, 2n - 1 for the odd ones.  So the classification is a PROOF below
the PROOF CROSSING k_proof(n, F) = (3.317e24 - 1 - s) / m_max -- 2.2e23 at
n = 15 for A088250, 1.1e23 at n = 16 for A164325 -- and above it the same
Miller-Rabin chain is a strong probable-prime test: excellent evidence, not
a proof.  That is where the CERTIFICATE takes over, on BOTH signs (v3):
N - s = m*k is completely factored once k is (m is tiny), so BLS75
Theorem 1 on N - 1 (the +1 families) or Theorem 15 on N + 1 (the -1
families; huntlib.certificate's N+1 route, with a Lucas sequence per prime
of the factorization) proves every value of a discovery at any height, and
a prime factor of k above the deterministic bound gets a subproof of its
own by the same machinery.  So no value size bounds k; what does is the
COST of that certificate per discovery -- factoring k once and proving its
factors -- which huntlib.ceiling measured (a worst-case k, unit times a
balanced semiprime, is seconds to 1e40) and pins as K_CEIL = 1e40, ONE
ceiling for every family and both signs.  v2's ceilings were the
deterministic bound on k for the +1 families and the crossing itself for
the -1 ones (no N+1 route existed); the crossing is now a MILESTONE the
launcher logs, not a stop.  G10 pins the crossing per (n, F) and the
ceiling, so no future edit can quietly assume determinism after the
range moves.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, all families, k space and unit space; a unit that is not
forced is refused), G4 (CPU survivors == the oracle's definition of a
survivor on populated windows), G5 (CPU re-derives two knowns of every
family end-to-end as FIRST occurrences), G6 (engine run lengths == sympy
BPSW), G10 (numeric hygiene: where the values pass the deterministic
Miller-Rabin bound, and the one measured ceiling above it).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.ceiling import K_CEIL                             # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from lladder_reference import (K_FLOOR, KNOWN, FAMILIES,        # noqa: E402
                               family, forbidden_k_residues, mults, rung,
                               run_length as oracle_run_length, sign, w)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)


def m_max(fam, n):
    """The largest multiplier at filter n: what the top value is made of."""
    return rung(fam, n)


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof, for filter n of family
    F -- the deterministic Miller-Rabin bound rearranged.

    The largest value formed is m_max*k + s, so below this k every value
    is under MR_VALID_BELOW and every primality decision the hunt makes --
    census, NEAR, discovery -- is a PROOF.  At or above it the same
    Miller-Rabin chain is a strong probable-prime test.

    EXCLUSIVE, like every other bound in the engines: k_proof - 1 is the
    largest k whose top value stays under the bound.  G10 pins both halves,
    because a bound derived by formula fails by one or not at all.
    """
    fam = family(fam)
    return (MR_VALID_BELOW - 1 - sign(fam)) // m_max(fam, n) + 1


def k_ceil(n, fam):
    """The enforced ceiling on k: huntlib.ceiling.K_CEIL, the height below
    which a worst-case CERTIFICATE per discovery is measured to cost
    seconds -- the same number for every family and both signs (v3).

    Above the proof crossing a discovery is proved by certificate on its
    own structure, N - s = m*k factored once per find: BLS75 Theorem 1 on
    N - 1 for s = +1, Theorem 15 on N + 1 for s = -1, with a subproof for
    any prime factor of k past the deterministic bound.  v2 stopped the +1
    families at the deterministic bound on k (3.317e24, so that no factor
    needed a subproof) and the -1 families at the crossing (no N+1 route);
    both limits were the certificate's, not the engine's, and both are
    gone.  `n` and `fam` are kept in the signature because the ceiling is
    a property of the family's certificate route, which G10 checks per
    (n, F) -- and because a project whose route depended on n would state
    it here.

    EXCLUSIVE: k_ceil - 1 is the largest k that may be swept.
    """
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2):
    """The smallest k the engines will sweep (exclusive).

    Two separate reasons, and the larger wins.  A kill by q needs the value
    to EXCEED q, and the smallest value a family forms is 1*k + s >= k - 1
    (the r = 1 families), so a sieve to q2 is only valid from k = q2 + 2:
    the floor is q2 + 1.  K_FLOOR guards the other end, the exception zone
    where a value can BE the prime that divides it.
    """
    return max(K_FLOOR, q2 + 1)


def killed_residues(q, n, fam, unit=1):
    """K(q,n,F) = { -s * m^-1 mod q : m in mults(F, n), q not | m }.

    The algebraic construction -- one modular inverse per multiplier -- as
    opposed to the oracle's walk over every residue.  Deduplicated rather
    than counted, because relying on a proof for a data-structure invariant
    is how one gets a silent off-by-one; the size is separately gated (G2b)
    against the distinct-residue count.

    UNIT SPACE.  The forcing lemma (lladder_reference) makes every
    candidate at the campaign filters a multiple of a forced modulus, so
    the GPU engine sweeps k' = k / unit and the residues q kills are those
    of k':  q | m*unit*k' + s  <=>  k' == -s * (unit*m)^-1 (mod q), for q
    not dividing unit*m.  A prime OF the unit kills nothing (every value is
    == s mod q, which is why it could be forced) and returns the empty
    list.  Multiplication by unit^-1 is a bijection of (Z/q)^*, so the
    sizes -- hence the survival curve and the wheel counts -- are unchanged
    (G3 pins this against the k-space set).  `unit = 1` is k space itself.
    Whether a unit is ADMISSIBLE at a filter (each of its primes forced
    there) is `assert_unit`'s job, not this function's: called with a unit
    that is not forced it would quietly sieve a thinner line, which is
    exactly the failure that guard exists to catch.
    """
    fam = family(fam)
    s = sign(fam)
    unit = int(unit)
    if unit % q == 0:
        return []
    return sorted({(-s * pow(m * unit, -1, q)) % q
                   for m in mults(fam, n) if (m * unit) % q})


def forced_unit(n, fam, upto=60):
    """The product of the primes FORCED at filter n of family F -- those q
    with w(q,n,F) = q - 1, so that only k == 0 (mod q) survives (the
    forcing lemma).  The largest unit the engine may sweep in at that
    filter: 30030 for A088250 at n = 15, 510510 from n = 16."""
    u = 1
    for q in primerange(2, upto):
        if len(killed_residues(q, n, fam)) == q - 1:
            u *= q
    return u


def assert_unit(n, fam, unit):
    """Raise unless every prime factor of `unit` is forced at filter n.

    A unit that is not forced is a COVERAGE bug, not an inefficiency: an
    engine sweeping k = unit*k' would never look at the k that are not
    multiples of unit, and if some of those survive the sieve it has
    silently thinned the line it claims to have swept.  So the check is
    against the definition (the killed set is all of (Z/q)^*), per prime
    of the unit, and it raises.
    """
    fam = family(fam)
    unit = int(unit)
    if unit < 1:
        raise ValueError(f"unit {unit} is not a positive integer")
    for q in primerange(2, 60):
        if unit % q == 0 and len(killed_residues(q, n, fam)) != q - 1:
            raise ValueError(
                f"unit {unit} is not admissible at filter n = {n} of {fam}: "
                f"{q} kills {len(killed_residues(q, n, fam))} of {q} residues "
                f"there, not {q - 1}, so k need not be a multiple of {q} and "
                f"an engine sweeping k = {unit}*k' would skip line it claims "
                f"to cover; the largest admissible unit here is "
                f"{forced_unit(n, fam)}")
    rest = unit
    for q in primerange(2, 60):
        while rest % q == 0:
            rest //= q
    if rest != 1:
        raise ValueError(f"unit {unit} has a prime factor above 59, which "
                         f"nothing forces")
    return unit


class CpuEngine:
    """Segmented sieve over the dense k line, no wheel."""

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
        """Yield lists of the k in [k_lo, k_hi) that no prime q <= q2 kills.

        The bounds are checked EAGERLY, here, and the generator is a
        separate function -- a `yield` anywhere in this body would defer
        every check to the first `next()`, so a caller that built the
        generator and never iterated it would sail past both ceilings in
        silence.
        """
        if k_hi > k_ceil(self.n, self.fam):
            raise ValueError(f"k {k_hi} past the enforced ceiling "
                             f"{k_ceil(self.n, self.fam)}")
        if k_lo <= k_floor(self.q2):
            raise ValueError(
                f"engines refuse to run at or below max(K_FLOOR, q2 + 1) = "
                f"{k_floor(self.q2)}: the wheel argument has an exception "
                f"zone there and a kill by q needs value > q")
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
                # OFFSETS into the block and stays small, but the answers
                # are absolute k and this engine is the parity reference
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
    def run_length(self, k, cap=64):
        """Largest r <= cap with every form up to index r prime at k.

        A proof below k_proof(n, F) and a thirteen-base strong probable-prime
        chain above it, where a DISCOVERY is proved by certificate instead
        -- see the module docstring and G10."""
        r = FAMILIES[self.fam]["rungs_from"] - 1
        while r < cap and mr_is_prime(rung(self.fam, r + 1) * k + self.s):
            r += 1
        return r

    def hunt(self, k_lo, k_hi, cap=None):
        """[(k, run)] for every survivor whose run reaches the filter n."""
        cap = cap or self.n + 8
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
    for every family.

    One direction stops the engine emitting a candidate it should have
    killed; the other stops it killing one it should have kept, which is
    the failure a parity gate between two engines sharing the construction
    could never see.
    """
    for fam in FAMILIES:
        s = sign(fam)
        for n in (7, 10, 15, 17):
            ms = mults(fam, n)
            for q in primerange(2, 300):
                built = set(killed_residues(q, n, fam))
                direct = forbidden_k_residues(q, n, fam)
                if built != direct:
                    return False, (f"G3 FAIL: {fam} n={n} q={q} "
                                   f"built={sorted(built)} "
                                   f"direct={sorted(direct)}")
                for u in built:                 # and the kill is a real kill
                    if not any((m * u + s) % q == 0 for m in ms):
                        return False, (f"G3 FAIL: {fam} n={n} q={q} residue "
                                       f"{u} kills nothing")
    # UNIT SPACE: the k' residues q kills, mapped back through k = unit*k',
    # must be exactly the k residues q kills that are multiples of unit --
    # both directions -- and the same size; a prime of the unit kills no
    # k' at all; and a unit that is not forced is refused.
    checked = 0
    cases = (("A088250", 10, 2310), ("A088250", 15, 30030),
             ("A088250", 16, 510510), ("A088250", 18, 9699690),
             ("A173750", 16, 30030), ("A125838", 15, 30030),
             ("A125839", 16, 30030), ("A164325", 16, 30030),
             ("A164326", 15, 30030), ("A088651", 16, 510510),
             ("A088651", 12, 30030), ("A164325", 9, 210))
    for fam, n, unit in cases:
        assert_unit(n, fam, unit)
        if forced_unit(n, fam) % unit:
            return False, (f"G3 FAIL: forced_unit({n}, {fam}) = "
                           f"{forced_unit(n, fam)} is not a multiple of the "
                           f"admissible unit {unit}")
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
                               f"k-space kills are {sorted(direct)}")
            checked += 1
    refused = 0
    for fam, n, unit in (("A088250", 15, 510510), ("A088250", 11, 30030),
                         ("A173750", 13, 30030), ("A125839", 14, 30030),
                         ("A164326", 16, 510510), ("A088651", 15, 510510)):
        try:
            assert_unit(n, fam, unit)
            return False, (f"G3 FAIL: unit {unit} accepted at n = {n} of {fam}, "
                           f"where it is not forced")
        except ValueError:
            refused += 1
    return True, ("G3 ok: constructed K(q,n,F) == direct divisibility in "
                  "both directions, every prime q < 300 at n = 7, 10, 15, 17 "
                  f"and all seven families; in unit space ({checked} (q, n, "
                  "unit, F) cases at the units the campaigns open in: 30030 "
                  "at n = 15/16, 510510 for A088651 at 16 and A088250 at 16, "
                  "9699690 at 18) the k' kills map back exactly onto the k "
                  f"kills and the unit's own primes kill nothing; {refused} "
                  "units that are not forced one filter earlier are refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, several
    families.

    The oracle's notion of a survivor is the definition: no value m*k + s
    has a prime factor q <= q2 (excluding the value that IS q, which
    k_lo > q2 + 1 rules out).
    """
    checks = 0
    # The windows are WIDE because survivors are sparse here: forced
    # divisibility alone leaves one k in 30030 at n = 15, and a window that
    # comes out empty is a vacuous check, which G4 refuses.
    for fam, n, q2, k_lo, span in (("A088250", 5, 128, 70_000, 500_000),
                                   ("A088250", 10, 64, 2_000_000, 10_000_000),
                                   ("A088250", 15, 32, 50_000_000, 20_000_000),
                                   ("A125838", 6, 128, 70_000, 500_000),
                                   ("A164326", 15, 32, 30_000_000, 20_000_000),
                                   ("A173750", 16, 32, 30_000_000, 20_000_000),
                                   ("A125839", 12, 32, 30_000_000, 10_000_000)):
        eng = CpuEngine(n, fam, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        s = sign(fam)
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            ks = np.arange(c0, min(c0 + (1 << 22), k_lo + span),
                           dtype=np.int64)
            ok = np.ones(ks.size, dtype=bool)
            for m in mults(fam, n):
                v = ks * m + s
                for q in smalls:
                    ok &= (v % q) != 0
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
    return True, (f"G4 ok: engine survivors == oracle survivors on 7 "
                  f"populated windows ({checks} survivors; five families, "
                  f"n = 5 to 16)")


# The two largest knowns of each family that a dense CPU sweep to their
# value affords in a gate (under ~2e9 of line), re-derived end to end.
G5_TERMS = {"A088250": (6, 8), "A173750": (8, 9), "A125838": (8, 9),
            "A125839": (9, 11), "A164325": (6, 8), "A164326": (8,),
            "A088651": (8, 9)}


def g5_rederive_knowns():
    """The CPU engine finds two published terms of EVERY family end-to-end,
    and FIRST.  The prefix below the engine floor is covered by the oracle,
    so the claim is about the line and not about a window."""
    from lladder_reference import first_k
    found = []
    for fam, ns in G5_TERMS.items():
        for n in ns:
            eng = CpuEngine(n, fam, q2=4096)
            lo = k_floor(4096) + 1
            if first_k(fam, n, lo=1, hi=lo - 1) is not None:
                return False, f"G5 FAIL: {fam} a({n}) is below the engine floor"
            hits = eng.hunt(lo, KNOWN[fam][n] + 1)
            firsts = [k for k, r in hits if r >= n]
            if not firsts or min(firsts) != KNOWN[fam][n]:
                return False, (f"G5 FAIL: {fam} least k with run >= {n} came "
                               f"out {min(firsts) if firsts else None}, "
                               f"expected {KNOWN[fam][n]}")
            found.append(f"{fam} a({n})")
    return True, ("G5 ok: CPU engine re-derived " + ", ".join(found) +
                  " end-to-end as FIRST occurrences, with the sub-floor "
                  "prefix cleared by the oracle")


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW, on real candidates."""
    seen = 0
    for fam in FAMILIES:
        eng = CpuEngine(14, fam, q2=2048)
        top = max(KNOWN[fam])
        for k in (KNOWN[fam][top], KNOWN[fam][top - 1], KNOWN[fam][9],
                  512820, 2894220, 987654210, 30030 * 33333):
            a = eng.run_length(k, cap=18)
            b = oracle_run_length(fam, k, cap=18)
            if a != b:
                return False, (f"G6 FAIL: {fam} k={k} engine run {a} != "
                               f"oracle run {b}")
            seen += 1
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates including every frontier term")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: state the bounds and pin where they are crossed.

    The deterministic Miller-Rabin bound is a property of the VALUES, not
    of k.  Here the largest value is m_max*k + s, so the PROOF CROSSING
    k_proof(n, F) is that bound rearranged, and the claim to check is "it
    is exactly as high as the proof allows, and not one k higher" -- both
    halves, per (n, F), because a bound derived by formula fails by being
    off by one, not by being wildly wrong.

    Then the CEILING.  It is huntlib.ceiling's measured K_CEIL for every
    family and both signs; it sits above every crossing the campaigns can
    reach (so the certificate is load-bearing at the top of the range,
    not decorative), above every frontier this project has found and above
    every v2 ceiling the campaigns stopped at (so a resumed campaign
    continues rather than stopping at once); and at the ceiling the
    largest value is past the deterministic bound on every family, which
    is what the certificate drill in launch.py proves both routes at.
    """
    from lladder_reference import FOUND
    for fam in FAMILIES:
        s = sign(fam)
        for n in range(FAMILIES[fam]["first_n"], 41):
            c = k_proof(n, fam)
            mm = m_max(fam, n)
            if mm * (c - 1) + s >= MR_VALID_BELOW:
                return False, ("G10 FAIL: the largest deterministic k for "
                               "(n, F) = (%d, %s) is %.4g and its value "
                               "leaves the deterministic MR zone"
                               % (n, fam, c - 1))
            if mm * c + s < MR_VALID_BELOW:
                return False, ("G10 FAIL: the proof crossing for (n, F) = "
                               "(%d, %s) is %.4g but k = %.4g would still "
                               "be deterministic -- the crossing is not the "
                               "bound" % (n, fam, c, c))
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
        # the v2 ceilings the campaigns stopped at, and the frontiers
        v2 = MR_VALID_BELOW if s > 0 else k_proof(max(FOUND[fam]) + 1, fam)
        if K_CEIL <= v2 or any(K_CEIL <= k for k in FOUND[fam].values()):
            return False, (f"G10 FAIL: K_CEIL = {K_CEIL:.4g} does not lie "
                           f"above {fam}'s v2 ceiling {v2:.4g} and its "
                           f"frontier -- a resumed campaign would stop at "
                           f"once")
    if K_CEIL - 1 < MR_VALID_BELOW:
        return False, "G10 FAIL: the ceiling is under the deterministic bound"
    kk, ii = 11429352906540438870, 15
    if not mr_is_prime(14 * kk + 1):
        return False, "G10 FAIL: A088250's frontier term's 14th value is not prime"
    if mr_is_prime(15 * kk + 1):
        return False, "G10 FAIL: A088250's wall value tests prime"
    return True, ("G10 ok: the proof crossing IS the deterministic MR bound "
                  "(3.317e24) rearranged, tight to one k, for every filter "
                  "up to n = 40 of all seven families -- k < %.4g at n = 15 "
                  "and %.4g at n = 17 for A088250, %.4g at n = 16 for A164325 "
                  "(m_max = 31); the ceiling is ONE number for every family "
                  "and both signs, huntlib.ceiling.K_CEIL = %.4g (measured: "
                  "a worst-case certificate there is seconds), above every "
                  "crossing to n = 40, every frontier found and every v2 "
                  "ceiling, with the top value past the bound at it on every "
                  "family"
                  % (k_proof(15, "A088250"), k_proof(17, "A088250"),
                     k_proof(16, "A164325"), K_CEIL))


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
