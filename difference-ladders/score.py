"""score.py -- gates x fingerprinted benchmark for difference-ladders.

Prints a SCORE only if every correctness gate is green AND every frozen
benchmark shape reproduces its work fingerprint exactly (survivor count +
xor checksum of the surviving terms).  An engine that skips work fails the
fingerprint; an engine that breaks the mathematics fails the gates.  Either
way it scores nothing.  Optimize under the score, never around it.

THE HEADLINE SITS AT A DAY-LONG FILTER (CLAUDE.md 3b), and there is a shape
at every opening the launcher has (5g).  Each campaign shape is the PLANNED
configuration there, resolved from the plan (wheel, depth, window) with the
launch decomposition pinned (SHAPE_TCHUNK) so that a tuning pass cannot
move a benchmark's window, and each with the DEVICE FERMAT STAGE on (the
launcher's prp_count: 5 forms on both families) -- the stream the
campaign classifies.  Each stands at an EXPLICIT height (frozen with it):

  SCORE   A216666 n = 11   the filter whose term the model puts at a month
                           (a(11) median 3.2e21, ~29 days at the survey's
                           rate): b = 3e21, inside that search
  D24     A216668 n = 24   its day-long filter (a(24) median 2.8e19,
                           p = 89 joins the sieved forms): b = 3e19
  S9      A216666 n = 9    the OPENING, from a(8) = 5.58e10
  S10     A216666 n = 10   the first promotion, at a(9)'s median (3.7e15)
  D18     A216668 n = 18   the OPENING, from a(17) = a(11) = 2.89e11 (the
                           free terms); n = 19..23 sieve the same forms

          Denominated in LAUNCHES of one SEGMENT, the segment that holds
          the shape's height (so the Fermat stage runs at the limb counts
          the campaign does), at a PINNED launch decomposition: the first
          SHAPE_LAUNCHES launches are a FIXED set of candidates that no
          later planner or guard can move.

and three anchors that belong to no campaign (the sieve stream, no Fermat
stage):

  SCORE2L A216666 n = 9: the TWO-level wheel (13],(23] over 24 of ITS
          periods (W = 2.2e8), and
  SCORE1L the ONE-level wheel (primes to 13) over the IDENTICAL absolute
          window, sweeping 24 x (17*19*23 = 7429) periods.  It must return
          the IDENTICAL fingerprint: two wheels enumerating the same
          candidates by different arithmetic, so a bug in the CRT lift
          shows up here as a mismatch inside the benchmark itself.
  SCORE6  A216668 n = 6, one-level wheel to 13, sieve 4096 -- a filter with
          far more survivors per unit of line, so it weighs candidate
          throughput and the survivor path where the others weigh line.

The reported rate is END-TO-END line of the term per second (b/s), the
quantity the hunt is paid in, divided by 1e6 for the SCORE.

Frozen 2026-11-23 on engine v1 and planner p1 (OPTIMIZATION_LOG.md round 0):
every fingerprint is the first run's survivor count and xor, taken after G9
pinned the engine's stream to the CPU engine's.  The campaign shapes
re-frozen the same day on engine v2 / planner p2 (round 1: a different
sieve set, so a different stage stream), and every campaign shape timed by
the EXACT-LAUNCH protocol (work_for's max_launches) since then.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling, certificate                        # noqa: E402
from huntlib import scoring                                     # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
import difference_gpu as dgpu                                   # noqa: E402
import difference_model as dmodel                               # noqa: E402
import difference_reference as dref                             # noqa: E402
import difference_search as dsearch                             # noqa: E402
from difference_gpu import GpuEngine                            # noqa: E402

KNOWN = dref.KNOWN

# The launches a campaign shape takes per run: 16 launches is a second or
# two at every campaign filter, and the whole battery has to fit CLAUDE.md
# rule 0's five minutes.  The first launch of a sweep is unpipelined (the
# engine enqueues one launch ahead), so a shape's rate reads a few percent
# under a steady-state A/B's; the paired ratio is the record.
SHAPE_LAUNCHES = 16

# label, family, n, p1, p2, p3, q2, j0, blocks, residues, expected count,
# xor, unit, nu, pb, prp, launches, campaign
#
# A row with p1 None is a CAMPAIGN shape: its wheel, depth and window are
# the launcher's plan at that filter (resolved here; the launcher's
# families-stay-apart drill holds them to it), its height is _HEIGHTS, and
# `launches` are the first launches of the segment there.  The anchors name
# everything and sweep `blocks` whole wheel periods from period j0.  An
# expected count of None is a shape not yet frozen: score.py prints what it
# got and scores 0.
SHAPES = [
    ("SCORE",   "A216666", 11, None, None, None, None, None, None, None,
     None, None, 1, None, None, 5, SHAPE_LAUNCHES, True),
    ("D24",     "A216668", 24, None, None, None, None, None, None, None,
     None, None, 1, None, None, 5, SHAPE_LAUNCHES, True),
    ("S9",      "A216666", 9, None, None, None, None, None, None, None,
     None, None, 1, None, None, 5, SHAPE_LAUNCHES, True),
    ("S10",     "A216666", 10, None, None, None, None, None, None, None,
     None, None, 1, None, None, 5, SHAPE_LAUNCHES, True),
    ("D18",     "A216668", 18, None, None, None, None, None, None, None,
     None, None, 1, None, None, 5, SHAPE_LAUNCHES, True),
    ("SCORE2L", "A216666", 9, 13, 23, None, 65536, 600, 24, None,
     None, None, 1, None, 224, 0, None, False),
    ("SCORE1L", "A216666", 9, 13, None, None, 65536, 600 * 7429,
     24 * 7429, None, None, None, 1, None, 224, 0, None, False),
    ("SCORE6",  "A216668", 6, 13, None, None, 4096, 3330003, 400,
     None, None, None, 1, None, 224, 0, None, False),
]

# The heights the campaign shapes stand at, FROZEN with them: the opening
# filters at their floors (the frontier terms), the promotion at the model's
# median of its floor, the day-long filters inside their searches.
_HEIGHTS = {"SCORE": 3 * 10 ** 21,
            "D24": 3 * 10 ** 19,
            "S9": KNOWN["A216666"][8],
            "S10": 37 * 10 ** 14,
            "D18": KNOWN["A216668"][11]}

# THE FROZEN FINGERPRINTS: (count, xor), frozen 2026-11-23 on engine v1 /
# planner p1 with the device Fermat stage on PRP_FORMS = 5 forms (the
# measured setting, OPTIMIZATION_LOG.md round 0), after G9 pinned the sieve
# stream to the CPU engine's and G23 the stage to the CPU Fermat chain; two
# runs each, identical.  A shape without an entry prints its fingerprint
# and scores 0.
#
# RE-FROZEN 2026-11-23 for ENGINE v2 / PLANNER p2 (OPTIMIZATION_LOG.md round
# 1), the campaign shapes only: v2 sieves a different SET of primes (the
# value rule, select_primes at SIEVE_TAU, to 32768), so different values
# reach the Fermat stage and the stage's stream is a different, equally
# correct one -- G24 pins it to the CPU engine sieving the same set and the
# CPU Fermat chain over it.  Three runs each, identical.  The v1 values,
# reproduced exactly by v1's configuration on the v2 code (round 1):
#   SCORE (1965, 3005121492909293006085), D24 (3199, 30921444358059622733),
#   S9 (19004, 157274159624077), S10 (8499, 266833324717289126),
#   D18 (28424, 4413080787833).
# The anchors sieve every prime to their own q2 with no Fermat stage, so
# their streams do not depend on the selection, and they reproduce the v1
# fingerprints unchanged.
FROZEN = {
    "SCORE": (834, 29662494119915843287),
    "D24": (1641, 30553643201573126792),
    "S9": (11238, 134500289900383),
    "S10": (4310, 248479526521910636),
    "D18": (16216, 39174857474391),
    "SCORE2L": (6242, 974192456),
    "SCORE1L": (6242, 974192456),
    "SCORE6": (9549, 100006044018),
}

# ... and the WINDOW AND LAUNCH DECOMPOSITION each campaign shape was
# frozen at, (tchunk, nu, pb): the planned engine's at the time.  A shape
# with no entry takes the plan's and prints it.
SHAPE_TCHUNK = {
    "SCORE": (46592, 1, 256),
    "D24": (4096, 1, 256),
    "S9": (253440, 1, 256),
    "S10": (13696, 1, 256),
    "D18": (164480, 1, 256),
}


def _campaign_row(row):
    """Resolve a campaign shape's None fields to the PLAN at its filter."""
    (label, fam, n, p1, p2, p3, q2, j0, blocks, residues, count, xor,
     unit, nu, pb, prp, launches, camp) = row
    import launch as _launch
    want_unit, pp1, pp2, pp3, pq2, ppb = _launch.plan_for(fam, n)
    if unit != want_unit:
        raise ValueError(f"{label}: the shape names unit {unit} and the plan "
                         f"{want_unit} at {fam} n = {n}")
    if prp != _launch.prp_count(fam):
        raise ValueError(f"{label}: the shape's Fermat stage tests {prp} forms, "
                         f"the campaign's {_launch.prp_count(fam)}")
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
            unit, nu, pb, prp, launches, camp)


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
    if launches > eng.launches_per_segment:
        raise ValueError(f"{launches} launches: a segment is "
                         f"{eng.launches_per_segment} launches")
    # the EXACT candidates of those launches, not launches x cand_per_launch
    nl, per_unit = int(launches), 1
    units = sum(launch_candidates(eng, li) for li in range(1, nl + 1))
    line = units * per_unit / eng.density()

    def work():
        # EXACTLY nl launches (engine v2's max_launches): the sweep stops
        # enqueueing after them and drains what is in flight, so the timer
        # holds those launches and no others.  Breaking off after nl results
        # instead left the launches in flight running into the timer --
        # one under engine v1 (16 + 1 timed for 16 counted), two under v2's
        # three buffers (round 1; BENCHMARKS.md has the paired ratio of the
        # protocol change on its own).
        out = []
        k_min = dsearch.k_floor(eng.q2, eng.n, eng.fam) + 1
        for _, _, sv in eng.sweep(j0, j0 + eng.seg_periods,
                                  k_min=k_min if j0 * eng.W <= k_min else None,
                                  max_launches=nl):
            out.extend(sv)
        return sorted(out)
    return work, line, units, per_unit


def engine_for(row):
    """The engine a shape names, exactly as it names it -- the launch
    decomposition it was frozen at included (SHAPE_TCHUNK)."""
    (label, fam, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, nu, pb,
     prp, _launches, _camp) = row
    _camp = bool(_camp)
    tchunk = SHAPE_TCHUNK[label][0] if label in SHAPE_TCHUNK else None
    # a campaign shape sieves the campaign's SET (select_primes with the
    # value rule, engine v2); an anchor sieves every prime to its q2
    return GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit, nu=nu,
                     pb=pb, prp=prp, seg_cap=pb if prp else None,
                     tchunk=tchunk, select=dgpu.SIEVE_TAU if _camp else None)


def resolved_shapes():
    """Every shape with its plan, height and launch decomposition resolved."""
    out = []
    for row in SHAPES:
        row = _campaign_row(row) if row[3] is None else row
        (label, fam, n, p1, p2, p3, q2, j0, blocks, residues, count, xor,
         unit, nu, pb, prp, launches, camp) = row
        if count is None and label in FROZEN:
            count, xor = FROZEN[label]
        if j0 is None:
            eng = engine_for(row)
            j0 = int(_HEIGHTS[label]) // eng.W
            if label not in SHAPE_TCHUNK:
                print(f"  ({label}: decomposition NOT FROZEN -- the plan's is "
                      f"tchunk={eng.tchunk}, nu={eng.nu}, pb={eng.pb}; freeze "
                      f"it in SHAPE_TCHUNK)")
            nu = eng.nu
            del eng
        out.append((label, fam, n, p1, p2, p3, q2, j0, blocks, residues,
                    count, xor, unit, nu, pb, prp, launches, camp))
    return out


def main():
    gates = (dref.GATES + dsearch.GATES + dgpu.GATES + dmodel.GATES
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
    # THE GATES LEAVE A HEAVY HEAP BEHIND (kill-set caches, survivor lists,
    # dozens of engines' host tables), and Python's cyclic collector then
    # walks all of it every few launches: the shapes measured 2-5x under
    # their fresh-process rates (D18 1.2e12 against 5.9e12 b/s) until the
    # survivors of the gates were frozen out of the collector's view.  The
    # campaign never runs a gate, so this is the benchmark measuring the
    # engine, not a change to it.
    import gc
    gc.collect()
    gc.freeze()
    cp.get_default_memory_pool().free_all_blocks()
    cp.get_default_pinned_memory_pool().free_all_blocks()

    ok_all = True
    for row in resolved_shapes():
        (label, fam, n, p1, p2, p3, q2, j0, blocks, residues,
         count, xor, unit, nu, pb, prp, launches, _camp) = row
        eng = engine_for(row)
        work, line, units, per_unit = work_for(eng, j0, blocks, residues,
                                               launches)
        got = work()                                    # warm on the window
        g = 0
        for v in got:
            g ^= int(v)
        if count is None:
            print(f"  ({label}: NOT FROZEN -- first run gives count={len(got)} "
                  f"xor={g}; tchunk={eng.tchunk} nu={eng.nu} pb={eng.pb}; "
                  f"freeze it in FROZEN and log it)")
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
                                   dgpu._wheel_primes(p1, p2, p3)) + "}"
        else:
            wheel = (f"<={p1}" if not p2 else
                     f"({p1}],({p2}],({p3}]" if p3 else f"({p1}],({p2}]")
        t = dref.letter(fam)
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
