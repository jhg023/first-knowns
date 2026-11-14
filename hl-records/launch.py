# launch.py -- THE CAMPAIGN for A331940 (owner-started; see README.md).
#
# A331940: addends k > 0 such that the polynomial x^2 + x + k produces a
# record of its Hardy-Littlewood constant C.  Eleven terms are known
# (..., 239621, 247757) and the entry says a(12) > 3*10^6.
#
#   python launch.py --selftest    the gate battery (never sweeps new line)
#   python launch.py --status      read the checkpoint; writes nothing
#   python launch.py               THE HUNT -- the owner's command only
#       --to K                     stop at k = K (opt-in depth cap)
#       --stop-on-discovery        stop once THIS RUN confirms a new record
#       --fresh                    discard the checkpoint, start at k = 1
#       --heartbeat S              [STATUS] every S seconds (default 30)
#       --gpu-yield-ms N           idle the device N ms after every window
#                                  (costs N / window time: ~1% per 10 ms at
#                                  k = 10^10, less above)
#       --gentle                   idle 10% of each window's time (~9%)
#       --no-health                skip the sampled independent recounts
#       --verify-workers N         at most N processes for a find's
#                                  confirmations (default 12; 1 = none: a
#                                  find at k = 2*10^10 then takes ~6 min
#                                  instead of ~35 s, the sweep waiting)
#
# WHAT A RUN DOES.  One line, k = 1, 3, 5, ... in order, no wheel (README:
# no congruence on k is provable).  For a window of 2^23 k the GPU engine
# first proves, for all but about one k in a thousand, a lower bound of
# the class number of the fundamental discriminant of 1 - 4k large enough
# that the rigorous rule (hlc_search.py) drops k whatever its count is --
# the class-group prefilter -- then counts T = 3H(4k - 1) for the rest by
# reduced forms, dropping most of them on a partial count, and keeps the
# survivors of the rule.  Every k it drops has C(k) <= floor BY A PROVED
# BOUND OR A COUNTED CLASS NUMBER, the floor being min(7.5, the standing
# record).  The host
# turns each survivor's count into an exact interval for C and classifies
# it: a record (DISCOVERY), within 1% below the record (NEAR), or a census
# count in its bin of 0.25 from 7.5.
#
# OPENINGS (CONVENTIONS "the default is the fastest correct configuration
# at every opening").  There is ONE family, ONE engine configuration and no
# filter that follows the frontier: the device floor is 7.5 from k = 55663
# on, whatever is found.  The openings are therefore heights, not filters:
#   fresh start, k = 1          windows grow from 2^11 to 2^22 of m while
#                               the floor ramps through a(1)..a(8)
#   any resume, any height      the same engine; BENCHMARKS.md has the
#                               measured rate at each decade (2.6e7 k/s at
#                               3*10^11, 1.8e7 at 10^12, 1.2e7 at 3*10^12)
# and score.py freezes a shape at 10^8 (the opening band), at 3*10^11 and
# 10^12 (earlier headlines) and at 3*10^12 (the band that runs for days).
#
# CANARIES.  The campaign starts at k = 1 and must rediscover a(1)..a(11)
# as records, in order, with the table's C; find NO record in
# (247757, 3*10^6] (the entry's bound); and meet Fung & Williams' published
# discriminants above that with their published C.  Any miss is an [ALARM]
# and exit 2: a stream that cannot find what is known may not report what
# is not.
#
# ASCII-only log; Ctrl+C is a normal exit (boundary checkpoint, one line,
# exit 130, no traceback).

import argparse
import concurrent.futures
import contextlib
import copy
import math
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from huntlib.hlog import log, banner, Heartbeat               # noqa: E402
from huntlib.hostcost import HostCost                         # noqa: E402
from huntlib import checkpoint, evidence, hostcost, shutdown  # noqa: E402
from huntlib import pool as hpool                             # noqa: E402
from huntlib.rungs import Ladder, LiveLadder, eta_str         # noqa: E402

import hlc_reference as ref                                   # noqa: E402
import hlc_search as cpu                                      # noqa: E402
import hlc_model as model                                     # noqa: E402

SEQUENCE = "A331940"
FORMS = "x^2 + x + k"
CKPT = str(HERE / "campaign_checkpoint.json")
EVID_DIR = str(HERE / "evidence")
LEDGER_NAME = "hlc_discoveries.json"
# The key names what a cursor CLAIMS: every odd k below it decided -- dropped
# on a proved bound C(k) <= the floor (a lower bound of its class number
# from the class-group prefilter or a prefix of the sparse count, or its
# exact count, against the survivor rule with these constants), or
# classified exactly.  Engine v3's rule bounds E(k) with the local Euler
# factors at p <= 251 (rule=p251-local) where v1 and v2 used pi^2/8
# (rule=p251): it drops more k, but only k with C(k) <= the floor, so the
# census, the near events and the records below a cursor are the same
# under both and a v1 or v2 cursor covers the IDENTICAL line -- accepted as
# it stands.  Only the raw survivor count changes meaning; an inherited
# one is kept apart (survivors_by_rule) and the count restarts.  Engine
# v4 (the ceiling raised from 10^13 to 10^18) runs v3's rule and v3's
# decisions on every window below 2^46 -- the per-window constants equal
# v3's there and the wider arithmetic is exact where the narrow one was --
# so a v3 cursor covers the identical line, survivor count included.
CONFIG_KEY = (f"{SEQUENCE}|engine=v4-classgroup-sparse-count-wide|"
              f"floor={cpu.CENSUS_FLOOR}|rule=p251-local")
RULE = "p251-local"
KEY_V3 = (f"{SEQUENCE}|engine=v3-classgroup-sparse-count|"
          f"floor={cpu.CENSUS_FLOOR}|rule=p251-local")
KEY_V2 = (f"{SEQUENCE}|engine=v2-classgroup-three-squares|"
          f"floor={cpu.CENSUS_FLOOR}|rule=p251")
KEY_V1 = (f"{SEQUENCE}|engine=v1-three-squares|"
          f"floor={cpu.CENSUS_FLOOR}|rule=p251")
CURSOR = checkpoint.CursorPolicy(CKPT, CONFIG_KEY,
                                 accept=(KEY_V3, KEY_V2, KEY_V1))
K_CEIL = cpu.K_CEIL         # 10^18 (engine v4); hlc_gpu.k_ceil() agrees (P0)
# A find's confirmations (OPTIMIZATION_LOG.md round 3): the analytic leg's
# ~sqrt(4k) terms and the enumeration of forms split into chunks over a
# short-lived pool while this process does the device recount.  Sized from
# the measured cost (hlc_search.confirm_seconds), one process per
# VERIFY_TARGET_S of it, at most VERIFY_WORKERS: per-worker efficiency
# measured 1.00 / 0.97 / 0.95 / 0.85 at 4 / 8 / 12 / 16, so 12 is where the
# machine stops paying.  The sweep waits for the confirmations, so these
# cores are taken from nothing the hunt is doing; the pool exists only for
# the minute or so a find takes.
VERIFY_WORKERS = 12
VERIFY_TARGET_S = 20.0
HEALTH_S = 20.0             # seconds between sampled independent recounts
SLOW_HOST_S = 5.0           # a host step this long gets a [WARN] (hostcost)
SEG_TARGET_S = 3.0          # a checkpoint segment is about this long
LITERATURE = [((1 - D) // 4, 2 * float(c)) for D, c in cpu.LITERATURE
              if (1 - D) // 4 > ref.SEARCHED_ABOVE]


class CampaignAlarm(RuntimeError):
    """A canary missed, a leg disagreed, a count was not a class number:
    an engine bug by definition.  The campaign halts (exit 2)."""


def _health_task(n):
    """Pool task: the analytic 3H(n) of one sampled n (hlc_search)."""
    t, frac = cpu.hurwitz3_analytic(n)
    return int(n), int(t), float(frac)


def pool_factory(workers):
    return concurrent.futures.ProcessPoolExecutor(
        max_workers=int(workers), initializer=hpool.worker_init,
        initargs=("numpy", "hlc_search"))


def confirm_pool_factory(workers):
    return concurrent.futures.ProcessPoolExecutor(
        max_workers=int(workers), initializer=hpool.worker_init,
        initargs=("numpy", "gmpy2", "mpmath", "sympy", "hlc_search"))


def confirm_workers(k, digits, cap=VERIFY_WORKERS):
    """Processes for the CPU legs of a find (or an analytic resolve) at k:
    one per VERIFY_TARGET_S of their measured single-core cost, 1 to cap."""
    est = cpu.confirm_seconds(k, digits)
    return max(1, min(int(cap), math.ceil(est / VERIFY_TARGET_S)))


@contextlib.contextmanager
def confirm_pool(workers):
    """A burst pool of `workers` processes (huntlib.pool.burst: terminated
    at once on Ctrl+C), or None when one process is all the work wants."""
    if workers <= 1:
        yield None
        return
    with hpool.burst(confirm_pool_factory, workers) as pool:
        yield pool


def fresh_state():
    return {"key": CONFIG_KEY, "next_k": 1, "terms": [], "census": {},
            "near": 0, "survivors": 0, "finds": 0, "passed": [],
            "odds_passed": [], "lit_seen": [], "clock_s": 0.0,
            "health_checked": 0, "decade": 0}


class Campaign:
    def __init__(self, engine, ckpt=CKPT, evid_dir=EVID_DIR, known=None,
                 searched_above=None, literature=None, digits=34,
                 stop_on_discovery=False, to=None, heartbeat=30.0,
                 gpu_yield_ms=0.0, gentle=False, pool=None, fresh=False,
                 say=log, announce=banner, record_override=None,
                 verify_workers=VERIFY_WORKERS):
        self.e = engine
        self.verify_workers = max(1, int(verify_workers))
        self.ckpt = ckpt
        self.policy = CURSOR.at(ckpt)
        self.evid_dir = evid_dir
        self.ledger = os.path.join(evid_dir, LEDGER_NAME)
        self.known = list(ref.KNOWN if known is None else known)
        self.searched_above = (ref.SEARCHED_ABOVE if searched_above is None
                               else searched_above)
        self.literature = dict(LITERATURE if literature is None
                               else literature)
        self.digits = digits
        self.stop_on_discovery = stop_on_discovery
        self.limit = min(K_CEIL, int(to)) if to else K_CEIL
        self.interval = float(heartbeat)
        self.yield_s = float(gpu_yield_ms) / 1000.0
        self.gentle = gentle
        self.pool = pool
        self.say, self.announce = say, announce
        self.record_override = record_override
        self.found_this_run = False          # the --stop-on-discovery latch
        self.host_s = 0.0
        self.wall0 = time.time()
        self.win_s = 0.0
        self._health = None
        self._health_t = time.time()
        self._last_save = 0.0
        self._wrote_evidence = False
        self.hb = None
        self.hc = HostCost(say=say, warn_s=SLOW_HOST_S)
        st = None
        if not fresh:
            st, _kind = self.policy.load(warn=lambda m: self.say("WARN", m))
        if st is not None and st.get("key") != CONFIG_KEY:
            # an inherited cursor (the same line): take it under this key,
            # and keep the raw survivor count of its rule apart -- the
            # rules differ in what they hand the host, not in what is found
            old = st["key"].rsplit("rule=", 1)[-1]
            if old != RULE:
                by = st.setdefault("survivors_by_rule", {})
                by[old] = by.get(old, 0) + st["survivors"]
                st["survivors"] = 0
            st["key"] = CONFIG_KEY
        self.resumed = st is not None
        self.st = st if st is not None else fresh_state()
        self.boundary = copy.deepcopy(self.st)
        self._lad = LiveLadder(self._build_ladder)

    # ------------------------------------------------------------ frontier
    def frontier(self):
        return len(self.st["terms"])

    def rec(self):
        if self.record_override is not None:
            return self.record_override
        if not self.st["terms"]:
            return None
        t = self.st["terms"][-1]
        return (t["k"], t["C_lo"], t["C_hi"])

    def _build_ladder(self, frontier, rec_k):
        rec = self.rec()
        cur = max(self.st["next_k"], self.searched_above)
        if rec is None or frontier < len(self.known):
            return Ladder([], ceiling=K_CEIL), 0.0, cur
        preds = model.predictions(frontier, rec[1], cur, n_ahead=4,
                                  ceiling=K_CEIL)
        return (Ladder.from_predictions(preds, ceiling=K_CEIL),
                model.tail(rec[1]), cur)

    def ladder(self):
        rec = self.rec()
        return self._lad.get(self.frontier(), rec[0] if rec else 0)

    # -------------------------------------------------------------- events
    def _alarm(self, msg):
        self.say("ALARM", msg)
        raise CampaignAlarm(msg)

    def _bump(self, lo):
        if lo >= cpu.CENSUS_FLOOR:
            b = str(cpu.bin_of(lo))
            self.st["census"][b] = self.st["census"].get(b, 0) + 1

    def handle(self, k, t):
        """Classify one survivor (k ascending within the line)."""
        st = self.st
        st["survivors"] += 1
        rec = self.rec()
        try:
            kind, lo, hi, hD, P = cpu.classify(k, t, rec)
        except ArithmeticError as ex:
            self._alarm(f"k = {k}: {ex} -- the device count is not a "
                        f"class number")
        if P > cpu.P_CHECK:            # a deep tier: counted, in [STATUS]
            self.hc.path(f"tier2^{P.bit_length() - 1}")
        if kind == "UNRESOLVED":
            kind, lo, hi = self._resolve(k, rec)
        if kind in (None, "TIE"):
            if kind == "TIE":
                self._bump(lo)
            return
        self._bump(lo)
        if k in self.literature:
            c = self.literature[k]
            if not lo - 1.01e-7 <= c <= hi + 1.01e-7:
                lo2, hi2 = cpu.C_bounds(4 * k - 1, hD, cpu.P_CHECK)
                if not lo2 - 1.01e-7 <= c <= hi2 + 1.01e-7:
                    self._alarm(f"literature canary k = {k}: C in "
                                f"[{lo2:.8f}, {hi2:.8f}], published {c:.7f}")
            st["lit_seen"].append(k)
            self.say("CANARY-GOLD", f"k = {k}: C = {c:.7f} as published by "
                                    f"Fung & Williams (h = {hD})")
        if kind == "NEAR":
            t2, frac = cpu.hurwitz3_analytic(4 * k - 1)
            if t2 != t:
                self._alarm(f"k = {k}: device count {t}, analytic {t2}")
            st["near"] += 1
            self.say("NEAR", f"k = {k}: C in [{lo:.6f}, {hi:.6f}], within "
                             f"{100 * cpu.NEAR_MARGIN:.0f}% below the record "
                             f"{rec[1]:.6f} at k = {rec[0]} (near #"
                             f"{st['near']} of the campaign; count verified "
                             f"analytically) -- short of a("
                             f"{self.frontier() + 1})")
        elif kind == "DISCOVERY":
            self._record(k, t, lo, hi, hD, rec)

    def _record_C(self, rec):
        """The standing record's C as an mpf: the 34 digits its discovery
        stored when there are any (never recomputed -- it was, on every
        call, until 2026-11-11), else 30 digits computed now."""
        import mpmath
        if rec is None:
            return mpmath.mpf(0)
        for t in reversed(self.st["terms"]):
            if t["k"] == rec[0] and t.get("C"):
                return mpmath.mpf(t["C"])
        return self._highprec(rec[0])

    def _resolve(self, k, rec):
        """An interval the prime tiers could not separate from the record
        or from a cut: decide it at 30 digits.  Minutes above k = 10^10 --
        counted as a slow path, named to the heartbeat, and priced in
        OPTIMIZATION_LOG.md 2.13 (once in thousands of windows since the
        tiers reach 2^26)."""
        import mpmath
        self.hc.path("analytic resolve")
        w = confirm_workers(k, 30, self.verify_workers)
        if self.hb is not None:
            self.hb.doing(f"k = {k}: C is within the last tier's width of a "
                          f"census edge or the record; computing it to 30 "
                          f"digits on {w} process{'es' if w > 1 else ''} "
                          f"(~{cpu.confirm_seconds(k, 30) / w:.0f} s)")
        c = self._highprec(k)
        r = self._record_C(rec)
        if abs(c - r) < mpmath.mpf(10) ** -20:
            self._alarm(f"k = {k}: C agrees with the record at k = {rec[0]} "
                        f"to 20 digits and is not a structural tie")
        cf = float(c)
        kind = ("DISCOVERY" if c > r else cpu.event_kind(cf, float(r)))
        return kind, cf - 1e-12, cf + 1e-12

    def _highprec(self, k, digits=30):
        """C(k) by Cohen's route, its AFE chunked over a burst pool."""
        w = confirm_workers(k, digits, self.verify_workers)
        with confirm_pool(w) as pool:
            return cpu.C_highprec(k, digits=digits, pool=pool,
                                  workers=w)["C"]

    def _record(self, k, t, lo, hi, hD, rec):
        st = self.st
        n = self.frontier() + 1
        if n <= len(self.known):                       # the canary zone
            kk, cs = self.known[n - 1]
            lo, hi = cpu.C_bounds(4 * k - 1, hD, cpu.P_CHECK)
            if k != kk or not (lo - 0.5000001e-5 <= float(cs)
                               <= hi + 0.5000001e-5):
                self._alarm(f"record at k = {k} (C ~ {lo:.5f}) where the "
                            f"entry has a({n}) = {kk} with C = {cs}")
            st["terms"].append({"n": n, "k": k, "C_lo": lo, "C_hi": hi,
                                "h": hD, "kind": "canary"})
            self.say("CANARY-GOLD", f"a({n}) = {k} rediscovered: C = "
                                    f"{(lo + hi) / 2:.5f} (table {cs}), "
                                    f"h = {hD}")
            return
        if k <= self.searched_above:
            self._alarm(f"a record at k = {k} contradicts the entry's bound "
                        f"a({n}) > {self.searched_above}")
        self.hc.expect("discovery verification")
        w = confirm_workers(k, self.digits, self.verify_workers)
        eta = cpu.confirm_seconds(k, self.digits) / w
        self.say("STAGE", f"candidate record at k = {k} (C ~ {lo:.6f} over "
                          f"{rec[1]:.6f}): running the three confirmations "
                          f"on {w} process{'es' if w > 1 else ''} "
                          f"(~{eta:.0f} s)")
        self.hb.doing(f"verifying a candidate record at k = {k} (three "
                      f"confirmations, {w} process{'es' if w > 1 else ''}, "
                      f"~{eta:.0f} s)")
        with confirm_pool(w) as pool:
            ok, ev = cpu.verify_find(k, t, rec, digits=self.digits,
                                     recount=self.e.recount, pool=pool,
                                     workers=w)
        if not ok:
            self._alarm(f"k = {k}: the three confirmations DISAGREE: {ev}")
        import mpmath
        C = mpmath.mpf(ev["C"])
        cf = float(C)
        # C as the entry's own table prints it: 5 decimals
        from decimal import Decimal
        c_table = str(Decimal(ev["C"]).quantize(Decimal("0.00001")))
        out = evidence.header(SEQUENCE, FORMS, "k", k, [n])
        out.update({
            "index": n, "settles": [n], "C": ev["C"],
            "C_table": c_table,
            "C_error_bound": ev["C_error_bound"],
            "margin_over_previous": ev["margin_over_previous"],
            "previous_record": ev["previous_record"],
            "verification": "3-way",
            "leg1_engine": ev["leg1_engine"],
            "leg2_analytic": ev["leg2_analytic"],
            "leg3_class_number": ev["leg3_class_number"],
            "least_claim": {
                "swept_from_k": 1, "swept_to_k": k,
                "basis": ("every odd k below this one was taken in order by "
                          "the engine and either dropped by the survivor "
                          "rule (a proved lower bound of its class number "
                          "-- from the class group, or the counted class "
                          "number itself -- puts C <= the floor, itself <= "
                          "the standing record) or classified exactly on "
                          "the host from its counted class number and found "
                          "not to exceed the standing record; even k has "
                          "C = 0"),
                "conditional_on": "nothing (no GRH; Gauss's three-squares "
                                  "theorem, the class number formula, "
                                  "composition of forms and genus theory)",
                "canaries": (f"a(1)..a({len(self.known)}) rediscovered in "
                             f"order by this campaign"),
                "engine": CONFIG_KEY},
            "found_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        evidence.record(out, self.evid_dir, f"hlc_record_a{n}_k{k}.json",
                        self.ledger, key="k", label="DISCOVERY")
        lad_before = self.ladder()[0]
        st["terms"].append({"n": n, "k": k, "C_lo": cf - 1e-12,
                            "C_hi": cf + 1e-12, "h": hD,
                            "kind": "discovery", "C": ev["C"],
                            "C_table": c_table})
        st["finds"] += 1
        self.found_this_run = True
        self._wrote_evidence = True
        self.announce("DISCOVERY", [
            f"{SEQUENCE} a({n}) = {k}",
            f"x^2 + x + {k}: C = {ev['C']}  (table: {c_table})",
            f"record over a({n - 1}) = {rec[0]} by "
            f"{ev['margin_over_previous']}; h(1 - 4k) = {hD}",
            "verified 3-way: rigorous interval; analytic C (no class "
            "number); second class-number algorithm",
            f"evidence: evidence/hlc_record_a{n}_k{k}.json"])
        retired = lad_before.retired_by(n, n - 1)
        nxt = self.ladder()[0].next_rung(st["next_k"], self.frontier())
        self.say("RUNG", f"a({n}) found: retired {retired or 'no rungs'}; "
                         f"the ladder now aims at a({n + 1})"
                         + (f", next {nxt[0]} at {nxt[1]:.3g}" if nxt else ""))

    # ------------------------------------------------------------ boundary
    def _check_canaries(self):
        pos = self.st["next_k"]
        got = {t["k"] for t in self.st["terms"]}
        for kk, _cs in self.known:
            if kk < pos and kk not in got:
                self._alarm(f"canary MISSED: the sweep passed a(n) = {kk} "
                            f"without finding it")
        for kk in self.literature:
            if kk < pos and kk not in self.st["lit_seen"] \
                    and kk >= self._lit_floor:
                self._alarm(f"literature canary MISSED: k = {kk}")

    def _check_rungs(self):
        st = self.st
        pos = st["next_k"]
        lad, tail, cur0 = self.ladder()
        for lab in lad.newly_passed(pos, self.frontier(), st["passed"]):
            st["passed"].append(lab)
            nxt = lad.next_rung(pos, self.frontier())
            self.say("RUNG", f"passed {lab} "
                             f"({lad.progress_str(pos, self.frontier(), st['passed'])})"
                             + (f" -- next: {nxt[0]} at {nxt[1]:.3g}"
                                if nxt else ""))
        d = int(math.log10(pos)) if pos > 0 else 0
        if d > st["decade"] and d >= 6:
            st["decade"] = d
            self.say("MILESTONE", f"swept every k below 10^{d}: "
                                  f"{cpu.census_str(st['census'])}; "
                                  f"{self.frontier()} terms")
        if tail:
            p = 1.0 - math.exp(-max(pos - cur0, 0) / 2.0 * tail)
            for q in (25, 50, 75, 90):
                tag = f"{self.frontier()}:{q}"
                if p * 100 >= q and tag not in st["odds_passed"]:
                    st["odds_passed"].append(tag)
                    self.say("MILESTONE",
                             f"past the model's {q}% point for a("
                             f"{self.frontier() + 1}) (k = {pos:.4g}); "
                             f"{cpu.census_str(st['census'])}")

    def _health_poll(self):
        if self.pool is None:
            return
        if self._health is not None and self._health[0].done():
            fut, n, t_dev, tabulated, floor = self._health
            self._health = None
            _n, t, frac = fut.result()
            self.st["health_checked"] += 1
            if frac > 0.05 or (tabulated and t != t_dev):
                self._alarm(f"health check FAILED at k = {(n + 1) // 4}: "
                            f"device count {t_dev}, analytic {t}")
            if not tabulated and bool(cpu.survivor_mask(
                    (n - 3) // 8, cpu.np.array([t], dtype=cpu.np.uint32),
                    floor)[0]):
                self._alarm(f"health check FAILED at k = {(n + 1) // 4}: the "
                            f"prefilter dropped it, and its analytic count "
                            f"{t} survives the rule at {floor}")
        if self._health is None and time.time() - self._health_t >= HEALTH_S:
            # one k of the last window, alternately a tabulated count
            # (must equal the analytic class number) and a k the prefilter
            # dropped (its analytic count must be dropped by the rule too);
            # None when the engine's buffers no longer hold that window
            got = self.e.sample(self.st["survivors"] * 2654435761
                                + self.st["next_k"])
            if got is not None:
                self._health_t = time.time()
                n, t_dev, tabulated, floor = got
                self._health = (self.pool.submit(_health_task, n), n, t_dev,
                                tabulated, floor)

    def mark_boundary(self):
        self.st["clock_s"] += time.time() - self._clock_t
        self._clock_t = time.time()
        self.boundary = copy.deepcopy(self.st)

    def save(self, force=False):
        now = time.time()
        if not (force or self._wrote_evidence
                or now - self._last_save >= self.interval):
            return None
        landed = checkpoint.save(self.ckpt, self.boundary)
        if landed:
            self._last_save = now
            self._wrote_evidence = False
        return landed

    def _on_interrupt(self):
        landed = checkpoint.save(self.ckpt, self.boundary)
        what = ("written" if landed else
                "NOT written (file locked; the previous one stands)")
        return (f"checkpoint {what} at the last segment boundary, "
                f"k = {self.boundary['next_k']}")

    # -------------------------------------------------------------- status
    def status_line(self):
        st = self.st
        pos = st["next_k"]
        rate = self.hb.rate() if self.hb else 0.0
        lad, tail, cur0 = self.ladder()
        n = self.frontier()
        bits = [f"k {pos:.5g}", f"{rate:.3g} k/s",
                f"survivors {st['survivors']}", cpu.census_str(st["census"]),
                f"terms {n} (new {st['finds']})", f"near {st['near']}"]
        wall = max(time.time() - self.wall0, 1e-9)
        bits.append(f"host {100 * self.host_s / wall:.1f}% of wall")
        slow = self.hc.status()            # not `tail`: that is the model's
        if slow:
            bits.append(slow)
        if tail:
            p = 1.0 - math.exp(-max(pos - cur0, 0) / 2.0 * tail)
            bits.append(f"P(a({n + 1}) by now) {100 * p:.0f}%")
        nxt = lad.next_rung(pos, n)
        if nxt and rate > 0:
            # the measured rate law's clock from here to the rung, scaled
            # by this run's own rate (a closed form: no model query)
            rem = model.clock_seconds(nxt[1], pos) * model.rate_at(pos)
            bits.append(f"next: {nxt[0]} at {nxt[1]:.3g} "
                        f"(ETA {eta_str(rem, rate)})")
        elif nxt:
            bits.append(f"next: {nxt[0]} at {nxt[1]:.3g}")
        s = " | ".join(bits)
        stall = self.hb.stalled() if self.hb else None
        if stall:
            s += (f" -- no segment closed since the last status: "
                  f"{stall[0]} for {stall[1]:.0f}s")
        return s

    # ----------------------------------------------------------------- run
    def window(self):
        st = self.st
        m0 = (st["next_k"] - 1) // 2
        m_end = self.limit // 2
        W = min(self.e.W, max(2048, m0), m_end - m0)
        rec = self.rec()
        floor = 0.0 if rec is None else min(cpu.CENSUS_FLOOR,
                                            rec[1] * (1 - 1e-9))
        t0 = time.time()
        ks, ts = self.e.survivors(m0, W, floor)
        t1 = time.time()
        for k, t in zip(ks.tolist(), ts.tolist()):
            with self.hc.item(f"classifying k = {k}"):
                self.handle(k, t)
        st["next_k"] = 2 * (m0 + W) + 1
        self._last_m0, self._last_W = m0, W
        self.host_s += time.time() - t1
        self.win_s = t1 - t0
        pause = self.yield_s + (0.1 * self.win_s if self.gentle else 0.0)
        if pause > 0:
            time.sleep(pause)

    def run(self):
        st = self.st
        self._lit_floor = max(st["next_k"], self.searched_above)
        self._clock_t = time.time()
        self.hb = Heartbeat(self.interval)
        self.hc.hb = self.hb
        self.hb.mark(st["next_k"])
        self.hb.start(self.status_line)
        cb = shutdown.on_interrupt(self._on_interrupt)
        why = "reached the engine ceiling (the last rung)"
        try:
            while True:
                if st["next_k"] >= self.limit:
                    if self.limit < K_CEIL:
                        why = f"reached --to {self.limit}"
                    break
                if self.stop_on_discovery and self.found_this_run:
                    why = ("--stop-on-discovery: this run confirmed a new "
                           "record")
                    break
                nwin = 1 if self.win_s <= 0 else max(
                    1, min(64, int(SEG_TARGET_S / max(self.win_s, 1e-3))))
                self.hb.doing(f"sweeping from k = {st['next_k']}")
                for _ in range(nwin):
                    if st["next_k"] >= self.limit:
                        break
                    self.window()
                    if self.found_this_run and self.stop_on_discovery:
                        break
                self._check_canaries()
                self._check_rungs()
                self._health_poll()
                self.mark_boundary()
                self.hb.mark(st["next_k"])
                self.save()
        finally:
            self.hb.stop()
            try:
                shutdown._callbacks.remove(cb)
            except ValueError:
                pass
        if self._health is not None:           # the sample in flight counts
            self.hb.doing("finishing the last sampled recount")
            self._health[0].result(timeout=300)
            self._health_t = float("inf")
            self._health_poll()
            self.mark_boundary()
        landed = self.save(force=True)
        self.say("STAGE", f"stopped: {why}; every odd k < {st['next_k']} "
                          f"swept; {self.frontier()} terms "
                          f"({st['finds']} new); checkpoint "
                          f"{'written' if landed else 'DEFERRED (locked)'}")
        return 0


# --------------------------------------------------------------- commands
def print_status():
    st, kind = CURSOR.load(warn=lambda m: log("WARN", m))
    if st is None:
        print("no checkpoint: a fresh campaign starts at k = 1 and "
              "rediscovers a(1)..a(11) first")
        return 0
    print(f"{SEQUENCE}: {FORMS}   [{st['key']}]")
    print(f"swept: every odd k < {st['next_k']}  ({st['clock_s'] / 3600:.2f}"
          f" h of campaign clock)")
    for t in st["terms"]:
        c = (f"C = {t['C']}  (table: {t['C_table']})" if t.get("C_table")
             else f"C in [{t['C_lo']:.8f}, {t['C_hi']:.8f}]")
        print(f"  a({t['n']}) = {t['k']}   {c}   h = {t['h']}   "
              f"({t['kind']})")
    print(f"survivors {st['survivors']}; {cpu.census_str(st['census'])}; "
          f"near {st['near']}; health checks {st['health_checked']}")
    for rule, n in sorted(st.get("survivors_by_rule", {}).items()):
        print(f"  (+ {n} survivors handed over under rule={rule}, before "
              f"the local Euler factors)")
    return 0


def campaign(args, policy=CURSOR, evid_dir=EVID_DIR, say=log,
             announce=banner):
    """The owner's entry point.  `policy`, `evid_dir`, `say` and `announce`
    exist so that the selftest can drive THIS function, unchanged, over the
    canary range against a scratch checkpoint."""
    import hlc_gpu
    from huntlib.gpu import device_report
    policy.refuse_mismatch(
        fresh=args.fresh,
        describe=lambda s: f"cursor at k = {s.get('next_k')}")
    if not hlc_gpu.available():
        say("ALARM", "no CUDA device: this campaign runs on the GPU engine")
        return 2
    e = hlc_gpu._engine()
    say("STAGE", f"{SEQUENCE}: records of the Hardy-Littlewood constant C "
                 f"of {FORMS}")
    say("STAGE", device_report(e.held_bytes()))
    model.tail_table()
    with pool_factory(1) as pool:
        hpool.ramp(pool, 1)
        c = Campaign(e, ckpt=policy.path, evid_dir=evid_dir,
                     stop_on_discovery=args.stop_on_discovery,
                     to=args.to, heartbeat=args.heartbeat,
                     gpu_yield_ms=args.gpu_yield_ms, gentle=args.gentle,
                     pool=None if args.no_health else pool,
                     fresh=args.fresh, say=say, announce=announce,
                     verify_workers=getattr(args, "verify_workers",
                                            VERIFY_WORKERS))
        say("STAGE", ("resuming" if c.resumed else "fresh start") +
            f" at k = {c.st['next_k']}; {c.frontier()} terms; ceiling "
            f"k = 10^{round(math.log10(K_CEIL))}; one pool worker for "
            f"sampled recounts; a find's confirmations on up to "
            f"{c.verify_workers} process"
            f"{'es' if c.verify_workers > 1 else ''}")
        try:
            return c.run()
        except CampaignAlarm:
            checkpoint.save(c.ckpt, c.boundary)
            say("STAGE", "HALTED on an alarm; the checkpoint stands at the "
                         "last good segment boundary; exit 2")
            return 2


# ------------------------------------------------------------ the selftest
def _quiet(lines):
    return lambda tag, msg: lines.append((tag, msg if isinstance(msg, str)
                                          else " / ".join(msg)))


def drills(engine):
    """The launcher's own drills, as [(ok, msg)]."""
    import tempfile
    from huntlib import drills as hdrills
    out = []
    # the discovery-once taxonomy
    out.append(hdrills.event_kind_drill(
        lambda c: cpu.event_kind(c, 8.24741),
        [(8.5, "DISCOVERY"), (8.2, "NEAR"), (7.9, "CENSUS"), (7.2, None),
         (8.24741, "NEAR"), (7.5, "CENSUS")]))
    # the evidence header speaks the entry's letters
    ev = evidence.header(SEQUENCE, FORMS, "k", 247757, [11])
    ev["settles"] = [11]
    good = evidence.check_names(ev, "k")[0]
    bad = evidence.check_names(dict(ev, forms="n^2 + n + A"), "k")[0]
    gn = evidence.gate_names(EVID_DIR, "k")
    out.append((good and not bad and gn[0],
                "evidence names: the record carries a(n) under `k` beside "
                "forms = 'x^2 + x + k' with its oeis_terms map; a `forms` "
                "in other letters is refused; " + gn[1]))
    tmp = tempfile.mkdtemp(prefix="hlc-drill-")
    try:
        # (a) the campaign loop over known territory: canaries, census,
        #     resume = unsplit
        lines = []
        kw = dict(say=_quiet(lines), announce=_quiet(lines), heartbeat=3600)
        a = Campaign(engine, ckpt=os.path.join(tmp, "a.json"),
                     evid_dir=os.path.join(tmp, "ev-a"), to=300001, **kw)
        a.run()
        b1 = Campaign(engine, ckpt=os.path.join(tmp, "b.json"),
                      evid_dir=os.path.join(tmp, "ev-b"), to=100001, **kw)
        b1.run()
        b2 = Campaign(engine, ckpt=os.path.join(tmp, "b.json"),
                      evid_dir=os.path.join(tmp, "ev-b"), to=300001, **kw)
        b2.run()
        same = all(a.st[f] == b2.st[f] for f in
                   ("next_k", "terms", "census", "near", "survivors"))
        ks = [t["k"] for t in a.st["terms"]]
        gold = sum(1 for tag, _ in lines if tag == "CANARY-GOLD")
        out.append((ks == ref.KNOWN_TERMS and same and b2.resumed
                    and a.st["finds"] == 0 and gold == 22,
                    f"campaign drill: the loop over k < 300001 rediscovers "
                    f"a(1)..a(11) as canaries and nothing else; a run split "
                    f"at k = 100001 and resumed ends in the identical state "
                    f"({a.st['survivors']} survivors, "
                    f"{cpu.census_str(a.st['census'])})"))
        # (b) the discovery protocol end to end, and --stop-on-discovery on
        #     the RESUMED case: pretend the entry stopped at a(8)
        lines2 = []
        kw2 = dict(say=_quiet(lines2), announce=_quiet(lines2),
                   heartbeat=3600, known=ref.KNOWN[:8], searched_above=60000,
                   digits=30, stop_on_discovery=True,
                   ckpt=os.path.join(tmp, "c.json"),
                   evid_dir=os.path.join(tmp, "ev-c"), to=300001)
        stops = []
        for _ in range(3):
            c = Campaign(engine, **kw2)
            before = c.st["finds"]
            c.run()
            stops.append((before, c.st["finds"], c.st["terms"][-1]["k"],
                          c.st["next_k"]))
        # 239621 and 247757 share a window, and the stop is taken at the
        # window boundary, so the second run confirms both before it stops.
        s1, s2, s3 = stops
        flow = (s1[:3] == (0, 1, 115721) and s1[3] < 300001
                and s2[:3] == (1, 3, 247757) and s1[3] < s2[3] < 300001
                and s3[:3] == (3, 3, 247757) and s3[3] == 300001)
        names = evidence.gate_names(os.path.join(tmp, "ev-c"), "k")
        led = evidence.load_ledger(os.path.join(tmp, "ev-c", LEDGER_NAME))
        retired = sum(1 for tag, m in lines2 if tag == "RUNG"
                      and "found" in m)
        out.append((flow and names[0]
                    and len(led) == 3 and retired == 3
                    and all(r["verification"] == "3-way" for r in led)
                    and led[2]["oeis_terms"] == {"11": 247757}
                    and [r["C_table"] for r in led] == [cs for _, cs in
                                                        ref.KNOWN[8:]],
                    "discovery drill (the entry cut back to a(8)): 115721, "
                    "239621 and 247757 are each confirmed 3-way and "
                    "evidenced under `k`; --stop-on-discovery stops a fresh "
                    "run at its first find, a run resumed with 1 prior find "
                    "only after finding its own, and a run resumed with 3 "
                    "sweeps to --to instead of stopping at once; each find "
                    "retires its rungs"))
        # (c) a stream that drops or corrupts a canary must ALARM

        class Bent:
            def __init__(self, e, drop=None, bend=None):
                self.e, self.drop, self.bend, self.W = e, drop, bend, e.W
                self.cnt = e.cnt

            def survivors(self, m0, W, floor):
                ks, ts = self.e.survivors(m0, W, floor)
                keep = ks != self.drop
                ts = ts.copy()
                ts[ks == self.bend] += 3
                return ks[keep], ts[keep]

            def recount(self, k):
                return self.e.recount(k)

            def sample(self, seed):
                return self.e.sample(seed)

        alarms = 0
        for bent in (Bent(engine, drop=27941), Bent(engine, bend=41537)):
            try:
                Campaign(bent, ckpt=os.path.join(tmp, "d.json"),
                         evid_dir=os.path.join(tmp, "ev-d"), to=60001,
                         fresh=True, **kw).run()
            except CampaignAlarm:
                alarms += 1
        out.append((alarms == 2,
                    "canary alarm drill: a stream that drops a(6) = 27941, "
                    "and one whose count at a(7) = 41537 is off by one "
                    "class, both HALT the campaign"))
        # (e) the owner's entry point itself, over the canary range: the
        #     refusal, the device report, the pool ramp, the sampled
        #     recounts and the throttles, against a scratch checkpoint
        global HEALTH_S
        lines3 = []
        pol = CURSOR.at(os.path.join(tmp, "e.json"))
        ns = argparse.Namespace(to=300001, fresh=False, heartbeat=3600,
                                stop_on_discovery=False, gpu_yield_ms=1.0,
                                gentle=True, no_health=False)
        keep, HEALTH_S = HEALTH_S, 0.0
        try:
            rc = campaign(ns, policy=pol, evid_dir=os.path.join(tmp, "ev-e"),
                          say=_quiet(lines3), announce=_quiet(lines3))
        finally:
            HEALTH_S = keep
        st3, _ = pol.load()
        with open(pol.path, "w") as fh:
            fh.write('{"key": "some-other-engine", "next_k": 5}')
        try:
            campaign(ns, policy=pol, evid_dir=os.path.join(tmp, "ev-e"),
                     say=_quiet(lines3), announce=_quiet(lines3))
            refused = False
        except checkpoint.CursorRefused:
            refused = True
        out.append((rc == 0 and st3 is not None and st3["next_k"] == 300001
                    and [t["k"] for t in st3["terms"]] == ref.KNOWN_TERMS
                    and st3["health_checked"] >= 2 and refused,
                    f"entry-point drill: campaign() itself, to k = 300001 on "
                    f"a scratch checkpoint, reports the device, ramps its "
                    f"worker, rediscovers the eleven terms, passes "
                    f"{st3['health_checked'] if st3 else 0} sampled recounts "
                    f"with both throttles on, and refuses a checkpoint "
                    f"written under another key"))
        # (d) the ladder is cached on the frontier; --status never writes
        c = Campaign(engine, **dict(kw2, stop_on_discovery=False))
        b0 = c._lad.builds
        for _ in range(50):
            c.ladder()
            c.status_line() if False else None
        cached = c._lad.builds - b0 == 1
        lad = c.ladder()[0]
        aims = lad.next_rung(c.st["next_k"], c.frontier())
        m0 = os.path.getmtime(kw2["ckpt"])
        st, kind = CURSOR.at(kw2["ckpt"]).load()
        out.append((cached and st is not None and kind == "own"
                    and os.path.getmtime(kw2["ckpt"]) == m0
                    and aims is not None and aims[0].startswith("a(12)"),
                    "wiring drill: fifty ladder reads at a standing frontier "
                    "cost one build; the live ladder aims at the next open "
                    "term; reading the checkpoint does not write it"))
        # (f) a cursor of engine v2 (the universal rule) is inherited: the
        #     line, terms and census carry over, the key becomes v3's, the
        #     raw survivor count is kept apart, and a resumed run goes on
        old = dict(st, key=KEY_V2, survivors=1234)
        old.pop("survivors_by_rule", None)
        mp = os.path.join(tmp, "m.json")
        checkpoint.save(mp, old)
        mc = Campaign(engine, **dict(kw2, ckpt=mp, stop_on_discovery=False,
                                     to=old["next_k"] + 4096))
        moved = (mc.resumed and mc.st["key"] == CONFIG_KEY
                 and mc.st["survivors"] == 0
                 and mc.st["survivors_by_rule"] == {"p251": 1234}
                 and mc.st["next_k"] == old["next_k"]
                 and mc.st["terms"] == old["terms"]
                 and mc.st["census"] == old["census"])
        mc.run()
        st5, kind5 = CURSOR.at(mp).load()
        # an engine-v3 cursor (v3's rule exactly: v4 IS v3 below 2^46) is
        # inherited whole, survivor count included
        v3c = dict(st, key=KEY_V3, survivors=4321)
        v3c.pop("survivors_by_rule", None)
        mp3 = os.path.join(tmp, "m3.json")
        checkpoint.save(mp3, v3c)
        m3 = Campaign(engine, **dict(kw2, ckpt=mp3, stop_on_discovery=False,
                                     to=v3c["next_k"] + 4096))
        kept = (m3.resumed and m3.st["key"] == CONFIG_KEY
                and m3.st["survivors"] == 4321
                and "survivors_by_rule" not in m3.st
                and m3.st["terms"] == v3c["terms"])
        out.append((moved and kind5 == "own" and kept
                    and st5["survivors_by_rule"] == {"p251": 1234}
                    and st5["next_k"] > old["next_k"],
                    "migration drill: an engine-v2 cursor (rule p251) is "
                    "inherited with its line, terms and census, rewritten "
                    "under the current key with its 1234 raw survivors kept "
                    "apart under rule=p251, and the resumed run saves as its "
                    "own; an engine-v3 cursor (the same rule) is inherited "
                    "whole, its 4321 survivors included"))
        # (g) a slow host step is announced with its k and kept in [STATUS]
        #     (huntlib.hostcost; the census-edge stall of 2026-11-11)
        out.append(hostcost.drill())
        lines6, slow = [], []

        class Slow(Campaign):
            def handle(self, k, t):
                if not slow and self.rec() is not None:
                    slow.append(k)
                    time.sleep(0.12)
                return super().handle(k, t)
        sc = Slow(engine, ckpt=os.path.join(tmp, "s.json"),
                  evid_dir=os.path.join(tmp, "ev-s"), to=60001, fresh=True,
                  say=_quiet(lines6), announce=_quiet(lines6),
                  heartbeat=3600)
        sc.hc.warn_s = 0.1
        sc.run()
        warns = [m for tag, m in lines6 if tag == "WARN" and "host step" in m]
        out.append((len(slow) == 1 and len(warns) == 1
                    and f"classifying k = {slow[0]}" in warns[0]
                    and f"k = {slow[0]}" in sc.status_line()
                    and sc.hc.n >= sc.st["survivors"],
                    f"slow-step drill: a survivor whose handling takes 0.12 s "
                    f"against a 0.1 s threshold gets one [WARN] naming it "
                    f"(k = {slow[0] if slow else '-'}), [STATUS] keeps it as "
                    f"the slowest step, and every survivor of the run was "
                    f"timed ({sc.hc.n})"))
        # (h) a find's confirmations on a burst pool give the evidence the
        #     in-process route gives, digit for digit, and Ctrl+C inside a
        #     burst ends it at once (huntlib.pool.burst)
        import json
        t = int(cpu.h3_window((247757 - 1) // 2, 1)[0])
        rec11 = (239621, 7.72930, 7.72934)
        one = cpu.verify_find(247757, t, rec11, digits=30,
                              recount=engine.recount)
        with confirm_pool(3) as pool:
            three = cpu.verify_find(247757, t, rec11, digits=30,
                                    recount=engine.recount, pool=pool,
                                    workers=3)
        same = json.dumps(one, sort_keys=True) == \
            json.dumps(three, sort_keys=True)
        out.append((one[0] and same and confirm_workers(247757, 34) == 1
                    and confirm_workers(21425625701, 34) == VERIFY_WORKERS
                    and confirm_workers(21425625701, 34, cap=1) == 1,
                    "confirmation drill: the three confirmations of a(11) "
                    "on a pool of 3 (AFE in 12 chunks, the enumeration in 3, "
                    "the device recount meanwhile) give the in-process "
                    "evidence to the last digit; a find at a(11)'s height "
                    "stays in one process, one at a(32)'s takes "
                    f"{VERIFY_WORKERS}, and --verify-workers 1 keeps it in "
                    "one"))
        out.append(hpool.burst_drill(confirm_pool_factory))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def selftest():
    import hlc_gpu
    from huntlib import drills as hdrills
    t0 = time.time()
    ok = ref.selftest()
    ok = cpu.selftest() and ok
    ok = hlc_gpu.selftest() and ok
    results = [g() for g in model.GATES]
    if hlc_gpu.available():
        results += drills(hlc_gpu._engine())
    results += hdrills.standard(pool_factory=pool_factory, cursor=CURSOR)
    for good, msg in results:
        print(("PASS " if good else "FAIL ") + msg, flush=True)
        ok = ok and good
    print(("ALL GREEN" if ok else "RED") + f"  ({time.time() - t0:.0f}s)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--to", type=float, default=None)
    ap.add_argument("--stop-on-discovery", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--heartbeat", type=float, default=30.0)
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0)
    ap.add_argument("--gentle", action="store_true")
    ap.add_argument("--no-health", action="store_true")
    ap.add_argument("--verify-workers", type=int, default=VERIFY_WORKERS)
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.status:
        return print_status()
    return campaign(args)


if __name__ == "__main__":
    sys.exit(shutdown.graceful(main))
