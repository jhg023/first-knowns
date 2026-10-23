"""The campaign for the power ladders -- A229626: the smallest m with 2*m^k - 1 prime for k = 1..n; A229627: the smallest prime q with 2*q^k - 1 prime for k = 1..n; A229630: the smallest semiprime m with 2*m^k - 1 prime for k = 1..n; A229902: the smallest m with 19*m^k + 1 prime for k = 1..n.

    python launch.py                       the hunt: indefinite, resumable (A229626)
    python launch.py --family A229627      2*q^k - 1, q prime
    python launch.py --family A229630      2*m^k - 1, m semiprime
    python launch.py --family A229902      19*m^k + 1
    python launch.py --status              where the cursor is; reads, never writes
    python launch.py --selftest            the full gate battery; must end ALL GREEN

FOUR FAMILIES, ONE ENGINE, ONE CAMPAIGN AT A TIME.  `--family` names the
entry (power_reference.FAMILIES).  Each family has its own checkpoint,
ledger and config key, and a campaign hunts one of them.  No derived entry
rides on any.

EVERY FORM IS KNOWN AT EVERY INDEX, so the campaign can be planned, priced
and benchmarked at every filter it will promote itself through, in advance
(CLAUDE.md 5g): `plan_for` is the one place a configuration is derived,
score.py has a shape at each family's opening, and G18 compiles the
opening and the filters above it.  The openings (5g's test plan):
A229626 n = 10, A229627 n = 9, A229630 n = 9 and A229902 n = 9, each fresh
and resumed, and every filter each promotes itself into above that -- n =
10, 11, 12 on the first three, and on A229902 n = 10 at once (its first
segment records a(9) = a(8): power_reference.RUNS_PAST) and 11, 12 after.

THE LADDERS NEST, AND THE LINE STARTS AT THE FRONTIER TERM, INCLUSIVE.
Every condition of index n is one of index n + 1, so a(n+1) >= a(n), and a
term whose run passes its index is the next term as well -- which is why
the sweep for a(n) starts AT a(n - 1): A229902's published a(8) has a run
of nine, and the first segment of an A229902 campaign records a(9) = a(8)
as a discovery with its evidence and certificates.  Because the
classification reads runs to the filter plus RUN_AHEAD, everything a filter
swept past a find was already classified against the next filter's
conditions, so the CARRIED line is kept: the new filter resumes at the old
segment's end, re-denominated by floor into its own period with the clip at
the old boundary, so no line is skipped and none is swept twice
(_promotion_drill, on scratch files, on published terms).

THE DEVICE FERMAT STAGE (power_gpu; this project's own).  A prime kills
about one residue per form here, so millions of sieve survivors a second
leave the sieve; the device Fermat-tests their leading forms -- q itself on
A229627, then c*m^k + d for k = 1..CENSUS_FLOOR -- and only the values that
pass reach the host, a few thousand a second.  A failed Fermat test is a
proof of compositeness, so nothing with a run at the census floor or above
is dropped; the host re-reads every run.

THE EXCEPTION ZONE IS COVERED AT EVERY FILTER START.  A kill by a sieve
prime needs the value to exceed it, so the device starts above the engine
floor; the integers between the sweep's floor and the engine's are
classified one at a time on the host (power_search.prefix_hits).  Every
campaign's frontier is far above it; the drills that open low meet it.

THE RUN of a value: 0 outside the domain (a composite q; an m that is not a
semiprime), else the number of leading k whose value c*m^k + d is prime.  A
run of r >= the filter n is a DISCOVERY settling a(n)..a(r) at once; r = n
- 1 is NEAR; CENSUS_FLOOR <= r < n - 1 is counted only.

INDEFINITE BY DEFAULT (CONVENTIONS.md).  With no arguments this runs until
the engine ceiling, huntlib's K_CEIL = 1e40 on the term, every family.  The
proof crossing -- where classification stops being a proof -- is where
c*m^n + d passes 3.317e24, a few hundred at these filters: every campaign
starts past it, and it is a [MILESTONE], never a stop.  Every value is
multiplier x term^k +- 1, so a discovery's values are each proved by BLS75
on N + 1 = 2*m^k (Theorem 15) or N - 1 = 19*m^k (Theorem 1), from ONE
factorization of the term.

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
from sympy import isprime                                       # noqa: E402

import power_gpu as gpu                                         # noqa: E402
import power_model as model                                     # noqa: E402
import power_reference as ref                                   # noqa: E402
import power_search as cpu                                      # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
EVID = str(HERE / "evidence")


def TERM(fam):
    """The letter the OEIS name gives the term: m, q, m, m (rule 5i);
    every surface a person reads carries the integer under it."""
    return ref.letter(fam)


PLAN_VERSION = "p1"               # bump when plan_for's answer changes
#   p3 (2026-10-20), A229630 ONLY: the COFACTOR SIEVE -- the semiprime
#   wheel's first branch split into its zero-free and one-zero halves (four
#   branches), and every branch whose classes carry a wheel zero killing
#   residue 0 of every sieve prime too (power_gpu.engine_kills).  The same
#   period and segment as p2; the launches inside a segment are counted
#   over different branches, so a p2 cursor is ADOPTED (an open segment
#   re-swept).  1.30x at n = 11 (OPTIMIZATION_LOG.md round 6).
#   p2 (2026-10-19), A229630 ONLY: the SEMIPRIME WHEEL (power_gpu.
#   SemiprimeEngine) -- the plan's wheel with 2 in its first level and the
#   classes with two or more wheel-prime factors never enumerated, in three
#   branches; half the window, so the segment is the same line.  3.7x at
#   n = 11 (OPTIMIZATION_LOG.md round 5).  Its p1 cursor is ADOPTED.
PLAN_VERSIONS = {"A229630": "p3"}
#   p1 (2026-10-15): polynomial-runs' planner p1 taken whole -- the wheel
#   and the window chosen together by expected clock to a confirmed find
#   (power_gpu.plan) over every greedy wheel subset the kernel admits --
#   with the sieve depth a DEVICE decision (power_gpu.PRP_Q2: the Fermat
#   stage makes the host's load independent of it) and the floor it prices
#   from the index's own (a(n-1), or the model's median of it).


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
    p1, p2, p3, q2, pb = gpu.campaign_plan(n, fam, unit)
    return unit, p1, p2, p3, q2, pb


def plan_version(fam):
    return PLAN_VERSIONS.get(ref.family(fam), PLAN_VERSION)


def engine_class(fam):
    """GpuEngine, or on the semiprime domain the semiprime wheel."""
    return (gpu.SemiprimeEngine if ref.domain(ref.family(fam)) == "semiprime"
            else gpu.GpuEngine)


def x_floor(fam, n, frontier_x):
    """Where the sweep for a(n) starts: the frontier term ITSELF (the
    ladders nest, and the frontier term is a(n) too when its run reaches
    n -- A229902's a(8)), never below the domain's least member."""
    fam = ref.family(fam)
    return max(int(frontier_x), ref.floor_x(fam, 1))


def open_n(fam):
    """The filter a FRESH campaign of this family opens at."""
    return max(ref.KNOWN[ref.family(fam)]) + 1


# HOW OFTEN THE CHECKPOINT MOVES, in kernel launches, inside a segment.
CKPT_LAUNCHES = 32
# Runs shorter than this are not even counted -- and the device Fermat
# stage tests exactly this many leading forms, so nothing at the floor or
# above is ever dropped before the host reads it.
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

ENGINE_VERSION = "v1"
#   v1 (2026-10-15): polynomial-runs' engine v2, with the tail's residue
#   list sized per engine to the power forms' kill sets (up to n(n+1)/2 a
#   prime), primes that kill nothing left out of the sieve, a 100-prime
#   window (LIT_MAX), shapes that never starve their queues (STARVE_GUARD),
#   and the DEVICE FERMAT STAGE.
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


def config_key(fam, engine=None, plan=None):
    fam = ref.family(fam)
    return (f"{fam.lower()}-{engine or ENGINE_VERSION}-"
            f"{plan or plan_version(fam)}"
            f"-seg{CKPT_LAUNCHES}"
            f"-pbd{gpu.PB_DEFAULT}"
            f"-cpl{gpu.CAND_PER_LAUNCH4.bit_length() - 1}"
            f"w{gpu.CAND_PER_LAUNCH_WIDE.bit_length() - 1}"
            f"-f{CENSUS_FLOOR}")


def ckpt_path(fam):
    return str(HERE / f"campaign_checkpoint_{ref.family(fam).lower()}.json")


def ledger_path(fam):
    return str(HERE / "evidence" / f"{ref.family(fam).lower()}_discoveries.json")


# THE CURSORS A NEW PLAN ADOPTS (CONVENTIONS.md "Re-denominating a cursor
# across a wheel change").  A229630's p1 covered the same line with a
# different wheel, and its p2 with the same wheel in different branches, so
# only "every m below this is swept" carries over: the new plan runs at once
# from the start of the stored segment, floored into its own period with
# the clip there, and an OPEN segment is re-swept, its census counted twice
# (Campaign._adopt; the owner's call, 2026-10-19).
ADOPTS = {"A229630": ("p1", "p2")}

# EVERY reader of the checkpoint goes through this object and none of them
# takes a key list of its own (CONVENTIONS.md "Reading an existing cursor").
_POLICIES = {fam: checkpoint.CursorPolicy(
                 ckpt_path(fam), config_key(fam),
                 accept=tuple(config_key(fam, engine=e) for e in PREVIOUS_ENGINES),
                 adopt=tuple(config_key(fam, plan=p)
                             for p in ADOPTS.get(fam, ())))
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


def stopper_of(fam, x, run):
    """The value at k = run + 1 and why it stops the run."""
    fam = ref.family(fam)
    c, d = ref.coeffs(fam)
    v = c * int(x) ** (int(run) + 1) + d
    return int(v), ("composite" if v >= 4 else "not prime")


def verify(x, run, fam, witness=True):
    """The three independent confirmations plus the bounding witness.

    1. huntlib's Miller-Rabin over every value of the run (and q itself on
       A229627), a strong probable-prime chain past the proof crossing --
       every value of a DISCOVERY is then PROVED by certificate;
    2. sympy's BPSW, an independent implementation, which must agree on the
       run LENGTH and on the domain, not merely on primality;
    3. a from-scratch re-derivation by different machinery -- the CPU
       engine, which marks the dense line and uses no wheel at all, must
       agree that x survives a sieve at a DIFFERENT depth from the
       campaign's, at the filter the run reaches.

    plus a factor witness for the composite that STOPS the run, which is
    what bounds the claim to exactly `run`.  witness=False is the [NEAR]
    path: verified, not evidenced, no factoring.
    """
    fam = ref.family(fam)
    x, run = int(x), int(run)
    vals = ref.values(fam, x, run)
    # the re-sieve is only a proof where every value exceeds the depth
    q2 = min(4096, min(vals) - 1)
    legs = {"mr_chain": all(mr_is_prime(v) for v in vals),
            "domain": cpu.in_domain_fast(fam, x) and ref.in_domain(fam, x),
            "sympy_bpsw": ref.run_length(fam, x, cap=run + 1) == run,
            "resieve_other_wheel": (q2 < 2 or
                                    cpu.CpuEngine(max(run, 1), fam, q2=q2).survives(x))}
    stop, why = stopper_of(fam, x, run)
    legs["stopper_composite"] = (why == "not prime") or not mr_is_prime(stop)
    ok = all(legs.values())
    wit = None
    if witness and why == "composite" and legs["stopper_composite"]:
        wit = stopper_witness(stop)
    return ok, legs, {"k": run + 1, "value": stop, "factor": wit, "why": why}


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


# THE CERTIFICATE ROUTE.  Every value is c*x^k + d with d = -+1, so the
# value PLUS one (2*m^k, on the three 2*m^k - 1 ladders) or MINUS one
# (19*m^k, on A229902) is completely factored by one factorization of the
# term: BLS75 Theorem 15 (a Lucas sequence per prime of 2*m) or Theorem 1,
# at any height and for any k.  A prime factor of the term past the
# deterministic bound -- A229627's q itself, at every height a campaign will
# see past 3.3e24 -- is admitted with a subproof of its own.  The
# structureless search (certify_value) is the fallback, never the route.
CERT_RETRY_CURVES = 200
CERT_RETRY_SPLITS = 16


def certify_value(N, fac=None, fac_plus=None):
    """A RE-VERIFIED primality certificate for one value, or None."""
    N = int(N)
    proof = certificate.prove(N, fac=fac, fac_plus=fac_plus)
    if proof is not None and not certificate.verify(proof)[0]:
        proof = None
    if proof is None and (fac is not None or fac_plus is not None):
        proof = certificate.prove(N)
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
    if proof is None:
        proof = certificate.prove(N, ecm_curves=CERT_RETRY_CURVES,
                                  budget=CERT_RETRY_SPLITS)
        if proof is not None and not certificate.verify(proof)[0]:
            proof = None
    return proof


def term_factors(x):
    """{p: e} of the term, every p proved (or subproved by the certificate
    that admits it): huntlib's bounded chain, then sympy's factorint on
    what is left -- the one factorization a discovery costs."""
    return {int(p): int(e) for p, e in certificate.factor_full(int(x)).items()}


def certify_run(x, run, fam):
    """A re-verified certificate for every value of a run: ({key: proof},
    [the keys left UNPROVED]).  Keys are the exponent k, "0" for q itself
    on A229627."""
    fam = ref.family(fam)
    x, run = int(x), int(run)
    c, d = ref.coeffs(fam)
    fx = term_factors(x)
    fc = {int(p): int(e) for p, e in certificate.factor_full(c).items()}
    certs, unproved = {}, []
    if ref.domain(fam) == "prime":
        certs["0"] = certify_value(x)
        if certs["0"] is None:
            unproved.append("0")
    for k in range(1, run + 1):
        N = c * x ** k + d
        side = dict(fc)
        for p, e in fx.items():
            side[p] = side.get(p, 0) + e * k
        proof = (certify_value(N, fac_plus=side) if d == -1
                 else certify_value(N, fac=side))
        certs[str(k)] = proof
        if proof is None:
            unproved.append(str(k))
    return certs, unproved


def also_settles(fam, x, run, settles):
    """What a find settles in DERIVED entries: none here."""
    ref.family(fam)
    return []


# ----------------------------- classification -------------------------------

def filter_forms(fam, n, cap=None):
    """(c, d, domain) for a pool worker: what the k-th value is and what
    the term must be.  A worker is another process; it is handed what it
    needs."""
    fam = ref.family(fam)
    c, d = ref.coeffs(fam)
    return (int(c), int(d), ref.domain(fam))


def sprp_run(x, forms, cap, floor=CENSUS_FLOOR):
    """The run of x, read with a base-2 strong probable-prime test on each
    value, the powers built incrementally; and the DOMAIN decided exactly
    wherever the answer can matter (a run at the census floor or above).

    A failed base-2 test is a PROOF of compositeness (huntlib.primes), so
    the screen can only overstate a run, never understate it.  The census
    is counted on this chain -- it is a count, not a claim -- and every
    value that is narrated (a NEAR) or recorded (a DISCOVERY) is verified
    three ways first (verify).  A run under the census floor is returned as
    the screen read it, without the domain: nothing reads it.
    """
    c, d, dom = forms
    x, cap = int(x), int(cap)
    if dom == "prime" and not sprp_base2(x):
        return 0
    r, pw = 0, x
    while r < cap:
        v = c * pw + d
        if v < 2 or not sprp_base2(v):
            break
        r += 1
        pw *= x
    if r < floor:
        return r
    if dom == "prime" and not mr_is_prime(x):
        return 0
    if dom == "semiprime" and not cpu.is_semiprime_fast(x):
        return 0
    return r


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
    """The condition of exponent k in the entry's own letters."""
    fam = ref.family(fam)
    t = TERM(fam)
    if k == 0:
        return f"{t} prime"
    c, d = ref.coeffs(fam)
    return f"{c}*{t}^{k} {'+' if d > 0 else '-'} {abs(d)}"


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
        # DRILLS ONLY: open below the published frontier so that a drill's
        # "find" is a real published term; and stop before the filter of
        # `stop_n`, so a drill never sweeps an open index (CLAUDE.md 0a).
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
        # the x below which the line is covered by an EARLIER filter's
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
        self._stored = None
        self.loaded = self.load()
        self.eng = self._build_engine(self.filter_n())
        if self._stored_n is not None and self._stored_n != self.filter_n():
            raise ValueError(
                f"{self.ckpt} holds a cursor for filter n = {self._stored_n} "
                f"but this campaign's next open term is a({self.filter_n()}): "
                f"the stored `found` and the stored filter disagree, so the "
                f"cursor cannot be read")
        if self._load_kind == "adopted":
            self._adopt()
        elif self._stored_w and self._stored_w != int(self.eng.W):
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
        return engine_class(self.fam)(n, self.fam, p1=p1, p2=p2, p3=p3,
                                      q2=q2, unit=unit, pb=pb, seg_cap=pb,
                                      prp=CENSUS_FLOOR)

    def _adopt(self):
        """A cursor of a superseded plan (ADOPTS): only "every term below
        the stored claim is swept" carries over, and the new plan runs AT
        ONCE from the claim, floored into its own period with the clip
        there.  An OPEN segment (u > 0) is re-swept from its start on the
        new plan, so the census counts the part the old engine had already
        swept TWICE -- the owner's call (2026-10-19) over finishing it on
        the old engine first, which held A229630's 3.7x back for ~2.5 h of
        its open half against ~1.5 h for the whole segment on p2."""
        st = self._stored
        old_key = st["key"]
        claim = int(st.get("k", 0))
        lost = self.u
        self.cover_x = max(self.cover_x, claim)
        self.j, self.u, self.pending = self.floor_period(), 0, []
        log("STAGE",
            f"cursor ADOPTED from {old_key} by {config_key(self.fam)}: the "
            f"line below {self.term} = {claim:,} is swept, and the new plan "
            f"starts there now, floored into its own period with the clip at "
            f"the claim"
            + (f"; the old segment was open at launch {lost:,} of "
               f"{self._stored_units[1]:,}, so it is re-swept from its start "
               f"on the new plan and the census counts the part already "
               f"swept TWICE" if lost else ""))

    # ------------------------------------------------------------- frontier
    def frontier(self):
        top = self._known_top
        for n in self.found:
            top = max(top, int(n))
        return top

    def frontier_k(self):
        n = self.frontier()
        return int(self.found.get(str(n), ref.KNOWN[self.fam].get(n, 0)))

    def filter_n(self):
        return self.frontier() + 1

    def x_start(self):
        """The floor of THIS filter's sweep: the frontier term (inclusive),
        or the carried coverage of the previous filter, whichever is
        higher."""
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
        """How far past the filter a survivor's run is read: RUN_AHEAD, or
        in a drill no further than the index it was opened to find (a drill
        never settles an index it was not opened for; CLAUDE.md 0a)."""
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
                f"the value plus or minus one, which is the multiplier "
                f"times {self.term}^k -- factored by one factorization of "
                f"{self.term} -- re-verified before it is written; the "
                f"ceiling is {self.term} < "
                f"{cpu.k_ceil(self.filter_n(), self.fam):.4g}")

    # ---------------------------------------------------------- checkpoint
    def state(self):
        return {"key": self.key,
                "engine": ENGINE_VERSION,
                "plan": self.key.split("-")[2],
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
                        f"ONE condition short of a({frontier + 1})!")
            return False
        self.record_discovery(k, run)
        return True

    def record_discovery(self, x, run):
        frontier = self.frontier()
        n = self.filter_n()
        self.hb.doing(f"verifying run-{run} {self.term}={x}")
        # the run, re-read with NO cap by the oracle: a run at the
        # classification's cap may be longer
        full = ref.run_length(self.fam, x, cap=64)
        if full < run or full < n or x < self.x_start():
            log("ALARM", f"claimed {self.oeis} a({n}) = {x} (run {run}) is "
                         f"not a term by the oracle: run {full}, floor "
                         f"{self.x_start()}")
            raise SystemExit(2)
        run = full
        ok, legs, stop = verify(x, run, self.fam)
        if not ok:
            log("ALARM", f"claimed a({frontier + 1}) = {x} failed the "
                         f"protocol: {legs}")
            raise SystemExit(2)
        settles = list(range(frontier + 1, run + 1))
        self.hb.doing(f"certifying run-{run} {self.term}={x}")
        certs, unproved = certify_run(x, run, self.fam)
        routes = {}
        for c in certs.values():
            r = c.get("proof") if c else "none"
            routes[r] = routes.get(r, 0) + 1
        also = also_settles(self.fam, x, run, settles)
        k0 = 0 if ref.domain(self.fam) == "prime" else 1
        vals = ref.values(self.fam, x, run)
        fx = term_factors(x)
        ev = {**evidence.header(self.oeis, ref.FAMILIES[self.fam]["forms"],
                                self.term, x, settles),
              "filter_n": int(n), "run": int(run), "settles": settles,
              "conditions": {str(k0 + i): condition(self.fam, k0 + i)
                             for i in range(len(vals))},
              "values": {str(k0 + i): int(v) for i, v in enumerate(vals)},
              f"{self.term}_factored": {str(p): e for p, e in sorted(fx.items())},
              "verification": legs,
              "stopper": {ref.FAMILIES[self.fam]["exp"]: stop["k"],
                          "condition": condition(self.fam, stop["k"]),
                          "value": int(stop["value"]),
                          "why": stop["why"],
                          "factor": stop["factor"]},
              "certificates": certs,
              "certificates_verified": not unproved,
              "unproved": unproved,
              "proof_routes": routes,
              "also_settles": also,
              "least_claim": {"swept_from": int(self.x_start()),
                              "campaign_started_at": int(self.start_x),
                              "swept_to": int(x),
                              "floor": (f"a({frontier}) = {self.frontier_k()}, "
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
        if ref.domain(self.fam) == "semiprime":
            ev[f"{self.term}_semiprime"] = sorted(
                p for p, e in fx.items() for _ in range(e))
        for m in settles:
            self.found[str(m)] = int(x)
        path = evidence.record(
            ev, self.evid, evidence_name(self.oeis, settles[0], x),
            self.ledger, key=self.term,
            label="%s a(%s)" % (self.oeis, ",".join(map(str, settles))))
        self.discoveries += 1
        proved = len(certs) - len(unproved)
        lines = [
            headline(self.oeis, settles, x),
            f"run {run}: {ref.FAMILIES[self.fam]['forms'].split(',')[0]} "
            f"prime for k = 1..{run}",
            f"stopped at k = {stop['k']}: {condition(self.fam, stop['k'])} is "
            f"{stop['why']}"
            + (f" = {stop['factor']} x ..." if stop["factor"] else ""),
            f"verified 3 ways, {proved} of {len(certs)} certificates "
            f"re-verified ({', '.join(f'{r} x{c}' for r, c in sorted(routes.items()))}), "
            f"evidence {path}"]
        if unproved:
            lines.append(f"UNPROVED at k = {unproved}: those values passed "
                         f"the Miller-Rabin chain and BPSW and no "
                         f"certificate landed within the bounded effort; "
                         f"the find stands on the three legs; certify them "
                         f"by hand from the evidence file")
        banner("DISCOVERY", lines)

    def follow_frontier(self, old_boundary_x):
        """After a find: rebuild the engine at the next open index; the
        classified line is carried and the sweep resumes at the old
        segment's end, re-denominated by floor into the new period with the
        clip at the old boundary."""
        old = self.eng
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
        filter: every integer in the forced class between the sweep's floor
        and the engine's floor, through the same taxonomy as a device
        survivor.  Returns True if a find landed there."""
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
                                   cap=self.run_cap())
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
        # a run the frontier has already settled the successor of is
        # counted only, at every frontier this segment can reach (it only
        # rises, at the segment's end): COUNT it here rather than holding
        # its value to the segment's end, where it was copied into every
        # checkpoint of the segment -- 152,246 of them, 0.31 s a save, at
        # A229626 n = 11 (round 4)
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
        log("STAGE", device_report(self.eng.bytes_held()))
        cfg = self.eng.config()
        log("STAGE",
            f"sweeping the {self.term} line to {target:.4g}; {self.oeis} "
            f"({ref.FAMILIES[self.fam]['forms']}) filter n = "
            f"{self.filter_n()}; wheel W = {self.eng.W:,} at unit "
            f"{self.eng.unit} ({self.eng.R:,} residues, "
            + (self.eng.shape_str() + " in the semiprime wheel's branches"
               if hasattr(self.eng, "shape_str") else
               f"{self.eng.R1} x {self.eng.R2} x {self.eng.R3}")
            + f", {100.0 * self.eng.density():.6f}% "
            f"of the line); a segment is {self.eng.seg_periods} periods "
            f"({self.eng.seg_periods * self.eng.W:.4g} of line) in "
            f"{self.eng.launches_per_segment} launches of "
            f"{cfg['cand_per_launch']:.3g} candidates; the sieve runs to "
            f"{self.eng.q2} and the device Fermat-tests the first "
            f"{len(self.eng.prp_forms)} conditions of every survivor; the "
            f"sweep's floor is {self.term} = {self.x_start():,}; resume at "
            f"period {self.j}, launch {self.u} ({self.term} = "
            f"{self.u_progress(self.j, self.u):,})")
        for n, qs in sorted(model.predictions(
                self.fam, self.frontier(), self.frontier_k(),
                n_ahead=3, ceiling=cpu.k_ceil(self.filter_n(), self.fam)).items()):
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
            cap = self.run_cap()
            forms = filter_forms(self.fam, self.filter_n())
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
                        f"line; {held} value{'' if held == 1 else 's'} one "
                        f"short of the frontier or past it classified in "
                        f"numerical order, the census counted as it came"
                        + (f"; {self._plog_n} segments closed since the last "
                           f"such line" if self._plog_n > 1 else "") + ")")
                    self._plog_t, self._plog_n = time.time(), 0
                if found_now:
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


# --------------------------------- selftest ---------------------------------

def _event_cases():
    """All four outcomes of the taxonomy, on this project's mathematics: at
    filter n = 10 (frontier 9) a full run is 10, one short is 9."""
    return [((10, 9), "DISCOVERY"),
            ((12, 9), "DISCOVERY"),       # a long run settles several at once
            ((9, 9), "NEAR"),
            ((8, 9), "CENSUS"),
            ((6, 9), "CENSUS"),
            ((5, 9), None),
            ((0, 9), None)]


# The canaries: published terms a mini-hunt reaches from the frontier term
# in a second or two, in x space and in each forced class.
_CANARIES = (("A229626", 7, 1), ("A229626", 8, 1),
             ("A229627", 6, 6), ("A229627", 7, 6),
             ("A229630", 6, 1),
             ("A229902", 6, 10), ("A229902", 7, 10))


def _canary_hunt():
    """The stream must organically rediscover published terms, in every
    family, from the frontier term (inclusive), so FIRST is a claim about
    the line."""
    hits_all = []
    for fam, n, unit in _CANARIES:
        if cpu.forced_unit(n, fam) % unit:
            return False, f"CANARY FAIL: unit {unit} is not forced at n = {n} of {fam}"
        want = ref.KNOWN[fam][n]
        q2 = 4096
        # the device Fermat stage on all n forms: what reaches the host is
        # a superset of every value whose run reaches n.  A229630 runs the
        # semiprime wheel, on three levels so that all three branches sweep
        if ref.domain(fam) == "semiprime":
            eng = gpu.SemiprimeEngine(n, fam, p1=[2, 3, 5, 7], p2=[11, 13],
                                      p3=[17], q2=q2, unit=unit, pb=32, prp=n)
        else:
            eng = gpu.GpuEngine(n, fam, p1=13, p2=None, p3=None, q2=q2,
                                unit=unit, prp=n)
        lo = x_floor(fam, n, ref.KNOWN[fam][n - 1])
        pre = [x for x, r in cpu.prefix_hits(fam, n, q2, floor=n) if x >= lo]
        if pre and min(pre) < want:
            return False, f"CANARY FAIL: {fam} n={n}: the zone holds {min(pre)}"
        start = max(lo, cpu.k_floor(q2, n, fam) + 1)
        ceng = cpu.CpuEngine(n, fam, q2=q2)
        surv = eng.survivors_j(start // eng.W, want // eng.W + 1, k_min=start)
        hits = [int(k) for k in surv if ceng.run_length(int(k), cap=n) >= n]
        if not hits or min(hits) != want:
            return False, (f"CANARY FAIL: {fam} filter n={n} unit={unit} "
                           f"found {min(hits) if hits else None}, "
                           f"expected a({n}) = {want}")
        hits_all.append(f"{fam} a({n})" + (f" (class {eng.r0} mod {unit})"
                                           if unit > 1 else ""))
    return True, ("canary ok: the GPU stream rediscovered " +
                  ", ".join(hits_all) + " as FIRST occurrences from the "
                  "frontier term, in x space and in class space, every "
                  "family, through the device Fermat stage on every form "
                  "(A229630 through the semiprime wheel's three branches, "
                  "the domain then decided on the host)")


def _true_run(fam, n):
    """The run of the published a(n): n, or more where the entry's term
    passes its index (power_reference.RUNS_PAST)."""
    return ref.RUNS_PAST.get(fam, {}).get(n, n)


def _protocol_drill():
    """The discovery protocol, tested in BOTH directions, on every family."""
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        run = _true_run(fam, top)
        ok, legs, stop = verify(x, run, fam)
        if not ok or stop["k"] != run + 1 or stop["factor"] is None:
            return False, (f"PROTOCOL FAIL: genuine a({top}) = {x} ({fam}) "
                           f"at its run {run} rejected: {legs} {stop}")
        if stop["value"] % stop["factor"] or stop["factor"] in (1, stop["value"]):
            return False, f"PROTOCOL FAIL: {fam}: the witness is not a factor"
        bad, legs_b, _ = verify(x, run + 1, fam)
        if bad:
            return False, (f"PROTOCOL FAIL: fake run-{run + 1} claim at {x} "
                           f"({fam}) ACCEPTED ({legs_b})")
        # an earlier term mislabelled as the frontier's run
        prev = max(n for n in ref.KNOWN[fam] if ref.KNOWN[fam][n] < x)
        fake, _lc, _ = verify(ref.KNOWN[fam][prev], run, fam)
        if fake:
            return False, f"PROTOCOL FAIL: {fam}: a({prev}) accepted as a run-{run}"
    # THE DOMAINS: a composite q on A229627 and a non-semiprime m on
    # A229630 are rejected however their forms behave (9: 17, 161 -- 17 is
    # prime; 8 = 2^3: 15 -- composite, so use 12 = 2^2*3: 23, 287 = 7*41)
    okd, legs_d, _ = verify(9, 1, "A229627")
    if okd or legs_d["domain"]:
        return False, "PROTOCOL FAIL: a COMPOSITE q was accepted on A229627"
    okd, legs_d, _ = verify(12, 1, "A229630")
    if okd or legs_d["domain"]:
        return False, "PROTOCOL FAIL: a non-semiprime m was accepted on A229630"
    oks, legs_s, _ = verify(6, 5, "A229630")
    if not oks:
        return False, f"PROTOCOL FAIL: the semiprime 6 with run 5 was rejected: {legs_s}"
    return True, ("protocol ok, every family: each frontier term accepted at "
                  "its true run (A229902's a(8) at nine) with a factor "
                  "witness for its stopper, a run one too long and a "
                  "mislabelled earlier term both rejected, and the domains "
                  "enforced (a composite q on A229627 and a non-semiprime m "
                  "on A229630 rejected, the entry's own example 6 accepted)")


def _ceiling_drill():
    """Every ceiling RAISES rather than computing, on every family."""
    raised = []
    for fam, n in (("A229626", 10), ("A229627", 9), ("A229630", 9),
                   ("A229902", 10)):
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
    try:
        gpu.wheel(7, "A229626", 53)
        return False, "CEILING FAIL: an oversized flat wheel was built"
    except ValueError:
        raised.append("wheel RES_MAX")
    try:
        gpu.GpuEngine(10, "A229626", p1=31, p2=None, p3=None, q2=4096)
        return False, "CEILING FAIL: a first-level modulus past u32 was built"
    except ValueError:
        raised.append("W1 < 2^32")
    try:
        gpu.GpuEngine(7, "A229626", p1=13, p2=37, p3=None, q2=4096)
        return False, "CEILING FAIL: an oversized second level was accepted"
    except ValueError:
        raised.append("gridDim.y")
    # the residue list holds NRES_MAX kills a prime and a prime can kill up
    # to n(n+1)/2: the first index past n_max is refused
    for fam in ("A229626", "A229627"):
        n = cpu.n_max(fam) + 1
        if ref.maxkills(fam, n) <= gpu.NRES_MAX:
            return False, f"CEILING FAIL: {fam} n = {n} fits the residue list"
        try:
            gpu.GpuEngine(n, fam, p1=13, p2=None, p3=None, q2=1024)
            return False, "CEILING FAIL: a filter whose kills overflow the tail's residue list was accepted"
        except ValueError:
            raised.append(f"maxkills <= NRES_MAX ({fam} n = {n})")
    for fam, unit in (("A229626", 2), ("A229626", 6), ("A229627", 30),
                      ("A229902", 30), ("A229627", 12)):
        try:
            gpu.GpuEngine(10, fam, p1=13, p2=None, p3=None, q2=1024, unit=unit)
            return False, f"CEILING FAIL: unit {unit}, which nothing forces on {fam}, was accepted"
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


def _check_cert(c, N, label, route=None):
    if c is None or c.get("proof") not in _BLS_ROUTES:
        return False, (f"{label}: not proved by a BLS75 route "
                       f"({c and c.get('proof')})")
    if route is not None and c.get("proof") != route:
        return False, f"{label}: proved by {c.get('proof')}, not {route}"
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
    each frontier term's run (values to 112-161 digits) on the route its
    sign gives -- Theorem 15 on N + 1 = 2*m^k, Theorem 1 on N - 1 =
    19*m^k -- and AT THE CEILING, terms near 1e40 on both routes, A229627's
    prime q past the deterministic bound exercising the subproof, which
    cannot be stripped."""
    parts = []
    t0 = time.time()
    for fam in ref.FAMILIES:
        top = max(ref.KNOWN[fam])
        x = ref.KNOWN[fam][top]
        run = _true_run(fam, top)
        certs, unproved = certify_run(x, run, fam)
        if unproved:
            return False, f"CERTIFICATE FAIL: {fam} a({top}) left {unproved} unproved"
        c, d = ref.coeffs(fam)
        want = "bls75-thm15" if d == -1 else "bls75-thm1"
        for key, proof in certs.items():
            N = x if key == "0" else c * x ** int(key) + d
            if N < MR_VALID_BELOW:
                if proof.get("proof") != "deterministic-mr":
                    return False, f"CERTIFICATE FAIL: {fam} k = {key} under the bound took {proof.get('proof')}"
                continue
            ok, why = _check_cert(proof, N, f"{fam} a({top}) k = {key}", want)
            if not ok:
                return False, "CERTIFICATE FAIL: " + why
        routes = sorted({p["proof"] for p in certs.values()})
        parts.append(f"{fam} a({top})'s {len(certs)} values ({'/'.join(routes)})")
    subbed = None
    for fam in ("A229626", "A229627", "A229902"):
        c, d = ref.coeffs(fam)
        r0, u = cpu.forced_class(12, fam)
        x = ceiling.K_CEIL - 10 ** 30
        x = x - x % u + r0
        want = "bls75-thm15" if d == -1 else "bls75-thm1"
        found = None
        for _ in range(200000):
            if ref.domain(fam) == "prime" and not (sprp_base2(x) and isprime(x)):
                x += u
                continue
            ps = [k for k in range(1, 5) if isprime(c * x ** k + d)]
            if ps:
                found = (x, ps[0])
                break
            x += u
        if found is None:
            return False, f"CERTIFICATE FAIL: no prime value of {fam}'s shape near the ceiling"
        x, k = found
        certs, unproved = certify_run(x, 0, fam)    # q itself, on A229627
        fx = term_factors(x)
        side = {}
        for p, e in certificate.factor_full(c).items():
            side[int(p)] = int(e)
        for p, e in fx.items():
            side[p] = side.get(p, 0) + e * k
        N = c * x ** k + d
        proof = (certify_value(N, fac_plus=side) if d == -1
                 else certify_value(N, fac=side))
        ok, why = _check_cert(proof, N, f"{fam} at {x:.4g} k = {k}", want)
        if not ok:
            return False, "CERTIFICATE FAIL (at the ceiling): " + why
        if proof.get("subproofs") and subbed is None:
            subbed = (fam, N, proof)
        parts.append(f"{fam} {want} at {TERM(fam)} = {x:.4g}, k = {k} "
                     f"({len(str(N))} digits)")
    if subbed is None:
        return False, "CERTIFICATE FAIL: no ceiling certificate exercised the recursion"
    _lab, N, proof = subbed
    if certificate.verify({a_: b_ for a_, b_ in proof.items()
                           if a_ != "subproofs"})[0]:
        return False, "CERTIFICATE FAIL: a proof stripped of its subproof verified"
    parts.append(f"the recursion exercised ({len(proof['subproofs'])} "
                 f"subproof(s) for {_lab}'s term past the bound, which cannot "
                 f"be stripped); {time.time() - t0:.1f} s in all")
    return True, "certificates ok: " + "; ".join(parts)


def _resume_drill():
    """A split sweep must equal the unsplit sweep, exactly, across the seams
    a real interrupt leaves: a period boundary, the (j, u) sub-period
    cursor, and the clipped first period -- on every family's engine
    shape, x space and both classes, the Fermat stage on and off."""
    total = 0
    for lab, fam, n, kw, x_at, span, cut in (
            ("one-level", "A229626", 10, dict(p1=17, p2=None, p3=None, q2=512),
             10 ** 13, 300, 117),
            ("two-level", "A229627", 10, dict(p1=19, p2=31, p3=None, q2=8192,
                                              unit=6, pb=32),
             10 ** 15, 3, 1),
            ("three-level", "A229902", 10, dict(p1=13, p2=17, p3=19, q2=1024,
                                                unit=10, pb=32),
             9 * 10 ** 14, 300, 111),
            ("Fermat stage", "A229626", 9, dict(p1=13, p2=23, p3=None,
                                                q2=2048, pb=32, prp=1),
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
    # THE (j, u) SEAM, in x space and in class space, in the segment that
    # starts at the clipped first period and in an ordinary one
    for eng, j0s in ((gpu.GpuEngine(10, "A229626", p1=11, p2=17, p3=23, q2=1024,
                                    nu=4, pb=32),
                      ((lambda e: e.j_of(9 * 10 ** 14), None), (lambda e: 0, 10 ** 6))),
                     (gpu.GpuEngine(10, "A229627", p1=11, p2=19, p3=29, q2=1024,
                                    nu=8, unit=6, pb=32),
                      ((lambda e: e.j_of(10 ** 16), None),
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
                  f"three-level wheels in x space and in the classes 1 (mod "
                  f"6) and 0 (mod 10), and with the Fermat stage on; across "
                  f"the (j, u) sub-segment seam in x space (A229626) and in "
                  f"class space (A229627), and inside the clipped first "
                  f"segment on both ({total} survivors across the seams)")


def _classification_drill():
    """The base-2 screen reads the same runs as the all-bases chain on real
    survivors, the pool's chunked answer == the serial one, and the
    domains are honoured."""
    fam, n = "A229626", 7
    eng = gpu.GpuEngine(n, fam, p1=13, p2=23, p3=None, q2=2048)
    j0 = eng.j_of(10 ** 9)
    surv = eng.survivors_j(j0, j0 + 1)
    if len(surv) < 3 * CHUNK:
        return False, f"CLASSIFY FAIL: only {len(surv)} survivors"
    forms = filter_forms(fam, n)
    cap = n + RUN_AHEAD
    two = [sprp_run(k, forms, cap) for k in surv]
    ceng = cpu.CpuEngine(n, fam, q2=64)
    full = [ceng.run_length(k, cap=cap) for k in surv]
    if two != full:
        i = next(i for i in range(len(surv)) if two[i] != full[i])
        return False, (f"CLASSIFY FAIL: the base-2 screen read run {two[i]} "
                       f"and the all-bases chain {full[i]} at m = {surv[i]}")
    with _pool_factory(2) as pool:
        parts = _submit(pool, forms, cap, surv)
        got = [r for ks, f in parts for r in f.result()]
    if got != full:
        return False, "CLASSIFY FAIL: the pool's chunked result differs"
    # THE DOMAINS through the pool's own form lists: on A229627 a composite
    # q reads 0 and 3 reads 3; on A229630 the semiprime 6 reads 5 and 12
    # (2*2*3) reads 0 however its forms behave; and every frontier term
    # reads its true run at its own index and is capped under a cap
    fq, fs = filter_forms("A229627", 9), filter_forms("A229630", 9)
    if (sprp_run(9, fq, 9, floor=1) != 0 or sprp_run(3, fq, 9, floor=1) != 3
            or sprp_run(6, fs, 9, floor=1) != 5
            or sprp_run(12, fs, 9, floor=1) != 0):
        return False, "CLASSIFY FAIL: a domain through the pool's forms"
    for f in ref.FAMILIES:
        top = max(ref.KNOWN[f])
        x = ref.KNOWN[f][top]
        run = _true_run(f, top)
        if (sprp_run(x, filter_forms(f, top), run + 3) != run
                or sprp_run(x, filter_forms(f, top), CENSUS_FLOOR) != CENSUS_FLOOR):
            return False, f"CLASSIFY FAIL: {f} a({top}) through the pool's forms"
    return True, (f"classification ok: the base-2 screen == the all-bases "
                  f"chain on {len(surv)} real survivors (max run "
                  f"{max(full)}), {len(parts)} pool chunks reassemble to the "
                  f"serial answer, every frontier term reads its true run "
                  f"and is capped under a cap, a composite q reads 0 on "
                  f"A229627 and a non-semiprime m reads 0 on A229630")


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
# a(DRILL_N + 1) are published and a few seconds of device apart, and the
# run is BOUNDED before the filter of DRILL_N + 2 (`stop_n`), so no drill
# ever sweeps an open index (CLAUDE.md 0a).  A229626: a(7) (from a(6) =
# 11256895) then a(8) = 45779314036; A229627: a(6), a(7) = 24137752519;
# A229630: a(6) = 118909855, a(7) = 5740959589; A229902: a(6), a(7) =
# 4355942080.
DRILL_N = {"A229626": 7, "A229627": 6, "A229630": 6, "A229902": 6}


def _promotion_drill():
    """A FIND MOVES THE FILTER and CARRIES THE LINE: the sweep resumes at
    the old boundary, floored into the new period with the clip at the
    boundary.  On scratch files, with the REAL published term as the
    find."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="power-promote-")
    path = str(pathlib.Path(tmp) / "c.json")
    rows = []
    for fam in ref.FAMILIES:
        n0 = DRILL_N[fam]
        found_x = ref.KNOWN[fam][n0]
        pol = _POLICIES[fam].at(path)
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
                         cursor=_POLICIES[fam].at(path))
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
                      cursor=_POLICIES[fam].at(path))
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
                     cursor=_POLICIES[fam].at(path))
            return False, f"PROMOTION FAIL: {fam} read a cursor stored at the wrong index"
        except ValueError:
            pass
        for ext in ("", ".bak"):
            if os.path.exists(path + ext):
                os.remove(path + ext)
        rows.append(f"{fam} n = {n0} -> {n0 + 1}: wheel {before[4]} -> "
                    f"({c.eng.p1},{c.eng.p2},{c.eng.p3}), period {before[2]:.3g} "
                    f"-> {c.eng.W:.3g}, carried to the old boundary {swept_old:.4g}")
    return True, ("promotion ok: " + "; ".join(rows) + " -- the engine is "
                  "rebuilt with one more condition, an interrupt between the "
                  "find and the promotion writes a checkpoint that still "
                  "opens, the classified line is carried to the old "
                  "boundary, the cursor round-trips, and a cursor stored at "
                  "the wrong index is REFUSED")


def _adoption_drill():
    """A229630's p1 AND p2 CURSORS ARE ADOPTED BY THE COFACTOR SIEVE
    (ADOPTS), on scratch files at the family's opening, both ways each can
    arrive: a CLOSED segment and an OPEN one (re-swept from its start, the
    owner's call 2026-10-19).  Either way the new plan runs at once from
    the claim with the clip there, its own key is what the next save
    writes, and the census, the finds and the campaign's start are carried
    untouched.  p1 is the plain wheel (its own period); p2 is the semiprime
    wheel in three branches -- the same period and segment as p3, its
    launches counted over branches that no longer exist."""
    import tempfile
    fam = "A229630"
    tmp = tempfile.mkdtemp(prefix="power-adopt-")
    path = str(pathlib.Path(tmp) / "c.json")
    n0 = open_n(fam)
    unit = cpu.forced_unit(n0, fam)
    p1, p2, p3, q2, pb = gpu.plan(n0, fam, unit)
    old = gpu.GpuEngine(n0, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit,
                        pb=pb, seg_cap=pb, prp=CENSUS_FLOOR)
    s1, s2, s3, _q2, spb = gpu.semiprime_plan(n0, fam, unit)
    w_semi = unit
    for q in gpu._wheel_primes(s1, s2, s3):
        w_semi *= q
    olds = (("p1", (p1, p2, p3), int(old.W), int(old.seg_periods),
             int(old.launches_per_segment)),
            ("p2", (s1, s2, s3), w_semi, int(spb),
             int(old.launches_per_segment)))
    for plan, _wh, _w, _seg, nl in olds:
        if config_key(fam, plan=plan) not in _POLICIES[fam].adopt or nl < 2:
            return False, (f"ADOPT FAIL: the {plan} key is not adopted, or "
                           f"its engine has {nl} launches a segment")
    a8 = ref.KNOWN[fam][n0 - 1]
    census = {"6": 5, "7": 2}

    def stored(plan, wh, w_old, seg, nl, j_old, u):
        return {"key": config_key(fam, plan=plan), "engine": ENGINE_VERSION,
                "plan": plan, "family": fam, "n": n0, "q2": int(q2),
                "wheel": [list(lv or []) for lv in wh],
                "unit": unit, "j": j_old, "u": u,
                "seg_periods": seg, "launches_per_segment": nl,
                "W": w_old, "k": j_old * w_old,
                "k_start": a8, "start_x": a8, "cover_x": 0, "zone_n": n0,
                "pending": [[a8 + 1, n0 - 1]] if u else [],
                "found": {}, "census": dict(census), "passed": [],
                "elapsed": 100.0, "discoveries": 0, "near": 3,
                "survivors": 77}
    rows = []
    try:
        pol = _POLICIES[fam].at(path)
        for plan, wh, w_old, seg, nl, u, what in (
                [o + (0, "a closed segment") for o in olds]
                + [o + (1, f"an open one (launch 1 of {o[4]}) re-swept")
                   for o in olds]):
            j_old = a8 // w_old + 3                  # odd: floors mid-period
            claim = j_old * w_old
            what = f"{plan}: {what}"
            checkpoint.save(path, stored(plan, wh, w_old, seg, nl, j_old, u))
            pol.refuse_mismatch()
            c = Campaign(_args_for(fam), ckpt=path, cursor=pol)
            new_w = int(c.eng.W)
            if (not isinstance(c.eng, gpu.SemiprimeEngine)
                    or c.key != config_key(fam)
                    or c.state()["key"] != config_key(fam)
                    or c.cover_x != claim or c.x_start() != claim
                    or c.k_min() != claim or c.j != claim // new_w
                    or c.u != 0 or c.pending or c.start_x != a8
                    or {str(r): v for r, v in c.census.items()} != census):
                return False, (f"ADOPT FAIL: {what} came up on "
                               f"{type(c.eng).__name__} at ({c.j}, {c.u}) key "
                               f"{c.key}, cover {c.cover_x}, clip {c.k_min()}")
            c.save()
            st, kind = pol.load()
            if (kind != "own" or int(st["j"]) != c.j
                    or int(st["cover_x"]) != claim):
                return False, (f"ADOPT FAIL: after {what} the checkpoint is "
                               f"not the new plan's")
            rows.append(f"{what} from {claim:.4g} at once, floored into "
                        f"period {c.j} of {new_w:.4g}")
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
    return True, (f"adoption ok ({fam} n = {n0}, the p1 and p2 cursors read "
                  f"by {plan_version(fam)}): "
                  + "; ".join(rows) + " -- the census, the finds and the "
                  "campaign's start carried untouched, and the next save "
                  "under the new key")


def _other_families_cursor_drill(fam):
    import tempfile
    tmp = tempfile.mkdtemp(prefix="power-cursor-")
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


_WANT_UNIT = {"A229626": 1, "A229627": 6, "A229630": 1, "A229902": 10}


def _families_stay_apart():
    """No two campaigns may read each other's cursor; the plan is admissible
    at every opening and the filters above it, in the forced class, with an
    expected sweep near the unavoidable one; and the benchmark shape at
    each opening names the campaign's own plan (rule 5g)."""
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
            if unit != _WANT_UNIT[f]:
                return False, (f"FAMILY FAIL: {f} n = {n}: the forced unit is "
                               f"{unit}, not {_WANT_UNIT[f]}")
            W = unit
            for q in gpu._wheel_primes(p1, p2, p3):
                W *= q
            _wide, pv = gpu._record_for(W // unit, q2, pb)
            floor_k = model.plan_floor(f, n)
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
        (label, f, n, p1, p2, p3, q2, _j0, _b, _r, _c, _x, unit, _nu, pb) = row[:15]
        if n != open_n(f) or label.startswith("SCORE1") or label.startswith("SCORE2"):
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
                  "plan is admissible at every opening and the filters "
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
    tmp = tempfile.mkdtemp(prefix="power-drill-")
    path = str(pathlib.Path(tmp) / "c.json")
    pol = _POLICIES[fam].at(path)
    n0 = open_n(fam)
    a = _args_for(fam)
    try:
        c = Campaign(a, ckpt=path, cursor=pol)
        if c.frontier() != n0 - 1 or c.filter_n() != n0:
            return False, f"WIRING FAIL: frontier {c.frontier()}, filter {c.filter_n()}"
        floor = c.x_start()
        want_floor = x_floor(fam, n0, ref.KNOWN[fam][n0 - 1])
        if floor != want_floor or floor != ref.KNOWN[fam][n0 - 1] or \
                (c.j, c.u) != (c.floor_period(), 0):
            return False, (f"WIRING FAIL: a fresh campaign starts at {floor} "
                           f"(j, u) = ({c.j}, {c.u}); expected the frontier "
                           f"term {want_floor}, inclusive")
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
        if c.handle(floor + 1, CENSUS_FLOOR + 1) is not False or \
                c.census.get(CENSUS_FLOOR + 1) != 1:
            return False, "WIRING FAIL: a census run was not counted"
        if c.handle(floor + 3, CENSUS_FLOOR - 1) is not False or \
                CENSUS_FLOOR - 1 in c.census:
            return False, "WIRING FAIL: a run under the floor was counted"
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
        inflight.append(((jf, 52), [([5, 6, 7, 8], _Done([3, fr - 1, fr, fr + 3]))]))
        inflight.append(((jf, 104), [([9], _Done([0]))]))
        c._drain(inflight, block=True)
        if c.pending != [(7, fr), (8, fr + 3)] or (c.j, c.u) != (jf, 104) \
                or c.census.get(fr - 1, 0) != cen0 + 1 or 3 in c.census:
            return False, (f"WIRING FAIL: the drain left {c.pending}, "
                           f"({c.j}, {c.u}), census {c.census} (a census run "
                           f"is COUNTED at the drain, a NEAR or a find held)")
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
                  f"AT the frontier term ({TERM(fam)} = {floor:,}, inclusive) "
                  f"with the PLANNED engine at n = {n0}, unit {unit}, wheel "
                  f"({p1},{p2},{p3}), depth {q2} and the Fermat stage on "
                  f"{CENSUS_FLOOR} forms; its status line and rung ladder aim "
                  f"at a({n0}), 75 ladder reads at a standing frontier cost "
                  f"0 model rebuilds while a find costs exactly 1, the pool "
                  f"is sized from a live measurement ({ms['per_s']:,.0f} "
                  f"values/s x {1e6 * ms['cost']:.0f} us), back-pressure "
                  f"times the wait, the drain keeps the work cursor behind "
                  f"the classified launches, and the checkpoint round trips "
                  f"through both the normal save and the interrupt snapshot")


def _rediscovery_run_drill(fam):
    """THE REAL LOOP, END TO END, ON PUBLISHED GROUND: `Campaign.run`
    itself, on scratch files, opened at DRILL_N and bounded before
    DRILL_N + 2: it finds a(n0) and a(n0 + 1), both published, carries
    the line between them, and stops."""
    import json as _json
    import tempfile
    tmp = tempfile.mkdtemp(prefix="power-rerun-")
    path = str(pathlib.Path(tmp) / "c.json")
    evid = str(pathlib.Path(tmp) / "evidence")
    n0 = DRILL_N[fam]
    want = {str(n): ref.KNOWN[fam][n] for n in (n0, n0 + 1)}
    if n0 + 2 > open_n(fam):
        return False, f"RERUN FAIL: {fam}'s drill would reach the open index"
    args = _args_for(fam, start_n=n0, stop_n=n0 + 2,
                     to=want[str(n0 + 1)] + 10 ** 7, heartbeat=3600.0)
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
        if ev["oeis_terms"] != {str(n): x} or ev["settles"] != [n] or ev["filter_n"] != n:
            return False, f"RERUN FAIL: a({n})'s evidence files it under {ev['oeis_terms']}"
        vals = ref.values(fam, x, n)
        if ev["unproved"] or len(ev["values"]) != ref.nforms(fam, n) \
                or [int(v) for v in ev["values"].values()] != vals \
                or ev["least_claim"]["swept_from"] > x:
            return False, f"RERUN FAIL: a({n})'s evidence is not self-contained"
        prod = 1
        for p, e in ev[f"{TERM(fam)}_factored"].items():
            prod *= int(p) ** int(e)
        if prod != x:
            return False, f"RERUN FAIL: a({n})'s factorization of the term is wrong"
        if fam == "A229630" and len(ev[f"{TERM(fam)}_semiprime"]) != 2:
            return False, "RERUN FAIL: the semiprime witness is not two primes"
    ok, msg = evidence.gate_names(evid, TERM(fam))
    if not ok:
        return False, "RERUN FAIL: " + msg
    return True, (f"rediscovery run ok: Campaign.run, opened at index {n0} of "
                  f"{fam} on scratch files, found a({n0}) = {want[str(n0)]:,}, "
                  f"carried the line, and found a({n0 + 1}) = "
                  f"{want[str(n0 + 1)]:,}, then stopped before the filter of "
                  f"a({n0 + 2}); each evidence file is named and keyed by the "
                  f"OEIS index, carries the term's factorization and passes "
                  f"the naming gate ({c.survivors:,} values classified, "
                  f"census {dict(sorted(c.census.items()))})")


def _zone_drill():
    """The exception zone can hold terms, and the host finds them: A229627's
    a(1) = a(2) = 2 and a(3) = 3 are primes inside [2, 4096], which a sieve
    with the form q would have 'killed' by themselves; the host's walk of
    the zone at n = 3 finds 3 first (run 3) and agrees with the oracle's."""
    fam, n0, q2 = "A229627", 3, 4096
    hits = cpu.prefix_hits(fam, n0, q2, floor=n0)
    if not hits or hits[0] != (3, 3):
        return False, f"ZONE FAIL: the zone at n = 3 reads {hits[:3]}"
    oh = ref.prefix_hits(fam, n0, ref.floor_x(fam, 1), cpu.k_floor(q2, n0, fam), floor=n0)
    if [(x, r) for x, r in oh if ref.in_domain(fam, x)] != hits:
        return False, "ZONE FAIL: the oracle's zone walk differs from the engine's"
    two = cpu.prefix_hits(fam, 1, q2, floor=1)
    if not two or two[0] != (2, 2):
        return False, f"ZONE FAIL: 2 is not first in the zone at n = 1: {two[:2]}"
    return True, (f"zone ok: A229627's a(3) = 3 and a(1) = a(2) = 2 lie in "
                  f"the exception zone [2, {q2}] and the host's walk finds "
                  f"them first (runs 3 and 2), agreeing with the oracle's walk")


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


def selftest(fam="A229626"):
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
    for d in (_adoption_drill, _ceiling_drill, _zone_drill, _canary_hunt,
              _protocol_drill,
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
    front = max(ref.KNOWN[fam])
    for n in st.get("found", {}):
        front = max(front, int(n))
    log("STATUS", "  ".join([
        f"{fam}",
        f"swept to {TERM(fam)} = {int(st['k']):,}",
        f"work cursor period {int(st['j'])} u = {int(st.get('u', 0))}",
        f"filter n = {front + 1}",
        census_str(cen, CENSUS_FLOOR, front),
        f"finds {st.get('discoveries', 0)}",
        f"near {st.get('near', 0)}",
        f"survivors {int(st.get('survivors', 0)):,}",
        f"elapsed {float(st.get('elapsed', 0)) / 3600:.2f} h",
        f"saved {st.get('saved', '?')}"]))
    for n, k in sorted(st.get("found", {}).items(), key=lambda x: int(x[0])):
        log("STATUS", f"  found: a({n}) = {TERM(fam)} = {int(k):,}")
    if kind == "adopted":
        log("STATUS", f"  this cursor is {st.get('key')}, a superseded plan: "
                      f"the next start runs {config_key(fam)} at once from "
                      f"the start of its segment (an open one is re-swept, "
                      f"its census counted twice)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--family", default="A229626",
                    help="which sequence to hunt: " +
                         ", ".join(ref.FAMILIES) + " (default A229626)")
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
