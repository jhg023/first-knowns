"""cyclotomic_model.py -- the odds model for the cyclotomic ladders.

Bateman-Horn over the forms of an index:

    E(F, n; a, b) = S(F, n) * integral_a^b  dx / prod_{forms} ln Phi_k(x)

    S(F, n) = prod_q (1 - w(q,S)/q) / (1 - 1/q)^M,   M = nforms(F, n)

with w(q,S) the size of the SAME killed set the sieve is built from (the
CPU engine's primitive-root construction, which G3 pins to the oracle's
walk), so a wrong w would move the model and the engine together and the
validation below would catch it.  ln Phi_k(x) is phi(k) ln x plus a
correction that vanishes as x grows, so index n of A070737 costs a factor
of about (phi(n) ln x) over index n - 1 -- a hundred to a few hundred here
-- and an index of A072942 weighs its divisor set's total degree, which is
n itself: a(96) is as far out as a(60) for a shorter divisor list.

THE TWO LINES.  A070737's index n is searched from a(n - 1), inclusive (the
ladder nests); every index of A072942 from x = 3.  Both floors are what the
validation draws use.

VALIDATION (G11), stated before any run.  E -- the expected number of hits
between the floor and the a(n) that actually occurred -- is Exp(1) if the
intensity is right.  The draws are the published terms that were searched
for: on A070737 strictly above their predecessor and above the exception
zone (a(n) >= K_FLOOR = 10^4), so a(5) to a(10); on A072942 every index to
99 whose term is at or above K_FLOOR, from x = 3.  G11 is a test of the
LAW, not of a mean within a band: the pooled sum must not sit in either
0.1% tail of its Gamma law, the quantiles 1 - exp(-E) must scatter across
the middle, and each family's mean must be inside (0.2, 4).

AND THE MODEL IS A FLOOR ELSEWHERE IN THIS REPOSITORY, NOT A FORECAST.
Earlier ladder projects landed their first occurrences at a pooled
0.7-2.5x of the medians (primorial-runs early, primorial-ladders late,
polynomial-runs and power-ladders on time).  The honest reading is the
quantile table, not its median.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from cyclotomic_reference import (FAMILIES, KNOWN, K_FLOOR, TARGETS, X_MIN,
                                  cyclotomic, degree, family, floor_x, forms,
                                  frontier, kind, nforms, open_indices, term)

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_SMALL = list(primerange(2, 60))
_LS = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# G11's pooled test: the sum of the E's must not sit in either tail beyond
# this probability under its Gamma(N, 1) law.
TAIL_P = 1e-3

# How many indices model_results.json states for the ladder: enough to
# reach past the last term a week of any campaign can buy.
N_AHEAD = 4


def _w(q, n, fam):
    from cyclotomic_search import w_fast
    return w_fast(q, n, fam)


def log_singular(fam, n):
    """log S(F, n)."""
    fam, n = family(fam), int(n)
    key = (fam, n)
    if key in _LS:
        return _LS[key]
    m, acc = nforms(fam, n), 0.0
    for q in _PRIMES:
        w = _w(q, n, fam)
        if w >= q:
            acc = -math.inf
            break
        acc += math.log(1 - w / q) - m * math.log(1 - 1.0 / q)
    _LS[key] = acc
    return acc


def _ln_phi(k, lv):
    """ln Phi_k(x) at ln x = lv (an array): phi(k) ln x plus the exact
    correction ln(1 + sum_{i < deg} c_i x^(i - deg)), which is under 1/x."""
    cs = cyclotomic(k)
    deg = len(cs) - 1
    corr = np.zeros_like(lv)
    for i, c in enumerate(cs[:-1]):
        if c:
            corr = corr + c * np.exp((i - deg) * lv)
    return deg * lv + np.log1p(corr)


def _density_curve(fam, n, v):
    """S / prod ln Phi_k(x) at the points x = v."""
    dens = np.full_like(v, math.exp(log_singular(fam, n)))
    lv = np.log(np.maximum(v, 3.0))
    for k in forms(fam, n):
        dens = dens / np.maximum(_ln_phi(k, lv), 0.6931)
    return dens


def expected(fam, n, a, c, points=3000):
    """Expected number of x in [a, c] satisfying index n."""
    fam = family(fam)
    va, vc = float(max(int(a), X_MIN)), float(int(c))
    if vc <= va:
        return 0.0
    v = np.logspace(math.log10(va), math.log10(vc), points)
    return float(np.trapezoid(_density_curve(fam, n, v), v))


def p_by(fam, n, floor_k, x):
    """P(a(n) has appeared by x), given it is at or above `floor_k`."""
    e = expected(fam, n, floor_k, x)
    return 1.0 - math.exp(-e) if e > 0 else 0.0


def quantile(fam, n, floor_k, p, hi=None):
    """The x at which P(a(n) found) reaches p, searching from `floor_k`."""
    if hi is None:
        from cyclotomic_search import K_CEIL
        hi = K_CEIL
    fam = family(fam)
    target = -math.log(1.0 - p)
    lo, c = float(max(int(floor_k), X_MIN)), float(int(hi))
    if c <= lo or expected(fam, n, lo, c) < target:
        return None                        # not reachable below `hi`
    for _ in range(90):
        mid = math.sqrt(lo * c)
        if expected(fam, n, max(int(floor_k), X_MIN), mid) < target:
            lo = mid
        else:
            c = mid
    return math.sqrt(lo * c)


_SWEEP = {}


def _survival_table(fam, n, floor_k, hi, points=6000):
    """(ln x grid, cumulative E(floor, x), integral of exp(-E)): the model's
    survival curve for a(n) above `floor_k`, tabulated ONCE per (family,
    index, floor) -- the planner asks for it at dozens of segment widths,
    and an `expected` per question would be the 2.14 trap."""
    key = (fam, n, int(floor_k), float(hi))
    if key not in _SWEEP:
        a = float(max(int(floor_k), X_MIN))
        v = np.logspace(math.log10(a), math.log10(float(hi)), points)
        dens = _density_curve(fam, n, v)
        cum = np.concatenate(
            [[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(v))])
        surv = np.exp(-cum)
        _SWEEP[key] = (np.log(v), cum, float(np.trapezoid(surv, v)))
    return _SWEEP[key]


def expected_sweep(fam, n, floor_k, start_x, seg, hi=None):
    """E[line swept before a(n) is CONFIRMED], when the sweep runs in whole
    segments of `seg` from `start_x` (<= floor_k: the segment boundary
    under the floor) and a find is only known to be the least once ITS
    segment closes -- so the segment holding a(n) is swept to its end.

        sum over segments k of  seg * P(a(n) >= start of segment k)

    For segments far shorter than the search the sum is the integral of
    the survival curve plus half a segment, which is what it returns past
    2e6 terms.
    """
    fam = family(fam)
    if hi is None:
        from cyclotomic_search import K_CEIL
        hi = K_CEIL
    floor_k, start_x, seg = int(floor_k), int(start_x), float(seg)
    lnv, cum, mean_excess = _survival_table(fam, int(n), floor_k, hi)
    count = (float(hi) - start_x) / seg
    if count > 2e6:
        return (floor_k - start_x) + mean_excess + seg / 2.0
    x = float(start_x) + seg * np.arange(0, int(count) + 1, dtype=np.float64)
    e = np.interp(np.log(np.maximum(x, max(floor_k, X_MIN))), lnv, cum)
    return float(seg * np.exp(-e).sum())


def floor_for(fam, n, frontier_x):
    """Where the search for a(n) starts: on A070737 the frontier term,
    inclusive (the ladder nests), never below X_MIN; on A072942 X_MIN --
    every index is its own line."""
    fam, n = family(fam), int(n)
    if kind(fam) != "ladder":
        return X_MIN
    return max(int(frontier_x), X_MIN)


def plan_floor(fam, n):
    """The floor a PLAN prices filter n from: on A070737 a(n - 1) where it
    is known, else the model's median of it, chained up from the frontier
    (a filter the campaign will only reach after finds is priced where
    those finds are expected, not from the bottom of the line); on A072942
    X_MIN, where every index's line starts."""
    fam, n = family(fam), int(n)
    if kind(fam) != "ladder":
        return X_MIN
    top = frontier(fam)
    if n - 1 <= top:
        return floor_x(fam, n)
    x = term(fam, top)
    for m in range(top + 1, n):
        med = quantile(fam, m, x, 0.5)
        x = int(med) if med is not None else x
    return x


def density(fam, n, upto=60):
    """The fraction of x the primes under `upto` let through at index n --
    the forced primes included (each keeps 1/q), so this is the density of
    the class-space wheel to 59 over the WHOLE line."""
    d = 1.0
    for q in _SMALL:
        if q < upto:
            d *= 1 - _w(q, n, fam) / q
    return d


def clock_weight(fam, n, floor_k=None):
    """median(a(n)) x the density of the campaign's class-space wheel to 59
    -- the density to 59 times 1/q for every FORCED prime above 59 (61 at
    n = 60, 73 at 72, 97 at 96), which the unit removes from the line: the
    expected candidates a device must test to reach the median at a fixed
    rate, what ranks A072942's open indices (TARGETS; G12 checks the
    order)."""
    from cyclotomic_search import forced_unit
    fam, n = family(fam), int(n)
    fl = plan_floor(fam, n) if floor_k is None else int(floor_k)
    med = quantile(fam, n, fl, 0.5)
    if med is None:
        return None
    dens = density(fam, n)
    for q in primerange(60, 130):
        if forced_unit(n, fam) % q == 0:
            dens /= q
    return (med - fl) * dens


def predictions(fam, frontier_n, frontier_x, n_ahead=3, ceiling=None):
    """{n: {quantile: x depth}} for the next `n_ahead` indices of A070737,
    each from the frontier term (a later index's line starts where the
    earlier one's term will be, at the earliest at the frontier).  Derived
    from the live frontier on every call; the launcher caches it with
    huntlib.rungs.LiveLadder (OPTIMIZATION.md 2.14)."""
    fam = family(fam)
    out = {}
    base = int(frontier_x)
    for n in range(frontier_n + 1, frontier_n + 1 + n_ahead):
        qs = {}
        if ceiling is not None and base >= ceiling:
            break
        for name in QUANTILES:
            d = quantile(fam, n, base, _Q[name], hi=ceiling)
            if d is not None and (ceiling is None or d < ceiling):
                qs[name] = d
        if qs:
            out[n] = qs
    return out


def predictions_index(fam, n, ceiling=None):
    """{n: {quantile: x depth}} for ONE index of A072942, from X_MIN: the
    ladder its campaign reads progress off while it hunts that index."""
    fam, n = family(fam), int(n)
    qs = {}
    for name in QUANTILES:
        d = quantile(fam, n, X_MIN, _Q[name], hi=ceiling)
        if d is not None and (ceiling is None or d < ceiling):
            qs[name] = d
    return {n: qs} if qs else {}


def independent_knowns(fam):
    """[(n, floor, a(n))] for the published terms the model is scored on:
    searched for and above the exception zone -- on A070737 strictly above
    the predecessor, from it; on A072942 from X_MIN."""
    fam = family(fam)
    out = []
    for n in sorted(KNOWN[fam]):
        x = KNOWN[fam][n]
        if x < K_FLOOR:
            continue
        if kind(fam) == "ladder":
            if n == 1 or x <= KNOWN[fam][n - 1]:
                continue
            out.append((n, KNOWN[fam][n - 1], x))
        else:
            out.append((n, X_MIN, x))
    return out


def gamma_cdf(s, k):
    """P(Gamma(k, 1) <= s) for an integer shape k: 1 - e^-s sum s^j/j!."""
    t, acc = 1.0, 1.0
    for j in range(1, k):
        t *= s / j
        acc += t
    return 1.0 - math.exp(-s) * acc


# --------------------------------- gates -----------------------------------

def g11_model_validates_on_knowns():
    """E at each published term searched above the exception zone is a draw
    of Exp(1) under a correct model: the pooled sum must not sit in either
    TAIL_P tail of its Gamma law, the quantiles 1 - exp(-E) must scatter
    across the middle, and each family's mean must be inside (0.2, 4)."""
    es, detail = [], []
    for fam in FAMILIES:
        fam_es = [expected(fam, n, lo, t) for n, lo, t in independent_knowns(fam)]
        es += fam_es
        mean = sum(fam_es) / len(fam_es)
        detail.append("%s %.2f over %d" % (fam, mean, len(fam_es)))
        if not 0.2 < mean < 4.0:
            return False, (f"G11 FAIL: {fam}'s mean E at its knowns is "
                           f"{mean:.2f} over {len(fam_es)} draws; under a "
                           f"correct model it is Exp(1) with mean 1")
    tot, k = sum(es), len(es)
    lo_tail = gamma_cdf(tot, k)
    if lo_tail < TAIL_P or 1.0 - lo_tail < TAIL_P:
        return False, (f"G11 FAIL: the {k} E's sum to {tot:.2f}, at "
                       f"P = {min(lo_tail, 1 - lo_tail):.2g} in a tail of "
                       f"Gamma({k}, 1) ({'; '.join(detail)})")
    us = [1.0 - math.exp(-e) for e in es]
    if min(us) > 0.5 or max(us) < 0.5:
        return False, (f"G11 FAIL: every quantile sits on one side of the "
                       f"median ({min(us):.2f}-{max(us):.2f}) -- biased")
    return True, ("G11 ok: E at the %d published terms searched above the "
                  "exception zone sums to %.2f against a Gamma(%d, 1) law "
                  "(P(sum <= it) = %.3f, inside both %.0e tails), quantiles "
                  "%.2f-%.2f -- per family %s"
                  % (k, tot, k, lo_tail, TAIL_P, min(us), max(us),
                     "; ".join(detail)))


def g12_monotone_and_sane():
    """Deeper A070737 terms are predicted deeper and finite; one new index
    adds at most phi(n + 1) killed residues per prime and moves the series
    by a sane factor; the wheel's density is in the middle regime; the two
    families are different problems; and A072942's TARGETS are in the
    model's own order of expected clock, cheapest first."""
    rows = []
    fam = "A070737"
    top = frontier(fam)
    prev_med = float(term(fam, top))
    base = term(fam, top)
    for n in range(top + 1, top + 4):
        med = quantile(fam, n, base, 0.5)
        if med is None or med <= prev_med:
            return False, (f"G12 FAIL: {fam} a({n}) median {med} is not "
                           f"above {prev_med:.4g}")
        if not 0 < math.exp(log_singular(fam, n)) < math.inf:
            return False, f"G12 FAIL: S({fam}, {n}) is not finite and positive"
        prev_med = med
    for n in range(4, top + 2):
        ratio = math.exp(log_singular(fam, n + 1) - log_singular(fam, n))
        if not 0.2 < ratio < 40:
            return False, (f"G12 FAIL: S({fam}) moves x{ratio:.2f} from "
                           f"index {n} to {n + 1}")
        for q in primerange(2, 400):
            a, b = _w(q, n, fam), _w(q, n + 1, fam)
            if not 0 <= b - a <= degree(n + 1):
                return False, (f"G12 FAIL: {fam} q = {q} gained {b - a} "
                               f"killed residues from index {n + 1}")
    d = density(fam, top + 1)
    if not 1e-9 < d < 1e-1:
        return False, f"G12 FAIL: {fam} keeps {d:.3g} of x to 59"
    rows.append("%s S(%d) = %.3g, %.2g of the line to 59"
                % (fam, top + 1, math.exp(log_singular(fam, top + 1)), d))
    fam = "A072942"
    weights = {}
    for n in TARGETS:
        if not 0 < math.exp(log_singular(fam, n)) < math.inf:
            return False, f"G12 FAIL: S({fam}, {n}) is not finite and positive"
        wgt = clock_weight(fam, n)
        if wgt is None:
            return False, f"G12 FAIL: {fam} a({n}) has no median under the ceiling"
        weights[n] = wgt
    order = tuple(sorted(weights, key=weights.get))
    if order != TARGETS:
        return False, (f"G12 FAIL: the model ranks A072942's open indices "
                       f"{order} by expected clock; TARGETS says {TARGETS}")
    if set(TARGETS) != set(open_indices(fam)):
        return False, "G12 FAIL: TARGETS is not the set of open indices"
    rows.append("%s clock weights (median x density to 59) %s"
                % (fam, ", ".join("a(%d) %.2g" % (n, weights[n]) for n in TARGETS)))
    if abs(log_singular("A070737", 12) - log_singular("A072942", 60)) < 0.5:
        return False, "G12 FAIL: two different ladders share a series"
    return True, ("G12 ok: predicted medians increase over the next three "
                  "indices of A070737, one new index adds at most phi(n + 1) "
                  "killed residues per prime and moves the series by 0.2-40x, "
                  "the wheel to 59 is in the middle regime, the families are "
                  "different problems, and A072942's TARGETS are the model's "
                  "order of expected clock -- " + "; ".join(rows))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    from cyclotomic_search import k_ceil, k_proof
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over the forms of an index: Phi_k(x), "
                    "k = 1..n (A070737, from a(n-1) inclusive); Phi(d,x), "
                    "d | n (A072942, each index from x = 3). w(q,S) is the "
                    "size of the sieve's own killed set.",
           "qmax": QMAX,
           "units": "every depth is a candidate for a(n), the published term "
                    "itself: x on both entries",
           "floors": "A070737's a(n) is searched from a(n-1), inclusive: the "
                     "ladder nests (a(3) = a(4) = 6); every index of A072942 "
                     "from x = 3",
           "caveat": "the validation draws cannot pin a bias either way; "
                     "elsewhere in this repository first occurrences ran "
                     "0.7-2.5x of the medians. Read the whole quantile table.",
           "families": {}}
    fam = "A070737"
    top = frontier(fam)
    preds = predictions(fam, top, term(fam, top), n_ahead=N_AHEAD,
                        ceiling=k_ceil(top + 1, fam))
    es = {str(n): expected(fam, n, lo, t) for n, lo, t in independent_knowns(fam)}
    out["families"][fam] = {
        "forms": FAMILIES[fam]["forms"],
        "frontier": {"n": top, FAMILIES[fam]["term"]: term(fam, top),
                     "by": FAMILIES[fam]["frontier_by"]},
        "singular_series": {str(n): math.exp(log_singular(fam, n)) for n in preds},
        "density_to_59": {str(n): density(fam, n) for n in preds},
        "validation": {"E_at_known": es, "mean_E": sum(es.values()) / len(es),
                       "draws": len(es)},
        "predictions": {str(n): {q: float(v) for q, v in qs.items()}
                        for n, qs in preds.items()},
        "proof_crossing": {str(n): float(k_proof(n, fam)) for n in preds},
        "ceiling": float(k_ceil(top + 1, fam)),
        "also_settles": list(FAMILIES[fam]["also"])}
    fam = "A072942"
    preds = {}
    for n in TARGETS:
        preds.update(predictions_index(fam, n, ceiling=k_ceil(n, fam)))
    es = {str(n): expected(fam, n, lo, t) for n, lo, t in independent_knowns(fam)}
    out["families"][fam] = {
        "forms": FAMILIES[fam]["forms"],
        "open_indices": list(TARGETS),
        "order": "TARGETS: the open indices in the model's order of expected "
                 "clock (median x density to 59), cheapest first",
        "frontier": {"known_to": 99, "by": FAMILIES[fam]["frontier_by"]},
        "singular_series": {str(n): math.exp(log_singular(fam, n)) for n in preds},
        "density_to_59": {str(n): density(fam, n) for n in preds},
        "clock_weight": {str(n): clock_weight(fam, n) for n in TARGETS},
        "validation": {"E_at_known": es, "mean_E": sum(es.values()) / len(es),
                       "draws": len(es)},
        "predictions": {str(n): {q: float(v) for q, v in qs.items()}
                        for n, qs in preds.items()},
        "proof_crossing": {str(n): float(k_proof(n, fam)) for n in TARGETS},
        "ceiling": float(k_ceil(60, fam))}
    with open(path, "w", newline="\n") as fh:
        json.dump(out, fh, indent=1)
    return out


GATES = [g11_model_validates_on_knowns, g12_monotone_and_sane]

if __name__ == "__main__":
    import pathlib as _pl
    import sys as _s
    _s.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown

    def _main():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
        out = write_model_results()
        for fam, d in out["families"].items():
            print("  %s; validation mean E %.2f over %d:"
                  % (fam, d["validation"]["mean_E"], d["validation"]["draws"]))
            for n, e in sorted(d["validation"]["E_at_known"].items(), key=lambda z: int(z[0])):
                print("     E a(%s) = %.2f" % (n, e))
            for n, qs in sorted(d["predictions"].items(), key=lambda z: int(z[0])):
                print("     a(%s): %s   (to 59: %.3g)" % (
                    n, "  ".join("%s %.4g" % (q, qs[q]) for q in QUANTILES if q in qs),
                    d["density_to_59"][n]))
        if "clock_weight" in out["families"]["A072942"]:
            cw = out["families"]["A072942"]["clock_weight"]
            print("  A072942 by clock weight:", sorted(cw, key=lambda n: cw[n]))

    _shutdown.graceful(_main)
