# euler_reference.py -- ORACLE for the A164926 Euler-ladder hunt.
#
# Object: for prime p, run(p) = number of consecutive integers x = 0, 1, 2, ...
# with x^2 + x + p prime (the run breaks at the first composite value).
# A164926(n) = least prime p with run(p) == n exactly.
# Note run(p) >= 1 iff p is prime (x = 0 gives p itself), so the oracle
# sweeps all integers and nonprimes get run 0.
#
# This file is the slow, trustworthy reference: sympy primality only,
# no sieves, no cleverness.  Everything the engines produce is gated
# against it.  Frozen literature values below were read from the local
# OEIS clone (A164926 edit #28, 2026-04-22) on 2026-08-05.
#
# ASCII only (legacy console code pages).

from sympy import isprime

# ---------------------------------------------------------------------------
# Frozen knowns: n -> A164926(n).  Source: OEIS A164926 %S data (a(1)-a(16))
# + comments (a(40) = 41 Euler; a(21) upper value Waldvogel-Leikauf, see
# UNVERIFIED note).  Do not edit without a STATUS.md entry.
KNOWN = {
    1: 2,
    2: 3,
    3: 107,
    4: 5,
    5: 347,
    6: 1607,
    7: 1277,
    8: 21557,
    9: 51867197,
    10: 11,
    11: 180078317,
    12: 1761702947,
    13: 8776320587,
    14: 27649987598537,
    15: 291598227841757,
    16: 17,
    40: 41,
}

# Waldvogel-Leikauf value for run 21 (OEIS comment, Andersen Sep 2009).
# Their search was construction-style; treat as an UPPER BOUND for a(21),
# not a confirmed least.  Frozen here as a run-length canary only.
A21_UPPER = 234505015943235329417

# Euler's lucky numbers (A014556) -- complete by Baker/Stark (Heegner).
LUCKY = [2, 3, 5, 11, 17, 41]

# OPEN targets of the hunt.
OPEN_N = [17, 18, 19, 20]

# Formal exhaustive frontier from the entry ("no other terms less than
# 10^12", 2009).  Andersen's a(14)/a(15) finds imply deeper coverage, but
# 1e12 is the only *stated* bound, so production re-sweeps from scratch --
# the low decades cost seconds and turn a(14)/a(15) into in-stream canaries.
STATED_FRONTIER = 10**12


def value(p, x):
    return x * x + x + p


def run_length(p, cap=100):
    """Exact run length of p by direct primality (oracle-grade)."""
    x = 0
    while x < cap and isprime(x * x + x + p):
        x += 1
    return x


def oracle_search(lo, hi, n, exact=True):
    """All p in [lo, hi) with run exactly n (or >= n).  Slow; small ranges."""
    out = []
    for p in range(max(lo, 2), hi):
        r = run_length(p, cap=n + 1 if not exact else max(n + 2, 42))
        if (r == n) if exact else (r >= n):
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Gates G1/G2 (oracle-internal; engines add G3+)

def g1_known_runs():
    """G1: every frozen known has the exact run its index claims."""
    for n, p in sorted(KNOWN.items()):
        r = run_length(p)
        if r != n:
            return False, f"G1 FAIL: run({p}) = {r}, expected {n}"
    r = run_length(A21_UPPER)
    if r != 21:
        return False, f"G1 FAIL: run(A21_UPPER) = {r}, expected 21"
    return True, "G1 ok: all frozen knowns reproduce their run lengths"


def g2_small_exhaustive():
    """G2: re-derive a(1)-a(8) (and interlopers a(10), a(16)) from scratch."""
    best = {}
    for p in range(2, 22000):
        r = run_length(p)
        if r > 0 and r not in best:
            best[r] = p
    for n in [1, 2, 3, 4, 5, 6, 7, 8, 10, 16]:
        if best.get(n) != KNOWN[n]:
            return False, f"G2 FAIL: least run-{n} found {best.get(n)}, expected {KNOWN[n]}"
    return True, "G2 ok: a(1)-a(8), a(10), a(16) re-derived exhaustively"


def selftest():
    for g in (g1_known_runs, g2_small_exhaustive):
        ok, msg = g()
        print(("PASS " if ok else "FAIL ") + msg)
        if not ok:
            return False
    return True


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.  huntlib is
# imported HERE, in the script path only, so the module itself keeps the
# dependencies its gates are argued from and nothing else.
if __name__ == "__main__":
    import pathlib as _pl
    import sys as _s
    _s.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown
    _s.exit(_shutdown.graceful(lambda: 0 if selftest() else 1))
