"""The odds model, and the gates that decide whether it may be used.

    E[terms of (m,e) in (A, B)] = c(m,e) * ln(B/A)         on the INDEX line

because P(k | e + S(m,k)) ~ 1/k under the equidistribution heuristic, and
summing 1/k over the k the obstruction leaves is a logarithm.

c IS DERIVED, NOT FITTED.  For e = 0 the oracle's G3 shows S(m,k) == k-1
(mod q) for every prime q with (q-1) | m, so no k divisible by such a q can
be a term; the survivors are the k coprime to Q(m), whose reciprocals sum
to (phi(Q)/Q) * ln x.  Hence

    c(m, 0) = prod_{q : (q-1) | m} (1 - 1/q)

which is 1/2 at every odd m, 0.267 at m = 4, 0.211 at m = 12.  Nothing is
tuned; the only freedom the model has is whether that derivation is right,
which is what G11 tests against 124 published terms nobody here found.

e = 1 INVERTS THE SAME FACT: 1 + S(m,k) == k (mod q), so a k divisible by q
gets that congruence free instead of being barred, and the sum picks up a
factor q on those k.  For Q = 2 (odd m) that is c = 3/2, measured 1.28 in
[1e5, 1.2e6] and 1.55 below 2e5.  For even m the boost compounds over
3-5 primes and c runs 8-30: those families have thousands of terms, are
NOT a discovery class, and the project carries one of them only as a
census/health stream (psum_reference.CENSUS_FAMILY).

WHAT THE MODEL IS ALLOWED TO DO.  Place rungs, and state the odds in
[STATUS].  It is not evidence of anything (OPTIMIZATION.md: the cost model
has mispredicted by 4x in both directions in this repository), and no
find is ever judged by it -- only scored against it afterwards.

Gates in this file: G11 (pooled observed/predicted over the frozen tables,
with the interval that has to contain 1), G12 (the quantile scatter
CONVENTIONS.md demands -- a model whose knowns all sit at ~0 or ~1 is
wrong and may not plan a run), and G13 (c matches the obstruction the
oracle proved, and the parity fingerprint it predicts is in the data).
"""

import json
import math
import os

import psum_reference as ref

VALID_FROM = 1e6          # asymptotic regime: below this 1/k is not small
QUANTILES = ("Q1", "median", "Q3", "P90")
_Q = {"Q1": 0.25, "median": 0.50, "Q3": 0.75, "P90": 0.90}


def c_of(m, e=0):
    """The density constant of family (m, e) on the index line."""
    if e == 0:
        return ref.c_of(m, 0)
    if m % 2 == 1:
        return 1.5                      # derived; measured 1.28-1.55
    boost = 1.0
    for q in ref.obstruction_primes(m):
        boost *= (2.0 - 1.0 / q)        # the compounded free congruence
    return boost


def expected(m, e, a, b):
    """E[new terms] for a sweep of the index line from a to b."""
    if b <= a:
        return 0.0
    return c_of(m, e) * math.log(b / a)


def p_by(m, e, frontier, k):
    """P(the next term of (m,e) has appeared by index k)."""
    if k <= frontier:
        return 0.0
    return 1.0 - math.exp(-expected(m, e, frontier, k))


def quantile(m, e, frontier, q):
    """The index by which the next term appears with probability q."""
    c = c_of(m, e)
    return frontier * math.exp(-math.log(max(1e-12, 1.0 - q)) / c)


def k_to_p(k):
    """Index line -> prime line: p_k ~ k(ln k + ln ln k - 1)."""
    k = max(float(k), 3.0)
    return k * (math.log(k) + math.log(math.log(k)) - 1.0)


def p_to_k(p):
    """Prime line -> index line: pi(p) ~ p / (ln p - 1)."""
    p = max(float(p), 3.0)
    return p / max(math.log(p) - 1.0, 1.0)


def predictions(family, frontier=None, n_next=None):
    """{n_next: {"Q1": depth, ...}} in PRIME-LINE depths, for the ladder.

    The campaign's cursor is the prime line, so the ladder must be in that
    unit; the model lives on the index line, so every rung is converted
    here and nowhere else.
    """
    m, e = family
    f = ref.FAMILIES[family]
    frontier = f["frontier"] if frontier is None else frontier
    n_next = (len(f["terms"]) + 1) if n_next is None else n_next
    return {int(n_next): {q: k_to_p(quantile(m, e, frontier, _Q[q]))
                          for q in QUANTILES}}


def campaign_board(frontiers=None):
    """One row per family: what it costs to reach each quantile."""
    rows = []
    for fam in ref.TARGETS:
        m, e = fam
        f = ref.FAMILIES[fam]
        front = (frontiers or {}).get(fam, f["frontier"])
        n = len(f["terms"]) + 1
        rows.append(dict(family=fam, idx=f["idx"], val=f["val"], next_term=n,
                         c=c_of(m, e), frontier=front,
                         quantiles={q: quantile(m, e, front, _Q[q])
                                    for q in QUANTILES}))
    return rows


def write_model_results(path=None):
    """model_results.json -- the predictions, stated BEFORE the run."""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "model_results.json")
    board = campaign_board()
    out = {"model": "E = c*ln(B/A) on the index line; c = phi(Q)/Q derived "
                    "from the Fermat obstruction (oracle G3)",
           "validated": g11_pooled_validation()[1],
           "families": {}}
    for r in board:
        out["families"][r["idx"]] = {
            "m": r["family"][0], "e": r["family"][1], "c": round(r["c"], 4),
            "next_term": r["next_term"], "frontier_index": r["frontier"],
            "quantiles_index": {q: r["quantiles"][q] for q in QUANTILES},
            "quantiles_prime_line": {q: k_to_p(r["quantiles"][q])
                                     for q in QUANTILES}}
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    return path


# --------------------------------- gates -----------------------------------

def _exposure_rows():
    """(family, observed, predicted) over the frozen tables, k >= VALID_FROM.

    Exposure runs to the SEARCHED limit (the frontier), never to the last
    known term: ending a window at a hit conditions on a hit and inflates
    the observed rate.  One row per family -- the same condition is never
    counted twice, since the index and prime tables of a family are one
    object (oracle G1b).
    """
    rows = []
    for fam in ref.TARGETS:
        m, e = fam
        f = ref.FAMILIES[fam]
        big = [k for k in f["terms"] if k >= VALID_FROM]
        if len(big) < 3:
            continue
        top = max(f["frontier"], big[-1])
        rows.append((fam, len(big) - 1, c_of(m, e) * math.log(top / big[0])))
    return rows


def g11_pooled_validation():
    """The derived c, against 124 published terms this project did not find.

    Pooled observed/predicted with a Poisson interval; the model is USABLE
    only if that interval contains 1.
    """
    rows = _exposure_rows()
    obs = sum(o for _, o, _ in rows)
    pred = sum(p for _, _, p in rows)
    if len(rows) < 5 or obs < 30:
        return False, (f"G11 FAIL: only {len(rows)} families / {obs} terms "
                       f"in the asymptotic regime -- too weak to validate")
    ratio = obs / pred
    lo = (obs - 1.96 * math.sqrt(obs)) / pred
    hi = (obs + 1.96 * math.sqrt(obs)) / pred
    if not lo <= 1.0 <= hi:
        return False, (f"G11 FAIL: observed/predicted = {ratio:.2f}, 95% "
                       f"[{lo:.2f}, {hi:.2f}] excludes 1 -- the model may "
                       f"not be used to plan a run")
    return True, (f"G11 ok: observed/predicted = {ratio:.2f} over {len(rows)} "
                  f"families and {obs} published terms (95% [{lo:.2f}, "
                  f"{hi:.2f}] contains 1)")


def g12_quantile_scatter():
    """CONVENTIONS.md: the knowns' model quantiles must SCATTER.  A model
    whose every known sits at ~0 or ~1 is wrong however good its mean is."""
    qs = []
    for fam in ref.TARGETS:
        m, e = fam
        terms = [k for k in ref.FAMILIES[fam]["terms"] if k >= VALID_FROM]
        for prev, k in zip(terms, terms[1:]):
            qs.append(p_by(m, e, prev, k))
    if len(qs) < 20:
        return False, f"G12 FAIL: only {len(qs)} quantiles -- too few"
    mean = sum(qs) / len(qs)
    low = sum(1 for q in qs if q < 0.25) / len(qs)
    high = sum(1 for q in qs if q > 0.75) / len(qs)
    if not 0.35 <= mean <= 0.65:
        return False, (f"G12 FAIL: mean quantile {mean:.2f} -- the model is "
                       f"biased {'late' if mean < 0.5 else 'early'}")
    if low < 0.12 or high < 0.12:
        return False, (f"G12 FAIL: quantiles do not scatter ({low:.0%} below "
                       f"0.25, {high:.0%} above 0.75)")
    return True, (f"G12 ok: {len(qs)} known-term quantiles scatter -- mean "
                  f"{mean:.2f}, {low:.0%} below 0.25, {high:.0%} above 0.75")


def g13_c_matches_obstruction():
    """c is the obstruction, not a fit: phi(Q)/Q recomputed from Q(m), and
    the parity fingerprint it predicts (every e = 0 term odd) is present in
    every frozen table."""
    for fam in ref.TARGETS:
        m, e = fam
        q = ref.Q(m)
        phi = 1
        for r in ref.obstruction_primes(m):
            phi *= (r - 1)
        want = phi / q
        if abs(c_of(m, e) - want) > 1e-12:
            return False, (f"G13 FAIL: m={m} c={c_of(m, e)} != phi(Q)/Q="
                           f"{want}")
        evens = [k for k in ref.FAMILIES[fam]["terms"] if k % 2 == 0]
        if evens:
            return False, (f"G13 FAIL: {ref.FAMILIES[fam]['idx']} has even "
                           f"terms {evens[:3]} -- the obstruction says a "
                           f"e=0 term is always odd")
    return True, ("G13 ok: c == phi(Q)/Q for every family, and all 124 "
                  "frozen e=0 terms are odd as the obstruction predicts")


GATES = [g11_pooled_validation, g12_quantile_scatter, g13_c_matches_obstruction]

if __name__ == "__main__":
    import pathlib as _pl
    import sys as _s
    _s.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown

    def _main():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
        print()
        print("%-9s %-9s %-3s %-6s %-11s %s"
              % ("SEQ", "partner", "m", "c", "frontier k", "next term at "
                 "index (Q1 / median / Q3 / P90)"))
        for r in campaign_board():
            q = r["quantiles"]
            print("%-9s %-9s %-3d %-6.3f %-11.3g a(%d): %.3g / %.3g / %.3g "
                  "/ %.3g" % (r["idx"], r["val"], r["family"][0], r["c"],
                              r["frontier"], r["next_term"], q["Q1"],
                              q["median"], q["Q3"], q["P90"]))
        print("\nwrote " + os.path.basename(write_model_results()))

    _s.exit(_shutdown.graceful(_main) or 0)
