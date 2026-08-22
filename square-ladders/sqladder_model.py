"""The odds model for A089761 -- Bateman-Horn over n linear forms.

    a(n) = least k with k*i^2 + 1 prime for i = 1..n

For a fixed n the n forms f_i(k) = i^2*k + 1 are distinct, irreducible and
have no fixed prime divisor, so Bateman-Horn puts the density of k at which
all n are simultaneously prime at

    S(n) / prod_{i=1..n} log(i^2 k),      S(n) = prod_q  (1 - w(q,n)/q)
                                                        ------------------
                                                          (1 - 1/q)^n

with w(q,n) = min(n, (q-1)/2) the killed-residue count PROVED in
sqladder_reference.  The singular series is computed numerically to QMAX
and is the same quantity the sieve is built from, which is the useful
consistency: a wrong w would move the model and the engine together, and
the model's validation against the known terms would catch it.

VALIDATION (gate G11).  E(n, a(n)) -- the expected number of hits the model
puts below the term that actually occurred -- must scatter around 1 on the
knowns.  A model whose knowns all sit at ~0 or ~1 is wrong and may not be
used to plan a campaign (CONVENTIONS.md "The odds model").

ONE VOTE PER CONDITION.  a(11) through a(15) of this sequence are the SAME
INTEGER: 861066640 was found as a(11) and cleared four further conditions
for free.  Scoring the model at all five would be scoring one event five
times and would manufacture agreement out of nothing.  The validation
therefore uses only terms that were separately searched for, which is
a(8), a(9), a(10), a(11) -- the last four independent ones.

WHAT IT PREDICTS, stated before the run:

    a(16)  Q1 3.5e14   median 1.8e15   Q3 6.3e15
    a(17)  Q1 1.2e16   median 5.7e16   Q3 1.9e17
    a(18)  Q1 4.2e17   median 2.0e18   Q3 6.3e18
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from sqladder_reference import KNOWN, PUBLISHED_BOUNDS, w

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_LS = {}

# The knowns that were SEPARATELY SEARCHED FOR (see the docstring).  a(12)
# through a(15) are riders on a(11) and are not independent evidence.
INDEPENDENT_KNOWNS = (8, 9, 10, 11)

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}


def log_singular(n):
    """log S(n), computed once per n."""
    if n in _LS:
        return _LS[n]
    s = 0.0
    for q in _PRIMES:
        ww = w(q, n)
        if ww >= q:                       # cannot happen for n < (q-1)/2+1
            _LS[n] = -math.inf
            return -math.inf
        s += math.log(1 - ww / q) - n * math.log(1 - 1.0 / q)
    _LS[n] = s
    return s


def expected(n, a, b, points=3000):
    """Expected number of k in [a, b] with all n forms prime."""
    a, b = float(max(a, 10.0)), float(b)
    if b <= a:
        return 0.0
    S = math.exp(log_singular(n))
    t = np.logspace(math.log10(a), math.log10(b), points)
    dens = np.full_like(t, S)
    for i in range(1, n + 1):
        dens = dens / np.log(np.maximum(i * i * t, 3.0))
    return float(np.trapezoid(dens, t))


def p_by(n, frontier, k):
    """P(a(n) has appeared by k), given it is known to exceed `frontier`."""
    e = expected(n, frontier, k)
    return 1.0 - math.exp(-e) if e > 0 else 0.0


def quantile(n, frontier, p, hi=1e26):
    """The k at which P(a(n) found) reaches p, searching from `frontier`."""
    target = -math.log(1.0 - p)
    lo, b = float(max(frontier, 100.0)), float(hi)
    if expected(n, lo, b) < target:
        return None                        # not reachable below `hi`
    for _ in range(80):
        m = math.sqrt(lo * b)
        if expected(n, max(frontier, 100.0), m) < target:
            lo = m
        else:
            b = m
    return math.sqrt(lo * b)


def floor_for(n, frontier_k):
    """Where the search for a(n) actually starts.

    Not simply the previous term: somebody has already swept past it.
    a(16) is known to exceed 1.4e13 (Alekseyev), so the odds for it must be
    measured from THERE -- crediting the model for ground another person
    already cleared would make every prediction optimistic.
    """
    return max(float(frontier_k), float(PUBLISHED_BOUNDS.get(n, 0)))


def predictions(frontier_n, frontier_k, n_ahead=3, ceiling=None):
    """{n: {quantile: depth}} for the next `n_ahead` open terms.

    Derived from the LIVE frontier on every call (CONVENTIONS.md: "a rung
    retires with its term"), never cached, so a find cannot leave the
    ladder aiming at a depth that has stopped meaning anything.
    """
    out = {}
    for n in range(frontier_n + 1, frontier_n + 1 + n_ahead):
        qs = {}
        base = floor_for(n, frontier_k)
        for name in QUANTILES:
            d = quantile(n, base, _Q[name])
            if d is not None and (ceiling is None or d < ceiling):
                qs[name] = d
        if qs:
            out[n] = qs
    return out


def campaign_board(frontier_n, frontier_k):
    """One row per open term: what it costs to reach each quantile."""
    rows = []
    preds = predictions(frontier_n, frontier_k, n_ahead=4)
    for n in sorted(preds):
        rows.append(dict(n=n, S=math.exp(log_singular(n)),
                         quantiles=preds[n]))
    return rows


# --------------------------------- gates -----------------------------------

def g11_model_validates_on_knowns():
    """E at each independently-searched known must scatter around 1.

    The window starts at the PREVIOUS term, because that is what was known
    when the search for this one began; starting at 0 would double-count
    the ground already ruled out.
    """
    es = []
    for n in INDEPENDENT_KNOWNS:
        prev = KNOWN[n - 1]
        es.append(expected(n, prev, KNOWN[n]))
    lo, hi = min(es), max(es)
    mean = sum(es) / len(es)
    # If the intensity is right, the integral of it up to the first event is
    # Exp(1): mean 1, and a spread from near 0 to ~2 is what Exp(1) LOOKS
    # like on four draws.  So the test is the mean against 1, plus a
    # scatter that is neither degenerate nor absurd -- not "every value
    # near 1", which would actually indicate an overfitted model.
    if not 0.35 < mean < 2.5:
        return False, (f"G11 FAIL: mean E at the knowns is {mean:.2f}; under "
                       f"a correct model it is Exp(1) with mean 1, so the "
                       f"intensity is off by roughly that factor")
    if lo > 1.0 or hi < 0.5:
        return False, (f"G11 FAIL: every known sits on one side of E = 1 "
                       f"({[round(e, 2) for e in es]}) -- biased, and it may "
                       f"not be used to plan")
    return True, ("G11 ok: E at the independently-searched knowns a(8)-a(11) "
                  "is %s -- mean %.2f against the Exp(1) mean of 1, so the "
                  "intensity is honest (a(12)-a(15) are riders on a(11) and "
                  "are excluded: one vote per condition)"
                  % ("/".join("%.2f" % e for e in es), mean))


def g12_monotone_and_sane():
    """Deeper terms must be predicted deeper, and the singular series must
    grow with n (each extra condition makes survivors rarer but the
    conditioning stronger)."""
    prev_med, prev_S = 0.0, 0.0
    for n in (16, 17, 18, 19):
        S = math.exp(log_singular(n))
        med = quantile(n, KNOWN[15], 0.5)
        if med is None or med <= prev_med:
            return False, f"G12 FAIL: a({n}) median {med} not above {prev_med}"
        if S <= prev_S:
            return False, f"G12 FAIL: S({n}) = {S:.3g} not above {prev_S:.3g}"
        prev_med, prev_S = med, S
    return True, ("G12 ok: predicted medians and singular series both "
                  "increase with n over a(16)-a(19)")


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    frontier_n, frontier_k = max(KNOWN), KNOWN[max(KNOWN)]
    preds = predictions(frontier_n, frontier_k, n_ahead=4)
    es = {n: expected(n, KNOWN[n - 1], KNOWN[n]) for n in INDEPENDENT_KNOWNS}
    out = {"model": "Bateman-Horn over f_i(k) = i^2*k+1, i = 1..n; "
                    "w(q,n) = min(n,(q-1)/2) proved in sqladder_reference",
           "qmax": QMAX,
           "frontier": {"n": frontier_n, "k": frontier_k,
                        "searched_to": 14_000_000_000_000},
           "validation": {"independent_knowns": list(INDEPENDENT_KNOWNS),
                          "E_at_known": {str(k): v for k, v in es.items()},
                          "note": "a(12)-a(15) are the same integer as a(11) "
                                  "and are excluded: one vote per condition"},
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
        for n, qs in sorted(out["predictions"].items()):
            print("  a(%s): %s" % (n, "  ".join(
                "%s %.3g" % (q, v) for q, v in qs.items())))

    _s.exit(_shutdown.graceful(_main) or 0)
