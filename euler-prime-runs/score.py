# score.py -- gates x throughput, repo convention (un-gameable; see
# ../huntlib/scoring.py for the contract):
# SCORE = Mp/s on a FROZEN benchmark shape, printed only if every gate is
# green AND the benchmark reproduces the frozen work fingerprint
# (survivor count + checksum) exactly.  Skipping work scores 0.
#
#   python score.py            # full battery + benchmark
#   python score.py --bench-only
#
# TWO frozen shapes, both n=17 on the 29# wheel, both a 5e14 span, measured
# with the ONE production engine:
#   SCORE     [1e16, +5e14)    fingerprint frozen 2026-08-05
#   SCORE128  [2.3e20, +5e14)  fingerprint frozen 2026-08-06
# Same span four orders of magnitude apart, so the pair is also a
# height-flatness check.  Both fingerprints predate the current engine (they
# were frozen from the u64-only kernel and the first 128 path, both since
# retired) and both still have to reproduce bit-for-bit -- that is what makes
# the score un-gameable across engine generations.
#
# Shape amendment (2026-08-15): the benchmarks take the engine's default
# launch size, raised 8192 -> 131072 periods, so a 77,285-period window is
# now ONE launch and the scores no longer include multi-launch overhead. The
# WORK is unchanged. Cross-generation comparisons quote the paired ratio
# measured in a single battery, per BENCHMARKS.md.

import argparse
import sys
import time

import numpy as np

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))

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
    import cupy as cp
    from euler_gpu import GpuEngine
    e = GpuEngine(17)
    e.survivors_pre_mr(BENCH_LO, BENCH_LO + BENCH_SPAN)   # warmup on the
    #                                                    # MEASURED window:
    # the engine sizes its queues on first use, and letting a multi-GB
    # allocation land inside the timed region penalises whichever
    # benchmark runs first (the second finds the blocks pooled).
    cp.cuda.Device().synchronize()
    rates, surv = [], None
    for _ in range(runs):
        t0 = time.time()
        s = e.survivors_pre_mr(BENCH_LO, BENCH_LO + BENCH_SPAN)
        cp.cuda.Device().synchronize()
        rates.append(BENCH_SPAN / (time.time() - t0))
        surv = s
    checksum = 0
    for p in surv:
        checksum ^= p
    return float(np.median(rates)), len(surv), checksum


def benchmark128(runs=3):
    import cupy as cp
    from euler_gpu import GpuEngine
    e = GpuEngine(17)
    e.survivors_pre_mr(BENCH128_LO, BENCH128_LO + BENCH128_SPAN)  # ditto
    cp.cuda.Device().synchronize()
    rates, surv = [], None
    for _ in range(runs):
        t0 = time.time()
        s = e.survivors_pre_mr(BENCH128_LO, BENCH128_LO + BENCH128_SPAN)
        cp.cuda.Device().synchronize()
        rates.append(BENCH128_SPAN / (time.time() - t0))
        surv = s
    checksum = 0
    for p in surv:                       # exact Python ints
        checksum ^= p
    return float(np.median(rates)), len(surv), checksum


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
    if args.freeze:
        print(f"FINGERPRINT_COUNT = {count}")
        print(f"FINGERPRINT_CHECKSUM = {checksum}")
        print(f"FINGERPRINT128_COUNT = {count128}")
        print(f"FINGERPRINT128_CHECKSUM = {checksum128}")
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
    print(f"benchmark: {rate:.3e} p/s over [{BENCH_LO:.0e}, +{BENCH_SPAN:.0e})")
    print(f"SCORE {rate/1e6:,.0f}")
    print(f"benchmark128: {rate128:.3e} p/s over "
          f"[{BENCH128_LO:.0e}, +{BENCH128_SPAN:.0e})")
    print(f"SCORE128 {rate128/1e6:,.0f}")


if __name__ == "__main__":
    main()
