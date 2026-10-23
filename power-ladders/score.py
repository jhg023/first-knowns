"""score.py -- gates x fingerprinted benchmark for power-ladders.

Prints a SCORE only if every correctness gate is green AND every frozen
benchmark shape reproduces its work fingerprint exactly (survivor count +
xor checksum of the surviving terms).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

A SHAPE AT EVERY OPENING THE LAUNCHER HAS (CLAUDE.md 5g), and at A229902's
live filter: five campaign shapes, each the PLANNED configuration there,
named explicitly (wheel, class, depth, window, launch decomposition) rather
than asked of the planner, so that a tuning pass cannot move a benchmark's
window, and each with the DEVICE FERMAT STAGE on (prp = the launcher's
CENSUS_FLOOR, six forms) -- the stream the campaign classifies:

  SCORE     A229626, n = 10  unit 1, wheel {3..31 less 19, 29},{47,73},{89},
                             sieve 2^13, 128-period segments
  S229627   A229627, n = 9   class 1 (mod 6), wheel {5..23},{31,41},{47}
  S229630   A229630, n = 9   unit 1, THE SEMIPRIME WHEEL (round 5) WITH ITS
                             COFACTOR SIEVE (round 6): {2..31 less 19,
                             29},{47},{73} in four branches, 128 periods of
                             the doubled wheel -- the same line as the v1
                             plan's 256
  S229630L  A229630, n = 11  the live filter, a day-long one (CLAUDE.md 3b):
                             {2..23},{31,41,47},{73,89}, four branches, at
                             the campaign's height
  S229902   A229902, n = 9   class 0 (mod 10), wheel {3,7,..,23,43},{47}
  S229902L  A229902, n = 10  the live filter after the first segment (which
                             records a(9) = a(8)): {3,7,..,23,43},{47,61},{83}

            Denominated in THIRD-LEVEL RESIDUES of one SEGMENT, the segment
            that holds the frontier term (so the Fermat stage runs at the
            limb counts the campaign does): the engine sieves a segment of
            `pb` wheel periods at once, so its natural work unit is one
            third-level residue x every first- and second-level residue x
            the segment's periods -- a set of candidates no launch
            decomposition can move (G15).

            The semiprime shapes are denominated in LAUNCHES of each branch
            from the start of the segment -- `residues` of the first, and
            the same fraction of each other branch's (at least one) -- and
            their line is the candidates those launches hold over the
            wheel's density.  Pinned: the plan fixes every branch's launch
            decomposition, and a change to it is a new fingerprint.

and three anchors that belong to no campaign (the sieve stream, no Fermat
stage):

  SCORE2L   the x-space TWO-level wheel (19],(31] at n = 10 of A229626 over
            24 of ITS periods (W = 2.0e11), and
  SCORE1L   the x-space ONE-level wheel (primes to 19) over the IDENTICAL
            absolute window, sweeping 20,677 times as many periods.  It must
            return the IDENTICAL fingerprint: two wheels enumerating the same
            candidates by different arithmetic, so a bug in the CRT lift
            shows up here as a mismatch inside the benchmark itself.
  SCORE6    A229626, n = 6, one-level x-space wheel to 13, sieve 4096 -- a
            filter with far more survivors per unit of line, so it weighs
            candidate throughput and the survivor path where the others
            weigh line.

The reported rate is END-TO-END line of the term per second (m/s, q/s),
the quantity the hunt is paid in, divided by 1e6 for the SCORE.

A FIND MOVES A CAMPAIGN SHAPE'S REASON TO EXIST, NOT ITS FINGERPRINT: the
shapes name their index, and an index's form list never changes.  When a
campaign is resumed at an index with no shape, add one (and log it).

Frozen 2026-10-15 on engine v1 and planner p1 (OPTIMIZATION_LOG.md);
S229630 re-frozen on A229630's plan p2, the semiprime wheel, and S229630L
added at its live filter, 2026-10-19 (round 5): the new S229630 stream is
the old plan's over the same segment filtered by semi_wheel_ok, 2,899 of
10,276.  Both re-frozen on plan p3, the cofactor sieve, 2026-10-20 (round
6): S229630 still covers the whole segment (4 launches of the first branch
and all of the others), and its stream is p2's filtered by
semi_cofactor_ok, 1,439 of 2,899; S229630L is 16 launches of the first
branch, about the old shape's 51 launches in all.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import power_gpu                                                # noqa: E402
import power_model                                              # noqa: E402
import power_reference                                          # noqa: E402
import power_search                                             # noqa: E402
from power_gpu import GpuEngine                                 # noqa: E402

KNOWN = power_reference.KNOWN

# label, family, n, p1, p2, p3, q2, j0, blocks, residues, expected count,
# xor, unit, nu, pb, prp
#
# `pb` and `nu` are PINNED per shape, deliberately (pb on a campaign shape is
# the width the planner derives at that opening): a shape denominated in
# third-level residues needs the count to be a multiple of nu, and leaving
# either free would let a launch-size sweep move the benchmark's own window.
# `blocks` sweeps whole wheel periods from period j0.  `residues` is for the
# segment-denominated shapes: the first `residues` third-level residues of
# the segment that starts at period j0.
_W626 = 3 * 5 * 7 * 11 * 13 * 17 * 23 * 31 * 47 * 73 * 89
_W627 = 6 * 5 * 7 * 11 * 13 * 17 * 19 * 23 * 31 * 41 * 47
_W630 = 2 * 3 * 5 * 7 * 11 * 13 * 17 * 23 * 31 * 47 * 73
_W902 = 10 * 3 * 7 * 11 * 13 * 17 * 23 * 43 * 47
_W902L = _W902 * 61 * 83
SHAPES = [
    ("SCORE",    "A229626", 10, [3, 5, 7, 11, 13, 17, 23, 31], [47, 73], [89],
     8192, max(1, KNOWN["A229626"][9] // _W626), None, 3, 2695, 7609207792066970, 1, 1, 128, 6),
    ("S229627",  "A229627", 9, [5, 7, 11, 13, 17, 19, 23], [31, 41], [47],
     8192, max(1, KNOWN["A229627"][8] // _W627), None, 16, 607, 684580967501399, 6, 2, 256, 6),
    ("S229630",  "A229630", 9, [2, 3, 5, 7, 11, 13, 17, 23, 31], [47], [73],
     8192, max(1, KNOWN["A229630"][8] // _W630), None, 4, 1439, 98230428482451,
     1, None, 128, 6),
    # period 643 of the semiprime wheel, m = 5.567e19: the segment the live
    # campaign stood in at round 5 (period 1286 of the v1 plan's wheel)
    ("S229630L", "A229630", 11, [2, 3, 5, 7, 11, 13, 17, 19, 23], [31, 41, 47],
     [73, 89], 8192, 643, None, 16, 1448, 1935969150529959824, 1, None,
     128, 6),
    ("S229902",  "A229902", 9, [3, 7, 11, 13, 17, 23, 43], [47], None,
     8192, max(1, KNOWN["A229902"][8] // _W902), 5120, None, 1440, 109687303892984, 10, 1, 256, 6),
    ("S229902L", "A229902", 10, [3, 7, 11, 13, 17, 23, 43], [47, 61], [83],
     8192, KNOWN["A229902"][8] // _W902L + 1, None, 2, 1081, 11208449253174586, 10, 1, 256, 6),
    ("SCORE2L",  "A229626", 10, 19, 31, None, 65536, 600, 24, None,
     455547, 118758903108175, 1, None, 224, 0),
    ("SCORE1L",  "A229626", 10, 19, None, None, 65536, 600 * 20677,
     24 * 20677, None, 455547, 118758903108175, 1, None, 224, 0),
    ("SCORE6",   "A229626", 6, 13, None, None, 4096, 3330003, 40000,
     None, 234204, 3906727894, 1, None, 224, 0),
]


def work_for(eng, j0, blocks, residues):
    """The benchmark's work function for one shape: a callable returning the
    sorted survivors, plus the line it covers and the units it is counted in."""
    if hasattr(eng, "parts"):
        return _work_for_branches(eng, j0, residues)
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


def _work_for_branches(eng, j0, k1):
    """The semiprime wheel's work unit: the first k1 launches of the first
    branch's segment and the same fraction (at least one) of every other
    branch's; the line is the candidates they hold over the density."""
    l1 = eng.parts[0].launches_per_segment
    ks = [max(1, round(k1 * p.launches_per_segment / l1)) for p in eng.parts]
    if any(k > p.launches_per_segment for k, p in zip(ks, eng.parts)):
        raise ValueError(f"{ks} launches: a branch's segment holds fewer")
    cand = sum(k * p.R * p.pv / p.launches_per_segment
               for k, p in zip(ks, eng.parts))
    line = cand / eng.density()

    def work():
        out = []
        for k, p in zip(ks, eng.parts):
            it = p.sweep(j0, j0 + p.seg_periods)
            for i, (_, _, sv) in enumerate(it):
                out.extend(sv)
                if i + 1 >= k:
                    break
            it.close()
        return sorted(out)
    return work, line, sum(ks), cand / sum(ks)


def engine_for(row):
    """The engine a shape names, exactly as it names it."""
    (_label, fam, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, nu, pb,
     prp) = row
    if power_reference.domain(fam) == "semiprime":
        return power_gpu.SemiprimeEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2,
                                         unit=unit, pb=pb, prp=prp)
    return GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit, nu=nu,
                     pb=pb, prp=prp, seg_cap=pb if prp else None)


def main():
    gates = (power_reference.GATES + power_search.GATES
             + power_gpu.GATES + power_model.GATES
             + certificate.GATES + ceiling.GATES)
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
         count, xor, unit, nu, pb, prp) = row
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
                                   power_gpu._wheel_primes(p1, p2, p3)) + "}"
        else:
            wheel = (f"<={p1}" if not p2 else
                     f"({p1}],({p2}],({p3}]" if p3 else f"({p1}],({p2}]")
        if unit > 1:
            wheel += f" in the class {eng.r0} (mod {unit})"
        t = power_reference.letter(fam)
        print(f"benchmark {label}: {rate_k:.3e} {t}/s over "
              f"[{j0 * eng.W:.4e}, +{line:.4e}) "
              f"({rate_k * eng.density():.3e} candidates/s, {fam}, "
              f"filter n={n}, wheel {wheel} W={eng.W}, sieve {q2}, "
              f"Fermat stage {prp} forms, fingerprint {count}/{xor})")
        print(f"{label} {rate_k / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
