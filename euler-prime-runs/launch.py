# launch.py -- THE HUNT for A164926 a(17)-a(20): checkpointed, resumable,
# canary-alarmed, no-false-discovery.  Follows the repo-wide project
# conventions (see ../CONVENTIONS.md).
#
#   python launch.py              # phase-1 hunt (n=17 filter, u64 cap; done)
#   python launch.py --engine gpu128 --stop-on-discovery
#                                 # phase-2 hunt beyond the u64 cap (a(19));
#                                 # halts after a frontier-extending find
#   python launch.py --selftest   # full gate battery + resume + planted drills
#   python launch.py --status     # scoreboard from checkpoints (both phases)
#   python launch.py --to 1e18 --engine gpu --fresh
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
from euler_search import (CpuEngine, CpuEngine128, P128_CEIL, P_FLOOR,
                          WHEEL_PRIMES_29, mr_is_prime_u64, mr_run_length)

CKPT = "ladder_checkpoint.json"
CKPT128 = "ladder128_checkpoint.json"
DISC = os.path.join("evidence", "euler_discoveries.json")
U64_CAP = 18_000_000_000_000_000_000          # < 2^64 - 272, u64-safe
SEG_PERIODS = 131_072                          # 29-wheel periods per checkpoint segment
CONFIG_KEY = "euler-prime-runs/v2/n={n}/wheel=29#/Q1=1024/Q2=65536"
CONFIG_KEY128 = "euler-prime-runs/v3-128/n={n}/wheel=29#/Q1=1024/Q2=65536/ceil=1e24"

EXPECTED_KNOWN = {41: 40}                      # low-range positive control

# Verified finds of THIS campaign (phase 1, evidence/ + RESULTS.md).
# The discovery frontier: only a run strictly beyond every previously
# recorded value counts as a discovery (repo convention; rediscoveries
# and census-grade repeats of settled run lengths never trigger
# --stop-on-discovery).
CAMPAIGN_FOUND = {17: 348_284_517_256_411_907,
                  18: 8_461_068_614_861_832_371}
FRONTIER_RUN = max(CAMPAIGN_FOUND)             # discovery = run > FRONTIER_RUN
P2_DEFAULT_TO = 320 * 10**18                   # 3.2e20: past the E=1 depth for
                                               # run>=19 (3.1e20) and the
                                               # Waldvogel-Leikauf zone


class CorruptEngineError(RuntimeError):
    pass


# ------------------------- verification (three-way) -------------------------

def three_way_verify(p, claimed_run, n_filter):
    """Independent confirmation that run(p) == claimed_run exactly."""
    r_own = mr_run_length(p, cap=claimed_run + 40)
    r_sym = oracle_run(p, cap=claimed_run + 40)
    if not (r_own == r_sym == claimed_run):
        return None, f"run disagreement own={r_own} sympy={r_sym} claimed={claimed_run}"
    # alternate-alignment re-sieve: a fresh CPU engine window around p
    # must reproduce p as a pre-MR survivor (only meaningful above floor).
    # Above the u64 cap the exact-int CPU-128 engine takes over (gated
    # G9/G10 against the u64 engine and direct trial division).
    if p >= P_FLOOR:
        lo = max(P_FLOOR, p - 10**6)
        seen = []
        if p + 10**6 < U64_CAP:
            for arr in CpuEngine(n_filter).survivors_pre_mr(lo, p + 10**6):
                seen.extend(int(v) for v in arr.tolist())
        else:
            for chunk in CpuEngine128(n_filter).survivors_pre_mr(lo, p + 10**6):
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

def ckpt_key(n, is128=False):
    return (CONFIG_KEY128 if is128 else CONFIG_KEY).format(n=n)


def ckpt_file(is128=False):
    return CKPT128 if is128 else CKPT


def load_ckpt(n, is128=False):
    return _ckpt.load(ckpt_file(is128), ckpt_key(n, is128),
                      warn=lambda m: log("WARN", m))


def save_ckpt(c, is128=False):
    _ckpt.save(ckpt_file(is128), c)


def fresh_ckpt(n, is128=False):
    # phase 2 starts at the last u64-covered period boundary: the sliver
    # [ (U64_CAP//M)*M, U64_CAP ) is re-covered on purpose (seam overlap,
    # no gap risk); phase 1 owns everything below.
    start_k = (U64_CAP // 6469693230) if is128 else 0
    return {"key": ckpt_key(n, is128), "M": 6469693230, "next_k": start_k,
            "canaries_done": False, "survivors": 0, "events": [],
            "best_near": 0, "best_near_p": 0, "near_counts": {}, "hits": 0,
            "wall_s": 0.0, "started": time.time()}


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
    """n=14 and n=15 mini-hunts MUST rediscover a(14), a(15) exactly."""
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


def canary_prelude128(engine_factory, n):
    """Phase-2 prelude: the production 128 engine must rediscover a(18)
    (below the u64 cap, tying it to the phase-1 record) and the
    Waldvogel-Leikauf run-21 value (above the cap, in the zone it will
    hunt) before any production segment runs."""
    eng = engine_factory(n)
    for target, run in ((CAMPAIGN_FOUND[18], 18), (A21_UPPER, 21)):
        t0 = time.time()
        hits = eng.hunt(target - 5 * 10**9, target + 10**6)
        if (target, run) not in hits:
            raise CorruptEngineError(
                f"CANARY ALARM: 128-path rediscovery of run-{run} value "
                f"{target} failed (got {hits})")
        log("CANARY-GOLD", f"run-{run} value {target} rediscovered "
            f"end-to-end via 128 path ({time.time()-t0:.0f}s)")


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
    is128 = args.engine in ("cpu128", "gpu128")
    if args.engine == "cpu":
        from euler_search import CpuEngine as Eng
    elif args.engine == "cpu128":
        Eng = CpuEngine128
    elif args.engine == "gpu128":
        from euler_gpu import GpuEngine128 as Eng
    else:
        from euler_gpu import GpuEngine as Eng

    c = None if args.fresh else load_ckpt(n, is128)
    if c is None:
        c = fresh_ckpt(n, is128)

    def make_engine(m):
        return Eng(m, wheel_primes=WHEEL_PRIMES_29)

    if not c["canaries_done"]:
        if is128:
            log("STAGE", "canary prelude (128): a(18) + Waldvogel-Leikauf "
                "run-21 rediscovery via the production engine")
            canary_prelude128(make_engine, n)
        else:
            log("STAGE", "canary prelude: oracle low-pass + a(14)/a(15) rediscovery")
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
        save_ckpt(c, is128)

    eng = make_engine(n)
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
    seg = args.seg_periods
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
            if isinstance(surv, np.ndarray):         # u64 GPU: one array
                plist = np.sort(surv).tolist()
            elif isinstance(surv, list):             # 128 GPU: sorted ints
                plist = surv
            else:                                    # CPU engines yield chunks
                chunks = list(surv)
                if chunks and isinstance(chunks[0], np.ndarray):
                    plist = np.sort(np.concatenate(chunks)).tolist()
                else:
                    plist = sorted(p for ch in chunks for p in ch)
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
                            save_ckpt(c, is128)
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
                        log("NEAR", f"run {r} at p = {p}  ({label}; "
                            "verified 3-way, evidence written)")
                        if r > c["best_near"]:
                            c["best_near"], c["best_near_p"] = r, p
                elif r >= 13:
                    nc = c.setdefault("near_counts", {})
                    nc[str(r)] = nc.get(str(r), 0) + 1
                    with open(os.path.join("evidence", "euler_nearmiss.jsonl"), "a") as fh:
                        fh.write(json.dumps({"p": int(p), "run": int(r),
                                             "t": time.time()}) + "\n")
                    tail = "  -- ONE value short!" if r == n - 1 else ""
                    log("NEAR", f"run {r} at p = {p}  "
                        f"(run-{r} #{nc[str(r)]} of the campaign){tail}")
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
                save_ckpt(c, is128)
            dec = 10 ** int(math.log10(max(k1 * M, 10)))
            if k0 * M < dec <= k1 * M:
                nc = c.get("near_counts", {})
                nears = "/".join(str(nc.get(str(r), 0))
                                 for r in range(13, FRONTIER_RUN + 1))
                log("MILESTONE", f"passed p = {dec:.0e}  survivors "
                    f"{c['survivors']:,}  near13-{FRONTIER_RUN} {nears}  "
                    f"run{target_run}+ hits {c.get('hits', 0)}")
        save_ckpt(c, is128)
        log("STAGE", f"cap {cap:.3e} reached; survivors {c['survivors']}; "
            f"best near-miss run {c['best_near']} at {c['best_near_p']}")
        return 0
    except KeyboardInterrupt:
        save_ckpt(c, is128)
        log("STAGE", "interrupted -- checkpoint saved; rerun to resume")
        return 0


# ------------------------------- selftest ----------------------------------

def selftest():
    import euler_reference, euler_model, euler_search, euler_gpu
    ok = euler_reference.selftest()
    ok = euler_model.main() and ok
    ok = euler_search.selftest() and ok
    ok = euler_gpu.selftest() and ok

    # resume drill: 2-segment run == uninterrupted run (state parity)
    from euler_gpu import GpuEngine
    n = 13
    eng = GpuEngine(n)
    a = eng.survivors_pre_mr(P_FLOOR, 2 * 10**9)
    b1 = eng.survivors_pre_mr(P_FLOOR, 10**9)
    b2 = eng.survivors_pre_mr(10**9, 2 * 10**9)
    b = np.sort(np.concatenate([b1, b2]))
    if not np.array_equal(a, b):
        print("FAIL resume drill: split != whole")
        ok = False
    else:
        print("PASS resume drill: split-at-1e9 stream == whole stream")

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

    # 128 resume drill: split window above the u64 cap == whole window
    from euler_gpu import GpuEngine128
    e128 = GpuEngine128(13)
    lo128, mid128, hi128 = 3 * 10**19, 3 * 10**19 + 47 * 10**9, 3 * 10**19 + 10**11
    a = e128.survivors_pre_mr(lo128, hi128)
    b = sorted(e128.survivors_pre_mr(lo128, mid128)
               + e128.survivors_pre_mr(mid128, hi128))
    if a != b or len(a) < 1:
        print(f"FAIL 128 resume drill: split != whole ({len(a)} vs {len(b)})")
        ok = False
    else:
        print(f"PASS 128 resume drill: split-above-cap stream == whole "
              f"({len(a)} survivors)")

    # 128 positive control: the Waldvogel-Leikauf value through the full
    # protocol (exercises the >u64 re-sieve leg of three_way_verify)...
    ev, msg = three_way_verify(A21_UPPER, 21, 17)
    if ev is None:
        print(f"FAIL 128 positive control: A21 upper rejected ({msg})")
        ok = False
    else:
        print("PASS 128 positive control: run-21 value verified 3-way above cap")
    # ...and a planted FALSE claim about it must be rejected
    ev, msg = three_way_verify(A21_UPPER, 22, 17)
    if ev is not None:
        print("FAIL 128 planted drill: fake run-22 claim ACCEPTED")
        ok = False
    else:
        print(f"PASS 128 planted drill: fake run-22 claim rejected ({msg})")
    print("SELFTEST " + ("ALL GREEN" if ok else "FAILED"))
    return ok


def status():
    any_ckpt = False
    for path in (CKPT, CKPT128):
        if not os.path.exists(path):
            continue
        any_ckpt = True
        with open(path) as f:
            c = json.load(f)
        print(f"key       : {c['key']}")
        print(f"position  : p ~ {c['next_k']*c.get('M', 6469693230):.4e}")
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
                    help="depth cap (default: u64 cap, or 3.2e20 for the "
                         "128 engines)")
    ap.add_argument("--engine",
                    choices=["auto", "cpu", "gpu", "cpu128", "gpu128"],
                    default="auto")
    ap.add_argument("--seg-periods", type=int, default=SEG_PERIODS)
    ap.add_argument("--heartbeat", type=float, default=30.0)
    args = ap.parse_args()
    if args.engine == "auto":
        try:
            import cupy  # noqa
            args.engine = "gpu"
        except Exception:
            args.engine = "cpu"
    if args.engine in ("cpu128", "gpu128"):
        if args.to <= 0:
            args.to = float(P2_DEFAULT_TO)
        if args.to > P128_CEIL:
            print(f"cap clamped to 128-path ceiling {P128_CEIL:.3e}")
            args.to = float(P128_CEIL)
    else:
        if args.to <= 0:
            args.to = float(U64_CAP)
        if args.to > U64_CAP:
            print(f"cap clamped to u64-safe {U64_CAP:.3e} "
                  "(use --engine gpu128 to go beyond)")
            args.to = float(U64_CAP)
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
