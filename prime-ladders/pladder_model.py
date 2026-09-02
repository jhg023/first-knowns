"""The odds model for the prime ladders -- Bateman-Horn over n linear forms.

    A(s, n) = least k with prime(i)*k + s prime for i = 1..n

For a fixed (s, n) the n forms f_i(k) = prime(i)*k + s are distinct,
irreducible and have no fixed prime divisor (proved in pladder_reference),
so Bateman-Horn puts the density of k at which all n are simultaneously
prime at

    S(n) / prod_{i=1..n} log(prime(i)*k + s),

    S(n) = prod_q  (1 - w(q,n)/q) / (1 - 1/q)^n

with w(q,n) the number of distinct residues of the first n primes (other
than q) mod q -- the killed count PROVED in pladder_reference, and the
SAME for both signs.  So the two families share one singular series and
one density; the only thing that separates their predictions is where
each search starts.  The series is computed numerically to QMAX and is the
quantity the sieve is built from, which is the useful consistency: a wrong
w would move the model and the engine together, and the model's validation
against the known terms would catch it.

The series is LARGE.  The first n primes cover every nonzero residue mod
2, 3, 5, 7 and 11 by n = 14, so those five primes contribute (1/q)/(1-1/q)^n
each instead of the (1-n/q)/(1-1/q)^n a generic form would -- at n = 14
that is S = 6.6e5, against 5.6e4 for the r*k+1 ladder of A088250 at the
same n.  Forced divisibility is a gift to the density as well as to the
wheel: it is why these terms are as small as they are for their n.

TWO FAMILIES, ONE MODEL, AND THE VALIDATION IS POOLED.  s = +1 and s = -1
are different sequences with different frontiers, but they are the same
model with the same intensity, so scoring it on both at once is not mixing
evidence, it is doubling the sample: each alone offers four to six
independently-searched terms, together they offer ten.

VALIDATION (gate G11).  E(n, s) -- the expected number of hits the model
puts between the previous term and the one that actually occurred -- must
scatter around 1 on the knowns.  A model whose knowns all sit at ~0 or ~1
is wrong and may not be used to plan a campaign (CONVENTIONS.md "The odds
model").

ONE VOTE PER CONDITION.  Both families have RIDERS: A084700's a(3) rides
on a(2) and a(5)-a(7) on a(4); A084701's a(2) rides on a(1) and a(6), a(7)
on a(5).  A rider was never searched for -- it came free with its
predecessor -- so its E is identically zero and scoring it would
manufacture agreement out of nothing.  Only terms that strictly exceed
their predecessor are used, and only from n = 8, above the exception zone.

AND THE MODEL IS A FLOOR, NOT A FORECAST.  Every quantile this file prints
should be read with the repo's measured correction: across the thirteen
first occurrences scored in first-knowns' three ladder projects before
this one, the finds land at a pooled optimism factor of 1.92x (95%
interval [1.12, 3.60], excluding 1) while every census showed the modelled
INTENSITY right to a percent or two.  Mean count right, first occurrence
late: budget 2-3x the median below before expecting a term.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from pladder_reference import FAMILIES, KNOWN, PUBLISHED_BOUNDS, rung, w

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_LS = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# The knowns that were SEPARATELY SEARCHED FOR: strictly above their
# predecessor (so not a rider) and clear of the exception zone.  Ten terms
# across the two families: a(8)-a(13) of A084700, a(8)-a(11) of A084701.
VALIDATE_FROM = 8


def independent_knowns(s):
    """[(n, prev, term)] for the terms this model may be scored on."""
    out = []
    for n in sorted(KNOWN[s]):
        if n < VALIDATE_FROM or n - 1 not in KNOWN[s]:
            continue
        prev, term = KNOWN[s][n - 1], KNOWN[s][n]
        if term > prev:
            out.append((n, prev, term))
    return out


def log_singular(n):
    """log S(n), computed once per n.  Sign-independent (pladder_reference
    G2c), so there is one series for both families."""
    if n in _LS:
        return _LS[n]
    acc = 0.0
    for q in _PRIMES:
        ww = w(q, n)
        if ww >= q:                       # proved impossible; assert anyway
            _LS[n] = -math.inf
            return -math.inf
        acc += math.log(1 - ww / q) - n * math.log(1 - 1.0 / q)
    _LS[n] = acc
    return acc


def expected(n, s, a, c, points=3000):
    """Expected number of k in [a, c] with all n forms prime."""
    a, c = float(max(a, 10.0)), float(c)
    if c <= a:
        return 0.0
    S = math.exp(log_singular(n))
    t = np.logspace(math.log10(a), math.log10(c), points)
    dens = np.full_like(t, S)
    for i in range(1, n + 1):
        dens = dens / np.log(np.maximum(rung(i) * t + s, 3.0))
    return float(np.trapezoid(dens, t))


def p_by(n, s, frontier, k):
    """P(a(n) has appeared by k), given it is known to exceed `frontier`."""
    e = expected(n, s, frontier, k)
    return 1.0 - math.exp(-e) if e > 0 else 0.0


def quantile(n, s, frontier, p, hi=1e30):
    """The k at which P(a(n) found) reaches p, searching from `frontier`."""
    target = -math.log(1.0 - p)
    lo, c = float(max(frontier, 100.0)), float(hi)
    if expected(n, s, lo, c) < target:
        return None                        # not reachable below `hi`
    for _ in range(90):
        mid = math.sqrt(lo * c)
        if expected(n, s, max(frontier, 100.0), mid) < target:
            lo = mid
        else:
            c = mid
    return math.sqrt(lo * c)


def floor_for(n, s, frontier_k):
    """Where the search for a(n) actually starts.

    Monotonicity alone: the conditions nest, so a(n) >= a(n-1), and neither
    family carries a published searched-empty bound beyond its last term.
    (Crediting a model for ground somebody else already cleared is what
    `PUBLISHED_BOUNDS` exists to prevent in the projects that have one.)
    """
    return max(float(frontier_k), float(PUBLISHED_BOUNDS[s].get(n, 0)))


def predictions(s, frontier_n, frontier_k, n_ahead=3, ceiling=None):
    """{n: {quantile: depth}} for the next `n_ahead` open terms.

    Derived from the LIVE frontier on every call (CONVENTIONS.md: "a rung
    retires with its term"); the launcher caches the result on the frontier
    with huntlib.rungs.LiveLadder, because a call is ~1,000 numerical
    integrals and the segment loop may not pay that (OPTIMIZATION.md 2.14).
    """
    out = {}
    for n in range(frontier_n + 1, frontier_n + 1 + n_ahead):
        qs = {}
        base = floor_for(n, s, frontier_k)
        for name in QUANTILES:
            d = quantile(n, s, base, _Q[name])
            if d is not None and (ceiling is None or d < ceiling):
                qs[name] = d
        if qs:
            out[n] = qs
    return out


# --------------------------------- gates -----------------------------------

def g11_model_validates_on_knowns():
    """E at each independently-searched known must scatter around 1.

    The window starts at the PREVIOUS term, because that is what was known
    when the search for this one began; starting at 0 would double-count
    the ground already ruled out.  Pooled over both families, because it is
    one model and ten draws beat five.
    """
    es, detail = [], []
    for s in sorted(FAMILIES, reverse=True):
        fam = []
        for n, prev, term in independent_knowns(s):
            e = expected(n, s, prev, term)
            es.append(e)
            fam.append("a(%d) %.2f" % (n, e))
        detail.append("%s: %s" % (FAMILIES[s]["oeis"], " ".join(fam)))
    lo, hi = min(es), max(es)
    mean = sum(es) / len(es)
    # If the intensity is right, the integral of it up to the first event is
    # Exp(1): mean 1, and a spread from near 0 to ~3 is what Exp(1) LOOKS
    # like on ten draws.  So the test is the mean against 1, plus a scatter
    # that is neither degenerate nor absurd -- not "every value near 1",
    # which would indicate an overfitted model rather than a validated one.
    if not 0.35 < mean < 2.5:
        return False, (f"G11 FAIL: mean E at the knowns is {mean:.2f}; under "
                       f"a correct model it is Exp(1) with mean 1, so the "
                       f"intensity is off by roughly that factor "
                       f"({'; '.join(detail)})")
    if lo > 1.0 or hi < 0.5:
        return False, (f"G11 FAIL: every known sits on one side of E = 1 "
                       f"-- biased, and it may not be used to plan "
                       f"({'; '.join(detail)})")
    return True, ("G11 ok: E at the %d independently-searched knowns is "
                  "mean %.2f against the Exp(1) mean of 1, spread %.2f-%.2f "
                  "-- %s (riders excluded: one vote per condition)"
                  % (len(es), mean, lo, hi, "; ".join(detail)))


def g12_monotone_and_sane():
    """Deeper terms must be predicted deeper, and the singular series must
    grow with n (each extra condition makes survivors rarer but the
    conditioning stronger).  Also: the two families share ONE series but
    start from different floors, so their predictions for the same n must
    differ -- the cheapest guard against a sign that stopped reaching the
    floor."""
    for s in sorted(FAMILIES, reverse=True):
        top = max(KNOWN[s])
        prev_med, prev_S = 0.0, 0.0
        for n in range(top + 1, top + 5):
            S = math.exp(log_singular(n))
            med = quantile(n, s, KNOWN[s][top], 0.5)
            if med is None or med <= prev_med:
                return False, (f"G12 FAIL: s={s:+d} a({n}) median {med} not "
                               f"above {prev_med}")
            if S <= prev_S:
                return False, (f"G12 FAIL: S({n}) = {S:.3g} not above "
                               f"{prev_S:.3g}")
            prev_med, prev_S = med, S
    mp = quantile(14, +1, KNOWN[+1][13], 0.5)
    mm = quantile(14, -1, KNOWN[-1][11], 0.5)
    if mp is None or mm is None or abs(math.log(mp / mm)) < 0.05:
        return False, (f"G12 FAIL: a(14) medians {mp} (s=+1) and {mm} (s=-1) "
                       f"coincide although the floors differ by 40x")
    return True, ("G12 ok: predicted medians and singular series both "
                  "increase with n over the next four open terms of each "
                  "family; S(14) = %.4g; and the two families' a(14) medians "
                  "differ (%.3g vs %.3g) because their floors do"
                  % (math.exp(log_singular(14)), mp, mm))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over f_i(k) = prime(i)*k + s, i = 1..n; "
                    "w(q,n) = #distinct residues of the first n primes mod "
                    "q (other than q), proved in pladder_reference and "
                    "independent of s",
           "qmax": QMAX,
           "caveat": "the repo's first-occurrence models run late: 13 "
                     "scored finds across three ladder projects land at a "
                     "pooled optimism factor of 1.92x [1.12, 3.60] while "
                     "every census showed the intensity right to a percent "
                     "or two. Read every depth below as a floor and budget "
                     "2-3x the median.",
           "families": {}}
    for s in sorted(FAMILIES, reverse=True):
        top = max(KNOWN[s])
        preds = predictions(s, top, KNOWN[s][top], n_ahead=4)
        es = {str(n): expected(n, s, prev, term)
              for n, prev, term in independent_knowns(s)}
        out["families"][FAMILIES[s]["oeis"]] = {
            "sign": s,
            "frontier": {"n": top, "k": KNOWN[s][top],
                         "by": FAMILIES[s]["frontier_by"]},
            "singular_series": {str(n): math.exp(log_singular(n))
                                for n in range(top + 1, top + 5)},
            "validation": {"E_at_known": es,
                           "note": "riders excluded: one vote per condition"},
            "predictions": {str(n): {q: float(v) for q, v in qs.items()}
                            for n, qs in preds.items()}}
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
        for oeis, fam in sorted(out["families"].items()):
            print("  %s (s = %+d), frontier a(%d) = %d:"
                  % (oeis, fam["sign"], fam["frontier"]["n"],
                     fam["frontier"]["k"]))
            for n, qs in sorted(fam["predictions"].items(),
                                key=lambda x: int(x[0])):
                print("     a(%s): %s" % (n, "  ".join(
                    "%s %.3g" % (q, v) for q, v in qs.items())))

    _s.exit(_shutdown.graceful(_main) or 0)
