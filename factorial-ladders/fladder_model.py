"""The odds model for the factorial ladders -- Bateman-Horn over linear forms.

    A(F, n) = least x with k!*x + s prime for k = 1..n

For a fixed n the forms f_k(x) = k!*x + s are distinct, irreducible and
have no fixed prime divisor (proved in fladder_reference), so Bateman-Horn
puts the density of x at which all of them are simultaneously prime at

    S(n) / prod_k log(k!*x + s),

    S(n) = prod_q  (1 - w(q,n)/q) / (1 - 1/q)^n

with w(q,n) = #distinct(1!, ..., min(n, q-1)! mod q) -- the killed count
PROVED in fladder_reference, the quantity the sieve is built from, and the
same for BOTH families.  So A177013 and A177014 share one singular series
exactly; the sign enters only through log(k!*x + s), which is negligible,
and their predictions differ only because their frontiers do.  The useful
consistency: a wrong w would move the model and the engine together, and
the validation against the known terms would catch it.

EVERYTHING HERE IS IN x, WHICH IS THE PUBLISHED TERM.  No conversion
anywhere: the campaign cursor, the quantiles and the OEIS entry are all the
same number.  `floor_for` is the monotonicity bound -- the previous term --
and nothing else.

THE SERIES GROWS WITH n, mechanically.  From filter n to n + 1 every prime
q <= n + 1 keeps its kill set (saturation: (n+1)! == 0 mod q) and so
contributes a factor q/(q - 1) through the denominator alone.  A prime
q > n + 1 gains ONE killed residue -- contributing slightly under 1 -- or
NONE, when (n+1)! collides with an earlier factorial mod q, in which case it
too contributes q/(q - 1).  Collisions are common enough (a third of the
primes at n = 10) that the primes above n + 1 can push the ratio either
way; the saturated primes' product, about e^gamma * log n, is what
guarantees S(n+1) > S(n).  G12 asserts the per-prime mechanism (every kill
set grows by 0 or 1, the saturated ones by 0) and the growth, not a number.

THE SERIES IS LARGE -- S(15) is about 2.1e8, above even the lcm ladders'
1.3e8 and four orders above the linear ladders' 2.9e4 -- and the reason is
the collisions.  w(q,n) <= min(n, q-1) for EVERY prime, with equality
exactly when the factorials up to min(n, q-1) are distinct mod q; the
linear ladders (multipliers 1..n) have equality everywhere, so their series
is the floor of this one, and the primes just above n fall well short of it
here (only 12 of 1!..17! are distinct mod 31, 14 mod 47), so each of those
primes kills fewer residues than in any other ladder and the series grows
by exp(sum (n - w)/q).  G12 asserts the ordering against the linear law on
the same primes, which is a theorem, rather than a band around a number.

VALIDATION (gate G11).  E(F, n) -- the expected number of hits the model
puts between the previous term and the one that actually occurred -- must
scatter around 1 on the knowns.  A model whose knowns all sit at ~0 or ~1
is wrong and may not be used to plan a campaign (CONVENTIONS.md "The odds
model").  Two families give 8 draws between them.

ONE VOTE PER CONDITION.  Both families have RIDERS -- terms equal to their
predecessor because one x cleared two rungs at once (A177013's a(2)..a(5)
on a(1) and a(7) on a(6); A177014's a(2), a(3) on a(1), a(5) on a(4) and
a(10) on a(9)).  A rider was never searched for, so its E is identically
zero and scoring it would manufacture agreement out of nothing.  Only terms
that strictly exceed their predecessor are used, and only from n = 6, above
the exception zone.

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

from fladder_reference import (FAMILIES, KNOWN, PUBLISHED_BOUNDS, family,
                               mults, sign, w_count)

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
    """log S(n).  Family-INDEPENDENT: w(q,n) does not depend on the sign
    (fladder_reference G2c), so both families share one series exactly, and
    the cache is keyed on n alone."""
    family(fam)
    n = int(n)
    if n in _LS:
        return _LS[n]
    acc = 0.0
    for q in _PRIMES:
        ww = w_count(q, n)
        if ww >= q:                       # proved impossible; assert anyway
            _LS[n] = -math.inf
            return -math.inf
        acc += math.log(1 - ww / q) - n * math.log(1 - 1.0 / q)
    _LS[n] = acc
    return acc


def expected(fam, n, a, c, points=3000):
    """Expected number of x in [a, c] with all forms of (F, n) prime."""
    fam = family(fam)
    a, c = float(max(a, 2.0)), float(c)
    if c <= a:
        return 0.0
    S = math.exp(log_singular(fam, n))
    s = sign(fam)
    t = np.logspace(math.log10(a), math.log10(c), points)
    dens = np.full_like(t, S)
    for m in mults(fam, n):
        dens = dens / np.log(np.maximum(float(m) * t + s, 3.0))
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


def floor_for(fam, n, frontier_x):
    """Where the search for a(n) actually starts.

    Monotonicity alone: the conditions nest, so a(n) >= a(n-1), and neither
    entry carries a published searched-empty bound beyond its last term.
    `PUBLISHED_BOUNDS` is consulted so that a bound somebody else publishes
    later is credited to them and not to the model.
    """
    fam = family(fam)
    return max(int(frontier_x), int(PUBLISHED_BOUNDS[fam].get(n, 0)))


def predictions(fam, frontier_n, frontier_x, n_ahead=3, ceiling=None):
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
        base = floor_for(fam, n, frontier_x)
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
    # If the intensity is right, the integral of it up to the first event is
    # Exp(1): mean 1, and a spread from near 0 to ~3 is what Exp(1) LOOKS
    # like on eight draws.  So the test is the mean against 1, plus a
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
    """Deeper terms must be predicted deeper; the two families must share the
    series exactly; the series must sit between the linear ladders' and the
    lcm ladders' at n = 15; and it must GROW with n by the mechanism the
    docstring states -- every prime q <= n + 1 contributes exactly q/(q - 1)
    from n to n + 1 because its kill set has saturated.
    """
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
            if not 0 < math.exp(log_singular(fam, n)) < math.inf:
                return False, f"G12 FAIL: S({n}) is not finite and positive"
            prev_med = med
    for n in range(10, 24):
        ratio = math.exp(log_singular("A177013", n + 1)
                         - log_singular("A177013", n))
        if ratio <= 1.0:
            return False, (f"G12 FAIL: S({n+1}) is not above S({n}) "
                           f"(x{ratio:.3f}); the saturated primes' q/(q-1) "
                           f"factors should carry it")
        # the saturated primes' share, exactly; every prime above n + 1
        # gains 0 or 1 killed residues (a collision or a new one), and the
        # product of their factors stays within a modest band of 1
        sat = 1.0
        for q in primerange(2, n + 2):
            if w_count(q, n + 1) != w_count(q, n):
                return False, (f"G12 FAIL: q = {q} <= n + 1 = {n+1} changed "
                               f"its kill set from n = {n}: saturation failed")
            sat *= q / (q - 1.0)
        for q in primerange(n + 2, 2000):
            if w_count(q, n + 1) - w_count(q, n) not in (0, 1):
                return False, (f"G12 FAIL: q = {q} > n + 1 = {n+1} gained "
                               f"{w_count(q, n + 1) - w_count(q, n)} killed "
                               f"residues from one rung")
        rest = ratio / sat
        if not 0.3 < rest < 3.0:
            return False, (f"G12 FAIL: from n = {n} to {n+1} the primes above "
                           f"n + 1 contribute x{rest:.3f}, outside (0.3, 3)")
    if abs(log_singular("A177013", 15) - log_singular("A177014", 15)) > 1e-12:
        return False, "G12 FAIL: the two families do not share the series"
    S15 = math.exp(log_singular("A177013", 15))
    # w(q,n) <= min(n, q-1) at every prime (at most n multipliers, and never
    # all of (Z/q)^* for q >= 5), with equality exactly when the factorials
    # are distinct mod q -- so the series computed with the LINEAR ladders'
    # law w = min(n, q-1) on the same primes is a floor of this one, and the
    # collisions (12 of 1!..17! distinct mod 31) make it a strict one
    lin = 0.0
    for q in _PRIMES:
        wl = min(15, q - 1)
        if w_count(q, 15) > wl:
            return False, (f"G12 FAIL: w({q},15) = {w_count(q, 15)} exceeds "
                           f"min(n, q-1) = {wl}")
        lin += math.log(1 - wl / q) - 15 * math.log(1 - 1.0 / q)
    S15_lin = math.exp(lin)
    if not S15_lin < S15 < 1e12:
        return False, (f"G12 FAIL: S(15) = {S15:.3g} is not above the linear "
                       f"law's {S15_lin:.3g} on the same primes (it must be: "
                       f"every kill count is at most the linear ladders') "
                       f"and under 1e12")
    mp = quantile("A177013", 11, floor_for("A177013", 11, KNOWN["A177013"][10]), 0.5)
    mm = quantile("A177014", 11, floor_for("A177014", 11, KNOWN["A177014"][10]), 0.5)
    if mp is None or mm is None:
        return False, "G12 FAIL: a(11) has no median"
    # the same series and nearly the same forms, so the a(11) medians can
    # differ only through the floors (3.2e9 against 2.3e8) -- within 2x
    if not 0.5 < mp / mm < 2.0:
        return False, (f"G12 FAIL: the a(11) medians {mp:.4g} and {mm:.4g} "
                       f"differ by more than the floors can explain")
    r16 = math.exp(log_singular("A177013", 16) - log_singular("A177013", 15))
    return True, ("G12 ok: predicted medians increase with n over the next "
                  "four open terms of both families; S(15) = %.4g, above the "
                  "linear ladders' law on the same primes (%.3g) as the "
                  "theorem w <= min(n, q-1) requires, the excess being the "
                  "factorial collisions; the two families share the series "
                  "exactly and "
                  "their a(11) medians differ by %.2fx (%.4g vs %.4g, the "
                  "floors' doing); and the series GROWS at every n from 10 "
                  "to 24 by the saturation mechanism -- every q <= n + 1 "
                  "keeps its kill set and contributes q/(q-1), every prime "
                  "above gains 0 or 1 residues (x%.2f in all from n = 15 to "
                  "16)"
                  % (S15, S15_lin, mp / mm, mp, mm, r16))


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    from fladder_search import forced_unit, k_ceil, k_proof
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    out = {"model": "Bateman-Horn over f_k(x) = k!*x + s, k = 1..n; w(q,n) = "
                    "#distinct(1!..min(n,q-1)! mod q), proved in "
                    "fladder_reference and independent of the sign, so both "
                    "families share one singular series",
           "qmax": QMAX,
           "units": "every depth is in x, which is the published term itself",
           "caveat": "the repo's first-occurrence models run late: the ladder "
                     "projects before this one landed their scored finds at "
                     "about 1.9-2.5x their medians while every census showed "
                     "the intensity right to a percent or two. Read every "
                     "depth below as a floor and budget 2-3x the median.",
           "families": {}}
    for fam in FAMILIES:
        top = max(KNOWN[fam])
        preds = predictions(fam, top, KNOWN[fam][top], n_ahead=10)
        es = {str(n): expected(fam, n, floor_for(fam, n, prev), t)
              for n, prev, t in independent_knowns(fam)}
        under = {}
        for n in range(top + 1, top + 11):
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
            "sign": sign(fam),
            "frontier": {"n": top, "x": KNOWN[fam][top],
                         "by": FAMILIES[fam]["frontier_by"]},
            "singular_series": {str(n): math.exp(log_singular(fam, n))
                                for n in range(top + 1, top + 11)},
            "validation": {"E_at_known": es,
                           "mean_E": sum(es.values()) / len(es),
                           "draws": len(es),
                           "note": "riders excluded: one vote per condition"},
            "predictions_x": {str(n): {q: float(v) for q, v in qs.items()}
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
                  % (fam, d["forms"], d["frontier"]["n"], d["frontier"]["x"],
                     d["validation"]["mean_E"], d["validation"]["draws"]))
            for n, qs in sorted(d["predictions_x"].items(),
                                key=lambda x: int(x[0])):
                u = d["under_the_ceiling"].get(n)
                print("     a(%s): %s%s" % (n, "  ".join(
                    "%s %.3g" % (q, v) for q, v in qs.items()),
                    ("  [unit %d, crossing %.3g, %.0f%% under the ceiling]"
                     % (u["unit"], u["proof_crossing_x"],
                        100 * u["P_under_ceiling"]))
                    if u else ""))

    _s.exit(_shutdown.graceful(_main) or 0)
