# hlc_reference.py -- THE ORACLE for A331940 (slow, literal, boring).
#
# A331940: "Addends k > 0 such that the polynomial x^2 + x + k produces a
# record of its Hardy-Littlewood Constant."
#
# The constant C of the entry's table is the Bateman-Horn / Conjecture F
# product over ALL primes p
#
#     C(k) = prod_p (1 - w(p)/p) / (1 - 1/p),
#
# w(p) the number of x mod p with x^2 + x + k == 0 (mod p).  For odd k the
# prime 2 has w = 0 and contributes the factor 2; for an odd prime p,
# w(p) = 1 + (D|p) with D = 1 - 4k (Legendre symbol; one root when p | D),
# so C(k) = 2 * prod_{p odd} (1 - (D|p)/(p-1)).  Even k has w(2) = 2 and
# C = 0.  The product converges only conditionally, so nothing here sums it
# literally for a decision; the oracle uses two classical facts instead:
#
#   (class number formula, Dirichlet)  for D < 0, D == 1 (mod 4),
#       prod_p (1 - (D|p)/p)^-1 = L(1, chi_D) = 2*pi*h(D) / (w * sqrt|D|),
#       h(D) the number of reduced PRIMITIVE forms (a, b, c) of discriminant
#       D = b^2 - 4ac, and w = 6 for D = -3, else 2 (D is odd here);
#
#   (the remaining product converges absolutely)
#       C(k) = 2w*sqrt(4k-1) / (3*pi*h(1-4k)) * E(k),
#       E(k) = prod_{p odd, p does not divide 4k-1} e_p,
#       e_p = 1 - 1/(p-1)^2 if (D|p) = +1,  1/(1 - 1/p^2) if (D|p) = -1,
#   and truncating E at P costs a factor inside [1 - T, 1/(1 - T)] with
#   T = 1/(3(P - 8)): every prime > 3 is +-1 (mod 6), so the sum of
#   1/(p-1)^2 over p > P is at most sum_{i >= P/6} 2/(6i-2)^2 <= T.
#
# h is counted by enumerating reduced forms from the definition; primes come
# from sympy; the Legendre symbol is Euler's criterion.  No optimization,
# and nothing here is called by, or calls, the engines.
#
# Gates:
#   G1  the literal single-discriminant count agrees with the bucketed
#       enumeration, and with the eleven h(1-4k) the table implies
#   G2  exhaustively over odd k <= 3*10^5 the records are exactly a(1)..a(11)
#       and every C matches the entry's table to its 5 decimals
#   G3  the literal partial product over p <= 2*10^4 (root counting, no
#       class number) agrees with G2's values to 2% -- the normalization

import math
import sys
import time

from sympy import primerange

SEQUENCE = "A331940"
FORMS = "x^2 + x + k"

# The entry's eleven terms with the table's C (5 decimals), frozen from the
# OEIS data (%S and %C lines, revision of Jan 25 2026).
KNOWN = [
    (1, "2.24147"), (11, "3.25944"), (17, "4.17466"), (41, "6.63955"),
    (21377, "6.92868"), (27941, "7.26400"), (41537, "7.32220"),
    (55661, "7.45791"), (115721, "7.70935"), (239621, "7.72932"),
    (247757, "8.24741"),
]
KNOWN_TERMS = [k for k, _ in KNOWN]
SEARCHED_ABOVE = 3 * 10**6      # "a(12) > 3*10^6" (Pfoertner, Jan 25 2026)
# Jacobson & Williams' k (A392688): C = 2*5.36708, so it bounds a(12) above.
JW_K = 3399714628553118047


def tail_bound(P):
    """T with prod_{p > P} e_p inside [1 - T, 1/(1 - T)] (header)."""
    return 1.0 / (3.0 * (P - 8))


def legendre(D, p):
    """(D|p) for an odd prime p by Euler's criterion."""
    r = pow(D % p, (p - 1) // 2, p)
    return 0 if r == 0 else (1 if r == 1 else -1)


def roots_mod(k, p):
    """w(p): the number of x mod p with x^2 + x + k == 0, by trying them."""
    return sum(1 for x in range(p) if (x * x + x + k) % p == 0)


def class_number_forms(D):
    """h(D): reduced primitive forms of discriminant D < 0, from the
    definition (-a < b <= a <= c, and b >= 0 when a = c)."""
    assert D < 0 and D % 4 in (0, 1)
    h = 0
    a = 1
    while 3 * a * a <= -D:
        for b in range(-a + 1, a + 1):
            if (b * b - D) % (4 * a):
                continue
            c = (b * b - D) // (4 * a)
            if c < a or (c == a and b < 0):
                continue
            if math.gcd(a, math.gcd(b, c)) == 1:
                h += 1
        a += 1
    return h


def class_numbers_upto(kmax):
    """{k: h(1-4k)} for every odd k <= kmax, by enumerating every reduced
    primitive form with b odd, a and c odd (4ac = b^2 - D == 4 mod 8 forces
    both odd when D == 5 mod 8) and bucketing it under its discriminant."""
    nmax = 4 * kmax - 1
    h = {}
    a = 1
    while 3 * a * a <= nmax:
        for b in range(2 - a, a + 1, 2):         # odd b with -a < b <= a
            bb = b * b
            c = a
            cmax = (nmax + bb) // (4 * a)
            while c <= cmax:
                if not (c == a and b < 0) and \
                        math.gcd(a, math.gcd(b, c)) == 1:
                    n = 4 * a * c - bb
                    h[n] = h.get(n, 0) + 1
                c += 2
        a += 2
    return {(n + 1) // 4: v for n, v in h.items()}


def E_truncated(k, P):
    """prod of e_p over odd primes p <= P (a float; ~1e-13 relative)."""
    D = 1 - 4 * k
    e = 1.0
    for p in primerange(3, P + 1):
        s = legendre(D, p)
        if s == 1:
            e *= 1.0 - 1.0 / ((p - 1) * (p - 1))
        elif s == -1:
            e /= 1.0 - 1.0 / (p * p)
    return e


def C_interval(k, h, P):
    """(lo, hi) containing C(k), from h = h(1-4k) and primes <= P."""
    if k % 2 == 0:
        return 0.0, 0.0
    n = 4 * k - 1
    w = 6 if n == 3 else 2
    mid = 2 * w * math.sqrt(n) * E_truncated(k, P) / (3 * math.pi * h)
    T = tail_bound(P) + 1e-11
    return mid * (1 - T), mid / (1 - T)


def same_constant(k1, k2):
    """True when C(k1) = C(k2) EXACTLY: the two discriminants differ by a
    square factor and have the same prime support, so (D|p) agrees at every
    prime (k = 7, D = -27, against k = 1, D = -3)."""
    n1, n2 = 4 * k1 - 1, 4 * k2 - 1
    r = math.isqrt(n1 * n2)
    if r * r != n1 * n2:
        return False
    g = math.gcd(n1, n2)
    for n in (n1, n2):
        m = n
        while True:
            t = math.gcd(m, g)
            if t == 1:
                break
            m //= t
        if m != 1:
            return False
    return True


def records(kmax, P0=47, verbose=None):
    """The records of C over 0 < k <= kmax: [(k, C_lo, C_hi, h)].

    Every odd k gets an interval from the primes <= P0; one that could
    reach the standing record is refined (P x 8 each time) until it is
    separated from it, above or below, or is an exact tie (same_constant).
    """
    hs = class_numbers_upto(kmax)
    out = []
    rec_k, rec_lo, rec_hi = None, 0.0, 0.0
    for k in range(1, kmax + 1, 2):
        h = hs[k]
        P = P0
        lo, hi = C_interval(k, h, P)
        while hi > rec_lo:
            if lo > rec_hi:
                out.append((k, lo, hi, h))
                rec_k, rec_lo, rec_hi = k, lo, hi
                break
            if rec_k is not None and same_constant(k, rec_k):
                break
            P *= 8
            if P > 2 * 10**7:
                raise RuntimeError(f"oracle cannot separate k = {k} from the "
                                   f"record at k = {rec_k}")
            lo, hi = C_interval(k, h, P)
            if rec_k is not None:
                rec_lo, rec_hi = (max(a, b) if i == 0 else min(a, b)
                                  for i, (a, b) in enumerate(zip(
                                      C_interval(rec_k, hs[rec_k], P),
                                      (rec_lo, rec_hi))))
        if verbose and k % verbose == 1:
            print(f"  oracle at k = {k}", flush=True)
    # tighten every record for reporting
    fin = []
    for k, lo, hi, h in out:
        lo, hi = C_interval(k, h, 2 * 10**6)
        fin.append((k, lo, hi, h))
    return fin


def literal_product(k, P):
    """prod_{p <= P} (1 - w(p)/p)/(1 - 1/p) with w(p) counted by trying
    every x: the definition, truncated.  Converges conditionally (error
    ~ 1/sqrt(P)); a normalization check, never a decision."""
    c = 1.0
    for p in primerange(2, P + 1):
        c *= (1.0 - roots_mod(k, p) / p) / (1.0 - 1.0 / p)
    return c


# ------------------------------------------------------------------ gates
def gate_g1():
    want = {1: 1, 11: 1, 17: 1, 41: 1, 21377: 22, 27941: 24, 41537: 29,
            55661: 33, 115721: 46, 239621: 66, 247757: 63}
    hs = class_numbers_upto(3000)
    for k in list(range(1, 400, 2)) + [1001, 2999]:
        if hs[k] != class_number_forms(1 - 4 * k):
            return False, f"G1 bucketed h({1 - 4 * k}) != literal count"
    for k in (21377, 55661):
        if class_number_forms(1 - 4 * k) != want[k]:
            return False, f"G1 literal h(1-4*{k}) != {want[k]}"
    if not (same_constant(7, 1) and not same_constant(11, 1)
            and same_constant(1082687, 41)):
        return False, "G1 exact-tie rule wrong"
    return True, ("G1 literal reduced-form count = bucketed enumeration on "
                  "202 discriminants; h(-85507) = 22, h(-222643) = 33; "
                  "exact ties recognised (k = 7 against k = 1)")


def gate_g2(kmax=300000):
    t0 = time.time()
    recs = records(kmax)
    ks = [r[0] for r in recs]
    if ks != KNOWN_TERMS:
        return False, f"G2 oracle records {ks} != the entry's {KNOWN_TERMS}"
    for (k, lo, hi, h), (_, cs) in zip(recs, KNOWN):
        c = float(cs)
        if not (lo - 0.5000001e-5 <= c <= hi + 0.5000001e-5):
            return False, (f"G2 C({k}) in [{lo:.7f}, {hi:.7f}] does not round "
                           f"to the table's {cs}")
    return True, (f"G2 exhaustive over odd k <= {kmax}: the records are "
                  f"exactly a(1)..a(11) and all eleven C match the table to "
                  f"5 decimals ({time.time() - t0:.0f}s)")


def gate_g3():
    worst = 0.0
    hs = class_numbers_upto(41)
    for k in (1, 11, 17, 41):
        lo, hi = C_interval(k, hs[k], 10**5)
        lit = literal_product(k, 20000)
        worst = max(worst, abs(lit / lo - 1))
    if literal_product(6, 100) != 0.0:
        return False, "G3 even k should give C = 0"
    if worst > 0.02:
        return False, f"G3 literal product off by {worst:.3%}"
    return True, (f"G3 root-counting product over p <= 20000 within "
                  f"{worst:.2%} of the class-number evaluation at k = 1, 11, "
                  f"17, 41; even k gives 0")


GATES = [gate_g1, gate_g2, gate_g3]


def selftest():
    ok = True
    for g in GATES:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg, flush=True)
        ok = ok and good
    return ok


if __name__ == "__main__":
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown
    sys.exit(_shutdown.graceful(lambda: 0 if selftest() else 1))
