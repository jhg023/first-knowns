# hlc_model.py -- the odds model for A331940 (where the next records of the
# Hardy-Littlewood constant C of x^2 + x + k should fall).
#
# THE MODEL.  For odd k the residue of 1 - 4k modulo an odd prime p is
# uniform, so the Legendre symbol s_p = (1-4k | p) is +1 or -1 with
# probability (p-1)/(2p) each and 0 with probability 1/p, independently
# over p (exactly so over a full period of any finite set of primes).
# The model takes C(k) = 2 * prod_{p odd} (1 - s_p/(p-1)) with the s_p
# independent -- the random Euler product whose extreme values Granville
# and Soundararajan (GAFA 13, 2003) proved describe L(1, chi), which C
# follows through C = (4/3) E / L(1, chi), E within 1% of pi^2/8 for every
# k near a record.  Its law is computed, not simulated: the exact
# convolution of the three-point laws of log(1 - s_p/(p-1)) on a grid for
# p <= P_CONV, and a Gaussian for the rest (variance sum 1/p^2).
#
#   tail(T) = P(C > T) for a random odd k.
#
# RECORDS.  Given the standing record R and everything below the cursor
# swept, the next record is the first odd k with C > R: its distance past
# the cursor is geometric with rate tail(R)/2 per unit of k, and its value
# R' has tail(R')/tail(R) uniform.  The literature supplies ANCHORS -- k
# with C known exactly (Fung & Williams 1990) -- which cap the walk: on
# reaching an anchor whose C exceeds the record, the anchor IS the record.
# predictions() runs that walk (seeded Monte Carlo) and reads off quantiles
# of the next open terms.
#
# VALIDATION (gate M1): the tail against the exhaustive counts over odd
# k <= 3*10^6, and the model quantile of each known record given its
# predecessor -- these must scatter, not pile up at 0 or 1.
#
# EXPENSIVE: predictions() is a Monte Carlo of ~2*10^4 walks.  The launcher
# calls it once per find through huntlib.rungs.LiveLadder, never from the
# segment loop.

import json
import math
import os

import numpy as np

P_CONV = 20000
GRID = 2.0e-4
LO, HI = -5.0, 3.5

# (k, C): Fung & Williams' discriminants above 3*10^6 with C recomputed by
# this project (hlc_search gate S4 reproduces their 7 decimals).
ANCHORS = [
    (15102077, 8.1021841), (42895751, 8.1630137), (67374467, 8.2184315),
    (99539591, 8.3158226), (160834691, 8.5432039), (352031501, 8.5543495),
    (398878547, 8.7233587), (1016793977, 8.8649576),
    (17959429571, 9.2194286), (21425625701, 9.4146088),
    (4125444938831, 9.5049625), (7514981191031, 9.6758115),
    (9305398948667, 9.7268218),
]
# exhaustive counts of C > t over odd k <= 3*10^6 (1.5*10^6 values),
# from the tabulation of that range (known territory: a(12) > 3*10^6)
EMPIRICAL_N = 1500000
EMPIRICAL = [(6.0, 2912), (6.5, 810), (7.0, 153), (7.25, 63), (7.5, 28),
             (7.75, 7), (8.0, 4)]
KNOWN = [(41, 6.63955), (21377, 6.92868), (27941, 7.26400),
         (41537, 7.32220), (55661, 7.45791), (115721, 7.70935),
         (239621, 7.72932), (247757, 8.24741)]

_TAIL = None


def _primes(n):
    s = np.ones(n + 1, dtype=bool)
    s[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = False
    return np.nonzero(s)[0]


def _shift_add(dst, src, shift, weight):
    """dst += weight * src shifted by `shift` (grid units, real), linear
    interpolation between the two neighbouring cells (mean-preserving)."""
    j = math.floor(shift)
    fr = shift - j
    n = len(src)
    for jj, w in ((j, (1 - fr) * weight), (j + 1, fr * weight)):
        if w == 0.0:
            continue
        if jj >= 0:
            dst[jj:] += w * src[:n - jj] if jj else w * src
        else:
            dst[:n + jj] += w * src[-jj:]


def tail_table():
    """(c, tail): tail[i] = P(C > c[i]) on the grid c = 2*exp(LO + GRID*i)."""
    global _TAIL
    if _TAIL is not None:
        return _TAIL
    n = int(round((HI - LO) / GRID)) + 1
    dist = np.zeros(n)
    dist[int(round(-LO / GRID))] = 1.0
    var_tail = 0.0
    for p in _primes(2 * 10**6)[1:]:
        p = int(p)
        if p > P_CONV:
            var_tail += (p - 1) / p / float(p - 1) ** 2
            continue
        new = np.zeros(n)
        _shift_add(new, dist, 0.0, 1.0 / p)
        _shift_add(new, dist, math.log(1 - 1.0 / (p - 1)) / GRID,
                   (p - 1) / (2.0 * p))
        _shift_add(new, dist, math.log(1 + 1.0 / (p - 1)) / GRID,
                   (p - 1) / (2.0 * p))
        dist = new
    sd = math.sqrt(var_tail + 1.0 / (2e6 * math.log(2e6))) / GRID
    hw = int(6 * sd) + 1
    ker = np.exp(-0.5 * (np.arange(-hw, hw + 1) / sd) ** 2)
    dist = np.convolve(dist, ker / ker.sum(), mode="same")
    tail = np.cumsum(dist[::-1])[::-1] - dist          # strictly above
    c = 2.0 * np.exp(LO + GRID * np.arange(n))
    _TAIL = (c, np.maximum(tail, 1e-300))
    return _TAIL


def tail(T):
    """P(C > T) for a random odd k."""
    c, t = tail_table()
    return float(np.exp(np.interp(math.log(T), np.log(c), np.log(t))))


def tail_inv(q):
    """The T with tail(T) = q."""
    c, t = tail_table()
    lt = np.log(t)[::-1]
    return float(np.exp(np.interp(math.log(q), lt, np.log(c)[::-1])))


def walks(record_c, cursor, n_ahead, ceiling, paths=20000, seed=331940):
    """Positions of the next n_ahead records, one row per walk (np.inf
    where a walk passes the ceiling first)."""
    rng = np.random.default_rng(seed)
    c, t = tail_table()
    lc, lt = np.log(c), np.log(t)
    out = np.full((paths, n_ahead), np.inf)
    r = np.full(paths, float(record_c))
    pos = np.full(paths, float(cursor))
    for j in range(n_ahead):
        ltr = np.interp(np.log(np.maximum(r, 1.0)), lc, lt)   # log tail(r)
        cand = pos + 2.0 * rng.exponential(size=paths) / np.exp(ltr)
        nk = np.full(paths, np.inf)                      # the next anchor
        nc = np.zeros(paths)                             # that beats r
        for ka, ca in reversed(ANCHORS):
            use = (ka > pos) & (ca > r)
            nk = np.where(use, float(ka), nk)
            nc = np.where(use, ca, nc)
        hit = np.isfinite(nk) & (cand >= nk)
        newr = np.exp(np.interp(ltr + np.log(rng.random(size=paths)),
                                lt[::-1], lc[::-1]))
        pos = np.where(hit, nk, cand)
        r = np.where(hit, nc, newr)
        out[:, j] = np.where(pos < ceiling, pos, np.inf)
        pos = np.where(pos < ceiling, pos, np.inf)
    return out


def predictions(frontier, record_c, cursor, n_ahead=4, ceiling=1e13,
                paths=20000):
    """{term: {"Q1","median","Q3","P90"}} for the next n_ahead open terms,
    a(frontier + 1) onward, given the standing record and the swept
    cursor.  A quantile past the ceiling is absent."""
    w = walks(record_c, cursor, n_ahead, ceiling, paths)
    preds = {}
    for j in range(n_ahead):
        col = np.sort(w[:, j])
        qs = {}
        for name, q in (("Q1", 0.25), ("median", 0.5), ("Q3", 0.75),
                        ("P90", 0.9)):
            v = col[int(q * (len(col) - 1))]
            if np.isfinite(v) and v < ceiling:
                qs[name] = float(v)
        preds[int(frontier) + 1 + j] = qs
    return preds


def prob_by(record_c, cursor, k):
    """P(the next record falls at or below k), anchors included."""
    for ka, ca in ANCHORS:
        if cursor < ka <= k and ca > record_c:
            return 1.0
    return 1.0 - math.exp(-(k - cursor) / 2.0 * tail(record_c))


# Engine v3 on one RTX 4090, measured 2026-11-11 (BENCHMARKS.md): seconds
# per window of 2^23 k at each height.  Between the points the cost is
# taken as a power of k (the prefilter grows like k^(1/4), the sparse count
# of the n it leaves like k^(1/2)), and the end exponents extend it.
# (Engine v2's law, whose flagged tabulation grew like k^(1/2) to k:
# 0.127 / 0.216 / 0.383 / 0.809 / 1.300 / 2.530 / 5.380 / 13.587.)
# Past engine v3's ceiling, engine v4 measured 2026-11-12 (OPTIMIZATION_LOG
# round 3): its windows equal v3's below 10^13 (1.185 s at 9.9*10^12), and
# above it the prefilter's giant-step table is full (128 steps) so its
# cost goes like sqrt(k), and the wide form keys (from k ~ 5.3*10^13) cost
# 0.76x: 2.147 / 4.660 / 8.093 / 14.758 s, exponent 0.50 at the top.
# Engine v4.1 (OPTIMIZATION_LOG round 4, 2026-11-12): each point is v4's
# divided by the paired v4 / v4.1 ratio measured at that height in one
# sitting (1.15-1.17 to 10^10, 1.27 to 10^12, 1.35 at 3*10^12, 1.44-1.46
# at 10^13-3*10^13, 1.32 / 1.29 / 1.23 at 10^14 / 3*10^14 / 10^15), so the
# law keeps v4's calibration; v4's own windows that sitting were within 2%
# of its points below 3*10^14.  (v4: 0.062 / 0.090 / 0.139 / 0.239 / 0.317
# / 0.478 / 0.726 / 1.192 / 2.147 / 4.660 / 8.093 / 14.758.)
RATE_POINTS = [(1e8, 0.054), (1e9, 0.077), (1e10, 0.120), (1e11, 0.189),
               (3e11, 0.249), (1e12, 0.376), (3e12, 0.539), (9.9e12, 0.830),
               (3e13, 1.475), (1e14, 3.533), (3e14, 6.260), (1e15, 12.036)]
_WINDOW_K = float(1 << 23)


def _segments():
    pts = RATE_POINTS
    segs = []
    for (k1, t1), (k2, t2) in zip(pts, pts[1:]):
        segs.append((k1, k2, t1, math.log(t2 / t1) / math.log(k2 / k1)))
    k1, _k2, t1, a = segs[0]
    segs[0] = (0.0, segs[0][1], t1, a)            # extend below the table
    k1, _k2, t1, a = segs[-1]
    segs[-1] = (k1, float("inf"), t1, a)          # and above it
    return [(lo, hi, RATE_POINTS[i][0], t1, a)
            for i, (lo, hi, t1, a) in enumerate(segs)]


def rate_at(k):
    """k per second at height k (the measured law)."""
    k = max(float(k), 1.0)
    for lo, hi, kref, t1, a in _segments():
        if k < hi:
            return _WINDOW_K / (t1 * (k / kref) ** a)
    return 0.0


def clock_seconds(k, k0=0.0):
    """Seconds to sweep from k0 to k at the measured rate law."""
    k, k0 = float(k), max(float(k0), 0.0)
    total = 0.0
    for lo, hi, kref, t1, a in _segments():
        x0, x1 = max(lo, k0), min(hi, k)
        if x1 > x0:
            total += t1 * kref * ((x1 / kref) ** (a + 1.0)
                                  - (x0 / kref) ** (a + 1.0)) / (a + 1.0)
    return total / _WINDOW_K


def validate():
    """(ok, text): tail against the exhaustive counts, and the scatter of
    the known records' model quantiles."""
    rows, ok = [], True
    for t, n in EMPIRICAL:
        m = EMPIRICAL_N * tail(t)
        rows.append(f"C>{t}: {n} seen, {m:.1f} modelled")
        # Poisson-compatible to ~3 sigma, with a 25% model allowance
        if abs(n - m) > 3.0 * math.sqrt(max(m, 1.0)) + 0.25 * m:
            ok = False
    us = []
    for (k0, c0), (k1, _c1) in zip(KNOWN, KNOWN[1:]):
        us.append(1.0 - math.exp(-(k1 - k0) / 2.0 * tail(c0)))
    piled = sum(1 for u in us if u < 0.02 or u > 0.98)
    if piled > 2:
        ok = False
    return ok, rows, us


def write_results(path, frontier=11, record_c=8.24741, cursor=3 * 10**6,
                  ceiling=1e13):
    ok, rows, us = validate()
    preds = predictions(frontier, record_c, cursor, n_ahead=14,
                        ceiling=ceiling, paths=200000)
    w = walks(record_c, cursor, 48, ceiling, paths=100000)
    by = {}
    for K in (1e8, 1e9, 1e10, 1e11, 1e12, 1e13):
        cnt = (w < K).sum(axis=1)
        by[f"{K:.0e}"] = {"mean_new_terms": float(cnt.mean()),
                          "p10": int(np.percentile(cnt, 10)),
                          "p90": int(np.percentile(cnt, 90)),
                          "clock_s": clock_seconds(K)}
    res = {
        "sequence": "A331940",
        "model": "random Euler product; record walk with literature anchors",
        "stated": "before any campaign",
        "conditioned_on": {"frontier": frontier, "record_C": record_c,
                           "swept_to_k": cursor},
        "tail": {f"{t:.2f}": tail(t) for t in
                 (7.5, 7.75, 8.0, 8.24741, 8.5, 8.75, 9.0, 9.25, 9.5, 9.75,
                  10.0, 10.5, 10.73416)},
        "validation": {"ok": ok, "counts": rows,
                       "record_quantiles": [round(u, 4) for u in us]},
        "predictions": {str(t): q for t, q in preds.items()},
        "new_terms_by_k": by,
        "P_a12_is_the_anchor_99539591": math.exp(
            -(99539591 - cursor) / 2.0 * tail(record_c)),
    }
    with open(path, "w", newline="\n") as f:
        json.dump(res, f, indent=1)
    return res


def gate_m1():
    ok, rows, us = validate()
    t = tail(8.24741)
    mono = tail(9.0) < tail(8.5) < t < tail(7.5)
    inv = abs(tail_inv(tail(8.6)) - 8.6) < 1e-3
    if not (ok and mono and inv):
        return False, f"M1 model validation failed: {rows}; quantiles {us}"
    return True, ("M1 model: tail matches the exhaustive counts over odd "
                  f"k <= 3*10^6 ({'; '.join(rows[2:6])}); the seven known "
                  f"records sit at model quantiles "
                  f"{', '.join(f'{u:.2f}' for u in us)}; "
                  f"P(C > 8.24741) = {t:.3g} per odd k")


GATES = [gate_m1]

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    r = write_results(os.path.join(here, "model_results.json"))
    print(json.dumps(r, indent=1))
