"""The oracle for the linear ladders -- slow, obviously correct, sympy only.

    A(F, n) = least k >= 1 such that m*k + s is prime for EVERY multiplier m
              in the family F's list at index n

Seven families, one engine.  Each is one unknown k and a nested list of
linear conditions whose multipliers are consecutive integers (or
consecutive odd integers) rather than the primes of this repo's
prime-ladders project -- the same ladder with the rung labels changed:

    A088250   r*k + 1,      r = 1..n       Murthy 2003; a(14) Resta 2017
    A173750   r*k + 1,      r = 2..n       Seidov 2010; a(15) Resta 2017
    A125838   r*k - 1,      r = 2..n       Rivera 2007; a(14) Resta 2017
    A125839   r*k - 1,      r = 3..n       Pebody 2007; a(15) Resta 2017
    A164325   (2r-1)*k + 1, r = 1..n       Firoozbakht 2009; a(15) Resta 2017
    A164326   (2r-1)*k - 1, r = 1..n       Firoozbakht 2009; a(14) Resta 2017
    A088651   r*k - 1,      r = 1..n       Murthy 2003; a(15) J. K. Andersen 2008

Two more entries are SETTLED by finds here without being hunted for:
A202778 (x*k + 1 prime for x = 1..n and COMPOSITE at n + 1) equals
A088250(n) whenever A088250(n) has run exactly n, and A071576 (2ik + 1
prime for i = 1..n) is A088250(n)/2 for n >= 3 because k is even from
n = 2; likewise A202779 is the exact-run version of A088651.  The family
tables carry those identities and G2d asserts them on every published term.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Four facts are PROVED here rather than assumed, because both engines and the
odds model are built on them.

  THE KILLED SET.  Fix a prime q and a multiplier m of the family at index
  n.  If q | m the form m*k + s is congruent to s (mod q), and |s| = 1 < q,
  so that form is NEVER divisible by q: a rung whose multiplier q divides
  kills nothing.  For q not dividing m,

      q | m*k + s   <=>   k == -s * m^-1  (mod q),

  so the residues of k that q kills are exactly

      K(q,n,F) = { -s * m^-1 mod q : m in mults(F, n), q does not divide m }

  and the engines sieve k against K(q,n,F) and nothing else.

  ITS SIZE, EXACTLY.  Inversion and negation are bijections of (Z/q)^*, so

      w(q,n,F) = |K(q,n,F)| = |{ m mod q : m in mults(F, n), q not | m }|

  -- the number of DISTINCT nonzero residues the multipliers take mod q.
  For the 1..n family that is min(n, q - 1); for every family it is
  independent of the SIGN (K(q,n,-1) = -K(q,n,+1)), so a family and its
  sign-twin share every table size, the whole survival curve and one
  singular series.

  FORCED DIVISIBILITY.  When w(q,n,F) = q - 1 -- the multipliers cover
  every nonzero residue mod q -- the only surviving k are k == 0 (mod q).
  Consecutive integers cover the residues fast: for the 1..n family EVERY
  prime q <= n + 1 is forced (`forcing_n` computes the threshold per
  family), so A088250's a(15) is a multiple of 30030 and its a(16) of
  510510, and each prime above the forced ones kills the MAXIMUM number of
  residues, min(n, q - 1).  That is a stronger wheel than the prime ladders
  have at the same n, and it is what makes this project's line rate.

  ADMISSIBLE AT EVERY n, FOR EVERY FAMILY.  k == 0 (mod q) gives every value
  == s != 0 (mod q), so residue 0 is never killed and w(q,n,F) <= q - 1 < q
  for every prime q.  No fixed prime divisor at any n; by Dickson's
  conjecture there are infinitely many k for every n, so a(n) is defined for
  all n and a find CONFIRMS the guiding conjecture and can never refute it.

  THE EXCEPTION ZONE is real and small.  "q divides the value, so the value
  is composite" needs the value to EXCEED q.  It does not for the smallest
  terms: A164326's a(5) = 6 has 1*6 - 1 = 5, which IS the prime 5 and would
  be killed by the q = 5 rule; A088250's a(1) = a(2) = 1 has 1*1 + 1 = 2.
  The oracle therefore sweeps WITHOUT the wheel below K_FLOOR, and both
  engines refuse to run at or below max(K_FLOOR, sieve depth + 1) -- the
  smallest form is 1*k + s >= k - 1, so k must exceed q2 + 1 for every kill
  by a sieve prime to be a composite.

Gates in this file: G1 (the frozen knowns reproduce, are monotone, sit on
the wheel above the floor, and each frontier's wall is composite; A088651's
monotone table agrees with A202779's exact-run table), G1b (this project's
own finds, once there are any, from the bare definition), G2 (the small
terms re-derived exhaustively from the bare definition), G2b (the w(q,n,F)
formula equals direct divisibility, both signs), G2c (admissibility,
sign-independence of w, the forcing thresholds, and every known term above
the floor obeying them), G2d (the derived identities A202778 / A071576 /
A202779 on every published term).
"""

from sympy import isprime, primerange

# ---------------------------------------------------------------- families

# `kind`       "linear": the multiplier of the i-th rung is i
#              "odd":    it is 2i - 1
# `rungs_from` the index of the FIRST rung that is a condition -- A173750's
#              a(1) is vacuous (r = 2..1 is empty), A125838 starts at 2 and
#              A125839 at 3, so a run length there is counted from that
#              index (a k whose very first form is composite has run
#              rungs_from - 1).
# `first_n`    the OEIS offset: the first index the sequence has a term at.
# Every entry was re-verified against oeis.org on 2026-09-03 (the internal
# format, %I revision stamps identical to the local export of 2026-09-01).
FAMILIES = {
    "A088250": {"sign": +1, "kind": "linear", "rungs_from": 1, "first_n": 1,
                "forms": "r*k + 1, r = 1..n", "keywords": "nonn,more",
                "author": "Amarnath Murthy, Sep 26 2003",
                "frontier_by": "Giovanni Resta, Mar 31 2017",
                "also": (("A202778", "exact"), ("A071576", "half"))},
    "A173750": {"sign": +1, "kind": "linear", "rungs_from": 2, "first_n": 1,
                "forms": "r*k + 1, r = 2..n", "keywords": "nonn,more",
                "author": "Zak Seidov, Nov 26 2010",
                "frontier_by": "Giovanni Resta, Mar 31 2017", "also": ()},
    "A125838": {"sign": -1, "kind": "linear", "rungs_from": 2, "first_n": 2,
                "forms": "r*k - 1, r = 2..n", "keywords": "hard,more,nonn",
                "author": "Carlos Rivera, Jan 01 2007",
                "frontier_by": "Giovanni Resta, Mar 29 2017", "also": ()},
    "A125839": {"sign": -1, "kind": "linear", "rungs_from": 3, "first_n": 3,
                "forms": "r*k - 1, r = 3..n", "keywords": "hard,more,nonn",
                "author": "Luke Pebody, Jan 02 2007",
                "frontier_by": "Giovanni Resta, Mar 30 2017", "also": ()},
    "A164325": {"sign": +1, "kind": "odd", "rungs_from": 1, "first_n": 1,
                "forms": "(2r-1)*k + 1, r = 1..n", "keywords": "more,nonn",
                "author": "Farideh Firoozbakht, Sep 15 2009",
                "frontier_by": "Giovanni Resta, Apr 01 2017", "also": ()},
    "A164326": {"sign": -1, "kind": "odd", "rungs_from": 1, "first_n": 1,
                "forms": "(2r-1)*k - 1, r = 1..n", "keywords": "more,nonn",
                "author": "Farideh Firoozbakht, Sep 16 2009",
                "frontier_by": "Giovanni Resta, Mar 31 2017", "also": ()},
    "A088651": {"sign": -1, "kind": "linear", "rungs_from": 1, "first_n": 1,
                "forms": "r*k - 1, r = 1..n", "keywords": "nonn",
                "author": "Amarnath Murthy, Sep 26 2003",
                "frontier_by": "Jens Kruse Andersen, May 02 2008",
                "also": (("A202779", "exact"),)},
}

# The exact-run entry A202779 is what the handoff for this project named
# for the r*k - 1 family; A088651 is its MONOTONE version (least k with
# run >= n), which is what an engine hunting "run >= n" actually finds, and
# the two agree at every index where the monotone term has run exactly n.
# Both spellings open the same campaign.
ALIASES = {"A202779": "A088651", "A202778": "A088250"}

# The published terms, as published, indexed by the OEIS index n.
KNOWN = {
    "A088250": {1: 1, 2: 1, 3: 2, 4: 330, 5: 10830, 6: 25410, 7: 512820,
                8: 512820, 9: 12960606120, 10: 434491727670,
                11: 1893245380950, 12: 71023095613470,
                13: 878232256181280, 14: 11429352906540438870},
    "A173750": {1: 1, 2: 1, 3: 2, 4: 330, 5: 714, 6: 13530, 7: 192660,
                8: 512820, 9: 4601310, 10: 863815050, 11: 262428279750,
                12: 2169289182060, 13: 2169289182060, 14: 2169289182060,
                15: 4646092391146085880},
    "A125838": {2: 2, 3: 2, 4: 2, 5: 6, 6: 120, 7: 120, 8: 2894220,
                9: 397073040, 10: 1236161850, 11: 764907546690,
                12: 8955490023480, 13: 138393712627170,
                14: 8047290924923250},
    "A125839": {3: 1, 4: 1, 5: 6, 6: 18, 7: 120, 8: 1260, 9: 1485540,
                10: 28667100, 11: 28667100, 12: 842889105240,
                13: 2281585556250, 14: 163881570370980,
                15: 45187548280664790},
    "A164325": {1: 1, 2: 2, 3: 2, 4: 6, 5: 1170, 6: 64590, 7: 25153800,
                8: 25153800, 9: 4747505070, 10: 207187349040,
                11: 6703860240000, 12: 26997529639080,
                13: 1760354281625940, 14: 1760354281625940,
                15: 10718654377787155800},
    "A164326": {1: 3, 2: 4, 3: 4, 4: 6, 5: 6, 6: 2100, 7: 2100,
                8: 105828450, 9: 3533468190, 10: 240544635660,
                11: 7392639784530, 12: 1896344521244250,
                13: 5389539504929580, 14: 68086992545221650},
    "A088651": {1: 3, 2: 3, 3: 4, 4: 6, 5: 6, 6: 154770, 7: 2894220,
                8: 2894220, 9: 407874180, 10: 214580145780,
                11: 9448481062020, 12: 247236503934420,
                13: 2545206711847800, 14: 18178612369988250180,
                15: 53792264108455702830},
}

# The DERIVED entries, as published, so their identities can be gated.
KNOWN_ALSO = {
    # least k with x*k + 1 prime for x = 1..n and COMPOSITE at x = n + 1
    "A202778": {1: 4, 2: 1, 3: 2, 4: 330, 5: 10830, 6: 25410, 7: 8224860,
                8: 512820, 9: 12960606120, 10: 434491727670,
                11: 1893245380950, 12: 71023095613470,
                13: 878232256181280, 14: 11429352906540438870},
    # least k with 2ik + 1 prime for i = 1..n
    "A071576": {1: 1, 2: 1, 3: 1, 4: 165, 5: 5415, 6: 12705, 7: 256410,
                8: 256410, 9: 6480303060, 10: 217245863835,
                11: 946622690475, 12: 35511547806735,
                13: 439116128090640, 14: 5714676453270219435},
    # least k with x*k - 1 prime for x = 1..n and COMPOSITE at x = n + 1
    "A202779": {1: 8, 2: 3, 3: 4, 4: 1410, 5: 6, 6: 154770, 7: 5246010,
                8: 2894220, 9: 407874180, 10: 214580145780,
                11: 9448481062020, 12: 247236503934420,
                13: 2545206711847800, 14: 18178612369988250180,
                15: 53792264108455702830},
}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against
# and a fresh campaign starts from; these are the project's own claim,
# which the campaign carries in its checkpoint (`found`) and promotes its
# frontier from at runtime.  G1b re-checks whatever lands here from the
# bare definition.  A088250's three were found 2026-09-03 by the one
# campaign that ran from k = 1e6 to the family's ceiling (RESULTS.md); each
# also settles A202778 at its index (the runs are exact) and A071576 at
# half its value.
FOUND = {fam: {} for fam in FAMILIES}
FOUND["A088250"] = {15: 1555360041314493173760,
                    16: 87117680854368555070680,
                    17: 1048124771278912649231910}
# A125838's four, the same day, 17 minutes from k = 1e6 to its ceiling;
# a(15) is the integer the literature holds as A125839's a(15), and every
# term is an upper bound on A125839's at the same index (fewer conditions).
FOUND["A125838"] = {15: 45187548280664790,
                    16: 436409209028729276340,
                    17: 44387933133290055609300,
                    18: 74882388347598051560340}
# A125839's three, 15 minutes to its ceiling; each under A125838's term at
# the same index, as the subset of conditions requires.
FOUND["A125839"] = {16: 14423013361403116470,
                    17: 771355748787892768500,
                    18: 6530891065478723143200}
# A173750's four in 37 minutes to the +1 ceiling: a(18) = a(19) is a RIDER
# -- one k with a run of 19 found while a(18) was open, like the family's
# published a(12) = a(13) = a(14) -- evidenced once under a(18).
FOUND["A173750"] = {16: 828196248070762801230,
                    17: 67335095107785754679430,
                    18: 147316106448079863444150,
                    19: 147316106448079863444150}

# No family carries a published bound of any kind -- no upper bound at any
# open n, and no searched-empty lower bound beyond the last term.  The floor
# for the next term is therefore monotonicity alone, which is free: the
# conditions nest, so a(n+1) >= a(n).
PUBLISHED_BOUNDS = {fam: {} for fam in FAMILIES}

# The open terms: the four indices past each family's published frontier.
OPEN_N = {fam: [max(KNOWN[fam]) + i for i in range(1, 5)] for fam in FAMILIES}

# The wheel argument has an exception zone below this k (a value can BE the
# small prime that would otherwise divide it), so the engines refuse to run
# there and the oracle covers it by brute force.
K_FLOOR = 10 ** 4

# The single composite that keeps each family's next term open: the value
# at the rung after the frontier, on the frontier term.  Gate G1 asserts it.
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
    return int(FAMILIES[family(fam)]["rungs_from"])


def rung(fam, i):
    """The multiplier of the i-th form: i, or 2i - 1 for the odd families."""
    kind = FAMILIES[family(fam)]["kind"]
    i = int(i)
    return i if kind == "linear" else 2 * i - 1


def mults(fam, n):
    """The multipliers of the family at index n -- the conditions a(n) must
    satisfy.  Empty for A173750 at n = 1 (its a(1) is vacuous)."""
    fam = family(fam)
    return [rung(fam, i) for i in range(rungs_from(fam), int(n) + 1)]


def nforms(fam, n):
    """How many conditions the filter n imposes: what the singular series
    exponent and the residue-list width are sized from."""
    return max(0, int(n) - rungs_from(fam) + 1)


def value(fam, k, i):
    """The i-th form at k."""
    return rung(fam, i) * int(k) + sign(fam)


def run_length(fam, k, cap=64):
    """Largest r <= cap with every form up to index r prime at k.

    Counted from the family's first rung: a k whose first form is composite
    has run rungs_from - 1 (0 for most families, 1 for A173750 and A125838,
    2 for A125839).
    """
    fam = family(fam)
    r = rungs_from(fam) - 1
    while r < cap and isprime(value(fam, k, r + 1)):
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
    for k in range(q):
        for m in ms:
            if (m * k + s) % q == 0:
                out.add(k)
                break
    return out


def w(q, n, fam):
    """|K(q,n,F)| by the closed form proved in the module docstring: the
    number of distinct nonzero residues of the family's multipliers mod q."""
    return len({m % q for m in mults(fam, n) if m % q})


def forcing_n(q, fam, n_max=200):
    """The least n at which the multipliers hit every nonzero residue mod q,
    so that k == 0 (mod q) is FORCED; None if that does not happen below
    n_max."""
    for n in range(rungs_from(fam), n_max + 1):
        if w(q, n, fam) == q - 1:
            return n
    return None


def forced_primes(fam, n, upto=60):
    """The primes forced at filter n, in order."""
    return [q for q in primerange(2, upto) if w(q, n, fam) == q - 1]


def wheel_residues(fam, n, p1):
    """Every k mod W that survives all primes q <= p1, by brute force.

    W = product of the primes <= p1.  This is the oracle's version: it
    walks the whole period.  The engines build the same set by CRT lifting
    and are gated against this on small p1.
    """
    W = 1
    for q in primerange(2, p1 + 1):
        W *= q
    killed = {q: forbidden_k_residues(q, n, fam) for q in primerange(2, p1 + 1)}
    return W, [r for r in range(W)
               if all(r % q not in killed[q] for q in killed)]


def first_k(fam, n, lo=1, hi=None):
    """Least k in [lo, hi] with run_length(k) >= n, by definition.

    The literal definition swept one integer at a time -- the slowest thing
    in this project, and the reason G2 only covers the small terms.
    """
    k = lo
    while hi is None or k <= hi:
        if run_length(fam, k, cap=n) >= n:
            return k
        k += 1
    return None


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, each ladder is monotone,
    every term above the floor survives the small-prime wheel, the wall that
    keeps the next term open is composite, and A088651's monotone table is
    exactly the running minimum of A202779's exact-run table."""
    parts = []
    for fam in FAMILIES:
        known = KNOWN[fam]
        prev = 0
        for n in sorted(known):
            k = known[n]
            r = run_length(fam, k, cap=n + 3)
            if r < n:
                return False, f"G1 FAIL: {fam} a({n}) = {k} has run {r} < {n}"
            if k < prev:
                return False, f"G1 FAIL: {fam} a({n}) = {k} < a({n-1}) = {prev}"
            if k >= K_FLOOR:
                W, res = wheel_residues(fam, n, 13)
                if k % W not in set(res):
                    return False, (f"G1 FAIL: {fam} a({n}) = {k} is killed by "
                                   f"the wheel mod {W}")
            prev = k
        kk, ii = THE_WALL[fam]
        if kk != known[max(known)] or ii != max(known) + 1:
            return False, (f"G1 FAIL: THE_WALL for {fam} is not the frontier "
                           f"term's next rung")
        if run_length(fam, kk, cap=max(known) + 4) != max(known):
            return False, (f"G1 FAIL: {fam} frontier term {kk} does not reach "
                           f"exactly {max(known)}")
        if isprime(value(fam, kk, ii)):
            return False, (f"G1 FAIL: {rung(fam, ii)}*{kk}{sign(fam):+d} is "
                           f"prime, so {fam} a({ii}) would not be open")
        parts.append(f"{fam} a({min(known)})-a({max(known)})")
    ex = KNOWN_ALSO["A202779"]
    for n in KNOWN["A088651"]:
        if KNOWN["A088651"][n] != min(ex[r] for r in ex if r >= n):
            return False, (f"G1 FAIL: A088651 a({n}) is not the running "
                           f"minimum of A202779 from {n}")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every published term "
                  "satisfies the definition, every ladder is monotone, every "
                  "term above the floor is on the wheel, each frontier term "
                  "stops exactly where the sequence says it does (its wall "
                  "is composite), and A088651 is the running minimum of the "
                  "exact-run A202779")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition.

    Independent of the engines and of the evidence files: sympy alone says
    each k reaches EXACTLY its run (the value at the next rung is composite),
    the ladder continues monotonically from the published frontier, and
    every k obeys the forced primes at its index.  One k may settle several
    consecutive terms: the run must then reach every term the k carries and
    be exactly the last of them.
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
            k = found[n]
            if n != top + 1:
                return False, (f"G1b FAIL: {fam} a({n}) does not continue "
                               f"the ladder from a({top})")
            rider = found.get(n + 1) == k
            r = run_length(fam, k, cap=n + 3)
            if (r < n) if rider else (r != n):
                return False, (f"G1b FAIL: {fam} a({n}) = {k} has run {r}, "
                               f"not {'at least' if rider else 'exactly'} {n}")
            if k < prev:
                return False, f"G1b FAIL: {fam} a({n}) = {k} < a({n-1}) = {prev}"
            for q in forced_primes(fam, n):
                if k % q:
                    return False, (f"G1b FAIL: {fam} a({n}) = {k} is not a "
                                   f"multiple of the forced prime {q}")
            if rider:
                riders.append(f"a({n + 1}) = a({n})")
            elif isprime(value(fam, k, n + 1)):
                return False, (f"G1b FAIL: {rung(fam, n + 1)}*{k}"
                               f"{sign(fam):+d} is prime, so {fam} a({n}) "
                               f"would be a({n + 1}) or more")
            prev, top = k, n
        parts.append(f"{fam} a({min(found)})-a({max(found)})"
                     + (f" ({', '.join(riders)} on one k)" if riders else ""))
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each from the bare definition the moment one "
                      "is entered in FOUND")
    return True, ("G1b ok: this project's finds " + "; ".join(parts) +
                  " -- each reaches exactly its run from the bare definition, "
                  "continues the ladder monotonically from the published "
                  "frontier and obeys every forced prime")


# The largest index each family is re-derived to one integer at a time.  The
# terms stop at a few times 1e5 because a gate may not cost minutes; G5
# (lladder_search) re-derives the next two knowns of every family through
# the CPU engine instead.
G2_UPTO = {"A088250": 6, "A173750": 6, "A125838": 7, "A125839": 8,
           "A164325": 6, "A164326": 7, "A088651": 6}


def g2_rederive_small(upto=None):
    """Re-derive the small terms exhaustively from the bare definition."""
    upto = upto or G2_UPTO
    done = []
    for fam in FAMILIES:
        for n in range(FAMILIES[fam]["first_n"], upto[fam] + 1):
            got = first_k(fam, n, lo=1, hi=KNOWN[fam][n])
            if got != KNOWN[fam][n]:
                return False, (f"G2 FAIL: {fam} re-derived a({n}) = {got} != "
                               f"{KNOWN[fam][n]}")
        done.append(f"{fam} a({FAMILIES[fam]['first_n']})-a({upto[fam]})")
    return True, ("G2 ok: " + ", ".join(done) + " re-derived exhaustively, "
                  "one integer at a time, from the definition alone")


def g2b_killed_set_size():
    """The closed form w(q,n,F) IS direct divisibility, for every family.

    Both regimes (q small, where the multipliers may collide or cover
    everything, and q above the largest multiplier, where w = nforms),
    because the engines size every table from this formula and a wrong size
    is either a missed kill or a lost candidate.
    """
    for fam in FAMILIES:
        s = sign(fam)
        for n in (3, 7, 11, 15, 16, 19):
            ms = mults(fam, n)
            for q in primerange(2, 120):
                direct = forbidden_k_residues(q, n, fam)
                if len(direct) != w(q, n, fam):
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: direct "
                                   f"{len(direct)} != formula {w(q, n, fam)}")
                built = {(-s * pow(m, -1, q)) % q for m in ms if m % q}
                if built != direct:
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: constructed "
                                   f"{sorted(built)} != direct {sorted(direct)}")
                if 0 in direct:
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: k == 0 (mod "
                                   f"q) must always be safe")
                if ms and q > max(ms) and len(direct) != len(ms):
                    return False, (f"G2b FAIL: {fam} n={n} q={q} exceeds every "
                                   f"multiplier but w = {len(direct)} != "
                                   f"{len(ms)}")
    return True, ("G2b ok: |K(q,n,F)| = #distinct nonzero residues of the "
                  "multipliers mod q, and the constructed set equals direct "
                  "divisibility, for every prime q < 120 at n = 3, 7, 11, 15, "
                  "16, 19 and all seven families; k == 0 (mod q) always "
                  "survives; w = nforms whenever q exceeds every multiplier")


# The forcing thresholds, per family: the least n at which each small prime
# forces k == 0.  Consecutive integers 1..n cover the nonzero residues mod q
# from n = q - 1; 2..n needs the residue 1 from m = q + 1; 3..n needs 1 and 2
# from q + 1 and q + 2 (2 from m = 3); the odd numbers 1, 3, ..., 2n - 1 reach
# the even residue q - 1 at m = 2q - 1, so n = q.
FORCING = {
    "A088250": {2: 1, 3: 2, 5: 4, 7: 6, 11: 10, 13: 12, 17: 16, 19: 18, 23: 22},
    "A173750": {2: 3, 3: 4, 5: 6, 7: 8, 11: 12, 13: 14, 17: 18, 19: 20, 23: 24},
    "A125838": {2: 3, 3: 4, 5: 6, 7: 8, 11: 12, 13: 14, 17: 18, 19: 20, 23: 24},
    "A125839": {2: 3, 3: 5, 5: 7, 7: 9, 11: 13, 13: 15, 17: 19, 19: 21, 23: 25},
    "A164325": {2: 1, 3: 3, 5: 5, 7: 7, 11: 11, 13: 13, 17: 17, 19: 19, 23: 23},
    "A164326": {2: 1, 3: 3, 5: 5, 7: 7, 11: 11, 13: 13, 17: 17, 19: 19, 23: 23},
    "A088651": {2: 1, 3: 2, 5: 4, 7: 6, 11: 10, 13: 12, 17: 16, 19: 18, 23: 22},
}


def g2c_admissible_and_forcing():
    """Bar 1 as an assertion, plus the two lemmas the engine turns on.

    (a) w(q,n,F) < q for every prime q and every n up to well past the
        production filters: no fixed prime divisor, so every family is
        conjecturally infinite and a find CONFIRMS.
    (b) w does not depend on the sign: K(q,n,-1) is the negative of
        K(q,n,+1) for the three sign-twin pairs.
    (c) the forcing thresholds are the closed forms above, so A088250's
        a(15) is a multiple of 30030 and its a(16) of 510510 -- and every
        published term above the exception zone obeys its forced primes.
    """
    for fam in FAMILIES:
        for q in primerange(2, 400):
            for n in range(1, 31):
                if w(q, n, fam) >= q:
                    return False, (f"G2c FAIL: {fam}: w({q},{n}) = "
                                   f"{w(q, n, fam)} >= q -- a fixed prime "
                                   f"divisor")
    for plus, minus in (("A088250", "A088651"), ("A173750", "A125838"),
                        ("A164325", "A164326")):
        for q in primerange(2, 200):
            for n in (2, 5, 9, 14, 17, 24):
                kp = forbidden_k_residues(q, n, plus)
                km = forbidden_k_residues(q, n, minus)
                if {(-u) % q for u in kp} != km:
                    return False, (f"G2c FAIL: q={q} n={n}: K({minus}) is not "
                                   f"the negative of K({plus})")
    for fam, want in FORCING.items():
        got = {q: forcing_n(q, fam) for q in want}
        if got != want:
            return False, f"G2c FAIL: {fam} forcing thresholds {got}, want {want}"
        for n, k in KNOWN[fam].items():
            for q, at in want.items():
                if n >= at and k % q:
                    # below the floor a form may BE the prime q (the
                    # exception zone); above it the lemma is binding
                    if k >= K_FLOOR or not any(
                            value(fam, k, i) == q
                            for i in range(rungs_from(fam), n + 1)):
                        return False, (f"G2c FAIL: {fam} a({n}) = {k} is not "
                                       f"divisible by {q}, which the forcing "
                                       f"lemma requires from n = {at}")
    return True, ("G2c ok: w(q,n,F) < q at every prime q < 400 for n <= 30 "
                  "in all seven families, so no fixed prime divisor exists; "
                  "K(q,n,-1) = -K(q,n,+1) for the three sign-twin pairs at "
                  "every q < 200 and six filters; the forcing thresholds are "
                  "the closed forms (1..n: q from n = q-1; 2..n: q+1; 3..n: "
                  "q+2; odd: q), so a(15) of A088250 is a multiple of 30030 "
                  "and a(16) of 510510, and every published term above the "
                  "exception zone obeys its forced primes")


def g2d_derived_identities():
    """The entries a find here settles for free, asserted on the literature.

    A202778(n) = A088250(n) exactly when A088250(n) has run exactly n (a
    rider index leaves A202778 open there: its own term is a larger k, and
    the published table shows it -- a(7) = 8,224,860 against A088250's
    512,820, which has run 8).  A071576(n) = A088250(n) / 2 for n >= 3: k
    is even from n = 2 because 1*k + 1 must be an odd prime, and 2ik + 1
    with k = k'/2 is the same ladder.  A202779 is to A088651 what A202778 is
    to A088250.
    """
    checks = 0
    for fam, ex in (("A088250", "A202778"), ("A088651", "A202779")):
        for n, k in KNOWN[fam].items():
            r = run_length(fam, k, cap=n + 3)
            if r == n:
                if KNOWN_ALSO[ex].get(n) != k:
                    return False, (f"G2d FAIL: {fam} a({n}) = {k} has run "
                                   f"exactly {n} but {ex}({n}) = "
                                   f"{KNOWN_ALSO[ex].get(n)}")
            else:
                if KNOWN_ALSO[ex].get(n) == k:
                    return False, (f"G2d FAIL: {fam} a({n}) = {k} has run {r} "
                                   f"> {n} yet {ex}({n}) equals it")
                if KNOWN_ALSO[ex].get(n, 0) <= k:
                    return False, (f"G2d FAIL: {ex}({n}) should exceed the "
                                   f"rider {k}")
            checks += 1
    for n, k in KNOWN["A088250"].items():
        if n >= 3:
            if k % 2 or KNOWN_ALSO["A071576"][n] != k // 2:
                return False, (f"G2d FAIL: A071576({n}) = "
                               f"{KNOWN_ALSO['A071576'][n]} != A088250({n})/2 "
                               f"= {k}/2")
            checks += 1
    # and the identity itself, from the definition: 2ik + 1 over i = 1..n
    for n, h in KNOWN_ALSO["A071576"].items():
        if n >= 3 and run_length("A088250", 2 * h, cap=n + 2) < n:
            return False, f"G2d FAIL: 2*A071576({n}) fails the A088250 ladder"
    return True, (f"G2d ok: on {checks} published terms, A202778(n) = "
                  f"A088250(n) and A202779(n) = A088651(n) exactly at the "
                  f"indices where the monotone term has run exactly n (and "
                  f"exceed it at the rider indices), and A071576(n) = "
                  f"A088250(n)/2 for n >= 3 -- the claims a find here "
                  f"settles for free")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce, g2b_killed_set_size,
         g2c_admissible_and_forcing, g2d_derived_identities, g2_rederive_small]

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
