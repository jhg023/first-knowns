"""Primality CERTIFICATES -- proof, where a strong test is only evidence.

`huntlib.primes.mr_is_prime` is DETERMINISTIC below 3.317e24, and inside
that range a positive is a proof.  Above it the same call is a strong
probable prime chain: excellent evidence, and not a proof.  A hunt that
records a FIRST OCCURRENCE whose values pass that bound therefore owes the
reader an actual certificate, and this module is where the classical N-1
tests and the N+1 test live so that no project writes its own.

All are Brillhart-Lehmer-Selfridge (Math. Comp. 29 (1975)).  The two N-1
tests rest on the same lemma:

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

  THE N+1 TEST (BLS75 Theorem 15, the N+1 analogue of Theorem 1).  Let
  N + 1 = F * R with F completely factored and gcd(F, R) = 1, N odd.  Fix
  a discriminant D with Jacobi symbol (D/N) = -1, and for every prime
  q | F a Lucas sequence U_k(P_q, Q_q) with P_q^2 - 4 Q_q = D and
  gcd(Q_q, N) = 1 such that

        N | U_{N+1}(P_q, Q_q)   and   gcd(U_{(N+1)/q}(P_q, Q_q), N) = 1.

  Then every prime divisor p of N satisfies p == (D/p) == +-1 (mod F), so
  p >= F - 1, and N is prime as soon as (F - 1)^2 > N.

  Why it holds: for a prime p not dividing 2 Q D, p | U_{p - (D/p)}, so the
  rank of apparition w(p) of p in the sequence divides p - (D/p).  The two
  conditions say w(p) | N + 1 and w(p) does not divide (N+1)/q, so the full
  power of q in N + 1 divides w(p), hence divides p - (D/p).  Over every
  q | F that gives F | p - (D/p).  The sequences may differ per q, but they
  MUST share the discriminant: (D/p) is what fixes the sign, and two
  sequences with different D would let it differ from one q to the next,
  leaving only p == +-1 modulo each prime power separately -- which is not
  p == +-1 (mod F).  That is why the certificate carries ONE D and a (P, Q)
  per q, and why `verify` checks every pair against the same D.

  N | U_{N+1} failing for a pair with gcd(Q, N) = 1 is a proof that N is
  COMPOSITE (for a prime N with (D/N) = -1 it cannot fail), exactly as a
  failed Fermat condition is on the N-1 side.

Why the N+1 route earns its keep: a hunt whose values are m*k - 1 has
N + 1 = m*k completely factored once k is, so the N-1 tests -- which would
need m*k - 2 factored, a structureless number -- are the wrong side, and
without this route such a family is stuck at the deterministic bound.
linear-ladders' four -1 families and prime-ladders' A084701 are that case.

RIGOUR NOTE.  Every prime claimed in F must itself be PROVED prime.  Below
MR_VALID_BELOW that is `mr_is_prime` and nothing more is needed.  Above it
a factor is admitted only with a SUBPROOF of its own -- the same routine,
one level down, carried in the certificate and re-checked by `verify` --
so a proof is a finite tree whose every leaf is a deterministic
Miller-Rabin.  A cofactor that BPSW merely calls prime is never admitted
on that say-so: "probably prime" is not what a certificate is for.  The
subproof takes whichever side factors (N-1 first, then N+1), so a prime
factor of k above the bound is proved by the same machinery as N itself.

The recursion is what makes the module usable rather than lucky.  Measured
on primes near 1e26: N-1 factors completely into deterministic-MR primes
about 9 times in 10, and almost every remaining case is a single large
prime cofactor -- exactly the case one level of recursion settles.  The
depth is bounded (PROOF_DEPTH) like everything else in a verification
path, and running out of it is reported, never guessed around.

THE CEILING THIS SETS.  With both sides available and the recursion, what
bounds a hunt's k is no longer the deterministic test but the cost of
factoring k once per discovery and proving its factors -- see
`huntlib.ceiling`, which measures that cost and states the ceiling a new
project should start from.

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
LUCAS_P_CAP = 2_000           # N+1 witnesses: P tried up to this, same parity as D
LUCAS_D_CAP = 10_000          # N+1 discriminants tried up to this
TDIV_TO = 1 << 17             # factor_partial: trial division bound
RHO_ITERS = 60_000            # factor_partial: iterations per Brent rho try
RHO_TRIES = 3
ECM_CURVES = 24               # factor_partial: bounded ECM, or give up
FULL_ECM_CURVES = 200         # factor_full: the curves before factorint is asked
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


def factor_full(m, ecm_curves=FULL_ECM_CURVES):
    """The COMPLETE factorization of m as {p: e}, every p a prime (proved
    where it is under the deterministic bound; above it, a probable prime
    that the caller must SUBPROVE -- `prove` does).

    The bounded chain first, then sympy's factorint on whatever is left.
    That last step is the one unbounded call a certificate makes, and it
    is what a hunt's k CEILING exists to bound: `huntlib.ceiling` measures
    the worst case (a balanced semiprime cofactor) at each height and
    states the k below which this stays seconds.  Used once per discovery
    on k, so that every value m*k +- 1 of a run is proved on ONE
    factorization.
    """
    from sympy import factorint
    fac, R = factor_partial(int(m), ecm_curves=ecm_curves)
    if R > 1:
        for p, e in factorint(R).items():
            fac[int(p)] = fac.get(int(p), 0) + int(e)
    return fac


# ------------------------------ Lucas sequences ------------------------------

def jacobi(a, n):
    """The Jacobi symbol (a/n) for odd n > 0; a may be negative."""
    a, n = int(a), int(n)
    if n <= 0 or n % 2 == 0:
        raise ValueError("jacobi: n must be a positive odd integer")
    a %= n
    result = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                result = -result
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a %= n
    return result if n == 1 else 0


def lucas_u(P, Q, m, N):
    """U_m(P, Q) mod N for odd N, by the binary ladder on (U, V, Q^k)."""
    P, Q, m, N = int(P), int(Q), int(m), int(N)
    if m == 0:
        return 0
    D = P * P - 4 * Q
    inv2 = (N + 1) // 2                    # 2^-1 mod N, N odd
    U, V, Qk = 1, P % N, Q % N             # (U_1, V_1, Q^1)
    for bit in bin(m)[3:]:
        U, V, Qk = U * V % N, (V * V - 2 * Qk) % N, Qk * Qk % N
        if bit == "1":
            U, V = (P * U + V) * inv2 % N, (D * U + P * V) * inv2 % N
            Qk = Qk * Q % N
    return U


def _discriminants(cap=LUCAS_D_CAP):
    """Non-square D == 0 or 1 (mod 4), ascending: 5, 8, 12, 13, 17, ..."""
    for D in range(5, cap):
        if D % 4 in (0, 1) and isqrt(D) ** 2 != D:
            yield D


def lucas_witnesses(N, primes_of_F, p_cap=LUCAS_P_CAP, d_cap=LUCAS_D_CAP):
    """(D, {q: (P, Q)}) satisfying the N+1 conditions for every prime
    q | F, or None.

    One discriminant D with (D/N) = -1 for the whole certificate (the
    docstring says why it must be shared), then per prime q the first
    (P, Q) with P^2 - 4Q = D and gcd(Q, N) = 1 whose U_{(N+1)/q} is coprime
    to N -- different q may need different pairs for the same reason the
    N-1 witnesses do.  A pair whose U_{N+1} is NOT divisible by N proves
    N composite outright, and the search stops there.
    """
    N = int(N)
    if N < 3 or N % 2 == 0:
        return None
    D = None
    for d in _discriminants(d_cap):
        if jacobi(d, N) == -1:
            D = d
            break
    if D is None:
        return None                        # N is a perfect square, or huge luck
    out = {}
    for q in primes_of_F:
        q = int(q)
        for P in range(D % 2 or 2, p_cap, 2):
            if (P * P - D) % 4:
                continue
            Q = (P * P - D) // 4
            if Q == 0 or gcd(Q, N) != 1:
                continue
            if lucas_u(P, Q, N + 1, N) != 0:
                return None                # (D/N) = -1 and N does not divide
                                           # U_{N+1}: N is COMPOSITE
            if gcd(lucas_u(P, Q, (N + 1) // q, N), N) == 1:
                out[q] = (P, Q)
                break
        else:
            return None
    return D, out


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


def theorem15(N, fac, p_cap=LUCAS_P_CAP):
    """BLS75 Theorem 15 with N+1 FULLY factored: (D, {q: (P, Q)}), or None.

    The N+1 twin of `theorem1`, for a project whose values are m*k - 1 and
    which therefore owns the factorization of N + 1 = m*k already.
    """
    return lucas_witnesses(N, sorted(fac), p_cap=p_cap)


def _admit(fac, R, depth, base_cap, kw):
    """The primes a certificate may put in F, from a claimed factorization.

    Every prime under the bound is proved by `mr_is_prime` and admitted.
    One above it gets a SUBPROOF -- `prove` one level down, whichever side
    factors -- and is admitted with it; if no subproof lands inside the
    depth, its whole power moves to R and the theorem's size test decides
    whether what is left still proves N.  A claimed factor that is not
    prime at all is a wrong factorization, and the answer is None.

    Returns (fac, R, subproofs, tried) -- `tried` being the large primes
    that were offered a subproof and declined it, so the cofactor step does
    not pay for them twice.
    """
    out, subs, tried = {}, {}, set()
    for p, e in sorted(fac.items()):
        p, e = int(p), int(e)
        if e < 1:
            return None
        if _proved(p):
            out[p] = out.get(p, 0) + e
            continue
        if p < MR_VALID_BELOW or not _isprime(p):
            return None
        if depth > 0:
            sub = prove(p, base_cap=base_cap, depth=depth - 1, **kw)
            if sub is not None:
                out[p] = out.get(p, 0) + e
                subs[str(p)] = sub
                continue
        tried.add(p)
        R *= p ** e
    return out, R, subs, tried


def _factors_out(fac):
    return {str(p): e for p, e in sorted(fac.items())}


def _prove_minus(N, fac, R, subs, base_cap):
    """The N-1 side on an admitted factorization: Theorem 1, else 5."""
    F = 1
    for p, e in fac.items():
        F *= p ** e
    if F % 2 or gcd(F, R) != 1:        # Theorem 5 needs F even and R coprime
        return None
    w = witnesses(N, sorted(fac), base_cap)
    if w is None:
        return None
    out = {"N": N, "F": F, "R": R, "factors": _factors_out(fac),
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


def _prove_plus(N, fac, R, subs):
    """The N+1 side on an admitted factorization: Theorem 15."""
    F = 1
    for p, e in fac.items():
        F *= p ** e
    if gcd(F, R) != 1 or (F - 1) ** 2 <= N:
        return None
    lw = lucas_witnesses(N, sorted(fac))
    if lw is None:
        return None
    D, pairs = lw
    out = {"proof": "bls75-thm15", "N": N, "F": F, "R": R, "D": int(D),
           "factors": _factors_out(fac),
           "lucas": {str(q): [int(P), int(Q)]
                     for q, (P, Q) in sorted(pairs.items())}}
    if subs:
        out["subproofs"] = subs
    return out


def prove(N, fac=None, fac_plus=None, base_cap=CERT_BASE_CAP,
          depth=PROOF_DEPTH, **kw):
    """A checkable primality PROOF for N, or None if this cannot prove it.

    Returns a JSON-safe dict; `verify` re-checks it from scratch and is what
    a gate -- and a reader with a calculator -- runs.  The routes, in the
    order they are tried:

      {"proof": "deterministic-mr"}   N < 3.317e24: mr_is_prime IS a proof,
                                      and no certificate adds anything to it
      {"proof": "bls75-thm1", ...}    N-1 factored past sqrt(N)
      {"proof": "bls75-thm5", ...}    N-1 factored past N^(1/3)
      {"proof": "bls75-thm15", ...}   N+1 factored past sqrt(N) + 1, with a
                                      Lucas sequence per prime of F

    Pass `fac` when the caller already knows a factorization of N-1, or
    `fac_plus` for one of N+1 (both are checked, never trusted); with
    neither, factor_partial does what it can inside its bounds on N-1 and
    then on N+1.  A prime factor above the deterministic bound on either
    side is admitted only with a subproof of its own, found by this same
    function one level down.  A None return means "not proved HERE" -- it
    is not a claim that N is composite, except where noted in the tests.
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
    sides = []
    if fac is not None:
        sides.append(("-", fac))
    if fac_plus is not None:
        sides.append(("+", fac_plus))
    if not sides:
        sides = [("-", None), ("+", None)]
    for side, given in sides:
        M = N - 1 if side == "-" else N + 1
        if given is None:
            f0, R = factor_partial(M, **kw)
        else:
            f0 = {int(p): int(e) for p, e in given.items()}
            prod = 1
            for p, e in f0.items():
                prod *= p ** e
            if prod < 1 or M % prod:
                continue               # not a factorization of this side
            R = M // prod
        adm = _admit(f0, R, depth, base_cap, kw)
        if adm is None:
            continue
        f1, R, subs, tried = adm
        # A large prime cofactor is the usual reason F comes out too small,
        # and it is the one case a single level of recursion settles: prove
        # it, carry the subproof, and it becomes an admissible factor.
        if 1 < R < MR_VALID_BELOW and mr_is_prime(R):
            f1[R] = f1.get(R, 0) + 1
            R = 1
        elif (R > 1 and depth > 0 and R >= MR_VALID_BELOW and R not in tried
              and _isprime(R)):
            sub = prove(R, base_cap=base_cap, depth=depth - 1, **kw)
            if sub is not None:
                f1[R] = f1.get(R, 0) + 1
                subs[str(R)] = sub
                R = 1
        if not f1:
            continue
        out = (_prove_minus(N, f1, R, subs, base_cap) if side == "-"
               else _prove_plus(N, f1, R, subs))
        if out is not None:
            return out
    return None


def _verify_factors(proof, N):
    """(F, fac) from a proof's claimed factorization, every prime of it
    proved -- by the deterministic test or by a subproof about exactly that
    prime -- or (None, why)."""
    fac = {int(p): int(e) for p, e in proof.get("factors", {}).items()}
    if not fac:
        return None, "no factorization"
    subs = proof.get("subproofs", {}) or {}
    F = 1
    for p, e in sorted(fac.items()):
        if e < 1:
            return None, f"bad exponent {e} for {p}"
        if not _proved(p):
            sub = subs.get(str(p), subs.get(p))
            if sub is None:
                return None, (f"claimed factor {p} is past the deterministic "
                              f"bound and carries no subproof")
            if int(sub.get("N", 0)) != p:
                return None, f"subproof for {p} is about {sub.get('N')}"
            ok, why = verify(sub)
            if not ok:
                return None, f"subproof for factor {p} fails: {why}"
        F *= p ** e
    return F, fac


def verify(proof):
    """Re-check a proof from scratch: (ok, message).

    This is the function a gate drills and the one a reader would write.  It
    trusts NOTHING in the dict -- not the factorization, not that the
    claimed factors are prime, not the witnesses, not the arithmetic of the
    theorem's side condition, not even that F divides N-1 (or N+1).
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
    if kind not in ("bls75-thm1", "bls75-thm5", "bls75-thm15"):
        return False, f"unknown proof kind {kind!r}"
    if N % 2 == 0:
        return False, "N is even"
    F, fac = _verify_factors(proof, N)
    if F is None:
        return False, fac
    if kind == "bls75-thm15":
        if (N + 1) % F:
            return False, "F does not divide N+1"
        R = (N + 1) // F
        if gcd(F, R) != 1:
            return False, f"gcd(F, R) = {gcd(F, R)} != 1"
        if (F - 1) ** 2 <= N:
            return False, (f"F = {F} does not exceed sqrt(N) + 1; Theorem 15 "
                           f"shows only that every prime factor is +-1 mod F")
        D = int(proof.get("D", 0))
        if D == 0 or jacobi(D, N) != -1:
            return False, f"the discriminant {D} does not have (D/N) = -1"
        pairs = proof.get("lucas", {}) or {}
        for q in sorted(fac):
            pq = pairs.get(str(q), pairs.get(q))
            if not pq or len(pq) != 2:
                return False, f"no Lucas sequence for {q}"
            P, Q = int(pq[0]), int(pq[1])
            if P * P - 4 * Q != D:
                return False, (f"the sequence for {q} has discriminant "
                               f"{P * P - 4 * Q}, not {D}")
            if Q == 0 or gcd(Q, N) != 1:
                return False, f"Q = {Q} for {q} is not coprime to N"
            if lucas_u(P, Q, N + 1, N) != 0:
                return False, (f"N does not divide U_(N+1) for (P, Q) = "
                               f"({P}, {Q}): N is COMPOSITE")
            if gcd(lucas_u(P, Q, (N + 1) // q, N), N) != 1:
                return False, (f"U_((N+1)/{q}) is not coprime to N for "
                               f"(P, Q) = ({P}, {Q})")
        return True, ("BLS75 Theorem 15: F | N + 1 with (F - 1)^2 > N and a "
                      "Lucas sequence per prime of F, so N is prime")
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

    # THE N+1 ROUTE.  A prime past the bound whose N + 1 is smooth and
    # completely factored -- the shape of a value m*k - 1 once k is
    # factored -- is proved by Theorem 15 and re-verifies; the four
    # tamperings the N-1 side is drilled against are refused here too.
    n15 = _N15_PRIME
    if n15 < MR_VALID_BELOW or n15 + 1 != _F15:
        return False, "the Theorem 15 sample is not F - 1 past the bound"
    p15 = prove(n15, fac_plus=dict(_F15_FAC))
    if p15 is None or p15.get("proof") != "bls75-thm15":
        return False, f"Theorem 15 route not taken for {n15}: {p15}"
    ok, msg = verify(p15)
    if not ok:
        return False, f"Theorem 15 proof of {n15} does not verify: {msg}"
    if jacobi(int(p15["D"]), n15) != -1:
        return False, "the Theorem 15 proof's discriminant is not a non-residue"
    if len({int(pq[0]) ** 2 - 4 * int(pq[1]) for pq in p15["lucas"].values()}) != 1:
        return False, "the Lucas sequences of one proof differ in discriminant"
    q0 = next(iter(p15["lucas"]))
    bad_l = dict(p15["lucas"])
    bad_l[q0] = [int(bad_l[q0][0]) + 2, int(bad_l[q0][1])]
    for name, bad in (("a neighbouring N", dict(p15, N=n15 + 2)),
                      ("a tampered Lucas witness", dict(p15, lucas=bad_l)),
                      ("a truncated factorization",
                       dict(p15, factors=dict(list(p15["factors"].items())[:1]))),
                      ("a mislabelled theorem", dict(p15, proof="bls75-thm1"))):
        if verify(bad)[0]:
            return False, f"{name} verified on the N+1 route"
    # a composite (aF - 1)(bF + 1) with N + 1 = F * (something) offered as
    # if it were factored: no Lucas sequence satisfies both conditions
    if prove(_N15_COMPOSITE) is not None:
        return False, f"produced a proof for the composite {_N15_COMPOSITE}"
    # and the recursion on THIS side: N = 2P - 1 with P a prime above the
    # bound is proved only with a subproof of P, which cannot be stripped
    p2 = prove(_N15_RECUR, fac_plus={2: 1, _N15_RECUR_P: 1})
    if (p2 is None or p2.get("proof") != "bls75-thm15"
            or str(_N15_RECUR_P) not in (p2.get("subproofs") or {})):
        return False, f"the N+1 recursion sample was not proved with a subproof: {p2}"
    if not verify(p2)[0]:
        return False, "the N+1 recursive proof does not verify"
    if verify({k: v for k, v in p2.items() if k != "subproofs"})[0]:
        return False, "an N+1 proof stripped of its subproof still verified"
    return True, ("certificates ok: BLS75 Theorem 1, Theorem 5, Theorem 15 "
                  "(N+1, Lucas) and the subproof recursion on both sides all "
                  "prove and all verify; the constructed composites, a "
                  "tampered (s, r), a tampered Lucas witness, a neighbouring "
                  "N, a truncated factorization, a mislabelled theorem and a "
                  "stripped subproof are all rejected (thm5 F^3/N = %.3g, "
                  "recursion samples %d and %d)" % (_F5**3 / n5, nr, _N15_RECUR))


# The N+1 samples.  _F15 is smooth and _N15_PRIME = _F15 - 1 is a prime past
# the deterministic bound; _N15_RECUR = 2 * P - 1 with P a prime past the
# bound, so its N + 1 = 2 * P needs a subproof; _N15_COMPOSITE is
# (F' - 1)(F' + 1) for a smooth F', a composite of the shape Theorem 15
# must refuse.  All three are fixed rather than searched, so the gate
# drills the same arithmetic every time.
_F15_FAC = {2: 2, 3: 24, 5: 7, 7: 9}
_F15 = 2**2 * 3**24 * 5**7 * 7**9                        # 3561578287608261552187500
_N15_PRIME = _F15 - 1
_N15_RECUR_P = 10000000000000000000014229
_N15_RECUR = 2 * _N15_RECUR_P - 1
_N15_COMPOSITE = 907745640255718380955238399999999       # (F' - 1)(F' + 1)


# Primes past the deterministic bound whose N-1 has a large prime cofactor,
# for the recursion half of the gate.  Several, because which of them needs
# a subproof depends on how far factor_partial gets; the gate takes the
# first that does.
_RECUR_SAMPLES = (10**25 + 1237, 10**25 + 1291, 10**25 + 1417,
                  10**25 + 1447, 10**25 + 1483, 10**25 + 1531,
                  10**25 + 1567, 10**25 + 1621, 10**25 + 1747,
                  10**25 + 1801, 10**25 + 1879, 10**25 + 1951)

GATES = [gate_certificates]
