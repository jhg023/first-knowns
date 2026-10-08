"""The oracle for the exact-run primorial shift ladders -- slow, obviously
correct, sympy only.

    A257466(n) = smallest prime p with p + pps(1), ..., p + pps(n) all prime
                 but p + pps(n+1) not, pps the partial sums of the primorials
    A257467(n) = the same with psq, the squares of the primorials
    A258035(n) = the same with pssq, the partial sums of those squares

Three SHIFT LADDERS of Fred Schneider's (April-May 2015), each `hard`, none
touched since 2015: one unknown prime p and conditions that differ only by
an ADDITIVE constant built from the primorials,

    pps(k)  = 2# + 3# + ... + prime(k)#          2, 8, 38, 248, 2558, ...
    psq(k)  = (prime(k)#)^2                      4, 36, 900, 44100, ...
    pssq(k) = psq(1) + ... + psq(k)              4, 40, 940, 45040, ...

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

A FORM is a triple (a, b, e) meaning a*x^e + b, kept so that the engines
read their forms the way every project here does; every form of these
families is (1, c, 1): x + c.  The conditions a sieve can express at index
n are the n + 1 that must be PRIME,

    x,  x + c(1),  x + c(2),  ...,  x + c(n)

and the one that must NOT be, x + c(n+1), is no sieve's business: it is
read by the classification, which reads every survivor's run to its end.

THE RUN IS EXACT, SO THE SEQUENCES ARE NOT MONOTONE.  The run of a prime p
is the number of leading shifts c(1), c(2), ... whose value p + c(k) is
prime, and a(n) is the first prime whose run is EXACTLY n: a prime with a
longer run is a term of a later index and says nothing about this one
(A257466's a(9) = 191 and a(10) = 59 sit far below its a(8) = 191459).
Every index's line therefore starts at the bottom, p = 2, and what a sweep
at filter n establishes -- every prime below the cursor whose run is at
least n, each with its exact run -- settles the first occurrence of EVERY
exact run from n up at once.  A campaign sweeps one line from the bottom
with the filter at the lowest open index.

AN ERRATUM IN THE PUBLISHED DATA OF A258035, which G1 states and checks:
the entry lists a(11) = 1368737917 and a(12) = 4428230508349, and by the
entry's own definition the run of 1368737917 is exactly 12 and the run of
4428230508349 exactly 13.  PUBLISHED keeps the %S line verbatim (G1c);
KNOWN, which everything else reads, stops at a(10), so that entry's
campaign opens at index 11 and settles 11, 12 and 13 from the bottom of the
line like any other term.

Facts PROVED here rather than assumed, because both engines and the odds
model are built on them.

  THE KILLED SET.  For a prime q and a form x + c,  q | x + c  <=>  x == -c
  (mod q).  So

      K(q,n,F) = { -c mod q : c a constant of index n }

  and the engines sieve x against K(q,n,F) and nothing else.  w(q,n,F) is
  its size.  K(q,n) is a subset of K(q,n+1).

  ITS SIZE, BOUNDED.  prime(k)# == 0 (mod q) as soon as prime(k) >= q, so
  from k = pi(q) on psq(k) is 0 -- the residue x itself kills -- and pps(k)
  and pssq(k) stop moving.  Either way at most pi(q) - 1 shifts are
  distinct and nonzero modulo q:

      w(q,n,F) <= 1 + min(n, pi(q) - 1)

  -- the small primes are nearly blind (47 kills at most 15 residues of
  47), which is lcm-ladders' regime and the reason the wheel is weak.

  ADMISSIBLE AT EVERY n.  The bound is below q (pi(q) <= q - 1 for q >= 3,
  and w(2) = 1: every shift is even), so no prime kills every residue,
  Dickson's conjecture applies and every index of every entry is
  conjecturally attained.

  THE FORCED CLASSES.  Every shift is even, so x is ODD.  Modulo 3 the
  forms x and x + c(1) kill 0 and -c(1): c(1) = 2 on A257466 leaves
  x == 2 (mod 3), c(1) = 4 on the other two leaves x == 1 (mod 3), and
  every later shift is c(1) (mod 3).  So the class is 5 (mod 6) on A257466
  and 1 (mod 6) on A257467 and A258035, from n = 1 on.  No prime past 3 is
  ever forced: w <= pi(q) < q - 1 for q >= 5.  G2c checks all of it.

  THE EXCEPTION ZONE.  "q divides the value, so the value is composite"
  needs the value to EXCEED q.  The smallest value is x itself, so a sieve
  to q2 is valid from x > q2; the engines refuse to run below that
  (k_floor), and the primes from 2 to q2 are classified one at a time by
  brute force (prefix_hits).  It is not vacuous: a(3) = 5 and a(4) = 3 of
  A257466 are primes that a sieve would have "killed" by themselves.

Gates in this file: G1 (every known term is prime with a run of EXACTLY its
index and lies in its forced class; the erratum above), G1b (this
project's own finds), G1c (every index is the OEIS index: PUBLISHED rebuilt
from the %S and %O lines verbatim), G2 (the small terms re-derived
exhaustively from the bare definition, as first occurrences of each exact
run), G2b (the killed set three ways and its proved bound), G2c
(admissibility and the forced classes).
"""

from functools import lru_cache as _lru_cache

from sympy import isprime, primerange, primorial

# ---------------------------------------------------------------- families

# `kind`       "primorial": the shifts are built from the primorials and the
#              term itself is a form (p is prime).  One kind here.
# `shift`      which shift: "pps", "psq" or "pssq" (shift_k).
# `term`       the letter the OEIS NAME gives the term (p), under which the
#              evidence files carry it (CONVENTIONS.md "Naming in an evidence
#              file"); `index` the name's index letter (n: the names write
#              the shifts as pps(1), ..., pps(n) and give them no letter).
# `forms`      the condition in the name's own letters, for the evidence.
# `name`, `data`, `offset_line`, `revision`: the %N, %S (+%T), %O and %I
#              lines VERBATIM from the OEIS export of 2026-10-05, which G1c
#              rebuilds every index from.
# `also`       entries settled for free: none.
FAMILIES = {
    "A257466": {"kind": "primorial", "shift": "pps", "term": "p", "index": "n",
                "forms": "p + pps(1), ..., p + pps(n) all prime, "
                         "p + pps(n+1) not (and p prime)",
                "name": "Smallest prime number p such that p + pps(1), "
                        "p + pps(2), ..., p + pps(n) are all prime but "
                        "p + pps(n+1) is not, where pps(n) is the partial "
                        "primorial sum (A060389(n)).",
                "data": "2,17,11,5,3,101,19469,38669,191459,191,59,3877889,"
                        "494272241,360772331,6004094833991,41320119600341",
                "offset_line": "0,1",
                "revision": "#19 May 17 2015 05:37:21",
                "keywords": "hard,nonn,more",
                "author": "Fred Schneider, Apr 25 2015",
                "frontier_by": "Fred Schneider, May 15 2015",
                "also": ()},
    "A257467": {"kind": "primorial", "shift": "psq", "term": "p", "index": "n",
                "forms": "p + psq(1), ..., p + psq(n) all prime, "
                         "p + psq(n+1) not (and p prime)",
                "name": "Smallest prime number p such that p + psq(1), "
                        "p + psq(2), ... p + psq(n) are all prime but "
                        "p+psq(n+1) is not. (psq(n) is the square of the "
                        "primorial.)",
                "data": "2,3,43,7,163,397,5527,454543,615883,142516687,"
                        "68967673,57502725253,37520993053,2630665498987,"
                        "39809897510563",
                "offset_line": "0,1",
                "revision": "#19 May 16 2015 17:40:57",
                "keywords": "hard,nonn",
                "author": "Fred Schneider, Apr 25 2015",
                "frontier_by": "Fred Schneider, May 16 2015",
                "also": ()},
    "A258035": {"kind": "primorial", "shift": "pssq", "term": "p", "index": "n",
                "forms": "p + pssq(1), ..., p + pssq(n) all prime, "
                         "p + pssq(n+1) not (and p prime)",
                "name": "Smallest prime number p such that p + pssq(1), "
                        "p + pssq(2), ... p + pssq(n) are all prime but "
                        "p+pssq(n+1) is not, where pssq(n) is the partial "
                        "sum of the square of the proper terms of the "
                        "primorial (A189997(n)-1).",
                "data": "2,37,3,7,13,277,2617,43,2924263,300999679,"
                        "631112173,1368737917,4428230508349",
                "offset_line": "0,1",
                "revision": "#20 Jul 09 2015 20:08:57",
                "keywords": "hard,more,nonn",
                "author": "Fred Schneider, May 16 2015",
                "frontier_by": "Fred Schneider, Jul 09 2015",
                "also": ()},
}

ALIASES = {}

# Published terms that do NOT satisfy their entry's definition at the index
# they are listed under: {family: {index: the run the listed value really
# has}}.  G1 checks every row.  KNOWN stops below the first of them.
ERRATA = {"A258035": {11: 12, 12: 13}}


def _published(fam):
    """{OEIS index: term}, from the %S data and the %O offset, verbatim."""
    f = FAMILIES[fam]
    off = int(f["offset_line"].split(",")[0])
    return {off + i: int(v) for i, v in enumerate(f["data"].split(","))}


def _cut(fam):
    """The first index KNOWN does not build on: the first erratum, or one
    past the published list."""
    return min(ERRATA.get(fam, {}), default=len(PUBLISHED[fam]))


# The published terms, as published, keyed by the OEIS INDEX (%O).
PUBLISHED = {fam: _published(fam) for fam in FAMILIES}

# The published terms this project builds on: PUBLISHED below the first
# erratum.  Everything but G1 and G1c reads this.
KNOWN = {fam: {n: x for n, x in PUBLISHED[fam].items() if n < _cut(fam)}
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
    """The letter the OEIS name gives the term."""
    return FAMILIES[family(fam)]["term"]


def offset(fam):
    """The OEIS index of the family's first term (its %O offset): 0 here."""
    return int(FAMILIES[family(fam)]["offset_line"].split(",")[0])


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


def frontier(fam):
    """The largest n with a(0..n) all known: the index below the LOWEST
    open one.  (A term found above an open index does not move it.)"""
    fam = family(fam)
    n = offset(fam) - 1
    while term(fam, n + 1, missing=None) is not None:
        n += 1
    return n


@_lru_cache(maxsize=None)
def primorial_k(k):
    """prime(k)#, with prime(0)# = 1."""
    return 1 if k == 0 else int(primorial(k))


@_lru_cache(maxsize=None)
def shift_k(fam, k):
    """c(k), k >= 1: pps(k), psq(k) or pssq(k)."""
    fam, k = family(fam), int(k)
    if k < 1:
        raise ValueError("the shifts are indexed from 1")
    s = FAMILIES[fam]["shift"]
    if s == "pps":
        return sum(primorial_k(i) for i in range(1, k + 1))
    if s == "psq":
        return primorial_k(k) ** 2
    return sum(primorial_k(i) ** 2 for i in range(1, k + 1))


def constants(fam, n):
    """The additive constants of the conditions that must be PRIME at index
    n, in form order: 0 (the term itself) then c(1), ..., c(n)."""
    fam, n = family(fam), int(n)
    return [0] + [shift_k(fam, k) for k in range(1, n + 1)]


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
    """x is a prime whose run is EXACTLY n.  NOT the least-claim: that is a
    sweep's to make."""
    fam, x, n = family(fam), int(x), int(n)
    return in_domain(fam, x) and run_length(fam, x, cap=n + 1) == n


def first_reach(fam, n):
    """(m, a(m)): the least known term of index m >= n -- the first prime a
    sweep from the bottom of the line meets with a run of AT LEAST n, as
    far as the known terms say.  What a canary at filter n must find."""
    fam = family(fam)
    both = dict(KNOWN[fam])
    both.update(FOUND[fam])
    x, m = min((x, m) for m, x in both.items() if m >= int(n))
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
    family(fam)
    q, n = int(q), int(n)
    pi_q = sum(1 for _ in primerange(2, q + 1))
    return 1 + min(n, pi_q - 1)


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
    """The least prime x >= lo (default 2) whose run is EXACTLY n, by the
    bare definition, one integer at a time; None if there is none below
    hi.  The slowest thing in this project."""
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
# the published term of that index.
REGEN_X = {"A257466": 200_000, "A257467": 620_000, "A258035": 50_000}


def g1_knowns_reproduce():
    """Every known term is a prime whose run is EXACTLY its index, in its
    forced class (the primes 2 and 3 excepted); and the erratum: each
    published value KNOWN leaves out has the run ERRATA says, not the index
    it is listed under."""
    parts = []
    for fam in FAMILIES:
        known = KNOWN[fam]
        for n in sorted(known):
            x = known[n]
            if not in_domain(fam, x):
                return False, f"G1 FAIL: {fam} a({n}) = {x} is not prime"
            r = run_length(fam, x, cap=n + 3)
            if r != n:
                return False, (f"G1 FAIL: {fam} a({n}) = {x} has run {r}, "
                               f"not exactly {n}")
            if not is_term(fam, x, n):
                return False, f"G1 FAIL: {fam} a({n}) = {x}: is_term disagrees"
            if n >= 1 and x > 3:
                for q in forced_primes(fam, n):
                    if x % q != forced_residue(q, n, fam):
                        return False, (f"G1 FAIL: {fam} a({n}) = {x} is not in "
                                       f"the class {q} forces")
        top = max(known)
        if sorted(known) != list(range(0, top + 1)) or frontier(fam) != top:
            return False, f"G1 FAIL: {fam}'s known terms are not a(0)..a({top})"
        parts.append(f"{fam} a(0)-a({top})")
    err = []
    for fam, rows in ERRATA.items():
        for n, real in sorted(rows.items()):
            x = PUBLISHED[fam][n]
            r = run_length(fam, x, cap=real + 2)
            if r != real or r == n or n in KNOWN[fam]:
                return False, (f"G1 FAIL: the erratum on {fam} a({n}) = {x}: "
                               f"its run is {r}, ERRATA says {real}")
            err.append(f"{fam}'s listed a({n}) = {x} has a run of exactly {r}")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every term is a prime "
                  "whose run is EXACTLY its index and lies in its forced "
                  "class; ERRATUM, checked: " + "; ".join(err) + ", so neither "
                  "is the term it is listed as and KNOWN stops below them")


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
                               f"prime with a run of exactly {n}")
        parts.append(f"{fam} a({min(found)})-a({max(found)})")
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each against the bare definition the moment "
                      "one is entered in FOUND")
    return True, "G1b ok: this project's finds " + "; ".join(parts)


def g1c_every_index_is_the_oeis_index():
    """PUBLISHED is the %S list keyed by the %O offset, and KNOWN is
    PUBLISHED below the first erratum, and nothing else."""
    rows = []
    for fam, f in FAMILIES.items():
        off = int(f["offset_line"].split(",")[0])
        data = [int(v) for v in f["data"].split(",")]
        want = {off + i: v for i, v in enumerate(data)}
        if off != 0 or PUBLISHED[fam] != want or offset(fam) != 0:
            return False, f"G1c FAIL: {fam}'s PUBLISHED is not its %S list keyed by %O"
        cut = _cut(fam)
        if KNOWN[fam] != {n: v for n, v in want.items() if n < cut}:
            return False, f"G1c FAIL: {fam}'s KNOWN is not PUBLISHED below a({cut})"
        if frontier(fam) != cut - 1:
            return False, f"G1c FAIL: {fam}'s frontier is a({frontier(fam)})"
        rows.append(f"{fam} %O {f['offset_line']}: a(0)..a({len(data) - 1}) "
                    f"published, a(0)..a({cut - 1}) built on, open a({cut}) "
                    f"with {nforms(fam, cut)} conditions")
    return True, "G1c ok: " + "; ".join(rows)


def g2_rederive_small():
    """Walk every prime below REGEN_X, read its exact run from the bare
    definition, and require the first occurrence of each run length to be
    the published term of that index -- and no run length to appear below
    the bound whose term is published above it."""
    done = []
    for fam in FAMILIES:
        first = {}
        for x in primerange(2, REGEN_X[fam]):
            r = run_length(fam, x)
            if r not in first:
                first[r] = x
        want = {n: x for n, x in PUBLISHED[fam].items() if x < REGEN_X[fam]}
        if first != want:
            return False, (f"G2 FAIL: {fam}: the first occurrences below "
                           f"{REGEN_X[fam]} are {first}, published {want}")
        for n, x in want.items():
            if first_x(fam, n, lo=max(2, x - 50), hi=x + 1) != x:
                return False, f"G2 FAIL: first_x disagrees at {fam} a({n})"
        done.append(f"{fam} a({', '.join(map(str, sorted(want)))}) below "
                    f"{REGEN_X[fam]:,}")
    return True, ("G2 ok: " + "; ".join(done) + " -- every prime below each "
                  "bound read from the definition alone, the first occurrence "
                  "of each exact run is the published term, and no other run "
                  "length occurs there")


def _filters(fam):
    top = frontier(fam)
    return sorted({1, 2, 5, 9, top - 2, top, top + 1, top + 4})


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
                  f"(q < 120, n, F), each inside its proved bound 1 + "
                  f"min(n, pi(q) - 1), and K(q,n) is a subset of K(q,n+1)")


_WANT_UNIT = {"A257466": (5, 6), "A257467": (1, 6), "A258035": (1, 6)}


def g2c_admissible_and_forced():
    """Every filter to n = 30 is admissible (w < q at every prime under
    400); the forced primes are exactly 2 and 3 from n = 1 on (classes 5,
    1 and 1 mod 6); no prime past 3 is ever forced."""
    rows = []
    for fam in FAMILIES:
        r, u = _WANT_UNIT[fam]
        for n in range(1, 31):
            for q in primerange(2, 400):
                if w(q, n, fam) >= q:
                    return False, (f"G2c FAIL: {fam} n={n}: q={q} kills every "
                                   f"residue")
            forced = forced_primes(fam, n)
            if forced != [2, 3]:
                return False, (f"G2c FAIL: {fam} forces {forced} at n = {n}")
            rr, mm = 0, 1
            for q in forced:
                a = forced_residue(q, n, fam)
                rr, mm = rr + mm * (((a - rr) * pow(mm, -1, q)) % q), mm * q
            if (rr, mm) != (r, u):
                return False, (f"G2c FAIL: {fam} n={n}: the forced class is "
                               f"{rr} (mod {mm}), expected {r} (mod {u})")
        ok, q = admissible(fam, 60)
        if not ok:
            return False, f"G2c FAIL: {fam} is not admissible at n = 60 ({q})"
        rows.append(f"{fam} x == {r} (mod {u})")
    return True, ("G2c ok: every filter to n = 30 is admissible at every prime "
                  "under 400, the forced classes are exactly " +
                  "; ".join(rows) + " at every n >= 1, and no prime past 3 is "
                  "forced")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce,
         g1c_every_index_is_the_oeis_index, g2b_killed_set_three_ways,
         g2c_admissible_and_forced, g2_rederive_small]


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
