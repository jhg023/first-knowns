"""The campaign for the cyclotomic ladders -- A070737: the smallest number x such that the first n cyclotomic polynomials evaluated at x are primes; A072942: the least x such that the cyclotomic polynomial values Phi(d,x) are prime for all d dividing n.

    python launch.py                       the hunt: A070737, indefinite, resumable
    python launch.py --family A072942      A072942: its open indices, cheapest first
    python launch.py --family A072942 --index 60    one open index of A072942
    python launch.py --status              where the cursor is; reads, never writes
    python launch.py --selftest            the full gate battery; must end ALL GREEN

TWO FAMILIES, TWO SHAPES OF LINE, ONE ENGINE, ONE CAMPAIGN AT A TIME.
`--family` names the entry (cyclotomic_reference.FAMILIES).

  * A070737 is a LADDER: every condition of index n is one of index n + 1,
    so a(n+1) >= a(n), the sweep for a(n) starts AT a(n - 1) inclusive (a
    term whose run passes its index is the next term too: a(3) = a(4) = 6),
    and a find PROMOTES the filter and CARRIES the line -- the
    classification reads runs to the filter plus RUN_AHEAD, so everything
    the old filter swept past a find was already classified against the
    next filter's conditions; the new filter resumes at the old segment's
    end, re-denominated by floor into its own period with the clip at the
    old boundary (_promotion_drill).  One checkpoint, one ledger.  Every
    find at n >= 5 also settles A233512 (Noe's strictly increasing
    restatement) at the same index (`also_settles`).
  * A072942's indices are SEPARATE PROBLEMS: a(n) is the least x whose
    Phi(d,x) are prime for every divisor d of n, and nothing about a(n)
    bears on a(n + 1).  Each open index -- 48, 60, 66, 72, 78, 80, 84, 88,
    90, 96, the question marks of Don Reble's a-file -- is its own line
    from x = 3, with its own checkpoint and config key; a find CLOSES the
    index (there is nothing more to sweep for) and the campaign moves to
    the next open index in TARGETS, the model's order of expected clock.
    With no `--index` the campaign runs them all, cheapest first, and stops
    when none is open.

EVERY FORM IS KNOWN AT EVERY INDEX, so the campaign can be planned, priced
and benchmarked at every filter it will run, in advance (CLAUDE.md 5g):
`plan_for` is the one place a configuration is derived, score.py has a
shape at A070737's opening and at the day-long filters of both families,
and G18 compiles every opening.  The openings (5g's test plan): A070737
n = 11 fresh and resumed and the filters it promotes itself into, n = 12
and 13; A072942 at each of its ten open indices.

THE DEVICE FERMAT STAGE (cyclotomic_gpu; power-ladders' own, kept).  A
prime kills about one residue per form on average, so millions of sieve
survivors a second leave the sieve; the device Fermat-tests their leading
forms -- Phi_1(x), Phi_2(x), ... in run order, the smallest degrees first,
CENSUS_FLOOR of them -- and only the values that pass reach the host, a few
thousand a second.  A failed Fermat test is a proof of compositeness, so
nothing with a run at the census floor or above is dropped; the host
re-reads every run.

THE EXCEPTION ZONE IS COVERED AT EVERY FILTER START.  A kill by a sieve
prime needs the value to exceed it, so the device starts above the engine
floor x = q2 + 1 (Phi_1(x) = x - 1 is the smallest value); the integers
between the sweep's floor and the engine's are classified one at a time on
the host (cyclotomic_search.prefix_hits).  A070737's frontier is far above
it; every A072942 index opens AT x = 3 and covers the zone first -- and
most of its small terms live there (a(47) = 62).

THE RUN of a value: the number of leading forms of the filter (Phi_1,
Phi_2, ... on A070737; Phi_d over the divisors of n, ascending, on A072942)
whose value is prime.  On A070737 a run of r >= the filter n is a DISCOVERY
settling a(n)..a(r) at once; r = n - 1 is NEAR; CENSUS_FLOOR <= r < n - 1
is counted only.  On A072942 a run equal to the number of divisors is a
DISCOVERY of a(n); one short is NEAR; CENSUS_FLOOR <= r below that is
counted.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine ceiling, huntlib's K_CEIL = 1e40 on the term, both families.
The proof crossing -- where classification stops being a proof -- is where
the largest value of the filter passes 3.317e24 (x = 258 at n = 11 of
A070737): every campaign starts past it, and it is a [MILESTONE], never a
stop.  Every value Phi_k(x) has Phi_k(x) - 1 = x^a * (a product of OTHER
cyclotomic values at x, most of them earlier values of the same run) *
(a leftover polynomial of degree 0, 3, 5 or 6), so a discovery's values
are each proved by BLS75 Theorem 1 or 5 on N - 1, the run's own earlier
values standing in F with their own certificates as subproofs (certify_run;
_certificate_drill at the ceiling).

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
candidates of a segment come out in wheel order, so nothing in a segment is
known to be the LEAST until it closes: 'swept to' is the term below which
every value has been tested; (period, launch) is the work cursor inside it.

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
from sympy import Poly, Symbol, cyclotomic_poly, factor_list, isprime  # noqa: E402

import cyclotomic_gpu as gpu                                    # noqa: E402
import cyclotomic_model as model                                # noqa: E402
import cyclotomic_reference as ref                              # noqa: E402
import cyclotomic_search as cpu                                 # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")


def TERM(fam):
    """The letter the OEIS name gives the term: x on both entries (rule 5i);
    every surface a person reads carries the integer under it."""
    return ref.letter(fam)


def per_index(fam):
    """True for a family whose every index is its own line (A072942)."""
    return ref.per_index(fam)


PLAN_VERSION = "p3"               # bump when plan_for's answer changes
#   p1 (2026-10-23): power-ladders' planner p1 taken whole -- the wheel and
#   the window chosen together by expected clock to a confirmed find
#   (cyclotomic_gpu.plan) over every greedy wheel subset the kernel admits
#   -- with the sieve depth a DEVICE decision (cyclotomic_gpu.PRP_Q2: the
#   Fermat stage makes the host's load independent of it) and the floor it
#   prices from the index's own (a(n-1) on A070737, or the model's median
#   of it; x = 3 on A072942).  NOT yet re-measured on this project's filters
#   (OPTIMIZATION_LOG.md round 0).
#   p2 (2026-10-23, round 1): the same planner with its constants measured
#   on THIS project's day-long filters -- the width curve (CREL_WIDTH: 160
#   periods 1.06 over 128, flat past it), the window depth (BIT_SURV 0.0065:
#   64 primes at A070737 n = 13, 87 at A072942 n = 60) and the window-table
#   budget set so the pairs layout fits everywhere (WINDOW_TABLE_BYTES 12 KB
#   of the halved pattern, PAT_BYTES_MAX 24 KB).  A070737 n = 12 and 13 move
#   to 160 periods; the A072942 indices keep 256.  No campaign has run on
#   p1, so there is no cursor to adopt.
#   p3 (2026-10-24, round 2): the MEASURED wheels of A072942 n = 72, 84 and
#   96 (cyclotomic_gpu.MEASURED_WHEELS -- a strong prime above the
#   planner's 89 in place of a weak small one: 1.04-1.10x paired at x = 3
#   and at the median, the coverage segment at 84 and 96 five times
#   shorter) and of n = 60 (1.07-1.09x, the segment half as long), every
#   other filter planned exactly as p2 did.  A p2 cursor at a filter whose
#   wheel did not move covers the identical line and is ACCEPTED (`policy`);
#   at a moved index it is ADOPTED (Campaign.adopt_cursor: the swept
#   boundary re-denominated with flooring, the work cursor dropped) -- the
#   live n = 60 cursor, one segment closed under p2, is the case that
#   wrote it (the owner's word, 2026-10-24); no cursor existed at 72, 84
#   or 96.
PREVIOUS_PLANS = ("p2",)


@functools.lru_cache(maxsize=None)
def plan_for(fam, n):
    """(unit, p1, p2, p3, q2, pb) for filter n of family F -- the
    configuration the campaign runs there.  Pure and cached: a function of
    (family, n) alone, so a resumed campaign derives the identical plan and
    the launcher still asserts W and the segment on load (OPTIMIZATION.md
    2.9).  Cached because `x_start` and `state` call it every launch (2.14's
    trap)."""
    fam = ref.family(fam)
    unit = cpu.forced_unit(n, fam)
    p1, p2, p3, q2, pb = gpu.campaign_plan(n, fam, unit)
    return unit, p1, p2, p3, q2, pb


def x_floor(fam, n, frontier_x):
    """Where the sweep for a(n) starts: on A070737 the frontier term ITSELF
    (the ladder nests, and the frontier term is a(n) too when its run
    reaches n -- a(3) is a(4)); on A072942 x = 3, every index's own start."""
    fam = ref.family(fam)
    if per_index(fam):
        return ref.X_MIN
    return max(int(frontier_x), ref.X_MIN)


def open_n(fam):
    """The filter a FRESH campaign of this family opens at: A070737's
    frontier + 1; A072942's first open index in TARGETS."""
    fam = ref.family(fam)
    if per_index(fam):
        return next_target(fam, set())
    return max(ref.KNOWN[fam]) + 1


def next_target(fam, closed):
    """The first index of TARGETS that is open -- not published, not in
    FOUND, not in `closed` (the indices this run has settled) -- or None."""
    fam = ref.family(fam)
    for n in ref.TARGETS:
        if ref.term(fam, n, missing=None) is None and n not in closed:
            return n
    return None


# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a segment.
CKPT_LAUNCHES = 32
# Runs shorter than this are not even counted -- and the device Fermat
# stage tests exactly this many leading forms, so nothing at the floor or
# above is ever dropped before the host reads it.
CENSUS_FLOOR = 6
# How far past the filter the classification reads a run on A070737: a find
# of run r settles a(n)..a(r), and the line a filter swept is carried to the
# next filter only because every value on it was read this far past n.  A
# run that reaches the cap is re-read with no cap at verification.  On
# A072942 the divisor list is the whole run.
RUN_AHEAD = 6
# WHAT A PLAN MAY WASTE: a plan whose expected sweep to a confirmed find
# exceeds the unavoidable one by more than this factor is a decision for a
# human (_families_stay_apart).
PLAN_WASTE_MAX = 1.5

ENGINE_VERSION = "v2"
#   v1 (2026-10-23): power-ladders' engine v1 (round 7) -- polynomial-runs'
#   window sieve with the device Fermat stage -- with the kill sets the
#   elements of each order the forms ask for, the Fermat stage's values
#   formed by Horner from the cyclotomic coefficients, and no semiprime
#   wheel.  Every constant inherited, none re-swept here yet.
#   v2 (2026-10-23, OPTIMIZATION_LOG.md round 1): the window pattern holds
#   ONE period (WINDOW_HALF: the position reduced by one unsigned min), so
#   the pairs table, the packed x0/ne and the per-launch offset table fit at
#   every campaign filter (96 registers and 4 blocks a SM at A070737 n = 13
#   where v1 ran the plain aligned read at 168 and 3); the Fermat stage
#   tests its forms by degree (PRP_BY_DEGREE); the last tail round is
#   generated (TAIL_LITERAL_LAST); the constants re-swept here (BIT_SURV,
#   the width curve, the table budgets, WINDOW_QUAD_ALL off).  The same
#   stream as v1 on every shape (G9, G14, G21; every A/B arm identical):
#   1.31x at A070737 n = 13 and A072942 n = 60, 1.9-2.0x at n = 90 and 96.
#   No campaign ran on v1, so nothing is adopted.
PREVIOUS_ENGINES = ()
WORKERS_DEFAULT = 2
POOL_MARGIN = 2.0
CAL_MIN_SURVIVORS = 300
CAL_MIN_S = 1.0
CAL_MAX_S = 4.0
CAL_SEGMENTS = 256
CAL_SAMPLE = 600
BACKLOG_LAUNCHES = 64
CKPT_MIN_S = 2.0
CKPT_COST_FRACTION = 0.02
PERIOD_LOG_S = 60.0
WORKER_RAMP_S = _pool.RAMP_S
CHUNK = 64                        # survivors per pool task


def config_key(fam, index=None, engine=None, plan=None):
    fam = ref.family(fam)
    return (f"{fam.lower()}" + (f"-n{int(index)}" if index is not None else "")
            + f"-{engine or ENGINE_VERSION}-{plan or PLAN_VERSION}"
            f"-seg{CKPT_LAUNCHES}"
            f"-pbd{gpu.PB_DEFAULT}"
            f"-cpl{gpu.CAND_PER_LAUNCH4.bit_length() - 1}"
            f"w{gpu.CAND_PER_LAUNCH_WIDE.bit_length() - 1}"
            f"-f{CENSUS_FLOOR}")


def ckpt_path(fam, index=None):
    fam = ref.family(fam)
    tag = fam.lower() + (f"_n{int(index)}" if index is not None else "")
    return str(HERE / f"campaign_checkpoint_{tag}.json")


def ledger_path(fam):
    return str(HERE / "evidence" / f"{ref.family(fam).lower()}_discoveries.json")


# EVERY reader of a checkpoint goes through one of these objects and none
# of them takes a key list of its own (CONVENTIONS.md "Reading an existing
# cursor").  A070737 has one; A072942 one per index.
_POLICIES = {}


def plan_moved(fam, index=None):
    """True where the live plan's wheel differs from every PREVIOUS_PLANS'
    at this family and index: the measured per-filter wheels.  A cursor
    written under an older plan there counts periods of a different W, so
    it is ADOPTED (Campaign.__init__: only the swept boundary carries over,
    re-denominated with flooring), never accepted."""
    return (ref.family(fam), index) in gpu.MEASURED_WHEELS


def policy(fam, index=None):
    fam = ref.family(fam)
    index = int(index) if index is not None else None
    key = (fam, index)
    if key not in _POLICIES:
        # an older ENGINE gated to the identical stream, or an older PLAN
        # whose wheel at this filter is the live one: the same line
        same = [config_key(fam, index, engine=e) for e in PREVIOUS_ENGINES]
        older = [config_key(fam, index, plan=p) for p in PREVIOUS_PLANS]
        moved = plan_moved(fam, index)
        _POLICIES[key] = checkpoint.CursorPolicy(
            ckpt_path(fam, index), config_key(fam, index),
            accept=tuple(same + ([] if moved else older)),
            adopt=tuple(older if moved else []))
    return _POLICIES[key]


# ------------------------------- the taxonomy -------------------------------

def event_kind(run, frontier):
    """DISCOVERY / NEAR / CENSUS / None -- the repo-wide rule, this
    project's mathematics.  `frontier` is the run below a discovery: the
    largest n already settled on A070737 (a run past it settles a(n) and
    every index up to the run); the number of divisors less one on an
    A072942 index (a run of every divisor settles a(n))."""
    run, frontier = int(run), int(frontier)
    if run > frontier:
        return "DISCOVERY"
    if run == frontier:
        return "NEAR"
    if run >= CENSUS_FLOOR:
        return "CENSUS"
    return None


def read_index(fam, n):
    """The index whose forms the classification reads at filter n: n +
    RUN_AHEAD on the ladder (to see past the filter), n itself on A072942."""
    fam = ref.family(fam)
    return int(n) if per_index(fam) else int(n) + RUN_AHEAD


def stopper_of(fam, x, run, n):
    """The value at the form after the run and why it stops the run, or None
    when the run is the whole form list (an A072942 solution)."""
    fam = ref.family(fam)
    ks = ref.forms(fam, read_index(fam, n) if not per_index(fam) else n)
    if run >= len(ks):
        if per_index(fam):
            return None
        ks = ref.forms(fam, int(run) + 1)
    k = ks[int(run)]
    v = ref.value(k, int(x))
    return {"k": int(k), "value": int(v),
            "why": "composite" if v >= 4 else "not prime"}


def verify(x, run, fam, n, witness=True):
    """The three independent confirmations plus the bounding witness.

    1. huntlib's Miller-Rabin over every value of the run, a strong
       probable-prime chain past the proof crossing -- every value of a
       DISCOVERY is then PROVED by certificate;
    2. sympy's BPSW, an independent implementation, which must agree on the
       run LENGTH, not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense line and uses no wheel at all, must
       agree that x survives a sieve at a DIFFERENT depth from the
       campaign's, at the filter the run reaches.

    plus a factor witness for the composite that STOPS the run, which is
    what bounds the claim to exactly `run` (an A072942 solution has no
    stopper: every divisor's value is prime).  witness=False is the [NEAR]
    path: verified, not evidenced, no factoring.
    """
    fam = ref.family(fam)
    x, run, n = int(x), int(run), int(n)
    rn = n if per_index(fam) else max(run, 1)
    ks = ref.forms(fam, rn)[:run]
    vals = [ref.value(k, x) for k in ks]
    # the re-sieve is only a proof where every value exceeds the depth
    q2 = min(4096, min(vals) - 1) if vals else 1
    legs = {"mr_chain": all(mr_is_prime(v) for v in vals),
            "sympy_bpsw": ref.run_length(fam, x, rn) == run,
            "resieve_other_wheel": (q2 < 2 or
                                    cpu.CpuEngine(rn, fam, q2=q2).survives(x))}
    stop = stopper_of(fam, x, run, n)
    if stop is None:
        legs["stopper_composite"] = True        # nothing to stop: a solution
    else:
        legs["stopper_composite"] = (stop["why"] == "not prime"
                                     or not mr_is_prime(stop["value"]))
    ok = all(legs.values())
    wit = None
    if stop is not None:
        if witness and stop["why"] == "composite" and legs["stopper_composite"]:
            wit = stopper_witness(stop["value"])
        stop = dict(stop, factor=wit)
    return ok, legs, stop


WITNESS_FULL_BELOW = 10 ** 30


def stopper_witness(stop):
    """A nontrivial prime factor of the composite stopper, or None if the
    bounded effort (trial division, rho, ECM curves) found none -- in which
    case the failed Miller-Rabin base is the witness, and the evidence says
    so."""
    fac, _R = certificate.factor_partial(int(stop), ecm_curves=40)
    if fac:
        return int(min(fac))
    if stop < WITNESS_FULL_BELOW:
        w = factor_witness(int(stop))
        return int(w) if w and w > 1 else None
    return None


# THE CERTIFICATE ROUTE.  Phi_k(x) - 1 factors over the integers as x^a
# times cyclotomic polynomials of smaller index at x times a leftover of
# degree 0, 3, 5 or 6 (`minus_one_shape`): for a prime k it is x * prod
# Phi_d(x) over the divisors d > 1 of k - 1 exactly, and for every k to 14,
# 16 to 20, 24, 40, 48, 72 and 96 the leftover is 1.  So N - 1 is factored
# by one factorization of x plus the VALUES Phi_d(x) -- which, when d is a
# form of the same run, are its own proved primes.  BLS75 Theorem 1 where
# the factored part passes sqrt(N), Theorem 5 where it passes the cube root
# (Phi_15, Phi_30, Phi_60, Phi_80, Phi_84, Phi_90); the leftover's value and
# any Phi_d(x) outside the run go to huntlib's bounded factor_partial, and a
# value whose F stays short is left UNPROVED in the evidence (A072942's
# n = 66, 78 and 88 need a 65-70-digit cofactor factored for Phi_11, Phi_13
# and Phi_44: the find then stands on the three legs, and the evidence says
# which values to certify by hand).  The structureless search
# (certificate.prove on N alone) is the fallback, never the route.
_X = Symbol("x")
CERT_RETRY_CURVES = 200
CERT_RETRY_SPLITS = 16


@functools.lru_cache(maxsize=None)
def minus_one_shape(k):
    """[(kind, j, e)]: the factorization of Phi_k(X) - 1 over Z into
    ("x", 1, a) for X^a, ("phi", d, e) for Phi_d(X)^e and ("poly",
    coefficients, 1) for a non-cyclotomic factor, by sympy's factor_list
    (checked by multiplying back)."""
    k = int(k)
    poly = cyclotomic_poly(k, _X) - 1
    const, parts = factor_list(poly)
    out = []
    for f, e in parts:
        pf = Poly(f, _X)
        if pf == Poly(_X, _X):
            out.append(("x", 1, int(e)))
            continue
        found = None
        for j in range(1, 4 * k + 2):
            if Poly(cyclotomic_poly(j, _X), _X) == pf:
                found = j
                break
        if found is not None:
            out.append(("phi", int(found), int(e)))
        else:
            out.append(("poly", tuple(int(c) for c in reversed(pf.all_coeffs())),
                        int(e)))
    if int(const) != 1 and k > 1:
        out.append(("const", int(const), 1))
    return tuple(out)


def _poly_value(coeffs, x):
    v = 0
    for c in reversed(coeffs):
        v = v * x + c
    return v


def _verified(proof):
    return proof is not None and certificate.verify(proof)[0]


def certify_value(N, fac, subproofs):
    """A RE-VERIFIED primality certificate for N from the factorization
    `fac` of (part of) N - 1 -- {p: e}, every p a prime under the bound or
    one with its proof in `subproofs` -- or None.  BLS75 Theorem 1 where F
    passes sqrt(N), Theorem 5 where it passes the cube root, else
    huntlib's bounded search on N alone."""
    N = int(N)
    if N < MR_VALID_BELOW:
        p = certificate.prove(N)
        return p if _verified(p) else None
    F = 1
    for p, e in fac.items():
        F *= int(p) ** int(e)
    if (N - 1) % F == 0 and F % 2 == 0 and math.gcd(F, (N - 1) // F) == 1:
        R = (N - 1) // F
        subs = {str(int(p)): subproofs[int(p)] for p in fac
                if int(p) >= MR_VALID_BELOW and int(p) in subproofs}
        if all(int(p) < MR_VALID_BELOW or str(int(p)) in subs for p in fac):
            w = certificate.witnesses(N, sorted(int(p) for p in fac))
            if w is not None:
                out = {"N": N, "F": F, "R": R,
                       "factors": {str(int(p)): int(e) for p, e in sorted(fac.items())},
                       "witnesses": {str(p): a for p, a in sorted(w.items())}}
                if subs:
                    out["subproofs"] = subs
                if F > math.isqrt(N):
                    out["proof"] = "bls75-thm1"
                    if _verified(out):
                        return out
                elif F ** 3 > N:
                    s, r = certificate.theorem5_split(F, R)
                    out["proof"], out["s"], out["r"] = "bls75-thm5", s, r
                    if _verified(out):
                        return out
    proof = certificate.prove(N, fac={int(p): int(e) for p, e in fac.items()
                                      if int(p) < MR_VALID_BELOW} or None)
    if not _verified(proof):
        proof = certificate.prove(N, ecm_curves=CERT_RETRY_CURVES,
                                  budget=CERT_RETRY_SPLITS)
    return proof if _verified(proof) else None


def term_factors(x):
    """{p: e} of the term, every p proved (or subproved by the certificate
    that admits it): huntlib's bounded chain, then sympy's factorint on
    what is left -- the one factorization a discovery costs."""
    return {int(p): int(e) for p, e in certificate.factor_full(int(x)).items()}


def certify_run(x, run, fam, n):
    """A re-verified certificate for every value of a run, in form order:
    ({str(k): proof}, [the k left UNPROVED]).  Each Phi_k(x) - 1 is
    factored by its shape (minus_one_shape): x's own factorization, the
    values Phi_d(x) of the run already proved (their proofs the subproofs),
    any other Phi_d(x) and the leftover polynomial's value through
    huntlib's bounded factor_partial."""
    fam = ref.family(fam)
    x, run, n = int(x), int(run), int(n)
    rn = n if per_index(fam) else max(run, 1)
    ks = list(ref.forms(fam, rn))[:run]
    fx = term_factors(x)
    certs, unproved, proved_values = {}, [], {}
    for k in ks:
        N = ref.value(k, x)
        if N < MR_VALID_BELOW:
            proof = certify_value(N, {}, {})
        else:
            fac, subs = {}, {}
            for kind_, j, e in minus_one_shape(k):
                if kind_ == "x":
                    for p, ee in fx.items():
                        fac[p] = fac.get(p, 0) + ee * e
                    continue
                if kind_ == "const":
                    for p, ee in certificate.factor_full(abs(j)).items():
                        fac[int(p)] = fac.get(int(p), 0) + int(ee)
                    continue
                v = ref.value(j, x) if kind_ == "phi" else _poly_value(j, x)
                if v in (1, -1):
                    continue
                if v < 0:
                    v = -v
                if kind_ == "phi" and v in proved_values:
                    fac[v] = fac.get(v, 0) + e
                    subs[v] = proved_values[v]
                    continue
                if v < MR_VALID_BELOW and mr_is_prime(v):
                    fac[v] = fac.get(v, 0) + e
                    continue
                part, _R = certificate.factor_partial(v)
                for p, ee in part.items():
                    fac[int(p)] = fac.get(int(p), 0) + int(ee) * e
            proof = certify_value(N, fac, subs)
        certs[str(k)] = proof
        if proof is None:
            unproved.append(str(k))
        else:
            proved_values[N] = proof
    return certs, unproved


def also_settles(fam, x, run, settles, terms=None):
    """What a find settles in DERIVED entries, under the letter that
    entry's own lines give the term (A233512's name gives none; its %C and
    %e lines say x).

    A233512 is A070737 with the arguments STRICTLY INCREASING: B(n) is the
    least x > B(n - 1) with the first n values prime, where A070737's A(n)
    is the least such x at all, A(n) >= A(n - 1).  G1d proves B(n) = A(n)
    for n = 5..10.  Inductively, if B(n - 1) = A(n - 1) and A(n) > A(n - 1)
    then B(n) = A(n); if A(n) = A(n - 1) (a plateau) then B(n) > A(n) is
    unknown and the chain is broken from there on (Codex CYL-005: the
    first cut settled the rider at EVERY index a find settles, which a
    plateau makes false).  So a find x that settles [m0, m0 + 1, ...]
    settles the rider at m0 ALONE, and only if the primary terms from
    a(from_n) to a(m0 - 1) are all known and strictly increasing (the
    chain intact) and x > a(m0 - 1); a plateau's later indices stay open.
    `terms` is {index: a(index)} of the primary entry -- the published
    terms plus this campaign's finds -- and defaults to the published."""
    fam = ref.family(fam)
    x = int(x)
    terms = (dict(ref.KNOWN[fam]) if terms is None
             else {int(k): int(v) for k, v in terms.items()})
    out = []
    if not settles:
        return out
    m0 = int(min(settles))
    for seq in ref.FAMILIES[fam]["also"]:
        d = ref.DERIVED[seq]
        if m0 < d["from_n"]:
            continue
        chain = [terms.get(i) for i in range(d["from_n"], m0)]
        if any(v is None for v in chain):
            continue                        # a gap: the chain is not known
        if any(b <= a for a, b in zip(chain, chain[1:])):
            continue                        # a plateau broke the chain
        if chain and x <= chain[-1]:
            continue                        # x is not above B(m0 - 1)
        out.append({"sequence": seq, "n": m0, d["term"]: x})
    return out


# ----------------------------- classification -------------------------------

def filter_forms(fam, n):
    """The coefficient tuples of the forms a pool worker reads at filter n,
    in run order -- the first read_index(n) polynomials on A070737, the
    divisors of n on A072942.  A worker is another process; it is handed
    what it needs and nothing of the engines."""
    fam = ref.family(fam)
    return tuple(ref.cyclotomic(k) for k in ref.forms(fam, read_index(fam, n)))


def sprp_run(x, forms):
    """The run of x, read with a base-2 strong probable-prime test on each
    value, the values formed by Horner from the coefficients.

    A failed base-2 test is a PROOF of compositeness (huntlib.primes), so
    the screen can only overstate a run, never understate it.  The census
    is counted on this chain -- it is a count, not a claim -- and every
    value that is narrated (a NEAR) or recorded (a DISCOVERY) is verified
    three ways first (verify).
    """
    x = int(x)
    r = 0
    for cs in forms:
        v = 0
        for c in reversed(cs):
            v = v * x + c
        if v < 2 or not sprp_base2(v):
            break
        r += 1
    return r


def _classify_chunk(task):
    """Pool worker: runs of a chunk of survivors, in order."""
    forms, ks = task
    return [sprp_run(int(k), forms) for k in ks]


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


def _submit(pool, forms, ks):
    ks = [int(k) for k in ks]
    out = []
    for i in range(0, len(ks), CHUNK):
        chunk = ks[i:i + CHUNK]
        if pool is None:
            out.append((chunk, _Done(_classify_chunk((forms, chunk)))))
        else:
            out.append((chunk, pool.submit(_classify_chunk, (forms, chunk))))
    return out


def condition(fam, k):
    """The condition of cyclotomic index k in the entry's own letters."""
    fam = ref.family(fam)
    t = TERM(fam)
    if per_index(fam):
        return f"Phi({int(k)},{t}) prime"
    return f"Phi_{int(k)}({t}) prime"


def headline(fam, settles, x):
    fam = ref.family(fam)
    if len(settles) == 1:
        return f"{fam} a({settles[0]}) = {int(x):,}"
    return f"{fam} a({settles[0]})..a({settles[-1]}) = {int(x):,}"


def evidence_name(fam, n, x):
    return f"{ref.family(fam)}_a{int(n)}_{int(x)}.json"


# --------------------------------- campaign ---------------------------------

class Campaign:
    def __init__(self, args, ckpt=None, cursor=None, pool=None, evid=None):
        self.args = args
        self.fam = ref.family(args.family)
        self.oeis = self.fam
        self.term = TERM(self.fam)
        self.per_index = per_index(self.fam)
        # DRILLS ONLY: open below the published frontier so that a drill's
        # "find" is a real published term; and stop before the filter of
        # `stop_n`, so a drill never sweeps an open index (CLAUDE.md 0a).
        self._known_top = (int(args.start_n) - 1 if getattr(args, "start_n", None)
                           else (max(ref.KNOWN[self.fam]) if not self.per_index else 0))
        self._stop_n = (int(args.stop_n) if getattr(args, "stop_n", None)
                        else None)
        # the one index an A072942 campaign hunts (a drill names a
        # published one through start_n)
        if self.per_index:
            self.index = int(getattr(args, "start_n", None) or getattr(args, "index", None)
                             or open_n(self.fam))
            if ref.term(self.fam, self.index, missing=None) is not None and \
                    not getattr(args, "start_n", None):
                raise ValueError(f"{self.fam} a({self.index}) is published or "
                                 f"found already; the open indices are "
                                 f"{ref.open_indices(self.fam)}")
        else:
            self.index = None
        self.key = config_key(self.fam, self.index)
        self.ckpt = ckpt or ckpt_path(self.fam, self.index)
        self.cursor = cursor or policy(self.fam, self.index)
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
        # the x below which the line is covered by an EARLIER filter's
        # classified sweep (the carried line; A070737 only); the sweep of
        # the current filter starts at max(its floor, this)
        self.cover_x = 0
        # the filter whose exception zone has been covered by brute force
        self.zone_n = 0
        self.start_x = 0               # where this campaign first started
        self.closed = False            # A072942: the index has been found
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
        self._stored = None
        self.loaded = self.load()
        self.eng = self._build_engine(self.filter_n())
        if self._stored_n is not None and self._stored_n != self.filter_n():
            raise ValueError(
                f"{self.ckpt} holds a cursor for filter n = {self._stored_n} "
                f"but this campaign's filter is n = {self.filter_n()}: "
                f"the stored `found` and the stored filter disagree, so the "
                f"cursor cannot be read")
        if self.loaded and self._load_kind == "adopted":
            self.adopt_cursor()
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

    def adopt_cursor(self):
        """A cursor written under an older PLAN whose wheel at this filter
        has moved (policy: adopt): the one claim that carries over is the
        swept boundary `k` -- the x below which every value at or above the
        sweep's floor was swept -- and it is re-denominated onto THIS
        engine's periods with flooring, so no gap opens: j = k // W, and the
        line between j*W and k (under one period) is swept again.  The work
        cursor inside the old segment (u) counted launches of a different
        wheel and is dropped: the segment at j is swept from its start, and
        the census it had counted is counted once more (counts, not
        claims).  Finds, pending values, rungs passed, census, near and
        survivor counts are carried as they are.  CONVENTIONS.md "Reading
        an existing cursor"; the live n = 60 cursor of A072942 was adopted
        this way onto planner p3's wheel (2026-10-24)."""
        st = self._stored
        k_old = int(st.get("k", 0))
        W = int(self.eng.W)
        j_new = max(k_old // W, self.floor_period())
        if j_new * W > k_old and k_old > 0:
            raise ValueError(f"adoption would claim x < {j_new * W} from a "
                             f"cursor swept to {k_old}")
        units = (int(self.eng.seg_periods), int(self.eng.launches_per_segment))
        log("STAGE",
            f"cursor ADOPTED from plan {st.get('plan', '?')} (key "
            f"{st.get('key')}): it counted periods of W = {self._stored_w:,} "
            f"and this plan's wheel at n = {self.filter_n()} has W = {W:,}; "
            f"swept to {self.term} = {k_old:,} carries over as period "
            f"{j_new} (x >= {j_new * W:,} is swept again, "
            f"{k_old - j_new * W:,} of line given back); the old work cursor "
            f"(period {self.j}, launch {self.u:,} of "
            f"{self._stored_units[1]:,}) is dropped and the segment at "
            f"{j_new} is swept from its start in launches of this plan's "
            f"({units[1]:,} a segment of {units[0]} periods); its census is "
            f"counted again")
        self.j, self.u = j_new, 0
        self._stored_w = W
        self._stored_units = units
        self._adopted_from = (st.get("key"), k_old)

    def _build_engine(self, n):
        ok, q = ref.admissible(self.fam, n)
        if not ok:                     # a theorem says never; checked anyway
            banner("MILESTONE", [
                f"{self.oeis} IS FINITE: at index {n} the conditions kill "
                f"EVERY residue class mod {q}"])
            raise SystemExit(0)
        unit, p1, p2, p3, q2, pb = plan_for(self.fam, n)
        return gpu.GpuEngine(n, self.fam, p1=p1, p2=p2, p3=p3, q2=q2,
                             unit=unit, pb=pb, seg_cap=pb, prp=CENSUS_FLOOR)

    # ------------------------------------------------------------- frontier
    def frontier(self):
        """A070737: the largest index settled.  A072942: the run one short
        of a discovery -- the number of divisors less one -- so that
        event_kind reads the same way on both."""
        if self.per_index:
            return ref.nforms(self.fam, self.index) - 1
        top = self._known_top
        for n in self.found:
            top = max(top, int(n))
        return top

    def frontier_k(self):
        if self.per_index:
            return ref.X_MIN
        n = self.frontier()
        return int(self.found.get(str(n), ref.KNOWN[self.fam].get(n, 0)))

    def filter_n(self):
        if self.per_index:
            return self.index
        return self.frontier() + 1

    def x_start(self):
        """The floor of THIS filter's sweep: the frontier term (inclusive),
        or the carried coverage of the previous filter, whichever is
        higher; x = 3 on A072942."""
        return max(x_floor(self.fam, self.filter_n(), self.frontier_k()),
                   int(self.cover_x))

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
        """The index whose forms the classification reads: the filter plus
        RUN_AHEAD on A070737, or in a drill no further than the index it was
        opened to find (a drill never settles an index it was not opened
        for; CLAUDE.md 0a); the index itself on A072942."""
        if self.per_index:
            return self.index
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
    def _build_ladder(self, frontier, frontier_k, n):
        ceil = cpu.k_ceil(n, self.fam)
        if self.per_index:
            preds = model.predictions_index(self.fam, n, ceiling=ceil)
        else:
            preds = model.predictions(self.fam, frontier, frontier_k,
                                      n_ahead=3, ceiling=ceil)
        return Ladder.from_predictions(preds, ceiling=ceil,
                                       ceiling_label="engine ceiling")

    def ladder(self):
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
        return cpu.k_proof(self.filter_n(), self.fam)

    def check_proof_crossing(self, k):
        if self._proof_logged == self.filter_n():
            return
        pc = self.proof_crossing()
        if k >= pc:
            self._proof_logged = self.filter_n()
            log("MILESTONE",
                f"past the proof crossing of {self.oeis} at filter n = "
                f"{self.filter_n()}, {self.term} = {pc:,}: the largest value "
                f"formed exceeds the deterministic Miller-Rabin bound, so "
                f"classification is a strong probable-prime chain (the "
                f"census is counted and a NEAR is a health check either "
                f"way) and a DISCOVERY's values are each proved by BLS75 on "
                f"the value less one, which is a power of {self.term} times "
                f"earlier cyclotomic values of the same run -- re-verified "
                f"before it is written; the ceiling is {self.term} < "
                f"{cpu.k_ceil(self.filter_n(), self.fam):.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "plan": PLAN_VERSION,
                "family": self.fam,
                "index": self.index,
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
                "closed": bool(self.closed),
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
        t_save = time.perf_counter()        # the snapshot is part of the cost
        self.mark_boundary()
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
        self._stored = st
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
        self.closed = bool(st.get("closed", False))
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
                 (f"{self.oeis} index n = {self.index}" if self.per_index
                  else f"{self.oeis} filter n = {self.filter_n()}")]
        if rate:
            parts.append(f"{rate:.3g} {self.term}/s")
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
            parts.append(f"next {lab} {d:.4g} (ETA {eta})")
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
        """Classify one value.  True if it was a find."""
        frontier = self.frontier()
        kind = event_kind(run, frontier)
        if kind is None:
            return False
        self.census[run] = self.census.get(run, 0) + 1
        if kind == "CENSUS":
            return False
        if kind == "NEAR":
            if self._stop_n is not None and not self.per_index and run >= self.run_cap():
                # a drill reads runs no further than its bound: a value at
                # the cap may run on past it, and is not narrated
                return False
            self.near += 1
            ok, legs, _ = verify(k, run, self.fam, self.filter_n(), witness=False)
            if not ok:
                log("ALARM", f"NEAR candidate {self.term} = {k:,} run {run} "
                             f"failed verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at {self.term} = {k:,} (run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of a({self.filter_n()})!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, x, run):
        frontier = self.frontier()
        n = self.filter_n()
        self.hb.doing(f"verifying run-{run} {self.term}={x}")
        # the run, re-read with NO cap by the oracle: a run at the
        # classification's cap may be longer (A070737; an A072942 run is
        # the whole divisor list)
        read_to = n if self.per_index else cpu.n_max(self.fam)
        full = ref.run_length(self.fam, x, read_to)
        want = ref.nforms(self.fam, n) if self.per_index else n
        if full < run or full < want or x < self.x_start():
            log("ALARM", f"claimed {self.oeis} a({n}) = {x} (run {run}) is "
                         f"not a term by the oracle: run {full}, floor "
                         f"{self.x_start()}")
            raise SystemExit(2)
        run = full
        ok, legs, stop = verify(x, run, self.fam, n)
        if not ok:
            log("ALARM", f"claimed a({n}) = {x} failed the protocol: {legs}")
            raise SystemExit(2)
        settles = [n] if self.per_index else list(range(frontier + 1, run + 1))
        self.hb.doing(f"certifying run-{run} {self.term}={x}")
        certs, unproved = certify_run(x, run, self.fam, n)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        terms = {**ref.KNOWN[self.fam],
                 **{int(m): int(v) for m, v in self.found.items()}}
        also = also_settles(self.fam, x, run, settles, terms)
        ks = list(ref.forms(self.fam, n if self.per_index else run))[:run]
        vals = [ref.value(k, x) for k in ks]
        fx = term_factors(x)
        ev = {**evidence.header(self.oeis, ref.FAMILIES[self.fam]["forms"],
                                self.term, x, settles),
              "filter_n": int(n), "run": int(run), "settles": settles,
              "conditions": {str(k): condition(self.fam, k) for k in ks},
              "values": {str(k): int(v) for k, v in zip(ks, vals)},
              f"{self.term}_factored": {str(p): e for p, e in sorted(fx.items())},
              "verification": legs,
              "stopper": ({ref.FAMILIES[self.fam]["poly"]: stop["k"],
                           "condition": condition(self.fam, stop["k"]),
                           "value": int(stop["value"]),
                           "why": stop["why"],
                           "factor": stop["factor"]} if stop is not None
                          else {"none": "every divisor's value is prime: the "
                                        "run is the whole form list"}),
              "certificates": certs,
              "certificates_verified": not unproved,
              "unproved": unproved,
              "proof_routes": routes,
              "also_settles": also,
              "least_claim": {"swept_from": int(self.x_start()),
                              "campaign_started_at": int(self.start_x),
                              "swept_to": int(x),
                              "floor": (f"x = {ref.X_MIN}: every index of "
                                        f"{self.oeis} is its own line"
                                        if self.per_index else
                                        f"a({frontier}) = {self.frontier_k()}, "
                                        f"inclusive: the conditions nest"),
                              "carried": (f"the line below {self.cover_x} was "
                                          f"classified by the previous filter "
                                          f"with runs read to the filter + "
                                          f"{RUN_AHEAD}" if self.cover_x else None),
                              "exception_zone": list(self.zone()) if self.zone() else None,
                              "filter": int(n),
                              "wheel": int(self.eng.W),
                              "sieve_depth": int(self.eng.q2),
                              "fermat_stage": int(self.eng.prp),
                              "class": [int(self.eng.r0), int(self.eng.unit)]},
              "engine": self.key}
        for m in settles:
            self.found[str(m)] = int(x)
        # THE LEDGER ROW'S IDENTITY (Codex CYL-006): the shared ledger keeps
        # one row per key and drops an earlier row with the same key.  On
        # A070737 a find is one row (one x settles every index of its run),
        # so x is the identity; on A072942 two indices may have the same
        # least x (a(1) = a(3) = a(7) = 3, and nothing excludes a(48) =
        # a(96)), so the row is keyed by (index, x) -- the integer index x
        # 10^41 + x, x below the 10^40 ceiling -- and both rows survive.
        if self.per_index:
            ev["ledger_key"] = int(n) * 10 ** 41 + int(x)
            key = "ledger_key"
        else:
            key = self.term
        path = evidence.record(
            ev, self.evid, evidence_name(self.oeis, settles[0], x),
            self.ledger, key=key,
            label="%s a(%s)" % (self.oeis, ",".join(map(str, settles))))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        lines = [
            headline(self.oeis, settles, x),
            (f"every Phi(d,{self.term}), d | {n}, prime ({run} values)"
             if self.per_index else
             f"run {run}: Phi_k({self.term}) prime for k = 1..{run}")]
        if stop is not None:
            lines.append(f"stopped at k = {stop['k']}: {condition(self.fam, stop['k'])} "
                         f"fails, the value is {stop['why']}"
                         + (f" = {stop['factor']} x ..." if stop["factor"] else ""))
        lines.append(f"verified 3 ways, {proved} of {len(certs)} certificates "
                     f"re-verified ({', '.join(f'{r} x{c}' for r, c in sorted(routes.items()))}), "
                     f"evidence {path}")
        if also:
            lines.append("also settles " + ", ".join(
                f"{a['sequence']} a({a['n']})" for a in also))
        if unproved:
            lines.append(f"UNPROVED at k = {unproved}: those values passed "
                         f"the Miller-Rabin chain and BPSW and no "
                         f"certificate landed within the bounded effort; "
                         f"the find stands on the three legs; certify them "
                         f"by hand from the evidence file")
        banner("DISCOVERY", lines)

    def follow_frontier(self, old_boundary_x):
        """After a find.  A070737: rebuild the engine at the next open index;
        the classified line is carried and the sweep resumes at the old
        segment's end, re-denominated by floor into the new period with the
        clip at the old boundary.  A072942: the index is CLOSED -- there is
        nothing more to sweep for -- and the campaign ends; main() moves to
        the next open index."""
        if self.per_index:
            self.closed = True
            self.pending = []
            log("STAGE",
                f"index closed: {self.oeis} a({self.index}) is found, so its "
                f"line has nothing more to sweep for; the campaign moves to "
                f"the next open index of TARGETS "
                f"({next_target(self.fam, {self.index})})")
            self.mark_boundary()
            return
        old = self.eng
        self.cover_x = int(old_boundary_x)
        self.eng = self._build_engine(self.filter_n())
        self.key = config_key(self.fam, self.index)
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
            f"the line below {self.cover_x:,} is CARRIED (classified by the "
            f"old filter with runs read to n + {RUN_AHEAD}) and the sweep "
            f"resumes there, floored into the new period {self.j} with the "
            f"clip at the old boundary; the ladder now aims at "
            f"a({self.filter_n()})")
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
        filter: every integer between the sweep's floor and the engine's
        floor, through the same taxonomy as a device survivor.  Returns
        True if a find landed there."""
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
                                   read_n=self.run_cap())
            hits = [(x, r) for x, r in hits if x >= lo]
            for x, r in hits:
                self.survivors += 1
                if self.handle(x, r):
                    found_now = True
                    break
            log("STAGE",
                f"exception zone of {self.oeis} at filter n = {n}: the "
                f"{hi - lo + 1:,} integers in [{lo:,}, {hi:,}] -- between the "
                f"sweep's floor and the engine's (a kill by a sieve prime "
                f"needs the value to exceed it) -- classified one at a time "
                f"on the host in {time.perf_counter() - t0:.1f} s: "
                f"{len(hits)} at run >= {CENSUS_FLOOR}"
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
        forms = filter_forms(self.fam, self.filter_n())
        sample = surv[:CAL_SAMPLE]
        t1 = time.perf_counter()
        for k in sample:
            sprp_run(k, forms)
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
        # a run the frontier has already settled the successor of is
        # counted only, at every frontier this segment can reach (it only
        # rises, at the segment's end): COUNT it here rather than holding
        # its value to the segment's end
        frontier = self.frontier()
        while inflight:
            cur, parts = inflight[0]
            if not block and not all(f.done() for _ks, f in parts):
                break
            inflight.popleft()
            for ks, f in parts:
                for k, r in zip(ks, f.result()):
                    self.survivors += 1
                    kind = event_kind(r, frontier)
                    if kind == "CENSUS":
                        self.census[r] = self.census.get(r, 0) + 1
                    elif kind is not None:
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
        if self.closed:
            log("STAGE", f"{self.oeis} a({self.index}) was found by an earlier "
                         f"run of this campaign ({self.found}); nothing to "
                         f"sweep -- the next open index is "
                         f"{next_target(self.fam, {self.index})}")
            return 0
        log("STAGE", device_report(self.eng.bytes_held()))
        cfg = self.eng.config()
        log("STAGE",
            f"sweeping the {self.term} line to {target:.4g}; {self.oeis} "
            f"({ref.FAMILIES[self.fam]['forms']}) "
            + (f"index n = {self.index} ({ref.nforms(self.fam, self.index)} "
               f"conditions)" if self.per_index else f"filter n = {self.filter_n()}")
            + f"; wheel W = {self.eng.W:,} at unit "
            f"{self.eng.unit} ({self.eng.R:,} residues, "
            f"{self.eng.R1} x {self.eng.R2} x {self.eng.R3}"
            f", {100.0 * self.eng.density():.6f}% "
            f"of the line); a segment is {self.eng.seg_periods} periods "
            f"({self.eng.seg_periods * self.eng.W:.4g} of line) in "
            f"{self.eng.launches_per_segment} launches of "
            f"{cfg['cand_per_launch']:.3g} candidates; the sieve runs to "
            f"{self.eng.q2} and the device Fermat-tests the first "
            f"{len(self.eng.prp_forms)} conditions of every survivor; the "
            f"sweep's floor is {self.term} = {self.x_start():,}; resume at "
            f"period {self.j}, launch {self.u} ({self.term} = "
            f"{self.u_progress(self.j, self.u):,})")
        preds = (model.predictions_index(self.fam, self.index,
                                         ceiling=cpu.k_ceil(self.index, self.fam))
                 if self.per_index else
                 model.predictions(self.fam, self.frontier(), self.frontier_k(),
                                   n_ahead=3,
                                   ceiling=cpu.k_ceil(self.filter_n(), self.fam)))
        for n, qs in sorted(preds.items()):
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
                self.follow_frontier(self.boundary * self.eng.W)
                stop_now = bool(self.args.stop_on_discovery) or self.closed
                self.save()
            forms = filter_forms(self.fam, self.filter_n())
            while self.swept_k() < target and not stop_now:
                if self._stop_n is not None and not self.per_index and \
                        self.filter_n() >= self._stop_n:
                    log("STAGE", f"drill bound: this drill campaign stops "
                                 f"before the filter for a({self.filter_n()})")
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
                    inflight.append(((jn, un), _submit(self.pool, forms, surv)))
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
                # A RUN AT THE CLASSIFICATION'S CAP IS "AT LEAST THAT LONG"
                # (Codex CYL-007): the pool reads runs to the filter plus
                # RUN_AHEAD, and a find among the pending values moves the
                # frontier before the values after it are classified -- so a
                # later value stored at the old cap, whose true run passes
                # the new frontier, would be counted as census and lost.
                # Every pending value at or past the cap the segment was
                # swept under is re-read uncapped by the oracle first (a
                # drill reads no further than the index it was opened for).
                cap0 = self.run_cap()
                read_to = (cpu.n_max(self.fam) if self._stop_n is None
                           else max(cap0, int(self._stop_n) - 1))
                for k, r in sorted(self.pending):
                    if not self.per_index and r >= cap0:
                        r = ref.run_length(self.fam, k, read_to)
                    if self.handle(k, r):
                        found_now = True
                        if self.per_index:
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
                        f"line; {held} value{'' if held == 1 else 's'} one "
                        f"short of the frontier or past it classified in "
                        f"numerical order, the census counted as it came"
                        + (f"; {self._plog_n} segments closed since the last "
                           f"such line" if self._plog_n > 1 else "") + ")")
                    self._plog_t, self._plog_n = time.time(), 0
                if found_now:
                    self.follow_frontier(self.boundary * self.eng.W)
                    forms = filter_forms(self.fam, self.filter_n())
                    stop_now = bool(self.args.stop_on_discovery) or self.closed
                self.hb.mark(self.swept_k())
                self.check_rungs(self.swept_k())
                self.check_proof_crossing(self.swept_k())
                if found_now or self.save_due():
                    self.save()
                else:
                    self.mark_boundary()
                if stop_now and not self.closed:
                    log("STAGE", "stopping on discovery "
                                 "(--stop-on-discovery): THIS run confirmed "
                                 "a frontier-extending find")
        finally:
            self.hb.stop()
            if self.pool is not None:
                self.pool.shutdown(wait=False, cancel_futures=True)
        landed = self.save()
        log("STAGE", f"campaign stopped at {self.term} = {self.swept_k():,} "
                     f"({self.discoveries} find(s) this campaign; checkpoint "
                     f"{'written' if landed else 'DEFERRED -- held open'})"
                     + ("; the index is closed" if self.closed else ""))
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
    filter n = 11 of A070737 (frontier 10) a full run is 11, one short is
    10; at index 60 of A072942 (12 divisors, frontier 11) a full run is 12,
    one short is 11."""
    return [((11, 10), "DISCOVERY"),
            ((13, 10), "DISCOVERY"),      # a long run settles several at once
            ((10, 10), "NEAR"),
            ((9, 10), "CENSUS"),
            ((6, 10), "CENSUS"),
            ((5, 10), None),
            ((0, 10), None),
            ((12, 11), "DISCOVERY"),
            ((11, 11), "NEAR"),
            ((7, 11), "CENSUS"),
            ((4, 11), None)]


# The canaries: published terms a mini-hunt reaches from the index's floor
# in a second or two, each in its forced class.
_CANARIES = (("A070737", 7, 210), ("A070737", 8, 210),
             ("A072942", 24, 2730), ("A072942", 30, 14322),
             ("A072942", 40, 2 * 3 * 5 * 11 * 41), ("A072942", 44, 2 * 3 * 5 * 23))


def _canary_hunt():
    """The stream must organically rediscover published terms, in both
    families, from the index's floor (inclusive), so FIRST is a claim about
    the line."""
    hits_all = []
    for fam, n, unit in _CANARIES:
        if cpu.forced_unit(n, fam) != unit:
            return False, f"CANARY FAIL: {fam} n = {n} forces {cpu.forced_unit(n, fam)}, not {unit}"
        want = ref.KNOWN[fam][n]
        q2 = 4096
        nf = ref.nforms(fam, n)
        # the device Fermat stage on every form: what reaches the host is a
        # superset of every value whose run reaches the full form count
        eng = gpu.GpuEngine(n, fam, p1=19, p2=None, p3=None, q2=q2,
                            unit=unit, prp=nf)
        lo = x_floor(fam, n, ref.KNOWN[fam].get(n - 1, 0))
        pre = [x for x, r in cpu.prefix_hits(fam, n, q2, floor=nf) if x >= lo]
        if pre and min(pre) < want:
            return False, f"CANARY FAIL: {fam} n={n}: the zone holds {min(pre)}"
        start = max(lo, cpu.k_floor(q2, n, fam) + 1)
        ceng = cpu.CpuEngine(n, fam, q2=q2)
        surv = eng.survivors_j(start // eng.W, want // eng.W + 1, k_min=start)
        hits = [int(k) for k in surv if ceng.run_length(int(k)) >= nf]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: {fam} index n={n} unit={unit} "
                           f"found {min(hits) if hits else None}, "
                           f"expected a({n}) = {want}")
        hits_all.append(f"{fam} a({n}) (class 0 mod {unit})")
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as FIRST occurrences from each "
                  "index's floor, in class space, both families, through the "
                  "device Fermat stage on every form")


def _true_run(fam, n):
    """The run of the published a(n): the form count, or more where the
    entry's term passes its index (cyclotomic_reference.RUNS_PAST)."""
    if per_index(fam):
        return ref.nforms(fam, n)
    return ref.RUNS_PAST.get(fam, {}).get(n, n)


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on both families."""
    fam = "A070737"
    top = max(ref.KNOWN[fam])
    x = ref.KNOWN[fam][top]
    ok, legs, stop = verify(x, top, fam, top)
    if not ok or stop is None or stop["k"] != top + 1 or stop["factor"] is None:
        return False, (f"PROTOCOL FAIL: genuine a({top}) = {x} ({fam}) at its "
                       f"run {top} rejected: {legs} {stop}")
    if stop["value"] % stop["factor"] or stop["factor"] in (1, stop["value"]):
        return False, f"PROTOCOL FAIL: {fam}: the witness is not a factor"
    bad, legs_b, _ = verify(x, top + 1, fam, top + 1)
    if bad:
        return False, (f"PROTOCOL FAIL: fake run-{top + 1} claim at {x} "
                       f"({fam}) ACCEPTED ({legs_b})")
    fake, _lc, _ = verify(ref.KNOWN[fam][9], top, fam, top)
    if fake:
        return False, f"PROTOCOL FAIL: {fam}: a(9) accepted as a run-{top}"
    ok3, _l3, stop3 = verify(6, 4, fam, 3)           # a(3) = 6 runs to 4
    if not ok3 or stop3["k"] != 5:
        return False, "PROTOCOL FAIL: a(3) = a(4) = 6 at its true run 4 rejected"
    fam = "A072942"
    for n in (36, 70):
        x = ref.KNOWN[fam][n]
        nf = ref.nforms(fam, n)
        ok, legs, stop = verify(x, nf, fam, n)
        if not ok or stop is not None:
            return False, (f"PROTOCOL FAIL: genuine {fam} a({n}) = {x} rejected: "
                           f"{legs} {stop}")
        okn, legsn, stopn = verify(x, nf - 1, fam, n, witness=False)
        if not okn or stopn is None or stopn["why"] != "composite" or stopn["value"] != ref.value(ref.forms(fam, n)[-1], x):
            # a solution read one short: its "stopper" is the last divisor's
            # value, which is PRIME, so the one-short claim must FAIL
            pass
        if okn:
            return False, f"PROTOCOL FAIL: {fam} a({n}) accepted one condition short"
        wrong, legs_w, _ = verify(x, ref.nforms(fam, 60), fam, 60)
        if wrong:
            return False, f"PROTOCOL FAIL: {fam} a({n})'s x accepted as a solution of index 60"
    return True, ("protocol ok, both families: A070737's a(10) accepted at "
                  "run 10 with a factor witness for Phi_11, a run one too "
                  "long and a(9) mislabelled as run 10 both rejected, a(3) = "
                  "6 accepted at its true run 4; A072942's a(36) and a(70) "
                  "accepted as solutions of their own index (no stopper: "
                  "every divisor's value is prime), rejected one condition "
                  "short (the last value is prime, not a stopper) and "
                  "rejected as solutions of index 60")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing, on both families."""
    raised = []
    for fam, n, unit in (("A070737", 11, 2310), ("A072942", 60, 56786730)):
        eng = gpu.GpuEngine(n, fam, p1=19, p2=None, p3=None, q2=1024, unit=unit)
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
    try:
        gpu.wheel(3, "A070737", 59, unit=6)
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(5, "A070737", p1=37, p2=None, p3=None, q2=4096, unit=30)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    # the residue list holds NRES_MAX kills a prime and a prime can kill up
    # to the sum of phi(k) over the forms: the first index past n_max is
    # refused on A070737 (n = 21: 140 > 128)
    n = cpu.n_max("A070737") + 1
    if ref.maxkills("A070737", n) <= gpu.NRES_MAX:
        return False, f"CEILING FAIL: A070737 n = {n} fits the residue list"
    try:
        gpu.GpuEngine(n, "A070737", p1=29, p2=None, p3=None, q2=1024,
                      unit=cpu.forced_unit(n, "A070737"))
        return False, "CEILING FAIL: a filter whose kills overflow the tail's residue list was accepted"
    except ValueError:
        raised.append(f"maxkills <= NRES_MAX (A070737 n = {n})")
    for fam, n, unit in (("A070737", 11, 2 * 2310), ("A070737", 11, 13 * 2310),
                         ("A072942", 60, 17 * 56786730), ("A072942", 60, 4),
                         ("A070737", 11, 67)):
        try:
            gpu.GpuEngine(n, fam, p1=19, p2=None, p3=None, q2=1024, unit=unit)
            return False, f"CEILING FAIL: unit {unit}, which nothing forces on {fam} n = {n}, was accepted"
        except ValueError:
            raised.append(f"unit {unit} refused ({fam})")
    try:
        gpu.GpuEngine(9, "A000001", p1=13, p2=None, p3=None, q2=1024)
        return False, "CEILING FAIL: an unknown family was accepted"
    except KeyError:
        raised.append("family")
    return True, ("ceiling ok: %s all raise rather than compute" %
                  ", ".join(raised))


_BLS_ROUTES = ("bls75-thm1", "bls75-thm5", "bls75-thm15")


def _check_cert(c, N, label, routes=None):
    if c is None or c.get("proof") not in _BLS_ROUTES:
        return False, (f"{label}: not proved by a BLS75 route "
                       f"({c and c.get('proof')})")
    if routes is not None and c.get("proof") not in routes:
        return False, f"{label}: proved by {c.get('proof')}, not {routes}"
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
    """A discovery past the proof crossing is PROVED on its own structure:
    every value of A070737's a(10) (to 65 digits) and of A072942's a(36)
    (to 190 digits: Phi_36 at 2.4e16) on the N - 1 route, the run's own
    earlier values standing in F with their certificates as subproofs; the
    shapes of Phi_k(x) - 1 multiply back; and AT THE CEILING, Phi_2, Phi_3
    and Phi_4 of an x near 1e40 whose prime factor is past the
    deterministic bound, so the subproof is exercised and cannot be
    stripped."""
    parts = []
    t0 = time.time()
    for k in list(range(1, 21)) + [24, 30, 36, 40, 48, 60, 72, 96]:
        shape = minus_one_shape(k)
        xv = 10 ** 6 + 7
        prod = 1
        for kind_, j, e in shape:
            if kind_ == "x":
                prod *= xv ** e
            elif kind_ == "phi":
                prod *= ref.value(j, xv) ** e
            elif kind_ == "const":
                prod *= j
            else:
                prod *= _poly_value(j, xv) ** e
        if prod != ref.value(k, xv) - 1:
            return False, f"CERTIFICATE FAIL: the shape of Phi_{k}(x) - 1 does not multiply back"
    for fam, n in (("A070737", 10), ("A072942", 36)):
        x = ref.KNOWN[fam][n]
        run = _true_run(fam, n)
        certs, unproved = certify_run(x, run, fam, n)
        if unproved:
            return False, f"CERTIFICATE FAIL: {fam} a({n}) left {unproved} unproved"
        ks = ref.forms(fam, n)
        subbed = 0
        for k in ks:
            proof = certs[str(k)]
            N = ref.value(k, x)
            if N < MR_VALID_BELOW:
                if proof.get("proof") != "deterministic-mr":
                    return False, f"CERTIFICATE FAIL: {fam} k = {k} under the bound took {proof.get('proof')}"
                continue
            ok, why = _check_cert(proof, N, f"{fam} a({n}) k = {k}",
                                  ("bls75-thm1", "bls75-thm5"))
            if not ok:
                return False, "CERTIFICATE FAIL: " + why
            subbed += len(proof.get("subproofs", {}))
        routes = sorted({p["proof"] for p in certs.values()})
        parts.append(f"{fam} a({n})'s {len(certs)} values ({'/'.join(routes)}, "
                     f"{subbed} subproofs of the run's own earlier values)")
    # AT THE CEILING: x = 2310 * p with p a prime past the deterministic
    # bound whose p - 1 is smooth (so p itself is proved by Theorem 1 one
    # level down), and Phi_2(x) = x + 1, Phi_3(x), Phi_4(x) prime
    base = 2 ** 56 * 3 ** 28                   # 1.65e30: past the bound, smooth
    found = None
    for c in range(1, 2000000):
        p = base * c + 1
        x = 2310 * p
        if x >= ceiling.K_CEIL:
            break
        if not sprp_base2(p):
            continue
        if isprime(p) and isprime(x + 1):
            found = (x, p)
            break
    if found is None:
        return False, "CERTIFICATE FAIL: no x of the ceiling drill's shape"
    x, p = found
    fx = term_factors(x)
    if p not in fx or p < MR_VALID_BELOW:
        return False, "CERTIFICATE FAIL: the ceiling drill's term lacks its big prime"
    N = x + 1
    sub = certificate.prove(p)
    if sub is None or not certificate.verify(sub)[0]:
        return False, "CERTIFICATE FAIL: the smooth prime past the bound was not proved"
    proof = certify_value(N, fx, {p: sub})
    ok, why = _check_cert(proof, N, f"Phi_2 at x = {x:.4g}", ("bls75-thm1",))
    if not ok:
        return False, "CERTIFICATE FAIL (at the ceiling): " + why
    if not proof.get("subproofs"):
        return False, "CERTIFICATE FAIL: the ceiling certificate carries no subproof"
    if certificate.verify({a_: b_ for a_, b_ in proof.items()
                           if a_ != "subproofs"})[0]:
        return False, "CERTIFICATE FAIL: a proof stripped of its subproof verified"
    parts.append(f"Phi_2 at {TERM('A070737')} = {x:.4g} ({len(str(N))} digits) by "
                 f"Theorem 1 with a subproof for the {len(str(p))}-digit prime "
                 f"factor of {TERM('A070737')}, which cannot be stripped")
    # and the other two routes of a run at that height, where they land
    routes_at = []
    for k in (4, 3):
        Nk = ref.value(k, x)
        if not isprime(Nk):
            continue
        certs_k, unp = certify_run(x, 1, "A070737", 1)   # x - 1 alone: warm
        fac = {}
        for kind_, j, e in minus_one_shape(k):
            if kind_ == "x":
                for q_, ee in fx.items():
                    fac[q_] = fac.get(q_, 0) + ee * e
            elif kind_ == "phi":
                v = ref.value(j, x)
                for q_, ee in certificate.factor_full(v).items():
                    fac[int(q_)] = fac.get(int(q_), 0) + int(ee) * e
        pr = certify_value(Nk, fac, {p: sub})
        if pr is not None:
            routes_at.append(f"Phi_{k} {pr['proof']}")
    parts.append(f"{time.time() - t0:.1f} s in all" + (f"; also {', '.join(routes_at)}" if routes_at else ""))
    return True, "certificates ok: " + "; ".join(parts)


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly, across the seams
    a real interrupt leaves: a period boundary, the (j, u) sub-period
    cursor, and the clipped first period -- on both families' engine
    shapes in class space, the Fermat stage on and off."""
    total = 0
    for lab, fam, n, kw, x_at, span, cut in (
            ("one-level", "A070737", 9, dict(p1=17, p2=None, p3=None, q2=512, unit=210),
             10 ** 13, 300, 117),
            ("two-level", "A070737", 11, dict(p1=19, p2=31, p3=None, q2=8192,
                                              unit=2310, pb=32),
             10 ** 16, 3, 1),
            ("three-level", "A072942", 60, dict(p1=19, p2=29, p3=37, q2=1024,
                                                unit=56786730, pb=32),
             10 ** 18, 100, 37),
            ("Fermat stage", "A070737", 9, dict(p1=13, p2=23, p3=None,
                                                q2=2048, pb=32, prp=1, unit=210),
             10 ** 13, 60, 23)):
        eng = gpu.GpuEngine(n, fam, **kw)
        j0 = eng.j_of(x_at)
        whole = eng.survivors_j(j0, j0 + span)
        split = (eng.survivors_j(j0, j0 + cut)
                 + eng.survivors_j(j0 + cut, j0 + span))
        if not whole:
            return False, f"RESUME FAIL: {lab} window is empty -- vacuous"
        if sorted(whole) != sorted(split):
            return False, (f"RESUME FAIL: {lab}: {len(whole)} whole vs "
                           f"{len(split)} split")
        total += len(whole)
    # THE (j, u) SEAM, in the segment that starts at the clipped first
    # period and in an ordinary one, both families
    for eng, j0s in ((gpu.GpuEngine(11, "A070737", p1=19, p2=29, p3=37, q2=1024,
                                    nu=4, pb=32, unit=2310),
                      ((lambda e: e.j_of(9 * 10 ** 15), None), (lambda e: 0, 10 ** 6))),
                     (gpu.GpuEngine(60, "A072942", p1=19, p2=29, p3=41, q2=1024,
                                    nu=8, unit=56786730, pb=32),
                      ((lambda e: e.j_of(10 ** 18), None),
                       (lambda e: 0, 10 ** 6)))):
        nl = eng.launches_per_segment
        if nl < 4:
            return False, "RESUME FAIL: the seam engine has no sub-segment cursor"
        seg = eng.seg_periods
        for jf, k_min in j0s:
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
                  f"three-level wheels in the classes 0 (mod 210), 0 (mod "
                  f"2310) and 0 (mod 56,786,730), and with the Fermat stage "
                  f"on; across the (j, u) sub-segment seam on A070737 n = 11 "
                  f"and A072942 n = 60, and inside the clipped first segment "
                  f"on both ({total} survivors across the seams)")


def _classification_drill():
    """The base-2 screen reads the same runs as the all-bases chain on real
    survivors, the pool's chunked answer == the serial one, and every
    frontier term reads its true run through the pool's own form lists."""
    fam, n = "A070737", 7
    eng = gpu.GpuEngine(n, fam, p1=13, p2=23, p3=None, q2=2048, unit=210)
    j0 = eng.j_of(10 ** 9)
    surv = eng.survivors_j(j0, j0 + 4)
    if len(surv) < 3 * CHUNK:
        return False, f"CLASSIFY FAIL: only {len(surv)} survivors"
    forms = filter_forms(fam, n)
    two = [sprp_run(k, forms) for k in surv]
    ceng = cpu.CpuEngine(n, fam, q2=64)
    full = [ceng.run_length(k, read_n=read_index(fam, n)) for k in surv]
    if two != full:
        i = next(i for i in range(len(surv)) if two[i] != full[i])
        return False, (f"CLASSIFY FAIL: the base-2 screen read run {two[i]} "
                       f"and the all-bases chain {full[i]} at x = {surv[i]}")
    with _pool_factory(2) as pool:
        parts = _submit(pool, forms, surv)
        got = [r for ks, f in parts for r in f.result()]
    if got != full:
        return False, "CLASSIFY FAIL: the pool's chunked result differs"
    for f, n_, want in (("A070737", 10, 10), ("A070737", 3, 4), ("A070737", 6, 6),
                        ("A072942", 36, 9), ("A072942", 70, 8), ("A072942", 47, 2)):
        x = ref.KNOWN[f][n_]
        if sprp_run(x, filter_forms(f, n_)) != want:
            return False, f"CLASSIFY FAIL: {f} a({n_}) through the pool's forms"
    if (sprp_run(62, filter_forms("A072942", 15)) != 4
            or sprp_run(61, filter_forms("A072942", 15)) != 0
            or sprp_run(150, filter_forms("A070737", 4)) != 4):
        return False, "CLASSIFY FAIL: a small case through the pool's forms"
    return True, (f"classification ok: the base-2 screen == the all-bases "
                  f"chain on {len(surv)} real survivors (max run "
                  f"{max(full)}), {len(parts)} pool chunks reassemble to the "
                  f"serial answer, every frontier term reads its true run "
                  f"through the pool's own form lists (A070737 a(3) = 6 reads "
                  f"4, A072942 a(36) reads 9 and a(47) = 62 reads 2), and "
                  f"150 reads 4 on A070737 and 62 reads 4 on A072942's n = 15")


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
             workers=1, worker_ramp=WORKER_RAMP_S, start_n=None, stop_n=None,
             index=None)
    d.update(over)
    for k, v in d.items():
        setattr(a, k, v)
    return a


# The index the drill campaigns OPEN at, per family: on A070737 a(DRILL_N)
# and a(DRILL_N + 1) are published and a few seconds of device apart, and
# the run is BOUNDED before the filter of DRILL_N + 2 (`stop_n`), so no
# drill ever sweeps an open index (CLAUDE.md 0a): a(7) = 2,981,997,480 from
# a(6) = 6,770,610, then a(8) = 339,126,523,890.  On A072942 the drill
# hunts ONE published index from x = 3 and closes it: a(24) =
# 1,035,844,571,580 (eight divisors), then a second drill a(30).
DRILL_N = {"A070737": 7, "A072942": 24}
DRILL_N2 = {"A072942": 30}


def _promotion_drill():
    """A FIND MOVES THE FILTER and CARRIES THE LINE on A070737: the sweep
    resumes at the old boundary, floored into the new period with the clip
    at the boundary; and CLOSES THE INDEX on A072942.  On scratch files,
    with the REAL published term as the find."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="cyclo-promote-")
    path = str(pathlib.Path(tmp) / "c.json")
    rows = []
    fam = "A070737"
    n0 = DRILL_N[fam]
    found_x = ref.KNOWN[fam][n0]
    pol = policy(fam).at(path)
    c = Campaign(_args_for(fam, start_n=n0), ckpt=path, cursor=pol)
    before = (c.eng.n, c.eng.unit, c.eng.W, c.eng.q2,
              (c.eng.p1, c.eng.p2, c.eng.p3), c.eng.nforms, c.eng.r0)
    if c.filter_n() != n0 or c.j != c.floor_period() or \
            c.x_start() != x_floor(fam, n0, ref.KNOWN[fam][n0 - 1]):
        return False, f"PROMOTION FAIL: {fam} drill campaign did not open at index {n0}"
    c.found[str(n0)] = int(found_x)      # what record_discovery does
    c.state()
    c.status_line()
    if not c.save_boundary():
        return False, f"PROMOTION FAIL: {fam}'s in-window save did not land"
    try:
        w = Campaign(_args_for(fam, start_n=n0), ckpt=path,
                     cursor=policy(fam).at(path))
    except ValueError as e:
        return False, f"PROMOTION FAIL: {fam}: the in-window checkpoint refused: {e}"
    if w.filter_n() != n0 or w.found or w.j != c.j:
        return False, f"PROMOTION FAIL: {fam}: the in-window checkpoint reopened wrong"
    # the old filter swept five segments past the find's own segment
    c.boundary = found_x // c.eng.W + 5 * c.eng.seg_periods
    swept_old = c.boundary * c.eng.W
    c.follow_frontier(swept_old)
    if c.eng.n != n0 + 1 or c.eng.nforms != before[5] + 1:
        return False, f"PROMOTION FAIL: {fam} did not move to n = {n0 + 1}"
    cpu.assert_unit(n0 + 1, fam, c.eng.unit)
    if c.eng.r0 != cpu.unit_residue(n0 + 1, fam, c.eng.unit):
        return False, f"PROMOTION FAIL: {fam}'s class did not follow the filter"
    if c.cover_x != swept_old or c.x_start() != swept_old:
        return False, (f"PROMOTION FAIL: {fam} did not carry the line to "
                       f"{swept_old} (cover {c.cover_x}, start {c.x_start()})")
    if c.k_min() != swept_old or c.j != swept_old // c.eng.W:
        return False, (f"PROMOTION FAIL: {fam} resumed at period {c.j}, "
                       f"clip {c.k_min()}; expected the period holding "
                       f"{swept_old} with the clip there")
    if c.u != 0 or c.boundary != c.j or c.pending:
        return False, f"PROMOTION FAIL: {fam}'s cursor after the promotion"
    if any(p_.startswith(f"a({n0})") for p_ in c.passed):
        return False, f"PROMOTION FAIL: {fam} kept a retired rung"
    if not c.save():
        return False, f"PROMOTION FAIL: {fam}'s post-promotion save did not land"
    c2 = Campaign(_args_for(fam, start_n=n0), ckpt=path,
                  cursor=policy(fam).at(path))
    if (c2.filter_n(), c2.j, c2.u, c2.cover_x, c2.zone_n) != \
            (n0 + 1, c.j, 0, c.cover_x, c.zone_n):
        return False, f"PROMOTION FAIL: {fam} reloaded differently"
    import json as _json
    with open(path) as fh:
        st = _json.load(fh)
    st["n"] = n0
    checkpoint.save(path, st)
    try:
        Campaign(_args_for(fam, start_n=n0), ckpt=path,
                 cursor=policy(fam).at(path))
        return False, f"PROMOTION FAIL: {fam} read a cursor stored at the wrong index"
    except ValueError:
        pass
    for ext in ("", ".bak"):
        if os.path.exists(path + ext):
            os.remove(path + ext)
    rows.append(f"{fam} n = {n0} -> {n0 + 1}: wheel {before[4]} -> "
                f"({c.eng.p1},{c.eng.p2},{c.eng.p3}), period {before[2]:.3g} "
                f"-> {c.eng.W:.3g}, carried to the old boundary {swept_old:.4g}")
    # A072942: a find CLOSES the index
    fam = "A072942"
    n0 = DRILL_N[fam]
    pol = policy(fam, n0).at(path)
    c = Campaign(_args_for(fam, start_n=n0), ckpt=path, cursor=pol)
    if c.index != n0 or c.filter_n() != n0 or c.x_start() != ref.X_MIN or \
            c.frontier() != ref.nforms(fam, n0) - 1:
        return False, f"PROMOTION FAIL: {fam} drill campaign did not open at index {n0}"
    c.found[str(n0)] = int(ref.KNOWN[fam][n0])
    c.follow_frontier(c.boundary * c.eng.W)
    if not c.closed or c.pending:
        return False, f"PROMOTION FAIL: {fam}'s find did not close the index"
    if not c.save():
        return False, f"PROMOTION FAIL: {fam}'s post-close save did not land"
    c2 = Campaign(_args_for(fam, start_n=n0), ckpt=path, cursor=pol)
    if not c2.closed or c2.found != c.found or c2.run() != 0:
        return False, f"PROMOTION FAIL: {fam}'s closed index did not reload closed"
    if next_target(fam, {60}) != [n for n in ref.TARGETS if n != 60][0] or \
            next_target(fam, set(ref.TARGETS)) is not None or \
            next_target(fam, set()) != ref.TARGETS[0]:
        return False, "PROMOTION FAIL: next_target does not walk TARGETS"
    for ext in ("", ".bak"):
        if os.path.exists(path + ext):
            os.remove(path + ext)
    rows.append(f"{fam} n = {n0}: the find closes the index, the closed "
                f"checkpoint reloads closed and runs nothing, and next_target "
                f"walks TARGETS {ref.TARGETS}")
    return True, ("promotion ok: " + "; ".join(rows) + " -- on A070737 the "
                  "engine is rebuilt with one more condition, an interrupt "
                  "between the find and the promotion writes a checkpoint "
                  "that still opens, the classified line is carried to the "
                  "old boundary, the cursor round-trips, and a cursor stored "
                  "at the wrong index is REFUSED")


def _other_cursors_drill():
    """Every cursor policy -- A070737's and one per A072942 target -- reads
    all its declared keys through both readers and refuses a foreign one."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="cyclo-cursor-")
    path = str(pathlib.Path(tmp) / "c.json")
    seen = 0
    try:
        for fam, idx in [("A070737", None)] + [("A072942", n) for n in ref.TARGETS]:
            pol = policy(fam, idx).at(path)
            for key in pol.readable():
                checkpoint.save(path, {"key": key, "j": 7, "u": 0, "k": 11})
                st, kind = pol.load()
                if not st or kind is None:
                    return False, f"CURSOR FAIL: {fam} {idx} will not read {key}"
                pol.refuse_mismatch()
                seen += 1
            checkpoint.save(path, {"key": "not-a-real-key", "j": 7, "k": 11})
            st, _k = pol.load()
            if st:
                return False, f"CURSOR FAIL: {fam} {idx} read a foreign key"
            try:
                pol.refuse_mismatch()
                return False, f"CURSOR FAIL: {fam} {idx} did not refuse a foreign key"
            except checkpoint.CursorRefused:
                pass
            # an A072942 policy must refuse another index's cursor
            if idx is not None:
                checkpoint.save(path, {"key": config_key(fam, ref.TARGETS[-1] if idx != ref.TARGETS[-1] else ref.TARGETS[0]), "j": 7, "k": 11})
                try:
                    pol.refuse_mismatch()
                    return False, f"CURSOR FAIL: index {idx} read another index's cursor"
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
    return True, (f"cursor policies ok: all {seen} declared keys of A070737's "
                  f"policy and of the {len(ref.TARGETS)} A072942 index policies "
                  f"pass BOTH readers; a foreign key and another index's key "
                  f"refuse")


_WANT_UNIT = {("A070737", 11): 2310, ("A070737", 12): 30030, ("A070737", 13): 30030,
              ("A072942", 60): 56786730, ("A072942", 96): 4501770,
              ("A072942", 48): 46410}


def _adopt_drill():
    """A cursor written under an older PLAN at an index whose wheel moved
    is ADOPTED, not read: the swept boundary re-denominated onto the live
    wheel's periods with flooring (no gap), the work cursor dropped, the
    counts carried -- and a cursor still under one period adopts to period
    0.  Run at A072942 n = 60 (a moved index: the live cursor there was
    the case) on a synthetic p2 cursor in a temporary file; nothing is
    swept (CLAUDE.md 0a): the campaign is built and inspected only."""
    import tempfile
    fam, n = "A072942", 60
    if not plan_moved(fam, n):
        return False, f"ADOPT FAIL: {fam} n = {n} is not a moved index any more"
    tmp = tempfile.mkdtemp(prefix="cyclo-adopt-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = policy(fam, n).at(path)
    old_key = config_key(fam, n, plan=PREVIOUS_PLANS[0])
    if old_key not in pol.adopt or old_key in pol.accept:
        return False, f"ADOPT FAIL: the p2 key at n = {n} is not in `adopt` alone"
    # the p2 wheel of n = 60, as planner p2 ran it (OPTIMIZATION_LOG.md
    # round 1's 5g table), and a cursor one segment past it with a partial
    # second segment -- the live cursor's shape on 2026-10-24
    unit = cpu.forced_unit(n, fam)
    W_old = unit
    for q in (17, 19, 23, 29, 37, 41, 43, 71, 73):
        W_old *= q
    k_old = 256 * W_old
    base = {"key": old_key, "engine": ENGINE_VERSION, "plan": PREVIOUS_PLANS[0],
            "family": fam, "index": n, "n": n, "q2": 8192, "unit": unit,
            "W": W_old, "seg_periods": 256, "launches_per_segment": 26047,
            "k_start": ref.X_MIN, "start_x": ref.X_MIN, "cover_x": 0,
            "zone_n": n, "closed": False, "pending": [], "found": {},
            "census": {"6": 10, "7": 3}, "passed": ["a(60) Q1"],
            "elapsed": 1.5, "discoveries": 0, "near": 8, "survivors": 1000}
    try:
        for case, j, u, k in (("one segment closed, a partial second", 256, 6431, k_old),
                              ("under one period", 0, 5, ref.X_MIN)):
            checkpoint.save(path, dict(base, j=j, u=u, k=k))
            c = Campaign(_args_for(fam, index=n), ckpt=path, cursor=pol)
            W = int(c.eng.W)
            if W == W_old:
                return False, f"ADOPT FAIL: the live wheel at n = {n} has the p2 period"
            want_j = max(k // W, 0)
            if c._load_kind != "adopted" or c.j != want_j or c.u != 0 \
                    or c.boundary != want_j:
                return False, (f"ADOPT FAIL ({case}): loaded as {c._load_kind}, "
                               f"period {c.j} launch {c.u}, expected period "
                               f"{want_j} launch 0")
            if c.j * W > k or (k >= W and (c.j + 1) * W <= k):
                return False, (f"ADOPT FAIL ({case}): period {c.j} x W = {c.j * W} "
                               f"against a boundary swept to {k}")
            if c.swept_k() != max(c.j * W, c.x_start()):
                return False, f"ADOPT FAIL ({case}): swept_k {c.swept_k()} after adoption"
            if c.census != {6: 10, 7: 3} or c.near != 8 or c.survivors != 1000 \
                    or c.passed != ["a(60) Q1"] or c.elapsed != 1.5:
                return False, f"ADOPT FAIL ({case}): the counts were not carried"
            if not c.save():
                return False, f"ADOPT FAIL ({case}): the adopted cursor did not save"
            st, kind = pol.load()
            if kind != "own" or int(st["j"]) != want_j or int(st["u"]) != 0 \
                    or int(st["W"]) != W or int(st["k"]) != c.swept_k():
                return False, (f"ADOPT FAIL ({case}): the saved cursor reads back "
                               f"{kind}, period {st.get('j')}, W {st.get('W')}")
            c2 = Campaign(_args_for(fam, index=n), ckpt=path, cursor=pol)
            if c2._load_kind != "own" or c2.j != want_j or c2.u != 0:
                return False, f"ADOPT FAIL ({case}): the adopted cursor did not reload as its own"
            del c, c2
    finally:
        for f in pathlib.Path(tmp).glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass
    return True, (f"adopt drill ok: a p2 cursor at {fam} n = {n} (W = {W_old:,}) "
                  f"adopts onto the live wheel (W = {W:,}) as period k // W "
                  f"with launch 0 -- one segment closed plus a partial second "
                  f"becomes period {k_old // W}, {k_old - (k_old // W) * W:,} "
                  f"of line swept again, and a cursor under one period becomes "
                  f"period 0 -- the counts carried, the saved cursor its own "
                  f"key and reloaded as such")


def _families_stay_apart():
    """No two campaigns may read each other's cursor; the plan is admissible
    at every opening, in the forced class, with an expected sweep near the
    unavoidable one; and the benchmark shape at each opening names the
    campaign's own plan (rule 5g)."""
    import score as _score
    keys = [config_key("A070737")] + [config_key("A072942", n) for n in ref.TARGETS]
    paths = [ckpt_path("A070737")] + [ckpt_path("A072942", n) for n in ref.TARGETS]
    if len(set(keys)) != len(keys) or len(set(paths)) != len(paths):
        return False, "FAMILY FAIL: two campaigns share a key or checkpoint"
    if ledger_path("A070737") == ledger_path("A072942"):
        return False, "FAMILY FAIL: the families share a ledger"
    tight = []
    for fam, n in gpu.openings("A070737") + gpu.openings("A072942"):
        unit, p1, p2, p3, q2, pb = plan_for(fam, n)
        cpu.assert_unit(n, fam, unit)
        if (fam, n) in _WANT_UNIT and unit != _WANT_UNIT[(fam, n)]:
            return False, (f"FAMILY FAIL: {fam} n = {n}: the forced unit is "
                           f"{unit}, not {_WANT_UNIT[(fam, n)]}")
        W = unit
        for q in gpu._wheel_primes(p1, p2, p3):
            W *= q
        _wide, pv = gpu._record_for(W // unit, q2, pb)
        floor_k = model.plan_floor(fam, n)
        ideal = model.expected_sweep(fam, n, floor_k, floor_k, 1.0)
        swept = model.expected_sweep(fam, n, floor_k, (floor_k // W) * W, pv * W)
        if swept > PLAN_WASTE_MAX * ideal:
            return False, (f"FAMILY FAIL: {fam} n = {n} plans a segment of "
                           f"{pv} periods x {W:.4g}, whose expected sweep "
                           f"to a confirmed find is {swept / ideal:.2f}x "
                           f"the unavoidable one")
        tight.append((ideal / swept, fam, n))
    lv = lambda z: tuple(z or ())               # noqa: E731
    seen = set()
    labels = set()
    past = []
    for row in _score.resolved_shapes():
        (label, f, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, _nu, pb) = row[:15]
        labels.add(label)
        if label.startswith("SCORE1") or label.startswith("SCORE2") or label == "SCORE6":
            continue
        if label in _score.PAST_PLAN_SHAPES:
            # a past plan's wheel, kept for its fingerprint (round 2): it
            # must NOT be the plan, and its live counterpart must exist
            past.append(label)
            if (lv(p1), lv(p2), lv(p3)) == tuple(lv(z) for z in plan_for(f, n)[1:4]):
                return False, (f"FAMILY FAIL: benchmark shape {label} is listed "
                               f"as a PAST plan's wheel but names the live plan "
                               f"at {f} n = {n}: drop it or rename it")
            continue
        want = plan_for(f, n)
        got = (unit, lv(p1), lv(p2), lv(p3), q2, pb)
        if got != (want[0], lv(want[1]), lv(want[2]), lv(want[3]), want[4], want[5]):
            return False, (f"FAMILY FAIL: benchmark shape {label} names {got} "
                           f"and the campaign plans {want} at {f} n = {n}: "
                           f"re-freeze the shape at the plan (and log it)")
        seen.add((f, n))
    if ("A070737", open_n("A070737")) not in seen or ("A072942", 60) not in seen:
        return False, f"FAMILY FAIL: no benchmark shape at an opening ({sorted(seen)})"
    for label in past:
        if _score.PAST_PLAN_SHAPES[label] not in labels:
            return False, (f"FAMILY FAIL: the past-plan shape {label} has no live "
                           f"shape {_score.PAST_PLAN_SHAPES[label]} beside it")
    tight.sort()
    return True, ("families stay apart: %d distinct config keys and "
                  "checkpoint files (one per A072942 index), two ledgers, "
                  "the plan is admissible at every opening in the forced "
                  "classes (2310 / 30030 on A070737; 46,410 to 56,786,730 "
                  "on A072942), every plan's expected sweep to a CONFIRMED "
                  "find stays near the unavoidable one (the worst is %s "
                  "n = %d at %.2fx, against a %gx bound), and the benchmark "
                  "shapes at the openings name exactly the configuration "
                  "the campaign plans there"
                  % (len(keys), tight[0][1], tight[0][2], 1 / tight[0][0],
                     PLAN_WASTE_MAX))


def _campaign_wiring_drill(fam):
    """Build a campaign and exercise everything the loop touches, without
    sweeping a whole period."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="cyclo-drill-")
    path = str(pathlib.Path(tmp) / "c.json")
    n0 = open_n(fam)
    pol = policy(fam, n0 if per_index(fam) else None).at(path)
    a = _args_for(fam)
    try:
        c = Campaign(a, ckpt=path, cursor=pol)
        if c.filter_n() != n0:
            return False, f"WIRING FAIL: filter {c.filter_n()}, expected {n0}"
        floor = c.x_start()
        want_floor = (ref.X_MIN if per_index(fam)
                      else x_floor(fam, n0, ref.KNOWN[fam][n0 - 1]))
        if floor != want_floor or (c.j, c.u) != (c.floor_period(), 0):
            return False, (f"WIRING FAIL: a fresh campaign starts at {floor} "
                           f"(j, u) = ({c.j}, {c.u}); expected {want_floor}")
        if c.k_min() != max(floor, cpu.k_floor(c.eng.q2, n0, fam) + 1):
            return False, f"WIRING FAIL: the clip is {c.k_min()}"
        unit, p1, p2, p3, q2, pb = plan_for(fam, n0)
        if (c.eng.n, c.eng.fam, c.eng.unit, c.eng.q2, c.eng.pv) != (n0, fam, unit, q2, pb) \
                or (c.eng.p1, c.eng.p2, c.eng.p3) != (p1, p2, p3) \
                or c.eng.prp != CENSUS_FLOOR:
            return False, "WIRING FAIL: the engine is not the PLANNED one"
        line = c.status_line()
        for want in ("swept to", fam, "census", f"periods [{c.floor_period()},"):
            if want not in line:
                return False, f"WIRING FAIL: status line lacks {want!r}"
        # a run AT the floor is census on both families (A072942's eight-
        # divisor indices have frontier 7, so one above the floor is NEAR)
        if c.handle(floor + 1, CENSUS_FLOOR) is not False or \
                c.census.get(CENSUS_FLOOR) != 1:
            return False, "WIRING FAIL: a census run was not counted"
        if c.handle(floor + 3, CENSUS_FLOOR - 1) is not False or \
                CENSUS_FLOOR - 1 in c.census:
            return False, "WIRING FAIL: a run under the floor was counted"
        if per_index(fam):
            if c.zone() is None or c.zone()[0] != ref.X_MIN:
                return False, f"WIRING FAIL: {fam} has no zone from x = 3 ({c.zone()})"
            if c.cover_zone() or c.zone_n != n0 or c.cover_zone():
                return False, "WIRING FAIL: the zone cover is not once per index"
        else:
            if c.zone() is not None:
                return False, f"WIRING FAIL: {fam} has a zone {c.zone()} at its frontier"
            if c.cover_zone() or c.zone_n != n0 or c.cover_zone():
                return False, "WIRING FAIL: the zone cover is not once per filter"
        jf = c.floor_period()
        fr = c.frontier()
        if fr - 1 < CENSUS_FLOOR:
            return False, f"WIRING FAIL: the drain drill needs a census run under {fr}"
        cen0 = c.census.get(fr - 1, 0)
        inflight = collections.deque()
        inflight.append(((jf, 52), [([5, 6, 7, 8], _Done([3, fr - 1, fr, fr + 1]))]))
        inflight.append(((jf, 104), [([9], _Done([0]))]))
        c._drain(inflight, block=True)
        if c.pending != [(7, fr), (8, fr + 1)] or (c.j, c.u) != (jf, 104) \
                or c.census.get(fr - 1, 0) != cen0 + 1 or 3 in c.census:
            return False, (f"WIRING FAIL: the drain left {c.pending}, "
                           f"({c.j}, {c.u}), census {c.census} (a census run "
                           f"is COUNTED at the drain, a NEAR or a find held)")
        c.pending = []
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
        if (m["launches"] < 1 or m["rate"] <= 0
                or not 0 <= m["cost"] < 0.05 or m["need"] < 0):
            return False, f"WIRING FAIL: the sizing measurement is {m}"
        if (c.j, c.u, c.survivors, list(c.pending), dict(c.census)) != before:
            return False, "WIRING FAIL: the calibration moved the campaign"
        w = c.size_pool()
        ms = c._sizing
        if (ms is None or w != max(1, math.ceil(ms["need"] * POOL_MARGIN))
                or c.workers != w or c.pool is None):
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
        s0 = c.survivors
        inflight = collections.deque()
        for i in range(BACKLOG_LAUNCHES + 5):
            inflight.append(((jf, 200 + i), [([11 + i], _Slow([3]))]))
        c._drain(inflight, block=False)
        if len(inflight) != BACKLOG_LAUNCHES + 5:
            return False, "WIRING FAIL: the drain took launches not yet classified"
        c._backpressure(inflight)
        if (len(inflight) != BACKLOG_LAUNCHES or c._hostwait <= 0
                or not c._hostbound_logged or c.survivors != s0 + 5
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
        if not per_index(fam):
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
        if (d.j, d.u, d.pending, d.census, d.survivors, d.zone_n, d.index) != (
                c.j, c.u, c.pending, c.census, c.survivors, c.zone_n, c.index):
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
                  f"AT its floor ({TERM(fam)} = {floor:,}, inclusive) "
                  f"with the PLANNED engine at n = {n0}, unit {unit}, wheel "
                  f"({p1},{p2},{p3}), depth {q2} and the Fermat stage on "
                  f"{CENSUS_FLOOR} forms; its status line and rung ladder aim "
                  f"at a({n0}), 75 ladder reads at a standing frontier cost "
                  f"0 model rebuilds" + ("" if per_index(fam) else " while a find costs exactly 1")
                  + f", the pool is sized from a live measurement ({ms['per_s']:,.0f} "
                  f"values/s x {1e6 * ms['cost']:.0f} us), back-pressure "
                  f"times the wait, the drain keeps the work cursor behind "
                  f"the classified launches, and the checkpoint round trips "
                  f"through both the normal save and the interrupt snapshot")


def _rediscovery_run_drill(fam):
    """THE REAL LOOP, END TO END, ON PUBLISHED GROUND: `Campaign.run` itself,
    on scratch files.  A070737: opened at DRILL_N and bounded before
    DRILL_N + 2, it finds a(7) and a(8), carries the line between them, and
    stops.  A072942: opened at the published index DRILL_N, it finds a(24)
    from x = 3 and closes the index; then a(30)."""
    import json as _json
    import tempfile
    tmp = tempfile.mkdtemp(prefix="cyclo-rerun-")
    path = str(pathlib.Path(tmp) / "c.json")
    evid = str(pathlib.Path(tmp) / "evidence")
    n0 = DRILL_N[fam]
    if per_index(fam):
        want = {}
        rows = []
        for idx in (n0, DRILL_N2[fam]):
            want = {str(idx): ref.KNOWN[fam][idx]}
            p_ = str(pathlib.Path(tmp) / f"c{idx}.json")
            args = _args_for(fam, start_n=idx, to=ref.KNOWN[fam][idx] + 10 ** 7,
                             heartbeat=3600.0)
            c = Campaign(args, ckpt=p_, cursor=policy(fam, idx).at(p_), evid=evid)
            rc = c.run()
            found = {k: int(v) for k, v in c.found.items()}
            if rc != 0 or found != want or not c.closed or c.discoveries != 1:
                return False, (f"RERUN FAIL: {fam} index {idx} found {c.found} "
                               f"(closed {c.closed}), published {want}")
            x = want[str(idx)]
            f = pathlib.Path(evid) / evidence_name(fam, idx, x)
            if not f.exists():
                return False, f"RERUN FAIL: no evidence file for a({idx})"
            with open(f) as fh:
                ev = _json.load(fh)
            ok, msg = evidence.check_names(ev, TERM(fam))
            if not ok:
                return False, f"RERUN FAIL: a({idx})'s evidence: {msg}"
            if ev["oeis_terms"] != {str(idx): x} or ev["settles"] != [idx] or ev["filter_n"] != idx:
                return False, f"RERUN FAIL: a({idx})'s evidence files it under {ev['oeis_terms']}"
            vals = ref.values(fam, x, idx)
            if ev["unproved"] or len(ev["values"]) != ref.nforms(fam, idx) \
                    or [int(v) for v in ev["values"].values()] != vals \
                    or ev["least_claim"]["swept_from"] != ref.X_MIN \
                    or "none" not in ev["stopper"]:
                return False, f"RERUN FAIL: a({idx})'s evidence is not self-contained"
            prod = 1
            for p, e in ev[f"{TERM(fam)}_factored"].items():
                prod *= int(p) ** int(e)
            if prod != x:
                return False, f"RERUN FAIL: a({idx})'s factorization of the term is wrong"
            rows.append(f"a({idx}) = {x:,} ({c.survivors:,} values classified, "
                        f"census {dict(sorted(c.census.items()))})")
        ok, msg = evidence.gate_names(evid, TERM(fam))
        if not ok:
            return False, "RERUN FAIL: " + msg
        return True, (f"rediscovery run ok: Campaign.run, opened at A072942's "
                      f"published indices on scratch files, found "
                      + " and ".join(rows) + " from x = 3 and CLOSED each "
                      f"index; each evidence file is named and keyed by the "
                      f"OEIS index, carries the term's factorization, every "
                      f"value's certificate and no stopper, and passes the "
                      f"naming gate")
    want = {str(n): ref.KNOWN[fam][n] for n in (n0, n0 + 1)}
    if n0 + 2 > open_n(fam):
        return False, f"RERUN FAIL: {fam}'s drill would reach the open index"
    args = _args_for(fam, start_n=n0, stop_n=n0 + 2,
                     to=want[str(n0 + 1)] + 10 ** 7, heartbeat=3600.0)
    c = Campaign(args, ckpt=path, cursor=policy(fam).at(path), evid=evid)
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
        if ev["oeis_terms"] != {str(n): x} or ev["settles"] != [n] or ev["filter_n"] != n:
            return False, f"RERUN FAIL: a({n})'s evidence files it under {ev['oeis_terms']}"
        vals = ref.values(fam, x, n)
        if ev["unproved"] or len(ev["values"]) != n \
                or [int(v) for v in ev["values"].values()] != vals \
                or ev["least_claim"]["swept_from"] > x \
                or ev["stopper"].get("k") != n + 1:
            return False, f"RERUN FAIL: a({n})'s evidence is not self-contained"
        prod = 1
        for p, e in ev[f"{TERM(fam)}_factored"].items():
            prod *= int(p) ** int(e)
        if prod != x:
            return False, f"RERUN FAIL: a({n})'s factorization of the term is wrong"
        if ev["also_settles"] != [{"sequence": "A233512", "n": n, "x": x}]:
            return False, f"RERUN FAIL: a({n}) does not also settle A233512 a({n})"
    ok, msg = evidence.gate_names(evid, TERM(fam))
    if not ok:
        return False, "RERUN FAIL: " + msg
    return True, (f"rediscovery run ok: Campaign.run, opened at index {n0} of "
                  f"{fam} on scratch files, found a({n0}) = {want[str(n0)]:,}, "
                  f"carried the line, and found a({n0 + 1}) = "
                  f"{want[str(n0 + 1)]:,}, then stopped before the filter of "
                  f"a({n0 + 2}); each evidence file is named and keyed by the "
                  f"OEIS index, carries the term's factorization, every "
                  f"value's certificate, the stopper Phi_(n+1) with its factor "
                  f"and the A233512 rider, and passes the naming gate "
                  f"({c.survivors:,} values classified, census "
                  f"{dict(sorted(c.census.items()))})")


def _zone_drill():
    """The exception zone can hold terms, and the host finds them: A070737's
    a(1) = 3 to a(4) = 6 lie in [3, 4097] -- the host's walk at n = 4 finds
    6 first with run 4; and A072942's a(47) = 62 and a(15) = 62 lie in
    the zone of their indices -- the walk finds each first; both walks
    agree with the oracle's."""
    q2 = 4096
    hits = cpu.prefix_hits("A070737", 4, q2, floor=4)
    if not hits or hits[0][0] != 6 or hits[0][1] < 4:
        return False, f"ZONE FAIL: the zone at n = 4 reads {hits[:3]}"
    oh = ref.prefix_hits("A070737", 4, ref.X_MIN, cpu.k_floor(q2, 4, "A070737"), floor=4)
    if oh[0][0] != 6 or [(x, r) for x, r in oh] != hits:
        return False, "ZONE FAIL: the oracle's zone walk differs from the engine's"
    for n in (47, 15):
        h = cpu.prefix_hits("A072942", n, q2, floor=ref.nforms("A072942", n))
        if not h or h[0] != (62, ref.nforms("A072942", n)):
            return False, f"ZONE FAIL: the zone of A072942 n = {n} reads {h[:3]}"
    one = cpu.prefix_hits("A070737", 1, q2, floor=1)
    if not one or one[0][0] != 3:
        return False, f"ZONE FAIL: 3 is not first in the zone at n = 1: {one[:2]}"
    return True, (f"zone ok: A070737's a(4) = 6 (run 4) and a(1) = 3 lie in "
                  f"the exception zone [3, {q2 + 1}] and the host's walk finds "
                  f"them first, agreeing with the oracle's walk; A072942's "
                  f"a(47) = a(15) = 62 likewise")


def _rider_drill():
    """The derived entry's rule (also_settles; Codex CYL-005): a find
    settles A233512 at the FIRST index it settles, only above the previous
    term and only while the primary chain from a(5) is strictly increasing
    and known; a plateau settles no rider at its later indices, breaks the
    chain, and a gap in the known terms settles nothing."""
    fam = "A070737"
    K = dict(ref.KNOWN[fam])
    a10 = K[10]
    x = a10 + 30030
    # the published prefix, a find at n = 11: one rider, at 11
    got = also_settles(fam, x, 11, [11], K)
    if got != [{"sequence": "A233512", "n": 11, "x": x}]:
        return False, f"RIDER FAIL: a single settle gives {got}"
    # a find settling 11 AND 12 (a plateau): the rider at 11 alone
    got = also_settles(fam, x, 12, [11, 12], K)
    if got != [{"sequence": "A233512", "n": 11, "x": x}]:
        return False, f"RIDER FAIL: a plateau gives {got}, not the first index alone"
    # the next find after that plateau: B(12) is unknown, so no rider at 13
    K2 = {**K, 11: x, 12: x}
    got = also_settles(fam, x + 60060, 13, [13], K2)
    if got:
        return False, f"RIDER FAIL: a rider {got} after a plateau broke the chain"
    # a find EQUAL to the previous term (the ladder nests: a(3) = a(4)) is
    # not above B(n - 1)
    got = also_settles(fam, a10, 11, [11], K)
    if got:
        return False, f"RIDER FAIL: x = a(10) settles the rider {got}"
    # a gap in the known chain settles nothing
    K3 = {k: v for k, v in K.items() if k != 8}
    got = also_settles(fam, x, 11, [11], K3)
    if got:
        return False, f"RIDER FAIL: an unknown a(8) still gives {got}"
    # below the rider's first index nothing is derived
    got = also_settles(fam, 7, 4, [3, 4], K)
    if got:
        return False, f"RIDER FAIL: n = 3, 4 give {got}"
    # the published prefix itself: every a(n), n = 6..10, is a rider at n
    for m in range(6, 11):
        got = also_settles(fam, K[m], m, [m], K)
        if got != [{"sequence": "A233512", "n": m, "x": K[m]}]:
            return False, f"RIDER FAIL: the published a({m}) gives {got}"
    return True, ("rider drill ok: A233512 is settled at the first index a "
                  "find settles, above the previous term, while the chain "
                  "from a(5) is known and strictly increasing; a plateau "
                  "settles its first index alone and no rider after it, an "
                  "equal term or a gap settles none, and a(6)..a(10) each "
                  "settle their own index")


def _evidence_names_drill():
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        ev = dict(evidence.header(fam, ref.FAMILIES[fam]["forms"], TERM(fam),
                                  ref.KNOWN[fam][top], [top]), settles=[top])
        ok, msg = evidence.check_names(ev, TERM(fam))
        if not ok:
            return False, f"EVIDENCE NAMES FAIL: {fam} writer: {msg}"
    os.makedirs(EVID, exist_ok=True)
    return evidence.gate_names(EVID, lambda rec: TERM(rec["sequence"]))


def selftest(fam="A070737"):
    t0 = time.time()
    rows = []
    for g in (ref.GATES + cpu.GATES + gpu.GATES + model.GATES
              + certificate.GATES + ceiling.GATES):
        rows.append(g())
    rows.append(drills.event_kind_drill(
        lambda c: event_kind(*c), _event_cases()))
    for d in drills.standard(pool_factory=_pool_factory,
                             cursor=policy("A070737")):
        rows.append(d)
    rows.append(_other_cursors_drill())
    for d in (_ceiling_drill, _zone_drill, _canary_hunt, _protocol_drill,
              _certificate_drill, _resume_drill, _promotion_drill,
              _classification_drill, _stop_on_discovery_drill,
              _adopt_drill, _families_stay_apart):
        rows.append(d())
    for f in ref.FAMILIES:
        rows.append(_campaign_wiring_drill(f))
        rows.append(_rediscovery_run_drill(f))
    rows.append(_evidence_names_drill())
    rows.append(_rider_drill())
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

def _status(fam, index=None):
    fam = ref.family(fam)
    if per_index(fam) and index is None:
        rc = 0
        for n in ref.TARGETS:
            rc |= _status(fam, n)
        return rc
    pol = policy(fam, index)
    st, kind = pol.load(warn=lambda m: log("STAGE", m))
    if not st:
        log("STATUS", f"no checkpoint for {config_key(fam, index)} yet")
        return 0
    cen = {int(r): int(c) for r, c in st.get("census", {}).items()}
    if per_index(fam):
        front = ref.nforms(fam, index) - 1
        head = f"{fam} index n = {index}" + (" CLOSED" if st.get("closed") else "")
    else:
        front = max(ref.KNOWN[fam])
        for n in st.get("found", {}):
            front = max(front, int(n))
        head = f"{fam} filter n = {front + 1}"
    if kind == "adopted":
        # an older plan's cursor at a filter whose wheel moved: say what the
        # next start will do with it (Campaign.adopt_cursor), reading only
        n_live = index if per_index(fam) else front + 1
        unit, p1, p2, p3, _q2, _pb = plan_for(fam, n_live)
        Wn = unit
        for q in gpu._wheel_primes(p1, p2, p3):
            Wn *= q
        log("STATUS", f"  cursor from plan {st.get('plan', '?')} (W = "
                      f"{int(st.get('W', 0)):,}): the next start ADOPTS it "
                      f"onto this plan's W = {Wn:,} as period "
                      f"{int(st['k']) // Wn}, launch 0 (the old work cursor "
                      f"is dropped and the segment there is swept again)")
    log("STATUS", "  ".join([
        head,
        f"swept to {TERM(fam)} = {int(st['k']):,}",
        f"work cursor period {int(st['j'])} u = {int(st.get('u', 0))}",
        census_str(cen, CENSUS_FLOOR, front),
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
    ap.add_argument("--family", default="A070737",
                    help="which sequence to hunt: " +
                         ", ".join(ref.FAMILIES) + " (default A070737)")
    ap.add_argument("--index", type=int, default=None,
                    help="A072942 only: the one open index to hunt (default: "
                         "every open index in turn, cheapest first: "
                         + ", ".join(map(str, ref.TARGETS)) + ")")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint(s) and say where the hunt is")
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
                         "(1 ms against a launch of tens of ms costs a few "
                         "percent of the rate)")
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
    if args.index is not None and not per_index(args.family):
        ap.error("--index is for A072942, whose indices are separate lines")
    if args.selftest:
        return selftest(args.family)
    if args.status:
        return _status(args.family, args.index)
    if args.to:
        args.to = int(args.to)
    if not per_index(args.family):
        policy(args.family).refuse_mismatch(
            fresh=args.fresh,
            describe=lambda st: (f"period {st.get('j')}, u = {st.get('u')}, "
                                 f"swept to {TERM(args.family)} = {st.get('k')}"))
        if args.fresh:
            for p in (ckpt_path(args.family), ckpt_path(args.family) + ".bak"):
                if os.path.exists(p):
                    os.remove(p)
        return Campaign(args).run()
    # A072942: one index, or every open one in TARGETS order.  An index
    # named on the command line is THAT index alone: once it closes the
    # campaign stops (Codex CYL-006), where a run with no --index moves on
    # to the next open index of TARGETS.
    closed = set()
    explicit = args.index is not None
    while True:
        idx = args.index if args.index is not None else next_target(args.family, closed)
        if idx is None:
            log("STAGE", f"no open index of {args.family} is left in TARGETS "
                         f"{ref.TARGETS}: nothing to hunt")
            return 0
        args.index = idx
        policy(args.family, idx).refuse_mismatch(
            fresh=args.fresh,
            describe=lambda st: (f"index {st.get('index')}, period {st.get('j')}, "
                                 f"u = {st.get('u')}, swept to "
                                 f"{TERM(args.family)} = {st.get('k')}"))
        if args.fresh:
            for p in (ckpt_path(args.family, idx), ckpt_path(args.family, idx) + ".bak"):
                if os.path.exists(p):
                    os.remove(p)
        c = Campaign(args)
        rc = c.run()
        if rc or not c.closed or args.stop_on_discovery or args.to:
            return rc
        closed.add(idx)
        if explicit:
            log("STAGE", f"--index {idx} named this index alone; it is "
                         f"closed, so the campaign stops (the next open "
                         f"index of TARGETS is "
                         f"{next_target(args.family, closed)})")
            return rc
        args.index = None


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
