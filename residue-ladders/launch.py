# launch.py -- THE CAMPAIGN for the power-residue ladders (owner-started;
# see README.md).
#
#   A002226  Smallest prime p such that first n primes (p_1=2, ..., p_n) are
#            quintic residues mod p.                        (the default)
#   A002227  ... are 7th power residues mod p.
#   A002228  ... are 11th power residues mod p.
#   A060363  ... are 13th power residues mod p.
#   A060364  ... are 17th power residues mod p.
#
#   python launch.py --selftest    the gate battery (never sweeps new line)
#   python launch.py --status      read the checkpoints; writes nothing
#   python launch.py               THE HUNT -- the owner's command only
#       --family A002227           which entry (default A002226)
#       --to P                     sweep every candidate p <= P and stop
#                                  (opt-in depth cap; an exact integer,
#                                  1e16 and 2.5e17 are read exactly)
#       --stop-on-discovery        stop once THIS RUN confirms a new term
#       --fresh                    discard the checkpoint, start at the
#                                  line's first candidate
#       --heartbeat S              [STATUS] every S seconds (default 30)
#       --gpu-yield-ms N           idle the device N ms after every launch
#                                  (a launch is 15-19 ms: N = 1 costs 5-6%)
#       --gentle                   idle 10% of each launch's time (~9%)
#       --no-parity                skip the sampled CPU parity checks
#
# WHAT A RUN DOES.  One line per family: the candidates N = 2*power*j + 1
# in order from j = 1, which holds every prime p with p - 1 divisible by the
# power.  The GPU engine (residue_gpu.py) drops candidates with a small
# prime factor, tests 2^((N-1)/power) == 1 (mod N) on the rest -- for a
# prime that is "2 is a residue", and a composite almost never passes --
# and reads the RUN of each one that passes: how many of 2, 3, 5, 7, ...
# are residues, in order.  It hands the host every candidate whose run is
# at least the census floor.  The host proves each one prime (deterministic
# Miller-Rabin), recomputes its run with plain integer arithmetic, and
# classifies it against the frontier f (the largest index settled):
#
#     run > f      DISCOVERY: p = a(f+1) = ... = a(run), each logged once
#     run = f      NEAR: one prime short of a(f+1); one line, no file
#     run < f      CENSUS: counted, from the floor f - depth + 1 up
#
# A fresh campaign starts at the line's first candidate and re-derives the
# entry's published terms itself; those are the CANARIES, and a least-p
# claim here rests on this campaign's own sweep from j = 1, not on anyone's
# search limit.
#
# OPENINGS (CONVENTIONS "the default is the fastest correct configuration
# at every opening").  Five families, and for each ONE engine configuration
# -- the sieve depth and launch size do not follow the frontier; a find
# moves only the census floor, which the device applies after the work is
# done.  The openings are therefore heights:
#   fresh, p = 2*power + 1     launches grow from 16 words while the floor
#                              climbs through the published terms (seconds)
#   p ~ 2^42                   the first open term of every family
#   any resume, any height     the same engine; BENCHMARKS.md has the rate
#                              at 2^42 and at each family's day-long height
# and score.py freezes a shape at both for every family.  There is no host
# pool: the host verifies a few thousand primes per term (huntlib.hostcost
# times each; OPTIMIZATION_LOG.md prices it), so nothing is sized, ramped
# or throttled on the host side.
#
# ASCII-only log; Ctrl+C is a normal exit (boundary checkpoint, one line,
# exit 130, no traceback).

import argparse
import copy
import decimal
import math
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from huntlib.hlog import log, banner, Heartbeat, census_str   # noqa: E402
from huntlib.hostcost import HostCost                         # noqa: E402
from huntlib import checkpoint, evidence, hostcost, shutdown  # noqa: E402
from huntlib import primes as hprimes                         # noqa: E402
from huntlib.rungs import Ladder, LiveLadder                  # noqa: E402

import residue_reference as ref                               # noqa: E402
import residue_search as cpu                                  # noqa: E402
import residue_model as model                                 # noqa: E402

DEFAULT_FAMILY = "A002226"
EVID_DIR = str(HERE / "evidence")
P_CEIL = cpu.P_CEIL
# How many run lengths below the frontier are counted (and so handed to the
# host).  Sized so that a term's stretch hands over power^depth primes at
# most a few thousand: 3125, 2401, 1331, 2197, 4913.
CENSUS_DEPTH = {5: 5, 7: 4, 11: 3, 13: 3, 17: 3}
SURVIVOR_BUDGET = 3000      # device survivors a launch may hand the host
MIN_WORDS = 16
SEG_TARGET_S = 3.0          # a checkpoint segment is about this long
PARITY_S = 20.0             # seconds between sampled CPU parity checks
PARITY_SPAN = 2048          # candidates per sampled check
SLOW_HOST_S = 5.0           # a host step this long gets a [WARN]


def config_key(seq):
    """What a cursor CLAIMS: every candidate 2*power*j + 1 with j below it
    decided -- composite, or a prime whose run is below the floor in force
    when it was met, or classified.  The stream is defined by mathematics
    (residue_search.py), not by an engine version: an engine that
    reproduces the frozen fingerprints covers the identical line, so the
    key carries no version.  The census depth is in it because it decides
    which run lengths the census counted."""
    d = ref.FAMILIES[seq]["power"]
    return f"{seq}|line=2*{d}*j+1|census-depth={CENSUS_DEPTH[d]}"


def ckpt_path(seq):
    return str(HERE / f"campaign_checkpoint_{seq.lower()}.json")


CURSORS = {seq: checkpoint.CursorPolicy(ckpt_path(seq), config_key(seq))
           for seq in ref.FAMILIES}


def floor_of(power, frontier):
    """The census floor at a frontier: the shortest run still counted."""
    return max(1, int(frontier) - CENSUS_DEPTH[power] + 1)


def event_kind(run, frontier, power):
    """DISCOVERY / NEAR / CENSUS / None for a prime of this run met while
    the largest settled index is `frontier` (the repo's discovery-once
    taxonomy on a monotone ladder)."""
    run, frontier = int(run), int(frontier)
    if run > frontier:
        return "DISCOVERY"
    if run < floor_of(power, frontier) or run < 1:
        return None
    return "NEAR" if run == frontier else "CENSUS"


def parse_to(text):
    """--to as an EXACT integer.  Decimal and scientific notation are read
    with `decimal`, never through a float (a float cannot hold an integer
    above 2^53, and the line runs to 2^63); a value that is not a whole
    number is refused rather than rounded."""
    try:
        d = decimal.Decimal(str(text).replace("_", "").replace(",", ""))
    except decimal.InvalidOperation:
        raise argparse.ArgumentTypeError(f"--to {text!r} is not a number")
    if not d.is_finite() or d < 1 or d != d.to_integral_value():
        raise argparse.ArgumentTypeError(
            f"--to {text!r} is not a positive whole number")
    return int(d)


class CampaignAlarm(RuntimeError):
    """A canary missed, a leg disagreed, the device and the host read a
    different run: an engine bug by definition.  The campaign halts
    (exit 2)."""


def fresh_state(seq):
    return {"key": config_key(seq), "sequence": seq, "next_j": 1,
            "terms": [], "census": {}, "near": 0, "survivors": 0,
            "composites": 0, "finds": 0, "passed": [], "odds_passed": [],
            "clock_s": 0.0, "decade": 0, "parity_checked": 0}


class Campaign:
    def __init__(self, engine, seq, ckpt=None, evid_dir=EVID_DIR, known=None,
                 searched_above=None, stop_on_discovery=False, to=None,
                 heartbeat=30.0, gpu_yield_ms=0.0, gentle=False, parity=True,
                 fresh=False, say=log, announce=banner, alt_engine=None):
        fam = ref.FAMILIES[seq]
        self.e, self.seq, self.power = engine, seq, fam["power"]
        self.step = 2 * self.power
        self.forms = ref.forms(seq)
        self.ckpt = ckpt or ckpt_path(seq)
        self.policy = CURSORS[seq].at(self.ckpt)
        self.evid_dir = evid_dir
        self.ledger = os.path.join(evid_dir, f"{seq.lower()}_discoveries.json")
        self.known = list(fam["known"] if known is None else known)
        self.searched_above = (ref.SEARCHED_ABOVE.get(seq, 0)
                               if searched_above is None else searched_above)
        self.stop_on_discovery = stop_on_discovery
        # --to is INCLUSIVE: every candidate p <= to is swept.  end_j is the
        # first index NOT swept; with no --to it is one past the last
        # candidate below the ceiling.
        self.to = None if to is None else int(to)
        top = P_CEIL - 1 if self.to is None else min(self.to, P_CEIL - 1)
        self.end_j = (top - 1) // self.step + 1
        self.interval = float(heartbeat)
        self.yield_s = float(gpu_yield_ms) / 1000.0
        self.gentle, self.parity = gentle, parity
        self.say, self.announce = say, announce
        self._alt = alt_engine
        self.found_this_run = False          # the --stop-on-discovery latch
        self.host_s, self.wall0, self.win_s = 0.0, time.time(), 0.0
        self._parity_t = time.time()
        self._last_save = 0.0
        self._wrote_evidence = False
        self._last_launch = None
        self._pending = []                   # finds confirmed, not yet public
        self.hb = None
        self.hc = HostCost(say=say, warn_s=SLOW_HOST_S)
        st = None
        if not fresh:
            st, _kind = self.policy.load(warn=lambda m: self.say("WARN", m))
        self.resumed = st is not None
        self.st = st if st is not None else fresh_state(seq)
        self.boundary = copy.deepcopy(self.st)
        self._lad = LiveLadder(self._build_ladder)

    # ------------------------------------------------------------ frontier
    def frontier(self):
        return len(self.st["terms"])

    def pos(self):
        """Every candidate below this p is swept."""
        return self.step * self.st["next_j"] + 1

    def last_p(self):
        return self.st["terms"][-1]["p"] if self.st["terms"] else 0

    def since(self):
        """Where the odds of the next open term start: everything KNOWN
        empty below it -- the last settled prime, or the bound the entry
        states above its last published term while that is the term being
        hunted (a find below the bound alarms, so after one the last prime
        is the larger).  The odds of a term at or below this are zero."""
        return max(self.last_p(), self.searched_above)

    def _build_ladder(self, frontier, since):
        if frontier < len(self.known):       # the canary zone: nothing open
            return Ladder([], ceiling=P_CEIL)
        preds = model.predictions(self.power, frontier, since, n_ahead=4,
                                  ceiling=P_CEIL)
        return Ladder.from_predictions(preds, ceiling=P_CEIL)

    def ladder(self):
        return self._lad.get(self.frontier(), self.since())

    # -------------------------------------------------------------- events
    def _alarm(self, msg):
        self.say("ALARM", msg)
        raise CampaignAlarm(msg)

    def handle(self, p, run):
        """One device survivor (ascending p within the line)."""
        st = self.st
        f = self.frontier()
        kind = event_kind(run, f, self.power)
        if kind is None:
            return      # below the floor now in force (the launch's floor
            #             was set at its start; the frontier has moved since)
        if not hprimes.mr_is_prime(p):
            st["composites"] += 1            # a composite that passed: dropped
            return
        r_host = cpu.run_of(p, self.power)
        if r_host != run:
            self._alarm(f"p = {p}: the device read run {run}, plain integer "
                        f"arithmetic reads {r_host}")
        if run >= cpu.RUN_CAP:
            # every engine here reads a run against RUN_CAP primes and no
            # further, so this run is a LOWER BOUND, and nothing below may
            # treat it as the run (the witness of a find needs the first
            # prime that fails).  A composite gets here -- a Carmichael
            # number of the line passes every base -- and was dropped above;
            # for a PRIME below 2^63 the expectation is under 10^-10 over
            # the whole line.  Halt and let a person read it.
            self._alarm(f"p = {p} is PRIME and its first {cpu.RUN_CAP} primes "
                        f"are all residues: the run is at least "
                        f"{cpu.RUN_CAP}, beyond what the engines read")
        st["survivors"] += 1
        key = str(run)
        st["census"][key] = st["census"].get(key, 0) + 1
        if kind == "NEAR":
            st["near"] += 1
            if f >= len(self.known):
                self.say("NEAR", f"run {run} at p = {p} (run-{run} #"
                                 f"{st['census'][key]} of the campaign; a({f}) "
                                 f"settled at p = {self.last_p()}; prime by "
                                 f"Miller-Rabin, run re-read on the host) -- "
                                 f"ONE prime short of a({f + 1})!")
        elif kind == "DISCOVERY":
            self._settle(p, run, f)

    def _settle(self, p, run, f):
        st = self.st
        canary = [n for n in range(f + 1, run + 1) if n <= len(self.known)]
        new = [n for n in range(f + 1, run + 1) if n > len(self.known)]
        for n in canary:
            if self.known[n - 1] != p:
                self._alarm(f"first prime of run >= {n} is p = {p} where the "
                            f"entry has a({n}) = {self.known[n - 1]}")
            st["terms"].append({"n": n, "p": p, "run": run, "kind": "canary"})
        if canary:
            idx = (f"a({canary[0]})" if len(canary) == 1
                   else f"a({canary[0]})..a({canary[-1]})")
            self.say("CANARY-GOLD", f"{self.seq} {idx} = {p} rediscovered "
                                    f"(run {run})")
        if new:
            if p <= self.searched_above:
                self._alarm(f"a prime of run {run} at p = {p} contradicts the "
                            f"entry's bound a({new[0]}) > {self.searched_above}")
            self._record(p, run, new)

    def alt_engine(self):
        """The engine of a find's re-derivation: a shallower sieve and short
        launches, so the alignment and the sieve both differ."""
        if self._alt is None:
            import residue_gpu
            self._alt = residue_gpu._engine(self.power, sieve_primes=64,
                                            words=1024)
        return self._alt

    def _record(self, p, run, new):
        st = self.st
        self.hc.expect("discovery verification")
        if self.hb is not None:
            self.hb.doing(f"verifying a candidate a({new[0]}) at p = {p} "
                          f"(three confirmations)")
        j = cpu.index_of(self.power, p)
        # leg 2: an independent implementation (sympy, the oracle, roots)
        from sympy import isprime
        wit = cpu.witnesses(p, self.power, new[-1])
        cert = cpu.lucas_certificate(p)
        leg2 = (isprime(p) and ref.run(p, self.power) == run
                and cpu.check_witnesses(p, self.power, wit)
                and cpu.check_lucas(p, cert))
        # leg 3: re-derivation by different machinery -- the device again at
        # another alignment and sieve depth, and the CPU engine around p
        # both windows are clipped to the line below the ceiling (they
        # reach past p, and a find may sit against 2^63)
        alt = self.alt_engine()
        j_top = (P_CEIL - 2) // self.step
        a0 = max(1, j - 37 * 64 - 11)
        a_n = min(j - a0 + 500, j_top - a0 + 1)
        redo = alt.stream(a0, a_n, new[0])
        b0 = max(1, min(j - 12000, j_top - 16383))
        dev = self.e.stream(b0, 16384, 1)
        host = cpu.sweep(self.power, b0, 16384, 1, bound=1 << 14)
        leg3 = (bool(redo) and redo[0] == (p, run) and dev == host
                and (p, run) in host and len(host) >= 20)
        if not (leg2 and leg3):
            self._alarm(f"p = {p}: the confirmations DISAGREE (independent "
                        f"implementation {leg2}; re-derivation {leg3})")
        last = new[-1]
        out = evidence.header(self.seq, self.forms, "p", p, new)
        out.update({
            "index": last, "settles": new, "run": run, "power": self.power,
            "verification": "3-way",
            "leg1_engine": ("device stream (sieve, 4^j == 1 mod p, run by "
                            "Montgomery powers); p proved prime by "
                            "deterministic Miller-Rabin; run re-read with "
                            "plain integer arithmetic"),
            "leg2_independent": ("sympy isprime; the oracle's run; an "
                                 "explicit root for each of the first "
                                 f"{run} primes, the symbol of the next, and "
                                 "a Lucas certificate for p, each checked"),
            "leg3_rederivation": (f"device re-sweep of {a_n} "
                                  f"candidates ending past p at another "
                                  f"alignment with a 64-prime sieve: p is "
                                  f"first of run >= {new[0]}; CPU engine = "
                                  f"device on the 16384 candidates around p "
                                  f"at floor 1 ({len(host)} primes)"),
            "roots": wit["roots"],
            "roots_note": (f"x with x^{self.power} == q (mod p) for each of "
                           f"the first {run} primes q"),
            "stopper": wit["stopper"],
            "primality": {"deterministic_miller_rabin": True, "lucas": cert},
            "least_claim": {
                "swept_from_p": self.step + 1, "swept_to_p": p,
                "basis": (f"every integer 2*{self.power}*j + 1 below p -- "
                          f"which includes every prime of which the power "
                          f"divides p - 1 -- was taken in order by this "
                          f"campaign from j = 1: dropped as composite on a "
                          f"small prime factor or on 2^((N-1)/{self.power}) "
                          f"!= 1 (mod N), or as a prime of which 2 is not a "
                          f"residue by the same test, or read to its run, "
                          f"which was below {new[0]}"),
                "conditional_on": "nothing (Euler's criterion; Fermat's "
                                  "little theorem for the compositeness "
                                  "test)",
                "canaries": (f"a(1)..a({len(self.known)}) rediscovered in "
                             f"order by this campaign"),
                "engine": st["key"]},
            "found_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        name = f"{self.seq.lower()}_a{last}_p{p}.json"
        # The find is CONFIRMED here and PUBLISHED at the segment boundary,
        # after the canary and parity checks of the segment that holds it
        # (_publish): a least-p claim says no smaller prime was dropped
        # anywhere below it, and the three legs above cannot see what the
        # sweep lost elsewhere in the segment.  The frontier moves now, so
        # the rest of the segment is classified against it.
        lad_before = self.ladder()
        f_before = self.frontier()
        for n in new:
            st["terms"].append({"n": n, "p": p, "run": run,
                                "kind": "discovery"})
        st["finds"] += len(new)
        self.found_this_run = True
        self._pending.append({
            "record": out, "name": name, "p": p, "run": run, "new": new,
            "stopper": wit["stopper"]["prime"],
            "retired": lad_before.retired_by(last, f_before)})

    def _publish(self):
        """Write the evidence of the segment's finds and announce them --
        called at the boundary, after every check of the segment passed.
        An alarm before this leaves nothing public: the checkpoint stays at
        the previous boundary and the segment is swept again."""
        pending, self._pending = self._pending, []
        for d in pending:
            p, new, last = d["p"], d["new"], d["new"][-1]
            # one claim per index: a ledger that already gives one of these
            # indices to ANOTHER prime contradicts this sweep, and neither
            # claim may be overwritten in silence
            for row in evidence.load_ledger(self.ledger):
                for n_s, v in row.get("oeis_terms", {}).items():
                    if int(n_s) in new and int(v) != p:
                        self._alarm(
                            f"the ledger {os.path.basename(self.ledger)} "
                            f"already claims a({n_s}) = {v}; this sweep "
                            f"finds a({n_s}) = {p}.  Nothing was written")
            evidence.record(d["record"], self.evid_dir, d["name"],
                            self.ledger, key="p", label="DISCOVERY")
            self._wrote_evidence = True
            idx = (f"a({new[0]})" if len(new) == 1
                   else f"a({new[0]}) = ... = a({last})")
            self.announce("DISCOVERY", [
                f"{self.seq} {idx} = {p}",
                f"the first {d['run']} primes are "
                f"{ref.FAMILIES[self.seq]['residues']} mod p; "
                f"{d['stopper']} is not",
                "verified 3-way: device stream + Miller-Rabin + host run; "
                "sympy, the oracle, explicit roots, Lucas certificate; "
                "re-derived at another alignment and by the CPU engine; "
                "the segment's canary and parity checks passed",
                f"evidence: evidence/{d['name']}"])
            nxt = self.ladder().next_rung(self.pos(), self.frontier())
            self.say("RUNG", f"a({last}) found: retired "
                             f"{d['retired'] or 'no rungs'}; the ladder now "
                             f"aims at a({last + 1})"
                             + (f", next {nxt[0]} at {nxt[1]:.3g}"
                                if nxt else ""))

    # ------------------------------------------------------------ boundary
    def _check_canaries(self):
        pos = self.pos()
        got = {t["p"] for t in self.st["terms"]}
        for i, p in enumerate(self.known):
            if p < pos and p not in got:
                self._alarm(f"canary MISSED: the sweep passed a({i + 1}) = "
                            f"{p} without finding it")

    def _check_rungs(self):
        st = self.st
        pos, f = self.pos(), self.frontier()
        lad = self.ladder()
        for lab in lad.newly_passed(pos, f, st["passed"]):
            st["passed"].append(lab)
            nxt = lad.next_rung(pos, f)
            self.say("RUNG", f"passed {lab} "
                             f"({lad.progress_str(pos, f, st['passed'])})"
                             + (f" -- next: {nxt[0]} at {nxt[1]:.3g}"
                                if nxt else ""))
        d = int(math.log10(pos)) if pos > 0 else 0
        if d > st["decade"] and d >= 12:
            st["decade"] = d
            self.say("MILESTONE", f"swept every candidate below p = 10^{d}: "
                                  f"{self._census()}; {f} terms")
        if f >= len(self.known):
            pr = model.odds(self.power, f + 1, self.since(), pos)
            for q in (25, 50, 75, 90):
                tag = f"{f}:{q}"
                if pr * 100 >= q and tag not in st["odds_passed"]:
                    st["odds_passed"].append(tag)
                    self.say("MILESTONE",
                             f"past the model's {q}% point for a({f + 1}) "
                             f"(p = {pos:.4g}); {self._census()}")

    def _census(self):
        f = self.frontier()
        return census_str(self.st["census"], floor_of(self.power, f),
                          max(f, 1))

    def _parity_sample(self):
        """One sampled window of the launch just swept, the device against
        the CPU engine at floor 1: the check that covers what the device
        DROPPED, which no survivor-side check can see."""
        if not self.parity or self._last_launch is None:
            return
        if time.time() - self._parity_t < PARITY_S:
            return
        self._parity_t = time.time()
        j0, count = self._last_launch
        span = min(PARITY_SPAN, count)
        seed = (self.st["survivors"] * 2654435761 + self.st["next_j"]) % (1 << 61)
        a = j0 + seed % (count - span + 1)
        if self.hb is not None:
            self.hb.doing(f"sampled parity check at p = {self.step * a + 1}")
        dev = self.e.stream(a, span, 1)
        host = cpu.sweep(self.power, a, span, 1, bound=1 << 12)
        self.st["parity_checked"] += 1
        if dev != host:
            self._alarm(f"sampled parity FAILED on {span} candidates from p = "
                        f"{self.step * a + 1}: device {len(dev)} primes of "
                        f"run >= 1, CPU engine {len(host)}")

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
        return (f"checkpoint {what} at the last segment boundary, p = "
                f"{self.step * self.boundary['next_j'] + 1}")

    # -------------------------------------------------------------- status
    def status_line(self):
        st = self.st
        pos, f = self.pos(), self.frontier()
        rate = self.hb.rate() if self.hb else 0.0
        bits = [f"{self.seq} p {pos:.5g}", f"{rate:.3g} p/s",
                f"survivors {st['survivors']}", self._census(),
                f"terms {f} (new {st['finds']})", f"near {st['near']}"]
        wall = max(time.time() - self.wall0, 1e-9)
        bits.append(f"host {100 * self.host_s / wall:.1f}% of wall")
        slow = self.hc.status()
        if slow:
            bits.append(slow)
        if f >= len(self.known):
            pr = model.odds(self.power, f + 1, self.since(), pos)
            bits.append(f"P(a({f + 1}) by now) {100 * pr:.0f}%")
        bits.append(self.ladder().status_str(pos, f, rate))
        s = " | ".join(bits)
        stall = self.hb.stalled() if self.hb else None
        if stall:
            s += (f" -- no segment closed since the last status: "
                  f"{stall[0]} for {stall[1]:.0f}s")
        return s

    # ----------------------------------------------------------------- run
    def _plan(self, j0, floor):
        """(first index of the launch, words, candidates classified) for
        the next window, or None when nothing is left: the engine's launch,
        cut back while the floor is low (the host is handed about
        SURVIVOR_BUDGET primes a launch at most) and to what is left before
        --to or the ceiling.  A window is EXACT: it classifies the indices
        j0 .. j0 + count - 1 and nothing else, though the device works in
        64-candidate words.  The padding of the last word is discarded; and
        where that padding would reach the ceiling the launch is moved back
        to END on the last candidate instead, its first few outputs -- swept
        already -- discarded."""
        left = self.end_j - j0
        if left <= 0:
            return None
        n = self.step * j0 + 1
        per_word = 64.0 * self.step / ((self.power - 1) * math.log(n + 3))
        cap = SURVIVOR_BUDGET * float(self.power) ** floor / per_word
        words = int(max(MIN_WORDS, min(self.e.W, cap)))
        words = min(words, (left + 63) // 64)
        count = min(left, 64 * words)
        start = j0
        if self.step * (j0 + 64 * words - 1) + 1 >= P_CEIL:
            start = j0 + count - 64 * words
        return start, words, count

    def window(self):
        st = self.st
        j0 = st["next_j"]
        floor = floor_of(self.power, self.frontier())
        plan = self._plan(j0, floor)
        if plan is None:
            return False
        start, words, count = plan
        t0 = time.time()
        idx, rr = self.e.raw(start, words, floor)
        t1 = time.time()
        for t, r in zip(idx.tolist(), rr.tolist()):
            j = start + t
            if j < j0 or j >= j0 + count:
                continue                     # the launch's padding
            p = self.step * j + 1
            with self.hc.item(f"verifying p = {p}"):
                self.handle(p, r)
        st["next_j"] = j0 + count
        self._last_launch = (j0, count)
        self.host_s += time.time() - t1
        self.win_s = t1 - t0
        pause = self.yield_s + (0.1 * self.win_s if self.gentle else 0.0)
        if pause > 0:
            time.sleep(pause)
        return True

    def _done(self):
        return self.st["next_j"] >= self.end_j

    def _unregister(self, cb):
        try:
            shutdown._callbacks.remove(cb)
        except ValueError:
            pass

    def run(self):
        st = self.st
        self._clock_t = time.time()
        self.hb = Heartbeat(self.interval)
        self.hc.hb = self.hb
        self.hb.mark(self.pos())
        self.hb.start(self.status_line)
        # The boundary save stays REGISTERED while an interrupt unwinds:
        # shutdown.graceful catches the KeyboardInterrupt outside this
        # frame and runs the callbacks then, so removing it on the way out
        # (in a `finally`) would leave Ctrl+C with nothing to save.  It is
        # removed on a normal return and on any other exception.
        cb = shutdown.on_interrupt(self._on_interrupt)
        try:
            if self.to is not None and self.to < P_CEIL - 1:
                why = f"reached --to {self.to}"
            else:
                why = ("reached the engine ceiling p = 2^63 (the last rung): "
                       "the last candidate below it is swept")
            while not self._done():
                if self.stop_on_discovery and self.found_this_run:
                    why = ("--stop-on-discovery: this run confirmed a new "
                           "term")
                    break
                nwin = 1 if self.win_s <= 0 else max(
                    1, min(4096, int(SEG_TARGET_S / max(self.win_s, 1e-4))))
                self.hb.doing(f"sweeping from p = {self.pos()}")
                t_seg = time.time()
                for _ in range(nwin):
                    if not self.window() or self._done():
                        break
                    if self.found_this_run and self.stop_on_discovery:
                        break
                    if time.time() - t_seg > 2 * SEG_TARGET_S:
                        break
                self._check_canaries()
                self._check_rungs()
                self._parity_sample()
                self._publish()
                self.mark_boundary()
                self.hb.mark(self.pos())
                self.save()
            self.hb.stop()
            landed = self.save(force=True)
        except KeyboardInterrupt:
            self.hb.stop()
            raise                            # the callback stays for graceful
        except BaseException:
            self.hb.stop()
            self._unregister(cb)
            raise
        self._unregister(cb)
        self.say("STAGE", f"stopped: {why}; every candidate below p = "
                          f"{self.pos()} swept; {self.frontier()} terms "
                          f"({st['finds']} new); checkpoint "
                          f"{'written' if landed else 'DEFERRED (locked)'}")
        return 0


# --------------------------------------------------------------- commands
def print_status(only=None):
    for seq in ref.FAMILIES:
        if only and seq != only:
            continue
        fam = ref.FAMILIES[seq]
        st, _kind = CURSORS[seq].load(warn=lambda m: log("WARN", m))
        print(f"{seq}: {ref.forms(seq)}")
        if st is None:
            print(f"  no checkpoint: a fresh campaign starts at p = "
                  f"{2 * fam['power'] + 1} and rediscovers a(1)..a("
                  f"{len(fam['known'])}) first")
            continue
        d = fam["power"]
        f = len(st["terms"])
        print(f"  [{st['key']}]")
        print(f"  swept: every candidate below p = {2 * d * st['next_j'] + 1}"
              f"  ({st['clock_s'] / 3600:.2f} h of campaign clock)")
        for t in st["terms"]:
            if t["kind"] == "discovery":
                print(f"  a({t['n']}) = {t['p']}   run {t['run']}   "
                      f"(discovery)")
        print(f"  terms {f} ({st['finds']} new, {f - st['finds']} canaries); "
              f"survivors {st['survivors']}; "
              f"{census_str(st['census'], floor_of(d, f), max(f, 1))}; near "
              f"{st['near']}; composites dropped {st['composites']}; parity "
              f"checks {st['parity_checked']}")
    return 0


def campaign(args, policy=None, evid_dir=EVID_DIR, say=log, announce=banner):
    """The owner's entry point.  `policy`, `evid_dir`, `say` and `announce`
    exist so that the selftest can drive THIS function, unchanged, over the
    canary range against a scratch checkpoint."""
    import residue_gpu
    from huntlib.gpu import device_report
    seq = args.family.upper()
    if seq not in ref.FAMILIES:
        say("ALARM", f"no family {args.family}: one of "
                     f"{', '.join(ref.FAMILIES)}")
        return 2
    policy = policy or CURSORS[seq]
    policy.refuse_mismatch(
        fresh=args.fresh,
        describe=lambda s: f"cursor at j = {s.get('next_j')}")
    if not residue_gpu.available():
        say("ALARM", "no CUDA device: this campaign runs on the GPU engine")
        return 2
    d = ref.FAMILIES[seq]["power"]
    e = residue_gpu._engine(d)
    say("STAGE", f"{seq}: {ref.forms(seq)}")
    say("STAGE", device_report(e.held_bytes()))
    c = Campaign(e, seq, ckpt=policy.path, evid_dir=evid_dir,
                 stop_on_discovery=args.stop_on_discovery, to=args.to,
                 heartbeat=args.heartbeat, gpu_yield_ms=args.gpu_yield_ms,
                 gentle=args.gentle, parity=not args.no_parity,
                 fresh=args.fresh, say=say, announce=announce)
    say("STAGE", ("resuming" if c.resumed else "fresh start") +
        f" at p = {c.pos()}; {c.frontier()} terms settled "
        f"({len(c.known)} published); ceiling p = 2^63; engine "
        f"{residue_gpu.ENGINE}, {residue_gpu.SIEVE_PRIMES} sieve primes, "
        f"launches of 2^{e.W.bit_length() - 1} words; no host pool")
    try:
        return c.run()
    except CampaignAlarm:
        checkpoint.save(c.ckpt, c.boundary)
        say("STAGE", "HALTED on an alarm; the checkpoint stands at the last "
                     "good segment boundary; exit 2")
        return 2


# ------------------------------------------------------------ the selftest
def _quiet(lines):
    return lambda tag, msg: lines.append((tag, msg if isinstance(msg, str)
                                          else " / ".join(msg)))


def drills():
    """The launcher's own drills, as [(ok, msg)]."""
    import tempfile
    import residue_gpu
    from huntlib import drills as hdrills
    out = []
    # the discovery-once taxonomy (power 5: depth 5, so at frontier 15 the
    # floor is 11)
    out.append(hdrills.event_kind_drill(
        lambda r: event_kind(r, 15, 5),
        [(16, "DISCOVERY"), (19, "DISCOVERY"), (15, "NEAR"), (14, "CENSUS"),
         (11, "CENSUS"), (10, None), (0, None)]))
    # every family's evidence header speaks its entry's letters
    good = True
    for seq, fam in ref.FAMILIES.items():
        ev = evidence.header(seq, ref.forms(seq), "p", fam["known"][-1],
                             [len(fam["known"])])
        ev["settles"] = [len(fam["known"])]
        good = good and evidence.check_names(ev, "p")[0]
        good = good and not evidence.check_names(
            dict(ev, forms="x^5 == q (mod N)"), "p")[0]
    gn = evidence.gate_names(EVID_DIR, "p")
    out.append((good and gn[0],
                "evidence names: all five families' records carry a(n) under "
                "`p` beside the entry's own words (first n primes (p_1=2, "
                "..., p_n) are ... residues mod p) with the oeis_terms map; "
                "a `forms` in other letters is refused; " + gn[1]))
    seq = "A060363"                      # its published terms end at 7.3e10
    e = residue_gpu._engine(13)
    known = ref.FAMILIES[seq]["known"]
    tmp = tempfile.mkdtemp(prefix="residue-drill-")
    try:
        # (a) the campaign loop over known territory: canaries, census,
        #     resume = unsplit
        lines = []
        kw = dict(say=_quiet(lines), announce=_quiet(lines), heartbeat=3600)
        TO = 10 ** 11
        a = Campaign(e, seq, ckpt=os.path.join(tmp, "a.json"),
                     evid_dir=os.path.join(tmp, "ev-a"), to=TO, **kw)
        a.run()
        b1 = Campaign(e, seq, ckpt=os.path.join(tmp, "b.json"),
                      evid_dir=os.path.join(tmp, "ev-b"), to=10 ** 9, **kw)
        b1.run()
        b2 = Campaign(e, seq, ckpt=os.path.join(tmp, "b.json"),
                      evid_dir=os.path.join(tmp, "ev-b"), to=TO, **kw)
        b2.run()
        same = all(a.st[f] == b2.st[f] for f in
                   ("next_j", "terms", "census", "near", "survivors",
                    "composites"))
        ps = [t["p"] for t in a.st["terms"]]
        gold = sum(1 for tag, _ in lines if tag == "CANARY-GOLD")
        # one line per distinct prime: 7 in the unsplit run (a(7) = a(8)),
        # 6 below 10^9 and 1 above it in the split one
        out.append((ps == known and same and b2.resumed
                    and a.st["finds"] == 0 and gold == 7 + 6 + 1,
                    f"campaign drill ({seq}): the loop from the line's first "
                    f"candidate to p = 10^11 rediscovers a(1)..a(8) as "
                    f"canaries and nothing else; a run split at 10^9 and "
                    f"resumed ends in the identical state "
                    f"({a.st['survivors']} survivors, {a._census()}, "
                    f"{a.st['composites']} composites dropped by the host)"))
        # the quintic line through its first ten terms
        q = Campaign(residue_gpu._engine(5), "A002226",
                     ckpt=os.path.join(tmp, "q.json"),
                     evid_dir=os.path.join(tmp, "ev-q"), to=10 ** 9, **kw)
        q.run()
        out.append(([t["p"] for t in q.st["terms"]]
                    == ref.FAMILIES["A002226"]["known"][:10]
                    and q.st["finds"] == 0,
                    "campaign drill (A002226): the quintic line to p = 10^9 "
                    "rediscovers a(1)..a(10) in order"))
        # (b) the discovery protocol end to end, and --stop-on-discovery on
        #     the RESUMED case: pretend the entry stopped at a(4)
        lines2 = []
        kw2 = dict(say=_quiet(lines2), announce=_quiet(lines2),
                   heartbeat=3600, known=known[:4], searched_above=0,
                   stop_on_discovery=True, ckpt=os.path.join(tmp, "c.json"),
                   evid_dir=os.path.join(tmp, "ev-c"), to=TO)
        stops = []
        for _ in range(4):
            c = Campaign(e, seq, **kw2)
            before = c.st["finds"]
            c.run()
            stops.append((before, c.st["finds"], c.st["terms"][-1]["p"],
                          c.pos() >= TO))
        flow = (stops[0] == (0, 1, known[4], False)
                and stops[1] == (1, 2, known[5], False)
                and stops[2] == (2, 4, known[7], False)
                and stops[3] == (4, 4, known[7], True))
        names = evidence.gate_names(os.path.join(tmp, "ev-c"), "p")
        led = evidence.load_ledger(os.path.join(
            tmp, "ev-c", f"{seq.lower()}_discoveries.json"))
        retired = sum(1 for tag, m in lines2 if tag == "RUNG" and "found" in m)
        ok_led = (len(led) == 3
                  and all(r["verification"] == "3-way" for r in led)
                  and led[2]["oeis_terms"] == {"7": known[7], "8": known[7]}
                  and all(cpu.check_witnesses(r["p"], 13, {
                      "run": r["run"], "roots": r["roots"],
                      "stopper": r["stopper"]}) for r in led)
                  and all(cpu.check_lucas(r["p"], r["primality"]["lucas"])
                          for r in led))
        out.append((flow and names[0] and ok_led and retired == 3,
                    f"discovery drill ({seq} cut back to a(4)): "
                    f"{known[4]}, {known[5]} and {known[7]} -- the last "
                    f"settling a(7) and a(8) at once -- are each confirmed "
                    f"3-way and evidenced under `p` with roots, stopper and "
                    f"Lucas certificate that check; --stop-on-discovery "
                    f"stops a fresh run at its first find, runs resumed with "
                    f"1 and 2 prior finds only after their own, and a run "
                    f"resumed with 4 sweeps to --to; each find retires its "
                    f"rungs"))
        # (c) a stream that drops or bends a canary must ALARM, and so must
        #     one that drops an ordinary prime a sampled check lands on

        class Bent:
            def __init__(self, e, drop=None, bend=None, thin=False):
                self.e, self.drop, self.bend, self.thin = e, drop, bend, thin
                self.W, self.step, self.power = e.W, e.step, e.power

            def raw(self, j0, words, floor):
                idx, rr = self.e.raw(j0, words, floor)
                p = (j0 + idx.astype("uint64")) * self.step + 1
                rr = rr.copy()
                rr[p == self.bend] += 1
                keep = p != self.drop
                return idx[keep], rr[keep]

            def stream(self, j0, count, floor=1):
                got = self.e.stream(j0, count, floor)
                return got[1:] if self.thin else got

        alarms = 0
        for bent in (Bent(e, drop=known[3]), Bent(e, bend=known[2])):
            try:
                Campaign(bent, seq, ckpt=os.path.join(tmp, "d.json"),
                         evid_dir=os.path.join(tmp, "ev-d"), to=10 ** 8,
                         fresh=True, **kw).run()
            except CampaignAlarm:
                alarms += 1
        global PARITY_S
        keep_s, PARITY_S = PARITY_S, 0.0
        try:
            Campaign(Bent(e, thin=True), seq, ckpt=os.path.join(tmp, "d.json"),
                     evid_dir=os.path.join(tmp, "ev-d"), to=10 ** 8,
                     fresh=True, **kw).run()
        except CampaignAlarm:
            alarms += 1
        finally:
            PARITY_S = keep_s
        out.append((alarms == 3,
                    "alarm drill: a stream that drops a(4), one that bends "
                    "the run of a(3), and one that loses an ordinary prime "
                    "where a sampled parity check lands all HALT the "
                    "campaign"))
        # (d) the owner's entry point itself over the canary range: the
        #     refusal, the device report, sampled parity and both throttles
        lines3 = []
        pol = CURSORS[seq].at(os.path.join(tmp, "e.json"))
        ns = argparse.Namespace(family=seq, to=TO, fresh=False,
                                heartbeat=3600, stop_on_discovery=False,
                                gpu_yield_ms=0.01, gentle=True,
                                no_parity=False)
        keep_s, PARITY_S = PARITY_S, 0.0
        try:
            rc = campaign(ns, policy=pol, evid_dir=os.path.join(tmp, "ev-e"),
                          say=_quiet(lines3), announce=_quiet(lines3))
        finally:
            PARITY_S = keep_s
        st3, _ = pol.load()
        with open(pol.path, "w") as fh:
            fh.write('{"key": "some-other-line", "next_j": 5}')
        try:
            campaign(ns, policy=pol, evid_dir=os.path.join(tmp, "ev-e"),
                     say=_quiet(lines3), announce=_quiet(lines3))
            refused = False
        except checkpoint.CursorRefused:
            refused = True
        out.append((rc == 0 and st3 is not None
                    and [t["p"] for t in st3["terms"]] == known
                    and st3["parity_checked"] >= 2 and refused,
                    f"entry-point drill: campaign() itself, {seq} to p = "
                    f"10^11 on a scratch checkpoint, reports the device, "
                    f"rediscovers the eight terms, passes "
                    f"{st3['parity_checked'] if st3 else 0} sampled parity "
                    f"checks with both throttles on, and refuses a "
                    f"checkpoint written under another key"))
        # (e) the ladder is cached on the frontier and aims at the open
        #     term; reading a checkpoint does not write it
        c = Campaign(e, seq, **dict(kw2, stop_on_discovery=False))
        b0 = c._lad.builds
        for _ in range(50):
            c.ladder()
            c.status_line()
        cached = c._lad.builds - b0 == 1
        aims = c.ladder().next_rung(c.last_p(), c.frontier())
        m0 = os.path.getmtime(kw2["ckpt"])
        st, kind = CURSORS[seq].at(kw2["ckpt"]).load()
        out.append((cached and st is not None and kind == "own"
                    and os.path.getmtime(kw2["ckpt"]) == m0
                    and aims is not None and aims[0].startswith("a(9)"),
                    "wiring drill: fifty ladder reads and status lines at a "
                    "standing frontier cost one build; the live ladder aims "
                    "at the next open term; reading the checkpoint does not "
                    "write it"))
        # (f) a slow host step is announced with its p and kept in [STATUS]
        out.append(hostcost.drill())
        lines6, slow = [], []

        class Slow(Campaign):
            def handle(self, p, run):
                if not slow and self.frontier() >= 2:
                    slow.append(p)
                    time.sleep(0.12)
                return super().handle(p, run)
        sc = Slow(e, seq, ckpt=os.path.join(tmp, "s.json"),
                  evid_dir=os.path.join(tmp, "ev-s"), to=10 ** 8, fresh=True,
                  say=_quiet(lines6), announce=_quiet(lines6), heartbeat=3600)
        sc.hc.warn_s = 0.1
        sc.run()
        warns = [m for tag, m in lines6 if tag == "WARN" and "host step" in m]
        out.append((len(slow) == 1 and len(warns) == 1
                    and f"verifying p = {slow[0]}" in warns[0]
                    and f"p = {slow[0]}" in sc.status_line()
                    and sc.hc.n >= sc.st["survivors"],
                    f"slow-step drill: a survivor whose handling takes 0.12 s "
                    f"against a 0.1 s threshold gets one [WARN] naming it "
                    f"(p = {slow[0] if slow else '-'}), [STATUS] keeps it as "
                    f"the slowest step, and every survivor of the run was "
                    f"timed ({sc.hc.n})"))
        # (g) the launch sizes: small while the floor is low, the engine's
        #     own launch once the frontier has climbed, clipped at --to and
        #     at the ceiling
        w = Campaign(residue_gpu._engine(5), "A002226",
                     ckpt=os.path.join(tmp, "w.json"),
                     evid_dir=os.path.join(tmp, "ev-w"), **kw)
        j_top = (P_CEIL - 2) // 10
        plans = (w._plan(1, 1), w._plan(10 ** 12, 11),
                 w._plan(j_top - 100, 11), w._plan(j_top + 1, 11))
        out.append((plans[0][0] == 1 and plans[0][1] <= 256
                    and plans[1] == (10 ** 12, w.e.W, 64 * w.e.W)
                    and plans[2] == (j_top - 127, 2, 101)
                    and plans[3] is None,
                    f"launch-size drill: {plans[0][1]} words at the line's "
                    f"first candidate (floor 1), the engine's 2^"
                    f"{w.e.W.bit_length() - 1} at the open frontier; against "
                    f"the ceiling the last 101 candidates are one launch of "
                    f"two words moved back to end on the last candidate, and "
                    f"there is none above it"))
        # (h) Ctrl+C: the boundary save is still registered when the
        #     interrupt reaches shutdown.graceful, and it writes the LAST
        #     boundary -- not the last periodic save (finding RSL-003)
        lines7 = []
        kw7 = dict(say=_quiet(lines7), announce=_quiet(lines7), heartbeat=3600)

        class Interrupted(Campaign):
            hits = 0

            def mark_boundary(self):
                super().mark_boundary()
                Interrupted.hits += 1

            def window(self):
                if Interrupted.hits >= 3:    # in the fourth segment
                    raise KeyboardInterrupt
                return super().window()

        ic = Interrupted(e, seq, ckpt=os.path.join(tmp, "i.json"),
                         evid_dir=os.path.join(tmp, "ev-i"), to=TO, **kw7)
        n_cb = len(shutdown._callbacks)
        global SEG_TARGET_S
        keep_seg, SEG_TARGET_S = SEG_TARGET_S, 1e-9   # one window a segment
        try:
            ic.run()
            stopped = False
        except KeyboardInterrupt:
            stopped = True
        finally:
            SEG_TARGET_S = keep_seg
        still = ic._on_interrupt in shutdown._callbacks
        on_disk = CURSORS[seq].at(ic.ckpt).load()[0]
        stale = on_disk is not None and on_disk["next_j"] < ic.boundary["next_j"]
        msg = ic._on_interrupt() if still else ""     # what graceful runs
        ic._unregister(ic._on_interrupt)
        saved = CURSORS[seq].at(ic.ckpt).load()[0]
        i2 = Campaign(e, seq, ckpt=ic.ckpt, evid_dir=os.path.join(tmp, "ev-i"),
                      to=TO, **kw7)
        i2.run()
        resumed = all(a.st[f] == i2.st[f] for f in
                      ("next_j", "terms", "census", "near", "survivors",
                       "composites"))
        out.append((stopped and still and stale and saved == ic.boundary
                    and Interrupted.hits == 3 and "written" in msg
                    and i2.resumed and resumed
                    and len(shutdown._callbacks) == n_cb,
                    f"interrupt drill: Ctrl+C in the fourth segment leaves the "
                    f"boundary save registered for shutdown.graceful; the "
                    f"file then held the first segment's cursor (the periodic "
                    f"save is throttled) and the callback writes the third "
                    f"boundary, p = {ic.step * ic.boundary['next_j'] + 1}, "
                    f"field for field; a run resumed from it ends in the "
                    f"state of the uninterrupted one; a run that returns "
                    f"normally leaves no callback behind"))
        # (i) the interval is exact (finding RSL-001): --to is inclusive
        #     and read as an integer; the last partial word below the
        #     ceiling is swept, for every length 0..63 and every family
        got_to = []
        for lim in (known[3] - 1, known[3], known[3] + 1):
            t = Campaign(e, seq, ckpt=os.path.join(tmp, f"t{lim}.json"),
                         evid_dir=os.path.join(tmp, "ev-t"), to=lim, **kw7)
            t.run()
            got_to.append((len(t.st["terms"]), t.st["next_j"]))
        j3 = cpu.index_of(13, known[3])
        exact = got_to == [(3, j3), (4, j3 + 1), (4, j3 + 1)]
        try:
            parse_to("1e16.5")
            parsed = False
        except argparse.ArgumentTypeError:
            parsed = (parse_to("9007199254740993") == 2 ** 53 + 1
                      and parse_to("1e18") == 10 ** 18
                      and parse_to("2.5e17") == 25 * 10 ** 16)
            try:
                parse_to("0.5")
                parsed = False
            except argparse.ArgumentTypeError:
                pass
        tails = n_tail = 0
        for s2, fam2 in ref.FAMILIES.items():
            d2 = fam2["power"]
            seen = []

            class Tail(Campaign):
                def handle(self, p, run):
                    if hprimes.mr_is_prime(p):
                        seen.append((p, run))

            tc = Tail(residue_gpu._engine(d2), s2,
                      ckpt=os.path.join(tmp, f"tail-{s2}.json"),
                      evid_dir=os.path.join(tmp, "ev-tail"), known=[], **kw7)
            top = (P_CEIL - 2) // (2 * d2)
            for length in range(64):
                del seen[:]
                tc.st["next_j"] = top + 1 - length
                while tc.window():
                    pass
                want = (cpu.sweep(d2, top + 1 - length, length, 1)
                        if length else [])
                if (tc.st["next_j"] == top + 1 and seen == want
                        and tc._plan(top + 1, 1) is None):
                    tails += 1
                n_tail += len(seen)
        out.append((exact and parsed and tails == 64 * len(ref.FAMILIES)
                    and n_tail > 0,
                    f"exact-interval drill: --to one below a(4), at it and one "
                    f"above it stops with 3, 4 and 4 terms and the cursor on "
                    f"the candidate after the limit; --to is read as an exact "
                    f"integer (2^53 + 1, 1e18, 2.5e17) and a fraction is "
                    f"refused; started 0 to 63 candidates below the ceiling, "
                    f"every family's loop classifies exactly the CPU engine's "
                    f"primes of that tail ({n_tail} in all) and ends on the "
                    f"last candidate below 2^63"))
        # (j) a find is PUBLISHED only after its segment's checks (finding
        #     RSL-002): an alarm at the boundary leaves no evidence and no
        #     discovery in the checkpoint; a ledger that already gives the
        #     index to another prime halts the run instead of being rewritten
        lines8 = []
        kw8 = dict(say=_quiet(lines8), announce=_quiet(lines8), heartbeat=3600,
                   known=known[:4], searched_above=0, to=TO,
                   ckpt=os.path.join(tmp, "p.json"),
                   evid_dir=os.path.join(tmp, "ev-p"))

        class Alarmed(Campaign):
            def _parity_sample(self):
                if self._pending:
                    self._alarm("planted: the segment of a find fails a check")

        ac = Alarmed(e, seq, **kw8)
        try:
            ac.run()
            halted = False
        except CampaignAlarm:
            halted = True
        confirmed = ac.st["finds"] >= 1 and len(ac._pending) >= 1
        checkpoint.save(ac.ckpt, ac.boundary)         # what campaign() does
        on_disk = CURSORS[seq].at(ac.ckpt).load()[0]
        silent = (not os.path.exists(os.path.join(tmp, "ev-p"))
                  or not os.listdir(os.path.join(tmp, "ev-p")))
        clean = (on_disk["finds"] == 0
                 and all(t["kind"] == "canary" for t in on_disk["terms"])
                 and not any(tag == "DISCOVERY" for tag, _ in lines8))
        pc = Campaign(e, seq, **dict(kw8, stop_on_discovery=True))
        pc.run()
        led_p = os.path.join(tmp, "ev-p", f"{seq.lower()}_discoveries.json")
        once = ([r["p"] for r in evidence.load_ledger(led_p)] == [known[4]]
                and sum(1 for tag, _ in lines8 if tag == "DISCOVERY") == 1)
        # plant a rival claim for the next index and sweep on
        rows = evidence.load_ledger(led_p)
        rival = dict(rows[0], p=known[5] + 26,
                     oeis_terms={"6": known[5] + 26}, settles=[6], index=6)
        checkpoint.save_json(led_p, rows + [rival])
        try:
            Campaign(e, seq, **kw8).run()
            refused = False
        except CampaignAlarm:
            refused = True
        kept = [r["p"] for r in evidence.load_ledger(led_p)]
        out.append((halted and confirmed and silent and clean and once
                    and refused and kept == [known[4], known[5] + 26],
                    f"publication drill ({seq} cut back to a(4)): a find "
                    f"confirmed 3-way in a segment whose boundary check then "
                    f"alarms is NOT published -- no evidence file, no ledger, "
                    f"no [DISCOVERY] line, no discovery in the checkpoint; "
                    f"the next run finds it again and publishes it once; a "
                    f"ledger that already gives a(6) to another prime halts "
                    f"the sweep with both claims untouched"))
        # (k) a run that fills the engines' cap is a lower bound (finding
        #     RSL-004): a PRIME that reaches it halts the campaign rather
        #     than being settled on a run nobody read to its end
        keep_cap, cpu.RUN_CAP = cpu.RUN_CAP, 3
        lines9 = []
        try:
            Campaign(e, seq, ckpt=os.path.join(tmp, "k.json"),
                     evid_dir=os.path.join(tmp, "ev-k"), to=10 ** 8,
                     say=_quiet(lines9), announce=_quiet(lines9),
                     heartbeat=3600).run()
            capped = False
        except CampaignAlarm as exc:
            capped = "beyond what the engines read" in str(exc)
        finally:
            cpu.RUN_CAP = keep_cap
        out.append((capped and len(shutdown._callbacks) == n_cb,
                    "saturated-run drill: with the cap lowered to 3 in "
                    "scratch, the first prime whose run reaches it HALTS the "
                    "campaign (its run is a lower bound, and a find's witness "
                    "needs the first prime that fails) instead of settling a "
                    "term on it"))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def selftest():
    import residue_gpu
    from huntlib import drills as hdrills
    from huntlib import ceiling as hceiling
    t0 = time.time()
    ok = ref.selftest()
    ok = cpu.selftest() and ok
    ok = residue_gpu.selftest() and ok
    results = [g() for g in model.GATES]
    if residue_gpu.available():
        results += drills()
    results += [g() for g in hceiling.GATES]
    results += hdrills.standard(cursor=CURSORS[DEFAULT_FAMILY])
    for good, msg in results:
        print(("PASS " if good else "FAIL ") + msg, flush=True)
        ok = ok and good
    print(("ALL GREEN" if ok else "RED") + f"  ({time.time() - t0:.0f}s)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="The power-residue ladders: "
                                 "A002226, A002227, A002228, A060363, A060364")
    ap.add_argument("--family", default=DEFAULT_FAMILY)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--to", type=parse_to, default=None)
    ap.add_argument("--stop-on-discovery", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--heartbeat", type=float, default=30.0)
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0)
    ap.add_argument("--gentle", action="store_true")
    ap.add_argument("--no-parity", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.status:
        only = args.family.upper() if "--family" in sys.argv else None
        return print_status(only)
    return campaign(args)


if __name__ == "__main__":
    sys.exit(shutdown.graceful(main))
