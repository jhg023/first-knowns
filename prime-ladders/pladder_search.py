"""pladder_search.py -- the CPU engine for A084700 and A084701.

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
  * construction: the killed set K(q,n,s) is built here by inverting and
    negating the rung primes; the oracle builds it by walking every residue
    and testing divisibility.  G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (k, off) pairs on
the GPU -- k = base + off with base a host-side big int and off < W, so no
machine word bounds the search.  That is OPTIMIZATION.md 2.7, taken from
the first commit as shift-ladders did, rather than retrofitted as
square-ladders had to.

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24, and the largest value this project forms is
prime(n)*k + s -- a MULTIPLICATIVE offset of at most prime(n), which at
n = 18 is 61.  So the classification is a PROOF below the PROOF CROSSING
k_proof(n, s) = (3.317e24 - 1 - s) / prime(n) -- 5.6e22 at n = 17, 5.4e22
at n = 18 -- and above it the same Miller-Rabin chain is a strong
probable-prime test: excellent evidence, not a proof.  For A084700
(s = +1) that is where the CERTIFICATE takes over.  N - 1 = prime(i)*k is
completely factored once k is, so BLS75 Theorem 1 (huntlib.certificate)
proves every value of a discovery at any height, and the proof is ONE
LEVEL DEEP as long as every prime factor of k is itself under the
deterministic bound -- which is guaranteed while k is.  So the s = +1
ceiling is k_ceil(n, +1) = MR_VALID_BELOW on k itself, 61x the crossing
at n = 18; the campaign that hit the crossing on 2026-09-02 at 5.4e22
with a(18) still open resumes under it.  A084701's structure is on
N + 1, which needs an N+1 test huntlib does not have, so its ceiling
stays AT the crossing and every primality decision on that family is a
proof.  Raising a ceiling is a new engine version (CONVENTIONS.md
"Numeric hygiene"): this is v3, with the certificate drill in the
selftest and G10 pinning the crossing per (n, s) and both ceilings, so no
future edit can quietly assume determinism after the range moves.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, both signs), G4 (CPU survivors == the oracle's definition of a
survivor on populated windows), G5 (CPU re-derives A084700 a(8), a(9) and
A084701 a(8), a(9) end-to-end as FIRST occurrences), G6 (engine run
lengths == sympy BPSW), G10 (numeric hygiene: where the values pass the
deterministic Miller-Rabin bound, and the two ceilings that follow).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from pladder_reference import (K_FLOOR, KNOWN, FAMILIES,        # noqa: E402
                               forbidden_k_residues, rung,
                               run_length as oracle_run_length, w)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)


def k_proof(n, s):
    """Where the CLASSIFICATION stops being a proof, for a filter of n
    conditions with sign s -- the deterministic Miller-Rabin bound
    rearranged.

    The largest value this project forms is prime(n)*k + s, so below this k
    every value is under MR_VALID_BELOW and every primality decision the
    hunt makes -- census, NEAR, discovery -- is a PROOF.  At or above it
    the same Miller-Rabin chain is a strong probable-prime test.

    EXCLUSIVE, like every other bound in the engines: k_proof - 1 is the
    largest k whose top value prime(n)*(k_proof - 1) + s stays under the
    bound.  G10 pins both halves, because a bound derived by formula fails
    by one or not at all.
    """
    return (MR_VALID_BELOW - 1 - s) // rung(n) + 1


def k_ceil(n, s):
    """The enforced ceiling on k: the PRIMALITY-PROOF VALIDITY BOUND of the
    family, which is what OPTIMIZATION.md 2.7 says to pick.

    s = -1 (A084701): the proof crossing itself.  The structure there is
    N + 1 = prime(i)*k and huntlib has no N+1 test, so past k_proof nothing
    could prove a discovery; the engine stops where the proofs do.

    s = +1 (A084700): MR_VALID_BELOW, on k ITSELF.  Above the crossing a
    discovery is proved by BLS75 Theorem 1 (huntlib.certificate) on
    N - 1 = prime(i)*k, which is completely factored once k is.  Every
    prime factor of k is below k, so with k under the deterministic bound
    the certificate is ONE LEVEL DEEP: each factor is checked by the
    deterministic Miller-Rabin test and nothing recurses.  Past this k a
    factor of k could itself exceed the bound and need a subproof (huntlib.certificate
    carries them, to PROOF_DEPTH); that is a new engine version with gates
    at that height, not something this one quietly assumes.

    Both are EXCLUSIVE: k_ceil - 1 is the largest k that may be swept.
    """
    if int(s) > 0:
        return MR_VALID_BELOW
    return k_proof(n, s)


def k_floor(q2):
    """The smallest k the engines will sweep.

    Two separate reasons, and the larger wins.  A kill by q needs the value
    to EXCEED q, and the smallest value is 2k + s >= 2k - 1, so a sieve to
    q2 is only valid above k = q2.  K_FLOOR guards the other end, the
    exception zone where a value can BE the prime that divides it.
    """
    return max(K_FLOOR, q2)


def killed_residues(q, n, s, unit=1):
    """K(q,n,s) = { -s * prime(i)^-1 mod q : i = 1..n, prime(i) != q }.

    The algebraic construction -- one modular inverse per rung -- as
    opposed to the oracle's walk over every residue.  Deduplicated rather
    than counted, because relying on a proof for a data-structure invariant
    is how one gets a silent off-by-one; the size is separately gated (G2b)
    against the distinct-residue count.

    UNIT SPACE (v3).  The forcing lemma (pladder_reference) makes every
    candidate at the campaign filters a multiple of 2310, so the GPU engine
    sweeps k' = k / unit instead of k and the residues q kills are those
    of k':  q | prime(i)*unit*k' + s  <=>  k' == -s * (unit*prime(i))^-1
    (mod q), for q not dividing unit*prime(i).  A prime OF the unit kills
    nothing (every value is == s mod q, which is why it could be forced)
    and returns the empty list.  Multiplication by unit^-1 is a bijection
    of (Z/q)^*, so the sizes -- hence the survival curve and the wheel
    counts -- are unchanged (G3 pins this against the k-space set).
    `unit = 1` is k space itself.  Whether a unit is ADMISSIBLE at a filter
    (each of its primes forced there) is `assert_unit`'s job, not this
    function's: called with a unit that is not forced it would quietly
    sieve a thinner line, which is exactly the failure that guard exists
    to catch.
    """
    unit = int(unit)
    if unit % q == 0:
        return []
    return sorted({(-s * pow(rung(i) * unit, -1, q)) % q
                   for i in range(1, n + 1) if (rung(i) * unit) % q})


def forced_unit(n, s=+1):
    """The product of the primes FORCED at filter n -- those q with
    w(q,n,s) = q - 1, so that only k == 0 (mod q) survives (the forcing
    lemma): 2310 from n = 14, 210 from n = 10, 30 from n = 8.  The largest
    unit the engine may sweep in at that filter."""
    u = 1
    for q in (2, 3, 5, 7, 11, 13):
        if len(killed_residues(q, n, s)) == q - 1:
            u *= q
    return u


def assert_unit(n, s, unit):
    """Raise unless every prime factor of `unit` is forced at filter n.

    A unit that is not forced is a COVERAGE bug, not an inefficiency: an
    engine sweeping k = unit*k' would never look at the k that are not
    multiples of unit, and if some of those survive the sieve it has
    silently thinned the line it claims to have swept.  So the check is
    against the definition (the killed set is all of (Z/q)^* ), per prime
    of the unit, and it raises.
    """
    unit = int(unit)
    if unit < 1:
        raise ValueError(f"unit {unit} is not a positive integer")
    for q in primerange(2, 60):
        if unit % q == 0 and len(killed_residues(q, n, s)) != q - 1:
            raise ValueError(
                f"unit {unit} is not admissible at filter n = {n} (sign "
                f"{s:+d}): {q} kills {len(killed_residues(q, n, s))} of "
                f"{q} residues there, not {q - 1}, so k need not be a "
                f"multiple of {q} and an engine sweeping k = {unit}*k' "
                f"would skip line it claims to cover; the largest "
                f"admissible unit here is {forced_unit(n, s)}")
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

    def __init__(self, n, s, q2=Q2_DEFAULT):
        self.n = n
        self.s = int(s)
        self.q2 = q2
        self.primes = list(primerange(2, q2 + 1))
        self.table = {q: killed_residues(q, n, s) for q in self.primes}
        self.marks_per_k = sum(len(v) / q for q, v in self.table.items())
        self.ps = [rung(i) for i in range(1, n + 9)]

    # ---------------------------------------------------------------- sieve
    def survivors(self, k_lo, k_hi, block=1 << 22):
        """Yield lists of the k in [k_lo, k_hi) that no prime q <= q2 kills.

        The bounds are checked EAGERLY, here, and the generator is a
        separate function -- a `yield` anywhere in this body would defer
        every check to the first `next()`, so a caller that built the
        generator and never iterated it would sail past both ceilings in
        silence.  The ceiling drill in the selftest calls this without
        consuming it, which is exactly the case that caught it elsewhere.
        """
        if k_hi > k_ceil(self.n, self.s):
            raise ValueError(f"k {k_hi} past the enforced ceiling "
                             f"{k_ceil(self.n, self.s)}")
        if k_lo <= k_floor(self.q2):
            raise ValueError(
                f"engines refuse to run at or below max(K_FLOOR, q2) = "
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
        """Largest r <= cap with prime(i)*k + s prime for i = 1..r.

        A proof below k_proof(n, s) and a thirteen-base strong probable-prime
        chain above it, where a DISCOVERY is proved by certificate instead
        -- see the module docstring and G10."""
        r = 0
        while r < cap and mr_is_prime(rung(r + 1) * k + self.s):
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
    for BOTH signs.

    One direction stops the engine emitting a candidate it should have
    killed; the other stops it killing one it should have kept, which is
    the failure a parity gate between two engines sharing the construction
    could never see.
    """
    for s in (+1, -1):
        for n in (7, 10, 14, 17):
            for q in primerange(2, 300):
                built = set(killed_residues(q, n, s))
                direct = forbidden_k_residues(q, n, s)
                if built != direct:
                    return False, (f"G3 FAIL: s={s:+d} n={n} q={q} "
                                   f"built={sorted(built)} "
                                   f"direct={sorted(direct)}")
                for u in built:                 # and the kill is a real kill
                    if not any((rung(i) * u + s) % q == 0
                               for i in range(1, n + 1)):
                        return False, (f"G3 FAIL: s={s:+d} n={n} q={q} "
                                       f"residue {u} kills nothing")
    # UNIT SPACE: the k' residues q kills, mapped back through k = unit*k',
    # must be exactly the k residues q kills that are multiples of unit --
    # both directions -- and the same size; a prime of the unit kills no
    # k' at all; and a unit that is not forced is refused.
    checked = 0
    for s in (+1, -1):
        for n, unit in ((8, 30), (10, 210), (14, 2310), (18, 2310),
                        (12, 210), (14, 30)):
            assert_unit(n, s, unit)
            if forced_unit(n, s) % unit:
                return False, (f"G3 FAIL: forced_unit({n}) = "
                               f"{forced_unit(n, s)} is not a multiple of "
                               f"the admissible unit {unit}")
            for q in primerange(2, 300):
                kp = set(killed_residues(q, n, s, unit))
                direct = forbidden_k_residues(q, n, s)
                if unit % q == 0:
                    if kp:
                        return False, (f"G3 FAIL: s={s:+d} n={n} unit {unit}: "
                                       f"q={q} divides the unit but kills "
                                       f"{sorted(kp)}")
                    continue
                back = {(unit * u) % q for u in kp}
                want = {u for u in direct}          # every k residue killed
                if back != want or len(kp) != len(direct):
                    return False, (f"G3 FAIL: s={s:+d} n={n} unit {unit} q={q}: "
                                   f"unit-space kills map to {sorted(back)}, "
                                   f"k-space kills are {sorted(want)}")
                checked += 1
    for n, unit in ((12, 2310), (9, 210), (7, 30), (13, 2310)):
        try:
            assert_unit(n, +1, unit)
            return False, (f"G3 FAIL: unit {unit} accepted at n = {n}, where "
                           f"it is not forced")
        except ValueError:
            pass
    return True, ("G3 ok: constructed K(q,n,s) == direct divisibility in "
                  "both directions, every prime q < 300 at n = 7, 10, 14, "
                  "17 and both signs; in unit space (30, 210, 2310 at the "
                  f"filters that force them, {checked} (q, n, unit, s) "
                  "cases) the k' kills map back exactly onto the k kills "
                  "and the unit's own primes kill nothing; a unit that is "
                  "not forced (2310 at n = 12, 13; 210 at 9; 30 at 7) is "
                  "refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, both signs.

    The oracle's notion of a survivor is the definition: no value
    prime(i)*k + s has a prime factor q <= q2 (excluding the value that
    IS q, which k_lo > q2 rules out).
    """
    checks = 0
    # The windows are WIDE because survivors are sparse here: forced
    # divisibility alone leaves one k in 2310 at n = 14, and a window that
    # comes out empty is a vacuous check, which G4 refuses.
    for s, n, q2, k_lo, span in ((+1, 5, 128, 20_000, 500_000),
                                 (+1, 10, 64, 2_000_000, 10_000_000),
                                 (+1, 14, 32, 50_000_000, 10_000_000),
                                 (-1, 6, 128, 20_000, 500_000),
                                 (-1, 12, 32, 30_000_000, 10_000_000)):
        eng = CpuEngine(n, s, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            ks = np.arange(c0, min(c0 + (1 << 22), k_lo + span),
                           dtype=np.int64)
            ok = np.ones(ks.size, dtype=bool)
            for i in range(1, n + 1):
                v = ks * rung(i) + s
                for q in smalls:
                    ok &= (v % q) != 0
            want.update(int(x) for x in ks[ok].tolist())
        if got != want:
            bad = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: s={s:+d} n={n} window {k_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {bad}")
        if not want:
            return False, (f"G4 FAIL: s={s:+d} n={n} window is empty -- "
                           f"vacuous check")
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on 5 "
                  f"populated windows ({checks} survivors, both signs, "
                  f"n = 5, 6, 10, 12, 14)")


def g5_rederive_knowns():
    """The CPU engine finds a(8) and a(9) of BOTH families end-to-end, and
    FIRST.  The prefix below the engine floor is covered by the oracle, so
    the claim is about the line and not about a window."""
    found = []
    for s in (+1, -1):
        for n in (8, 9):
            eng = CpuEngine(n, s, q2=4096)
            lo = k_floor(4096) + 1
            from pladder_reference import first_k
            if first_k(n, s, lo=1, hi=lo - 1) is not None:
                return False, (f"G5 FAIL: {FAMILIES[s]['oeis']} a({n}) is "
                               f"below the engine floor")
            hits = eng.hunt(lo, KNOWN[s][n] + 1)
            firsts = [k for k, r in hits if r >= n]
            if not firsts or min(firsts) != KNOWN[s][n]:
                return False, (f"G5 FAIL: {FAMILIES[s]['oeis']} least k with "
                               f"run >= {n} came out "
                               f"{min(firsts) if firsts else None}, expected "
                               f"{KNOWN[s][n]}")
            found.append(f"{FAMILIES[s]['oeis']} a({n}) = {KNOWN[s][n]}")
    return True, ("G5 ok: CPU engine re-derived " + ", ".join(found) +
                  " end-to-end as FIRST occurrences, with the sub-floor "
                  "prefix cleared by the oracle")


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW, on real candidates."""
    seen = 0
    for s in (+1, -1):
        eng = CpuEngine(14, s, q2=2048)
        for k in (KNOWN[s][max(KNOWN[s])], KNOWN[s][10], KNOWN[s][9],
                  KNOWN[s][8], 192660, 21972720, 987654210):
            a = eng.run_length(k, cap=16)
            b = oracle_run_length(k, s, cap=16)
            if a != b:
                return False, (f"G6 FAIL: s={s:+d} k={k} engine run {a} != "
                               f"oracle run {b}")
            seen += 1
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates including both frontier terms")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: state the bounds and pin where they are crossed.

    The deterministic Miller-Rabin bound is a property of the VALUES, not
    of k.  Here the largest value is prime(n)*k + s, so the PROOF CROSSING
    k_proof(n, s) is that bound rearranged, and the claim to check is "it
    is exactly as high as the proof allows, and not one k higher" -- both
    halves, per (n, s), because a bound derived by formula fails by being
    off by one, not by being wildly wrong.

    Then the two CEILINGS.  For s = -1 the ceiling IS the crossing.  For
    s = +1 it is the deterministic bound on k itself: at the top of the
    range the values are PAST the bound, so the certificate is load-bearing
    there rather than decorative, while every k -- hence every prime factor
    of k -- is under it, so the certificate is one level deep.
    """
    for s in (+1, -1):
        for n in range(1, 41):
            c = k_proof(n, s)
            if rung(n) * (c - 1) + s >= MR_VALID_BELOW:
                return False, ("G10 FAIL: the largest deterministic k for "
                               "(n, s) = (%d, %+d) is %.4g and its value "
                               "leaves the deterministic MR zone" % (n, s, c - 1))
            if rung(n) * c + s < MR_VALID_BELOW:
                return False, ("G10 FAIL: the proof crossing for (n, s) = "
                               "(%d, %+d) is %.4g but k = %.4g would still "
                               "be deterministic -- the crossing is not the "
                               "bound" % (n, s, c, c))
            top = k_ceil(n, s)
            if s < 0 and top != c:
                return False, ("G10 FAIL: the A084701 ceiling at n = %d is "
                               "%.4g, not its proof crossing %.4g -- that "
                               "family has no certificate past the crossing"
                               % (n, top, c))
            if s > 0:
                if top != MR_VALID_BELOW:
                    return False, ("G10 FAIL: the A084700 ceiling at n = %d "
                                   "is %.4g, not the deterministic bound on "
                                   "k" % (n, top))
                if rung(n) * (top - 1) + s < MR_VALID_BELOW:
                    return False, ("G10 FAIL: at the A084700 ceiling the top "
                                   "value at n = %d is still deterministic "
                                   "-- the certificate would be decorative"
                                   % n)
                if top - 1 >= MR_VALID_BELOW:
                    return False, ("G10 FAIL: the largest sweepable k of "
                                   "A084700 is not under the bound -- a "
                                   "factor of k could need a subproof")
    kk, ii = 161082438032880, 14
    if not mr_is_prime(rung(13) * kk + 1):
        return False, "G10 FAIL: A084700's frontier term's 13th value is not prime"
    if mr_is_prime(rung(ii) * kk + 1):
        return False, "G10 FAIL: A084700's wall value tests prime"
    return True, ("G10 ok: the proof crossing IS the deterministic MR bound "
                  "(3.317e24) rearranged, tight to one k, for every filter "
                  "n = 1..40 and both signs -- k < %.4g at n = 17, %.4g at "
                  "n = 18; A084701's ceiling is that crossing (every "
                  "decision a proof) and A084700's is the bound on k itself, "
                  "%.4g, where the top value is past the bound and every "
                  "factor of k is under it"
                  % (k_proof(17, +1), k_proof(18, +1), k_ceil(18, +1)))


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
