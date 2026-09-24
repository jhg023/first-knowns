"""score.py -- gates x fingerprinted benchmark for clique-ladders.

Prints a SCORE only if every correctness gate is green AND all nine frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count +
xor checksum of the surviving x).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

NINE SHAPES, AND THE REASON IS CLAUDE.md 5g: a shape at every opening the
launcher has.  Here a family has exactly ONE opening -- its open index; the
filter after it does not exist until a term is found -- so there are six
campaign shapes, one per family, each the PLANNED configuration at that
family's open index, named explicitly (wheel, class, depth, window, launch
decomposition) rather than asked of the planner, so that a tuning pass
cannot move a benchmark's window:

  SCORE     A093483, n = 18  class 2 (mod 6),   wheel to 41, 128 periods, sieve 2^17
  S103828   A103828, n = 19  class 9 (mod 30),  wheel to 43, 224 periods, sieve 2^16
  S037100   A037100, n = 19  class 0 (mod 6),   wheel to 41, 224 periods, sieve 2^16
  S119752   A119752, n = 15  class 2 (mod 6),   wheel to 31, 128 periods, sieve 2^17
  S119751   A119751, n = 15  class 9 (mod 30),  wheel to 31, 224 periods, sieve 2^17
  S133761   A133761, n = 17  class 11 (mod 30), wheel to 41, 224 periods, sieve 2^17

            Denominated in THIRD-LEVEL RESIDUES of one SEGMENT: the engine
            sieves a segment of `pb` wheel periods at once, so its natural
            work unit is one third-level residue x every first- and
            second-level residue x the segment's periods, and the shape is
            the first `residues` such residues of the segment at period 1 --
            a set of candidates no launch decomposition can move (G15).
            The wheels and windows differ by family because the plan
            minimises the expected clock to a CONFIRMED find (clique_gpu.plan):
            A037100's a(19) is a tenth as deep as A103828's, so it runs a
            wheel one prime shorter rather than a 32-period window on the
            same one.

and three anchors that belong to no campaign:

  SCORE2L   the x-space TWO-level wheel (23],(37] at n = 15 of A037100 over
            240 of ITS periods (W = 7.42e12), and
  SCORE1L   the x-space ONE-level wheel (primes to 23) over the IDENTICAL
            absolute window, sweeping 33,263 times as many periods.  It must
            return the IDENTICAL fingerprint: two wheels enumerating the same
            candidates by different arithmetic, so a bug in the CRT lift
            shows up here as a mismatch inside the benchmark itself.
  SCORE9    A093483, n = 9, one-level x-space wheel to 13, sieve 4096 -- a
            filter with far more survivors per unit of line, so it weighs
            candidate throughput and the survivor path where the others
            weigh line.

A change that helps one and hurts another is visible instead of averaged
away.  The reported rate is END-TO-END x-line per second, the quantity the
hunt is paid in (the published term IS x), divided by 1e6 for the SCORE.

A FIND MOVES A CAMPAIGN SHAPE'S REASON TO EXIST, NOT ITS FINGERPRINT.  The
shapes name their index, and the form list of an index never changes once it
exists, so every fingerprint here stays reproducible for ever.  What a find
does is open a NEW filter, and rule 5g then owes a shape at it: add one (and
log it) when a campaign is resumed at an index with no shape.

All nine were frozen on 2026-09-19 with engine v3 as inherited from
factorial-ladders plus the forced-class map; five of the six campaign shapes
were RE-FROZEN the same day at planner p2's configuration (the wheel and
window by expected clock, the deeper sieve from 17 forms; OPTIMIZATION_LOG.md
round 1).  S119751 and the three anchors did not move.  A deliberate coverage change
-- a new wheel, a new sieve depth, a new window -- legitimately moves a
fingerprint: update it in the same commit and say why in
OPTIMIZATION_LOG.md.

Wall clock: about 4 min, of which the gates are most.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import clique_gpu                                              # noqa: E402
import clique_model                                            # noqa: E402
import clique_reference                                        # noqa: E402
import clique_search                                           # noqa: E402
from clique_gpu import GpuEngine                               # noqa: E402

# label, family, n, p1, p2, p3, q2, j0, blocks, residues, expected count,
# xor, unit, nu, pb
#
# `pb` and `nu` are PINNED per shape, and that is deliberate.  (pb on a
# campaign shape is the width the planner derives at that opening, so the
# shape IS the campaign's window; it is pinned so that a change to the
# planner moves the fingerprint visibly rather than silently.)  A shape
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
# label, family, n, p1, p2, p3, q2, j0, blocks, residues, count, xor, unit, nu, pb
SHAPES = [
    # RE-FROZEN 2026-09-19 at planner p2's configuration for each opening
    # (OPTIMIZATION_LOG.md round 1: the wheel and window chosen by expected
    # clock, the deeper sieve from 17 forms) -- five of the six moved, each
    # new fingerprint reproduced on a second engine built with the inherited
    # block shape and the smallest queue margin before it was frozen; the
    # three anchors below did not move and are the comparison across it.
    ("SCORE",   "A093483", 18, [5, 7, 11, 13, 17, 19, 23, 29], [31, 37], [41],
     131072, 1, None, 16, 6056, 45373809339410856, 6, 1, 128),
    ("S103828", "A103828", 19, [7, 11, 13, 17, 19, 23, 29], [31, 37], [41, 43],
     65536, 1, None, 16, 10423, 1622921865908186999, 30, 1, 224),
    ("S037100", "A037100", 19, [5, 7, 11, 13, 17, 19, 23, 29], [31, 37], [41],
     65536, 1, None, 8, 6920, 16859153692801908, 6, 1, 224),
    ("S119752", "A119752", 15, [5, 7, 11, 13, 17, 19, 23], [29], [31],
     131072, 1, None, 18, 3948, 621344468468060, 6, 18, 128),
    ("S119751", "A119751", 15, [7, 11, 13, 17, 19, 23, 29], [31], None,
     131072, 1, None, 1, 3949, 527123306958529, 30, 1, 224),
    ("S133761", "A133761", 17, [7, 11, 13, 17, 19, 23, 29], [31, 37], [41],
     131072, 1, None, 16, 7122, 53488743232834886, 30, 1, 224),
    ("SCORE2L", "A037100", 15, 23,   37, None,  65536, 94334,  240, None,
     59938, 1037504555151628, 1, None, 224),
    ("SCORE1L", "A037100", 15, 23, None, None,  65536, 94334 * 33263,
     240 * 33263, None, 59938, 1037504555151628, 1, None, 224),
    ("SCORE9",  "A093483",  9, 13, None, None,   4096, 3330003, 400000000,
     None, 10505565, 9428818188514, 1, None, 224),
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
    gates = (clique_reference.GATES + clique_search.GATES + clique_gpu.GATES
             + clique_model.GATES + certificate.GATES + ceiling.GATES)
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
                                   clique_gpu._wheel_primes(p1, p2, p3)) + "}"
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
