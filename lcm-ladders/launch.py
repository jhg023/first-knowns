"""The campaign for the lcm ladders -- least N with (N +- k)/k prime for
every k = 1..n, hunted as N = lcm(1..n)*x.

    python launch.py --selftest            the full gate battery (must end ALL GREEN)
    python launch.py                       the hunt: indefinite, resumable (A078502)
    python launch.py --family A074200      the other family
    python launch.py --to 1e20             stop at a chosen depth in x
    python launch.py --status              read the checkpoint and say where it is

TWO FAMILIES, FOUR OEIS ENTRIES, ONE CAMPAIGN AT A TIME.  `--family` names
the entry (lcml_reference.FAMILIES; A093554 and A093553 are accepted as
aliases of A078502 and A074200, being those sequences shifted by one).  The
two hunted families are the same multipliers with the sign flipped, so they
share every file here and every killed-set size -- but they are different
sequences with different frontiers, so each carries its OWN checkpoint under
its own config key and a campaign hunts one of them.  Each find settles its
rider entry at every index it settles, for nothing.

THE SUBSTITUTION.  (N + s*k)/k is an integer for every k <= n exactly when
L(n) = lcm(1..n) divides N.  So N = L(n)*x and the conditions are
(L(n)/k)*x + s prime for k = 1..n: one unknown, a multiplier list, a fixed
sign.  The engine sweeps x; the launcher reports N = L(n)*x.  G2 re-derives
the small terms BOTH ways -- walking N with the divisibility test the
definition states, and walking x -- so the substitution is gated, not
assumed.

THE OPENINGS (CLAUDE.md 5g, step 1 -- the test plan for every default
below), and the thing that makes this project different from every other
one here: EVERY FILTER IS A DIFFERENT LINE, AND A DIFFERENT CONFIGURATION.

    n     L(n)         unit   wheel            q2       period W      x/s
    15    360360       2      (..19](19,31](31,43]  131072  1.31e16   5.3e16
    16    720720       34     (..23](23,37](37,47]  131072  6.15e17   3.0e17
    17    12252240     2      (..19](19,31](31,43]   32768  1.31e16   3.8e16
    18    12252240     114    (..23](23,37](37,47]   32768  4.61e17   4.1e17
    19    232792560    6      (..23](23,37](37,47]   16384  6.15e17
    20    232792560    30     (..23](23,37](37,47]    8192  6.15e17

The forcing is SPORADIC: q = n + 1 is forced whenever n + 1 is prime, so the
unit is 2 at n = 15, 34 at 16, 2 again at 17 and 114 at 18.  Nothing may be
carried from one filter to the next -- not the unit, not the wheel, not the
depth, not the period.  `plan_for` derives the whole configuration per
filter and this file stores none of it; G8, G13 and G18 check the planned
configuration at every filter of both families, and `_families_stay_apart`
asserts the units really do come out 2, 34, 2, 114, 6, 30.

AND A FIND RESTARTS THE LINE.  Elsewhere in this repo a filter change keeps
the cursor: the wheel and the k line do not depend on n.  Here an x at
filter n and an x at filter n + 1 are not the same number, so on a find the
campaign rebuilds the engine and restarts at the new filter's floor.  That
floor is the term just found -- a() is non-decreasing in N because the
conditions nest -- so nothing is skipped and nothing is re-swept, and the
whole of [1, a(n)) is excluded by the find rather than by a sweep.
`_promotion_drill` is the gate for it.

WHAT IS OPEN, AND WHY IT IS WORTH A SWEEP.  A078502's frontier is Jens Kruse
Andersen's a(13) = a(14) = 7.27e18 (January 2003) and A074200's is his
a(14) = 2.92e21 (February 2004); A093554 and A093553 have never been
extended by anyone.  No entry carries a bound of any kind at any open index
and none has a b-file.  a(15) is open on all four, and the modelled median
for it is 2-3 seconds of device.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine's enforced ceiling -- k_ceil in lcml_search, huntlib.ceiling
.K_CEIL = 1e40 on x for both families -- and that is the last rung.  Below
the PROOF CROSSING k_proof(n, F) every classification is a deterministic
proof; above it the same seven-base chain is a strong probable-prime test,
the census is a count and a NEAR is a health check either way, and a
DISCOVERY is proved by CERTIFICATE on its own structure.  THE CROSSING IS
LOW HERE -- x = 9.2e18 at n = 15 and 2.7e17 at n = 17, because the largest
value is the published term itself -- so the certificate is the normal path
in this project, not an edge case: (N/i + s) - s = N/i and N = L(n)*x with
L(n) n-smooth, so ONE factorization of x proves the whole run by BLS75
Theorem 1 on V - 1 (s = +1) or Theorem 15, the N+1 Lucas test, on V + 1
(s = -1), with a subproof for any prime factor of x past the bound.  The
crossing is a [MILESTONE], not a stop.  `--to` and `--stop-on-discovery` are
the only stops and both are opt-in.  Progress is read off RUNGS taken from
the odds model's quantiles, logged as they are passed and shown with an ETA
in every [STATUS].  A rung retires with its term: the ladder is derived from
the LIVE frontier and cached on it (huntlib.rungs.LiveLadder), never
recomputed in the loop.

THE TAXONOMY, mapped to this problem (CONVENTIONS.md "the discovery
protocol").  A survivor is an x with a run length r, capped at the filter it
was sieved for:

  DISCOVERY  r > frontier: N = L(n)*x settles a(frontier+1) ... a(r) at
             once, each logged once, all evidenced under the FIRST value
             they belong to.  Whether it settles MORE than the filter it was
             found at -- a RIDER -- is decided on N, not on the filter,
             because reaching n + 1 also needs L(n+1) | N.  Verified three
             ways plus a witness for whatever stops the run, and a
             re-verified certificate for every value.  The evidence file
             records what the find settles in the rider entry: A093554(m) =
             N - 1 for A078502 and A093553(m) = N + 1 for A074200, at every
             m the find settles.
  NEAR       r == frontier: one condition short of the open term.  One line
             with its campaign ordinal, verified by the cheap legs as an
             engine health check, never evidenced.
  CENSUS     CENSUS_FLOOR <= r < frontier: counted in [STATUS], never
             narrated.
  None       r < CENSUS_FLOOR: noise, not counted.

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
engine sieves a SEGMENT of eng.seg_periods wheel periods at once (192), and
a segment's candidates come out in (t, s, u, period) order, so the x line is
contiguous only at the end of a whole segment.  COVERAGE (`boundary`, the x
below which every value is swept) advances one segment at a time and is the
only thing a least-claim rests on; WORK (`j`, `u`) advances every launch.
Values classified mid-segment are held IN THE CHECKPOINT and narrated in x
order when the segment closes.

THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER, at
start and again every time the filter moves (Campaign.size_pool: the next
launches are swept and timed, their survivors counted, a sample of them
classified, and ceil(need x POOL_MARGIN) workers ramped one at a time at
below-normal priority, huntlib.pool).  Measured at n = 15 of A078502:
104,000 survivors/s x 12.4 us = 1.29 core-seconds per second, so 3 workers.
The SIEVE DEPTH is chosen so that number lands near one core at every filter
(lcml_gpu.plan_q2), which is why it is 131072 at n = 15 and 32768 at n = 17.
The device may run at most BACKLOG_LAUNCHES ahead of the pool, so a pool
that binds throttles the device VISIBLY -- the [STATUS] line says HOST-BOUND
and by how much -- instead of silently.  Classification runs in the pool
while the device sweeps, and the WORK cursor lags behind the launches whose
survivors are still being classified, so a crash never loses a survivor it
has not yet looked at.  The throttles are `--workers`, `--gpu-yield-ms` and
`--gentle`, priced in the help text against the launch.  No machine setting
is ever changed on the owner's behalf.
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

from huntlib import ceiling, certificate, checkpoint, drills, evidence  # noqa: E402
from huntlib import pool as _pool                               # noqa: E402
from huntlib import shutdown                                    # noqa: E402
from huntlib.gpu import device_report                           # noqa: E402
from huntlib.hlog import Heartbeat, banner, census_str, log     # noqa: E402
from huntlib.primes import (MR_VALID_BELOW, factor_witness,     # noqa: E402
                            mr_is_prime, sprp_base2)
from huntlib.rungs import Ladder, LiveLadder, eta_str           # noqa: E402

import lcml_gpu as gpu                                       # noqa: E402
import lcml_model as model                                   # noqa: E402
import lcml_reference as ref                                 # noqa: E402
import lcml_search as cpu                                    # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")

# NOTHING ABOUT THE WHEEL IS A CONSTANT HERE.  The unit, the three wheel
# levels, the sieve depth and the window width are all PLANNED per filter,
# because all four change with n and none of them changes monotonically:
# the unit is 2 at n = 15, 34 at n = 16, 2 again at n = 17 and 114 at n = 18
# (the forcing is sporadic -- lcml_reference G2c), and the kill counts jump
# by a factor of q at every filter where a prime enters L(n).  A constant
# carried one filter forward is a coverage claim the sweep never made.
# `plan_for` is the ONE place a configuration is derived, and `--status`,
# the campaign and every drill go through it (OPTIMIZATION.md 2.9: derive
# configuration in exactly one place).
PLAN_VERSION = "p1"               # bump when plan_for's answer changes


def plan_for(fam, n):
    """(unit, p1, p2, p3, q2) for filter n of family F -- the configuration
    the campaign runs there, and the fastest correct one it has (CLAUDE.md
    5g).  Measured, not assumed: the wheel maximises candidates per unit of
    line subject to the 2^63 reduction bound and a window worth having, and
    the depth is the smallest whose analytic survivor rate two workers can
    absorb (lcml_gpu.wheel_plan, lcml_gpu.plan_q2)."""
    fam = ref.family(fam)
    unit = cpu.forced_unit(n, fam)
    p1, p2, p3 = gpu.wheel_plan(n, fam, unit)
    q2 = gpu.plan_q2(n, fam, unit, max(x for x in (p1, p2, p3) if x))
    return unit, p1, p2, p3, q2


def x_floor(fam, n, frontier_N):
    """Where the sweep for a(n) starts, in x at filter n.

    a() is non-decreasing in N (the conditions nest), so nothing at or below
    the previous term can be the next one and the floor is free.  It is a
    FLOOR IN N converted to this filter's x by rounding UP, which is the
    only safe direction: an x below ceil(prev/L) stands for an N already
    excluded, and one above would skip line.  The engine's own floor (the
    exception zone, where a value could BE the prime dividing it) is a
    handful of x here and is taken as well."""
    fam = ref.family(fam)
    _u, _a, _b, _c, q2 = plan_for(fam, n)
    return max(-(-int(frontier_N) // ref.L(n)),
               cpu.k_floor(q2, n, fam) + 1)


def open_n(fam):
    """The filter a FRESH campaign of this family opens at: the index after
    the published frontier."""
    return max(ref.KNOWN[ref.family(fam)]) + 1




# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a period.  On
# the v2 wheel a launch is ONE third-level residue below c = 17 -- 7.3e9
# candidates and ~15 ms at A078502's n = 15, and fewer at n = 17's
# opening -- and two from c = 17 (1.5e9, 4 ms), so 32 launches is 1.3 s at
# n = 15, 5.5 s at the -1 openings and 0.13 s at n = 17: what an interrupt
# costs to redo, and the denominator that prices --gpu-yield-ms.  A period
# is 1,672 launches at n = 15 and 756 at n = 17, so the mid-period save
# fires throughout, rate-limited by CKPT_MIN_S.
CKPT_LAUNCHES = 32
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
# THE ENGINE IS THIS PROJECT'S OWN v1: the linear ladders' v4 window sieve
# with the multiplier list swapped from i to L(n)/i, and every tuning
# constant re-swept for a regime whose wheel is 2,400x weaker
# (OPTIMIZATION_LOG.md).  The window width and the shared-queue budget moved
# together (64 -> 192 and 12 -> 20 KB, 1.288x), the sieve depth became a
# per-filter plan rather than a constant, and a latent kernel bug that only
# a non-power-of-two window can reach was fixed.
ENGINE_VERSION = "v1"
# No predecessor: this project's engine is its own first version.  The list
# is kept (empty) because CursorPolicy takes it and because the moment a v2
# exists it belongs HERE and nowhere else -- a list of old keys given to two
# of the three readers is a green battery and a campaign that will not start
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
           f"-cpl{gpu.CAND_PER_LAUNCH4.bit_length() - 1}")
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


def verify(N, run, fam):
    """The three independent confirmations plus the bounding witness.

    Everything is stated on N, the published term, because that is what the
    OEIS entry claims and because a RIDER -- a find whose run passes the
    filter it was swept at -- has values that belong to L(run), not to the
    filter's L(n).  Value i is N/i + s, and i must DIVIDE N: that is half
    the condition, and a run stops at the first i that does not divide N
    just as surely as at the first composite.

    1. huntlib's Miller-Rabin, which is a PROOF below the proof crossing
       k_proof(n, F) (G10) and a seven-base strong probable-prime chain
       above it -- where the certificate (certify_run), not this leg, is
       the proof;
    2. sympy's BPSW, an independent implementation, which must agree on the
       run LENGTH and not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense x line and uses no wheel at all, must
       agree that this x survives a sieve at a DIFFERENT depth from the
       campaign's.

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
    N = int(N)
    legs = {"mr_chain": all(N % i == 0 and mr_is_prime(N // i + s)
                            for i in range(1, run + 1)),
            "sympy_bpsw": ref.run_length_N(fam, N, cap=run + 1) == run,
            "resieve_other_wheel": cpu.CpuEngine(run, fam, q2=4096).survives(
                N // ref.L(run))}
    stop_i = run + 1
    if N % stop_i:
        # the run is stopped by DIVISIBILITY, not by a composite: L(run+1)
        # does not divide N, so value run+1 is not an integer at all.  That
        # is a stronger stop than a composite and needs no witness.
        legs["stopper_composite"] = True
        return all(legs.values()), legs, {"i": stop_i, "value": None,
                                          "factor": None,
                                          "why": f"{stop_i} does not divide N"}
    stop = N // stop_i + s
    legs["stopper_composite"] = not mr_is_prime(stop)
    ok = all(legs.values())
    wit = stopper_witness(stop) if legs["stopper_composite"] else None
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


def certify_run(N, run, fam, only=None):
    """A checkable primality certificate for every value N/i + s of the
    run: ({str(i): proof}, [the i left UNPROVED]).

    THIS PROJECT IS RULE 5h'S BEST CASE.  Value i is N/i + s, so

        (N/i + s) - s  =  N/i  =  L(n)/i * x

    is completely factored the moment N is -- and N = L(n)*x with L(n)
    n-smooth, so ONE factorization of x factors every value's N -+ 1 at
    once.  Below the deterministic bound huntlib.certificate.prove answers
    with the seven-base test, which IS the proof there.  Above it every
    value gets BLS75 Theorem 1 on N - 1 (s = +1, A074200) or Theorem 15,
    the N+1 test with a Lucas sequence per prime, on N + 1 (s = -1,
    A078502), from that same factorization with i's own factors divided
    out.  A prime factor of x past the bound is admitted with a SUBPROOF of
    its own (huntlib.certificate's recursion), so the certificate is a
    finite tree whose leaves are deterministic tests.  A value the shared
    factorization cannot prove falls back to certificate.prove's own
    bounded search on both sides.

    Every proof is RE-VERIFIED from scratch before it is returned.  A
    certificate that was not checked is a claim, not a certificate.
    """
    from sympy import factorint, primerange
    fam = ref.family(fam)
    N, s = int(N), ref.sign(fam)
    # ONE factorization for the whole run, and it is taken off N ITSELF
    # rather than off N // L(run).  The smooth part is peeled by trial
    # division first -- N = L(n)*x and L(n) is n-smooth by construction, so
    # this costs nothing and leaves only x's hard part -- and only that goes
    # to factor_full (huntlib's bounded chain then sympy's factorint, which
    # the ceiling K_CEIL was measured against).  Taking it off N // L(run)
    # would assume L(run) divides N, which is true of a real discovery and
    # NOT of an arbitrary (N, i) a drill hands in: the division would
    # silently truncate and the certificate would be about a different
    # number.
    fac = {}
    rest = N
    for p in primerange(2, 128):
        while rest % p == 0:
            fac[int(p)] = fac.get(int(p), 0) + 1
            rest //= p
    if rest > 1:
        for p, e in certificate.factor_full(rest).items():
            fac[int(p)] = fac.get(int(p), 0) + int(e)
    certs, unproved = {}, []
    for i in (range(1, run + 1) if only is None else only):
        if N % i:
            continue
        facN = dict(fac)
        for p, e in factorint(i).items():
            facN[int(p)] = facN[int(p)] - int(e)
            if facN[int(p)] == 0:
                del facN[int(p)]
        proof = (certificate.prove(N // i + s, fac=facN) if s > 0
                 else certificate.prove(N // i + s, fac_plus=facN))
        if proof is None:
            proof = certificate.prove(N // i + s)
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
        certs[str(i)] = proof
        if proof is None:
            unproved.append(int(i))
    return certs, unproved


def also_settles(fam, N, run, settles):
    """What a find settles in the DERIVED entries, as records for the
    evidence file.

    Both riders are the same integer shifted by one -- A093554 = A078502 - 1
    and A093553 = A074200 + 1, which is Sloane's own comment on each and is
    re-derived from the bare definition by lcml_reference G2d -- so a find
    settles its rider at EVERY index it settles, with no extra search and no
    extra condition.  Two entries per find, four across the two families.
    """
    fam = ref.family(fam)
    out = []
    for seq, shift in ref.FAMILIES[fam]["also"]:
        for n in settles:
            out.append({"sequence": seq, "n": int(n),
                        "value": int(N) + int(shift),
                        "claim": f"{fam}({n}) {shift:+d}"})
    return out


# ----------------------------- classification -------------------------------

def sprp_run(x, fam, n, cap, floor=CENSUS_FLOOR):
    """Run length of x at filter n, screened with a base-2 strong test and
    CONFIRMED with the deterministic chain wherever the answer matters.

    A failed base-2 test is a PROOF of compositeness (huntlib.primes), so
    the first pass can only overstate a run, never understate it.  Runs that
    come out below the census floor are never looked at again, so an
    overstatement there costs nothing; a run at or above it is recomputed
    with all seven bases, which is the deterministic answer below the proof
    crossing and a strong probable-prime answer above it (a DISCOVERY there
    is proved by certificate; the census is a count).

    Capped at n by construction: a filter-n sweep sieved for n conditions
    and can only speak about those.  Whether the find is a RIDER -- whether
    it also clears n + 1, which needs L(n+1) | N as well -- is decided by
    ref.run_length_N once, on the find, not here on every survivor.
    """
    fam = ref.family(fam)
    s = ref.sign(fam)
    cap = min(int(cap), int(n))
    r = 0
    while r < cap and sprp_base2(ref.rung(n, r + 1) * x + s):
        r += 1
    if r >= floor:
        r = 0
        while r < cap and mr_is_prime(ref.rung(n, r + 1) * x + s):
            r += 1
    return r


def _classify_chunk(task):
    """Pool worker: run lengths of a chunk of survivors, in order.

    Module-level and self-contained so it survives Windows spawn; touches
    no GPU, so workers never contend with the parent's device work."""
    fam, n, cap, ks = task
    return [sprp_run(int(k), fam, n, cap) for k in ks]


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


def _submit(pool, fam, n, cap, ks):
    """Hand a launch's survivors to the pool.  Returns [(ks_chunk, future)]
    in survivor order; with no pool the chunk is classified right here."""
    ks = [int(k) for k in ks]
    out = []
    for i in range(0, len(ks), CHUNK):
        chunk = ks[i:i + CHUNK]
        if pool is None:
            out.append((chunk, _Done(_classify_chunk((fam, n, cap, chunk)))))
        else:
            out.append((chunk, pool.submit(_classify_chunk,
                                           (fam, n, cap, chunk))))
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
        # from filter to filter (6.5e15 at n = 15, 1.8e16 at n = 16).
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
        unit, p1, p2, p3, q2 = plan_for(self.fam, n)
        return gpu.GpuEngine(n, self.fam, p1=p1, p2=p2, p3=p3, q2=q2,
                             unit=unit)

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
        """The floor of THIS filter's sweep, in x -- the monotonicity bound
        converted to this filter's line.  Re-derived from the LIVE frontier
        on every call, so it follows a find the way the ladder does."""
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
        """The k from which the CLASSIFICATION at the current filter is a
        probable-prime chain rather than a proof (lcml_search.k_proof)."""
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
                f"{self.oeis}) = {pc:.4g}: L({self.filter_n()})"
                f"*x {self.s:+d} = N {self.s:+d}, the top value, now exceeds "
                f"the deterministic Miller-Rabin "
                f"bound, so classification is a seven-base strong "
                f"probable-prime chain from here (the census is counted and "
                f"a NEAR is a health check either way) and a DISCOVERY is "
                f"proved by BLS75 certificate on "
                f"{'V - 1' if self.s > 0 else 'V + 1'} = N/i "
                f"({'Theorem 1' if self.s > 0 else 'Theorem 15, Lucas'}; "
                f"certify_run); the ceiling is k < "
                f"{cpu.k_ceil(self.filter_n(), self.fam):.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "plan": PLAN_VERSION,
                "family": self.fam,
                "sign": self.s,
                # THE FILTER IS PART OF THE CURSOR, not a derived quantity:
                # each n is its own x line with its own wheel and period, so
                # a cursor without its filter is a number without a unit.
                "n": int(self.eng.n),
                "L": int(ref.L(self.eng.n)),
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
            N = ref.term(self.eng.n, k)
            ok, legs, _ = verify(N, run, self.fam)
            if not ok:
                log("ALARM", f"NEAR value N = {N:,} run {run} failed "
                             f"verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at N = {N:,} (x = {k:,}; run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of a({frontier + 1})!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, x, run):
        frontier = self.frontier()
        n = self.eng.n
        N = ref.term(n, x)
        # A RIDER IS DECIDED HERE, ON N, NOT ON THE FILTER.  The sweep can
        # only see n conditions, but the value it found may clear more --
        # and clearing n + 1 needs L(n+1) | N as well as one more prime, so
        # it is a question about N and not about this filter's multipliers.
        # A078502's published a(13) = a(14) is exactly this.
        self.hb.doing(f"verifying run-{run} x={x}")
        true_run = ref.run_length_N(self.fam, N, cap=n + 8)
        if true_run < run:
            log("ALARM", f"claimed a({frontier+1}) = {N} has run {true_run} "
                         f"on N but {run} at filter {n}")
            raise SystemExit(2)
        run = true_run
        ok, legs, stop = verify(N, run, self.fam)
        if not ok:
            log("ALARM", f"claimed a({frontier+1}) = {N} failed the "
                         f"protocol: {legs}")
            raise SystemExit(2)
        settles = list(range(frontier + 1, run + 1))
        self.hb.doing(f"certifying run-{run} N={N}")
        certs, unproved = certify_run(N, run, self.fam)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        also = also_settles(self.fam, N, run, settles)
        ev = {"sequence": self.oeis, "forms": ref.FAMILIES[self.fam]["forms"],
              "sign": self.s,
              "N": int(N), "x": int(x), "filter_n": int(n), "L": int(ref.L(n)),
              "run": int(run), "settles": settles,
              "values": {str(i): int(N // i + self.s)
                         for i in range(1, run + 1)},
              "multipliers": {str(i): int(ref.L(run) // i)
                              for i in range(1, run + 1)},
              "x_at_run": int(N // ref.L(run)),
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
                              "swept_from_N": int(ref.term(n, self.x_start())),
                              "swept_to_N": int(N),
                              "filter": int(n),
                              "wheel": int(self.eng.W),
                              "sieve_depth": int(self.eng.q2),
                              "unit": int(self.eng.unit),
                              "monotone_floor": int(self.frontier_k())},
              "engine": self.key}
        for m in settles:
            self.found[str(m)] = int(N)
        path = evidence.record(
            ev, EVID, f"{self.oeis}_a{settles[0]}_{N}.json",
            ledger_path(self.fam), key="N",
            label="%s a(%s)" % (self.oeis, ",".join(map(str, settles))))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        stopline = (f"stopped by {stop['i']} not dividing N"
                    if stop["value"] is None else
                    f"stopped by N/{stop['i']} {self.s:+d} = "
                    f"{stop['value']:,} = {stop['factor']} * ...")
        lines = [
            f"{self.oeis} a({settles[0]}) = {N:,}" if len(settles) == 1 else
            f"{self.oeis} a({settles[0]})..a({settles[-1]}) = {N:,}",
            f"run {run}: (N {'+' if self.s > 0 else '-'} k)/k is prime for "
            f"every k = 1..{run}   (N = {ref.L(run):,} * {N // ref.L(run):,})",
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
        """After a find: rebuild the engine at the next open term AND START
        ITS LINE OVER.

        This is where the lcm ladders differ from every other project here.
        Elsewhere a filter change keeps the cursor, because the wheel and
        the unit do not depend on n and the k line is the same line.  Here
        the line ITSELF changes: the published term is N = L(n)*x and L(n+1)
        is a different modulus, so an x at the old filter and an x at the new
        one are not the same number.  The cursor is therefore RESET to the
        new filter's floor -- which is free, because that floor is the term
        just found (monotonicity) and everything below it is excluded by the
        find itself, not by a sweep.

        Nothing is re-swept and nothing is skipped: the old filter's coverage
        claim ended at the find, and the new filter's claim starts there.
        """
        old = self.eng
        self.eng = self._build_engine(self.filter_n())
        self.j = self.floor_period()
        self.u = 0
        self.boundary = self.j
        self.pending = []
        log("STAGE",
            f"filter follows the frontier: n = {old.n} -> {self.eng.n}, and "
            f"with it the whole line -- L({old.n}) = {ref.L(old.n):,} becomes "
            f"L({self.eng.n}) = {ref.L(self.eng.n):,}, the unit {old.unit} "
            f"becomes {self.eng.unit}, the wheel "
            f"({old.p1},{old.p2},{old.p3}) becomes "
            f"({self.eng.p1},{self.eng.p2},{self.eng.p3}), the depth "
            f"{old.q2} becomes {self.eng.q2} and the period {old.W:.4g} "
            f"becomes {self.eng.W:.4g}; the sweep restarts at x = "
            f"{self.x_start():,} (N = {ref.term(self.eng.n, self.x_start()):,}"
            f", the term just found -- monotonicity, so nothing is skipped) "
            f"and the ladder now aims at a({self.filter_n()})")
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({m})")
                                  for m in self.found)]
        # the crossing moves with the filter (L(n) grew), and may already be
        # behind the sweep
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

        The line is taken off the cursor the sweep yields, so a period
        shorter than the calibration window (8 launches at n = 18) is
        measured as exactly the line it is."""
        sync = self.eng.cp.cuda.Stream.null.synchronize
        nl = self.eng.launches_per_segment
        it = self.eng.sweep(self.j, self.segment_end(), u_from=self.u,
                            k_min=self.k_min())
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
                if (un == 0 or el >= CAL_MAX_S
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
            sprp_run(k, self.fam, self.eng.n, cap)
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
            f"sweeping the k line to {target:.4g}; {self.oeis} "
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
                     f" = m*k, k factored once, subproofs for factors past "
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
                                     _submit(self.pool, self.fam,
                                             self.eng.n, cap, surv)))
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
    return [((15, 14), "DISCOVERY"),      # beyond the frontier
            ((18, 14), "DISCOVERY"),      # a long run settles several at once
            ((14, 14), "NEAR"),           # one condition short of a(15)
            ((13, 14), "CENSUS"),         # below the frontier: counted only
            ((8, 14), "CENSUS"),          # the census floor itself
            ((7, 14), None),              # under the floor: not even counted
            ((0, 14), None)]


# The canaries: published terms a period-0 mini-hunt reaches in a second or
# two, at the filter each belongs to, in x space AND in that filter's own
# unit space (the stream that sweeps x' = x / unit must find the same first
# x).  n = 8 forces 6 and n = 9 forces 2 -- the sporadic forcing again, and
# a canary at each is the cheapest check that the unit really is per-filter.
_CANARIES = (("A078502", 8, 1), ("A078502", 8, 6), ("A078502", 9, 1),
             ("A078502", 9, 2),
             ("A074200", 8, 1), ("A074200", 8, 6), ("A074200", 9, 1),
             ("A074200", 9, 2))


def _canary_hunt():
    """The stream must organically rediscover known terms, in both families.

    Dedicated mini-hunts at the filters those terms belong to.  The
    production filter cannot rediscover them -- a(8) has run 8 and an
    n = 15 wheel is entitled to kill it -- so rediscovery is done at the
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
        want = ref.x_of(n, ref.KNOWN[fam][n])
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
                           f"expected a({n})/L({n}) = {want}")
        hits_all.append(f"{fam} a({n})" + (f" (unit {unit})" if unit > 1
                                           else ""))
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as FIRST occurrences at their own "
                  "filters, sweeping period 0 from the engine floor with the "
                  "prefix cleared by the oracle -- in x space and in each "
                  "filter's own unit space, both families")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on both families."""
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        N = ref.KNOWN[fam][top]
        ok, legs, stop = verify(N, top, fam)
        if not ok:
            return False, (f"PROTOCOL FAIL: genuine run-{top} at N={N} "
                           f"({fam}) rejected: {legs}")
        if stop["i"] != top + 1:
            return False, f"PROTOCOL FAIL: {fam}: the stopper is not rung {top+1}"
        if stop["value"] is not None:
            if stop["factor"] is None:
                return False, (f"PROTOCOL FAIL: {fam}: no factor witness for "
                               f"the composite stopper")
            if (stop["value"] % stop["factor"]) or \
                    stop["factor"] in (1, stop["value"]):
                return False, f"PROTOCOL FAIL: {fam}: the witness is not a factor"
        elif N % stop["i"] == 0:
            return False, (f"PROTOCOL FAIL: {fam}: the stopper was recorded as "
                           f"a divisibility stop but {stop['i']} divides N")
        bad, legs_b, _ = verify(N, top + 1, fam)
        if bad:
            return False, (f"PROTOCOL FAIL: fake run-{top+1} claim at N={N} "
                           f"({fam}) ACCEPTED ({legs_b})")
        prev = max(n for n in ref.KNOWN[fam] if ref.KNOWN[fam][n] < N)
        fake, _lc, _ = verify(ref.KNOWN[fam][prev], top, fam)
        if fake:
            return False, (f"PROTOCOL FAIL: {fam}: a({prev})'s N accepted as "
                           f"a run-{top}")
    # and the derived claims: each find settles its rider at EVERY index it
    # settles, shifted by one, and never the other family's rider
    N = ref.KNOWN["A078502"][14]
    also = also_settles("A078502", N, 14, [12, 13, 14])
    if [a["sequence"] for a in also] != ["A093554"] * 3 or \
            any(a["value"] != N - 1 for a in also) or \
            [a["n"] for a in also] != [12, 13, 14]:
        return False, f"PROTOCOL FAIL: A078502's derived claim came out {also}"
    Np = ref.KNOWN["A074200"][14]
    alsop = also_settles("A074200", Np, 14, [14])
    if [a["sequence"] for a in alsop] != ["A093553"] or \
            alsop[0]["value"] != Np + 1:
        return False, f"PROTOCOL FAIL: A074200's derived claim came out {alsop}"
    # and the published rider tables agree with what the identity claims
    for fam, shift, other in (("A078502", -1, "A093554"),
                              ("A074200", +1, "A093553")):
        for n, v in ref.KNOWN[fam].items():
            if ref.KNOWN_ALSO[other].get(n) != v + shift:
                return False, (f"PROTOCOL FAIL: {other}({n}) is not "
                               f"{fam}({n}) {shift:+d}")
    return True, ("protocol ok, both families: each frontier term accepted at "
                  "its true run with a witness for its stopper (a factor when "
                  "the stopping value is composite, the divisibility itself "
                  "when L(run+1) does not divide N), and a run one too long "
                  "and a mislabelled earlier term both rejected; the derived "
                  "claims (A093554 = A078502 - 1 and A093553 = A074200 + 1 at "
                  "every settled index) come out as the identities say and "
                  "agree with both published rider tables")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing."""
    raised = []
    eng = gpu.GpuEngine(12, "A074200", p1=13, p2=None, p3=None, q2=1024)
    ceil = cpu.k_ceil(12, "A074200")
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
        eng.sweep(0, 2, k_min=cpu.k_floor(1024, 12, "A074200"))
        return False, "CEILING FAIL: a clip AT the floor was accepted"
    except ValueError:
        raised.append("gpu k_min <= floor")
    c = cpu.CpuEngine(12, "A074200", q2=1024)
    try:
        c.survivors(10 ** 5, cpu.k_ceil(12, "A074200") + 10)
        return False, "CEILING FAIL: the CPU engine swept past k_ceil"
    except ValueError:
        raised.append("cpu k_ceil")
    # the two signs share ONE ceiling (lcml_search.k_ceil, v3): huntlib's
    # measured K_CEIL, above both crossings, and the engines enforce it on
    # a -1 family too -- and refuse it tight: the last whole period under
    # it sweeps (checked, not swept), the next raises
    if cpu.k_ceil(15, "A074200") != ceiling.K_CEIL or \
            cpu.k_ceil(15, "A078502") != ceiling.K_CEIL or \
            not cpu.k_proof(15, "A074200") < cpu.k_ceil(15, "A074200") or \
            not cpu.k_proof(15, "A078502") < cpu.k_ceil(15, "A078502"):
        return False, ("CEILING FAIL: the family ceilings are not the "
                       "one K_CEIL G10 pins")
    engm = gpu.GpuEngine(12, "A078502", p1=13, p2=None, p3=None, q2=1024)
    ceilm = cpu.k_ceil(12, "A078502")
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
        cpu.CpuEngine(12, "A078502", q2=1024).survivors(10 ** 5, ceilm + 10)
        return False, "CEILING FAIL: a -1 CPU engine swept past K_CEIL"
    except ValueError:
        raised.append("cpu k_ceil (-1)")
    try:
        c.survivors(cpu.k_floor(1024, 12, "A074200"), 10 ** 6)
        return False, "CEILING FAIL: the CPU engine swept at the floor"
    except ValueError:
        raised.append("cpu floor")
    # The floor is NEARLY ZERO at the campaign filters -- the smallest value
    # is (L/n)*x, so a sieve to q2 is valid from x = 3 at n = 15 -- which
    # makes the check above nearly vacuous on its own.  So it is also drilled
    # where the floor genuinely bites: at n = 2 the smallest multiplier is 1,
    # the value is x + s, and the floor is q2.
    lowf = cpu.k_floor(1024, 2, "A074200")
    if lowf < 1000:
        return False, (f"CEILING FAIL: the n = 2 floor is {lowf}, so the "
                       f"floor check is vacuous everywhere")
    try:
        cpu.CpuEngine(2, "A074200", q2=1024).survivors(lowf, lowf + 10 ** 5)
        return False, "CEILING FAIL: the CPU engine swept at a floor that bites"
    except ValueError:
        raised.append("cpu floor (n = 2, floor = %d)" % lowf)
    try:
        gpu.wheel(7, "A074200", 53)          # a flat wheel far past RES_MAX
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(15, "A074200", p1=31, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    try:
        gpu.GpuEngine(7, "A074200", p1=13, p2=37, p3=None, q2=4096)
        return False, "CEILING FAIL: an oversized second level was accepted"
    except ValueError:
        raised.append("gridDim.y")
    try:
        gpu.GpuEngine(gpu.NRES_MAX + 1, "A074200", p1=13, p2=None,
                      p3=None, q2=1024)
        return False, ("CEILING FAIL: a filter longer than the tail's "
                       "residue list was accepted")
    except ValueError:
        raised.append("nforms <= NRES_MAX")
    try:
        # 34 is forced at n = 16 and at NO other filter: the sporadic
        # forcing makes the neighbouring filter the easy mistake here.
        gpu.GpuEngine(15, "A074200", p1=13, p2=None, p3=None, q2=1024,
                      unit=34)
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


def _first_prime_rung(fam, N, n_max=24):
    """The first rung i <= n_max that divides N and whose value N/i + s is a
    probable prime past the deterministic bound, or None -- a drill at an
    arbitrary N has to take the value it is given."""
    s = ref.sign(fam)
    for i in range(1, n_max + 1):
        if N % i:
            continue
        v = N // i + s
        if v >= MR_VALID_BELOW and sprp_base2(v) and mr_is_prime(v):
            return i
    return None


def _certificate_drill():
    """A discovery past the proof crossing is PROVED, not just tested --
    on BOTH signs, and at the CEILING.

    THE ROUTE IS THE WHOLE POINT OF THIS PROJECT'S CEILING.  Value i is
    N/i + s, so (N/i + s) - s = N/i, and N = L(n)*x with L(n) n-smooth:
    ONE factorization of x factors every value's N -+ 1 at once.  Below the
    crossing every certificate takes the deterministic route.  Above it the
    structure does the work: BLS75 Theorem 1 on V - 1 (s = +1, A074200) or
    Theorem 15, the N+1 Lucas test, on V + 1 (s = -1, A078502), and each
    proof must re-verify from scratch and refuse a neighbouring value.

    Drilled on each family's frontier term (every value under the bound),
    on the first x past k_proof(n, F) whose top value is a probable prime
    (the crossing this campaign passes at x = 9.2e18 for n = 15 and
    2.7e17 for n = 17 -- BELOW the modelled median at n = 16 and 17, so
    this is the normal path here and not an edge case), and then AT K_CEIL
    on both signs: a worst-case x (the unit times a balanced semiprime,
    huntlib.ceiling.hard_k) and an x with a prime factor above the
    deterministic bound, whose certificate must carry a subproof that
    cannot be stripped.
    """
    parts = []
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        N = ref.KNOWN[fam][top]
        certs, unproved = certify_run(N, top, fam)
        if unproved or len(certs) != top:
            return False, (f"CERTIFICATE FAIL: {fam} a({top}) left "
                           f"{unproved} unproved ({len(certs)} certificates)")
        if any(c.get("proof") != "deterministic-mr" for c in certs.values()):
            return False, ("CERTIFICATE FAIL: a value under the bound took "
                           "the certificate route")
        parts.append(f"{fam} a({top})'s {top} values take the deterministic "
                     f"route and re-verify")
    # past the crossing, both signs, at the filters the campaigns cross it
    for fam, n in (("A074200", 15), ("A078502", 17)):
        want = "bls75-thm1" if ref.sign(fam) > 0 else "bls75-thm15"
        unit = cpu.forced_unit(n, fam)
        s_ = ref.sign(fam)
        m = -(-cpu.k_proof(n, fam) // unit)
        NN = None
        for _ in range(6000):
            cand = ref.term(n, unit * m)
            v = cand + s_
            if v >= MR_VALID_BELOW and sprp_base2(v) and mr_is_prime(v):
                NN = cand
                break
            m += 1
        if NN is None:
            return False, (f"CERTIFICATE FAIL: no x of {fam} past the "
                           f"crossing at n = {n} with a probable-prime top "
                           f"value in 6000 tries")
        certs, unproved = certify_run(NN, 1, fam, only=(1,))
        c = certs.get("1")
        if unproved or c is None or c.get("proof") != want:
            return False, (f"CERTIFICATE FAIL: {fam} N {s_:+d} at N = "
                           f"{NN:.4g} (past the bound) was not proved by "
                           f"{want}: {c and c.get('proof')}")
        if int(c["N"]) != NN + s_ or int(c["R"]) != 1:
            return False, (f"CERTIFICATE FAIL: the {want} proof is not about "
                           f"the value, or N was not factored completely")
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
        parts.append(f"{fam} at n = {n}: N {s_:+d} = {NN + s_:.4g} past the "
                     f"crossing is proved by {want} on N = L({n})*x factored "
                     f"completely ({len(c['factors'])} primes), re-verifies, "
                     f"refused for N + 2 and as a bare MR claim")
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
            NN, i = None, None
            for sd in range(1, 40):
                x = maker(sd)
                if x >= cpu.k_ceil(n, fam):
                    return False, (f"CERTIFICATE FAIL: the {label} x is past "
                                   f"the ceiling")
                cand = ref.term(n, x)
                i = _first_prime_rung(fam, cand)
                if i is not None:
                    NN = cand
                    break
            if NN is None:
                return False, (f"CERTIFICATE FAIL: no {label} x of {fam} near "
                               f"K_CEIL with a probable-prime value in 39 tries")
            certs, unproved = certify_run(NN, i, fam, only=(i,))
            c = certs.get(str(i))
            if unproved or c is None or c.get("proof") != want:
                return False, (f"CERTIFICATE FAIL ({label}, {fam}): rung {i} "
                               f"at N = {NN:.4g} not proved by {want}: "
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
                parts.append(f"{fam} at x = {NN // ref.L(n):.3g} (a "
                             f"{len(str(big[0]))}-digit prime factor above "
                             f"the bound): {want} with a subproof of it, "
                             f"which cannot be stripped")
            else:
                parts.append(f"{fam} at x = {NN // ref.L(n):.3g} (the unit x "
                             f"two "
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
            # The spans are a fiftieth of what the same drill used in the
            # linear ladders, for the reason everything here is: the wheel is
            # ~2,400x weaker, so a window a fiftieth as wide holds more
            # survivors than theirs did.  These three hold 1e5-1e6 between
            # them; the version inherited from that project held 7.1e7 and
            # took three minutes.
            ("one-level", "A078502", dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 1200, 457),
            ("two-level", "A074200", dict(p1=19, p2=31, p3=None, q2=8192,
                                          unit=2, pb=32),
             10 ** 15, 3, 1),
            ("three-level", "A078502", dict(p1=13, p2=17, p3=19, q2=128,
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
    # -- the campaigns' engine -- where a period is `unit` times an x' period
    # and the seam must still close.
    # pb = 32 so a SEGMENT is 32 periods rather than 192: the seam is what
    # is under test, and a whole production segment of this wheel is 1.4e11
    # candidates.  G15 pins the stream's independence from pb.
    for eng in (gpu.GpuEngine(15, "A078502", p1=11, p2=17, p3=23, q2=128,
                              nu=4, pb=32),
                gpu.GpuEngine(16, "A074200", p1=11, p2=19, p3=29, q2=128,
                              nu=8, unit=34, pb=32)):
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
    # 6,000 periods of the (13],(23] wheel at n = 10 is 1.3e12 of line,
    # which at that density and sieve depth is a few thousand survivors
    eng = gpu.GpuEngine(10, "A078502", p1=13, p2=23, p3=None, q2=4096)
    j0 = eng.j_of(10 ** 13)
    surv = eng.survivors_j(j0, j0 + 150)
    if len(surv) < 3 * CHUNK:
        return False, (f"CLASSIFY FAIL: only {len(surv)} survivors -- the "
                       f"drill cannot span several chunks")
    two = [sprp_run(k, "A078502", 10, 10) for k in surv]
    full = []
    for k in surv:
        r = 0
        while r < 10 and mr_is_prime(ref.rung(10, r + 1) * k - 1):
            r += 1
        full.append(r)
    if two != full:
        i = next(i for i in range(len(surv)) if two[i] != full[i])
        return False, (f"CLASSIFY FAIL: two-pass sprp gave run {two[i]} and "
                       f"the all-bases chain {full[i]} at k = {surv[i]}")
    with _pool_factory(2) as pool:
        parts = _submit(pool, "A078502", 10, 10, surv)
        got = [r for ks, f in parts for r in f.result()]
    if got != full:
        return False, "CLASSIFY FAIL: the pool's chunked result differs"
    # and the run is CAPPED at the filter: a filter-n sweep sieved for n
    # conditions and may not speak about the n+1-th, which needs L(n+1) | N
    # as well.  A classifier that ignored the cap would report runs the
    # sweep never sieved for -- the one way a rider could be claimed
    # without the divisibility that makes it one.
    for fam in ref.FAMILIES:
        x = ref.x_of(9, ref.KNOWN[fam][9])
        if sprp_run(x, fam, 9, 9) != 9 or sprp_run(x, fam, 9, 30) != 9:
            return False, (f"CLASSIFY FAIL: {fam} a(9)'s run at filter 9 is "
                           f"not 9, or the cap did not bind")
        # the same TERM at a lower filter is a different x -- N = L(n)*x --
        # so it is converted, not reused; a(9) satisfies filter 7 as well,
        # and the cap must stop the run there
        x7 = ref.x_of(7, ref.KNOWN[fam][9])
        if sprp_run(x7, fam, 7, 30) != 7:
            return False, (f"CLASSIFY FAIL: {fam} a(9) classified at filter 7 "
                           f"did not stop at 7")
    return True, (f"classification ok: two-pass sprp == all-bases chain on "
                  f"{len(surv)} real survivors (max run {max(full)}), "
                  f"{len(parts)} pool chunks reassemble to the serial answer, "
                  f"and the run is capped at the filter it was sieved for on "
                  f"both families")


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
    """A FIND MOVES THE WHOLE LINE, and the cursor must move with it.

    This is the drill for the thing this project has that no other in the
    repo does.  Elsewhere a filter change keeps the cursor: the wheel, the
    unit and the k line do not depend on n, so a(n) and a(n+1) are hunted on
    the same line and the sweep simply carries on.  Here the published term
    is N = L(n)*x, and L(n+1) is a different modulus -- so the x cursor at
    the old filter means nothing at the new one, and EVERY constant derived
    from the filter (the forced unit, the three wheel levels, the sieve
    depth, the period, the window width) changes with it, in both
    directions.

    What is asserted, on a scratch checkpoint:
      * promoting rebuilds the engine at the new filter and the plan really
        does change (unit 2 -> 34 and period 6.5e15 -> 1.8e16 from n = 15 to
        16, and back to unit 2 at 17);
      * the cursor RESETS to the new filter's floor, which is the term just
        found -- so nothing is skipped (monotonicity) and nothing is
        re-swept;
      * the ladder retires the rungs of the term that was found;
      * the checkpoint round-trips at the new filter and reloads to the same
        place;
      * and a cursor stored at ONE filter is REFUSED by a campaign whose
        frontier puts it at another.  That last one is this project's
        version of the failure that cost the repo two campaign starts: the
        stored number is fine, its UNITS are not, and only an assertion
        catches it (OPTIMIZATION.md 2.9).
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="lcml-promote-")
    path = str(pathlib.Path(tmp) / "c.json")
    rows = []
    for fam in ref.FAMILIES:
        pol = _POLICIES[fam].at(path)
        c = Campaign(_args_for(fam), ckpt=path, cursor=pol)
        n0 = c.filter_n()
        before = (c.eng.n, c.eng.unit, c.eng.W, c.eng.q2,
                  (c.eng.p1, c.eng.p2, c.eng.p3))
        if c.j != c.floor_period() or c.x_start() <= 0:
            return False, (f"PROMOTION FAIL: {fam} fresh campaign did not "
                           f"start at its floor period")
        # a fabricated find at the filter's floor, recorded the way a real
        # one is -- the term itself is not checked here (the protocol drill
        # does that); what is under test is what the campaign does NEXT
        found_N = ref.term(n0, c.x_start() + 10)
        c.found[str(n0)] = int(found_N)
        c.follow_frontier()
        after = (c.eng.n, c.eng.unit, c.eng.W, c.eng.q2,
                 (c.eng.p1, c.eng.p2, c.eng.p3))
        if after[0] != n0 + 1:
            return False, f"PROMOTION FAIL: {fam} did not move to n = {n0+1}"
        if after[1:] == before[1:]:
            return False, (f"PROMOTION FAIL: {fam} kept the whole plan across "
                           f"n = {n0} -> {n0+1}: {before} -- at these filters "
                           f"the unit and the period must both move")
        if c.u != 0 or c.j != c.floor_period() or c.boundary != c.j:
            return False, (f"PROMOTION FAIL: {fam} kept a cursor across the "
                           f"promotion (j = {c.j}, floor period "
                           f"{c.floor_period()}, u = {c.u})")
        # the new floor is the term just found, so nothing below it is swept
        # and nothing above it is skipped
        want = -(-int(found_N) // ref.L(n0 + 1))
        if c.x_start() != max(want, cpu.k_floor(c.eng.q2, n0 + 1, fam) + 1):
            return False, (f"PROMOTION FAIL: {fam}'s new floor is "
                           f"{c.x_start()}, not the found term "
                           f"{found_N} re-denominated ({want})")
        if any(p.startswith(f"a({n0})") for p in c.passed):
            return False, f"PROMOTION FAIL: {fam} kept a retired rung"
        # round trip at the new filter
        if not c.save():
            return False, f"PROMOTION FAIL: {fam}'s post-promotion save did not land"
        c2 = Campaign(_args_for(fam), ckpt=path, cursor=_POLICIES[fam].at(path))
        if (c2.filter_n(), c2.j, c2.u) != (n0 + 1, c.j, 0):
            return False, (f"PROMOTION FAIL: {fam} reloaded at "
                           f"({c2.filter_n()}, {c2.j}, {c2.u}), not "
                           f"({n0+1}, {c.j}, 0)")
        # ... and a cursor whose stored filter disagrees with the frontier is
        # REFUSED rather than read in the wrong units
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
        rows.append(f"{fam} n = {n0} -> {n0+1}: unit {before[1]} -> "
                    f"{after[1]}, wheel {before[4]} -> {after[4]}, q2 "
                    f"{before[3]} -> {after[3]}, period {before[2]:.3g} -> "
                    f"{after[2]:.3g}")
        os.remove(path)
        for ext in (".bak",):
            if os.path.exists(path + ext):
                os.remove(path + ext)
    return True, ("promotion ok: " + "; ".join(rows) + " -- the cursor resets "
                  "to the new filter's floor (the term just found, so nothing "
                  "is skipped and nothing re-swept), the retired rungs go, the "
                  "checkpoint round-trips at the new filter, and a cursor "
                  "stored at the wrong filter is REFUSED rather than read in "
                  "the wrong units")


def _other_families_cursor_drill(fam):
    """Every OTHER family's policy, put in front of every key it declares."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="lcml-cursor-")
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
    # the rider spellings open the right campaign
    if ref.family("A093554") != "A078502" or ref.family("A093553") != "A074200":
        return False, "FAMILY FAIL: the rider aliases do not resolve"
    # and the PER-FILTER plan is admissible at every filter it is used at,
    # and is NOT the same at neighbouring ones -- the sporadic forcing means
    # a plan carried one filter forward is a coverage claim never made, and
    # this is the cheapest place to assert it
    units = {}
    for f in fams:
        for n in range(open_n(f), open_n(f) + 6):
            unit, p1, p2, p3, q2 = plan_for(f, n)
            cpu.assert_unit(n, f, unit)      # raises if not forced there
            units[n] = unit
    if [units[n] for n in range(15, 21)] != [2, 34, 2, 114, 6, 30]:
        return False, (f"FAMILY FAIL: the per-filter units came out "
                       f"{[units[n] for n in range(15, 21)]}, not "
                       f"[2, 34, 2, 114, 6, 30]")
    # each of these contains a prime that is NOT forced at that filter --
    # 17 is forced only at n = 16, 3 only from n = 18 -- so each must RAISE
    for n, wrong in ((15, 34), (17, 34), (18, 34), (16, 6), (17, 114)):
        try:
            cpu.assert_unit(n, "A078502", wrong)
            return False, (f"FAMILY FAIL: unit {wrong} accepted at n = {n}, "
                           f"where one of its primes is not forced")
        except ValueError:
            pass
    return True, ("families stay apart: two distinct config keys, checkpoint "
                  "files and ledgers, no policy reads the other's cursor, the "
                  "rider aliases resolve, and the PER-FILTER plan is "
                  "admissible at every filter n = 15..20 with the units "
                  "coming out 2, 34, 2, 114, 6, 30 -- not monotone, so a "
                  "carried-forward unit is refused")


def _campaign_wiring_drill(fam="A078502"):
    """Build a campaign and exercise everything the loop touches, without
    sweeping a whole period: construction from nothing at period 0, the
    status line, census and NEAR/CENSUS classification, the cached rung
    ladder, the drain of a fake in-flight launch, the pool sized from a
    real measurement, back-pressure, a find moving the filter, a save/load
    round trip, and the interrupt snapshot."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="lcml-drill-")
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
        # A fresh campaign here starts at the MONOTONICITY FLOOR of its own
        # filter, not at a constant: the previous term re-denominated into
        # this filter's x, which is free and is most of the line.
        floor = c.x_start()
        if (c.j, c.u, c.k_min()) != (c.floor_period(), 0, floor):
            return False, (f"WIRING FAIL: a fresh campaign starts at "
                           f"(j, u) = ({c.j}, {c.u}), clip {c.k_min()} -- "
                           f"expected period {c.floor_period()} clipped at "
                           f"{floor}")
        if floor != -(-ref.KNOWN[fam][n0 - 1] // ref.L(n0)):
            return False, (f"WIRING FAIL: the floor {floor} is not a({n0-1}) "
                           f"re-denominated into filter {n0}")
        unit, p1, p2, p3, q2 = plan_for(fam, n0)
        if (c.eng.n, c.eng.fam, c.eng.unit, c.eng.q2) != (n0, fam, unit, q2) \
                or (c.eng.p1, c.eng.p2, c.eng.p3) != (p1, p2, p3):
            return False, ("WIRING FAIL: the engine is not the PLANNED one "
                           "for the campaign filter")
        line = c.status_line()
        for want in ("swept to", fam, "census", "periods [0,"):
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
        c.found[str(n0)] = int(ref.term(n0, floor + 4))   # a find, unverified
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
        # the PERIOD changes with the filter here, which is exactly why the
        # cursor resets rather than carrying over
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
                  f"at the monotonicity floor of its own filter (x = "
                  f"{floor:,}, a({n0-1}) re-denominated) with the PLANNED "
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


def selftest(fam="A078502"):
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
    ap.add_argument("--family", default="A078502",
                    help="which sequence to hunt: " +
                         ", ".join(f"{f} ({ref.FAMILIES[f]['forms']})"
                                   for f in ref.FAMILIES) +
                         "; A093554 and A093553 are aliases of A078502 "
                         "and A074200, being those sequences shifted by one "
                         "(default A078502)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this depth on the k line (default: the "
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
