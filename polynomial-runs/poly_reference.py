"""The oracle for the exact-run polynomial ladders -- slow, obviously
correct, sympy only.

    A165234(n) = least prime p such that 2x^2 + p is prime for x = 0..n-1
                 and composite for x = n
    A230663(n) = least prime p such that x^2 + 3*x + p is prime for
                 x = 0..n-1 but not for x = n
    A092120(n) = first prime p such that p + 4m^2 is prime for m = 0..n but
                 composite for m = n+1                       (offset 0)
    A347537(n) = smallest prime p such that k^4 + k^3 + k^2 + k + p is prime
                 for k = 0..n-1 but not for k = n

Four EXACT-RUN SHIFT LADDERS whose shifts are the values of a polynomial
with no constant term: one unknown prime p (the value at 0) and conditions
that differ only by an ADDITIVE constant,

    A165234:  2, 8, 18, 32, 50, ...             2x^2
    A230663:  4, 10, 18, 28, 40, ...            x^2 + 3x = x(x + 3)
    A092120:  4, 16, 36, 64, 100, ...           4m^2
    A347537:  4, 30, 120, 340, 780, ...         k^4 + k^3 + k^2 + k

They are the siblings of euler-prime-runs' A164926 (x^2 + x + p), which
T. D. Noe entered within days of A165234 (September 2009); A230663 is Zak
Seidov's (2013), A092120 Ray G. Opao's (2004, its last five terms Jens
Kruse Andersen's of 2008) and A347537 Jon E. Schoenfield's (2021, its last
three Bert Dobbelaere's of May 2026).

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

A FORM is a triple (a, b, e) meaning a*x^e + b, kept so that the engines
read their forms the way every project here does; every form of these
families is (1, c, 1): x + c.  The conditions a sieve can express at index
n are the ones that must be PRIME,

    x,  x + c(1),  x + c(2),  ...,  x + c(r)         r = run_of(n)

and the one that must NOT be, x + c(r + 1), is no sieve's business: it is
read by the classification, which reads every survivor's run to its end.

THE RUN, AND THE INDEX.  The RUN of a prime p is the number of leading
shifts c(1), c(2), ... whose value p + c(k) is prime -- the count of k >= 1,
p itself being the value at 0.  Three of the names count the polynomial's
argument from 0 and ask for n prime values, so a(n) is the first prime
whose run is EXACTLY n - 1; A092120 asks for m = 0..n prime, so its a(n) is
the first prime whose run is exactly n.  `run_of(fam, n)` and
`index_of(fam, r)` carry the two readings and nothing else in this project
knows the difference: a(n) has nforms(fam, n) = run_of(n) + 1 conditions
that must be prime.

THE RUN IS EXACT, SO THE SEQUENCES ARE NOT MONOTONE.  A prime with a longer
run is a term of a later index and says nothing about this one: A165234's
a(3) = 3, a(5) = 5, a(11) = 11 and a(29) = 29 are the primes p for which
2x^2 + p is prime for every x < p (the imaginary quadratic field
Q(sqrt(-2p)) has class number 2, and that list is complete), and A230663's
a(39) = 43 is Euler's polynomial shifted by one.  Every index's line
therefore starts at the bottom, p = 2, and what a sweep at filter n
establishes -- every prime below the cursor whose run is at least run_of(n),
each with its exact run -- settles the first occurrence of EVERY exact run
from there up at once.  A campaign sweeps one line from the bottom with the
filter at the lowest open index.

THE KNOWN TERMS ARE NOT CONTIGUOUS.  Each entry's %S list runs a(1) (or
a(0)) to a(15) (a(16) on A347537), and three of the entries add one term
far above it in a comment (a(29) = 29, a(39) = 43, a(19) = 163).  KNOWN
carries both; the FRONTIER is the index below the lowest OPEN one, and an
index whose term a comment settles is skipped by the campaign like an index
found early.

A230663 AND A164926 ARE ONE PROBLEM, SHIFTED.  x^2 + 3x + p = (x + 1)^2 +
(x + 1) + (p - 2), so x^2 + 3x + p is prime for x = 0..n-1 exactly when
y^2 + y + (p - 2) is prime for y = 1..n.  Two consequences, both PROVED
below and gated (G1d):
  * if p' = A164926(n + 1) then p' + 2 is prime (it is the value at y = 1)
    with run exactly n on A230663, so A230663(n) <= A164926(n + 1) + 2 --
    an UPPER BOUND at every open index of A230663 whose successor is known
    on A164926 (UPPER);
  * every prime p' with run n + 1 on A164926 gives p' + 2 with run n on
    A230663, so A164926(n + 1) >= A230663(n) - 2; and if A230663(n) - 2 is
    itself prime it has run exactly n + 1 on A164926 and the two are equal.
    A find of A230663(n) whose p - 2 is prime therefore SETTLES A164926(n +
    1) (launch.py also_settles), and one whose p - 2 is composite proves
    A164926(n + 1) > A230663(n) - 2.

Facts PROVED here rather than assumed, because both engines and the odds
model are built on them.

  THE KILLED SET.  For a prime q and a form x + c,  q | x + c  <=>  x == -c
  (mod q).  So

      K(q,n,F) = { -c mod q : c a constant of index n }

  and the engines sieve x against K(q,n,F) and nothing else.  w(q,n,F) is
  its size.  K(q,n) is a subset of K(q,n+1).

  ITS SIZE, BOUNDED.  Every shift is EVEN (2x^2; x(x + 3) is a product of
  two integers of opposite parity; 4m^2; k(k + 1)(k^2 + 1)), so w(2) = 1 at
  every index.  For odd q a quadratic a*x^2 + b*x takes at most (q + 1)/2
  distinct values modulo q (complete the square: it is a square times a
  unit, shifted), and the quartic k(k + 1)(k^2 + 1) at most q - 1 (it
  vanishes at 0 and at -1, so it is not a bijection of Z/q).  Hence

      w(q,n,F) <= min(nforms(n), (q + 1)/2)      quadratics, q odd
      w(q,n,F) <= min(nforms(n), q - 1)          A347537, q odd

  -- the primes to 59 keep about 5e-6 of the line at the open indices: the
  wheel is STRONG, the opposite of the primorial ladders' regime, and what
  the hunt pays for is the line rather than the candidate (the engine's
  wheel does most of the work).

  ADMISSIBLE AT EVERY n.  Both bounds are below q, so no prime kills every
  residue, Dickson's conjecture applies and every index of every entry is
  conjecturally attained (the entries say so themselves, citing the prime
  k-tuples conjecture and Mollin's theorem).

  THE FORCED CLASSES.  Every shift is even, so x is ODD.  Modulo 3 the
  first two forms kill two classes on every family: 2x^2 takes the values
  0 and 2, so x == 2 (mod 3) on A165234; x^2 + 3x, 4m^2 and the quartic
  take 0 and 1, so x == 1 (mod 3) on the other three.  So the class is
  5 (mod 6) on A165234 and 1 (mod 6) on A230663, A092120 and A347537, from
  the first index with two forms on (n = 2; n = 1 on A092120).  No prime
  past 3 is ever forced on the quadratics ((q + 1)/2 < q - 1 for q >= 5),
  and G2c checks the quartic to n = 30 at every prime under 400.

  THE EXCEPTION ZONE.  "q divides the value, so the value is composite"
  needs the value to EXCEED q.  The smallest value is x itself, so a sieve
  to q2 is valid from x > q2; the engines refuse to run below that
  (k_floor), and the primes from 2 to q2 are classified one at a time by
  brute force (prefix_hits).  It is not vacuous: A165234's a(3), a(5),
  a(11) and a(29) and A230663's a(9) = 13, a(15) = 19 and a(39) = 43 are
  primes a sieve would have "killed" by themselves.

Gates in this file: G1 (every known term is prime with a run of EXACTLY
its index's run and lies in its forced class), G1b (this project's own
finds), G1c (every index is the OEIS index: PUBLISHED rebuilt from the %S
and %O lines verbatim, the comment terms on top), G1d (the A164926 bounds
on A230663), G2 (the small terms re-derived exhaustively from the bare
definition, as first occurrences of each exact run), G2b (the killed set
three ways and its proved bound), G2c (admissibility and the forced
classes).
"""

from functools import lru_cache as _lru_cache

from sympy import isprime, primerange

# ---------------------------------------------------------------- families

# `poly`       the polynomial whose values are the shifts, as ascending
#              coefficients: (0, 0, 2) is 2x^2, (0, 1, 1, 1, 1) the quartic.
#              Its constant term is 0: the term itself is the value at 0.
# `var`        the letter the OEIS NAME gives the polynomial's argument (x,
#              m or k); `term` the letter it gives the term (p on every
#              entry), under which the evidence files carry it
#              (CONVENTIONS.md "Naming in an evidence file"); `index` the
#              name's index letter (n everywhere).
# `shift`      index = run + shift: 1 where the name counts the argument
#              from 0 and asks for n primes, 0 on A092120 (m = 0..n).
# `forms`      the condition in the name's own letters, for the evidence.
# `name`, `data`, `offset_line`, `revision`, `keywords`: the %N, %S (+%T),
#              %O, %I and %K lines VERBATIM from the OEIS export of
#              2026-10-08, which G1c rebuilds every index from.
# `comment_terms`  terms the entry states in a comment rather than its data
#              (far above the %S list), with the comment's words.
# `also`       entries a find can settle: A164926 from A230663 (module
#              docstring).
FAMILIES = {
    "A165234": {"kind": "polynomial", "poly": (0, 0, 2), "var": "x",
                "term": "p", "index": "n", "shift": 1,
                "forms": "2x^2 + p prime for x = 0..n-1, composite for "
                         "x = n (p prime)",
                "name": "Least prime p such that 2x^2 + p produces primes "
                        "for x=0..n-1 and composite for x=n.",
                "data": "2,17,3,1481,5,149,569,2081,2339,5939831,11,"
                        "33164857769,3217755097229,272259344081,"
                        "17762917045631",
                "offset_line": "1,1",
                "revision": "#18 Nov 05 2025 15:35:33",
                "keywords": "hard,nonn,more",
                "author": "T. D. Noe, Sep 09 2009",
                "frontier_by": "Daniel Suteu, Dec 22 2024",
                "comment_terms": {29: 29},
                "comment": "Other known values: a(14)=272259344081 and "
                           "a(29)=29. There are no other terms less than "
                           "10^12.",
                "also": ()},
    "A230663": {"kind": "polynomial", "poly": (0, 3, 1), "var": "x",
                "term": "p", "index": "n", "shift": 1,
                "forms": "x^2 + 3*x + p prime for x = 0..n-1, not prime "
                         "for x = n (p prime)",
                "name": "Least prime p such that x^2 + 3*x + p produces "
                        "primes for x = 0..n-1 but not x = n.",
                "data": "2,67,3,349,79,439,21559,14713,13,8123233,223,"
                        "3468214093,1701300344203,11613197109589,19",
                "offset_line": "1,1",
                "revision": "#17 Nov 05 2025 15:35:36",
                "keywords": "nonn,more",
                "author": "Zak Seidov, Oct 27 2013",
                "frontier_by": "Daniel Suteu, Dec 22 2024",
                "comment_terms": {39: 43},
                "comment": "a(39) = 43 and all other terms > 128865958933.",
                "also": ("A164926",)},
    "A092120": {"kind": "polynomial", "poly": (0, 0, 4), "var": "m",
                "term": "p", "index": "n", "shift": 0,
                "forms": "p + 4m^2 prime for m = 0..n, composite for "
                         "m = n+1 (p prime)",
                "name": "a(n) is the first term p in a sequence of primes "
                        "such that p+4m^2 is prime for m = 0 to n, but "
                        "composite for m = n+1; a(n) = -1 if no such prime "
                        "exists.",
                "data": "2,19,3,277,43,53593,7,67,37,1483087,1867783,"
                        "9671300983,376040154163,13491637509487,"
                        "604490757900187,409333",
                "offset_line": "0,1",
                "revision": "#9 Feb 08 2019 12:30:38",
                "keywords": "nonn",
                "author": "Ray G. Opao, Mar 29 2004",
                "frontier_by": "Jens Kruse Andersen, Oct 24 2008",
                "comment_terms": {19: 163},
                "comment": "a(19)=163. All other terms after a(15) are "
                           "greater than 10^17 (if they exist).",
                "also": ()},
    "A347537": {"kind": "polynomial", "poly": (0, 1, 1, 1, 1), "var": "k",
                "term": "p", "index": "n", "shift": 1,
                "forms": "k^4 + k^3 + k^2 + k + p prime for k = 0..n-1, "
                         "not prime for k = n (p prime)",
                "name": "a(n) is the smallest prime p such that the "
                        "polynomial k^4 + k^3 + k^2 + k + p yields primes "
                        "for k = 0..n-1, but not for k = n.",
                "data": "2,3,13,37,109,7,1093,457,43,430879,130901527,"
                        "1838420599,48181700197,19179409633399,"
                        "699669742107967,1500599554819",
                "offset_line": "1,1",
                "revision": "#26 May 12 2026 15:34:15",
                "keywords": "nonn,more",
                "author": "Jon E. Schoenfield, Sep 11 2021",
                "frontier_by": "Bert Dobbelaere, May 12 2026",
                "comment_terms": {},
                "comment": "",
                "also": ()},
}

ALIASES = {}

# The published data of A164926 (Least prime p such that x^2+x+p produces
# primes for x=0..n-1 and composite for x=n; euler-prime-runs' entry) that
# BOUND A230663 (module docstring): a(16) from its comment, a(17)-a(19)
# from its %S data and a(21) from its comment (J. Waldvogel and Peter
# Leikauf, via Jens Kruse Andersen, Sep 09 2009), export of 2026-10-08.
# a(20) is open.
A164926 = {16: 17, 17: 348284517256411907, 18: 8461068614861832371,
           19: 3744101869688673856367, 21: 234505015943235329417}

# UPPER BOUNDS at open indices, derived: A230663(n) <= A164926(n + 1) + 2.
UPPER = {"A230663": {n - 1: p + 2 for n, p in A164926.items()}}


def _published(fam):
    """{OEIS index: term}, from the %S data and the %O offset, verbatim."""
    f = FAMILIES[fam]
    off = int(f["offset_line"].split(",")[0])
    return {off + i: int(v) for i, v in enumerate(f["data"].split(","))}


# The published terms, as published, keyed by the OEIS INDEX (%O).
PUBLISHED = {fam: _published(fam) for fam in FAMILIES}

# The published terms this project builds on: the %S list plus the terms
# the entry's comment states.  Sparse: see `frontier`.
KNOWN = {fam: {**PUBLISHED[fam], **FAMILIES[fam]["comment_terms"]}
         for fam in FAMILIES}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against;
# these are the project's own claim, which a campaign carries in its
# checkpoint (`found`).  G1b re-checks whatever lands here.
FOUND = {fam: {} for fam in FAMILIES}

# The engines refuse to run at or below the sieve depth (the exception zone:
# a value can BE the small prime that would otherwise divide it), and the
# prefix is covered by brute force.
K_FLOOR = 10 ** 4


def family(fam):
    """The canonical family key, aliases resolved; raises on an unknown one."""
    fam = str(fam).upper()
    fam = ALIASES.get(fam, fam)
    if fam not in FAMILIES:
        raise KeyError(f"no family {fam!r}; the families are "
                       f"{', '.join(sorted(FAMILIES))}")
    return fam


def kind(fam):
    return FAMILIES[family(fam)]["kind"]


def letter(fam):
    """The letter the OEIS name gives the term: p."""
    return FAMILIES[family(fam)]["term"]


def var(fam):
    """The letter the OEIS name gives the polynomial's argument."""
    return FAMILIES[family(fam)]["var"]


def offset(fam):
    """The OEIS index of the family's first term (its %O offset)."""
    return int(FAMILIES[family(fam)]["offset_line"].split(",")[0])


def run_of(fam, n):
    """The run a term of index n has: n less the family's index shift."""
    r = int(n) - FAMILIES[family(fam)]["shift"]
    if r < 0:
        raise ValueError(f"{fam} has no index {n}")
    return r


def index_of(fam, r):
    """The index a prime with run r is a candidate for."""
    return int(r) + FAMILIES[family(fam)]["shift"]


def term(fam, n, missing=KeyError):
    """a(n) from the literature or this project's finds; `missing=None`
    returns None instead of raising."""
    fam, n = family(fam), int(n)
    for table in (KNOWN[fam], FOUND[fam]):
        if n in table:
            return int(table[n])
    if missing is None:
        return None
    raise KeyError(f"{fam} a({n}) is not known")


def settled(fam):
    """Every index whose term is known: the literature and the finds."""
    fam = family(fam)
    return frozenset(KNOWN[fam]) | frozenset(int(n) for n in FOUND[fam])


def frontier(fam):
    """The largest n with a(offset..n) all known: the index below the LOWEST
    open one.  (A term known above an open index -- a comment's, or one
    found early -- does not move it.)"""
    fam = family(fam)
    n = offset(fam) - 1
    while term(fam, n + 1, missing=None) is not None:
        n += 1
    return n


def open_indices(fam, count=3, start=None):
    """The next `count` indices with no known term, from `start` (default
    the one above the frontier) up, skipping the ones a comment or an early
    find settled."""
    fam = family(fam)
    s, out = settled(fam), []
    n = frontier(fam) + 1 if start is None else int(start)
    while len(out) < count:
        if n not in s:
            out.append(n)
        n += 1
    return out


def poly_value(fam, k):
    """The polynomial's value at k: the shift c(k), with c(0) = 0."""
    k = int(k)
    v, pk = 0, 1
    for a in FAMILIES[family(fam)]["poly"]:
        v += a * pk
        pk *= k
    return v


@_lru_cache(maxsize=None)
def shift_k(fam, k):
    """c(k), k >= 1: the polynomial's value at k."""
    fam, k = family(fam), int(k)
    if k < 1:
        raise ValueError("the shifts are indexed from 1")
    return poly_value(fam, k)


def constants(fam, n):
    """The additive constants of the conditions that must be PRIME at index
    n, in form order: 0 (the term itself) then c(1), ..., c(run_of(n))."""
    fam = family(fam)
    return [0] + [shift_k(fam, k) for k in range(1, run_of(fam, n) + 1)]


def forms(fam, n):
    """The conditions on x at index n, as (a, b, e) with a*x^e + b prime:
    (1, c, 1) for every constant c."""
    return [(1, c, 1) for c in constants(fam, n)]


def nforms(fam, n):
    """How many conditions index n requires to be prime."""
    return len(constants(fam, n))


def maxkills(fam, n):
    """The most residues one prime can kill at index n: one per form."""
    return nforms(fam, n)


def in_domain(fam, x):
    """Whether x is in the sequence's DOMAIN: a prime."""
    family(fam)
    x = int(x)
    return x >= 2 and bool(isprime(x))


def floor_x(fam, n):
    """The definition's own floor for a(n), INCLUSIVE: 2, the least prime,
    at every index -- the sequences are not monotone, so no earlier term
    bounds a later one."""
    family(fam)
    int(n)
    return 2


def value(f, x):
    """The value of form f = (a, b, e) at x."""
    a, b, e = f
    return a * int(x) ** e + b


def values(fam, x, n):
    """Every value the conditions at index n form at x, in form order."""
    return [value(f, x) for f in forms(fam, n)]


def run_length(fam, x, cap=64):
    """The run of x: 0 if x is not prime, else the largest r <= cap with
    x + c(k) prime for every k = 1..r."""
    fam, x = family(fam), int(x)
    if not in_domain(fam, x):
        return 0
    r = 0
    while r < cap and isprime(x + shift_k(fam, r + 1)):
        r += 1
    return r


def is_term(fam, x, n):
    """x is a prime whose run is EXACTLY run_of(n).  NOT the least-claim:
    that is a sweep's to make."""
    fam, x = family(fam), int(x)
    r = run_of(fam, n)
    return in_domain(fam, x) and run_length(fam, x, cap=r + 1) == r


def first_reach(fam, n, above=0):
    """(m, a(m)): the least known term of index m >= n that is above
    `above` -- the first prime a sweep from there meets with a run of AT
    LEAST run_of(n), as far as the known terms say.  What a canary at
    filter n must find above the exception zone."""
    fam = family(fam)
    both = dict(KNOWN[fam])
    both.update(FOUND[fam])
    x, m = min((x, m) for m, x in both.items() if m >= int(n) and x > above)
    return m, x


def forbidden_k_residues(q, n, fam):
    """The residues of x mod q at which some condition of index n is
    divisible by q -- by walking every residue and testing divisibility."""
    fs = forms(fam, n)
    return [r for r in range(q)
            if any((a * pow(r, e, q) + b) % q == 0 for a, b, e in fs)]


def w(q, n, fam):
    """|K(q,n,F)|, from the walk."""
    return len(forbidden_k_residues(q, n, fam))


def killed_algebraic(q, n, fam):
    """K(q,n,F) the algebraic way: { -c mod q } over the constants."""
    return {(-c) % q for c in constants(fam, n)}


def w_count(q, n, fam):
    """|K(q,n,F)| the algebraic way.  G2b proves it equal to the walk."""
    return len(killed_algebraic(q, n, fam))


def w_bound(q, n, fam):
    """The PROVED upper bound on w(q,n,F) (module docstring)."""
    fam = family(fam)
    q, n = int(q), int(n)
    if q == 2:
        return 1
    deg = len(FAMILIES[fam]["poly"]) - 1
    image = (q + 1) // 2 if deg == 2 else q - 1
    return min(nforms(fam, n), image)


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
    """(ok, q): ok unless some prime q has every residue killed at index n.
    A theorem here (w <= the bound < q), checked anyway on every prime up
    to the form count, the only ones that could be covered."""
    for q in primerange(2, maxkills(fam, n) + 2):
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
    """The least prime x >= lo (default 2) whose run is EXACTLY run_of(n),
    by the bare definition, one integer at a time; None if there is none
    below hi.  The slowest thing in this project."""
    fam, n = family(fam), int(n)
    x = floor_x(fam, n) if lo is None else int(lo)
    while hi is None or x < hi:
        if is_term(fam, x, n):
            return x
        x += 1
    return None


def prefix_hits(fam, n, lo, hi, floor=1, cap=64):
    """[(x, run)] for every x in [lo, hi] with a run of at least `floor`,
    by the bare definition -- how the exception zone between the
    definition's floor and the engine's is covered."""
    fam = family(fam)
    out = []
    for x in range(int(lo), int(hi) + 1):
        r = run_length(fam, x, cap=cap)
        if r >= floor:
            out.append((x, r))
    return out


# --------------------------------- gates -----------------------------------

# How far G2 walks each line by brute force: every prime below the bound has
# its exact run read, and the first occurrence of each run length must be
# the known term of that index.
REGEN_X = {"A165234": 1_000_000, "A230663": 1_000_000,
           "A092120": 2_000_000, "A347537": 1_000_000}

# The first index with two forms: the forced class holds from there on.
FORCED_FROM = {fam: index_of(fam, 1) for fam in FAMILIES}
_WANT_UNIT = {"A165234": (5, 6), "A230663": (1, 6), "A092120": (1, 6),
              "A347537": (1, 6)}


def g1_knowns_reproduce():
    """Every known term is a prime whose run is EXACTLY its index's run, in
    its forced class (the primes 2 and 3 excepted); the %S list is
    contiguous from the offset to the frontier and every comment term sits
    above it."""
    parts = []
    for fam in FAMILIES:
        known = KNOWN[fam]
        for n in sorted(known):
            x = known[n]
            if not in_domain(fam, x):
                return False, f"G1 FAIL: {fam} a({n}) = {x} is not prime"
            r = run_length(fam, x, cap=run_of(fam, n) + 3)
            if r != run_of(fam, n):
                return False, (f"G1 FAIL: {fam} a({n}) = {x} has run {r}, "
                               f"not exactly {run_of(fam, n)}")
            if not is_term(fam, x, n):
                return False, f"G1 FAIL: {fam} a({n}) = {x}: is_term disagrees"
            if n >= FORCED_FROM[fam] and x > 3:
                for q in forced_primes(fam, n):
                    if x % q != forced_residue(q, n, fam):
                        return False, (f"G1 FAIL: {fam} a({n}) = {x} is not in "
                                       f"the class {q} forces")
        top = frontier(fam)
        if sorted(PUBLISHED[fam]) != list(range(offset(fam), top + 1)):
            return False, (f"G1 FAIL: {fam}'s published terms are not "
                           f"a({offset(fam)})..a({top})")
        extra = sorted(FAMILIES[fam]["comment_terms"])
        if any(m <= top for m in extra) or set(known) != set(PUBLISHED[fam]) | set(extra):
            return False, f"G1 FAIL: {fam}'s comment terms {extra} are not above a({top})"
        parts.append(f"{fam} a({offset(fam)})-a({top})"
                     + "".join(f" and a({m}) = {known[m]}" for m in extra))
    return True, ("G1 ok: " + "; ".join(parts) + " -- every term is a prime "
                  "whose run is EXACTLY its index's run and lies in its "
                  "forced class, the data contiguous to the frontier and "
                  "each comment term above it")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition."""
    parts = []
    for fam in FAMILIES:
        found = FOUND[fam]
        if not found:
            continue
        for n in sorted(found):
            if n in KNOWN[fam]:
                return False, f"G1b FAIL: {fam} a({n}) is already published"
            if not is_term(fam, found[n], n):
                return False, (f"G1b FAIL: {fam} a({n}) = {found[n]} is not a "
                               f"prime with a run of exactly {run_of(fam, n)}")
        parts.append(f"{fam} a({min(found)})-a({max(found)})")
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each against the bare definition the moment "
                      "one is entered in FOUND")
    return True, "G1b ok: this project's finds " + "; ".join(parts)


def g1c_every_index_is_the_oeis_index():
    """PUBLISHED is the %S list keyed by the %O offset, KNOWN is PUBLISHED
    plus the comment terms, and the index arithmetic is the name's: a(n)
    has n forms where the name counts from 0 to n - 1, n + 1 on A092120."""
    rows = []
    for fam, f in FAMILIES.items():
        off = int(f["offset_line"].split(",")[0])
        data = [int(v) for v in f["data"].split(",")]
        want = {off + i: v for i, v in enumerate(data)}
        if PUBLISHED[fam] != want or offset(fam) != off:
            return False, f"G1c FAIL: {fam}'s PUBLISHED is not its %S list keyed by %O"
        if KNOWN[fam] != {**want, **f["comment_terms"]}:
            return False, f"G1c FAIL: {fam}'s KNOWN is not PUBLISHED plus the comment terms"
        top = frontier(fam)
        if top != off + len(data) - 1:
            return False, f"G1c FAIL: {fam}'s frontier is a({top})"
        nf = nforms(fam, top + 1)
        want_nf = (top + 1) + (1 - f["shift"])
        if nf != want_nf or index_of(fam, run_of(fam, top + 1)) != top + 1:
            return False, (f"G1c FAIL: {fam} a({top + 1}) has {nf} forms, the "
                           f"name says {want_nf}")
        if open_indices(fam)[0] != top + 1 or any(
                m in open_indices(fam, 40) for m in f["comment_terms"]):
            return False, f"G1c FAIL: {fam}'s open indices are {open_indices(fam, 6)}"
        rows.append(f"{fam} %O {f['offset_line']}: a({off})..a({top}) "
                    f"published, open a({top + 1}) with {nf} conditions"
                    + (f", a({', '.join(map(str, sorted(f['comment_terms'])))}) "
                       f"from the comment" if f["comment_terms"] else "")
                    + f"; next open {open_indices(fam, 4)}")
    return True, "G1c ok: " + "; ".join(rows)


def g1d_a164926_bounds_a230663():
    """x^2 + 3x + p = (x + 1)^2 + (x + 1) + (p - 2): every A164926 term p'
    of index n + 1 gives p' + 2 prime with run exactly n on A230663, so
    A230663(n) <= A164926(n + 1) + 2; the bound is checked by the bare
    definition on every row of UPPER, and the identity on the known
    overlap (A230663's a(39) = 43 is A164926's a(40) = 41 plus two)."""
    rows = []
    for n, p2 in sorted(UPPER["A230663"].items()):
        if not isprime(p2) or not is_term("A230663", p2, n):
            return False, (f"G1d FAIL: {p2} = A164926({n + 1}) + 2 does not "
                           f"have run exactly {run_of('A230663', n)} on A230663")
        if n in KNOWN["A230663"] and KNOWN["A230663"][n] > p2:
            return False, f"G1d FAIL: A230663 a({n}) is above its bound {p2}"
        rows.append(f"a({n}) <= {p2}")
    if not is_term("A230663", 41 + 2, 39) or run_length("A230663", 43) != 38:
        return False, "G1d FAIL: a(39) = 43 is not Euler's 41 plus two"
    # the identity, pointwise: the A230663 INDEX of p (its run plus one:
    # x = 0..ra prime) is one less than the count of y >= 0 with
    # y^2 + y + (p - 2) prime, for every prime p whose p - 2 is prime
    for p in primerange(5, 5000):
        if isprime(p - 2):
            ra = run_length("A230663", p, cap=60)
            rb = 0
            while rb < 61 and isprime(rb * rb + rb + (p - 2)):
                rb += 1
            if rb - 1 != index_of("A230663", ra):
                return False, f"G1d FAIL: the identity fails at p = {p}"
    return True, ("G1d ok: A230663(n) <= A164926(n + 1) + 2 at " +
                  ", ".join(rows) + " (each bound a prime with EXACTLY the "
                  "run of its index, by the bare definition); the identity "
                  "x^2 + 3x + p = (x + 1)^2 + (x + 1) + (p - 2) checked "
                  "pointwise on every twin-prime pair under 5000 and on "
                  "a(39) = 43 against Euler's 41")


def g2_rederive_small():
    """Walk every prime below REGEN_X, read its exact run from the bare
    definition, and require the first occurrence of each run length to be
    the known term of that index -- and no run length to appear below the
    bound whose term is known above it or not known at all."""
    done = []
    for fam in FAMILIES:
        first = {}
        for x in primerange(2, REGEN_X[fam]):
            r = run_length(fam, x)
            if r not in first:
                first[r] = x
        first = {index_of(fam, r): x for r, x in first.items()}
        want = {n: x for n, x in KNOWN[fam].items() if x < REGEN_X[fam]}
        if first != want:
            return False, (f"G2 FAIL: {fam}: the first occurrences below "
                           f"{REGEN_X[fam]} are {first}, known {want}")
        for n, x in want.items():
            if first_x(fam, n, lo=max(2, x - 50), hi=x + 1) != x:
                return False, f"G2 FAIL: first_x disagrees at {fam} a({n})"
        done.append(f"{fam} a({', '.join(map(str, sorted(want)))}) below "
                    f"{REGEN_X[fam]:,}")
    return True, ("G2 ok: " + "; ".join(done) + " -- every prime below each "
                  "bound read from the definition alone, the first occurrence "
                  "of each exact run is the known term of its index (the "
                  "comment terms a(29) = 29, a(39) = 43 and a(19) = 163 "
                  "among them), and no other run length occurs there")


def _filters(fam):
    top = frontier(fam)
    return sorted({offset(fam) + 1, 2, 5, 9, top - 2, top, top + 1, top + 4})


def g2b_killed_set_three_ways():
    """K(q,n,F) by the residue walk, by the algebraic construction and by
    direct divisibility of the values, at every prime under 120 and a
    spread of filters; the proved bound holds; K(q,n) grows with n."""
    checked = 0
    for fam in FAMILIES:
        prev = {}
        for n in sorted(set(_filters(fam)) | {3, 4, 6, 7, 8}):
            for q in primerange(2, 120):
                walk = set(forbidden_k_residues(q, n, fam))
                alg = killed_algebraic(q, n, fam)
                if walk != alg or w_count(q, n, fam) != len(walk):
                    return False, (f"G2b FAIL: K({q},{n},{fam}) differs between "
                                   f"the walk and the construction")
                for r in range(q):
                    x = K_FLOOR * q * 10 ** 6 + r
                    direct = any(v % q == 0 for v in values(fam, x, n))
                    if direct != (r in walk):
                        return False, (f"G2b FAIL: K({q},{n},{fam}) disagrees "
                                       f"with divisibility at x = {x}")
                if len(walk) > w_bound(q, n, fam):
                    return False, (f"G2b FAIL: w({q},{n},{fam}) = {len(walk)} "
                                   f"passes the proved bound {w_bound(q, n, fam)}")
                if n - 1 in prev and not prev[n - 1].get(q, set()) <= walk:
                    return False, f"G2b FAIL: K({q},{n},{fam}) lost a residue"
                prev.setdefault(n, {})[q] = walk
                checked += 1
    return True, (f"G2b ok: K(q,n,F) three ways -- residue walk, {{-c mod q}} "
                  f"and direct divisibility -- agree at all {checked} "
                  f"(q < 120, n, F), each inside its proved bound (min(forms, "
                  f"(q + 1)/2) on the quadratics, min(forms, q - 1) on the "
                  f"quartic, 1 at q = 2), and K(q,n) is a subset of K(q,n+1)")


def g2c_admissible_and_forced():
    """Every filter to n = 30 is admissible (w < q at every prime under
    400); the forced primes are exactly 2 at the first index and 2 and 3
    from the first index with two forms on (classes 5, 1, 1 and 1 mod 6);
    no prime past 3 is ever forced."""
    rows = []
    for fam in FAMILIES:
        r, u = _WANT_UNIT[fam]
        for n in range(offset(fam), 31):
            for q in primerange(2, 400):
                if w(q, n, fam) >= q:
                    return False, (f"G2c FAIL: {fam} n={n}: q={q} kills every "
                                   f"residue")
            forced = forced_primes(fam, n)
            want = [2, 3] if n >= FORCED_FROM[fam] else [2]
            if forced != want:
                return False, (f"G2c FAIL: {fam} forces {forced} at n = {n}, "
                               f"expected {want}")
            rr, mm = 0, 1
            for q in forced:
                a = forced_residue(q, n, fam)
                rr, mm = rr + mm * (((a - rr) * pow(mm, -1, q)) % q), mm * q
            if n >= FORCED_FROM[fam] and (rr, mm) != (r, u):
                return False, (f"G2c FAIL: {fam} n={n}: the forced class is "
                               f"{rr} (mod {mm}), expected {r} (mod {u})")
        ok, q = admissible(fam, 30)
        if not ok:
            return False, f"G2c FAIL: {fam} is not admissible at n = 30 ({q})"
        rows.append(f"{fam} x == {r} (mod {u}) from n = {FORCED_FROM[fam]}")
    return True, ("G2c ok: every filter to n = 30 is admissible at every prime "
                  "under 400, the forced classes are exactly " +
                  "; ".join(rows) + " (2 alone before that), and no prime "
                  "past 3 is forced")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce,
         g1c_every_index_is_the_oeis_index, g1d_a164926_bounds_a230663,
         g2b_killed_set_three_ways, g2c_admissible_and_forced,
         g2_rederive_small]


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
