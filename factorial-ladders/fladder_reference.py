"""The oracle for the factorial ladders -- slow, obviously correct, sympy only.

    A(F, n) = least x >= 1 such that k!*x + s is prime for EVERY k = 1..n

Two families, one engine, three OEIS entries:

    A177013   k!*m - 1 prime, k = 1..n    Haga & Firoozbakht, May 2010
    A177014   k!*m + 1 prime, k = 1..n    Haga & Firoozbakht, May 2010
                                          (a(10) corrected by Schoenfield, 2018)

and the second settles a third entry for free:

    A226935(n) = A177014(n) + 1    "least prime p(1) beginning a chain of
                                    primes p(i) = i*p(i-1) - (i-1), i = 2..n"

THE CHAIN IDENTITY.  Unrolling p(i) = i*p(i-1) - (i-1) from p(1) = p gives,
by induction, p(i) = i!*(p - 1) + 1: it holds at i = 1, and if
p(i-1) = (i-1)!*(p-1) + 1 then i*p(i-1) - (i-1) = i!*(p-1) + i - (i-1)
= i!*(p-1) + 1.  So "p(1), ..., p(n) all prime" is exactly "k!*m + 1 prime
for k = 1..n" at m = p - 1, and the least such prime p is the least such m
plus one -- p = m + 1 is itself the k = 1 value, so it is prime whenever m
qualifies.  A226935 = A177014 + 1 at every index, gated (G2d) against the
published table AND by re-running the chain on the shifted integer.  (No
OEIS entry exists for the analogous chain p(i) = i*p(i-1) + (i-1), which
would be A177013 - 1; a find on A177013 settles that entry alone.)

THE SHAPE.  This is the same linear ladder this repository has hunted five
times -- one unknown x, a list of multipliers, a fixed sign -- with the
multiplier list

    mults(n) = [ 1!, 2!, ..., n! ].

The published term IS x: there is no L(n) in front of it, so every filter
n sweeps the SAME line, and a find at filter n hands the next filter its
floor without re-denominating anything (unlike the lcm ladders, where
N = lcm(1..n)*x made each filter a different line).  What changes with the
filter is the sieve: more multipliers, so more killed residues per prime.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Five facts are PROVED here rather than assumed, because both engines and
the odds model are built on them.

  THE KILLED SET.  Fix a prime q and a multiplier m = k!.  If k >= q then
  q | k!, the form k!*x + s is congruent to s (mod q), and |s| = 1 < q, so
  that form is NEVER divisible by q: a rung whose multiplier q divides
  kills nothing.  For k < q, k! is invertible mod q and

      q | k!*x + s   <=>   x == -s * (k!)^-1  (mod q),

  so the residues of x that q kills are exactly

      K(q,n,F) = { -s * (k!)^-1 mod q : 1 <= k <= min(n, q - 1) }

  and the engines sieve x against K(q,n,F) and nothing else.

  ITS SIZE.  Inversion and negation are bijections of (Z/q)^*, so
  w(q,n) = |K(q,n,F)| is the number of DISTINCT residues among
  1!, 2!, ..., min(n, q-1)! mod q -- the same for both signs, which is why
  the two families share one singular series (G2c).  There is no closed
  form: consecutive factorials collide mod q whenever a product of
  consecutive integers is 1 mod q (5! == 1! mod 7, 4! == 2! mod 11), and
  they do so often -- only 5 of 1!..10! are distinct mod 11, and 9 of
  1!..12! mod 13.  `w_count` counts them; G2b pins that count against the
  distinct-multiplier count and against direct divisibility.

  SATURATION.  For n >= q - 1 every further multiplier is 0 mod q, so
  w(q,n) = w(q,q-1) for all n >= q - 1: a prime's kill set stops growing
  once the ladder passes it.  For q > n it grows by at most one per rung.
  Either way K(q,n) is a SUBSET of K(q,n+1), so a filter-n sieve keeps a
  superset of what the filter-(n+1) sieve keeps -- which is what lets a
  run longer than the filter (a RIDER) be found by the shorter sieve.

  FORCED DIVISIBILITY, AND ITS LIMIT.  When w(q,n) = q - 1 only
  x == 0 (mod q) survives.  q = 2 is forced at every n >= 1 (1! = 1 is the
  one nonzero residue) and q = 3 at every n >= 2 (1! = 1, 2! = 2).  NO
  OTHER PRIME IS EVER FORCED: for q >= 5 Wilson's theorem gives
  (q-1)! == -1, hence (q-2)! == 1 == 1! (mod q), so two of the q - 1
  candidate factorials share a residue and w(q,n) <= q - 2 < q - 1.  The
  forced unit is therefore 2 at n = 1 and 6 at every n >= 2, and it never
  changes again -- the opposite of the lcm ladders' sporadic forcing.  The
  engines still DERIVE it per filter (forced_unit) and refuse anything
  else (assert_unit), because a unit is a coverage claim.

  ADMISSIBLE AT EVERY n, FOR BOTH SIGNS.  x == 0 (mod q) gives every value
  == s != 0 (mod q), so residue 0 is never killed and w(q,n) <= q - 1 for
  every prime q.  No fixed prime divisor at any n; by Dickson's conjecture
  there are infinitely many x for every n, so a(n) is defined for all n and
  a find CONFIRMS the guiding conjecture and can never refute it.

  THE EXCEPTION ZONE is real and it bites at every filter.  "q divides the
  value, so the value is composite" needs the value to EXCEED q.  The
  smallest value is the k = 1 form, x + s, so a sieve to q2 is only valid
  from x > q2 - s; the engines refuse to run below that (k_floor), and the
  oracle covers the prefix by brute force.  The published small terms live
  there: A177013's a(1) = 3 has 1!*3 - 1 = 2, which IS the prime 2, and is
  odd although q = 2 is forced.

Gates in this file: G1 (the frozen knowns reproduce from the bare
definition, are monotone, are multiples of every forced prime, and each
frontier's wall is composite), G1b (this project's own finds, once there
are any), G2 (the small terms re-derived exhaustively), G2b (w(q,n) three
ways, both signs, plus saturation and the Wilson bound), G2c
(admissibility, sign-independence of w, the forcing -- 2 and 3 only, ever),
G2d (the derived identity A226935 = A177014 + 1 on every published term,
by the chain's own recurrence).
"""

from math import factorial

from sympy import isprime, primerange

# ---------------------------------------------------------------- families

# `sign`       the s in k!*x + s.
# `first_n`    the OEIS offset: the first index the sequence has a term at.
# `also`       the entry settled for free, and by what shift.
# Every entry was re-verified against the local OEIS export of 2026-09-14
# (%I revision stamps A177013 #13, A177014 #11, A226935 #23).
FAMILIES = {
    "A177013": {"sign": -1, "first_n": 1,
                "forms": "k!*m - 1, k = 1..n",
                "keywords": "more,nonn",
                "author": "Enoch Haga and Farideh Firoozbakht, May 20 2010",
                "frontier_by": "Enoch Haga and Farideh Firoozbakht, "
                               "May 20 2010",
                "also": ()},
    "A177014": {"sign": +1, "first_n": 1,
                "forms": "k!*m + 1, k = 1..n",
                "keywords": "more,nonn",
                "author": "Enoch Haga and Farideh Firoozbakht, May 20 2010",
                "frontier_by": "Enoch Haga and Farideh Firoozbakht, "
                               "May 20 2010; a(10) corrected by "
                               "Jon E. Schoenfield, Mar 07 2018",
                "also": (("A226935", +1),)},
}

# The rider spelling opens the same campaign as the entry it shifts.
ALIASES = {"A226935": "A177014"}

# The published terms, as published, indexed by the OEIS index n.
KNOWN = {
    "A177013": {1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1500, 7: 1500, 8: 154770,
                9: 1656252, 10: 3240034842},
    "A177014": {1: 1, 2: 1, 3: 1, 4: 18, 5: 18, 6: 8628, 7: 748668,
                8: 2506980, 9: 228698250, 10: 228698250},
}

# The DERIVED entry, as published, so its identity can be gated.
KNOWN_ALSO = {
    # A226935(n) = A177014(n) + 1: least prime p(1) with p(i) = i*p(i-1) -
    # (i-1) prime for i = 1..n
    "A226935": {1: 2, 2: 2, 3: 2, 4: 19, 5: 19, 6: 8629, 7: 748669,
                8: 2506981, 9: 228698251, 10: 228698251},
}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against and
# a fresh campaign starts from; these are the project's own claim, which the
# campaign carries in its checkpoint (`found`) and promotes its frontier
# from at runtime.  G1b re-checks whatever lands here from the bare
# definition.  A177013's eight came from the one campaign of 2026-09-16
# (RESULTS.md): a(11)..a(16) inside its first minute, a(17) at 24 minutes
# and a(18) at 5.75 hours.
FOUND = {fam: {} for fam in FAMILIES}
FOUND["A177013"] = {11: 83398005540,
                    12: 7740678645990,
                    13: 476382545091120,
                    14: 985173408688560,
                    15: 107596829892570252,
                    16: 744858063184134930,
                    17: 159027369950870799240,
                    18: 1639203889936938872760}
# A177014's eight on six integers, 2026-09-16/18: a(13) = a(14) = a(15) is
# one x with run 15 (a rider, as the published a(9) = a(10) is), and a(18)
# landed 32 campaign hours in, at 4.7x its median.  Each is A226935 at the
# same index, less one.
FOUND["A177014"] = {11: 133493208618,
                    12: 946564216260,
                    13: 63877984659108,
                    14: 63877984659108,
                    15: 63877984659108,
                    16: 2356745767044800940,
                    17: 118296999554873123520,
                    18: 30911690086525348609590}

# Neither entry carries a published bound of any kind -- no upper bound at
# any open n, and no searched-empty lower bound beyond the last term.  The
# floor for the next term is therefore monotonicity alone, which is free:
# the conditions nest, so a(n+1) >= a(n).
PUBLISHED_BOUNDS = {fam: {} for fam in FAMILIES}

# The open terms: the four indices past each family's published frontier.
OPEN_N = {fam: [max(KNOWN[fam]) + i for i in range(1, 5)] for fam in FAMILIES}

# The wheel argument has an exception zone below this x (a value can BE the
# small prime that would otherwise divide it), so the engines refuse to run
# there and the oracle covers it by brute force.
K_FLOOR = 10 ** 4

# The single composite that keeps each family's next term open: the value at
# the rung after the frontier, on the frontier term.  Gate G1 asserts it.
THE_WALL = {fam: (KNOWN[fam][max(KNOWN[fam])], max(KNOWN[fam]) + 1)
            for fam in FAMILIES}


def family(fam):
    """The canonical family key, aliases resolved; raises on an unknown one."""
    fam = str(fam).upper()
    fam = ALIASES.get(fam, fam)
    if fam not in FAMILIES:
        raise KeyError(f"no family {fam!r}; the families are "
                       f"{', '.join(sorted(FAMILIES))} (aliases "
                       f"{', '.join(sorted(ALIASES))})")
    return fam


def sign(fam):
    return int(FAMILIES[family(fam)]["sign"])


def rungs_from(fam):
    """The index of the first rung that is a condition -- always 1 here."""
    family(fam)
    return 1


def rung(n, i):
    """The multiplier of the i-th form: i!.

    Family-independent, and independent of the filter n too -- the i-th form
    is k!*x + s whatever filter it is sieved at, which is why one x line
    serves every filter.  `n` stays in the signature so the engines can ask
    for a rung PAST their filter (a rider is decided by running the chain
    on): it is validated, not used.
    """
    n, i = int(n), int(i)
    if n < 0 or i < 1:
        raise ValueError(f"rung {i} at filter {n} is not a form")
    return factorial(i)


def mults(fam, n):
    """The multipliers of the family at index n -- the conditions a(n) must
    satisfy.  Ascending: 1! < 2! < ... < n!."""
    family(fam)
    return [rung(n, i) for i in range(1, int(n) + 1)]


def nforms(fam, n):
    """How many conditions the filter n imposes: what the singular series
    exponent and the residue-list width are sized from."""
    family(fam)
    return max(0, int(n))


def value(fam, x, i):
    """The i-th form at x: i!*x + s."""
    return factorial(int(i)) * int(x) + sign(fam)


def run_length(fam, x, cap=64):
    """Largest r <= cap with k!*x + s prime for every k <= r.

    Counted from rung 1, so an x whose very first form x + s is composite
    has run 0.  THIS IS THE DEFINITION AS THE OEIS STATES IT, with no filter
    in it: a filter-n sweep sieves for n conditions, but the run of the x it
    finds is a property of x alone and may pass n -- a RIDER, one x settling
    several consecutive terms (A177014's a(9) = a(10)).  The engines cap
    their classification at the filter; the launcher decides riders with
    this function, on the find.
    """
    fam = family(fam)
    s = sign(fam)
    x = int(x)
    r = 0
    while r < cap and isprime(factorial(r + 1) * x + s):
        r += 1
    return r


def forbidden_k_residues(q, n, fam):
    """K(q,n,F), computed DIRECTLY from divisibility -- the definition.

    Not the invert-and-negate construction the engines use: the parity gate
    between the two is what makes the construction trustworthy.
    """
    fam = family(fam)
    s = sign(fam)
    ms = mults(fam, n)
    out = set()
    for x in range(q):
        for m in ms:
            if (m * x + s) % q == 0:
                out.add(x)
                break
    return out


def w(q, n, fam):
    """|K(q,n,F)| as the number of distinct nonzero residues of the
    multipliers mod q.  G2b pins it against `w_count` and against direct
    divisibility."""
    family(fam)
    return len({m % q for m in mults(fam, n) if m % q})


def w_count(q, n):
    """The killed count from the proof in the module docstring: the number of
    distinct residues among 1!, ..., min(n, q-1)! mod q.

    Family-independent and sign-independent, which is why the two families
    share a singular series; the same quantity as `w` by a different route
    (the bound min(n, q-1) is the saturation argument, where `w` relies on
    k! % q being 0 for k >= q).
    """
    q, n = int(q), int(n)
    return len({factorial(k) % q for k in range(1, min(n, q - 1) + 1)})


def forcing_n(q, fam, n_max=200):
    """The least n at which the multipliers hit every nonzero residue mod q,
    so that x == 0 (mod q) is FORCED; None if that never happens below
    n_max -- which, by Wilson, is every q >= 5."""
    for n in range(1, n_max + 1):
        if w(q, n, fam) == q - 1:
            return n
    return None


def forced_primes(fam, n, upto=64):
    """The primes forced at filter n, in order: [2] at n = 1, [2, 3] after."""
    return [q for q in primerange(2, upto) if w(q, n, fam) == q - 1]


def wheel_residues(fam, n, p1):
    """Every x mod W that survives all primes q <= p1, by brute force.

    W = product of the primes <= p1.  This is the oracle's version: it walks
    the whole period.  The engines build the same set by CRT lifting and are
    gated against this on small p1.
    """
    W = 1
    for q in primerange(2, p1 + 1):
        W *= q
    killed = {q: forbidden_k_residues(q, n, fam) for q in primerange(2, p1 + 1)}
    return W, [r for r in range(W)
               if all(r % q not in killed[q] for q in killed)]


def first_x(fam, n, lo=1, hi=None):
    """Least x in [lo, hi] with run_length(fam, x) >= n, by definition.

    The literal definition swept one integer at a time -- the slowest thing
    in this project, and the reason G2 only covers the small terms.
    """
    x = int(lo)
    while hi is None or x <= hi:
        if run_length(fam, x, cap=n) >= n:
            return x
        x += 1
    return None


def chain(p, n):
    """A226935's chain from p(1) = p: [p(1), ..., p(n)] with
    p(i) = i*p(i-1) - (i-1), computed by the recurrence as the entry states
    it -- not by the closed form, which is what G2d is checking."""
    out = [int(p)]
    for i in range(2, int(n) + 1):
        out.append(i * out[-1] - (i - 1))
    return out


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, each ladder is monotone,
    every term is a multiple of every prime forced there (outside the
    exception zone), every term above the floor survives the small-prime
    wheel, and the wall that keeps the next term open is composite."""
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
            # The forcing lemma needs every value to EXCEED q, or the value
            # can BE the prime that divides it -- A177013's a(1) = 3 has
            # 1*3 - 1 = 2, which is why it is odd although q = 2 is forced
            # at every n.  The smallest value is the k = 1 form, x + s.
            vmin = x + sign(fam)
            for q in forced_primes(fam, n):
                if vmin > q and x % q:
                    return False, (f"G1 FAIL: {fam} a({n}) = {x} is not a "
                                   f"multiple of the forced prime {q}")
            if x >= K_FLOOR:
                W, res = wheel_residues(fam, n, 11)
                if x % W not in set(res):
                    return False, (f"G1 FAIL: {fam} a({n}) = {x} is killed by "
                                   f"the wheel mod {W}")
            prev = x
        xx, ii = THE_WALL[fam]
        if xx != known[max(known)] or ii != max(known) + 1:
            return False, (f"G1 FAIL: THE_WALL for {fam} is not the frontier "
                           f"term's next rung")
        if run_length(fam, xx, cap=max(known) + 4) != max(known):
            return False, (f"G1 FAIL: {fam} frontier term {xx} does not reach "
                           f"exactly {max(known)}")
        if isprime(value(fam, xx, ii)):
            return False, (f"G1 FAIL: {fam}'s wall {ii}!*{xx} {sign(fam):+d} "
                           f"is prime, so a({ii}) would not be open")
        parts.append(f"{fam} a({min(known)})-a({max(known)})")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every published term "
                  "satisfies the definition, every ladder is monotone, every "
                  "term outside the exception zone is a multiple of every "
                  "prime forced at its filter, every x above the floor is on "
                  "the wheel, and each frontier term stops exactly where the "
                  "sequence says it does (its wall is composite)")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition.

    Independent of the engines and of the evidence files: sympy alone says
    each x reaches EXACTLY its run, the ladder continues monotonically from
    the published frontier, and every x obeys the forced primes.  One x may
    settle several consecutive terms: the run must then reach every term the
    x carries and be exactly the last of them.
    """
    parts = []
    for fam in FAMILIES:
        found = FOUND[fam]
        if not found:
            continue
        top = max(KNOWN[fam])
        prev = KNOWN[fam][top]
        riders = []
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
                return False, f"G1b FAIL: {fam} a({n}) = {x} < a({n-1}) = {prev}"
            for q in forced_primes(fam, n):
                if x % q:
                    return False, (f"G1b FAIL: {fam} a({n}) = {x} is not a "
                                   f"multiple of the forced prime {q}")
            if rider:
                riders.append(f"a({n + 1}) = a({n})")
            prev, top = x, n
        parts.append(f"{fam} a({min(found)})-a({max(found)})"
                     + (f" ({', '.join(riders)} on one x)" if riders else ""))
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each from the bare definition the moment one "
                      "is entered in FOUND")
    return True, ("G1b ok: this project's finds " + "; ".join(parts) +
                  " -- each reaches exactly its run from the bare definition, "
                  "continues the ladder monotonically from the published "
                  "frontier and obeys every forced prime")


def g2_small_terms_from_the_definition():
    """Re-derive the small terms by sweeping x itself, one integer at a time,
    asking the OEIS question directly.  No substitution is involved in this
    project, so this is the definition and nothing else."""
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
    """The distinct-residue count, the saturation-bounded count and direct
    divisibility must all agree, at every prime and both signs -- and the
    two structural facts the engines and the wheel plan rest on must hold:
    SATURATION (w(q,n) = w(q,q-1) for n >= q-1, and K grows with n) and the
    WILSON BOUND (w(q,n) <= q - 2 for q >= 5).

    Three independent computations of the same set size: `w_count` is the
    proof's bound, `w` counts residues of the actual multipliers,
    `forbidden_k_residues` walks every residue and tests divisibility.  A
    disagreement is a wrong wheel, which is a coverage bug rather than a
    slow one.
    """
    cases = 0
    for n in list(range(1, 26)) + [30, 42, 43]:
        for q in primerange(2, 90):
            wc = w_count(q, n)
            for fam in FAMILIES:
                if w(q, n, fam) != wc:
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: distinct "
                                   f"residues {w(q, n, fam)} != w_count {wc}")
                direct = forbidden_k_residues(q, n, fam)
                if len(direct) != wc:
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: divisibility "
                                   f"kills {len(direct)} residues, w_count "
                                   f"says {wc}")
                if n > 1 and not forbidden_k_residues(q, n - 1, fam) <= direct:
                    return False, (f"G2b FAIL: {fam} q={q}: K(q,{n-1}) is not "
                                   f"a subset of K(q,{n})")
                cases += 1
            if q >= 5 and wc > q - 2:
                return False, (f"G2b FAIL: w({q},{n}) = {wc} exceeds q - 2, "
                               f"but 1! == (q-2)! mod q by Wilson")
            if n >= q - 1 and wc != w_count(q, q - 1):
                return False, (f"G2b FAIL: w({q},{n}) = {wc} != w({q},{q-1}) "
                               f"= {w_count(q, q-1)}: the kill set grew past "
                               f"saturation")
    # the collisions are real, not a rounding of "n": name a few
    if not (w_count(7, 6) == 4 and w_count(11, 10) == 5
            and w_count(13, 12) == 9):
        return False, ("G2b FAIL: the collision counts at q = 7, 11, 13 are "
                       "not 4, 5, 9 -- the factorials mod q are not what the "
                       "docstring says")
    return True, (f"G2b ok: w(q,n) = #distinct(1!..min(n,q-1)! mod q) equals "
                  f"the distinct-multiplier-residue count AND direct "
                  f"divisibility in {cases} (q, n, F) cases (q < 90, n to 43, "
                  f"both signs); K(q,n) grows with n; it SATURATES at "
                  f"n = q - 1; and w(q,n) <= q - 2 for every q >= 5 (Wilson: "
                  f"1! == (q-2)!), with the collisions as stated -- 4 of "
                  f"1!..6! distinct mod 7, 5 of 1!..10! mod 11, 9 of 1!..12! "
                  f"mod 13")


def g2c_admissible_and_forced():
    """Residue 0 is never killed (so every filter is admissible), w does not
    depend on the sign (so the families share a singular series), and the
    forcing is EXACTLY q = 2 from n = 1 and q = 3 from n = 2 -- no other
    prime is ever forced, at any filter to n = 44, so the unit is 6 for the
    whole hunt."""
    for n in range(1, 45):
        for q in primerange(2, 200):
            if w_count(q, n) > q - 1:
                return False, (f"G2c FAIL: w({q},{n}) = {w_count(q, n)} "
                               f"exceeds q - 1, so filter {n} is inadmissible")
            for fam in FAMILIES:
                if 0 in forbidden_k_residues(q, n, fam):
                    return False, (f"G2c FAIL: {fam} n={n} q={q} kills x == 0")
        if w_count(2, n) != 1:
            return False, f"G2c FAIL: q = 2 is not forced at n = {n}"
        if n >= 2 and w_count(3, n) != 2:
            return False, f"G2c FAIL: q = 3 is not forced at n = {n}"
        a = {q: len(forbidden_k_residues(q, n, "A177013"))
             for q in primerange(2, 60)}
        b = {q: len(forbidden_k_residues(q, n, "A177014"))
             for q in primerange(2, 60)}
        if a != b:
            return False, f"G2c FAIL: the killed-set SIZES differ by sign at n={n}"
        want = [2] if n == 1 else [2, 3]
        for fam in FAMILIES:
            if forced_primes(fam, n, upto=200) != want:
                return False, (f"G2c FAIL: the forced primes at n = {n} of "
                               f"{fam} are {forced_primes(fam, n, upto=200)}, "
                               f"not {want}")
    for q in (5, 7, 11, 13, 17, 19, 23):
        if forcing_n(q, "A177013") is not None:
            return False, f"G2c FAIL: q = {q} becomes forced at some n"
    return True, ("G2c ok: residue 0 survives every prime at every filter to "
                  "n = 44 (admissible, so Dickson gives a term at every n and "
                  "a find can only confirm it); the killed-set sizes are "
                  "sign-independent, so the two families share one singular "
                  "series; and the forcing is exactly q = 2 from n = 1 and "
                  "q = 3 from n = 2, with NO prime >= 5 ever forced (Wilson), "
                  "so the unit is 6 for the whole hunt and never changes")


def g2d_derived_identity():
    """A226935 = A177014 + 1 at every published index, from the bare
    definition of the DERIVED entry.

    Checked twice: against the published table of the rider, and by running
    the rider's own recurrence p(i) = i*p(i-1) - (i-1) from p(1) = m + 1 and
    requiring every p(i) prime AND equal to i!*m + 1 -- the closed form the
    identity rests on.  That is what makes a find on A177014 a find on two
    entries.
    """
    fam = "A177014"
    tab = KNOWN_ALSO["A226935"]
    for n in sorted(KNOWN[fam]):
        m = KNOWN[fam][n]
        p = m + 1
        if n in tab and tab[n] != p:
            return False, (f"G2d FAIL: A226935 a({n}) = {tab[n]}, but "
                           f"A177014 a({n}) + 1 = {p}")
        ch = chain(p, n)
        for i, pi in enumerate(ch, start=1):
            if pi != factorial(i) * m + 1:
                return False, (f"G2d FAIL: p({i}) by the recurrence is {pi}, "
                               f"not {i}!*{m} + 1")
            if not isprime(pi):
                return False, f"G2d FAIL: p({i}) = {pi} in the chain is composite"
    # and the LEAST claim: no prime below p starts a chain of length n
    for n in (4, 6):
        p = tab[n]
        for q in primerange(2, p):
            if all(isprime(v) for v in chain(q, n)):
                return False, (f"G2d FAIL: p = {q} < {p} starts a length-{n} "
                               f"chain, so A226935({n}) != A177014({n}) + 1")
    return True, ("G2d ok: A226935 = A177014 + 1 at a(1)-a(10), verified "
                  "against the rider's published table AND by running its "
                  "recurrence p(i) = i*p(i-1) - (i-1) from m + 1 (every link "
                  "prime and equal to i!*m + 1), with the least-claim checked "
                  "exhaustively at n = 4 and 6 -- so every A177014 find "
                  "settles two OEIS entries")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce, g2b_killed_set_three_ways,
         g2c_admissible_and_forced, g2d_derived_identity,
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
