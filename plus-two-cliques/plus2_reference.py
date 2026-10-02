"""The oracle for the +2 product cliques -- slow, obviously correct, sympy only.

    a(n) = least integer > a(n-1) such that  a(n)*a(i) + 2  is prime for EVERY
           earlier term a(i)

Join two integers when their product plus TWO is prime.  Each sequence here
is the GREEDY CLIQUE of that graph from its first term: the lexicographically
first infinite set in which every pair is joined.  Two OEIS entries hunt it,
and their names are word for word the same but for the start:

    A083518  "Beginning with 3, a(i)*a(j) + 2 is prime for all i, j, i != j."
             %O 1,1: a(1) = 3, and a(n)*a(i) + 2 for i = 1..n-1
    A083519  "Beginning with 1, a(i)*a(j) + 2 is prime for all i, j, i != j."
             %O 0,2: a(0) = 1, and a(n)*a(i) + 2 for i = 0..n-1

Both are Amarnath Murthy and Meenakshi Srikanth's (May 2003); A083518's
a(9)-a(13) are David Wasserman's (Nov 2004, with "Next term is > 266*10^9"),
A083519's were corrected and extended by Stefan Steinerberger (Jun 2007) and
its a(10) is Donovan Johnson's (Nov 2008).  It is product-cliques' clique
(a(n)*a(i) + 1, A034881) with the constant one changed to two.

THE OFFSET IS THE TRAP OF THIS PROJECT.  A083519 starts at INDEX 0, so its
published list is a(0..10) and its open term is a(11), while A083518 starts
at 1.  Every index here -- KNOWN's keys, the filter n, a run length, the
evidence's oeis_terms -- is the OEIS index by the entry's own %O line, never
a position in a list.  The entry's own %e line counts the other way ("a(4) =
9"; by %O and %S, 9 is a(3)), which is exactly the slip this gate battery
exists to refuse: G1c rebuilds every index from the %S and %O lines stored
below, verbatim.

THERE IS NO SELF CONDITION.  The name says "i != j", and the data agree:
5 = A083518's a(2) has 5^2 + 2 = 27.  So the conditions at index n are the
products with every earlier term and nothing else (unlike product-cliques'
A219761, whose a(n)^2 + 1 was a form of its own):

    forms(F, n) = [ a(off)*x + 2, a(off+1)*x + 2, ..., a(n-1)*x + 2 ]

with off the entry's offset.  A form is a triple (a, b, e) meaning a*x^e + b,
kept from product-cliques so that the engines read their forms the same way;
here every one is (a(i), 2, 1).  As there, THE FORM LIST IS STATE: the filter
for a(n+1) does not exist until a(n) does, the engine is rebuilt at every
find, and an error in one term would poison every later one -- so a find is
never taken from the engine: it is re-derived by this file, from the bare
definition, against the whole prefix.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Facts PROVED or CHECKED here rather than assumed, because both engines and
the odds model are built on them.

  THE KILLED SET.  For a prime q and a form a*x + 2,
  q | a*x + 2  <=>  x == -2 * a^-1 (mod q) when q does not divide a, and
  never when it does (the form is then == 2, which no odd q divides, and
  q = 2 divides no term: every term is odd).  So each earlier term kills
  exactly one residue, -2*a(i)^-1, or none.

      K(q,n,F) = U over forms of { x mod q : a*x + 2 == 0 (mod q) }

  and the engines sieve x against K(q,n,F) and nothing else.  w(q,n,F) is
  its size.  K(q,n) is a SUBSET of K(q,n+1): a new term adds one form and
  removes none.

  ADMISSIBILITY IS A THEOREM, AND THE CLASS IS 3 (mod 6).  At x == 0 every
  value is == 2: residue 0 survives every ODD prime at every index.  At
  q = 2 a*x + 2 == x (every term is odd), so x must be ODD -- and residue 1
  survives 2 for the same reason.  So no finite set of primes can empty the
  line.  Three is forced from A083518's a(4) and A083519's a(3): modulo 3,
  -2 == 1 and a^-1 == a, so a term == 1 kills x == 1 and a term == 2 kills
  x == 2, and A083518's 5, 7 (A083519's 1, 5) are one of each.  The class is
  x == 3 (mod 6), not product-cliques' 0, and every published term from
  those indices is in it.  G2c checks all of it.

  FIVE IS NOT FORCED, AND THE %C LINES SAY WHICH CLASSES IT KEEPS.  A083518
  keeps x == 0, 2, 3 (mod 5) from a(4) on (its terms' last digits 3, 5, 7,
  Pontus von Broemssen's %C), A083519 keeps 0 and 4 from a(4) on (last digit
  5 or 9, his %C on that entry), and no later term can move either set: a
  term in a kept class kills a class that is already dead.  G2c checks it.

  NO PRIME PAST 3 IS EVER FORCED.  r -> -2*r^-1 is an involution of the
  nonzero residues mod q, a term a(i) kills the image of its own residue,
  and two terms whose residues it swaps have a(i)*a(j) + 2 == 0 (mod q) --
  which a prime value allows only by BEING q (3*5 + 2 = 17, 1*3 + 2 = 5, ...,
  all among the first few terms).  A term may sit on a FIXED point of the
  involution (a(i)^2 == -2 mod q) because there is no self condition, and
  then kills its own residue; there are at most two.  So outside the
  exceptional pairs |K| <= (q - 1 - f)/2 + f <= (q + 1)/2, far from the q - 1
  that forcing needs, and a prime q can only be forced at all once more than
  q - 2 terms exist.  G2d checks the bound, its exceptions and "never forced"
  at every index that exists; nothing in the engines depends on it (the
  forced unit is DERIVED per filter), but it is why the class never moves.

  THE EXCEPTION ZONE.  "q divides the value, so the value is composite"
  needs the value to EXCEED q.  The smallest value at every index is
  a(off)*x + 2: 3x + 2 in A083518 and x + 2 in A083519, so a sieve to q2 is
  valid from x > q2; the engines refuse to run below that (k_floor), and the
  oracle covers the prefix by brute force.  The early terms live there.

THE RUN of an x at filter n, in INDEX units so that it reads like every other
ladder here: off + the number of leading forms a(off)*x + 2, a(off+1)*x + 2,
... that are prime.  A run of r says "x is compatible with every term before
index r" -- it could stand as a(r) if it were the least such.  A full run is
n; a run of n - 1 is ONE condition short of the open term.  It cannot pass n:
the form that would decide n + 1 is a(n)*x + 2, and a(n) does not exist until
this x is it.  (A083519's runs start at 0: a run of 0 means x + 2, its
product with a(0) = 1, is composite.)

Gates in this file: G1 (every published term list is a clique under the
bare definition, strictly increasing, with no self condition, and
regenerates greedily from its first term as far as brute force reaches),
G1b (this project's own finds continue their clique), G1c (every index is
the OEIS index: KNOWN rebuilt from the %S and %O lines), G2 (the killed set
three ways), G2c (admissibility, the forced class 3 (mod 6) and the mod-5
classes the %C lines state, at every filter that exists), G2d (no prime past
3 kills more than (q + 1)/2 residues, so none is ever forced).
"""

from functools import lru_cache as _lru_cache

from sympy import isprime, primerange

# ---------------------------------------------------------------- families

# `start`      the first term, a(off).
# `offset`     the entry's %O offset: the OEIS index of `start`.
# `extra`      forms a family imposes beyond the products (a, b, e): none
#              here -- the names say i != j, so there is no self condition.
# `forms`      the condition, in the OEIS name's own letters.  NEITHER name
#              gives the term a letter of its own ("a(i)*a(j) + 2 is prime for
#              all i, j, i != j"), so the evidence files carry it under a(n)
#              -- A083519's own %C writes a(n) -- and the condition is written
#              with the partner as a(i), as the name writes it (CONVENTIONS.md
#              "Naming in an evidence file").
# `name`, `data`, `offset_line`, `revision`: the %N, %S (with %T), %O and %I
#              lines VERBATIM from the OEIS export of 2026-10-01, which G1c
#              rebuilds every index from.
# `also`       the entries settled for free.  None: no OEIS entry is an
#              affine map of either (checked against the export of
#              2026-10-01).
FAMILIES = {
    "A083518": {"start": 3, "offset": 1, "extra": (),
                "forms": "a(n)*a(i) + 2, i = 1..n-1",
                "name": "Beginning with 3, a(i)*a(j) + 2 is prime for all "
                        "i, j, i != j.",
                "data": "3,5,7,27,45,495,3615,16695,533445,832305,122789427,"
                        "8705408757,77597861913",
                "offset_line": "1,1",
                "revision": "#15 Feb 02 2026 12:48:21",
                "keywords": "nonn,more",
                "author": "Amarnath Murthy and Meenakshi Srikanth, May 05 2003",
                "frontier_by": "David Wasserman, Nov 22 2004",
                # the entry's %C "Next term is > 266*10^9" (Wasserman, Nov 22
                # 2004): a searched bound on a(14).  The campaign does not
                # rely on it -- it sweeps from a(13) + 1 and re-establishes it
                "bound": (14, 266 * 10 ** 9),
                "also": ()},
    "A083519": {"start": 1, "offset": 0, "extra": (),
                "forms": "a(n)*a(i) + 2, i = 0..n-1",
                "name": "Beginning with 1, a(i)*a(j) + 2 is prime for all "
                        "i, j, i != j.",
                "data": "1,3,5,9,129,1179,21105,96525,419925,13690959,"
                        "8403613179",
                "offset_line": "0,2",
                "revision": "#24 Oct 13 2023 10:02:07",
                "keywords": "hard,more,nonn",
                "author": "Amarnath Murthy and Meenakshi Srikanth, May 05 2003",
                "frontier_by": "Donovan Johnson, Nov 11 2008",
                "bound": None,
                "also": ()},
}

# The letter the evidence files carry the term under (rule 5i).
TERM = "a(n)"

# No derived entry rides on either family, so no alias opens one.
ALIASES = {}


def _published(fam):
    """{OEIS index: term}, from the %S data and the %O offset, verbatim."""
    f = FAMILIES[fam]
    off = int(f["offset_line"].split(",")[0])
    return {off + i: int(v) for i, v in enumerate(f["data"].split(","))}


# The published terms, as published, keyed by the OEIS INDEX (%O) -- a(1..13)
# for A083518 and a(0..10) for A083519.
KNOWN = {fam: _published(fam) for fam in FAMILIES}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against and
# a fresh campaign starts from; these are the project's own claim, which the
# campaign carries in its checkpoint (`found`).  G1b re-checks whatever lands
# here from the bare definition, against the whole prefix.
FOUND = {fam: {} for fam in FAMILIES}

# Terms a RUNNING campaign has found and not yet published into FOUND.  The
# form list at index n needs a(off..n-1), so the launcher registers each find
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
                       f"{', '.join(sorted(FAMILIES))}")
    return fam


def offset(fam):
    """The OEIS index of the family's first term (its %O offset)."""
    return int(FAMILIES[family(fam)]["offset"])


def extra(fam):
    """The family's extra forms, as (a, b, e): none here (i != j)."""
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
        if n <= offset(fam) or term(fam, n - 1, missing=None) is None:
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
    """The largest n with a(off..n) all known."""
    fam = family(fam)
    n = offset(fam) - 1
    while term(fam, n + 1, missing=None) is not None:
        n += 1
    return n


def terms(fam, n):
    """[a(off), ..., a(n-1)]: the prefix the conditions at index n are built
    from.  Raises if any of it is unknown."""
    return [term(fam, i) for i in range(offset(fam), int(n))]


def forms(fam, n):
    """The conditions on x at index n, as (a, b, e) with a*x^e + b prime:
    a(i)*x + 2 for i = off..n-1, in order."""
    return list(extra(fam)) + [(t, 2, 1) for t in terms(fam, n)]


def nforms(fam, n):
    """How many conditions index n imposes: one per earlier term."""
    fam = family(fam)
    return len(extra(fam)) + max(0, int(n) - offset(fam))


def maxkills(fam, n):
    """The most residues one prime can kill at index n: one per form (every
    form has degree 1).  The number the engines' per-prime residue lists are
    sized from; it needs no term, so an engine asked for an index past the
    prefix is refused by its size before it is refused for the missing
    term."""
    return nforms(fam, n)


def value(f, x):
    """The value of form f = (a, b, e) at x."""
    a, b, e = f
    return a * int(x) ** e + b


def values(fam, x, n):
    """Every value the conditions at index n form at x, in form order."""
    return [value(f, x) for f in forms(fam, n)]


def run_length(fam, x, n, cap=None):
    """The run of x at index n, in INDEX units (module docstring): off + the
    number of leading forms a(off)*x + 2, a(off+1)*x + 2, ... that are prime,
    capped at `cap` (default n).  Full is n."""
    fam = family(fam)
    x = int(x)
    cap = int(n) if cap is None else min(int(cap), int(n))
    r = offset(fam)
    for t in terms(fam, n):
        if r >= cap or not isprime(t * x + 2):
            break
        r += 1
    return r


def is_term(fam, x, n):
    """x satisfies every condition of index n and exceeds a(n-1).  NOT the
    least-claim: that is a sweep's to make."""
    fam, x, n = family(fam), int(x), int(n)
    if n > offset(fam) and x <= term(fam, n - 1):
        return False
    return run_length(fam, x, n) == n


def forbidden_k_residues(q, n, fam):
    """The residues of x mod q at which some condition of index n is
    divisible by q -- by walking every residue and testing divisibility."""
    fs = forms(fam, n)
    return [r for r in range(q)
            if any((a * pow(r, e, q) + b) % q == 0 for a, b, e in fs)]


def w(q, n, fam):
    """|K(q,n,F)|, from the walk."""
    return len(forbidden_k_residues(q, n, fam))


@_lru_cache(maxsize=None)
def _roots(a, b, e, q):
    """The roots of a*x^e + b mod q, the algebraic way: -b*a^-1 for e = 1,
    none when q | a.  Only linear forms exist here."""
    a %= q
    if e != 1:
        raise ValueError(f"forms of degree {e} do not occur in this project")
    if a == 0:
        return ()
    return ((-b * pow(a, -1, q)) % q,)


def killed_algebraic(q, n, fam):
    """K(q,n,F) the algebraic way: the union of each form's root."""
    out = set()
    for a, b, e in forms(fam, n):
        out.update(_roots(a % q, b, e, q))
    return out


def w_count(q, n, fam):
    """|K(q,n,F)| the algebraic way (killed_algebraic).  G2 proves it equal
    to the walk and to direct divisibility."""
    return len(killed_algebraic(q, n, fam))


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
    A THEOREM here (module docstring: x == 0 survives every odd prime, x == 1
    survives 2), checked anyway -- only q <= maxkills can be covered, so the
    check is finite."""
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
    """The least x > lo (default a(n-1)) with a full run at index n, by the
    bare definition; None if there is none below hi."""
    fam, n = family(fam), int(n)
    x = (term(fam, n - 1) if lo is None else int(lo)) + 1
    while hi is None or x < hi:
        if run_length(fam, x, n) == n:
            return x
        x += 1
    return None


def forced_from(fam):
    """The first index at which 3 is forced (and the class is 3 mod 6):
    A083518's a(4), A083519's a(3) -- the module docstring."""
    fam = family(fam)
    return {"A083518": 4, "A083519": 3}[fam]


# The classes mod 5 each entry's %C line names, as the filter keeps them from
# index MOD5_FROM on: A083518's "10*k+3, 10*k+5, or 10*k+7" is x == 3, 0, 2
# (mod 5) with x odd; A083519's "the last digit of a(n) is 5 or 9" is 0, 4.
MOD5_KEPT = {"A083518": (0, 2, 3), "A083519": (0, 4)}
MOD5_FROM = {"A083518": 4, "A083519": 4}
# ... and the terms each %C line is a statement about: every term of A083518
# ("All terms"), and A083519's "For n >= 2".
MOD10_DIGITS = {"A083518": ((3, 5, 7), 1), "A083519": ((5, 9), 2)}


# --------------------------------- gates -----------------------------------

REGEN_BELOW = 10 ** 6         # how far G1 regenerates each clique by brute force


def g1_knowns_reproduce():
    """Every published list is a clique under the bare definition, strictly
    increasing, starts where its name says, needs no self condition, and the
    greedy rule regenerates it from its first term as far as brute force
    reaches -- which pins the DEFINITION rather than quoting it."""
    parts = []
    for fam in FAMILIES:
        off = offset(fam)
        idx = sorted(KNOWN[fam])
        t = [KNOWN[fam][i] for i in idx]
        if idx != list(range(off, off + len(t))) or \
                t[0] != FAMILIES[fam]["start"] or sorted(set(t)) != t:
            return False, f"G1 FAIL: {fam} does not start or increase as published"
        for j in range(len(t)):
            for i in range(j):
                if not isprime(t[i] * t[j] + 2):
                    return False, (f"G1 FAIL: {fam} a({off + i})*a({off + j}) "
                                   f"+ 2 is composite")
        regen = 1
        while regen < len(t) and t[regen] < REGEN_BELOW:
            got = first_x(fam, off + regen, hi=REGEN_BELOW)
            if got != t[regen]:
                return False, (f"G1 FAIL: the greedy rule gives {fam} "
                               f"a({off + regen}) = {got}, published "
                               f"{t[regen]}")
            regen += 1
        parts.append(f"{fam} a({off})-a({off + len(t) - 1}) ({regen} "
                     f"regenerated)")
    # NO SELF CONDITION: a published term whose square plus two is composite
    # (A083518's a(2) = 5, 5^2 + 2 = 27), so "i != j" is meant
    if KNOWN["A083518"][2] != 5 or isprime(5 ** 2 + 2):
        return False, "G1 FAIL: the no-self-condition witness moved"
    selfs = sum(1 for fam in FAMILIES for x in KNOWN[fam].values()
                if not isprime(x * x + 2))
    return True, ("G1 ok: " + "; ".join(parts) + " -- every pairwise product "
                  "plus two is prime, and the greedy rule rebuilds each list "
                  f"from its first term below {REGEN_BELOW:,}; there is no "
                  f"self condition ({selfs} published terms have a(n)^2 + 2 "
                  f"composite, A083518's a(2) = 5 among them)")


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


def g1c_every_index_is_the_oeis_index():
    """KNOWN is the %S list keyed by the %O offset, and nothing else: the
    index a person reads (oeis_terms, the evidence file's name, every log
    line) is the OEIS index, never a position.  A083519 is offset 0, and its
    own %e line counts from 1 ("a(4) = 9"): 9 is a(3) here, a term at index 3
    and not at 4, and the open term is a(11)."""
    rows = []
    for fam, f in FAMILIES.items():
        off = int(f["offset_line"].split(",")[0])
        data = [int(v) for v in f["data"].split(",")]
        want = {off + i: v for i, v in enumerate(data)}
        if off != f["offset"] or KNOWN[fam] != want:
            return False, (f"G1c FAIL: {fam}'s KNOWN is not its %S list keyed "
                           f"by %O = {f['offset_line']}")
        if min(KNOWN[fam]) != off or KNOWN[fam][off] != f["start"]:
            return False, f"G1c FAIL: {fam}'s first term is not a({off})"
        if frontier(fam) != off + len(data) - 1:
            return False, (f"G1c FAIL: {fam}'s frontier is a({frontier(fam)}), "
                           f"not a({off + len(data) - 1})")
        if [term(fam, i) for i in range(off, frontier(fam) + 1)] != data:
            return False, f"G1c FAIL: {fam}'s terms do not read back as %S"
        if nforms(fam, frontier(fam) + 1) != len(data):
            return False, (f"G1c FAIL: {fam}'s open index does not have one "
                           f"condition per published term")
        rows.append(f"{fam} %O {f['offset_line']}: a({off})..a({off + len(data) - 1}), "
                    f"open a({off + len(data)}) with {len(data)} conditions")
    # A083519's %e says "a(4) = 9"; by %O and %S it is a(3)
    if KNOWN["A083519"].get(3) != 9 or not is_term("A083519", 9, 3) or \
            is_term("A083519", 9, 4) or KNOWN["A083519"].get(4) != 129:
        return False, "G1c FAIL: A083519's 9 is not a(3) by its %O line"
    return True, ("G1c ok: " + "; ".join(rows) + " -- every index is the OEIS "
                  "index by the entry's own %O line; A083519's 9 is a(3) (its "
                  "%e line's 'a(4) = 9' counts from 1) and its open term is "
                  "a(11)")


def g2_killed_set_three_ways():
    """K(q,n,F) by the residue walk, by the algebraic construction, and by
    direct divisibility of the values -- at every prime under 90 and every
    index that exists; and K(q,n) is a subset of K(q,n+1)."""
    checked = 0
    for fam in FAMILIES:
        prev = {}
        for n in range(offset(fam) + 1, frontier(fam) + 2):
            for q in primerange(2, 90):
                walk = set(forbidden_k_residues(q, n, fam))
                alg = killed_algebraic(q, n, fam)
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
    return True, (f"G2 ok: K(q,n,F) three ways -- residue walk, the union of "
                  f"each form's root (-2*a(i)^-1, none where q divides "
                  f"a(i)), and direct divisibility -- agree at all {checked} "
                  f"(q < 90, n, F), and K(q,n) is a subset of K(q,n+1) "
                  f"throughout")


def g2c_admissible_and_forced():
    """Every filter that exists is admissible; residue 0 survives every ODD
    prime and is killed by 2; the forced class is x == 3 (mod 6) -- 2 from
    the first condition, 3 from A083518's a(4) and A083519's a(3), nothing
    else -- and every published term from there is in it; and 5 keeps the
    classes the %C lines name."""
    rows = []
    for fam in FAMILIES:
        off, top, f3 = offset(fam), frontier(fam), forced_from(fam)
        for n in range(off + 1, top + 2):
            ok, q = admissible(fam, n)
            if not ok:
                return False, (f"G2c FAIL: every class mod {q} is killed at "
                               f"index {n} of {fam}")
            if forbidden_k_residues(2, n, fam) != [0]:
                return False, (f"G2c FAIL: at index {n} of {fam}, 2 does not "
                               f"kill exactly the even x")
            for q in primerange(3, 64):
                if 0 in forbidden_k_residues(q, n, fam):
                    return False, (f"G2c FAIL: residue 0 is killed by {q} at "
                                   f"index {n} of {fam} -- a form is not "
                                   f"a*x + 2")
            forced = forced_primes(fam, n)
            want = [2] if n < f3 else [2, 3]
            if forced != want:
                return False, (f"G2c FAIL: {fam} forces {forced} at index {n}, "
                               f"expected {want}")
            if n >= f3 and forced_residue(3, n, fam) != 0:
                return False, f"G2c FAIL: {fam} keeps x != 0 (mod 3) at {n}"
            if n >= MOD5_FROM[fam]:
                kept = tuple(r for r in range(5)
                             if r not in forbidden_k_residues(5, n, fam))
                if kept != MOD5_KEPT[fam]:
                    return False, (f"G2c FAIL: {fam} keeps {kept} (mod 5) at "
                                   f"index {n}, the %C line says "
                                   f"{MOD5_KEPT[fam]}")
        for i in range(f3, top + 1):
            if term(fam, i) % 6 != 3:
                return False, (f"G2c FAIL: {fam} a({i}) = {term(fam, i)} is "
                               f"not == 3 (mod 6)")
        digits, d_from = MOD10_DIGITS[fam]
        for i in range(d_from, top + 1):
            if term(fam, i) % 10 not in digits:
                return False, (f"G2c FAIL: {fam} a({i}) = {term(fam, i)} breaks "
                               f"its %C line's last digits {digits}")
        rows.append(f"{fam} n = {off + 1}..{top + 1}, 3 forced from n = {f3}, "
                    f"mod 5 keeps {MOD5_KEPT[fam]} from n = {MOD5_FROM[fam]}")
    return True, ("G2c ok: every filter is admissible, residue 0 survives "
                  "every odd prime under 64 and 2 kills exactly the even x, "
                  "the forced primes are 2 and then 2, 3 and no others ("
                  + "; ".join(rows) + "), every published term from there is "
                  "== 3 (mod 6), and the last digits are the ones the %C "
                  "lines state (3, 5, 7 in A083518; 5, 9 from a(2) in "
                  "A083519)")


def g2d_no_prime_past_3_is_forced():
    """For every prime 5 <= q < 400 at every index that exists: two terms
    whose residues r -> -2*r^-1 swaps have a(i)*a(j) + 2 EQUAL to q (a prime
    value can be divisible by q no other way); |K(q,n,F)| <= (q + 1)/2 plus
    one for each such pair; and q is never forced (w <= q - 2)."""
    worst, pairs = (0.0, None), set()
    for fam in FAMILIES:
        off = offset(fam)
        for n in range(off + 1, frontier(fam) + 2):
            ts = terms(fam, n)
            for q in primerange(5, 400):
                k = w_count(q, n, fam)
                if k > q - 2:
                    return False, (f"G2d FAIL: {fam} n = {n}: q = {q} kills "
                                   f"{k} of {q} residues -- a prime past 3 is "
                                   f"forced")
                swapped = 0
                for j in range(len(ts)):
                    for i in range(j):
                        v = ts[i] * ts[j] + 2
                        if v % q == 0:
                            if v != q:
                                return False, (f"G2d FAIL: {fam}: a({off + i})"
                                               f"*a({off + j}) + 2 = {v} is "
                                               f"divisible by {q} and is not "
                                               f"{q}")
                            swapped += 1
                            pairs.add(f"{fam} a({off + i})*a({off + j}) + 2 "
                                      f"= {q}")
                if k > (q + 1) // 2 + swapped:
                    return False, (f"G2d FAIL: {fam} n = {n}: q = {q} kills "
                                   f"{k} residues, over (q + 1)/2 + {swapped}")
                frac = k / (q - 1)
                if frac > worst[0]:
                    worst = (frac, f"{fam} n = {n}, q = {q}: {k} of {q - 1} "
                                   f"nonzero residues killed")
    return True, (f"G2d ok: at every index of either family and every prime "
                  f"5 <= q < 400 the killed set is at most (q + 1)/2 plus one "
                  f"for each pair of terms whose product plus two IS q "
                  f"({len(pairs)} pairs, e.g. "
                  f"{', '.join(sorted(pairs)[:4])}), and no such q is forced "
                  f"-- so only 2 and 3 ever are (tightest: {worst[1]})")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce,
         g1c_every_index_is_the_oeis_index, g2_killed_set_three_ways,
         g2c_admissible_and_forced, g2d_no_prime_past_3_is_forced]


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
