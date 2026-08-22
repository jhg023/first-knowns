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
swept at all.  The campaign still starts far below it: at ~1.4e14 k/s the
whole of Alekseyev's range is a tenth of a second, so this hunt re-derives his
bound independently before it reaches new ground, and the least-claim rests
on our own coverage rather than on a citation.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine's enforced ceiling (K_CEIL = 9e18), which is the last rung.
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
This hunt has NO host worker pool, by construction rather than omission.
The device does the whole sieve; the host classifies survivors, and a
segment of 5.9e13 of k line yields about 640 of them, each costing a
handful of 64-bit Miller-Rabin tests.  That is milliseconds of host work
per ~0.5 s of device work, so there is nothing to ramp and no core count
to size.  The throttles that exist are `--gpu-yield-ms` and `--gentle`,
both priced in the help text against that half-second segment -- see
SEG_BLOCKS, which is set to hold the segment DURATION fixed as the engine
gets faster, precisely so those prices stay true.  No machine setting is
ever changed on the owner's behalf.
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
Q2 = cpu.Q2_DEFAULT               # sieve depth
# One wheel block is W = 7.42e12 of k line and 5.5e9 candidates, about
# 0.055 s of device time on the v3.1 engine.  MEASURED, and re-measured on
# v3: the rate is flat from 1 to 16 blocks per segment (1.158-1.163e14
# k/s, 0.4% across a 16x range), so this is not a throughput knob at all --
# per-launch overhead is already negligible.  That makes it purely a
# crash-cost choice, and CONVENTIONS.md says to spend a tie on the machine.
#
# The value moved from 2 to 8 when v3 landed, and the reason is worth
# stating because it is the trap in re-sweeping a knob that measures flat:
# what was chosen here is a SEGMENT DURATION of about half a second -- that
# is what an interrupt or a power cut costs to redo, and it is also the
# denominator that prices --gpu-yield-ms.  v3 made a block 4x faster, so
# holding SEG_BLOCKS at 2 would have silently cut the segment to 0.13 s and
# turned a 20 ms yield from 4% of the rate into 16% of it, and a `--gentle`
# 40 ms into 31%.  Neither number appears in any benchmark, which is
# exactly OPTIMIZATION.md rule 7: a sweep that measures only throughput
# cannot see a constraint that is not throughput.  At 8 blocks the segment
# is about half a second again, an interrupt still costs about half a
# second, the checkpoint fsync is 0.7% and the throttles cost roughly
# what their help text says (0.44 s at the v3.1 rate: 20 ms is 4.6%,
# 40 ms is 9.2%).  Re-derive those two the next time the engine gets
# much faster -- what is held fixed here is the DURATION, not the
# block count.
SEG_BLOCKS = 8
K_START = 10 ** 6                 # above max(K_FLOOR, Q2); see the docstring
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
ENGINE_VERSION = "v3.1"

CONFIG_KEY = (f"a089761-{ENGINE_VERSION}-p1{P1}-p2{P2}-q2{Q2}-"
              f"seg{SEG_BLOCKS}")


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
        self.hb = Heartbeat(interval=args.heartbeat)
        self._t0 = time.time()
        self.load()
        self.eng = gpu.GpuEngine(self.filter_n(), p1=P1, p2=P2, q2=Q2)
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
        preds = model.predictions(self.frontier(), self.frontier_k(),
                                  n_ahead=3, ceiling=cpu.K_CEIL)
        return Ladder.from_predictions(preds, ceiling=cpu.K_CEIL,
                                       ceiling_label="engine ceiling 9e18")

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
              "W": int(self.eng.W),
              "k": int(self.boundary) * int(self.eng.W),
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
        st = checkpoint.load(CKPT, CONFIG_KEY, warn=lambda m: log("STAGE", m))
        if not st:
            return False
        self.j = int(st["j"])
        self.found = dict(st.get("found", {}))
        self.census = {int(r): int(c) for r, c in st.get("census", {}).items()}
        self.passed = list(st.get("passed", []))
        self.elapsed = float(st.get("elapsed", 0.0))
        self.discoveries = int(st.get("discoveries", 0))
        self.near = int(st.get("near", 0))
        return True

    # ------------------------------------------------------------- status
    def status_line(self):
        k = (self.hb.pos() or self.j * self.eng.W)
        rate = self.hb.rate()
        parts = [f"k = {k:.6g}", f"filter n = {self.filter_n()}"]
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
        self.eng = gpu.GpuEngine(self.filter_n(), p1=P1, p2=P2, q2=Q2)
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
        target = self.args.to or cpu.K_CEIL
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
                j1 = min(self.j + SEG_BLOCKS, target // self.eng.W + 1)
                if j1 * self.eng.W > cpu.K_CEIL:
                    break
                self.hb.doing(f"sieving k in [{self.j * self.eng.W:.4g}, "
                              f"{j1 * self.eng.W:.4g})")
                surv = self.eng.survivors_j(self.j, j1)
                for k in surv.tolist():
                    r = self.run_length(int(k),
                                        cap=self.filter_n() + 6)
                    self.handle(int(k), r)
                self.j = j1
                self.boundary = self.j
                self.hb.mark(self.j * self.eng.W)
                self.check_rungs(self.j * self.eng.W)
                self.save()
                if self.args.stop_on_discovery and self.discoveries:
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
        eng = gpu.GpuEngine(n, p1=13, p2=None, q2=4096)
        surv = eng.survivors_k(30031, ref.KNOWN[n] + 1)
        ceng = cpu.CpuEngine(n, q2=4096)
        hits = [int(k) for k in surv.tolist()
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
    import numpy as _np
    total = 0
    for lab, kw, j_at, span, cut in (
            ("one-level", dict(p1=17, p2=None, q2=512), 10 ** 13, 20000, 7500),
            ("two-level", dict(p1=P1, p2=P2, q2=Q2), 10 ** 15, 6, 2)):
        eng = gpu.GpuEngine(16, **kw)
        j0 = eng.j_of(j_at)
        whole = eng.survivors_j(j0, j0 + span)
        a = eng.survivors_j(j0, j0 + cut)
        b = eng.survivors_j(j0 + cut, j0 + span)
        split = _np.concatenate([a, b])
        if whole.size == 0:
            return False, f"RESUME FAIL: {lab} window is empty -- vacuous"
        if not _np.array_equal(whole, split):
            return False, (f"RESUME FAIL: {lab}: {whole.size} whole vs "
                           f"{split.size} split")
        total += int(whole.size)
    return True, (f"resume ok: split sweep == unsplit sweep on both kernels "
                  f"({total} survivors across the seams), including the "
                  f"campaign's own (23,37] wheel")


def _ceiling_drill():
    """The enforced ceilings are enforced, not documented."""
    eng = gpu.GpuEngine(16, p1=23, p2=P2, q2=4096)
    checks = []
    try:
        eng.survivors_j(cpu.K_CEIL // eng.W, cpu.K_CEIL // eng.W + 10)
    except ValueError:
        checks.append("K_CEIL")
    else:
        return False, "CEILING FAIL: K_CEIL was not enforced"
    try:
        gpu.GpuEngine(16, p1=29, p2=None, q2=4096)
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
        gpu.GpuEngine(16, p1=13, p2=37, q2=4096)
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
    for d in (_ceiling_drill, _canary_hunt, _protocol_drill, _resume_drill):
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
    st = checkpoint.load(CKPT, CONFIG_KEY, warn=lambda m: log("STAGE", m))
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
                    help="checkpoint and exit once a find is confirmed")
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (default 30)")
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0,
                    help="idle the device this long after every segment. "
                         "20 ms against a ~0.5 s segment costs about 5%% of "
                         "the rate and leaves the desktop noticeably freer")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 40 (about 9%% of the rate)")
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
                               describe=lambda s: f"k = {s.get('k')}")
    if args.fresh and os.path.exists(CKPT):
        os.remove(CKPT)
    return Campaign(args).run()


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    sys.exit(shutdown.graceful(main))
