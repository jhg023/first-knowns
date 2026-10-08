"""poly_search.py -- the CPU engine for the exact-run polynomial ladders.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is independent
in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array over
    the x line and uses no wheel at all.  The GPU engine never materialises
    the x line: it generates only the residues that survive a wheel and
    tests those against packed forbidden-residue tables, bailing out at the
    first kill.  A wheel bug on the GPU side therefore shows up as a parity
    failure rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(q,n,F) is built here as {-c mod q} over
    the constants, while the oracle walks every residue and tests
    divisibility.  G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (x, off) pairs on
the GPU -- x = base + off with base a host-side big int -- so no machine
word bounds the search (OPTIMIZATION.md 2.7, from the first commit).

WHAT IS SIEVED, AND WHAT IS NOT.  At filter n the sieve expresses the n + 1
forms that must be PRIME: the term itself and the term plus each of its
first n shifts.  That the run is EXACT -- the next shift's value NOT prime
-- is no sieve's business: it is the oracle's definition (is_term) and the
classification's reading (run_length_fast reads every survivor's run to
its end).  So a survivor of filter n is a candidate for every index from n
up, which is what lets one sweep from the bottom of the line settle the
first occurrence of every exact run at or above its filter.

WHAT IS SWEPT.  The term itself, the prime p, on ONE line from the bottom.
The forced primes pin it to a single CLASS from the first index with two
forms: 5 (mod 6) on A165234, 1 (mod 6) on A230663, A092120 and A347537
(poly_reference G2c); at the one-form index only 2 is forced (unit 2).
The machinery sweeps a general class x = r + u*t and this engine marks the
dense x line knowing nothing of r or u, which is what makes the parity gate
a check of the forcing as well as of the sieve.  u is DERIVED per filter
(`forced_unit`), and a unit whose primes are not all forced is refused
(`assert_unit`), because a unit is a coverage claim.

THE INDEX IS NOT THE RUN.  A sieve at filter n expresses nforms(fam, n) =
run_of(fam, n) + 1 forms (poly_reference): n of them where the entry's name
counts the polynomial's argument from 0 to n - 1, n + 1 on A092120.  The
engines take the INDEX everywhere and ask the oracle for its constants;
the classification reads a RUN (the count of shifts whose value is prime)
and the launcher maps it back with index_of.

THE EXCEPTION ZONE IS [2, q2], AT EVERY FILTER.  A kill by q proves nothing
unless the value exceeds q, and the smallest value is the term itself, so
the engines refuse to run at or below the sieve depth (k_floor) and the
integers from 2 to q2 are classified one at a time (prefix_hits).  The walk
is the forced class PLUS the forced primes themselves: 2 and 3 are primes
outside the class that 2 and 3 force, and 3 is a term (a(3) of A165234 and
of A230663, a(2) of A092120 and of A347537).

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24.  The largest value at x is x plus the largest
shift of the filter, so the PROOF CROSSING k_proof(n, F) is the bound less
that shift -- and the shifts here are SMALL (2 * 31^2 = 1922 at the last
filter the engine can express), so the crossing is the bound itself to
within a few thousand, and every classification below 3.3e24 is a proof.
Past it a classification is a strong probable-prime chain, which can only
lengthen a run, never hide one, and a discovery is proved by CERTIFICATE:
a value here has NO multiplier x term +- 1 structure, so each value is
proved by huntlib.certificate.prove's own bounded search on N -+ 1, which
huntlib.ceiling MEASURED to 1e40 (and this repository's primorial-runs to
1e60 for structureless values).  ONE CEILING binds: huntlib's K_CEIL =
1e40 on the term, which is also the height of every value to within a
few thousand.  What ends a family is not a ceiling but the ENGINE'S
RESIDUE LIST: the tail keeps FORMS_MAX = 32 killed residues a prime, one
per form, so the last index a campaign can express is n_max (32 on the
entries that count from 0 to n - 1, 31 on A092120) -- and the model puts
a(23) a decade of GPU time away, so the cap is academic.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, every family, in x space and in class space; a unit that is
not forced -- or not squarefree -- is refused), G4 (CPU survivors == the
oracle's definition of a survivor on populated windows), G5 (the CPU engine
finds, from the bottom of the line with the exception zone brute-forced,
the FIRST prime above the exception zone with a run of at least the
filter's, and it is the least known term of that index or a later one,
with a run of exactly its index's), G6 (engine run lengths == sympy BPSW, every known term reading
exactly its index's run), G10 (numeric hygiene: the crossing tight to one
x at every index, the ceiling on the term from huntlib, and the last index
the engine can express).
"""

import pathlib as _pathlib
import sys as _sys
from functools import lru_cache as _lru_cache

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling as _ceiling                        # noqa: E402
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from poly_reference import (FAMILIES, FOUND, KNOWN, constants,  # noqa: E402
                            family, first_reach, floor_x,
                            forbidden_k_residues, forms, frontier,
                            in_domain, index_of, nforms, offset,
                            run_length as oracle_run_length, run_of,
                            shift_k, w, w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing search runs over (the log and the documents
# name the forced class; nothing in the engines depends on it).
UNIT_UPTO = 64

# THE CEILING ON THE TERM: huntlib's, MEASURED here rather than assumed
# (module docstring; rule 5h).  EXCLUSIVE.
K_CEIL = _ceiling.K_CEIL

# THE LAST FILTER THE ENGINE CAN EXPRESS.  The GPU tail keeps one killed
# residue per form in a list of poly_gpu.NRES_MAX slots (G10 pins the two
# constants to each other), so a filter of more forms than that cannot be
# sieved; a family's campaign ends when its lowest open index passes n_max.
# The values themselves stay within a few thousand of the term, so no
# ceiling on the VALUES is needed here (primorial-runs measured one for
# shifts of 1e50; these shifts are 2 * 31^2).
FORMS_MAX = 32


def n_max(fam):
    """The largest index n with at most FORMS_MAX forms: the last filter
    the engine can express, and where that family's campaign ends."""
    fam = family(fam)
    n = offset(fam)
    while nforms(fam, n + 1) <= FORMS_MAX:
        n += 1
    return n


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof at index n -- the
    deterministic Miller-Rabin bound less the largest constant.  EXCLUSIVE:
    k_proof - 1 is the largest x whose every value stays under the bound
    (G10 pins both halves).  The constants are small here, so it sits within
    a few thousand of the bound at every filter."""
    return MR_VALID_BELOW - max(constants(fam, n))


def k_ceil(n, fam):
    """The enforced ceiling on the term, every family: K_CEIL.  EXCLUSIVE."""
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2, n, fam):
    """The smallest x the engines will sweep (EXCLUSIVE).

    A kill by q is only a proof of compositeness when the value EXCEEDS q.
    The smallest value is x itself (the term is a form and every shift is
    positive), so a sieve to q2 is valid from x > q2.
    """
    return int(q2) - min(constants(fam, n))


def zone(q2, n, fam):
    """(lo, hi) INCLUSIVE: the integers between the definition's floor and
    the engine's that a sweep at depth q2 must cover by brute force: [2,
    q2] here, at every filter (every line starts at the bottom)."""
    lo, hi = floor_x(fam, n), k_floor(q2, n, fam)
    return (lo, hi) if lo <= hi else None


def killed_residues(q, n, fam, unit=1):
    """K(q,n,F) = { -c mod q } over the constants of index n -- the
    residues of x that some form x + c makes divisible by q.

    CLASS SPACE.  The forced primes pin x to ONE class, x == r (mod unit)
    (`unit_residue`), so the GPU engine sweeps t with x = r + unit*t, and
    the residues of t that q kills are those of x carried through the map:
    t == (k - r) * unit^-1 (mod q) for each killed k, q not dividing unit.
    A prime OF the unit kills no t at all -- the class was chosen so that
    it cannot -- and returns the empty list.  The map is a bijection of
    Z/q, so the sizes, hence the survival curve and the wheel counts, are
    unchanged (G3 pins this against the x-space set).  `unit = 1` is x
    space itself.  Whether a unit is ADMISSIBLE at a filter is
    `assert_unit`'s job.
    """
    unit = int(unit)
    if unit % q == 0:
        return []
    ks = _xkills(int(q), int(n), family(fam))
    if unit == 1:
        return sorted(ks)
    r, inv = unit_residue(n, fam, unit), pow(unit, -1, q)
    return sorted({((k - r) * inv) % q for k in ks})


@_lru_cache(maxsize=None)
def _consts(n, fam):
    return tuple(constants(fam, n))


@_lru_cache(maxsize=None)
def _xkills(q, n, fam):
    return frozenset((-c) % q for c in _consts(n, fam))


def _free(q, n, fam):
    """The residues of x mod q that no form kills."""
    return sorted(set(range(q)) - _xkills(int(q), int(n), family(fam)))


def forced_unit(n, fam, upto=UNIT_UPTO):
    """The product of the primes FORCED at index n -- those q that leave x
    exactly one residue class: 2 at the one-form index, 6 from the first
    index with two forms on, every family.  Derived per filter and never
    stored: a unit is a coverage claim."""
    u = 1
    for q in primerange(2, upto):
        if len(_free(q, n, fam)) == 1:
            u *= q
    return u


def unit_residue(n, fam, unit):
    """r with x == r (mod unit) for every x that survives the primes of
    `unit` -- the CRT of their single free classes.  0 <= r < unit."""
    return _unit_residue(int(n), family(fam), int(unit))


@_lru_cache(maxsize=None)
def _unit_residue(n, fam, unit):
    unit = assert_unit(n, fam, unit)
    r, m = 0, 1
    for q in primerange(2, UNIT_UPTO):
        if unit % q == 0:
            a = _free(q, n, fam)[0]
            r, m = r + m * (((a - r) * pow(m, -1, q)) % q), m * q
    return r


def forced_class(n, fam, upto=UNIT_UPTO):
    """(r, u): the class x == r (mod u) the forced primes pin x to."""
    u = forced_unit(n, fam, upto)
    return unit_residue(n, fam, u), u


def assert_unit(n, fam, unit):
    """Raise unless `unit` is SQUAREFREE and every prime factor of it is
    forced at index n.

    A unit that is not forced is a COVERAGE bug, not an inefficiency: an
    engine sweeping x = r + unit*t never looks at the other classes, and if
    a prime of the unit leaves two classes free it has silently dropped one
    of them.  So the check is against the definition -- exactly one free
    class per prime of the unit -- and it raises.
    """
    fam = family(fam)
    unit = int(unit)
    if unit < 1:
        raise ValueError(f"unit {unit} is not a positive integer")
    for q in primerange(2, UNIT_UPTO):
        if unit % q == 0 and len(_free(q, n, fam)) != 1:
            raise ValueError(
                f"unit {unit} is not admissible at index {n} of {fam}: {q} "
                f"leaves {len(_free(q, n, fam))} residue classes free there, "
                f"not 1, so an engine sweeping x = r + {unit}*t would skip "
                f"line it claims to cover; the largest admissible unit here "
                f"is {forced_unit(n, fam)}")
        if unit % (q * q) == 0:
            raise ValueError(
                f"unit {unit} is not squarefree: forcing pins x mod {q}, "
                f"never mod {q * q}")
    rest = unit
    for q in primerange(2, UNIT_UPTO):
        while rest % q == 0:
            rest //= q
    if rest != 1:
        raise ValueError(f"unit {unit} has a prime factor above {UNIT_UPTO}, "
                         f"which nothing forces")
    return unit


def in_domain_fast(fam, x):
    """The domain predicate with huntlib's chain: a prime."""
    family(fam)
    x = int(x)
    return x >= 2 and mr_is_prime(x)


def run_length_fast(fam, x, cap=64):
    """The oracle's run_length with huntlib's deterministic Miller-Rabin
    (a strong probable-prime chain past the proof crossing)."""
    fam, x = family(fam), int(x)
    if not in_domain_fast(fam, x):
        return 0
    r = 0
    while r < cap and mr_is_prime(x + shift_k(fam, r + 1)):
        r += 1
    return r


def prefix_hits(fam, n, q2, floor=1, cap=64):
    """[(x, run)] over the exception zone of index n at depth q2 -- every
    integer between the definition's floor and the engine's with a run of
    at least `floor` -- by huntlib's chain (the oracle's own prefix_hits is
    the sympy version).  The walk is the forced class PLUS the forced primes
    themselves: 2 and 3 are primes outside the class that 2 and 3 force (3
    is a(3) of A165234), which is the exception zone's whole point."""
    fam = family(fam)
    z = zone(q2, n, fam)
    if z is None:
        return []
    lo, hi = z
    r0, u = forced_class(n, fam)
    out = []
    for x in sorted(q for q in primerange(2, UNIT_UPTO) if u % q == 0 and lo <= q <= hi):
        r = run_length_fast(fam, x, cap=cap)
        if r >= floor:
            out.append((x, r))
    x = lo + ((r0 - lo) % u)
    while x <= hi:
        r = run_length_fast(fam, x, cap=cap)
        if r >= floor:
            out.append((x, r))
        x += u
    return sorted(out)


class CpuEngine:
    """Segmented sieve over the dense x line, no wheel."""

    def __init__(self, n, fam, q2=Q2_DEFAULT):
        self.n = int(n)
        self.fam = family(fam)
        self.q2 = q2
        self.primes = list(primerange(2, q2 + 1))
        self.table = {q: killed_residues(q, n, self.fam) for q in self.primes}
        self.marks_per_k = sum(len(v) / q for q, v in self.table.items())

    # ---------------------------------------------------------------- sieve
    def survivors(self, k_lo, k_hi, block=1 << 22):
        """Yield lists of the x in [k_lo, k_hi) that no prime q <= q2 kills.

        The bounds are checked EAGERLY, here, and the generator is a separate
        function -- a `yield` anywhere in this body would defer every check
        to the first `next()`.
        """
        if k_hi > k_ceil(self.n, self.fam):
            raise ValueError(f"x {k_hi} past the enforced ceiling "
                             f"{k_ceil(self.n, self.fam)}")
        if k_lo <= k_floor(self.q2, self.n, self.fam):
            raise ValueError(
                f"engines refuse to run at or below "
                f"{k_floor(self.q2, self.n, self.fam)}: a kill by q <= q2 = "
                f"{self.q2} is only a proof of compositeness once the value "
                f"exceeds q, and the smallest value is x + "
                f"{min(constants(self.fam, self.n))}")
        return self._survivors(k_lo, k_hi, block)

    def _survivors(self, k_lo, k_hi, block):
        k0 = int(k_lo)
        while k0 < k_hi:
            k1 = min(k0 + block, int(k_hi))
            alive = np.ones(k1 - k0, dtype=bool)
            for q in self.primes:
                for u in self.table[q]:
                    first = (u - k0) % q
                    if first < alive.size:
                        alive[first::q] = False
            idx = np.nonzero(alive)[0]
            if idx.size:
                # Python ints, not u64: this engine is the parity reference
                # for a range that runs past 2^64.
                yield [k0 + int(i) for i in idx]
            k0 = k1

    def survives(self, k):
        """The same decision, one candidate at a time, in Python ints."""
        k = int(k)
        return all(k % q not in st for q, st in self._sets().items())

    def _sets(self):
        if not hasattr(self, "_frozen"):
            self._frozen = {q: frozenset(v) for q, v in self.table.items()}
        return self._frozen

    # ------------------------------------------------------------ classify
    def run_length(self, k, cap=None):
        """The run of x = k (poly_reference.run_length, with huntlib's
        chain): 0 outside the domain, else the leading constants whose
        value is prime.  A proof below k_proof(n, F), a thirteen-base
        strong probable-prime chain above it."""
        cap = run_of(self.fam, self.n) + 6 if cap is None else int(cap)
        return run_length_fast(self.fam, k, cap=cap)

    def hunt(self, k_lo, k_hi, cap=None):
        """[(x, run)] for every survivor whose run reaches the filter's."""
        out = []
        need = run_of(self.fam, self.n)
        for chunk in self.survivors(k_lo, k_hi):
            for k in chunk:
                r = self.run_length(int(k), cap=cap)
                if r >= need:
                    out.append((int(k), r))
        return out


# --------------------------------- gates -----------------------------------

def _filters(fam):
    """A spread of filters, always including the open one."""
    top = frontier(fam) + 1
    return sorted({1, 3, 5, 8, 10, top - 2, top - 1, top, top + 3})


def g3_table_matches_divisibility():
    """The constructed killed set must equal direct divisibility, BOTH ways,
    for every family; and every unit but the forced one is refused."""
    checked = 0
    for fam in FAMILIES:
        for n in _filters(fam):
            fs = forms(fam, n)
            for q in primerange(2, 300):
                built = set(killed_residues(q, n, fam))
                direct = set(forbidden_k_residues(q, n, fam))
                if built != direct:
                    return False, (f"G3 FAIL: {fam} n={n} q={q} "
                                   f"built={sorted(built)} direct={sorted(direct)}")
                if len(built) != w_count(q, n, fam) or len(built) != w(q, n, fam):
                    return False, f"G3 FAIL: {fam} n={n} q={q}: |K| disagrees"
                for u in built:                 # and the kill is a real kill
                    if not any((a * pow(u, e, q) + b) % q == 0
                               for a, b, e in fs):
                        return False, (f"G3 FAIL: {fam} n={n} q={q} residue "
                                       f"{u} kills nothing")
                checked += 1
    # CLASS SPACE: the t residues q kills, mapped back through
    # x = r + unit*t, must be exactly the x residues q kills -- both
    # directions, same size; a prime of the unit kills no t at all; and the
    # class is what the ORACLE says survives.
    cls, classes = 0, {}
    for fam in FAMILIES:
        for n in _filters(fam):
            unit = forced_unit(n, fam)
            r = unit_residue(n, fam, unit)
            classes.setdefault(fam, set()).add((r, unit))
            free = [x for x in range(unit) if all(
                x % q not in forbidden_k_residues(q, n, fam)
                for q in primerange(2, UNIT_UPTO) if unit % q == 0)]
            if free != [r]:
                return False, (f"G3 FAIL: {fam} n={n}: the oracle leaves the "
                               f"classes {free} mod {unit} free, the engine "
                               f"sweeps {r}")
            for q in primerange(2, 300):
                kt = killed_residues(q, n, fam, unit)
                direct = set(forbidden_k_residues(q, n, fam))
                if unit % q == 0:
                    if kt:
                        return False, (f"G3 FAIL: {fam} n={n}: q={q} divides "
                                       f"the unit but kills {kt}")
                    continue
                back = {(r + unit * t) % q for t in kt}
                if back != direct or len(kt) != len(direct):
                    return False, (f"G3 FAIL: {fam} n={n} unit {unit} q={q}: "
                                   f"class-space kills map to {sorted(back)}, "
                                   f"x-space kills are {sorted(direct)}")
                cls += 1
    # the one-form index (n = 1 on three families) forces 2 alone
    want = {"A165234": {(5, 6), (1, 2)}, "A230663": {(1, 6), (1, 2)},
            "A092120": {(1, 6)}, "A347537": {(1, 6), (1, 2)}}
    if classes != want:
        return False, f"G3 FAIL: the forced classes are {classes}, expected {want}"
    refused = 0
    for fam in FAMILIES:
        n = frontier(fam) + 1
        u = forced_unit(n, fam)
        for unit in (7, 5 * u, 7 * u, 30030, 4, 2 * u, 67):
            try:
                assert_unit(n, fam, unit)
                return False, f"G3 FAIL: unit {unit} accepted for {fam} n={n}"
            except ValueError:
                refused += 1
    opens = "; ".join("%s x == %d (mod %d)" % ((fam,) + forced_class(frontier(fam) + 1, fam))
                      for fam in FAMILIES)
    return True, (f"G3 ok: constructed K(q,n,F) == direct divisibility in both "
                  f"directions at all {checked} (q < 300, n, F), with |K| equal "
                  f"to w_count and to w; in class space ({cls} (q, n, F) "
                  f"cases) the t kills map back exactly onto the x kills "
                  f"through x = r + unit*t, the unit's own primes kill "
                  f"nothing, and r is the one class the oracle leaves free -- "
                  f"{opens} at the open indices, and 1 (mod 2) alone at the "
                  f"one-form index; {refused} inadmissible units (a prime "
                  f"that is not forced, 30030, non-squarefree) are refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, every family,
    from n = 5 to each open index."""
    checks = 0
    windows = []
    for fam in FAMILIES:
        top = frontier(fam) + 1
        windows += [(fam, 5, 128, 70_000, 400_000),
                    (fam, 9, 64, 2_000_000, 4_000_000),
                    (fam, top, 32, 50_000_000, 4_000_000)]
    for fam, n, q2, k_lo, span in windows:
        eng = CpuEngine(n, fam, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        cs = constants(fam, n)
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            hi = min(c0 + (1 << 22), k_lo + span)
            # residues of a window that may start past 2^64: the window is
            # (c0 mod q) + i, i < 2^22, in int64
            idx = np.arange(0, hi - c0, dtype=np.int64)
            ok = np.ones(idx.size, dtype=bool)
            for q in smalls:
                base = (c0 % q)
                for c in cs:
                    ok &= (base + idx + (c % q)) % q != 0
            want.update(c0 + int(i) for i in idx[ok].tolist())
        if got != want:
            bad = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: {fam} n={n} window {k_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {bad}")
        if not want:
            return False, f"G4 FAIL: {fam} n={n} window is empty -- vacuous"
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on "
                  f"{len(windows)} populated windows ({checks} survivors; "
                  f"every family, from n = 5 to each open index)")


# Filters a dense CPU sweep from the bottom of the line affords in a gate.
# The exception zone (to 1024) holds terms on every family -- A165234's
# a(11) = 11 and a(29) = 29 have runs past any filter here -- so the gate
# reads the zone by brute force and requires its hits to be known terms,
# and then requires the FIRST prime the engine meets above the zone with a
# run of at least the filter's to be the least known term above the zone
# of index >= the filter: A165234 at n = 10 (a(10) = 5,939,831); A230663 at
# n = 7 (a(8) = 14,713 comes BEFORE a(7) = 21,559 -- a later index met
# first) and at n = 10 (a(10) = 8,123,233); A092120 at n = 5 (a(5) =
# 53,593) and at n = 9 (a(15) = 409,333 comes first, six indices up);
# A347537 at n = 7 (a(7) = 1,093) and at n = 9 (a(10) = 430,879 first).
G5_TERMS = {"A165234": (10,), "A230663": (7, 10), "A092120": (5, 9),
            "A347537": (7, 9)}


def g5_rederive_knowns():
    """The CPU engine finds known terms of EVERY family end-to-end, and
    FIRST: the sweep starts at the bottom of the line, the exception zone
    is covered by brute force and every hit in it is a known term, and the
    first prime the engine meets above the zone with a run of at least the
    filter's must be the least known term of index >= n above the zone,
    with a run of EXACTLY its index's (poly_reference.first_reach)."""
    found = []
    for fam, ns in G5_TERMS.items():
        for n in ns:
            q2 = 1024
            need = run_of(fam, n)
            eng = CpuEngine(n, fam, q2=q2)
            floor_k = k_floor(q2, n, fam)
            for x, r in prefix_hits(fam, n, q2, floor=need):
                # a zone hit is the known term of its index, or a census
                # value whose index a smaller known term settled
                if KNOWN[fam].get(index_of(fam, r), x + 1) > x:
                    return False, (f"G5 FAIL: {fam}: the zone holds {x} with run "
                                   f"{r}, a first occurrence nobody published")
            m, target = first_reach(fam, n, above=floor_k)
            # a hit whose index was settled BELOW it (by a term in the
            # zone: A092120's a(7) = 67 has primes of run 7 above the
            # zone before a(5)) is a census value, not a first occurrence
            hits = [(x, r) for x, r in eng.hunt(floor_k + 1, target + 1, cap=64)
                    if KNOWN[fam].get(index_of(fam, r), x) >= x]
            if not hits or min(hits) != (target, run_of(fam, m)):
                return False, (f"G5 FAIL: {fam}: the first run >= {need} above "
                               f"the zone came out {min(hits) if hits else None}, "
                               f"expected a({m}) = {target}")
            found.append(f"{fam} a({m}) at filter {n}")
    return True, ("G5 ok: CPU engine re-derived " + ", ".join(found) +
                  " end-to-end as the FIRST prime above the exception zone "
                  "with a run of at least the filter's, from the bottom of "
                  "the line (the zone brute-forced, every hit in it a known "
                  "term -- A165234's a(11) = 11 and a(29) = 29 among them), "
                  "each with a run of exactly its OEIS index's")


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW on real candidates, the
    domain predicate included: a composite p reads 0, and every known term
    reads EXACTLY its index in both."""
    seen = 0
    for fam in FAMILIES:
        top = frontier(fam)
        xs = [2, 3, 5, 7, 9, 15, 25, 2913, 12345679, 10 ** 12 + 39, KNOWN[fam][top],
              KNOWN[fam][top] + 6, KNOWN[fam][top] - 6, KNOWN[fam][min(top, 9)],
              2 ** 64 + 13, 10 ** 30 + 57]
        eng = CpuEngine(top + 1, fam, q2=2048)
        for k in xs:
            a = eng.run_length(k, cap=24)
            b = oracle_run_length(fam, k, cap=24)
            if a != b:
                return False, (f"G6 FAIL: {fam} x={k} engine run {a} != "
                               f"oracle run {b}")
            if a > 0 and not in_domain(fam, k):
                return False, f"G6 FAIL: {fam} x={k}: a run outside the domain"
            seen += 1
        for n in sorted(KNOWN[fam]):
            x = KNOWN[fam][n]
            r = run_of(fam, n)
            if eng.run_length(x, cap=64) != r or oracle_run_length(fam, x) != r:
                return False, (f"G6 FAIL: {fam} a({n}) does not read exactly "
                               f"run {r} in both implementations")
            seen += 2
    # the small cases, in the entries' own words: 3 has run 2 on A165234
    # (5 and 11 prime, 21 = 3 * 7), 5 has run 4 (7, 13, 23, 37; 55); 29 has
    # run 28; a composite reads 0; 43 has run 38 on A230663 (Euler's 41,
    # shifted); 7 has run 6 on A092120 (11, 23, 43, 71, 107, 151; 203 =
    # 7 * 29) and run 5 on A347537 (11, 37, 127, 347, 787; 1561 = 7 * 223,
    # the entry's own example)
    if (run_length_fast("A165234", 3) != 2 or run_length_fast("A165234", 5) != 4
            or run_length_fast("A165234", 29) != 28
            or run_length_fast("A165234", 9) != 0 or run_length_fast("A230663", 43) != 38
            or run_length_fast("A092120", 7) != 6 or run_length_fast("A347537", 7) != 5
            or oracle_run_length("A165234", 9) != 0):
        return False, "G6 FAIL: the small cases read wrong"
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates across every family (2^64 + 13 and 10^30 + 57 "
                  f"among them), every known term reads EXACTLY its index's "
                  f"run uncapped, a composite p reads 0, and the entries' "
                  f"own examples read as the entries say (3 has run 2 and 29 "
                  f"run 28 on A165234, 43 run 38 on A230663, 7 run 6 on "
                  f"A092120 and run 5 on A347537)")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: the proof crossing tight to one x per (n, F), the
    ceiling huntlib's K_CEIL and above every crossing, and the last filter
    the engine can express tight to its residue list (module docstring)."""
    import poly_gpu as _gpu
    if _gpu.NRES_MAX != FORMS_MAX:
        return False, (f"G10 FAIL: FORMS_MAX = {FORMS_MAX} but the GPU tail "
                       f"holds {_gpu.NRES_MAX} residues a prime")
    for fam in FAMILIES:
        for n in range(offset(fam), frontier(fam) + 12):
            c = k_proof(n, fam)
            fs = forms(fam, n)
            if max(value(f, c - 1) for f in fs) >= MR_VALID_BELOW:
                return False, (f"G10 FAIL: the largest deterministic x for "
                               f"({n}, {fam}) leaves the deterministic MR zone")
            if max(value(f, c) for f in fs) < MR_VALID_BELOW:
                return False, (f"G10 FAIL: the proof crossing for ({n}, {fam}) "
                               f"is not the bound: x = {c} is still deterministic")
            top = k_ceil(n, fam)
            if top != _ceiling.K_CEIL or top <= c:
                return False, f"G10 FAIL: the {fam} ceiling at n = {n} is {top}"
        if any(K_CEIL <= x for x in FOUND[fam].values()):
            return False, f"G10 FAIL: a {fam} find sits at or above the ceiling"
        nm = n_max(fam)
        if not nforms(fam, nm) <= FORMS_MAX < nforms(fam, nm + 1):
            return False, f"G10 FAIL: {fam}'s last index with <= {FORMS_MAX} forms is not {nm}"
        if nm <= frontier(fam) + 1:
            return False, f"G10 FAIL: {fam} has no open index the engine can express"
        if MR_VALID_BELOW - k_proof(nm, fam) > 10 ** 6:
            return False, f"G10 FAIL: {fam}'s shifts are not small at n = {nm}"
    rows = "; ".join("%s n = %d: x < %.6g, last index %d (%d forms)"
                     % (f, frontier(f) + 1, k_proof(frontier(f) + 1, f), n_max(f),
                        nforms(f, n_max(f)))
                     for f in FAMILIES)
    return True, ("G10 ok: the proof crossing IS the deterministic MR bound "
                  "(3.317e24) less the largest shift, tight to one x at "
                  f"every index to the frontier + 11 of every family ({rows}; "
                  "the shifts are under a million at the last filter, so the "
                  "crossing is the bound itself); the ceiling on the term is "
                  "huntlib's K_CEIL = %.4g on every family; and the last "
                  "filter is the one whose forms fill the GPU tail's residue "
                  "list (FORMS_MAX = NRES_MAX = %d), tight to one index"
                  % (K_CEIL, FORMS_MAX))


def value(f, x):
    a, b, e = f
    return a * int(x) ** e + b


GATES = [g3_table_matches_divisibility, g4_cpu_matches_oracle,
         g6_run_length_matches_oracle, g10_values_stay_inside_the_mr_bound,
         g5_rederive_knowns]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
