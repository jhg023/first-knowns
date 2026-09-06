"""The odds model for the lcm ladders -- Bateman-Horn over linear forms.

    A(F, n) = least N = L(n)*x with (L(n)/k)*x + s prime for k = 1..n

For a fixed n the forms f_k(x) = (L/k)*x + s are distinct, irreducible and
have no fixed prime divisor (proved in lcml_reference), so Bateman-Horn puts
the density of x at which all of them are simultaneously prime at

    S(n) / prod_k log((L/k)*x + s),

    S(n) = prod_q  (1 - w(q,n)/q) / (1 - 1/q)^n

with w(q,n) = floor(n/q^e) for q <= n and n for q > n -- the killed count
PROVED in lcml_reference, the quantity the sieve is built from, and the same
for BOTH families.  So A078502 and A074200 share one singular series
exactly; the sign enters only through log((L/k)*x + s), which is negligible,
and their predictions differ only because their frontiers do.  The useful
consistency: a wrong w would move the model and the engine together, and the
validation against the known terms would catch it.

EVERYTHING HERE IS IN x, NOT IN N.  The published term is N = L(n)*x and L
changes with n, so a depth quoted in N means a different amount of work at
every filter.  The campaign cursor is x; so are all the quantiles; the
launcher multiplies by L(n) when it prints a term.  `floor_for` is the one
place the conversion happens, and it converts the MONOTONICITY bound -- the
previous term, in N -- into this filter's x.

The series is far LARGER than the linear ladders' at the same n -- S(15) is
1.3e8 here against 2.9e4 there -- and that is the same fact as the weak
wheel, seen from the other side.  The lcm multipliers are nearly all
divisible by each small prime, so those primes kill almost nothing
(w(3,15) = 1 against min(15, 2) = 2; w(5,15) = 3 against 4; w(7,15) = 2
against 6), which leaves far more x alive per unit of line AND makes each
surviving x far likelier to be a hit.  What the engine loses in candidates
per unit of line it gets back in terms per candidate.

VALIDATION (gate G11).  E(F, n) -- the expected number of hits the model
puts between the previous term and the one that actually occurred -- must
scatter around 1 on the knowns.  A model whose knowns all sit at ~0 or ~1
is wrong and may not be used to plan a campaign (CONVENTIONS.md "The odds
model").  Two families give 12 draws between them.

ONE VOTE PER CONDITION.  Both families have RIDERS -- terms equal to their
predecessor because one N cleared two rungs at once (A078502's a(4) on
a(3), a(8) on a(7) and a(14) on a(13); A074200's a(7) on a(6)).  A rider was
never searched for, so its E is identically zero and scoring it would
manufacture agreement out of nothing.  Only terms that strictly exceed their
predecessor are used, and only from n = 8, above the exception zone.

AND THE MODEL IS A FLOOR, NOT A FORECAST.  Every quantile this file prints
should be read with the repo's measured correction: the ladder projects
before this one landed their first occurrences at a pooled optimism factor
of about 1.9-2.5x over the medians while every census showed the modelled
INTENSITY right to a percent or two.  Mean count right, first occurrence
late: budget 2-3x the median below before expecting a term.

WHAT IT PREDICTS, stated before the run -- see model_results.json.
"""

import json
import math
import os

import numpy as np
from sympy import primerange

from lcml_reference import (FAMILIES, KNOWN, L, PUBLISHED_BOUNDS, family,
                            mults, nforms, sign, w_closed)

QMAX = 200_000
_PRIMES = list(primerange(2, QMAX))
_LS = {}

QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.5, "Q3": 0.75, "P90": 0.90}

# The knowns that were SEPARATELY SEARCHED FOR: strictly above their
# predecessor (so not a rider) and clear of the exception zone.
VALIDATE_FROM = 8


def independent_knowns(fam):
    """[(n, prev_N, term_N)] for the terms this model may be scored on."""
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
    """log S(n).  Family-INDEPENDENT: w(q,n) does not depend on the sign
    (lcml_reference G2c), so both families share one series exactly, and the
    cache is keyed on n alone."""
    family(fam)
    n = int(n)
    if n in _LS:
        return _LS[n]
    c = n
    acc = 0.0
    for q in _PRIMES:
        ww = w_closed(q, n)
        if ww >= q:                       # proved impossible; assert anyway
            _LS[n] = -math.inf
            return -math.inf
        acc += math.log(1 - ww / q) - c * math.log(1 - 1.0 / q)
    _LS[n] = acc
    return acc


def expected(fam, n, a, c, points=3000):
    """Expected number of x in [a, c] with all forms of (F, n) prime.

    In x, not N.  `a` and `c` are x depths at filter n.
    """
    fam = family(fam)
    a, c = float(max(a, 2.0)), float(c)
    if c <= a:
        return 0.0
    S = math.exp(log_singular(fam, n))
    s = sign(fam)
    t = np.logspace(math.log10(a), math.log10(c), points)
    dens = np.full_like(t, S)
    for m in mults(fam, n):
        dens = dens / np.log(np.maximum(m * t + s, 3.0))
    return float(np.trapezoid(dens, t))


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


def floor_for(fam, n, frontier_N):
    """Where the search for a(n) actually starts, in x at filter n.

    Monotonicity alone: the conditions nest in N, so a(n) >= a(n-1), and
    neither entry carries a published searched-empty bound beyond its last
    term.  This is the ONE place the model converts between N and x, and it
    rounds UP -- an x below ceil(prev/L) would stand for an N the previous
    term has already excluded, and crediting the model for ground somebody
    else already cleared is what `PUBLISHED_BOUNDS` exists to prevent.
    """
    fam = family(fam)
    base = max(int(frontier_N), int(PUBLISHED_BOUNDS[fam].get(n, 0)))
    return -(-base // L(n))               # ceil


def predictions(fam, frontier_n, frontier_N, n_ahead=3, ceiling=None):
    """{n: {quantile: x depth}} for the next `n_ahead` open terms.

    Derived from the LIVE frontier on every call (CONVENTIONS.md: "a rung
    retires with its term"); the launcher caches the result on the frontier
    with huntlib.rungs.LiveLadder, because a call is ~1,000 numerical
    integrals and the segment loop may not pay that (OPTIMIZATION.md 2.14).
    """
    fam = family(fam)
    out = {}
    for n in range(frontier_n + 1, frontier_n + 1 + n_ahead):
        qs = {}
        base = floor_for(fam, n, frontier_N)
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
    when the search for this one began; starting at 0 would double-count the
    ground already ruled out.  Scored per family and pooled.
    """
    es, detail = [], []
    for fam in FAMILIES:
        fam_es = []
        for n, prev, t in independent_knowns(fam):
            e = expected(fam, n, floor_for(fam, n, prev), t / L(n))
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
    # If the intensity is right, the integral of it up to the first event is
    # Exp(1): mean 1, and a spread from near 0 to ~3 is what Exp(1) LOOKS
    # like on a dozen draws.  So the test is the mean against 1, plus a
    # scatter that is neither degenerate nor absurd -- not "every value near
    # 1", which would indicate an overfitted model rather than a validated
    # one.
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
    """Deeper terms must be predicted deeper IN N; the two families must
    share the series exactly; the series must be far larger than the linear
    ladders'; and the series must be NON-monotone in exactly the way the
    sporadic forcing requires.

    That last clause is the one worth stating.  Every earlier ladder project
    in this repo has S increasing with n, and inheriting that assumption here
    produces a gate that fails on correct code: S(18) < S(17), because
    q = 3 goes from w = 1 to w = 2 (forced) at n = 18.  The large jumps go
    the other way and are just as structural -- when n is PRIME it enters
    L(n), so q = n's kill count collapses from n - 1 (every multiplier
    distinct mod q, because q > n - 1) to 1 (only k = n leaves L/k
    invertible), and the series jumps by ~q.  Both directions are asserted
    against their mechanism, not against a number.
    """
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        prev_med = 0.0
        for n in range(top + 1, top + 5):
            med = quantile(fam, n, floor_for(fam, n, KNOWN[fam][top]), 0.5)
            if med is None:
                return False, f"G12 FAIL: {fam} a({n}) has no median"
            medN = med * L(n)
            if medN <= prev_med:
                return False, (f"G12 FAIL: {fam} a({n}) median N {medN:.4g} "
                               f"not above {prev_med:.4g}")
            if not 0 < math.exp(log_singular(fam, n)) < math.inf:
                return False, f"G12 FAIL: S({n}) is not finite and positive"
            prev_med = medN
    ratio = {n: math.exp(log_singular("A078502", n)
                         - log_singular("A078502", n - 1))
             for n in range(15, 24)}
    for n in (17, 19, 23):
        if ratio[n] < 10:
            return False, (f"G12 FAIL: n = {n} is prime, so q = {n} enters "
                           f"L(n) and its kill count must collapse, but S "
                           f"only moved x{ratio[n]:.2f}")
        if w_closed(n, n) != 1 or w_closed(n, n - 1) != n - 1:
            return False, (f"G12 FAIL: the collapse at the prime n = {n} is "
                           f"not w = {n-1} -> 1 (got {w_closed(n, n-1)} -> "
                           f"{w_closed(n, n)})")
    for n in (18, 20, 21, 22):
        if ratio[n] >= 10:
            return False, (f"G12 FAIL: n = {n} is composite but S jumped "
                           f"x{ratio[n]:.2f}")
    if ratio[18] >= 1.0:
        return False, ("G12 FAIL: S(18) is not BELOW S(17); the series is "
                       "expected to fall where a prime becomes forced")
    if not (w_closed(3, 17) == 1 and w_closed(3, 18) == 2):
        return False, ("G12 FAIL: q = 3 does not become forced at n = 18, so "
                       "the S(18) < S(17) dip has no mechanism")
    if abs(log_singular("A078502", 15) - log_singular("A074200", 15)) > 1e-12:
        return False, "G12 FAIL: the two families do not share the series"
    mp = quantile("A078502", 15, floor_for("A078502", 15, KNOWN["A078502"][14]), 0.5)
    mm = quantile("A074200", 15, floor_for("A074200", 15, KNOWN["A074200"][14]), 0.5)
    if mp is None or mm is None:
        return False, "G12 FAIL: a(15) has no median"
    S15 = math.exp(log_singular("A078502", 15))
    # the linear ladders' S(15) is 2.9e4 (linear-ladders/model_results.json);
    # the lcm multipliers are divisible by every small prime for all but a
    # few k, so those primes kill far FEWER residues and the series must
    # come out much larger -- a series near the linear ladders' would mean
    # w() had reverted to min(n, q-1)
    if not 1e6 < S15 < 1e10:
        return False, (f"G12 FAIL: S(15) = {S15:.3g} is not far above the "
                       f"linear ladders' 2.9e4 -- the killed counts in the "
                       f"series look like the wrong family's")
    if abs(mp / mm - 1) > 0.5:
        return False, (f"G12 FAIL: the a(15) medians {mp:.4g} and {mm:.4g} "
                       f"differ by more than the floors can explain")
    return True, ("G12 ok: predicted medians in N increase with n over the "
                  "next four open terms of both families; S(15) = %.4g, three "
                  "orders above the linear ladders' 2.9e4 as the weak "
                  "small-prime kills require; the two families share the "
                  "series exactly and their a(15) medians in x agree to %.1f%% "
                  "(%.4g vs %.4g), the frontiers being nearly equal; and the "
                  "series is NON-monotone exactly where the sporadic forcing "
                  "says -- x%.1f at the prime n = 17 and x%.1f at n = 19 "
                  "(q = n enters L and its kill count collapses from n - 1 to "
                  "1), against x%.3f at n = 18, a FALL, because q = 3 becomes "
                  "forced there"
                  % (S15, 100 * abs(mp / mm - 1), mp, mm, ratio[17],
                     ratio[19], ratio[18]))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    from lcml_search import forced_unit, k_ceil, k_proof
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over f_k(x) = (L(n)/k)*x + s, k = 1..n, "
                    "with N = L(n)*x and L(n) = lcm(1..n); w(q,n) = "
                    "floor(n/q^e) for q <= n and n for q > n, proved in "
                    "lcml_reference and independent of the sign, so both "
                    "families share one singular series",
           "qmax": QMAX,
           "units": "every depth is in x at the stated filter; the published "
                    "term is N = L(n)*x",
           "caveat": "the repo's first-occurrence models run late: the ladder "
                     "projects before this one landed their scored finds at "
                     "about 1.9-2.5x their medians while every census showed "
                     "the intensity right to a percent or two. Read every "
                     "depth below as a floor and budget 2-3x the median.",
           "families": {}}
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        preds = predictions(fam, top, KNOWN[fam][top], n_ahead=4)
        es = {str(n): expected(fam, n, floor_for(fam, n, prev), t / L(n))
              for n, prev, t in independent_knowns(fam)}
        under = {}
        for n in range(top + 1, top + 4):
            ceil = k_ceil(n, fam)
            under[str(n)] = {
                "ceiling_x": float(ceil),
                "proof_crossing_x": float(k_proof(n, fam)),
                "unit": forced_unit(n, fam),
                "L": L(n),
                "P_under_ceiling": p_by(fam, n,
                                        floor_for(fam, n, KNOWN[fam][top]),
                                        ceil)}
        out["families"][fam] = {
            "forms": FAMILIES[fam]["forms"],
            "sign": sign(fam),
            "frontier": {"n": top, "N": KNOWN[fam][top],
                         "x": KNOWN[fam][top] // L(top),
                         "by": FAMILIES[fam]["frontier_by"]},
            "singular_series": {str(n): math.exp(log_singular(fam, n))
                                for n in range(top + 1, top + 5)},
            "validation": {"E_at_known": es,
                           "mean_E": sum(es.values()) / len(es),
                           "draws": len(es),
                           "note": "riders excluded: one vote per condition"},
            "predictions_x": {str(n): {q: float(v) for q, v in qs.items()}
                              for n, qs in preds.items()},
            "predictions_N": {str(n): {q: float(v) * L(int(n))
                                       for q, v in qs.items()}
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
                  % (fam, d["forms"], d["frontier"]["n"], d["frontier"]["N"],
                     d["validation"]["mean_E"], d["validation"]["draws"]))
            for n, qs in sorted(d["predictions_x"].items(),
                                key=lambda x: int(x[0])):
                u = d["under_the_ceiling"].get(n)
                print("     a(%s) in x: %s%s" % (n, "  ".join(
                    "%s %.3g" % (q, v) for q, v in qs.items()),
                    ("  [unit %d, L %d, %.0f%% under the ceiling]"
                     % (u["unit"], u["L"], 100 * u["P_under_ceiling"]))
                    if u else ""))

    _s.exit(_shutdown.graceful(_main) or 0)
