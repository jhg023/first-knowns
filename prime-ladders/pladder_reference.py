"""The oracle for the prime ladders -- slow, obviously correct, sympy only.

    A(s, n) = least k >= 1 such that prime(i)*k + s is prime for ALL i = 1..n

    s = +1  ->  A084700   (Murthy 2003; a(11)-a(13) Phil Carmody, Mar 2004)
    s = -1  ->  A084701   (Murthy 2003; a(11) Robert G. Wilson v / Don
                           Reble, Jun 2003)

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Four facts are PROVED here rather than assumed, because both engines and
the odds model are built on them.  They are also what separates this
ladder from square-ladders, whose engine it otherwise shares: the rungs
are the PRIMES, and the primes are not a polynomial.

  THE KILLED SET.  Fix a prime q and write p_i = prime(i).  If q = p_i for
  some i <= n then the form p_i*k + s is congruent to s (mod q), and |s| = 1
  < q, so that form is NEVER divisible by q: the rung whose multiplier is
  q itself kills nothing.  For p_i != q,

      q | p_i*k + s   <=>   k == -s * p_i^-1  (mod q),

  so the residues of k that q kills are exactly

      K(q,n,s) = { -s * p_i^-1 mod q : 1 <= i <= n, p_i != q }

  and the engines sieve k against K(q,n,s) and nothing else.

  ITS SIZE, EXACTLY.  Inversion and negation are bijections of (Z/q)^*, so

      w(q,n,s) = |K(q,n,s)| = |{ p_i mod q : 1 <= i <= n, p_i != q }|

  -- the number of DISTINCT residues the first n primes other than q take
  mod q.  Three consequences, each used downstream:

    * w is INDEPENDENT OF s: K(q,n,-1) = -K(q,n,+1).  The two families
      have the same wheel sizes, the same survival curve and the same
      singular series; what differs is which residues die, never how many.
    * for q > p_n every p_i is a distinct nonzero residue, so w = n.  For
      q <= p_n the primes may collide mod q, so w <= min(n, q-1), with the
      inequality strict exactly when some nonzero residue is missed.
    * FORCED DIVISIBILITY.  When w(q,n,s) = q - 1 -- every nonzero residue
      mod q is the residue of some p_i, i <= n -- the only surviving k are
      k == 0 (mod q).  The first n primes cover the nonzero residues mod
      2 / 3 / 5 / 7 / 11 from n = 2 / 4 / 8 / 10 / 14 respectively
      (`forcing_n` below computes it), which is why the OEIS entries note
      a(n) == 0 (mod 30) for n >= 8 and why every candidate at the
      campaign filters is a multiple of 2310.  Mod 13 the residue 12 is
      first reached by 103 = prime(27), so 13 forces nothing until n = 27.
      The consequence for the engine is a wheel whose residue table is
      TINY -- 2,800 residues mod 223,092,870 at n = 14 against
      square-ladders' 1,088,640 -- and a candidate density of about 1e-6
      per unit of k line, which is what sets this project's line rate.

  ADMISSIBLE AT EVERY n, FOR BOTH SIGNS.  k == 0 (mod q) gives every value
  == s != 0 (mod q), so residue 0 is never killed and w(q,n,s) <= q - 1 < q
  for every prime q.  The constellation { p_i*k + s } therefore has no
  fixed prime divisor at any n; by Dickson's conjecture (equivalently
  Hardy-Littlewood / Schinzel's Hypothesis H) there are infinitely many k
  for every n, so a(n) is defined for all n and a find CONFIRMS the guiding
  conjecture and can never refute it.

  THE EXCEPTION ZONE is real and small.  "q divides the value, so the
  value is composite" needs the value to EXCEED q.  It does not for the
  smallest terms: A084700's a(3) = 2 is fine, but a candidate k = 3 at
  n = 3 has 2*3 + 1 = 7, which IS the prime 7 and would be killed by the
  q = 7 rule.  The oracle therefore sweeps WITHOUT the wheel below K_FLOOR,
  and both engines refuse to run at or below max(K_FLOOR, sieve depth).

Gates in this file: G1 (the frozen knowns reproduce, are monotone, and sit
on the wheel above the floor; each frontier's wall is composite), G1b
(this project's own finds, a(14)-a(17) of A084700, reach exactly their
run from the bare definition, continue the ladder monotonically above the
published frontier, sit on the wheel, and each stops at a composite), G2
(the small terms are re-derived exhaustively from the bare definition),
G2b (the w(q,n,s) formula equals direct divisibility, for both signs), G2c
(admissibility, sign-independence of w, and the forcing thresholds).
"""

from sympy import isprime, prime, primerange

# The two families, keyed by the sign of the additive constant.  Both are
# `more` sequences whose terms were re-verified against the OEIS export of
# 2026-09-01 the day this project was built.
FAMILIES = {
    +1: {"oeis": "A084700",
         "keywords": "more,nonn",
         "author": "Amarnath Murthy, Jun 08 2003",
         "frontier_by": "Phil Carmody (GenSv siever), Mar 08 2004",
         "note": "For n > 7, a(n) == 0 mod 30 (entry); proved here as the "
                 "forcing lemma"},
    -1: {"oeis": "A084701",
         "keywords": "more,nonn",
         "author": "Amarnath Murthy, Jun 08 2003",
         "frontier_by": "Robert G. Wilson v and Don Reble, Jun 15 2003",
         "note": "a(10) was reported by a Prime Curios page (entry)"},
}

# A084700, as published: least k with prime(i)*k + 1 prime for i = 1..n.
# a(3) rides on a(2) and a(5)-a(7) ride on a(4): 6 clears 11, 13 and 17
# for free and stops at 19*6 + 1 = 115.
KNOWN_PLUS = {1: 1, 2: 2, 3: 2, 4: 6, 5: 6, 6: 6, 7: 6,
              8: 192660,
              9: 437286240,
              10: 37202202450,
              11: 148684126500,
              12: 2258581791060,
              13: 161082438032880}

# A084701, as published: least k with prime(i)*k - 1 prime for i = 1..n.
# a(2) rides on a(1) and a(6), a(7) ride on a(5): 120 stops at
# 19*120 - 1 = 2279 = 43 * 53.
KNOWN_MINUS = {1: 2, 2: 2, 3: 4, 4: 6, 5: 120, 6: 120, 7: 120,
               8: 21972720,
               9: 827779590,
               10: 2481129210,
               11: 3894254360010}

KNOWN = {+1: KNOWN_PLUS, -1: KNOWN_MINUS}

# FOUND BY THIS PROJECT (2026-09-02, first campaign, RESULTS.md) and not yet
# in the OEIS: verified four ways at discovery time, evidenced under
# evidence/, and re-checked from the bare definition by G1b below.  Kept
# APART from KNOWN on purpose: KNOWN is the literature, which the model is
# validated against and a fresh campaign starts from; these are the
# project's own claim, which the campaign carries in its checkpoint
# (`found`) and promotes its frontier from at runtime.
FOUND = {+1: {14: 24581646307811670,
              15: 1183192161007235610,
              16: 161515890673488267840,
              17: 2446970377116913184460},
         -1: {}}

# NEITHER family carries a published bound of any kind -- no upper bound at
# any open n, and no searched-empty lower bound beyond the last term.  The
# floor for the next term is therefore monotonicity alone, which is free:
# the conditions nest, so a(n+1) >= a(n).
PUBLISHED_BOUNDS = {+1: {}, -1: {}}

# The open terms, counting this project's finds: a(18) of A084700 is the
# one the campaign is sweeping for.
OPEN_N = {+1: [18, 19, 20, 21], -1: [12, 13, 14, 15]}

# The wheel argument has an exception zone below this k (a value can BE the
# small prime that would otherwise divide it), so the engines refuse to run
# there and the oracle covers it by brute force.
K_FLOOR = 10 ** 4

# The single composite that keeps each family's next term open: the value
# at i = n+1 on the last published term.  Gate G1 asserts both.
THE_WALL = {+1: (161082438032880, 14), -1: (3894254360010, 12)}

_PRIMES = [int(p) for p in primerange(2, 1000)]      # prime(i) for i <= 168


def rung(i):
    """prime(i), the multiplier of the i-th form."""
    return _PRIMES[i - 1] if i <= len(_PRIMES) else int(prime(i))


def value(k, i, s):
    return rung(i) * k + s


def run_length(k, s, cap=64):
    """Largest r <= cap with prime(i)*k + s prime for every i = 1..r."""
    r = 0
    while r < cap and isprime(value(k, r + 1, s)):
        r += 1
    return r


def forbidden_k_residues(q, n, s):
    """K(q,n,s), computed DIRECTLY from divisibility -- the definition.

    Not the invert-and-negate construction the engines use: the parity gate
    between the two is what makes the construction trustworthy.
    """
    out = set()
    for k in range(q):
        for i in range(1, n + 1):
            if (rung(i) * k + s) % q == 0:
                out.add(k)
                break
    return out


def w(q, n, s=+1):
    """|K(q,n,s)| by the closed form proved in the module docstring: the
    number of distinct residues mod q among the first n primes other than
    q.  The sign is accepted for symmetry with the engines' signatures and
    ignored, because the count does not depend on it (G2c asserts that)."""
    return len({rung(i) % q for i in range(1, n + 1) if rung(i) != q})


def forcing_n(q, n_max=200):
    """The least n at which every nonzero residue mod q is hit by one of the
    first n primes (other than q), so that k == 0 (mod q) is FORCED; None
    if that does not happen below n_max."""
    for n in range(1, n_max + 1):
        if w(q, n) == q - 1:
            return n
    return None


def wheel_residues(n, s, p1):
    """Every k mod W that survives all primes q <= p1, by brute force.

    W = product of the primes <= p1.  This is the oracle's version: it
    walks the whole period.  The engines build the same set by CRT lifting
    and are gated against this on small p1.
    """
    W = 1
    for q in primerange(2, p1 + 1):
        W *= q
    killed = {q: forbidden_k_residues(q, n, s) for q in primerange(2, p1 + 1)}
    return W, [r for r in range(W)
               if all(r % q not in killed[q] for q in killed)]


def first_k(n, s, lo=1, hi=None):
    """Least k in [lo, hi] with run_length(k, s) >= n, by definition.

    The literal definition swept one integer at a time -- the slowest thing
    in this project, and the reason G2 only covers the small terms.
    """
    k = lo
    while hi is None or k <= hi:
        if run_length(k, s, cap=n) >= n:
            return k
        k += 1
    return None


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, each ladder is monotone,
    every term above the floor survives the small-prime wheel, and the wall
    that keeps the next term open is composite."""
    parts = []
    for s in sorted(FAMILIES, reverse=True):
        known = KNOWN[s]
        prev = 0
        for n in sorted(known):
            k = known[n]
            r = run_length(k, s, cap=n + 3)
            if r < n:
                return False, (f"G1 FAIL: {FAMILIES[s]['oeis']} a({n}) = {k} "
                               f"has run {r} < {n}")
            if k < prev:
                return False, (f"G1 FAIL: {FAMILIES[s]['oeis']} a({n}) = {k} "
                               f"< a({n-1}) = {prev}")
            if k >= K_FLOOR:
                W, res = wheel_residues(n, s, 13)
                if k % W not in set(res):
                    return False, (f"G1 FAIL: {FAMILIES[s]['oeis']} a({n}) = "
                                   f"{k} is killed by the wheel mod {W}")
            prev = k
        kk, ii = THE_WALL[s]
        if kk != known[max(known)] or ii != max(known) + 1:
            return False, (f"G1 FAIL: THE_WALL for {FAMILIES[s]['oeis']} is "
                           f"not the frontier term's next rung")
        if run_length(kk, s, cap=max(known) + 4) != max(known):
            return False, (f"G1 FAIL: {FAMILIES[s]['oeis']} frontier term "
                           f"{kk} does not reach exactly {max(known)}")
        if isprime(value(kk, ii, s)):
            return False, (f"G1 FAIL: {rung(ii)}*{kk}{s:+d} is prime, so "
                           f"{FAMILIES[s]['oeis']} a({ii}) would not be open")
        parts.append(f"{FAMILIES[s]['oeis']} a(1)-a({max(known)}) (wall "
                     f"{rung(ii)}*{kk}{s:+d} composite)")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every term satisfies "
                  "the definition, both ladders are monotone, every term "
                  "above the floor is on the wheel, and each frontier term "
                  "stops exactly where the sequence says it does")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition.

    Independent of the engines and of the evidence files: sympy alone says
    each k reaches EXACTLY its run (the value at i = n + 1 is composite, so
    the term is n and not more), the ladder continues monotonically from
    the published frontier, and every k sits on the small-prime wheel --
    at n >= 14 that means a multiple of 2310, the forcing lemma.  "Least"
    is not checkable here (that is the campaign's coverage claim,
    RESULTS.md); "is a term of the sequence with this index" is.
    """
    parts = []
    for s in sorted(FAMILIES, reverse=True):
        found = FOUND[s]
        if not found:
            continue
        top = max(KNOWN[s])
        prev = KNOWN[s][top]
        for n in sorted(found):
            k = found[n]
            if n != top + 1:
                return False, (f"G1b FAIL: {FAMILIES[s]['oeis']} a({n}) does "
                               f"not continue the ladder from a({top})")
            r = run_length(k, s, cap=n + 3)
            if r != n:
                return False, (f"G1b FAIL: {FAMILIES[s]['oeis']} a({n}) = {k} "
                               f"has run {r}, not exactly {n}")
            if k < prev:
                return False, (f"G1b FAIL: {FAMILIES[s]['oeis']} a({n}) = {k} "
                               f"< a({n-1}) = {prev}")
            W, res = wheel_residues(n, s, 13)
            if k % W not in set(res):
                return False, (f"G1b FAIL: {FAMILIES[s]['oeis']} a({n}) = {k} "
                               f"is killed by the wheel mod {W}")
            if n >= 14 and k % 2310:
                return False, (f"G1b FAIL: {FAMILIES[s]['oeis']} a({n}) = {k} "
                               f"is not a multiple of 2310 (forcing lemma)")
            if isprime(value(k, n + 1, s)):
                return False, (f"G1b FAIL: {rung(n + 1)}*{k}{s:+d} is prime, "
                               f"so {FAMILIES[s]['oeis']} a({n}) would be "
                               f"a({n + 1}) or more")
            prev, top = k, n
        parts.append(f"{FAMILIES[s]['oeis']} a({min(found)})-a({max(found)}) "
                     f"(stops at {rung(top + 1)}*k{s:+d}, composite)")
    return True, ("G1b ok: this project's finds " + "; ".join(parts) +
                  " -- each reaches exactly its run from the bare definition, "
                  "continues the ladder monotonically from the published "
                  "frontier, is on the wheel and a multiple of 2310")


def g2_rederive_small(upto=None):
    """Re-derive the small terms exhaustively from the bare definition.

    A084700 to a(8) = 192,660 and A084701 to a(7) = 120: its a(8) is
    21,972,720 and re-deriving that one integer at a time is minutes, which
    a gate may not cost.  G5 (pladder_search) re-derives a(8) and a(9) of
    both families through the CPU engine instead."""
    upto = upto or {+1: 8, -1: 7}
    done = []
    for s in sorted(FAMILIES, reverse=True):
        for n in range(1, upto[s] + 1):
            got = first_k(n, s, lo=1, hi=KNOWN[s][n])
            if got != KNOWN[s][n]:
                return False, (f"G2 FAIL: {FAMILIES[s]['oeis']} re-derived "
                               f"a({n}) = {got} != {KNOWN[s][n]}")
        done.append(f"{FAMILIES[s]['oeis']} a(1)-a({upto[s]})")
    return True, ("G2 ok: " + " and ".join(done) + " re-derived "
                  "exhaustively, one integer at a time, from the definition "
                  "alone")


def g2b_killed_set_size():
    """The closed form w(q,n,s) IS direct divisibility, for both signs.

    Both regimes (q <= p_n, where the primes may collide mod q, and
    q > p_n, where w = n), because the engines size every table from this
    formula and a wrong size is either a missed kill or a lost candidate.
    """
    for s in (+1, -1):
        for n in (3, 7, 11, 14, 16, 19):
            for q in primerange(2, 120):
                direct = forbidden_k_residues(q, n, s)
                if len(direct) != w(q, n, s):
                    return False, (f"G2b FAIL: s={s:+d} n={n} q={q}: direct "
                                   f"{len(direct)} != formula {w(q, n, s)}")
                built = {(-s * pow(rung(i), -1, q)) % q
                         for i in range(1, n + 1) if rung(i) % q}
                if built != direct:
                    return False, (f"G2b FAIL: s={s:+d} n={n} q={q}: "
                                   f"constructed {sorted(built)} != direct "
                                   f"{sorted(direct)}")
                if 0 in direct:
                    return False, (f"G2b FAIL: s={s:+d} n={n} q={q}: k == 0 "
                                   f"(mod q) must always be safe")
                if q > rung(n) and len(direct) != n:
                    return False, (f"G2b FAIL: s={s:+d} n={n} q={q} > p_n "
                                   f"but w = {len(direct)} != n")
    return True, ("G2b ok: |K(q,n,s)| = #distinct residues of the first n "
                  "primes (other than q) mod q, and the constructed set "
                  "equals direct divisibility, for every prime q < 120 at "
                  "n = 3, 7, 11, 14, 16, 19 and both signs; k == 0 (mod q) "
                  "always survives; w = n whenever q > prime(n)")


def g2c_admissible_and_forcing():
    """Bar 1 as an assertion, plus the two lemmas the engine turns on.

    (a) w(q,n,s) < q for every prime q and every n up to well past the
        production filters, so the constellation is admissible and both
        sequences are conjecturally infinite -- a find CONFIRMS.
    (b) w does not depend on s: K(q,n,-1) is the negative of K(q,n,+1),
        so the two families share every table size and the whole
        survival curve.
    (c) the forcing thresholds: 2, 3, 5, 7, 11 force k == 0 from
        n = 2, 4, 8, 10, 14, and 13 does not before n = 27 -- which is the
        a(n) == 0 (mod 30) the OEIS entries observe for n >= 8, proved.
    """
    for q in primerange(2, 400):
        for n in range(1, 31):
            if w(q, n) >= q:
                return False, (f"G2c FAIL: w({q},{n}) = {w(q, n)} >= q -- "
                               f"the constellation would have a fixed "
                               f"prime divisor")
    for q in primerange(2, 200):
        for n in (2, 5, 9, 14, 17, 24):
            kp = forbidden_k_residues(q, n, +1)
            km = forbidden_k_residues(q, n, -1)
            if {(-u) % q for u in kp} != km:
                return False, (f"G2c FAIL: q={q} n={n}: K(-1) is not the "
                               f"negative of K(+1)")
    want = {2: 2, 3: 4, 5: 8, 7: 10, 11: 14, 13: 27}
    got = {q: forcing_n(q) for q in want}
    if got != want:
        return False, f"G2c FAIL: forcing thresholds {got}, expected {want}"
    for s in FAMILIES:
        for n, k in KNOWN[s].items():
            for q in (2, 3, 5, 7, 11):
                if n >= want[q] and k % q:
                    return False, (f"G2c FAIL: {FAMILIES[s]['oeis']} a({n}) = "
                                   f"{k} is not divisible by {q}, which the "
                                   f"forcing lemma requires from n = "
                                   f"{want[q]}")
    return True, ("G2c ok: w(q,n) < q at every prime q < 400 for n <= 30, so "
                  "no fixed prime divisor exists and both sequences are "
                  "conjecturally infinite; K(q,n,-1) = -K(q,n,+1) at every "
                  "q < 200 for six filters; 2, 3, 5, 7, 11 force k == 0 from "
                  "n = 2, 4, 8, 10, 14 and 13 only from n = 27, and every "
                  "published term obeys it -- a(n) == 0 (mod 2310) from "
                  "n = 14")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce, g2b_killed_set_size,
         g2c_admissible_and_forcing, g2_rederive_small]

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
