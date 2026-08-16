# euler_gpu.py -- THE GPU engine for the A164926 hunt (CuPy RawKernel).
#
# ONE engine, spanning [P_FLOOR, P_CEIL) in a single piece.  Every candidate
# is carried as the pair (k, off) with p = k*29# + off, so every sieve test
# reduces to ((k mod q)*(29# mod q) + off mod q) mod q, which stays u64-safe
# at any height below the enforced ceiling 1e24 -- a factor >3 under the
# deterministic Miller-Rabin validity bound 3.317e24.  There is no 2^64
# boundary in the search and no second engine to switch to; the exact p
# exists only on the host, as a Python int.
#
# Pipeline, three kernel stages:
#   stage 1a  bit-sieve over the first NINC stage-1 primes: one precomputed
#             W-period kill pattern OR-ed per prime per W periods, survivors
#             extracted from the complement with __ffsll, pushed to a queue
#             as (off, kp) -- the offset's VALUE, so nothing downstream has
#             to gather it back out of the offset table
#   stage 1b  compaction ROUNDS over the remaining stage-1 primes: each round
#             is its own GENERATED kernel with its primes unrolled and their
#             moduli, magics and mask offsets as literals, and forwards
#             survivors to a second queue, so every round restarts with all
#             32 lanes alive instead of letting a warp run until its last
#             lane dies
#   stage 2   primes Q1..Q2, one thread per surviving candidate; the kill
#             test is a bit probe rather than a scan over the n values,
#             because every stage-2 prime exceeds max(x^2+x) (see _S2_BITSET)
# Every grid is fixed and every count stays on the device, so a launch is
# enqueued end to end and reaches the host exactly once -- however many
# offset CHUNKS it is cut into (see CHUNK: the queue is bounded by offsets in
# flight, not by the launch's period count, which is what lets T stay large).
# Miller-Rabin and exact-run classification stay on the HOST: the GPU only
# ever PROPOSES (euler_search.mr_*).
#
# Barrett: for prime q, MAGIC = floor(2^64 / q).  qhat = mulhi64(p, MAGIC)
# satisfies qhat in [floor(p/q) - 2, floor(p/q)], so r = p - qhat*q needs at
# most two corrective subtracts.  Exactness is never assumed -- G6 pins this
# whole stream bit-for-bit against the numpy-`%` CPU reference.
#
# Gates here: G6 GPU == CPU reference on populated windows at seven heights
# (to the ceiling zone), G7 comparator planted-fake drill, G8 canary
# rediscovery of a(13), G12 canary rediscovery of a(18) and the
# Waldvogel-Leikauf run-21 value, G13 slicing-independence across launch
# geometries, split points AND offset-chunk sizes, G14 pattern tables ==
# big-integer divisibility in both layouts, G15 the bitset test and the
# 32-bit reductions (including the off-split's 2^32 bound at its worst
# case) == exact integer arithmetic.  See ../OPTIMIZATION.md for why the
# engine is shaped this way, and RESULTS.md for what the retired engines
# were.
#
# ASCII only.

import os

import numpy as np

import cupy as cp

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.gpu import barrett_magics  # noqa: E402

from euler_reference import A21_UPPER, KNOWN
from euler_search import (CpuEngine, M_WHEEL_29, P_CEIL, P_FLOOR,
                          WHEEL_PRIMES,
                          WHEEL_PRIMES_29, WHEEL_PRIMES_31, best_wheel,
                          build_wheel, forbidden, mr_is_prime, mr_run_length,
                          stage_primes)

MP_T = 4096              # TARGET periods per thread; __init__ derives the real
                         # T from it and PPL so the grid's y-slices come out
                         # even.  4096 rather than 2048 because at the
                         # production PPL it resolves to a single y-slice,
                         # halving the thread count -- and the sieve's
                         # per-thread cost is real: fitting sieve = a + b/T
                         # over T = 192..2176 gives 239 ms of pattern loop plus
                         # 109449/T ms of per-thread setup, 17.4% of the kernel
                         # at T=2176.  Worth 1.022x.

_COLD_SRC = r"""
// Phase B (cold): one thread per queued stage-1a survivor.  Runs the
// remaining stage-1 primes and stage 2 with every lane busy -- this
// work was the serialized 80% of the one-kernel design.
extern "C" __global__
void ladder_cold_128(const unsigned long long k_base,
                     const unsigned long long* __restrict__ offs,
                     const unsigned long long* __restrict__ n_in,
                     const unsigned long long in_cap,
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
                     const unsigned int* __restrict__ s2_kbq,
                     const unsigned int* __restrict__ s2_m32,
                     const unsigned int* __restrict__ s2_c,
                     const int nxx,
                     const unsigned int* __restrict__ xx,
                     unsigned long long* __restrict__ out_k,
                     unsigned long long* __restrict__ out_off,
                     unsigned long long* __restrict__ out_n,
                     const unsigned long long out_cap)
{
    const int NINC = __MP_NINC__;
    // The candidate count arrives as a DEVICE pointer and the grid strides,
    // exactly as in ladder_round_128, so the whole sieve -> rounds -> cold
    // chain is enqueued without a host round-trip.  `in_cap` clamps the read:
    // on a stage-1a overflow the count exceeds what was actually written, and
    // the host raises straight afterwards -- but the clamp is what stops the
    // kernel dereferencing uninitialised queue entries in the meantime.
    const unsigned long long total = (*n_in < in_cap) ? *n_in : in_cap;
    const unsigned long long stride = (unsigned long long)gridDim.x
                                      * blockDim.x;
    for (unsigned long long idx = (unsigned long long)blockIdx.x * blockDim.x
                                  + threadIdx.x;
         idx < total; idx += stride) {
    unsigned long long e = queue[idx];
__UNPACK__
__OSPLIT__
    unsigned long long k = k_base + (unsigned long long)kp;
    unsigned int rr;

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
        rr = (unsigned int)vq;
        if ((s1_mask[s1_woff[j] + (rr >> 5)] >> (rr & 31)) & 1u)
            alive = false;
    }
    // stage 2
    for (int j = 0; j < ns2 && alive; ++j) {
        unsigned int qq = s2_q[j];
__S2RED__
__S2TEST__
    }
    if (alive) {
        unsigned long long slot = atomicAdd(out_n, 1ULL);
        if (slot < out_cap) {
            out_k[slot] = k;
            out_off[slot] = off;
        }
    }
    }
}
"""

# Stage-2 kill test, two ways.  `scan` walks the n values of x^2+x and asks
# whether any is == 0 or q mod q -- n table reads and n branches per prime,
# run to completion on every survivor because a kill is rare (17/q).
#
# `bitset` uses the fact that the test is a membership question about a set
# that never changes: q | p + x^2 + x means rr == -(x^2+x) mod q, and every
# stage-2 prime exceeds max(x^2+x) = (n-1)^2 + (n-1), so no residue wraps.
# Hence rr is killed iff rr == 0 (the x = 0 case) or q - rr is itself of the
# form x^2 + x -- one bounds test and one bit probe of a 273-bit table,
# branch-free, instead of a 17-iteration loop.  The kernel argument pair
# (nxx, xx) carries (n, the x^2+x values) for `scan` and (xxmax, the packed
# bitset) for `bitset`, so the signature and the call site are shared.
# The same reduction split as _R_MIX32, for stage 2.  The u32 bound is
# tighter here because q can reach 65521, but kq*dM + oq is still below
# q^2 + q = 4.293e9 < 2^32 -- G15 checks that for every stage-2 prime rather
# than trusting the arithmetic.
_S2_RED_U64 = """        {
            unsigned long long mg = s2_magic[j];
            unsigned long long k = k_base + (unsigned long long)kp;
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
            rr = (unsigned int)vq;
        }"""

_S2_RED_MIX32 = """        {
            const unsigned int m32 = s2_m32[j];
            unsigned int kx = s2_kbq[j] + kp;
            unsigned int kq = kx - __umulhi(kx, m32) * qq;
            if (kq >= qq) kq -= qq;
            if (kq >= qq) kq -= qq;
            unsigned long long oq = off - __umul64hi(off, s2_magic[j]) * qq;
            if (oq >= qq) oq -= qq;
            if (oq >= qq) oq -= qq;
            unsigned int v = kq * s2_dM[j] + (unsigned int)oq;
            unsigned int vq = v - __umulhi(v, m32) * qq;
            if (vq >= qq) vq -= qq;
            if (vq >= qq) vq -= qq;
            rr = vq;
        }"""

# Stage 2 with the same split as the baked rounds: off = oa*2^s + ob, so
# off mod q needs no 64-bit Barrett either.  The split point is WIDER here
# (q reaches 65521, so the product oa*(2^s mod q) has less room), which is
# why it is derived per stage rather than shared -- off_split does that and
# G15 checks the resulting bound against every stage-2 prime.
_S2_RED_SPLIT32 = """        {
            const unsigned int m32 = s2_m32[j];
            unsigned int kx = s2_kbq[j] + kp;
            unsigned int kq = kx - __umulhi(kx, m32) * qq;
            if (kq >= qq) kq -= qq;
            if (kq >= qq) kq -= qq;
            unsigned int oq = oa * s2_c[j] + ob;
            oq = oq - __umulhi(oq, m32) * qq;
            if (oq >= qq) oq -= qq;
            if (oq >= qq) oq -= qq;
            unsigned int v = kq * s2_dM[j] + oq;
            unsigned int vq = v - __umulhi(v, m32) * qq;
            if (vq >= qq) vq -= qq;
            if (vq >= qq) vq -= qq;
            rr = vq;
        }"""

_S2_SCAN = """        for (int x = 0; x < nxx; ++x) {
            unsigned int tt = rr + xx[x];
            if (tt == 0u || tt == qq) { alive = false; break; }
        }"""

_S2_BITSET = """        {
            unsigned int d = qq - rr;          // rr != 0 => d in [1, qq)
            if (rr == 0u || (d <= (unsigned int)nxx
                             && ((xx[d >> 5] >> (d & 31)) & 1u)))
                alive = false;
        }"""


# ---------------------------- the bit-sieve --------------------------------
#
# Stage 1a does not test candidates one at a time.  For prime q let F_q be
# the residues it kills.  If a block of W consecutive wheel periods starts
# at residue r, then period offset u is killed by q exactly when
# (r + u*(M mod q)) mod q is in F_q -- a function of (q, r) alone.  So the
# host precomputes pat[q][r], a W-bit kill pattern, and the kernel ORs ONE
# word per prime per W periods, then reads the survivors straight out of the
# complement with __ffsll.
#
# Versus testing each candidate: W times less residue stepping, ~W/2.2 times
# fewer table lookups, and -- the part that mattered most -- an inner loop
# that is branch-free over candidates, so the early-exit chain's warp
# divergence disappears instead of merely shrinking.  Measured 4.47x on the
# frozen window when it landed; see ../OPTIMIZATION.md section 2.1.
#
# Tables are exact Python integers (G14 pins them against big-integer
# divisibility of the actual values).  The kernel is generated with q,
# M mod q, (W*M) mod q, the Barrett magics and the table offsets as
# literals, which also frees the registers a per-thread copy would need.

SIEVE_INIT_FORM = "mix32"   # residue seeding: "mix32" or "u64"
SIEVE_MARCH = True       # lay the pattern table out in VISIT ORDER.
                         # The inner loop's index sequence for prime q is
                         # r_s = (r_0 + s*dmw) mod q, so the kernel carried a
                         # residue per prime and stepped it: an add and a
                         # conditional subtract per prime per pattern word,
                         # on the critical path of the NEXT iteration's
                         # address.  dmw is invertible mod q (q divides
                         # neither W nor M), so storing G[m] = pat[m*dmw mod q]
                         # makes the sequence m_s = m_0 + s -- a walk of
                         # STRIDE ONE, shared by every prime.  Hoist
                         # `gs = pat + s` out of the prime list and the whole
                         # step collapses to `acc |= gs[po_q + m_q]`: the
                         # add/compare/subtract disappears and the residue
                         # registers become loop-invariant.
                         # Costs T/W - 1 words of tail padding per prime
                         # (the table is periodic, so the tail is a copy of
                         # the head) -- 21.5 KB -> 29.1 KB at the production
                         # T, which matters because the footprint cliff
                         # (Phase 3) starts somewhere below 86 KB.
SIEVE_LB = 2             # min blocks/SM in the sieve's __launch_bounds__; 0
                         # omits the clause and lets the compiler choose.  At 4
                         # the compiler is held to 64 registers and SPILLS (24
                         # B of local memory per thread); the optimum sits just
                         # past where the spill disappears, and it MOVES with
                         # the register demand.  It was 3 at NINC=28; at
                         # NINC=26 (two fewer live residues) it is 2:
                         # 2/3/4/0 -> 1.000/0.990/0.972/0.995.
SIEVE_W = 64             # periods per pattern word (u64); must divide T
SIEVE_NINC = 26          # sieve-phase primes.  An extra prime costs one OR
                         # plus one stepped residue per W periods and multiplies
                         # the cold queue by (q-r_q)/q, so there is an interior
                         # optimum -- and it MOVES with every structural change
                         # around it.  Measured history, each interleaved:
                         #   single-shot cold path, 29# wheel:  28
                         #   + stage-1b compaction rounds:      24 (rounds made
                         #     the cold path ~3.5x cheaper, so it was worth
                         #     handing work back to it)
                         #   + 31# wheel:                       28 (folding 31
                         #     into the wheel pushed the sieve range up to
                         #     37.., costing its strongest killer -- 31 kills
                         #     52% of candidates, 149 only 11% -- so the queue
                         #     per unit p-line grew 1.41x until NINC came back
                         #     up).  At 31#: 24/26/28/30/32/36 ->
                         #     1.110/1.152/1.212/1.159/1.160/0.874 vs the
                         #     previous 29#/24 config.
                         #   + baked stage-1b rounds:            26 (they cut
                         #     stage 1b 2.39x, so handing a prime BACK to it
                         #     got cheaper and the optimum fell again).  At
                         #     22/24/26/28/30 -> 1.000/0.998/1.020/0.976/0.960.
                         # See BENCHMARKS.md and ../OPTIMIZATION.md.

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

# Seeding the residues is not a rounding error: measured by forcing T down and
# fitting, the sieve costs 239 ms of pattern loop + 109449/T ms of per-thread
# init, i.e. **17.4% of the kernel at T=2176** -- and it is what decides
# whether a wider wheel can ever pay, since a longer period leaves each thread
# fewer periods to amortize it over.
#
# Same trick as _R_MIX32: only off mod q genuinely needs 64 bits.  k is never
# formed -- the host passes k_base mod q per launch and the thread adds its own
# (kp0 + tb), which is bounded by PPL -- and the recombination kq*dM + oq is
# below q^2 + q, under 2^20 for any stage-1 prime.
_SIEVE_INIT32 = """
    unsigned int r%(j)d;
    {
        const unsigned int q = %(q)du, m32 = %(m32)du;
        unsigned int kx = kbq[%(j)d] + kk;
        unsigned int kq = kx - __umulhi(kx, m32) * q;
        if (kq >= q) kq -= q;
        if (kq >= q) kq -= q;
        unsigned long long oq = off - __umul64hi(off, %(magic)dULL)
                                      * (unsigned long long)q;
        if (oq >= q) oq -= q;
        if (oq >= q) oq -= q;
        unsigned int v = kq * %(dm)du + (unsigned int)oq;
        unsigned int vq = v - __umulhi(v, m32) * q;
        if (vq >= q) vq -= q;
        if (vq >= q) vq -= q;
        r%(j)d = vq;
    }"""

# The marched forms.  `m` is the position in the visit-order table, and it
# advances by exactly one per pattern word for EVERY prime, so the advance is
# hoisted into a single pointer bump shared by all NINC primes.  Seeding pays
# one extra 32-bit multiply-reduce (m0 = r0 * dmw^-1 mod q, both factors < q
# so the product is under 2^32 for any stage-1 prime).
_SIEVE_INIT_M = _SIEVE_INIT.replace("        r%(j)d = (unsigned int)vq;", """
        v = vq * %(dmwinv)dULL;
        vq = v - __umul64hi(v, mg) * q;
        if (vq >= q) vq -= q;
        if (vq >= q) vq -= q;
        r%(j)d = (unsigned int)vq;""")

_SIEVE_INIT32_M = _SIEVE_INIT32.replace("        r%(j)d = vq;", """
        v = vq * %(dmwinv)du;
        vq = v - __umulhi(v, m32) * q;
        if (vq >= q) vq -= q;
        if (vq >= q) vq -= q;
        r%(j)d = vq;""")

_SIEVE_STEP1_M = """
        acc[0] |= gs[%(po)du + r%(j)d];"""

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
void __SIEVE_LB__
ladder_sieve_128(const unsigned long long k_base,   // absolute first k
                 const unsigned int n_offs,
                 const unsigned long long* __restrict__ offs,
                 const unsigned long long lo_k,     // p >= lo bound
                 const unsigned long long lo_s,
                 const unsigned long long hi_k,     // p < hi bound
                 const unsigned long long hi_s,
                 const unsigned int np_total,       // periods this launch
                 const unsigned int* __restrict__ kbq,   // k_base mod q
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
    unsigned int kk = kp0 + tb;

    // residues at period tb: ((kst mod q)*(M mod q) + off mod q) mod q
__SIEVE_INIT__
__SIEVE_MARCH_DECL__
    for (unsigned int t = tb; t < t_end; t += W) {
        unsigned long long acc[NW];
        #pragma unroll
        for (int w = 0; w < NW; ++w) acc[w] = 0ULL;
__SIEVE_STEP__
__SIEVE_MARCH_INC__
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
                    queue[slot] = __PACK__
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
                      const unsigned int* __restrict__ s1_kbq,
                      const unsigned int* __restrict__ s1_m32,
                      const unsigned int* __restrict__ xxt,
                      unsigned long long* __restrict__ qout,
                      unsigned long long* __restrict__ n_out,
                      const unsigned long long out_cap)
{
    // both ping-pong queues are allocated at the same capacity, so out_cap
    // is also the input capacity; clamp for the same reason as the cold
    // kernel (see there) -- an overflowed count must not become a wild read.
    const unsigned long long tin = *n_in;
    const unsigned long long total = (tin < out_cap) ? tin : out_cap;
    const unsigned long long stride = (unsigned long long)gridDim.x
                                      * blockDim.x;
    for (unsigned long long idx = (unsigned long long)blockIdx.x * blockDim.x
                                  + threadIdx.x;
         idx < total; idx += stride) {
        unsigned long long e = qin[idx];
__UNPACK__
__OSPLIT__
        bool alive = true;
__PRIMES__
        if (alive) {
            unsigned long long slot = atomicAdd(n_out, 1ULL);
            if (slot < out_cap) qout[slot] = e;
        }
    }
}
"""


# Queue entry layout, two ways.  A stage-1a survivor is the pair (off, kp):
# which wheel offset, and which period inside the launch.
#
# `index` stores the offset's INDEX, so every consumer -- each compaction
# round and the cold kernel -- has to gather offs[i] back out of a table that
# is 240 MB on the production wheel.  That is one scattered DRAM read per
# queue entry per round, and it buys nothing: the sieve already had `off` in
# a register when it pushed.
#
# `value` stores `off` itself, shifted up by KSHIFT bits to leave room for
# kp.  It fits because off < M (38 bits on the 31# wheel) and kp < PPL, so
# the pair needs 38 + ceil(log2 PPL) bits; the engine derives KSHIFT from M
# and REFUSES the layout if a launch could ever overflow it, rather than
# assuming (../OPTIMIZATION.md 2.9 -- store the unit, assert it).
_UNPACK_INDEX_COLD = """    unsigned long long off = offs[e >> 32];
    unsigned int kp = (unsigned int)(e & 0xffffffffULL);"""
_UNPACK_VALUE_COLD = """    unsigned long long off = e >> __KSHIFT__;
    unsigned int kp = (unsigned int)(e & __KMASK__ULL);"""
_UNPACK_INDEX_ROUND = """        unsigned long long off = offs[e >> 32];
        unsigned int kp = (unsigned int)(e & 0xffffffffULL);"""
_UNPACK_VALUE_ROUND = """        unsigned long long off = e >> __KSHIFT__;
        unsigned int kp = (unsigned int)(e & __KMASK__ULL);"""


# Stage-1b residue reduction, two ways.  Both compute
# rr = (k*M + off) mod q with k = k_base + kp.
#
# `u64` reduces k, off and the recombination with the 64-bit Barrett magic --
# three __umul64hi, each of which the compiler expands into several IMADs
# because it is a 64x64->128 high multiply.
#
# `mix32` keeps only the reduction that genuinely needs 64 bits.  off < M can
# be ~2^38, so it stays.  But k mod q does not need k: the host already knows
# k_base mod q, and kp is the low 32 bits of the queue entry, so
# (k_base mod q) + kp is a u32 -- and the recombination kq*dM + oq is bounded
# by q^2 + q, which for a stage-1 prime (q < 1024) is under 2^21 and for a
# stage-2 prime (q < 65536) is still under 2^32.  Both become __umulhi.
# Barrett stays exact: for x < 2^32 and m32 = floor(2^32/q) the quotient
# estimate is short by at most one, so the same two conditional subtracts
# that the 64-bit path uses are more than sufficient.
_R_U64 = """            unsigned long long mg = s1_magic[j];
            unsigned long long k = k_base + (unsigned long long)kp;
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
            unsigned int rr = (unsigned int)vq;"""

_R_MIX32 = """            const unsigned int m32 = s1_m32[j];
            unsigned int kx = s1_kbq[j] + kp;
            unsigned int kq = kx - __umulhi(kx, m32) * qq;
            if (kq >= qq) kq -= qq;
            if (kq >= qq) kq -= qq;
            unsigned long long oq = off - __umul64hi(off, s1_magic[j]) * qq;
            if (oq >= qq) oq -= qq;
            if (oq >= qq) oq -= qq;
            unsigned int v = kq * s1_dM[j] + (unsigned int)oq;
            unsigned int vq = v - __umulhi(v, m32) * qq;
            if (vq >= qq) vq -= qq;
            if (vq >= qq) vq -= qq;
            unsigned int rr = vq;"""

# Table-driven stage 1b (the loop above), for reference and for the gate that
# pins the generated form against it.
_ROUND_TABLE = """        for (int j = j0; j < j1 && alive; ++j) {
            unsigned int qq = s1_q[j];
__RTEST__
            if ((s1_mask[s1_woff[j] + (rr >> 5)] >> (rr & 31)) & 1u)
                alive = false;
        }"""

# BAKED stage 1b (catalogue 2.5, applied to a phase that never had it).  The
# round kernel's inner loop read SIX values per prime out of global arrays --
# q, the 64-bit magic, M mod q, the mask's word offset, k_base mod q and the
# 32-bit magic -- all warp-uniform, all costing an instruction and an L1
# broadcast.  Five of the six are properties of the prime and are known when
# the kernel is generated, so they become literals; only k_base mod q changes
# per launch and stays a load.
#
# Two more things fall out of generating the source:
#
#   * `off mod q` no longer needs 64-bit Barrett.  Split off = a*2^s + b with
#     s chosen so that a*(2^s mod q) + b < 2^32 for every prime in the stage
#     (the engine derives s and G15 checks the bound), and one __umulhi
#     replaces __umul64hi plus a 64-bit multiply, subtract and two 64-bit
#     conditional subtracts.  a and b are computed ONCE per candidate,
#     outside the prime list.
#   * primes above max(x^2+x) can use the stage-2 bitset identity instead of
#     the per-prime forbidden-residue mask: rr is killed iff rr == 0 or
#     q - rr is itself of the form x^2+x.  That trades a gather into the
#     ~10 KB stage-1 mask table for a probe of the 36-byte x^2+x bitset.
_R_PRIME_HEAD = """
        if (alive) {
            const unsigned int qq = %(q)du, m32 = %(m32)du;
            unsigned int kx = s1_kbq[%(j)d] + kp;
            unsigned int kq = kx - __umulhi(kx, m32) * qq;
            if (kq >= qq) kq -= qq;
            if (kq >= qq) kq -= qq;
%(ored)s
            unsigned int v = kq * %(dm)du + oq;
            unsigned int rr = v - __umulhi(v, m32) * qq;
            if (rr >= qq) rr -= qq;
            if (rr >= qq) rr -= qq;
%(test)s
        }"""

_O_SPLIT32 = """            unsigned int oq = oa * %(c)du + ob;
            oq = oq - __umulhi(oq, m32) * qq;
            if (oq >= qq) oq -= qq;
            if (oq >= qq) oq -= qq;"""

_O_U64 = """            unsigned long long o64 = off - __umul64hi(off, %(magic)dULL)
                                            * (unsigned long long)qq;
            if (o64 >= qq) o64 -= qq;
            if (o64 >= qq) o64 -= qq;
            unsigned int oq = (unsigned int)o64;"""

_R_TEST_MASK = """            if ((s1_mask[%(woff)du + (rr >> 5)] >> (rr & 31)) & 1u)
                alive = false;"""

_R_TEST_BITSET = """            {
                unsigned int d = qq - rr;
                if (rr == 0u || (d <= %(xxmax)du
                                 && ((xxt[d >> 5] >> (d & 31)) & 1u)))
                    alive = false;
            }"""


def off_split(M, qmax):
    """Bit position s at which `off` can be split for a 32-bit reduction.

    off mod q == ((off >> s)*(2^s mod q) + (off & (2^s - 1))) mod q exactly;
    what the 32-bit Barrett needs is that the right-hand side never reaches
    2^32.  The bound is (M >> s)*(q - 1) + 2^s, which is convex in s, so
    scan and take the first s that clears it.  Returns None when no split
    works (then the caller keeps 64-bit arithmetic).
    """
    M, qmax = int(M), int(qmax)
    for s in range(1, 64):
        if (M >> s) * (qmax - 1) + (1 << s) < (1 << 32):
            return s
    return None


def round_kernel_src(s1_list, j0, j1, form="baked", rtest="mix32",
                     ored="split32", spl=None, xxmax=0, M=0, woff=None):
    """Generated stage-1b compaction-round kernel for primes [j0, j1).

    `baked` unrolls the prime list with q, M mod q, the magics and the mask
    offsets as literals (catalogue 2.5); `table` keeps the original indexed
    loop and is what the generated form is gated against.
    """
    if form == "table":
        body = _ROUND_TABLE.replace("__RTEST__",
                                    _R_MIX32 if rtest == "mix32" else _R_U64)
        osp = ""
    else:
        out = []
        for j in range(j0, j1):
            q = int(s1_list[j])
            m32 = (1 << 32) // q
            if ored == "split32" and spl:
                o = _O_SPLIT32 % {"c": (1 << spl) % q}
            else:
                o = _O_U64 % {"magic": (1 << 64) // q}
            if xxmax and q > xxmax:
                t = _R_TEST_BITSET % {"xxmax": xxmax}
            else:
                t = _R_TEST_MASK % {"woff": int(woff[j])}
            out.append(_R_PRIME_HEAD % {"q": q, "m32": m32, "j": j,
                                        "dm": int(M) % q, "ored": o,
                                        "test": t})
        body = "".join(out)
        osp = ("        const unsigned int oa = (unsigned int)(off >> %du);\n"
               "        const unsigned int ob = (unsigned int)(off & %dULL);"
               % (spl, (1 << spl) - 1)) if (ored == "split32" and spl) else ""
    return (_ROUND_SRC.replace("__PRIMES__", body)
                      .replace("__OSPLIT__", osp))


def sieve_layout(n, M, s1, ninc, W=SIEVE_W, T=MP_T, march=SIEVE_MARCH):
    """Per-prime table geometry: where prime j's words live and how the
    kernel indexes them.  ONE source of truth, so the generator and G14
    cannot drift apart (../OPTIMIZATION.md 2.9)."""
    M, nw, po, out = int(M), W // 64, 0, []
    pad = (T // W) - 1 if march else 0    # tail copies for the stride-1 walk
    for j, q in enumerate([int(v) for v in s1[:ninc]]):
        dmw = (W * M) % q
        if march and dmw == 0:
            raise ValueError("q=%d divides W*M: the marched table needs "
                             "dmw invertible" % q)
        out.append({"j": j, "q": q, "po": po, "nw": nw, "dm": M % q,
                    "dmw": dmw, "rows": q + pad,
                    "dmwinv": pow(dmw, -1, q) if march else 0,
                    "magic": (1 << 64) // q, "m32": (1 << 32) // q})
        po += q + pad          # ROW units; the step templates scale by nw
    return out


def sieve_tables(n, M, s1, ninc, W=SIEVE_W, T=MP_T, form=SIEVE_INIT_FORM,
                 march=SIEVE_MARCH):
    """Exact-integer pattern tables for the first `ninc` stage-1 primes.

    Returns (init_src, step_src, flat_pattern_array, layout).  In the plain
    layout pat[po_j + r] has bit u set iff q_j divides one of the n values at
    the period W-block that starts with p == r (mod q_j) -- i.e. iff
    (r + u*(M mod q_j)) mod q_j is a forbidden residue of q_j.  In the MARCHED
    layout the same words are stored in the order the inner loop visits them,
    pat[po_j + m] = plain[po_j + (m*dmw_j mod q_j)], extended past q_j by the
    table's own period so a thread's whole run is a stride-1 walk.  Pure
    Python ints; no numpy modulo, no Barrett, nothing shared with the CPU
    engine.
    """
    if W & (W - 1):
        raise ValueError("SIEVE_W must be a power of two")
    if T % W:
        raise ValueError("SIEVE_W must divide the periods-per-thread T")
    if march and W != 64:
        raise ValueError("the marched layout is defined for W=64 only")
    M = int(M)
    nw = W // 64
    tmpl = (_SIEVE_STEP1_M if march else
            {1: _SIEVE_STEP1, 2: _SIEVE_STEP2}.get(nw, _SIEVE_STEPN))
    init, step, pat = [], [], []
    for e in sieve_layout(n, M, s1, ninc, W, T, march):
        q, dm = e["q"], e["dm"]
        F = forbidden(q, n)
        plain = []
        for r in range(q):
            w, rr = 0, r
            for u in range(W):
                if rr in F:
                    w |= 1 << u
                rr += dm
                if rr >= q:
                    rr -= q
            # split the W-bit pattern into nw little-endian u64 words
            plain.append([(w >> (64 * c)) & ((1 << 64) - 1)
                          for c in range(nw)])
        for m in range(e["rows"]):
            r = (m * e["dmw"]) % q if march else m
            pat.extend(plain[r])
        init.append((_SIEVE_INIT32_M if march else _SIEVE_INIT32)
                    if form == "mix32" else
                    (_SIEVE_INIT_M if march else _SIEVE_INIT))
        init[-1] = init[-1] % e
        step.append(tmpl % e)
    return ("".join(init), "".join(step),
            np.array(pat, dtype=np.uint64),
            sieve_layout(n, M, s1, ninc, W, T, march))


def sieve_kernel_src(n, M, s1, ninc, W=SIEVE_W, T=MP_T, lb=SIEVE_LB,
                     form=SIEVE_INIT_FORM, march=SIEVE_MARCH, block=256):
    """Generated CUDA source + the pattern table it indexes.

    `block` is baked into __launch_bounds__ and must be the block size the
    launcher actually uses -- a knob changed after compilation desyncing the
    kernel from its geometry is a bug this project has already shipped once
    (OPTIMIZATION_LOG, "two robustness bugs the gates caught").
    """
    init, step, pat, _ = sieve_tables(n, M, s1, ninc, W, T, form, march)
    src = (_SIEVE_BODY.replace("__MP_T__", str(T))
                      .replace("__SIEVE_W__", str(W))
                      .replace("__SIEVE_NW__", str(W // 64))
                      .replace("__SIEVE_LB__",
                               "__launch_bounds__(%d, %d)" % (block, lb)
                               if lb else "")
                      .replace("__SIEVE_INIT__", init)
                      .replace("__SIEVE_MARCH_DECL__",
                               "    const unsigned long long* __restrict__"
                               " gs = pat;" if march else "")
                      .replace("__SIEVE_MARCH_INC__",
                               "        ++gs;" if march else "")
                      .replace("__SIEVE_STEP__", step))
    return src, pat


class GpuEngine:
    """THE GPU engine.  Bit-sieve -> compaction rounds -> cold stage 2.

    Covers [P_FLOOR, P_CEIL) in one piece; see the module header for the
    (k, off) representation that makes the 2^64 boundary a non-event.
    Survivors leave the device as (k, off) pairs and become Python ints on
    the host.  Tuning constants are class attributes and are snapshotted
    onto the instance in __init__, because the kernel bakes NINC, W and T in
    as literals -- changing a class attribute afterwards must not be able to
    desync the compiled kernel from the launch geometry.
    """

    NINC = SIEVE_NINC        # primes handled by the bit-sieve
    SIEVE_LB = SIEVE_LB      # sieve __launch_bounds__ min blocks/SM (0 = none)
    SIEVE_INIT_FORM = SIEVE_INIT_FORM
    SIEVE_MARCH = SIEVE_MARCH   # visit-order pattern table (see the constant)
    W = SIEVE_W              # pattern width in periods (multiple of 64)
    T = MP_T                 # periods per thread -- a TARGET, not the final
                             # value: __init__ re-derives it from PPL so the
                             # sieve grid's y-slices come out even
    LAUNCH_SPAN = 131072 * 6469693230    # ~8.48e14 of p-line per launch.
                             # Expressed as a SPAN, not a period count, so it
                             # is wheel-independent: the period is 31x longer
                             # on the 31# wheel, and 131072 of those would
                             # want a 17 GB queue.  Big launches matter now
                             # that stage 1a is cheap -- steady-state A/B over
                             # [2.3e20, +2e15) gave 8192 -> 131072 periods =
                             # 1.395x on the 29# wheel, identical streams.
    PPL = None               # periods per launch; derived from LAUNCH_SPAN,
                             # the wheel period and QUEUE_BUDGET unless set
    QUEUE_BUDGET = 220_000_000   # max stage-1a queue entries in flight, i.e.
                             # ~1.8 GB per ping-pong buffer.  This used to cap
                             # PPL, which made the launch's PERIOD count a
                             # function of the memory budget -- and since T is
                             # derived from PPL, a wheel with a longer period
                             # left each thread too few periods to amortize its
                             # setup over.  That coupling is what priced the
                             # 37# wheel at 0.75x in Phase 4.  It was never
                             # necessary: the launch is now cut along the
                             # OFFSET axis instead (CHUNK below), so PPL is set
                             # purely by LAUNCH_SPAN and the queue is bounded
                             # by how many offsets are in flight at once.
    CHUNK = None             # offsets per sieve->rounds->cold chain; derived
                             # from QUEUE_BUDGET unless set.  One chunk (the
                             # whole offset table) reproduces the pre-chunking
                             # launch exactly, which is what the 31# wheel
                             # still resolves to.
    ROUND = 16               # stage-1b primes per compaction round; 0 sends
                             # all of stage 1b to the single cold kernel.
                             # Moves with everything around it.  On 29#: peak
                             # 8.  The 31# wheel shifted work into stage 1b and
                             # moved it to 16.  Making the stage-1b reduction
                             # 32-bit (_R_MIX32) made each prime cheaper, so
                             # the peak moved out again: 16/20/24/28/34 ->
                             # 1.000/1.016/1.023/1.009/0.978.  Note 24 MEASURED
                             # 0.984 before that change and 1.023 after -- the
                             # direction reversed, which is why this is
                             # re-swept after every structural change and never
                             # reasoned about.  Baking the round kernels moved
                             # it back to 16: 8/12/16/20/24/34 ->
                             # 0.938/0.988/1.000/0.983/0.959/0.918.
    BLOCK = 256              # threads per block, for every kernel.  Baked into
                             # the sieve's __launch_bounds__ from the same
                             # snapshot the launcher uses, so the two cannot
                             # disagree
    ROUND_GRID = 4096        # fixed grid for the grid-striding round kernel;
                             # swept 2048/4096/8192/16384 -> 1.002/1.000/
                             # 1.002/1.000, i.e. the stride loop does not care
    COLD_GRID = 4096         # ditto for the cold kernel, which strides too so
                             # that its count never has to reach the host
    S2_TEST = "bitset"       # stage-2 kill test: "bitset" or "scan"
    Q_FORM = "value"         # queue entry: "value" (off itself) or "index"
    ROUND_FORM = "baked"     # stage-1b kernel: "baked" (per-prime literals,
                             # one kernel per round) or "table" (indexed loop)
    O_RED = "split32"        # `off mod q` in the baked rounds: "split32" or
                             # "u64" (see off_split)
    R_TEST = "mix32"         # stage-1b reduction width: "mix32" or "u64"
    S2_RED = "split32"       # stage-2 reduction: "split32", "mix32" or "u64"
    Q_HEADROOM = 1.25        # queue slack over the exact expected occupancy

    def __init__(self, n, wheel_primes=None):
        self.n = n
        # the largest wheel whose offset table fits the budget: fewer
        # candidates generated, identical survivor set (see euler_search)
        self.wheel_primes = wheel_primes or best_wheel(n)
        offs, self.M = build_wheel(n, self.wheel_primes)
        self.n_offs = offs.size
        self.d_offs = cp.asarray(offs.astype(np.uint64))
        s1, s2 = stage_primes(after=self.wheel_primes[-1])

        # stage-1 forbidden-residue bitmasks, packed end to end (L2-resident)
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
        # 32-bit Barrett magics + the per-launch (k_base mod q) table that let
        # stage 1b reduce k without ever forming k (see _R_MIX32)
        self.s1_list = [int(q) for q in s1.tolist()]
        self.np_s1q = s1.astype(np.uint64)
        self.d_s1m32 = cp.asarray(np.array([(1 << 32) // q
                                            for q in self.s1_list],
                                           dtype=np.uint32))
        self.h_s1kbq = np.zeros(len(self.s1_list), dtype=np.uint32)
        self.d_s1kbq = cp.zeros(len(self.s1_list), dtype=np.uint32)
        self.d_s2q = cp.asarray(s2.astype(np.uint32))
        self.d_s2magic = cp.asarray(barrett_magics(s2))
        self.d_s2dM = cp.asarray(np.array([int(self.M) % int(q)
                                           for q in s2.tolist()],
                                          dtype=np.uint32))
        self.np_s2q = s2.astype(np.uint64)
        self.d_s2m32 = cp.asarray(np.array([(1 << 32) // int(q)
                                            for q in s2.tolist()],
                                           dtype=np.uint32))
        self.h_s2kbq = np.zeros(int(s2.size), dtype=np.uint32)
        self.d_s2kbq = cp.zeros(int(s2.size), dtype=np.uint32)
        self.d_xx = cp.asarray(np.array([x * x + x for x in range(n)],
                                        dtype=np.uint32))

        # stage-2 kill test: see _S2_SCAN / _S2_BITSET.  The bitset form is
        # only valid while every stage-2 prime exceeds max(x^2+x), which is
        # what makes q - rr an unwrapped membership question; assert it
        # rather than assume it, and fall back to the scan if it ever fails.
        self.S2_TEST = str(self.S2_TEST)
        self.xxmax = (n - 1) * (n - 1) + (n - 1)
        if self.S2_TEST == "bitset" and int(s2[0]) <= self.xxmax:
            self.S2_TEST = "scan"
        if self.S2_TEST == "bitset":
            bits = np.zeros((self.xxmax >> 5) + 1, dtype=np.uint32)
            for x in range(n):
                v = x * x + x
                bits[v >> 5] |= np.uint32(1 << (v & 31))
            self.d_s2tab = cp.asarray(bits)
            self.s2_nxx = self.xxmax
        else:
            self.d_s2tab = self.d_xx
            self.s2_nxx = n

        # snapshot the tuning before anything is compiled against it
        self.NINC, self.W, self.T = int(self.NINC), int(self.W), int(self.T)
        self.ROUND = int(self.ROUND)
        if self.PPL:
            self.PPL = int(self.PPL)
        else:
            self.PPL = max(self.W, int(self.LAUNCH_SPAN // int(self.M)))
        # offsets in flight per chain: the queue holds CHUNK * PPL * rate
        # entries, so this is what QUEUE_BUDGET actually bounds
        if self.CHUNK:
            self.CHUNK = min(int(self.CHUNK), self.n_offs)
        else:
            self.CHUNK = min(self.n_offs,
                             max(1 << 14,
                                 int(self.QUEUE_BUDGET
                                     / max(self.PPL * self._s1a_rate(s1) *
                                           self.Q_HEADROOM, 1.0))))
        self.nchunks = -(-self.n_offs // self.CHUNK)

        # Balance the sieve grid.  blockIdx.y indexes a slice of T periods and
        # the last slice takes the remainder, but per-thread setup -- NINC
        # Barrett reductions to seed the residues -- is paid in full by every
        # slice however few periods it ends up with.  At PPL = 4228 a flat
        # T = 2048 gives slices of 2048/2048/132, so a third of the threads
        # pay full setup for a sixteenth of the work.  So pick the slice count
        # from the target first, then divide PPL evenly over it, rounded up to
        # a whole pattern block: 4228 -> gy = 2, T = 2176, slices 2176/2052.
        # Measured 1.066x, and it is derived rather than tuned because PPL
        # moves with the wheel, with n, and with LAUNCH_SPAN.
        gy = max(1, int(round(self.PPL / float(self.T))))
        per = -(-self.PPL // gy)                       # ceil(PPL / gy)
        self.T = max(self.W, -(-per // self.W) * self.W)

        # Queue entry layout (see _UNPACK_*).  `value` needs off and kp to
        # share 64 bits; derive the split from M and REFUSE it -- fall back to
        # the index form -- if a launch of PPL periods could overflow kp.
        self.Q_FORM = str(self.Q_FORM)
        self.KSHIFT = 64 - int(self.M).bit_length()
        if self.PPL > (1 << self.KSHIFT):
            self.Q_FORM = "index"
        if self.Q_FORM == "index" and self.n_offs >= (1 << 32):
            raise RuntimeError("offset table too large for the index queue "
                               "form (%d offsets)" % self.n_offs)

        self.SIEVE_LB, self.BLOCK = int(self.SIEVE_LB), int(self.BLOCK)
        # kx = (k_base mod q) + (kp0 + tb) must not wrap a u32; kp0 + tb is
        # bounded by one launch's period count plus a slice, so this is the
        # same guard the other two 32-bit reductions carry
        # ONE derivation of the stage-1 off-split point (2.9: a derived
        # quantity computed in two places will eventually disagree)
        self.spl = off_split(self.M, max(self.s1_list))
        self.SIEVE_INIT_FORM = str(self.SIEVE_INIT_FORM)
        if self.PPL + self.T + int(s1[self.NINC - 1]) >= (1 << 32):
            self.SIEVE_INIT_FORM = "u64"
        # the marched layout is derived for W=64 (one word per residue)
        self.SIEVE_MARCH = bool(self.SIEVE_MARCH) and self.W == 64
        src, pat = sieve_kernel_src(n, int(self.M), s1, self.NINC,
                                    W=self.W, T=self.T, lb=self.SIEVE_LB,
                                    form=self.SIEVE_INIT_FORM,
                                    march=self.SIEVE_MARCH, block=self.BLOCK)
        src = src.replace("__PACK__",
                          "(off << %du)" % self.KSHIFT
                          if self.Q_FORM == "value"
                          else "((unsigned long long)i << 32)")
        self.sieve_src = src
        self.d_pat = cp.asarray(pat)
        self.kern_sieve = cp.RawKernel(src, "ladder_sieve_128")

        # stage-1b compaction schedule; whatever it does not cover is left to
        # the cold kernel, which also owns stage 2 (at cold_j0 == ns1 its
        # stage-1b loop is empty and it runs stage 2 only)
        ns1 = int(s1.size)
        self.rounds, j = [], self.NINC
        while self.ROUND and j < ns1:
            j1 = min(j + self.ROUND, ns1)
            self.rounds.append((j, j1))
            j = j1
        self.cold_j0 = j
        self.S2_RED = str(self.S2_RED)
        if self.PPL + int(s2[-1]) >= (1 << 32):
            self.S2_RED = "u64"
        # stage-2 split point.  Its primes reach 65521, so the product
        # oa*(2^s mod q) has far less room than stage 1b's and needs its own
        # s -- derived, and checked against every stage-2 prime by G15.
        self.spl2 = (off_split(self.M, int(s2[-1]))
                     if self.S2_RED == "split32" else None)
        if self.S2_RED == "split32" and not self.spl2:
            self.S2_RED = "mix32"
        self.d_s2c = cp.asarray(np.array(
            [(1 << (self.spl2 or 0)) % int(q) for q in s2.tolist()],
            dtype=np.uint32))
        val = self.Q_FORM == "value"
        unpack = (lambda s: s.replace("__KSHIFT__", str(self.KSHIFT))
                             .replace("__KMASK__",
                                      "0x%x" % ((1 << self.KSHIFT) - 1)))
        self.kern_cold = cp.RawKernel(
            _COLD_SRC.replace("__MP_NINC__", str(self.cold_j0))
                     .replace("__UNPACK__",
                              unpack(_UNPACK_VALUE_COLD) if val
                              else _UNPACK_INDEX_COLD)
                     .replace("__OSPLIT__",
                              "    const unsigned int oa = "
                              "(unsigned int)(off >> %du);\n"
                              "    const unsigned int ob = "
                              "(unsigned int)(off & %dULL);"
                              % (self.spl2, (1 << self.spl2) - 1)
                              if self.spl2 else "")
                     .replace("__S2RED__",
                              _S2_RED_SPLIT32 if self.S2_RED == "split32"
                              else (_S2_RED_MIX32 if self.S2_RED == "mix32"
                                    else _S2_RED_U64))
                     .replace("__S2TEST__",
                              _S2_BITSET if self.S2_TEST == "bitset"
                              else _S2_SCAN),
            "ladder_cold_128")
        # kx = (k_base mod q) + kp must not wrap a u32 for _R_MIX32 to hold
        if self.PPL + max(self.s1_list) >= (1 << 32):
            self.R_TEST = "u64"
        self.ROUND_FORM, self.O_RED = str(self.ROUND_FORM), str(self.O_RED)
        if not self.spl:
            self.O_RED = "u64"
        rxx = self.xxmax if self.S2_TEST == "bitset" else 0
        self.kern_rounds = [
            cp.RawKernel(
                round_kernel_src(self.s1_list, j0, j1,
                                 form=self.ROUND_FORM, rtest=self.R_TEST,
                                 ored=self.O_RED, spl=self.spl, xxmax=rxx,
                                 M=int(self.M), woff=woff)
                .replace("__UNPACK__",
                         unpack(_UNPACK_VALUE_ROUND) if val
                         else _UNPACK_INDEX_ROUND),
                "ladder_round_128")
            for j0, j1 in self.rounds]

        # Stage-1a survival is a deterministic product over the sieve primes,
        # so the queue is sized exactly rather than guessed; grown on demand
        # below, which keeps the gate battery's tiny windows from each
        # reserving a production-sized buffer.
        self.s1a_rate = self._s1a_rate(s1)

        self.out_cap = 1 << 22
        self.d_outk = cp.zeros(self.out_cap, dtype=np.uint64)
        self.d_outo = cp.zeros(self.out_cap, dtype=np.uint64)
        self.d_outn = cp.zeros(1, dtype=np.uint64)
        # one stage-1a counter per chunk, so a launch still reaches the host
        # exactly ONCE however many chains it is cut into
        self.d_qn = cp.zeros(self.nchunks, dtype=np.uint64)
        # one output counter per compaction round, in a single array: the
        # rounds used to ping-pong between two counters and zero one per
        # round, which is a host-side launch each.  One fill per chain
        # instead -- the counters are already distinct, so nothing else
        # changes.
        self.d_rn = cp.zeros(max(1, len(self.rounds)), dtype=np.uint64)
        self.d_queue, self.d_queue2, self.Q_CAP = None, None, 0

    def _s1a_rate(self, s1):
        """Exact stage-1a survival: a deterministic product over the sieve
        primes, so queue sizing is computed rather than guessed."""
        rate = 1.0
        for q in [int(v) for v in s1.tolist()[:self.NINC]]:
            rate *= 1.0 - len(forbidden(q, self.n)) / q
        return rate

    def _ensure_queue(self, periods):
        """Grow the stage-1a queue(s) to hold one launch of `periods` periods.

        Both ping-pong buffers get the same capacity on purpose: a round's
        output can never exceed its input, and the stage-1a count is checked
        against the capacity right after the sieve, so no round can overflow.
        That makes the chained rounds safe without a per-round host readback
        (an undetected mid-round overflow would corrupt the queue tail and
        silently LOSE survivors, which no amount of headroom can rule out).
        """
        need = int(min(self.CHUNK, self.n_offs) * periods * self.s1a_rate
                   * self.Q_HEADROOM)
        need = max(need, 1 << 16)
        if need > self.Q_CAP:
            self.d_queue = self.d_queue2 = None   # release before reserving
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
        lo, hi = int(lo), int(hi)
        if lo < P_FLOOR:
            raise ValueError("GPU engine floor is %d" % P_FLOOR)
        if hi > P_CEIL:
            raise ValueError("GPU engine ceiling is %d" % P_CEIL)
        M = int(self.M)
        k0, k1 = lo // M, hi // M + 1
        lo_k, lo_s = k0, lo - k0 * M
        hi_k, hi_s = hi // M, hi % M
        block = self.BLOCK
        if periods_per_launch is None:
            periods_per_launch = self.PPL
        self._ensure_queue(min(periods_per_launch, k1 - k0))
        got = []
        for kc in range(k0, k1, periods_per_launch):
            np_launch = min(periods_per_launch, k1 - kc)
            gy = (np_launch + self.T - 1) // self.T
            # (k_base mod q) for this launch, uploaded once: the sieve's
            # first NINC entries and stage 1b's the rest, so neither ever has
            # to reduce k itself
            self.h_s1kbq[:] = np.uint64(kc) % self.np_s1q
            self.d_s1kbq.set(self.h_s1kbq)
            self.h_s2kbq[:] = np.uint64(kc) % self.np_s2q
            self.d_s2kbq.set(self.h_s2kbq)
            self.d_qn.fill(0)
            self.d_outn.fill(0)
            # The launch is cut along the OFFSET axis: each chunk runs the
            # whole sieve -> rounds -> cold chain over its own slice of the
            # offset table, so the queue only ever holds one chunk's
            # survivors.  Chunk c owns d_qn[c], so no chain has to be waited
            # on -- the launch still reaches the host exactly once, at the end.
            for c, c0 in enumerate(range(0, self.n_offs, self.CHUNK)):
                cn = min(self.CHUNK, self.n_offs - c0)
                offs = self.d_offs[c0:c0 + cn]
                gx = (cn + block - 1) // block
                qn_c = self.d_qn[c:c + 1]
                self.kern_sieve((int(gx), int(gy)), (block,),
                                (np.uint64(kc),
                                 np.uint32(cn), offs,
                                 np.uint64(lo_k), np.uint64(lo_s),
                                 np.uint64(hi_k), np.uint64(hi_s),
                                 np.uint32(np_launch), self.d_s1kbq,
                                 self.d_pat, self.d_queue, qn_c,
                                 np.uint64(self.Q_CAP)),
                                )
                # stage-1b compaction rounds, then the cold kernel: every
                # count stays on the device and every grid is fixed, so the
                # whole chain is enqueued without a single host round-trip.
                # The round counters ping-pong between d_qn2 and d_qn3 and
                # never touch qn_c, so the stage-1a count survives the chain
                # and can be overflow-checked at the end instead of mid-stream.
                qin, nin = self.d_queue, qn_c
                if self.rounds and self.d_queue2 is None:
                    raise RuntimeError("compaction rounds active but no second"
                                       " queue was reserved (ROUND changed"
                                       " after the queues were sized)")
                if self.rounds:
                    self.d_rn.fill(0)
                for r, ((j0, j1), kern) in enumerate(zip(self.rounds,
                                                         self.kern_rounds)):
                    qout = (self.d_queue2 if qin is self.d_queue
                            else self.d_queue)
                    nout = self.d_rn[r:r + 1]
                    kern((self.ROUND_GRID,), (block,),
                         (np.uint64(kc), offs, nin, qin,
                          np.int32(j0), np.int32(j1),
                          self.d_s1q, self.d_s1magic, self.d_s1dM,
                          self.d_s1w, self.d_s1m,
                          self.d_s1kbq, self.d_s1m32, self.d_s2tab,
                          qout, nout, np.uint64(self.Q_CAP)),
                         )
                    qin, nin = qout, nout
                self.kern_cold((int(self.COLD_GRID),), (block,),
                               (np.uint64(kc), offs,
                                nin, np.uint64(self.Q_CAP), qin,
                                np.int32(self.d_s1q.size), self.d_s1q,
                                self.d_s1magic, self.d_s1dM,
                                self.d_s1w, self.d_s1m,
                                np.int32(self.d_s2q.size), self.d_s2q,
                                self.d_s2magic, self.d_s2dM,
                                self.d_s2kbq, self.d_s2m32, self.d_s2c,
                                np.int32(self.s2_nxx), self.d_s2tab,
                                self.d_outk, self.d_outo,
                                self.d_outn, np.uint64(self.out_cap)),
                               )
            # the launch's ONE host round-trip: every chunk's stage-1a
            # overflow check and the survivor count come back together
            qns = self.d_qn.get()
            qn = int(qns.max())
            if qn > self.Q_CAP:
                raise RuntimeError(
                    "stage-1a queue overflow: %d > %d (expected %.3e at rate "
                    "%.4e); raise Q_HEADROOM or lower CHUNK"
                    % (qn, self.Q_CAP,
                       min(self.CHUNK, self.n_offs) * np_launch
                       * self.s1a_rate, self.s1a_rate))
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
            if all(mr_is_prime(p + x * x + x) for x in range(self.n)):
                out.append((p, mr_run_length(p, cap=cap)))
        return out


# ------------------------------- gates -------------------------------------

G6_CASES = [(5, 10**5, 4 * 10**5, 20),
            (9, 10**6, 6 * 10**7, 2),
            (13, 10**5, 8_900_000_000, 1),
            (17, 10**15, 10**15 + 3 * 10**12, 1),
            (17, 17 * 10**18, 17 * 10**18 + 2 * 10**12, 1),
            (17, A21_UPPER - 10**10, A21_UPPER + 10**10, 1),
            (17, P_CEIL - 10**13, P_CEIL, 1)]

G6_SPLIT_PERIODS = 128   # reference sub-window size, in 29# wheel periods


def _g6_cpu(job):
    """Worker: the numpy reference over ONE sub-window, in its own process.

    Module-level and self-contained so it survives Windows spawn.  It touches
    no GPU -- the reference is plain numpy -- so the workers never contend
    with the parent's device work.
    """
    n, lo, hi = job
    return sorted(p for chunk in CpuEngine(n, wheel_primes=WHEEL_PRIMES_29)
                  .survivors_pre_mr(lo, hi) for p in chunk)


def _g6_jobs(n, lo, hi):
    """Cut [lo, hi) into contiguous, disjoint sub-windows.

    Their concatenation is exactly the reference sweep of the whole window,
    because survivors_pre_mr filters to [lo, hi) exactly.  The cuts land at
    arbitrary p (not period boundaries) on purpose.
    """
    span = G6_SPLIT_PERIODS * M_WHEEL_29
    if hi - lo <= span:
        return [(n, lo, hi)]
    cuts = list(range(lo, hi, span)) + [hi]
    return [(n, a, b) for a, b in zip(cuts, cuts[1:])]


def g6_parity(workers=None):
    """THE parity gate: GPU stream == CPU reference stream, bit-for-bit.

    Two independent implementations of the hot path, as CONVENTIONS
    requires -- Barrett bit-sieve on the device, plain numpy `%` on the host,
    neither calling the other -- compared on POPULATED windows (an
    empty-vs-empty comparison proves nothing and does not count).

    Heights deliberately straddle everything that used to be a boundary:
    the low range the oracle also covers, the old u64 ceiling zone, the
    Waldvogel-Leikauf run-21 value, and the 1e24 ceiling zone.  The retired
    u64-only kernel could not reach the last three at all, so this is
    strictly more coverage than the pre-unification G6+G11 pair it replaces.

    The reference side is swept in PARALLEL, one process per sub-window,
    while the parent runs the GPU sweeps -- this gate was 89% of the battery
    and the reference is single-threaded numpy by design (it may not be
    optimized; its slowness and its independence are the point).  Nothing
    about the comparison changes except that the reference now arrives as a
    concatenation of sub-windows while the GPU still sweeps each window
    UNSPLIT, so a boundary bug on either side breaks the gate -- strictly
    more than the old unsplit-vs-unsplit form could catch.
    """
    from concurrent.futures import ProcessPoolExecutor
    jobs, owner = [], []
    for ci, (n, lo, hi, _) in enumerate(G6_CASES):
        for j in _g6_jobs(n, lo, hi):
            jobs.append(j)
            owner.append(ci)
    if workers is None:
        workers = min(12, len(jobs), os.cpu_count() or 4)

    cpus, gpus = [[] for _ in G6_CASES], []
    if workers <= 1:
        parts = [_g6_cpu(j) for j in jobs]
        gpus = [_g6_gpu(n, lo, hi) for n, lo, hi, _ in G6_CASES]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_g6_cpu, j) for j in jobs]
            # the device work overlaps the pool instead of queueing after it
            gpus = [_g6_gpu(n, lo, hi) for n, lo, hi, _ in G6_CASES]
            parts = [f.result() for f in futs]      # exceptions propagate
    for ci, part in zip(owner, parts):
        cpus[ci].extend(part)

    counts = []
    for (n, lo, hi, min_surv), cpu, gpu in zip(G6_CASES, cpus, gpus):
        cpu.sort()
        if len(cpu) < min_surv:
            return False, f"G6 FAIL n={n}: window under-populated ({len(cpu)})"
        if cpu != gpu:
            return False, (f"G6 FAIL n={n} [{lo},{hi}): cpu {len(cpu)}"
                           f" gpu {len(gpu)}")
        counts.append(len(cpu))
    return True, ("G6 ok: GPU == CPU reference on 7 populated windows from"
                  f" 1e5 to the 1e24 ceiling, sizes {counts}"
                  f" ({len(jobs)} reference sub-windows, {workers} workers)")


def _g6_gpu(n, lo, hi):
    eng = GpuEngine(n)
    out = eng.survivors_pre_mr(lo, hi)
    del eng
    cp.get_default_memory_pool().free_all_blocks()
    return out


def g7_comparator_drill():
    """The parity comparator must catch a planted fake survivor."""
    n, lo, hi = 5, 10**5, 4 * 10**5
    cpu = sorted(p for chunk in CpuEngine(n, wheel_primes=WHEEL_PRIMES_29)
                 .survivors_pre_mr(lo, hi) for p in chunk)
    assert len(cpu) >= 3, "drill window unexpectedly empty"
    fake = list(cpu)
    fake[len(fake) // 2] += 2
    if fake == cpu:
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


def g12_canaries():
    """End-to-end rediscovery of a(18) and the run-21 literature value.

    One engine spans the range, so these land on opposite sides of the old
    u64 boundary in the same gate -- which is the point: that boundary is no
    longer a thing the search knows about.
    """
    a18 = 8_461_068_614_861_832_371
    eng = GpuEngine(17)
    hits = eng.hunt(a18 - 5 * 10**9, a18 + 5 * 10**9)
    firsts = [p for p, r in hits if r == 18]
    if not firsts or firsts[0] != a18:
        return False, f"G12 FAIL: a(18) not rediscovered ({hits})"
    hits = eng.hunt(A21_UPPER - 10**7, A21_UPPER + 10**7)
    if (A21_UPPER, 21) not in hits:
        return False, f"G12 FAIL: run-21 value not rediscovered ({hits})"
    return True, ("G12 ok: rediscovered a(18) = %d (below 2^64) and the"
                  " Waldvogel-Leikauf run-21 value (above it)" % a18)


def g13_slicing_independence():
    """The stream must not depend on how the work was sliced.

    The bit-sieve evaluates candidates in W-period pattern words, and the
    launcher cuts work into per-thread (T) and per-launch chunks, so the
    live risk is boundary masking: the edge words of a window, windows
    shorter than one word, starts landing mid-word, launch sizes that are
    not multiples of T.  Every one of those bugs makes the answer depend on
    the SLICING -- so the test is that it does not.  The same window is
    swept at five launch geometries and split at word/thread/launch
    boundaries, and all of it must be one identical stream.

    This is complementary to G6, not a substitute: G6 pins the stream to an
    independent implementation (is it the RIGHT answer?), G13 pins it across
    slicings (is it the SAME answer however we cut it?).  A boundary bug
    that dropped the same survivor at every geometry would slip past G13 and
    be caught by G6; a bug that only fires at one launch size would slip
    past G6's single geometry and be caught here.

    There are now TWO slicing axes.  A launch is also cut along the OFFSET
    axis into CHUNK-sized groups, each running its own sieve -> rounds ->
    cold chain over the launch's whole period range, with its own stage-1a
    counter.  A chunking bug loses or duplicates survivors exactly the way a
    period-boundary bug does -- and it is the newer mechanism -- so the same
    test applies to it: same window, several chunk sizes, one stream.
    """
    M = 6469693230
    heights = [3 * 10**19, 230 * 10**18, A21_UPPER, 10**24 - 10**15]
    checks = surv = 0
    for n, span in ((13, 137), (17, 5000)):
        eng = GpuEngine(n)
        W, T = eng.W, eng.T
        for h in heights:
            cases = [(h, h + span * M),                     # aligned
                     (h + 1, h + span * M - 1),             # unaligned ends
                     (h + M // 3, h + span * M + M // 7),   # mid-period bounds
                     (h, h + M // 2),                       # sub-period window
                     (h + M - 10, h + M + 10),              # straddles a period
                     (h + 17, h + W * M + 17),              # exactly one word
                     (h + 1, h + (W + 1) * M),              # word + 1
                     (h + T * M - 3 * M, h + T * M + 3 * M)]    # T boundary
            for lo, hi in cases:
                ref = None
                for ppl in (None, T, T + 1, 1000, 137):
                    got = eng.survivors_pre_mr(lo, hi, periods_per_launch=ppl)
                    if ref is None:
                        ref, surv = got, surv + len(got)
                    elif got != ref:
                        return False, ("G13 FAIL n=%d [%d,%d) ppl=%s: %d vs %d"
                                       % (n, lo, hi, ppl, len(got), len(ref)))
                    checks += 1
            # resume drill: split on word / thread / launch boundaries
            lo, hi = h + 7, h + (2 * T + 11) * M + 13
            whole = eng.survivors_pre_mr(lo, hi, periods_per_launch=512)
            for cut in (lo + 1, lo + (W - 1) * M, lo + W * M, lo + W * M + 5,
                        lo + T * M, lo + T * M + 7, hi - 1):
                split = sorted(
                    eng.survivors_pre_mr(lo, cut, periods_per_launch=512)
                    + eng.survivors_pre_mr(cut, hi, periods_per_launch=512))
                checks += 1
                surv += len(whole)
                if split != whole:
                    return False, ("G13 FAIL n=%d split at +%d: %d vs %d"
                                   % (n, cut - lo, len(split), len(whole)))
        del eng
        cp.get_default_memory_pool().free_all_blocks()
    # the offset axis
    csurv, saved = 0, GpuEngine.CHUNK
    try:
        for n, lo, hi in ((13, 3 * 10**19, 3 * 10**19 + 6 * 10**13),
                          (17, 230 * 10**18, 230 * 10**18 + 8 * 10**14)):
            ref = None
            for chunk in (None, 1_000_000, 65_536, 4093):
                GpuEngine.CHUNK = chunk
                eng = GpuEngine(n)
                got = eng.survivors_pre_mr(lo, hi)
                nch = eng.nchunks
                del eng
                cp.get_default_memory_pool().free_all_blocks()
                if ref is None:
                    ref, csurv = got, csurv + len(got)
                elif got != ref:
                    return False, ("G13 FAIL n=%d chunk=%s (%d chains): %d vs"
                                   " %d" % (n, chunk, nch, len(got), len(ref)))
                checks += 1
    finally:
        GpuEngine.CHUNK = saved
    if surv < 1000 or csurv < 100:
        return False, ("G13 FAIL: only %d/%d survivors compared -- windows are"
                       " too sparse to prove anything" % (surv, csurv))
    return True, ("G13 ok: stream independent of slicing over %d comparisons"
                  " (%d + %d survivors) across launch geometries, word/thread"
                  " boundaries, split points and offset-chunk sizes, to the"
                  " 1e24 ceiling" % (checks, surv, csurv))


def g14_pattern_tables(trials=40, seed=11):
    """The bit-sieve pattern tables satisfy their ORIGINAL definition.

    G6 pins the stream against an independent implementation, so a table bug
    would have to be reproduced by numpy `%` arithmetic to survive.  This
    gate closes the gap differently: it checks the tables directly against
    the mathematics they encode, with no engine in the loop.  For a real
    candidate p = k*29# + off and a real period offset u, bit u of
    pat[q][p mod q] must equal "q divides one of x^2+x+(p + u*29#) for some
    x < n" -- big-integer divisibility of the actual values, not a restated
    residue identity.

    The index is whatever `sieve_layout` says it is, which is the point: the
    marched layout permutes the rows and pads them, so a gate that hard-coded
    `pat[po + p % q]` would silently stop testing the table that is actually
    loaded.  Both layouts are checked, at every step s a thread can reach, so
    the padded rows are covered too.
    """
    import random
    for n in (13, 17):
        wp = best_wheel(n)
        offs, M = build_wheel(n, wp)
        s1, _ = stage_primes(after=wp[-1])
        T, qs, checks = GpuEngine.T, [int(q) for q in s1[:SIEVE_NINC]], 0
        for march in (False, True):
            _, _, pat, lay = sieve_tables(n, int(M), s1, SIEVE_NINC, SIEVE_W,
                                          T=T, march=march)
            rng = random.Random(seed + n)
            for e in lay:
                q, po = e["q"], e["po"]
                for _ in range(trials):
                    k = rng.randrange(5 * 10**10, 6 * 10**10)  # above 2^64
                    off = int(offs[rng.randrange(offs.size)])
                    p = k * int(M) + off
                    u = rng.randrange(SIEVE_W)
                    # s: the pattern-word index within a thread's run.  The
                    # kernel loads row (idx + s) when it is at p + s*W*M.
                    s = rng.randrange(T // SIEVE_W) if march else 0
                    idx = ((p % q) * e["dmwinv"]) % q if march else p % q
                    bit = (int(pat[po + idx + s]) >> u) & 1
                    pu = p + (u + s * SIEVE_W) * int(M)
                    direct = any((pu + x * x + x) % q == 0 for x in range(n))
                    if bit != int(direct):
                        return False, ("G14 FAIL n=%d march=%d q=%d r=%d u=%d"
                                       " s=%d: pattern %d vs divisibility %d"
                                       % (n, march, q, p % q, u, s, bit,
                                          int(direct)))
                    checks += 1
    return True, ("G14 ok: pattern bits == big-integer divisibility of the"
                  " actual values, both layouts, %d checks per n over primes"
                  " %d..%d" % (checks, qs[0], qs[-1]))


def g15_reduction_identities(trials=3000, seed=17):
    """The two arithmetic shortcuts, checked against exact integer arithmetic.

    G6 pins the whole stream, so either of these failing would have to be
    reproduced by the numpy-`%` reference to survive.  This gate closes the
    gap the way G14 does for the tables -- directly, with no engine in the
    loop -- because both shortcuts are conditional identities whose
    PRECONDITIONS are what a future parameter change would break, and a
    stream comparison would only reveal that after the fact.

    (a) The stage-2 kill test (_S2_BITSET).  q divides one of p + x^2 + x for
        some x < n exactly when p mod q == 0 or q - (p mod q) is itself of the
        form x^2 + x -- valid only while q > max(x^2+x), which is asserted.
    (b) The 32-bit reductions, now used in three places -- _SIEVE_INIT32
        (residue seeding), _R_MIX32 (stage 1b) and _S2_RED_MIX32 (stage 2).
        For m32 = floor(2^32/q) and any x < 2^32, two conditional subtracts
        recover x mod q exactly; and the recombination kq*dM + oq that all
        three keep in 32 bits really does stay under 2^32 for every stage-1
        and stage-2 prime -- the stage-2 bound is the tight one, at
        q^2 + q = 4.293e9 for q = 65521.
    """
    import random
    rng = random.Random(seed)
    for n in (13, 17, 21):
        xxmax = (n - 1) * (n - 1) + (n - 1)
        xxset = {x * x + x for x in range(n)}
        s1, s2 = stage_primes()
        if int(s2[0]) <= xxmax:
            return False, ("G15 FAIL n=%d: stage-2 floor %d <= max(x^2+x) %d,"
                           " so the bitset test's precondition is void"
                           % (n, int(s2[0]), xxmax))
        for _ in range(trials):
            q = int(s2[rng.randrange(s2.size)])
            p = rng.randrange(10**20, 10**24)
            rr = p % q
            direct = any((p + x * x + x) % q == 0 for x in range(n))
            shortcut = (rr == 0) or ((q - rr) <= xxmax and (q - rr) in xxset)
            if direct != shortcut:
                return False, ("G15 FAIL n=%d q=%d p=%d: divisibility %d vs"
                               " bitset %d" % (n, q, p, direct, shortcut))
    # (b) 32-bit Barrett, over both prime ranges and the extremes of the input
    s1, s2 = stage_primes()
    for arr in (s1, s2):
        for q in [int(v) for v in arr.tolist()]:
            m32 = (1 << 32) // q
            dM = rng.randrange(q)
            if (q - 1) * dM + (q - 1) >= (1 << 32):
                return False, ("G15 FAIL q=%d: kq*dM + oq can reach %d, which"
                               " overflows the u32 _R_MIX32 keeps it in"
                               % (q, (q - 1) * dM + (q - 1)))
            for x in [0, 1, q - 1, q, q + 1, (1 << 32) - 1,
                      rng.randrange(1 << 32), rng.randrange(1 << 32)]:
                r = x - ((x * m32) >> 32) * q
                if r >= q:
                    r -= q
                if r >= q:
                    r -= q
                if r != x % q:
                    return False, ("G15 FAIL 32-bit Barrett q=%d x=%d: %d vs"
                                   " %d" % (q, x, r, x % q))
    # (c) the off-split reduction.  off mod q == (a*(2^s mod q) + b) mod q
    # with off = a*2^s + b is an identity for ANY s; what the 32-bit Barrett
    # needs is that a*(2^s mod q) + b never reaches 2^32.  Check the bound at
    # its worst case (off = M - 1) and the value on real offsets, for each
    # wheel the engine can pick and for BOTH stage split points -- the two
    # differ because stage 2's primes are 64x wider.
    for wp in (WHEEL_PRIMES_29, WHEEL_PRIMES_31):
        for n in (13, 17):
            offs, M = build_wheel(n, wp)
            s1, s2 = stage_primes(after=wp[-1])
            for arr in (s1, s2):
                qs = [int(v) for v in arr.tolist()]
                s = off_split(M, qs[-1])
                if s is None:
                    continue
                for q in qs:
                    c = (1 << s) % q
                    worst = ((int(M) - 1) >> s) * c + ((1 << s) - 1)
                    if worst >= (1 << 32):
                        return False, ("G15 FAIL split s=%d q=%d wheel=%d: the"
                                       " 32-bit form can reach %d"
                                       % (s, q, wp[-1], worst))
                for _ in range(200):
                    off = int(offs[rng.randrange(offs.size)])
                    q = qs[rng.randrange(len(qs))]
                    v = (off >> s) * ((1 << s) % q) + (off & ((1 << s) - 1))
                    if v % q != off % q or v >= (1 << 32):
                        return False, ("G15 FAIL split off=%d q=%d s=%d: %d vs"
                                       " %d" % (off, q, s, v % q, off % q))
    # (d) the stage-1b bitset.  Same identity as (a), now also used for the
    # stage-1 primes above max(x^2+x); those are the ones whose precondition
    # a wider n would break first, so check them at the n the engine runs.
    for n in (13, 17):
        xxmax = (n - 1) * (n - 1) + (n - 1)
        xxset = {x * x + x for x in range(n)}
        s1, _ = stage_primes(after=31)
        for q in [int(v) for v in s1.tolist() if int(v) > xxmax]:
            for _ in range(20):
                p = rng.randrange(10**20, 10**24)
                rr = p % q
                direct = any((p + x) % q == 0 for x in xxset)
                if direct != ((rr == 0) or ((q - rr) <= xxmax
                                            and (q - rr) in xxset)):
                    return False, ("G15 FAIL stage-1b bitset n=%d q=%d p=%d"
                                   % (n, q, p))
    return True, ("G15 ok: the bitset test == big-integer divisibility over"
                  " n=13/17/21 for stage 2 and for every stage-1 prime above"
                  " max(x^2+x); the 32-bit reductions are exact over all"
                  " %d stage-1 + %d stage-2 primes; and the off-split stays"
                  " under 2^32 at its worst case on both wheels"
                  % (s1.size, s2.size))


def selftest():
    ok = True
    for g in (g6_parity, g7_comparator_drill, g8_gpu_canary, g12_canaries,
              g13_slicing_independence, g14_pattern_tables,
              g15_reduction_identities):
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
