# hlc_gpu.py -- THE GPU ENGINE for A331940 (the production engine), v3.
#
# A331940: addends k > 0 such that x^2 + x + k produces a record of its
# Hardy-Littlewood constant C.  The hunt needs, for every odd k in order,
# a proof that C(k) does not exceed a threshold, or the exact C(k); both
# come from the class number of the discriminant 1 - 4k (hlc_search.py
# derives the survivor rule).  For n = 4k - 1 the rule drops k as soon as
# ANY lower bound LB <= h(-n) has 3*LB*rho(n)*2F >= pi*sqrt(n), and keeps
# k with its exact T(n) = 3H(n) otherwise.  This engine produces, per
# window of 2^22 consecutive n = 8m + 3, exactly that:
#
#   1. THE CLASS-GROUP PREFILTER (kernels pre1, pre2).  One thread per n
#      proves h(-n) >= need from the order of a prime form in the class
#      group, the genus factor 2^(t-1) and, when one form is not enough,
#      the index of a second form's square in the first one's
#      (hlc_search.py states the three bounds and their proofs).  It costs
#      O(n^(1/4)) compositions per n and decides ~99.7% of them.
#   2. THE SPARSE EXACT COUNT, for the n the prefilter could not decide
#      (kernels spa, spb; engine v3): reduced forms counted by their
#      leading coefficient a, one n per thread block -- see below.  Phase
#      A drops n as soon as a prefix of the count reaches the rule; phase B
#      finishes the count for the ~1% it cannot drop (the survivors).
#   3. THE SURVIVOR RULE on the exact counts (kernel classify).
#
# The survivor stream is IDENTICAL to tabulating every counter (kernel
# tab, the v1 path, kept as h3() for the gates, the recount, floor 0 and
# the opening band below PRE_MIN_N): the prefilter and phase A only remove
# n the rule would drop, by proof, and phase B counts exactly.
#
# THE SPARSE COUNT (engine v3; the Codex review's HLC-003, with the roots
# replaced by their number where the reduction condition allows it).  T(n)
# is 3 x the number of reduced forms (a, b, c), b^2 - 4ac = -n, primitive
# or not, a form a(x^2 + xy + y^2) at 1/3.  A reduced form of this odd
# discriminant has a, b, c odd and |b| <= a <= c, so a <= isqrt(n/3); for a
# given odd a the b are the roots of b^2 = -n (mod a), each taken as its
# odd representative in (-a, a] (4a | b^2 + n then holds: b^2 + n == 4
# mod 8), and the form is reduced iff c >= a (with b >= 0 when c = a).
#   * PHASE A, odd a <= A = isqrt(n) // 2: 4a^2 < n, so c > a for EVERY
#     root and the a contribute 3*N(a), N(a) the number of square roots of
#     -n modulo a -- multiplicative: N(p^e) = 1 + (-n|p) for p !| n, and
#     for p^v || n, p^(e//2) when e <= v, 0 when e > v and v is odd, and
#     p^(v/2) (1 + (-u|p)) when e > v and v is even (u = n / p^v).  No
#     root is computed: one Legendre symbol per prime p <= A (Euler's
#     criterion), the smallest-prime-factor table for a, a sum.  Every
#     prefix is a LOWER bound of T, so the rule (monotone in T) may drop n
#     after any chunk; it does so for 99% of the flagged n, after about
#     half of the range at the median.
#   * PHASE B, A < a <= isqrt(n/3) (the band): the roots themselves --
#     Tonelli-Shanks modulo each split prime, Hensel lifting to its power,
#     the closed forms above for p | n, and the Chinese remainder theorem
#     -- each tested for c >= a.  Weight 3, or 1 for a = b = c (n = 3a^2).
# OPTIMIZATION_LOG.md round 2 has the identity checked against the
# three-squares count and the measurements; gate P7 pins the two counts.
#
# THE TABULATION (Gauss).  For n == 3 (mod 8), n = 8m + 3, every
# representation n = x^2 + y^2 + z^2 has x, y, z odd, and r_3(n) = 24*H(n),
# H the Hurwitz class number.  Dropping the 8 sign choices,
#
#     T(n) = 3*H(n) = sum over odd x >= y >= z >= 1, x^2 + y^2 + z^2 = n,
#            of 6 (all different), 3 (two equal), 1 (all equal).
#
# One kernel thread owns CH consecutive y for one x and walks the odd z
# with x^2 + y^2 + z^2 inside the window; consecutive z differ by
# (z + 1)/2 in m.  Tabulating every counter costs one atomic add per
# representation into a table that must stay inside the device's L2 cache
# (2^22 counters).  Engine v2 tabulated the flagged counters this way too,
# testing one bit per representation; it visited every representation of
# the window to find the 0.3% it needed, and the sparse count replaced it
# (3.8x a window at k = 10^12; OPTIMIZATION_LOG.md round 2).
#
# THE PREFILTER'S ARITHMETIC.  A form is (a, b, c), b^2 - 4ac = -n, all
# three odd (n == 3 mod 8); reduced forms have a <= sqrt(n/3) < 2^23.
#   * a prime-form step g -> g o (p, beta) needs one inverse modulo p (a
#     byte table) and the exact division by p as a multiplication by the
#     inverse of p modulo 2^64;
#   * a general composition is Cohen's Algorithm 5.4.7 with a 32-bit
#     extended Euclid; its last coefficient (B^2 + n)/(4A), a 92-bit
#     numerator, is computed in wrapping 64-bit arithmetic through the
#     inverse of the odd A modulo 2^64 (the quotient is below 2^62);
#   * divisibility by the trial primes is one multiplication by the
#     prime's inverse modulo 2^64 and a comparison.
# The CPU reference (hlc_search.prefilter_flag) uses Python integers, the
# textbook formulas and dictionaries; gate P5 pins the two decisions
# bit-for-bit and gate P6 pins the filtered stream to the unfiltered one.
#
# NUMERIC HYGIENE (enforced constants; engine v4 -- v3 stopped at 2^46).
#   N_CEIL = 2^62 bounds n = 4k - 1 (K_CEIL = 10^18 is n = 4.0e18), so a
#   reduced form has a <= isqrt(n/3) < 2^30.3, |b| <= a, c < 2^60:
#     * prefilter: a composed form before reduction has a < 2^61, |b| <= a
#       and c = (B^2 + n)/4A < 2^62 (computed mod 2^62 through the inverse
#       of A mod 2^64); Gauss reduction's products are differences of c's;
#       the CRT products of Cohen 5.4.7 are below 2^61; a prime-form step's
#       residues are taken by a 32-bit multiply-high quotient, exact for
#       every u32 (v3 used a float quotient, exact while a < 2^23); every
#       product in it is below 2^62.  The table key must be INJECTIVE on
#       reduced forms: a*2^24 + (b mod 2^24) in one u64 below N_WIDE =
#       3*2^46 (a < 2^23, as v3), a*2^32 + (b mod 2^32) in a 16-byte slot
#       above (0.76x on the window, measured where it was forced at
#       3*10^12; it is needed from k ~ 5.3*10^13).  Orders and step counts
#       are below PRE_NEED_MAX + 2^7 < 2^29.  Trial division reaches the
#       cube root of the window's top (PRE_TRIAL_MAX passes 2^62's).
#     * sparse count: a <= isqrt(n/3) < 2^31; residues and moduli are
#       below 2^31, so a product of two is below 2^62 and the Barrett
#       reduction by floor(2^64/p) needs one correction; b^2 + n < 2^63;
#       the tables grow with the height (SP_PMAX at start, at most
#       SP_PMAX_TOP); the characters of the first 32*SP_MAXW primes sit in
#       shared memory and those of larger primes are computed on the fly
#       (at most one such prime divides an a); an odd a < 2^31 has at
#       most eight distinct prime factors (the root tables hold eight); T
#       of a counted n is below 2^32 (it passed phase A's prefix test), and
#       is checked before it is stored.
#     * the walk (the gates, the opening band and the recount): x^2 + y^2
#       + z^2 < 2^64; square roots from a double, made exact by integer
#       correction; T(n) < 2^32 needs n < WALK_MAX_N = 2^53 (T = 3H <= 3 *
#       (sqrt(n)/pi) * (2 + log n)), past which the walk refuses; a window
#       needing more than 2^31 - 1 blocks is launched in pieces.
#     * the rule: RHO_LARGE and RHO_MIN are the WINDOW's (rho_large,
#       rho_min): v3's constants below 2^46, three primes past 251 and
#       RHO_MIN 0.32 by 2^62 (gate S0 on the CPU, P0 between the engines).
#   The ceiling comes from these; cost puts it far past any campaign (see
#   k_ceil()).
#
# The GPU proposes; the host verifies (hlc_search.py).  This module never
# calls the CPU engine outside its gates.

import bisect
import math
import sys
import time

import numpy as np

SEQUENCE = "A331940"
FORMS = "x^2 + x + k"
ENGINE_VERSION = "v4.1"       # v4.1: v4's stream, round-4 kernels (the
                              # cursor key stays v4's: coverage identical)

N_CEIL = 1 << 62             # n = 4k - 1 below this: every product fits
K_CEIL = 10**18              # the last rung (n = 4.0e18); engine v3: 10^13
N_OLD = 1 << 46              # engine v3's ceiling: below it v4 IS v3
N_WIDE = 3 << 46             # from here a reduced form can have a >= 2^23
WALK_MAX_N = 1 << 53         # the walk's u32 counters hold T(n) below this
TAB_GRID = (1 << 31) - 1     # walk blocks per launch, at most (one launch
                             # below k ~ 8*10^13, as in v3; pieces above)
LOGW = 22                    # window: 2^22 values of m = 2^23 of k
CH = 8                       # y per thread, full tabulation
SP_PMAX = math.isqrt((N_OLD - 1) // 3) + 2    # sparse tables at start (v3's)
SP_PMAX_TOP = math.isqrt((N_CEIL - 1) // 3) + 2   # ... grown to this at most
SP_MAXW = 12160              # character words a block keeps in shared memory
                             # (48 KB less the statics): the primes past the
                             # 389,120th (5.6e6) get their characters on the
                             # fly, from k ~ 2.3*10^13 (phase B) on
SP_THREADS = 256             # sparse count: threads per block (one n each)
SP_CHUNK = 32                # phase A: the rule is tried after each 1/32 of a
SP_BLOCKS_A = 1024           # resident blocks, phase A
SP_BLOCKS_B = 256            # resident blocks, phase B

# the survivor rule's constants: this engine's own copy (gate P0 compares
# them with the CPU engine's).  See hlc_search.survivor_mask for the rule.
SMALLP = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
          67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131,
          137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197,
          199, 211, 223, 227, 229, 233, 239, 241, 251]
RHO_LARGE = (1.0 - 1.0 / 257) * (1.0 - 1.0 / 263) * (1.0 - 2.0 ** -40)
RHO_MIN = 0.33               # (both: every window below 2^46, as in v3)
PI_UP = math.pi * (1.0 + 2.0 ** -40)
_PAST_251 = (257, 263, 269, 271, 277)   # the primes after 251, to 2^64


def rho_large(nmax):
    """RHO_LARGE for a window whose largest n is nmax: (1 - 1/p) over the
    primes past 251 whose squares can all divide some n <= max(nmax,
    2^46 - 1), padded by 2^-40 -- v3's constant below 2^46, three primes
    by 2^62 (this engine's copy; gate P0 compares it with the CPU's)."""
    nmax = max(int(nmax), N_OLD - 1)
    rho, prod = 1.0, 1
    for p in _PAST_251:
        if prod * p * p > nmax:
            break
        prod *= p * p
        rho *= 1.0 - 1.0 / p
    return rho * (1.0 - 2.0 ** -40)


def rho_min(nmax):
    """RHO_MIN for a window whose largest n is nmax: 0.33 while that is at
    most the least rho(n) of any n <= nmax (to 1.24e16), else that least
    value rounded down to 0.01 (0.32 to 2^62)."""
    nmax = max(int(nmax), N_OLD - 1)
    rho, prod = 1.0, 1
    for p in SMALLP:
        if prod * p * p > nmax:
            break
        prod *= p * p
        rho *= 1.0 - 1.0 / p
    v = rho * rho_large(nmax)
    return RHO_MIN if v >= RHO_MIN else math.floor(v * 100.0) / 100.0
# the local Euler factors at p <= 251 (hlc_search states the bound): the
# right side of the rule is (PI_UP*sqrt(n)) * (prod q_p * Q_PAD), the
# product in ascending p -- 1 inert, Q_RAM p | n, Q_SPL split
Q_RAM = [1.0 - 1.0 / (p * p) for p in SMALLP]
Q_SPL = [1.0 - 2.0 / (p * (p - 1)) for p in SMALLP]
Q_PAD = 1.0 + 2.0 ** -40

# the prefilter's constants: this engine's own copy (gate P0 again)
PRE_MIN_N = 1 << 20
PRE_NGENS = 8
PRE_NBASE = 2
PRE_CAP2 = 16
PRE_NEED_MAX = 1 << 28       # v3: 2^22, which no n below 2^46 reaches
PRE_RATIO = 5                # general compositions priced in prime steps
PRE_SP_MAX = 128             # giant steps tabled (the table has 256 slots)
PRE_THREADS = 57344          # prefilter threads resident (448 per SM; full
                             # occupancy is 512, and one step past it costs
                             # 0.84x -- OPTIMIZATION_LOG.md round 2)
PRE_BLOCK = 128
PRE_TRIAL_MAX = 1700000      # trial primes: past the cube root of 2^62
                             # (1664511); a window uses those to its own

_WALK = r'''
// T(8m+3) += weights for m in [m0, m0+W): n0 = 8*m0 + 3.  Threads t0 +
// [0, grid): a window needing more than one grid's worth is launched in
// pieces (engine v4: past k ~ 3*10^13 one grid is not enough).
extern "C" __global__
void @NAME@(const u64 n0, const u32 W, const int ch, const long long nthreads,
            const long long t0, const int nx, const u64* pref, const u32* xs,
            const u32* ylo, const u32* ycnt, u32* cnt@FLAGPARAM@)
{
    const long long t = t0 + (long long)blockIdx.x * blockDim.x
                        + threadIdx.x;
    if (t >= nthreads) return;
    int lo = 0, hi = nx;                 // pref[lo] <= t < pref[lo+1]
    while (hi - lo > 1) {
        const int mid = (lo + hi) >> 1;
        if (pref[mid] <= (u64)t) lo = mid; else hi = mid;
    }
    const u64 x = xs[lo];
    const u64 x2 = x * x;
    const u32 yc = ycnt[lo];
    const u32 j0 = (u32)((u64)t - pref[lo]) * (u32)ch;
    u32 j1 = j0 + (u32)ch; if (j1 > yc) j1 = yc;
    if (j0 >= j1) return;
    // State for the current y: zl, the least odd z >= 1 with
    // x^2 + y^2 + zl^2 >= n0, and e = x^2 + y^2 + zl^2 - n0 (a multiple
    // of 8; e < 4*zl - 4 when zl > 1, by minimality).  One square root
    // for the thread's first y; after that y -> y + 2 adds 4y + 4 to e
    // and zl steps down while (zl - 2)^2 still reaches n0.
    u32 yy = ylo[lo] + 2u * j0;
    u32 zl = 1u, e;
    {
        const u64 S = x2 + (u64)yy * (u64)yy;
        if (S + 1 >= n0) {
            const u64 d = S + 1 - n0;
            if (d >= 8ull * (u64)W) return;  // this y and every later one
            e = (u32)d;
        } else {
            const u64 r = n0 - S;
            u64 z = (u64)sqrt((double)r);    // within one of the root
            while (z * z > r) --z;
            while ((z + 1) * (z + 1) <= r) ++z;
            if (z * z < r) ++z;
            z |= 1ull;
            zl = (u32)z;
            e = (u32)(z * z - r);
        }
    }
    const u32 e_end = 8u * W;
    const u32 xx = (u32)x;
    for (u32 j = j0; ; ) {
        if (zl == 1u && e >= e_end) break;   // z = 1 is past the window
        u32 idx = e >> 3;
        u32 zz = zl;
        const u32 w = (xx == yy) ? 3u : 6u;
        while (zz < yy && idx < W) {         // the z < y part
            ADD(idx, w);
            idx += (zz + 1u) >> 1;
            zz += 2u;
        }
        if (zz == yy && idx < W)             // the z = y term
            ADD(idx, (xx == yy) ? 1u : 3u);
        if (++j >= j1) break;
        e += 4u * yy + 4u;
        yy += 2u;
        while (zl > 1u && e >= 4u * zl - 4u) { e -= 4u * zl - 4u; zl -= 2u; }
    }
}
'''

_SRC = r'''
typedef unsigned long long u64;
typedef long long i64;
typedef unsigned int u32;
typedef int i32;

#define ADD(i, w) atomicAdd(cnt + (i), (w))
@TAB@
#undef ADD

#define QPAD @QPAD@
#define NSMALL @NSMALL@

// Q(n) * QPAD: the known Euler factors at the 53 primes <= 251 over their
// maxima, multiplied in ascending p (hlc_search.local_q).
// sqt[soff[j] + r] is the odd square root of r mod p_j, or 0.
__device__ __forceinline__ double localq(const u64 n, const u32* tp,
        const u64* smu, const u32* soff, const unsigned char* sqt,
        const double* qram, const double* qspl)
{
    double Q = 1.0;
    for (int j = 0; j < NSMALL; ++j) {
        const u32 pp = tp[j];
        const u64 qq = __umul64hi(n, smu[j]);
        u32 nm = (u32)(n - qq * pp);
        if (nm >= pp) nm -= pp;
        if (nm == 0u) Q = Q * qram[j];
        else if (sqt[soff[j] + (pp - nm)]) Q = Q * qspl[j];
    }
    return Q * QPAD;
}

// The survivor rule, in the IEEE-double order hlc_search.survivor_mask
// uses: A = T*f2, R = (pi_up*sqrt(n)) * localq(n); survivor iff
// A*rho_min < R and A*rho(n) < R, rho(n) = rho_large * prod_{p^2 | n}
// (1 - 1/p) ascending.  With a bitmap, only the counters counted to the
// end are read (the others were dropped by the prefilter or by a prefix of
// the sparse count, and hold no count).
extern "C" __global__
void classify(const u64 m0, const int W, const u32* cnt, const u32* flag,
              const double f2, const double pi_up, const double rho_min,
              const double rho_large, const int np, const u32* p2,
              const double* inv, const u32* tp, const u64* smu,
              const u32* soff, const unsigned char* sqt, const double* qram,
              const double* qspl, u32* nout, u32* out_i, u32* out_t)
{
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= W) return;
    if (flag && !((flag[i >> 5] >> (i & 31)) & 1u)) return;
    const u64 n = 8ull * (m0 + (u64)i) + 3ull;
    const u32 T = cnt[i];
    const double A = (double)T * f2;
    const double R = (pi_up * sqrt((double)n))
                     * localq(n, tp, smu, soff, sqt, qram, qspl);
    if (!(A * rho_min < R)) return;
    double rho = rho_large;
    for (int j = 0; j < np; ++j)
        if (n % (u64)p2[j] == 0) rho = rho * inv[j];
    if (A * rho < R) {
        const u32 o = atomicAdd(nout, 1u);
        out_i[o] = (u32)i;
        out_t[o] = T;
    }
}

// ===================================================== the prefilter
#define TS 256
#define NSMALL @NSMALL@
#define SP_MAX @SP_MAX@
#define RATIO @RATIO@
#define CAP2 @CAP2@
#define NGENS @NGENS@
#define NEED_MAX @NEED_MAX@ull

__device__ __forceinline__ i64 fdiv_near(const i64 b, const i64 a)
{   // floor((b + a) / (2a)), a > 0
    const i64 num = b + a, den = 2 * a;
    if (num >= 0) {
        if (num < den) return 0;
        if (num < 2 * den) return 1;
        if (num < 3 * den) return 2;
    } else {
        if (num >= -den) return -1;
        if (num >= -2 * den) return -2;
    }
    {   // |q| < 2^20: a float estimate, made exact by the remainder (the
        // loops end with 0 <= num - q*den < den whatever the estimate was;
        // engine v4.1, in place of the 64-bit division subroutine that one
        // lane at a time took ~10% of pass 1's instructions)
        const float qf = floorf(__fdividef((float)num, (float)den));
        if (fabsf(qf) < 1048576.0f) {
            i64 q = (i64)qf;
            i64 r = num - q * den;
            while (r < 0) { --q; r += den; }
            while (r >= den) { ++q; r -= den; }
            return q;
        }
    }
    i64 q = num / den;
    if (num - q * den < 0) --q;
    return q;
}

// Gauss reduction.  The iteration cap cannot bind on a form of
// discriminant -n (a Euclidean descent from below 2^47); it is there so
// that no arithmetic fault can hang a kernel.
__device__ __forceinline__ void reduce(i64 &a, i64 &b, i64 &c)
{
    for (int it = 0; it < 128; ++it) {
        if (a > c) { const i64 t = a; a = c; c = t; b = -b; }
        if (b > a || b <= -a) {
            i64 q = fdiv_near(b, a);
            i64 b2 = b - 2 * a * q;
            if (b2 == -a) { b2 = a; --q; }
            c = c - q * ((b + b2) >> 1);
            b = b2;
            continue;
        }
        if (a == c && b < 0) b = -b;
        return;
    }
}

__device__ __forceinline__ u64 inv64(const u64 a)
{   // the inverse of an odd a modulo 2^64 (Newton, 5 -> 80 bits)
    u64 x = (a * 3ull) ^ 2ull;
    x *= 2ull - a * x; x *= 2ull - a * x; x *= 2ull - a * x; x *= 2ull - a * x;
    return x;
}

// x mod p for EVERY u32 x and an odd p <= 251, pm = floor((2^32 - 1)/p):
// pm >= (2^32 - p)/p, so q = floor(x*pm/2^32) > x/p - 1 and the remainder
// needs one correction.  (Engine v3 took the quotient from a float, exact
// only while a < 2^23; this is exact to 2^32 and agrees with it below.)
__device__ __forceinline__ u32 umodp(const u32 x, const u32 p, const u32 pm)
{
    const u32 q = __umulhi(x, pm);
    u32 r = x - q * p;
    if (r >= p) r -= p;
    return r;
}

__device__ __forceinline__ u32 smodp(const i32 x, const u32 p, const u32 pm)
{   // x mod p in [0, p) for |x| < 2^31
    if (x >= 0) return umodp((u32)x, p, pm);
    const u32 r = umodp((u32)(-x), p, pm);
    return r ? p - r : 0u;
}

// g <- g o (p, beta, .), the prime form of norm p: Cohen 5.4.7 with
// a1 = p.  g reduced (a < 2^31, |b| <= a).  invt[x] = x^-1 mod p.
//   p !| a:               r = a^-1 (beta - b)/2 mod p
//   p | a, p !| s:        r = -s^-1 c mod p,  s = (beta + b)/2
//   p | a, p | s:         (a/p, b, c*p)
// and otherwise (a*p, b + 2ar, (c + r(b + ar))/p) with r centred, so
// |b + 2ar| <= a*p and every product stays below 2^62 (c < 2^60 for a
// reduced form of n < 2^62; r(b + ar) < 2^46).
__device__ __forceinline__ void cheap(i64 &a, i64 &b, i64 &c, const u32 p,
                                      const i32 beta, const u32 pm,
                                      const u64 pinv64,
                                      const unsigned char* invt)
{
    const u32 am = umodp((u32)a, p, pm);
    i64 r;
    if (am != 0u) {
        const u32 inv = invt[am];
        const u32 dm = smodp((beta - (i32)b) >> 1, p, pm);
        r = umodp(inv * dm, p, pm);
    } else {
        const u32 sm = smodp((beta + (i32)b) >> 1, p, pm);
        if (sm == 0u) {
            a = a / (i64)p; c = c * (i64)p;
            reduce(a, b, c);
            return;
        }
        const u32 x2 = invt[sm];
        const u32 cm = (u32)((u64)c % (u64)p);
        const u32 x = (x2 * cm) % p;
        r = (p - x) % p;
    }
    if (2 * r > (i64)p) r -= p;
    const i64 ar = a * r;
    const i64 X = c + r * (b + ar);
    c = (i64)((u64)X * pinv64);
    b = b + 2 * ar;
    a = a * (i64)p;
    reduce(a, b, c);
}

__device__ __forceinline__ void xgcd_u(const u32 a, const u32 b, i64 &u, u32 &d)
{   // u*a == d (mod b), d = gcd(a, b), b > 0
    i64 u0 = 1, u1 = 0;
    u32 r0 = a, r1 = b;
    while (r1) {
        const u32 q = r0 / r1;
        const u32 t = r0 - q * r1; r0 = r1; r1 = t;
        const i64 tu = u0 - (i64)q * u1; u0 = u1; u1 = tu;
    }
    u = u0; d = r0;
}

__device__ __forceinline__ i64 smod(const i64 x, const i64 v)
{
    if (x >= 0 && x < v) return x;
    i64 r = x % v;
    if (r < 0) r += v;
    return r;
}

// (A, B, C) <- (a1, b1, c1) o (a2, b2, c2), reduced inputs: Cohen 5.4.7.
__device__ __noinline__ void compose(i64 a1, i64 b1, i64 c1, i64 a2, i64 b2,
                                     i64 c2, const u64 n, i64 &A, i64 &B,
                                     i64 &C)
{
    if (a1 > a2) {
        i64 t = a1; a1 = a2; a2 = t;
        t = b1; b1 = b2; b2 = t;
        t = c1; c1 = c2; c2 = t;
    }
    const i64 s = (b1 + b2) >> 1;
    const i64 m = b2 - s;
    i64 y1; u32 d;
    if ((u32)a2 % (u32)a1 == 0) { y1 = 0; d = (u32)a1; }
    else xgcd_u((u32)a2, (u32)a1, y1, d);
    i64 y2 = -1, x2 = 0; u32 d1 = d;
    if (d != 1) {
        const u32 sa = (u32)(s < 0 ? -s : s);
        if (sa % d != 0) {
            i64 u;
            xgcd_u(sa, d, u, d1);
            const i64 v = ((i64)d1 - u * (i64)sa) / (i64)d;
            x2 = (s < 0) ? -u : u;
            y2 = -v;
        }
    }
    i64 v1 = a1, v2 = a2;
    if (d1 != 1) { v1 = a1 / (i64)d1; v2 = a2 / (i64)d1; }
    i64 r = smod(y1, v1);
    r = smod(r * smod(y2, v1), v1);
    r = smod(r * smod(m, v1), v1);
    if (x2 != 0) {
        const i64 w = smod(smod(x2, v1) * smod(c2, v1), v1);
        r = smod(r - w, v1);
    }
    B = b2 + 2 * v2 * r;
    A = v1 * v2;
    {
        const i64 q = fdiv_near(B, A);
        B -= 2 * A * q;
        if (B == -A) B = A;
    }
    // C = (B^2 + n) / (4A): exact, below 2^62, A odd
    const u64 x = (u64)B * (u64)B + n;
    C = (i64)(((x >> 2) * inv64((u64)A)) & 0x3FFFFFFFFFFFFFFFull);
    reduce(A, B, C);
}

__device__ __noinline__ void fpow(i64 ba, i64 bb, i64 bc, u32 e, const u64 n,
                                  i64 &A, i64 &B, i64 &C)
{
    i64 ga = 1, gb = 1, gc = (i64)((n + 1ull) >> 2);
    while (e) {
        if (e & 1u) compose(ga, gb, gc, ba, bb, bc, n, ga, gb, gc);
        e >>= 1;
        if (e) compose(ba, bb, bc, ba, bb, bc, n, ba, bb, bc);
    }
    A = ga; B = gb; C = gc;
}

// The key of a reduced form (a, b): INJECTIVE, or a hit would claim an
// order the group does not have.  Narrow (a < 2^23, i.e. n < 3*2^46):
// a*2^24 + (b mod 2^24), 47 bits, b in (-a, a] being determined mod 2a.
// Wide (a < 2^31, every n < 2^62): a*2^32 + (b mod 2^32), 63 bits.
__device__ __forceinline__ u64 fkey(const i64 a, const i64 b, const int wide)
{
    return wide ? (((u64)a << 32) | (u64)(u32)b)
                : (((u64)a << 24) | ((u64)b & 0xFFFFFFull));
}

// Narrow table: TS u64 per thread, an entry key << 17 | generation (10
// bits) << 7 | i (7 bits).  Wide table: TS slots of two u64 (the key; the
// generation << 7 | i), read as one 16-byte load.  An entry of another
// generation is an empty slot.
__device__ __forceinline__ void tins(u64* T, const u32 gen, const u64 key,
                                     const u32 i, const int wide)
{
    u32 h = (u32)((key * 0x9E3779B97F4A7C15ull) >> 56);
    if (!wide) {
        for (int it = 0; it < TS; ++it) {
            const u64 e = T[h];
            if ((u32)((e >> 7) & 1023u) != gen) {
                T[h] = (key << 17) | ((u64)gen << 7) | (u64)i;
                return;
            }
            if ((e >> 17) == key) return;      // keep the least i
            h = (h + 1) & (TS - 1);
        }
        return;
    }
    ulonglong2* W2 = reinterpret_cast<ulonglong2*>(T);
    for (int it = 0; it < TS; ++it) {
        const ulonglong2 e = W2[h];
        if ((u32)((e.y >> 7) & 1023u) != gen) {
            W2[h] = make_ulonglong2(key, ((u64)gen << 7) | (u64)i);
            return;
        }
        if (e.x == key) return;
        h = (h + 1) & (TS - 1);
    }
}

__device__ __forceinline__ int tget(const u64* T, const u32 gen, const u64 key,
                                    const int wide)
{
    u32 h = (u32)((key * 0x9E3779B97F4A7C15ull) >> 56);
    if (!wide) {
        for (int it = 0; it < TS; ++it) {
            const u64 e = T[h];
            if ((u32)((e >> 7) & 1023u) != gen) return -1;
            if ((e >> 17) == key) return (int)(e & 127u);
            h = (h + 1) & (TS - 1);
        }
        return -1;
    }
    const ulonglong2* W2 = reinterpret_cast<const ulonglong2*>(T);
    for (int it = 0; it < TS; ++it) {
        const ulonglong2 e = W2[h];
        if ((u32)((e.y >> 7) & 1023u) != gen) return -1;
        if (e.x == key) return (int)(e.y & 127u);
        h = (h + 1) & (TS - 1);
    }
    return -1;
}

__device__ __forceinline__ u64 montmul(const u64 a, const u64 b, const u64 c,
                                       const u64 np)
{
    const u64 lo = a * b, hi = __umul64hi(a, b);
    const u64 mm = lo * np;
    const u64 mh = __umul64hi(mm, c);
    u64 r = hi + mh + (lo != 0ull ? 1ull : 0ull);
    if (r >= c) r -= c;
    return r;
}

__device__ __noinline__ bool sprp2(const u64 c)
{   // strong probable prime to base 2; c odd, 2 < c < 2^62
    const u64 np = 0ull - inv64(c);
    const u64 one = ((~0ull) % c + 1ull) % c;        // 2^64 mod c
    u64 d = c - 1; int s = 0;
    while (!(d & 1ull)) { d >>= 1; ++s; }
    u64 x = one;                                     // 2^d, Montgomery form
    for (int bit = 63 - __clzll(d); bit >= 0; --bit) {
        x = montmul(x, x, c, np);
        if ((d >> bit) & 1ull) { x = x + x; if (x >= c) x -= c; }
    }
    const u64 minus1 = c - one;
    if (x == one || x == minus1) return true;
    for (int j = 1; j < s; ++j) {
        x = montmul(x, x, c, np);
        if (x == minus1) return true;
    }
    return false;
}

struct Setup { u32 t; u32 ng; u64 need; u64 gp; u64 gb; u64 d; };

__device__ __forceinline__ int legendre_u(const u64 x, const u64 p)
{   // (x | p) for the odd prime p < 2^23, p !| x: Euler's criterion
    u64 b = x % p, r = 1ull, e = (p - 1ull) >> 1;
    while (e) {
        if (e & 1ull) r = r * b % p;
        e >>= 1;
        if (e) b = b * b % p;
    }
    return r == 1ull ? 1 : -1;
}

// n = d f^2, d squarefree (-d the fundamental discriminant).  t: a lower
// bound of the number of distinct primes dividing d; Sf: the Hurwitz
// conductor factor S(f) = prod_{p^e || f} (1 + (p - (-d|p))(p^e - 1)/(p - 1)),
// so that T(n) = 3 h(-d) S(f) for d > 3; need: the least L with which the
// survivor rule drops the count 3 L S(f) (the classify kernel's doubles),
// so that h(-d) >= need drops n; the first NGENS primes <= 251 split for
// -d, as indices (gp) and odd roots (gb).  d = 3 is the caller's to refuse.
__device__ __forceinline__ void setup(const u64 n, const double f2,
        const double pi_up, const double rho_large, const int np1,
        const u32* tp, const u64* tinv, const u64* tlim, const u64* smu,
        const u32* soff, const unsigned char* sqt, const double* sinv,
        const double* qram, const double* qspl, Setup &S)
{
    u32 t = 0; u64 c = n, d = 1ull, Sf = 1ull; double rho = rho_large;
    for (int j = 0; j < np1; ++j) {
        if (n * tinv[j] <= tlim[j]) {            // tp[j] divides n
            const u64 p = tp[j];
            int e = 0;
            while (c % p == 0ull) { c /= p; ++e; }
            if (e & 1) { d *= p; ++t; }
            if (e >= 2) {
                if (j < NSMALL) rho = rho * sinv[j];
                int chi = 0;                      // (-d | p)
                if (!(e & 1)) {
                    u64 u = n;
                    for (int k = 0; k < e; ++k) u /= p;
                    const u64 um = u % p;
                    chi = legendre_u(p - um, p);  // (-d|p) = (-n/p^e | p)
                }
                u64 g = 0ull, pk = 1ull;          // (p^(e/2) - 1)/(p - 1)
                for (int k = 0; k < (e >> 1); ++k) { g += pk; pk *= p; }
                Sf *= 1ull + (u64)((i64)p - chi) * g;
            }
        }
    }
    if (c > 1ull) {
        u64 r = (u64)sqrt((double)c);           // within one of the root
        while (r * r > c) --r;
        while ((r + 1) * (r + 1) <= c) ++r;
        if (r * r == c) {                         // r^2 || n, r prime
            const u64 um = (n / c) % r;
            Sf *= 1ull + (u64)((i64)r - legendre_u(r - um, r));
        } else { d *= c; t += sprp2(c) ? 1 : 2; }
    }
    // the split primes of -d (the forms), and Q(n) -- the characters of
    // -n, as localq() takes them
    u32 ng = 0; u64 gp = 0, gb = 0;
    double Q = 1.0;
    for (int j = 0; j < NSMALL; ++j) {
        const u32 pp = tp[j];
        const u64 qq = __umul64hi(n, smu[j]);
        u32 nm = (u32)(n - qq * pp);
        if (nm >= pp) nm -= pp;
        const u32 rr = nm ? pp - nm : 0u;            // (-n) mod p
        if (rr == 0u) Q = Q * qram[j];
        else if (sqt[soff[j] + rr]) Q = Q * qspl[j];
        u32 rd = rr;
        if (d != n) {
            const u64 qd = __umul64hi(d, smu[j]);
            u32 dm = (u32)(d - qd * pp);
            if (dm >= pp) dm -= pp;
            rd = dm ? pp - dm : 0u;                  // (-d) mod p
        }
        const u32 bb = sqt[soff[j] + rd];            // its odd root, or 0
        if (bb && ng < NGENS) {
            gp |= (u64)j << (8 * ng);
            gb |= (u64)bb << (8 * ng);
            ++ng;
        }
    }
    Q = Q * QPAD;
    const double R = (pi_up * sqrt((double)n)) * Q;
    u64 need = (u64)(R / (3.0 * f2 * rho * (double)Sf));
    if (need < 1ull) need = 1ull;
    while (((double)(3ull * need * Sf) * f2) * rho < R) ++need;
    while (need > 1ull
           && !(((double)(3ull * (need - 1ull) * Sf) * f2) * rho < R))
        --need;
    S.t = t; S.ng = ng; S.need = need; S.gp = gp; S.gb = gb; S.d = d;
}

// the step sizes of a base form's table: sp giant steps F^-i tabled,
// s prime steps walked, s*sp >= need1 - 1.
__device__ __forceinline__ void steps(const u64 need1, u32 &sp, u32 &s)
{
    const u64 xr = need1 / RATIO;
    u64 q = (u64)sqrtf((float)xr);
    while (q * q > xr) --q;
    while ((q + 1) * (q + 1) <= xr) ++q;
    sp = (u32)q;
    if (sp < 1u) sp = 1u;
    if (sp > SP_MAX) sp = SP_MAX;
    s = (u32)((need1 - 1ull + sp - 1ull) / sp);
    if (s < 1u) s = 1u;
}

__device__ __forceinline__ void prime_form(const u64 n, const u32 p,
                                           const i32 beta, i64 &a, i64 &b,
                                           i64 &c)
{
    a = p; b = beta;
    c = (i64)(((u64)beta * (u64)beta + n) / (4ull * p));
    reduce(a, b, c);
}

// the table {F^-i : 0 <= i < sp}, F = f^s
__device__ __forceinline__ void build(u64* T, const u32 gen, const u64 n,
                                      const i64 fa, const i64 fb, const i64 fc,
                                      const u32 s, const u32 sp,
                                      const int wide)
{
    i64 ia, ib, ic;
    fpow(fa, fb, fc, s, n, ia, ib, ic);
    ib = -ib;
    if (ib == -ia || (ia == ic && ib < 0)) ib = -ib;
    i64 Ea = 1, Eb = 1, Ec = (i64)((n + 1ull) >> 2);
    for (u32 k = 0; k < sp; ++k) {
        tins(T, gen, fkey(Ea, Eb, wide), k, wide);
        if (k + 1 < sp) compose(Ea, Eb, Ec, ia, ib, ic, n, Ea, Eb, Ec);
    }
}

#define PRE_ARGS const double f2, const double pi_up, const double rho_large, \
    const int np1, const u32* tp, const u64* tinv, const u64* tlim, \
    const u64* smu, const u32* soff, const unsigned char* sqt, \
    const unsigned char* invt, const double* sinv, \
    const u64* spinv64, const double* qram, const double* qspl

// PASS 1: the order of the base-th prime form.
// out[q]: 0 = h(-n) >= need PROVED (dropped); 1 = no decision (tabulate);
//         m1 + 2 = the exact order m1 < need1 of the base form.
extern "C" __global__
void pre1(const u64 m0, const u32 count, const u32* list, const u32 nthr,
          const int base, const int wide, PRE_ARGS, u64* tbl, u32* out)
{
    const u32 tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= nthr) return;
    const int tw = wide ? 2 * TS : TS;
    u64* T = tbl + (u64)tid * tw;
    for (int i = 0; i < tw; ++i) T[i] = 0ull;
    u32 gen = 0;
    for (u32 q = tid; q < count; q += nthr) {
        const u32 i = list ? list[q] : q;
        const u64 n = 8ull * (m0 + (u64)i) + 3ull;
        ++gen;
        Setup S;
        setup(n, f2, pi_up, rho_large, np1, tp, tinv, tlim, smu, soff, sqt,
              sinv, qram, qspl, S);
        if (S.d == 3ull) { out[q] = 1u; continue; }  // T = S(f), count it
        if (S.need <= 1ull) { out[q] = 0u; continue; }
        if ((u32)base >= S.ng) { out[q] = 1u; continue; }
        const u32 sh = S.t <= 1u ? 0u : S.t - 2u;
        const u64 need1 = (S.need + ((1ull << sh) - 1ull)) >> sh;
        if (need1 <= 1ull) { out[q] = 0u; continue; }
        if (need1 > NEED_MAX) { out[q] = 1u; continue; }
        u32 sp, s;
        steps(need1, sp, s);
        const int pj = (int)((S.gp >> (8 * base)) & 255ull);
        const u32 p = tp[pj];
        const i32 beta = (i32)((S.gb >> (8 * base)) & 255ull);
        const u32 pm = 0xFFFFFFFFu / p;
        const u64 pinv64 = spinv64[pj];
        const unsigned char* inv = invt + soff[pj];
        i64 fa, fb, fc;
        prime_form(S.d, p, beta, fa, fb, fc);
        build(T, gen, S.d, fa, fb, fc, s, sp, wide);
        // f^r = F^-i  <=>  f^(r + s*i) = 1; every exponent in [1, s*sp]
        // is r + s*i once, so the least hit is the order.
        u32 best = 0;
        i64 ga = fa, gb = fb, gc = fc;
        for (u32 r = 1; r <= s; ++r) {
            const int k = tget(T, gen, fkey(ga, gb, wide), wide);
            if (k >= 0) {
                const u32 j = r + s * (u32)k;
                if (!best || j < best) best = j;
            }
            if (r < s) cheap(ga, gb, gc, p, beta, pm, pinv64, inv);
        }
        out[q] = (best && (u64)best < need1) ? best + 2u : 0u;
    }
}

// PASS 2, for the n whose base form has order m1 < need1 (m1in = m1 + 2).
// mode 0: bound (2), then bound (3) through ord((g^2)^m') for each other
//         prime form g.     out: 0 dropped, 2 index too large for this
//         base, 3 undecided.
// mode 1: bound (3) itself: (g^2)^e not in <f^2> for 1 <= e < need2, a
//         discrete logarithm in <f> by the base form's table.
//         out: 0 dropped, 1 undecided.
extern "C" __global__
void pre2(const u64 m0, const u32 count, const u32* list, const u32* m1in,
          const u32 nthr, const int base, const int mode, const int wide,
          PRE_ARGS, u64* tbl, u32* out)
{
    const u32 tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= nthr) return;
    const int tw = wide ? 2 * TS : TS;
    u64* T = tbl + (u64)tid * tw;
    if (mode) for (int i = 0; i < tw; ++i) T[i] = 0ull;
    u32 gen = 0;
    for (u32 q = tid; q < count; q += nthr) {
        const u32 i = list[q];
        const u64 n = 8ull * (m0 + (u64)i) + 3ull;
        ++gen;
        Setup S;
        setup(n, f2, pi_up, rho_large, np1, tp, tinv, tlim, smu, soff, sqt,
              sinv, qram, qspl, S);
        const u32 m1 = m1in[q] - 2u;
        const u32 mp = (m1 & 1u) ? m1 : (m1 >> 1);
        const u32 g2s = S.t >= 1u ? S.t - 1u : 0u;
        const u64 G2mp = (u64)mp << g2s;
        if (G2mp >= S.need) { out[q] = 0u; continue; }
        const u64 need2 = (S.need + G2mp - 1ull) / G2mp;
        if (need2 > CAP2) { out[q] = 2u; continue; }
        bool ok = false;
        if (mode == 0) {
            for (u32 j = 0; j < S.ng && !ok; ++j) {
                if ((int)j == base) continue;
                const u32 p = tp[(S.gp >> (8 * j)) & 255ull];
                const i32 beta = (i32)((S.gb >> (8 * j)) & 255ull);
                i64 a, b, c, ua, ub, uc;
                prime_form(S.d, p, beta, a, b, c);
                compose(a, b, c, a, b, c, S.d, a, b, c);
                fpow(a, b, c, mp, S.d, ua, ub, uc);
                i64 wa = ua, wb = ub, wc = uc;
                bool good = true;
                for (u64 e = 1; e < need2; ++e) {
                    if (wa == 1) { good = false; break; }
                    compose(wa, wb, wc, ua, ub, uc, S.d, wa, wb, wc);
                }
                ok = good;
            }
            out[q] = ok ? 0u : 3u;
            continue;
        }
        // the discrete logarithm in <f> needs exponents below ord(f) = m1
        // only (pass 1 found the EXACT order m1 < need1): every element of
        // <f> is f^-u for exactly one u in [0, m1), and every hit gives the
        // same u mod m1, so the parity verdict is the one a search sized by
        // need1 reaches.  hlc_search._in_squares sizes it by m1 too.
        // (engine v4: steps(need1, ...); v4.1 walks m1/need1 as far)
        u32 sp, s;
        steps((u64)m1 + 1ull, sp, s);
        const int pj = (int)((S.gp >> (8 * base)) & 255ull);
        const u32 p1 = tp[pj];
        const i32 beta1 = (i32)((S.gb >> (8 * base)) & 255ull);
        const u32 pm = 0xFFFFFFFFu / p1;
        const u64 pinv64 = spinv64[pj];
        const unsigned char* inv = invt + soff[pj];
        i64 fa, fb, fc;
        prime_form(S.d, p1, beta1, fa, fb, fc);
        build(T, gen, S.d, fa, fb, fc, s, sp, wide);
        for (u32 j = 0; j < S.ng && !ok; ++j) {
            if ((int)j == base) continue;
            const u32 p = tp[(S.gp >> (8 * j)) & 255ull];
            const i32 beta = (i32)((S.gb >> (8 * j)) & 255ull);
            i64 ga, gb, gc;
            prime_form(S.d, p, beta, ga, gb, gc);
            compose(ga, gb, gc, ga, gb, gc, S.d, ga, gb, gc);
            i64 wa = ga, wb = gb, wc = gc;
            bool good = true;
            for (u64 e = 1; e < need2 && good; ++e) {
                // w = f^-(r + s*k) for some r < s, k < sp, or w not in <f>
                i64 va = wa, vb = wb, vc = wc;
                for (u32 r = 0; r < s; ++r) {
                    const int k = tget(T, gen, fkey(va, vb, wide), wide);
                    if (k >= 0) {
                        if ((m1 & 1u) || !((r + s * (u32)k) & 1u)) good = false;
                        break;
                    }
                    if (r + 1 < s) cheap(va, vb, vc, p1, beta1, pm, pinv64, inv);
                }
                if (good && e + 1 < need2)
                    compose(wa, wb, wc, ga, gb, gc, S.d, wa, wb, wc);
            }
            ok = good;
        }
        out[q] = ok ? 0u : 1u;
    }
}

// ================================================ the sparse exact count
// One n per block of SPB threads; blocks take n from a queue (qctr).
// pr: the odd primes below SP_PMAX ascending; mu[j] = floor(2^64/pr[j]);
// pinv[j] = pr[j]^-1 mod 2^32 (exact division); spf[x >> 1] = the index in
// pr of the least prime factor of the odd x >= 3.  bits (shared): bit j set
// iff (-n | pr[j]) = +1; the primes dividing n go to a shared list instead
// (p, v = v_p(n), [(-u | p) = +1], u = n / p^v).
#define SPB @SPB@
#define NDL 16

__device__ __forceinline__ u32 mulm(const u32 a, const u32 b, const u32 p,
                                    const u64 mu)
{   // a*b mod p for a, b < p < 2^23: q is floor(ab/p) or one less
    const u64 x = (u64)a * (u64)b;
    const u64 q = __umul64hi(x, mu);
    u64 r = x - q * (u64)p;
    if (r >= p) r -= p;
    return (u32)r;
}

__device__ __forceinline__ u32 modn(const u64 n, const u32 p, const u64 mu)
{   // n mod p
    const u64 q = __umul64hi(n, mu);
    u64 r = n - q * (u64)p;
    while (r >= p) r -= p;
    return (u32)r;
}

__device__ u32 powm(u32 b, u32 e, const u32 p, const u64 mu)
{
    u32 r = 1u;
    while (e) {
        if (e & 1u) r = mulm(r, b, p, mu);
        e >>= 1;
        if (e) b = mulm(b, b, p, mu);
    }
    return r;
}

__device__ u32 sqrtm(const u32 r, const u32 p, const u64 mu)
{   // a square root of the quadratic residue r != 0 modulo the odd prime p
    // (Tonelli-Shanks; p == 3 mod 4 by one power)
    if ((p & 3u) == 3u) return powm(r, (p + 1u) >> 2, p, mu);
    u32 Q = p - 1u, S = 0;
    while (!(Q & 1u)) { Q >>= 1; ++S; }
    u32 z = 2u;
    while (powm(z, (p - 1u) >> 1, p, mu) != p - 1u) ++z;
    u32 M = S, c = powm(z, Q, p, mu), t = powm(r, Q, p, mu);
    u32 R = powm(r, (Q + 1u) >> 1, p, mu);
    while (t != 1u) {
        u32 i = 0, tt = t;
        while (tt != 1u) { tt = mulm(tt, tt, p, mu); ++i; }
        u32 b = c;
        for (u32 j = 0; j + 1u < M - i; ++j) b = mulm(b, b, p, mu);
        M = i; c = mulm(b, b, p, mu); t = mulm(t, c, p, mu);
        R = mulm(R, b, p, mu);
    }
    return R;
}

__device__ u64 minv(const u64 x, const u64 m)
{   // x^-1 mod m, gcd(x, m) = 1, m < 2^23
    i64 a = (i64)(x % m), b = (i64)m, u = 1, v = 0;
    while (b) {
        const i64 q = a / b;
        i64 t = a - q * b; a = b; b = t;
        t = u - q * v; u = v; v = t;
    }
    if (u < 0) u += (i64)m;
    return (u64)u;
}

__device__ u32 hensel(u32 s, const u32 p, const u32 e, const u64 nn)
{   // s^2 = -nn (mod p), p odd, p !| nn  ->  the root mod p^e above s
    u64 m = p;
    for (u32 k = 1; k < e; ++k) {
        m *= p;
        const u64 f = ((u64)s * (u64)s + nn % m) % m;
        const u64 iv = minv((2ull * s) % m, m);
        s = (u32)(((u64)s + m - (f * iv) % m) % m);
    }
    return s;
}

__device__ __forceinline__ u32 ipow(const u32 p, u32 e)
{
    u32 r = 1u;
    while (e--) r *= p;
    return r;
}

__device__ __forceinline__ u32 nprimes(const u32* pr, const u32 npr,
                                       const u32 x)
{   // the number of entries of pr that are <= x
    u32 lo = 0, hi = npr;
    while (lo < hi) {
        const u32 mid = (lo + hi) >> 1;
        if (pr[mid] <= x) lo = mid + 1; else hi = mid;
    }
    return lo;
}

__device__ __forceinline__ u64 isqrt64(const u64 n)
{
    u64 r = (u64)sqrt((double)n);
    while (r * r > n) --r;
    while ((r + 1) * (r + 1) <= n) ++r;
    return r;
}

// the characters of the primes with index in [j0, j1)
__device__ __forceinline__ void chi_range(const u64 n, const u32 j0,
        const u32 j1, const u32* pr, const u64* mu, u32* bits, u32* dlp,
        u32* dlv, u32* dlc, u64* dlu, u32* ndl)
{
    for (u32 j = j0 + threadIdx.x; j < j1; j += SPB) {
        const u32 p = pr[j];
        const u64 m = mu[j];
        const u32 nm = modn(n, p, m);
        if (nm == 0u) {
            u64 u = n; u32 v = 0;
            while (u % p == 0ull) { u /= p; ++v; }
            const u32 um = modn(u, p, m);
            const u32 c = powm(p - um, (p - 1u) >> 1, p, m) == 1u ? 1u : 0u;
            const u32 k = atomicAdd(ndl, 1u);
            if (k < NDL) { dlp[k] = p; dlv[k] = v; dlc[k] = c; dlu[k] = u; }
            continue;
        }
        if (powm(p - nm, (p - 1u) >> 1, p, m) == 1u)
            atomicOr(bits + (j >> 5), 1u << (j & 31u));
    }
}

// The character of -n at the prime pr[j] past the shared bitmap (j >= jb:
// engine v4, once the primes below isqrt(n/3) outgrow 48 KB of bits, from
// k ~ 2.3*10^13): 0 split, 2 inert, 1 p | n with v = v_p(n), u = n / p^v
// and c = [(-u | p) = +1] -- what chi_range records for the primes it
// covers.  Each a past the bitmap has at most one such prime (a < jb-th
// prime squared), so this costs one Euler criterion where a lookup was.
__device__ __forceinline__ u32 chi_one(const u64 n, const u32 p, const u64 m,
                                       u32 &v, u32 &c, u64 &u)
{
    const u32 nm = modn(n, p, m);
    if (nm) return powm(p - nm, (p - 1u) >> 1, p, m) == 1u ? 0u : 2u;
    u = n; v = 0u;
    while (u % p == 0ull) { u /= p; ++v; }
    c = powm(p - modn(u, p, m), (p - 1u) >> 1, p, m) == 1u ? 1u : 0u;
    return 1u;
}

// N(x): the number of square roots of -n modulo the odd x
__device__ __forceinline__ u32 nroots(u32 x, const u64 n, const u32* pr,
        const u64* mu, const u32* pinv, const u32* spf, const u32* bits,
        const u32 jb, const u32* dlp, const u32* dlv, const u32* dlc,
        const u32 nd)
{
    u32 N = 1u;
    while (x > 1u) {
        const u32 j = spf[x >> 1];
        const u32 p = pr[j];
        const u32 pi = pinv[j];
        u32 e = 0;
        do { x *= pi; ++e; } while (x > 1u && spf[x >> 1] == j);
        u32 v, c;
        if (j < jb) {
            if ((bits[j >> 5] >> (j & 31u)) & 1u) { N <<= 1; continue; }
            int k = -1;
            for (u32 t = 0; t < nd; ++t) if (dlp[t] == p) { k = (int)t; break; }
            if (k < 0) return 0u;                     // p inert
            v = dlv[k]; c = dlc[k];
        } else {
            u64 u;
            const u32 kind = chi_one(n, p, mu[j], v, c, u);
            if (kind == 0u) { N <<= 1; continue; }
            if (kind == 2u) return 0u;
        }
        if (e <= v) N *= ipow(p, e >> 1);
        else if ((v & 1u) || !c) return 0u;
        else N *= 2u * ipow(p, v >> 1);
    }
    return N;
}

__device__ __forceinline__ u64 bsum(u64 s, u64* red)
{   // the block's sum, returned to every thread
    for (int o = 16; o; o >>= 1) s += __shfl_down_sync(0xffffffffu, s, o);
    __syncthreads();
    if ((threadIdx.x & 31) == 0) red[threadIdx.x >> 5] = s;
    __syncthreads();
    u64 t = 0;
    for (int w = 0; w < SPB / 32; ++w) t += red[w];
    return t;
}

// PHASE A.  stat[q] = 0: the rule drops n on a prefix of the count (a
// proved lower bound of T); 1: undecided after every a <= A, and then
// outA[q] = 3 * sum_{odd a <= A} N(a) exactly.  f2 = 0 never drops.
extern "C" __global__
void spa(const u64 m0, const u32* list, const u32 count, u32* qctr,
         const double f2, const double pi_up, const double rho_min,
         const double rho_large, const int np, const u32* p2,
         const double* inv, const u32* pr, const u32 npr, const u64* mu,
         const u32* pinv, const u32* spf, const u32 nwords, const u32 jb,
         const int nchunk, const u32* tp, const u64* smu, const u32* soff,
         const unsigned char* sqt, const double* qram, const double* qspl,
         u64* outA, u32* stat)
{
    extern __shared__ u32 bits[];
    __shared__ u32 item, ndl, dlp[NDL], dlv[NDL], dlc[NDL];
    __shared__ u64 dlu[NDL], red[SPB / 32];
    for (;;) {
        if (threadIdx.x == 0) { item = atomicAdd(qctr, 1u); ndl = 0u; }
        for (u32 w = threadIdx.x; w < nwords; w += SPB) bits[w] = 0u;
        __syncthreads();
        const u32 q = item;
        if (q >= count) return;
        const u64 n = 8ull * (m0 + (u64)list[q]) + 3ull;
        const u32 A = (u32)(isqrt64(n) >> 1);
        const double R = (pi_up * sqrt((double)n))    // as classify()
                         * localq(n, tp, smu, soff, sqt, qram, qspl);
        double rho = rho_large;
        for (int j = 0; j < np; ++j)
            if (n % (u64)p2[j] == 0ull) rho = rho * inv[j];
        u64 S = 0;
        u32 alo = 1u, plo = 0u, st = 1u;
        for (int ch = 1; ch <= nchunk; ++ch) {
            const u32 ahi = (u32)(((u64)A * (u64)ch) / (u64)nchunk);
            if (ahi < alo) continue;
            const u32 phi = nprimes(pr, npr, ahi);
            chi_range(n, plo < jb ? plo : jb, phi < jb ? phi : jb, pr, mu,
                      bits, dlp, dlv, dlc, dlu, &ndl);
            __syncthreads();
            const u32 nd = ndl < NDL ? ndl : NDL;
            u64 s = 0;
            for (u32 a = alo + 2u * threadIdx.x; a <= ahi; a += 2u * SPB)
                s += nroots(a, n, pr, mu, pinv, spf, bits, jb, dlp, dlv, dlc,
                            nd);
            S += bsum(s, red);
            const double Ad = (double)(3ull * S) * f2;
            alo = ahi + 1u + (ahi & 1u);
            plo = phi;
            if (!(Ad * rho_min < R && Ad * rho < R)) { st = 0u; break; }
        }
        if (threadIdx.x == 0) { stat[q] = st; outA[q] = 3ull * S; }
        __syncthreads();
    }
}

// PHASE B.  outT[q] = inA[q] + 3 x (1 for a = b = c) the reduced forms of
// the band A < a <= isqrt(n/3): T(n) exactly.
extern "C" __global__
void spb(const u64 m0, const u32* list, const u32 count, u32* qctr,
         const u64* inA, const u32* pr, const u32 npr, const u64* mu,
         const u32* pinv, const u32* spf, const u32 nwords, const u32 jb,
         u64* outT)
{
    extern __shared__ u32 bits[];
    __shared__ u32 item, ndl, dlp[NDL], dlv[NDL], dlc[NDL];
    __shared__ u64 dlu[NDL], red[SPB / 32];
    for (;;) {
        if (threadIdx.x == 0) { item = atomicAdd(qctr, 1u); ndl = 0u; }
        for (u32 w = threadIdx.x; w < nwords; w += SPB) bits[w] = 0u;
        __syncthreads();
        const u32 q = item;
        if (q >= count) return;
        const u64 n = 8ull * (m0 + (u64)list[q]) + 3ull;
        const u32 A = (u32)(isqrt64(n) >> 1);
        const u32 X = (u32)isqrt64(n / 3ull);
        const u32 pX = nprimes(pr, npr, X);
        chi_range(n, 0u, pX < jb ? pX : jb, pr, mu, bits, dlp, dlv, dlc,
                  dlu, &ndl);
        __syncthreads();
        const u32 nd = ndl < NDL ? ndl : NDL;
        u64 s = 0;
        for (u32 a = A + 1u + (A & 1u) + 2u * threadIdx.x; a <= X;
             a += 2u * SPB) {
            // a's prime powers and their root sets:
            //   type 0, p !| n: {r, p^e - r}, r Tonelli-Shanks then Hensel
            //   type 1, p^e | n (e <= v): {i * p^ceil(e/2)}, p^(e/2) of them
            //   type 2, e > v even: {p^(v/2) (+-t + i p^(e-v))}, t^2 = -u
            u32 fm[8], fty[8], fsz[8], fs[8], fb[8], fpe[8];
            u32 nf = 0, x = a, total = 1u;
            bool zero = false;
            while (x > 1u) {
                const u32 j = spf[x >> 1];
                const u32 p = pr[j];
                const u32 pi = pinv[j];
                u32 e = 0, m = 1u;
                do { x *= pi; ++e; m *= p; } while (x > 1u && spf[x >> 1] == j);
                fm[nf] = m;
                // the character: from the bitmap and the list of primes
                // dividing n, or (past the bitmap) computed now
                u32 kind, v = 0u, chu = 0u;     // 0 split, 1 p | n, 2 inert
                u64 u = 0ull;
                if (j < jb) {
                    if ((bits[j >> 5] >> (j & 31u)) & 1u) kind = 0u;
                    else {
                        int k = -1;
                        for (u32 t = 0; t < nd; ++t)
                            if (dlp[t] == p) { k = (int)t; break; }
                        if (k < 0) kind = 2u;
                        else { kind = 1u; v = dlv[k]; chu = dlc[k]; u = dlu[k]; }
                    }
                } else {
                    kind = chi_one(n, p, mu[j], v, chu, u);
                }
                if (kind == 0u) {
                    u32 r = sqrtm(p - modn(n, p, mu[j]), p, mu[j]);
                    if (e > 1u) r = hensel(r, p, e, n);
                    fty[nf] = 0u; fsz[nf] = 2u; fs[nf] = r;
                } else {
                    if (kind == 2u) { zero = true; break; }
                    if (e <= v) {
                        fty[nf] = 1u; fsz[nf] = ipow(p, e >> 1);
                        fb[nf] = ipow(p, (e + 1u) >> 1);
                    } else if ((v & 1u) || !chu) { zero = true; break; }
                    else {
                        u32 t = sqrtm(p - modn(u, p, mu[j]), p, mu[j]);
                        if (e - v > 1u) t = hensel(t, p, e - v, u);
                        fty[nf] = 2u; fsz[nf] = 2u * ipow(p, v >> 1);
                        fs[nf] = t; fb[nf] = ipow(p, v >> 1);
                        fpe[nf] = ipow(p, e - v);
                    }
                }
                total *= fsz[nf];
                ++nf;
            }
            if (zero) continue;
            u64 cc[8];                                // CRT coefficients
            for (u32 i = 0; i < nf; ++i) {
                const u64 Mi = a / fm[i];
                cc[i] = (Mi * minv(Mi % fm[i], fm[i])) % a;
            }
            const i64 fa = 4 * (i64)a * (i64)a;
            for (u32 idx = 0; idx < total; ++idx) {
                u32 tq = idx;
                u64 r = 0;
                for (u32 i = 0; i < nf; ++i) {
                    const u32 jj = tq % fsz[i];
                    tq /= fsz[i];
                    u64 root;
                    if (fty[i] == 0u) root = jj ? fm[i] - fs[i] : fs[i];
                    else if (fty[i] == 1u) root = (u64)jj * fb[i];
                    else {
                        const u64 sv = (u64)((jj & 1u) ? fpe[i] - fs[i] : fs[i])
                                       + (u64)(jj >> 1) * fpe[i];
                        root = (fb[i] * sv) % fm[i];
                    }
                    r = (r + root * cc[i]) % a;
                }
                // the odd representative of r in (-a, a]; c >= a iff
                // b^2 + n >= 4a^2, and c = a needs b >= 0
                const i64 b = r == 0ull ? (i64)a
                              : ((r & 1ull) ? (i64)r : (i64)r - (i64)a);
                const i64 lhs = b * b + (i64)n;
                if (lhs > fa) s += 3ull;
                else if (lhs == fa && b >= 0) s += (b == (i64)a) ? 1ull : 3ull;
            }
        }
        const u64 band = bsum(s, red);
        if (threadIdx.x == 0) outT[q] = inA[q] + band;
        __syncthreads();
    }
}
'''

_cp = None


def _cupy():
    global _cp
    if _cp is None:
        import cupy
        _cp = cupy
    return _cp


def available():
    try:
        cp = _cupy()
        return cp.cuda.runtime.getDeviceCount() > 0
    except Exception:
        return False


def k_ceil():
    """The enforced ceiling on k, and where it comes from.

    A primality-certificate ceiling does not apply: nothing here is a
    primality claim.  What bounds the hunt is the arithmetic above: every
    product of the prefilter and the sparse count fits 64 bits for n <
    2^62 (engine v4; v3 stopped at 2^46, where the form-table key, the
    character bitmap and the float quotients ran out).  10^18 sits inside
    it, and is no limit a campaign will meet: the sweep costs about k^1.4
    (BENCHMARKS.md has the measured clocks) -- 10^13 is twelve days, 10^14
    most of a year.  Past WALK_MAX_N (k ~ 2.25*10^15) the three-squares
    walk refuses, so the recount says so and the confirmations rest on the
    analytic class number."""
    return K_CEIL


def source():
    """The kernel source: the three-squares walk (every counter), the
    prefilter and the sparse count, with their constants baked in."""
    tab = _WALK.replace("@NAME@", "tab").replace("@FLAGPARAM@", "")
    src = _SRC.replace("@TAB@", tab)
    for key, val in (("@SPB@", SP_THREADS),
                     ("@QPAD@", repr(Q_PAD)),
                     ("@NSMALL@", len(SMALLP)), ("@SP_MAX@", PRE_SP_MAX),
                     ("@RATIO@", PRE_RATIO), ("@CAP2@", PRE_CAP2),
                     ("@NGENS@", PRE_NGENS), ("@NEED_MAX@", PRE_NEED_MAX)):
        src = src.replace(key, str(val))
    return src


def _isqrt_arr(v, xp=np):
    r = xp.floor(xp.sqrt(v.astype(xp.float64))).astype(xp.int64)
    r = xp.where(r * r > v, r - 1, r)
    r = xp.where((r + 1) * (r + 1) <= v, r + 1, r)
    return r


def plan(m0, W, ch=CH, xp=np):
    """The (x, y-range) rows of a window and the prefix of thread counts.

    Row x holds the odd y <= x for which SOME odd z in [1, y] can land in
    the window: x^2 + y^2 + 1 <= nmax and x^2 + 2*y^2 >= n0.  A row that
    is too generous costs idle threads, never a missed representation; a
    row that is too tight would, so both bounds are exact integer roots.
    xp is numpy or cupy (the production path plans on the device).
    """
    m0, W = int(m0), int(W)
    n0 = 8 * m0 + 3
    nmax = 8 * (m0 + W - 1) + 3
    if nmax >= WALK_MAX_N:
        raise ValueError(f"4k - 1 = {nmax} is past the walk's bound 2^53 "
                         f"(u32 counters)")
    xhi = math.isqrt(nmax - 2)
    xhi -= 1 - (xhi % 2)
    xlo = math.isqrt(n0 // 3)
    while 3 * xlo * xlo < n0:
        xlo += 1
    xlo = max(1, xlo - 1)
    xlo -= 1 - (xlo % 2)
    xlo = max(1, xlo)
    xs = xp.arange(xlo, xhi + 1, 2, dtype=xp.int64)
    x2 = xs * xs
    room = nmax - 1 - x2
    ymax = xp.minimum(xs, _isqrt_arr(xp.maximum(room, 0), xp))
    ymax = xp.where(room < 1, 0, ymax)
    ymax = ymax - (1 - (ymax % 2))
    half = xp.maximum((n0 - x2 + 1) // 2, 0)
    ymin = _isqrt_arr(half, xp)
    ymin = xp.where(ymin * ymin < half, ymin + 1, ymin)
    ymin = xp.maximum(ymin, 1)
    ymin = ymin + (1 - (ymin % 2))
    ny = xp.where(ymax >= ymin, (ymax - ymin) // 2 + 1, 0)
    keep = ny > 0
    xs, ymin, ny = xs[keep], ymin[keep], ny[keep]
    pref = xp.zeros(len(xs) + 1, dtype=xp.uint64)
    pref[1:] = xp.cumsum((ny + ch - 1) // ch)
    return (n0, nmax, xs.astype(xp.uint32), ymin.astype(xp.uint32),
            ny.astype(xp.uint32), pref)


def _primes_to(N):
    s = bytearray([1]) * (N + 1)
    s[0:2] = b"\0\0"
    for i in range(2, math.isqrt(N) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(3, N + 1) if s[i]]


def _icbrt_up(n):
    """The least integer P with P^3 > n."""
    P = int(round(n ** (1.0 / 3.0)))
    while P * P * P > n:
        P -= 1
    while P * P * P <= n:
        P += 1
    return P


def sparse_tables(pmax=SP_PMAX):
    """(pr, mu, pinv, spf) for the sparse count: the odd primes below pmax,
    floor(2^64/p), p^-1 mod 2^32, and for every odd x <= pmax (index
    x >> 1) the index in pr of its least prime factor (0 at x = 1).
    Built in u32 and vectorised (engine v4: the tables grow with the
    height, to 1.2e9 at 2^62); identical to v3's tables at v3's size."""
    s = np.ones(pmax + 1, dtype=bool)
    s[:2] = False
    s[4::2] = False
    for i in range(3, math.isqrt(pmax) + 1, 2):
        if s[i]:
            s[i * i::2 * i] = False
    pr = np.nonzero(s)[0]
    del s
    pr = pr[pr > 2]
    nodd = (pmax + 1) // 2
    unset = np.uint32(0xFFFFFFFF)
    spf = np.full(nodd, unset, dtype=np.uint32)
    spf[pr >> 1] = np.arange(len(pr), dtype=np.uint32)   # a prime: itself
    for j, p in enumerate(pr[:int(np.searchsorted(
            pr, math.isqrt(pmax), side="right"))].tolist()):
        sl = spf[(p * p) >> 1::p]           # p^2, p^2 + 2p, ... (composite)
        sl[sl == unset] = j
    spf[0] = 0
    p64 = pr.astype(np.uint64)
    mu = np.uint64(0xFFFFFFFFFFFFFFFF) // p64    # = floor(2^64/p), p odd
    p32 = pr.astype(np.uint32)
    x = p32.copy()                          # p^-1 mod 2^32 by Newton: 3 bits,
    for _ in range(4):                      # then 6, 12, 24, 48
        x = x * (np.uint32(2) - p32 * x)
    return p32, mu, x, spf


class GpuEngine:
    """Per window: the class-group prefilter, the sparse exact count of the
    n it leaves, and the survivor rule.

        e = GpuEngine()
        ks, ts = e.survivors(m0, W, floor)      # one window, ascending k
        for m0, W, ks, ts in e.sweep(k_lo, k_hi, floor): ...
        t3 = e.h3(m0, W)                        # EVERY counter, three squares
        t3 = e.exact(m0, W)                     # EVERY counter, sparse count

    prefilter=False tabulates every counter (the reference configuration
    gate P6 and the benchmarks compare against).
    """

    def __init__(self, logw=LOGW, ch=CH, block=256, prefilter=True,
                 pre_threads=PRE_THREADS, pre_block=PRE_BLOCK,
                 sp_chunk=SP_CHUNK, sp_blocks_a=SP_BLOCKS_A,
                 sp_blocks_b=SP_BLOCKS_B, force_wide=False, sp_maxw=SP_MAXW):
        """force_wide (wide form-table keys at every height) and a small
        sp_maxw (characters on the fly past that many words of primes)
        exist for the gates: each must change no decision and no count."""
        cp = _cupy()
        self.cp = cp
        self.force_wide = bool(force_wide)
        self.sp_maxw = max(1, int(sp_maxw))
        self.W = 1 << int(logw)
        self.ch = int(ch)
        self.block = int(block)
        self.use_pre = bool(prefilter)
        self.pre_threads = int(pre_threads)
        self.pre_block = int(pre_block)
        self.sp_chunk = int(sp_chunk)
        self.sp_blocks_a = int(sp_blocks_a)
        self.sp_blocks_b = int(sp_blocks_b)
        mod = cp.RawModule(code=source(), options=("--std=c++14",))
        self._tab = mod.get_function("tab")
        self._classify = mod.get_function("classify")
        self._pre1 = mod.get_function("pre1")
        self._pre2 = mod.get_function("pre2")
        self._spa = mod.get_function("spa")
        self._spb = mod.get_function("spb")
        self.cnt = cp.zeros(self.W, dtype=cp.uint32)
        self.out_i = cp.zeros(self.W, dtype=cp.uint32)
        self.out_t = cp.zeros(self.W, dtype=cp.uint32)
        self.nout = cp.zeros(1, dtype=cp.uint32)
        self.p2 = cp.asarray(np.array([p * p for p in SMALLP],
                                      dtype=np.uint32))
        self.inv = cp.asarray(np.array([1.0 - 1.0 / p for p in SMALLP],
                                       dtype=np.float64))
        self._pre_tables()
        self._sp_pmax = 0
        self._ensure_sparse(SP_PMAX)
        self.qctr = cp.zeros(1, dtype=cp.uint32)
        self.pairs = 0            # (x, y) pairs planned, last full window
        self.threads = 0
        self.launches = 0         # walk launches, last full window
        self.flags = None         # last window: the n counted exactly
                                  # (device bool), or None (all of them)
        self.pre_n = None         # last window: how many n the prefilter
        self.pre_s = None         # left, and the sum of their (i + 1)
        self.last = None          # (m0, W, floor) while cnt holds that
                                  # survivors() window; None otherwise
        self.pre_stats = {}
        self.sp_stats = {}

    # ---------------------------------------------------- prefilter tables
    def _pre_tables(self):
        cp = self.cp
        pr = _primes_to(PRE_TRIAL_MAX)
        if pr[:len(SMALLP)] != SMALLP:
            raise AssertionError("trial primes do not open with SMALLP")
        M = (1 << 64) - 1
        self._trial = pr
        self.tp = cp.asarray(np.array(pr, dtype=np.uint32))
        self.tinv = cp.asarray(np.array([pow(p, -1, 1 << 64) for p in pr],
                                        dtype=np.uint64))
        self.tlim = cp.asarray(np.array([M // p for p in pr],
                                        dtype=np.uint64))
        self.smu = cp.asarray(np.array([(1 << 64) // p for p in SMALLP],
                                       dtype=np.uint64))
        off, sq, inv = [], [], []
        for p in SMALLP:
            off.append(len(sq))
            row = [0] * p                    # the odd root in [1, p), or 0
            for b in range(1, p, 2):
                row[b * b % p] = b
            sq.extend(row)
            inv.extend([0] + [pow(x, -1, p) for x in range(1, p)])
        self.soff = cp.asarray(np.array(off, dtype=np.uint32))
        self.sqt = cp.asarray(np.array(sq, dtype=np.uint8))
        self.invt = cp.asarray(np.array(inv, dtype=np.uint8))
        self.spinv64 = cp.asarray(np.array(
            [pow(p, -1, 1 << 64) for p in SMALLP], dtype=np.uint64))
        self.qram = cp.asarray(np.array(Q_RAM, dtype=np.float64))
        self.qspl = cp.asarray(np.array(Q_SPL, dtype=np.float64))
        self.tbl = cp.zeros(self.pre_threads * 256, dtype=cp.uint64)
        self.tbl_wide = None        # 2 u64 a slot, allocated on first use

    def _ensure_sparse(self, pmax):
        """The sparse count's tables cover every a <= pmax: grown (at least
        doubled, at most to SP_PMAX_TOP) when a window needs more."""
        if pmax <= self._sp_pmax:
            return
        cp = self.cp
        pmax = min(SP_PMAX_TOP, max(int(pmax), 2 * self._sp_pmax))
        pr, mu, pinv, spf = sparse_tables(pmax)
        self._sp_pr = pr
        self.sp_pr = cp.asarray(pr)
        self.sp_mu = cp.asarray(mu)
        self.sp_pinv = cp.asarray(pinv)
        self.sp_spf = cp.asarray(spf)
        self._sp_pmax = pmax

    def _table(self, wide):
        if not wide:
            return self.tbl
        if self.tbl_wide is None:
            self.tbl_wide = self.cp.zeros(self.pre_threads * 512,
                                          dtype=self.cp.uint64)
        return self.tbl_wide

    def held_bytes(self):
        return int(self.cnt.nbytes + self.out_i.nbytes + self.out_t.nbytes
                   + self.tbl.nbytes + 6 * self.W + self.sp_pr.nbytes
                   + (self.tbl_wide.nbytes if self.tbl_wide is not None
                      else 0)
                   + self.sp_mu.nbytes + self.sp_pinv.nbytes
                   + self.sp_spf.nbytes)

    # ------------------------------------------------------------ tabulate
    def tab(self, m0, W=None, ch=None):
        """T(8m + 3) for EVERY m in [m0, m0 + W) as the engine's device
        buffer (a view of the first W counters; overwritten by the next
        call)."""
        cp = self.cp
        W = self.W if W is None else int(W)
        if W > self.W:
            raise ValueError("window larger than the engine's buffer")
        ch = self.ch if ch is None else int(ch)
        n0, nmax, xs, ylo, ny, pref = plan(m0, W, ch)
        self.pairs = int(ny.sum())
        self.threads = nthreads = int(pref[-1])
        cnt = self.cnt[:W]
        cnt.fill(0)
        self.flags = self.pre_n = self.pre_s = None
        self.last = None
        if nthreads:
            dp, dx, dy, dn = (cp.asarray(pref), cp.asarray(xs),
                              cp.asarray(ylo), cp.asarray(ny))
            chunk = TAB_GRID * self.block
            self.launches = 0
            for t0 in range(0, nthreads, chunk):
                self.launches += 1
                nt = min(chunk, nthreads - t0)
                grid = (nt + self.block - 1) // self.block
                self._tab((grid,), (self.block,),
                          (np.uint64(n0), np.uint32(W), np.int32(ch),
                           np.int64(nthreads), np.int64(t0),
                           np.int32(len(xs)), dp, dx, dy, dn, cnt))
        return cnt

    def h3(self, m0, W=None, ch=None):
        """The same, copied to the host (np.uint32)."""
        return self.cp.asnumpy(self.tab(m0, W, ch))

    # --------------------------------------------------------- sparse count
    def _words(self, x):
        """u32 words of character bits for the primes <= x."""
        return (int(np.searchsorted(self._sp_pr, x, side="right")) + 31) // 32

    def sparse(self, m0, lst, f2, wmax=None):
        """The sparse count of the n = 8(m0 + i) + 3, i in lst (device
        u32): phase A drops every n whose prefix count reaches the rule at
        f2 = 2F (f2 = 0 drops none), phase B counts the rest.  wmax: the
        largest n of the window the rule's constants are taken for
        (default: the list's own).  Returns (und, T): the indices counted
        to the end and their exact T (device u64)."""
        cp = self.cp
        cnt = int(lst.size)
        if not cnt:
            return lst, cp.zeros(0, dtype=cp.uint64)
        nmax = 8 * (int(m0) + int(lst.max())) + 3
        if nmax >= N_CEIL:
            raise ValueError(f"4k - 1 = {nmax} is past the engine ceiling "
                             f"2^62")
        wmax = nmax if wmax is None else int(wmax)
        self._ensure_sparse(math.isqrt(nmax // 3) + 2)
        # the characters of the primes below A (phase A) and below
        # isqrt(n/3) (phase B) in shared memory, as far as sp_maxw words
        # reach; past the jb-th prime they are computed on the fly
        wa = min(self._words(math.isqrt(nmax) // 2), self.sp_maxw)
        wb = min(self._words(math.isqrt(nmax // 3)), self.sp_maxw)
        out_a = cp.zeros(cnt, dtype=cp.uint64)
        stat = cp.zeros(cnt, dtype=cp.uint32)
        self.qctr.fill(0)
        self._spa((min(self.sp_blocks_a, cnt),), (SP_THREADS,),
                  (np.uint64(m0), lst, np.uint32(cnt), self.qctr,
                   np.float64(f2), np.float64(PI_UP),
                   np.float64(rho_min(wmax)), np.float64(rho_large(wmax)),
                   np.int32(len(SMALLP)), self.p2,
                   self.inv, self.sp_pr, np.uint32(self.sp_pr.size),
                   self.sp_mu, self.sp_pinv, self.sp_spf, np.uint32(wa),
                   np.uint32(32 * wa), np.int32(self.sp_chunk), self.tp,
                   self.smu, self.soff, self.sqt, self.qram, self.qspl,
                   out_a, stat),
                  shared_mem=4 * wa)
        und = cp.flatnonzero(stat == 1)
        ul, ua = lst[und], out_a[und]
        T = cp.zeros(int(ul.size), dtype=cp.uint64)
        if ul.size:
            self.qctr.fill(0)
            self._spb((min(self.sp_blocks_b, int(ul.size)),), (SP_THREADS,),
                      (np.uint64(m0), ul, np.uint32(ul.size), self.qctr, ua,
                       self.sp_pr, np.uint32(self.sp_pr.size), self.sp_mu,
                       self.sp_pinv, self.sp_spf, np.uint32(wb),
                       np.uint32(32 * wb), T),
                      shared_mem=4 * wb)
        self.sp_stats = {"in": cnt, "phase_b": int(ul.size)}
        return ul, T

    def exact(self, m0, W):
        """T(8m + 3) for EVERY m in [m0, m0 + W) by the sparse count, no
        rule (np.uint64) -- the gates' second road to the counts."""
        cp = self.cp
        ul, T = self.sparse(m0, cp.arange(int(W), dtype=cp.uint32), 0.0)
        out = cp.zeros(int(W), dtype=cp.uint64)
        out[ul] = T
        return cp.asnumpy(out)

    # ----------------------------------------------------------- prefilter
    def _pre_args(self, f2, np1, rl):
        return (np.float64(f2), np.float64(PI_UP), np.float64(rl),
                np.int32(np1), self.tp, self.tinv, self.tlim, self.smu,
                self.soff, self.sqt, self.invt, self.inv,
                self.spinv64, self.qram, self.qspl)

    def _launch(self, count):
        nthr = min(self.pre_threads, int(count))
        if count > 1000 * nthr:
            raise ValueError("prefilter launch too long for the table "
                             "generation counter")
        return nthr, ((nthr + self.pre_block - 1) // self.pre_block,)

    def _k1(self, m0, count, lst, base, f2, np1, rl, wide):
        cp = self.cp
        out = cp.zeros(int(count), dtype=cp.uint32)
        nthr, grid = self._launch(count)
        self._pre1(grid, (self.pre_block,),
                   (np.uint64(m0), np.uint32(count),
                    lst if lst is not None else 0, np.uint32(nthr),
                    np.int32(base), np.int32(wide))
                   + self._pre_args(f2, np1, rl)
                   + (self._table(wide), out))
        return out

    def _k2(self, m0, lst, m1, base, mode, f2, np1, rl, wide):
        cp = self.cp
        count = int(lst.size)
        out = cp.zeros(count, dtype=cp.uint32)
        nthr, grid = self._launch(count)
        self._pre2(grid, (self.pre_block,),
                   (np.uint64(m0), np.uint32(count), lst, m1,
                    np.uint32(nthr), np.int32(base), np.int32(mode),
                    np.int32(wide))
                   + self._pre_args(f2, np1, rl)
                   + (self._table(wide), out))
        return out

    def prefilter(self, m0, W, floor):
        """The flags of [m0, m0 + W) as a device bool array: False where
        h(-n) >= need is PROVED (the survivor rule drops that k whatever
        its count is), True where T(n) must be counted."""
        cp = self.cp
        m0, W = int(m0), int(W)
        f2 = 2.0 * float(floor)
        flags = cp.ones(W, dtype=cp.bool_)
        st = {"W": W, "pass1": 0, "order": 0, "bound2": 0, "index": 0,
              "base2": 0, "flagged": W}
        self.pre_stats = st
        i_lo = max(0, -(-(PRE_MIN_N - 3) // 8) - m0)
        if f2 <= 0.0 or i_lo >= W:
            return flags
        nmax = 8 * (m0 + W - 1) + 3
        if nmax >= N_CEIL:
            raise ValueError(f"4k - 1 = {nmax} is past the engine ceiling "
                             f"2^62")
        P1 = _icbrt_up(nmax)
        np1 = bisect.bisect_right(self._trial, P1)
        rl = rho_large(nmax)
        wide = 1 if (nmax >= N_WIDE or self.force_wide) else 0
        st["wide"] = wide
        mb, cnt = m0 + i_lo, W - i_lo
        st["pass1"] = cnt
        out = self._k1(mb, cnt, None, 0, f2, np1, rl, wide)
        final = [cp.flatnonzero(out == 1).astype(cp.uint32)]
        und = cp.flatnonzero(out >= 2).astype(cp.uint32)
        lst, m1 = und, out[und]
        st["order"] = int(lst.size)
        for base in range(PRE_NBASE):
            if base:
                if not lst.size:
                    break
                st["base2"] = int(lst.size)
                o = self._k1(mb, lst.size, lst, base, f2, np1, rl, wide)
                final.append(lst[o == 1])
                keep = o >= 2
                lst, m1 = lst[keep], o[keep]
            if not lst.size:
                continue
            o = self._k2(mb, lst, m1, base, 0, f2, np1, rl, wide)
            cap = lst[o == 2]
            u3 = o == 3
            l3, m3 = lst[u3], m1[u3]
            if not base:
                st["bound2"] = int(lst.size - cap.size - l3.size)
                st["index"] = int(l3.size)
            if l3.size:
                o3 = self._k2(mb, l3, m3, base, 1, f2, np1, rl, wide)
                l3 = l3[o3 == 1]
            lst = cp.concatenate([cap, l3])
        final.append(lst)
        fl = cp.concatenate(final)
        flags[i_lo:] = False
        if fl.size:
            flags[fl.astype(cp.int64) + i_lo] = True
        st["flagged"] = int(fl.size) + i_lo
        return flags

    def _pack(self, flags):
        """The u32 bitmap of a bool array (bit i in word i >> 5), padded."""
        cp = self.cp
        W = int(flags.size)
        nw = (W + 31) // 32 + 1
        buf = cp.zeros(nw * 32, dtype=cp.uint32)
        buf[:W] = flags
        return (buf.reshape(nw, 32) << cp.arange(32, dtype=cp.uint32)).sum(
            axis=1, dtype=cp.uint32)

    # ------------------------------------------------------------ classify
    def survivors(self, m0, W=None, floor=0.0, ch=None):
        """(ks, ts): the survivors of [m0, m0 + W) at `floor`, k ascending
        (np.int64) with their T (np.uint32)."""
        cp = self.cp
        W = self.W if W is None else int(W)
        if W > self.W:
            raise ValueError("window larger than the engine's buffer")
        self.last = None
        lst = None
        wmax = 8 * (int(m0) + W - 1) + 3        # the rule's constants: this
        if wmax >= N_CEIL:                      # window's (rho_large, rho_min)
            raise ValueError(f"4k - 1 = {wmax} is past the engine ceiling "
                             f"2^62")
        if self.use_pre and floor > 0.0:
            flags = self.prefilter(m0, W, floor)
            if self.pre_stats["flagged"] < W:
                lst = cp.flatnonzero(flags).astype(cp.uint32)
        if lst is None:                     # the opening band, floor 0
            cnt = self.tab(m0, W, ch)
            fptr = 0
        else:
            ul, T = self.sparse(m0, lst, 2.0 * floor, wmax)
            cnt = self.cnt[:W]
            cnt.fill(0)
            ex = cp.zeros(W, dtype=cp.bool_)
            if ul.size:
                if int(T.max()) >= 1 << 32:
                    raise OverflowError("a count past 2^32: the arithmetic "
                                        "bound of the header is broken")
                cnt[ul] = T.astype(cp.uint32)
                ex[ul] = True
            self.flags = ex
            self.pre_n = int(lst.size)
            self.pre_s = int((lst.astype(cp.uint64) + 1).sum()) & ((1 << 64) - 1)
            fptr = self._pack(ex)
        self.nout.fill(0)
        self._classify(((W + 255) // 256,), (256,),
                       (np.uint64(m0), np.int32(W), cnt, fptr,
                        np.float64(2.0 * floor), np.float64(PI_UP),
                        np.float64(rho_min(wmax)),
                        np.float64(rho_large(wmax)),
                        np.int32(len(SMALLP)), self.p2, self.inv,
                        self.tp, self.smu, self.soff, self.sqt, self.qram,
                        self.qspl, self.nout, self.out_i, self.out_t))
        n = int(self.nout[0])
        self.last = (int(m0), W, float(floor))
        if n == 0:
            return np.zeros(0, np.int64), np.zeros(0, np.uint32)
        ii = cp.asnumpy(self.out_i[:n]).astype(np.int64)
        tt = cp.asnumpy(self.out_t[:n])
        order = np.argsort(ii, kind="stable")
        return 2 * (int(m0) + ii[order]) + 1, tt[order]

    def sweep(self, k_lo, k_hi, floor):
        """Yield (m0, W, ks, ts) over the odd k in [k_lo, k_hi), in full
        windows from (k_lo - 1)/2."""
        m = (int(k_lo) - 1 + 1) // 2 if int(k_lo) % 2 == 0 \
            else (int(k_lo) - 1) // 2
        m_end = int(k_hi) // 2            # odd k < k_hi  <=>  m < k_hi // 2
        while m < m_end:
            W = min(self.W, m_end - m)
            ks, ts = self.survivors(m, W, floor)
            yield m, W, ks, ts
            m += W

    def recount(self, k):
        """T(4k - 1) again, from scratch, at a different alignment and
        chunking: a window of 37 starting 11 below, three y per thread,
        every counter tabulated (no prefilter).  None past the walk's
        bound (k ~ 2.25*10^15; O(k): 2.9 s at 10^13, ~11 min at the bound,
        on the device while the CPU legs of the confirmations run)."""
        m = (int(k) - 1) // 2
        m0 = max(0, m - 11)
        if 8 * (m0 + 36) + 3 >= WALK_MAX_N:
            return None
        return int(self.h3(m0, 37, ch=3)[m - m0])

    def sample(self, seed):
        """One k of the last survivors() window for the campaign's health
        check: (n, T, tabulated, floor), or None when the counters no
        longer hold that window (a recount or a gate ran since).
        tabulated True: T is the exact count (counted to the end by the
        sparse count, or by the walk).  False: the prefilter or a prefix
        of the sparse count dropped it -- T is 0 and the claim to check is
        that the survivor rule drops n at that floor.  Even seeds pick a
        counted k when the window has one."""
        if self.last is None:
            return None
        m0, W, floor = self.last
        i = int(seed) % max(W, 1)
        if self.flags is not None and int(seed) % 2 == 0:
            idx = self.cp.flatnonzero(self.flags)
            if idx.size:
                i = int(idx[int(seed) % int(idx.size)])
        tab = self.flags is None or bool(self.flags[i])
        return 8 * (m0 + i) + 3, int(self.cnt[i]), tab, floor

    def digest(self, W=None):
        """(sum of T, sum of T*(i+1) mod 2^64, counters counted exactly,
        n the prefilter left, sum of their (i+1) mod 2^64) over the last
        window; a counter not counted to the end is zero."""
        cp = self.cp
        W = self.W if W is None else int(W)
        c = self.cnt[:W].astype(cp.uint64)
        s1 = int(c.sum())
        s2 = int((c * cp.arange(1, W + 1, dtype=cp.uint64)).sum())
        if self.flags is None:
            return s1, s2 & ((1 << 64) - 1), W, W, W * (W + 1) // 2
        return (s1, s2 & ((1 << 64) - 1), int(self.flags[:W].sum()),
                self.pre_n, self.pre_s)


def fingerprint(engine, k_lo, windows, floor):
    """The frozen-work fingerprint of `windows` full windows from k_lo: a
    list of ints, one per survivor (k * 2^32 + T) and five per window (the
    two digests of its exact counts, their number, and the number and
    position sum of the n the prefilter left), so a wrong count or a
    changed prefilter decision anywhere in the window moves the checksum
    whether or not it is a survivor's."""
    out = []
    m = (int(k_lo) - 1) // 2
    for _ in range(int(windows)):
        ks, ts = engine.survivors(m, engine.W, floor)
        out.extend((int(k) << 32) | int(t) for k, t in zip(ks, ts))
        out.extend(engine.digest())
        m += engine.W
    return out


# ------------------------------------------------------------------ gates
_ENGINE = None


def _engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = GpuEngine()
    return _ENGINE


def _rule_heights():
    """The heights where a per-window rule constant moves (a further prime
    square fits below them), each with its neighbours, between 2^46 and
    the ceiling."""
    marks = set()
    for ps in (SMALLP, _PAST_251):
        prod = 1
        for p in ps:
            prod *= p * p
            if N_OLD <= prod < N_CEIL:
                marks |= {prod - 1, prod}
    return sorted(marks | {1, N_OLD - 1, N_OLD, N_WIDE, N_CEIL - 1})


def gate_p0():
    import hlc_search as cpu
    same = (SMALLP == cpu.SMALLP and RHO_LARGE == cpu.RHO_LARGE
            and RHO_MIN == cpu.RHO_MIN and PI_UP == cpu.PI_UP
            and Q_RAM == cpu.Q_RAM and Q_SPL == cpu.Q_SPL
            and Q_PAD == cpu.Q_PAD
            and float(repr(Q_PAD)) == Q_PAD
            and N_CEIL == cpu.N_CEIL and K_CEIL == cpu.K_CEIL
            and N_OLD == cpu.N_OLD and PRE_MIN_N == cpu.PRE_MIN_N
            and PRE_NGENS == cpu.PRE_NGENS and PRE_NBASE == cpu.PRE_NBASE
            and PRE_CAP2 == cpu.PRE_CAP2
            and PRE_NEED_MAX == cpu.PRE_NEED_MAX)
    hs = _rule_heights()
    per_window = all(rho_large(h) == cpu.rho_large(h)
                     and rho_min(h) == cpu.rho_min(h) for h in hs)
    v3 = (rho_large(N_OLD - 1) == RHO_LARGE == rho_large(1)
          and rho_min(N_OLD - 1) == RHO_MIN == rho_min(1))
    e = _engine()
    refused = 0
    for call in (lambda: e.survivors((N_CEIL - 3) // 8, 4, 7.5),
                 lambda: e.prefilter((N_CEIL - 3) // 8, 4, 7.5),
                 lambda: plan((WALK_MAX_N - 3) // 8, 4)):
        try:
            call()
        except ValueError:
            refused += 1
    cube = PRE_TRIAL_MAX ** 3 > N_CEIL and PRE_SP_MAX * 2 <= 256 \
        and PRE_SP_MAX <= 128 and PRE_NGENS <= 8 \
        and math.isqrt(N_CEIL // 3) < 1 << 31 and PRE_NEED_MAX < 1 << 31
    if not (same and per_window and v3 and refused == 3 and cube
            and 4 * K_CEIL < N_CEIL and k_ceil() == K_CEIL):
        return False, ("P0 rule constants, prefilter constants or guards "
                       f"differ (same {same}, per-window {per_window}, v3 "
                       f"{v3}, refusals {refused}/3, bounds {cube})")
    return True, (f"P0 both engines state the same survivor rule (53 primes, "
                  f"PI_UP, and RHO_LARGE / RHO_MIN per window, equal at the "
                  f"{len(hs)} heights where they move and v3's below 2^46) "
                  f"and the same prefilter decision (bases, partners, index "
                  f"cap, bound cap); the trial primes pass the cube root of "
                  f"2^62 and every reduced a is below 2^31; a window past "
                  f"2^62 and a walk past 2^53 are refused; K_CEIL = 10^18 "
                  f"is inside")


PARITY_WINDOWS = [   # (k_lo, W in m, floor): populated at every height
    (1, 1 << 15, 6.0), (10**6 + 1, 8192, 5.0), (10**7 + 1, 4096, 5.0),
    (10**8 + 1, 2048, 4.5), (10**9 + 1, 768, 4.5), (4 * 10**9 + 1, 512, 4.5),
]


def gate_p1():
    import hlc_search as cpu
    e = _engine()
    nsurv = 0
    for k_lo, W, floor in PARITY_WINDOWS:
        m0 = (k_lo - 1) // 2
        ref = cpu.h3_window(m0, W)
        got = e.h3(m0, W)
        if not np.array_equal(ref, got):
            bad = int(np.nonzero(ref != got)[0][0])
            return False, (f"P1 parity FAILED at k = {2 * (m0 + bad) + 1}: "
                           f"forms {int(ref[bad])}, squares {int(got[bad])}")
        ks, ts = e.survivors(m0, W, floor)
        want = cpu.survivors(m0, W, floor)
        if [(int(a), int(b)) for a, b in zip(ks, ts)] != want or not want:
            return False, (f"P1 survivor streams differ at k_lo = {k_lo} "
                           f"({len(ks)} vs {len(want)})")
        nsurv += len(want)
    # the comparator itself: a planted corruption must be caught
    m0 = PARITY_WINDOWS[2][0] // 2
    got = e.h3(m0, 512).copy()
    got[137] += 6
    if np.array_equal(got, cpu.h3_window(m0, 512)):
        return False, "P1 comparator missed a planted +6"
    return True, (f"P1 parity: sums of three squares (GPU) = reduced forms "
                  f"(CPU), every counter, and the production stream "
                  f"(prefilter, sparse count, rule) = the forms "
                  f"sieve's survivors, on {len(PARITY_WINDOWS)} populated "
                  f"windows from k = 1 to 4*10^9 ({nsurv} survivors); a "
                  f"planted +6 is caught")


def gate_p2():
    e = _engine()
    for k_lo, W in ((3 * 10**6 + 1, 1 << 16), (10**10 + 1, 6000),
                    (10**12 + 1, 3000)):
        m0 = (k_lo - 1) // 2
        whole = e.h3(m0, W).copy()
        cuts = [0, W // 7, W // 7 + 1, W // 2 + 3, W]
        parts = np.concatenate([e.h3(m0 + a, b - a, ch=5)
                                for a, b in zip(cuts, cuts[1:])])
        if not np.array_equal(whole, parts):
            return False, f"P2 split != whole at k_lo = {k_lo}"
        for m in (m0 + 5, m0 + W - 1):
            if e.recount(2 * m + 1) != int(whole[m - m0]):
                return False, f"P2 recount differs at k = {2 * m + 1}"
    return True, ("P2 resume / alignment: a window equals its four unequal "
                  "pieces (different chunking) and the single-k recount, at "
                  "k = 3*10^6, 10^10 and 10^12")


def gate_p3():
    """The heights to past the old ceiling, against the analytic class
    number (no form, no square): the walk's counts to 10^13, the sparse
    count's (every counter, no rule) at 10^14 -- wide keys, characters on
    the fly and three primes past 251 in the rule all in force there."""
    import hlc_search as cpu
    e = _engine()
    n_checked, worst = 0, 0.0
    for k_lo, W, step, road in ((10**10 + 1, 64, 9, "walk"),
                                (10**11 + 1, 64, 13, "walk"),
                                (10**12 + 1, 64, 21, "walk"),
                                (10**13 - 129, 64, 31, "walk"),
                                (10**14 + 1, 64, 37, "sparse")):
        m0 = (k_lo - 1) // 2
        t3 = e.h3(m0, W) if road == "walk" else e.exact(m0, W)
        for i in range(0, W, step):
            t, frac = cpu.hurwitz3_analytic(8 * (m0 + i) + 3)
            worst = max(worst, frac)
            n_checked += 1
            if t != int(t3[i]) or frac > 0.05:
                return False, (f"P3 k = {2 * (m0 + i) + 1}: device "
                               f"{int(t3[i])}, analytic {t}")
    return True, (f"P3 heights: {n_checked} device counts at k = 10^10, "
                  f"10^11, 10^12 and 10^13 (three squares) and 10^14 (the "
                  f"sparse count, past every v3 bound) equal the analytic "
                  f"class numbers (worst distance from an integer "
                  f"{worst:.1e})")


def gate_p4():
    """Canaries: the eleven terms and the literature's values come out of
    the device stream with the class numbers the host expects."""
    import hlc_search as cpu
    e = _engine()
    seen = {}
    for m0, W, ks, ts in e.sweep(1, 300001, 6.6):
        seen.update(zip(ks.tolist(), ts.tolist()))
    want_h = {21377: 22, 27941: 24, 41537: 29, 55661: 33, 115721: 46,
              239621: 66, 247757: 63}
    for k, h in want_h.items():
        if seen.get(k) != 3 * h:
            return False, f"P4 canary k = {k} missing or wrong in the stream"
    for D, cs in cpu.LITERATURE[-2:] + cpu.LITERATURE[8:9]:
        k = (1 - D) // 4
        ks, ts = e.survivors((k - 1) // 2 - 3, 8, cpu.CENSUS_FLOOR)
        if k not in ks.tolist():
            return False, f"P4 literature canary k = {k} did not survive"
        t = int(ts[ks.tolist().index(k)])
        lo, hi = cpu.C_bounds(4 * k - 1, cpu.h_from_t3(4 * k - 1, t)[3],
                              1 << 20)
        if not (lo - 1.01e-7 <= 2 * float(cs) <= hi + 1.01e-7):
            return False, f"P4 literature canary k = {k}: wrong C"
    return True, (f"P4 canaries: a(5)..a(11) survive the stream over "
                  f"k <= 3*10^5 with the right class numbers "
                  f"({len(seen)} survivors at 6.6), and Fung & Williams' "
                  f"k = 99539591, 17959429571 and 21425625701 survive at "
                  f"the census floor with their published C")


PRE_WINDOWS = [   # (k_lo, W in m, floor): the prefilter against its reference
    (262145, 1024, 7.5), (10**8 + 1, 1024, 7.5), (10**9 + 1, 768, 4.5),
    (3 * 10**11 + 1, 1024, 7.5), (10**12 + 1, 512, 7.5),
    (10**13 - 1025, 384, 7.5),          # engine v3's ceiling
    (9 * 10**13 + 1, 96, 7.5),          # wide keys, three primes past 251
]


def gate_p5():
    """The prefilter's decision, bit for bit, against the CPU reference
    (Python integers, textbook composition, dictionaries)."""
    import hlc_search as cpu
    e = _engine()
    tot = drop = 0
    for k_lo, W, floor in PRE_WINDOWS:
        m0 = (k_lo - 1) // 2
        got = e.cp.asnumpy(e.prefilter(m0, W, floor))
        ref = cpu.prefilter_window(m0, W, floor)
        if not np.array_equal(got, ref):
            bad = int(np.nonzero(got != ref)[0][0])
            return False, (f"P5 prefilter decisions differ at k = "
                           f"{2 * (m0 + bad) + 1}: device "
                           f"{'tabulate' if got[bad] else 'drop'}, reference "
                           f"{'tabulate' if ref[bad] else 'drop'}")
        tot += W
        drop += int(W - got.sum())
    if not (0.9 * tot < drop < tot):
        return False, f"P5 windows not populated: {drop} of {tot} dropped"
    # the descent's corners: a prime square beyond the trial division (the
    # cofactor r^2), odd exponents >= 3 (p in d and in f), several square
    # primes, d = 3 (always counted)
    nsp = 0
    for n in _descent_n():
        m0 = (n - 3) // 8 - 3
        for floor in (7.5, 4.5):
            got = e.cp.asnumpy(e.prefilter(m0, 8, floor))
            ref = cpu.prefilter_window(m0, 8, floor)
            if not np.array_equal(got, ref):
                return False, (f"P5 prefilter decisions differ near the "
                               f"constructed n = {n} (floor {floor})")
            nsp += 8
    return True, (f"P5 prefilter parity: the device's decision (wrapping "
                  f"64-bit forms, a table of giant steps, the group of the "
                  f"fundamental discriminant) = the reference's (Python "
                  f"integers, baby steps in a dictionary) for every k of "
                  f"{len(PRE_WINDOWS)} windows from k = 2.6*10^5 to 9*10^13 "
                  f"({drop} of {tot} dropped, {tot - drop} left to count) and "
                  f"of {nsp // 16} neighbourhoods of constructed conductors at "
                  f"two floors")


def _descent_n():
    """n == 3 (mod 8) with the conductors the descent must read right."""
    cand = [100003 ** 2 * d for d in (3, 11, 19, 35, 43, 123, 1003)]
    cand += [1000003 ** 2 * d for d in (3, 11, 19, 3 * 17)]
    cand += [3 ** 7 * 1000039, 3 ** 9 * 5 ** 3 * 4001, 5 ** 4 * 7 ** 3 * 2027,
             3 ** 2 * 5 ** 2 * 7 ** 2 * 11 ** 2 * 1000001,
             13 ** 4 * 17 ** 2 * 100019, 251 ** 2 * 257 ** 2 * 7]
    out = []
    for c in cand:
        for mult in (1, 3, 5, 7, 9, 11, 13, 15):
            if (c * mult) % 8 == 3 and c * mult < N_CEIL // 2:
                out.append(c * mult)
                break
    return sorted(set(out))


def gate_p6():
    """The production stream against the tabulation of every counter, and
    the exact counts against the same; a planted wrong drop is seen."""
    import hlc_search as cpu
    e = _engine()
    cp = e.cp
    nsurv = nflag = tot = 0
    for k_lo, W, floor in ((10**8 + 1, (1 << 18) + 77, 6.0),
                           (3 * 10**11 + 1, (1 << 17) + 5, 6.0),
                           (3 * 10**11 + 1 + (1 << 19), 1 << 17, 7.5),
                           (10**12 + 1, 1 << 15, 5.5),
                           (10**13 - (1 << 14) - 1, 1 << 13, 5.5),
                           (9 * 10**13 + 1, 1 << 12, 5.5)):
        m0 = (k_lo - 1) // 2
        full = e.h3(m0, W)
        want = np.nonzero(cpu.survivor_mask(m0, full, floor))[0]
        ks, ts = e.survivors(m0, W, floor)
        if e.flags is None:
            return False, f"P6 the prefilter did not run at k_lo = {k_lo}"
        fl = cp.asnumpy(e.flags)
        cnt = cp.asnumpy(e.cnt[:W])
        if not (np.array_equal(ks, 2 * (m0 + want) + 1)
                and np.array_equal(ts, full[want])):
            return False, (f"P6 filtered stream != full tabulation at "
                           f"k_lo = {k_lo} ({len(ks)} vs {len(want)})")
        if not (np.array_equal(cnt[fl], full[fl]) and not cnt[~fl].any()):
            return False, f"P6 exact counts differ at k_lo = {k_lo}"
        nsurv += len(want)
        nflag += int(e.pre_n)
        tot += W
    if nsurv < 50:
        return False, f"P6 windows not populated ({nsurv} survivors)"
    # the comparator: the n the prefilter left, less one survivor, sent to
    # the sparse count -- that survivor must be missing from its output
    i = int(want[0])
    lst = cp.flatnonzero(e.prefilter(m0, W, floor)).astype(cp.uint32)
    ul, T = e.sparse(m0, lst, 2.0 * floor)
    ul2, _ = e.sparse(m0, lst[lst != i], 2.0 * floor)
    got = dict(zip(cp.asnumpy(ul).tolist(), cp.asnumpy(T).tolist()))
    if got.get(i) != int(full[i]) or i in set(cp.asnumpy(ul2).tolist()):
        return False, "P6 the sparse count's output does not follow its list"
    return True, (f"P6 soundness: the production stream equals the survivor "
                  f"rule on EVERY counter on six windows from k = 10^8 to "
                  f"9*10^13 -- the last past every v3 bound, its walk in "
                  f"{e.launches} launches ({nsurv} survivors, none dropped; "
                  f"{nflag} of "
                  f"{tot} n left by the prefilter to the sparse count, every "
                  f"count it finished equal to the full tabulation's); a "
                  f"survivor withheld from the sparse count is missing from "
                  f"its output")


def _special_n():
    """n == 3 (mod 8) built to exercise the sparse count's corners: forms
    a(x^2 + xy + y^2) (n = 3a^2), high prime powers dividing n with both
    parities of the exponent and both characters of the cofactor, large
    square factors, many small primes."""
    cand = [3 * a * a for a in (1, 3, 12345, 99999, 1000001)]
    cand += [3 ** 15, 3 ** 15 * 17, 3 ** 13 * 41, 3 ** 9 * 11 * 43]
    cand += [5 ** 8 * 3, 5 ** 8 * 11, 5 ** 7 * 7 * 29, 7 ** 6 * 3 * 13]
    cand += [3001 ** 2 * q for q in (11, 19, 43, 59, 3)]
    cand += [101 ** 4 * 3, 101 ** 4 * 11, 1009 ** 3 * 3, 1009 ** 3 * 11]
    cand += [65537 ** 2 * 3, 65537 ** 2 * 19, 3 * 5 * 7 * 11 * 13 * 17 * 19,
             3 * 5 * 7 * 11 * 13 * 17 * 19 * 23 * 29]
    out = []
    for c in cand:
        for mult in (1, 3, 5, 7, 9, 11, 13, 15):
            if (c * mult) % 8 == 3:
                out.append(c * mult)
                break
    return sorted(set(out))


def gate_p7():
    """The sparse count against the three-squares count, every counter:
    two theorems again (reduced forms by their leading coefficient, with
    roots counted by multiplicativity or found by Tonelli-Shanks, Hensel
    and CRT; against sums of three squares)."""
    e = _engine()
    nchk = 0
    for k_lo, W in ((1, 4096), (10**5 + 1, 4096), (10**6 + 1, 4096),
                    (10**8 + 1, 2048), (10**10 + 1, 1024),
                    (10**12 + 1, 512), (10**13 - 1025, 512),
                    (6 * 10**13 + 1, 256)):
        m0 = (k_lo - 1) // 2
        full = e.h3(m0, W).astype(np.uint64)
        got = e.exact(m0, W)
        if not np.array_equal(full, got):
            i = int(np.nonzero(full != got)[0][0])
            return False, (f"P7 k = {2 * (m0 + i) + 1}: sparse {int(got[i])}, "
                           f"three squares {int(full[i])}")
        nchk += W
    sp = _special_n()
    for n in sp:
        m = (n - 3) // 8
        m0 = max(0, m - 3)
        full = e.h3(m0, 8).astype(np.uint64)
        got = e.exact(m0, 8)
        if not np.array_equal(full, got):
            i = int(np.nonzero(full != got)[0][0])
            return False, (f"P7 n = {8 * (m0 + i) + 3} (near a constructed "
                           f"n): sparse {int(got[i])}, three squares "
                           f"{int(full[i])}")
        nchk += 8
    # the comparator: a count off by one form is seen
    m0 = (10**8 + 1 - 1) // 2
    got = e.exact(m0, 64)
    got[17] += 3
    if np.array_equal(got, e.h3(m0, 64).astype(np.uint64)):
        return False, "P7 comparator missed a planted +3"
    return True, (f"P7 two roads to the counts: the sparse count (reduced "
                  f"forms by leading coefficient) = the three-squares count "
                  f"on {nchk} n -- eight windows from k = 1 to 6*10^13 and "
                  f"{len(sp)} neighbourhoods of constructed n (n = 3a^2, "
                  f"3^15 | n, 5^8 | n, p^2, p^3, p^4 | n up to p = 65537, "
                  f"nine small primes); a planted +3 is caught")


def _top_n():
    """[(n, d, f, role)]: n = d f^2 == 3 (mod 8) built past every height a
    walk or an analytic class number reaches in a gate, with d small
    (h(-d) by enumeration in milliseconds) and f chosen -- a prime past the
    character bitmap (p^2 | n read on the fly), a high prime power, d = 3
    -- so that T(n) = 3 h(-d) S(f) (S(f) for d = 3) is known exactly.
    role "count": the device counts it; "decide": the prefilter only (the
    sparse tables of 4*10^18 are 3.5 GB; the count's arithmetic is
    exercised at 4*10^16 and bounded in the header to 2^62)."""
    from sympy import nextprime
    out = []
    for d, f, role in (
            (11, nextprime(19 * 10**6), "count"),          # n ~ 4.0e15
            (11, 3 ** 9 * 5 ** 3 * 7, "count"),            # 3^18 | n
            (3, nextprime(365 * 10**5), "count"),          # T = S(f)
            (59, nextprime(26 * 10**6), "count"),          # n ~ 4.0e16
            (100003, 5 ** 4 * 1009, "count"),
            (11, nextprime(6 * 10**8), "decide"),          # n ~ 4.0e18
            (1155, nextprime(58 * 10**6), "decide")):
        n = d * f * f
        assert n % 8 == 3 and n < N_CEIL, (d, f)
        out.append((n, d, f, role))
    return out


def gate_p8():
    """Past the walk: constructed n whose counts are known (the sparse count
    against 3 h(-d) S(f), the production stream against the rule on every
    exact count of their windows, the Hurwitz relation on every
    neighbour), the prefilter at 4*10^18 against its reference, and the
    two v4 paths forced where v3's held -- wide form keys, and characters
    computed on the fly -- changing no decision and no count."""
    import hlc_search as cpu
    from sympy import factorint
    e = _engine()
    cp = e.cp
    ncount = ndec = nsurv = 0
    for n, d, f, role in _top_n():
        m0 = (n - 3) // 8 - 3
        if role == "decide":
            got = cp.asnumpy(e.prefilter(m0, 8, 7.5))
            ref = cpu.prefilter_window(m0, 8, 7.5)
            if not np.array_equal(got, ref):
                return False, (f"P8 prefilter decisions differ near the "
                               f"constructed n = {n}")
            ndec += 8
            continue
        S = 1
        for p, e2 in factorint(f).items():
            chi = 0 if d % p == 0 else cpu.legendre(-d, int(p))
            S *= 1 + (int(p) - chi) * (int(p) ** e2 - 1) // (int(p) - 1)
        want = S if d == 3 else 3 * cpu.class_number_enum(d) * S
        T = e.exact(m0, 8)
        if int(T[3]) != want:
            return False, (f"P8 n = {n} = {d}*{f}^2: sparse count "
                           f"{int(T[3])}, 3 h(-d) S(f) = {want}")
        for i in range(8):
            cpu.h_from_t3(8 * (m0 + i) + 3, int(T[i]))   # raises if not 3H
        mask = cpu.survivor_mask(m0, T.astype(np.uint32), 2.0)
        ks, ts = e.survivors(m0, 8, 2.0)
        idx = np.nonzero(mask)[0]
        if not (np.array_equal(ks, 2 * (m0 + idx) + 1)
                and np.array_equal(ts, T[idx].astype(np.uint32))):
            return False, f"P8 stream != the rule on the exact counts near {n}"
        ncount += 8
        nsurv += len(ks)
    if nsurv < 5:
        return False, f"P8 the top windows are not populated ({nsurv})"
    # the v4 paths forced at heights where v3's paths are exact
    ew, eb = GpuEngine(force_wide=True), GpuEngine(sp_maxw=4)
    for k_lo, W, floor in ((10**8 + 1, 1 << 15, 6.0),
                           (10**12 + 1, 1 << 17, 7.5)):
        m0 = (k_lo - 1) // 2
        r, dg = e.survivors(m0, W, floor), e.digest(W)
        for alt in (ew, eb):
            r2, dg2 = alt.survivors(m0, W, floor), alt.digest(W)
            if not (np.array_equal(r[0], r2[0]) and np.array_equal(r[1], r2[1])
                    and dg == dg2):
                return False, (f"P8 a forced v4 path changed the window at "
                               f"k_lo = {k_lo}")
    for n in _special_n():
        m0 = max(0, (n - 3) // 8 - 3)
        if not np.array_equal(e.exact(m0, 8), eb.exact(m0, 8)):
            return False, f"P8 characters on the fly differ near n = {n}"
    return True, (f"P8 past the walk: {ncount} sparse counts at k ~ 10^15 and "
                  f"10^16 around five constructed n = d f^2 (f a prime past "
                  f"the character bitmap, 3^18 | n, d = 3) give 3 h(-d) S(f) "
                  f"exactly and the Hurwitz relation everywhere, with the "
                  f"production stream equal to the rule on them ({nsurv} "
                  f"survivors at 2.0); {ndec} prefilter decisions at "
                  f"k ~ 10^18 equal the reference's; wide form keys and "
                  f"characters on the fly, forced at 10^8 and 10^12, change "
                  f"no survivor, digest or count (and none near the "
                  f"{len(_special_n())} constructed corners)")


GATES = [gate_p0, gate_p1, gate_p2, gate_p3, gate_p4, gate_p5, gate_p6,
         gate_p7, gate_p8]


def selftest():
    if not available():
        print("FAIL no CUDA device: the GPU engine cannot be gated")
        return False
    ok = True
    for g in GATES:
        t0 = time.time()
        try:
            good, msg = g()
        except Exception as ex:
            good, msg = False, f"{g.__name__}: {type(ex).__name__}: {ex}"
        print(("PASS " if good else "FAIL ") + msg
              + f"  [{time.time() - t0:.1f}s]", flush=True)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown
    sys.exit(_shutdown.graceful(lambda: 0 if selftest() else 1))
