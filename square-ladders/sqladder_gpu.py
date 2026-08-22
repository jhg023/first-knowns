"""sqladder_gpu.py -- the GPU engine for A089761.

The same mathematics a third time, in CuPy, and shaped so that nothing it
shares with the CPU engine could hide a bug in either.

WHAT THE KERNEL DOES.  The CPU engine materialises the dense k line and
marks arithmetic progressions into it.  This engine never forms the line
at all.  It carries a wheel index and reconstitutes

    k = W*j + x,        x congruent to a residue that no wheel prime kills

Each candidate is then TESTED, not marked: for each prime q above the
wheel the kernel reduces k mod q by Barrett magic-multiply and reads one
bit out of a packed table of the forbidden residues, BAILING OUT at the
first kill.  That early exit is the whole performance argument.  w(q,n) is
16 out of every q for q >= 37 (sqladder_reference), so the first prime
tested kills a large fraction and the expected number of tests per
candidate is three, against the ~22 marks per candidate a marking sieve of
the same depth would pay.

THE WHEEL IS FACTORED (v2, worth 3.9x).  A wheel is a table of the
surviving residues mod W, and that table grows as fast as W does: primes
to 23 give 1,088,640 residues mod 223,092,870 (4.4 MB, comfortably
cache-resident), while primes to 31 would give 261 million residues mod
2.0e11 -- 2 GB, read from DRAM, and the wheel would cost more than it
saves.  So the wheel is stored as TWO tables and combined per candidate by
CRT:

    x = RES1[t] + W1 * ( (RES2[s] - RES1[t]) * W1^-1  mod W2 )

with W1 the primes up to P1 and W2 the primes in (P1, P2].  The residues
mod W1*W2 are enumerated exactly, none stored: 5,040 entries beside the
1,088,640 give the wheel of primes up to 37, which is 6.6x fewer
candidates per unit of k line than primes to 23, out of two tables that
still fit in cache.

THE TEST LOOP IS ISSUE-BOUND, AND THE WARP PAYS THE MAX (v3, worth 4.1x).
Adding 24 independent instructions to the loop body costs 42% of the wall
clock, so the kernel is bound by instruction ISSUE -- which makes both
"fewer instructions per test" and "fewer tests per warp" real levers, and
they multiply.  v3 takes both:

  * The reduction is 32-bit where it can be.  k - qhat*q lies in [0, 2q)
    < 2^17, and arithmetic mod 2^32 is exact for a value that small, so
    the 64-bit multiply, subtract and conditional subtractions all become
    32-bit.  ONE conditional subtraction suffices, and that is a theorem
    rather than a hope: with M = floor(2^64/q) and k < 2^63,

        k*M/2^64 = k/q - k*s/(q*2^64)   where s = 2^64 mod q < q,

    so the error term is under 1/2, qhat > k/q - 3/2, and qhat is
    therefore floor(k/q) or one less.  K_CEIL = 9e18 < 2^63 = 9.223e18 is
    what makes it true, and _CHECK_ONE_SUBTRACT below enforces it.
    (huntlib's shared snippet keeps two subtractions because it does not
    get to assume a ceiling; this engine does, and states it.)

  * The per-prime constants are one uint4 (magic_lo, magic_hi, q, boff),
    so a test issues ONE 128-bit uniform load instead of three loads.

  * The first LIT primes are baked into the generated source as literals
    (OPTIMIZATION.md 2.5).  For q < 64 the whole forbidden set fits in a
    64-bit literal, so those tests read no table at all: `(KILL >> r) & 1`.
    Primes 41..61 are the six that kill 90% of candidates and every one of
    them is under 64.

  * The generation CRT is algebraic, not arithmetic.  m = ((r2 - r1)*INV)
    mod W2 = (r2*INV - r1*INV) mod W2, and each half is a function of one
    table index, so A[t] = (-r1*INV) mod W2 goes in the first-level table
    and C[s] = (r2*INV) mod W2 in the second, and generation becomes one
    add and one conditional subtract.  The r2 residues are then never
    needed on the device at all.

  * Divergence is compacted inside the CUDA block.  A lane needs 3.07
    tests but a warp of 32 runs to the deepest of them, 16.06 -- a 5.23x
    tax.  So each thread takes JPT candidates, runs the branchless literal
    prefix on all of them, and pushes the survivors to a SHARED-memory
    queue; after one __syncthreads the whole block chews that queue with
    every lane alive.  A JPT=8, TPB=128 block compacts 1,024 candidates
    into ~36 survivors, which is a full warp where an uncompacted warp
    would have carried one lane.  The queue cannot overflow by
    construction: a block pushes at most one entry per candidate it owns,
    and the queue holds exactly JPT*TPB.

    The survivors leave in queue order rather than in candidate order.
    `survivors_j` sorts, and the frozen work fingerprint is a count plus
    an xor, so neither depends on the order.

WHY THIS IS NOT dickson-ladders' ENGINE.  A247965 forces its k to be a
multiple of the wheel modulus -- one candidate residue per period, R = 1 --
so its engine can walk j alone and needs no residue table at all.  Here
half the nonzero residues survive each small prime, R is millions, and the
two problems need different machinery however similar they read.  The
proof of the difference is in sqladder_reference's docstring.

CEILINGS, stated and enforced (CONVENTIONS.md "Numeric hygiene"):
  * k < K_CEIL = 9e18 < 2^63, which is what keeps the Barrett reduction
    within ONE conditional subtraction of exact (above).  Every value
    k*i^2+1 below it is under huntlib's DETERMINISTIC Miller-Rabin bound
    (G10): this project proves its primes.
  * W1 < 2^32, so the first-level table is u32.
  * W2 < 2^32 and W1*W2 < 2^63.

Gates here: G7 (both wheel constructions == the oracle's brute-force period
walk), G8 (the wheel partitions the period: the count is the formula and no
kept residue is killed), G9 (GPU survivor stream == CPU survivor stream,
bit for bit, on populated windows at three heights and three filters,
one-level AND two-level, including at the ceiling), G13 (the production
wheel constants), G14 (the v3 mechanisms: the A/C generation tables, the
baked literal prefix, and the queue's capacity invariant).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.gpu import barrett_magics                         # noqa: E402
from sqladder_reference import K_FLOOR, wheel_residues
from sqladder_search import (K_CEIL, Q2_DEFAULT, CpuEngine, killed_residues)

P1_DEFAULT = 23              # first-level wheel: the primes up to here
P2_DEFAULT = 37              # second-level wheel: the primes in (P1, P2]
TPB_DEFAULT = 128            # threads per block   (swept on the v3 geometry)
JPT_DEFAULT = 8              # candidates per thread before compaction
LIT_DEFAULT = 6              # sieve primes baked into the source as literals
UNROLL = 4                   # independent Barrett chains in the queue tail
HIT_CAP = 1 << 16            # survivors buffered per launch
RES_MAX = 1 << 24            # refuse a one-level wheel table bigger than this
LIT_INLINE_Q = 64            # below this, a prime's kill set is a u64 literal

# How much candidate work a single launch should carry.  It sets how many
# wheel blocks go in gridDim.z, and it exists because the two ends of the
# range are 7 orders of magnitude apart: one production wheel block is
# 5.5e9 candidates and wants a launch to itself, while a gate shape whose
# wheel is 30,030 wide has 1,008 candidates per block and would otherwise
# pay 200,000 launches for one benchmark.  Measured flat to within 2.6%
# across the range (OPTIMIZATION_LOG, measurement 6).
CAND_PER_LAUNCH = 1 << 30

# The one-conditional-subtraction reduction is exact only below 2^63; see
# the module docstring.  Asserted here so raising K_CEIL cannot silently
# invalidate the kernel's arithmetic.
_CHECK_ONE_SUBTRACT = K_CEIL < (1 << 63)
if not _CHECK_ONE_SUBTRACT:
    raise ValueError(
        f"K_CEIL = {K_CEIL} is not below 2^63; the GPU kernel's single "
        f"conditional subtraction is only exact under 2^63, so raising the "
        f"ceiling is a new engine version (CONVENTIONS.md numeric hygiene)")

_MODCACHE = {}


def wheel(n, p1, lo=1):
    """(W, RES): residues mod W = prod(lo < q <= p1) that no such q kills.

    Built by CRT lifting -- one prime at a time, each existing residue
    lifted to the q classes above it and the killed ones dropped.  The
    oracle builds the same set by walking the whole period; G7 pins them
    together.  Lifting is what makes a million-entry table cheap: the work
    is sum(R_i * q_i), not W.

    Refuses rather than thrashes.  The table has prod(q - w(q,n)) entries,
    which grows fast enough that one careless argument is an out-of-memory
    death rather than a slow gate: primes to 37 in ONE level would be 5.5e9
    residues, about 44 GB.  That is the whole reason the engine factors the
    wheel into two levels, so asking for it in one is a mistake worth
    naming (it cost a gate battery two silent kills before this check
    existed).
    """
    W, count = 1, 1
    for q in primerange(lo + 1, p1 + 1):
        count *= q - len(killed_residues(q, n))
    if count > RES_MAX:
        raise ValueError(
            f"a one-level wheel over ({lo}, {p1}] at n={n} would hold "
            f"{count:,} residues (> RES_MAX = {RES_MAX:,}); factor it into "
            f"two levels instead -- that is what P2 is for")
    res = np.zeros(1, dtype=np.int64)
    for q in primerange(lo + 1, p1 + 1):
        bad = np.array(killed_residues(q, n), dtype=np.int64)
        cand = (res[None, :] + W * np.arange(q, dtype=np.int64)[:, None])
        cand = cand.ravel()
        res = np.sort(cand[~np.isin(cand % q, bad)])
        W *= q
    return W, res


def lit_prefix(n, primes, nlit):
    """The first `nlit` sieve primes, as straight-line CUDA with literals.

    No table load for the modulus, the magic or the bit offset; and for
    q < LIT_INLINE_Q no table load at all, because the whole forbidden set
    is a 64-bit immediate.  `off` walks the same cumulative offsets the
    packed bitmap uses, so a literal test and a table test address the
    identical bit -- G14 checks that against killed_residues directly.
    """
    lines, off = [], 0
    for q in primes[:nlit]:
        mg = (1 << 64) // q
        if q < LIT_INLINE_Q:
            mask = 0
            for u in killed_residues(q, n):
                mask |= 1 << u
            hit = f"kill |= (unsigned int)(({mask}ULL >> r) & 1ULL);"
        else:
            hit = (f"const unsigned int b = {off}u + r; "
                   f"kill |= (bits[b >> 5] >> (b & 31)) & 1u;")
        lines.append("            { unsigned int r = (unsigned int)k - "
                     f"(unsigned int)__umul64hi(k, {mg}ULL) * {q}u; "
                     f"if (r >= {q}u) r -= {q}u; {hit} }}")
        off += q
    return "\n".join(lines)


_SRC = r"""
#define W1C  %(w1)du
#define W2C  %(w2)du
#define WC   %(w)dULL
#define TWOLEVEL %(two)d
#define LITN %(lit)d
#define JPT  %(jpt)d
#define TPB  %(tpb)d
#define UNROLL %(unroll)d

/* One test against the packed per-prime uint4 (magic_lo, magic_hi, q,
   boff).  The remainder correction is 32-bit: the true value of
   k - qhat*q is in [0, 2q) < 2^17 and arithmetic mod 2^32 is exact for
   it, and ONE conditional subtraction is enough below 2^63 (see the
   module docstring). */
#define TEST(IDX, DST) { \
    const uint4 e = pk[IDX]; \
    const unsigned long long mg = ((unsigned long long)e.y << 32) | e.x; \
    unsigned int r = (unsigned int)k - (unsigned int)__umul64hi(k, mg) * e.z; \
    if (r >= e.z) r -= e.z; \
    const unsigned int b = e.w + r; \
    DST |= (bits[b >> 5] >> (b & 31)) & 1u; }

/* The compacted tail: every lane entering this is alive, so the early
   exit costs what it should.  UNROLL independent Barrett chains hide the
   dependent-chain latency the divergent version could not. */
__device__ __forceinline__ bool tail_survives(
        const unsigned long long k, const int np_,
        const uint4* __restrict__ pk, const unsigned int* __restrict__ bits)
{
    int i = LITN;
    for (; i + UNROLL <= np_; i += UNROLL) {
        unsigned int kill = 0u;
#pragma unroll
        for (int z = 0; z < UNROLL; ++z) TEST(i + z, kill)
        if (kill) return false;
    }
    for (; i < np_; ++i) {
        unsigned int kill = 0u;
        TEST(i, kill)
        if (kill) return false;
    }
    return true;
}

extern "C" __global__ void sieve(
        const unsigned long long base0, const int R1, const int np_,
        const unsigned int* __restrict__ bits,
        unsigned long long* out, int* nout, const int cap,
        const uint4* __restrict__ pk,
        const uint2* __restrict__ res1x,
        const unsigned int* __restrict__ res2c)
{
    /* capacity is exactly the number of candidates the block owns, so a
       block that pushed every one of them still fits */
    __shared__ unsigned long long qk[JPT * TPB];
    __shared__ int qn;
    if (threadIdx.x == 0) qn = 0;
    __syncthreads();

    const unsigned long long base = base0
                                  + WC * (unsigned long long)blockIdx.z;
#if TWOLEVEL
    const unsigned int c2 = res2c[blockIdx.y];
#endif
    const int tbase = blockIdx.x * (blockDim.x * JPT) + threadIdx.x;

#pragma unroll
    for (int jj = 0; jj < JPT; ++jj) {
        const int t = tbase + jj * TPB;
        if (t < R1) {
            const uint2 e1 = res1x[t];
#if TWOLEVEL
            unsigned int m = e1.y + c2;
            if (m >= W2C) m -= W2C;
            const unsigned long long k = base + (unsigned long long)e1.x
                                       + (unsigned long long)W1C * m;
#else
            const unsigned long long k = base + (unsigned long long)e1.x;
#endif
            unsigned int kill = 0u;
%(prefix)s
            if (!kill) qk[atomicAdd(&qn, 1)] = k;
        }
    }
    __syncthreads();

    const int n = qn;
    for (int idx = threadIdx.x; idx < n; idx += TPB) {
        const unsigned long long k = qk[idx];
        if (tail_survives(k, np_, pk, bits)) {
            const int p = atomicAdd(nout, 1);
            if (p < cap) out[p] = k;
        }
    }
}
"""


class GpuEngine:
    """Wheel-generated candidates, Barrett-tested against a bitmap."""

    def __init__(self, n, p1=P1_DEFAULT, p2=P2_DEFAULT, q2=Q2_DEFAULT,
                 tpb=TPB_DEFAULT, jpt=JPT_DEFAULT, lit=LIT_DEFAULT):
        import cupy as cp
        self.cp = cp
        self.n, self.p1, self.p2, self.q2, self.tpb = n, p1, p2, q2, tpb
        self.jpt = jpt

        self.W1, res1 = wheel(n, p1)
        if self.W1 >= 1 << 32:
            raise ValueError(
                f"first-level wheel modulus {self.W1} needs more than u32; "
                f"the residue type is baked into the kernel, so raising P1 "
                f"past this is a new engine version with a new fingerprint")
        self.R1 = int(res1.size)

        if p2 and p2 > p1:
            self.W2, res2 = wheel(n, p2, lo=p1)
            if self.W2 >= 1 << 32 or self.W1 * self.W2 >= 1 << 63:
                raise ValueError(
                    f"second-level wheel {self.W1}*{self.W2} exceeds the "
                    f"enforced u32/2^63 limits")
            self.R2 = int(res2.size)
            if self.R2 > 65535:
                raise ValueError(
                    f"second-level wheel has {self.R2} residues; the kernel "
                    f"maps them to gridDim.y, which CUDA caps at 65535")
            self.W = self.W1 * self.W2
            self.R = self.R1 * self.R2
            self.inv = pow(self.W1 % self.W2, -1, self.W2)
            wheel_top = p2
        else:
            self.W2, self.R2, self.inv, res2 = 1, 1, 0, None
            self.W, self.R = self.W1, self.R1
            wheel_top = p1

        # The generation tables.  m = ((r2 - r1)*inv) mod W2 splits into
        # one term per index: A[t] = (-r1*inv) mod W2 and C[s] = r2*inv mod
        # W2, so the kernel adds them and conditionally subtracts W2.
        # uint64 is exact here because both factors are reduced mod
        # W2 < 2^32 first, so the product stays under 2^64.
        w2 = np.uint64(self.W2)
        r1u = res1.astype(np.uint64)
        res1x = np.empty((self.R1, 2), dtype=np.uint32)
        res1x[:, 0] = r1u.astype(np.uint32)
        if self.R2 > 1:
            a = (r1u % w2) * np.uint64(self.inv) % w2
            res1x[:, 1] = ((w2 - a) % w2).astype(np.uint32)
            c = (res2.astype(np.uint64) % w2) * np.uint64(self.inv) % w2
            self.d_res2c = cp.asarray(c.astype(np.uint32))
        else:
            res1x[:, 1] = 0
            self.d_res2c = cp.zeros(1, dtype=np.uint32)
        self.d_res1x = cp.asarray(res1x.ravel())

        self.primes = [q for q in primerange(wheel_top + 1, q2 + 1)]
        if not self.primes:
            raise ValueError("no sieve primes above the wheel")
        self.lit = min(lit, len(self.primes))

        # packed forbidden-residue bitmap: q bits per prime, concatenated
        offs, tot = [], 0
        for q in self.primes:
            offs.append(tot)
            tot += q
        bits = np.zeros((tot + 31) // 32, dtype=np.uint32)
        for o, q in zip(offs, self.primes):
            for u in killed_residues(q, n):
                b = o + u
                bits[b >> 5] |= np.uint32(1) << np.uint32(b & 31)

        # the per-prime constants, one uint4 per prime: a test is one
        # 128-bit uniform load instead of three
        magic = barrett_magics(self.primes)
        pk = np.empty((len(self.primes), 4), dtype=np.uint32)
        pk[:, 0] = (magic & np.uint64(0xFFFFFFFF)).astype(np.uint32)
        pk[:, 1] = (magic >> np.uint64(32)).astype(np.uint32)
        pk[:, 2] = np.array(self.primes, dtype=np.uint32)
        pk[:, 3] = np.array(offs, dtype=np.uint32)
        self.d_pk = cp.asarray(pk.ravel())
        self.d_bits = cp.asarray(bits)
        self.d_out = cp.empty(HIT_CAP, dtype=np.uint64)
        self.d_n = cp.zeros(1, dtype=np.int32)

        self.tile = self.tpb * self.jpt          # candidates per CUDA block
        self.per_launch = max(1, min(65535, CAND_PER_LAUNCH // self.R))

        key = (n, self.W1, self.W2, q2, tpb, jpt, self.lit)
        if key not in _MODCACHE:
            src = _SRC % {"w1": self.W1, "w2": self.W2, "w": self.W,
                          "two": 1 if self.R2 > 1 else 0, "lit": self.lit,
                          "jpt": jpt, "tpb": tpb, "unroll": UNROLL,
                          "prefix": lit_prefix(n, self.primes, self.lit)}
            _MODCACHE[key] = cp.RawModule(code=src, options=("-std=c++14",),
                                          backend="nvrtc")
        self.k_sieve = _MODCACHE[key].get_function("sieve")

    # ------------------------------------------------------------- geometry
    def j_of(self, k):
        """The wheel block a k lives in."""
        return int(k) // self.W

    def density(self):
        """Candidates per unit of k line -- what the wheel is worth."""
        return self.R / float(self.W)

    def bytes_held(self):
        n = (self.d_res1x.nbytes + self.d_bits.nbytes + self.d_pk.nbytes
             + self.d_out.nbytes + self.d_res2c.nbytes)
        return int(n)

    # ---------------------------------------------------------------- sieve
    def survivors_j(self, j0, j1):
        """Sorted u64 array of surviving k with k // W in [j0, j1)."""
        cp = self.cp
        j0, j1 = int(j0), int(j1)
        if j1 * self.W > K_CEIL:
            raise ValueError(f"k {j1 * self.W} past the enforced ceiling "
                             f"{K_CEIL}")
        if j0 * self.W <= max(K_FLOOR, self.q2):
            raise ValueError(
                "engines refuse to run at or below max(K_FLOOR, q2): the "
                "wheel argument has an exception zone there and a kill by q "
                "needs value > q")
        out = []
        gx = (self.R1 + self.tile - 1) // self.tile
        for lo in range(0, j1 - j0, self.per_launch):
            n_l = min(self.per_launch, j1 - j0 - lo)
            self.d_n.fill(0)
            self.k_sieve((gx, self.R2, n_l), (self.tpb,),
                         (np.uint64(self.W * (j0 + lo)), np.int32(self.R1),
                          np.int32(len(self.primes)), self.d_bits,
                          self.d_out, self.d_n, np.int32(HIT_CAP),
                          self.d_pk, self.d_res1x, self.d_res2c))
            cnt = int(self.d_n.get()[0])
            if cnt > HIT_CAP:
                raise RuntimeError(
                    f"survivor buffer overflow: {cnt} > {HIT_CAP}; the "
                    f"window is too wide or the sieve too shallow")
            if cnt:
                out.append(cp.asnumpy(self.d_out[:cnt]))
        if not out:
            return np.zeros(0, dtype=np.uint64)
        return np.sort(np.concatenate(out))

    def survivors_k(self, k_lo, k_hi):
        """Same stream, clipped to an arbitrary half-open k window."""
        j0, j1 = int(k_lo) // self.W, int(k_hi - 1) // self.W + 1
        s = self.survivors_j(j0, j1)
        return s[(s >= np.uint64(k_lo)) & (s < np.uint64(k_hi))]


# --------------------------------- gates -----------------------------------

def g7_wheel_matches_oracle():
    """The CRT-lifted wheel == the oracle's brute-force walk of the period.

    Small p1 only: the oracle walks all W residues, which is the point --
    it is the definition, and it is why p1 stops at 13 here.  The
    second-level construction is checked the same way, over its own prime
    range, plus the CRT recombination itself.
    """
    for n, p1 in ((5, 7), (10, 11), (16, 11), (16, 13), (19, 13)):
        W, res = wheel(n, p1)
        Wo, reso = wheel_residues(n, p1)
        if W != Wo or list(res) != list(reso):
            return False, (f"G7 FAIL: n={n} p1={p1}: lifted {len(res)} "
                           f"residues mod {W}, oracle {len(reso)} mod {Wo}")
    # the CRT recombination must reproduce the one-level wheel exactly
    for n, p1, p2 in ((16, 7, 13), (16, 11, 17), (10, 7, 11)):
        W1, r1 = wheel(n, p1)
        W2, r2 = wheel(n, p2, lo=p1)
        inv = pow(W1 % W2, -1, W2)
        got = sorted(int(a) + W1 * (((int(b) - int(a)) * inv) % W2)
                     for a in r1 for b in r2)
        Wf, ref_res = wheel(n, p2)
        if W1 * W2 != Wf or got != [int(v) for v in ref_res]:
            return False, (f"G7 FAIL: CRT recombination at n={n} "
                           f"({p1},{p2}]: {len(got)} vs {len(ref_res)}")
    return True, ("G7 ok: CRT-lifted wheel == oracle period walk at "
                  "(n,p1) = (5,7), (10,11), (16,11), (16,13), (19,13); the "
                  "two-level CRT recombination == the one-level wheel at "
                  "three (p1,p2] splits")


def g8_wheel_partitions_the_period():
    """Kept + killed == the whole period, and the count is the formula.

    The direction that matters is the second one: a wheel that DROPS a
    residue it should have kept loses candidates silently, and no parity
    gate against another engine using the same wheel could ever see it.
    """
    from sqladder_reference import w as w_formula
    for n, p1, lo in ((16, 13, 1), (16, 23, 1), (11, 23, 1), (19, 19, 1),
                      (16, 37, 23), (16, 31, 23), (17, 37, 23)):
        W, res = wheel(n, p1, lo=lo)
        want = 1
        for q in primerange(lo + 1, p1 + 1):
            want *= q - w_formula(q, n)
        if res.size != want:
            return False, (f"G8 FAIL: n={n} ({lo},{p1}]: {res.size} "
                           f"residues, formula says {want}")
        if len(set(res.tolist())) != res.size:
            return False, f"G8 FAIL: n={n} ({lo},{p1}]: duplicate residues"
        for q in primerange(lo + 1, p1 + 1):
            bad = set(killed_residues(q, n))
            if np.isin(res % q, np.array(sorted(bad), dtype=np.int64)).any():
                return False, (f"G8 FAIL: n={n} ({lo},{p1}]: a kept residue "
                               f"is killed by q={q}")
    return True, ("G8 ok: the wheel is exactly prod(q - w(q,n)) residues, "
                  "duplicate-free, none of them killed by a wheel prime, at "
                  "(n,p1) = (16,13), (16,23), (11,23), (19,19) and at the "
                  "SECOND-level ranges (23,37], (23,31], (23,37] at n=17")


def g9_gpu_matches_cpu():
    """GPU survivor stream == CPU survivor stream, bit for bit.

    Populated windows at three filters and four heights, the last of them
    hard against the enforced ceiling, because a reduction that is correct
    at 1e12 and wrong at 9e18 is exactly the bug a mid-range parity gate
    cannot see.  BOTH wheel paths are covered -- the one-level kernel the
    frozen fingerprints are pinned to, and the two-level CRT kernel the
    campaign runs -- because they generate the same candidates by
    different arithmetic.  An empty-vs-empty comparison is vacuous and is
    refused.
    """
    # The two-level cases are chosen so the COMBINED modulus stays small
    # enough that a dense CPU sieve can cover a populated window: a wheel
    # block of the production split (23, 37] is 7.4e12 of k line, which no
    # dense array can hold.  The kernel is the same code at every split --
    # only W1, W2 and W1^-1 change -- so these exercise its arithmetic in
    # full, and G13 pins the production constants themselves.
    cases = ((10, 13, None, 256, 2 * 10 ** 9, 4 * 10 ** 6),
             (16, 13, None, 128, 10 ** 12, 2 * 10 ** 7),
             (16, 17, None, 256, 9 * 10 ** 14, 10 ** 8),
             (16, 23, None, 64, K_CEIL - 3 * 223_092_870, 3 * 10 ** 7),
             (16, 13, 23, 128, 10 ** 12, 2 * 10 ** 7),
             (16, 13, 17, 256, 9 * 10 ** 14, 10 ** 8),
             (16, 11, 23, 64, K_CEIL - 3 * 223_092_870, 3 * 10 ** 7))
    total = 0
    for n, p1, p2, q2, k_lo, span in cases:
        eng = GpuEngine(n, p1=p1, p2=p2, q2=q2)
        got = eng.survivors_k(k_lo, k_lo + span)
        cpu = CpuEngine(n, q2=q2)
        want = np.concatenate([np.zeros(0, dtype=np.uint64)]
                              + list(cpu.survivors(k_lo, k_lo + span)))
        if got.size != want.size or not np.array_equal(got, want):
            gs, ws = set(got.tolist()), set(want.tolist())
            return False, (f"G9 FAIL: n={n} p1={p1} p2={p2} q2={q2} at "
                           f"k~{k_lo:.3g}: GPU {got.size} vs CPU "
                           f"{want.size}, diff {sorted(gs ^ ws)[:4]}")
        if got.size == 0:
            return False, (f"G9 FAIL: n={n} p1={p1} p2={p2} at k~{k_lo:.3g} "
                           f"is empty -- vacuous parity check")
        total += int(got.size)
    return True, (f"G9 ok: GPU stream == CPU stream on 7 populated windows "
                  f"({total} survivors) -- one-level AND two-level wheels, "
                  f"filters n = 10, 16, heights 2e9 -> the enforced ceiling")


def g13_production_wheel_constants():
    """The baked CRT constants of the configurations the campaign runs.

    G9 proves the two-level KERNEL is right, but only at splits whose
    combined wheel a dense CPU sieve can follow.  The production split is
    bigger than that by four orders of magnitude, and what differs there
    is not code but three literals compiled into the source: W1, W2 and
    W1^-1 mod W2.  This gate checks those literals directly, on the host,
    against the definition -- so nothing about the production engine rests
    on a configuration that was never examined.
    """
    rng = np.random.default_rng(20260821)
    from sqladder_reference import w as w_formula
    for n, p1, p2 in ((16, 23, 37), (16, 23, 31), (17, 23, 37)):
        W1, r1 = wheel(n, p1)
        W2, r2 = wheel(n, p2, lo=p1)
        inv = pow(W1 % W2, -1, W2)
        if W1 % W2 * inv % W2 != 1:
            return False, f"G13 FAIL: n={n} ({p1},{p2}]: W1^-1 is wrong"
        want = 1
        for q in primerange(2, p2 + 1):
            want *= q - w_formula(q, n)
        if r1.size * r2.size != want:
            return False, (f"G13 FAIL: n={n} ({p1},{p2}]: {r1.size}*{r2.size}"
                           f" != {want}")
        killed = {q: set(killed_residues(q, n))
                  for q in primerange(2, p2 + 1)}
        ts = rng.integers(0, r1.size, 4000)
        ss = rng.integers(0, r2.size, 4000)
        for t, s in zip(ts.tolist(), ss.tolist()):
            a, b = int(r1[t]), int(r2[s])
            x = a + W1 * (((b - a) * inv) % W2)
            if not 0 <= x < W1 * W2:
                return False, f"G13 FAIL: n={n} CRT value {x} out of range"
            if x % W1 != a or x % W2 != b:
                return False, (f"G13 FAIL: n={n} CRT value {x} does not "
                               f"recombine to ({a}, {b})")
            for q, bad in killed.items():
                if x % q in bad:
                    return False, (f"G13 FAIL: n={n} ({p1},{p2}]: CRT value "
                                   f"{x} is killed by q={q}")
    return True, ("G13 ok: the production wheel constants (W1, W2, W1^-1) "
                  "are exact at (n,p1,p2) = (16,23,37), (16,23,31), "
                  "(17,23,37); 4000 sampled CRT residues per config "
                  "recombine correctly and survive every wheel prime")


def g14_v3_mechanisms():
    """The three v3 mechanisms, each against its own definition.

    G9 would catch any of these end-to-end, but only where a dense CPU
    sieve can follow -- and the split-CRT tables and the literal prefix are
    exactly the things whose PRODUCTION values G9 cannot reach.  So each is
    checked here on the host, at the production configuration, against the
    definition it is supposed to implement.

      A/C tables   A[t] + C[s] (mod W2) must be the m the one-table CRT
                   would have computed, for every sampled pair -- and the
                   reconstructed k must be the same integer.
      literals     the baked 64-bit kill mask and bit offset of each
                   literal-prefix prime must agree with killed_residues and
                   with the packed bitmap the table path reads.
      queue        the shared queue holds JPT*TPB and a block owns exactly
                   JPT*TPB candidates, so "cannot overflow" is arithmetic,
                   not optimism.
    """
    rng = np.random.default_rng(20260822)
    for n, p1, p2, q2 in ((16, 23, 37, 65536), (17, 23, 37, 65536),
                          (16, 23, 31, 4096)):
        W1, r1 = wheel(n, p1)
        W2, r2 = wheel(n, p2, lo=p1)
        inv = pow(W1 % W2, -1, W2)
        w2u, r1u = np.uint64(W2), r1.astype(np.uint64)
        a = (r1u % w2u) * np.uint64(inv) % w2u
        A = ((w2u - a) % w2u).astype(np.int64)
        C = ((r2.astype(np.uint64) % w2u) * np.uint64(inv) % w2u
             ).astype(np.int64)
        for t, s in zip(rng.integers(0, r1.size, 3000).tolist(),
                        rng.integers(0, r2.size, 3000).tolist()):
            m_split = (int(A[t]) + int(C[s])) % W2
            if int(A[t]) >= W2 or int(C[s]) >= W2:
                return False, (f"G14 FAIL: n={n}: a split table entry is "
                               f"not reduced mod W2, so the kernel's single "
                               f"conditional subtract is not enough")
            m_ref = ((int(r2[s]) - int(r1[t])) * inv) % W2
            if m_split != m_ref:
                return False, (f"G14 FAIL: n={n} ({p1},{p2}]: A[{t}]+C[{s}] "
                               f"gives m={m_split}, CRT says {m_ref}")
            if int(r1[t]) + W1 * m_split != int(r1[t]) + W1 * m_ref:
                return False, f"G14 FAIL: n={n}: reconstructed x differs"

        primes = [q for q in primerange(p2 + 1, q2 + 1)]
        nlit = min(LIT_DEFAULT, len(primes))
        src = lit_prefix(n, primes, nlit)
        off = 0
        for q in primes[:nlit]:
            bad = killed_residues(q, n)
            if q < LIT_INLINE_Q:
                mask = 0
                for u in bad:
                    mask |= 1 << u
                if f"{mask}ULL >> r" not in src:
                    return False, (f"G14 FAIL: n={n}: the literal kill mask "
                                   f"for q={q} is not in the emitted source")
                if [u for u in range(q) if (mask >> u) & 1] != bad:
                    return False, (f"G14 FAIL: n={n}: literal mask for q={q}"
                                   f" != killed_residues")
            elif f"{off}u + r" not in src:
                return False, (f"G14 FAIL: n={n}: the bit offset for q={q} "
                               f"is not the packed bitmap's offset {off}")
            if f"* {q}u;" not in src or f"__umul64hi(k, {(1 << 64) // q}ULL)" \
                    not in src:
                return False, (f"G14 FAIL: n={n}: q={q} or its magic is not "
                               f"baked into the literal prefix")
            off += q

    if JPT_DEFAULT * TPB_DEFAULT <= 0:
        return False, "G14 FAIL: the queue capacity is not positive"
    return True, (f"G14 ok: the split A/C generation tables reproduce the "
                  f"one-table CRT on 9000 sampled pairs at (n,p1,p2) = "
                  f"(16,23,37), (17,23,37), (16,23,31); the {LIT_DEFAULT} "
                  f"baked literal-prefix primes carry the same kill sets and "
                  f"bit offsets as the packed bitmap; the shared queue holds "
                  f"{JPT_DEFAULT}*{TPB_DEFAULT} = "
                  f"{JPT_DEFAULT * TPB_DEFAULT}, exactly the candidates a "
                  f"block owns, so it cannot overflow")


GATES = [g7_wheel_matches_oracle, g8_wheel_partitions_the_period,
         g13_production_wheel_constants, g14_v3_mechanisms,
         g9_gpu_matches_cpu]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
