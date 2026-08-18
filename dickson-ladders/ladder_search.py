"""ladder_search.py -- the CPU engine for A247965.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is
independent in three ways that matter:

  * arithmetic: plain Python/numpy `%` and slice-strided kills, never the
    GPU's Barrett magic-multiply;
  * shape: a segmented sieve that marks arithmetic progressions of j,
    never a per-candidate residue walk;
  * construction: this engine builds a table of killed j-residues from
    sympy's square roots; the GPU engine builds no table at all and
    re-derives the kill test per candidate by stepping m*t+1.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share nothing but the answer.

Representation.  Candidates are carried as the pair (W, j) with k = W*j,
W = W(n) the wheel modulus.  k itself is never formed here: every sieve
test needs only k mod q = ((W mod q) * (j mod q)) mod q.  j stays inside
u64 to the enforced ceiling, so one engine spans the whole search range
and there is no second engine waiting at 2^64 (OPTIMIZATION.md 2.7) --
even though k passes 2^64 around a(12) and the VALUES m*k^2+1 pass it
before a(8).

Primality note.  m*k^2+1 exceeds huntlib's deterministic Miller-Rabin
bound (3.317e24) once k passes ~5e11, i.e. before a(9).  The chain here
is therefore a STRONG PROBABLE PRIME chain, used as a filter; claimed
finds are certified separately in launch.py (Pocklington, which this
problem hands us for free because N-1 = m*k^2 is our own number).
Compositeness, which is what the least-claim actually rests on, stays
rigorous either way: a small factor from the sieve or a failed strong
test is a proof.

Gates here: G3 (constructed residue table == direct divisibility, both
directions), G4 (CPU survivors == oracle survivors on small windows),
G5 (CPU re-derives a(7) and a(8) end-to-end).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange, sqrt_mod

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.primes import MR_VALID_BELOW, mr_is_prime      # noqa: E402
from ladder_reference import (K_FLOOR, KNOWN, forbidden_k_residues,
                              wheel_modulus)

Q2_DEFAULT = 65536           # sieve depth (primes tested by the engines)
J_CEIL = 4 * 10**18          # enforced: j must stay inside u64 with room


class CpuEngine:
    """Segmented sieve over j, where k = W*j."""

    def __init__(self, n, q2=Q2_DEFAULT):
        self.n = n
        self.q2 = q2
        self.W = wheel_modulus(n)
        # Primes above the wheel are the ones that can still kill.  A prime
        # q <= n+1 divides no value at all once k is on the wheel: k == 0
        # (mod q) makes every m*k^2+1 == 1 (mod q).
        self.primes = [q for q in primerange(n + 2, q2)]
        self.table = {q: self._forbidden_j(q) for q in self.primes}

    # ---------------------------------------------------------------- table
    def _forbidden_j(self, q):
        """Residues of j mod q killed by q, via sympy's square roots.

        k^2 == -1/m (mod q) has two roots exactly when (-m|q) = +1; j is
        recovered as root * W^-1.  Distinct m give disjoint roots, so the
        list is already duplicate-free, but it is de-duplicated anyway
        because relying on a proof for a data-structure invariant is how
        one gets a silent off-by-one.
        """
        winv = pow(self.W % q, q - 2, q)
        out = set()
        for m in range(1, self.n + 1):
            rhs = (-pow(m, q - 2, q)) % q
            r = sqrt_mod(rhs, q, all_roots=True)
            if not r:
                continue
            for root in r:
                out.add(int(root) * winv % q)
        return np.array(sorted(out), dtype=np.int64)

    # ---------------------------------------------------------------- sieve
    def survivors_j(self, j_lo, j_hi, block=1 << 22):
        """Yield arrays of surviving j in [j_lo, j_hi)."""
        if j_hi > J_CEIL:
            raise ValueError(f"j {j_hi} past the enforced ceiling {J_CEIL}")
        if j_lo * self.W < K_FLOOR:
            raise ValueError("engines refuse to run below K_FLOOR; the wheel "
                             "argument has an exception zone there")
        j0 = int(j_lo)
        while j0 < j_hi:
            j1 = min(j0 + block, int(j_hi))
            alive = np.ones(j1 - j0, dtype=bool)
            for q in self.primes:
                start = j0 % q
                for r in self.table[q]:
                    first = int((r - start) % q)
                    if first < alive.size:
                        alive[first::q] = False
            idx = np.nonzero(alive)[0]
            if idx.size:
                yield (j0 + idx).astype(np.uint64)
            j0 = j1

    def survivors_pre_mr(self, k_lo, k_hi, block=1 << 22):
        """Same stream, expressed on the k line (inclusive of both ends)."""
        j_lo = max(1, -(-int(k_lo) // self.W))
        j_hi = int(k_hi) // self.W + 1
        for chunk in self.survivors_j(j_lo, j_hi, block):
            yield chunk

    # ------------------------------------------------------------ classify
    def run_length(self, k, cap=64):
        """Strong-probable-prime run length (see the module docstring)."""
        r = 0
        while r < cap and mr_is_prime((r + 1) * k * k + 1):
            r += 1
        return r

    def hunt(self, k_lo, k_hi, cap=None):
        """[(k, run)] for every survivor whose run reaches the filter n."""
        cap = cap or self.n + 8
        out = []
        for chunk in self.survivors_pre_mr(k_lo, k_hi):
            for j in chunk.tolist():
                k = int(j) * self.W
                if k < k_lo or k > k_hi:
                    continue
                r = self.run_length(k, cap=cap)
                if r >= self.n:
                    out.append((k, r))
        return out


# --------------------------------- gates -----------------------------------

def g3_table_matches_divisibility():
    """The constructed j-table must equal direct divisibility, BOTH ways.

    One direction stops the engine from emitting a candidate it should
    have killed; the other stops it from killing one it should have kept,
    which is the failure mode a parity gate against another engine using
    the same construction could never see.
    """
    for n in (7, 10, 13):
        eng = CpuEngine(n, q2=400)
        W = eng.W
        for q in eng.primes:
            built = set(int(v) for v in eng.table[q])
            direct = set((k * pow(W % q, q - 2, q)) % q
                         for k in forbidden_k_residues(q, n))
            if built != direct:
                return False, (f"G3 FAIL: n={n} q={q} built={sorted(built)} "
                               f"direct={sorted(direct)}")
            # and the kill really is a kill: every emitted residue divides
            for r in built:
                k = (r * W) % q
                if not any(((m * k * k + 1) % q) == 0
                           for m in range(1, n + 1)):
                    return False, f"G3 FAIL: n={n} q={q} residue {r} kills nothing"
    return True, ("G3 ok: constructed j-residues == direct divisibility in "
                  "both directions, every prime q < 400 at n = 7, 10, 13")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows.

    The oracle's notion of a survivor is the definition: no value
    m*k^2+1 has a prime factor <= q2.
    """
    checks = 0
    for n, q2, k_lo, span in ((5, 1024, 10**4, 4 * 10**6),
                              (7, 4096, 10**6, 2 * 10**7),
                              (10, 2048, 10**7, 4 * 10**8)):
        eng = CpuEngine(n, q2=q2)
        got = set()
        for chunk in eng.survivors_pre_mr(k_lo, k_lo + span):
            got.update(int(j) * eng.W for j in chunk.tolist())
        got = {k for k in got if k_lo <= k <= k_lo + span}
        want = set()
        smalls = list(primerange(2, q2))
        k = k_lo + (-k_lo) % eng.W
        while k <= k_lo + span:
            if all(not any((m * k * k + 1) % q == 0 and m * k * k + 1 != q
                           for q in smalls) for m in range(1, n + 1)):
                want.add(k)
            k += eng.W
        if got != want:
            return False, (f"G4 FAIL: n={n} window {k_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {sorted(got ^ want)[:4]}")
        if not want:
            return False, f"G4 FAIL: n={n} window is empty -- vacuous check"
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on 3 "
                  f"populated windows ({checks} survivors, n = 5, 7, 10)")


def g5_rederive_knowns():
    """The CPU engine finds a(7) and a(8) end-to-end, and finds them FIRST."""
    for n in (7, 8):
        eng = CpuEngine(n)
        hits = eng.hunt(K_FLOOR, KNOWN[n])
        firsts = [k for k, r in hits if r >= n]
        if not firsts or min(firsts) != KNOWN[n]:
            return False, (f"G5 FAIL: least k with run >= {n} came out "
                           f"{min(firsts) if firsts else None}, "
                           f"expected {KNOWN[n]}")
    return True, ("G5 ok: CPU engine re-derived a(7) = %d and a(8) = %d "
                  "end-to-end as FIRST occurrences" % (KNOWN[7], KNOWN[8]))


def g10_values_past_the_mr_bound():
    """Numeric hygiene: state the bound, and prove we know where it fails.

    The deterministic Miller-Rabin bound is a property of the VALUES here,
    not of k, and it is crossed early.  This gate pins the crossing point
    so no future edit can quietly assume determinism where there is none.
    """
    n = 10
    k = 1
    while n * k * k + 1 < MR_VALID_BELOW:
        k *= 2
    lo = k // 2
    if n * lo * lo + 1 >= MR_VALID_BELOW or n * k * k + 1 < MR_VALID_BELOW:
        return False, "G10 FAIL: bracket for the MR bound is wrong"
    if KNOWN[9] * KNOWN[9] * 9 + 1 < MR_VALID_BELOW:
        return False, ("G10 FAIL: a(9) values were assumed past the MR bound "
                       "and are not")
    return True, ("G10 ok: values pass huntlib's deterministic MR bound "
                  "(3.317e24) between k = %d and %d -- before a(9), so the "
                  "engine chain is SPRP by construction and finds are "
                  "certified by Pocklington instead" % (lo, k))


GATES = [g3_table_matches_divisibility, g4_cpu_matches_oracle,
         g10_values_past_the_mr_bound, g5_rederive_knowns]

if __name__ == "__main__":
    for g in GATES:
        ok, msg = g()
        print(("PASS " if ok else "FAIL ") + msg)
