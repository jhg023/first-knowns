"""ladder_gpu.py -- the GPU engine for A247965.

The same mathematics a third time, in CUDA, and never trusted alone: G6
pins its output stream bit-for-bit against the numpy CPU engine on
populated windows at several heights including the enforced ceiling, and
G14 pins its kill decisions against big-integer divisibility of the
actual values with no engine on the other side.

How it differs from the CPU engine -- which is the point of having two:

  * The CPU engine derives the killed j-residues of each prime from
    sympy's SQUARE ROOTS of -1/m and marks arithmetic progressions with
    numpy slice strides.  This engine never takes a square root: it
    derives every kill decision from the residue WALK

        t  = ((W mod q) * s)^2 mod q          == k^2 mod q for j == s
        r  = t + 1, then r += t, n times      == m*k^2 + 1 mod q, m = 1..n

    and a hit on r == 0 is a kill.  The walk is evaluated on the device,
    once per (prime, residue), into a bit table; the sieve then consumes
    the table.  Two constructions, no shared subroutine -- the engines
    agree only because the mathematics does.
  * Arithmetic is Barrett magic-multiply throughout (huntlib/gpu.py); the
    CPU engine uses plain `%`.

The engine (v2, the bit-sieve restructure of OPTIMIZATION.md 2.1/2.2):

  stage 1a  For a fixed prime q, whether j is killed depends only on
            j mod q, so 64 consecutive j share one 64-bit kill pattern
            indexed by (q, j mod q).  A thread walks T blocks of 64
            candidates, holds one residue register per sieve prime, ORs
            one pattern word per prime per block, and extracts survivors
            from the complement with find-first-set.  NS primes.
  stage 1b  Survivors of 1a (a queue) are tested against the remaining
            primes to q2 in COMPACTION ROUNDS cut geometrically by
            population (each round ends when survival within it has
            fallen RATIO-fold), so every round restarts with all lanes
            alive and warps do not idle behind their slowest lane.  The
            test is one Barrett j mod q and one probe of the kill-bit
            table.  Dense rounds run one thread per candidate; sparse
            deep rounds run one WARP per candidate with the lanes
            splitting the primes and voting.  Counts stay on the device;
            a launch is a captured CUDA graph, two launches are in
            flight on two streams, and the chain reaches the host once
            per launch.
  v1        The original one-thread-per-candidate kernel is kept BELOW,
            unreachable from the campaign, as the parity reference for
            G15 (v2 stream == v1 stream, bit for bit).

Representation: candidates are the pair (W, j) with k = W*j.  k is never
formed on the device -- it does not fit a machine word past a(12) and it
does not need to.  j stays inside u64 to the enforced ceiling J_CEIL, so
this one engine spans the entire search range.

Sizes, all enforced by G14 rather than asserted in a comment: W mod q and
s = j mod q are both < q < 2^16, so their product is < 2^32; t < q so t*t
is < 2^32; every reduction runs on inputs it is exact for.

Gates here: G6 (GPU == CPU parity), G7 (planted-fake drill), G8 (the GPU
rediscovers a(7) end-to-end), G13 (the stream does not depend on how the
work is sliced), G14 (the kernel's kill decisions == big-integer
divisibility of the actual values m*k^2+1), G15 (v2 == v1).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown  # noqa: E402
from huntlib.gpu import barrett_magics                        # noqa: E402
from huntlib.primes import mr_is_prime                        # noqa: E402
from ladder_reference import K_FLOOR, KNOWN, wheel_modulus    # noqa: E402
from ladder_search import CpuEngine, J_CEIL, Q2_DEFAULT       # noqa: E402

try:
    import cupy as cp
except Exception:                                    # pragma: no cover
    cp = None

BLOCK = 256
Q2_MAX = 1 << 31         # the deepest sieve this engine's arithmetic is
#                          exact for.  The binding constraint is the residue
#                          walk in _TABLE_SRC, whose intermediates reach q^2;
#                          in u64 that needs q < 2^32.  Stage 1b's Barrett
#                          (j mod q with j < 2^62) and stage 1a's are exact
#                          over the same range.  Gated by g16, not asserted.

# ---- tuning constants (v2).  Snapshotted onto the instance in __init__;
# ---- nothing compiles against the class attribute after that.
S1A_TARGET = 1.2e-3      # stage 1a takes the fewest primes that bring the
#                          survival below this; NS is DERIVED from it, not
#                          tuned per filter (n = 13 -> 16 primes, n = 10 ->
#                          23), because the sweep optimum was NS = 16 at
#                          n = 13 and ~20 at n = 10 -- the same survival
NS_MAX = 32              # and never more: the pattern table's footprint is
#                          a cliff (12 KB -> 48 KB measured 2.6x slower)
T_MAX = 2048             # 64-candidate blocks per stage-1a thread, at most.
#                          T is DERIVED per launch: the largest T (per-thread
#                          setup amortized furthest) that still puts
#                          MIN_BLOCKS_PER_SM thread blocks on every SM, so
#                          small windows keep the device full.  T=None
#                          derives; an int pins it.  RE-SWEPT with RATIO 2
#                          (OPTIMIZATION_LOG.md #23): 2048 is 1.025x on the
#                          campaign shape and 1.020x on SCORE13 over 1024,
#                          paired min 1.007/1.014.  4096 measured another
#                          1.4% but is NOT reachable by the derivation at
#                          LAUNCH 2^34 without halving MIN_BLOCKS_PER_SM,
#                          which is the guarantee that a small window still
#                          fills the device -- priced, not taken.
MIN_BLOCKS_PER_SM = 4
RATIO_DEFAULT = 2.0      # a stage-1b round ends when survival within it
#                          drops below 1/RATIO (geometric schedule; 0 = one
#                          shot).  The tail is where the divergence lives:
#                          a lane that reaches q ~ 4096 has 6000 primes to
#                          walk while its warp-mates idle, so rounds are
#                          cut by POPULATION, not by prime count.
#                          RE-SWEPT (OPTIMIZATION_LOG.md #22) when the
#                          campaign moved to n = 12 at q2 = 262144, which
#                          is 3.5x the stage-1b primes: 2 beats 4 by
#                          1.116x there (16 rounds against 8), by 1.103x
#                          at n = 12 / q2 = 65536 and by 1.034x on
#                          SCORE13 -- so it is not a campaign-only
#                          setting, and the earlier verdict (4 by 1.097x)
#                          does not reproduce on an idle machine.
LAUNCH_DEFAULT = 1 << 34  # candidates per launch (SCORE13: 2^33 0.93x, 2^32 0.84x)
GRID_1B_MAX = 4096       # cap on a round kernel's grid (grid-stride)


# --------------------------------------------------------------- tables ---
# The residue WALK, evaluated once per (prime, residue) into a bit table.
#
# 64-BIT Barrett, and the width is the whole point.  This walk squares a
# residue (t = k^2 mod q) and multiplies W mod q by s, so its intermediates
# reach q^2.  In 32-bit that is exact only for q < 2^16 -- which is why the
# engines' own q2 default is 65536 and why nothing here ever noticed.  Ask
# for a deeper sieve and the products silently wrap: at q2 = 262144 the
# table came out wrong for primes above ~2^16 (measured: q = 81899 marked 7
# residues dead where 10 are, and not a subset), the sieve both kept
# candidates it should kill and KILLED CANDIDATES IT SHOULD KEEP, and the
# a(7) canary went missing -- caught by the prelude, before a campaign.
# With 64-bit products the walk is exact for every q < 2^32, which is past
# any sieve depth this problem will ever want.  It runs once per engine, so
# the width costs nothing that matters.
_TABLE_SRC = r'''
extern "C" __global__
void build_bits(const int nprimes, const int nfilter,
                const unsigned long long* __restrict__ primes,
                const unsigned long long* __restrict__ wmod,
                const unsigned long long* __restrict__ magic,
                const unsigned int* __restrict__ boff,
                unsigned int* __restrict__ bits)
{
    const int i = blockIdx.x;
    if (i >= nprimes) return;
    const unsigned long long q = primes[i], wm = wmod[i], mg = magic[i];
    const unsigned int base = boff[i];
    for (unsigned int s = threadIdx.x; s < (unsigned int)q; s += blockDim.x) {
        /* t = k^2 mod q with k = W*j and j == s: both factors are < q, so
           every product below is < 2^64 and every reduction is exact */
        unsigned long long t = wm * (unsigned long long)s;
        t -= __umul64hi(t, mg) * q;
        if (t >= q) t -= q;
        if (t >= q) t -= q;
        t = t * t;
        t -= __umul64hi(t, mg) * q;
        if (t >= q) t -= q;
        if (t >= q) t -= q;
        unsigned long long r = t + 1ULL;
        if (r >= q) r -= q;
        bool dead = false;
        for (int m = 0; m < nfilter; ++m) {
            if (r == 0ULL) { dead = true; break; }
            r += t;
            if (r >= q) r -= q;
        }
        if (dead) atomicOr(&bits[base + (s >> 5)], 1u << (s & 31u));
    }
}

extern "C" __global__
void build_pat(const int ns,
               const unsigned int* __restrict__ primes,
               const unsigned int* __restrict__ boff,
               const unsigned int* __restrict__ bits,
               const unsigned int* __restrict__ po,
               unsigned long long* __restrict__ pat)
{
    const int i = blockIdx.x;
    if (i >= ns) return;
    const unsigned int q = primes[i], base = boff[i], p0 = po[i];
    for (unsigned int s = threadIdx.x; s < q; s += blockDim.x) {
        unsigned long long w = 0ULL;
        unsigned int r = s;
        for (int b = 0; b < 64; ++b) {
            if ((bits[base + (r >> 5)] >> (r & 31u)) & 1u)
                w |= 1ULL << b;
            r += 1u;
            if (r >= q) r -= q;
        }
        pat[p0 + s] = w;
    }
}
'''

# ------------------------------------------------------------ stage 1a ---
# Generated per engine: NS primes baked as literals (q, Barrett magic,
# 64 mod q, table row offset).  One residue register per prime.
_S1A_HEAD = r'''
extern "C" __global__ void __launch_bounds__(256)
sieve1a(const unsigned long long* __restrict__ args,   /* j0, count, T */
        const unsigned long long* __restrict__ pat,
        unsigned long long* __restrict__ out,
        unsigned int* __restrict__ nout, const unsigned int cap)
{
    const unsigned long long j0 = args[0], count = args[1];
    const unsigned int T = (unsigned int)args[2];
    const unsigned long long tid = blockIdx.x * (unsigned long long)blockDim.x
                                   + threadIdx.x;
    const unsigned long long base = tid * (64ULL * T);
    if (base >= count) return;
    const unsigned long long jb = j0 + base;
    const unsigned long long rem = count - base;
    unsigned int nblk = T;
    unsigned long long tailmask = ~0ULL;
    if (rem < 64ULL * T) {
        nblk = (unsigned int)((rem + 63ULL) >> 6);
        const unsigned int tailbits = (unsigned int)(rem - 64ULL * (nblk - 1u));
        if (tailbits < 64u) tailmask = (~0ULL) >> (64u - tailbits);
    }
'''
_S1A_INIT = r'''
    unsigned int s%(i)d;
    {
        const unsigned long long qh = __umul64hi(jb, %(magic)dULL);
        unsigned long long r = jb - qh * %(q)dULL;
        if (r >= %(q)dULL) r -= %(q)dULL;
        if (r >= %(q)dULL) r -= %(q)dULL;
        s%(i)d = (unsigned int)r;
    }
'''
_S1A_LOOP_HEAD = r'''
    for (unsigned int b = 0; b < nblk; ++b) {
        unsigned long long acc = 0ULL;
'''
_S1A_STEP = r'''
        acc |= pat[%(po)du + s%(i)d];
        s%(i)d += %(step)du; if (s%(i)d >= %(q)du) s%(i)d -= %(q)du;
'''
_S1A_TAIL = r'''
        unsigned long long alive = ~acc;
        if (b == nblk - 1u) alive &= tailmask;
        while (alive) {
            const unsigned int u = (unsigned int)__ffsll((long long)alive) - 1u;
            alive &= alive - 1ULL;
            const unsigned int slot = atomicAdd(nout, 1u);
            if (slot < cap) out[slot] = jb + 64ULL * b + u;
        }
    }
}
'''


def _sieve1a_src(entries):
    src = [_S1A_HEAD]
    for e in entries:
        src.append(_S1A_INIT % e)
    src.append(_S1A_LOOP_HEAD)
    for e in entries:
        src.append(_S1A_STEP % e)
    src.append(_S1A_TAIL)
    return "".join(src)


# ------------------------------------------------------------ stage 1b ---
# Queue-driven; tests primes [i0, i1), forwards survivors.  Counts arrive
# as device pointers so rounds chain without host round-trips.  Two
# thread shapes (dense: one thread per candidate; sparse: one warp per
# candidate, lanes split the primes and vote) are generated from one
# template.  The per-prime test is one Barrett j mod q and one probe of
# the device-built kill-bit table.  (The v1 residue walk in this position
# measured 0.69x on SCORE13 -- OPTIMIZATION_LOG.md; it survives only in
# the v1 parity kernel below.)
_S1B_TEST_BITS = r"""
                const unsigned long long q = primes[i];
                const unsigned long long qhat = __umul64hi(j, magic[i]);
                unsigned long long jq = j - qhat * q;
                if (jq >= q) jq -= q;
                if (jq >= q) jq -= q;
                const unsigned int s = (unsigned int)jq;
                if ((bits[boff[i] + (s >> 5)] >> (s & 31u)) & 1u) dead = true;
"""
_S1B_ARGS = r"""(const unsigned int* __restrict__ nin_ptr,
             const unsigned long long* __restrict__ qin,
             const unsigned int cap_in,
             const int i0, const int i1, const int nfilter,
             const unsigned long long* __restrict__ primes,
             const unsigned long long* __restrict__ magic,
             const unsigned long long* __restrict__ wmod,
             const unsigned int* __restrict__ boff,
             const unsigned int* __restrict__ bits,
             unsigned long long* __restrict__ qout,
             unsigned int* __restrict__ nout, const unsigned int cap)"""
_S1B_DENSE = r"""
extern "C" __global__
void sieve1b__ARGS__
{
    unsigned int total = *nin_ptr;
    if (total > cap_in) total = cap_in;
    for (unsigned int idx = blockIdx.x * blockDim.x + threadIdx.x;
         idx < total; idx += gridDim.x * blockDim.x) {
        const unsigned long long j = qin[idx];
        bool dead = false;
        for (int i = i0; i < i1; ++i) {
            {
__TEST__
            }
            if (dead) break;
        }
        if (!dead) {
            const unsigned int slot = atomicAdd(nout, 1u);
            if (slot < cap) qout[slot] = j;
        }
    }
}
"""
# Sparse variant: ONE WARP PER CANDIDATE, lanes split the primes.  In the
# geometric schedule the deep rounds hold a few thousand candidates that
# each walk thousands of primes; one thread per candidate leaves the GPU
# nearly empty and every lane latency-bound on its own dependent chain.
# Lane l tests primes i0+l, i0+l+32, ... and the warp votes every
# VOTE_EVERY iterations so a killed candidate stops early.
_S1B_SPARSE = r"""
extern "C" __global__
void sieve1b_warp__ARGS__
{
    unsigned int total = *nin_ptr;
    if (total > cap_in) total = cap_in;
    const unsigned int lane = threadIdx.x & 31u;
    const unsigned int wid = (blockIdx.x * blockDim.x + threadIdx.x) >> 5;
    const unsigned int nwarps = (gridDim.x * blockDim.x) >> 5;
    for (unsigned int c = wid; c < total; c += nwarps) {
        const unsigned long long j = qin[c];
        bool dead = false;
        int i = i0 + (int)lane;
        for (;;) {
            #pragma unroll 1
            for (int v = 0; v < __VOTE_EVERY__; ++v, i += 32) {
                if (i < i1) {
__TEST__
                }
            }
            if (__any_sync(0xffffffffu, dead)) { dead = true; break; }
            if (i - (int)lane >= i1) break;   /* uniform: all lanes past i1 */
        }
        if (!dead && lane == 0u) {
            const unsigned int slot = atomicAdd(nout, 1u);
            if (slot < cap) qout[slot] = j;
        }
    }
}
"""


def _s1b_src(sparse, vote):
    src = (_S1B_SPARSE if sparse else _S1B_DENSE)
    return (src.replace("__ARGS__", _S1B_ARGS)
               .replace("__TEST__", _S1B_TEST_BITS)
               .replace("__VOTE_EVERY__", str(int(vote))))


VOTE_EVERY_DEFAULT = 1
WARP_POP_DEFAULT = 1 << 16   # a round whose expected population per launch
#                              is below this uses the warp-per-candidate
#                              kernel (deep, sparse) instead of the
#                              thread-per-candidate one (shallow, dense)


class GpuEngine:
    """CuPy sieve over j, where k = W*j.  v2: bit-sieve + compaction rounds."""

    def __init__(self, n, q2=Q2_DEFAULT, ns=None, T=None,
                 ratio=RATIO_DEFAULT, launch=LAUNCH_DEFAULT,
                 warp_pop=WARP_POP_DEFAULT, vote=VOTE_EVERY_DEFAULT):
        if cp is None:
            raise RuntimeError("CuPy/CUDA not available; use --engine cpu")
        if not (2 < q2 <= Q2_MAX):
            raise ValueError(
                f"q2 {q2} is outside the range this engine's arithmetic is "
                f"exact for (2, {Q2_MAX}]: the residue walk squares values "
                f"below q, so q^2 must stay inside u64")
        self.n = n
        self.q2 = q2
        self.W = wheel_modulus(n)
        primes = np.array([q for q in primerange(n + 2, q2)], dtype=np.uint64)
        self.primes = primes
        self.NP = int(primes.size)
        # snapshot the tuning constants; everything below compiles against
        # the snapshot, never the module constant
        self.NS = None if ns is None else int(min(ns, self.NP))
        self.T = None if T is None else int(T)
        sms = int(cp.cuda.Device().attributes["MultiProcessorCount"])
        self._min_threads = MIN_BLOCKS_PER_SM * sms * BLOCK
        self.RATIO = float(ratio)
        self.LAUNCH = int(launch)
        self.WARP_POP = float(warp_pop)
        self.VOTE = int(vote)
        if (self.T is not None and self.T < 1) or self.LAUNCH < 64 \
                or self.VOTE < 1:
            raise ValueError("bad tuning constants")

        self.d_primes = cp.asarray(primes)
        self.d_magic = cp.asarray(barrett_magics(primes))
        wmod = np.array([self.W % int(q) for q in primes], dtype=np.uint64)
        self.d_wmod = cp.asarray(wmod)

        # ---- kill-bit table for every prime (device-built by the walk)
        p32 = primes.astype(np.uint32)
        words = ((primes.astype(np.int64) + 31) // 32)
        boff = np.concatenate([[0], np.cumsum(words)[:-1]]).astype(np.uint32)
        d_p32 = cp.asarray(p32)
        d_boff = cp.asarray(boff)
        self.d_bits = cp.zeros(int(words.sum()), dtype=cp.uint32)
        mod = cp.RawModule(code=_TABLE_SRC)
        k_bits = mod.get_function("build_bits")
        k_bits((self.NP,), (256,),
               (np.int32(self.NP), np.int32(n), self.d_primes, self.d_wmod,
                self.d_magic, d_boff, self.d_bits))
        # killed-residue counts per prime, from the table itself (one
        # derivation, used for the queue sizing below)
        self.wq = self._popcounts(words, boff)
        # ---- survival through the primes, from the table itself (one
        # derivation, used for NS, the round schedule, the grids, the queues)
        surv = np.cumprod(1.0 - self.wq / primes.astype(np.float64))
        self.survival = np.concatenate([[1.0], surv])   # [i] = through i primes
        if self.NS is None:
            self.NS = int(min(max(int(np.searchsorted(-self.survival,
                                                      -S1A_TARGET)), 1),
                              NS_MAX, self.NP))
        self.s1a_survival = float(self.survival[self.NS])

        # ---- stage-1a pattern table for the first NS primes
        rows = primes[:self.NS].astype(np.int64)
        po = np.concatenate([[0], np.cumsum(rows)[:-1]]).astype(np.uint32)
        self.d_pat = cp.empty(int(rows.sum()), dtype=cp.uint64)
        k_pat = mod.get_function("build_pat")
        k_pat((self.NS,), (256,),
              (np.int32(self.NS), d_p32, d_boff, self.d_bits, cp.asarray(po),
               self.d_pat))
        self.pat_bytes = int(rows.sum()) * 8
        entries = [{"i": i, "q": int(primes[i]),
                    "magic": (1 << 64) // int(primes[i]),
                    "step": 64 % int(primes[i]), "po": int(po[i])}
                   for i in range(self.NS)]
        self.src_1a = _sieve1a_src(entries)
        self.k_1a = cp.RawKernel(self.src_1a, "sieve1a")
        self.k_1b = cp.RawKernel(_s1b_src(False, self.VOTE), "sieve1b")
        self.k_1bw = cp.RawKernel(_s1b_src(True, self.VOTE), "sieve1b_warp")
        self.d_boff = d_boff

        # ---- compaction schedule over the stage-1b primes: a round ends
        # when the population entering it has fallen by RATIO
        self.rounds = []
        i = self.NS
        while i < self.NP:
            if self.RATIO <= 1.0:
                i1 = self.NP
            else:
                target = self.survival[i] / self.RATIO
                i1 = int(np.searchsorted(-self.survival, -target, side="left"))
                i1 = min(max(i1, i + 1), self.NP)
            self.rounds.append((i, i1))
            i = i1
        # grid per round from the expected population entering it; the
        # kernels grid-stride, so an under-estimate costs time, not results.
        # Dense rounds: one thread per candidate.  Sparse rounds (expected
        # population below WARP_POP): one warp per candidate.
        self.round_grid, self.round_warp = [], []
        for i0, i1 in self.rounds:
            exp_in = self.LAUNCH * self.survival[i0]
            warp = exp_in < self.WARP_POP
            lanes = 32 if warp else 1
            g = int(-(-(1.5 * exp_in * lanes) // BLOCK)) + 1
            self.round_grid.append(int(min(max(g, 1), GRID_1B_MAX)))
            self.round_warp.append(bool(warp))

        # ---- queues, sized analytically from the stage-1a survival rate
        # (OPTIMIZATION.md 2.6): both ping-pong buffers get the SAME
        # capacity, so a round's output can never exceed its input and only
        # the stage-1a count needs the overflow check.  Two SLOTS, each with
        # its own stream, queues, counters and scalar args: chain i+1 is
        # enqueued before chain i is read back, so the device never idles
        # on the host (the per-launch sync bubble measured 15% of wall).
        cap = int(1.25 * self.LAUNCH * self.s1a_survival) + (1 << 16)
        self.queue_cap = int(min(max(cap, 1 << 14), 1 << 26))
        self._slots = []
        for _ in range(2):
            self._slots.append({
                "stream": cp.cuda.Stream(non_blocking=True),
                "q1": cp.empty(self.queue_cap, dtype=cp.uint64),
                "q2": cp.empty(self.queue_cap, dtype=cp.uint64),
                # one counter per stage: [0] = stage 1a, [1 + r] = round r
                "cnt": cp.zeros(2 + len(self.rounds), dtype=cp.uint32),
                # stage-1a scalars live on the device so a full-size launch
                # is a CUDA-graph replay (one args upload, one graph launch)
                "args": cp.zeros(4, dtype=cp.uint64),
                "graph": None, "graph_qin": None,
                "count": 0, "qin": None, "prof": None})
        self._use_graph = True     # False: eager launches (measurement only)
        self._serial = False       # True: finish each launch before the next
        #                            (measurement only)

    def _popcounts(self, words, boff):
        bits = self.d_bits.get()
        out = np.zeros(self.NP, dtype=np.int64)
        for i in range(self.NP):
            seg = bits[int(boff[i]):int(boff[i]) + int(words[i])]
            out[i] = int(np.unpackbits(seg.view(np.uint8)).sum())
        return out

    # ---------------------------------------------------------------- sieve
    def _T_for(self, count):
        if self.T is not None:
            return self.T
        return int(min(T_MAX, max(1, count // (64 * self._min_threads))))

    def _enqueue(self, slot, count, marks=None):
        """Enqueue the chain (counters zero -> stage 1a -> rounds) on the
        current stream for a launch of `count` candidates whose scalars are
        already in the slot's args.  With `marks` a list, an event is
        recorded after every kernel (profiling only)."""
        d_cnt = slot["cnt"]
        d_cnt.fill(0)
        cap = np.uint32(self.queue_cap)
        T = self._T_for(count)
        threads = (count + 64 * T - 1) // (64 * T)
        grid = (threads + BLOCK - 1) // BLOCK
        self.k_1a((grid,), (BLOCK,),
                  (slot["args"], self.d_pat, slot["q1"], d_cnt[0:1], cap))
        if marks is not None:
            e = cp.cuda.Event(); e.record(); marks.append(e)
        qin, nin = slot["q1"], d_cnt[0:1]
        for r, (i0, i1) in enumerate(self.rounds):
            qout = slot["q2"] if qin is slot["q1"] else slot["q1"]
            nout = d_cnt[1 + r:2 + r]
            kern = self.k_1bw if self.round_warp[r] else self.k_1b
            kern((self.round_grid[r],), (BLOCK,),
                 (nin, qin, cap, np.int32(i0), np.int32(i1),
                  np.int32(self.n), self.d_primes, self.d_magic,
                  self.d_wmod, self.d_boff, self.d_bits, qout, nout, cap))
            qin, nin = qout, nout
            if marks is not None:
                e = cp.cuda.Event(); e.record(); marks.append(e)
        return qin

    def _start(self, slot, j0, count):
        """Enqueue one launch on a slot and return without waiting.

        A full-size launch (count == LAUNCH) replays a CUDA graph captured
        on the slot's first use; the window's ragged last launch, and any
        launch with self.profile set to a list (CUDA events around every
        kernel, measurement only), run the same kernels eagerly.
        """
        prof = getattr(self, "profile", None)
        slot["count"] = count
        with slot["stream"]:
            slot["args"].set(np.array([j0, count, self._T_for(count), 0],
                                      dtype=np.uint64))
            if prof is not None:
                e0 = cp.cuda.Event(); e0.record()
                marks = []
                slot["qin"] = self._enqueue(slot, count, marks)
                slot["prof"] = (e0, marks)
            elif count == self.LAUNCH and self._use_graph:
                if slot["graph"] is None:
                    slot["stream"].begin_capture()
                    slot["graph_qin"] = self._enqueue(slot, count)
                    slot["graph"] = slot["stream"].end_capture()
                slot["graph"].launch(stream=slot["stream"])
                slot["qin"] = slot["graph_qin"]
            else:
                slot["qin"] = self._enqueue(slot, count)

    def _finish(self, slot):
        """Wait for a slot's launch and return its sorted survivors."""
        prof = getattr(self, "profile", None)
        with slot["stream"]:
            counts = slot["cnt"].get()
            if int(counts[0]) > self.queue_cap:
                raise RuntimeError(f"stage-1a queue overflow: {int(counts[0])}"
                                   f" > {self.queue_cap}; shrink the launch")
            got = int(counts[len(self.rounds)])
            arr = None
            if got:
                # atomics scramble the order; the survivors of a launch are
                # few (~1e-7 of it), so they are sorted on the host
                arr = slot["qin"][:got].get()
                arr.sort()
            if prof is not None and slot["prof"] is not None:
                e0, marks = slot["prof"]
                e3 = cp.cuda.Event(); e3.record(); e3.synchronize()
                seq = [e0] + marks + [e3]
                prof.append({"stage": [cp.cuda.get_elapsed_time(x, y)
                                       for x, y in zip(seq[:-1], seq[1:])],
                             "counts": counts.tolist()})
                slot["prof"] = None
        return arr

    def survivors_j(self, j_lo, j_hi, launch=None):
        """Sorted u64 array of surviving j in [j_lo, j_hi)."""
        if j_hi > J_CEIL:
            raise ValueError(f"j {j_hi} past the enforced ceiling {J_CEIL}")
        if j_lo * self.W < K_FLOOR:
            raise ValueError("engines refuse to run below K_FLOOR")
        launch = int(launch or self.LAUNCH)
        if launch > self.LAUNCH:
            raise ValueError("launch larger than the queues were sized for")
        out = []
        j0 = int(j_lo)
        pending, i = None, 0
        while j0 < int(j_hi):
            count = min(launch, int(j_hi) - j0)
            slot = self._slots[i & 1]
            self._start(slot, j0, count)         # device runs chain i ...
            if pending is not None:              # ... while the host reads
                got = self._finish(pending)      #     back chain i-1
                if got is not None:
                    out.append(got)
            pending = slot
            if self._serial:
                got = self._finish(pending)
                if got is not None:
                    out.append(got)
                pending = None
            j0 += count
            i += 1
        if pending is not None:
            got = self._finish(pending)
            if got is not None:
                out.append(got)
        if not out:
            return np.empty(0, dtype=np.uint64)
        return np.concatenate(out)

    def survivors_pre_mr(self, k_lo, k_hi, launch=None):
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


# ------------------------------- v1, gate-only ------------------------------
# The engine as first gated (2026-08-18): one thread per candidate, every
# prime in one loop, early exit.  Retained as the parity reference for G15
# and NEVER reachable from the campaign (CLAUDE.md rule 3).
_KERNEL_V1 = r'''
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


class GpuEngineV1:
    """The v1 kernel, for G15 only.  Not a campaign engine."""

    def __init__(self, n, q2=Q2_DEFAULT):
        if cp is None:
            raise RuntimeError("CuPy/CUDA not available")
        self.n = n
        self.q2 = q2
        self.W = wheel_modulus(n)
        primes = np.array([q for q in primerange(n + 2, q2)], dtype=np.uint64)
        self.primes = primes
        self.d_primes = cp.asarray(primes)
        self.d_magic = cp.asarray(barrett_magics(primes))
        self.d_wmod = cp.asarray(np.array([self.W % int(q) for q in primes],
                                          dtype=np.uint64))
        self.kernel = cp.RawKernel(_KERNEL_V1, "sieve")
        self.queue_cap = 1 << 22
        self._d_out = cp.empty(self.queue_cap, dtype=cp.uint64)
        self._d_n = cp.zeros(1, dtype=cp.uint32)

    def survivors_j(self, j_lo, j_hi, launch=1 << 24):
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
                raise RuntimeError("v1 survivor queue overflow")
            if got:
                out.append(cp.sort(d_out[:got]).get())
            j0 += count
        if not out:
            return np.empty(0, dtype=np.uint64)
        return np.concatenate(out)


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

    Cuts that have all broken sieves elsewhere: a split in the middle of
    a launch, launches smaller than a block, a start that is not aligned
    to anything -- and, for a block-structured sieve, cuts that are not
    multiples of the 64-candidate pattern word and of the per-thread
    strip, so the edge masks and the partial-strip path are exercised on
    populated windows.
    """
    n, j_lo, span = 10, 7 * 10**9 + 12345, 8 * 10**6
    eng = GpuEngine(n, q2=1024)
    whole = eng.survivors_j(j_lo, j_lo + span)
    strip = 64 * eng._T_for(span)
    for cut in (span // 3, span // 2, span - 1, 63, 64, 65, strip - 1,
                strip, strip + 1, 3 * strip + 17):
        a = eng.survivors_j(j_lo, j_lo + cut)
        b = eng.survivors_j(j_lo + cut, j_lo + span)
        joined = np.concatenate([a, b]) if a.size or b.size else a
        if not np.array_equal(whole, joined):
            return False, f"G13 FAIL: split at {cut} != whole"
    for launch in (BLOCK // 2, BLOCK + 1, 100_003, strip, strip + 1,
                   BLOCK * strip + 64):
        sliced = eng.survivors_j(j_lo, j_lo + span, launch=launch)
        if not np.array_equal(whole, sliced):
            return False, f"G13 FAIL: launch size {launch} != whole"
    # a different T changes the strip geometry, never the stream
    for T in (1, 3, 17):
        alt = GpuEngine(n, q2=1024, T=T)
        if not np.array_equal(whole, alt.survivors_j(j_lo, j_lo + span)):
            return False, f"G13 FAIL: T={T} != whole"
    # a small LAUNCH makes the window several full launches (the captured
    # CUDA graph, replayed) plus a ragged last one (the eager path)
    small = GpuEngine(n, q2=1024, launch=1 << 20)
    if not np.array_equal(whole, small.survivors_j(j_lo, j_lo + span)):
        return False, "G13 FAIL: graph-replayed launches != whole"
    if any(sl["graph"] is None for sl in small._slots):
        return False, "G13 FAIL: the graph path was not exercised on both slots"
    if whole.size == 0:
        return False, "G13 FAIL: vacuous (empty window)"
    return True, (f"G13 ok: stream independent of slicing over 10 cuts, "
                  f"6 launch sizes, 3 strip widths and graph-vs-eager "
                  f"launches ({whole.size} survivors)")


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


def g15_v2_matches_v1():
    """The restructured engine returns the v1 stream, bit for bit.

    v1 is the one-thread-per-candidate kernel the project was first gated
    with; it lives above as a gate-only reference.  Populated windows at
    two filters, including one at reduced depth so the deep filter is
    populated too.
    """
    windows = [(10, 10**12 + 777, 6 * 10**7, Q2_DEFAULT),
               (12, 6 * 10**11 + 5, 4 * 10**6, 2048)]
    total = 0
    for n, j_lo, span, q2 in windows:
        v2 = GpuEngine(n, q2=q2).survivors_j(j_lo, j_lo + span)
        v1 = GpuEngineV1(n, q2=q2).survivors_j(j_lo, j_lo + span)
        if v2.size != v1.size or not np.array_equal(v2, v1):
            return False, (f"G15 FAIL: n={n} j in [{j_lo}, {j_lo+span}): "
                           f"{v2.size} v2 vs {v1.size} v1 survivors")
        if v1.size == 0:
            return False, f"G15 FAIL: window n={n} at {j_lo} is empty"
        total += int(v1.size)
    return True, (f"G15 ok: v2 (bit-sieve + rounds) == v1 (one thread per "
                  f"candidate) on {len(windows)} populated windows "
                  f"({total} survivors)")


def g16_deep_sieve_arithmetic():
    """The engine is exact at sieve depths PAST 2^16, and the gate looks there.

    This gate exists because a bug got through every other one.  The walk
    that builds the kill-bit table squares a residue, so its intermediates
    reach q^2; it was written in 32-bit, which is exact only for q < 2^16.
    Every gate in this file used the engine's own q2 default of 65536, so
    for the whole life of the engine no test ever evaluated a prime whose
    square left u32 -- and the first campaign to ask for a deeper sieve got
    a table that was wrong in BOTH directions (at q = 81899 it marked 7
    residues dead where 10 are, and not a subset), which silently kills
    candidates that could be the term being hunted.  The a(7) canary caught
    it; a gate should have.

    So: sample primes across the WHOLE range of a deep sieve, above 2^16 as
    well as below, and check the device-built table against big-integer
    divisibility of the actual values -- no engine on the other side.  Then
    check the deep stream itself against the independent CPU engine, whose
    table comes from sympy's square roots in Python integers and cannot
    share this failure.
    """
    n, q2 = 12, 1 << 18
    eng = GpuEngine(n, q2=q2)
    primes = eng.primes
    words = (primes.astype(np.int64) + 31) // 32
    boff = np.concatenate([[0], np.cumsum(words)[:-1]]).astype(np.int64)
    bits = eng.d_bits.get()
    idx = sorted(set([0, 1, eng.NP // 4, eng.NP // 2] +
                     [int(np.searchsorted(primes, b))
                      for b in (1 << 16, (1 << 16) + 1, 100003, 200003)] +
                     [eng.NP - 2, eng.NP - 1]))
    above = 0
    for i in idx:
        if not 0 <= i < eng.NP:
            continue
        q = int(primes[i])
        above += q > (1 << 16)
        seg = bits[int(boff[i]):int(boff[i]) + int(words[i])]
        got = set(int(x) for x in
                  np.nonzero(np.unpackbits(seg.view(np.uint8),
                                           bitorder="little"))[0] if x < q)
        wm = eng.W % q
        want = set(sj for sj in range(q)
                   if any((m * (wm * sj % q) ** 2 + 1) % q == 0
                          for m in range(1, n + 1)))
        if got != want:
            return False, (f"G16 FAIL: kill-bit table for q={q} has "
                           f"{len(got)} dead residues, divisibility says "
                           f"{len(want)}; symmetric difference "
                           f"{sorted(got ^ want)[:4]}")
    if above < 3:
        return False, "G16 FAIL: fewer than 3 sampled primes exceed 2^16"
    # and the deep stream, against the other engine
    ce = CpuEngine(7, q2=q2)
    ge = GpuEngine(7, q2=q2)
    lo, span = 10**7, 6 * 10**7
    gs = [int(x) for x in ge.survivors_j(lo, lo + span)]
    cs = [int(x) for ch in ce.survivors_j(lo, lo + span) for x in ch.tolist()]
    if not cs:
        return False, "G16 FAIL: deep parity window is empty -- vacuous"
    if gs != cs:
        return False, (f"G16 FAIL: at q2={q2} the GPU stream has {len(gs)} "
                       f"survivors, the CPU engine {len(cs)}")
    return True, (f"G16 ok: at q2={q2} the kill-bit table == big-integer "
                  f"divisibility for {len(idx)} primes spanning the range "
                  f"({above} of them above 2^16, where a 32-bit walk wraps), "
                  f"and the deep GPU stream == the CPU engine's on a "
                  f"populated window ({len(cs)} survivors)")


GATES = [g6_parity_with_cpu, g7_planted_fake, g8_gpu_rediscovers_a7,
         g13_slicing_independence, g14_kernel_matches_bigint,
         g15_v2_matches_v1, g16_deep_sieve_arithmetic]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
