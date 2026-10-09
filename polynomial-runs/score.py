"""score.py -- gates x fingerprinted benchmark for polynomial-runs.

Prints a SCORE only if every correctness gate is green AND all seven frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count +
xor checksum of the surviving terms).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

SEVEN SHAPES, AND THE REASON IS CLAUDE.md 5g: a shape at every opening the
launcher has.  Four campaign shapes, one per family at its open index, each
the PLANNED configuration there, named explicitly (wheel, class, depth,
window, launch decomposition) rather than asked of the planner, so that a
tuning pass cannot move a benchmark's window:

  SCORE     A165234, n = 16  class 5 (mod 6), wheel {5..29},{31},{37},
                             sieve 2^15, 256-period segments
  S230663   A230663, n = 16  class 1 (mod 6), wheel {5..23},{29,31},{37},
                             sieve 2^15
  S092120   A092120, n = 16  class 1 (mod 6), wheel {5..29},{31,37},{41},
                             sieve 2^16
  S347537   A347537, n = 17  class 1 (mod 6), wheel {5..29},{31,37},{43},
                             sieve 2^17

            Denominated in THIRD-LEVEL RESIDUES of one SEGMENT: the engine
            sieves a segment of `pb` wheel periods at once, so its natural
            work unit is one third-level residue x every first- and
            second-level residue x the segment's periods -- a set of
            candidates no launch decomposition can move (G15).  Each takes
            the WHOLE third level of the segment at period 1.

and three anchors that belong to no campaign:

  SCORE2L   the x-space TWO-level wheel (23],(37] at n = 17 of A165234 over
            240 of ITS periods (W = 7.42e12), and
  SCORE1L   the x-space ONE-level wheel (primes to 23) over the IDENTICAL
            absolute window, sweeping 33,263 times as many periods.  It must
            return the IDENTICAL fingerprint: two wheels enumerating the same
            candidates by different arithmetic, so a bug in the CRT lift
            shows up here as a mismatch inside the benchmark itself.
  SCORE9    A092120, n = 9, one-level x-space wheel to 13, sieve 4096 -- a
            filter with far more survivors per unit of line, so it weighs
            candidate throughput and the survivor path where the others
            weigh line.

The reported rate is END-TO-END line of the term per second (p/s), the
quantity the hunt is paid in, divided by 1e6 for the SCORE.

A FIND MOVES A CAMPAIGN SHAPE'S REASON TO EXIST, NOT ITS FINGERPRINT: the
shapes name their index, and an index's form list never changes.  When a
campaign is resumed at an index with no shape, add one (and log it).

Frozen 2026-10-08 on engine v1 (primorial-runs' engine v2 taken whole) and
planner p1, after G9 passed on populated windows (OPTIMIZATION_LOG.md);
reproduced the same day by engine v2 (the fallback out of line, the queue
margin re-ranked on the compiled footprint: a faster kernel, the same
stream).
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import poly_gpu                                            # noqa: E402
import poly_model                                          # noqa: E402
import poly_reference                                      # noqa: E402
import poly_search                                         # noqa: E402
from poly_gpu import GpuEngine                             # noqa: E402

# label, family, n, p1, p2, p3, q2, j0, blocks, residues, expected count,
# xor, unit, nu, pb
#
# `pb` and `nu` are PINNED per shape, deliberately (pb on a campaign shape is
# the width the planner derives at that opening): a shape denominated in
# third-level residues needs the count to be a multiple of nu, and leaving
# either free would let a launch-size sweep move the benchmark's own window.
# `blocks` sweeps whole wheel periods from period j0.  `residues` is for the
# segment-denominated shapes: the first `residues` third-level residues of
# the segment that starts at period j0.
SHAPES = [
    ("SCORE",   "A165234", 16, [5, 7, 11, 13, 17, 19, 23, 29], [31], [37],
     32768, 1, None, 21, 6521, 1601343003530803, 6, 21, 256),
    ("S230663", "A230663", 16, [5, 7, 11, 13, 17, 19, 23], [29, 31], [37],
     32768, 1, None, 21, 9120, 682995423446552, 6, 21, 256),
    ("S092120", "A092120", 16, [5, 7, 11, 13, 17, 19, 23, 29], [31, 37], [41],
     65536, 1, None, 24, 27481, 11674479549184331, 6, 24, 256),
    ("S347537", "A347537", 17, [5, 7, 11, 13, 17, 19, 23, 29], [31, 37], [43],
     131072, 1, None, 28, 12208, 102828151028243808, 6, 28, 256),
    ("SCORE2L", "A165234", 17, 23,   37, None,  65536, 94334,   240, None,
     624, 3399412268315720, 1, None, 224),
    ("SCORE1L", "A165234", 17, 23, None, None,  65536, 94334 * 33263,
     240 * 33263, None, 624, 3399412268315720, 1, None, 224),
    ("SCORE9",  "A092120",  9, 13, None, None,   4096, 3330003, 100000000,
     None, 202174, 3963986673996, 1, None, 224),
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
    gates = (poly_reference.GATES + poly_search.GATES
             + poly_gpu.GATES + poly_model.GATES
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
                                   poly_gpu._wheel_primes(p1, p2, p3)) + "}"
        else:
            wheel = (f"<={p1}" if not p2 else
                     f"({p1}],({p2}],({p3}]" if p3 else f"({p1}],({p2}]")
        if unit > 1:
            wheel += f" in the class {eng.r0} (mod {unit})"
        t = poly_reference.letter(fam)
        print(f"benchmark {label}: {rate_k:.3e} {t}/s over "
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
