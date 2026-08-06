# score.py -- gates x throughput, repo convention (un-gameable; see
# ../huntlib/scoring.py for the contract):
# SCORE = Mp/s on a FROZEN benchmark shape, printed only if every gate is
# green AND the benchmark reproduces the frozen work fingerprint
# (survivor count + checksum) exactly.  Skipping work scores 0.
#
#   python score.py            # full battery + benchmark
#   python score.py --bench-only
#
# Frozen benchmark shape v1 (2026-08-05): n=17, 29# wheel, Barrett v3
# kernel, window [1e16, 1e16 + 5e14), periods_per_launch = 8192.
# FINGERPRINT frozen from the gated v2 engine (v3 must match bit-for-bit).
# Phase-2 shape (2026-08-06): same span via the 128 path at [2.3e20,
# +5e14) -- SCORE128, own fingerprint, frozen from the gated 128 engine.

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
    import cupy as cp
    from euler_gpu import GpuEngine
    e = GpuEngine(17)
    e.survivors_pre_mr(BENCH_LO, BENCH_LO + 10**12)     # warmup
    cp.cuda.Device().synchronize()
    rates, surv = [], None
    for _ in range(runs):
        t0 = time.time()
        s = e.survivors_pre_mr(BENCH_LO, BENCH_LO + BENCH_SPAN)
        cp.cuda.Device().synchronize()
        rates.append(BENCH_SPAN / (time.time() - t0))
        surv = s
    checksum = int(np.bitwise_xor.reduce(surv)) if surv.size else 0
    return float(np.median(rates)), int(surv.size), checksum


def benchmark128(runs=3):
    import cupy as cp
    from euler_gpu import GpuEngine128
    e = GpuEngine128(17)
    e.survivors_pre_mr(BENCH128_LO, BENCH128_LO + 10**12)   # warmup
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
