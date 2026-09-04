"""The campaign for the linear ladders -- least k with m*k + s prime for
every multiplier m of a family at index n.

    python launch.py --selftest            the full gate battery (must end ALL GREEN)
    python launch.py                       the hunt: indefinite, resumable (A088250)
    python launch.py --family A125838      another family (one campaign per family)
    python launch.py --to 1e22             stop at a chosen depth on the k line
    python launch.py --status              read the checkpoint and say where it is

SEVEN FAMILIES, ONE ENGINE, ONE CAMPAIGN AT A TIME.  `--family` names the
OEIS entry (lladder_reference.FAMILIES; A202778/A202779 are accepted as
aliases of A088250/A088651, whose exact-run versions they are).  They are
the same mathematics with the multiplier list and the sign changed, so
they share every file here -- but they are different sequences with
different frontiers, so each carries its OWN checkpoint under its own
config key and a campaign hunts one of them.

THE OPENINGS (CLAUDE.md 5g, step 1 -- the test plan for every default
below).  Each family opens at the filter after its published frontier and
promotes itself one filter per find; the unit is fixed per family at its
opening and stays (a forced prime stays forced as n grows), so the wheel
period W = 1.92e21 never moves inside a campaign.  Up to each family's
ceiling the campaign can be at:

    A088250  n = 15 (unit 30030) -> 16 -> 17 -> 18      ceiling 3.3e24 (+1)
    A173750  n = 16 (unit 30030) -> 17 -> 18            ceiling 3.3e24 (+1)
    A164325  n = 16 (unit 30030) -> 17 -> 18            ceiling 3.3e24 (+1)
    A125838  n = 15 (unit 30030) -> 16 -> 17 -> 18      ceiling 2.2e23 (-1, the crossing)
    A125839  n = 16 (unit 30030) -> 17 -> 18 -> 19      ceiling 2.1e23 (-1)
    A164326  n = 15 (unit 30030) -> 16 -> 17            ceiling 1.1e23 (-1)
    A088651  n = 16 (unit 510510) -> 17                 ceiling 2.1e23 (-1)

Every one of those (family, filter) pairs was priced by calling the
engine on a chosen window (OPTIMIZATION_LOG.md): the line rate, the
survivors per unit of line and the host need at each, and the compaction
constant re-swept at each.  The pool is not one of the priced constants:
it is MEASURED at the campaign's own configuration at start and at every
promotion (size_pool).

WHAT IS OPEN, AND WHY IT IS WORTH A SWEEP.  None of the seven published
frontiers had moved since Giovanni Resta's 2017 extensions (A088651's
a(15) is Jens Kruse Andersen's, 2008), and none carries a bound of any
kind at any open n.  Every published frontier sits inside the FIRST
PERIOD of this engine's wheel.  Four campaigns have run (2026-09-03,
RESULTS.md): A088250's found a(15)..a(17) and swept empty to the ceiling
at n = 18; A125838's found a(15)..a(18) and A125839's a(16)..a(18), each
swept empty to the ceiling at n = 19; A173750's found a(16), a(17) and
a(18) = a(19) on one k and swept empty to the ceiling at n = 20.  Those
checkpoints sit at their ceilings, so a resume of any of them stops at
once; `--fresh` would re-sweep the whole line.

THE CLAIM'S FLOOR IS FREE.  a() is non-decreasing (the conditions nest), so
the next term is at least the last one and nothing below it has to be swept
at all.  The campaign still starts far below: at K_START = 1e6, inside
period 0, which the engine sweeps whole and clips at K_START (lladder_gpu,
"a window may start inside period zero").  Below K_START the least-claim
rests on monotonicity -- A088250's a(14) is 1.1e19 -- and above it on our
own coverage.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine's enforced ceiling -- the PRIMALITY-PROOF validity bound of the
family, k_ceil(n, F) in lladder_search -- which is the last rung.  For the
+1 families that is k < 3.317e24, the deterministic Miller-Rabin bound on
k itself: below the PROOF CROSSING k_proof(n, F) (2.2e23 at n = 15) every
classification is a deterministic proof, above it the same seven-base
chain is a strong probable-prime test and a DISCOVERY is proved by a BLS75
Theorem 1 certificate on N - 1 = m*k, k factored once per find
(certify_run); the ceiling is where a factor of k could itself pass the
bound and need a subproof.  The -1 families' structure is on N + 1 and
huntlib has no N+1 test, so their ceiling is the crossing.  `--to` and
`--stop-on-discovery` are the only stops and both are opt-in.  Progress is
read off RUNGS taken from the odds model's quantiles, logged as they are
passed and shown with an ETA in every [STATUS].  A rung retires with its
term: the ladder is derived from the LIVE frontier and cached on it
(huntlib.rungs.LiveLadder), never recomputed in the loop.

THE TAXONOMY, mapped to this problem (CONVENTIONS.md "the discovery
protocol").  A survivor is a k with a run length r:

  DISCOVERY  r > frontier: it settles a(frontier+1) ... a(r) at once, each
             logged once, all evidenced under the FIRST value they belong
             to.  Verified three ways plus a factor witness for the
             composite that stops the run, and a re-verified primality
             certificate for every value (deterministic Miller-Rabin
             under the bound, BLS75 Theorem 1 past it).  The evidence file
             also records what the find settles in the DERIVED entries:
             A202778(r) = k for A088250 (the exact-run version, at the
             last index settled) and A071576(n) = k/2 for every settled
             n >= 3; A202779(r) = k for A088651.
  NEAR       r == frontier: a k that reaches the settled frontier and no
             further -- ONE condition short of the open term.  One line
             with its campaign ordinal, verified by the cheap legs as an
             engine health check, never evidenced.
  CENSUS     CENSUS_FLOOR <= r < frontier: counted in [STATUS], never
             narrated.
  None       r < CENSUS_FLOOR: noise, not counted.

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
three-level wheel emits a period's candidates in (t, s, u) order, so the k
line is contiguous only at the end of a whole period -- 1.92e21 of k, a
minute of device at A088250's opening filter and five seconds at n = 17.
COVERAGE (`boundary`, the k below which every value is swept) advances one
period at a time and is the only thing a least-claim rests on; WORK
(`j`, `u`) advances every launch.  Values classified mid-period are held IN
THE CHECKPOINT (`pending`) and narrated in k order when the period closes,
so a discovery is only announced once it is known to be the least.  A find
costs at most one period of over-sweep (a minute at the opening filters,
seconds from n = 17).  Because periods can close every few seconds at the
deeper filters, the period-close save and the period-close log line are
RATE-LIMITED (CKPT_MIN_S, PERIOD_LOG_S): a save every few seconds is tens
of thousands of chances per campaign for a scanner's handle to land in
the rename window (CONVENTIONS.md "Writing a cursor"), and a line every
few seconds is a log nobody can read.  The boundary snapshot is still
taken at every period close, so an interrupt writes the latest one.

LOAD (CONVENTIONS.md "Sizing a hunt so it leaves the machine usable").
Measured at every opening configuration (OPTIMIZATION_LOG.md v2), paired
and interleaved:

    A088250 n = 15   2.8e19 k/s   2.1e-15 survivors per unit line  5.9e4/s  0.85 core-s/s
    A125838 n = 15   7.6e18 k/s   1.7e-14                          1.3e5/s  1.9 core-s/s
    A088250 n = 17   3.7e20 k/s   2.5e-17                          9.2e3/s  0.13 core-s/s

so the host need runs from about two cores at the -1 openings to a
fraction of one at the live filters, and no constant serves them all: the
pool is SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER, again every
time the filter moves (Campaign.size_pool: the next launches are swept and
timed, their survivors counted, a sample of them classified, and
ceil(need x POOL_MARGIN) workers ramped one at a time at below-normal
priority, huntlib.pool).  The device may run at most BACKLOG_LAUNCHES ahead
of the pool, so a pool that binds throttles the device VISIBLY -- the
[STATUS] line says HOST-BOUND and by how much -- instead of silently.
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

import lladder_gpu as gpu                                       # noqa: E402
import lladder_model as model                                   # noqa: E402
import lladder_reference as ref                                 # noqa: E402
import lladder_search as cpu                                    # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")

# THE WHEEL, IN UNIT SPACE (OPTIMIZATION_LOG.md).  The forcing lemma makes
# every candidate a multiple of 30030 at every family's opening filter
# (510510 for A088651), so the device sweeps k' = k / unit: 2..13 leave the
# wheel and 29, 31, 37, 53 and 59 come in under the same u32 / 2^63 bounds
# that stop a k-space wheel at 47.  Levels (..37], (37, 47], (47, 59]: a
# period of 1.92e21 of k for every family.  v1 ran (..31], (31, 41],
# (41, 53] (a period of 3.26e19) and had declined this wheel on a paired
# measurement that read 1.00x at n = 17 and 0.83x at A125838's opening;
# v2 found both numbers were the configuration and not the wheel -- a
# group budget that stopped its first triple forming, and a tail-queue cap
# that sent 60% of a launch through the in-block fallback -- and re-measured
# it at 1.27x / 1.50x / 1.20x / 1.32x at c = 15 / 16 / 17 / 18 and within 5%
# at c = 14 (OPTIMIZATION_LOG.md v2).  The unit is fixed PER FAMILY at the
# filter its campaign opens in and stays: at a higher filter it is still
# admissible (lladder_search.assert_unit), merely not maximal, and a fixed
# unit is what keeps W -- the cursor's denomination -- constant across
# follow_frontier.
P1 = 37                           # first-level wheel: primes to 37 not in the unit
P2 = 47                           # second-level wheel: primes (37, 47]
P3 = 59                           # third-level wheel:  primes (47, 59]
Q2 = cpu.Q2_DEFAULT               # sieve depth


def open_n(fam):
    """The filter a FRESH campaign of this family opens at: the index after
    the published frontier."""
    return max(ref.KNOWN[ref.family(fam)]) + 1


UNIT = {fam: cpu.forced_unit(open_n(fam), fam) for fam in ref.FAMILIES}

# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a period.  On
# the v2 wheel a launch is ONE third-level residue below c = 17 -- 7.3e9
# candidates and 40 ms at A088250's n = 15, 2.05e10 and 170 ms at A125838's
# opening -- and two from c = 17 (1.5e9, 4 ms), so 32 launches is 1.3 s at
# n = 15, 5.5 s at the -1 openings and 0.13 s at n = 17: what an interrupt
# costs to redo, and the denominator that prices --gpu-yield-ms.  A period
# is 1,672 launches at n = 15 and 756 at n = 17, so the mid-period save
# fires throughout, rate-limited by CKPT_MIN_S.
CKPT_LAUNCHES = 32
K_START = 10 ** 6                 # the clip inside period 0; > k_floor(Q2)
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
ENGINE_VERSION = "v2"
# THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER
# (CLAUDE.md 5f and 5g; CONVENTIONS.md "Sizing a hunt"), not from a
# constant: `Campaign.size_pool` sweeps the launches the loop is about to
# run, times them, counts their survivors, times sprp_run on a sample, and
# takes ceil(core-seconds per second x POOL_MARGIN) workers -- at start,
# and again at every filter promotion.  WORKERS_DEFAULT survives only as
# the fallback for a drill with no device, and `--workers` still overrides.
WORKERS_DEFAULT = 2
POOL_MARGIN = 2.0                 # workers = ceil(core-s per s x this):
#                                   CONVENTIONS.md step 2 says two to three
#                                   times the need; the pool's own overhead
#                                   (pickling, IPC) made 13 us/survivor into
#                                   17 in the pool in prime-ladders
CAL_MIN_SURVIVORS = 500           # the sample the sizing is measured on ...
CAL_MIN_S = 1.0                   # ... over at least this much device time
CAL_MAX_S = 4.0                   # and at most this much
CAL_SAMPLE = 2000                 # survivors timed through sprp_run
# BACK-PRESSURE: the device may run at most this many launches ahead of
# the pool.  Past it the loop waits for the oldest launch, so a pool that
# binds throttles the device VISIBLY (the wait is timed into the [STATUS]
# line and the rate printed is the pipeline's) instead of growing a
# backlog in memory.
BACKLOG_LAUNCHES = 64
# A checkpoint is rewritten at every mid-period boundary and every period
# close, but not so often that the writing is a cost or a lock exposure:
# never more often than CKPT_MIN_S, and each save stays under
# CKPT_COST_FRACTION of wall clock.  A period close that wrote evidence
# saves at once regardless.
CKPT_MIN_S = 2.0
CKPT_COST_FRACTION = 0.02
# A "period complete" line no more often than this (a period is 0.1 s at
# n = 17); the line then says how many periods closed since the last one.
PERIOD_LOG_S = 60.0
WORKER_RAMP_S = _pool.RAMP_S
CHUNK = 256                       # survivors per pool task


def config_key(fam, engine=None):
    fam = ref.family(fam)
    return (f"{fam.lower()}-{engine or ENGINE_VERSION}-u{UNIT[fam]}"
            f"-p1{P1}-p2{P2}-p3{P3}-q2{Q2}-seg{CKPT_LAUNCHES}")


def ckpt_path(fam):
    return str(HERE / f"campaign_checkpoint_{ref.family(fam).lower()}.json")


def ledger_path(fam):
    return str(HERE / "evidence" / f"{ref.family(fam).lower()}_discoveries.json")


# EVERY reader of the checkpoint goes through this object and none of them
# takes a key list of its own.  There are three readers -- the campaign's
# load, --status, and the refusal check in main() -- and passing the same
# list to three places is a thing you can forget at one of them; it cost
# this repo two campaign starts before the policy existed (CONVENTIONS.md
# "Reading an existing cursor").  This project has no predecessor engine,
# so every policy declares its own key and nothing else; the cursor drills
# in --selftest put every reader in front of it and refuse a foreign key.
_POLICIES = {fam: checkpoint.CursorPolicy(ckpt_path(fam), config_key(fam),
                                          accept=(), adopt=())
             for fam in ref.FAMILIES}


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


def verify(k, run, fam):
    """The three independent confirmations plus the bounding witness.

    1. huntlib's Miller-Rabin, which is a PROOF below the proof crossing
       k_proof(n, F) (G10) and a seven-base strong probable-prime chain
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
    fam = ref.family(fam)
    lo = ref.rungs_from(fam)
    legs = {"mr_chain": all(mr_is_prime(ref.value(fam, k, i))
                            for i in range(lo, run + 1)),
            "sympy_bpsw": ref.run_length(fam, k, cap=run + 1) == run,
            "resieve_other_wheel": cpu.CpuEngine(run, fam, q2=4096).survives(k)}
    stop = ref.value(fam, k, run + 1)
    legs["stopper_composite"] = not mr_is_prime(stop)
    ok = all(legs.values())
    wit = factor_witness(stop) if legs["stopper_composite"] else None
    return ok, legs, {"i": run + 1, "value": stop, "factor": wit}


def certify_run(k, run, fam, only=None):
    """A checkable primality certificate for every value m*k + s of the
    run: ({str(i): proof}, [the i left UNPROVED]).

    Below the deterministic bound huntlib.certificate.prove answers with
    the seven-base test, which IS the proof there.  Above it, for the +1
    families, N - 1 = m*k with m the multiplier: k is factored ONCE --
    trial division, a bounded rho, bounded ECM, then sympy's factorint on
    whatever is left, which for a k under the 3.317e24 ceiling is a
    25-digit number and seconds at most -- the multiplier's own small
    factors are folded in (m is composite in general here: 15 = 3 * 5),
    and every value gets BLS75 Theorem 1 on that one factorization.  Every
    prime factor of k is under the bound because k is, so the certificate
    is one level deep.  A value the shared factorization cannot prove
    falls back to certificate.prove's own bounded search, and for the -1
    families only that fallback runs: the structure there is on N + 1, the
    ceiling keeps those families under the bound, and the answer stays
    honest if it is ever asked.

    Every proof is RE-VERIFIED from scratch before it is returned.  A
    certificate that was not checked is a claim, not a certificate.
    """
    from sympy import factorint
    fam = ref.family(fam)
    k, s = int(k), ref.sign(fam)
    fac, R = certificate.factor_partial(k, ecm_curves=200)
    if R > 1:
        for p, e in factorint(R).items():
            fac[int(p)] = fac.get(int(p), 0) + int(e)
    certs, unproved = {}, []
    lo = ref.rungs_from(fam)
    for i in (range(lo, run + 1) if only is None else only):
        N = ref.value(fam, k, i)
        proof = None
        if s > 0:
            facN = dict(fac)
            for p, e in factorint(ref.rung(fam, i)).items():
                facN[int(p)] = facN.get(int(p), 0) + int(e)
            proof = certificate.prove(N, fac=facN)
        if proof is None:
            proof = certificate.prove(N)
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
        certs[str(i)] = proof
        if proof is None:
            unproved.append(int(i))
    return certs, unproved


def also_settles(fam, k, run, settles):
    """What a find settles in the DERIVED entries (lladder_reference
    FAMILIES[fam]['also']), as a list of records for the evidence file.

    exact  A202778 / A202779: least k with the run EXACTLY n.  The find has
           run exactly `run`, and it is the least k with run >= run, so it
           is the least with run exactly `run`: the exact-run entry is
           settled at `run` and only there -- at a rider index (settled
           here with a longer run) the exact-run entry stays OPEN, its own
           term being some larger k.
    half   A071576(n) = A088250(n) / 2 for n >= 3 (k even from n = 2).
    """
    fam = ref.family(fam)
    out = []
    for seq, kind in ref.FAMILIES[fam]["also"]:
        if kind == "exact":
            out.append({"sequence": seq, "n": int(run), "value": int(k),
                        "claim": f"least k with the run exactly {run}",
                        "open_at": [int(n) for n in settles if n != run]})
        elif kind == "half" and k % 2 == 0:
            for n in settles:
                if n >= 3:
                    out.append({"sequence": seq, "n": int(n), "value": k // 2,
                                "claim": f"{fam}({n}) / 2"})
    return out


# ----------------------------- classification -------------------------------

def sprp_run(k, fam, cap, floor=CENSUS_FLOOR):
    """Run length of k, screened with a base-2 strong test and CONFIRMED
    with the deterministic chain wherever the answer matters.

    A failed base-2 test is a PROOF of compositeness (huntlib.primes), so
    the first pass can only overstate a run, never understate it.  Runs
    that come out below the census floor are never looked at again, so an
    overstatement there costs nothing; a run at or above it is recomputed
    with all seven bases, which is the deterministic answer below the
    proof crossing and a strong probable-prime answer above it (a
    DISCOVERY there is proved by certificate; the census is a count).
    """
    fam = ref.family(fam)
    s = ref.sign(fam)
    lo = ref.rungs_from(fam) - 1
    r = lo
    while r < cap and sprp_base2(ref.rung(fam, r + 1) * k + s):
        r += 1
    if r >= floor:
        r = lo
        while r < cap and mr_is_prime(ref.rung(fam, r + 1) * k + s):
            r += 1
    return r


def _classify_chunk(task):
    """Pool worker: run lengths of a chunk of survivors, in order.

    Module-level and self-contained so it survives Windows spawn; touches
    no GPU, so workers never contend with the parent's device work."""
    fam, cap, ks = task
    return [sprp_run(int(k), fam, cap) for k in ks]


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


def _submit(pool, fam, cap, ks):
    """Hand a launch's survivors to the pool.  Returns [(ks_chunk, future)]
    in survivor order; with no pool the chunk is classified right here."""
    ks = [int(k) for k in ks]
    out = []
    for i in range(0, len(ks), CHUNK):
        chunk = ks[i:i + CHUNK]
        if pool is None:
            out.append((chunk, _Done(_classify_chunk((fam, cap, chunk)))))
        else:
            out.append((chunk, pool.submit(_classify_chunk, (fam, cap, chunk))))
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
        self.fam = ref.family(args.family)
        self.s = ref.sign(self.fam)
        self.oeis = self.fam
        self.key = config_key(self.fam)
        self.ckpt = ckpt or ckpt_path(self.fam)
        self.cursor = cursor or _POLICIES[self.fam]
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
        self.hb = Heartbeat(interval=args.heartbeat)
        self._lad = LiveLadder(self._build_ladder)
        self._t0 = time.time()
        self.workers = None            # the pool's size once size_pool ran
        self._sizing = None            # the measurement it was sized from
        self._hostwait = 0.0           # seconds the device waited on the pool
        self._hw_ref = (0.0, time.time())
        self._hostbound_logged = False
        self._ckpt_t = 0.0             # when the last save landed
        self._ckpt_every_s = CKPT_MIN_S
        self._plog_t = 0.0             # when the last period line was logged
        self._plog_n = 0               # periods closed since it
        self._snapshot = None
        self._proof_logged = None      # the filter whose crossing was logged
        self.loaded = self.load()
        self.eng = gpu.GpuEngine(self.filter_n(), self.fam, p1=P1, p2=P2,
                                 p3=P3, q2=Q2, unit=UNIT[self.fam])
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
        top = max(ref.KNOWN[self.fam])
        for n in self.found:
            top = max(top, int(n))
        return top

    def frontier_k(self):
        n = self.frontier()
        return int(self.found.get(str(n), ref.KNOWN[self.fam].get(n, 0)))

    def filter_n(self):
        """The sieve filter is always the next OPEN term."""
        return self.frontier() + 1

    def k_min(self):
        """The clip for the period being worked: K_START inside period 0,
        none elsewhere."""
        return K_START if self.j == 0 else None

    # ----------------------------------------------------------------- rungs
    def _build_ladder(self, frontier, frontier_k, n):
        ceil = cpu.k_ceil(n, self.fam)
        preds = model.predictions(self.fam, frontier, frontier_k,
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
        probable-prime chain rather than a proof (lladder_search.k_proof)."""
        return cpu.k_proof(self.filter_n(), self.fam)

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
                f"{self.oeis}) = {pc:.4g}: {ref.rung(self.fam, self.filter_n())}"
                f"*k {self.s:+d} now exceeds the deterministic Miller-Rabin "
                f"bound, so classification is a seven-base strong "
                f"probable-prime chain from here and a DISCOVERY is proved "
                f"by BLS75 certificate (certify_run); the ceiling is k < "
                f"{cpu.k_ceil(self.filter_n(), self.fam):.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "family": self.fam,
                "sign": self.s,
                "unit": int(self.eng.unit),
                "j": int(self.j),
                "u": int(self.u),
                "W": int(self.eng.W),
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
        t_save = time.perf_counter()
        landed = checkpoint.save(self.ckpt, self._snapshot)
        cost = time.perf_counter() - t_save
        self._ckpt_t = time.time()
        self._ckpt_every_s = max(CKPT_MIN_S, cost / CKPT_COST_FRACTION)
        return landed

    def save_due(self):
        """Whether the rate limit allows a save now."""
        return time.time() - self._ckpt_t >= self._ckpt_every_s

    def save_boundary(self):
        return checkpoint.save(self.ckpt, self._snapshot or self.state())

    def load(self):
        st, kind = self.cursor.load(warn=lambda m: log("STAGE", m))
        if not st:
            return False
        self._stored_w = int(st.get("W", 0))
        self.j = int(st["j"])
        self.u = int(st.get("u", 0))
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
        -- the coverage claim.  It is the period boundary.  Inside period 0
        it is 0, and the least-claim there is monotonicity (nothing below
        a(frontier) can be the next term)."""
        return self.boundary * self.eng.W

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
        # 0 in prime-ladders, because at an opening filter every rung can
        # sit inside period 0.
        k = (self.hb.pos() or self.swept_k())
        cov = self.swept_k()
        rate = self.hb.rate()
        lo = self.boundary * self.eng.W
        pct = min(100.0, max(0.0, 100.0 * (k - lo) / self.eng.W))
        parts = [f"swept to {self.swept_k():.6g}",
                 f"period {self.boundary} [{lo:.5g}, {lo + self.eng.W:.5g}) "
                 f"{pct:.0f}%",
                 f"{self.oeis} filter n = {self.filter_n()}"]
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
            p = model.p_by(self.fam, self.filter_n(),
                           model.floor_for(self.fam, self.filter_n(),
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
        self.census[run] = self.census.get(run, 0) + 1
        if kind == "CENSUS":
            return False
        if kind == "NEAR":
            self.near += 1
            ok, legs, _ = verify(k, run, self.fam)
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
        ok, legs, stop = verify(k, run, self.fam)
        if not ok:
            log("ALARM", f"claimed a({frontier+1}) = {k} failed the "
                         f"protocol: {legs}")
            raise SystemExit(2)
        settles = list(range(frontier + 1, run + 1))
        self.hb.doing(f"certifying run-{run} k={k}")
        certs, unproved = certify_run(k, run, self.fam)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        lo = ref.rungs_from(self.fam)
        also = also_settles(self.fam, k, run, settles)
        ev = {"sequence": self.oeis, "forms": ref.FAMILIES[self.fam]["forms"],
              "sign": self.s, "k": int(k),
              "run": int(run), "settles": settles,
              "values": {str(i): int(ref.value(self.fam, k, i))
                         for i in range(lo, run + 1)},
              "multipliers": {str(i): int(ref.rung(self.fam, i))
                              for i in range(lo, run + 1)},
              "verification": legs,
              "stopper": {"i": stop["i"],
                          "multiplier": ref.rung(self.fam, stop["i"]),
                          "value": int(stop["value"]),
                          "factor": stop["factor"]},
              "certificates": certs,
              # every proof above was re-verified from scratch before it
              # was accepted; `unproved` lists any i that has none
              "certificates_verified": not unproved,
              "unproved": unproved,
              "proof_routes": routes,
              "also_settles": also,
              "least_claim": {"swept_from": K_START,
                              "swept_to": int(k),
                              "wheel": int(self.eng.W), "sieve_depth": Q2,
                              "unit": int(self.eng.unit),
                              "monotone_floor": ref.KNOWN[self.fam][
                                  max(ref.KNOWN[self.fam])]},
              "engine": self.key}
        for n in settles:
            self.found[str(n)] = int(k)
        path = evidence.record(
            ev, EVID, f"{self.oeis}_a{settles[0]}_{k}.json",
            ledger_path(self.fam), key="k",
            label="%s a(%s)" % (self.oeis, ",".join(map(str, settles))))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        lines = [
            f"{self.oeis} a({settles[0]}) = {k:,}" if len(settles) == 1 else
            f"{self.oeis} a({settles[0]})..a({settles[-1]}) = {k:,}",
            f"run {run}: {ref.FAMILIES[self.fam]['forms'].split(',')[0]} is "
            f"prime for every multiplier up to {ref.rung(self.fam, run)}",
            f"stopped by {ref.rung(self.fam, stop['i'])}*k {self.s:+d} = "
            f"{stop['value']:,} = {stop['factor']} * ...",
            f"verified 3 ways, {proved} of {len(certs)} certificates "
            f"re-verified ({', '.join(f'{r} x{c}' for r, c in sorted(routes.items()))}), "
            f"evidence {path}"]
        for a in also:
            lines.append(f"also settles {a['sequence']}({a['n']}) = "
                         f"{a['value']:,}"
                         + (f" (open at {a['open_at']})" if a.get("open_at")
                            else ""))
        if unproved:
            lines.append(f"UNPROVED at i = {unproved}: those values passed "
                         f"the seven-base chain and BPSW but no certificate "
                         f"landed within the bounded effort -- the find "
                         f"stands on the three legs; certify them by hand "
                         f"from the evidence file")
        banner("DISCOVERY", lines)

    def follow_frontier(self):
        """After a find: rebuild the engine at the next open term.

        The wheel PRIMES and the unit do not depend on n, so W is unchanged
        and the cursor keeps its meaning; only the residue tables shrink
        (a prime newly forced at the new filter keeps one residue).  The
        period just closed was swept under a SMALLER filter, whose
        survivors are a superset of the new filter's, and every one of them
        has been classified -- so there is nothing to re-sweep and coverage
        stays contiguous from the next period on.
        """
        old_n = self.eng.n
        self.eng = gpu.GpuEngine(self.filter_n(), self.fam, p1=P1, p2=P2,
                                 p3=P3, q2=Q2, unit=UNIT[self.fam])
        if int(self.eng.W) != self._snapshot["W"]:
            raise RuntimeError("the wheel period changed with the filter; "
                               "the cursor would need re-denomination")
        log("STAGE", f"filter follows the frontier: n = {old_n} -> "
                     f"{self.eng.n}; the ladder now aims at "
                     f"a({self.filter_n()})")
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({n})")
                                  for n in self.found)]
        # the crossing moves with the filter (the top multiplier grew), and
        # may already be behind the sweep
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
        Nothing is recorded -- the loop sweeps the same launches again.

        The line is taken off the cursor the sweep yields, so a period
        shorter than the calibration window (8 launches at n = 18) is
        measured as exactly the line it is."""
        sync = self.eng.cp.cuda.Stream.null.synchronize
        it = self.eng.sweep(self.j, self.j + 1, u_from=self.u,
                            k_min=self.k_min())
        surv, launches, u_prev, cov = [], 0, self.u, 0
        sync()
        t0 = time.perf_counter()
        try:
            for _jn, un, sv in it:
                launches += 1
                cov += (un if un else self.eng.R3) - u_prev
                u_prev = un
                surv.extend(int(k) for k in sv)
                sync()
                el = time.perf_counter() - t0
                if (un == 0 or el >= CAL_MAX_S
                        or (len(surv) >= CAL_MIN_SURVIVORS and el >= CAL_MIN_S)):
                    break
        finally:
            it.close()
        dt = max(time.perf_counter() - t0, 1e-9)
        line = cov * self.eng.W / max(self.eng.R3, 1)
        cap = self.filter_n() + 8
        sample = surv[:CAL_SAMPLE]
        t1 = time.perf_counter()
        for k in sample:
            sprp_run(k, self.fam, cap)
        cost = (time.perf_counter() - t1) / max(len(sample), 1)
        per_s = len(surv) / dt
        return {"launches": launches, "seconds": dt,
                "rate": line / dt,
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
        # two one-second measurements of the same launches can differ 1.6x
        # (ambient load), so a re-size grows on any increase but shrinks
        # only when the need has at least halved -- which a promotion does
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
        target = int(self.args.to or cpu.k_ceil(self.filter_n(), self.fam))
        log("STAGE", f"campaign {self.key}")
        log("STAGE", device_report(self.eng.bytes_held()))
        cfg = self.eng.config()
        log("STAGE",
            f"sweeping the k line to {target:.4g}; {self.oeis} "
            f"({ref.FAMILIES[self.fam]['forms']}) filter n = "
            f"{self.filter_n()}; wheel W = {self.eng.W:,} at unit "
            f"{self.eng.unit} ({self.eng.R:,} residues, {self.eng.R1} x "
            f"{self.eng.R2} x {self.eng.R3}, {100.0 * self.eng.density():.6f}% "
            f"of the line); {cfg['nu']} third-level residues per launch, "
            f"{-(-self.eng.R3 // cfg['nu'])} launches per period; resume at "
            f"period {self.j}, u = {self.u} (k = "
            f"{self.u_progress(self.j, self.u):,})")
        for n, qs in sorted(model.predictions(
                self.fam, self.frontier(), self.frontier_k(),
                n_ahead=3, ceiling=cpu.k_ceil(self.filter_n(), self.fam)).items()):
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
                     f"k_proof({self.filter_n()}, {self.oeis}) = "
                     f"{self.proof_crossing():.4g} and a seven-base strong "
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
        self._plog_t = time.time()
        try:
            while self.swept_k() < target and not stop_now:
                j1 = self.j + 1                 # ONE PERIOD
                if j1 * self.eng.W > cpu.k_ceil(self.filter_n(), self.fam):
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
                                     _submit(self.pool, self.fam, cap, surv)))
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
                self._plog_n += 1
                if found_now or time.time() - self._plog_t >= PERIOD_LOG_S:
                    log("STAGE",
                        f"period {j1 - 1} complete: swept to "
                        f"{self.swept_k():,} (+{self.eng.W:.4g} of line; "
                        f"{held} value{'' if held == 1 else 's'} at run >= "
                        f"{CENSUS_FLOOR} classified in k order"
                        + (f"; {self._plog_n} periods closed since the last "
                           f"such line" if self._plog_n > 1 else "") + ")")
                    self._plog_t, self._plog_n = time.time(), 0
                if found_now:
                    self.mark_boundary()
                    self.follow_frontier()
                    cap = self.filter_n() + 8
                    stop_now = bool(self.args.stop_on_discovery)
                self.hb.mark(self.swept_k())
                self.check_rungs(self.swept_k())
                self.check_proof_crossing(self.swept_k())
                # the boundary is ALWAYS snapshotted (an interrupt writes
                # it); the file is written when the rate limit allows, or
                # at once when this period wrote evidence
                if found_now or self.save_due():
                    self.save()
                else:
                    self.mark_boundary()
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
    return [((15, 14), "DISCOVERY"),      # beyond the frontier
            ((18, 14), "DISCOVERY"),      # a long run settles several at once
            ((14, 14), "NEAR"),           # one condition short of a(15)
            ((13, 14), "CENSUS"),         # below the frontier: counted only
            ((8, 14), "CENSUS"),          # the census floor itself
            ((7, 14), None),              # under the floor: not even counted
            ((0, 14), None)]


# The canaries: two published terms per family that a period-0 mini-hunt
# of a small wheel reaches in a second or two, and the unit those filters
# force (the stream that sweeps k' = k / unit must find the same first k).
_CANARIES = (("A088250", 8, 1), ("A088250", 9, 1), ("A088250", 9, 210),
             ("A173750", 8, 1), ("A173750", 9, 30),
             ("A125838", 8, 1), ("A125838", 9, 210),
             ("A125839", 9, 1), ("A125839", 10, 210),
             ("A164325", 8, 1), ("A164325", 9, 210),
             ("A164326", 8, 1), ("A164326", 9, 210),
             ("A088651", 8, 1), ("A088651", 9, 210))


def _canary_hunt():
    """The stream must organically rediscover known terms, in every family.

    Dedicated mini-hunts at the filters those terms belong to.  The
    production filter cannot rediscover them -- a(8) has run 8 and an
    n = 15 wheel is entitled to kill it -- so rediscovery is done at the
    filter each term belongs to, sweeping period 0 from the engine floor
    with the clip, and the prefix [1, floor] checked by the oracle so
    "FIRST occurrence" is a claim about the line and not about a window.
    """
    hits_all = []
    for fam, n, unit in _CANARIES:
        want = ref.KNOWN[fam][n]
        eng = gpu.GpuEngine(n, fam, p1=13, p2=None, p3=None, q2=4096,
                            unit=unit)
        lo = cpu.k_floor(4096) + 1
        if ref.first_k(fam, n, lo=1, hi=lo - 1) is not None:
            return False, (f"CANARY FAIL: {fam} n={n}: the oracle found a "
                           f"run-{n} below the engine floor")
        ceng = cpu.CpuEngine(n, fam, q2=4096)
        surv = eng.survivors_j(0, want // eng.W + 1, k_min=lo)
        hits = [int(k) for k in surv if ceng.run_length(int(k), cap=n) >= n]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: {fam} filter n={n} unit={unit} "
                           f"found {min(hits) if hits else None}, expected "
                           f"a({n}) = {want}")
        hits_all.append(f"{fam} a({n})" + (f" (unit {unit})" if unit > 1
                                            else ""))
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as FIRST occurrences at their own "
                  "filters, sweeping period 0 from the engine floor with the "
                  "prefix cleared by the oracle -- in k space and in unit "
                  "space, all seven families")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on every family."""
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        k = ref.KNOWN[fam][top]
        ok, legs, stop = verify(k, top, fam)
        if not ok:
            return False, (f"PROTOCOL FAIL: genuine run-{top} at k={k} "
                           f"({fam}) rejected: {legs}")
        if stop["i"] != top + 1 or stop["factor"] is None:
            return False, f"PROTOCOL FAIL: {fam}: no factor witness for the stopper"
        if (stop["value"] % stop["factor"]) or stop["factor"] in (1, stop["value"]):
            return False, f"PROTOCOL FAIL: {fam}: the witness is not a factor"
        bad, legs_b, _ = verify(k, top + 1, fam)
        if bad:
            return False, (f"PROTOCOL FAIL: fake run-{top+1} claim at k={k} "
                           f"({fam}) ACCEPTED ({legs_b})")
        prev = max(n for n in ref.KNOWN[fam] if ref.KNOWN[fam][n] < k)
        fake, _lc, _ = verify(ref.KNOWN[fam][prev], top, fam)
        if fake:
            return False, (f"PROTOCOL FAIL: {fam}: a({prev})'s k accepted as "
                           f"a run-{top}")
    # and the derived claims: an exact-run find settles A202778 at its run
    # and leaves the rider indices open; the half identity holds
    also = also_settles("A088250", 30030 * 7, 17, [15, 16, 17])
    ex = [a for a in also if a["sequence"] == "A202778"]
    hf = [a for a in also if a["sequence"] == "A071576"]
    if (len(ex) != 1 or ex[0]["n"] != 17 or ex[0]["open_at"] != [15, 16]
            or len(hf) != 3 or hf[0]["value"] != 30030 * 7 // 2):
        return False, f"PROTOCOL FAIL: also_settles gave {also}"
    if [a["sequence"] for a in also_settles("A088651", 30030, 16, [16])] != ["A202779"]:
        return False, "PROTOCOL FAIL: A088651's derived claim is not A202779"
    if also_settles("A125838", 30030, 15, [15]):
        return False, "PROTOCOL FAIL: A125838 claims a derived entry it has not"
    return True, ("protocol ok, all seven families: each frontier term "
                  "accepted at its true run with a factor witness for its "
                  "stopper, and a run one too long and a mislabelled earlier "
                  "term both rejected; the derived claims (A202778 at the run "
                  "only, riders left open; A071576 = k/2; A202779 for "
                  "A088651) come out as the identities say")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing."""
    raised = []
    eng = gpu.GpuEngine(12, "A088250", p1=13, p2=None, p3=None, q2=1024)
    ceil = cpu.k_ceil(12, "A088250")
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
    c = cpu.CpuEngine(12, "A088250", q2=1024)
    try:
        c.survivors(10 ** 5, cpu.k_ceil(12, "A088250") + 10)
        return False, "CEILING FAIL: the CPU engine swept past k_ceil"
    except ValueError:
        raised.append("cpu k_ceil")
    # the two signs have DIFFERENT ceilings (lladder_search.k_ceil): the +1
    # families' is the deterministic bound on k, the -1 families' their
    # proof crossing, and the engines enforce each
    if cpu.k_ceil(15, "A088250") != MR_VALID_BELOW or \
            cpu.k_ceil(15, "A125838") != cpu.k_proof(15, "A125838") or \
            not cpu.k_proof(15, "A088250") < cpu.k_ceil(15, "A088250"):
        return False, ("CEILING FAIL: the family ceilings are not the "
                       "proof bounds G10 pins")
    engm = gpu.GpuEngine(12, "A125838", p1=13, p2=None, p3=None, q2=1024)
    ceilm = cpu.k_ceil(12, "A125838")
    try:
        engm.sweep(ceilm // engm.W - 1, ceilm // engm.W + 2)
        return False, "CEILING FAIL: a -1 engine swept past its proof crossing"
    except ValueError:
        raised.append("gpu k_ceil (-1: the proof crossing)")
    try:
        cpu.CpuEngine(12, "A125838", q2=1024).survivors(10 ** 5, ceilm + 10)
        return False, "CEILING FAIL: a -1 CPU engine swept past its proof crossing"
    except ValueError:
        raised.append("cpu k_ceil (-1)")
    try:
        c.survivors(10, 10 ** 6)
        return False, "CEILING FAIL: the CPU engine swept at the floor"
    except ValueError:
        raised.append("cpu floor")
    try:
        gpu.wheel(7, "A088250", 53)          # a flat wheel far past RES_MAX
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(15, "A088250", p1=31, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    try:
        gpu.GpuEngine(7, "A088250", p1=13, p2=37, p3=None, q2=4096)
        return False, "CEILING FAIL: an oversized second level was accepted"
    except ValueError:
        raised.append("gridDim.y")
    try:
        gpu.GpuEngine(gpu.NRES_MAX + 1, "A088250", p1=13, p2=None, p3=None,
                      q2=1024)
        return False, ("CEILING FAIL: a filter longer than the tail's "
                       "residue list was accepted")
    except ValueError:
        raised.append("nforms <= NRES_MAX")
    try:
        gpu.GpuEngine(15, "A088250", p1=13, p2=None, p3=None, q2=1024,
                      unit=510510)
        return False, "CEILING FAIL: a unit not forced at the filter was accepted"
    except ValueError:
        raised.append("unit forced")
    try:
        gpu.GpuEngine(15, "A000001", p1=13, p2=None, p3=None, q2=1024)
        return False, "CEILING FAIL: an unknown family was accepted"
    except KeyError:
        raised.append("family")
    return True, ("ceiling ok: %s all raise rather than compute" %
                  ", ".join(raised))


def _certificate_drill():
    """A discovery past the proof crossing is PROVED, not just tested.

    Below the crossing every certificate takes the deterministic route.
    Above it the value's own structure -- N - 1 = m*k, k factored once, m's
    own factors folded in -- gives BLS75 Theorem 1, and the proof must
    re-verify from scratch and refuse a neighbouring N.  Drilled on the
    A088250 frontier (every value under the bound) and on the first wheel k
    past k_proof(15, A088250) whose 15th value is a strong probable prime
    -- a value past the bound, proved by exactly the wiring the campaign
    runs when a(15) lands past the crossing.  The multiplier there is 15 =
    3 * 5, composite, which is what makes the fold worth drilling.
    """
    top = max(ref.KNOWN["A088250"])
    k = ref.KNOWN["A088250"][top]
    certs, unproved = certify_run(k, top, "A088250")
    if unproved or len(certs) != top:
        return False, (f"CERTIFICATE FAIL: A088250 a({top}) left "
                       f"{unproved} unproved")
    if any(c.get("proof") != "deterministic-mr" for c in certs.values()):
        return False, ("CERTIFICATE FAIL: a value under the bound took the "
                       "certificate route")
    unit = UNIT["A088250"]
    m = -(-cpu.k_proof(15, "A088250") // unit)
    kk = None
    for _ in range(4000):
        cand = unit * m
        if ref.value("A088250", cand, 15) >= MR_VALID_BELOW and \
                sprp_base2(ref.value("A088250", cand, 15)):
            kk = cand
            break
        m += 1
    if kk is None:
        return False, ("CERTIFICATE FAIL: no wheel k past the crossing with "
                       "a probable-prime 15th value in 4000 tries")
    certs, unproved = certify_run(kk, 15, "A088250", only=(15,))
    c15 = certs.get("15")
    if unproved or c15 is None or c15.get("proof") != "bls75-thm1":
        return False, (f"CERTIFICATE FAIL: 15*{kk}+1 (past the bound) was "
                       f"not proved by BLS75 Theorem 1: {c15 and c15.get('proof')}")
    if int(c15["N"]) != ref.value("A088250", kk, 15) or int(c15["R"]) != 1:
        return False, ("CERTIFICATE FAIL: the Theorem 1 proof is not about "
                       "the value, or N - 1 was not factored completely")
    ok, why = certificate.verify(c15)
    if not ok:
        return False, f"CERTIFICATE FAIL: the proof does not re-verify: {why}"
    if certificate.verify(dict(c15, N=int(c15["N"]) + 2))[0]:
        return False, ("CERTIFICATE FAIL: the proof verified for a "
                       "neighbouring N")
    if certificate.verify({"proof": "deterministic-mr",
                           "N": int(c15["N"])})[0]:
        return False, ("CERTIFICATE FAIL: a deterministic-MR claim past the "
                       "bound was accepted as a proof")
    return True, (f"certificates ok: A088250 a({top})'s {top} values take the "
                  f"deterministic route and re-verify; past the crossing, "
                  f"15*k+1 = {ref.value('A088250', kk, 15):.4g} at k = {kk:.4g} "
                  f"is proved by BLS75 Theorem 1 on N - 1 = 15*k factored "
                  f"completely ({len(c15['factors'])} prime factors, every "
                  f"one under the deterministic bound), re-verifies from "
                  f"scratch, and is refused for N + 2 and as a bare "
                  f"deterministic-MR claim")


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly, on every kernel
    and across the seams a real interrupt leaves: a period boundary, the
    (j, u) sub-period cursor, and the clipped period 0."""
    total = 0
    for lab, fam, kw, j_at, span, cut in (
            ("one-level", "A088250", dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 60000, 23000),
            # the production first two levels, in the unit (a two-level
            # period there is 6.2e17 of k and 2e10 candidates, 0.2 s, so
            # the window sits above period 0 and spans six)
            ("two-level", "A125838", dict(p1=P1, p2=P2, p3=None, q2=Q2,
                                          unit=UNIT["A125838"]),
             10 ** 19, 6, 2),
            ("three-level", "A088250", dict(p1=13, p2=17, p3=19, q2=128),
             9 * 10 ** 14, 4000, 1111)):
        eng = gpu.GpuEngine(15, fam, **kw)
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
    # which is where every campaign's first interrupt will land.  nu is
    # forced below R3 so the period really is cut into launches; in k space
    # and in UNIT space -- the campaigns' engine -- where a period is 30030
    # times a k' period and the seam must still close.
    for eng in (gpu.GpuEngine(15, "A088250", p1=13, p2=23, p3=37, q2=512,
                              nu=64),
                gpu.GpuEngine(15, "A088250", p1=19, p2=23, p3=31, q2=64,
                              nu=4, unit=30030)):
        if eng.nu >= eng.R3:
            return False, "RESUME FAIL: the seam engine has no sub-period cursor"
        for j0, k_min in ((eng.j_of(9 * 10 ** 14), None), (0, K_START)):
            whole = sorted(eng.survivors_j(j0, j0 + 1, k_min=k_min))
            if not whole:
                return False, (f"RESUME FAIL: the (j, u) seam window is empty "
                               f"(unit {eng.unit}, period {j0})")
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
                  f"and in unit space (30030), and inside the clipped period "
                  f"0 on both ({total} survivors across the seams)")


def _classification_drill():
    """The two-pass screen == the all-bases chain on real survivors, and the
    pool's chunked answer == the serial one."""
    # 6,000 periods of the (13],(23] wheel at n = 10 is 1.3e12 of line,
    # which at that density and sieve depth is a few thousand survivors
    eng = gpu.GpuEngine(10, "A088250", p1=13, p2=23, p3=None, q2=4096)
    j0 = eng.j_of(10 ** 13)
    surv = eng.survivors_j(j0, j0 + 6000)
    if len(surv) < 3 * CHUNK:
        return False, (f"CLASSIFY FAIL: only {len(surv)} survivors -- the "
                       f"drill cannot span several chunks")
    two = [sprp_run(k, "A088250", 22) for k in surv]
    full = []
    for k in surv:
        r = 0
        while r < 22 and mr_is_prime(ref.rung("A088250", r + 1) * k + 1):
            r += 1
        full.append(r)
    if two != full:
        i = next(i for i in range(len(surv)) if two[i] != full[i])
        return False, (f"CLASSIFY FAIL: two-pass sprp gave run {two[i]} and "
                       f"the all-bases chain {full[i]} at k = {surv[i]}")
    with _pool_factory(2) as pool:
        parts = _submit(pool, "A088250", 22, surv)
        got = [r for ks, f in parts for r in f.result()]
    if got != full:
        return False, "CLASSIFY FAIL: the pool's chunked result differs"
    # and the families whose runs start above 0 count from their first rung
    if sprp_run(2, "A125838", 8) != 4 or sprp_run(1, "A125839", 8) != 4 \
            or sprp_run(1, "A173750", 8) != 2:
        return False, "CLASSIFY FAIL: a family's run does not start at its first rung"
    return True, (f"classification ok: two-pass sprp == all-bases chain on "
                  f"{len(surv)} real survivors (max run {max(full)}), "
                  f"{len(parts)} pool chunks reassemble to the serial answer, "
                  f"and the families whose rungs start at 2 or 3 count from "
                  f"there")


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


def _other_families_cursor_drill(fam):
    """Every OTHER family's policy, put in front of every key it declares."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="lladder-cursor-")
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
                    return False, (f"CURSOR FAIL: {other} will not read a "
                                   f"checkpoint keyed {key}")
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
    """No two campaigns may be able to read each other's cursor."""
    fams = list(ref.FAMILIES)
    keys = {config_key(f) for f in fams}
    if len(keys) != len(fams):
        return False, "FAMILY FAIL: two families share a config key"
    if len({ckpt_path(f) for f in fams}) != len(fams):
        return False, "FAMILY FAIL: two families share a checkpoint file"
    if len({ledger_path(f) for f in fams}) != len(fams):
        return False, "FAMILY FAIL: two families share a ledger"
    for f in fams:
        for other in fams:
            if other != f and config_key(other) in _POLICIES[f].readable():
                return False, (f"FAMILY FAIL: the {f} policy accepts the "
                               f"{other} key")
    # the aliases open the right campaign, and the units are the forced ones
    if ref.family("A202778") != "A088250" or ref.family("A202779") != "A088651":
        return False, "FAMILY FAIL: the exact-run aliases do not resolve"
    if UNIT["A088250"] != 30030 or UNIT["A088651"] != 510510:
        return False, f"FAMILY FAIL: the opening units are {UNIT}"
    for f in fams:
        cpu.assert_unit(open_n(f), f, UNIT[f])
        cpu.assert_unit(open_n(f) + 4, f, UNIT[f])
    return True, ("families stay apart: seven distinct config keys, "
                  "checkpoint files and ledgers, no policy reads another's "
                  "cursor, the exact-run aliases resolve, and every "
                  "family's unit is forced at its opening filter and four "
                  "filters after it")


def _campaign_wiring_drill(fam="A088250"):
    """Build a campaign and exercise everything the loop touches, without
    sweeping a whole period: construction from nothing at period 0, the
    status line, census and NEAR/CENSUS classification, the cached rung
    ladder, the drain of a fake in-flight launch, the pool sized from a
    real measurement, back-pressure, a find moving the filter, a save/load
    round trip, and the interrupt snapshot."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="lladder-drill-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[fam].at(path)
    n0 = open_n(fam)

    class _A:
        pass
    a = _A()
    for k, v in dict(family=fam, fresh=False, to=None,
                     stop_on_discovery=False, heartbeat=30.0,
                     gpu_yield_ms=0.0, status=False, selftest=False,
                     workers=1, worker_ramp=WORKER_RAMP_S).items():
        setattr(a, k, v)
    try:
        c = Campaign(a, ckpt=path, cursor=pol)
        if c.frontier() != n0 - 1 or c.filter_n() != n0:
            return False, (f"WIRING FAIL: frontier {c.frontier()}, filter "
                           f"{c.filter_n()} -- expected {n0 - 1} and {n0}")
        if (c.j, c.u, c.swept_k(), c.k_min()) != (0, 0, 0, K_START):
            return False, (f"WIRING FAIL: a fresh campaign starts at "
                           f"(j, u) = ({c.j}, {c.u}), swept {c.swept_k()}, "
                           f"clip {c.k_min()} -- expected period 0 clipped "
                           f"at {K_START}")
        if c.eng.n != n0 or c.eng.fam != fam or c.eng.unit != UNIT[fam]:
            return False, "WIRING FAIL: the engine is not at the campaign filter"
        line = c.status_line()
        for want in ("swept to", fam, "census", "period 0"):
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
        if not nxt or not nxt[0].startswith(f"a({n0})"):
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
        # calibration sweeps real launches of period 0 at the opening
        # filter, counts survivors, times a classified sample, and the
        # pool that comes up is ceil(need x margin) real interpreters
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
        if (f"P(a({n0}) under the claim) = 0%" not in line
                or f"next a({n0})" not in line):
            return False, (f"WIRING FAIL: the status line reads the rungs "
                           f"off progress, not coverage: {line}")
        c.pool.shutdown(wait=True, cancel_futures=True)
        c.pool, c.workers, c.args.workers = None, None, 1
        c.found[str(n0)] = int(ref.KNOWN[fam][n0 - 1]) + UNIT[fam]   # a find, unverified
        if c.frontier() != n0 or c.filter_n() != n0 + 1:
            return False, "WIRING FAIL: a find did not move the frontier"
        aim = c.next_rung(c.swept_k())
        if c._lad.builds != builds + 1:
            return False, ("WIRING FAIL: the frontier moved and the ladder "
                           "was served from cache")
        if not aim or not aim[0].startswith((f"a({n0 + 1})", "engine ceiling")):
            return False, (f"WIRING FAIL: after finding a({n0}) the campaign "
                           f"aims at {aim} -- a retired rung")
        c.mark_boundary()
        c.follow_frontier()
        if c.eng.n != n0 + 1 or int(c.eng.W) != c._snapshot["W"]:
            return False, "WIRING FAIL: follow_frontier did not move the filter"
        c.found.pop(str(n0))
        c._lad.invalidate()
        # the period-close save is rate-limited, the boundary snapshot is
        # not: a save that is not due still leaves a fresh snapshot
        c._ckpt_t = time.time()
        if c.save_due():
            return False, "WIRING FAIL: a save was due right after a save"
        c._ckpt_t = 0.0
        if not c.save_due():
            return False, "WIRING FAIL: a save was not due after the interval"
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
    return True, (f"campaign wiring ok ({fam}): a campaign builds from nothing "
                  f"at period 0 clipped at K_START with the engine at "
                  f"n = {n0} and unit {UNIT[fam]}, its status line and rung "
                  f"ladder aim at a({n0}), 75 ladder reads at a standing "
                  f"frontier cost 0 model rebuilds while a find costs "
                  f"exactly 1 and moves the aim and the filter, the pool is "
                  f"sized from a live measurement and survives a re-size "
                  f"inside the noise band, back-pressure times the wait, "
                  f"the drain keeps the work cursor behind the classified "
                  f"launches and floors the census, the period save is "
                  f"rate-limited, and the checkpoint round trips through "
                  f"both the normal save and the interrupt snapshot, pending "
                  f"included")


def selftest(fam="A088250"):
    t0 = time.time()
    rows = []
    for g in (ref.GATES + cpu.GATES + gpu.GATES + model.GATES
              + certificate.GATES):
        rows.append(g())
    rows.append(drills.event_kind_drill(
        lambda c: event_kind(*c), _event_cases()))
    for d in drills.standard(pool_factory=_pool_factory,
                             cursor=_POLICIES[fam]):
        rows.append(d)
    rows.append(_other_families_cursor_drill(fam))
    for d in (_ceiling_drill, _canary_hunt, _protocol_drill,
              _certificate_drill, _resume_drill,
              _classification_drill, _stop_on_discovery_drill,
              _families_stay_apart):
        rows.append(d())
    rows.append(_campaign_wiring_drill(fam))
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
    front = max(ref.KNOWN[fam])
    for n in st.get("found", {}):
        front = max(front, int(n))
    log("STATUS", "  ".join([
        f"{fam}",
        f"swept to k = {int(st['k']):,}",
        f"work cursor period {int(st['j'])} u = {int(st.get('u', 0))}",
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
    ap.add_argument("--family", default="A088250",
                    help="which sequence to hunt: " +
                         ", ".join(f"{f} ({ref.FAMILIES[f]['forms']})"
                                   for f in ref.FAMILIES) +
                         "; A202778 and A202779 are aliases of A088250 and "
                         "A088651, whose exact-run versions they are "
                         "(default A088250)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this depth on the k line (default: the "
                         "engine ceiling -- the family's primality-proof "
                         "validity bound, 3.3e24 for the +1 families and "
                         "the proof crossing, about 2e23, for the -1 ones)")
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
                         "1 ms against a ~5 ms launch costs about 17%% of "
                         "the rate and leaves the desktop noticeably freer")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 2 --workers 1 --worker-ramp "
                         "1.0 (about a third of the rate, one fewer process)")
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
                             f"swept to k = {st.get('k')}"))
    if args.fresh:
        for p in (ckpt_path(args.family), ckpt_path(args.family) + ".bak"):
            if os.path.exists(p):
                os.remove(p)
    return Campaign(args).run()


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
