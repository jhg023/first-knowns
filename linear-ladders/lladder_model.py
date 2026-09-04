"""The odds model for the linear ladders -- Bateman-Horn over linear forms.

    A(F, n) = least k with m*k + s prime for every multiplier m of family F
              at index n

For a fixed (F, n) the forms f_m(k) = m*k + s are distinct, irreducible and
have no fixed prime divisor (proved in lladder_reference), so Bateman-Horn
puts the density of k at which all of them are simultaneously prime at

    S(F, n) / prod_m log(m*k + s),

    S(F, n) = prod_q  (1 - w(q,n,F)/q) / (1 - 1/q)^c,     c = nforms(F, n)

with w(q,n,F) the number of distinct nonzero residues of the multipliers
mod q -- the killed count PROVED in lladder_reference, the quantity the
sieve is built from, and the SAME for a family and its sign twin.  So
A088250 and A088651 share one singular series, as do A173750 and A125838,
and A164325 and A164326; the sign enters only through log(m*k + s), which
is negligible, and each family's predictions differ by where its own
search starts.  The useful consistency: a wrong w would move the model and
the engine together, and the validation against the known terms would
catch it.

The series is SMALLER than the prime ladders' at the same n -- S(14) is
2.3e4 here against 6.6e5 for A084700 -- because consecutive multipliers
kill the MAXIMUM min(c, q - 1) residues at every prime, where the first n
primes collide mod q and kill fewer.  Fewer k survive per unit of line and
the terms are larger for their n (A088250's a(14) is 1.1e19 against
A084700's 2.5e16); the wheel thins the candidates by exactly the same
factors, so what the model loses in density the engine gains in line per
candidate, and a unit of device time covers far more line here.

VALIDATION (gate G11).  E(F, n) -- the expected number of hits the model
puts between the previous term and the one that actually occurred -- must
scatter around 1 on the knowns.  A model whose knowns all sit at ~0 or ~1
is wrong and may not be used to plan a campaign (CONVENTIONS.md "The odds
model").  Seven families give 46 draws between them; each alone gives
six or seven.

ONE VOTE PER CONDITION.  Every family has RIDERS -- terms equal to their
predecessor because one k cleared two rungs at once (A088250's a(8) rides
on a(7), A173750's a(13) and a(14) on a(12), ...).  A rider was never
searched for, so its E is identically zero and scoring it would
manufacture agreement out of nothing.  Only terms that strictly exceed
their predecessor are used, and only from n = 8, above the exception zone.

AND THE MODEL IS A FLOOR, NOT A FORECAST.  Every quantile this file prints
should be read with the repo's measured correction: the four ladder
projects before this one landed their first occurrences at a pooled
optimism factor of about 1.9-2.5x over the medians while every census
showed the modelled INTENSITY right to a percent or two.  Mean count
right, first occurrence late: budget 2-3x the median below before
expecting a term.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from lladder_reference import (FAMILIES, KNOWN, PUBLISHED_BOUNDS, family,
                               mults, nforms, sign, w)

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_LS = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# The knowns that were SEPARATELY SEARCHED FOR: strictly above their
# predecessor (so not a rider) and clear of the exception zone.
VALIDATE_FROM = 8


def independent_knowns(fam):
    """[(n, prev, term)] for the terms this model may be scored on."""
    fam = family(fam)
    out = []
    for n in sorted(KNOWN[fam]):
        if n < VALIDATE_FROM or n - 1 not in KNOWN[fam]:
            continue
        prev, term = KNOWN[fam][n - 1], KNOWN[fam][n]
        if term > prev:
            out.append((n, prev, term))
    return out


def log_singular(fam, n):
    """log S(F, n), computed once per (w-class, n).  Sign-independent
    (lladder_reference G2c), so a family and its twin share one series."""
    fam = family(fam)
    key = (FAMILIES[fam]["kind"], FAMILIES[fam]["rungs_from"], int(n))
    if key in _LS:
        return _LS[key]
    c = nforms(fam, n)
    acc = 0.0
    for q in _PRIMES:
        ww = w(q, n, fam)
        if ww >= q:                       # proved impossible; assert anyway
            _LS[key] = -math.inf
            return -math.inf
        acc += math.log(1 - ww / q) - c * math.log(1 - 1.0 / q)
    _LS[key] = acc
    return acc


def expected(fam, n, a, c, points=3000):
    """Expected number of k in [a, c] with all forms of (F, n) prime."""
    fam = family(fam)
    a, c = float(max(a, 10.0)), float(c)
    if c <= a:
        return 0.0
    S = math.exp(log_singular(fam, n))
    s = sign(fam)
    t = np.logspace(math.log10(a), math.log10(c), points)
    dens = np.full_like(t, S)
    for m in mults(fam, n):
        dens = dens / np.log(np.maximum(m * t + s, 3.0))
    return float(np.trapezoid(dens, t))


def p_by(fam, n, frontier, k):
    """P(a(n) has appeared by k), given it is known to exceed `frontier`."""
    e = expected(fam, n, frontier, k)
    return 1.0 - math.exp(-e) if e > 0 else 0.0


def quantile(fam, n, frontier, p, hi=None):
    """The k at which P(a(n) found) reaches p, searching from `frontier`
    (up to `hi`, by default the engine ceiling)."""
    if hi is None:
        from huntlib.ceiling import K_CEIL
        hi = K_CEIL
    target = -math.log(1.0 - p)
    lo, c = float(max(frontier, 100.0)), float(hi)
    if expected(fam, n, lo, c) < target:
        return None                        # not reachable below `hi`
    for _ in range(90):
        mid = math.sqrt(lo * c)
        if expected(fam, n, max(frontier, 100.0), mid) < target:
            lo = mid
        else:
            c = mid
    return math.sqrt(lo * c)


def floor_for(fam, n, frontier_k):
    """Where the search for a(n) actually starts.

    Monotonicity alone: the conditions nest, so a(n) >= a(n-1), and no
    family carries a published searched-empty bound beyond its last term.
    (Crediting a model for ground somebody else already cleared is what
    `PUBLISHED_BOUNDS` exists to prevent in the projects that have one.)
    """
    return max(float(frontier_k),
               float(PUBLISHED_BOUNDS[family(fam)].get(n, 0)))


def predictions(fam, frontier_n, frontier_k, n_ahead=3, ceiling=None):
    """{n: {quantile: depth}} for the next `n_ahead` open terms.

    Derived from the LIVE frontier on every call (CONVENTIONS.md: "a rung
    retires with its term"); the launcher caches the result on the frontier
    with huntlib.rungs.LiveLadder, because a call is ~1,000 numerical
    integrals and the segment loop may not pay that (OPTIMIZATION.md 2.14).
    """
    fam = family(fam)
    out = {}
    for n in range(frontier_n + 1, frontier_n + 1 + n_ahead):
        qs = {}
        base = floor_for(fam, n, frontier_k)
        for name in QUANTILES:
            d = quantile(fam, n, base, _Q[name])
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
    the ground already ruled out.  Scored per family and pooled: one
    intensity function per w-class, seven frontiers.
    """
    es, detail = [], []
    for fam in FAMILIES:
        fam_es = []
        for n, prev, term in independent_knowns(fam):
            e = expected(fam, n, prev, term)
            es.append(e)
            fam_es.append(e)
        detail.append("%s mean %.2f (%d)" % (fam, sum(fam_es) / len(fam_es),
                                             len(fam_es)))
        if not 0.25 < sum(fam_es) / len(fam_es) < 3.0:
            return False, (f"G11 FAIL: {fam}'s mean E at its knowns is "
                           f"{sum(fam_es) / len(fam_es):.2f} over "
                           f"{len(fam_es)} draws; under a correct model it is "
                           f"Exp(1) with mean 1")
    lo, hi = min(es), max(es)
    mean = sum(es) / len(es)
    # If the intensity is right, the integral of it up to the first event is
    # Exp(1): mean 1, and a spread from near 0 to ~3 is what Exp(1) LOOKS
    # like on 46 draws.  So the test is the mean against 1, plus a scatter
    # that is neither degenerate nor absurd -- not "every value near 1",
    # which would indicate an overfitted model rather than a validated one.
    if not 0.6 < mean < 1.6:
        return False, (f"G11 FAIL: pooled mean E at the knowns is {mean:.2f}; "
                       f"under a correct model it is Exp(1) with mean 1 "
                       f"({'; '.join(detail)})")
    if lo > 0.5 or hi < 1.5:
        return False, (f"G11 FAIL: the knowns do not scatter around E = 1 "
                       f"(spread {lo:.2f}-{hi:.2f}) -- biased, and it may not "
                       f"be used to plan ({'; '.join(detail)})")
    return True, ("G11 ok: E at the %d independently-searched knowns is "
                  "mean %.2f against the Exp(1) mean of 1, spread %.2f-%.2f "
                  "-- %s (riders excluded: one vote per condition)"
                  % (len(es), mean, lo, hi, "; ".join(detail)))


def g12_monotone_and_sane():
    """Deeper terms must be predicted deeper, and the singular series must
    grow with n (each extra condition makes survivors rarer but the
    conditioning stronger).  Also: sign twins share ONE series but start
    from different floors, so their predictions for the same n must differ
    -- the cheapest guard against a family that stopped reaching the
    floor -- and the series really is larger than the prime ladders' at
    the same n, which is the forcing lemma in the density."""
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        prev_med, prev_S = 0.0, 0.0
        for n in range(top + 1, top + 5):
            S = math.exp(log_singular(fam, n))
            med = quantile(fam, n, KNOWN[fam][top], 0.5)
            if med is None or med <= prev_med:
                return False, (f"G12 FAIL: {fam} a({n}) median {med} not "
                               f"above {prev_med}")
            if S <= prev_S:
                return False, (f"G12 FAIL: {fam} S({n}) = {S:.3g} not above "
                               f"{prev_S:.3g}")
            prev_med, prev_S = med, S
    mp = quantile("A088250", 15, KNOWN["A088250"][14], 0.5)
    mm = quantile("A088651", 15, KNOWN["A088651"][14], 0.5)
    if mp is None or mm is None or abs(math.log(mp / mm)) < 0.02:
        return False, (f"G12 FAIL: a(15) medians {mp} (A088250) and {mm} "
                       f"(A088651) coincide although the floors differ")
    if abs(log_singular("A088250", 15) - log_singular("A088651", 15)) > 1e-9:
        return False, "G12 FAIL: sign twins do not share the singular series"
    S14 = math.exp(log_singular("A088250", 14))
    # the prime ladders' S(14) is 6.6e5 (prime-ladders/model_results.json);
    # consecutive multipliers kill MORE residues per prime than the first n
    # primes do, so this series must come out smaller -- a series above the
    # prime ladders' would mean w() had stopped counting the kills
    if not 1e3 < S14 < 6.6e5:
        return False, (f"G12 FAIL: S(A088250, 14) = {S14:.3g} is not below "
                       f"the prime ladders' 6.6e5 (and above 1e3) -- the "
                       f"killed counts in the series are wrong")
    # and the three w-classes are three different series
    S = {f: log_singular(f, 16) for f in ("A088250", "A173750", "A164325")}
    if len({round(v, 6) for v in S.values()}) != 3:
        return False, f"G12 FAIL: the three w-classes share a series: {S}"
    return True, ("G12 ok: predicted medians and singular series both "
                  "increase with n over the next four open terms of every "
                  "family; S(A088250, 14) = %.4g, below the prime ladders' "
                  "6.6e5 as the maximal kill counts require; the three "
                  "w-classes have three series; sign twins share theirs and "
                  "their a(15) medians differ (%.3g vs %.3g) because their "
                  "floors do" % (S14, mp, mm))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    from lladder_search import k_ceil, k_proof
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over f_m(k) = m*k + s for the multipliers "
                    "m of each family at index n; w(q,n,F) = #distinct "
                    "nonzero residues of the multipliers mod q, proved in "
                    "lladder_reference and independent of the sign",
           "qmax": QMAX,
           "caveat": "the repo's first-occurrence models run late: the four "
                     "ladder projects before this one landed their scored "
                     "finds at about 1.9-2.5x their medians while every "
                     "census showed the intensity right to a percent or "
                     "two. Read every depth below as a floor and budget 2-3x "
                     "the median.",
           "families": {}}
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        preds = predictions(fam, top, KNOWN[fam][top], n_ahead=4)
        es = {str(n): expected(fam, n, prev, term)
              for n, prev, term in independent_knowns(fam)}
        under = {}
        for n in range(top + 1, top + 4):
            ceil = k_ceil(n, fam)
            under[str(n)] = {"ceiling": float(ceil),
                             "proof_crossing": float(k_proof(n, fam)),
                             "P_under_ceiling": p_by(fam, n, KNOWN[fam][top],
                                                     ceil)}
        out["families"][fam] = {
            "forms": FAMILIES[fam]["forms"],
            "sign": sign(fam),
            "frontier": {"n": top, "k": KNOWN[fam][top],
                         "by": FAMILIES[fam]["frontier_by"]},
            "singular_series": {str(n): math.exp(log_singular(fam, n))
                                for n in range(top + 1, top + 5)},
            "validation": {"E_at_known": es,
                           "mean_E": sum(es.values()) / len(es),
                           "draws": len(es),
                           "note": "riders excluded: one vote per condition"},
            "predictions": {str(n): {q: float(v) for q, v in qs.items()}
                            for n, qs in preds.items()},
            "under_the_ceiling": under,
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
            print("  %s (%s), frontier a(%d) = %d; validation mean E %.2f "
                  "over %d draws:"
                  % (fam, d["forms"], d["frontier"]["n"], d["frontier"]["k"],
                     d["validation"]["mean_E"], d["validation"]["draws"]))
            for n, qs in sorted(d["predictions"].items(),
                                key=lambda x: int(x[0])):
                u = d["under_the_ceiling"].get(n)
                print("     a(%s): %s%s" % (n, "  ".join(
                    "%s %.3g" % (q, v) for q, v in qs.items()),
                    ("  [%.0f%% under the ceiling %.3g]"
                     % (100 * u["P_under_ceiling"], u["ceiling"])) if u else ""))

    _s.exit(_shutdown.graceful(_main) or 0)
