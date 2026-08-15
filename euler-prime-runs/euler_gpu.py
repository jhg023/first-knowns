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
# Pipeline, three kernels:
#   stage 1a  bit-sieve over the first NINC stage-1 primes: one precomputed
#             W-period kill pattern OR-ed per prime per W periods, survivors
#             extracted from the complement with __ffsll, pushed to a queue
#   stage 1b  compaction ROUNDS over the remaining stage-1 primes: each round
#             tests a few primes and forwards survivors to a second queue, so
#             every round restarts with all 32 lanes alive instead of letting
#             a warp run until its last lane dies
#   stage 2   primes Q1..Q2 via the exact n-value divisibility test, one
#             thread per surviving candidate
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
# geometries and split points, G14 pattern tables == big-integer
# divisibility.  See ../OPTIMIZATION.md for why the engine is shaped this
# way, and RESULTS.md for what the retired engines were.
#
# ASCII only.

import numpy as np

import cupy as cp

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.gpu import barrett_magics  # noqa: E402

from euler_reference import A21_UPPER, KNOWN
from euler_search import (CpuEngine, P_CEIL, P_FLOOR, WHEEL_PRIMES,
                          WHEEL_PRIMES_29, build_wheel, forbidden,
                          mr_is_prime, mr_run_length, stage_primes)

MP_T = 2048              # wheel periods per thread (rate plateaus 1024..4096)

_COLD_SRC = r"""
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

SIEVE_W = 64             # periods per pattern word (u64); must divide T
SIEVE_NINC = 24          # sieve-phase primes (31..139).  An extra prime
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
    W = SIEVE_W              # pattern width in periods (multiple of 64)
    T = MP_T                 # periods per thread
    PPL = 131072             # periods per launch.  Big launches matter now
                             # that stage 1a is cheap: steady-state A/B over
                             # [2.3e20, +2e15) gave 8192 -> 131072 = 1.395x
                             # with identical streams.  Matches the
                             # launcher's SEG_PERIODS: one launch per segment.
    ROUND = 8                # stage-1b primes per compaction round; 0 sends
                             # all of stage 1b to the single cold kernel
    ROUND_GRID = 4096        # fixed grid for the grid-striding round kernel
    Q_HEADROOM = 1.25        # queue slack over the exact expected occupancy

    def __init__(self, n, wheel_primes=None):
        self.n = n
        self.wheel_primes = wheel_primes or WHEEL_PRIMES_29
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
        self.d_s2q = cp.asarray(s2.astype(np.uint32))
        self.d_s2magic = cp.asarray(barrett_magics(s2))
        self.d_s2dM = cp.asarray(np.array([int(self.M) % int(q)
                                           for q in s2.tolist()],
                                          dtype=np.uint32))
        self.d_xx = cp.asarray(np.array([x * x + x for x in range(n)],
                                        dtype=np.uint32))

        # snapshot the tuning before anything is compiled against it
        self.NINC, self.W, self.T = int(self.NINC), int(self.W), int(self.T)
        self.PPL, self.ROUND = int(self.PPL), int(self.ROUND)

        src, pat = sieve_kernel_src(n, int(self.M), s1, self.NINC,
                                    W=self.W, T=self.T)
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
        self.kern_cold = cp.RawKernel(
            _COLD_SRC.replace("__MP_NINC__", str(self.cold_j0)),
            "ladder_cold_128")
        self.kern_round = cp.RawKernel(_ROUND_SRC, "ladder_round_128")

        # Stage-1a survival is a deterministic product over the sieve primes,
        # so the queue is sized exactly rather than guessed; grown on demand
        # below, which keeps the gate battery's tiny windows from each
        # reserving a production-sized buffer.
        rate = 1.0
        for q in [int(v) for v in s1.tolist()[:self.NINC]]:
            rate *= 1.0 - len(forbidden(q, n)) / q
        self.s1a_rate = rate

        self.out_cap = 1 << 22
        self.d_outk = cp.zeros(self.out_cap, dtype=np.uint64)
        self.d_outo = cp.zeros(self.out_cap, dtype=np.uint64)
        self.d_outn = cp.zeros(1, dtype=np.uint64)
        self.d_qn = cp.zeros(1, dtype=np.uint64)
        self.d_qn2 = cp.zeros(1, dtype=np.uint64)
        self.d_queue, self.d_queue2, self.Q_CAP = None, None, 0

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
            self.kern_cold((int(gxc),), (block,),
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
            if all(mr_is_prime(p + x * x + x) for x in range(self.n)):
                out.append((p, mr_run_length(p, cap=cap)))
        return out


# ------------------------------- gates -------------------------------------

def g6_parity():
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
    """
    cases = [(5, 10**5, 4 * 10**5, 20),
             (9, 10**6, 6 * 10**7, 2),
             (13, 10**5, 8_900_000_000, 1),
             (17, 10**15, 10**15 + 3 * 10**12, 1),
             (17, 17 * 10**18, 17 * 10**18 + 2 * 10**12, 1),
             (17, A21_UPPER - 10**10, A21_UPPER + 10**10, 1),
             (17, P_CEIL - 10**13, P_CEIL, 1)]
    counts = []
    for n, lo, hi, min_surv in cases:
        cpu = sorted(p for chunk in CpuEngine(n, wheel_primes=WHEEL_PRIMES_29)
                     .survivors_pre_mr(lo, hi) for p in chunk)
        gpu = GpuEngine(n).survivors_pre_mr(lo, hi)
        if len(cpu) < min_surv:
            return False, f"G6 FAIL n={n}: window under-populated ({len(cpu)})"
        if cpu != gpu:
            return False, (f"G6 FAIL n={n} [{lo},{hi}): cpu {len(cpu)}"
                           f" gpu {len(gpu)}")
        counts.append(len(cpu))
    return True, ("G6 ok: GPU == CPU reference on 7 populated windows from"
                  f" 1e5 to the 1e24 ceiling, sizes {counts}")


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
    """
    M = 6469693230
    heights = [3 * 10**19, 230 * 10**18, A21_UPPER, 10**24 - 10**15]
    checks = surv = 0
    for n, span in ((13, 137), (17, 77285)):
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
    if surv < 1000:
        return False, ("G13 FAIL: only %d survivors compared -- windows are"
                       " too sparse to prove anything" % surv)
    return True, ("G13 ok: stream independent of slicing over %d comparisons"
                  " (%d survivors) across launch geometries, word/thread"
                  " boundaries and split points, to the 1e24 ceiling"
                  % (checks, surv))


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
    """
    import random
    for n in (13, 17):
        offs, M = build_wheel(n, WHEEL_PRIMES_29)
        s1, _ = stage_primes(after=WHEEL_PRIMES_29[-1])
        _, _, pat = sieve_tables(n, int(M), s1, SIEVE_NINC, SIEVE_W)
        qs = [int(q) for q in s1[:SIEVE_NINC]]
        rng = random.Random(seed + n)
        po = checks = 0
        for q in qs:
            for _ in range(trials):
                k = rng.randrange(5 * 10**10, 6 * 10**10)   # above 2^64
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
    for g in (g6_parity, g7_comparator_drill, g8_gpu_canary, g12_canaries,
              g13_slicing_independence, g14_pattern_tables):
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
