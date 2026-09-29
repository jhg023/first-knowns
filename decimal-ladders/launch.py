"""The decimal-ladders campaign: A305740 (10^m*k + 1), A153431 (m*10^k + 1).
In the code's own notation: the least x with 10^j*x + 1 prime for every j
in J(F, n).

    python launch.py --selftest            the full gate battery (must end ALL GREEN)
    python launch.py --family A305740      the hunt: indefinite, resumable
    python launch.py --family A153431      the other family
    python launch.py --status              read the checkpoint and say where it is

TWO FAMILIES, OPPOSITE LETTERS, ONE CAMPAIGN AT A TIME.  A305740 asks for
the smallest k with 10^m*k + 1 prime for m = 1..n; A153431 for the smallest
m with m*10^k + 1 prime for k = 0..n.  The code calls the swept integer x
and the exponent j in both; every line a person reads uses the entry's own
letter for the term (TERM: k for A305740, m for A153431).  Each family has
its own checkpoint under its own config key.

THE LINE.  The published term is x itself, so every filter sweeps ONE line,
and what a find changes is the FILTER: the kill sets grow (one more exponent)
and the forced unit may grow, the cursor carries the classified line across
(every survivor of a closed segment was run to n + 8, and the filter-(n+1)
sieve keeps a subset of the filter-n sieve's survivors), and the engine is
rebuilt at the new filter's PLAN.

THE OPENINGS (CLAUDE.md 5g, step 1 -- the test plan for every default
below).  Every filter a campaign opens at or promotes into, with the plan
the campaign runs there -- decl_gpu.MEASURED_PLANS, the measured best of
the model's shortlist, ranked on EXACT per-launch candidate counts
(OPTIMIZATION_LOG.md Measurements 8 and 12); the depth is plan_q2's and the
record the engine's own choice -- and its steady rate:

    A305740   median k    unit   wheel                 window  record  k/s
    n = 13    2.6e14      7      to 43 (9 primes)      192     narrow  5.01e15
        14    9.9e15      7      to 47 (10)            192     narrow  1.86e16
        15    7.8e17      7      to 53 (11)            224     narrow  7.64e16
        16    1.0e20      119    to 61 (11)            224     narrow  4.02e17
        17    7.5e21      119    to 61 (12)            224     narrow  1.19e18
        18    8.6e23      2261   to 67 (12)            224     wide    5.11e18
        19    4.7e25      2261   to 71 (12)            256     wide    9.44e18

    A153431   median m    unit   wheel                 window  record  m/s
    n = 14    1.3e18      14     to 47 (11)            256     narrow  1.61e17
        15    1.6e20      238    to 59 (11)            224     narrow  8.65e17
        16    1.2e22      238    to 67 (12)            256     narrow  2.65e18
        17    1.4e24      4522   to 67 (12)            256     narrow  1.05e19
        18    7.5e25      4522   to 67 (13)            256     wide    2.04e19

BENCHMARKS.md has the frozen shapes.  The early filters are minutes (A305740 a(13)..a(17),
A153431 a(14)..a(16)); the hunt proper is A305740 a(18) and A153431 a(17).

A FIND MOVES THE FILTER, NOT THE LINE; A FIND MAY BE A RIDER.  The sieve at
filter n keeps a superset of what the filter-(n+1) sieve keeps, so an x
whose run passes n settles every term up to its run at once, decided by
running the chain on (decl_reference.run_length).  And an A305740 find x
with x + 1 prime is ALSO A153431 at the same indices, whenever that entry
has not yet settled them (decl_reference G2d: equality exactly when
A305740(n) + 1 is prime); the evidence records it under `also_settles`.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no --to this runs to the
engine's enforced ceiling, huntlib.ceiling.K_CEIL = 1e40 on x, the last
rung.  Every classification is a strong probable-prime chain from the first
filter (the proof crossing, 3.3e11 at n = 13, is under both frontiers); a
DISCOVERY is proved by CERTIFICATE on its own structure: V - 1 = 10^j*x is
factored once x is, so BLS75 Theorem 1 proves every value of a run from ONE
factorization of x.  `--to` and `--stop-on-discovery` are the only stops.

THE TAXONOMY (CONVENTIONS.md "the discovery protocol").  A survivor is an x
with a run r, counted in the entry's own index (A153431's run of an x whose
x + 1 is composite is -1):

  DISCOVERY  r > frontier: x settles a(frontier+1) ... a(r) at once, each
             logged once, evidenced under the FIRST index it settles.
             Verified three ways plus a witness for the composite that stops
             the run, and a re-verified certificate for every value.
  NEAR       r == frontier: one condition short of the open term.  One line
             with its campaign ordinal, verified by the cheap legs, never
             evidenced.
  CENSUS     CENSUS_FLOOR <= r < frontier: counted in [STATUS], never narrated.
  None       r < CENSUS_FLOOR: noise, not counted.

TWO CURSORS, BECAUSE COVERAGE IS COARSER THAN WORK (CONVENTIONS.md).  The
engine sieves a SEGMENT of periods at once and its candidates come out in
(t, s, u, period) order, so COVERAGE (`boundary`) advances one segment at a
time and is the only thing a least-claim rests on; WORK (`j`, `u`)
advances every launch.  Values classified mid-segment are held IN THE
CHECKPOINT and narrated in x order when the segment closes.

THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER, at
start and at every promotion (Campaign.size_pool), ramped one worker at a
time at below-normal priority; the device may run at most BACKLOG_LAUNCHES
ahead of the pool, and [STATUS] says HOST-BOUND and by how much when it
waits.  Throttles: `--workers`, `--gpu-yield-ms`, `--gentle`.  No machine
setting is ever changed on the owner's behalf.
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

import decl_gpu as gpu                                          # noqa: E402
import decl_model as model                                      # noqa: E402
import decl_reference as ref                                    # noqa: E402
import decl_search as cpu                                       # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")


def term_letter(fam):
    """THE LETTER THE OEIS USES FOR THE TERM (rule 5i): k for A305740 ("the
    smallest k such that 10^m*k + 1 is prime"), m for A153431 ("the
    smallest number m such that all n+1 numbers m*10^k+1 ...").  Every
    surface a person reads uses it; the engines call the integer x and the
    checkpoint stores the cursor as "k", which is nobody's problem."""
    return ref.letter(fam)


def form_less_one(fam, e=None):
    """A value less one in the entry's own letters AND order (rule 5i):
    10^e*k for A305740, m*10^e for A153431.  With no e, the exponent is the
    entry's own letter -- the other of k and m."""
    t = term_letter(fam)
    if e is None:
        e = "m" if t == "k" else "k"
    return f"10^{e}*{t}" if t == "k" else f"{t}*10^{e}"


PLAN_VERSION = "p1"               # bump when plan_for's answer changes
ENGINE_VERSION = "v1"
# No predecessor cursor: nothing has opened a campaign yet.  The list is
# kept (empty) because CursorPolicy takes it and because the moment an old
# key exists it belongs HERE and nowhere else (CONVENTIONS.md "Reading an
# existing cursor").
PREVIOUS_ENGINES = ()


@functools.lru_cache(maxsize=None)
def plan_for(fam, n):
    """(unit, p1, p2, p3, q2, pb) for filter n of family F -- the
    configuration the campaign runs there, and the fastest correct one it
    has (CLAUDE.md 5g): decl_gpu.plan chooses the wheel, the depth and the
    window together by expected clock to a confirmed find.  The RECORD is
    not planned here: the engine chooses it from the wheel and window it is
    handed, at every build.

    CACHED, AND THAT IS NOT AN OPTIMISATION DETAIL: planning prices a dozen
    wheels against the odds model, and `x_floor` / `k_min` / `state` reach
    it every launch -- a per-launch cost that does not scale with the work
    is OPTIMIZATION.md 2.14's trap (lcm-ladders paid 34 ms a launch for it).
    """
    fam = ref.family(fam)
    unit = cpu.forced_unit(n, fam)
    p1, p2, p3, q2, pb = gpu.plan(n, fam, unit)
    return unit, p1, p2, p3, q2, pb


def x_floor(fam, n, frontier_x):
    """Where the sweep for a(n) starts: the previous term (monotonicity,
    free), the engine's own floor, or -- A305740 only -- the SIBLING's
    floor, whichever is highest."""
    fam = ref.family(fam)
    _u, _a, _b, _c, q2, _pb = plan_for(fam, n)
    return max(int(frontier_x), cpu.k_floor(q2, n, fam) + 1,
               sibling_floor(fam, n))


# THE SIBLING'S FLOOR.  If x had an A305740 run of n or more, y = 10x would
# meet A153431's condition at index n - 1 (10^k*y + 1 = 10^(k+1)*x + 1 for
# k = 0..n-1), so A153431(n - 1) <= 10x: NO x below ceil(A153431(n - 1)/10)
# can be A305740(n), by the sibling's own least-claim (decl_reference G2d
# checks the relation on every published index).  So once A153431(n - 1)
# is settled -- published, in FOUND, or a verified first occurrence in this
# project's evidence -- A305740's sweep for a(n) starts there, and the
# region below it is settled by that theorem, not swept (the evidence says
# so under least_claim.sibling_floor).  The relation bounds A153431 from
# ABOVE, so A153431 gets nothing back.  Hunting A153431 first therefore
# moves every A305740 floor: at the medians, ~16% of the n = 18 leg
# (A153431 a(17) ~ 1.4e24 puts A305740 a(18)'s floor at ~1.4e23).
SIBLING = {"A305740": ("A153431", 1)}      # fam: (sibling, index offset)


def settled_term(fam, idx):
    """fam(idx) if it is settled: published, in FOUND, or the integer of a
    verified first-occurrence record in evidence/ (the only files there);
    None if not."""
    fam = ref.family(fam)
    v = ref.KNOWN[fam].get(idx) or ref.FOUND[fam].get(idx)
    if v:
        return int(v)
    import glob
    import json
    for path in sorted(glob.glob(os.path.join(EVID, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(rec, dict) and rec.get("sequence") == fam:
            v = (rec.get("oeis_terms") or {}).get(str(idx))
            if v is not None:
                return int(v)
    return None


@functools.lru_cache(maxsize=None)
def sibling_floor(fam, n):
    """ceil(A153431(n - 1) / 10) for A305740 when that term is settled,
    else 0.  Read once per process (the families run one at a time)."""
    fam = ref.family(fam)
    if fam not in SIBLING:
        return 0
    sib, off = SIBLING[fam]
    t = settled_term(sib, int(n) - off)
    return 0 if t is None else -(-int(t) // 10)


def open_n(fam):
    """The filter a FRESH campaign of this family opens at."""
    return max(ref.KNOWN[ref.family(fam)]) + 1


def c_front(fam):
    """The frontier term a fresh campaign of `fam` starts from."""
    fam = ref.family(fam)
    return ref.KNOWN[fam][max(ref.KNOWN[fam])]


# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a segment; the
# save is further rate-limited by CKPT_MIN_S.
CKPT_LAUNCHES = 32
CENSUS_FLOOR = 8                  # runs shorter than this are not even counted
# THE HOST POOL IS SIZED FROM A MEASUREMENT AT THE CAMPAIGN'S OWN FILTER
# (CLAUDE.md 5f and 5g): WORKERS_DEFAULT survives only as the fallback for a
# drill with no device, and `--workers` still overrides.
WORKERS_DEFAULT = 2
POOL_MARGIN = 2.0                 # workers = ceil(core-s per s x this)
CAL_MIN_SURVIVORS = 500           # the sample the sizing is measured on ...
CAL_MIN_S = 1.0                   # ... over at least this much device time
CAL_MAX_S = 4.0                   # and at most this much
CAL_SEGMENTS = 256
CAL_SAMPLE = 2000                 # survivors timed through sprp_run
# BACK-PRESSURE: the device may run at most this many launches ahead of
# the pool; past it the loop waits for the oldest launch, visibly.
BACKLOG_LAUNCHES = 64
CKPT_MIN_S = 2.0
CKPT_COST_FRACTION = 0.02
PERIOD_LOG_S = 60.0
WORKER_RAMP_S = _pool.RAMP_S
CHUNK = 256                       # survivors per pool task


def config_key(fam, engine=None):
    fam = ref.family(fam)
    # The wheel is NOT in the key: it is planned per filter, and the filter
    # is in the STATE.  What is in the key is what would change the meaning
    # of a stored cursor for a GIVEN filter: the engine and planner versions
    # and the launch decomposition that gives the work cursor its units.
    # The per-filter configuration is ASSERTED on load (n, W).
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
# takes a key list of its own: the campaign's load, --status, and the
# refusal in main() (CONVENTIONS.md "Reading an existing cursor").
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
    evidenced, so nobody reads its stopper's factor, and a bounded rho plus
    ECM on a 40-digit stopper is device-idle time bought for nothing.  The
    stopper is still shown composite -- that leg is what bounds the run.

    Everything is stated on x, the published term; the value with exponent
    j is 10^j*x + 1.

    1. huntlib's Miller-Rabin chain (a proof below the proof crossing, a
       thirteen-base strong probable-prime chain above it -- where the
       certificate, not this leg, is the proof);
    2. sympy's BPSW, an independent implementation, which must agree on the
       run LENGTH and not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense x line and uses no wheel at all, must
       agree that this x survives a sieve at a DIFFERENT depth from the
       campaign's, at the filter the run reaches;
    plus a factor witness for the composite that STOPS the run.
    """
    fam = ref.family(fam)
    x = int(x)
    js = ref.exponents(fam, run)
    legs = {"mr_chain": all(mr_is_prime(10 ** j * x + 1) for j in js),
            "sympy_bpsw": ref.run_length(fam, x, cap=run + 1) == run,
            "resieve_other_wheel": cpu.CpuEngine(run, fam, q2=4096).survives(x)}
    stop_j = run + 1
    stop = 10 ** stop_j * x + 1
    legs["stopper_composite"] = not mr_is_prime(stop)
    ok = all(legs.values())
    wit = (stopper_witness(stop)
           if witness and legs["stopper_composite"] else None)
    return ok, legs, {"exponent": stop_j, "value": stop, "factor": wit,
                      "why": "composite"}


# Below this a stopper's full factorization is seconds at worst, so
# huntlib's factor_witness (which ends in sympy's factorint) may be asked;
# above it only the BOUNDED chain runs.
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
    """A checkable primality certificate for every value 10^j*x + 1 of the
    run: ({str(j): proof}, [the j left UNPROVED]).

    RULE 5h'S BEST CASE.  V - 1 = 10^j * x = 2^j * 5^j * x is completely
    factored the moment x is, so ONE factorization of x factors every
    value's N - 1 at once and BLS75 Theorem 1 proves the whole run
    (A153431's x + 1 included: N - 1 = x).  Below the deterministic bound
    huntlib.certificate.prove answers with the deterministic test, which IS
    the proof there.  A prime factor of x past the bound is admitted with a
    SUBPROOF of its own.  Every proof is RE-VERIFIED from scratch before it
    is returned.
    """
    from sympy import primerange
    fam = ref.family(fam)
    x = int(x)
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
    for j in (ref.exponents(fam, run) if only is None else only):
        facN = dict(fac)
        if j:
            facN[2] = facN.get(2, 0) + int(j)
            facN[5] = facN.get(5, 0) + int(j)
        N = 10 ** int(j) * x + 1
        proof = certificate.prove(N, fac=facN)
        if proof is None:
            proof = certificate.prove(N)
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
        certs[str(j)] = proof
        if proof is None:
            unproved.append(int(j))
    return certs, unproved


def also_settles(fam, x, run, settles, known=None):
    """What a find settles in the OTHER entry, as evidence records.

    A305740 -> A153431: A153431(n) = A305740(n) exactly when A305740(n) + 1
    is prime (decl_reference G2d) -- the stricter condition adds only the
    form x + 1, and nothing below the least x meeting the weaker one can
    meet the stricter.  So an A305740 find x with x + 1 prime settles
    A153431 at every index it settles that A153431 has not published.
    A153431 -> A305740 settles nothing: A305740(n) may be smaller.
    `known` overrides the published table (the drill uses it).
    """
    fam = ref.family(fam)
    if fam != "A305740" or not mr_is_prime(int(x) + 1):
        return []
    known = ref.KNOWN["A153431"] if known is None else known
    return [{"sequence": "A153431", "n": int(n), "value": int(x),
             "claim": f"A305740({n}) + 1 = {int(x) + 1} is prime, so "
                      f"A153431({n}) = A305740({n}) (decl_reference G2d)"}
            for n in settles if n not in known]


# ----------------------------- classification -------------------------------

def sprp_run(x, fam, cap, floor=CENSUS_FLOOR):
    """Run of x (in the entry's index), screened with a base-2 strong test
    and CONFIRMED with the full chain wherever the answer matters.

    A failed base-2 test is a PROOF of compositeness, so the first pass can
    only overstate a run, never understate it.  Runs below the census floor
    are never looked at again; a run at or above it is recomputed with the
    full base set.  NOT capped at the filter: a survivor whose run passes
    the filter is a RIDER and its run is what it is.  `cap` bounds the chain
    (the launcher passes filter + 8).
    """
    j0 = ref.j0(fam)
    cap = int(cap)
    j = j0
    while j <= cap and sprp_base2(10 ** j * x + 1):
        j += 1
    r = j - 1
    if r >= floor:
        j = j0
        while j <= cap and mr_is_prime(10 ** j * x + 1):
            j += 1
        r = j - 1
    return r


def _classify_chunk(task):
    """Pool worker: runs of a chunk of survivors, in order.  Module-level
    and self-contained so it survives Windows spawn; touches no GPU."""
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
    """Hand a launch's survivors to the pool: [(ks_chunk, future)] in
    survivor order; with no pool the chunk is classified right here."""
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
        # `ckpt`/`cursor`/`pool` are overridable so the selftest can build a
        # campaign against a scratch file and exercise the wiring without
        # sweeping.
        self.args = args
        self.fam = ref.family(args.family)
        self.oeis = self.fam
        self.TERM = term_letter(self.fam)
        self.key = config_key(self.fam)
        self.ckpt = ckpt or ckpt_path(self.fam)
        self.cursor = cursor or _POLICIES[self.fam]
        self.pool = pool
        self.found = {}                # str(n) -> x found by THIS campaign
        self.census = {}               # run length -> count
        self.passed = []
        self.elapsed = 0.0
        self.discoveries = 0
        self.near = 0
        self.survivors = 0
        self._stored_n = None
        self.j = None
        self.u = 0
        self.pending = []
        self.pending_census = {}       # run -> count, the open segment's
        self._stored_w = 0
        self.hb = Heartbeat(interval=args.heartbeat)
        self._lad = LiveLadder(self._build_ladder)
        self._t0 = time.time()
        self.workers = None
        self._sizing = None
        self._hostwait = 0.0
        # the x below which THIS filter's least-claim rests on the previous
        # filter's classified sweep rather than its own (follow_frontier)
        self.cover_x = 0
        self._hw_ref = (0.0, time.time())
        self._hostbound_logged = False
        self._ckpt_t = 0.0
        self._ckpt_every_s = CKPT_MIN_S
        self._plog_t = 0.0
        self._plog_n = 0
        self._snapshot = None
        self._proof_logged = None
        self._load_kind = None
        self.loaded = self.load()
        self.eng = self._build_engine(self.filter_n())
        # STORE THE UNIT NEXT TO THE NUMBER AND ASSERT IT ON LOAD
        # (OPTIMIZATION.md 2.9): the period really does change from filter
        # to filter here (the unit grows 7 -> 119 -> 2261).
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
        # --stop-on-discovery means THIS RUN's find: latched against the
        # count at run start (CONVENTIONS.md "Stopping a run")
        self._discoveries_at_start = self.discoveries
        self.mark_boundary()

    def _build_engine(self, n):
        """The engine for filter n, PLANNED (never a stored constant)."""
        unit, p1, p2, p3, q2, pb = plan_for(self.fam, n)
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

    def model_floor(self):
        """The x the odds model conditions a(filter) on: the frontier term,
        or the sibling's floor where that is higher (nothing below it can
        be the term, so the model must not spend probability there)."""
        return max(int(self.frontier_k()),
                   sibling_floor(self.fam, self.filter_n()))

    def x_start(self):
        """The floor of THIS filter's sweep, from the LIVE frontier."""
        return x_floor(self.fam, self.filter_n(), self.frontier_k())

    def floor_period(self):
        return self.x_start() // int(self.eng.W)

    def k_min(self):
        """The clip: the floor while the sweep is inside the segment that
        contains it, none after."""
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
        REBUILT only when it moves (OPTIMIZATION.md 2.14)."""
        return self._lad.get(self.frontier(), self.model_floor(),
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
        """One [MILESTONE] per filter when the sweep passes the proof
        crossing (here: at once -- it is below both frontiers)."""
        if self._proof_logged == self.filter_n():
            return
        pc = self.proof_crossing()
        if k >= pc:
            self._proof_logged = self.filter_n()
            log("MILESTONE",
                f"past the proof crossing of {self.oeis} at filter n = "
                f"{self.filter_n()}, {self.TERM} = {pc:.4g}: "
                f"{form_less_one(self.fam, self.filter_n())} + 1, "
                f"the top value, exceeds the deterministic Miller-Rabin bound, "
                f"so classification is a thirteen-base strong probable-prime "
                f"chain (the census is counted and a NEAR is a health check "
                f"either way) and a DISCOVERY is proved by BLS75 Theorem 1 on "
                f"each value less one, {form_less_one(self.fam)} "
                f"(certify_run); the ceiling is "
                f"{self.TERM} < {cpu.k_ceil(self.filter_n(), self.fam):.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "plan": PLAN_VERSION,
                "family": self.fam,
                # THE FILTER IS PART OF THE CURSOR: each n has its own
                # wheel, unit and period
                "n": int(self.eng.n),
                "q2": int(self.eng.q2),
                "wheel": [self.eng.p1, self.eng.p2, self.eng.p3],
                "unit": int(self.eng.unit),
                "j": int(self.j),
                "u": int(self.u),
                "seg_periods": int(self.eng.seg_periods),
                "launches_per_segment": int(self.eng.launches_per_segment),
                "W": int(self.eng.W),
                # the COVERAGE claim: every x in [k_start, k) is swept
                "k": int(self.swept_k()),
                "k_start": int(self.x_start()),
                "cover_x": int(self.cover_x),
                # values classified inside the segment in progress, held
                # until its close makes their x order meaningful
                "pending": [[int(k), int(r)] for k, r in self.pending],
                # ... and the census runs of that segment, counted only
                "pending_census": {str(r): int(c) for r, c
                                   in sorted(self.pending_census.items())},
                "found": self.found,
                "census": {str(r): c for r, c in sorted(self.census.items())},
                "passed": self.passed,
                "elapsed": self.elapsed + (time.time() - self._t0),
                "discoveries": self.discoveries,
                "near": self.near,
                "survivors": self.survivors,
                "saved": time.strftime("%Y-%m-%d %H:%M:%S")}

    def mark_boundary(self):
        """Snapshot the state as of the last fully classified launch -- what
        an interrupt writes (CONVENTIONS.md "Ctrl+C")."""
        self._snapshot = self.state()

    def save(self):
        # the snapshot is part of what a save costs the loop, so the rate
        # limit below is priced on both
        t_save = time.perf_counter()
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
        self._stored_w = int(st.get("W", 0))
        self._stored_n = st.get("n")
        self.j = int(st["j"])
        self.u = int(st.get("u", 0))
        self.pending = [(int(k), int(r)) for k, r in st.get("pending", [])]
        # absent in a checkpoint from before the counts (its census runs
        # are still values in `pending`, and are counted at the close)
        self.pending_census = {int(r): int(c) for r, c
                               in st.get("pending_census", {}).items()}
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
        """The x below which EVERY value at or above the floor has been
        swept -- the coverage claim, a segment boundary."""
        return self.boundary * self.eng.W

    def u_progress(self, jn, un):
        """An x for the HEARTBEAT inside a segment -- progress, not coverage."""
        return self.eng.progress_k(jn, un)

    def segment_end(self):
        jmax = cpu.k_ceil(self.filter_n(), self.fam) // self.eng.W
        return min(self.j + self.eng.seg_periods, jmax)

    # ------------------------------------------------------------- status
    def status_line(self):
        # TWO cursors (CONVENTIONS.md "Two cursors"): `pos` is PROGRESS and
        # prices an ETA; `cov` is the COVERAGE claim and alone says which
        # rungs are passed and how much of the open term's mass is behind us
        k = (self.hb.pos() or self.swept_k())
        cov = self.swept_k()
        rate = self.hb.rate()
        lo = self.boundary * self.eng.W
        seg = self.eng.seg_periods
        pct = min(100.0, max(0.0, 100.0 * (k - lo) / (seg * self.eng.W)))
        parts = [f"swept to {self.TERM} = {self.swept_k():.6g}",
                 f"segment [{lo:.5g}, {lo + seg * self.eng.W:.5g}) {pct:.0f}%",
                 f"{self.oeis} filter n = {self.filter_n()}"]
        if rate:
            parts.append(f"{rate:.3g} {self.TERM}/s")
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
                eta = "inside the segment being worked"
            parts.append(f"next {lab} {d:.3g} (ETA {eta})")
            p = model.p_by(self.fam, self.filter_n(),
                           model.floor_for(self.fam, self.filter_n(),
                                           self.model_floor()), cov)
            parts.append(f"P(a({self.filter_n()}) under the claim) = "
                         f"{100 * p:.0f}%")
        stall = self.hb.stalled()
        if stall:
            parts.append(f"-- no segment closed since the last status: "
                         f"{stall[0]} for {stall[1]:.0f}s")
        return "  ".join(parts)

    # --------------------------------------------------------------- hits
    def handle(self, k, run):
        """Classify one value at a segment close.  True if it was a find."""
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
                log("ALARM", f"NEAR value {self.TERM} = {k:,} run {run} failed "
                             f"verification: {legs}")
                raise SystemExit(2)
            log("NEAR", f"run {run} at {self.TERM} = {k:,} (run-{run} "
                        f"#{self.census[run]} of the campaign; verified) -- "
                        f"ONE condition short of a({frontier + 1})!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, x, run):
        frontier = self.frontier()
        n = self.eng.n
        # A RIDER IS DECIDED HERE, by running the chain past the filter by
        # the oracle's own definition, before anything is claimed
        self.hb.doing(f"verifying run-{run} {self.TERM}={x}")
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
        self.hb.doing(f"certifying run-{run} {self.TERM}={x}")
        certs, unproved = certify_run(x, run, self.fam)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        also = also_settles(self.fam, x, run, settles)
        js = ref.exponents(self.fam, run)
        # The record speaks the OEIS entry's language (rule 5i): the term
        # under the entry's own letter, `forms` in its own letters, and
        # `oeis_terms` literally what goes into the OEIS
        ev = {**evidence.header(self.oeis, ref.FAMILIES[self.fam]["forms"],
                                self.TERM, x, settles),
              "filter_n": int(n),
              "run": int(run), "settles": settles,
              "values": {str(j): int(10 ** j * x + 1) for j in js},
              "multipliers": {str(j): 10 ** j for j in js},
              "values_note": "keyed by the exponent -- the entry's "
                             + ("m" if self.fam == "A305740" else "k"),
              "verification": legs,
              "stopper": stop,
              "certificates": certs,
              "certificates_verified": not unproved,
              "unproved": unproved,
              "proof_routes": routes,
              "also_settles": also,
              "least_claim": {f"swept_from_{self.TERM}": int(self.x_start()),
                              # up to here the claim rests on the PREVIOUS
                              # filter's classified sweep (follow_frontier)
                              "covered_by_previous_filter_to":
                                  int(max(self.cover_x, self.x_start())),
                              f"swept_to_{self.TERM}": int(x),
                              "filter": int(n),
                              "wheel": int(self.eng.W),
                              "sieve_depth": int(self.eng.q2),
                              "unit": int(self.eng.unit),
                              "monotone_floor": int(self.frontier_k()),
                              **({"sibling_floor": {
                                  "value": int(sibling_floor(self.fam, n)),
                                  "rests_on": f"A153431({n - 1}) = "
                                              f"{settled_term('A153431', n - 1)}",
                                  "why": "a k below it with run >= n would "
                                         "make m = 10k meet A153431's condition "
                                         f"at index {n - 1} below that term"}}
                                 if sibling_floor(self.fam, n)
                                 > self.frontier_k() else {})},
              "engine": self.key}
        for m in settles:
            self.found[str(m)] = int(x)
        path = evidence.record(
            ev, EVID, f"{self.oeis}_a{settles[0]}_{x}.json",
            ledger_path(self.fam), key=self.TERM,
            label="%s a(%s)" % (self.oeis, ",".join(map(str, settles))))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        stopline = (f"stopped by {form_less_one(self.fam, stop['exponent'])}"
                    f" + 1 = {stop['value']:,} = {stop['factor']} * ...")
        lines = [
            f"{self.oeis} a({settles[0]}) = {x:,}" if len(settles) == 1 else
            f"{self.oeis} a({settles[0]})..a({settles[-1]}) = {x:,}",
            f"run {run}: {ref.FAMILIES[self.fam]['forms'].split(',')[0]} is "
            f"prime for every exponent {js[0]}..{js[-1]}",
            stopline,
            f"verified 3 ways, {proved} of {len(certs)} certificates "
            f"re-verified ({', '.join(f'{r} x{c}' for r, c in sorted(routes.items()))}), "
            f"evidence {path}"]
        for a in also:
            lines.append(f"also settles {a['sequence']}({a['n']}) = "
                         f"{a['value']:,} ({self.TERM} + 1 is prime)")
        if unproved:
            lines.append(f"UNPROVED at exponent {unproved}: those values "
                         f"passed the Miller-Rabin chain and BPSW but no "
                         f"certificate landed within the bounded effort -- the "
                         f"find stands on the three legs; certify them by hand "
                         f"from the evidence file")
        banner("DISCOVERY", lines)

    def follow_frontier(self):
        """After a find: rebuild the engine at the next open term, carrying
        the classified line.

        Every survivor of every closed segment was classified to run n + 8
        at the old filter, and the filter-(n+1) sieve keeps a SUBSET of the
        filter-n sieve's survivors (K(q,n) is a subset of K(q,n+1); a newly
        forced prime only removes x that the new sieve kills anyway), so no
        x below the old boundary can be a(n + 1) without having been found
        already as a rider.  The new filter resumes at the END of the
        classified line, floored onto its own period so no gap can open;
        the claim's floor is the find (monotonicity).
        """
        old = self.eng
        self.cover_x = max(int(self.cover_x), int(self.boundary) * int(old.W))
        self.eng = self._build_engine(self.filter_n())
        self.j = max(self.floor_period(), self.cover_x // int(self.eng.W))
        self.u = 0
        self.boundary = self.j
        self.pending = []
        self.pending_census = {}
        log("STAGE",
            f"filter follows the frontier: n = {old.n} -> {self.eng.n} on the "
            f"same {self.TERM} line -- the wheel to {max(old.wheel_set)} becomes "
            f"the wheel to {max(self.eng.wheel_set)}, the unit {old.unit} "
            f"becomes {self.eng.unit}, the depth {old.q2} becomes "
            f"{self.eng.q2}, the period {old.W:.4g} becomes {self.eng.W:.4g}, "
            f"the segment {old.seg_periods} -> {self.eng.seg_periods} periods "
            f"on the {'WIDE' if self.eng.wide else 'narrow'} survivor record "
            f"(the engine chose it from the plan); the claim's floor is "
            f"{self.TERM} = {self.x_start():,} ("
            + ("the term just found"
               if sibling_floor(self.fam, self.filter_n()) <= self.frontier_k()
               else f"ceil(A153431({self.filter_n() - 1}) / 10), the sibling's "
                    f"floor, above the term just found")
            + f") and the sweep resumes at {self.TERM} = "
            f"{self.j * self.eng.W:,}, the end of the line the old filter "
            f"classified or the floor if that is higher (every survivor of "
            f"the line was run to n + 8, so nothing below it can be "
            f"a({self.filter_n()})); the ladder now aims at "
            f"a({self.filter_n()})")
        self.passed = [p for p in self.passed
                       if not any(p.startswith(f"a({m})")
                                  for m in self.found)]
        self._proof_logged = None
        self.check_proof_crossing(self.swept_k())
        self.size_pool()
        self.mark_boundary()

    # ----------------------------------------------------------- the pool
    def calibrate(self):
        """MEASURE this configuration on the launches the loop is about to
        run: device x/s, survivors per second, host cost per survivor.
        Nothing is recorded -- the loop sweeps the same launches again."""
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
                # exact: the launches of a segment are NOT equal (the last
                # first-level chunk of every unit is partial)
                cov += self.eng.line_between(u_prev, un if un else nl)
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
        line = cov
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
        again whenever the filter moves."""
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
                   f"s of device at {m['rate']:.3g} {self.TERM}/s: "
                   f"{m['per_s']:,.0f} survivors/s x {1e6 * m['cost']:.1f} us "
                   f"= {m['need']:.2f} core-s per s, x{POOL_MARGIN:g} margin")
            cap = max(1, (os.cpu_count() or 2) - 1)
            if want > cap:
                log("WARN", f"the host binds: this filter needs {want} "
                            f"workers and the machine offers {cap}; the "
                            f"device will wait on the pool (back-pressure) "
                            f"and every [STATUS] line will say so")
                want = cap
        have = self.workers is not None and (self.pool is not None
                                             or self.workers == 1)
        # two one-second measurements can differ 1.6x (ambient load), so a
        # re-size grows on any increase but shrinks only on a halving
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
        """The device may run at most BACKLOG_LAUNCHES ahead of the pool;
        past that, wait for the oldest launch, timed into the heartbeat."""
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

    # ---------------------------------------------------------- draining
    def _close_census(self):
        """At a segment's close: the counted census runs join the census.
        Returns how many there were."""
        held = 0
        for r, c in self.pending_census.items():
            self.census[r] = self.census.get(r, 0) + c
            held += c
        self.pending_census = {}
        return held

    def _drain(self, inflight, block):
        """Move classified launches from `inflight` into `pending`, in
        launch order, and advance the WORK cursor behind them -- never past
        a launch whose survivors are not yet classified.

        A run under the frontier is census whatever else the segment holds
        (the frontier only rises), so it is COUNTED here, in
        `pending_census`, and never held as a value: at A305740 n = 18 that
        was 59,523 of 59,525 held values and a 2.5 MB checkpoint, whose
        save took 126 ms where the counts take 1 ms.  The count still lands at the
        segment's close, with the values, so the census never runs ahead of
        the coverage claim."""
        front = self.frontier()
        pc = self.pending_census
        while inflight:
            cur, parts = inflight[0]
            if not block and not all(f.done() for _ks, f in parts):
                break
            inflight.popleft()
            for ks, f in parts:
                for k, r in zip(ks, f.result()):
                    self.survivors += 1
                    if r >= CENSUS_FLOOR:
                        if r < front:
                            pc[r] = pc.get(r, 0) + 1
                        else:
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
            f"sweeping the {self.TERM} line to {target:.4g}; {self.oeis} "
            f"({ref.FAMILIES[self.fam]['forms']}) filter n = "
            f"{self.filter_n()}; wheel to {max(self.eng.wheel_set)}, W = "
            f"{self.eng.W:,} at unit {self.eng.unit} ({self.eng.R:,} residues, "
            f"{self.eng.R1} x {self.eng.R2} x {self.eng.R3}); a segment is "
            f"{self.eng.seg_periods} periods ({self.eng.seg_periods * self.eng.W:.4g} "
            f"of line) in {self.eng.launches_per_segment} launches of "
            f"{cfg['cand_per_launch']:.3g} candidates on the "
            f"{'wide' if self.eng.wide else 'narrow'} record; resume at "
            f"period {self.j}, launch {self.u} ({self.TERM} = "
            f"{self.u_progress(self.j, self.u):,})")
        for n, qs in sorted(model.predictions(
                self.fam, self.frontier(), self.model_floor(),
                n_ahead=3, ceiling=cpu.k_ceil(self.filter_n(), self.fam)).items()):
            log("STAGE", "  a(%d): %s" % (n, "  ".join(
                "%s %.3g" % (q, v) for q, v in qs.items())))
        log("STAGE", "the heartbeat carries TWO numbers, and they are not "
                     "the same claim: 'swept to' is the %s below which EVERY "
                     "value has been tested, and it advances one whole "
                     "segment at a time; 'segment .. X%%' is progress THROUGH "
                     "the segment being worked, whose candidates arrive out "
                     "of order, so no part of it is clear until that reads "
                     "100%%." % self.TERM)
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
                j1 = self.segment_end()
                if j1 <= self.j:
                    break
                self.hb.doing(f"sieving [{self.j * self.eng.W:.4g}, "
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
                self.hb.doing(f"classifying the tail of the segment at "
                              f"{self.j * self.eng.W:.4g}")
                self._drain(inflight, block=True)
                held = len(self.pending) + self._close_census()
                found_now = False
                for k, r in sorted(self.pending):
                    found_now = self.handle(k, r) or found_now
                self.pending = []
                self.j, self.u = j1, 0
                self.boundary = self.j
                self._plog_n += 1
                if found_now or time.time() - self._plog_t >= PERIOD_LOG_S:
                    log("STAGE",
                        f"segment complete: swept to {self.TERM} = "
                        f"{self.swept_k():,} (+{self.eng.seg_periods * self.eng.W:.4g} "
                        f"of line; {held} value{'' if held == 1 else 's'} at "
                        f"run >= {CENSUS_FLOOR} classified in {self.TERM} order"
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
        log("STAGE", f"campaign stopped at {self.TERM} = {self.swept_k():,} "
                     f"({self.discoveries} find(s) this campaign; checkpoint "
                     f"{'written' if landed else 'DEFERRED -- held open'})")
        return 0

    def _on_interrupt(self):
        snap = self._snapshot or self.state()
        if self.save_boundary():
            return (f"checkpoint written at the last classified launch: "
                    f"period {int(snap['j'])}, u = {int(snap['u'])}, swept "
                    f"to {self.TERM} = {int(snap['k']):,} ({self.ckpt})")
        return (f"{self.ckpt} is held open by another process, so THIS "
                f"boundary (period {int(snap['j'])}, u = {int(snap['u'])}) "
                f"was not written; the run resumes from the last save that "
                f"landed")


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """All four outcomes of the taxonomy, on this project's mathematics."""
    return [((13, 12), "DISCOVERY"),     # beyond the frontier
            ((15, 12), "DISCOVERY"),     # a long run settles several at once
            ((12, 12), "NEAR"),          # one condition short of a(13)
            ((11, 12), "CENSUS"),        # below the frontier: counted only
            ((8, 12), "CENSUS"),         # the census floor itself
            ((7, 12), None),             # under the floor: not even counted
            ((-1, 12), None)]            # A153431 with x + 1 composite


# The canaries: published terms a period-0 mini-hunt reaches in a second or
# two, at the filter each belongs to, in x space AND in unit space.
_CANARIES = (("A305740", 8, 1), ("A305740", 9, 7), ("A305740", 10, 7),
             ("A153431", 8, 1), ("A153431", 8, 14), ("A153431", 9, 14))


def _canary_hunt():
    """The stream must organically rediscover known terms, in both families,
    as FIRST occurrences at their own filters -- sweeping period 0 from the
    engine floor with the clip, the prefix [1, floor] checked by the
    oracle."""
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
                  "space, both families, up to A305740's a(10) = "
                  "10,562,770,680 and A153431's a(9) = 15,538,734,736")


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on both
    families; and the A305740 -> A153431 claim both ways."""
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        ok, legs, stop = verify(x, top, fam)
        if not ok:
            return False, (f"PROTOCOL FAIL: genuine run-{top} at x={x} "
                           f"({fam}) rejected: {legs}")
        if stop["exponent"] != top + 1:
            return False, f"PROTOCOL FAIL: {fam}: the stopper is not exponent {top+1}"
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
    # the derived claim: A305740(7) = 170926 has 170927 prime, so with
    # A153431 pretended unknown it settles A153431(7) = 170926 -- which IS
    # the published A153431(7); A305740(6) = 170716 has 170717 composite
    # and settles nothing; A153431 finds settle nothing in A305740
    x7 = ref.KNOWN["A305740"][7]
    a = also_settles("A305740", x7, 7, [7], known={})
    if [(r["sequence"], r["n"], r["value"]) for r in a] != [("A153431", 7, x7)] \
            or ref.KNOWN["A153431"][7] != x7:
        return False, f"PROTOCOL FAIL: A305740(7)'s derived claim came out {a}"
    if also_settles("A305740", x7, 7, [7]):
        return False, "PROTOCOL FAIL: a derived claim on a PUBLISHED index"
    if also_settles("A305740", ref.KNOWN["A305740"][6], 6, [6], known={}):
        return False, "PROTOCOL FAIL: 170716 + 1 is composite but was claimed"
    if also_settles("A153431", ref.KNOWN["A153431"][13], 13, [13], known={}):
        return False, "PROTOCOL FAIL: A153431 claimed a rider it does not have"
    return True, ("protocol ok, both families: each frontier term accepted at "
                  "its true run with a factor witness for its composite "
                  "stopper, and a run one too long and a mislabelled earlier "
                  "term both rejected; an A305740 find with x + 1 prime "
                  "settles A153431 at an unpublished index (170926 -> "
                  "A153431(7), which is what the OEIS has), never at a "
                  "published one, never with x + 1 composite, and A153431 "
                  "settles nothing in A305740")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing."""
    raised = []
    for fam in ref.FAMILIES:
        eng = gpu.GpuEngine(12, fam, p1=13, p2=None, p3=None, q2=1024)
        ceil = cpu.k_ceil(12, fam)
        if ceil != ceiling.K_CEIL:
            return False, f"CEILING FAIL: {fam}'s ceiling is not K_CEIL"
        try:
            eng.sweep(ceil // eng.W - 1, ceil // eng.W + 2)
            return False, f"CEILING FAIL: the {fam} GPU engine swept past k_ceil"
        except ValueError:
            raised.append(f"gpu k_ceil ({fam})")
        jc = ceil // eng.W
        eng._check_window(jc - 1, jc, None)
        try:
            eng._check_window(jc, jc + 1, None)
            return False, "CEILING FAIL: the first period past K_CEIL was accepted"
        except ValueError:
            raised.append(f"gpu k_ceil tight to one period ({fam})")
        try:
            eng.sweep(0, 2)
            return False, "CEILING FAIL: the GPU engine swept period 0 unclipped"
        except ValueError:
            raised.append(f"gpu floor ({fam})")
        try:
            eng.sweep(0, 2, k_min=cpu.k_floor(1024, 12, fam))
            return False, "CEILING FAIL: a clip AT the floor was accepted"
        except ValueError:
            raised.append(f"gpu k_min <= floor ({fam})")
        c = cpu.CpuEngine(12, fam, q2=1024)
        try:
            c.survivors(10 ** 5, ceil + 10)
            return False, "CEILING FAIL: the CPU engine swept past k_ceil"
        except ValueError:
            raised.append(f"cpu k_ceil ({fam})")
        lowf = cpu.k_floor(1024, 12, fam)
        try:
            c.survivors(lowf, lowf + 10 ** 5)
            return False, "CEILING FAIL: the CPU engine swept at the floor"
        except ValueError:
            raised.append(f"cpu floor ({fam}, {lowf})")
    if cpu.k_floor(1024, 12, "A305740") != 102 or \
            cpu.k_floor(1024, 12, "A153431") != 1023:
        return False, ("CEILING FAIL: the floors are not (q2 - 1)/10 and "
                       "q2 - 1: the smallest values are 10x + 1 and x + 1")
    try:
        gpu.wheel(7, "A305740", 53)
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(15, "A305740", p1=31, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    try:
        gpu.GpuEngine(18, "A305740", p1=13, p2=19, p3=23, q2=4096, unit=2261)
        return False, ("CEILING FAIL: a wheel whose middle level is all unit "
                       "primes was built -- its third level would be dropped")
    except ValueError:
        raised.append("empty middle level")
    try:
        gpu.GpuEngine(gpu.NRES_MAX + 1, "A305740", p1=13, p2=None,
                      p3=None, q2=1024)
        return False, ("CEILING FAIL: a filter longer than the tail's "
                       "residue list was accepted")
    except ValueError:
        raised.append("nforms <= NRES_MAX")
    for fam, unit in (("A305740", 14), ("A305740", 6), ("A153431", 4522)):
        try:
            gpu.GpuEngine(15, fam, p1=13, p2=None, p3=None, q2=1024,
                          unit=unit)
            return False, (f"CEILING FAIL: unit {unit}, which nothing forces "
                           f"at n = 15 of {fam}, was accepted")
        except ValueError:
            raised.append(f"unit {unit} refused ({fam})")
    try:
        gpu.GpuEngine(15, "A000001", p1=13, p2=None, p3=None, q2=1024)
        return False, "CEILING FAIL: an unknown family was accepted"
    except KeyError:
        raised.append("family")
    return True, ("ceiling ok: %s all raise rather than compute" %
                  ", ".join(raised))


def _first_prime_rung(fam, x, n_max=24):
    """The first exponent j <= n_max whose value 10^j*x + 1 is a probable
    prime past the deterministic bound, or None."""
    for j in range(ref.j0(fam), n_max + 1):
        v = 10 ** j * x + 1
        if v >= MR_VALID_BELOW and sprp_base2(v) and mr_is_prime(v):
            return j
    return None


def _certificate_drill():
    """A discovery past the proof crossing is PROVED, not just tested -- and
    at the CEILING, with the recursion.

    Each family's frontier term is certified value by value (every value
    under the bound takes the deterministic route; A305740's a(12) and
    A153431's a(13) reach past it at their top exponents, which take BLS75
    Theorem 1 on 10^j*x); then the first x past k_proof(n, F) whose top
    value is a probable prime; then AT K_CEIL a worst-case x (the unit times
    a balanced semiprime) and an x with a prime factor above the
    deterministic bound, whose certificate must carry a subproof that
    cannot be stripped.
    """
    parts = []
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        certs, unproved = certify_run(x, top, fam)
        if unproved or len(certs) != ref.nforms(fam, top):
            return False, (f"CERTIFICATE FAIL: {fam} a({top}) left "
                           f"{unproved} unproved ({len(certs)} certificates)")
        routes = sorted({c.get("proof") for c in certs.values()})
        if not set(routes) <= {"deterministic-mr", "bls75-thm1"}:
            return False, f"CERTIFICATE FAIL: {fam} a({top}) took {routes}"
        for j, c in certs.items():
            N = 10 ** int(j) * x + 1
            if int(c["N"]) != N:
                return False, f"CERTIFICATE FAIL: {fam} proof {j} is not about 10^j*x + 1"
            want = "deterministic-mr" if N < MR_VALID_BELOW else "bls75-thm1"
            if c.get("proof") != want:
                return False, (f"CERTIFICATE FAIL: {fam} a({top}) exponent {j} "
                               f"took {c.get('proof')}, not {want}")
        parts.append(f"{fam} a({top})'s {len(certs)} values ({', '.join(routes)})")
    for fam, n in (("A305740", 18), ("A153431", 17)):
        unit = cpu.forced_unit(n, fam)
        m = -(-cpu.k_proof(n, fam) // unit)
        xx = None
        for _ in range(20000):
            cand = unit * m
            v = 10 ** n * cand + 1
            if v >= MR_VALID_BELOW and sprp_base2(v) and mr_is_prime(v):
                xx = cand
                break
            m += 1
        if xx is None:
            return False, (f"CERTIFICATE FAIL: no x of {fam} past the "
                           f"crossing at n = {n} with a probable-prime top "
                           f"value in 20000 tries")
        certs, unproved = certify_run(xx, n, fam, only=(n,))
        c = certs.get(str(n))
        if unproved or c is None or c.get("proof") != "bls75-thm1":
            return False, (f"CERTIFICATE FAIL: {fam} 10^{n}*x + 1 at x = "
                           f"{xx:.4g} was not proved by bls75-thm1: "
                           f"{c and c.get('proof')}")
        if int(c["N"]) != 10 ** n * xx + 1 or int(c["R"]) != 1:
            return False, ("CERTIFICATE FAIL: the proof is not about the "
                           "value, or N - 1 was not factored completely")
        ok, why = certificate.verify(c)
        if not ok:
            return False, f"CERTIFICATE FAIL: the proof does not re-verify: {why}"
        if certificate.verify(dict(c, N=int(c["N"]) + 2))[0]:
            return False, "CERTIFICATE FAIL: a proof verified for a neighbouring N"
        if certificate.verify({"proof": "deterministic-mr",
                               "N": int(c["N"])})[0]:
            return False, ("CERTIFICATE FAIL: a deterministic-MR claim past "
                           "the bound was accepted as a proof")
        parts.append(f"{fam} at n = {n}: 10^{n}*x + 1 = "
                     f"{10 ** n * xx + 1:.4g} past the crossing is proved by "
                     f"bls75-thm1 on 10^{n}*x factored completely "
                     f"({len(c['factors'])} primes), re-verifies, refused for "
                     f"N + 2 and as a bare MR claim")
    t0 = time.time()
    for fam in ref.FAMILIES:
        n = 18 if fam == "A305740" else 17
        unit = cpu.forced_unit(n, fam)
        for label, maker in (("hard", lambda sd: ceiling.hard_k(
                                  ceiling.K_CEIL - 10 ** 38, unit, seed=sd)[0]),
                             ("big-prime", lambda sd: ceiling.big_prime_k(
                                  ceiling.K_CEIL // 10 ** 6 + sd * 10 ** 30,
                                  unit)[0])):
            xx, jj = None, None
            for sd in range(1, 60):
                x = maker(sd)
                if x >= cpu.k_ceil(n, fam):
                    return False, (f"CERTIFICATE FAIL: the {label} x is past "
                                   f"the ceiling")
                jj = _first_prime_rung(fam, x)
                if jj is not None:
                    xx = x
                    break
            if xx is None:
                return False, (f"CERTIFICATE FAIL: no {label} x of {fam} near "
                               f"K_CEIL with a probable-prime value in 59 tries")
            certs, unproved = certify_run(xx, jj, fam, only=(jj,))
            c = certs.get(str(jj))
            if unproved or c is None or c.get("proof") != "bls75-thm1":
                return False, (f"CERTIFICATE FAIL ({label}, {fam}): exponent "
                               f"{jj} at x = {xx:.4g} not proved by "
                               f"bls75-thm1: {c and c.get('proof')}")
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
                             f"the bound): bls75-thm1 with a subproof of it, "
                             f"which cannot be stripped")
            else:
                parts.append(f"{fam} at x = {xx:.3g} (the unit {unit} x two "
                             f"{len(str(max(int(p) for p in c['factors'])))}"
                             f"-digit primes): bls75-thm1, R = 1, re-verified")
    parts.append(f"the four ceiling certificates took {time.time() - t0:.1f} s "
                 f"in all")
    return True, "certificates ok: " + "; ".join(parts)


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly, on every kernel
    and across the seams a real interrupt leaves: a period boundary, the
    (j, u) sub-segment cursor, and the clipped period 0."""
    total = 0
    for lab, fam, kw, j_at, span, cut in (
            ("one-level", "A305740", dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 1200, 457),
            ("two-level", "A153431", dict(p1=19, p2=31, p3=None, q2=8192,
                                          unit=14, pb=32),
             10 ** 15, 3, 1),
            ("three-level", "A305740", dict(p1=13, p2=17, p3=19, q2=128,
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
    # THE (j, u) SEAM, in the segment that starts at period 0 with the clip
    # too; nu forced below R3 so the segment really is cut into launches
    for eng in (gpu.GpuEngine(15, "A305740", p1=11, p2=17, p3=23, q2=128,
                              nu=4, pb=32),
                gpu.GpuEngine(16, "A153431", p1=11, p2=23, p3=29, q2=128,
                              nu=2, unit=238, pb=32)):
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
                  f"included), across the (j, u) sub-segment seam in x "
                  f"space and in unit space (238), and inside the clipped "
                  f"segment at period 0 on both ({total} survivors across "
                  f"the seams)")


def _classification_drill():
    """The two-pass screen == the all-bases chain on real survivors, both
    families; the pool's chunked answer == the serial one; and a run is
    bounded by the cap alone (riders read past the filter)."""
    rows = []
    for fam in ref.FAMILIES:
        eng = gpu.GpuEngine(10, fam, p1=13, p2=23, p3=None, q2=4096)
        j0 = eng.j_of(10 ** 13)
        surv = eng.survivors_j(j0, j0 + 150)
        if len(surv) < 3 * CHUNK:
            return False, (f"CLASSIFY FAIL: only {len(surv)} survivors -- the "
                           f"drill cannot span several chunks")
        two = [sprp_run(k, fam, 18) for k in surv]
        full = []
        for k in surv:
            j = ref.j0(fam)
            while j <= 18 and mr_is_prime(10 ** j * k + 1):
                j += 1
            full.append(j - 1)
        if two != full:
            i = next(i for i in range(len(surv)) if two[i] != full[i])
            return False, (f"CLASSIFY FAIL: {fam} two-pass sprp gave run "
                           f"{two[i]} and the all-bases chain {full[i]} at "
                           f"x = {surv[i]}")
        with _pool_factory(2) as pool:
            parts = _submit(pool, fam, 18, surv)
            got = [r for ks, f in parts for r in f.result()]
        if got != full:
            return False, f"CLASSIFY FAIL: {fam}: the pool's chunked result differs"
        rows.append(f"{fam} {len(surv)} survivors (max run {max(full)})")
    x = ref.KNOWN["A153431"][6]
    if sprp_run(x, "A153431", 6) != 6 or sprp_run(x, "A153431", 30) != 7:
        return False, ("CLASSIFY FAIL: A153431's rider a(6) = a(7) does not "
                       "read 6 under cap 6 and 7 under cap 30")
    x = ref.KNOWN["A305740"][4]
    if sprp_run(x, "A305740", 30, floor=0) != 5:
        return False, "CLASSIFY FAIL: A305740's rider a(4) = a(5) = 7 does not read 5"
    if sprp_run(ref.KNOWN["A305740"][6], "A153431", 30, floor=0) != -1:
        return False, ("CLASSIFY FAIL: an x with x + 1 composite does not "
                       "read run -1 in A153431")
    return True, (f"classification ok: two-pass sprp == all-bases chain on "
                  f"{'; '.join(rows)}, pool chunks reassemble to the serial "
                  f"answer, riders read past the filter (A153431 a(6) = a(7), "
                  f"A305740 a(4) = a(5)) and A153431's run of an x with "
                  f"x + 1 composite is -1")


def _stop_on_discovery_drill():
    """--stop-on-discovery stops on a NEW find, not on a loaded one --
    drilled on the RESUMED case, at non-zero prior counts, through the real
    Campaign's latch (the count at run start)."""
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
    # and a REAL campaign resumed from a checkpoint holding finds latches
    # the count it started with
    import tempfile
    tmp = tempfile.mkdtemp(prefix="decl-stop-")
    path = str(pathlib.Path(tmp) / "c.json")
    try:
        fam = "A305740"
        pol = _POLICIES[fam].at(path)
        c = Campaign(_args_for(fam), ckpt=path, cursor=pol)
        c.discoveries = 3
        c.save()
        d = Campaign(_args_for(fam, stop_on_discovery=True), ckpt=path,
                     cursor=_POLICIES[fam].at(path))
        if d.discoveries != 3 or d._discoveries_at_start != 3 or stops(d):
            return False, ("STOP DRILL FAIL: a resumed campaign with 3 finds "
                           "in its checkpoint would stop before sweeping")
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
    return True, ("stop-on-discovery ok: a resumed campaign with 0, 1, 2 or "
                  "7 finds already in the checkpoint does NOT stop before "
                  "finding something, and DOES stop on the next new find; a "
                  "real Campaign reloaded with 3 finds latches 3 at run start")


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
    """A FIND MOVES THE FILTER, and the cursor must carry the classified
    line.

    On a scratch checkpoint, per family: promoting rebuilds the engine at
    the new filter with one more form; the cursor lands at the END OF THE
    LINE THE OLD FILTER CLASSIFIED, floored onto the new period, never below
    the new floor (the term just found); the clip is gone past the floor;
    the ladder retires the found term's rungs; the checkpoint round-trips;
    and a cursor stored at ONE filter is REFUSED by a campaign whose
    frontier puts it at another.  Then the promotions THAT CHANGE THE UNIT
    (A305740 15 -> 16 -> 17 -> 18: 7, 119, 119, 2261; A153431 14 -> 15 and
    16 -> 17: 14, 238, 4522) and the record: every engine the campaign
    builds comes up on the record the planner priced, by itself.
    """
    import tempfile
    import json as _json
    tmp = tempfile.mkdtemp(prefix="decl-promote-")
    path = str(pathlib.Path(tmp) / "c.json")
    rows = []
    try:
        for fam in ref.FAMILIES:
            pol = _POLICIES[fam].at(path)
            c = Campaign(_args_for(fam), ckpt=path, cursor=pol)
            n0 = c.filter_n()
            before = (c.eng.n, c.eng.unit, c.eng.W, c.eng.nforms)
            if c.j != c.floor_period() or c.x_start() <= 0:
                return False, (f"PROMOTION FAIL: {fam} fresh campaign did not "
                               f"start at its floor period")
            found_x = c.x_start() + 10 * c.eng.unit
            c.found[str(n0)] = int(found_x)
            c.boundary = c.j + c.eng.seg_periods
            covered = c.boundary * c.eng.W
            c.follow_frontier()
            if c.eng.n != n0 + 1 or c.eng.nforms != before[3] + 1:
                return False, (f"PROMOTION FAIL: {fam} did not move to n = "
                               f"{n0+1} with one more form")
            want_j = max(c.floor_period(), covered // c.eng.W)
            if c.u != 0 or c.j != want_j or c.boundary != c.j:
                return False, (f"PROMOTION FAIL: {fam} resumed at (j, u) = "
                               f"({c.j}, {c.u}), expected period {want_j}")
            if c.j * c.eng.W > max(covered, c.x_start()) or \
                    (c.j + 1) * c.eng.W <= max(covered, c.x_start()):
                return False, (f"PROMOTION FAIL: {fam}'s resumed period {c.j} "
                               f"is not the FLOOR of the classified line "
                               f"{covered} onto the period {c.eng.W}")
            if c.cover_x != covered:
                return False, f"PROMOTION FAIL: {fam} cover_x {c.cover_x} != {covered}"
            if c.j * c.eng.W > c.x_start() and c.k_min() is not None:
                return False, f"PROMOTION FAIL: {fam} still clips past the floor"
            if c.x_start() != max(found_x, cpu.k_floor(c.eng.q2, n0 + 1, fam) + 1,
                                  sibling_floor(fam, n0 + 1)):
                return False, (f"PROMOTION FAIL: {fam}'s new floor is "
                               f"{c.x_start()}, not the found term {found_x}")
            if any(p.startswith(f"a({n0})") for p in c.passed):
                return False, f"PROMOTION FAIL: {fam} kept a retired rung"
            if not c.save():
                return False, f"PROMOTION FAIL: {fam}'s post-promotion save did not land"
            c2 = Campaign(_args_for(fam), ckpt=path, cursor=_POLICIES[fam].at(path))
            if (c2.filter_n(), c2.j, c2.u, c2.cover_x) != (n0 + 1, c.j, 0, covered):
                return False, (f"PROMOTION FAIL: {fam} reloaded at "
                               f"({c2.filter_n()}, {c2.j}, {c2.u}, cover "
                               f"{c2.cover_x})")
            with open(path) as fh:
                st = _json.load(fh)
            st["n"] = n0
            checkpoint.save(path, st)
            try:
                Campaign(_args_for(fam), ckpt=path,
                         cursor=_POLICIES[fam].at(path))
                return False, (f"PROMOTION FAIL: {fam} read a cursor stored at "
                               f"filter {n0} while hunting a({n0+1})")
            except ValueError:
                pass
            rows.append(f"{fam} n = {n0} -> {n0+1}: unit {before[1]} -> "
                        f"{c.eng.unit}, period {before[2]:.3g} -> {c.eng.W:.3g}")
            # the promotions that change the unit, and the record at each
            # engine the campaign builds, walked through follow_frontier
            units = []
            last = max(gpu.campaign_filters(fam))
            while c.filter_n() < last:
                m = c.filter_n()
                c.found[str(m)] = int(c.x_start() + 1000 * c.eng.unit)
                c.boundary = c.j + c.eng.seg_periods
                old_cov = c.boundary * c.eng.W
                c.follow_frontier()
                if c.j * c.eng.W > max(old_cov, c.x_start()):
                    return False, (f"PROMOTION FAIL: {fam} {m} -> {m + 1} "
                                   f"opened a gap above the classified line")
                u, *lv, q2, pb = plan_for(fam, c.filter_n())
                Wp = c.eng.Wp
                wide, pv = gpu._record_for(Wp, q2, pb)
                if c.eng.unit != u or c.eng.unit != cpu.forced_unit(c.filter_n(), fam) \
                        or c.eng.wide != wide or c.eng.seg_periods != pv:
                    return False, (f"PROMOTION FAIL: {fam} at n = {c.filter_n()}"
                                   f" came up unit {c.eng.unit}, "
                                   f"{'wide' if c.eng.wide else 'narrow'} with "
                                   f"{c.eng.seg_periods} periods; the plan "
                                   f"says unit {u}, {'wide' if wide else 'narrow'}"
                                   f", {pv}")
                units.append(f"{c.filter_n()}:{c.eng.unit}"
                             f"{'W' if c.eng.wide else ''}")
            rows.append(f"{fam} through n = {last}: " + " ".join(units))
            os.remove(path)
            if os.path.exists(path + ".bak"):
                os.remove(path + ".bak")
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
    return True, ("promotion ok: " + "; ".join(rows) + " (unit per filter, "
                  "W = the wide record) -- the cursor lands at the end of the "
                  "line the old filter classified, floored onto the new "
                  "period and never below the new floor, the clip is gone past "
                  "the floor, the carried coverage round-trips, the retired "
                  "rungs go, a cursor stored at the wrong filter is REFUSED, "
                  "and every engine through the last campaign filter comes up "
                  "at the forced unit on the record the plan priced")


def _other_families_cursor_drill(fam):
    """Every OTHER family's policy, put in front of every key it declares."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="decl-cursor-")
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
                  f"family ok: all {seen} declared keys pass BOTH readers; "
                  f"an unknown key refuses")


def _families_stay_apart():
    """No two campaigns can read each other's cursor; the per-filter plan is
    admissible at every campaign filter, at the forced unit; the planned
    segment's expected over-sweep is priced; and every campaign benchmark
    shape in score.py names exactly what the campaign plans there."""
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
    want_units = {"A305740": {13: 7, 14: 7, 15: 7, 16: 119, 17: 119,
                              18: 2261, 19: 2261},
                  "A153431": {14: 14, 15: 238, 16: 238, 17: 4522, 18: 4522}}
    worst = []
    for f in fams:
        for n in gpu.campaign_filters(f):
            unit, p1, p2, p3, q2, pb = plan_for(f, n)
            cpu.assert_unit(n, f, unit)
            if unit != want_units[f][n]:
                return False, (f"FAMILY FAIL: {f} n = {n} plans at unit "
                               f"{unit}, not {want_units[f][n]}")
            # THE PLAN'S PRICE AGAINST THE UNAVOIDABLE SWEEP: the expected
            # line to a confirmed find with this plan's segment, against the
            # mean excess alone (an infinitely fine segment)
            Wp = 1
            for q in gpu._wheel_primes(p1, p2, p3):
                if unit % q:
                    Wp *= q
            wide, pv = gpu._record_for(Wp, q2, pb)
            fl = model.projected_floor(f, n)
            W = unit * Wp
            start = (fl // W) * W
            got = model.expected_sweep(f, n, fl, start, pv * W)
            ideal = model.expected_sweep(f, n, fl, fl, 1.0)
            worst.append((got / ideal, f, n))
            if got > 1.5 * ideal:
                return False, (f"FAMILY FAIL: {f} n = {n}: the planned segment "
                               f"({pv} x {W:.4g}) makes the expected sweep "
                               f"{got / ideal:.2f}x the unavoidable one")
    # the benchmark shapes are the campaign's (a planner change must
    # re-freeze them in the same commit)
    try:
        import score as _score
    except Exception as e:                      # noqa: BLE001
        return False, f"FAMILY FAIL: score.py does not import: {e}"
    for sh in _score.SHAPES:
        label, fam, n, p1, p2, p3, q2 = sh[:7]
        unit, pb, campaign = sh[12], sh[14], sh[16]
        if not campaign:
            continue
        pu, a, b, cc, pq2, ppb = plan_for(fam, n)
        def _t(lv):
            return tuple(lv) if lv else None
        if (pu, _t(a), _t(b), _t(cc), pq2, ppb) != \
                (unit, _t(p1), _t(p2), _t(p3), q2, pb):
            return False, (f"FAMILY FAIL: the benchmark shape {label} ({fam} "
                           f"n = {n}) is not what the campaign plans there: "
                           f"{(unit, p1, p2, p3, q2, pb)} against "
                           f"{(pu, a, b, cc, pq2, ppb)} -- re-freeze it")
    for n, wrong in ((13, 6), (15, 119), (17, 2261), (13, 49)):
        try:
            cpu.assert_unit(n, "A305740", wrong)
            return False, (f"FAMILY FAIL: unit {wrong} accepted at n = {n}")
        except ValueError:
            pass
    worst.sort(reverse=True)
    return True, ("families stay apart: two distinct config keys, checkpoint "
                  "files and ledgers, no policy reads the other's cursor; the "
                  "PER-FILTER plan is admissible at every campaign filter at "
                  "the forced unit (7 / 119 / 2261 and 14 / 238 / 4522, and "
                  "6, 119 early, 2261 early and 49 refused); every planned "
                  "segment's expected sweep is within 1.5x of the unavoidable "
                  "one (the worst is %s n = %d at %.3fx); and every campaign "
                  "benchmark shape names exactly what the campaign plans"
                  % (worst[0][1], worst[0][2], worst[0][0]))


def _campaign_wiring_drill(fam="A305740"):
    """Build a campaign and exercise everything the loop touches, without
    sweeping a whole segment: construction from nothing, the status line,
    census and NEAR/CENSUS classification, the cached rung ladder, the drain
    of a fake in-flight launch, the pool sized from a real measurement,
    back-pressure, a find moving the filter, a save/load round trip, and the
    interrupt snapshot."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="decl-drill-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[fam].at(path)
    n0 = open_n(fam)
    a = _args_for(fam)
    try:
        c = Campaign(a, ckpt=path, cursor=pol)
        if c.frontier() != n0 - 1 or c.filter_n() != n0:
            return False, (f"WIRING FAIL: frontier {c.frontier()}, filter "
                           f"{c.filter_n()} -- expected {n0 - 1} and {n0}")
        floor = c.x_start()
        if (c.j, c.u, c.k_min()) != (c.floor_period(), 0, floor):
            return False, (f"WIRING FAIL: a fresh campaign starts at "
                           f"(j, u) = ({c.j}, {c.u}), clip {c.k_min()}")
        if floor != ref.KNOWN[fam][n0 - 1]:
            return False, f"WIRING FAIL: the floor {floor} is not a({n0-1})"
        unit, p1, p2, p3, q2, pb = plan_for(fam, n0)
        if (c.eng.n, c.eng.fam, c.eng.unit, c.eng.q2) != (n0, fam, unit, q2) \
                or (c.eng.p1, c.eng.p2, c.eng.p3) != (p1, p2, p3):
            return False, ("WIRING FAIL: the engine is not the PLANNED one "
                           "for the campaign filter")
        line = c.status_line()
        for want in ("swept to", fam, "census", f"{c.TERM} = "):
            if want not in line:
                return False, f"WIRING FAIL: status line lacks {want!r}"
        if c.handle(floor + 1, 9) is not False or c.census.get(9) != 1:
            return False, "WIRING FAIL: a census run was not counted"
        if c.handle(floor + 3, 7) is not False or 7 in c.census:
            return False, "WIRING FAIL: a run under the floor was counted"
        jf = c.floor_period()
        inflight = collections.deque()
        # a run under the frontier is COUNTED at the drain and only joins
        # the census at the close; a run at it (a NEAR) is held as a value
        front = c.frontier()
        inflight.append(((jf, 52), [([5, 6, 7], _Done([3, 8, front]))]))
        inflight.append(((jf, 104), [([9], _Done([0]))]))
        c._drain(inflight, block=True)
        if (c.pending != [(7, front)] or c.pending_census != {8: 1}
                or c.survivors != 4):
            return False, (f"WIRING FAIL: the drain left pending "
                           f"{c.pending}, counted {c.pending_census} and "
                           f"{c.survivors} survivors")
        c8 = c.census.get(8, 0)
        if (c._close_census() != 1 or c.census.get(8, 0) != c8 + 1
                or c.pending_census):
            return False, (f"WIRING FAIL: the close did not move the counted "
                           f"census run into the census ({c.census}, "
                           f"{c.pending_census} left)")
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
        # THE POOL IS SIZED FROM A MEASUREMENT AT THIS FILTER
        c.args.workers = None
        c.u = 0
        c.pending = []
        before = (c.j, c.u, c.survivors, list(c.pending),
                  dict(c.pending_census), dict(c.census))
        m = c.calibrate()
        if (m["launches"] < 1 or m["survivors"] < 1 or m["rate"] <= 0
                or not 1e-7 < m["cost"] < 1e-3 or m["need"] <= 0):
            return False, f"WIRING FAIL: the sizing measurement is {m}"
        if (c.j, c.u, c.survivors, list(c.pending), dict(c.pending_census),
                dict(c.census)) != before:
            return False, "WIRING FAIL: the calibration moved the campaign"
        w = c.size_pool()
        ms = c._sizing
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

        class _Slow:
            def __init__(self, v):
                self._v, self._d = v, False

            def done(self):
                return self._d

            def result(self):
                self._d = True
                return self._v
        c.survivors = 4
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
        c.u = 0
        c.found[str(n0)] = int(floor + 4 * c.eng.unit)
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
        if c.eng.n != n0 + 1:
            return False, "WIRING FAIL: follow_frontier did not move the filter"
        c.found.pop(str(n0))
        c.eng = c._build_engine(c.filter_n())
        c.j, c.u, c.boundary = c.floor_period(), 0, c.floor_period()
        c.cover_x = 0
        c._lad.invalidate()
        c.mark_boundary()
        c._ckpt_t = time.time()
        if c.save_due():
            return False, "WIRING FAIL: a save was due right after a save"
        c._ckpt_t = 0.0
        if not c.save_due():
            return False, "WIRING FAIL: a save was not due after the interval"
        c.pending_census = {9: 2, 10: 1}       # a mid-segment save
        c.save()
        d = Campaign(a, ckpt=path, cursor=pol)
        if (d.j, d.u, d.pending, d.pending_census, d.census, d.survivors) != (
                c.j, c.u, c.pending, c.pending_census, c.census, c.survivors):
            return False, (f"WIRING FAIL: reload gave (j,u)=({d.j},{d.u}) "
                           f"pending={d.pending} counted={d.pending_census} "
                           f"census={d.census}")
        c.pending_census = {}
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
                  f"at the monotonicity floor ({floor:,}, a({n0-1}) itself) "
                  f"with the PLANNED engine at n = {n0}, unit {unit}; its "
                  f"status line and rung ladder aim at a({n0}), 75 ladder "
                  f"reads at a standing frontier cost 0 model rebuilds while "
                  f"a find costs exactly 1 and moves the aim and the filter, "
                  f"the pool is sized from a live measurement ({w} worker(s) "
                  f"for {ms['need']:.2f} core-s/s) and survives a re-size "
                  f"inside the noise band, back-pressure times the wait, the "
                  f"drain keeps the work cursor behind the classified "
                  f"launches and floors the census, the save is rate-limited, "
                  f"and the checkpoint round trips through both the normal "
                  f"save and the interrupt snapshot, pending included")


def _evidence_names_drill():
    """The writer and the files on disk speak the OEIS entries' language:
    k for A305740, m for A153431, each standing alone in its own `forms`,
    and the other family's letter REFUSED (the siblings disagree)."""
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        ev = dict(evidence.header(fam, ref.FAMILIES[fam]["forms"],
                                  term_letter(fam), ref.KNOWN[fam][top],
                                  [top]), settles=[top])
        ok, msg = evidence.check_names(ev, term_letter(fam))
        if not ok:
            return False, f"EVIDENCE NAMES FAIL: {fam} writer: {msg}"
    # the swap the siblings invite: A305740's term under m (its exponent's
    # letter) must NOT be what the writer produces
    if term_letter("A305740") != "k" or term_letter("A153431") != "m":
        return False, ("EVIDENCE NAMES FAIL: the letters are not A305740 k, "
                       "A153431 m")
    return evidence.gate_names(EVID, lambda rec: term_letter(rec["sequence"]))


def _sibling_floor_drill():
    """A305740's sweep for a(n) starts at ceil(A153431(n - 1) / 10) once that
    term is settled: the theorem holds on every published index, the floor
    is read from the published terms and from a verified first occurrence
    in evidence/, A153431 gets nothing back, and the campaign's floor and
    the odds model both use it."""
    global EVID
    import json
    import tempfile
    kn5, kn1 = ref.KNOWN["A305740"], ref.KNOWN["A153431"]
    # the theorem, on every index both entries publish
    for n, x in sorted(kn5.items()):
        if (n - 1) in kn1 and x < -(-kn1[n - 1] // 10):
            return False, (f"SIBLING FAIL: A305740({n}) = {x} is below "
                           f"ceil(A153431({n - 1}) / 10)")
    top1 = max(kn1)
    sibling_floor.cache_clear()
    want = -(-kn1[top1] // 10)
    if sibling_floor("A305740", top1 + 1) != want:
        return False, (f"SIBLING FAIL: A305740 a({top1 + 1})'s floor is "
                       f"{sibling_floor('A305740', top1 + 1)}, not {want}")
    if any(sibling_floor("A153431", n) for n in range(10, 20)):
        return False, "SIBLING FAIL: A153431 was given a floor by A305740"
    if x_floor("A305740", top1 + 1, 1) < want:
        return False, "SIBLING FAIL: x_floor ignores the sibling's floor"
    # a verified first occurrence in evidence/ moves it; a record of the
    # OTHER sequence does not
    fake = 10 ** 18 + 12345
    saved = EVID
    try:
        with tempfile.TemporaryDirectory() as d:
            EVID = d
            with open(os.path.join(d, "A153431_a14_x.json"), "w",
                      encoding="utf-8") as fh:
                json.dump({"sequence": "A153431",
                           "oeis_terms": {str(top1 + 1): fake}}, fh)
            with open(os.path.join(d, "A305740_a16_x.json"), "w",
                      encoding="utf-8") as fh:
                json.dump({"sequence": "A305740",
                           "oeis_terms": {str(top1 + 2): 7}}, fh)
            sibling_floor.cache_clear()
            got = sibling_floor("A305740", top1 + 2)
            none = sibling_floor("A305740", top1 + 3)
    finally:
        EVID = saved
        sibling_floor.cache_clear()
    if got != -(-fake // 10) or none != 0:
        return False, (f"SIBLING FAIL: from evidence the floor read {got} "
                       f"(want {-(-fake // 10)}) and {none} (want 0)")
    return True, (f"sibling floor ok: A305740(n) >= ceil(A153431(n-1)/10) "
                  f"holds on every published index; A305740 a({top1 + 1})'s "
                  f"sweep starts at {want:,} (from A153431 a({top1})), a "
                  f"verified A153431 first occurrence in evidence/ moves the "
                  f"next floor and a record of the other sequence does not, "
                  f"and A153431 gets nothing back")


def selftest(fam="A305740"):
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
              _families_stay_apart, _sibling_floor_drill):
        rows.append(d())
    rows.append(_campaign_wiring_drill(fam))
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
    TERM = term_letter(fam)
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
        log("STATUS", f"  found: a({n}) = {TERM} = {int(k):,}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--family", default="A305740",
                    help="which sequence to hunt: " +
                         ", ".join(f"{f} ({ref.FAMILIES[f]['forms']})"
                                   for f in ref.FAMILIES) +
                         " (default A305740)")
    ap.add_argument("--selftest", action="store_true",
                    help="run the full gate battery and exit")
    ap.add_argument("--status", action="store_true",
                    help="read the checkpoint and say where the hunt is")
    ap.add_argument("--to", type=float, default=None,
                    help="stop once the sweep reaches this value of the term "
                         "(" + ", ".join(f"{term_letter(f)} for {f}"
                                         for f in ref.FAMILIES) +
                         "; default: the engine ceiling, "
                         "huntlib.ceiling.K_CEIL = 1e40)")
    ap.add_argument("--stop-on-discovery", action="store_true",
                    help="checkpoint and exit once THIS RUN confirms a find "
                         "(finds already in the checkpoint do not count)")
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (default 30)")
    ap.add_argument("--workers", type=int, default=None,
                    help="classification pool size. By default it is "
                         "MEASURED at the campaign's own filter and re-"
                         "measured at every promotion: ceil(core-seconds per "
                         "second x 2). 1 classifies in the main thread and "
                         "idles the device while it does (a throttle)")
    ap.add_argument("--worker-ramp", type=float, default=WORKER_RAMP_S,
                    help="seconds between worker starts (default "
                         f"{WORKER_RAMP_S})")
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0,
                    help="idle the device this long after every launch; "
                         "priced in OPTIMIZATION_LOG.md against the launch "
                         "time at each filter")
    ap.add_argument("--gentle", action="store_true",
                    help="preset: --gpu-yield-ms 2 --workers 1 --worker-ramp "
                         "1.0")
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
                             f"swept to {term_letter(args.family)} = "
                             f"{st.get('k')}"))
    if args.fresh:
        for p in (ckpt_path(args.family), ckpt_path(args.family) + ".bak"):
            if os.path.exists(p):
                os.remove(p)
    return Campaign(args).run()


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    sys.exit(shutdown.graceful(main) or 0)
