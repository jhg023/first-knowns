"""score.py -- gates x fingerprinted benchmark for plus-two-cliques.

Prints a SCORE only if every correctness gate is green AND all five frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count +
xor checksum of the surviving x).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

FIVE SHAPES, AND THE REASON IS CLAUDE.md 5g: a shape at every opening the
launcher has.  Here a family has exactly ONE opening -- its open index; the
filter after it does not exist until a term is found -- so there are two
campaign shapes, one per family, each the PLANNED configuration at that
family's open index, named explicitly (wheel, class, depth, window, launch
decomposition) rather than asked of the planner, so that a tuning pass
cannot move a benchmark's window:

  SCORE     A083518, n = 14  class 3 (mod 6), wheel {5..23},{31}, 160 periods,
                             sieve 2^19
  S083519   A083519, n = 11  class 3 (mod 6), wheel {5..23}, 160 periods,
                             sieve 2^20

            Denominated in THIRD-LEVEL RESIDUES of one SEGMENT: the engine
            sieves a segment of `pb` wheel periods at once, so its natural
            work unit is one third-level residue x every first- and
            second-level residue x the segment's periods, and the shape is
            the first `residues` such residues of the segment at period 1 --
            a set of candidates no launch decomposition can move (G15).
            Neither planned opening wheel has a third level, so each shape
            is the whole first segment.

and three anchors that belong to no campaign:

  SCORE2L   the x-space TWO-level wheel (23],(37] at n = 14 of A083518 over
            24 of ITS periods (W = 7.42e12), and
  SCORE1L   the x-space ONE-level wheel (primes to 23) over the IDENTICAL
            absolute window, sweeping 33,263 times as many periods (W =
            2.23e8).  It must
            return the IDENTICAL fingerprint: two wheels enumerating the same
            candidates by different arithmetic, so a bug in the CRT lift
            shows up here as a mismatch inside the benchmark itself.
  SCORE9    A083519, n = 9, one-level x-space wheel to 13, sieve 4096 -- a
            filter with far more survivors per unit of line (5,957,470
            over 1.2e13), so it weighs candidate throughput and the survivor
            path where the others weigh line.

A change that helps one and hurts another is visible instead of averaged
away.  The reported rate is END-TO-END a(n)-line per second, the quantity the
hunt is paid in (the published term IS the swept integer), divided by 1e6
for the SCORE.

A FIND MOVES A CAMPAIGN SHAPE'S REASON TO EXIST, NOT ITS FINGERPRINT.  The
shapes name their index, and the form list of an index never changes once it
exists, so every fingerprint here stays reproducible for ever.  What a find
does is open a NEW filter, and rule 5g then owes a shape at it: add one (and
log it) when a campaign is resumed at an index with no shape.

All five were frozen on 2026-10-01 with this project's engine v1 (product-
cliques' engine v2, with the first-level chunk capped at gridDim.y) and
planner p2, after the GPU/CPU parity gate (G9) passed on 26 populated
windows (OPTIMIZATION_LOG.md).  Engine v2 (round 2, 2026-10-01: lazy narrow
rounds, u32 queue entries, packed window offsets, the per-launch offset
table) reproduced all five bit for bit; nothing was re-frozen.  Engine v3
(round 3, 2026-10-02: the periodic window on quad loads, the wide record's
folded rounds, the generated tail rounds) reproduced all five again.  The
anchors are not product-cliques' windows:
its SCORE2L/1L window at n = 13 here keeps 4.67 million survivors and took
39 s a run, so they moved to n = 14 and a tenth of the periods.  A deliberate
coverage change -- a new wheel, a new sieve depth, a new window --
legitimately moves a fingerprint: update it in the same commit and say why in
OPTIMIZATION_LOG.md.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import plus2_gpu                                                # noqa: E402
import plus2_model                                              # noqa: E402
import plus2_reference                                          # noqa: E402
import plus2_search                                             # noqa: E402
from plus2_gpu import GpuEngine                                 # noqa: E402

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
# anyway).
#
# `blocks` sweeps whole wheel periods from period j0.  `residues` is for the
# segment-denominated shapes: the first `residues` third-level residues
# (every first- and second-level residue, every period) of the segment that
# starts at period j0.
SHAPES = [
    # Each is its family's planned opening (G-check:
    # launch._families_stay_apart), each the WHOLE first segment.
    ("SCORE",   "A083518", 14, [5, 7, 11, 13, 17, 19, 23], [31], None,
     524288, 1, None, 1, 6511, 110145145451837, 6, 1, 160),
    ("S083519", "A083519", 11, [5, 7, 11, 13, 17, 19, 23], None, None,
     1048576, 1, None, 1, 31882, 81801758003166, 6, 1, 160),
    ("SCORE2L", "A083518", 14, 23,   37, None,  65536, 94334,   24, None,
     137965, 699912790830580669, 1, None, 224),
    ("SCORE1L", "A083518", 14, 23, None, None,  65536, 94334 * 33263,
     24 * 33263, None, 137965, 699912790830580669, 1, None, 224),
    ("SCORE9",  "A083519",  9, 13, None, None,   4096, 3330003, 400000000,
     None, 5957470, 13208176851254, 1, None, 224),
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


def engine_for(row):
    """The engine a shape names, exactly as it names it."""
    (_label, fam, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, nu, pb) = row
    return GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit, nu=nu,
                     pb=pb)


def main():
    gates = (plus2_reference.GATES + plus2_search.GATES + plus2_gpu.GATES
             + plus2_model.GATES + certificate.GATES + ceiling.GATES)
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
    for row in SHAPES:
        (label, fam, n, p1, p2, p3, q2, j0, blocks, residues,
         count, xor, unit, nu, pb) = row
        eng = engine_for(row)
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
                                   plus2_gpu._wheel_primes(p1, p2, p3)) + "}"
        else:
            wheel = (f"<={p1}" if not p2 else
                     f"({p1}],({p2}],({p3}]" if p3 else f"({p1}],({p2}]")
        if unit > 1:
            wheel += f" in the class {eng.r0} (mod {unit})"
        print(f"benchmark {label}: {rate_k:.3e} a(n)-line/s over "
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
