"""score.py -- gates x fingerprinted benchmark for factorial-ladders.

Prints a SCORE only if every correctness gate is green AND all eight frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count +
xor checksum of the surviving x).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

EIGHT SHAPES, AND THE REASON THERE ARE EIGHT IS CLAUDE.md 5g.  The plan is
per filter -- the kill sets grow with n and the period the search can afford
grows with the modelled median -- so a single configuration would measure
one filter and say nothing about the next.  There is a shape at the opening
the campaign starts at and at every filter that costs real time on the
first night:

  SCORE     A177013, n = 17, the PLANNED configuration for the filter that
            costs the night: the wheel {5..29},{31,37,41},{43,47} at unit 6
            (the full wheel the reduction bound admits, a 179-period window
            under the 2^64 bound of engine v2), sieve 65536.  The row to
            read for the hunt's throughput.
            Denominated in THIRD-LEVEL RESIDUES of one SEGMENT: the engine
            sieves a segment of `pb` wheel periods at once, so its natural
            work unit is one third-level residue x every first- and
            second-level residue x the segment's periods, and the shape is
            the first `residues` such residues of the segment at period 1.
            A set of candidates no launch decomposition can move (G15).
  SCOREP    A177014 at the SAME filter and the same wheel.  The two families
            share every killed-set SIZE (the multipliers are identical; only
            the sign differs), so they share the wheel, the period and the
            candidate count -- and NOT the survivors.  The two fingerprints
            differ, which is the cheapest check that the sign reaches the
            kill tables at all.
  SCORE16   A177013, n = 16: the same wheel, sieve 131072 -- the filter the
            campaign reaches within minutes and the first that takes the
            full wheel.
  SCORE18   A177014, n = 18: the same wheel, sieve 32768 -- the filter that
            costs the day after the night.
  SCORE11   A177013, n = 11, the OPENING: the short wheel {5..23},{31} the
            period cap allows there (a(11)'s modelled median is 3e10, a few
            periods of even this wheel), sieve 2^20 (the ladder's top: at
            this filter the analytic survival never reaches the target).
            Whole periods.  Seconds of the campaign, and the row that says
            what the opening costs.
  SCORE2L   the x-space TWO-level wheel (23],(37] at n = 15 over 240 of ITS
            periods (W = 7.42e12), and
  SCORE1L   the x-space ONE-level wheel (primes to 23) over the IDENTICAL
            absolute window, sweeping 33,263 times as many periods.  It must
            return the IDENTICAL fingerprint: two wheels enumerating the same
            candidates by different arithmetic, so a bug in the CRT lift
            shows up here as a mismatch inside the benchmark itself rather
            than as a wrong answer months later.
  SCORE9    A177014, n = 9, one-level x-space wheel to 13, sieve 4096 -- a
            filter with far more survivors per unit of line, so it weighs
            candidate throughput and the survivor path where the others
            weigh line.

A change that helps one and hurts another is visible instead of averaged
away.  The reported rate is END-TO-END x-line per second, the quantity the
hunt is paid in (the published term IS x), divided by 1e6 for the SCORE.

Every period-denominated j0 is an exact multiple of that shape's wheel
modulus, and SCORE1L's window is deliberately the SAME ABSOLUTE WINDOW as
SCORE2L's, which is only possible because W(2L) = W(1L) * 33263.

All eight were frozen on 2026-09-16 with the engine as inherited from
lcm-ladders; the four campaign shapes were RE-FROZEN the same day at engine
v2's 179-period window (OPTIMIZATION_LOG.md round 2 records both sets), and
SCORE11, SCORE2L, SCORE1L and SCORE9 are the anchors across that change.  A
deliberate coverage change -- a new wheel, a new sieve depth, a new window
-- legitimately moves a fingerprint: update it in the same commit and say
why in OPTIMIZATION_LOG.md.  The five campaign shapes name their wheel,
depth, window width and launch decomposition EXPLICITLY rather than asking
the planner: the planner's answer is a default that optimization is
expected to move, and a benchmark whose window moves with it is not an
anchor.  G18 is what checks the planner still produces these.

Wall clock: about 3 min, of which the gates are most.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import fladder_gpu                                              # noqa: E402
import fladder_model                                            # noqa: E402
import fladder_reference                                        # noqa: E402
import fladder_search                                           # noqa: E402
from fladder_gpu import GpuEngine                               # noqa: E402

# label, family, n, p1, p2, p3, q2, j0, blocks, residues, expected count,
# xor, unit, nu, pb
#
# `pb` and `nu` are PINNED per shape, and that is deliberate.  (pb = 192 on
# the campaign shapes is the width the planner derives on this wheel -- the
# reduction bound admits 179 periods -- so the shape IS the campaign's
# segment; it is pinned so a change to that bound or to PB_DEFAULT moves the
# fingerprint visibly rather than silently.)  A shape
# denominated in third-level residues needs the count to be a multiple of nu
# for a whole number of launches to cover exactly that set, and nu is derived
# from CAND_PER_LAUNCH4, which is a tuning constant; pb sets the segment
# width and does the same thing.  Leaving them free would mean every
# launch-size or window-width sweep moved the benchmark's own window
# (OPTIMIZATION.md 2.13, the benchmark shape becoming the blocker).  Pinning
# them makes the shape a fixed SET OF CANDIDATES for the life of the project
# (G15 proves the survivor stream does not depend on the decomposition
# anyway).  The price is that the score cannot see the third level of the
# launch size; the first level (tchunk) still moves with it, and the
# campaign's own rate is measured in the log.
#
# `blocks` sweeps whole wheel periods from period j0.  `residues` is for the
# segment-denominated shapes: the first `residues` third-level residues
# (every first- and second-level residue, every period) of the segment that
# starts at period j0.
W47 = ([5, 7, 11, 13, 17, 19, 23, 29], [31, 37, 41], [43, 47])
SHAPES = [
    # pb = 192 names the PLANNER'S window on this wheel: the 2^64 bound
    # admits 179 periods and the engine takes them all in a six-word window
    # with the last word partial (v1 pinned 64 under the 2^63 bound)
    ("SCORE",   "A177013", 17, *W47, 65536, 1, None, 4,
     237557, 2767396319084044674, 6, 1, 192),
    ("SCOREP",  "A177014", 17, *W47, 65536, 1, None, 4,
     236826, 80766670185484481804, 6, 1, 192),
    ("SCORE16", "A177013", 16, *W47, 131072, 1, None, 4,
     315001, 4287120428541611542, 6, 1, 192),
    ("SCORE18", "A177014", 18, *W47, 32768, 1, None, 4,
     242137, 8189509089178047674, 6, 1, 192),
    ("SCORE11", "A177013", 11, [5, 7, 11, 13, 17, 19, 23], [31], None,
     1 << 20, 1, 4480, None,
     6008, 28122740176000, 6, None, 224),
    ("SCORE2L", "A177013", 15, 23,   37, None,  65536, 94334,  240, None,
     13912, 4097233734626840, 1, None, 224),
    # the SAME absolute window as SCORE2L: W(2L) = W(1L) * 33263 exactly, so
    # both j0 and the block count scale by that factor (written as the
    # product rather than the number, because a hand-multiplied constant was
    # once off by 200 periods in prime-ladders) -- and the SAME fingerprint
    ("SCORE1L", "A177013", 15, 23, None, None,  65536, 94334 * 33263,
     240 * 33263, None, 13912, 4097233734626840, 1, None, 224),
    ("SCORE9",  "A177014",  9, 13, None, None,   4096, 3330003, 400000000,
     None, 5709215, 2391121983764, 1, None, 224),
]


def work_for(eng, j0, blocks, residues):
    """The benchmark's work function for one shape: a callable returning the
    sorted survivors, plus the line it covers and the units it is counted in."""
    if residues is None:
        line = blocks * eng.W

        def work():
            return eng.survivors_j(j0, j0 + blocks)
        return work, line, blocks, eng.R
    if residues > eng.R3 or residues % eng.nu:
        raise ValueError(f"{residues} third-level residues: a segment holds "
                         f"{eng.R3} and a launch {eng.nu}, so the count must "
                         f"be a multiple of {eng.nu} up to {eng.R3}")
    per_res_cand = eng.R1 * eng.R2 * eng.seg_periods
    nl = (residues // eng.nu) * eng.n_tchunks    # launches to take
    line = residues * per_res_cand / eng.density()

    def work():
        out = []
        it = eng.sweep(j0, j0 + eng.seg_periods)
        for i, (_, _, sv) in enumerate(it):
            out.extend(sv)
            if i + 1 >= nl:
                break
        it.close()
        return sorted(out)
    return work, line, residues, per_res_cand


def main():
    gates = (fladder_reference.GATES + fladder_search.GATES + fladder_gpu.GATES
             + fladder_model.GATES + certificate.GATES + ceiling.GATES)
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
    for (label, fam, n, p1, p2, p3, q2, j0, blocks, residues,
         count, xor, unit, nu, pb) in SHAPES:
        eng = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit, nu=nu,
                        pb=pb)
        work, line, units, per_unit = work_for(eng, j0, blocks, residues)
        work()                                          # warm on the window
        runs = 3 if units * per_unit > 10 ** 10 else 5
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
        if not isinstance(p1, int):
            wheel = "{" + ",".join(str(q) for q in
                                   fladder_gpu._wheel_primes(p1, p2, p3)) + "}"
        else:
            wheel = (f"<={p1}" if not p2 else
                     f"({p1}],({p2}],({p3}]" if p3 else f"({p1}],({p2}]")
        if unit > 1:
            wheel += f" at unit {unit}"
        print(f"benchmark {label}: {rate_k:.3e} x/s over "
              f"[{j0 * eng.W:.4e}, +{line:.4e}) "
              f"({rate_k * eng.density():.3e} candidates/s, {fam}, "
              f"filter n={n}, wheel {wheel} W={eng.W}, sieve {q2}, "
              f"fingerprint {count}/{xor})")
        print(f"{label} {rate_k / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
