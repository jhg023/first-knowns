# score.py -- gates x throughput, repo convention (un-gameable; see
# ../huntlib/scoring.py for the contract):
# SCORE = Mp/s on a FROZEN benchmark shape, printed only if every gate is
# green AND the benchmark reproduces the frozen work fingerprint
# (survivor count + checksum) exactly.  Skipping work scores 0.
#
#   python score.py            # full battery + all three benchmarks
#   python score.py --bench-only
#   python score.py --freeze   # gates, then print every fingerprint
#
# THREE frozen shapes, all n=17, all measured with the ONE production engine:
#   SCORE       [1e16,   +5e14)  fingerprint frozen 2026-08-05
#   SCORE128    [2.3e20, +5e14)  fingerprint frozen 2026-08-06
#   SCORE_WIDE  [6.11e20, +2e16) fingerprint frozen 2026-08-16
# The first two share a 5e14 span four orders of magnitude apart, so that pair
# is also a height-flatness check.  Their fingerprints predate the current
# engine (they were frozen from the u64-only kernel and the first 128 path,
# both since retired) and both still have to reproduce bit-for-bit -- that is
# what makes the score un-gameable across engine generations.  They are the
# CROSS-GENERATION ANCHOR and are never amended; a shape that stops resolving
# a change gets a sibling, not an edit.
#
# Shape amendment (2026-08-15): the benchmarks take the engine's default
# launch size, raised 8192 -> 131072 periods, so a 77,285-period window is
# now ONE launch and the scores no longer include multi-launch overhead. The
# WORK is unchanged. Cross-generation comparisons quote the paired ratio
# measured in a single battery, per BENCHMARKS.md.
#
# Third shape added (2026-08-16), because the 5e14 shape had stopped being
# able to resolve the one lever left in the sieve.  A frozen window is
# expressed in absolute units while the engine's work unit -- the wheel period
# -- grows underneath it.  5e14 held 77,285 periods when it was frozen (period
# 6.47e9); on the 31# wheel it holds 2,494; on the next wheel up it would hold
# 68, which is two pattern words per thread against 20x as many threads, so
# the same change that is worth 1.85x in production measures 0.58x there
# (../OPTIMIZATION.md 2.13).  A benchmark that inverts the sign of a real
# change is no longer neutral about which answer gets picked.
#
# So SCORE_WIDE: [6.11e20, +2e16), 6,996 survivors.  It is 24 launches at the
# current PPL, so no single-launch flattery (Rule 4); it is the window the
# Phase-5 A/B sweeps already ran on, so it is heavily exercised; and it holds
# ~2,696 periods of the 37# wheel, which is enough to resolve it.  The two
# older shapes keep their exact bytes and still have to reproduce -- this is
# purely additive, and all three are checked on every run.

import argparse
import sys
import time

import numpy as np

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                     # noqa: E402

BENCH_LO = 10**16
BENCH_SPAN = 5 * 10**14
FINGERPRINT_COUNT = 178
FINGERPRINT_CHECKSUM = 120489734542316   # frozen 2026-08-05, v3 kernel, gated

# Phase-2 (128-bit path) benchmark shape: same span, above the u64 cap
# in the zone the a(19) hunt sweeps.  Fingerprint frozen from the first
# fully gated run of the 128 engine (2026-08-06).
BENCH128_LO = 230 * 10**18               # 2.3e20
BENCH128_SPAN = 5 * 10**14
FINGERPRINT128_COUNT = 178               # frozen 2026-08-06, gated 128 path
FINGERPRINT128_CHECKSUM = 133625321009290

# The WIDE shape (2026-08-16).  40x the span of the other two, in the zone the
# a(19) hunt is sweeping, sized so that it holds a few thousand periods of a
# wheel wider than the one in the tree -- see the header for why that matters.
# Frozen from the same battery that added it, on a green tree.
BENCH_WIDE_LO = 611 * 10**18             # 6.11e20
BENCH_WIDE_SPAN = 2 * 10**16
FINGERPRINT_WIDE_COUNT = 6996            # frozen 2026-08-16, 13 gates green
FINGERPRINT_WIDE_CHECKSUM = 71330844491704598


def _bench(lo, span, runs):
    """Median end-to-end rate over `runs` sweeps of [lo, lo+span), plus the
    work fingerprint (survivor count + xor checksum of the exact ints).

    One body for all three shapes: they differ only in the window, and a
    benchmark whose three shapes could drift apart in how they time is a
    benchmark that can be gamed on one of them.
    """
    import cupy as cp
    from euler_gpu import GpuEngine
    e = GpuEngine(17)
    # Warm up on the MEASURED window.  The engine sizes its queues on first
    # use, and letting a multi-GB allocation land inside the timed region
    # penalises whichever shape runs first while the later ones find the
    # blocks already pooled -- that defect cost a 63% phantom height effect
    # once already (see BENCHMARKS.md).
    e.survivors_pre_mr(lo, lo + span)
    cp.cuda.Device().synchronize()
    rates, surv = [], None
    for _ in range(runs):
        t0 = time.time()
        s = e.survivors_pre_mr(lo, lo + span)
        cp.cuda.Device().synchronize()
        rates.append(span / (time.time() - t0))
        surv = s
    checksum = 0
    for p in surv:                       # exact Python ints
        checksum ^= p
    return float(np.median(rates)), len(surv), checksum


def benchmark(runs=3):
    """The LOW frozen shape, now run by the production engine.

    This window used to belong to the u64-only kernel.  One engine spans
    the range, so it is measured here too -- and because both shapes are the
    same span swept by the same engine, SCORE vs SCORE128 doubles as a
    height-flatness check across four orders of magnitude.  The frozen
    fingerprint is unchanged and still has to reproduce -- it was frozen from
    the u64-only kernel that has since been retired, so this window is also
    the standing check that the current engine still agrees with it.
    """
    return _bench(BENCH_LO, BENCH_SPAN, runs)


def benchmark128(runs=3):
    """The HIGH frozen shape: same span, above the old u64 cap, in the zone
    the a(19) hunt sweeps."""
    return _bench(BENCH128_LO, BENCH128_SPAN, runs)


def benchmark_wide(runs=3):
    """The WIDE frozen shape: 2e16 at 6.11e20, 24 launches at the current PPL.

    The other two are 5e14 windows frozen against wheel periods four and two
    wheels ago; this one is wide enough to still hold thousands of periods
    when the period grows.  It resolves what they no longer can, and it is the
    shape a wheel change is judged on.  It does NOT replace them: all three
    are checked on every run, and the older pair remains the anchor that ties
    today's engine to the retired ones.
    """
    return _bench(BENCH_WIDE_LO, BENCH_WIDE_SPAN, runs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench-only", action="store_true")
    ap.add_argument("--freeze", action="store_true",
                    help="print fingerprint values for freezing")
    args = ap.parse_args()

    ok = True
    if not args.bench_only:
        import euler_reference, euler_search, euler_gpu
        ok = euler_reference.selftest() and ok
        ok = euler_search.selftest() and ok
        ok = euler_gpu.selftest() and ok
        if not ok:
            print("SCORE 0 (gates failed)")
            sys.exit(1)

    rate, count, checksum = benchmark()
    rate128, count128, checksum128 = benchmark128()
    ratew, countw, checksumw = benchmark_wide()
    if args.freeze:
        print(f"FINGERPRINT_COUNT = {count}")
        print(f"FINGERPRINT_CHECKSUM = {checksum}")
        print(f"FINGERPRINT128_COUNT = {count128}")
        print(f"FINGERPRINT128_CHECKSUM = {checksum128}")
        print(f"FINGERPRINT_WIDE_COUNT = {countw}")
        print(f"FINGERPRINT_WIDE_CHECKSUM = {checksumw}")
        return
    fp_ok = (count == FINGERPRINT_COUNT and
             (FINGERPRINT_CHECKSUM is None or checksum == FINGERPRINT_CHECKSUM))
    if not fp_ok:
        print(f"SCORE 0 (fingerprint mismatch: count={count}, checksum={checksum})")
        sys.exit(1)
    fp128_ok = (FINGERPRINT128_COUNT is None or
                (count128 == FINGERPRINT128_COUNT and
                 checksum128 == FINGERPRINT128_CHECKSUM))
    if not fp128_ok:
        print(f"SCORE 0 (128 fingerprint mismatch: count={count128}, "
              f"checksum={checksum128})")
        sys.exit(1)
    fpw_ok = (FINGERPRINT_WIDE_COUNT is None or
              (countw == FINGERPRINT_WIDE_COUNT and
               checksumw == FINGERPRINT_WIDE_CHECKSUM))
    if not fpw_ok:
        print(f"SCORE 0 (wide fingerprint mismatch: count={countw}, "
              f"checksum={checksumw})")
        sys.exit(1)
    print(f"benchmark: {rate:.3e} p/s over [{BENCH_LO:.0e}, +{BENCH_SPAN:.0e})")
    print(f"SCORE {rate/1e6:,.0f}")
    print(f"benchmark128: {rate128:.3e} p/s over "
          f"[{BENCH128_LO:.0e}, +{BENCH128_SPAN:.0e})")
    print(f"SCORE128 {rate128/1e6:,.0f}")
    print(f"benchmark_wide: {ratew:.3e} p/s over "
          f"[{BENCH_WIDE_LO:.3e}, +{BENCH_WIDE_SPAN:.0e})")
    print(f"SCORE_WIDE {ratew/1e6:,.0f}")


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main) or 0)
