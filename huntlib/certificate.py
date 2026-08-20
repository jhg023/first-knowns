"""Primality CERTIFICATES -- proof, where a strong test is only evidence.

`huntlib.primes.mr_is_prime` is DETERMINISTIC below 3.317e24, and inside
that range a positive is a proof.  Above it the same call is a strong
probable prime chain: excellent evidence, and not a proof.  A hunt that
records a FIRST OCCURRENCE whose values pass that bound therefore owes the
reader an actual certificate, and this module is where the two classical
N-1 tests live so that no project writes its own.

Both are Brillhart-Lehmer-Selfridge (Math. Comp. 29 (1975)), and both rest
on the same lemma:

  THEOREM 1 (Pocklington, in BLS form).  Let N - 1 = F * R with F
  completely factored.  If for every prime p | F there is a witness a_p
  with

        a_p^(N-1) == 1 (mod N)   and   gcd(a_p^((N-1)/p) - 1, N) == 1,

  then every prime divisor q of N satisfies q == 1 (mod F).

With F > sqrt(N) that is already a primality proof: two factors both
exceeding F would multiply past N.  `theorem1` is that case, and it is the
lucky one -- it needs N-1 factored past its square root.

  THEOREM 5.  Same hypotheses, but only F > N^(1/3), with F EVEN and
  gcd(F, R) = 1 (so R is odd).  Write R = 2*F*s + r with 1 <= r < 2F.
  Then N is prime if and only if s = 0 or r^2 - 8s is not a perfect
  square.

The proof of the hard direction is short enough to state, because a
certificate nobody can follow is not much of a certificate.  F > N^(1/3)
leaves N at most two prime factors, so a composite N is (1 + aF)(1 + bF)
with a, b >= 1; expanding, R = (a + b) + abF.  F even and gcd(F, R) = 1
force R odd, hence a + b odd, hence ab even.  So R = (a+b) + 2F*(ab/2)
with a + b <= ab + 1 <= F < 2F, which is exactly the division above with
r = a + b and s = ab/2 -- and then r^2 - 8s = (a+b)^2 - 4ab = (a-b)^2 is a
perfect square.  Contrapositive: no perfect square, no factorization.

Why the second theorem earns its keep: N-1 for an arbitrary prime has no
structure at all, so factoring it past sqrt(N) is luck, while factoring it
past N^(1/3) is routine -- for a 26-digit value that is a factored part
above ~5e8, which trial division and a bounded rho usually hand over
without ECM being asked.  A project whose values are its OWN numbers
(dickson-ladders: N - 1 = m*k^2, both factors known) never needs it; a
project sieving for primes in a progression (primorial-ap: N - 1 =
p - 1 + j*P(n), structureless) needs it from its fourth open term on.

RIGOUR NOTE.  Every prime claimed in F must itself be PROVED prime.  Below
MR_VALID_BELOW that is `mr_is_prime` and nothing more is needed.  Above it
a factor is admitted only with a SUBPROOF of its own -- the same routine,
one level down, carried in the certificate and re-checked by `verify` --
so a proof is a finite tree whose every leaf is a deterministic
Miller-Rabin.  A cofactor that BPSW merely calls prime is never admitted
on that say-so: "probably prime" is not what a certificate is for.

The recursion is what makes the module usable rather than lucky.  Measured
on primes near 1e26: N-1 factors completely into deterministic-MR primes
about 9 times in 10, and almost every remaining case is a single large
prime cofactor -- exactly the case one level of recursion settles.  The
depth is bounded (PROOF_DEPTH) like everything else in a verification
path, and running out of it is reported, never guessed around.

BOUNDEDNESS (CONVENTIONS.md).  Nothing in a verification path may run
unbounded.  `factor_partial` is trial division to a cap, then a bounded
Brent rho, then a bounded number of ECM curves, and then it gives up and
says so.  It never hands a possibly-hard semiprime to a full factorization
routine and waits.
"""

import random
from math import gcd, isqrt

from sympy import isprime as _isprime, primerange
from sympy.ntheory import ecm as _ecm

from .primes import MR_VALID_BELOW, mr_is_prime

CERT_BASE_CAP = 10_000        # witness bases: the primes below this, ascending
TDIV_TO = 1 << 17             # factor_partial: trial division bound
RHO_ITERS = 60_000            # factor_partial: iterations per Brent rho try
RHO_TRIES = 3
ECM_CURVES = 24               # factor_partial: bounded ECM, or give up
SPLIT_BUDGET = 8              # factor_partial: total splits attempted
PROOF_DEPTH = 3               # levels of subproof for large prime factors

_TDIV = None                  # the trial-division primes, built once


def _tdiv_primes():
    global _TDIV
    if _TDIV is None:
        _TDIV = list(primerange(2, TDIV_TO))
    return _TDIV


# ------------------------------- witnesses ---------------------------------

def witnesses(N, primes_of_F, base_cap=CERT_BASE_CAP):
    """{p: a_p} satisfying the BLS conditions for every prime p | F, or None.

    Different p may use different witnesses, which is what makes this
    practical: one universal base fails whenever it happens to be a p-th
    power residue, and with six prime factors that is most of the time.
    The bases are the primes in ascending order, as many as it takes -- a
    FIXED list is a trap, and it sprang once: a hunt whose candidates are
    all multiples of a wheel makes every wheel prime a quadratic residue of
    N by reciprocity, so the first eleven primes left only five or six coin
    flips at p = 2 and ran out on a genuine value mid-campaign.

    A None return is not always a failure of the search: if the Fermat
    condition itself fails, N is COMPOSITE and no certificate exists.
    """
    out = {}
    for p in primes_of_F:
        for a in primerange(2, base_cap):
            if pow(a, N - 1, N) != 1:
                return None          # Fermat fails: N is composite outright
            if gcd(pow(a, (N - 1) // int(p), N) - 1, N) == 1:
                out[int(p)] = int(a)
                break
        else:
            return None
    return out


# ------------------------------- factoring ----------------------------------

def _proved(v):
    """True iff v is a prime this module is allowed to put inside F."""
    return 1 < v < MR_VALID_BELOW and mr_is_prime(v)


def _rho(m, iters=RHO_ITERS, tries=RHO_TRIES):
    """A nontrivial factor of composite m, or None.  Bounded, deliberately.

    Seeded from m rather than from the clock so that a verification is
    REPRODUCIBLE: an evidence file that cannot be regenerated is a weaker
    claim than one that can.
    """
    rng = random.Random(m & 0xFFFFFFFF)
    for _ in range(tries):
        y = rng.randrange(1, m)
        c = rng.randrange(1, m)
        x, fac = y, 1
        for _ in range(iters):
            x = (x * x + c) % m
            y = (y * y + c) % m
            y = (y * y + c) % m
            fac = gcd(abs(x - y), m)
            if fac != 1:
                break
        if 1 < fac < m:
            return fac
    return None


def _split(v, ecm_curves):
    """One bounded attempt to split composite v: rho, then ECM."""
    f = _rho(v)
    if f is None and ecm_curves:
        try:
            found = _ecm(v, max_curve=ecm_curves)
            f = min(found) if found else None
        except Exception:            # ECM declining to split is not an error
            f = None
    return f if (f is not None and 1 < f < v) else None


def factor_partial(m, ecm_curves=ECM_CURVES, budget=SPLIT_BUDGET):
    """(fac, R): a COMPLETE factorization of F = m // R into PROVED primes,
    with gcd(F, R) == 1, and R whatever this bounded effort could not split.

    R == 1 means m factored completely; R > 1 means it did not, and the
    caller decides whether the F it got is big enough for the theorem it
    wants.  Saying so is the point: an unbounded factorization inside a
    verification path is exactly what CONVENTIONS.md forbids.
    """
    fac, rest = {}, int(m)
    for q in _tdiv_primes():
        if q * q > rest:
            break
        if rest % q == 0:
            e = 0
            while rest % q == 0:
                rest //= q
                e += 1
            fac[q] = fac.get(q, 0) + e
    R = 1
    pending = [rest] if rest > 1 else []
    while pending:
        v = pending.pop()
        if v == 1:
            continue
        if _proved(v):
            fac[int(v)] = fac.get(int(v), 0) + 1
            continue
        if budget <= 0:
            R *= v
            continue
        budget -= 1
        f = _split(v, ecm_curves)
        if f is None:
            R *= v                   # unfactored, and it stays unfactored
            continue
        pending.append(f)
        pending.append(v // f)
    # A repeated prime split across two branches would break gcd(F, R) = 1;
    # pull any shared factor back out of F so the invariant is structural
    # rather than hoped for.
    for p in list(fac):
        while R % p == 0:
            R //= p
            fac[p] += 1
    return fac, R


# -------------------------------- the tests ---------------------------------

def theorem1(N, fac, base_cap=CERT_BASE_CAP):
    """BLS75 Theorem 1 with N-1 FULLY factored: the witnesses, or None.

    Kept as its own entry point because a project that owns its N-1 (a
    value built as m*k^2, say) has the factorization already and should not
    pay factor_partial to rediscover it.
    """
    return witnesses(N, sorted(fac), base_cap)


def theorem1_verify(N, fac, wit):
    """Re-check a Theorem 1 certificate given as (N, factorization, witnesses).

    The shape a project has when N-1 is its OWN construction and is
    therefore factored completely -- dickson-ladders' N - 1 = m*k^2, with m
    tiny and k no larger than its ceiling.  Same checks as `verify`, which
    is what it calls: the factorization must multiply to exactly N-1, every
    claimed factor must be a certified prime, and every witness must satisfy
    both BLS conditions.
    """
    return verify({"proof": "bls75-thm1", "N": int(N),
                   "factors": {str(int(p)): int(e) for p, e in fac.items()},
                   "witnesses": {str(int(p)): int(a) for p, a in wit.items()}})


def theorem5_split(F, R):
    """(s, r) with R = 2*F*s + r and 1 <= r < 2F."""
    s, r = divmod(int(R), 2 * int(F))
    return int(s), int(r)


def _is_square(x):
    if x < 0:
        return False
    r = isqrt(x)
    return r * r == x


def prove(N, fac=None, base_cap=CERT_BASE_CAP, depth=PROOF_DEPTH, **kw):
    """A checkable primality PROOF for N, or None if this cannot prove it.

    Returns a JSON-safe dict; `verify` re-checks it from scratch and is what
    a gate -- and a reader with a calculator -- runs.  The routes, in the
    order they are tried:

      {"proof": "deterministic-mr"}   N < 3.317e24: mr_is_prime IS a proof,
                                      and no certificate adds anything to it
      {"proof": "bls75-thm1", ...}    N-1 factored past sqrt(N)
      {"proof": "bls75-thm5", ...}    N-1 factored past N^(1/3)

    Pass `fac` when the caller already knows a factorization of N-1 (it is
    checked, never trusted); otherwise factor_partial does what it can
    inside its bounds.  A None return means "not proved HERE" -- it is not
    a claim that N is composite, except where noted below.
    """
    N = int(N)
    if N < 2:
        return None
    if N < MR_VALID_BELOW:
        if not mr_is_prime(N):
            return None
        return {"proof": "deterministic-mr", "N": N, "bound": MR_VALID_BELOW,
                "note": "7-base Miller-Rabin is deterministic below the bound"}
    if N % 2 == 0:
        return None
    if fac is None:
        fac, R = factor_partial(N - 1, **kw)
    else:
        fac = {int(p): int(e) for p, e in fac.items()}
        prod = 1
        for p, e in fac.items():
            prod *= p ** e
        if prod < 1 or (N - 1) % prod:
            return None
        R = (N - 1) // prod
    # A large prime cofactor is the usual reason F comes out too small, and
    # it is the one case a single level of recursion settles: prove it, carry
    # the subproof, and it becomes an admissible factor like any other.
    subs = {}
    if R > 1 and depth > 0 and R >= MR_VALID_BELOW and _isprime(R):
        sub = prove(R, base_cap=base_cap, depth=depth - 1, **kw)
        if sub is not None:
            fac[int(R)] = fac.get(int(R), 0) + 1
            subs[str(int(R))] = sub
            R = 1
    F = 1
    for p, e in fac.items():
        if not (_proved(p) or str(p) in subs):
            return None
        F *= p ** e
    if F % 2 or gcd(F, R) != 1:        # Theorem 5 needs F even and R coprime
        return None
    w = witnesses(N, sorted(fac), base_cap)
    if w is None:
        return None
    out = {"N": N, "F": F, "R": R,
           "factors": {str(p): e for p, e in sorted(fac.items())},
           "witnesses": {str(p): a for p, a in sorted(w.items())}}
    if subs:
        out["subproofs"] = subs
    if F > isqrt(N):
        out["proof"] = "bls75-thm1"
        return out
    if F ** 3 > N:
        s, r = theorem5_split(F, R)
        if s != 0 and _is_square(r * r - 8 * s):
            return None                # the theorem is an IFF: N is composite
        out["proof"] = "bls75-thm5"
        out["s"], out["r"] = s, r
        return out
    return None                        # F too small: the caller escalates


def verify(proof):
    """Re-check a proof from scratch: (ok, message).

    This is the function a gate drills and the one a reader would write.  It
    trusts NOTHING in the dict -- not the factorization, not that the
    claimed factors are prime, not the witnesses, not the arithmetic of the
    theorem's side condition, not even that F divides N-1.
    """
    if not isinstance(proof, dict):
        return False, "not a proof object"
    kind, N = proof.get("proof"), int(proof.get("N", 0))
    if N < 2:
        return False, "no N"
    if kind == "deterministic-mr":
        if N >= MR_VALID_BELOW:
            return False, (f"N = {N} is not below the deterministic bound "
                           f"{MR_VALID_BELOW}; this is not a proof")
        if not mr_is_prime(N):
            return False, "N fails deterministic Miller-Rabin"
        return True, "deterministic 7-base Miller-Rabin below 3.317e24"
    if kind not in ("bls75-thm1", "bls75-thm5"):
        return False, f"unknown proof kind {kind!r}"
    fac = {int(p): int(e) for p, e in proof.get("factors", {}).items()}
    if not fac:
        return False, "no factorization of N-1"
    subs = proof.get("subproofs", {}) or {}
    F = 1
    for p, e in sorted(fac.items()):
        if e < 1:
            return False, f"bad exponent {e} for {p}"
        if not _proved(p):
            sub = subs.get(str(p), subs.get(p))
            if sub is None:
                return False, (f"claimed factor {p} is past the deterministic "
                               f"bound and carries no subproof")
            if int(sub.get("N", 0)) != p:
                return False, f"subproof for {p} is about {sub.get('N')}"
            ok, why = verify(sub)
            if not ok:
                return False, f"subproof for factor {p} fails: {why}"
        F *= p ** e
    if (N - 1) % F:
        return False, "F does not divide N-1"
    R = (N - 1) // F
    if F % 2:
        return False, "F must be even"
    if gcd(F, R) != 1:
        return False, f"gcd(F, R) = {gcd(F, R)} != 1"
    wit = proof.get("witnesses", {})
    for p in sorted(fac):
        a = wit.get(str(p), wit.get(p))
        if a is None:
            return False, f"no witness for {p}"
        if pow(int(a), N - 1, N) != 1:
            return False, f"witness {a} fails Fermat at p = {p}"
        if gcd(pow(int(a), (N - 1) // p, N) - 1, N) != 1:
            return False, f"witness {a} fails the gcd condition at p = {p}"
    if kind == "bls75-thm1":
        if F <= isqrt(N):
            return False, (f"F = {F} does not exceed sqrt(N); Theorem 1 shows "
                           f"only that every prime factor is 1 mod F")
        return True, f"BLS75 Theorem 1: F > sqrt(N), so N is prime"
    if F ** 3 <= N:
        return False, (f"F = {F} does not exceed N^(1/3); Theorem 5 does not "
                       f"apply")
    s, r = theorem5_split(F, R)
    if s != int(proof.get("s", -1)) or r != int(proof.get("r", -1)):
        return False, (f"stated (s, r) = ({proof.get('s')}, {proof.get('r')}) "
                       f"but R = 2Fs + r gives ({s}, {r})")
    if s != 0 and _is_square(r * r - 8 * s):
        return False, (f"r^2 - 8s = {r * r - 8 * s} IS a perfect square: "
                       f"Theorem 5 says N is COMPOSITE")
    why = "s = 0" if s == 0 else f"r^2 - 8s = {r * r - 8 * s} is not a square"
    return True, f"BLS75 Theorem 5: F > N^(1/3) and {why}, so N is prime"


# ---------------------------------- gate ------------------------------------

# Fixed samples for the gate.  F is smooth and even; the two N built on it
# are a PRIME and a COMPOSITE that both sit in the Theorem 5 range
# (N^(1/3) < F <= sqrt(N)), so the gate exercises the theorem's arithmetic
# in both directions instead of hoping factor_partial stops in the right
# place on some arbitrary prime.
_F5 = 2**5 * 3**3 * 5**2 * 7 * 11 * 13 * 17 * 19 * 23        # 160626866400
_F5_FAC = {2: 5, 3: 3, 5: 2, 7: 1, 11: 1, 13: 1, 17: 1, 19: 1, 23: 1}
_N5_PRIME = 12131403568136753874573601                       # = _F5 * R + 1
_N5_AB = (4, 33)                                             # composite control


def gate_certificates():
    """Both theorems prove primes, reject composites, and refuse a small F.

    Drilled here rather than in a project because the mathematics belongs to
    this file: a project's own gates should be about ITS values, not about
    whether Pocklington was transcribed correctly.
    """
    # Below the deterministic bound there is nothing to certify and the
    # answer says so; a composite gets no proof at all.
    small = prove(122774401)                          # 2^7*3^3*5^2*7^2*29 + 1
    if small is None or small.get("proof") != "deterministic-mr":
        return False, f"a prime below the MR bound took the wrong route: {small}"
    if not verify(small)[0] or prove(122774403) is not None:
        return False, "the deterministic-MR route mishandles a small prime pair"
    if verify(dict(small, N=10**30 + 57))[0]:
        return False, "a deterministic-MR claim ABOVE the bound verified"

    # Theorem 1 route: N-1 smooth and completely factored, past sqrt(N),
    # on an N the deterministic test cannot reach.
    n1 = 2 * 3**2 * 5**18 * 7**14 + 1
    p1 = prove(n1, fac={2: 1, 3: 2, 5: 18, 7: 14})
    if p1 is None or p1.get("proof") != "bls75-thm1":
        return False, f"Theorem 1 route not taken for {n1}: {p1}"
    if n1 < MR_VALID_BELOW:
        return False, "the Theorem 1 sample is below the deterministic bound"
    ok, msg = verify(p1)
    if not ok:
        return False, f"Theorem 1 proof of {n1} does not verify: {msg}"

    # Theorem 5 route: past the deterministic bound, with only the smooth
    # part of N-1 offered -- the situation a hunt in an arithmetic
    # progression is actually in.
    n5 = _N5_PRIME
    if n5 < MR_VALID_BELOW:
        return False, "the Theorem 5 sample is below the deterministic bound"
    p5 = prove(n5, fac=dict(_F5_FAC))
    if p5 is None or p5.get("proof") != "bls75-thm5":
        return False, f"Theorem 5 route not taken for {n5}: {p5}"
    if not (_F5**3 > n5 and _F5 <= isqrt(n5)):
        return False, "the Theorem 5 sample is not in the Theorem 5 range"
    ok, msg = verify(p5)
    if not ok:
        return False, f"Theorem 5 proof of {n5} does not verify: {msg}"

    # The IFF, from the composite side: for N = (1 + aF)(1 + bF) the split
    # must reproduce r = a + b and s = ab/2, so that r^2 - 8s = (a - b)^2 is
    # the perfect square the theorem says condemns N.  This is the half that
    # cannot be drilled with a real composite (it fails Fermat long before),
    # so it is drilled as the algebra it is.
    a, b = _N5_AB
    nc = (1 + a * _F5) * (1 + b * _F5)
    if nc < MR_VALID_BELOW or _F5**3 <= nc or _F5 > isqrt(nc):
        return False, "the composite control is not in the Theorem 5 range"
    s, r = theorem5_split(_F5, (nc - 1) // _F5)
    if (r, s) != (a + b, a * b // 2):
        return False, (f"Theorem 5 split gave (s, r) = ({s}, {r}); the "
                       f"algebra says ({a * b // 2}, {a + b})")
    if not _is_square(r * r - 8 * s) or isqrt(r * r - 8 * s) != b - a:
        return False, "r^2 - 8s is not (b - a)^2 on a constructed composite"
    if prove(nc, fac=dict(_F5_FAC)) is not None:
        return False, f"produced a proof for the composite {nc}"

    # Doctored proofs must not verify.
    for name, bad in (("a tampered (s, r)", dict(p5, s=int(p5["s"]) + 1)),
                      ("a truncated factorization",
                       dict(p5, factors=dict(list(p5["factors"].items())[:1]))),
                      ("a mislabelled theorem", dict(p5, proof="bls75-thm1"))):
        if verify(bad)[0]:
            return False, f"{name} verified"

    # And the recursion: a prime past the bound whose N-1 carries a large
    # prime cofactor is proved only WITH a subproof, and stripping the
    # subproof must invalidate it.
    nr = None
    for cand in _RECUR_SAMPLES:
        p = prove(cand)
        if p is not None and p.get("subproofs"):
            nr, pr = cand, p
            break
    if nr is None:
        return False, "no sample exercised the subproof recursion"
    if not verify(pr)[0]:
        return False, f"recursive proof of {nr} does not verify"
    if verify({k: v for k, v in pr.items() if k != "subproofs"})[0]:
        return False, "a proof stripped of its subproofs still verified"
    return True, ("certificates ok: BLS75 Theorem 1, Theorem 5 and the "
                  "subproof recursion all prove and all verify; the "
                  "constructed composite, a tampered (s, r), a truncated "
                  "factorization, a mislabelled theorem and a stripped "
                  "subproof are all rejected (thm5 F^3/N = %.3g, recursion "
                  "sample %d)" % (_F5**3 / n5, nr))


# Primes past the deterministic bound whose N-1 has a large prime cofactor,
# for the recursion half of the gate.  Several, because which of them needs
# a subproof depends on how far factor_partial gets; the gate takes the
# first that does.
_RECUR_SAMPLES = (10**25 + 1237, 10**25 + 1291, 10**25 + 1417,
                  10**25 + 1447, 10**25 + 1483, 10**25 + 1531,
                  10**25 + 1567, 10**25 + 1621, 10**25 + 1747,
                  10**25 + 1801, 10**25 + 1879, 10**25 + 1951)

GATES = [gate_certificates]
