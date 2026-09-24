"""The campaign for the prime ladders -- least k with prime(i)*k + s prime,
i = 1..n.

    python launch.py --selftest      the full gate battery (must end ALL GREEN)
    python launch.py                 the hunt: indefinite, resumable (A084700)
    python launch.py --sign -1       the A084701 family instead
    python launch.py --to 1e20       stop at a chosen depth on the k line
    python launch.py --status        read the checkpoint and say where it is

TWO FAMILIES, ONE ENGINE, ONE CAMPAIGN AT A TIME.  `--sign +1` is A084700
(the default and the headline: prime(i)*k + 1) and `--sign -1` is A084701
(prime(i)*k - 1).  They are the same mathematics with the killed residues
negated, so they share every file here -- but they are different sequences
with different frontiers, so each carries its OWN checkpoint under its own
config key and a campaign hunts one of them.

WHAT IS OPEN, AND WHY IT IS WORTH A SWEEP.  A084700 has thirteen terms and
its last, a(13) = 161,082,438,032,880, was found by Phil Carmody's GenSv
siever in MARCH 2004 -- twenty-two years ago; A084701 has eleven, and its
a(11) = 3,894,254,360,010 dates from June 2003.  Neither entry carries a
bound of any kind at any open n.  Both frontiers sit inside the FIRST
PERIOD of this engine's wheel.

THE CLAIM'S FLOOR IS FREE.  a() is non-decreasing (the conditions nest), so
the next term is at least the last one and nothing below it has to be swept
at all.  The campaign still starts far below: at K_START = 1e6, inside
period 0, which the engine sweeps whole and clips at K_START (pladder_gpu,
"a window may start inside period zero").  Below K_START the least-claim
rests on monotonicity -- a(13) is 1.6e14 -- and above it on our own
coverage.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine's enforced ceiling -- the PRIMALITY-PROOF validity bound of the
family, k_ceil(n, s) in pladder_search -- which is the last rung.  For
A084700 that is k < 3.317e24, the deterministic Miller-Rabin bound on k
itself: below the PROOF CROSSING k_proof(n, s) (5.4e22 at n = 18) every
classification is a deterministic proof, above it the same Miller-Rabin
chain is a strong probable-prime test and a DISCOVERY is proved by a BLS75
Theorem 1 certificate on N - 1 = prime(i)*k, k factored once per find
(certify_run); the ceiling is where a factor of k could itself pass the
bound and need a subproof.  The first campaign stopped at the crossing on
2026-09-02 with a(18) open, which is why v3 raised it.  A084701's structure
is on N + 1 and huntlib has no N+1 test, so its ceiling is the crossing,
9.0e22 at n = 12 and 4.95e22 at n = 19 -- which its campaign reached on
2026-09-03 after finding a(12) through a(18) in 2.5 hours; a resumed
A084701 campaign has no period left under its ceiling and stops at once,
and its a(19) waits on an N+1 route (a new engine version) or on somebody
else.  `--to` and `--stop-on-discovery` are the only stops and
both are opt-in.  Progress is read off RUNGS taken from the odds model's quantiles,
logged as they are passed and shown with an ETA in every [STATUS].  A rung
retires with its term: the ladder is derived from the LIVE frontier and
cached on it (huntlib.rungs.LiveLadder), never recomputed in the loop.

THE TAXONOMY, mapped to this problem (CONVENTIONS.md "the discovery
protocol").  A survivor is a k with a run length r:

  DISCOVERY  r > frontier: it settles a(frontier+1) ... a(r) at once, each
             logged once, all evidenced under the FIRST value they belong
             to.  Verified three ways plus a factor witness for the
             composite that stops the run, and a re-verified primality
             certificate for every value (deterministic Miller-Rabin
             under the bound, BLS75 Theorem 1 past it).
  NEAR       r == frontier: a k that reaches the settled frontier and no
             further -- ONE condition short of the open term.  One line
             with its campaign ordinal, verified by the cheap legs as an
             engine health check, never evidenced.
  CENSUS     CENSUS_FLOOR <= r < frontier: counted in [STATUS], never
             narrated.
  None       r < CENSUS_FLOOR: noise, not counted.

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
three-level wheel emits a period's candidates in (t, s, u) order, so the k
line is contiguous only at the end of a whole period -- 3.26e19 of k on
the v3 unit wheel, about five seconds of device at n = 18 (two minutes at
n = 14).  COVERAGE (`boundary`, the k below which every value is swept)
advances one period at a time and is the only thing a least-claim rests
on; WORK (`j`, `u`) advances every launch, so a crash costs one checkpoint
interval.  Values classified mid-period are held IN THE CHECKPOINT
(`pending`) and narrated in k order when the period closes, so a discovery
is only announced once it is known to be the least.  A find costs at most
one period of over-sweep.  A v1/v2 cursor (period 6.15e17) is ADOPTED
onto this period by flooring and the overlap re-swept as a cross-check
(`census_floor`); see _POLICIES below.

LOAD (CONVENTIONS.md "Sizing a hunt so it leaves the machine usable").
Measured at the OPENING configuration (n = 14, three-level wheel, sieve
65536), paired and interleaved, on the v1 engine:

    device     1.08e17 k/s, 1.03e11 candidates/s, 10.4 ms per launch
    survivors  4.8e-13 per unit of k line  ->  5.2e4 per second
    host       13.1 us per survivor (two-pass sprp screen)  ->  0.68 core-s/s

and the v3 unit wheel at n = 14 runs 1.8e17 k/s, so the host there needs
about 1.1 core-seconds per second: NOT nothing and NOT a pool's worth
either -- and at A084701's opening filter (n = 12, unit 210) it is 6.3,
because the sieve passes 34x more survivors per unit of line there.  So
the pool is SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER, again
every time the filter moves (Campaign.size_pool: the next launches are
swept and timed, their survivors counted, a sample of them classified,
and ceil(need x POOL_MARGIN) workers ramped one at a time at below-normal
priority, huntlib.pool).  A fixed default of 3, priced at n = 14, was 2x
short at n = 12 on 2026-09-03: the pool saturated, the device ran ahead
into an unbounded backlog, and the heartbeat reported the host's rate as
the hunt's.  Now the device may run at most BACKLOG_LAUNCHES ahead of the
pool, so a pool that binds throttles the device VISIBLY -- the [STATUS]
line says host-bound and by how much -- instead of silently.  At
the LIVE filter (n = 18, 6.1e18 k/s) survivors are 4.5e-16 per unit of
line -- 2.7e3 per second, 0.035 core-seconds per second -- so the
measurement gives one worker there (classifying inline in the main thread
instead would idle the device about 4%).  The alternatives were priced: a sieve
to 2^17 halves the survivors for 7% of the device rate
(OPTIMIZATION_LOG.md), and inline classification in the main thread at
the opening filter would leave the device idle a third of the time.
Classification runs in the pool while the device sweeps, and the WORK
cursor lags behind the launches whose survivors are still being
classified, so a crash never loses a survivor it has not yet looked at.
The throttles are `--workers`, `--gpu-yield-ms` and `--gentle`, priced in
the help text against the launch.  No machine setting is ever changed on
the owner's behalf.
"""

import argparse
import collections
import concurrent.futures as _cf
import math
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from huntlib import certificate, checkpoint, drills, evidence   # noqa: E402
from huntlib import pool as _pool                               # noqa: E402
from huntlib import shutdown                                    # noqa: E402
from huntlib.gpu import device_report                           # noqa: E402
from huntlib.hlog import Heartbeat, banner, census_str, log     # noqa: E402
from huntlib.primes import (MR_VALID_BELOW, factor_witness,     # noqa: E402
                            mr_is_prime, sprp_base2)
from huntlib.rungs import Ladder, LiveLadder, eta_str           # noqa: E402

import pladder_gpu as gpu                                       # noqa: E402
import pladder_model as model                                   # noqa: E402
import pladder_reference as ref                                 # noqa: E402
import pladder_search as cpu                                    # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")

# THE v3 WHEEL, IN UNIT SPACE (OPTIMIZATION_LOG.md v3).  The forcing lemma
# makes every candidate a multiple of 2310 from n = 14 (210 from n = 10),
# so the device sweeps k' = k / unit: 2, 3, 5, 7 (and 11) leave the wheel
# and 29, 31 and 53 come in under the same u32 / 2^63 bounds that stopped
# the k-space wheel at 47.  Levels (..31], (31, 41], (41, 53]: W1 = 8.7e7,
# W2 = 1.6e8, a period of 3.26e19 of k (53 v2 periods), 1.47x fewer
# candidates per unit of line at n = 18 and 1.29x the line rate, paired
# (G17 pins the stream to the v2 wheel's).  The unit is fixed PER FAMILY at
# the filter its campaign opens in and stays: at a higher filter it is
# still admissible (pladder_search.assert_unit), merely not maximal, and a
# fixed unit is what keeps W -- the cursor's denomination -- constant
# across follow_frontier.
UNIT = {+1: 2310, -1: 210}
P1 = 31                           # first-level wheel: primes to 31 not in the unit
P2 = 41                           # second-level wheel: primes (31, 41]
P3 = 53                           # third-level wheel:  primes (41, 53]
Q2 = cpu.Q2_DEFAULT               # sieve depth
# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches.  A launch at n = 18
# is 1.03e9 candidates and about 5.5 ms, so 128 launches is about 0.7 s:
# what an interrupt costs to redo, and the denominator that prices
# --gpu-yield-ms.  A period is 1,277 launches there (38,610 at n = 14,
# where the launches are 6.0e8 candidates), so the WORK cursor lands ten
# times per period and the COVERAGE cursor once.
CKPT_LAUNCHES = 128
K_START = 10 ** 6                 # the clip inside period 0; > k_floor(Q2)
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
# v3 (2026-09-02): the A084700 ceiling raised from the proof crossing to
# the deterministic bound on k itself, with discoveries past the crossing
# proved by certificate (certify_run); and the wheel moved to unit space,
# to 53.  The sieve depth is v2's, so the SURVIVOR SET over any window is
# unchanged (G17), but the period is not, so a v1/v2 cursor is ADOPTED --
# re-denominated, floored -- never accepted.
ENGINE_VERSION = "v3"
# THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER
# (CLAUDE.md 5f and 5g; CONVENTIONS.md "Sizing a hunt"), not from a
# constant: `Campaign.size_pool` sweeps the launches the loop is about to
# run, times them, counts their survivors, times sprp_run on a sample, and
# takes ceil(core-seconds per second x POOL_MARGIN) workers -- at start,
# and again at every filter promotion (the need falls ~5x per condition,
# and a pool that ties on throughput asks for less machine).  The old
# constant, 3, was that measurement taken once at A084700's n = 14 (1.07
# core-s/s); at A084701's n = 12 the need is 6.3 and it was 2x short
# (2026-09-03).  It survives only as the fallback for a drill with no
# device, and `--workers` still overrides.
WORKERS_DEFAULT = 3
POOL_MARGIN = 2.0                 # workers = ceil(core-s per s x this):
#                                   CONVENTIONS.md step 2 says two to three
#                                   times the need; the pool's own overhead
#                                   (pickling, IPC) made 13.1 us/survivor
#                                   into 16.7 in the pool at n = 12
CAL_MIN_SURVIVORS = 500           # the sample the sizing is measured on ...
CAL_MIN_S = 1.0                   # ... over at least this much device time
CAL_MAX_S = 4.0                   # and at most this much
# Two one-second measurements of the same launches differed 1.6x in the
# battery (ambient load; OPTIMIZATION.md's +-30%), so a re-size grows on
# any increase but shrinks only when the need has at least halved --
# which a filter promotion always does (~5x per condition).
CAL_SAMPLE = 2000                 # survivors timed through sprp_run
# BACK-PRESSURE: the device may run at most this many launches ahead of
# the pool.  Past it the loop waits for the oldest launch, so a pool that
# binds throttles the device VISIBLY (the wait is timed into the [STATUS]
# line and the rate printed is the pipeline's) instead of growing a
# backlog in memory -- which at n = 12 grew at 300,000 survivors a second.
BACKLOG_LAUNCHES = 64
# A checkpoint is rewritten every CKPT_LAUNCHES launches, but not so often
# that the writing is a cost: `pending` grows through a period (640k values,
# 25 MB of JSON, at the end of an n = 12 period), so the interval stretches
# to keep each save under CKPT_COST_FRACTION of wall clock.
CKPT_MIN_S = 2.0
CKPT_COST_FRACTION = 0.02
WORKER_RAMP_S = _pool.RAMP_S
CHUNK = 256                       # survivors per pool task


def family_tag(s):
    return "plus" if int(s) > 0 else "minus"


def config_key(s, engine=None):
    return (f"{ref.FAMILIES[int(s)]['oeis'].lower()}-{engine or ENGINE_VERSION}"
            f"-u{UNIT[int(s)]}-p1{P1}-p2{P2}-p3{P3}-q2{Q2}-seg{CKPT_LAUNCHES}")


def old_key(s, engine):
    """The v1/v2 key: the k-space wheel (23],(37],(47], same sieve depth.
    Written out rather than derived from the live constants because it
    describes a wheel this file no longer builds by default."""
    return (f"{ref.FAMILIES[int(s)]['oeis'].lower()}-{engine}"
            f"-p123-p237-p347-q2{Q2}-seg{CKPT_LAUNCHES}")


OLD_W = 614_889_782_588_491_410   # the v1/v2 period, for the adopt drill


def ckpt_path(s):
    return str(HERE / f"campaign_checkpoint_{family_tag(s)}.json")


def ledger_path(s):
    return str(HERE / "evidence" /
               f"{ref.FAMILIES[int(s)]['oeis'].lower()}_discoveries.json")


# EVERY reader of the checkpoint goes through this object and none of them
# takes a key list of its own.  There are three readers -- the campaign's
# load, --status, and the refusal check in main() -- and passing the same
# list to three places is a thing you can forget at one of them; it cost
# this repo two campaign starts before the policy existed (CONVENTIONS.md
# "Reading an existing cursor").  `accept` is for a version gated to
# return the identical stream (same wheel, same sieve); anything that
# moves coverage goes in `adopt`.  v3's unit wheel keeps every SURVIVOR a
# v1/v2 sweep kept (G17) but counts a different PERIOD -- 3.26e19 against
# 6.15e17 -- so a v1/v2 cursor is ADOPTED: only its arithmetic claim
# "every k below this is swept" carries over, re-denominated onto v3's
# period by flooring (an overlap of under one period is re-swept as a
# cross-check; a gap would be a lost frontier), and no index from it is
# reused.  The live A084700 cursor that stopped at the old ceiling resumes
# that way; the adopt drill and the cursor drill in --selftest put every
# reader in front of each key.
_POLICIES = {s: checkpoint.CursorPolicy(ckpt_path(s), config_key(s),
                                        accept=(),
                                        adopt=(old_key(s, "v2"),
                                               old_key(s, "v1")))
             for s in ref.FAMILIES}


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


def verify(k, run, s):
    """The three independent confirmations plus the bounding witness.

    1. huntlib's Miller-Rabin, which is a PROOF below the proof crossing
       k_proof(n, s) (G10) and a thirteen-base strong probable-prime chain
       above it -- where the certificate (certify_run), not this leg, is
       the proof;
    2. sympy's BPSW, an independent implementation, which must agree on the
       run LENGTH and not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense k line and uses no wheel at all, must
       agree that this k survives a sieve at a DIFFERENT depth from the
       campaign's.

    plus a factor witness for the composite that STOPS the run, which is
    what bounds the claim to exactly `run`.  Nothing here is unbounded: the
    witness is trial division, then a bounded rho, then bounded ECM.
    """
    legs = {"mr_chain": all(mr_is_prime(ref.value(k, i, s))
                            for i in range(1, run + 1)),
            "sympy_bpsw": ref.run_length(k, s, cap=run + 1) == run,
            "resieve_other_wheel": cpu.CpuEngine(run, s, q2=4096).survives(k)}
    stop = ref.value(k, run + 1, s)
    legs["stopper_composite"] = not mr_is_prime(stop)
    ok = all(legs.values())
    wit = factor_witness(stop) if legs["stopper_composite"] else None
    return ok, legs, {"i": run + 1, "value": stop, "factor": wit}


def certify_run(k, run, s, only=None):
    """A checkable primality certificate for every value prime(i)*k + s,
    i = 1..run: ({str(i): proof}, [the i left UNPROVED]).

    Below the deterministic bound huntlib.certificate.prove answers with
    the deterministic Miller-Rabin test, which IS the proof there.  Above
    it, for s = +1, N - 1 = prime(i)*k: so k is factored ONCE -- trial division, a bounded
    rho, bounded ECM, then sympy's factorint on whatever is left, which for
    a k under the 3.317e24 ceiling is a 25-digit number and seconds at
    most (the bound huntlib.primes.factor_witness already accepts on the
    stopper, in the same live path) -- and every value gets BLS75 Theorem 1
    on that one factorization.  Every prime factor of k is under the bound
    because k is, so the certificate is one level deep.  A value the shared
    factorization cannot prove (R = 1 once k is factored, so it should not
    happen) falls back to certificate.prove's own bounded search, and for
    s = -1 only that fallback runs: the structure there is on N + 1, the
    ceiling keeps that family under the bound, and the answer stays honest
    if it is ever asked.

    Every proof is RE-VERIFIED from scratch before it is returned.  A
    certificate that was not checked is a claim, not a certificate.
    """
    k, s = int(k), int(s)
    fac, R = certificate.factor_partial(k, ecm_curves=200)
    if R > 1:
        from sympy import factorint
        for p, e in factorint(R).items():
            fac[int(p)] = fac.get(int(p), 0) + int(e)
    certs, unproved = {}, []
    for i in (range(1, run + 1) if only is None else only):
        N = ref.value(k, i, s)
        proof = None
        if s > 0:
            facN = dict(fac)
            p = ref.rung(i)
            facN[p] = facN.get(p, 0) + 1
            proof = certificate.prove(N, fac=facN)
        if proof is None:
            proof = certificate.prove(N)
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
        certs[str(i)] = proof
        if proof is None:
            unproved.append(int(i))
    return certs, unproved


# ----------------------------- classification -------------------------------

def sprp_run(k, s, cap, floor=CENSUS_FLOOR):
    """Run length of k, screened with a base-2 strong test and CONFIRMED
    with the deterministic chain wherever the answer matters.

    A failed base-2 test is a PROOF of compositeness (huntlib.primes), so
    the first pass can only overstate a run, never understate it.  Runs
    that come out below the census floor are never looked at again, so an
    overstatement there costs nothing; a run at or above it is recomputed
    with the full base set, which is the deterministic answer below the
    proof crossing k_proof(n, s) and a strong probable-prime answer above
    it (a DISCOVERY there is proved by certificate; the census is a count).
    Measured on real survivors: 13.1 us against 49.6 us for the all-bases
    chain, with identical run lengths (the classification drill asserts it).
    """
    r = 0
    while r < cap and sprp_base2(ref.rung(r + 1) * k + s):
        r += 1
    if r >= floor:
        r = 0
        while r < cap and mr_is_prime(ref.rung(r + 1) * k + s):
            r += 1
    return r


def _classify_chunk(task):
    """Pool worker: run lengths of a chunk of survivors, in order.

    Module-level and self-contained so it survives Windows spawn; touches
    no GPU, so workers never contend with the parent's device work."""
    s, cap, ks = task
    return [sprp_run(int(k), s, cap) for k in ks]


def _worker_init():
    _pool.worker_init("numpy", "sympy")


def _pool_factory(workers):
    return _cf.ProcessPoolExecutor(max_workers=workers,
                                   initializer=_worker_init)


class _Done:
    """A completed 'future' for the inline (no pool) path."""

    def __init__(self, value):
        self._v = value

    def done(self):
        return True

    def result(self):
        return self._v


def _submit(pool, s, cap, ks):
    """Hand a launch's survivors to the pool.  Returns [(ks_chunk, future)]
    in survivor order; with no pool the chunk is classified right here."""
    ks = [int(k) for k in ks]
    out = []
    for i in range(0, len(ks), CHUNK):
        chunk = ks[i:i + CHUNK]
        if pool is None:
            out.append((chunk, _Done(_classify_chunk((s, cap, chunk)))))
        else:
            out.append((chunk, pool.submit(_classify_chunk, (s, cap, chunk))))
    return out


# --------------------------------- campaign ---------------------------------

class Campaign:
    def __init__(self, args, ckpt=None, cursor=None, pool=None):
        # `ckpt`/`cursor`/`pool` are overridable for ONE reason: so the
        # selftest can instantiate a campaign against a scratch file and
        # exercise the wiring -- checkpoint round trip, status line, census,
        # rungs -- without sweeping.  A launcher whose loop is only ever run
        # for real is a launcher whose first bug is the owner's to find.
        self.args = args
        self.s = int(args.sign)
        self.fam = ref.FAMILIES[self.s]
        self.oeis = self.fam["oeis"]
        self.key = config_key(self.s)
        self.ckpt = ckpt or ckpt_path(self.s)
        self.cursor = cursor or _POLICIES[self.s]
        self.pool = pool
        self.found = {}                # str(n) -> k found by THIS campaign
        self.census = {}               # run length -> count
        self.passed = []
        self.elapsed = 0.0
        self.discoveries = 0
        self.near = 0
        self.survivors = 0             # classified this campaign
        self.j = None                  # the period being worked
        self.u = 0                     # third-level cursor inside it (WORK)
        self.pending = []              # classified, not yet narrated
        self._stored_w = 0
        # the ADOPTED overlap: line below this was swept by the engine
        # whose cursor this one re-denominated, so it is re-swept as a
        # cross-check and neither counted nor narrated (a discovery there
        # is an ALARM: the two wheels would disagree about cleared line)
        self.census_floor = 0
        self._adopt_k = None
        self.hb = Heartbeat(interval=args.heartbeat)
        self._lad = LiveLadder(self._build_ladder)
        self._t0 = time.time()
        self.workers = None            # the pool's size once size_pool ran
        self._sizing = None            # the measurement it was sized from
        self._hostwait = 0.0           # seconds the device waited on the pool
        self._hw_ref = (0.0, time.time())
        self._hostbound_logged = False
        self._ckpt_t = 0.0             # when the last mid-period save landed
        self._ckpt_every_s = CKPT_MIN_S
        self._snapshot = None
        self._proof_logged = None      # the filter whose crossing was logged
        self.loaded = self.load()
        self.eng = gpu.GpuEngine(self.filter_n(), self.s, p1=P1, p2=P2,
                                 p3=P3, q2=Q2, unit=UNIT[self.s])
        if self._adopt_k is not None:
            # RE-DENOMINATION, here where the engine exists to floor
            # against: the policy decided only that the old cursor is
            # readable.  Floored, never rounded up -- an overlap is a free
            # cross-check, a gap is a lost frontier.  The old period's
            # in-flight values are dropped: they sit above the new
            # boundary and will be classified again.
            self.j = self._adopt_k // int(self.eng.W)
            self.u = 0
            self.pending = []
            self.census_floor = self._adopt_k
            self._stored_w = 0
            log("STAGE", f"cursor re-denominated: the adopted claim 'swept "
                         f"to k = {self._adopt_k:,}' becomes period "
                         f"{self.j} of W = {int(self.eng.W):,} (floored: "
                         f"{self._adopt_k - self.j * int(self.eng.W):,} of "
                         f"line is re-swept as a cross-check, not counted)")
        # STORE THE UNIT NEXT TO THE NUMBER AND ASSERT IT ON LOAD
        # (OPTIMIZATION.md 2.9).  The config key DESCRIBES the wheel, which
        # is documentation; this is the assertion.
        if self._stored_w and self._stored_w != int(self.eng.W):
            raise ValueError(
                f"{self.ckpt} counts periods of W = {self._stored_w:,} but "
                f"this engine's period is {int(self.eng.W):,}: the cursor "
                f"means something else and has to be re-denominated, not "
                f"read")
        if self.j is None:
            self.j, self.u = 0, 0      # period 0, clipped at K_START
        self.boundary = self.j
        # `discoveries` is CUMULATIVE and restored by load(), so "have there
        # been any finds" is not "has THIS RUN found something" the moment a
        # resumed campaign has history.  --stop-on-discovery means the second
        # one, and it is latched where the find is confirmed.
        self._discoveries_at_start = self.discoveries
        self.mark_boundary()

    # ------------------------------------------------------------- frontier
    def frontier(self):
        """The largest n settled: the literature plus this campaign."""
        top = max(ref.KNOWN[self.s])
        for n in self.found:
            top = max(top, int(n))
        return top

    def frontier_k(self):
        n = self.frontier()
        return int(self.found.get(str(n), ref.KNOWN[self.s].get(n, 0)))

    def filter_n(self):
        """The sieve filter is always the next OPEN term."""
        return self.frontier() + 1

    def k_min(self):
        """The clip for the period being worked: K_START inside period 0,
        none elsewhere."""
        return K_START if self.j == 0 else None

    # ----------------------------------------------------------------- rungs
    def _build_ladder(self, frontier, frontier_k, n):
        ceil = cpu.k_ceil(n, self.s)
        preds = model.predictions(self.s, frontier, frontier_k,
                                  n_ahead=3, ceiling=ceil)
        return Ladder.from_predictions(preds, ceiling=ceil,
                                       ceiling_label="engine ceiling")

    def ladder(self):
        """Derived from the LIVE frontier (a rung retires with its term) and
        REBUILT only when it moves -- the frontier is the first argument of
        LiveLadder.get by signature (OPTIMIZATION.md 2.14)."""
        return self._lad.get(self.frontier(), self.frontier_k(),
                             self.filter_n())

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
        """The k from which the CLASSIFICATION at the current filter is a
        probable-prime chain rather than a proof (pladder_search.k_proof)."""
        return cpu.k_proof(self.filter_n(), self.s)

    def check_proof_crossing(self, k):
        """One [MILESTONE] line per filter when the sweep passes the proof
        crossing; a campaign resumed above it says so at start.  Cheap --
        one comparison -- so it may run in the loop (no model here)."""
        if self._proof_logged == self.filter_n():
            return
        pc = self.proof_crossing()
        if k >= pc:
            self._proof_logged = self.filter_n()
            log("MILESTONE",
                f"past the proof crossing k_proof({self.filter_n()}, "
                f"{self.s:+d}) = {pc:.4g}: prime({self.filter_n()})*k "
                f"{self.s:+d} now exceeds the deterministic Miller-Rabin "
                f"bound, so classification is a thirteen-base strong "
                f"probable-prime chain from here and a DISCOVERY is proved "
                f"by BLS75 certificate (certify_run); the ceiling is k < "
                f"{cpu.k_ceil(self.filter_n(), self.s):.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "sign": self.s,
                "unit": int(self.eng.unit),
                "j": int(self.j),
                "u": int(self.u),
                "W": int(self.eng.W),
                "census_floor": int(self.census_floor),
                # the COVERAGE claim: every k in [K_START, k) is swept.  It
                # is the period boundary, never the live (j, u) cursor,
                # because a part-swept period is not contiguous in k.
                "k": int(self.swept_k()),
                "k_start": K_START,
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
                "survivors": self.survivors,
                "saved": time.strftime("%Y-%m-%d %H:%M:%S")}

    def mark_boundary(self):
        """Snapshot the state as of the last fully classified launch.

        This is what an interrupt writes.  Every field is committed HERE --
        a field folded in later would be silently dropped on the exit path
        the program actually uses (CONVENTIONS.md "Ctrl+C").
        """
        self._snapshot = self.state()

    def save(self):
        self.mark_boundary()
        return checkpoint.save(self.ckpt, self._snapshot)

    def save_boundary(self):
        return checkpoint.save(self.ckpt, self._snapshot or self.state())

    def load(self):
        st, kind = self.cursor.load(warn=lambda m: log("STAGE", m))
        if not st:
            return False
        if kind == "adopted":
            # only the CLAIM carries over; every index is re-derived in
            # __init__ once the engine exists to floor against
            self._adopt_k = int(st.get("k", 0))
            log("STAGE", f"checkpoint written by {st.get('key')} adopted: "
                         f"it claims the line swept to k = "
                         f"{self._adopt_k:,}")
        self._stored_w = int(st.get("W", 0))
        self.j = int(st["j"])
        self.u = int(st.get("u", 0))
        self.census_floor = int(st.get("census_floor", 0))
        self.pending = [(int(k), int(r)) for k, r in st.get("pending", [])]
        self.found = dict(st.get("found", {}))
        self.census = {int(r): int(c) for r, c in st.get("census", {}).items()}
        self.passed = list(st.get("passed", []))
        self.elapsed = float(st.get("elapsed", 0.0))
        self.discoveries = int(st.get("discoveries", 0))
        self.near = int(st.get("near", 0))
        self.survivors = int(st.get("survivors", 0))
        return True

    def swept_k(self):
        """The k below which EVERY value at or above K_START has been swept
        -- the coverage claim.  It is the period boundary, except while the
        first period after a re-denomination is still running: the line
        under `census_floor` was swept by the engine whose cursor this one
        adopted, and that claim is exactly what was adopted (taking the max
        is the difference between reporting the frontier and losing most of
        a period of it, in the heartbeat AND in the checkpoint).  Inside
        period 0 it is 0, and the least-claim there is monotonicity
        (nothing below a(frontier) can be the next term)."""
        return max(self.boundary * self.eng.W, self.census_floor)

    def u_progress(self, jn, un):
        """A k for the HEARTBEAT inside a period -- progress, not coverage."""
        return int(jn * self.eng.W
                   + self.eng.W * un // max(self.eng.R3, 1))

    # ------------------------------------------------------------- status
    def status_line(self):
        # TWO cursors (CONVENTIONS.md "Two cursors"): `pos` is PROGRESS
        # through the period being worked and prices an ETA; `cov` is the
        # COVERAGE claim, and it alone says which rungs are passed and how
        # much of the open term's mass is behind us.  Reading the rungs off
        # `pos` said "next engine ceiling" and "P(a(12)) = 100%" at swept-to
        # 0 on 2026-09-03, because at n = 12 every rung sits inside period 0.
        k = (self.hb.pos() or self.swept_k())
        cov = self.swept_k()
        rate = self.hb.rate()
        lo = self.boundary * self.eng.W
        pct = min(100.0, max(0.0, 100.0 * (k - lo) / self.eng.W))
        parts = [f"swept to {self.swept_k():.6g}",
                 f"period {self.boundary} [{lo:.5g}, {lo + self.eng.W:.5g}) "
                 f"{pct:.0f}%"]
        if self.census_floor > lo:
            # keyed off the PERIOD: being in the adopted overlap is a
            # property of which period is being worked
            parts.append(f"RE-SWEEPING the adopted overlap below "
                         f"{self.census_floor:.6g} as a cross-check "
                         f"(not counted; frontier holds)")
        parts.append(f"{self.oeis} filter n = {self.filter_n()}")
        if rate:
            parts.append(f"{rate:.3g} k/s")
        parts.append(census_str(self.census, CENSUS_FLOOR, self.frontier()))
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
            parts.append(f"next {lab} {d:.3g} (ETA {eta})")
            p = model.p_by(self.filter_n(), self.s,
                           model.floor_for(self.filter_n(), self.s,
                                           self.frontier_k()), cov)
            parts.append(f"P(a({self.filter_n()}) under the claim) = "
                         f"{100 * p:.0f}%")
        stall = self.hb.stalled()
        if stall:
            parts.append(f"-- no segment closed since the last status: "
                         f"{stall[0]} for {stall[1]:.0f}s")
        return "  ".join(parts)

    # --------------------------------------------------------------- hits
    def handle(self, k, run):
        """Classify one value at a period close.  True if it was a find."""
        frontier = self.frontier()
        kind = event_kind(run, frontier)
        if kind is None:
            return False
        if k < self.census_floor:
            # THE ADOPTED OVERLAP: the previous wheel cleared this line.
            # Its census was counted then and its NEAR values narrated
            # then; a discovery-grade run here means the two wheels
            # disagree about swept line, which is an alarm and not a find.
            if kind == "DISCOVERY":
                log("ALARM", f"run {run} at k = {k:,} lies BELOW the adopted "
                             f"coverage claim {self.census_floor:,}: the "
                             f"previous wheel swept this line and recorded "
                             f"no such run, so one of the two wheels is "
                             f"wrong about it -- halting")
                raise SystemExit(2)
            return False
        self.census[run] = self.census.get(run, 0) + 1
        if kind == "CENSUS":
            return False
        if kind == "NEAR":
            self.near += 1
            ok, legs, _ = verify(k, run, self.s)
            if not ok:
                log("ALARM", f"NEAR value k = {k:,} run {run} failed "
                             f"verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at k = {k:,} (run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of a({frontier + 1})!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, k, run):
        frontier = self.frontier()
        self.hb.doing(f"verifying run-{run} k={k}")
        ok, legs, stop = verify(k, run, self.s)
        if not ok:
            log("ALARM", f"claimed a({frontier+1}) = {k} failed the "
                         f"protocol: {legs}")
            raise SystemExit(2)
        settles = list(range(frontier + 1, run + 1))
        self.hb.doing(f"certifying run-{run} k={k}")
        certs, unproved = certify_run(k, run, self.s)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        # The record speaks the OEIS entry's language (CONVENTIONS.md
        # "Naming in an evidence file"): the published integer under the
        # entry's own letter, a `forms` that uses it, and `oeis_terms`
        # saying literally what goes into the OEIS.
        forms = "k*prime(i) %s 1, i = 1..n" % ("+" if self.s > 0 else "-")
        ev = {**evidence.header(self.oeis, forms, "k", k, settles),
              "sign": self.s,
              "run": int(run), "settles": settles,
              "values": {str(i): int(ref.value(k, i, self.s))
                         for i in range(1, run + 1)},
              "verification": legs,
              "stopper": {"i": stop["i"], "prime": ref.rung(stop["i"]),
                          "value": int(stop["value"]),
                          "factor": stop["factor"]},
              "certificates": certs,
              # every proof above was re-verified from scratch before it
              # was accepted; `unproved` lists any i that has none
              "certificates_verified": not unproved,
              "unproved": unproved,
              "proof_routes": routes,
              "least_claim": {"swept_from": K_START,
                              "swept_to": int(k),
                              "wheel": int(self.eng.W), "sieve_depth": Q2,
                              "monotone_floor": ref.KNOWN[self.s][
                                  max(ref.KNOWN[self.s])]},
              "engine": self.key}
        for n in settles:
            self.found[str(n)] = int(k)
        path = evidence.record(
            ev, EVID, f"{self.oeis}_a{settles[0]}_{k}.json",
            ledger_path(self.s), key="k",
            label="%s a(%s)" % (self.oeis, ",".join(map(str, settles))))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        banner("DISCOVERY", [
            f"{self.oeis} a({settles[0]}) = {k:,}" if len(settles) == 1 else
            f"{self.oeis} a({settles[0]})..a({settles[-1]}) = {k:,}",
            f"run {run}: prime(i)*k {self.s:+d} is prime for i = 1..{run}",
            f"stopped by {ref.rung(stop['i'])}*k {self.s:+d} = "
            f"{stop['value']:,} = {stop['factor']} * ...",
            f"verified 3 ways, {proved} of {len(certs)} certificates "
            f"re-verified ({', '.join(f'{r} x{c}' for r, c in sorted(routes.items()))}), "
            f"evidence {path}",
        ] + ([f"UNPROVED at i = {unproved}: those values passed the "
              f"Miller-Rabin chain and BPSW but no certificate landed within "
              f"the bounded effort -- the find stands on the three legs; "
              f"certify them by hand from the evidence file"]
             if unproved else []))

    def follow_frontier(self):
        """After a find: rebuild the engine at the next open term.

        The wheel PRIMES do not depend on n, so W is unchanged and the
        cursor keeps its meaning; only the residue tables shrink.  The
        period just closed was swept under a SMALLER filter, whose
        survivors are a superset of the new filter's, and every one of them
        has been classified -- so there is nothing to re-sweep and coverage
        stays contiguous from the next period on.
        """
        old_n = self.eng.n
        self.eng = gpu.GpuEngine(self.filter_n(), self.s, p1=P1, p2=P2,
                                 p3=P3, q2=Q2, unit=UNIT[self.s])
        if int(self.eng.W) != self._snapshot["W"]:
            raise RuntimeError("the wheel period changed with the filter; "
                               "the cursor would need re-denomination")
        log("STAGE", f"filter follows the frontier: n = {old_n} -> "
                     f"{self.eng.n}; the ladder now aims at "
                     f"a({self.filter_n()})")
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({n})")
                                  for n in self.found)]
        # the crossing moves with the filter (prime(n) grew), and may
        # already be behind the sweep
        self.check_proof_crossing(self.swept_k())
        # and the host's need moved with it: re-measure, re-size
        self.size_pool()

    # ----------------------------------------------------------- the pool
    def line_per_launch(self):
        cfg = self.eng.config()
        return self.eng.R1 * self.eng.R2 * cfg["nu"] / self.eng.density()

    def calibrate(self):
        """MEASURE this configuration on the launches the loop is about to
        run: device k/s, survivors per second, host cost per survivor.
        Nothing is recorded -- the loop sweeps the same launches again."""
        sync = self.eng.cp.cuda.Stream.null.synchronize
        it = self.eng.sweep(self.j, self.j + 1, u_from=self.u,
                            k_min=self.k_min())
        surv, launches = [], 0
        sync()
        t0 = time.perf_counter()
        try:
            for _jn, un, sv in it:
                launches += 1
                surv.extend(int(k) for k in sv)
                sync()
                el = time.perf_counter() - t0
                if (un == 0 or el >= CAL_MAX_S
                        or (len(surv) >= CAL_MIN_SURVIVORS and el >= CAL_MIN_S)):
                    break
        finally:
            it.close()
        dt = max(time.perf_counter() - t0, 1e-9)
        cap = self.filter_n() + 8
        sample = surv[:CAL_SAMPLE]
        t1 = time.perf_counter()
        for k in sample:
            sprp_run(k, self.s, cap)
        cost = (time.perf_counter() - t1) / max(len(sample), 1)
        per_s = len(surv) / dt
        return {"launches": launches, "seconds": dt,
                "rate": launches * self.line_per_launch() / dt,
                "survivors": len(surv), "per_s": per_s, "cost": cost,
                "need": per_s * cost}

    def size_pool(self):
        """Size the classification pool FROM THE MEASUREMENT at this filter
        (CLAUDE.md 5f/5g), unless --workers was given; ramp it; and do it
        again whenever the filter moves.  Returns the size."""
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
                   f"s of device at {m['rate']:.3g} k/s: {m['per_s']:,.0f} "
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
            return self.workers        # the same, or within the noise
        if self.pool is not None:      # idle: a period has closed and drained
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
        """The device may run at most BACKLOG_LAUNCHES ahead of the pool.
        Past that, wait for the oldest launch: the host binds, and it binds
        VISIBLY -- the wait is timed into the heartbeat."""
        if len(inflight) <= BACKLOG_LAUNCHES:
            return
        t0 = time.perf_counter()
        while len(inflight) > BACKLOG_LAUNCHES:
            _cur, parts = inflight[0]
            for _ks, f in parts:
                f.result()                          # blocks
            self._drain(inflight, block=False)      # pops the done head
        self._hostwait += time.perf_counter() - t0
        if not self._hostbound_logged:
            self._hostbound_logged = True
            log("WARN", f"host-bound: the classification pool ({self.workers} "
                        f"workers) is not keeping up with the device, which "
                        f"now waits on it ({BACKLOG_LAUNCHES} launches of "
                        f"back-pressure). The pool was sized from a "
                        f"measurement at this filter, so either the machine "
                        f"is busy or the measurement was wrong; the "
                        f"[STATUS] line carries the fraction of wall clock "
                        f"spent waiting")

    # ---------------------------------------------------------- draining
    def _drain(self, inflight, block):
        """Move classified launches from `inflight` into `pending`, in
        launch order, and advance the WORK cursor behind them.

        `inflight` holds (cursor_after_launch, [(ks, future)]).  Without
        `block` only launches whose every chunk is done are taken, so the
        cursor written by a mid-period checkpoint never runs ahead of the
        classification -- a crash then redoes the unclassified launches
        instead of losing their survivors.
        """
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
            if cur[1]:                         # still inside the period
                self.j, self.u = cur
            else:                              # the period's last launch
                self.j, self.u = cur[0] - 1, 0
                self._period_done = True

    # ---------------------------------------------------------------- loop
    def run(self):
        target = int(self.args.to or cpu.k_ceil(self.filter_n(), self.s))
        log("STAGE", f"campaign {self.key}")
        log("STAGE", device_report(self.eng.bytes_held()))
        cfg = self.eng.config()
        log("STAGE",
            f"sweeping the k line to {target:.4g}; {self.oeis} filter n = "
            f"{self.filter_n()}; wheel W = {self.eng.W:,} "
            f"({self.eng.R:,} residues, {self.eng.R1} x {self.eng.R2} x "
            f"{self.eng.R3}, {100.0 * self.eng.density():.5f}% of the line); "
            f"{cfg['nu']} third-level residues per launch, "
            f"{-(-self.eng.R3 // cfg['nu'])} launches per period; resume at "
            f"period {self.j}, u = {self.u} (k = "
            f"{self.u_progress(self.j, self.u):,})")
        for n, qs in sorted(model.predictions(
                self.s, self.frontier(), self.frontier_k(),
                n_ahead=3, ceiling=cpu.k_ceil(self.filter_n(), self.s)).items()):
            log("STAGE", "  a(%d): %s" % (n, "  ".join(
                "%s %.3g" % (q, v) for q, v in qs.items())))
        log("STAGE", "the heartbeat carries TWO numbers, and they are not "
                     "the same claim: 'swept to' is the k below which EVERY "
                     "value at or above K_START has been tested, and it "
                     "advances one whole wheel period (%.4g of line) at a "
                     "time; 'period N .. X%%' is progress THROUGH the period "
                     "being worked, whose candidates arrive out of k order, "
                     "so no part of it is clear until that reads 100%%."
                     % self.eng.W)
        log("STAGE", f"proofs: classification is a deterministic "
                     f"Miller-Rabin proof below the proof crossing "
                     f"k_proof({self.filter_n()}, {self.s:+d}) = "
                     f"{self.proof_crossing():.4g} and a thirteen-base strong "
                     f"probable-prime chain above it; a DISCOVERY is proved "
                     f"by certificate either way (certify_run), and the "
                     f"engine ceiling {target:.4g} is the family's "
                     f"primality-proof validity bound")
        self.check_proof_crossing(self.swept_k())
        self.size_pool()
        self.hb.mark(self.u_progress(self.j, self.u))
        self.hb.start(self.status_line)
        shutdown.on_interrupt(self._on_interrupt)
        stop_now = False
        cap = self.filter_n() + 8
        try:
            while self.swept_k() < target and not stop_now:
                j1 = self.j + 1                 # ONE PERIOD
                if j1 * self.eng.W > cpu.k_ceil(self.filter_n(), self.s):
                    break
                self.hb.doing(f"sieving period {self.j} "
                              f"[{self.j * self.eng.W:.4g}, "
                              f"{j1 * self.eng.W:.4g})")
                inflight = collections.deque()
                self._period_done = False
                since = 0
                for jn, un, surv in self.eng.sweep(self.j, j1, u_from=self.u,
                                                   k_min=self.k_min()):
                    inflight.append(((jn, un),
                                     _submit(self.pool, self.s, cap, surv)))
                    self._drain(inflight, block=False)
                    self._backpressure(inflight)
                    since += 1
                    if (since >= CKPT_LAUNCHES and un
                            and time.time() - self._ckpt_t >= self._ckpt_every_s):
                        since = 0
                        self.hb.mark(self.u_progress(self.j, self.u))
                        t_save = time.perf_counter()
                        self.save()
                        cost = time.perf_counter() - t_save
                        self._ckpt_t = time.time()
                        self._ckpt_every_s = max(CKPT_MIN_S,
                                                 cost / CKPT_COST_FRACTION)
                    if self.args.gpu_yield_ms:
                        time.sleep(self.args.gpu_yield_ms / 1000.0)
                    if un == 0:
                        break
                self.hb.doing(f"classifying the tail of period {self.j}")
                self._drain(inflight, block=True)
                # The period is closed, so its values are contiguous in k
                # again and the LEAST of them is meaningful.  Nothing is
                # narrated before this point.
                held = len(self.pending)
                found_now = False
                for k, r in sorted(self.pending):
                    found_now = self.handle(k, r) or found_now
                self.pending = []
                self.j, self.u = j1, 0
                self.boundary = self.j
                log("STAGE",
                    f"period {j1 - 1} complete: swept to {self.swept_k():,} "
                    f"(+{self.eng.W:.4g} of line; {held} value"
                    f"{'' if held == 1 else 's'} at run >= {CENSUS_FLOOR} "
                    f"classified in k order)")
                if found_now:
                    self.mark_boundary()
                    self.follow_frontier()
                    cap = self.filter_n() + 8
                    stop_now = bool(self.args.stop_on_discovery)
                self.hb.mark(self.swept_k())
                self.check_rungs(self.swept_k())
                self.check_proof_crossing(self.swept_k())
                self.save()
                if stop_now:
                    log("STAGE", "stopping on discovery "
                                 "(--stop-on-discovery): THIS run confirmed "
                                 "a frontier-extending find")
        finally:
            self.hb.stop()
            if self.pool is not None:
                self.pool.shutdown(wait=False, cancel_futures=True)
        landed = self.save()
        log("STAGE", f"campaign stopped at k = {self.swept_k():,} "
                     f"({self.discoveries} find(s) this campaign; checkpoint "
                     f"{'written' if landed else 'DEFERRED -- held open'})")
        return 0

    def _on_interrupt(self):
        # The message says what LANDED, not what was attempted: a save can
        # be deferred by another process's handle on the checkpoint.
        snap = self._snapshot or self.state()
        if self.save_boundary():
            return (f"checkpoint written at the last classified launch: "
                    f"period {int(snap['j'])}, u = {int(snap['u'])}, swept "
                    f"to k = {int(snap['k']):,} ({self.ckpt})")
        return (f"{self.ckpt} is held open by another process, so THIS "
                f"boundary (period {int(snap['j'])}, u = {int(snap['u'])}) "
                f"was not written; the run resumes from the last save that "
                f"landed")


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """All four outcomes of the taxonomy, on this project's mathematics."""
    return [((14, 13), "DISCOVERY"),      # beyond the frontier
            ((17, 13), "DISCOVERY"),      # a long run settles several at once
            ((13, 13), "NEAR"),           # one condition short of a(14)
            ((12, 13), "CENSUS"),         # below the frontier: counted only
            ((8, 13), "CENSUS"),          # the census floor itself
            ((7, 13), None),              # under the floor: not even counted
            ((0, 13), None)]


def _canary_hunt():
    """The stream must organically rediscover known terms, on both families.

    Dedicated mini-hunts at the filters those terms belong to.  The
    production filter cannot rediscover them -- a(8) has run 8 and an
    n = 14 wheel is entitled to kill it -- so rediscovery is done at the
    filter each term belongs to, sweeping period 0 from the engine floor
    with the clip, and the prefix [1, floor] checked by the oracle so
    "FIRST occurrence" is a claim about the line and not about a window.
    """
    hits_all = []
    # in k space, and in unit space at the unit those filters force (30):
    # the stream that sweeps k' = k / 30 must find the same first k
    for s, n, unit in ((+1, 8, 1), (+1, 9, 1), (-1, 8, 1), (-1, 9, 1),
                       (+1, 8, 30), (+1, 9, 30), (-1, 9, 30)):
        want = ref.KNOWN[s][n]
        eng = gpu.GpuEngine(n, s, p1=13, p2=None, p3=None, q2=4096,
                            unit=unit)
        lo = cpu.k_floor(4096) + 1
        if ref.first_k(n, s, lo=1, hi=lo - 1) is not None:
            return False, (f"CANARY FAIL: s={s:+d} n={n}: the oracle found a "
                           f"run-{n} below the engine floor")
        ceng = cpu.CpuEngine(n, s, q2=4096)
        surv = eng.survivors_j(0, want // eng.W + 1, k_min=lo)
        hits = [int(k) for k in surv if ceng.run_length(int(k), cap=n) >= n]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: {ref.FAMILIES[s]['oeis']} filter "
                           f"n={n} unit={unit} found "
                           f"{min(hits) if hits else None}, expected a({n}) "
                           f"= {want}")
        hits_all.append(f"{ref.FAMILIES[s]['oeis']} a({n})"
                        + (f" (unit {unit})" if unit > 1 else ""))
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as FIRST occurrences at their own "
                  "filters, sweeping period 0 from the engine floor with the "
                  "prefix cleared by the oracle -- in k space and in unit "
                  "space")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on both families."""
    for s in (+1, -1):
        top = max(ref.KNOWN[s])
        k = ref.KNOWN[s][top]
        ok, legs, stop = verify(k, top, s)
        if not ok:
            return False, (f"PROTOCOL FAIL: genuine run-{top} at k={k} "
                           f"(s={s:+d}) rejected: {legs}")
        if stop["i"] != top + 1 or stop["factor"] is None:
            return False, (f"PROTOCOL FAIL: s={s:+d}: no factor witness for "
                           f"the stopper")
        if (stop["value"] % stop["factor"]) or stop["factor"] in (1, stop["value"]):
            return False, f"PROTOCOL FAIL: s={s:+d}: the witness is not a factor"
        bad, legs_b, _ = verify(k, top + 1, s)
        if bad:
            return False, (f"PROTOCOL FAIL: fake run-{top+1} claim at k={k} "
                           f"(s={s:+d}) ACCEPTED ({legs_b})")
        prev = max(n for n in ref.KNOWN[s] if ref.KNOWN[s][n] < k)
        fake, _lc, _ = verify(ref.KNOWN[s][prev], top, s)
        if fake:
            return False, (f"PROTOCOL FAIL: s={s:+d}: a({prev})'s k accepted "
                           f"as a run-{top}")
    return True, ("protocol ok, both families: each frontier term accepted "
                  "at its true run with a factor witness for its stopper, "
                  "and a run one too long and a mislabelled earlier term "
                  "both rejected")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing."""
    raised = []
    eng = gpu.GpuEngine(12, +1, p1=13, p2=None, p3=None, q2=1024)
    ceil = cpu.k_ceil(12, +1)
    try:
        eng.sweep(ceil // eng.W - 1, ceil // eng.W + 2)
        return False, "CEILING FAIL: the GPU engine swept past k_ceil"
    except ValueError:
        raised.append("gpu k_ceil")
    try:
        eng.sweep(0, 2)
        return False, "CEILING FAIL: the GPU engine swept period 0 unclipped"
    except ValueError:
        raised.append("gpu floor")
    try:
        eng.sweep(0, 2, k_min=cpu.k_floor(1024))
        return False, "CEILING FAIL: a clip AT the floor was accepted"
    except ValueError:
        raised.append("gpu k_min <= floor")
    c = cpu.CpuEngine(12, +1, q2=1024)
    try:
        c.survivors(10 ** 5, cpu.k_ceil(12, +1) + 10)
        return False, "CEILING FAIL: the CPU engine swept past k_ceil"
    except ValueError:
        raised.append("cpu k_ceil")
    # the two families have DIFFERENT ceilings (pladder_search.k_ceil):
    # A084700's is the deterministic bound on k, A084701's its proof
    # crossing, and the engines enforce each
    if cpu.k_ceil(18, +1) != MR_VALID_BELOW or \
            cpu.k_ceil(12, -1) != cpu.k_proof(12, -1) or \
            not cpu.k_proof(18, +1) < cpu.k_ceil(18, +1):
        return False, ("CEILING FAIL: the family ceilings are not the "
                       "proof bounds G10 pins")
    engm = gpu.GpuEngine(12, -1, p1=13, p2=None, p3=None, q2=1024)
    ceilm = cpu.k_ceil(12, -1)
    try:
        engm.sweep(ceilm // engm.W - 1, ceilm // engm.W + 2)
        return False, ("CEILING FAIL: the A084701 engine swept past its "
                       "proof crossing")
    except ValueError:
        raised.append("gpu k_ceil (s = -1: the proof crossing)")
    try:
        cpu.CpuEngine(12, -1, q2=1024).survivors(10 ** 5, ceilm + 10)
        return False, ("CEILING FAIL: the A084701 CPU engine swept past its "
                       "proof crossing")
    except ValueError:
        raised.append("cpu k_ceil (s = -1)")
    try:
        c.survivors(10, 10 ** 6)
        return False, "CEILING FAIL: the CPU engine swept at the floor"
    except ValueError:
        raised.append("cpu floor")
    try:
        gpu.wheel(14, +1, 47)          # 2.4e10 residues in one level
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(14, +1, p1=29, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    try:
        gpu.GpuEngine(14, +1, p1=13, p2=37, p3=None, q2=4096)
        return False, "CEILING FAIL: an oversized second level was accepted"
    except ValueError:
        raised.append("gridDim.y")
    try:
        gpu.GpuEngine(gpu.NRES_MAX + 1, +1, p1=13, p2=None, p3=None, q2=1024)
        return False, ("CEILING FAIL: a filter longer than the tail's "
                       "residue list was accepted")
    except ValueError:
        raised.append("n <= NRES_MAX")
    try:
        gpu.GpuEngine(14, 0)
        return False, "CEILING FAIL: a sign other than +-1 was accepted"
    except ValueError:
        raised.append("sign")
    return True, ("ceiling ok: %s all raise rather than compute" %
                  ", ".join(raised))


def _certificate_drill():
    """A discovery past the proof crossing is PROVED, not just tested.

    Below the crossing every certificate takes the deterministic route.
    Above it the value's own structure -- N - 1 = prime(i)*k, k factored
    once -- gives BLS75 Theorem 1, and the proof must re-verify from
    scratch and refuse a neighbouring N.  Drilled on the A084700 frontier
    (every value under the bound) and on the first wheel k past
    k_proof(18, +1) whose 18th value is a strong probable prime -- a value
    past the bound, proved by exactly the wiring the campaign runs when
    a(18) lands.
    """
    top = max(ref.KNOWN[+1])
    k = ref.KNOWN[+1][top]
    certs, unproved = certify_run(k, top, +1)
    if unproved or len(certs) != top:
        return False, (f"CERTIFICATE FAIL: A084700 a({top}) left "
                       f"{unproved} unproved")
    if any(c.get("proof") != "deterministic-mr" for c in certs.values()):
        return False, ("CERTIFICATE FAIL: a value under the bound took the "
                       "certificate route")
    m = -(-cpu.k_proof(18, +1) // 2310)
    kk = None
    for _ in range(4000):
        cand = 2310 * m
        if ref.value(cand, 18, +1) >= MR_VALID_BELOW and \
                sprp_base2(ref.value(cand, 18, +1)):
            kk = cand
            break
        m += 1
    if kk is None:
        return False, ("CERTIFICATE FAIL: no wheel k past the crossing with "
                       "a probable-prime 18th value in 4000 tries")
    certs, unproved = certify_run(kk, 18, +1, only=(18,))
    c18 = certs.get("18")
    if unproved or c18 is None or c18.get("proof") != "bls75-thm1":
        return False, (f"CERTIFICATE FAIL: 61*{kk}+1 (past the bound) was "
                       f"not proved by BLS75 Theorem 1: {c18 and c18.get('proof')}")
    if int(c18["N"]) != ref.value(kk, 18, +1) or int(c18["R"]) != 1:
        return False, ("CERTIFICATE FAIL: the Theorem 1 proof is not about "
                       "the value, or N - 1 was not factored completely")
    ok, why = certificate.verify(c18)
    if not ok:
        return False, f"CERTIFICATE FAIL: the proof does not re-verify: {why}"
    if certificate.verify(dict(c18, N=int(c18["N"]) + 2))[0]:
        return False, ("CERTIFICATE FAIL: the proof verified for a "
                       "neighbouring N")
    if certificate.verify({"proof": "deterministic-mr",
                           "N": int(c18["N"])})[0]:
        return False, ("CERTIFICATE FAIL: a deterministic-MR claim past the "
                       "bound was accepted as a proof")
    return True, (f"certificates ok: A084700 a({top})'s {top} values take the "
                  f"deterministic route and re-verify; past the crossing, "
                  f"61*k+1 = {ref.value(kk, 18, +1):.4g} at k = {kk:.4g} "
                  f"is proved by BLS75 Theorem 1 on N - 1 = 61*k factored "
                  f"completely ({len(c18['factors'])} prime factors, every "
                  f"one under the deterministic bound), re-verifies from "
                  f"scratch, and is refused for N + 2 and as a bare "
                  f"deterministic-MR claim")


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly, on every kernel
    and across the seams a real interrupt leaves: a period boundary, the
    (j, u) sub-period cursor, and the clipped period 0."""
    total = 0
    for lab, s, kw, j_at, span, cut in (
            ("one-level", +1, dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 20000, 7500),
            # the production first two levels, in the A084701 unit
            ("two-level", -1, dict(p1=P1, p2=P2, p3=None, q2=Q2,
                                   unit=UNIT[-1]),
             10 ** 15, 60, 23),
            ("three-level", +1, dict(p1=13, p2=17, p3=19, q2=128),
             9 * 10 ** 14, 400, 111)):
        eng = gpu.GpuEngine(14, s, **kw)
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

    # THE (j, u) SEAM: sweeping u in [0, c) then [c, R3) must give the same
    # set as sweeping the period whole -- and in PERIOD 0 with the clip,
    # which is where this campaign's first interrupt will land.  The wheel
    # is (13],(23],(37] so that ONE period (7.4e12 of line) is populated at
    # this density, and nu is forced below R3 so the period really is cut
    # into launches; at the default nu this wheel fits a period in one.
    # in k space, and in UNIT space -- the campaign's engine -- where a
    # period is 2310 times a k' period and the seam must still close
    for eng in (gpu.GpuEngine(14, +1, p1=13, p2=23, p3=37, q2=4096, nu=1024),
                gpu.GpuEngine(14, +1, p1=19, p2=23, p3=31, q2=256, nu=64,
                              unit=2310)):
        if eng.nu >= eng.R3:
            return False, "RESUME FAIL: the seam engine has no sub-period cursor"
        for j0, k_min in ((eng.j_of(9 * 10 ** 14), None), (0, K_START)):
            whole = sorted(eng.survivors_j(j0, j0 + 1, k_min=k_min))
            if not whole:
                return False, (f"RESUME FAIL: the (j, u) seam window is empty "
                               f"(unit {eng.unit})")
            for cut in (1, 3, eng.R3 - 1):
                part, stopped = [], 0
                for _, un, sv in eng.sweep(j0, j0 + 1, k_min=k_min):
                    part.extend(sv)
                    stopped = un
                    if un == 0 or un >= cut:
                        break
                if stopped:
                    for _, _, sv in eng.sweep(j0, j0 + 1, u_from=stopped,
                                              k_min=k_min):
                        part.extend(sv)
                if sorted(part) != whole:
                    return False, (f"RESUME FAIL: the (j, u) seam at u = "
                                   f"{stopped} (period {j0}, unit "
                                   f"{eng.unit}) loses or repeats values: "
                                   f"{len(part)} vs {len(whole)}")
            total += len(whole)
    return True, (f"resume ok: split sweep == unsplit sweep on all three "
                  f"kernels, across the (j, u) sub-period seam in k space "
                  f"and in unit space (2310), and inside the clipped period "
                  f"0 on both ({total} survivors across the seams)")


def _classification_drill():
    """The two-pass screen == the all-bases chain on real survivors, and the
    pool's chunked answer == the serial one."""
    # 200,000 periods of the (13],(23] wheel is 4.5e13 of line, which at
    # this density and sieve depth is about a thousand survivors
    eng = gpu.GpuEngine(14, +1, p1=13, p2=23, p3=None, q2=4096)
    j0 = eng.j_of(10 ** 13)
    surv = eng.survivors_j(j0, j0 + 200_000)
    if len(surv) < 3 * CHUNK:
        return False, (f"CLASSIFY FAIL: only {len(surv)} survivors -- the "
                       f"drill cannot span several chunks")
    two = [sprp_run(k, +1, 22) for k in surv]
    full = []
    for k in surv:
        r = 0
        while r < 22 and mr_is_prime(ref.rung(r + 1) * k + 1):
            r += 1
        full.append(r)
    if two != full:
        i = next(i for i in range(len(surv)) if two[i] != full[i])
        return False, (f"CLASSIFY FAIL: two-pass sprp gave run {two[i]} and "
                       f"the all-bases chain {full[i]} at k = {surv[i]}")
    with _pool_factory(2) as pool:
        parts = _submit(pool, +1, 22, surv)
        got = [r for ks, f in parts for r in f.result()]
    if got != full:
        return False, "CLASSIFY FAIL: the pool's chunked result differs"
    return True, (f"classification ok: two-pass sprp == all-bases chain on "
                  f"{len(surv)} real survivors (max run {max(full)}), and "
                  f"{len(parts)} pool chunks reassemble to the serial answer")


def _stop_on_discovery_drill():
    """--stop-on-discovery stops on a NEW find, not on a loaded one.

    The counter is cumulative and restored from the checkpoint; the run
    latches the stop where the find is confirmed instead of reading the
    counter.  Drilled on the RESUMED case, at non-zero prior counts.
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


def _other_family_cursor_drill(sign):
    """The OTHER family's policy, put in front of every key it declares."""
    import tempfile
    other = -int(sign)
    tmp = tempfile.mkdtemp(prefix="pladder-cursor-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[other].at(path)
    seen = []
    try:
        for key in pol.readable():
            checkpoint.save(path, {"key": key, "j": 7, "u": 0, "k": 11})
            st, kind = pol.load()
            if not st or kind is None:
                return False, (f"CURSOR FAIL: sign {other:+d} will not read "
                               f"a checkpoint keyed {key}")
            pol.refuse_mismatch()
            seen.append(kind)
        checkpoint.save(path, {"key": "not-a-real-key", "j": 7, "k": 11})
        st, _k = pol.load()
        if st:
            return False, f"CURSOR FAIL: sign {other:+d} read a foreign key"
        try:
            pol.refuse_mismatch()
            return False, (f"CURSOR FAIL: sign {other:+d} did not refuse a "
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
    return True, (f"cursor policy (sign {other:+d}) ok: all {len(seen)} "
                  f"declared key(s) pass BOTH readers with the right "
                  f"classification ({', '.join(seen)}); an unknown key "
                  f"refuses")


def _adopt_drill():
    """A v2 cursor is RE-DENOMINATED onto the v3 period, floored, and the
    overlap is a cross-check rather than a census.

    Drilled on the shape of the live cursor: the A084700 checkpoint that
    stopped at the old ceiling, keyed v2, counting periods of 6.15e17.
    The v3 campaign must read it as adopted, floor its k onto the 3.26e19
    period (never round up), drop the old period's in-flight values, keep
    the frontier and the counters, report the ADOPTED k as swept (never
    less), refuse to count or narrate anything in the overlap, halt on a
    discovery-grade run there, and write itself back under its own key.
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="pladder-adopt-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[+1].at(path)

    class _A:
        pass
    a = _A()
    for k, v in dict(sign=+1, fresh=False, to=None, stop_on_discovery=False,
                     heartbeat=30.0, gpu_yield_ms=0.0, status=False,
                     selftest=False, workers=1,
                     worker_ramp=WORKER_RAMP_S).items():
        setattr(a, k, v)
    j_old = 88434
    k_old = j_old * OLD_W
    found = {"14": 24581646307811670, "15": 1183192161007235610,
             "16": 161515890673488267840, "17": 2446970377116913184460}
    try:
        checkpoint.save(path, {
            "key": old_key(+1, "v2"), "engine": "v2", "sign": 1,
            "j": j_old, "u": 0, "W": OLD_W, "k": k_old, "k_start": K_START,
            "pending": [[k_old + 2310, 9], [k_old + 4620, 17]],
            "found": found, "census": {"8": 9078, "17": 1},
            "passed": ["a(17) P90"], "elapsed": 15848.7,
            "discoveries": 4, "near": 8, "survivors": 32304365})
        c = Campaign(a, ckpt=path, cursor=pol)
        W = int(c.eng.W)
        if c.eng.unit != 2310 or W == OLD_W:
            return False, "ADOPT FAIL: the campaign engine is not the unit wheel"
        if c.frontier() != 17 or c.filter_n() != 18 or c.eng.n != 18:
            return False, (f"ADOPT FAIL: frontier {c.frontier()}, filter "
                           f"{c.filter_n()} -- the finds did not carry over")
        if c.j != k_old // W or c.u != 0 or c.pending:
            return False, (f"ADOPT FAIL: re-denominated to (j, u) = ({c.j}, "
                           f"{c.u}) with pending {c.pending}; expected "
                           f"({k_old // W}, 0) and nothing pending")
        if not c.j * W <= k_old < (c.j + 1) * W:
            return False, "ADOPT FAIL: the floored period does not contain k"
        if c.census_floor != k_old or c.swept_k() != k_old:
            return False, (f"ADOPT FAIL: the adopted claim {k_old:,} is not "
                           f"what is reported swept ({c.swept_k():,})")
        if (c.discoveries, c.near, c.survivors, c.census.get(17)) != \
                (4, 8, 32304365, 1) or c.passed != ["a(17) P90"]:
            return False, "ADOPT FAIL: counters or passed rungs did not carry"
        if "RE-SWEEPING" not in c.status_line():
            return False, "ADOPT FAIL: the status line does not say it is re-sweeping"
        # the overlap: not counted, not narrated, and a discovery halts
        if c.handle(k_old - 2310, 12) is not False or c.census.get(12):
            return False, "ADOPT FAIL: a census run in the overlap was counted"
        try:
            c.handle(k_old - 2310, 18)
            return False, "ADOPT FAIL: a discovery-grade run in the overlap did not halt"
        except SystemExit:
            pass
        if c.handle(k_old + 2310, 12) is not False or c.census.get(12) != 1:
            return False, "ADOPT FAIL: a census run above the overlap was not counted"
        c.save()
        d = Campaign(a, ckpt=path, cursor=pol)
        st, kind = pol.load()
        if kind != "own" or (d.j, d.u, d.census_floor, d.swept_k()) != \
                (c.j, 0, k_old, k_old) or d._adopt_k is not None:
            return False, (f"ADOPT FAIL: after the save the cursor reads as "
                           f"{kind} with (j, u, floor) = ({d.j}, {d.u}, "
                           f"{d.census_floor})")
        # and once the first v3 period closes the boundary passes the
        # floor and the claim moves with the period again
        d.boundary = d.j + 1
        if d.swept_k() != (d.j + 1) * W or "RE-SWEEPING" in d.status_line():
            return False, "ADOPT FAIL: the claim did not follow the boundary past the floor"
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
    return True, (f"adopt ok: the v2 cursor (period {j_old} of {OLD_W:,}, "
                  f"swept to {k_old:.6g}) re-denominates to period "
                  f"{k_old // W} of {W:,} with u = 0 and nothing pending, "
                  f"keeps a(14)..a(17) and every counter, reports the "
                  f"adopted k as swept, neither counts nor narrates the "
                  f"{k_old - (k_old // W) * W:.3g} of overlap and halts on "
                  f"a discovery there, saves under its own key, and lets "
                  f"the claim follow the boundary once the period closes")


def _two_families_stay_apart():
    """The two campaigns must not be able to read each other's cursor."""
    if config_key(+1) == config_key(-1):
        return False, "FAMILY FAIL: both signs share a config key"
    if ckpt_path(+1) == ckpt_path(-1):
        return False, "FAMILY FAIL: both signs share a checkpoint file"
    if ledger_path(+1) == ledger_path(-1):
        return False, "FAMILY FAIL: both signs share a ledger"
    for s, other in ((+1, -1), (-1, +1)):
        if config_key(other) in _POLICIES[s].readable():
            return False, (f"FAMILY FAIL: the s={s:+d} policy accepts the "
                           f"s={other:+d} key")
    return True, ("families stay apart: distinct config keys, checkpoint "
                  "files and ledgers, and neither policy will read the "
                  "other's cursor")


def _campaign_wiring_drill():
    """Build a campaign and exercise everything the loop touches, without
    sweeping a single candidate: construction from nothing at period 0,
    the status line, census and NEAR/CENSUS classification, the cached
    rung ladder, the drain of a fake in-flight launch, a save/load round
    trip, and the interrupt snapshot."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="pladder-drill-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[+1].at(path)

    class _A:
        pass
    a = _A()
    for k, v in dict(sign=+1, fresh=False, to=None, stop_on_discovery=False,
                     heartbeat=30.0, gpu_yield_ms=0.0, status=False,
                     selftest=False, workers=1,
                     worker_ramp=WORKER_RAMP_S).items():
        setattr(a, k, v)
    try:
        c = Campaign(a, ckpt=path, cursor=pol)
        if c.frontier() != 13 or c.filter_n() != 14:
            return False, (f"WIRING FAIL: frontier {c.frontier()}, filter "
                           f"{c.filter_n()} -- expected 13 and 14")
        if (c.j, c.u, c.swept_k(), c.k_min()) != (0, 0, 0, K_START):
            return False, (f"WIRING FAIL: a fresh campaign starts at "
                           f"(j, u) = ({c.j}, {c.u}), swept {c.swept_k()}, "
                           f"clip {c.k_min()} -- expected period 0 clipped "
                           f"at {K_START}")
        if c.eng.n != 14 or c.eng.s != +1 or c.eng.unit != UNIT[+1]:
            return False, "WIRING FAIL: the engine is not at the campaign filter"
        line = c.status_line()
        for want in ("swept to", "A084700", "census", "period 0"):
            if want not in line:
                return False, f"WIRING FAIL: status line lacks {want!r}"
        if c.handle(K_START + 1, 9) is not False or c.census.get(9) != 1:
            return False, "WIRING FAIL: a census run was not counted"
        if c.handle(K_START + 3, 7) is not False or 7 in c.census:
            return False, "WIRING FAIL: a run under the floor was counted"
        # the drain: a fake in-flight launch's survivors land in `pending`
        # (only those at or above the census floor) and the WORK cursor
        # follows it, but not past it
        inflight = collections.deque()
        inflight.append(((0, 52), [([5, 6, 7], _Done([3, 8, 12]))]))
        inflight.append(((0, 104), [([9], _Done([0]))]))
        c._drain(inflight, block=True)
        if c.pending != [(6, 8), (7, 12)] or c.survivors != 4:
            return False, (f"WIRING FAIL: the drain left pending "
                           f"{c.pending} and {c.survivors} survivors")
        if (c.j, c.u) != (0, 104):
            return False, f"WIRING FAIL: the work cursor is ({c.j}, {c.u})"
        nxt = c.next_rung(c.swept_k())
        if not nxt or not nxt[0].startswith("a(14)"):
            return False, f"WIRING FAIL: the ladder aims at {nxt}"
        c.check_rungs(c.swept_k())
        builds = c._lad.builds
        for _ in range(25):
            c.ladder()
            c.next_rung(c.swept_k())
            c.check_rungs(c.swept_k())
        if c._lad.builds != builds:
            return False, (f"WIRING FAIL: 75 ladder reads at a standing "
                           f"frontier caused {c._lad.builds - builds} "
                           f"rebuild(s)")
        # THE POOL IS SIZED FROM A MEASUREMENT AT THIS FILTER: the
        # calibration sweeps real launches of period 0 at n = 14, counts
        # survivors, times a classified sample, and the pool that comes up
        # is ceil(need x margin) real interpreters, ramped
        c.args.workers = None
        before = (c.j, c.u, c.survivors, list(c.pending), dict(c.census))
        m = c.calibrate()
        if (m["launches"] < 1 or m["survivors"] < 1 or m["rate"] <= 0
                or not 1e-6 < m["cost"] < 1e-3 or m["need"] <= 0):
            return False, f"WIRING FAIL: the sizing measurement is {m}"
        if (c.j, c.u, c.survivors, list(c.pending), dict(c.census)) != before:
            return False, ("WIRING FAIL: the calibration moved the campaign "
                           f"from {before} to ({c.j}, {c.u}, {c.survivors}, "
                           f"{c.pending}, {c.census})")
        w = c.size_pool()
        ms = c._sizing                      # the measurement IT took
        if (ms is None or w != max(1, math.ceil(ms["need"] * POOL_MARGIN))
                or c.workers != w or c.pool is None
                or abs(ms["need"] - m["need"]) > 0.5 * max(m["need"], 1e-9)):
            return False, (f"WIRING FAIL: size_pool gave {w} workers from "
                           f"{ms} against the drill's own {m['need']:.3f} "
                           f"core-s/s, pool {c.pool}")
        pool_obj = c.pool
        w2 = c.size_pool()
        if not (c.pool is pool_obj or w2 > w or 2 * w2 <= w):
            return False, (f"WIRING FAIL: re-sizing from {w} to {w2} workers "
                           f"rebuilt the pool inside the noise band")
        w = c.workers
        # BACK-PRESSURE: launches whose futures are not done stay in flight,
        # and past BACKLOG_LAUNCHES the loop waits on the oldest, timing it

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
            inflight.append(((0, 200 + i), [([11 + i], _Slow([3]))]))
        c._drain(inflight, block=False)
        if len(inflight) != BACKLOG_LAUNCHES + 5:
            return False, "WIRING FAIL: the drain took launches not yet classified"
        c._backpressure(inflight)
        if (len(inflight) != BACKLOG_LAUNCHES or c._hostwait <= 0
                or not c._hostbound_logged or c.survivors != 9
                or (c.j, c.u) != (0, 204)):
            return False, (f"WIRING FAIL: back-pressure left {len(inflight)} "
                           f"in flight, waited {c._hostwait:.3g} s, cursor "
                           f"({c.j}, {c.u})")
        c._hostwait, c._hostbound_logged = 0.0, False
        line = c.status_line()
        if f"pool {w}" not in line or "HOST-BOUND" in line:
            return False, f"WIRING FAIL: status line pool fragment: {line}"
        if "P(a(14) under the claim) = 0%" not in line or "next a(14)" not in line:
            return False, (f"WIRING FAIL: the status line reads the rungs "
                           f"off progress, not coverage: {line}")
        c.pool.shutdown(wait=True, cancel_futures=True)
        c.pool, c.workers, c.args.workers = None, None, 1
        c.found["14"] = int(ref.KNOWN[+1][13]) + 2310      # a find, unverified
        if c.frontier() != 14 or c.filter_n() != 15:
            return False, "WIRING FAIL: a find did not move the frontier"
        aim = c.next_rung(c.swept_k())
        if c._lad.builds != builds + 1:
            return False, ("WIRING FAIL: the frontier moved and the ladder "
                           "was served from cache")
        if not aim or not aim[0].startswith(("a(15)", "engine ceiling")):
            return False, (f"WIRING FAIL: after finding a(14) the campaign "
                           f"aims at {aim} -- a retired rung")
        c.mark_boundary()
        c.follow_frontier()
        if c.eng.n != 15 or int(c.eng.W) != c._snapshot["W"]:
            return False, "WIRING FAIL: follow_frontier did not move the filter"
        c.found.pop("14")
        c._lad.invalidate()
        # round trip, pending included
        c.save()
        d = Campaign(a, ckpt=path, cursor=pol)
        if (d.j, d.u, d.pending, d.census, d.survivors) != (
                c.j, c.u, c.pending, c.census, c.survivors):
            return False, (f"WIRING FAIL: reload gave (j,u)=({d.j},{d.u}) "
                           f"pending={d.pending} census={d.census}, wrote "
                           f"({c.j},{c.u}) {c.pending} {c.census}")
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
    return True, ("campaign wiring ok: a campaign builds from nothing at "
                  "period 0 clipped at K_START with the engine at n = 14, "
                  "its status line and rung ladder aim at a(14), 75 ladder "
                  "reads at a standing frontier cost 0 model rebuilds while "
                  "a find costs exactly 1 and moves the aim and the filter, "
                  "the drain keeps the work cursor behind the classified "
                  "launches and floors the census, and the checkpoint "
                  "round trips through both the normal save and the "
                  "interrupt snapshot, pending included")


def selftest(sign=+1):
    t0 = time.time()
    rows = []
    for g in (ref.GATES + cpu.GATES + gpu.GATES + model.GATES
              + certificate.GATES):
        rows.append(g())
    rows.append(drills.event_kind_drill(
        lambda c: event_kind(*c), _event_cases()))
    for d in drills.standard(pool_factory=_pool_factory,
                             cursor=_POLICIES[sign]):
        rows.append(d)
    rows.append(_other_family_cursor_drill(sign))
    for d in (_ceiling_drill, _canary_hunt, _protocol_drill,
              _certificate_drill, _resume_drill,
              _classification_drill, _stop_on_discovery_drill,
              _two_families_stay_apart, _campaign_wiring_drill,
              _adopt_drill):
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

def _status(sign):
    st, kind = _POLICIES[sign].load(warn=lambda m: log("STAGE", m))
    if not st:
        log("STATUS", f"no checkpoint for {config_key(sign)} yet")
        return 0
    cen = {int(r): int(c) for r, c in st.get("census", {}).items()}
    front = max(ref.KNOWN[sign])
    for n in st.get("found", {}):
        front = max(front, int(n))
    # an adopted cursor's indices are in the OLD period; say so rather
    # than print a number the campaign will not use
    cursor = (f"work cursor period {int(st['j'])} u = {int(st.get('u', 0))}"
              + (f" (in periods of W = {int(st.get('W', 0)):,}, the stored "
                 f"key's; the campaign re-denominates on start)"
                 if kind == "adopted" else ""))
    log("STATUS", "  ".join([
        f"{ref.FAMILIES[sign]['oeis']}",
        f"swept to k = {int(st['k']):,}",
        cursor,
        f"filter n = {front + 1}",
        census_str(cen, CENSUS_FLOOR, front),
        f"finds {st.get('discoveries', 0)}",
        f"near {st.get('near', 0)}",
        f"survivors {int(st.get('survivors', 0)):,}",
        f"elapsed {float(st.get('elapsed', 0)) / 3600:.2f} h",
        f"saved {st.get('saved', '?')}"]))
    for n, k in sorted(st.get("found", {}).items(), key=lambda x: int(x[0])):
        log("STATUS", f"  found: a({n}) = {int(k):,}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sign", type=int, default=+1, choices=(1, -1),
                    help="+1 = A084700, prime(i)*k + 1 (default); "
                         "-1 = A084701, prime(i)*k - 1")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this depth on the k line (default: the "
                         "engine ceiling -- the family's primality-proof "
                         "validity bound, 3.3e24 for A084700)")
    ap.add_argument("--stop-on-discovery", action="store_true",
                    help="checkpoint and exit once THIS RUN confirms a find "
                         "(finds already in the checkpoint do not count)")
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (default 30)")
    ap.add_argument("--workers", type=int, default=None,
                    help="classification pool size. By default it is "
                         "MEASURED at the campaign's own filter (the next "
                         "launches are swept and timed, their survivors "
                         "counted, a sample classified) and re-measured at "
                         "every filter promotion: ceil(core-seconds per "
                         "second x 2). Give a number to override it; 1 "
                         "classifies in the main thread and idles the device "
                         "while it does (a throttle, not a speed)")
    ap.add_argument("--worker-ramp", type=float, default=WORKER_RAMP_S,
                    help="seconds between worker starts (default "
                         f"{WORKER_RAMP_S})")
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0,
                    help="idle the device this long after every launch. "
                         "1 ms against a ~10 ms launch costs about 9%% of "
                         "the rate and leaves the desktop noticeably freer")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 2 --workers 1 --worker-ramp "
                         "1.0 (about a sixth of the rate, one fewer process)")
    ap.add_argument("--fresh", action="store_true",
                    help="discard an existing cursor deliberately")
    args = ap.parse_args(argv)
    if args.gentle:
        args.gpu_yield_ms = args.gpu_yield_ms or 2.0
        args.workers = 1
        args.worker_ramp = max(args.worker_ramp, 1.0)
    if args.selftest:
        return selftest(args.sign)
    if args.status:
        return _status(args.sign)
    if args.to:
        args.to = int(args.to)
    _POLICIES[args.sign].refuse_mismatch(
        fresh=args.fresh,
        describe=lambda st: (f"period {st.get('j')}, u = {st.get('u')}, "
                             f"swept to k = {st.get('k')}"))
    if args.fresh:
        import os
        for p in (ckpt_path(args.sign), ckpt_path(args.sign) + ".bak"):
            if os.path.exists(p):
                os.remove(p)
    return Campaign(args).run()


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
