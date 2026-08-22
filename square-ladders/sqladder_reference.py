"""The oracle for A089761 -- slow, obviously correct, sympy only.

    a(n) = least k such that k*i^2 + 1 is prime for ALL i = 1..n.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Two facts about the problem are PROVED here rather than assumed, because
both engines are built on them.  They are also the reason this sequence is
not the engine A247965 already has, despite reading like its transpose.

  THE KILLED SET.  Fix a prime q.  For k with q | k every value is
  k*i^2 + 1 == 1 (mod q), so q kills nothing; k == 0 (mod q) is always
  SAFE.  For q not dividing k,

      q | k*i^2 + 1   <=>   i^2 == -k^-1  (mod q),

  so k is killed exactly when -k^-1 is a square mod q that is hit by some
  i <= n.  Writing K(q,n) = { -(i^2)^-1 mod q : 1 <= i <= n, q does not
  divide i } for that killed set, the engines sieve k against K(q,n) and
  nothing else.

  ITS SIZE, EXACTLY.  w(q,n) = |K(q,n)| = min(n, (q-1)/2) for odd q, and
  w(2,n) = 1.  Both halves are elementary:

    * q > 2n:  the i^2 are pairwise distinct mod q, since i = j would need
      q | i-j or q | i+j and both are impossible for 1 <= i < j <= n when
      q > 2n.  Inversion and negation are bijections, so w = n.
    * q <= 2n+1:  i^2 for i = 1..(q-1)/2 already runs over ALL (q-1)/2
      quadratic residues, and (q-1)/2 <= n, so every residue is reached.
      The squares are a group closed under inversion, so K(q,n) = -QR(q)
      and w = (q-1)/2.

  WHAT THAT MEANS FOR THE ENGINE.  A247965 kills EVERY nonzero k mod q for
  small q -- there the analogous u = -k^-2 always lands among the m being
  tested -- which forces a(n) to be a multiple of the wheel modulus and
  leaves exactly ONE candidate residue per period.  Here only half the
  nonzero residues die, so the wheel is a RESIDUE TABLE with
  prod (q - w(q,n)) entries rather than a single multiplier, and the two
  problems need different machinery however similar they read.

  THE EXCEPTION ZONE is real and small.  The argument above says a value
  divisible by q is composite, which needs the value to EXCEED q.  It does
  not for the smallest terms: a(1) = a(2) = 1 survives because 1*1^2+1 = 2
  IS the prime 2, and k = 1 is odd, which the q = 2 rule would forbid.  The
  oracle therefore sweeps WITHOUT the wheel below K_FLOOR and both engines
  refuse to run there.

Gates in this file: G1 (the frozen knowns reproduce), G2 (the small terms
are re-derived exhaustively from scratch), G2b (the w(q,n) formula equals
direct divisibility).
"""

from sympy import isprime, primerange

# A089761, as published.  a(11)-a(15) are one value, found by Donovan
# Johnson (Sep 27 2008) as a(11); a(12)-a(15) rode along with it and were
# never separately searched for.  Re-verified against oeis.org the day this
# project was built (OEIS export 2026-08-21, revision #14 Aug 14 2017).
KNOWN = {1: 1,
         2: 1,
         3: 4,
         4: 22,
         5: 58,
         6: 58,
         7: 58,
         8: 54972,
         9: 68112,
         10: 4748632,
         11: 861066640,
         12: 861066640,
         13: 861066640,
         14: 861066640,
         15: 861066640}

# Published searched-empty lower bound (Max Alekseyev, in the entry since
# at latest 2017).  A LOWER bound only: this sequence has no published
# upper bound at any open n, which is what makes it a hunt.
PUBLISHED_BOUNDS = {16: 14_000_000_000_000}

OPEN_N = [16, 17, 18, 19, 20]

# The wheel argument has an exception zone below this k (a value can BE the
# small prime that would otherwise divide it), so the engines refuse to run
# there and the oracle covers it by brute force.
K_FLOOR = 10 ** 4

# The single composite that keeps a(16) open: 861066640*16^2 + 1.
THE_WALL = (861066640, 16)


def value(k, i):
    return k * i * i + 1


def run_length(k, cap=64):
    """Largest r <= cap with k*i^2+1 prime for every i = 1..r."""
    r = 0
    while r < cap and isprime(value(k, r + 1)):
        r += 1
    return r


def forbidden_k_residues(q, n):
    """K(q,n), computed DIRECTLY from divisibility -- the definition.

    Not the inverse-and-negate construction the engines use: the parity
    gate between the two is what makes the construction trustworthy.
    """
    out = set()
    for k in range(q):
        for i in range(1, n + 1):
            if (k * i * i + 1) % q == 0:
                out.add(k)
                break
    return out


def w(q, n):
    """|K(q,n)| by the closed form proved in the module docstring."""
    return 1 if q == 2 else min(n, (q - 1) // 2)


def wheel_residues(n, p1):
    """Every k mod W that survives all primes q <= p1, by brute force.

    W = product of the primes <= p1.  This is the oracle's version: it
    walks the whole period.  The engines build the same set by CRT lifting
    and are gated against this on small p1.
    """
    W = 1
    for q in primerange(2, p1 + 1):
        W *= q
    killed = {q: forbidden_k_residues(q, n) for q in primerange(2, p1 + 1)}
    return W, [r for r in range(W)
               if all(r % q not in killed[q] for q in killed)]


def first_k(n, lo=1, hi=None, step=1, start=None):
    """Least k in [lo, hi] with run_length(k) >= n, by definition.

    With step = 1 this is the literal definition swept one integer at a
    time -- the slowest thing in this project, and the reason G2 only
    covers the small terms.
    """
    k = lo if start is None else start
    while hi is None or k <= hi:
        if run_length(k, cap=n) >= n:
            return k
        k += step
    return None


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, the ladder is monotone,
    and every term above the floor survives the small-prime wheel."""
    prev = 0
    W, res = wheel_residues(max(KNOWN), 13)
    keep = set(res)
    for n in sorted(KNOWN):
        k = KNOWN[n]
        r = run_length(k, cap=n + 4)
        if r < n:
            return False, f"G1 FAIL: a({n}) = {k} has run {r} < {n}"
        if k < prev:
            return False, f"G1 FAIL: a({n}) = {k} < a({n-1}) = {prev}"
        if k >= K_FLOOR and k % W not in keep:
            return False, (f"G1 FAIL: a({n}) = {k} is killed by the wheel "
                           f"mod {W}")
        prev = k
    # the plateau is a fact about ONE k, and the wall is a single composite
    kk, ii = THE_WALL
    if run_length(kk, cap=20) != 15:
        return False, f"G1 FAIL: a(11) champion {kk} does not reach exactly 15"
    if isprime(value(kk, ii)):
        return False, (f"G1 FAIL: {kk}*{ii}^2+1 is prime, so a(16) would not "
                       f"be open")
    return True, ("G1 ok: a(1)-a(%d) satisfy the definition, the ladder is "
                  "monotone, every term above the floor is on the wheel, and "
                  "the a(11) champion reaches exactly 15 (its wall "
                  "%d*%d^2+1 is composite)" % (max(KNOWN), kk, ii))


def g2_rederive_small(upto=9):
    """Re-derive the small terms exhaustively from the bare definition."""
    for n in range(1, upto + 1):
        got = first_k(n, lo=1, hi=KNOWN[n])
        if got != KNOWN[n]:
            return False, f"G2 FAIL: re-derived a({n}) = {got} != {KNOWN[n]}"
    return True, (f"G2 ok: a(1)-a({upto}) re-derived exhaustively, one "
                  f"integer at a time, from the definition alone")


def g2b_killed_set_size():
    """The closed form w(q,n) = min(n,(q-1)/2) IS direct divisibility.

    Both directions and both regimes (q <= 2n+1 and q > 2n), because the
    engines size every table from this formula and a wrong size is either
    a missed kill or a lost candidate.
    """
    for n in (3, 7, 11, 16, 19):
        for q in primerange(2, 120):
            direct = forbidden_k_residues(q, n)
            if len(direct) != w(q, n):
                return False, (f"G2b FAIL: n={n} q={q}: direct "
                               f"{len(direct)} != formula {w(q, n)}")
            built = {(-pow(i * i, -1, q)) % q
                     for i in range(1, n + 1) if i % q}
            if built != direct:
                return False, (f"G2b FAIL: n={n} q={q}: constructed "
                               f"{sorted(built)} != direct {sorted(direct)}")
            if 0 in direct:
                return False, (f"G2b FAIL: n={n} q={q}: k == 0 (mod q) must "
                               f"always be safe")
    return True, ("G2b ok: |K(q,n)| = min(n,(q-1)/2) and the constructed set "
                  "equals direct divisibility, every prime q < 120 at "
                  "n = 3, 7, 11, 16, 19; k == 0 (mod q) always survives")


GATES = [g1_knowns_reproduce, g2b_killed_set_size, g2_rederive_small]

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
