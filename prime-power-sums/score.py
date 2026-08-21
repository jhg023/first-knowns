"""score.py -- gates x fingerprinted benchmark.  The un-gameable number.

Prints

    SCORE <end-to-end Mp/s of prime line on a frozen workload>

and prints it ONLY if every correctness gate is green AND the benchmark
reproduces a frozen WORK FINGERPRINT: the exact hit count and their xor
checksum on a pinned window.  An engine that skips work fails the
fingerprint and scores 0; an engine that breaks correctness fails the
gates and scores 0.  Optimize under the score, never around it.

THE FROZEN SHAPE is a sweep from p = 2 -- the whole line, from scratch,
with all eight families live.  That is deliberately NOT the campaign's
shape (which starts wherever the checkpoint left it, at p ~ 1e15 where
there are a thousand times more sieving primes and the index wheel skips
far more).  The score has to keep meaning the same thing while the
campaign's configuration moves, so it is pinned to a shape and left there;
the production rate is measured separately and reported in BENCHMARKS.md,
because THAT is the number the campaign is priced on (CLAUDE.md rule 5c).

A from-scratch window is also the only shape whose fingerprint is a
statement about the mathematics rather than about an arbitrary seed: every
hit in it is a real term of a real sequence, and 147 of them are published
values this project did not find.

Wall clock: about 40 seconds, of which the gates are most of it.
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import scoring, shutdown as _shutdown                  # noqa: E402
import psum_gpu                                                     # noqa: E402
import psum_gpu2                                                    # noqa: E402
import psum_model                                                   # noqa: E402
import psum_reference as ref                                        # noqa: E402
import psum_search as cpu                                           # noqa: E402

# ------------------------------ frozen shape --------------------------------
BENCH_SPAN = 1 << 26                   # 6.7e7 of prime line, from p = 2
BENCH_SEG = 1 << 26
BENCH_CHUNK = 1 << 16                  # v1's shape, kept for the record
BENCH_RUN = psum_gpu2.RUN_DEFAULT
BENCH_FAMILIES = ref.ALL_FAMILIES

# The frozen fingerprint: reproduced by every engine that does the work.
FP_COUNT = 147
FP_CHECKSUM = 5908722711111303797

GATES = (ref.GATES + cpu.GATES + psum_gpu.GATES + psum_gpu2.GATES
         + psum_model.GATES)


def _encode(hits):
    """(m, e, k) -> one uint64.  k < 2^57 by K_CEIL, so m and e fit above."""
    return np.array(sorted((m << 58) | (e << 57) | k for m, e, k in hits),
                    dtype=np.uint64)


_ENG = []


def _work():
    # The engine is built once and reused: v2 compiles its kernels for the
    # run's limb widths, and rebuilding them per timing round would measure
    # NVRTC rather than the sweep.  The frozen shape is unchanged.
    if not _ENG:
        _ENG.append(psum_gpu2.GpuSweep2(BENCH_FAMILIES, seg=BENCH_SEG,
                                        run=BENCH_RUN))
    ms = sorted({m for m, _ in BENCH_FAMILIES})
    hits, _ = _ENG[0].run(BENCH_SPAN, state=cpu.State(ms))
    return _encode(hits)


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
    print(f"  (Mp/s of prime line, from p = 2 to {BENCH_SPAN:.3e}, "
          f"{len(BENCH_FAMILIES)} families, seg {BENCH_SEG}, run "
          f"{BENCH_RUN}, fingerprint {FP_COUNT}/{FP_CHECKSUM})")
    return 0


if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main) or 0)
