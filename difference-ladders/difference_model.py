"""difference_model.py -- the odds model for the difference ladders.

Bateman-Horn over the conditions of an index:

    E(F, n; a, c) = S(F, n) * integral_a^c  db * prod_{sieved p} 1/ln f_p(b)
                                             * prod_{composite p} (1 - P_p(b))

    S(F, n) = prod_q (1 - w(q,n)/q) / (1 - 1/q)^M,   M = nforms(F, n)

with w(q,n) the size of the SAME killed set the sieve is built from (the CPU
engine's primitive-root construction, which G3 pins to the oracle's walk), so
a wrong w would move the model and the engine together and the validation
below would catch it.  ln f_p(b) is (p - 1) ln b + ln p plus a correction
that vanishes as b grows, so index n of A216666 costs a factor of about
(prime(n) - 1) ln b over index n - 1 -- several hundred to over a thousand
here.  A216668's conditions at the non-Mersenne exponents ask for a
COMPOSITE value, which almost every b gives: each multiplies the density by
1 - P_p(b), the single-form Bateman-Horn chance that f_p(b) is prime
(S_p / ln f_p(b), S_p that form's own series) -- a few percent in all.

THE LINES.  Index n of either family is searched from a(n - 1), inclusive
(the ladders nest).  Those floors are what the validation draws use.

VALIDATION (G11), stated before any run.  E -- the expected number of hits
between the floor and the a(n) that actually occurred -- is Exp(1) if the
intensity is right.  The draws are the published terms that were searched
for: strictly above their predecessor and at or above MODEL_FLOOR = 100
(A216666's a(5)..a(8), A216668's a(4), a(6), a(7), a(8) and a(11)).  G11 is
a test of the LAW, not of a mean within a band: the pooled sum must not sit
in either 0.1% tail of its Gamma law, the quantiles 1 - exp(-E) must scatter
across the middle, and each family's mean must be inside (0.2, 4).

AND THE MODEL IS A FLOOR ELSEWHERE IN THIS REPOSITORY, NOT A FORECAST.
Earlier ladder projects landed their first occurrences at a pooled
0.5-2.5x of the medians.  The honest reading is the quantile table, not its
median.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from difference_reference import (FAMILIES, KNOWN, b_min, conditions,
                                  degree, family, floor_x, forms, frontier,
                                  nforms, nth_prime, term)

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_SMALL = list(primerange(2, 60))
_LS = {}
_LS1 = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# G11's pooled test: the sum of the E's must not sit in either tail beyond
# this probability under its Gamma(N, 1) law.
TAIL_P = 1e-3

# The validation draws: published terms strictly above their predecessor
# and at least this large (the asymptotic density is not asked to explain
# b = 1 or 2).
MODEL_FLOOR = 100

# How many indices model_results.json states per family: to A216666's a(12)
# (out of reach) and to A216668's a(24) (the day-long filter, p = 89).
N_AHEAD = {"A216666": 4, "A216668": 7}


def _w(q, n, fam):
    from difference_search import w_fast
    return w_fast(q, n, fam)


def log_singular(fam, n):
    """log S(F, n), over the SIEVED forms."""
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


def log_singular_one(p):
    """log S_p: the series of the single form f_p (it loses p - 1 residues
    at every prime q == 1 (mod p), none elsewhere)."""
    p = int(p)
    if p in _LS1:
        return _LS1[p]
    acc = 0.0
    for q in _PRIMES:
        w = (p - 1) if (q - 1) % p == 0 else 0
        acc += math.log(1 - w / q) - math.log(1 - 1.0 / q)
    _LS1[p] = acc
    return acc


def _ln_f(p, lv):
    """ln f_p(b) at ln b = lv (an array), exactly: p ln(b + 1) + ln(1 -
    (b/(b + 1))^p), the second term formed as log(-expm1(p log1p(-1/(b+1))))
    so it keeps its digits at b = 1e40."""
    b = np.exp(lv)
    u = p * np.log1p(-1.0 / (b + 1.0))
    return p * np.log1p(b) + np.log(-np.expm1(u))


def _density_curve(fam, n, v):
    """S / prod ln f_p(b) x prod over the composite conditions of
    (1 - P_p(b)), at the points b = v."""
    dens = np.full_like(v, math.exp(log_singular(fam, n)))
    lv = np.log(np.maximum(v, 1.0))
    for p, want in conditions(fam, n):
        lf = np.maximum(_ln_f(p, lv), 0.6931)
        if want:
            dens = dens / lf
        else:
            dens = dens * np.maximum(1.0 - math.exp(log_singular_one(p)) / lf, 0.0)
    return dens


def expected(fam, n, a, c, points=3000):
    """Expected number of b in [a, c] satisfying index n."""
    fam = family(fam)
    va, vc = float(max(int(a), b_min(fam))), float(int(c))
    if vc <= va:
        return 0.0
    v = np.logspace(math.log10(va), math.log10(vc), points)
    return float(np.trapezoid(_density_curve(fam, n, v), v))


def p_by(fam, n, floor_k, x):
    """P(a(n) has appeared by b = x), given it is at or above `floor_k`."""
    e = expected(fam, n, floor_k, x)
    return 1.0 - math.exp(-e) if e > 0 else 0.0


def quantile(fam, n, floor_k, p, hi=None):
    """The b at which P(a(n) found) reaches p, searching from `floor_k`."""
    if hi is None:
        from difference_search import K_CEIL
        hi = K_CEIL
    fam = family(fam)
    target = -math.log(1.0 - p)
    lo, c = float(max(int(floor_k), b_min(fam))), float(int(hi))
    if c <= lo or expected(fam, n, lo, c) < target:
        return None                        # not reachable below `hi`
    for _ in range(90):
        mid = math.sqrt(lo * c)
        if expected(fam, n, max(int(floor_k), b_min(fam)), mid) < target:
            lo = mid
        else:
            c = mid
    return math.sqrt(lo * c)


_SWEEP = {}


def _survival_table(fam, n, floor_k, hi, points=6000):
    """(ln b grid, cumulative E(floor, b), integral of exp(-E)): the model's
    survival curve for a(n) above `floor_k`, tabulated ONCE per (family,
    index, floor) -- the planner asks for it at dozens of segment widths,
    and an `expected` per question would be the 2.14 trap."""
    key = (fam, n, int(floor_k), float(hi))
    if key not in _SWEEP:
        a = float(max(int(floor_k), b_min(fam)))
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
        from difference_search import K_CEIL
        hi = K_CEIL
    floor_k, start_x, seg = int(floor_k), int(start_x), float(seg)
    lnv, cum, mean_excess = _survival_table(fam, int(n), floor_k, hi)
    count = (float(hi) - start_x) / seg
    if count > 2e6:
        return (floor_k - start_x) + mean_excess + seg / 2.0
    x = float(start_x) + seg * np.arange(0, int(count) + 1, dtype=np.float64)
    e = np.interp(np.log(np.maximum(x, max(floor_k, b_min(fam)))), lnv, cum)
    return float(seg * np.exp(-e).sum())


def floor_for(fam, n, frontier_x):
    """Where the search for a(n) starts: the frontier term, inclusive (the
    ladders nest), never below the family's least b."""
    fam, n = family(fam), int(n)
    return max(int(frontier_x), b_min(fam))


def plateau(fam, m):
    """True when index m's own condition asks for a COMPOSITE value (an
    A216668 non-Mersenne exponent): almost every b meets it -- the chance
    that f_p(b) is prime at p >= 11 and b >= 1e10 is under 1% -- so a(m)
    is a(m - 1) with that probability and the chain does not move."""
    return not conditions(fam, int(m))[-1][1]


def plan_floor(fam, n):
    """The floor a PLAN prices filter n from: a(n - 1) where it is known,
    else the model's median of it, chained up from the frontier (a filter
    the campaign will only reach after finds is priced where those finds
    are expected, not from the bottom of the line); an index whose own
    condition asks for a composite (`plateau`) does not move the chain."""
    fam, n = family(fam), int(n)
    top = frontier(fam)
    if n - 1 <= top:
        return floor_x(fam, n)
    x = term(fam, top)
    for m in range(top + 1, n):
        if plateau(fam, m):
            continue
        med = quantile(fam, m, x, 0.5)
        x = int(med) if med is not None else x
    return x


def density(fam, n, upto=60):
    """The fraction of b the primes under `upto` let through at index n --
    the density of the wheel to 59 over the WHOLE line (nothing is forced)."""
    d = 1.0
    for q in _SMALL:
        if q < upto:
            d *= 1 - _w(q, n, fam) / q
    return d


def predictions(fam, frontier_n, frontier_x, n_ahead=3, ceiling=None):
    """{n: {quantile: b depth}} for the next `n_ahead` indices, each from
    the frontier term (a later index's line starts where the earlier one's
    term will be, at the earliest at the frontier).  Derived from the live
    frontier on every call; the launcher caches it with
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


def chained_predictions(fam, n_ahead=None, ceiling=None):
    """{n: {quantile: b}} for the next indices, each searched from the
    model's MEDIAN of the one before (the plan's floors, plateaus kept):
    what the clock column of the README reads.  The first open index is
    from the frontier term itself."""
    fam = family(fam)
    n_ahead = N_AHEAD[fam] if n_ahead is None else int(n_ahead)
    top = frontier(fam)
    out = {}
    for n in range(top + 1, top + 1 + n_ahead):
        base = plan_floor(fam, n)
        qs = {}
        for name in QUANTILES:
            d = quantile(fam, n, base, _Q[name], hi=ceiling)
            if d is not None:
                qs[name] = d
        if qs:
            out[n] = {"from": float(base), **qs}
    return out


def independent_knowns(fam):
    """[(n, floor, a(n))] for the published terms the model is scored on:
    searched for, strictly above the predecessor and at least MODEL_FLOOR,
    from the predecessor."""
    fam = family(fam)
    out = []
    for n in sorted(KNOWN[fam]):
        x = KNOWN[fam][n]
        if x < MODEL_FLOOR or n == 1 or x <= KNOWN[fam][n - 1]:
            continue
        out.append((n, KNOWN[fam][n - 1], x))
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
    """E at each published term searched above MODEL_FLOOR is a draw of
    Exp(1) under a correct model: the pooled sum must not sit in either
    TAIL_P tail of its Gamma law, the quantiles 1 - exp(-E) must scatter
    across the middle, and each family's mean must be inside (0.2, 4)."""
    es, detail = [], []
    for fam in FAMILIES:
        fam_es = [expected(fam, n, lo, t) for n, lo, t in independent_knowns(fam)]
        es += fam_es
        mean = sum(fam_es) / len(fam_es)
        detail.append("%s %.2f over %d (%s)" % (
            fam, mean, len(fam_es), ", ".join("%.2f" % e for e in fam_es)))
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
    return True, ("G11 ok: E at the %d published terms searched above %d "
                  "sums to %.2f against a Gamma(%d, 1) law (P(sum <= it) = "
                  "%.3f, inside both %.0e tails), quantiles %.2f-%.2f -- per "
                  "family %s"
                  % (k, MODEL_FLOOR, tot, k, lo_tail, TAIL_P, min(us), max(us),
                     "; ".join(detail)))


def g12_monotone_and_sane():
    """Deeper terms are predicted deeper and finite; one new index adds at
    most (p - 1) killed residues per prime (p = prime(n + 1), and none when
    its condition asks for a composite) and moves the series by a sane
    factor; the wheel's density to 59 is in the weak regime; the two
    families are different problems."""
    rows = []
    for fam in FAMILIES:
        top = frontier(fam)
        base = term(fam, top)
        prev_med = float(base)
        for n in range(top + 1, top + 4):
            med = quantile(fam, n, base, 0.5)
            if med is None or med < prev_med:
                return False, (f"G12 FAIL: {fam} a({n}) median {med} is not "
                               f"above {prev_med:.4g}")
            if not 0 < math.exp(log_singular(fam, n)) < math.inf:
                return False, f"G12 FAIL: S({fam}, {n}) is not finite and positive"
            prev_med = med
        for n in range(4, top + 4):
            ratio = math.exp(log_singular(fam, n + 1) - log_singular(fam, n))
            if not 0.2 < ratio < 40:
                return False, (f"G12 FAIL: S({fam}) moves x{ratio:.2f} from "
                               f"index {n} to {n + 1}")
            p = nth_prime(n + 1)
            gain = degree(p) if p in forms(fam, n + 1) else 0
            for q in primerange(2, 400):
                a, b = _w(q, n, fam), _w(q, n + 1, fam)
                if not 0 <= b - a <= gain:
                    return False, (f"G12 FAIL: {fam} q = {q} gained {b - a} "
                                   f"killed residues from index {n + 1}")
        d = density(fam, top + 1)
        if not 1e-5 < d < 1e-1:
            return False, f"G12 FAIL: {fam} keeps {d:.3g} of b to 59"
        rows.append("%s S(%d) = %.3g, %.2g of the line to 59"
                    % (fam, top + 1, math.exp(log_singular(fam, top + 1)), d))
    if abs(log_singular("A216666", 9) - log_singular("A216668", 18)) < 0.5:
        return False, "G12 FAIL: two different ladders share a series"
    return True, ("G12 ok: predicted medians increase over the next three "
                  "indices of both families, one new index adds at most p - 1 "
                  "killed residues per prime and moves the series by 0.2-40x, "
                  "the wheel to 59 is weak (nothing forced), the families are "
                  "different problems -- " + "; ".join(rows))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    from difference_search import k_ceil, k_proof
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over the conditions of an index: (b+1)^p - "
                    "b^p prime for every p <= prime(n) (A216666), prime iff "
                    "2^p - 1 is prime (A216668: the non-Mersenne exponents "
                    "ask for a composite, each a factor 1 - P_p). w(q,n) is "
                    "the size of the sieve's own killed set.",
           "qmax": QMAX,
           "units": "every depth is a candidate for a(n), the published term "
                    "itself: b on both entries; A229073's m is b + 1",
           "floors": "a(n) is searched from a(n-1), inclusive: the ladders "
                     "nest. 'predictions' are from the frontier term; "
                     "'chained' from the model's median of the index before",
           "caveat": "the validation draws cannot pin a bias either way; "
                     "elsewhere in this repository first occurrences ran "
                     "0.5-2.5x of the medians. Read the whole quantile table.",
           "families": {}}
    for fam in FAMILIES:
        top = frontier(fam)
        preds = predictions(fam, top, term(fam, top), n_ahead=N_AHEAD[fam],
                            ceiling=k_ceil(top + 1, fam))
        chained = chained_predictions(fam, ceiling=k_ceil(top + 1, fam))
        es = {str(n): expected(fam, n, lo, t) for n, lo, t in independent_knowns(fam)}
        out["families"][fam] = {
            "forms": FAMILIES[fam]["forms"],
            "frontier": {"n": top, FAMILIES[fam]["term"]: term(fam, top),
                         "by": FAMILIES[fam]["frontier_by"]
                         + (" (a(12)..a(17) = a(11): this project's free "
                            "terms)" if fam == "A216668" else "")},
            "singular_series": {str(n): math.exp(log_singular(fam, n)) for n in preds},
            "density_to_59": {str(n): density(fam, n) for n in preds},
            "validation": {"E_at_known": es, "mean_E": sum(es.values()) / len(es),
                           "draws": len(es)},
            "predictions": {str(n): {q: float(v) for q, v in qs.items()}
                            for n, qs in preds.items()},
            "chained": {str(n): {q: float(v) for q, v in qs.items()}
                        for n, qs in chained.items()},
            "proof_crossing": {str(n): float(k_proof(n, fam)) for n in preds},
            "ceiling": float(k_ceil(top + 1, fam)),
            "also_settles": list(FAMILIES[fam]["also"])}
    with open(path + ".tmp", "w", newline="\n") as fh:
        json.dump(out, fh, indent=1)
    os.replace(path + ".tmp", path)
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
            for n, qs in sorted(d["chained"].items(), key=lambda z: int(z[0])):
                print("     chained a(%s) from %.3g: %s" % (
                    n, qs["from"], "  ".join("%s %.4g" % (q, qs[q]) for q in QUANTILES if q in qs)))

    _shutdown.graceful(_main)
