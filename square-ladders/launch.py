"""The campaign for A089761 -- least k with k*i^2+1 prime for i = 1..n.

    python launch.py --selftest      the full gate battery (must end ALL GREEN)
    python launch.py                 the hunt: indefinite, resumable
    python launch.py --to 1e16       stop at a chosen depth on the k line
    python launch.py --status        read the checkpoint and say where it is

WHAT IS OPEN, AND WHY IT IS WORTH A SWEEP.  Fifteen terms are published.
The last FIVE of them are the same integer: Donovan Johnson searched for
a(11) in 2008 and found k = 861,066,640, which then cleared conditions
i = 12, 13, 14 and 15 for free.  The run stops at exactly one composite,

    861066640 * 16^2 + 1 = 220433059841 = 47 * 149 * 31476947,

and that single factorization is the whole reason a(16) is open.  So the
real frontier is much staler than "fifteen terms" suggests: a(11) in 2008
is the last term anybody searched for, and the only work since is Max
Alekseyev's searched-empty bound a(16) > 1.4e13.

THE CLAIM'S FLOOR IS FREE.  a() is non-decreasing (the conditions nest), so
a(16) >= a(15) = 861,066,640 by definition and nothing below that has to be
swept at all.  The campaign still starts far below it: at ~1.2e15 k/s the
whole of Alekseyev's range is under a tenth of a second, so this hunt re-derives his
bound independently before it reaches new ground, and the least-claim rests
on our own coverage rather than on a citation.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine's enforced ceiling -- since v4 the PRIMALITY-TEST validity
bound k_ceil(n) (1.02e22 at n = 18), not a machine word -- which is the
last rung.
`--to` and `--stop-on-discovery` are the only stops and both are opt-in.
Progress is read off RUNGS taken from the odds model's quantiles, logged as
they are passed and shown with an ETA in every [STATUS].  A rung retires
with its term: the ladder is derived from the LIVE frontier on every use.

THE TAXONOMY, mapped to this problem (CONVENTIONS.md "the discovery
protocol").  A survivor is a k with a run length r:

  DISCOVERY  r > frontier: it settles a(frontier+1) ... a(r) at once, each
             logged once, all evidenced under the FIRST value they belong
             to.  Verified three ways plus a factor witness for the
             composite that stops the run.
  NEAR       r == frontier: a k that reaches the settled frontier and no
             further -- ONE condition short of the open term.  One line
             with its campaign ordinal, verified by the cheap legs as an
             engine health check, never evidenced.
  CENSUS     CENSUS_FLOOR <= r < frontier: counted in [STATUS], never
             narrated.
  None       r < CENSUS_FLOOR: noise, not counted.

LOAD (CONVENTIONS.md "Sizing a hunt so it leaves the machine usable").
This hunt has NO host worker pool, by construction rather than omission,
and v5 is what made that stay true.  The device does the whole sieve; the
host classifies survivors, and that is about 33 of them per launch, each a
handful of Miller-Rabin tests -- 2.6 ms against a 32 ms launch, or 8% of a
core.  At the v4 rate it was 2%; the engine got 4.3x faster and the share
would have grown with it, so the work was moved OFF the critical path
instead of being given cores: the engine enqueues the next launch before
handing back the survivors of the last one, and the classification runs
against a busy device.  MEASURED at 0.0% of the rate, paired, with the
device flush that makes it real (sqladder_gpu, "FLUSH").  So there is
still nothing to ramp and no core count to size.  The throttles that exist
are `--gpu-yield-ms` and `--gentle`, both priced in the help text against
the half-second checkpoint interval -- see CKPT_LAUNCHES, which is set to
hold that DURATION fixed as the engine gets faster, precisely so those
prices stay true.  No machine setting is ever changed on the owner's
behalf.
"""

import argparse
import json
import math
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from huntlib import certificate, checkpoint, drills, evidence   # noqa: E402
from huntlib import shutdown                                    # noqa: E402
from huntlib.gpu import device_report                           # noqa: E402
from huntlib.hlog import Heartbeat, banner, census_str, log     # noqa: E402
from huntlib.primes import factor_witness, mr_is_prime          # noqa: E402
from huntlib.rungs import Ladder, eta_str                       # noqa: E402

import sqladder_gpu as gpu                                      # noqa: E402
import sqladder_model as model                                  # noqa: E402
import sqladder_reference as ref                                # noqa: E402
import sqladder_search as cpu                                   # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CKPT = str(HERE / "campaign_checkpoint.json")
EVID = str(HERE / "evidence")
LEDGER = str(HERE / "evidence" / "a089761_discoveries.json")
MODEL_JSON = str(HERE / "model_results.json")

P1 = gpu.P1_DEFAULT               # first-level wheel: primes 2..23
P2 = gpu.P2_DEFAULT               # second-level wheel: primes (23, 37]
P3 = gpu.P3_DEFAULT               # third-level wheel:  primes (37, 47]
Q2 = cpu.Q2_DEFAULT               # sieve depth
# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches.
#
# v5's wheel changed what a "segment" can mean.  With three levels the
# candidates of a wheel period come out in (t, s, u) order and not in k
# order, so only a WHOLE PERIOD is contiguous in k -- and a period is now
# 6.15e17 of line and about ten minutes of device.  Those are two different
# quantities and the launcher tracks both:
#
#   COVERAGE advances one period at a time.  `boundary`, the k below which
#   the line is swept, only moves at a period end, and a discovery is only
#   the LEAST k once its period is finished.  That costs at most one period
#   of over-sweep at a find, against a wheel worth 3.5x -- at the a(18)
#   frontier, ten minutes against hours.
#   WORK is resumable per launch.  The cursor is (j, u) and a crash costs
#   one checkpoint interval, not one period, which is what rule 5d asks.
#
# 16 launches is about half a second at the v5 rate, which is the same
# segment DURATION the old SEG_BLOCKS was chosen to hold, and for the same
# reasons: it is what an interrupt costs to redo and it is the denominator
# that prices --gpu-yield-ms (20 ms is 4% of it, 40 ms is 8%).
CKPT_LAUNCHES = 16
K_START = 10 ** 6                 # above max(K_FLOOR, Q2); see the docstring
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
ENGINE_VERSION = "v5"

CONFIG_KEY = (f"a089761-{ENGINE_VERSION}-p1{P1}-p2{P2}-p3{P3}-q2{Q2}-"
              f"seg{CKPT_LAUNCHES}")
# Engine versions whose swept line this one inherits.  v4 changed the
# REPRESENTATION (k as (base, off) instead of a u64) and nothing about
# which k are covered: same wheel, same sieve depth, and G9/G15 plus the
# four frozen benchmark fingerprints pin the survivor stream as identical.
# A change to the WHEEL or the SIEVE DEPTH does not belong here -- those
# move coverage, and the key must break.  v5 changed the wheel, so nothing
# is inherited and this is deliberately EMPTY.
INHERITS = ()
# Derived from the SAME live constants as CONFIG_KEY, so a wheel or sieve
# change rebuilds both and the old cursor stops being inherited on its own.
# That is the whole safety argument, so it is asserted rather than trusted:
# an entry here may differ from CONFIG_KEY in the VERSION FIELD ONLY.  A
# hardcoded key that survived a constant change would silently adopt a
# cursor covering different line, which is the one failure this guard
# exists to prevent.
for _old in INHERITS:
    if (_old.split("-")[2:] != CONFIG_KEY.split("-")[2:]
            or _old.split("-")[0] != CONFIG_KEY.split("-")[0]):
        raise ValueError(
            f"INHERITS entry {_old!r} differs from {CONFIG_KEY!r} in more "
            f"than the engine version: a cursor may only be inherited "
            f"across a change that covers the identical k line")

# RE-DENOMINATION is the other thing, and it is NOT inheritance.  v5's wheel
# is (23,47] where v4's was (23,37], so the two do not enumerate the same
# candidates and no fingerprint pins them together -- INHERITS would be a
# lie.  What DOES carry across a wheel change is the plain arithmetic claim
# the old checkpoint makes: "every k below this one has been swept".  So the
# old cursor's k is adopted, floored to the new period (never rounded up --
# that would leave a GAP), and the overlap is re-swept.
#
# Re-sweeping is not free of consequences and both are handled: the census
# counts would be inflated by counting the same values twice, so `census
# _floor` suppresses counting below the old cursor; and a DISCOVERY-grade
# run down there would mean the two wheels disagree about line one of them
# has already cleared, so it raises an ALARM instead of being recorded.
# That makes the re-sweep a free cross-check between the v4 and v5 wheels
# over one wheel period of line.
REDENOMINATE = (f"a089761-v4-p1{P1}-p2{P2}-q2{Q2}-seg14",
                f"a089761-v3.4-p1{P1}-p2{P2}-q2{Q2}-seg14")


# ------------------------------- the taxonomy -------------------------------

def event_kind(run, frontier):
    """DISCOVERY / NEAR / CENSUS / None -- the repo-wide rule, this
    project's mathematics.  `frontier` is the largest n already settled."""
    run, frontier = int(run), int(frontier)
    if run > frontier:
        return "DISCOVERY"
    if run == frontier:
        return "NEAR"
    if run >= CENSUS_FLOOR:
        return "CENSUS"
    return None


def verify(k, run, frontier):
    """The three independent confirmations plus the bounding witness.

    1. huntlib's Miller-Rabin, which is a PROOF here (G10: every value in
       the enforced range is under the deterministic bound);
    2. sympy's BPSW, an independent implementation;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, on a DIFFERENT wheel from the campaign's, must agree that
       this k survives the sieve.

    plus a factor witness for the composite that STOPS the run, which is
    what bounds the claim to exactly `run`.  Nothing here is unbounded:
    the witness is trial division then a bounded rho then bounded ECM.
    """
    legs = {"mr_chain": all(mr_is_prime(ref.value(k, i))
                            for i in range(1, run + 1)),
            "sympy_bpsw": ref.run_length(k, cap=run + 1) == run,
            "resieve_other_wheel": cpu.CpuEngine(run, q2=4096).survives(k)}
    stop = ref.value(k, run + 1)
    legs["stopper_composite"] = not mr_is_prime(stop)
    ok = all(legs.values())
    wit = factor_witness(stop) if legs["stopper_composite"] else None
    return ok, legs, {"i": run + 1, "value": stop, "factor": wit}


# --------------------------------- campaign ---------------------------------

class Campaign:
    def __init__(self, args):
        self.args = args
        self.found = {}                # str(n) -> k found by THIS campaign
        self.census = {}               # run length -> count
        self.passed = []
        self.elapsed = 0.0
        self.discoveries = 0
        self.near = 0
        self.j = None
        self.u = 0                     # third-level cursor inside a period
        self.census_floor = 0          # k below which values are not counted
        self.pending = []              # classified, not yet narrated
        self._resume_k = 0             # set by a re-denomination
        self.hb = Heartbeat(interval=args.heartbeat)
        self._t0 = time.time()
        self.load()
        # `discoveries` is CUMULATIVE over the campaign and is restored by
        # load(), so "have there been any finds" is not the same question as
        # "has THIS RUN found something" the moment a resumed campaign has
        # any history.  --stop-on-discovery means the second one; with the
        # a(16)/a(17) cursor loaded it read the first and stopped on the
        # opening segment, having found nothing.
        self._discoveries_at_start = self.discoveries
        self.eng = gpu.GpuEngine(self.filter_n(), p1=P1, p2=P2, p3=P3,
                                 q2=Q2)
        if self._resume_k:
            # FLOOR, never round up: the new period containing the old
            # cursor is re-swept so that no k is left uncovered between the
            # two wheels.  Nothing below the old cursor is counted again.
            self.j = self._resume_k // self.eng.W
            self.u = 0
            self.census_floor = self._resume_k
            log("STAGE",
                f"cursor RE-DENOMINATED onto the v5 wheel: k = "
                f"{self._resume_k:,} floors to period j = {self.j:,} "
                f"(k = {self.j * self.eng.W:,}); "
                f"{self._resume_k - self.j * self.eng.W:.4g} of line is "
                f"re-swept as a cross-check and is NOT counted again")
        if self.j is None:
            self.j = K_START // self.eng.W + 1
        self.boundary = self.j

    # ----------------------------------------------------------- frontiers
    def frontier(self):
        """The largest n settled: published, promoted by our own finds."""
        f = max(ref.KNOWN)
        for n in self.found:
            f = max(f, int(n))
        return f

    def filter_n(self):
        """The sieve filter is always the next OPEN term."""
        return self.frontier() + 1

    def frontier_k(self):
        base = ref.KNOWN[max(ref.KNOWN)]
        for n, k in self.found.items():
            base = max(base, int(k))
        return base

    # --------------------------------------------------------------- rungs
    def ladder(self):
        ceil = cpu.k_ceil(self.filter_n())
        preds = model.predictions(self.frontier(), self.frontier_k(),
                                  n_ahead=3, ceiling=ceil)
        return Ladder.from_predictions(
            preds, ceiling=ceil,
            ceiling_label=f"engine ceiling {ceil:.3g}")

    def next_rung(self, k):
        live = self.ladder().live(self.frontier())
        for term, lab, d in live:
            if d > k:
                return lab, d
        return None

    def check_rungs(self, k):
        for term, lab, d in self.ladder().live(self.frontier()):
            if d <= k and lab not in self.passed:
                self.passed.append(lab)
                nxt = self.next_rung(k)
                log("RUNG", f"passed {lab} (k = {d:.4g})" +
                    (f" -- next: {nxt[0]} at {nxt[1]:.4g}" if nxt else ""))

    # ---------------------------------------------------------- checkpoint
    def save(self, why=""):
        st = {"key": CONFIG_KEY,
              "engine": ENGINE_VERSION,
              "j": int(self.boundary),
              "u": int(self.u),
              "W": int(self.eng.W),
              # the COVERAGE claim: every k below this is swept.  It is the
              # period boundary, never the live (j, u) cursor, because a
              # part-swept period is not contiguous in k.
              "k": int(self.boundary) * int(self.eng.W),
              "census_floor": int(self.census_floor),
              # values classified inside the period still in progress.  A
              # crash must not lose them: they are only narrated once the
              # period closes and their k order becomes meaningful, so
              # between those two moments the checkpoint is where they live.
              "pending": [[int(k), int(r)] for k, r in self.pending],
              "found": self.found,
              "census": {str(r): c for r, c in sorted(self.census.items())},
              "passed": self.passed,
              "elapsed": self.elapsed + (time.time() - self._t0),
              "discoveries": self.discoveries,
              "near": self.near,
              "saved": time.strftime("%Y-%m-%d %H:%M:%S")}
        checkpoint.save(CKPT, st)
        return st

    def load(self):
        st = checkpoint.load(CKPT, CONFIG_KEY, warn=lambda m: log("STAGE", m),
                             accept=INHERITS)
        if not st:
            st = self._redenominate()
        if not st:
            return False
        self.j = int(st["j"]) if not self._resume_k else None
        self.u = int(st.get("u", 0))
        self.census_floor = int(st.get("census_floor", 0))
        self.pending = [(int(k), int(r)) for k, r in st.get("pending", [])]
        self.found = dict(st.get("found", {}))
        self.census = {int(r): int(c) for r, c in st.get("census", {}).items()}
        self.passed = list(st.get("passed", []))
        self.elapsed = float(st.get("elapsed", 0.0))
        self.discoveries = int(st.get("discoveries", 0))
        self.near = int(st.get("near", 0))
        return True

    def u_progress(self, jn, un):
        """A k for the HEARTBEAT inside a period -- progress, not coverage.

        Candidates come out in (t, s, u) order, so a part-swept period is
        not contiguous in k and `boundary` cannot move.  The rate and the
        ETA still want to see work happening, and the fraction of the
        period done is exactly that; the status line labels it.
        """
        return int(jn * self.eng.W
                   + self.eng.W * un // max(self.eng.R3, 1))

    def _redenominate(self):
        """Adopt an older wheel's SWEPT-TO k, floored onto this wheel.

        Not inheritance -- see REDENOMINATE.  What carries across is the
        arithmetic claim "every k below this is swept", which is true of
        any correct engine; what does not carry is the cursor `j`, which is
        denominated in a wheel period this configuration does not have.
        """
        for old in REDENOMINATE:
            st = checkpoint.load(CKPT, old, accept=(old,))
            if st and st.get("key") == old:
                self._resume_k = int(st.get("k", 0))
                log("STAGE", f"checkpoint written by {old} adopted: it "
                             f"claims the line swept to k = "
                             f"{self._resume_k:,}")
                return st
        return None

    # ------------------------------------------------------------- status
    def status_line(self):
        k = (self.hb.pos() or self.j * self.eng.W)
        rate = self.hb.rate()
        swept = self.boundary * self.eng.W
        # Two numbers, because they are two claims.  `k` is where the work
        # has got to inside the period; `swept` is the line actually
        # covered, and it only moves when a period closes.
        parts = [f"k = {k:.6g}"]
        if k > swept:
            parts.append(f"swept to {swept:.6g} "
                         f"(period {100.0 * (k - swept) / self.eng.W:.0f}%)")
        parts.append(f"filter n = {self.filter_n()}")
        if rate:
            parts.append(f"{rate:.3g} k/s")
        parts.append(census_str(self.census, CENSUS_FLOOR, self.frontier()))
        parts.append(f"finds {self.discoveries}")
        nr = self.next_rung(k)
        if nr:
            lab, d = nr
            parts.append(f"next {lab} {d:.3g} "
                         f"(ETA {eta_str(d - k, rate) if rate else '?'})")
            p = model.p_by(self.filter_n(),
                           model.floor_for(self.filter_n(), self.frontier_k()),
                           k)
            parts.append(f"P(a({self.filter_n()}) by now) = {100 * p:.0f}%")
        stall = self.hb.stalled()
        if stall:
            parts.append(f"-- no segment closed since the last status: "
                         f"{stall[0]} for {stall[1]:.0f}s")
        return "  ".join(parts)

    # --------------------------------------------------------------- hits
    def handle(self, k, run):
        frontier = self.frontier()
        kind = event_kind(run, frontier)
        if kind is None:
            return
        if k < self.census_floor:
            # Re-swept line from a wheel change (see REDENOMINATE).  It was
            # already counted by the engine that swept it first, so counting
            # it again would inflate the census -- but a DISCOVERY here is
            # not a duplicate, it is two engines disagreeing about line one
            # of them has certified as clear, and that stops the campaign.
            if kind == "DISCOVERY":
                log("ALARM", f"run {run} at k = {k:,} is BELOW the "
                             f"re-denomination floor {self.census_floor:,}: "
                             f"the previous wheel swept this line and did "
                             f"not report it -- the two engines disagree")
                raise SystemExit(2)
            return
        self.census[run] = self.census.get(run, 0) + 1
        if kind == "CENSUS":
            return
        if kind == "NEAR":
            self.near += 1
            ok, legs, _ = verify(k, run, frontier)
            if not ok:
                log("ALARM", f"NEAR value k = {k:,} run {run} failed "
                             f"verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at k = {k:,} (run-{run} #{self.census[run]}"
                        f" of the campaign; verified) -- ONE condition short "
                        f"of a({frontier + 1})!")
            return
        self.record_discovery(k, run)

    def record_discovery(self, k, run):
        frontier = self.frontier()
        self.hb.doing(f"verifying run-{run} k={k}")
        ok, legs, stop = verify(k, run, frontier)
        if not ok:
            log("ALARM", f"claimed a({frontier+1}) = {k} failed the protocol: "
                         f"{legs}")
            raise SystemExit(2)
        settles = list(range(frontier + 1, run + 1))
        certs = {}
        for i in range(1, run + 1):
            v = ref.value(k, i)
            certs[str(i)] = certificate.prove(v)
        ev = {"sequence": "A089761", "k": int(k), "run": int(run),
              "settles": settles,
              "values": {str(i): int(ref.value(k, i))
                         for i in range(1, run + 1)},
              "verification": legs,
              "stopper": {"i": stop["i"], "value": int(stop["value"]),
                          "factor": stop["factor"]},
              "certificates": certs,
              "least_claim": {"swept_from": K_START,
                              "swept_to": int(k),
                              "wheel": int(self.eng.W), "sieve_depth": Q2,
                              "monotone_floor": ref.KNOWN[max(ref.KNOWN)]},
              "engine": CONFIG_KEY}
        for n in settles:
            self.found[str(n)] = int(k)
        path = evidence.record(ev, EVID, f"A089761_a{settles[0]}_{k}.json",
                               LEDGER, key="k",
                               label="A089761 a(%s)" % ",".join(map(str, settles)))
        self.discoveries += 1
        banner("DISCOVERY", [
            f"A089761 a({settles[0]}) = {k:,}" if len(settles) == 1 else
            f"A089761 a({settles[0]})..a({settles[-1]}) = {k:,}",
            f"run {run}: k*i^2+1 is prime for i = 1..{run}",
            f"stopped by k*{stop['i']}^2+1 = {stop['value']:,} "
            f"= {stop['factor']}",
            f"verified 3 ways, {len(certs)} certificates, evidence {path}",
        ])
        old = self.eng
        self.eng = gpu.GpuEngine(self.filter_n(), p1=P1, p2=P2, p3=P3,
                                 q2=Q2)
        log("STAGE", f"filter follows the frontier: n = {old.n} -> "
                     f"{self.eng.n}; the ladder now aims at "
                     f"a({self.filter_n()})")
        # a wider filter is a COARSER wheel in k terms only if W changes;
        # re-denominate the cursor by floor so coverage overlaps, never gaps
        self.j = (int(k) // self.eng.W)
        self.boundary = self.j
        self.passed = [p for p in self.passed
                       if not p.startswith(tuple(f"a({n})" for n in settles))]

    # ---------------------------------------------------------------- loop
    def run(self):
        target = self.args.to or cpu.k_ceil(self.filter_n())
        log("STAGE", f"campaign {CONFIG_KEY}")
        log("STAGE", device_report(self.eng.bytes_held()))
        log("STAGE", f"sweeping the k line to {target:.4g}; filter n = "
                     f"{self.filter_n()}; wheel W = {self.eng.W:,} "
                     f"({self.eng.R:,} residues, "
                     f"{100.0 * self.eng.R / self.eng.W:.3f}% of the line); "
                     f"resume at k = {self.j * self.eng.W:,}")
        for row in model.campaign_board(self.frontier(), self.frontier_k()):
            qs = row["quantiles"]
            log("STAGE", "  a(%d): S = %.4g  Q1 %.3g  median %.3g  Q3 %.3g"
                % (row["n"], row["S"], qs.get("Q1", float("nan")),
                   qs.get("median", float("nan")), qs.get("Q3", float("nan"))))
        self.hb.mark(self.j * self.eng.W)
        self.hb.start(self.status_line)
        shutdown.on_interrupt(self._on_interrupt)
        try:
            while self.j * self.eng.W < target:
                j1 = self.j + 1               # ONE PERIOD: see CKPT_LAUNCHES
                if j1 * self.eng.W > cpu.k_ceil(self.filter_n()):
                    break
                self.hb.doing(f"sieving k in [{self.j * self.eng.W:.4g}, "
                              f"{j1 * self.eng.W:.4g})")
                # Classification runs INSIDE the sweep loop deliberately:
                # the engine enqueues the next launch before handing these
                # survivors over, so this work overlaps the device instead
                # of stalling it (sqladder_gpu, "FLUSH").
                since = 0
                for jn, un, surv in self.eng.sweep(self.j, j1, u_from=self.u):
                    for k in surv:
                        r = self.run_length(int(k), cap=self.filter_n() + 6)
                        if r >= CENSUS_FLOOR:
                            self.pending.append((int(k), r))
                    self.u = un
                    since += 1
                    if since >= CKPT_LAUNCHES and un:
                        since = 0
                        self.hb.mark(self.u_progress(jn, un))
                        self.save()
                    if un == 0:
                        break
                # The period is closed, so its values are contiguous in k
                # again and the LEAST of them is meaningful.  Nothing is
                # narrated before this point.
                for k, r in sorted(self.pending):
                    self.handle(k, r)
                self.pending = []
                self.j = j1
                self.u = 0
                self.boundary = self.j
                self.hb.mark(self.j * self.eng.W)
                self.check_rungs(self.j * self.eng.W)
                self.save()
                if (self.args.stop_on_discovery
                        and self.discoveries > self._discoveries_at_start):
                    log("STAGE", "stopping on discovery (--stop-on-discovery)")
                    break
                if self.args.gpu_yield_ms:
                    time.sleep(self.args.gpu_yield_ms / 1000.0)
        finally:
            self.hb.stop()
        log("STAGE", f"reached k = {self.j * self.eng.W:.6g}; "
                     f"{self.discoveries} discoveries, {self.near} near, "
                     f"{sum(self.census.values())} census")
        self.save("end of run")
        return 0

    # the run-length classifier, borrowed from the CPU engine so the
    # campaign and the parity gate use literally the same code path
    run_length = cpu.CpuEngine.run_length

    def _on_interrupt(self):
        self.save("interrupt")
        return (f"checkpoint written at the last segment boundary: "
                f"k = {self.boundary * self.eng.W:,} ({CKPT})")


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """All four outcomes of the taxonomy, on this project's mathematics."""
    return [((16, 15), "DISCOVERY"),      # beyond the frontier
            ((19, 15), "DISCOVERY"),      # a long run settles several at once
            ((15, 15), "NEAR"),           # one condition short of a(16)
            ((14, 15), "CENSUS"),         # below the frontier: counted only
            ((8, 15), "CENSUS"),          # the census floor itself
            ((7, 15), None),              # under the floor: not even counted
            ((0, 15), None)]


def _canary_hunt():
    """The stream must organically rediscover known terms.

    Three dedicated mini-hunts at the filters those terms belong to.  The
    campaign filter (n = 16) CANNOT rediscover them -- a(8) has run 8 and
    the n = 16 wheel is entitled to kill it -- so a canary in the
    production stream would be a category error here.  Rediscovery is what
    a canary is for, and it is done at the filter each term belongs to.
    """
    for n in (8, 9, 10):
        eng = gpu.GpuEngine(n, p1=13, p2=None, p3=None, q2=4096)
        surv = eng.survivors_k(30031, ref.KNOWN[n] + 1)
        ceng = cpu.CpuEngine(n, q2=4096)
        hits = [int(k) for k in surv
                if ceng.run_length(int(k), cap=n) >= n]
        if not hits or min(hits) != ref.KNOWN[n]:
            return False, (f"CANARY FAIL: filter n={n} found "
                           f"{min(hits) if hits else None}, "
                           f"expected a({n}) = {ref.KNOWN[n]}")
    return True, ("canary ok: the GPU stream rediscovered a(8), a(9) and "
                  "a(10) as FIRST occurrences at their own filters")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions."""
    k = ref.KNOWN[11]
    ok, legs, stop = verify(k, 15, 11)
    if not ok:
        return False, f"PROTOCOL FAIL: genuine run-15 at k={k} rejected: {legs}"
    if stop["i"] != 16 or stop["factor"] is None:
        return False, "PROTOCOL FAIL: no factor witness for the stopper"
    bad, legs_b, _ = verify(k, 16, 11)
    if bad:
        return False, (f"PROTOCOL FAIL: fake run-16 claim at k={k} ACCEPTED "
                       f"({legs_b}) -- the protocol does not reject")
    fake, _lc, _ = verify(ref.KNOWN[10], 15, 11)
    if fake:
        return False, "PROTOCOL FAIL: a(10)'s k accepted as a run-15"
    return True, ("protocol ok: genuine run-15 accepted with a factor "
                  "witness for its stopper, fake run-16 and mislabelled "
                  "a(10) both rejected")


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly.

    Run on BOTH kernels, and the second case is the configuration the
    campaign actually resumes on -- a seam drill that only covers the
    one-level wheel proves nothing about the cursor a real interrupt
    leaves behind.
    """
    total = 0
    for lab, kw, j_at, span, cut in (
            ("one-level", dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 20000, 7500),
            ("two-level", dict(p1=P1, p2=P2, p3=None, q2=Q2),
             10 ** 15, 6, 2),
            ("three-level", dict(p1=13, p2=17, p3=19, q2=128),
             9 * 10 ** 14, 4, 1)):
        eng = gpu.GpuEngine(16, **kw)
        j0 = eng.j_of(j_at)
        whole = eng.survivors_j(j0, j0 + span)
        a = eng.survivors_j(j0, j0 + cut)
        b = eng.survivors_j(j0 + cut, j0 + span)
        split = a + b
        if not whole:
            return False, f"RESUME FAIL: {lab} window is empty -- vacuous"
        if sorted(whole) != sorted(split):
            return False, (f"RESUME FAIL: {lab}: {len(whole)} whole vs "
                           f"{len(split)} split")
        total += len(whole)

    # THE SEAM A REAL INTERRUPT LEAVES is not a period boundary any more.
    # v5's cursor is (j, u) and a resume restarts inside a period, so the
    # drill has to cut THERE: sweeping u in [0, c) then [c, R3) must give
    # the same set as sweeping the period whole.  A drill that only cuts at
    # period boundaries cannot see a broken sub-cursor.
    eng = gpu.GpuEngine(16, p1=13, p2=17, p3=19, q2=128)
    j0 = eng.j_of(9 * 10 ** 14)
    whole = sorted(eng.survivors_j(j0, j0 + 1))
    for cut in (1, 3, eng.R3 - 1):
        part, stopped = [], 0
        for _, un, sv in eng.sweep(j0, j0 + 1):
            part.extend(sv)
            stopped = un
            if un == 0 or un >= cut:
                break
        # resume exactly where the interrupt left the cursor
        if stopped:
            for _, _, sv in eng.sweep(j0, j0 + 1, u_from=stopped):
                part.extend(sv)
        if sorted(part) != whole or not whole:
            return False, (f"RESUME FAIL: the (j, u) seam at u = {stopped} "
                           f"loses or repeats values: {len(part)} vs "
                           f"{len(whole)}")
        total += len(whole)
    return True, (f"resume ok: split sweep == unsplit sweep on all three "
                  f"kernels and across the (j, u) SUB-PERIOD seam a v5 "
                  f"interrupt leaves ({total} survivors across the seams), "
                  f"including the campaign's own wheel")


def _ceiling_drill():
    """The enforced ceilings are enforced, not documented."""
    eng = gpu.GpuEngine(16, p1=23, p2=P2, p3=P3, q2=4096)
    checks = []
    try:
        c = cpu.k_ceil(16)
        eng.survivors_j(c // eng.W, c // eng.W + 10)
    except ValueError:
        checks.append("k_ceil")
    else:
        return False, "CEILING FAIL: k_ceil was not enforced"
    try:
        gpu.GpuEngine(16, p1=29, p2=None, p3=None, q2=4096)
    except ValueError:
        checks.append("u32 wheel modulus")
    else:
        return False, "CEILING FAIL: the u32 wheel ceiling was not enforced"
    try:
        gpu.wheel(16, 43)
    except ValueError:
        checks.append("RES_MAX")
    else:
        return False, "CEILING FAIL: an oversized one-level wheel was built"
    try:
        gpu.GpuEngine(16, p1=13, p2=37, p3=None, q2=4096)
    except ValueError:
        checks.append("gridDim.y")
    else:
        return False, "CEILING FAIL: an oversized second level was accepted"
    try:
        cpu.CpuEngine(16, q2=4096).survivors(4000, 5000)
    except ValueError:
        checks.append("max(K_FLOOR, q2) floor")
    else:
        return False, "CEILING FAIL: the floor was not enforced"
    return True, ("ceiling ok: " + ", ".join(checks) + " all raise rather "
                  "than compute")


def _stop_on_discovery_drill():
    """--stop-on-discovery stops on a NEW find, not on a loaded one.

    The counter is cumulative and restored from the checkpoint, so on a
    campaign resumed with history "any discoveries" is true before the
    first segment runs.  It shipped that way and stopped a resumed a(18)
    hunt on its opening segment, having found nothing.  Drilled on the
    resumed case specifically, because the fresh case cannot see it: with
    no history the two readings agree.
    """
    class _A:
        pass
    a = _A()
    for k, v in dict(fresh=False, to=None, stop_on_discovery=True,
                     heartbeat=30.0, gpu_yield_ms=0.0, status=False,
                     selftest=False).items():
        setattr(a, k, v)

    def stops(camp):
        return bool(a.stop_on_discovery
                    and camp.discoveries > camp._discoveries_at_start)

    class _C:
        def __init__(self, prior):
            self.discoveries = prior
            self._discoveries_at_start = prior
    for prior in (0, 1, 2, 7):
        c = _C(prior)
        if stops(c):
            return False, (f"STOP DRILL FAIL: a campaign resumed with "
                           f"{prior} prior discoveries stops before finding "
                           f"anything")
        c.discoveries += 1
        if not stops(c):
            return False, (f"STOP DRILL FAIL: a campaign with {prior} prior "
                           f"discoveries does not stop on its own find")
    return True, ("stop-on-discovery ok: a resumed campaign with 0, 1, 2 or 7 "
                  "finds already in the checkpoint does NOT stop before "
                  "finding something, and DOES stop on the next new find")


def selftest():
    t0 = time.time()
    rows = []
    for g in (ref.GATES + cpu.GATES + gpu.GATES + model.GATES
              + certificate.GATES):
        rows.append(g())
    rows.append(drills.event_kind_drill(
        lambda c: event_kind(*c), _event_cases()))
    for d in drills.standard():
        rows.append(d)
    for d in (_ceiling_drill, _canary_hunt, _protocol_drill, _resume_drill,
              _stop_on_discovery_drill):
        rows.append(d())
    bad = 0
    for ok, msg in rows:
        log("GATE" if ok else "ALARM", ("PASS " if ok else "FAIL ") + msg)
        bad += 0 if ok else 1
    log("STAGE",
        f"{len(rows) - bad}/{len(rows)} green in {time.time() - t0:.0f}s")
    if bad:
        log("ALARM", f"{bad} FAILURES")
        return 1
    banner("STAGE", ["ALL GREEN"])
    return 0


# ---------------------------------- status ----------------------------------

def _status():
    st = checkpoint.load(CKPT, CONFIG_KEY, warn=lambda m: log("STAGE", m),
                         accept=INHERITS)
    if not st:
        log("STATUS", "no checkpoint for this configuration yet")
        return 0
    cen = {int(r): int(c) for r, c in st.get("census", {}).items()}
    front = max(ref.KNOWN)
    for n in st.get("found", {}):
        front = max(front, int(n))
    log("STATUS", "  ".join([
        f"k = {int(st['k']):,}", f"filter n = {front + 1}",
        census_str(cen, CENSUS_FLOOR, front),
        f"finds {st.get('discoveries', 0)}",
        f"near {st.get('near', 0)}",
        f"elapsed {float(st.get('elapsed', 0)) / 3600:.2f} h",
        f"saved {st.get('saved', '?')}"]))
    for n, k in sorted(st.get("found", {}).items(), key=lambda x: int(x[0])):
        log("STATUS", f"  found: a({n}) = {int(k):,}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this depth on the k line (default: the "
                         "engine ceiling, 9e18)")
    ap.add_argument("--stop-on-discovery", action="store_true",
                    help="checkpoint and exit once THIS RUN confirms a find "
                         "(finds already in the checkpoint do not count)")
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (default 30)")
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0,
                    help="idle the device this long after every segment. "
                         "20 ms against a ~0.5 s segment costs about 4%% of "
                         "the rate and leaves the desktop noticeably freer")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 40 (about 8%% of the rate)")
    ap.add_argument("--fresh", action="store_true",
                    help="discard an existing cursor deliberately")
    args = ap.parse_args(argv)
    if args.gentle and not args.gpu_yield_ms:
        args.gpu_yield_ms = 40.0
    if args.selftest:
        return selftest()
    if args.status:
        return _status()
    if args.to:
        args.to = int(args.to)
    checkpoint.refuse_mismatch(CKPT, CONFIG_KEY, fresh=args.fresh,
                               describe=lambda s: f"k = {s.get('k')}",
                               accept=INHERITS)
    if args.fresh and os.path.exists(CKPT):
        os.remove(CKPT)
    return Campaign(args).run()


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    sys.exit(shutdown.graceful(main))
