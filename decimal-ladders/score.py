"""score.py -- gates x fingerprinted benchmark for decimal-ladders.

Prints a SCORE only if every correctness gate is green AND every frozen
benchmark shape reproduces its work fingerprint exactly (survivor count +
xor of the surviving x).  An engine that skips work fails the fingerprint;
an engine that breaks the mathematics fails the gates.  Either way it
scores nothing.  Optimize under the score, never around it.

THE SHAPES, AND WHY THESE (CLAUDE.md 5g).  The plan is per filter -- the
kill sets, the forced unit and the affordable wheel all move with n -- so
one configuration would measure one filter.  There is a shape at each
family's OPENING and at the filter where each family's hunt spends its days:

  SCORE     A305740, n = 18: the planned configuration of the filter that
            costs the most (a(18)'s median is 8.6e23, the last reachable
            term).  THE ROW TO READ for the hunt's throughput; the SCORE of
            a commit is this row.
  SCORE153  A153431, n = 17: the same for the other family (a(17), median
            1.4e24).
  SCORE13   A305740, n = 13: the opening (seconds of the campaign).
  SCORE14   A153431, n = 14: the opening.
  SCORE2L   the x-space TWO-level wheel (23],(37] at n = 15 of A305740 over
            240 of ITS periods, and
  SCORE1L   the x-space ONE-level wheel (primes to 23) over the IDENTICAL
            absolute window: two wheels enumerating the same candidates by
            different arithmetic must return the IDENTICAL fingerprint, so a
            CRT-lift bug shows up inside the benchmark itself.
  SCORE9    A153431, n = 9, one-level x-space wheel to 13, sieve 4096 -- far
            more survivors per unit of line, so it weighs the survivor path.

The four campaign shapes name their wheel, depth, window, unit and launch
decomposition EXPLICITLY -- `_families_stay_apart` in launch.py asserts they
are exactly what the campaign plans, so a planner change must re-freeze them
in the same commit -- and are denominated in LAUNCHES of a pinned (tchunk,
nu): the first `launches` launches of the segment at period j0, a fixed set
of candidates no tuning constant can move.  The reported rate is END-TO-END
line per second (the published term IS x), divided by 1e6 for the number.

Wall clock: about 3 min, of which the gates are most.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import decl_gpu                                                 # noqa: E402
import decl_model                                               # noqa: E402
import decl_reference                                           # noqa: E402
import decl_search                                              # noqa: E402
from decl_gpu import GpuEngine                                  # noqa: E402

# (label, family, n, p1, p2, p3, q2, j0, blocks, launches, count, xor,
#  unit, nu, pb, tchunk, campaign)
#
# `blocks` sweeps whole wheel periods from period j0; `launches` takes the
# first that many launches of the segment at period j0 with the pinned
# (tchunk, nu) -- one of the two is None.
SHAPES = [
    ("SCORE", "A305740", 18,
     (3, 23, 29, 31, 47, 59), (11, 13, 43, 53), (61, 67), 262144,
     1000, None, 16, 21219, 633403670445840895464015, 2261, 1, 224, 19456, True),
    ("SCORE153", "A153431", 17,
     (3, 5, 11, 13, 23, 29, 31), (43, 47, 59), (61, 67), 262144,
     1000, None, 16, 8163, 119430980700175536911810, 4522, 1, 256, 18048, True),
    ("SCORE13", "A305740", 13,
     (3, 11, 13, 17, 19, 23, 29), (31,), (43,), 1048576,
     1120, 192 * 40, None, 126079, 1240139239024586, 7, 30, 192, 483840, True),
    ("SCORE14", "A153431", 14,
     (3, 5, 11, 13, 17, 19, 23, 29), (31, 43), (47,), 262144,
     1120, None, 8, 30533, 485706402864992910, 14, 2, 256, 451584, True),
    ("SCORE2L", "A305740", 15, 23, 37, None, 65536, 94334, 240, None,
     15297, 698556166393375796, 1, None, 224, None, False),
    # the SAME absolute window as SCORE2L: W(2L) = W(1L) * 33263 exactly
    ("SCORE1L", "A305740", 15, 23, None, None, 65536, 94334 * 33263,
     240 * 33263, None, 15297, 698556166393375796, 1, None, 224, None, False),
    ("SCORE9", "A153431", 9, 13, None, None, 4096, 3330003, 400000000,
     None, 3346661, 4216072310568, 1, None, 224, None, False),
]


def work_for(eng, j0, blocks, launches):
    """(work, line, units, per_unit): the benchmark's work function for one
    shape, the line it covers and the units it is counted in."""
    if blocks is not None:
        line = blocks * eng.W

        def work():
            return eng.survivors_j(j0, j0 + blocks)
        return work, line, blocks, eng.R
    # the line these launches ACTUALLY cover: the last first-level chunk of
    # each unit is partial, so launches x cand_per_launch overcounted the
    # campaign shapes by ~1.12 (OPTIMIZATION_LOG.md Measurement 12)
    line = eng.line_between(0, launches)
    per_launch = line * eng.density() / launches

    # `limit`: the sweep runs one launch ahead, and stopping the iterator
    # after `launches` results left launch launches + 1 queued, which the
    # timer's synchronize then charged to the work -- SCORE read 16/17 of
    # the rate, SCORE14 8/9 (measured 1.061 and 1.122 against the predicted
    # 1.0625 and 1.125; BENCHMARKS.md)
    def work():
        out = []
        for _, _, sv in eng.sweep(j0, j0 + eng.seg_periods, limit=launches):
            out.extend(sv)
        return sorted(out)
    return work, line, launches, per_launch


def main():
    gates = (decl_reference.GATES + decl_search.GATES + decl_gpu.GATES
             + decl_model.GATES + certificate.GATES + ceiling.GATES)
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
    for (label, fam, n, p1, p2, p3, q2, j0, blocks, launches, count, xor,
         unit, nu, pb, tchunk, _camp) in SHAPES:
        kw = dict(p1=p1, p2=p2, p3=p3, q2=q2, unit=unit, nu=nu, pb=pb)
        if tchunk is not None:
            kw.update(tchunk=tchunk, seg_cap=pb)
        eng = GpuEngine(n, fam, **kw)
        work, line, units, per_unit = work_for(eng, j0, blocks, launches)
        work()                                          # warm on the window
        runs = 3 if units * per_unit > 10 ** 10 else 5
        if count is None:
            got = work()
            g = 0
            for v in got:
                g ^= int(v)
            print(f"  ({label}: UNFROZEN -- count={len(got)} xor={g})")
            ok_all = False
            continue
        rate_units, ok = scoring.fingerprint_benchmark(
            work, units, count, xor, runs=runs, sync=sync)
        if not ok:
            got = work()
            g = 0
            for v in got:
                g ^= int(v)
            print(f"  ({label}: got count={len(got)} xor={g})")
            ok_all = False
            continue
        rate_k = rate_units * line / units
        wheel = "{" + ",".join(str(q) for q in
                               decl_gpu._wheel_primes(p1, p2, p3)) + "}"
        if unit > 1:
            wheel += f" at unit {unit}"
        print(f"benchmark {label}: {rate_k:.3e} x/s from period {j0} "
              f"({rate_k * eng.density():.3e} candidates/s, {fam}, "
              f"filter n={n}, wheel {wheel} W={eng.W}, window {eng.pv} "
              f"{'wide' if eng.wide else 'narrow'}, sieve {q2}, "
              f"fingerprint {count}/{xor})")
        print(f"{label} {rate_k / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
