"""The gates-times-benchmark SCORE runner (un-gameable by construction).

Every project exposes `python score.py`, which must print

    SCORE <end-to-end Mitems/s on a frozen benchmark shape>

and must print it ONLY if (a) every correctness gate is green and (b) the
benchmark reproduces a frozen WORK FINGERPRINT -- e.g. exact survivor
count and checksum on a pinned window. An engine that skips work fails
the fingerprint and scores 0; an engine that breaks correctness fails the
gates and scores 0. Optimize under the score, never around it.

A deliberate coverage change (new wheel, new bounds) legitimately changes
the fingerprint: update it in the same commit with an OPTIMIZATION_LOG.md
entry explaining why.
"""

import sys
import time

import numpy as np


def run_gates(gates):
    """Run [(callable -> (ok, msg)), ...]; print PASS/FAIL; return all-ok."""
    ok = True
    for g in gates:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


def fingerprint_benchmark(work_fn, span, count_expect, checksum_expect,
                          runs=3, sync=None):
    """Median rate of work_fn() over `runs`, with fingerprint enforcement.

    work_fn() must return a numpy array of results (survivors); the count
    and xor-checksum are compared against the frozen expectations.
    Returns (rate_items_per_s, ok).
    """
    rates, out = [], None
    for _ in range(runs):
        t0 = time.perf_counter()          # not time.time(): a fast engine
        out = work_fn()                   # crosses a frozen window in under
        if sync:                          # the wall clock's resolution
            sync()
        rates.append(span / max(time.perf_counter() - t0, 1e-9))
    count = int(out.size)
    checksum = int(np.bitwise_xor.reduce(out)) if out.size else 0
    ok = (count == count_expect and
          (checksum_expect is None or checksum == checksum_expect))
    if not ok:
        print(f"SCORE 0 (fingerprint mismatch: count={count}, "
              f"checksum={checksum})")
    return float(np.median(rates)), ok


def emit_score(rate, unit=1e6):
    print(f"SCORE {rate/unit:,.0f}")


def score_exit(ok):
    sys.exit(0 if ok else 1)
