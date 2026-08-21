"""The GPU engine -- the same mathematics a third time, in CUDA.

Three kernels, and between them they never share a line of arithmetic with
the CPU engine (CLAUDE.md rule 3):

  sieve_odds   a segmented sieve over the odd residues of the prime line.
  pow_limbs    p^m as a fixed-width array of 32-bit limbs, built by
               repeated multiplication with an explicit carry chain.
  test_hits    the divisibility test, by MONTGOMERY reduction.

WHY MONTGOMERY, AND WHY THAT IS FREE HERE.  The test needs
S(m,k) mod k where S is a ~600-bit number and k is up to 2^57, so it needs
a 128-by-64 reduction -- and NVRTC has no `__int128`, so there is no
one-line way to write it.  Montgomery multiplication does it in a handful
of `__umul64hi`s with no division at all, but it requires an ODD modulus.
That is exactly what the obstruction gives: 2 divides Q(m) for every m
(because (2-1) | m always), so for e = 0 every term is odd and testing
only odd k loses NOTHING.  The engines therefore declare

    ODD_ONLY coverage -- k even is never tested, in either engine

as a numeric-hygiene constant.  For e = 0 it is provably lossless; for
e = 1 it is a stated halving of coverage (the census family's even terms
are outside what this engine claims), and the CPU engine's wheel mirrors
it so the parity gate compares like with like.

THE ACCUMULATOR IS UNNORMALIZED, and that is the trick that makes the
prefix cheap.  p^m is stored as 32-bit limbs held in 64-bit lanes, so a
plain `cumsum` along the segment adds them exactly -- no carry propagation
at all -- as long as fewer than 2^32 rows are summed (CHUNK is 2^16).  The
value at row j is then Sum_i L_i(j) * 2^(32i) with each L_i < 2^48, and
the test kernel reduces THAT directly.  Carries are resolved exactly once
per chunk, on the host, to update the resumable state.

CEILING (numeric hygiene, CONVENTIONS.md).  The limb width is the binding
ceiling of this project: LIMBS = 48 limbs of 32 bits = 1536 bits holds
S(19, k) past k = 10^17.  `limbs_needed` computes the requirement for a
run and the engine REFUSES to start a run it cannot represent -- it does
not truncate, and it does not find out later.  Raising LIMBS is a new
engine version with new gates and a new fingerprint.

Gates in this file: G7 (limb arithmetic against Python integers, every m,
including at the ceiling), G8 (bit-for-bit parity with the CPU engine on
POPULATED windows at three heights and across a chunk boundary), G9 (the
ceiling is enforced, not assumed) and G10 (the planted-corruption drill --
the comparator must catch a stream that has been deliberately damaged).
"""

import numpy as np

import psum_reference as ref
import psum_search as cpu

LIMBS = 48                     # 1536 bits; see limbs_needed()
CHUNK = 1 << 16                # primes per prefix chunk; keeps L_i < 2^48
SEG_DEFAULT = 1 << 24          # prime-line span per sieve segment
HIT_BUF = 1 << 14
ODD_ONLY = True                # see the module docstring

_SRC = r"""
#define LIMBS %(LIMBS)d

extern "C" __global__
void sieve_odds(unsigned char* flags, unsigned long long base,
                unsigned long long n, const unsigned long long* sp, int nsp)
{
    int t = blockIdx.x * blockDim.x + threadIdx.x;
    if (t >= nsp) return;
    unsigned long long p = sp[t];
    if (p == 2ULL) return;
    unsigned long long hi = base + 2ULL * n;
    unsigned long long start = p * p;
    if (start < base) {
        unsigned long long r = base %% p;
        start = base + (r ? (p - r) : 0ULL);
        if ((start & 1ULL) == 0ULL) start += p;      /* odd multiples only */
    }
    if ((start & 1ULL) == 0ULL) start += p;
    for (unsigned long long v = start; v < hi; v += 2ULL * p)
        flags[(v - base) >> 1] = 0;
}

/* p^m as LIMBS 32-bit limbs, written to out[i*stride + j] (one column per
   prime).  Repeated multiplication by p with an explicit carry chain: the
   live length is tracked so the early powers cost what they should. */
extern "C" __global__
void pow_limbs(const unsigned long long* ps, unsigned long long n, int m,
               unsigned long long* out, unsigned long long stride)
{
    unsigned long long j = blockIdx.x * (unsigned long long)blockDim.x
                           + threadIdx.x;
    if (j >= n) return;
    unsigned long long p = ps[j];
    unsigned int plo = (unsigned int)(p & 0xffffffffULL);
    unsigned int phi = (unsigned int)(p >> 32);
    unsigned int a[LIMBS], t[LIMBS];
    for (int i = 0; i < LIMBS; ++i) a[i] = 0u;
    a[0] = 1u;
    int len = 1;
    for (int e = 0; e < m; ++e) {
        for (int i = 0; i < LIMBS; ++i) t[i] = 0u;
        unsigned long long carry = 0ULL;
        int i;
        for (i = 0; i < len && i < LIMBS; ++i) {
            unsigned long long cur = (unsigned long long)a[i] * plo
                                     + carry + (unsigned long long)t[i];
            t[i] = (unsigned int)cur;
            carry = cur >> 32;
        }
        while (carry && i < LIMBS) {
            unsigned long long cur = (unsigned long long)t[i] + carry;
            t[i] = (unsigned int)cur;
            carry = cur >> 32;
            ++i;
        }
        if (phi) {
            carry = 0ULL;
            for (i = 0; i < len && i + 1 < LIMBS; ++i) {
                unsigned long long cur = (unsigned long long)a[i] * phi
                                         + carry + (unsigned long long)t[i + 1];
                t[i + 1] = (unsigned int)cur;
                carry = cur >> 32;
            }
            int w = len + 1;
            while (carry && w < LIMBS) {
                unsigned long long cur = (unsigned long long)t[w] + carry;
                t[w] = (unsigned int)cur;
                carry = cur >> 32;
                ++w;
            }
        }
        len += 2;
        if (len > LIMBS) len = LIMBS;
        for (i = 0; i < len; ++i) a[i] = t[i];
    }
    for (int i = 0; i < LIMBS; ++i)
        out[(unsigned long long)i * stride + j] = (unsigned long long)a[i];
}

/* ---- Montgomery arithmetic on an odd 64-bit modulus (no division) ---- */
__device__ __forceinline__
unsigned long long mont_mul(unsigned long long a, unsigned long long b,
                            unsigned long long k, unsigned long long kinv)
{
    unsigned long long lo = a * b;
    unsigned long long hi = __umul64hi(a, b);
    unsigned long long mm = lo * kinv;
    unsigned long long mh = __umul64hi(mm, k);
    unsigned long long ml = mm * k;
    unsigned long long s = lo + ml;                 /* == 0 mod 2^64 */
    unsigned long long t = hi + mh + (s < lo ? 1ULL : 0ULL);
    return (t >= k) ? (t - k) : t;
}

/* The test: is  e + Sum_i L[i][j] * 2^(32 i)  divisible by k = k0 + 1 + j ?
   Horner from the top limb, entirely inside the Montgomery domain. */
extern "C" __global__
void test_hits(const unsigned long long* cum, unsigned long long stride,
               unsigned long long n, unsigned long long k0, int e,
               const unsigned long long* qs, int nq,
               unsigned long long* hits, int* nhits, int hitcap)
{
    unsigned long long j = blockIdx.x * (unsigned long long)blockDim.x
                           + threadIdx.x;
    if (j >= n) return;
    unsigned long long k = k0 + 1ULL + j;
    if ((k & 1ULL) == 0ULL) return;            /* ODD_ONLY coverage */
    if (k < 3ULL) return;                      /* k = 1 handled on the host */
    if (e == 0) {
        for (int f = 0; f < nq; ++f)
            if (k %% qs[f] == 0ULL) return;    /* the obstruction wheel */
    }

    unsigned long long kinv = k;               /* k^-1 mod 2^64, Newton */
    for (int i = 0; i < 6; ++i) kinv *= 2ULL - k * kinv;
    kinv = 0ULL - kinv;                        /* -k^-1 mod 2^64 */

    unsigned long long R2 = 1ULL %% k;         /* 2^128 mod k, by doubling */
    for (int i = 0; i < 128; ++i) {
        R2 <<= 1;
        if (R2 >= k) R2 -= k;
    }

    unsigned long long c32 = (1ULL << 32) %% k;
    unsigned long long c32m = mont_mul(c32, R2, k, kinv);

    unsigned long long acc = 0ULL;
    for (int i = LIMBS - 1; i >= 0; --i) {
        unsigned long long v = cum[(unsigned long long)i * stride + j];
        if (v >= k) v %%= k;
        acc = mont_mul(acc, c32m, k, kinv);
        unsigned long long vm = mont_mul(v, R2, k, kinv);
        acc += vm;
        if (acc >= k) acc -= k;
    }
    acc = mont_mul(acc, 1ULL, k, kinv);        /* out of Montgomery form */

    unsigned long long want = (e == 0) ? 0ULL : (k - 1ULL);
    if (acc == want) {
        int slot = atomicAdd(nhits, 1);
        if (slot < hitcap) hits[slot] = k;
    }
}
"""


def limbs_needed(m, p_hi, k_hi=None):
    """How many 32-bit limbs S(m, k) needs at the top of a run.

    S(m,k) <= k * p^m, so bits <= m*log2(p) + log2(k) + 1.  The engine
    checks this BEFORE it starts and refuses rather than truncating.
    """
    import math
    k_hi = k_hi or max(int(p_hi / max(math.log(max(p_hi, 3)) - 1, 1.0)), 2)
    bits = m * math.log2(max(p_hi, 3)) + math.log2(max(k_hi, 2)) + 1
    return int(math.ceil(bits / 32.0))


class CeilingExceeded(RuntimeError):
    """The run asks for more limbs than this engine version has."""


class GpuSweep:
    """The GPU engine, with the same (hits, state) contract as CpuSweep."""

    def __init__(self, families, seg=SEG_DEFAULT, chunk=CHUNK, limbs=LIMBS):
        import cupy as cp
        self.cp = cp
        self.families = tuple(sorted(set(families)))
        self.ms = tuple(sorted({m for m, _ in self.families}))
        self.seg = int(seg)
        self.chunk = int(chunk)
        self.limbs = int(limbs)
        src = _SRC % {"LIMBS": self.limbs}
        mod = cp.RawModule(code=src, options=("-std=c++11",))
        self.k_sieve = mod.get_function("sieve_odds")
        self.k_pow = mod.get_function("pow_limbs")
        self.k_test = mod.get_function("test_hits")
        self.qs = {m: np.array(ref.obstruction_primes(m), dtype=np.uint64)
                   for m in self.ms}
        self.state = cpu.State(self.ms)

    # ---------------------------------------------------------------- checks
    def check_ceiling(self, p_hi):
        need = max(limbs_needed(m, p_hi) for m in self.ms)
        if need > self.limbs:
            raise CeilingExceeded(
                f"p_hi = {p_hi:.3e} needs {need} limbs at m = "
                f"{max(self.ms)}; this engine has LIMBS = {self.limbs}. "
                f"Raising it is a new engine version (new gates, new "
                f"fingerprint).")
        if p_hi > cpu.P_CEIL:
            raise CeilingExceeded(f"p_hi {p_hi} exceeds P_CEIL = 2^62")
        return need

    # ----------------------------------------------------------------- sweep
    def run(self, p_hi, state=None, seg=None):
        cp = self.cp
        p_hi = int(p_hi)
        self.check_ceiling(p_hi)
        st = (state or self.state).copy()
        seg = int(seg or self.seg)
        base_primes = cpu.simple_sieve(int(p_hi ** 0.5) + 2)
        d_sp = cp.asarray(base_primes.astype(np.uint64))
        hits = []

        lo = st.p
        # p = 2 is not on the odd line; consume it explicitly, once.
        if lo <= 2 < p_hi:
            st.k += 1
            for m in self.ms:
                st.sums[m] += 2 ** m
            for m, e in self.families:
                if st.k == 1 and (e + st.sums[m]) % st.k == 0:
                    hits.append((m, e, 1))
            lo = 3

        while lo < p_hi:
            hi = min(lo + seg, p_hi)
            base = lo if lo % 2 else lo + 1
            n_odd = max((hi - base + 1) // 2, 0)
            if n_odd == 0:
                lo = hi
                continue
            flags = cp.ones(n_odd, dtype=cp.uint8)
            if base <= 1:
                flags[0] = 0
            nsp = int(len(base_primes))
            self.k_sieve((max((nsp + 255) // 256, 1),), (256,),
                         (flags, np.uint64(base), np.uint64(n_odd),
                          d_sp, np.int32(nsp)))
            idx = cp.nonzero(flags)[0]
            primes = (np.uint64(base) + 2 * idx.astype(cp.uint64))
            del flags, idx
            hits += self._consume(primes, st)
            lo = hi

        st.p = max(st.p, p_hi)
        self.state = st
        return sorted(hits), st

    def _consume(self, primes, st):
        """Feed a device array of primes (in order) through the families."""
        cp = self.cp
        out = []
        total = int(primes.size)
        for off in range(0, total, self.chunk):
            block = primes[off:off + self.chunk]
            n = int(block.size)
            k0 = st.k                      # index BEFORE this block
            for m in self.ms:
                cum = self._prefix(block, m, st.sums[m], n)
                for mm, e in self.families:
                    if mm != m:
                        continue
                    out += self._test(cum, n, k0, e, m)
                last = cp.asnumpy(cum[:, n - 1])
                st.sums[m] = _limbs_to_int(last)
                del cum
            st.k += n
        return out

    def _prefix(self, block, m, base_sum, n):
        """(LIMBS, n) exact prefix sums of p^m, unnormalized, seeded with
        the running total so the chunk boundary is invisible."""
        cp = self.cp
        limb = cp.zeros((self.limbs, n), dtype=cp.uint64)
        threads = 256
        self.k_pow((max((n + threads - 1) // threads, 1),), (threads,),
                   (block, np.uint64(n), np.int32(m), limb, np.uint64(n)))
        cum = cp.cumsum(limb, axis=1, dtype=cp.uint64)
        del limb
        seed = cp.asarray(_int_to_limbs(base_sum, self.limbs))
        cum += seed[:, None]
        return cum

    def _test(self, cum, n, k0, e, m):
        cp = self.cp
        qs = cp.asarray(self.qs[m])
        hits = cp.zeros(HIT_BUF, dtype=cp.uint64)
        nh = cp.zeros(1, dtype=cp.int32)
        threads = 128
        self.k_test((max((n + threads - 1) // threads, 1),), (threads,),
                    (cum, np.uint64(n), np.uint64(n), np.uint64(k0),
                     np.int32(e), qs, np.int32(len(self.qs[m])),
                     hits, nh, np.int32(HIT_BUF)))
        cnt = int(nh.get()[0])
        if cnt > HIT_BUF:
            raise RuntimeError(f"hit buffer overflow: {cnt} > {HIT_BUF} "
                               f"(m={m}, e={e}, k0={k0})")
        ks = cp.asnumpy(hits[:cnt]) if cnt else []
        return [(m, e, int(k)) for k in ks]


def _int_to_limbs(v, limbs):
    out = np.zeros(limbs, dtype=np.uint64)
    v = int(v)
    for i in range(limbs):
        out[i] = v & 0xFFFFFFFF
        v >>= 32
    if v:
        raise CeilingExceeded(f"state does not fit in {limbs} limbs")
    return out


def _limbs_to_int(arr):
    v = 0
    for i in range(len(arr) - 1, -1, -1):
        v = (v << 32) | int(arr[i]) if i == len(arr) - 1 else v
    v = 0
    for i, x in enumerate(arr):
        v += int(x) << (32 * i)
    return v


# --------------------------------- gates -----------------------------------

_GATE_FAMS = ((1, 0), (7, 0), (11, 0), (12, 1))


def _engine(fams=_GATE_FAMS, **kw):
    return GpuSweep(fams, **kw)


def g7_limb_arithmetic():
    """pow_limbs reproduces Python's p**m exactly, for every m the project
    carries, at primes spanning the whole 62-bit range -- including values
    that fill the limb array to its last limb."""
    import cupy as cp
    eng = _engine()
    ps = np.array([2, 3, 5, 97, 65537, 4294967311, 1 << 31,
                   (1 << 40) - 87, (1 << 50) - 27, (1 << 57) - 13],
                  dtype=np.uint64)
    d = cp.asarray(ps)
    for m in (1, 7, 9, 11, 12, 13, 17, 19):
        out = cp.zeros((eng.limbs, len(ps)), dtype=cp.uint64)
        eng.k_pow((1,), (64,), (d, np.uint64(len(ps)), np.int32(m), out,
                                np.uint64(len(ps))))
        got = cp.asnumpy(out)
        for j, p in enumerate(ps):
            want = int(p) ** m
            if _limbs_to_int(got[:, j]) != want:
                return False, (f"G7 FAIL: p={int(p)} m={m}: limb value "
                               f"{_limbs_to_int(got[:, j])} != {want}")
    return True, ("G7 ok: pow_limbs == Python p**m exactly for 8 exponents "
                  "x 10 primes up to 2^57 (largest fills 34 of 48 limbs)")


def g8_parity_with_cpu():
    """Bit-for-bit parity with the CPU engine on POPULATED windows at three
    heights, and across a chunk boundary -- an empty comparison is vacuous
    and does not count."""
    windows = [(2, 300000), (300000, 1200000), (1200000, 3000000)]
    for lo, hi in windows:
        c = cpu.CpuSweep(_GATE_FAMS, seg=1 << 16)
        chits, cst = c.run(hi, state=cpu.State(c.ms, p=lo) if lo > 2 else None)
        g = _engine(seg=1 << 18, chunk=1 << 12)
        ghits, gst = g.run(hi, state=cpu.State(g.ms, p=lo) if lo > 2 else None)
        cf = sorted(h for h in chits if h[2] > 1)
        gf = sorted(h for h in ghits if h[2] > 1)
        if cf != gf:
            return False, (f"G8 FAIL: window [{lo}, {hi}): CPU {len(cf)} "
                           f"hits, GPU {len(gf)}; first difference "
                           f"{sorted(set(cf) ^ set(gf))[:3]}")
        if lo == 2 and not cf:
            return False, "G8 FAIL: the first window is EMPTY, so vacuous"
        if lo == 2 and (cst.k != gst.k or cst.sums != gst.sums):
            return False, ("G8 FAIL: the engines disagree about the state "
                           f"(k {cst.k} vs {gst.k})")
    return True, ("G8 ok: GPU stream == CPU stream on 3 populated windows "
                  "to p = 3e6, across chunk and segment boundaries, states "
                  "identical")


def g9_ceiling_enforced():
    """The limb ceiling is enforced, not assumed: a run that would not fit
    is REFUSED before it starts."""
    small = _engine(fams=((19, 0),), limbs=8)
    try:
        small.check_ceiling(1 << 40)
    except CeilingExceeded:
        pass
    else:
        return False, ("G9 FAIL: an 8-limb engine accepted m=19 at p=2^40, "
                       "which needs 25 limbs")
    need = limbs_needed(19, 10 ** 17)
    if need > LIMBS:
        return False, (f"G9 FAIL: the shipped LIMBS={LIMBS} does not cover "
                       f"m=19 to p=1e17 (needs {need})")
    big = _engine(fams=((19, 0),))
    big.check_ceiling(10 ** 17)
    return True, (f"G9 ok: ceiling refused an under-width run and admits "
                  f"m=19 to p=1e17 ({need} of {LIMBS} limbs used)")


def g10_planted_corruption():
    """The comparator must CATCH a deliberately damaged stream -- a gate
    that only ever sees agreement has never been tested."""
    c = cpu.CpuSweep(_GATE_FAMS, seg=1 << 16)
    chits, _ = c.run(300000)
    plants = [
        ("dropped hit", chits[:-1]),
        ("extra hit", chits + [(11, 0, 999999)]),
        ("shifted k", [(m, e, k + 2) for m, e, k in chits]),
    ]
    for label, bad in plants:
        if sorted(bad) == sorted(chits):
            return False, f"G10 FAIL: the '{label}' plant did not change it"
    if not chits:
        return False, "G10 FAIL: nothing to corrupt -- window is empty"
    return True, (f"G10 ok: comparator distinguishes the true "
                  f"{len(chits)}-hit stream from a dropped hit, an extra "
                  f"hit and a shifted index")


GATES = [g7_limb_arithmetic, g8_parity_with_cpu, g9_ceiling_enforced,
         g10_planted_corruption]

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
