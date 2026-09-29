"""The oracle for the decimal ladders -- slow, obviously correct, sympy only.

Two OEIS entries, one family of forms, OPPOSITE LETTERS:

    A305740   a(n) is the smallest k such that 10^m*k + 1 is prime for all
              m in 1..n.            Jon E. Schoenfield, Jun 2018; a(12) by
                                    Giovanni Resta, Jun 2018
    A153431   a(n) is the smallest number m such that all n+1 numbers
              m*10^k+1 k=0,1,...,n are prime.
                                    Farideh Firoozbakht, Mar 2009; a(11)-a(13)
                                    by Don Reble, Jul 2022

A305740 calls the TERM k and the exponent m; A153431 calls the term m and
the exponent k.  Every surface a person reads uses each entry's own letter
(CONVENTIONS.md "Naming in an evidence file"); the code calls the swept
integer x and the exponent j, in both families:

    A(F, n) = least x >= 1 such that 10^j*x + 1 is prime for EVERY j in
              J(F, n),   J(A305740, n) = 1..n,   J(A153431, n) = 0..n.

So A305740 has n forms at index n and starts at n = 1; A153431 has n + 1
forms at index n and starts at n = 0 (its extra form is j = 0, x + 1).

THE NESTING.  J(A153431, n) = J(A305740, n) + {0}, so every x that
satisfies A153431's condition at n satisfies A305740's, and
A305740(n) <= A153431(n), with EQUALITY EXACTLY WHEN A305740(n) + 1 IS
PRIME (then A305740(n) meets the stricter condition too, and nothing
smaller can, since it would meet the weaker one).  G2d checks both facts on
every published index.

THE SHIFT.  10^j*(10x) + 1 = 10^(j+1)*x + 1, so "10x satisfies A153431's
condition at n - 1" is "x satisfies A305740's condition at n", and
A153431(n - 1) <= 10*A305740(n).  G2d checks it too.  (It is also what the
joint-sweep question in OPTIMIZATION_LOG.md turns on: A305740's filter n is
A153431's filter n - 1 restricted to multiples of 10.)

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW;
n_order, primerange) and the definition as written.

Five facts are PROVED here rather than assumed, because both engines and
the odds model are built on them.

  THE KILLED SET.  Fix a prime q and an exponent j.  If q = 2 or 5 then
  10^j == 0 (mod q) for j >= 1, the form is == 1 (mod q), and q never
  divides it; for j = 0 the form is x + 1, which q divides exactly when
  x == -1 (mod q).  For every other q, 10 is invertible and

      q | 10^j*x + 1   <=>   x == -10^(-j)  (mod q),

  so the residues of x that q kills are exactly

      K(q,n,F) = { -10^(-j) mod q : j in J(F, n) }

  and the engines sieve x against K(q,n,F) and nothing else.

  ITS SIZE.  -10^(-j) depends on j only mod d = ord_q(10), so
  w(q,n,F) = |K(q,n,F)| is the number of DISTINCT residues of J(F, n) mod d
  -- min(|J|, d) for the contiguous J here.  Small orders make weak primes:
  ord_3 = 1, ord_11 = 2, ord_37 = 3, ord_101 = 4, ord_41 = ord_271 = 5,
  ord_7 = ord_13 = 6, ord_73 = ord_137 = 8, ord_53 = ord_79 = 13,
  ord_31 = 15; a prime with 10 as a primitive root (7, 17, 19, 23, 29, 47,
  59, 61, 97, ...) kills |J| residues until |J| reaches q - 1.  G2b pins the
  count three ways.

  SATURATION.  K(q,n,F) is a SUBSET of K(q,n+1,F) (J grows by one exponent),
  equal from |J| >= d on.  So a filter-n sieve keeps a superset of what the
  filter-(n+1) sieve keeps, and an x whose run passes the filter -- a RIDER
  -- is found by the shorter sieve and settles every term up to its run at
  once (A305740's a(4) = a(5) = 7, A153431's a(6) = a(7) = 170926).

  FORCED DIVISIBILITY.  When w(q,n,F) = q - 1 only x == 0 (mod q) survives
  (0 is never killed: the value is then == 1 mod q).  That happens exactly
  when 10 is a primitive root of q and |J| >= q - 1: q = 7 from |J| = 6,
  17 from 16, 19 from 18, 23 from 22, 29 from 28.  And q = 2 for A153431 at
  every n (x + 1 must be odd; A153431's a(0) = 1 is inside the exception
  zone, where x + 1 IS the prime 2).  So the forced unit is
      A305740:  7 (n = 6..15), 7*17 (n = 16, 17), 7*17*19 (n = 18..21)
      A153431:  2*7 (n = 5..14), 2*7*17 (n = 15, 16), 2*7*17*19 (n = 17..20)
  and the forced CLASS is always 0 -- the engines sweep x = unit*x'.  They
  still DERIVE it per filter (forced_unit) and refuse anything else
  (assert_unit), because a unit is a coverage claim.  (A153431's own
  comment -- "for n > 3, 7 divides a(n)" -- is the n >= 5 case plus the
  fact that a(4) = 28 happens to be a multiple of 7.)

  ADMISSIBLE AT EVERY n.  Residue 0 is never killed by any q (x == 0 makes
  every form == 1 mod q), so w(q,n,F) <= q - 1 at every prime and every
  filter: no fixed prime divisor, a(n) exists for every n by Dickson's
  conjecture, and a find CONFIRMS the guiding conjecture.

  THE EXCEPTION ZONE.  "q divides the value, so it is composite" needs the
  value to EXCEED q.  The smallest value is 10^j0*x + 1 (10x + 1 for
  A305740, x + 1 for A153431), so a sieve to q2 is valid only from
  x > (q2 - 1)/10^j0; the engines refuse to run below that (k_floor) and the
  oracle covers the prefix by brute force.

Gates in this file: G1 (the frozen knowns reproduce from the bare
definition, are monotone, multiples of every forced prime, and each
frontier's wall is composite), G1b (this project's own finds, once there
are any), G2 (the small terms re-derived exhaustively), G2b (w three ways,
saturation, the order formula), G2c (admissibility and the forcing, prime
by prime), G2d (the nesting and the shift, on every published index).
"""

from sympy import isprime, n_order, primerange

# ---------------------------------------------------------------- families

# `j0`         the first exponent: J(F, n) = j0..n.
# `first_n`    the OEIS offset: the first index the sequence has a term at.
# `letter`     the letter the OEIS NAME gives the term (rule 5i).
# `forms`      the condition in the entry's own letters.
# Re-read from the local OEIS export (A305740 %I #14 Jun 26 2018, A153431
# %I #6 Jul 06 2022) on 2026-09-24.
FAMILIES = {
    "A305740": {"j0": 1, "first_n": 1, "letter": "k",
                "forms": "10^m*k + 1, m = 1..n",
                "keywords": "nonn,hard,more",
                "author": "Jon E. Schoenfield, Jun 23 2018",
                "frontier_by": "Giovanni Resta, Jun 25 2018 (a(12))",
                "also": ()},
    "A153431": {"j0": 0, "first_n": 0, "letter": "m",
                "forms": "m*10^k + 1, k = 0..n",
                "keywords": "nonn,more",
                "author": "Farideh Firoozbakht, Mar 15 2009",
                "frontier_by": "Don Reble, Jul 06 2022 (a(11)-a(13))",
                "also": ()},
}

ALIASES = {}

# The published terms, as published, indexed by the OEIS index n.
KNOWN = {
    "A305740": {1: 1, 2: 1, 3: 4, 4: 7, 5: 7, 6: 170716, 7: 170926,
                8: 26373004, 9: 247201983, 10: 10562770680,
                11: 118345066231, 12: 54717848613610},
    "A153431": {0: 1, 1: 1, 2: 1, 3: 4, 4: 28, 5: 28, 6: 170926,
                7: 170926, 8: 931371868, 9: 15538734736, 10: 89468493268,
                11: 6009549731752, 12: 89984938946056,
                13: 43000687652274618},
}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against and
# a fresh campaign starts from; these are the project's own claim, which the
# campaign carries in its checkpoint (`found`).  G1b re-checks whatever
# lands here from the bare definition.
FOUND = {fam: {} for fam in FAMILIES}

# A305740 carries one published bound, superseded by its own a(12): the
# comment "a(12) > 3*10^11" (Schoenfield, before Resta's a(12)).  Neither
# entry bounds any OPEN index, so the floor for the next term is
# monotonicity alone.
PUBLISHED_BOUNDS = {fam: {} for fam in FAMILIES}

# The wheel argument has an exception zone below this x (a value can BE the
# small prime that would otherwise divide it), so the engines refuse to run
# there and the oracle covers it by brute force.
K_FLOOR = 10 ** 4


def family(fam):
    """The canonical family key; raises on an unknown one."""
    fam = str(fam).upper()
    fam = ALIASES.get(fam, fam)
    if fam not in FAMILIES:
        raise KeyError(f"no family {fam!r}; the families are "
                       f"{', '.join(sorted(FAMILIES))}")
    return fam


def j0(fam):
    return int(FAMILIES[family(fam)]["j0"])


def letter(fam):
    return FAMILIES[family(fam)]["letter"]


def exponents(fam, n):
    """J(F, n): the exponents the condition at index n asks about."""
    return list(range(j0(fam), int(n) + 1))


def nforms(fam, n):
    """How many conditions index n imposes: n for A305740, n + 1 for
    A153431 -- what the singular series exponent and the residue-list width
    are sized from."""
    return max(0, int(n) + 1 - j0(fam))


def index_of(fam, count):
    """The OEIS index whose condition is `count` consecutive forms from the
    first: count for A305740, count - 1 for A153431."""
    return int(count) + j0(fam) - 1


def rung(fam, i):
    """The multiplier of the i-th form (i = 1, 2, ...): 10^(j0 + i - 1).
    Independent of the filter: the i-th form is the same whatever filter it
    is sieved at, which is why one x line serves every filter."""
    i = int(i)
    if i < 1:
        raise ValueError(f"form {i} is not a form")
    return 10 ** (j0(fam) + i - 1)


def mults(fam, n):
    """The multipliers of the family at index n, ascending."""
    return [10 ** j for j in exponents(fam, n)]


def value(fam, x, j):
    """The form with exponent j at x: 10^j*x + 1."""
    return 10 ** int(j) * int(x) + 1


def run_length(fam, x, cap=64):
    """The largest INDEX n (at most `cap`) whose condition x meets: the
    consecutive exponents from j0 at which 10^j*x + 1 is prime, counted in
    the entry's own index -- so an A305740 x whose 10x + 1 is composite has
    run 0, and an A153431 x whose x + 1 is composite has run -1.

    THIS IS THE DEFINITION AS THE OEIS STATES IT, with no filter in it: a
    filter-n sweep sieves for index n, but the run of the x it finds may
    pass n -- a RIDER, one x settling several consecutive terms.
    """
    fam = family(fam)
    x = int(x)
    j = j0(fam)
    while j <= cap and isprime(10 ** j * x + 1):
        j += 1
    return j - 1


def forbidden_k_residues(q, n, fam):
    """K(q,n,F), computed DIRECTLY from divisibility -- the definition.

    Not the inverse-power construction the engines use: the parity gate
    between the two is what makes the construction trustworthy.
    """
    fam = family(fam)
    ms = mults(fam, n)
    out = set()
    for x in range(q):
        for m in ms:
            if (m * x + 1) % q == 0:
                out.add(x)
                break
    return out


def w(q, n, fam):
    """|K(q,n,F)| from the multipliers' residues: the distinct residues of
    10^j mod q over J that are nonzero (a multiple of q kills nothing)."""
    family(fam)
    return len({m % q for m in mults(fam, n) if m % q})


def w_count(q, n, fam):
    """The killed count from the proof in the module docstring: the number
    of distinct residues of J(F, n) mod ord_q(10), and for q = 2, 5 one
    residue exactly when j = 0 is in J.  The same quantity as `w` by a
    different route (orders, not residues)."""
    q = int(q)
    js = exponents(fam, n)
    if q in (2, 5):
        return 1 if 0 in js else 0
    d = int(n_order(10, q))
    return len({j % d for j in js})


def forced_primes(fam, n, upto=64):
    """The primes forced at index n: those that kill every nonzero residue."""
    return [q for q in primerange(2, upto) if w(q, n, fam) == q - 1]


def wheel_residues(fam, n, p1):
    """Every x mod W that survives all primes q <= p1, by brute force.
    W = product of the primes <= p1.  The oracle's version walks the whole
    period; the engines build the same set by CRT lifting."""
    W = 1
    for q in primerange(2, p1 + 1):
        W *= q
    killed = {q: forbidden_k_residues(q, n, fam) for q in primerange(2, p1 + 1)}
    return W, [r for r in range(W)
               if all(r % q not in killed[q] for q in killed)]


def first_x(fam, n, lo=1, hi=None):
    """Least x in [lo, hi] with run_length(fam, x) >= n, by definition.
    The literal definition swept one integer at a time -- the slowest
    thing in this project, and why G2 only covers the small terms."""
    x = int(lo)
    while hi is None or x <= hi:
        if run_length(fam, x, cap=n) >= n:
            return x
        x += 1
    return None


# The single composite that keeps each family's next term open: the form
# after the frontier's last, on the frontier term.  G1 asserts it.
THE_WALL = {fam: (KNOWN[fam][max(KNOWN[fam])], max(KNOWN[fam]) + 1)
            for fam in FAMILIES}


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, each ladder is monotone,
    every term is a multiple of every prime forced there (outside the
    exception zone), and the wall that keeps the next term open is
    composite."""
    parts = []
    for fam in FAMILIES:
        known = KNOWN[fam]
        prev = 0
        for n in sorted(known):
            x = known[n]
            r = run_length(fam, x, cap=n + 3)
            if r < n:
                return False, f"G1 FAIL: {fam} a({n}) = {x} has run {r} < {n}"
            if x < prev:
                return False, f"G1 FAIL: {fam} a({n}) = {x} < a({n-1}) = {prev}"
            # the forcing lemma needs every value to EXCEED q: the smallest
            # is 10^j0*x + 1 (A153431's a(0) = 1 has x + 1 = 2, the prime 2)
            vmin = 10 ** j0(fam) * x + 1
            for q in forced_primes(fam, n):
                if vmin > q and x % q:
                    return False, (f"G1 FAIL: {fam} a({n}) = {x} is not a "
                                   f"multiple of the forced prime {q}")
            prev = x
        xx, ii = THE_WALL[fam]
        if xx != known[max(known)] or ii != max(known) + 1:
            return False, f"G1 FAIL: THE_WALL for {fam} is not the frontier's"
        if run_length(fam, xx, cap=max(known) + 4) != max(known):
            return False, (f"G1 FAIL: {fam} frontier term {xx} does not reach "
                           f"exactly {max(known)}")
        if isprime(value(fam, xx, ii)):
            return False, (f"G1 FAIL: {fam}'s wall 10^{ii}*{xx} + 1 is prime, "
                           f"so a({ii}) would not be open")
        parts.append(f"{fam} a({min(known)})-a({max(known)})")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every published term "
                  "satisfies the definition, every ladder is monotone, every "
                  "term outside the exception zone is a multiple of every "
                  "prime forced at its index, and each frontier term stops "
                  "exactly where the sequence says it does (its wall "
                  "10^(n+1)*a(n) + 1 is composite)")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition: each x
    reaches EXACTLY its run (at least, for a rider carrying the next index
    too), the ladder continues monotonically from the published frontier,
    and every x obeys the forced primes."""
    parts = []
    for fam in FAMILIES:
        found = FOUND[fam]
        if not found:
            continue
        top = max(KNOWN[fam])
        prev = KNOWN[fam][top]
        for n in sorted(found):
            x = found[n]
            if n != top + 1:
                return False, (f"G1b FAIL: {fam} a({n}) does not continue the "
                               f"ladder from a({top})")
            rider = found.get(n + 1) == x
            r = run_length(fam, x, cap=n + 3)
            if (r < n) if rider else (r != n):
                return False, (f"G1b FAIL: {fam} a({n}) = {x} has run {r}, "
                               f"not {'at least' if rider else 'exactly'} {n}")
            if x < prev:
                return False, f"G1b FAIL: {fam} a({n}) = {x} < a({n-1})"
            for q in forced_primes(fam, n):
                if x % q:
                    return False, (f"G1b FAIL: {fam} a({n}) = {x} is not a "
                                   f"multiple of the forced prime {q}")
            prev, top = x, n
        parts.append(f"{fam} a({min(found)})-a({max(found)})")
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each from the bare definition the moment one "
                      "is entered in FOUND")
    return True, ("G1b ok: this project's finds " + "; ".join(parts) +
                  " -- each reaches exactly its run from the bare definition, "
                  "continues the ladder monotonically and obeys every forced "
                  "prime")


def g2_small_terms_from_the_definition():
    """Re-derive the small terms by sweeping x itself, one integer at a
    time, asking the OEIS question directly."""
    checked = []
    for fam in FAMILIES:
        for n in sorted(KNOWN[fam]):
            x = KNOWN[fam][n]
            if x > 200_000:
                continue
            got = first_x(fam, n, lo=1, hi=x)
            if got != x:
                return False, (f"G2 FAIL: {fam} a({n}) swept from 1 came out "
                               f"{got}, expected {x}")
            checked.append(f"{fam} a({n})")
    return True, ("G2 ok: " + ", ".join(checked) + " re-derived exhaustively "
                  "from x = 1 by the bare definition, including every term "
                  "inside the exception zone the engines refuse to sweep")


def g2b_killed_set_three_ways():
    """The order formula, the distinct-multiplier count and direct
    divisibility must agree at every prime and every filter, for both
    families; K grows with n; and it SATURATES once |J| reaches the order."""
    cases = 0
    for fam in FAMILIES:
        for n in list(range(j0(fam), 26)) + [30, 42]:
            for q in primerange(2, 120):
                wc = w_count(q, n, fam)
                if w(q, n, fam) != wc:
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: distinct "
                                   f"residues {w(q, n, fam)} != order count "
                                   f"{wc}")
                direct = forbidden_k_residues(q, n, fam)
                if len(direct) != wc:
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: divisibility "
                                   f"kills {len(direct)} residues, the order "
                                   f"count says {wc}")
                if n > j0(fam) and not forbidden_k_residues(q, n - 1, fam) <= direct:
                    return False, (f"G2b FAIL: {fam} q={q}: K(q,{n-1}) is not "
                                   f"a subset of K(q,{n})")
                if q not in (2, 5):
                    d = int(n_order(10, q))
                    if wc != min(nforms(fam, n), d):
                        return False, (f"G2b FAIL: {fam} n={n} q={q}: w = {wc}"
                                       f", not min(|J|, ord) = "
                                       f"{min(nforms(fam, n), d)}")
                cases += 1
    # the weak primes the docstring names really are weak
    orders = {q: int(n_order(10, q)) for q in (3, 7, 11, 13, 17, 19, 31, 37,
                                                41, 53, 73, 101)}
    want = {3: 1, 7: 6, 11: 2, 13: 6, 17: 16, 19: 18, 31: 15, 37: 3, 41: 5,
            53: 13, 73: 8, 101: 4}
    if orders != want:
        return False, f"G2b FAIL: the orders of 10 are {orders}, not {want}"
    return True, (f"G2b ok: w(q,n,F) = #distinct(J mod ord_q(10)) = min(|J|, "
                  f"ord) equals the distinct-multiplier count AND direct "
                  f"divisibility in {cases} (q, n, F) cases (q < 120, both "
                  f"families, n to 42); K(q,n) grows with n and saturates at "
                  f"|J| = ord_q(10); the weak primes are as stated (ord 3 = 1, "
                  f"11 = 2, 37 = 3, 101 = 4, 41 = 5, 13 = 6, 73 = 8, 53 = 13, "
                  f"31 = 15)")


def g2c_admissible_and_forced():
    """Residue 0 is never killed (so every filter is admissible), and the
    forced primes are EXACTLY those with 10 a primitive root once |J| has
    reached q - 1 -- plus 2 for A153431 -- at every filter to n = 40."""
    for fam in FAMILIES:
        for n in range(j0(fam), 41):
            want = []
            for q in primerange(2, 64):
                k = forbidden_k_residues(q, n, fam)
                if 0 in k:
                    return False, f"G2c FAIL: {fam} n={n} q={q} kills x == 0"
                if q == 2:
                    if (0 in exponents(fam, n)):
                        want.append(2)
                    continue
                if q == 5:
                    continue
                if int(n_order(10, q)) == q - 1 and nforms(fam, n) >= q - 1:
                    want.append(q)
            got = forced_primes(fam, n, upto=64)
            if got != want:
                return False, (f"G2c FAIL: {fam} n={n}: forced primes {got}, "
                               f"the primitive-root rule says {want}")
    # the units the docstring states, at the filters the campaigns reach
    tab = {("A305740", 13): [7], ("A305740", 16): [7, 17],
           ("A305740", 18): [7, 17, 19], ("A305740", 21): [7, 17, 19],
           ("A305740", 22): [7, 17, 19, 23],
           ("A153431", 14): [2, 7], ("A153431", 15): [2, 7, 17],
           ("A153431", 17): [2, 7, 17, 19], ("A153431", 21): [2, 7, 17, 19, 23]}
    for (fam, n), want in tab.items():
        if forced_primes(fam, n) != want:
            return False, (f"G2c FAIL: {fam} n={n}: forced {forced_primes(fam, n)}"
                           f", the docstring says {want}")
    return True, ("G2c ok: residue 0 survives every prime at every filter to "
                  "n = 40 of both families (admissible: Dickson gives a term at "
                  "every n and a find can only confirm it); the forced primes "
                  "are exactly the primes with 10 as a primitive root once "
                  "|J| >= q - 1, plus 2 for A153431 (its x + 1 form) -- 7 from "
                  "|J| = 6, 17 from 16, 19 from 18, 23 from 22 -- so the unit "
                  "is 7 / 119 / 2261 for A305740 and 14 / 238 / 4522 for "
                  "A153431 at the filters the campaigns reach")


def g2d_nesting_and_shift():
    """The two identities between the entries, on every published index.

      NESTING: A305740(n) <= A153431(n), with equality exactly when
               A305740(n) + 1 is prime.
      SHIFT:   10*x meets A153431's condition at n - 1 exactly when x meets
               A305740's at n, so A153431(n - 1) <= 10*A305740(n); checked on
               the terms themselves, and as a statement about the forms.
    """
    a, b = KNOWN["A305740"], KNOWN["A153431"]
    both = sorted(set(a) & set(b))
    for n in both:
        if a[n] > b[n]:
            return False, (f"G2d FAIL: A305740({n}) = {a[n]} exceeds "
                           f"A153431({n}) = {b[n]}")
        eq = a[n] == b[n]
        if eq != bool(isprime(a[n] + 1)):
            return False, (f"G2d FAIL: at n = {n} equality is {eq} but "
                           f"A305740({n}) + 1 prime is {isprime(a[n] + 1)}")
        if n - 1 in b and b[n - 1] > 10 * a[n]:
            return False, (f"G2d FAIL: A153431({n-1}) = {b[n-1]} exceeds "
                           f"10*A305740({n}) = {10 * a[n]}")
    for n in sorted(a):
        x = a[n]
        if n - 1 >= 0 and run_length("A153431", 10 * x, cap=n + 2) < n - 1:
            return False, (f"G2d FAIL: 10*A305740({n}) does not meet "
                           f"A153431's condition at {n - 1}")
        if run_length("A153431", 10 * x, cap=n + 3) != \
                run_length("A305740", x, cap=n + 4) - 1:
            return False, (f"G2d FAIL: the run of 10x in A153431 is not the "
                           f"run of x in A305740 less one at x = {x}")
    eqs = [n for n in both if a[n] == b[n]]
    return True, (f"G2d ok: A305740(n) <= A153431(n) at n = {both[0]}..{both[-1]}"
                  f", with equality exactly at n = {eqs} -- the indices where "
                  f"A305740(n) + 1 is prime; and 10x carries x's A305740 run "
                  f"less one into A153431 on every published term, so "
                  f"A153431(n - 1) <= 10*A305740(n) throughout")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce, g2b_killed_set_three_ways,
         g2c_admissible_and_forced, g2d_nesting_and_shift,
         g2_small_terms_from_the_definition]

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
