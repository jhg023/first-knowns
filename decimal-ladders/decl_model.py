"""The odds model for the decimal ladders -- Bateman-Horn over linear forms.

    A(F, n) = least x with 10^j*x + 1 prime for every j in J(F, n)

For a fixed n the forms f_j(x) = 10^j*x + 1 are distinct, irreducible and
have no fixed prime divisor (proved in decl_reference: residue 0 is never
killed), so Bateman-Horn puts the density of x at which all of them are
simultaneously prime at

    S(F, n) / prod_j log(10^j*x + 1),

    S(F, n) = prod_q  (1 - w(q,n,F)/q) / (1 - 1/q)^|J|

with w(q,n,F) = #distinct(J mod ord_q(10)) -- the killed count PROVED in
decl_reference, the quantity the sieve is built from.  A wrong w would move
the model and the engine together, and the validation against the known
terms would catch it.

EVERYTHING HERE IS IN x, WHICH IS THE PUBLISHED TERM (A305740's k,
A153431's m).  No conversion anywhere: the campaign cursor, the quantiles
and the OEIS entry are the same number.  `floor_for` is the monotonicity
bound -- the previous term -- and nothing else.

THE SERIES IS LARGE AND IT GROWS WITH n, like every ladder here: the
primes with 10 as a primitive root kill |J| residues until they are
FORCED, and the small-order primes (3, 11, 37, 101, 41, 271, 13, 7, 73,
137, ...) saturate at their order, so each of them contributes a factor
growing like (1 - 1/q)^-|J|.  S(A305740, 18) = 4.6e9, S(A153431, 17) =
1.8e9.

VALIDATION (gate G11).  E(F, n) -- the expected number of hits the model
puts between the previous term and the one that actually occurred -- must
scatter around 1 on the knowns.  One vote per condition: a term equal to its
predecessor (a rider: A305740's a(5) = a(4), A153431's a(7) = a(6)) was
never searched for and is excluded, and so is everything below n = 6, inside
the exception zone.  Seven draws per family.

AND THE MODEL IS A FLOOR, NOT A FORECAST.  The ladder projects before this
one landed their scored finds at 1.9-2.5x their medians while every census
showed the modelled INTENSITY right to a percent or two; factorial-ladders'
14 draws averaged E = 1.10.  Mean count right, first occurrence noisy:
budget 2-3x the median below before expecting a term.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from decl_reference import (FAMILIES, KNOWN, PUBLISHED_BOUNDS, exponents,
                            family, j0, nforms, w_count)

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_LS = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# The knowns that were SEPARATELY SEARCHED FOR: strictly above their
# predecessor (so not a rider) and clear of the exception zone.
VALIDATE_FROM = 6


def independent_knowns(fam):
    """[(n, prev_x, term_x)] for the terms this model may be scored on."""
    fam = family(fam)
    out = []
    for n in sorted(KNOWN[fam]):
        if n < VALIDATE_FROM or n - 1 not in KNOWN[fam]:
            continue
        prev, t = KNOWN[fam][n - 1], KNOWN[fam][n]
        if t > prev:
            out.append((n, prev, t))
    return out


def log_singular(fam, n):
    """log S(F, n), cached per (family, n)."""
    fam = family(fam)
    n = int(n)
    key = (fam, n)
    if key in _LS:
        return _LS[key]
    k = nforms(fam, n)
    acc = 0.0
    for q in _PRIMES:
        ww = w_count(q, n, fam)
        if ww >= q:                       # proved impossible; assert anyway
            _LS[key] = -math.inf
            return -math.inf
        acc += math.log(1 - ww / q) - k * math.log(1 - 1.0 / q)
    _LS[key] = acc
    return acc


def _log_dens(fam, n, t):
    """log of the Bateman-Horn density at the points t (array)."""
    out = np.full_like(t, log_singular(fam, n))
    for j in exponents(fam, n):
        out -= np.log(np.log(np.maximum(10.0 ** j * t + 1.0, 3.0)))
    return out


def expected(fam, n, a, c, points=3000):
    """Expected number of x in [a, c] with every form of (F, n) prime."""
    fam = family(fam)
    a, c = float(max(a, 2.0)), float(c)
    if c <= a:
        return 0.0
    t = np.logspace(math.log10(a), math.log10(c), points)
    return float(np.trapezoid(np.exp(_log_dens(fam, n, t)), t))


def p_by(fam, n, floor_x, x):
    """P(a(n) has appeared by x), given it is known to exceed `floor_x`."""
    e = expected(fam, n, floor_x, x)
    return 1.0 - math.exp(-e) if e > 0 else 0.0


def quantile(fam, n, floor_x, p, hi=None):
    """The x at which P(a(n) found) reaches p, searching from `floor_x`."""
    if hi is None:
        from huntlib.ceiling import K_CEIL
        hi = K_CEIL
    target = -math.log(1.0 - p)
    lo, c = float(max(floor_x, 2.0)), float(hi)
    if expected(fam, n, lo, c) < target:
        return None                        # not reachable below `hi`
    for _ in range(90):
        mid = math.sqrt(lo * c)
        if expected(fam, n, max(floor_x, 2.0), mid) < target:
            lo = mid
        else:
            c = mid
    return math.sqrt(lo * c)


def floor_for(fam, n, frontier_x):
    """Where the search for a(n) starts: monotonicity alone (the conditions
    nest, so a(n) >= a(n-1)); a bound somebody publishes later goes in
    PUBLISHED_BOUNDS and is credited to them, not to the model."""
    fam = family(fam)
    return max(int(frontier_x), int(PUBLISHED_BOUNDS[fam].get(n, 0)))


_PROJ = {}


def projected_floor(fam, n):
    """The floor the PLANNER assumes for filter n: the published term at
    the open index, and past it the chain of modelled medians from the
    published frontier.  A pure function of (family, n) -- the plan must be
    the same on every resume -- and deliberately not the campaign's actual
    finds, which would make the plan (and the period a stored cursor counts)
    depend on the run."""
    fam = family(fam)
    n = int(n)
    top = max(KNOWN[fam])
    if n <= top + 1:
        return KNOWN[fam][min(top, max(n - 1, min(KNOWN[fam])))]
    key = (fam, n)
    if key not in _PROJ:
        prev = projected_floor(fam, n - 1)
        _PROJ[key] = int(quantile(fam, n - 1, prev, 0.5))
    return _PROJ[key]


_SWEEP = {}


def _survival_table(fam, n, floor_x, hi, points=6000):
    """(ln x grid, cumulative E(floor, x), integral of exp(-E)): the
    model's survival curve for a(n) above `floor_x`, tabulated ONCE per
    (family, index, floor) -- a planner asks for it at dozens of segment
    widths, and an `expected` per question would be the 2.14 trap."""
    key = (family(fam), int(n), int(floor_x), float(hi))
    if key not in _SWEEP:
        a = float(max(floor_x, 2.0))
        t = np.logspace(math.log10(a), math.log10(float(hi)), points)
        dens = np.exp(_log_dens(fam, n, t))
        cum = np.concatenate(
            [[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(t))])
        surv = np.exp(-cum)
        _SWEEP[key] = (np.log(t), cum, float(np.trapezoid(surv, t)))
    return _SWEEP[key]


def expected_sweep(fam, n, floor_x, start_x, seg, hi=None):
    """E[line swept before a(n) is CONFIRMED], when the sweep runs in whole
    segments of `seg` from `start_x` (<= floor_x: the segment boundary under
    the floor) and a find is only known to be the least once ITS segment
    closes -- so the segment holding a(n) is swept to its end:

        sum over segments k of  seg * P(a(n) >= start of segment k)

    For segments far shorter than the search the sum is the integral of the
    survival curve plus half a segment, which is what it returns past 2e6
    terms.  (The launcher CARRIES the classified line past a find into the
    next filter, so the over-sweep is not thrown away here as it is in
    clique-ladders -- but it is done at this filter's rate, not the next
    one's, and at the last reachable filter it is never used, so the planner
    prices it as the clock to a confirmed find: OPTIMIZATION_LOG.md.)
    """
    fam = family(fam)
    if hi is None:
        from huntlib.ceiling import K_CEIL
        hi = K_CEIL
    floor_x, start_x, seg = float(floor_x), float(start_x), float(seg)
    lnt, cum, mean_excess = _survival_table(fam, int(n), floor_x, hi)
    count = (float(hi) - start_x) / seg
    if count > 2e6:
        return (floor_x - start_x) + mean_excess + seg / 2.0
    x = start_x + seg * np.arange(0, int(count) + 1, dtype=np.float64)
    e = np.interp(np.log(np.maximum(x, max(floor_x, 2.0))), lnt, cum)
    return float(seg * np.exp(-e).sum())


def predictions(fam, frontier_n, frontier_x, n_ahead=3, ceiling=None):
    """{n: {quantile: x depth}} for the next `n_ahead` open terms.

    Derived from the LIVE frontier on every call (a rung retires with its
    term); the launcher caches the result on the frontier with
    huntlib.rungs.LiveLadder, because a call is ~1,000 numerical integrals
    and the segment loop may not pay that (OPTIMIZATION.md 2.14).
    """
    fam = family(fam)
    out = {}
    base = floor_for(fam, frontier_n + 1, frontier_x)
    for n in range(frontier_n + 1, frontier_n + 1 + n_ahead):
        qs = {}
        for name in QUANTILES:
            d = quantile(fam, n, base, _Q[name])
            if d is not None and (ceiling is None or d < ceiling):
                qs[name] = d
        if qs:
            out[n] = qs
        # the next term's search starts, at the earliest, where this one's
        # median puts it -- the chained floor the README's table uses
        if "median" not in qs:
            break
        base = qs["median"]
    return out


# --------------------------------- gates -----------------------------------

def g11_model_validates_on_knowns():
    """E at each independently-searched known must scatter around 1.

    The window starts at the PREVIOUS term, because that is what was known
    when the search for this one began.  Scored per family and pooled.
    """
    es, detail = [], []
    for fam in FAMILIES:
        fam_es = []
        for n, prev, t in independent_knowns(fam):
            e = expected(fam, n, floor_for(fam, n, prev), t)
            es.append(e)
            fam_es.append(e)
        detail.append("%s mean %.2f (%d)" % (fam, sum(fam_es) / len(fam_es),
                                             len(fam_es)))
        if not 0.2 < sum(fam_es) / len(fam_es) < 4.0:
            return False, (f"G11 FAIL: {fam}'s mean E at its knowns is "
                           f"{sum(fam_es) / len(fam_es):.2f} over "
                           f"{len(fam_es)} draws; under a correct model it is "
                           f"Exp(1) with mean 1")
    lo, hi = min(es), max(es)
    mean = sum(es) / len(es)
    if not 0.5 < mean < 2.2:
        return False, (f"G11 FAIL: pooled mean E at the knowns is {mean:.2f}; "
                       f"under a correct model it is Exp(1) with mean 1 "
                       f"({'; '.join(detail)})")
    if lo > 0.5 or hi < 1.5:
        return False, (f"G11 FAIL: the knowns do not scatter around E = 1 "
                       f"(spread {lo:.2f}-{hi:.2f}) -- biased, and it may not "
                       f"be used to plan ({'; '.join(detail)})")
    return True, ("G11 ok: E at the %d independently-searched knowns is mean "
                  "%.2f against the Exp(1) mean of 1, spread %.2f-%.2f -- %s "
                  "(riders excluded: one vote per condition)"
                  % (len(es), mean, lo, hi, "; ".join(detail)))


def g12_monotone_and_sane():
    """Deeper terms predicted deeper; the series grows with n by the
    mechanism the docstring states; the nesting holds in the model too
    (A153431's condition at n is A305740's plus x + 1, so its density is
    lower at every x and its median higher from a common floor)."""
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        prev_med = 0.0
        for n in range(top + 1, top + 5):
            med = quantile(fam, n, floor_for(fam, n, KNOWN[fam][top]), 0.5)
            if med is None:
                return False, f"G12 FAIL: {fam} a({n}) has no median"
            if med <= prev_med:
                return False, (f"G12 FAIL: {fam} a({n}) median {med:.4g} not "
                               f"above {prev_med:.4g}")
            prev_med = med
        for n in range(max(j0(fam), 6), 24):
            ratio = math.exp(log_singular(fam, n + 1) - log_singular(fam, n))
            if ratio <= 1.0:
                return False, (f"G12 FAIL: {fam} S({n+1}) is not above S({n})")
            # every prime gains 0 or 1 killed residues from one more form,
            # and 0 exactly when |J| has already reached its order
            for q in primerange(3, 2000):
                if q == 5:
                    continue
                dw = w_count(q, n + 1, fam) - w_count(q, n, fam)
                if dw not in (0, 1):
                    return False, (f"G12 FAIL: {fam} q = {q} gained {dw} "
                                   f"residues from one form")
    # the nesting, in the model: from the same floor, A153431's density is
    # below A305740's at every x (one more form, and every kill set a
    # superset), so its median is higher
    for n in (13, 15, 17):
        fl = 10 ** 14
        a = quantile("A305740", n, fl, 0.5)
        b = quantile("A153431", n, fl, 0.5)
        if not b > a:
            return False, (f"G12 FAIL: at n = {n} from a common floor the "
                           f"A153431 median {b:.4g} is not above A305740's "
                           f"{a:.4g}")
    s1 = math.exp(log_singular("A305740", 18))
    s2 = math.exp(log_singular("A153431", 17))
    return True, ("G12 ok: predicted medians increase with n over the next "
                  "four open terms of both families; the series grows at every "
                  "n from 6 to 24 on both, each prime gaining 0 or 1 killed "
                  "residues per form (0 once |J| reaches its order); from a "
                  "common floor A153431's median is above A305740's at "
                  "n = 13, 15, 17 (the nesting); S(A305740, 18) = %.3g, "
                  "S(A153431, 17) = %.3g" % (s1, s2))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    from decl_search import forced_unit, k_ceil, k_proof
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over each entry's forms, 10^m*k + 1 for "
                    "m = 1..n (A305740) and m*10^k + 1 for k = 0..n "
                    "(A153431); w(q,n,F) = the number of distinct residues "
                    "of the exponents mod ord_q(10), proved in decl_reference",
           "qmax": QMAX,
           "units": "every depth is in the published term itself "
                    "(A305740's k, A153431's m)",
           "caveat": "the repo's first-occurrence models run late: the ladder "
                     "projects before this one landed their scored finds at "
                     "about 1.9-2.5x their medians while every census showed "
                     "the intensity right to a percent or two. Read every "
                     "depth below as a floor and budget 2-3x the median.",
           "families": {}}
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        preds = predictions(fam, top, KNOWN[fam][top], n_ahead=8)
        es = {str(n): expected(fam, n, floor_for(fam, n, prev), t)
              for n, prev, t in independent_knowns(fam)}
        under = {}
        for n in range(top + 1, top + 9):
            ceil = k_ceil(n, fam)
            under[str(n)] = {
                "ceiling_x": float(ceil),
                "proof_crossing_x": float(k_proof(n, fam)),
                "unit": forced_unit(n, fam),
                "P_under_ceiling": p_by(fam, n,
                                        floor_for(fam, n, KNOWN[fam][top]),
                                        ceil)}
        out["families"][fam] = {
            "forms": FAMILIES[fam]["forms"],
            "letter": FAMILIES[fam]["letter"],
            "frontier": {"n": top, "x": KNOWN[fam][top],
                         "by": FAMILIES[fam]["frontier_by"]},
            "singular_series": {str(n): math.exp(log_singular(fam, n))
                                for n in range(top + 1, top + 9)},
            "validation": {"E_at_known": es,
                           "mean_E": sum(es.values()) / len(es),
                           "draws": len(es),
                           "note": "riders excluded: one vote per condition"},
            "predictions_x": {str(n): {q: float(v) for q, v in qs.items()}
                              for n, qs in preds.items()},
            "predictions_note": "each term's quantiles are from the previous "
                                "term's MEDIAN (chained), the published "
                                "frontier for the first",
            "under_the_ceiling": under}
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
            print("  %s (%s), frontier a(%d) = %d; validation mean E %.2f "
                  "over %d draws:"
                  % (fam, d["forms"], d["frontier"]["n"], d["frontier"]["x"],
                     d["validation"]["mean_E"], d["validation"]["draws"]))
            for n, qs in sorted(d["predictions_x"].items(),
                                key=lambda x: int(x[0])):
                u = d["under_the_ceiling"].get(n)
                print("     a(%s): %s%s" % (n, "  ".join(
                    "%s %.3g" % (q, v) for q, v in qs.items()),
                    ("  [unit %d, crossing %.3g]"
                     % (u["unit"], u["proof_crossing_x"])) if u else ""))

    _s.exit(_shutdown.graceful(_main) or 0)
