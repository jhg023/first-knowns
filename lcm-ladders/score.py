"""score.py -- gates x fingerprinted benchmark for lcm-ladders.

Prints a SCORE only if every correctness gate is green AND all seven frozen
benchmark shapes reproduce their work fingerprints exactly (survivor count +
xor checksum of the surviving x).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

SEVEN SHAPES, AND THE REASON THERE ARE SEVEN IS THIS PROJECT'S SHAPE.  Every
filter here is a different line -- the published term is N = L(n)*x, so L,
the forced unit, the wheel, the sieve depth and the period all change with n,
and NOT monotonically (unit 2 at n = 15, 34 at 16, 2 again at 17).  A single
benchmark configuration would therefore measure one opening and say nothing
about the next, which is exactly what CLAUDE.md 5g forbids.  So there is a
shape at every opening the campaign can start at or promote into over the
night it is expected to run:

  SCORE     A078502, n = 15, the PLANNED opening: the SUBSET wheel
            {3,5,7,17,19,23,29,31,37,41,43,47} at unit 2 -- 11 and 13 are
            left to the sieve, because they kill under a tenth of the line
            each and would cost a factor of 143 in period -- sieve 262144,
            from period 1.  The headline campaign's
            first configuration and the row to read for opening throughput.
            Denominated in THIRD-LEVEL RESIDUES of one SEGMENT: the engine
            sieves a segment of eng.pb (192) wheel periods at once, so its
            natural work unit is one third-level residue x every first- and
            second-level residue x 192 periods -- 6.6e9 candidates -- and the
            shape is the first 500 such residues of the segment at period 1.
            A set of candidates no launch decomposition can move (G15).
  SCOREP    A074200 at the SAME filter and the same wheel.  The two families
            share every killed-set SIZE (the multipliers are identical; only
            the sign differs), so they share the wheel, the period and the
            candidate count -- and NOT the survivors.  The two fingerprints
            differ, which is the cheapest check that the sign reaches the
            kill tables at all.
  SCORE16   A078502, n = 16: unit 34, the subset wheel to 53, period
            2.28e17.  The filter the campaign promotes into on its first
            find, and a configuration NOTHING about n = 15 predicts -- 17 is
            forced here and free either side.
  SCORE17   A074200, n = 17: back to unit 2, and the subset wheel here
            skips 11, 13 AND 17 (each keeps over nine tenths of the line at
            this filter) to reach 47 and 53 -- 1.82x fewer candidates per
            unit of line than the prefix wheel, and 1.49x end to end.  The long leg of the
            night (~40 min at the modelled median against seconds at n = 15),
            so this is the row to read for the hunt that actually costs time.
  SCORE2L   the x-space TWO-level wheel (23],(37] at n = 15 over 240 of ITS
            periods (W = 7.42e12), and
  SCORE1L   the x-space ONE-level wheel (primes to 23) over the IDENTICAL
            absolute window, sweeping 33,263 times as many periods.  It must
            return the IDENTICAL fingerprint: two wheels enumerating the same
            candidates by different arithmetic, so a bug in the CRT lift
            shows up here as a mismatch inside the benchmark itself rather
            than as a wrong answer months later.
  SCORE9    A074200, n = 9, one-level x-space wheel to 13, sieve 4096 -- a
            filter with far more survivors per unit of line (5.5 million in
            this window), so it weighs candidate throughput and the survivor
            path where the others weigh line.

A change that helps one and hurts another is visible instead of averaged
away.  The reported rate is END-TO-END x-line per second, the quantity the
hunt is paid in, divided by 1e6 for the SCORE.  To read a rate in the
PUBLISHED term N, multiply by L(n): 360360 at n = 15 and 16, 12252240 at
n = 17.

Every period-denominated j0 is an exact multiple of that shape's wheel
modulus, and SCORE1L's window is deliberately the SAME ABSOLUTE WINDOW as
SCORE2L's, which is only possible because W(2L) = W(1L) * 33263.

SCORE2L, SCORE1L and SCORE9 were frozen on 2026-09-06 and are the anchor
across engine changes: whole wheel periods are the same candidates whatever
sweeps them.  The four CAMPAIGN shapes were re-frozen the same day when the
wheel planner learned to skip a prime -- a deliberate coverage change, which
legitimately moves a fingerprint (OPTIMIZATION_LOG.md round 6).
A deliberate coverage change -- a new wheel, a new sieve depth -- legitimately
moves a fingerprint: update it in the same commit and say why in
OPTIMIZATION_LOG.md.  Note that the four campaign shapes name their wheel and
depth EXPLICITLY rather than asking the planner: the planner's answer is a
default that optimization is expected to move, and a benchmark whose window
moves with it is not an anchor.  G18 is what checks the planner still
produces these.

Wall clock: about 3.5 min, of which the gates are most.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import lcml_gpu                                                 # noqa: E402
import lcml_model                                               # noqa: E402
import lcml_reference                                           # noqa: E402
import lcml_search                                              # noqa: E402
from lcml_gpu import GpuEngine                                  # noqa: E402

# label, family, n, p1, p2, p3, q2, j0, blocks, residues, expected count,
# xor, unit, nu, pb
#
# `pb` and `nu` are PINNED per shape, and that is deliberate.  A shape denominated in third-level residues needs the count to
# be a multiple of nu for a whole number of launches to cover exactly that
# set, and nu is derived from CAND_PER_LAUNCH4, which is a tuning constant.
# Leaving them free would mean every launch-size or window-width sweep moved
# the benchmark's own window -- OPTIMIZATION.md 2.13, the benchmark shape
# becoming the blocker; pb went 192 -> 224 in round 7 and would have taken
# the fingerprints with it.  Pinning it makes the shape a fixed SET OF CANDIDATES for the life
# of the project (G15 proves the survivor stream does not depend on the
# decomposition anyway).  The price is that the score cannot see the third
# level of the launch size; the first level (tchunk) still moves with it, and
# the campaign's own rate is measured in the log.
#
# `blocks` sweeps whole wheel periods from period j0.  `residues` is for the
# segment-denominated shapes: the first `residues` third-level residues
# (every first- and second-level residue, every period) of the segment that
# starts at period j0.
SHAPES = [
    # THE FOUR CAMPAIGN SHAPES NAME THEIR WHEEL AS A LIST, because the
    # campaign's wheel is a SUBSET of the primes and not a prefix of them
    # (lcml_gpu.wheel_plan).  They were re-frozen on 2026-09-06 when the
    # planner learned to skip a prime: the old shapes named prefix wheels
    # (19,31,43] and (23,37,47], which the campaign no longer runs, so a
    # score against them had stopped measuring the hunt.  The x-space
    # shapes below are untouched and are the anchor across that change.
    ("SCORE",   "A078502", 15, [3, 5, 7, 17, 19, 23, 29, 31], [37, 41],
     [43, 47], 262144, 1, None, 96,
     74297, 849661955738965598, 2, 4, 192),
    ("SCOREP",  "A074200", 15, [3, 5, 7, 17, 19, 23, 29, 31], [37, 41],
     [43, 47], 262144, 1, None, 96,
     74590, 962011421661791124, 2, 4, 192),
    ("SCORE16", "A078502", 16, [3, 5, 7, 19, 23, 29, 31, 37], [41, 43],
     [47, 53], 131072, 1, None, 20,
     118075, 21369117790222865260, 34, 1, 192),
    ("SCORE17", "A074200", 17, [3, 5, 7, 19, 23, 29, 31, 37], [41, 43],
     [47, 53], 65536, 1, None, 54,
     119087, 2410739981118000456, 2, 1, 192),
    ("SCORE2L", "A078502", 15, 23,   37, None,  65536, 94334,  240, None,
     8691, 702330747726546914, 1, None, 192),
    # the SAME absolute window as SCORE2L: W(2L) = W(1L) * 33263 exactly, so
    # both j0 and the block count scale by that factor (written as the
    # product rather than the number, because a hand-multiplied constant was
    # once off by 200 periods in prime-ladders) -- and the SAME fingerprint
    ("SCORE1L", "A078502", 15, 23, None, None,  65536, 94334 * 33263,
     240 * 33263, None, 8691, 702330747726546914, 1, None, 192),
    ("SCORE9",  "A074200",  9, 13, None, None,   4096, 3330003, 400000000,
     None, 5537992, 1223908228450, 1, None, 192),
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
    gates = (lcml_reference.GATES + lcml_search.GATES + lcml_gpu.GATES
             + lcml_model.GATES + certificate.GATES + ceiling.GATES)
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
                                   lcml_gpu._wheel_primes(p1, p2, p3)) + "}"
        else:
            wheel = (f"<={p1}" if not p2 else
                     f"({p1}],({p2}],({p3}]" if p3 else f"({p1}],({p2}]")
        if unit > 1:
            wheel += f" at unit {unit}"
        print(f"benchmark {label}: {rate_k:.3e} x/s over "
              f"[{j0 * eng.W:.4e}, +{line:.4e}) "
              f"({rate_k * eng.density():.3e} candidates/s, "
              f"{rate_k * lcml_reference.L(n):.3e} N/s, {fam}, "
              f"filter n={n}, wheel {wheel} W={eng.W}, sieve {q2}, "
              f"fingerprint {count}/{xor})")
        print(f"{label} {rate_k / 1e6:,.0f}")
    return 0 if ok_all else 1


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main))
