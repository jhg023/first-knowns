"""The oracle for the product cliques -- slow, obviously correct, sympy only.

    a(n) = least x > a(n-1) such that  x * a(i) + 1  is prime for EVERY i < n
           (and, in A219761, x^2 + 1 as well)

Join two integers when their product plus one is prime.  Each sequence here
is the GREEDY CLIQUE of that graph from a(1) = 1: the lexicographically first
infinite set in which every pair is joined.  Two OEIS entries hunt it:

    A034881   a(n)*a(i) + 1, i = 1..n-1      Erich Friedman; Carmody; Reble 2012
    A219761   a(n)*a(n-i) + 1, i = 0..n-1    Sloane 2012; R. G. Wilson v 2012

The second lets i reach 0, which is the SELF-product a(n)*a(n) + 1: the clique
where every element also joins itself.  It is the multiplicative twin of the
six additive cliques in clique-ladders (a(n) + a(i) + 1 prime), and both
entries cite that family (A093483).

THE SHAPE.  At index n the conditions on x are n - 1 PRODUCT forms whose
multipliers are the sequence's own earlier terms, plus the family's extra
form:

    forms(F, n) = [ extra(F) ... ,  a(1)*x + 1,  ...,  a(n-1)*x + 1 ]

A form here is a triple (a, b, e) meaning a*x^e + b: every product form is
(a(i), 1, 1) and A219761's extra form is (1, 1, 2), x^2 + 1.  So one form in
this project is not linear, and that is the only thing the engines had to
learn: a prime q kills the ROOTS of each form mod q, one for a product form
and zero or two for x^2 + 1.  As in clique-ladders, THE FORM LIST IS STATE:
the filter for a(n+1) does not exist until a(n) does, the engine is rebuilt
at every find, and an error in one term would poison every later one -- so a
find is never taken from the engine: it is re-derived by this file, from the
bare definition, against the whole prefix.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW,
and sympy's sqrt_mod) and the definition as written.

Facts PROVED or CHECKED here rather than assumed, because both engines and
the odds model are built on them.

  THE KILLED SET.  For a prime q and a form a*x^e + b,
  q | a*x^e + b  <=>  x^e == -b * a^-1 (mod q) when q does not divide a, and
  never when it does (the form is then == b = 1).  So for a product form the
  one killed residue is -a(i)^-1, none when q | a(i); for x^2 + 1 the killed
  residues are the square roots of -1 mod q -- two when q == 1 (mod 4), one
  (x == 1) at q = 2, none otherwise.

      K(q,n,F) = U over forms of { x mod q : a*x^e + b == 0 (mod q) }

  and the engines sieve x against K(q,n,F) and nothing else.  w(q,n,F) is
  its size.  K(q,n) is a SUBSET of K(q,n+1): a new term adds one form and
  removes none.

  ADMISSIBILITY IS A THEOREM HERE (unlike clique-ladders).  Every form is
  a*x^e + 1, so at x == 0 (mod q) every value is == 1: residue 0 survives
  EVERY prime at EVERY index, and no finite set of primes can empty the line.
  G2c checks it anyway.

  ONLY 2 AND 3 ARE FORCED, and x == 0 (mod 6) from index 3.  At q = 2,
  a(1) = 1 kills x == 1; at q = 3, a(1) = 1 and a(2) = 2 kill x == 2 and
  x == 1.  For q >= 5 the killed set stays near HALF of the residues, far
  from q - 1: the map r -> -r^-1 is an involution of the nonzero residues, a
  product form kills -a(i)^-1, and two terms whose residues it swaps have
  a(i)*a(j) + 1 == 0 (mod q) -- which a prime value allows only by BEING q.
  That happens among the first few terms (1*6 + 1 = 7, 2*6 + 1 = 13) and
  nowhere a multiplier is large, so outside those pairs the multipliers hold
  at most one residue per orbit and |K| <= (q + 1)/2.  G2d checks the bound,
  its exceptions and "never forced" at every index that exists; nothing in
  the engines depends on it (the forced unit is DERIVED per filter), but it
  is why the class never moves.

  THE EXCEPTION ZONE.  "q divides the value, so the value is composite"
  needs the value to EXCEED q.  The smallest value at every index from 2 is
  a(1)*x + 1 = x + 1 (and x^2 + 1 > x), so a sieve to q2 is valid from
  x > q2; the engines refuse to run below that (k_floor), and the oracle
  covers the prefix by brute force.  The early terms live there.

THE RUN of an x at filter n, in INDEX units so that it reads like every other
ladder here: 0 if the extra form fails, else 1 + the number of leading product
forms a(1)*x + 1, a(2)*x + 1, ... that are prime.  A run of r says "x is
compatible with the first r - 1 terms" -- it could stand as a(r) if it were
the least such.  A full run is n; a run of n - 1 is ONE condition short of
the open term.  It cannot pass n: the form that would decide n + 1 is
a(n)*x + 1, and a(n) does not exist until this x is it.

Gates in this file: G1 (every published term list is a clique under the
bare definition, strictly increasing, and regenerates greedily from a(1) as
far as brute force reaches), G1b (this project's own finds continue their
clique), G2 (the killed set three ways), G2c (admissibility and the forced
class at every filter that exists), G2d (no prime past 3 kills more than
(q + 1)/2 residues, so none is ever forced).
"""

from functools import lru_cache as _lru_cache

from sympy import isprime, primerange
from sympy.ntheory import sqrt_mod as _sqrt_mod

# ---------------------------------------------------------------- families

# `start`      a(1).
# `extra`      the family's extra forms (a, b, e): a*x^e + b must be prime too.
# `forms`      the condition, in the OEIS name's own wording.  NEITHER name
#              gives the term a letter ("smallest integer > a(n-1) such that
#              a(n)*a(i)+1 is prime"), so the evidence files carry it under
#              a(n) and the forms below are written in it (CONVENTIONS.md
#              "Naming in an evidence file"; A219761 writes the partner
#              a(n-i) and lets i reach 0, and that is kept).
# `also`       the entries settled for free.  None: no OEIS entry is an
#              affine map of either (checked against the export of
#              2026-09-29 -- A274694 is the prime-POWER variant, a different
#              sequence).
# Both entries were re-verified against the local OEIS export of 2026-09-29
# (%I stamps: A034881 #30, A219761 #23).
FAMILIES = {
    "A034881": {"start": 1, "extra": (),
                "forms": "a(n)*a(i) + 1, i = 1..n-1",
                "keywords": "nonn",
                "author": "Erich Friedman",
                "frontier_by": "Don Reble, Oct 15 2012",
                "bound": (16, 2 * 10 ** 16),      # the entry's "a(16) > 2*10^16"
                "also": ()},
    "A219761": {"start": 1, "extra": ((1, 1, 2),),
                "forms": "a(n)*a(n-i) + 1, i = 0..n-1 (so a(n)^2 + 1 too)",
                "keywords": "nonn,more",
                "author": "N. J. A. Sloane, Dec 01 2012",
                "frontier_by": "Robert G. Wilson v, Dec 04 2012",
                "bound": None,
                "also": ()},
}

# The letter the evidence files carry the term under (rule 5i).
TERM = "a(n)"

# No derived entry rides on either family, so no alias opens one.
ALIASES = {}

# The published terms, as published, indexed by the OEIS index n (offset 1).
KNOWN = {
    "A034881": [1, 2, 6, 18, 30, 270, 606, 123120, 888456, 23070450,
                238550160, 8282903640, 72789145650, 15681266370000,
                18216437241240],
    "A219761": [1, 2, 6, 156, 4260, 117306, 160650, 13937550, 32742516,
                3306719796, 7746764190],
}
KNOWN = {fam: {i + 1: v for i, v in enumerate(t)} for fam, t in KNOWN.items()}

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
                       f"{', '.join(sorted(FAMILIES))}")
    return fam


def extra(fam):
    """The family's extra forms, as (a, b, e): a*x^e + b must be prime."""
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
    """The conditions on x at index n, as (a, b, e) with a*x^e + b prime: the
    family's extra forms first, then a(i)*x + 1 for i = 1..n-1 in order."""
    return list(extra(fam)) + [(t, 1, 1) for t in terms(fam, n)]


def nforms(fam, n):
    """How many conditions index n imposes."""
    fam = family(fam)
    return len(extra(fam)) + max(0, int(n) - 1)


def maxkills(fam, n):
    """The most residues one prime can kill at index n: a form of degree e
    has at most e roots mod q, so the sum of the degrees.  A219761's x^2 + 1
    makes this one more than the form count -- the number the engines' per-
    prime residue lists are sized from.  Every product form has degree 1, so
    it needs no term: an engine asked for an index past the prefix is refused
    by its size before it is refused for the missing term."""
    return sum(e for _a, _b, e in extra(fam)) + max(0, int(n) - 1)


def value(f, x):
    """The value of form f = (a, b, e) at x."""
    a, b, e = f
    return a * int(x) ** e + b


def values(fam, x, n):
    """Every value the conditions at index n form at x, in form order."""
    return [value(f, x) for f in forms(fam, n)]


def run_length(fam, x, n, cap=None):
    """The run of x at index n, in INDEX units (module docstring): 0 if an
    extra form fails, else 1 + the number of leading product forms that are
    prime, capped at `cap` (default n).  Full is n."""
    fam = family(fam)
    x = int(x)
    cap = int(n) if cap is None else min(int(cap), int(n))
    if any(not isprime(value(f, x)) for f in extra(fam)):
        return 0
    r = 1
    for t in terms(fam, n):
        if r >= cap or not isprime(t * x + 1):
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
    return [r for r in range(q)
            if any((a * pow(r, e, q) + b) % q == 0 for a, b, e in fs)]


def w(q, n, fam):
    """|K(q,n,F)|, from the walk."""
    return len(forbidden_k_residues(q, n, fam))


@_lru_cache(maxsize=None)
def _roots(a, b, e, q):
    """The roots of a*x^e + b mod q, the algebraic way: -b*a^-1 for e = 1,
    sympy's modular square roots of -b*a^-1 for e = 2; none when q | a."""
    a %= q
    if a == 0:
        return ()
    c = (-b * pow(a, -1, q)) % q
    if e == 1:
        return (c,)
    if e == 2:
        return tuple(sorted(int(r) for r in (_sqrt_mod(c, q, all_roots=True)
                                             or [])))
    raise ValueError(f"forms of degree {e} are not supported")


def killed_algebraic(q, n, fam):
    """K(q,n,F) the algebraic way: the union of each form's roots."""
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
    A THEOREM here (module docstring: every form is 1 at x == 0), checked
    anyway -- only q <= maxkills can be covered, so the check is finite."""
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


# --------------------------------- gates -----------------------------------

REGEN_BELOW = 10 ** 6         # how far G1 regenerates each clique by brute force


def g1_knowns_reproduce():
    """Every published list is a clique under the bare definition, strictly
    increasing, and the greedy rule regenerates it from a(1) as far as brute
    force reaches -- which pins the DEFINITION (including the extra form and
    the start) rather than quoting it."""
    parts = []
    for fam in FAMILIES:
        t = [KNOWN[fam][i] for i in sorted(KNOWN[fam])]
        if t[0] != FAMILIES[fam]["start"] or sorted(set(t)) != t:
            return False, f"G1 FAIL: {fam} does not start or increase as published"
        for j, x in enumerate(t):
            for f in extra(fam):
                if not isprime(value(f, x)):
                    return False, (f"G1 FAIL: {fam} a({j + 1}) = {x} fails its "
                                   f"extra form {f}")
            for i in range(j):
                if not isprime(t[i] * x + 1):
                    return False, (f"G1 FAIL: {fam} a({i + 1})*a({j + 1}) + 1 "
                                   f"is composite")
        regen = 1
        while regen < len(t) and t[regen] < REGEN_BELOW:
            got = first_x(fam, regen + 1, hi=REGEN_BELOW)
            if got != t[regen]:
                return False, (f"G1 FAIL: the greedy rule gives {fam} "
                               f"a({regen + 1}) = {got}, published {t[regen]}")
            regen += 1
        parts.append(f"{fam} a(1)-a({len(t)}) ({regen} regenerated)")
    # the two definitions part at a(4): 18 is A034881's, and 18^2 + 1 = 325
    # is what A219761's i = 0 condition refuses
    if KNOWN["A034881"][4] != 18 or isprime(18 ** 2 + 1) or \
            KNOWN["A219761"][4] != 156:
        return False, "G1 FAIL: the two families do not part at a(4) as published"
    return True, ("G1 ok: " + "; ".join(parts) + " -- every pairwise product "
                  "plus one is prime (and every self-product plus one in "
                  "A219761), and the greedy rule rebuilds each list from "
                  f"a(1) = 1 below {REGEN_BELOW:,}; the families part at "
                  f"a(4) = 18 / 156, because 18^2 + 1 = 325")


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
    checked, sq = 0, 0
    for fam in FAMILIES:
        prev = {}
        for n in range(2, frontier(fam) + 2):
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
                if extra(fam) and q % 4 == 1:
                    sq += 1
    return True, (f"G2 ok: K(q,n,F) three ways -- residue walk, the union of "
                  f"each form's roots (-a(i)^-1 for a product form, sympy's "
                  f"square roots of -1 for x^2 + 1), and direct divisibility "
                  f"-- agree at all {checked} (q < 90, n, F), {sq} of them "
                  f"with the quadratic form killing two residues, and K(q,n) "
                  f"is a subset of K(q,n+1) throughout")


def g2c_admissible_and_forced():
    """Every filter that exists is admissible (a theorem here: every form is
    1 at x == 0), and the forced class is x == 0 (mod 6) -- 2 and 3, nothing
    else -- on the latest published terms."""
    rows = []
    for fam in FAMILIES:
        top = frontier(fam)
        for n in range(2, top + 2):
            ok, q = admissible(fam, n)
            if not ok:
                return False, (f"G2c FAIL: every class mod {q} is killed at "
                               f"index {n} of {fam}")
            for q in primerange(2, 64):
                if 0 in forbidden_k_residues(q, n, fam):
                    return False, (f"G2c FAIL: residue 0 is killed by {q} at "
                                   f"index {n} of {fam} -- a form is not "
                                   f"a*x^e + 1")
            forced = forced_primes(fam, n)
            want = [2] if n == 2 else [2, 3]
            if forced != want:
                return False, (f"G2c FAIL: {fam} forces {forced} at index {n}, "
                               f"expected {want}")
        for i in range(3, top + 1):
            if term(fam, i) % 6:
                return False, (f"G2c FAIL: {fam} a({i}) = {term(fam, i)} is "
                               f"not == 0 (mod 6)")
        rows.append(f"{fam} n = 2..{top + 1}")
    return True, ("G2c ok: residue 0 survives every prime under 64 at every "
                  "filter (" + "; ".join(rows) + "), the forced primes are 2 "
                  "from n = 2 and 2, 3 from n = 3 and no others, and every "
                  "published term from a(3) is == 0 (mod 6)")


def g2d_no_prime_past_3_is_forced():
    """For every prime 5 <= q < 400 at every index that exists: two terms
    whose residues r -> -r^-1 swaps have a(i)*a(j) + 1 EQUAL to q (a prime
    value can be divisible by q no other way); |K(q,n,F)| <= (q + 1)/2 plus
    one for each such pair; and q is never forced (w <= q - 2)."""
    worst, pairs = (0.0, None), set()
    for fam in FAMILIES:
        for n in range(3, frontier(fam) + 2):
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
                        v = ts[i] * ts[j] + 1
                        if v % q == 0:
                            if v != q:
                                return False, (f"G2d FAIL: {fam}: a({i + 1})*"
                                               f"a({j + 1}) + 1 = {v} is "
                                               f"divisible by {q} and is not "
                                               f"{q}")
                            swapped += 1
                            pairs.add(f"a({i + 1})*a({j + 1}) + 1 = {q}")
                if k > (q + 1) // 2 + swapped:
                    return False, (f"G2d FAIL: {fam} n = {n}: q = {q} kills "
                                   f"{k} residues, over (q + 1)/2 + {swapped}")
                frac = k / (q - 1)
                if frac > worst[0]:
                    worst = (frac, f"{fam} n = {n}, q = {q}: {k} of {q - 1} "
                                   f"nonzero residues killed")
    return True, (f"G2d ok: at every index of either family and every prime "
                  f"5 <= q < 400 the killed set is at most (q + 1)/2 plus one "
                  f"for each pair of terms whose product plus one IS q ("
                  f"{', '.join(sorted(pairs))}), and no such q is forced -- "
                  f"so only 2 and 3 ever are (tightest: {worst[1]})")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce, g2_killed_set_three_ways,
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
