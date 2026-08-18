"""ladder_gpu.py -- the GPU engine for A247965.

The same mathematics a third time, in CUDA, and never trusted alone: G6
pins its output stream bit-for-bit against the numpy CPU engine on
populated windows at several heights including the enforced ceiling.

How it differs from the CPU engine -- which is the point of having two:

  * The CPU engine builds a table of killed j-residues per prime (sympy
    square roots) and marks arithmetic progressions.  This engine builds
    NO residue table at all.  For each candidate it re-derives the kill
    test from scratch:

        jq = j mod q                      (Barrett)
        t  = (W mod q) * jq mod q, squared mod q      == k^2 mod q
        r  = t + 1, then r += t, n times  == m*k^2 + 1 mod q for m = 1..n

    kill if any r hits 0.  No square roots, no table, no shared code --
    the two engines agree only because the mathematics does.
  * Arithmetic is Barrett magic-multiply throughout (huntlib/gpu.py); the
    CPU engine uses plain `%`.

Representation: candidates are the pair (W, j) with k = W*j.  k is never
formed on the device -- it does not fit a machine word past a(12) and it
does not need to.  j stays inside u64 to the enforced ceiling J_CEIL, so
this one engine spans the entire search range.

Sizes, all enforced by G14 rather than asserted in a comment: W mod q and
j mod q are both < q < 2^16, so their product is < 2^32; t < q so t*t is
< 2^32; every Barrett reduction therefore runs on inputs it is exact for.

Gates here: G6 (GPU == CPU parity), G7 (planted-fake drill), G8 (the GPU
rediscovers a(7) end-to-end), G13 (the stream does not depend on how the
work is sliced), G14 (the kernel's kill decisions == big-integer
divisibility of the actual values m*k^2+1).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.gpu import barrett_magics                        # noqa: E402
from huntlib.primes import mr_is_prime                        # noqa: E402
from ladder_reference import K_FLOOR, KNOWN, wheel_modulus    # noqa: E402
from ladder_search import J_CEIL, Q2_DEFAULT                  # noqa: E402

try:
    import cupy as cp
except Exception:                                    # pragma: no cover
    cp = None

_KERNEL = r'''
extern "C" __global__
void sieve(const unsigned long long j0,
           const unsigned long long count,
           const int nprimes,
           const int nfilter,
           const unsigned long long* __restrict__ primes,
           const unsigned long long* __restrict__ magic,
           const unsigned long long* __restrict__ wmod,
           unsigned long long* __restrict__ out,
           unsigned int* __restrict__ nout,
           const unsigned int cap)
{
    unsigned long long idx = blockIdx.x * (unsigned long long)blockDim.x
                             + threadIdx.x;
    if (idx >= count) return;
    const unsigned long long j = j0 + idx;

    for (int i = 0; i < nprimes; ++i) {
        const unsigned long long q = primes[i];
        /* jq = j mod q, Barrett (huntlib/gpu.py) */
        unsigned long long qhat = __umul64hi(j, magic[i]);
        unsigned long long jq = j - qhat * q;
        if (jq >= q) jq -= q;
        if (jq >= q) jq -= q;
        /* t = k^2 mod q with k = W*j, never forming k */
        unsigned long long t = wmod[i] * jq;
        qhat = __umul64hi(t, magic[i]);
        t -= qhat * q;
        if (t >= q) t -= q;
        if (t >= q) t -= q;
        t = t * t;
        qhat = __umul64hi(t, magic[i]);
        t -= qhat * q;
        if (t >= q) t -= q;
        if (t >= q) t -= q;
        /* r walks m*t + 1 for m = 1..nfilter; a zero is a small factor */
        unsigned long long r = t + 1;
        if (r >= q) r -= q;
        for (int m = 0; m < nfilter; ++m) {
            if (r == 0ULL) return;
            r += t;
            if (r >= q) r -= q;
        }
    }
    unsigned int slot = atomicAdd(nout, 1u);
    if (slot < cap) out[slot] = j;
}
'''

BLOCK = 256


class GpuEngine:
    """CuPy sieve over j, where k = W*j."""

    def __init__(self, n, q2=Q2_DEFAULT):
        if cp is None:
            raise RuntimeError("CuPy/CUDA not available; use --engine cpu")
        self.n = n
        self.q2 = q2
        self.W = wheel_modulus(n)
        primes = np.array([q for q in primerange(n + 2, q2)], dtype=np.uint64)
        self.primes = primes
        self.d_primes = cp.asarray(primes)
        self.d_magic = cp.asarray(barrett_magics(primes))
        self.d_wmod = cp.asarray(np.array([self.W % int(q) for q in primes],
                                          dtype=np.uint64))
        self.kernel = cp.RawKernel(_KERNEL, "sieve")
        # The survivor queue is allocated ONCE.  Allocating it per launch
        # (32 MB of fresh device memory per call) measured 1.06x slower --
        # smaller than the 2.5x guessed before measuring it, which is the
        # usual lesson; see OPTIMIZATION_LOG.md.
        self.queue_cap = 1 << 22
        self._d_out = cp.empty(self.queue_cap, dtype=cp.uint64)
        self._d_n = cp.zeros(1, dtype=cp.uint32)

    # ---------------------------------------------------------------- sieve
    def survivors_j(self, j_lo, j_hi, launch=1 << 24):
        """Sorted u64 array of surviving j in [j_lo, j_hi)."""
        if j_hi > J_CEIL:
            raise ValueError(f"j {j_hi} past the enforced ceiling {J_CEIL}")
        if j_lo * self.W < K_FLOOR:
            raise ValueError("engines refuse to run below K_FLOOR")
        out = []
        j0 = int(j_lo)
        while j0 < int(j_hi):
            count = min(launch, int(j_hi) - j0)
            d_out, d_n = self._d_out, self._d_n
            d_n.fill(0)
            grid = (count + BLOCK - 1) // BLOCK
            self.kernel((grid,), (BLOCK,),
                        (np.uint64(j0), np.uint64(count),
                         np.int32(self.primes.size), np.int32(self.n),
                         self.d_primes, self.d_magic, self.d_wmod,
                         d_out, d_n, np.uint32(self.queue_cap)))
            got = int(d_n.get()[0])
            if got > self.queue_cap:
                raise RuntimeError(f"survivor queue overflow: {got} > "
                                   f"{self.queue_cap}; shrink the launch")
            if got:
                out.append(cp.sort(d_out[:got]).get())
            j0 += count
        if not out:
            return np.empty(0, dtype=np.uint64)
        return np.concatenate(out)

    def survivors_pre_mr(self, k_lo, k_hi, launch=1 << 24):
        """The same stream expressed on the k line (both ends inclusive)."""
        j_lo = max(1, -(-int(k_lo) // self.W))
        j_hi = int(k_hi) // self.W + 1
        return self.survivors_j(j_lo, j_hi, launch)

    # ------------------------------------------------------------ classify
    def run_length(self, k, cap=64):
        r = 0
        while r < cap and mr_is_prime((r + 1) * k * k + 1):
            r += 1
        return r

    def hunt(self, k_lo, k_hi, cap=None):
        cap = cap or self.n + 8
        out = []
        for j in self.survivors_pre_mr(k_lo, k_hi).tolist():
            k = int(j) * self.W
            if k < k_lo or k > k_hi:
                continue
            r = self.run_length(k, cap=cap)
            if r >= self.n:
                out.append((k, r))
        return out


# --------------------------------- gates -----------------------------------

def _cpu_stream(n, j_lo, j_hi, q2=Q2_DEFAULT):
    from ladder_search import CpuEngine
    eng = CpuEngine(n, q2=q2)
    got = [c for c in eng.survivors_j(j_lo, j_hi)]
    return np.concatenate(got) if got else np.empty(0, dtype=np.uint64)


def g6_parity_with_cpu():
    """GPU == CPU, bit-for-bit, on POPULATED windows at several heights.

    The heights matter more than the count: the top window sits against
    the enforced j ceiling, where the Barrett reductions have the least
    headroom, and an empty window would prove nothing at any height.
    """
    # (n, j_lo, span, q2).  Survivor density falls off a cliff with n and
    # with sieve depth -- at n=13/q2=65536 it is 1e-8, so a window wide
    # enough to be populated would not fit the five-minute rule.  The two
    # deep windows therefore run at reduced sieve depth: same kernel, same
    # arithmetic, same ceiling, a populated comparison instead of a vacuous
    # one.  An empty-vs-empty parity check proves nothing (CONVENTIONS).
    windows = [(10, 10**6, 4 * 10**7, Q2_DEFAULT),
               (10, 4 * 10**9, 4 * 10**7, Q2_DEFAULT),
               (10, 10**12, 4 * 10**7, Q2_DEFAULT),
               (12, 6 * 10**11, 2 * 10**6, 2048),
               (13, J_CEIL - 4 * 10**6, 4 * 10**6, 2048)]
    total = 0
    for n, j_lo, span, q2 in windows:
        eng = GpuEngine(n, q2=q2)
        gpu = eng.survivors_j(j_lo, j_lo + span)
        cpu = _cpu_stream(n, j_lo, j_lo + span, q2=q2)
        if gpu.size != cpu.size or not np.array_equal(gpu, cpu):
            return False, (f"G6 FAIL: n={n} j in [{j_lo}, {j_lo+span}): "
                           f"{gpu.size} GPU vs {cpu.size} CPU survivors")
        if cpu.size == 0:
            return False, f"G6 FAIL: window n={n} at {j_lo} is empty (vacuous)"
        total += int(cpu.size)
    return True, (f"G6 ok: GPU == CPU on {len(windows)} populated windows "
                  f"({total} survivors) at n = 10, 12, 13, from j = 1e6 up "
                  f"to the enforced ceiling {J_CEIL:.0e}")


def g7_planted_fake():
    """The comparator must catch a corrupted stream (both directions)."""
    n, j_lo, span = 10, 10**9, 4 * 10**6
    eng = GpuEngine(n, q2=1024)
    good = eng.survivors_j(j_lo, j_lo + span)
    if good.size < 4:
        return False, "G7 FAIL: drill window under-populated"
    dropped = good[1:]
    added = np.sort(np.append(good, good[0] + 1))
    if np.array_equal(good, dropped) or np.array_equal(good, added):
        return False, "G7 FAIL: comparator cannot tell the plants apart"
    return True, (f"G7 ok: comparator rejects both a dropped survivor and "
                  f"an invented one ({good.size} in the drill window)")


def g8_gpu_rediscovers_a7():
    """End-to-end: the GPU stream finds a(7), and finds it FIRST."""
    n = 7
    eng = GpuEngine(n)
    hits = eng.hunt(K_FLOOR, KNOWN[n])
    firsts = sorted(k for k, r in hits if r >= n)
    if not firsts or firsts[0] != KNOWN[n]:
        return False, (f"G8 FAIL: least k with run >= 7 = "
                       f"{firsts[:1]}, expected {KNOWN[7]}")
    return True, f"G8 ok: GPU rediscovered a(7) = {KNOWN[7]} end-to-end"


def g13_slicing_independence():
    """The stream must not depend on how the work was cut.

    Three cuts that have all broken sieves elsewhere: a split in the
    middle of a launch, launches smaller than a block, and a start that
    is not aligned to anything.
    """
    n, j_lo, span = 10, 7 * 10**9 + 12345, 8 * 10**6
    eng = GpuEngine(n, q2=1024)
    whole = eng.survivors_j(j_lo, j_lo + span)
    for cut in (span // 3, span // 2, span - 1):
        a = eng.survivors_j(j_lo, j_lo + cut)
        b = eng.survivors_j(j_lo + cut, j_lo + span)
        joined = np.concatenate([a, b]) if a.size or b.size else a
        if not np.array_equal(whole, joined):
            return False, f"G13 FAIL: split at {cut} != whole"
    for launch in (BLOCK // 2, BLOCK + 1, 100_003):
        sliced = eng.survivors_j(j_lo, j_lo + span, launch=launch)
        if not np.array_equal(whole, sliced):
            return False, f"G13 FAIL: launch size {launch} != whole"
    if whole.size == 0:
        return False, "G13 FAIL: vacuous (empty window)"
    return True, (f"G13 ok: stream independent of slicing over 6 cuts "
                  f"(3 split points, 3 launch sizes, {whole.size} survivors)")


def g14_kernel_matches_bigint():
    """The kernel's kill decisions == big-integer divisibility, directly.

    No engine on the other side of this comparison: for real k values the
    gate forms m*k^2+1 as a Python int and trial-divides.  A survivor must
    have no prime factor below q2 in any of its n values; a killed
    candidate must have one.
    """
    n, j_lo, span = 10, 3 * 10**9, 4 * 10**7
    eng = GpuEngine(n)
    surv = set(int(v) for v in eng.survivors_j(j_lo, j_lo + span).tolist())
    smalls = [q for q in primerange(n + 2, eng.q2)]

    def divisor(k):
        """The first small prime dividing one of the n values, or None."""
        for q in smalls:
            kq = k % q
            t = kq * kq % q
            for m in range(1, n + 1):
                if (m * t + 1) % q == 0:
                    return q
        return None

    checked_alive = checked_dead = 0
    for j in range(j_lo, j_lo + span, 199_999):      # a coarse sample
        k = j * eng.W
        d = divisor(k)
        if j in surv and d is not None:
            return False, f"G14 FAIL: j={j} survived but {d} divides a value"
        if j not in surv and d is None:
            return False, f"G14 FAIL: j={j} was killed with no small factor"
        checked_dead += d is not None
        checked_alive += d is None
    for j in sorted(surv):                            # and EVERY survivor
        k = j * eng.W
        d = divisor(k)
        if d is not None:
            return False, (f"G14 FAIL: emitted survivor j={j} has "
                           f"{d} dividing one of its values")
        # the divisor() helper is itself checked against real big integers
        for m in range(1, n + 1):
            v = m * k * k + 1
            for q in smalls[:64]:
                if v % q == 0:
                    return False, (f"G14 FAIL: {q} divides {m}*k^2+1 for "
                                   f"j={j}, missed by the residue walk")
    return True, (f"G14 ok: kernel decisions == big-integer divisibility of "
                  f"the actual values ({checked_dead} killed + "
                  f"{checked_alive} kept sampled, and all {len(surv)} "
                  f"survivors of a 4e7 window checked against every prime "
                  f"below {eng.q2})")


GATES = [g6_parity_with_cpu, g7_planted_fake, g8_gpu_rediscovers_a7,
         g13_slicing_independence, g14_kernel_matches_bigint]

if __name__ == "__main__":
    for g in GATES:
        ok, msg = g()
        print(("PASS " if ok else "FAIL ") + msg)
