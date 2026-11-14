# hlc_search.py -- THE CPU ENGINE and the host mathematics for A331940.
#
# A331940: addends k > 0 such that x^2 + x + k produces a record of its
# Hardy-Littlewood constant C (hlc_reference.py states C and the two
# classical facts everything rests on).
#
# What this module is, in the five-file skeleton:
#
#   * the CPU engine: an INDEPENDENT tabulation of the class numbers of
#     every discriminant 1 - 4k in a window, by a sieve over reduced forms
#     (plain integer division and %).  The GPU engine tabulates the same
#     numbers by Gauss's three-squares theorem and never calls this; the
#     parity gate pins the two bit-for-bit, so it checks one theorem
#     against another, not one arithmetic against another;
#   * the host verification: exact C intervals from a tabulated count,
#     the discovery-once taxonomy, and the three confirmations a find
#     must survive (a rigorous interval; an analytic evaluation to 30+
#     digits that never sees a class number; a direct enumeration of
#     reduced forms).
#
# THE TABULATED QUANTITY.  For n = 4k - 1 == 3 (mod 8) (k odd; k = 2m + 1,
# n = 8m + 3) both engines produce
#
#     T(n) = 3*H(n),   H the Hurwitz class number: every reduced form
#     (a, b, c) of discriminant -n, primitive or not, counted once, and
#     the forms a*(x^2 + xy + y^2) counted 1/3.
#
# Here: a reduced form of an odd discriminant == 5 (mod 8) has a, b, c all
# odd, and (a, +-b, c) with 0 < b <= a <= c are both reduced unless b = a
# or a = c, so T(n) = sum over odd 0 < b <= a <= c with 4ac - b^2 = n of
# 6 (b < a < c), 3 (b = a < c or b < a = c), 1 (a = b = c).  For fixed
# (a, b) the admissible n form an arithmetic progression of difference 8a
# -- a sieve.  The GPU side counts odd x >= y >= z >= 1 with
# x^2 + y^2 + z^2 = n, weights 6 / 3 / 1 by the number of equal squares
# (Gauss: r_3(n) = 24*H(n) for n == 3 mod 8, and all three squares are
# odd, so the count of positive odd ordered triples is 3*H(n)).
#
# FROM T TO h(1 - 4k).  Write n = d*f^2 with d squarefree (D0 = -d is the
# fundamental discriminant, f the conductor) and chi = (D0|.).  Then
#     H(n) = h'(D0) * prod_{p^e || f} (1 + (p - chi(p))(p^e - 1)/(p - 1)),
#     h(-n) = h(D0) * prod_{p^e || f} p^(e-1) (p - chi(p)) / u,
# h'(D0) = h(D0) (1/3 for D0 = -3), u = 3 for D0 = -3 and f > 1, else 1.
# So h(-n) is an exact function of T(n) and the factorization of f, the
# division must come out exact (an integrity check on every survivor), and
#     h(-n) >= H(n) * prod_{p | f} (1 - 1/p)            (equality iff all
# chi(p) = 1): the lower bound the survivor rule uses.
#
# THE SURVIVOR RULE (the rigorous prune).  E(k) <= (pi^2/8) Q(n) (every
# factor is at most 1/(1 - p^-2), and the factors at the primes <= 251 are
# known exactly -- Q below, the Codex review's HLC-001), so for n > 3
#     C(k) > F  =>  h(-n) < 4*sqrt(n)*E/(3*pi*F) <= pi*sqrt(n)*Q(n)/(6F)
#               =>  T(n) * rho(n) * 2F < pi*sqrt(n)*Q(n),
# rho(n) any lower bound of prod_{p | f} (1 - 1/p).  A k that fails the
# last inequality has C(k) <= F unconditionally: its class number was
# COUNTED and is too large.  Both engines evaluate the same IEEE-double
# expression (see survivor_mask), padded so that rounding can only add
# survivors.  (Engines v1-v3 used Q = 1: the same census and records, a
# larger raw stream.)
#
# Nothing here is called by the oracle, and nothing here calls the GPU.

import math
import sys
import time

import numpy as np

SEQUENCE = "A331940"
FORMS = "x^2 + x + k"

# ---- the campaign's fixed thresholds (documented in README.md)
CENSUS_FLOOR = 7.5          # census counts C >= this, in bins of BIN_W
BIN_W = 0.25
NEAR_MARGIN = 0.01          # [NEAR]: C within 1% below the standing record
N_CEIL = 1 << 62            # 4k - 1 below this (K_CEIL = 10^18 is 4.0e18)
K_CEIL = 10**18             # the campaign's last rung (engine v4; v3: 10^13)
N_OLD = 1 << 46             # engine v3's ceiling: the rule is v3's below it

# ---- the survivor rule's constants (each engine keeps its own copy; a
#      gate compares them)
SMALLP = [p for p in range(3, 252, 2)
          if all(p % q for q in range(3, int(p ** 0.5) + 1, 2))]


def _rho_large(n_ceil, pmax):
    """Lower bound of prod (1 - 1/p) over primes p > pmax with p^2 | n,
    n < n_ceil: the product over the smallest such primes whose squares
    still multiply to less than n_ceil."""
    rho, prod, p = 1.0, 1, pmax + 2
    while True:
        while any(p % q == 0 for q in range(3, int(p ** 0.5) + 1, 2)):
            p += 2
        if prod * p * p >= n_ceil:
            return rho
        prod *= p * p
        rho *= 1.0 - 1.0 / p
        p += 2


def rho_large(nmax):
    """The rule's RHO_LARGE for a window whose largest n is nmax: the bound
    of _rho_large over every n <= max(nmax, 2^46).  Engine v3 used the
    2^46 value for every window; the floor keeps every window below 2^46
    on that IDENTICAL rule (the stream, the fingerprints and the cursor
    are v3's there), and above it the bound covers the window it is used
    for -- three primes past 251 fit in n < 2^62 where two fit below
    2^48.  Both engines pass this value per launch (gate P0)."""
    return _rho_large(max(int(nmax) + 1, N_OLD), SMALLP[-1]) \
        * (1.0 - 2.0 ** -40)


RHO_LARGE = rho_large(0)    # every window below 2^46 (engine v3's constant)
RHO_MIN = 0.33              # <= rho(n) for every n below 1.2e16 (gate S0)
PI_UP = math.pi * (1.0 + 2.0 ** -40)
INV = [1.0 - 1.0 / p for p in SMALLP]
# The local Euler factors (the Codex review's HLC-001).  E(k) is a product
# over odd p !| n of e_p <= 1/(1 - p^-2), and prod_p 1/(1 - p^-2) = pi^2/8,
# so dividing each known factor by its maximum gives
#     E(k) <= (pi^2/8) * Q(n),   Q(n) = prod_{p in SMALLP} q_p(n),
#     q_p = 1 (inert), 1 - 1/p^2 (p | n), 1 - 2/(p(p - 1)) (split)
# -- the split ratio is (1 - 1/(p-1)^2)(1 - 1/p^2).  Every omitted ratio is
# at most 1, so this is a proved bound with no truncation and no GRH, and
# C(k) > F  =>  h(-n) < pi*sqrt(n)*Q(n)/(6F).  Q is multiplied in ascending
# p in IEEE doubles and padded by Q_PAD (53 roundings of 2^-53 each are far
# inside 2^-40), the same expression in both engines (gate P0).
Q_RAM = [1.0 - 1.0 / (p * p) for p in SMALLP]
Q_SPL = [1.0 - 2.0 / (p * (p - 1)) for p in SMALLP]
Q_PAD = 1.0 + 2.0 ** -40
_QR = [np.zeros(p, dtype=bool) for p in SMALLP]
for _p, _t in zip(SMALLP, _QR):
    _t[[(b * b) % _p for b in range(1, _p)]] = True


def local_q(n):
    """Q(n) * Q_PAD as the engines evaluate it (Python floats)."""
    n = int(n)
    q = 1.0
    for p, qr, qs in zip(SMALLP, Q_RAM, Q_SPL):
        r = (-n) % p
        if r == 0:
            q = q * qr
        elif pow(r, (p - 1) // 2, p) == 1:
            q = q * qs
    return q * Q_PAD


def local_q_array(n):
    """The same for an int64 array of n."""
    q = np.ones(len(n), dtype=np.float64)
    for p, qr, qs, tab in zip(SMALLP, Q_RAM, Q_SPL, _QR):
        r = (-n) % p
        q = np.where(r == 0, q * np.float64(qr),
                     np.where(tab[r], q * np.float64(qs), q))
    return q * np.float64(Q_PAD)


def rho_min_true(n_ceil=N_CEIL):
    """The true minimum of prod_{p^2 | n} (1 - 1/p) over n < n_ceil."""
    rho, prod = 1.0, 1
    for p in SMALLP:
        if prod * p * p >= n_ceil:
            break
        prod *= p * p
        rho *= 1.0 - 1.0 / p
    return rho * rho_large(n_ceil - 1)


def rho_min(nmax):
    """The rule's RHO_MIN for a window whose largest n is nmax: 0.33 (engine
    v3's constant) while that is <= the true minimum of rho below the
    window's top -- every n < 1.24e16, where at most seven primes of
    SMALLP can have their squares divide n -- and the true minimum rounded
    down to 0.01 above (0.32 to 2^62, where eight can).  Both engines pass
    this value per launch (gate S0, gate P0)."""
    v = rho_min_true(max(int(nmax) + 1, N_OLD))
    return RHO_MIN if v >= RHO_MIN else math.floor(v * 100.0) / 100.0


# ============================================================ CPU engine
def h3_window(m0, W):
    """T(8m + 3) for m in [m0, m0 + W), by the reduced-forms sieve."""
    m0, W = int(m0), int(W)
    n0 = 8 * m0 + 3
    nmax = 8 * (m0 + W - 1) + 3
    cnt = np.zeros(W, dtype=np.int64)
    amax = math.isqrt(nmax // 3)
    SPLIT = 96
    idx_parts, w_parts = [], []
    for a in range(1, amax + 1, 2):
        a4 = 4 * a
        if a < SPLIT:
            for b in range(1, a + 1, 2):
                bb = b * b
                clo = max(a, -((-(n0 + bb)) // a4))
                clo += 1 - (clo % 2)
                chi = (nmax + bb) // a4
                chi -= 1 - (chi % 2)
                if chi < clo:
                    continue
                i0 = (a4 * clo - bb - n0) // 8
                nc = (chi - clo) // 2 + 1
                wt = 3 if b == a else 6
                cnt[i0:i0 + a * nc:a] += wt
                if clo == a:                       # the a = c form
                    cnt[i0] += (1 if b == a else 3) - wt
            continue
        b = np.arange(1, a + 1, 2, dtype=np.int64)
        bb = b * b
        clo = np.maximum(a, -((-(n0 + bb)) // a4))
        clo += 1 - (clo % 2)
        chi = (nmax + bb) // a4
        chi -= 1 - (chi % 2)
        nc = (chi - clo) // 2 + 1
        i0 = (a4 * clo - bb - n0) // 8
        wt = np.where(b == a, 3, 6)
        j = 0
        while True:
            live = nc > j
            if not live.any():
                break
            w = wt[live]
            if j == 0:
                first = clo[live] == a
                w = np.where(first, np.where(b[live] == a, 1, 3), w)
            idx_parts.append(i0[live] + a * j)
            w_parts.append(w)
            j += 1
        if len(idx_parts) > 4096:
            cnt += np.bincount(np.concatenate(idx_parts),
                               weights=np.concatenate(w_parts),
                               minlength=W).astype(np.int64)
            idx_parts, w_parts = [], []
    if idx_parts:
        cnt += np.bincount(np.concatenate(idx_parts),
                           weights=np.concatenate(w_parts),
                           minlength=W).astype(np.int64)
    return cnt.astype(np.uint32)


def survivor_mask(m0, t3, floor, local=True):
    """The survivor rule on a tabulated window, as IEEE doubles in a fixed
    order (the GPU engine evaluates the identical expression):

        A = (double)T * (2*floor);
        R = (PI_UP * sqrt((double)n)) * (Q(n) * Q_PAD)
        survivor  <=>  A * rho_min(nmax) < R  and  A * rho(n) < R,
        rho(n) = rho_large(nmax) * prod_{p in SMALLP, p^2 | n} (1 - 1/p),
    each product taken in ascending p, nmax the window's largest n.
    floor = 0 keeps everything."""
    W = len(t3)
    n = 8 * (np.arange(W, dtype=np.int64) + int(m0)) + 3
    nmax = 8 * (int(m0) + W - 1) + 3
    A = t3.astype(np.float64) * np.float64(2.0 * floor)
    R = np.float64(PI_UP) * np.sqrt(n.astype(np.float64))
    if local:                           # local=False: engines v1-v3's rule
        R = R * local_q_array(n)
    loose = A * np.float64(rho_min(nmax)) < R
    rho = np.full(W, rho_large(nmax), dtype=np.float64)
    for p, inv in zip(SMALLP, INV):
        hit = (n % (p * p)) == 0
        rho[hit] = rho[hit] * np.float64(inv)
    return loose & (A * rho < R)


def survivors(m0, W, floor):
    """[(k, T)] for the survivors of [m0, m0 + W) at `floor`, ascending."""
    t3 = h3_window(m0, W)
    idx = np.nonzero(survivor_mask(m0, t3, floor))[0]
    return [(2 * (int(m0) + int(i)) + 1, int(t3[i])) for i in idx]


# ========================================================= host arithmetic
_PRIMES = None


def primes_upto(N):
    global _PRIMES
    if _PRIMES is None or _PRIMES[-1] < N:
        M = max(int(N), 1 << 16)
        s = np.ones(M + 1, dtype=bool)
        s[:2] = False
        for i in range(2, math.isqrt(M) + 1):
            if s[i]:
                s[i * i::i] = False
        _PRIMES = np.nonzero(s)[0]
    return _PRIMES[:int(np.searchsorted(_PRIMES, N, side="right"))]


def legendre(D, p):
    r = pow(D % p, (p - 1) // 2, p)
    return 0 if r == 0 else (1 if r == 1 else -1)


def square_part(n):
    """(d, {p: e}) with n = d * prod p^(2e), d squarefree: trial division
    by the primes p with p^3 <= n, then one perfect-square test."""
    n = int(n)
    c, f = n, {}
    for p in primes_upto(int(round(n ** (1.0 / 3.0))) + 2)[1:]:
        p = int(p)
        if p * p * p > c:
            break
        v = 0
        while c % p == 0:
            c //= p
            v += 1
        if v >= 2:
            f[p] = v // 2
    r = math.isqrt(c)
    if c > 1 and r * r == c:
        f[r] = f.get(r, 0) + 1
    d = n
    for p, e in f.items():
        d //= p ** (2 * e)
    return d, f


def h_from_t3(n, t3):
    """(d, f, h(-d), h(-n)) from T(n) = 3*H(n); raises if the division is
    not exact -- a tabulated count that is not a Hurwitz class number."""
    n, t3 = int(n), int(t3)
    d, f = square_part(n)
    S, psi = 1, 1
    for p, e in f.items():
        chi = legendre(-d, p)
        S *= 1 + (p - chi) * (p ** e - 1) // (p - 1)
        psi *= p ** (e - 1) * (p - chi)
    if d == 3:
        if t3 != S:
            raise ArithmeticError(f"T({n}) = {t3} is not 3H({n}) = {S}")
        hd, hD = 1, (1 if not f else psi // 3)
    else:
        if t3 % (3 * S):
            raise ArithmeticError(f"T({n}) = {t3} is not 3*{S}*h")
        hd = t3 // (3 * S)
        hD = hd * psi
    return d, f, hd, hD


# The truncated Euler product and its two error terms (rewritten 2026-11-11,
# OPTIMIZATION_LOG.md 2.13).  For every odd p >= 199, |log e_p| <=
# 1.0001/(p - 1)^2 <= 1.0001 (1 + 3/p)/p^2 (split: -log(1 - x) <= x/(1 - x)
# with x = 1/(p-1)^2 <= 2.6e-5; inert: -log(1 - 1/p^2) likewise; ramified:
# 0), so the factors past P change log E by at most
#     T(P) = 1.0001 (1 + 3/P) (P(2) - sum_{p <= P} 1/p^2),
# P(2) = sum over all primes of 1/p^2, the prime zeta value below (gate S10
# recomputes it by Moebius inversion of log zeta).  That is about
# 1/(P ln P), where the old bound 1/(3(P - 8)) counted every integer +-1 mod
# 6: 4.6x tighter at 2^20 and 6x at 2^26.  The product itself is taken as
# an exactly rounded sum of logarithms (math.fsum), so its rounding error
# is a few ulps of the sum of |log e_p| -- below 1e-15 -- however many
# primes it covers.  (The old product was multiplied out and carried a fixed
# 1e-11 for its rounding, which the 82,025 primes below 2^20 could exceed in
# the worst case: an allowance must grow with the operations it covers, or
# the operations must be arranged so that it need not.)
P2_PRIME_ZETA = 0.4522474200410654985065433648322479341732313432398924217
_U = 2.0 ** -53
_SMALL_TIER = 1 << 22         # primes_upto() caches up to here; past it the
_SEGMENT = 1 << 24            # primes come from a segmented sieve


def _powmod_vec(b, e, m):
    """b^e mod m elementwise (int64 arrays, m < 2^31: products < 2^62)."""
    r = np.ones_like(b)
    b = b % m
    e = e.copy()
    while True:
        r = np.where((e & 1) == 1, r * b % m, r)
        e >>= 1
        if not e.any():
            return r
        b = b * b % m


def _odd_prime_chunks(P):
    """The odd primes <= P as int64 arrays: one cached array up to
    _SMALL_TIER, a segmented sieve of _SEGMENT numbers at a time above."""
    if P <= _SMALL_TIER:
        yield primes_upto(P)[1:].astype(np.int64)
        return
    base = primes_upto(math.isqrt(P) + 1)[1:].tolist()
    lo = 3
    while lo <= P:
        hi = min(P, lo + _SEGMENT - 1)
        seg = np.ones(hi - lo + 1, dtype=bool)
        seg[lo % 2::2] = False                       # the even numbers
        for p in base:
            if p * p > hi:
                break
            st = max(p * p, -(-lo // p) * p)
            seg[st - lo::p] = False
        yield (np.nonzero(seg)[0] + lo).astype(np.int64)
        lo = hi + 1


_SUM_INV2 = {}


def _odd_sum_inv2(P):
    """sum_{3 <= p <= P} 1/p^2, exactly rounded (depends on P alone)."""
    if P not in _SUM_INV2:
        _SUM_INV2[P] = math.fsum(
            math.fsum((1.0 / (ps.astype(np.float64) ** 2)).tolist())
            for ps in _odd_prime_chunks(P))
    return _SUM_INV2[P]


def tail_bound(P):
    """|log prod_{p > P} e_p| <= tail_bound(P), P >= 199 (see above)."""
    if P < 199:
        raise ValueError("the tail bound is stated for P >= 199")
    rest = max(P2_PRIME_ZETA - 0.25 - _odd_sum_inv2(P), 0.0)
    return 1.0001 * (1.0 + 3.0 / P) * rest + 1e-15


def E_bounds(n, P):
    """(lo, hi) containing E(k), n = 4k - 1, from the odd primes <= P: the
    truncated product as exp of an exactly rounded sum of logarithms,
    widened by the tail bound and the rounding allowance (0.06 s at 2^22,
    about 1 s at 2^26 and 6 s at 2^28 -- the tiers past 2^20 are reached
    once in hundreds of windows and more)."""
    n = int(n)
    parts, absparts = [], []
    for ps in _odd_prime_chunks(P):
        r = (-n) % ps
        split = _powmod_vec(r, (ps - 1) // 2, ps) == 1
        inert = (r != 0) & ~split
        pf = ps.astype(np.float64)
        terms = np.zeros(len(ps), dtype=np.float64)
        terms[split] = np.log1p(-1.0 / ((pf[split] - 1.0) ** 2))
        terms[inert] = -np.log1p(-1.0 / (pf[inert] ** 2))
        parts.append(math.fsum(terms.tolist()))
        absparts.append(math.fsum(np.abs(terms).tolist()))
    L = math.fsum(parts)
    # each term within 8 ulps of itself (an argument and a log1p of a few
    # ulps each), each partial and the total exactly rounded
    d = 8.0 * _U * math.fsum(absparts) + (len(parts) + 1) * _U * abs(L) \
        + 1e-16
    T = tail_bound(P)
    return (math.exp(L - T - d) * (1.0 - 4.0 * _U),
            math.exp(L + T + d) * (1.0 + 4.0 * _U))


def C_bounds(n, hD, P):
    """(lo, hi) containing C(k) for n = 4k - 1 and h(-n) = hD."""
    w = 6 if n == 3 else 2
    lo, hi = E_bounds(n, P)
    s = 2 * w * math.sqrt(n) / (3 * math.pi * hD)
    return s * lo * (1 - 1e-13), s * hi * (1 + 1e-13)


# The prime tiers classify() refines through, each only when the interval
# of the one before straddles a cut (the record, the near threshold or a
# census bin edge).  Past the last one the only exact road is the analytic
# route at 30 digits (_resolve in the launcher: four minutes at k = 10^10,
# forty at 10^12).  Until 2026-11-11 the tiers stopped at 2^20 with the
# looser tail bound, a survivor within 2.4e-6 of the census floor reached
# that road once in ~450 windows at k = 1.3*10^10, and the first engine-v3
# run spent ~90% of its wall clock there.  The deep tiers settle what they
# are handed in 0.06 s (2^22) to ~6 s (2^28); with the tighter tail bound a
# survivor reaches the analytic road about once in 750,000 windows
# (OPTIMIZATION_LOG.md 2.13 has the counts).
P_TIERS = (199, 9973, 1 << 20, 1 << 22, 1 << 24, 1 << 26, 1 << 28)
P_CHECK = 1 << 20           # enough for the 5- and 7-decimal canary checks


def bin_of(c):
    return int(math.floor((c - CENSUS_FLOOR) / BIN_W))


def bin_label(i):
    return f"{CENSUS_FLOOR + BIN_W * i:.2f}"


def census_str(counts):
    """`census 7.50:1203 7.75:310 8.00:71` -- counts of C per bin of BIN_W
    from CENSUS_FLOOR (the repo's census_str is keyed by run length; this
    entry's census is keyed by C, so the keys are the bins' lower edges)."""
    if not counts:
        return "census -"
    ks = sorted(int(x) for x in counts)
    return "census " + " ".join(
        f"{bin_label(i)}:{int(counts.get(str(i), counts.get(i, 0)))}"
        for i in range(ks[0], ks[-1] + 1))


def event_kind(c, record_c):
    """The discovery-once taxonomy on point values: beyond the standing
    record -> DISCOVERY; within NEAR_MARGIN below it -> NEAR; at or above
    CENSUS_FLOOR -> CENSUS (counted, never narrated); else None."""
    if c > record_c:
        return "DISCOVERY"
    if c >= record_c * (1 - NEAR_MARGIN):
        return "NEAR"
    if c >= CENSUS_FLOOR:
        return "CENSUS"
    return None


def same_constant(n1, n2):
    """C equal EXACTLY: n1*n2 a square and equal prime supports (every
    local factor then agrees: the conductor's primes all ramify)."""
    r = math.isqrt(n1 * n2)
    if r * r != n1 * n2:
        return False
    for a, b in ((n1, n2), (n2, n1)):
        m = a
        while True:
            t = math.gcd(m, b)
            if t == 1:
                break
            m //= t
        if m != 1:
            return False
    return True


def classify(k, t3, rec):
    """Classify one survivor against the standing record.

    rec = (k_rec, lo, hi) or None.  Returns (kind, lo, hi, hD, P): kind in
    DISCOVERY / NEAR / CENSUS / None / "TIE" / "UNRESOLVED"; (lo, hi) the
    interval that decided it.  The interval is refined through P_TIERS
    only as far as the decision (record, near band, census bin) needs."""
    n = 4 * k - 1
    d, f, hd, hD = h_from_t3(n, t3)
    rk, rlo, rhi = rec if rec else (None, 0.0, 0.0)
    near = rlo * (1 - NEAR_MARGIN)
    lo = hi = 0.0
    P = P_TIERS[0]
    for P in P_TIERS:
        lo, hi = C_bounds(n, hD, P)
        if lo > rhi:
            return "DISCOVERY", lo, hi, hD, P
        if hi < rlo:
            cuts = [near, CENSUS_FLOOR] + [
                CENSUS_FLOOR + BIN_W * i for i in
                range(1, int((hi - CENSUS_FLOOR) / BIN_W) + 2)]
            if not any(lo < c <= hi for c in cuts):
                if lo >= near:
                    return "NEAR", lo, hi, hD, P
                if lo >= CENSUS_FLOOR:
                    return "CENSUS", lo, hi, hD, P
                return None, lo, hi, hD, P
        elif rk is not None and same_constant(n, 4 * rk - 1):
            # an exact tie can never separate from the record: say so at
            # the first tier that meets it, not after every tier to 2^28
            # (7 s), and bin it by the record's own interval
            return "TIE", rlo, rhi, hD, P
    if rk is not None and same_constant(n, 4 * rk - 1):
        return "TIE", lo, hi, hD, P
    return "UNRESOLVED", lo, hi, hD, P


# ===================== the class-group prefilter: the CPU reference
#
# WHAT IT PROVES.  Write n = 4k - 1 = d f^2, d squarefree (-d is the
# fundamental discriminant; d == n == 3 mod 8 since f is odd).  For d > 3
# the rule's own quantity is exactly
#     T(n) = 3 H(n) = 3 h(-d) S(f),  S(f) = prod_{p^e || f}
#                                  (1 + (p - (-d|p)) (p^e - 1)/(p - 1))
# (the header's Hurwitz relation), so a k is dropped by the survivor rule as
# soon as SOME lower bound L <= h(-d) satisfies (double)(3*L*S(f))*2F*rho(n)
# >= PI_UP*sqrt(n)*Q(n): the rule is monotone in T.  (The Codex review's
# HLC-002: the group work is done for the fundamental discriminant, whose
# class group is smaller by the factor h(-n)/h(-d) = prod p^(e-1)(p - (-d|p)),
# and S(f) carries the conductor exactly.  d = 3, where T = S(f), is always
# counted.)  Counting every form gives the bound the expensive way
# (~0.13*sqrt(n) increments); the class GROUP gives it in O(d^(1/4))
# compositions:
#
#   G = the class group of primitive forms of discriminant -d (d == 3 mod 8,
#   squarefree), t = the number of distinct primes dividing d.  Genus
#   theory (Gauss; Cox, "Primes of the form x^2 + ny^2", Prop. 3.11 and
#   Thm. 3.15 for an odd discriminant): G has exactly 2^(t-1) elements of
#   order <= 2, so |G/G^2| = 2^(t-1) and  h = 2^(t-1) * |G^2|.
#
#   (1) f a form, m = ord(f).  The cyclic group <f> meets G[2] in at most
#       two elements, so h >= |<f> G[2]| >= m * 2^(t-2)  (t >= 2), and
#       h >= m always.
#   (2) m' = ord(f^2) = m / gcd(m, 2); <f^2> lies in G^2, so
#       h >= 2^(t-1) * m'.
#   (3) g another form, e' = the least e >= 1 with (g^2)^e in <f^2>.  Then
#       |<f^2, g^2>| = m' * e' and it lies in G^2:  h >= 2^(t-1) * m' * e'.
#       (g^2)^e in <f^2> forces ((g^2)^m')^e = 1, so e' >= ord((g^2)^m')
#       -- a cheaper sufficient test, tried first.
#   (Engine v2's bound (4), H(n) >= h(-n) prod (1 + 1/(p - chi)) over the
#   p <= 251 with p^2 | n, was the part of S(f) visible from the group of
#   -n; the descent replaces it with all of S(f).)
#
# The factorization comes from trial division to the cube root: what is
# left is 1, a prime, a product of two primes (all in d) or the square of a
# prime (in f), told apart by a square test and a base-2 strong probable
# prime test.  Every statement is a LOWER bound, t may be undercounted (a
# lower bound of t is all the proofs use), and a k the prefilter cannot
# decide is simply counted: nothing here can add a survivor or remove one.
# The forms are the prime forms (p, b, .) of discriminant -d of the first
# primes p <= 251 split for -d.
#
# The GPU engine implements the same decision with its own arithmetic
# (64-bit wrapping products, inverses modulo 2^64, a hashed table of giant
# steps walked by prime-form steps); this reference uses Python integers,
# dictionaries and the textbook composition, and gate P5 pins the two
# decisions bit-for-bit.  The decision is a function of n, the floor and
# the trial-division bound alone: neither side's step sizes enter it.
PRE_MIN_N = 1 << 20         # below this every k is tabulated
PRE_NGENS = 8               # split primes used (the base and its partners)
PRE_NBASE = 2               # base forms tried
PRE_CAP2 = 16               # largest index e' worth proving in (3)
PRE_NEED_MAX = 1 << 28      # a bound above this is not attempted (v3: 2^22,
                            # which no n below 2^46 reaches: need < 6e5)


def form_reduce(a, b, c):
    """The reduced form equivalent to (a, b, c), a, c > 0."""
    while True:
        if a > c:
            a, b, c = c, -b, a
        if -a < b <= a:
            if a == c and b < 0:
                b = -b
            return a, b, c
        q = (b + a) // (2 * a)
        if b - 2 * a * q == -a:
            q -= 1
        b2 = b - 2 * a * q
        c = c - q * (b + b2) // 2
        b = b2


def _xgcd(a, b):
    """(u, v, d): u*a + v*b = d = gcd(a, b), for a, b >= 0."""
    u0, v0, u1, v1 = 1, 0, 0, 1
    while b:
        q = a // b
        a, b = b, a - q * b
        u0, u1 = u1, u0 - q * u1
        v0, v1 = v1, v0 - q * v1
    return u0, v0, a


def form_compose(f1, f2, n):
    """The reduced composition of two forms of discriminant -n (Cohen, "A
    Course in Computational Algebraic Number Theory", Algorithm 5.4.7)."""
    a1, b1, c1 = f1
    a2, b2, c2 = f2
    if a1 > a2:
        a1, b1, c1, a2, b2, c2 = a2, b2, c2, a1, b1, c1
    s = (b1 + b2) // 2
    m = b2 - s
    if a2 % a1 == 0:
        y1, d = 0, a1
    else:
        y1, _v, d = _xgcd(a2, a1)
    if s % d == 0:
        y2, x2, d1 = -1, 0, d
    else:
        u, v, d1 = _xgcd(abs(s), d)
        x2, y2 = (-u if s < 0 else u), -v
    v1, v2 = a1 // d1, a2 // d1
    r = (y1 * y2 * m - x2 * c2) % v1
    b3 = b2 + 2 * v2 * r
    a3 = v1 * v2
    c3, rem = divmod(b3 * b3 + n, 4 * a3)
    if rem:
        raise ArithmeticError(f"composition left discriminant -{n}")
    return form_reduce(a3, b3, c3)


def form_pow(f, e, n):
    g, base = (1, 1, (n + 1) // 4), f
    while e:
        if e & 1:
            g = form_compose(g, base, n)
        e >>= 1
        if e:
            base = form_compose(base, base, n)
    return g


def _sprp2(c):
    d, s = c - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    x = pow(2, d, c)
    if x == 1 or x == c - 1:
        return True
    for _ in range(s - 1):
        x = x * x % c
        if x == c - 1:
            return True
    return False


def icbrt_up(n):
    """The least integer P with P^3 > n."""
    P = int(round(n ** (1.0 / 3.0)))
    while P * P * P > n:
        P -= 1
    while P * P * P <= n:
        P += 1
    return P


def prefilter_setup(n, f2, P1, rl=None):
    """(t, need, gens, d): n = d f^2 by trial division by the odd primes <=
    P1 (then the cofactor is 1, a prime, the square of a prime or a product
    of two primes when P1^3 > n: a square goes to f, anything else to d, a
    base-2 strong probable prime counting one prime and anything else
    two); t a lower bound of the number of distinct primes dividing d; need
    the least L with which the survivor rule drops the count 3 L S(f) (rho
    in ascending p, as the device does; the local factor Q(n) in the
    rule's right side), so that h(-d) >= need drops n; gens the first
    primes split for -d with the odd root of -d.  rl: the window's
    rho_large (default: n's own)."""
    rho, t, c, d = (rho_large(n) if rl is None else rl), 0, n, 1
    fpart = []
    for p in primes_upto(P1)[1:]:
        p = int(p)
        if c % p == 0:
            e = 0
            while c % p == 0:
                c //= p
                e += 1
            if e & 1:
                d *= p
                t += 1
            if e >= 2:
                fpart.append((p, e))
                if p <= SMALLP[-1]:
                    rho = rho * (1.0 - 1.0 / p)
    if c > 1:
        r = math.isqrt(c)
        if r * r == c:
            fpart.append((r, 2))
        else:
            d *= c
            t += 1 if _sprp2(c) else 2
    S = 1
    for p, e in fpart:
        chi = 0 if e & 1 else legendre(-(n // p ** e), p)
        S *= 1 + (p - chi) * (p ** (e // 2) - 1) // (p - 1)
    R = PI_UP * math.sqrt(float(n))
    R = R * local_q(n)

    def drops(L):
        A = float(3 * L * S) * f2
        return not (A * rho < R)
    need = max(1, int(R / (3.0 * f2 * rho * float(S))))
    while not drops(need):
        need += 1
    while need > 1 and drops(need - 1):
        need -= 1
    gens = []
    for p in SMALLP:
        r = (-d) % p
        if r == 0:
            continue
        for b in range(1, p, 2):
            if (b * b - r) % p == 0:
                gens.append((p, b))
                break
        if len(gens) == PRE_NGENS:
            break
    return t, need, gens, d


def _order_upto(f, n, limit):
    """ord(f) if it is <= limit, else None: baby steps f^r, giant steps
    (f^s)^i; the first collision is the order itself."""
    if limit < 1:
        return None
    one = (1, 1, (n + 1) // 4)
    s = math.isqrt(limit) + 1
    table, g = {}, one
    for r in range(s):
        if r and g == one:
            return r
        table[g] = r
        g = form_compose(g, f, n)
    F = G = g
    for i in range(1, s + 1):
        r = table.get(G)
        if r is not None:
            m = s * i - r
            return m if m <= limit else None
        G = form_compose(G, F, n)
    return None


def _in_squares(w, f, m, n):
    """Is w in <f^2>?  (m = ord(f).)  A discrete logarithm in <f>, then
    the parity of the exponent when m is even."""
    s = math.isqrt(m) + 1
    table, g = {}, (1, 1, (n + 1) // 4)
    for r in range(s):
        table.setdefault(g, r)
        g = form_compose(g, f, n)
    Finv = form_reduce(g[0], -g[1], g[2])
    v = w
    for i in range(s + 1):
        r = table.get(v)
        if r is not None:
            return (m & 1 == 1) or ((s * i + r) & 1 == 0)
        v = form_compose(v, Finv, n)
    return False


def prefilter_flag(n, f2, P1, rl=None):
    """True: count T(n).  False: h(-d) >= need is PROVED (n = d f^2), so
    the survivor rule drops k = (n + 1)/4 whatever T(n) is."""
    if n < PRE_MIN_N or f2 <= 0.0:
        return True
    t, need, gens, n = prefilter_setup(n, f2, P1, rl)  # n := d from here on
    if n == 3:
        return True                   # T = S(f): the sparse count counts it
    if need <= 1:
        return False
    if not gens:
        return True
    need1 = -(-need // (1 << max(t - 2, 0)))
    if need1 <= 1:
        return False
    if need1 > PRE_NEED_MAX:
        return True
    one = (1, 1, (n + 1) // 4)
    forms = [form_reduce(p, b, (b * b + n) // (4 * p)) for p, b in gens]
    G2 = 1 << max(t - 1, 0)
    for base in range(min(PRE_NBASE, len(forms))):
        f1 = forms[base]
        m1 = _order_upto(f1, n, need1 - 1)
        if m1 is None:
            return False                                    # (1)
        mp = m1 if m1 & 1 else m1 >> 1
        if G2 * mp >= need:
            return False                                    # (2)
        need2 = -(-need // (G2 * mp))
        if need2 > PRE_CAP2:
            continue
        others = [f for j, f in enumerate(forms) if j != base]
        for f in others:                                    # (3), cheap form
            u = form_pow(form_compose(f, f, n), mp, n)
            w, good = u, True
            for _e in range(1, need2):
                if w == one:
                    good = False
                    break
                w = form_compose(w, u, n)
            if good:
                return False
        for f in others:                                    # (3)
            g2 = form_compose(f, f, n)
            w, good = g2, True
            for _e in range(1, need2):
                if _in_squares(w, f1, m1, n):
                    good = False
                    break
                w = form_compose(w, g2, n)
            if good:
                return False
    return True


def prefilter_window(m0, W, floor):
    """The flags of [m0, m0 + W) as a bool array (True: tabulate)."""
    m0, W = int(m0), int(W)
    nmax = 8 * (m0 + W - 1) + 3
    P1, rl = icbrt_up(nmax), rho_large(nmax)
    f2 = 2.0 * float(floor)
    return np.array([prefilter_flag(8 * (m0 + i) + 3, f2, P1, rl)
                     for i in range(W)], dtype=bool)


# ============================================== independent class numbers
def chi_table(d, J):
    """chi(j) = (-d|j) for 0 <= j <= J (Kronecker; d == 3 mod 8, so
    chi(2) = -1), filled multiplicatively from Euler's criterion."""
    chi = np.ones(J + 1, dtype=np.int8)
    chi[0] = 0
    for p in primes_upto(J):
        p = int(p)
        s = -1 if p == 2 else legendre(-d, p)
        if s == 1:
            continue
        q = p
        while q <= J:
            chi[q::q] *= s
            if s == 0:
                break
            q *= p
    return chi


def class_number_analytic(d):
    """h(-d) for squarefree d == 3 (mod 4), d > 3, from the theta series

        h = sum_{j >= 1} chi(j) * (erfc(j*sqrt(pi/d))
                                   + sqrt(d)/(pi*j) * exp(-pi*j^2/d)),

    in doubles, truncated where the tail is below 1e-3; returns (h, frac)
    with frac the distance of the sum from the integer h.  No form and no
    square is counted: a class number by a different road."""
    d = int(d)
    a = math.sqrt(math.pi / d)
    X = 3.0
    while math.exp(-X * X) / (math.sqrt(math.pi) * a * X * X) > 1e-3:
        X += 0.1
    J = int(X / a) + 2
    chi = chi_table(d, J)
    j = np.arange(1, J + 1, dtype=np.float64)
    x = j * a
    erfc = np.fromiter((math.erfc(v) for v in x), dtype=np.float64, count=J)
    terms = chi[1:] * (erfc + np.exp(-x * x) / (math.sqrt(math.pi) * x))
    s = float(np.sum(terms))
    h = int(round(s))
    return h, abs(s - h)


def hurwitz3_analytic(n):
    """T(n) = 3H(n) rebuilt from the analytic class number of the
    fundamental discriminant -- the host's independent check of one
    tabulated count.  Returns (T, frac)."""
    d, f = square_part(n)
    if d == 3:
        hd, frac = 1, 0.0
    else:
        hd, frac = class_number_analytic(d)
    S = 1
    for p, e in f.items():
        chi = legendre(-d, p)
        S *= 1 + (p - chi) * (p ** e - 1) // (p - 1)
    return (S if d == 3 else 3 * hd * S), frac


# Direct enumeration is O(n): measured 0.8 s at n = 4.1e9 and 15 s at
# 7.2e10, so ~14 minutes at this bound (k = 10^12) and hours above it.
ENUM_MAX_N = 4 * 10**12


def class_number_enum(n):
    """h(-n): the reduced PRIMITIVE forms of discriminant -n (n == 3 mod
    4), enumerated directly -- every odd b in (0, a], every a with
    3a^2 <= n, testing 4a | b^2 + n.  The third confirmation."""
    n = int(n)
    return _enum_chunk(n, 1, math.isqrt(n // 3) + 1)


def _enum_bounds(n, chunks):
    """Split a in [1, isqrt(n/3)] into `chunks` ranges of about equal work
    (the work at a is ~a/2 values of b, so the cuts are at A*sqrt(i/C))."""
    A = math.isqrt(n // 3)
    cuts = sorted({1} | {max(1, math.isqrt(A * A * i // chunks))
                         for i in range(1, chunks)} | {A + 1})
    return list(zip(cuts[:-1], cuts[1:]))


def _enum_chunk(n, a0, a1):
    """The reduced primitive forms of discriminant -n with a0 <= a < a1,
    counted as class_number_enum counts them (a sum over a, so chunks of
    a add up to h(-n) exactly)."""
    n = int(n)
    assert n % 4 == 3
    h = 0
    for a in range(int(a0), int(a1)):
        b = np.arange(1, a + 1, 2, dtype=np.int64)
        t = b * b + n
        ok = (t % (4 * a)) == 0
        if not ok.any():
            continue
        b = b[ok]
        c = t[ok] // (4 * a)
        keep = c >= a
        b, c = b[keep], c[keep]
        for bi, ci in zip(b.tolist(), c.tolist()):
            if math.gcd(a, math.gcd(bi, ci)) == 1:
                h += 1 if (bi == a or ci == a) else 2
    return h


# ===================== Cohen's route: C to 30+ digits, no class number
def _mobius(n):
    m, p = 1, 2
    while p * p <= n:
        if n % p == 0:
            n //= p
            if n % p == 0:
                return 0
            m = -m
        p += 1
    return -m if n > 1 else m


def _afe_chunk(q, N, smax, bits, E, c0, step):
    """One chunk of the Lambda-sums of the approximate functional equation
    for the odd primitive real character chi = (-q|.):

        Lam(s) = sum_{n <= N} chi(n) n [x^-a G(a, x) + x^-b G(b, x)],
        x = pi n^2 / q, a = (s+1)/2, b = (2-s)/2, G the upper incomplete
        gamma function,

    over the n == c0 + 1 (mod step), for s = 1..smax, with G by recurrence
    from exp(-x), erfc(sqrt x) and E1(x) at `bits` of precision.  Every
    term is computed exactly as the serial route of engine v3 computed it
    and truncated to the grid 2^-E[s]; the chunk returns the INTEGER sums.
    Integer addition is exact, so the total does not depend on how the n
    are split -- one process or twelve, the same digits.  chi(n) is the
    Kronecker symbol, one gmpy2 call per n: no table, so a chunk needs no
    memory that grows with q.

    The recurrences, for the normalised g(j) = G(j/2, x) x^(-j/2):
        up:    g(a + 1) = (a g(a) + e^-x) / x
        down:  g(a - 1) = (x g(a) - e^-x) / (a - 1)
    from g(1) = e^-x / x, g(0) = E1(x), g(1/2) = sqrt(pi) erfc(sqrt x)
    / sqrt x.  The downward steps cancel ~log10(2x) digits each; the
    caller's guard digits cover the at most smax/2 of them."""
    import gmpy2
    acc = [0] * (smax + 1)
    with gmpy2.context(gmpy2.get_context(), precision=int(bits)):
        mpf = gmpy2.mpfr
        pi = gmpy2.const_pi()
        sqrtpi = gmpy2.sqrt(pi)
        piq = pi / int(q)
        zero, half = mpf(0), mpf(1) / 2
        off = smax
        top, bot = smax + 1, 2 - smax
        g = [None] * (2 * smax + 4)
        mq = -int(q)
        kron, fexp, ferfc = gmpy2.kronecker, gmpy2.exp, gmpy2.erfc
        fsqrt, fe1, shift = gmpy2.sqrt, gmpy2.gamma_inc, gmpy2.mul_2exp
        for n in range(int(c0) + 1, int(N) + 1, int(step)):
            ch = kron(mq, n)
            if not ch:
                continue
            x = piq * n * n
            sx = fsqrt(x)
            e = fexp(-x)
            xinv = 1 / x
            g[off + 2] = e * xinv
            g[off] = fe1(zero, x)
            g[off + 1] = sqrtpi * ferfc(sx) / sx
            for j0 in (2, 1):
                j = j0
                while j + 2 <= top:
                    g[off + j + 2] = (g[off + j] * j * half + e) * xinv
                    j += 2
            for j0 in (0, 1):
                j = j0
                while j - 2 >= bot:
                    g[off + j - 2] = (x * g[off + j] - e) * 2 / (j - 2)
                    j -= 2
            c = int(ch) * n
            for s in range(1, smax + 1):
                acc[s] += int(shift(c * (g[off + s + 1] + g[off + 2 - s]),
                                    E[s]))
    return acc


# A find's confirmations are one heavy host computation: the AFE's terms
# (~sqrt(4k - 1) of them, 220 us each at 34 digits) and, below ENUM_MAX_N,
# the enumeration of forms (O(k)).  Both are sums, so both split into
# chunks that a process pool runs side by side; the launcher sizes the
# pool from confirm_seconds() (OPTIMIZATION_LOG.md round 3).
AFE_TERM_S = 2.2e-4         # one AFE term at 34 digits (229 bits), one core:
                            # 213-217 us measured at a(32), 2026-11-12
ENUM_N_S = 1.9e-10          # the enumeration per unit of n: 16 s at n = 8.6e10


def _hp_size(k, digits):
    """(n, N): 4k - 1 and the AFE's length (an upper bound: the true
    length uses the squarefree part d <= n)."""
    n = 4 * int(k) - 1
    X = (digits + 8) * math.log(10)
    return n, int(math.sqrt(X * n / math.pi)) + 2


def confirm_seconds(k, digits=34):
    """One core's seconds for the CPU legs of a find at k: the AFE terms
    and (below ENUM_MAX_N) the enumeration, at their measured costs."""
    n, N = _hp_size(k, digits)
    return N * AFE_TERM_S + (n * ENUM_N_S if n <= ENUM_MAX_N else 0.0)


def _start(tasks, pool=None, workers=1, ramp_s=0.35):
    """Begin [(fn, args)].  On a pool the first `workers` submissions go
    `ramp_s` apart -- each starts one interpreter while the earlier ones
    already work, so the pool is RAMPED with real work instead of stamped
    (CONVENTIONS.md "Sizing a hunt") -- and the rest at once.  Without a
    pool nothing starts here: _collect runs the tasks in this process."""
    if pool is None:
        return [(fn, args) for fn, args in tasks]
    out = []
    for i, (fn, args) in enumerate(tasks):
        out.append(pool.submit(fn, *args))
        if i + 1 < workers:
            time.sleep(ramp_s)
    return out


def _wait(fut):
    """A future's result, waited for in quarter-second slices: on Windows a
    blocking wait defers Ctrl+C until the future completes -- minutes, for
    a chunk of the confirmations -- and a sliced one sees it at once."""
    while True:
        try:
            return fut.result(timeout=0.25)
        except TimeoutError:
            continue


def _collect(started):
    return [_wait(s) if hasattr(s, "result") else s[0](*s[1])
            for s in started]


def _hp_plan(k, digits=34, P0=1 << 16):
    """Everything Cohen's route fixes before the AFE: the factorization,
    the AFE's length N, the number of L-values smax, the working precision
    and the fixed-point grids E[s] (2^-(bits + 32) of the AFE's largest
    term, the n = 1 term ~ Gamma(a) (q/pi)^a, so N truncations cost under
    2^-(bits + 32 - log2 N) of Lam(s) -- far inside the guard digits)."""
    from sympy import factorint
    k = int(k)
    n = 4 * k - 1
    fac = {int(p): int(e) for p, e in factorint(n).items()}
    d, f = 1, {}
    for p, e in fac.items():
        if e % 2:
            d *= p
        if e // 2:
            f[p] = e // 2
    guard = 30
    X = (digits + 8) * math.log(10)
    N = int(math.sqrt(X * d / math.pi)) + 2
    # how far the tail series must go: (2/P0)^s * P0 < 10^-(digits+6)
    scut = 2
    while (2.0 / P0) ** scut * P0 > 10.0 ** -(digits + 6):
        scut += 1
    smax = scut                         # L(s, chi) for s = 1..scut
    bits = int((digits + guard) * 3.33) + 16
    E = [0] + [bits + 32 - math.floor(math.lgamma((s + 1) / 2) / math.log(2)
                                      + (s + 1) / 2 * math.log2(d / math.pi))
               for s in range(1, smax + 1)]
    return {"k": k, "n": n, "fac": fac, "d": d, "f": f, "guard": guard,
            "N": max(N, 2), "scut": scut, "smax": smax, "bits": bits,
            "E": E, "digits": digits, "P0": P0}


def _hp_tasks(plan, chunks=1):
    """The AFE as `chunks` interleaved chunks (n == c + 1 mod chunks, so
    every chunk sees the same mix of x and costs the same)."""
    return [(_afe_chunk, (plan["d"], plan["N"], plan["smax"], plan["bits"],
                          plan["E"], c, chunks)) for c in range(chunks)]


def _hp_finish(plan, parts):
    """C(k) from the summed chunks: the L-values, then the Euler products.

        C = (4/3) / L(1, chi) / prod_{p | f} (1 - chi(p)/p) * E,
        log E = sum_{3 <= p <= P0, p not | n} log e_p
              + sum_{j >= 2} [a_j Pz(j) + b_j Px(j)]
              - sum_{p | n, p > P0} [A(1/p) + chi(p) B(1/p)],
    where log e_p = A(1/p) + chi(p) B(1/p),
        A(x) = [log(1-2x) - 3 log(1-x) - log(1+x)]/2 = sum a_j x^j,
        B(x) = [log(1-2x) -   log(1-x) + log(1+x)]/2 = sum b_j x^j,
    Pz(j), Px(j) the sums of p^-j and chi(p) p^-j over p > P0, by Moebius
    inversion of log zeta(mj) and log L(mj, chi^m) with the Euler factors
    of p <= P0 removed."""
    import mpmath
    k, n, fac, d, f = plan["k"], plan["n"], plan["fac"], plan["d"], plan["f"]
    digits, guard, P0 = plan["digits"], plan["guard"], plan["P0"]
    scut, smax, E = plan["scut"], plan["smax"], plan["E"]
    mpmath.mp.dps = digits + guard
    mp = mpmath.mp
    q = mpmath.mpf(d)
    L = {}
    for s in range(1, smax + 1):
        lam = mpmath.ldexp(mpmath.mpf(sum(p[s] for p in parts)), -E[s])
        a = mpmath.mpf(s + 1) / 2
        L[s] = lam / ((q / mp.pi) ** a * mpmath.gamma(a))
    pr = [int(p) for p in primes_upto(P0)]
    chis = {p: (-1 if p == 2 else legendre(-d, p)) for p in pr}
    # Euler products over p > P0
    logz, logL = {}, {}

    def lz(s):
        if s not in logz:
            v = mpmath.log(mpmath.zeta(s))
            for p in pr:
                v += mpmath.log1p(-mpmath.mpf(p) ** -s)
            logz[s] = v
        return logz[s]

    def ll(s):
        if s not in logL:
            v = mpmath.log(L[s])
            for p in pr:
                if chis[p]:
                    v += mpmath.log1p(-chis[p] * mpmath.mpf(p) ** -s)
            logL[s] = v
        return logL[s]

    big_ram = [p for p in fac if p > P0 and d % p == 0]
    logE = mpmath.mpf(0)
    for p in pr[1:]:
        if n % p == 0:
            continue
        if chis[p] == 1:
            logE += mpmath.log1p(-mpmath.mpf(1) / ((p - 1) * (p - 1)))
        else:
            logE -= mpmath.log1p(-mpmath.mpf(1) / (p * p))
    for j in range(2, scut + 1):
        aj = mpmath.mpf(3 - 2 ** j + (-1) ** j) / (2 * j)
        bj = mpmath.mpf(1 - 2 ** j - (-1) ** j) / (2 * j)
        pz = px = mpmath.mpf(0)
        m = 1
        while m * j <= scut:
            mu = _mobius(m)
            if mu:
                z = lz(m * j)
                pz += mpmath.mpf(mu) / m * z
                if m % 2:
                    px += mpmath.mpf(mu) / m * ll(m * j)
                else:
                    t = z
                    for p in big_ram:
                        t += mpmath.log1p(-mpmath.mpf(p) ** -(m * j))
                    px += mpmath.mpf(mu) / m * t
            m += 1
        logE += aj * pz + bj * px
    for p in fac:
        if p > P0:
            x = mpmath.mpf(1) / p
            A = (mpmath.log1p(-2 * x) - 3 * mpmath.log1p(-x)
                 - mpmath.log1p(x)) / 2
            B = (mpmath.log1p(-2 * x) - mpmath.log1p(-x)
                 + mpmath.log1p(x)) / 2
            c = 0 if d % p == 0 else legendre(-d, p)
            logE -= A + c * B
    C = mpmath.mpf(4) / 3 / L[1] * mpmath.exp(logE)
    for p in f:
        c = 0 if d % p == 0 else legendre(-d, p)
        C /= (1 - mpmath.mpf(c) / p)
    w = 6 if d == 3 else 2
    h_an = w * mpmath.sqrt(q) * L[1] / (2 * mp.pi)
    return {"C": C, "err": abs(C) * mpmath.mpf(10) ** -(digits - 1),
            "h_analytic": h_an, "d": d, "f": f, "terms": plan["N"],
            "P0": P0, "digits": digits}


def C_highprec(k, digits=34, P0=1 << 16, pool=None, workers=1):
    """C(k) to `digits` significant digits by Cohen's route, with the
    L-values by the approximate functional equation -- no class number, no
    form, no sum of squares enters.  Returns a dict:

        C          mpmath.mpf
        err        a bound on |C - true| (dominated by the stated cuts)
        h_analytic w*sqrt(d)*L(1, chi)/(2 pi) for the fundamental -d
        d, f       n = 4k - 1 = d * f^2

    With chi = (-d|.) primitive mod d and odd; _hp_finish states the
    method.  pool: an Executor of `workers` processes for the AFE's chunks
    (four per worker, so the early workers take up the slack of the ramp);
    the digits are the same with or without it."""
    plan = _hp_plan(k, digits, P0)
    started = _start(_hp_tasks(plan, 4 * workers if pool else 1), pool,
                     workers)
    return _hp_finish(plan, _collect(started))


# ================================================== the three confirmations
def verify_find(k, t3, rec, digits=34, recount=None, pool=None, workers=1):
    """The discovery protocol for a candidate record at k.

    rec = (k_rec, lo, hi) the standing record.  `recount(k)` is the
    engine-side alternate-alignment recount of T(4k - 1) (the launcher
    passes the GPU engine's; None skips it, and a recount that returns
    None says the engine does not reach that height).  pool / workers: an
    Executor for the CPU legs' chunks -- the AFE and the enumeration of
    forms run side by side on it while this process does the recount;
    the evidence is the same with or without it.  Returns (ok, evidence
    dict); ok is False when any leg disagrees -- an engine bug by
    definition."""
    import mpmath
    n = 4 * k - 1
    ev = {"n_minus": n, "T": int(t3)}
    d, f, hd, hD = h_from_t3(n, t3)
    lo, hi = C_bounds(n, hD, P_CHECK)
    ev["leg1_engine"] = {
        "h": hD, "fundamental_d": -d, "conductor": {str(p): e
                                                    for p, e in f.items()},
        "h_fundamental": hd, "C_interval": [repr(lo), repr(hi)],
        "primes_to": P_CHECK, "tail_bound": tail_bound(P_CHECK),
        "exceeds_record": bool(rec is None or lo > rec[2])}
    ok = ev["leg1_engine"]["exceeds_record"]
    plan = _hp_plan(k, digits)
    tasks = _hp_tasks(plan, 4 * workers if pool else 1)
    nafe = len(tasks)
    if n <= ENUM_MAX_N:
        tasks += [(_enum_chunk, (n, a0, a1)) for a0, a1 in
                  _enum_bounds(n, max(1, workers) if pool else 1)]
    started = _start(tasks, pool, workers)
    t2 = None
    if recount is not None and pool is not None:
        t2 = recount(k)                     # on the device, meanwhile
    parts = _collect(started)
    if recount is not None and pool is None:
        t2 = recount(k)
    hp = _hp_finish(plan, parts[:nafe])
    C = hp["C"]
    hn = int(mpmath.nint(hp["h_analytic"]))
    frac = abs(hp["h_analytic"] - hn)
    in_iv = lo <= C <= hi
    ev["leg2_analytic"] = {
        "C": mpmath.nstr(C, digits), "error_bound": mpmath.nstr(hp["err"], 3),
        "digits": digits, "afe_terms": hp["terms"],
        "h_fundamental_analytic": hn,
        "distance_from_integer": mpmath.nstr(frac, 3),
        "inside_leg1_interval": bool(in_iv)}
    ok = ok and in_iv and hn == (1 if d == 3 else hd) \
        and frac < mpmath.mpf(10) ** -(digits - 12)
    leg3 = {}
    if n <= ENUM_MAX_N:
        he = sum(parts[nafe:])
        leg3["h_enumerated"] = he
        leg3["method"] = ("direct enumeration of the reduced primitive "
                          "forms of discriminant 1 - 4k")
        ok = ok and he == hD
    else:
        leg3["h_enumerated"] = None
        leg3["method"] = (f"direct enumeration skipped: 4k - 1 exceeds "
                          f"{ENUM_MAX_N} (cost O(k)); the analytic class "
                          f"number of leg 2 is the second algorithm")
    if recount is not None:
        if t2 is None:
            leg3["T_recount_alternate_alignment"] = None
            leg3["recount"] = ("skipped: the three-squares recount costs "
                               "O(k) and the engine does not run it at "
                               "this height; leg 2's analytic class number "
                               "checks the count")
        else:
            t2 = int(t2)
            leg3["T_recount_alternate_alignment"] = t2
            ok = ok and t2 == int(t3)
    ev["leg3_class_number"] = leg3
    ev["C"] = mpmath.nstr(C, digits)
    ev["C_error_bound"] = mpmath.nstr(hp["err"], 3)
    if rec is not None:
        ev["previous_record"] = {"k": rec[0],
                                 "C_interval": [repr(rec[1]), repr(rec[2])]}
        ev["margin_over_previous"] = mpmath.nstr(C - rec[2], 8)
    ev["verified_3way"] = bool(ok)
    return ok, ev


# ------------------------------------------------------------------ gates
A221712 = ("3.31977317747142166532355685764988796646855458565298584915394"
           "0727950263310426118149737")
# Fung & Williams (Math. Comp. 55, 1990), as tabulated by Jacobson (1995,
# Table 6.1): discriminant D = 1 - 4k and their C(D) = C/2 to 7 decimals.
# Fourteen rows are as printed.  The row D = -60408307 is printed there as
# 4.0501092; this module computes 4.0510921 (the printed digits transposed,
# and the same table's observed ratio 4.0531570 sits beside it), so it is
# carried CORRECTED and flagged.  The table's first row, printed -88507, is
# -85507 (k = 21377, the entry's a(5)) and is covered by the eleven terms.
LITERATURE = [
    (-111763, "3.6319998"), (-222643, "3.7289570"), (-1333963, "3.8123997"),
    (-9471067, "3.9760501"), (-10560643, "4.0194873"),
    (-60408307, "4.0510921"), (-171583003, "4.0815068"),
    (-269497867, "4.1092157"), (-398158363, "4.1579113"),
    (-643338763, "4.2716019"), (-1408126003, "4.2771747"),
    (-1595514187, "4.3616794"), (-4067175907, "4.4324788"),
    (-71837718283, "4.6097143"), (-85702502803, "4.7073044"),
]


def gate_s0():
    """The rule's per-window constants: below 2^46 they are engine v3's
    (so is the stream there); at every height to the ceiling RHO_MIN is
    at most the true minimum of rho and RHO_LARGE at most the product it
    bounds, checked at each height where either changes and just below."""
    if not (SMALLP[0] == 3 and SMALLP[-1] == 251 and len(SMALLP) == 53
            and rho_large(N_OLD - 1) == RHO_LARGE
            and rho_min(N_OLD - 1) == RHO_MIN and RHO_MIN <= rho_min_true(N_OLD)
            and 0.99 < RHO_LARGE < 1):
        return False, "S0 survivor-rule constants inconsistent below 2^46"
    # the heights where a constant moves: a new prime square fits
    marks, prod = set(), 1
    for p in SMALLP:
        prod *= p * p
        if prod < N_CEIL:
            marks.add(prod)
    prod, p = 1, 257
    for p in (257, 263, 269, 271):
        prod *= p * p
        if prod < N_CEIL:
            marks.add(prod)
    heights = sorted({N_OLD, N_CEIL} | marks | {m - 1 for m in marks})
    for h in heights:
        if not N_OLD - 1 <= h <= N_CEIL:
            continue
        if rho_min(h - 1) > rho_min_true(h) or not 0.98 < rho_large(h - 1):
            return False, f"S0 rho_min({h - 1}) above the true minimum"
    return True, (f"S0 survivor rule: below 2^46 RHO_MIN = {RHO_MIN} <= the "
                  f"true minimum {rho_min_true(N_OLD):.4f} and RHO_LARGE = "
                  f"{RHO_LARGE:.5f} (two primes above 251), engine v3's; to "
                  f"the ceiling 2^62 the per-window values hold at the "
                  f"{len(heights)} heights where they move (RHO_MIN "
                  f"{rho_min(N_CEIL - 1)} <= {rho_min_true(N_CEIL):.4f}, "
                  f"RHO_LARGE {rho_large(N_CEIL - 1):.5f}, three primes)")


def gate_s1(kmax=40001):
    import hlc_reference as ref
    hs = ref.class_numbers_upto(kmax)
    t3 = h3_window(0, (kmax + 1) // 2)
    nonsf = 0
    for m, t in enumerate(t3.tolist()):
        k = 2 * m + 1
        d, f, hd, hD = h_from_t3(4 * k - 1, t)
        nonsf += bool(f)
        if hD != hs[k]:
            return False, f"S1 CPU h(1-4*{k}) = {hD}, oracle {hs[k]}"
    a = h3_window(1000, 3000)
    if not (np.array_equal(a, t3[1000:4000])
            and np.array_equal(h3_window(12345, 1), t3[12345:12346])):
        return False, "S1 CPU window split changed the counts"
    return True, (f"S1 CPU forms sieve = oracle's reduced-form counts for "
                  f"every odd k <= {kmax} ({nonsf} of them with a "
                  f"non-trivial conductor, every Hurwitz division exact); "
                  f"split windows identical")


def gate_s2():
    import random
    rnd = random.Random(331940)
    worst = 0.0
    for base in (10**5, 10**6, 3 * 10**7, 10**9):
        W = 24
        m0 = base // 2 + rnd.randrange(1000)
        t3 = h3_window(m0, W)
        for i in range(W):
            n = 8 * (m0 + i) + 3
            t, frac = hurwitz3_analytic(n)
            worst = max(worst, frac)
            if t != int(t3[i]) or frac > 0.05:
                return False, (f"S2 n = {n}: forms sieve {int(t3[i])}, "
                               f"analytic {t} (frac {frac:.3f})")
    for n in (163, 85507, 991027, 4 * 68501 - 1, 27, 243, 4 * 999983 - 1):
        d, f, hd, hD = h_from_t3(n, int(h3_window((n - 3) // 8, 1)[0]))
        if class_number_enum(n) != hD:
            return False, f"S2 direct enumeration disagrees at n = {n}"
    return True, (f"S2 three class-number algorithms agree: the forms sieve "
                  f"against the analytic theta series on 96 discriminants "
                  f"up to 4*10^9 (worst distance from an integer "
                  f"{worst:.1e}), and against direct enumeration on seven "
                  f"(two non-fundamental)")


def gate_s3():
    import mpmath
    import hlc_reference as ref
    hp = C_highprec(41, digits=44)
    got = mpmath.nstr(hp["C"] / 2, 42)
    if got[:41] != A221712[:41]:
        return False, f"S3 C(41)/2 = {got}, A221712 = {A221712[:44]}"
    if abs(hp["h_analytic"] - 1) > mpmath.mpf(10) ** -35:
        return False, "S3 analytic h(-163) is not 1"
    for k, cs in ref.KNOWN:
        hp = C_highprec(k, digits=24)
        if abs(hp["C"] - mpmath.mpf(cs)) > mpmath.mpf("0.50001e-5"):
            return False, f"S3 C({k}) = {mpmath.nstr(hp['C'], 12)} != {cs}"
        t = int(h3_window((k - 1) // 2, 1)[0])
        lo, hi = C_bounds(4 * k - 1, h_from_t3(4 * k - 1, t)[3], 1 << 16)
        if not lo <= hp["C"] <= hi:
            return False, f"S3 C({k}) outside the rigorous interval"
    hp = C_highprec(68501, digits=24)          # 4k - 1 = 163 * 41^2
    hp41 = C_highprec(41, digits=24)
    if abs(hp["C"] - hp41["C"] * 40 / 39) > mpmath.mpf(10) ** -20:
        return False, "S3 conductor rule wrong at k = 68501"
    return True, ("S3 Cohen's route: C(41)/2 agrees with A221712 to 40 "
                  "digits; all eleven table values to 5 decimals, each "
                  "inside its rigorous interval; k = 68501 (4k - 1 = "
                  "163*41^2) is C(41)*40/39 to 20 digits")


def gate_s4():
    worst = 0.0
    for D, cs in LITERATURE:
        n = -D
        t, frac = hurwitz3_analytic(n)
        d, f, hd, hD = h_from_t3(n, t)
        lo, hi = C_bounds(n, hD, 1 << 20)
        c = 2 * float(cs)
        worst = max(worst, abs((lo + hi) / 2 - c))
        if not (lo - 1.01e-7 <= c <= hi + 1.01e-7) or frac > 0.05:
            return False, (f"S4 D = {D}: [{lo:.8f}, {hi:.8f}] against "
                           f"Fung & Williams' 2*{cs}")
    return True, (f"S4 Fung & Williams' C(D) for fifteen discriminants, "
                  f"1.1*10^5 < |D| < 8.6*10^10, reproduced to their 7 "
                  f"decimals (largest difference {worst:.1e}; the row "
                  f"-60408307 as corrected in the source comment)")


def gate_s5():
    cases = [(8.30, "DISCOVERY"), (8.20, "NEAR"), (7.60, "CENSUS"),
             (7.40, None), (8.24741, "NEAR")]
    for c, want in cases:
        if event_kind(c, 8.24741) != want:
            return False, f"S5 event_kind({c}) != {want}"
    rec = (1, 2.2414, 2.2415)
    t = int(h3_window(3, 1)[0])                    # k = 7, n = 27
    if classify(7, t, rec)[0] != "TIE":
        return False, "S5 k = 7 should tie k = 1 exactly"
    t = int(h3_window((247757 - 1) // 2, 1)[0])
    kind, lo, hi, hD, P = classify(247757, t, (239621, 7.72930, 7.72934))
    if kind != "DISCOVERY" or hD != 63:
        return False, "S5 k = 247757 should be a record over 239621"
    kind = classify(239621, int(h3_window(119810, 1)[0]),
                    (247757, 8.24740, 8.24742))[0]
    if kind != "CENSUS" or census_str({"0": 3, "2": 1}) != \
            "census 7.50:3 7.75:0 8.00:1":
        return False, "S5 census classification wrong"
    return True, ("S5 event_kind: record / near (within 1%) / census bin / "
                  "below the floor; k = 7 ties k = 1 exactly and is no "
                  "record; 247757 is a record over 239621")


def gate_s6():
    """The discovery protocol in both directions, on known values."""
    t = int(h3_window((247757 - 1) // 2, 1)[0])
    rec = (239621, 7.72930, 7.72934)
    ok, ev = verify_find(247757, t, rec, digits=30,
                         recount=lambda k: h3_window((k - 1) // 2, 1)[0])
    if not ok or ev["leg3_class_number"]["h_enumerated"] != 63:
        return False, "S6 a genuine record (247757) was rejected"
    bad, _ = verify_find(247757, t + 6, rec, digits=24) \
        if (t + 6) % 3 == 0 else (True, None)
    ok2, _ = verify_find(239621, int(h3_window(119810, 1)[0]),
                         (247757, 8.24740, 8.24742), digits=24)
    if bad or ok2:
        return False, "S6 a planted claim was accepted"
    return True, ("S6 discovery protocol: 247757 over 239621 accepted on "
                  "three legs (interval; analytic C to 30 digits with "
                  "h(-991027) = 63 from L(1, chi); 63 forms enumerated); a "
                  "corrupted count and a non-record are rejected")


def _all_reduced(n):
    """Every reduced primitive form of discriminant -n, from the definition
    (the gates' ground truth for the composition law)."""
    out = []
    b = 1
    while 3 * b * b <= n:
        q = (b * b + n) // 4
        a = b
        while a * a <= q:
            if q % a == 0:
                c = q // a
                if math.gcd(math.gcd(a, b), c) == 1:
                    out.append((a, b, c))
                    if b != a and a != c:
                        out.append((a, -b, c))
            a += 1
        b += 2
    return out


def _dirichlet(f1, f2, n):
    """Composition from the definition (united forms): for coprime leading
    coefficients, the form (a1*a2, B, .) with B == b1 (mod 2a1) and
    B == b2 (mod 2a2)."""
    a1, b1, _ = f1
    a2, b2, _ = f2
    t = ((b2 - b1) // 2) * pow(a1, -1, a2) % a2
    B = b1 + 2 * a1 * t
    return form_reduce(a1 * a2, B, (B * B + n) // (4 * a1 * a2))


def gate_s7():
    """The composition law the prefilter stands on, and the genus count."""
    import random
    rnd = random.Random(331940)
    ns = list(range(3, 6000, 8)) + [8 * rnd.randrange(10**3, 10**5) + 3
                                    for _ in range(120)]
    ncomp = nform = 0
    for n in ns:
        forms = _all_reduced(n)
        h, S = len(forms), set(forms)
        one = (1, 1, (n + 1) // 4)
        # genus theory: exactly 2^(t-1) classes of order <= 2
        t, c, p = 0, n, 3
        while p * p <= c:
            if c % p == 0:
                t += 1
                while c % p == 0:
                    c //= p
            p += 2
        t += c > 1
        amb = sum(1 for f in forms if form_compose(f, f, n) == one)
        if amb != 1 << (t - 1):
            return False, (f"S7 n = {n}: {amb} classes of order <= 2, genus "
                           f"theory says 2^{t - 1}")
        sample = forms if h <= 10 else rnd.sample(forms, 10)
        for f1 in sample:
            inv = form_reduce(f1[0], -f1[1], f1[2])
            if form_compose(f1, one, n) != f1 or \
                    form_compose(f1, inv, n) != one or \
                    form_pow(f1, h, n) != one:
                return False, f"S7 n = {n}: identity / inverse / f^h fails"
            for f2 in sample:
                g = form_compose(f1, f2, n)
                ncomp += 1
                if g not in S or g != form_compose(f2, f1, n):
                    return False, f"S7 n = {n}: composition not a class"
                # the definition, after moving f2 inside its class to a
                # leading coefficient coprime to a1
                a2, b2, c2 = f2
                f2p = None
                for x in range(1, 60):
                    for y in range(0, 60):
                        if math.gcd(x, y) != 1:
                            continue
                        v = a2 * x * x + b2 * x * y + c2 * y * y
                        if math.gcd(v, f1[0]) == 1:
                            u, w, _d = _xgcd(x, y) if y else (1, 0, x)
                            p_, q_, r_, s_ = x, -w, y, u
                            B = (2 * a2 * p_ * q_ + b2 * (p_ * s_ + q_ * r_)
                                 + 2 * c2 * r_ * s_)
                            C = a2 * q_ * q_ + b2 * q_ * s_ + c2 * s_ * s_
                            f2p = (v, B, C)
                            break
                    if f2p:
                        break
                if f2p is None or form_reduce(*f2p) != f2 or \
                        g != _dirichlet(f1, f2p, n):
                    return False, (f"S7 n = {n}: {f1} o {f2} disagrees with "
                                   f"the definition")
                for f3 in sample[:3]:
                    if form_compose(g, f3, n) != \
                            form_compose(f1, form_compose(f2, f3, n), n):
                        return False, f"S7 n = {n}: not associative"
        nform += h
    return True, (f"S7 composition (Cohen 5.4.7) equals the definition by "
                  f"united forms on {ncomp} pairs over {len(ns)} "
                  f"discriminants ({nform} classes; associative, f^h = 1), "
                  f"and every one has exactly 2^(t-1) classes of order <= 2 "
                  f"(genus theory, conductors included)")


def gate_s8():
    """The prefilter reference against the forms sieve: nothing it drops is
    a survivor, and every bound it claims holds for the counted h."""
    tot = drop = 0
    for k_lo, W, floor in ((10**7 + 1, 1536, 7.5), (3 * 10**6 + 1, 1024, 4.5),
                           (262145, 512, 7.5)):
        m0 = (k_lo - 1) // 2
        t3 = h3_window(m0, W)
        mask = survivor_mask(m0, t3, floor)
        flags = prefilter_window(m0, W, floor)
        P1 = icbrt_up(8 * (m0 + W - 1) + 3)
        for i in range(W):
            if flags[i]:
                continue
            n = 8 * (m0 + i) + 3
            _t, need, _g, d = prefilter_setup(n, 2.0 * floor, P1)
            dd, _f, hd, _hD = h_from_t3(n, int(t3[i]))
            if mask[i] or hd < need or dd != d:
                return False, (f"S8 k = {(n + 1) // 4} dropped with h(-{d}) "
                               f"= {hd} < {need} (survivor: {bool(mask[i])})")
        tot += W
        drop += int(W - flags.sum())
    if drop < 0.9 * tot:
        return False, f"S8 the prefilter decided only {drop} of {tot}"
    # the rule's edges: tiny n and a zero floor are never decided
    if not (prefilter_flag(PRE_MIN_N - 5, 15.0, 200)
            and prefilter_flag(8 * 10**7 + 3, 0.0, 500)):
        return False, "S8 a k below PRE_MIN_N or at floor 0 was decided"
    return True, (f"S8 class-group prefilter (reference): {drop} of {tot} k "
                  f"dropped on three windows (k = 2.6*10^5, 3*10^6, 10^7; "
                  f"floors 7.5 and 4.5), none of them a survivor of the "
                  f"forms sieve and every claimed bound <= the counted "
                  f"class number of the fundamental discriminant; k below "
                  f"2^18 and floor 0 are always counted")


def gate_s9():
    """The local Euler factors on their own terms: every k the local rule
    removes from the universal rule's survivors has C(k) <= the floor by
    the host's rigorous interval, and no k is added."""
    removed, worst = 0, 0.0
    for k_lo, W, floor in ((262145, 8192, 5.0), (3 * 10**6 + 1, 8192, 6.0),
                           (10**7 + 1, 8192, 7.5)):
        m0 = (k_lo - 1) // 2
        t3 = h3_window(m0, W)
        new = survivor_mask(m0, t3, floor)
        old = survivor_mask(m0, t3, floor, local=False)
        if (new & ~old).any():
            return False, f"S9 the local rule kept a k the universal one drops"
        for i in np.nonzero(old & ~new)[0].tolist():
            k = 2 * (m0 + i) + 1
            _kind, lo, hi, _h, _P = classify(k, int(t3[i]), None)
            removed += 1
            worst = max(worst, hi / floor)
            if hi > floor:
                return False, (f"S9 k = {k} removed by the local rule with C "
                               f"in [{lo:.6f}, {hi:.6f}] above the floor "
                               f"{floor}")
    if removed < 50:
        return False, f"S9 windows not populated ({removed} removed)"
    return True, (f"S9 local Euler factors: of the universal rule's survivors "
                  f"on three windows (floors 5, 6, 7.5) the local rule "
                  f"removes {removed}, every one with C <= the floor by the "
                  f"rigorous interval (largest C/floor {worst:.4f}), and "
                  f"adds none")


def gate_s10():
    """The census-edge stall of 2026-11-11 (OPTIMIZATION_LOG.md 2.13): the
    two survivors that stalled the first engine-v3 run, whose C lies
    1.3e-6 below the census floor, are classified below it by a deep prime
    tier in well under a second -- never by the analytic route (minutes);
    every tier's interval contains a known C to 30 digits; the rounding
    allowance grows with the primes it covers."""
    import mpmath
    rec = (11410046357, 9.328963776428486, 9.328963776430486)
    worst = 0.0
    for k in (12763724651, 12885017267):
        n = 4 * k - 1
        d, f = square_part(n)
        h, frac = class_number_analytic(n)
        if f or frac > 0.05:
            return False, f"S10 k = {k} is not the fundamental case it was"
        t0 = time.time()
        kind, lo, hi, _hD, P = classify(k, 3 * h, rec)
        dt = time.time() - t0
        worst = max(worst, dt)
        if kind is not None or not hi < CENSUS_FLOOR or dt > 2.0:
            return False, (f"S10 k = {k}: {kind} at P = {P}, C in [{lo}, "
                           f"{hi}] in {dt:.2f}s -- not settled below the "
                           f"floor by a prime tier")
    C = mpmath.mpf("8.24741345236759360963578660603")
    for P in P_TIERS:
        lo, hi = C_bounds(991027, 63, P)
        if not mpmath.mpf(lo) <= C <= mpmath.mpf(hi):
            return False, f"S10 the tier P = {P} interval misses C(247757)"
    # the tail bound: P(2) recomputed by Moebius inversion of log zeta; the
    # bound covers the next stretch of primes it is a bound for; tighter
    # than the old 1/(3(P - 8)); and the segmented primes are the primes
    mpmath.mp.dps = 40
    p2 = mpmath.mpf(0)
    for kk in range(1, 120):
        mu = _mobius(kk)
        if mu:
            p2 += mpmath.mpf(mu) / kk * mpmath.log(mpmath.zeta(2 * kk))
    if abs(p2 - mpmath.mpf(P2_PRIME_ZETA)) > 1e-16:
        return False, f"S10 P(2) = {mpmath.nstr(p2, 20)} disagrees"
    nxt = primes_upto(1 << 21)
    nxt = nxt[nxt > (1 << 20)].astype(np.float64)
    part = math.fsum((1.0 / (nxt - 1.0) ** 2).tolist())
    tb = tail_bound(1 << 20)
    seg = np.concatenate(list(_odd_prime_chunks((1 << 22) + (1 << 20))))
    ref = primes_upto((1 << 22) + (1 << 20))[1:]
    if not (part < tb < 1.0 / (3.0 * ((1 << 20) - 8)) / 4
            and np.array_equal(seg, ref)):
        return False, (f"S10 tail bound {tb:.3e} against the next primes' "
                       f"{part:.3e}, or the segmented sieve disagrees")
    return True, (f"S10 deep tiers: k = 12763724651 and 12885017267 (C 1.3e-6 "
                  f"below the census floor; they cost the first v3 run ~7 "
                  f"minutes each in the analytic route) are settled below "
                  f"the floor by a prime tier in {worst:.2f}s at most; every "
                  f"tier to 2^28 contains C(247757) to 30 digits; the tail "
                  f"bound from P(2) (recomputed by Moebius inversion) is "
                  f"{1.0 / (3.0 * ((1 << 20) - 8)) / tb:.1f}x tighter than "
                  f"the old one at 2^20 and still covers the primes after it; "
                  f"the segmented sieve gives the primes")


GATES = [gate_s0, gate_s1, gate_s2, gate_s3, gate_s4, gate_s5, gate_s6,
         gate_s7, gate_s8, gate_s9, gate_s10]


def selftest():
    ok = True
    for g in GATES:
        t0 = time.time()
        try:
            good, msg = g()
        except Exception as e:                      # a gate must not crash
            good, msg = False, f"{g.__name__}: {type(e).__name__}: {e}"
        print(("PASS " if good else "FAIL ") + msg
              + f"  [{time.time() - t0:.1f}s]", flush=True)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown
    sys.exit(_shutdown.graceful(lambda: 0 if selftest() else 1))
