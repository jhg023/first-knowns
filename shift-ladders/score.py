"""score.py -- gates x fingerprinted benchmark for shift-ladders.

Prints a SCORE only if every correctness gate is green AND all five frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count
+ xor checksum of the surviving m).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

Five shapes, because one configuration is not a benchmark:

  SCORE     b = 4, n = 19, wheel to 23, sieve 65536 -- the PRODUCTION
            configuration of the A130003 campaign, and the row to read for
            campaign throughput.
  SCORE1L   the SAME WINDOW and the same sieve on the COARSE wheel (13).
            It sweeps 7,429 times as many periods to cover the identical
            line and it must return the IDENTICAL fingerprint: two
            different wheels enumerating the same candidates, so a bug in
            the CRT lift shows up here as a mismatch inside the benchmark
            itself rather than as a wrong answer months later.
  SCORE2    b = 2, n = 17, wheel to 37, sieve 65536 -- the PRODUCTION
            configuration of the A110096 campaign.  Its wheel is 3,000x
            sparser than base 4's, so its line rate is four orders of
            magnitude higher at the same candidate rate; both numbers are
            printed because only one of them is the thing being optimized.
  SCORE4W   the production filter on a coarse wheel and a shallow sieve --
            the knob whose optimum is most likely to move under an engine
            change (OPTIMIZATION.md: re-sweep tuning constants after any
            structural change).
  SCORE10   b = 4, n = 10, wheel 13, sieve 4096 -- a different filter with
            far more survivors per unit of line, so it weighs candidate
            throughput and the survivor path where the others weigh line.

A change that helps one and hurts another is visible instead of averaged
away.  The reported rate is END-TO-END m-line per second: blocks * W /
wall, the quantity the hunt is actually paid in, divided by 1e6.

Every j0 is a period index, so each window is exactly aligned to its own
wheel -- and SCORE1L's is deliberately the SAME ABSOLUTE WINDOW as
SCORE's, which is only possible because W(23) = W(13) * 7429.  Getting
that wrong produces two engines that are both right and appear to
disagree; it happened in another project in this repo during an A/B.

Frozen 2026-08-23 on the v1 engine (flat wheel table, one Barrett test
loop).  A deliberate coverage change -- a new wheel, a new sieve depth --
legitimately moves a fingerprint: update it in the same commit and say why
in OPTIMIZATION_LOG.md.

Wall clock: about 40 s, of which the gates are half.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import certificate                                 # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import shiftladder_gpu                                          # noqa: E402
import shiftladder_model                                        # noqa: E402
import shiftladder_reference                                    # noqa: E402
import shiftladder_search                                       # noqa: E402
from shiftladder_gpu import GpuEngine                           # noqa: E402

# label, b, n, p1, q2, j0, blocks, expected count, expected xor
SHAPES = [
    ("SCORE",    4, 19, 23, 65536,      4482439,       8192,  7,
     998631924604311),
    ("SCORE1L",  4, 19, 13, 65536,  33300039331,   60858368,  7,
     998631924604311),
    ("SCORE2",   2, 17, 37, 65536,          135,       2048, 59,
     17289912876387275),
    ("SCORE4W",  4, 19, 13,  1024,  33300033301,   10000000, 5014,
     694483282552),
    ("SCORE10",  4, 10, 13,  4096,  33300033301,    2000000, 58213,
     999951251185409),
]


def main():
    gates = (shiftladder_reference.GATES + shiftladder_search.GATES
             + shiftladder_gpu.GATES + shiftladder_model.GATES
             + certificate.GATES)
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
    for label, b, n, p1, q2, j0, blocks, count, xor in SHAPES:
        eng = GpuEngine(n, b, p1=p1, q2=q2)
        line = blocks * eng.W

        def work(_e=eng, _j=j0, _n=blocks):
            return _e.survivors_j(_j, _j + _n)

        work()                                          # warm on the window
        runs = 3 if blocks * eng.R > 10 ** 9 else 5
        rate_blocks, ok = scoring.fingerprint_benchmark(
            work, blocks, count, xor, runs=runs, sync=sync)
        if not ok:
            got = work()
            g = 0
            for v in got:
                g ^= int(v)
            print(f"  ({label}: got count={len(got)} xor={g})")
            ok_all = False
            continue
        rate_m = rate_blocks * eng.W
        print(f"benchmark {label}: {rate_m:.3e} m/s over "
              f"[{j0 * eng.W:.4e}, +{line:.4e}) "
              f"({rate_blocks * eng.R:.3e} candidates/s, base {b}, filter "
              f"n={n}, wheel <={p1} W={eng.W}, sieve {q2}, "
              f"fingerprint {count}/{xor})")
        print(f"{label} {rate_m / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
