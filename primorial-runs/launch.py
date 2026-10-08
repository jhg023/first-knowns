"""The campaign for the exact-run primorial shift ladders -- A257466, A257467 and A258035: the smallest prime p such that p + pps(1), ..., p + pps(n) are all prime but p + pps(n+1) is not (and the same with psq, and with pssq).

    python launch.py                       the hunt: indefinite, resumable (A257466)
    python launch.py --family A257467      the squared-primorial family
    python launch.py --family A258035      the partial sums of squared primorials
    python launch.py --status              where the cursor is; reads, never writes
    python launch.py --selftest            the full gate battery; must end ALL GREEN

THREE FAMILIES, ONE ENGINE, ONE CAMPAIGN AT A TIME.  `--family` names the
entry (runs_reference.FAMILIES).  Each family has its own checkpoint,
ledger and config key, and a campaign hunts one of them.  No derived entry
rides on any.

EVERY FORM IS KNOWN AT EVERY INDEX, so the campaign can be planned, priced
and benchmarked at every filter it will promote itself through, in advance
(CLAUDE.md 5g): `plan_for` is the one place a configuration is derived,
score.py has a shape at each family's opening, and G18 compiles the opening
and the filters above it.

THE RUN IS EXACT, AND THE SEQUENCES ARE NOT MONOTONE (runs_reference).  The
run of a prime p is the number of leading shifts whose value is prime, and
a(n) is the FIRST prime whose run is exactly n.  So there is ONE line, swept
from the bottom (p = 2), with the filter at the LOWEST OPEN index n: every
prime below the cursor with a run of at least n has had its exact run read,
which settles the first occurrence of every exact run from n up.  A survivor
whose exact run is r >= n:
  * a(r) not yet settled: a DISCOVERY of a(r) ALONE.  If r > n the filter
    does not move (a(n) is still open) and the sweep goes on; if r = n the
    frontier advances to the next unsettled index -- it may jump over
    indices found early -- and the filter follows, CARRYING the line: the
    new filter resumes at the old segment's end, re-denominated by floor
    into its own period with the clip at the old boundary, so no line is
    skipped and none is swept twice.
  * a(r) settled and a(r+1) not: NEAR -- one condition short of an open
    term; verified, not evidenced.
  * otherwise it is counted (CENSUS_FLOOR <= r) and nothing else.
Both promotions are drilled (_promotion_drill, _rediscovery_run_drill), on
scratch files, on published terms.

THE EXCEPTION ZONE IS COVERED AT THE BOTTOM OF THE LINE.  A kill by q needs
the value to exceed q, so the device starts above the sieve depth; the
primes from 2 to the depth are classified one at a time on the host
(runs_search.prefix_hits), their census counted and a find there handled
like any other, before the first launch.  The checkpoint records which
filter's zone is done (`zone_n`), so a resume does not count it twice.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine ceiling on p (huntlib's K_CEIL = 1e40) or until the lowest open
index passes runs_search.n_max -- the last index whose shift stays under
the MEASURED ceiling on the values (V_CEIL), past which a discovery could
not be certified.  The proof crossing -- where classification stops being a
proof -- is 3.317e24 less the largest shift, which on the squared families
is the bottom of the line: a [MILESTONE], never a stop.

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
candidates of a segment come out in wheel order, so nothing in a segment is
known to be the LEAST until it closes: 'swept to' is the p below which every
value has been tested; (period, launch) is the work cursor inside it.

THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER, at
start and at every promotion (CLAUDE.md 5f, 5g); back-pressure bounds the
device's lead over the host and the waited fraction is in every [STATUS].

Ctrl+C is a normal exit: a checkpoint at the last segment boundary, one
[STAGE] line, exit code 130, no traceback (huntlib.shutdown).
"""

import argparse
import collections
import concurrent.futures as _cf
import functools
import math
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from huntlib import ceiling, certificate, checkpoint, drills, evidence  # noqa: E402
from huntlib import pool as _pool                               # noqa: E402
from huntlib import shutdown                                    # noqa: E402
from huntlib.gpu import device_report                           # noqa: E402
from huntlib.hlog import Heartbeat, banner, census_str, log     # noqa: E402
from huntlib.primes import (MR_VALID_BELOW, factor_witness,     # noqa: E402
                            mr_is_prime, sprp_base2)
from huntlib.rungs import Ladder, LiveLadder, eta_str           # noqa: E402
from sympy import isprime                                       # noqa: E402

import runs_gpu as gpu                                     # noqa: E402
import runs_model as model                                 # noqa: E402
import runs_reference as ref                               # noqa: E402
import runs_search as cpu                                  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")


def TERM(fam):
    """The letter the OEIS name gives the term: p on every family here
    (rule 5i); every surface a person reads carries the integer under it."""
    return ref.letter(fam)


def SHIFT(fam):
    """The name the entry gives its shift: pps, psq or pssq."""
    return ref.FAMILIES[ref.family(fam)]["shift"]


PLAN_VERSION = "p1"               # bump when plan_for's answer changes
#   p1 (2026-10-02): plus-two-cliques' planner p2 taken whole -- the wheel
#   and the window chosen together by expected clock to a confirmed find
#   (runs_gpu.plan) over every greedy wheel subset the kernel admits,
#   with the second first-level budget; the floor it prices from is the
#   bottom of the line (every index's line starts at p = 2).


@functools.lru_cache(maxsize=None)
def plan_for(fam, n):
    """(unit, p1, p2, p3, q2, pb) for filter n of family F -- the
    configuration the campaign runs there, and the fastest correct one it
    has (CLAUDE.md 5g).  Pure and cached: a function of (family, n) alone,
    so a resumed campaign derives the identical plan and the launcher still
    asserts W and the segment on load (OPTIMIZATION.md 2.9).  Cached
    because `x_start` and `state` call it every launch (2.14's trap)."""
    fam = ref.family(fam)
    unit = cpu.forced_unit(n, fam)
    p1, p2, p3, q2, pb = gpu.plan(n, fam, unit)
    return unit, p1, p2, p3, q2, pb


def x_floor(fam, n, _unused=None):
    """Where the line of a(n) starts, the definition's own floor: 2, the
    least prime, at every index (the sequences are not monotone)."""
    return ref.floor_x(ref.family(fam), int(n))


def open_n(fam):
    """The filter a FRESH campaign of this family opens at."""
    return max(ref.KNOWN[ref.family(fam)]) + 1


# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a segment.
CKPT_LAUNCHES = 32
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
# How far past the filter the POOL reads a run.  The run that decides
# anything is EXACT: a value whose run reaches this cap is re-read with no
# cap before it is classified (Campaign.handle), so the line a filter swept
# is carried to every later filter with every run on it known exactly.
RUN_AHEAD = 8
RUN_EXACT_CAP = 64                # "no cap": no run here comes near it
# WHAT A PLAN MAY WASTE: a plan whose expected sweep to a confirmed find
# exceeds the unavoidable one by more than this factor is a decision for a
# human (_families_stay_apart).
PLAN_WASTE_MAX = 1.5

ENGINE_VERSION = "v1"
#   v1 (2026-10-02): plus-two-cliques' engine v3, taken whole -- the window
#   sieve on quad loads, the lazy narrow rounds, the folded wide rounds, the
#   generated tail rounds, with primorial-ladders' round 1 (the extraction
#   batch and the queue entry decided on the compiled occupancy).  The
#   kernel never sees a form, only the residues each prime kills.
PREVIOUS_ENGINES = ()
WORKERS_DEFAULT = 2
POOL_MARGIN = 2.0
CAL_MIN_SURVIVORS = 500
CAL_MIN_S = 1.0
CAL_MAX_S = 4.0
CAL_SEGMENTS = 256
CAL_SAMPLE = 2000
BACKLOG_LAUNCHES = 64
CKPT_MIN_S = 2.0
CKPT_COST_FRACTION = 0.02
PERIOD_LOG_S = 60.0
WORKER_RAMP_S = _pool.RAMP_S
CHUNK = 256                       # survivors per pool task


def config_key(fam, engine=None):
    fam = ref.family(fam)
    return (f"{fam.lower()}-{engine or ENGINE_VERSION}-{PLAN_VERSION}"
            f"-seg{CKPT_LAUNCHES}"
            f"-pbd{gpu.PB_DEFAULT}"
            f"-cpl{gpu.CAND_PER_LAUNCH4.bit_length() - 1}"
            f"w{gpu.CAND_PER_LAUNCH_WIDE.bit_length() - 1}")


def ckpt_path(fam):
    return str(HERE / f"campaign_checkpoint_{ref.family(fam).lower()}.json")


def ledger_path(fam):
    return str(HERE / "evidence" / f"{ref.family(fam).lower()}_discoveries.json")


# EVERY reader of the checkpoint goes through this object and none of them
# takes a key list of its own (CONVENTIONS.md "Reading an existing cursor").
_POLICIES = {fam: checkpoint.CursorPolicy(
                 ckpt_path(fam), config_key(fam),
                 accept=tuple(config_key(fam, engine=e) for e in PREVIOUS_ENGINES),
                 adopt=())
             for fam in ref.FAMILIES}


# ------------------------------- the taxonomy -------------------------------

def event_kind(run, settled):
    """DISCOVERY / NEAR / CENSUS / None -- the repo-wide rule, this
    project's mathematics.  `settled` is the set of indices whose term is
    known (published or found); a run is EXACT here, so a run of r is a
    candidate for a(r) and for nothing else.

        a(r) not settled                 DISCOVERY (the first prime whose
                                         run is exactly r: the line below
                                         it was swept at a filter <= r)
        a(r) settled, a(r+1) not         NEAR: one condition short of an
                                         open term
        both settled, r >= CENSUS_FLOOR  CENSUS
    """
    run = int(run)
    if run not in settled:
        return "DISCOVERY"
    if run < CENSUS_FLOOR:
        return None
    if run + 1 not in settled:
        return "NEAR"
    return "CENSUS"


def stopper_of(fam, x, run):
    """The value at index run + 1, which must be COMPOSITE for the run to be
    exactly `run`."""
    return int(x) + ref.shift_k(ref.family(fam), int(run) + 1)


STOPPER_NOTE = ("no factor was found within the bounded effort; a failed "
                "strong probable-prime test to the base given is a proof of "
                "compositeness")


def verify(x, run, fam, witness=True):
    """The three independent confirmations plus the bounding witness.

    1. huntlib's Miller-Rabin over every value of the run (p itself is a
       value), a PROOF below the proof crossing;
    2. sympy's BPSW, an independent implementation, which must agree that
       the run is EXACTLY `run` -- no shorter and no longer -- and on the
       domain, not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense line and uses no wheel at all, must
       agree that p survives a sieve at a DIFFERENT depth from the
       campaign's, at the filter the run reaches.

    plus the witness that the value at index run + 1 is COMPOSITE, which is
    what makes the run exact: a prime factor where the bounded effort finds
    one (the squared shifts put that value near 1e50), else the base of a
    failed strong probable-prime test, which is a proof as well.
    witness=False is the [NEAR] path: verified, not evidenced, no factoring.
    """
    fam = ref.family(fam)
    x, run = int(x), int(run)
    vals = ref.values(fam, x, run)
    # the re-sieve is only a proof where every value exceeds the depth: a
    # term in the exception zone is re-sieved to just under itself
    q2 = min(4096, min(vals) - 1)
    legs = {"mr_chain": all(mr_is_prime(v) for v in vals),
            "domain": cpu.in_domain_fast(fam, x) and ref.in_domain(fam, x),
            "sympy_bpsw": ref.run_length(fam, x, cap=run + 1) == run,
            "resieve_other_wheel": (q2 < 2 or
                                    cpu.CpuEngine(max(run, 1), fam, q2=q2).survives(x))}
    stop = stopper_of(fam, x, run)
    base2 = sprp_base2(stop)
    legs["stopper_composite"] = (not base2) or not mr_is_prime(stop)
    ok = all(legs.values())
    out = {"n": run + 1, "value": stop, "factor": None, "why": "composite"}
    if witness and legs["stopper_composite"]:
        out["factor"] = stopper_witness(stop)
        if out["factor"] is None:
            out["sprp_base"] = None if base2 else 2
            out["note"] = (STOPPER_NOTE if not base2 else
                           "no factor was found within the bounded effort and "
                           "the value is a base-2 strong pseudoprime; the "
                           "thirteen-base chain proves it composite")
    return ok, legs, out


WITNESS_FULL_BELOW = 10 ** 30


def stopper_witness(stop):
    """A nontrivial prime factor of the composite stopper, or None if the
    bounded effort (trial division, rho, 200 ECM curves) found none."""
    fac, _R = certificate.factor_partial(int(stop), ecm_curves=200)
    if fac:
        return int(min(int(f) for f in fac))
    if stop < WITNESS_FULL_BELOW:
        w = factor_witness(int(stop))
        return int(w) if w and w > 1 else None
    return None


# THE CERTIFICATE ROUTE.  No value here has multiplier x term +- 1
# structure (p + the shift, less one, is a number like any other), so each
# value is proved by huntlib.certificate.prove's own bounded search on
# N -+ 1, then ONE retry with more ECM.  The height it is trusted to is
# runs_search.V_CEIL, measured (OPTIMIZATION_LOG.md Measurement 1).
CERT_RETRY_CURVES = 200
CERT_RETRY_SPLITS = 16


def certify_value(N):
    """A RE-VERIFIED primality certificate for one value, or None."""
    N = int(N)
    proof = certificate.prove(N)
    if proof is not None and not certificate.verify(proof)[0]:
        proof = None
    if proof is None:
        proof = certificate.prove(N, ecm_curves=CERT_RETRY_CURVES,
                                  budget=CERT_RETRY_SPLITS)
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
    return proof


def certify_run(x, run, fam):
    """A re-verified certificate for every value of a run: ({key: proof},
    [the keys left UNPROVED]).  Keys are the index of the shift, "0" for
    the term itself."""
    fam = ref.family(fam)
    certs, unproved = {}, []
    for i, c in enumerate(ref.constants(fam, int(run))):
        key = str(i)
        proof = certify_value(int(x) + c)
        certs[key] = proof
        if proof is None:
            unproved.append(key)
    return certs, unproved


def also_settles(fam, x, run, settles):
    """What a find settles in DERIVED entries: none here."""
    ref.family(fam)
    return []


# ----------------------------- classification -------------------------------

def filter_forms(fam, n, cap=None):
    """The shifts c(1)..c(cap) as plain ints, for a pool worker (cap
    defaults to n + RUN_AHEAD).  A worker is another process; it is handed
    what it needs."""
    fam = ref.family(fam)
    cap = int(n) + RUN_AHEAD if cap is None else int(cap)
    return tuple(int(c) for c in ref.constants(fam, cap)[1:])


def sprp_run(x, forms, cap, floor=CENSUS_FLOOR):
    """The run of x (runs_reference.run_length) read to `cap`, screened
    with a base-2 strong test and CONFIRMED with the deterministic chain
    wherever the answer matters.

    A failed base-2 test is a PROOF of compositeness (huntlib.primes), so
    the screen can only overstate a run, never understate it; a run that
    comes out below the census floor is never looked at again, one at or
    above it is recomputed with the full base set.
    """
    x, cap = int(x), int(cap)

    def chain(test):
        if not test(x):
            return 0
        r = 0
        for c in forms:
            if r >= cap:
                break
            v = x + c
            if v < 2 or not test(v):
                break
            r += 1
        return r

    r = chain(sprp_base2)
    if r < floor:
        return r
    return chain(mr_is_prime)


def _classify_chunk(task):
    """Pool worker: runs of a chunk of survivors, in order."""
    forms, cap, ks = task
    return [sprp_run(int(k), forms, cap) for k in ks]


def _worker_init():
    _pool.worker_init("numpy", "sympy")


def _pool_factory(workers):
    return _cf.ProcessPoolExecutor(max_workers=workers,
                                   initializer=_worker_init)


class _Done:
    def __init__(self, value):
        self._v = value

    def done(self):
        return True

    def result(self):
        return self._v


def _submit(pool, forms, cap, ks):
    ks = [int(k) for k in ks]
    out = []
    for i in range(0, len(ks), CHUNK):
        chunk = ks[i:i + CHUNK]
        if pool is None:
            out.append((chunk, _Done(_classify_chunk((forms, cap, chunk)))))
        else:
            out.append((chunk, pool.submit(_classify_chunk,
                                           (forms, cap, chunk))))
    return out


def condition(fam, k):
    """The condition at shift index k in the entry's own letters."""
    fam = ref.family(fam)
    t = TERM(fam)
    if k == 0:
        return f"{t} prime"
    return f"{t} + {SHIFT(fam)}({k})"


def headline(fam, settles, x):
    fam = ref.family(fam)
    return f"{fam} a({settles[0]}) = {int(x):,}"


def evidence_name(fam, n, x):
    return f"{ref.family(fam)}_a{int(n)}_{int(x)}.json"


# --------------------------------- campaign ---------------------------------

class Campaign:
    def __init__(self, args, ckpt=None, cursor=None, pool=None, evid=None):
        self.args = args
        self.fam = ref.family(args.family)
        self.oeis = self.fam
        self.term = TERM(self.fam)
        # DRILLS ONLY: open below the published frontier so that a drill's
        # "find" is a real published term (the published terms above
        # `start_n - 1` then count as unsettled); and stop before the filter
        # of `stop_n`, ignoring every run from `stop_n` up, so a drill never
        # sweeps or settles an open index (CLAUDE.md 0a).
        self._known_top = (int(args.start_n) - 1 if getattr(args, "start_n", None)
                           else max(ref.KNOWN[self.fam]))
        self._stop_n = (int(args.stop_n) if getattr(args, "stop_n", None)
                        else None)
        self.key = config_key(self.fam)
        self.ckpt = ckpt or ckpt_path(self.fam)
        self.cursor = cursor or _POLICIES[self.fam]
        self.pool = pool
        self.evid = evid or EVID
        self.ledger = (str(pathlib.Path(evid) / "ledger.json") if evid
                       else ledger_path(self.fam))
        self.found = {}                # str(n) -> x found by THIS campaign
        self.census = {}
        self.passed = []
        self.elapsed = 0.0
        self.discoveries = 0
        self.near = 0
        self.survivors = 0
        self._stored_n = None
        self.j = None
        self.u = 0
        self.pending = []
        self._stored_w = 0
        self.hb = Heartbeat(interval=args.heartbeat)
        self._lad = LiveLadder(self._build_ladder)
        self._t0 = time.time()
        self.workers = None
        self._sizing = None
        self._hostwait = 0.0
        # the p below which the line is covered by an EARLIER filter's
        # classified sweep (the carried line); the sweep of the current
        # filter starts at max(the bottom of the line, this)
        self.cover_x = 0
        # the filter whose exception zone has been covered by brute force
        self.zone_n = 0
        self.start_x = 0               # where this campaign first started
        self._hw_ref = (0.0, time.time())
        self._hostbound_logged = False
        self._ckpt_t = 0.0
        self._ckpt_every_s = CKPT_MIN_S
        self._plog_t = 0.0
        self._plog_n = 0
        self._snapshot = None
        self._proof_logged = None
        self._load_kind = None
        self._stored_units = (0, 0)
        self.loaded = self.load()
        self.eng = self._build_engine(self.filter_n())
        if self._stored_n is not None and self._stored_n != self.filter_n():
            raise ValueError(
                f"{self.ckpt} holds a cursor for filter n = {self._stored_n} "
                f"but this campaign's lowest open term is a({self.filter_n()}): "
                f"the stored `found` and the stored filter disagree, so the "
                f"cursor cannot be read")
        if self._stored_w and self._stored_w != int(self.eng.W):
            raise ValueError(
                f"{self.ckpt} counts periods of W = {self._stored_w:,} but "
                f"this engine's period at n = {self.filter_n()} is "
                f"{int(self.eng.W):,}: the cursor means something else and "
                f"has to be re-denominated, not read")
        if self.loaded and self.u:
            units = (int(self.eng.seg_periods),
                     int(self.eng.launches_per_segment))
            if self._stored_units != units:
                log("STAGE",
                    f"work cursor not carried: launch {self.u:,} was counted "
                    f"in segments of {self._stored_units[0]} periods and "
                    f"{self._stored_units[1]:,} launches, this engine's are "
                    f"{units[0]} and {units[1]:,}; the segment at period "
                    f"{self.j} is re-swept from its start")
                self.u = 0
        if self.j is None:
            self.j, self.u = self.floor_period(), 0
            self.start_x = self.x_start()
        self.boundary = self.j
        self._discoveries_at_start = self.discoveries
        self.mark_boundary()

    def _build_engine(self, n):
        ok, q = ref.admissible(self.fam, n)
        if not ok:                     # a theorem says never; checked anyway
            banner("MILESTONE", [
                f"{self.oeis} IS FINITE: at index {n} the conditions kill "
                f"EVERY residue class mod {q}"])
            raise SystemExit(0)
        unit, p1, p2, p3, q2, pb = plan_for(self.fam, n)
        return gpu.GpuEngine(n, self.fam, p1=p1, p2=p2, p3=p3, q2=q2,
                             unit=unit, pb=pb, seg_cap=pb)

    # ------------------------------------------------------------- frontier
    def frontier(self):
        """The index below the LOWEST open one.  A term found above an open
        index (an early find) does not move it."""
        top = self._known_top
        while str(top + 1) in self.found:
            top += 1
        return top

    def settled(self):
        """The indices whose term is settled: the published ones this
        campaign builds on, and its own finds."""
        s = set(range(ref.offset(self.fam), self._known_top + 1))
        s.update(int(n) for n in self.found)
        return s

    def early(self):
        """The indices found ABOVE the lowest open one, sorted."""
        f = self.frontier()
        return tuple(sorted(int(n) for n in self.found if int(n) > f))

    def open_indices(self, count=3):
        """The next `count` unsettled indices from the filter up, none past
        the last index a discovery could be certified at."""
        s, out, n = self.settled(), [], self.filter_n()
        top = cpu.n_max(self.fam)
        while len(out) < count and n <= top:
            if n not in s:
                out.append(n)
            n += 1
        return out

    def filter_n(self):
        return self.frontier() + 1

    def x_start(self):
        """The floor of THIS filter's sweep: the bottom of the line, or the
        carried coverage of the earlier filters, whichever is higher."""
        return max(x_floor(self.fam, self.filter_n()), int(self.cover_x))

    def floor_period(self):
        return self.x_start() // int(self.eng.W)

    def k_min(self):
        """The clip for the segment being worked: the first x the device
        may report while the sweep is inside the segment that holds the
        floor (above the engine floor, whose zone is the host's), none
        after."""
        st = max(self.x_start(), cpu.k_floor(self.eng.q2, self.filter_n(), self.fam) + 1)
        return st if self.j * int(self.eng.W) <= st else None

    def run_cap(self):
        """How far past the filter the POOL reads a survivor's run:
        RUN_AHEAD, or in a drill no further than the last index it was
        opened to find.  A run that reaches it is re-read exactly (handle)."""
        cap = self.filter_n() + RUN_AHEAD
        if self._stop_n is not None:
            cap = min(cap, self._stop_n - 1)
        return cap

    def zone(self):
        """(lo, hi) of this filter's exception zone above the sweep's floor,
        or None."""
        lo = self.x_start()
        hi = cpu.k_floor(self.eng.q2, self.filter_n(), self.fam)
        return (lo, hi) if lo <= hi else None

    # ----------------------------------------------------------------- rungs
    def _build_ladder(self, frontier, early, n):
        ceil = cpu.k_ceil(n, self.fam)
        preds = model.predictions_open(self.fam, self.open_indices(),
                                       ceiling=ceil)
        return Ladder.from_predictions(preds, ceiling=ceil,
                                       ceiling_label="engine ceiling")

    def ladder(self):
        # the key carries the early finds: one retires its rungs
        return self._lad.get(self.frontier(), self.early(), self.filter_n())

    def next_rung(self, k):
        return self.ladder().next_rung(k, self.frontier())

    def check_rungs(self, k):
        lad = self.ladder()
        for lab in lad.newly_passed(k, self.frontier(), self.passed):
            self.passed.append(lab)
            nxt = lad.next_rung(k, self.frontier())
            log("RUNG", f"passed {lab}" +
                (f" -- next: {nxt[0]} at {nxt[1]:.4g}" if nxt else ""))

    # ------------------------------------------------------ proof crossing
    def proof_crossing(self):
        return cpu.k_proof(self.filter_n(), self.fam)

    def check_proof_crossing(self, k):
        if self._proof_logged == self.filter_n():
            return
        pc = self.proof_crossing()
        if k >= pc:
            self._proof_logged = self.filter_n()
            where = (f"{self.term} = {pc:.4g}" if pc > self.x_start() else
                     f"the bottom of the line ({SHIFT(self.fam)}"
                     f"({self.filter_n()}) alone passes the bound)")
            log("MILESTONE",
                f"past the proof crossing of {self.oeis} at filter n = "
                f"{self.filter_n()}, {where}: the largest "
                f"value formed now exceeds the deterministic Miller-Rabin "
                f"bound, so classification is a thirteen-base strong "
                f"probable-prime chain from here (the census is counted and "
                f"a NEAR is a health check either way) and a DISCOVERY's "
                f"values are each proved by a certificate on N - 1 or N + 1 "
                f"found by a bounded search (certify_value), re-verified "
                f"before it is written; the ceiling is {self.term} < "
                f"{cpu.k_ceil(self.filter_n(), self.fam):.4g} and values "
                f"under {cpu.V_CEIL:.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "plan": PLAN_VERSION,
                "family": self.fam,
                "n": int(self.eng.n),
                "q2": int(self.eng.q2),
                "wheel": [self.eng.p1, self.eng.p2, self.eng.p3],
                "unit": int(self.eng.unit),
                "j": int(self.j),
                "u": int(self.u),
                "seg_periods": int(self.eng.seg_periods),
                "launches_per_segment": int(self.eng.launches_per_segment),
                "W": int(self.eng.W),
                "k": int(self.swept_k()),
                "k_start": int(self.x_start()),
                "start_x": int(self.start_x),
                "cover_x": int(self.cover_x),
                "zone_n": int(self.zone_n),
                "pending": [[int(k), int(r)] for k, r in self.pending],
                "found": dict(self.found),
                "census": {str(r): c for r, c in sorted(self.census.items())},
                "passed": list(self.passed),
                "elapsed": self.elapsed + (time.time() - self._t0),
                "discoveries": self.discoveries,
                "near": self.near,
                "survivors": self.survivors,
                "saved": time.strftime("%Y-%m-%d %H:%M:%S")}

    def mark_boundary(self):
        self._snapshot = self.state()

    def save(self):
        self.mark_boundary()
        t_save = time.perf_counter()
        landed = checkpoint.save(self.ckpt, self._snapshot)
        cost = time.perf_counter() - t_save
        self._ckpt_t = time.time()
        self._ckpt_every_s = max(CKPT_MIN_S, cost / CKPT_COST_FRACTION)
        return landed

    def save_due(self):
        return time.time() - self._ckpt_t >= self._ckpt_every_s

    def save_boundary(self):
        return checkpoint.save(self.ckpt, self._snapshot or self.state())

    def load(self):
        st, kind = self.cursor.load(warn=lambda m: log("STAGE", m))
        if not st:
            return False
        self._load_kind = kind
        self._stored_w = int(st.get("W", 0))
        self._stored_n = st.get("n")
        self._stored_units = (int(st.get("seg_periods", 0)),
                              int(st.get("launches_per_segment", 0)))
        self.j = int(st["j"])
        self.u = int(st.get("u", 0))
        self.pending = [(int(k), int(r)) for k, r in st.get("pending", [])]
        self.cover_x = int(st.get("cover_x", 0))
        self.zone_n = int(st.get("zone_n", 0))
        self.start_x = int(st.get("start_x", 0))
        self.found = dict(st.get("found", {}))
        self.census = {int(r): int(c) for r, c in st.get("census", {}).items()}
        self.passed = list(st.get("passed", []))
        self.elapsed = float(st.get("elapsed", 0.0))
        self.discoveries = int(st.get("discoveries", 0))
        self.near = int(st.get("near", 0))
        self.survivors = int(st.get("survivors", 0))
        return True

    def swept_k(self):
        """The x below which EVERY value at or above the sweep's floor has
        been swept -- the coverage claim.  It is the period boundary, or
        the floor itself while the boundary is still under it (the first
        segment of a line, and the carried boundary after a promotion)."""
        return max(self.boundary * self.eng.W, self.x_start())

    def u_progress(self, jn, un):
        return self.eng.progress_k(jn, un)

    def segment_end(self):
        jmax = cpu.k_ceil(self.filter_n(), self.fam) // self.eng.W
        return min(self.j + self.eng.seg_periods, jmax)

    # ------------------------------------------------------------- status
    def status_line(self):
        k = (self.hb.pos() or self.swept_k())
        cov = self.swept_k()
        rate = self.hb.rate()
        lo = self.boundary * self.eng.W
        seg = self.eng.seg_periods
        pct = min(100.0, max(0.0, 100.0 * (k - lo) / (seg * self.eng.W)))
        parts = [f"swept to {self.swept_k():.6g}",
                 f"periods [{self.boundary}, {self.boundary + seg}) "
                 f"[{lo:.5g}, {lo + seg * self.eng.W:.5g}) {pct:.0f}%",
                 f"{self.oeis} filter n = {self.filter_n()}"]
        if rate:
            parts.append(f"{rate:.3g} {self.term}/s")
        parts.append(census_str(self.census, CENSUS_FLOOR, max(self.settled())))
        parts.append(f"finds {self.discoveries}")
        parts.append(f"survivors {self.survivors:,}")
        if self.workers:
            hw, t_ref = self._hw_ref
            now = time.time()
            frac = (self._hostwait - hw) / max(now - t_ref, 1e-9)
            self._hw_ref = (self._hostwait, now)
            parts.append(f"pool {self.workers}" +
                         (f" HOST-BOUND {100 * frac:.0f}% of the interval"
                          if frac >= 0.005 else ""))
        nr = self.next_rung(cov)
        if nr:
            lab, d = nr
            if d > k:
                eta = eta_str(d - k, rate) if rate else "?"
            else:
                eta = "inside the period being worked"
            parts.append(f"next {lab} {d:.4g} (ETA {eta})")
            p = model.p_by(self.fam, self.filter_n(),
                           x_floor(self.fam, self.filter_n()), cov)
            parts.append(f"P(a({self.filter_n()}) under the claim) = "
                         f"{100 * p:.0f}%")
        stall = self.hb.stalled()
        if stall:
            parts.append(f"-- no segment closed since the last status: "
                         f"{stall[0]} for {stall[1]:.0f}s")
        return "  ".join(parts)

    # --------------------------------------------------------------- hits
    def handle(self, k, run):
        """Classify one value.  True if it was a find."""
        if run >= self.run_cap():
            # the pool reads to a cap; the run that decides is exact
            run = cpu.run_length_fast(self.fam, k, cap=RUN_EXACT_CAP)
        if self._stop_n is not None and run >= self._stop_n:
            # a drill neither narrates nor settles an index past its bound
            return False
        settled = self.settled()
        kind = event_kind(run, settled)
        if kind is None:
            return False
        self.census[run] = self.census.get(run, 0) + 1
        if kind == "CENSUS":
            return False
        if kind == "NEAR":
            self.near += 1
            ok, legs, _ = verify(k, run, self.fam, witness=False)
            if not ok:
                log("ALARM", f"NEAR candidate {self.term} = {k:,} run {run} "
                             f"failed verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at {self.term} = {k:,} (run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of a({run + 1})!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, x, run):
        n = self.filter_n()
        x, run = int(x), int(run)
        self.hb.doing(f"verifying run-{run} {self.term}={x}")
        # the oracle, from the bare definition: a prime whose run is
        # EXACTLY `run`, at an index this sweep covers and nobody has settled
        if (not ref.is_term(self.fam, x, run) or run < n
                or run in self.settled()):
            log("ALARM", f"claimed {self.oeis} a({run}) = {x} is not a first "
                         f"occurrence by the oracle: its run is "
                         f"{ref.run_length(self.fam, x)}, the filter is n = "
                         f"{n}, settled {sorted(self.settled())}")
            raise SystemExit(2)
        ok, legs, stop = verify(x, run, self.fam)
        if not ok:
            log("ALARM", f"claimed a({run}) = {x} failed the "
                         f"protocol: {legs}")
            raise SystemExit(2)
        settles = [run]
        self.hb.doing(f"certifying run-{run} {self.term}={x}")
        certs, unproved = certify_run(x, run, self.fam)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        also = also_settles(self.fam, x, run, settles)
        cs = ref.constants(self.fam, run)
        stopper = {ref.FAMILIES[self.fam]["index"]: stop["n"],
                   "condition": condition(self.fam, stop["n"]),
                   "value": int(stop["value"]),
                   "why": stop["why"],
                   "factor": stop["factor"]}
        for extra in ("sprp_base", "note"):
            if extra in stop:
                stopper[extra] = stop[extra]
        ev = {**evidence.header(self.oeis, ref.FAMILIES[self.fam]["forms"],
                                self.term, x, settles),
              "filter_n": int(n), "run": int(run), "settles": settles,
              "conditions": {str(i): condition(self.fam, i)
                             for i in range(len(cs))},
              "values": {str(i): int(x + c) for i, c in enumerate(cs)},
              "verification": legs,
              "stopper": stopper,
              "certificates": certs,
              "certificates_verified": not unproved,
              "unproved": unproved,
              "proof_routes": routes,
              "also_settles": also,
              "least_claim": {"claim": (f"no prime below {self.term} = {x} "
                                        f"has a run of exactly {run}"),
                              "basis": (f"every prime from the bottom of the "
                                        f"line to {self.term} with a run of "
                                        f"at least the filter was read to "
                                        f"its exact run, at filters <= {run} "
                                        f"throughout"),
                              "swept_from": int(self.x_start()),
                              "campaign_started_at": int(self.start_x),
                              "swept_to": int(x),
                              "floor": "2: every index's line starts at the "
                                       "bottom, the sequence is not monotone",
                              "carried": (f"the line below {self.cover_x} was "
                                          f"classified by the earlier filters "
                                          f"(each at an index <= {run}) with "
                                          f"every run read exactly"
                                          if self.cover_x else None),
                              "exception_zone": list(self.zone()) if self.zone() else None,
                              "filter": int(n),
                              "wheel": int(self.eng.W),
                              "sieve_depth": int(self.eng.q2),
                              "class": [int(self.eng.r0), int(self.eng.unit)]},
              "engine": self.key}
        self.found[str(run)] = int(x)
        path = evidence.record(
            ev, self.evid, evidence_name(self.oeis, run, x),
            self.ledger, key=self.term,
            label="%s a(%d)" % (self.oeis, run))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        sh = SHIFT(self.fam)
        lines = [
            headline(self.oeis, settles, x),
            f"run exactly {run}: {self.term} + {sh}(1), ..., {self.term} + "
            f"{sh}({run}) all prime"
            + (f" (found EARLY: the filter is n = {n} and a({n}) is still "
               f"open)" if run > n else ""),
            f"stopped at {condition(self.fam, stop['n'])} = "
            f"{stop['value']:,}, composite"
            + (f" = {stop['factor']} x ..." if stop["factor"] else
               " (no factor within the bounded effort; a failed strong "
               "probable-prime test is the witness)"),
            f"verified 3 ways, {proved} of {len(certs)} certificates "
            f"re-verified ({', '.join(f'{r} x{c}' for r, c in sorted(routes.items()))}), "
            f"evidence {path}"]
        if unproved:
            lines.append(f"UNPROVED at shift index {unproved}: those values "
                         f"passed the Miller-Rabin chain and BPSW and no "
                         f"certificate landed within the bounded effort; "
                         f"the find stands on the three legs; certify them "
                         f"by hand from the evidence file")
        banner("DISCOVERY", lines)

    def follow_frontier(self, old_boundary_x):
        """After a find at the filter: rebuild the engine at the next open
        index (it may be several up, past indices found early).  The
        classified line is CARRIED and the sweep resumes at the old
        segment's end, re-denominated by floor into the new period with the
        clip at the old boundary."""
        old = self.eng
        self.cover_x = int(old_boundary_x)
        self.eng = self._build_engine(self.filter_n())
        self.j = self.floor_period()
        self.u = 0
        self.boundary = self.j
        self.pending = []
        log("STAGE",
            f"filter follows the frontier: n = {old.n} -> {self.eng.n}; the "
            f"wheel ({old.p1},{old.p2},{old.p3}) becomes "
            f"({self.eng.p1},{self.eng.p2},{self.eng.p3}), the class "
            f"{old.r0} (mod {old.unit}) becomes {self.eng.r0} (mod "
            f"{self.eng.unit}), the depth {old.q2} becomes {self.eng.q2}, the "
            f"period {old.W:.4g} becomes {self.eng.W:.4g}, the segment "
            f"{old.seg_periods} -> {self.eng.seg_periods} periods on the "
            f"{'WIDE' if self.eng.wide else 'narrow'} survivor record; "
            f"the line below {self.cover_x:,} is CARRIED (every prime on it "
            f"with a run of at least {old.n} was read to its exact run) and "
            f"the sweep resumes there, floored into the new period "
            f"{self.j} with the clip at the old boundary"
            + f"; the ladder now aims at a({self.filter_n()})")
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({m})")
                                  for m in self.found)]
        self._proof_logged = None
        self.cover_zone()
        self.check_proof_crossing(self.swept_k())
        self.size_pool()
        self.mark_boundary()

    # ------------------------------------------------------------ the zone
    def cover_zone(self):
        """Classify the exception zone of this filter on the host, once per
        filter: every integer in the forced class between the sweep's floor
        and the engine's floor, each run read exactly, through the same
        taxonomy as a device survivor (2 and 3, outside the class, have
        published runs under the census floor).  Returns True if a find
        landed there."""
        n = self.filter_n()
        if self.zone_n == n:
            return False
        z = self.zone()
        found_now = False
        if z is not None:
            lo, hi = z
            self.hb.doing(f"covering the exception zone [{lo:,}, {hi:,}]")
            t0 = time.perf_counter()
            hits = cpu.prefix_hits(self.fam, n, self.eng.q2, floor=CENSUS_FLOOR,
                                   cap=RUN_EXACT_CAP)
            # only the part of the zone above the sweep's floor
            hits = [(x, r) for x, r in hits if x >= lo]
            cnt = sum(1 for _ in range(lo, hi + 1))
            for x, r in hits:
                self.survivors += 1
                if self.handle(x, r):
                    found_now = True
            log("STAGE",
                f"exception zone of {self.oeis} at filter n = {n}: the "
                f"{cnt:,} integers in [{lo:,}, {hi:,}] -- between the "
                f"definition's floor and the engine's (a kill by q <= "
                f"{self.eng.q2} needs the value to exceed q) -- classified "
                f"one at a time on the host in {time.perf_counter() - t0:.1f} "
                f"s: {len(hits)} at run >= {CENSUS_FLOOR}"
                + (", a FIND among them" if found_now else ""))
        self.zone_n = n
        return found_now

    # ----------------------------------------------------------- the pool
    def calibrate(self):
        sync = self.eng.cp.cuda.Stream.null.synchronize
        nl = self.eng.launches_per_segment
        jmax = cpu.k_ceil(self.filter_n(), self.fam) // self.eng.W
        j_end = min(self.j + self.eng.seg_periods * CAL_SEGMENTS, jmax)
        it = self.eng.sweep(self.j, j_end, u_from=self.u, k_min=self.k_min())
        surv, launches, u_prev, cov = [], 0, self.u, 0
        sync()
        t0 = time.perf_counter()
        try:
            for _jn, un, sv in it:
                launches += 1
                cov += (un if un else nl) - u_prev
                u_prev = un
                surv.extend(int(k) for k in sv)
                sync()
                el = time.perf_counter() - t0
                if (el >= CAL_MAX_S
                        or (len(surv) >= CAL_MIN_SURVIVORS and el >= CAL_MIN_S)):
                    break
        finally:
            it.close()
        dt = max(time.perf_counter() - t0, 1e-9)
        line = cov * self.eng.W * self.eng.seg_periods / max(nl, 1)
        cap = self.run_cap()
        forms = filter_forms(self.fam, self.filter_n())
        sample = surv[:CAL_SAMPLE]
        t1 = time.perf_counter()
        for k in sample:
            sprp_run(k, forms, cap)
        cost = (time.perf_counter() - t1) / max(len(sample), 1)
        per_s = len(surv) / dt
        return {"launches": launches, "seconds": dt,
                "rate": line / dt,
                "survivors": len(surv), "per_s": per_s, "cost": cost,
                "need": per_s * cost}

    def size_pool(self):
        if self.args.workers is not None:
            want = max(1, int(self.args.workers))
            inline = want == 1
            how = f"--workers {want}"
        else:
            m = self.calibrate()
            self._sizing = m
            want = max(1, math.ceil(m["need"] * POOL_MARGIN))
            inline = False
            how = (f"measured on {m['launches']} launches, {m['seconds']:.2f} "
                   f"s of device at {m['rate']:.3g} {self.term}/s: "
                   f"{m['per_s']:,.0f} "
                   f"survivors/s x {1e6 * m['cost']:.1f} us = {m['need']:.2f} "
                   f"core-s per s, x{POOL_MARGIN:g} margin")
            cap = max(1, (os.cpu_count() or 2) - 1)
            if want > cap:
                log("WARN", f"the host binds: this filter needs {want} "
                            f"workers and the machine offers {cap}; the "
                            f"device will wait on the pool (back-pressure) "
                            f"and every [STATUS] line will say so")
                want = cap
        have = self.workers is not None and (self.pool is not None
                                             or self.workers == 1)
        if have and (want == self.workers
                     or (want < self.workers and 2 * want > self.workers)):
            return self.workers
        if self.pool is not None:
            self.pool.shutdown(wait=True, cancel_futures=True)
            self.pool = None
        self.workers = want
        if inline:
            log("STAGE", f"classification inline in the main thread ({how})")
            return want
        self.pool = _pool_factory(want)
        t_ramp = time.time()
        up = _pool.ramp(self.pool, want, ramp_s=self.args.worker_ramp)
        log("STAGE", f"classification pool: {up} workers ({how}), ramped "
                     f"one at a time at {self.args.worker_ramp:.2f} s in "
                     f"{time.time() - t_ramp:.1f} s, below-normal priority")
        return want

    def _backpressure(self, inflight):
        if len(inflight) <= BACKLOG_LAUNCHES:
            return
        t0 = time.perf_counter()
        while len(inflight) > BACKLOG_LAUNCHES:
            _cur, parts = inflight[0]
            for _ks, f in parts:
                f.result()
            self._drain(inflight, block=False)
        self._hostwait += time.perf_counter() - t0
        if not self._hostbound_logged:
            self._hostbound_logged = True
            log("WARN", f"host-bound: the classification pool ({self.workers} "
                        f"workers) is not keeping up with the device, which "
                        f"now waits on it ({BACKLOG_LAUNCHES} launches of "
                        f"back-pressure); the [STATUS] line carries the "
                        f"fraction of wall clock spent waiting")

    def _drain(self, inflight, block):
        while inflight:
            cur, parts = inflight[0]
            if not block and not all(f.done() for _ks, f in parts):
                break
            inflight.popleft()
            for ks, f in parts:
                for k, r in zip(ks, f.result()):
                    self.survivors += 1
                    if r >= CENSUS_FLOOR:
                        self.pending.append((k, r))
            if cur[1]:
                self.j, self.u = cur
            else:
                self.u = 0
                self._period_done = True

    # ---------------------------------------------------------------- loop
    def run(self):
        target = int(self.args.to or cpu.k_ceil(self.filter_n(), self.fam))
        log("STAGE", f"campaign {self.key}")
        log("STAGE", device_report(self.eng.bytes_held()))
        cfg = self.eng.config()
        log("STAGE",
            f"sweeping the {self.term} line to {target:.4g}; {self.oeis} "
            f"({ref.FAMILIES[self.fam]['forms']}) filter n = "
            f"{self.filter_n()}; wheel W = {self.eng.W:,} at unit "
            f"{self.eng.unit} ({self.eng.R:,} residues, {self.eng.R1} x "
            f"{self.eng.R2} x {self.eng.R3}, {100.0 * self.eng.density():.6f}% "
            f"of the line); a segment is {self.eng.seg_periods} periods "
            f"({self.eng.seg_periods * self.eng.W:.4g} of line) in "
            f"{self.eng.launches_per_segment} launches of "
            f"{cfg['cand_per_launch']:.3g} candidates; the sweep's floor is "
            f"{self.term} = {self.x_start():,}; resume at period {self.j}, "
            f"launch {self.u} ({self.term} = {self.u_progress(self.j, self.u):,})")
        for n, qs in sorted(model.predictions_open(
                self.fam, self.open_indices(),
                ceiling=cpu.k_ceil(self.filter_n(), self.fam)).items()):
            log("STAGE", "  a(%d): %s" % (n, "  ".join(
                "%s %.4g" % (q, v) for q, v in qs.items())))
        log("STAGE", "the heartbeat carries TWO numbers: 'swept to' is the "
                     "point on the line below which EVERY candidate above "
                     "the floor has been tested, and it advances one whole "
                     "segment (%.4g of line) at a time; 'periods .. X%%' is "
                     "progress THROUGH the segment being worked, whose "
                     "candidates arrive out of numerical order."
                     % (self.eng.seg_periods * self.eng.W))
        self.check_proof_crossing(self.swept_k())
        self.size_pool()
        self.hb.mark(self.u_progress(self.j, self.u))
        self.hb.start(self.status_line)
        shutdown.on_interrupt(self._on_interrupt)
        stop_now = False
        self._plog_t = time.time()
        try:
            if self.cover_zone():
                if self.filter_n() != self.eng.n:
                    self.follow_frontier(self.boundary * self.eng.W)
                stop_now = bool(self.args.stop_on_discovery)
                self.save()
            cap = self.run_cap()
            forms = filter_forms(self.fam, self.filter_n())
            while self.swept_k() < target and not stop_now:
                if self._stop_n is not None and self.filter_n() >= self._stop_n:
                    log("STAGE", f"drill bound: this drill campaign stops "
                                 f"before the filter for a({self.filter_n()})")
                    break
                if self.filter_n() > cpu.n_max(self.fam):
                    log("STAGE",
                        f"the lowest open index of {self.oeis}, "
                        f"{self.filter_n()}, is past n = "
                        f"{cpu.n_max(self.fam)}, the last whose shift stays "
                        f"under the measured ceiling on the values "
                        f"({cpu.V_CEIL:.4g}): a discovery there could not be "
                        f"certified, so the campaign ends here")
                    break
                j1 = self.segment_end()
                if j1 <= self.j:
                    break
                self.hb.doing(f"sieving periods [{self.j}, {j1}) "
                              f"[{self.j * self.eng.W:.4g}, "
                              f"{j1 * self.eng.W:.4g})")
                inflight = collections.deque()
                self._period_done = False
                since = 0
                for jn, un, surv in self.eng.sweep(self.j, j1, u_from=self.u,
                                                   k_min=self.k_min()):
                    inflight.append(((jn, un),
                                     _submit(self.pool, forms, cap, surv)))
                    self._drain(inflight, block=False)
                    self._backpressure(inflight)
                    since += 1
                    if since >= CKPT_LAUNCHES and un and self.save_due():
                        since = 0
                        self.hb.mark(self.u_progress(self.j, self.u))
                        self.save()
                    if self.args.gpu_yield_ms:
                        time.sleep(self.args.gpu_yield_ms / 1000.0)
                    if un == 0:
                        break
                self.hb.doing(f"classifying the tail of periods "
                              f"[{self.j}, {j1})")
                self._drain(inflight, block=True)
                held = len(self.pending)
                found_now = False
                for k, r in sorted(self.pending):
                    if self.handle(k, r):
                        found_now = True
                self.pending = []
                self.j, self.u = j1, 0
                self.boundary = self.j
                self._plog_n += 1
                if found_now or time.time() - self._plog_t >= PERIOD_LOG_S:
                    log("STAGE",
                        f"periods [{j1 - self.eng.seg_periods}, {j1}) "
                        f"complete: swept to {self.swept_k():,} "
                        f"(+{self.eng.seg_periods * self.eng.W:.4g} of "
                        f"line; {held} value{'' if held == 1 else 's'} at "
                        f"run >= {CENSUS_FLOOR} classified in numerical "
                        f"order"
                        + (f"; {self._plog_n} segments closed since the last "
                           f"such line" if self._plog_n > 1 else "") + ")")
                    self._plog_t, self._plog_n = time.time(), 0
                if found_now:
                    # an early find (a run above the filter) leaves the
                    # filter where it is: a(n) is still open
                    if self.filter_n() != self.eng.n:
                        self.follow_frontier(self.boundary * self.eng.W)
                        cap = self.run_cap()
                        forms = filter_forms(self.fam, self.filter_n())
                    stop_now = bool(self.args.stop_on_discovery)
                self.hb.mark(self.swept_k())
                self.check_rungs(self.swept_k())
                self.check_proof_crossing(self.swept_k())
                if found_now or self.save_due():
                    self.save()
                else:
                    self.mark_boundary()
                if stop_now:
                    log("STAGE", "stopping on discovery "
                                 "(--stop-on-discovery): THIS run confirmed "
                                 "a first occurrence")
        finally:
            self.hb.stop()
            if self.pool is not None:
                self.pool.shutdown(wait=False, cancel_futures=True)
        landed = self.save()
        log("STAGE", f"campaign stopped at {self.term} = {self.swept_k():,} "
                     f"({self.discoveries} find(s) this campaign; checkpoint "
                     f"{'written' if landed else 'DEFERRED -- held open'})")
        return 0

    def _on_interrupt(self):
        snap = self._snapshot or self.state()
        if self.save_boundary():
            return (f"checkpoint written at the last classified launch: "
                    f"period {int(snap['j'])}, u = {int(snap['u'])}, swept "
                    f"to {self.term} = {int(snap['k']):,} ({self.ckpt})")
        return (f"{self.ckpt} is held open by another process, so THIS "
                f"boundary (period {int(snap['j'])}, u = {int(snap['u'])}) "
                f"was not written; the run resumes from the last save that "
                f"landed")


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """All four outcomes of the taxonomy, on this project's mathematics: at
    filter n = 16 (a(0)..a(15) settled) a run of exactly 16 is the open
    term, a longer one an EARLY find of its own index, 15 is one short."""
    base = frozenset(range(0, 16))
    early = base | {18}                     # a(18) found early, a(16) open
    both = early | {17}
    return [((16, base), "DISCOVERY"),      # the open term at the filter
            ((19, base), "DISCOVERY"),      # an early find, of a(19) alone
            ((15, base), "NEAR"),
            ((14, base), "CENSUS"),
            ((8, base), "CENSUS"),
            ((7, base), None),
            ((0, base), None),
            ((18, early), "NEAR"),          # settled early; a(19) is open
            ((17, early), "DISCOVERY"),
            ((16, early), "DISCOVERY"),
            ((17, both), "CENSUS"),         # a(17) and a(18) both settled
            ((18, both), "NEAR")]


# The canaries: (family, filter n, unit).  A sweep at filter n from the
# bottom of the line must meet ref.first_reach(family, n) FIRST -- the least
# published term of index >= n -- and read its run exactly: at A257466's
# n = 12 and A257467's n = 9 that is a term of the NEXT index (a(13) <
# a(12), a(10) < a(9)), the early-find path.
_CANARIES = (("A257466", 11, 1), ("A257466", 12, 6),
             ("A257467", 9, 1), ("A257467", 12, 6),
             ("A258035", 9, 1), ("A258035", 10, 6))


def _canary_hunt():
    """The stream must organically rediscover known terms, in every family,
    from the bottom of the line (the exception zone cleared on the host),
    so FIRST is a claim about the line."""
    hits_all = []
    for fam, n, unit in _CANARIES:
        if cpu.forced_unit(n, fam) % unit:
            return False, f"CANARY FAIL: unit {unit} is not forced at n = {n} of {fam}"
        m, want = ref.first_reach(fam, n)
        q2 = 4096
        eng = gpu.GpuEngine(n, fam, p1=13, p2=None, p3=None, q2=q2, unit=unit)
        pre = [x for x, r in cpu.prefix_hits(fam, n, q2, floor=n)]
        if pre:
            return False, f"CANARY FAIL: {fam} n={n}: the zone holds {min(pre)}"
        start = cpu.k_floor(q2, n, fam) + 1
        ceng = cpu.CpuEngine(n, fam, q2=q2)
        surv = eng.survivors_j(start // eng.W, want // eng.W + 1, k_min=start)
        hits = [int(k) for k in surv if ceng.run_length(int(k), cap=n) >= n]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: {fam} filter n={n} unit={unit} "
                           f"found {min(hits) if hits else None}, "
                           f"expected a({m}) = {want}")
        if cpu.run_length_fast(fam, want, cap=RUN_EXACT_CAP) != m:
            return False, f"CANARY FAIL: {fam} a({m}) = {want} did not read run {m}"
        hits_all.append(f"{fam} a({m}) at filter {n}" +
                        (f" (class {eng.r0} mod {unit})" if unit > 1 else ""))
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as the FIRST prime with a run of at "
                  "least the filter from the bottom of the line (the "
                  "exception zone cleared on the host), each read to its "
                  "exact run, in p space and in class space, every family")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on every family:
    exactness means a run one too long AND one too short are both wrong."""
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        ok, legs, stop = verify(x, top, fam)
        if not ok or stop["n"] != top + 1 or stop["why"] != "composite":
            return False, (f"PROTOCOL FAIL: genuine a({top}) = {x} ({fam}) "
                           f"rejected: {legs} {stop}")
        if stop["factor"] is not None:
            if stop["value"] % stop["factor"] or stop["factor"] in (1, stop["value"]):
                return False, f"PROTOCOL FAIL: {fam}: the witness is not a factor"
        elif stop.get("sprp_base") != 2 or sprp_base2(stop["value"]):
            return False, (f"PROTOCOL FAIL: {fam}: the stopper has neither a "
                           f"factor nor a failed base-2 test: {stop}")
        for wrong in (top + 1, top - 1):
            bad, legs_b, _ = verify(x, wrong, fam, witness=False)
            if bad:
                return False, (f"PROTOCOL FAIL: fake run-{wrong} claim at {x} "
                               f"({fam}) ACCEPTED ({legs_b})")
        # an earlier term mislabelled as the frontier's run
        fake, _lc, _ = verify(ref.KNOWN[fam][top - 2], top, fam, witness=False)
        if fake:
            return False, f"PROTOCOL FAIL: {fam}: a({top - 2}) accepted as a run-{top}"
        # the DOMAIN: a composite p in the forced class is rejected whatever
        # its shifts do
        y = x + 6
        while isprime(y):
            y += 6
        okd, legs_d, _ = verify(y, 0, fam, witness=False)
        if okd or legs_d["domain"]:
            return False, f"PROTOCOL FAIL: a composite p was accepted on {fam}"
    # a stopper nobody can factor in the bounded effort is still a witness:
    # the base of a failed strong probable-prime test
    semi = (10 ** 24 + 7) * (10 ** 24 + 43)
    if sprp_base2(semi) or mr_is_prime(semi):
        return False, "PROTOCOL FAIL: a 49-digit semiprime passed a primality test"
    return True, ("protocol ok, every family: each frontier term accepted at "
                  "its EXACT run with a witness for its composite stopper (a "
                  "prime factor, or the base of a failed strong "
                  "probable-prime test where the bounded effort finds none), "
                  "the same value claimed one run longer and one run shorter "
                  "both rejected, a mislabelled earlier term rejected, and a "
                  "composite p rejected by the domain leg")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing, on every family."""
    raised = []
    for fam, n in (("A257466", 15), ("A257467", 13), ("A258035", 10)):
        eng = gpu.GpuEngine(n, fam, p1=13, p2=None, p3=None, q2=1024)
        ceil = cpu.k_ceil(n, fam)
        try:
            eng.sweep(ceil // eng.W - 1, ceil // eng.W + 2)
            return False, f"CEILING FAIL: {fam}: the GPU engine swept past k_ceil"
        except ValueError:
            raised.append(f"gpu k_ceil ({fam})")
        try:
            eng.sweep(0, 2)
            return False, f"CEILING FAIL: {fam}: the GPU engine swept period 0 unclipped"
        except ValueError:
            raised.append(f"gpu floor ({fam})")
        try:
            eng.sweep(0, 2, k_min=cpu.k_floor(1024, n, fam))
            return False, f"CEILING FAIL: {fam}: a clip AT the floor was accepted"
        except ValueError:
            raised.append(f"gpu k_min <= floor ({fam})")
        c = cpu.CpuEngine(n, fam, q2=1024)
        try:
            c.survivors(cpu.k_floor(1024, n, fam) + 1, ceil + 10)
            return False, f"CEILING FAIL: {fam}: the CPU engine swept past k_ceil"
        except ValueError:
            raised.append(f"cpu k_ceil ({fam})")
        try:
            c.survivors(cpu.k_floor(1024, n, fam), cpu.k_floor(1024, n, fam) + 10 ** 5)
            return False, f"CEILING FAIL: {fam}: the CPU engine swept at the floor"
        except ValueError:
            raised.append(f"cpu floor ({fam})")
        if cpu.k_ceil(n, fam) != ceiling.K_CEIL or not cpu.k_proof(n, fam) < ceil:
            return False, f"CEILING FAIL: {fam}'s ceiling is not huntlib's K_CEIL"
        jc = ceil // eng.W
        eng._check_window(jc - 1, jc, None)
        try:
            eng._check_window(jc, jc + 1, None)
            return False, "CEILING FAIL: the first period past the ceiling was accepted"
        except ValueError:
            raised.append(f"gpu k_ceil tight to one period ({fam})")
        # THE VALUE CEILING: the last index is the last whose shift is under it
        nm = cpu.n_max(fam)
        if not ref.shift_k(fam, nm) < cpu.V_CEIL <= ref.shift_k(fam, nm + 1):
            return False, f"CEILING FAIL: {fam}'s n_max = {nm} is not tight to V_CEIL"
        raised.append(f"n_max = {nm} tight to the value ceiling ({fam})")
    try:
        gpu.wheel(7, "A257466", 53)
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(17, "A257466", p1=31, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    try:
        gpu.GpuEngine(7, "A257466", p1=13, p2=37, p3=None, q2=4096)
        return False, "CEILING FAIL: an oversized second level was accepted"
    except ValueError:
        raised.append("gridDim.y")
    # the residue list holds NRES_MAX kills a prime; one form kills one, so
    # an index of more forms than that is refused
    for fam, n in (("A257466", gpu.NRES_MAX), ("A257467", gpu.NRES_MAX + 1)):
        if ref.maxkills(fam, n) <= gpu.NRES_MAX:
            return False, f"CEILING FAIL: {fam} n = {n} fits the residue list"
        try:
            gpu.GpuEngine(n, fam, p1=13, p2=None, p3=None, q2=1024)
            return False, "CEILING FAIL: a filter whose kills overflow the tail's residue list was accepted"
        except ValueError:
            raised.append(f"maxkills <= NRES_MAX ({fam})")
    for unit in (30, 10, 12):
        try:
            gpu.GpuEngine(16, "A257466", p1=13, p2=None, p3=None, q2=1024, unit=unit)
            return False, f"CEILING FAIL: unit {unit}, which nothing forces, was accepted"
        except ValueError:
            raised.append(f"unit {unit} refused")
    try:
        gpu.GpuEngine(14, "A000001", p1=13, p2=None, p3=None, q2=1024)
        return False, "CEILING FAIL: an unknown family was accepted"
    except KeyError:
        raised.append("family")
    return True, ("ceiling ok: %s all raise rather than compute" %
                  ", ".join(raised))


_BLS_ROUTES = ("bls75-thm1", "bls75-thm5", "bls75-thm15")


def _check_cert(c, N, label):
    if c is None or c.get("proof") not in _BLS_ROUTES:
        return False, (f"{label}: not proved by a BLS75 route "
                       f"({c and c.get('proof')})")
    if int(c["N"]) != N:
        return False, f"{label}: the proof is not about the value"
    ok, why = certificate.verify(c)
    if not ok:
        return False, f"{label}: does not re-verify: {why}"
    if certificate.verify(dict(c, N=N + 2))[0]:
        return False, f"{label}: verified for a neighbouring N"
    if certificate.verify({"proof": "deterministic-mr", "N": N})[0]:
        return False, f"{label}: a bare deterministic-MR claim past the bound passed"
    return True, ""


def _certificate_drill():
    """A discovery past the proof crossing is PROVED, not just tested: each
    frontier term's values (the deterministic test under the bound, a BLS75
    route above it -- A257467's a(14) already has values of 32 digits); and
    AT THE VALUE CEILING, on every family: primes of a find's own shape,
    p + the last shift under V_CEIL, with the recursion exercised."""
    parts = []
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        certs, unproved = certify_run(x, top, fam)
        if unproved:
            return False, f"CERTIFICATE FAIL: {fam} a({top}) left {unproved} unproved"
        det = 0
        for key, c in certs.items():
            N = x + ref.constants(fam, top)[int(key)]
            want_det = N < MR_VALID_BELOW
            if (c.get("proof") == "deterministic-mr") != want_det or int(c["N"]) != N                     or not certificate.verify(c)[0]:
                return False, (f"CERTIFICATE FAIL: {fam} a({top})'s value {key} "
                               f"took the route {c.get('proof')}")
            det += want_det
        parts.append(f"{fam} a({top})'s {len(certs)} values ({det} "
                     f"deterministic, {len(certs) - det} by BLS75)")
    t0 = time.time()
    subbed = None
    for fam in ref.FAMILIES:
        nm = cpu.n_max(fam)
        c = ref.shift_k(fam, nm)
        r0, u = cpu.forced_class(nm, fam)
        x = 10 ** 22
        x = x - x % u + r0
        proved = 0
        for _ in range(40000):
            N = x + c
            if sprp_base2(N) and mr_is_prime(N):
                proof = certify_value(N)
                ok, why = _check_cert(proof, N, f"{fam} at n = {nm}")
                if not ok:
                    return False, "CERTIFICATE FAIL (at the ceiling): " + why
                proved += 1
                if proof.get("subproofs") and subbed is None:
                    subbed = (fam, N, proof)
                if proved >= 2:
                    break
            x += u
        if proved < 2:
            return False, f"CERTIFICATE FAIL: no prime values near the ceiling for {fam}"
        parts.append(f"{fam}: {proved} values p + {SHIFT(fam)}({nm}) of "
                     f"{len(str(x + c))} digits proved at the value ceiling")
    if subbed is None:
        # a structureless prime past the bound with a factor past it too
        from sympy import nextprime
        for sd in range(50):
            N = int(nextprime(ceiling.K_CEIL - 10 ** 18 - sd * 10 ** 12))
            proof = certify_value(N)
            if proof is not None and proof.get("subproofs"):
                subbed = ("a 40-digit prime", N, proof)
                break
    if subbed is None:
        return False, "CERTIFICATE FAIL: no ceiling certificate exercised the recursion"
    _lab, N, proof = subbed
    if certificate.verify({a_: b_ for a_, b_ in proof.items()
                           if a_ != "subproofs"})[0]:
        return False, "CERTIFICATE FAIL: a proof stripped of its subproof verified"
    parts.append(f"the recursion exercised ({len(proof['subproofs'])} "
                 f"subproof(s), which cannot be stripped); {time.time() - t0:.1f} s in all")
    return True, "certificates ok: " + "; ".join(parts)


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly, across the seams
    a real interrupt leaves: a period boundary, the (j, u) sub-period
    cursor, and the clipped first period -- on every family."""
    total = 0
    for lab, fam, n, kw, j_at, span, cut in (
            ("one-level", "A257467", 13, dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 1200, 457),
            ("two-level", "A257466", 15, dict(p1=19, p2=31, p3=None, q2=8192,
                                              unit=6, pb=32),
             10 ** 19, 3, 1),
            ("three-level", "A258035", 10, dict(p1=13, p2=17, p3=19, q2=1024, pb=32),
             9 * 10 ** 14, 600, 211)):
        eng = gpu.GpuEngine(n, fam, **kw)
        j0 = eng.j_of(j_at)
        whole = eng.survivors_j(j0, j0 + span)
        split = (eng.survivors_j(j0, j0 + cut)
                 + eng.survivors_j(j0 + cut, j0 + span))
        if not whole:
            return False, f"RESUME FAIL: {lab} window is empty -- vacuous"
        if sorted(whole) != sorted(split):
            return False, (f"RESUME FAIL: {lab}: {len(whole)} whole vs "
                           f"{len(split)} split")
        total += len(whole)
    # THE (j, u) SEAM, in p space and in class space, deep in the line and in
    # the segment that starts at the clipped first period (the bottom of the
    # line, where every campaign here opens)
    for eng in (gpu.GpuEngine(15, "A257466", p1=11, p2=17, p3=23, q2=1024,
                              nu=4, pb=32),
                gpu.GpuEngine(14, "A257467", p1=11, p2=19, p3=29, q2=1024,
                              nu=8, unit=6, pb=32)):
        nl = eng.launches_per_segment
        if nl < 4:
            return False, "RESUME FAIL: the seam engine has no sub-segment cursor"
        seg = eng.seg_periods
        for jf, k_min in ((lambda e: e.j_of(9 * 10 ** 14), None),
                          (lambda e: 0, 10 ** 6)):
            j0 = jf(eng)
            whole = sorted(eng.survivors_j(j0, j0 + seg, k_min=k_min))
            if not whole:
                return False, (f"RESUME FAIL: the (j, u) seam window is empty "
                               f"({eng.fam}, period {j0})")
            for cut in (1, 3, nl - 1):
                part, stopped = [], 0
                for _, un, sv in eng.sweep(j0, j0 + seg, k_min=k_min):
                    part.extend(sv)
                    stopped = un
                    if un == 0 or un >= cut:
                        break
                if stopped:
                    for _, _, sv in eng.sweep(j0, j0 + seg, u_from=stopped,
                                              k_min=k_min):
                        part.extend(sv)
                if sorted(part) != whole:
                    return False, (f"RESUME FAIL: the (j, u) seam at u = "
                                   f"{stopped} ({eng.fam}, period {j0}) "
                                   f"loses or repeats values: {len(part)} vs "
                                   f"{len(whole)}")
            total += len(whole)
    return True, (f"resume ok: split sweep == unsplit sweep on one-, two- and "
                  f"three-level wheels across every family, across the (j, u) "
                  f"sub-segment seam in p space (A257466) and in class space "
                  f"(A257467), and inside the clipped first segment at the "
                  f"bottom of the line on both ({total} survivors across the "
                  f"seams)")


def _classification_drill():
    """The two-pass screen == the all-bases chain on real survivors, the
    pool's chunked answer == the serial one, the cap is honoured and a run
    at the cap is re-read exactly."""
    fam, n = "A257466", 12
    eng = gpu.GpuEngine(n, fam, p1=13, p2=23, p3=None, q2=2048)
    j0 = eng.j_of(10 ** 13)
    surv = eng.survivors_j(j0, j0 + 160)
    if len(surv) < 3 * CHUNK:
        return False, f"CLASSIFY FAIL: only {len(surv)} survivors"
    forms = filter_forms(fam, n)
    two = [sprp_run(k, forms, n + RUN_AHEAD) for k in surv]
    ceng = cpu.CpuEngine(n, fam, q2=64)
    full = [ceng.run_length(k, cap=n + RUN_AHEAD) for k in surv]
    if two != full:
        i = next(i for i in range(len(surv)) if two[i] != full[i])
        return False, (f"CLASSIFY FAIL: two-pass sprp gave run {two[i]} and "
                       f"the all-bases chain {full[i]} at p = {surv[i]}")
    with _pool_factory(2) as pool:
        parts = _submit(pool, forms, n + RUN_AHEAD, surv)
        got = [r for ks, f in parts for r in f.result()]
    if got != full:
        return False, "CLASSIFY FAIL: the pool's chunked result differs"
    # every frontier term through the pool's own form list: exactly its
    # index with room to run on, capped under a smaller cap, and a
    # composite p reads 0 whatever its shifts do
    for f in ref.FAMILIES:
        top = max(ref.KNOWN[f])
        x = ref.KNOWN[f][top]
        fs = filter_forms(f, top)
        if len(fs) != top + RUN_AHEAD or sprp_run(x, fs, top + RUN_AHEAD) != top \
                or sprp_run(x, fs, 9) != 9 or sprp_run(25, fs, top, floor=1) != 0 \
                or sprp_run(x * 7, fs, top, floor=1) != 0:
            return False, f"CLASSIFY FAIL: {f} a({top}) through the pool's forms"
    # A RUN AT THE CAP IS RE-READ: A257466's a(13) read under a cap of 12
    # says 12, and the exact re-read says 13
    x13 = ref.KNOWN["A257466"][13]
    if sprp_run(x13, filter_forms("A257466", 4, cap=12), 12) != 12 or \
            cpu.run_length_fast("A257466", x13, cap=RUN_EXACT_CAP) != 13:
        return False, "CLASSIFY FAIL: the capped read and the exact re-read of A257466's a(13)"
    return True, (f"classification ok: two-pass sprp == all-bases chain on "
                  f"{len(surv)} real survivors (max run {max(full)}), "
                  f"{len(parts)} pool chunks reassemble to the serial answer, "
                  f"every frontier term reads exactly its own index with "
                  f"{RUN_AHEAD} shifts of room and capped under a smaller "
                  f"cap, a composite p reads 0, and a run at the cap "
                  f"(A257466's a(13) under a cap of 12) is re-read to 13")


def _stop_on_discovery_drill():
    def stops(camp, flag=True):
        return bool(flag and camp.discoveries > camp._discoveries_at_start)

    class _C:
        def __init__(self, prior):
            self.discoveries = prior
            self._discoveries_at_start = prior
    for prior in (0, 1, 2, 7):
        c = _C(prior)
        if stops(c):
            return False, f"STOP DRILL FAIL: resumed with {prior} finds, stops at once"
        c.discoveries += 1
        if not stops(c):
            return False, f"STOP DRILL FAIL: {prior} prior finds, no stop on a new one"
    return True, ("stop-on-discovery ok: a resumed campaign with 0, 1, 2 or "
                  "7 finds already in the checkpoint does NOT stop before "
                  "finding something, and DOES stop on the next new find")


def _args_for(fam, **over):
    class _A:
        pass
    a = _A()
    d = dict(family=fam, fresh=False, to=None, stop_on_discovery=False,
             heartbeat=30.0, gpu_yield_ms=0.0, status=False, selftest=False,
             workers=1, worker_ramp=WORKER_RAMP_S, start_n=None, stop_n=None)
    d.update(over)
    for k, v in d.items():
        setattr(a, k, v)
    return a


# The index the drill campaigns OPEN at, per family: a(DRILL_N) and
# a(DRILL_N + 1) are published and a second of device from the bottom of the
# line, and the run is BOUNDED before the filter of DRILL_N + 2 (`stop_n`),
# with every run from there up ignored, so no drill ever sweeps or settles
# an open index (CLAUDE.md 0a).  A257466 from 12: a(13) = 360,772,331 comes
# FIRST (an early find; the filter stays at 12), then a(12) = 494,272,241
# and the frontier jumps 11 -> 13.  A257467 from 9: a(10) = 68,967,673
# early, then a(9) = 142,516,687.  A258035 from 9: a(9) then a(10), in
# order, one promotion each (its listed a(11) and a(12) are errata and are
# not used).
DRILL_N = {"A257466": 12, "A257467": 9, "A258035": 9}


def _promotion_drill():
    """A FIND MOVES THE FILTER ONLY WHEN IT IS THE FILTER'S OWN: an early
    find (a run above the filter) leaves the filter and the frontier where
    they are; the find of a(n) then moves the frontier past every index
    settled early, the classified line is CARRIED and the sweep resumes at
    the old boundary, floored into the new period with the clip at the
    boundary.  On scratch files, with the REAL published terms as finds."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="runs-promote-")
    path = str(pathlib.Path(tmp) / "c.json")
    rows = []
    for fam in ref.FAMILIES:
        n0 = DRILL_N[fam]
        found_x = ref.KNOWN[fam][n0]
        early_x = ref.KNOWN[fam][n0 + 1]
        pol = _POLICIES[fam].at(path)
        c = Campaign(_args_for(fam, start_n=n0), ckpt=path, cursor=pol)
        before = (c.eng.n, c.eng.unit, c.eng.W, c.eng.q2,
                  (c.eng.p1, c.eng.p2, c.eng.p3), c.eng.nforms, c.eng.r0)
        if c.filter_n() != n0 or c.j != c.floor_period() or \
                c.x_start() != 2 or c.j != 0:
            return False, f"PROMOTION FAIL: {fam} drill campaign did not open at index {n0} from the bottom"
        if event_kind(n0 + 1, c.settled()) != "DISCOVERY" or \
                event_kind(n0, c.settled()) != "DISCOVERY" or \
                event_kind(n0 - 1, c.settled()) != "NEAR":
            return False, f"PROMOTION FAIL: {fam}: the drill's settled set is {sorted(c.settled())}"
        # AN EARLY FIND: a(n0 + 1) lands while a(n0) is open
        c.found[str(n0 + 1)] = int(early_x)     # what record_discovery does
        if c.frontier() != n0 - 1 or c.filter_n() != n0 or c.early() != (n0 + 1,):
            return False, f"PROMOTION FAIL: {fam}: an early find moved the filter"
        if event_kind(n0 + 1, c.settled()) != "NEAR" or \
                c.open_indices() != [n0, n0 + 2, n0 + 3]:
            return False, (f"PROMOTION FAIL: {fam}: after the early find the open "
                           f"indices are {c.open_indices()}")
        nxt = c.next_rung(c.swept_k())
        if not nxt or not nxt[0].startswith(f"a({n0})"):
            return False, f"PROMOTION FAIL: {fam}: after an early find the ladder aims at {nxt}"
        c.state()
        c.status_line()
        if not c.save_boundary():
            return False, f"PROMOTION FAIL: {fam}'s in-window save did not land"
        try:
            w = Campaign(_args_for(fam, start_n=n0), ckpt=path,
                         cursor=_POLICIES[fam].at(path))
        except ValueError as e:
            return False, f"PROMOTION FAIL: {fam}: the in-window checkpoint refused: {e}"
        if w.filter_n() != n0 or w.found or w.j != c.j:
            return False, f"PROMOTION FAIL: {fam}: the in-window checkpoint reopened wrong"
        # THE FILTER'S OWN FIND: the frontier passes the early index too
        c.found[str(n0)] = int(found_x)
        if c.frontier() != n0 + 1 or c.filter_n() != n0 + 2 or c.early():
            return False, f"PROMOTION FAIL: {fam}: the frontier is {c.frontier()} after a({n0})"
        # the old filter swept five segments past the finds' own segment
        c.boundary = max(found_x, early_x) // c.eng.W + 5 * c.eng.seg_periods
        swept_old = c.boundary * c.eng.W
        c.follow_frontier(swept_old)
        if c.eng.n != n0 + 2 or c.eng.nforms != before[5] + 2:
            return False, f"PROMOTION FAIL: {fam} did not move to n = {n0 + 2}"
        cpu.assert_unit(n0 + 2, fam, c.eng.unit)
        if c.eng.r0 != cpu.unit_residue(n0 + 2, fam, c.eng.unit):
            return False, f"PROMOTION FAIL: {fam}'s class did not follow the filter"
        if c.cover_x != swept_old or c.x_start() != swept_old:
            return False, (f"PROMOTION FAIL: {fam} did not carry the line to "
                           f"{swept_old} (cover {c.cover_x}, start {c.x_start()})")
        if c.k_min() != swept_old or c.j != swept_old // c.eng.W:
            return False, (f"PROMOTION FAIL: {fam} resumed at period {c.j}, "
                           f"clip {c.k_min()}; expected the period holding "
                           f"{swept_old} with the clip there")
        if c.zone() is not None or c.zone_n != n0 + 2:
            return False, f"PROMOTION FAIL: {fam}: a carried line has a zone {c.zone()}"
        if c.u != 0 or c.boundary != c.j or c.pending:
            return False, f"PROMOTION FAIL: {fam}'s cursor after the promotion"
        if any(p_.startswith((f"a({n0})", f"a({n0 + 1})")) for p_ in c.passed):
            return False, f"PROMOTION FAIL: {fam} kept a retired rung"
        if not c.save():
            return False, f"PROMOTION FAIL: {fam}'s post-promotion save did not land"
        c2 = Campaign(_args_for(fam, start_n=n0), ckpt=path,
                      cursor=_POLICIES[fam].at(path))
        if (c2.filter_n(), c2.j, c2.u, c2.cover_x, c2.zone_n) != \
                (n0 + 2, c.j, 0, c.cover_x, c.zone_n):
            return False, f"PROMOTION FAIL: {fam} reloaded differently"
        import json as _json
        with open(path) as fh:
            st = _json.load(fh)
        st["n"] = n0
        checkpoint.save(path, st)
        try:
            Campaign(_args_for(fam, start_n=n0), ckpt=path,
                     cursor=_POLICIES[fam].at(path))
            return False, f"PROMOTION FAIL: {fam} read a cursor stored at the wrong index"
        except ValueError:
            pass
        for ext in ("", ".bak"):
            if os.path.exists(path + ext):
                os.remove(path + ext)
        rows.append(f"{fam} n = {n0} -> {n0 + 2} (a({n0 + 1}) found early): "
                    f"wheel {before[4]} -> ({c.eng.p1},{c.eng.p2},{c.eng.p3}), "
                    f"period {before[2]:.3g} -> {c.eng.W:.3g}, carried to the "
                    f"old boundary {swept_old:.4g}")
    return True, ("promotion ok: " + "; ".join(rows) + " -- an early find "
                  "leaves the filter and the frontier where they are and "
                  "retires only its own rungs, the filter's own find moves "
                  "the frontier past it, the engine is rebuilt at the next "
                  "open index, an interrupt between a find and the promotion "
                  "writes a checkpoint that still opens, the classified line "
                  "is carried to the old boundary, the cursor round-trips, "
                  "and a cursor stored at the wrong index is REFUSED")


def _other_families_cursor_drill(fam):
    import tempfile
    tmp = tempfile.mkdtemp(prefix="runs-cursor-")
    path = str(pathlib.Path(tmp) / "c.json")
    seen = 0
    try:
        for other in ref.FAMILIES:
            if other == fam:
                continue
            pol = _POLICIES[other].at(path)
            for key in pol.readable():
                checkpoint.save(path, {"key": key, "j": 7, "u": 0, "k": 11})
                st, kind = pol.load()
                if not st or kind is None:
                    return False, f"CURSOR FAIL: {other} will not read {key}"
                pol.refuse_mismatch()
                seen += 1
            checkpoint.save(path, {"key": "not-a-real-key", "j": 7, "k": 11})
            st, _k = pol.load()
            if st:
                return False, f"CURSOR FAIL: {other} read a foreign key"
            try:
                pol.refuse_mismatch()
                return False, f"CURSOR FAIL: {other} did not refuse a foreign key"
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
    return True, (f"cursor policies of the other {len(ref.FAMILIES) - 1} "
                  f"families ok: all {seen} declared keys pass BOTH readers; "
                  f"an unknown key refuses")


def _families_stay_apart():
    """No two campaigns may read each other's cursor; the plan is admissible
    at every opening and the three filters above it, in the forced class,
    with an expected sweep near the unavoidable one; and the benchmark
    shape at each opening names the campaign's own plan (rule 5g)."""
    fams = list(ref.FAMILIES)
    if len({config_key(f) for f in fams}) != len(fams) or \
            len({ckpt_path(f) for f in fams}) != len(fams) or \
            len({ledger_path(f) for f in fams}) != len(fams):
        return False, "FAMILY FAIL: two families share a key, checkpoint or ledger"
    for f in fams:
        for other in fams:
            if other != f and config_key(other) in _POLICIES[f].readable():
                return False, f"FAMILY FAIL: the {f} policy accepts the {other} key"
    classes, tight = {}, []
    for f in fams:
        for n in range(open_n(f), open_n(f) + gpu.OPENINGS_AHEAD):
            unit, p1, p2, p3, q2, pb = plan_for(f, n)
            cpu.assert_unit(n, f, unit)
            if unit != 6:
                return False, f"FAMILY FAIL: {f} n = {n}: the forced unit is {unit}, not 6"
            W = unit
            for q in gpu._wheel_primes(p1, p2, p3):
                W *= q
            _wide, pv = gpu._record_for(W // unit, q2, pb)
            floor_k = x_floor(f, n)
            ideal = model.expected_sweep(f, n, floor_k, floor_k, 1.0)
            swept = model.expected_sweep(f, n, floor_k, (floor_k // W) * W, pv * W)
            if swept > PLAN_WASTE_MAX * ideal:
                return False, (f"FAMILY FAIL: {f} n = {n} plans a segment of "
                               f"{pv} periods x {W:.4g}, whose expected sweep "
                               f"to a confirmed find is {swept / ideal:.2f}x "
                               f"the unavoidable one")
            tight.append((ideal / swept, f, n))
        classes[f] = "%d (mod %d)" % cpu.forced_class(open_n(f), f)
    import score as _score
    lv = lambda z: tuple(z or ())               # noqa: E731
    seen = set()
    for row in _score.SHAPES:
        (label, f, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, _nu, pb) = row
        if unit == 1 or n != open_n(f):
            continue
        seen.add(f)
        want = plan_for(f, n)
        got = (unit, lv(p1), lv(p2), lv(p3), q2, pb)
        if got != (want[0], lv(want[1]), lv(want[2]), lv(want[3]), want[4], want[5]):
            return False, (f"FAMILY FAIL: benchmark shape {label} names {got} "
                           f"and the campaign plans {want} at {f} n = {n}: "
                           f"re-freeze the shape at the plan (and log it)")
    if seen != set(fams):
        return False, f"FAMILY FAIL: no benchmark shape at the opening of {sorted(set(fams) - seen)}"
    tight.sort()
    return True, ("families stay apart: %d distinct config keys, checkpoint "
                  "files and ledgers, no policy reads another's cursor, the "
                  "plan is admissible at every opening and the three filters "
                  "above it in the forced classes %s, every plan's expected "
                  "sweep to a CONFIRMED find stays near the unavoidable one "
                  "(the worst is %s n = %d at %.2fx, against a %gx bound), "
                  "and the benchmark shape at every opening names exactly "
                  "the configuration the campaign plans there"
                  % (len(fams), ", ".join(f"{f} x == {c}" for f, c in classes.items()),
                     tight[0][1], tight[0][2], 1 / tight[0][0], PLAN_WASTE_MAX))


def _campaign_wiring_drill(fam):
    """Build a campaign and exercise everything the loop touches, without
    sweeping a whole period."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="runs-drill-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[fam].at(path)
    n0 = open_n(fam)
    a = _args_for(fam)
    try:
        c = Campaign(a, ckpt=path, cursor=pol)
        if c.frontier() != n0 - 1 or c.filter_n() != n0:
            return False, f"WIRING FAIL: frontier {c.frontier()}, filter {c.filter_n()}"
        floor = c.x_start()
        want_floor = 2
        if floor != want_floor or (c.j, c.u) != (0, 0) or c.floor_period() != 0:
            return False, (f"WIRING FAIL: a fresh campaign starts at {floor} "
                           f"(j, u) = ({c.j}, {c.u}); expected the bottom of "
                           f"the line, {want_floor}")
        if c.settled() != set(range(0, n0)) or c.open_indices() != [n0, n0 + 1, n0 + 2]:
            return False, (f"WIRING FAIL: a fresh campaign has settled "
                           f"{sorted(c.settled())} and aims at {c.open_indices()}")
        if c.k_min() != max(floor, cpu.k_floor(c.eng.q2, n0, fam) + 1):
            return False, f"WIRING FAIL: the clip is {c.k_min()}"
        unit, p1, p2, p3, q2, pb = plan_for(fam, n0)
        if (c.eng.n, c.eng.fam, c.eng.unit, c.eng.q2, c.eng.pv) != (n0, fam, unit, q2, pb) \
                or (c.eng.p1, c.eng.p2, c.eng.p3) != (p1, p2, p3):
            return False, "WIRING FAIL: the engine is not the PLANNED one"
        line = c.status_line()
        for want in ("swept to", fam, "census", f"periods [{c.floor_period()},"):
            if want not in line:
                return False, f"WIRING FAIL: status line lacks {want!r}"
        if c.handle(floor + 1, 9) is not False or c.census.get(9) != 1:
            return False, "WIRING FAIL: a census run was not counted"
        if c.handle(floor + 3, 7) is not False or 7 in c.census:
            return False, "WIRING FAIL: a run under the floor was counted"
        # THE ZONE: every line starts at the bottom, so it is real at the
        # opening; the drill covers it (the small published terms in it are
        # counted, none is a find) and a second call is a no-op
        z = c.zone()
        if z is None or z != (floor, cpu.k_floor(c.eng.q2, n0, fam)):
            return False, f"WIRING FAIL: {fam}'s zone is {z}"
        if c.cover_zone() or c.zone_n != n0 or c.cover_zone() or c.discoveries:
            return False, "WIRING FAIL: the zone cover is not once per filter"
        surv0 = c.survivors
        jf = c.floor_period()
        inflight = collections.deque()
        inflight.append(((jf, 52), [([5, 6, 7], _Done([3, 8, 12]))]))
        inflight.append(((jf, 104), [([9], _Done([0]))]))
        c._drain(inflight, block=True)
        if c.pending != [(6, 8), (7, 12)] or (c.j, c.u) != (jf, 104):
            return False, f"WIRING FAIL: the drain left {c.pending}, ({c.j}, {c.u})"
        nxt = c.next_rung(c.swept_k())
        if not nxt or not nxt[0].startswith(f"a({n0})"):
            return False, f"WIRING FAIL: the ladder aims at {nxt}"
        c.check_rungs(c.swept_k())
        builds = c._lad.builds
        for _ in range(25):
            c.ladder()
            c.next_rung(c.swept_k())
            c.check_rungs(c.swept_k())
        if c._lad.builds != builds:
            return False, "WIRING FAIL: ladder reads at a standing frontier rebuilt"
        c.args.workers = None
        c.u = 0
        before = (c.j, c.u, c.survivors, list(c.pending), dict(c.census))
        m = c.calibrate()
        if (m["launches"] < 1 or m["survivors"] < 1 or m["rate"] <= 0
                or not 1e-6 < m["cost"] < 1e-3 or m["need"] <= 0):
            return False, f"WIRING FAIL: the sizing measurement is {m}"
        if (c.j, c.u, c.survivors, list(c.pending), dict(c.census)) != before:
            return False, "WIRING FAIL: the calibration moved the campaign"
        w = c.size_pool()
        ms = c._sizing
        if (ms is None or w != max(1, math.ceil(ms["need"] * POOL_MARGIN))
                or c.workers != w or c.pool is None
                or not 1 / 3 < ms["need"] / max(m["need"], 1e-9) < 3):
            return False, f"WIRING FAIL: size_pool gave {w} workers from {ms}"
        pool_obj = c.pool
        w2 = c.size_pool()
        if not (c.pool is pool_obj or w2 > w or 2 * w2 <= w):
            return False, "WIRING FAIL: re-sizing rebuilt the pool inside the noise band"
        w = c.workers

        class _Slow:
            def __init__(self, v):
                self._v, self._d = v, False

            def done(self):
                return self._d

            def result(self):
                self._d = True
                return self._v
        inflight = collections.deque()
        for i in range(BACKLOG_LAUNCHES + 5):
            inflight.append(((jf, 200 + i), [([11 + i], _Slow([3]))]))
        c._drain(inflight, block=False)
        if len(inflight) != BACKLOG_LAUNCHES + 5:
            return False, "WIRING FAIL: the drain took launches not yet classified"
        c._backpressure(inflight)
        if (len(inflight) != BACKLOG_LAUNCHES or c._hostwait <= 0
                or not c._hostbound_logged or c.survivors != surv0 + 9
                or (c.j, c.u) != (jf, 204)):
            return False, f"WIRING FAIL: back-pressure left {len(inflight)} in flight"
        c._hostwait, c._hostbound_logged = 0.0, False
        line = c.status_line()
        if f"pool {w}" not in line or "HOST-BOUND" in line:
            return False, f"WIRING FAIL: status line pool fragment: {line}"
        if (f"P(a({n0}) under the claim) = 0%" not in line
                or f"next a({n0})" not in line):
            return False, f"WIRING FAIL: the status line reads the rungs off progress: {line}"
        c.pool.shutdown(wait=True, cancel_futures=True)
        c.pool, c.workers, c.args.workers = None, None, 1
        c.found[str(n0 + 2)] = int(floor + 6)
        early_aim = c.next_rung(c.swept_k())
        if c.frontier() != n0 - 1 or c.filter_n() != n0 or \
                c._lad.builds != builds + 1 or not early_aim or \
                not early_aim[0].startswith(f"a({n0})") or \
                c.open_indices() != [n0, n0 + 1, n0 + 3]:
            return False, ("WIRING FAIL: an early find moved the filter, or "
                           "did not rebuild the ladder without its rungs")
        c.found.pop(str(n0 + 2))
        c._lad.invalidate()
        c.ladder()
        builds = c._lad.builds
        c.found[str(n0)] = int(floor + 4)
        if c.frontier() != n0 or c.filter_n() != n0 + 1:
            return False, "WIRING FAIL: a find did not move the frontier"
        aim = c.next_rung(c.swept_k())
        if c._lad.builds != builds + 1:
            return False, "WIRING FAIL: the frontier moved and the ladder was served from cache"
        if not aim or not aim[0].startswith((f"a({n0 + 1})", "engine ceiling")):
            return False, f"WIRING FAIL: after finding a({n0}) the campaign aims at {aim}"
        c.found.pop(str(n0))
        if c.frontier() != n0 - 1 or c.filter_n() != n0:
            return False, "WIRING FAIL: the frontier did not come back"
        c._lad.invalidate()
        c.mark_boundary()
        c._ckpt_t = time.time()
        if c.save_due():
            return False, "WIRING FAIL: a save was due right after a save"
        c._ckpt_t = 0.0
        if not c.save_due():
            return False, "WIRING FAIL: a save was not due after the interval"
        c.save()
        d = Campaign(a, ckpt=path, cursor=pol)
        if (d.j, d.u, d.pending, d.census, d.survivors, d.zone_n) != (
                c.j, c.u, c.pending, c.census, c.survivors, c.zone_n):
            return False, "WIRING FAIL: reload gave a different state"
        msg = c._on_interrupt()
        if "checkpoint written at the last classified launch" not in msg:
            return False, f"WIRING FAIL: the interrupt path said {msg!r}"
        st, kind = pol.load()
        if kind != "own" or int(st["u"]) != c.u:
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
    return True, (f"campaign wiring ok ({fam}): a campaign builds from nothing "
                  f"at the bottom of the line ({TERM(fam)} = {floor:,}) with "
                  f"the PLANNED engine at n = {n0}, unit {unit}, wheel "
                  f"({p1},{p2},{p3}) and depth {q2}; its exception zone is "
                  f"covered once; its status line and rung ladder aim at "
                  f"a({n0}), 75 ladder reads at a standing frontier cost 0 "
                  f"model rebuilds while a find -- early or the filter's own "
                  f"-- costs exactly 1, the pool is "
                  f"sized from a live measurement, back-pressure times the "
                  f"wait, the drain keeps the work cursor behind the "
                  f"classified launches, and the checkpoint round trips "
                  f"through both the normal save and the interrupt snapshot")


def _rediscovery_run_drill(fam):
    """THE REAL LOOP, END TO END, ON PUBLISHED GROUND: `Campaign.run`
    itself, on scratch files, opened at DRILL_N from the bottom of the line
    and bounded before DRILL_N + 2: it finds a(n0) and a(n0 + 1), both
    published -- on A257466 and A257467 the LATER index first, as an early
    find -- moves its filter when a(n0) lands, and stops."""
    import json as _json
    import tempfile
    tmp = tempfile.mkdtemp(prefix="runs-rerun-")
    path = str(pathlib.Path(tmp) / "c.json")
    evid = str(pathlib.Path(tmp) / "evidence")
    n0 = DRILL_N[fam]
    want = {str(n): ref.KNOWN[fam][n] for n in (n0, n0 + 1)}
    if n0 + 2 > open_n(fam):
        return False, f"RERUN FAIL: {fam}'s drill would reach the open index"
    early = want[str(n0 + 1)] < want[str(n0)]
    args = _args_for(fam, start_n=n0, stop_n=n0 + 2,
                     to=max(want.values()) + 10 ** 7, heartbeat=3600.0)
    c = Campaign(args, ckpt=path, cursor=_POLICIES[fam].at(path), evid=evid)
    rc = c.run()
    found = {k: int(v) for k, v in c.found.items()}
    if rc != 0 or found != want:
        return False, f"RERUN FAIL: {fam} from index {n0} found {c.found}, published {want}"
    if c.discoveries != 2 or c.filter_n() != n0 + 2:
        return False, f"RERUN FAIL: {c.discoveries} discoveries, filter {c.filter_n()}"
    for n in (n0, n0 + 1):
        x = want[str(n)]
        f = pathlib.Path(evid) / evidence_name(fam, n, x)
        if not f.exists():
            return False, f"RERUN FAIL: no evidence file for a({n})"
        with open(f) as fh:
            ev = _json.load(fh)
        ok, msg = evidence.check_names(ev, TERM(fam))
        if not ok:
            return False, f"RERUN FAIL: a({n})'s evidence: {msg}"
        if ev["oeis_terms"] != {str(n): x} or ev["settles"] != [n] or ev["run"] != n:
            return False, f"RERUN FAIL: a({n})'s evidence files it under {ev['oeis_terms']}"
        # an early find is evidenced under the filter that was running
        if ev["filter_n"] != (n0 if (early or n == n0) else n0 + 1):
            return False, f"RERUN FAIL: a({n})'s evidence names filter {ev['filter_n']}"
        st = ev["stopper"]
        if st["n"] != n + 1 or st["value"] != x + ref.shift_k(fam, n + 1) or \
                not (st["factor"] and st["value"] % st["factor"] == 0
                     or st.get("sprp_base") == 2):
            return False, f"RERUN FAIL: a({n})'s stopper is {st}"
        if ev["unproved"] or len(ev["values"]) != ref.nforms(fam, n) \
                or any(int(v) != x + c for v, c in zip(ev["values"].values(), ref.constants(fam, n))) \
                or ev["least_claim"]["swept_from"] > x \
                or ev["least_claim"]["campaign_started_at"] != 2:
            return False, f"RERUN FAIL: a({n})'s evidence is not self-contained"
    ok, msg = evidence.gate_names(evid, TERM(fam))
    if not ok:
        return False, "RERUN FAIL: " + msg
    order = (f"a({n0 + 1}) = {want[str(n0 + 1)]:,} FIRST, as an early find "
             f"(the filter stayed at {n0}), then a({n0}) = {want[str(n0)]:,}, "
             f"and moved its filter past both"
             if early else
             f"a({n0}) = {want[str(n0)]:,}, promoted itself carrying the "
             f"line, and found a({n0 + 1}) = {want[str(n0 + 1)]:,}")
    return True, (f"rediscovery run ok: Campaign.run, opened at index {n0} of "
                  f"{fam} from the bottom of the line on scratch files, found "
                  f"{order}, then stopped before the filter of a({n0 + 2}); "
                  f"each evidence file is named and keyed by the OEIS index, "
                  f"carries its exact run and its stopper's witness, and "
                  f"passes the naming gate ({c.survivors:,} survivors "
                  f"classified, census {dict(sorted(c.census.items()))})")


def _zone_drill():
    """The exception zone holds terms, and the host finds them: the primes
    up to the sieve depth are classified one at a time, and at depth 4096
    A257466's zone holds a(1) = 17, a(2) = 11, a(3) = 5, a(5) = 101,
    a(9) = 191 and a(10) = 59, each the first of its exact run there.  (2
    and 3 are outside the forced class the walk steps through; their runs
    are published and under the census floor.)"""
    fam, n0, q2 = "A257466", 5, 4096
    hits = [h for h in cpu.prefix_hits(fam, n0, q2, floor=1) if h[0] > 3]
    oh = [h for h in ref.prefix_hits(fam, n0, 2, cpu.k_floor(q2, n0, fam),
                                     floor=1) if h[0] > 3]
    if not hits or hits != oh:
        return False, (f"ZONE FAIL: the engine's zone walk ({len(hits)} primes "
                       f"with a run) differs from the oracle's ({len(oh)})")
    first = {}
    for x, r in hits:
        first.setdefault(r, x)
    want = {n: x for n, x in ref.KNOWN[fam].items() if 3 < x <= q2}
    if len(want) < 6 or any(first.get(n) != x for n, x in want.items()):
        return False, f"ZONE FAIL: the zone's first occurrences are {first}, published {want}"
    for small in (2, 3):
        if cpu.run_length_fast(fam, small, cap=RUN_EXACT_CAP) >= CENSUS_FLOOR:
            return False, f"ZONE FAIL: {small} has a run at the census floor"
    return True, (f"zone ok: the {len(hits)} primes of A257466's exception "
                  f"zone (5 to {q2}) with a run, walked on the host, agree "
                  f"with the oracle's walk run for run, and the first of each "
                  f"exact run is the published term: " +
                  ", ".join(f"a({n}) = {x}" for n, x in sorted(want.items())))


def _evidence_names_drill():
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        ev = dict(evidence.header(fam, ref.FAMILIES[fam]["forms"], TERM(fam),
                                  ref.KNOWN[fam][top], [top]), settles=[top])
        ok, msg = evidence.check_names(ev, TERM(fam))
        if not ok:
            return False, f"EVIDENCE NAMES FAIL: {fam} writer: {msg}"
    return evidence.gate_names(EVID, lambda rec: TERM(rec["sequence"]))


def selftest(fam="A257466"):
    t0 = time.time()
    rows = []
    for g in (ref.GATES + cpu.GATES + gpu.GATES + model.GATES
              + certificate.GATES + ceiling.GATES):
        rows.append(g())
    rows.append(drills.event_kind_drill(
        lambda c: event_kind(*c), _event_cases()))
    for d in drills.standard(pool_factory=_pool_factory,
                             cursor=_POLICIES[fam]):
        rows.append(d)
    rows.append(_other_families_cursor_drill(fam))
    for d in (_ceiling_drill, _zone_drill, _canary_hunt, _protocol_drill,
              _certificate_drill, _resume_drill, _promotion_drill,
              _classification_drill, _stop_on_discovery_drill,
              _families_stay_apart):
        rows.append(d())
    for f in ref.FAMILIES:
        rows.append(_campaign_wiring_drill(f))
        rows.append(_rediscovery_run_drill(f))
    rows.append(_evidence_names_drill())
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

def _status(fam):
    st, kind = _POLICIES[fam].load(warn=lambda m: log("STAGE", m))
    if not st:
        log("STATUS", f"no checkpoint for {config_key(fam)} yet")
        return 0
    cen = {int(r): int(c) for r, c in st.get("census", {}).items()}
    found = {int(n) for n in st.get("found", {})}
    front = max(ref.KNOWN[fam])
    while front + 1 in found:
        front += 1
    log("STATUS", "  ".join([
        f"{fam}",
        f"swept to {TERM(fam)} = {int(st['k']):,}",
        f"work cursor period {int(st['j'])} u = {int(st.get('u', 0))}",
        f"filter n = {front + 1}",
        census_str(cen, CENSUS_FLOOR, max(found | {front})),
        f"finds {st.get('discoveries', 0)}",
        f"near {st.get('near', 0)}",
        f"survivors {int(st.get('survivors', 0)):,}",
        f"elapsed {float(st.get('elapsed', 0)) / 3600:.2f} h",
        f"saved {st.get('saved', '?')}"]))
    for n, k in sorted(st.get("found", {}).items(), key=lambda x: int(x[0])):
        log("STATUS", f"  found: a({n}) = {TERM(fam)} = {int(k):,}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--family", default="A257466",
                    help="which sequence to hunt: " +
                         ", ".join(ref.FAMILIES) + " (default A257466)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this depth on the term's line (default: "
                         "the engine ceiling, 1e40)")
    ap.add_argument("--stop-on-discovery", action="store_true",
                    help="checkpoint and exit once THIS RUN confirms a find")
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (default 30)")
    ap.add_argument("--workers", type=int, default=None,
                    help="classification pool size. By default it is "
                         "MEASURED at the campaign's own filter and "
                         "re-measured at every promotion: ceil(core-seconds "
                         "per second x 2). 1 classifies in the main thread "
                         "(a throttle, not a speed)")
    ap.add_argument("--worker-ramp", type=float, default=WORKER_RAMP_S,
                    help=f"seconds between worker starts (default {WORKER_RAMP_S})")
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0,
                    help="idle the device this long after every launch "
                         "(1 ms against a ~20 ms launch costs about 5%% of "
                         "the rate)")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 2 --workers 1 --worker-ramp 1.0")
    ap.add_argument("--fresh", action="store_true",
                    help="discard an existing cursor deliberately")
    args = ap.parse_args(argv)
    args.family = ref.family(args.family)
    if args.gentle:
        args.gpu_yield_ms = args.gpu_yield_ms or 2.0
        args.workers = 1
        args.worker_ramp = max(args.worker_ramp, 1.0)
    if args.selftest:
        return selftest(args.family)
    if args.status:
        return _status(args.family)
    if args.to:
        args.to = int(args.to)
    _POLICIES[args.family].refuse_mismatch(
        fresh=args.fresh,
        describe=lambda st: (f"period {st.get('j')}, u = {st.get('u')}, "
                             f"swept to {TERM(args.family)} = {st.get('k')}"))
    if args.fresh:
        for p in (ckpt_path(args.family), ckpt_path(args.family) + ".bak"):
            if os.path.exists(p):
                os.remove(p)
    return Campaign(args).run()


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
