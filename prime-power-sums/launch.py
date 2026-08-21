"""The campaign for the prime power-sum divisibility farm.

One contiguous sweep of the prime line feeds SEVEN open OEIS sequences at
once (fourteen counting their prime-reported partners), because every
family shares the same primes and differs only in which power is summed.
The sweep starts below every live frontier, so before it reaches new
ground it must rediscover 124 published terms -- the canary battery, which
nobody had to invent.

    python launch.py --selftest      the full gate battery (must end ALL GREEN)
    python launch.py                 the hunt: indefinite, resumable, ~days
    python launch.py --to 1e16       stop at a chosen prime-line depth
    python launch.py --status        read the checkpoint and say where it is

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine's enforced ceiling (P_CEIL = 2^62), which is the last rung.
`--to` and `--stop-on-discovery` are the only stops and both are opt-in.
Progress is read off RUNGS: the odds model's quantiles for each family's
next open term, converted to the prime line, logged as they are passed and
shown with an ETA in every [STATUS].  A rung retires with its term -- the
ladder is derived from the LIVE frontier on every use, so it cannot go on
advertising a depth for a term already found.

THE TAXONOMY, mapped to this problem (CONVENTIONS.md "the discovery
protocol").  A hit is (m, e, k):

  DISCOVERY  a target family, k beyond that family's frontier: the next
             term of two OEIS sequences at once (index and prime), and for
             m = 1 of four.  Verified three ways, evidenced, logged once.
  NEAR       the census family beyond ITS published frontier -- a real new
             value of A233264/A233265, but that pair runs to thousands of
             terms and extending it is data entry, not discovery.  One line
             with its ordinal, verified cheaply, never evidenced.  This
             project has no "one value short" event in the ladder sense
             (a k either divides or does not), so NEAR is mapped to the
             class the convention describes: real, worth a line, not
             evidence.
  CENSUS     a census-family hit below that frontier: counted in [STATUS],
             never narrated.
  None       anything outside the declared coverage.
  ALARM      a hit in a target family BELOW its frontier that is not in the
             frozen table -- either this engine is wrong or a published
             search missed a term.  Both stop the campaign (exit 2).

LOAD (CONVENTIONS.md "Sizing a hunt so it leaves the machine usable").
This hunt has NO host worker pool, by construction rather than by
omission: the device does the sieve, the powers and the reduction, and the
host does one carry-normalization per chunk (a few hundred microseconds
per ~60 ms of device work) plus a verification only when something is
found.  There is therefore nothing to ramp and no core count to size --
the throttles that exist are `--gpu-yield-ms` and `--gentle`, both priced
in the help text.  No machine setting is ever changed on the owner's
behalf.
"""

import argparse
import math
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from huntlib import checkpoint, drills, evidence, shutdown          # noqa: E402
from huntlib.hlog import Heartbeat, banner, census_str, log         # noqa: E402
from huntlib.rungs import Ladder, eta_str                           # noqa: E402

import psum_gpu                                                     # noqa: E402
import psum_gpu2                                                    # noqa: E402
import psum_model as model                                          # noqa: E402
import psum_reference as ref                                        # noqa: E402
import psum_search as cpu                                           # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CKPT = str(HERE / "campaign_checkpoint.json")
EVID = str(HERE / "evidence")
LEDGER = str(HERE / "evidence" / "psum_discoveries.json")

ENGINE_VERSION = "v2"
SEG = psum_gpu2.SEG_DEFAULT
RUN = 32                                  # tuned at campaign height, not
                                          # at the score window
CHUNK = psum_gpu.CHUNK                    # v1's shape, kept for the gates
# v2 sizes its limbs from the run rather than from a constant, so the
# config key carries the geometry that fixes the stream instead of LIMBS.
CEILING = cpu.P_CEIL                      # the last rung: 2^62
CONFIG_KEY = (f"psum-{ENGINE_VERSION}-run{RUN}-"
              f"odd{int(cpu.ODD_ONLY)}-fams"
              f"{'_'.join('%d.%d' % f for f in ref.ALL_FAMILIES)}")

CENSUS_FAMILY = ref.CENSUS_FAMILY
CENSUS_FRONTIER = 2 * 10 ** 13            # A233264: a(1171) > 2e13, Garner 2021


# ------------------------------- the taxonomy -------------------------------

def event_kind(rec, frontiers=None):
    """DISCOVERY / NEAR / CENSUS / None for a hit -- the repo-wide rule,
    this project's mathematics.  `frontiers` is the LIVE table (the
    checkpoint's promotions included), never the frozen one.

    rec: {"m": m, "e": e, "k": k}
    """
    m, e, k = int(rec["m"]), int(rec["e"]), int(rec["k"])
    fam = (m, e)
    if cpu.ODD_ONLY and k % 2 == 0:
        return None                                   # outside coverage
    if fam == CENSUS_FAMILY:
        front = (frontiers or {}).get(fam, CENSUS_FRONTIER)
        return "NEAR" if k > front else "CENSUS"
    if fam not in ref.FAMILIES:
        return None
    front = (frontiers or {}).get(fam, ref.FAMILIES[fam]["frontier"])
    if k > front:
        return "DISCOVERY"
    return "CENSUS"                                   # a known term: canary


def is_canary(fam, k):
    """A hit that the literature already contains."""
    return fam in ref.FAMILIES and k in ref.FAMILIES[fam]["terms"]


def is_alarm(fam, k, frontiers):
    """A target-family hit below the frontier that is NOT published: either
    the engine is wrong or a published search missed a term."""
    if fam == CENSUS_FAMILY or fam not in ref.FAMILIES:
        return False
    front = frontiers.get(fam, ref.FAMILIES[fam]["frontier"])
    return k <= front and not is_canary(fam, k)


# ------------------------------ verification --------------------------------

def rederive(fam, k, boundary_state, p_hi, seg=7919):
    """Re-derive the window on the CPU engine, with a DIFFERENT segmentation,
    and capture the exact state AT the hit.

    `boundary_state` is the (p, k, sums) at the start of the segment, which
    the campaign checkpointed before that segment ran, so this is bounded
    work: one segment, deterministic, no unbounded step anywhere in a
    verification path (CONVENTIONS.md).

    Returns (found, cap) with cap = {"sums": {...}, "p": prime(k)} -- the
    sum AT index k, which is the only sum the test is about.  Reading the
    campaign's running sum instead would read the value at the END of the
    segment; the protocol drill caught exactly that and it is why this
    function exists.
    """
    m, e = fam
    cap = {}

    def on_hit(mm, ee, kk, p, st):
        if (mm, ee, kk) == (m, e, k):
            cap["sums"] = dict(st.sums)
            cap["p"] = int(p)

    eng = cpu.CpuSweep((fam,), seg=seg)           # 7919: deliberately unlike SEG
    hits, _ = eng.run(p_hi, state=boundary_state.copy(), on_hit=on_hit)
    return ((m, e, k) in hits), cap


def verify(fam, k, cap, engine_claim=True):
    """The three independent confirmations a find must survive.

    1. the engine's own claim (GPU Montgomery reduction over limbs);
    2. an independent re-derivation of the segment by the CPU engine, at a
       different segment size, which must produce the same hit;
    3. an independent arithmetic path on the sum that re-derivation
       captured: exact Python integers reduced by `%`, a different
       representation and a different operation from the GPU's Montgomery
       reduction over 32-bit limbs.

    The prefix BELOW the window is warranted separately and continuously by
    the canary chain: the sweep has rediscovered every published term below
    it, or it would have halted long before here.

    Returns (ok, legs) with legs a dict for the evidence file.
    """
    m, e = fam
    legs = {"engine_montgomery": bool(engine_claim),
            "resegment_rederivation": bool(cap)}
    total = cap.get("sums", {}).get(m)
    legs["host_exact_mod"] = (total is not None and (e + total) % k == 0)
    legs["quotient"] = (str((e + total) // k) if legs["host_exact_mod"]
                        else None)
    ok = all(legs[x] is True for x in ("engine_montgomery",
                                       "resegment_rederivation",
                                       "host_exact_mod"))
    return ok, legs


# --------------------------------- campaign ---------------------------------

class Campaign:
    def __init__(self, args):
        self.args = args
        self.families = ref.ALL_FAMILIES
        self.ms = sorted({m for m, _ in self.families})
        self.engine = psum_gpu2.GpuSweep2(self.families, seg=SEG, run=RUN)
        self.state = cpu.State(self.ms)
        self.boundary = self.state.copy()
        self.found = {}            # "m.e" -> [k, ...] found by THIS project
        self.census = {}           # m -> count of hits seen
        self.passed = []           # rung labels already logged
        self.elapsed = 0.0
        self.discoveries = 0
        self.near = 0
        self.hb = Heartbeat(interval=args.heartbeat)
        self._t0 = time.time()

    # ----------------------------------------------------------- frontiers
    def frontiers(self):
        """The LIVE frontier per family: the published one, promoted by
        anything this campaign has already found.  Derived on every use so
        a promotion can never be forgotten."""
        out = {}
        for fam in ref.TARGETS:
            out[fam] = ref.FAMILIES[fam]["frontier"]
        out[CENSUS_FAMILY] = CENSUS_FRONTIER
        for key, ks in self.found.items():
            m, e = (int(x) for x in key.split("."))
            if ks:
                out[(m, e)] = max(out.get((m, e), 0), max(ks))
        return out

    def n_known(self, fam):
        """How many terms of this family are settled (published + found)."""
        base = len(ref.FAMILIES[fam]["terms"]) if fam in ref.FAMILIES else 0
        return base + len(self.found.get("%d.%d" % fam, []))

    # --------------------------------------------------------------- rungs
    def ladders(self):
        out = {}
        for fam in ref.TARGETS:
            preds = model.predictions(fam, frontier=self.frontiers()[fam],
                                      n_next=self.n_known(fam) + 1)
            out[fam] = Ladder.from_predictions(
                preds, ceiling=CEILING,
                ceiling_label="engine ceiling 2^62")
        return out

    def next_rung(self, pos):
        best = None
        for fam, lad in self.ladders().items():
            nr = lad.next_rung(pos, self.n_known(fam) - 1)
            if nr and (best is None or nr[1] < best[1][1]):
                best = (fam, nr)
        return best

    def check_rungs(self, pos):
        for fam, lad in self.ladders().items():
            for lab in lad.newly_passed(pos, self.n_known(fam) - 1,
                                        self.passed):
                self.passed.append(lab)
                nxt = self.next_rung(pos)
                log("RUNG", f"passed {ref.FAMILIES[fam]['idx']} {lab} "
                            f"(p = {pos:.4g})" +
                            (f" -- next: {ref.FAMILIES[nxt[0]]['idx']} "
                             f"{nxt[1][0]} at {nxt[1][1]:.4g}" if nxt else ""))

    # ---------------------------------------------------------- checkpoint
    def save(self, why=""):
        st = {"key": CONFIG_KEY,
              "engine": ENGINE_VERSION,
              "state": self.boundary.to_json(),
              "found": self.found,
              "census": {str(m): n for m, n in sorted(self.census.items())},
              "passed": self.passed,
              "elapsed": self.elapsed + (time.time() - self._t0),
              "discoveries": self.discoveries,
              "near": self.near,
              "saved": time.strftime("%Y-%m-%d %H:%M:%S")}
        checkpoint.save(CKPT, st)
        return st

    def load(self):
        st = checkpoint.load(CKPT, CONFIG_KEY,
                             warn=lambda m: log("STAGE", m))
        if not st:
            return False
        self.state = cpu.State.from_json(st["state"])
        self.boundary = self.state.copy()
        self.found = dict(st.get("found", {}))
        self.census = {int(k): int(v) for k, v in st.get("census", {}).items()}
        self.passed = list(st.get("passed", []))
        self.elapsed = float(st.get("elapsed", 0.0))
        self.discoveries = int(st.get("discoveries", 0))
        self.near = int(st.get("near", 0))
        return True

    # ------------------------------------------------------------- status
    def status_line(self):
        pos = self.hb.pos() or self.state.p
        rate = self.hb.rate()
        lo, hi = min(self.ms), max(self.ms)
        parts = [f"p = {pos:.6g}", f"k = {self.state.k:,}"]
        if rate:
            parts.append(f"{rate:.3g} p/s")
        parts.append(census_str(self.census, lo, hi))
        parts.append(f"finds {self.discoveries}")
        nr = self.next_rung(pos)
        if nr:
            fam, (lab, depth) = nr
            eta = eta_str(depth - pos, rate) if rate else "?"
            parts.append(f"next {ref.FAMILIES[fam]['idx']} {lab} "
                         f"{depth:.3g} (ETA {eta})")
        fam0 = (11, 0)
        k_now = model.p_to_k(pos)
        parts.append("P(a(%d) of %s by now) = %.0f%%"
                     % (self.n_known(fam0) + 1, ref.FAMILIES[fam0]["idx"],
                        100 * model.p_by(fam0[0], fam0[1],
                                         self.frontiers()[fam0], k_now)))
        stall = self.hb.stalled()
        if stall:
            parts.append(stall)
        return "  ".join(parts)

    # --------------------------------------------------------------- hits
    def handle(self, fam, k, p_lo, p_hi):
        """Classify one hit and do what the taxonomy says."""
        m, e = fam
        fronts = self.frontiers()
        kind = event_kind({"m": m, "e": e, "k": k}, fronts)
        if kind is None:
            return
        if is_alarm(fam, k, fronts):
            banner("ALARM", [
                f"{ref.FAMILIES[fam]['idx']}: hit at k = {k:,} is BELOW the "
                f"published frontier {fronts[fam]:,} and is not in the "
                f"frozen table.",
                "Either this engine is wrong or a published search missed a "
                "term. The campaign stops here; a human decides which.",
            ])
            self.save("alarm")
            raise SystemExit(2)
        if kind == "CENSUS":
            self.census[m] = self.census.get(m, 0) + 1
            if is_canary(fam, k):
                log("CANARY-GOLD",
                    f"{ref.FAMILIES[fam]['idx']} rediscovered a known term "
                    f"k = {k:,} (published, expected here)")
            return
        if kind == "NEAR":
            self.near += 1
            self.census[m] = self.census.get(m, 0) + 1
            log("NEAR", f"{ref.CENSUS_INFO['idx']} new value k = {k:,} "
                        f"(census-class #{self.near} of the campaign; "
                        f"engine-verified only, no witness and no "
                        f"certificate -- that pair runs to thousands of "
                        f"terms and extending it is data entry)")
            return
        # DISCOVERY
        self.record_discovery(fam, k, p_lo, p_hi)

    def record_discovery(self, fam, k, p_lo, p_hi):
        m, e = fam
        f = ref.FAMILIES[fam]
        n = self.n_known(fam) + 1
        found, cap = rederive(fam, k, self.boundary, p_hi)
        ok, legs = verify(fam, k, cap, engine_claim=found)
        legs["canary_chain"] = sum(self.census.values())
        if not ok:
            banner("ALARM", [
                f"{f['idx']} a({n}) candidate k = {k:,} FAILED verification",
                f"legs: {legs}",
                "A disagreement between the legs is an engine bug by "
                "definition. Stopping (exit 2).",
            ])
            self.save("failed verification")
            raise SystemExit(2)
        total = cap["sums"][m]
        p_k = cap.get("p")
        self.found.setdefault("%d.%d" % fam, []).append(k)
        self.discoveries += 1
        ev = {"sequence_index": f["idx"], "sequence_prime": f["val"],
              "also_extends": list(f["also"]), "m": m, "e": e, "term": n,
              "k": k, "prime_k": p_k, "sum": str(total),
              "quotient": legs.get("quotient"),
              "previous_term": f["terms"][-1] if f["terms"] else None,
              "published_frontier": f["frontier"],
              "frontier_held_by": f["held"],
              "verification": legs,
              "engine": ENGINE_VERSION, "config": CONFIG_KEY,
              "swept_from_prime": 2, "found_in_window": [p_lo, p_hi]}
        evidence.record(ev, EVID, f"psum_m{m}e{e}_k{k}.json", LEDGER, key="k",
                        label=f"{f['idx']} a({n})")
        banner("DISCOVERY", [
            f"{f['idx']} a({n}) = {k:,}",
            f"  and {f['val']} a({n}) = prime({k:,})"
            + (f" = {p_k:,}" if p_k else ""),
            *[f"  and {a} a({n})" for a in f["also"]],
            f"  m = {m}, e = {e}; previous term {f['terms'][-1]:,}",
            f"  published frontier {f['frontier']:,} ({f['held']})",
            f"  verified 3 ways; evidence written; quotient recorded",
        ])
        self.save("discovery")
        if self.args.stop_on_discovery:
            log("STAGE", "--stop-on-discovery: checkpointed and stopping so "
                         "a human can react before more GPU time is spent")
            raise SystemExit(0)

    # ---------------------------------------------------------------- main
    def run(self):
        target = self.args.to or CEILING
        self.engine.check_ceiling(min(target, CEILING))
        log("STAGE", f"campaign {CONFIG_KEY}")
        log("STAGE", f"sweeping the prime line to {target:.4g}; "
                     f"{len(ref.TARGETS)} target families + 1 census family; "
                     f"resume at p = {self.state.p:,}")
        board = model.campaign_board(self.frontiers())
        for r in board:
            log("STAGE", "  %-8s m=%-2d c=%.3f  next a(%d) median at k = %.3g"
                         % (r["idx"], r["family"][0], r["c"], r["next_term"],
                            r["quantiles"]["median"]))
        self.hb.mark(self.state.p)
        self.hb.start(self.status_line)
        shutdown.on_interrupt(self._on_interrupt)
        try:
            while self.state.p < target:
                p_lo = self.state.p
                p_hi = min(p_lo + SEG, target)
                self.hb.doing(f"sieving [{p_lo:.4g}, {p_hi:.4g})")
                hits, st = self.engine.run(p_hi, state=self.state)
                self.state = st
                for m, e, k in hits:
                    self.handle((m, e), k, p_lo, p_hi)
                # the segment is fully classified: THIS is the boundary
                self.boundary = self.state.copy()
                self.hb.mark(self.state.p)
                self.check_rungs(self.state.p)
                self.save()
                if self.args.gpu_yield_ms:
                    time.sleep(self.args.gpu_yield_ms / 1000.0)
        finally:
            self.hb.stop()
        log("STAGE", f"reached p = {self.state.p:.6g}; "
                     f"{self.discoveries} discoveries, {self.near} near, "
                     f"{sum(self.census.values())} census")
        self.save("end of run")
        return 0

    def _on_interrupt(self):
        st = self.save("interrupt")
        return (f"checkpoint written at the last segment boundary: "
                f"p = {self.boundary.p:,} k = {self.boundary.k:,} "
                f"({CKPT})")


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """All four outcomes of the taxonomy, on this project's mathematics."""
    fronts = {fam: ref.FAMILIES[fam]["frontier"] for fam in ref.TARGETS}
    fronts[CENSUS_FAMILY] = CENSUS_FRONTIER
    m, e = (11, 0)
    return [
        ({"m": m, "e": e, "k": fronts[(m, e)] + 3}, "DISCOVERY"),
        ({"m": CENSUS_FAMILY[0], "e": CENSUS_FAMILY[1],
          "k": CENSUS_FRONTIER + 3}, "NEAR"),
        ({"m": CENSUS_FAMILY[0], "e": CENSUS_FAMILY[1], "k": 175}, "CENSUS"),
        ({"m": m, "e": e, "k": ref.FAMILIES[(m, e)]["terms"][-1]}, "CENSUS"),
        ({"m": m, "e": e, "k": fronts[(m, e)] + 2}, None),   # even: no coverage
        ({"m": 5, "e": 0, "k": 12345}, None),                # not carried
    ]


def selftest():
    banner("STAGE", ["prime-power-sums selftest -- " + CONFIG_KEY])
    ok = True
    for mod, name in ((ref, "oracle"), (cpu, "cpu"), (psum_gpu, "gpu"),
                      (psum_gpu2, "gpu2"), (model, "model")):
        for g in mod.GATES:
            good, msg = g()
            ok &= good
            print(("PASS " if good else "FAIL ") + msg)

    fronts = {fam: ref.FAMILIES[fam]["frontier"] for fam in ref.TARGETS}
    fronts[CENSUS_FAMILY] = CENSUS_FRONTIER
    good, msg = drills.event_kind_drill(
        lambda r: event_kind(r, fronts), _event_cases())
    ok &= good
    print(("PASS " if good else "FAIL ") + msg)

    for good, msg in drills.standard(pool_factory=None):
        ok &= good
        print(("PASS " if good else "FAIL ") + msg)

    good, msg = _canary_hunt()
    ok &= good
    print(("PASS " if good else "FAIL ") + msg)
    good, msg = _protocol_drill()
    ok &= good
    print(("PASS " if good else "FAIL ") + msg)
    good, msg = _resume_drill()
    ok &= good
    print(("PASS " if good else "FAIL ") + msg)

    print()
    log("STAGE", "ALL GREEN" if ok else "NOT GREEN -- do not run the campaign")
    return 0 if ok else 1


def _canary_hunt():
    """A dedicated rediscovery mini-hunt: the production engine, cold, must
    find published terms in its path."""
    eng = psum_gpu2.GpuSweep2(ref.ALL_FAMILIES, seg=1 << 20, run=16)
    hits, st = eng.run(4_000_000)
    want = set()
    for fam in ref.TARGETS:
        for k in ref.FAMILIES[fam]["terms"]:
            if 1 < k <= st.k:
                want.add((fam[0], fam[1], k))
    got = set(hits)
    missing = sorted(want - got)
    if missing:
        return False, (f"canary hunt: the engine MISSED published terms "
                       f"{missing[:4]} -- a stream that cannot find what is "
                       f"known may not report what is unknown")
    if len(want) < 6:
        return False, f"canary hunt: only {len(want)} knowns in path -- weak"
    return True, (f"canary hunt: the production engine rediscovered all "
                  f"{len(want)} published terms below k = {st.k:,}, cold")


def _protocol_drill():
    """The discovery protocol must REJECT a fake claim and ACCEPT a genuine
    one -- both directions, every selftest."""
    fam = (11, 0)
    p_hi = ref._nth_prime_bound(500000)
    eng = cpu.CpuSweep((fam,), seg=1 << 16)
    hits, _ = eng.run(p_hi)
    real = [k for m, e, k in hits if k > 1]
    if not real:
        return False, "protocol drill: no genuine hit available to accept"
    k = real[-1]
    start = cpu.State([fam[0]])
    found, cap = rederive(fam, k, start, p_hi)
    ok_true, legs = verify(fam, k, cap, engine_claim=found)
    if not ok_true:
        return False, (f"protocol drill: REJECTED the genuine term k = {k} "
                       f"(legs {legs})")
    found_f, cap_f = rederive(fam, k + 2, start, p_hi)
    ok_fake, _ = verify(fam, k + 2, cap_f, engine_claim=found_f)
    if ok_fake:
        return False, f"protocol drill: ACCEPTED the fake claim k = {k + 2}"
    return True, (f"protocol drill: accepted the genuine k = {k:,} and "
                  f"rejected the fabricated k = {k + 2:,}")


def _resume_drill():
    """A split campaign equals an unsplit one, through the checkpoint's own
    serialization (not just the engine's state object)."""
    fams = ((11, 0), (12, 1))
    whole, st_w = cpu.CpuSweep(fams, seg=1 << 16).run(2_000_000)
    a, st_a = cpu.CpuSweep(fams, seg=1 << 16).run(900_000)
    round_trip = cpu.State.from_json(st_a.to_json())
    if round_trip != st_a:
        return False, "resume drill: the checkpoint round trip lost state"
    b, st_b = cpu.CpuSweep(fams, seg=1 << 16).run(2_000_000, state=round_trip)
    if sorted(a + b) != sorted(whole) or st_b != st_w:
        return False, (f"resume drill: split stream {len(a) + len(b)} hits "
                       f"!= unsplit {len(whole)}")
    return True, (f"resume drill: split-through-the-checkpoint stream and "
                  f"state are identical to the unsplit run ({len(whole)} "
                  f"hits)")


# ------------------------------------ cli -----------------------------------

def _status():
    st = checkpoint.load(CKPT, CONFIG_KEY, warn=lambda m: log("STAGE", m))
    if not st:
        log("STAGE", "no checkpoint for this configuration")
        return 0
    state = cpu.State.from_json(st["state"])
    census = {int(k): int(v) for k, v in st.get("census", {}).items()}
    log("STATUS", f"p = {state.p:,}  k = {state.k:,}  "
                  f"{census_str(census, min(census or [1]), max(census or [1]))}"
                  f"  finds {st.get('discoveries', 0)}  "
                  f"elapsed {st.get('elapsed', 0) / 3600:.2f} h  "
                  f"saved {st.get('saved')}")
    for key, ks in sorted(st.get("found", {}).items()):
        log("STATUS", f"  found {key}: {ks}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and stop")
    ap.add_argument("--status", action="store_true",
                    help="print the checkpoint's position and stop")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this prime-line depth (default: run to the "
                         "engine ceiling 2^62)")
    ap.add_argument("--stop-on-discovery", action="store_true",
                    help="checkpoint and exit as soon as a find is verified")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore any existing checkpoint and sweep from p = 2")
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (default 30)")
    ap.add_argument("--gpu-yield-ms", type=int, default=0,
                    help="idle the device this long after every segment; "
                         "10 ms costs about 1%% of rate and noticeably "
                         "smooths desktop interactivity")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 25 (about 3%% of rate)")
    args = ap.parse_args(argv)
    if args.gentle and not args.gpu_yield_ms:
        args.gpu_yield_ms = 25
    if args.to:
        args.to = int(args.to)

    if args.selftest:
        return selftest()
    if args.status:
        return _status()

    camp = Campaign(args)
    if not args.fresh and camp.load():
        log("STAGE", f"resumed from checkpoint at p = {camp.state.p:,}")
    elif args.fresh:
        log("STAGE", "--fresh: starting the sweep at p = 2")
    return camp.run()


if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
