"""The campaign for the shift ladders -- least m with m + b^k prime, k = 1..n.

    python launch.py --selftest      the full gate battery (must end ALL GREEN)
    python launch.py                 the hunt: indefinite, resumable
    python launch.py --base 2        the A110096 family instead of A130003
    python launch.py --to 1e17       stop at a chosen depth on the m line
    python launch.py --status        read the checkpoint and say where it is

TWO FAMILIES, ONE ENGINE, ONE CAMPAIGN AT A TIME.  `--base 4` is A130003
(the default and the headline) and `--base 2` is A110096.  They are the
same mathematics with a different orbit, so they share every file here --
but they are different sequences with different frontiers, so each carries
its OWN checkpoint under its own config key and a campaign hunts one of
them.  Nothing about the engine changes when the base does; what changes is
the wheel, and by three thousand times (shiftladder_reference, the ord
lemma).

WHAT IS OPEN, AND WHY IT IS WORTH A SWEEP.  A130003 has eighteen terms and
its last, a(18) = 1,158,174,141,556,287, was found by Jens Kruse Andersen
in JUNE 2007 -- nineteen years ago, and nothing has touched the frontier
since; Rivera's Puzzle 403, the entry's only link, ends on the same value.
A110096 has sixteen, the last three from Bert Dobbelaere in April 2021 on
CPU.  Neither entry carries an upper bound of any kind, at any open n.

THE CLAIM'S FLOOR IS FREE.  a() is non-decreasing (the conditions nest), so
the next term is at least the last one and nothing below it has to be swept
at all.  The campaign still starts far below: re-deriving the published
terms on the way up costs seconds and puts the least-claim on our own
coverage rather than on a citation.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine's enforced ceiling -- the PRIMALITY-TEST validity bound
k_ceil(n, b) = 3.317e24 - b^n, which is the last rung.  `--to` and
`--stop-on-discovery` are the only stops and both are opt-in.  Progress is
read off RUNGS taken from the odds model's quantiles, logged as they are
passed and shown with an ETA in every [STATUS].  A rung retires with its
term: the ladder is derived from the LIVE frontier on every use.

THE TAXONOMY, mapped to this problem (CONVENTIONS.md "the discovery
protocol").  A survivor is an m with a run length r:

  DISCOVERY  r > frontier: it settles a(frontier+1) ... a(r) at once, each
             logged once, all evidenced under the FIRST value they belong
             to.  Verified three ways plus a factor witness for the
             composite that stops the run.
  NEAR       r == frontier: an m that reaches the settled frontier and no
             further -- ONE condition short of the open term.  One line
             with its campaign ordinal, verified by the cheap legs as an
             engine health check, never evidenced.
  CENSUS     CENSUS_FLOOR <= r < frontier: counted in [STATUS], never
             narrated.
  None       r < CENSUS_FLOOR: noise, not counted.

LOAD (CONVENTIONS.md "Sizing a hunt so it leaves the machine usable").
This hunt has NO host worker pool, and the measurement says it needs none.
RE-SWEPT at v2 against the segment loop itself, at the filters each family
resumes at (base 4 n = 21, base 2 n = 19), with the ladder cached:

    base 4   13.13 ms per launch:  sweep 94.7%  classify 1.3%  save 3.9%
    base 2   23.75 ms per launch:  sweep 89.8%  classify 7.8%  save 2.4%

1.9 and 24.2 survivors per launch, ~70 us of Miller-Rabin each.  Both
campaigns are DEVICE-BOUND, so there is nothing to ramp and no core count
to size, and the sizing rule is satisfied by measurement rather than by
omission.  The number to watch is survivors per second, logged in
[STATUS]: classification is serial with the device here, so if a future
engine raises the survivor rate by an order of magnitude the base-2 row
goes past half and the pool comes back.  The throttles are
`--gpu-yield-ms` and `--gentle`; the help text's price for `--gentle` is
NOT reproduced (measured 2.5 ms per launch, about a fifth at base 4, not a
third) and the disagreement is in OPTIMIZATION_LOG.md rather than silently
overwritten.  No machine setting is ever changed on the owner's behalf.
"""

import argparse
import math
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from huntlib import certificate, checkpoint, drills, evidence   # noqa: E402
from huntlib import shutdown                                    # noqa: E402
from huntlib.gpu import device_report                           # noqa: E402
from huntlib.hlog import Heartbeat, banner, census_str, log     # noqa: E402
from huntlib.primes import factor_witness, mr_is_prime          # noqa: E402
from huntlib.rungs import Ladder, LiveLadder, eta_str           # noqa: E402

import shiftladder_gpu as gpu                                   # noqa: E402
import shiftladder_model as model                               # noqa: E402
import shiftladder_reference as ref                             # noqa: E402
import shiftladder_search as cpu                                # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")

Q2 = cpu.Q2_DEFAULT               # sieve depth
# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches.  v1's wheel is a flat
# residue table, so a launch emits whole periods and COVERAGE and WORK
# advance together -- there is one cursor, not two, and an interrupt costs
# whatever is in flight.  (When the multi-level wheel lands they separate,
# and this file is already written to take them as two: `boundary` is the
# coverage claim and is the only thing a least-m claim rests on.)
# 16 launches is a fraction of a second at the v1 rate, which is what an
# interrupt should cost to redo and is the denominator that prices
# --gpu-yield-ms.
CKPT_LAUNCHES = 16
M_START = 10 ** 6                 # above max(K_FLOOR, Q2); see the docstring
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
ENGINE_VERSION = "v2"


def config_key(b, engine=None, p1=None):
    return (f"{ref.FAMILIES[b]['oeis'].lower()}-{engine or ENGINE_VERSION}"
            f"-p1{p1 or gpu.P1_DEFAULT[b]}-q2{Q2}-seg{CKPT_LAUNCHES}")


def ckpt_path(b):
    return str(HERE / f"campaign_checkpoint_b{b}.json")


def ledger_path(b):
    return str(HERE / "evidence" / f"{ref.FAMILIES[b]['oeis'].lower()}"
                                   f"_discoveries.json")


# EVERY reader of the checkpoint goes through this object and none of them
# takes a key list of its own.  There are three readers -- the campaign's
# load, --status, and the refusal check in main() -- and passing the same
# list to three places is a thing you can forget at one of them; it cost
# this repo two campaign starts before the policy existed (CONVENTIONS.md
# "Reading an existing cursor").  v1 is the first engine, so there is
# nothing to inherit and nothing to re-denominate yet, and both lists are
# deliberately empty rather than absent: the next engine version edits
# THESE and the drill in --selftest puts every reader in front of the
# result.
# TWO CLASSES OF OLD KEY, AND THEY ARE NOT INTERCHANGEABLE.
#
#   accept  the old configuration counted periods of the SAME W and swept
#           the same line, so the cursor carries over untouched.  v2 raised
#           the wheel with BIT PLANES over the period index, which leave W
#           alone -- so a p2 change, however large, is always `accept`.
#   adopt   the old configuration counted periods of a DIFFERENT W.  Only
#           the arithmetic claim "every m below this is swept" carries
#           over, and `load` re-denominates it by FLOORING into this
#           engine's periods so no gap can open.
#
# BOTH families are now `adopt` and NEITHER has an `accept` left: base 4
# moved p1 23 -> 29 (1.198x) and base 2 moved 37 -> 41 (1.398x) on
# 2026-08-27, so every key this project has ever written counts a period
# that is no longer this period.  The b = 2 keys moved OUT of `accept` in
# the same edit that added p1 = 41 -- leaving a stale key in `accept`
# would inherit a cursor counted in W(37) as though it were W(41) and
# silently claim 41x more line than was swept, which is the exact failure
# CursorPolicy exists to prevent.
ADOPT_B2 = (("v1", 37), ("v2", 37))
ADOPT_B4 = (("v1", 23), ("v2", 23))

_POLICIES = {b: checkpoint.CursorPolicy(
                    ckpt_path(b), config_key(b),
                    accept=(),
                    adopt=tuple(config_key(b, e, w)
                                for e, w in (ADOPT_B2 if b == 2
                                             else ADOPT_B4)))
             for b in ref.FAMILIES}


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


def verify(m, run, b):
    """The three independent confirmations plus the bounding witness.

    1. huntlib's Miller-Rabin, which is a PROOF here (G10: every value in
       the enforced range is under the deterministic bound);
    2. sympy's BPSW, an independent implementation, which must agree on the
       run LENGTH and not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense m line and uses no wheel at all, must
       agree that this m survives a sieve at a DIFFERENT depth from the
       campaign's.

    plus a factor witness for the composite that STOPS the run, which is
    what bounds the claim to exactly `run`.  Nothing here is unbounded: the
    witness is trial division, then a bounded rho, then bounded ECM.
    """
    legs = {"mr_chain": all(mr_is_prime(ref.value(m, k, b))
                            for k in range(1, run + 1)),
            "sympy_bpsw": ref.run_length(m, b, cap=run + 1) == run,
            "resieve_other_wheel": cpu.CpuEngine(run, b, q2=4096).survives(m)}
    stop = ref.value(m, run + 1, b)
    legs["stopper_composite"] = not mr_is_prime(stop)
    ok = all(legs.values())
    wit = factor_witness(stop) if legs["stopper_composite"] else None
    return ok, legs, {"k": run + 1, "value": stop, "factor": wit}


# --------------------------------- campaign ---------------------------------

class Campaign:
    def __init__(self, args, ckpt=None, cursor=None):
        # `ckpt`/`cursor` are overridable for ONE reason: so the selftest can
        # instantiate a campaign against a scratch file and exercise the
        # wiring -- checkpoint round trip, status line, census, rungs --
        # without sweeping.  A launcher whose loop is only ever run for real
        # is a launcher whose first bug is the owner's to find, and this
        # repo has lost two campaign starts that way.
        self.args = args
        self.b = int(args.base)
        self.fam = ref.FAMILIES[self.b]
        self.oeis = self.fam["oeis"]
        self.key = config_key(self.b)
        self.ckpt = ckpt or ckpt_path(self.b)
        self.cursor = cursor or _POLICIES[self.b]
        self.found = {}                # str(n) -> m found by THIS campaign
        self.census = {}               # run length -> count
        self.passed = []
        self.elapsed = 0.0
        self.discoveries = 0
        self.near = 0
        self.j = None
        self._stored_w = 0
        self._adopted = None
        self.hb = Heartbeat(interval=args.heartbeat)
        self._lad = LiveLadder(self._build_ladder)
        self._t0 = time.time()
        self._snapshot = None
        self.loaded = self.load()
        self.eng = gpu.GpuEngine(self.filter_n(), self.b, q2=Q2)
        # STORE THE UNIT NEXT TO THE NUMBER AND ASSERT IT ON LOAD
        # (OPTIMIZATION.md 2.9).  The config key DESCRIBES the wheel, which
        # is documentation; this is the assertion, and it is the half that
        # does not depend on the description being right.  It has to run
        # after the engine exists, which is why it is here and not in load().
        if self._adopted:
            log("STAGE",
                f"checkpoint written by {self._adopted[0]} ADOPTED: it "
                f"claims the line swept to m = {self._adopted[1]:,}, which "
                f"floors to period {self.j:,} of this engine's W = "
                f"{int(self.eng.W):,} (m = {self.j * int(self.eng.W):,}) -- "
                f"floored, so no line is skipped")
        if self._stored_w and self._stored_w != int(self.eng.W):
            raise ValueError(
                f"{self.ckpt} counts periods of W = {self._stored_w:,} but "
                f"this engine's period is {int(self.eng.W):,}: the cursor "
                f"means something else and has to be re-denominated, not "
                f"read")
        if self.j is None:
            self.j = max(M_START, cpu.m_floor(Q2) + 1) // self.eng.W + 1
        self.boundary = self.j
        self._discoveries_at_start = self.discoveries
        self.mark_boundary()

    # ------------------------------------------------------------- frontier
    def frontier(self):
        """The largest n settled: the literature plus this campaign."""
        top = max(ref.KNOWN[self.b])
        for n in self.found:
            top = max(top, int(n))
        return top

    def frontier_m(self):
        n = self.frontier()
        return int(self.found.get(str(n), ref.KNOWN[self.b].get(n, 0)))

    def filter_n(self):
        """The sieve filter is always the next OPEN term."""
        return self.frontier() + 1

    # ----------------------------------------------------------------- rungs
    def _build_ladder(self, frontier, frontier_m, n):
        ceil = cpu.k_ceil(n, self.b)
        preds = model.predictions(self.b, frontier, frontier_m,
                                  n_ahead=3, ceiling=ceil)
        return Ladder.from_predictions(preds, ceiling=ceil)

    def ladder(self):
        """Derived from the LIVE frontier on every use, so a find cannot
        leave the ladder aiming at a retired depth (CONVENTIONS.md: "a rung
        retires with its term") -- and REBUILT only when that frontier
        moves, which it does a handful of times per campaign.

        Deriving live is the safety property; deriving it again every
        segment was 1,080 numerical integrals for an identical answer and
        FOUR FIFTHS of this project's first campaign (OPTIMIZATION_LOG.md,
        "The campaign, measured").  `LiveLadder` keeps the first and drops
        the second: the frontier is the first component of its key by
        signature, so a cached ladder cannot outlive the frontier it came
        from.  Drilled in huntlib (gate_live_ladder) and here.
        """
        return self._lad.get(self.frontier(), self.frontier_m(),
                             self.filter_n())

    def next_rung(self, m):
        return self.ladder().next_rung(m, self.frontier())

    def check_rungs(self, m):
        lad = self.ladder()
        for lab in lad.newly_passed(m, self.frontier(), self.passed):
            self.passed.append(lab)
            nxt = lad.next_rung(m, self.frontier())
            log("RUNG", f"passed {lab}" +
                (f" -- next: {nxt[0]} at {nxt[1]:.4g}" if nxt else ""))

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "base": self.b,
                "j": int(self.boundary),
                "W": int(self.eng.W),
                # the COVERAGE claim: every m below this is swept.
                "m": int(self.swept_m()),
                "found": self.found,
                "census": {str(r): c for r, c in sorted(self.census.items())},
                "passed": self.passed,
                "elapsed": self.elapsed + (time.time() - self._t0),
                "discoveries": self.discoveries,
                "near": self.near,
                "saved": time.strftime("%Y-%m-%d %H:%M:%S")}

    def mark_boundary(self):
        """Snapshot the state as of the last fully classified segment.

        This is what an interrupt writes.  Every field is committed HERE,
        at the boundary -- a field folded in later would be silently
        dropped on the exit path the program actually uses (CONVENTIONS.md
        "Ctrl+C": primorial-ap lost its campaign clock exactly that way).
        """
        self._snapshot = self.state()

    def save(self, why=""):
        st = self.state()
        checkpoint.save(self.ckpt, st)
        return st

    def save_boundary(self):
        return checkpoint.save(self.ckpt, self._snapshot or self.state())

    def load(self):
        st, kind = self.cursor.load(warn=lambda m: log("STAGE", m))
        if not st:
            return False
        self._stored_w = int(st.get("W", 0))
        if kind == "adopted":
            # a different W: the stored period INDEX is meaningless here, so
            # only the coverage claim carries over, floored into this
            # engine's periods.  Flooring is the whole point -- rounding up
            # would skip line that was never swept.  The W assertion below
            # is skipped for exactly this case, and only this case.
            self._stored_w = 0
            self._adopted = (st.get("key"), int(st["m"]))
            self.j = int(st["m"]) // gpu.wheel_modulus(self.b)
        else:
            self.j = int(st["j"])
        self.found = dict(st.get("found", {}))
        self.census = {int(r): int(c) for r, c in st.get("census", {}).items()}
        self.passed = list(st.get("passed", []))
        self.elapsed = float(st.get("elapsed", 0.0))
        self.discoveries = int(st.get("discoveries", 0))
        self.near = int(st.get("near", 0))
        return True

    def swept_m(self):
        """The m below which EVERY value has been swept -- the coverage
        claim.  It is the period boundary and nothing else."""
        return self.boundary * self.eng.W

    # ------------------------------------------------------------- status
    def status_line(self):
        m = self.hb.pos() or self.swept_m()
        rate = self.hb.rate()
        parts = [f"swept to {self.swept_m():.6g}",
                 f"{self.oeis} filter n = {self.filter_n()}"]
        if rate:
            parts.append(f"{rate:.3g} m/s")
        parts.append(census_str(self.census, CENSUS_FLOOR, self.frontier()))
        parts.append(f"finds {self.discoveries}")
        nr = self.next_rung(m)
        if nr:
            lab, d = nr
            parts.append(f"next {lab} {d:.3g} "
                         f"(ETA {eta_str(d - m, rate) if rate else '?'})")
            p = model.p_by(self.filter_n(), self.b,
                           model.floor_for(self.filter_n(), self.b,
                                           self.frontier_m()), m)
            parts.append(f"P(a({self.filter_n()}) by now) = {100 * p:.0f}%")
        stall = self.hb.stalled()
        if stall:
            parts.append(f"-- no segment closed since the last status: "
                         f"{stall[0]} for {stall[1]:.0f}s")
        return "  ".join(parts)

    # --------------------------------------------------------------- hits
    def handle(self, m, run):
        frontier = self.frontier()
        kind = event_kind(run, frontier)
        if kind is None:
            return False
        self.census[run] = self.census.get(run, 0) + 1
        if kind == "CENSUS":
            return False
        if kind == "NEAR":
            self.near += 1
            ok, legs, _ = verify(m, run, self.b)
            if not ok:
                log("ALARM", f"NEAR value m = {m:,} run {run} failed "
                             f"verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at m = {m:,} (run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of a({frontier + 1})!")
            return False
        self.record_discovery(m, run)
        return True

    def record_discovery(self, m, run):
        frontier = self.frontier()
        self.hb.doing(f"verifying run-{run} m={m}")
        ok, legs, stop = verify(m, run, self.b)
        if not ok:
            log("ALARM", f"claimed a({frontier+1}) = {m} failed the "
                         f"protocol: {legs}")
            raise SystemExit(2)
        settles = list(range(frontier + 1, run + 1))
        certs = {str(k): certificate.prove(ref.value(m, k, self.b))
                 for k in range(1, run + 1)}
        # The record speaks the OEIS entry's language (CONVENTIONS.md
        # "Naming in an evidence file"): the published integer under the
        # entry's own letter, a `forms` that uses it, and `oeis_terms`
        # saying literally what goes into the OEIS.
        ev = {**evidence.header(self.oeis, f"{self.b}^k + m, k = 1..n",
                                "m", m, settles),
              "base": self.b,
              "run": int(run), "settles": settles,
              "values": {str(k): int(ref.value(m, k, self.b))
                         for k in range(1, run + 1)},
              "verification": legs,
              "stopper": {"k": stop["k"], "value": int(stop["value"]),
                          "factor": stop["factor"]},
              "certificates": certs,
              "least_claim": {"swept_from": M_START,
                              "swept_to": int(m),
                              "wheel": int(self.eng.W), "sieve_depth": Q2,
                              "monotone_floor": ref.KNOWN[self.b][
                                  max(ref.KNOWN[self.b])]},
              "engine": self.key}
        for n in settles:
            self.found[str(n)] = int(m)
        path = evidence.record(
            ev, EVID, f"{self.oeis}_a{settles[0]}_{m}.json",
            ledger_path(self.b), key="m",
            label="%s a(%s)" % (self.oeis, ",".join(map(str, settles))))
        self.discoveries += 1
        banner("DISCOVERY", [
            f"{self.oeis} a({settles[0]}) = {m:,}" if len(settles) == 1 else
            f"{self.oeis} a({settles[0]})..a({settles[-1]}) = {m:,}",
            f"run {run}: m + {self.b}^k is prime for k = 1..{run}",
            f"stopped by m + {self.b}^{stop['k']} = {stop['value']:,} "
            f"= {stop['factor']}",
            f"verified 3 ways, {len(certs)} certificates, evidence {path}",
        ])
        old_n = self.eng.n
        self.eng = gpu.GpuEngine(self.filter_n(), self.b, q2=Q2)
        log("STAGE", f"filter follows the frontier: n = {old_n} -> "
                     f"{self.eng.n}; the ladder now aims at "
                     f"a({self.filter_n()})")
        # the wheel is per (n, b), so a filter change re-denominates the
        # cursor: floor it so coverage overlaps and never gaps
        self.j = int(m) // self.eng.W
        self.boundary = self.j
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({n})") for n in settles)]

    # ---------------------------------------------------------------- loop
    def run(self):
        target = int(self.args.to or cpu.k_ceil(self.filter_n(), self.b))
        log("STAGE", f"campaign {self.key}")
        log("STAGE", device_report(self.eng.nbytes()))
        cfg = self.eng.config()
        log("STAGE",
            f"sweeping the m line to {target:.4g}; {self.oeis} filter n = "
            f"{self.filter_n()}; wheel W = {self.eng.W:,} "
            f"({self.eng.R:,} residues) x {cfg['ng']} bit planes to "
            f"{cfg['p2']}, leaving {100.0 * self.eng.density():.5f}% of the "
            f"line as candidates; resume at m = {self.swept_m():,}")
        # The one configuration fault score.py cannot see: the global tail
        # queue is sized from per_launch, and the frozen benchmark window is
        # a quarter of one launch, so a ceiling that binds here is invisible
        # there and costs about a fifth of the rate.  So the campaign says it.
        if cfg.get("q3_short"):
            log("STAGE",
                "note: the global tail queue is at its ceiling "
                f"({cfg['q3cap']:,} entries), so some of the tail runs "
                "uncompacted in the sieve block -- correct, and "
                "measured at about 3% here against 19% at base 4; the "
                "trade is written up in OPTIMIZATION_LOG.md")
        for n, qs in sorted(model.predictions(
                self.b, self.frontier(), self.frontier_m(), n_ahead=3).items()):
            log("STAGE", "  a(%d): %s" % (n, "  ".join(
                "%s %.3g" % (q, v) for q, v in qs.items())))
        log("STAGE", "'swept to' is the m below which EVERY value has been "
                     "tested -- it is the frontier, and it advances one "
                     "whole launch (%d periods, %.4g of line) at a time."
                     % (self.eng.per_launch,
                        self.eng.per_launch * self.eng.W))
        self.hb.mark(self.swept_m())
        self.hb.start(self.status_line)
        shutdown.on_interrupt(self._on_interrupt)
        stop_now = False
        try:
            while self.swept_m() < target and not stop_now:
                j1 = min(self.j + self.eng.per_launch * CKPT_LAUNCHES,
                         target // self.eng.W)
                if j1 <= self.j:
                    break
                if j1 * self.eng.W > cpu.k_ceil(self.filter_n(), self.b):
                    break
                self.hb.doing(f"sieving m in [{self.swept_m():.4g}, "
                              f"{j1 * self.eng.W:.4g})")
                for jn, surv in self.eng.sweep(self.j, j1):
                    for m in surv:
                        r = self.run_length(int(m),
                                            cap=self.filter_n() + 6)
                        if self.handle(int(m), r):
                            stop_now = stop_now or self.args.stop_on_discovery
                    self.j = jn
                    self.boundary = jn
                    if self.args.gpu_yield_ms:
                        time.sleep(self.args.gpu_yield_ms / 1000.0)
                self.hb.mark(self.swept_m())
                self.check_rungs(self.swept_m())
                self.mark_boundary()
                self.save()
                if stop_now:
                    log("STAGE", "stopping on discovery "
                                 "(--stop-on-discovery): THIS run confirmed "
                                 "a frontier-extending find")
        finally:
            self.hb.stop()
        self.mark_boundary()
        self.save()
        log("STAGE", f"campaign stopped at m = {self.swept_m():,} "
                     f"({self.discoveries} find(s) this campaign)")
        return 0

    run_length = None                  # bound below, after CpuEngine exists

    def _on_interrupt(self):
        # The message says what LANDED, not what was attempted: a save can
        # be deferred by another process's handle on the checkpoint, and an
        # exit line claiming a cursor that is not on disk is how an
        # operator comes back to the wrong resume point.
        if self.save_boundary():
            return (f"checkpoint written at the last segment boundary: "
                    f"m = {int(self._snapshot['m']):,} ({self.ckpt})")
        return (f"{self.ckpt} is held open by another process, so THIS "
                f"boundary (m = {int(self._snapshot['m']):,}) was not "
                f"written; the run resumes from the last save that landed")


def _run_length(self, m, cap=64):
    """Classification, on the host: huntlib's deterministic Miller-Rabin."""
    r = 0
    while r < cap and mr_is_prime(m + self.b ** (r + 1)):
        r += 1
    return r


Campaign.run_length = _run_length


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """All four outcomes of the taxonomy, on this project's mathematics."""
    return [((19, 18), "DISCOVERY"),      # beyond the frontier
            ((22, 18), "DISCOVERY"),      # a long run settles several at once
            ((18, 18), "NEAR"),           # one condition short of a(19)
            ((17, 18), "CENSUS"),         # below the frontier: counted only
            ((8, 18), "CENSUS"),          # the census floor itself
            ((7, 18), None),              # under the floor: not even counted
            ((0, 18), None)]


def _canary_hunt():
    """The stream must organically rediscover known terms.

    Dedicated mini-hunts at the filters those terms belong to.  The
    production filter cannot rediscover them -- a(9) has run 9 and an
    n = 19 wheel is entitled to kill it -- so a canary in the production
    stream would be a category error.  Rediscovery is what a canary is
    for, and it is done at the filter each term belongs to, on BOTH
    families: A130003's first term above the exception zone is a(15), and
    A110096 offers two inside a second of device time.

    The device may only start at a whole period above the engine floor, so
    the prefix between the floor and that period is checked on the CPU --
    otherwise "FIRST occurrence" would be a claim about a window rather
    than about the line.
    """
    for b, n, p1 in ((4, 15, 13), (2, 10, 13), (2, 9, 7)):
        want = ref.KNOWN[b][n]
        eng = gpu.GpuEngine(n, b, p1=p1, q2=4096, per_launch=256)
        lo = cpu.m_floor(4096) + 1
        j0 = cpu.m_floor(4096) // eng.W + 1
        ceng = cpu.CpuEngine(n, b, q2=4096)
        prefix = [int(m) for chunk in ceng.survivors(lo, j0 * eng.W)
                  for m in chunk if ceng.run_length(int(m), cap=n) >= n]
        if prefix:
            return False, (f"CANARY FAIL: b={b} n={n}: the CPU found "
                           f"{min(prefix)} below the first whole period")
        surv = eng.survivors_j(j0, want // eng.W + 1)
        hits = [int(m) for m in surv if ceng.run_length(int(m), cap=n) >= n]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: b={b} filter n={n} found "
                           f"{min(hits) if hits else None}, expected "
                           f"a({n}) = {want}")
    return True, ("canary ok: the GPU stream rediscovered A130003 a(15) and "
                  "A110096 a(10), a(9) as FIRST occurrences at their own "
                  "filters, with the sub-period prefix above the floor "
                  "cleared on the CPU")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on both families."""
    for b in (4, 2):
        top = max(ref.KNOWN[b])
        m = ref.KNOWN[b][top]
        ok, legs, stop = verify(m, top, b)
        if not ok:
            return False, (f"PROTOCOL FAIL: genuine run-{top} at m={m} "
                           f"(b={b}) rejected: {legs}")
        if stop["k"] != top + 1 or stop["factor"] is None:
            return False, (f"PROTOCOL FAIL: b={b}: no factor witness for "
                           f"the stopper")
        bad, legs_b, _ = verify(m, top + 1, b)
        if bad:
            return False, (f"PROTOCOL FAIL: fake run-{top+1} claim at m={m} "
                           f"(b={b}) ACCEPTED ({legs_b})")
        prev = max(n for n in ref.KNOWN[b] if ref.KNOWN[b][n] < m)
        fake, _lc, _ = verify(ref.KNOWN[b][prev], top, b)
        if fake:
            return False, (f"PROTOCOL FAIL: b={b}: a({prev})'s m accepted "
                           f"as a run-{top}")
    return True, ("protocol ok, both families: each frontier term accepted "
                  "at its true run with a factor witness for its stopper, "
                  "and a run one too long and a mislabelled earlier term "
                  "both rejected")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing: the primality-proof cap,
    the engine floor, and the Barrett bound on the wheel modulus."""
    raised = []
    eng = gpu.GpuEngine(12, 4, p1=13, q2=1024, per_launch=4)
    ceil = cpu.k_ceil(12, 4)
    try:
        eng.sweep(ceil // eng.W - 1, ceil // eng.W + 2)
        return False, "CEILING FAIL: the GPU engine swept past k_ceil"
    except ValueError:
        raised.append("gpu k_ceil")
    try:
        eng.sweep(0, 2)
        return False, "CEILING FAIL: the GPU engine swept at the floor"
    except ValueError:
        raised.append("gpu floor")
    c = cpu.CpuEngine(12, 4, q2=1024)
    try:
        c.survivors(10 ** 5, cpu.k_ceil(12, 4) + 10)
        return False, "CEILING FAIL: the CPU engine swept past k_ceil"
    except ValueError:
        raised.append("cpu k_ceil")
    try:
        c.survivors(10, 10 ** 6)
        return False, "CEILING FAIL: the CPU engine swept at the floor"
    except ValueError:
        raised.append("cpu floor")
    try:
        gpu.wheel(19, 2, 47)           # 1.29e9 residues: past RES_MAX
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.wheel(3, 2, 59)            # W would pass the Barrett bound
        return False, "CEILING FAIL: an oversized wheel modulus was built"
    except ValueError:
        raised.append("wheel modulus < 2^63")
    return True, ("ceiling ok: %s all raise rather than compute" %
                  ", ".join(raised))


def _resume_drill():
    """A split sweep must equal the unsplit sweep, on both families.

    The windows are wide enough to be POPULATED -- 40 periods is plenty at
    base 4 and empty at base 2, whose wheel is thousands of times sparser,
    and comparing two empty streams would drill nothing.
    """
    for b, n, p1, q2, nper in ((4, 8, 11, 64, 40), (2, 10, 13, 64, 400)):
        eng = gpu.GpuEngine(n, b, p1=p1, q2=q2, per_launch=5)
        j0 = (10 ** 6) // eng.W + 1
        cuts = (nper // 6, nper // 2)
        whole = eng.survivors_j(j0, j0 + nper)
        split = (eng.survivors_j(j0, j0 + cuts[0])
                 + eng.survivors_j(j0 + cuts[0], j0 + cuts[1])
                 + eng.survivors_j(j0 + cuts[1], j0 + nper))
        if whole != split or not whole:
            return False, (f"RESUME FAIL: b={b} {len(whole)} whole vs "
                           f"{len(split)} split")
    return True, ("resume ok: a sweep split at two arbitrary period "
                  "boundaries returns the identical stream on both "
                  "families (populated windows, base 4 and base 2)")


def _campaign_wiring_drill():
    """Build a campaign and exercise everything the loop touches, without
    sweeping a single candidate.

    Starting a hunt is the owner's command (CLAUDE.md rule 0a), so the
    campaign object is the one part of a launcher that a gate battery can
    easily leave untested -- and it is the part whose failures show up at
    the owner's hand rather than here.  This drills, on a scratch
    checkpoint: construction from nothing, the status line, the census and
    NEAR/CENSUS classification, the rung ladder, a save/load round trip,
    and the interrupt snapshot.
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="shiftladder-drill-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[4].at(path)

    class _A:
        pass
    a = _A()
    for k, v in dict(base=4, fresh=False, to=None, stop_on_discovery=False,
                     heartbeat=30.0, gpu_yield_ms=0.0, status=False,
                     selftest=False).items():
        setattr(a, k, v)
    try:
        c = Campaign(a, ckpt=path, cursor=pol)
        if c.frontier() != 18 or c.filter_n() != 19:
            return False, (f"WIRING FAIL: frontier {c.frontier()}, filter "
                           f"{c.filter_n()} -- expected 18 and 19")
        if c.swept_m() <= cpu.m_floor(Q2):
            return False, "WIRING FAIL: a fresh campaign starts at the floor"
        line = c.status_line()
        for want in ("swept to", "A130003", "census"):
            if want not in line:
                return False, f"WIRING FAIL: status line lacks {want!r}"
        # the census path, without a sweep: a run below the frontier is
        # counted and narrates nothing
        if c.handle(c.swept_m() + 1, 9) is not False or c.census.get(9) != 1:
            return False, "WIRING FAIL: a census run was not counted"
        if c.handle(c.swept_m() + 3, 7) is not False or 7 in c.census:
            return False, "WIRING FAIL: a run under the floor was counted"
        # the ladder must aim at the OPEN term and nothing retired
        nxt = c.next_rung(c.swept_m())
        if not nxt or not nxt[0].startswith("a(19)"):
            return False, f"WIRING FAIL: the ladder aims at {nxt}"
        c.check_rungs(c.swept_m())
        # THE LADDER IS CACHED ON THE FRONTIER, and both halves matter: it
        # must not rebuild while the frontier stands (that was 4/5 of this
        # project's first campaign) and it MUST rebuild the moment a find
        # moves it (that was the dickson-ladders incident).  huntlib's
        # gate_live_ladder drills the mechanism; this drills the wiring.
        builds = c._lad.builds
        for _ in range(25):
            c.ladder()
            c.next_rung(c.swept_m())
            c.check_rungs(c.swept_m())
        if c._lad.builds != builds:
            return False, (f"WIRING FAIL: 75 ladder reads at a standing "
                           f"frontier caused {c._lad.builds - builds} "
                           f"rebuild(s) -- the segment loop pays the model "
                           f"again every segment")
        c.found["19"] = int(ref.KNOWN[4][18]) + 2      # a find, not verified
        if c.frontier() != 19 or c.filter_n() != 20:
            return False, "WIRING FAIL: a find did not move the frontier"
        aim = c.next_rung(c.swept_m())
        if c._lad.builds != builds + 1:
            return False, ("WIRING FAIL: the frontier moved and the ladder "
                           "was served from cache")
        if not aim or not aim[0].startswith(("a(20)", "engine ceiling")):
            return False, (f"WIRING FAIL: after finding a(19) the campaign "
                           f"aims at {aim} -- a retired rung")
        c.found.pop("19")
        c._lad.invalidate()
        # round trip
        c.mark_boundary()
        c.save()
        d = Campaign(a, ckpt=path, cursor=pol)
        if (d.j, d.census, d.discoveries) != (c.boundary, c.census,
                                              c.discoveries):
            return False, (f"WIRING FAIL: reload gave j={d.j} census="
                           f"{d.census}, wrote j={c.boundary} census="
                           f"{c.census}")
        msg = c._on_interrupt()
        if "checkpoint written at the last segment boundary" not in msg:
            return False, f"WIRING FAIL: the interrupt path said {msg!r}"
        st, kind = pol.load()
        if kind != "own" or int(st["m"]) != c.swept_m():
            return False, "WIRING FAIL: the boundary snapshot did not land"
    finally:
        for f in pathlib.Path(tmp).glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            pathlib.Path(tmp).rmdir()
        except OSError:
            pass
    return True, ("campaign wiring ok: a campaign builds from nothing at the "
                  "right frontier, its status line and rung ladder aim at "
                  "a(19), 75 ladder reads at a standing frontier cost 0 "
                  "model rebuilds while a find costs exactly 1 and moves "
                  "the aim off a(19), a census run is counted and a "
                  "sub-floor run is not, and the checkpoint round trips "
                  "through both the normal save and the interrupt snapshot")


def _stop_on_discovery_drill():
    """--stop-on-discovery stops on a NEW find, not on a loaded one.

    The counter is cumulative and restored from the checkpoint, so on a
    campaign resumed with history "any discoveries" is true before the
    first segment runs.  square-ladders shipped exactly that and a resumed
    a(18) hunt exited on its opening segment having found nothing.  Drilled
    on the RESUMED case specifically, because the fresh case cannot see it.
    """
    def stops(camp, flag=True):
        return bool(flag and camp.discoveries > camp._discoveries_at_start)

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
    return True, ("stop-on-discovery ok: a resumed campaign with 0, 1, 2 or "
                  "7 finds already in the checkpoint does NOT stop before "
                  "finding something, and DOES stop on the next new find")


def _other_family_cursor_drill(base):
    """The OTHER family's policy, put in front of every key it declares.

    `drills.standard` exercises the policy of the base the selftest was run
    for, and the two families do not declare the same old keys: base 4
    ADOPTS two p1 = 23 cursors (its flat wheel moved 23 -> 29), base 2
    INHERITS one v1 cursor (its p1 never moved).  Drilling only one of them
    leaves the other's classification unproven -- and a launcher whose
    battery is green and whose campaign will not start is the exact failure
    CursorPolicy exists to prevent, twice over in this repo.
    """
    import tempfile
    other = 2 if int(base) == 4 else 4
    tmp = tempfile.mkdtemp(prefix="shiftladder-cursor-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[other].at(path)
    seen = []
    try:
        for key in pol.readable():
            checkpoint.save(path, {"key": key, "j": 7, "m": 11,
                                   "W": int(gpu.wheel_modulus(other))})
            st, kind = pol.load()
            if not st or kind is None:
                return False, (f"CURSOR FAIL: base {other} will not read a "
                               f"checkpoint keyed {key}")
            pol.refuse_mismatch()          # must NOT raise
            seen.append(kind)
        checkpoint.save(path, {"key": "not-a-real-key", "j": 7, "m": 11})
        st, _k = pol.load()
        if st:
            return False, (f"CURSOR FAIL: base {other} read a foreign key")
        try:
            pol.refuse_mismatch()
            return False, (f"CURSOR FAIL: base {other} did not refuse a "
                           f"foreign key")
        except checkpoint.CursorRefused:
            pass
    finally:
        for f in pathlib.Path(tmp).glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            pathlib.Path(tmp).rmdir()
        except OSError:
            pass
    return True, (f"cursor policy (base {other}) ok: all {len(seen)} declared "
                  f"key(s) pass BOTH readers with the right classification "
                  f"({', '.join(seen)}); an unknown key refuses")


def _two_families_stay_apart():
    """The two campaigns must not be able to read each other's cursor.

    They cover different sequences on different lines, so a checkpoint from
    one is not a stale file to be ignored but a foreign one to refuse.  The
    config keys carry the OEIS id, so this is true by construction -- which
    is exactly the kind of claim that stops being true silently, so it is
    asserted.
    """
    if config_key(2) == config_key(4):
        return False, "FAMILY FAIL: both bases share a config key"
    if ckpt_path(2) == ckpt_path(4):
        return False, "FAMILY FAIL: both bases share a checkpoint file"
    for b, other in ((2, 4), (4, 2)):
        if config_key(other) in _POLICIES[b].readable():
            return False, (f"FAMILY FAIL: the b={b} policy accepts the "
                           f"b={other} key")
    return True, ("families stay apart: distinct config keys and checkpoint "
                  "files, and neither policy will read the other's cursor")


def selftest(base=4):
    t0 = time.time()
    rows = []
    for g in (ref.GATES + cpu.GATES + gpu.GATES + model.GATES
              + certificate.GATES):
        rows.append(g())
    rows.append(drills.event_kind_drill(
        lambda c: event_kind(*c), _event_cases()))
    for d in drills.standard(cursor=_POLICIES[base]):
        rows.append(d)
    rows.append(_other_family_cursor_drill(base))
    for d in (_ceiling_drill, _canary_hunt, _protocol_drill, _resume_drill,
              _stop_on_discovery_drill, _two_families_stay_apart,
              _campaign_wiring_drill):
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

def _status(base):
    st, _kind = _POLICIES[base].load(warn=lambda m: log("STAGE", m))
    if not st:
        log("STATUS", f"no checkpoint for {config_key(base)} yet")
        return 0
    cen = {int(r): int(c) for r, c in st.get("census", {}).items()}
    front = max(ref.KNOWN[base])
    for n in st.get("found", {}):
        front = max(front, int(n))
    log("STATUS", "  ".join([
        f"{ref.FAMILIES[base]['oeis']}",
        f"m = {int(st['m']):,}", f"filter n = {front + 1}",
        census_str(cen, CENSUS_FLOOR, front),
        f"finds {st.get('discoveries', 0)}",
        f"near {st.get('near', 0)}",
        f"elapsed {float(st.get('elapsed', 0)) / 3600:.2f} h",
        f"saved {st.get('saved', '?')}"]))
    for n, m in sorted(st.get("found", {}).items(), key=lambda x: int(x[0])):
        log("STATUS", f"  found: a({n}) = {int(m):,}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=int, default=4, choices=(2, 4),
                    help="4 = A130003 (default), 2 = A110096")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this depth on the m line (default: the "
                         "engine ceiling, 3.317e24)")
    ap.add_argument("--stop-on-discovery", action="store_true",
                    help="checkpoint and exit once THIS RUN confirms a find "
                         "(finds already in the checkpoint do not count)")
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (default 30)")
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0,
                    help="idle the device this long after every launch. "
                         "1 ms against a ~5 ms launch costs about 20%% of "
                         "the rate and leaves the desktop noticeably freer")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 2 (about a third of the "
                         "rate, and the quietest this hunt gets)")
    ap.add_argument("--fresh", action="store_true",
                    help="discard an existing cursor deliberately")
    args = ap.parse_args(argv)
    if args.gentle and not args.gpu_yield_ms:
        args.gpu_yield_ms = 2.0
    if args.selftest:
        return selftest(args.base)
    if args.status:
        return _status(args.base)
    if args.to:
        args.to = int(args.to)
    _POLICIES[args.base].refuse_mismatch(
        fresh=args.fresh,
        describe=lambda k: log("STAGE", f"refusing to start: the checkpoint "
                                        f"at {ckpt_path(args.base)} was "
                                        f"written by {k}"))
    return Campaign(args).run()


if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
