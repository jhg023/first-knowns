"""The oracle for the cyclotomic ladders -- slow, obviously correct, sympy only.

    A070737(n) = the smallest number x such that the first n cyclotomic
                 polynomials evaluated at x are primes: Phi_1(x), ...,
                 Phi_n(x) all prime
    A072942(n) = the least x such that the cyclotomic polynomial values
                 Phi(d,x) are prime for all d dividing n
    A233512(n) = "the first n cyclotomic polynomials are simultaneously
                 prime for these arguments": A070737's ladder with the
                 arguments STRICTLY INCREASING, a derived entry that every
                 A070737 find settles (below)

Two CYCLOTOMIC LADDERS: one unknown x and a set of conditions that differ
in which cyclotomic polynomial is evaluated.  A070737 is Don Reble's (May
2002) with Phil Carmody (Aug 2002), ten terms to a(10) = 1.35e16 and not
one added in twenty-four years; A072942 is Carmody's (Aug 2002), corrected
and extended by Reble (Feb 2014) to n = 39 in the data, n = 47 in the
b-file and n = 99 in an a-file with question marks at the ten indices
48, 60, 66, 72, 78, 80, 84, 88, 90, 96 -- the open ones.  A233512 is
T. D. Noe's (Dec 2013) restatement of A070737 with a(n) > a(n-1): its
a(4) = 150 is the least x > 6 with the first four values prime, and from
n = 5 on it is A070737 (G1d).

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW;
sympy's cyclotomic_poly, nthroot_mod, divisors, totient) and the
definition as written.

A FORM is a cyclotomic index k: the condition is Phi_k(x) prime, with
Phi_k the k-th cyclotomic polynomial (degree phi(k), coefficients in
{-1, 0, 1} for every k below 105), evaluated by Horner in Python ints.
The conditions of index n are

    A070737:   Phi_k(x), k = 1..n          (n forms, degrees 1, 1, 2, 2, 4, ...)
    A072942:   Phi_d(x), d | n, ascending  (tau(n) forms, total degree n)

where x is the engines' name for the term AND the letter both entries give
it.  A070737's ladder NESTS (every condition of index n is one of index
n + 1, so a(n+1) >= a(n), the line of a(n) starts AT a(n-1), and a(3) =
a(4) = 6); A072942's indices are separate problems, each its own line
from x = 3 (Phi_1(2) = 1 is not prime, so 2 never appears -- the entry's
own comment).

Facts PROVED here rather than assumed, because both engines and the odds
model are built on them.

  THE KILLED SET.  For a prime q and x not divisible by q,

      q | Phi_k(x)   <=>   ord_q(x) = k / q^v,   q^v || k

  (the classical lemma: a prime divides Phi_k(x) exactly when the order of
  x is k with its q-part stripped).  And Phi_k(0) = 1 for k >= 2, Phi_1(0)
  = -1, so the residue 0 is NEVER killed.  Hence for a form set S,

      K(q, S) = { x in (Z/q)^* : ord_q(x) in T_q(S) },
      T_q(S)  = { k / q^(v_q(k)) : k in S },

  the elements of each attainable order m (m | q - 1): phi(m) of them, the
  m-th roots of unity that are not d-th roots for any d < m.  It is built
  three ways below -- the residue walk (every residue, every value), the
  roots of unity by sympy's nthroot_mod, and direct divisibility of the
  values -- and the CPU engine builds it a fourth way (powers of a
  primitive root), G3.

  ITS SIZE, BOUNDED.  |K(q, S)| <= sum_{k in S} phi(k): sum_{k <= n} phi(k)
  on A070737 (128 at n = 20 exactly), n itself on A072942 (sum of phi(d)
  over d | n).  That is the residue list the GPU tail must hold
  (maxkills).  Its average over q is about |S| (an order m divides q - 1
  for one prime in phi(m)), so a prime kills about one residue per form
  on average -- but up to q - 1 where q - 1 is smooth: the wheel is of
  MIDDLE strength, between the power ladders' and the polynomial runs'.

  ADMISSIBLE AT EVERY n: the class 0 survives every prime (Phi_k(0) = +-1),
  so no prime covers every residue, Schinzel's hypothesis H applies (the
  entries' own comments) and every index is conjecturally attained.

  THE FORCED CLASSES, AND A FORMULA FOR THEM.  A prime q is FORCED -- x == 0
  (mod q) -- exactly when every order dividing q - 1 is in T_q(S), and the
  order q - 1 itself must be, so q - 1 = k / q^v <= max S: a forced prime is
  at most n + 1.  On A070737 that is every prime q <= n + 1 (then every
  divisor of q - 1 is a form): 2, 3 from n = 2; 5 from n = 4; 7 from n = 6;
  11 from n = 10; 13 from n = 12; 17 from n = 16.  On A072942 it is every
  prime q with (q - 1) | n (then every divisor of q - 1 divides n), and no
  other: at n = 60 the unit is 2*3*5*7*11*13*31*61, at n = 96 it holds 97.
  The forced class is 0 (mod every forced prime) -- r0 = 0 always.  G2c
  proves the formula against the walk at every filter to n = 30 and every
  n <= 99 of A072942.

  THE EXCEPTION ZONE.  "q divides the value, so the value is composite"
  needs the value to EXCEED q.  The smallest value is Phi_1(x) = x - 1, so
  a sieve to q2 is valid from x - 1 > q2; the engines refuse to run at or
  below x = q2 + 1 (k_floor), and the integers below are classified one at
  a time by brute force (prefix_hits).  Most of A072942's small terms --
  a(47) = 62, a(97) = 12 -- live there, and G2 re-derives them.

Gates in this file: G1 (every published term satisfies its definition,
A070737 is monotone with each frontier run exactly its index except a(3) =
6, which runs to 4 and IS a(4); every A072942 term is a solution of its own
index), G1b (this project's own finds), G1c (every index is the OEIS index:
KNOWN rebuilt from the %S/%T/%U and %O lines verbatim, the a-file values
apart from them), G1d (A233512 is A070737's increasing variant: a(4) = 150
is the least x > 6, and the data agree from n = 5), G2 (the small terms
re-derived exhaustively from the bare definition), G2b (the killed set
three ways, its proved bound, the nesting on A070737, residue 0 never
killed), G2c (admissibility and the forced primes equal to the formula).
"""

from functools import lru_cache as _lru_cache

from sympy import (Poly, Symbol, cyclotomic_poly, divisors, isprime,
                   nthroot_mod, primerange, totient)

# ---------------------------------------------------------------- families

# `kind`        "ladder" (the first n polynomials: nesting, one line per
#               family from the frontier term) or "divisors" (the
#               polynomials of the divisors of n: one line per INDEX from
#               x = 3).
# `term`        the letter the OEIS NAME gives the term (x on both), under
#               which the evidence files carry it (CONVENTIONS.md "Naming in
#               an evidence file"); `index` the name's index letter (n);
#               `poly` the letter the name gives the cyclotomic index (k --
#               the name says "the first n", its %C line says "each k from 1
#               to n" -- and d on A072942).
# `forms`       the condition in the name's own letters, for the evidence.
# `name`, `data`, `offset_line`, `revision`, `keywords`: the %N, %S/%T/%U,
#               %O, %I and %K lines VERBATIM from the OEIS export of
#               2026-10-23, which G1c rebuilds every index from.
# `afile`       A072942 only: the a-file (Don Reble, "Table of n, a(n) for n
#               = 1..99 (with question marks at the unknown entries)",
#               /A072942/a072942.txt, read 2026-10-23) beyond the %S/%T/%U
#               data: its known entries for n = 40..99, the question marks
#               being the open indices.  The b-file (n = 1..47) agrees.
# `also`        derived entries a find settles for free.
FAMILIES = {
    "A070737": {"kind": "ladder", "term": "x", "index": "n", "poly": "k",
                "forms": "Phi_k(x), k = 1..n",
                "name": "Smallest number x such that the first n cyclotomic "
                        "polynomials evaluated at x are primes.",
                "data": "3,4,6,6,1068630,6770610,2981997480,339126523890,"
                        "120351747887280,13533264289711320",
                "offset_line": "1,1",
                "revision": "#7 Oct 19 2017 03:14:01",
                "keywords": "nonn",
                "author": "Don Reble, May 15 2002 and Phil Carmody, Aug 09 2002",
                "frontier_by": "Don Reble and Phil Carmody, 2002",
                "afile": {},
                "also": ("A233512",)},
    "A072942": {"kind": "divisors", "term": "x", "index": "n", "poly": "d",
                "forms": "Phi(d,x), d | n",
                "name": "a(n) is the least x such that the cyclotomic "
                        "polynomial values Phi(d,x) are prime for all d "
                        "dividing n.",
                "data": "3,4,3,4,12,6,3,4,3,12,20,24687390,3,72,62,4,20,"
                        "1102903830,12,58051620,3,1793172,468,1035844571580,"
                        "62,882,398,75274140,6,81206805256038,14,1288005000,"
                        "78428,93888,37664,24380304369772260,432,3300,21962",
                "offset_line": "1,1",
                "revision": "#47 Jul 12 2018 08:57:35",
                "keywords": "nonn",
                "author": "Phil Carmody, Aug 12 2002",
                "frontier_by": "Don Reble, Feb 03 2014 (the a-file to n = 99)",
                "afile": {40: 16066737508140, 41: 14, 42: 143657627809878,
                          43: 114, 44: 36352614120, 45: 22874682, 46: 8953500,
                          47: 62, 49: 20550, 50: 3763118238, 51: 19388,
                          52: 37509098520, 53: 24, 54: 235734798214188,
                          55: 545948, 56: 257943509313180, 57: 101022,
                          58: 1335288, 59: 102, 61: 138, 62: 25170, 63: 3,
                          64: 4109355036960, 65: 906902, 67: 314,
                          68: 713139420, 69: 2278730, 70: 2355476281187040,
                          71: 3, 73: 114, 74: 717528, 75: 1176582692,
                          76: 1791027390, 77: 204378, 79: 140, 81: 5960484,
                          82: 7154268, 83: 930, 85: 199812, 86: 129918,
                          87: 3122672, 89: 114, 91: 208458, 92: 1125700552260,
                          93: 8664, 94: 145932, 95: 18618, 97: 12,
                          98: 1410193452, 99: 401248874},
                "also": ()},
}

# THE DERIVED ENTRY: A233512 (T. D. Noe, Dec 13 2013; hard,more; "a(7) >
# 2*10^9").  Its name gives the term no letter, so its records carry the
# integer under a(n) (CONVENTIONS.md).  Verbatim lines of the 2026-10-23
# export.
DERIVED = {
    "A233512": {"of": "A070737", "from_n": 5,
                # the name gives the term no letter; the entry's own %C
                # and %e lines call it x ("At x = 3, x-1 = 2"), so a
                # record carries the integer under x (CLAUDE.md 5i)
                "term": "x",
                "name": "The first n cyclotomic polynomials are "
                        "simultaneously prime for these arguments.",
                "data": "3,4,6,150,1068630,6770610",
                "offset_line": "1,1",
                "revision": "#6 Jan 23 2014 12:29:20",
                "keywords": "nonn,hard,more",
                "author": "T. D. Noe, Dec 13 2013",
                "comment": "a(7) > 2*10^9."},
}

ALIASES = {}

# The last index of A072942 the a-file states (and the campaign ranges over).
INDEX_TOP = 99

# The order the A072942 campaign takes its open indices in: the odds model's
# expected clock to each (cyclotomic_model, model_results.json), cheapest
# first, frozen here so that a campaign started with no flags is the same
# campaign tomorrow; G12 checks the model still ranks them so.
TARGETS = (66, 78, 88, 48, 80, 60, 72, 84, 96, 90)


def _published(fam):
    """{OEIS index: term}, from the %S data and the %O offset, verbatim,
    plus the a-file's known entries."""
    f = FAMILIES[fam]
    off = int(f["offset_line"].split(",")[0])
    out = {off + i: int(v) for i, v in enumerate(f["data"].split(","))}
    out.update({int(n): int(v) for n, v in f["afile"].items()})
    return out


# The published terms, keyed by the OEIS INDEX (%O).
KNOWN = {fam: _published(fam) for fam in FAMILIES}

# The indices the %S/%T/%U lines carry (G1c): a(1..10) and a(1..39).
DATA_INDICES = {fam: set(range(int(FAMILIES[fam]["offset_line"].split(",")[0]),
                               int(FAMILIES[fam]["offset_line"].split(",")[0])
                               + len(FAMILIES[fam]["data"].split(","))))
                for fam in FAMILIES}

# A PUBLISHED TERM WHOSE RUN PASSES ITS INDEX: A070737's a(3) = 6 has run 4
# and IS a(4) = 6 (the OEIS lists both).  G1 proves it from the definition.
RUNS_PAST = {"A070737": {3: 4}}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against;
# these are the project's own claim, which a campaign carries in its
# checkpoint (`found`).  G1b re-checks whatever lands here.
FOUND = {fam: {} for fam in FAMILIES}

# The exception zone is covered by brute force; G2b's divisibility checks
# run their values at heights well above any sieve depth.
K_FLOOR = 10 ** 4

# The least x of either entry: Phi_1(x) = x - 1 must be a prime, so x >= 3.
X_MIN = 3

_X = Symbol("x")


@_lru_cache(maxsize=None)
def cyclotomic(k):
    """The coefficients of the k-th cyclotomic polynomial, LOWEST degree
    first, from sympy."""
    k = int(k)
    if k < 1:
        raise ValueError(f"no cyclotomic polynomial of index {k}")
    cs = Poly(cyclotomic_poly(k, _X), _X).all_coeffs()
    return tuple(int(c) for c in reversed(cs))


def degree(k):
    """deg Phi_k = phi(k)."""
    return int(totient(int(k)))


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


def per_index(fam):
    """True for a family whose every index is its own line (A072942)."""
    return kind(fam) == "divisors"


def letter(fam):
    """The letter the OEIS name gives the term: x on both entries."""
    return FAMILIES[family(fam)]["term"]


def offset(fam):
    return int(FAMILIES[family(fam)]["offset_line"].split(",")[0])


def term(fam, n, missing=KeyError):
    """a(n) from the literature or this project's finds."""
    fam, n = family(fam), int(n)
    for table in (KNOWN[fam], FOUND[fam]):
        if n in table:
            return int(table[n])
    if missing is None:
        return None
    raise KeyError(f"{fam} a({n}) is not known")


def frontier(fam):
    """The largest n with a(1..n) all known (the literature and the finds)
    -- a LADDER's frontier; on A072942 the indices are separate problems
    (`open_indices`)."""
    fam = family(fam)
    n = offset(fam) - 1
    while term(fam, n + 1, missing=None) is not None:
        n += 1
    return n


def open_indices(fam, top=INDEX_TOP):
    """The indices up to `top` with no published term and no find, in
    order: A072942's 48, 60, 66, 72, 78, 80, 84, 88, 90, 96."""
    fam = family(fam)
    return tuple(n for n in range(offset(fam), int(top) + 1)
                 if term(fam, n, missing=None) is None)


def forms(fam, n):
    """The cyclotomic indices k whose Phi_k(x) must be prime at index n, in
    the order the run is read: 1..n on A070737, the divisors of n ascending
    on A072942."""
    fam, n = family(fam), int(n)
    if n < 1:
        raise ValueError(f"index {n} of {fam} imposes no condition")
    if kind(fam) == "ladder":
        return tuple(range(1, n + 1))
    return tuple(int(d) for d in divisors(n))


def nforms(fam, n):
    return len(forms(fam, n))


def total_degree(fam, n):
    """sum of deg Phi_k over the forms: the Bateman-Horn weight of an index."""
    return sum(degree(k) for k in forms(fam, n))


def max_degree(fam, n):
    return max(degree(k) for k in forms(fam, n))


def maxkills(fam, n):
    """The PROVED bound on how many residues one prime can kill at index n:
    sum of phi(k) over the forms (module docstring)."""
    return sum(degree(k) for k in forms(fam, n))


def value(k, x):
    """Phi_k(x), by Horner in Python ints."""
    v = 0
    for c in reversed(cyclotomic(k)):
        v = v * int(x) + c
    return v


def values(fam, x, n):
    """Every value the conditions of index n form at x, in form order."""
    return [value(k, x) for k in forms(fam, n)]


def run_length(fam, x, n):
    """The run of x against index n: the number of LEADING forms of index n
    (in form order) whose value is prime -- nforms(fam, n) when x satisfies
    the index.  On A070737 read with a larger n to see past an index."""
    fam, x = family(fam), int(x)
    if x < X_MIN:
        return 0
    r = 0
    for k in forms(fam, n):
        if not isprime(value(k, x)):
            break
        r += 1
    return r


def is_term(fam, x, n):
    """x satisfies index n: every form's value is prime.  NOT the
    least-claim: that is a sweep's to make."""
    return run_length(fam, x, n) == nforms(fam, n)


def floor_x(fam, n):
    """The definition's own floor for a(n), INCLUSIVE: on A070737 a(n - 1)
    itself when it is known (the ladder nests, and a(n - 1) IS a(n) when
    its run reaches n: a(3) = a(4)), else X_MIN; on A072942 always X_MIN --
    every index is its own line."""
    fam, n = family(fam), int(n)
    if kind(fam) != "ladder" or n <= offset(fam):
        return X_MIN
    prev = term(fam, n - 1, missing=None)
    return X_MIN if prev is None else max(X_MIN, prev)


def forbidden_k_residues(q, n, fam):
    """The residues of x mod q at which some condition of index n is
    divisible by q -- by walking every residue and testing divisibility."""
    q = int(q)
    ks = forms(fam, n)
    return [r for r in range(q) if any(value(k, r) % q == 0 for k in ks)]


def w(q, n, fam):
    """|K(q, S)|, from the walk."""
    return len(forbidden_k_residues(q, n, fam))


def reduced_orders(q, n, fam):
    """T_q(S): the orders the forms of index n ask for modulo q -- each k
    with its q-part stripped -- intersected with the divisors of q - 1."""
    q = int(q)
    out = set()
    for k in forms(fam, n):
        m = int(k)
        while m % q == 0:
            m //= q
        if (q - 1) % m == 0:
            out.add(m)
    return out


def killed_algebraic(q, n, fam):
    """K(q, S) the algebraic way: for each attainable order m, the m-th
    roots of unity (sympy's nthroot_mod) that are not roots of unity of any
    smaller order dividing m -- the elements of order exactly m."""
    q = int(q)
    out = set()
    for m in reduced_orders(q, n, fam):
        roots = set(int(r) % q for r in (nthroot_mod(1, m, q, all_roots=True) or []))
        if m == 1:
            roots = {1 % q}
        lower = set()
        for d in divisors(m):
            if d < m:
                lower |= set(int(r) % q for r in
                             (nthroot_mod(1, d, q, all_roots=True) or [1]))
        out |= roots - lower
    return out


def w_count(q, n, fam):
    """|K(q, S)| the algebraic way.  G2b proves it equal to the walk."""
    return len(killed_algebraic(q, n, fam))


def w_bound(q, n, fam):
    """The PROVED upper bound on w(q, S) (module docstring)."""
    return min(int(q) - 1, maxkills(fam, n))


def forced_formula(fam, n, upto=128):
    """The forced primes BY THE THEOREM of the module docstring: q <= n + 1
    on A070737; (q - 1) | n on A072942.  G2c checks the walk against it."""
    fam, n = family(fam), int(n)
    if kind(fam) == "ladder":
        return [q for q in primerange(2, upto) if q <= n + 1]
    return [q for q in primerange(2, upto) if n % (q - 1) == 0]


def forced_primes(fam, n, upto=128):
    """The primes that leave exactly one residue class at index n, by the
    walk."""
    return [q for q in primerange(2, upto) if w(q, n, fam) == q - 1]


def forced_residue(q, n, fam):
    """The one class a forced prime leaves (always 0 here); raises if q is
    not forced."""
    free = sorted(set(range(int(q))) - set(forbidden_k_residues(q, n, fam)))
    if len(free) != 1:
        raise ValueError(f"{q} is not forced at index {n} of {fam}: it leaves "
                         f"{len(free)} classes")
    return free[0]


def admissible(fam, n):
    """(ok, q): ok unless some prime q has every residue killed at index n.
    A theorem here (the class 0 survives every prime: module docstring),
    checked anyway on every prime up to the kill bound, the only ones that
    could be covered."""
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
    """The least x >= lo (default the definition's floor) that satisfies
    index n, by the bare definition, one integer at a time; None if there
    is none below hi.  The slowest thing in this project."""
    fam, n = family(fam), int(n)
    x = floor_x(fam, n) if lo is None else max(int(lo), X_MIN)
    while hi is None or x < hi:
        if is_term(fam, x, n):
            return x
        x += 1
    return None


def prefix_hits(fam, n, lo, hi, floor=1, read_n=None):
    """[(x, run)] for every x in [lo, hi] with a run of at least `floor`
    against index n (A070737: read against `read_n` >= n, to see past the
    index), by the bare definition -- how the exception zone is covered."""
    fam = family(fam)
    read_n = int(n) if read_n is None or kind(fam) != "ladder" else max(int(read_n), int(n))
    out = []
    for x in range(max(int(lo), X_MIN), int(hi) + 1):
        r = run_length(fam, x, read_n)
        if r >= floor:
            out.append((x, r))
    return out


# --------------------------------- gates -----------------------------------

# How far G2 walks each line by brute force.  A070737: every x below the
# bound has its run read (a twin-prime prefilter, then the definition), and
# the first occurrence of each run length must be the published term of
# that index -- a(1) to a(6) = 6,770,610 lie below 7e6.  A072942: every
# index n <= 99 whose term is under REGEN_DIV is re-derived, 70 of them.
REGEN_X = {"A070737": 7_000_000}
REGEN_DIV = 100_000


def g1_knowns_reproduce():
    """Every published term satisfies its definition; A070737 is monotone
    and each term's run is exactly its index, except a(3) = 6, which runs
    to 4 and is a(4) (RUNS_PAST); every forced prime divides every term
    above it; A072942's indices are separate problems (no monotonicity is
    claimed) and each term's value set is prime through its last divisor
    and no further claim is made."""
    parts = []
    fam = "A070737"
    known = KNOWN[fam]
    prev = 0
    for n in sorted(known):
        x = known[n]
        r = run_length(fam, x, n + 3)
        if r < n:
            return False, f"G1 FAIL: {fam} a({n}) = {x} has run {r} < {n}"
        want = RUNS_PAST.get(fam, {}).get(n, n)
        if r != want:
            return False, (f"G1 FAIL: {fam} a({n}) = {x} has run {r}, expected "
                           f"exactly {want}")
        if x < prev or x < floor_x(fam, n):
            return False, f"G1 FAIL: {fam} a({n}) = {x} < a({n - 1}) = {prev}"
        for q in forced_primes(fam, n):
            # a forced prime pins x only once every value EXCEEDS it (the
            # smallest is Phi_1(x) = x - 1): a(1) = 3 has Phi_1(3) = 2
            if x - 1 > q and x % q != forced_residue(q, n, fam):
                return False, (f"G1 FAIL: {fam} a({n}) = {x} is not in the "
                               f"class {q} forces")
        prev = x
    top = max(known)
    if isprime(value(top + 1, known[top])):
        return False, f"G1 FAIL: {fam}: Phi_{top + 1}(a({top})) is prime"
    parts.append(f"{fam} a(1)-a({top}) (a(3) = 6 runs to 4: a(4) = a(3))")
    fam = "A072942"
    known = KNOWN[fam]
    for n in sorted(known):
        x = known[n]
        if x < X_MIN or not is_term(fam, x, n):
            return False, (f"G1 FAIL: {fam} a({n}) = {x} does not make every "
                           f"Phi(d,x), d | {n}, prime")
        for q in forced_primes(fam, n):
            if x - 1 > q and x % q != forced_residue(q, n, fam):
                return False, (f"G1 FAIL: {fam} a({n}) = {x} is not in the "
                               f"class {q} forces")
    parts.append(f"{fam} a(1)-a(39) and the a-file's "
                 f"{len(FAMILIES[fam]['afile'])} entries to a(99)")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every published term "
                  "satisfies its definition, A070737 is monotone with each "
                  "frontier run exactly its index (Phi_11 of a(10) is "
                  "composite), every term lies in the class its forced primes "
                  "pin it to, and every A072942 value set is prime through "
                  "its last divisor")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition."""
    parts = []
    for fam in FAMILIES:
        found = FOUND[fam]
        if not found:
            continue
        for n in sorted(found):
            x = found[n]
            if kind(fam) == "ladder":
                prev = term(fam, n - 1)
                if x < prev or not is_term(fam, x, n):
                    return False, (f"G1b FAIL: {fam} a({n}) = {x} does not "
                                   f"satisfy index {n} at or above a({n - 1})")
            elif not is_term(fam, x, n):
                return False, f"G1b FAIL: {fam} a({n}) = {x} is not a solution"
        parts.append(f"{fam} " + ", ".join(f"a({n})" for n in sorted(found)))
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each against the bare definition the moment "
                      "one is entered in FOUND")
    return True, "G1b ok: this project's finds " + "; ".join(parts)


def g1c_every_index_is_the_oeis_index():
    """KNOWN is the %S/%T/%U list keyed by the %O offset, plus the a-file's
    entries at their own indices, and nothing else; the open indices are
    exactly the a-file's question marks."""
    rows = []
    for fam, f in FAMILIES.items():
        off = int(f["offset_line"].split(",")[0])
        data = [int(v) for v in f["data"].split(",")]
        want = {off + i: v for i, v in enumerate(data)}
        if off != 1 or offset(fam) != 1 or DATA_INDICES[fam] != set(want):
            return False, f"G1c FAIL: {fam}'s %O or data indices read wrong"
        if any(KNOWN[fam].get(n) != v for n, v in want.items()):
            return False, f"G1c FAIL: {fam}'s KNOWN is not its %S list keyed by %O"
        extra = {n: v for n, v in KNOWN[fam].items() if n not in want}
        if extra != {int(n): int(v) for n, v in f["afile"].items()}:
            return False, f"G1c FAIL: {fam}'s extra indices are not the a-file's"
        if any(n <= max(want) for n in extra):
            return False, f"G1c FAIL: {fam}'s a-file entries overlap the data"
        if kind(fam) == "ladder":
            if frontier(fam) != len(data) or extra:
                return False, f"G1c FAIL: {fam}'s frontier is a({frontier(fam)})"
            if [term(fam, i) for i in range(1, frontier(fam) + 1)] != data:
                return False, f"G1c FAIL: {fam}'s terms do not read back as %S"
            if nforms(fam, len(data) + 1) != len(data) + 1:
                return False, f"G1c FAIL: {fam}'s open index has the wrong form count"
            rows.append(f"{fam} %O {f['offset_line']}: a(1)..a({len(data)}), "
                        f"open a({len(data) + 1}) with {len(data) + 1} conditions")
        else:
            op = open_indices(fam)
            if op != tuple(sorted(TARGETS)) or len(KNOWN[fam]) + len(op) != INDEX_TOP:
                return False, (f"G1c FAIL: {fam}'s open indices are {op}, the "
                               f"a-file's question marks {sorted(TARGETS)}")
            for n in op:
                if nforms(fam, n) != len(divisors(n)):
                    return False, f"G1c FAIL: {fam} n = {n} has the wrong form count"
            rows.append(f"{fam} %O {f['offset_line']}: a(1)..a(39) in the data, "
                        f"{len(extra)} a-file entries to a(99), open "
                        + ", ".join(f"a({n})" for n in op))
    return True, "G1c ok: " + "; ".join(rows)


def g1d_derived_entry():
    """A233512 is A070737 with the arguments strictly increasing: its data
    agree with A070737's for n = 1..3 and from n = 5 on, and its a(4) = 150
    is the LEAST x > a(3) = 6 with the first four values prime (checked by
    walking x from 7); so every A070737 find at n >= 5 settles A233512 at
    the same index."""
    d = DERIVED["A233512"]
    off = int(d["offset_line"].split(",")[0])
    data = {off + i: int(v) for i, v in enumerate(d["data"].split(","))}
    base = KNOWN[d["of"]]
    for n, v in data.items():
        if n == 4:
            continue
        if base.get(n) != v:
            return False, f"G1d FAIL: A233512 a({n}) = {v} is not A070737's"
    walk = first_x("A070737", 4, lo=data[3] + 1)
    if walk != data[4] or not all(isprime(value(k, 150)) for k in range(1, 5)):
        return False, (f"G1d FAIL: the least x > 6 with four prime values is "
                       f"{walk}, A233512 says a(4) = {data[4]}")
    if d["from_n"] != 5 or min(n for n in data if n > 4) != 5:
        return False, "G1d FAIL: the index A233512 joins A070737 from is not 5"
    if not all(base[n] > base[n - 1] for n in range(5, max(base) + 1)):
        return False, "G1d FAIL: A070737 is not strictly increasing from n = 5"
    return True, ("G1d ok: A233512's data are A070737's at n = 1..3 and "
                  "n = 5..6, its a(4) = 150 is the least x > 6 with "
                  "Phi_1..Phi_4 prime (walked from 7), and A070737 is strictly "
                  "increasing from n = 5, so the two coincide from there: "
                  "every A070737 find settles A233512 at the same index "
                  "(and a(7)-a(10) of A233512 are A070737's published terms)")


def _primes_below(m):
    """A sieve of the primes below m (bytearray; nothing clever)."""
    s = bytearray([1]) * m
    s[0:2] = b"\x00\x00"
    for p in range(2, int(m ** 0.5) + 1):
        if s[p]:
            s[p * p::p] = bytearray(len(range(p * p, m, p)))
    return s


def g2_rederive_small():
    """Walk x from 3 and read its run from the bare definition: on A070737
    the first x with a run of at least n must be the published a(n) for
    every n it reaches (a(3) = a(4) = 6 included); on A072942 every index
    n <= 99 whose term is under REGEN_DIV must be the first solution of its
    own divisor set."""
    fam = "A070737"
    top_x = REGEN_X[fam]
    sv = _primes_below(top_x + 2)
    first, top = {}, 0
    for x in range(X_MIN, top_x):
        if not (sv[x - 1] and sv[x + 1]):     # Phi_1 and Phi_2 by the sieve
            r = 1 if sv[x - 1] else 0
        else:
            r = 2
            while r < 12 and isprime(value(r + 1, x)):
                r += 1
        while top < r:
            top += 1
            first[top] = int(x)
    want = {n: x for n, x in KNOWN[fam].items() if x < top_x}
    if any(first.get(n) != x for n, x in want.items()):
        return False, (f"G2 FAIL: {fam}: the first occurrences below {top_x} "
                       f"are {first}, published {want}")
    if any(n not in KNOWN[fam] for n in first):
        return False, f"G2 FAIL: {fam}: a run occurs below {top_x} with no published term"
    fam = "A072942"
    want = {n: x for n, x in KNOWN[fam].items() if x < REGEN_DIV}
    pending = dict(want)
    found = {}
    sv = _primes_below(REGEN_DIV + 2)
    for x in range(X_MIN, REGEN_DIV):
        if not sv[x - 1]:
            continue                       # Phi_1(x) = x - 1 is a divisor of every n
        memo = {1: True}

        def prime_at(d):
            if d not in memo:
                memo[d] = bool(isprime(value(d, x)))
            return memo[d]
        for n in list(pending):
            if all(prime_at(d) for d in forms(fam, n)):
                found[n] = x
                del pending[n]
        if not pending:
            break
    if found != want:
        bad = {n: (found.get(n), want[n]) for n in want if found.get(n) != want[n]}
        return False, (f"G2 FAIL: {fam}: first solutions below {REGEN_DIV} differ "
                       f"from the a-file at {bad}")
    return True, (f"G2 ok: A070737's a(1)-a(6) are the first occurrences of "
                  f"runs 1-6 below {top_x:,} (a(3) = a(4) = 6 among them), read "
                  f"from the definition alone; and the {len(want)} indices of "
                  f"A072942 up to 99 whose term is under {REGEN_DIV:,} are each "
                  f"the first solution of their own divisor set")


def _filters(fam):
    if kind(fam) == "ladder":
        top = frontier(fam)
        return sorted({1, 2, 3, 4, 6, 9, top, top + 1, top + 3})
    return sorted({1, 6, 12, 30, 36} | set(TARGETS))


def g2b_killed_set_three_ways():
    """K(q, S) by the residue walk, by the roots of unity (nthroot_mod) and
    by direct divisibility of the values, at every prime under 120 and a
    spread of filters; the proved bound holds; residue 0 is never killed;
    on A070737 K(q, n) is a subset of K(q, n + 1)."""
    checked = 0
    biggest = (0, 0, 0, "")
    for fam in FAMILIES:
        prev = {}
        for n in _filters(fam):
            for q in primerange(2, 120):
                walk = set(forbidden_k_residues(q, n, fam))
                alg = killed_algebraic(q, n, fam)
                if walk != alg or w_count(q, n, fam) != len(walk):
                    return False, (f"G2b FAIL: K({q},{n},{fam}) differs between "
                                   f"the walk {sorted(walk)} and the roots of "
                                   f"unity {sorted(alg)}")
                if 0 in walk:
                    return False, f"G2b FAIL: residue 0 killed mod {q} at {fam} n={n}"
                for r in range(q):
                    x = K_FLOOR * q * 10 ** 6 + r
                    direct = any(v % q == 0 for v in values(fam, x, n))
                    if direct != (r in walk):
                        return False, (f"G2b FAIL: K({q},{n},{fam}) disagrees "
                                       f"with divisibility at x = {x}")
                if len(walk) > w_bound(q, n, fam) or len(walk) > maxkills(fam, n):
                    return False, (f"G2b FAIL: w({q},{n},{fam}) = {len(walk)} "
                                   f"passes the proved bound {w_bound(q, n, fam)}")
                if kind(fam) == "ladder":
                    prior = [m for m in prev if m < n]
                    if prior and not prev[max(prior)].get(q, set()) <= walk:
                        return False, f"G2b FAIL: K({q},{n},{fam}) lost a residue"
                    prev.setdefault(n, {})[q] = walk
                biggest = max(biggest, (len(walk), q, n, fam))
                checked += 1
    return True, (f"G2b ok: K(q, S) three ways -- residue walk, the roots of "
                  f"unity of each attainable order by sympy's nthroot_mod, and "
                  f"direct divisibility of the values -- agree at all {checked} "
                  f"(q < 120, index, family), each inside its proved bound (the "
                  f"sum of phi(k) over the forms), residue 0 never killed, and "
                  f"K(q, n) a subset of K(q, n+1) on A070737; the most a prime "
                  f"under 120 kills is {biggest[0]} residues (q = {biggest[1]}, "
                  f"{biggest[3]} n = {biggest[2]})")


def g2c_admissible_and_forced():
    """Every filter is admissible (w < q at every prime under 400) and the
    forced primes are EXACTLY the formula's: q <= n + 1 on A070737 at every
    n to 30, (q - 1) | n on A072942 at every n to 99 -- so 13 is forced from
    n = 12, 17 from 16; 61 at n = 60, 97 at n = 96; and nothing above
    n + 1 is ever forced."""
    rows = []
    for fam in FAMILIES:
        ns = range(1, 31) if kind(fam) == "ladder" else range(1, INDEX_TOP + 1)
        shown = []
        for n in ns:
            for q in primerange(2, 400):
                if w(q, n, fam) >= q:
                    return False, f"G2c FAIL: {fam} n={n}: q={q} kills every residue"
            got = forced_primes(fam, n, upto=400)
            want = forced_formula(fam, n, upto=400)
            if got != want:
                return False, (f"G2c FAIL: {fam} forces {got} at n = {n}, the "
                               f"formula says {want}")
            if any(forced_residue(q, n, fam) != 0 for q in got):
                return False, f"G2c FAIL: {fam} n={n}: a forced class is not 0"
            if any(q > n + 1 for q in got):
                return False, f"G2c FAIL: {fam} n={n}: a forced prime above n + 1"
            ok, q = admissible(fam, n)
            if not ok:
                return False, f"G2c FAIL: {fam} is not admissible at n = {n} ({q})"
            if n in (11, 13, 16, 48, 60, 72, 96):
                shown.append(f"n = {n}: {got}")
        rows.append(f"{fam} " + "; ".join(shown))
    return True, ("G2c ok: every filter is admissible at every prime under "
                  "400 (the class 0 survives), and the forced primes are "
                  "exactly the formula's -- every q <= n + 1 on A070737 (to "
                  "n = 30), every q with (q - 1) | n on A072942 (to n = 99) -- "
                  "each pinning x to 0 (mod q): " + " | ".join(rows))


GATES = [g1_knowns_reproduce, g1b_finds_reproduce,
         g1c_every_index_is_the_oeis_index, g1d_derived_entry,
         g2b_killed_set_three_ways, g2c_admissible_and_forced,
         g2_rederive_small]


if __name__ == "__main__":
    import pathlib as _pathlib
    import sys as _sys
    _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
    from huntlib import shutdown as _shutdown

    def _main():
        import time as _time
        bad = 0
        for g in GATES:
            t0 = _time.time()
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg + " [%.1fs]" % (_time.time() - t0))
            bad += 0 if ok else 1
        return 1 if bad else 0

    _shutdown.graceful(_main)
