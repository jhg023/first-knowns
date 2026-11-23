# residue_gpu.py -- THE GPU ENGINE for the power-residue ladders
# (A002226, A002227, A002228, A060363, A060364).  Engine v2.
#
# The production engine.  It implements the sweep of residue_search.py a
# second time, in CUDA through CuPy, with 64-bit Montgomery arithmetic where
# the CPU engine uses Python integers and `%`; neither file calls the other
# for a result (CLAUDE.md rule 3 -- the parity gates below import the CPU
# engine to COMPARE, which is the point of having two).
#
# THE LINE (residue_search.py): a family is a power; its candidates are
# N = 2*power*j + 1, indexed by j.  There is no sieve for the property
# itself: "q is a residue of the power mod p" is a congruence on a prime of
# the cyclotomic field above p, not on p (README).  So every candidate that
# might be prime is tested:
#
#   1. SIEVE (rl_sieve, one thread per 256 candidates, in registers).  A
#      candidate with a prime factor among the first SIEVE_PRIMES odd primes
#      is composite and is dropped: the primes below 64 by a rotated 64-bit
#      pattern per word, the rest by marking their multiples in the block.
#      A sieve prime q is used only in launches that start above q, so a
#      candidate that IS q is never dropped.  The survivors are appended to
#      one list (an atomic counter reserves each block's slots).
#   2. THE FIRST TEST (rl_test2, two sieve survivors per thread):
#      2^j == +-1 (mod N).  Since (N-1)/power = 2j, for a prime N this is
#      2^((N-1)/power) == 1, "2 is a residue" (Euler's criterion; a square
#      root of 1 mod a prime is +-1).  A prime fails it four times in five
#      (power 5) to sixteen in seventeen (power 17), and a composite fails
#      it unless it is a base-2 pseudoprime of a special kind, since it
#      forces 2^(N-1) == 1.  This one modular power is both the
#      compositeness test and the first residue test, which is why there is
#      no separate primality pass.  Those that pass are appended to a list.
#
#      The kernel computes 2^(-j) instead, which is +-1 exactly when 2^j
#      is (the set {1, -1} is closed under inversion mod any odd N, prime
#      or not), because that power starts five squarings in and needs no
#      remainder: with t = j + 64, k = bitlength(t) - 6, h = ceil(t / 2^k)
#      (32 to 64 at height) and b = h*2^k - t (0 <= b < 2^k), the word
#      2^(64-h) already IS 2^64 * 2^(-h) mod N -- the Montgomery form of
#      2^(-h) -- and k Montgomery squarings, each followed by a doubling
#      where the matching bit of b is set, take the exponent -h to
#      -(h*2^k - b) = -t.  The Montgomery form of 2^(-t) is 2^64 * 2^(-j-64)
#      = 2^(-j) itself, so the result is compared with 1 and N - 1 as it
#      stands.  (The identity, and the idea, are RSL-005 of the Codex
#      review of 2026-11-21; codex-reviews/.)
#   3. THE RUN, in stages, each appending the candidates that pass to a
#      list for the next -- a warp whose threads leave a loop at different
#      bases idles until the last one is done, and one base per kernel has
#      no such loop: rl_base3 (two candidates per thread) keeps those with
#      3^j == +-1; rl_run, restricted to the base 5, keeps those that pass
#      it; rl_run then reads 7, 11, ... until one fails; the count of
#      leading passes is the run.  Candidates whose run reaches the floor
#      are appended to the output.  A stage is used only while it is below
#      the floor (a candidate that fails the base 3 has run 1, and at floor
#      1 it must be reported), so at floor 1 there are none and at floor 2
#      one.
#
# LAZY ARITHMETIC.  While every candidate of a launch is below 2^60
# (LAZY_BELOW), the squarings of the first test and of rl_base3 skip the
# conditional subtraction: a Montgomery square of a < 4N is returned as
# hi - mh + N, which lies in (0, 2N) because hi < 16 N^2 / 2^64 < N and
# mh < N; a doubling of that is below 4N again, and three times it is
# below 6N, brought under 4N by one conditional subtraction.  The residue
# is made canonical once, after the last squaring.  A launch that reaches
# 2^60 uses the same kernels with every residue kept in [0, N).
#
# The device hands back every candidate whose run is at least the floor it
# was asked for, as (index offset, run), sorted on the host.  THE GPU
# PROPOSES, THE HOST VERIFIES: `stream` keeps the ones huntlib's
# deterministic Miller-Rabin proves prime, which is what removes the rare
# composite that passes.
#
# NUMERIC CEILING: p < 2^63 (P_CEIL), enforced.  Montgomery reduction with
# R = 2^64 needs N odd and N < 2^63 so that a sum of two residues fits a
# word; every intermediate is stated in the kernels' comments.  The README
# says why 2^63 and not huntlib's 10^40: this sweep has no sieve for the
# property, its cost is linear in p, and 2^63 is months of device time
# away on every family.

import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from huntlib import primes as hprimes                         # noqa: E402

ENGINE = "v2"
POWERS = (5, 7, 11, 13, 17)
P_CEIL = 2 ** 63
RUN_CAP = 40
SIEVE_PRIMES = 512          # sieve primes per family (OPTIMIZATION_LOG.md round 1)
WORDS = 1 << 24             # 64-candidate words per launch (round 3)
LAZY_BELOW = 1 << 60        # launches below this skip the conditional
#                             subtractions (see LAZY ARITHMETIC above)
RUN_STAGES = 2              # bases tested one per kernel before rl_run
MAX_WORDS = 1 << 25         # a bit offset must fit 31 bits
BLOCK_WORDS = 4             # words per sieve thread (256 candidates)
MAX_SIEVE_PRIME = 1 << 20   # block offsets and marks stay in 32 bits

_SRC = r"""
typedef unsigned long long u64;
typedef unsigned int u32;
#define BW 4

// Montgomery product a*b/2^64 mod n, for odd n < 2^63 and a, b < n, with
// ninv = n^-1 mod 2^64.  T = a*b = hi*2^64 + lo; m = lo*ninv, so m*n == lo
// (mod 2^64) and (T - m*n)/2^64 = hi - mh EXACTLY, mh the high word of m*n.
// hi < n^2/2^64 < n/2 and mh < n, so the difference lies in (-n, n) and one
// conditional add of n lands it in [0, n).
__device__ __forceinline__ u64 rl_montmul(u64 a, u64 b, u64 n, u64 ninv)
{
    u64 lo = a * b;
    u64 hi = __umul64hi(a, b);
    u64 mh = __umul64hi(lo * ninv, n);
    u64 t = hi - mh;
    return hi < mh ? t + n : t;
}

// n^-1 mod 2^64 by Newton: n*n == 1 (mod 8) gives 3 bits, five steps 96.
__device__ __forceinline__ u64 rl_ninv(u64 n)
{
    u64 x = n;
    x *= 2ULL - n * x; x *= 2ULL - n * x; x *= 2ULL - n * x;
    x *= 2ULL - n * x; x *= 2ULL - n * x;
    return x;
}

// One thread sieves BW = 4 words (256 candidates), all in registers, and
// appends the survivors' bit offsets to cand.  q, mg = floor(2^32/q), r0 =
// offset of q's first multiple in the launch; the first ntiny primes are
// below 64 and use the rotated patterns pat[patoff[i] + s] (bits == s mod
// q) with s stepping by 64 mod q from word to word; a larger prime has at
// most four multiples among 256 candidates and marks each.
extern "C" __global__
void rl_sieve(const u32* q, const u32* mg, const u32* r0, const u64* pat,
              const int* patoff, int ntiny, int nprime, u32* cand,
              u32* count, u32 cap, int words)
{
    int blk = blockIdx.x * blockDim.x + threadIdx.x;
    int w0 = blk * BW;
    if (w0 >= words) return;
    u64 d0 = 0ULL, d1 = 0ULL, d2 = 0ULL, d3 = 0ULL;
    u32 x = (u32)blk << 8;               // offset of this block's first bit
    for (int i = 0; i < nprime; ++i) {
        u32 qq = q[i];
        u32 u = x - qq * __umulhi(x, mg[i]);      // x mod qq, or that + qq
        if (u >= qq) u -= qq;
        u32 r = r0[i];
        u32 s = r >= u ? r - u : r + qq - u;      // first dead bit, < qq
        if (i < ntiny) {
            const u64* pt = pat + patoff[i];
            u32 st = 64u % qq;
            d0 |= pt[s]; s = s >= st ? s - st : s + qq - st;
            d1 |= pt[s]; s = s >= st ? s - st : s + qq - st;
            d2 |= pt[s]; s = s >= st ? s - st : s + qq - st;
            d3 |= pt[s];
        } else {
            for (; s < 256u; s += qq) {
                u64 bit = 1ULL << (s & 63u);
                u32 wi = s >> 6;
                d0 |= wi == 0u ? bit : 0ULL;
                d1 |= wi == 1u ? bit : 0ULL;
                d2 |= wi == 2u ? bit : 0ULL;
                d3 |= wi == 3u ? bit : 0ULL;
            }
        }
    }
    u64 m[BW];
    m[0] = ~d0;
    m[1] = w0 + 1 < words ? ~d1 : 0ULL;  // past the launch: nothing
    m[2] = w0 + 2 < words ? ~d2 : 0ULL;
    m[3] = w0 + 3 < words ? ~d3 : 0ULL;
    u32 total = (u32)(__popcll(m[0]) + __popcll(m[1]) + __popcll(m[2])
                      + __popcll(m[3]));
    if (!total) return;
    u32 o = atomicAdd(count, total);
    if (o + total > cap) return;         // the host sees count > cap
    for (int w = 0; w < BW; ++w) {
        u64 mm = m[w];
        u32 base = x + ((u32)w << 6);
        while (mm) {
            cand[o++] = base + (u32)(__ffsll((long long)mm) - 1);
            mm &= mm - 1ULL;
        }
    }
}

// a*a/2^64 mod n for odd n < 2^63, with ninv = n^-1 mod 2^64 (rl_montmul's
// derivation with b = a).  LAZY = 0: a < n, result in [0, n).  LAZY = 1,
// which needs n < 2^60 and a < 4n: the result is hi - mh + n without the
// conditional subtraction; hi <= a^2/2^64 < 16n^2/2^64 < n and mh < n, so
// it lies in (0, 2n) and is congruent to a*a/2^64.
template <int LAZY>
__device__ __forceinline__ u64 rl_sqr(u64 a, u64 n, u64 ninv)
{
    u64 lo = a * a;
    u64 hi = __umul64hi(a, a);
    u64 mh = __umul64hi(lo * ninv, n);
    if (LAZY) return hi - mh + n;
    u64 t = hi - mh;
    return hi < mh ? t + n : t;
}

// 2^64 * 2^-h mod n in [0, n), for 1 <= h <= 64: the word 2^(64-h),
// reduced where n is that small (never, once n > 2^32 and h >= 32)
__device__ __forceinline__ u64 rl_seed(u64 h, u64 n)
{
    u64 x = 1ULL << (64ULL - h);
    if (x >= n) x %= n;
    return x;
}

// THE FIRST TEST.  Append cand[i] to pass when 2^j == +-1 mod N, N =
// step*j + 1, j = j0 + cand[i]; decided as 2^-j == +-1.  NL candidates per
// thread, their squarings interleaved: a modular power is one chain of
// dependent wide multiplies, and a warp that carries a single chain idles
// while each multiply completes (OPTIMIZATION_LOG.md rounds 2 and 3).
//
// With t = j + 64 and one k for the thread, k = bitlength(largest t) - 6
// >= 1: h = ceil(t / 2^k) is in [1, 64] for every lane (32 to 64 for the
// largest t), b = h*2^k - t is in [0, 2^k), and x = 2^(64-h) = 2^64 * 2^-h
// (mod N).  A Montgomery squaring takes 2^64 * 2^-e to 2^64 * 2^-2e and a
// doubling to 2^64 * 2^-(e-1), so reading the k bits of b from the top
// leaves e = h*2^k - b = t: x = 2^64 * 2^-(j+64) = 2^-j (mod N), compared
// with 1 and N - 1 directly.  A lane with a shorter t simply has a smaller
// h; no lane is padded.
#define NL 2
template <int LAZY>
__device__ __forceinline__
void rl_test2_body(const u32* cand, u32 ncand, u64 j0, u64 step, u32* pass,
                   u32* count)
{
    u32 i = (blockIdx.x * blockDim.x + threadIdx.x) * NL;
    if (i >= ncand) return;
    u32 c[NL]; u64 n[NL], iv[NL], t[NL], x[NL], bb[NL];
    u64 tm = 0ULL;
    #pragma unroll
    for (int l = 0; l < NL; ++l) {
        c[l] = cand[i + l < ncand ? i + l : i];   // a lane past the end
        u64 j = j0 + c[l];                        // repeats lane 0, unreported
        n[l] = j * step + 1ULL;
        iv[l] = rl_ninv(n[l]);
        t[l] = j + 64ULL;
        tm = t[l] > tm ? t[l] : tm;
    }
    int k = 58 - __clzll((long long)tm);          // bitlength - 6; t >= 65
    u64 rnd = (1ULL << k) - 1ULL;
    #pragma unroll
    for (int l = 0; l < NL; ++l) {
        u64 h = (t[l] + rnd) >> k;
        bb[l] = (h << k) - t[l];
        x[l] = rl_seed(h, n[l]);
    }
    for (int b = k - 1; b >= 0; --b) {
        #pragma unroll
        for (int l = 0; l < NL; ++l) x[l] = rl_sqr<LAZY>(x[l], n[l], iv[l]);
        #pragma unroll
        for (int l = 0; l < NL; ++l) {
            if (LAZY) x[l] <<= (bb[l] >> b) & 1ULL;        // < 4n
            else if ((bb[l] >> b) & 1ULL) {
                x[l] <<= 1; if (x[l] >= n[l]) x[l] -= n[l];
            }
        }
    }
    #pragma unroll
    for (int l = 0; l < NL; ++l) {
        u64 y = x[l];
        if (LAZY) {                               // y < 4n: make it canonical
            if (y >= (n[l] << 1)) y -= n[l] << 1;
            if (y >= n[l]) y -= n[l];
        }
        if ((l == 0 || i + l < ncand) && (y == 1ULL || y == n[l] - 1ULL))
            pass[atomicAdd(count, 1u)] = c[l];
    }
}

extern "C" __global__
void rl_test2(const u32* cand, u32 ncand, u64 j0, u64 step, u32* pass,
              u32* count)
{ rl_test2_body<0>(cand, ncand, j0, step, pass, count); }

extern "C" __global__
void rl_test2_lazy(const u32* cand, u32 ncand, u64 j0, u64 step, u32* pass,
                   u32* count)
{ rl_test2_body<1>(cand, ncand, j0, step, pass, count); }

// THE BASE 3.  Append in[i] to out when 3^j == +-1 mod N; two candidates
// per thread.  Montgomery form throughout: o = 2^64 mod N is 1, m = 3o is
// 3, and a multiplication by 3 is two additions.  LAZY as in rl_sqr: after
// a squaring x < 2n, 3x < 6n, and one conditional subtraction of 4n leaves
// x < 4n.  A shorter exponent starts at 1, whose squares stay 1 until its
// own leading bit.
template <int LAZY>
__device__ __forceinline__
void rl_base3_body(const u32* in, u32 nin, u64 j0, u64 step, u32* out,
                   u32* count)
{
    u32 i = (blockIdx.x * blockDim.x + threadIdx.x) << 1;
    if (i >= nin) return;
    bool two = i + 1u < nin;
    u32 ca = in[i], cb = two ? in[i + 1u] : ca;
    u64 ja = j0 + ca, jb = j0 + cb;
    u64 na = ja * step + 1ULL, nb = jb * step + 1ULL;
    u64 ia = rl_ninv(na), ib = rl_ninv(nb);
    u64 oa = (0ULL - na) % na, ob = (0ULL - nb) % nb;
    u64 ma = oa << 1; if (ma >= na) ma -= na; ma += oa; if (ma >= na) ma -= na;
    u64 mb = ob << 1; if (mb >= nb) mb -= nb; mb += ob; if (mb >= nb) mb -= nb;
    int ta = 63 - __clzll((long long)ja), tb = 63 - __clzll((long long)jb);
    int top = ta > tb ? ta : tb;
    u64 xa = ta == top ? ma : oa, xb = tb == top ? mb : ob;
    u64 fa = na << 2, fb = nb << 2;               // used only when LAZY
    for (int b = top - 1; b >= 0; --b) {
        xa = rl_sqr<LAZY>(xa, na, ia);
        xb = rl_sqr<LAZY>(xb, nb, ib);
        if (LAZY) {
            u64 ya = xa + (xa << 1), yb = xb + (xb << 1);     // < 6n
            ya = ya >= fa ? ya - fa : ya;                     // < 4n
            yb = yb >= fb ? yb - fb : yb;
            xa = ((ja >> b) & 1ULL) ? ya : xa;
            xb = ((jb >> b) & 1ULL) ? yb : xb;
        } else {
            if ((ja >> b) & 1ULL) {
                u64 y = xa << 1; if (y >= na) y -= na;
                y += xa; if (y >= na) y -= na; xa = y;
            }
            if ((jb >> b) & 1ULL) {
                u64 y = xb << 1; if (y >= nb) y -= nb;
                y += xb; if (y >= nb) y -= nb; xb = y;
            }
        }
    }
    if (LAZY) {
        if (xa >= (na << 1)) xa -= na << 1;
        if (xa >= na) xa -= na;
        if (xb >= (nb << 1)) xb -= nb << 1;
        if (xb >= nb) xb -= nb;
    }
    if (xa == oa || xa == na - oa) out[atomicAdd(count, 1u)] = ca;
    if (two && (xb == ob || xb == nb - ob)) out[atomicAdd(count, 1u)] = cb;
}

extern "C" __global__
void rl_base3(const u32* in, u32 nin, u64 j0, u64 step, u32* out, u32* count)
{ rl_base3_body<0>(in, nin, j0, step, out, count); }

extern "C" __global__
void rl_base3_lazy(const u32* in, u32 nin, u64 j0, u64 step, u32* out,
                   u32* count)
{ rl_base3_body<1>(in, nin, j0, step, out, count); }

// THE RUN from a known start.  Every candidate of `pass` has run >= tstart
// (2 and the tstart - 1 bases after it passed).  Read on against pr[tstart],
// ..., pr[tend - 1]: the run is tstart plus the number of those, in order,
// with pr[t]^j == +-1 mod N (a prime that is 0 mod N ends the run); append
// (cand, run) when run >= floor.  With tend = tstart + 1 = floor it is a
// one-base stage: the candidates that pass pr[tstart].
extern "C" __global__
void rl_run(const u32* pass, u32 npass, u64 j0, u64 step, const u32* pr,
            int tstart, int tend, int floor, u32* oidx, unsigned char* orun,
            u32* count)
{
    u32 i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= npass) return;
    u64 j = j0 + pass[i];
    u64 n = j * step + 1ULL;
    u64 ninv = rl_ninv(n);
    u64 one = (0ULL - n) % n;            // 2^64 mod n: 1 in Montgomery form
    u64 mone = n - one;
    int top = 62 - __clzll((long long)j);
    int r = tstart;
    for (int t = tstart; t < tend; ++t) {
        u64 base = pr[t];
        if (base >= n) base %= n;
        if (base == 0ULL) break;
        u64 xb = 0ULL;                   // base in Montgomery form
        for (int b = 7; b >= 0; --b) {
            xb <<= 1; if (xb >= n) xb -= n;
            if ((base >> b) & 1ULL) { xb += one; if (xb >= n) xb -= n; }
        }
        u64 x = xb;
        for (int b = top; b >= 0; --b) {
            x = rl_montmul(x, x, n, ninv);
            if ((j >> b) & 1ULL) x = rl_montmul(x, xb, n, ninv);
        }
        if (x != one && x != mone) break;
        ++r;
    }
    if (r >= floor) {
        u32 o = atomicAdd(count, 1u);
        oidx[o] = pass[i];
        orun[o] = (unsigned char)r;
    }
}
"""

_cp = None
_mod = None
_engines = {}


def available():
    """True iff CuPy imports and a CUDA device answers."""
    global _cp
    if _cp is not None:
        return True
    try:
        import cupy as cp
        cp.cuda.Device(0).use()
        cp.zeros(1).sum()
    except Exception:
        return False
    _cp = cp
    return True


def _module():
    global _mod
    if _mod is None:
        _mod = _cp.RawModule(code=_SRC, options=("--std=c++14",))
    return _mod


def _odd_primes(count, skip):
    """The first `count` odd primes other than `skip` (own sieve)."""
    lim, out = 64, []
    while len(out) < count:
        lim *= 2
        s = np.ones(lim, dtype=bool)
        s[:2] = False
        for i in range(2, int(lim ** 0.5) + 1):
            if s[i]:
                s[i * i::i] = False
        out = [int(q) for q in np.flatnonzero(s) if q != 2 and q != skip]
    return out[:count]


class GpuEngine:
    """One family's sweep.  `raw` is the device stream of one launch;
    `stream` is the production stream (primes only) of any window."""

    def __init__(self, power, sieve_primes=SIEVE_PRIMES, words=WORDS):
        if power not in POWERS:
            raise ValueError(f"no family of power {power}")
        if not available():
            raise RuntimeError("no CUDA device")
        if not 1 <= int(words) <= MAX_WORDS:
            raise ValueError("words per launch out of range")
        cp = _cp
        self.power, self.step = int(power), 2 * int(power)
        self.W = int(words)
        mod = _module()
        self.k_sieve = mod.get_function("rl_sieve")
        # (canonical, lazy): chosen per launch by its largest candidate
        self.k_test2 = (mod.get_function("rl_test2"),
                        mod.get_function("rl_test2_lazy"))
        self.k_base3 = (mod.get_function("rl_base3"),
                        mod.get_function("rl_base3_lazy"))
        self.k_run = mod.get_function("rl_run")
        qs = _odd_primes(int(sieve_primes), self.power)
        if qs[-1] >= MAX_SIEVE_PRIME:
            raise ValueError("sieve primes must stay below 2^20")
        self.q = np.array(qs, dtype=np.uint64)
        self.inv = np.array([pow(self.step, -1, q) for q in qs],
                            dtype=np.uint64)
        # the density of candidates left by the first i sieve primes
        self.alive = np.concatenate(
            ([1.0], np.cumprod(1.0 - 1.0 / self.q.astype(np.float64))))
        self.ntiny_all = sum(1 for q in qs if q < 64)
        pat, off = [], []
        for q in qs[: self.ntiny_all]:
            off.append(len(pat))
            for s in range(q):
                m = 0
                for b in range(s, 64, q):
                    m |= 1 << b
                pat.append(m)
        self.d_q = cp.asarray(self.q.astype(np.uint32))
        self.d_mg = cp.asarray(((1 << 32) // self.q).astype(np.uint32))
        self.d_pat = cp.asarray(np.array(pat or [0], dtype=np.uint64))
        self.d_off = cp.asarray(np.array(off or [0], dtype=np.int32))
        pr = _odd_primes(RUN_CAP - 1, 0)
        self.d_pr = cp.asarray(np.array([2] + pr, dtype=np.uint32))
        self.last = {}

    def held_bytes(self):
        # the candidate list and the pass list, at the full sieve's density
        return int(2 * 4 * 64 * self.W * (self.alive[-1] * 1.05)) + (1 << 20)

    # ------------------------------------------------------------- a launch
    def raw(self, j0, words, floor):
        """The device stream of candidates j0 .. j0 + 64*words - 1: (idx,
        run) numpy arrays, idx ascending, for every candidate j0 + idx
        that survives the sieve and has device run >= floor."""
        cp = _cp
        j0, words, floor = int(j0), int(words), int(floor)
        if j0 < 1 or floor < 1 or not 1 <= words <= MAX_WORDS:
            raise ValueError("bad launch")
        n_max = self.step * (j0 + 64 * words - 1) + 1
        if n_max >= P_CEIL:
            raise ValueError("launch above the ceiling 2^63")
        lazy = 1 if n_max < LAZY_BELOW else 0
        n_min = self.step * j0 + 1
        # a sieve prime is used only where every candidate exceeds it
        nprime = int(np.searchsorted(self.q, n_min, side="left"))
        ntiny = min(nprime, self.ntiny_all)
        q = self.q
        r0 = (q - (self.inv + np.uint64(j0) % q) % q) % q
        d_r0 = cp.asarray(r0.astype(np.uint32))
        ncand = 64 * words
        cap = int(min(ncand, ncand * self.alive[nprime] * 1.05 + 65536))
        cand = cp.empty(cap, dtype=cp.uint32)
        cnt = cp.zeros(5, dtype=cp.uint32)
        blk = 256
        blocks = (words + BLOCK_WORDS - 1) // BLOCK_WORDS
        self.k_sieve(((blocks + blk - 1) // blk,), (blk,),
                     (self.d_q, self.d_mg, d_r0, self.d_pat, self.d_off,
                      np.int32(ntiny), np.int32(nprime), cand, cnt[0:1],
                      np.uint32(cap), np.int32(words)))
        total = int(cnt[0])
        if total > cap:
            raise RuntimeError(f"sieve overflow: {total} survivors, room "
                               f"for {cap}")
        self.last = {"candidates": ncand, "sieved": total, "passed": 0,
                     "kept": 0, "nprime": nprime, "lazy": bool(lazy)}
        empty = (np.zeros(0, np.uint32), np.zeros(0, np.uint8))
        if total == 0:
            return empty
        u_j0, u_step = np.uint64(j0), np.uint64(self.step)
        passed = cp.empty(total, dtype=cp.uint32)
        self.k_test2[lazy]((((total + 1) // 2 + blk - 1) // blk,), (blk,),
                           (cand, np.uint32(total), u_j0, u_step, passed,
                            cnt[1:2]))
        npass = int(cnt[1])
        self.last["passed"] = npass
        if npass == 0:
            return empty
        # the staged bases: only those below the floor (a candidate that
        # fails one of them has a run the caller did not ask for)
        cur, ncur, tstart = passed, npass, 1
        stages = min(RUN_STAGES, floor - 1)
        if stages >= 1:                                   # the base 3
            nxt = cp.empty(ncur, dtype=cp.uint32)
            self.k_base3[lazy]((((ncur + 1) // 2 + blk - 1) // blk,), (blk,),
                               (cur, np.uint32(ncur), u_j0, u_step, nxt,
                                cnt[3:4]))
            cur, ncur, tstart = nxt, int(cnt[3]), 2
            if ncur == 0:
                return empty
        if stages >= 2:                                   # the base 5
            nxt = cp.empty(ncur, dtype=cp.uint32)
            unused = cp.empty(ncur, dtype=cp.uint8)
            self.k_run(((ncur + blk - 1) // blk,), (blk,),
                       (cur, np.uint32(ncur), u_j0, u_step, self.d_pr,
                        np.int32(2), np.int32(3), np.int32(3), nxt, unused,
                        cnt[4:5]))
            cur, ncur, tstart = nxt, int(cnt[4]), 3
            if ncur == 0:
                return empty
        oidx = cp.empty(ncur, dtype=cp.uint32)
        orun = cp.empty(ncur, dtype=cp.uint8)
        self.k_run(((ncur + blk - 1) // blk,), (blk,),
                   (cur, np.uint32(ncur), u_j0, u_step, self.d_pr,
                    np.int32(tstart), np.int32(RUN_CAP), np.int32(floor),
                    oidx, orun, cnt[2:3]))
        kept = int(cnt[2])
        self.last["kept"] = kept
        if kept == 0:
            return empty
        idx, rr = cp.asnumpy(oidx[:kept]), cp.asnumpy(orun[:kept])
        order = np.argsort(idx, kind="stable")
        return idx[order], rr[order]

    # ------------------------------------------------------------ a window
    def raw_window(self, j0, count, floor):
        """[(j, run)] of the device stream over j0 <= j < j0 + count, in
        launches of at most self.W words (the last one clipped on host)."""
        j0, count = int(j0), int(count)
        out, j = [], j0
        end = j0 + count
        while j < end:
            words = min(self.W, (end - j + 63) // 64)
            start = j
            if self.step * (j + 64 * words - 1) + 1 >= P_CEIL:
                # only the padding of the window's last word can reach the
                # ceiling (a window that itself does is refused by `raw`):
                # move the launch back to END on the last candidate, and
                # drop the few it repeats
                start = max(1, end - 64 * words)
            idx, rr = self.raw(start, words, floor)
            for t, r in zip(idx.tolist(), rr.tolist()):
                if j <= start + t < end:
                    out.append((start + t, r))
            j = start + 64 * words
        return out

    def stream(self, j0, count, floor=1):
        """THE STREAM (residue_search.sweep's definition): [(p, run)] for
        every PRIME p = 2*power*j + 1 of the window with run >= floor.  The
        device proposes; huntlib's deterministic Miller-Rabin disposes."""
        out = []
        for j, r in self.raw_window(j0, count, floor):
            p = self.step * j + 1
            if hprimes.mr_is_prime(p):
                out.append((p, r))
        return out


def _engine(power, **kw):
    key = (power,) + tuple(sorted(kw.items()))
    if key not in _engines:
        _engines[key] = GpuEngine(power, **kw)
    return _engines[key]


def k_ceil():
    return P_CEIL


_FP_A = np.uint64(0x9E3779B97F4A7C15)
_FP_B = np.uint64(0xD6E8FEB86659FD93)


def bind(p, run):
    """One uint64 per (p, run) pair that BINDS the run to its prime:
    (p + run*B)*A mod 2^64, folded.  The entry of a prime changes with its
    run and differs from that of any other prime with the same run, and it
    is not additive in the pair -- so the XOR over a window is not kept by
    two primes exchanging unequal runs, which the XOR of p ^ (run << 56) is
    (finding RSL-008 of the Codex review; gate P6 plants the exchange)."""
    v = (p.astype(np.uint64) + run.astype(np.uint64) * _FP_B) * _FP_A
    return v ^ (v >> np.uint64(32))


def launch_pairs(e, j0, launches, floor):
    """[(p, run, sieve survivors, first-test passes)] of `launches` full
    launches from j0; p and run are arrays over the device survivors at the
    floor, p ascending."""
    out = []
    j = int(j0)
    for _ in range(int(launches)):
        idx, rr = e.raw(j, e.W, floor)
        p = (np.uint64(j) + idx.astype(np.uint64)) * np.uint64(e.step) \
            + np.uint64(1)
        out.append((p, rr, e.last["sieved"], e.last["passed"]))
        j += 64 * e.W
    return out


def fingerprint(e, j0, launches, floor):
    """The work fingerprint of `launches` full launches from j0: a uint64
    array with one entry per device survivor at the floor, bind(p, run) --
    so a missing prime, an extra one, a changed run or two runs exchanged
    moves the count or the checksum -- plus two entries per launch digesting
    what the launch did on the way (the number of sieve survivors and of
    candidates that passed the first test), so a skipped stage moves it
    too."""
    parts = []
    for p, rr, sieved, passed in launch_pairs(e, j0, launches, floor):
        parts.append(bind(p, rr))
        parts.append(np.array([sieved, passed * 2654435761 % (1 << 62)],
                              dtype=np.uint64))
    return np.concatenate(parts)


# ---------------------------------------------------------------- the gates
def _cpu():
    import residue_search as cpu
    return cpu


def gate_p0():
    cpu = _cpu()
    if not (P_CEIL == cpu.P_CEIL and RUN_CAP == cpu.RUN_CAP
            and POWERS == cpu.POWERS):
        return False, "P0 the two engines disagree about their constants"
    e = _engine(5)
    try:
        e.raw(P_CEIL // 10, 1, 1)
        return False, "P0 a launch above 2^63 ran"
    except ValueError:
        pass
    # the last candidates below the ceiling, in a window that is not a
    # whole number of words: swept (the launch ends on the last candidate),
    # equal to the CPU engine, and refused one candidate further
    n = 0
    for power in POWERS:
        e = _engine(power)
        j_top = (P_CEIL - 2) // (2 * power)
        got = e.stream(j_top - 999, 1000, 1)
        if got != cpu.sweep(power, j_top - 999, 1000, 1):
            return False, f"P0 power {power}: the tail below 2^63 differs"
        if e.stream(j_top - 36, 37, 1) != [g for g in got
                                           if g[0] >= 2 * power * (j_top - 36) + 1]:
            return False, f"P0 power {power}: a 37-candidate tail differs"
        try:
            e.stream(j_top - 999, 1001, 1)
            return False, "P0 a window one candidate above 2^63 ran"
        except ValueError:
            pass
        n += len(got)
    if n == 0:
        return False, "P0 the tails below 2^63 are empty"
    return True, (f"P0 constants: both engines state the ceiling p < 2^63, "
                  f"runs read against 40 primes and the five powers; a launch "
                  f"above the ceiling is refused; the last 1000 candidates "
                  f"below it -- not a whole number of words, so the launch is "
                  f"moved back to end on the last one -- give the CPU "
                  f"engine's {n} pairs over the five lines, the last 37 "
                  f"likewise, and one candidate further is refused")


# (label, p at the window's start); the window is 2^17 candidates
_HEIGHTS = (("the line's first candidate", 0), ("p = 10^6", 10 ** 6),
            ("10^9", 10 ** 9), ("2^42", 2 ** 42), ("10^16", 10 ** 16),
            ("10^17", 10 ** 17))


def _spans(power, count):
    """(label, first index, lazy arithmetic expected) of the windows of
    `count` candidates the parity gates use: the heights a campaign passes,
    the last window that runs the lazy arithmetic (its largest candidates:
    the bound hi < N is tightest there), the first that does not, and the
    last window under the ceiling."""
    step = 2 * power
    spans = [(lab, max(1, p0 // step), True) for lab, p0 in _HEIGHTS]
    spans.append(("the last window below 2^60",
                  (LAZY_BELOW - 2) // step - count + 1, True))
    spans.append(("2^60", LAZY_BELOW // step + 1, False))
    spans.append(("the ceiling 2^63", (P_CEIL - 2) // step - count + 1,
                  False))
    return spans


def gate_p1():
    """Parity with the CPU engine on POPULATED windows at every height the
    campaign passes, both sides of the lazy-arithmetic boundary and the
    ceiling, floor 1, all five families."""
    cpu = _cpu()
    n, least, wins = 0, None, 0
    count = 1 << 17
    for power in POWERS:
        e = _engine(power)
        for lab, j0, lazy in _spans(power, count):
            got = e.stream(j0, count, 1)
            if e.last.get("lazy") is not lazy:
                return False, (f"P1 power {power} at {lab}: the launch ran "
                               f"the wrong arithmetic")
            want = cpu.sweep(power, j0, count, 1)
            if got != want:
                return False, (f"P1 power {power} at {lab}: device stream "
                               f"({len(got)}) != CPU stream ({len(want)})")
            if not got:
                return False, f"P1 power {power} at {lab}: empty window"
            n += len(got)
            wins += 1
            least = len(got) if least is None else min(least, len(got))
    return True, (f"P1 parity GPU = CPU: {n} (p, run) pairs identical over "
                  f"{wins} windows of 2^17 candidates -- five families at the "
                  f"line's first candidate, 10^6, 10^9, 2^42, 10^16, 10^17, "
                  f"the last window below 2^60 (lazy arithmetic at its "
                  f"largest candidates), the first above it (canonical) and "
                  f"against the ceiling 2^63 -- none with fewer than {least} "
                  f"pairs")


def gate_p2():
    """Split and alignment invariance, and invariance under the depth of
    the sieve (a sieve that dropped a prime would show here)."""
    n = 0
    for power in POWERS:
        j0 = 10 ** 15 // (2 * power) + 7
        count = 3 * 64 * 1024 + 17
        base = _engine(power).stream(j0, count, 2)
        if not base:
            return False, f"P2 power {power}: empty"
        small = GpuEngine(power, words=1000)
        a = small.stream(j0, count, 2)
        b = (small.stream(j0, 50_001, 2)
             + small.stream(j0 + 50_001, count - 50_001, 2))
        if not (a == base and b == base):
            return False, f"P2 power {power}: a split or shifted run differs"
        for sp in (1, 16, 64, 1024, 20000):
            if GpuEngine(power, sieve_primes=sp).stream(j0, count, 2) != base:
                return False, f"P2 power {power}: stream changes with {sp} sieve primes"
        n += len(base)
    return True, (f"P2 invariance at p = 10^15: one launch, launches of 1000 "
                  f"words (a ragged last block), a window split at an odd "
                  f"index, and sieves of 1, 16, 64, 1024, {SIEVE_PRIMES} and "
                  f"20000 primes all give the same {n} pairs (floor 2)")


def gate_p3():
    """Planted drills: the comparator used by P1 catches a dropped pair, a
    bent run and a planted composite."""
    cpu = _cpu()
    e = _engine(7)
    j0 = 10 ** 12 // 14
    got = e.stream(j0, 1 << 15, 1)
    want = cpu.sweep(7, j0, 1 << 15, 1)
    if got != want or len(got) < 50:
        return False, "P3 base window differs"
    dropped = got[:20] + got[21:]
    bent = got[:20] + [(got[20][0], got[20][1] + 1)] + got[21:]
    planted = sorted(got + [(got[20][0] + 14, 1)])
    if dropped == want or bent == want or planted == want:
        return False, "P3 a corrupted stream compared equal"
    return True, (f"P3 planted drill: against the CPU stream of a window of "
                  f"{len(want)} pairs, a stream with one pair dropped, one "
                  f"with a run bent by 1 and one with a composite added are "
                  f"each caught")


def gate_p4():
    """Every published term is found by the device, first of its run in a
    launch around it, with the run the oracle gives it."""
    import residue_reference as ref
    n = 0
    for seq, fam in ref.FAMILIES.items():
        power = fam["power"]
        e = _engine(power, words=64)
        for i, p in enumerate(fam["known"]):
            j = (p - 1) // (2 * power)
            got = e.stream(max(1, j - 2000), 4096, i + 1)
            if not got or got[0] != (p, ref.run(p, power)):
                return False, f"P4 {seq}: a({i + 1}) = {p} not first in the device stream"
            n += 1
    return True, (f"P4 known terms on the device: all {n} published terms "
                  f"come first, with the oracle's run, in the device stream "
                  f"of the 4096 candidates around them at their index as "
                  f"floor")


def gate_p5():
    """The host leg is needed and works: with the sieve all but off the
    device hands over composites that pass the first test; Miller-Rabin
    removes exactly those."""
    cpu = _cpu()
    tot = 0
    for power in POWERS:
        e = GpuEngine(power, sieve_primes=1, words=1024)
        count = 1 << 16
        rawv = [e.step * j + 1 for j, _r in e.raw_window(1, count, 1)]
        comp = [v for v in rawv if not hprimes.mr_is_prime(v)]
        if comp != [v for v in cpu.first_test_composites(power, 1, count)
                    if v % 3]:
            return False, f"P5 power {power}: device composites differ from plain Python's"
        if [v for v in rawv if hprimes.mr_is_prime(v)] != \
                [p for p, _ in cpu.sweep(power, 1, count, 1)]:
            return False, f"P5 power {power}: primes differ"
        tot += len(comp)
    if tot == 0:
        return False, "P5 no composite passed the first test: the gate is vacuous"
    return True, (f"P5 the host leg: sieving by 3 alone, the device reports "
                  f"{tot} COMPOSITES among the first 65,536 candidates of "
                  f"the five lines (2^j == +-1 mod N without N prime) -- the "
                  f"same ones plain Python finds -- and Miller-Rabin removes "
                  f"exactly them")


def gate_p6():
    """The fingerprint is deterministic, moves when work is skipped, and
    binds each run to its own prime."""
    e = _engine(5, words=4096)
    j0 = 10 ** 16 // 10
    a = fingerprint(e, j0, 2, 3)
    b = fingerprint(e, j0, 2, 3)
    c = fingerprint(e, j0, 1, 3)
    x = int(np.bitwise_xor.reduce(a))
    if not (a.size == b.size and x == int(np.bitwise_xor.reduce(b))
            and a.size > c.size and a.size > 40):
        return False, "P6 fingerprint not deterministic"
    # planted: two primes of the window exchange their unequal runs
    p, rr, _s, _t = launch_pairs(e, j0, 1, 3)[0]
    lo, hi = int(np.argmin(rr)), int(np.argmax(rr))
    if rr[lo] == rr[hi]:
        return False, "P6 the window holds one run length: the plant is vacuous"
    sw = rr.copy()
    sw[lo], sw[hi] = rr[hi], rr[lo]
    sh = np.uint64(56)
    legacy_same = (int(np.bitwise_xor.reduce(p ^ (rr.astype(np.uint64) << sh)))
                   == int(np.bitwise_xor.reduce(p ^ (sw.astype(np.uint64) << sh))))
    moved = (int(np.bitwise_xor.reduce(bind(p, rr)))
             != int(np.bitwise_xor.reduce(bind(p, sw))))
    if not (legacy_same and moved):
        return False, ("P6 two runs exchanged between primes did not move "
                       "the checksum")
    return True, (f"P6 fingerprint: two launches at p = 10^16 give the same "
                  f"{a.size} entries twice; one launch gives fewer; the runs "
                  f"{int(rr[lo])} and {int(rr[hi])} exchanged between two "
                  f"primes move the checksum (the XOR of p ^ run*2^56 they "
                  f"leave unchanged)")


def gate_p7():
    """The first test against plain Python on EVERY candidate, prime or
    composite, of windows placed on the corners of its arithmetic: sieve by
    3 alone, floor 1, so the device reports exactly the candidates with
    2^j == +-1 (mod N)."""
    cpu = _cpu()
    count = 1 << 14
    n = comp = wins = 0
    for power in POWERS:
        step = 2 * power
        e = GpuEngine(power, sieve_primes=1, words=count // 64)
        if [int(q) for q in e.q] != [3]:
            return False, "P7 the one sieve prime is not 3"
        spans = [
            ("the line's first candidates", 1, True),
            ("N across 2^32", (1 << 32) // step - count // 2, True),
            ("j + 64 across 2^40", (1 << 40) - 64 - count // 2, True),
            ("the last window below 2^60",
             (LAZY_BELOW - 2) // step - count + 1, True),
            ("2^60", LAZY_BELOW // step + 1, False),
            ("the ceiling 2^63", (P_CEIL - 2) // step - count + 1, False)]
        for lab, j0, lazy in spans:
            got = [j for j, _r in e.raw_window(j0, count, 1)]
            if e.last.get("lazy") is not lazy:
                return False, f"P7 power {power} at {lab}: wrong arithmetic"
            want = cpu.first_test_passes(power, j0, count, skip=3)
            if got != want:
                return False, (f"P7 power {power} at {lab}: the device passes "
                               f"{len(got)} candidates, plain Python "
                               f"{len(want)}")
            if not got:
                return False, f"P7 power {power} at {lab}: empty window"
            n += len(got)
            wins += 1
            comp += sum(1 for j in got
                        if not hprimes.mr_is_prime(step * j + 1))
    if comp == 0:
        return False, "P7 no composite among the passes: the gate is vacuous"
    return True, (f"P7 the first test = plain Python on every candidate: "
                  f"{n} candidates with 2^j == +-1 (mod N), {comp} of them "
                  f"composite, identical over {wins} windows of 2^14 -- five "
                  f"families at the line's first candidates (seeds reduced), "
                  f"N across 2^32, j + 64 across a power of two (the lanes "
                  f"of a thread on either side; h = 32 and h = 64), the last "
                  f"window below 2^60, the first above it and the ceiling")


def gate_p8():
    """The staged run = the unstaged run: the stream at floors 2 to 5 (one
    stage, then two) is the floor-1 stream (none) with the shorter runs
    removed, on both arithmetics."""
    count = 1 << 20
    n = wins = 0
    for power in POWERS:
        e = _engine(power)
        for lab, j0, lazy in _spans(power, count):
            base = e.raw_window(j0, count, 1)
            if e.last.get("lazy") is not lazy:
                return False, f"P8 power {power} at {lab}: wrong arithmetic"
            for floor in (2, 3, 4, 5):
                want = [(j, r) for j, r in base if r >= floor]
                if e.raw_window(j0, count, floor) != want:
                    return False, (f"P8 power {power} at {lab}: floor "
                                   f"{floor} differs from the floor-1 stream")
                if floor == 3 and not want:
                    return False, f"P8 power {power} at {lab}: empty at floor 3"
                n += len(want)
            wins += 1
    return True, (f"P8 staged run = unstaged run: over {wins} windows of 2^20 "
                  f"candidates (the heights of P1) the device stream at "
                  f"floors 2, 3, 4 and 5 -- the base 3 in its own kernel, "
                  f"then the base 5 -- is the floor-1 stream, which runs no "
                  f"stage, with the shorter runs removed: {n} pairs")


GATES = [gate_p0, gate_p1, gate_p2, gate_p3, gate_p4, gate_p5, gate_p6,
         gate_p7, gate_p8]


def selftest():
    if not available():
        print("FAIL no CUDA device: the GPU engine's gates did not run")
        return False
    ok = True
    for g in GATES:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg, flush=True)
        ok = ok and good
    return ok


if __name__ == "__main__":
    from huntlib import shutdown
    sys.exit(shutdown.graceful(lambda: 0 if selftest() else 1))
