"""The odds model for the shift ladders -- Bateman-Horn over n linear forms.

    A(b, n) = least m with m + b^k prime for k = 1..n

For a fixed (b, n) the n forms f_k(m) = m + b^k are distinct, irreducible
and have no fixed prime divisor (proved in shiftladder_reference), so
Bateman-Horn puts the density of m at which all n are simultaneously prime
at

    S(n,b) / prod_{k=1..n} log(m + b^k),

    S(n,b) = prod_q  (1 - w(q,n,b)/q) / (1 - 1/q)^n

with w(q,n,b) = 1 for q | b and min(n, ord_q(b)) otherwise -- the killed
count PROVED in shiftladder_reference.  The singular series is computed
numerically to QMAX and is the same quantity the sieve is built from, which
is the useful consistency: a wrong w would move the model and the engine
together, and the model's validation against the known terms would catch
it.

TWO FAMILIES, ONE MODEL, AND THE VALIDATION IS POOLED.  b = 2 and b = 4 are
different problems -- their singular series differ by orders of magnitude
and so do their wheels -- but they are the same model, so scoring it on
both at once is not mixing evidence, it is doubling the sample.  That
matters here: each family alone offers four or five independently-searched
terms, which is too few to distinguish a factor-of-two error from noise,
and together they offer ten.

VALIDATION (gate G11).  E(n, b) -- the expected number of hits the model
puts between the previous term and the one that actually occurred -- must
scatter around 1 on the knowns.  A model whose knowns all sit at ~0 or ~1
is wrong and may not be used to plan a campaign (CONVENTIONS.md "The odds
model").

ONE VOTE PER CONDITION.  Both families are riddled with RIDERS: a(11)
through a(14) of A130003 are one integer (4503), and A110096 repeats at
a(2), a(4), a(6), a(8), a(13) and a(16).  A rider was never searched for --
it came free with its predecessor -- so its E is identically zero and
scoring it would manufacture agreement out of nothing.  Only terms that
strictly exceed their predecessor are used.

AND THE MODEL IS A FLOOR, NOT A FORECAST.  Every quantile this file prints
should be read with the repo's measured correction: across the seven
first occurrences scored in first-knowns before this project, the finds
land at a mean model quantile of 0.85 where a correct model gives 0.50,
and square-ladders' own optimism factor is 3.7x with a 95% interval
[1.25, 17.7] that excludes 1 -- while its census showed the modelled
INTENSITY right to 2%.  Mean count right, first occurrence late: budget
2-3x the median below before expecting a term.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from shiftladder_reference import FAMILIES, KNOWN, PUBLISHED_BOUNDS, w

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_LS = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# The knowns that were SEPARATELY SEARCHED FOR: strictly above their
# predecessor (so not a rider) and clear of the exception zone, where the
# values are so small that "density 1/log v" is not yet describing
# anything.  Ten terms across the two families.
VALIDATE_FROM = 10


def independent_knowns(b):
    """[(n, prev, term)] for the terms this model may be scored on."""
    out = []
    for n in sorted(KNOWN[b]):
        if n < VALIDATE_FROM or n - 1 not in KNOWN[b]:
            continue
        prev, term = KNOWN[b][n - 1], KNOWN[b][n]
        if term > prev:
            out.append((n, prev, term))
    return out


def log_singular(n, b):
    """log S(n,b), computed once per (n, b)."""
    key = (n, b)
    if key in _LS:
        return _LS[key]
    s = 0.0
    for q in _PRIMES:
        ww = w(q, n, b)
        if ww >= q:                       # proved impossible; assert anyway
            _LS[key] = -math.inf
            return -math.inf
        s += math.log(1 - ww / q) - n * math.log(1 - 1.0 / q)
    _LS[key] = s
    return s


def expected(n, b, a, c, points=3000):
    """Expected number of m in [a, c] with all n forms prime."""
    a, c = float(max(a, 10.0)), float(c)
    if c <= a:
        return 0.0
    S = math.exp(log_singular(n, b))
    t = np.logspace(math.log10(a), math.log10(c), points)
    dens = np.full_like(t, S)
    for k in range(1, n + 1):
        dens = dens / np.log(np.maximum(t + float(b) ** k, 3.0))
    return float(np.trapezoid(dens, t))


def p_by(n, b, frontier, m):
    """P(a(n) has appeared by m), given it is known to exceed `frontier`."""
    e = expected(n, b, frontier, m)
    return 1.0 - math.exp(-e) if e > 0 else 0.0


def quantile(n, b, frontier, p, hi=1e30):
    """The m at which P(a(n) found) reaches p, searching from `frontier`."""
    target = -math.log(1.0 - p)
    lo, c = float(max(frontier, 100.0)), float(hi)
    if expected(n, b, lo, c) < target:
        return None                        # not reachable below `hi`
    for _ in range(90):
        mid = math.sqrt(lo * c)
        if expected(n, b, max(frontier, 100.0), mid) < target:
            lo = mid
        else:
            c = mid
    return math.sqrt(lo * c)


def floor_for(n, b, frontier_m):
    """Where the search for a(n) actually starts.

    Monotonicity alone: the conditions nest, so a(n) >= a(n-1), and neither
    family carries a published searched-empty bound beyond its last term.
    (Crediting a model for ground somebody else already cleared is what
    `PUBLISHED_BOUNDS` exists to prevent in the projects that have one.)
    """
    return max(float(frontier_m), float(PUBLISHED_BOUNDS[b].get(n, 0)))


def predictions(b, frontier_n, frontier_m, n_ahead=3, ceiling=None):
    """{n: {quantile: depth}} for the next `n_ahead` open terms.

    Derived from the LIVE frontier on every call (CONVENTIONS.md: "a rung
    retires with its term"), never cached, so a find cannot leave the
    ladder aiming at a depth that has stopped meaning anything.
    """
    out = {}
    for n in range(frontier_n + 1, frontier_n + 1 + n_ahead):
        qs = {}
        base = floor_for(n, b, frontier_m)
        for name in QUANTILES:
            d = quantile(n, b, base, _Q[name])
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
    for b in sorted(FAMILIES):
        fam = []
        for n, prev, term in independent_knowns(b):
            e = expected(n, b, prev, term)
            es.append(e)
            fam.append("a(%d) %.2f" % (n, e))
        detail.append("%s: %s" % (FAMILIES[b]["oeis"], " ".join(fam)))
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
                       f"intensity is off by roughly that factor")
    if lo > 1.0 or hi < 0.5:
        return False, (f"G11 FAIL: every known sits on one side of E = 1 "
                       f"-- biased, and it may not be used to plan")
    return True, ("G11 ok: E at the %d independently-searched knowns is "
                  "mean %.2f against the Exp(1) mean of 1, spread %.2f-%.2f "
                  "-- %s (riders excluded: one vote per condition)"
                  % (len(es), mean, lo, hi, "; ".join(detail)))


def g12_monotone_and_sane():
    """Deeper terms must be predicted deeper, and the singular series must
    grow with n (each extra condition makes survivors rarer but the
    conditioning stronger).  Also: the two families are NOT the same
    numbers, which is the cheapest possible guard against a b that silently
    stopped being used."""
    for b in sorted(FAMILIES):
        top = max(KNOWN[b])
        prev_med, prev_S = 0.0, 0.0
        for n in range(top + 1, top + 5):
            S = math.exp(log_singular(n, b))
            med = quantile(n, b, KNOWN[b][top], 0.5)
            if med is None or med <= prev_med:
                return False, (f"G12 FAIL: b={b} a({n}) median {med} not "
                               f"above {prev_med}")
            if S <= prev_S:
                return False, (f"G12 FAIL: b={b} S({n}) = {S:.3g} not above "
                               f"{prev_S:.3g}")
            prev_med, prev_S = med, S
    s2, s4 = log_singular(19, 2), log_singular(19, 4)
    if abs(s2 - s4) < 1.0:
        return False, (f"G12 FAIL: log S(19,2) = {s2:.3f} and log S(19,4) = "
                       f"{s4:.3f} are the same to within a factor of e -- "
                       f"the base is not reaching the singular series")
    return True, ("G12 ok: predicted medians and singular series both "
                  "increase with n over the next four open terms of each "
                  "family, and S(19,2)/S(19,4) = %.4g, so the two families "
                  "are genuinely different problems" % math.exp(s2 - s4))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over f_k(m) = m + b^k, k = 1..n; "
                    "w(q,n,b) = min(n, ord_q(b)) (1 at q | b), proved in "
                    "shiftladder_reference",
           "qmax": QMAX,
           "caveat": "the repo's first-occurrence models run late: 7 scored "
                     "finds land at a mean quantile of 0.85 and "
                     "square-ladders measured 3.7x [1.25, 17.7] while its "
                     "census showed the intensity right to 2%. Read every "
                     "depth below as a floor and budget 2-3x the median.",
           "families": {}}
    for b in sorted(FAMILIES):
        top = max(KNOWN[b])
        preds = predictions(b, top, KNOWN[b][top], n_ahead=3)
        es = {str(n): expected(n, b, prev, term)
              for n, prev, term in independent_knowns(b)}
        out["families"][FAMILIES[b]["oeis"]] = {
            "base": b,
            "frontier": {"n": top, "m": KNOWN[b][top],
                         "by": FAMILIES[b]["frontier_by"]},
            "singular_series": {str(n): math.exp(log_singular(n, b))
                                for n in range(top + 1, top + 4)},
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
            print("  %s (b = %d), frontier a(%d) = %d:"
                  % (oeis, fam["base"], fam["frontier"]["n"],
                     fam["frontier"]["m"]))
            for n, qs in sorted(fam["predictions"].items(), key=lambda x: int(x[0])):
                print("     a(%s): %s" % (n, "  ".join(
                    "%s %.3g" % (q, v) for q, v in qs.items())))

    _s.exit(_shutdown.graceful(_main) or 0)
