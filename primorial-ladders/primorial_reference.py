"""The oracle for the primorial shift ladders -- slow, obviously correct,
sympy only.

    A115785(n) = smallest prime p with p - prime(k)# prime for k = 1..n
    A115786(n) = smallest prime p with p + prime(k)# prime for k = 1..n
    A145743(n) = smallest COMPOSITE m with m + 4*k^2 prime for k = 1..n

Three SHIFT LADDERS: one unknown and n (or n + 1) conditions that differ
only by an ADDITIVE constant -- the primorials, with either sign, or the
even squares.  The first two are Rick L. Shepherd's (Jan 2006), their last
terms Jens Kruse Andersen's (Feb 2006); the third is Farideh Firoozbakht's
(Oct 2008), its last two Donovan Johnson's (Nov 2008).  Nothing has moved
on any of them since.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

A FORM is a triple (a, b, e) meaning a*x^e + b, kept so that the engines
read their forms the way every project here does; every form of these
families is (1, c, 1): x + c.  The conditions of index n:

    A115785:  x,  x - 2,  x - 6,  ...,  x - prime(n)#       (n + 1 forms)
    A115786:  x,  x + 2,  x + 6,  ...,  x + prime(n)#       (n + 1 forms)
    A145743:  x + 4,  x + 16,  ...,  x + 4*n^2              (n forms; and
                                                            x COMPOSITE)

The term itself is a form of the primorial families (p is prime) and is
NOT one of A145743's: m must be composite, which no sieve expresses -- it is
a DOMAIN predicate the classification applies (a prime m has run 0 here).

THE FLOOR OF A115785 IS THE PRIMORIAL, NOT THE PREVIOUS TERM.  p - prime(n)#
must be a prime, so p >= prime(n)# + 2, and every published term sits within
1.2% above its own primorial (a(15) - 47# = 3.8e15 against 47# = 6.1e17).
Each index is therefore its OWN short line from prime(n)#, and a find of
a(n) says nothing about the line of a(n + 1), which starts prime(n + 1)
times further out.  The other two families nest the ordinary way: a(n) >=
a(n - 1) (every condition of index n - 1 is a condition of index n), riders
are common (A115786's a(5)-a(8) are one integer, A145743's a(8)-a(10)), and
a find of run r settles every open index up to r at once.

Facts PROVED here rather than assumed, because both engines and the odds
model are built on them.

  THE KILLED SET.  For a prime q and a form x + c,  q | x + c  <=>  x == -c
  (mod q).  So

      K(q,n,F) = { -c mod q : c a constant of index n }

  and the engines sieve x against K(q,n,F) and nothing else: no inverse, no
  character, no case on q dividing anything.  w(q,n,F) is its size.
  K(q,n) is a subset of K(q,n+1): an index adds a constant and removes none.

  ITS SIZE, BOUNDED.  On the primorial families prime(k)# == 0 (mod q) as
  soon as prime(k) >= q, so every constant from index pi(q) on kills the
  SAME residue 0 that the form x itself kills:

      w(q,n,F) <= 1 + min(n, pi(q) - 1)         (primorial families)

  -- the small primes are nearly blind (q = 47 kills at most 15 residues of
  47 where a linear ladder's 47 kills n of them), which is lcm-ladders'
  regime and the reason the wheel here is weak and the sieve deep.  On
  A145743, -4k^2 ranges over -4 times the squares, (q - 1)/2 nonzero
  values and 0 (at k == 0 mod q), so w <= (q + 1)/2 for odd q and 1 at 2.

  ADMISSIBLE AT EVERY n, FOR EVERY FAMILY.  Both bounds are below q (pi(q)
  <= q - 1 for q >= 3, and w(2) = 1), so no prime kills every residue, the
  constellations have no fixed prime divisor, Dickson's conjecture applies
  and a find CONFIRMS it: each sequence is conjecturally infinite.

  THE FORCED CLASSES.  Modulo 2 every form x + c has c even, so x is ODD in
  all three families.  Modulo 3 the primorial families kill 0 (from x) and
  -(-+2) = +-2 mod 3 (from x -+ 2): one class is left, p == 1 (mod 3) on
  A115785 and p == 2 (mod 3) on A115786 -- the class is 1 (mod 6) or
  5 (mod 6) from n = 1 on.  A145743 kills 2 (mod 3) from n = 1 (k^2 == 1
  for 3 not dividing k, so -4k^2 == 2) and 0 (mod 3) from n = 3 (k = 3),
  so from n = 3 its class is 1 (mod 6) too, and 1 (mod 2) before.  No
  prime past 3 is ever forced: w <= 1 + pi(q) - 1 < q - 1 for q >= 5 on
  the primorial families and w <= (q + 1)/2 < q - 1 on A145743.  G2c checks
  all of it at every filter the campaigns will run.

  THE EXCEPTION ZONE.  "q divides the value, so the value is composite"
  needs the value to EXCEED q.  The smallest value is x - prime(n)# on
  A115785 and x itself (x + 4 on A145743) elsewhere, so a sieve to q2 is
  valid from x > prime(n)# + q2 (A115785) or x > q2; the engines refuse to
  run below that (k_floor), and the prefix between the definition's floor
  and the engine's is covered by brute force (prefix_hits) -- at every
  filter on A115785, whose line starts there every time.

Gates in this file: G1 (every published term satisfies the definition,
each ladder is monotone, A115785's terms sit just above their primorials,
the frontier term stops exactly where the entry says), G1b (this project's
own finds re-checked from the bare definition), G1c (every index is the
OEIS index: KNOWN rebuilt from the %S and %O lines verbatim), G2 (the small
terms re-derived exhaustively from the bare definition), G2b (the killed set
three ways and its proved bound), G2c (admissibility, the forced classes,
the riders as published).
"""

from functools import lru_cache as _lru_cache

from sympy import isprime, primerange, primorial

# ---------------------------------------------------------------- families

# `kind`       "primorial" (constants -+prime(k)#, the term a form) or
#              "square" (constants 4k^2, the term COMPOSITE).
# `sign`       the sign of the primorial constants.
# `term`       the letter the OEIS NAME gives the term (p, p, m), under which
#              the evidence files carry it (CONVENTIONS.md "Naming in an
#              evidence file"); `index` the name's index letter.
# `forms`      the condition in the name's own letters, for the evidence.
# `name`, `data`, `offset_line`, `revision`: the %N, %S (+%T +%U), %O and
#              %I lines VERBATIM from the OEIS export of 2026-10-02, which
#              G1c rebuilds every index from.
# `also`       entries settled for free: none.  A115785 is a subset of
#              A006512 and A115786 of A001359 and A022004 (the entries'
#              own %C lines); neither is an affine map of a term.
FAMILIES = {
    "A115785": {"kind": "primorial", "sign": -1, "term": "p", "index": "k",
                "forms": "p - prime(k)#, k = 1..n (and p prime)",
                "name": "Smallest prime number p such that p - prime(1)#, "
                        "p - prime(2)#, ..., p - prime(n)# are all prime, "
                        "where prime(i)# is the primorial of the i-th prime "
                        "(A002110(i)).",
                "data": "5,13,43,229,3463,43789,1088449,19800379,264333259,"
                        "9348884059,228178314439,7931712374479,"
                        "307867708410673,13230211614496609,"
                        "618681508598750923",
                "offset_line": "1,1",
                "revision": "#13 Jun 25 2025 04:03:36",
                "keywords": "nonn,more",
                "author": "Rick L. Shepherd, Jan 31 2006",
                "frontier_by": "Jens Kruse Andersen, Feb 26 2006",
                "also": ()},
    "A115786": {"kind": "primorial", "sign": +1, "term": "p", "index": "k",
                "forms": "p + prime(k)#, k = 1..n (and p prime)",
                "name": "Smallest prime number p such that p + 2#, p + 3#, "
                        "..., p + prime(n)# are all prime, where x# = "
                        "A034386(x) is the primorial.",
                "data": "3,5,11,17,41,41,41,41,86351,86351,235313357,"
                        "729457511,99445156397,818113387907,7986903815771,"
                        "29065965967667",
                "offset_line": "1,1",
                "revision": "#12 Jan 19 2019 04:14:58",
                "keywords": "more,nonn",
                "author": "Rick L. Shepherd, Jan 31 2006",
                "frontier_by": "Jens Kruse Andersen, Feb 28 2006",
                "also": ()},
    "A145743": {"kind": "square", "sign": +1, "term": "m", "index": "k",
                "forms": "m + 4*k^2, k = 1..n (and m composite)",
                "name": "a(n) is the smallest composite number m such that "
                        "all n numbers m+4*k^2 for k=1,2,...,n are prime.",
                "data": "9,15,25,25,247,583,5377,143473,143473,143473,"
                        "2821813,62087033647,91450844347",
                "offset_line": "1,1",
                "revision": "#3 Mar 30 2012 17:37:44",
                "keywords": "more,nonn",
                "author": "Farideh Firoozbakht, Oct 17 2008",
                "frontier_by": "Donovan Johnson, Nov 17 2008",
                # the entry's %C: "There is no further term up to 5*10^8"
                # (stale: a(12) and a(13) are past it; the campaign sweeps
                # from a(13) + 1 and relies on nothing)
                "also": ()},
}

ALIASES = {}


def _published(fam):
    """{OEIS index: term}, from the %S data and the %O offset, verbatim."""
    f = FAMILIES[fam]
    off = int(f["offset_line"].split(",")[0])
    return {off + i: int(v) for i, v in enumerate(f["data"].split(","))}


# The published terms, as published, keyed by the OEIS INDEX (%O).
KNOWN = {fam: _published(fam) for fam in FAMILIES}

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
    """The OEIS index of the family's first term (its %O offset): 1 here."""
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
    """The largest n with a(1..n) all known."""
    fam = family(fam)
    n = 0
    while term(fam, n + 1, missing=None) is not None:
        n += 1
    return n


@_lru_cache(maxsize=None)
def primorial_k(k):
    """prime(k)#, with prime(0)# = 1."""
    return 1 if k == 0 else int(primorial(k))


def constants(fam, n):
    """The additive constants of index n, in form order: 0 then
    -+prime(k)# for k = 1..n (the primorial families, the term itself
    first), or 4k^2 for k = 1..n (A145743)."""
    fam, n = family(fam), int(n)
    f = FAMILIES[fam]
    if f["kind"] == "primorial":
        return [0] + [f["sign"] * primorial_k(k) for k in range(1, n + 1)]
    return [4 * k * k for k in range(1, n + 1)]


def forms(fam, n):
    """The conditions on x at index n, as (a, b, e) with a*x^e + b prime:
    (1, c, 1) for every constant c."""
    return [(1, c, 1) for c in constants(fam, n)]


def nforms(fam, n):
    """How many conditions index n imposes."""
    return len(constants(fam, n))


def maxkills(fam, n):
    """The most residues one prime can kill at index n: one per form."""
    return nforms(fam, n)


def in_domain(fam, x):
    """Whether x is in the sequence's DOMAIN: a prime (the primorial
    families) or a composite (A145743).  The sieve expresses the first
    (x is a form) and cannot express the second."""
    fam, x = family(fam), int(x)
    if kind(fam) == "primorial":
        return x >= 2 and bool(isprime(x))
    return x >= 4 and not isprime(x)


def floor_x(fam, n):
    """The definition's own floor for a(n), INCLUSIVE: the least integer
    that could be a(n).  A115785: prime(n)# + 2 (p - prime(n)# is a prime)
    -- and at least a(n - 1), by nesting; the others: a(n - 1) itself
    (INCLUSIVE: a(n - 1) is a(n) too when its run reaches n -- a rider),
    else 2 (a prime) or 4 (a composite)."""
    fam, n = family(fam), int(n)
    prev = term(fam, n - 1, missing=None) if n > 1 else None
    if kind(fam) == "primorial" and FAMILIES[fam]["sign"] < 0:
        lo = primorial_k(n) + 2
        return max(lo, prev or 0)
    if prev is None:
        return 2 if kind(fam) == "primorial" else 4
    return prev


def value(f, x):
    """The value of form f = (a, b, e) at x."""
    a, b, e = f
    return a * int(x) ** e + b


def values(fam, x, n):
    """Every value the conditions at index n form at x, in form order."""
    return [value(f, x) for f in forms(fam, n)]


def run_length(fam, x, cap=64):
    """The run of x: 0 if x is outside the domain (a composite on the
    primorial families, a prime or x < 4 on A145743), else the largest
    r <= cap with x + c_k prime for every k = 1..r.  A value below 2 (x -
    prime(k)# past the floor) is not prime, so a run on A115785 cannot
    pass pi(the largest primorial under x)."""
    fam, x = family(fam), int(x)
    if not in_domain(fam, x):
        return 0
    f = FAMILIES[fam]
    r = 0
    while r < cap:
        c = (f["sign"] * primorial_k(r + 1) if f["kind"] == "primorial"
             else 4 * (r + 1) ** 2)
        v = x + c
        if v < 2 or not isprime(v):
            break
        r += 1
    return r


def is_term(fam, x, n):
    """x satisfies every condition of index n and lies at or above the
    definition's floor.  NOT the least-claim: that is a sweep's to make."""
    fam, x, n = family(fam), int(x), int(n)
    return x >= floor_x(fam, n) and run_length(fam, x, cap=n) >= n


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
    fam, q, n = family(fam), int(q), int(n)
    if kind(fam) == "primorial":
        pi_q = sum(1 for _ in primerange(2, q + 1))
        return 1 + min(n, pi_q - 1)
    return 1 if q == 2 else min(n, (q - 1) // 2) + (1 if n >= q else 0)


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
    """The least x >= lo (default the definition's floor) with a run of at
    least n, by the bare definition, one integer at a time; None if there
    is none below hi.  The slowest thing in this project, and the reason
    G2 only covers the small terms."""
    fam, n = family(fam), int(n)
    x = floor_x(fam, n) if lo is None else int(lo)
    while hi is None or x < hi:
        if run_length(fam, x, cap=n) >= n:
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

# How far G2 regenerates each family by brute force: A115785 to a(7) (a
# 578,000-integer walk above 7#), A115786 to a(10) (86,351), A145743 to
# a(10) (143,473).  Beyond those the walk is minutes, and the CPU engine's
# G5 takes over.
REGEN_TO = {"A115785": 7, "A115786": 10, "A145743": 10}


def g1_knowns_reproduce():
    """Every published term satisfies the definition with a run of at least
    its index, each ladder is monotone, every A115785 term sits just above
    its own primorial, each term is in its forced class, and the frontier
    term's run is EXACTLY the frontier (the next value is composite)."""
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
            if x < floor_x(fam, n) and n > 1:
                return False, (f"G1 FAIL: {fam} a({n}) = {x} is under the "
                               f"definition's floor {floor_x(fam, n)}")
            if not in_domain(fam, x):
                return False, f"G1 FAIL: {fam} a({n}) = {x} is outside the domain"
            if fam == "A115785" and not (primorial_k(n) < x < 3 * primorial_k(n)
                                         and (n < 13 or x < 1.02 * primorial_k(n))):
                return False, (f"G1 FAIL: {fam} a({n}) = {x} is not just above "
                               f"prime({n})# = {primorial_k(n)} (within 3x, and "
                               f"2% from n = 13)")
            if n >= 2:
                for q in forced_primes(fam, n):
                    if x % q != forced_residue(q, n, fam):
                        return False, (f"G1 FAIL: {fam} a({n}) = {x} is not in "
                                       f"the class {q} forces")
            prev = x
        top = max(known)
        if run_length(fam, known[top], cap=top + 4) != top:
            return False, (f"G1 FAIL: {fam} a({top}) does not stop exactly at "
                           f"run {top} -- a({top + 1}) would not be open")
        wall = values(fam, known[top], top + 1)[-1]
        parts.append(f"{fam} a(1)-a({top}) (the value at index {top + 1}, "
                     f"{wall}, composite)")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every term satisfies the "
                  "definition, each ladder is monotone, every A115785 term "
                  "sits within 2% above its primorial, every term is in its "
                  "forced class, and each frontier term stops exactly where "
                  "the entry says")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition."""
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
                               f"satisfy index {n} above its floor")
            top = n
        parts.append(f"{fam} a({min(found)})-a({max(found)})")
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each against the bare definition the moment "
                      "one is entered in FOUND")
    return True, "G1b ok: this project's finds " + "; ".join(parts)


def g1c_every_index_is_the_oeis_index():
    """KNOWN is the %S list keyed by the %O offset, and nothing else."""
    rows = []
    for fam, f in FAMILIES.items():
        off = int(f["offset_line"].split(",")[0])
        data = [int(v) for v in f["data"].split(",")]
        want = {off + i: v for i, v in enumerate(data)}
        if off != 1 or KNOWN[fam] != want or offset(fam) != 1:
            return False, f"G1c FAIL: {fam}'s KNOWN is not its %S list keyed by %O"
        if frontier(fam) != len(data):
            return False, f"G1c FAIL: {fam}'s frontier is a({frontier(fam)})"
        if [term(fam, i) for i in range(1, frontier(fam) + 1)] != data:
            return False, f"G1c FAIL: {fam}'s terms do not read back as %S"
        rows.append(f"{fam} %O {f['offset_line']}: a(1)..a({len(data)}), "
                    f"open a({len(data) + 1}) with {nforms(fam, len(data) + 1)} "
                    f"conditions")
    return True, "G1c ok: " + "; ".join(rows)


def g2_rederive_small():
    """Re-derive the small terms exhaustively from the bare definition, from
    each index's own floor (prime(n)# on A115785) -- riders included: a
    rider must come out EQUAL to its predecessor."""
    done = []
    for fam in FAMILIES:
        for n in range(1, REGEN_TO[fam] + 1):
            got = first_x(fam, n, hi=KNOWN[fam][n] + 1)
            if got != KNOWN[fam][n]:
                return False, (f"G2 FAIL: {fam} re-derived a({n}) = {got} != "
                               f"{KNOWN[fam][n]}")
        done.append(f"{fam} a(1)-a({REGEN_TO[fam]})")
    return True, ("G2 ok: " + ", ".join(done) + " re-derived exhaustively, one "
                  "integer at a time from each index's own floor, from the "
                  "definition alone (riders included)")


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
                  f"(q < 120, n, F), each inside its proved bound (1 + "
                  f"min(n, pi(q) - 1) on the primorial families, (q + 1)/2 on "
                  f"A145743), and K(q,n) is a subset of K(q,n+1)")


def g2c_admissible_and_forced():
    """Every filter to n = 30 is admissible (w < q at every prime under
    400); the forced primes are exactly 2 and 3 -- from n = 1 on the
    primorial families (classes 1 and 5 mod 6), from n = 3 on A145743
    (class 1 mod 6; 1 mod 2 before); no prime past 3 is ever forced; and
    the published riders are riders."""
    rows = []
    want_unit = {"A115785": (1, 6), "A115786": (5, 6), "A145743": (1, 6)}
    for fam in FAMILIES:
        for n in range(1, 31):
            r, u = want_unit[fam]
            if fam == "A145743" and n < 3:
                r, u = 1, 2          # 3 is forced from k = 3 on
            for q in primerange(2, 400):
                if w(q, n, fam) >= q:
                    return False, (f"G2c FAIL: {fam} n={n}: q={q} kills every "
                                   f"residue")
            forced = forced_primes(fam, n)
            if forced != [q for q in (2, 3) if u % q == 0]:
                return False, (f"G2c FAIL: {fam} forces {forced} at n = {n}")
            # the CRT of the single free classes
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
        riders = [n for n in sorted(KNOWN[fam]) if n > 1
                  and KNOWN[fam][n] == KNOWN[fam][n - 1]]
        for n in riders:
            if run_length(fam, KNOWN[fam][n], cap=n) < n:
                return False, f"G2c FAIL: {fam} a({n}) is listed as a rider but is not"
        rows.append(f"{fam} x == {r} (mod {u}) from n = "
                    f"{3 if fam == 'A145743' else 1}, riders at {riders or 'none'}")
    return True, ("G2c ok: every filter to n = 30 is admissible at every prime "
                  "under 400, the forced classes are exactly " +
                  "; ".join(rows) + " at every n, no prime past 3 is forced, "
                  "and every published rider reaches its index")


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
