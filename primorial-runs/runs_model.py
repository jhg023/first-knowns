"""The odds model for the exact-run primorial shift ladders.

Bateman-Horn over the forms of an index, the singular series computed from
the same killed sets the sieve is built from:

    lambda_n(x) = S(F, n) / (ln x * ln(x + c(1)) * ... * ln(x + c(n)))

is the intensity of primes x whose run is AT LEAST n.  The entries ask for
a run of EXACTLY n, so the intensity of a(n)'s event is

    lambda_n(x) - lambda_(n+1)(x)

-- at least n, less those that go on -- and the expected number of primes
with a run of exactly n in [a, c] is the integral of that.  Every index's
line starts at the bottom (x = 2): the sequences are not monotone, so no
term is a floor for another.

The shifts are large (psq(15) is 3.8e35 against terms near 1e16), so each
logarithm is taken of the VALUE x + c, not of x: for the squared families
most of the factors are constants set by the shifts, and that is what makes
their terms come so much later than A257466's at the same index.

VALIDATION (G11): E at each published term at or above the exception zone
is a draw of Exp(1) under a correct model.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from runs_reference import (FAMILIES, KNOWN, K_FLOOR, constants, family,
                            floor_x, frontier)

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_SMALL = list(primerange(2, 60))
_LS = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# G11's pooled test: the sum of the E's must not sit in either tail beyond
# this probability under its Gamma(N, 1) law.
TAIL_P = 1e-3

# How many indices model_results.json states per family: enough to reach
# past the last term a week of either campaign can buy.
N_AHEAD = 6


def shift(fam, n):
    """L: the integrals run over v = x - L.  0 here: the smallest value is
    x itself."""
    return max(0, -min(constants(fam, n)))


def log_singular(fam, n):
    """log S(F, n)."""
    fam, n = family(fam), int(n)
    key = (fam, n)
    if key in _LS:
        return _LS[key]
    cs = constants(fam, n)
    m, acc = len(cs), 0.0
    for q in _PRIMES:
        ks = {(-c) % q for c in cs}
        if len(ks) >= q:
            acc = -math.inf
            break
        acc += math.log(1 - len(ks) / q) - m * math.log(1 - 1.0 / q)
    _LS[key] = acc
    return acc


def _atleast_curve(fam, n, v, L):
    """S * prod 1/ln(value) at x = v + L: the intensity of a run of AT
    LEAST n."""
    dens = np.full_like(v, math.exp(log_singular(fam, n)))
    for c in constants(fam, n):
        dens = dens / np.log(np.maximum(v + float(L + c), 3.0))
    return dens


def _density_curve(fam, n, v, L):
    """The intensity of a run of EXACTLY n: at least n, less at least
    n + 1.  Never negative (the heuristic is loose at the very bottom of
    the line, where it is not used)."""
    return np.maximum(_atleast_curve(fam, n, v, L)
                      - _atleast_curve(fam, n + 1, v, L), 0.0)


def expected(fam, n, a, c, points=3000):
    """Expected number of primes x in [a, c] whose run is EXACTLY n."""
    fam = family(fam)
    L = shift(fam, n)
    va, vc = float(max(int(a) - L, 2)), float(int(c) - L)
    if vc <= va:
        return 0.0
    v = np.logspace(math.log10(va), math.log10(vc), points)
    return float(np.trapezoid(_density_curve(fam, n, v, L), v))


def p_by(fam, n, floor_k, x):
    """P(a(n) has appeared by x), given it is at or above `floor_k`."""
    e = expected(fam, n, floor_k, x)
    return 1.0 - math.exp(-e) if e > 0 else 0.0


def quantile(fam, n, floor_k, p, hi=None):
    """The x at which P(a(n) found) reaches p, searching from `floor_k`."""
    if hi is None:
        from runs_search import K_CEIL
        hi = K_CEIL
    fam = family(fam)
    L = shift(fam, n)
    target = -math.log(1.0 - p)
    lo, c = float(max(int(floor_k) - L, 2)), float(int(hi) - L)
    if c <= lo or expected(fam, n, lo + L, c + L) < target:
        return None                        # not reachable below `hi`
    for _ in range(90):
        mid = math.sqrt(lo * c)
        if expected(fam, n, max(int(floor_k), 2), mid + L) < target:
            lo = mid
        else:
            c = mid
    return math.sqrt(lo * c) + L


_SWEEP = {}


def _survival_table(fam, n, floor_k, hi, points=6000):
    """(ln v grid, cumulative E(floor, v + L), integral of exp(-E)): the
    model's survival curve for a(n) above `floor_k`, tabulated ONCE per
    (family, index, floor) -- the planner asks for it at dozens of segment
    widths, and an `expected` per question would be the 2.14 trap."""
    key = (fam, n, int(floor_k), float(hi))
    if key not in _SWEEP:
        L = shift(fam, n)
        a = float(max(int(floor_k) - L, 2))
        v = np.logspace(math.log10(a), math.log10(float(hi) - L), points)
        dens = _density_curve(fam, n, v, L)
        cum = np.concatenate(
            [[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(v))])
        surv = np.exp(-cum)
        _SWEEP[key] = (np.log(v), cum, float(np.trapezoid(surv, v)), L)
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
        from runs_search import K_CEIL
        hi = K_CEIL
    floor_k, start_x, seg = int(floor_k), int(start_x), float(seg)
    lnv, cum, mean_excess, L = _survival_table(fam, int(n), floor_k, hi)
    count = (float(hi) - start_x) / seg
    if count > 2e6:
        return (floor_k - start_x) + mean_excess + seg / 2.0
    x = float(start_x) + seg * np.arange(0, int(count) + 1, dtype=np.float64)
    e = np.interp(np.log(np.maximum(x - L, max(floor_k - L, 2))), lnv, cum)
    return float(seg * np.exp(-e).sum())


def floor_for(fam, n, frontier_x=0):
    """Where the search for a(n) starts: the bottom of the line, 2, at
    every index (`frontier_x` is ignored: no term is a floor for another)."""
    return int(floor_x(family(fam), int(n)))


def density(fam, n, upto=60):
    """The fraction of x the primes under `upto` let through at index n."""
    cs = constants(fam, n)
    d = 1.0
    for q in _SMALL:
        if q < upto:
            d *= 1 - len({(-c) % q for c in cs}) / q
    return d


def predictions_open(fam, indices, ceiling=None):
    """{n: {quantile: x depth}} for the given open indices, each from the
    bottom of the line."""
    fam = family(fam)
    out = {}
    for n in indices:
        qs = {}
        base = floor_for(fam, n)
        for name in QUANTILES:
            d = quantile(fam, n, base, _Q[name], hi=ceiling)
            if d is not None and (ceiling is None or d < ceiling):
                qs[name] = d
        if qs:
            out[int(n)] = qs
    return out


def predictions(fam, frontier_n, frontier_x=0, n_ahead=3, ceiling=None):
    """{n: {quantile: x depth}} for the `n_ahead` indices above
    `frontier_n`.  Derived from the live frontier on every call; the
    launcher caches it with huntlib.rungs.LiveLadder (OPTIMIZATION.md
    2.14)."""
    return predictions_open(fam, range(frontier_n + 1, frontier_n + 1 + n_ahead),
                            ceiling=ceiling)


def independent_knowns(fam):
    """[(n, floor, a(n))] for the published terms the model is scored on:
    every known term above the exception zone, from the bottom of the
    line."""
    fam = family(fam)
    return [(n, floor_for(fam, n), KNOWN[fam][n]) for n in sorted(KNOWN[fam])
            if KNOWN[fam][n] >= K_FLOOR]


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
                  "%.2f-%.2f -- per family %s (each term scored as the first "
                  "prime with a run of EXACTLY its index, from the bottom of "
                  "the line)"
                  % (k, tot, k, lo_tail, TAIL_P, min(us), max(us),
                     "; ".join(detail)))


def g12_monotone_and_sane():
    """Deeper terms are predicted deeper and finite, one new index adds at
    most one killed residue per prime and moves the series by a sane
    factor, the exact-run intensity is the at-least intensity less the next
    one's, and the families are different problems."""
    rows = []
    for fam in FAMILIES:
        top = frontier(fam)
        prev_med = 0.0
        for n in range(top + 1, top + 5):
            med = quantile(fam, n, floor_for(fam, n), 0.5)
            if med is None or med <= prev_med:
                return False, (f"G12 FAIL: {fam} a({n}) median {med} is not "
                               f"above {prev_med:.4g}")
            if not 0 < math.exp(log_singular(fam, n)) < math.inf:
                return False, f"G12 FAIL: S({fam}, {n}) is not finite and positive"
            v = np.array([med])
            a0, a1 = _atleast_curve(fam, n, v, 0)[0], _atleast_curve(fam, n + 1, v, 0)[0]
            ex = _density_curve(fam, n, v, 0)[0]
            if not (0 < a1 < a0 and abs(ex - (a0 - a1)) <= 1e-12 * a0):
                return False, (f"G12 FAIL: {fam} n = {n}: exact {ex:.3g} is not "
                               f"at-least {a0:.3g} less the next {a1:.3g}")
            prev_med = med
        for n in range(6, top + 1):
            ratio = math.exp(log_singular(fam, n + 1) - log_singular(fam, n))
            if not 1.0 < ratio < 40:
                return False, (f"G12 FAIL: S({fam}) moves x{ratio:.2f} from "
                               f"index {n} to {n + 1}")
            a, b = constants(fam, n), constants(fam, n + 1)
            for q in primerange(2, 400):
                ka, kb = {(-c) % q for c in a}, {(-c) % q for c in b}
                if len(kb) - len(ka) not in (0, 1) or not ka <= kb:
                    return False, (f"G12 FAIL: {fam} q = {q} gained more than "
                                   f"one killed residue from one new index")
        d = density(fam, top + 1)
        if not 1e-6 < d < 1e-2:
            return False, f"G12 FAIL: {fam} keeps {d:.3g} of x to 59"
        rows.append("%s S(%d) = %.3g, %.2g of x to 59"
                    % (fam, top + 1, math.exp(log_singular(fam, top + 1)), d))
    ls = [log_singular(f, 12) for f in FAMILIES]
    if len({round(x, 6) for x in ls}) != len(ls):
        return False, "G12 FAIL: two families have the same series at n = 12"
    return True, ("G12 ok: predicted medians increase over the next four "
                  "indices of every family, the exact-run intensity is the "
                  "at-least intensity less the next index's and positive at "
                  "each median, one new index adds 0 or 1 killed residues per "
                  "prime and moves the series by 1-40x, and the three families "
                  "are different problems -- " + "; ".join(rows))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    from runs_search import k_ceil, k_proof
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over the forms of index n: p and "
                    "p + c(1), ..., p + c(n) with c = pps (A257466), psq "
                    "(A257467) or pssq (A258035), each logarithm taken of the "
                    "value p + c; the intensity of a run of EXACTLY n is the "
                    "intensity of at least n less that of at least n + 1. "
                    "w(q,n,F) is the size of the sieve's own killed set "
                    "{-c mod q}.",
           "qmax": QMAX,
           "units": "every depth is a candidate for a(n), the published "
                    "term itself: the prime p",
           "floors": "every index is searched from the bottom of the line, "
                     "p = 2: the sequences are not monotone",
           "caveat": "the validation draws cannot pin a bias either way; "
                     "elsewhere in this repository first occurrences ran "
                     "1.2-2.5x past their medians. Read the whole quantile "
                     "table.",
           "families": {}}
    for fam in FAMILIES:
        top = frontier(fam)
        preds = predictions(fam, top, 0, n_ahead=N_AHEAD,
                            ceiling=k_ceil(top + 1, fam))
        es = {str(n): expected(fam, n, lo, t) for n, lo, t in independent_knowns(fam)}
        out["families"][fam] = {
            "forms": FAMILIES[fam]["forms"],
            "frontier": {"n": top, FAMILIES[fam]["term"]: KNOWN[fam][top],
                         "by": FAMILIES[fam]["frontier_by"]},
            "singular_series": {str(n): math.exp(log_singular(fam, n))
                                for n in preds},
            "density_to_59": {str(n): density(fam, n) for n in preds},
            "floor": {str(n): int(floor_for(fam, n)) for n in preds},
            "validation": {"E_at_known": es,
                           "mean_E": sum(es.values()) / len(es),
                           "draws": len(es)},
            "predictions": {str(n): {q: float(v) for q, v in qs.items()}
                            for n, qs in preds.items()},
            "proof_crossing": float(k_proof(top + 1, fam)),
            "ceiling": float(k_ceil(top + 1, fam))}
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
            print("  %s, frontier a(%d) = %d; validation mean E %.2f over %d:"
                  % (fam, d["frontier"]["n"], d["frontier"][FAMILIES[fam]["term"]],
                     d["validation"]["mean_E"], d["validation"]["draws"]))
            for n, e in sorted(d["validation"]["E_at_known"].items(), key=lambda z: int(z[0])):
                print("     E a(%s) = %.2f" % (n, e))
            for n, qs in sorted(d["predictions"].items(), key=lambda z: int(z[0])):
                print("     a(%s): %s" % (
                    n, "  ".join("%s %.4g" % (q, qs[q]) for q in QUANTILES if q in qs)))

    _shutdown.graceful(_main)
