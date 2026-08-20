"""score.py -- gates x fingerprinted benchmark.  The un-gameable number.

Prints

    SCORE <end-to-end Mp/s on a frozen workload>

and prints it ONLY if every correctness gate is green AND the benchmark
reproduces a frozen WORK FINGERPRINT: the exact survivor count and their
xor checksum on a pinned window.  An engine that skips work fails the
fingerprint and scores 0; an engine that breaks correctness fails the gates
and scores 0.  Optimize under the score, never around it.

The benchmark shape is FROZEN at the engine's default sieve depth (2^16),
deliberately NOT at the campaign's (2048).  The campaign depth is a
configuration decision that has already moved once and will move again as
the engine changes; the score has to keep meaning the same thing across
those moves, so it is pinned to a shape and left there.  A deliberate
coverage change legitimately changes the fingerprint: update it in the same
commit, with an OPTIMIZATION_LOG.md entry explaining why.

Wall clock: about 40 seconds, of which the gates are most of it.
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import certificate as _cert                        # noqa: E402
from huntlib import frontier as _front                          # noqa: E402
from huntlib import rungs as _rungs                             # noqa: E402
from huntlib import scoring, shutdown as _shutdown              # noqa: E402
import ap_gpu                                                   # noqa: E402
import ap_model                                                 # noqa: E402
import ap_reference as ref                                      # noqa: E402
import ap_search                                                # noqa: E402
from ap_reference import W0                                     # noqa: E402
from ap_search import Q2_DEFAULT                                 # noqa: E402

# ------------------------------ frozen shape --------------------------------
BENCH_N = 16
BENCH_Q2 = Q2_DEFAULT                  # 2^16 -- the engine default, frozen
BENCH_BASE = (4 * 10**13 // W0) * W0   # the production height for a(16)
BENCH_LAUNCH_U = 1 << 25
BENCH_SPAN = W0 * BENCH_LAUNCH_U * 16  # ~1.6e10 of p-line, ~3 s

# The frozen fingerprint: reproduced by every engine that does the work.
FP_COUNT = 192
FP_CHECKSUM = 4046714554

GATES = (ref.GATES + ap_model.GATES + ap_search.GATES + ap_gpu.GATES
         + _cert.GATES + _rungs.GATES + _front.GATES)


def _work():
    eng = ap_gpu.GpuEngine(BENCH_N, BENCH_Q2, launch_u=BENCH_LAUNCH_U)
    parts = [c for c in eng.survivors(BENCH_BASE, BENCH_SPAN)]
    return (np.concatenate(parts) if parts
            else np.zeros(0, dtype=np.uint64))


def main():
    ok = scoring.run_gates(GATES)
    if not ok:
        print("SCORE 0 (gates are not green)")
        return 1
    import cupy as cp

    def sync():
        cp.cuda.Stream.null.synchronize()

    _work()                                    # warm: compile, allocate
    rate, fp_ok = scoring.fingerprint_benchmark(
        _work, BENCH_SPAN, FP_COUNT, FP_CHECKSUM, runs=3, sync=sync)
    if not fp_ok:
        return 1
    scoring.emit_score(rate, unit=1e6)
    print(f"  (Mp/s of p-line, n = {BENCH_N}, sieve depth {BENCH_Q2}, "
          f"{BENCH_SPAN:.3e} of line from p = {BENCH_BASE:.3e}, "
          f"fingerprint {FP_COUNT}/{FP_CHECKSUM})")
    return 0


if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main) or 0)
