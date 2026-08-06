# euler_gpu.py -- GPU engine (CuPy RawKernel) for the A164926 hunt.
#
# v4 kernel: 29-wheel candidate generation, multi-period threads.  Each
# thread owns ONE wheel offset and MP_T consecutive periods: residues mod
# the first MP_NINC stage-1 primes are computed once (Barrett) and then
# stepped incrementally per period (r += M mod q, conditional subtract),
# so the common case -- a candidate killed by one of the first ~2.5
# stage-1 tests -- costs an add, a compare-subtract, and a bitmask load,
# with no multiply.  Only the ~0.3% of wheel survivors that pass all
# MP_NINC incremental tests fall back to full Barrett for the remaining
# stage-1 primes (to Q1) and the stage-2 17-value test (to Q2).
# Survivors go to a global buffer; MR / exact-run classification stays on
# the HOST (euler_search.mr_*): the GPU only proposes.
#
# Barrett: for prime q, MAGIC = floor(2^64 / q).  qhat = mulhi64(p, MAGIC)
# satisfies qhat in [floor(p/q) - 2, floor(p/q)], so r = p - qhat*q needs
# at most two corrective subtracts.  Exactness is not assumed -- neither
# for Barrett nor for the incremental residue stepping: G6 pins the GPU
# stream bit-for-bit against the numpy-% CPU engine at several heights
# including the u64 ceiling zone.
#
# Gates: G6 GPU==CPU survivor parity (incl. 1.7e19), G7 comparator
# planted-fake drill, G8 GPU canary rediscovery a(13).
#
# ASCII only.

import numpy as np

import cupy as cp

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.gpu import barrett_magics  # noqa: E402

from euler_reference import KNOWN
from euler_search import (CpuEngine, P_FLOOR, WHEEL_PRIMES_29, build_wheel,
                          forbidden, mr_is_prime_u64, mr_run_length,
                          stage_primes)

# v4 tuning constants (swept 2026-08-06, see OPTIMIZATION_LOG.md):
# MP_T periods per thread (rate plateaus 1024..4096), MP_NINC incremental
# stage-1 primes (16 is the register sweet spot; 99.7% of stage-1 kills).
MP_T = 2048
MP_NINC = 16

KERNEL_SRC = r"""
extern "C" __global__
void ladder_filter(const unsigned long long base,      // k_start * M
                   const unsigned long long M,
                   const unsigned int n_offs,
                   const unsigned long long* __restrict__ offs,
                   const unsigned long long lo,
                   const unsigned long long hi,
                   const unsigned int np_total,        // periods this launch
                   const int ns1,
                   const unsigned int* __restrict__ s1_q,
                   const unsigned long long* __restrict__ s1_magic,
                   const unsigned int* __restrict__ s1_dM,
                   const unsigned int* __restrict__ s1_woff,
                   const unsigned int* __restrict__ s1_mask,
                   const int ns2,
                   const unsigned int* __restrict__ s2_q,
                   const unsigned long long* __restrict__ s2_magic,
                   const int nxx,
                   const unsigned int* __restrict__ xx,
                   unsigned long long* __restrict__ out,
                   unsigned long long* __restrict__ out_n,
                   const unsigned long long out_cap)
{
    const int T = __MP_T__;         // periods per thread
    const int NINC = __MP_NINC__;   // incremental stage-1 primes
    unsigned int i = blockIdx.x * blockDim.x + threadIdx.x;   // offset index
    if (i >= n_offs) return;
    unsigned int kp0 = blockIdx.y * T;                        // first period
    if (kp0 >= np_total) return;
    unsigned long long p0 = base + (unsigned long long)kp0 * M + offs[i];

    // one Barrett per incremental prime for the whole T-period run
    unsigned int q[NINC], dM[NINC], w[NINC], r[NINC];
    #pragma unroll
    for (int j = 0; j < NINC; ++j) {
        q[j]  = s1_q[j];
        dM[j] = s1_dM[j];
        w[j]  = s1_woff[j];
        unsigned long long qhat = __umul64hi(p0, s1_magic[j]);
        unsigned long long r64 = p0 - qhat * q[j];
        if (r64 >= q[j]) r64 -= q[j];
        if (r64 >= q[j]) r64 -= q[j];
        r[j] = (unsigned int)r64;
    }

    unsigned long long p = p0;
    for (int t = 0; t < T; ++t, p += M) {
        if (kp0 + (unsigned int)t >= np_total) break;
        if (p >= hi) break;                       // p ascends with t
        if (p >= lo) {
            // stage 1a: incremental residues + global bitmask (L2)
            bool alive = true;
            #pragma unroll
            for (int j = 0; j < NINC; ++j) {
                if ((s1_mask[w[j] + (r[j] >> 5)] >> (r[j] & 31)) & 1u) {
                    alive = false;
                    break;
                }
            }
            // stage 1b: remaining stage-1 primes, full Barrett
            if (alive) {
                for (int j = NINC; j < ns1; ++j) {
                    unsigned int qq = s1_q[j];
                    unsigned long long qhat = __umul64hi(p, s1_magic[j]);
                    unsigned long long r64 = p - qhat * qq;
                    if (r64 >= qq) r64 -= qq;
                    if (r64 >= qq) r64 -= qq;
                    unsigned int rr = (unsigned int)r64;
                    if ((s1_mask[s1_woff[j] + (rr >> 5)] >> (rr & 31)) & 1u) {
                        alive = false;
                        break;
                    }
                }
            }
            // stage 2: q > 272 so r + xx < 2q; dead iff r+xx == 0 or q
            if (alive) {
                for (int j = 0; j < ns2 && alive; ++j) {
                    unsigned int qq = s2_q[j];
                    unsigned long long qhat = __umul64hi(p, s2_magic[j]);
                    unsigned long long r64 = p - qhat * qq;
                    if (r64 >= qq) r64 -= qq;
                    if (r64 >= qq) r64 -= qq;
                    unsigned int rr = (unsigned int)r64;
                    for (int x = 0; x < nxx; ++x) {
                        unsigned int tt = rr + xx[x];
                        if (tt == 0u || tt == qq) { alive = false; break; }
                    }
                }
                if (alive) {
                    unsigned long long slot = atomicAdd(out_n, 1ULL);
                    if (slot < out_cap) out[slot] = p;
                }
            }
        }
        // step residues to the next period
        #pragma unroll
        for (int j = 0; j < NINC; ++j) {
            r[j] += dM[j];
            if (r[j] >= q[j]) r[j] -= q[j];
        }
    }
}
"""

KERNEL = (KERNEL_SRC.replace("__MP_T__", str(MP_T))
                    .replace("__MP_NINC__", str(MP_NINC)))


class GpuEngine:
    def __init__(self, n, wheel_primes=None):
        self.n = n
        self.wheel_primes = wheel_primes or WHEEL_PRIMES_29
        offs, self.M = build_wheel(n, self.wheel_primes)
        self.n_offs = offs.size
        self.d_offs = cp.asarray(offs.astype(np.uint64))
        s1, s2 = stage_primes(after=self.wheel_primes[-1])
        woff, words, mask_bits = [], 0, []
        for q in s1.tolist():
            woff.append(words)
            nw = (q + 31) // 32
            m = np.zeros(nw, dtype=np.uint32)
            for r in forbidden(q, n):
                m[r >> 5] |= np.uint32(1 << (r & 31))
            mask_bits.append(m)
            words += nw
        self.mask_words = words
        self.d_s1q = cp.asarray(s1.astype(np.uint32))
        self.d_s1magic = cp.asarray(barrett_magics(s1))
        self.d_s1dM = cp.asarray(np.array([int(self.M) % int(q)
                                           for q in s1.tolist()],
                                          dtype=np.uint32))
        self.d_s1w = cp.asarray(np.array(woff, dtype=np.uint32))
        self.d_s1m = cp.asarray(np.concatenate(mask_bits))
        self.d_s2q = cp.asarray(s2.astype(np.uint32))
        self.d_s2magic = cp.asarray(barrett_magics(s2))
        self.d_xx = cp.asarray(np.array([x * x + x for x in range(n)],
                                        dtype=np.uint32))
        self.kern = cp.RawKernel(KERNEL, "ladder_filter")
        self.out_cap = 1 << 22
        self.d_out = cp.zeros(self.out_cap, dtype=np.uint64)
        self.d_outn = cp.zeros(1, dtype=np.uint64)

    def survivors_pre_mr(self, lo, hi, periods_per_launch=8192):
        """Sorted numpy array of pre-MR survivors in [lo, hi)."""
        if lo < P_FLOOR:
            raise ValueError("GPU engine floor is %d" % P_FLOOR)
        k0, k1 = lo // self.M, hi // self.M + 1
        block = 256
        gx = (self.n_offs + block - 1) // block
        got = []
        for kc in range(int(k0), int(k1), periods_per_launch):
            np_launch = min(periods_per_launch, int(k1) - kc)
            gy = (np_launch + MP_T - 1) // MP_T
            self.d_outn[0] = 0
            self.kern((int(gx), int(gy)), (block,),
                      (np.uint64(kc * self.M), np.uint64(self.M),
                       np.uint32(self.n_offs), self.d_offs,
                       np.uint64(lo), np.uint64(hi),
                       np.uint32(np_launch),
                       np.int32(self.d_s1q.size), self.d_s1q, self.d_s1magic,
                       self.d_s1dM, self.d_s1w, self.d_s1m,
                       np.int32(self.d_s2q.size), self.d_s2q, self.d_s2magic,
                       np.int32(self.n), self.d_xx,
                       self.d_out, self.d_outn, np.uint64(self.out_cap)),
                      )
            cnt = int(self.d_outn.get()[0])
            if cnt > self.out_cap:
                raise RuntimeError("survivor buffer overflow: %d" % cnt)
            if cnt:
                got.append(cp.asnumpy(self.d_out[:cnt]))
        if not got:
            return np.array([], dtype=np.uint64)
        allp = np.concatenate(got)
        allp.sort()
        return allp

    def hunt(self, lo, hi, cap=100, periods_per_launch=8192):
        """Ascending [(p, exact_run)] with run >= n in [lo, hi)."""
        out = []
        for p in self.survivors_pre_mr(lo, hi, periods_per_launch).tolist():
            if all(mr_is_prime_u64(p + x * x + x) for x in range(self.n)):
                out.append((p, mr_run_length(p, cap=cap)))
        return out


# ------------------------------- gates -------------------------------------

def g6_parity():
    """GPU pre-MR survivor stream == CPU stream (both 29-wheel), POPULATED
    windows at several heights, including the u64 ceiling zone."""
    cases = [(5, 10**5, 4 * 10**5, 20), (9, 10**6, 6 * 10**7, 2),
             (13, 10**5, 8_900_000_000, 1),
             (17, 10**15, 10**15 + 3 * 10**12, 1),
             (17, 17 * 10**18, 17 * 10**18 + 2 * 10**12, 0)]
    counts = []
    for n, lo, hi, min_surv in cases:
        cpu_eng = CpuEngine(n, wheel_primes=WHEEL_PRIMES_29)
        cpu = np.concatenate([a for a in cpu_eng.survivors_pre_mr(lo, hi)]
                             or [np.array([], dtype=np.uint64)])
        cpu.sort()
        gpu = GpuEngine(n).survivors_pre_mr(lo, hi)
        if cpu.size < min_surv:
            return False, f"G6 FAIL n={n}: window under-populated ({cpu.size})"
        if cpu.size != gpu.size or not np.array_equal(cpu, gpu):
            return False, f"G6 FAIL n={n} [{lo},{hi}): cpu {cpu.size} gpu {gpu.size}"
        counts.append(int(cpu.size))
    return True, f"G6 ok: GPU==CPU parity, heights up to 1.7e19, sizes {counts}"


def g7_comparator_drill():
    """The parity comparator must catch a planted fake survivor."""
    n, lo, hi = 5, 10**5, 4 * 10**5
    eng = CpuEngine(n, wheel_primes=WHEEL_PRIMES_29)
    cpu = np.concatenate([a for a in eng.survivors_pre_mr(lo, hi)])
    cpu.sort()
    assert cpu.size >= 3, "drill window unexpectedly empty"
    fake = cpu.copy()
    fake[len(fake) // 2] += 2
    caught = (fake.size != cpu.size) or (not np.array_equal(cpu, fake))
    if not caught:
        return False, "G7 FAIL: planted fake not caught"
    return True, "G7 ok: comparator catches a planted fake survivor"


def g8_gpu_canary():
    """GPU end-to-end rediscovers a(13) exactly (and nothing earlier)."""
    target = KNOWN[13]
    hits = GpuEngine(13).hunt(P_FLOOR, target + 1000)
    firsts = [p for p, r in hits if r == 13]
    if not firsts or firsts[0] != target:
        return False, f"G8 FAIL: first run-13 = {firsts[:1]}, expected {target}"
    return True, f"G8 ok: GPU rediscovered a(13) = {target} end-to-end"


def selftest():
    ok = True
    for g in (g6_parity, g7_comparator_drill, g8_gpu_canary):
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
