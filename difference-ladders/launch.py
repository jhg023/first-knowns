"""The campaign for the difference ladders -- A216666: the smallest integer b such that (b+1)^p - b^p is prime for all primes p <= prime(n); A216668: the smallest integer b > 1 such that for all primes p <= prime(n), (b+1)^p - b^p is prime if and only if 2^p-1 is prime; A229073 (riding A216666): the least m >= 2 such that m^p - (m - 1)^p is composite for p = prime(n) but no smaller prime p.

    python launch.py                       the hunt: A216666 (with A229073), indefinite, resumable
    python launch.py --family A216668      A216668
    python launch.py --status [--family F] where the cursor is; reads, never writes
    python launch.py --selftest            the full gate battery; must end ALL GREEN

TWO LADDERS, ONE ENGINE, ONE CAMPAIGN AT A TIME.  `--family` names the
entry (difference_reference.FAMILIES); `--family A229073` runs A216666's
campaign, which settles both.

  * Both are LADDERS: every condition of index n is one of index n + 1, so
    a(n+1) >= a(n), the sweep for a(n) starts AT a(n - 1) inclusive (a term
    whose run passes its index is the next term too), and a find PROMOTES
    the filter and CARRIES the line -- the classification reads runs to
    the filter plus RUN_AHEAD, so everything the old filter swept past a
    find was already classified against the next filter's conditions; the
    new filter resumes at the old segment's end, re-denominated by floor
    into its own period with the clip at the old boundary
    (_promotion_drill).  One checkpoint and one ledger per family.
  * A229073 RIDES A216666'S LINE.  Its a(r + 1) is the least m whose
    b = m - 1 has an A216666 run of EXACTLY r.  An A216666 find of run r is
    such a b, so it settles A229073 a(r + 1) when that is open -- but when
    the run passes the filter (r > n), A229073's a(n + 1)..a(r) still need
    b's of exact runs n..r - 1, which a filter above them would sieve away.
    So the campaign's filter is the LOWER of A216666's open index and
    A229073's lowest open exact run (`filter_n`): the line keeps being
    classified at n until the exact-n run appears, every value of run n or
    more is read on the way (A216666's next term included), and the filter
    climbs only when nothing below it is open (_rider_campaign_drill).
  * A216668 asks for a COMPOSITE value at every non-Mersenne exponent.
    Those conditions cannot be sieved (a small factor is what they want),
    so the engines sieve the Mersenne exponents' forms and the host reads
    the composite conditions for the rare survivor (sprp_run).

EVERY FORM IS KNOWN AT EVERY INDEX, so the campaign can be planned, priced
and benchmarked at every filter it will run, in advance (CLAUDE.md 5g):
`plan_for` is the one place a configuration is derived, score.py has a
shape at each family's opening and its day-long filter, and G18 compiles
every opening.  The openings (5g's test plan): A216666 n = 9 fresh and
resumed and the filters it promotes itself into, n = 10 and 11 (11 is the
day-long filter); A216668 n = 18 and every filter to its day-long n = 24
(a find at 18 settles 19-23 with near certainty: their conditions ask for
a composite).

THE DEVICE FERMAT STAGE (difference_gpu; power-ladders' own, kept).  A
prime kills about one residue per form on average, so millions of sieve
survivors a second leave the sieve; the device Fermat-tests their leading
sieved forms -- (b+1)^2 - b^2, (b+1)^3 - b^3, ... -- as many of them as
lie among the first CENSUS_FLOOR conditions, and only the values that pass
reach the host.  A failed Fermat test is a proof of compositeness, so
nothing with a run at the census floor or above is dropped; the host
re-reads every run.

THE RUN of b: the number of leading conditions (in the order of p) it
meets.  A run of r > the frontier is a DISCOVERY settling a(frontier + 1)
.. a(r) at once (and A229073 a(r + 1) when open); a run equal to an open
A229073 exact run is a DISCOVERY of that term alone; one short of the
filter is NEAR; CENSUS_FLOOR <= r below that is counted only.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine ceiling, huntlib's K_CEIL = 1e40 on the term, both families.
The proof crossing -- where classification stops being a proof -- is
where the largest sieved value of the filter passes 3.317e24 (b = 11 at
n = 9 of A216666): every campaign starts past it, and it is a [MILESTONE],
never a stop.  (b+1)^p - b^p - 1 = p * b * (b+1) * (b^2+b+1)^e * E(b), with
e = 2 when p == 1 (mod 6) and E of degree p - 3 - 2e, so the factored part
of N - 1 is all of it at p <= 7, over a third at p = 11, 13, 19 and under
a fifth from p = 23 on: a discovery's values are each proved by BLS75
Theorem 1 or 5 where that part reaches, and the rest are left UNPROVED in
the evidence for a general prover (APR-CL or ECPP; README "Trust").

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
candidates of a segment come out in wheel order, so nothing in a segment is
known to be the LEAST until it closes: 'swept to' is the term below which
every value has been tested; (period, launch) is the work cursor inside it.

THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER, at
start and at every promotion (CLAUDE.md 5f, 5g); back-pressure bounds the
device's lead over the host and the waited fraction is in every [STATUS].
Every per-value host step runs inside huntlib.hostcost.HostCost.item, so a
slow one is announced and the slowest is in [STATUS] (CLAUDE.md 5k).

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
from huntlib import hostcost                                    # noqa: E402
from huntlib import pool as _pool                               # noqa: E402
from huntlib import shutdown                                    # noqa: E402
from huntlib.gpu import device_report                           # noqa: E402
from huntlib.hlog import Heartbeat, banner, census_str, log     # noqa: E402
from huntlib.hostcost import HostCost                           # noqa: E402
from huntlib.primes import (MR_VALID_BELOW, factor_witness,     # noqa: E402
                            mr_is_prime, sprp_base2)
from huntlib.rungs import Ladder, LiveLadder, eta_str           # noqa: E402
from sympy import Poly, Symbol, factor_list, isprime            # noqa: E402

import difference_gpu as gpu                                    # noqa: E402
import difference_model as model                                # noqa: E402
import difference_reference as ref                              # noqa: E402
import difference_search as cpu                                 # noqa: E402

try:                                    # optional: 8x faster at 1,700 digits
    import gmpy2 as _gmpy2
except ImportError:                     # noqa: BLE001
    _gmpy2 = None

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")

# THE DERIVED ENTRY and the line it rides.
RIDER, RIDER_OF = "A229073", "A216666"


def TERM(fam):
    """The letter the OEIS name gives the term: b on both families, m on
    A229073 (rule 5i); every surface a person reads carries the integer
    under it."""
    return ref.letter(fam)


PLAN_VERSION = "p2"               # bump when plan_for's answer changes
#   p1 (2026-11-23): cyclotomic-ladders' planner p2 taken whole -- the wheel
#   and the window chosen together by expected clock to a confirmed find
#   (difference_gpu.plan) over every greedy wheel subset the kernel admits,
#   with the sieve depth a DEVICE decision (difference_gpu.PRP_Q2) and the
#   floor it prices from the index's own (a(n - 1), or the model's median
#   of it, with A216668's composite-asking indices not moving the chain).
#   p2 (2026-11-23, OPTIMIZATION_LOG.md round 1): the depth 8192 -> 32768
#   with the VALUE RULE's sieve set (difference_search.select_primes at
#   difference_gpu.SIEVE_TAU), which the window depth is planned over too.
#   The wheel and the window it plans are p1's at every campaign filter
#   (A216666 n = 9-11, A216668 n = 18-24), so a p1 cursor counts the
#   identical periods and is ACCEPTED (policy below).
PREVIOUS_PLANS = ("p1",)


@functools.lru_cache(maxsize=None)
def plan_for(fam, n):
    """(unit, p1, p2, p3, q2, pb) for filter n of family F -- the
    configuration the campaign runs there.  Pure and cached: a function of
    (family, n) alone, so a resumed campaign derives the identical plan and
    the launcher still asserts W and the segment on load (OPTIMIZATION.md
    2.9).  The unit is 1 at every filter: nothing is forced."""
    fam = ref.family(fam)
    unit = cpu.forced_unit(n, fam)
    p1, p2, p3, q2, pb = gpu.campaign_plan(n, fam, unit)
    return unit, p1, p2, p3, q2, pb


def x_floor(fam, n, frontier_x):
    """Where the sweep for a(n) starts: the frontier term ITSELF (the
    ladder nests, and the frontier term is a(n) too when its run reaches
    n)."""
    fam = ref.family(fam)
    return max(int(frontier_x), ref.b_min(fam))


def rider_known_top():
    """A229073's frontier in the literature and this project's finds."""
    return ref.frontier(RIDER)


def open_n(fam):
    """The filter a FRESH campaign of this family opens at: the frontier +
    1, held down on A216666 to A229073's lowest open exact run."""
    fam = ref.family(fam)
    n = ref.frontier(fam) + 1
    if fam == RIDER_OF:
        n = min(n, rider_known_top())
    return n


# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a segment.
CKPT_LAUNCHES = 32
# Runs shorter than this are not even counted -- and the device Fermat
# stage tests exactly the sieved forms among this many leading conditions
# (`prp_count`), so nothing at the floor or above is ever dropped before
# the host reads it.
CENSUS_FLOOR = 6
# How far past the filter the classification reads a run: a find of run r
# settles a(n)..a(r), and the line a filter swept is carried to the next
# filter only because every value on it was read this far past n.  A run
# that reaches the cap is re-read with no cap at verification.
RUN_AHEAD = 6
# WHAT A PLAN MAY WASTE: a plan whose expected sweep to a confirmed find
# exceeds the unavoidable one by more than this factor is a decision for a
# human (_families_stay_apart).
PLAN_WASTE_MAX = 1.5
# A host step this slow gets a [WARN] (CLAUDE.md 5k).
SLOW_HOST_S = 5.0

ENGINE_VERSION = "v2"
#   v1 (2026-11-23): cyclotomic-ladders' engine v2 -- power-ladders' window
#   sieve with the device Fermat stage, the window pattern of one period --
#   with the kill sets b == 1/(zeta - 1) for each primitive p-th root of
#   unity zeta, the Fermat stage's values (b+1)^p - b^p as two truncated
#   powers, the tail's residue list widened to 256, and no class (nothing
#   is forced).  Every constant inherited; the measurements of this project
#   are in OPTIMIZATION_LOG.md.
#   v2 (2026-11-23, OPTIMIZATION_LOG.md round 1): the sieve set chosen by
#   the value rule, its primes past 8192 tested in the tail through a
#   perfect-hash table; the Fermat stage on its own stream beside the next
#   launch's sieve, three launch buffers, squarings by a Montgomery square;
#   the in-block rounds' item loop not unrolled; TAIL_ROUND_DROP 0.8.  The
#   same wheel, window and segment as v1, so the same line: a v1 cursor is
#   ACCEPTED.  1.33x to 1.69x at the five campaign filters, paired.
PREVIOUS_ENGINES = ("v1",)
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


# HOW MANY FORMS THE DEVICE FERMAT STAGE TESTS, per family: MEASURED at the
# day-long filters and the openings (OPTIMIZATION_LOG.md round 0), paired
# and interleaved, the host's load priced beside the rate.  A216666: 5 (p =
# 2..11) -- 1.069x over 6 at n = 11, 1.045x at n = 10, 1.026x at n = 9, the
# host then testing f_13 on 1,300 / 5,100 / 17,000 values a second (0.2 to
# 0.5 core-s/s); 4 forms measured 1.12 / 1.08 / 1.07x but hands the host
# 43,000 to 350,000 values a second, five to ten cores, and is declined
# under the load budget (CLAUDE.md 5f).  A216668: 5 (p = 2, 3, 5, 7, 13),
# the most its census floor allows and the best measured: 4 is 0.945x at
# n = 18 (and 1.058x at n = 24 for 85,000 values a second), 6 is 0.949x.
# Never more than the sieved forms among the first CENSUS_FLOOR conditions
# (`prp_count`), so nothing at the census floor or above is dropped.
PRP_FORMS = {"A216666": 5, "A216668": 5}


def prp_count(fam, floor=None):
    """How many sieved forms the device Fermat stage tests: PRP_FORMS,
    never more than the sieved forms among the first CENSUS_FLOOR
    conditions (6 on A216666, p = 2..13; 5 on A216668, p = 2, 3, 5, 7, 13
    -- 11 asks for a composite), so that every value whose run reaches the
    census floor passes the stage."""
    floor = CENSUS_FLOOR if floor is None else int(floor)
    fam = ref.family(fam)
    return min(PRP_FORMS[fam], len(ref.forms(fam, floor)))


def config_key(fam, engine=None, plan=None):
    fam = ref.family(fam)
    return (f"{fam.lower()}-{engine or ENGINE_VERSION}-{plan or PLAN_VERSION}"
            f"-seg{CKPT_LAUNCHES}"
            f"-pbd{gpu.PB_DEFAULT}"
            f"-cpl{gpu.CAND_PER_LAUNCH4.bit_length() - 1}"
            f"w{gpu.CAND_PER_LAUNCH_WIDE.bit_length() - 1}"
            f"-f{CENSUS_FLOOR}-r{RUN_AHEAD}")


def ckpt_path(fam):
    return str(HERE / f"campaign_checkpoint_{ref.family(fam).lower()}.json")


def ledger_path(seq, evid=None):
    return str(pathlib.Path(evid or EVID) / f"{str(seq).lower()}_discoveries.json")


# EVERY reader of a checkpoint goes through one of these objects and none
# of them takes a key list of its own (CONVENTIONS.md "Reading an existing
# cursor").  One per family.
_POLICIES = {}


def policy(fam):
    fam = ref.family(fam)
    if fam not in _POLICIES:
        same = [config_key(fam, engine=e) for e in PREVIOUS_ENGINES]
        older = [config_key(fam, plan=p) for p in PREVIOUS_PLANS]
        # ... and a cursor from before BOTH moved (v1 with p1)
        both = [config_key(fam, engine=e, plan=p)
                for e in PREVIOUS_ENGINES for p in PREVIOUS_PLANS]
        _POLICIES[fam] = checkpoint.CursorPolicy(
            ckpt_path(fam), config_key(fam),
            accept=tuple(same + older + both), adopt=())
    return _POLICIES[fam]


# ------------------------------- the taxonomy -------------------------------

def event_kind(run, frontier, open_exact=(), filter_n=None):
    """DISCOVERY / NEAR / CENSUS / None -- the repo-wide rule, this
    project's mathematics.  `frontier` is the largest index settled; a run
    past it settles every index up to the run.  `open_exact` holds the runs
    r whose A229073 a(r + 1) is open (A216666's campaign only): the first b
    of such an exact run is a discovery of the rider even below the
    frontier.  NEAR is one short of the filter being swept (frontier + 1
    unless the rider holds it lower)."""
    run, frontier = int(run), int(frontier)
    if run > frontier or run in open_exact:
        return "DISCOVERY"
    fn = frontier + 1 if filter_n is None else int(filter_n)
    if run == fn - 1:
        return "NEAR"
    if run >= CENSUS_FLOOR:
        return "CENSUS"
    return None


def read_index(fam, n):
    """The index whose conditions the classification reads at filter n."""
    ref.family(fam)
    return int(n) + RUN_AHEAD


def condition(fam, p, want=None):
    """The condition at the prime p in the entry's own letters."""
    fam = ref.family(fam)
    t = TERM(fam)
    if want is None:
        want = dict(ref.conditions(fam, ref.READ_TOP)).get(int(p), True)
    if ref.FAMILIES[fam]["pattern"] == "all":
        return f"({t}+1)^{int(p)} - {t}^{int(p)} prime"
    if want:
        return f"({t}+1)^{int(p)} - {t}^{int(p)} prime (2^{int(p)}-1 is prime)"
    return f"({t}+1)^{int(p)} - {t}^{int(p)} composite (2^{int(p)}-1 is composite)"


def stopper_of(fam, x, run):
    """The condition after the run and why it stops it: its prime p, the
    value, and "composite" (a prime was asked) or "prime" (A216668 asked
    for a composite there)."""
    fam = ref.family(fam)
    conds = ref.conditions(fam, int(run) + 1)
    p, want = conds[int(run)]
    v = ref.value(p, int(x))
    return {"p": int(p), "value": int(v), "wants_prime": bool(want),
            "why": "composite" if want else "prime"}


def verify(x, run, fam, n=None, witness=True):
    """The three independent confirmations plus the bounding witness.

    1. huntlib's Miller-Rabin over every condition of the run -- each
       prime-asking value a strong probable prime past the proof crossing
       (then PROVED by certificate where its structure allows), each
       composite-asking value failing a base;
    2. sympy's BPSW, an independent implementation, which must agree on the
       run LENGTH, not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense line and uses no wheel at all, must
       agree that b survives a sieve at a DIFFERENT depth from the
       campaign's, at the filter the run reaches.

    plus a witness for the condition that STOPS the run, which is what
    bounds the claim to exactly `run`: a prime factor of the composite
    value where a prime was asked (A216666 always), or the value's
    primality where A216668 asked for a composite.  witness=False is the
    [NEAR] path: verified, not evidenced, no factoring.
    """
    fam = ref.family(fam)
    x, run = int(x), int(run)
    conds = ref.conditions(fam, max(run, 1))[:run]
    vals = [(p, want, ref.value(p, x)) for p, want in conds]
    sieved = [v for p, want, v in vals if want]
    q2 = min(4096, min(sieved) - 1) if sieved else 1
    legs = {"mr_chain": all(mr_is_prime(v) == want for p, want, v in vals),
            "sympy_bpsw": ref.run_length(fam, x, run + 1) == run,
            "resieve_other_wheel": (q2 < 2 or
                                    cpu.CpuEngine(max(run, 1), fam, q2=q2).survives(x))}
    stop = stopper_of(fam, x, run)
    if stop["why"] == "composite":
        legs["stopper_fails"] = not mr_is_prime(stop["value"])
    else:
        legs["stopper_fails"] = bool(isprime(stop["value"]))
    ok = all(legs.values())
    wit, fermat = None, None
    if stop["why"] == "composite" and legs["stopper_fails"]:
        wit = small_factor(stop["value"])
        if wit is None and witness:
            wit = stopper_witness(stop["value"])
        if wit is None:
            v = stop["value"]
            fermat = pow(2, v - 1, v) != 1
    stop = dict(stop, factor=wit, fermat_base2_fails=fermat)
    return ok, legs, stop


WITNESS_FULL_BELOW = 10 ** 30
# The bounded ECM effort a find's stopper gets when trial division and rho
# find no factor (~20 s at 200 digits); the evidence otherwise records the
# failed base-2 Fermat test.  The rediscovery drills set it to 0 (their
# stoppers are published terms' and the battery has five minutes).
WITNESS_ECM = 40


def stopper_witness(stop):
    """A nontrivial prime factor of a composite value, or None if the
    bounded effort (trial division, rho, ECM curves) found none -- in which
    case the failed Fermat base is the witness, and the evidence says so."""
    fac, _R = certificate.factor_partial(int(stop), ecm_curves=WITNESS_ECM)
    if fac:
        return int(min(fac))
    if stop < WITNESS_FULL_BELOW:
        w = factor_witness(int(stop))
        return int(w) if w and w > 1 else None
    return None


# THE CERTIFICATE ROUTE.  (b+1)^p - b^p - 1 factors over the integers as
# p * b * (b+1) * (b^2+b+1)^e * E(b), e = 2 when p == 1 (mod 6) else 1 (p >= 5;
# `minus_one_shape`, sympy's factor_list, multiplied back in the drill).  So
# N - 1 is factored by the term's own factorization, that of b + 1 (both
# complete: they are 50-75 bits at the heights the campaigns reach), the
# value b^2 + b + 1 and whatever huntlib's bounded factor_partial takes out
# of E(b).  The factored part F (every prime taken to its full power in
# N - 1) passes sqrt(N) at p <= 7 and p = 13 (BLS75 Theorem 1) and the cube
# root at p = 11 and 19 (Theorem 5); from p = 17 on it is a quarter of N or
# less and NO N - 1 route exists: those values are left UNPROVED in the
# evidence, for a general prover (APR-CL, ECPP) -- the find stands on the
# three legs, and the evidence says which values to certify.  The
# structureless search (certificate.prove on N alone) is not tried past the
# deterministic bound: at hundreds of digits it would cost minutes for
# nothing.
_B = Symbol("b")
# b^2 + b + 1 below this is factored completely (factor_full); above it
# (b past 1e30) the bounded factor_partial, and a value whose route needed
# it may be left UNPROVED (OPTIMIZATION_LOG.md, the proof-cost table).
QUAD_FULL_BELOW = 10 ** 60


@functools.lru_cache(maxsize=None)
def minus_one_shape(p):
    """[(kind, payload, e)]: the factorization of (b+1)^p - b^p - 1 over Z
    into ("const", c, 1) and ("poly", coefficients lowest-first, e)."""
    p = int(p)
    poly = (_B + 1) ** p - _B ** p - 1
    const, parts = factor_list(poly)
    out = []
    if int(const) != 1:
        out.append(("const", int(const), 1))
    for f, e in parts:
        cs = tuple(int(c) for c in reversed(Poly(f, _B).all_coeffs()))
        out.append(("poly", cs, int(e)))
    return tuple(out)


def _poly_value(coeffs, x):
    v = 0
    for c in reversed(coeffs):
        v = v * x + c
    return v


def _verified(proof):
    return proof is not None and certificate.verify(proof)[0]


def certify_value(N, fac, subproofs=None):
    """A RE-VERIFIED primality certificate for N from the factorization
    `fac` of (part of) N - 1 -- {q: e}, every q a prime under the bound or
    one with its proof in `subproofs` -- or None.  Each q is taken to its
    FULL power in N - 1, so F and R = (N - 1)/F are coprime.  BLS75
    Theorem 1 where F passes sqrt(N), Theorem 5 where it passes the cube
    root; under the deterministic bound huntlib's own proof."""
    N = int(N)
    subproofs = subproofs or {}
    if N < MR_VALID_BELOW:
        p = certificate.prove(N)
        return p if _verified(p) else None
    full = {}
    for q in fac:
        q = int(q)
        e, m = 0, N - 1
        while m % q == 0:
            m //= q
            e += 1
        if e:
            full[q] = e
    F = 1
    for q, e in full.items():
        F *= q ** e
    if F % 2 or (N - 1) % F:
        return None
    R = (N - 1) // F
    subs = {str(q): subproofs[q] for q in full
            if q >= MR_VALID_BELOW and q in subproofs}
    if not all(q < MR_VALID_BELOW or str(q) in subs for q in full):
        return None
    if F ** 3 <= N:
        return None                       # no N - 1 route
    w = certificate.witnesses(N, sorted(full))
    if w is None:
        return None
    out = {"N": N, "F": F, "R": R,
           "factors": {str(q): int(e) for q, e in sorted(full.items())},
           "witnesses": {str(q): a for q, a in sorted(w.items())}}
    if subs:
        out["subproofs"] = subs
    if F > math.isqrt(N):
        out["proof"] = "bls75-thm1"
    else:
        s, r = certificate.theorem5_split(F, R)
        out["proof"], out["s"], out["r"] = "bls75-thm5", s, r
    return out if _verified(out) else None


def term_factors(x):
    """{q: e} of an integer near the term, every q proved: huntlib's
    bounded chain, then sympy's factorint on what is left."""
    return {int(q): int(e) for q, e in certificate.factor_full(int(x)).items()}


def n_minus_one_factors(p, x, fx=None, fx1=None):
    """{q: e}: the primes of (x+1)^p - x^p - 1 this project can name -- p
    itself, the term's and its successor's factorizations, and the bounded
    factor_partial of every other factor of the shape."""
    x = int(x)
    fx = term_factors(x) if fx is None else fx
    fx1 = term_factors(x + 1) if fx1 is None else fx1
    fac = {}

    def add(d, e=1):
        for q, ee in d.items():
            fac[int(q)] = fac.get(int(q), 0) + int(ee) * int(e)
    for kind_, payload, e in minus_one_shape(p):
        if kind_ == "const":
            add(certificate.factor_full(abs(payload)))
            continue
        if payload == (0, 1):
            add(fx, e)
            continue
        if payload == (1, 1):
            add(fx1, e)
            continue
        v = abs(_poly_value(payload, x))
        if v <= 1:
            continue
        if v < MR_VALID_BELOW and mr_is_prime(v):
            add({v: 1}, e)
            continue
        if len(payload) == 3 and v < QUAD_FULL_BELOW:
            # b^2 + b + 1: the structural part every route past p = 7
            # rests on (squared at p == 1 mod 6), factored COMPLETELY --
            # 44 digits at b = 3e21, huntlib.factor_full's ECM-then-sympy
            # chain (a balanced 44-digit semiprime costs seconds to a
            # minute, once per discovery)
            add(certificate.factor_full(v), e)
            continue
        part, _R = certificate.factor_partial(v)
        add(part, e)
    return fac


def certify_run(x, run, fam):
    """A re-verified certificate for every PRIME-asking value of a run, in
    order of p: ({str(p): proof or None}, [the p left UNPROVED])."""
    fam = ref.family(fam)
    x, run = int(x), int(run)
    conds = ref.conditions(fam, max(run, 1))[:run]
    fx, fx1 = term_factors(x), term_factors(x + 1)
    certs, unproved, subs = {}, [], {}
    for p, want in conds:
        if not want:
            continue
        N = ref.value(p, x)
        if N < MR_VALID_BELOW:
            proof = certify_value(N, {})
        else:
            fac = n_minus_one_factors(p, x, fx, fx1)
            proof = certify_value(N, fac, big_prime_subproofs(fac, subs))
        certs[str(p)] = proof
        if proof is None:
            unproved.append(str(p))
    return certs, unproved


def big_prime_subproofs(fac, cache=None):
    """{q: proof} for every prime q of `fac` past the deterministic bound
    (a factor of b^2 + b + 1, or of the term itself near the ceiling):
    huntlib's own recursive prover, each proof re-verified, so the
    certificate that cites q carries q's proof with it."""
    cache = {} if cache is None else cache
    out = {}
    for q in fac:
        q = int(q)
        if q < MR_VALID_BELOW:
            continue
        if q not in cache:
            pr = certificate.prove(q)
            cache[q] = pr if _verified(pr) else None
        if cache[q] is not None:
            out[q] = cache[q]
    return out


_TDIV = None


def small_factor(v, bound=1 << 17):
    """The least prime factor of v under `bound` by trial division, or
    None.  Cheap at any size (12,251 remainders at 2^17)."""
    global _TDIV
    if _TDIV is None:
        from sympy import primerange
        _TDIV = list(primerange(2, bound))
    for q in _TDIV:
        if v % q == 0:
            return int(q) if v != q else None
    return None


def composite_witnesses(x, run, fam):
    """{str(p): {"factor": q or None, "fermat_base2_fails": bool}} for
    every COMPOSITE-asking condition of the run (A216668's non-Mersenne
    exponents).  A value that asks for a composite is unsieved, so about 19
    in 20 have a factor under 2^17; for the rest the failed base-2 Fermat
    test -- 2^(N-1) != 1 (mod N), which anyone can rerun -- is the proof.
    No ECM here: a run can hold a dozen of these at a thousand digits."""
    out = {}
    for p, want in ref.conditions(fam, max(int(run), 1))[:int(run)]:
        if not want:
            v = ref.value(p, int(x))
            f = small_factor(v)
            out[str(p)] = {"factor": f,
                           "fermat_base2_fails": (pow(2, v - 1, v) != 1
                                                  if f is None else None)}
    return out


def rider_settles(fam, x, run, open_exact):
    """A229073's index settled by a find on A216666's line: a(run + 1),
    with m = b + 1, when that index is open (A216666's run ends at a
    composite value, so every A216666 run is exact)."""
    if ref.family(fam) != RIDER_OF or int(run) not in open_exact:
        return None
    return {"sequence": RIDER, "n": int(run) + 1, "m": int(x) + 1}


# ----------------------------- classification -------------------------------

def filter_conditions(fam, n):
    """((p, wants_prime), ...) a pool worker reads at filter n, in run
    order, and the family's least b.  A worker is another process; it is
    handed what it needs and nothing of the engines."""
    fam = ref.family(fam)
    return (tuple(ref.conditions(fam, read_index(fam, n))), ref.b_min(fam))


_SPRP_SMALL = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def _sprp2(v):
    """huntlib's sprp_base2 -- trial division by the primes to 37, then a
    strong test to base 2 -- with the test done by gmpy2 when it is
    installed (8x faster at 1,700 digits); the classification drill pins
    the two to each other, pseudoprimes included."""
    if _gmpy2 is None:
        return sprp_base2(v)
    if v < 2:
        return False
    for sp in _SPRP_SMALL:
        if v % sp == 0:
            return v == sp
    return bool(_gmpy2.is_strong_prp(v, 2))


def sprp_run(x, task):
    """The run of b = x, read with a base-2 strong probable-prime test.

    The PRIME-asking conditions are read first, in order, to the first that
    fails (a failed base-2 test is a PROOF of compositeness, so this can
    only overstate a run); then the COMPOSITE-asking ones before it, in
    order, to the first whose value is prime -- confirmed by the full
    Miller-Rabin chain, so a base-2 pseudoprime cannot shorten a run.  The
    census is counted on this chain -- it is a count, not a claim -- and
    every value that is narrated (a NEAR) or recorded (a DISCOVERY) is
    verified three ways first (verify)."""
    conds, bmin = task
    b = int(x)
    if b < bmin:
        return 0
    stop = len(conds)
    for i, (p, want) in enumerate(conds):
        if want:
            v = (b + 1) ** p - b ** p
            if v < 2 or not _sprp2(v):
                stop = i
                break
    for i, (p, want) in enumerate(conds[:stop]):
        if not want:
            v = (b + 1) ** p - b ** p
            if _sprp2(v) and mr_is_prime(v):
                return i
    return stop


def _classify_chunk(task):
    """Pool worker: runs of a chunk of survivors, in order."""
    conds, ks = task
    return [sprp_run(int(k), conds) for k in ks]


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


def _submit(pool, conds, ks):
    ks = [int(k) for k in ks]
    out = []
    for i in range(0, len(ks), CHUNK):
        chunk = ks[i:i + CHUNK]
        if pool is None:
            out.append((chunk, _Done(_classify_chunk((conds, chunk)))))
        else:
            out.append((chunk, pool.submit(_classify_chunk, (conds, chunk))))
    return out


def headline(seq, settles, x):
    if len(settles) == 1:
        return f"{seq} a({settles[0]}) = {int(x):,}"
    return f"{seq} a({settles[0]})..a({settles[-1]}) = {int(x):,}"


def evidence_name(seq, n, x):
    return f"{str(seq).upper()}_a{int(n)}_{int(x)}.json"


def evidence_record(fam, x, run, legs, stop, certs, unproved, settles,
                    rider, least_claim, engine, filter_n=None):
    """The evidence dict of a find (or of a free term): the header in the
    OEIS entry's own letters, then the run, every value, the factored term,
    the legs, the stopper with its witness, the certificates and the
    least-claim.  When the find settles only A229073 (an exact run below
    A216666's frontier) the record IS A229073's, under m."""
    fam = ref.family(fam)
    x, run = int(x), int(run)
    conds = ref.conditions(fam, max(run, 1))[:run]
    if settles:
        ev = evidence.header(fam, ref.FAMILIES[fam]["forms"], TERM(fam), x,
                             settles)
    else:
        d = ref.DERIVED[RIDER]
        ev = evidence.header(RIDER, d["forms"], d["term"], x + 1,
                             [rider["n"]])
        ev[TERM(fam)] = x                 # A216666's b = m - 1, for the record
    routes = {}
    for c in certs.values():
        r_ = c.get("proof") if c else "none"
        routes[r_] = routes.get(r_, 0) + 1
    ev.update({
        "filter_n": int(filter_n if filter_n is not None else (settles or [run])[0]),
        "run": run,
        "settles": list(settles) if settles else [rider["n"]],
        "conditions": {str(p): condition(fam, p, want) for p, want in conds},
        "values": {str(p): int(ref.value(p, x)) for p, want in conds},
        f"{TERM(fam)}_factored": {str(q): e for q, e in sorted(term_factors(x).items())},
        "verification": legs,
        "stopper": {"p": stop["p"],
                    "condition": condition(fam, stop["p"], stop["wants_prime"]),
                    "value": int(stop["value"]), "why": stop["why"],
                    "factor": stop.get("factor"),
                    "fermat_base2_fails": stop.get("fermat_base2_fails")},
        "composite_witnesses": composite_witnesses(x, run, fam),
        "certificates": certs,
        "certificates_verified": not unproved,
        "unproved": unproved,
        "unproved_note": ("no BLS75 route: the factored part of N - 1 is "
                          "under the cube root of N (p >= 17); these values "
                          "passed the Miller-Rabin chain and BPSW and await "
                          "a general prover (APR-CL or ECPP)") if unproved else None,
        "proof_routes": routes,
        "also_settles": ([rider] if (rider and settles) else []),
        "least_claim": least_claim,
        "engine": engine})
    return ev


# --------------------------------- campaign ---------------------------------

class Campaign:
    def __init__(self, args, ckpt=None, cursor=None, pool=None, evid=None):
        self.args = args
        self.fam = ref.family(args.family)
        self.oeis = self.fam
        self.term = TERM(self.fam)
        self.rides = self.fam == RIDER_OF
        # DRILLS ONLY: open below the published frontier so that a drill's
        # "find" is a real published term; and stop before the filter of
        # `stop_n`, so a drill never sweeps an open index (CLAUDE.md 0a).
        drill_n = getattr(args, "start_n", None)
        self._known_top = (int(drill_n) - 1 if drill_n else ref.frontier(self.fam))
        self._rider_top = (int(drill_n) if drill_n else rider_known_top())
        self._stop_n = (int(args.stop_n) if getattr(args, "stop_n", None)
                        else None)
        self.key = config_key(self.fam)
        self.ckpt = ckpt or ckpt_path(self.fam)
        self.cursor = cursor or policy(self.fam)
        self.pool = pool
        self.evid = evid or EVID
        self.found = {}                # str(n) -> b found by THIS campaign
        self.found_rider = {}          # str(n) -> m of A229073 found here
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
        self.hc = HostCost(say=log, hb=self.hb, warn_s=SLOW_HOST_S)
        self._lad = LiveLadder(self._build_ladder)
        self._t0 = time.time()
        self.workers = None
        self._sizing = None
        self._hostwait = 0.0
        # the b below which the line is covered by an EARLIER filter's
        # classified sweep (the carried line); the sweep of the current
        # filter starts at max(its floor, this)
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
                f"but this campaign's filter is n = {self.filter_n()}: "
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
                             unit=unit, pb=pb, seg_cap=pb,
                             prp=prp_count(self.fam), select=gpu.SIEVE_TAU)

    # ------------------------------------------------------------- frontier
    def frontier(self):
        """The largest index of THIS family settled."""
        top = self._known_top
        for n in self.found:
            top = max(top, int(n))
        return top

    def frontier_k(self):
        n = self.frontier()
        if str(n) in self.found:
            return int(self.found[str(n)])
        return int(ref.term(self.fam, n)) if n >= 1 else ref.b_min(self.fam)

    def rider_open(self):
        """The runs r whose A229073 a(r + 1) is open, up to the furthest
        any run is read (A216666's campaign only)."""
        if not self.rides:
            return frozenset()
        top = self._rider_top
        known = {int(m) for m in self.found_rider}
        return frozenset(j - 1 for j in range(top + 1, cpu.READ_MAX + 2)
                         if j not in known)

    def rider_low(self):
        """A229073's lowest open index, or None."""
        op = self.rider_open()
        return (min(op) + 1) if op else None

    def filter_n(self):
        """The index whose sieved forms the engine runs: the frontier + 1,
        held down on A216666 to A229073's lowest open EXACT run (module
        docstring) -- never below it, so every value whose run could settle
        an open index of either entry is in the stream."""
        n = self.frontier() + 1
        low = self.rider_low()
        if low is not None:
            n = min(n, low - 1)
        return n

    def x_start(self):
        """The floor of THIS filter's sweep: the frontier term (inclusive),
        or the carried coverage of the previous filter, whichever is
        higher."""
        return max(x_floor(self.fam, self.filter_n(), self.frontier_k()),
                   int(self.cover_x))

    def floor_period(self):
        return self.x_start() // int(self.eng.W)

    def k_min(self):
        """The clip for the segment being worked: the first b the device
        may report while the sweep is inside the segment that holds the
        floor (above the engine floor, whose zone is the host's), none
        after."""
        st = max(self.x_start(), cpu.k_floor(self.eng.q2, self.filter_n(), self.fam) + 1)
        return st if self.j * int(self.eng.W) <= st else None

    def run_cap(self):
        """The index whose conditions the classification reads: the filter
        plus RUN_AHEAD, or in a drill no further than the index it was
        opened to find (a drill never settles an index it was not opened
        for; CLAUDE.md 0a)."""
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

    def kind(self, run):
        return event_kind(run, self.frontier(), self.rider_open(),
                          self.filter_n())

    # ----------------------------------------------------------------- rungs
    def _build_ladder(self, frontier, frontier_k, n):
        ceil = cpu.k_ceil(n, self.fam)
        preds = model.predictions(self.fam, frontier, frontier_k,
                                  n_ahead=3, ceiling=ceil)
        return Ladder.from_predictions(preds, ceiling=ceil,
                                       ceiling_label="engine ceiling")

    def ladder(self):
        return self._lad.get(self.frontier(), self.frontier_k(),
                             self.frontier() + 1)

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
                f"way) and a DISCOVERY's values are proved by BLS75 on the "
                f"value less one where its factored part reaches (p <= 13 "
                f"and p = 19), the rest left for a general prover; the "
                f"ceiling is {self.term} < "
                f"{cpu.k_ceil(self.filter_n(), self.fam):.4g}")

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
                "found_rider": dict(self.found_rider),
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
        self.found = dict(st.get("found", {}))
        self.found_rider = dict(st.get("found_rider", {}))
        self.census = {int(r): int(c) for r, c in st.get("census", {}).items()}
        self.passed = list(st.get("passed", []))
        self.elapsed = float(st.get("elapsed", 0.0))
        self.discoveries = int(st.get("discoveries", 0))
        self.near = int(st.get("near", 0))
        self.survivors = int(st.get("survivors", 0))
        return True

    def swept_k(self):
        """The b below which EVERY value at or above the sweep's floor has
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
        if self.rides:
            low = self.rider_low()
            parts.append(f"{RIDER} open a({low})" if low else f"{RIDER} none open")
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
            nf = self.frontier() + 1
            p = model.p_by(self.fam, nf,
                           model.floor_for(self.fam, nf, self.frontier_k()), cov)
            parts.append(f"P(a({nf}) under the claim) = {100 * p:.0f}%")
        slow = self.hc.status()
        if slow:
            parts.append(slow)
        stall = self.hb.stalled()
        if stall:
            parts.append(f"-- no segment closed since the last status: "
                         f"{stall[0]} for {stall[1]:.0f}s")
        return "  ".join(parts)

    # --------------------------------------------------------------- hits
    def handle(self, k, run):
        """Classify one value.  True if it was a find."""
        kind = self.kind(run)
        if kind is None:
            return False
        self.census[run] = self.census.get(run, 0) + 1
        if kind == "CENSUS":
            return False
        if kind == "NEAR":
            if self._stop_n is not None and run >= self.run_cap():
                # a drill reads runs no further than its bound: a value at
                # the cap may run on past it, and is not narrated
                return False
            self.near += 1
            ok, legs, _ = verify(k, run, self.fam, witness=False)
            if not ok:
                log("ALARM", f"NEAR candidate {self.term} = {k:,} run {run} "
                             f"failed verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at {self.term} = {k:,} (run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of filter n = {self.filter_n()}!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, x, run):
        frontier = self.frontier()
        n = self.filter_n()
        self.hc.expect("discovery verification")
        self.hb.doing(f"verifying run-{run} {self.term}={x}")
        # the run, re-read with NO cap by the oracle: a run at the
        # classification's cap may be longer
        read_to = cpu.read_max(self.fam) if self._stop_n is None else self.run_cap()
        full = ref.run_length(self.fam, x, read_to)
        if self._stop_n is None and full >= cpu.READ_MAX:
            log("ALARM", f"{self.term} = {x} runs to the read limit "
                         f"{cpu.READ_MAX}: a run that long is an engine bug "
                         f"until proved otherwise -- halting")
            raise SystemExit(2)
        if full < run or full < n or x < self.x_start():
            log("ALARM", f"claimed {self.oeis} run {run} at {x} is not one by "
                         f"the oracle: run {full}, filter {n}, floor "
                         f"{self.x_start()}")
            raise SystemExit(2)
        run = full
        settles = list(range(frontier + 1, run + 1))
        rider = rider_settles(self.fam, x, run, self.rider_open())
        if not settles and rider is None:
            # an exact run the drain held but nothing open any more: census
            return False
        ok, legs, stop = verify(x, run, self.fam)
        if not ok:
            log("ALARM", f"claimed run {run} at {x} failed the protocol: {legs}")
            raise SystemExit(2)
        self.hb.doing(f"certifying run-{run} {self.term}={x}")
        certs, unproved = certify_run(x, run, self.fam)
        least = {"swept_from": int(self.x_start()),
                 "campaign_started_at": int(self.start_x),
                 "swept_to": int(x),
                 "floor": (f"a({frontier}) = {self.frontier_k()}, inclusive: "
                           f"the conditions nest"),
                 "carried": (f"the line below {self.cover_x} was classified "
                             f"by the previous filter with runs read to the "
                             f"filter + {RUN_AHEAD}" if self.cover_x else None),
                 "rider": (f"every b at or above the floor whose run is "
                           f"{n} or more was read (the filter is held at "
                           f"A229073's lowest open exact run): {x} is the "
                           f"first of run exactly {run}" if rider else None),
                 "exception_zone": list(self.zone()) if self.zone() else None,
                 "filter": int(n),
                 "wheel": int(self.eng.W),
                 "sieve_depth": int(self.eng.q2),
                 "fermat_stage": int(self.eng.prp)}
        ev = evidence_record(self.fam, x, run, legs, stop, certs, unproved,
                             settles, rider, least, self.key, filter_n=n)
        seq = self.oeis if settles else RIDER
        idx = settles[0] if settles else rider["n"]
        letter = TERM(seq)
        for m in settles:
            self.found[str(m)] = int(x)
        if rider is not None:
            self.found_rider[str(rider["n"])] = int(x) + 1
        path = evidence.record(
            ev, self.evid, evidence_name(seq, idx, ev[letter]),
            ledger_path(seq, self.evid), key=letter,
            label="%s a(%s)" % (seq, ",".join(map(str, ev["settles"]))))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        lines = []
        if settles:
            lines.append(headline(self.oeis, settles, x))
        if rider is not None:
            lines.append(headline(RIDER, [rider["n"]], x + 1) +
                         f" (m = {self.term} + 1; run exactly {run})")
        lines.append(f"run {run}: the conditions at p = "
                     f"{', '.join(str(p) for p, _w in ref.conditions(self.fam, run))} hold")
        lines.append(f"stopped at p = {stop['p']}: "
                     f"{condition(self.fam, stop['p'], stop['wants_prime'])} "
                     f"fails, the value is {stop['why']}"
                     + (f" = {stop['factor']} x ..." if stop.get("factor") else ""))
        lines.append(f"verified 3 ways, {proved} of {len(certs)} certificates "
                     f"re-verified ({', '.join(f'{r} x{c}' for r, c in sorted(ev['proof_routes'].items()))}), "
                     f"evidence {path}")
        if unproved:
            lines.append(f"UNPROVED at p = {unproved}: no N - 1 route (the "
                         f"factored part is under the cube root); those values "
                         f"passed the Miller-Rabin chain and BPSW; prove them "
                         f"with a general prover from the evidence file")
        banner("DISCOVERY", lines)
        return True

    def follow_frontier(self, old_boundary_x):
        """After a find: rebuild the engine at the new filter when it moved
        -- the classified line is carried and the sweep resumes at the old
        segment's end, re-denominated by floor into the new period with the
        clip at the old boundary.  When A229073 holds the filter where it
        was, the engine and the line simply go on.  A find inside the new
        filter's exception zone (drills at small indices only) promotes
        again, until the zone of the filter reached holds none."""
        while self._follow_once(old_boundary_x):
            old_boundary_x = self.boundary * self.eng.W

    def _follow_once(self, old_boundary_x):
        """One promotion; True when the new filter's zone held a find."""
        old = self.eng
        if self.filter_n() == old.n:
            self.pending = []
            self.passed = [p for p in self.passed
                           if not any(p.startswith(f"a({m})")
                                      for m in self.found)]
            log("STAGE",
                f"filter stays at n = {old.n}: {RIDER}'s lowest open index "
                f"is a({self.rider_low()}), which needs a run of exactly "
                f"{self.rider_low() - 1}; the sweep goes on at period "
                f"{self.j}, and the ladder now aims at "
                f"a({self.frontier() + 1}) of {self.oeis}")
            self.mark_boundary()
            return False
        self.cover_x = int(old_boundary_x)
        self.eng = self._build_engine(self.filter_n())
        self.key = config_key(self.fam)
        self.j = self.floor_period()
        self.u = 0
        self.boundary = self.j
        self.pending = []
        log("STAGE",
            f"filter follows the frontier: n = {old.n} -> {self.eng.n}; the "
            f"wheel ({old.p1},{old.p2},{old.p3}) becomes "
            f"({self.eng.p1},{self.eng.p2},{self.eng.p3}), the depth "
            f"{old.q2} becomes {self.eng.q2}, the period {old.W:.4g} becomes "
            f"{self.eng.W:.4g}, the segment {old.seg_periods} -> "
            f"{self.eng.seg_periods} periods on the "
            f"{'WIDE' if self.eng.wide else 'narrow'} survivor record; "
            f"the line below {self.cover_x:,} is CARRIED (classified by the "
            f"old filter with runs read to n + {RUN_AHEAD}) and the sweep "
            f"resumes there, floored into the new period {self.j} with the "
            f"clip at the old boundary; the ladder now aims at "
            f"a({self.frontier() + 1})")
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({m})")
                                  for m in self.found)]
        self._proof_logged = None
        again = self.cover_zone()
        if again:
            return True
        self.check_proof_crossing(self.swept_k())
        self.size_pool()
        self.mark_boundary()
        return False

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
                with self.hc.item(f"classifying {self.term} = {x} (zone)"):
                    if self.handle(x, r):
                        found_now = True
                # a find that moves the filter ends this walk (the new
                # filter walks its own zone); one that A229073 holds the
                # filter under does not -- the rest of the zone is still
                # this filter's to cover
                if found_now and self.filter_n() != n:
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
        task = filter_conditions(self.fam, self.filter_n())
        sample = surv[:CAL_SAMPLE]
        t1 = time.perf_counter()
        for k in sample:
            sprp_run(k, task)
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
        # a run that the state already counts as census is counted here
        # (the frontier only rises and the open sets only shrink, at the
        # segment's end), rather than held to the segment's end
        frontier, op, fn = self.frontier(), self.rider_open(), self.filter_n()
        while inflight:
            cur, parts = inflight[0]
            if not block and not all(f.done() for _ks, f in parts):
                break
            inflight.popleft()
            for ks, f in parts:
                for k, r in zip(ks, f.result()):
                    self.survivors += 1
                    kind = event_kind(r, frontier, op, fn)
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
        log("STAGE", device_report(self.eng.bytes_held()))
        cfg = self.eng.config()
        log("STAGE",
            f"sweeping the {self.term} line to {target:.4g}; {self.oeis} "
            f"({ref.FAMILIES[self.fam]['forms']}) filter n = {self.filter_n()} "
            f"({self.eng.nforms} sieved forms, p = "
            f"{', '.join(map(str, ref.forms(self.fam, self.filter_n())))})"
            + (f", {RIDER} riding (open a({self.rider_low()}))" if self.rides else "")
            + f"; wheel W = {self.eng.W:,} ({self.eng.R:,} residues, "
            f"{self.eng.R1} x {self.eng.R2} x {self.eng.R3}"
            f", {100.0 * self.eng.density():.6f}% "
            f"of the line); a segment is {self.eng.seg_periods} periods "
            f"({self.eng.seg_periods * self.eng.W:.4g} of line) in "
            f"{self.eng.launches_per_segment} launches of "
            f"{cfg['cand_per_launch']:.3g} candidates; the sieve runs to "
            f"{self.eng.q2} and the device Fermat-tests the first "
            f"{len(self.eng.prp_forms)} sieved forms of every survivor; the "
            f"sweep's floor is {self.term} = {self.x_start():,}; resume at "
            f"period {self.j}, launch {self.u} ({self.term} = "
            f"{self.u_progress(self.j, self.u):,})")
        preds = model.predictions(self.fam, self.frontier(), self.frontier_k(),
                                  n_ahead=3,
                                  ceiling=cpu.k_ceil(self.filter_n(), self.fam))
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
                stop_now = bool(self.args.stop_on_discovery)
                self.save()
            task = filter_conditions(self.fam, self.filter_n())
            while self.swept_k() < target and not stop_now:
                if self._stop_n is not None and self.filter_n() >= self._stop_n:
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
                cap0 = self.run_cap()
                task = (filter_conditions(self.fam, cap0 - RUN_AHEAD)
                        if self._stop_n is None else
                        (tuple(ref.conditions(self.fam, cap0)), ref.b_min(self.fam)))
                for jn, un, surv in self.eng.sweep(self.j, j1, u_from=self.u,
                                                   k_min=self.k_min()):
                    inflight.append(((jn, un), _submit(self.pool, task, surv)))
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
                # A RUN AT THE CLASSIFICATION'S CAP IS "AT LEAST THAT LONG":
                # a find among the pending values moves the frontier before
                # the values after it are classified -- so a later value
                # stored at the old cap, whose true run passes the new
                # frontier, would be counted as census and lost.  Every
                # pending value at or past the cap the segment was swept
                # under is re-read uncapped by the oracle first (a drill
                # reads no further than the index it was opened for).
                read_to = (cpu.read_max(self.fam) if self._stop_n is None
                           else cap0)
                for k, r in sorted(self.pending):
                    if r >= cap0:
                        r = ref.run_length(self.fam, k, read_to)
                    with self.hc.item(f"classifying {self.term} = {k} (run {r})"):
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
                        f"line; {held} value{'' if held == 1 else 's'} one "
                        f"short of the filter or past it classified in "
                        f"numerical order, the census counted as it came"
                        + (f"; {self._plog_n} segments closed since the last "
                           f"such line" if self._plog_n > 1 else "") + ")")
                    self._plog_t, self._plog_n = time.time(), 0
                if found_now:
                    self.follow_frontier(self.boundary * self.eng.W)
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
                                 "a frontier-extending find")
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


# ------------------------------ the free terms ------------------------------

# THE FREE TERMS (2026-11-23), recorded without a campaign: A216668's run at
# its published a(11) = 288,975,248,496 is exactly 17, so a(12)..a(17) are
# that integer; A216666's runs at its published a(7) and a(8) are exactly 7
# and 8, so A229073's a(8) and a(9) are those integers plus one.  Each is
# least by nesting alone (difference_reference G1b): no sweep was needed.
FREE = (("A216668", 288975248496, 17, list(range(12, 18)), None),
        ("A216666", 30717523794, 7, [], {"sequence": RIDER, "n": 8, "m": 30717523795}),
        ("A216666", 55779743835, 8, [], {"sequence": RIDER, "n": 9, "m": 55779743836}))


def free_evidence(witness=True):
    """[(sequence, filename, evidence dict)] for the free terms, built
    through the same protocol as a campaign's find: the run re-read by the
    oracle, the three legs, the stopper's witness, the certificates, the
    composite witnesses -- and a least-claim that says why no sweep was
    needed.  witness=False skips the bounded rho/ECM search for a stopper
    factor that trial division did not find (the selftest's re-derivation:
    the recorded factor is checked by division instead)."""
    out = []
    for fam, b, run, settles, rider in FREE:
        if ref.run_length(fam, b, run + 4) != run:
            raise ArithmeticError(f"{fam}: the run at {b} is not exactly {run}")
        ok, legs, stop = verify(b, run, fam, witness=witness)
        if not ok:
            raise ArithmeticError(f"{fam}: the free term at {b} fails {legs}")
        certs, unproved = certify_run(b, run, fam)
        if settles:
            least = {"free_term": True,
                     "basis": (f"a(11) = {b} is published (Jean-Louis Charton, "
                               f"Oct 2012); every b with a run of 12 or more has "
                               f"a run of 11, so a(n) >= a(11) for n >= 12, and "
                               f"the run at {b} is exactly {run}: a(12)..a({run}) "
                               f"= a(11).  No sweep was needed.")}
        else:
            n = rider["n"]
            least = {"free_term": True,
                     "basis": (f"A216666 a({n - 1}) = {b} is published (Jean-"
                               f"Louis Charton, 2012) and its run is exactly "
                               f"{n - 1}; every m with A229073's condition at "
                               f"index {n} has m - 1 of run exactly {n - 1}, so "
                               f"m - 1 >= A216666 a({n - 1}): A229073 a({n}) = "
                               f"A216666 a({n - 1}) + 1 = {b + 1}.  No sweep "
                               f"was needed.")}
        ev = evidence_record(fam, b, run, legs, stop, certs, unproved,
                             settles, rider, least,
                             "free term (no campaign): " + config_key(fam),
                             filter_n=(settles[0] if settles else rider["n"] - 1))
        seq = fam if settles else RIDER
        idx = settles[0] if settles else rider["n"]
        out.append((seq, evidence_name(seq, idx, ev[TERM(seq)]), ev))
    return out


def record_free_terms(evid=None):
    """Write the free terms' evidence files and ledger rows (idempotent:
    records are upserted)."""
    evid = evid or EVID
    paths = []
    for seq, name, ev in free_evidence():
        paths.append(evidence.record(ev, evid, name, ledger_path(seq, evid),
                                     key=TERM(seq),
                                     label="%s a(%s) (free term)" % (
                                         seq, ",".join(map(str, ev["settles"])))))
    return paths


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """The taxonomy on this project's mathematics: at A216666's opening
    (frontier 8, A229073 open from a(10), so the exact runs 9.. open) a
    run of 9 or more is a find, 8 is NEAR; at A216668's (frontier 17, no
    rider) 18 is a find and 17 NEAR; and with A229073 holding the filter
    at 9 under a frontier of 11, runs 9 and 10 are finds, 11 census."""
    op = frozenset(range(9, 41))
    held = frozenset({9, 10} | set(range(12, 41)))
    return [((9, 8, op, 9), "DISCOVERY"),
            ((12, 8, op, 9), "DISCOVERY"),     # a long run settles several
            ((8, 8, op, 9), "NEAR"),
            ((7, 8, op, 9), "CENSUS"),
            ((6, 8, op, 9), "CENSUS"),
            ((5, 8, op, 9), None),
            ((18, 17, (), 18), "DISCOVERY"),
            ((17, 17, (), 18), "NEAR"),
            ((11, 17, (), 18), "CENSUS"),
            ((4, 17, (), 18), None),
            ((9, 11, held, 9), "DISCOVERY"),   # the rider holds the filter
            ((10, 11, held, 9), "DISCOVERY"),
            ((11, 11, held, 9), "CENSUS"),
            ((12, 11, held, 9), "DISCOVERY"),
            ((8, 11, held, 9), "NEAR")]


# The canaries: published terms a mini-hunt reaches from the index's floor
# in seconds, each through the device Fermat stage on every sieved form.
_CANARIES = (("A216666", 6), ("A216666", 7), ("A216666", 8), ("A216668", 7),
             ("A216668", 8))


def _canary_hunt():
    """The stream must organically rediscover published terms, in both
    families, from the index's floor (inclusive), so FIRST is a claim about
    the line."""
    hits_all = []
    for fam, n in _CANARIES:
        want = ref.KNOWN[fam][n]
        q2 = 4096
        nf = ref.nforms(fam, n)
        eng = gpu.GpuEngine(n, fam, p1=19, p2=None, p3=None, q2=q2, prp=nf)
        lo = x_floor(fam, n, ref.KNOWN[fam].get(n - 1, 0))
        pre = [x for x, r in cpu.prefix_hits(fam, n, q2, floor=n) if x >= lo]
        if pre and min(pre) < want:
            return False, f"CANARY FAIL: {fam} n={n}: the zone holds {min(pre)}"
        start = max(lo, cpu.k_floor(q2, n, fam) + 1)
        ceng = cpu.CpuEngine(n, fam, q2=q2)
        surv = eng.survivors_j(start // eng.W, want // eng.W + 1, k_min=start)
        hits = [int(k) for k in surv if ceng.run_length(int(k)) >= n]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: {fam} index n={n} found "
                           f"{min(hits) if hits else None}, expected a({n}) = {want}")
        hits_all.append(f"{fam} a({n}) = {want:,}")
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as FIRST occurrences from each "
                  "index's floor, both families, through the device Fermat "
                  "stage on every sieved form")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on both families,
    with both kinds of stopper (a composite where a prime was asked, a
    prime where A216668 asked for a composite)."""
    fam = "A216666"
    x = ref.KNOWN[fam][8]
    # the stopper f_23(a(8)) has no factor under 2^17: the drill takes the
    # cheap witness, the failed base-2 Fermat test, and leaves the bounded
    # rho/ECM search to the find itself
    ok, legs, stop = verify(x, 8, fam, witness=False)
    if not ok or stop["p"] != 23 or stop["why"] != "composite" or not (
            stop["factor"] or stop["fermat_base2_fails"]):
        return False, (f"PROTOCOL FAIL: genuine A216666 a(8) = {x} at its run 8 "
                       f"rejected: {legs} {stop}")
    if stop["factor"] and (stop["value"] % stop["factor"]
                           or stop["factor"] in (1, stop["value"])):
        return False, "PROTOCOL FAIL: the witness is not a factor"
    bad, legs_b, _ = verify(x, 9, fam)
    if bad:
        return False, f"PROTOCOL FAIL: a fake run-9 claim at {x} ACCEPTED ({legs_b})"
    fake, _lc, _ = verify(ref.KNOWN[fam][7], 8, fam)
    if fake:
        return False, "PROTOCOL FAIL: A216666 a(7) accepted as a run-8"
    ok1, _l1, s1 = verify(1, 4, fam)            # b = 1 runs to 4: 2^11 - 1
    if not ok1 or s1["p"] != 11:
        return False, "PROTOCOL FAIL: b = 1 at its true run 4 rejected"
    fam = "A216668"
    x = ref.KNOWN[fam][11]
    ok, legs, stop = verify(x, 17, fam)
    if not ok or stop["p"] != 61 or stop["why"] != "composite" or not stop["wants_prime"]:
        return False, (f"PROTOCOL FAIL: A216668's run 17 at a(11) = {x} "
                       f"rejected: {legs} {stop}")
    if not stop["factor"] or stop["value"] % stop["factor"] or \
            stop["factor"] in (1, stop["value"]):
        return False, "PROTOCOL FAIL: the p = 61 witness is not a factor"
    bad, legs_b, _ = verify(x, 18, fam)
    if bad:
        return False, "PROTOCOL FAIL: A216668 a(11) accepted at run 18"
    # 6524 (A216666's a(5)) makes f_11 PRIME, where A216668 asks for a
    # composite: its A216668 run is 4, stopped by a prime
    ok6, l6, s6 = verify(6524, 4, fam)
    if not ok6 or s6["p"] != 11 or s6["why"] != "prime" or s6["wants_prime"]:
        return False, f"PROTOCOL FAIL: 6524's A216668 run 4 read {l6} {s6}"
    bad6, _l, _s = verify(6524, 5, fam)
    if bad6:
        return False, "PROTOCOL FAIL: 6524 accepted at A216668 run 5"
    return True, ("protocol ok, both families: A216666's a(8) accepted at run "
                  "8 with p = 23 composite (no factor under 2^17: the failed "
                  "base-2 Fermat test is the witness), a run one too long and "
                  "a(7) mislabelled as run 8 both rejected, b = 1 accepted at "
                  "its true run 4; A216668's a(11) accepted at run 17 (p = 61 "
                  "composite where 2^61 - 1 is prime, with a factor witness) "
                  "and rejected at 18; and "
                  "b = 6524 accepted at A216668 run 4, stopped by a PRIME at "
                  "p = 11 where 2^11 - 1 is composite, and rejected at run 5")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing, on both families."""
    raised = []
    for fam, n in (("A216666", 11), ("A216668", 24)):
        eng = gpu.GpuEngine(n, fam, p1=19, p2=None, p3=None, q2=1024)
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
        gpu.wheel(9, "A216666", 59)
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(5, "A216666", p1=31, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    # the residue list holds NRES_MAX kills a prime and a prime can kill up
    # to the sum of (p - 1) over the sieved forms: the first index past
    # n_max is refused on both families
    for fam in ("A216666", "A216668"):
        n = cpu.n_max(fam) + 1
        if ref.maxkills(fam, n) <= gpu.NRES_MAX:
            return False, f"CEILING FAIL: {fam} n = {n} fits the residue list"
        try:
            gpu.GpuEngine(n, fam, p1=19, p2=None, p3=None, q2=1024)
            return False, (f"CEILING FAIL: {fam} n = {n}, whose kills overflow "
                           f"the tail's residue list, was accepted")
        except ValueError:
            raised.append(f"maxkills <= NRES_MAX ({fam} n = {n})")
    for fam, n, unit in (("A216666", 11, 2), ("A216666", 9, 6),
                         ("A216668", 24, 3), ("A216668", 18, 2310)):
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


# The routes each prime-asking value of a run takes at the heights here:
# Theorem 1 where the factored part of N - 1 passes sqrt(N) (p <= 7: all of
# it; p = 13: half and a little), Theorem 5 past the cube root (p = 11 at
# 0.4; p = 19 at exactly a third of the degree, carried over the cube root
# by the factor p = 19 itself and by whatever small factors of E(b) the
# bounded search takes out -- measured on A216666's a(8), A229073's free
# terms and A216668's), none at p = 17 (a quarter) or from p = 23 on.
ROUTE_OF = {2: "bls75-thm1", 3: "bls75-thm1", 5: "bls75-thm1",
            7: "bls75-thm1", 11: "bls75-thm5", 13: "bls75-thm1",
            19: "bls75-thm5"}


def _certificate_drill():
    """A discovery past the proof crossing is PROVED on its own structure
    where it can be: every value of A216666's a(8) at p <= 13 and p = 19 by
    BLS75 on N - 1, the route each p takes pinned (ROUTE_OF), p = 17 left
    UNPROVED as the README says; the shapes of (b+1)^p - b^p - 1 multiply
    back for every p to 89; and AT THE CEILING, f_2 = 2b + 1 at a b near
    1e40 whose prime factor is past the deterministic bound, so the
    subproof is exercised and cannot be stripped."""
    parts = []
    t0 = time.time()
    for p in [q for q in range(2, 90) if isprime(q)]:
        xv = 10 ** 6 + 7
        prod = 1
        for kind_, payload, e in minus_one_shape(p):
            prod *= (payload if kind_ == "const" else _poly_value(payload, xv)) ** e
        if prod != ref.value(p, xv) - 1:
            return False, f"CERTIFICATE FAIL: the shape of f_{p}(b) - 1 does not multiply back"
    fam = "A216666"
    x = ref.KNOWN[fam][8]
    certs, unproved = certify_run(x, 8, fam)
    for p in (2, 3, 5, 7, 11, 13, 19):
        N = ref.value(p, x)
        proof = certs[str(p)]
        if N < MR_VALID_BELOW:
            if not proof or proof.get("proof") != "deterministic-mr":
                return False, f"CERTIFICATE FAIL: p = {p} under the bound took {proof}"
            continue
        ok, why = _check_cert(proof, N, f"A216666 a(8) p = {p}", (ROUTE_OF[p],))
        if not ok:
            return False, "CERTIFICATE FAIL: " + why
    if unproved != ["17"]:
        return False, (f"CERTIFICATE FAIL: A216666 a(8) left {unproved} "
                       f"unproved, the routes say ['17']")
    parts.append(f"A216666 a(8)'s eight values: p = 2..13 and 19 proved "
                 f"({', '.join(sorted({c['proof'] for c in certs.values() if c}))}), "
                 f"p = 17 left UNPROVED (no N - 1 route: a quarter of N)")
    # AT THE CEILING: b = 2 * 3 * P with P a prime past the deterministic
    # bound whose P - 1 is smooth (so P itself is proved by Theorem 1 one
    # level down), and f_2(b) = 2b + 1 prime: N - 1 = 2b
    base = 2 ** 56 * 3 ** 28                   # 1.65e30: past the bound, smooth
    found = None
    for c in range(1, 2000000):
        P = base * c + 1
        b = 6 * P
        if b >= ceiling.K_CEIL:
            break
        if not sprp_base2(P):
            continue
        if isprime(P) and isprime(2 * b + 1):
            found = (b, P)
            break
    if found is None:
        return False, "CERTIFICATE FAIL: no b of the ceiling drill's shape"
    b, P = found
    fx = term_factors(b)
    if P not in fx or P < MR_VALID_BELOW:
        return False, "CERTIFICATE FAIL: the ceiling drill's term lacks its big prime"
    N = 2 * b + 1
    sub = certificate.prove(P)
    if sub is None or not certificate.verify(sub)[0]:
        return False, "CERTIFICATE FAIL: the smooth prime past the bound was not proved"
    proof = certify_value(N, n_minus_one_factors(2, b, fx, term_factors(b + 1)),
                          {P: sub})
    ok, why = _check_cert(proof, N, f"f_2 at b = {b:.4g}", ("bls75-thm1",))
    if not ok:
        return False, "CERTIFICATE FAIL (at the ceiling): " + why
    if not proof.get("subproofs"):
        return False, "CERTIFICATE FAIL: the ceiling certificate carries no subproof"
    if certificate.verify({a_: b_ for a_, b_ in proof.items()
                           if a_ != "subproofs"})[0]:
        return False, "CERTIFICATE FAIL: a proof stripped of its subproof verified"
    parts.append(f"f_2 at b = {b:.4g} ({len(str(N))} digits) by Theorem 1 "
                 f"with a subproof for the {len(str(P))}-digit prime factor of "
                 f"b, which cannot be stripped")
    parts.append(f"{time.time() - t0:.1f} s in all")
    return True, "certificates ok: " + "; ".join(parts)


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly, across the seams
    a real interrupt leaves: a period boundary, the (j, u) sub-period
    cursor, and the clipped first period -- on both families' engine
    shapes, the Fermat stage on and off."""
    total = 0
    for lab, fam, n, kw, x_at, span, cut in (
            ("one-level", "A216666", 9, dict(p1=17, p2=None, p3=None, q2=2048),
             10 ** 13, 40, 17),
            ("two-level", "A216668", 18, dict(p1=19, p2=29, p3=None, q2=8192, pb=32),
             10 ** 16, 3, 1),
            ("three-level", "A216666", 11, dict(p1=13, p2=19, p3=23, q2=4096, pb=32),
             10 ** 18, 40, 17),
            ("Fermat stage", "A216666", 9, dict(p1=13, p2=23, p3=None,
                                                q2=2048, pb=32, prp=1),
             10 ** 13, 30, 13)):
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
    for eng, j0s in ((gpu.GpuEngine(11, "A216666", p1=13, p2=19, p3=23, q2=8192,
                                    nu=2, pb=32),
                      ((lambda e: e.j_of(9 * 10 ** 15), None), (lambda e: 0, 10 ** 4))),
                     (gpu.GpuEngine(24, "A216668", p1=13, p2=19, p3=29, q2=8192,
                                    nu=2, pb=32),
                      ((lambda e: e.j_of(10 ** 18), None),
                       (lambda e: 0, 10 ** 4)))):
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
                  f"three-level wheels and with the Fermat stage on, both "
                  f"families; across the (j, u) sub-segment seam at A216666 "
                  f"n = 11 and A216668 n = 24, and inside the clipped first "
                  f"segment on both ({total} survivors across the seams)")


def _classification_drill():
    """The base-2 screen reads the same runs as the all-bases chain on real
    survivors (A216668's composite conditions included), gmpy2's test is
    huntlib's, the pool's chunked answer == the serial one, and every
    frontier term reads its true run through the pool's own conditions."""
    rows = []
    for fam, n, x_at in (("A216666", 7, 10 ** 9), ("A216668", 11, 10 ** 9)):
        eng = gpu.GpuEngine(n, fam, p1=13, p2=23, p3=None, q2=65536, pb=32)
        j0 = eng.j_of(x_at)
        surv = eng.survivors_j(j0, j0 + 1)
        if len(surv) < 3 * CHUNK:
            return False, f"CLASSIFY FAIL: only {len(surv)} survivors ({fam})"
        task = filter_conditions(fam, n)
        two = [sprp_run(k, task) for k in surv]
        ceng = cpu.CpuEngine(n, fam, q2=64)
        full = [ceng.run_length(k, read_n=read_index(fam, n)) for k in surv]
        if two != full:
            i = next(i for i in range(len(surv)) if two[i] != full[i])
            return False, (f"CLASSIFY FAIL: {fam}: the base-2 screen read run "
                           f"{two[i]} and the all-bases chain {full[i]} at b = "
                           f"{surv[i]}")
        with _pool_factory(2) as pool:
            parts = _submit(pool, task, surv)
            got = [r for ks, f in parts for r in f.result()]
        if got != full:
            return False, f"CLASSIFY FAIL: {fam}: the pool's chunked result differs"
        rows.append(f"{fam} n = {n}: {len(surv)} survivors (max run {max(full)}, "
                    f"{len(parts)} pool chunks)")
    for v in (341, 561, 2047, 3215031751, 2 ** 89 - 1, 2 ** 89 + 1, 3277, 4033, 4681,
              ref.value(13, 10 ** 15 + 7)):
        if bool(_sprp2(v)) != bool(sprp_base2(v)):
            return False, f"CLASSIFY FAIL: the two base-2 tests disagree at {v}"
    for f, n_, want in (("A216666", 8, 8), ("A216666", 1, 4), ("A216666", 5, 5),
                        ("A216668", 11, 17), ("A216668", 4, 5), ("A216668", 1, 3)):
        x = ref.KNOWN[f][n_]
        task = (tuple(ref.conditions(f, 24)), ref.b_min(f))
        if sprp_run(x, task) != want:
            return False, f"CLASSIFY FAIL: {f} a({n_}) through the pool's conditions"
    if sprp_run(6524, (tuple(ref.conditions("A216668", 8)), 2)) != 4:
        return False, "CLASSIFY FAIL: 6524 does not read A216668 run 4 (f_11 prime)"
    return True, ("classification ok: the base-2 screen == the all-bases chain "
                  "on real survivors -- " + "; ".join(rows) + " -- gmpy2's "
                  "strong test agrees with huntlib's on the pseudoprimes, "
                  "every frontier term reads its true run through the pool's "
                  "conditions (A216668's a(11) reads 17), and b = 6524 reads "
                  "A216668 run 4: a PRIME at p = 11 stops it")


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
# a(DRILL_N + 1) are published and seconds of device apart, and the run is
# BOUNDED before the filter of DRILL_N + 2 (`stop_n`), so no drill ever
# sweeps an open index (CLAUDE.md 0a): on A216666 a(6) = 809,652,228 from
# a(5) = 6,524, then a(7) = 30,717,523,794 -- with A229073 riding: its
# a(7) = 809,652,229 and a(8) = 30,717,523,795; on A216668 a(6) = 369,719
# from a(5) = 296 (the exception zone first), then a(7) = 457,578.
DRILL_N = {"A216666": 6, "A216668": 6}


def _promotion_drill():
    """A FIND MOVES THE FILTER and CARRIES THE LINE: the sweep resumes at
    the old boundary, floored into the new period with the clip at the
    boundary -- and when A229073 holds the filter, the find does NOT move
    it.  On scratch files, with REAL published terms as the finds."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="diff-promote-")
    path = str(pathlib.Path(tmp) / "c.json")
    rows = []
    fam = "A216668"
    n0 = DRILL_N[fam]
    found_x = ref.KNOWN[fam][n0]
    pol = policy(fam).at(path)
    c = Campaign(_args_for(fam, start_n=n0), ckpt=path, cursor=pol)
    before = (c.eng.n, c.eng.W, c.eng.q2, (c.eng.p1, c.eng.p2, c.eng.p3))
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
    c.boundary = found_x // c.eng.W + 5 * c.eng.seg_periods
    swept_old = c.boundary * c.eng.W
    c.follow_frontier(swept_old)
    if c.eng.n != n0 + 1:
        return False, f"PROMOTION FAIL: {fam} did not move to n = {n0 + 1}"
    if c.cover_x != swept_old or c.x_start() != swept_old:
        return False, (f"PROMOTION FAIL: {fam} did not carry the line to "
                       f"{swept_old} (cover {c.cover_x}, start {c.x_start()})")
    if c.k_min() != swept_old or c.j != swept_old // c.eng.W:
        return False, (f"PROMOTION FAIL: {fam} resumed at period {c.j}, clip "
                       f"{c.k_min()}; expected the period holding {swept_old}")
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
        Campaign(_args_for(fam, start_n=n0), ckpt=path, cursor=policy(fam).at(path))
        return False, f"PROMOTION FAIL: {fam} read a cursor stored at the wrong index"
    except ValueError:
        pass
    for ext in ("", ".bak"):
        if os.path.exists(path + ext):
            os.remove(path + ext)
    rows.append(f"{fam} n = {n0} -> {n0 + 1}: wheel {before[3]} -> "
                f"({c.eng.p1},{c.eng.p2},{c.eng.p3}), period {before[1]:.3g} "
                f"-> {c.eng.W:.3g}, carried to the old boundary {swept_old:.4g}")
    # A216666 with A229073 riding: a find of run r = n0 + 1 at filter n0
    # (A216666 a(n0) and a(n0 + 1) at once) leaves A229073's a(n0 + 1) --
    # an exact run of n0 -- open, so the filter STAYS at n0
    fam = "A216666"
    pol = policy(fam).at(path)
    c = Campaign(_args_for(fam, start_n=n0), ckpt=path, cursor=pol)
    if c.filter_n() != n0 or c.rider_low() != n0 + 1:
        return False, (f"PROMOTION FAIL: the A216666 drill opened at filter "
                       f"{c.filter_n()} with A229073 open from a({c.rider_low()})")
    W0, n_eng = c.eng.W, c.eng.n
    c.found[str(n0)] = c.found[str(n0 + 1)] = 10 ** 13 + 1
    c.found_rider[str(n0 + 2)] = 10 ** 13 + 2
    c.boundary = (10 ** 13) // c.eng.W + 2
    j_before = c.j = c.boundary
    c.follow_frontier(c.boundary * c.eng.W)
    if c.eng.n != n_eng or c.eng.W != W0 or c.filter_n() != n0 or c.j != j_before:
        return False, (f"PROMOTION FAIL: the rider did not hold the filter: "
                       f"n {c.eng.n}, filter {c.filter_n()}")
    if c.kind(n0) != "DISCOVERY" or c.kind(n0 + 1) != "CENSUS" or \
            c.kind(n0 + 2) != "DISCOVERY" or c.kind(n0 - 1) != "NEAR":
        return False, "PROMOTION FAIL: the held filter's taxonomy is wrong"
    # the exact run of n0 lands: the filter climbs to frontier + 1
    c.found_rider[str(n0 + 1)] = 10 ** 14 + 1
    c.follow_frontier(c.boundary * c.eng.W)
    if c.filter_n() != n0 + 2 or c.eng.n != n0 + 2:
        return False, f"PROMOTION FAIL: the filter did not climb past the rider ({c.filter_n()})"
    for ext in ("", ".bak"):
        if os.path.exists(path + ext):
            os.remove(path + ext)
    rows.append(f"A216666 with A229073 riding: a run-{n0 + 1} find at filter "
                f"{n0} keeps the filter at {n0} (A229073 a({n0 + 1}) needs an "
                f"exact run of {n0}), runs {n0} and {n0 + 2} stay finds and "
                f"{n0 + 1} census, and the filter climbs to {n0 + 2} once that "
                f"run lands")
    return True, ("promotion ok: " + "; ".join(rows) + " -- an interrupt "
                  "between the find and the promotion writes a checkpoint "
                  "that still opens, the classified line is carried to the "
                  "old boundary, the cursor round-trips, and a cursor stored "
                  "at the wrong index is REFUSED")


def _other_cursors_drill():
    """Every cursor policy reads all its declared keys through both readers
    and refuses a foreign one, and neither family reads the other's."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="diff-cursor-")
    path = str(pathlib.Path(tmp) / "c.json")
    seen = 0
    try:
        for fam in ref.FAMILIES:
            pol = policy(fam).at(path)
            for key in pol.readable():
                checkpoint.save(path, {"key": key, "j": 7, "u": 0, "k": 11})
                st, kind = pol.load()
                if not st or kind is None:
                    return False, f"CURSOR FAIL: {fam} will not read {key}"
                pol.refuse_mismatch()
                seen += 1
            for key in ("not-a-real-key",
                        config_key([f for f in ref.FAMILIES if f != fam][0])):
                checkpoint.save(path, {"key": key, "j": 7, "k": 11})
                st, _k = pol.load()
                if st:
                    return False, f"CURSOR FAIL: {fam} read the foreign key {key}"
                try:
                    pol.refuse_mismatch()
                    return False, f"CURSOR FAIL: {fam} did not refuse {key}"
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
    return True, (f"cursor policies ok: all {seen} declared keys pass BOTH "
                  f"readers on both families; a foreign key and the other "
                  f"family's key refuse")


def _families_stay_apart():
    """No two campaigns may read each other's cursor; the plan is admissible
    at every opening with an expected sweep near the unavoidable one; and
    the benchmark shape at each opening names the campaign's own plan
    (rule 5g)."""
    import score as _score
    keys = [config_key(f) for f in ref.FAMILIES]
    paths = [ckpt_path(f) for f in ref.FAMILIES]
    ledgers = [ledger_path(s) for s in list(ref.FAMILIES) + [RIDER]]
    if len(set(keys)) != len(keys) or len(set(paths)) != len(paths) \
            or len(set(ledgers)) != len(ledgers):
        return False, "FAMILY FAIL: two campaigns share a key, checkpoint or ledger"
    tight = []
    for fam in ref.FAMILIES:
        for f_, n in gpu.openings(fam):
            unit, p1, p2, p3, q2, pb = plan_for(f_, n)
            cpu.assert_unit(n, f_, unit)
            W = unit
            for q in gpu._wheel_primes(p1, p2, p3):
                W *= q
            _wide, pv = gpu._record_for(W // unit, q2, pb)
            floor_k = model.plan_floor(f_, n)
            ideal = model.expected_sweep(f_, n, floor_k, floor_k, 1.0)
            swept = model.expected_sweep(f_, n, floor_k, (floor_k // W) * W, pv * W)
            if swept > PLAN_WASTE_MAX * ideal:
                return False, (f"FAMILY FAIL: {f_} n = {n} plans a segment of "
                               f"{pv} periods x {W:.4g}, whose expected sweep "
                               f"to a confirmed find is {swept / ideal:.2f}x "
                               f"the unavoidable one")
            tight.append((ideal / swept, f_, n))
    lv = lambda z: tuple(z or ())               # noqa: E731
    seen = set()
    for row in _score.resolved_shapes():
        (label, f, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, _nu, pb) = row[:15]
        if not row[-1]:                          # an anchor shape, not a plan
            continue
        want = plan_for(f, n)
        got = (unit, lv(p1), lv(p2), lv(p3), q2, pb)
        if got != (want[0], lv(want[1]), lv(want[2]), lv(want[3]), want[4], want[5]):
            return False, (f"FAMILY FAIL: benchmark shape {label} names {got} "
                           f"and the campaign plans {want} at {f} n = {n}: "
                           f"re-freeze the shape at the plan (and log it)")
        seen.add((f, n))
    for fam, n in (("A216666", open_n("A216666")), ("A216666", 11),
                   ("A216668", open_n("A216668")), ("A216668", 24)):
        if (fam, n) not in seen:
            return False, f"FAMILY FAIL: no benchmark shape at {fam} n = {n} ({sorted(seen)})"
    tight.sort()
    return True, ("families stay apart: %d config keys, checkpoint files and "
                  "three ledgers (A229073's its own), the plan is admissible "
                  "at every opening, every plan's expected sweep to a "
                  "CONFIRMED find stays near the unavoidable one (the worst "
                  "is %s n = %d at %.2fx, against a %gx bound), and the "
                  "benchmark shapes at each family's opening and day-long "
                  "filter name exactly the configuration the campaign plans "
                  "there" % (len(keys), tight[0][1], tight[0][2],
                             1 / tight[0][0], PLAN_WASTE_MAX))


def _campaign_wiring_drill(fam):
    """Build a campaign and exercise everything the loop touches, without
    sweeping a whole period."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="diff-drill-")
    path = str(pathlib.Path(tmp) / "c.json")
    n0 = open_n(fam)
    pol = policy(fam).at(path)
    a = _args_for(fam)
    try:
        c = Campaign(a, ckpt=path, cursor=pol)
        if c.filter_n() != n0:
            return False, f"WIRING FAIL: filter {c.filter_n()}, expected {n0}"
        floor = c.x_start()
        want_floor = x_floor(fam, n0, ref.term(fam, ref.frontier(fam)))
        if floor != want_floor or (c.j, c.u) != (c.floor_period(), 0):
            return False, (f"WIRING FAIL: a fresh campaign starts at {floor} "
                           f"(j, u) = ({c.j}, {c.u}); expected {want_floor}")
        if c.k_min() != max(floor, cpu.k_floor(c.eng.q2, n0, fam) + 1):
            return False, f"WIRING FAIL: the clip is {c.k_min()}"
        unit, p1, p2, p3, q2, pb = plan_for(fam, n0)
        if (c.eng.n, c.eng.fam, c.eng.unit, c.eng.q2, c.eng.pv) != (n0, fam, unit, q2, pb) \
                or (c.eng.p1, c.eng.p2, c.eng.p3) != (p1, p2, p3) \
                or c.eng.prp != prp_count(fam):
            return False, "WIRING FAIL: the engine is not the PLANNED one"
        line = c.status_line()
        for want in ("swept to", fam, "census", f"periods [{c.floor_period()},"):
            if want not in line:
                return False, f"WIRING FAIL: status line lacks {want!r}"
        if c.rides and f"{RIDER} open a({n0 + 1})" not in line:
            return False, f"WIRING FAIL: the status line does not name the rider: {line}"
        if c.handle(floor + 1, CENSUS_FLOOR) is not False or \
                c.census.get(CENSUS_FLOOR) != 1:
            return False, "WIRING FAIL: a census run was not counted"
        if c.handle(floor + 3, CENSUS_FLOOR - 1) is not False or \
                CENSUS_FLOOR - 1 in c.census:
            return False, "WIRING FAIL: a run under the floor was counted"
        if c.zone() is not None:
            return False, f"WIRING FAIL: {fam} has a zone {c.zone()} at its frontier"
        if c.cover_zone() or c.zone_n != n0 or c.cover_zone():
            return False, "WIRING FAIL: the zone cover is not once per filter"
        jf = c.floor_period()
        fr = c.filter_n() - 1
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
        if not nxt or not nxt[0].startswith(f"a({c.frontier() + 1})"):
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
        nf = c.frontier() + 1
        if f"pool {w}" not in line or "HOST-BOUND" in line:
            return False, f"WIRING FAIL: status line pool fragment: {line}"
        if (f"P(a({nf}) under the claim) = 0%" not in line
                or f"next a({nf})" not in line):
            return False, f"WIRING FAIL: the status line reads the rungs off progress: {line}"
        c.pool.shutdown(wait=True, cancel_futures=True)
        c.pool, c.workers, c.args.workers = None, None, 1
        c.found[str(nf)] = int(floor + 4)
        aim = c.next_rung(c.swept_k())
        if c._lad.builds != builds + 1:
            return False, "WIRING FAIL: the frontier moved and the ladder was served from cache"
        if not aim or not aim[0].startswith((f"a({nf + 1})", "engine ceiling")):
            return False, f"WIRING FAIL: after finding a({nf}) the campaign aims at {aim}"
        c.found.pop(str(nf))
        if c.frontier() != nf - 1 or c.filter_n() != n0:
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
                  f"AT its floor ({TERM(fam)} = {floor:,}, inclusive) "
                  f"with the PLANNED engine at n = {n0}, wheel "
                  f"({p1},{p2},{p3}), depth {q2} and the Fermat stage on "
                  f"{prp_count(fam)} forms; its status line and rung ladder "
                  f"aim at a({n0})" + (f" with {RIDER} named" if fam == RIDER_OF else "")
                  + f", 75 ladder reads at a standing frontier cost 0 model "
                  f"rebuilds while a find costs exactly 1, the pool is sized "
                  f"from a live measurement ({ms['per_s']:,.0f} values/s x "
                  f"{1e6 * ms['cost']:.0f} us), back-pressure times the wait, "
                  f"the drain keeps the work cursor behind the classified "
                  f"launches, and the checkpoint round trips through both the "
                  f"normal save and the interrupt snapshot")


def _rediscovery_run_drill(fam):
    """THE REAL LOOP, END TO END, ON PUBLISHED GROUND: `Campaign.run` itself,
    on scratch files, opened at DRILL_N and bounded before DRILL_N + 2: it
    finds a(DRILL_N) and a(DRILL_N + 1), carries the line between them, and
    stops.  On A216666 each find also settles A229073 a(n + 1) = b + 1 --
    published at a(7), this project's free term at a(8) -- through the
    rider, with the A229073 record under m."""
    import json as _json
    import tempfile
    tmp = tempfile.mkdtemp(prefix="diff-rerun-")
    path = str(pathlib.Path(tmp) / "c.json")
    evid = str(pathlib.Path(tmp) / "evidence")
    n0 = DRILL_N[fam]
    want = {str(n): ref.KNOWN[fam][n] for n in (n0, n0 + 1)}
    if n0 + 2 > open_n(fam):
        return False, f"RERUN FAIL: {fam}'s drill would reach the open index"
    args = _args_for(fam, start_n=n0, stop_n=n0 + 2,
                     to=want[str(n0 + 1)] + 10 ** 7, heartbeat=3600.0)
    c = Campaign(args, ckpt=path, cursor=policy(fam).at(path), evid=evid)
    global WITNESS_ECM
    keep = WITNESS_ECM
    try:
        WITNESS_ECM = 0
        rc = c.run()
    finally:
        WITNESS_ECM = keep
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
        if len(ev["values"]) != n or ev["least_claim"]["swept_from"] > x \
                or ev["stopper"].get("p") != ref.nth_prime(n + 1):
            return False, f"RERUN FAIL: a({n})'s evidence is not self-contained"
        prod = 1
        for p, e in ev[f"{TERM(fam)}_factored"].items():
            prod *= int(p) ** int(e)
        if prod != x:
            return False, f"RERUN FAIL: a({n})'s factorization of the term is wrong"
        if fam == RIDER_OF:
            if ev["also_settles"] != [{"sequence": RIDER, "n": n + 1, "m": x + 1}]:
                return False, f"RERUN FAIL: a({n}) does not also settle {RIDER} a({n + 1})"
            if c.found_rider.get(str(n + 1)) != x + 1 or \
                    ref.term(RIDER, n + 1) != x + 1:
                return False, f"RERUN FAIL: {RIDER} a({n + 1}) is not b + 1"
    ok, msg = evidence.gate_names(evid, lambda rec: TERM(rec["sequence"]))
    if not ok:
        return False, "RERUN FAIL: " + msg
    return True, (f"rediscovery run ok: Campaign.run, opened at index {n0} of "
                  f"{fam} on scratch files, found a({n0}) = {want[str(n0)]:,}, "
                  f"carried the line, and found a({n0 + 1}) = "
                  f"{want[str(n0 + 1)]:,}, then stopped before the filter of "
                  f"a({n0 + 2})"
                  + (f", each also settling {RIDER} a(n + 1) = b + 1"
                     if fam == RIDER_OF else "")
                  + f"; each evidence file is named and keyed by the OEIS "
                  f"index, carries the term's factorization, every value, the "
                  f"stopper with its witness and the certificates, and passes "
                  f"the naming gate ({c.survivors:,} values classified, census "
                  f"{dict(sorted(c.census.items()))})")


def _zone_drill():
    """The exception zone can hold terms, and the host finds them: A216666's
    a(1)..a(5) lie in [1, 8192] -- the host's walk at n = 5 finds 6524
    first with run 5; A216668's a(4) = a(5) = 296; both walks agree with
    the oracle's."""
    q2 = 8192
    hits = cpu.prefix_hits("A216666", 5, q2, floor=5)
    if not hits or hits[0] != (6524, 5):
        return False, f"ZONE FAIL: the zone at A216666 n = 5 reads {hits[:3]}"
    oh = ref.prefix_hits("A216666", 5, 1, cpu.k_floor(q2, 5, "A216666"), floor=5)
    if [(x, r) for x, r in oh] != hits:
        return False, "ZONE FAIL: the oracle's zone walk differs from the engine's"
    h8 = cpu.prefix_hits("A216668", 5, q2, floor=5)
    if not h8 or h8[0] != (296, 5):
        return False, f"ZONE FAIL: the zone of A216668 n = 5 reads {h8[:3]}"
    one = cpu.prefix_hits("A216666", 1, q2, floor=1)
    if not one or one[0] != (1, 1):
        return False, f"ZONE FAIL: 1 is not first in the zone at n = 1: {one[:2]}"
    return True, (f"zone ok: A216666's a(5) = 6524 (run 5) and a(1) = 1 lie in "
                  f"the exception zone [1, {q2}] and the host's walk finds them "
                  f"first, agreeing with the oracle's walk; A216668's a(4) = "
                  f"a(5) = 296 likewise")


def _rider_drill():
    """A229073 rides A216666: a find of run r settles A229073 a(r + 1) =
    b + 1 exactly when that index is open, never at a(r) or below, never
    twice; the free terms a(8), a(9) are the published A216666 a(7), a(8)
    plus one; and the rider's letter is m, in a record of its own when an
    exact run lands below A216666's frontier."""
    op = frozenset(r for r in range(9, 41))
    x = 10 ** 15 + 1
    if rider_settles("A216666", x, 9, op) != {"sequence": RIDER, "n": 10, "m": x + 1}:
        return False, "RIDER FAIL: a run of 9 does not settle A229073 a(10)"
    if rider_settles("A216666", x, 11, op) != {"sequence": RIDER, "n": 12, "m": x + 1}:
        return False, "RIDER FAIL: a run of 11 does not settle A229073 a(12)"
    if rider_settles("A216666", x, 8, op) is not None:
        return False, "RIDER FAIL: a run of 8 settled a published A229073 term"
    if rider_settles("A216668", x, 9, op) is not None:
        return False, "RIDER FAIL: A216668 settled the rider"
    for n in (8, 9):
        if ref.term(RIDER, n) != ref.KNOWN["A216666"][n - 1] + 1:
            return False, f"RIDER FAIL: A229073 a({n}) is not A216666 a({n - 1}) + 1"
    stop = {"p": 23, "value": 9, "why": "composite", "wants_prime": True, "factor": 3}
    ev = evidence_record("A216666", 10 ** 6, 2, {"x": True}, stop, {}, [], [],
                         {"sequence": RIDER, "n": 3, "m": 10 ** 6 + 1}, {}, "drill",
                         filter_n=2)
    ok, msg = evidence.check_names(ev, "m")
    if not ok or ev["sequence"] != RIDER or ev["m"] != 10 ** 6 + 1 or ev["b"] != 10 ** 6:
        return False, f"RIDER FAIL: a rider-only record reads {msg} {ev.get('sequence')}"
    return True, ("rider drill ok: an A216666 find of run r settles A229073 "
                  "a(r + 1) = b + 1 exactly when that index is open (runs 9 "
                  "and 11 do; 8 does not; A216668 never does); the free terms "
                  "a(8), a(9) are A216666's a(7), a(8) plus one; and a "
                  "rider-only record is A229073's, under m, with b beside it")


def _rider_campaign_drill():
    """THE HELD FILTER IN THE REAL LOOP, on published ground: A216666 opened
    at index 1 on scratch files with A229073 known only to a(3) (so its
    a(4), a(5), a(6) -- exact runs 3, 4, 5 -- are open), bounded before
    filter 6, the census floor lowered to 1 for the drill (these runs are
    under the campaign's floor of 6; the exception zone covers them).
    b = 1 runs to 4 (2^11 - 1 = 23 * 89): A216666 a(1)..a(4) and A229073
    a(5) = 2 at once, which leaves A229073 a(4) open -- so the filter must
    be HELD at 3 (not 5), where b = 2 (run exactly 3: 3^7 - 2^7 = 29 * 71)
    is A229073's a(4) = 3; only then does it climb to 5 and find A216666
    a(5) = 6524 with A229073 a(6) = 6525.  Every integer is the published
    term."""
    import tempfile
    global CENSUS_FLOOR
    tmp = tempfile.mkdtemp(prefix="diff-rider-")
    path = str(pathlib.Path(tmp) / "c.json")
    evid = str(pathlib.Path(tmp) / "evidence")
    keep = CENSUS_FLOOR
    filters = []
    try:
        CENSUS_FLOOR = 1
        args = _args_for("A216666", start_n=1, stop_n=6, to=10 ** 4,
                         heartbeat=3600.0)

        class _Watch(Campaign):
            def _follow_once(self, old_boundary_x):
                filters.append(self.filter_n())
                return super()._follow_once(old_boundary_x)
        c = _Watch(args, ckpt=path, cursor=policy("A216666").at(path), evid=evid)
        c._rider_top = 3                   # the drill's A229073: a(1)..a(3)
        c.eng = c._build_engine(c.filter_n())
        c.j, c.boundary = c.floor_period(), c.floor_period()
        rc = c.run()
    finally:
        CENSUS_FLOOR = keep
    got6 = {k: int(v) for k, v in c.found.items()}
    gotr = {k: int(v) for k, v in c.found_rider.items()}
    want6 = {**{str(n): 1 for n in range(1, 5)}, "5": ref.KNOWN["A216666"][5]}
    wantr = {str(n): ref.KNOWN_DERIVED[RIDER][n] for n in (4, 5, 6)}
    if rc != 0 or got6 != want6 or gotr != wantr:
        return False, (f"RIDER CAMPAIGN FAIL: found A216666 {got6} and A229073 "
                       f"{gotr}; published {want6} and {wantr}")
    if filters[:3] != [3, 5, 6]:
        return False, (f"RIDER CAMPAIGN FAIL: the filters after the finds were "
                       f"{filters}, not held at 3 then 5 then 6")
    ok, msg = evidence.gate_names(evid, lambda rec: TERM(rec["sequence"]))
    if not ok:
        return False, "RIDER CAMPAIGN FAIL: " + msg
    return True, ("rider campaign ok: Campaign.run from A216666's index 1 on "
                  "scratch files found a(1)..a(4) = 1 at once (b = 1 runs to "
                  "4) with A229073 a(5) = 2, then -- the filter HELD at 3, "
                  "not 5, while A229073's exact run 3 was open -- A229073 "
                  "a(4) = 3, and only then A216666 a(5) = 6524 with A229073 "
                  "a(6) = 6525: every one the published term, each A229073 "
                  "integer in a record under m")


def _free_terms_drill():
    """The free terms re-verified through the launcher's own protocol and
    compared with the records in evidence/: the same integers, indices,
    runs, values, stoppers and proof routes."""
    import json as _json
    rows = []
    for seq, name, ev in free_evidence(witness=False):
        letter = TERM(seq)
        ok, msg = evidence.check_names(ev, letter)
        if not ok:
            return False, f"FREE TERMS FAIL: {name}: {msg}"
        f = pathlib.Path(EVID) / name
        if not f.exists():
            return False, f"FREE TERMS FAIL: {name} is not in evidence/"
        with open(f) as fh:
            disk = _json.load(fh)
        for key in ("sequence", "forms", letter, "oeis_terms", "run", "settles",
                    "values", "proof_routes", "unproved",
                    "composite_witnesses"):
            if disk.get(key) != _json.loads(_json.dumps(ev.get(key))):
                return False, f"FREE TERMS FAIL: {name}'s {key} differs from the re-derivation"
        ds, es = disk["stopper"], ev["stopper"]
        if (ds["p"], ds["value"], ds["why"]) != (es["p"], es["value"], es["why"]):
            return False, f"FREE TERMS FAIL: {name}'s stopper differs"
        fac = ds.get("factor")
        if ds["why"] == "composite" and not (
                (fac and 1 < fac < ds["value"] and ds["value"] % fac == 0)
                or (fac is None and ds.get("fermat_base2_fails")
                    and pow(2, ds["value"] - 1, ds["value"]) != 1)):
            return False, f"FREE TERMS FAIL: {name}'s stopper witness does not check"
        rows.append(f"{seq} a({','.join(map(str, ev['settles']))}) = "
                    f"{ev[letter]:,} ({ev['proof_routes']}, unproved "
                    f"{ev['unproved'] or 'none'})")
    return True, ("free terms ok: " + "; ".join(rows) + " -- each re-derived "
                  "through verify and certify_run and identical to its record")


def _slow_step_drill():
    """A slow host step is announced with its label and kept in [STATUS]
    (CLAUDE.md 5k): a survivor whose handling takes 0.12 s against a 0.1 s
    threshold, inside the real item wrapper."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="diff-slow-")
    path = str(pathlib.Path(tmp) / "c.json")
    lines = []
    c = Campaign(_args_for("A216668"), ckpt=path, cursor=policy("A216668").at(path))
    c.hc = HostCost(say=lambda t, m: lines.append((t, m)), hb=c.hb, warn_s=0.1)
    k = c.x_start() + 7
    with c.hc.item(f"classifying {c.term} = {k} (run 3)"):
        time.sleep(0.12)
        c.handle(k, 3)
    warns = [m for t, m in lines if t == "WARN"]
    st = c.status_line()
    ok = (len(warns) == 1 and f"{c.term} = {k}" in warns[0]
          and f"{c.term} = {k}" in st and c.hc.n == 1)
    return ok, ("slow-step drill: a value whose handling takes 0.12 s against "
                "a 0.1 s threshold gets one [WARN] naming it and [STATUS] "
                "keeps it as the slowest step" if ok else
                f"SLOW STEP FAIL: warns {warns}, status {st}")


def _evidence_names_drill():
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        ev = dict(evidence.header(fam, ref.FAMILIES[fam]["forms"], TERM(fam),
                                  ref.KNOWN[fam][top], [top]), settles=[top])
        ok, msg = evidence.check_names(ev, TERM(fam))
        if not ok:
            return False, f"EVIDENCE NAMES FAIL: {fam} writer: {msg}"
    d = ref.DERIVED[RIDER]
    ev = dict(evidence.header(RIDER, d["forms"], d["term"], 7, [3]), settles=[3])
    ok, msg = evidence.check_names(ev, "m")
    if not ok:
        return False, f"EVIDENCE NAMES FAIL: {RIDER} writer: {msg}"
    os.makedirs(EVID, exist_ok=True)
    return evidence.gate_names(EVID, lambda rec: TERM(rec["sequence"]))


def selftest(fam="A216666"):
    t0 = time.time()
    rows = []
    for g in (ref.GATES + cpu.GATES + gpu.GATES + model.GATES
              + certificate.GATES + ceiling.GATES):
        rows.append(g())
    rows.append(drills.event_kind_drill(
        lambda c: event_kind(*c), _event_cases()))
    for d in drills.standard(pool_factory=_pool_factory,
                             cursor=policy("A216666")):
        rows.append(d)
    rows.append(hostcost.drill())
    rows.append(_other_cursors_drill())
    for d in (_ceiling_drill, _zone_drill, _canary_hunt, _protocol_drill,
              _certificate_drill, _resume_drill, _promotion_drill,
              _classification_drill, _stop_on_discovery_drill,
              _families_stay_apart, _rider_drill, _rider_campaign_drill,
              _free_terms_drill, _slow_step_drill):
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
    fam = ref.family(fam)
    pol = policy(fam)
    st, kind = pol.load(warn=lambda m: log("STAGE", m))
    if not st:
        log("STATUS", f"no checkpoint for {config_key(fam)} yet; a fresh "
                      f"campaign opens at filter n = {open_n(fam)}, "
                      f"{TERM(fam)} = {ref.term(fam, ref.frontier(fam)):,}"
                      + (f" ({RIDER} riding, open from a({rider_known_top() + 1}))"
                         if fam == RIDER_OF else ""))
        return 0
    cen = {int(r): int(c) for r, c in st.get("census", {}).items()}
    front = ref.frontier(fam)
    for n in st.get("found", {}):
        front = max(front, int(n))
    log("STATUS", "  ".join([
        f"{fam} filter n = {st.get('n')}",
        f"swept to {TERM(fam)} = {int(st['k']):,}",
        f"work cursor period {int(st['j'])} u = {int(st.get('u', 0))}",
        census_str(cen, CENSUS_FLOOR, front),
        f"finds {st.get('discoveries', 0)}",
        f"near {st.get('near', 0)}",
        f"survivors {int(st.get('survivors', 0)):,}",
        f"elapsed {float(st.get('elapsed', 0)) / 3600:.2f} h",
        f"saved {st.get('saved', '?')}"]))
    for n, k in sorted(st.get("found", {}).items(), key=lambda x: int(x[0])):
        log("STATUS", f"  found: {fam} a({n}) = {TERM(fam)} = {int(k):,}")
    for n, k in sorted(st.get("found_rider", {}).items(), key=lambda x: int(x[0])):
        log("STATUS", f"  found: {RIDER} a({n}) = m = {int(k):,}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--family", default="A216666",
                    help="which sequence to hunt: A216666 (default; A229073 "
                         "rides it, and --family A229073 runs it) or A216668")
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
                         "(1 ms against a launch of tens of ms costs a few "
                         "percent of the rate)")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 2 --workers 1 --worker-ramp 1.0")
    ap.add_argument("--fresh", action="store_true",
                    help="discard an existing cursor deliberately")
    args = ap.parse_args(argv)
    asked = str(args.family).upper()
    args.family = ref.family(args.family)
    if asked in ref.ALIASES:
        log("STAGE", f"--family {asked}: {asked} rides {args.family}'s line "
                     f"(m = b + 1 with an exact run); the campaign below "
                     f"settles both")
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
    policy(args.family).refuse_mismatch(
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
