# launch.py -- THE HUNT for A164926 a(17)-a(20): checkpointed, resumable,
# canary-alarmed, no-false-discovery.  Follows the repo-wide project
# conventions (see ../CONVENTIONS.md).
#
#   python launch.py              # the hunt (n=17 filter, to U64 cap, resume)
#   python launch.py --selftest   # full gate battery + resume + planted drills
#   python launch.py --status     # scoreboard from checkpoint
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

from euler_reference import KNOWN, OPEN_N, run_length as oracle_run
from euler_search import (CpuEngine, P_FLOOR, WHEEL_PRIMES_29,
                          mr_is_prime_u64, mr_run_length)

CKPT = "ladder_checkpoint.json"
DISC = os.path.join("evidence", "euler_discoveries.json")
U64_CAP = 18_000_000_000_000_000_000          # < 2^64 - 272, u64-safe
SEG_PERIODS = 131_072                          # 29-wheel periods per checkpoint segment
CONFIG_KEY = "euler-prime-runs/v2/n={n}/wheel=29#/Q1=1024/Q2=65536"

EXPECTED_KNOWN = {41: 40}                      # low-range positive control


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
    # must reproduce p as a pre-MR survivor (only meaningful above floor)
    if p >= P_FLOOR:
        eng = CpuEngine(n_filter)
        lo = max(P_FLOOR, p - 10**6)
        seen = []
        for arr in eng.survivors_pre_mr(lo, p + 10**6):
            seen.extend(arr.tolist())
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

def ckpt_key(n):
    return CONFIG_KEY.format(n=n)


def load_ckpt(n):
    return _ckpt.load(CKPT, ckpt_key(n), warn=lambda m: log("WARN", m))


def save_ckpt(c):
    _ckpt.save(CKPT, c)


def fresh_ckpt(n):
    return {"key": ckpt_key(n), "M": 6469693230, "next_k": 0, "canaries_done": False,
            "survivors": 0, "events": [], "best_near": 0, "best_near_p": 0,
            "near_counts": {}, "hits": 0, "wall_s": 0.0, "started": time.time()}


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
        from euler_search import CpuEngine as Eng
    else:
        from euler_gpu import GpuEngine as Eng

    c = None if args.fresh else load_ckpt(n)
    if c is None:
        c = fresh_ckpt(n)

    def make_engine(m):
        return Eng(m, wheel_primes=WHEEL_PRIMES_29)

    if not c["canaries_done"]:
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
        save_ckpt(c)

    eng = make_engine(n)
    logc_next = None
    try:
        from euler_model import expected_count
        with open("model_results.json") as fh:
            logc_next = json.load(fh)["singular"][str(n + 1)]["logC"]
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
            if not isinstance(surv, np.ndarray):     # CPU engine yields chunks
                chunks = list(surv)
                surv = (np.concatenate(chunks) if chunks
                        else np.array([], dtype=np.uint64))
            for p in np.sort(surv).tolist():
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
                    if args.stop_on_find:
                        save_ckpt(c)
                        return 0
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
                nears = "/".join(str(nc.get(str(r), 0)) for r in range(13, n))
                odds = ""
                if logc_next is not None and expected_count is not None:
                    En = expected_count(n + 1, pos, logc_next)
                    haz = math.exp(logc_next) / math.log(pos) ** (n + 1)                           * rate * 3600.0
                    odds = (f"P(a{n+1} by now) {1.0-math.exp(-En):.0%} "
                            f"(+{haz:.1%}/h)  ")
                eta_s = (cap - pos) / max(rate, 1)
                finish = time.strftime("%a %H:%M",
                                       time.localtime(now + eta_s))
                log("STATUS", f"p {pos:.3e}  {pct:.2f}%  "
                    f"{rate/1e14:.2f}e14 p/s  surv {c['survivors']:,}  "
                    f"near13-16 {nears}  run17+ {c.get('hits', 0)}  "
                    f"{odds}ETA {eta_s/3600.0:.1f}h ({finish})")
                t_last, p_last = now, pos
                save_ckpt(c)
            dec = 10 ** int(math.log10(max(k1 * M, 10)))
            if k0 * M < dec <= k1 * M:
                nc = c.get("near_counts", {})
                nears = "/".join(str(nc.get(str(r), 0)) for r in range(13, n))
                log("MILESTONE", f"passed p = {dec:.0e}  survivors "
                    f"{c['survivors']:,}  near13-16 {nears}  "
                    f"run17+ hits {c.get('hits', 0)}")
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
    print("SELFTEST " + ("ALL GREEN" if ok else "FAILED"))
    return ok


def status():
    if not os.path.exists(CKPT):
        print("no checkpoint")
        return
    with open(CKPT) as f:
        c = json.load(f)
    print(f"key       : {c['key']}")
    print(f"position  : p ~ {c['next_k']*c.get('M', 6469693230):.4e}")
    print(f"survivors : {c['survivors']}")
    print(f"best near : run {c['best_near']} at p = {c['best_near_p']}")
    print(f"wall      : {c['wall_s']:.0f}s")
    if os.path.exists(DISC):
        with open(DISC) as f:
            for d in json.load(f):
                print(f"DISCOVERY : run {d['run']} at p = {d['p']}  [{d['label']}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--stop-on-find", action="store_true")
    ap.add_argument("--n", type=int, default=17)
    ap.add_argument("--to", type=float, default=float(U64_CAP))
    ap.add_argument("--engine", choices=["auto", "cpu", "gpu"], default="auto")
    ap.add_argument("--seg-periods", type=int, default=SEG_PERIODS)
    ap.add_argument("--heartbeat", type=float, default=30.0)
    args = ap.parse_args()
    if args.to > U64_CAP:
        print(f"cap clamped to u64-safe {U64_CAP:.3e}")
        args.to = float(U64_CAP)
    if args.engine == "auto":
        try:
            import cupy  # noqa
            args.engine = "gpu"
        except Exception:
            args.engine = "cpu"
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
