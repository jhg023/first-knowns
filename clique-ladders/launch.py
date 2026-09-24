"""The campaign for the clique ladders -- a(n) = least x > a(n-1) with
x + a(i) + 1 prime for every i < n (plus one extra condition per family).

    python launch.py                       the hunt: indefinite, resumable (A093483)
    python launch.py --family A119752      any of the six families
    python launch.py --status              where the cursor is; reads, never writes
    python launch.py --selftest            the full gate battery; must end ALL GREEN

SIX FAMILIES, ELEVEN OEIS ENTRIES, ONE CAMPAIGN AT A TIME.  `--family` names
the entry (clique_reference.FAMILIES); the five derived entries -- A180565,
A115760, A128933, A120403, A113875, each a hunted entry under an affine map
-- are accepted as aliases and open their base family.  Each family has its
own checkpoint, ledger and config key and a campaign hunts one of them.  A
find settles its derived entries at the same index, and the evidence file
says so (`also_settles`).

THE FORM LIST IS STATE, AND EVERYTHING DIFFERENT ABOUT THIS LAUNCHER FOLLOWS
FROM THAT.  The conditions at index n are x + a(i) + 1 for i < n, so the
filter for a(n+1) does not exist until a(n) does.  Therefore:

  * ONE OPENING PER FAMILY (CLAUDE.md 5g).  A campaign can be planned,
    priced and benchmarked at exactly one index, the open one; score.py has
    one campaign shape per family, and `plan_for` is the one place a
    configuration is derived.  Every later filter is planned at runtime,
    when the term that defines it lands, and the pool is re-sized from a
    fresh measurement there.
  * EVERY TERM THE CAMPAIGN FINDS IS REGISTERED WITH THE ORACLE before any
    engine is built (`_register`), at start from the checkpoint and at every
    promotion.  The oracle refuses to have a term CHANGED, and pool workers,
    being other processes, are handed the form list inside each task
    (`filter_forms`) rather than trusted to know it.
  * A FIND RESTARTS THE SWEEP JUST ABOVE ITSELF (`follow_frontier`).  The
    new index has a condition the old filter never tested, so whatever the
    old filter swept past the find claims nothing.  The segment loop stops
    narrating at the first find, drops the rest of that segment's survivors
    UNCOUNTED, and the rebuilt engine re-sweeps from the find.  factorial-
    ladders carries its classified line across a promotion; here that would
    be a coverage hole one segment wide with every gate green, and
    `_promotion_drill` stands in front of it.  The cost is at most one old
    segment, and the planner PRICES that waste against the rate a longer
    segment buys (clique_gpu.plan: expected clock to a confirmed find).
  * NO RIDERS.  a(n) > a(n-1) strictly and a run cannot pass the filter, so
    a find settles exactly one index.
  * ADMISSIBILITY IS CHECKED AT EVERY PROMOTION.  Nothing proves the offsets
    leave a residue class free modulo every prime; if a new term covers one,
    no x satisfies the next index and the sequence is FINITE.  That is a
    result, not a fault: the launcher says so in a [MILESTONE] and stops
    instead of sweeping a line that holds nothing.
  * A FIND IS RE-DERIVED BY THE ORACLE against the whole prefix before
    anything is written, because a wrong a(n) would poison every later term;
    the evidence file carries that prefix.

THE LINE.  The published term is x itself.  The engine sweeps the FORCED
CLASS x = r + u*t (clique_search.forced_class: 2 mod 6, 0 mod 6, 9 mod 30 or
11 mod 30 at the open indices), and because r < u the periods of x and of t
share their boundaries, so every cursor here is in x.  u is derived per
filter; it grows as the sequence does.

THE RUN of a survivor, in index units: 0 if the family's extra form fails,
else 1 + the leading conditions x + a(1) + 1, x + a(2) + 1, ... that are
prime.  A full run is n, one condition short is n - 1.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine ceiling, huntlib.ceiling.K_CEIL = 1e40.  THE PROOF CROSSING IS
HIGH HERE -- x = 1.66e24 where 2x + 1 is a form, 3.3e24 elsewhere, above
every term the campaign can reach in weeks -- so for nearly the whole hunt a
classification IS a proof.  Past it the values are UNSTRUCTURED (V - 1 =
x + a(i)), which is rule 5h's exception: the ceiling rests on a measurement
(huntlib.ceiling.subproof_rate: 12 of 12 to 1e40), repeated by G10 and by
the certificate drill on this project's own values, and a value that cannot
be proved is reported in the evidence file rather than hidden.

THE TAXONOMY, mapped to this problem (CONVENTIONS.md "the discovery
protocol"), for a survivor with run r while a(n) is open (frontier n - 1):

  DISCOVERY  r == n, above a(n-1): a(n).  Re-derived by the oracle, verified
             three ways, a re-verified certificate for every value.  There is
             NO STOPPER: the form that would decide index n + 1 is
             x + a(n) + 1, and a(n) is this x.  The evidence file records the
             prefix the claim is relative to and what it settles in the
             derived entries.
  NEAR       r == n - 1: one condition short.  One line with its campaign
             ordinal, verified by the cheap legs as an engine health check
             (no factor witness), never evidenced.
  CENSUS     CENSUS_FLOOR <= r < n - 1: counted in [STATUS], never narrated.

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
candidates of a segment come out in wheel order, not x order, so nothing in
a segment is known to be the LEAST until the segment closes: 'swept to' is
the x below which every value has been tested and moves a segment at a time;
(period, launch) is the work cursor inside it, which a resume picks up and
which claims nothing.  After a find 'swept to' moves BACK to the find: the
new filter's coverage starts there.

THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER, at
start and at every promotion (CLAUDE.md 5f, 5g): the next launches are swept
and timed, their survivors counted, a sample classified, and the pool is
ceil(core-seconds per second x margin) workers, ramped one at a time.
Back-pressure bounds the device's lead over the host and the waited fraction
is in every [STATUS] line.

Ctrl+C is a normal exit: a checkpoint at the last segment boundary, one
[STAGE] line, exit code 130, no traceback (huntlib.shutdown).
"""

import argparse
import collections
import concurrent.futures as _cf
import contextlib
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

import clique_gpu as gpu                                       # noqa: E402
import clique_model as model                                   # noqa: E402
import clique_reference as ref                                 # noqa: E402
import clique_search as cpu                                    # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")

# THE LETTER THE OEIS USES FOR THE TERM.  None of these entries gives it one
# -- they read "a(n) is the smallest integer > a(n-1) such that a(n) + a(i)
# + 1 is prime" -- so every surface a person reads (the evidence files, the
# [DISCOVERY] / [NEAR] / [STATUS] / [STAGE] lines, --status) carries it under
# the entry's own wording, a(n).  The engines call their sweep variable x
# and the checkpoint stores the cursor as "k"; neither is the owner's
# problem (CONVENTIONS.md "Naming in an evidence file").
TERM = ref.TERM

# NOTHING ABOUT THE WHEEL IS A CONSTANT HERE.  The three wheel levels, the
# sieve depth and the window width are all PLANNED per filter, because the
# kill sets grow with every term found (clique_reference: K(q,n) is a
# subset of K(q,n+1)) and the period the search can afford grows with the
# modelled median.  The forced class moves too -- its modulus grows the
# moment a new term fills a prime's last class but one -- so it is derived
# per filter and never stored.  `plan_for` is the ONE
# place a configuration is derived, and `--status`, the campaign and every
# drill go through it (OPTIMIZATION.md 2.9: derive configuration in exactly
# one place).
PLAN_VERSION = "p2"               # bump when plan_for's answer changes
#   p1: factorial-ladders' p2 planner (the SEGMENT capped against the
#   modelled median, the window planned per filter, subset wheels) with the
#   forced class in place of the unit
#   p2: the wheel and the window chosen together by expected clock to a
#   confirmed find (clique_gpu.plan) -- no hard segment cap; the window-
#   dependent block shape; never opened a campaign under p1, so there is no
#   p1 cursor to adopt


@functools.lru_cache(maxsize=None)
def plan_for(fam, n):
    """(unit, p1, p2, p3, q2, pb) for filter n of family F -- the
    configuration the campaign runs there, and the fastest correct one it
    has (CLAUDE.md 5g).  The wheel and the window are chosen TOGETHER, to
    minimise the expected clock to a CONFIRMED find: the model's expected
    line swept until the segment holding a(n) closes (a find restarts the
    sweep here, so the rest of its segment is thrown away) times the
    measured device seconds per unit of line at that wheel and width; the
    depth is the smallest whose analytic survivor rate the host absorbs
    (clique_gpu.plan, wheel_candidates, plan_q2; planner p2,
    OPTIMIZATION_LOG.md round 1).  THE RECORD IS NOT PLANNED HERE: the engine chooses
    the narrow or the wide survivor record from the wheel and window it is
    handed, at every build -- the campaign's start and every promotion --
    so the wheel to 53 at n = 18 comes up on the wide record with no flag
    (clique_gpu.GpuEngine, `wide`; drilled in _promotion_drill).

    CACHED, AND THAT IS NOT AN OPTIMISATION DETAIL.  Planning enumerates
    every admissible three-level split and walks the sieve primes: 33 ms.
    It is a pure function of (family, filter), so its answer changes a
    handful of times in a campaign -- but `x_floor` calls it, `k_min` calls
    `x_floor` every segment and `state` calls it every launch, and 33 ms
    against a 14 ms launch is OPTIMIZATION.md 2.14's trap wearing a
    different hat: a per-launch cost that does not scale with the work.
    Measured on the campaign's own loop, before and after: 34.1 ms per
    `mark_boundary` -> 4.6 us.  The tell was the same one shift-ladders
    left: an absolute per-launch constant that two configurations four
    orders of magnitude apart in line agreed on.
    """
    fam = ref.family(fam)
    unit = cpu.forced_unit(n, fam)
    p1, p2, p3, q2, pb = gpu.plan(n, fam, unit)
    return unit, p1, p2, p3, q2, pb


@functools.lru_cache(maxsize=None)
def x_floor(fam, n, frontier_x):
    """Where the sweep for a(n) starts.

    a() is non-decreasing (the conditions nest), so nothing below the
    previous term can be the next one and the floor is free -- and it is the
    same number on every filter, because the published term IS x.  The
    engine's own floor (the exception zone, where a value could BE the prime
    dividing it: x + s <= q2) is taken as well; it is q2 at every filter
    here, far below any frontier."""
    fam = ref.family(fam)
    _u, _a, _b, _c, q2, _pb = plan_for(fam, n)
    # STRICTLY above the previous term: the definition says a(n) > a(n-1),
    # and there are no riders here (one x cannot be two terms)
    return max(int(frontier_x) + 1, cpu.k_floor(q2, n, fam) + 1)


def open_n(fam):
    """The filter a FRESH campaign of this family opens at: the index after
    the published frontier."""
    return max(ref.KNOWN[ref.family(fam)]) + 1




# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a segment.  A
# launch is 2^37 candidates at most (clique_gpu.CAND_PER_LAUNCH4), some tens
# of milliseconds, so 32 launches is a second or two: what an interrupt
# costs to redo, and the denominator that prices --gpu-yield-ms.  The
# mid-segment save is rate-limited by CKPT_MIN_S.
CKPT_LAUNCHES = 32
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
# WHAT A PLAN MAY WASTE.  A find is only known to be the least once its
# segment closes, and here the rest of that segment is thrown away (the new
# index has a condition the old filter never tested), so a plan is priced in
# EXPECTED LINE SWEPT TO A CONFIRMED FIND (clique_model.expected_sweep)
# rather than capped: the planner trades that waste against the rate a longer
# wheel or a wider window buys.  This is the CHECK on the trade, not the
# trade: a plan whose expected sweep exceeds the unavoidable one (segments of
# zero length) by more than this factor is a decision for a human.  The
# worst shipped plan is 1.34 (A037100's opening: the median is 1.8 segments
# of the shortest window of its best wheel, and the search is 5 s).
PLAN_WASTE_MAX = 1.5


def c_front(fam):
    """The frontier term a fresh campaign of `fam` starts from."""
    fam = ref.family(fam)
    return ref.KNOWN[fam][max(ref.KNOWN[fam])]
# THE ENGINE IS THIS PROJECT'S v1: factorial-ladders' v3 (the window sieve,
# the 2^64 reduction bound, the WIDE survivor record taken at runtime
# wherever a wheel's period admits no u64 window, subset wheels) with the
# form list built from the sequence's own terms and the unit generalised to
# a forced class x = r + u*t (OPTIMIZATION_LOG.md, Decision 1).  Round 1
# changed how a block is SHAPED (residues per block and the extraction batch
# follow the window's width) and nothing about what it computes: the stream
# is identical and the anchors' fingerprints did not move, so it is still v1
# -- what moved the campaign's line is the PLAN, and that is p2.
ENGINE_VERSION = "v1"
# No predecessor CURSOR: neither v1 nor v2 ever opened a campaign, so there
# is no checkpoint to accept or adopt (and one could only be ADOPTED, since
# the segment width moved with each version).  The list is kept (empty) because
# CursorPolicy takes it and because the moment an old key exists it
# belongs HERE and nowhere else -- a list of old keys given to two of the
# three readers is a green battery and a campaign that will not start
# (CONVENTIONS.md "Reading an existing cursor"; it has cost this repo two
# campaign starts).
PREVIOUS_ENGINES = ()
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
# The calibration sweeps up to this many SEGMENTS: since v3 a segment at an
# opening filter is one window of a small wheel -- a single launch of a few
# milliseconds and a handful of survivors -- and a pool sized from one of
# those is sized from noise (the wiring drill read 3 survivors).  The time
# and sample floors above still stop it; this only stops it running away.
CAL_SEGMENTS = 256
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
    # The wheel is NOT in the key, because it is not fixed for the campaign
    # -- it is planned per filter, and the filter is in the STATE.  What is
    # in the key is what would change the meaning of a stored cursor for a
    # GIVEN filter: the engine version, the planner version, and the launch
    # decomposition that gives the work cursor its units.  The per-filter
    # configuration is then ASSERTED on load (unit, W, q2, seg_periods),
    # which is the check that actually stops a misread cursor
    # (OPTIMIZATION.md 2.9: a key describes, an assertion enforces).
    key = (f"{fam.lower()}-{engine or ENGINE_VERSION}-{PLAN_VERSION}"
           f"-seg{CKPT_LAUNCHES}"
           f"-pbd{gpu.PB_DEFAULT}"
           f"-cpl{gpu.CAND_PER_LAUNCH4.bit_length() - 1}"
           f"w{gpu.CAND_PER_LAUNCH_WIDE.bit_length() - 1}")
    return key


def ckpt_path(fam):
    return str(HERE / f"campaign_checkpoint_{ref.family(fam).lower()}.json")


def ledger_path(fam):
    return str(HERE / "evidence" / f"{ref.family(fam).lower()}_discoveries.json")


# EVERY reader of the checkpoint goes through this object and none of them
# takes a key list of its own.  There are three readers -- the campaign's
# load, --status, and the refusal check in main() -- and passing the same
# list to three places is a thing you can forget at one of them; it cost
# this repo two campaign starts before the policy existed (CONVENTIONS.md
# "Reading an existing cursor").  v3 inherits v2's cursor (the identical
# line: same wheel, unit, sieve and W, every fingerprint reproduced), so
# every policy ACCEPTS the v2 key; the cursor drills in --selftest put all
# three readers in front of every declared key, the v2-resume drill builds
# a campaign on each family's real v2 checkpoint, and a foreign key refuses.
_POLICIES = {fam: checkpoint.CursorPolicy(
                 ckpt_path(fam), config_key(fam),
                 accept=tuple(config_key(fam, engine=e) for e in PREVIOUS_ENGINES),
                 adopt=())
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


def verify(x, run, fam, witness=True, n=None):
    """The three independent confirmations plus the bounding witness.

    witness=False is the [NEAR] path: a one-short value is verified but not
    evidenced, so nobody reads its stopper's factor, and rho plus 200 ECM
    curves on a 40-digit stopper is device-idle time bought for nothing.
    The stopper is still shown composite -- that leg is what bounds the run.

    Everything is stated on x, the published term.  `run` is in index
    units (clique_reference.run_length) and `n` is the filter it was
    measured at (default: the run itself, i.e. a full run).

    1. huntlib's Miller-Rabin, which is a PROOF below the proof crossing
       k_proof(n, F) (G10) and a thirteen-base strong probable-prime chain
       above it -- where the certificate (certify_run), not this leg, is
       the proof;
    2. sympy's BPSW, an independent implementation, which must agree on the
       run LENGTH and not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense x line and uses no wheel at all, must
       agree that this x survives a sieve at a DIFFERENT depth from the
       campaign's, at the filter the run reaches.

    plus a factor witness for the composite that STOPS the run, which is
    what bounds the claim to exactly `run`.  Nothing here is unbounded: the
    witness is trial division, then a bounded rho, then bounded ECM
    (stopper_witness), and a stopper that keeps its factors from that
    effort is recorded as composite by the strong test -- a failed
    Miller-Rabin is a PROOF of compositeness -- with no witness rather than
    with an hour of factorint at the campaign's expense.
    """
    fam = ref.family(fam)
    x, run = int(x), int(run)
    n = run if n is None else int(n)
    # the conditions a run of `run` claims: every form of INDEX run (the
    # extra forms and the shifts by a(1..run-1))
    legs = {"mr_chain": all(mr_is_prime(v) for v in ref.values(fam, x, run)),
            "sympy_bpsw": ref.run_length(fam, x, n) == run,
            "resieve_other_wheel": cpu.CpuEngine(run, fam, q2=4096).survives(x)}
    if run >= n:
        # A FULL RUN HAS NO STOPPER: the form that would decide index n + 1
        # is x + a(n) + 1, and a(n) is this x.  What bounds the claim is the
        # sweep below it, not a composite above it.
        return all(legs.values()), legs, None
    stop = x + ref.term(fam, run) + 1            # the first shift form it fails
    legs["stopper_composite"] = not mr_is_prime(stop)
    ok = all(legs.values())
    wit = (stopper_witness(stop)
           if witness and legs["stopper_composite"] else None)
    return ok, legs, {"i": run, "value": stop, "factor": wit,
                      "why": "composite"}


# Below this a stopper's full factorization is seconds at worst, so
# huntlib's factor_witness -- which ends in sympy's factorint -- may still
# be asked; above it only the BOUNDED chain runs, because a 40-digit
# semiprime with two 20-digit factors would hold the campaign for as long
# as factorint needs.
WITNESS_FULL_BELOW = 10 ** 30


def stopper_witness(stop):
    """A nontrivial prime factor of the composite stopper, or None if the
    bounded effort (trial division, rho, 200 ECM curves) found none."""
    fac, _R = certificate.factor_partial(int(stop), ecm_curves=200)
    if fac:
        return int(min(fac))
    if stop < WITNESS_FULL_BELOW:
        w = factor_witness(int(stop))
        return int(w) if w and w > 1 else None
    return None


def certify_run(x, run, fam, only=None):
    """A checkable primality certificate for every value of a full run at
    index `run`: ({str(i): proof}, [the i left UNPROVED]), i counting the
    forms of that index from 1 in clique_reference.forms order.

    THIS PROJECT IS RULE 5h'S EXCEPTION, NOT ITS BEST CASE.  The values are
    x + a(i) + 1, 2x + 1 and x: V - 1 is an integer with no structure, so
    nothing about x factors it.  Below the deterministic bound -- which is
    ABOVE every term this campaign can reach in weeks (clique_search) --
    huntlib.certificate.prove answers with deterministic Miller-Rabin, which
    IS the proof there.  Above it each value gets prove()'s own bounded search on
    V - 1 and V + 1 (rho, then ECM), which `huntlib.ceiling.subproof_rate`
    measured at 12 of 12 to 1e40 and G10 re-measures on every battery.  A
    value it cannot prove is REPORTED, never hidden.

    Every proof is RE-VERIFIED from scratch before it is returned.
    """
    fam = ref.family(fam)
    vals = ref.values(fam, int(x), int(run))
    certs, unproved = {}, []
    for i in (range(1, len(vals) + 1) if only is None else only):
        proof = certificate.prove(int(vals[i - 1]))
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
        certs[str(i)] = proof
        if proof is None:
            unproved.append(int(i))
    return certs, unproved


def also_settles(fam, x, run, settles):
    """What a find settles in the DERIVED entries, as records for the
    evidence file: each is this entry under an affine map (mul*x + shift),
    proved term by term and by the derived entry's own condition in
    clique_reference G2d."""
    fam = ref.family(fam)
    out = []
    for seq, mul, shift in ref.FAMILIES[fam]["also"]:
        for n in settles:
            out.append({"sequence": seq, "n": int(n),
                        "value": int(mul) * int(x) + int(shift),
                        "claim": (f"{mul}*{fam}({n}) + {shift}" if mul != 1
                                  else f"{fam}({n}) + {shift}")})
    return out


# ----------------------------- classification -------------------------------

def filter_forms(fam, n):
    """(extra, shifts) for index n: what a worker needs to classify, as
    plain ints -- a pool worker is another process and knows nothing of the
    terms this campaign has found."""
    fam = ref.family(fam)
    return (tuple(ref.extra(fam)), tuple(t + 1 for t in ref.terms(fam, n)))


def sprp_run(x, forms, cap, floor=CENSUS_FLOOR):
    """The run of x in INDEX units (clique_reference.run_length), screened
    with a base-2 strong test and CONFIRMED with the deterministic chain
    wherever the answer matters.

    A failed base-2 test is a PROOF of compositeness (huntlib.primes), so
    the first pass can only overstate a run, never understate it.  Runs that
    come out below the census floor are never looked at again; a run at or
    above it is recomputed with the full base set.  `forms` is
    filter_forms(F, n) and `cap` is n: a run cannot pass the filter here.
    """
    extra, shifts = forms
    x, cap = int(x), int(cap)

    def chain(test):
        for a, b in extra:
            if not test(a * x + b):
                return 0
        r = 1
        for c in shifts:
            if r >= cap or not test(x + c):
                break
            r += 1
        return r

    r = chain(sprp_base2)
    return chain(mr_is_prime) if r >= floor else r


def _classify_chunk(task):
    """Pool worker: runs of a chunk of survivors, in order.

    Module-level and self-contained so it survives Windows spawn; touches
    no GPU, so workers never contend with the parent's device work."""
    forms, cap, ks = task
    return [sprp_run(int(k), forms, cap) for k in ks]


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


def _submit(pool, forms, cap, ks):
    """Hand a launch's survivors to the pool.  Returns [(ks_chunk, future)]
    in survivor order; with no pool the chunk is classified right here."""
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


# --------------------------------- campaign ---------------------------------

class Campaign:
    def __init__(self, args, ckpt=None, cursor=None, pool=None, evid=None):
        # `ckpt`/`cursor`/`pool` are overridable for ONE reason: so the
        # selftest can instantiate a campaign against a scratch file and
        # exercise the wiring -- checkpoint round trip, status line, census,
        # rungs -- without sweeping.  A launcher whose loop is only ever run
        # for real is a launcher whose first bug is the owner's to find.
        self.args = args
        self.fam = ref.family(args.family)
        self.oeis = self.fam
        # DRILLS ONLY (see DRILL_N): open below the published frontier, so
        # that the "find" a drill promotes on is a real published term.
        # No command-line flag sets this.
        self._known_top = (int(getattr(args, "start_n", 0) or 0) - 1
                           if getattr(args, "start_n", None)
                           else max(ref.KNOWN[self.fam]))
        self.key = config_key(self.fam)
        self.ckpt = ckpt or ckpt_path(self.fam)
        self.cursor = cursor or _POLICIES[self.fam]
        self.pool = pool
        # where evidence goes: the project's evidence/ -- or a scratch
        # directory, for the one drill that runs the real loop
        self.evid = evid or EVID
        self.ledger = (str(pathlib.Path(evid) / "ledger.json") if evid
                       else ledger_path(self.fam))
        self.found = {}                # str(n) -> k found by THIS campaign
        self.census = {}               # run length -> count
        self.passed = []
        self.elapsed = 0.0
        self.discoveries = 0
        self.near = 0
        self.survivors = 0             # classified this campaign
        self._stored_n = None          # the filter the cursor belongs to
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
        # the x below which THIS filter's least-claim rests on the previous
        # filter's classified sweep rather than on its own (follow_frontier);
        # the monotone floor until a promotion has happened
        self.cover_x = 0
        self._hw_ref = (0.0, time.time())
        self._hostbound_logged = False
        self._ckpt_t = 0.0             # when the last save landed
        self._ckpt_every_s = CKPT_MIN_S
        self._plog_t = 0.0             # when the last period line was logged
        self._plog_n = 0               # periods closed since it
        self._snapshot = None
        self._proof_logged = None      # the filter whose crossing was logged
        self._load_kind = None
        self.loaded = self.load()
        if self.loaded and self._load_kind != "own" and self.u:
            # a v2/v3 work cursor counts third-level residues of one period;
            # v4's counts launches of a segment.  Resume at the period.
            log("STAGE", f"inherited cursor: u = {self.u} was a third-level "
                         f"residue index of period {self.j}; v4 re-sweeps "
                         f"that period from its start (at most one period "
                         f"of device)")
            self.u = 0
        self.eng = self._build_engine(self.filter_n())
        # STORE THE UNIT NEXT TO THE NUMBER AND ASSERT IT ON LOAD
        # (OPTIMIZATION.md 2.9).  The config key DESCRIBES the plan, which is
        # documentation; this is the assertion -- and here it is load-bearing
        # rather than belt-and-braces, because the period really does change
        # from filter to filter (6e9 at n = 11, 6e17 from n = 16).
        if self._stored_n is not None and self._stored_n != self.filter_n():
            raise ValueError(
                f"{self.ckpt} holds a cursor for filter n = {self._stored_n} "
                f"but this campaign's next open term is a({self.filter_n()}): "
                f"the stored `found` and the stored filter disagree, so the "
                f"cursor cannot be read")
        if self._stored_w and self._stored_w != int(self.eng.W):
            raise ValueError(
                f"{self.ckpt} counts periods of W = {self._stored_w:,} but "
                f"this engine's period at n = {self.filter_n()} is "
                f"{int(self.eng.W):,}: the cursor means something else and "
                f"has to be re-denominated, not read")
        if self.j is None:
            self.j, self.u = self.floor_period(), 0
        self.boundary = self.j
        # `discoveries` is CUMULATIVE and restored by load(), so "have there
        # been any finds" is not "has THIS RUN found something" the moment a
        # resumed campaign has history.  --stop-on-discovery means the second
        # one, and it is latched where the find is confirmed.
        self._discoveries_at_start = self.discoveries
        self.mark_boundary()

    def _register(self):
        """Tell the oracle every term this campaign has found.  The form list
        of the open index is built from them, so this runs before ANY engine
        is built -- at start (from the checkpoint) and at every promotion --
        and it refuses a term that contradicts one already known."""
        for m in sorted(self.found, key=int):
            ref.register(self.fam, int(m), int(self.found[m]))

    def _settle(self, n, x):
        """a(n) = x, settled: `found` and the oracle move TOGETHER.

        `found` is what `frontier()`, `filter_n()` and `x_start()` read, so
        the moment it holds a(n) everything downstream asks the oracle for
        the conditions of index n + 1 -- which are built from a(n).  Set one
        without the other and the next `state()`, status line or ladder read
        is a KeyError: that ended the first real campaign seconds after it
        found a(18) (2026-09-19), between the find and `follow_frontier`.
        The drills could not see it, because on published ground the oracle
        holds the term already; `_unpublished` is what closed that."""
        ref.register(self.fam, int(n), int(x))
        self.found[str(int(n))] = int(x)

    def _build_engine(self, n):
        """The engine for filter n, PLANNED (never a stored constant)."""
        self._register()
        ok, q = ref.admissible(self.fam, n)
        if not ok:
            banner("MILESTONE", [
                f"{self.oeis} IS FINITE: at index {n} the conditions kill "
                f"EVERY residue class mod {q}",
                f"no x can satisfy them, so a({n - 1}) = "
                f"{ref.term(self.fam, n - 1):,} is the LAST term",
                "this is a theorem about the sequence, not an engine fault: "
                "check it by hand from clique_reference.forbidden_k_residues"])
            raise SystemExit(0)
        unit, p1, p2, p3, q2, pb = plan_for(self.fam, n)
        # the RECORD is the engine's own runtime decision from this plan
        return gpu.GpuEngine(n, self.fam, p1=p1, p2=p2, p3=p3, q2=q2,
                             unit=unit, pb=pb, seg_cap=pb)

    # ------------------------------------------------------------- frontier
    def frontier(self):
        """The largest n settled: the literature plus this campaign."""
        top = self._known_top
        for n in self.found:
            top = max(top, int(n))
        return top

    def frontier_k(self):
        n = self.frontier()
        return int(self.found.get(str(n), ref.KNOWN[self.fam].get(n, 0)))

    def filter_n(self):
        """The sieve filter is always the next OPEN term."""
        return self.frontier() + 1

    def x_start(self):
        """The floor of THIS filter's sweep -- the monotonicity bound, the
        frontier term itself.  Re-derived from the LIVE frontier on every
        call, so it follows a find the way the ladder does."""
        return x_floor(self.fam, self.filter_n(), self.frontier_k())

    def floor_period(self):
        """The period the floor sits in: where a fresh sweep of this filter
        starts.  The engine sweeps that period whole and clips at the
        floor."""
        return self.x_start() // int(self.eng.W)

    def k_min(self):
        """The clip for the segment being worked: the floor while the sweep
        is still inside the segment that contains it, none after."""
        st = self.x_start()
        return st if self.j * int(self.eng.W) <= st else None

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
        """The x from which the CLASSIFICATION at the current filter is a
        probable-prime chain rather than a proof (clique_search.k_proof)."""
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
                f"{self.oeis}) = {pc:.4g}: the largest value formed now "
                f"exceeds the deterministic Miller-Rabin "
                f"bound, so classification is a thirteen-base strong "
                f"probable-prime chain from here (the census is counted and "
                f"a NEAR is a health check either way) and a DISCOVERY is "
                f"proved value by value by huntlib.certificate.prove on "
                f"V - 1 and V + 1, which have no structure here (rule 5h's "
                f"exception: measured 12 of 12 to 1e40, re-measured by G10; "
                f"certify_run); the ceiling is x < "
                f"{cpu.k_ceil(self.filter_n(), self.fam):.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "plan": PLAN_VERSION,
                "family": self.fam,
                # THE FILTER IS PART OF THE CURSOR, not a derived quantity:
                # each n has its own wheel and period, so a cursor without
                # its filter is a number without a unit.
                "n": int(self.eng.n),
                "q2": int(self.eng.q2),
                "wheel": [self.eng.p1, self.eng.p2, self.eng.p3],
                "unit": int(self.eng.unit),
                "j": int(self.j),
                "u": int(self.u),
                "seg_periods": int(self.eng.seg_periods),
                "launches_per_segment": int(self.eng.launches_per_segment),
                "W": int(self.eng.W),
                # the COVERAGE claim: every k in [K_START, k) is swept.  It
                # is the period boundary, never the live (j, u) cursor,
                # because a part-swept period is not contiguous in k.
                "k": int(self.swept_k()),
                "k_start": int(self.x_start()),
                "cover_x": int(self.cover_x),
                # values classified inside the period still in progress.  A
                # crash must not lose them: they are only narrated once the
                # period closes and their k order becomes meaningful, so
                # between those two moments the checkpoint is where they live.
                "pending": [[int(k), int(r)] for k, r in self.pending],
                # COPIES, not references: a snapshot is held across the next
                # segment and written by an interrupt, and one that aliases
                # `found` acquires a find made AFTER it was taken -- filter n
                # beside found[n], which __init__ refuses (_promotion_drill)
                "found": dict(self.found),
                "census": {str(r): c for r, c in sorted(self.census.items())},
                "passed": list(self.passed),
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
        self._load_kind = kind
        self._stored_w = int(st.get("W", 0))
        self._stored_n = st.get("n")
        self.j = int(st["j"])
        self.u = int(st.get("u", 0))
        self.pending = [(int(k), int(r)) for k, r in st.get("pending", [])]
        self.cover_x = int(st.get("cover_x", 0))
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
        """A k for the HEARTBEAT inside a segment -- progress, not coverage:
        `un` launches of the segment starting at period `jn` are done."""
        return self.eng.progress_k(jn, un)

    def segment_end(self):
        """The first period after the segment being worked, clamped to the
        ceiling; equal to self.j when nothing is left to sweep."""
        jmax = cpu.k_ceil(self.filter_n(), self.fam) // self.eng.W
        return min(self.j + self.eng.seg_periods, jmax)

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
        seg = self.eng.seg_periods
        pct = min(100.0, max(0.0, 100.0 * (k - lo) / (seg * self.eng.W)))
        parts = [f"swept to {self.swept_k():.6g}",
                 f"periods [{self.boundary}, {self.boundary + seg}) "
                 f"[{lo:.5g}, {lo + seg * self.eng.W:.5g}) {pct:.0f}%",
                 f"{self.oeis} filter n = {self.filter_n()}"]
        if rate:
            parts.append(f"{rate:.3g} {TERM}/s")
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
            ok, legs, _ = verify(k, run, self.fam, witness=False,
                                 n=self.eng.n)
            if not ok:
                log("ALARM", f"NEAR value m = {k:,} run {run} failed "
                             f"verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at m = {k:,} (run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of a({frontier + 1})!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, x, run):
        frontier = self.frontier()
        n = self.eng.n
        # THE FIND IS RE-DERIVED BY THE ORACLE, against the whole prefix,
        # before anything is claimed: an error here would poison every later
        # term, because a(n) becomes part of the definition of a(n + 1).
        self.hb.doing(f"verifying run-{run} {TERM}={x}")
        if run != n or not ref.is_term(self.fam, x, n):
            log("ALARM", f"claimed a({n}) = {x} (run {run}) is not a term by "
                         f"the oracle: it must exceed a({n - 1}) and satisfy "
                         f"every condition of index {n}")
            raise SystemExit(2)
        ok, legs, _stop = verify(x, run, self.fam, n=n)
        if not ok:
            log("ALARM", f"claimed a({frontier+1}) = {x} failed the "
                         f"protocol: {legs}")
            raise SystemExit(2)
        settles = [n]
        self.hb.doing(f"certifying run-{run} {TERM}={x}")
        certs, unproved = certify_run(x, run, self.fam)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        also = also_settles(self.fam, x, run, settles)
        fs = ref.forms(self.fam, n)
        # The record speaks the OEIS entry's language (CONVENTIONS.md "Naming
        # in an evidence file").  These entries give the term no letter, so it
        # is carried under the entry's own wording, a(n), which is what
        # `forms` is written in; `oeis_terms` is literally what to submit.
        ev = {**evidence.header(self.oeis, ref.FAMILIES[self.fam]["forms"],
                                TERM, x, settles),
              "filter_n": int(n), "run": int(run), "settles": settles,
              # THE PREFIX THE CLAIM IS RELATIVE TO.  a(n) is only a(n) given
              # a(1..n-1), so the file carries them and says where each came
              # from; a reader can recompute every value below from these.
              "prefix": [int(t) for t in ref.terms(self.fam, n)],
              "prefix_found_by_this_campaign": sorted(int(m) for m in self.found),
              "conditions": [f"{a}*a(n) + {b}" if a != 1 else f"a(n) + {b}"
                             for a, b in fs],
              "values": {str(i + 1): int(a * x + b)
                         for i, (a, b) in enumerate(fs)},
              "verification": legs,
              # no stopper: a full run has nothing above it to fail (the form
              # that would decide index n + 1 is a(n) + this x + 1)
              "certificates": certs,
              # every proof above was re-verified from scratch before it
              # was accepted; `unproved` lists any i that has none
              "certificates_verified": not unproved,
              "unproved": unproved,
              "proof_routes": routes,
              "also_settles": also,
              "least_claim": {"swept_from": int(self.x_start()),
                              "swept_to": int(x),
                              "floor": f"a({n - 1}) = {self.frontier_k()}: the "
                                       f"definition requires a(n) > a(n-1)",
                              "filter": int(n),
                              "wheel": int(self.eng.W),
                              "sieve_depth": int(self.eng.q2),
                              "class": [int(self.eng.r0), int(self.eng.unit)]},
              "engine": self.key}
        self._settle(n, x)
        path = evidence.record(
            ev, self.evid, f"{self.oeis}_a{n}_{x}.json",
            self.ledger, key=TERM,
            label="%s a(%d)" % (self.oeis, n))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        lines = [
            f"{self.oeis} a({n}) = {x:,}",
            f"every one of its {len(fs)} conditions is prime: a({n}) + a(i) + 1 "
            f"for i = 1..{n - 1}" + ("".join(
                f", and {a}*a({n}) + {b}" if a != 1 else f", and a({n}) itself"
                for a, b in ref.extra(self.fam))),
            f"re-derived by the oracle against the whole prefix, verified 3 "
            f"ways, {proved} of {len(certs)} certificates re-verified "
            f"({', '.join(f'{r} x{c}' for r, c in sorted(routes.items()))}), "
            f"evidence {path}"]
        for a in also:
            lines.append(f"also settles {a['sequence']}({a['n']}) = "
                         f"{a['value']:,}")
        if unproved:
            lines.append(f"UNPROVED at i = {unproved}: those values passed "
                         f"the Miller-Rabin chain and BPSW but no certificate "
                         f"landed within the bounded effort -- the find "
                         f"stands on the three legs; certify them by hand "
                         f"from the evidence file")
        banner("DISCOVERY", lines)

    def follow_frontier(self):
        """After a find: rebuild the engine at the next open index and start
        it JUST ABOVE the term just found.

        The new index has one more condition -- a(n+1) + a(n) + 1 prime --
        and a(n) did not exist until a moment ago, so NOTHING the old filter
        classified says anything about it: the rest of the old segment is
        re-swept under the new filter, from the find.  (factorial-ladders
        carries the classified line across a promotion; that is sound there
        because its forms do not depend on the find.  Here it would be a
        coverage hole exactly one segment wide.)  The cost is at most one
        old segment, which the planner prices against the rate a longer
        segment buys (clique_gpu.plan).
        """
        old = self.eng
        self.cover_x = 0
        self.eng = self._build_engine(self.filter_n())
        self.j = self.floor_period()
        self.u = 0
        self.boundary = self.j
        self.pending = []
        log("STAGE",
            f"filter follows the frontier: n = {old.n} -> {self.eng.n} on the "
            f"same x line -- one more condition, built from the term just "
            f"found; the wheel ({old.p1},{old.p2},{old.p3}) becomes "
            f"({self.eng.p1},{self.eng.p2},{self.eng.p3}), the class x == "
            f"{old.r0} (mod {old.unit}) becomes x == {self.eng.r0} (mod "
            f"{self.eng.unit}), the depth {old.q2} becomes {self.eng.q2}, the "
            f"period {old.W:.4g} becomes {self.eng.W:.4g}, the segment "
            f"{old.seg_periods} -> {self.eng.seg_periods} periods on the "
            f"{'WIDE' if self.eng.wide else 'narrow'} survivor record; the "
            f"sweep restarts at x = {self.x_start():,}, just above the find "
            f"(the old filter never tested the new condition, so its sweep "
            f"past the find claims nothing); the ladder now aims at "
            f"a({self.filter_n()})")
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({m})")
                                  for m in self.found)]
        self._proof_logged = None
        self.check_proof_crossing(self.swept_k())
        # and the host's need moved with it: re-measure, re-size
        self.size_pool()
        self.mark_boundary()

    # ----------------------------------------------------------- the pool
    def line_per_launch(self):
        cfg = self.eng.config()
        return self.eng.R1 * self.eng.R2 * cfg["nu"] / self.eng.density()

    def calibrate(self):
        """MEASURE this configuration on the launches the loop is about to
        run: device k/s, survivors per second, host cost per survivor.
        Nothing is recorded -- the loop sweeps the same launches again.

        The line is taken off the cursor the sweep yields, so a segment
        shorter than the calibration window (one launch at n = 11, where
        the sweep runs on into the next segments until the time and sample
        floors are met) is measured as exactly the line it is."""
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
        cap = self.filter_n()
        forms = filter_forms(self.fam, cap)
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
            if cur[1]:                         # still inside the segment
                self.j, self.u = cur
            else:                              # the segment's last launch:
                self.u = 0                     # closed by the loop, below
                self._period_done = True

    # ---------------------------------------------------------------- loop
    def run(self):
        target = int(self.args.to or cpu.k_ceil(self.filter_n(), self.fam))
        log("STAGE", f"campaign {self.key}")
        log("STAGE", device_report(self.eng.bytes_held()))
        cfg = self.eng.config()
        log("STAGE",
            f"sweeping the x line to {target:.4g}; {self.oeis} "
            f"({ref.FAMILIES[self.fam]['forms']}) filter n = "
            f"{self.filter_n()}; wheel W = {self.eng.W:,} at unit "
            f"{self.eng.unit} ({self.eng.R:,} residues, {self.eng.R1} x "
            f"{self.eng.R2} x {self.eng.R3}, {100.0 * self.eng.density():.6f}% "
            f"of the line); a segment is {self.eng.seg_periods} periods "
            f"({self.eng.seg_periods * self.eng.W:.4g} of line) in "
            f"{self.eng.launches_per_segment} launches of "
            f"{cfg['cand_per_launch']:.3g} candidates ({cfg['nu']} "
            f"third-level residues x {cfg['tchunk']} first-level); resume at "
            f"period {self.j}, launch {self.u} (k = "
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
                     f"{self.proof_crossing():.4g} and a thirteen-base strong "
                     f"probable-prime chain above it; a DISCOVERY is proved "
                     f"value by value either way (certify_run: the "
                     f"deterministic test below the bound, "
                     f"huntlib.certificate.prove on the unstructured V - 1 / "
                     f"V + 1 above it), and the engine ceiling {target:.4g} "
                     f"is where that was measured to succeed on 12 of 12 "
                     f"random primes (huntlib.ceiling.subproof_rate; G10)")
        self.check_proof_crossing(self.swept_k())
        self.size_pool()
        self.hb.mark(self.u_progress(self.j, self.u))
        self.hb.start(self.status_line)
        shutdown.on_interrupt(self._on_interrupt)
        stop_now = False
        cap = self.filter_n()
        forms = filter_forms(self.fam, cap)
        self._plog_t = time.time()
        try:
            while self.swept_k() < target and not stop_now:
                j1 = self.segment_end()         # ONE SEGMENT of periods
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
                                     _submit(self.pool, forms, cap,
                                             surv)))
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
                # The period is closed, so its values are contiguous in k
                # again and the LEAST of them is meaningful.  Nothing is
                # narrated before this point.
                held = len(self.pending)
                found_now = False
                for k, r in sorted(self.pending):
                    found_now = self.handle(k, r) or found_now
                    if found_now:
                        # everything past the find in this segment was
                        # classified WITHOUT the condition the find creates;
                        # it is dropped uncounted and re-swept under the new
                        # filter (follow_frontier restarts at the find)
                        break
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
                        f"run >= {CENSUS_FLOOR} classified in k order"
                        + (f"; {self._plog_n} segments closed since the last "
                           f"such line" if self._plog_n > 1 else "") + ")")
                    self._plog_t, self._plog_n = time.time(), 0
                if found_now:
                    # NO SNAPSHOT IS TAKEN HERE.  Between the find and the
                    # promotion the campaign is in two minds -- `found` says
                    # index n + 1, the engine and (j, W) say n -- and a
                    # checkpoint of that state is one `__init__` REFUSES
                    # (stored filter != open index).  An interrupt inside
                    # follow_frontier therefore writes the snapshot it
                    # already holds, the last boundary BEFORE the find: one
                    # segment redone, the find made again, its evidence
                    # rewritten in place (huntlib.evidence.record upserts).
                    # follow_frontier ends with the first coherent snapshot
                    # of the new index.
                    self.follow_frontier()
                    cap = self.filter_n()
                    forms = filter_forms(self.fam, cap)
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
        log("STAGE", f"campaign stopped at {TERM} = {self.swept_k():,} "
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
                    f"to {TERM} = {int(snap['k']):,} ({self.ckpt})")
        return (f"{self.ckpt} is held open by another process, so THIS "
                f"boundary (period {int(snap['j'])}, u = {int(snap['u'])}) "
                f"was not written; the run resumes from the last save that "
                f"landed")


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """All four outcomes of the taxonomy, on this project's mathematics.  The
    run is in index units (clique_reference.run_length): at filter n = 11 a
    full run is 11 and one condition short is 10."""
    return [((11, 10), "DISCOVERY"),      # a full run at the open index
            ((10, 10), "NEAR"),           # one condition short of a(11)
            ((9, 10), "CENSUS"),          # below the frontier: counted only
            ((8, 10), "CENSUS"),          # the census floor itself
            ((7, 10), None),              # under the floor: not even counted
            ((0, 10), None)]              # an extra form failed


# The canaries: published terms a mini-hunt reaches from their predecessor in
# a second or two, at the index each belongs to, in x space AND in class
# space (the stream that sweeps t with x = r + unit*t must find the same
# first x).  Every family, and both extra forms.
_CANARIES = (("A093483", 13, 1), ("A093483", 13, 6), ("A103828", 12, 30),
             ("A037100", 14, 6), ("A119752", 12, 6), ("A119751", 11, 1),
             ("A119751", 11, 30), ("A133761", 10, 30))


def _canary_hunt():
    """The stream must organically rediscover known terms, in every family.

    Dedicated mini-hunts at the index those terms belong to -- the production
    filter cannot rediscover them (a(13) has a run of 13 and an n = 18 wheel
    is entitled to kill it) -- sweeping from just above a(n-1), which is the
    definition's own floor, so "FIRST occurrence" is a claim about the line
    and not about a window.
    """
    hits_all = []
    for fam, n, unit in _CANARIES:
        if cpu.forced_unit(n, fam) % unit:
            return False, (f"CANARY FAIL: unit {unit} is not forced at "
                           f"n = {n} of {fam}, so the canary would sweep a "
                           f"thinner line than it claims")
        want = ref.KNOWN[fam][n]
        eng = gpu.GpuEngine(n, fam, p1=13, p2=None, p3=None, q2=4096,
                            unit=unit)
        lo = max(ref.KNOWN[fam][n - 1], cpu.k_floor(4096, n, fam)) + 1
        ceng = cpu.CpuEngine(n, fam, q2=4096)
        surv = eng.survivors_j(lo // eng.W, want // eng.W + 1, k_min=lo)
        hits = [int(k) for k in surv if ceng.run_length(int(k)) >= n]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: {fam} filter n={n} unit={unit} "
                           f"found x = {min(hits) if hits else None}, "
                           f"expected a({n}) = {want}")
        hits_all.append(f"{fam} a({n})" + (f" (class mod {unit})"
                                           if unit > 1 else ""))
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as FIRST occurrences above their "
                  "predecessors, each at its own index -- in x space and in "
                  "class space, every family, both extra forms")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on every family."""
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        ok, legs, stop = verify(x, top, fam)
        if not ok or stop is not None or not ref.is_term(fam, x, top):
            return False, (f"PROTOCOL FAIL: genuine a({top}) = {x} ({fam}) "
                           f"rejected: {legs}")
        # a fake claim: a non-term offered as a full run
        bad, legs_b, _ = verify(x + 30, top, fam)
        if bad or ref.is_term(fam, x + 30, top):
            return False, (f"PROTOCOL FAIL: fake a({top}) = {x + 30} ({fam}) "
                           f"ACCEPTED ({legs_b})")
        # AN EARLIER TERM IS NOT A LATER ONE.  In the families that carry
        # 2x + 1 an earlier term satisfies EVERY condition of a later index
        # (a clique is a clique in any order, and 2a + 1 is its own extra
        # form), so what rejects it is the ordering, and only the ordering.
        if ref.is_term(fam, ref.KNOWN[fam][top - 1], top):
            return False, (f"PROTOCOL FAIL: {fam}: a({top - 1}) accepted as "
                           f"a({top}); the definition says a(n) > a(n-1)")
        # ONE SHORT, with a factor witness for the composite that stops it:
        # the first x above a(8) compatible with a(1..7) and not with a(8)
        # -- a rival candidate for a(8) that lost on size -- found by the
        # CPU engine at index 8 and read by the oracle at index 9, above
        # the exception zone of the re-sieve leg
        n = 9
        lo = max(ref.KNOWN[fam][n - 1], 10 ** 5) + 1
        rivals = [k for k, _ in cpu.CpuEngine(n - 1, fam, q2=256).hunt(
            lo, lo + 3 * 10 ** 7) if ref.run_length(fam, k, n) == n - 1]
        if not rivals:
            return False, f"PROTOCOL FAIL: {fam}: no one-short value to drill"
        x7 = rivals[0]
        ok, legs, stop = verify(x7, n - 1, fam, n=n)
        if not ok or stop["i"] != n - 1 or \
                stop["value"] != x7 + ref.KNOWN[fam][n - 1] + 1:
            return False, (f"PROTOCOL FAIL: {fam}: the one-short value x = "
                           f"{x7} at index {n} came out {legs}, {stop}")
        if stop["factor"] is None or stop["value"] % stop["factor"] or \
                stop["factor"] in (1, stop["value"]):
            return False, f"PROTOCOL FAIL: {fam}: the witness is not a factor"
        if verify(x7, n, fam)[0]:
            return False, (f"PROTOCOL FAIL: {fam}: x = {x7} accepted as a full "
                           f"run of {n}")
        # the derived claims come out as the identities say, and agree with
        # every published derived term
        for seq, mul, shift in ref.FAMILIES[fam]["also"]:
            pub = ref.KNOWN_ALSO[seq]
            for m in range(1, len(pub) + 1):
                got = [r for r in also_settles(fam, ref.KNOWN[fam][m], m, [m])
                       if r["sequence"] == seq]
                if len(got) != 1 or got[0]["value"] != pub[m - 1] or \
                        got[0]["n"] != m:
                    return False, (f"PROTOCOL FAIL: {seq}({m}) came out "
                                   f"{got}, published {pub[m - 1]}")
    if also_settles("A037100", 4, 1, [1]) or also_settles("A133761", 5, 1, [1]):
        return False, "PROTOCOL FAIL: a family claims a rider it does not have"
    return True, ("protocol ok, every family: each frontier term accepted as a "
                  "full run (which has no stopper) and as a term by the "
                  "oracle; a non-term offered as a full run rejected; an "
                  "EARLIER term offered as a later one rejected by the "
                  "ordering (in the 2x + 1 families it satisfies every other "
                  "condition); a one-short value accepted with a factor "
                  "witness for the composite that stops it and rejected as a "
                  "full run; and every derived claim (A180565, A115760, "
                  "A128933, A120403, A113875) reproduces its published table")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing."""
    raised = []
    eng = gpu.GpuEngine(12, "A093483", p1=13, p2=None, p3=None, q2=1024)
    ceil = cpu.k_ceil(12, "A093483")
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
        eng.sweep(0, 2, k_min=cpu.k_floor(1024, 12, "A093483"))
        return False, "CEILING FAIL: a clip AT the floor was accepted"
    except ValueError:
        raised.append("gpu k_min <= floor")
    c = cpu.CpuEngine(12, "A093483", q2=1024)
    try:
        c.survivors(10 ** 5, cpu.k_ceil(12, "A093483") + 10)
        return False, "CEILING FAIL: the CPU engine swept past k_ceil"
    except ValueError:
        raised.append("cpu k_ceil")
    # every family shares ONE ceiling (clique_search.k_ceil): huntlib's
    # K_CEIL, above every crossing, enforced by both engines -- and tight:
    # the last whole period under it sweeps (checked, not swept), the next
    # raises
    if cpu.k_ceil(15, "A093483") != ceiling.K_CEIL or \
            cpu.k_ceil(15, "A037100") != ceiling.K_CEIL or \
            not cpu.k_proof(15, "A093483") < cpu.k_ceil(15, "A093483") or \
            not cpu.k_proof(15, "A037100") < cpu.k_ceil(15, "A037100"):
        return False, ("CEILING FAIL: the family ceilings are not the "
                       "one K_CEIL G10 pins")
    engm = gpu.GpuEngine(12, "A037100", p1=13, p2=None, p3=None, q2=1024)
    ceilm = cpu.k_ceil(12, "A037100")
    try:
        engm.sweep(ceilm // engm.W - 1, ceilm // engm.W + 2)
        return False, "CEILING FAIL: a second family's engine swept past K_CEIL"
    except ValueError:
        raised.append("gpu k_ceil (a second family, at K_CEIL)")
    jc = ceilm // engm.W
    engm._check_window(jc - 1, jc, None)        # the last period under it
    try:
        engm._check_window(jc, jc + 1, None)
        return False, "CEILING FAIL: the first period past K_CEIL was accepted"
    except ValueError:
        raised.append("gpu k_ceil tight to one period")
    try:
        cpu.CpuEngine(12, "A037100", q2=1024).survivors(10 ** 5, ceilm + 10)
        return False, "CEILING FAIL: a second family's CPU engine swept past K_CEIL"
    except ValueError:
        raised.append("cpu k_ceil (a second family)")
    # The floor BITES at every filter here: every value is at least x, so
    # a sieve to q2 is valid only from x > q2.
    lowf = cpu.k_floor(1024, 12, "A093483")
    if lowf < 1000:
        return False, (f"CEILING FAIL: the n = 12 floor is {lowf}, so the "
                       f"floor check is vacuous")
    try:
        c.survivors(lowf, lowf + 10 ** 5)
        return False, "CEILING FAIL: the CPU engine swept at the floor"
    except ValueError:
        raised.append("cpu floor (n = 12, floor = %d)" % lowf)
    try:
        gpu.wheel(7, "A093483", 53)          # a flat wheel far past RES_MAX
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(15, "A093483", p1=31, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    try:
        gpu.GpuEngine(7, "A093483", p1=13, p2=37, p3=None, q2=4096)
        return False, "CEILING FAIL: an oversized second level was accepted"
    except ValueError:
        raised.append("gridDim.y")
    try:
        gpu.GpuEngine(gpu.NRES_MAX + 2, "A093483", p1=13, p2=None,
                      p3=None, q2=1024)
        return False, ("CEILING FAIL: a filter longer than the tail's "
                       "residue list was accepted")
    except ValueError:
        raised.append("nforms <= NRES_MAX")
    # AN INDEX WHOSE PREFIX DOES NOT EXIST HAS NO FILTER: the form list of
    # a(n) is built from a(1..n-1), so neither engine may be built two past
    # the frontier -- it would have to invent a term
    for build in (gpu.GpuEngine, cpu.CpuEngine):
        try:
            build(ref.frontier("A093483") + 2, "A093483")
            return False, ("CEILING FAIL: an engine was built at an index "
                           "whose prefix is not known")
        except KeyError:
            raised.append(f"{build.__name__} past the known prefix")
    try:
        ref.register("A093483", 17, ref.KNOWN["A093483"][17] + 6)
        return False, "CEILING FAIL: a published term was re-registered"
    except ValueError:
        raised.append("register refuses to change a term")
    for unit in (30, 10, 12):
        try:
            gpu.GpuEngine(15, "A093483", p1=13, p2=None, p3=None, q2=1024,
                          unit=unit)
            return False, (f"CEILING FAIL: unit {unit}, which nothing forces "
                           f"here, was accepted")
        except ValueError:
            raised.append(f"unit {unit} refused")
    try:
        gpu.GpuEngine(15, "A000001", p1=13, p2=None, p3=None, q2=1024)
        return False, "CEILING FAIL: an unknown family was accepted"
    except KeyError:
        raised.append("family")
    return True, ("ceiling ok: %s all raise rather than compute" %
                  ", ".join(raised))


def _prime_value_near(fam, n, x0, tries=4000):
    """(x, i): the first x >= x0 in the forced class whose i-th condition
    (1-based, clique_reference.forms order) is a probable prime -- a drill at
    an arbitrary height has to take the value it is given."""
    r, u = cpu.forced_class(n, fam)
    fs = ref.forms(fam, n)
    x = int(x0) - int(x0) % u + r
    for _ in range(tries):
        x += u
        for i, (a, b) in enumerate(fs):
            v = a * x + b
            if sprp_base2(v) and mr_is_prime(v):
                return x, i + 1
    return None, None


def _certificate_drill():
    """A discovery past the proof crossing is PROVED, not just tested -- and
    here that is rule 5h's EXCEPTION, so it is drilled AT the ceiling.

    The values are x + a(i) + 1, 2x + 1 and x: V - 1 has no structure, and
    nothing about x factors it.  Below the crossing (about 1.66e24 and
    3.3e24, above every term the campaign can reach in weeks) every
    certificate takes the deterministic route.  Above it each value is
    proved on its own by huntlib.certificate.prove -- V - 1 or V + 1
    factored by bounded rho and ECM, a subproof for any prime factor past
    the bound.  Whether that WORKS at a given height is an empirical
    question, which is why the ceiling here rests on a measurement
    (clique_search, G10) and why this drill repeats it on the project's own
    values: every sampled value at K_CEIL must be proved, the proof must
    re-verify, refuse a neighbouring N, and carry a subproof that cannot be
    stripped whenever a factor sits past the bound.
    """
    parts = []
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        certs, unproved = certify_run(x, top, fam)
        if unproved or len(certs) != ref.nforms(fam, top):
            return False, (f"CERTIFICATE FAIL: {fam} a({top}) left "
                           f"{unproved} unproved ({len(certs)} certificates)")
        if any(c.get("proof") != "deterministic-mr" for c in certs.values()):
            return False, ("CERTIFICATE FAIL: a value under the bound took "
                           "the certificate route")
    parts.append("every family's frontier term takes the deterministic route "
                 "on all its values and re-verifies")
    t0 = time.time()
    heights = (("just past the crossing", lambda f, n: cpu.k_proof(n, f) * 3),
               ("at the ceiling", lambda f, n: ceiling.K_CEIL // 3))
    stripped = 0
    for label, height in heights:
        proved = 0
        for fam in ref.FAMILIES:
            n = ref.frontier(fam) + 1
            x0 = height(fam, n)
            for rep in range(2):
                xx, i = _prime_value_near(fam, n, x0 + rep * 10 ** 12)
                if xx is None or xx >= cpu.k_ceil(n, fam):
                    return False, (f"CERTIFICATE FAIL: no {fam} value "
                                   f"{label} is a probable prime")
                certs, unproved = certify_run(xx, n, fam, only=(i,))
                c = certs.get(str(i))
                if unproved or c is None or c.get("proof") == "deterministic-mr":
                    return False, (f"CERTIFICATE FAIL: {fam} condition {i} at "
                                   f"x = {xx:.4g} ({label}) was not proved by "
                                   f"certificate: {c and c.get('proof')}")
                N = int(c["N"])
                if N != ref.values(fam, xx, n)[i - 1] or N < MR_VALID_BELOW:
                    return False, "CERTIFICATE FAIL: the proof is not about the value"
                if not certificate.verify(c)[0]:
                    return False, (f"CERTIFICATE FAIL: the {c['proof']} proof "
                                   f"{label} does not re-verify")
                if certificate.verify(dict(c, N=N + 2))[0]:
                    return False, "CERTIFICATE FAIL: verified for a neighbouring N"
                if certificate.verify({"proof": "deterministic-mr", "N": N})[0]:
                    return False, ("CERTIFICATE FAIL: a deterministic-MR claim "
                                   "past the bound was accepted as a proof")
                if c.get("subproofs"):
                    if certificate.verify({k: v for k, v in c.items()
                                           if k != "subproofs"})[0]:
                        return False, ("CERTIFICATE FAIL: a proof stripped of "
                                       "its subproof still verified")
                    stripped += 1
                proved += 1
        parts.append(f"{proved} of {proved} sampled values {label} (two per "
                     f"family, each the first probable-prime condition in the "
                     f"forced class) are proved by certificate on an "
                     f"UNSTRUCTURED V -+ 1, re-verify, and are refused for "
                     f"N + 2 and as a bare MR claim")
    if not stripped:
        return False, ("CERTIFICATE FAIL: no sampled proof needed a subproof, "
                       "so the recursion was not exercised")
    parts.append(f"{stripped} of them carry a subproof for a prime factor past "
                 f"the bound, which cannot be stripped; all of it took "
                 f"{time.time() - t0:.1f} s")
    return True, "certificates ok: " + "; ".join(parts)


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly, on every kernel
    and across the seams a real interrupt leaves: a period boundary, the
    (j, u) sub-period cursor, and the clipped period 0."""
    total = 0
    for lab, fam, kw, j_at, span, cut in (
            # The spans are lcm-ladders', which sized them for a weak wheel;
            # this wheel is stronger per prime, so the windows hold fewer
            # survivors than theirs did and the drill is cheaper, not
            # vacuous (asserted below).
            ("one-level", "A037100", dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 1200, 457),
            ("two-level", "A093483", dict(p1=19, p2=31, p3=None, q2=8192,
                                          unit=6, pb=32),
             10 ** 15, 3, 1),
            ("three-level", "A037100", dict(p1=13, p2=17, p3=19, q2=128,
                                            pb=32),
             9 * 10 ** 14, 600, 211)):
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

    # THE (j, u) SEAM: sweeping the launches [0, c) of a segment and then
    # [c, all) must give the same set as sweeping the segment whole -- and
    # in the segment that starts at PERIOD 0 with the clip, which is where
    # every campaign's first interrupt will land.  nu is forced below R3 so
    # the segment really is cut into launches; in k space and in UNIT space
    # -- the campaigns' engine, sweeping t with x = r + 6t -- where a period
    # is 6 times a t period and the seam must still close.
    # pb = 32 so a SEGMENT is 32 periods rather than 224: the seam is what
    # is under test, and a whole production segment of this wheel is 1.4e11
    # candidates.  G15 pins the stream's independence from pb.
    for eng in (gpu.GpuEngine(15, "A037100", p1=11, p2=17, p3=23, q2=128,
                              nu=4, pb=32),
                gpu.GpuEngine(16, "A093483", p1=11, p2=19, p3=29, q2=128,
                              nu=8, unit=6, pb=32)):
        nl = eng.launches_per_segment
        if nl < 4:
            return False, "RESUME FAIL: the seam engine has no sub-segment cursor"
        seg = eng.seg_periods
        for j0, k_min in ((eng.j_of(9 * 10 ** 14), None),
                          (0, 10 ** 6)):
            whole = sorted(eng.survivors_j(j0, j0 + seg, k_min=k_min))
            if not whole:
                return False, (f"RESUME FAIL: the (j, u) seam window is empty "
                               f"(unit {eng.unit}, period {j0})")
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
                                   f"{stopped} (segment at period {j0}, unit "
                                   f"{eng.unit}) loses or repeats values: "
                                   f"{len(part)} vs {len(whole)}")
            total += len(whole)
    return True, (f"resume ok: split sweep == unsplit sweep on all three "
                  f"kernels (segment boundaries and partial segments "
                  f"included), across the (j, u) sub-segment seam in k "
                  f"space and in unit space, and inside the clipped "
                  f"segment at period 0 on both ({total} survivors across "
                  f"the seams)")


def _classification_drill():
    """The two-pass screen == the all-bases chain on real survivors, and the
    pool's chunked answer == the serial one -- with the form list CARRIED IN
    THE TASK, because a pool worker is another process and knows nothing of
    the terms a campaign has found."""
    fam, n = "A037100", 10
    # 150 periods of the (13],(23] wheel at n = 10 is 3.3e10 of line, which
    # at that density and sieve depth is a few thousand survivors
    eng = gpu.GpuEngine(n, fam, p1=13, p2=23, p3=None, q2=4096)
    j0 = eng.j_of(10 ** 13)
    surv = eng.survivors_j(j0, j0 + 150)
    if len(surv) < 3 * CHUNK:
        return False, (f"CLASSIFY FAIL: only {len(surv)} survivors -- the "
                       f"drill cannot span several chunks")
    forms = filter_forms(fam, n)
    two = [sprp_run(k, forms, n) for k in surv]
    ceng = cpu.CpuEngine(n, fam, q2=64)
    full = [ceng.run_length(k) for k in surv]         # the full set, always
    if two != full:
        i = next(i for i in range(len(surv)) if two[i] != full[i])
        return False, (f"CLASSIFY FAIL: two-pass sprp gave run {two[i]} and "
                       f"the all-bases chain {full[i]} at x = {surv[i]}")
    with _pool_factory(2) as pool:
        parts = _submit(pool, forms, n, surv)
        got = [r for ks, f in parts for r in f.result()]
    if got != full:
        return False, "CLASSIFY FAIL: the pool's chunked result differs"
    # the run is capped at `cap`, a published term is FULL at its own index,
    # and an extra form that fails reads 0 however many shifts would pass
    for f in ref.FAMILIES:
        top = max(ref.KNOWN[f])
        x = ref.KNOWN[f][top]
        fs = filter_forms(f, top)
        if sprp_run(x, fs, top) != top or sprp_run(x, fs, 9) != 9:
            return False, (f"CLASSIFY FAIL: {f} a({top}) does not read {top} "
                           f"at its own index and 9 under a cap of 9")
    fs = filter_forms("A119752", 12)
    x = ref.KNOWN["A093483"][13]          # passes A119752's shifts? no matter:
    while mr_is_prime(2 * x + 1):         # find an x whose 2x + 1 is composite
        x += 6
    if sprp_run(x, fs, 12) != 0:
        return False, ("CLASSIFY FAIL: an x whose extra form 2x + 1 is "
                       "composite did not read run 0")
    return True, (f"classification ok: two-pass sprp == all-bases chain on "
                  f"{len(surv)} real survivors (max run {max(full)}), "
                  f"{len(parts)} pool chunks reassemble to the serial answer "
                  f"with the form list carried in each task, every frontier "
                  f"term reads full at its own index and capped under a "
                  f"smaller cap, and a failed extra form reads 0")


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


def _args_for(fam, **over):
    """A namespace shaped like the parsed args, for a drill campaign."""
    class _A:
        pass
    a = _A()
    d = dict(family=fam, fresh=False, to=None, stop_on_discovery=False,
             heartbeat=30.0, gpu_yield_ms=0.0, status=False, selftest=False,
             workers=1, worker_ramp=WORKER_RAMP_S, start_n=None)
    d.update(over)
    for k, v in d.items():
        setattr(a, k, v)
    return a


# The index the drill campaigns OPEN at.  A drill may not fabricate a find:
# a term becomes part of the definition of every later index, the oracle
# refuses to have one changed, and a fake one would sit in its tables (and in
# every cache keyed on them) for the rest of the battery.  So a drill
# campaign is started BELOW the published frontier (`start_n`) and "finds"
# the real published term, which the oracle already holds.
DRILL_N = 13                  # a(12) is past the planned sieve depth (2^20) in every family


@contextlib.contextmanager
def _unpublished(fam, n0):
    """Hide a(n0), a(n0 + 1), ... from the oracle while a drill runs.

    "Which the oracle already holds" (above) is a BLIND SPOT as well as a
    safeguard: on published ground `ref.term` answers from KNOWN whether or
    not the launcher ever registered its find, so every path that reads the
    new frontier BEFORE the find is registered is green in the drill and a
    KeyError at the real frontier.  The first real campaign died exactly
    there -- a(18) found, verified and evidenced, then a boundary snapshot
    taken between `found` moving and `register` running (2026-09-19), with
    47 of 47 gates green.  Inside this block the oracle knows what a
    campaign at the real frontier knows: the prefix below n0 and nothing
    else, so the find reaches it through `register` or not at all.  Nothing
    is fabricated -- what gets registered are the real published terms --
    and the tables are put back as they were on the way out."""
    fam = ref.family(fam)
    held = {n: ref.KNOWN[fam].pop(n)
            for n in sorted(ref.KNOWN[fam]) if n >= int(n0)}
    try:
        yield held
    finally:
        for n in held:
            ref._RUNTIME[fam].pop(n, None)
        ref.KNOWN[fam].update(held)     # in place: the table is shared


def _promotion_drill():
    """A FIND MOVES THE FILTER, and the sweep RESTARTS JUST ABOVE THE FIND.

    The new index has one more condition, built from the term just found,
    so nothing the old filter classified past the find says anything about
    it.  factorial-ladders carries the classified line across a promotion;
    here that would be a coverage hole one segment wide, and this drill is
    what stands between the inherited launcher and that hole.

    What is asserted, on a scratch checkpoint, in every family, with the
    REAL published term as the find (see DRILL_N):
      * promoting rebuilds the engine at the new index with exactly one
        more condition, in a forced class that is still admissible;
      * the cursor lands on the period that holds the find, clipped just
        above it -- NOT at the end of the line the old filter swept, however
        far that was -- with no carried coverage;
      * the new floor is the find plus one, the ladder retires the rungs of
        the term that was found, and the oracle now holds the term;
      * the checkpoint round-trips at the new index and reloads to the same
        place, in a process that must re-register the find to build its
        engine at all;
      * and a cursor stored at ONE index is REFUSED by a campaign whose
        frontier puts it at another (OPTIMIZATION.md 2.9).
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="clique-promote-")
    path = str(pathlib.Path(tmp) / "c.json")
    rows = []
    for fam in ref.FAMILIES:
        found_x = ref.KNOWN[fam][DRILL_N]            # the real a(n0)
        # the oracle is HIDDEN the term for the whole promotion, so it can
        # only come to hold it the way it does at the real frontier
        with _unpublished(fam, DRILL_N):
            ok, row = _promote_one(fam, DRILL_N, found_x, path)
        if not ok:
            return False, row
        rows.append(row)
    return True, ("promotion ok: " + "; ".join(rows) + " -- in every family "
                  "the engine is rebuilt with exactly one more condition (the "
                  "real published term standing in as the find, HIDDEN from "
                  "the oracle until the campaign settles it), an interrupt "
                  "between the find and the promotion writes a checkpoint "
                  "that still opens, the sweep "
                  "restarts on the period that holds the find and clips just "
                  "above it, NOT at the end of the old filter's sweep, "
                  "nothing is carried, the oracle holds the term, the cursor "
                  "round-trips, and a cursor stored at the wrong index is "
                  "REFUSED")


def _promote_one(fam, n0, found_x, path):
    """One family's promotion, for `_promotion_drill`: (ok, row or failure)."""
    pol = _POLICIES[fam].at(path)
    c = Campaign(_args_for(fam, start_n=n0), ckpt=path, cursor=pol)
    before = (c.eng.n, c.eng.unit, c.eng.W, c.eng.q2,
              (c.eng.p1, c.eng.p2, c.eng.p3), c.eng.nforms, c.eng.r0)
    if c.filter_n() != n0 or c.j != c.floor_period() or \
            c.x_start() != ref.KNOWN[fam][n0 - 1] + 1:
        return False, (f"PROMOTION FAIL: {fam} drill campaign did not "
                       f"open at index {n0}, just above a({n0 - 1})")
    if ref.term(fam, n0, missing=None) is not None:
        return False, (f"PROMOTION FAIL: {fam} a({n0}) is visible to the "
                       f"oracle before the campaign settled it, so this "
                       f"drill cannot see an unregistered find")
    c._settle(n0, found_x)           # what record_discovery does
    # THE WINDOW BETWEEN THE FIND AND THE PROMOTION.  `found` says index
    # n0 + 1 and the engine says n0; everything the loop and the
    # heartbeat thread read here has to answer (it was a KeyError at the
    # real frontier), and an interrupt here must leave a checkpoint that
    # OPENS -- the held boundary, one segment behind, never a snapshot
    # of the two-minded state, which __init__ refuses.
    c.state()
    c.status_line()
    if not c.save_boundary():
        return False, f"PROMOTION FAIL: {fam}'s in-window save did not land"
    try:
        w = Campaign(_args_for(fam, start_n=n0), ckpt=path,
                     cursor=_POLICIES[fam].at(path))
    except ValueError as e:
        return False, (f"PROMOTION FAIL: {fam}: an interrupt between the "
                       f"find and the promotion wrote a checkpoint the "
                       f"campaign refuses: {e}")
    if w.filter_n() != n0 or w.found or w.j != c.j:
        return False, (f"PROMOTION FAIL: {fam}: the in-window checkpoint "
                       f"reopened at filter {w.filter_n()}, period {w.j} "
                       f"with found = {w.found}; expected the boundary "
                       f"before the find")
    # the old filter swept well past the find before its segment closed
    c.boundary = c.j + 5 * c.eng.seg_periods
    swept_old = c.boundary * c.eng.W
    c.follow_frontier()
    if c.eng.n != n0 + 1 or c.eng.nforms != before[5] + 1:
        return False, (f"PROMOTION FAIL: {fam} did not move to n = {n0+1} "
                       f"with one more condition")
    cpu.assert_unit(n0 + 1, fam, c.eng.unit)
    if c.eng.r0 != cpu.unit_residue(n0 + 1, fam, c.eng.unit):
        return False, f"PROMOTION FAIL: {fam}'s class did not follow the filter"
    if c.x_start() != found_x + 1:
        return False, (f"PROMOTION FAIL: {fam}'s new floor is "
                       f"{c.x_start()}, not the find plus one")
    if c.u != 0 or c.j != c.floor_period() or c.boundary != c.j or \
            c.j != (found_x + 1) // c.eng.W or c.cover_x != 0:
        return False, (f"PROMOTION FAIL: {fam} resumed at (j, u) = "
                       f"({c.j}, {c.u}), boundary {c.boundary}, carried "
                       f"coverage {c.cover_x}; expected the period that "
                       f"holds the find, {(found_x + 1) // c.eng.W}, and "
                       f"nothing carried")
    if swept_old > found_x and c.j * c.eng.W >= swept_old:
        return False, (f"PROMOTION FAIL: {fam} resumed at the end of the "
                       f"OLD filter's sweep ({swept_old}), skipping "
                       f"({found_x}, {swept_old}) -- which the old filter "
                       f"never tested against the new condition")
    if c.k_min() != found_x + 1:
        return False, (f"PROMOTION FAIL: {fam}'s clip is {c.k_min()}, not "
                       f"just above the find")
    if ref.term(fam, n0) != found_x or c.pending:
        return False, f"PROMOTION FAIL: {fam}: the oracle does not hold the find"
    if any(p_.startswith(f"a({n0})") for p_ in c.passed):
        return False, f"PROMOTION FAIL: {fam} kept a retired rung"
    # round trip at the new index
    if not c.save():
        return False, f"PROMOTION FAIL: {fam}'s post-promotion save did not land"
    # a NEW process has an oracle that never heard of the find: the
    # reload has to put it back from the checkpoint's `found`
    ref._RUNTIME[fam].pop(n0, None)
    c2 = Campaign(_args_for(fam, start_n=n0), ckpt=path,
                  cursor=_POLICIES[fam].at(path))
    if ref.term(fam, n0, missing=None) != found_x:
        return False, (f"PROMOTION FAIL: {fam} reloaded without "
                       f"re-registering a({n0}) from the checkpoint")
    if (c2.filter_n(), c2.j, c2.u, c2.eng.nforms) != \
            (n0 + 1, c.j, 0, c.eng.nforms):
        return False, (f"PROMOTION FAIL: {fam} reloaded at "
                       f"({c2.filter_n()}, {c2.j}, {c2.u}), not "
                       f"({n0+1}, {c.j}, 0)")
    # ... and a cursor whose stored filter disagrees with the frontier is
    # REFUSED rather than read against the wrong plan
    import json as _json
    with open(path) as fh:
        st = _json.load(fh)
    st["n"] = n0                      # stale filter, fresh `found`
    checkpoint.save(path, st)
    try:
        Campaign(_args_for(fam, start_n=n0), ckpt=path,
                 cursor=_POLICIES[fam].at(path))
        return False, (f"PROMOTION FAIL: {fam} read a cursor stored at "
                       f"index {n0} while hunting a({n0+1})")
    except ValueError:
        pass
    os.remove(path)
    for ext in (".bak",):
        if os.path.exists(path + ext):
            os.remove(path + ext)
    return True, (f"{fam} n = {n0} -> {n0+1}: wheel {before[4]} -> "
                  f"({c.eng.p1},{c.eng.p2},{c.eng.p3}), class {before[6]} "
                  f"(mod {before[1]}) -> {c.eng.r0} (mod {c.eng.unit}), "
                  f"period {before[2]:.3g} -> {c.eng.W:.3g}")


def _other_families_cursor_drill(fam):
    """Every OTHER family's policy, put in front of every key it declares."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="fladder-cursor-")
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
    # every rider spelling opens the campaign of the entry it is a map of
    for alias, base in ref.ALIASES.items():
        if ref.family(alias) != base or base not in fams:
            return False, f"FAMILY FAIL: the alias {alias} does not resolve"
    # THE PLAN IS ADMISSIBLE AT EVERY INDEX THAT EXISTS: the open one, where
    # the campaign starts, and the three before it (the rediscovery filters).
    # No later index can be planned -- its form list needs a term nobody has
    # -- so there is one opening per family, not a ladder of them.  The class
    # is derived per filter and asserted, because it is a coverage claim.
    classes, tight = {}, []
    for f in fams:
        for n in range(open_n(f) - 3, open_n(f) + 1):
            unit, p1, p2, p3, q2, pb = plan_for(f, n)
            cpu.assert_unit(n, f, unit)      # raises if not forced there
            if unit % 6:
                return False, (f"FAMILY FAIL: {f} n = {n}: the forced unit "
                               f"{unit} does not contain 2 and 3")
            # THE SEGMENT IS PRICED AGAINST THE SEARCH: a find is only
            # known to be the least once its segment closes, and here the
            # whole segment past the find is then RE-SWEPT under the new
            # filter (follow_frontier), so the plan's expected sweep to a
            # confirmed find may not run far over the unavoidable one.
            W = unit
            for q in gpu._wheel_primes(p1, p2, p3):
                W *= q
            _wide, pv = gpu._record_for(W // unit, q2, pb)
            floor_x = ref.term(f, n - 1)
            ideal = model.expected_sweep(f, n, floor_x, floor_x, 1.0)
            swept = model.expected_sweep(f, n, floor_x, (floor_x // W) * W,
                                         pv * W)
            if swept > PLAN_WASTE_MAX * ideal:
                return False, (f"FAMILY FAIL: {f} n = {n} plans a segment of "
                               f"{pv} periods x {W:.4g}, whose expected sweep "
                               f"to a confirmed find is {swept / ideal:.2f}x "
                               f"the unavoidable one -- over the "
                               f"{PLAN_WASTE_MAX}x bound")
            tight.append((ideal / swept, f, n))
        n = open_n(f)
        classes[f] = "%d (mod %d)" % cpu.forced_class(n, f)
        # a unit with a prime that is NOT forced there, or not squarefree
        u = cpu.forced_unit(n, f)
        for wrong in (7 * u, 30030, 4 * u, 67 * u):
            try:
                cpu.assert_unit(n, f, wrong)
                return False, f"FAMILY FAIL: unit {wrong} accepted for {f} n = {n}"
            except ValueError:
                pass
    # THE BENCHMARK SHAPE AT EACH OPENING IS THE CAMPAIGN'S OWN PLAN (rule
    # 5g).  The shapes name their configuration explicitly so that a tuning
    # pass cannot move a window -- which also means a PLANNER change leaves
    # them behind silently, scoring a configuration no campaign runs.  That
    # is a decision to re-freeze (and log), so it fails here until it is made.
    import score as _score
    lv = lambda z: tuple(z or ())               # noqa: E731
    seen = set()
    for row in _score.SHAPES:
        (label, f, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, _nu, pb) = row
        if unit == 1 or n != open_n(f):
            continue                            # an x-space anchor
        seen.add(f)
        want = plan_for(f, n)
        got = (unit, lv(p1), lv(p2), lv(p3), q2, pb)
        if got != (want[0], lv(want[1]), lv(want[2]), lv(want[3]),
                   want[4], want[5]):
            return False, (f"FAMILY FAIL: benchmark shape {label} names "
                           f"{got} and the campaign plans {want} at {f} "
                           f"n = {n}: re-freeze the shape at the plan (and "
                           f"log it), or the score measures a configuration "
                           f"no campaign runs")
    if seen != set(fams):
        return False, (f"FAMILY FAIL: no benchmark shape at the opening of "
                       f"{sorted(set(fams) - seen)} (rule 5g)")
    tight.sort()
    return True, ("families stay apart: %d distinct config keys, checkpoint "
                  "files and ledgers, no policy reads another's cursor, all "
                  "%d rider aliases resolve, the plan is admissible at the "
                  "open index of every family and the three before it, in the "
                  "forced classes %s (a unit with an unforced prime, or not "
                  "squarefree, is refused), and every plan's expected sweep "
                  "to a CONFIRMED find stays near the unavoidable one (the "
                  "worst is %s n = %d at %.2fx, against a %gx bound; a find "
                  "costs the rest of its segment, re-swept under the new "
                  "filter); and the benchmark shape at every opening names "
                  "exactly the configuration the campaign plans there"
                  % (len(fams), len(ref.ALIASES),
                     ", ".join(f"{f} x == {c}" for f, c in classes.items()),
                     tight[0][1], tight[0][2], 1 / tight[0][0], PLAN_WASTE_MAX))


def _campaign_wiring_drill(fam="A093483"):
    """Build a campaign and exercise everything the loop touches, without
    sweeping a whole period: construction from nothing at period 0, the
    status line, census and NEAR/CENSUS classification, the cached rung
    ladder, the drain of a fake in-flight launch, the pool sized from a
    real measurement, back-pressure, a find moving the filter, a save/load
    round trip, and the interrupt snapshot."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="clique-drill-")
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
        # A fresh campaign here starts at the MONOTONICITY FLOOR, not at a
        # constant: the previous term, which is free and is most of the line.
        floor = c.x_start()
        if (c.j, c.u, c.k_min()) != (c.floor_period(), 0, floor):
            return False, (f"WIRING FAIL: a fresh campaign starts at "
                           f"(j, u) = ({c.j}, {c.u}), clip {c.k_min()} -- "
                           f"expected period {c.floor_period()} clipped at "
                           f"{floor}")
        if floor != ref.KNOWN[fam][n0 - 1] + 1:
            return False, (f"WIRING FAIL: the floor {floor} is not just "
                           f"above a({n0-1})")
        unit, p1, p2, p3, q2, pb = plan_for(fam, n0)
        if (c.eng.n, c.eng.fam, c.eng.unit, c.eng.q2, c.eng.pv) != (n0, fam, unit, q2, pb) \
                or (c.eng.p1, c.eng.p2, c.eng.p3) != (p1, p2, p3):
            return False, ("WIRING FAIL: the engine is not the PLANNED one "
                           "for the campaign filter")
        line = c.status_line()
        for want in ("swept to", fam, "census", f"periods [{c.floor_period()},"):
            if want not in line:
                return False, f"WIRING FAIL: status line lacks {want!r}"
        if c.handle(floor + 1, 9) is not False or c.census.get(9) != 1:
            return False, "WIRING FAIL: a census run was not counted"
        if c.handle(floor + 3, 7) is not False or 7 in c.census:
            return False, "WIRING FAIL: a run under the floor was counted"
        # the drain: a fake in-flight launch's survivors land in `pending`
        # (only those at or above the census floor) and the WORK cursor
        # follows it, but not past it
        jf = c.floor_period()
        inflight = collections.deque()
        inflight.append(((jf, 52), [([5, 6, 7], _Done([3, 8, 12]))]))
        inflight.append(((jf, 104), [([9], _Done([0]))]))
        c._drain(inflight, block=True)
        if c.pending != [(6, 8), (7, 12)] or c.survivors != 4:
            return False, (f"WIRING FAIL: the drain left pending "
                           f"{c.pending} and {c.survivors} survivors")
        if (c.j, c.u) != (jf, 104):
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
        # the fake work cursors above (launch 204) sit past the ONE launch
        # a segment is at this opening filter (24,416 periods of a 6.9e9
        # wheel in a single launch), so the calibration would find nothing
        # left to sweep; put the cursor back at the segment start first
        c.u = 0
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
        # within a factor of three of the drill's own measurement, not the
        # 50% lcm-ladders asked: at this opening filter a segment is ONE
        # launch of a quarter second, and two such measurements read 2x
        # apart with the first pool's interpreters starting between them
        if (ms is None or w != max(1, math.ceil(ms["need"] * POOL_MARGIN))
                or c.workers != w or c.pool is None
                or not 1 / 3 < ms["need"] / max(m["need"], 1e-9) < 3):
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
            inflight.append(((jf, 200 + i), [([11 + i], _Slow([3]))]))
        c._drain(inflight, block=False)
        if len(inflight) != BACKLOG_LAUNCHES + 5:
            return False, "WIRING FAIL: the drain took launches not yet classified"
        c._backpressure(inflight)
        if (len(inflight) != BACKLOG_LAUNCHES or c._hostwait <= 0
                or not c._hostbound_logged or c.survivors != 9
                or (c.j, c.u) != (jf, 204)):
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
        c.found[str(n0)] = int(floor + 4)   # a find, unverified, unregistered
        if c.frontier() != n0 or c.filter_n() != n0 + 1:
            return False, "WIRING FAIL: a find did not move the frontier"
        aim = c.next_rung(c.swept_k())
        if c._lad.builds != builds + 1:
            return False, ("WIRING FAIL: the frontier moved and the ladder "
                           "was served from cache")
        if not aim or not aim[0].startswith((f"a({n0 + 1})", "engine ceiling")):
            return False, (f"WIRING FAIL: after finding a({n0}) the campaign "
                           f"aims at {aim} -- a retired rung")
        # THE PROMOTION ITSELF IS NOT RUN HERE.  This campaign sits at the
        # real open index, where the only find there could be is a fabricated
        # one, and follow_frontier would REGISTER it with the oracle, which
        # keeps a term for good.  _promotion_drill runs the promotion in every
        # family on real published terms; what is checked here is only what
        # needs no engine: the frontier, the filter and the ladder follow
        # `found`, and come back when it goes.
        c.found.pop(str(n0))
        if c.frontier() != n0 - 1 or c.filter_n() != n0:
            return False, "WIRING FAIL: the frontier did not come back"
        c._lad.invalidate()
        c.mark_boundary()
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
                  f"at the monotonicity floor (x = {floor:,}, a({n0-1}) "
                  f"itself) with the PLANNED "
                  f"engine at n = {n0}, unit {unit}, wheel ({p1},{p2},{p3}) "
                  f"and depth {q2}; its status line and rung "
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


def _rediscovery_run_drill(fam="A093483"):
    """THE REAL LOOP, END TO END, ON PUBLISHED GROUND.

    Every other drill exercises a piece of the campaign; this one runs
    `Campaign.run` itself -- sweep, drain, classify, narrate at the segment
    close, verify, certify, write evidence, register the term, rebuild the
    filter, restart just above the find, and do it again -- on a scratch
    checkpoint and a scratch evidence directory, opened BELOW the published
    frontier (DRILL_N) and bounded just past a(DRILL_N + 1).  It can find
    nothing new: everything it may find is already in the OEIS, and the
    oracle already holds it.  What it proves is the thing a gate battery
    built from pieces cannot: that the loop as written finds a(13), promotes
    itself, and then finds a(14) UNDER THE CONDITION a(13) CREATED -- the
    sequential dependence that is this project's whole risk.
    """
    import json as _json
    import tempfile
    tmp = tempfile.mkdtemp(prefix="clique-rerun-")
    path = str(pathlib.Path(tmp) / "c.json")
    evid = str(pathlib.Path(tmp) / "evidence")
    n0 = DRILL_N
    want = {str(n): ref.KNOWN[fam][n] for n in (n0, n0 + 1)}
    args = _args_for(fam, start_n=n0, to=want[str(n0 + 1)] + 10 ** 6,
                     heartbeat=3600.0)
    # ... with the terms it is about to find HIDDEN from the oracle, so the
    # loop stands where a campaign at the real frontier stands: a find it
    # has not registered is a find nothing downstream can see (_unpublished)
    with _unpublished(fam, n0):
        c = Campaign(args, ckpt=path, cursor=_POLICIES[fam].at(path),
                     evid=evid)
        rc = c.run()
        registered = {str(n): ref._RUNTIME[fam].get(n) for n in (n0, n0 + 1)}
    if registered != want:
        return False, (f"RERUN FAIL: the oracle was hidden a({n0}), "
                       f"a({n0 + 1}) and the campaign registered {registered}, "
                       f"not {want}")
    if rc != 0 or {k: int(v) for k, v in c.found.items()} != want:
        return False, (f"RERUN FAIL: {fam} from index {n0} found {c.found}, "
                       f"published {want}")
    if c.discoveries != 2 or c.filter_n() != n0 + 2:
        return False, (f"RERUN FAIL: {c.discoveries} discoveries, filter "
                       f"{c.filter_n()}")
    for n in (n0, n0 + 1):
        f = pathlib.Path(evid) / f"{fam}_a{n}_{want[str(n)]}.json"
        if not f.exists():
            return False, f"RERUN FAIL: no evidence file for a({n})"
        with open(f) as fh:
            ev = _json.load(fh)
        ok, msg = evidence.check_names(ev, TERM)
        if not ok:
            return False, f"RERUN FAIL: a({n})'s evidence: {msg}"
        if ev["prefix"] != ref.terms(fam, n) or ev["unproved"] or \
                len(ev["values"]) != ref.nforms(fam, n) or \
                ev["least_claim"]["swept_from"] != ref.KNOWN[fam][n - 1] + 1:
            return False, f"RERUN FAIL: a({n})'s evidence is not self-contained"
        for a in ev["also_settles"]:
            if ref.KNOWN_ALSO[a["sequence"]][n - 1] != a["value"]:
                return False, f"RERUN FAIL: {a['sequence']}({n}) came out wrong"
    ok, msg = evidence.gate_names(evid, TERM)
    if not ok:
        return False, "RERUN FAIL: " + msg
    return True, (f"rediscovery run ok: Campaign.run, opened at index {n0} of "
                  f"{fam} on scratch files, found a({n0}) = "
                  f"{want[str(n0)]:,}, promoted itself, and found a({n0 + 1}) "
                  f"= {want[str(n0 + 1)]:,} under the condition the first "
                  f"find created; both evidence files carry their prefix, "
                  f"their values, their certificates and their derived "
                  f"claims, and pass the naming gate ({c.survivors:,} "
                  f"survivors classified, census {dict(sorted(c.census.items()))})")


def _evidence_names_drill():
    """The writer and the files on disk speak the OEIS entries' language.

    The writer's header is built here exactly as `record_discovery` builds
    it, for both families, and every record already in evidence/ is read
    back: the integer is under TERM, TERM stands alone in `forms`, and
    `oeis_terms` says what to submit.  This project shipped its first
    sixteen finds under `x` beside a `forms` that said m.
    """
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        ev = dict(evidence.header(fam, ref.FAMILIES[fam]["forms"], TERM,
                                  ref.KNOWN[fam][top], [top]), settles=[top])
        ok, msg = evidence.check_names(ev, TERM)
        if not ok:
            return False, f"EVIDENCE NAMES FAIL: {fam} writer: {msg}"
    return evidence.gate_names(EVID, TERM)


def selftest(fam="A093483"):
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
    for d in (_ceiling_drill, _canary_hunt, _protocol_drill,
              _certificate_drill, _resume_drill, _promotion_drill,
              _classification_drill, _stop_on_discovery_drill,
              _families_stay_apart):
        rows.append(d())
    rows.append(_campaign_wiring_drill(fam))
    rows.append(_rediscovery_run_drill(fam))
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
    front = max(ref.KNOWN[fam])
    for n in st.get("found", {}):
        front = max(front, int(n))
    log("STATUS", "  ".join([
        f"{fam}",
        f"swept to {TERM} = {int(st['k']):,}",
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
    ap.add_argument("--family", default="A093483",
                    help="which sequence to hunt: " +
                         ", ".join(ref.FAMILIES) + "; the derived entries " +
                         ", ".join(f"{a} (= {b})" for a, b in
                                   sorted(ref.ALIASES.items())) +
                         " are accepted as aliases (default A093483)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this depth on the x line (default: the "
                         "engine ceiling, huntlib.ceiling.K_CEIL = 1e40 for "
                         "every family -- where certificates on these "
                         "unstructured values were measured to succeed)")
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
                             f"swept to {TERM} = {st.get('k')}"))
    if args.fresh:
        for p in (ckpt_path(args.family), ckpt_path(args.family) + ".bak"):
            if os.path.exists(p):
                os.remove(p)
    return Campaign(args).run()


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
