"""ladder_model.py -- Bateman-Horn odds model for A247965.

The n forms f_m(k) = m*k^2 + 1, m = 1..n, are irreducible, have no fixed
common divisor once k is on the wheel, and Bateman-Horn (Dickson's
conjecture, quantified) predicts

    #{k <= K : all n values prime}  ~  C_n * Integral_2^K dk / prod_m ln f_m(k)

with the singular series

    C_n = prod_q (1 - w_q(n)/q) / (1 - 1/q)^n

over primes q, where w_q(n) = #{k mod q : some m <= n has m*k^2+1 == 0}.
Two closed forms make that product cheap and exact (both proved in
ladder_reference.py's docstring and gated against the oracle by Z4):

    q <= n+1 :  w_q = q - 1        (every nonzero k is killed)
    q >  n+1 :  w_q = 2 * #{m <= n : (-m|q) = +1}

The q <= n+1 factors are the interesting ones: they read
q^(n-1)/(q-1)^n >> 1, which is the model's way of saying that surviving k
are rare (multiples of W(n)) but enormously more fertile than average.

First-occurrence law used throughout: hits arrive as a Poisson process in
E, so P(a(n) > K) = exp(-E_n(K)) and the median solves E = ln 2.

Gates: Z1 (tail bound), Z2 (validation on the knowns -- their quantiles
must SCATTER, not pile up at 0 or 1), Z3 (E=1 depths increase with n),
Z4 (the closed forms for w_q agree with the oracle's direct count).

ASCII only.
"""

import json
import math

import numpy as np
from sympy import primerange

from ladder_reference import KNOWN, OPEN_N, PUBLISHED_BOUNDS

Q_CUT = 2_000_000        # singular-series product cut; tail bounded in Z1


def w_of_q(q, n):
    """Killed residues of k mod q -- closed form, gated against the oracle."""
    if q <= n + 1:
        return q - 1
    c = 0
    for m in range(1, n + 1):
        if pow((-m) % q, (q - 1) // 2, q) == 1:
            c += 1
    return 2 * c


def log_singular_series(n, qcut=Q_CUT):
    """ln C_n, plus a crude bound on the discarded tail."""
    ls = 0.0
    for q in primerange(2, qcut):
        ls += math.log1p(-w_of_q(q, n) / q) - n * math.log1p(-1.0 / q)
    # For q > n+1 the factor is 1 + (n - w_q)/q + O(n^2/q^2) with w_q
    # averaging n, so the tail is dominated by sum_{q > qcut} n^2/q^2.
    return ls, (n * n) / qcut


def expected_count(n, K, logC, lo=2.0, pts=4000):
    """E_n(K), log-spaced quadrature of the Bateman-Horn integral."""
    if K <= lo:
        return 0.0
    u = np.linspace(math.log(lo), math.log(K), pts)
    t = np.exp(u)
    dens = np.ones_like(t)
    for m in range(1, n + 1):
        dens = dens * np.log(m * t * t + 1.0)
    return math.exp(logC) * float(np.trapezoid(t / dens, u))


def depth_for(n, logC, target, lo=2.0):
    """Bisect for the K where E_n(K) reaches target."""
    a, b = lo, 1e40
    for _ in range(200):
        mid = math.exp((math.log(a) + math.log(b)) / 2)
        if expected_count(n, mid, logC) < target:
            a = mid
        else:
            b = mid
    return a


def model(ns=tuple(range(4, 14))):
    return {n: dict(zip(("logC", "tail"), log_singular_series(n))) for n in ns}


def quantiles(m):
    """Model quantile of each known term the model did not help find."""
    out = {}
    for n in sorted(KNOWN):
        if n in m:
            E = expected_count(n, KNOWN[n], m[n]["logC"])
            out[n] = (E, 1.0 - math.exp(-E))
    return out


def predictions(m, ns=OPEN_N):
    """Quartiles/median for each open term, conditional on the published
    searched-empty range where one exists."""
    out = {}
    for n in ns:
        logC = m[n]["logC"]
        base = PUBLISHED_BOUNDS.get(n, 0)
        spent = expected_count(n, base, logC) if base else 0.0
        row = {"searched_empty_to": base, "E_spent": spent}
        for lbl, p in (("Q1", .25), ("median", .5), ("Q3", .75), ("P90", .90)):
            row[lbl] = depth_for(n, logC, spent - math.log(1 - p))
        row["E=1 at"] = depth_for(n, logC, 1.0)
        out[n] = row
    return out


# --------------------------------- gates -----------------------------------

def z1_tail_small(m):
    for n, d in m.items():
        if d["tail"] > 1e-3:
            return False, f"Z1 FAIL: singular tail {d['tail']:.2e} at n={n}"
    return True, "Z1 ok: singular-series tails < 1e-3 in ln"


def z2_validation(m):
    qs = quantiles(m)
    detail = ", ".join(f"a({n}):E={E:.2f}/u={u:.2f}" for n, (E, u) in qs.items())
    us = [u for _, u in qs.values()]
    if all(u > 0.98 for u in us) or all(u < 0.02 for u in us):
        return False, "Z2 FAIL: quantiles degenerate -- " + detail
    return True, "Z2 ok: " + detail


def z3_monotone(m):
    locs = [depth_for(n, m[n]["logC"], 1.0) for n in OPEN_N]
    if any(b < a for a, b in zip(locs, locs[1:])):
        return False, f"Z3 FAIL: E=1 depths not increasing: {locs}"
    return True, "Z3 ok: E=1 depths " + " ".join("%.2g" % v for v in locs)


def z4_w_matches_oracle(m=None):
    """The closed forms for w_q must equal the oracle's direct count."""
    from ladder_reference import forbidden_k_residues
    for n in (4, 9, 10, 13):
        for q in primerange(2, 400):
            if w_of_q(q, n) != len(forbidden_k_residues(q, n)):
                return False, (f"Z4 FAIL: w({q},{n}) = {w_of_q(q, n)} != "
                               f"{len(forbidden_k_residues(q, n))} direct")
    return True, ("Z4 ok: closed-form w(q) == oracle's direct divisibility "
                  "count for every prime q < 400 at n = 4, 9, 10, 13")


def main():
    print("building singular series (q < %d) ..." % Q_CUT)
    m = model()
    ok = True
    for g in (z1_tail_small, z2_validation, z3_monotone, z4_w_matches_oracle):
        good, msg = g(m)
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    pr = predictions(m)
    print("\npredictions (first occurrence; conditional on the published "
          "searched-empty range):")
    for n, row in pr.items():
        print("  a(%2d): empty to %.3g (E spent %.3f)  Q1 %.3g  median %.3g"
              "  Q3 %.3g  P90 %.3g" %
              (n, row["searched_empty_to"], row["E_spent"], row["Q1"],
               row["median"], row["Q3"], row["P90"]))
    with open("model_results.json", "w") as f:
        json.dump({"singular": {str(k): v for k, v in m.items()},
                   "quantiles": {str(k): list(v)
                                 for k, v in quantiles(m).items()},
                   "predictions": {str(k): v for k, v in pr.items()}},
                  f, indent=1)
    print("\nmodel_results.json written")
    return ok


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.  huntlib is
# imported HERE, in the script path only, so the module itself keeps the
# dependencies its gates are argued from and nothing else.
if __name__ == "__main__":
    import pathlib as _pl
    import sys as _s
    _s.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown
    _s.exit(_shutdown.graceful(lambda: 0 if main() else 1))
