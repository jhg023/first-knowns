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
  3. a from-scratch re-derivation by different machinery -- the CPU
     engine's residue table (sympy square roots, plain `%`) on a
     DIFFERENT wheel, consulted directly in Python integers so the leg
     holds at any depth (the windowed form of this check once converted
     k to j on the coarser wheel and crashed on the j ceiling 13x before
     the campaign's own);
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

ASCII only.  Ctrl+C is a normal exit: huntlib.shutdown writes the last
SEGMENT BOUNDARY, logs one [STAGE] line and leaves with 130 -- no traceback,
and a second Ctrl+C cannot land inside the checkpoint write.
"""

import argparse
import json
import math
import os
import pathlib as _pathlib
import sys as _sys
import time

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from sympy import factorint                                   # noqa: E402

from huntlib import certificate as _cert                      # noqa: E402
from huntlib import checkpoint as _ckpt                       # noqa: E402
from huntlib import evidence as _evid                         # noqa: E402
from huntlib import pool as _hpool                            # noqa: E402
from huntlib.checkpoint import CheckpointCorrupt              # noqa: E402
from huntlib.gpu import device_report as _device_report       # noqa: E402
from huntlib.gpu import nbytes_of as _nbytes_of               # noqa: E402
from huntlib.hlog import log, census_str, Heartbeat           # noqa: E402
from huntlib import shutdown as _shutdown                     # noqa: E402
from huntlib.primes import (factor_witness, mr_is_prime,      # noqa: E402
                            sprp_base2)
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
# table seeds a FRESH checkpoint, so that a --fresh run does not re-report
# what is already in RESULTS.md as a discovery.)
CAMPAIGN_FOUND = {10: 9_328_409_578_841_430,
                  11: 433_871_469_806_557_860,
                  12: 55_119_263_286_518_170_740,
                  13: 12_094_123_415_384_869_458_600}
FRONTIER_N = max(max(KNOWN), *([max(CAMPAIGN_FOUND)] if CAMPAIGN_FOUND else [0]))

# A campaign runs INDEFINITELY (CONVENTIONS.md): there is no depth at which
# it stops on its own except the enforced ceiling of its wheel, which is
# the last rung.  --to caps a run deliberately; --stop-on-discovery is the
# other deliberate stop.  Progress is read off RUNGS: the model's quartiles
# for every open term (model_results.json, stated before the run), logged
# as [RUNG] when passed, with the next rung and its ETA in every [STATUS].
# next to launch.py, not next to the working directory: a campaign or a
# drill started from elsewhere used to load NO rungs at all and say so
# only by printing a one-rung ladder
MODEL_FILE = str(_pathlib.Path(__file__).with_name("model_results.json"))
# The sieve filter FOLLOWS THE FRONTIER: filter = max(--n, frontier + 1 -
# FILTER_LAG).  With the default lag of 1 the filter equals the frontier,
# so once a(10) lands the sieve runs at n = 10 -- hunting a(11) while still
# seeing run-10 values (one short of a(11): logged) and counting shorter
# runs -- and steps to 11 when a(11) lands, and so on; lag 0 is the fastest
# possible hunt (filter = frontier + 1) and sees nothing below the next
# open term.  A step that widens the wheel re-denominates the cursor with
# FLOOR (an overlap of at most one new period, never a gap).
FILTER_LAG = 0
# LAG 0 IS THE DEFAULT AND IT IS THE WHOLE BALLGAME, so the reason is here.
# The filter sets the wheel: W(n) is the product of the primes <= n + 1,
# because run(k) >= n forces q | k for every prime q <= n + 1 (m ranges over
# a complete set of residues mod q, so some m has m*k^2 == -1, and that
# value exceeds q above the floor).  Hunting a(12) at filter 12 therefore
# sieves the 30030 wheel instead of the 2310 one: 13x fewer candidates per
# unit of k-line AND 13x fewer survivors to classify.  Measured at k = 1e19,
# per 1e18 of k-line: filter 11 costs 142 s of device and 2.98e7 survivors;
# filter 12 costs 14.6 s and 2.30e6.  That is 13x end-to-end, and it is the
# largest single lever in this project.
#
# What lag 1 bought, and what it costs: at lag 1 the sieve runs one step
# behind the frontier, so run-11 values (one short of a(12)) still appear
# and get their [NEAR] line, and shorter runs are still counted in the
# census.  That census is bookkeeping; a(12) is the hunt.  Nothing about
# the least-claim weakens at lag 0 -- a(12) is a multiple of 30030 by the
# argument above, so the coarser wheel skips no candidate that could be
# a(12) -- but the [STATUS] census stops filling in below the frontier and
# [NEAR] lines become rare.  --filter-lag 1 restores the old behaviour at
# 1/13 the speed.
SEG_J = 1 << 42                # j per checkpoint segment: ~1 s of device
#                                time at the v2 rate on any wheel (in k it
#                                is 1e16 at n = 10, 1.3e17 at n = 13; v1 used
#                                a fixed 2e13 k).  --seg-span (in k) overrides.
NEAR_FROM = 7                  # the census floor: runs at or above this are
#                                counted per length (checkpoint `near_counts`,
#                                shown in every [STATUS]); only a run equal
#                                to the frontier is logged individually
CHUNK = 1024                   # survivors per classification task

# ---- sieve depth: the knob that decides HOW MUCH MACHINE the hunt needs --
# The engines' default q2 (65536) is the frozen benchmark depth and it stays
# frozen there so SCORE keeps meaning the same thing across engine
# generations.  The CAMPAIGN is a different question: it pays for both the
# device sieve AND the host classification of whatever survives, and q2 sets
# the ratio between them.
#
# Measured at n = 12, k = 1e19, paired and interleaved (Rule 3), per 1e18 of
# k-line, with the two-pass sprp_run below at its measured 45.7 us:
#
#     q2        device    survivors    host core-s    pool needed    end-to-end
#     65536     14.35 s   2,293,610      104.8 s        8 workers    6.97e16 k/s
#     131072    14.93 s   1,106,720       50.6 s        4 workers    6.70e16 k/s
#     262144    14.78 s     560,509       25.6 s        2 workers    6.77e16 k/s
#     524288    16.07 s     292,700       13.4 s        1 worker     6.22e16 k/s
#
# The device is nearly FLAT from 65536 to 262144 (the extra primes land in
# deep compaction rounds whose populations are already tiny), so four times
# the sieve depth costs the device 3% and takes four times the work off the
# host.  End-to-end the four settings are within 3% of each other -- which
# means the real choice here is not speed, it is HOW MUCH OF THE MACHINE THE
# HUNT ASKS FOR: 8 host processes or 2.
#
# So 262144 is chosen by the rule in CONVENTIONS.md ("Sizing a hunt so it
# leaves the machine usable", step 3): when settings tie on throughput,
# take the one that asks for less machine.  It gives up 3% of the rate and
# asks for a quarter of the CPU, on a program that runs for days on a
# desktop somebody else also has to use.
#
# NOTE for anyone raising this further: the engine's kill-bit table is built
# by a residue walk whose intermediates reach q^2, and it was 32-bit until
# this depth was first tried -- which silently corrupted the sieve above
# q = 2^16 and lost a(7) from the canary.  It is u64 now (exact to
# ladder_gpu.Q2_MAX = 2^31) and g16 gates it at this depth.

Q2_CAMPAIGN = 1 << 18

# Host classification runs in a process pool, one segment behind the GPU:
# the pool classifies segment i-1 while the device sieves segment i.  The
# results are consumed in ASCENDING order in the parent and the cursor only
# advances past a fully classified segment, so the least-claim ordering the
# checkpoint depends on is untouched.  --workers 1 is the old serial path.
#
# SMALL BY DEFAULT, and the reason is measured.  At the settings above the
# pool needs TWO cores to stay a segment ahead of the device; the default is
# 4, which is 2x the requirement (a segment whose survivors run long must
# not become the bottleneck) and leaves the pool at ~38% duty.  Everything
# above that is throughput the device cannot use.
#
# Sized from the requirement, NOT from the core count.  `cpu_count - k` is
# not sizing, it is an appetite: it scales with the machine rather than
# with the work, so it is largest exactly where it is least needed -- on
# this 64-thread host it would have asked for 60 processes to do the work
# of two, each one on Windows a fresh interpreter importing numpy and
# sympy.  A hunt runs for days on somebody's desktop: it may not take the
# whole machine, and here it gains nothing whatever by trying.  The pool is
# also RAMPED rather than stamped (see _prime_pool): interpreters start one
# at a time.  Full procedure: CONVENTIONS.md "Sizing a hunt so it leaves
# the machine usable".
WORKERS_DEFAULT = max(1, min(4, (os.cpu_count() or 2) - 2))
WORKER_RAMP_S = 0.35           # seconds between worker starts (_prime_pool)



class CorruptEngineError(RuntimeError):
    pass


def device_report(eng):
    """One line of machine state at campaign start.

    The reporting itself is huntlib.gpu.device_report (shared: every hunt
    in this repo owes its own log the same line, and all of it is READ-ONLY
    -- a campaign names the machine's levers and never pulls one,
    CONVENTIONS.md step 7).  What stays here is the only part that is this
    engine's business: WHICH of its arrays count as held VRAM.
    """
    held = _nbytes_of(*(getattr(eng, a, None) for a in
                        ("d_bits", "d_pat", "d_primes", "d_magic", "d_wmod")),
                      *[slot.get(key) for slot in getattr(eng, "_slots", [])
                        for key in ("q1", "q2", "cnt", "args")])
    return _device_report(held)


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

    The search itself is huntlib.certificate.witnesses -- the theorem is not
    this project's mathematics, and a second project now depends on it.
    What is this project's is the paragraph above: WHY the base list has to
    be open-ended here.
    """
    return _cert.witnesses(N, sorted(fac), base_cap)


def verify_certificate(N, fac, witnesses):
    """Re-check a certificate from scratch: this is what the gate drills.

    huntlib.certificate.theorem1_verify, which trusts nothing in what it is
    handed -- not the factorization, not that the claimed factors are
    prime, not the witnesses.
    """
    return _cert.theorem1_verify(N, fac, witnesses)


# ------------------------- verification (four-way) --------------------------

# Below this run length nothing is recorded anywhere: the census counts
# start at NEAR_FROM (7), [NEAR] and [DISCOVERY] are higher still, and
# `best_run` is guarded to the same floor in consume().  So a run PROVED
# shorter than this never has to be resolved exactly.
SPRP_EXACT_FROM = 5


def sprp_run(k, cap):
    """The strong-probable-prime run length of k, exact wherever it counts.

    Two passes, and the reason the first one is legitimate is that a strong
    test has an ASYMMETRIC verdict: a failure is a PROOF of compositeness,
    a pass is only evidence.  So a base-2-only chain (one modular
    exponentiation per value instead of seven) yields a rigorous UPPER
    BOUND on the run -- it can stop too late, never too early.  If that
    bound lands below SPRP_EXACT_FROM the true run is below it too, proved,
    and nothing that gets recorded depends on which of 0..4 it is.  If the
    bound reaches SPRP_EXACT_FROM the chain is redone with the full huntlib
    base set and the exact value returned.

    This is not a probabilistic shortcut: every run length this campaign
    writes down still comes from the full base set.  It costs 1.34 modular
    exponentiations per survivor against 3.27 -- measured 103 us -> 36 us
    at k ~ 1e19, which is what lets the classification pool run on ~1.4
    cores instead of ~4 (OPTIMIZATION_LOG.md #24).

    Why the prime case dominated: 24% of survivors at this depth have
    m*k^2+1 prime at m = 1, and a PRIME is what makes mr_is_prime evaluate
    all seven bases -- a composite is rejected by the first.
    """
    kk = k * k
    r = 0
    while r < cap and sprp_base2((r + 1) * kk + 1):
        r += 1
    if r < SPRP_EXACT_FROM:
        return r                       # proved short; nothing records it
    r = 0
    while r < cap and mr_is_prime((r + 1) * kk + 1):
        r += 1
    return r


def _classify_chunk(task):
    """Pool worker: run lengths of a chunk of survivors, in the given order.

    Module-level and self-contained so it survives Windows spawn; touches
    no GPU, so workers never contend with the parent's device work.
    """
    W, cap, js = task
    return [sprp_run(int(j) * W, cap) for j in js]


def _worker_init():
    """Pool worker startup: go deaf to Ctrl+C, drop priority, pay the imports.

    huntlib.pool.worker_init, which is where the reasoning now lives: the
    PARENT decides when a run ends (a worker that kills itself on the
    console's Ctrl+C can break the pool underneath a parent still writing
    its checkpoint), a classification worker has a whole segment of slack
    and no business competing with the display driver for a time slice, and
    the imports are paid inside the ramp rather than inside the first real
    segment.
    """
    _hpool.worker_init("numpy", "sympy")


def _worker_ping():
    return os.getpid()


def _prime_pool(pool, workers, ramp_s=WORKER_RAMP_S):
    """Start the pool's interpreters ONE AT A TIME (huntlib.pool.ramp).

    The subtlety that has to be right, and the reason this is not a loop of
    pings: a pool spawns on submit ONLY IF no worker is idle, so pinging and
    waiting ramps nothing -- the single worker that exists answers every
    ping and the pool never grows.  Each worker has to be HELD busy while
    the next is asked for.
    """
    return _hpool.ramp(pool, workers, ramp_s=ramp_s)


def _submit_segment(pool, surv, W, cap):
    """Chunk a segment's survivors and hand them to the pool (or classify
    inline when there is no pool).  Returns a callable that yields the run
    lengths in survivor order.  Survivors arrive as a list of Python ints
    (the deep-zone API: j exceeds u64 past k ~ 5.5e23) or a numpy array."""
    js = surv if isinstance(surv, list) else surv.tolist()
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
    # progression, and the table it is checked against is built from
    # sympy's square roots with plain `%` -- never the GPU's residue walk
    # or its Barrett arithmetic.  The table is consulted DIRECTLY
    # (CpuEngine.survives, Python integers, exact at any k).  The windowed
    # segmented sweep this replaces converted k to j on the COARSER wheel,
    # which crosses the enforced j ceiling 13x sooner than the campaign
    # does: at k ~ 1.1e22 a run-12 [NEAR] verification asked the 2310
    # wheel for j ~ 4.7e18 and the ceiling guard killed a live campaign
    # mid-hunt.  What is verified is unchanged -- k is on the alt wheel
    # and no prime below the alt sieve depth divides any of its values --
    # and the leg now holds to any depth the hunt can reach.
    alt_n = max(3, min(n_filter, claimed_run) - 1)
    alt = CpuEngine(alt_n)
    if k % alt.W:
        return None, f"alternate-alignment re-sieve: k is not on the {alt.W} wheel"
    if not alt.survives(k // alt.W):
        return None, f"alternate-alignment re-sieve (wheel {alt.W}) kills k"
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
    """Load the cursor, and say so loudly if it had to come from the .bak.

    Recovering from the backup means the previous run did not shut down
    cleanly -- the main checkpoint was mid-write when the process, or the
    machine, stopped.  The campaign carries on (one segment is redone), but
    the owner should be told, because on this machine that has three times
    meant the machine itself went down rather than the program.
    """
    def _warn(m):
        log("WARN", m)
        if "RECOVERED" in m:
            log("WARN", "a recovered checkpoint means the last run stopped "
                        "mid-save; the cursor is one segment behind and the "
                        "campaign carries on from there.")
    return _ckpt.load(CKPT, ckpt_key(q2), warn=_warn)


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
    """[(term, label, depth_k)] ascending: the model's Q1/median/Q3/P90 for
    every predicted term, from the predictions stated before the run.  The
    enforced ceiling of the running wheel is appended at run time as the
    last rung (term None -- it belongs to no term and never retires).

    `term` is the n each rung is a prediction ABOUT, and it is carried
    because a rung stops being a progress marker the moment that term
    lands: see live_rungs."""
    rungs = []
    try:
        with open(path) as fh:
            preds = json.load(fh)["predictions"]
    except Exception:
        return rungs
    for n_s, v in preds.items():
        for q in ("Q1", "median", "Q3", "P90"):
            if q in v:
                rungs.append((int(n_s), f"a({int(n_s)}) {q}", float(v[q])))
    rungs.sort(key=lambda t: t[2])
    return rungs


def open_rungs(rungs, frontier):
    """The rungs still worth aiming at: the model's quartiles for terms
    ABOVE the frontier.  A term's rungs retire the moment it is settled --
    a prediction of where a(12) should appear is not progress once a(12)
    is a number in the evidence directory."""
    return [(t, lab, d) for (t, lab, d) in rungs if t > frontier]


def passed_labels(c):
    return c.get("rungs_passed", [])


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

    The refusal itself is huntlib.checkpoint.refuse_mismatch -- the rule is
    repo-wide, and a second project now depends on it.  The exception type
    at this call site is unchanged.
    """
    try:
        _ckpt.refuse_mismatch(CKPT, ckpt_key(eng.q2), fresh=fresh,
                              describe=lambda s: f"n={s.get('n')} next_j="
                                                 f"{s.get('next_j')} of "
                                                 f"W={s.get('W')}")
    except (_ckpt.CursorRefused, CheckpointCorrupt) as e:
        raise CorruptEngineError(f"[ALARM] {e}")


# ------------------------------- discovery ---------------------------------

def record_discovery(ev, label):
    """Write the evidence JSON for a FIRST OCCURRENCE and upsert the ledger
    entry for k.  Called for discoveries only: the evidence directory holds
    first occurrences, never census values (CONVENTIONS.md).

    Keyed by k, so redoing a segment (the one in flight at an interrupt or
    a crash is redone on resume) rewrites the same records instead of
    appending duplicates.  huntlib.evidence.record does the keying, the
    upsert and the durable write; the file NAME is this project's."""
    return _evid.record(ev, "evidence",
                        f"ladder_hit_run{ev['run']}_k{ev['k']}.json",
                        DISC, key="k", label=label)


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
        def make_engine(m):
            return CpuEngine(m, q2=args.q2)
    else:
        from ladder_gpu import GpuEngine

        def make_engine(m):
            f = "auto" if args.fold < 0 else (args.fold if args.fold else None)
            return GpuEngine(m, q2=args.q2, fold=f)

    # ---- cursor: the checkpoint says which filter the campaign is on
    c = None if args.fresh else load_ckpt(args.q2)
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

    # ---- what Ctrl+C saves.  NOT the live `c`: its counters are updated
    # per survivor, so a mid-segment save persists census that the redone
    # segment counts a second time -- the same reason the periodic save is
    # pinned to segment boundaries.  `boundary` is a copy of the cursor as
    # of the last FULLY classified segment; the interrupt writes that, so
    # an interrupted run costs at most the segment in flight and never
    # double-counts.  (huntlib.shutdown runs this deaf to further signals,
    # so a second Ctrl+C cannot land inside the write.)
    boundary = [json.loads(json.dumps(c))]

    def mark_boundary():
        """Called wherever `c` is consistent: end of a segment, after a
        filter switch, after the prelude."""
        boundary[0] = json.loads(json.dumps(c))

    def _save_on_interrupt():
        b = boundary[0]
        save_ckpt(b)
        return ("checkpoint saved at the last segment boundary, k = %.4e "
                "(the segment in flight is redone on resume)"
                % (b["next_j"] * b["W"]))

    _shutdown.on_interrupt(_save_on_interrupt)

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
        mark_boundary()

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

    def j_reach():
        # the engine's enforced line reach: fold P x J_CEIL folded (the
        # device's u64 quantity is u, not j), J_CEIL otherwise
        return getattr(eng, "J_REACH", J_CEIL)

    def ceiling():
        return j_reach() * W

    def cap_now():
        return ceiling() if user_cap is None else min(user_cap, ceiling())

    def j_cap_now():
        return min(cap_now() // W + 1, j_reach())

    if user_cap is not None and user_cap > ceiling():
        log("ALARM", f"requested depth {user_cap:.3e} is past the enforced "
                     f"ceiling {ceiling():.3e}")
        return 2

    def live_rungs():
        """The ladder as it stands NOW: the model's quartiles for the terms
        that are still OPEN, then the enforced ceiling.

        A rung is a prediction of where a term should appear, so the moment
        that term is found its remaining quartiles stop being progress
        markers -- keeping them made [STATUS] advertise `next a(12) P90 at
        9.51e19` for as long as the hunt kept running after a(12) was found
        at 5.51e19, pointing the operator at a depth that no longer meant
        anything.  Retiring is by the LIVE frontier, so it happens the
        instant a find is verified and needs nothing stored."""
        live = open_rungs(rungs, frontier_of(c))
        return live + [(None, f"enforced ceiling of the {W} wheel",
                        float(ceiling()))]

    def next_rung(pos):
        passed = c.get("rungs_passed", [])
        for i, (term, label, depth) in enumerate(live_rungs()):
            if label not in passed and depth > pos:
                return i, label, depth
        return None
    # rungs already behind the cursor (a resume from before rungs existed)
    # are recorded silently
    for _t, label, depth in live_rungs():
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
        pool = ProcessPoolExecutor(max_workers=workers,
                                   initializer=_worker_init)
        hb.doing(f"starting {workers} classification workers, one at a time")
        t_ramp = time.time()
        up = _prime_pool(pool, workers, args.worker_ramp)
        log("STAGE", f"classification pool: {up} workers up and warm in "
                     f"{time.time()-t_ramp:.1f}s (ramped one at a time at "
                     f"below-normal priority; a simultaneous start of N "
                     f"interpreters is the campaign's largest host load "
                     f"step, and the pool has a whole segment of slack in "
                     f"which to avoid it)")
    fold_note = (f", fold {eng.P} ({len(eng.offs)}/{eng.P} offsets, "
                 f"reach k = {ceiling():.2e})"
                 if getattr(eng, "P", 1) > 1 else "")
    log("STAGE", "machine: " + device_report(eng))
    log("STAGE", f"production: n={n} filter, wheel {W}{fold_note}, sieve depth q2="
                 f"{args.q2}, k from {c['next_j']*W:.4e} to {cap_now():.3e} "
                 f"({'--to' if user_cap is not None else 'the enforced ceiling'};"
                 f" {len(live_rungs())} rungs to a({frontier_of(c)+1})+, "
                 f"filter lag {args.filter_lag}) "
                 f"({args.engine}, {workers} classification worker"
                 f"{'s' if workers > 1 else ''}"
                 + (f", {args.gpu_yield_ms:.0f} ms device yield per segment"
                    if args.gpu_yield_ms else "")
                 + (", GENTLE" if args.gentle else "") + ")")

    yield_s = float(args.gpu_yield_ms) / 1000.0

    def sieve(j0, j1):
        if hasattr(eng, "survivors_j_deep"):     # GPU: Python ints, exact
            surv = eng.survivors_j_deep(j0, j1)  # to the folded reach
        else:                                    # CPU engine: chunks
            surv = [int(x) for ch in eng.survivors_j(j0, j1)
                    for x in ch.tolist()]
        if yield_s:
            # A deliberate idle window between segments (--gpu-yield-ms).
            # OFF by default: it lowers the average draw by ADDING load
            # transitions, and a steady load is easier on a machine than an
            # oscillating one of the same mean (CONVENTIONS.md step 5).  It
            # is here because it is something the campaign can do about its
            # own appetite without admin rights and without changing any
            # machine setting, which is the owner's call (step 7).
            time.sleep(yield_s)
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
        mark_boundary()

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
        for j, r in zip(surv, runs):
            k = int(j) * W
            c["survivors"] += 1
            fr = frontier_of(c)
            # the floor sprp_run resolves exactly (a shorter run is
            # proved short but not pinned down, and is recorded nowhere)
            new_best = r > c["best_run"] and r >= SPRP_EXACT_FROM
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
                # the ladder re-aims at the next open term.  The settled
                # terms' unreached quartiles are predictions of where
                # something ALREADY FOUND should have appeared: they are
                # retired here rather than left to be "passed", so no
                # [STATUS] line ever points at a depth for a settled term.
                fr2 = frontier_of(c)
                gone = [(lab, d) for (t, lab, d) in rungs
                        if t <= fr2 and d > k and lab not in passed_labels(c)]
                nr = next_rung(k)
                nxt = ("no rung left but the ceiling" if nr is None else
                       f"next: {nr[1]} at k = {nr[2]:.3e}")
                log("RUNG", f"a({r}) settled: {len(gone)} unreached rung"
                            f"{'' if len(gone) == 1 else 's'} retired"
                            + ("" if not gone else
                               " (" + ", ".join(f"{lab} at k = {d:.3e}"
                                                for lab, d in gone) + ")")
                            + f"; the ladder is now {len(live_rungs())} rung"
                            f"{'' if len(live_rungs()) == 1 else 's'} to "
                            f"a({fr2+1})+ -- {nxt}")
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
        mark_boundary()                     # what a Ctrl+C from here saves
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
        # rungs: the model's quartiles for the terms still OPEN, then the
        # ceiling.  A find retires the rest of that term's rungs (live_rungs)
        # and the ladder renumbers around what is left.
        passed = c.setdefault("rungs_passed", [])
        ladder = live_rungs()
        for i, (term, label, depth) in enumerate(ladder):
            if depth <= pos and label not in passed:
                passed.append(label)
                nr = next_rung(pos)
                nxt = ("last rung -- the campaign ends here" if nr is None else
                       f"next: {nr[1]} at k = {nr[2]:.3e}")
                log("RUNG", f"passed rung {i+1}/{len(ladder)}: {label} "
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
            rung = (f"rung {i}/{len(live_rungs())} passed, next {label} at "
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
                         f"({len(p_surv):,} survivors)")
                if consume(p_j0, p_j1, p_surv, p_collect()):
                    return 0
            pending = new
        # A run that ENDS must persist where it got to.  Every other exit
        # saves (segment boundary every --heartbeat, evidence at once,
        # Ctrl+C, --stop-on-discovery) and this one did not, so a --to run
        # threw away everything it had swept and the next one started over
        # from the floor -- silently, because a re-sweep looks exactly like
        # a sweep.  Caught by running --to twice and reading --status.
        save_ckpt(c)
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
    except CorruptEngineError:
        raise                                  # an ALARM, handled in main()
    except Exception as e:
        # Anything else -- a CUDA error after a driver reset, a device that
        # fell off the bus, an OOM.  DO NOT SAVE: the counts in `c` may be
        # part-way through a segment, and the file on disk is the last
        # SEGMENT BOUNDARY, which is exactly what resume wants.  Say where
        # that is, so the log answers the only question the owner will have.
        log("ALARM", f"{type(e).__name__}: {e}")
        log("ALARM", "the checkpoint on disk is at a segment boundary and is "
                     "untouched by this failure; resuming redoes at most the "
                     "segments since the last save (--heartbeat apart). "
                     "If the machine itself went down rather than the "
                     "program, the same is true and the cursor is intact.")
        raise
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
    r_ok = (len(rungs) >= 8 and all(rungs[i][2] <= rungs[i + 1][2]
                                    for i in range(len(rungs) - 1))
            and any(lab.startswith("a(13) median") for _t, lab, _d in rungs))
    # a settled term's rungs RETIRE: the ladder never points [STATUS] at a
    # depth predicted for a term that has already been found.  Drilled
    # frontier-relative on fixed input so landing a term cannot weaken it.
    terms = sorted({t for t, _lab, _d in rungs})
    t0 = terms[0]
    r_ok = (r_ok
            and open_rungs(rungs, t0 - 1) == rungs               # none settled
            and all(t > t0 for t, _lab, _d in open_rungs(rungs, t0))
            and len(open_rungs(rungs, t0)) < len(rungs)          # some retired
            and open_rungs(rungs, terms[-1]) == [])              # all settled
    # frontier-relative, so landing a term does not falsify the drill
    c0 = fresh_ckpt(10, GpuEngine(10))
    F = FRONTIER_N
    # both lags explicitly, and the DEFAULT pinned: lag 0 is what puts the
    # campaign on the next open term, and so on the coarser wheel
    r_ok = r_ok and FILTER_LAG == 0 and filter_for(c0, F) == F + 1
    r_ok = (r_ok and filter_for(c0, F, lag=1) == F
            and filter_for(c0, F, lag=0) == F + 1)
    settle(c0, F + 1, 10**15)                       # a(F+1) lands
    r_ok = (r_ok and filter_for(c0, F, lag=1) == F + 1
        and filter_for(c0, F, lag=0) == F + 2)
    settle(c0, F + 2, 10**17)                       # a(F+2) lands
    r_ok = (r_ok and filter_for(c0, F, lag=1) == F + 2
        and filter_for(c0, F, lag=0) == F + 3)
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
        print(f"PASS indefinite-run drill: {len(rungs)} model rungs ascending "
              f"and retiring with their term (a({t0}) settled leaves "
              f"{len(open_rungs(rungs, t0))}), "
              f"the default lag is 0 and the filter follows the frontier "
              f"(lag 1: {F} -> {F+1} -> {F+2}; "
              f"lag 0: {F+1} -> {F+2} -> {F+3}), and a 2310 -> 30030 wheel "
              f"change moves the cursor by floor (overlap < one period, never "
              f"a gap)")

    # --- graceful-shutdown drill: Ctrl+C is a NORMAL exit ---------------
    # Binding repo-wide (CONVENTIONS.md "Stopping a run"): one path out,
    # deaf to further signals while the checkpoint is written, exit 130,
    # and never a traceback.  The second Ctrl+C is the one that used to
    # bite -- it lands inside the handler and Python prints the pair.
    import signal as _sig
    saved = {n: _sig.getsignal(getattr(_sig, n))
             for n in ("SIGINT", "SIGTERM", "SIGBREAK") if hasattr(_sig, n)}
    saved_cbs = list(_shutdown._callbacks)
    _shutdown._callbacks.clear()
    _shutdown._shutting_down = False
    order, deaf = [], []

    def _cb_first():
        order.append("first")
        return "checkpoint saved at the last segment boundary"

    def _cb_second():
        deaf.append(_sig.getsignal(_sig.SIGINT))     # deaf BEFORE any write?
        order.append("second")

    def _cb_second_ctrl_c():
        raise KeyboardInterrupt                      # the operator, again

    _shutdown.on_interrupt(_cb_first)
    _shutdown.on_interrupt(_cb_second)
    _shutdown.on_interrupt(_cb_second_ctrl_c)

    def _interrupted():
        raise KeyboardInterrupt

    rc = _shutdown.graceful(_interrupted)
    sd_ok = (rc == _shutdown.EXIT_INTERRUPTED == 130
             and order == ["second", "first"]        # LIFO, all of them ran
             and deaf == [_sig.SIG_IGN]              # deaf before the save
             and _shutdown.graceful(lambda: 7) == 7)  # a normal exit passes
    for n, h in saved.items():
        _sig.signal(getattr(_sig, n), h)
    _shutdown._callbacks[:] = saved_cbs
    _shutdown._shutting_down = False
    if not sd_ok:
        print(f"FAIL graceful-shutdown drill: rc={rc} order={order} "
              f"deaf={deaf}")
        ok = False
    else:
        print("PASS graceful-shutdown drill: an interrupt runs every "
              "registered save (LIFO) with SIGINT already ignored, survives "
              "a second Ctrl+C inside the handler, and exits 130")

    # --- discovery-once / census drill: the frontier promotes and the
    # classification follows it: beyond = DISCOVERY, at = NEAR (one short,
    # logged), below = CENSUS (counted only), under the floor = None ------
    # relative to the frontier, so the drill keeps its meaning as terms land
    c = fresh_ckpt(10, GpuEngine(10))
    F = FRONTIER_N
    steps = [(F - 2, "CENSUS"), (F - 1, "CENSUS"), (F, "NEAR"),
             (F + 1, "DISCOVERY"), (NEAR_FROM, "CENSUS"), (NEAR_FROM - 1, None)]
    seq_ok = frontier_of(c) == F and all(
        event_kind(c, r) == kind for r, kind in steps)
    settle(c, F + 1, 10**15)                       # a(F+1) lands
    seq_ok = seq_ok and frontier_of(c) == F + 1 \
        and event_kind(c, F + 1) == "NEAR" and event_kind(c, F) == "CENSUS" \
        and event_kind(c, F + 2) == "DISCOVERY"
    newly = settle(c, F + 3, 3 * 10**15)           # one run settles F+2 AND F+3
    seq_ok = seq_ok and newly == [F + 2, F + 3] and frontier_of(c) == F + 3 \
        and event_kind(c, F + 3) == "NEAR" and event_kind(c, F + 1) == "CENSUS" \
        and event_kind(c, F + 4) == "DISCOVERY" \
        and settled_at(c, F + 2) == 3 * 10**15 and settled_at(c, 9) == KNOWN[9] \
        and event_kind(c, NEAR_FROM - 1) is None
    # the STATUS census format itself, on fixed input (independent of where
    # the frontier happens to stand, so a landed term cannot silently
    # weaken this into a tautology)
    cs = census_str({"7": 280, "9": 28, "12": 1}, 7, 12)
    seq_ok = seq_ok and cs == "census 7:280 8:0 9:28 10:0 11:0 12:1"
    # and that the launcher asks for floor..frontier
    live = census_str(c.get("near_counts", {}), NEAR_FROM, frontier_of(c))
    seq_ok = seq_ok and live.startswith("census %d:" % NEAR_FROM) \
        and live.endswith(" %d:0" % (F + 3))
    if not seq_ok:
        print("FAIL discovery-once drill: frontier/near/census classification "
              f"or census string ({cs})")
        ok = False
    else:
        print(f"PASS discovery-once drill: a({F+1}) is a discovery once; "
              f"run-{F+1} values are then NEAR (one short, logged) and "
              f"run-{F} drops to census (counted only); one run of {F+3} "
              f"settles a({F+2}) and a({F+3}) together and the frontier "
              f"promotes {F} -> {F+1} -> {F+3}; census string is "
              f"floor..frontier in the shared format")

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

    # --- classification drill: the two-pass chain == the all-bases chain --
    # sprp_run runs a base-2-only chain first and only redoes it with the
    # full huntlib base set when that chain reaches SPRP_EXACT_FROM.  That
    # is sound because a strong-test FAILURE IS A PROOF of compositeness,
    # so the cheap chain is a rigorous upper bound -- but "sound" is an
    # argument, and this is the measurement.  Every survivor of a real
    # window, both ways, on the engine's own run_length (which never took
    # the shortcut), plus the direction of any disagreement.
    eng = GpuEngine(12, q2=Q2_CAMPAIGN)
    # the campaign depth leaves ~5.6e5 survivors per 1e18 of k-line, so the
    # window has to be wide to be populated at all
    surv = eng.survivors_j(10**12, 10**12 + 6 * 10**10)[:1200]
    cap = FRONTIER_N + 8
    two = [sprp_run(int(j) * eng.W, cap) for j in surv.tolist()]
    full = [eng.run_length(int(j) * eng.W, cap=cap) for j in surv.tolist()]
    cheap_hi = all(a >= b for a, b in zip(two, full))
    if surv.size < 500:
        print("FAIL classification drill: window under-populated (vacuous)")
        ok = False
    elif two != full:
        bad = [(int(j) * eng.W, a, b) for j, a, b
               in zip(surv.tolist(), two, full) if a != b]
        print(f"FAIL classification drill: {len(bad)} of {surv.size} disagree "
              f"with the all-bases chain, e.g. {bad[:3]}")
        ok = False
    elif not cheap_hi:
        print("FAIL classification drill: the cheap chain UNDERSTATED a run")
        ok = False
    else:
        print(f"PASS classification drill: two-pass sprp_run == the all-bases "
              f"run_length on all {surv.size} survivors of a real window "
              f"(runs to {max(full)}); exact at and above "
              f"SPRP_EXACT_FROM={SPRP_EXACT_FROM}, and every run the campaign "
              f"records (census floor {NEAR_FROM}, [NEAR], [DISCOVERY], "
              f"best_run) is at or above it")

    # --- deep-verification drill: the alternate-alignment leg must hold
    # ABOVE the coarse wheel's old reach.  The windowed re-sieve it
    # replaced converted k to j on the ALT wheel (2310), which crosses
    # J_CEIL at k = 9.24e21 -- 13x before the campaign's own ceiling --
    # and a run-12 [NEAR] verification at k ~ 1.1e22 crashed a live
    # campaign there (ValueError from the ceiling guard, mid-hunt).  The
    # direct table check (CpuEngine.survives, Python ints) must agree
    # with big-integer divisibility in BOTH directions at exactly that
    # depth, on the alt wheel the leg really uses.
    alt = CpuEngine(11, q2=4096)
    j_crash = 4_748_822_888_266_957_986          # the j that raised
    sample = list(range(j_crash, j_crash + 25))
    j_star = next((j for j in range(j_crash, j_crash + 10_000_000)
                   if alt.survives(j)), None)
    if j_star is not None and j_star not in sample:
        sample.append(j_star)

    def _bigint_clean(j):
        k = j * alt.W
        return not any((m * k * k + 1) % q == 0
                       for q in alt.primes for m in range(1, alt.n + 1))

    agree = all(alt.survives(j) == _bigint_clean(j) for j in sample)
    kills = sum(1 for j in sample if not alt.survives(j))
    if (j_star is None or j_star <= J_CEIL or not agree
            or kills < 5 or not _bigint_clean(j_star)):
        print(f"FAIL deep-verification drill: j*={j_star} agree={agree} "
              f"kills={kills} of {len(sample)}")
        ok = False
    else:
        print(f"PASS deep-verification drill: direct alt-wheel check == "
              f"big-integer divisibility on {len(sample)} candidates at "
              f"j ~ {j_crash:.2e} on the 2310 wheel ({kills} killed, "
              f"survivor j* = {j_star} kept both ways) -- all PAST the "
              f"j ceiling {J_CEIL:.0e} that the old windowed re-sieve "
              f"crashed on at k ~ 1.1e22")

    # --- durability drill: a crash mid-save must not cost the cursor ------
    # The real failure, reproduced exactly: a campaign checkpoint written
    # across an abrupt stop came back as 785 bytes of NUL -- right size, no
    # content,
    # because os.replace is atomic for the directory ENTRY and the DATA was
    # still in the page cache.  A save now fsyncs before the replace and
    # rotates the previous file to .bak, so the cursor survives either way.
    import shutil
    import tempfile
    from huntlib import checkpoint as _cp
    d_ = tempfile.mkdtemp()
    try:
        pth = os.path.join(d_, "c.json")
        _cp.save(pth, {"key": "K", "next_j": 1})
        _cp.save(pth, {"key": "K", "next_j": 2})
        d_ok = (_cp.load(pth, "K")["next_j"] == 2
                and json.load(open(pth + ".bak"))["next_j"] == 1)
        with open(pth, "wb") as fh:                  # the observed corruption
            fh.write(bytes(785))            # 785 NUL bytes, as found
        d_ok = d_ok and _cp.load(pth, "K")["next_j"] == 1   # recovered
        os.remove(pth + ".bak")
        try:
            _cp.load(pth, "K")
            d_ok = False                             # must not be silent
        except _cp.CheckpointCorrupt:
            pass
        d_ok = d_ok and _cp.load(os.path.join(d_, "absent.json"), "K") is None
    finally:
        shutil.rmtree(d_, ignore_errors=True)
    if not d_ok:
        print("FAIL durability drill: fsync/.bak rotation or corrupt handling")
        ok = False
    else:
        print("PASS durability drill: saves fsync before replace and rotate a "
              ".bak; a 785-NUL checkpoint (the real corruption this drill "
              "was written from) is "
              "RECOVERED from the .bak, and with no .bak it raises "
              "CheckpointCorrupt instead of silently restarting the sweep")

    # --- persistence drill: a run that ENDS must persist where it got to --
    # Every other exit saved (segment boundary, evidence, Ctrl+C,
    # --stop-on-discovery) and the ordinary completion did not, so a --to
    # run threw away everything it had swept and the next one silently
    # started over from the floor -- a re-sweep looks exactly like a sweep.
    # Two bounded runs in a temp directory; the second must START where the
    # first stopped and END further on.
    import types
    d2 = tempfile.mkdtemp()
    cwd = os.getcwd()
    try:
        os.chdir(d2)
        seed = fresh_ckpt(12, GpuEngine(12, q2=Q2_DEFAULT))
        seed["canaries_done"] = True          # drilled separately (G5/G8)
        save_ckpt(seed)
        a = types.SimpleNamespace(
            engine="gpu", fresh=False, n=12, filter_lag=0, q2=Q2_DEFAULT,
            to=2e16, seg_span=None, heartbeat=30.0, workers=1,
            worker_ramp=0.0, gpu_yield_ms=0.0, gentle=False,
            stop_on_discovery=False, fold=-1)
        production(a)
        mid = load_ckpt(Q2_DEFAULT)
        a.to = 4e16
        production(a)
        end = load_ckpt(Q2_DEFAULT)
        p_ok = (mid is not None and end is not None
                and mid["next_j"] > seed["next_j"]
                and end["next_j"] > mid["next_j"]
                and end["survivors"] > mid["survivors"] > 0
                and mid["next_j"] * mid["W"] >= 2e16
                and end["next_j"] * end["W"] >= 4e16)
        detail = (f"{seed['next_j']} -> "
                  f"{mid['next_j'] if mid else None} -> "
                  f"{end['next_j'] if end else None}")
    finally:
        os.chdir(cwd)
        shutil.rmtree(d2, ignore_errors=True)
    if not p_ok:
        print(f"FAIL persistence drill: cursor did not advance and persist "
              f"across two bounded runs ({detail})")
        ok = False
    else:
        print(f"PASS persistence drill: two bounded runs, the second resumed "
              f"where the first stopped and both persisted their cursor "
              f"(next_j {detail}, survivors {mid['survivors']:,} -> "
              f"{end['survivors']:,})")

    # --- ramp drill: the pool comes up one interpreter at a time -----------
    # N fresh interpreters importing numpy in the same instant is the
    # campaign's largest host load step, and it landed while the device was
    # flat out.  _prime_pool must return with every worker already up and
    # warm, and must have taken at least the ramp interval to do it.
    with ProcessPoolExecutor(max_workers=3, initializer=_worker_init) as pl:
        t_r = time.time()
        up = _prime_pool(pl, 3, ramp_s=0.05)
        el = time.time() - t_r
        pids = {pl.submit(_worker_ping).result() for _ in range(24)}
    if up != 3 or el < 0.10 or len(pids) != 3:
        print(f"FAIL ramp drill: {up} up in {el:.2f}s, {len(pids)} distinct "
              f"pids afterwards")
        ok = False
    else:
        print(f"PASS ramp drill: 3 workers started one at a time ({el:.2f}s "
              f"at a 0.05s interval), all warm and distinct before the first "
              f"segment")

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
    try:
        with open(CKPT) as f:
            c = json.load(f)
    except Exception as e:
        bak = CKPT + ".bak"
        if not os.path.exists(bak):
            print(f"{CKPT} is unreadable ({e}) and there is no {bak}: the "
                  f"cursor is gone (a hard crash mid-save leaves a "
                  f"right-sized file of NUL). --fresh restarts the sweep.")
            return 2
        with open(bak) as f:
            c = json.load(f)
        print(f"NOTE: {CKPT} is unreadable ({e}); showing {bak}, which is "
              f"at most one segment behind")
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
    # The starting filter tracks the SAME rule filter_for uses, so a fresh
    # run and a resumed one agree.  At the default lag of 0 that is the
    # frontier plus one -- sieve for run >= 12 with a(11) settled -- which
    # puts the campaign on the 30030 wheel and is 13x the hunt (FILTER_LAG).
    # Pinning it to a literal instead would silently disagree with
    # filter_for the moment a term lands.
    ap.add_argument("--n", type=int,
                    default=max(NEAR_FROM, FRONTIER_N + 1 - FILTER_LAG),
                    help="the STARTING filter (sieve for k with run >= n); "
                         "the filter then follows the frontier (--filter-lag)")
    ap.add_argument("--filter-lag", type=int, default=FILTER_LAG,
                    help="filter = max(--n, frontier + 1 - lag): 0 (default) "
                         "is the fastest hunt -- the sieve asks only for the "
                         "next open term, which coarsens the wheel and is "
                         "worth 13x; 1 runs a step behind so the last "
                         "settled length still shows up as one-short [NEAR] "
                         "lines and the census fills in, at 1/13 the rate")
    ap.add_argument("--q2", type=int, default=Q2_CAMPAIGN,
                    help="sieve depth for the CAMPAIGN (default %d). Sets "
                         "which side of the pipe binds: 4x deeper costs the "
                         "device 7%%%% and takes 4.1x the work off the "
                         "classification pool. The frozen benchmark depth "
                         "(%d) is unaffected and stays comparable."
                         % (Q2_CAMPAIGN, Q2_DEFAULT))
    ap.add_argument("--to", type=float, default=None,
                    help="depth cap in k (default: none -- the campaign runs "
                         "to the enforced ceiling of its wheel, the last rung)")
    ap.add_argument("--engine", choices=["gpu", "cpu"], default="gpu")
    ap.add_argument("--fold", type=int, default=-1,
                    help="fold this sieve prime into candidate generation "
                         "(default -1 = auto, the first sieve prime: 3.4x "
                         "fewer candidates at n=13 for the identical stream, "
                         "and the reach extends to fold x J_CEIL x wheel -- "
                         "past a(14) P90. 0 disables the fold, capping the "
                         "reach at k = 1.2e23, below the a(14) median)")
    ap.add_argument("--seg-span", type=float, default=None,
                    help="k per checkpoint segment (default: %d j)" % SEG_J)
    ap.add_argument("--heartbeat", type=float, default=30.0,
                    help="seconds between [STATUS] lines (position, rate, the "
                         "census counts per run length, finds, odds, next "
                         "rung); 30 is the repo convention")
    ap.add_argument("--workers", type=int, default=WORKERS_DEFAULT,
                    help="classification processes (default %d: at the "
                         "campaign sieve depth the pool needs ~4 cores to "
                         "stay a segment ahead of the device, and a hunt "
                         "must not take the whole machine; 1 = serial, "
                         "in-process)" % WORKERS_DEFAULT)
    ap.add_argument("--worker-ramp", type=float, default=WORKER_RAMP_S,
                    help="seconds between worker starts (default %.2f). The "
                         "pool is started one interpreter at a time; N fresh "
                         "interpreters importing numpy in the same instant "
                         "is the campaign's largest host load step."
                         % WORKER_RAMP_S)
    ap.add_argument("--gpu-yield-ms", type=float, default=0.0,
                    help="idle the device this long after every segment "
                         "(default 0 = off). A documented way to cut the "
                         "campaign's sustained draw when the machine is "
                         "shared with something else; see --gentle.")
    ap.add_argument("--gentle", action="store_true",
                    help="be quiet on a machine somebody else is using: "
                         "half the workers, a slower ramp, a 25 ms device "
                         "yield per segment. Costs a few percent of the "
                         "rate. This program never changes a machine "
                         "setting for you; clocks and power limits are the "
                         "owner's to set.")
    args = ap.parse_args()
    if args.gentle:
        args.workers = max(1, min(args.workers, WORKERS_DEFAULT // 2))
        args.worker_ramp = max(args.worker_ramp, 1.0)
        args.gpu_yield_ms = max(args.gpu_yield_ms, 25.0)
    if args.selftest:
        return selftest()
    if args.status:
        return status()
    # --to against the ceiling is checked in production(), where the
    # engine exists: the reach depends on the fold (P x J_CEIL folded)
    if args.filter_lag < 0:
        log("ALARM", "--filter-lag must be >= 0")
        return 2
    if args.q2 < 1024:
        log("ALARM", "--q2 below 1024 is not a sieve")
        return 2
    if args.gpu_yield_ms < 0:
        log("ALARM", "--gpu-yield-ms must be >= 0")
        return 2
    try:
        return production(args)
    except CheckpointCorrupt as e:
        log("ALARM", str(e))
        return 2
    except CorruptEngineError as e:
        log("ALARM", str(e))
        return 2


if __name__ == "__main__":
    # the ONLY place a KeyboardInterrupt is caught: an interrupt anywhere --
    # prelude, pool ramp, sieve, verification, final save -- takes one path
    # out, deaf to further Ctrl+C, and never prints a traceback
    _sys.exit(_shutdown.graceful(main))
