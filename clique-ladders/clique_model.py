"""clique_model.py -- the odds model for the clique ladders.

Bateman-Horn over the linear forms of an index:

    E(F, n; a, c) = S(F, n) * integral_a^c  dx / prod_{forms} ln(a_i x + b_i)

    S(F, n) = prod_q (1 - w(q,n,F)/q) / (1 - 1/q)^m,   m = nforms(F, n)

with w(q,n,F) the size of the SAME killed set the sieve is built from
(clique_reference), so a wrong w would move the model and the engine
together and the validation below would catch it.

THE MODEL CAN ONLY SEE ONE TERM AHEAD -- EXACTLY.  The form list at index n
is built from a(1..n-1), so the singular series of the index AFTER the open
one depends on a term nobody has.  For the open index every number here is
the model's real answer.  For the indices beyond it (the rung ladder wants
three, the documents want a page) the unknown terms are replaced by
STAND-INS: the first x at or past the previous index's median that survives
every prime under 2000 at that index -- a number with the small-prime
residues a real term must have, at the depth the model expects it.  Those
rows are PROJECTIONS and every consumer labels them so; they are
deterministic, keyed on the real prefix, and recomputed the moment a real
term lands (`_prefix_key`).

VALIDATION (G11), stated before any run.  E -- the expected number of hits
between a(n-1) and the a(n) that actually occurred, given the real prefix --
must scatter around 1: if the intensity is right the integral up to the
first event is Exp(1).  Every published term from n = 9 is a separately
searched draw (there are no riders in this project: a(n) > a(n-1) strictly).

AND THE MODEL IS A FLOOR, NOT A FORECAST.  Every quantile this file prints
should be read with the repo's measured correction: earlier ladder projects
landed their first occurrences at a pooled 1.2-2.5x over the medians while
every census showed the modelled INTENSITY right to a percent or two.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from clique_reference import (FAMILIES, KNOWN, extra, family, forms, frontier,
                              term)

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_SMALL = list(primerange(2, 60))
_STAND_PRIMES = list(primerange(32, 2000))
_LS = {}
_STAND = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# The published terms that were searched for above the exception zone.
VALIDATE_FROM = 9


def _prefix_key(fam):
    """What every cache here is keyed on besides (fam, n): how much of the
    sequence is REAL.  A stand-in is only valid until the term it stands for
    exists."""
    return frontier(fam)


def prefix(fam, n):
    """[a(1..n-1)] with stand-ins past the real frontier, and how many of
    them are stand-ins."""
    fam, n = family(fam), int(n)
    top = frontier(fam)
    real = [term(fam, i) for i in range(1, min(n, top + 1))]
    fake = [stand_in(fam, i) for i in range(top + 1, n)]
    return real + fake, len(fake)


def forms_for(fam, n):
    """forms(F, n), with stand-in terms wherever the real ones do not exist
    yet.  Identical to clique_reference.forms for every index that does."""
    fam = family(fam)
    if int(n) <= frontier(fam) + 1:
        return forms(fam, n)
    pre, _ = prefix(fam, n)
    return list(extra(fam)) + [(1, t + 1) for t in pre]


def _kills(fs, q):
    return {(-b * pow(a, -1, q)) % q for a, b in fs if a % q}


def stand_in(fam, n):
    """The deterministic stand-in for an unknown a(n): the first x at or
    past the modelled median of index n, in an allowed class of every prime
    to 31 (by CRT) and killed by no prime under 2000."""
    fam, n = family(fam), int(n)
    key = (fam, n, _prefix_key(fam))
    if key not in _STAND:
        fs = forms_for(fam, n)
        pre, _ = prefix(fam, n)
        x0 = int(quantile(fam, n, pre[-1], 0.5))
        M, r = 1, 0
        for q in primerange(2, 32):
            k = _kills(fs, q)
            a = next(c for c in range(q) if c not in k)
            r, M = r + M * (((a - r) * pow(M, -1, q)) % q), M * q
        ks = [(q, _kills(fs, q)) for q in _STAND_PRIMES]
        x = x0 - x0 % M + r
        while x < x0 or any((x % q) in k for q, k in ks):
            x += M
        _STAND[key] = x
    return _STAND[key]


def log_singular(fam, n):
    """log S(F, n), over the real prefix and stand-ins past it."""
    fam, n = family(fam), int(n)
    key = (fam, n, _prefix_key(fam) if n > frontier(fam) + 1 else -1)
    if key in _LS:
        return _LS[key]
    fs = forms_for(fam, n)
    ones = [(-b) for a, b in fs if a == 1]
    twos = [b for a, b in fs if a == 2]
    m, acc = len(fs), 0.0
    for q in _PRIMES:
        ks = {c % q for c in ones}
        if q > 2:
            h = (q + 1) // 2                     # 2^-1 mod q
            ks.update((-b * h) % q for b in twos)
        if len(ks) >= q:
            acc = -math.inf
            break
        acc += math.log(1 - len(ks) / q) - m * math.log(1 - 1.0 / q)
    _LS[key] = acc
    return acc


def expected(fam, n, a, c, points=3000):
    """Expected number of x in [a, c] with every form of index n prime."""
    fam = family(fam)
    a, c = float(max(a, 2.0)), float(c)
    if c <= a:
        return 0.0
    S = math.exp(log_singular(fam, n))
    t = np.logspace(math.log10(a), math.log10(c), points)
    dens = np.full_like(t, S)
    for fa, fb in forms_for(fam, n):
        dens = dens / np.log(np.maximum(fa * t + float(fb), 3.0))
    return float(np.trapezoid(dens, t))


def p_by(fam, n, floor_x, x):
    """P(a(n) has appeared by x), given it exceeds `floor_x`."""
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


_SWEEP = {}


def _survival_table(fam, n, floor_x, hi, points=6000):
    """(ln x grid, cumulative E(floor, x), S = exp(-E), integral of S): the
    model's survival curve for a(n) above `floor_x`, tabulated ONCE per
    (family, index, floor) -- a planner asks for it at dozens of segment
    widths, and an `expected` per question would be the 2.14 trap."""
    key = (fam, n, int(floor_x), float(hi), _prefix_key(fam))
    if key not in _SWEEP:
        a = float(max(floor_x, 2.0))
        t = np.logspace(math.log10(a), math.log10(float(hi)), points)
        dens = np.full_like(t, math.exp(log_singular(fam, n)))
        for fa, fb in forms_for(fam, n):
            dens = dens / np.log(np.maximum(fa * t + float(fb), 3.0))
        cum = np.concatenate(
            [[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(t))])
        surv = np.exp(-cum)
        _SWEEP[key] = (np.log(t), cum, float(np.trapezoid(surv, t)))
    return _SWEEP[key]


def expected_sweep(fam, n, floor_x, start_x, seg, hi=None):
    """E[line swept before a(n) is CONFIRMED], when the sweep runs in whole
    segments of `seg` from `start_x` (<= floor_x: the segment boundary under
    the floor) and a find is only known to be the least once ITS segment
    closes -- so the segment holding a(n) is swept to its end, and in this
    project everything past the find is thrown away (the next index has a
    condition the old filter never tested; launch.follow_frontier).

        sum over segments k of  seg * P(a(n) >= start of segment k)

    This is what a plan is priced in: line rate alone says nothing about
    the half segment a find wastes, and the old hard cap (segment <= one
    median) said nothing about rate.  For segments far shorter than the
    search the sum is the integral of the survival curve plus half a
    segment, which is what it returns past 2e6 terms.
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


def floor_for(fam, n, frontier_x):
    """Where the search for a(n) starts: a(n-1) itself, because the
    definition says a(n) > a(n-1) and nothing else is published.  For an
    index past the open one the floor is the stand-in before it."""
    fam, n = family(fam), int(n)
    pre, fakes = prefix(fam, n)
    return max(int(frontier_x), int(pre[-1])) if fakes else int(frontier_x)


def density(fam, n, upto=60):
    """The fraction of x the primes under `upto` let through at index n."""
    fs = forms_for(fam, n)
    d = 1.0
    for q in _SMALL:
        if q < upto:
            d *= 1 - len(_kills(fs, q)) / q
    return d


def predictions(fam, frontier_n, frontier_x, n_ahead=3, ceiling=None):
    """{n: {quantile: x depth}} for the next `n_ahead` indices.  The first
    is the model's real answer; the rest are PROJECTIONS over stand-in terms
    (module docstring).  Derived from the live frontier on every call; the
    launcher caches it with huntlib.rungs.LiveLadder (OPTIMIZATION.md 2.14).
    """
    fam = family(fam)
    out = {}
    for n in range(frontier_n + 1, frontier_n + 1 + n_ahead):
        qs = {}
        base = floor_for(fam, n, frontier_x)
        for name in QUANTILES:
            d = quantile(fam, n, base, _Q[name])
            if d is not None and (ceiling is None or d < ceiling):
                qs[name] = d
        if qs:
            out[n] = qs
    return out


def independent_knowns(fam):
    """[(n, a(n-1), a(n))] for the published terms the model is scored on."""
    fam = family(fam)
    return [(n, KNOWN[fam][n - 1], KNOWN[fam][n])
            for n in sorted(KNOWN[fam]) if n >= VALIDATE_FROM]


# --------------------------------- gates -----------------------------------

def g11_model_validates_on_knowns():
    """E at each published term from n = 9 must scatter around 1, per family
    and pooled.  The window starts at a(n-1): that is the definition's floor,
    and it is what was known when the search for a(n) began."""
    es, detail = [], []
    for fam in FAMILIES:
        fam_es = [expected(fam, n, prev, t)
                  for n, prev, t in independent_knowns(fam)]
        es += fam_es
        mean = sum(fam_es) / len(fam_es)
        detail.append("%s %.2f (%d)" % (fam, mean, len(fam_es)))
        if not 0.2 < mean < 4.0:
            return False, (f"G11 FAIL: {fam}'s mean E at its knowns is "
                           f"{mean:.2f} over {len(fam_es)} draws; under a "
                           f"correct model it is Exp(1) with mean 1")
    lo, hi, mean = min(es), max(es), sum(es) / len(es)
    if not 0.6 < mean < 1.6:
        return False, (f"G11 FAIL: pooled mean E at the knowns is {mean:.2f} "
                       f"({'; '.join(detail)})")
    if lo > 0.5 or hi < 1.5:
        return False, (f"G11 FAIL: the knowns do not scatter around E = 1 "
                       f"(spread {lo:.2f}-{hi:.2f}) -- biased")
    return True, ("G11 ok: E at the %d published terms from n = %d is mean %.2f "
                  "against the Exp(1) mean of 1, spread %.2f-%.2f -- per family "
                  "%s (no riders here: every term is a searched draw)"
                  % (len(es), VALIDATE_FROM, mean, lo, hi, "; ".join(detail)))


def g12_monotone_and_sane():
    """The projections are ordered and finite; one new term adds at most one
    killed residue per prime; the series grows by a sane factor per index;
    the stand-ins are what they claim to be; and the open index does not
    depend on them."""
    rows = []
    for fam in FAMILIES:
        top = frontier(fam)
        prev_med = float(term(fam, top))
        for n in range(top + 1, top + 5):
            med = quantile(fam, n, floor_for(fam, n, term(fam, top)), 0.5)
            if med is None or med <= prev_med:
                return False, (f"G12 FAIL: {fam} a({n}) median {med} is not "
                               f"above {prev_med:.4g}")
            if not 0 < math.exp(log_singular(fam, n)) < math.inf:
                return False, f"G12 FAIL: S({fam}, {n}) is not finite and positive"
            prev_med = med
        if forms_for(fam, top + 1) != forms(fam, top + 1):
            return False, f"G12 FAIL: {fam}'s open index uses a stand-in"
        s = stand_in(fam, top + 1)
        fs = forms_for(fam, top + 1)
        if s <= term(fam, top) or any((fa * s + fb) % q == 0
                                      for fa, fb in fs for q in primerange(2, 2000)):
            return False, f"G12 FAIL: {fam}'s stand-in for a({top + 1}) is killed"
        for n in range(10, top + 1):
            ratio = math.exp(log_singular(fam, n + 1) - log_singular(fam, n))
            if not 1.5 < ratio < 40:
                return False, (f"G12 FAIL: S({fam}) moves x{ratio:.2f} from "
                               f"index {n} to {n + 1}")
            a, b = forms(fam, n), forms(fam, n + 1)
            for q in primerange(2, 400):
                if len(_kills(b, q)) - len(_kills(a, q)) not in (0, 1):
                    return False, (f"G12 FAIL: {fam} q = {q} gained more than "
                                   f"one killed residue from one new term")
        d = density(fam, top + 1)
        if not 1e-7 < d < 1e-3:
            return False, f"G12 FAIL: {fam} keeps {d:.3g} of x to 59"
        rows.append("%s S(%d) = %.3g, %.2g of x to 59"
                    % (fam, top + 1, math.exp(log_singular(fam, top + 1)), d))
    return True, ("G12 ok: projected medians increase over the next four "
                  "indices of every family, the open index uses no stand-in, "
                  "each stand-in survives every prime under 2000 above its "
                  "predecessor, one new term adds 0 or 1 killed residues per "
                  "prime and moves the series by 1.5-40x -- " + "; ".join(rows))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    from clique_search import k_ceil, k_proof
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over the forms of index n: x + a(i) + 1 for "
                    "i < n, plus the family's extra form (2x + 1, or x). "
                    "w(q,n,F) is the size of the sieve's own killed set.",
           "qmax": QMAX,
           "units": "every depth is x, which is the published term itself",
           "projection": "ONLY the first index per family is the model's real "
                         "answer. The form list of every later index depends "
                         "on terms nobody has; those rows replace each unknown "
                         "term by a stand-in (first x past the previous median "
                         "that survives every prime under 2000).",
           "caveat": "first-occurrence models run late in this repository: "
                     "read every depth as a floor and budget 2-3x the median.",
           "families": {}}
    for fam in FAMILIES:
        top = frontier(fam)
        preds = predictions(fam, top, term(fam, top), n_ahead=6)
        es = {str(n): expected(fam, n, prev, t)
              for n, prev, t in independent_knowns(fam)}
        out["families"][fam] = {
            "forms": FAMILIES[fam]["forms"],
            "extra_forms": [list(f) for f in extra(fam)],
            "frontier": {"n": top, "x": term(fam, top),
                         "by": FAMILIES[fam]["frontier_by"]},
            "singular_series": {str(n): math.exp(log_singular(fam, n))
                                for n in preds},
            "density_to_59": {str(n): density(fam, n) for n in preds},
            "validation": {"E_at_known": es,
                           "mean_E": sum(es.values()) / len(es),
                           "draws": len(es)},
            "predictions_x": {str(n): dict({q: float(v) for q, v in qs.items()},
                                           projected=(n > top + 1))
                              for n, qs in preds.items()},
            "stand_ins": {str(n): stand_in(fam, n)
                          for n in range(top + 1, top + 6)},
            "proof_crossing_x": float(k_proof(top + 1, fam)),
            "ceiling_x": float(k_ceil(top + 1, fam)),
            "also_settles": [list(x) for x in FAMILIES[fam]["also"]]}
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
                  % (fam, d["frontier"]["n"], d["frontier"]["x"],
                     d["validation"]["mean_E"], d["validation"]["draws"]))
            for n, qs in sorted(d["predictions_x"].items(), key=lambda z: int(z[0])):
                print("     a(%s)%s: %s" % (
                    n, " (projected)" if qs["projected"] else "",
                    "  ".join("%s %.3g" % (q, qs[q]) for q in QUANTILES if q in qs)))

    _shutdown.graceful(_main)
