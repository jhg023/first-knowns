"""The campaign for the factorial ladders -- least m with k!*m +- 1 prime for
every k = 1..n.

    python launch.py --selftest            the full gate battery (must end ALL GREEN)
    python launch.py                       the hunt: indefinite, resumable (A177013)
    python launch.py --family A177014      the other family
    python launch.py --to 1e20             stop at a chosen depth in x
    python launch.py --status              read the checkpoint and say where it is

TWO FAMILIES, THREE OEIS ENTRIES, ONE CAMPAIGN AT A TIME.  `--family` names
the entry (fladder_reference.FAMILIES; A226935 is accepted as an alias of
A177014, being that sequence shifted by one).  The two hunted families are
the same multipliers with the sign flipped, so they share every file here
and every killed-set size -- but they are different sequences with
different frontiers, so each carries its OWN checkpoint under its own config
key and a campaign hunts one of them.  A find on A177014 settles A226935 at
every index it settles, for nothing (the chain p(i) = i*p(i-1) - (i-1)
unrolls to i!*(p-1) + 1: fladder_reference G2d).

THE LINE.  The published term is x itself -- no substitution, no L(n) --
so every filter sweeps ONE line, and what a find changes is the FILTER, not
the line: the wheel grows (more multipliers, more killed residues per
prime), the unit stays 6, and the cursor moves to the find, which is the
next filter's floor by monotonicity.  The engine still rebuilds at each
promotion, because the plan is per filter; `_promotion_drill` is the gate
for it.

THE OPENINGS (CLAUDE.md 5g, step 1 -- the test plan for every default
below).  Both families open at n = 11, and the early filters are minutes:

    n     median x    unit   wheel (planned)              q2         period    window   record
    11    3.4e10      6      {5..23} (segment cap)        2^20       2.2e8     160      narrow
    12    1.3e12      6      {5..23, 31}                  2^20       6.9e9     160      narrow
    13    4.9e13      6      to 31                        2^20       2.0e11    224      narrow
    14    1.9e15      6      to 37                        262144     7.4e12    224      narrow
    15    6.2e16      6      to 41                        131072     3.0e14    192      narrow
    16    3.1e18      6      to 43                        131072     1.3e16    224      narrow
    17    1.4e20      6      to 47                        65536      6.1e17    179      narrow
    18    6.0e21      6      to 53 (non-contiguous split) 65536      3.3e19    160      WIDE
    19    2.8e23      6      to 53                        32768      3.3e19    224      WIDE

(A177014's a(11) median is 2.4e10 and its opening window 128 periods.)  The
SEGMENT is capped at the modelled median (fladder_gpu.SEGMENT_MARGIN; v1
capped the period at a quarter of it and let the window multiply that by
224), the window is the widest the cap and the record admit, and THE
RECORD IS THE ENGINE'S OWN RUNTIME CHOICE from the wheel and window it is
handed: the wheel to 53 has a period no u64 window admits, so the engine the
campaign builds at n = 18 comes up on the wide (offset, period) record with
no flag anywhere in this file, 1.19x at n = 18 and 1.24x at n = 19
(OPTIMIZATION_LOG.md round 3; _promotion_drill and _families_stay_apart
assert the choice through the campaign's own build path).

The unit is 6 at every one of them (2 and 3 are forced, and by Wilson no
prime >= 5 ever is), and what moves from filter to filter is the kill set,
the wheel the planner can afford under the period cap (a find is only known
to be the least once its period closes, and at n = 11 a full wheel's period
would be a hundred times the search), and the sieve depth.  `plan_for`
derives the whole configuration per filter and this file stores none of it;
G8, G13 and G18 check the planned configuration at every filter of both
families, and `_families_stay_apart` asserts the unit really is 6 at each.

A FIND MOVES THE FLOOR, NOT THE LINE.  On a find the campaign rebuilds the
engine at the next filter; the new filter's claim starts at the term just
found -- a() is non-decreasing because the conditions nest -- and its
SWEEP resumes at the end of the line the old filter classified: every
survivor of a closed segment was run to n + 8 and the new filter's sieve
keeps a subset of the old one's survivors, so nothing below that line can
be the next term without having been found (Campaign.follow_frontier).
Nothing is skipped and nothing already classified is re-swept.  A find may be a RIDER: the sieve at filter
n keeps a superset of what the filter-(n+1) sieve keeps (K(q,n) is a subset
of K(q,n+1)), so an x whose run passes n settles every term up to its run at
once, decided by running the chain on (fladder_reference.run_length).

WHAT IS OPEN, AND WHY IT IS WORTH A SWEEP.  Both frontiers are Enoch Haga
and Farideh Firoozbakht's a(10) of May 2010 (3,240,034,842 and 228,698,250;
the latter corrected by Jon E. Schoenfield in 2018), and A226935 has never
been extended.  No entry carries a bound of any kind at any open index and
none has a b-file.  a(11) is open on all three, and the modelled medians
put a(11) through a(16) inside the first few minutes of device, a(17) at
under an hour, a(18) at a day and a(19) at weeks.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine's enforced ceiling -- k_ceil in fladder_search, huntlib.ceiling
.K_CEIL = 1e40 on x for both families -- and that is the last rung.  Below
the PROOF CROSSING k_proof(n, F) every classification is a deterministic
proof; above it the same seven-base chain is a strong probable-prime test,
the census is a count and a NEAR is a health check either way, and a
DISCOVERY is proved by CERTIFICATE on its own structure.  THE CROSSING IS
VERY LOW HERE -- x = 8.3e16 at n = 11, 2.5e12 at n = 15, 9.3e9 at n = 17,
and x = 1 from n = 25 -- so the certificate is the normal path in this
project from the first minutes: (k!*x + s) - s = k!*x with k! k-smooth, so
ONE factorization of x proves the whole run by BLS75 Theorem 1 on V - 1
(s = +1) or Theorem 15, the N+1 Lucas test, on V + 1 (s = -1), with a
subproof for any prime factor of x past the bound.  The crossing is a
[MILESTONE], not a stop.  `--to` and `--stop-on-discovery` are the only
stops and both are opt-in.  Progress is read off RUNGS taken from the odds
model's quantiles, logged as they are passed and shown with an ETA in every
[STATUS].  A rung retires with its term: the ladder is derived from the
LIVE frontier and cached on it (huntlib.rungs.LiveLadder), never recomputed
in the loop.

THE TAXONOMY, mapped to this problem (CONVENTIONS.md "the discovery
protocol").  A survivor is an x with a run length r:

  DISCOVERY  r > frontier: x settles a(frontier+1) ... a(r) at once, each
             logged once, all evidenced under the FIRST value they belong
             to.  Verified three ways plus a witness for the composite that
             stops the run, and a re-verified certificate for every value.
             The evidence file records what the find settles in the rider
             entry: A226935(m) = x + 1 for A177014, at every m the find
             settles.
  NEAR       r == frontier: one condition short of the open term.  One line
             with its campaign ordinal, verified by the cheap legs as an
             engine health check, never evidenced.
  CENSUS     CENSUS_FLOOR <= r < frontier: counted in [STATUS], never
             narrated.
  None       r < CENSUS_FLOOR: noise, not counted.

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
engine sieves a SEGMENT of eng.seg_periods wheel periods at once, and a
segment's candidates come out in (t, s, u, period) order, so the x line is
contiguous only at the end of a whole segment.  COVERAGE (`boundary`, the x
below which every value is swept) advances one segment at a time and is the
only thing a least-claim rests on; WORK (`j`, `u`) advances every launch.
Values classified mid-segment are held IN THE CHECKPOINT and narrated in x
order when the segment closes.  At the opening filters a whole segment may
hold several terms (a(11) and a(12) both sit inside the first one at
n = 11): they are narrated in x order, each promoting the frontier before
the next is classified, so a run-12 value found by the filter-11 sieve is
a(12) only if no smaller x in the segment reached 12 -- which the ordering
guarantees.

THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER, at
start and again every time the filter moves (Campaign.size_pool: the next
launches are swept and timed, their survivors counted, a sample of them
classified, and ceil(need x POOL_MARGIN) workers ramped one at a time at
below-normal priority, huntlib.pool).  The SIEVE DEPTH is chosen so that
number lands near one core at every filter where the analytic survival can
reach the target (fladder_gpu.plan_q2); at n = 11..13 it cannot, the ladder
tops out at 2^20, and the pool is sized to what is measured there for the
seconds those filters last.  The device may run at most BACKLOG_LAUNCHES
ahead of the pool, so a pool that binds throttles the device VISIBLY -- the
[STATUS] line says HOST-BOUND and by how much -- instead of silently.
Classification runs in the pool while the device sweeps, and the WORK
cursor lags behind the launches whose survivors are still being classified,
so a crash never loses a survivor it has not yet looked at.  The throttles
are `--workers`, `--gpu-yield-ms` and `--gentle`, priced in the help text
against the launch.  No machine setting is ever changed on the owner's
behalf.
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

import fladder_gpu as gpu                                       # noqa: E402
import fladder_model as model                                   # noqa: E402
import fladder_reference as ref                                 # noqa: E402
import fladder_search as cpu                                    # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")

# NOTHING ABOUT THE WHEEL IS A CONSTANT HERE.  The three wheel levels, the
# sieve depth and the window width are all PLANNED per filter, because the
# kill sets grow with n (fladder_reference: K(q,n) is a subset of K(q,n+1),
# saturating at n = q - 1) and the period the search can afford grows with
# the modelled median (a hundredth of a full wheel's period at n = 11, a
# hundred times it at n = 17).  The unit alone is constant -- 6 at every
# n >= 2 -- and it is still derived, never stored.  `plan_for` is the ONE
# place a configuration is derived, and `--status`, the campaign and every
# drill go through it (OPTIMIZATION.md 2.9: derive configuration in exactly
# one place).
PLAN_VERSION = "p2"               # bump when plan_for's answer changes
#   p2 (v3): the SEGMENT is capped against the median (not the period),
#   the window is planned per filter, and the wheel to 53 enters at n >= 18


@functools.lru_cache(maxsize=None)
def plan_for(fam, n):
    """(unit, p1, p2, p3, q2, pb) for filter n of family F -- the
    configuration the campaign runs there, and the fastest correct one it
    has (CLAUDE.md 5g).  Measured, not assumed: the wheel maximises
    candidates per unit of line subject to the period bound and a segment
    no longer than the modelled median, the depth is the smallest whose
    analytic survivor rate two workers can absorb, and the window is the
    widest the segment cap and the record admit (fladder_gpu.wheel_plan,
    plan_q2, plan_pb).  THE RECORD IS NOT PLANNED HERE: the engine chooses
    the narrow or the wide survivor record from the wheel and window it is
    handed, at every build -- the campaign's start and every promotion --
    so the wheel to 53 at n = 18 comes up on the wide record with no flag
    (fladder_gpu.GpuEngine, `wide`; drilled in _promotion_drill).

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
    cap = gpu.search_segment_cap(n, fam)
    p1, p2, p3 = gpu.wheel_plan(n, fam, unit, max_segment=cap)
    q2 = gpu.plan_q2(n, fam, unit, gpu._wheel_primes(p1, p2, p3))
    pb = gpu.plan_pb(n, fam, unit, gpu._wheel_primes(p1, p2, p3), q2,
                     max_segment=cap)
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
    return max(int(frontier_x), cpu.k_floor(q2, n, fam) + 1)


def open_n(fam):
    """The filter a FRESH campaign of this family opens at: the index after
    the published frontier."""
    return max(ref.KNOWN[ref.family(fam)]) + 1




# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a segment.  A
# launch is 2^37 candidates at most (fladder_gpu.CAND_PER_LAUNCH4), some tens
# of milliseconds, so 32 launches is a second or two: what an interrupt
# costs to redo, and the denominator that prices --gpu-yield-ms.  The
# mid-segment save is rate-limited by CKPT_MIN_S.
CKPT_LAUNCHES = 32
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
# The SEGMENT a plan sweeps may be at most this many modelled medians long.
# A find is only known to be the least once its segment closes, so it costs
# up to one segment of over-sweep -- inherited by the next filter since the
# launcher carries the classified line (follow_frontier), so a segment as
# long as the median costs ~15% of a median-time in expectation, against
# window and wheel gains of 1.2-1.5x (fladder_gpu.SEGMENT_MARGIN).  Checked,
# not enforced: a plan that failed it would be a decision for a human, not
# something for the planner to route around silently.
SEGMENT_MARGIN = gpu.SEGMENT_MARGIN


def c_front(fam):
    """The frontier term a fresh campaign of `fam` starts from."""
    fam = ref.family(fam)
    return ref.KNOWN[fam][max(ref.KNOWN[fam])]
# THE ENGINE IS v3: v1 was lcm-ladders' v1 window sieve (the linear
# ladders' v4 with a per-filter subset-wheel plan) with the multiplier list
# swapped to k!; v2 lifted the reduction bound to 2^64, which the
# arithmetic always had (a 179-period window on the full wheel instead of
# 64: 1.19x at n = 17), and re-chose the queue margin against the actual
# occupancy; v3 adds the WIDE survivor record -- (within-period offset,
# period) instead of a u64 launch offset -- which the engine takes at
# runtime wherever the wheel's period admits no u64 window, and the plan
# that uses it: the segment capped at the median, the window per filter,
# non-contiguous level splits, the wheel to 53 from n = 18 (1.19x there,
# 1.24x at n = 19; OPTIMIZATION_LOG.md round 3).
ENGINE_VERSION = "v3"
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


def verify(x, run, fam, witness=True):
    """The three independent confirmations plus the bounding witness.

    witness=False is the [NEAR] path: a one-short value is verified but not
    evidenced, so nobody reads its stopper's factor, and rho plus 200 ECM
    curves on a 40-digit stopper is device-idle time bought for nothing.
    The stopper is still shown composite -- that leg is what bounds the run.

    Everything is stated on x, the published term.  Value i is i!*x + s.

    1. huntlib's Miller-Rabin, which is a PROOF below the proof crossing
       k_proof(n, F) (G10) and a seven-base strong probable-prime chain
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
    s = ref.sign(fam)
    x = int(x)
    legs = {"mr_chain": all(mr_is_prime(math.factorial(i) * x + s)
                            for i in range(1, run + 1)),
            "sympy_bpsw": ref.run_length(fam, x, cap=run + 1) == run,
            "resieve_other_wheel": cpu.CpuEngine(run, fam, q2=4096).survives(x)}
    stop_i = run + 1
    stop = math.factorial(stop_i) * x + s
    legs["stopper_composite"] = not mr_is_prime(stop)
    ok = all(legs.values())
    wit = (stopper_witness(stop)
           if witness and legs["stopper_composite"] else None)
    return ok, legs, {"i": stop_i, "value": stop, "factor": wit,
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
    """A checkable primality certificate for every value i!*x + s of the
    run: ({str(i): proof}, [the i left UNPROVED]).

    THIS PROJECT IS RULE 5h'S BEST CASE.  Value i is i!*x + s, so

        (i!*x + s) - s  =  i! * x

    is completely factored the moment x is -- i! is i-smooth by
    construction, its factorization is Legendre's formula -- so ONE
    factorization of x factors every value's N -+ 1 at once.  Below the
    deterministic bound huntlib.certificate.prove answers with the
    seven-base test, which IS the proof there.  Above it every value gets
    BLS75 Theorem 1 on N - 1 (s = +1, A177014) or Theorem 15, the N+1 test
    with a Lucas sequence per prime, on N + 1 (s = -1, A177013), from that
    same factorization with i!'s own factors added in.  A prime factor of x
    past the bound is admitted with a SUBPROOF of its own
    (huntlib.certificate's recursion), so the certificate is a finite tree
    whose leaves are deterministic tests.  A value the shared factorization
    cannot prove falls back to certificate.prove's own bounded search on
    both sides.

    Every proof is RE-VERIFIED from scratch before it is returned.  A
    certificate that was not checked is a claim, not a certificate.
    """
    from sympy import primerange
    fam = ref.family(fam)
    x, s = int(x), ref.sign(fam)
    # ONE factorization for the whole run, of x itself.  The smooth part is
    # peeled by trial division first and only the hard part goes to
    # factor_full (huntlib's bounded chain then sympy's factorint, which the
    # ceiling K_CEIL was measured against).
    fac = {}
    rest = x
    for p in primerange(2, 128):
        while rest % p == 0:
            fac[int(p)] = fac.get(int(p), 0) + 1
            rest //= p
    if rest > 1:
        for p, e in certificate.factor_full(rest).items():
            fac[int(p)] = fac.get(int(p), 0) + int(e)
    certs, unproved = {}, []
    for i in (range(1, run + 1) if only is None else only):
        facN = dict(fac)
        # i! = prod p^e with e = sum_j floor(i / p^j) (Legendre)
        for p in primerange(2, i + 1):
            e, pj = 0, p
            while pj <= i:
                e += i // pj
                pj *= p
            facN[int(p)] = facN.get(int(p), 0) + e
        N = math.factorial(i) * x + s
        proof = (certificate.prove(N, fac=facN) if s > 0
                 else certificate.prove(N, fac_plus=facN))
        if proof is None:
            proof = certificate.prove(N)
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
        certs[str(i)] = proof
        if proof is None:
            unproved.append(int(i))
    return certs, unproved


def also_settles(fam, x, run, settles):
    """What a find settles in the DERIVED entry, as records for the
    evidence file.

    A226935 = A177014 + 1 -- the chain p(i) = i*p(i-1) - (i-1) from p(1) = p
    is i!*(p-1) + 1, re-derived from the bare definition by
    fladder_reference G2d -- so a find on A177014 settles it at EVERY index
    it settles, with no extra search and no extra condition.  A177013 has
    no rider: nobody has entered the chain p(i) = i*p(i-1) + (i-1).
    """
    fam = ref.family(fam)
    out = []
    for seq, shift in ref.FAMILIES[fam]["also"]:
        for n in settles:
            out.append({"sequence": seq, "n": int(n),
                        "value": int(x) + int(shift),
                        "claim": f"{fam}({n}) {shift:+d}"})
    return out


# ----------------------------- classification -------------------------------

def sprp_run(x, fam, cap, floor=CENSUS_FLOOR):
    """Run length of x, screened with a base-2 strong test and CONFIRMED
    with the deterministic chain wherever the answer matters.

    A failed base-2 test is a PROOF of compositeness (huntlib.primes), so
    the first pass can only overstate a run, never understate it.  Runs that
    come out below the census floor are never looked at again, so an
    overstatement there costs nothing; a run at or above it is recomputed
    with all seven bases, which is the deterministic answer below the proof
    crossing and a strong probable-prime answer above it (a DISCOVERY there
    is proved by certificate; the census is a count).

    NOT capped at the filter: the forms do not depend on n, so a survivor
    of the filter-n sieve whose run passes n is a RIDER and its run is
    what it is.  `cap` bounds the chain (the launcher passes filter + 8).
    """
    fam = ref.family(fam)
    s = ref.sign(fam)
    cap = int(cap)
    r = 0
    while r < cap and sprp_base2(math.factorial(r + 1) * x + s):
        r += 1
    if r >= floor:
        r = 0
        while r < cap and mr_is_prime(math.factorial(r + 1) * x + s):
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
            out.append((chunk, pool.submit(_classify_chunk,
                                           (fam, cap, chunk))))
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

    def _build_engine(self, n):
        """The engine for filter n, PLANNED (never a stored constant)."""
        unit, p1, p2, p3, q2, pb = plan_for(self.fam, n)
        # the RECORD is the engine's own runtime decision from this plan
        return gpu.GpuEngine(n, self.fam, p1=p1, p2=p2, p3=p3, q2=q2,
                             unit=unit, pb=pb, seg_cap=pb)

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
        probable-prime chain rather than a proof (fladder_search.k_proof)."""
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
                f"{self.oeis}) = {pc:.4g}: {self.filter_n()}!*x {self.s:+d}, "
                f"the top value, now exceeds the deterministic Miller-Rabin "
                f"bound, so classification is a seven-base strong "
                f"probable-prime chain from here (the census is counted and "
                f"a NEAR is a health check either way) and a DISCOVERY is "
                f"proved by BLS75 certificate on "
                f"{'V - 1' if self.s > 0 else 'V + 1'} = k!*x "
                f"({'Theorem 1' if self.s > 0 else 'Theorem 15, Lucas'}; "
                f"certify_run); the ceiling is x < "
                f"{cpu.k_ceil(self.filter_n(), self.fam):.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "plan": PLAN_VERSION,
                "family": self.fam,
                "sign": self.s,
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
            ok, legs, _ = verify(k, run, self.fam, witness=False)
            if not ok:
                log("ALARM", f"NEAR value x = {k:,} run {run} failed "
                             f"verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at x = {k:,} (run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of a({frontier + 1})!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, x, run):
        frontier = self.frontier()
        n = self.eng.n
        # A RIDER IS DECIDED HERE, by running the chain past the filter.
        # The sweep sieved for n conditions; the x it found may clear more,
        # and the classification already ran to filter + 8 -- this re-runs
        # it by the oracle's own definition, further, before anything is
        # claimed.  A177014's published a(9) = a(10) is exactly this.
        self.hb.doing(f"verifying run-{run} x={x}")
        true_run = ref.run_length(self.fam, x, cap=n + 8)
        if true_run < run:
            log("ALARM", f"claimed a({frontier+1}) = {x} has run {true_run} "
                         f"by the oracle but {run} by the classifier")
            raise SystemExit(2)
        run = true_run
        ok, legs, stop = verify(x, run, self.fam)
        if not ok:
            log("ALARM", f"claimed a({frontier+1}) = {x} failed the "
                         f"protocol: {legs}")
            raise SystemExit(2)
        settles = list(range(frontier + 1, run + 1))
        self.hb.doing(f"certifying run-{run} x={x}")
        certs, unproved = certify_run(x, run, self.fam)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        also = also_settles(self.fam, x, run, settles)
        ev = {"sequence": self.oeis, "forms": ref.FAMILIES[self.fam]["forms"],
              "sign": self.s,
              "x": int(x), "filter_n": int(n),
              "run": int(run), "settles": settles,
              "values": {str(i): int(math.factorial(i) * x + self.s)
                         for i in range(1, run + 1)},
              "multipliers": {str(i): int(math.factorial(i))
                              for i in range(1, run + 1)},
              "verification": legs,
              "stopper": stop,
              "certificates": certs,
              # every proof above was re-verified from scratch before it
              # was accepted; `unproved` lists any i that has none
              "certificates_verified": not unproved,
              "unproved": unproved,
              "proof_routes": routes,
              "also_settles": also,
              "least_claim": {"swept_from_x": int(self.x_start()),
                              # up to here the claim rests on the PREVIOUS
                              # filter's classified sweep (follow_frontier):
                              # every survivor there was run to n + 8, so a
                              # run of this length would have been found
                              "covered_by_previous_filter_to":
                                  int(max(self.cover_x, self.x_start())),
                              "swept_to_x": int(x),
                              "filter": int(n),
                              "wheel": int(self.eng.W),
                              "sieve_depth": int(self.eng.q2),
                              "unit": int(self.eng.unit),
                              "monotone_floor": int(self.frontier_k())},
              "engine": self.key}
        for m in settles:
            self.found[str(m)] = int(x)
        path = evidence.record(
            ev, EVID, f"{self.oeis}_a{settles[0]}_{x}.json",
            ledger_path(self.fam), key="x",
            label="%s a(%s)" % (self.oeis, ",".join(map(str, settles))))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        stopline = (f"stopped by {stop['i']}!*x {self.s:+d} = "
                    f"{stop['value']:,} = {stop['factor']} * ...")
        lines = [
            f"{self.oeis} a({settles[0]}) = {x:,}" if len(settles) == 1 else
            f"{self.oeis} a({settles[0]})..a({settles[-1]}) = {x:,}",
            f"run {run}: k!*x {'+' if self.s > 0 else '-'} 1 is prime for "
            f"every k = 1..{run}",
            stopline,
            f"verified 3 ways, {proved} of {len(certs)} certificates "
            f"re-verified ({', '.join(f'{r} x{c}' for r, c in sorted(routes.items()))}), "
            f"evidence {path}"]
        for a in also:
            lines.append(f"also settles {a['sequence']}({a['n']}) = "
                         f"{a['value']:,}")
        if unproved:
            lines.append(f"UNPROVED at i = {unproved}: those values passed "
                         f"the seven-base chain and BPSW but no certificate "
                         f"landed within the bounded effort -- the find "
                         f"stands on the three legs; certify them by hand "
                         f"from the evidence file")
        banner("DISCOVERY", lines)

    def follow_frontier(self):
        """After a find: rebuild the engine at the next open term and start
        it at the term just found.

        The line is the same line -- the published term is x -- but the plan
        is per filter (a bigger kill set, possibly a longer wheel and a
        different depth), so the engine is rebuilt and its cursor set to the
        new filter's floor, which is the find (monotonicity: everything
        below it is excluded by the find itself, not by a sweep).  Nothing
        is re-swept and nothing is skipped: the old filter's coverage claim
        ended at the find, and the new filter's claim starts there.
        """
        old = self.eng
        # THE OLD FILTER'S CLASSIFIED COVERAGE CARRIES OVER.  Every survivor
        # of every closed segment was classified to run cap n + 8 at the
        # old filter, and the filter-(n+1) sieve keeps a SUBSET of the
        # filter-n sieve's survivors (K(q,n) is a subset of K(q,n+1)), so no
        # x below the old boundary can have a run the new filter is hunting
        # for without having been found already -- any such x was a rider
        # and is in `found`.  So the new filter resumes at the END of the
        # classified line, not at the find: re-sweeping [find, boundary) at
        # the new filter finds nothing by construction and costs a segment
        # (a fifth of a(17)'s median at the 179-period window, ten minutes
        # at n = 16 -> 17 and eight at 17 -> 18; OPTIMIZATION_LOG.md round 2).
        # Floored onto the new period so no gap can open; the overlap (under
        # one new period, and empty from n = 16 on, where the wheel no longer
        # changes) is re-swept and re-counted, which is harmless.
        self.cover_x = max(int(self.cover_x), int(self.boundary) * int(old.W))
        self.eng = self._build_engine(self.filter_n())
        self.j = max(self.floor_period(), self.cover_x // int(self.eng.W))
        self.u = 0
        self.boundary = self.j
        self.pending = []
        log("STAGE",
            f"filter follows the frontier: n = {old.n} -> {self.eng.n} on the "
            f"same x line -- the wheel "
            f"({old.p1},{old.p2},{old.p3}) becomes "
            f"({self.eng.p1},{self.eng.p2},{self.eng.p3}), the depth "
            f"{old.q2} becomes {self.eng.q2}, the period {old.W:.4g} "
            f"becomes {self.eng.W:.4g}, the segment {old.seg_periods} -> "
            f"{self.eng.seg_periods} periods on the "
            f"{'WIDE' if self.eng.wide else 'narrow'} survivor record "
            f"(was {'wide' if old.wide else 'narrow'}; the engine chose it "
            f"from the plan) and the unit stays {self.eng.unit}; "
            f"the claim's floor is x = {self.x_start():,} (the term just "
            f"found -- monotonicity) and the sweep resumes at x = "
            f"{self.j * self.eng.W:,}, the end of the line the old filter "
            f"classified (every survivor of it was run to n + 8, so nothing "
            f"below it can be a({self.filter_n()})); the ladder now aims at "
            f"a({self.filter_n()})")
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({m})")
                                  for m in self.found)]
        # the crossing moves with the filter ((n+1)! is bigger), and is
        # already behind the sweep at every filter past n = 14
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
                     f"{self.proof_crossing():.4g} and a seven-base strong "
                     f"probable-prime chain above it; a DISCOVERY is proved "
                     f"by certificate either way (certify_run: BLS75 "
                     f"{'Theorem 1 on N - 1' if self.s > 0 else 'Theorem 15 on N + 1'}"
                     f" = k!*x, x factored once, subproofs for factors past "
                     f"the bound), and the engine ceiling {target:.4g} is "
                     f"where a worst-case certificate was measured to cost "
                     f"seconds (huntlib.ceiling)")
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
                                     _submit(self.pool, self.fam, cap,
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
    return [((11, 10), "DISCOVERY"),      # beyond the frontier
            ((14, 10), "DISCOVERY"),      # a long run settles several at once
            ((10, 10), "NEAR"),           # one condition short of a(11)
            ((9, 10), "CENSUS"),          # below the frontier: counted only
            ((8, 10), "CENSUS"),          # the census floor itself
            ((7, 10), None),              # under the floor: not even counted
            ((0, 10), None)]


# The canaries: published terms a period-0 mini-hunt reaches in a second or
# two, at the filter each belongs to, in x space AND in unit space (the
# stream that sweeps x' = x / 6 must find the same first x).  a(10) of
# A177013 at 3.2e9 is the deepest -- the frontier itself, rediscovered.
_CANARIES = (("A177013", 9, 1), ("A177013", 9, 6), ("A177013", 10, 6),
             ("A177014", 8, 1), ("A177014", 8, 6), ("A177014", 9, 6))


def _canary_hunt():
    """The stream must organically rediscover known terms, in both families.

    Dedicated mini-hunts at the filters those terms belong to.  The
    production filter cannot rediscover them -- a(9) has run 9 and an
    n = 11 wheel is entitled to kill it -- so rediscovery is done at the
    filter each term belongs to, sweeping period 0 from the engine floor
    with the clip, and the prefix [1, floor] checked by the oracle so
    "FIRST occurrence" is a claim about the line and not about a window.
    """
    hits_all = []
    for fam, n, unit in _CANARIES:
        if cpu.forced_unit(n, fam) % unit:
            return False, (f"CANARY FAIL: unit {unit} is not forced at "
                           f"n = {n}, so the canary would sweep a thinner "
                           f"line than it claims")
        want = ref.KNOWN[fam][n]
        eng = gpu.GpuEngine(n, fam, p1=13, p2=None, p3=None, q2=4096,
                            unit=unit)
        lo = cpu.k_floor(4096, n, fam) + 1
        if ref.first_x(fam, n, lo=1, hi=lo - 1) is not None:
            return False, (f"CANARY FAIL: {fam} n={n}: the oracle found a "
                           f"run-{n} below the engine floor")
        ceng = cpu.CpuEngine(n, fam, q2=4096)
        surv = eng.survivors_j(0, want // eng.W + 1, k_min=lo)
        hits = [int(k) for k in surv if ceng.run_length(int(k)) >= n]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: {fam} filter n={n} unit={unit} "
                           f"found x = {min(hits) if hits else None}, "
                           f"expected a({n}) = {want}")
        hits_all.append(f"{fam} a({n})" + (f" (unit {unit})" if unit > 1
                                           else ""))
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as FIRST occurrences at their own "
                  "filters, sweeping period 0 from the engine floor with the "
                  "prefix cleared by the oracle -- in x space and in unit "
                  "space, both families, up to A177013's frontier a(10) = "
                  "3,240,034,842")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on both families."""
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        ok, legs, stop = verify(x, top, fam)
        if not ok:
            return False, (f"PROTOCOL FAIL: genuine run-{top} at x={x} "
                           f"({fam}) rejected: {legs}")
        if stop["i"] != top + 1:
            return False, f"PROTOCOL FAIL: {fam}: the stopper is not rung {top+1}"
        if stop["factor"] is None:
            return False, (f"PROTOCOL FAIL: {fam}: no factor witness for "
                           f"the composite stopper")
        if (stop["value"] % stop["factor"]) or \
                stop["factor"] in (1, stop["value"]):
            return False, f"PROTOCOL FAIL: {fam}: the witness is not a factor"
        bad, legs_b, _ = verify(x, top + 1, fam)
        if bad:
            return False, (f"PROTOCOL FAIL: fake run-{top+1} claim at x={x} "
                           f"({fam}) ACCEPTED ({legs_b})")
        prev = max(n for n in ref.KNOWN[fam] if ref.KNOWN[fam][n] < x)
        fake, _lc, _ = verify(ref.KNOWN[fam][prev], top, fam)
        if fake:
            return False, (f"PROTOCOL FAIL: {fam}: a({prev})'s x accepted as "
                           f"a run-{top}")
    # and the derived claim: a find on A177014 settles A226935 at EVERY
    # index it settles, shifted by one; A177013 settles nothing else
    x = ref.KNOWN["A177014"][10]
    also = also_settles("A177014", x, 10, [9, 10])
    if [a["sequence"] for a in also] != ["A226935"] * 2 or \
            any(a["value"] != x + 1 for a in also) or \
            [a["n"] for a in also] != [9, 10]:
        return False, f"PROTOCOL FAIL: A177014's derived claim came out {also}"
    if also_settles("A177013", ref.KNOWN["A177013"][10], 10, [10]):
        return False, "PROTOCOL FAIL: A177013 claims a rider it does not have"
    # and the published rider table agrees with what the identity claims
    for n, v in ref.KNOWN["A177014"].items():
        if ref.KNOWN_ALSO["A226935"].get(n) != v + 1:
            return False, f"PROTOCOL FAIL: A226935({n}) is not A177014({n}) + 1"
    return True, ("protocol ok, both families: each frontier term accepted at "
                  "its true run with a factor witness for its composite "
                  "stopper, and a run one too long and a mislabelled earlier "
                  "term both rejected; the derived claim (A226935 = A177014 "
                  "+ 1 at every settled index) comes out as the identity says "
                  "and agrees with the published rider table, and A177013 "
                  "claims no rider")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing."""
    raised = []
    eng = gpu.GpuEngine(12, "A177014", p1=13, p2=None, p3=None, q2=1024)
    ceil = cpu.k_ceil(12, "A177014")
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
        eng.sweep(0, 2, k_min=cpu.k_floor(1024, 12, "A177014"))
        return False, "CEILING FAIL: a clip AT the floor was accepted"
    except ValueError:
        raised.append("gpu k_min <= floor")
    c = cpu.CpuEngine(12, "A177014", q2=1024)
    try:
        c.survivors(10 ** 5, cpu.k_ceil(12, "A177014") + 10)
        return False, "CEILING FAIL: the CPU engine swept past k_ceil"
    except ValueError:
        raised.append("cpu k_ceil")
    # the two signs share ONE ceiling (fladder_search.k_ceil): huntlib's
    # measured K_CEIL, above both crossings, and the engines enforce it on
    # the -1 family too -- and refuse it tight: the last whole period under
    # it sweeps (checked, not swept), the next raises
    if cpu.k_ceil(15, "A177014") != ceiling.K_CEIL or \
            cpu.k_ceil(15, "A177013") != ceiling.K_CEIL or \
            not cpu.k_proof(15, "A177014") < cpu.k_ceil(15, "A177014") or \
            not cpu.k_proof(15, "A177013") < cpu.k_ceil(15, "A177013"):
        return False, ("CEILING FAIL: the family ceilings are not the "
                       "one K_CEIL G10 pins")
    engm = gpu.GpuEngine(12, "A177013", p1=13, p2=None, p3=None, q2=1024)
    ceilm = cpu.k_ceil(12, "A177013")
    try:
        engm.sweep(ceilm // engm.W - 1, ceilm // engm.W + 2)
        return False, "CEILING FAIL: a -1 engine swept past K_CEIL"
    except ValueError:
        raised.append("gpu k_ceil (-1, past the crossing, at K_CEIL)")
    jc = ceilm // engm.W
    engm._check_window(jc - 1, jc, None)        # the last period under it
    try:
        engm._check_window(jc, jc + 1, None)
        return False, "CEILING FAIL: the first period past K_CEIL was accepted"
    except ValueError:
        raised.append("gpu k_ceil tight to one period")
    try:
        cpu.CpuEngine(12, "A177013", q2=1024).survivors(10 ** 5, ceilm + 10)
        return False, "CEILING FAIL: a -1 CPU engine swept past K_CEIL"
    except ValueError:
        raised.append("cpu k_ceil (-1)")
    # The floor BITES at every filter here: the smallest value is x + s, so
    # a sieve to q2 is valid only from x > q2 - s.  Checked at a campaign
    # filter, where it is q2 itself.
    lowf = cpu.k_floor(1024, 12, "A177014")
    if lowf < 1000:
        return False, (f"CEILING FAIL: the n = 12 floor is {lowf}, so the "
                       f"floor check is vacuous")
    try:
        c.survivors(lowf, lowf + 10 ** 5)
        return False, "CEILING FAIL: the CPU engine swept at the floor"
    except ValueError:
        raised.append("cpu floor (n = 12, floor = %d)" % lowf)
    try:
        gpu.wheel(7, "A177014", 53)          # a flat wheel far past RES_MAX
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(15, "A177014", p1=31, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    try:
        gpu.GpuEngine(7, "A177014", p1=13, p2=37, p3=None, q2=4096)
        return False, "CEILING FAIL: an oversized second level was accepted"
    except ValueError:
        raised.append("gridDim.y")
    try:
        gpu.GpuEngine(gpu.NRES_MAX + 1, "A177014", p1=13, p2=None,
                      p3=None, q2=1024)
        return False, ("CEILING FAIL: a filter longer than the tail's "
                       "residue list was accepted")
    except ValueError:
        raised.append("nforms <= NRES_MAX")
    for unit in (30, 10, 12):
        try:
            gpu.GpuEngine(15, "A177014", p1=13, p2=None, p3=None, q2=1024,
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


def _first_prime_rung(fam, x, n_max=24):
    """The first rung i <= n_max whose value i!*x + s is a probable prime
    past the deterministic bound, or None -- a drill at an arbitrary x has
    to take the value it is given."""
    s = ref.sign(fam)
    for i in range(1, n_max + 1):
        v = math.factorial(i) * x + s
        if v >= MR_VALID_BELOW and sprp_base2(v) and mr_is_prime(v):
            return i
    return None


def _certificate_drill():
    """A discovery past the proof crossing is PROVED, not just tested --
    on BOTH signs, and at the CEILING.

    THE ROUTE IS THE WHOLE POINT OF THIS PROJECT'S CEILING.  Value i is
    i!*x + s, so (i!*x + s) - s = i!*x with i! i-smooth: ONE factorization
    of x factors every value's N -+ 1 at once.  Below the crossing every
    certificate takes the deterministic route.  Above it the structure does
    the work: BLS75 Theorem 1 on V - 1 (s = +1, A177014) or Theorem 15, the
    N+1 Lucas test, on V + 1 (s = -1, A177013), and each proof must
    re-verify from scratch and refuse a neighbouring value.

    Drilled on each family's frontier term (every value under the bound),
    on the first x past k_proof(n, F) whose TOP value n!*x + s is a
    probable prime (the crossing this campaign passes at x = 2.5e12 for
    n = 15 and 9.3e9 for n = 17 -- far below the modelled medians, so this
    is the normal path here and not an edge case), and then AT K_CEIL on
    both signs: a worst-case x (the unit times a balanced semiprime,
    huntlib.ceiling.hard_k) and an x with a prime factor above the
    deterministic bound, whose certificate must carry a subproof that
    cannot be stripped.
    """
    parts = []
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        certs, unproved = certify_run(x, top, fam)
        if unproved or len(certs) != top:
            return False, (f"CERTIFICATE FAIL: {fam} a({top}) left "
                           f"{unproved} unproved ({len(certs)} certificates)")
        if any(c.get("proof") != "deterministic-mr" for c in certs.values()):
            return False, ("CERTIFICATE FAIL: a value under the bound took "
                           "the certificate route")
        parts.append(f"{fam} a({top})'s {top} values take the deterministic "
                     f"route and re-verify")
    # past the crossing, both signs, at the filters the campaigns cross it
    for fam, n in (("A177014", 15), ("A177013", 17)):
        want = "bls75-thm1" if ref.sign(fam) > 0 else "bls75-thm15"
        unit = cpu.forced_unit(n, fam)
        s_ = ref.sign(fam)
        m = -(-cpu.k_proof(n, fam) // unit)
        xx = None
        for _ in range(6000):
            cand = unit * m
            v = math.factorial(n) * cand + s_
            if v >= MR_VALID_BELOW and sprp_base2(v) and mr_is_prime(v):
                xx = cand
                break
            m += 1
        if xx is None:
            return False, (f"CERTIFICATE FAIL: no x of {fam} past the "
                           f"crossing at n = {n} with a probable-prime top "
                           f"value in 6000 tries")
        certs, unproved = certify_run(xx, n, fam, only=(n,))
        c = certs.get(str(n))
        if unproved or c is None or c.get("proof") != want:
            return False, (f"CERTIFICATE FAIL: {fam} {n}!*x {s_:+d} at x = "
                           f"{xx:.4g} (past the bound) was not proved by "
                           f"{want}: {c and c.get('proof')}")
        if int(c["N"]) != math.factorial(n) * xx + s_ or int(c["R"]) != 1:
            return False, (f"CERTIFICATE FAIL: the {want} proof is not about "
                           f"the value, or N -+ 1 was not factored completely")
        ok, why = certificate.verify(c)
        if not ok:
            return False, (f"CERTIFICATE FAIL: the {want} proof does not "
                           f"re-verify: {why}")
        if certificate.verify(dict(c, N=int(c["N"]) + 2))[0]:
            return False, (f"CERTIFICATE FAIL: the {want} proof verified for "
                           f"a neighbouring N")
        if certificate.verify({"proof": "deterministic-mr",
                               "N": int(c["N"])})[0]:
            return False, ("CERTIFICATE FAIL: a deterministic-MR claim past "
                           "the bound was accepted as a proof")
        parts.append(f"{fam} at n = {n}: {n}!*x {s_:+d} = "
                     f"{math.factorial(n) * xx + s_:.4g} past the crossing is "
                     f"proved by {want} on {n}!*x factored completely "
                     f"({len(c['factors'])} primes), re-verifies, refused for "
                     f"N + 2 and as a bare MR claim")
    # AT THE CEILING, both signs: the worst-case x, then the recursion
    t0 = time.time()
    for fam in ref.FAMILIES:
        n = 15
        unit = cpu.forced_unit(n, fam)
        want = "bls75-thm1" if ref.sign(fam) > 0 else "bls75-thm15"
        for label, maker in (("hard", lambda sd: ceiling.hard_k(
                                  ceiling.K_CEIL - 10 ** 38, unit, seed=sd)[0]),
                             ("big-prime", lambda sd: ceiling.big_prime_k(
                                  ceiling.K_CEIL // 10 ** 6 + sd * 10 ** 30,
                                  unit)[0])):
            xx, i = None, None
            for sd in range(1, 40):
                x = maker(sd)
                if x >= cpu.k_ceil(n, fam):
                    return False, (f"CERTIFICATE FAIL: the {label} x is past "
                                   f"the ceiling")
                i = _first_prime_rung(fam, x)
                if i is not None:
                    xx = x
                    break
            if xx is None:
                return False, (f"CERTIFICATE FAIL: no {label} x of {fam} near "
                               f"K_CEIL with a probable-prime value in 39 tries")
            certs, unproved = certify_run(xx, i, fam, only=(i,))
            c = certs.get(str(i))
            if unproved or c is None or c.get("proof") != want:
                return False, (f"CERTIFICATE FAIL ({label}, {fam}): rung {i} "
                               f"at x = {xx:.4g} not proved by {want}: "
                               f"{c and c.get('proof')}")
            if int(c["R"]) != 1 or not certificate.verify(c)[0]:
                return False, (f"CERTIFICATE FAIL ({label}, {fam}): the proof "
                               f"at the ceiling is incomplete or does not "
                               f"re-verify")
            if certificate.verify(dict(c, N=int(c["N"]) + 2))[0]:
                return False, (f"CERTIFICATE FAIL ({label}, {fam}): verified "
                               f"for a neighbouring N")
            if label == "big-prime":
                subs = c.get("subproofs") or {}
                big = [p for p in c["factors"] if int(p) >= MR_VALID_BELOW]
                if not big or any(p not in subs for p in big):
                    return False, (f"CERTIFICATE FAIL ({fam}): the prime "
                                   f"factor of x above the bound carries no "
                                   f"subproof")
                if certificate.verify({a: b for a, b in c.items()
                                       if a != "subproofs"})[0]:
                    return False, (f"CERTIFICATE FAIL ({fam}): the proof "
                                   f"stripped of its subproof still verified")
                parts.append(f"{fam} at x = {xx:.3g} (a "
                             f"{len(str(big[0]))}-digit prime factor above "
                             f"the bound): {want} with a subproof of it, "
                             f"which cannot be stripped")
            else:
                parts.append(f"{fam} at x = {xx:.3g} (the unit x two "
                             f"{len(str(max(int(p) for p in c['factors'])))}"
                             f"-digit primes): {want}, R = 1, re-verified")
    parts.append(f"the four ceiling certificates took {time.time() - t0:.1f} s "
                 f"in all")
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
            ("one-level", "A177013", dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 1200, 457),
            ("two-level", "A177014", dict(p1=19, p2=31, p3=None, q2=8192,
                                          unit=6, pb=32),
             10 ** 15, 3, 1),
            ("three-level", "A177013", dict(p1=13, p2=17, p3=19, q2=128,
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
    # -- the campaigns' engine -- where a period is 6 times an x' period
    # and the seam must still close.
    # pb = 32 so a SEGMENT is 32 periods rather than 224: the seam is what
    # is under test, and a whole production segment of this wheel is 1.4e11
    # candidates.  G15 pins the stream's independence from pb.
    for eng in (gpu.GpuEngine(15, "A177013", p1=11, p2=17, p3=23, q2=128,
                              nu=4, pb=32),
                gpu.GpuEngine(16, "A177014", p1=11, p2=19, p3=29, q2=128,
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
    pool's chunked answer == the serial one."""
    # 150 periods of the (13],(23] wheel at n = 10 is 3.3e10 of line, which
    # at that density and sieve depth is a few thousand survivors
    eng = gpu.GpuEngine(10, "A177013", p1=13, p2=23, p3=None, q2=4096)
    j0 = eng.j_of(10 ** 13)
    surv = eng.survivors_j(j0, j0 + 150)
    if len(surv) < 3 * CHUNK:
        return False, (f"CLASSIFY FAIL: only {len(surv)} survivors -- the "
                       f"drill cannot span several chunks")
    two = [sprp_run(k, "A177013", 18) for k in surv]
    full = []
    for k in surv:
        r = 0
        while r < 18 and mr_is_prime(math.factorial(r + 1) * k - 1):
            r += 1
        full.append(r)
    if two != full:
        i = next(i for i in range(len(surv)) if two[i] != full[i])
        return False, (f"CLASSIFY FAIL: two-pass sprp gave run {two[i]} and "
                       f"the all-bases chain {full[i]} at x = {surv[i]}")
    with _pool_factory(2) as pool:
        parts = _submit(pool, "A177013", 18, surv)
        got = [r for ks, f in parts for r in f.result()]
    if got != full:
        return False, "CLASSIFY FAIL: the pool's chunked result differs"
    # the run is NOT capped at the filter -- a rider is a longer run on the
    # same x -- but it IS capped at `cap`: A177014's a(9) = a(10) reads 9
    # under a cap of 9 and 10 under a cap of 30, and A177013's a(9) reads 9
    # under both (a(10) is a different x)
    x = ref.KNOWN["A177014"][9]
    if sprp_run(x, "A177014", 9) != 9 or sprp_run(x, "A177014", 30) != 10:
        return False, ("CLASSIFY FAIL: A177014's rider a(9) = a(10) does not "
                       "read 9 under cap 9 and 10 under cap 30")
    x = ref.KNOWN["A177013"][9]
    if sprp_run(x, "A177013", 9) != 9 or sprp_run(x, "A177013", 30) != 9:
        return False, ("CLASSIFY FAIL: A177013's a(9) does not read 9 under "
                       "both caps")
    return True, (f"classification ok: two-pass sprp == all-bases chain on "
                  f"{len(surv)} real survivors (max run {max(full)}), "
                  f"{len(parts)} pool chunks reassemble to the serial answer, "
                  f"and the run is bounded by the cap alone -- A177014's "
                  f"rider a(9) = a(10) reads 10 past the filter, A177013's "
                  f"a(9) stops at 9")


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
             workers=1, worker_ramp=WORKER_RAMP_S)
    d.update(over)
    for k, v in d.items():
        setattr(a, k, v)
    return a


def _promotion_drill():
    """A FIND MOVES THE FILTER, and the cursor must move to the find.

    The published term is x, so the line does not change at a promotion;
    what changes is every constant derived from the filter -- the kill sets
    (larger: K(q,n) is a subset of K(q,n+1)), the wheel the period cap
    admits, the sieve depth, the period, the window width.  The unit stays
    6, and that is asserted too.

    What is asserted, on a scratch checkpoint:
      * promoting rebuilds the engine at the new filter, with strictly
        more forms and a unit of 6 either side;
      * the cursor lands at the END OF THE LINE THE OLD FILTER CLASSIFIED
        (floored onto the new period), never below the new filter's floor,
        which is the term just found -- so nothing is skipped
        (monotonicity), nothing the old filter already classified to n + 8
        is re-swept, and the clip is gone once the cursor is past the floor;
      * the ladder retires the rungs of the term that was found;
      * the checkpoint round-trips at the new filter and reloads to the same
        place;
      * and a cursor stored at ONE filter is REFUSED by a campaign whose
        frontier puts it at another.  That last one is this project's
        version of the failure that cost the repo two campaign starts: the
        stored number is fine, its plan is not, and only an assertion
        catches it (OPTIMIZATION.md 2.9).
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="fladder-promote-")
    path = str(pathlib.Path(tmp) / "c.json")
    rows = []
    for fam in ref.FAMILIES:
        pol = _POLICIES[fam].at(path)
        c = Campaign(_args_for(fam), ckpt=path, cursor=pol)
        n0 = c.filter_n()
        before = (c.eng.n, c.eng.unit, c.eng.W, c.eng.q2,
                  (c.eng.p1, c.eng.p2, c.eng.p3), c.eng.nforms)
        if c.j != c.floor_period() or c.x_start() <= 0:
            return False, (f"PROMOTION FAIL: {fam} fresh campaign did not "
                           f"start at its floor period")
        # a fabricated find at the filter's floor, recorded the way a real
        # one is -- the term itself is not checked here (the protocol drill
        # does that); what is under test is what the campaign does NEXT
        found_x = c.x_start() + 10
        c.found[str(n0)] = int(found_x)
        # the segment that held the find closed: the boundary sits one
        # segment past the floor period, and everything below it was
        # classified at the old filter
        c.boundary = c.j + c.eng.seg_periods
        covered = c.boundary * c.eng.W
        c.follow_frontier()
        after = (c.eng.n, c.eng.unit, c.eng.W, c.eng.q2,
                 (c.eng.p1, c.eng.p2, c.eng.p3), c.eng.nforms)
        if after[0] != n0 + 1 or after[5] != before[5] + 1:
            return False, (f"PROMOTION FAIL: {fam} did not move to n = {n0+1} "
                           f"with one more form")
        if after[1] != 6 or before[1] != 6:
            return False, (f"PROMOTION FAIL: {fam} unit is not 6 on both "
                           f"sides of the promotion ({before[1]}, {after[1]})")
        want_j = max(c.floor_period(), covered // c.eng.W)
        if c.u != 0 or c.j != want_j or c.boundary != c.j:
            return False, (f"PROMOTION FAIL: {fam} resumed at (j, u) = "
                           f"({c.j}, {c.u}) after the promotion, boundary "
                           f"{c.boundary}; expected period {want_j} (the end "
                           f"of the classified line {covered} floored onto "
                           f"the new period {c.eng.W}, floor period "
                           f"{c.floor_period()})")
        if c.j <= c.floor_period():
            return False, (f"PROMOTION FAIL: {fam}'s drill did not exercise "
                           f"the carried coverage: the resumed period {c.j} "
                           f"is the floor period {c.floor_period()}")
        if c.j * c.eng.W > covered or (c.j + 1) * c.eng.W <= covered:
            return False, (f"PROMOTION FAIL: {fam}'s resumed period {c.j} is "
                           f"not the FLOOR of the classified line {covered} "
                           f"onto the period {c.eng.W}: a gap or a wasted "
                           f"period")
        if c.k_min() is not None or c.cover_x != covered:
            return False, (f"PROMOTION FAIL: {fam} still clips at the floor "
                           f"(k_min {c.k_min()}) with the cursor past it, or "
                           f"cover_x {c.cover_x} != {covered}")
        if c.swept_k() != c.j * c.eng.W:
            return False, (f"PROMOTION FAIL: {fam}'s coverage claim "
                           f"{c.swept_k()} is not the resumed boundary")
        # the new floor is the term just found, so nothing below it is swept
        # and nothing above it is skipped
        if c.x_start() != max(found_x, cpu.k_floor(c.eng.q2, n0 + 1, fam) + 1):
            return False, (f"PROMOTION FAIL: {fam}'s new floor is "
                           f"{c.x_start()}, not the found term {found_x}")
        if any(p.startswith(f"a({n0})") for p in c.passed):
            return False, f"PROMOTION FAIL: {fam} kept a retired rung"
        # round trip at the new filter
        if not c.save():
            return False, f"PROMOTION FAIL: {fam}'s post-promotion save did not land"
        c2 = Campaign(_args_for(fam), ckpt=path, cursor=_POLICIES[fam].at(path))
        if (c2.filter_n(), c2.j, c2.u, c2.cover_x) != (n0 + 1, c.j, 0, covered):
            return False, (f"PROMOTION FAIL: {fam} reloaded at "
                           f"({c2.filter_n()}, {c2.j}, {c2.u}, cover "
                           f"{c2.cover_x}), not ({n0+1}, {c.j}, 0, {covered})")
        # ... and a cursor whose stored filter disagrees with the frontier is
        # REFUSED rather than read against the wrong plan
        import json as _json
        with open(path) as fh:
            st = _json.load(fh)
        st["n"] = n0                      # stale filter, fresh `found`
        checkpoint.save(path, st)
        try:
            Campaign(_args_for(fam), ckpt=path,
                     cursor=_POLICIES[fam].at(path))
            return False, (f"PROMOTION FAIL: {fam} read a cursor stored at "
                           f"filter {n0} while hunting a({n0+1})")
        except ValueError:
            pass
        rows.append(f"{fam} n = {n0} -> {n0+1}: wheel {before[4]} -> "
                    f"{after[4]}, q2 {before[3]} -> {after[3]}, period "
                    f"{before[2]:.3g} -> {after[2]:.3g}, unit 6 -> 6")
        # ... AND THE PROMOTION THAT CHANGES THE RECORD: a campaign that has
        # found a(11)..a(17) promotes into n = 18, where the plan is the
        # wheel to 53 and no u64 window admits its period, so the engine
        # the campaign builds there must come up on the WIDE record by
        # itself -- from the plan, at runtime, with no flag -- and the one
        # at n = 17 narrow.  This is the detection the owner asked for.
        for m in range(n0, 17):
            c.found[str(m)] = int(c.x_start() + 10 * m)
        c.eng = c._build_engine(c.filter_n())
        if c.filter_n() != 17 or c.eng.wide:
            return False, (f"PROMOTION FAIL: {fam} at n = {c.filter_n()} "
                           f"(wheel to {max(gpu._wheel_primes(c.eng.p1, c.eng.p2, c.eng.p3))}) "
                           f"came up {'wide' if c.eng.wide else 'narrow'}; "
                           f"expected narrow at n = 17")
        c.boundary = c.j = c.floor_period()
        c.found["17"] = int(c.x_start() + 1000)
        c.follow_frontier()
        top = max(gpu._wheel_primes(c.eng.p1, c.eng.p2, c.eng.p3))
        if c.filter_n() != 18 or top != 53 or not c.eng.wide \
                or c.eng.seg_periods != plan_for(fam, 18)[5]:
            return False, (f"PROMOTION FAIL: {fam} promoted into n = 18 on "
                           f"the wheel to {top}, {c.eng.seg_periods} periods, "
                           f"{'wide' if c.eng.wide else 'NARROW'} record -- "
                           f"expected the wheel to 53 on the wide record at "
                           f"{plan_for(fam, 18)[5]} periods, chosen by the "
                           f"engine from the plan")
        if (c.eng.seg_periods + 1) * c.eng.Wp < 1 << 64:
            return False, (f"PROMOTION FAIL: {fam} n = 18's segment fits a "
                           f"u64 window -- the drill is not exercising the "
                           f"record change")
        rows.append(f"{fam} n = 17 -> 18: wheel to 47 (narrow record) -> "
                    f"wheel to 53 ({c.eng.seg_periods} periods, WIDE record, "
                    f"chosen at runtime from the plan)")
        os.remove(path)
        for ext in (".bak",):
            if os.path.exists(path + ext):
                os.remove(path + ext)
    return True, ("promotion ok: " + "; ".join(rows) + " -- the record "
                  "follows the plan at runtime (narrow at n = 17, wide at "
                  "n = 18, decided in the engine from the wheel and window it "
                  "is handed, no flag), the cursor lands "
                  "at the end of the line the old filter classified, floored "
                  "onto the new period and never below the new floor (the "
                  "term just found), the clip is gone past the floor, the "
                  "carried coverage round-trips through the checkpoint, the "
                  "retired rungs go, and a cursor stored at the wrong filter "
                  "is REFUSED rather than read against the wrong plan")


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
    # the rider spelling opens the right campaign
    if ref.family("A226935") != "A177014":
        return False, "FAMILY FAIL: the rider alias does not resolve"
    # and the PER-FILTER plan is admissible at every filter it is used at,
    # with the unit 6 at every one of them -- derived, and asserted, because
    # a unit is a coverage claim
    units = {}
    for f in fams:
        for n in range(open_n(f), open_n(f) + 9):
            unit, p1, p2, p3, q2, pb = plan_for(f, n)
            cpu.assert_unit(n, f, unit)      # raises if not forced there
            units[n] = unit
    if [units[n] for n in range(11, 19)] != [6] * 8:
        return False, (f"FAMILY FAIL: the per-filter units came out "
                       f"{[units[n] for n in range(11, 19)]}, not 6 at "
                       f"every filter")
    # THE PERIOD MUST BE SMALL AGAINST THE SEARCH, and that is a property of
    # the plan nothing else checks.  The wheel plan maximises candidate
    # density, and a denser wheel is a LONGER period -- but the candidates of
    # a period come out in (t, s, u, j) order, so a find is only known to be
    # the LEAST once its period closes (CONVENTIONS.md "Two cursors").  A
    # find therefore costs up to one period of over-sweep, and a plan whose
    # period approached the search would spend more on that than the density
    # ever bought.  square-ladders rejected a wheel for exactly this reason
    # and re-priced it two terms later, when the same period had become 0.13%
    # of the hunt; the ratio is what matters, so it is checked per filter.
    tight = []
    records = {}
    for f in fams:
        for n in range(open_n(f), open_n(f) + 9):
            unit, p1, p2, p3, q2, pb = plan_for(f, n)
            W = unit
            for q in gpu._wheel_primes(p1, p2, p3):
                if unit % q:
                    W *= q
            med = model.quantile(f, n, model.floor_for(f, n, c_front(f)), 0.5)
            if med is None:
                continue
            seg = pb * W
            if seg > SEGMENT_MARGIN * med:
                return False, (f"FAMILY FAIL: {f} n = {n} plans a segment of "
                               f"{pb} periods x {W:.4g} = {seg:.4g} against "
                               f"a modelled median of {med:.4g} -- over the "
                               f"{SEGMENT_MARGIN}x margin a find's "
                               f"over-sweep allows")
            tight.append((med / seg, f, n))
            # THE RECORD FOLLOWS THE PLAN AT RUNTIME: the wheel to 53 (n >= 18)
            # has W' = 5.4e18, which no u64 window admits, so the engine the
            # campaign builds there must come up WIDE by itself, and the
            # wheel to 47 narrow -- decided in GpuEngine from (wheel, window),
            # with no flag anywhere in this file
            top = max(gpu._wheel_primes(p1, p2, p3))
            records[(f, n)] = (top, pb)
    for (f, n), (top, pb) in sorted(records.items()):
        if n in (17, 18):
            eng = gpu.GpuEngine(n, f, *plan_for(f, n)[1:4], q2=plan_for(f, n)[4],
                                unit=plan_for(f, n)[0], pb=pb, seg_cap=pb)
            want_wide = top >= 53
            if eng.wide != want_wide or eng.seg_periods > pb:
                return False, (f"FAMILY FAIL: {f} n = {n} plans the wheel to "
                               f"{top} at {pb} periods and the engine came up "
                               f"{'wide' if eng.wide else 'narrow'} with pv "
                               f"{eng.pv} -- expected "
                               f"{'wide' if want_wide else 'narrow'} at {pb}")
    tight.sort()
    # each of these contains a prime that is NOT forced here (5, 7, 17) or
    # is not squarefree, so each must RAISE at every filter
    for n, wrong in ((11, 30), (17, 30030), (18, 10), (16, 12), (17, 42)):
        try:
            cpu.assert_unit(n, "A177013", wrong)
            return False, (f"FAMILY FAIL: unit {wrong} accepted at n = {n}, "
                           f"where one of its primes is not forced")
        except ValueError:
            pass
    return True, ("families stay apart: two distinct config keys, checkpoint "
                  "files and ledgers, no policy reads the other's cursor, the "
                  "rider alias resolves, the PER-FILTER plan is admissible at "
                  "every filter n = 11..19 with the unit 6 at each (and 30, "
                  "30030, 10, 42 and the non-squarefree 12 refused), every "
                  "planned SEGMENT fits its own search (the tightest is %s "
                  "n = %d at %.2f medians per segment, against a %gx margin; "
                  "a find costs at most one segment of over-sweep, inherited "
                  "by the next filter), and the engine the campaign builds "
                  "from the plan comes up narrow at n = 17 (wheel to 47) and "
                  "WIDE at n = 18 (wheel to 53) on its own"
                  % (tight[0][1], tight[0][2], 1 / tight[0][0], SEGMENT_MARGIN))


def _campaign_wiring_drill(fam="A177013"):
    """Build a campaign and exercise everything the loop touches, without
    sweeping a whole period: construction from nothing at period 0, the
    status line, census and NEAR/CENSUS classification, the cached rung
    ladder, the drain of a fake in-flight launch, the pool sized from a
    real measurement, back-pressure, a find moving the filter, a save/load
    round trip, and the interrupt snapshot."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="fladder-drill-")
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
        if floor != ref.KNOWN[fam][n0 - 1]:
            return False, (f"WIRING FAIL: the floor {floor} is not a({n0-1})")
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
        c.found[str(n0)] = int(floor + 4)               # a find, unverified
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
        oldW = int(c.eng.W)
        c.follow_frontier()
        # the plan changes with the filter (a bigger kill set, and at the
        # opening a longer period the cap now admits), which is why the
        # cursor resets to the find rather than carrying over
        if c.eng.n != n0 + 1 or int(c.eng.W) == oldW:
            return False, ("WIRING FAIL: follow_frontier did not move the "
                           "filter, or the period did not change with it")
        if c.j != c.floor_period() or c.u:
            return False, "WIRING FAIL: the cursor did not reset on promotion"
        c.found.pop(str(n0))
        c.eng = c._build_engine(c.filter_n())
        c.j, c.u, c.boundary = c.floor_period(), 0, c.floor_period()
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


def selftest(fam="A177013"):
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
    ap.add_argument("--family", default="A177013",
                    help="which sequence to hunt: " +
                         ", ".join(f"{f} ({ref.FAMILIES[f]['forms']})"
                                   for f in ref.FAMILIES) +
                         "; A226935 is an alias of A177014, being that "
                         "sequence shifted by one (default A177013)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this depth on the x line (default: the "
                         "engine ceiling, huntlib.ceiling.K_CEIL = 1e40 for "
                         "every family -- where a worst-case certificate per "
                         "discovery was measured to cost seconds)")
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
