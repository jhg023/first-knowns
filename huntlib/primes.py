"""Primality and factoring utilities shared by every hunt.

Nothing here is probabilistic hand-waving: the Miller-Rabin base set
(2, 325, 9375, 28178, 450775, 9780504, 1795265022) is DETERMINISTIC for
all n < 3.317e24 (Sorenson & Webster, "Strong pseudoprimes to twelve prime
bases", Math. Comp. 86 (2017); the 7-base bound). Engines that test values
anywhere near that bound must say so in their gates.

House verification rule: this module is one leg of any discovery's
three-way check; sympy's independent BPSW implementation is another; the
third is project-specific (typically an alternate-alignment re-sieve).
"""

import math
import random

MR_BASES = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
MR_VALID_BELOW = 3_317_044_064_679_887_385_961_981   # 3.317e24

_SMALL = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def mr_is_prime(m):
    """Deterministic Miller-Rabin for 0 <= m < 3.317e24 (python ints)."""
    if m < 2:
        return False
    for sp in _SMALL:
        if m % sp == 0:
            return m == sp
    d, s = m - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in MR_BASES:
        a %= m
        if a == 0:
            continue
        x = pow(a, d, m)
        if x == 1 or x == m - 1:
            continue
        for _ in range(s - 1):
            x = x * x % m
            if x == m - 1:
                break
        else:
            return False
    return True


RHO_ITERS = 200_000        # bounded Brent rho: finds factors to ~1e10 fast


def factor_witness(m):
    """A nontrivial factor of composite m: trial division to 1e6, then a
    BOUNDED Brent rho, then sympy's factorint (ECM) for whatever is left.

    Used to make every 'this value is composite' claim in an evidence file
    independently checkable with one multiplication.  Bounded because an
    unbounded rho on a run breaker that happens to be a semiprime with a
    16-digit smallest factor took 105 s inside a live campaign (rho needs
    ~sqrt(p) steps; ECM does not), and a verification step must never
    stall the hunt for minutes.
    """
    for q in _SMALL + (41, 43, 47):
        if m % q == 0 and m != q:
            return q
    d = 41
    while d * d <= m and d < 10**6:
        if m % d == 0:
            return d
        d += 2
    if d * d > m:
        return 1                                # m is prime (or 1)
    for _ in range(4):                          # Pollard rho, Brent variant
        y, cadd, fac = random.randrange(1, m), random.randrange(1, m), 1
        x = y
        for _ in range(RHO_ITERS):
            x = (x * x + cadd) % m
            y = (y * y + cadd) % m
            y = (y * y + cadd) % m
            fac = math.gcd(abs(x - y), m)
            if fac != 1:
                break
        if 1 < fac < m:
            return fac
    from sympy import factorint                 # ECM et al.: seconds, not minutes
    fac = factorint(m)
    smallest = min(fac)
    return smallest if smallest < m else 1
