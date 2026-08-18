"""launch.py -- the A247965 campaign.

    a(n) = least k such that m*k^2 + 1 is prime for all m = 1..n

One engine, one cursor, no flags: every candidate is carried as the pair
(W, j) with k = W*j, which is as valid at 1e4 as at 1e22, so a single
ascending sweep runs from the oracle floor to the enforced ceiling with
no seam at 2^64 -- even though k crosses it around a(12) and the values
m*k^2+1 cross it before a(8).

Discovery protocol (CONVENTIONS.md, with one addition this problem pays
for itself):

  1. the engine's own strong-probable-prime chain (huntlib MR bases);
  2. sympy's independent BPSW chain;
  3. a from-scratch re-derivation by different machinery -- the numpy CPU
     engine on a DIFFERENT wheel, so k sits in a different progression;
  4. a PRIMALITY CERTIFICATE for every one of the n values.

Leg 4 is not optional decoration here.  The values m*k^2+1 pass huntlib's
deterministic Miller-Rabin bound (3.317e24) before a(9), so legs 1 and 2
are probable-prime evidence, not proof.  But N - 1 = m*k^2 is OUR OWN
number: factor m and k and the factorization of N-1 is complete, which is
exactly the input Brillhart-Lehmer-Selfridge Theorem 1 needs.  Every
prime factor of N-1 is far below the MR bound, so each is certified
deterministically, and a per-factor witness set proves N prime outright.

The other half of the least-claim never needed certificates: a candidate
is rejected because a small prime divides one of its values, or because a
strong test fails.  Both are proofs of compositeness.  So "this is the
LEAST k" rests on rigorous ground throughout, and "these n values are
prime" rests on certificates.

Discovery means FIRST OCCURRENCE, once (CONVENTIONS.md).  The frontier --
the largest run length settled so far -- starts at the literature (a(9))
plus CAMPAIGN_FOUND and is PROMOTED AT RUNTIME the moment a longer run is
verified: that k is a(r) for every unsettled r up to its run, each is
logged as [DISCOVERY] exactly once, evidenced, and stored in the
checkpoint.  Everything else is CENSUS, and the census is COUNTED, not
narrated: a k whose run is exactly the frontier is one value short of the
next open term and gets one [NEAR] line (verified 3-way, no evidence); a k
whose run is below the frontier -- a(run+1) already settled -- is counted
in the checkpoint and appears only in the census counts of every 30-second
[STATUS] line, never as a line of its own and never as a file.  The
evidence directory holds first occurrences only.  A campaign that finds
a(10) in its first minutes and keeps running therefore reports one
discovery, logs run-10 values one line each while a(11) is open, and
counts run-7/8/9 values silently.

ASCII only; graceful Ctrl+C (checkpoint, no stacktrace).
"""

import argparse
import json
import math
import os
import pathlib as _pathlib
import sys as _sys
import time
from math import gcd

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from sympy import factorint, isprime, primerange              # noqa: E402

from huntlib import checkpoint as _ckpt                       # noqa: E402
from huntlib.hlog import log, census_str, Heartbeat           # noqa: E402
from huntlib.primes import (MR_VALID_BELOW, factor_witness,   # noqa: E402
                            mr_is_prime)
from ladder_reference import (K_FLOOR, KNOWN, PUBLISHED_BOUNDS,  # noqa: E402
                              run_length as oracle_run, wheel_modulus)
from ladder_search import CpuEngine, J_CEIL, Q2_DEFAULT       # noqa: E402

CKPT = "campaign_checkpoint.json"
DISC = os.path.join("evidence", "ladder_discoveries.json")   # first occurrences only

# The key pins what would change the meaning of the cursor and never
# changes inside a campaign; the filter n and the wheel W are stored IN the
# checkpoint instead, because the campaign moves them itself (below).
CONFIG_KEY = "dickson-ladders/v2/q2={q2}/jceil=4e18"

# Terms this campaign has settled.  A term joins the table the moment it
# is verified, which demotes its run length from "discovery" to "census":
# the SECOND k with run >= 10 is a census repeat, not a new a(10).  (The
# runtime frontier in the checkpoint promotes itself the same way; this
# table seeds a FRESH checkpoint.)
CAMPAIGN_FOUND = {}
FRONTIER_N = max(max(KNOWN), *([max(CAMPAIGN_FOUND)] if CAMPAIGN_FOUND else [0]))

# A campaign runs INDEFINITELY (CONVENTIONS.md): there is no depth at which
# it stops on its own except the enforced ceiling of its wheel, which is
# the last rung.  --to caps a run deliberately; --stop-on-discovery is the
# other deliberate stop.  Progress is read off RUNGS: the model's quartiles
# for every open term (model_results.json, stated before the run), logged
# as [RUNG] when passed, with the next rung and its ETA in every [STATUS].
MODEL_FILE = "model_results.json"
# The sieve filter FOLLOWS THE FRONTIER: filter = max(--n, frontier + 1 -
# FILTER_LAG).  With the default lag of 1 the filter equals the frontier,
# so once a(10) lands the sieve runs at n = 10 -- hunting a(11) while still
# seeing run-10 values (one short of a(11): logged) and counting shorter
# runs -- and steps to 11 when a(11) lands, and so on; lag 0 is the fastest
# possible hunt (filter = frontier + 1) and sees nothing below the next
# open term.  A step that widens the wheel re-denominates the cursor with
# FLOOR (an overlap of at most one new period, never a gap).
FILTER_LAG = 1
SEG_J = 1 << 42                # j per checkpoint segment: ~1 s of device
#                                time at the v2 rate on any wheel (in k it
#                                is 1e16 at n = 10, 1.3e17 at n = 13; v1 used
#                                a fixed 2e13 k).  --seg-span (in k) overrides.
NEAR_FROM = 7                  # the census floor: runs at or above this are
#                                counted per length (checkpoint `near_counts`,
#                                shown in every [STATUS]); only a run equal
#                                to the frontier is logged individually
CHUNK = 1024                   # survivors per classification task
# Host classification runs in a process pool, one segment behind the GPU:
# the pool classifies segment i-1 while the device sieves segment i.  The
# results are consumed in ASCENDING order in the parent and the cursor only
# advances past a fully classified segment, so the least-claim ordering the
# checkpoint depends on is untouched.  --workers 1 is the old serial path.
WORKERS_DEFAULT = max(1, (os.cpu_count() or 2) - 4)


class CorruptEngineError(RuntimeError):
    pass


# ------------------------ certificates (BLS75 Thm 1) ------------------------

def factor_n_minus_1(m, k):
    """Complete factorization of N-1 = m*k^2, as {prime: exponent}.

    Complete because both m (tiny) and k (ours, and no larger than the
    ceiling) are factorable outright -- the whole reason this project can
    certify values of forty digits.
    """
    fac = {}
    for p, e in factorint(m).items():
        fac[int(p)] = fac.get(int(p), 0) + int(e)
    for p, e in factorint(k).items():
        fac[int(p)] = fac.get(int(p), 0) + 2 * int(e)
    return fac


CERT_BASE_CAP = 10_000         # witness bases: the primes below this, ascending


def certificate(N, fac, base_cap=CERT_BASE_CAP):
    """Witnesses {p: a_p} proving N prime, or None.

    Brillhart-Lehmer-Selfridge Theorem 1: with N-1 fully factored, N is
    prime iff for every prime p | N-1 there is a_p with

        a_p^(N-1) == 1 (mod N)   and   gcd(a_p^((N-1)/p) - 1, N) == 1.

    Different p may use different witnesses -- which is what makes this
    practical: a single universal base fails whenever it happens to be a
    p-th power residue, and with six prime factors that is most of the
    time.

    The bases are the primes in ascending order, as many as it takes.  For
    a prime N a base fails the p-condition exactly when it is a p-th power
    residue -- one base in p at random -- and p = 2 is the hard case here
    for a STRUCTURAL reason: k is a multiple of the wheel, so for every
    prime q | k, N = m*k^2 + 1 == 1 (mod q) and quadratic reciprocity (with
    (N-1)/2 = m*k^2/2 even) gives (q/N) = (N/q) = 1; 2 itself is a residue
    whenever N == 1 (mod 8), i.e. for every even m (and every m once
    4 | k).  So the wheel primes never witness p = 2, and a fixed list of
    the first eleven primes left only five or six coin flips per value --
    it ran out on a genuine run-10 census value at m = 2 (every prime
    below 41 a residue) and aborted the campaign with a false ALARM.
    """
    out = {}
    for p in fac:
        for a in primerange(2, base_cap):
            if pow(a, N - 1, N) != 1:
                return None            # Fermat fails: N is composite, no proof exists
            if gcd(pow(a, (N - 1) // p, N) - 1, N) == 1:
                out[p] = a
                break
        else:
            return None
    return out


def verify_certificate(N, fac, witnesses):
    """Re-check a certificate from scratch: this is what the gate drills."""
    prod = 1
    for p, e in fac.items():
        if p >= MR_VALID_BELOW or not mr_is_prime(p):
            return False, f"claimed factor {p} is not a certified prime"
        prod *= p ** e
    if prod != N - 1:
        return False, "factorization does not multiply to N-1"
    for p in fac:
        a = witnesses.get(p) or witnesses.get(str(p))
        if a is None:
            return False, f"no witness for {p}"
        if pow(a, N - 1, N) != 1:
            return False, f"witness {a} fails Fermat at p={p}"
        if gcd(pow(a, (N - 1) // p, N) - 1, N) != 1:
            return False, f"witness {a} fails the gcd condition at p={p}"
    return True, "ok"


# ------------------------- verification (four-way) --------------------------

def sprp_run(k, cap):
    r = 0
    while r < cap and mr_is_prime((r + 1) * k * k + 1):
        r += 1
    return r


def _classify_chunk(task):
    """Pool worker: run lengths of a chunk of survivors, in the given order.

    Module-level and self-contained so it survives Windows spawn; touches
    no GPU, so workers never contend with the parent's device work.
    """
    W, cap, js = task
    return [sprp_run(int(j) * W, cap) for j in js]


def _submit_segment(pool, surv, W, cap):
    """Chunk a segment's survivors and hand them to the pool (or classify
    inline when there is no pool).  Returns a callable that yields the run
    lengths in survivor order."""
    js = surv.tolist()
    if pool is None:
        return lambda: _classify_chunk((W, cap, js))
    futs = [pool.submit(_classify_chunk, (W, cap, js[i:i + CHUNK]))
            for i in range(0, len(js), CHUNK)]

    def collect():
        out = []
        for f in futs:                       # in order: ascending j
            out.extend(f.result())           # exceptions propagate
        return out
    return collect


def full_verify(k, claimed_run, n_filter, certify=True, witness=True):
    """Independent confirmation that run(k) == claimed_run exactly.

    Legs 1-3 always (own SPRP chain, sympy, alternate-alignment re-sieve).
    `certify` adds the BLS75 certificates and `witness` the factor of the
    run breaker -- both are for the EVIDENCE of a first occurrence; a
    [NEAR] value records nothing, so it runs with both off (the witness
    once cost 105 s on a semiprime breaker inside a live segment)."""
    r_own = sprp_run(k, cap=claimed_run + 8)
    r_sym = oracle_run(k, cap=claimed_run + 8)
    if not (r_own == r_sym == claimed_run):
        return None, (f"run disagreement own={r_own} sympy={r_sym} "
                      f"claimed={claimed_run}")
    # Alternate-alignment re-sieve: a coarser wheel puts k in a different
    # progression and uses numpy `%` instead of the GPU's Barrett path.
    alt_n = max(3, min(n_filter, claimed_run) - 1)
    alt = CpuEngine(alt_n)
    lo = max(K_FLOOR, k - 4 * alt.W)
    seen = set()
    for chunk in alt.survivors_pre_mr(lo, k + 4 * alt.W):
        seen.update(int(j) * alt.W for j in chunk.tolist())
    if k not in seen:
        return None, f"alternate-alignment re-sieve (wheel {alt.W}) lost k"
    certs = {}
    if certify:
        kf = factorint(k)
        for m in range(1, claimed_run + 1):
            N = m * k * k + 1
            fac = factor_n_minus_1(m, k)
            w = certificate(N, fac)
            if w is None:
                return None, f"no primality certificate for m={m}"
            ok, why = verify_certificate(N, fac, w)
            if not ok:
                return None, f"certificate for m={m} failed re-check: {why}"
            certs[str(m)] = {str(p): int(a) for p, a in w.items()}
    breaker_m = claimed_run + 1
    breaker = breaker_m * k * k + 1
    fw = 0
    if witness:
        fw = factor_witness(breaker)
        if fw in (1, breaker) or breaker % fw:
            return None, "no composite witness for the run breaker"
    ev = {"k": int(k), "run": int(claimed_run),
          "values_prime_m": list(range(1, claimed_run + 1)),
          "k_factorization": {str(p): int(e) for p, e in factorint(k).items()},
          "breaker_m": int(breaker_m), "breaker_factor": int(fw),
          "certificates_bls75": certs}
    return ev, "ok"


# ------------------------------ checkpoint ---------------------------------

def ckpt_key(q2=Q2_DEFAULT):
    return CONFIG_KEY.format(q2=q2)


def load_ckpt(q2=Q2_DEFAULT):
    return _ckpt.load(CKPT, ckpt_key(q2), warn=lambda m: log("WARN", m))


def save_ckpt(c):
    _ckpt.save(CKPT, c)


def fresh_ckpt(n, eng):
    return {"key": ckpt_key(eng.q2), "n": int(n), "W": eng.W,
            "next_j": max(1, -(-K_FLOOR // eng.W)),
            "canaries_done": False, "survivors": 0,
            "near_counts": {}, "best_run": 0, "best_k": 0, "hits": 0,
            "found": {}, "odds_marks": [], "rungs_passed": [],
            "wall_s": 0.0, "started": time.time()}


def filter_for(c, n_min, lag=FILTER_LAG):
    """The sieve filter the campaign should be running: at least --n, and
    following the frontier one step behind (lag 1) or on it (lag 0)."""
    return max(int(n_min), frontier_of(c) + 1 - int(lag))


def redenominate(next_j, W_old, W_new):
    """The cursor after a wheel change: FLOOR, so the new sweep starts at or
    below the old position -- an overlap of under one new period, never a
    gap (no candidate of the new wheel at or above the old position is
    skipped; below one period the first candidate IS the next one).
    Exhaustiveness is the whole claim; a re-swept period is cheap."""
    return max(1, (int(next_j) * int(W_old)) // int(W_new))


def load_rungs(path=MODEL_FILE):
    """[(label, depth_k)] ascending: the model's Q1/median/Q3/P90 for every
    open term, from the predictions stated before the run.  The enforced
    ceiling of the running wheel is appended at run time as the last rung."""
    rungs = []
    try:
        with open(path) as fh:
            preds = json.load(fh)["predictions"]
    except Exception:
        return rungs
    for n_s, v in preds.items():
        for q in ("Q1", "median", "Q3", "P90"):
            if q in v:
                rungs.append((f"a({int(n_s)}) {q}", float(v[q])))
    rungs.sort(key=lambda t: t[1])
    return rungs


def frontier_of(c):
    """The campaign frontier: the largest run length settled so far, from
    the literature, from CAMPAIGN_FOUND, and from this campaign's own
    verified first occurrences (persisted in the checkpoint as `found`).
    Everything above it is undiscovered; everything at or below it is
    census."""
    found = c.get("found", {}) if c else {}
    return max([FRONTIER_N] + [int(r) for r in found])


def event_kind(c, r):
    """DISCOVERY / NEAR / CENSUS / None for a survivor with run r -- the one
    place the discovery-once and census rules live (CONVENTIONS.md).

    DISCOVERY: beyond the frontier -- a first occurrence; the full protocol,
    evidence written, logged once.  NEAR: exactly AT the frontier -- one
    value short of the next open term; verified 3-way and logged as one
    [NEAR] line with its census ordinal, but not evidenced (evidence holds
    first occurrences only).  CENSUS: below the frontier but at or above
    NEAR_FROM -- a(r+1) is already settled, so the value is noise as an
    individual: COUNTED in the checkpoint and shown in every [STATUS] /
    [MILESTONE] line, no log line, no record.  None: below the floor.
    A run-9 value is NEAR while a(10) is open and CENSUS the moment a(10)
    lands -- the frontier moves and the classification follows it."""
    fr = frontier_of(c)
    if r > fr:
        return "DISCOVERY"
    if r == fr:
        return "NEAR"
    if r >= NEAR_FROM:
        return "CENSUS"
    return None


def settle(c, r, k):
    """Promote the frontier: k is a(r') for every unsettled r' <= r (run >= r
    implies run >= r', and the sweep is ascending).  Returns the r' list."""
    fr = frontier_of(c)
    found = c.setdefault("found", {})
    newly = list(range(fr + 1, r + 1))
    for rr in newly:
        found[str(rr)] = int(k)
    return newly


def settled_at(c, r):
    """Where a(r) was settled: literature, CAMPAIGN_FOUND, or this campaign."""
    if r in KNOWN:
        return KNOWN[r]
    if r in CAMPAIGN_FOUND:
        return CAMPAIGN_FOUND[r]
    return c.get("found", {}).get(str(r))


def check_cursor(c, eng):
    if c.get("W") != eng.W or wheel_modulus(int(c.get("n", -1))) != eng.W:
        raise CorruptEngineError(
            f"[ALARM] cursor was written for wheel {c.get('W')} (filter "
            f"{c.get('n')}) but the engine runs {eng.W}; next_j counts "
            f"multiples of the wheel, so reading it against another one "
            f"moves the frontier silently")


def refuse_unreadable_cursor(eng, fresh):
    """A key mismatch must HALT, not silently restart at zero.

    huntlib ignores a checkpoint whose key does not match, which is the
    right default for a stale file and the wrong one for a live frontier:
    the campaign would begin again at k = K_FLOOR and quietly abandon
    everything already swept.  (This trap cost the sibling project a
    real incident; it is closed here before the first production run.)
    """
    if fresh or not os.path.exists(CKPT):
        return
    with open(CKPT) as fh:
        stored = json.load(fh).get("key")
    raise CorruptEngineError(
        f"[ALARM] checkpoint key {stored!r} does not match the running "
        f"configuration {ckpt_key(eng.q2)!r}. Refusing to start a fresh "
        f"sweep over a range that may already be covered; pass --fresh to "
        f"discard it deliberately.")


# ------------------------------- discovery ---------------------------------

def record_discovery(ev, label):
    """Write the evidence JSON for a FIRST OCCURRENCE and upsert the ledger
    entry for k.  Called for discoveries only: the evidence directory holds
    first occurrences, never census values (CONVENTIONS.md).

    Keyed by k, so redoing a segment (the one in flight at an interrupt or
    a crash is redone on resume) rewrites the same records instead of
    appending duplicates."""
    os.makedirs("evidence", exist_ok=True)
    path = os.path.join("evidence", f"ladder_hit_run{ev['run']}_k{ev['k']}.json")
    with open(path, "w") as f:
        json.dump(ev, f, indent=1)
    allrec = []
    if os.path.exists(DISC):
        with open(DISC) as f:
            allrec = json.load(f)
    rec = dict(ev)
    rec["label"] = label
    rec["t"] = time.time()
    allrec = [d for d in allrec if int(d.get("k", -1)) != int(ev["k"])]
    allrec.append(rec)
    allrec.sort(key=lambda d: d["k"])
    with open(DISC, "w") as f:
        json.dump(allrec, f, indent=1)
    return path


# -------------------------------- preludes ---------------------------------

def low_pass():
    """Exhaustive oracle sweep of [1, K_FLOOR): the engines refuse to run
    there (the wheel argument has an exception zone), so the oracle owns
    it, and a(1)-a(4) come back as a positive control of the whole
    protocol on genuine knowns."""
    firsts = {}
    for k in range(1, K_FLOOR):
        r = oracle_run(k, cap=12)
        if r >= 1:
            for n in range(1, r + 1):
                firsts.setdefault(n, k)
    for n, k in sorted(firsts.items()):
        if n in KNOWN and KNOWN[n] != k:
            raise CorruptEngineError(
                f"low pass says a({n}) = {k}, literature says {KNOWN[n]}")
    return firsts


def canary_prelude(make_engine):
    """Rediscover a(7), a(8) and a(9) end-to-end, as FIRST occurrences.

    Least-claim drills, not mere hits: the engine must produce the known
    value as the smallest k with that run, sweeping from the floor.  A
    stream that cannot find what is known does not get to report what is
    not."""
    for cn in (7, 8, 9):
        t0 = time.time()
        eng = make_engine(cn)
        hits = eng.hunt(K_FLOOR, KNOWN[cn])
        firsts = sorted(k for k, r in hits if r >= cn)
        if not firsts or firsts[0] != KNOWN[cn]:
            raise CorruptEngineError(
                f"CANARY ALARM: a({cn}) rediscovery failed (got "
                f"{firsts[:1]}, expected {KNOWN[cn]})")
        log("CANARY-GOLD", f"a({cn}) = {KNOWN[cn]} rediscovered end-to-end "
                           f"as the first occurrence ({time.time()-t0:.0f}s)")


# -------------------------------- the hunt ---------------------------------

def production(args):
    if args.engine == "cpu":
        from ladder_search import CpuEngine as Eng
    else:
        from ladder_gpu import GpuEngine as Eng

    def make_engine(m):
        return Eng(m, q2=Q2_DEFAULT)

    # ---- cursor: the checkpoint says which filter the campaign is on
    c = None if args.fresh else load_ckpt()
    if c is None:
        eng = make_engine(args.n)
        refuse_unreadable_cursor(eng, args.fresh)
        c = fresh_ckpt(args.n, eng)
        n = args.n
    else:
        n = int(c.get("n", args.n))
        eng = make_engine(n)
    check_cursor(c, eng)
    W = eng.W

    if not c["canaries_done"]:
        log("STAGE", "prelude: oracle low pass + a(7)/a(8)/a(9) rediscovery")
        firsts = low_pass()
        log("CANARY-GOLD", "oracle low pass [1, %d): first occurrences %s -- "
            "matches the literature" % (K_FLOOR, {k: v for k, v in
                                                  sorted(firsts.items())
                                                  if k <= 4}))
        canary_prelude(make_engine)
        c["canaries_done"] = True
        save_ckpt(c)

    logC = None
    try:
        from ladder_model import log_singular_series
        from ladder_model import expected_count as _expected_count
        _logc_cache = {}

        def expected_count(target, pos, _unused):
            if target not in _logc_cache:
                _logc_cache[target] = log_singular_series(target)[0]
            return _expected_count(target, pos, _logc_cache[target])
        logC = True
    except Exception:
        expected_count = None

    # ---- depth: indefinite by default -- the enforced ceiling of the
    # running wheel is the last rung; --to caps a run deliberately
    user_cap = None if args.to is None else int(args.to)
    rungs = load_rungs()

    def ceiling():
        return J_CEIL * W

    def cap_now():
        return ceiling() if user_cap is None else min(user_cap, ceiling())

    def j_cap_now():
        return min(cap_now() // W + 1, J_CEIL)

    def all_rungs():
        return rungs + [(f"enforced ceiling of the {W} wheel", float(ceiling()))]

    def next_rung(pos):
        passed = c.get("rungs_passed", [])
        for i, (label, depth) in enumerate(all_rungs()):
            if label not in passed and depth > pos:
                return i, label, depth
        return None
    # rungs already behind the cursor (a resume from before rungs existed)
    # are recorded silently
    for label, depth in all_rungs():
        if depth <= c["next_j"] * W and label not in c.setdefault("rungs_passed", []):
            c["rungs_passed"].append(label)

    seg = SEG_J if args.seg_span is None else max(1, int(args.seg_span) // W)
    # the wall-clock [STATUS] heartbeat (huntlib.hlog.Heartbeat): its own
    # thread, every --heartbeat seconds, whatever the main loop is doing;
    # the checkpoint is saved from the main loop at segment boundaries
    hb = Heartbeat(args.heartbeat)
    t_save = [time.time()]
    workers = max(1, int(args.workers))
    pool = None
    if workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        pool = ProcessPoolExecutor(max_workers=workers)
    log("STAGE", f"production: n={n} filter, wheel {W}, k from "
                 f"{c['next_j']*W:.4e} to {cap_now():.3e} "
                 f"({'--to' if user_cap is not None else 'the enforced ceiling'};"
                 f" {len(all_rungs())} rungs, filter lag {args.filter_lag}) "
                 f"({args.engine}, {workers} classification worker"
                 f"{'s' if workers > 1 else ''})")

    def sieve(j0, j1):
        surv = eng.survivors_j(j0, j1)
        if not hasattr(surv, "tolist"):                  # CPU engine: chunks
            import numpy as np
            surv = (np.concatenate([x for x in surv])
                    if surv else np.empty(0, dtype="uint64"))
        return surv

    def switch_filter(new_n):
        """Rebuild the engine at a new filter; re-denominate the cursor if
        the wheel widened.  Called only with no segment in flight."""
        nonlocal eng, n, W, seg
        old_n, old_W, old_j = n, W, c["next_j"]
        eng = make_engine(new_n)
        n, W = new_n, eng.W
        new_j = old_j if W == old_W else redenominate(old_j, old_W, W)
        c["n"], c["W"], c["next_j"] = n, W, new_j
        if args.seg_span is not None:
            seg = max(1, int(args.seg_span) // W)
        overlap = old_j * old_W - new_j * W
        log("STAGE", f"filter {old_n} -> {n} (frontier a({frontier_of(c)}), "
                     f"lag {args.filter_lag}); wheel {old_W} -> {W}; cursor "
                     f"k {old_j*old_W:.4e} -> {new_j*W:.4e}"
                     + (f" (overlap {overlap:.3e}, floor: never a gap)"
                        if W != old_W else " (same wheel, cursor unchanged)")
                     + f"; ceiling now {ceiling():.3e}")
        save_ckpt(c)

    t_mark = time.time()

    def census_now():
        """The census counts per run length, floor to frontier, in the
        shared STATUS format (`census 7:280 8:71 9:28 10:8`)."""
        return census_str(c.get("near_counts", {}), NEAR_FROM, frontier_of(c))

    def consume(seg_j0, seg_j1, surv, runs):
        """Bookkeeping for one classified segment, survivors ascending.
        Returns True if the campaign should stop (--stop-on-discovery)."""
        nonlocal t_mark
        evidenced = False       # a discovery in this segment
        for j, r in zip(surv.tolist(), runs):
            k = int(j) * W
            c["survivors"] += 1
            fr = frontier_of(c)
            new_best = r > c["best_run"]
            if new_best:
                c["best_run"], c["best_k"] = r, k
            if r >= NEAR_FROM:
                nc = c.setdefault("near_counts", {})
                nc[str(r)] = nc.get(str(r), 0) + 1
            kind = event_kind(c, r)
            if kind == "DISCOVERY":
                # ---- the first k with a run beyond the frontier.  It is
                # a(r') for EVERY unsettled r' <= r, each logged exactly once.
                hb.doing(f"verifying run-{r} k={k} (full protocol + certificates)")
                ev, msg = full_verify(k, r, n)
                if ev is None:
                    raise CorruptEngineError(f"verify failed at k={k}: {msg}")
                label = "A247965(%d) CANDIDATE -- first occurrence" % r
                path = record_discovery(ev, label)
                evidenced = True
                newly = settle(c, r, k)
                c["hits"] = c.get("hits", 0) + 1
                log("DISCOVERY", "=" * 60)
                log("DISCOVERY", f"run == {r} at k = {k}  ({label})")
                for rr in newly:
                    log("DISCOVERY", f"a({rr}) = {k}" +
                        ("" if rr == r else f"  (settled by the same k: run "
                                            f"{r} >= {rr})"))
                log("DISCOVERY", f"breaker m={ev['breaker_m']}: factor "
                                 f"{ev['breaker_factor']}")
                log("DISCOVERY", f"verified 4 ways incl. BLS75 "
                                 f"certificates; evidence {path}")
                log("DISCOVERY", f"frontier is now a({r}); run-{r} values "
                                 f"are now [NEAR] (one short of a({r+1})), "
                                 f"shorter runs are counted in [STATUS] only")
                log("DISCOVERY", "=" * 60)
                if args.stop_on_discovery:
                    save_ckpt(c)
                    log("STAGE", "frontier-extending discovery confirmed "
                                 "-- stopping (--stop-on-discovery)")
                    return True
            elif kind == "NEAR":
                # ---- exactly at the frontier: one value short of the next
                # open term.  Verified 3-way as a running engine health
                # check (own chain, sympy, alternate-alignment re-sieve --
                # no certificates: nothing is being recorded), logged once
                # with its census ordinal, never evidenced.
                hb.doing(f"verifying run-{r} k={k} (3-way)")
                ev, msg = full_verify(k, r, n, certify=False, witness=False)
                if ev is None:
                    raise CorruptEngineError(f"verify failed at k={k}: {msg}")
                cnt = c["near_counts"][str(r)]
                tail = "  -- ONE value short of a(%d)!" % (fr + 1)
                if new_best:
                    tail += "  -- new campaign best"
                if cnt == 1:
                    tail += "  -- first run-%d of the campaign" % r
                log("NEAR", f"run {r} at k = {k}  (run-{r} #{cnt} of the "
                            f"campaign; a({r}) settled at {settled_at(c, r)}; "
                            f"verified 3-way){tail}")
            # CENSUS (below the frontier): counted above, nothing else --
            # the counts are in every [STATUS] and [MILESTONE] line.
        # the cursor advances only past a FULLY classified segment
        c["next_j"] = seg_j1
        now = time.time()
        c["wall_s"] += now - t_mark
        t_mark = now
        hb.mark(seg_j1 * W)                 # the heartbeat's position + rate
        hb.doing("between segments")
        if evidenced or now - t_save[0] >= args.heartbeat:
            # the checkpoint is saved at segment BOUNDARIES only (a
            # mid-segment save would persist counts the redone segment
            # re-counts): every --heartbeat seconds, and at once when the
            # segment wrote evidence -- a promoted frontier must never
            # outlive the process only in memory
            save_ckpt(c)
            t_save[0] = now
        fr = frontier_of(c)
        pos = seg_j1 * W
        dec = 10 ** int(math.log10(max(pos, 10)))
        if seg_j0 * W < dec <= pos:
            log("MILESTONE", f"passed k = {dec:.0e}  survivors "
                             f"{c['survivors']:,}  {census_now()}  "
                             f"best run {c['best_run']}  finds {c.get('hits', 0)}")
        # rungs: the model's quartiles for the open terms, then the ceiling
        passed = c.setdefault("rungs_passed", [])
        for i, (label, depth) in enumerate(all_rungs()):
            if depth <= pos and label not in passed:
                passed.append(label)
                nr = next_rung(pos)
                nxt = ("last rung -- the campaign ends here" if nr is None else
                       f"next: {nr[1]} at k = {nr[2]:.3e}")
                log("RUNG", f"passed rung {i+1}/{len(all_rungs())}: {label} "
                            f"(k = {depth:.3e}) at k = {pos:.4e}  -- {nxt}")
        # model odds crossing a quartile: the hunt is past where the model
        # put a(fr+1) with that probability -- once per threshold per frontier
        if logC is not None and expected_count is not None:
            E = expected_count(fr + 1, pos, logC)
            pnow = 1.0 - math.exp(-E)
            marks = c.setdefault("odds_marks", [])
            for thr in (0.25, 0.50, 0.75, 0.90):
                key = f"a{fr+1}:{thr:.2f}"
                if pnow >= thr and key not in marks:
                    marks.append(key)
                    log("MILESTONE", f"model: P(a({fr+1}) by now) crossed "
                                     f"{thr:.0%} at k = {pos:.3e}"
                                     + ("  -- past the median" if thr == 0.5 else ""))
        return False

    def status_line():
        """The 30-second [STATUS] line (CONVENTIONS.md), composed on the
        heartbeat thread from the main loop's state: position, end-to-end
        rate, survivors, the CENSUS COUNTS per run length from the floor to
        the frontier -- the only place values below the frontier appear --
        finds, live odds, next rung + ETA; and, when no segment has closed
        since the previous line, what the launcher is busy with and for how
        long, so a stall reads as a stall and never as silence."""
        pos = c["next_j"] * W
        rate = hb.rate()
        fr = frontier_of(c)
        odds = ""
        if logC is not None and expected_count is not None:
            E = expected_count(fr + 1, pos, logC)
            odds = f"P(a{fr+1} by now) {1-math.exp(-E):.0%}  "
        nr = next_rung(pos)
        rung = ""
        if nr is not None:
            i, label, depth = nr
            eta = (f"{(depth - pos) / rate / 3600:.1f}h" if rate > 0 else "n/a")
            rung = (f"rung {i}/{len(all_rungs())} passed, next {label} at "
                    f"{depth:.2e} (ETA {eta})  ")
        stall = hb.stalled()
        busy = ("" if stall is None else
                f"  -- no segment closed since the last status: {stall[0]} "
                f"for {stall[1]:.0f}s")
        return (f"k {pos:.4e}  n={n}  {rate:.3e} k/s  "
                f"surv {c['survivors']:,}  {census_now()}  "
                f"best run {c['best_run']}  finds {c.get('hits', 0)}  "
                f"{odds}{rung}{busy}")

    hb.mark(c["next_j"] * W)
    hb.start(status_line)
    pending = None          # (j0, j1, surv, collect): one segment behind
    try:
        next_j = c["next_j"]
        while True:
            want = filter_for(c, args.n, args.filter_lag)
            if want != n and pending is None:
                switch_filter(want)          # no segment in flight: safe
                next_j = c["next_j"]
            j_cap = j_cap_now()
            if next_j >= j_cap and pending is None:
                break
            new = None
            if next_j < j_cap and want == n:   # never sieve at a stale filter
                j0, j1 = next_j, min(next_j + seg, j_cap)
                hb.doing(f"sieving k {j0*W:.4e}..{j1*W:.4e}")
                surv = sieve(j0, j1)                 # device works while the
                collect = _submit_segment(pool, surv, W, frontier_of(c) + 8)
                new = (j0, j1, surv, collect)        # pool chews on `pending`
                next_j = j1
            if pending is not None:
                p_j0, p_j1, p_surv, p_collect = pending
                hb.doing(f"classifying k {p_j0*W:.4e}..{p_j1*W:.4e} "
                         f"({p_surv.size:,} survivors)")
                if consume(p_j0, p_j1, p_surv, p_collect()):
                    return 0
            pending = new
        hb.emit()                       # the final line, at the last position
        if user_cap is not None and user_cap < ceiling():
            log("STAGE", f"--to {user_cap:.3e} reached; survivors "
                         f"{c['survivors']}; best run {c['best_run']} at "
                         f"k = {c['best_k']}")
        else:
            log("STAGE", f"the enforced ceiling {ceiling():.3e} of the {W} "
                         f"wheel is the last rung and it has been reached; "
                         f"survivors {c['survivors']}; best run "
                         f"{c['best_run']} at k = {c['best_k']}")
        return 0
    except KeyboardInterrupt:
        save_ckpt(c)
        log("STAGE", "interrupted; checkpoint saved at k = %.4e (the "
                     "segment in flight is redone on resume)"
                     % (c["next_j"] * W))
        return 0
    finally:
        hb.stop()
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)


# -------------------------------- selftest ---------------------------------

def selftest():
    import ladder_gpu
    import ladder_model
    import ladder_reference
    import ladder_search
    ok = True
    for mod in (ladder_reference, ladder_search, ladder_gpu):
        for g in mod.GATES:
            good, msg = g()
            print(("PASS " if good else "FAIL ") + msg)
            ok = ok and good
    m = ladder_model.model()
    for g in (ladder_model.z1_tail_small, ladder_model.z2_validation,
              ladder_model.z3_monotone, ladder_model.z4_w_matches_oracle):
        good, msg = g(m)
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good

    # --- resume drill: a split stream must equal the unsplit one -----------
    from ladder_gpu import GpuEngine
    eng = GpuEngine(10, q2=1024)
    j_lo, span = 5 * 10**9, 4 * 10**6
    whole = eng.survivors_j(j_lo, j_lo + span)
    part = list(eng.survivors_j(j_lo, j_lo + span // 3)) + \
        list(eng.survivors_j(j_lo + span // 3, j_lo + span))
    if whole.size == 0:
        print("FAIL resume drill: window under-populated (vacuous)")
        ok = False
    elif list(whole) != part:
        print("FAIL resume drill: split stream != whole stream")
        ok = False
    else:
        print(f"PASS resume drill: split stream == whole stream "
              f"({whole.size} survivors)")

    # --- indefinite-run drill: rungs, filter following, re-denomination --
    rungs = load_rungs()
    r_ok = (len(rungs) >= 8 and all(rungs[i][1] <= rungs[i + 1][1]
                                    for i in range(len(rungs) - 1))
            and any(lab.startswith("a(13) median") for lab, _ in rungs))
    c0 = fresh_ckpt(10, GpuEngine(10))
    r_ok = r_ok and filter_for(c0, 10) == 10 and filter_for(c0, 10, lag=0) == 10
    settle(c0, 10, 10**15)                          # a(10) lands: frontier 10
    r_ok = r_ok and filter_for(c0, 10) == 10 and filter_for(c0, 10, lag=0) == 11
    settle(c0, 11, 10**17)                          # frontier 11
    r_ok = r_ok and filter_for(c0, 10) == 11 and filter_for(c0, 10, lag=0) == 12
    # wheel widening 2310 -> 30030 re-denominates by FLOOR: overlap, no gap
    W1, W2 = wheel_modulus(11), wheel_modulus(12)
    for j in (1, 7, 12345, 4 * 10**18 // W2 * 3):
        j2 = redenominate(j, W1, W2)
        # no candidate of the wider wheel at or above the old position is
        # skipped: j2 <= ceil(old_k / W2); and never below the first one
        r_ok = r_ok and 1 <= j2 <= -(-(j * W1) // W2)
    r_ok = r_ok and W1 == 2310 and W2 == 30030 \
        and redenominate(30030, 2310, 30030) == 2310
    if not r_ok:
        print("FAIL indefinite-run drill: rungs / filter following / "
              "re-denomination")
        ok = False
    else:
        print(f"PASS indefinite-run drill: {len(rungs)} model rungs ascending, "
              f"the filter follows the frontier (lag 1: 10 -> 10 -> 11; lag 0: "
              f"10 -> 11 -> 12), and a 2310 -> 30030 wheel change moves the "
              f"cursor by floor (overlap < one period, never a gap)")

    # --- discovery-once / census drill: the frontier promotes and the
    # classification follows it: beyond = DISCOVERY, at = NEAR (one short,
    # logged), below = CENSUS (counted only), under the floor = None ------
    c = fresh_ckpt(10, GpuEngine(10))
    steps = [(8, "CENSUS"), (9, "NEAR"), (10, "DISCOVERY"), (NEAR_FROM, "CENSUS"),
             (NEAR_FROM - 1, None)]
    seq_ok = frontier_of(c) == FRONTIER_N and all(
        event_kind(c, r) == kind for r, kind in steps)
    settle(c, 10, 10**15)                          # a(10) lands
    seq_ok = seq_ok and frontier_of(c) == 10 and event_kind(c, 10) == "NEAR" \
        and event_kind(c, 9) == "CENSUS" and event_kind(c, 11) == "DISCOVERY"
    newly = settle(c, 12, 3 * 10**15)              # a run of 12 settles 11 AND 12
    seq_ok = seq_ok and newly == [11, 12] and frontier_of(c) == 12 \
        and event_kind(c, 12) == "NEAR" and event_kind(c, 10) == "CENSUS" \
        and event_kind(c, 13) == "DISCOVERY" \
        and settled_at(c, 11) == 3 * 10**15 and settled_at(c, 9) == KNOWN[9] \
        and event_kind(c, NEAR_FROM - 1) is None
    # the STATUS census string covers floor..frontier in the shared format
    c["near_counts"] = {"7": 280, "9": 28, "12": 1}
    cs = census_str(c["near_counts"], NEAR_FROM, frontier_of(c))
    seq_ok = seq_ok and cs == "census 7:280 8:0 9:28 10:0 11:0 12:1"
    if not seq_ok:
        print("FAIL discovery-once drill: frontier/near/census classification "
              f"or census string ({cs})")
        ok = False
    else:
        print("PASS discovery-once drill: a(10) is a discovery once; run-10 "
              "values are then NEAR (one short, logged) and run-9 drops to "
              "census (counted only); a run of 12 settles a(11) and a(12) "
              "together and the frontier promotes 9 -> 10 -> 12; census "
              "string floor..frontier in the shared format")

    # --- pool drill: pooled classification == serial, in survivor order ----
    from concurrent.futures import ProcessPoolExecutor
    eng = GpuEngine(10)
    j_lo, span = 10**12, 12 * 10**9
    surv = eng.survivors_j(j_lo, j_lo + span)
    serial = _classify_chunk((eng.W, FRONTIER_N + 8, surv.tolist()))
    with ProcessPoolExecutor(max_workers=4) as pool:
        pooled = _submit_segment(pool, surv, eng.W, FRONTIER_N + 8)()
    if surv.size < 2 * CHUNK:
        print("FAIL pool drill: window too small to span several chunks")
        ok = False
    elif pooled != serial:
        print("FAIL pool drill: pooled run lengths != serial (or misordered)")
        ok = False
    else:
        print(f"PASS pool drill: pooled classification == serial, in order "
              f"({surv.size} survivors over {-(-surv.size // CHUNK)} chunks, "
              f"max run {max(serial)})")

    # --- positive control: a genuine known passes the full protocol --------
    ev, msg = full_verify(KNOWN[7], 7, 7)
    if ev is None:
        print("FAIL positive control: a(7) rejected -- " + msg)
        ok = False
    else:
        ncerts = len(ev["certificates_bls75"])
        print(f"PASS positive control: a(7) verified 4 ways with {ncerts} "
              f"BLS75 certificates (values up to {7*KNOWN[7]**2:.3e})")

    # --- planted drill: a fake run claim must be rejected -------------------
    ev, msg = full_verify(KNOWN[7], 8, 7)
    if ev is not None:
        print("FAIL planted drill: fake run-8 claim accepted")
        ok = False
    else:
        print(f"PASS planted drill: fake run-8 claim rejected ({msg})")

    # --- G11: a forged certificate must be rejected ------------------------
    k = KNOWN[7]
    N = k * k + 1
    fac = factor_n_minus_1(1, k)
    good = certificate(N, fac)
    okc, _ = verify_certificate(N, fac, good)
    forged = dict(good)
    forged[next(iter(forged))] = 1                    # a^(N-1) == 1 trivially
    bad, why = verify_certificate(N, fac, forged)
    liar = dict(fac)
    liar[next(iter(liar))] += 1                       # wrong factorization
    bad2, why2 = verify_certificate(N, liar, good)
    if not okc or bad or bad2:
        print(f"FAIL G11: certificate drill (genuine={okc}, forged={bad}, "
              f"wrong-factorization={bad2})")
        ok = False
    else:
        print(f"PASS G11: certificate verifier accepts the genuine proof and "
              f"rejects a forged witness ({why}) and a wrong factorization "
              f"({why2})")

    # --- G12: the witness search must not run out of bases -----------------
    # A genuine run-10 census value of the campaign: at m = 2 every prime
    # below 41 is a quadratic residue mod N (k is a wheel multiple and m is
    # even -- see certificate()), so a fixed list of the first eleven primes
    # finds no witness for p = 2 -- exactly the false ALARM that once
    # aborted the hunt.  The open-ended search must certify it and the
    # verifier must accept the result.
    k = 37715882280469470
    N = 2 * k * k + 1
    fac = factor_n_minus_1(2, k)
    short = certificate(N, fac, base_cap=32)          # the old eleven primes
    w = certificate(N, fac)
    okw, whyw = ((False, "no certificate") if w is None
                 else verify_certificate(N, fac, w))
    if short is not None or not okw:
        print(f"FAIL G12: base-exhaustion drill (eleven-prime list finds a "
              f"witness: {short is not None}; open-ended search: {whyw})")
        ok = False
    else:
        print(f"PASS G12: genuine run-10 value certified at m=2 with p=2 "
              f"witness {w[2]} after the first eleven primes all fail; "
              f"verifier re-check ok")

    print("SELFTEST ALL GREEN" if ok else "SELFTEST FAILED")
    return 0 if ok else 1


def status():
    if not os.path.exists(CKPT):
        print("no campaign checkpoint yet")
        return 0
    with open(CKPT) as f:
        c = json.load(f)
    W = c.get("W", 1)
    print(f"key       : {c['key']}")
    print(f"filter    : n = {c.get('n')}  wheel {W}")
    print(f"frontier  : k = {c['next_j'] * W:.6e}  (next_j {c['next_j']:,})")
    print(f"rungs     : {len(c.get('rungs_passed', []))} passed; last: "
          f"{(c.get('rungs_passed') or ['-'])[-1]}")
    print(f"survivors : {c['survivors']:,} classified in "
          f"{c['wall_s']/3600:.2f} h")
    print(f"best run  : {c['best_run']} at k = {c['best_k']}")
    cs = census_str(c.get('near_counts', {}), NEAR_FROM, frontier_of(c))
    print(f"census    : {cs[len('census '):]}  (values met per run length, "
          f"floor {NEAR_FROM} to the frontier; counted, not evidenced)")
    print(f"found     : {c.get('found', {})}  (this campaign's first "
          f"occurrences; frontier a({frontier_of(c)}))")
    print(f"finds     : {c.get('hits', 0)}")
    for n, b in sorted(PUBLISHED_BOUNDS.items()):
        print(f"published : a({n}) > {b:,}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="A247965 hunt")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--stop-on-discovery", action="store_true",
                    help="halt after a verified FIRST OCCURRENCE beyond the "
                         "frontier (a(%d) at start; promoted as finds land); "
                         "census repeats never trigger it" % FRONTIER_N)
    ap.add_argument("--n", type=int, default=FRONTIER_N + 1,
                    help="the STARTING filter (sieve for k with run >= n); "
                         "the filter then follows the frontier (--filter-lag)")
    ap.add_argument("--filter-lag", type=int, default=FILTER_LAG,
                    help="filter = max(--n, frontier + 1 - lag): 1 (default) "
                         "keeps seeing the last settled length (one short of "
                         "the next term, logged) while hunting the next; 0 "
                         "is the fastest hunt")
    ap.add_argument("--to", type=float, default=None,
                    help="depth cap in k (default: none -- the campaign runs "
                         "to the enforced ceiling of its wheel, the last rung)")
    ap.add_argument("--engine", choices=["gpu", "cpu"], default="gpu")
    ap.add_argument("--seg-span", type=float, default=None,
                    help="k per checkpoint segment (default: %d j)" % SEG_J)
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (position, rate, the "
                         "census counts per run length, finds, odds, next "
                         "rung); 30 is the repo convention")
    ap.add_argument("--workers", type=int, default=WORKERS_DEFAULT,
                    help="classification processes (1 = serial, in-process)")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.status:
        return status()
    if args.to is not None and args.to > J_CEIL * wheel_modulus(args.n):
        log("ALARM", "requested depth is past the enforced ceiling")
        return 2
    if args.filter_lag < 0:
        log("ALARM", "--filter-lag must be >= 0")
        return 2
    try:
        return production(args)
    except CorruptEngineError as e:
        log("ALARM", str(e))
        return 2


if __name__ == "__main__":
    _sys.exit(main())
