"""The oracle for the clique ladders -- slow, obviously correct, sympy only.

    a(n) = least x > a(n-1) such that  x + a(i) + 1  is prime for EVERY i < n
           (and, per family, one extra condition on x alone)

Join two integers when their sum plus one is prime.  Each sequence here is
the GREEDY CLIQUE of that graph from a given first term: the lexicographically
first infinite set in which every pair is joined.  Six OEIS entries hunt it
from different starts and with different extra conditions, and five more are
the same integers under an affine map:

    A093483   start 2                       Murthy 2004; Reble 2012   hard,nice
    A103828   start 1 (odd)                 Kehowski 2006; Reble 2021
    A037100   start 4 (even)                Rivera; Reble 2019
    A119752   start 2, and 2x + 1 prime     Kehowski 2006; D. Johnson 2008   hard
    A119751   start 1, and 2x + 1 prime     Kehowski 2006; D. Johnson 2008   hard
    A133761   start 5, and x itself prime   Ekl 2008; Reble 2015

    A180565 = 2*A093483 + 1    A120403 = A119752 + 1    A113875 = 2*A119751 + 1
    A115760 = 2*A103828 + 1    A128933 = A103828 + 1

THE SHAPE.  At index n the conditions on x are n - 1 SHIFT forms whose
offsets are the sequence's own earlier terms, plus the family's extra form:

    forms(F, n) = [ extra(F) ... ,  x + a(1) + 1,  ...,  x + a(n-1) + 1 ]

Every form is linear, a*x + b with a in {1, 2}, so this is the simultaneous-
primality ladder this repository has hunted eight times -- with one
difference that reaches everywhere: THE FORM LIST IS NOT A FUNCTION OF n.  It
is a function of the terms already found, so the filter for a(n+1) does not
exist until a(n) does, the engine is rebuilt at every find, and an error in
one term would poison every later one.  That last fact is why a find here is
never taken from the engine: it is re-derived by this file, from the bare
definition, against the whole prefix.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Facts PROVED or CHECKED here rather than assumed, because both engines and
the odds model are built on them.

  THE KILLED SET.  For a prime q and a form a*x + b with q not dividing a,
  q | a*x + b  <=>  x == -b * a^-1 (mod q); a form with q | a (only 2x + 1
  at q = 2) is == b != 0 and never divisible.  So

      K(q,n,F) = { -b * a^-1 mod q : (a, b) in forms(F, n), q not | a }

  and the engines sieve x against K(q,n,F) and nothing else.  w(q,n,F) is
  its size.  K(q,n) is a SUBSET of K(q,n+1): a new term adds one form and
  removes none.

  ADMISSIBILITY IS NOT A THEOREM HERE.  In every other ladder of this
  repository residue 0 (or the forced class) provably survives every prime.
  Here nothing proves that the offsets a(i) + 1 leave a residue free modulo
  every q: if at some n they cover all of Z/q, NO x satisfies the conditions
  and the sequence is FINITE -- which would be a result, and a bigger one
  than a term.  So admissibility is CHECKED at every filter (G2c, and by the
  launcher at every promotion: `admissible`), never assumed.  What can be
  said: a prime q > nforms cannot be covered, so only finitely many primes
  need checking at each filter.

  FORCING IS TO A RESIDUE, NOT TO ZERO.  When w(q,n,F) = q - 1 exactly one
  residue class survives q -- x == 2 (mod 3) for A093483 from n = 3, because
  x + 3 kills 0 and x + 5 kills 1.  The surviving class is not 0, so the
  "unit" of the other ladders (sweep the multiples of 6) does not exist
  here: the engines sweep x itself, and the wheel takes the forced primes
  first because a prime that keeps one residue in q is the best value a
  wheel can buy (clique_search.forced_unit is 1 at every filter, derived).

  THE EXCEPTION ZONE.  "q divides the value, so the value is composite"
  needs the value to EXCEED q.  The smallest value at every filter is at
  least x (the forms are x + a(i) + 1 >= x + 2, 2x + 1, and x itself), so a
  sieve to q2 is valid from x > q2; the engines refuse to run below that
  (k_floor), and the oracle covers the prefix by brute force.  The early
  terms live there.

  THE DERIVED ENTRIES are the same integers under an affine map, because
  the map carries one definition onto the other: with b = 2a + 1,
  (b_i + b_j)/2 = a_i + a_j + 1 (A180565, A115760; and A113875, whose
  entries must also be prime, which is A119751's extra form 2x + 1); with
  b = a + 1, b_i + b_j - 1 = a_i + a_j + 1 and 2b - 1 = 2a + 1 (A120403),
  and A128933 is A103828 + 1 by its own name.  G2d checks every published
  term of each, AND the derived entry's own condition on the mapped set.

THE RUN of an x at filter n, in INDEX units so that it reads like every other
ladder here: 0 if an extra form fails, else 1 + the number of leading shift
forms x + a(1) + 1, x + a(2) + 1, ... that are prime.  A run of r says "x is
compatible with the first r - 1 terms" -- it could stand as a(r) if it were
the least such.  A full run is n; a run of n - 1 is ONE condition short of
the open term.  It cannot pass n: the form that would decide n + 1 does not
exist until a(n) is known.

Gates in this file: G1 (every published term list is a clique under the
bare definition, strictly increasing, and regenerates greedily from its first
term as far as brute force reaches), G1b (this project's own finds continue
their clique), G2 (the killed set three ways), G2c (admissibility and the
forced classes at every filter that exists), G2d (the derived identities).
"""

from sympy import isprime, primerange

# ---------------------------------------------------------------- families

# `start`      a(1).
# `extra`      the family's extra forms (a, b): a*x + b must also be prime.
# `term`       the letter used for the term in evidence files.  NONE of these
#              OEIS names gives the term a letter ("smallest integer > a(n-1)
#              such that a(n) + a(i) + 1 is prime"), so the files use the
#              entry's own wording, a(n), and the forms below are written in
#              it (CONVENTIONS.md "Naming in an evidence file").
# `also`       the entries settled for free: (A-number, multiplier, shift).
# Every entry was re-verified against the local OEIS export of 2026-09-18
# (%I stamps: A093483 #37, A103828 #41, A037100 #15, A119752 #18, A119751
# #20, A133761 #6; riders A180565 #24, A120403 #4, A113875 #14, A115760 #15,
# A128933 #3).
FAMILIES = {
    "A093483": {"start": 2, "extra": (),
                "forms": "a(n) + a(i) + 1, i = 1..n-1",
                "keywords": "hard,nonn,nice",
                "author": "Amarnath Murthy, Apr 14 2004",
                "frontier_by": "Don Reble, Sep 18 2012",
                "also": (("A180565", 2, 1),)},
    "A103828": {"start": 1, "extra": (),
                "forms": "a(n) + a(i) + 1, i = 1..n-1",
                "keywords": "nonn,more",
                "author": "Walter Kehowski, May 29 2006",
                "frontier_by": "Don Reble, Aug 17 2021",
                "also": (("A115760", 2, 1), ("A128933", 1, 1))},
    "A037100": {"start": 4, "extra": (),
                "forms": "a(n) + a(i) + 1, i = 1..n-1",
                "keywords": "nonn,more",
                "author": "Carlos Rivera",
                "frontier_by": "Don Reble, Feb 13 2019", "also": ()},
    "A119752": {"start": 2, "extra": ((2, 1),),
                "forms": "a(i) + a(n) + 1, i = 1..n (so 2*a(n) + 1 too)",
                "keywords": "nonn,more,hard",
                "author": "Walter Kehowski, Jun 17 2006",
                "frontier_by": "Donovan Johnson, Mar 23 2008",
                "also": (("A120403", 1, 1),)},
    "A119751": {"start": 1, "extra": ((2, 1),),
                "forms": "a(n) + a(i) + 1, i = 1..n (so 2*a(n) + 1 too)",
                "keywords": "nonn,hard,more",
                "author": "Walter Kehowski, Jun 17 2006",
                "frontier_by": "Donovan Johnson, Mar 23 2008",
                "also": (("A113875", 2, 1),)},
    "A133761": {"start": 5, "extra": ((1, 0),),
                "forms": "a(n) prime, and a(n) + a(i) + 1, i = 1..n-1",
                "keywords": "more,nonn",
                "author": "Randy L. Ekl, Jan 01 2008",
                "frontier_by": "Don Reble, Feb 25 2015", "also": ()},
}

# The letter the evidence files carry the term under (rule 5i).
TERM = "a(n)"

# The rider spellings open the campaign of the entry they are a map of.
ALIASES = {"A180565": "A093483", "A120403": "A119752", "A113875": "A119751",
           "A115760": "A103828", "A128933": "A103828"}

# The published terms, as published, indexed by the OEIS index n (offset 1).
KNOWN = {
    "A093483": [2, 4, 8, 14, 38, 98, 344, 22268, 79808, 187124, 347978,
                2171618, 4219797674, 98059918334, 22518029924768,
                54420534706118, 252534792143648],
    "A103828": [1, 3, 9, 27, 69, 429, 1059, 56499, 166839, 5020059, 7681809,
                274343589, 8316187179, 2866819175649, 7180244842749,
                216549352241349, 22129340663539629, 2504509324460255499],
    "A037100": [4, 6, 12, 24, 54, 186, 3246, 25926, 169314, 412026, 541524,
                37949286, 124716066, 324532464, 26678398374, 3559613215806,
                30751771983294, 20116294396883346],
    "A119752": [2, 8, 14, 44, 224, 638, 1274, 4004, 675404, 2203958, 3075158,
                6195234164, 77989711184, 4566262987328],
    "A119751": [1, 3, 9, 69, 429, 4089, 86529, 513099, 913569, 7914339,
                6593621379, 9366241599, 456246278469, 4565283812559],
    "A133761": [5, 7, 11, 101, 1481, 3911, 67421, 67751, 7592471, 1922120561,
                3015551711, 19694875121, 4397554721831, 29626637107421,
                55746215858141, 3544413963914171],
}
KNOWN = {fam: {i + 1: v for i, v in enumerate(t)} for fam, t in KNOWN.items()}

# The DERIVED entries, as published, so their identities can be gated.
# A128933 carries only 13 of A103828's 18 terms.
KNOWN_ALSO = {
    "A180565": [5, 9, 17, 29, 77, 197, 689, 44537, 159617, 374249, 695957,
                4343237, 8439595349, 196119836669, 45036059849537,
                108841069412237, 505069584287297],
    "A120403": [3, 9, 15, 45, 225, 639, 1275, 4005, 675405, 2203959, 3075159,
                6195234165, 77989711185, 4566262987329],
    "A113875": [3, 7, 19, 139, 859, 8179, 173059, 1026199, 1827139, 15828679,
                13187242759, 18732483199, 912492556939, 9130567625119],
    "A115760": [3, 7, 19, 55, 139, 859, 2119, 112999, 333679, 10040119,
                15363619, 548687179, 16632374359, 5733638351299,
                14360489685499, 433098704482699, 44258681327079259,
                5009018648920510999],
    "A128933": [2, 4, 10, 28, 70, 430, 1060, 56500, 166840, 5020060, 7681810,
                274343590, 8316187180],
}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against and
# a fresh campaign starts from; these are the project's own claim, which the
# campaign carries in its checkpoint (`found`).  G1b re-checks whatever lands
# here from the bare definition, against the whole prefix.
FOUND = {fam: {} for fam in FAMILIES}

# Terms a RUNNING campaign has found and not yet published into FOUND.  The
# form list at index n needs a(1..n-1), so the launcher registers each find
# here (and in every pool worker) before it builds the next filter's engine.
# `register` refuses to CHANGE a term: a prefix is an append-only record.
_RUNTIME = {fam: {} for fam in FAMILIES}

# The engines refuse to run at or below the sieve depth (the exception zone:
# a value can BE the small prime that would otherwise divide it), and the
# oracle covers that prefix by brute force.
K_FLOOR = 10 ** 4


def family(fam):
    """The canonical family key, aliases resolved; raises on an unknown one."""
    fam = str(fam).upper()
    fam = ALIASES.get(fam, fam)
    if fam not in FAMILIES:
        raise KeyError(f"no family {fam!r}; the families are "
                       f"{', '.join(sorted(FAMILIES))} (aliases "
                       f"{', '.join(sorted(ALIASES))})")
    return fam


def extra(fam):
    """The family's extra forms, as (a, b) pairs: a*x + b must be prime."""
    return tuple(FAMILIES[family(fam)]["extra"])


def register(fam, n, x):
    """Record a(n) = x, found at runtime.  Idempotent; raises on a conflict
    with anything already known, because a prefix never changes."""
    fam, n, x = family(fam), int(n), int(x)
    have = term(fam, n, missing=None)
    if have is not None and have != x:
        raise ValueError(f"{fam} a({n}) is already {have}; refusing to "
                         f"re-register it as {x}")
    if have is None:
        if term(fam, n - 1, missing=None) is None:
            raise ValueError(f"{fam} a({n}) cannot be registered before "
                             f"a({n - 1}): the prefix is sequential")
        _RUNTIME[fam][n] = x


def term(fam, n, missing=KeyError):
    """a(n) from the literature, this project's finds, or the running
    campaign -- in that order.  `missing=None` returns None instead of
    raising."""
    fam, n = family(fam), int(n)
    for table in (KNOWN[fam], FOUND[fam], _RUNTIME[fam]):
        if n in table:
            return int(table[n])
    if missing is None:
        return None
    raise KeyError(f"{fam} a({n}) is not known: the filter for a({n + 1}) "
                   f"does not exist until it is")


def frontier(fam):
    """The largest n with a(1..n) all known."""
    fam = family(fam)
    n = 0
    while term(fam, n + 1, missing=None) is not None:
        n += 1
    return n


def terms(fam, n):
    """[a(1), ..., a(n-1)]: the prefix the conditions at index n are built
    from.  Raises if any of it is unknown."""
    return [term(fam, i) for i in range(1, int(n))]


def forms(fam, n):
    """The conditions on x at index n, as (a, b) with a*x + b prime: the
    family's extra forms first, then x + a(i) + 1 for i = 1..n-1 in order."""
    return list(extra(fam)) + [(1, t + 1) for t in terms(fam, n)]


def nforms(fam, n):
    """How many conditions index n imposes."""
    fam = family(fam)
    return len(extra(fam)) + max(0, int(n) - 1)


def values(fam, x, n):
    """Every value the conditions at index n form at x, in form order."""
    x = int(x)
    return [a * x + b for a, b in forms(fam, n)]


def run_length(fam, x, n, cap=None):
    """The run of x at index n, in INDEX units (module docstring): 0 if an
    extra form fails, else 1 + the number of leading shift forms that are
    prime, capped at `cap` (default n).  Full is n."""
    fam = family(fam)
    x = int(x)
    cap = int(n) if cap is None else min(int(cap), int(n))
    if any(not isprime(a * x + b) for a, b in extra(fam)):
        return 0
    r = 1
    for t in terms(fam, n):
        if r >= cap or not isprime(x + t + 1):
            break
        r += 1
    return r


def is_term(fam, x, n):
    """x satisfies every condition of index n and exceeds a(n-1).  NOT the
    least-claim: that is a sweep's to make."""
    fam, x, n = family(fam), int(x), int(n)
    if n > 1 and x <= term(fam, n - 1):
        return False
    return run_length(fam, x, n) == n


def forbidden_k_residues(q, n, fam):
    """The residues of x mod q at which some condition of index n is
    divisible by q -- by walking every residue and testing divisibility."""
    fs = forms(fam, n)
    return [r for r in range(q) if any((a * r + b) % q == 0 for a, b in fs)]


def w(q, n, fam):
    """|K(q,n,F)|, from the walk."""
    return len(forbidden_k_residues(q, n, fam))


def w_count(q, n, fam):
    """|K(q,n,F)| the algebraic way: distinct -b*a^-1 mod q over the forms q
    does not divide the leading coefficient of."""
    return len({(-b * pow(a, -1, q)) % q for a, b in forms(fam, n) if a % q})


def forced_primes(fam, n, upto=64):
    """The primes that leave exactly one residue class at index n."""
    return [q for q in primerange(2, upto) if w(q, n, fam) == q - 1]


def forced_residue(q, n, fam):
    """The one class a forced prime leaves; raises if q is not forced."""
    free = sorted(set(range(q)) - set(forbidden_k_residues(q, n, fam)))
    if len(free) != 1:
        raise ValueError(f"{q} is not forced at index {n} of {fam}: it leaves "
                         f"{len(free)} classes")
    return free[0]


def admissible(fam, n):
    """(ok, q): ok unless some prime q has every residue killed at index n,
    in which case NO x satisfies the conditions and the sequence is finite.
    Only q <= nforms can be covered, so the check is finite."""
    for q in primerange(2, nforms(fam, n) + 2):
        if w(q, n, fam) >= q:
            return False, q
    return True, None


def wheel_residues(fam, n, p1):
    """The x mod W(p1) that survive every prime q <= p1, by brute force."""
    qs = list(primerange(2, p1 + 1))
    W = 1
    for q in qs:
        W *= q
    killed = {q: set(forbidden_k_residues(q, n, fam)) for q in qs}
    return W, [r for r in range(W) if all(r % q not in killed[q] for q in qs)]


def first_x(fam, n, lo=None, hi=None):
    """The least x > lo (default a(n-1)) with a full run at index n, by the
    bare definition; None if there is none below hi."""
    fam, n = family(fam), int(n)
    x = (term(fam, n - 1) if lo is None else int(lo)) + 1
    while hi is None or x < hi:
        if run_length(fam, x, n) == n:
            return x
        x += 1
    return None


# --------------------------------- gates -----------------------------------

REGEN_BELOW = 10 ** 6         # how far G1 regenerates each clique by brute force


def g1_knowns_reproduce():
    """Every published list is a clique under the bare definition, strictly
    increasing, and the greedy rule regenerates it from a(1) as far as brute
    force reaches -- which pins the DEFINITION (including each family's extra
    form and its start) rather than quoting it."""
    parts = []
    for fam in FAMILIES:
        t = [KNOWN[fam][i] for i in sorted(KNOWN[fam])]
        if t[0] != FAMILIES[fam]["start"] or sorted(set(t)) != t:
            return False, f"G1 FAIL: {fam} does not start or increase as published"
        for j, x in enumerate(t):
            for a, b in extra(fam):
                if not isprime(a * x + b):
                    return False, (f"G1 FAIL: {fam} a({j + 1}) = {x} fails its "
                                   f"extra form {a}*x + {b}")
            for i in range(j):
                if not isprime(t[i] + x + 1):
                    return False, (f"G1 FAIL: {fam} a({i + 1}) + a({j + 1}) + 1 "
                                   f"is composite")
        regen = 1
        while regen < len(t) and t[regen] < REGEN_BELOW:
            got = first_x(fam, regen + 1, hi=REGEN_BELOW)
            if got != t[regen]:
                return False, (f"G1 FAIL: the greedy rule gives {fam} "
                               f"a({regen + 1}) = {got}, published {t[regen]}")
            regen += 1
        parts.append(f"{fam} a(1)-a({len(t)}) ({regen} regenerated)")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every pair sums to a "
                  "prime less one, every extra form holds, and the greedy rule "
                  f"rebuilds each list from its first term below {REGEN_BELOW:,}")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition against the
    WHOLE prefix -- the literature's terms and the finds before it."""
    parts = []
    for fam in FAMILIES:
        found = FOUND[fam]
        if not found:
            continue
        top = max(KNOWN[fam])
        for n in sorted(found):
            if n != top + 1:
                return False, (f"G1b FAIL: {fam} a({n}) does not continue the "
                               f"sequence from a({top})")
            if not is_term(fam, found[n], n):
                return False, (f"G1b FAIL: {fam} a({n}) = {found[n]} does not "
                               f"satisfy every condition of index {n} above "
                               f"a({n - 1})")
            top = n
        parts.append(f"{fam} a({min(found)})-a({max(found)})")
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each against its whole prefix the moment one "
                      "is entered in FOUND")
    return True, ("G1b ok: this project's finds " + "; ".join(parts) + " -- "
                  "each exceeds its predecessor and satisfies every condition "
                  "of its index from the bare definition")


def g2_killed_set_three_ways():
    """K(q,n,F) by the residue walk, by the algebraic construction, and by
    direct divisibility of the values -- at every prime under 90 and every
    index that exists; and K(q,n) is a subset of K(q,n+1)."""
    checked = 0
    for fam in FAMILIES:
        prev = {}
        for n in range(2, frontier(fam) + 2):
            fs = forms(fam, n)
            for q in primerange(2, 90):
                walk = set(forbidden_k_residues(q, n, fam))
                alg = {(-b * pow(a, -1, q)) % q for a, b in fs if a % q}
                if walk != alg or w_count(q, n, fam) != len(walk):
                    return False, (f"G2 FAIL: K({q},{n},{fam}) differs between "
                                   f"the walk and the construction")
                for r in range(q):
                    x = K_FLOOR * q + r
                    direct = any(v % q == 0 for v in values(fam, x, n))
                    if direct != (r in walk):
                        return False, (f"G2 FAIL: K({q},{n},{fam}) disagrees "
                                       f"with divisibility at x = {x}")
                if not prev.get(q, set()) <= walk:
                    return False, (f"G2 FAIL: K({q},{n},{fam}) lost a residue "
                                   f"K({q},{n - 1}) had")
                prev[q] = walk
                checked += 1
    return True, (f"G2 ok: K(q,n,F) three ways -- residue walk, -b*a^-1, and "
                  f"direct divisibility -- agree at all {checked} (q < 90, n, F) "
                  f"and K(q,n) is a subset of K(q,n+1) throughout")


def g2c_admissible_and_forced():
    """Every filter that exists is admissible (no prime has every class
    killed -- not a theorem here), and the forced classes are what the
    literature's congruences say."""
    rows = []
    for fam in FAMILIES:
        top = frontier(fam)
        for n in range(2, top + 2):
            ok, q = admissible(fam, n)
            if not ok:
                return False, (f"G2c FAIL: every class mod {q} is killed at "
                               f"index {n} of {fam}: the sequence would be "
                               f"FINITE there, and it has a term")
        n = top + 1
        forced = {q: forced_residue(q, n, fam) for q in forced_primes(fam, n)}
        if 2 not in forced or 3 not in forced:
            return False, f"G2c FAIL: {fam} does not force 2 and 3 at index {n}"
        for i in range(max(3, top - 3), top + 1):
            x = term(fam, i)
            for q, r in forced.items():
                if i > q and x % q != r:
                    return False, (f"G2c FAIL: {fam} a({i}) = {x} is not == "
                                   f"{r} (mod {q}), the class forced at "
                                   f"index {n}")
        rows.append(f"{fam} n = {n}: " + ", ".join(
            f"x == {r} (mod {q})" for q, r in sorted(forced.items())))
    return True, ("G2c ok: every filter from n = 2 to each open index is "
                  "admissible (checked, not assumed), and the forced classes "
                  "at the open index hold on the latest published terms -- "
                  + "; ".join(rows))


def g2d_derived_identities():
    """The five derived entries are their base entry under an affine map, on
    every published term, and the mapped set satisfies the derived entry's
    OWN condition (pairwise average, or pairwise sum less one, prime)."""
    rows = []
    for fam in FAMILIES:
        for seq, mul, shift in FAMILIES[fam]["also"]:
            pub = KNOWN_ALSO[seq]
            base = [KNOWN[fam][i] for i in sorted(KNOWN[fam])]
            mapped = [mul * x + shift for x in base]
            if mapped[:len(pub)] != pub:
                return False, (f"G2d FAIL: {seq} is not {mul}*{fam} + {shift} "
                               f"on its published terms")
            for j in range(len(mapped)):
                for i in range(j):
                    s = mapped[i] + mapped[j]
                    v = s // 2 if mul == 2 else s - 1
                    if (mul == 2 and s % 2) or not isprime(v):
                        return False, (f"G2d FAIL: {seq}'s own pairwise "
                                       f"condition fails at ({i + 1}, {j + 1})")
            if seq == "A113875" and not all(isprime(v) for v in mapped):
                return False, "G2d FAIL: a mapped A113875 entry is not prime"
            rows.append(f"{seq} = {mul if mul > 1 else ''}"
                        f"{'*' if mul > 1 else ''}{fam} + {shift} "
                        f"({len(pub)} published terms)")
    return True, ("G2d ok: " + "; ".join(rows) + " -- each on every published "
                  "term, with the derived entry's own pairwise condition "
                  "re-checked on the mapped set")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce, g2_killed_set_three_ways,
         g2c_admissible_and_forced, g2d_derived_identities]


if __name__ == "__main__":
    import pathlib as _pathlib
    import sys as _sys
    _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown

    def _main():
        bad = 0
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
            bad += 0 if ok else 1
        return 1 if bad else 0

    _shutdown.graceful(_main)
