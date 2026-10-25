"""score.py -- gates x fingerprinted benchmark for cyclotomic-ladders.

Prints a SCORE only if every correctness gate is green AND every frozen
benchmark shape reproduces its work fingerprint exactly (survivor count +
xor checksum of the surviving terms).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

THE HEADLINE SITS AT THE DAY-LONG FILTER (CLAUDE.md 3b), and there is a
shape at every opening the launcher has (5g).  Each campaign shape is the
PLANNED configuration there, named explicitly (wheel, class, depth, window,
launch decomposition) rather than asked of the planner, so that a tuning
pass cannot move a benchmark's window, and each with the DEVICE FERMAT
STAGE on (prp = the launcher's CENSUS_FLOOR, six forms) -- the stream the
campaign classifies:

  SCORE     A070737, n = 13  the filter whose term the model puts at days
                             (a(13) median 1.7e25): the class 0 (mod 30030),
                             the planned wheel, at the height of the a(13)
                             line's start (the a(12) median)
  S11       A070737, n = 11  the OPENING, from a(10) = 1.35e16
  S12       A070737, n = 12  the first promotion
  D60       A072942, n = 60  class 0 (mod 56,786,730): the first day-long
                             index (median 3.4e25)
  D72       A072942, n = 72  class 0 (mod 2*3*5*7*13*19*37*73)
  D84       A072942, n = 84  class 0 (mod 2*3*5*7*13*29*43)
  D90       A072942, n = 90  class 0 (mod 2*3*7*11*19*31)
  D96       A072942, n = 96  class 0 (mod 2*3*5*7*13*17*97)
  D60p2, D72p2, D84p2, D96p2 the same four indices on the wheels planner
                             p2 ran (named explicitly): planner p3 moved
                             D60, D72, D84 and D96 to the MEASURED wheels
                             (OPTIMIZATION_LOG.md round 2), and the p2
                             workloads keep their fingerprints beside them
                             -- two wheels enumerating one line by different
                             CRTs, both reproduced by one engine

            Denominated in LAUNCHES of one SEGMENT, the segment that holds
            the shape's height (so the Fermat stage runs at the limb counts
            the campaign does), at a PINNED launch decomposition: the
            engine sieves a segment of `pb` wheel periods at once, in
            launches of a first-level chunk (`tchunk`) x `nu` third-level
            residues x every second-level residue x the segment's periods,
            and with tchunk and nu pinned per shape (SHAPE_TCHUNK, frozen
            with the fingerprint) the first SHAPE_LAUNCHES launches are a
            FIXED set of candidates that no later planner or guard can
            move -- the complete workload CYL-008 asks for.  A whole
            third-level residue would be the decomposition-free unit (G15),
            but at A070737 n = 13 one residue is 115 launches of 119 ms and
            at A072942 n = 96 177, and the battery has five minutes.

and three anchors that belong to no campaign (the sieve stream, no Fermat
stage):

  SCORE2L   A070737 n = 9 in the class 0 (mod 210): the TWO-level wheel
            (13],(23] over 24 of ITS periods (W = 6.9e8), and
  SCORE1L   the ONE-level wheel (primes to 13) over the IDENTICAL absolute
            window, sweeping 24 x (17*19*23 = 7429) periods.  It must return
            the IDENTICAL fingerprint: two wheels enumerating the same
            candidates by different arithmetic, so a bug in the CRT lift
            shows up here as a mismatch inside the benchmark itself.
  SCORE6    A072942, n = 12, class 0 (mod 2730), one-level wheel to 13 (so a
            wheel of 11 alone), sieve 4096 -- a filter with far more
            survivors per unit of line, so it weighs candidate throughput
            and the survivor path where the others weigh line.

The reported rate is END-TO-END line of the term per second (x/s), the
quantity the hunt is paid in, divided by 1e6 for the SCORE.

A FIND MOVES A CAMPAIGN SHAPE'S REASON TO EXIST, NOT ITS FINGERPRINT: the
shapes name their index, and an index's form list never changes.  When a
campaign is resumed at an index with no shape, add one (and log it).

Frozen 2026-10-23 on engine v1 and planner p1 (OPTIMIZATION_LOG.md round 0):
every fingerprint is the first run's survivor count and xor, taken after G9
pinned the engine's stream to the CPU engine's.  Nothing has been optimized
on this project yet; the next session's rounds measure under these shapes.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import cyclotomic_gpu as cgpu                                   # noqa: E402
import cyclotomic_model as cmodel                               # noqa: E402
import cyclotomic_reference as cref                             # noqa: E402
import cyclotomic_search as csearch                             # noqa: E402
from cyclotomic_gpu import GpuEngine                            # noqa: E402

KNOWN = cref.KNOWN

# label, family, n, p1, p2, p3, q2, j0, blocks, residues, expected count,
# xor, unit, nu, pb, prp, launches
#
# `pb`, `nu` and (SHAPE_TCHUNK) `tchunk` are PINNED per shape, deliberately
# (pb on a campaign shape is the width the planner derives at that opening,
# tchunk and nu the launch decomposition it derives there, recorded when the
# shape is frozen): leaving any of them free would let a launch-size sweep or
# a guard move the benchmark's own window.  `blocks` sweeps whole wheel
# periods from period j0.  `residues` is the first `residues` third-level
# residues of the segment that starts at period j0 (a multiple of nu), and
# `launches` the first `launches` launches of that segment at the pinned
# decomposition -- the campaign shapes' denomination.  An expected count of
# None is a shape not yet frozen: score.py prints what it got and scores 0.
_U11 = 2 * 3 * 5 * 7 * 11
_U13 = _U11 * 13
_U60 = _U13 * 31 * 61
_U72 = 2 * 3 * 5 * 7 * 13 * 19 * 37 * 73
_U84 = 2 * 3 * 5 * 7 * 13 * 29 * 43
_U90 = 2 * 3 * 7 * 11 * 19 * 31
_U96 = 2 * 3 * 5 * 7 * 13 * 17 * 97
_W210 = 210 * 11 * 13 * 17 * 19 * 23
# The launches a campaign shape takes per run: 16 launches is 1.5-2 s at
# every campaign filter, and the whole battery has to fit CLAUDE.md rule 0's
# five minutes.  The first launch of a sweep is unpipelined (the engine
# enqueues one launch ahead), so a shape's rate reads a few percent under a
# steady-state A/B's; the paired ratio is the record (OPTIMIZATION.md Rule 4).
SHAPE_LAUNCHES = 16
SHAPES = [
    # the day-long filter: the a(13) line opens at a(12), whose model median
    # is 3.2e22, so the shape stands there
    ("SCORE",   "A070737", 13, None, None, None, None, None, None, None,
     None, None, _U13, None, None, 6, SHAPE_LAUNCHES),
    ("S11",     "A070737", 11, None, None, None, None, None, None, None,
     None, None, _U11, None, None, 6, SHAPE_LAUNCHES),
    ("S12",     "A070737", 12, None, None, None, None, None, None, None,
     None, None, _U13, None, None, 6, SHAPE_LAUNCHES),
    ("D60",     "A072942", 60, None, None, None, None, None, None, None,
     None, None, _U60, None, None, 6, SHAPE_LAUNCHES),
    ("D72",     "A072942", 72, None, None, None, None, None, None, None,
     None, None, _U72, None, None, 6, SHAPE_LAUNCHES),
    ("D84",     "A072942", 84, None, None, None, None, None, None, None,
     None, None, _U84, None, None, 6, SHAPE_LAUNCHES),
    ("D90",     "A072942", 90, None, None, None, None, None, None, None,
     None, None, _U90, None, None, 6, SHAPE_LAUNCHES),
    ("D96",     "A072942", 96, None, None, None, None, None, None, None,
     None, None, _U96, None, None, 6, SHAPE_LAUNCHES),
    # THE PLANNER-p2 WHEELS OF n = 60, 72, 84 AND 96, named explicitly: the
    # shapes above moved with planner p3 (the measured wheels, round 2), so
    # these keep the p2 workload and its fingerprint alive beside them --
    # a wheel the campaign no longer runs, enumerating the same line by a
    # different CRT, and an engine that reproduces both (OPTIMIZATION.md
    # Rule 4: a plan that moves is a new shape, frozen beside the old one)
    ("D60p2",   "A072942", 60, [17, 19, 23, 29], [37, 41, 43], [71, 73],
     8192, None, None, None, None, None, _U60, 1, 256, 6, SHAPE_LAUNCHES),
    ("D72p2",   "A072942", 72, [11, 17, 23, 29, 31], [41, 43], [61, 67],
     8192, None, None, None, None, None, _U72, 1, 256, 6, SHAPE_LAUNCHES),
    ("D84p2",   "A072942", 84, [11, 17, 19, 23, 31], [37, 41, 61], [71, 73],
     8192, None, None, None, None, None, _U84, 1, 256, 6, SHAPE_LAUNCHES),
    ("D96p2",   "A072942", 96, [11, 19, 23, 29, 31], [37, 41, 43], [61, 73],
     8192, None, None, None, None, None, _U96, 1, 256, 6, SHAPE_LAUNCHES),
    ("SCORE2L", "A070737", 9, 13, 23, None, 65536, 600, 24, None,
     14, 1151007804, 210, None, 224, 0, None),
    ("SCORE1L", "A070737", 9, 13, None, None, 65536, 600 * 7429,
     24 * 7429, None, 14, 1151007804, 210, None, 224, 0, None),
    ("SCORE6",  "A072942", 12, 13, None, None, 4096, 3330003, 40000,
     None, 757, 101633636300, 2730, None, 224, 0, None),
]

# The heights the campaign shapes stand at: the model's median of the
# index's floor (a(12) for the a(13) filter) or the frontier term itself;
# x = 3 is where every A072942 index opens, and its day-long shapes stand at
# the first segment, where the campaign spends its first hours.
_HEIGHTS = {"SCORE": None, "S11": KNOWN["A070737"][10], "S12": None}

# THE FROZEN FINGERPRINTS of the campaign shapes: (count, xor), frozen
# 2026-10-23 on engine v2 / planner p2 (OPTIMIZATION_LOG.md round 1) after
# G9 pinned the stream to the CPU engine's and every round's A/B arms
# returned the identical stream.  The round-0 (engine v1, planner p1)
# readings of the same shapes are in BENCHMARKS.md; where the plan moved
# (SCORE and S12 to 160 periods, SCORE and D90 to the launch size the tail
# queue guard leaves) the v1 fingerprint is a different workload and is
# recorded there, not here.  A shape without an entry prints its
# fingerprint and scores 0.
FROZEN = {
    "SCORE": (1530, 77074378752480246796742),
    "S11": (13412, 1777963672041623798),
    "S12": (5265, 2793084704459754875646),
    # D60, D72, D84 and D96 moved to the measured wheels with planner p3
    # (2026-10-24, round 2); their p2 workloads keep their fingerprints as
    # the explicit D60p2 / D72p2 / D84p2 / D96p2 shapes
    "D60p2": (5447, 617956020680209447729626),
    "D72p2": (6622, 509999702468430256332460),
    "D84p2": (3916, 357856295057912534942206),
    "D90": (2208, 28381702166265587180224),
    "D96p2": (7056, 2232459242012039507890966),
    # the measured wheels (planner p3), frozen 2026-10-24 after the exact
    # sieve-stream parity of each wheel's campaign engine against the CPU
    # engine on 509-863 launches at the production depth and the CPU
    # re-derivation of every survivor the A/B emitted (round 2)
    "D60": (5500, 513110205094724911442778),
    "D72": (3668, 48140159372603435368684),
    "D84": (3143, 289269573103394776183992),
    "D96": (6383, 235076235038982124538322),
}
# THE SHAPES THAT NAME A PAST PLAN'S WHEEL, kept beside the live shape of the
# same index so its fingerprint survives a plan that moved (OPTIMIZATION.md
# Rule 4).  They are not the campaign's configuration and the launcher's
# families-stay-apart drill, which holds every other campaign shape to the
# plan (CLAUDE.md 5g), skips exactly these -- and requires the live shape
# of the same index to be present.
PAST_PLAN_SHAPES = {"D60p2": "D60", "D72p2": "D72", "D84p2": "D84",
                    "D96p2": "D96"}
# ... and the WINDOW AND LAUNCH DECOMPOSITION each was frozen at, (tchunk,
# nu, pb): the planned engine's at the time.  A shape with no entry takes
# the plan's and prints it; a planner or guard that later moves the width
# or the decomposition does not move a frozen shape's window (a plan that
# moves is a new shape, frozen beside the old one with the paired ratio in
# BENCHMARKS.md -- OPTIMIZATION.md Rule 4).
SHAPE_TCHUNK = {
    "SCORE": (7296, 1, 160),
    "S11": (466816, 1, 256),
    "S12": (29056, 1, 160),
    "D60p2": (13696, 1, 256),
    "D72p2": (219776, 1, 256),
    "D84p2": (5888, 1, 256),
    "D90": (7424, 1, 256),
    "D96p2": (8704, 1, 256),
    # the measured wheels' decompositions (planner p3): the tail-queue
    # guard sizes these launches, at half the planned candidates each
    "D60": (105728, 1, 256),
    "D72": (90880, 1, 256),
    "D84": (48000, 1, 256),
    "D96": (3200, 1, 256),
}


def _campaign_row(row):
    """Resolve a campaign shape's None fields to the PLAN at its opening:
    the planned wheel, depth and window, and its height."""
    (label, fam, n, p1, p2, p3, q2, j0, blocks, residues, count, xor,
     unit, nu, pb, prp, launches) = row
    import launch as _launch
    want_unit, pp1, pp2, pp3, pq2, ppb = _launch.plan_for(fam, n)
    if unit != want_unit:
        raise ValueError(f"{label}: the shape names unit {unit} and the plan "
                         f"{want_unit} at {fam} n = {n}")
    p1, p2, p3 = pp1, pp2, pp3
    q2 = pq2 if q2 is None else q2
    if label in SHAPE_TCHUNK:
        _t, fnu, fpb = SHAPE_TCHUNK[label]
        nu = fnu if nu is None else nu
        pb = fpb if pb is None else pb
    pb = ppb if pb is None else pb
    if count is None and label in FROZEN:
        count, xor = FROZEN[label]
    return (label, fam, n, p1, p2, p3, q2, j0, blocks, residues, count, xor,
            unit, nu, pb, prp, launches)


def _height(label, fam, n):
    """Where a campaign shape's segment starts, in x."""
    if label in _HEIGHTS and _HEIGHTS[label] is not None:
        return int(_HEIGHTS[label])
    if cref.per_index(fam):
        return cref.X_MIN
    return int(cmodel.plan_floor(fam, n))


def launch_candidates(eng, li):
    """The candidates of launch `li` (1-based) of a segment, in the
    engine's own order (GpuEngine._sweep: third-level chunks outer,
    first-level chunks inner), the partial last chunks counted as what
    they hold."""
    ui, ti = divmod(li - 1, eng.n_tchunks)
    u0, t_lo = ui * eng.nu, ti * eng.tchunk
    nu_l = min(eng.nu, eng.R3 - u0)
    nt = min(eng.tchunk, eng.R1 - t_lo)
    return nt * eng.R2 * nu_l * eng.pv


def work_for(eng, j0, blocks, residues, launches=None):
    """The benchmark's work function for one shape: a callable returning the
    sorted survivors, plus the line it covers and the units it is counted in."""
    if residues is None and launches is None:
        line = blocks * eng.W

        def work():
            return eng.survivors_j(j0, j0 + blocks)
        return work, line, blocks, eng.R
    if launches is not None:
        if launches > eng.launches_per_segment:
            raise ValueError(f"{launches} launches: a segment is "
                             f"{eng.launches_per_segment} launches")
        # the EXACT candidates of those launches, not launches x
        # cand_per_launch: the last first-level chunk of every third-level
        # residue is partial (305 of 90,880 residues on the measured n = 72
        # wheel), and a full launch's worth charged to it overstated that
        # shape's rate 1.2x (round 2; the trap decimal-ladders found)
        nl, per_unit = int(launches), 1
        units = sum(launch_candidates(eng, li) for li in range(1, nl + 1))
    else:
        if residues > eng.R3 or residues % eng.nu:
            raise ValueError(f"{residues} third-level residues: a segment "
                             f"holds {eng.R3} and a launch {eng.nu}, so the "
                             f"count must be a multiple of {eng.nu} up to "
                             f"{eng.R3}")
        per_unit = eng.R1 * eng.R2 * eng.seg_periods
        nl = (residues // eng.nu) * eng.n_tchunks    # launches to take
        units = residues
    line = units * per_unit / eng.density()

    def work():
        out = []
        k_min = csearch.k_floor(eng.q2, eng.n, eng.fam) + 1
        it = eng.sweep(j0, j0 + eng.seg_periods,
                       k_min=k_min if j0 * eng.W <= k_min else None)
        for i, (_, _, sv) in enumerate(it):
            out.extend(sv)
            if i + 1 >= nl:
                break
        it.close()
        return sorted(out)
    return work, line, units, per_unit


def engine_for(row):
    """The engine a shape names, exactly as it names it -- the launch
    decomposition it was frozen at included (SHAPE_TCHUNK)."""
    (label, fam, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, nu, pb,
     prp, _launches) = row
    tchunk = SHAPE_TCHUNK[label][0] if label in SHAPE_TCHUNK else None
    return GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit, nu=nu,
                     pb=pb, prp=prp, seg_cap=pb if prp else None,
                     tchunk=tchunk)


def resolved_shapes():
    """Every shape with its plan, height and launch decomposition resolved:
    a campaign shape sweeps the first launches of the segment at its
    height, as many third-level residues as one launch holds times the
    launches that fit the benchmark's budget."""
    out = []
    for row in SHAPES:
        row = _campaign_row(row) if row[3] is None else row
        (label, fam, n, p1, p2, p3, q2, j0, blocks, residues, count, xor,
         unit, nu, pb, prp, launches) = row
        if count is None and label in FROZEN:
            count, xor = FROZEN[label]       # an explicit shape's fingerprint
        if j0 is None:
            eng = engine_for(row)
            j0 = _height(label, fam, n) // eng.W
            # the decomposition the shape stands at: frozen, or the plan's
            # (printed with the fingerprint, to be frozen beside it)
            if label not in SHAPE_TCHUNK:
                print(f"  ({label}: decomposition NOT FROZEN -- the plan's is "
                      f"tchunk={eng.tchunk}, nu={eng.nu}, pb={eng.pb}; freeze "
                      f"it in SHAPE_TCHUNK)")
            nu = eng.nu
            del eng
        out.append((label, fam, n, p1, p2, p3, q2, j0, blocks, residues,
                    count, xor, unit, nu, pb, prp, launches))
    return out


def main():
    gates = (cref.GATES + csearch.GATES + cgpu.GATES + cmodel.GATES
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
    for row in resolved_shapes():
        (label, fam, n, p1, p2, p3, q2, j0, blocks, residues,
         count, xor, unit, nu, pb, prp, launches) = row
        eng = engine_for(row)
        work, line, units, per_unit = work_for(eng, j0, blocks, residues,
                                               launches)
        got = work()                                    # warm on the window
        g = 0
        for v in got:
            g ^= int(v)
        if count is None:
            print(f"  ({label}: NOT FROZEN -- first run gives count={len(got)} "
                  f"xor={g}; freeze it in FROZEN and log it)")
            ok_all = False
            continue
        runs = 3 if units * per_unit > 10 ** 10 else 5
        rate_units, ok = scoring.fingerprint_benchmark(
            work, units, count, xor, runs=runs, sync=sync)
        if not ok:
            print(f"  ({label}: got count={len(got)} xor={g})")
            ok_all = False
            continue
        rate_k = rate_units * line / units
        if not isinstance(p1, int):
            wheel = "{" + ",".join(str(q) for q in
                                   cgpu._wheel_primes(p1, p2, p3)) + "}"
        else:
            wheel = (f"<={p1}" if not p2 else
                     f"({p1}],({p2}],({p3}]" if p3 else f"({p1}],({p2}]")
        if unit > 1:
            wheel += f" in the class {eng.r0} (mod {unit})"
        t = cref.letter(fam)
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
