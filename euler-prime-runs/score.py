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
    if args.freeze:
        print(f"FINGERPRINT_COUNT = {count}")
        print(f"FINGERPRINT_CHECKSUM = {checksum}")
        return
    fp_ok = (count == FINGERPRINT_COUNT and
             (FINGERPRINT_CHECKSUM is None or checksum == FINGERPRINT_CHECKSUM))
    if not fp_ok:
        print(f"SCORE 0 (fingerprint mismatch: count={count}, checksum={checksum})")
        sys.exit(1)
    print(f"benchmark: {rate:.3e} p/s over [{BENCH_LO:.0e}, +{BENCH_SPAN:.0e})")
    print(f"SCORE {rate/1e6:,.0f}")


if __name__ == "__main__":
    main()
