# residue_model.py -- THE ODDS MODEL for the power-residue ladders
# (A002226, A002227, A002228, A060363, A060364).
#
# WHAT IS MODELLED.  For a family (a power), the primes p with p - 1
# divisible by the power number pi(x)/(power - 1) below x, and by
# Chebotarev's theorem each of the first n primes is a residue of the power
# mod p for one such p in `power`, independently in the limit: the primes of
# run >= n have density power^-n among them.  So the first prime of run >= n
# past a cursor is, to first order, the first event of a Poisson process
# whose EXPOSURE between lo and hi is
#
#       E_n(lo, hi) = (li(hi) - li(lo)) / ((power - 1) * power^n).
#
# THE PUBLISHED TERMS ARE LATE, AND THE MODEL SAYS SO.  Under independence
# the exposures between consecutive distinct published terms would be
# standard exponentials.  They are not: over the 51 distinct terms of the
# five entries their mean is 1.69, not 1 (gate M1: the independence model is
# REJECTED by a Kolmogorov-Smirnov test, and by 4.9 standard errors on the
# rate).  The cause is a bias of Chebyshev's kind, measured before this
# file was written (OPTIMIZATION_LOG.md, round 0): the primes that are 1 mod
# the power and have small numbers as residues are under-represented at a
# finite height, because the prime ideals of degree two of the cyclotomic
# field -- over the primes that are -1 mod the power -- have EVERY rational
# number as a residue and occupy the class the count is after.  The deficit
# is exactly as the explicit formula predicts for one residue condition
# (89 primes of 121,651 for the quintic line below 4*10^7, predicted 72),
# falls off for products of many primes, and is largest for the leading
# primes 2, 3, 5, 7: 451 primes of run >= 4 below 2*10^7 where independence
# expects 508.  No closed form is claimed for it near a first occurrence,
# where it is far from small.  The model therefore carries ONE fitted
# constant,
#
#       LATE = 0.59  (the maximum-likelihood rate factor over the 51 terms,
#                     standard error 0.08),
#
# and a first occurrence is the first event of a Poisson process of rate
# LATE per unit of exposure.  The fit counts the two intervals the entries
# state EMPTY above their last term (A002227: a(13) > 2^42; A060363: no
# more terms through 10^11) as exposure without an event.  With LATE the
# 51 exposures sit at a Kolmogorov-Smirnov distance of 0.149 from the
# exponential -- against 0.341 without it -- but that is NOT a comfortable
# fit: the constant was estimated from the same 51 numbers, and for a
# fitted exponential of 51 values the 5% point of the distance is 0.149 and
# the 1% point 0.175 (gate M1 simulates that null; the fixed-distribution
# cutoff 0.190 would flatter it).  The published terms are consistent with
# ONE constant only marginally, about one chance in twenty.  The fit is on
# terms below 4.4*10^12; the later half of the terms gives 0.67 and the
# earlier half 0.52, so LATE may well drift toward 1 with height, and the
# campaign's finds are scored against it in RESULTS.md.
#
# WHERE A FORECAST STARTS.  From everything known to be empty: the last
# published term, the bound the entry states above it where it states one,
# and the campaign's own cursor once it is past both (`origin`).  The odds
# of a term at or below its origin are zero.
#
# THE CLOCK.  The sweep has no sieve for the property, so its cost is linear
# in p: RATE is the measured p per second of each family's line at its
# day-long height (BENCHMARKS.md), and a clock is a distance over a rate.
#
# The segment loop never calls this file's quantiles: the launcher caches
# the ladder on the frontier (huntlib.rungs.LiveLadder).

import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
P_CEIL = 2 ** 63
LATE = 0.59
QS = (("Q1", 0.25), ("median", 0.5), ("Q3", 0.75), ("P90", 0.9))
# measured p per second, engine v2, at each family's day-long height:
# the DAY shapes of score.py, 2026-11-21
# (BENCHMARKS.md; updated with the SCORE ledger)
RATE = {5: 5.61e11, 7: 8.45e11, 11: 1.57e12, 13: 1.88e12, 17: 2.49e12}
_GAMMA = 0.5772156649015329


def li(x):
    """The logarithmic integral, by its series in ln x (x > 1)."""
    L = math.log(x)
    s, t = _GAMMA + math.log(L), 1.0
    for k in range(1, 500):
        t *= L / k
        s += t / k
        if t / k < 1e-17 * abs(s):
            break
    return s


def pi_class(power, x):
    """Primes p <= x with p - 1 divisible by the power, to first order."""
    return li(x) / (power - 1) if x > 2 else 0.0


def exposure(power, n, lo, hi):
    """Expected number of primes of run >= n in (lo, hi] at independence."""
    if hi <= lo:
        return 0.0
    return (pi_class(power, hi) - pi_class(power, max(lo, 3))) / power ** n


def odds(power, n, since, pos):
    """P(a(n) <= pos), given that it lies above `since`."""
    return 1.0 - math.exp(-LATE * exposure(power, n, since, pos))


def quantile(power, n, since, u, ceiling=P_CEIL):
    """The p at which odds(power, n, since, p) = u, or None above the
    ceiling."""
    if odds(power, n, since, ceiling) < u:
        return None
    lo, hi = float(max(since, 3)), float(ceiling)
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if odds(power, n, since, mid) < u:
            lo = mid
        else:
            hi = mid
        if hi / lo < 1 + 1e-12:
            break
    return hi


def predictions(power, frontier, cursor, n_ahead=4, ceiling=P_CEIL):
    """{n: {"Q1": p, "median": p, "Q3": p, "P90": p}} for the next open
    terms, from a cursor below which no prime of run > frontier exists.
    A quantile above the ceiling is absent."""
    out = {}
    for n in range(int(frontier) + 1, int(frontier) + 1 + int(n_ahead)):
        row = {}
        for name, u in QS:
            v = quantile(power, n, cursor, u, ceiling)
            if v is not None:
                row[name] = v
        if row:
            out[n] = row
    return out


def clock_seconds(power, lo, hi):
    """Device seconds from p = lo to p = hi at the measured rate."""
    return max(hi - lo, 0.0) / RATE[power]


def exposures_of_known(known, power):
    """The exposures between consecutive DISTINCT published terms (a tie
    a(n) = a(n-1) is one prime of longer run, not a waiting time)."""
    out, prev = [], 2 * power + 1
    for i, p in enumerate(known):
        if i and p == known[i - 1]:
            continue
        out.append(exposure(power, i + 1, prev, p))
        prev = p
    return out


def _ks(us):
    us = sorted(us)
    n = len(us)
    return max(max(abs((i + 1) / n - u), abs(i / n - u))
               for i, u in enumerate(us))


def origin(seq, cursor=0):
    """Where a forecast of the entry's first open term starts: the largest
    of its last published term, the bound the entry states above that term
    (residue_reference.SEARCHED_ABOVE) and a campaign's cursor."""
    import residue_reference as ref
    return max(ref.FAMILIES[seq]["known"][-1],
               ref.SEARCHED_ABOVE.get(seq, 0), int(cursor))


def censored_exposure():
    """{sequence: exposure} of the intervals the entries state empty above
    their last published term: exposure of the first open index with no
    event in it."""
    import residue_reference as ref
    out = {}
    for seq, bound in ref.SEARCHED_ABOVE.items():
        f = ref.FAMILIES[seq]
        out[seq] = exposure(f["power"], len(f["known"]) + 1, f["known"][-1],
                            bound)
    return out


def fit():
    """(rate factor, standard error, {sequence: exposures}) over the
    published terms: the maximum-likelihood rate of a Poisson process seen
    through its events AND the event-free intervals above the last terms
    -- events over total exposure."""
    import residue_reference as ref
    fam = {seq: exposures_of_known(f["known"], f["power"])
           for seq, f in ref.FAMILIES.items()}
    allv = [v for row in fam.values() for v in row]
    c = len(allv) / (sum(allv) + sum(censored_exposure().values()))
    return c, c / math.sqrt(len(allv)), fam


def fitted_ks_null(n, sims=20000, seed=20261121):
    """Sorted Kolmogorov-Smirnov distances of `sims` samples of n standard
    exponentials, each from the exponential with ITS OWN fitted rate: the
    null distribution of the statistic gate M1 reads for LATE (a rate
    estimated from the data pulls the distance in; Lilliefors 1969)."""
    import random
    rng = random.Random(seed)
    out = []
    for _ in range(sims):
        x = [rng.expovariate(1.0) for _ in range(n)]
        r = n / sum(x)
        out.append(_ks([1 - math.exp(-r * v) for v in x]))
    out.sort()
    return out


# ---------------------------------------------------------------- the gates
def gate_m1():
    """Validation against the published terms: independence is rejected,
    the fitted constant is the one in this file, and with it the terms
    scatter (pooled and per family)."""
    c, se, fam = fit()
    allv = [v for row in fam.values() for v in row]
    n = len(allv)
    crit = 1.36 / math.sqrt(n)           # a FIXED distribution: independence
    ks1 = _ks([1 - math.exp(-v) for v in allv])
    ksc = _ks([1 - math.exp(-LATE * v) for v in allv])
    if abs(c - LATE) > 0.01:
        return False, f"M1 the fit gives {c:.3f}, the file says LATE = {LATE}"
    if not ks1 > crit:
        return False, f"M1 KS: independence {ks1:.3f} is not rejected ({crit:.3f})"
    # the fitted rate is judged against the null of a FITTED exponential
    null = fitted_ks_null(n)
    p_fit = sum(1 for d in null if d >= ksc) / len(null)
    q95, q99 = null[int(0.95 * len(null))], null[int(0.99 * len(null))]
    if not (ksc < ks1 / 2 and p_fit > 0.01):
        return False, (f"M1 KS: the fitted rate leaves {ksc:.3f} (p = "
                       f"{p_fit:.3f} against a fitted exponential)")
    means = []
    for seq, row in fam.items():
        us = [1 - math.exp(-LATE * v) for v in row]
        m = sum(us) / len(us)
        if not 0.25 < m < 0.75 or _ks(us) > 1.36 / math.sqrt(len(us)):
            return False, f"M1 {seq}: quantiles do not scatter (mean {m:.2f})"
        means.append(f"{seq} {m:.2f}")
    return True, (f"M1 validation on {n} distinct published terms: under "
                  f"independence their quantiles fail a Kolmogorov-Smirnov "
                  f"test ({ks1:.3f} against {crit:.3f}) -- the terms are "
                  f"LATE; the fitted rate factor, the two stated-empty "
                  f"intervals counted, is {c:.3f} +- {se:.3f} (LATE = {LATE}) "
                  f"and leaves {ksc:.3f}, which for a rate fitted to the same "
                  f"{n} values is MARGINAL, not comfortable: p = {p_fit:.2f} "
                  f"(simulated null: 5% point {q95:.3f}, 1% point {q99:.3f}); "
                  f"mean quantile by family {', '.join(means)}")


def gate_m2():
    """li is the logarithmic integral, and li(x)/(power - 1) counts the
    class: against exact counts below 2*10^7."""
    if abs(li(1e6) - 78627.549) > 0.01 or abs(li(1e12) - 37607950280.8) > 1:
        return False, "M2 li is off"
    from sympy import primerange
    cnt = {d: 0 for d in RATE}
    for p in primerange(3, 2 * 10 ** 7):
        for d in cnt:
            if p % d == 1:
                cnt[d] += 1
    worst = max(abs(cnt[d] / pi_class(d, 2e7) - 1) for d in cnt)
    if worst > 0.005:
        return False, f"M2 class counts off by {100 * worst:.2f}%"
    return True, (f"M2 counting: li(10^6) and li(10^12) to their known "
                  f"values; li(x)/(power - 1) is within {100 * worst:.2f}% of "
                  f"the exact number of primes of each class below 2*10^7")


def gate_m3():
    """Predictions are ordered, respect the ceiling and agree with odds."""
    for d in RATE:
        pr = predictions(d, 10, 5e12, n_ahead=12)
        prev = 0.0
        for n in sorted(pr):
            row = pr[n]
            vals = [row[k] for k, _ in QS if k in row]
            if vals != sorted(vals) or vals[0] <= 5e12 or vals[-1] > P_CEIL:
                return False, f"M3 power {d}: quantiles of a({n}) disordered"
            if "median" in row:
                if abs(odds(d, n, 5e12, row["median"]) - 0.5) > 1e-6:
                    return False, f"M3 power {d}: odds at the median of a({n})"
                if row["median"] <= prev:
                    return False, f"M3 power {d}: medians not increasing"
                prev = row["median"]
        if quantile(d, 60, 5e12, 0.5) is not None or 60 in predictions(
                d, 59, 5e12, n_ahead=1):
            return False, f"M3 power {d}: a quantile above the ceiling"
    return True, ("M3 predictions: quantiles ordered within a term, medians "
                  "increasing with the index, the odds at a median equal to "
                  "one half, and nothing placed above the ceiling 2^63")


GATES = [gate_m1, gate_m2, gate_m3]


def write_results(path=None):
    """model_results.json: the predictions as they stood BEFORE any sweep of
    this project, each from its entry's origin (the last published term, or
    the bound the entry states above it)."""
    import residue_reference as ref
    c, se, fam = fit()
    out = {"model": "Poisson first occurrence at rate LATE per unit of "
                    "exposure (li(hi) - li(lo)) / ((power - 1) power^n)",
           "late": LATE, "late_fit": round(c, 4), "late_se": round(se, 4),
           "censored_exposure": {k: round(v, 4) for k, v in
                                 censored_exposure().items()},
           "terms_fitted": sum(len(r) for r in fam.values()),
           "rate_p_per_s": RATE, "ceiling": P_CEIL, "families": {}}
    for seq, f in ref.FAMILIES.items():
        d, known = f["power"], f["known"]
        start = origin(seq)
        pr = predictions(d, len(known), start, n_ahead=7)
        rows = {}
        for n, row in pr.items():
            rows[str(n)] = {k: float(f"{v:.4g}") for k, v in row.items()}
            if "median" in row:
                rows[str(n)]["median_clock_h"] = round(
                    clock_seconds(d, 0, row["median"]) / 3600, 2)
        out["families"][seq] = {
            "power": d, "frontier": len(known), "cursor": start,
            "last_published_term": known[-1],
            "exposures_of_known": [round(v, 3) for v in fam[seq]],
            "predictions": rows}
    path = path or str(HERE / "model_results.json")
    with open(path, "w", newline="\n") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE.parent))
    sys.path.insert(0, str(HERE))
    ok = True
    for g in GATES:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg, flush=True)
        ok = ok and good
    if "--write" in sys.argv and ok:
        res = write_results()
        for seq, f in res["families"].items():
            print(seq, {n: (r.get("median"), r.get("median_clock_h"))
                        for n, r in f["predictions"].items()})
    sys.exit(0 if ok else 1)
