"""launch.py -- the A053647 campaign.

    a(n) = least prime p such that p + j*P(n) is prime for j = 0 .. n-1,
           P(n) = A002110(n), the product of the first n primes

ONE TERM AT A TIME, AND THAT IS THE SHAPE OF EVERYTHING HERE.  The
difference P(n) changes with n, so a candidate says nothing about any other
term: there is no monotone ladder to climb and no single cursor that serves
every n (a(7) = 7937 is larger than a(8) = 7703 -- the sequence is not even
increasing).  The campaign therefore sieves for ONE n, from the floor, until
it finds a(n); then it retires that term's rungs, resets the cursor to the
floor and starts the next open term with a completely different sieve.  The
`[STAGE]` line that says so is not bookkeeping, it is the campaign changing
what it is looking for.

Candidates are carried as the pair (base, offset) with p = base + offset,
base a Python integer and offset a u64, so one engine spans the whole range
with no seam at 2^64 -- even though p passes it around a(21) and the VALUES
p + j*P(n) pass it at a(16).

Discovery protocol (CONVENTIONS.md):

  1. the engine's own strong-probable-prime chain (huntlib MR bases);
  2. sympy's independent BPSW chain, over the values in Python integers;
  3. a from-scratch re-derivation by different machinery -- the GPU
     engine's residue WALK consulted candidate-at-a-time at a DIFFERENT
     sieve depth from the campaign's, plus the oracle's direct divisibility
     on the actual values;
  4. a PRIMALITY PROOF for every one of the n values.

Leg 4 costs nothing for the first three open terms and everything after
that, which is worth being precise about.  The largest value is about
(n-1)*P(n): 4.9e20 at a(16), 3.1e22 at a(17), 2.0e24 at a(18) -- all below
huntlib's deterministic Miller-Rabin bound of 3.317e24, so there legs 1 and
2 are PROOFS and the certificate is the same statement again.  At a(19) the
values reach 1.4e26 and the bound is gone; from there every value carries a
BLS75 certificate from huntlib.certificate, and N - 1 = p - 1 + j*P(n) has
no structure to exploit, so the factored part is whatever a bounded trial
division, rho and ECM can find -- Theorem 5's cube-root threshold rather
than Theorem 1's square root, with a subproof when a large prime cofactor
turns up.  ap_search.g10 pins the crossing so no future edit can assume
determinism it does not have.

The other half of the least-claim never needs a certificate: a candidate is
rejected because a small prime divides one of its values, or because a
strong test fails.  Both are proofs of compositeness.  So "this is the LEAST
p" rests on rigorous ground throughout, and "these n values are prime" rests
on the bound below a(19) and on certificates above it.

Discovery means FIRST OCCURRENCE, once (CONVENTIONS.md).  Everything else is
CENSUS, and the census is COUNTED, not narrated: a p whose chain reaches
n - 1 is one value short of the term being hunted and gets one [NEAR] line;
a p whose chain reaches DEPTH_FLOOR or more is counted in the checkpoint and
appears only in the census counts of every 30-second [STATUS] line, never as
a line of its own and never as a file.  The evidence directory holds first
occurrences only.

ASCII only.  Ctrl+C is a normal exit: huntlib.shutdown writes the last
SEGMENT BOUNDARY, logs one [STAGE] line and leaves with 130 -- no traceback,
and a second Ctrl+C cannot land inside the checkpoint write.
"""

import argparse
import concurrent.futures as _cf
import json
import math
import os
import pathlib as _pathlib
import sys as _sys
import time

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))

from huntlib import certificate as _cert                        # noqa: E402
from huntlib import checkpoint as _ckpt                         # noqa: E402
from huntlib import evidence as _evid                           # noqa: E402
from huntlib import frontier as _front                          # noqa: E402
from huntlib import pool as _pool                               # noqa: E402
from huntlib import shutdown as _shutdown                       # noqa: E402
from huntlib.checkpoint import CheckpointCorrupt, CursorRefused  # noqa: E402
from huntlib.gpu import device_report                           # noqa: E402
from huntlib.hlog import Heartbeat, banner, census_str, log     # noqa: E402
from huntlib.rungs import Ladder                                # noqa: E402
import ap_model                                                 # noqa: E402
import ap_reference as ref                                      # noqa: E402
from ap_reference import KNOWN, W0, difference                  # noqa: E402
from ap_search import CpuEngine, DEPTH_FLOOR, P_CEIL          # noqa: E402

CKPT = "campaign_checkpoint.json"
DISC = os.path.join("evidence", "ap_discoveries.json")   # first occurrences

# The key pins what would change the meaning of the cursor.  The TARGET n is
# NOT in it: the campaign moves that itself when a term lands, and it lives
# in the checkpoint instead.
CONFIG_KEY = "primorial-ap/v1/q2={q2}/pceil=1e26"

# Terms this campaign has settled.  A term joins the table the moment it is
# verified, which is what stops a --fresh run from re-reporting as a
# discovery something already written up in RESULTS.md.  (The runtime
# frontier in the checkpoint promotes itself the same way; this table seeds
# a fresh one.)
CAMPAIGN_FOUND = {16: 116_781_362_669_989,
                  17: 2_097_209_048_106_247,
                  18: 14_042_451_608_819_603}
TABLES = (KNOWN, CAMPAIGN_FOUND)
FRONTIER_N = _front.top_settled(TABLES, {}, floor=0)

# Next to launch.py, not next to the working directory: a campaign or a
# drill started from elsewhere would otherwise load NO rungs at all and say
# so only by printing a suspiciously short ladder.
MODEL_FILE = str(_pathlib.Path(__file__).with_name("model_results.json"))

# ---- sieve depth: the knob that decides HOW MUCH MACHINE the hunt needs ---
# Re-measured against the v2 engine (OPTIMIZATION_LOG.md #4-#7), which is
# ~20x the device rate the first configuration was chosen against.  Same
# production shape (n = 16, p ~ 4e13), interleaved, median, sustained
# card, host priced at the measured 16.7 us per survivor -- which is
# pow(2, p-1, p) arithmetic on 70-bit integers, NOT Python overhead
# (OPTIMIZATION_LOG.md #9), so it does not vectorize away:
#
#     q2       device rate    survivors/unit   host cores    workers needed
#     2048     5.2e11 p/s       4.37e-06          38.8           impossible
#     4096     2.4e11 p/s       1.09e-06          4.5             8
#     8192     2.1e11 p/s       2.99e-07          1.1             3
#     16384    1.5e11 p/s       8.75e-08          0.23            2
#
# The v1 engine was device-bound at every depth and the shallow end won.
# v2 inverted that: the depth the DEVICE prefers (2048) now demands forty
# host cores of classification.  8192 is the default: 89% of 4096's
# device rate for a QUARTER of its host demand, comfortably inside the
# load budget of a desktop somebody else also uses (CONVENTIONS.md,
# "Sizing a hunt so it leaves the machine usable").  4096 is ~14% more
# rate for 4x the host and is one flag away:
# `--sieve-depth 4096 --workers 8` -- priced, declined as a default.
Q2_CAMPAIGN = 8192

# Host classification runs in a process pool one segment behind the device
# (the overlap is OPTIMIZATION_LOG.md #8: the pool classifies segment i-1
# in worker processes while the main thread blocks in segment i's device
# sync, so at the default depth the classify cost is fully hidden).
# SIZED FROM THE REQUIREMENT: 1.1 cores at the default depth, so three
# workers is 2.7x the need at ~37% duty.  `cpu_count - k` is not sizing,
# it is an appetite -- it scales with the machine rather than with the
# work.  The pool is RAMPED, not stamped (huntlib.pool.ramp).
WORKERS_DEFAULT = 3

SEG_LAUNCHES = 64              # device launches per checkpoint segment:
#                                ~6.4e10 of p-line, ~0.3 s at the default
#                                depth, so an interrupt or a crash costs a
#                                third of a second of sweep
CHUNK = 512                    # survivors per classification task
CERT_VALUE_CAP = 10**34        # past this a bounded proof cannot be promised
VERIFY_OVERSHOOT = 8           # a full chain may run PAST n (a(9)'s runs 10
#                                deep, and a claimed a(17) once ran 19); the
#                                verification legs walk this far beyond the
#                                claim to find the chain's true end and its
#                                breaker -- a bound, because nothing in a
#                                verification path may run unbounded


def _alt_q2(q2):
    """Verification leg 3 re-sieves at a depth the campaign is NOT running:
    8192 unless that IS the campaign depth, then 4096.  Derived, not
    pinned, so a campaign depth change cannot silently collapse the two
    legs onto the same sieve."""
    return (1 << 13) if int(q2) != (1 << 13) else (1 << 12)


class CorruptEngineError(RuntimeError):
    pass


# ------------------------------- the engine ---------------------------------

def make_engine(n, q2, which="gpu", launch_u=None):
    if which == "cpu":
        return CpuEngine(n, q2)
    from ap_gpu import GpuEngine, LAUNCH_U
    return GpuEngine(n, q2, launch_u=launch_u or LAUNCH_U)


def engine_span(eng):
    """p-line covered by one checkpoint segment for this engine."""
    lu = getattr(eng, "launch_u", None)
    if lu is None:                      # the CPU fallback has no launches
        return W0 * (1 << 22)
    return W0 * lu * SEG_LAUNCHES


# --------------------------- classification (host) --------------------------

_CLS = {}


def _classify_chunk(task):
    """Pool worker: chain depths for a chunk of candidates, in order.

    Module-level and self-contained so it survives Windows spawn; touches no
    GPU, so workers never contend with the parent's device work.
    """
    n, q2, base, offs = task
    key = (n, q2)
    if key not in _CLS:
        _CLS[key] = CpuEngine(n, q2)
    eng = _CLS[key]
    return [eng.chain_depth(base + int(o)) for o in offs]


def _worker_init():
    _pool.worker_init("numpy", "sympy")


def _pool_factory(workers):
    return _cf.ProcessPoolExecutor(max_workers=workers,
                                   initializer=_worker_init)


def _submit(pool, n, q2, base, offs):
    """Hand a segment's survivors to the pool (or classify inline).  Returns
    a callable yielding the depths in survivor order."""
    offs = list(offs)
    if pool is None or len(offs) < CHUNK:
        return lambda: _classify_chunk((n, q2, base, offs))
    futs = [pool.submit(_classify_chunk, (n, q2, base, offs[i:i + CHUNK]))
            for i in range(0, len(offs), CHUNK)]

    def collect():
        out = []
        for f in futs:                  # in order: ascending offset
            out.extend(f.result())
        return out
    return collect


# ------------------------------- checkpoint ---------------------------------

def ckpt_key(q2=Q2_CAMPAIGN):
    return CONFIG_KEY.format(q2=q2)


def load_ckpt(q2=Q2_CAMPAIGN, path=CKPT):
    """Load the cursor, and say so loudly if it had to come from the .bak.

    Recovering from the backup means the previous run did not shut down
    cleanly -- the main checkpoint was mid-write when the process, or the
    machine, stopped.  The campaign carries on (one segment is redone), but
    the owner should be told.
    """
    def _warn(m):
        log("WARN", m)
        if "RECOVER" in m.upper():
            log("WARN", "a recovered checkpoint means the last run stopped "
                        "mid-save; the cursor is one segment behind and the "
                        "campaign carries on from there.")
    return _ckpt.load(path, ckpt_key(q2), warn=_warn)


def save_ckpt(c, path=CKPT):
    _ckpt.save(path, c)


def fresh_ckpt(n, eng, q2=Q2_CAMPAIGN):
    return {"key": ckpt_key(q2), "n": int(n),
            "next_u": _floor_u(eng),
            "canaries_done": False, "survivors": 0, "census": {},
            "best_depth": 0, "best_p": 0, "hits": 0, "found": {},
            "odds_marks": [], "rungs_passed": [], "stages": [],
            "wall_s": 0.0, "started": time.time()}


def _floor_u(eng):
    """The first wheel period the engine will accept."""
    return -(-int(eng.floor) // W0)


def stage_reset(c, n, eng):
    """Point the campaign at a new term: new sieve, cursor back to the floor.

    Everything that was about the OLD term goes with it -- the cursor, the
    census counts (a chain of 12 means something different under a different
    difference), the passed rungs.  What survives is what belongs to the
    campaign rather than to the term: the finds, the totals, the clock.
    """
    c["n"] = int(n)
    c["next_u"] = _floor_u(eng)
    c["census"] = {}
    c["rungs_passed"] = []
    c["best_depth"] = 0
    c["best_p"] = 0
    c.setdefault("stages", []).append({"n": int(n), "t": time.time()})
    return c


# -------------------------- the discovery-once rule -------------------------

def event_kind(c, dep, n):
    """DISCOVERY / NEAR / CENSUS / None for a candidate of chain depth `dep`
    under the term being hunted -- the one place the discovery-once and
    census rules live (CONVENTIONS.md).

    DISCOVERY: a full chain, and a(n) still open -- a first occurrence; the
    full protocol, evidence written, logged once.  NEAR: a chain one value
    short of the term being hunted; verified by the cheap legs as a running
    engine health check, logged as one [NEAR] line with its census ordinal,
    and NOT evidenced.  CENSUS: at or above DEPTH_FLOOR but shorter -- noise
    as an individual, COUNTED in the checkpoint and shown in every [STATUS]
    line, no line of its own and no record.  None: below the floor.

    A full chain when a(n) is ALREADY settled is a census repeat, not a
    second discovery -- which is exactly what the segment redone after an
    interrupt produces.
    """
    if dep >= n:
        return ("DISCOVERY"
                if _front.settled_at(TABLES, c.get("found"), n) is None
                else "CENSUS")
    if dep == n - 1:
        return "NEAR"
    if dep >= DEPTH_FLOOR:
        return "CENSUS"
    return None


def settled_at(c, n):
    return _front.settled_at(TABLES, c.get("found"), n)


def target_n(c, n_min):
    """The term the campaign should be hunting: the smallest open n at or
    above --n."""
    return _front.next_open(TABLES, c.get("found"), n_min)


# --------------------------------- rungs ------------------------------------

def ladder():
    """The rung ladder, derived fresh from the model file every time.

    Never stored: a rung retires with its term (CONVENTIONS.md), and the way
    to make that impossible to forget is to have nothing to forget to
    update.
    """
    return Ladder.from_model_file(MODEL_FILE, ceiling=float(P_CEIL),
                                  ceiling_label="engine ceiling")


def live_rungs(c):
    """This term's rungs only.  Each n is its own sweep from the floor, so a
    higher term's depths are not on the line currently being walked."""
    n = int(c["n"])
    return ladder().live(_front.top_settled(TABLES, c.get("found")),
                         only_term=n)


# ------------------------------ verification --------------------------------

def _bounded_witness(m):
    """The smallest prime factor a BOUNDED effort can produce, or None.

    huntlib.certificate.factor_partial rather than an open-ended
    factorization: nothing in a verification path may run unbounded
    (CONVENTIONS.md), and this witness is a courtesy to the reader rather
    than part of any claim.
    """
    try:
        fac, _R = _cert.factor_partial(int(m))
    except Exception:
        return None
    return min(fac) if fac else None


def full_verify(p, n, claimed, certify=True, witness=True, q2=Q2_CAMPAIGN):
    """Independent confirmation of the chain at p behind a claim of `claimed`.

    What a claim MEANS depends on where it sits relative to n, because
    classification walks with cap = n (ap_search.chain_depth): a claim of n
    says the chain reaches AT LEAST n -- `chain_depth >= n` IS the
    definition -- while a claim below n was measured exactly, since that
    walk stopped at a composite rather than at its cap.  The legs are held
    to the same reading.  A chain that runs past n is still a(n) -- a(9) =
    272809 runs 10 deep -- not a corrupt engine; the legs walk a BOUNDED
    distance past a full claim so the true depth and the real breaker land
    in the evidence.

    Legs 1-3 always; `certify` adds the per-value primality proofs and
    `witness` the factor of the value that ends the chain.  Both are for the
    EVIDENCE of a first occurrence -- a [NEAR] value records nothing, so it
    runs with both off.
    """
    p, n, claimed = int(p), int(n), int(claimed)
    d = difference(n)
    exact = claimed < n
    cap = claimed + 1 if exact else claimed + 1 + VERIFY_OVERSHOOT

    r_own = CpuEngine(n, q2).chain_depth(p, cap=cap)             # leg 1
    r_sym = ref.chain_depth(p, n, cap=cap)                       # leg 2

    # leg 3: a from-scratch re-derivation by different machinery.  The GPU
    # engine's residue WALK, consulted one candidate at a time at a sieve
    # depth the campaign is not running, plus the oracle's direct
    # divisibility on the actual values.  Membership of one p is all this
    # leg has ever checked, and answering exactly that avoids handing a
    # windowed sieve a range it was never sized for.
    alt_q2 = _alt_q2(q2)
    try:
        from ap_gpu import GpuEngine
        alt = GpuEngine(n, alt_q2).survives(p)
    except Exception:
        alt = CpuEngine(n, alt_q2).survives(p)
    alt = bool(alt) and ref.sieve_survivor(p, n, min(alt_q2, 4096))

    depth_ok = (r_own == claimed) if exact else (r_own >= claimed)
    out = {"p": p, "n": n, "depth": int(r_own), "difference": d,
           "values": [p + j * d for j in range(min(claimed, n))],
           "legs": {"engine_mr": int(r_own), "sympy_bpsw": int(r_sym),
                    "alt_sieve_survives": bool(alt),
                    "alt_sieve_depth": alt_q2},
           "agree": bool(r_own == r_sym and depth_ok and alt)}
    if not out["agree"]:
        return out
    if r_own == cap:
        out["depth_is_lower_bound"] = True  # the bounded walk never broke

    if certify and claimed >= n:
        proofs = []
        for v in out["values"]:
            if v > CERT_VALUE_CAP:
                out["agree"] = False
                out["error"] = f"value {v} is past CERT_VALUE_CAP"
                return out
            pr = _cert.prove(v)
            if pr is None or not _cert.verify(pr)[0]:
                out["agree"] = False
                out["error"] = f"could not prove value {v} prime"
                return out
            proofs.append(pr)
        out["proofs"] = proofs
        out["proof_kinds"] = sorted({pr["proof"] for pr in proofs})
    if witness and r_own < cap:
        # both legs stopped AT r_own, so p + r_own*d is the value that
        # actually ends the chain -- never p + claimed*d, which for a chain
        # that overshoots its claim is prime
        breaker = p + r_own * d
        out["chain_breaker"] = breaker
        out["chain_breaker_factor"] = _bounded_witness(breaker)
    return out


def record_discovery(ev, label):
    """Write the evidence JSON for a FIRST OCCURRENCE and upsert the ledger.

    Keyed by p, so the segment redone after an interrupt or a crash rewrites
    the same record instead of appending a duplicate.
    """
    return _evid.record(ev, "evidence",
                        f"ap_a{ev['n']}_p{ev['p']}.json", DISC,
                        key="p", label=label)


# -------------------------------- preludes ----------------------------------

def low_pass(n, q2=Q2_CAMPAIGN, verbose=True):
    """The engines refuse to sieve below max(P_FLOOR, q2); the oracle covers
    that zone, so the least-claim is contiguous from 2.

    Cheap, and it has to happen once per term, because a(n) for small n
    really does live down there (a(1) = 2, a(3) = 7).
    """
    floor = max(ref.P_FLOOR, int(q2))
    got = ref.first_p(n, lo=2, hi=floor - 1, wheel=False)
    if verbose:
        log("STAGE", f"low pass n={n}: [2, {floor}) swept by the oracle -- "
                     f"{'FOUND ' + str(got) if got else 'nothing there'}")
    return got


def canary_prelude(which, verbose=True):
    """The stream must rediscover a known term before it is trusted with an
    unknown one.

    a(13) is re-derived end to end from the floor -- 3.7e9 of contiguous
    p-line -- and it has to come out as the SMALLEST p the stream accepts,
    not merely as one of them.  A stream that cannot find what is known is
    not allowed to report what is unknown.
    """
    n = 13
    eng = make_engine(n, 1 << 12, which)
    base = -(-int(eng.floor) // W0) * W0
    span = (KNOWN[n] // W0 + 1) * W0 - base
    t0 = time.time()
    hits = eng.hunt(base, span)
    firsts = sorted(p for p, dep in hits if dep >= n)
    ok = bool(firsts) and firsts[0] == KNOWN[n]
    if verbose:
        if ok:
            log("CANARY-GOLD", f"a({n}) = {KNOWN[n]} rediscovered from the "
                               f"floor in {time.time() - t0:.1f}s -- the "
                               f"stream is honest")
        else:
            log("ALARM", f"canary FAILED: least full chain came out "
                         f"{firsts[0] if firsts else None}, expected "
                         f"{KNOWN[n]}")
    return ok


# --------------------------------- the hunt ---------------------------------

def production(args):
    q2 = int(args.sieve_depth)
    try:
        _ckpt.refuse_mismatch(CKPT, ckpt_key(q2), fresh=args.fresh,
                              describe=lambda s: f"n={s.get('n')} next_u="
                                                 f"{s.get('next_u')}")
    except (CursorRefused, CheckpointCorrupt) as e:
        log("ALARM", str(e))
        return 2

    c = None if args.fresh else load_ckpt(q2)
    probe = make_engine(max(args.n, FRONTIER_N + 1), q2, args.engine)
    if c is None:
        c = fresh_ckpt(target_n({}, args.n), probe, q2)
        log("STAGE", "fresh campaign")
    n = target_n(c, args.n)
    if int(c.get("n", 0)) != n:
        stage_reset(c, n, probe)
    eng = make_engine(n, q2, args.engine)

    log("STAGE", f"primorial-ap v1 -- A053647, hunting a({n}); "
                 f"sieve depth {q2}, engine {args.engine}")
    log("STAGE", f"machine: {device_report(getattr(eng, 'nbytes', lambda: None)())}")
    log("STAGE", f"P({n}) = {difference(n)}; the largest value is "
                 f"{(n - 1) * difference(n):.4g}, "
                 f"{'inside' if (n - 1) * difference(n) < _cert.MR_VALID_BELOW else 'PAST'}"
                 f" the deterministic Miller-Rabin bound")

    if not c.get("canaries_done"):
        low_pass(n, q2)
        if not canary_prelude(args.engine):
            return 2
        c["canaries_done"] = True
        save_ckpt(c)

    workers = max(1, int(args.workers))
    pool = None
    if workers > 1:
        pool = _pool_factory(workers)
        t0 = time.time()
        up = _pool.ramp(pool, workers, ramp_s=args.worker_ramp)
        log("STAGE", f"classification pool: {up} workers up in "
                     f"{time.time() - t0:.1f}s (ramped one at a time, "
                     f"below normal priority)")

    boundary = dict(c)
    _shutdown.on_interrupt(lambda: _save_boundary(boundary))

    hb = Heartbeat(args.heartbeat)
    span = engine_span(eng)
    clock = [time.time()]          # last boundary the campaign clock counted
    stop_reason = "reached the last rung (the enforced ceiling)"

    def line():
        pos = hb.pos() or (int(c["next_u"]) * W0)
        rate = hb.rate()
        lad = ladder()
        fr = _front.top_settled(TABLES, c.get("found"))
        nn = int(c["n"])
        bits = [f"a({nn}) p={pos:.4e}", f"{rate:.3e} p/s",
                f"surv {int(c['survivors']):,}",
                census_str(c.get("census"), DEPTH_FLOOR, max(DEPTH_FLOOR, nn - 1)),
                f"finds {int(c['hits'])}",
                f"P(a({nn}) by now) {_odds(nn, pos):.0%}",
                lad.status_str(pos, fr, rate, only_term=nn)]
        st = hb.stalled()
        if st:
            bits.append(f"-- no segment closed since the last status: "
                        f"{st[0]} for {st[1]:.0f}s")
        return "  ".join(bits)

    hb.mark(int(c["next_u"]) * W0)
    hb.start(line)
    rc = 0
    try:
        # The device runs ONE SEGMENT AHEAD of the classified cursor
        # (OPTIMIZATION_LOG.md #8): while the main thread blocks in segment
        # i's device sync, the pool's worker processes classify segment
        # i-1.  `pending` is that in-flight segment; the cursor -- and so
        # the checkpoint, and so the least-claim -- only ever advances past
        # a FULLY CLASSIFIED segment, in _finalize below.
        pending = None
        while True:
            n_now = target_n(c, args.n)
            if n_now != int(c["n"]):
                lad = ladder()
                retired = lad.retired_by(int(c["n"]), int(c["n"]) - 1)
                log("RUNG", f"a({c['n']}) is settled -- {len(retired)} rungs "
                            f"retire; the ladder now aims at a({n_now})")
                stage_reset(c, n_now, probe)
                eng = make_engine(n_now, q2, args.engine)
                span = engine_span(eng)
                log("STAGE", f"now hunting a({n_now}): new difference "
                             f"P({n_now}) = {difference(n_now):.6g}, cursor "
                             f"back to the floor, a fresh sieve")
                save_ckpt(c)
                pending = None          # in-flight survivors were the OLD
                #                         term's; their p-line is moot now
            n = int(c["n"])

            ahead = (pending["seg"] // W0) if pending else 0
            base = (int(c["next_u"]) + ahead) * W0
            seg = 0
            if base < P_CEIL and not (args.to and base >= float(args.to)):
                seg = min(span, P_CEIL - base)
                seg -= seg % W0
            nxt = None
            if seg > 0:
                hb.doing(f"sieving a({n}) from p={base:.4e}" +
                         (f" (classifying {len(pending['offs'])} behind it)"
                          if pending else ""))
                offs = []
                for chunk in eng.survivors(base, seg):
                    offs.extend(int(o) for o in chunk.tolist())
                nxt = {"base": base, "seg": seg, "offs": offs,
                       "collect": _submit(pool, n, q2, base, offs)}

            if pending is None and nxt is None:
                if args.to and base >= float(args.to):
                    stop_reason = f"reached --to {args.to}"
                break

            found_here = False
            if pending is not None:
                hb.doing(f"classifying {len(pending['offs'])} survivors at "
                         f"p={pending['base']:.4e}")
                found_here = _finalize(c, eng, hb, n, q2, pending, clock)
                boundary = dict(c)
            pending = nxt

            if found_here and args.stop_on_discovery:
                stop_reason = "--stop-on-discovery"
                break
            if args.gpu_yield_ms:
                time.sleep(float(args.gpu_yield_ms) / 1000.0)
    except CorruptEngineError:
        rc = 2
    finally:
        # The clock is NOT topped up here.  It advances in _finalize, past a
        # fully classified segment, for the same reason the cursor does: the
        # segment in flight is redone on resume, so counting its seconds
        # would inflate the campaign clock by a segment on every stop.  What
        # this save persists is a `c` that may be mid-_finalize; the boundary
        # snapshot written by the interrupt callback lands on top of it, and
        # carries the clock because _finalize commits it next to the cursor.
        save_ckpt(c)
        hb.emit()
        hb.stop()
        if pool is not None:
            pool.shutdown(wait=True)
    if rc == 0:
        log("STAGE", f"campaign stopped: {stop_reason}; cursor at "
                     f"p = {int(c['next_u']) * W0:.6e}, checkpoint {CKPT}")
    return rc


def _tick(c, clock):
    """Fold the seconds since the last segment boundary into the campaign
    clock, and re-mark.

    Called from ONE place -- `_finalize`'s commit block, next to the cursor
    -- and that placement is the whole content of this function.  The clock
    measures classified coverage, so it must move exactly where coverage
    does: a segment in flight when the run stops is redone on resume, and
    counting its seconds would add a segment to the total on every stop.
    Committing it here also puts it in the shallow `boundary = dict(c)`
    snapshot the interrupt callback saves; when this was done in `run`'s
    `finally` instead, the snapshot was taken BEFORE the fold and the
    boundary save landed on top of it, so every Ctrl+C-ended run -- the
    normal exit for these campaigns -- contributed nothing at all.  The
    a(16)-a(18) campaign recorded 4.95 h of a 23.4 h span that way.
    """
    now = time.time()
    c["wall_s"] = float(c.get("wall_s", 0.0)) + (now - clock[0])
    clock[0] = now
    return c["wall_s"]


def _finalize(c, eng, hb, n, q2, pending, clock):
    """Collect one classified segment, record its events, advance the
    cursor past it and checkpoint.  This is the ONLY place the cursor
    moves, which is what makes the overlap safe: an interrupt between
    segments loses in-flight device work, never classified coverage.

    The census and the best-chain counters are accumulated in LOCALS and
    committed to `c` only at the end, next to the cursor: counters are per
    candidate, so if this function raises mid-segment (a failed
    verification does), `c` must still hold the boundary it started from
    or the redo of this segment double-counts (CLAUDE.md 5e).  Committing
    by ASSIGNMENT rather than in-place mutation is also what keeps the
    interrupt thread's shallow `boundary = dict(c)` snapshot honest.  The
    campaign clock is committed in the same block, by `_tick`, for the same
    reason and with the same consequence if it is not: it must reach disk
    with the cursor it belongs to, and it must not count a segment that is
    about to be redone.  The
    discovery ledger (`found`, `hits`, the evidence file) is the deliberate
    exception: it moves mid-loop, and a redo is safe because a settled term
    re-classifies as a census repeat and the evidence record is keyed by p.
    """
    base, seg, offs = pending["base"], pending["seg"], pending["offs"]
    depths = pending["collect"]()
    census = dict(c.get("census") or {})
    best_depth, best_p = int(c["best_depth"]), int(c["best_p"])
    found_here = False
    for o, dep in zip(offs, depths):
        p = base + o
        kind = event_kind(c, dep, n)
        if kind is None:
            continue
        if dep > best_depth:
            best_depth, best_p = int(dep), int(p)
        if kind == "CENSUS":
            _front.bump_census(census, dep)
            continue
        if kind == "NEAR":
            ordinal = _front.bump_census(census, dep)
            hb.doing(f"verifying a NEAR at p={p}")
            v = full_verify(p, n, dep, certify=False, witness=False,
                            q2=q2)
            if not v["agree"]:
                log("ALARM", f"verification legs disagree on p={p}: "
                             f"{v['legs']}")
                raise CorruptEngineError("legs disagree")
            log("NEAR", f"chain {dep} at p = {p} (depth-{dep} #"
                        f"{ordinal} of this stage; verified 3-way) "
                        f"-- ONE value short of a({n})!")
            continue
        # DISCOVERY
        hb.doing(f"verifying a claimed a({n}) at p={p}")
        v = full_verify(p, n, dep, q2=q2)
        if not v["agree"]:
            log("ALARM", f"a claimed a({n}) at p={p} failed "
                         f"verification: {v.get('error', v['legs'])}")
            raise CorruptEngineError("discovery failed verification")
        _front.settle_one(c["found"], n, p)
        c["hits"] = int(c["hits"]) + 1
        v["swept_from"] = int(eng.floor)
        v["swept_to"] = int(base + seg)
        v["config"] = ckpt_key(q2)
        path = record_discovery(v, "DISCOVERY")
        banner("DISCOVERY", [
            f"a({n}) = {p:,}",
            f"P({n}) = {difference(n):,}",
            f"all {n} values prime"
            + (f" -- and the chain runs {int(v['depth'])} deep"
               if int(v["depth"]) > n else "")
            + f"; proofs: {', '.join(v.get('proof_kinds', ['-']))}",
            f"verified 3 ways + per-value proof; evidence {path}",
            f"least-claim: contiguous sweep from {eng.floor} "
            f"to {base + seg}",
        ])
        found_here = True

    c["census"] = census
    c["best_depth"], c["best_p"] = best_depth, best_p
    c["survivors"] = int(c["survivors"]) + len(offs)
    c["next_u"] = int(c["next_u"]) + seg // W0
    _tick(c, clock)
    new_pos = int(c["next_u"]) * W0
    hb.mark(new_pos)
    _milestones(c, base, new_pos, n)
    save_ckpt(c)
    return found_here


def _save_boundary(state, path=CKPT):
    save_ckpt(state, path)
    return (f"checkpoint written at the last segment boundary: "
            f"a({state.get('n')}) p = {int(state.get('next_u', 0)) * W0:.6e}"
            f", {float(state.get('wall_s', 0.0)) / 3600:.2f} h swept")


def _odds(n, pos):
    """P(a(n) <= pos) under the model stated before the run."""
    try:
        return 1.0 - math.exp(-ap_model.expected_count(int(n), max(float(pos),
                                                                  11.0)))
    except Exception:
        return 0.0


_ODDS_MARKS = ((0.25, "Q1"), (0.50, "median"), (0.75, "Q3"), (0.90, "P90"))


def _milestones(c, was, now, n):
    """[MILESTONE] decade and model-odds crossings; [RUNG] ladder progress.

    Never twice for the same fact: the passed rungs and crossed odds marks
    are persisted in the checkpoint.
    """
    if was > 0 and int(math.log10(now)) > int(math.log10(was)):
        log("MILESTONE", f"p passed 1e{int(math.log10(now))} hunting a({n})  "
                         f"{census_str(c.get('census'), DEPTH_FLOOR, max(DEPTH_FLOOR, n - 1))}")
    o_now = _odds(n, now)
    marks = set(c.get("odds_marks", []))
    for q, name in _ODDS_MARKS:
        tag = f"a({n}) {name}"
        if o_now >= q and tag not in marks:
            marks.add(tag)
            log("MILESTONE", f"past the model's {name} for a({n}): the model "
                             f"gave it a {q:.0%} chance of having appeared by "
                             f"p = {now:.4e}")
    c["odds_marks"] = sorted(marks)

    lad = ladder()
    fr = _front.top_settled(TABLES, c.get("found"))
    new = lad.newly_passed(now, fr, c.get("rungs_passed"), only_term=n)
    if new:
        c["rungs_passed"] = sorted(set(c.get("rungs_passed", [])) | set(new))
        nxt = lad.next_rung(now, fr, only_term=n)
        log("RUNG", f"passed {', '.join(new)} ({lad.progress_str(now, fr, c['rungs_passed'], only_term=n)})"
                    f" -- next: {nxt[0] + ' at %.3g' % nxt[1] if nxt else 'the ceiling'}")


# --------------------------------- status -----------------------------------

def status(q2=Q2_CAMPAIGN):
    c = load_ckpt(q2)
    if c is None:
        print("no checkpoint for this configuration")
        return 0
    n = int(c["n"])
    pos = int(c["next_u"]) * W0
    fr = _front.top_settled(TABLES, c.get("found"))
    lad = ladder()
    print(f"primorial-ap -- A053647")
    print(f"  hunting      a({n})   (frontier a({fr}) settled)")
    print(f"  cursor       p = {pos:.6e}   swept from {max(ref.P_FLOOR, q2)}")
    print(f"  survivors    {int(c['survivors']):,}   finds {int(c['hits'])}")
    print(f"  {census_str(c.get('census'), DEPTH_FLOOR, max(DEPTH_FLOOR, n - 1))}")
    print(f"  best chain   {int(c['best_depth'])} at p = {int(c['best_p'])}")
    print(f"  model        P(a({n}) by now) = {_odds(n, pos):.1%}")
    print(f"  {lad.status_str(pos, fr, None, only_term=n)}")
    for r, v in sorted((int(k), v) for k, v in (c.get("found") or {}).items()):
        print(f"  FOUND        a({r}) = {v:,}")
    # both numbers, because their RATIO is the readout: swept is time the
    # device was actually sieving, span is how long ago the campaign began.
    # A campaign left running should have them close; far apart means the
    # run has been stopped and restarted (or that the clock is dropping
    # time again, which is how the first version of it was caught).
    span = time.time() - float(c.get("started") or time.time())
    print(f"  wall clock   {float(c.get('wall_s', 0)) / 3600:.2f} h swept"
          f"   ({span / 3600:.2f} h since the campaign started)")
    return 0


# -------------------------------- selftest ----------------------------------

def selftest(engine="gpu"):
    """The full gate battery.  Must end ALL GREEN."""
    import ap_gpu
    import ap_search
    t0 = time.time()
    results = []

    def run(name, fn):
        t = time.time()
        try:
            ok, msg = fn()
        except Exception as e:                     # a gate that throws FAILS
            ok, msg = False, f"{name}: {type(e).__name__}: {e}"
        results.append((ok, msg, time.time() - t))
        print(("PASS " if ok else "FAIL ") + msg + f"   ({time.time() - t:.1f}s)")
        return ok

    print("=== oracle (sympy only) ===")
    for g in ref.GATES:
        run("oracle", g)
    print("=== odds model ===")
    for g in ap_model.GATES:
        run("model", g)
    print("=== CPU engine ===")
    for g in ap_search.GATES:
        run("cpu", g)
    print("=== GPU engine ===")
    for g in ap_gpu.GATES:
        run("gpu", g)
    print("=== huntlib (shared machinery) ===")
    for g in (_cert.gate_certificates,):
        run("certificate", g)
    from huntlib import frontier as fr_mod, rungs as rungs_mod
    for g in rungs_mod.GATES + fr_mod.GATES:
        run("huntlib", g)
    from huntlib import drills
    for ok, msg in drills.standard(pool_factory=_pool_factory):
        results.append((ok, msg, 0.0))
        print(("PASS " if ok else "FAIL ") + msg)

    print("=== project drills ===")
    run("event_kind", _drill_event_kind)
    run("verification", _drill_verification)
    run("published terms", _drill_published)
    run("campaign clock", _drill_clock)
    run("low pass", _drill_low_pass)
    run("stage advance", _drill_stage_advance)
    run("resume", lambda: _drill_resume(engine))
    run("persistence", lambda: _drill_persistence(engine))
    run("census format", _drill_census)

    bad = [m for ok, m, _t in results if not ok]
    print()
    if bad:
        print(f"*** {len(bad)} FAILURES in {time.time() - t0:.0f}s")
        return 1
    print(f"ALL GREEN -- {len(results)} gates and drills in "
          f"{time.time() - t0:.0f}s")
    return 0


def _drill_event_kind():
    """All four outcomes of the discovery-once taxonomy, and the promotion.

    The cases are frontier-RELATIVE, so landing a term does not falsify the
    drill.
    """
    from huntlib import drills
    n = target_n({}, FRONTIER_N)
    c = {"found": {}, "n": n}
    cases = [(n, "DISCOVERY"), (n + 3, "DISCOVERY"), (n - 1, "NEAR"),
             (DEPTH_FLOOR, "CENSUS"), (n - 2, "CENSUS"),
             (DEPTH_FLOOR - 1, None), (0, None)]
    ok, msg = drills.event_kind_drill(lambda dep: event_kind(c, dep, n), cases)
    if not ok:
        return False, msg
    # and once a(n) is settled the same full chain is a census repeat
    _front.settle_one(c["found"], n, 12345)
    if event_kind(c, n, n) != "CENSUS":
        return False, ("event_kind: a full chain after a(%d) is settled must "
                       "be a census repeat, not a second discovery" % n)
    if target_n(c, 16) != n + 1:
        return False, "event_kind: the frontier did not promote itself"
    return True, msg + f"; and a repeat after a({n}) lands is census"


def _drill_verification():
    """The protocol accepts a genuine known and rejects a fake claim.

    Both directions, every selftest: a verifier that cannot reject is not
    evidence that an acceptance means anything.
    """
    n = 12
    v = full_verify(KNOWN[n], n, n, q2=4096)
    if not v["agree"]:
        return False, f"verification: rejected the genuine a({n}): {v['legs']}"
    if not v.get("proofs") or len(v["proofs"]) != n:
        return False, "verification: a discovery came back without proofs"
    kinds = set(v["proof_kinds"])
    fake = full_verify(KNOWN[n] + W0, n, n, q2=4096)
    if fake["agree"]:
        return False, "verification: ACCEPTED a fake claim"
    short = full_verify(KNOWN[n], n, n + 1, q2=4096)
    if short["agree"]:
        return False, "verification: accepted an overstated depth"
    # a chain that runs PAST its n is still the term: a claim of n is a
    # CAPPED walk (ap_search.chain_depth caps at n), so it means AT LEAST
    # n, and the verifier must report the true depth and put the breaker
    # at the chain's real end.  a(9) = 272809 runs 10 deep; the day this
    # case was missing, a genuine a(17) whose chain ran 19 deep was
    # rejected as a corrupt engine and the campaign died on it.
    deep = full_verify(KNOWN[9], 9, 9, q2=4096)
    if not deep["agree"]:
        return False, (f"verification: rejected a(9), whose chain runs "
                       f"past n: {deep['legs']}")
    if int(deep["depth"]) != 10:
        return False, (f"verification: a(9)'s chain is 10 deep, reported "
                       f"{deep['depth']}")
    if deep.get("chain_breaker") != KNOWN[9] + 10 * difference(9):
        return False, ("verification: the breaker must sit at the chain's "
                       "true end, not at the claimed depth")
    # ... and the OTHER direction stays an alarm: a NEAR measured exactly
    # (its walk stopped at a composite, not at the cap) that re-measures
    # LONGER means the classifier called a prime composite -- corruption.
    near_wrong = full_verify(KNOWN[9], 9, 8, certify=False, witness=False,
                             q2=4096)
    if near_wrong["agree"]:
        return False, ("verification: a NEAR claim below the chain's true "
                       "depth must be rejected -- that direction IS a "
                       "corrupt engine")
    # a value past the certificate cap must be refused, not guessed at
    return True, (f"verification: the genuine a({n}) passes all legs with "
                  f"{n} proofs ({'/'.join(sorted(kinds))}); a fake p, an "
                  f"overstated depth and a too-short NEAR are rejected; "
                  f"a(9)'s 10-deep chain verifies as a(9) with its breaker "
                  f"at the true end")


def _drill_published(certify=False):
    """Every term THIS project published must still satisfy the definition,
    and its evidence file must still say so.

    G1 does this for the literature table; CAMPAIGN_FOUND is the other half
    and is the half that is this repository's own claim, so it gets the
    same treatment on every gate run rather than a one-time check at
    publication.  Cheap legs by default -- the per-value proofs are what
    `certify` adds and what the campaign itself already ran once.
    """
    if not CAMPAIGN_FOUND:
        return True, "published terms: none yet"
    checked = []
    for n in sorted(CAMPAIGN_FOUND):
        p = CAMPAIGN_FOUND[n]
        v = full_verify(p, n, n, certify=certify, q2=4096)
        if not v["agree"]:
            return False, (f"published terms: a({n}) = {p} no longer "
                           f"verifies: {v['legs']}")
        path = str(_pathlib.Path(__file__).with_name("evidence") /
                   f"ap_a{n}_p{p}.json")
        if not os.path.exists(path):
            return False, f"published terms: a({n}) has no evidence file"
        with open(path) as fh:
            ev = json.load(fh)
        if int(ev["p"]) != p or int(ev["n"]) != n:
            return False, f"published terms: {path} is not about a({n})"
        if int(ev["depth"]) != int(v["depth"]):
            return False, (f"published terms: a({n})'s file records depth "
                           f"{ev['depth']}, the chain is {v['depth']}")
        if ev["values"] != [p + j * difference(n) for j in range(n)]:
            return False, (f"published terms: a({n})'s recorded values do "
                           f"not match the definition")
        br, w = ev.get("chain_breaker"), ev.get("chain_breaker_factor")
        if br != v.get("chain_breaker") or not w or br % w or not 1 < w < br:
            return False, (f"published terms: a({n})'s factor witness does "
                           f"not divide the value that ends the chain")
        checked.append(f"a({n}) {v['depth']} deep")
    return True, ("published terms: " + ", ".join(checked) +
                  " -- each re-verified against the definition and against "
                  "its own evidence file (values, true depth, factor "
                  "witness)")


def _drill_clock():
    """The campaign clock must reach disk by the path an interrupt takes,
    and must not count the segment that will be redone.

    The regression: the clock used to be folded in by `run`'s `finally`,
    AFTER the boundary snapshot had been taken, and the interrupt callback
    then saved that snapshot over the top -- so a Ctrl+C-ended run, which is
    how every one of these campaigns ends, contributed zero.  Both halves
    are checked here because a fix that counts the in-flight segment instead
    would trade an undercount for an overcount.
    """
    import tempfile
    tmp = tempfile.mkdtemp(prefix="ap-clock-")
    path = os.path.join(tmp, "ckpt.json")
    try:
        eng = CpuEngine(16, 4096)
        c = fresh_ckpt(16, eng, 4096)
        clock = [time.time() - 60.0]        # a minute of classified sweep
        _tick(c, clock)
        if not 59.0 <= float(c["wall_s"]) <= 61.0:
            return False, (f"clock: a 60 s segment folded in as "
                           f"{c['wall_s']:.1f} s")
        boundary = dict(c)                  # what run() snapshots afterwards
        clock[0] -= 30.0                    # ... then 30 s goes in flight
        _save_boundary(boundary, path)      # ... and Ctrl+C arrives
        back = _ckpt.load(path, ckpt_key(4096))
        if back is None:
            return False, "clock: the boundary save wrote nothing"
        got = float(back.get("wall_s", 0.0))
        if got < 59.0:
            return False, (f"clock: the interrupt path persisted {got:.1f} s "
                           f"of a 60 s campaign -- the boundary snapshot is "
                           f"not carrying the clock")
        if got > 61.0:
            return False, (f"clock: the interrupt path persisted {got:.1f} s, "
                           f"counting the segment in flight -- that segment "
                           f"is redone on resume and would be counted twice")
        # and a second segment accumulates rather than replacing
        _tick(c, [time.time() - 10.0])
        if not 69.0 <= float(c["wall_s"]) <= 71.0:
            return False, (f"clock: a second segment left the total at "
                           f"{c['wall_s']:.1f} s, want ~70")
        return True, ("clock: a 60 s segment survives Ctrl+C through the "
                      "boundary snapshot, the 30 s in flight is NOT counted "
                      "(it is redone on resume), and segments accumulate")
    finally:
        for f in os.listdir(tmp):
            try:
                os.remove(os.path.join(tmp, f))
            except OSError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass


def _drill_low_pass():
    """The zone the engines refuse must really be covered by the oracle."""
    if low_pass(3, verbose=False) != KNOWN[3]:
        return False, "low pass: the oracle did not find a(3) = 7 below the floor"
    if low_pass(16, verbose=False) is not None:
        return False, "low pass: claimed a(16) lives below the engine floor"
    return True, (f"low pass: the oracle covers [2, "
                  f"{max(ref.P_FLOOR, Q2_CAMPAIGN)}) -- it finds a(3) = 7 "
                  f"there and nothing for a(16), so the least-claim is "
                  f"contiguous from 2")


def _drill_stage_advance():
    """A find moves the campaign to the next term: cursor to the floor, the
    census cleared, that term's rungs retired.

    This is the drill for the failure the sibling project shipped -- a
    campaign that found its term and then spent hours advertising a rung
    belonging to it.

    Frontier-RELATIVE, like the event_kind drill: it hunts whatever term is
    open now and settles THAT, so publishing a term does not falsify it.
    The day a(16)-a(18) landed in CAMPAIGN_FOUND, a version of this drill
    that named a(16) failed -- correctly, and uselessly.
    """
    n = target_n({}, FRONTIER_N)
    eng = CpuEngine(n, 4096)
    c = fresh_ckpt(n, eng)
    c["next_u"] = 10**9
    c["census"] = {"7": 5}
    c["rungs_passed"] = [f"a({n}) Q1", f"a({n}) median"]
    _front.settle_one(c["found"], n, 39000000000000)
    nxt = target_n(c, FRONTIER_N)
    if nxt != n + 1:
        return False, f"stage advance: next target is a({nxt}), want a({n + 1})"
    lad = ladder()
    if any(l.startswith(f"a({n})") for _t, l, _d in
           lad.live(_front.top_settled(TABLES, c["found"]))):
        return False, f"stage advance: a({n}) rungs are still live after the find"
    stage_reset(c, nxt, CpuEngine(nxt, 4096))
    if c["next_u"] != _floor_u(eng) or c["census"] or c["rungs_passed"]:
        return False, ("stage advance: the cursor, census or rungs survived "
                       "the move to a new term")
    if c["found"].get(str(n)) is None or int(c["hits"]) != 0:
        return False, "stage advance: the find did not survive the move"
    return True, (f"stage advance: finding a({n}) retires its rungs, resets "
                  f"the cursor to the floor and clears the census, while the "
                  f"find itself survives")


def _drill_resume(engine="gpu"):
    """A split stream must equal the unsplit stream."""
    import numpy as np
    n, q2 = 16, 2048
    eng = make_engine(n, q2, engine, launch_u=1 << 21)
    base = (10**9 // W0) * W0
    span = (5 * 10**7 // W0) * W0
    whole = np.concatenate([c for c in eng.survivors(base, span)])
    half = span // 2 - (span // 2) % W0
    a = np.concatenate([c for c in eng.survivors(base, half)])
    b = np.concatenate([c for c in eng.survivors(base + half, span - half)])
    joined = np.concatenate([a, b + half])
    if whole.size < 50:
        return False, "resume drill: window under-populated (vacuous)"
    if not np.array_equal(whole, joined):
        return False, "resume drill: split stream != whole stream"
    return True, (f"resume drill: {whole.size} survivors identical whether "
                  f"the window is swept whole or in two pieces")


def _drill_persistence(engine="gpu"):
    """A run that ENDS must persist where it got to, and the next one must
    carry on from there rather than from the floor."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="ap-drill-")
    path = os.path.join(tmp, "ckpt.json")
    try:
        eng = make_engine(16, 4096, engine, launch_u=1 << 20)
        c = fresh_ckpt(16, eng, 4096)
        start = int(c["next_u"])
        c["next_u"] = start + 12345
        save_ckpt(c, path)
        back = _ckpt.load(path, ckpt_key(4096))
        if back is None or int(back["next_u"]) != start + 12345:
            return False, "persistence: the cursor did not survive a save"
        back["next_u"] = int(back["next_u"]) + 1
        save_ckpt(back, path)
        again = _ckpt.load(path, ckpt_key(4096))
        if int(again["next_u"]) != start + 12346:
            return False, "persistence: the second run did not resume"
        if not os.path.exists(path + ".bak"):
            return False, "persistence: no .bak was rotated"
        return True, ("persistence: two bounded runs, the second resumed from "
                      "the first's boundary, with a .bak behind it")
    finally:
        for f in os.listdir(tmp):
            try:
                os.remove(os.path.join(tmp, f))
            except OSError:
                pass
        os.rmdir(tmp)


def _drill_census():
    """The census line is the shared format, and counts what it says."""
    counts = {}
    for dep in (6, 6, 7, 9):
        _front.bump_census(counts, dep)
    s = census_str(counts, DEPTH_FLOOR, 9)
    if not s.startswith("census ") or "6:2" not in s or "8:0" not in s:
        return False, f"census: unexpected format {s!r}"
    return True, f"census: {s} -- the shared [STATUS] format, counts correct"


# ---------------------------------- main ------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="A053647 -- least prime starting an AP of n primes with "
                    "common difference the n-th primorial")
    ap.add_argument("--n", type=int, default=FRONTIER_N + 1,
                    help="hunt this term or the next open one above it")
    ap.add_argument("--sieve-depth", type=int, default=Q2_CAMPAIGN,
                    help=f"primes tested by the sieve (default {Q2_CAMPAIGN}; "
                         f"shallower is faster on the device but multiplies "
                         f"the host's classification load -- 4096 with "
                         f"--workers 8 is ~14%% more rate for 4x the "
                         f"machine; see the table in this file)")
    ap.add_argument("--engine", choices=("gpu", "cpu"), default="gpu")
    ap.add_argument("--workers", type=int, default=WORKERS_DEFAULT,
                    help=f"classification processes (default "
                         f"{WORKERS_DEFAULT}, sized from the measurement; 1 "
                         f"classifies inline and costs nothing measurable "
                         f"at the default depth)")
    ap.add_argument("--worker-ramp", type=float, default=_pool.RAMP_S,
                    help="seconds between worker starts")
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0,
                    help="idle the device this long between segments; ~1%% "
                         "of the rate per 15 ms, and it keeps the desktop "
                         "responsive under a long run")
    ap.add_argument("--gentle", action="store_true",
                    help="one worker and a 15 ms device yield: about 2%% of "
                         "the rate for a machine that stays comfortable")
    ap.add_argument("--heartbeat", type=float, default=30.0)
    ap.add_argument("--to", type=float, default=None,
                    help="stop at this p (opt-in; the default is indefinite)")
    ap.add_argument("--stop-on-discovery", action="store_true")
    ap.add_argument("--fresh", action="store_true",
                    help="discard an existing cursor deliberately")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.gentle:
        args.workers = 1
        args.gpu_yield_ms = max(args.gpu_yield_ms, 15.0)
    if args.selftest:
        return selftest(args.engine)
    if args.status:
        return status(args.sieve_depth)
    return production(args)


if __name__ == "__main__":
    _sys.exit(_shutdown.graceful(main) or 0)
