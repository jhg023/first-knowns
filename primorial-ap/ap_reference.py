"""The oracle for A053647 -- slow, obviously correct, sympy only.

    a(n) = the least prime p such that p, p + P(n), p + 2*P(n), ...,
           p + (n-1)*P(n) are ALL prime,

where P(n) = A002110(n) is the product of the first n primes.  In words:
the first term of the first arithmetic progression of n primes whose common
difference is the primorial -- the SMALLEST difference an n-term progression
of primes can have, since any such difference must be divisible by every
prime up to n.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Three facts about the problem are proved here rather than assumed, because
both engines depend on all three:

  ADMISSIBILITY.  The tuple {0, P(n), ..., (n-1)P(n)} is admissible: for a
  prime q <= prime(n) every member is congruent to p (mod q), so one
  residue class of p is excluded and no more; for q > prime(n) the n
  members are distinct mod q and q > n leaves a class free.  Nothing
  obstructs the progression at any prime, which is why Dickson's conjecture
  (and the Hardy-Littlewood k-tuple conjecture with it) predicts infinitely
  many p for every n -- a find CONFIRMS the conjecture, never refutes it.

  THE SIEVE.  For any prime q the killed residues of p are exactly

      F(q, n) = { (-j * P(n)) mod q : j = 0 .. n-1 },

  and that one formula covers both cases: when q | P(n) every j gives 0, so
  F = {0} (p must not be divisible by q -- p is prime and larger); when
  q does not divide P(n) the n values are distinct.  The engines build this
  set two different ways and the oracle a third (by direct divisibility),
  which is what the parity gates compare.

  THE WHEEL.  a(n) is itself prime and exceeds prime(n) for every n >= 5,
  so it is coprime to P(n) -- and in particular to 2, 3 and 5.  That is the
  whole justification for the mod-30 wheel both engines walk.  Below
  P_FLOOR the claim fails (a(1) = 2, a(2) = 5, a(3) = 7 are themselves
  wheel primes), so the engines refuse to run there and the oracle covers
  that zone by brute force.

WHAT THIS SEQUENCE IS NOT: monotone.  a(7) = 7937 is LARGER than
a(8) = 7703.  Each n is its own question with its own difference P(n), so
no term bounds any other and no engine may assume otherwise -- which is
also why the campaign re-sieves from the floor for every term rather than
carrying one cursor up the ladder.

Gates in this file: G1 (the frozen knowns reproduce) and G2 (the small
terms are re-derived exhaustively from scratch).
"""

from sympy import isprime, prime, primerange, primorial

# A053647, as published: a(1)..a(15).  a(11)-a(13) are Jud McCranie's
# (Feb 2000), a(14)-a(15) Donovan Johnson's (Oct 20, 2009); nothing
# computational has happened to the sequence since.  Re-verified against
# oeis.org the day this project was built (2026-08-20).
KNOWN = {1: 2,
         2: 5,
         3: 7,
         4: 13,
         5: 37,
         6: 73,
         7: 7937,
         8: 7703,
         9: 272809,
         10: 640943,
         11: 5378959,
         12: 116137159,
         13: 3708797237,
         14: 114649314209,
         15: 158317270283}

# There are NO published lower bounds on any open term.  The only bound in
# the OEIS entry -- "a(14) > 2^32 and a(15) > 2^32", Jud McCranie -- was
# superseded by the values themselves in 2009.  Every open term is open
# from the floor up, which is what makes this a hunt rather than a race to
# a known finish line.
PUBLISHED_BOUNDS = {}

OPEN_N = [16, 17, 18, 19, 20, 21, 22, 23]

# Below this p the wheel argument has an exception zone (p can BE one of
# the wheel primes), so the engines refuse to run there and the oracle
# covers it by brute force.  Far below every term this project hunts.
P_FLOOR = 10**4

# The mod-30 wheel both engines walk: p must be coprime to 2, 3 and 5.
W0 = 30
W0_RESIDUES = (1, 7, 11, 13, 17, 19, 23, 29)


_P = {}


def difference(n):
    """P(n) = A002110(n), the product of the first n primes.

    Memoized, and that is not an optimization of the mathematics -- it is
    the difference between an oracle that finishes and one that does not.
    Every chain test needs P(n), and recomputing a primorial per candidate
    made g2 take longer than the whole rest of the battery.
    """
    n = int(n)
    if n not in _P:
        _P[n] = int(primorial(n))
    return _P[n]


def values(p, n):
    """The n values the definition asks about, in order."""
    d = difference(n)
    return [p + j * d for j in range(n)]


def chain_depth(p, n, cap=None):
    """How many of the n values are prime, counting from j = 0 and stopping
    at the first that is not.  `chain_depth(p, n) >= n` is the definition."""
    d = difference(n)
    cap = n if cap is None else cap
    j = 0
    while j < cap and isprime(p + j * d):
        j += 1
    return j


def first_p(n, lo=2, hi=None, wheel=True):
    """The least p in [lo, hi] with chain_depth(p, n) >= n, by definition.

    With wheel=False this is the literal definition swept one integer at a
    time -- the slowest thing in this project, and the reason G2 only covers
    the small terms.
    """
    p = int(lo)
    while hi is None or p <= hi:
        if (not wheel) or p < P_FLOOR or all(p % q for q in (2, 3, 5)):
            if chain_depth(p, n) >= n:
                return p
        p += 1
    return None


def forbidden_residues(q, n):
    """Killed residues of p mod q, computed DIRECTLY from divisibility.

    This is the definition, not the arithmetic the engines use: the parity
    gates between the three constructions are what make the fast ones
    trustworthy.
    """
    d = difference(n)
    out = set()
    for r in range(q):
        for j in range(n):
            if (r + j * d) % q == 0:
                out.add(r)
                break
    return out


def sieve_survivor(p, n, q2):
    """True iff no value p + j*P(n) has a prime factor below q2 (except
    where the value IS that prime).  The oracle's notion of a survivor."""
    d = difference(n)
    for q in primerange(2, q2):
        for j in range(n):
            v = p + j * d
            if v % q == 0 and v != q:
                return False
    return True


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, is prime, is coprime to
    its own difference above the floor -- and is NOT assumed monotone."""
    for n in sorted(KNOWN):
        p = KNOWN[n]
        if not isprime(p):
            return False, f"G1 FAIL: a({n}) = {p} is not prime"
        depth = chain_depth(p, n)
        if depth < n:
            return False, (f"G1 FAIL: a({n}) = {p} has only {depth} of {n} "
                           f"values prime")
        if p >= P_FLOOR and any(p % q == 0 for q in (2, 3, 5)):
            return False, (f"G1 FAIL: a({n}) = {p} is not on the mod-30 wheel")
        if n >= 5 and p <= prime(n):
            return False, (f"G1 FAIL: a({n}) = {p} does not exceed "
                           f"prime({n}) = {prime(n)}, so the wheel argument "
                           f"does not cover it")
    if KNOWN[7] <= KNOWN[8]:
        return False, ("G1 FAIL: the frozen table has a(7) <= a(8); this "
                       "sequence is NOT monotone and the table said it was")
    return True, ("G1 ok: a(1)-a(%d) are prime, satisfy the definition, sit "
                  "on the mod-30 wheel above the floor, and a(7) > a(8) "
                  "confirms the sequence is not monotone" % max(KNOWN))


def g2_rederive_small(upto=9):
    """Re-derive the small terms exhaustively from the definition, without
    the wheel -- the literal sweep, one integer at a time."""
    for n in range(1, upto + 1):
        got = first_p(n, lo=2, hi=KNOWN[n], wheel=False)
        if got != KNOWN[n]:
            return False, f"G2 FAIL: re-derived a({n}) = {got} != {KNOWN[n]}"
    return True, (f"G2 ok: a(1)-a({upto}) re-derived exhaustively from the "
                  f"definition, one integer at a time, no wheel")


def g2b_forbidden_matches_formula():
    """The direct-divisibility residue set equals the closed formula, and
    the two cases of q come out right: |F| = 1 when q divides P(n),
    |F| = n otherwise."""
    for n in (5, 13, 16):
        d = difference(n)
        for q in primerange(2, 120):
            direct = forbidden_residues(q, n)
            formula = {(-j * d) % q for j in range(n)}
            if direct != formula:
                return False, (f"G2b FAIL: n={n} q={q} direct={sorted(direct)} "
                               f"formula={sorted(formula)}")
            want = 1 if d % q == 0 else n
            if len(direct) != want:
                return False, (f"G2b FAIL: n={n} q={q} has {len(direct)} "
                               f"killed residues, expected {want}")
    return True, ("G2b ok: killed residues by direct divisibility == the "
                  "formula {-j*P(n) mod q}, with |F| = 1 for q | P(n) and "
                  "|F| = n otherwise, every q < 120 at n = 5, 13, 16")


GATES = [g1_knowns_reproduce, g2_rederive_small, g2b_forbidden_matches_formula]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.  huntlib is
# imported HERE, in the script path only, so the module itself keeps the
# dependencies its gates are argued from and nothing else.
if __name__ == "__main__":
    import pathlib as _pl
    import sys as _s
    _s.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown

    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)

    _s.exit(_shutdown.graceful(_gates) or 0)
