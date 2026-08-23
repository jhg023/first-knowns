"""shiftladder_search.py -- the CPU engine for A130003 and A110096.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is
independent in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array
    over the m line and uses no wheel at all.  The GPU engine never
    materialises the m line: it generates only the residues that survive a
    wheel and tests each one against a packed forbidden-residue bitmap,
    bailing out at the first kill.  A wheel bug on the GPU side therefore
    shows up as a parity failure rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(q,n,b) is built here by negating the
    orbit of b; the oracle builds it by walking every residue and testing
    divisibility.  G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (m, off) pairs on
the GPU -- m = base + off with base a host-side big int and off < W, so no
machine word bounds the search.  That is OPTIMIZATION.md 2.7, and this
project takes it from the first commit rather than growing a second engine
at the word boundary later: square-ladders had to raise its ceiling twice,
and the second time cost an entire campaign stretch.

Primality note, and it is the best one in the repo.  huntlib's Miller-Rabin
is DETERMINISTIC below MR_VALID_BELOW = 3.317e24, and the largest value
this project forms is m + b^n -- an ADDITIVE offset, not a multiplicative
one.  At b = 4, n = 21 that offset is 4.4e12, which is 12 orders of
magnitude below the bound, so the ceiling is essentially the bound itself:
3.317e24 for both families, against square-ladders' 1.02e22 at n = 18.
Every primality decision this hunt can make is a proof, and it stays that
way for a very long time.  G10 pins the crossing point per (n, b) so no
future edit can quietly assume determinism after the range moves.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, both bases), G4 (CPU survivors == the oracle's definition of a
survivor on populated windows), G5 (CPU re-derives A110096 a(9)
end-to-end as a FIRST occurrence), G6 (engine run lengths == sympy BPSW),
G10 (numeric hygiene: where the values pass the deterministic Miller-Rabin
bound).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from shiftladder_reference import (K_FLOOR, KNOWN,              # noqa: E402
                                   forbidden_m_residues,
                                   run_length as oracle_run_length)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)


def k_ceil(n, b):
    """The enforced ceiling on m, for a filter of n conditions at base b.

    It is the PRIMALITY-TEST VALIDITY BOUND and nothing else, which is what
    OPTIMIZATION.md 2.7 says to pick: the largest m for which every value
    m + b^k this project forms stays under huntlib's DETERMINISTIC
    Miller-Rabin bound, so every primality decision the hunt makes is a
    proof rather than a probable-prime filter.

    EXCLUSIVE, like every other bound in the engines: the largest m that
    may be swept is k_ceil(n, b) - 1, and it is that m whose top value
    (k_ceil - 1) + b^n has to stay under the MR bound.  G10 pins both
    halves, because a ceiling derived by formula fails by one or not at
    all.

    The offset is ADDITIVE, so unlike a multiplicative ladder the ceiling
    barely moves with n: 3.317e24 minus 4.4e12 at (21, 4) is still
    3.317e24 to four figures.  What bounds this project is the model, the
    GPU-hours and the operator's patience -- not the arithmetic.
    """
    return MR_VALID_BELOW - b ** n


def m_floor(q2):
    """The smallest m the engines will sweep.

    Two separate reasons, and the larger wins.  A kill by q needs the value
    to EXCEED q, and the smallest value is m + b >= m + 2, so a sieve to q2
    is only valid above m = q2.  K_FLOOR guards the other end, the
    exception zone where a value can BE the prime that divides it
    (A110096's a(1) = 1 is the case: 1 + 2 = 3, and m = 1 is killed by the
    q = 3 rule at every n).
    """
    return max(K_FLOOR, q2)


def killed_residues(q, n, b):
    """K(q,n,b) = { -b^k mod q : k = 1..n }.

    The algebraic construction -- one modular exponentiation per k -- as
    opposed to the oracle's walk over every residue.  Deduplicated rather
    than counted, because relying on a proof for a data-structure invariant
    is how one gets a silent off-by-one; the size is separately gated (G2b)
    against min(n, ord_q(b)).
    """
    return sorted({(-pow(b, k, q)) % q for k in range(1, n + 1)})


class CpuEngine:
    """Segmented sieve over the dense m line, no wheel."""

    def __init__(self, n, b, q2=Q2_DEFAULT):
        self.n = n
        self.b = b
        self.q2 = q2
        self.primes = list(primerange(2, q2 + 1))
        self.table = {q: killed_residues(q, n, b) for q in self.primes}
        self.marks_per_m = sum(len(v) / q for q, v in self.table.items())

    # ---------------------------------------------------------------- sieve
    def survivors(self, m_lo, m_hi, block=1 << 22):
        """Yield lists of the m in [m_lo, m_hi) that no prime q <= q2 kills.

        The bounds are checked EAGERLY, here, and the generator is a
        separate function -- a `yield` anywhere in this body would defer
        every check to the first `next()`, so a caller that built the
        generator and never iterated it would sail past both ceilings in
        silence.  The ceiling drill in the selftest calls this without
        consuming it, which is exactly the case that catches it.
        """
        if m_hi > k_ceil(self.n, self.b):
            raise ValueError(f"m {m_hi} past the enforced ceiling "
                             f"{k_ceil(self.n, self.b)}")
        if m_lo <= m_floor(self.q2):
            raise ValueError(
                f"engines refuse to run at or below max(K_FLOOR, q2) = "
                f"{m_floor(self.q2)}: the wheel argument has an exception "
                f"zone there and a kill by q needs value > q")
        return self._survivors(m_lo, m_hi, block)

    def _survivors(self, m_lo, m_hi, block):
        m0 = int(m_lo)
        while m0 < m_hi:
            m1 = min(m0 + block, int(m_hi))
            alive = np.ones(m1 - m0, dtype=bool)
            for q in self.primes:
                for u in self.table[q]:
                    first = (u - m0) % q
                    if first < alive.size:
                        alive[first::q] = False
            idx = np.nonzero(alive)[0]
            if idx.size:
                # Python ints, not u64: the sieve's own arithmetic is on
                # OFFSETS into the block and stays small, but the answers
                # are absolute m and this engine is the parity reference
                # for a range that runs past 2^64.
                yield [m0 + int(i) for i in idx]
            m0 = m1

    def survives(self, m):
        """The same decision, one candidate at a time, in Python ints."""
        m = int(m)
        return all(m % q not in s for q, s in self._sets().items())

    def _sets(self):
        if not hasattr(self, "_frozen"):
            self._frozen = {q: frozenset(v) for q, v in self.table.items()}
        return self._frozen

    # ------------------------------------------------------------ classify
    def run_length(self, m, cap=64):
        """Largest r <= cap with m + b^k prime for k = 1..r.

        Deterministic in this project's range -- see the module docstring
        and G10."""
        r = 0
        while r < cap and mr_is_prime(m + self.b ** (r + 1)):
            r += 1
        return r

    def hunt(self, m_lo, m_hi, cap=None):
        """[(m, run)] for every survivor whose run reaches the filter n."""
        cap = cap or self.n + 8
        out = []
        for chunk in self.survivors(m_lo, m_hi):
            for m in chunk:
                r = self.run_length(int(m), cap=cap)
                if r >= self.n:
                    out.append((int(m), r))
        return out


# --------------------------------- gates -----------------------------------

def g3_table_matches_divisibility():
    """The constructed killed set must equal direct divisibility, BOTH ways.

    One direction stops the engine emitting a candidate it should have
    killed; the other stops it killing one it should have kept, which is
    the failure a parity gate between two engines sharing the construction
    could never see.
    """
    for b in (2, 4):
        for n in (7, 12, 17, 19, 21):
            for q in primerange(2, 300):
                built = set(killed_residues(q, n, b))
                direct = forbidden_m_residues(q, n, b)
                if built != direct:
                    return False, (f"G3 FAIL: b={b} n={n} q={q} "
                                   f"built={sorted(built)} "
                                   f"direct={sorted(direct)}")
                for u in built:                 # and the kill is a real kill
                    if not any((u + b ** k) % q == 0
                               for k in range(1, n + 1)):
                        return False, (f"G3 FAIL: b={b} n={n} q={q} residue "
                                       f"{u} kills nothing")
    return True, ("G3 ok: constructed K(q,n,b) == direct divisibility in "
                  "both directions, every prime q < 300 at n = 7, 12, 17, "
                  "19, 21 and both bases")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows.

    The oracle's notion of a survivor is the definition: no value m + b^k
    has a prime factor q <= q2 (excluding the value that IS q, which the
    floor rules out).
    """
    checks = 0
    # The b = 2 windows have to be much wider for the same survivor count:
    # its wheel is thousands of times sparser (the ord lemma in the oracle),
    # and a vacuous window is not a check, so each of these was sized until
    # it was populated and then frozen.
    for b, n, q2, m_lo, span in ((4, 5, 128, 20_000, 500_000),
                                 (4, 12, 128, 2_000_000, 1_000_000),
                                 (2, 9, 64, 50_000, 2_000_000),
                                 (2, 12, 64, 3_000_000, 4_000_000)):
        eng = CpuEngine(n, b, q2=q2)
        got = set()
        for chunk in eng.survivors(m_lo, m_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        # The oracle side works on the VALUES m + b^k and asks each prime
        # directly, which is the definition; the engine side never forms a
        # value and marks progressions off a residue table.  m_lo > q2, so
        # no value can BE the prime that divides it.
        ms = np.arange(m_lo, m_lo + span, dtype=np.int64)
        ok = np.ones(span, dtype=bool)
        for k in range(1, n + 1):
            v = ms + b ** k
            for q in smalls:
                ok &= (v % q) != 0
        want = set(int(x) for x in ms[ok].tolist())
        if got != want:
            bad = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: b={b} n={n} window {m_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {bad}")
        if not want:
            return False, (f"G4 FAIL: b={b} n={n} window is empty -- "
                           f"vacuous check")
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on 4 "
                  f"populated windows ({checks} survivors, both bases, "
                  f"n = 5, 9, 12)")


def g5_rederive_knowns():
    """The CPU engine finds A110096 a(9) end-to-end, and FIRST.

    Only one known term of either family sits between the engine floor and
    a range a dense CPU sieve can walk: A110096's a(9) = 19425.  Every
    other term is either inside the exception zone (A130003 tops out at
    4503 until a(15)) or is 8.3e8 and up, which is a GPU canary and not a
    CPU one -- the launcher runs those against the production stream
    (A130003 a(15), A110096 a(10)) at their own filters, which is where a
    rediscovery of that size belongs.
    """
    n, b = 9, 2
    eng = CpuEngine(n, b, q2=4096)
    hits = eng.hunt(m_floor(4096) + 1, KNOWN[b][n] + 1)
    firsts = [m for m, r in hits if r >= n]
    if not firsts or min(firsts) != KNOWN[b][n]:
        return False, (f"G5 FAIL: least m with run >= {n} at b = {b} came "
                       f"out {min(firsts) if firsts else None}, expected "
                       f"{KNOWN[b][n]}")
    return True, ("G5 ok: CPU engine re-derived A110096 a(9) = %d end-to-end "
                  "as a FIRST occurrence, sweeping from the floor "
                  "(A130003's terms below a(15) are inside the exception "
                  "zone and its a(15) is a GPU canary)" % KNOWN[b][n])


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW, on real candidates."""
    seen = 0
    for b, cands in ((4, (KNOWN[4][18], KNOWN[4][17], KNOWN[4][15], 4503,
                          1158174141556289)),
                     (2, (KNOWN[2][16], KNOWN[2][14], KNOWN[2][11], 19425,
                          143924005810811657))):
        eng = CpuEngine(19, b, q2=2048)
        for m in cands:
            a = eng.run_length(m, cap=22)
            c = oracle_run_length(m, b, cap=22)
            if a != c:
                return False, (f"G6 FAIL: b={b} m={m} engine run {a} != "
                               f"oracle run {c}")
            seen += 1
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates across both bases, including each family's "
                  f"frontier term and a neighbour of it")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: state the bound and pin where it is crossed.

    The deterministic Miller-Rabin bound is a property of the VALUES, not
    of m.  Here the largest value is m + b^n, and the ceiling IS that bound
    rearranged -- so the claim to check is not "the cap happens to sit low
    enough" but "the cap is exactly as high as the proof allows, and not
    one m higher".  Both halves are gated, per (n, b), because a ceiling
    derived by formula fails by being off by one, not by being wildly wrong
    (CONVENTIONS.md "Numeric hygiene").
    """
    for b in (2, 4):
        for n in range(1, 41):
            c = k_ceil(n, b)
            if (c - 1) + b ** n >= MR_VALID_BELOW:
                return False, ("G10 FAIL: the largest sweepable m for "
                               "(n, b) = (%d, %d) is %.6g and its value "
                               "m + b^n leaves the deterministic MR zone"
                               % (n, b, c - 1))
            if c + b ** n < MR_VALID_BELOW:
                return False, ("G10 FAIL: the ceiling for (n, b) = (%d, %d) "
                               "is %.6g but m = %.6g would still be "
                               "deterministic -- the cap is not the bound, "
                               "so it is the wrong cap" % (n, b, c, c))
    if not mr_is_prime(KNOWN[4][18] + 4 ** 18):
        return False, "G10 FAIL: A130003's frontier term fails at k = 18"
    if mr_is_prime(KNOWN[4][18] + 4 ** 19):
        return False, "G10 FAIL: A130003's wall value tests prime"
    return True, ("G10 ok: the ceiling IS the deterministic MR bound "
                  "(3.317e24) minus b^n, tight to one m, for every filter "
                  "n = 1..40 at both bases -- at (19, 4) that is "
                  "m < %.6g, so every primality decision anywhere in the "
                  "enforced range is a PROOF" % k_ceil(19, 4))


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
