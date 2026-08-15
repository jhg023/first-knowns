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
# the 1e24 ceiling zone), G12 (GPU-128 end-to-end rediscovery of
# a(18) and of the Waldvogel-Leikauf run-21 value above the u64 cap)
# and G13 (the v3-128 bit-sieve stream == the proven v2-128 stream,
# bit-for-bit, across pattern-word / thread / launch boundaries).
#
# Three generations of the 128 path live here on purpose: GpuEngine128V2
# is the two-phase compaction engine that phase 2's first 3.6e20 was swept
# with, kept as G13's parity reference, and GpuEngine128 is the v3-128
# bit-sieve production engine.  They must never share their stage-1a
# arithmetic -- that independence is what G13 measures.
#
# ASCII only.

import numpy as np

import cupy as cp

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.gpu import barrett_magics  # noqa: E402

from euler_reference import A21_UPPER, KNOWN
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


# --------------------- phase 2 v3: bit-sieve stage 1a ----------------------
#
# The v2 hot kernel tests ONE candidate at a time: per period it steps all
# MP_NINC residues (add + compare + subtract each, unconditionally, even
# though the average candidate dies at test 2.2) and then walks an
# early-exit chain of bitmask gathers.  Measured on the SCORE128 window it
# is 83.4% of GPU time, and an instruction count explains it: ~48 slots per
# warp-period go to stepping, and the mask chain costs 9.2 warp-iterations
# (mean 2.2 per lane -- a 4.2x warp-divergence tax) each carrying a 32-way
# scattered L1 gather.
#
# v3 inverts the loop.  For prime q let F_q be the killed residue set.  If
# a block of W consecutive periods starts at residue r, then period offset
# u is killed by q iff (r + u*(M mod q)) mod q is in F_q -- a function of
# (q, r) alone.  So the host precomputes pat[q][r], a W-bit word, and the
# kernel ORs ONE word per prime per W periods and reads the survivors out
# of the complement with __ffsll.  Per period that is W times less residue
# stepping and ~W/2.2 times fewer gathers, and the inner loop is
# branch-free over periods, so the divergence tax disappears as well.
# Tables are exact Python integers; the kernel is generated with q, M mod q,
# (W*M) mod q, the Barrett magics and the table offsets as literals, which
# also frees the 3*NINC registers the v2 kernel spends holding values that
# are identical in every thread.
#
# Same mathematics, same survivor set, bit-for-bit: gate G13 pins v3
# against the proven v2 stream on populated windows at four heights.

SIEVE_W = 64             # periods per pattern word (u64); must divide T
MP_NINC128 = 24          # sieve-phase primes (31..139).  An extra prime
                         # costs one OR + one stepped residue per 64 periods
                         # and multiplies the cold queue by (q-17)/q, so
                         # there is an interior optimum.  It MOVED when the
                         # compaction rounds landed: against the single-shot
                         # cold path 28 won (16/24/26/28/32 ->
                         # 1.000/1.363/1.387/1.434/1.349), but rounds made
                         # that path ~3.5x cheaper and the optimum fell to
                         # 24 (16/20/24/28 -> 1.000/1.126/1.143/1.095, and
                         # 24 beats 28 by 1.058x at the production launch
                         # size).  See BENCHMARKS/OPTIMIZATION_LOG.

_SIEVE_INIT = """
    unsigned int r%(j)d;
    {
        const unsigned long long q = %(q)dULL, mg = %(magic)dULL;
        unsigned long long kq = kst - __umul64hi(kst, mg) * q;
        if (kq >= q) kq -= q;
        if (kq >= q) kq -= q;
        unsigned long long oq = off - __umul64hi(off, mg) * q;
        if (oq >= q) oq -= q;
        if (oq >= q) oq -= q;
        unsigned long long v = kq * %(dm)dULL + oq;
        unsigned long long vq = v - __umul64hi(v, mg) * q;
        if (vq >= q) vq -= q;
        if (vq >= q) vq -= q;
        r%(j)d = (unsigned int)vq;
    }"""

_SIEVE_STEP1 = """
        acc[0] |= pat[%(po)du + r%(j)d];
        r%(j)d += %(dmw)du; if (r%(j)d >= %(q)du) r%(j)d -= %(q)du;"""

_SIEVE_STEP2 = """
        {
            const ulonglong2 pw = *(const ulonglong2*)(pat
                                  + ((%(po)du + r%(j)d) << 1));
            acc[0] |= pw.x; acc[1] |= pw.y;
        }
        r%(j)d += %(dmw)du; if (r%(j)d >= %(q)du) r%(j)d -= %(q)du;"""

_SIEVE_STEPN = """
        {
            const unsigned long long* pw = pat
                + (unsigned long long)(%(po)du + r%(j)d) * %(nw)du;
            #pragma unroll
            for (int w = 0; w < %(nw)d; ++w) acc[w] |= pw[w];
        }
        r%(j)d += %(dmw)du; if (r%(j)d >= %(q)du) r%(j)d -= %(q)du;"""

_SIEVE_BODY = r"""
extern "C" __global__
void __launch_bounds__(256, 4)
ladder_sieve_128(const unsigned long long k_base,   // absolute first k
                 const unsigned int n_offs,
                 const unsigned long long* __restrict__ offs,
                 const unsigned long long lo_k,     // p >= lo bound
                 const unsigned long long lo_s,
                 const unsigned long long hi_k,     // p < hi bound
                 const unsigned long long hi_s,
                 const unsigned int np_total,       // periods this launch
                 const unsigned long long* __restrict__ pat,
                 unsigned long long* __restrict__ queue,
                 unsigned long long* __restrict__ q_n,
                 const unsigned long long q_cap)
{
    const unsigned int T = __MP_T__;
    const unsigned int W = __SIEVE_W__;
    const int NW = __SIEVE_NW__;        // W / 64 pattern words per residue
    unsigned int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n_offs) return;
    unsigned int kp0 = blockIdx.y * T;
    if (kp0 >= np_total) return;
    unsigned long long off = offs[i];
    unsigned long long k0 = k_base + kp0;

    // Window resolution: identical algebra to ladder_stage1_128 -- for
    // fixed off, p < hi iff k < khi and p >= lo iff k >= klo, so the
    // period range is resolved ONCE and the interior carries no bounds
    // checks (only the two edge blocks get a validity mask).
    unsigned long long khi = hi_k + ((off < hi_s) ? 1ULL : 0ULL);
    unsigned long long klo = lo_k + ((off >= lo_s) ? 0ULL : 1ULL);
    if (k0 >= khi) return;
    unsigned int tmax = np_total - kp0;
    if (tmax > T) tmax = T;
    unsigned long long span = khi - k0;
    unsigned int t_end = (span < (unsigned long long)tmax)
                         ? (unsigned int)span : tmax;
    unsigned int t_lo = 0;
    if (klo > k0) {
        unsigned long long d = klo - k0;
        if (d >= (unsigned long long)t_end) return;
        t_lo = (unsigned int)d;
    }

    // pattern blocks are aligned to t = 0 within this thread's T-period
    // run, so the union over blockIdx.y still partitions the launch
    unsigned int tb = t_lo & ~(W - 1u);
    unsigned long long kst = k0 + tb;

    // residues at period tb: ((kst mod q)*(M mod q) + off mod q) mod q
__SIEVE_INIT__

    for (unsigned int t = tb; t < t_end; t += W) {
        unsigned long long acc[NW];
        #pragma unroll
        for (int w = 0; w < NW; ++w) acc[w] = 0ULL;
__SIEVE_STEP__
        #pragma unroll
        for (int w = 0; w < NW; ++w) {
            unsigned int b0 = t + 64u * (unsigned int)w;
            if (b0 >= t_end) break;                 // word past the window
            if (b0 + 64u <= t_lo) continue;         // word before it
            unsigned long long valid = ~0ULL;
            if (b0 < t_lo) valid &= (~0ULL) << (t_lo - b0);
            unsigned int rem = t_end - b0;
            if (rem < 64u) valid &= (~0ULL) >> (64u - rem);
            unsigned long long alive = (~acc[w]) & valid;
            while (alive) {
                unsigned int u = (unsigned int)__ffsll((long long)alive) - 1u;
                alive &= alive - 1ULL;
                unsigned long long slot = atomicAdd(q_n, 1ULL);
                if (slot < q_cap)
                    queue[slot] = ((unsigned long long)i << 32)
                                  | (unsigned long long)(kp0 + b0 + u);
            }
        }
    }
}
"""


_ROUND_SRC = r"""
// Phase B0 (compaction rounds).  The single-shot cold kernel lets a warp
// run until its LAST lane dies: over the 134 stage-1b primes the mean exit
// depth is 13.9 tests but the max over 32 lanes is 80.4, so 5.8 of every 7
// warp-iterations are spent on lanes that are already dead.  This kernel
// tests only primes [j0, j1) and forwards the survivors to a second queue,
// so the next round starts with all 32 lanes alive.  Stage 2 is NOT worth
// splitting this way: it is entered by 5.7e-3 of the queue, so at most one
// lane per warp is ever in it and the idle lanes have no work to steal.
//
// The candidate count arrives as a DEVICE pointer, so rounds chain with no
// host round-trip; the grid is fixed and strides over the queue.
extern "C" __global__
void ladder_round_128(const unsigned long long k_base,
                      const unsigned long long* __restrict__ offs,
                      const unsigned long long* __restrict__ n_in,
                      const unsigned long long* __restrict__ qin,
                      const int j0,
                      const int j1,
                      const unsigned int* __restrict__ s1_q,
                      const unsigned long long* __restrict__ s1_magic,
                      const unsigned int* __restrict__ s1_dM,
                      const unsigned int* __restrict__ s1_woff,
                      const unsigned int* __restrict__ s1_mask,
                      unsigned long long* __restrict__ qout,
                      unsigned long long* __restrict__ n_out,
                      const unsigned long long out_cap)
{
    const unsigned long long total = *n_in;
    const unsigned long long stride = (unsigned long long)gridDim.x
                                      * blockDim.x;
    for (unsigned long long idx = (unsigned long long)blockIdx.x * blockDim.x
                                  + threadIdx.x;
         idx < total; idx += stride) {
        unsigned long long e = qin[idx];
        unsigned long long off = offs[e >> 32];
        unsigned long long k = k_base + (e & 0xffffffffULL);
        bool alive = true;
        for (int j = j0; j < j1 && alive; ++j) {
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
        if (alive) {
            unsigned long long slot = atomicAdd(n_out, 1ULL);
            if (slot < out_cap) qout[slot] = e;
        }
    }
}
"""


def sieve_tables(n, M, s1, ninc, W=SIEVE_W, T=MP_T):
    """Exact-integer pattern tables for the first `ninc` stage-1 primes.

    Returns (source_fragments, flat_pattern_array).  pat[po_j + r] has bit
    u set iff q_j divides one of the n values at the period W-block that
    starts with p == r (mod q_j) -- i.e. iff (r + u*(M mod q_j)) mod q_j
    is a forbidden residue of q_j.  Pure Python ints; no numpy modulo, no
    Barrett, nothing shared with the CPU engine.
    """
    if W & (W - 1):
        raise ValueError("SIEVE_W must be a power of two")
    if T % W:
        raise ValueError("SIEVE_W must divide the periods-per-thread T")
    M = int(M)
    nw = W // 64
    tmpl = {1: _SIEVE_STEP1, 2: _SIEVE_STEP2}.get(nw, _SIEVE_STEPN)
    init, step, pat, po = [], [], [], 0
    for j, q in enumerate([int(v) for v in s1[:ninc]]):
        F = forbidden(q, n)
        dm = M % q
        for r in range(q):
            w, rr = 0, r
            for u in range(W):
                if rr in F:
                    w |= 1 << u
                rr += dm
                if rr >= q:
                    rr -= q
            # split the W-bit pattern into nw little-endian u64 words
            for c in range(nw):
                pat.append((w >> (64 * c)) & ((1 << 64) - 1))
        init.append(_SIEVE_INIT % {"j": j, "q": q, "dm": dm,
                                   "magic": (1 << 64) // q})
        step.append(tmpl % {"j": j, "q": q, "po": po, "nw": nw,
                            "dmw": (W * M) % q})
        po += q
    return ("".join(init), "".join(step),
            np.array(pat, dtype=np.uint64))


def sieve_kernel_src(n, M, s1, ninc, W=SIEVE_W, T=MP_T):
    """Generated CUDA source + the pattern table it indexes."""
    init, step, pat = sieve_tables(n, M, s1, ninc, W, T)
    src = (_SIEVE_BODY.replace("__MP_T__", str(T))
                      .replace("__SIEVE_W__", str(W))
                      .replace("__SIEVE_NW__", str(W // 64))
                      .replace("__SIEVE_INIT__", init)
                      .replace("__SIEVE_STEP__", step))
    return src, pat


class GpuEngine128V2(GpuEngine):
    """Phase-2 GPU engine v2 (two-phase compaction, one candidate per
    thread in stage 1a).  Superseded in production by the bit-sieve
    GpuEngine128 below, and kept forever as its parity reference: G13
    pins the two survivor streams bit-for-bit.  Reuses the u64 engine's
    device tables (they are height-independent); survivors come back as
    (k, off) pairs and become Python ints on the host."""

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


class GpuEngine128(GpuEngine128V2):
    """Phase-2 PRODUCTION engine, v3-128: bit-sieve stage 1a.

    Stage 1a stops testing candidates one at a time.  Per prime it ORs a
    single precomputed SIEVE_W-bit kill pattern per SIEVE_W periods and
    extracts survivors from the complement, which removes both the
    per-period residue stepping and the divergent per-candidate gather
    chain that made the v2 hot kernel 83% of GPU time (see the section
    comment above).  The cold phase is the v2 kernel source verbatim,
    recompiled so its first stage-1b prime matches this engine's NINC.

    Survivor stream is bit-identical to v2 (G13) and to CPU-128 (G11);
    the mathematical configuration -- wheel, Q1, Q2, ceiling -- is
    unchanged, so phase-2 checkpoints stay valid across the upgrade.
    """

    NINC = MP_NINC128
    W = SIEVE_W              # pattern width in periods (multiple of 64)
    T = MP_T                 # periods per thread; independent of the v2
                             # kernel's MP_T, which stays frozen
    PPL = 131072             # default periods per launch.  Big launches
                             # matter now that stage 1a is cheap: steady-state
                             # A/B over [2.3e20, +2e15) gave 8192 -> 131072 =
                             # 1.395x (identical streams).  Matches the
                             # launcher's SEG_PERIODS: one launch per segment.
    Q_HEADROOM = 1.25        # queue slack over the exact expected occupancy
    ROUND = 8                # stage-1b primes per compaction round; 0 gives
                             # the single-shot v2 cold path (A/B switch)
    ROUND_GRID = 4096        # fixed grid for the grid-striding round kernel

    def __init__(self, n, wheel_primes=None):
        super().__init__(n, wheel_primes)
        # snapshot the tuning onto the instance: the kernel bakes NINC and T
        # in as literals, so a later change to the class attributes must not
        # be able to desync the compiled kernel from the launch geometry
        self.NINC, self.T, self.PPL = int(self.NINC), int(self.T), int(self.PPL)
        self.ROUND, self.W = int(self.ROUND), int(self.W)
        src, pat = sieve_kernel_src(n, int(self.M), self.d_s1q.get(),
                                    self.NINC, W=self.W, T=self.T)
        self.sieve_src = src
        self.d_pat = cp.asarray(pat)
        self.kern_sieve = cp.RawKernel(src, "ladder_sieve_128")
        # stage-1b compaction schedule; whatever it does not cover is left to
        # the single-shot cold kernel, which also owns stage 2
        ns1 = int(self.d_s1q.size)
        self.rounds, j = [], self.NINC
        while self.ROUND and j < ns1:
            j1 = min(j + self.ROUND, ns1)
            self.rounds.append((j, j1))
            j = j1
        self.cold_j0 = j     # == NINC when ROUND == 0, == ns1 when fully round
        # cold phase: same gated source, first stage-1b prime matched to
        # wherever the rounds stopped (at ns1 its stage-1b loop is empty and
        # it runs stage 2 only)
        self.kern_cold3 = cp.RawKernel(
            KERNEL128_SRC.replace("__MP_T__", str(MP_T))
                         .replace("__MP_NINC__", str(self.cold_j0)),
            "ladder_cold_128")
        self.kern_round = cp.RawKernel(_ROUND_SRC, "ladder_round_128")
        self.d_qn2 = cp.zeros(1, dtype=np.uint64)
        # Stage-1a survival is a deterministic product over the sieve primes,
        # so the queue can be sized exactly instead of guessed: grown on
        # demand below, which also keeps the gate battery's tiny windows from
        # each reserving a production-sized buffer.
        rate = 1.0
        for q in [int(v) for v in self.d_s1q.get()[:self.NINC]]:
            rate *= 1.0 - len(forbidden(q, n)) / q
        self.s1a_rate = rate
        self.d_queue, self.Q_CAP = None, 0

    def _ensure_queue(self, periods):
        """Grow the stage-1a queue(s) to hold one launch of `periods` periods.

        Both ping-pong buffers get the same capacity on purpose: a round's
        output can never exceed its input, and the stage-1a count is checked
        against the capacity right after the sieve, so no round can overflow.
        That makes the chained rounds safe without a per-round host readback
        (an undetected mid-round overflow would corrupt the queue tail and
        silently LOSE survivors, which no amount of headroom can rule out).
        """
        need = int(self.n_offs * periods * self.s1a_rate * self.Q_HEADROOM)
        need = max(need, 1 << 16)
        if need > self.Q_CAP:
            self.d_queue = self.d_queue2 = None  # release before reserving
            cp.get_default_memory_pool().free_all_blocks()
            self.d_queue = cp.zeros(need, dtype=np.uint64)
            # keyed off the ROUND snapshot, never off the mutable schedule:
            # sizing the queues while the schedule happens to be empty must
            # not leave a later round with a null destination
            self.d_queue2 = (cp.zeros(need, dtype=np.uint64)
                             if self.ROUND else None)
            self.Q_CAP = need

    def survivors_pre_mr(self, lo, hi, periods_per_launch=None):
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
        if periods_per_launch is None:
            periods_per_launch = self.PPL
        self._ensure_queue(min(periods_per_launch, k1 - k0))
        got = []
        for kc in range(k0, k1, periods_per_launch):
            np_launch = min(periods_per_launch, k1 - kc)
            gy = (np_launch + self.T - 1) // self.T
            self.d_qn[0] = 0
            self.kern_sieve((int(gx), int(gy)), (block,),
                            (np.uint64(kc),
                             np.uint32(self.n_offs), self.d_offs,
                             np.uint64(lo_k), np.uint64(lo_s),
                             np.uint64(hi_k), np.uint64(hi_s),
                             np.uint32(np_launch), self.d_pat,
                             self.d_queue, self.d_qn, np.uint64(self.Q_CAP)),
                            )
            qn = int(self.d_qn.get()[0])
            if qn > self.Q_CAP:
                raise RuntimeError(
                    "stage-1a queue overflow: %d > %d (expected %.3e at rate "
                    "%.4e); raise Q_HEADROOM or lower periods_per_launch"
                    % (qn, self.Q_CAP,
                       self.n_offs * np_launch * self.s1a_rate, self.s1a_rate))
            if not qn:
                continue
            # stage-1b compaction rounds: counts stay on the device, so the
            # chain costs no host round-trips
            qin, nin = self.d_queue, self.d_qn
            if self.rounds and self.d_queue2 is None:
                raise RuntimeError("compaction rounds active but no second "
                                   "queue was reserved (ROUND changed after "
                                   "the queues were sized)")
            for j0, j1 in self.rounds:
                qout = self.d_queue2 if qin is self.d_queue else self.d_queue
                nout = self.d_qn2 if nin is self.d_qn else self.d_qn
                nout.fill(0)
                self.kern_round((self.ROUND_GRID,), (block,),
                                (np.uint64(kc), self.d_offs, nin, qin,
                                 np.int32(j0), np.int32(j1),
                                 self.d_s1q, self.d_s1magic, self.d_s1dM,
                                 self.d_s1w, self.d_s1m,
                                 qout, nout, np.uint64(self.Q_CAP)),
                                )
                qin, nin = qout, nout
            if self.rounds:
                qn = int(nin.get()[0])
                if not qn:
                    continue
            self.d_outn[0] = 0
            gxc = (qn + block - 1) // block
            self.kern_cold3((int(gxc),), (block,),
                            (np.uint64(kc), self.d_offs,
                             np.uint64(qn), qin,
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

    def hunt(self, lo, hi, cap=100, periods_per_launch=None):
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


def g13_sieve_parity():
    """The v3 bit-sieve stream == the PROVEN v2 stream, bit-for-bit.

    v3 changes how stage 1a is evaluated (W-period pattern words instead of
    one candidate at a time) and chains compaction rounds through stage 1b,
    so the two risk areas are (a) the pattern algebra and (b) the block
    boundaries -- the edge words of a window, windows shorter than one
    pattern word, starts landing mid-word, and launch sizes that are not
    multiples of the periods-per-thread T.  All of them are exercised here
    at four heights, including above the u64 cap and in the ceiling zone,
    plus the resume property (a split stream must equal the unsplit one)
    cut exactly on W, T and launch boundaries.
    """
    M = 6469693230
    # the ceiling-zone height leaves room for the widest window below
    # P128_CEIL (5e14 for the n=17 cases plus the drill span)
    heights = [3 * 10**19, 230 * 10**18, A21_UPPER, 10**24 - 10**15]
    checks = surv = 0
    # n=13 for the boundary algebra: at n=17 a few-hundred-period window is
    # almost always EMPTY, and empty-vs-empty proves nothing (CONVENTIONS).
    # n=13 keeps the same wheel, sieve and rounds but a dense survivor stream.
    # drill_ppl keeps the (much wider) resume-drill window inside the v2
    # reference engine's fixed queue, which the dense n=13 stream overflows
    # ref_ppl is the launch size for the v2 reference: its queue is a fixed
    # 512 MB and cannot take the launches v3 sizes its own queue for.  That
    # is a feature here -- v3 is compared at SEVERAL launch geometries
    # against a v2 stream computed at one, so agreeing across geometries is
    # part of what the gate proves.
    for n, span_periods, ppls, ref_ppl, drill_ppl in (
            (13, 137, (2048, 2049, 1000, 137), 512, 512),
            (17, 77285, (131072, 40000, 8192), 8192, 8192)):
        v3, v2 = GpuEngine128(n), GpuEngine128V2(n)
        W, T = v3.W, v3.T
        for h in heights:
            s = span_periods
            cases = [(h, h + s * M),                       # aligned
                     (h + 1, h + s * M - 1),               # unaligned ends
                     (h + M // 3, h + s * M + M // 7),     # mid-period bounds
                     (h, h + M // 2),                      # sub-period window
                     (h + M - 10, h + M + 10),             # straddles a period
                     (h + 17, h + W * M + 17),             # exactly one word
                     (h + 1, h + (W + 1) * M),             # word + 1
                     (h + T * M - 3 * M, h + T * M + 3 * M)]   # T boundary
            for lo, hi in cases:
                b = v2.survivors_pre_mr(lo, hi, periods_per_launch=ref_ppl)
                for ppl in ppls:
                    a = v3.survivors_pre_mr(lo, hi, periods_per_launch=ppl)
                    checks += 1
                    surv += len(a)
                    if a != b:
                        return False, ("G13 FAIL n=%d [%d,%d) ppl=%d: v3 %d"
                                       " vs v2 %d"
                                       % (n, lo, hi, ppl, len(a), len(b)))
            # resume drill on v3 itself, cut on word/thread/launch boundaries
            lo, hi = h + 7, h + (2 * T + 11) * M + 13
            whole = v3.survivors_pre_mr(lo, hi, periods_per_launch=drill_ppl)
            if whole != v2.survivors_pre_mr(
                    lo, hi, periods_per_launch=drill_ppl or 8192):
                return False, "G13 FAIL n=%d: v3 != v2 on the drill window" % n
            for cut in (lo + 1, lo + (W - 1) * M, lo + W * M, lo + W * M + 5,
                        lo + T * M, lo + T * M + 7, hi - 1):
                split = sorted(
                    v3.survivors_pre_mr(lo, cut, periods_per_launch=drill_ppl)
                    + v3.survivors_pre_mr(cut, hi,
                                          periods_per_launch=drill_ppl))
                checks += 1
                surv += len(whole)
                if split != whole:
                    return False, ("G13 FAIL n=%d split at +%d: %d vs %d"
                                   % (n, cut - lo, len(split), len(whole)))
        del v3, v2
        cp.get_default_memory_pool().free_all_blocks()
    if surv < 1000:
        return False, ("G13 FAIL: only %d survivors compared -- windows are"
                       " too sparse to prove anything" % surv)
    return True, ("G13 ok: v3 == v2 bit-for-bit over %d windows (%d survivors"
                  " compared) incl. word/thread/launch boundaries and the"
                  " resume drill, heights to the 1e24 ceiling"
                  % (checks, surv))


def g14_pattern_tables(trials=40, seed=11):
    """The bit-sieve pattern tables satisfy their ORIGINAL definition.

    G13 pins the v3 stream against v2, and G11 against CPU-128, so a table
    bug would have to survive two independent streams to get through.  This
    gate closes the remaining gap differently: it checks the tables directly
    against the mathematics they encode, with no engine in the loop.  For a
    real candidate p = k*29# + off and a real period offset u, bit u of
    pat[q][p mod q] must equal "q divides one of x^2+x+(p + u*29#) for some
    x < n" -- big-integer divisibility of the actual values, not a restated
    residue identity.
    """
    import random
    for n in (13, 17):
        offs, M = build_wheel(n, WHEEL_PRIMES_29)
        s1, _ = stage_primes(after=WHEEL_PRIMES_29[-1])
        _, _, pat = sieve_tables(n, int(M), s1, MP_NINC128, SIEVE_W)
        qs = [int(q) for q in s1[:MP_NINC128]]
        rng = random.Random(seed + n)
        po = checks = 0
        for q in qs:
            for _ in range(trials):
                k = rng.randrange(5 * 10**10, 6 * 10**10)   # above the u64 cap
                off = int(offs[rng.randrange(offs.size)])
                p = k * int(M) + off
                u = rng.randrange(SIEVE_W)
                bit = (int(pat[po + (p % q)]) >> u) & 1
                pu = p + u * int(M)
                direct = any((pu + x * x + x) % q == 0 for x in range(n))
                if bit != int(direct):
                    return False, ("G14 FAIL n=%d q=%d r=%d u=%d: pattern %d"
                                   " vs divisibility %d"
                                   % (n, q, p % q, u, bit, int(direct)))
                checks += 1
            po += q
    return True, ("G14 ok: pattern bits == big-integer divisibility of the"
                  " actual values, %d checks per n over primes %d..%d"
                  % (checks, qs[0], qs[-1]))


def selftest():
    ok = True
    for g in (g6_parity, g7_comparator_drill, g8_gpu_canary,
              g11_parity128, g12_canaries128, g13_sieve_parity,
              g14_pattern_tables):
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
