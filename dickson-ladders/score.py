"""score.py -- gates x fingerprinted benchmark for dickson-ladders.

Prints a SCORE only if every correctness gate is green AND both frozen
benchmark shapes reproduce their work fingerprints exactly (survivor
count + xor checksum of the surviving j).  An engine that skips work
fails the fingerprint; an engine that breaks the mathematics fails the
gates.  Either way it scores nothing.  Optimize under the score, never
around it.

Three shapes, because one configuration is not a benchmark:

  SCORE    n = 10 filter, wheel 2310,  j in [1e12, +2^32)
  SCORE12  n = 12 filter, wheel 30030, j in [6e11, +2^32)
  SCORE13  n = 13 filter, wheel 30030, j in [7e16, +2^38)

The first two disagree about what matters -- the n=12 shape has 4x fewer
survivors per candidate and 13x more k-line per candidate -- so a change
that helps one and hurts the other is visible instead of averaged away.
The third is the production configuration for the a(13) campaign, sited
at the model's a(13) median (k ~ 2.1e21), and 64x wider: the v2 engine
crosses a 2^32 window in ~5 ms, which is one to four launches and near
the floor of what that window can resolve, so LAUNCH-sized changes are
judged on SCORE13 (BENCHMARKS.md).  The frozen 2^32 shapes are never
amended; a shape that stops resolving a change gets a sibling.

The rate reported is END-TO-END k-line per second: span * W / wall, the
quantity the hunt is actually paid in.  Divided by 1e6 for the SCORE.

SCORE/SCORE12 frozen 2026-08-18 on the v1 kernel; SCORE13 frozen the same
day on v2 and cross-checked bit-for-bit against v1 (56 s at v1 speed).
A deliberate coverage change (new wheel, new sieve depth) legitimately
moves a fingerprint: update it in the same commit and say why in
OPTIMIZATION_LOG.md.
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown  # noqa: E402
from huntlib import scoring                                   # noqa: E402
import ladder_gpu                                             # noqa: E402
import ladder_reference                                       # noqa: E402
import ladder_search                                          # noqa: E402
from ladder_gpu import GpuEngine                              # noqa: E402

# The sieve DEPTH is part of a frozen shape, not a default to inherit.
# The campaign runs deeper than the benchmark (launch.py Q2_CAMPAIGN) because
# depth trades device time for host time, and that trade is a campaign
# decision; the benchmark's job is to stay comparable across engine
# generations, so it pins its own.
SHAPES = [
    # label, n, q2, j0, span, expected count, expected xor
    ("SCORE",   10, 65536, 10**12,      1 << 32, 1213, 1003170806905),
    ("SCORE12", 12, 65536, 6 * 10**11,  1 << 32,  292, 2752794123),
    ("SCORE13", 13, 65536, 7 * 10**16,  1 << 38, 2739, 70000110051605722),
]


def main():
    gates = (ladder_reference.GATES + ladder_search.GATES + ladder_gpu.GATES)
    if not scoring.run_gates(gates):
        print("SCORE 0 (gates failed)")
        return 1

    try:
        import cupy as cp
        sync = cp.cuda.Stream.null.synchronize
    except Exception:
        print("SCORE 0 (no GPU)")
        return 1

    ok_all = True
    for label, n, q2, j0, span, count, xor in SHAPES:
        eng = GpuEngine(n, q2=q2)
        eng.survivors_j(j0, j0 + span)                    # warm on the window

        def work():
            return eng.survivors_j(j0, j0 + span)

        rate_j, ok = scoring.fingerprint_benchmark(
            work, span, count, xor, runs=3, sync=sync)
        if not ok:
            got = work()
            print(f"  ({label}: got count={got.size} xor="
                  f"{int(np.bitwise_xor.reduce(got)) if got.size else 0})")
            ok_all = False
            continue
        rate_k = rate_j * eng.W
        print(f"benchmark {label}: {rate_k:.3e} k/s over "
              f"[{j0*eng.W:.3e}, +{span*eng.W:.3e}) "
              f"({rate_j:.3e} candidates/s, wheel {eng.W})")
        print(f"{label} {rate_k/1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
