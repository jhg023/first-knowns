"""ap_gpu.py -- the GPU engine for A053647.

The same mathematics a third time, in CUDA, and never trusted alone: G6
pins its output stream bit-for-bit against the numpy CPU engine on
populated windows at several heights including the enforced ceiling, and
G14 pins its kill decisions against big-integer divisibility of the actual
values with no engine on the other side.

How it differs from the CPU engine -- which is the point of having two:

  * The CPU engine computes each killed residue as `(-j * P(n)) % q` in
    Python integers.  This engine never multiplies by P(n) at all: it
    WALKS the residues, starting at 0 and subtracting (P(n) mod q) n times
    with a conditional add-back, so the whole set falls out of n additions
    in u32 registers.  When q divides P(n) the walk simply never leaves 0,
    which is the |F| = 1 case reproducing itself with no branch.
  * Arithmetic is Barrett magic-multiply throughout (huntlib/gpu.py); the
    CPU engine uses plain `%`.
  * The CPU engine sieves a flat array with one entry per integer and
    masks the wheel afterwards.  This engine sieves a BITMAP indexed by
    (wheel period u, lane l) -- p = base + 30*u + R[l] -- so an integer
    divisible by 2, 3 or 5 has no representation at all, and the strided
    kill for a prime q lands with stride 8q in bit space.

THE STRUCTURE OF ONE SEGMENT (v2).  Marking runs on three paths split by
prime size, and every prime is on exactly one of them:

  tables    q <= TAB_MAX_Q.  A prime's kills land in 32-bit bitmap words
            with period q words, so a per-launch table of q masks holds
            every kill it will ever make (build_tab, rebuilt each launch
            because the pattern depends on base mod q).  In mark_shared,
            each thread OWNS @K@ words of the block's sub-bitmap and ORs
            the tables into register accumulators -- the dense small-prime
            kills, ~97%% of all marks at the campaign depth, cost one
            coalesced load each and never touch memory at all until the
            single store (OPTIMIZATION.md 2.1: invert the loop).
  shared    TAB_MAX_Q < q <= SUB_U/QSPLIT_DIV.  One block owns SUB_U wheel
            periods as a sub-bitmap in shared memory; tasks of about
            TARGET_MARKS_SH bits walk the killed residues, solving
                30*u + R[l] == f - base   (mod q)
            once per (residue, lane) per block, and mark with SHARED
            atomics.  The block then stores its exclusively-owned word
            range out plain -- there are no global atomics on this path.
  global    q above the split.  Too sparse to amortize the per-block start
            solve, so these keep the v1 kernel: chunked (prime, chunk)
            tasks marking the global bitmap with atomicOr, launched after
            mark_shared on the same stream.
  compact   One thread per bitmap word, extracting the CLEAR bits with
            find-first-set and appending p - base to the survivor array
            through an atomic counter.  Survivors are sorted on the HOST:
            a device sort of a few thousand values was pure launch
            overhead.

At the campaign depth (2048) every prime is tabulated and the whole sieve
is the register-accumulator gather.  The chunking on the atomic paths is
arithmetic, not a heuristic: it changes which thread marks a bit, never
which bits are marked, and G13 drills every one of these decompositions
by re-sieving the same window with each knob moved.

REPRESENTATION: candidates are the pair (base, offset), base a Python
integer and offset a u64.  p is never formed on the device -- it does not
fit a machine word past a(21) and it does not need to.  The per-launch
(base + R[l]) mod q table is computed in numpy by splitting base as
hi*2^64 + lo against a precomputed 2^64 mod q, so no Python-integer loop
runs per launch.

SUB_U, THREADS and the table cutoff are BAKED into the kernel source as
literals and frozen on the engine instance at construction; the sweep
that chose them is OPTIMIZATION_LOG.md #4-#7.
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.gpu import barrett_magics                          # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
from ap_reference import (KNOWN, W0, W0_RESIDUES, difference)   # noqa: E402
from ap_search import (CpuEngine, P_CEIL, Q2_DEFAULT)           # noqa: E402

try:
    import cupy as cp
except Exception:                       # the CPU fallback path stays usable
    cp = None

Q2_MAX = 1 << 31              # Barrett magics are exact for u32 moduli only
LAUNCH_U = 1 << 27            # wheel periods per device launch (~4.0e9 of
#                               p-line, a 128 MiB bitmap; the sub-bitmaps
#                               live in shared memory so the global bitmap
#                               no longer needs to be L2-resident, and the
#                               larger launch amortizes per-launch host work
#                               (measured 1.105x over 2^25 at depth 2048)
TARGET_MARKS = 4096           # bits one global-path task marks
MAX_CHUNKS = 1 << 17
SURV_CAP = 1 << 22            # survivors one launch may emit before it is
#                               an engine bug rather than a busy window

# The shared-memory mark path (OPTIMIZATION_LOG #5).  Each block owns
# SUB_U wheel periods -- a SUB_U-byte sub-bitmap in shared memory -- marks
# every prime below the split into it with shared atomics, and writes its
# exclusively-owned word range out with plain stores.  Primes above the
# split are too sparse to amortize the per-block start solve (every
# (prime, residue, lane) triple must recompute its first hit in every
# block), so they keep the global-atomic kernel, launched afterwards on
# the same stream.
SUB_U = 1 << 16               # wheel periods per block: 64 KiB of shared
#                               (dynamic, opt-in past the 48 KiB static limit)
TARGET_MARKS_SH = 2048        # bits one shared-path task marks; small
#                               enough to balance, large enough that a
#                               16-residue prime is one task (setup is per
#                               task and per block)
THREADS = 1024                # block size for every kernel here


QSPLIT_DIV = 2                # shared path takes q <= SUB_U / QSPLIT_DIV
TAB_MAX_Q = 2048              # primes at or below this are TABULATED: their
#                               kill pattern per 32-bit bitmap word is
#                               periodic with period q words, so a per-launch
#                               table of q masks replaces every one of their
#                               shared atomics with one load and a register
#                               OR -- the loop inverted per OPTIMIZATION.md
#                               2.1, and the table stores double as the
#                               sub-bitmap's zero-fill


def _qsplit():
    """Largest prime the shared path takes: at least ~QSPLIT_DIV expected
    marks per (residue, lane) per block, so the per-block start solve
    stays a few percent of the marking work."""
    return SUB_U // QSPLIT_DIV

_SRC = r"""
extern "C" {

__device__ __forceinline__ unsigned int bmod(unsigned long long x,
                                             unsigned int q,
                                             unsigned long long magic)
{
    // Barrett magic-multiply modulo (huntlib/gpu.py): qhat is within 2 of
    // floor(x/q), so at most two subtractions finish the job.
    unsigned long long qhat = __umul64hi(x, magic);
    unsigned long long r = x - qhat * (unsigned long long)q;
    if (r >= (unsigned long long)q) r -= (unsigned long long)q;
    if (r >= (unsigned long long)q) r -= (unsigned long long)q;
    return (unsigned int)r;
}

// Per-launch pattern tables for the tabulated primes.  For an odd prime q
// the kills land in bitmap words with period q: word w contains u = 4w + r
// (r < 4), and u == a (mod q) puts bit 8r + l into word w == (a - r)/4
// (mod q).  One thread per tabulated prime writes its q-word table; the
// mark kernel then gathers ALL of a word's small-prime kills as @K@ loads.
__global__ void build_tab(const unsigned int* __restrict__ tabj,
                          const unsigned int* __restrict__ toff,
                          const unsigned int* __restrict__ primes,
                          const unsigned long long* __restrict__ magic,
                          const unsigned int* __restrict__ wcnt,
                          const unsigned int* __restrict__ dmodq,
                          const unsigned int* __restrict__ inv30,
                          const unsigned int* __restrict__ inv4,
                          const unsigned int* __restrict__ blq,
                          unsigned int* __restrict__ tab,
                          unsigned int ntab)
{
    unsigned int t = blockIdx.x * blockDim.x + threadIdx.x;
    if (t >= ntab) return;
    unsigned int j  = tabj[t];
    unsigned int q  = primes[j];
    unsigned long long mg = magic[j];
    unsigned int w  = wcnt[j];
    unsigned int dq = dmodq[j];
    unsigned int iv = inv30[j];
    unsigned int i4 = inv4[j];
    unsigned int off = toff[t];
    unsigned int f = 0u;
    for (unsigned int i = 0; i < w; ++i) {
        for (unsigned int l = 0; l < 8u; ++l) {
            unsigned int rhs = f;
            unsigned int sub = blq[(j << 3) | l];
            rhs = (rhs >= sub) ? (rhs - sub) : (rhs + q - sub);
            unsigned int a = bmod((unsigned long long)rhs
                                  * (unsigned long long)iv, q, mg);
            for (unsigned int r = 0; r < 4u; ++r) {
                unsigned int am = (a >= r) ? (a - r) : (a + q - r);
                unsigned int m = bmod((unsigned long long)am
                                      * (unsigned long long)i4, q, mg);
                atomicOr(&tab[off + m], 1u << ((r << 3) | l));
            }
        }
        f = (f >= dq) ? (f - dq) : (f + q - dq);
    }
}

// The shared-memory mark path (OPTIMIZATION_LOG #5).  One block owns the
// @SUB_U@ wheel periods starting at blockIdx.x * @SUB_U@: it zeroes a
// shared sub-bitmap, marks every task of every prime below the split into
// it with SHARED atomics (orders of magnitude cheaper than the global
// atomics they replace), and stores its word range out PLAIN -- the
// ranges partition the bitmap, so no other block ever touches these
// words, and the global-path kernel for the sparse large primes is
// launched after this one on the same stream.
__global__ void mark_shared(const unsigned int* __restrict__ task_prime,
                            const unsigned int* __restrict__ task_chunk,
                            const unsigned int* __restrict__ chunks,
                            const unsigned int* __restrict__ primes,
                            const unsigned long long* __restrict__ magic,
                            const unsigned int* __restrict__ wcnt,
                            const unsigned int* __restrict__ dmodq,
                            const unsigned int* __restrict__ inv30,
                            const unsigned int* __restrict__ blq,
                            const unsigned int* __restrict__ tabj,
                            const unsigned int* __restrict__ toff,
                            const unsigned int* __restrict__ tab,
                            unsigned int* __restrict__ bits,
                            unsigned long long U,
                            unsigned int nword,
                            unsigned int ntask,
                            unsigned int ntab)
{
    extern __shared__ unsigned int sbits[];      // @SW@ words, passed at launch

    unsigned long long ublk = (unsigned long long)blockIdx.x * @SUB_U@ULL;
    unsigned long long ulim = ublk + @SUB_U@ULL;
    if (ulim > U) ulim = U;

    // Phase B first: the tabulated primes.  Each thread OWNS the words
    // threadIdx.x + k*@THREADS@ and gathers their masks into registers --
    // the dense small-prime kills never touch shared memory, and the
    // stores below double as the sub-bitmap's zero-fill (acc stays 0 when
    // there are no tabulated primes).
    unsigned int acc[@K@];
    #pragma unroll
    for (int k = 0; k < @K@; ++k) acc[k] = 0u;
    unsigned long long w0blk = ublk >> 2;        // this block's first word
    for (unsigned int jt = 0; jt < ntab; ++jt) {
        unsigned int j = tabj[jt];
        unsigned int q = primes[j];
        unsigned long long mg = magic[j];
        unsigned int off = toff[jt];
        unsigned int m = bmod(w0blk + threadIdx.x, q, mg);
        unsigned int dm = bmod((unsigned long long)@THREADS@u, q, mg);
        #pragma unroll
        for (int k = 0; k < @K@; ++k) {
            acc[k] |= tab[off + m];
            m += dm;
            if (m >= q) m -= q;
        }
    }
    if (ntask == 0) {
        // no atomic phase at all: the accumulators ARE the sub-bitmap, so
        // store them straight to global and skip shared memory entirely
        #pragma unroll
        for (int k = 0; k < @K@; ++k) {
            unsigned long long gw = w0blk + threadIdx.x + k * @THREADS@;
            if (gw < nword) bits[gw] = acc[k];
        }
        return;
    }
    #pragma unroll
    for (int k = 0; k < @K@; ++k)
        sbits[threadIdx.x + k * @THREADS@] = acc[k];
    __syncthreads();

    for (unsigned int t = threadIdx.x; t < ntask; t += blockDim.x) {
        unsigned int j  = task_prime[t];
        unsigned int c  = task_chunk[t];
        unsigned int C  = chunks[j];
        unsigned int q  = primes[j];
        unsigned long long mg = magic[j];
        unsigned int w  = wcnt[j];
        unsigned int dq = dmodq[j];
        unsigned int iv = inv30[j];

        // the chunk is a slice of THIS block's u-range
        unsigned long long u_lo = ublk
            + ((unsigned long long)@SUB_U@ULL * c) / (unsigned long long)C;
        unsigned long long u_hi = ublk
            + ((unsigned long long)@SUB_U@ULL * (c + 1)) / (unsigned long long)C;
        if (u_hi > ulim) u_hi = ulim;
        if (u_lo >= u_hi) continue;

        unsigned int f = 0u;
        for (unsigned int i = 0; i < w; ++i) {
            for (unsigned int l = 0; l < 8u; ++l) {
                unsigned int rhs = f;
                unsigned int sub = blq[(j << 3) | l];   // (base+R[l]) mod q,
                rhs = (rhs >= sub) ? (rhs - sub) : (rhs + q - sub);  // host
                unsigned long long prod = (unsigned long long)rhs
                                        * (unsigned long long)iv;
                unsigned long long u = (unsigned long long)bmod(prod, q, mg);
                if (u < u_lo) {
                    unsigned long long need = u_lo - u;
                    u += ((need + (unsigned long long)q - 1ULL)
                          / (unsigned long long)q) * (unsigned long long)q;
                }
                for (; u < u_hi; u += (unsigned long long)q) {
                    unsigned int bit = ((unsigned int)(u - ublk) << 3) | l;
                    atomicOr(&sbits[bit >> 5], 1u << (bit & 31u));
                }
            }
            f = (f >= dq) ? (f - dq) : (f + q - dq);
        }
    }
    __syncthreads();

    unsigned long long w0 = ublk >> 2;           // @SUB_U@ * 8 / 32 words
    for (unsigned int i = threadIdx.x; i < @SW@; i += blockDim.x) {
        unsigned long long gw = w0 + i;
        if (gw < nword) bits[gw] = sbits[i];
    }
}

__global__ void mark(const unsigned int* __restrict__ task_prime,
                     const unsigned int* __restrict__ task_chunk,
                     const unsigned int* __restrict__ chunks,
                     const unsigned int* __restrict__ primes,
                     const unsigned long long* __restrict__ magic,
                     const unsigned int* __restrict__ wcnt,
                     const unsigned int* __restrict__ dmodq,
                     const unsigned int* __restrict__ inv30,
                     const unsigned int* __restrict__ blq,
                     unsigned int* __restrict__ bits,
                     unsigned long long U,
                     unsigned int ntask)
{
    unsigned int t = blockIdx.x * blockDim.x + threadIdx.x;
    if (t >= ntask) return;

    unsigned int j  = task_prime[t];
    unsigned int c  = task_chunk[t];
    unsigned int C  = chunks[j];
    unsigned int q  = primes[j];
    unsigned long long mg = magic[j];
    unsigned int w  = wcnt[j];
    unsigned int dq = dmodq[j];
    unsigned int iv = inv30[j];

    unsigned long long u_lo = (U * (unsigned long long)c) / (unsigned long long)C;
    unsigned long long u_hi = (U * (unsigned long long)(c + 1)) / (unsigned long long)C;
    if (u_lo >= u_hi) return;

    // f walks the killed residues: f_0 = 0, f_{i+1} = f_i - (P(n) mod q).
    // When q | P(n) the walk never leaves 0 and wcnt[j] is 1, so the
    // |F| = 1 case needs no branch of its own.
    unsigned int f = 0u;
    for (unsigned int i = 0; i < w; ++i) {
        for (unsigned int l = 0; l < 8u; ++l) {
            // 30*u + R[l] == f - base (mod q)  =>  u == (f - base - R[l])/30
            unsigned int rhs = f;
            unsigned int sub = blq[(j << 3) | l];    // (base+R[l]) mod q
            rhs = (rhs >= sub) ? (rhs - sub) : (rhs + q - sub);
            unsigned long long prod = (unsigned long long)rhs
                                    * (unsigned long long)iv;
            unsigned long long u = (unsigned long long)bmod(prod, q, mg);
            if (u < u_lo) {
                unsigned long long need = u_lo - u;
                u += ((need + (unsigned long long)q - 1ULL)
                      / (unsigned long long)q) * (unsigned long long)q;
            }
            for (; u < u_hi; u += (unsigned long long)q) {
                unsigned long long bit = (u << 3) | (unsigned long long)l;
                atomicOr(&bits[bit >> 5], 1u << (unsigned int)(bit & 31ULL));
            }
        }
        f = (f >= dq) ? (f - dq) : (f + q - dq);
    }
}

__global__ void compact(const unsigned int* __restrict__ bits,
                        unsigned long long* __restrict__ out,
                        unsigned int* __restrict__ count,
                        unsigned long long U,
                        unsigned int nword,
                        unsigned int cap,
                        const unsigned int* __restrict__ lanes)
{
    unsigned int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= nword) return;
    unsigned int alive = ~bits[i];
    while (alive) {
        unsigned int b = (unsigned int)(__ffs((int)alive) - 1);
        alive &= alive - 1u;
        unsigned long long bit = ((unsigned long long)i << 5) | b;
        unsigned long long u = bit >> 3;
        if (u >= U) continue;                    // tail of the last word
        unsigned int l = (unsigned int)(bit & 7ULL);
        unsigned int idx = atomicAdd(count, 1u);
        if (idx < cap) out[idx] = u * 30ULL + (unsigned long long)lanes[l];
    }
}

}
"""


class GpuEngine:
    """Bitmap sieve over (wheel period, lane), Barrett arithmetic."""

    def __init__(self, n, q2=Q2_DEFAULT, launch_u=LAUNCH_U):
        if cp is None:
            raise RuntimeError("cupy is not available; use --engine cpu")
        if not 7 <= q2 <= Q2_MAX:
            raise ValueError(f"q2 {q2} outside [7, {Q2_MAX}] (Barrett magics "
                             f"are exact for u32 moduli only)")
        self.n = int(n)
        self.q2 = int(q2)
        self.d = difference(n)
        self.launch_u = int(launch_u)
        cpu = CpuEngine(n, q2)                # the shared PARAMETERS, never
        self.primes = list(cpu.primes)        # the shared decisions: only the
        self.floor = cpu.floor                # prime list and the depth
        del cpu

        pr = np.array(self.primes, dtype=np.uint32)
        self.d_primes = cp.asarray(pr)
        self.d_magic = cp.asarray(barrett_magics(pr))
        dmod = np.array([self.d % int(q) for q in pr], dtype=np.uint32)
        self.d_dmodq = cp.asarray(dmod)
        self._w_host = np.where(dmod == 0, 1, self.n).astype(np.uint32)
        self.d_w = cp.asarray(self._w_host)
        self.d_inv30 = cp.asarray(
            np.array([pow(W0, -1, int(q)) for q in pr], dtype=np.uint32))
        self.d_lanes = cp.asarray(np.array(W0_RESIDUES, dtype=np.uint32))
        # for the vectorized per-launch (base + R[l]) mod q: q, 2^64 mod q
        # and the lanes as u64, so the whole reduction is numpy
        self._q64 = pr.astype(np.uint64)
        self._two64 = np.array([(1 << 64) % int(q) for q in pr],
                               dtype=np.uint64)
        self._lanes64 = np.array(W0_RESIDUES, dtype=np.uint64)

        # SUB_U, THREADS and the splits are read ONCE, here: the kernel
        # source bakes them in as literals (the shared array and the
        # per-thread word count are compile-time sizes), so everything
        # derived from them must be frozen with them or the task arrays
        # and the kernel could disagree.
        self._sub_u = int(SUB_U)
        self._threads = int(THREADS)
        self._qsplit = int(_qsplit())
        self._tabmax = min(int(TAB_MAX_Q), self._qsplit)
        sw = self._sub_u // 4
        if sw % self._threads:
            raise ValueError(f"SUB_U/4 = {sw} must be a multiple of "
                             f"THREADS = {self._threads}")
        src = (_SRC.replace("@SW@", str(sw))
                   .replace("@SUB_U@", str(self._sub_u))
                   .replace("@THREADS@", str(self._threads))
                   .replace("@K@", str(sw // self._threads)))
        mod = cp.RawModule(code=src, options=("-std=c++14",))
        self._mark = mod.get_function("mark")
        self._mark_sh = mod.get_function("mark_shared")
        self._build_tab = mod.get_function("build_tab")
        self._shbytes = self._sub_u          # SUB_U/4 words of 4 bytes
        if self._shbytes > 48 * 1024:        # past the static limit the
            self._mark_sh.max_dynamic_shared_size_bytes = self._shbytes
        self._compact = mod.get_function("compact")
        # the tabulated primes: q <= tabmax, one q-word pattern table each,
        # concatenated; rebuilt on the device at every launch (the pattern
        # depends on base mod q)
        self.d_inv4 = cp.asarray(
            np.array([pow(4, -1, int(q)) for q in pr], dtype=np.uint32))
        tsel = [(j, int(q)) for j, q in enumerate(self.primes)
                if q <= self._tabmax]
        self._ntab = len(tsel)
        if self._ntab:
            qs = np.array([q for _j, q in tsel], dtype=np.int64)
            offs = np.concatenate(([0], np.cumsum(qs[:-1]))).astype(np.uint32)
            self.d_tabj = cp.asarray(np.array([j for j, _q in tsel],
                                              dtype=np.uint32))
            self.d_toff = cp.asarray(offs)
            self.d_tab = cp.zeros(int(qs.sum()), dtype=cp.uint32)
        else:
            self.d_tabj = cp.zeros(1, dtype=cp.uint32)
            self.d_toff = cp.zeros(1, dtype=cp.uint32)
            self.d_tab = cp.zeros(1, dtype=cp.uint32)
        self._tasks = {}                      # launch_u -> (prime, chunk, cnt)
        self._sh = None                       # shared-path tasks (U-free)
        self._buf = {}

    # ---------------------------------------------------------------- setup
    @staticmethod
    def _chunked_tasks(chunks):
        """Flatten a per-prime chunk-count array into (task_prime,
        task_chunk) -- prime j appears chunks[j] times, its chunks numbered
        0..chunks[j]-1.  A zero means the prime has no task on this path."""
        n = len(chunks)
        task_prime = np.repeat(np.arange(n, dtype=np.uint32), chunks)
        starts = np.zeros(n, dtype=np.int64)
        np.cumsum(chunks[:-1], out=starts[1:])
        task_chunk = (np.arange(int(chunks.sum()), dtype=np.int64)
                      - np.repeat(starts, chunks)).astype(np.uint32)
        return task_prime, task_chunk

    def _task_arrays(self, U):
        """Global-path tasks for a launch of U wheel periods: the primes
        ABOVE the shared split, chunked to ~TARGET_MARKS bits each.

        Cached per U: the split depends only on the prime, its residue count
        and the launch size, none of which move inside a campaign.
        """
        if U in self._tasks:
            return self._tasks[U]
        q = np.array(self.primes, dtype=np.float64)
        w = self._w_host.astype(np.float64)
        marks = w * 8.0 * (U / q)             # bits this prime will set
        chunks = np.clip(np.ceil(marks / TARGET_MARKS), 1, MAX_CHUNKS)
        chunks = np.where(q > self._qsplit, chunks, 0).astype(np.uint32)
        task_prime, task_chunk = self._chunked_tasks(chunks)
        got = (cp.asarray(task_prime), cp.asarray(task_chunk),
               cp.asarray(np.maximum(chunks, 1)))
        self._tasks[U] = got
        return got

    def _task_arrays_sh(self):
        """Shared-path tasks: the primes AT OR BELOW the split, chunked to
        ~TARGET_MARKS_SH bits each -- of ONE BLOCK's SUB_U periods, because
        every block walks the same task list over its own sub-range."""
        if self._sh is not None:
            return self._sh
        q = np.array(self.primes, dtype=np.float64)
        w = self._w_host.astype(np.float64)
        marks = w * 8.0 * (self._sub_u / q)
        chunks = np.clip(np.ceil(marks / TARGET_MARKS_SH), 1, MAX_CHUNKS)
        chunks = np.where((q <= self._qsplit) & (q > self._tabmax),
                          chunks, 0).astype(np.uint32)
        task_prime, task_chunk = self._chunked_tasks(chunks)
        self._sh = (cp.asarray(task_prime), cp.asarray(task_chunk),
                    cp.asarray(np.maximum(chunks, 1)))
        return self._sh

    def _buffers(self, U):
        if U in self._buf:
            return self._buf[U]
        nword = int((U * 8 + 31) // 32)
        got = (cp.zeros(nword, dtype=cp.uint32),
               cp.zeros(SURV_CAP, dtype=cp.uint64),
               cp.zeros(1, dtype=cp.uint32))
        self._buf[U] = got
        return got

    def nbytes(self):
        arrays = [self.d_primes, self.d_magic, self.d_dmodq, self.d_w,
                  self.d_inv30, self.d_lanes, self.d_inv4, self.d_tabj,
                  self.d_toff, self.d_tab]
        for trio in self._tasks.values():
            arrays.extend(trio)
        if self._sh is not None:
            arrays.extend(self._sh)
        for trio in self._buf.values():
            arrays.extend(trio)
        return sum(int(a.nbytes) for a in arrays)

    # ---------------------------------------------------------------- sieve
    def survivors(self, base, span, launch_u=None):
        """Yield uint64 arrays of offsets o with base + o surviving, ascending.

        `base` must be a multiple of 30 and `span` a multiple of 30; the
        launcher aligns them.  Offsets are relative to `base`, so the pair
        (base, offset) spans the whole range with base a Python integer.
        """
        base, span = int(base), int(span)
        if base % W0 or span % W0:
            raise ValueError(f"base and span must be multiples of {W0}")
        if base < self.floor:
            raise ValueError(f"the engine refuses to sieve below {self.floor}")
        if base + span > P_CEIL:
            raise ValueError(f"p {base + span} is past the enforced ceiling "
                             f"{P_CEIL}")
        step_u = int(launch_u or self.launch_u)
        done = 0
        while done < span:
            u = min(step_u, (span - done) // W0)
            if u <= 0:
                break
            off = self._launch(base + done, u)
            if off.size:
                yield (off + done).astype(np.uint64)
            done += u * W0

    def _launch(self, base, U):
        bits, out, count = self._buffers(U)
        tp, tc, ch = self._task_arrays(U)
        stp, stc, sch = self._task_arrays_sh()
        count.fill(0)
        # (base + R[l]) mod q for every (prime, lane), all in numpy: base is
        # an arbitrary-precision int, so it is split hi*2^64 + lo and reduced
        # with the precomputed 2^64 mod q -- every intermediate fits u64.
        hi, lo = divmod(int(base), 1 << 64)
        bmq = (np.uint64(hi) % self._q64 * self._two64
               + np.uint64(lo) % self._q64) % self._q64
        blq = (bmq[:, None] + self._lanes64[None, :]) % self._q64[:, None]
        d_blq = cp.asarray(blq.astype(np.uint32).ravel())
        nword = int(bits.size)
        threads = self._threads
        ntask_sh = int(stp.size)
        if self._ntab:
            self.d_tab.fill(0)
            self._build_tab((int((self._ntab + 63) // 64),), (64,),
                            (self.d_tabj, self.d_toff, self.d_primes,
                             self.d_magic, self.d_w, self.d_dmodq,
                             self.d_inv30, self.d_inv4, d_blq, self.d_tab,
                             np.uint32(self._ntab)))
        if ntask_sh or self._ntab:
            # phase B's stores cover every word below nword, so no fill is
            # needed; the global path then ORs on top.
            nblk = (U + self._sub_u - 1) // self._sub_u
            self._mark_sh((int(nblk),), (threads,),
                          (stp, stc, sch, self.d_primes, self.d_magic,
                           self.d_w, self.d_dmodq, self.d_inv30, d_blq,
                           self.d_tabj, self.d_toff, self.d_tab,
                           bits, np.uint64(U),
                           np.uint32(nword), np.uint32(ntask_sh),
                           np.uint32(self._ntab)),
                          shared_mem=self._shbytes)
        else:
            bits.fill(0)
        ntask = int(tp.size)
        if ntask:
            self._mark((int((ntask + threads - 1) // threads),), (threads,),
                       (tp, tc, ch, self.d_primes, self.d_magic, self.d_w,
                        self.d_dmodq, self.d_inv30, d_blq,
                        bits, np.uint64(U), np.uint32(ntask)))
        self._compact((int((nword + threads - 1) // threads),), (threads,),
                      (bits, out, count, np.uint64(U), np.uint32(nword),
                       np.uint32(SURV_CAP), self.d_lanes))
        got = int(count[0])
        if got > SURV_CAP:
            raise RuntimeError(
                f"{got} survivors in one launch exceeds SURV_CAP {SURV_CAP}: "
                f"the sieve is not sieving, not the window being busy")
        # np.sort on the host: the device sort of a few thousand survivors
        # was ~4 ms of pure launch overhead, a third of the whole launch
        res = np.sort(cp.asnumpy(out[:got]))
        return res.astype(np.uint64)

    def survives(self, p):
        """One-candidate membership -- delegated to nothing: the same walk
        the kernel does, in Python, for the verification legs."""
        p = int(p)
        if any(p % q == 0 for q in (2, 3, 5)):
            return False
        for q in self.primes:
            f, dq, pm = 0, self.d % q, p % q
            for _ in range(self.n if dq else 1):
                if pm == f:
                    return False
                f = f - dq if f >= dq else f + q - dq
        return True

    # ------------------------------------------------------------- classify
    def chain_depth(self, p, cap=None):
        """Delegated to the CPU engine's chain: classification is host work
        in this project (the survivors are far too rare to be worth a
        device kernel), so there is one implementation of it, in one place,
        and this engine does not pretend to have a second."""
        if not hasattr(self, "_cls"):
            self._cls = CpuEngine(self.n, self.q2)
        return self._cls.chain_depth(p, cap)

    def hunt(self, base, span, min_depth=None):
        want = self.n if min_depth is None else int(min_depth)
        out = []
        for chunk in self.survivors(base, span):
            for o in chunk.tolist():
                p = int(base) + int(o)
                dep = self.chain_depth(p)
                if dep >= want:
                    out.append((p, dep))
        return out


# --------------------------------- gates -----------------------------------

def _down(p):
    return int(p) - int(p) % W0


def _up(p):
    return _down(int(p) + W0 - 1)


def _stream(eng, base, span):
    parts = [c for c in eng.survivors(base, span)]
    return (np.concatenate(parts) if parts
            else np.zeros(0, dtype=np.uint64))


# The gate windows, sized by MEASUREMENT rather than by guess.  Survivor
# density here is brutal -- at n = 16 and a 2048-deep sieve it is 4e-6, and
# at the production depth it is 1e-8 -- so a window picked for looking
# reasonable is an EMPTY window, and an empty parity check passes while
# proving nothing.  Every entry below was measured to hold 100-1000
# survivors before it was written down.
#
#     (n, q2, base, span)                             measured survivors
_W_MID = (13, 2048, _down(10**6), _down(2 * 10**7))              # 243
_W_PROD = (16, 2048, _down(10**9), _down(5 * 10**7))             # 202
_W_HIGH = (8, 4096, _down(4 * 10**13), _down(3 * 10**6))         # 194
_W_CEIL = (5, 2048, _down(P_CEIL - 3 * 10**6), _down(10**6))     # 948
_W_DEEP = (5, 1 << 18, _down(4 * 10**13), _down(2 * 10**6))      # 135


def g6_parity_with_cpu():
    """GPU stream == CPU stream, bit for bit, on POPULATED windows at
    several heights INCLUDING the enforced ceiling.

    An empty-vs-empty comparison is vacuous and does not count, so every
    window is checked for population first -- and the ceiling window is the
    one that matters most, because it is the only place the (base, offset)
    representation is exercised at a base that does not fit a machine word.
    """
    total = 0
    for n, q2, base, span in (_W_MID, _W_PROD, _W_HIGH, _W_CEIL):
        gpu = GpuEngine(n, q2, launch_u=1 << 16)
        cpu = CpuEngine(n, q2)
        g, c = _stream(gpu, base, span), _stream(cpu, base, span)
        if c.size < 50:
            return False, (f"G6 FAIL: n={n} window at {base:.3g} holds only "
                           f"{c.size} survivors -- too thin to mean anything")
        if g.size != c.size or not np.array_equal(g, c):
            bad = np.setxor1d(g, c)[:4]
            return False, (f"G6 FAIL: n={n} base={base} span={span}: "
                           f"{g.size} GPU vs {c.size} CPU, first differences "
                           f"{bad.tolist()}")
        total += int(c.size)
    return True, (f"G6 ok: GPU stream == CPU stream bit for bit on 4 "
                  f"populated windows ({total} survivors) at p ~ 1e6, 1e9, "
                  f"4e13 and the enforced ceiling 1e26")


def g7_planted_fake():
    """The comparator must CATCH a plant.  A gate that cannot fail on
    corrupted data is not evidence that it passes on good data."""
    n, q2, base, span = _W_MID
    g = _stream(GpuEngine(n, q2, launch_u=1 << 16), base, span)
    c = _stream(CpuEngine(n, q2), base, span)
    if g.size < 8:
        return False, "G7 FAIL: window too small to plant into"
    planted = g.copy()
    planted[len(planted) // 2] += W0                # a survivor that is not
    if np.array_equal(planted, g):
        return False, "G7 FAIL: the plant did not change the stream"
    if np.array_equal(planted, c):
        return False, "G7 FAIL: the comparator accepted the planted stream"
    if np.array_equal(np.delete(g, 3), c):
        return False, "G7 FAIL: the comparator accepted a truncated stream"
    if np.array_equal(np.append(g, g[-1] + W0), c):
        return False, "G7 FAIL: the comparator accepted an extended stream"
    return True, ("G7 ok: the parity comparator rejects a corrupted "
                  "survivor, a dropped one and an added one")


def g8_gpu_rediscovers_knowns():
    """The production stream must organically rediscover a known value.

    a(13) is found from the engine floor upward as a FIRST occurrence -- a
    least-claim drill, not a mere hit: 3.7e9 of p-line swept contiguously,
    with the known term coming out as the SMALLEST p the stream accepts.
    This is the canary that says the stream is honest before it is allowed
    to report anything that is not known.
    """
    n = 13
    gpu = GpuEngine(n, q2=1 << 12)
    base = _up(gpu.floor)
    span = _up(KNOWN[n] + 1) - base
    hits = gpu.hunt(base, span)
    firsts = [p for p, dep in hits if dep >= n]
    if not firsts or min(firsts) != KNOWN[n]:
        return False, (f"G8 FAIL: the GPU stream's least full chain at n={n} "
                       f"is {min(firsts) if firsts else None}, expected "
                       f"{KNOWN[n]}")
    return True, (f"G8 ok: the GPU stream rediscovered a({n}) = {KNOWN[n]} "
                  f"end-to-end over {span:.3g} of contiguous p-line from the "
                  f"floor, as a FIRST occurrence")


def g13_slicing_independence():
    """A split sweep must equal the unsplit one, and NO decomposition knob
    may change what is marked.

    Four independent slicings: the window cut into launches of different
    sizes; the shared-path chunk target; the sub-segment size SUB_U --
    which also MOVES THE SPLIT, so primes cross from the shared path to
    the global one and the partition itself is drilled; and the
    global-path chunk target, on an engine whose global path is populated.
    Chunking is what keeps a single thread from owning the segment, and it
    would be a very quiet bug if it also moved a boundary.
    """
    global TARGET_MARKS, TARGET_MARKS_SH, SUB_U, QSPLIT_DIV, TAB_MAX_Q
    n, q2, base, span = _W_PROD
    big = GpuEngine(n, q2, launch_u=1 << 21)
    whole = _stream(big, base, span)
    split = _stream(GpuEngine(n, q2, launch_u=1 << 15), base, span)
    if whole.size < 50:
        return False, "G13 FAIL: window under-populated (vacuous)"
    if not np.array_equal(whole, split):
        return False, ("G13 FAIL: a window swept in many launches != the "
                       "same window swept in few")
    # at the production defaults every prime at this depth is tabulated,
    # so to drill the shared-ATOMIC path the table cutoff is pushed down
    # first -- which is itself the partition drill between the two paths
    saved_sh, saved_tab = TARGET_MARKS_SH, TAB_MAX_Q
    try:
        TAB_MAX_Q = 64                       # most primes leave the tables
        engc = GpuEngine(n, q2, launch_u=1 << 21)    # for the atomic path
        coarse = _stream(engc, base, span)
        ntask_coarse = int(engc._task_arrays_sh()[0].size)
        ntab_small = engc._ntab
        TARGET_MARKS_SH = 64                 # ...which is then re-chunked
        eng = GpuEngine(n, q2, launch_u=1 << 21)
        fine = _stream(eng, base, span)
        ntask_fine = int(eng._task_arrays_sh()[0].size)
    finally:
        TARGET_MARKS_SH, TAB_MAX_Q = saved_sh, saved_tab
    if ntab_small >= big._ntab or ntask_coarse == 0:
        return False, ("G13 FAIL: shrinking TAB_MAX_Q did not move primes "
                       "onto the atomic path, so the drill proved nothing")
    if not np.array_equal(whole, coarse):
        return False, ("G13 FAIL: moving primes between the table path and "
                       "the atomic path changed the survivor stream")
    if ntask_fine <= ntask_coarse:
        return False, ("G13 FAIL: the shared chunk target did not change "
                       "the task count, so the drill proved nothing")
    if not np.array_equal(whole, fine):
        return False, ("G13 FAIL: changing the shared chunk target changed "
                       "the survivor stream -- chunking is supposed to move "
                       "work between threads, not move a boundary")
    saved_su, saved_t, saved_dv = SUB_U, TARGET_MARKS, QSPLIT_DIV
    try:
        SUB_U = 1 << 13                      # 8x smaller blocks, AND the
        QSPLIT_DIV = 8                       # split drops to 1024, pushing
        eng2 = GpuEngine(n, q2, launch_u=1 << 21)   # primes in (1024, 2048]
        moved = int(eng2._task_arrays(1 << 21)[0].size)  # onto the global
        resub = _stream(eng2, base, span)    # path at this depth
        TARGET_MARKS = 64
        eng3 = GpuEngine(n, q2, launch_u=1 << 21)
        gfine = _stream(eng3, base, span)
        ntask_g = int(eng3._task_arrays(1 << 21)[0].size)
    finally:
        SUB_U, TARGET_MARKS, QSPLIT_DIV = saved_su, saved_t, saved_dv
    if moved == 0:
        return False, ("G13 FAIL: shrinking SUB_U left the global path "
                       "empty, so the partition drill proved nothing")
    if not np.array_equal(whole, resub):
        return False, ("G13 FAIL: changing SUB_U changed the survivor "
                       "stream -- the shared/global partition moved a "
                       "boundary")
    if ntask_g <= moved:
        return False, ("G13 FAIL: the global chunk target did not change "
                       "the task count, so the drill proved nothing")
    if not np.array_equal(whole, gfine):
        return False, ("G13 FAIL: changing the global chunk target changed "
                       "the survivor stream")
    return True, (f"G13 ok: {whole.size} survivors identical whether the "
                  f"window is one launch or 64; identical with {ntab_small} "
                  f"pattern tables instead of {big._ntab}; identical with "
                  f"{ntask_fine} shared tasks instead of {ntask_coarse}; "
                  f"identical with SUB_U 8k moving {moved} tasks onto the "
                  f"global path; and identical again at {ntask_g} global "
                  f"tasks")


def g14_kernel_matches_bigint():
    """Kill decisions == big-integer divisibility of the ACTUAL values, with
    no engine on the other side.

    The parity gate compares two implementations; this one compares the
    engine to the definition.  Every survivor must have no value divisible
    by any sieve prime, and a sample of the killed must have one.
    """
    n, q2, base, span = _W_PROD
    eng = GpuEngine(n, q2, launch_u=1 << 21)
    surv = set(int(o) for c in eng.survivors(base, span) for o in c.tolist())
    if len(surv) < 50:
        return False, "G14 FAIL: window under-populated (vacuous)"
    d = difference(n)
    primes = list(eng.primes)
    for o in sorted(surv)[:64]:
        p = base + o
        for q in primes:
            for j in range(n):
                if (p + j * d) % q == 0:
                    return False, (f"G14 FAIL: survivor p = {p} has "
                                   f"p + {j}*P({n}) divisible by {q}")
    killed, checked = 0, 0
    for o in range(0, span, W0):
        for r in W0_RESIDUES:
            oo = o + r
            if oo >= span or oo in surv:
                continue
            p = base + oo
            checked += 1
            if any((p + j * d) % q == 0 for q in primes for j in range(n)):
                killed += 1
            if checked >= 256:
                break
        if checked >= 256:
            break
    if killed != checked or checked == 0:
        return False, (f"G14 FAIL: {checked - killed} of {checked} killed "
                       f"candidates had no small factor at all")
    return True, (f"G14 ok: {min(64, len(surv))} survivors have no value "
                  f"divisible by any of {len(primes)} sieve primes, and all "
                  f"{checked} sampled kills really do -- checked in big "
                  f"integers against the definition")


def g16_deep_sieve_arithmetic():
    """The kernel's arithmetic stays exact ABOVE q = 2^16.

    The residue walk and the Barrett reduction both run in fixed-width
    registers, and the sibling project in this repo shipped a kill-bit
    table that was silently wrong above q = 2^16 for months because every
    gate ran at the default depth.  This one runs deep on purpose.
    """
    n, q2, base, span = _W_DEEP
    gpu = GpuEngine(n, q2, launch_u=1 << 17)
    cpu = CpuEngine(n, q2)
    g, c = _stream(gpu, base, span), _stream(cpu, base, span)
    if c.size < 50:
        return False, f"G16 FAIL: deep window holds {c.size} -- vacuous"
    if not np.array_equal(g, c):
        return False, (f"G16 FAIL: at q2 = 2^18 the engines disagree "
                       f"({g.size} GPU vs {c.size} CPU)")
    # and the deep primes really are doing something: shortening the sieve
    # to 2^16 must let survivors through that the deep one killed
    shallow = _stream(CpuEngine(n, 1 << 16), base, span)
    extra = np.setdiff1d(shallow, c)
    if extra.size == 0:
        return False, ("G16 FAIL: the primes between 2^16 and 2^18 killed "
                       "nothing in this window, so the drill proved nothing")
    return True, (f"G16 ok: GPU == CPU at sieve depth 2^18 ({c.size} "
                  f"survivors), and the primes past 2^16 -- where fixed-width "
                  f"intermediates bite -- killed {extra.size} candidates a "
                  f"2^16 sieve let through")


GATES = [g6_parity_with_cpu, g7_planted_fake, g13_slicing_independence,
         g14_kernel_matches_bigint, g16_deep_sieve_arithmetic,
         g8_gpu_rediscovers_knowns]

if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
