"""sqladder_search.py -- the CPU engine for A089761.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is
independent in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array
    over the k line and uses no wheel at all.  The GPU engine never
    materialises the k line: it generates only the residues that survive a
    wheel and tests each one against a packed forbidden-residue bitmap,
    bailing out at the first kill.  A wheel bug on the GPU side therefore
    shows up as a parity failure rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(q,n) is built here by inverting and
    negating i^2; the oracle builds it by walking every residue and
    testing divisibility.  G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (k, off) pairs on
the GPU -- k = base + off with base a host-side big int and off < W, so no
machine word bounds the search (OPTIMIZATION.md 2.7).  This engine needs
no such care: `%` on a Python int is already arbitrary-precision, which is
exactly why it is the parity reference for a device that is not.

Primality note, and it is a good one.  huntlib's Miller-Rabin is
DETERMINISTIC below MR_VALID_BELOW = 3.317e24, and the largest value this
project forms is k*n^2+1.  At n = 16 that stays deterministic until
k = 1.3e22 -- four orders of magnitude past a(18)'s modelled median.  So
unlike dickson-ladders, whose values pass the bound before a(9), every
primality decision this hunt makes in its planned range is a proof, not a
probable-prime filter.  G10 pins the crossing point so no future edit can
quietly assume determinism after the range moves.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions), G4 (CPU survivors == the oracle's definition of a survivor on
populated windows), G5 (CPU re-derives a(8), a(9), a(10) end-to-end as
FIRST occurrences), G10 (numeric hygiene: where the values pass the
deterministic Miller-Rabin bound).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from sqladder_reference import (K_FLOOR, KNOWN, forbidden_k_residues,
                                run_length as oracle_run_length, w)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)


def k_ceil(n):
    """The enforced ceiling on k, for a filter of n conditions.

    It is the PRIMALITY-TEST VALIDITY BOUND and nothing else, which is what
    OPTIMIZATION.md 2.7 says to pick: the largest k for which every value
    k*i^2+1 this project forms stays under huntlib's DETERMINISTIC
    Miller-Rabin bound, so every primality decision the hunt makes is a
    proof rather than a probable-prime filter.

    Before v4 this was 9e18 -- a MACHINE WORD, not a mathematical bound,
    forced by a GPU kernel that carried the absolute k in u64.  v4 carries
    (k, off) instead (sqladder_gpu), so the word boundary is gone and the
    ceiling can be what it always should have been.  At n = 18 it is
    1.02e22, past the modelled P99 for a(18) by two orders of magnitude;
    the run ends when the term is found, not when the engine gives out.

    EXCLUSIVE, like every other bound in the engines: the largest k that
    may be swept is k_ceil(n) - 1, and it is that k whose top value
    (k_ceil(n)-1)*n^2 + 1 has to stay under the MR bound.  G10 pins both
    halves, because a ceiling derived by formula fails by one or not at
    all.
    """
    return (MR_VALID_BELOW - 2) // (n * n) + 1


def killed_residues(q, n):
    """K(q,n) = { -(i^2)^-1 mod q : i = 1..n, q does not divide i }.

    The algebraic construction, as opposed to the oracle's walk over every
    residue.  Deduplicated rather than counted, because relying on a proof
    for a data-structure invariant is how one gets a silent off-by-one --
    the size is separately gated (G2b) against min(n, (q-1)/2).
    """
    return sorted({(-pow(i * i, -1, q)) % q
                   for i in range(1, n + 1) if i % q})


class CpuEngine:
    """Segmented sieve over the dense k line."""

    def __init__(self, n, q2=Q2_DEFAULT):
        self.n = n
        self.q2 = q2
        self.primes = list(primerange(2, q2 + 1))
        self.table = {q: killed_residues(q, n) for q in self.primes}
        self.marks_per_k = sum(len(v) / q for q, v in self.table.items())

    # ---------------------------------------------------------------- sieve
    def survivors(self, k_lo, k_hi, block=1 << 22):
        """Yield lists of the k in [k_lo, k_hi) that no prime q <= q2 kills.

        The floor is not decoration.  "q divides the value, so the value is
        composite" needs the value to EXCEED q, and k*i^2+1 >= k+1, so a
        sieve to q2 is only valid above k = q2.  K_FLOOR guards the other
        end, where a value can BE the prime that divides it.

        The bounds are checked EAGERLY, here, and the generator is a
        separate function -- a `yield` anywhere in this body would defer
        every check to the first `next()`, so a caller that built the
        generator and never iterated it would sail past both ceilings in
        silence.  The ceiling drill in the selftest calls this without
        consuming it, which is exactly the case that caught it.
        """
        if k_hi > k_ceil(self.n):
            raise ValueError(f"k {k_hi} past the enforced ceiling "
                             f"{k_ceil(self.n)}")
        if k_lo <= max(K_FLOOR, self.q2):
            raise ValueError(
                f"engines refuse to run at or below max(K_FLOOR, q2) = "
                f"{max(K_FLOOR, self.q2)}: the wheel argument has an "
                f"exception zone there and a kill by q needs value > q")
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
        return all(k % q not in s for q, s in self._sets().items())

    def _sets(self):
        if not hasattr(self, "_frozen"):
            self._frozen = {q: frozenset(v) for q, v in self.table.items()}
        return self._frozen

    # ------------------------------------------------------------ classify
    def run_length(self, k, cap=64):
        """Largest r <= cap with k*i^2+1 prime for i = 1..r.

        Deterministic in this project's range -- see the module docstring
        and G10."""
        r = 0
        while r < cap and mr_is_prime(k * (r + 1) ** 2 + 1):
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
    """The constructed killed set must equal direct divisibility, BOTH ways.

    One direction stops the engine emitting a candidate it should have
    killed; the other stops it killing one it should have kept, which is
    the failure a parity gate between two engines sharing the construction
    could never see.
    """
    for n in (7, 10, 16, 19):
        for q in primerange(2, 300):
            built = set(killed_residues(q, n))
            direct = forbidden_k_residues(q, n)
            if built != direct:
                return False, (f"G3 FAIL: n={n} q={q} built={sorted(built)} "
                               f"direct={sorted(direct)}")
            for u in built:                     # and the kill is a real kill
                if not any((u * i * i + 1) % q == 0 for i in range(1, n + 1)):
                    return False, (f"G3 FAIL: n={n} q={q} residue {u} kills "
                                   f"nothing")
    return True, ("G3 ok: constructed K(q,n) == direct divisibility in both "
                  "directions, every prime q < 300 at n = 7, 10, 16, 19")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows.

    The oracle's notion of a survivor is the definition: no value k*i^2+1
    has a prime factor q <= q2 (excluding the value that IS q).
    """
    checks = 0
    for n, q2, k_lo, span in ((5, 128, 20_000, 500_000),
                              (10, 128, 2_000_000, 1_000_000),
                              (16, 64, 50_000_000, 1_000_000)):
        eng = CpuEngine(n, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        # The oracle side works on the VALUES k*i^2+1 and asks each prime
        # directly, which is the definition; the engine side never forms a
        # value and marks progressions off a residue table.  k_lo > q2, so
        # no value can BE the prime that divides it.
        ks = np.arange(k_lo, k_lo + span, dtype=np.int64)
        ok = np.ones(span, dtype=bool)
        for i in range(1, n + 1):
            v = ks * (i * i) + 1
            for q in smalls:
                ok &= (v % q) != 0
        want = set(int(x) for x in ks[ok].tolist())
        if got != want:
            bad = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: n={n} window {k_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {bad}")
        if not want:
            return False, f"G4 FAIL: n={n} window is empty -- vacuous check"
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on 3 "
                  f"populated windows ({checks} survivors, n = 5, 10, 16)")


def g5_rederive_knowns():
    """The CPU engine finds a(8), a(9) and a(10) end-to-end, and FIRST."""
    for n in (8, 9, 10):
        eng = CpuEngine(n, q2=4096)
        hits = eng.hunt(max(K_FLOOR, 4096) + 1, KNOWN[n] + 1)
        firsts = [k for k, r in hits if r >= n]
        if not firsts or min(firsts) != KNOWN[n]:
            return False, (f"G5 FAIL: least k with run >= {n} came out "
                           f"{min(firsts) if firsts else None}, "
                           f"expected {KNOWN[n]}")
    return True, ("G5 ok: CPU engine re-derived a(8) = %d, a(9) = %d and "
                  "a(10) = %d end-to-end as FIRST occurrences"
                  % (KNOWN[8], KNOWN[9], KNOWN[10]))


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW, on real candidates."""
    eng = CpuEngine(16, q2=2048)
    seen = 0
    for k in (KNOWN[11], KNOWN[10], KNOWN[9], 54972, 220433059, 987654320):
        a = eng.run_length(k, cap=18)
        b = oracle_run_length(k, cap=18)
        if a != b:
            return False, f"G6 FAIL: k={k} engine run {a} != oracle run {b}"
        seen += 1
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates including the a(11) champion")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: state the bound and pin where it is crossed.

    The deterministic Miller-Rabin bound is a property of the VALUES, not
    of k.  Here the largest value is k*n^2+1, and since v4 the ceiling IS
    that bound rearranged -- so the claim to check is no longer "the cap
    happens to sit low enough" but "the cap is exactly as high as the proof
    allows, and not one k higher".  Both halves are gated, per n, because
    a ceiling derived by formula fails by being off by one, not by being
    wildly wrong (CONVENTIONS.md "Numeric hygiene").
    """
    for n in range(1, 41):
        c = k_ceil(n)
        if (c - 1) * n * n + 1 >= MR_VALID_BELOW:
            return False, ("G10 FAIL: the largest sweepable k for n = %d is "
                           "%.4g and its value k*%d^2+1 leaves the "
                           "deterministic MR zone -- the engine may no "
                           "longer claim proofs" % (n, c - 1, n))
        if c * n * n + 1 < MR_VALID_BELOW:
            return False, ("G10 FAIL: the ceiling for n = %d is %.4g but "
                           "k = %.4g would still be deterministic -- the cap "
                           "is not the bound, so it is the wrong cap"
                           % (n, c, c))
    if not mr_is_prime(KNOWN[11] * 15 * 15 + 1):
        return False, "G10 FAIL: the a(11) champion's 15th value is not prime"
    if mr_is_prime(KNOWN[11] * 16 * 16 + 1):
        return False, "G10 FAIL: the wall value tests prime"
    return True, ("G10 ok: the ceiling IS the deterministic MR bound "
                  "(3.317e24) rearranged, tight to one k, for every filter "
                  "n = 1..40 -- at n = 18 that is k < %.4g, so every "
                  "primality decision anywhere in the enforced range is a "
                  "PROOF" % k_ceil(18))


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
