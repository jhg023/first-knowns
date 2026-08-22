"""score.py -- gates x fingerprinted benchmark for square-ladders.

Prints a SCORE only if every correctness gate is green AND all four frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count
+ xor checksum of the surviving k).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

Four shapes, because one configuration is not a benchmark:

  SCORE     n = 16, factored wheel (23, 37], sieve 65536, at k = 1e15
            -- the PRODUCTION configuration of the a(16) campaign.
  SCORE1L   the SAME k window and the same sieve, on the ONE-LEVEL wheel
            of primes to 23.  It is 3x slower and it must return the
            IDENTICAL fingerprint: the two kernels enumerate the same
            candidates by different arithmetic (a stored residue table
            versus a per-candidate CRT recombination), so a bug in the
            factored wheel's baked constants shows up here as a
            fingerprint mismatch inside the benchmark itself.
  SCORE10   n = 10, wheel 13, sieve 4096, at k = 2e9 -- a different
            filter, a 250x narrower wheel and a shallow sieve.  It has
            far more survivors per unit of line, so it weighs candidate
            throughput where SCORE weighs line throughput.
  SCORE16W  n = 16, one-level wheel 17, sieve 1024 -- the production
            filter on a coarse wheel, which is the knob whose optimum is
            most likely to move under an engine change (OPTIMIZATION.md:
            re-sweep tuning constants after any structural change).

A change that helps one and hurts another is visible instead of averaged
away.  The reported rate is END-TO-END k-line per second: blocks * W /
wall, the quantity the hunt is actually paid in, divided by 1e6 for the
SCORE.

Every k0 is an exact multiple of that shape's wheel modulus.  It has to be:
each engine floors k // W with its own W, so a shared cursor is a
different absolute window per wheel, and SCORE and SCORE1L would be
comparing fingerprints taken over different stretches of the line.  That
mistake produced a "disagreement" between two engines that were both
right, during the v2 A/B.

Frozen 2026-08-21 on the v2 engine (factored wheel).  A deliberate
coverage change -- a new wheel, a new sieve depth -- legitimately moves a
fingerprint: update it in the same commit and say why in
OPTIMIZATION_LOG.md.

Wall clock: about 40 s, of which the gates are half.
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import certificate                                 # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import sqladder_gpu                                             # noqa: E402
import sqladder_model                                           # noqa: E402
import sqladder_reference                                       # noqa: E402
import sqladder_search                                          # noqa: E402
from sqladder_gpu import GpuEngine                              # noqa: E402

# label, n, p1, p2, q2, j0, blocks, expected count, expected xor
SHAPES = [
    ("SCORE",    16, 23,   37, 65536,        134,      4,  303,
     999990048677220),
    ("SCORE1L",  16, 23, None, 65536,    4457242, 133052,  303,
     999990048677220),
    ("SCORE10",  10, 13, None,  4096,      66600, 200000, 2931,
     2555483804),
    ("SCORE16W", 16, 17, None,  1024, 1958825488,  60000,  581,
     999980563688462),
]


def main():
    gates = (sqladder_reference.GATES + sqladder_search.GATES
             + sqladder_gpu.GATES + sqladder_model.GATES + certificate.GATES)
    if not scoring.run_gates(gates):
        print("SCORE 0 (gates are not green)")
        return 1

    try:
        import cupy as cp
        sync = cp.cuda.Stream.null.synchronize
    except Exception:
        print("SCORE 0 (no GPU)")
        return 1

    ok_all = True
    for label, n, p1, p2, q2, j0, blocks, count, xor in SHAPES:
        eng = GpuEngine(n, p1=p1, p2=p2, q2=q2)
        eng.survivors_j(j0, j0 + blocks)                # warm on the window

        def work():
            return eng.survivors_j(j0, j0 + blocks)

        runs = 3 if blocks * eng.R > 10 ** 10 else 5
        rate_blocks, ok = scoring.fingerprint_benchmark(
            work, blocks, count, xor, runs=runs, sync=sync)
        if not ok:
            got = work()
            g = int(np.bitwise_xor.reduce(got)) if got.size else 0
            print(f"  ({label}: got count={got.size} xor={g})")
            ok_all = False
            continue
        rate_k = rate_blocks * eng.W
        wheel = f"({p1},{p2}]" if p2 else f"<={p1}"
        print(f"benchmark {label}: {rate_k:.3e} k/s over "
              f"[{j0 * eng.W:.4e}, +{blocks * eng.W:.4e}) "
              f"({rate_blocks * eng.R:.3e} candidates/s, wheel {wheel} "
              f"W={eng.W}, sieve {q2}, fingerprint {count}/{xor})")
        print(f"{label} {rate_k / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
