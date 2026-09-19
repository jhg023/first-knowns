"""The oracle for the lcm ladders -- slow, obviously correct, sympy only.

    A(F, n) = least N >= 1 such that (N + s*k)/k is prime for EVERY
              k = 1, 2, ..., n

Two families, one engine, four OEIS entries:

    A078502   (N - k)/k prime, k = 1..n     Pe 2003; a(13)/a(14) J. K. Andersen
    A074200   (m + k)/k prime, k = 1..n     Colin 2002; a(14) J. K. Andersen

and each find settles a second entry for free, because the two riders are
the same integer shifted by one (Sloane's own comments say so):

    A093554(n) = A078502(n) - 1     "least m with (m - k + 1)/k prime"
    A093553(n) = A074200(n) + 1     "least m with (m + k - 1)/k prime"

THE SUBSTITUTION.  (N + s*k)/k is an integer for k = 1..n exactly when
L | N, where L = L(n) = lcm(1, 2, ..., n).  So N = L*x, the k-th condition
reads

    N/k + s = (L/k)*x + s   is prime,

and the whole problem is the SAME linear ladder this repository has hunted
four times already -- one unknown x, a list of multipliers, a fixed sign --
with the multiplier list

    mults(n) = [ L(n)/1, L(n)/2, ..., L(n)/n ].

The multipliers are the same for both families; only the sign differs, so
the two families share every killed-set size, the whole survival curve and
one singular series (G2c).  The engines sweep x and the launcher reports
L(n)*x.

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy's isprime, i.e. BPSW)
and the definition as written.

Five facts are PROVED here rather than assumed, because both engines and
the odds model are built on them.

  THE KILLED SET.  Fix a prime q and a multiplier m = L/k.  If q | m the
  form m*x + s is congruent to s (mod q), and |s| = 1 < q, so that form is
  NEVER divisible by q: a rung whose multiplier q divides kills nothing.
  For q not dividing m,

      q | m*x + s   <=>   x == -s * m^-1  (mod q),

  so the residues of x that q kills are exactly

      K(q,n,F) = { -s * m^-1 mod q : m in mults(n), q does not divide m }

  and the engines sieve x against K(q,n,F) and nothing else.

  ITS SIZE, IN CLOSED FORM.  Inversion and negation are bijections of
  (Z/q)^*, so w(q,n) = |K(q,n,F)| is the number of DISTINCT nonzero
  residues the multipliers take mod q, and that has an exact answer:

      q > n :  every L/k is invertible mod q and L/k == L * k^-1, which is
               injective in k for k <= n < q, so   w(q,n) = n.
      q <= n:  let q^e be the largest power of q with q^e <= n.  Then
               q^e || L, so L/k is nonzero mod q exactly when q^e | k, i.e.
               k = q^e * j for j = 1 .. floor(n/q^e) -- and since
               q^(e+1) > n, that j range is 1..(<q), so the j are distinct
               and nonzero mod q and so are the L/k.  Hence

                   w(q,n) = floor(n / q^e).

  This is the whole difference from the linear ladders, and it is a large
  one: there w(q,n) = min(n, q-1) for EVERY q, so every small prime is a
  maximal killer; here the small primes are nearly blind (w(3,15) = 1,
  w(5,15) = 3, w(7,15) = 2) because L/k is divisible by q for all but a
  handful of k.  The wheel is ~2,400x weaker at n = 15 and the compensation
  is the singular series, which is ~1,500x larger.  Every engine constant
  in this project was re-swept for that regime; none was inherited.

  FORCED DIVISIBILITY.  When w(q,n) = q - 1 the multipliers cover every
  nonzero residue mod q and the only surviving x are x == 0 (mod q).
  q = 2 is forced at EVERY n (e = floor(log2 n) gives 1 <= n/2^e < 2, so
  w(2,n) = 1 = q - 1), which is the published observation that
  A078502(n) == 0 (mod 2L) for n > 4.  Above that the forcing is sporadic
  and NOT monotone in n: q = n + 1 is forced whenever n + 1 is prime
  (w = n = q - 1), so the unit is 2 at n = 15 and n = 17, 34 at n = 16 and
  114 at n = 18 (2 * 3 * 19: 19 by the n+1 rule, 3 because
  floor(18/9) = 2 = 3 - 1).  A campaign therefore changes wheel, unit and
  rate at EVERY filter, in both directions -- rule 5g's "price every
  opening" with no monotone shortcut available.

  ADMISSIBLE AT EVERY n, FOR BOTH SIGNS.  x == 0 (mod q) gives every value
  == s != 0 (mod q), so residue 0 is never killed and w(q,n) <= q - 1 for
  every prime q.  No fixed prime divisor at any n; by Dickson's conjecture
  there are infinitely many x for every n, so a(n) is defined for all n and
  a find CONFIRMS the guiding conjecture and can never refute it.

  THE EXCEPTION ZONE is real and small.  "q divides the value, so the value
  is composite" needs the value to EXCEED q.  The smallest value at filter
  n is (L/n)*x + s, so a sieve to q2 is only valid once (L/n)*x > q2; the
  engines refuse to run below that (k_floor), and the oracle covers the
  prefix by brute force.  The published small terms live there: A078502's
  a(4) = 12 has (12-3)/3 = 3, which IS the prime 3.

Gates in this file: G1 (the frozen knowns reproduce from the bare
definition, are monotone, are multiples of their L and of every forced
prime, and each frontier's wall is composite), G1b (this project's own
finds, once there are any), G2 (the small terms re-derived exhaustively),
G2b (the w(q,n) closed form equals direct divisibility, both signs, both
constructions), G2c (admissibility, sign-independence of w, the forcing
thresholds including the n+1 rule), G2d (the derived identities
A093554 = A078502 - 1 and A093553 = A074200 + 1 on every published term).
"""

from math import gcd

from sympy import isprime, primerange

# ---------------------------------------------------------------- families

# `sign`       the s in (L/k)*x + s.
# `first_n`    the OEIS offset: the first index the sequence has a term at.
# `also`       the entry settled for free, and by what shift.
# Every entry was re-verified against the local OEIS export of 2026-09-01
# (%I revision stamps A078502 #36, A074200 #24, A093553 #29, A093554 #20).
FAMILIES = {
    "A078502": {"sign": -1, "first_n": 1,
                "forms": "(N - k)/k = (L/k)*x - 1, k = 1..n", "term": "N",
                "keywords": "nonn,more",
                "author": "Joseph L. Pe, Jan 05 2003",
                "frontier_by": "Jens Kruse Andersen, Jan 10 2003",
                "also": (("A093554", -1),)},
    "A074200": {"sign": +1, "first_n": 1,
                "forms": "(m + k)/k = (L/k)*x + 1, k = 1..n", "term": "m",
                "keywords": "nonn,more",
                "author": "Jean-Christophe Colin, Sep 17 2002",
                "frontier_by": "Jens Kruse Andersen, Feb 15 2004",
                "also": (("A093553", +1),)},
}

# The rider spellings open the same campaign as the entry they shift.
ALIASES = {"A093554": "A078502", "A093553": "A074200"}

# The published terms, as published (in N), indexed by the OEIS index n.
KNOWN = {
    "A078502": {1: 3, 2: 6, 3: 12, 4: 12, 5: 174600, 6: 7224840,
                7: 10780560, 8: 10780560, 9: 1086338816640,
                10: 50060257410240, 11: 7720634052774720,
                12: 227457297898150320, 13: 7272877497848202240,
                14: 7272877497848202240},
    "A074200": {1: 1, 2: 2, 3: 12, 4: 12720, 5: 19440, 6: 5516280,
                7: 5516280, 8: 7321991040, 9: 363500177040,
                10: 2394196081200, 11: 3163427380990800,
                12: 22755817971366480, 13: 3788978012188649280,
                14: 2918756139031688155200},
}

# The DERIVED entries, as published, so their identities can be gated.
KNOWN_ALSO = {
    # A093554(n) = A078502(n) - 1: least m with (m - k + 1)/k prime, k = 1..n
    "A093554": {1: 2, 2: 5, 3: 11, 4: 11, 5: 174599, 6: 7224839,
                7: 10780559, 8: 10780559, 9: 1086338816639,
                10: 50060257410239, 11: 7720634052774719,
                12: 227457297898150319, 13: 7272877497848202239,
                14: 7272877497848202239},
    # A093553(n) = A074200(n) + 1: least m with (m + k - 1)/k prime, k = 1..n
    "A093553": {1: 2, 2: 3, 3: 13, 4: 12721, 5: 19441, 6: 5516281,
                7: 5516281, 8: 7321991041, 9: 363500177041,
                10: 2394196081201, 11: 3163427380990801,
                12: 22755817971366481, 13: 3788978012188649281,
                14: 2918756139031688155201},
}

# FOUND BY THIS PROJECT and not yet in the OEIS.  Kept APART from KNOWN on
# purpose: KNOWN is the literature, which the model is validated against and
# a fresh campaign starts from; these are the project's own claim, which the
# campaign carries in its checkpoint (`found`) and promotes its frontier
# from at runtime.  G1b re-checks whatever lands here from the bare
# definition.  Values are N, as published.
FOUND = {fam: {} for fam in FAMILIES}

# Neither entry carries a published bound of any kind -- no upper bound at
# any open n, and no searched-empty lower bound beyond the last term.  The
# floor for the next term is therefore monotonicity alone, which is free:
# the conditions nest in N, so a(n+1) >= a(n).
PUBLISHED_BOUNDS = {fam: {} for fam in FAMILIES}

# The open terms: the four indices past each family's published frontier.
OPEN_N = {fam: [max(KNOWN[fam]) + i for i in range(1, 5)] for fam in FAMILIES}

# The wheel argument has an exception zone below this x (a value can BE the
# small prime that would otherwise divide it), so the engines refuse to run
# there and the oracle covers it by brute force.
K_FLOOR = 10 ** 4

# The single composite that keeps each family's next term open: the value at
# the rung after the frontier, on the frontier term.  Gate G1 asserts it.
THE_WALL = {fam: (KNOWN[fam][max(KNOWN[fam])], max(KNOWN[fam]) + 1)
            for fam in FAMILIES}

_L = {0: 1}


def L(n):
    """lcm(1, 2, ..., n), memoized.  N is a multiple of this at filter n."""
    n = int(n)
    if n < 0:
        raise ValueError(f"n = {n} is negative")
    while max(_L) < n:
        m = max(_L) + 1
        _L[m] = _L[m - 1] * m // gcd(_L[m - 1], m)
    return _L[n]


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
    """The index of the first rung that is a condition -- always 1 here."""
    family(fam)
    return 1


def rung(n, i):
    """The multiplier of the i-th form at filter n: L(n)/i.

    Family-independent: both families share the multiplier list and differ
    only in the sign, which is why they share one singular series (G2c).
    """
    n, i = int(n), int(i)
    if not 1 <= i <= n:
        raise ValueError(f"rung {i} is outside 1..{n}")
    return L(n) // i


def mults(fam, n):
    """The multipliers of the family at index n -- the conditions a(n) must
    satisfy.  Descending, because L/1 > L/2 > ... > L/n."""
    family(fam)
    return [rung(n, i) for i in range(1, int(n) + 1)]


def nforms(fam, n):
    """How many conditions the filter n imposes: what the singular series
    exponent and the residue-list width are sized from."""
    family(fam)
    return max(0, int(n))


def value(fam, x, n, i):
    """The i-th form at x, filter n: (L(n)/i)*x + s."""
    return rung(n, i) * int(x) + sign(fam)


def term(n, x):
    """The OEIS term an x at filter n stands for: N = L(n)*x."""
    return L(int(n)) * int(x)


def x_of(n, N):
    """The x a published term N sits at, filter n; raises if L(n) does not
    divide N, which the definition forbids."""
    n, N = int(n), int(N)
    if N % L(n):
        raise ValueError(f"N = {N} is not a multiple of L({n}) = {L(n)}")
    return N // L(n)


def run_length(fam, x, n, cap=None):
    """Largest r <= cap with every form up to index r prime at x, filter n.

    Counted from rung 1, so a k whose very first form (the LARGEST value,
    L(n)*x + s) is composite has run 0.  `cap` defaults to n: a filter-n
    sweep can only speak about the n conditions it sieved for.  Riders --
    one N settling several consecutive terms -- are `run_length_N` below,
    because reaching index n + 1 also requires L(n+1) | N.
    """
    fam = family(fam)
    cap = n if cap is None else min(int(cap), int(n))
    r = 0
    while r < cap and isprime(value(fam, x, n, r + 1)):
        r += 1
    return r


def run_length_N(fam, N, cap=64):
    """Largest r <= cap with L(r) | N and (N/i + s) prime for every i <= r.

    The definition as the OEIS states it, on N rather than on a filter's x,
    so it is what decides a RIDER: an N found at filter n whose run reaches
    n + 1 or beyond settles every term up to its run at once.  The
    divisibility is part of the condition -- (N + s*k)/k must be an INTEGER
    and prime -- so a run stops at the first i that does not divide N just
    as surely as at the first composite value.
    """
    fam = family(fam)
    s = sign(fam)
    N = int(N)
    r = 0
    while r < cap:
        i = r + 1
        if N % i or not isprime(N // i + s):
            break
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
    for x in range(q):
        for m in ms:
            if (m * x + s) % q == 0:
                out.add(x)
                break
    return out


def w(q, n, fam):
    """|K(q,n,F)| as the number of distinct nonzero residues of the
    multipliers mod q.  G2b pins it against `w_closed` and against direct
    divisibility."""
    family(fam)
    return len({m % q for m in mults(fam, n) if m % q})


def w_closed(q, n):
    """The closed form proved in the module docstring: n for q > n, and
    floor(n / q^e) for q <= n with q^e the largest power of q at most n.

    Family-independent and sign-independent, which is why the two families
    share a singular series.
    """
    q, n = int(q), int(n)
    if q > n:
        return n
    e = 1
    while e * q <= n:
        e *= q
    return n // e


def forcing_n(q, fam, n_max=200):
    """The least n at which the multipliers hit every nonzero residue mod q,
    so that x == 0 (mod q) is FORCED; None if that does not happen below
    n_max.  Unlike the linear ladders this is NOT the start of a permanent
    regime -- q can be forced at n and free again at n + 1 (17 is forced at
    n = 16 and free at 17) -- so nothing may cache it across filters."""
    for n in range(1, n_max + 1):
        if w(q, n, fam) == q - 1:
            return n
    return None


def forced_primes(fam, n, upto=64):
    """The primes forced at filter n, in order."""
    return [q for q in primerange(2, upto) if w(q, n, fam) == q - 1]


def wheel_residues(fam, n, p1):
    """Every x mod W that survives all primes q <= p1, by brute force.

    W = product of the primes <= p1.  This is the oracle's version: it walks
    the whole period.  The engines build the same set by CRT lifting and are
    gated against this on small p1.
    """
    W = 1
    for q in primerange(2, p1 + 1):
        W *= q
    killed = {q: forbidden_k_residues(q, n, fam) for q in primerange(2, p1 + 1)}
    return W, [r for r in range(W)
               if all(r % q not in killed[q] for q in killed)]


def first_x(fam, n, lo=1, hi=None):
    """Least x in [lo, hi] with run_length(fam, x, n) >= n, by definition.

    The literal definition swept one integer at a time -- the slowest thing
    in this project, and the reason G2 only covers the small terms.
    """
    x = int(lo)
    while hi is None or x <= hi:
        if run_length(fam, x, n) >= n:
            return x
        x += 1
    return None


def first_N(fam, n, lo=1, hi=None):
    """Least N in [lo, hi] with run_length_N >= n -- the OEIS definition,
    swept over N itself with no substitution.  Used by G2 as the check that
    the L*x substitution loses nothing."""
    N = int(lo)
    while hi is None or N <= hi:
        if run_length_N(fam, N, cap=n) >= n:
            return N
        N += 1
    return None


# --------------------------------- gates -----------------------------------

def g1_knowns_reproduce():
    """Every frozen known satisfies the definition, each ladder is monotone,
    every term is a multiple of its L(n) and of every prime forced there,
    every term above the floor survives the small-prime wheel, and the wall
    that keeps the next term open is composite."""
    parts = []
    for fam in FAMILIES:
        known = KNOWN[fam]
        prev = 0
        for n in sorted(known):
            N = known[n]
            if N % L(n):
                return False, (f"G1 FAIL: {fam} a({n}) = {N} is not a multiple "
                               f"of L({n}) = {L(n)}")
            x = N // L(n)
            r = run_length_N(fam, N, cap=n + 3)
            if r < n:
                return False, f"G1 FAIL: {fam} a({n}) = {N} has run {r} < {n}"
            if N < prev:
                return False, f"G1 FAIL: {fam} a({n}) = {N} < a({n-1}) = {prev}"
            # The forcing lemma needs every value to EXCEED q, or the value
            # can BE the prime that divides it -- A078502's a(1) = 3 has
            # 1*3 - 1 = 2, which is why it is odd although q = 2 is forced
            # at every n.  The smallest value at filter n is (L/n)*x + s.
            vmin = (L(n) // n) * x + sign(fam)
            for q in forced_primes(fam, n):
                if vmin > q and x % q:
                    return False, (f"G1 FAIL: {fam} a({n}) = {N} has x = {x}, "
                                   f"not a multiple of the forced prime {q}")
            if x >= K_FLOOR:
                W, res = wheel_residues(fam, n, 11)
                if x % W not in set(res):
                    return False, (f"G1 FAIL: {fam} a({n}) = {N} has x = {x}, "
                                   f"killed by the wheel mod {W}")
            prev = N
        NN, ii = THE_WALL[fam]
        if NN != known[max(known)] or ii != max(known) + 1:
            return False, (f"G1 FAIL: THE_WALL for {fam} is not the frontier "
                           f"term's next rung")
        if run_length_N(fam, NN, cap=max(known) + 4) != max(known):
            return False, (f"G1 FAIL: {fam} frontier term {NN} does not reach "
                           f"exactly {max(known)}")
        parts.append(f"{fam} a({min(known)})-a({max(known)})")
    return True, ("G1 ok: " + "; ".join(parts) + " -- every published term "
                  "satisfies the definition on N, every ladder is monotone, "
                  "every term is a multiple of its lcm(1..n) and of every "
                  "prime forced at its filter, every x above the floor is on "
                  "the wheel, and each frontier term stops exactly where the "
                  "sequence says it does (its wall is composite or not "
                  "divisible)")


def g1b_finds_reproduce():
    """This project's finds, re-checked from the bare definition.

    Independent of the engines and of the evidence files: sympy alone says
    each N reaches EXACTLY its run, the ladder continues monotonically from
    the published frontier, and every N obeys L and the forced primes at its
    index.  One N may settle several consecutive terms: the run must then
    reach every term the N carries and be exactly the last of them.
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
            N = found[n]
            if n != top + 1:
                return False, (f"G1b FAIL: {fam} a({n}) does not continue the "
                               f"ladder from a({top})")
            rider = found.get(n + 1) == N
            r = run_length_N(fam, N, cap=n + 3)
            if (r < n) if rider else (r != n):
                return False, (f"G1b FAIL: {fam} a({n}) = {N} has run {r}, "
                               f"not {'at least' if rider else 'exactly'} {n}")
            if N < prev:
                return False, f"G1b FAIL: {fam} a({n}) = {N} < a({n-1}) = {prev}"
            if N % L(n):
                return False, (f"G1b FAIL: {fam} a({n}) = {N} is not a multiple "
                               f"of L({n}) = {L(n)}")
            for q in forced_primes(fam, n):
                if (N // L(n)) % q:
                    return False, (f"G1b FAIL: {fam} a({n}) = {N} has an x that "
                                   f"is not a multiple of the forced prime {q}")
            if rider:
                riders.append(f"a({n + 1}) = a({n})")
            prev, top = N, n
        parts.append(f"{fam} a({min(found)})-a({max(found)})"
                     + (f" ({', '.join(riders)} on one N)" if riders else ""))
    if not parts:
        return True, ("G1b ok: no finds of this project yet -- the gate "
                      "re-checks each from the bare definition the moment one "
                      "is entered in FOUND")
    return True, ("G1b ok: this project's finds " + "; ".join(parts) +
                  " -- each reaches exactly its run from the bare definition, "
                  "continues the ladder monotonically from the published "
                  "frontier and obeys L(n) and every forced prime")


def g2_small_terms_from_the_definition():
    """Re-derive the small terms by sweeping N itself, with no substitution.

    This is the gate that proves the L*x substitution is lossless: `first_N`
    walks every integer and asks the OEIS question directly (does k divide N,
    and is (N + s*k)/k prime), while `first_x` walks the wheel-free x line.
    They must agree, and both must equal the published term.
    """
    checked = []
    for fam in FAMILIES:
        for n in sorted(KNOWN[fam]):
            N = KNOWN[fam][n]
            if N > 200_000:
                continue
            got = first_N(fam, n, lo=1, hi=N)
            if got != N:
                return False, (f"G2 FAIL: {fam} a({n}) swept over N came out "
                               f"{got}, expected {N}")
            gx = first_x(fam, n, lo=1, hi=N // L(n))
            if gx is None or L(n) * gx != N:
                return False, (f"G2 FAIL: {fam} a({n}) swept over x came out "
                               f"{None if gx is None else L(n) * gx}, "
                               f"expected {N}")
            checked.append(f"{fam} a({n})")
    return True, ("G2 ok: " + ", ".join(checked) + " re-derived exhaustively "
                  "BOTH ways -- sweeping N with the divisibility test in the "
                  "definition, and sweeping x over N = L(n)*x -- so the "
                  "substitution the engines rely on loses nothing")


def g2b_killed_set_closed_form():
    """The closed form, the distinct-residue count and direct divisibility
    must all agree, at every prime and both signs.

    Three independent computations of the same set size: `w_closed` is the
    proof, `w` counts residues of the multipliers, `forbidden_k_residues`
    walks every residue and tests divisibility.  A disagreement is a wrong
    wheel, which is a coverage bug rather than a slow one.
    """
    cases = 0
    for n in list(range(1, 26)) + [30, 42, 43]:
        for q in primerange(2, 90):
            wc = w_closed(q, n)
            for fam in FAMILIES:
                if w(q, n, fam) != wc:
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: distinct "
                                   f"residues {w(q, n, fam)} != closed form "
                                   f"{wc}")
                direct = forbidden_k_residues(q, n, fam)
                if len(direct) != wc:
                    return False, (f"G2b FAIL: {fam} n={n} q={q}: divisibility "
                                   f"kills {len(direct)} residues, closed form "
                                   f"says {wc}")
                cases += 1
    return True, (f"G2b ok: w(q,n) = floor(n/q^e) for q <= n and n for q > n "
                  f"equals the distinct-multiplier-residue count AND direct "
                  f"divisibility in {cases} (q, n, F) cases (q < 90, n to 43, "
                  f"both signs)")


def g2c_admissible_and_forced():
    """Residue 0 is never killed (so every filter is admissible), w does not
    depend on the sign (so the families share a singular series), q = 2 is
    forced at every n, and the sporadic forcing is exactly the n+1 rule plus
    the prime-power rule -- INCLUDING the non-monotonicity that makes this
    project's wheel change at every filter."""
    for n in range(1, 45):
        for q in primerange(2, 200):
            if w_closed(q, n) > q - 1:
                return False, (f"G2c FAIL: w({q},{n}) = {w_closed(q, n)} "
                               f"exceeds q - 1, so filter {n} is inadmissible")
            for fam in FAMILIES:
                if 0 in forbidden_k_residues(q, n, fam):
                    return False, (f"G2c FAIL: {fam} n={n} q={q} kills x == 0")
        if w_closed(2, n) != 1:
            return False, f"G2c FAIL: q = 2 is not forced at n = {n}"
    for n in range(1, 45):
        a = {q: len(forbidden_k_residues(q, n, "A078502"))
             for q in primerange(2, 60)}
        b = {q: len(forbidden_k_residues(q, n, "A074200"))
             for q in primerange(2, 60)}
        if a != b:
            return False, f"G2c FAIL: the killed-set SIZES differ by sign at n={n}"
    # n = 22 forces 2, 3 (floor(22/9) = 2), 5 (floor(22/5) = 4) and 23
    # (the n+1 rule) at once -- the prime-power rule and the n+1 rule
    # compounding, which is why a unit is computed and never guessed.
    want = {15: 2, 16: 34, 17: 2, 18: 114, 19: 6, 20: 30, 22: 690, 30: 62}
    for n, u in want.items():
        got = 1
        for q in forced_primes("A078502", n):
            got *= q
        if got != u:
            return False, (f"G2c FAIL: the forced unit at n = {n} is {got}, "
                           f"not {u}")
    for n in (16, 18, 22, 30, 42):
        if n + 1 in (17, 19, 23, 31, 43) and w_closed(n + 1, n) != n:
            return False, (f"G2c FAIL: q = n + 1 = {n+1} is not forced at "
                           f"n = {n}")
    if forced_primes("A078502", 17) != [2] or forced_primes("A078502", 16) != [2, 17]:
        return False, "G2c FAIL: forcing is not sporadic between n = 16 and 17"
    return True, ("G2c ok: residue 0 survives every prime at every filter to "
                  "n = 44 (admissible, so Dickson gives a term at every n and "
                  "a find can only confirm it); the killed-set sizes are "
                  "sign-independent, so the two families share one singular "
                  "series; q = 2 is forced at every n; and the forcing is "
                  "SPORADIC -- unit 2 at n = 15 and 17, 34 at 16 (q = n + 1 = "
                  "17), 114 at 18 (19 by the same rule and 3 because "
                  "floor(18/9) = 2), 30 at 20 -- so no wheel constant may be "
                  "carried from one filter to the next")


def g2d_derived_identities():
    """A093554 = A078502 - 1 and A093553 = A074200 + 1 at every published
    index, from the bare definition of the DERIVED entries.

    Each is checked twice: against the published table of the rider, and by
    re-deriving the rider's own condition ((m - k + 1)/k, resp. (m + k - 1)/k)
    on the shifted integer.  That is what makes a find on one entry a find on
    two.
    """
    parts = []
    for fam in FAMILIES:
        for other, shift in FAMILIES[fam]["also"]:
            tab = KNOWN_ALSO[other]
            s = sign(fam)
            for n in sorted(KNOWN[fam]):
                N = KNOWN[fam][n]
                m = N + shift
                if n in tab and tab[n] != m:
                    return False, (f"G2d FAIL: {other} a({n}) = {tab[n]}, but "
                                   f"{fam} a({n}) {shift:+d} = {m}")
                # the rider's own condition: (m - k + 1)/k for A093554,
                # (m + k - 1)/k for A093553 -- both are (N + s*k)/k again
                for k in range(1, n + 1):
                    num = m - k + 1 if s < 0 else m + k - 1
                    if num % k or not isprime(num // k):
                        return False, (f"G2d FAIL: {other} at n = {n}: "
                                       f"({m} {'-' if s < 0 else '+'} k "
                                       f"{'+' if s < 0 else '-'} 1)/k is not "
                                       f"prime at k = {k}")
            parts.append(f"{other} = {fam} {shift:+d} (a(1)-a({max(tab)}))")
    return True, ("G2d ok: " + "; ".join(parts) + " -- verified against each "
                  "rider's published table AND by re-deriving the rider's own "
                  "condition on the shifted integer, so every find settles two "
                  "OEIS entries")


GATES = [g1_knowns_reproduce, g1b_finds_reproduce, g2b_killed_set_closed_form,
         g2c_admissible_and_forced, g2d_derived_identities,
         g2_small_terms_from_the_definition]

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
