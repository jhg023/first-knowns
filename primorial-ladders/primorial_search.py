"""primorial_search.py -- the CPU engine for the primorial shift ladders.

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
word bounds the search (OPTIMIZATION.md 2.7, from the first commit; the
A115785 line at n = 16 starts at 53# = 3.3e19, past 2^64, and every later
index is further out).

WHAT IS SWEPT.  The term itself, p or m, on ONE line per index.  The forced
primes pin it to a single CLASS: 1 (mod 6) on A115785, 5 (mod 6) on
A115786, 1 (mod 6) on A145743 from n = 3 (primorial_reference G2c).  The
machinery sweeps a general class x = r + u*t and this engine marks the dense
x line knowing nothing of r or u, which is what makes the parity gate a
check of the forcing as well as of the sieve.  u is DERIVED per filter
(`forced_unit`), and a unit whose primes are not all forced is refused
(`assert_unit`), because a unit is a coverage claim.

THE DOMAIN.  A145743's m must be COMPOSITE, which no sieve expresses: the
classification (run_length) gives a prime m a run of 0.  On the primorial
families the term is itself a form, so the sieve tests it like any other.

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24.  The largest value at x is x itself on A115785,
x + prime(n)# on A115786 and x + 4n^2 on A145743, so the PROOF CROSSING
k_proof(n, F) is the bound less that constant: 3.317e24 to five figures
everywhere (the shift is additive).  Past it a discovery is proved by
CERTIFICATE -- and a value x -+ prime(k)# has NO multiplier x term +- 1
structure, so each value is proved by huntlib.certificate.prove's own
bounded search on N -+ 1.  Rule 5h then asks for a measurement rather than
the 1e40 default: random structureless primes at 1e25, 1e30, 1e35 and 1e40
were each proved by the first search, 46 of 46, the worst in 0.4 s
(OPTIMIZATION_LOG.md Measurement 1), so the ceiling IS huntlib's K_CEIL =
1e40 and the certificate drill in launch.py proves this project's own
values at the height.  A115785's line passes the ceiling between n = 26
(101# = 2.3e38) and n = 27 (103# = 2.4e40): the campaign ends there.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, every family, in x space and in class space; a unit that is
not forced -- or not squarefree -- is refused), G4 (CPU survivors == the
oracle's definition of a survivor on populated windows), G5 (CPU re-derives
published terms of every family end-to-end as FIRST occurrences from each
index's own floor, with the exception zone covered by brute force), G6
(engine run lengths == sympy BPSW, the domain predicate included), G10
(numeric hygiene: the crossing tight to one x at every index, the ceiling
above it and from huntlib).
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
from primorial_reference import (FAMILIES, FOUND, KNOWN, constants,  # noqa: E402
                                 family, floor_x, forbidden_k_residues,
                                 forms, frontier, in_domain, kind,
                                 primorial_k, run_length as oracle_run_length,
                                 term, w, w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing search runs over (the log and the documents
# name the forced class; nothing in the engines depends on it).
UNIT_UPTO = 64

# THE CEILING ON THE TERM: huntlib's, MEASURED here rather than assumed
# (module docstring; rule 5h).  EXCLUSIVE.
K_CEIL = _ceiling.K_CEIL


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof at index n -- the
    deterministic Miller-Rabin bound less the largest constant.  EXCLUSIVE:
    k_proof - 1 is the largest x whose every value stays under the bound
    (G10 pins both halves)."""
    return MR_VALID_BELOW - max(constants(fam, n))


def k_ceil(n, fam):
    """The enforced ceiling on the term, every family: K_CEIL.  EXCLUSIVE."""
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2, n, fam):
    """The smallest x the engines will sweep (EXCLUSIVE).

    A kill by q is only a proof of compositeness when the value EXCEEDS q.
    The smallest value is x + min(constants): x - prime(n)# on A115785, x
    itself elsewhere (x + 4 on A145743), so a sieve to q2 is valid from the
    first x with that value above q2.
    """
    return int(q2) - min(constants(fam, n))


def zone(q2, n, fam):
    """(lo, hi) INCLUSIVE: the integers between the definition's floor and
    the engine's that a sweep at depth q2 must cover by brute force, or None
    when the engine's floor is below the definition's (every monotone
    family at its campaign filter)."""
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
    exactly one residue class: 6 on the primorial families from n = 1, 2
    then 6 (from n = 3) on A145743.  Derived per filter and never stored:
    a unit is a coverage claim."""
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
    """The domain predicate with huntlib's chain: a prime on the primorial
    families, a composite (>= 4) on A145743."""
    x = int(x)
    if kind(fam) == "primorial":
        return x >= 2 and mr_is_prime(x)
    return x >= 4 and not mr_is_prime(x)


def run_length_fast(fam, x, cap=64):
    """The oracle's run_length with huntlib's deterministic Miller-Rabin
    (a strong probable-prime chain past the proof crossing)."""
    fam, x = family(fam), int(x)
    if not in_domain_fast(fam, x):
        return 0
    f = FAMILIES[fam]
    r = 0
    while r < cap:
        c = (f["sign"] * primorial_k(r + 1) if f["kind"] == "primorial"
             else 4 * (r + 1) ** 2)
        v = x + c
        if v < 2 or not mr_is_prime(v):
            break
        r += 1
    return r


def prefix_hits(fam, n, q2, floor=1, cap=64):
    """[(x, run)] over the exception zone of index n at depth q2 -- every
    integer between the definition's floor and the engine's, in the forced
    class, with a run of at least `floor` -- by huntlib's chain (the
    oracle's own prefix_hits is the sympy version).  Empty when there is
    no zone."""
    fam = family(fam)
    z = zone(q2, n, fam)
    if z is None:
        return []
    lo, hi = z
    r0, u = forced_class(n, fam)
    out = []
    x = lo + ((r0 - lo) % u)
    while x <= hi:
        r = run_length_fast(fam, x, cap=cap)
        if r >= floor:
            out.append((x, r))
        x += u
    return out


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
        """The run of x = k (primorial_reference.run_length, with huntlib's
        chain): 0 outside the domain, else the leading constants whose
        value is prime.  A proof below k_proof(n, F), a thirteen-base
        strong probable-prime chain above it."""
        cap = self.n + 6 if cap is None else int(cap)
        return run_length_fast(self.fam, k, cap=cap)

    def hunt(self, k_lo, k_hi, cap=None):
        """[(x, run)] for every survivor whose run reaches the filter."""
        out = []
        for chunk in self.survivors(k_lo, k_hi):
            for k in chunk:
                r = self.run_length(int(k), cap=cap)
                if r >= self.n:
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
    want = {"A115785": {(1, 6)}, "A115786": {(5, 6)}, "A145743": {(1, 2), (1, 6)}}
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
                  f"{opens} at the open indices; {refused} inadmissible units "
                  f"(a prime that is not forced, 30030, non-squarefree) are "
                  f"refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, every family
    -- including A115785 windows just above their primorial."""
    checks = 0
    windows = (("A115785", 5, 128, primorial_k(5) + 200, 400_000),
               ("A115785", 9, 64, primorial_k(9) + 100, 2_000_000),
               ("A115785", 16, 32, primorial_k(16) + 40, 2_000_000),
               ("A115786", 6, 128, 70_000, 400_000),
               ("A115786", 11, 64, 2_000_000, 4_000_000),
               ("A115786", 17, 32, 50_000_000, 4_000_000),
               ("A145743", 5, 128, 70_000, 400_000),
               ("A145743", 9, 64, 2_000_000, 4_000_000),
               ("A145743", 14, 32, 30_000_000, 4_000_000))
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
                  f"every family, from n = 5 to each open index, A115785's "
                  f"just above 11#, 23# and 53# = 3.3e19 > 2^64)")


# Published terms a dense CPU sweep from each index's floor affords in a
# gate: A115785's a(7) and a(8) (lines of 5.8e5 and 1.0e7 above 17# and
# 19#), A115786's a(11) (2.3e8 above a(10)) and A145743's a(11) (2.7e6
# above a(10)); a(9) of A115785 is 4e7 of line and a(12) of A115786 5e8,
# minutes of dense sieve, so the GPU canaries take those.
G5_TERMS = {"A115785": (7, 8), "A115786": (11,), "A145743": (11,)}


def g5_rederive_knowns():
    """The CPU engine finds published terms of EVERY family end-to-end, and
    FIRST: the sweep starts at the definition's own floor (prime(n)# + 2
    on A115785, a(n-1) elsewhere), with the exception zone between that
    and the engine floor covered by brute force, so the claim is about the
    line and not about a window.  Riders: a(12) of A145743 is above a(11)
    with a(11) having run 11 exactly, so no rider hides a FIRST claim."""
    found = []
    for fam, ns in G5_TERMS.items():
        for n in ns:
            q2 = 1024
            eng = CpuEngine(n, fam, q2=q2)
            target = KNOWN[fam][n]
            lo = floor_x(fam, n)
            z = zone(q2, n, fam)
            pre = [x for x, r in prefix_hits(fam, n, q2, floor=n)] if z else []
            if pre and min(pre) < target:
                return False, (f"G5 FAIL: {fam}: the exception zone holds "
                               f"{min(pre)} below a({n}) = {target}")
            start = max(lo, k_floor(q2, n, fam) + 1)
            hits = eng.hunt(start, target + 1)
            if not hits or min(k for k, _ in hits) != target:
                return False, (f"G5 FAIL: {fam} least run-{n} from {lo} "
                               f"came out {min(hits)[0] if hits else None}, "
                               f"expected {target}")
            found.append(f"{fam} a({n})")
    return True, ("G5 ok: CPU engine re-derived " + ", ".join(found) +
                  " end-to-end as FIRST occurrences from each index's own "
                  "floor (A115785's just above its primorial, the exception "
                  "zone brute-forced), each at its OEIS index")


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW on real candidates, the
    domain predicate included: a composite p reads 0 on the primorial
    families, a PRIME m reads 0 on A145743, and every published term is
    full at its own index in both."""
    seen = 0
    for fam in FAMILIES:
        top = frontier(fam)
        xs = [3, 7, 9, 15, 25, 2913, 12345679, 10 ** 12 + 39, KNOWN[fam][top],
              KNOWN[fam][top] + 6, KNOWN[fam][top] - 6, KNOWN[fam][min(top, 9)],
              primorial_k(16) + 1, 2 ** 64 + 1]
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
        for n in range(1, top + 1):
            x = KNOWN[fam][n]
            if eng.run_length(x, cap=n) != n or oracle_run_length(fam, x, cap=n) != n:
                return False, (f"G6 FAIL: {fam} a({n}) is not a full run at its "
                               f"own index in both implementations")
            seen += 2
    # THE DOMAIN: 9 = A145743's a(1) is composite and reads 1 there (9 + 4 =
    # 13); 7 is prime and reads 0 there though 7 + 4 = 11 is prime; 9 reads
    # 0 on the primorial families (composite), 5 reads 1 on A115785 (5 - 2
    # = 3, 5 - 6 < 2) and 2 on A115786 (7, 11)
    if (run_length_fast("A145743", 9) != 1 or run_length_fast("A145743", 7) != 0
            or run_length_fast("A115785", 9) != 0 or run_length_fast("A115785", 5) != 1
            or run_length_fast("A115786", 5) != 2 or oracle_run_length("A145743", 7) != 0):
        return False, "G6 FAIL: the domain predicate is wrong on the small cases"
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates across every family (a 2^64 + 1 and a 53# + 1 "
                  f"among them), every published term full at its own OEIS "
                  f"index, and the domain is honoured: a prime m reads 0 on "
                  f"A145743 (7 does, 9 reads 1), a composite p reads 0 on the "
                  f"primorial families")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: the proof crossing tight to one x per (n, F), the
    ceiling huntlib's K_CEIL and above every crossing, and the ceiling
    MEASURED for this project's structureless values (module docstring)."""
    for fam in FAMILIES:
        for n in range(1, frontier(fam) + 12):
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
    # A115785's line leaves the ceiling between n = 26 and n = 27
    if not floor_x("A115785", 26) < K_CEIL <= floor_x("A115785", 27):
        return False, "G10 FAIL: A115785's last index under the ceiling moved"
    rows = "; ".join("%s n = %d: x < %.4g" % (f, frontier(f) + 1,
                                               k_proof(frontier(f) + 1, f))
                     for f in FAMILIES)
    return True, ("G10 ok: the proof crossing IS the deterministic MR bound "
                  "(3.317e24) less the largest constant, tight to one x at "
                  f"every index to the frontier + 11 of every family ({rows}; "
                  "the shift is additive, so every crossing is 3.317e24 to "
                  "five figures); the ceiling is huntlib's K_CEIL = %.4g on "
                  "every family, above every crossing, A115785's line leaves "
                  "it between n = 26 (101#) and n = 27 (103#), and the "
                  "certificate route at the height is measured "
                  "(OPTIMIZATION_LOG.md Measurement 1) and drilled in the "
                  "launcher" % K_CEIL)


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
