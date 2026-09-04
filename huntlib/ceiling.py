"""Where a hunt's k CEILING comes from -- and why a new project starts HIGH.

Every engine in this repository states an enforced ceiling on k
(CONVENTIONS.md "Numeric hygiene").  For the first six projects that
ceiling was the deterministic Miller-Rabin bound, 3.317e24, rearranged for
the family's largest value: below it every primality decision the hunt
makes is a proof, and a discovery needs no certificate.  Four campaigns
have since run INTO that ceiling with their next term probably just above
it (prime-ladders' A084701, linear-ladders' four -1 families), and each
one paid a new engine version to move it.  That is the wrong default.

THE DETERMINISTIC BOUND IS NOT THE CEILING.  A discovery is proved by a
CERTIFICATE (huntlib.certificate), and for every ladder hunt here the
values have structure -- m*k + 1 or m*k - 1 with m tiny -- so N -+ 1 is
completely factored the moment k is, and BLS75 Theorem 1 (N - 1) or
Theorem 15 (N + 1) proves every value of a run on ONE factorization of k.
A prime factor of k above 3.317e24 gets a subproof of its own by the same
machinery (whichever of p - 1, p + 1 factors), so no value size is a
limit.  What bounds k is the COST of that certificate per discovery:
factoring k once, and proving its factors.  The census, the NEAR values
and the bound argument ("a composite that passes a probable-prime chain
can only lengthen a run, never hide one") need no certificate at all.

THE CEILING IS MEASURED, NOT ASSUMED.  The worst case for the bounded
factoring chain (trial division, Brent rho, ECM, then sympy's factorint on
what is left) is k whose hard part is a BALANCED SEMIPRIME -- two primes
near sqrt(k / unit), where `unit` is what the hunt's forced primes
already divide out of every candidate.  Measured on this repository's
machine (2026-09-04, `factor_full`, 200 ECM curves, two seeds per height),
the worst case at unit 1 is

    k ~ 1e28  0.5 s      k ~ 1e32  0.7 s      k ~ 1e36  2.2 s
    k ~ 1e30  0.5 s      k ~ 1e34  1.1 s      k ~ 1e38  2.7 s
                                              k ~ 1e40  3.4 s

(and 0.1-1.6 s to 1e42 at unit 9699690, where the hard part is 1e7 times
smaller), a prime factor of k above the bound is subproved 8 of 8 times
at each of 1e25, 1e27, 1e29, 1e31 and 1e33 in at most 0.5 s, and a run of
18 values then costs under a second of Lucas and Fermat witnesses.  So
below K_CEIL the worst certificate a discovery can cost is seconds, and a
campaign that finds something every few hours never notices it.

    K_CEIL = 1e40

is therefore the ceiling every NEW project starts from, on both signs,
unless it measures a reason not to.  What would raise it: the same
measurement at 1e42 and 1e44 (ECM's curve count is the knob -- a 22-digit
factor wants more than 200 curves, or a larger B1), and the subproof rate
at the heights the factors of k would then reach.  What would LOWER it
for a project: a value whose structure is not m*k +- 1 (then N -+ 1 is
structureless, factor_partial is doing the work, and the honest ceiling is
where its success rate falls -- measure it with `subproof_rate`).

The other limits a ceiling once implied are gone by construction: the
device carries candidates as (k, off) with the base a Python int
(OPTIMIZATION.md 2.7), so no machine word bounds k; the CPU engine, the
checkpoint and the odds model are Python ints and floats; the
classification's cost grows only polynomially in the bit length.

HOW A PROJECT USES IT.  `k_ceil()` returns K_CEIL; a project's own
`k_ceil(n, ...)` returns it for every sign and states its proof crossing
(where classification stops being a proof) separately, as a MILESTONE
rather than a stop.  Its ceiling gate drills `certificate_drill` at the
height -- a hard k at K_CEIL on both routes, a k with a prime factor above
the deterministic bound so the recursion is exercised, every proof
re-verified and refused for a neighbouring N -- and refuses a sweep past
it.  `gate_ceiling` here is the repo-wide half of that: the machinery at
the height, with the project's own values left to the project.
"""

import random
import time
from math import isqrt

from sympy import isprime as _isprime, nextprime as _nextprime

from . import certificate
from .primes import MR_VALID_BELOW

K_CEIL = 10 ** 40             # measured (module docstring); both signs
CERT_BUDGET_S = 60.0          # what one worst-case certificate may cost


def k_ceil():
    """The enforced ceiling on k a project starts from.  One number, both
    signs: the certificate cost is symmetric in the sign of the value."""
    return K_CEIL


def hard_k(height, unit=1, seed=1):
    """A worst-case k near `height`: unit times a balanced semiprime.

    (k, (p, q)) with p and q the primes; the hard part is k / unit and its
    two factors sit within 1% of sqrt(k / unit), which is the shape the
    factoring chain finds slowest.  Seeded so a drill is reproducible.
    """
    rng = random.Random(seed)
    tgt = isqrt(int(height) // int(unit))
    p = _nextprime(tgt - rng.randrange(max(tgt // 100, 2)))
    q = _nextprime(tgt + rng.randrange(max(tgt // 100, 2)))
    return int(unit) * p * q, (int(p), int(q))


def big_prime_k(height, unit=1):
    """k = unit * P with P a prime ABOVE the deterministic bound -- the
    shape whose certificate needs the recursion (a subproof of P)."""
    P = _nextprime(int(height) // int(unit))
    if P < MR_VALID_BELOW:
        raise ValueError(f"{height:.3g} / {unit} is under the deterministic "
                         f"bound; no subproof would be needed")
    return int(unit) * P, int(P)


def prime_mults(k, s, want=2, m_max=2000):
    """The first `want` multipliers m >= 2 with m*k + s a (probable) prime
    -- so a drill at an arbitrary k has values to prove on the side s."""
    out = []
    for m in range(2, m_max):
        if _isprime(m * int(k) + int(s)):
            out.append(m)
            if len(out) >= want:
                break
    return out


def certificate_cost(k, mults=None, signs=(+1, -1), ecm_curves=None, want=2):
    """Time the certificate a discovery at k would cost: factor k once,
    then prove m*k + s for every m in `mults` (or, with None, the first
    `want` multipliers per sign whose value is prime) and s in `signs`,
    each proof re-verified.  Returns a dict with the seconds, the routes
    taken and how many of the values tried were proved.
    """
    k = int(k)
    t0 = time.perf_counter()
    fac = (certificate.factor_full(k) if ecm_curves is None
           else certificate.factor_full(k, ecm_curves=ecm_curves))
    t_fac = time.perf_counter() - t0
    routes, proved, tried, t_prove = {}, 0, 0, 0.0
    for s in signs:
        ms = prime_mults(k, s, want) if mults is None else mults
        for m in ms:
            N = int(m) * k + int(s)
            if N < MR_VALID_BELOW or not _isprime(N):
                continue
            tried += 1
            facN = dict(fac)
            for p, e in certificate.factor_partial(int(m))[0].items():
                facN[int(p)] = facN.get(int(p), 0) + int(e)
            t1 = time.perf_counter()
            proof = (certificate.prove(N, fac=facN) if s > 0
                     else certificate.prove(N, fac_plus=facN))
            ok = proof is not None and certificate.verify(proof)[0]
            t_prove += time.perf_counter() - t1
            if ok:
                proved += 1
                r = proof["proof"] + ("+sub" if proof.get("subproofs") else "")
                routes[r] = routes.get(r, 0) + 1
    return {"k": k, "factor_s": t_fac, "prove_s": t_prove,
            "total_s": t_fac + t_prove, "factors": len(fac),
            "largest_factor": max(fac) if fac else 1,
            "proved": proved, "tried": tried, "routes": routes}


def subproof_rate(height, samples=8, seed=20260904):
    """How often `certificate.prove` settles a RANDOM prime near `height`
    (the subproof a prime factor of k above the bound needs), and how long
    the slowest one took."""
    rng = random.Random(seed)
    ok, worst = 0, 0.0
    for _ in range(samples):
        P = _nextprime(int(height) + rng.randrange(max(int(height) // 10, 2)))
        t0 = time.perf_counter()
        pr = certificate.prove(P)
        worst = max(worst, time.perf_counter() - t0)
        if pr is not None and certificate.verify(pr)[0]:
            ok += 1
    return ok, samples, worst


# ---------------------------------- gate ------------------------------------

def gate_ceiling():
    """The certificate machinery works AT K_CEIL, on both routes, inside
    the budget, with the recursion exercised; and a subproof refuses to be
    stripped.  The project's own values are the project's drill."""
    unit = 1
    k, (p, q) = hard_k(K_CEIL, unit, seed=1)
    if not (k < K_CEIL * 1.02 and p < q and _isprime(p) and _isprime(q)):
        return False, f"ceiling gate: hard_k built {k} from ({p}, {q})"
    m = certificate_cost(k, signs=(+1, -1), want=2)
    if m["largest_factor"] != q or m["factors"] != 2:
        return False, (f"ceiling gate: the hard k at {K_CEIL:.3g} did not "
                       f"factor as p * q: {m}")
    if m["total_s"] > CERT_BUDGET_S:
        return False, (f"ceiling gate: a worst-case certificate at "
                       f"{K_CEIL:.3g} took {m['total_s']:.1f} s, over the "
                       f"{CERT_BUDGET_S:.0f} s budget -- lower K_CEIL or "
                       f"raise ECM's curves, and re-measure")
    if m["proved"] != m["tried"] or m["tried"] < 1:
        return False, (f"ceiling gate: {m['proved']} of {m['tried']} values "
                       f"at the hard k proved ({m['routes']})")
    routes = set(m["routes"])
    if not routes & {"bls75-thm1", "bls75-thm5"} or "bls75-thm15" not in routes:
        return False, (f"ceiling gate: both routes must be exercised at the "
                       f"ceiling; got {m['routes']}")
    # the recursion: k with a prime factor above the deterministic bound
    kb, P = big_prime_k(K_CEIL // 10 ** 6, unit)
    mb = certificate_cost(kb, signs=(+1, -1), want=2)
    if mb["proved"] < 1 or mb["proved"] != mb["tried"]:
        return False, (f"ceiling gate: values on k = unit * P with P = {P} "
                       f"above the bound: {mb['proved']} of {mb['tried']} "
                       f"proved ({mb['routes']})")
    if not any(r.endswith("+sub") for r in mb["routes"]):
        return False, (f"ceiling gate: no proof on k = unit * P carried a "
                       f"subproof of P: {mb['routes']}")
    if mb["total_s"] > CERT_BUDGET_S:
        return False, (f"ceiling gate: the recursion case took "
                       f"{mb['total_s']:.1f} s, over the budget")
    # and a subproof cannot be stripped: rebuild one proof and cut it
    side = -1 if prime_mults(kb, -1, 1) else +1
    N = prime_mults(kb, side, 1)[0] * kb + side
    fac = {P: 1}
    for pp, e in certificate.factor_partial((N - side) // P)[0].items():
        fac[pp] = fac.get(pp, 0) + e
    proof = (certificate.prove(N, fac=fac) if side > 0
             else certificate.prove(N, fac_plus=fac))
    if proof is None or not proof.get("subproofs"):
        return False, f"ceiling gate: no subproof was built for {N}"
    if certificate.verify({a: b for a, b in proof.items()
                           if a != "subproofs"})[0]:
        return False, "ceiling gate: a proof stripped of its subproof verified"
    if certificate.verify(dict(proof, N=N + 2))[0]:
        return False, "ceiling gate: a proof verified for a neighbouring N"
    return True, (f"ceiling ok: at K_CEIL = {K_CEIL:.3g} a worst-case k "
                  f"(unit x two {len(str(q))}-digit primes) is factored and "
                  f"{m['proved']} values on it proved on both routes in "
                  f"{m['total_s']:.1f} s ({', '.join(f'{r} x{c}' for r, c in sorted(m['routes'].items()))}); "
                  f"a k with a {len(str(P))}-digit prime factor above the "
                  f"deterministic bound is proved with a subproof "
                  f"({', '.join(f'{r} x{c}' for r, c in sorted(mb['routes'].items()))}) "
                  f"in {mb['total_s']:.1f} s, and the subproof cannot be "
                  f"stripped nor the proof moved to N + 2; budget "
                  f"{CERT_BUDGET_S:.0f} s")


GATES = [gate_ceiling]
