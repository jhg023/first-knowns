"""score.py -- gates x fingerprinted benchmark for shift-ladders.

Prints a SCORE only if every correctness gate is green AND all five frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count
+ xor checksum of the surviving m).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

Five shapes, because one configuration is not a benchmark:

  SCORE     b = 4, n = 19, flat wheel to 29, sieve 65536 -- the PRODUCTION
            configuration of the A130003 campaign, and the row to read for
            campaign throughput.  Its window is FOUR launches wide, which
            is deliberate: a window narrower than a launch cannot exercise
            anything the engine sizes from per_launch, and this benchmark
            was blind to exactly that once already (see OPTIMIZATION_LOG).
  SCORE1L   the SAME WINDOW and the same sieve on the COARSE wheel (13).
            It sweeps 215,441 times as many periods to cover the identical
            line and it must return the IDENTICAL fingerprint: two
            different wheels enumerating the same candidates, so a bug in
            the CRT lift or in a bit plane shows up here as a mismatch
            inside the benchmark itself rather than as a wrong answer
            months later.
  SCORE2    b = 2, n = 19, wheel to 41, sieve 65536 -- the PRODUCTION
            configuration of the A110096 campaign.  Its wheel is 16,000x
            sparser than base 4's, so its line rate is four orders of
            magnitude higher at the same candidate rate; both numbers are
            printed because only one of them is the thing being optimized.
            Its FILTER moved with its wheel: w(41,n,2) = min(n, 20), so at
            n = 17 the p1 = 41 flat table would hold 129 million residues
            and RES_MAX refuses it -- while at the n = 19 the campaign now
            runs it holds 44.5 million.  A shape pinned to a filter the
            hunt has already passed would have had to keep p1 = 37, and a
            benchmark that stops describing the configuration the campaign
            runs is the one option this project does not take.
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
SCORE's, which is only possible because W(29) = W(13) * 215441.  Getting
that wrong produces two engines that are both right and appear to
disagree; it happened in another project in this repo during an A/B.

SCORE4W and SCORE10 were frozen 2026-08-23 on the v1 engine and are
REPRODUCED UNCHANGED by v2 and by every wheel change since -- which is the
point: folding a prime into the wheel removes candidates, never survivors,
so a fingerprint still applies and says so.  The whole 2026-08-27 pass
that moved p2 79 -> 127 and 89 -> 137 is invisible to all five
fingerprints, and that is the correct behaviour.

THREE SHAPES HAVE BEEN RE-FROZEN, both times because p1 moved and p1 sets
W -- so the window is a different window and must be:

  2026-08-23  SCORE and SCORE1L, when p1 moved 23 -> 29 at base 4 (1.198x).
              Old: j0 = 4482439 / 33300039331, 8192 / 60858368 blocks,
              fingerprint 7 / 998631924604311.
  2026-08-27  SCORE and SCORE1L again -- NOT for a wheel change but because
              the derived per_launch reached 4096 and the old 4096-period
              window had become exactly ONE launch, which is the blindness
              the four-launch window was introduced to fix.  Same j0, four
              times the blocks.  Old: 4096 / 882446336 blocks, fingerprint
              73 / 1038246173448745.
              SCORE2, when p1 moved 37 -> 41 at base 2 (1.398x) and its
              filter moved 17 -> 19 with it.  Old: n = 17, p1 = 37,
              j0 = 135, 2048 blocks, fingerprint 59 / 17289912876387275.

Those numbers are kept here and in BENCHMARKS.md so the generations stay
auditable even though their SCOREs are not directly comparable.

The candidate rate printed beside each score is the rate after BOTH wheel
mechanisms (flat table x bit planes), so it is `m/s * density()` and not
`blocks/s * R`; at the v2 wheel those differ by two orders of magnitude.

Wall clock: about 70 s, of which the gates are most.
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
    ("SCORE",    4, 19, 29, 65536,       154567,      16384, 255,
     1106501012061793),
    ("SCORE1L",  4, 19, 13, 65536,  33300069047, 3529785344, 255,
     1106501012061793),
    ("SCORE2",   2, 19, 41, 65536,            3,       8192, 444,
     1412016495225835572),
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
        # candidates, not residues: the bit-plane wheel keeps only d2 of the
        # flat table's residues, so R alone would overstate this by 100x
        cand = rate_m * eng.density()
        print(f"benchmark {label}: {rate_m:.3e} m/s over "
              f"[{j0 * eng.W:.4e}, +{line:.4e}) "
              f"({cand:.3e} candidates/s, base {b}, filter "
              f"n={n}, wheel <={p1}+planes<={eng.p2} W={eng.W}, sieve {q2}, "
              f"fingerprint {count}/{xor})")
        print(f"{label} {rate_m / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
