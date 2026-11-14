# score.py -- gates x throughput for A331940 (un-gameable; the contract is
# ../huntlib/scoring.py):
#
#   SCORE = k per second (in units of 10^3 k/s) on a FROZEN benchmark shape,
#   printed only if every gate is green AND the run reproduces the frozen
#   work fingerprint exactly.  Skipping work scores 0.
#
#   python score.py              full battery + the five benchmarks
#   python score.py --bench-only
#   python score.py --freeze     gates, then print every fingerprint
#
# FIVE frozen shapes, one production engine (hlc_gpu.GpuEngine, defaults:
# the class-group prefilter, the sparse exact count, the survivor rule):
#
#   SCORE        [3*10^12 + 1, + 2^23 of k)   ONE window at the height the
#                model says runs for days at engine v3's rate, from the
#                campaign's cursor (k = 1.26*10^10, a(30) found): a(36)'s
#                median is k = 2.0*10^12, 31 hours in, and a(37)'s 5.4*10^12,
#                five days.  This is the headline, and the shape optimization
#                rounds are measured on.
#   SCORE_1E12   [10^12 + 1, + 2^23 of k)     the headline of engine v2 (the
#                day-long height at v2's rate; twelve hours in at v3's), kept
#                so that the ledger compares engines on one shape.
#   SCORE_3E11   [3*10^11 + 1, + 2^23 of k)   the round-0 headline shape.
#   SCORE_OPEN   [10^8 + 1, + 4 * 2^23 of k)  four windows in the opening
#                band (above Fung & Williams' k = 99539591, which bounds
#                a(12), so no open term can sit in a benchmark window).
#   SCORE_1E14   [10^14 + 1, + 2^23 of k)     past engine v3's ceiling
#                (engine v4): wide form keys, characters on the fly and
#                three primes past 251 in the rule are all in force, so the
#                paths v4 added are pinned by a fingerprint.  Its
#                expectation: the production stream and every finished
#                count equal the rule on the three-squares tabulation of
#                EVERY counter of the window (174 s of walk, 2026-11-12).
#
# The fingerprint of a shape is, per window, every survivor of the rule at
# the census floor as k * 2^32 + T (T = 3H(4k - 1), the exact count), TWO
# digests of the counts the sparse count finished (their sum, and their sum
# weighted by position), their NUMBER, and the number and position sum of
# the n the prefilter left -- so a wrong count or a changed prefilter
# decision anywhere in the window moves the checksum, survivor or not.  The
# survivor part is the stream of the rule with the local Euler factors
# (engine v3): engine v1's list, which v2 reproduced, less the k that rule
# proves to have C below the floor (BENCHMARKS.md has the comparison).  The
# expectation was established independently of the engine being scored as
# far as that is possible at these heights: the CPU engine (reduced
# forms) equals the GPU engine (three squares) counter for counter on six
# populated windows up to k = 4*10^9 and its survivors equal the
# production stream there (gate P1); the prefilter's decisions equal the
# CPU reference's bit for bit to 9*10^13 and at 10^18 (P5, P8); the
# production stream equals the survivor rule on every counter at 10^8,
# 3*10^11, 10^12, 10^13 and 9*10^13 (P6); the sparse count equals the
# three-squares count on every counter of eight windows to 6*10^13 (P7)
# and 3 h(-d) S(f) on constructed n at 10^15 and 10^16 (P8); every k the
# local rule removes has C below the floor by the host's rigorous interval
# (S9); above 4*10^9 a forms sieve costs O(k) per window, so the counts
# themselves rest on the split-invariance gate (P2), on sampled analytic
# class numbers inside 10^10..10^14 (P3) and on the literature canaries at
# 1.8*10^10 and 2.1*10^10 (P4).  BENCHMARKS.md records the freezes.
#
# Benchmark windows are counted and filtered, never classified: no C is
# computed for a k above 3*10^6 here.

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from huntlib import scoring, shutdown                         # noqa: E402

FLOOR = 7.5
# (name, k_lo, windows, count, checksum): frozen 2026-11-11, engine v3 (and
# reproduced unchanged by engine v4); SCORE_1E14 frozen 2026-11-12, v4
SHAPES = [
    ("SCORE", 3 * 10**12 + 1, 1, 96, 12884934779942494085505),
    ("SCORE_1E12", 10**12 + 1, 1, 98, 4294978698595606490122),
    ("SCORE_3E11", 3 * 10**11 + 1, 1, 98, 1288500965751632109998),
    ("SCORE_OPEN", 10**8 + 1, 4, 406, 221705018271837759),
    ("SCORE_1E14", 10**14 + 1, 1, 116, 429496743674342754768367),
]


def _bench(k_lo, windows, count, checksum, runs):
    import cupy as cp
    import hlc_gpu
    e = hlc_gpu.GpuEngine()
    sync = cp.cuda.Device().synchronize
    hlc_gpu.fingerprint(e, k_lo, 1, FLOOR)             # warm: compile, pool
    sync()
    span = 2 * e.W * windows
    if count is None:                                   # --freeze
        fp = hlc_gpu.fingerprint(e, k_lo, windows, FLOOR)
        x = 0
        for v in fp:
            x ^= v
        return 0.0, len(fp), x, True
    rate, ok = scoring.fingerprint_benchmark(
        lambda: hlc_gpu.fingerprint(e, k_lo, windows, FLOOR), span,
        count, checksum, runs=runs, sync=sync)
    return rate, count, checksum, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench-only", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    args = ap.parse_args()
    if not args.bench_only:
        import hlc_reference
        import hlc_search
        import hlc_gpu
        import hlc_model
        ok = hlc_reference.selftest()
        ok = hlc_search.selftest() and ok
        ok = hlc_gpu.selftest() and ok
        ok = scoring.run_gates(hlc_model.GATES) and ok
        if not ok:
            print("SCORE 0 (gates failed)")
            return 1
    if args.freeze:
        for name, k_lo, w, _c, _x in SHAPES:
            _, c, x, _ = _bench(k_lo, w, None, None, 1)
            print(f'    ("{name}", {k_lo}, {w}, {c}, {x}),')
        return 0
    if any(c is None for _n, _k, _w, c, _x in SHAPES):
        print("SCORE 0 (no frozen fingerprint: run --freeze on a green tree)")
        return 1
    rates = []
    for name, k_lo, w, c, x in SHAPES:
        rate, _, _, ok = _bench(k_lo, w, c, x, 3)
        if not ok:
            return 1
        rates.append((name, k_lo, w, rate))
    for name, k_lo, w, rate in rates:
        span = "+ 2^23" if w == 1 else f"+ {w} * 2^23"
        print(f"benchmark {name}: {rate:.4g} k/s over [{k_lo - 1:.0e} + 1, "
              f"{span})")
        if name == "SCORE":
            scoring.emit_score(rate, unit=1e3)
        else:
            print(f"{name} {rate / 1e3:,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
