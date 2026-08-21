"""The v2 GPU engine -- the same mathematics, fused into two kernels.

WHAT CHANGED, AND WHY.  v1 was built for correctness and measured three
orders of magnitude short of a runnable campaign (OPTIMIZATION_LOG.md).
A CUDA-event phase split of the fused design says where the time really
goes, and it is not where v1's architecture assumed: **the powering is
~73% of the sweep and the divisibility test is ~10%**.  v1 spent its time
elsewhere entirely -- materialising a (48 x 65536) uint64 limb array per
power per chunk, running `cumsum` over it, and reading its last column
back to the host, one blocking device->host copy per power per chunk.

v2 never materialises anything.  One kernel carries a prime's whole
journey -- p^m for every family, the running prefix, and the test -- in
registers, and the only device->host traffic in a segment is the hit
buffer.

THE FOUR THINGS THAT BOUGHT THE SPEED, in the order they paid:

1.  LIMB WIDTHS SIZED TO THE HEIGHT, AT CODEGEN TIME.  v1 walked 48 limbs
    for every family at every height, because LIMBS was a constant.  Here
    the source is generated per run: family (m, e) gets exactly
    ceil((m*log2 p_hi + log2 k_hi)/32) words, the power chain gets exactly
    ceil(j*log2 p_hi / 32) words for p^j, and every loop is a compile-time
    bound the compiler unrolls into registers.  At the score window that
    is 83 words instead of 8 x 48 = 384, and p^19 costs 16 words of
    multiply rather than 48.

2.  THE POWER CHAIN IS CHOSEN BY COST, NOT BY SHAPE.  Eight families share
    one addition chain, and the split that minimises truncated word
    multiplies is often not the binary one -- p^17 = p^9 * p^8 beats
    p^16 * p because p^16 is dead weight nothing else wants.  A small DP
    over (a + b = m) picks it, priced with the same truncated-schoolbook
    cost the kernel actually pays.

3.  THE TEST IS A MONTGOMERY HORNER THAT NEEDS NEITHER A DIVISION NOR R^2.
    v1 did, per candidate, 48 sixty-four-bit `%` operations plus a
    128-iteration doubling loop to build 2^128 mod k.  v2 runs the sum
    bottom-up,  A_j = w_j + A_{j-1} * 2^-64 (mod k), which is one REDC per
    limb and no back-conversion at all: k is odd (ODD_ONLY), so
    X * 2^-64L == 0 exactly when X == 0.  Two multiplies per limb, no
    division anywhere, and the per-candidate setup is one Newton inverse.
    The accumulator is deliberately left UNREDUCED between limbs -- `hi`
    carries weight 1 in that recurrence, so folding it by k when it would
    overflow is free and legal, which is what removes the last division.

4.  THE PREFIX IS A DECOUPLED LOOK-BACK, NOT A HOST ROUND TRIP.  Each warp
    owns a tile of 32*RUN consecutive primes, scans it internally with
    carry-propagating shuffles, publishes its aggregate, and sums its
    predecessors' aggregates 32-at-a-time until it meets a published
    inclusive prefix.  The whole prime line of a segment is one kernel
    launch and the running state never leaves the device.

WHAT DID NOT CHANGE: the mathematics, the coverage, and the stream.  v2 is
gated bit-for-bit against v1 and against the CPU engine (G14), so "the
fast engine returns the identical stream" stays a checkable claim.  v1
remains in the tree as that parity reference and is never reachable from
a campaign (CLAUDE.md rule 3).

CEILING.  v1's LIMBS = 48 is gone as a constant; the width is computed
per run and the engine still REFUSES a run it cannot represent -- now
because the plan itself is built from p_hi, so a run that does not fit
raises before a kernel is compiled.  P_CEIL = 2^62 still binds.
"""

import math

import numpy as np

import psum_reference as ref
import psum_search as cpu
from psum_gpu import CeilingExceeded, limbs_needed          # noqa: F401

# Measured on the campaign's own shape, not on the score window (rule 5c).
# The segment is the biggest single lever at height: at p = 1e16 going from
# 2^26 to 2^28 is 2.4x, because the per-segment costs (the base-prime pass,
# the buffers, the look-back chains) amortise over four times the line.
# 2^30 gives it back again -- the bitmap stops fitting the cache.
SEG_DEFAULT = 1 << 28          # prime-line span per sieve segment
RUN_DEFAULT = 128              # primes per thread inside a tile
TPB_DEFAULT = 128              # threads per block for the sweep
SUBW_DEFAULT = 2048            # u32 words of sieve bitmap per block
TPBMARK_DEFAULT = 256          # threads per block for the sieve
HIT_BUF = 1 << 14
ODD_ONLY = True                # unchanged from v1: Montgomery needs k odd

_MODCACHE = {}


# ------------------------------------------------------------------ planning
def _words(bits):
    return int(math.ceil(bits / 32.0))


def build_plan(families, p_hi, k_hi, run=RUN_DEFAULT):
    """Exact limb widths for one run, and nothing wider.

    Every number in the kernel is bounded by the run, so every loop bound
    is a compile-time constant: p^j < p_hi^j, and S(m,k) <= k_hi * p_hi^m.
    """
    lp = math.log2(max(float(p_hi), 3.0))
    lk = math.log2(max(float(k_hi), 2.0))
    fams = tuple(sorted(set(families)))

    def lpow(j):
        return max(_words(j * lp), 1)

    W, off, tot = {}, {}, 0
    for f in fams:
        m, e = f
        # one spare word for e = 1 so the +e carry out of the top limb has
        # somewhere to go; e = 0 never carries.
        W[f] = max(_words(m * lp + lk) + (1 if e else 0), lpow(m), 2)
    for f in fams:
        off[f] = tot
        tot += W[f]
    return dict(fams=fams, ms=sorted({m for m, _ in fams}), W=W, off=off,
                wtot=tot, lpow=lpow, pw=lpow(1), run=int(run),
                p_hi=int(p_hi), k_hi=int(k_hi))


def _mulcost(la, lb, lo):
    """Word multiplies a truncated schoolbook la x lb -> lo actually does."""
    return sum(1 for i in range(min(la, lo)) for j in range(lb)
               if i + j < lo)


def _chain_cost(exps, lpow):
    """Cost of the cheapest chain whose exponent set is exactly `exps`.

    Every element bar 1 must be a sum of two smaller members, so ordering by
    size is a valid schedule and the cost is separable per element.
    """
    have = sorted(exps)
    hs = set(have)
    total, how = 0, {}
    for m in have:
        if m == 1:
            continue
        best = None
        for a in range(1, m // 2 + 1):
            if a in hs and (m - a) in hs:
                c = _mulcost(lpow(a), lpow(m - a), lpow(m))
                if best is None or c < best[0]:
                    best = (c, (a, m - a))
        if best is None:
            return None, None
        total += best[0]
        how[m] = best[1]
    return total, how


def power_chain(ms, lpow):
    """Cheapest straight-line chain for every p^m, as [(out, a, b)].

    Chosen by SHARED cost over the whole family set, which is not what a
    per-exponent DP gives: a DP that prices p^m as cost(a) + cost(b) + mul
    double-counts everything a and b already share, and here that made it
    miss p^19 = p^17 * p^2 (28 word multiplies) in favour of building a
    p^18 nothing else wanted (65).  The intermediates live in a small set,
    so the exponent set itself is enumerated exactly.
    """
    targets = sorted(set(ms) | {1})
    top = max(targets)
    free = [x for x in range(2, top + 1) if x not in targets]
    best = (None, None, None)
    if len(free) <= 20:
        for mask in range(1 << len(free)):
            exps = set(targets)
            for i, x in enumerate(free):
                if mask >> i & 1:
                    exps.add(x)
            c, how = _chain_cost(exps, lpow)
            if c is not None and (best[0] is None or c < best[0]):
                best = (c, how, exps)
    if best[0] is None:                       # fall back: full range is legal
        exps = set(range(1, top + 1))
        c, how = _chain_cost(exps, lpow)
        best = (c, how, exps)
    how = best[1]
    return [(m, how[m][0], how[m][1]) for m in sorted(best[2]) if m != 1]


# ------------------------------------------------------------------- kernels
_HEAD = r"""
typedef unsigned int u32;
typedef unsigned long long u64;

#define RUN  @RUN@
#define WTOT @WTOT@
#define TILE (32 * RUN)

/* Truncated schoolbook: only the low LO words, which is all p^(a+b) has.
   The first row STORES instead of accumulating, so there is no zero-fill
   pass and no read-back on row 0 -- with LO up to 16 words and ten
   multiplies per prime that bookkeeping was a quarter of the powering. */
template<int LA, int LB, int LO>
__device__ __forceinline__ void bmul(const u32* a, const u32* b, u32* o)
{
    {
        u32 c = 0u;
#pragma unroll
        for (int j = 0; j < LB && j < LO; ++j) {
            u64 t = (u64)a[0] * b[j] + c;
            o[j] = (u32)t;
            c = (u32)(t >> 32);
        }
        if (LB < LO) o[LB] = c;
    }
#pragma unroll
    for (int i = 1; i < LA && i < LO; ++i) {
        u32 c = 0u;
#pragma unroll
        for (int j = 0; j < LB && i + j < LO; ++j) {
            u64 t = (u64)a[i] * b[j] + o[i + j] + c;
            o[i + j] = (u32)t;
            c = (u32)(t >> 32);
        }
        if (i + LB < LO) o[i + LB] = c;
    }
    /* LO <= LA + LB always holds for these widths; belt and braces. */
#pragma unroll
    for (int i = LA + LB; i < LO; ++i) o[i] = 0u;
}

template<int W, int L>
__device__ __forceinline__ void badd(u32* acc, const u32* x)
{
    u32 c = 0u;
#pragma unroll
    for (int i = 0; i < W; ++i) {
        u64 t = (u64)acc[i] + ((i < L) ? x[i] : 0u) + c;
        acc[i] = (u32)t;
        c = (u32)(t >> 32);
    }
}

/* -k^-1 mod 2^64 for odd k: 5 correct bits, then four Newton doublings */
__device__ __forceinline__ u64 neg_kinv(u64 k)
{
    u64 x = (3ULL * k) ^ 2ULL;
#pragma unroll
    for (int i = 0; i < 4; ++i) x *= 2ULL - k * x;
    return 0ULL - x;
}

/* A' = hi + A * 2^-64 (mod k), left below 2^64 rather than below k.
   `hi` carries weight 1 in this recurrence, so folding it by k when it
   would overflow costs two instructions and changes no residue -- that is
   what lets the whole reduction run without a single division. */
__device__ __forceinline__ u64 mstep(u64 hi, u64 lo, u64 k, u64 kinv, u64 lim)
{
    u64 mm = lo * kinv;
    u64 mh = __umul64hi(mm, k);
    u64 h  = (hi >= lim) ? (hi - k) : hi;
    return h + mh + ((lo != 0ULL) ? 1ULL : 0ULL);
}
"""

_SIEVE = r"""
/* ---------------------------------------------------------------- sieve ---
   Odd residues only: position i is the value base + 2i.  A block owns
   SUBBITS positions, sieves them in shared memory, and writes one word at
   a time -- the marking is a scatter, and doing it in L1-speed memory is
   what keeps it off the critical path. */
#define SUBW  @SUBW@              /* u32 words of bitmap per block */
#define SUBB  (SUBW * 32)           /* positions per block */

/* THE BALANCE IS THE WHOLE KERNEL.  One thread per prime is the obvious
   shape and it is catastrophic: the thread that draws q = 3 marks a third
   of the sub-segment by itself while its 255 neighbours mark sixteen
   positions each and wait.  Measured, that shape cost 2.9 ms of a 4.0 ms
   score window -- 72% of the run in the cheapest arithmetic in the file.
   So primes are split by how much work they carry: a SMALL prime is walked
   by the whole block in disjoint contiguous chunks (which also all but
   removes the shared-memory atomic conflicts), and only the large primes,
   which mark a handful of positions each, get a thread apiece. */
extern "C" __global__ void sieve_mark(u32* __restrict__ bits, u64 base,
        u64 npos, const u32* __restrict__ sp, int nsp, int nsmall)
{
    __shared__ u32 sm[SUBW];
    const u64 b0 = (u64)blockIdx.x * SUBB;
    const int nt = blockDim.x;
    for (int i = threadIdx.x; i < SUBW; i += nt) sm[i] = 0xffffffffu;
    __syncthreads();
    const u64 lo = base + 2ULL * b0;                /* first value here */
    const u64 hi = lo + 2ULL * SUBB;

    for (int t = 0; t < nsmall; ++t) {              /* block per prime */
        const u64 q = sp[t];
        u64 s = q * q;
        if (s < lo) {
            u64 r = lo % q;
            s = lo + (r ? (q - r) : 0ULL);
            if ((s & 1ULL) == 0ULL) s += q;
        }
        if (s >= hi) continue;
        const u64 i0 = (s - lo) >> 1;
        const u64 chunk = ((SUBB - i0 + q - 1ULL) / q + nt - 1ULL) / nt;
        u64 i = i0 + (u64)threadIdx.x * chunk * q;
        for (u64 c = 0; c < chunk && i < SUBB; ++c, i += q)
            atomicAnd(&sm[i >> 5], ~(1u << (i & 31)));
    }
    for (int t = nsmall + threadIdx.x; t < nsp; t += nt) {   /* thread per */
        const u64 q = sp[t];
        u64 s = q * q;
        if (s < lo) {
            u64 r = lo % q;
            s = lo + (r ? (q - r) : 0ULL);
            if ((s & 1ULL) == 0ULL) s += q;
        }
        if (s >= hi) continue;
        for (u64 i = (s - lo) >> 1; i < SUBB; i += q)
            atomicAnd(&sm[i >> 5], ~(1u << (i & 31)));
    }
    __syncthreads();
    for (int i = threadIdx.x; i < SUBW; i += blockDim.x) {
        u64 w = b0 / 32 + i;
        if (w * 32 < npos) {
            u32 v = sm[i];
            u64 rem = npos - w * 32;
            if (rem < 32) v &= (rem == 0) ? 0u : (0xffffffffu >> (32 - rem));
            bits[w] = v;
        }
    }
}

/* Count, scan and compact in ONE pass.  Three kernels here cost three
   launches and two grid-wide barriers -- 44 us of host time each at this
   size, which is more than the arithmetic.  A warp per run of `per` words
   counts its own popcount, publishes it, sums its predecessors the same
   decoupled way the sweep does, and then writes.  Order is preserved
   because the cursor is the exclusive prefix, and order is the whole
   contract: index k must mean the k-th prime. */
/* Primes larger than a sub-segment hit it at most once, so a per-block
   loop over them is all overhead: at p = 1e15 that was 512 blocks x 1.95e6
   primes of 64-bit division, 20 ms of a 24 ms segment.  Give each one a
   thread and let it walk the WHOLE segment, marking straight into the
   global bitmap.  Consecutive base primes do near-identical amounts of
   work, so a grid-stride loop over a sorted list is balanced for free.
   This runs AFTER the small pass, which stores whole words. */
extern "C" __global__ void sieve_mark_large(u32* __restrict__ bits, u64 base,
        u64 npos, const u32* __restrict__ sp, int lo_i, int nsp)
{
    const u64 hi = base + 2ULL * npos;
    for (int t = lo_i + blockIdx.x * blockDim.x + threadIdx.x; t < nsp;
         t += gridDim.x * blockDim.x) {
        const u64 q = sp[t];
        u64 s = q * q;
        if (s < base) {
            const u64 r = base % q;
            s = base + (r ? (q - r) : 0ULL);
            if ((s & 1ULL) == 0ULL) s += q;
        }
        if (s >= hi) continue;
        for (u64 i = (s - base) >> 1; i < npos; i += q)
            atomicAnd(&bits[i >> 5], ~(1u << (i & 31)));
    }
}

extern "C" __global__ void sieve_compact(const u32* __restrict__ bits,
        u64 nwords, int per, u64 base, u64* __restrict__ out, u64 outcap,
        volatile u64* agg, volatile u64* inc, volatile int* status,
        int* ctr, u64* total, int ncb)
{
    const int lane = threadIdx.x & 31;
    int tile;
    if (lane == 0) tile = atomicAdd(ctr, 1);
    tile = __shfl_sync(0xffffffffu, tile, 0);
    if (tile >= ncb) return;

    const u64 w0 = (u64)tile * per;
    const u64 w1 = min(w0 + (u64)per, nwords);
    u64 c = 0ULL;
    for (u64 i = w0 + lane; i < w1; i += 32) c += (u64)__popc(bits[i]);
#pragma unroll
    for (int o = 16; o > 0; o >>= 1) c += __shfl_down_sync(0xffffffffu, c, o);
    c = __shfl_sync(0xffffffffu, c, 0);
    if (lane == 0) {
        agg[tile] = c;
        __threadfence();
        status[tile] = 1;
    }

    u64 pre = 0ULL;
    int look = tile - 1;
    while (look >= 0) {
        const int j = look - lane;
        int st;
        do {
            st = (j < 0) ? 3 : status[j];
        } while (__any_sync(0xffffffffu, st == 0));
        const unsigned mask = __ballot_sync(0xffffffffu, st >= 2);
        const int first = mask ? (__ffs(mask) - 1) : 32;
        u64 v = 0ULL;
        if (lane < first) v = agg[j];
        else if (lane == first && j >= 0) v = inc[j];
#pragma unroll
        for (int o = 16; o > 0; o >>= 1)
            v += __shfl_down_sync(0xffffffffu, v, o);
        pre += __shfl_sync(0xffffffffu, v, 0);
        if (first < 32) break;
        look -= 32;
    }
    if (lane == 0) {
        inc[tile] = pre + c;
        __threadfence();
        status[tile] = 2;
        if (tile == ncb - 1) total[0] = pre + c;
    }

    u64 pos = pre;
    for (u64 i0 = w0; i0 < w1; i0 += 32) {
        const u64 i = i0 + lane;
        u32 v = (i < w1) ? bits[i] : 0u;
        int prefix = __popc(v);
        const int cnt = prefix;
#pragma unroll
        for (int o = 1; o < 32; o <<= 1) {
            int nb = __shfl_up_sync(0xffffffffu, prefix, o);
            if (lane >= o) prefix += nb;
        }
        const int tot = __shfl_sync(0xffffffffu, prefix, 31);
        u64 mypos = pos + (u64)(prefix - cnt);
        while (v) {
            const int j = __ffs(v) - 1;
            v &= v - 1;
            if (mypos < outcap) out[mypos] = base + 2ULL * (i * 32 + j);
            ++mypos;
        }
        pos += tot;
    }
}
"""

_SWEEP = r"""
extern "C" __global__ void sweep(
        const u64* __restrict__ ps, const u64* __restrict__ np,
        const u64* __restrict__ k0p,
        const u32* __restrict__ seed,
        u64* hits, int* nh, const int cap,
        volatile u32* agg, volatile u32* inc, volatile int* status, int* ctr,
        u32* seedout, u64* k0out)
{
    /* n and k0 arrive in DEVICE memory and the tile count is derived here,
       so a segment costs no host synchronisation at all: the sieve's count
       never has to come back to the CPU just to size this launch. */
    const u64 n = np[0];
    const u64 k0 = k0p[0];
    const int ntile = (int)((n + TILE - 1) / TILE);
    const int lane = threadIdx.x & 31;
    /* One tile per warp.  A persistent grid drawing tiles in a loop was
       tried and is 11% SLOWER here: it saves nothing the tighter prime
       bound does not already save, and the loop costs the compiler its
       straight-line schedule. */
    {
    int tile;
    if (lane == 0) tile = atomicAdd(ctr, 1);
    tile = __shfl_sync(0xffffffffu, tile, 0);
    if (tile >= ntile) return;

    u32 acc[WTOT];
#pragma unroll
    for (int i = 0; i < WTOT; ++i) acc[i] = 0u;

    const u64 base = (u64)tile * TILE + (u64)lane * RUN;
#pragma unroll 1
    for (int r = 0; r < RUN; ++r) {
        u64 idx = base + r;
        if (idx < n) addpow(acc, ps[idx]);
    }

    /* inclusive scan across the warp, carries propagated inside each lane */
#pragma unroll
    for (int o = 1; o < 32; o <<= 1) {
        u32 c = 0u;
        const bool act = (lane >= o);
#pragma unroll
        for (int i = 0; i < WTOT; ++i) {
            u32 nb = __shfl_up_sync(0xffffffffu, acc[i], o);
            u64 t = (u64)acc[i] + (act ? nb : 0u) + c;
            acc[i] = (u32)t;
            c = act ? (u32)(t >> 32) : 0u;
        }
    }
    if (lane == 31) {
#pragma unroll
        for (int i = 0; i < WTOT; ++i) agg[(u64)i * ntile + tile] = acc[i];
        __threadfence();
        status[tile] = 1;
    }
    __syncwarp();
#pragma unroll
    for (int i = 0; i < WTOT; ++i) {           /* exclusive within the warp */
        u32 v = __shfl_up_sync(0xffffffffu, acc[i], 1);
        acc[i] = (lane == 0) ? 0u : v;
    }

    /* Everything before this tile, folded straight into acc.  An inclusive
       prefix already carries the incoming seed; a walk that reaches the
       front of the line on aggregates alone does not, and must add the
       seed itself -- that case is invisible below 33 tiles. */
    int look = tile - 1;
    bool need_seed = true;
    while (look >= 0) {
        const int j = look - lane;
        int st;
        do {
            st = (j < 0) ? 3 : status[j];
        } while (__any_sync(0xffffffffu, st == 0));
        const unsigned mask = __ballot_sync(0xffffffffu, st >= 2);
        const int first = mask ? (__ffs(mask) - 1) : 32;
        const bool useagg = (lane < first);
        const bool useinc = (lane == first) && (j >= 0);
        volatile const u32* srcp = useagg ? agg : inc;
        const int col = (j < 0) ? 0 : j;
        u64 carry = 0ULL;
#pragma unroll
        for (int i = 0; i < WTOT; ++i) {
            u64 s = (useagg || useinc)
                    ? (u64)srcp[(u64)i * ntile + col] : 0ULL;
#pragma unroll
            for (int o = 16; o > 0; o >>= 1)
                s += __shfl_down_sync(0xffffffffu, s, o);
            s = __shfl_sync(0xffffffffu, s, 0);
            u64 t = (u64)acc[i] + s + carry;
            acc[i] = (u32)t;
            carry = t >> 32;
        }
        if (first < 32) {
            if (look - first >= 0) need_seed = false;
            break;
        }
        look -= 32;
    }
    if (need_seed) {
        u32 c = 0u;
#pragma unroll
        for (int i = 0; i < WTOT; ++i) {
            u64 t = (u64)acc[i] + seed[i] + c;
            acc[i] = (u32)t;
            c = (u32)(t >> 32);
        }
    }
    /* lane 0 holds the tile's exclusive prefix; lane 31 publishes the
       inclusive one from the aggregate it wrote itself */
    {
        u32 c = 0u;
#pragma unroll
        for (int i = 0; i < WTOT; ++i) {
            u32 pre = __shfl_sync(0xffffffffu, acc[i], 0);
            if (lane == 31) {
                u64 t = (u64)pre + agg[(u64)i * ntile + tile] + c;
                inc[(u64)i * ntile + tile] = (u32)t;
                c = (u32)(t >> 32);
                if (tile == ntile - 1) seedout[i] = (u32)t;
            }
        }
        if (lane == 31) {
            if (tile == ntile - 1) k0out[0] = k0 + n;
            __threadfence();
            status[tile] = 2;
        }
    }

#pragma unroll 1
    for (int r = 0; r < RUN; ++r) {
        u64 idx = base + r;
        if (idx >= n) break;
        addpow(acc, ps[idx]);
        const u64 k = k0 + idx + 1ULL;
        if ((k & 1ULL) && k >= 3ULL) testk(acc, k, hits, nh, cap);
    }
    }
}
"""


def gen_source(plan, subw=2048):
    fams, W, off = plan["fams"], plan["W"], plan["off"]
    lpow, pw = plan["lpow"], plan["pw"]
    steps = power_chain(plan["ms"], lpow)
    fam_of = {}
    for f in fams:
        fam_of.setdefault(f[0], []).append(f)

    src = [_HEAD.replace("@RUN@", str(plan["run"]))
                .replace("@WTOT@", str(plan["wtot"])),
           _SIEVE.replace("@SUBW@", str(subw))]

    a = ["__device__ __forceinline__ void addpow(u32* acc, u64 p)", "{",
         "    u32 E1[%d];" % pw]
    for i in range(pw):
        a.append("    E1[%d] = %s;" % (i, ("(u32)(p >> %d)" % (32 * i))
                                       if i < 2 else "0u"))
    for f in fam_of.get(1, []):
        a.append("    badd<%d,%d>(acc + %d, E1);" % (W[f], lpow(1), off[f]))
    for (m, x, y) in steps:
        a.append("    u32 E%d[%d]; bmul<%d,%d,%d>(E%d, E%d, E%d);"
                 % (m, lpow(m), lpow(x), lpow(y), lpow(m), x, y, m))
        for f in fam_of.get(m, []):
            a.append("    badd<%d,%d>(acc + %d, E%d);"
                     % (W[f], lpow(m), off[f], m))
    a.append("}")
    src.append("\n".join(a))

    t = ["__device__ __forceinline__ void testk(const u32* acc, u64 k,",
         "        u64* hits, int* nh, int cap)", "{",
         "    const u64 kinv = neg_kinv(k);",
         "    const u64 lim = 0ULL - k;",
         "    u64 A, w, c;"]
    for f in fams:
        m, e = f
        Wf, o = W[f], off[f]

        def limb(i, o=o, Wf=Wf):
            s = "(u64)acc[%d]" % (o + 2 * i)
            if 2 * i + 1 < Wf:
                s += " | ((u64)acc[%d] << 32)" % (o + 2 * i + 1)
            return s

        t.append("    c = %dULL;" % e)
        t.append("    w = (%s) + c;" % limb(0))
        t.append("    A = w; c = (w < c) ? 1ULL : 0ULL;")
        for i in range(1, (Wf + 1) // 2):
            t.append("    w = (%s) + c;" % limb(i))
            t.append("    c = (w < c) ? 1ULL : 0ULL;")
            t.append("    A = mstep(w, A, k, kinv, lim);")
        t.append("    A = mstep(0ULL, A, k, kinv, lim);")
        t.append("    if (A >= k) A -= k;")
        t.append("    if (A == 0ULL) { int s = atomicAdd(nh, 1);"
                 " if (s < cap) hits[s] = (%dULL << 58) | (%dULL << 57) | k; }"
                 % (m, e))
    t.append("}")
    src.append("\n".join(t))
    src.append(_SWEEP)
    return "\n".join(src)


# -------------------------------------------------------------------- engine
class GpuSweep2:
    """Same (hits, state) contract as CpuSweep and GpuSweep, one kernel."""

    def __init__(self, families, seg=SEG_DEFAULT, run=RUN_DEFAULT,
                 tpb=TPB_DEFAULT, subw=SUBW_DEFAULT,
                 tpb_mark=TPBMARK_DEFAULT, chunk=None):
        import cupy as cp
        self.cp = cp
        self.families = tuple(sorted(set(families)))
        self.ms = tuple(sorted({m for m, _ in self.families}))
        self.seg = int(seg)
        self.run_len = int(run)
        self.tpb = int(tpb)
        self.subw = int(subw)
        self.tpb_mark = int(tpb_mark)
        self.state = cpu.State(self.ms)
        self._plan = None
        self._bufs = {}
        self._sp_lim = None
        self._splitkey = None
        self._ceil_seen = None
        self._ceil_need = None
        self._plankey = None

    # ---------------------------------------------------------------- checks
    def check_ceiling(self, p_hi):
        if self._ceil_seen == p_hi:
            return self._ceil_need
        if p_hi > cpu.P_CEIL:
            raise CeilingExceeded(f"p_hi {p_hi} exceeds P_CEIL = 2^62")
        k_hi = _k_bound(p_hi)
        if k_hi > cpu.K_CEIL:
            raise CeilingExceeded(f"k_hi {k_hi} exceeds K_CEIL = 2^57")
        self._ceil_seen = p_hi
        self._ceil_need = max(limbs_needed(m, p_hi) for m in self.ms)
        return self._ceil_need

    # ----------------------------------------------------------- compilation
    def _build(self, p_hi, k_hi):
        cp = self.cp
        if self._plankey == (p_hi, k_hi):
            return self._plan
        plan = build_plan(self.families, p_hi, k_hi, self.run_len)
        self._plankey = (p_hi, k_hi)
        key = (plan["wtot"], plan["run"], plan["pw"], self.subw,
               tuple(sorted(plan["W"].items())))
        if self._plan is not None and self._key == key:
            self._plan = plan
            return plan
        if key not in _MODCACHE:
            src = gen_source(plan, self.subw)
            _MODCACHE[key] = cp.RawModule(code=src, options=("-std=c++14",),
                                          backend="nvrtc")
        mod = _MODCACHE[key]
        self._mod = mod
        self.k_sweep = mod.get_function("sweep")
        self.k_mark = mod.get_function("sieve_mark")
        self.k_compact = mod.get_function("sieve_compact")
        self.k_mark_large = mod.get_function("sieve_mark_large")
        self._plan, self._key = plan, key
        return plan

    def _splits(self, subb):
        """Where the base primes divide into the sieve's three regimes.

        Cached, because np.searchsorted against a uint32 array with a PYTHON
        int upcasts the whole array to int64 first: at p = 1e16 that is
        5.8e6 elements copied twice per segment, and it measured 17.6 ms of
        a 20 ms segment -- more than every kernel in the engine put
        together, in a line that looks like a lookup.
        """
        key = (subb, self._sp_lim, self.tpb_mark)
        if self._splitkey != key:
            sp = self._sp_host
            small = np.searchsorted(sp, np.uint32(
                max(subb // (4 * self.tpb_mark), 3)), "right")
            # a prime bigger than a sub-segment cannot hit one twice
            mid = np.searchsorted(sp, np.uint64(2 * subb), "right")
            self._split = (int(small), int(min(mid, sp.size)))
            self._splitkey = key
        return self._split

    # --------------------------------------------------------- device buffers
    def _buf(self, name, size, dtype):
        """Grow-only cached device buffers.

        Allocating and zeroing the eleven per-segment arrays cost ~0.5 ms of
        a 1.8 ms score window -- more than the sieve.  They are the same
        shapes every segment, so they are allocated once and reused; only
        the ones whose ZERO means something (the look-back status words and
        the tile counter) are cleared per launch.
        """
        cur = self._bufs.get(name)
        if cur is None or cur.size < size or cur.dtype != dtype:
            cur = self.cp.empty(int(max(size, 1)), dtype=dtype)
            self._bufs[name] = cur
        return cur[:size] if cur.size != size else cur

    # ----------------------------------------------------------------- sweep
    def run(self, p_hi, state=None, seg=None):
        cp = self.cp
        p_hi = int(p_hi)
        self.check_ceiling(p_hi)
        st = (state or self.state).copy()
        seg = int(seg or self.seg)
        plan = self._build(p_hi, _k_bound(p_hi))
        wtot = plan["wtot"]
        hits = []

        lo = st.p
        if lo <= 2 < p_hi:                 # p = 2 is not on the odd line
            st.k += 1
            for m in self.ms:
                st.sums[m] += 2 ** m
            for m, e in self.families:
                if st.k == 1 and (e + st.sums[m]) % st.k == 0:
                    hits.append((m, e, 1))
            lo = 3
        if lo >= p_hi:
            st.p = max(st.p, p_hi)
            self.state = st
            return sorted(hits), st

        lim = int(p_hi ** 0.5) + 2
        if self._sp_lim != lim:
            base_primes = cpu.simple_sieve(lim)
            self._sp_host = base_primes[base_primes > 2].astype(np.uint32)
            self._sp_dev = cp.asarray(self._sp_host)
            self._sp_lim = lim
        d_sp, nsp = self._sp_dev, int(self._sp_dev.size)

        d_seed = self._buf("seedA", wtot, np.uint32)
        d_seed2 = self._buf("seedB", wtot, np.uint32)
        d_seed.set(_state_words(plan, st.sums))
        d_k0 = self._buf("k0A", 1, np.uint64)
        d_k0b = self._buf("k0B", 1, np.uint64)
        d_k0.set(np.array([st.k], dtype=np.uint64))
        d_hits = self._buf("hits", HIT_BUF, np.uint64)
        d_nh = self._buf("nh", 1, np.int32)
        d_nh.fill(0)

        while lo < p_hi:
            hi = min(lo + seg, p_hi)
            self._segment(lo, hi, d_sp, nsp, d_seed, d_seed2, d_k0, d_k0b,
                          d_hits, d_nh, plan)
            d_seed, d_seed2 = d_seed2, d_seed
            d_k0, d_k0b = d_k0b, d_k0
            lo = hi

        if int(cp.asnumpy(self._buf("tot", 1, np.uint64))[0]) > self._nmax_seen:
            raise RuntimeError(
                "prime-count bound was too small for a segment; the "
                "compacted array would have overflowed")
        cnt = int(d_nh.get()[0])          # the run's one and only sync
        if cnt > HIT_BUF:
            raise RuntimeError(f"hit buffer overflow: {cnt} > {HIT_BUF}")
        v = cp.asnumpy(d_hits[:cnt]).astype(np.uint64)
        ms_ = (v >> np.uint64(58)).tolist()
        es_ = ((v >> np.uint64(57)) & np.uint64(1)).tolist()
        ks_ = (v & np.uint64((1 << 57) - 1)).tolist()
        hits.extend(zip(ms_, es_, ks_))
        st.k = int(cp.asnumpy(d_k0)[0])
        st.sums = _read_words(plan, cp.asnumpy(d_seed))
        st.p = max(st.p, p_hi)
        self.state = st
        return sorted(hits), st

    def _segment(self, lo, hi, d_sp, nsp, d_seed, d_seed2, d_k0, d_k0b,
                 d_hits, d_nh, plan):
        cp = self.cp
        base = max(lo if lo % 2 else lo + 1, 3)
        npos = max((hi - base + 1) // 2, 0)
        if npos == 0:
            cp.copyto(d_seed2, d_seed)
            cp.copyto(d_k0b, d_k0)
            return
        subw = self.subw
        subb = subw * 32
        nwords = int((npos + 31) // 32)
        nblk = int((npos + subb - 1) // subb)
        d_bits = self._buf("bits", nblk * subw, np.uint32)
        # A prime goes to the cooperative path only when it has enough
        # multiples here to keep the whole block busy.  MEASURED: sending
        # every prime that way costs 9 ms where the split costs 0.15, and
        # the optimum sits at about four multiples per thread -- the
        # cooperative path pays a 64-bit division and a block-wide pass per
        # prime, which swamps the imbalance it is there to fix.
        nsmall, nsm = self._splits(subb)
        self.k_mark((nblk,), (self.tpb_mark,),
                    (d_bits, np.uint64(base), np.uint64(npos), d_sp,
                     np.int32(nsm), np.int32(nsmall)))
        if nsm < nsp:
            nb = min((nsp - nsm + 255) // 256, 8192)
            self.k_mark_large((nb,), (256,),
                              (d_bits, np.uint64(base), np.uint64(npos),
                               d_sp, np.int32(nsm), np.int32(nsp)))
        per = 1024
        ncb = int((nwords + per - 1) // per)
        nmax = _prime_bound(lo, hi, npos)
        d_ps = self._buf("ps", nmax, np.uint64)
        d_cagg = self._buf("cagg", ncb, np.uint64)
        d_cinc = self._buf("cinc", ncb, np.uint64)
        ntile_s = int((nmax + 32 * self.run_len - 1) // (32 * self.run_len))
        d_all = self._buf("stat", ncb + ntile_s + 2, np.int32)
        d_all.fill(0)                # ONE fill for both look-backs
        d_cst = d_all[:ncb + 1]                        # [ncb] is the counter
        d_tot = self._buf("tot", 1, np.uint64)
        self._d_sst = d_all[ncb + 1:]
        self.k_compact((ncb,), (32,),
                       (d_bits, np.uint64(nwords), np.int32(per),
                        np.uint64(base), d_ps, np.uint64(nmax), d_cagg,
                        d_cinc, d_cst, d_cst[ncb:], d_tot, np.int32(ncb)))
        self._nmax_seen = max(getattr(self, "_nmax_seen", 0), nmax)
        self._sweep(d_ps, d_tot, nmax, d_k0, d_k0b, d_seed, d_seed2,
                    d_hits, d_nh, plan)

    def _sweep(self, d_ps, d_n, nmax, d_k0, d_k0b, d_seed, d_seed2,
               d_hits, d_nh, plan):
        wtot, run = plan["wtot"], plan["run"]
        # EVERY tile needs a warp: the kernel has no outer loop, so a grid
        # short of ntile drops the tail of the line in silence.
        ntile = int((nmax + 32 * run - 1) // (32 * run))
        d_agg = self._buf("agg", ntile * wtot, np.uint32)
        d_inc = self._buf("inc", ntile * wtot, np.uint32)
        d_st = self._d_sst                # zeroed with the compaction's, once
        d_ctr = d_st[ntile:ntile + 1]
        nblk = max((ntile * 32 + self.tpb - 1) // self.tpb, 1)
        self.k_sweep((nblk,), (self.tpb,),
                     (d_ps, d_n, d_k0, d_seed, d_hits, d_nh,
                      np.int32(HIT_BUF), d_agg, d_inc, d_st, d_ctr,
                      d_seed2, d_k0b))


def _prime_bound(lo, hi, npos):
    """A safe upper bound on the primes in [lo, hi).

    Rosser-Schoenfeld: pi(x) < x/(ln x - 1.1) for x > 60184, and
    pi(x) > x/ln x for x >= 17.  Tight matters twice over -- it sizes the
    compacted array AND the sweep's grid, and a loose bound launches warps
    that do nothing but contend for the tile counter (a 1.26x bound cost
    12% of the sweep).
    """
    if hi <= 60184:
        return int(npos)
    n = hi / (math.log(hi) - 1.1)
    if lo >= 17:
        n -= lo / math.log(lo)
    y = hi - lo
    if lo >= 10 ** 6 and y >= 1 << 20:
        # High on the line the density is 1/ln(lo) to well under a percent
        # over a segment this long; 1.25x of that is orders of magnitude of
        # margin, and sieve_compact clamps and reports rather than
        # overruns if it were ever wrong.
        n = min(n, 1.25 * y / math.log(lo) + 4096)
    if y >= 8:
        # Montgomery-Vaughan: pi(x+y) - pi(x) <= 2y/ln y, which is what
        # binds for a short segment high up the line, where the difference
        # of two large pi estimates is worthless (17x loose at p = 1e15).
        n = min(n, 2.0 * y / math.log(y))
    return int(min(npos, int(n) + 64))


def _k_bound(p_hi):
    """A safe upper bound on pi(p_hi) -- the width of the index line."""
    x = float(max(p_hi, 17))
    return int(1.26 * x / math.log(x)) + 16


def _state_words(plan, sums):
    """Pack the exact sums into the plan's little-endian words.

    Via int.to_bytes rather than a shift-and-mask loop: at 83 words and a
    ~500-bit sum the Python loop was 20 us of a 1.1 ms window, which is
    real money once the device side is under half a millisecond.
    """
    w = np.zeros(plan["wtot"], dtype=np.uint32)
    for f in plan["fams"]:
        m, _ = f
        v, o, W = int(sums.get(m, 0)), plan["off"][f], plan["W"][f]
        if v.bit_length() > 32 * W:
            raise CeilingExceeded(
                f"S({m}, k) does not fit the plan's {W} words; "
                f"the run was sized for p_hi = {plan['p_hi']}")
        w[o:o + W] = np.frombuffer(v.to_bytes(4 * W, "little"),
                                   dtype=np.uint32)
    return w


def _read_words(plan, w):
    out = {}
    raw = np.ascontiguousarray(w, dtype=np.uint32).tobytes()
    for f in plan["fams"]:
        m, _ = f
        o, W = plan["off"][f], plan["W"][f]
        out[m] = int.from_bytes(raw[4 * o:4 * (o + W)], "little")
    return out


# --------------------------------- gates -----------------------------------
#
# v2 is a REPLACEMENT engine, so its gates are about the thing that could go
# wrong when an engine is rewritten for speed: the stream changing.  v1 stays
# in the tree precisely so that claim stays checkable (CLAUDE.md rule 3), and
# these compare v2 against BOTH other implementations on populated windows.

_GATE_FAMS = ref.ALL_FAMILIES


def g14_parity_v1_v2():
    """Bit-for-bit parity with the v1 GPU engine AND the CPU engine on
    populated windows, at several heights and across segment boundaries.
    An empty comparison is vacuous and does not count."""
    import psum_gpu as v1
    windows = [(2, 300000), (2, 1200000), (300000, 3000000)]
    for lo, hi in windows:
        st = (lambda ms: cpu.State(ms, p=lo)) if lo > 2 else (lambda ms: None)
        c = cpu.CpuSweep(_GATE_FAMS, seg=1 << 16)
        chits, cst = c.run(hi, state=st(c.ms))
        a = v1.GpuSweep(_GATE_FAMS, seg=1 << 18, chunk=1 << 12)
        ahits, ast = a.run(hi, state=st(a.ms))
        b = GpuSweep2(_GATE_FAMS, seg=1 << 17, run=8, tpb=64, subw=512)
        bhits, bst = b.run(hi, state=st(b.ms))
        cf, af, bf = (sorted(h for h in x if h[2] > 1)
                      for x in (chits, ahits, bhits))
        if not cf:
            return False, f"G14 FAIL: window [{lo}, {hi}) is EMPTY, so vacuous"
        if not (cf == af == bf):
            diff = sorted(set(bf) ^ set(cf))[:3]
            return False, (f"G14 FAIL: window [{lo}, {hi}): cpu {len(cf)}, "
                           f"v1 {len(af)}, v2 {len(bf)}; first difference "
                           f"{diff}")
        if not (cst.k == ast.k == bst.k and cst.sums == ast.sums == bst.sums):
            return False, (f"G14 FAIL: window [{lo}, {hi}): the engines "
                           f"disagree about the state (k {cst.k} / {ast.k} / "
                           f"{bst.k})")
    return True, ("G14 ok: v2 stream == v1 stream == CPU stream on 3 "
                  "populated windows to p = 3e6, states identical, across "
                  "segment and tile boundaries")


def g15_segmentation_invisible():
    """The segmentation and the tile geometry must not be observable: the
    same window swept at several (seg, run, tpb, subw) settings has to give
    one stream and one state.  The look-back's seed path is only exercised
    beyond 32 tiles, which is exactly where the first version of it was
    wrong, so one setting here is deliberately tile-rich."""
    hi = 1200000
    shapes = [(1 << 20, 128, 64, 2048),      # one segment, few tiles
              (1 << 17, 8, 64, 512),         # many tiles: >32, seeds via
              (1 << 16, 4, 128, 512),        #   the look-back's front walk
              (1 << 19, 32, 32, 1024),
              (1 << 20, 1, 64, 2048)]        # MORE tiles than the device
                                             # holds warps -- the shape a
                                             # short grid drops in silence
    base = None
    for seg, run, tpb, subw in shapes:
        e = GpuSweep2(_GATE_FAMS, seg=seg, run=run, tpb=tpb, subw=subw)
        hits, st = e.run(hi)
        got = (sorted(hits), st.k, tuple(sorted(st.sums.items())))
        if base is None:
            base = got
            if not got[0]:
                return False, "G15 FAIL: the window is EMPTY, so vacuous"
        elif got != base:
            return False, (f"G15 FAIL: shape seg={seg} run={run} tpb={tpb} "
                           f"subw={subw} disagrees ({len(got[0])} hits vs "
                           f"{len(base[0])})")
    ntiles = max(1, base[1] // 32)
    return True, (f"G15 ok: 5 segment/tile geometries agree exactly on "
                  f"{len(base[0])} hits and the state, up to ~{ntiles} "
                  f"tiles -- past the device's warp capacity, so a grid "
                  f"that cannot cover the line is caught")


def g16_width_plan_is_sound():
    """The generated widths must hold every value the run can produce, and
    the engine must REFUSE a run it cannot represent rather than truncate."""
    for p_hi in (1 << 20, 1 << 26, 10 ** 12, 10 ** 15):
        k_hi = _k_bound(p_hi)
        plan = build_plan(_GATE_FAMS, p_hi, k_hi)
        for f in plan["fams"]:
            m, e = f
            top = k_hi * (p_hi - 1) ** m + e
            if top >= 1 << (32 * plan["W"][f]):
                return False, (f"G16 FAIL: m={m} at p_hi={p_hi:.3e} needs "
                               f"more than {plan['W'][f]} words")
            if (p_hi - 1) ** m >= 1 << (32 * plan["lpow"](m)):
                return False, (f"G16 FAIL: p^{m} at p_hi={p_hi:.3e} does not "
                               f"fit {plan['lpow'](m)} words")
        for (mm, a, b) in power_chain(plan["ms"], plan["lpow"]):
            if plan["lpow"](mm) > plan["lpow"](a) + plan["lpow"](b):
                return False, (f"G16 FAIL: chain step {mm} = {a}+{b} leaves "
                               f"words undefined at p_hi={p_hi:.3e}")
    e = GpuSweep2(_GATE_FAMS)
    try:
        e.check_ceiling(cpu.P_CEIL * 2)
    except CeilingExceeded:
        pass
    else:
        return False, "G16 FAIL: a run past P_CEIL was accepted"
    return True, ("G16 ok: generated widths hold k*p^m and p^m at 4 heights "
                  "to 1e15, every chain step is fully defined, and a run "
                  "past P_CEIL is refused")


GATES = [g14_parity_v1_v2, g15_segmentation_invisible, g16_width_plan_is_sound]

if __name__ == "__main__":
    import pathlib as _pl
    import sys as _s
    _s.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown

    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)

    _s.exit(_shutdown.graceful(_gates) or 0)
