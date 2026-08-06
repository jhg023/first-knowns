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
# ASCII only.

import numpy as np
from sympy import primerange

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib.primes import MR_BASES, mr_is_prime as mr_is_prime_u64  # noqa: E402

from euler_reference import KNOWN, run_length

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


def selftest(fast=False):
    gates = [g3_wheel_property, g4_engine_vs_oracle, g5_rediscover]
    ok = True
    for g in gates:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
