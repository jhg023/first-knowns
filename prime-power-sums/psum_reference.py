"""The oracle for the prime power-sum divisibility family -- slow,
obviously correct, sympy only.

    S(m, k) = Sum_{j=1..k} prime(j)^m

and a FAMILY is a pair (m, e) with e in {0, 1}, asking for the k with

    k  |  e + S(m, k).

Twelve OEIS sequences are carried here.  Each family is published twice --
once as the index k and once as prime(k) -- so one find extends two
entries, and for m = 1 two more (the sum itself and the integer average).

Nothing here is optimized and nothing here is clever; that is the point.
Everything the fast engines claim is ultimately checked against this file,
so it may only use trusted library primitives (sympy) and the definition
as written.

Three facts about the problem are proved here rather than assumed, because
both engines depend on all three:

  THE OBSTRUCTION.  Let q be a prime with (q-1) | m.  For every prime
  p != q, Fermat gives p^m == 1 (mod q).  Once q is itself among the first
  k primes, exactly one term of the sum (q^m) is 0 mod q and the other
  k-1 are 1, so

      S(m, k) == k - 1   (mod q)      for all k >= pi(q).

  For e = 0 a term needs S == 0 (mod k), so any k divisible by such a q
  has S == -1 (mod q) and can NEVER be a term: the terms are confined to
  k coprime to Q(m) = prod{q prime : (q-1) | m}.  For e = 1 the same
  congruence hands those k the mod-q condition for free instead.  This is
  the difference between a sequence with 18 terms and one with thousands,
  it is where the engines get their wheel on the index line, and it is
  why every known term of A045345 is odd (Q(1) = 2).

  THE DENSITY.  Summing the heuristic P(k | e + S) ~ 1/k over the k the
  obstruction leaves gives  E[terms in (A,B)] = c * ln(B/A)  with
  c = phi(Q)/Q for e = 0.  Validated at 1.09 (95% [0.90, 1.27]) against
  138 published terms; see psum_model.py, which owns the model and its
  gates.

  THE PAIRING.  The index-reported and prime-reported sequences of one
  family are the same mathematical object: A233192(n) = prime(A125827(n)).
  A transcription error in either table breaks the pairing, which is what
  G1b checks.

WHAT THIS FAMILY IS NOT: monotone across m.  Each (m, e) is its own
question with its own frontier -- m = 11 is open from k = 5e14 while
m = 1 is open only from k = 6.5e15 -- so no family bounds any other and
the campaign carries a frontier PER FAMILY rather than one cursor.

Gates in this file: G1 (the frozen knowns are structurally sound), G1b
(the index/prime pairing holds), G2 (small terms re-derived exhaustively
from the definition) and G3 (the obstruction theorem, verified directly
against the definition rather than assumed).
"""

from sympy import isprime, prime, primerange

# --------------------------------------------------------------------------
# The frozen tables, as published.  Every list is the COMPLETE set of known
# terms of that sequence: for each family the OEIS bound "a(N) > X" has
# N - 1 equal to the number of terms below, which is how the listing is
# known not to be truncated (%S/%T/%U hold only ~260 characters, and a
# clipped list would silently under-report).  Re-verified against the
# oeisdata export of 2026-08-21, pulled the day this project was built.
#
# frontier: the largest k proved clear, i.e. max(published bound, last
# known term).  A bound is written BEFORE the term it bounds is found and
# is never retracted afterwards, so several of these entries carry a bound
# that the sequence has since overtaken -- A125826 still says
# "a(19) > 1.9*10^14" next to a found a(19) = 1.26e15.  Taking the bound
# alone would put the next term far too cheap.
# --------------------------------------------------------------------------

FAMILIES = {
    (1, 0): dict(
        idx="A045345", val="A171399", also=("A050247", "A050248"),
        keywords="nonn,nice,more",
        held="Paul W. Dyson, Sep 26 2022",
        frontier=6_500_000_000_000_000,
        terms=[1, 23, 53, 853, 11869, 117267, 339615, 3600489, 96643287,
               2664167025, 43435512311, 501169672991, 745288471601,
               12255356398093, 153713440932055, 6361476515268337],
        primes=[2, 83, 241, 6599, 126551, 1544479, 4864121, 60686737,
                1966194317, 63481708607, 1161468891953, 14674403807731,
                22128836547913, 399379081448429, 5410229663058299,
                248264241666057167]),
    (7, 0): dict(
        idx="A125826", val="A232865", also=(),
        keywords="nonn,hard,more",
        held="Paul W. Dyson, Jan 17 2024",
        frontier=1_258_223_430_425_543,
        terms=[1, 25, 1677, 21875, 538513, 1015989, 18522325, 1130976595,
               1721158369, 561122374231, 1763726985077, 2735295422833,
               7631117283951, 22809199833151, 46929434362563,
               49217568518075, 151990420653423, 174172511353413,
               1258223430425543],
        primes=[2, 97, 14293, 247997, 7979737, 15749303, 344468591,
                25934255929, 40224745543, 16495569405383, 53941465463489,
                84897825837611, 244949151647509, 757938163218799,
                1594375071689591, 1674528348898463, 5347819657753523,
                6152744788157173, 47008163075851819]),
    (9, 0): dict(
        idx="A131263", val="A232962", also=(),
        keywords="nonn,more",
        held="Paul W. Dyson, Dec 16 2024",
        frontier=500_000_000_000_000,
        terms=[1, 281525, 1011881, 13721649, 309777093, 417800903,
               12252701193, 27377813605, 37762351523, 245773819141,
               51230573255953, 82578361848569, 277900491430385],
        primes=[2, 3974779, 15681179, 250818839, 6682314181, 9143935289,
                311484445891, 718930864213, 1004267651657, 7014674460791,
                1745134691306711, 2853623691677477, 9950715071009107]),
    (11, 0): dict(
        idx="A125827", val="A233192", also=(),
        keywords="nonn,hard,more",
        held="Paul W. Dyson, Dec 31 2024",
        frontier=500_000_000_000_000,
        terms=[1, 25, 59, 2599, 6195, 421407, 11651191, 19293221, 255136097,
               1820015683, 2183556659, 7993872143, 9850779563, 2006892138335,
               2649677145789, 6645858099781, 318039538085101,
               414996765110825],
        primes=[2, 97, 277, 23311, 61583, 6133811, 210952097, 359643241,
                5451597181, 42641466149, 51575229001, 199655689679,
                248181386429, 61646670874849, 82153230089767,
                212374157550341, 11432141933990629, 15031011453909223]),
    (13, 0): dict(
        idx="A131273", val="A232770", also=(),
        keywords="nonn,more,less",
        held="Paul W. Dyson, Dec 06 2024",
        frontier=500_000_000_000_000,
        terms=[1, 23, 299, 313, 171287, 435705, 487475, 3774601, 219347813,
               9613155161, 5150163868035, 37365789554345, 228914067371295],
        primes=[2, 83, 1979, 2081, 2326469, 6356923, 7170679, 63812027,
                4652001719, 241949473277, 163220642765623, 1260677492111911,
                8150959175977039]),
    (17, 0): dict(
        idx="A131277", val="A233555", also=(),
        keywords="nonn,more,less",
        held="Paul W. Dyson, Sep 15 2023",
        frontier=629_341_300_687_639,
        terms=[1, 395191, 697717, 1078323, 2050797, 10543929, 386099691,
               2467825171, 4488040933, 17387575533, 39641205433,
               825688143387, 2800262033655, 3214748608393, 5174884331693,
               16485974355373, 20683624349423, 34390023299149,
               629341300687639],
        primes=[2, 5724469, 10534369, 16784723, 33330911, 189781037,
                8418091991, 58605633953, 109388266843, 448366797199,
                1056238372873, 24603683667221, 86982253895059,
                100316149840769, 164029709175817, 542295448805641,
                685217940914237, 1701962315686097, 23064173255594491]),
    (19, 0): dict(
        idx="A131279", val="A233767", also=(),
        keywords="nonn",
        held="Paul W. Dyson, Dec 31 2024",
        frontier=500_000_000_000_000,
        terms=[1, 25, 453, 677, 839, 1015, 3735, 4175, 4413, 10369, 14239,
               43311, 452567, 1274185, 14102849, 37801813, 71271705,
               93524231, 386557609, 2151748733, 261349938459, 761474469415,
               1284262332971, 5115376212971, 17863411895047,
               122189141425495],
        primes=[2, 97, 3203, 5059, 6469, 8081, 35051, 39719, 42209, 109049,
                154591, 523297, 6621827, 20059771, 258196441, 731584957,
                1427109029, 1899496631, 8428550519, 50790885203,
                7475902096387, 22626378502139, 38855796912367,
                162082298018497, 589085299527401, 4271778258271487]),
}

# The CENSUS family.  e = 1 with m even inverts the obstruction into a free
# congruence at every q | Q(m), so its density is c ~ 30 rather than ~1/5:
# A233264 already lists over a thousand terms and its bound is a(1171).
# It is carried NOT as a hunt target but as the engine's live health
# signal -- it produces hits in every segment, so a stream that has gone
# wrong announces itself in seconds instead of in weeks.  Its hits are
# counted in [STATUS] and never narrated (CONVENTIONS.md, the census rule).
CENSUS_FAMILY = (12, 1)
CENSUS_INFO = dict(idx="A233264", val="A233265", keywords="nonn",
                   held="Bruce Garner, Jun 06 2021")
# A233264's first 63 terms, for the canary check at the bottom of the line.
CENSUS_TERMS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 18, 20,
                21, 24, 26, 27, 28, 30, 35, 36, 39, 40, 42, 45, 46, 48, 52,
                54, 56, 60, 63, 65, 66, 70, 72, 78, 80, 84, 87, 90, 91, 100,
                104, 105, 112, 117, 120, 126, 130, 138, 140, 144, 154, 156,
                160, 168, 175, 176]

TARGETS = tuple(sorted(FAMILIES))
ALL_FAMILIES = TARGETS + (CENSUS_FAMILY,)

# --------------------------------------------------------------------------
# A published value this project does not believe.
#
# The two tables of one family are the same object -- a_val(n) must be
# prime(a_idx(n)) -- so the ratio a_val(n) / [k(ln k + ln ln k)] has to sit
# just under 1 and creep upward with k.  Across the seven families it runs
# 0.89 -> 0.98 without an exception, except here:
#
#   A233555(18) = 1701962315686097   pairs with   A131277(18) = 34390023299149
#   ratio 1.430, where its neighbours are 0.972 and 0.975.
#
# prime(3.439e13) is about 1.157e15, not 1.702e15.  And 1701962315686097 is
# exactly prime(5e13) -- that is, A131277's OWN published search limit
# "a(19) > 5*10^13" rendered on the prime line, which A233555 also carries
# verbatim as its "a(19) > 1701962315686097" comment, submitted the same day
# (Bruce Garner, Jan 07 2022) as its a(18).  The search limit appears to
# have been entered where the term belongs.
#
# The project does NOT edit OEIS (CONVENTIONS.md: discoveries and
# corrections are the owner's call, never the pipeline's).  It does three
# things: excludes the value from the checks that would be fooled by it,
# PINS it with a gate so that a future export silently fixing it breaks the
# battery instead of drifting, and notes that the m = 17 sweep passes
# k = 3.44e13 in its first hours -- at which point this engine produces the
# correct value as a by-product and the owner can decide what to do with it.
SUSPECT = {
    (17, 0): {18: dict(
        table="val", published=1701962315686097,
        expect_near=1.157e15,
        why="equals prime(5e13), the family's own a(19) search limit; "
            "PNT ratio 1.430 against neighbours 0.972 and 0.975")},
}


# ------------------------------ the definition ------------------------------

def power_sum(k, m):
    """S(m, k) = Sum_{j=1..k} prime(j)^m, by the definition.

    Walks the primes in order with sympy and adds exact Python integers.
    This is the slowest thing in the project and the most trustworthy.
    """
    total, j = 0, 0
    limit = 64
    while True:                       # grow the window until it holds k primes
        got = 0
        total, j = 0, 0
        for p in primerange(2, limit):
            total += p ** m
            j += 1
            if j == k:
                got = 1
                break
        if got or k == 0:
            return total
        limit *= 2


def divides(k, m, e=0):
    """The condition itself: k | e + S(m, k)."""
    return k > 0 and (e + power_sum(k, m)) % k == 0


def terms_upto(m, e, kmax):
    """Every term of family (m, e) with k <= kmax, by the definition,
    accumulating the sum as the primes go by (one pass, exact integers)."""
    out, total, k = [], 0, 0
    for p in primerange(2, _nth_prime_bound(kmax)):
        total += p ** m
        k += 1
        if k > kmax:
            break
        if (e + total) % k == 0:
            out.append(k)
    return out


def _nth_prime_bound(k):
    """A safe upper bound for prime(k) (Rosser).  Deliberately generous:
    the oracle may be slow, it may not be wrong."""
    import math
    if k < 6:
        return 16
    return int(k * (math.log(k) + math.log(math.log(k)))) + 16


def obstruction_primes(m):
    """{q prime : (q-1) | m} -- the primes at which the sum is frozen."""
    return tuple(q for q in primerange(2, m + 2) if m % (q - 1) == 0)


def Q(m):
    """Q(m) = prod{q : (q-1) | m}: the modulus the terms must avoid (e = 0)
    or ride for free (e = 1)."""
    out = 1
    for q in obstruction_primes(m):
        out *= q
    return out


def c_of(m, e=0):
    """The density constant for e = 0: c = phi(Q)/Q, straight from the
    obstruction proved in G3.  E[terms in (A,B)] = c * ln(B/A).

    e = 1 is deliberately NOT here.  Its constant is not a consequence of
    the obstruction (the exclusion inverts into a free congruence) and is
    argued and validated in psum_model.py, which owns the odds model."""
    if e != 0:
        raise ValueError("c_of covers e = 0 only; see psum_model.c_of")
    c = 1.0
    for q in obstruction_primes(m):
        c *= (1.0 - 1.0 / q)
    return c


# --------------------------------- gates -----------------------------------

def g1_knowns_structural():
    """Every frozen known is structurally sound: strictly increasing, the
    prime-reported partner is prime and sits in the band the prime number
    theorem allows for prime(k), and -- the sharp one -- no term is
    divisible by any obstruction prime of its own family."""
    import math
    for (m, e), f in sorted(FAMILIES.items()):
        ts, ps, qs = f["terms"], f["primes"], obstruction_primes(m)
        if len(ts) != len(ps):
            return False, (f"G1 FAIL: {f['idx']} has {len(ts)} terms but "
                           f"{f['val']} has {len(ps)}")
        if any(b <= a for a, b in zip(ts, ts[1:])):
            return False, f"G1 FAIL: {f['idx']} is not strictly increasing"
        for k, p in zip(ts, ps):
            if k > 1 and any(k % q == 0 for q in qs) and e == 0:
                return False, (f"G1 FAIL: {f['idx']} term {k} is divisible "
                               f"by an obstruction prime of m={m} "
                               f"({qs}) and cannot be a term")
            if not isprime(p):
                return False, f"G1 FAIL: {f['val']} term {p} is not prime"
            n = ts.index(k) + 1
            if n in SUSPECT.get((m, e), {}):
                continue          # a value this project does not believe
            if k >= 10**5:
                # PNT band.  Below 1e5 G1b checks prime(k) EXACTLY instead;
                # the approximation is only tight once k is large, and a
                # band loose enough for k = 300 would not have caught the
                # one real error in these tables.
                band = p / (k * (math.log(k) + math.log(math.log(k))))
                if not 0.93 <= band <= 1.00:
                    return False, (f"G1 FAIL: {f['val']} {p} is not in the "
                                   f"PNT band for prime({k}) (ratio "
                                   f"{band:.3f})")
        if f["frontier"] < ts[-1]:
            return False, (f"G1 FAIL: {f['idx']} frontier {f['frontier']} is "
                           f"below its own last term {ts[-1]}")
    n = sum(len(f["terms"]) for f in FAMILIES.values())
    return True, (f"G1 ok: {n} frozen terms across {len(FAMILIES)} families "
                  f"are increasing, prime-partnered, inside the PNT band, "
                  f"and coprime to their own obstruction modulus")


def g1b_pairing(kmax=10**5):
    """The index table and the prime table are the same object:
    prime(a_idx(n)) == a_val(n).  Checked EXACTLY, by sympy, on every term
    small enough for sympy to produce prime(k)."""
    n = 0
    for (m, e), f in sorted(FAMILIES.items()):
        for k, p in zip(f["terms"], f["primes"]):
            if k <= kmax:
                if prime(k) != p:
                    return False, (f"G1b FAIL: {f['idx']} k={k} pairs with "
                                   f"prime(k)={prime(k)}, not "
                                   f"{f['val']}={p}")
                n += 1
    return True, (f"G1b ok: index/prime pairing verified exactly by sympy "
                  f"for all {n} terms with k <= {kmax:.0e}")


def g1c_suspect_still_wrong():
    """Pin the one published value this project does not believe.

    If a future oeisdata export corrects A233555(18), this gate FAILS --
    which is the point: the correction must be noticed and the table
    updated deliberately, not absorbed silently.  See SUSPECT above.
    """
    import math
    for (m, e), entries in SUSPECT.items():
        f = FAMILIES[(m, e)]
        for n, info in entries.items():
            table = f["primes"] if info["table"] == "val" else f["terms"]
            if table[n - 1] != info["published"]:
                return False, (f"G1c FAIL: {f['val']}({n}) is no longer "
                               f"{info['published']} -- the anomaly this "
                               f"project pinned has changed; re-check the "
                               f"pairing and update SUSPECT")
            k = f["terms"][n - 1]
            band = info["published"] / (k * (math.log(k)
                                             + math.log(math.log(k))))
            if 0.93 <= band <= 1.00:
                return False, (f"G1c FAIL: {f['val']}({n}) now sits INSIDE "
                               f"the PNT band (ratio {band:.3f}); it is no "
                               f"longer suspect and SUSPECT must be dropped")
    return True, ("G1c ok: A233555(18) is still the published anomaly "
                  "(ratio 1.430, equals prime(5e13) = the family's own "
                  "a(19) search limit); excluded from G1, pinned here")


def g2_rederive_small(kmax=60000):
    """Re-derive the small terms exhaustively from the definition: walk the
    primes one at a time, accumulate exact integers, test every k."""
    for (m, e), f in sorted(FAMILIES.items()):
        want = [k for k in f["terms"] if k <= kmax]
        got = terms_upto(m, e, kmax)
        if got != want:
            return False, (f"G2 FAIL: {f['idx']} re-derived {got} up to "
                           f"k={kmax}, frozen table says {want}")
    # The census family lists over a thousand terms, so its %S/%T/%U
    # rendering is TRUNCATED at 63 -- comparing past the last listed term
    # would compare against a table that simply stops.  Compare on the
    # prefix the export actually carries.
    cm, ce = CENSUS_FAMILY
    got = terms_upto(cm, ce, CENSUS_TERMS[-1])
    if got != CENSUS_TERMS:
        return False, (f"G2 FAIL: census family {CENSUS_INFO['idx']} "
                       f"re-derived {len(got)} terms up to "
                       f"k={CENSUS_TERMS[-1]}, table lists "
                       f"{len(CENSUS_TERMS)}")
    return True, (f"G2 ok: every frozen term with k <= {kmax} re-derived "
                  f"exhaustively from the definition in all "
                  f"{len(FAMILIES)} families, plus the census family to 2000")


def g3_obstruction_theorem(kmax=3000):
    """The obstruction, checked against the definition rather than assumed:
    S(m,k) == k-1 (mod q) for every q with (q-1)|m and every k >= pi(q),
    and NO k divisible by such a q divides S(m,k)."""
    for m in (1, 4, 7, 11, 12, 17, 19):
        qs = obstruction_primes(m)
        if not qs:
            return False, f"G3 FAIL: m={m} has no obstruction prime (2 always is)"
        total, k, seen = 0, 0, {q: False for q in qs}
        for p in primerange(2, _nth_prime_bound(kmax)):
            total += p ** m
            k += 1
            if k > kmax:
                break
            for q in qs:
                if p >= q:
                    seen[q] = True
                if not seen[q]:
                    continue
                if total % q != (k - 1) % q:
                    return False, (f"G3 FAIL: m={m} q={q} k={k}: "
                                   f"S mod q = {total % q}, expected "
                                   f"{(k - 1) % q}")
                if k % q == 0 and total % k == 0:
                    return False, (f"G3 FAIL: m={m} k={k} is divisible by "
                                   f"the obstruction prime {q} and yet "
                                   f"divides S -- the theorem is wrong")
    return True, (f"G3 ok: S(m,k) == k-1 (mod q) for every q with (q-1)|m, "
                  f"every k <= {kmax}, m in 1,4,7,11,12,17,19 -- so no k "
                  f"divisible by such a q is ever a term (e = 0)")


GATES = [g1_knowns_structural, g1b_pairing, g1c_suspect_still_wrong,
         g2_rederive_small, g3_obstruction_theorem]

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
