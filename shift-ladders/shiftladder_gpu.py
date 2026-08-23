"""shiftladder_gpu.py -- the GPU engine for A130003 and A110096.

The same mathematics a third time, on the device, and never trusted alone:
G9 pins its survivor stream bit-for-bit against the CPU engine on populated
windows at several heights, including above 2^64.

    A(b, n) = least m with m + b^k prime for k = 1..n

WHAT THE KERNEL DOES.  A candidate is killed by a prime q exactly when
m mod q lands in K(q,n,b) = { -b^k mod q }, so the engine never forms a
value: it enumerates the m that already survive every prime up to the
WHEEL, and tests each of those against the remaining primes by one Barrett
reduction and one bit lookup, bailing out at the first kill.  With the
wheel at 23 (base 4) the expected number of tests before a kill is about
three, which is what makes the sieve depth nearly free.

  m = base + off,   base = j0 * W (a host big int),   off < nper * W

THE (m, off) CARRY IS HERE FROM THE FIRST COMMIT, and that is deliberate.
OPTIMIZATION.md 2.7 says to carry candidates as a pair rather than let a
machine word bound the search, because the alternative is growing a second
engine at 2^64 later; square-ladders raised its ceiling twice and the
second time cost a campaign stretch.  Nothing on this device ever holds an
absolute m: the kernel reduces `basemod[t] + off`, where `basemod[t] =
base mod q_t` is folded once per launch on the host.  The enforced ceiling
is therefore the primality-proof bound (3.317e24 minus b^n), not a word,
and G15 checks that the stream does not depend on where the launch base
was put.

THE WHEEL IS A FLAT RESIDUE TABLE, and this is v1's one deliberate
simplification.  The table holds every m mod W that survives the primes up
to p1, built by CRT lifting (gated against the oracle's brute-force walk in
G7).  The two families need different p1 for the same reason they have
different everything -- ord_q(2) reaches q-1 where ord_q(4) cannot exceed
(q-1)/2, so the b = 2 wheel is thousands of times sparser and its table
stays small much further up:

    b = 4, n = 19, p1 = 23:  1,572,480 residues mod 2.23e8  (7.1e-3 of line)
    b = 2, n = 17, p1 = 37:  5,391,360 residues mod 7.42e12 (7.3e-7 of line)

A factored multi-level wheel -- the same CRT lift applied to a table too
big to hold, as square-ladders does to reach 47 -- is the FIRST
optimization this project owes and is priced in OPTIMIZATION_LOG.md.  It
is not here yet, and the campaign numbers in the README say so.

Gates here: G7 (the CRT-lifted wheel == the oracle's period walk), G8 (the
wheel is exactly prod(q - w) residues, duplicate-free, none of them
killed), G9 (GPU stream == CPU stream on populated windows, both bases,
including above 2^64), G15 (the stream is invariant under the launch base
and the launch split, which is what makes the (m, off) carry checkable).
"""

import math
import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                       # noqa: E402
from huntlib.gpu import barrett_magics                          # noqa: E402
from shiftladder_reference import K_FLOOR, w                    # noqa: E402
from shiftladder_search import (CpuEngine, Q2_DEFAULT,          # noqa: E402
                                k_ceil, killed_residues, m_floor)

# The wheel top per base.  Both are the largest prime whose flat residue
# table still fits comfortably in device memory at the production filter;
# they differ by six primes because the b = 2 wheel is far sparser.
P1_DEFAULT = {4: 23, 2: 37}

# Barrett reduces `basemod + off`, which must stay a u64.  Keeping it under
# 2^63 leaves a full bit of margin and is what bounds a launch: nper * W +
# q2 < REDUCE_MAX.  Stated as an enforced constant, not an assumption
# (CONVENTIONS.md "Numeric hygiene"); the ceiling drill exercises it.
REDUCE_MAX = 1 << 63

# The flat residue table's own ceiling.  v1 holds the whole wheel as a
# list, so "which primes fit in the wheel" is a MEMORY question and it is
# answered here, by refusing, rather than by an allocation that fails
# 183 GiB in: the b = 2 wheel reaches 1.29e9 residues at p1 = 47.  A
# multi-level wheel is what raises this, and that is the first
# optimization on the list.
RES_MAX = 1 << 25                # 33.5M residues = 268 MB as int64
HIT_CAP = 1 << 20                # survivors per launch before we refuse
TPB = 256


_WHEELS = {}


def wheel(n, b, p1):
    """(W, residues): every m mod W surviving the primes q <= p1.

    Built by CRT lifting -- start from the empty product and, at each new
    prime, keep the q - w(q,n,b) lifts of every surviving residue that q
    does not kill.  The oracle builds the same set by walking the whole
    period; G7 pins the two together on small p1, which is the only place
    the walk is affordable.

    The residues are int64, which is a claim and not a convenience: W is
    bounded by REDUCE_MAX below (the Barrett input has to stay a u64), so
    a wheel whose modulus would not fit is refused here rather than
    wrapping silently.
    """
    key = (n, b, p1)
    if key in _WHEELS:
        return _WHEELS[key]
    # BOTH ceilings are computed before a single residue is built: the
    # modulus and the residue count are plain products, so a wheel that
    # would not fit is refused here rather than part way through an
    # allocation.  (It was the other way round for one commit, and the
    # b = 2 wheel at p1 = 47 asked numpy for 183 GiB.)
    qs = list(primerange(2, p1 + 1))
    W_final, R_final = 1, 1
    for q in qs:
        W_final *= q
        R_final *= q - w(q, n, b)
    if W_final >= REDUCE_MAX:
        raise ValueError(f"wheel modulus {W_final} passes the Barrett bound "
                         f"{REDUCE_MAX}: pick a smaller p1")
    if R_final > RES_MAX:
        raise ValueError(f"a flat wheel at p1 = {p1} would hold {R_final} "
                         f"residues, past RES_MAX = {RES_MAX}: it needs the "
                         f"multi-level table, not a bigger allocation")
    W, res = 1, np.zeros(1, dtype=np.int64)
    for q in qs:
        killed = np.array(sorted(killed_residues(q, n, b)), dtype=np.int64)
        ginv = pow(W, -1, q)              # W is squarefree, so this exists
        # r + W*t is killed exactly when t == (u - r) * W^-1 (mod q)
        bad = ((killed[None, :] - (res % q)[:, None]) * ginv) % q
        keep = np.ones((res.size, q), dtype=bool)
        keep[np.arange(res.size)[:, None], bad] = False
        res = (res[:, None] + np.arange(q, dtype=np.int64) * W)[keep]
        W *= q
    res.sort()
    _WHEELS[key] = (W, res)
    return W, res


class GpuEngine:
    """Wheel enumeration plus a Barrett test loop, on the device."""

    KERNEL = r"""
extern "C" __global__ void shift_sieve(
    const unsigned long long* __restrict__ res, const int R,
    const unsigned long long W,
    const int np_,
    const unsigned int* __restrict__ pq,
    const unsigned long long* __restrict__ magic,
    const unsigned int* __restrict__ bmoff,
    const unsigned int* __restrict__ basemod,
    const unsigned int* __restrict__ bits,
    unsigned long long* out, unsigned int* cnt, const int cap)
{
    const int ri = blockIdx.x * blockDim.x + threadIdx.x;
    if (ri >= R) return;
    /* one block row per period: no 64-bit division in the inner index */
    const unsigned long long off =
        (unsigned long long)blockIdx.y * W + res[ri];
    for (int t = 0; t < np_; ++t) {
        const unsigned int q = pq[t];
        /* the absolute m never exists on the device: the base arrives
           already reduced, per prime, folded on the host once per launch */
        const unsigned long long p = (unsigned long long)basemod[t] + off;
        const unsigned long long qhat = __umul64hi(p, magic[t]);
        unsigned long long r = p - qhat * (unsigned long long)q;
        if (r >= q) r -= q;
        if (r >= q) r -= q;
        const unsigned int idx = bmoff[t] + (unsigned int)r;
        if ((bits[idx >> 5] >> (idx & 31)) & 1u) return;   /* killed */
    }
    const unsigned int slot = atomicAdd(cnt, 1u);
    if (slot < (unsigned int)cap) out[slot] = off;
}
"""

    def __init__(self, n, b, p1=None, q2=Q2_DEFAULT, per_launch=None):
        import cupy as cp
        self.cp = cp
        self.n, self.b, self.q2 = int(n), int(b), int(q2)
        self.p1 = int(p1 if p1 is not None else P1_DEFAULT[b])
        self.W, res = wheel(self.n, self.b, self.p1)
        self.R = int(res.size)
        self.d_res = cp.asarray(res.astype(np.uint64))

        self.primes = [q for q in primerange(self.p1 + 1, self.q2 + 1)]
        self.d_pq = cp.asarray(np.array(self.primes, dtype=np.uint32))
        self.d_magic = cp.asarray(barrett_magics(self.primes))
        # one bit per residue per prime, concatenated; the offsets are the
        # running sum, so a lookup is one add and one shift
        offs, total = [], 0
        for q in self.primes:
            offs.append(total)
            total += q
        self.bmoff = np.array(offs, dtype=np.uint32)
        self.d_bmoff = cp.asarray(self.bmoff)
        bits = np.zeros((total + 31) // 32, dtype=np.uint32)
        for t, q in enumerate(self.primes):
            for u in killed_residues(q, self.n, self.b):
                i = offs[t] + u
                bits[i >> 5] |= np.uint32(1) << np.uint32(i & 31)
        self.d_bits = cp.asarray(bits)

        # A launch covers whole periods, so `per_launch` is bounded by the
        # Barrett input and by gridDim.y -- both enforced, neither assumed.
        # The DEFAULT is sized from the wheel rather than fixed, because a
        # coarse wheel has few residues per period: 64 periods is 1e8
        # candidates at p1 = 23 and 65,000 at p1 = 13, and at the second of
        # those the per-launch host work would be most of the wall clock.
        # Aim at a constant amount of DEVICE work instead -- 2^29
        # candidates, which is where both families plateau in an
        # interleaved sweep (1.15x over 128 periods at base 4, 1.43x over
        # 12 at base 2; see OPTIMIZATION_LOG.md).
        cap = max(1, (REDUCE_MAX - self.q2) // self.W)
        want = per_launch or max(1, (1 << 29) // max(self.R, 1))
        self.per_launch = int(min(want, cap, 65535))
        if self.per_launch < 1:
            raise ValueError(f"one period ({self.W}) already exceeds the "
                             f"Barrett bound {REDUCE_MAX}")
        self.d_out = cp.empty(HIT_CAP, dtype=cp.uint64)
        self.d_cnt = cp.zeros(1, dtype=cp.uint32)
        self.kernel = cp.RawKernel(self.KERNEL, "shift_sieve")

    # ------------------------------------------------------------ metadata
    def config(self):
        return {"engine": "v1", "n": self.n, "b": self.b, "p1": self.p1,
                "q2": self.q2, "W": self.W, "R": self.R,
                "per_launch": self.per_launch}

    def nbytes(self):
        return int(self.d_res.nbytes + self.d_bits.nbytes + self.d_pq.nbytes
                   + self.d_magic.nbytes + self.d_bmoff.nbytes
                   + self.d_out.nbytes)

    def density(self):
        """Wheel survivors per unit of m line -- the cost driver."""
        return self.R / self.W

    # --------------------------------------------------------------- sweep
    def sweep(self, j0, j1):
        """Yield (j_next, survivors) after every launch.

        `j_next` is BOTH cursors at once: the flat wheel emits a period's
        candidates within one launch, so the line below j_next * W is
        swept and the work resumes there too.  When the multi-level wheel
        lands, the two separate (CONVENTIONS.md "Two cursors, when coverage
        is coarser than work") -- and the launcher is already written to
        take them as two.

        The bounds are checked EAGERLY, here, and the launches are a
        separate generator: a `yield` in this body would defer every check
        to the first `next()`, and a caller that built the iterator and
        never consumed it would sail past the ceiling in silence.
        """
        j0, j1 = int(j0), int(j1)
        ceil = k_ceil(self.n, self.b)
        if j1 * self.W > ceil:
            raise ValueError(f"m {j1 * self.W} past the enforced ceiling "
                             f"{ceil}")
        if j0 * self.W <= m_floor(self.q2):
            raise ValueError(
                "engines refuse to run at or below max(K_FLOOR, q2): the "
                "wheel argument has an exception zone there and a kill by q "
                "needs value > q")
        return self._sweep(j0, j1)

    def _sweep(self, j0, j1):
        cp = self.cp
        grid_x = (self.R + TPB - 1) // TPB
        # `base mod q` for 6,500 primes is 6,500 big-int divisions, and at
        # one per launch that was HALF the wall clock of a production
        # launch and 97% of a coarse-wheel one.  The base advances by a
        # fixed step between launches, so it is computed in full once per
        # sweep and stepped in numpy after that; a short final launch falls
        # back to the full computation, which happens at most once.
        step = np.array([(self.per_launch * self.W) % q for q in self.primes],
                        dtype=np.uint64)
        pq64 = np.array(self.primes, dtype=np.uint64)
        basemod = None
        for lo in range(j0, j1, self.per_launch):
            nper = min(self.per_launch, j1 - lo)
            base = self.W * lo
            if basemod is None:
                basemod = np.array([base % q for q in self.primes],
                                   dtype=np.uint64)
            d_basemod = cp.asarray(basemod.astype(np.uint32))
            basemod = (basemod + step) % pq64 if nper == self.per_launch                 else None
            self.d_cnt.fill(0)
            self.kernel((grid_x, nper), (TPB,),
                        (self.d_res, np.int32(self.R),
                         np.uint64(self.W), np.int32(len(self.primes)),
                         self.d_pq, self.d_magic, self.d_bmoff, d_basemod,
                         self.d_bits, self.d_out, self.d_cnt,
                         np.int32(HIT_CAP)))
            cnt = int(self.d_cnt.get()[0])
            if cnt > HIT_CAP:
                raise RuntimeError(
                    f"survivor buffer overflow: {cnt} > {HIT_CAP}; the "
                    f"launch is too wide or the sieve too shallow")
            surv = []
            if cnt:
                offs = cp.asnumpy(self.d_out[:cnt])
                surv = sorted(base + int(o) for o in offs)
            yield lo + nper, surv

    def survivors_j(self, j0, j1):
        out = []
        for _jn, surv in self.sweep(j0, j1):
            out.extend(surv)
        return out

    def survivors_m(self, m_lo, m_hi):
        """The same stream, clipped to an arbitrary half-open m window."""
        m_lo, m_hi = int(m_lo), int(m_hi)
        j0, j1 = m_lo // self.W, (m_hi - 1) // self.W + 1
        return [m for m in self.survivors_j(j0, j1) if m_lo <= m < m_hi]


# --------------------------------- gates -----------------------------------

def g7_wheel_matches_oracle():
    """The CRT-lifted wheel == the oracle's brute-force period walk."""
    from shiftladder_reference import wheel_residues
    checks = 0
    for b, n, p1 in ((4, 5, 7), (4, 12, 11), (2, 9, 11), (2, 17, 13),
                     (4, 19, 13)):
        W, res = wheel(n, b, p1)
        W2, want = wheel_residues(n, b, p1)
        got = [int(x) for x in res]
        if W != W2 or got != sorted(want):
            return False, (f"G7 FAIL: b={b} n={n} p1={p1}: {len(got)} "
                           f"lifted vs {len(want)} walked")
        if not want:
            return False, f"G7 FAIL: b={b} n={n} p1={p1} wheel is empty"
        checks += len(want)
    return True, (f"G7 ok: CRT-lifted wheel == oracle period walk at 5 "
                  f"(b, n, p1) settings ({checks} residues), both bases")


def g8_wheel_is_exactly_the_product():
    """|wheel| = prod (q - w(q,n,b)), duplicate-free, nothing killed."""
    for b, n, p1 in ((4, 19, 23), (4, 12, 19), (2, 17, 37), (2, 21, 23)):
        W, res = wheel(n, b, p1)
        want = 1
        for q in primerange(2, p1 + 1):
            want *= q - w(q, n, b)
        if res.size != want:
            return False, (f"G8 FAIL: b={b} n={n} p1={p1}: {res.size} "
                           f"residues, formula says {want}")
        ints = [int(x) for x in res]
        if len(set(ints)) != len(ints):
            return False, f"G8 FAIL: b={b} n={n} p1={p1}: duplicate residues"
        tables = {q: set(killed_residues(q, n, b))
                  for q in primerange(2, p1 + 1)}
        for r in ints[::max(1, len(ints) // 512)]:
            for q, killed in tables.items():
                if r % q in killed:
                    return False, (f"G8 FAIL: b={b} n={n} p1={p1}: residue "
                                   f"{r} is killed by {q}")
    return True, ("G8 ok: the wheel is exactly prod(q - w(q,n,b)) residues, "
                  "duplicate-free and unkilled, at (b,n,p1) = (4,19,23), "
                  "(4,12,19), (2,17,37), (2,21,23)")


def g9_gpu_matches_cpu():
    """GPU stream == CPU stream, bit for bit, on POPULATED windows.

    Both bases, several heights, and the top window sits ABOVE 2^64 -- the
    whole point of carrying (m, off), and a comparison of two empty sets
    would be no check at all, so each window is asserted non-empty.
    """
    cases = ((4, 5, 7, 64, 20_000, 400_000),
             (4, 12, 13, 128, 3_000_000, 2_000_000),
             (2, 9, 11, 64, 50_000, 2_000_000),
             (2, 14, 13, 64, 10_000_000, 20_000_000),
             (4, 8, 11, 64, 1 << 64, 4_000_000),
             (2, 10, 13, 64, (1 << 64) + 10 ** 12, 20_000_000))
    total = 0
    for b, n, p1, q2, m_lo, span in cases:
        eng = GpuEngine(n, b, p1=p1, q2=q2, per_launch=8)
        got = eng.survivors_m(m_lo, m_lo + span)
        cpu = CpuEngine(n, b, q2=q2)
        want = []
        for chunk in cpu.survivors(m_lo, m_lo + span):
            want.extend(int(x) for x in chunk)
        if got != want:
            bad = sorted(set(got) ^ set(want))[:4]
            return False, (f"G9 FAIL: b={b} n={n} p1={p1} q2={q2} window "
                           f"{m_lo}+{span}: {len(got)} GPU vs {len(want)} "
                           f"CPU, symmetric difference {bad}")
        if not want:
            return False, (f"G9 FAIL: b={b} n={n} window {m_lo}+{span} is "
                           f"empty -- vacuous check")
        total += len(want)
    return True, (f"G9 ok: GPU stream == CPU stream on {len(cases)} "
                  f"populated windows ({total} survivors), both bases, "
                  f"heights 2e4 -> 1.8e19, the top two ABOVE 2^64")


def g15_stream_is_invariant_under_the_base():
    """Nothing on the device may depend on where the launch base was put.

    Two checks, and the second is the one that matters for (m, off): the
    same window swept in one launch and in six must give the identical
    stream, and a window whose base is a big int far above 2^64 must give
    the stream the CPU engine gives -- which is only true if `basemod` is
    the exact fold of that base.
    """
    b, n, p1, q2 = 4, 8, 11, 64
    eng1 = GpuEngine(n, b, p1=p1, q2=q2, per_launch=64)
    eng6 = GpuEngine(n, b, p1=p1, q2=q2, per_launch=3)
    j0 = (10 ** 6) // eng1.W + 1
    a = eng1.survivors_j(j0, j0 + 18)
    c = eng6.survivors_j(j0, j0 + 18)
    if a != c or not a:
        return False, (f"G15 FAIL: {len(a)} survivors in one launch vs "
                       f"{len(c)} in six")
    folds = 0
    for base_m in (10 ** 12, 1 << 64, 10 ** 24, 3 * 10 ** 24):
        eng = GpuEngine(n, b, p1=p1, q2=q2, per_launch=4)
        j = base_m // eng.W
        lo, hi = j * eng.W, (j + 4) * eng.W
        if hi > k_ceil(n, b):
            continue
        got = eng.survivors_j(j, j + 4)
        cpu = CpuEngine(n, b, q2=q2)
        want = []
        for chunk in cpu.survivors(max(lo, m_floor(q2) + 1), hi):
            want.extend(int(x) for x in chunk)
        if got != want:
            return False, (f"G15 FAIL: base {base_m:.3g}: {len(got)} GPU vs "
                           f"{len(want)} CPU")
        folds += len(want)
    return True, (f"G15 ok: the survivor stream is invariant under the "
                  f"launch split (18 periods, 1 launch vs 6), and the base "
                  f"fold is exact at m = 1e12, 2^64, 1e24 and 3e24 "
                  f"({folds} survivors) -- so nothing on the device is "
                  f"bounded by a machine word")


GATES = [g7_wheel_matches_oracle, g8_wheel_is_exactly_the_product,
         g9_gpu_matches_cpu, g15_stream_is_invariant_under_the_base]

if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
