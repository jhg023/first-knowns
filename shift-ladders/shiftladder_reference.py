"""The oracle for the shift ladders -- slow, obviously correct, sympy only.

    A(b, n) = least m >= 1 such that m + b^k is prime for ALL k = 1..n

    b = 4  ->  A130003   (Firoozbakht 2007; a(18) Jens Kruse Andersen 2007)
    b = 2  ->  A110096   (Pe 2005; a(14)-a(16) Bert Dobbelaere 2021)

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Four facts are PROVED here rather than assumed, because both engines and
the odds model are built on them.

  THE KILLED SET.  Fix a prime q.  Then

      q | m + b^k   <=>   m == -b^k  (mod q),

  so the residues of m that q kills are exactly

      K(q,n,b) = { -b^k mod q : 1 <= k <= n }

  and the engines sieve m against K(q,n,b) and nothing else.  Note what is
  NOT here: no inverse, no quadratic character, no case on whether m is
  divisible by q.  A shift ladder kills by a GEOMETRIC ORBIT where a square
  ladder kills by a quadratic one, and that single difference is the whole
  of the arithmetic that separates this project from square-ladders.

  ITS SIZE, EXACTLY.  w(q,n,b) = |K(q,n,b)| = 1 if q | b, else
  min(n, ord_q(b)).  Both halves are elementary:

    * q | b:  every b^k == 0 (mod q) for k >= 1, so K = {0} and the rule
      is just "q does not divide m".  Here b is a power of two, so this is
      the single statement that m is ODD.
    * q does not divide b:  negation is a bijection on Z/q, so
      |K| = |{ b^k mod q : 1 <= k <= n }|, and the powers of b cycle with
      period d = ord_q(b), so the first n of them take min(n, d) distinct
      values.

  ADMISSIBLE AT EVERY n, FOR BOTH BASES.  w(q,n,b) <= max(1, ord_q(b))
  <= q - 1 < q, so for every prime q some residue of m survives: the
  constellation { b, b^2, ..., b^n } has no fixed prime divisor for any n.
  By Dickson's conjecture (equivalently Hardy-Littlewood / Schinzel's
  Hypothesis H) there are then infinitely many m for every n, so a(n) is
  defined for all n and a find CONFIRMS the guiding conjecture and can
  never refute it.  A110096's entry records the Dickson half of this
  (Charles R Greathouse IV, Oct 11 2011).

  THE TWO BASES ARE NOT THE SAME PROBLEM, and ord is what separates them.

      ord_q(4) = ord_q(2) / gcd(2, ord_q(2))  <=  (q-1)/2   for every odd q

  -- if d = ord_q(2) is even then ord_q(4) = d/2 <= (q-1)/2, and if d is
  odd then ord_q(4) = d, an odd divisor of the even number q-1, so again
  d <= (q-1)/2.  Meanwhile ord_q(2) itself reaches q-1 at every q for which
  2 is a primitive root.  So at b = 2 and q <= n+1 with 2 primitive mod q,
  w = q - 1: EVERY nonzero residue dies and m must be DIVISIBLE by q.  From
  n >= 4 that forces 3 | m and 5 | m, and with m odd every term of A110096
  above the exception zone is 15 mod 30 -- an observation A193109 records
  without proof, which is this lemma.  At b = 4 nothing of the sort
  happens: 2 of 3 residues survive mod 3 and 3 of 5 mod 5.  The b = 2 wheel
  is about 3,200x sparser than the b = 4 wheel at the production filters,
  and that is not a detail: it sets the line rate, the table sizes and the
  singular series all at once, in opposite directions that nearly cancel.

  THE EXCEPTION ZONE is real and small.  "q divides the value, so the value
  is composite" needs the value to EXCEED q.  It does not for the smallest
  terms: A110096's a(1) = 1 survives because 1 + 2^1 = 3 IS the prime 3,
  though m = 1 is killed by the q = 3 rule at every n >= 1.  The oracle
  therefore sweeps WITHOUT the wheel below K_FLOOR, and both engines refuse
  to run at or below max(K_FLOOR, sieve depth).

Gates in this file: G1 (the frozen knowns reproduce, are monotone, and sit
on the wheel above the floor), G2 (the small terms are re-derived
exhaustively from the bare definition), G2b (the w(q,n,b) formula equals
direct divisibility), G2c (admissibility, and the ord_q(4) <= (q-1)/2
lemma the two families' costs turn on).
"""

from sympy import isprime, n_order, primerange

# The two families, keyed by base.  Both are `more` sequences whose terms
# were re-verified against the OEIS export of 2026-08-22 the day this
# project was built.
FAMILIES = {
    4: {"oeis": "A130003",
        "keywords": "nonn,hard,more",
        "author": "Farideh Firoozbakht, May 30 2007",
        "frontier_by": "Jens Kruse Andersen, Jun 08 2007",
        "link": "Rivera, Puzzle 403"},
    2: {"oeis": "A110096",
        "keywords": "nonn,more",
        "author": "Joseph L. Pe, Sep 05 2005",
        "frontier_by": "Bert Dobbelaere, Apr 24 2021",
        "link": "A193109 (the exactly-n variant), A165235 (= a(n+1) + 2)"},
}

# A130003, as published: least m with m + 4^k prime for k = 1..n.
# a(10)-a(14) are one value, 4503, found as a(10); a(11)-a(14) rode along
# with it and were never separately searched for.
KNOWN_4 = {1: 1, 2: 1, 3: 3, 4: 7, 5: 7, 6: 15, 7: 37, 8: 163, 9: 177,
           10: 4503, 11: 4503, 12: 4503, 13: 4503, 14: 4503,
           15: 833021343,
           16: 12465115083,
           17: 95854279610863,
           18: 1158174141556287}

# A110096, as published: least m with m + 2^k prime for k = 1..n.
# Riders: a(2), a(4), a(6), a(8), a(13) and a(16) each repeat their
# predecessor.
KNOWN_2 = {1: 1, 2: 1, 3: 3, 4: 3, 5: 15, 6: 15, 7: 1605, 8: 1605,
           9: 19425,
           10: 2397347205,
           11: 153535525935,
           12: 29503289812425,
           13: 29503289812425,
           14: 32467505340816975,
           15: 143924005810811655,
           16: 143924005810811655}

KNOWN = {4: KNOWN_4, 2: KNOWN_2}

# NEITHER family carries a published bound of any kind -- no upper bound at
# any open n, and no searched-empty lower bound beyond the last term.  The
# floor for the next term is therefore monotonicity alone, which is free:
# the conditions nest, so a(n+1) >= a(n).
PUBLISHED_BOUNDS = {4: {}, 2: {}}

OPEN_N = {4: [19, 20, 21, 22], 2: [17, 18, 19, 20]}

# The wheel argument has an exception zone below this m (a value can BE the
# small prime that would otherwise divide it), so the engines refuse to run
# there and the oracle covers it by brute force.
K_FLOOR = 10 ** 4

# The single composite that keeps each family's next term open: the value
# at k = n+1 on the last published term.  Gate G1 asserts both.
THE_WALL = {4: (1158174141556287, 19), 2: (143924005810811655, 17)}


def value(m, k, b):
    return m + b ** k


def run_length(m, b, cap=64):
    """Largest r <= cap with m + b^k prime for every k = 1..r."""
    r = 0
    while r < cap and isprime(value(m, r + 1, b)):
        r += 1
    return r


def forbidden_m_residues(q, n, b):
    """K(q,n,b), computed DIRECTLY from divisibility -- the definition.

    Not the negate-the-orbit construction the engines use: the parity gate
    between the two is what makes the construction trustworthy.
    """
    out = set()
    for m in range(q):
        for k in range(1, n + 1):
            if (m + b ** k) % q == 0:
                out.add(m)
                break
    return out


def w(q, n, b):
    """|K(q,n,b)| by the closed form proved in the module docstring."""
    if b % q == 0:
        return 1
    return min(n, n_order(b, q))


def wheel_residues(n, b, p1):
    """Every m mod W that survives all primes q <= p1, by brute force.

    W = product of the primes <= p1.  This is the oracle's version: it
    walks the whole period.  The engines build the same set by CRT lifting
    and are gated against this on small p1.
    """
    W = 1
    for q in primerange(2, p1 + 1):
        W *= q
    killed = {q: forbidden_m_residues(q, n, b) for q in primerange(2, p1 + 1)}
    return W, [r for r in range(W)
               if all(r % q not in killed[q] for q in killed)]


def first_m(n, b, lo=1, hi=None):
    """Least m in [lo, hi] with run_length(m, b) >= n, by definition.

    The literal definition swept one integer at a time -- the slowest thing
    in this project, and the reason G2 only covers the small terms.
    """
    m = lo
    while hi is None or m <= hi:
        if run_length(m, b, cap=n) >= n:
            return m
        m += 1
    return None


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, each ladder is monotone,
    every term above the floor survives the small-prime wheel, and the wall
    that keeps the next term open is composite."""
    parts = []
    for b in sorted(FAMILIES):
        known = KNOWN[b]
        prev = 0
        for n in sorted(known):
            m = known[n]
            r = run_length(m, b, cap=n + 3)
            if r < n:
                return False, (f"G1 FAIL: {FAMILIES[b]['oeis']} a({n}) = {m} "
                               f"has run {r} < {n}")
            if m < prev:
                return False, (f"G1 FAIL: {FAMILIES[b]['oeis']} a({n}) = {m} "
                               f"< a({n-1}) = {prev}")
            if m >= K_FLOOR:
                W, res = wheel_residues(n, b, 13)
                if m % W not in set(res):
                    return False, (f"G1 FAIL: {FAMILIES[b]['oeis']} a({n}) = "
                                   f"{m} is killed by the wheel mod {W}")
            prev = m
        mm, kk = THE_WALL[b]
        if run_length(mm, b, cap=len(known) + 4) != max(known):
            return False, (f"G1 FAIL: {FAMILIES[b]['oeis']} frontier term "
                           f"{mm} does not reach exactly {max(known)}")
        if isprime(value(mm, kk, b)):
            return False, (f"G1 FAIL: {mm} + {b}^{kk} is prime, so "
                           f"{FAMILIES[b]['oeis']} a({kk}) would not be open")
        parts.append(f"{FAMILIES[b]['oeis']} a(1)-a({max(known)}) "
                     f"(wall {mm} + {b}^{kk} composite)")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every term satisfies "
                  "the definition, both ladders are monotone, every term "
                  "above the floor is on the wheel, and each frontier term "
                  "stops exactly where the sequence says it does")


def g2_rederive_small(upto=9):
    """Re-derive the small terms exhaustively from the bare definition."""
    done = []
    for b in sorted(FAMILIES):
        for n in range(1, upto + 1):
            got = first_m(n, b, lo=1, hi=KNOWN[b][n])
            if got != KNOWN[b][n]:
                return False, (f"G2 FAIL: {FAMILIES[b]['oeis']} re-derived "
                               f"a({n}) = {got} != {KNOWN[b][n]}")
        done.append(f"{FAMILIES[b]['oeis']} a(1)-a({upto})")
    return True, ("G2 ok: " + " and ".join(done) + " re-derived "
                  "exhaustively, one integer at a time, from the definition "
                  "alone")


def g2b_killed_set_size():
    """The closed form w(q,n,b) IS direct divisibility.

    Both bases, both regimes (n < ord and n >= ord), and the q | b case,
    because the engines size every table from this formula and a wrong size
    is either a missed kill or a lost candidate.
    """
    for b in sorted(FAMILIES):
        for n in (3, 7, 11, 17, 19, 21):
            for q in primerange(2, 120):
                direct = forbidden_m_residues(q, n, b)
                if len(direct) != w(q, n, b):
                    return False, (f"G2b FAIL: b={b} n={n} q={q}: direct "
                                   f"{len(direct)} != formula {w(q, n, b)}")
                built = {(-pow(b, k, q)) % q for k in range(1, n + 1)}
                if built != direct:
                    return False, (f"G2b FAIL: b={b} n={n} q={q}: "
                                   f"constructed {sorted(built)} != direct "
                                   f"{sorted(direct)}")
                if q % 2 and 0 in direct:
                    return False, (f"G2b FAIL: b={b} n={n} q={q}: m == 0 "
                                   f"(mod q) must be safe at odd q")
    return True, ("G2b ok: |K(q,n,b)| = min(n, ord_q(b)) (and 1 at q | b), "
                  "and the constructed orbit equals direct divisibility, for "
                  "every prime q < 120 at n = 3, 7, 11, 17, 19, 21 and both "
                  "bases; m == 0 (mod q) is safe at every odd q")


def g2c_admissible_and_the_order_lemma():
    """Bar 1 as an assertion, plus the lemma the two families' costs turn on.

    (a) w(q,n,b) < q for every prime q and every n up to well past the
        production filters, so the constellation is admissible and the
        sequences are conjecturally infinite -- a find CONFIRMS.
    (b) ord_q(4) = ord_q(2)/gcd(2, ord_q(2)) <= (q-1)/2, while ord_q(2)
        itself reaches q-1.  That is why b = 2 forces divisibility by the
        small primes and b = 4 does not.
    """
    forced = []
    for q in primerange(2, 400):
        for n in range(1, 26):
            for b in (2, 4):
                if w(q, n, b) >= q:
                    return False, (f"G2c FAIL: w({q},{n},{b}) = "
                                   f"{w(q, n, b)} >= q -- the constellation "
                                   f"would have a fixed prime divisor")
        if q == 2:
            continue
        d2, d4 = n_order(2, q), n_order(4, q)
        if d4 != d2 // (2 if d2 % 2 == 0 else 1):
            return False, f"G2c FAIL: ord_{q}(4) = {d4}, ord_{q}(2) = {d2}"
        if d4 > (q - 1) // 2:
            return False, (f"G2c FAIL: ord_{q}(4) = {d4} > (q-1)/2 at q = {q}")
        if d2 == q - 1 and q <= 20:
            forced.append(q)
    return True, ("G2c ok: w(q,n,b) < q at every prime q < 400 for n <= 25 "
                  "and both bases, so no fixed prime divisor exists and both "
                  "sequences are conjecturally infinite; ord_q(4) <= (q-1)/2 "
                  "always, while 2 is primitive at q = %s -- which is why "
                  "b = 2 forces those primes to divide m and b = 4 forces "
                  "nothing" % ", ".join(map(str, forced)))


GATES = [g1_knowns_reproduce, g2b_killed_set_size,
         g2c_admissible_and_the_order_lemma, g2_rederive_small]

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
