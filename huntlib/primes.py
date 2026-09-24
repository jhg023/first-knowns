"""Primality and factoring utilities shared by every hunt.

Nothing here is probabilistic hand-waving, and a base set is only as good as
the bound PROVED FOR THAT SET, so there are two and the test dispatches:

  n < 2^64      the seven bases (2, 325, 9375, 28178, 450775, 9780504,
                1795265022): J. Sinclair's set, deterministic below 2^64 by
                exhaustive check against Feitsma's enumeration of the base-2
                pseudoprimes to 2^64.  NOTHING is proved for it past 2^64.
  n < 3.317e24  the first thirteen primes (2 .. 41): psi_13 =
                3317044064679887385961981 is the least composite that is a
                strong pseudoprime to all thirteen (Sorenson & Webster,
                "Strong pseudoprimes to twelve prime bases", Math. Comp. 86
                (2017), which computes psi_12 and psi_13).

Until 2026-09-20 this module ran the SEVEN bases to the THIRTEEN-base bound
and called it deterministic: two true theorems, glued at the wrong joint.
Every evidence value in the gap [2^64, 3.317e24) was re-tested that day with
the thirteen prime bases (734 claims, every project's evidence/, no
disagreement with the seven-base verdict on any integer in the files), so
no published term moved -- but the label was unearned until this dispatch.
Engines that test values anywhere near the bound must say so in their gates.

House verification rule: this module is one leg of any discovery's
three-way check; sympy's independent BPSW implementation is another; the
third is project-specific (typically an alternate-alignment re-sieve).
"""

import math
import random

MR_BASES_U64 = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
MR_U64_BELOW = 1 << 64                 # all the seven-base set is proved for
MR_BASES_13 = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)
MR_VALID_BELOW = 3_317_044_064_679_887_385_961_981   # psi_13, 3.317e24

_SMALL = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def mr_bases(m):
    """The base set whose PROVED bound covers m.  Past MR_VALID_BELOW neither
    is a proof; the thirteen primes are what a caller gets there, as a strong
    probable-prime chain and nothing more."""
    return MR_BASES_U64 if m < MR_U64_BELOW else MR_BASES_13


def mr_is_prime(m):
    """Deterministic Miller-Rabin for 0 <= m < 3.317e24 (python ints): the
    seven bases below 2^64, the first thirteen primes from there up."""
    if m < 2:
        return False
    for sp in _SMALL:
        if m % sp == 0:
            return m == sp
    d, s = m - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in mr_bases(m):
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


PSI_12 = 318_665_857_834_031_151_167_461        # = 399165290221 * 798330580441


def gate_bases():
    """The base set in force at m is the one whose PROVED bound covers m.

    Tripwires, all composites with a known factorization: psi_12 is a strong
    pseudoprime to the first TWELVE primes, so only base 41 stands between it
    and a false proof -- a dispatch that dropped a base, or ran the seven-base
    set past 2^64, is what this catches.  psi_13 = MR_VALID_BELOW passes all
    thirteen: the bound is sharp, and `N < MR_VALID_BELOW` is the only thing
    that keeps it out, so callers must test the bound and not just the chain.
    """
    if mr_bases(MR_U64_BELOW - 1) is not MR_BASES_U64:
        return False, "the seven-base set is not in force just below 2^64"
    if mr_bases(MR_U64_BELOW) is not MR_BASES_13:
        return False, ("the seven-base set is in force at 2^64, where nothing "
                       "is proved for it")
    if MR_BASES_13 != tuple(q for q in range(2, 42)
                            if all(q % d for d in range(2, q))):
        return False, "MR_BASES_13 is not the first thirteen primes"
    if PSI_12 != 399165290221 * 798330580441 or mr_is_prime(PSI_12):
        return False, "psi_12 (composite, spsp to twelve prime bases) passed"
    if MR_VALID_BELOW != 1287836182261 * 2575672364521:
        return False, "MR_VALID_BELOW is not psi_13"
    if not mr_is_prime(MR_VALID_BELOW):
        return False, ("psi_13 no longer passes the chain: the bases moved, "
                       "and the bound with them")
    if not (mr_is_prime(MR_U64_BELOW - 59) and mr_is_prime(MR_U64_BELOW + 13)
            and not mr_is_prime(MR_U64_BELOW - 57)
            and not mr_is_prime(MR_U64_BELOW + 15)):
        return False, "the primes either side of 2^64 are misjudged"
    return True, ("bases ok: seven below 2^64, thirteen primes to psi_13; "
                  "psi_12 rejected, psi_13 sharp")


def sprp_base2(m):
    """Strong probable prime test to base 2 alone.  False is a PROOF.

    Half of a Miller-Rabin round, and the half that carries all the weight:
    a composite fails a strong test to base 2 with probability > 3/4, and a
    FAILURE IS A PROOF OF COMPOSITENESS -- there is nothing probabilistic
    about a negative.  Only a positive is evidence rather than proof.

    That asymmetry is what makes this worth having next to mr_is_prime.  A
    hunt that wants to know "is this run shorter than the shortest run I
    would ever record" can answer it rigorously at one modular
    exponentiation instead of seven or thirteen, because the answer it needs
    is the negative one.  See launch.py's sprp_run in dickson-ladders.
    """
    if m < 2:
        return False
    for sp in _SMALL:
        if m % sp == 0:
            return m == sp
    d, s = m - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    x = pow(2, d, m)
    if x == 1 or x == m - 1:
        return True
    for _ in range(s - 1):
        x = x * x % m
        if x == m - 1:
            return True
    return False


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
