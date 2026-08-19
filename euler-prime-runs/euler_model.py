# euler_model.py -- Bateman-Horn odds model for the A164926 ladder.
#
# Density of primes p <= P with x^2+x+p prime for x = 0..n-1 (run >= n):
#     E_n(P) ~ C_n * Integral_2^P dt / (ln t)^n
# with the singular series
#     C_n = prod_q  (1 - r_q(n)/q) / (1 - 1/q)^n
# over primes q, where r_q(n) = |{x^2+x mod q : x = 0..n-1}|.
# (For q > 2n there are no collisions x^2+x = y^2+y mod q with x,y < n,
#  so r_q = n and the factors converge as 1 + O(n^2/q^2).)
#
# Gates Z1-Z3 validate the model against the known generic terms
# a(9), a(11), a(12), a(13), a(14), a(15): the model quantile
# u = 1 - exp(-E_n(a(n))) should look uniform, not clustered at 0 or 1.
# (Lucky-number terms a(10), a(16), a(40) are Heegner magic, excluded.)
#
# ASCII only.

import json
import math

import numpy as np
from sympy import primerange

from euler_reference import KNOWN, OPEN_N

Q_CUT = 2_000_000       # singular-series product cut; tail bounded in z1


def r_q(q, n):
    return len({(x * x + x) % q for x in range(min(n, q))})


def log_singular_series(n, qcut=Q_CUT):
    """ln C_n, plus a rigorous-ish tail bound |ln tail| estimate."""
    ls = 0.0
    for q in primerange(2, qcut):
        rq = r_q(q, n)
        ls += math.log1p(-rq / q) - n * math.log1p(-1.0 / q)
    # tail: factors are 1 + (n - r_q)/q + O(n^2/q^2) with r_q = n exactly
    # for q > 2n, so ln-factor ~ (n^2 - n)/(2 q^2)-ish; bound crudely:
    tail = (n * n) / qcut  # sum_{q>qcut} n^2/q^2 < n^2/qcut
    return ls, tail


def expected_count(n, P, logC, lo=1e4, pts=4000):
    """E_n(P) = C_n * int_lo^P dt/(ln t)^n, log-spaced quadrature."""
    if P <= lo:
        return 0.0
    u = np.linspace(math.log(lo), math.log(P), pts)   # t = e^u, dt = t du
    t = np.exp(u)
    integ = np.trapezoid(t / np.log(t) ** n, u)
    return math.exp(logC) * integ


def model(ns=(9, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21)):
    out = {}
    for n in ns:
        logC, tail = log_singular_series(n)
        out[n] = {"logC": logC, "tail": tail}
    return out


def quantiles(m):
    """Model quantile of each known generic term."""
    qs = {}
    for n in (9, 11, 12, 13, 14, 15):
        E = expected_count(n, KNOWN[n], m[n]["logC"])
        qs[n] = (E, 1.0 - math.exp(-E))
    return qs


def predictions(m, depths=(1e15, 1e16, 1e17, 1e18, 1.8e19)):
    pr = {}
    for n in OPEN_N + [21]:
        row = {}
        for P in depths:
            E = expected_count(n, P, m[n]["logC"])
            row[f"{P:.2g}"] = (E, 1.0 - math.exp(-E))
        # location where E = 1 (median-ish first hit), bisect in log space
        lo, hi = 1e6, 1e40
        for _ in range(200):
            mid = math.exp((math.log(lo) + math.log(hi)) / 2)
            if expected_count(n, mid, m[n]["logC"]) < 1.0:
                lo = mid
            else:
                hi = mid
        row["E=1 at"] = f"{lo:.3g}"
        pr[n] = row
    return pr


# ------------------------------- gates -------------------------------------

def z1_tail_small(m):
    for n, d in m.items():
        if d["tail"] > 1e-3:
            return False, f"Z1 FAIL: singular tail bound {d['tail']:.2e} at n={n}"
    return True, "Z1 ok: singular-series tails < 1e-3 in ln"


def z2_quantile_validation(m):
    qs = quantiles(m)
    us = [u for (_, u) in qs.values()]
    detail = ", ".join(f"n={n}:E={E:.2f}/u={u:.2f}" for n, (E, u) in qs.items())
    # all six clustered above .98 or below .02 would mean the model is
    # off by an order of magnitude; scattered quantiles = healthy.
    bad = all(u > 0.98 for u in us) or all(u < 0.02 for u in us)
    if bad:
        return False, "Z2 FAIL: quantiles degenerate -- " + detail
    return True, "Z2 ok: " + detail


def z3_monotone_sanity(m):
    # E=1 locations must increase with n (harder target, deeper hit)
    pr = predictions(m)
    locs = [float(pr[n]["E=1 at"]) for n in OPEN_N]
    if any(b < a for a, b in zip(locs, locs[1:])):
        return False, f"Z3 FAIL: E=1 locations not increasing: {locs}"
    return True, f"Z3 ok: E=1 locations {['%.2g' % l for l in locs]}"


def main():
    print("building singular series (q < %d) ..." % Q_CUT)
    m = model()
    ok = True
    for g in (z1_tail_small, z2_quantile_validation, z3_monotone_sanity):
        good, msg = g(m)
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    pr = predictions(m)
    print("\npredictions (E[hits <= P], P(at least one)):")
    for n, row in pr.items():
        cells = "  ".join(f"{k}:{v[0]:.2f}/{v[1]:.2f}" if isinstance(v, tuple)
                          else f"{k} {v}" for k, v in row.items())
        print(f"  run>={n}: {cells}")
    with open("model_results.json", "w") as f:
        json.dump({"singular": {str(k): v for k, v in m.items()},
                   "quantiles": {str(k): v for k, v in quantiles(m).items()},
                   "predictions": {str(k): {kk: (vv if isinstance(vv, str) else list(vv))
                                            for kk, vv in row.items()}
                                   for k, row in pr.items()}}, f, indent=1)
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
