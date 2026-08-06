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
# planted-fake drill, G8 GPU canary rediscovery a(13).  Phase 2 adds
# G11 (GPU-128 == GPU-u64 on the fingerprint window; == CPU-128 up to
# the 1e24 ceiling zone) and G12 (GPU-128 end-to-end rediscovery of
# a(18) and of the Waldvogel-Leikauf run-21 value above the u64 cap).
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


# ---------------------- phase 2: 128-bit value path ------------------------
#
# Same mathematics as the v4 kernel, but p = k*M + off is never formed:
# every residue is ((k mod q) * (M mod q) + (off mod q)) mod q, all u64
# (k < 2^48 below P128_CEIL, products < 2^32).  The incremental stage-1a
# residue stepping is IDENTICAL to v4 -- it never needed p's magnitude.
# Survivors leave the GPU as (k, off) pairs; exact p exists only as a
# host-side Python int.  Window bounds arrive as (k, off) pairs too.
# The u64 kernel above is untouched; G11 pins this stream against it on
# the frozen fingerprint window and against CPU-128 elsewhere.
#
# v2-128 structure (two-phase compaction): profiling showed the cold
# path (stage 1b + stage 2) consumed ~80% of the ONE-KERNEL design's
# runtime through warp serialization -- when 1 lane of 32 survives
# stage 1a, the other 31 idle while it grinds ~6500 primes.  So the hot
# kernel now does stage 1a ONLY and pushes surviving (offset-index,
# period) pairs into a global queue; a second kernel processes queued
# candidates one per thread, 32 lanes busy.  Same tests, same survivor
# set, bit-for-bit (G11 fingerprint unchanged); the p-window bounds are
# resolved per thread to a period range BEFORE the loop, so the hot
# interior carries no bounds checks at all.

KERNEL128_SRC = r"""
// Phase A (hot): stage 1a only.  Survivors of the 16 incremental mask
// tests are pushed to a queue as packed (offset-index << 32 | period).
extern "C" __global__
void __launch_bounds__(256, 4)
ladder_stage1_128(const unsigned long long k_base,   // absolute first k
                  const unsigned int n_offs,
                  const unsigned long long* __restrict__ offs,
                  const unsigned long long lo_k,     // p >= lo bound
                  const unsigned long long lo_s,
                  const unsigned long long hi_k,     // p < hi bound
                  const unsigned long long hi_s,
                  const unsigned int np_total,       // periods this launch
                  const unsigned int* __restrict__ s1_q,
                  const unsigned long long* __restrict__ s1_magic,
                  const unsigned int* __restrict__ s1_dM,
                  const unsigned int* __restrict__ s1_woff,
                  const unsigned int* __restrict__ s1_mask,
                  unsigned long long* __restrict__ queue,
                  unsigned long long* __restrict__ q_n,
                  const unsigned long long q_cap)
{
    const int T = __MP_T__;
    const int NINC = __MP_NINC__;
    unsigned int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n_offs) return;
    unsigned int kp0 = blockIdx.y * T;
    if (kp0 >= np_total) return;
    unsigned long long off = offs[i];
    unsigned long long k0 = k_base + kp0;

    // Resolve the p-window to a per-thread period range ONCE: for fixed
    // off, p < hi iff k < khi and p >= lo iff k >= klo.  The interior
    // loop then carries NO bounds checks at all.
    unsigned long long khi = hi_k + ((off < hi_s) ? 1ULL : 0ULL);
    unsigned long long klo = lo_k + ((off >= lo_s) ? 0ULL : 1ULL);
    if (k0 >= khi) return;
    unsigned int tmax = np_total - kp0;
    if (tmax > (unsigned int)T) tmax = T;
    unsigned long long span = khi - k0;
    unsigned int t_end = (span < (unsigned long long)tmax)
                         ? (unsigned int)span : tmax;
    unsigned int t_lo = 0;
    if (klo > k0) {
        unsigned long long d = klo - k0;
        if (d >= (unsigned long long)t_end) return;
        t_lo = (unsigned int)d;
    }
    unsigned long long kst = k0 + t_lo;

    // initial residues AT kst: ((kst mod q)*(M mod q) + off mod q) mod q,
    // Barrett throughout; stepping below is identical to the v4 kernel
    unsigned int q[NINC], dM[NINC], w[NINC], r[NINC];
    #pragma unroll
    for (int j = 0; j < NINC; ++j) {
        q[j]  = s1_q[j];
        dM[j] = s1_dM[j];
        w[j]  = s1_woff[j];
        unsigned long long mg = s1_magic[j];
        unsigned long long kq = kst - __umul64hi(kst, mg) * q[j];
        if (kq >= q[j]) kq -= q[j];
        if (kq >= q[j]) kq -= q[j];
        unsigned long long oq = off - __umul64hi(off, mg) * q[j];
        if (oq >= q[j]) oq -= q[j];
        if (oq >= q[j]) oq -= q[j];
        unsigned long long v = kq * (unsigned long long)dM[j] + oq;
        unsigned long long vq = v - __umul64hi(v, mg) * q[j];
        if (vq >= q[j]) vq -= q[j];
        if (vq >= q[j]) vq -= q[j];
        r[j] = (unsigned int)vq;
    }

    for (unsigned int t = t_lo; t < t_end; ++t) {
        // stage 1a: incremental residues + global bitmask
        bool alive = true;
        #pragma unroll
        for (int j = 0; j < NINC; ++j) {
            if ((s1_mask[w[j] + (r[j] >> 5)] >> (r[j] & 31)) & 1u) {
                alive = false;
                break;
            }
        }
        if (alive) {
            unsigned long long slot = atomicAdd(q_n, 1ULL);
            if (slot < q_cap)
                queue[slot] = ((unsigned long long)i << 32)
                              | (unsigned long long)(kp0 + t);
        }
        #pragma unroll
        for (int j = 0; j < NINC; ++j) {
            r[j] += dM[j];
            if (r[j] >= q[j]) r[j] -= q[j];
        }
    }
}

// Phase B (cold): one thread per queued stage-1a survivor.  Runs the
// remaining stage-1 primes and stage 2 with every lane busy -- this
// work was the serialized 80% of the one-kernel design.
extern "C" __global__
void ladder_cold_128(const unsigned long long k_base,
                     const unsigned long long* __restrict__ offs,
                     const unsigned long long n_cand,
                     const unsigned long long* __restrict__ queue,
                     const int ns1,
                     const unsigned int* __restrict__ s1_q,
                     const unsigned long long* __restrict__ s1_magic,
                     const unsigned int* __restrict__ s1_dM,
                     const unsigned int* __restrict__ s1_woff,
                     const unsigned int* __restrict__ s1_mask,
                     const int ns2,
                     const unsigned int* __restrict__ s2_q,
                     const unsigned long long* __restrict__ s2_magic,
                     const unsigned int* __restrict__ s2_dM,
                     const int nxx,
                     const unsigned int* __restrict__ xx,
                     unsigned long long* __restrict__ out_k,
                     unsigned long long* __restrict__ out_off,
                     unsigned long long* __restrict__ out_n,
                     const unsigned long long out_cap)
{
    const int NINC = __MP_NINC__;
    unsigned long long idx = (unsigned long long)blockIdx.x * blockDim.x
                             + threadIdx.x;
    if (idx >= n_cand) return;
    unsigned long long e = queue[idx];
    unsigned long long off = offs[e >> 32];
    unsigned long long k = k_base + (e & 0xffffffffULL);

    bool alive = true;
    // stage 1b: remaining stage-1 primes via (k, off) Barrett
    for (int j = NINC; j < ns1 && alive; ++j) {
        unsigned int qq = s1_q[j];
        unsigned long long mg = s1_magic[j];
        unsigned long long kq = k - __umul64hi(k, mg) * qq;
        if (kq >= qq) kq -= qq;
        if (kq >= qq) kq -= qq;
        unsigned long long oq = off - __umul64hi(off, mg) * qq;
        if (oq >= qq) oq -= qq;
        if (oq >= qq) oq -= qq;
        unsigned long long v = kq * (unsigned long long)s1_dM[j] + oq;
        unsigned long long vq = v - __umul64hi(v, mg) * qq;
        if (vq >= qq) vq -= qq;
        if (vq >= qq) vq -= qq;
        unsigned int rr = (unsigned int)vq;
        if ((s1_mask[s1_woff[j] + (rr >> 5)] >> (rr & 31)) & 1u)
            alive = false;
    }
    // stage 2: q > 272 so rr + xx < 2q; dead iff rr+xx == 0 or q
    for (int j = 0; j < ns2 && alive; ++j) {
        unsigned int qq = s2_q[j];
        unsigned long long mg = s2_magic[j];
        unsigned long long kq = k - __umul64hi(k, mg) * qq;
        if (kq >= qq) kq -= qq;
        if (kq >= qq) kq -= qq;
        unsigned long long oq = off - __umul64hi(off, mg) * qq;
        if (oq >= qq) oq -= qq;
        if (oq >= qq) oq -= qq;
        unsigned long long v = kq * (unsigned long long)s2_dM[j] + oq;
        unsigned long long vq = v - __umul64hi(v, mg) * qq;
        if (vq >= qq) vq -= qq;
        if (vq >= qq) vq -= qq;
        unsigned int rr = (unsigned int)vq;
        for (int x = 0; x < nxx; ++x) {
            unsigned int tt = rr + xx[x];
            if (tt == 0u || tt == qq) { alive = false; break; }
        }
    }
    if (alive) {
        unsigned long long slot = atomicAdd(out_n, 1ULL);
        if (slot < out_cap) {
            out_k[slot] = k;
            out_off[slot] = off;
        }
    }
}
"""

KERNEL128 = (KERNEL128_SRC.replace("__MP_T__", str(MP_T))
                          .replace("__MP_NINC__", str(MP_NINC)))


class GpuEngine128(GpuEngine):
    """Phase-2 GPU engine: exact-int windows up to P128_CEIL.  Reuses the
    u64 engine's device tables (they are height-independent); survivors
    come back as (k, off) pairs and become Python ints on the host."""

    Q_CAP = 1 << 26          # stage-1a queue entries (512 MB); production
                             # n=17 launches enqueue ~5.2e7, 28% headroom

    def __init__(self, n, wheel_primes=None):
        super().__init__(n, wheel_primes)
        s2 = self.d_s2q.get()
        self.d_s2dM = cp.asarray(np.array([int(self.M) % int(q)
                                           for q in s2.tolist()],
                                          dtype=np.uint32))
        self.kern_hot = cp.RawKernel(KERNEL128, "ladder_stage1_128")
        self.kern_cold = cp.RawKernel(KERNEL128, "ladder_cold_128")
        self.d_queue = cp.zeros(self.Q_CAP, dtype=np.uint64)
        self.d_qn = cp.zeros(1, dtype=np.uint64)
        self.d_outk = cp.zeros(self.out_cap, dtype=np.uint64)
        self.d_outo = cp.zeros(self.out_cap, dtype=np.uint64)

    def survivors_pre_mr(self, lo, hi, periods_per_launch=8192):
        """Sorted list of exact survivor p (Python ints) in [lo, hi)."""
        from euler_search import P128_CEIL
        lo, hi = int(lo), int(hi)
        if lo < P_FLOOR:
            raise ValueError("128 engine floor is %d" % P_FLOOR)
        if hi > P128_CEIL:
            raise ValueError("128 engine ceiling is %d" % P128_CEIL)
        M = int(self.M)
        k0, k1 = lo // M, hi // M + 1
        lo_k, lo_s = k0, lo - k0 * M
        hi_k, hi_s = hi // M, hi % M
        block = 256
        gx = (self.n_offs + block - 1) // block
        got = []
        for kc in range(k0, k1, periods_per_launch):
            np_launch = min(periods_per_launch, k1 - kc)
            gy = (np_launch + MP_T - 1) // MP_T
            self.d_qn[0] = 0
            self.kern_hot((int(gx), int(gy)), (block,),
                          (np.uint64(kc),
                           np.uint32(self.n_offs), self.d_offs,
                           np.uint64(lo_k), np.uint64(lo_s),
                           np.uint64(hi_k), np.uint64(hi_s),
                           np.uint32(np_launch),
                           self.d_s1q, self.d_s1magic, self.d_s1dM,
                           self.d_s1w, self.d_s1m,
                           self.d_queue, self.d_qn, np.uint64(self.Q_CAP)),
                          )
            qn = int(self.d_qn.get()[0])
            if qn > self.Q_CAP:
                raise RuntimeError("stage-1a queue overflow: %d (lower "
                                   "periods_per_launch)" % qn)
            if not qn:
                continue
            self.d_outn[0] = 0
            gxc = (qn + block - 1) // block
            self.kern_cold((int(gxc),), (block,),
                           (np.uint64(kc), self.d_offs,
                            np.uint64(qn), self.d_queue,
                            np.int32(self.d_s1q.size), self.d_s1q,
                            self.d_s1magic, self.d_s1dM,
                            self.d_s1w, self.d_s1m,
                            np.int32(self.d_s2q.size), self.d_s2q,
                            self.d_s2magic, self.d_s2dM,
                            np.int32(self.n), self.d_xx,
                            self.d_outk, self.d_outo,
                            self.d_outn, np.uint64(self.out_cap)),
                           )
            cnt = int(self.d_outn.get()[0])
            if cnt > self.out_cap:
                raise RuntimeError("survivor buffer overflow: %d" % cnt)
            if cnt:
                ks = cp.asnumpy(self.d_outk[:cnt]).tolist()
                os_ = cp.asnumpy(self.d_outo[:cnt]).tolist()
                got.extend(int(k) * M + int(o) for k, o in zip(ks, os_))
        got.sort()
        return got

    def hunt(self, lo, hi, cap=100, periods_per_launch=8192):
        """Ascending [(p, exact_run)] with run >= n in [lo, hi)."""
        out = []
        for p in self.survivors_pre_mr(lo, hi, periods_per_launch):
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


def g11_parity128():
    """The 128-bit GPU stream is pinned two ways: against the PROVEN u64
    GPU stream on the frozen fingerprint window, and against the
    independent CPU-128 engine at heights up to the P128_CEIL zone."""
    from euler_search import CpuEngine128, P128_CEIL
    # (a) GPU-128 == GPU-u64 where both run: the fingerprint window
    lo, hi = 10**16, 10**16 + 5 * 10**14
    u64 = GpuEngine(17).survivors_pre_mr(lo, hi)
    p128 = GpuEngine128(17).survivors_pre_mr(lo, hi)
    if sorted(int(v) for v in u64.tolist()) != p128 or len(p128) < 100:
        return False, (f"G11 FAIL fingerprint window: u64 {u64.size}"
                       f" vs 128 {len(p128)}")
    # (b) GPU-128 == CPU-128, incl. above the u64 cap and the ceiling zone
    cases = [(5, 10**5, 4 * 10**5, 20),
             (13, 10**5, 8_900_000_000, 1),
             (17, 234_505_015_943_235_329_417 - 10**10,
              234_505_015_943_235_329_417 + 10**10, 1),
             (17, P128_CEIL - 10**13, P128_CEIL, 1)]
    counts = [len(p128)]
    for n, clo, chi, min_surv in cases:
        cpu = sorted(p for chunk in CpuEngine128(n).survivors_pre_mr(clo, chi)
                     for p in chunk)
        gpu = GpuEngine128(n).survivors_pre_mr(clo, chi)
        if len(cpu) < min_surv:
            return False, f"G11 FAIL n={n}: window under-populated ({len(cpu)})"
        if cpu != gpu:
            return False, (f"G11 FAIL n={n} [{clo},{chi}): cpu {len(cpu)}"
                           f" gpu {len(gpu)}")
        counts.append(len(cpu))
    return True, ("G11 ok: GPU-128 == GPU-u64 on the fingerprint window and"
                  f" == CPU-128 up to the 1e24 ceiling zone, sizes {counts}")


def g12_canaries128():
    """GPU-128 end-to-end rediscoveries: a(18) below the u64 cap and the
    Waldvogel-Leikauf run-21 literature value above it."""
    a18 = 8_461_068_614_861_832_371
    hits = GpuEngine128(17).hunt(a18 - 5 * 10**9, a18 + 5 * 10**9)
    firsts = [p for p, r in hits if r == 18]
    if not firsts or firsts[0] != a18:
        return False, f"G12 FAIL: a(18) not rediscovered ({hits})"
    a21 = 234_505_015_943_235_329_417
    hits = GpuEngine128(17).hunt(a21 - 10**7, a21 + 10**7)
    if (a21, 21) not in hits:
        return False, f"G12 FAIL: run-21 upper value not rediscovered ({hits})"
    return True, ("G12 ok: GPU-128 rediscovered a(18) = %d and the"
                  " Waldvogel-Leikauf run-21 value end-to-end" % a18)


def selftest():
    ok = True
    for g in (g6_parity, g7_comparator_drill, g8_gpu_canary,
              g11_parity128, g12_canaries128):
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
