"""ap_model.py -- the odds model for A053647, and its validation.

    a(n) = least prime p with p + j*P(n) prime for j = 0 .. n-1

A Bateman-Horn / Hardy-Littlewood k-tuple estimate with a numerically
computed singular series.  The point of it is not to be right about any one
term -- it cannot be -- but to say, BEFORE the run, where each open term
should be expected and with what spread, so that the finds can be scored
against a prediction nobody was free to adjust afterwards.

THE COUNT.  For the tuple {0, P(n), ..., (n-1)P(n)} the expected number of
p <= N with every member prime is

    E(n, N) = S(n) * integral_2^N  prod_j  dt / log(t + j*P(n))

with the singular series

    S(n) = prod_q  (1 - w(q)/q) / (1 - 1/q)^n ,
    w(q) = #{ (-j*P(n)) mod q : j = 0..n-1 }  =  1 if q | P(n) else n.

Two things about this problem make the arithmetic unusual and are worth
stating because they drive everything:

  * The singular series is ENORMOUS.  Every prime q <= prime(n) contributes
    (1 - 1/q)^(1-n), so at n = 16 the primes up to 53 alone multiply the
    density by about 5e9.  A progression whose difference is the primorial
    is the most favourable admissible shape there is, which is exactly why
    these terms are findable at all.
  * The log factors are NOT all log(p).  P(n) dwarfs every p this hunt will
    reach -- at n = 16 the difference is 3.3e19 against a p near 4e13 -- so
    for j >= 1 the value p + j*P(n) is essentially j*P(n), and its log
    barely moves as p sweeps.  Treating them all as log(p) would overstate
    the density by orders of magnitude.

VALIDATION.  The model is checked against the nine known terms it did not
help find: E(n, a(n)) should be an Exp(1) draw for each, so the values must
SCATTER around 1 rather than clustering at 0 or 1.  They do -- 0.06 to 2.53
-- with a mild early lean (sum 5.62 against 9 expected, p ~ 0.12), which is
recorded here rather than smoothed away.  A model whose knowns all sat at
quantile ~0 or ~1 would be wrong and CONVENTIONS.md would forbid using it
to plan.

Running this file rewrites model_results.json, which launch.py reads for
its rung ladder.  The predictions in it were fixed before the first
production sweep; they are not to be re-fitted after a find.
"""

import json
import math
import pathlib
import sys

import numpy as np
from sympy import primerange

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from ap_reference import KNOWN, difference                     # noqa: E402

QMAX = 100_000                # singular-series product cut (tail ~ 1e-3)
PRIMES = None
GRID = 4000                   # integration points, log-spaced

# The quantiles every launcher's rung ladder is built from.  P(found by N)
# = 1 - exp(-E), so a quantile q is the depth where E = -ln(1 - q).
RUNG_QUANTILES = (("Q1", 0.25), ("median", 0.50), ("Q3", 0.75), ("P90", 0.90))


def _primes():
    global PRIMES
    if PRIMES is None:
        PRIMES = list(primerange(2, QMAX))
    return PRIMES


def singular_series(n):
    """log S(n).  w(q) = 1 for q | P(n), n otherwise -- one formula, and the
    small primes are where nearly all of the value is."""
    d = difference(n)
    logs = 0.0
    for q in _primes():
        w = 1 if d % q == 0 else n
        if w >= q:
            return -math.inf                  # inadmissible: cannot happen
        logs += math.log(1 - w / q) - n * math.log(1 - 1 / q)
    return logs


_S = {}


def expected_count(n, N, lo=10.0):
    """E(n, N): expected number of p in [lo, N] starting a full chain."""
    if n not in _S:
        _S[n] = singular_series(n)
    s = math.exp(_S[n])
    d = float(difference(n))
    if N <= lo:
        return 0.0
    t = np.logspace(math.log10(lo), math.log10(N), GRID)
    dens = np.full_like(t, s)
    for j in range(n):
        dens = dens / np.log(np.maximum(t + j * d, 3.0))
    return float(np.trapezoid(dens, t))


def depth_for(n, e_target, hi=1e30, lo=10.0):
    """The depth N where E(n, N) reaches e_target, by bisection."""
    if expected_count(n, hi) < e_target:
        return None                           # not reached below hi
    a, b = math.log(max(lo, 11.0)), math.log(hi)
    for _ in range(90):
        m = 0.5 * (a + b)
        if expected_count(n, math.exp(m)) < e_target:
            a = m
        else:
            b = m
    return math.exp(b)


def quantiles(n):
    """{"Q1": depth, "median": depth, "Q3": depth, "P90": depth}."""
    out = {}
    for name, q in RUNG_QUANTILES:
        d = depth_for(n, -math.log(1.0 - q))
        if d is not None:
            out[name] = d
    return out


def validate(ns=range(7, 16)):
    """[(n, a(n), E(n, a(n)))] -- the model scored on terms it did not find."""
    return [(n, KNOWN[n], expected_count(n, KNOWN[n])) for n in ns
            if n in KNOWN]


def gate_model_validates():
    """(ok, msg): the knowns SCATTER, which is what makes the model usable.

    CONVENTIONS.md: a model whose knowns all sit at quantile ~0 or ~1 is
    wrong and may not be used to plan.  The test is deliberately weak in
    one direction and strict in the other -- it does not ask the model to
    be accurate, only to be honestly calibrated.
    """
    rows = validate()
    es = [e for _n, _p, e in rows]
    if len(es) < 6:
        return False, "model: too few knowns to validate against"
    if min(es) > 0.5 or max(es) < 1.5:
        return False, (f"model: E values {min(es):.2f}-{max(es):.2f} do not "
                       f"scatter; an Exp(1) sample of {len(es)} should "
                       f"straddle 1")
    tot = sum(es)
    # Sum of k Exp(1) is Gamma(k); flag only a gross failure in either
    # direction, which is what "unusable for planning" looks like.
    if not 0.25 * len(es) < tot < 2.5 * len(es):
        return False, (f"model: E sums to {tot:.2f} over {len(es)} knowns, "
                       f"far from the {len(es)} an Exp(1) sample would give")
    lean = "early" if tot < len(es) else "late"
    return True, (f"model ok: E on a({rows[0][0]})-a({rows[-1][0]}) ranges "
                  f"{min(es):.2f}-{max(es):.2f} and sums to {tot:.2f} against "
                  f"{len(es)} expected -- honest scatter with a mild {lean} "
                  f"lean")


GATES = [gate_model_validates]

OPEN = (16, 17, 18, 19, 20, 21, 22, 23)


def write(path=None):
    """Rewrite model_results.json -- predictions, validation, provenance."""
    path = path or str(pathlib.Path(__file__).with_name("model_results.json"))
    preds = {str(n): quantiles(n) for n in OPEN}
    rows = validate()
    doc = {
        "sequence": "A053647",
        "model": "Bateman-Horn, numerically computed singular series",
        "qmax": QMAX,
        "stated": "2026-08-20, before the first production sweep",
        "note": ("Predictions are depths on the p-line for each open term. "
                 "Each term is its own sweep from the floor: the differences "
                 "P(n) differ, so no term's depth bounds another's."),
        "validation": [{"n": n, "a_n": p, "E_at_a_n": e} for n, p, e in rows],
        "validation_sum": sum(e for _n, _p, e in rows),
        "validation_expected": len(rows),
        "predictions": preds,
    }
    with open(path, "w", newline="\n") as f:   # LF: the file is committed
        json.dump(doc, f, indent=1)
    return doc


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown

    def _main():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
        doc = write()
        print("\nvalidation (E at each known -- should scatter around 1):")
        for row in doc["validation"]:
            print("  a(%2d) = %-14d  E = %.2f" % (row["n"], row["a_n"],
                                                  row["E_at_a_n"]))
        print("  sum %.2f against %d expected"
              % (doc["validation_sum"], doc["validation_expected"]))
        print("\npredictions (depth on the p-line):")
        for n in OPEN:
            q = doc["predictions"][str(n)]
            print("  a(%2d)  Q1 %-10.3g median %-10.3g Q3 %-10.3g P90 %-10.3g"
                  % (n, q.get("Q1", float("nan")), q.get("median", float("nan")),
                     q.get("Q3", float("nan")), q.get("P90", float("nan"))))
        print("\nwrote model_results.json")

    sys.exit(_shutdown.graceful(_main) or 0)
