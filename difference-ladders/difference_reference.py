"""The oracle for the difference ladders -- slow, obviously correct, sympy only.

    A216666(n) = the smallest integer b such that (b+1)^p - b^p is prime for
                 all primes p <= prime(n)
    A216668(n) = the smallest integer b > 1 such that for all primes
                 p <= prime(n), (b+1)^p - b^p is prime if and only if 2^p-1
                 is prime
    A229073(n) = the least m >= 2 such that m^p - (m - 1)^p is composite for
                 p = prime(n) but no smaller prime p: A216666's line read
                 with m = b + 1 and the run EXACT (a derived entry every
                 A216666 find whose run is exact settles; below)

THE DIFFERENCE LADDERS: one unknown and a ladder of conditions that differ in
the exponent p of the difference of consecutive p-th powers.  A216666 and
A216668 are Jean-Louis Charton's (Sep-Oct 2012); Tyler Busby added
"a(9) > 10^11" to A216666 in Feb 2023.  A229073 is Eric M. Schmidt's (Sep
2013), "equivalently, least m such that A087896(m) = prime(n)", with "no
other terms <= 10^9".

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW;
sympy's prime, primerange, nthroot_mod) and the definitions as written.

A FORM is a prime p: the value is f_p(b) = (b+1)^p - b^p, of degree p - 1
in b, evaluated in Python ints.  The CONDITIONS of index n are the first n
primes p, read in order, each with what it asks of the value:

    A216666:  f_p(b) prime, for every p <= prime(n)
    A216668:  f_p(b) prime exactly when 2^p - 1 is prime -- prime at the
              Mersenne exponents 2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107,
              127, ... and COMPOSITE at every other p

The RUN of b against a family is the number of leading conditions (in the
order of p) that b meets; a(n) is the least b whose run is at least n.  Both
ladders NEST (every condition of index n is one of index n + 1), so
a(n + 1) >= a(n), the line of a(n) starts AT a(n - 1), and a term whose run
passes its index is the next term too: A216666's a(1) = ... = a(4) = 1
(2^p - 1 is prime for p = 2, 3, 5, 7 and 2^11 - 1 = 23 * 89),
A216668's a(8) = a(9) = a(10).

The SIEVED forms of index n are the conditions that ask for a PRIME: every
p <= prime(n) on A216666, the Mersenne exponents among them on A216668.  A
condition that asks for a composite cannot be sieved (a value divisible by
a small prime is what it wants), so A216668's are read on the host for the
rare survivor (launch.py).

Facts PROVED here rather than assumed, because both engines and the odds
model are built on them.

  THE KILLED SET.  For a prime q and the form p:

      q | f_p(b)   <=>   (b + 1)^p == b^p (mod q)
                   <=>   b != 0 and ((b + 1)/b)^p == 1, (b + 1)/b != 1
                   <=>   (b + 1)/b = zeta, a primitive p-th root of unity
                   <=>   b == 1/(zeta - 1) (mod q)

  (b == 0 gives f = 1; (b + 1)/b is never 1.)  A primitive p-th root of
  unity exists mod q exactly when p | q - 1, and then there are p - 1 of
  them, so q kills p - 1 residues for each sieved p dividing q - 1 and none
  for any other p -- q = p never kills (f_p(b) == 1 (mod p) by Fermat) and
  q = 2 never kills (one of b, b + 1 is even, the other odd, so f_p(b) is
  odd).  The kills of different p are disjoint (different orders) and the
  map zeta -> 1/(zeta - 1) is injective.  It is cyclotomic-ladders' kill
  set (the elements of order p) under the substitution b = 1/(x - 1).
  Built three ways below -- the residue walk (every residue, every value
  mod q), the roots of unity by sympy's nthroot_mod, and direct
  divisibility of the values -- and the CPU engine builds it a fourth way
  (powers of a primitive root), G3.

  ITS SIZE, BOUNDED.  |K(q, n)| = sum of (p - 1) over the sieved p dividing
  q - 1 <= the sum of (p - 1) over the sieved forms (maxkills): 91 at
  A216666's n = 9, 149 at n = 11; 149 at A216668's n = 18, 237 at n = 24.
  On average over q it is one residue per form (p | q - 1 for one prime q
  in p - 1): the wheel is WEAK.

  NOTHING IS FORCED, AND EVERY INDEX IS ADMISSIBLE.  The residues 0 and
  q - 1 are never killed (b == 0 gives 1, b == -1 gives (-1)^(p+1)... more
  simply zeta = 0 is not a root of unity), so every prime leaves at least
  two classes free: no prime pins b to one class (no unit, no class
  space), and no prime covers every residue (Schinzel's hypothesis H then
  makes every index conjecturally attained -- A216666's own comment asks
  whether it is infinite).  G2c checks both at every prime under 400.

  THE EXCEPTION ZONE.  "q divides the value, so the value is composite"
  needs the value to EXCEED q.  The smallest value is f_2(b) = 2b + 1, so a
  sieve to q2 is a proof from b > q2 on (k_floor, cautiously); the integers
  below are classified one at a time (prefix_hits).  Every campaign here
  opens far above it; G2 and the drills cover it.

Gates in this file: G1 (every published term satisfies its definition; both
ladders monotone; every term's run is exactly its index or the plateau the
entry shows; the composite stopper past each frontier), G1b (this project's
own finds -- the FREE TERMS -- re-checked from the bare definition, with
their least-claims), G1c (every index is the OEIS index: KNOWN rebuilt from
the %S/%T and %O lines verbatim), G1d (A229073 is A216666's exact-run line:
a(1)..a(6) re-derived by walking m from 2, a(7) from A216666(6)'s exact
run, and the identity a(n+1) = A216666(n) + 1 wherever the run is exact),
G2 (the small terms re-derived exhaustively from the bare definition), G2b
(the killed set three ways, its proved bound, the nesting, 0 and q - 1
never killed), G2c (admissible at every prime under 400, nothing forced),
G2d (the Mersenne exponents the engines freeze are sympy's).
"""

from functools import lru_cache as _lru_cache

from sympy import isprime, nthroot_mod, prime, primerange

# ---------------------------------------------------------------- families

# `kind`        "ladder" on both: the first n conditions, nesting, one line
#               per family from the frontier term.
# `pattern`     "all" (A216666: every condition asks for a prime) or
#               "mersenne" (A216668: prime iff 2^p - 1 is prime).
# `term`        the letter the OEIS NAME gives the term (b on both), under
#               which the evidence files carry it (CONVENTIONS.md "Naming in
#               an evidence file"); `index` the name's index letter (n);
#               `poly` the letter the name gives the exponent (p).
# `forms`       the condition in the name's own letters, for the evidence.
# `b_min`       the least b the definition admits: 1 on A216666 (b = 0
#               gives 1), 2 on A216668 ("b > 1").
# `name`, `data`, `offset_line`, `revision`, `keywords`, `comment`: the
#               %N, %S/%T, %O, %I, %K and %C lines VERBATIM from the OEIS
#               export of 2026-11-23 (re-read on oeis.org the same day),
#               which G1c rebuilds every index from.
# `also`        derived entries a find settles for free.
FAMILIES = {
    "A216666": {"kind": "ladder", "pattern": "all", "term": "b", "index": "n",
                "poly": "p",
                "forms": "(b+1)^p - b^p prime for all primes p <= prime(n)",
                "name": "Smallest integer b such that (b+1)^p - b^p is prime "
                        "for all primes p <= prime(n).",
                "data": "1,1,1,1,6524,809652228,30717523794,55779743835",
                "offset_line": "1,5",
                "revision": "#28 Feb 20 2023 03:17:48",
                "keywords": "nonn,hard,more",
                "author": "Jean-Louis Charton, Sep 13 2012",
                "comment": "a(9) > 10^11. - Tyler Busby, Feb 20 2023",
                "frontier_by": "Jean-Louis Charton, Oct 2012 (a(9) > 10^11: "
                               "Tyler Busby, Feb 2023)",
                "b_min": 1,
                "also": ("A229073",)},
    "A216668": {"kind": "ladder", "pattern": "mersenne", "term": "b",
                "index": "n", "poly": "p",
                "forms": "(b+1)^p - b^p prime iff 2^p-1 prime, for all "
                         "primes p <= prime(n)",
                "name": "Smallest integer b > 1 such that for all primes "
                        "p <= prime(n), (b+1)^p - b^p is prime if and only "
                        "if 2^p-1 is prime.",
                "data": "2,2,2,296,296,369719,457578,43410300320,43410300320,"
                        "43410300320,288975248496",
                "offset_line": "1,1",
                "revision": "#17 Feb 02 2023 04:19:31",
                "keywords": "nonn,hard,more",
                "author": "Jean-Louis Charton, Sep 13 2012",
                "comment": None,
                "frontier_by": "Jean-Louis Charton, Oct 2012",
                "b_min": 2,
                "also": ()},
}

# THE DERIVED ENTRY: A229073 (Eric M. Schmidt, Sep 12 2013; hard).  Its
# name's letter is m, and m = b + 1 for A216666's b: the record of a
# derived term carries the integer under m (CLAUDE.md 5i -- the siblings
# disagree, so it is never written in b).  Verbatim lines of the export.
DERIVED = {
    "A229073": {"of": "A216666", "term": "m", "shift": 1,
                "forms": "m^p - (m - 1)^p composite for p = prime(n) but no "
                         "smaller prime p",
                "name": "Least m >= 2 such that m^p - (m - 1)^p is composite "
                        "for p = prime(n) but no smaller prime p.",
                "data": "5,6,4,3,2,6525,809652229",
                "offset_line": "1,1",
                "revision": "#8 Sep 12 2013 21:48:59",
                "keywords": "nonn,hard",
                "author": "Eric M. Schmidt, Sep 12 2013",
                "comment": "There are no other terms <= 10^9.",
                "m_min": 2},
}

# `--family A229073` names the line it rides (launch.py says so in a log
# line): one campaign covers both entries.
ALIASES = {"A229073": "A216666"}

# The Mersenne exponents the engines freeze, to the last index any reader
# here reaches (READ_TOP's prime, 173); G2d rebuilds them from sympy.
MERSENNE_EXPONENTS = (2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127)
READ_TOP = 40                     # prime(40) = 173: the furthest any run is read

# A PUBLISHED TERM WHOSE RUN PASSES ITS INDEX (the plateaus the entries show,
# and the one the free terms rest on: A216668's a(11) runs to 17, which IS
# a(12)..a(17) -- G1 proves it from the definition, G1b records it).
RUNS_PAST = {"A216666": {1: 4, 2: 4, 3: 4},
             "A216668": {1: 3, 2: 3, 4: 5, 8: 10, 9: 10, 11: 17}}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against;
# these are the project's own claims.  G1b re-checks every one from the
# bare definition.  THE FREE TERMS (2026-11-23, before any campaign): the
# run at A216668's a(11) = 288,975,248,496 is exactly 17 -- (b+1)^p - b^p
# composite at p = 37, 41, 43, 47, 53, 59 as 2^p - 1 is, and composite at
# p = 61 where 2^61 - 1 is prime -- so a(12)..a(17) are a(11); and the runs
# at A216666's a(7) and a(8) are exactly 7 and 8, so A229073's a(8) and
# a(9) are those terms plus one.
FOUND = {"A216666": {},
         "A216668": {n: 288975248496 for n in range(12, 18)},
         "A229073": {8: 30717523795, 9: 55779743836}}

# The exception zone is covered by brute force; G2b's divisibility checks
# run their values at heights well above any sieve depth.
K_FLOOR = 10 ** 4

# The least b of either entry (A216666: b = 0 gives 1, never prime).
X_MIN = 1


def family(fam):
    """The canonical family key, aliases resolved; raises on an unknown one."""
    fam = str(fam).upper()
    fam = ALIASES.get(fam, fam)
    if fam not in FAMILIES:
        raise KeyError(f"no family {fam!r}; the families are "
                       f"{', '.join(sorted(FAMILIES))} (A229073 rides "
                       f"A216666's line)")
    return fam


def kind(fam):
    return FAMILIES[family(fam)]["kind"]


def per_index(fam):
    """Both families are nesting ladders: no index is its own line."""
    family(fam)
    return False


def letter(fam):
    """The letter the OEIS name gives the term: b on both families, m on
    the derived A229073."""
    if str(fam).upper() in DERIVED:
        return DERIVED[str(fam).upper()]["term"]
    return FAMILIES[family(fam)]["term"]


def b_min(fam):
    return int(FAMILIES[family(fam)]["b_min"])


def offset(fam):
    if str(fam).upper() in DERIVED:
        return int(DERIVED[str(fam).upper()]["offset_line"].split(",")[0])
    return int(FAMILIES[family(fam)]["offset_line"].split(",")[0])


def _published(f):
    off = int(f["offset_line"].split(",")[0])
    return {off + i: int(v) for i, v in enumerate(f["data"].split(","))}


# The published terms, keyed by the OEIS INDEX (%O).
KNOWN = {fam: _published(f) for fam, f in FAMILIES.items()}
KNOWN_DERIVED = {seq: _published(d) for seq, d in DERIVED.items()}


def term(fam, n, missing=KeyError):
    """a(n) from the literature or this project's finds (A229073 too)."""
    n = int(n)
    if str(fam).upper() in DERIVED:
        seq = str(fam).upper()
        tables = (KNOWN_DERIVED[seq], FOUND[seq])
    else:
        fam = family(fam)
        tables = (KNOWN[fam], FOUND[fam])
    for table in tables:
        if n in table:
            return int(table[n])
    if missing is None:
        return None
    raise KeyError(f"{fam} a({n}) is not known")


def frontier(fam):
    """The largest n with a(1..n) all known (the literature and the finds)."""
    n = offset(fam) - 1
    while term(fam, n + 1, missing=None) is not None:
        n += 1
    return n


# ------------------------------------------------------------- the forms

@_lru_cache(maxsize=None)
def nth_prime(n):
    """prime(n), sympy's."""
    return int(prime(int(n)))


@_lru_cache(maxsize=None)
def mersenne(p):
    """2^p - 1 is prime (sympy)."""
    return bool(isprime(2 ** int(p) - 1))


def conditions(fam, n):
    """[(p, wants_prime)] for the first n primes p, in run order."""
    fam, n = family(fam), int(n)
    if n < 1:
        raise ValueError(f"index {n} of {fam} imposes no condition")
    out = []
    for i in range(1, n + 1):
        p = nth_prime(i)
        want = True if FAMILIES[fam]["pattern"] == "all" else mersenne(p)
        out.append((p, want))
    return tuple(out)


def forms(fam, n):
    """The SIEVED forms of index n -- the primes p whose condition asks for
    a prime value -- in run order: every p <= prime(n) on A216666, the
    Mersenne exponents among them on A216668."""
    return tuple(p for p, want in conditions(fam, n) if want)


def nforms(fam, n):
    return len(forms(fam, n))


def degree(p):
    """deg f_p = p - 1."""
    return int(p) - 1


def total_degree(fam, n):
    return sum(degree(p) for p in forms(fam, n))


def maxkills(fam, n):
    """The PROVED bound on how many residues one prime can kill at index n:
    the sum of (p - 1) over the sieved forms (module docstring)."""
    return sum(degree(p) for p in forms(fam, n))


def value(p, b):
    """f_p(b) = (b + 1)^p - b^p, in Python ints."""
    p, b = int(p), int(b)
    return (b + 1) ** p - b ** p


def values(fam, b, n):
    """Every SIEVED value of index n at b, in form order."""
    return [value(p, b) for p in forms(fam, n)]


def run_length(fam, b, n):
    """The run of b against index n: the number of LEADING conditions of
    index n (in the order of p) that b meets -- n itself when b satisfies
    the index.  Read with a larger n to see past an index."""
    fam, b = family(fam), int(b)
    if b < b_min(fam):
        return 0
    r = 0
    for p, want in conditions(fam, n):
        if bool(isprime(value(p, b))) != want:
            break
        r += 1
    return r


def is_term(fam, b, n):
    """b satisfies index n.  NOT the least-claim: that is a sweep's."""
    return run_length(fam, b, n) >= int(n)


def floor_x(fam, n):
    """The definition's own floor for a(n), INCLUSIVE: a(n - 1) itself when
    it is known (the ladder nests, and a(n - 1) IS a(n) when its run
    reaches n), else the family's least b."""
    fam, n = family(fam), int(n)
    if n <= offset(fam):
        return b_min(fam)
    prev = term(fam, n - 1, missing=None)
    return b_min(fam) if prev is None else max(b_min(fam), prev)


# ----------------------------------------------------- the derived entry

def exact_run(b, n):
    """A229073's condition at m = b + 1 for index n: f_p(b) prime for the
    first n - 1 primes and composite at prime(n) -- the A216666 run of b
    read to n is EXACTLY n - 1."""
    return run_length("A216666", b, n) == int(n) - 1


def first_m(n, lo=2, hi=None):
    """The least m >= lo with A229073's condition at index n, by the bare
    definition; None below hi."""
    m = max(int(lo), DERIVED["A229073"]["m_min"])
    while hi is None or m < hi:
        if exact_run(m - 1, n):
            return m
        m += 1
    return None


# --------------------------------------------------------- the killed set

def forbidden_k_residues(q, n, fam):
    """The residues of b mod q at which some SIEVED value of index n is
    divisible by q -- by walking every residue and reducing the value."""
    q = int(q)
    ps = forms(fam, n)
    return [r for r in range(q)
            if any((pow(r + 1, p, q) - pow(r, p, q)) % q == 0 for p in ps)]


def w(q, n, fam):
    """|K(q, n)|, from the walk."""
    return len(forbidden_k_residues(q, n, fam))


def killed_algebraic(q, n, fam):
    """K(q, n) the algebraic way: for each sieved p dividing q - 1, the
    primitive p-th roots of unity zeta (sympy's nthroot_mod, less 1), and
    b = 1/(zeta - 1) mod q."""
    q = int(q)
    out = set()
    for p in forms(fam, n):
        if (q - 1) % p:
            continue
        roots = set(int(r) % q for r in (nthroot_mod(1, p, q, all_roots=True) or []))
        roots.discard(1)
        for z in roots:
            out.add(pow(z - 1, -1, q))
    return out


def w_count(q, n, fam):
    """|K(q, n)| the algebraic way.  G2b proves it equal to the walk."""
    return len(killed_algebraic(q, n, fam))


def w_formula(q, n, fam):
    """|K(q, n)| by the theorem: the sum of (p - 1) over the sieved p
    dividing q - 1."""
    return sum(p - 1 for p in forms(fam, n) if (int(q) - 1) % p == 0)


def w_bound(q, n, fam):
    """The PROVED upper bound on w(q, n) (module docstring)."""
    return min(int(q) - 2, maxkills(fam, n)) if int(q) > 2 else 0


def forced_formula(fam, n, upto=128):
    """The forced primes BY THE THEOREM of the module docstring: none."""
    family(fam)
    int(n)
    return []


def forced_primes(fam, n, upto=128):
    """The primes that leave exactly one residue class at index n, by the
    walk."""
    return [q for q in primerange(2, upto) if w(q, n, fam) == q - 1]


def admissible(fam, n):
    """(ok, q): ok unless some prime q has every residue killed at index n.
    A theorem here (0 and -1 survive every prime), checked anyway on every
    prime up to the kill bound, the only ones that could be covered."""
    for q in primerange(2, maxkills(fam, n) + 3):
        if w(q, n, fam) >= q:
            return False, q
    return True, None


def wheel_residues(fam, n, p1):
    """The b mod W(p1) that survive every prime q <= p1, by brute force."""
    qs = list(primerange(2, p1 + 1))
    W = 1
    for q in qs:
        W *= q
    killed = {q: set(forbidden_k_residues(q, n, fam)) for q in qs}
    return W, [r for r in range(W) if all(r % q not in killed[q] for q in qs)]


def first_x(fam, n, lo=None, hi=None):
    """The least b >= lo (default the definition's floor) that satisfies
    index n, by the bare definition, one integer at a time; None if there
    is none below hi.  The slowest thing in this project."""
    fam, n = family(fam), int(n)
    b = floor_x(fam, n) if lo is None else max(int(lo), b_min(fam))
    while hi is None or b < hi:
        if is_term(fam, b, n):
            return b
        b += 1
    return None


def prefix_hits(fam, n, lo, hi, floor=1, read_n=None):
    """[(b, run)] for every b in [lo, hi] with a run of at least `floor`
    against index n (read against `read_n` >= n, to see past the index),
    by the bare definition -- how the exception zone is covered."""
    fam = family(fam)
    read_n = int(n) if read_n is None else max(int(read_n), int(n))
    out = []
    for b in range(max(int(lo), b_min(fam)), int(hi) + 1):
        r = run_length(fam, b, read_n)
        if r >= floor:
            out.append((b, r))
    return out


# --------------------------------- gates -----------------------------------

# How far G2 walks each line by brute force: A216666's a(1)..a(5) lie below
# 7,000; A216668's a(1)..a(7) below 460,000.  The walk reads every b's run
# from the definition (a sieve of 2b + 1 first, the cheapest condition).
REGEN_X = {"A216666": 7_000, "A216668": 460_000}
REGEN_M = 6_600                   # A229073's a(1)..a(6) lie below it


def g1_knowns_reproduce():
    """Every published term satisfies its definition; both ladders are
    monotone; each term's run is exactly its index or the plateau the
    entry shows (RUNS_PAST); and the condition past each frontier fails."""
    parts = []
    for fam in FAMILIES:
        known = KNOWN[fam]
        prev = 0
        for n in sorted(known):
            b = known[n]
            r = run_length(fam, b, n + 8)
            want = RUNS_PAST.get(fam, {}).get(n, n)
            if r != want:
                return False, (f"G1 FAIL: {fam} a({n}) = {b} has run {r}, "
                               f"expected exactly {want}")
            if b < prev or b < floor_x(fam, n):
                return False, f"G1 FAIL: {fam} a({n}) = {b} < a({n - 1}) = {prev}"
            prev = b
        top = max(known)
        parts.append(f"{fam} a(1)-a({top}) (plateaus "
                     + ", ".join(f"a({n}) runs to {r}"
                                 for n, r in sorted(RUNS_PAST[fam].items()))
                     + ")")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every published term "
                  "satisfies its definition, both ladders are monotone, and "
                  "each term's run is exactly its index or the plateau the "
                  "entry shows")


def g1b_finds_reproduce():
    """This project's finds -- the FREE terms of 2026-11-23 -- re-checked
    from the bare definition, with their least-claims: on A216668 a(n) = b
    satisfies index n and b = a(n - 1) (a(n) >= a(n - 1) by nesting); on
    A229073 m - 1 = A216666(n - 1) has run exactly n - 1 (every m with that
    run has m - 1 >= A216666(n - 1))."""
    parts = []
    for fam in FAMILIES:
        for n in sorted(FOUND[fam]):
            b = FOUND[fam][n]
            prev = term(fam, n - 1)
            if not is_term(fam, b, n) or b < prev:
                return False, (f"G1b FAIL: {fam} a({n}) = {b} does not "
                               f"satisfy index {n} at or above a({n - 1})")
            if b != prev and fam != "A216666":
                return False, (f"G1b FAIL: {fam} a({n}) = {b} is not a({n - 1}) "
                               f"= {prev}, so nesting alone does not make it least")
        if FOUND[fam]:
            parts.append(f"{fam} " + ", ".join(f"a({n})" for n in sorted(FOUND[fam])))
    seq = "A229073"
    for n in sorted(FOUND[seq]):
        m = FOUND[seq][n]
        b = m - 1
        if b != term("A216666", n - 1) or not exact_run(b, n):
            return False, (f"G1b FAIL: {seq} a({n}) = {m}: m - 1 is not "
                           f"A216666(a({n - 1})) with run exactly {n - 1}")
    parts.append(f"{seq} " + ", ".join(f"a({n}) = {m}" for n, m in sorted(FOUND[seq].items())))
    if run_length("A216668", FOUND["A216668"][17], 30) != 17:
        return False, "G1b FAIL: A216668's free run is not exactly 17"
    return True, ("G1b ok: this project's finds " + "; ".join(parts) +
                  " -- each satisfies its index from the bare definition and "
                  "is least by nesting (A216668's run at a(11) is exactly 17: "
                  "composite at p = 37..59 as 2^p - 1 is, composite at p = 61 "
                  "where 2^61 - 1 is prime; A216666's runs at a(7), a(8) are "
                  "exactly 7 and 8)")


def g1c_every_index_is_the_oeis_index():
    """KNOWN is the %S/%T list keyed by the %O offset and nothing else, on
    both families and the derived entry; the frontiers and the open
    indices follow."""
    rows = []
    for fam, f in list(FAMILIES.items()) + list(DERIVED.items()):
        off = int(f["offset_line"].split(",")[0])
        data = [int(v) for v in f["data"].split(",")]
        want = {off + i: v for i, v in enumerate(data)}
        table = KNOWN.get(fam, KNOWN_DERIVED.get(fam))
        if off != 1 or offset(fam) != 1 or table != want:
            return False, f"G1c FAIL: {fam}'s KNOWN is not its %S list keyed by %O"
        if [term(fam, i) for i in range(1, len(data) + 1)] != data:
            return False, f"G1c FAIL: {fam}'s terms do not read back as %S"
        top = frontier(fam)
        rows.append(f"{fam} %O {f['offset_line']}: a(1)..a({len(data)}) published, "
                    f"frontier a({top}) with this project's finds, open a({top + 1})")
    if (frontier("A216666"), frontier("A216668"), frontier("A229073")) != (8, 17, 9):
        return False, "G1c FAIL: the frontiers are not a(8), a(17) and a(9)"
    if nforms("A216666", 9) != 9 or forms("A216668", 18) != (2, 3, 5, 7, 13, 17, 19, 31, 61):
        return False, "G1c FAIL: the open indices have the wrong sieved forms"
    return True, "G1c ok: " + "; ".join(rows)


def g1d_derived_entry():
    """A229073 is A216666's line read with m = b + 1 and the run EXACT:
    a(1)..a(6) re-derived by walking m from 2 (the definition: f_p(m - 1)
    prime below prime(n) and composite at it); a(7) = A216666(6) + 1
    because A216666(6)'s run is exactly 6 and every b with that run is at
    least A216666(6); and wherever A216666(n)'s run is exactly n,
    A229073(n + 1) = A216666(n) + 1 -- a(6) from A216666(5) too."""
    d = KNOWN_DERIVED["A229073"]
    for n in range(1, 7):
        m = first_m(n, hi=REGEN_M)
        if m != d[n]:
            return False, (f"G1d FAIL: the least m with A229073's condition at "
                           f"n = {n} is {m}, the entry says {d[n]}")
    a = KNOWN["A216666"]
    if not exact_run(a[6], 7) or d[7] != a[6] + 1:
        return False, "G1d FAIL: A229073 a(7) is not A216666(6) + 1 with an exact run"
    if not exact_run(a[5], 6) or d[6] != a[5] + 1:
        return False, "G1d FAIL: A229073 a(6) is not A216666(5) + 1"
    # A216666(1..4) = 1 runs to 4 exactly: m = 2 is A229073's a(5)
    if not exact_run(1, 5) or d[5] != 2:
        return False, "G1d FAIL: m = 2 does not run exactly to 4"
    return True, ("G1d ok: A229073's a(1)..a(6) = 5, 6, 4, 3, 2, 6525 are "
                  "the least m from 2 whose run is exactly n - 1 (walked to "
                  f"{REGEN_M:,}), a(7) = A216666(6) + 1 and a(6) = A216666(5) "
                  "+ 1 where A216666's run is exact, a(5) = 2 from b = 1's "
                  "run of exactly 4: so an A216666 find of run r settles "
                  "A229073 a(r + 1) = b + 1")


def _odd_composite_sieve(m):
    """bytearray s with s[v] = 1 for v prime, v < m (nothing clever)."""
    s = bytearray([1]) * m
    s[0:2] = b"\x00\x00"
    for p in range(2, int(m ** 0.5) + 1):
        if s[p]:
            s[p * p::p] = bytearray(len(range(p * p, m, p)))
    return s


def g2_rederive_small():
    """Walk b from the family's least and read its run from the bare
    definition: the first b with a run of at least n must be the published
    a(n) for every n the walk reaches (the plateaus included)."""
    rows = []
    for fam, top_b in REGEN_X.items():
        sv = _odd_composite_sieve(2 * top_b + 3)
        first, top = {}, 0
        for b in range(b_min(fam), top_b):
            if not sv[2 * b + 1]:             # f_2(b) = 2b + 1 must be prime
                continue
            r = run_length(fam, b, 12)
            while top < r:
                top += 1
                first[top] = int(b)
        want = {n: b for n, b in KNOWN[fam].items() if b < top_b}
        if any(first.get(n) != b for n, b in want.items()):
            return False, (f"G2 FAIL: {fam}: the first occurrences below "
                           f"{top_b} are {first}, published {want}")
        if any(n not in KNOWN[fam] for n in first):
            return False, f"G2 FAIL: {fam}: a run occurs below {top_b} with no published term"
        rows.append(f"{fam} a(1)-a({max(want)}) below {top_b:,}")
    return True, ("G2 ok: " + "; ".join(rows) + " are the first occurrences "
                  "of their runs, read from the definition alone (the "
                  "plateaus a(1) = ... = a(4) = 1 and a(4) = a(5) = 296 among "
                  "them)")


def _filters(fam):
    top = frontier(fam)
    return sorted({1, 2, 3, 4, 6, 9, 11, top, top + 1, min(top + 7, 27)})


def g2b_killed_set_three_ways():
    """K(q, n) by the residue walk, by the roots of unity (nthroot_mod) and
    by direct divisibility of the values, at every prime under 200 and a
    spread of filters; its size is the formula's; the proved bound holds;
    0 and q - 1 are never killed; K(q, n) is a subset of K(q, n + 1)."""
    checked = 0
    biggest = (0, 0, 0, "")
    for fam in FAMILIES:
        prev = {}
        for n in _filters(fam):
            for q in primerange(2, 200):
                walk = set(forbidden_k_residues(q, n, fam))
                alg = killed_algebraic(q, n, fam)
                if walk != alg or w_count(q, n, fam) != len(walk) \
                        or w_formula(q, n, fam) != len(walk):
                    return False, (f"G2b FAIL: K({q},{n},{fam}) differs between "
                                   f"the walk {sorted(walk)} and the roots of "
                                   f"unity {sorted(alg)}")
                if 0 in walk or (q - 1) in walk and q > 2:
                    return False, f"G2b FAIL: 0 or -1 killed mod {q} at {fam} n={n}"
                for r in (range(q) if q < 50 else ()):
                    b = K_FLOOR * q * 10 ** 6 + r
                    direct = any(v % q == 0 for v in values(fam, b, n))
                    if direct != (r in walk):
                        return False, (f"G2b FAIL: K({q},{n},{fam}) disagrees "
                                       f"with divisibility at b = {b}")
                if len(walk) > w_bound(q, n, fam):
                    return False, (f"G2b FAIL: w({q},{n},{fam}) = {len(walk)} "
                                   f"passes the proved bound {w_bound(q, n, fam)}")
                prior = [m for m in prev if m < n]
                if prior and not prev[max(prior)].get(q, set()) <= walk:
                    return False, f"G2b FAIL: K({q},{n},{fam}) lost a residue"
                prev.setdefault(n, {})[q] = walk
                biggest = max(biggest, (len(walk), q, n, fam))
                checked += 1
    return True, (f"G2b ok: K(q, n) three ways -- residue walk, b = 1/(zeta - 1) "
                  f"over the primitive p-th roots of unity by sympy's "
                  f"nthroot_mod, and direct divisibility of the values -- "
                  f"agree at all {checked} (q < 200, index, family), each the "
                  f"sum of (p - 1) over the sieved p dividing q - 1 and inside "
                  f"its proved bound, 0 and q - 1 never killed, K(q, n) a "
                  f"subset of K(q, n + 1); the most a prime under 200 kills "
                  f"is {biggest[0]} residues (q = {biggest[1]}, {biggest[3]} "
                  f"n = {biggest[2]})")


def g2c_admissible_and_nothing_forced():
    """Every filter is admissible and NOTHING is forced: at every prime
    under 400 and every index to 27, at least two residues (0 and q - 1)
    survive -- so the engines sweep the whole line, no class, no unit."""
    rows = []
    for fam in FAMILIES:
        # the kill sets nest, so the largest index decides "covered" and
        # "forced" for every index under it; a spread is walked anyway
        ns = (1, 5, 9, 11, 13, 18, 24, 27)
        for n in ns:
            forced = []
            for q in primerange(2, 400):
                k = w(q, n, fam)
                if k > q - 2:
                    return False, (f"G2c FAIL: {fam} n={n}: q={q} leaves "
                                   f"{q - k} classes")
                if k == q - 1:
                    forced.append(q)
            if forced != forced_formula(fam, n):
                return False, f"G2c FAIL: {fam} forces {forced} at n = {n}"
            ok, q = admissible(fam, n)
            if not ok:
                return False, f"G2c FAIL: {fam} is not admissible at n = {n} ({q})"
        rows.append(f"{fam} n = {', '.join(map(str, ns))}")
    return True, ("G2c ok: every filter is admissible and nothing is forced "
                  "(" + "; ".join(rows) + ": every prime under 400 leaves at "
                  "least 0 and q - 1 free; the kill sets nest, so the indices "
                  "between are covered by the larger)")


def g2d_mersenne_exponents():
    """The Mersenne exponents frozen for the engines are exactly the primes
    p <= prime(READ_TOP) with 2^p - 1 prime, by sympy."""
    top = nth_prime(READ_TOP)
    got = tuple(p for p in primerange(2, top + 1) if mersenne(p))
    if got != tuple(p for p in MERSENNE_EXPONENTS if p <= top):
        return False, f"G2d FAIL: sympy's Mersenne exponents to {top} are {got}"
    if forms("A216668", READ_TOP) != got:
        return False, "G2d FAIL: A216668's sieved forms are not the Mersenne exponents"
    return True, (f"G2d ok: the Mersenne exponents to prime({READ_TOP}) = {top} "
                  f"are {got} by sympy, and they are A216668's sieved forms")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce,
         g1c_every_index_is_the_oeis_index, g1d_derived_entry,
         g2b_killed_set_three_ways, g2c_admissible_and_nothing_forced,
         g2d_mersenne_exponents, g2_rederive_small]


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
