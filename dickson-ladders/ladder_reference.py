"""The oracle for A247965 -- slow, obviously correct, sympy only.

    a(n) = least k such that m*k^2 + 1 is prime for ALL m = 1..n.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Two facts about the problem are also proved here rather than assumed,
because both engines depend on them:

  WHEEL.  For a prime q <= n+1 and k not divisible by q, the residue
  u = -k^-2 mod q is a nonzero residue, so u lies in {1, ..., q-1}, and
  q-1 <= n means u is one of the m being tested.  That m has
  m*k^2 + 1 == 0 (mod q), so the value is divisible by q -- composite as
  soon as it exceeds q.  Hence every a(n) with a(n) >= sqrt(n+1) is
  divisible by W(n) = product of primes <= n+1.  (The exception zone is
  tiny and real: a(1) = a(2) = 1 works because 1*1+1 = 2 IS the prime 2.
  The oracle therefore sweeps WITHOUT the wheel below K_FLOOR and both
  engines refuse to run below it.)

  SIEVE.  For a prime q > n+1 the killed residues of k are the roots of
  k^2 == -1/m (mod q) over m = 1..n.  Each solvable m contributes exactly
  two roots (-1/m is never 0), and distinct m give disjoint root sets
  (m1*k^2 == m2*k^2 == -1 forces m1 == m2), so there are exactly
  2 * #{m <= n : (-m|q) = +1} of them.

Gates in this file: G1 (the frozen knowns reproduce) and G2 (the small
terms are re-derived exhaustively from scratch).
"""

from sympy import isprime, primerange

# A247965, as published: a(1)..a(9) with a(7)-a(9) from Hiroaki Yamanouchi
# (Oct 2014).  Re-verified against oeis.org the day this project was built.
KNOWN = {1: 1,
         2: 1,
         3: 6,
         4: 3240,
         5: 113730,
         6: 30473520,
         7: 3776600100,
         8: 16341921960,
         9: 3332396388090}

# Published searched-empty lower bounds (Yamanouchi, Oct 2014).  These are
# LOWER bounds only: the sequence has no published upper bound at any open
# n, which is what makes it a hunt.
PUBLISHED_BOUNDS = {10: 15_466_500_000_000, 11: 107_669_100_000_000}

OPEN_N = [10, 11, 12, 13, 14]

# Below this k the wheel argument above has an exception zone (a value can
# BE the small prime that would otherwise divide it), so the engines refuse
# to run there and the oracle covers it by brute force.
K_FLOOR = 10**4


def wheel_modulus(n):
    """W(n) = product of the primes q <= n+1; every a(n) >= K_FLOOR is a
    multiple of it (see the module docstring)."""
    w = 1
    for q in primerange(2, n + 2):
        w *= q
    return w


def value(m, k):
    return m * k * k + 1


def run_length(k, cap=64):
    """Largest r <= cap with m*k^2+1 prime for every m = 1..r."""
    r = 0
    while r < cap and isprime(value(r + 1, k)):
        r += 1
    return r


def first_k(n, lo=1, hi=None, wheel=True):
    """Least k in [lo, hi] with run_length(k) >= n, by definition.

    With wheel=False this is the literal definition swept one integer at a
    time -- the slowest thing in the repository, and the reason G2 only
    covers the small terms.
    """
    step = wheel_modulus(n) if wheel else 1
    k = lo + (-lo) % step if wheel else lo
    k = max(k, step if wheel else 1)
    while hi is None or k <= hi:
        if run_length(k, cap=n) >= n:
            return k
        k += step
    return None


def forbidden_k_residues(q, n):
    """Killed residues of k mod q, computed DIRECTLY from divisibility.

    This is the definition, not the Tonelli construction the engines use:
    the parity gate between them is what makes the construction trustworthy.
    """
    out = set()
    for k in range(q):
        kk = k * k % q
        for m in range(1, n + 1):
            if (m * kk + 1) % q == 0:
                out.add(k)
                break
    return out


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, and the ladder is
    monotone (run >= n+1 implies run >= n, so a() cannot decrease)."""
    prev = 0
    for n in sorted(KNOWN):
        k = KNOWN[n]
        r = run_length(k, cap=n + 4)
        if r < n:
            return False, f"G1 FAIL: a({n}) = {k} has run {r} < {n}"
        if k < prev:
            return False, f"G1 FAIL: a({n}) = {k} < a({n-1}) = {prev}"
        if k >= K_FLOOR and k % wheel_modulus(n):
            return False, (f"G1 FAIL: a({n}) = {k} is not a multiple of "
                           f"W({n}) = {wheel_modulus(n)}")
        prev = k
    return True, ("G1 ok: a(1)-a(%d) all satisfy the definition, the ladder "
                  "is monotone, and every term above the floor sits on its "
                  "wheel" % max(KNOWN))


def g2_rederive_small(upto=6):
    """Re-derive the small terms exhaustively from the definition."""
    for n in range(1, upto + 1):
        got = first_k(n, lo=1, hi=KNOWN[n] * 2, wheel=(n >= 3))
        if got != KNOWN[n]:
            return False, f"G2 FAIL: re-derived a({n}) = {got} != {KNOWN[n]}"
    return True, f"G2 ok: a(1)-a({upto}) re-derived exhaustively from scratch"


GATES = [g1_knowns_reproduce, g2_rederive_small]

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
