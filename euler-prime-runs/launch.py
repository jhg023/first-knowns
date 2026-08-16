# launch.py -- THE HUNT for A164926 a(17)-a(20): checkpointed, resumable,
# canary-alarmed, no-false-discovery.  Follows the repo-wide project
# conventions (see ../CONVENTIONS.md).
#
#   python launch.py              # THE HUNT (GPU, whole range, resumable)
#   python launch.py --selftest   # full gate battery + resume + planted drills
#   python launch.py --status     # scoreboard
#   python launch.py --to 1e18 --fresh
#
# ONE ENGINE, ONE CURSOR.  There is no 64-bit/128-bit split to manage any
# more: the production engine carries every candidate as the pair (k, off)
# with p = k*29# + off, which is exactly as valid at 10^5 as at 10^23, so a
# single sweep runs from the oracle floor to the enforced ceiling 10^24
# without a seam and without an engine flag.  The GPU is always used.
#
# --engine cpu selects the numpy reference engine.  It exists for
# verification and gating, not for hunting: it is ~4 orders of magnitude
# slower and would never finish a production leg.  There is nothing else to
# select: superseded engine versions are not kept in the tree, so the code
# here is the code that would run a campaign from zero.  Their streams were
# verified bit-for-bit against this one before they were removed; that
# evidence lives in the git history, not in a dead module.
#
# Discovery protocol: pre-filter survivor -> host MR run classification ->
# run >= 17 => THREE-WAY verification (own MR chain / sympy chain / fresh
# alternate-alignment re-sieve) + composite witness at x=run + evidence JSON
# euler_hit_run{r}_p{p}.json + entry in euler_discoveries.json; hunt
# CONTINUES (a(18)-a(20) remain) unless --stop-on-find.  Any verification
# disagreement = CorruptEngineError, exit 2.  Expected-known: p=41 (run 40)
# fires the full protocol as a positive control, labeled CANARY-GOLD.
#
# ASCII only; graceful Ctrl+C (checkpoint, no stacktrace).

import argparse
import json
import math
import os
import shutil
import sys
import time

import numpy as np

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import checkpoint as _ckpt  # noqa: E402
from huntlib.hlog import log  # noqa: E402
from huntlib.primes import factor_witness  # noqa: E402

from euler_reference import A21_UPPER, KNOWN, OPEN_N, run_length as oracle_run
from euler_search import (CpuEngine, P_CEIL, P_FLOOR, WHEEL_PRIMES,
                          WHEEL_PRIMES_29, mr_run_length)

CKPT = "campaign_checkpoint.json"              # the single campaign cursor
DISC = os.path.join("evidence", "euler_discoveries.json")
SEG_SPAN = 2 * 16912 * 7420738134810           # ~2.51e17 of p-line per
                                               # checkpoint segment: exactly
                                               # TWO launches on the production
                                               # wheel, ~10 s of work, which
                                               # is what a kill can cost.
                                               # A SPAN, not a period count --
                                               # it was 131,072 periods, which
                                               # is 2.63e16 on the 31# wheel
                                               # and 37x that on the next one,
                                               # the same absolute-vs-derived-
                                               # unit trap as LAUNCH_PERIODS
                                               # pointing the other way.
                                               # It must also be at least one
                                               # launch, or the launch size
                                               # never binds: at the old value
                                               # a segment was 3,544 periods
                                               # against a 16,912-period
                                               # launch, so production would
                                               # have run short launches and
                                               # every LAUNCH_PERIODS
                                               # measurement would have been
                                               # about a shape production
                                               # never used.
# The cursor is denominated in WHEEL PERIODS, so the key pins every part of
# the configuration that would change their meaning -- including the wheel
# itself, which is filled in from the engine's actual choice rather than
# hardcoded.  A wheel change makes the period 31x longer, so a cursor from a
# different wheel is meaningless and must be REJECTED rather than reused;
# deriving the key this way makes that automatic instead of a thing to
# remember.
CONFIG_KEY = ("euler-prime-runs/v4/n={n}/wheel={wheel}#"
              "/Q1=1024/Q2=65536/ceil=1e24")

EXPECTED_KNOWN = {41: 40}                      # low-range positive control

# Verified finds of THIS campaign (phase 1, evidence/ + RESULTS.md).
# The discovery frontier: only a run strictly beyond every previously
# recorded value counts as a discovery (repo convention; rediscoveries
# and census-grade repeats of settled run lengths never trigger
# --stop-on-discovery).
CAMPAIGN_FOUND = {17: 348_284_517_256_411_907,
                  18: 8_461_068_614_861_832_371}
FRONTIER_RUN = max(CAMPAIGN_FOUND)             # discovery = run > FRONTIER_RUN
DEFAULT_TO = 5000 * 10**18                      # 5e21: leg 2 of the a(19) hunt.
                                               # Leg 1 (to 3.2e20) came back
                                               # empty with E=1.02 spent.  The
                                               # cap was 1e21 (the conditional
                                               # median, ~62%) when a leg cost
                                               # ~14 days; the v3-128 engine
                                               # made the sweep ~14x faster, so
                                               # 1e21 is now under a day and
                                               # would stop the hunt at 59%
                                               # odds.  5e21 carries the
                                               # conditional odds to ~98% and
                                               # still costs only ~6 days.
                                               # --to overrides; stop-on-
                                               # discovery means the cap only
                                               # matters if nothing is found.


class CorruptEngineError(RuntimeError):
    pass


# ------------------------- verification (three-way) -------------------------

def three_way_verify(p, claimed_run, n_filter):
    """Independent confirmation that run(p) == claimed_run exactly."""
    r_own = mr_run_length(p, cap=claimed_run + 40)
    r_sym = oracle_run(p, cap=claimed_run + 40)
    if not (r_own == r_sym == claimed_run):
        return None, f"run disagreement own={r_own} sympy={r_sym} claimed={claimed_run}"
    # Alternate-alignment re-sieve: a fresh window around p, swept by
    # DIFFERENT machinery, must reproduce p as a pre-MR survivor.  Different
    # on two axes at once -- the reference engine is numpy `%` rather than
    # the GPU's Barrett arithmetic, and it runs on the 23# wheel rather than
    # production's 29#, so p sits at a different offset in a different
    # period.  (Before unification this only held below the u64 cap, where a
    # 23#-wheel engine happened to be the one available; it now holds at
    # every height.)  Gated end-to-end by G9/G10.
    if p >= P_FLOOR:
        lo = max(P_FLOOR, p - 10**6)
        seen = []
        for chunk in CpuEngine(n_filter, wheel_primes=WHEEL_PRIMES
                                  ).survivors_pre_mr(lo, p + 10**6):
            seen.extend(chunk)
        if p not in seen:
            return None, "alternate-alignment re-sieve did not reproduce p"
    breaker = claimed_run * claimed_run + claimed_run + p
    fac = factor_witness(breaker)
    if fac in (1, breaker) or breaker % fac:
        return None, "no composite witness for the run breaker"
    return {"p": int(p), "run": int(claimed_run),
            "values_prime_x": list(range(claimed_run)),
            "breaker_x": int(claimed_run), "breaker": int(breaker),
            "breaker_factor": int(fac)}, "ok"


# ------------------------------ checkpoint ---------------------------------

def ckpt_key(n, eng):
    """Cursor key, derived from THE ENGINE's actual wheel.

    Never recompute the wheel here independently of the engine.  Doing that
    once let the key claim 31# while the engine ran 29#, so the key check
    passed and next_k -- a count of wheel PERIODS -- was read against a
    period 31x too short.  The engine owns the wheel; everything else asks
    it.
    """
    return CONFIG_KEY.format(n=n, wheel=eng.wheel_primes[-1])


def load_ckpt(n, eng):
    return _ckpt.load(CKPT, ckpt_key(n, eng), warn=lambda m: log("WARN", m))


def save_ckpt(c):
    _ckpt.save(CKPT, c)


def fresh_ckpt(n, eng):
    # One engine spans the whole range, so a fresh campaign starts at zero:
    # there is no cap to start above and no seam to re-cover.
    return {"key": ckpt_key(n, eng), "M": int(eng.M), "next_k": 0,
            "canaries_done": False, "survivors": 0, "events": [],
            "best_near": 0, "best_near_p": 0, "near_counts": {}, "hits": 0,
            "wall_s": 0.0, "started": time.time()}


def check_cursor(c, eng):
    """Refuse a cursor whose period does not match the engine's.

    The key already pins the wheel, but this is the assertion that does not
    depend on anyone having derived the key correctly: next_k counts periods
    of c["M"], so if that disagrees with the engine's M the position is
    wrong by their ratio -- silently, and in the direction that can put a
    GAP in the coverage claim.  Cheap, and it turns the worst class of bug
    here into a refusal to start.
    """
    have, want = int(c.get("M", 0)), int(eng.M)
    if have != want:
        raise CorruptEngineError(
            "cursor period mismatch: next_k=%d counts periods of M=%d, but "
            "this engine's wheel gives M=%d (ratio %.4g).  Resuming would "
            "misplace the frontier by that factor.  Convert the cursor "
            "deliberately (see RESULTS.md on the 31# conversion) rather "
            "than resuming." % (c.get("next_k", -1), have, want,
                                (want / have) if have else float("inf")))


def refuse_unreadable_cursor(eng, fresh):
    """A cursor FILE this configuration cannot read must STOP the run.

    huntlib ignores a checkpoint whose key does not match, which is right --
    reinterpreting one is the bug that put a 31x error in the frontier once.
    But "ignore" then falls straight through to a fresh cursor at zero, and a
    campaign that silently restarts at p=0 after a wheel change destroys the
    frontier instead of misreading it.  Both directions are wrong, and
    check_cursor only guards one of them: it is never reached, because there
    is nothing left to check.

    So: an existing cursor whose key does not match is a refusal.  --fresh
    says "yes, start over" and --migrate-cursor says "convert it"; there is
    no path where a wheel change quietly rewinds the campaign.
    """
    if fresh or not os.path.exists(CKPT):
        return
    with open(CKPT) as f:
        old = json.load(f)
    raise CorruptEngineError(
        "a campaign cursor exists but this configuration cannot read it.\n"
        "        stored key : %s\n"
        "        wanted key : %s\n"
        "        stored     : next_k=%s of M=%s, i.e. p ~ %.4e\n"
        "  Starting anyway would begin a FRESH sweep at p=0 and abandon that "
        "frontier.  Convert the cursor with --migrate-cursor, or say --fresh "
        "to discard it deliberately."
        % (old.get("key"), ckpt_key(eng.n, eng), old.get("next_k"),
           old.get("M"), int(old.get("next_k", 0)) * int(old.get("M", 0))))


def migrate_cursor(eng, apply=False):
    """Re-denominate the campaign cursor in THIS engine's wheel period.

    next_k counts periods of the cursor's own M.  A wheel change multiplies
    the period by an exact integer, so the position is preserved by

        new_next_k = floor(old_next_k * old_M / new_M)

    FLOOR, deliberately.  With a longer period the seam then OVERLAPS by up
    to one new period rather than leaving a gap: coverage may be swept twice,
    it may never be claimed and swept zero times.  That is the same
    convention the 29# -> 31# conversion used, and the reason is that this
    project's whole claim is exhaustiveness.

    Everything the wheel decides is re-derived, not carried over: the key,
    M, and `canaries_done` -- the prelude ran on a different wheel, so it has
    established nothing about this one and must run again.  The cumulative
    counters are kept; the overlap re-sweeps at most one period (7.4e12 of
    p-line, ~3 expected survivors), so they drift by that and no more.
    """
    with open(CKPT) as f:
        c = json.load(f)
    old_m, old_k = int(c["M"]), int(c["next_k"])
    new_m = int(eng.M)
    if old_m == new_m:
        log("STAGE", "cursor already denominated in M=%d; nothing to do"
                     % new_m)
        return c
    p_old = old_k * old_m
    new_k = p_old // new_m
    log("STAGE", "cursor migration: period M %d -> %d (ratio %.6g)"
                 % (old_m, new_m, new_m / old_m))
    log("STAGE", "  from next_k=%d  (p = %.6e)" % (old_k, p_old))
    log("STAGE", "  to   next_k=%d  (p = %.6e)" % (new_k, new_k * new_m))
    log("STAGE", "  seam overlaps by %.4e of p-line (floor, never a gap)"
                 % (p_old - new_k * new_m))
    if not apply:
        log("WARN", "dry run: pass --migrate-cursor to write it")
        return c
    shutil.copyfile(CKPT, CKPT + ".pre-migration")
    c["key"], c["M"], c["next_k"] = ckpt_key(eng.n, eng), new_m, new_k
    c["canaries_done"] = False       # the prelude ran on the old wheel
    save_ckpt(c)
    log("STAGE", "written; backup at %s.pre-migration" % CKPT)
    return c


# ------------------------------- canaries ----------------------------------

def low_pass(n):
    """EXHAUSTIVE oracle sweep of [2, P_FLOOR): every run >= n classified.

    This is what makes the engine's least-claims self-contained: the
    sieve floor is covered by the slow trustworthy oracle, from scratch.
    """
    hits = []
    for p in range(2, P_FLOOR):
        r = oracle_run(p)
        if r >= n:
            hits.append((p, r))
    for p, r_exp in EXPECTED_KNOWN.items():
        if oracle_run(p) != r_exp:
            raise CorruptEngineError(f"expected-known table wrong at {p}")
    return hits


def canary_prelude(engine_factory, n):
    """Every canary, at every scale, through the production engine.

    One engine spans the range, so one prelude covers it: a(14)/a(15) are
    rediscovered as the FIRST run-exactly-n prime above the floor (a
    least-claim drill, not just a hit), and a(18) plus the
    Waldvogel-Leikauf run-21 value are rediscovered in local windows --
    the first tying this engine to the phase-1 record below the old u64
    cap, the second landing above it.  Spanning both sides of 2^64 in one
    prelude is the point: that boundary is no longer special, and the
    prelude is what proves it before production runs.
    """
    for cn in (14, 15):
        target = KNOWN[cn]
        t0 = time.time()
        hits = engine_factory(cn).hunt(P_FLOOR, target + 10**6)
        firsts = [p for p, r in hits if r == cn]
        if not firsts or firsts[0] != target:
            raise CorruptEngineError(
                f"CANARY ALARM: n={cn} rediscovery failed (got {firsts[:1]},"
                f" expected {target})")
        log("CANARY-GOLD", f"a({cn}) = {target} rediscovered end-to-end "
            f"({time.time()-t0:.0f}s)")
    eng = engine_factory(n)
    for target, run in ((CAMPAIGN_FOUND[18], 18), (A21_UPPER, 21)):
        t0 = time.time()
        hits = eng.hunt(target - 5 * 10**9, target + 10**6)
        if (target, run) not in hits:
            raise CorruptEngineError(
                f"CANARY ALARM: rediscovery of run-{run} value "
                f"{target} failed (got {hits})")
        log("CANARY-GOLD", f"run-{run} value {target} rediscovered "
            f"end-to-end ({time.time()-t0:.0f}s)")


# ------------------------------- the hunt ----------------------------------

def record_discovery(ev, label):
    os.makedirs("evidence", exist_ok=True)
    with open(os.path.join("evidence", f"euler_hit_run{ev['run']}_p{ev['p']}.json"), "w") as f:
        json.dump(ev, f, indent=1)
    allrec = []
    if os.path.exists(DISC):
        with open(DISC) as f:
            allrec = json.load(f)
    allrec.append({**ev, "label": label, "t": time.time()})
    with open(DISC, "w") as f:
        json.dump(allrec, f, indent=1)


def hunt(args):
    n = args.n
    if args.engine == "cpu":
        Eng = CpuEngine
        log("WARN", "the numpy reference engine is for verification, not "
                    "hunting -- production legs need the GPU")
    else:
        from euler_gpu import GpuEngine as Eng

    def make_engine(m):
        # no wheel override: the engine picks the largest wheel that fits,
        # and is then the single source of truth for the period the cursor
        # is denominated in
        return Eng(m)

    eng = make_engine(n)
    if getattr(args, "migrate_cursor", False):
        if not os.path.exists(CKPT):
            log("WARN", "no cursor to migrate")
            return 0
        migrate_cursor(eng, apply=True)
        return 0
    c = None if args.fresh else load_ckpt(n, eng)
    if c is None:
        refuse_unreadable_cursor(eng, args.fresh)   # raises, or there is
        c = fresh_ckpt(n, eng)                      # genuinely no cursor
    check_cursor(c, eng)

    if not c["canaries_done"]:
        log("STAGE", "canary prelude: oracle low-pass + a(14)/a(15)/a(18) "
                     "+ run-21 rediscovery via the production engine")
        for p, r in low_pass(n):
            ev, msg = three_way_verify(p, r, n)
            if ev is None:
                raise CorruptEngineError(f"low-range verify failed at {p}: {msg}")
            if p in EXPECTED_KNOWN and EXPECTED_KNOWN[p] == r:
                log("CANARY-GOLD", f"p={p} run={r} (Euler!) verified 3-way -- "
                    "positive control of the full discovery protocol")
            else:
                record_discovery(ev, "UNEXPECTED-LOW")
                log("DISCOVERY", f"UNEXPECTED low-range run>= {n} at {p}")
        canary_prelude(make_engine, n)
        c["canaries_done"] = True
        save_ckpt(c)

    target_run = FRONTIER_RUN + 1
    logc_next = None
    try:
        from euler_model import expected_count
        with open("model_results.json") as fh:
            logc_next = json.load(fh)["singular"][str(target_run)]["logC"]
    except Exception:
        expected_count = None
    cap = int(args.to)
    M = eng.M
    k_cap = cap // M + 1
    # periods per checkpoint segment, DERIVED from the engine's wheel: the
    # segment bounds what a kill costs, and that is p-line, not periods
    seg = max(1, int(args.seg_span) // M)
    t_last, p_last = time.time(), c["next_k"] * M
    log("STAGE", f"production: n={n} filter, from p ~ {c['next_k']*M:.3e} "
        f"to {cap:.3e} ({args.engine})")
    try:
        while c["next_k"] < k_cap:
            k0 = c["next_k"]
            k1 = min(k0 + seg, k_cap)
            lo = max(P_FLOOR, k0 * M)
            hi = min(cap, k1 * M)
            if lo >= hi:
                c["next_k"] = k1
                continue
            t0 = time.time()
            surv = eng.survivors_pre_mr(lo, hi)
            if isinstance(surv, list):               # GPU: one sorted list
                plist = surv
            else:                                    # CPU reference: chunks
                plist = sorted(p for ch in surv for p in ch)
            for p in plist:
                c["survivors"] += 1
                r = mr_run_length(p, cap=100)
                if r >= n:
                    ev, msg = three_way_verify(p, r, n)
                    if ev is None:
                        raise CorruptEngineError(f"verify failed at {p}: {msg}")
                    prior = []
                    if os.path.exists(DISC):
                        with open(DISC) as fh:
                            prior = [d for d in json.load(fh)
                                     if d["run"] == r and d["p"] < p]
                    if p == A21_UPPER:
                        # known literature value: in-flight canary, never
                        # a discovery, never a stop trigger
                        record_discovery(ev, "Waldvogel-Leikauf run-21 value"
                                             " -- in-flight canary (known)")
                        c["a21_canary"] = True
                        log("CANARY-GOLD", f"run-21 value {p} rediscovered "
                            "in-flight (literature value; not a discovery)")
                    elif r > FRONTIER_RUN:
                        if prior:
                            label = "run-%d #%d (a(%d) already settled at %d)" % (
                                r, len(prior) + 1, r, min(d["p"] for d in prior))
                        else:
                            label = "A164926(%d) CANDIDATE" % r
                        record_discovery(ev, label)
                        log("DISCOVERY", "=" * 60)
                        log("DISCOVERY", f"run == {r} at p = {p}  ({label})")
                        log("DISCOVERY", f"breaker x={r}: factor {ev['breaker_factor']}")
                        log("DISCOVERY", "verified 3-way; evidence JSON written")
                        log("DISCOVERY", "=" * 60)
                        c["hits"] = c.get("hits", 0) + 1
                        if args.stop_on_discovery:
                            save_ckpt(c)
                            log("STAGE", "frontier-extending discovery "
                                "confirmed -- stopping (--stop-on-discovery)")
                            return 0
                    else:
                        # census-grade repeat of a settled run length:
                        # fully verified + evidenced, but not a discovery
                        label = "run-%d census #%d (a(%d) settled at %d)" % (
                            r, len(prior) + 1, r,
                            CAMPAIGN_FOUND.get(r, min([d["p"] for d in prior],
                                                      default=0)))
                        record_discovery(ev, label)
                        nc = c.setdefault("near_counts", {})
                        nc[str(r)] = nc.get(str(r), 0) + 1
                        tail = ("  -- ONE value short of a(%d)!" % target_run
                                if r == FRONTIER_RUN else "")
                        log("NEAR", f"run {r} at p = {p}  ({label}; "
                            f"verified 3-way, evidence written){tail}")
                        if r > c["best_near"]:
                            c["best_near"], c["best_near_p"] = r, p
                elif r >= 13:
                    nc = c.setdefault("near_counts", {})
                    nc[str(r)] = nc.get(str(r), 0) + 1
                    with open(os.path.join("evidence", "euler_nearmiss.jsonl"), "a") as fh:
                        fh.write(json.dumps({"p": int(p), "run": int(r),
                                             "t": time.time()}) + "\n")
                    log("NEAR", f"run {r} at p = {p}  "
                        f"(run-{r} #{nc[str(r)]} of the campaign)")
                    if r > c["best_near"]:
                        c["best_near"], c["best_near_p"] = r, p
            c["next_k"] = k1
            c["wall_s"] += time.time() - t0
            now = time.time()
            if now - t_last >= args.heartbeat:
                pos = k1 * M
                rate = (pos - p_last) / max(now - t_last, 1e-9)
                pct = 100.0 * pos / cap
                nc = c.get("near_counts", {})
                nears = "/".join(str(nc.get(str(r), 0))
                                 for r in range(13, FRONTIER_RUN + 1))
                odds = ""
                if logc_next is not None and expected_count is not None:
                    En = expected_count(target_run, pos, logc_next)
                    haz = math.exp(logc_next) / math.log(pos) ** target_run \
                          * rate * 3600.0
                    odds = (f"P(a{target_run} by now) {1.0-math.exp(-En):.0%} "
                            f"(+{haz:.1%}/h)  ")
                eta_s = (cap - pos) / max(rate, 1)
                finish = time.strftime("%a %H:%M",
                                       time.localtime(now + eta_s))
                log("STATUS", f"p {pos:.3e}  {pct:.2f}%  "
                    f"{rate/1e14:.2f}e14 p/s  surv {c['survivors']:,}  "
                    f"near13-{FRONTIER_RUN} {nears}  "
                    f"run{target_run}+ {c.get('hits', 0)}  "
                    f"{odds}ETA {eta_s/3600.0:.1f}h ({finish})")
                t_last, p_last = now, pos
                save_ckpt(c)
            dec = 10 ** int(math.log10(max(k1 * M, 10)))
            if k0 * M < dec <= k1 * M:
                nc = c.get("near_counts", {})
                nears = "/".join(str(nc.get(str(r), 0))
                                 for r in range(13, FRONTIER_RUN + 1))
                log("MILESTONE", f"passed p = {dec:.0e}  survivors "
                    f"{c['survivors']:,}  near13-{FRONTIER_RUN} {nears}  "
                    f"run{target_run}+ hits {c.get('hits', 0)}")
        save_ckpt(c)
        log("STAGE", f"cap {cap:.3e} reached; survivors {c['survivors']}; "
            f"best near-miss run {c['best_near']} at {c['best_near_p']}")
        return 0
    except KeyboardInterrupt:
        save_ckpt(c)
        log("STAGE", "interrupted -- checkpoint saved; rerun to resume")
        return 0


# ------------------------------- selftest ----------------------------------

def selftest():
    import euler_reference, euler_model, euler_search, euler_gpu
    ok = euler_reference.selftest()
    ok = euler_model.main() and ok
    ok = euler_search.selftest() and ok
    ok = euler_gpu.selftest() and ok

    # resume drill: 2-segment run == uninterrupted run (state parity).  The
    # engine-level version of this lives in G13, which sweeps split points on
    # word/thread/launch boundaries; this one is the campaign-level check,
    # low in the range where the oracle also has jurisdiction.
    from euler_gpu import GpuEngine

    def resume_drill(label, eng, lo, cut, hi, min_surv):
        """Split stream == unsplit stream, on a POPULATED window.

        Both halves of that sentence are load-bearing, and the second one
        rotted quietly.  This drill used to ask n=13 for [1e5, 2e9), which
        holds exactly ZERO pre-MR survivors -- a(13) is at 8.776e9, just
        outside it -- on every wheel this project has ever run, including the
        one it was written against.  So it compared two empty lists, which
        CONVENTIONS says does not count, and its own `len(a) < 1` guard had
        been failing rather than passing vacuously.  The window is now
        populated and `min_surv` is asserted separately from the comparison,
        so the next time one goes empty it says so instead of reporting a
        mismatch of nothing against nothing.
        """
        whole = eng.survivors_pre_mr(lo, hi)
        split = sorted(eng.survivors_pre_mr(lo, cut)
                       + eng.survivors_pre_mr(cut, hi))
        if len(whole) < min_surv:
            print("FAIL %s: window under-populated (%d survivors, want >= %d)"
                  " -- the comparison would prove nothing"
                  % (label, len(whole), min_surv))
            return False
        if whole != split:
            print("FAIL %s: split != whole (%d vs %d)"
                  % (label, len(split), len(whole)))
            return False
        print("PASS %s: split stream == whole stream (%d survivors)"
              % (label, len(whole)))
        return True

    eng13 = GpuEngine(13)
    ok = resume_drill("resume drill (n=9, split at 1e8)", GpuEngine(9),
                      P_FLOOR, 10**8, 2 * 10**8, 5) and ok

    # planted-discovery drill: a genuine run-13 survivor pushed through the
    # n=17 protocol MUST be rejected
    hits = GpuEngine(13).hunt(P_FLOOR, KNOWN[13] + 1000)
    p13 = [p for p, r in hits if r == 13][0]
    ev, msg = three_way_verify(p13, 17, 17)
    if ev is not None:
        print("FAIL planted drill: fake run-17 claim ACCEPTED")
        ok = False
    else:
        print(f"PASS planted drill: fake run-17 claim rejected ({msg})")

    # positive control: Euler's 41 through the full protocol
    ev, msg = three_way_verify(41, 40, 17)
    if ev is None:
        print(f"FAIL positive control: 41/run-40 rejected ({msg})")
        ok = False
    else:
        print("PASS positive control: 41 (run 40) verified 3-way")

    # high-range resume drill: the same property 11 orders of magnitude up,
    # where p no longer fits a machine word -- and at n=13, which is where
    # the campaign-level drills meet the production 37# wheel and its
    # device-generated offset chunks
    ok = resume_drill("high-range resume drill (n=13, p ~ 3e19)", eng13,
                      3 * 10**19, 3 * 10**19 + 47 * 10**9,
                      3 * 10**19 + 10**11, 3) and ok

    # positive control at a height where p exceeds 2^64: the
    # Waldvogel-Leikauf value through the full protocol, which also
    # exercises the big-int leg of the alternate-alignment re-sieve...
    ev, msg = three_way_verify(A21_UPPER, 21, 17)
    if ev is None:
        print(f"FAIL positive control: A21 upper rejected ({msg})")
        ok = False
    else:
        print("PASS positive control: run-21 value verified 3-way at 2.3e20")
    # ...and a planted FALSE claim about it must be rejected
    ev, msg = three_way_verify(A21_UPPER, 22, 17)
    if ev is not None:
        print("FAIL planted drill: fake run-22 claim ACCEPTED")
        ok = False
    else:
        print(f"PASS planted drill: fake run-22 claim rejected ({msg})")
    print("SELFTEST " + ("ALL GREEN" if ok else "FAILED"))
    return ok


def status():
    any_ckpt = False
    for path in (CKPT,):
        if not os.path.exists(path):
            continue
        any_ckpt = True
        with open(path) as f:
            c = json.load(f)
        print(f"key       : {c['key']}")
        print(f"period M  : {c['M']}")
        print(f"position  : p ~ {c['next_k']*c['M']:.4e}  "
              f"(next_k = {c['next_k']:,})")
        print(f"survivors : {c['survivors']}")
        print(f"best near : run {c['best_near']} at p = {c['best_near_p']}")
        print(f"wall      : {c['wall_s']:.0f}s")
    if not any_ckpt:
        print("no checkpoint")
        return
    if os.path.exists(DISC):
        with open(DISC) as f:
            for d in json.load(f):
                print(f"DISCOVERY : run {d['run']} at p = {d['p']}  [{d['label']}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--stop-on-discovery", action="store_true",
                    help="halt cleanly once the discovery protocol confirms "
                         "a frontier-extending find (run > %d); known-value "
                         "rediscoveries and census repeats never trigger it"
                         % FRONTIER_RUN)
    ap.add_argument("--n", type=int, default=17)
    ap.add_argument("--to", type=float, default=0.0,
                    help="depth cap (default %.0e, the current leg; the hard "
                         "ceiling is %.0e)" % (DEFAULT_TO, P_CEIL))
    ap.add_argument("--engine", choices=["gpu", "cpu"], default="gpu",
                    help="gpu (default) is the production engine and spans "
                         "the whole range; cpu is the numpy reference, for "
                         "verification only")
    ap.add_argument("--seg-span", type=float, default=float(SEG_SPAN),
                    help="p-line per checkpoint segment (default %.2e); the "
                         "period count is derived from the engine's wheel"
                         % SEG_SPAN)
    ap.add_argument("--migrate-cursor", action="store_true",
                    help="re-denominate the campaign cursor in this engine's "
                         "wheel period and exit; see migrate_cursor()")
    ap.add_argument("--heartbeat", type=float, default=30.0)
    args = ap.parse_args()
    if args.to <= 0:
        args.to = float(DEFAULT_TO)
    if args.to > P_CEIL:
        print(f"cap clamped to the enforced ceiling {P_CEIL:.3e}")
        args.to = float(P_CEIL)
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    if args.status:
        status()
        sys.exit(0)
    try:
        sys.exit(hunt(args))
    except CorruptEngineError as e:
        log("ALARM", str(e))
        sys.exit(2)


if __name__ == "__main__":
    main()
