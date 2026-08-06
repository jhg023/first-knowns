# euler_search.py -- CPU engine for the A164926 Euler-ladder hunt.
#
# Pipeline (independent of the oracle; gated against it):
#   wheel   : p restricted to residues mod 23# = 223092870 that survive the
#             n forbidden classes of every wheel prime (2..23)
#   stage 1 : bitmask kill by primes 29..Q1 (numpy, compress-as-you-go)
#   stage 2 : kill by primes Q1..Q2 via the exact 17-value divisibility test
#   MR      : deterministic 7-base Miller-Rabin (valid < 3.317e24) on the
#             n values; survivors get their EXACT run computed
# The engine only ever *proposes*; launch.py's three-way verification
# (sympy + this MR + fresh window re-sieve) decides.
#
# Correctness floor: sieve assumes every value x^2+x+p > Q2, so the engine
# refuses p < P_FLOOR; [2, P_FLOOR) belongs to the oracle low-pass.
#
# Phase 2 adds CpuEngine128 (exact-int windows above the u64 cap, to
# P128_CEIL = 1e24) with gates G9 (bit-for-bit overlap parity vs the
# proven u64 engine) and G10 (direct big-int trial-division parity on
# above-cap mini-windows + Waldvogel-Leikauf run-21 rediscovery).
#
# ASCII only.

import numpy as np
from sympy import primerange

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.primes import MR_BASES, mr_is_prime as mr_is_prime_u64  # noqa: E402

from euler_reference import A21_UPPER, KNOWN, run_length

WHEEL_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23]
WHEEL_PRIMES_29 = WHEEL_PRIMES + [29]
M_WHEEL = 223092870                     # product of WHEEL_PRIMES
M_WHEEL_29 = 6469693230                 # product incl. 29
Q1 = 1024                               # stage-1 prime bound
Q2 = 65536                              # stage-2 prime bound
P_FLOOR = 100_000                       # engine floor (> Q2 guard is at 65536;
                                        # floor at 1e5 keeps a safety margin)

def forbidden(q, n):
    """Residues r mod q killed: q | x^2+x+p for some x < n when p = r."""
    return {(-(x * x + x)) % q for x in range(n)}


def build_wheel(n, wheel_primes=None):
    """Admissible offsets mod prod(wheel_primes) via CRT lifting (numpy)."""
    wheel_primes = wheel_primes or WHEEL_PRIMES
    offs = np.array([0], dtype=np.uint64)
    m = 1
    for q in wheel_primes:
        F = forbidden(q, n)
        lift = (offs[None, :] + (np.arange(q, dtype=np.uint64) * m)[:, None]).ravel()
        keep = ~np.isin((lift % q).astype(np.int64), np.fromiter(F, dtype=np.int64))
        offs = lift[keep]
        m *= q
    offs.sort()
    return offs, m


def stage_primes(after=23):
    s1 = np.array([q for q in primerange(after + 1, Q1)], dtype=np.uint64)
    s2 = np.array([q for q in primerange(Q1, Q2)], dtype=np.uint64)
    return s1, s2


def mr_run_length(p, cap=100):
    x = 0
    while x < cap and mr_is_prime_u64(x * x + x + p):
        x += 1
    return x


class CpuEngine:
    """Streams survivors of the run->=n pre-filter over [lo, hi)."""

    def __init__(self, n, wheel_primes=None):
        self.n = n
        self.wheel_primes = wheel_primes or WHEEL_PRIMES
        self.offs, self.M = build_wheel(n, self.wheel_primes)
        self.s1, self.s2 = stage_primes(after=self.wheel_primes[-1])
        # stage-1 lookup tables: per prime, bool array of killed residues
        self.luts = {}
        for q in self.s1:
            lut = np.zeros(int(q), dtype=bool)
            lut[list(forbidden(int(q), n))] = True
            self.luts[int(q)] = lut
        self.xx = [x * x + x for x in range(n)]

    def survivors_pre_mr(self, lo, hi, chunk_periods=32):
        """Yield numpy arrays of p in [lo, hi) surviving wheel+stage1+stage2."""
        if lo < P_FLOOR:
            raise ValueError("CPU engine floor is %d; use the oracle below" % P_FLOOR)
        k0 = lo // self.M
        k1 = hi // self.M + 1
        for kc in range(k0, k1, chunk_periods):
            ks = np.arange(kc, min(kc + chunk_periods, k1), dtype=np.uint64)
            p = (ks[:, None] * np.uint64(self.M) + self.offs[None, :]).ravel()
            p = p[(p >= lo) & (p < hi)]
            # stage 1: compress after each prime
            for q in self.s1:
                qi = int(q)
                p = p[~self.luts[qi][(p % q).astype(np.int64)]]
                if p.size == 0:
                    break
            if p.size == 0:
                continue
            # stage 2: exact divisibility of the n values
            alive = np.ones(p.size, dtype=bool)
            for q in self.s2:
                r = p % q
                dead = np.zeros(p.size, dtype=bool)
                for xx in self.xx:
                    dead |= (r + np.uint64(xx)) % q == 0
                alive &= ~dead
            p = p[alive]
            if p.size:
                yield p

    def hunt(self, lo, hi, cap=100):
        """All (p, exact_run) with run >= n in [lo, hi), ascending."""
        out = []
        for arr in self.survivors_pre_mr(lo, hi):
            for p in arr.tolist():
                # cheap first: value at x=0..n-1 must all be prime
                good = all(mr_is_prime_u64(p + xx) for xx in self.xx)
                if good:
                    out.append((p, mr_run_length(p, cap=cap)))
        return out


# ---------------------- phase 2: 128-bit value path ------------------------
#
# Above the u64 cap, p itself no longer fits numpy's u64.  The engines
# never materialize it: every candidate is carried as the pair (k, off)
# with p = k*M + off, off < M, and every sieve test needs only
#     p mod q = ((k mod q) * (M mod q) + (off mod q)) mod q
# which is u64-safe for any p below the ceiling (k < 2^48, products
# < 2^32).  Exact p values exist only as host-side Python ints.  The
# proven u64 engines above are untouched; parity gates pin the 128 path
# against them on their common range.

P128_CEIL = 10**24
# Enforced value ceiling of the 128-bit path.  Everything the engines
# and the MR chain touch (values x^2+x+p <= p + 10100 at run cap 100)
# stays a factor >3 below huntlib's deterministic-MR validity bound
# 3.317e24 (Sorenson-Webster 7-base).  Raising this is a new engine
# version: new gates, new fingerprint, log entry.


class CpuEngine128:
    """Phase-2 CPU engine: streams pre-MR survivors of [lo, hi) with
    lo/hi/survivors as exact Python ints, valid up to P128_CEIL.

    Same mathematics as CpuEngine, third implementation of the residue
    arithmetic (plain numpy `%` on (k, off) pairs -- the GPU twin uses
    Barrett; the two must never share code).  Yields sorted lists of
    Python ints."""

    def __init__(self, n, wheel_primes=None):
        self.n = n
        self.wheel_primes = wheel_primes or WHEEL_PRIMES_29
        self.offs, self.M = build_wheel(n, self.wheel_primes)
        self.s1, self.s2 = stage_primes(after=self.wheel_primes[-1])
        self.luts = {}
        for q in self.s1:
            lut = np.zeros(int(q), dtype=bool)
            lut[list(forbidden(int(q), n))] = True
            self.luts[int(q)] = lut
        self.xx = [x * x + x for x in range(n)]

    def survivors_pre_mr(self, lo, hi, chunk_periods=16):
        """Yield sorted lists of survivor p (Python ints) in [lo, hi)."""
        lo, hi = int(lo), int(hi)
        if lo < P_FLOOR:
            raise ValueError("128 engine floor is %d" % P_FLOOR)
        if hi > P128_CEIL:
            raise ValueError("128 engine ceiling is %d" % P128_CEIL)
        M = int(self.M)
        k0, k1 = lo // M, hi // M + 1
        s_lo = lo - k0 * M            # p >= lo  <=>  k > k0 or off >= s_lo
        kh, s_hi = hi // M, hi % M    # p < hi   <=>  k < kh or (k == kh and off < s_hi)
        for kc in range(k0, k1, chunk_periods):
            ks = np.arange(kc, min(kc + chunk_periods, k1), dtype=np.uint64)
            K = np.repeat(ks, self.offs.size)
            O = np.tile(self.offs, ks.size)
            keep = (((K < np.uint64(kh)) | ((K == np.uint64(kh)) & (O < np.uint64(s_hi))))
                    & ((K > np.uint64(k0)) | (O >= np.uint64(s_lo))))
            K, O = K[keep], O[keep]
            # stage 1: compress after each prime
            for q in self.s1:
                qq = np.uint64(q)
                Mq = np.uint64(M % int(q))
                r = ((K % qq) * Mq + (O % qq)) % qq
                dead = self.luts[int(q)][r.astype(np.int64)]
                K, O = K[~dead], O[~dead]
                if K.size == 0:
                    break
            if K.size == 0:
                continue
            # stage 2: exact divisibility of the n values
            alive = np.ones(K.size, dtype=bool)
            for q in self.s2:
                qq = np.uint64(q)
                Mq = np.uint64(M % int(q))
                r = ((K % qq) * Mq + (O % qq)) % qq
                dead = np.zeros(K.size, dtype=bool)
                for xx in self.xx:
                    dead |= (r + np.uint64(xx)) % qq == 0
                alive &= ~dead
            K, O = K[alive], O[alive]
            if K.size:
                yield sorted(int(k) * M + int(o)
                             for k, o in zip(K.tolist(), O.tolist()))

    def hunt(self, lo, hi, cap=100):
        """All (p, exact_run) with run >= n in [lo, hi), ascending."""
        out = []
        for chunk in self.survivors_pre_mr(lo, hi):
            for p in chunk:
                if all(mr_is_prime_u64(p + xx) for xx in self.xx):
                    out.append((p, mr_run_length(p, cap=cap)))
        return out


# ------------------------------- gates -------------------------------------

def g3_wheel_property(trials=4000, seed=1):
    """Wheel admissibility == 'no wheel prime divides any of the n values'."""
    rng = np.random.default_rng(seed)
    for wp in (WHEEL_PRIMES, WHEEL_PRIMES_29):
        for n in (9, 13, 17):
            offs_arr, m = build_wheel(n, wp)
            offs = set(offs_arr.tolist())
            for p in rng.integers(P_FLOOR, 10**7, trials).tolist():
                direct = all(all((p + x * x + x) % q for x in range(n))
                             for q in wp)
                if direct != ((p % m) in offs):
                    return False, f"G3 FAIL at n={n}, p={p}, wheel={wp[-1]}"
    return True, "G3 ok: wheel==direct divisibility, both wheels, n=9,13,17"


def g4_engine_vs_oracle():
    """Survivor (p, run) lists match the oracle exactly on windows."""
    from euler_reference import oracle_search
    for n, lo, hi in ((5, 100000, 400000), (6, 100000, 400000), (7, 100000, 1200000)):
        eng = CpuEngine(n).hunt(lo, hi)
        eng_ge = sorted(p for p, r in eng)
        ora = sorted(oracle_search(lo, hi, n, exact=False))
        if eng_ge != ora:
            return False, f"G4 FAIL n={n}: engine {len(eng_ge)} vs oracle {len(ora)}"
        for p, r in eng:
            if run_length(p) != r:
                return False, f"G4 FAIL n={n}: run({p}) engine={r}"
    return True, "G4 ok: engine survivor sets == oracle on 3 windows (n=5,6,7)"


def g5_rediscover(ns=(9, 11, 12)):
    """Engine re-finds a(n) as the FIRST run-exactly-n survivor above floor."""
    for n in ns:
        target = KNOWN[n]
        hits = CpuEngine(n).hunt(P_FLOOR, target + 1000)
        firsts = [p for p, r in hits if r == n]
        if not firsts or firsts[0] != target:
            return False, f"G5 FAIL n={n}: first={firsts[:1]}, expected {target}"
    return True, f"G5 ok: a(n) rediscovered for n={ns}"


def g9_128_overlap():
    """CPU-128 survivor stream == the PROVEN CPU-u64 stream, bit-for-bit,
    on populated windows across the u64 range (both engines can run
    there; the 128 path inherits the u64 path's evidence)."""
    cases = [(5, 10**5, 4 * 10**5, 20), (9, 10**6, 6 * 10**7, 2),
             (13, 10**5, 8_900_000_000, 1),
             (17, 10**15, 10**15 + 3 * 10**12, 1)]
    counts = []
    for n, lo, hi, min_surv in cases:
        u64 = np.concatenate(
            [a for a in CpuEngine(n, wheel_primes=WHEEL_PRIMES_29)
             .survivors_pre_mr(lo, hi)] or [np.array([], dtype=np.uint64)])
        u64_list = sorted(int(v) for v in u64.tolist())
        p128 = sorted(p for chunk in
                      CpuEngine128(n).survivors_pre_mr(lo, hi)
                      for p in chunk)
        if len(u64_list) < min_surv:
            return False, f"G9 FAIL n={n}: window under-populated ({len(u64_list)})"
        if u64_list != p128:
            return False, (f"G9 FAIL n={n} [{lo},{hi}): u64 {len(u64_list)}"
                           f" vs 128 {len(p128)}")
        counts.append(len(u64_list))
    return True, f"G9 ok: CPU-128 == CPU-u64 on 4 overlap windows, sizes {counts}"


def _direct_survivors(lo, hi, n):
    """Fourth implementation for mini-windows: wheel-admissible p tested
    by DIRECT big-int trial division over every prime in (29, Q2), pure
    Python, no numpy, no residue tricks.  Slow; tiny ranges only."""
    from sympy import primerange as _pr
    qs = [int(q) for q in _pr(30, Q2)]
    offs, M = build_wheel(n, WHEEL_PRIMES_29)
    out = []
    k0, k1 = lo // M, hi // M + 1
    for k in range(k0, k1):
        base = k * M
        for off in offs.tolist():
            p = base + int(off)
            if not (lo <= p < hi):
                continue
            alive = True
            for q in qs:
                if any((p + x * x + x) % q == 0 for x in range(n)):
                    alive = False
                    break
            if alive:
                out.append(p)
    return sorted(out)


def g10_128_above_cap():
    """Above the u64 cap the 128 path is pinned two independent ways:
    (a) mini-window parity against direct big-int trial division at
    2.35e20 and at the P128_CEIL zone; (b) end-to-end rediscovery of the
    Waldvogel-Leikauf run-21 literature value at 2.345e20."""
    for lo, span in ((235 * 10**18, 6 * 10**6),
                     (P128_CEIL - 6 * 10**6, 6 * 10**6)):
        hi = lo + span
        direct = _direct_survivors(lo, hi, 17)
        eng = sorted(p for chunk in
                     CpuEngine128(17).survivors_pre_mr(lo, hi)
                     for p in chunk)
        if direct != eng:
            return False, (f"G10 FAIL [{lo},{hi}): direct {len(direct)}"
                           f" vs engine {len(eng)}")
    lo, hi = A21_UPPER - 10**7, A21_UPPER + 10**7
    hits = CpuEngine128(17).hunt(lo, hi)
    good = [(p, r) for p, r in hits if p == A21_UPPER and r == 21]
    if not good:
        return False, f"G10 FAIL: A21 upper value not rediscovered ({hits})"
    return True, ("G10 ok: 128-path == direct trial division on 2 mini-windows"
                  " (2.35e20, ceil); Waldvogel-Leikauf run-21 value"
                  " rediscovered end-to-end above the u64 cap")


def selftest(fast=False):
    gates = [g3_wheel_property, g4_engine_vs_oracle, g5_rediscover,
             g9_128_overlap, g10_128_above_cap]
    ok = True
    for g in gates:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
