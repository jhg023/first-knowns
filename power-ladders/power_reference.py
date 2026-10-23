"""The oracle for the power ladders -- slow, obviously correct, sympy only.

    A229626(n) = the smallest m such that 2*m^k - 1 is prime for k = 1..n
    A229627(n) = the smallest prime q such that 2*q^k - 1 is prime for
                 k = 1..n
    A229630(n) = the smallest semiprime m such that 2*m^k - 1 is prime for
                 k = 1..n
    A229902(n) = the smallest m such that 19*m^k + 1 is prime for k = 1..n

Four POWER LADDERS: one unknown term and n conditions that differ only in
the EXPONENT -- the k-th condition is a multiplier times the k-th power of
the term, plus or minus one.  The cluster is October 2013: A229626 and
A229627 are Farideh Firoozbakht's (Sep 27 2013), A229630 hers too (Oct 14),
A229902 Jahangeer Kholdi's (Oct 04); Giovanni Resta and Charles R Greathouse
IV extended them that month, and Tyler Busby took A229626 to a(9), A229627
to a(8) and A229902 to a(8) in January 2023 (A229627's comment: "a(9) >
3*10^13").  A229630 has not moved since Greathouse's a(8) of Oct 17 2013.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW;
sympy's nthroot_mod and factorint) and the definition as written.

A FORM is a triple (a, b, e) meaning a*x^e + b -- the shape every project
here reads its forms in -- and the conditions of index n are

    A229626, A229630:   2*x^k - 1,  k = 1..n        (n forms)
    A229627:            x,  2*x^k - 1,  k = 1..n    (n + 1 forms: q prime)
    A229902:            19*x^k + 1, k = 1..n        (n forms)

where x is the engines' name for the term (m on three entries, q on
A229627).  A229627's q must itself be prime, and that IS a form -- the
sieve expresses it.  A229630's m must be a SEMIPRIME, which no sieve
expresses: it is a DOMAIN predicate the classification applies (a run is 0
outside the domain), exactly as primorial-ladders' A145743 applies "m
composite".

THE LADDERS NEST.  Every condition of index n is one of index n + 1, so
a(n + 1) >= a(n), and EQUALITY HAPPENS: a term whose run passes its index
is the next term too (A229626's a(1) = a(2) = 2, A229902's a(1) = a(2) =
a(3) = 10).  The line of a(n) therefore starts AT a(n - 1), inclusive --
and A229902's published a(8) = 1944616927560 has a run of NINE (19*m^9 + 1
is prime; 19*m^10 + 1 is divisible by 23), so a(9) = a(8): a term the
OEIS does not list, which the campaign's first segment records (RUNS_PAST,
G1).

Facts PROVED here rather than assumed, because both engines and the odds
model are built on them.

  THE KILLED SET.  For a prime l not dividing the multiplier c, a form
  c*x^k + d vanishes mod l exactly when x^k == a = -d/c (mod l), and that
  has gcd(k, l - 1) solutions when a is a gcd(k, l - 1)-th power residue
  and none otherwise (the k-th power map on the cyclic group (Z/l)* has
  kernel of size gcd(k, l - 1)).  So

      K(l,n,F) = union over k = 1..n of { x : x^k == a (mod l) }
                 (and {0} when the term itself is a form: A229627)

  and for l | c (2 on the 2*m^k - 1 ladders, 19 on A229902) no power form
  ever vanishes (c*x^k + d == d = -+1): K is empty, or {0} on A229627.
  K(l,n) is a subset of K(l,n+1).  It is built three ways below -- the
  residue walk, sympy's nthroot_mod, and direct divisibility of the values
  -- and the CPU engine builds it a fourth way (a discrete logarithm), G3.

  ITS SIZE, BOUNDED.  |K(l,n,F)| <= sum_{k<=n} gcd(k, l - 1) <= n(n+1)/2,
  plus one for A229627's form q.  That is the residue list the GPU tail
  must hold (maxkills), and unlike every linear ladder in this repository
  it is NOT one per form: l = 601 kills 28 residues at n = 9 and 41 at
  n = 12 on A229626.  The average over l is about one per form (a random
  a has one k-th root on average), so the wheel is WEAK -- the primes to 59
  keep 1e-3 to 2e-5 of the line at the open indices, the primorial ladders'
  regime, not the polynomial runs'.

  ADMISSIBLE AT EVERY n.  On the 2*m^k - 1 ladders the class 1 is never
  killed (2*1 - 1 = 1), and 0 is never killed by a power form (the value is
  -1); on A229902 the class 0 is never killed (the value is 1).  So no prime
  covers every residue, Dickson's conjecture applies, and every index is
  conjecturally attained.

  THE FORCED CLASSES.  A229627: q is odd and q == 1 (mod 3) from n = 1 (the
  form q kills 0 mod 2 and mod 3, and 2*q - 1 kills 2 mod 3): the class is
  1 (mod 6).  A229902: m is EVEN from n = 1 (19*m + 1 is even for odd m)
  and m == 0 (mod 5) from n = 4 (19 == -1 mod 5, so m^k == 1 for k = 1, 2,
  4 kills 1, 4, 2 and 3): the class is 0 (mod 10) -- the entry's own
  comment, "10 divides all terms".  A229626 and A229630 have NO forced
  prime: both 0 and 1 survive every l, and 2 kills nothing at all.  G2c
  checks it at every filter to n = 30.

  THE EXCEPTION ZONE.  "l divides the value, so the value is composite"
  needs the value to EXCEED l.  The smallest value is the k = 1 form (and
  q itself on A229627), so a sieve to q2 is valid from c*x + d > q2; the
  engines refuse to run below that (k_floor), and the integers below are
  classified one at a time by brute force (prefix_hits).  It is not
  vacuous: A229627's a(1) = a(2) = 2 and a(3) = 3 are primes a sieve with
  the form q would have "killed" by themselves.

Gates in this file: G1 (every published term satisfies the definition with
a run of at least its index, each ladder is monotone, each term is in its
domain and in its forced class, each frontier term stops exactly where the
entry says -- A229902's a(8) excepted, whose run of nine is RUNS_PAST),
G1b (this project's own finds), G1c (every index is the OEIS index: KNOWN
rebuilt from the %S and %O lines verbatim), G2 (the small terms re-derived
exhaustively from the bare definition, riders included), G2b (the killed
set three ways and its proved bound), G2c (admissibility and the forced
classes).
"""

from functools import lru_cache as _lru_cache
from math import gcd

from sympy import factorint, isprime, nthroot_mod, primerange

# ---------------------------------------------------------------- families

# `c`, `d`     the k-th condition is c*x^k + d.
# `domain`     "any" (every positive integer), "prime" (the term itself is a
#              form: A229627) or "semiprime" (a predicate no sieve
#              expresses: A229630).
# `term`       the letter the OEIS NAME gives the term (m, q, m, m), under
#              which the evidence files carry it (CONVENTIONS.md "Naming in
#              an evidence file"); `exp` the name's exponent letter (k
#              everywhere), `index` its index letter (n everywhere).
# `forms`      the condition in the name's own letters, for the evidence.
# `name`, `data`, `offset_line`, `revision`, `keywords`: the %N, %S, %O,
#              %I and %K lines VERBATIM from the OEIS export of 2026-10-15,
#              which G1c rebuilds every index from.
# `bound_comment`  a lower bound the entry states in a comment.  The
#              campaign does NOT start from it: its line starts at the
#              frontier term, so the claim it publishes rests on its own
#              sweep (and a find under the bound would contradict it).
# `also`       entries a find settles for free: none of these is an affine
#              map of a term of another entry.
FAMILIES = {
    "A229626": {"kind": "power", "c": 2, "d": -1, "domain": "any",
                "term": "m", "exp": "k", "index": "n",
                "forms": "2*m^k - 1, k = 1..n",
                "name": "a(n) is the smallest m such that 2*m^k-1 is prime "
                        "for k = 1, 2, ..., n.",
                "data": "2,2,3,6,6,11256895,15682744,45779314036,"
                        "687860415949",
                "offset_line": "1,1",
                "revision": "#19 Jan 06 2023 22:27:03",
                "keywords": "nonn,more",
                "author": "Farideh Firoozbakht, Sep 27 2013",
                "frontier_by": "Tyler Busby, Jan 06 2023",
                "bound_comment": None,
                "also": ()},
    "A229627": {"kind": "power", "c": 2, "d": -1, "domain": "prime",
                "term": "q", "exp": "k", "index": "n",
                "forms": "2*q^k - 1, k = 1..n (q prime)",
                "name": "a(n) is the smallest prime q such that 2*q^k - 1 is "
                        "prime for k = 1, 2, ..., n.",
                "data": "2,2,3,92581,385939,464938699,24137752519,"
                        "1095265755949",
                "offset_line": "1,1",
                "revision": "#29 Jun 14 2025 01:49:15",
                "keywords": "nonn,more",
                "author": "Farideh Firoozbakht, Sep 27 2013",
                "frontier_by": "Tyler Busby, Jan 06 2023",
                "bound_comment": (9, 3 * 10 ** 13,
                                  "a(9) > 3*10^13. - Tyler Busby, Jan 14 2023"),
                "also": ()},
    "A229630": {"kind": "power", "c": 2, "d": -1, "domain": "semiprime",
                "term": "m", "exp": "k", "index": "n",
                "forms": "2*m^k - 1, k = 1..n (m semiprime)",
                "name": "a(n) is the smallest semiprime m such that 2*m^k-1 "
                        "is prime for k = 1, 2, ..., n.",
                "data": "4,4,4,6,6,118909855,5740959589,79235997091",
                "offset_line": "1,1",
                "revision": "#12 Oct 17 2013 01:59:36",
                "keywords": "nonn,more",
                "author": "Farideh Firoozbakht, Oct 14 2013",
                "frontier_by": "Charles R Greathouse IV, Oct 17 2013",
                "bound_comment": None,
                "also": ()},
    "A229902": {"kind": "power", "c": 19, "d": 1, "domain": "any",
                "term": "m", "exp": "k", "index": "n",
                "forms": "19*m^k + 1, k = 1..n",
                "name": "a(n) is the smallest m such that 19*m^k+1 is prime "
                        "for k=1, 2,...,n.",
                "data": "10,10,10,2080,178030,41697270,4355942080,"
                        "1944616927560",
                "offset_line": "1,1",
                "revision": "#12 Jan 06 2023 22:26:52",
                "keywords": "nonn,more",
                "author": "Jahangeer Kholdi, Oct 04 2013",
                "frontier_by": "Tyler Busby, Jan 06 2023",
                "bound_comment": None,
                "also": ()},
}

ALIASES = {}


def _published(fam):
    """{OEIS index: term}, from the %S data and the %O offset, verbatim."""
    f = FAMILIES[fam]
    off = int(f["offset_line"].split(",")[0])
    return {off + i: int(v) for i, v in enumerate(f["data"].split(","))}


# The published terms, keyed by the OEIS INDEX (%O).
KNOWN = {fam: _published(fam) for fam in FAMILIES}

# A PUBLISHED TERM WHOSE RUN PASSES ITS INDEX: A229902's a(8) has a run of
# exactly nine, so it is a(9) too (the ladders nest, and a(9) >= a(8)).
# G1 proves the run from the bare definition; the term is NOT entered in
# KNOWN (the OEIS does not list it) or in FOUND (no campaign has recorded
# it): the A229902 campaign opens at filter 9 with its line starting AT
# a(8), inclusive, so its first segment records a(9) = a(8) as a discovery
# with the evidence and the certificates every find carries.
RUNS_PAST = {"A229902": {8: 9}}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against;
# these are the project's own claim, which a campaign carries in its
# checkpoint (`found`).  G1b re-checks whatever lands here.
FOUND = {fam: {} for fam in FAMILIES}

# The exception zone is covered by brute force; G2b's divisibility checks
# run their values at heights well above any sieve depth.
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
    """The letter the OEIS name gives the term: m, q, m, m."""
    return FAMILIES[family(fam)]["term"]


def domain(fam):
    return FAMILIES[family(fam)]["domain"]


def coeffs(fam):
    """(c, d): the k-th condition is c*x^k + d."""
    f = FAMILIES[family(fam)]
    return int(f["c"]), int(f["d"])


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
    """The largest n with a(1..n) all known (the literature and the finds)."""
    fam = family(fam)
    n = offset(fam) - 1
    while term(fam, n + 1, missing=None) is not None:
        n += 1
    return n


def forms(fam, n):
    """The conditions on x at index n, as (a, b, e) with a*x^e + b prime:
    x itself on A229627, then c*x^k + d for k = 1..n."""
    fam, n = family(fam), int(n)
    c, d = coeffs(fam)
    out = [(1, 0, 1)] if domain(fam) == "prime" else []
    return out + [(c, d, k) for k in range(1, n + 1)]


def nforms(fam, n):
    return len(forms(fam, n))


def maxkills(fam, n):
    """The PROVED bound on how many residues one prime can kill at index n:
    sum_{k<=n} gcd(k, l - 1) <= n(n+1)/2, plus one for the form q."""
    fam, n = family(fam), int(n)
    return n * (n + 1) // 2 + (1 if domain(fam) == "prime" else 0)


def is_semiprime(x):
    """A product of exactly two primes (sympy's factorint)."""
    x = int(x)
    return x >= 4 and sum(factorint(x).values()) == 2


def in_domain(fam, x):
    """Whether x is in the sequence's DOMAIN: a positive integer, a prime
    (A229627) or a semiprime (A229630)."""
    x, dom = int(x), domain(fam)
    if dom == "prime":
        return x >= 2 and bool(isprime(x))
    if dom == "semiprime":
        return is_semiprime(x)
    return x >= 1


def floor_x(fam, n):
    """The definition's own floor for a(n), INCLUSIVE: a(n - 1) itself when
    it is known -- the ladders nest, and a(n - 1) IS a(n) when its run
    reaches n (a rider; A229902's a(8) is a(9)) -- else the least member of
    the domain (1, the prime 2, the semiprime 4)."""
    fam, n = family(fam), int(n)
    least = {"any": 1, "prime": 2, "semiprime": 4}[domain(fam)]
    prev = term(fam, n - 1, missing=None) if n > 1 else None
    return least if prev is None else max(least, prev)


def value(f, x):
    """The value of form f = (a, b, e) at x."""
    a, b, e = f
    return a * int(x) ** e + b


def values(fam, x, n):
    """Every value the conditions of index n form at x, in form order."""
    return [value(f, x) for f in forms(fam, n)]


def run_length(fam, x, cap=64):
    """The run of x: 0 outside the domain, else the largest r <= cap with
    c*x^k + d prime for every k = 1..r."""
    fam, x = family(fam), int(x)
    if not in_domain(fam, x):
        return 0
    c, d = coeffs(fam)
    r = 0
    while r < cap and isprime(c * x ** (r + 1) + d):
        r += 1
    return r


def is_term(fam, x, n):
    """x satisfies index n: in the domain, with a run of at least n.  NOT
    the least-claim: that is a sweep's to make."""
    return run_length(fam, x, cap=int(n)) >= int(n)


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
    """K(q,n,F) the algebraic way: the k-th roots of -d/c (mod q) for every
    k = 1..n, by sympy's nthroot_mod, and 0 when the term is a form."""
    fam, q, n = family(fam), int(q), int(n)
    c, d = coeffs(fam)
    out = {0} if domain(fam) == "prime" else set()
    if c % q:
        a = (-d) * pow(c, -1, q) % q
        for k in range(1, n + 1):
            roots = nthroot_mod(a, k, q, all_roots=True)
            if roots:
                out.update(int(r) % q for r in roots)
    return out


def w_count(q, n, fam):
    """|K(q,n,F)| the algebraic way.  G2b proves it equal to the walk."""
    return len(killed_algebraic(q, n, fam))


def w_bound(q, n, fam):
    """The PROVED upper bound on w(q,n,F) (module docstring)."""
    fam, q, n = family(fam), int(q), int(n)
    c, _d = coeffs(fam)
    extra = 1 if domain(fam) == "prime" else 0
    if c % q == 0:
        return extra
    return min(q - 1, sum(gcd(k, q - 1) for k in range(1, n + 1)) + extra)


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
    A theorem here (a class survives every prime: module docstring),
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
    x = floor_x(fam, n) if lo is None else int(lo)
    while hi is None or x < hi:
        if is_term(fam, x, n):
            return x
        x += 1
    return None


def prefix_hits(fam, n, lo, hi, floor=1, cap=64):
    """[(x, run)] for every x in [lo, hi] with a run of at least `floor`,
    by the bare definition -- how the exception zone is covered."""
    fam = family(fam)
    out = []
    for x in range(int(lo), int(hi) + 1):
        r = run_length(fam, x, cap=cap)
        if r >= floor:
            out.append((x, r))
    return out


# --------------------------------- gates -----------------------------------

# How far G2 walks each line by brute force: every member of the domain
# below the bound has its run read, and the first occurrence of each run
# length must be the published term of that index.  A229626 and A229630 to
# a(5) = 6 (their a(6) is past 1e8), A229627 to a(5) = 385,939, A229902 to
# a(5) = 178,030; the CPU engine's G5 and the GPU canaries take a(6) on.
REGEN_X = {"A229626": 200_000, "A229627": 400_000, "A229630": 50_000,
           "A229902": 200_000}

# The forced classes, as G2c expects them: (class, unit, from n).
_WANT_FORCED = {"A229626": [], "A229630": [],
                "A229627": [(2, 1, 1), (3, 1, 1)],
                "A229902": [(2, 0, 1), (5, 0, 4)]}


def g1_knowns_reproduce():
    """Every published term satisfies the definition with a run of at least
    its index, each ladder is monotone, each term is in its domain and its
    forced class (above the exception zone), and each frontier term stops
    exactly where the entry says -- A229902's a(8) excepted, whose run of
    NINE (RUNS_PAST) makes it a(9) as well."""
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
                return False, f"G1 FAIL: {fam} a({n}) = {x} < a({n - 1}) = {prev}"
            if not in_domain(fam, x) or x < floor_x(fam, n):
                return False, f"G1 FAIL: {fam} a({n}) = {x} is outside the domain"
            for q in forced_primes(fam, n):
                if x > q and x % q != forced_residue(q, n, fam):
                    return False, (f"G1 FAIL: {fam} a({n}) = {x} is not in "
                                   f"the class {q} forces")
            prev = x
        top = max(known)
        want = RUNS_PAST.get(fam, {}).get(top, top)
        got = run_length(fam, known[top], cap=top + 6)
        if got != want:
            return False, (f"G1 FAIL: {fam} a({top}) = {known[top]} has run "
                           f"{got}, expected exactly {want}")
        c, d = coeffs(fam)
        wall = c * known[top] ** (want + 1) + d
        if isprime(wall):
            return False, f"G1 FAIL: {fam}: the value past a({top})'s run is prime"
        parts.append(f"{fam} a(1)-a({top})"
                     + (f" (a({top}) runs to {want}: a({want}) = a({top}))"
                        if want != top else ""))
    return True, ("G1 ok: " + "; ".join(parts) + " -- every term satisfies the "
                  "definition, each ladder is monotone, every term is in its "
                  "domain and its forced class, and each frontier term stops "
                  "exactly where the entry says, except A229902's a(8) = "
                  "1944616927560, which runs to k = 9 (19*m^10 + 1 is "
                  "composite): a(9) = a(8), for the campaign's first segment "
                  "to record")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition."""
    parts = []
    for fam in FAMILIES:
        found = FOUND[fam]
        if not found:
            continue
        top = max(KNOWN[fam])
        prev = KNOWN[fam][top]
        for n in sorted(found):
            if n != top + 1:
                return False, (f"G1b FAIL: {fam} a({n}) does not continue the "
                               f"sequence from a({top})")
            if found[n] < prev or not is_term(fam, found[n], n):
                return False, (f"G1b FAIL: {fam} a({n}) = {found[n]} does not "
                               f"satisfy index {n} at or above a({top})")
            top, prev = n, found[n]
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
        if nforms(fam, len(data) + 1) != len(data) + 1 + (domain(fam) == "prime"):
            return False, f"G1c FAIL: {fam}'s open index has the wrong form count"
        rows.append(f"{fam} %O {f['offset_line']}: a(1)..a({len(data)}), "
                    f"open a({len(data) + 1}) with {nforms(fam, len(data) + 1)} "
                    f"conditions")
    return True, "G1c ok: " + "; ".join(rows)


def g2_rederive_small():
    """Walk every member of the domain below REGEN_X, read its run from the
    bare definition, and require the first m (or q) with a run of at least
    n to be the published a(n) for every n it reaches -- riders (a term
    equal to its predecessor) included."""
    done = []
    for fam in FAMILIES:
        first = {}
        top = 0
        lo = floor_x(fam, 1)
        it = (primerange(lo, REGEN_X[fam]) if domain(fam) == "prime"
              else range(lo, REGEN_X[fam]))
        for x in it:
            if domain(fam) == "semiprime":
                if not is_semiprime(x):
                    continue
            r = run_length(fam, x, cap=12)
            while top < r:
                top += 1
                first[top] = int(x)
        want = {n: x for n, x in KNOWN[fam].items() if x < REGEN_X[fam]}
        got = {n: x for n, x in first.items() if n in want or x < REGEN_X[fam]}
        if any(first.get(n) != x for n, x in want.items()):
            return False, (f"G2 FAIL: {fam}: the first occurrences below "
                           f"{REGEN_X[fam]} are {got}, published {want}")
        extra = [n for n in first if n not in KNOWN[fam]]
        if extra:
            return False, (f"G2 FAIL: {fam}: a run of {extra} occurs below "
                           f"{REGEN_X[fam]} with no published term")
        done.append(f"{fam} a({min(want)})-a({max(want)}) below {REGEN_X[fam]:,}")
    return True, ("G2 ok: " + "; ".join(done) + " -- every member of each "
                  "domain below its bound read from the definition alone, the "
                  "first with a run of at least n is the published a(n) (the "
                  "riders A229626 a(1) = a(2), A229630 a(1) = a(2) = a(3), "
                  "A229902 a(1) = a(2) = a(3) among them), and no longer run "
                  "occurs there")


def _filters(fam):
    top = frontier(fam)
    return sorted({1, 2, 3, 4, 5, 6, 9, top, top + 1, top + 3})


def g2b_killed_set_three_ways():
    """K(q,n,F) by the residue walk, by sympy's nthroot_mod and by direct
    divisibility of the values, at every prime under 120 and a spread of
    filters; the proved bound holds; K(q,n) grows with n."""
    checked = 0
    biggest = (0, 0, 0)
    for fam in FAMILIES:
        prev = {}
        for n in _filters(fam):
            for q in primerange(2, 120):
                walk = set(forbidden_k_residues(q, n, fam))
                alg = killed_algebraic(q, n, fam)
                if walk != alg or w_count(q, n, fam) != len(walk):
                    return False, (f"G2b FAIL: K({q},{n},{fam}) differs between "
                                   f"the walk {sorted(walk)} and nthroot_mod "
                                   f"{sorted(alg)}")
                for r in range(q):
                    x = K_FLOOR * q * 10 ** 6 + r
                    direct = any(v % q == 0 for v in values(fam, x, n))
                    if direct != (r in walk):
                        return False, (f"G2b FAIL: K({q},{n},{fam}) disagrees "
                                       f"with divisibility at x = {x}")
                if len(walk) > w_bound(q, n, fam) or len(walk) > maxkills(fam, n):
                    return False, (f"G2b FAIL: w({q},{n},{fam}) = {len(walk)} "
                                   f"passes the proved bound {w_bound(q, n, fam)}")
                prior = [m for m in prev if m < n]
                if prior and not prev[max(prior)].get(q, set()) <= walk:
                    return False, f"G2b FAIL: K({q},{n},{fam}) lost a residue"
                prev.setdefault(n, {})[q] = walk
                biggest = max(biggest, (len(walk), q, n))
                checked += 1
    return True, (f"G2b ok: K(q,n,F) three ways -- residue walk, sympy's "
                  f"nthroot_mod over k = 1..n, and direct divisibility of the "
                  f"values -- agree at all {checked} (q < 120, n, F), each "
                  f"inside its proved bound (sum of gcd(k, q - 1), plus the "
                  f"form q on A229627; none where q divides the multiplier), "
                  f"and K(q,n) is a subset of K(q,n+1); the most a prime under "
                  f"120 kills is {biggest[0]} residues (q = {biggest[1]}, n = "
                  f"{biggest[2]}) -- several per form, not one")


def g2c_admissible_and_forced():
    """Every filter to n = 30 is admissible (w < q at every prime under
    400); the forced primes are exactly the ones the module docstring
    names, from the index it names, with the classes it names."""
    rows = []
    for fam in FAMILIES:
        for n in range(1, 31):
            for q in primerange(2, 400):
                if w(q, n, fam) >= q:
                    return False, (f"G2c FAIL: {fam} n={n}: q={q} kills every "
                                   f"residue")
            want = [(q, r) for q, r, frm in _WANT_FORCED[fam] if n >= frm]
            got = [(q, forced_residue(q, n, fam)) for q in forced_primes(fam, n)]
            if got != want:
                return False, (f"G2c FAIL: {fam} forces {got} at n = {n}, "
                               f"expected {want}")
        ok, q = admissible(fam, 30)
        if not ok:
            return False, f"G2c FAIL: {fam} is not admissible at n = 30 ({q})"
        rows.append(f"{fam} " + (", ".join(f"{r} (mod {q}) from n = {frm}"
                                           for q, r, frm in _WANT_FORCED[fam])
                                 or "nothing forced"))
    return True, ("G2c ok: every filter to n = 30 is admissible at every prime "
                  "under 400, and the forced classes are exactly: " +
                  "; ".join(rows))


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
