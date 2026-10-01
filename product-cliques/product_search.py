"""product_search.py -- the CPU engine for the product cliques.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is independent
in three ways that matter:

  * shape: this engine marks arithmetic progressions into a DENSE array over
    the x line and uses no wheel at all.  The GPU engine never materialises
    the x line: it generates only the residues that survive a wheel and
    tests each one against packed forbidden-residue tables, bailing out at
    the first kill.  A wheel bug on the GPU side therefore shows up as a
    parity failure rather than hiding inside a shared table.
  * arithmetic: plain Python `%` and numpy slice-strided kills, never the
    GPU's Barrett magic-multiply reduction.
  * construction: the killed set K(q,n,F) is built here algebraically -- one
    modular inverse per product form, and this file's OWN Tonelli-Shanks for
    the square roots of -1 that x^2 + 1 kills -- while the oracle walks every
    residue and tests divisibility (and takes its square roots from sympy).
    G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (x, off) pairs on
the GPU -- x = base + off with base a host-side big int and off < W, so no
machine word bounds the search (OPTIMIZATION.md 2.7, from the first commit).

WHAT IS SWEPT.  x itself, the published term, on ONE line for every filter.
The forced primes pin x to a single CLASS, x == r (mod u).  Here that class
is always 0 (mod 6) (product_reference: every form is 1 at x == 0, and only
2 and 3 are ever forced), but the machinery inherited from clique-ladders
sweeps a general class x = r + u*t and this engine marks the dense x line
knowing nothing of r or u, which is what makes the parity gate a check of
the forcing as well as of the sieve.  u is DERIVED per filter
(`forced_unit`), and a unit whose primes are not all forced is refused
(`assert_unit`), because a unit is a coverage claim.

THE FORM LIST IS STATE.  The conditions at index n are built from
a(1..n-1) (product_reference.forms), so an engine for index n can only be
built once a(n-1) is known, and a campaign registers each find with the
oracle (product_reference.register) before it builds the next engine.

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24.  The largest value at x is a(n-1)*x + 1 (or
x^2 + 1 in A219761, once x passes a(n-1)), so the PROOF CROSSING k_proof(n, F)
is about 3.3e24 / a(n-1): 1.8e11 at A034881's open index, a hundred times
BELOW its frontier, and 1.8e12 at A219761's, about where the model puts that
family's open term -- so nearly every classification this campaign makes is
a probable-prime chain and every discovery past the crossing is proved by
certificate.  That is rule 5h's BEST case, not a problem: every value less
one is a(i)*x (or x^2), completely factored the moment x is, since the
prefix terms were factored when they were found.  So the ceiling is
huntlib.ceiling.K_CEIL = 1e40 on the term, as measured there, and
launch.certify_run proves a whole run on ONE factorization of x.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, both families, in x space and in class space; a unit that is
not forced -- or not squarefree -- is refused), G4 (CPU survivors ==
the oracle's definition of a survivor on populated windows), G5 (CPU
re-derives published terms of both families end-to-end as FIRST occurrences
above their predecessor), G6 (engine run lengths == sympy BPSW, every
published term full at its own index), G10 (numeric hygiene: the crossing
tight to one x at every index, the ceiling K_CEIL above it).
"""

import pathlib as _pathlib
import sys as _sys
from functools import lru_cache as _lru_cache

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.ceiling import K_CEIL                             # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from product_reference import (FAMILIES, FOUND, KNOWN, extra,  # noqa: E402
                               family, forbidden_k_residues, forms, frontier,
                               run_length as oracle_run_length, term, terms,
                               value, w, w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing search runs over (the log and the documents
# name the forced class; nothing in the engines depends on it).
UNIT_UPTO = 64


def _iroot(v, e):
    """floor(v^(1/e)) for v >= 0, e in (1, 2)."""
    if e == 1:
        return int(v)
    from math import isqrt
    return isqrt(int(v))


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof at index n -- the
    deterministic Miller-Rabin bound rearranged over every form.

    Below this x every value a*x^e + b is under MR_VALID_BELOW, so every
    primality decision the hunt makes is a PROOF.  EXCLUSIVE: k_proof - 1 is
    the largest x whose every value stays under the bound (G10 pins both
    halves).
    """
    return min(_iroot((MR_VALID_BELOW - 1 - b) // a, e) + 1
               for a, b, e in forms(fam, n))


def k_ceil(n, fam):
    """The enforced ceiling on x: huntlib.ceiling.K_CEIL, rule 5h's default.
    The values have multiplier x term + 1 structure (every value less one is
    a(i)*x or x^2), so one factorization of x proves a run at any height and
    the ceiling is what huntlib.ceiling measured that factorization to cost.
    EXCLUSIVE."""
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2, n, fam):
    """The smallest x the engines will sweep (EXCLUSIVE).

    A kill by q is only a proof of compositeness when the value EXCEEDS q.
    Every value is at least x + 1 (a(1)*x + 1 = x + 1; the other product
    forms and x^2 + 1 are larger), so a sieve to q2 is valid from the first
    x > q2, at every filter.
    """
    family(fam)
    int(n)
    return int(q2)


def sqrt_mod_prime(c, q):
    """The square roots of c mod the prime q, sorted -- Tonelli-Shanks,
    written here so that the CPU engine owes the oracle nothing (the oracle
    takes its roots from sympy)."""
    c %= q
    if q == 2:
        return [c]
    if c == 0:
        return [0]
    if pow(c, (q - 1) // 2, q) != 1:
        return []
    if q % 4 == 3:
        r = pow(c, (q + 1) // 4, q)
        return sorted({r, q - r})
    s, d = 0, q - 1
    while d % 2 == 0:
        s, d = s + 1, d // 2
    z = 2
    while pow(z, (q - 1) // 2, q) != q - 1:
        z += 1
    m, cc, t, r = s, pow(z, d, q), pow(c, d, q), pow(c, (d + 1) // 2, q)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % q
            i += 1
        b = pow(cc, 1 << (m - i - 1), q)
        m, cc = i, b * b % q
        t, r = t * cc % q, r * b % q
    return sorted({r, q - r})


def killed_residues(q, n, fam, unit=1):
    """K(q,n,F) = the union over forms (a, b, e) of the x with
    a*x^e + b == 0 (mod q): -b*a^-1 for a product form, the square roots of
    -b*a^-1 for x^2 + 1, nothing for a form whose leading coefficient q
    divides.

    The algebraic construction -- one modular inverse per form, and a
    Tonelli-Shanks per quadratic -- as opposed to the oracle's walk over
    every residue.  Deduplicated rather than counted.

    CLASS SPACE.  The forced primes pin x to ONE class, x == r (mod unit)
    (`unit_residue`), so the GPU engine sweeps t with x = r + unit*t, and the
    residues of t that q kills are those of x carried through the map:
    t == (k - r) * unit^-1 (mod q) for each killed k, q not dividing unit.  A
    prime OF the unit kills no t at all -- the class was chosen so that it
    cannot -- and returns the empty list.  The map is a bijection of Z/q, so
    the sizes, hence the survival curve and the wheel counts, are unchanged
    (G3 pins this against the x-space set).  `unit = 1` is x space itself.
    Whether a unit is ADMISSIBLE at a filter is `assert_unit`'s job.
    """
    unit = int(unit)
    if unit % q == 0:
        return []
    ks = _xkills(int(q), int(n), family(fam))
    if unit == 1:
        return sorted(ks)
    r, inv = unit_residue(n, fam, unit), pow(unit, -1, q)
    return sorted({((k - r) * inv) % q for k in ks})


# The prefix a(1..n-1) never changes once it exists (product_reference.
# register refuses to), so everything derived from (n, F) alone may be cached.
@_lru_cache(maxsize=None)
def _forms(n, fam):
    return tuple(forms(fam, n))


@_lru_cache(maxsize=1 << 16)
def _qroots(a, b, q):
    """Roots of a*x^2 + b mod q (a mod q nonzero), memoised: they depend on
    neither the index nor the family."""
    return tuple(sqrt_mod_prime((-b * pow(a, -1, q)) % q, q))


def _xkills(q, n, fam):
    out = set()
    for a, b, e in _forms(n, fam):
        am = a % q
        if not am:
            continue
        if e == 1:
            out.add((-b * pow(am, -1, q)) % q)
        else:
            out.update(_qroots(am, b, q))
    return out


def _free(q, n, fam):
    """The residues of x mod q that no form kills."""
    return sorted(set(range(q)) - _xkills(int(q), int(n), family(fam)))


def forced_unit(n, fam, upto=UNIT_UPTO):
    """The product of the primes FORCED at index n -- those q that leave x
    exactly one residue class.

    Derived per filter and never stored: a unit is a coverage claim.  It is
    6 at every index from 3 in both families (product_reference G2c, G2d),
    and 2 at index 2.
    """
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
    class per prime of the unit -- and it raises.  Squarefree for the same
    reason: forcing pins x mod q, never mod q^2.
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


class CpuEngine:
    """Segmented sieve over the dense x line, no wheel."""

    def __init__(self, n, fam, q2=Q2_DEFAULT):
        self.n = int(n)
        self.fam = family(fam)
        self.q2 = q2
        self.extra = list(extra(self.fam))
        self.mults = list(terms(self.fam, self.n))
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
                f"exceeds q, and the smallest value is x + 1")
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
        """The run of x = k at this index, in INDEX units (the oracle's
        definition, product_reference): 0 if an extra form fails, else 1 +
        the leading product forms a(i)*x + 1 that are prime.  Full is n.  A
        proof below k_proof(n, F), a thirteen-base strong probable-prime
        chain above it."""
        k = int(k)
        cap = self.n if cap is None else min(int(cap), self.n)
        for f in self.extra:
            if not mr_is_prime(value(f, k)):
                return 0
        r = 1
        for a in self.mults:
            if r >= cap or not mr_is_prime(a * k + 1):
                break
            r += 1
        return r

    def hunt(self, k_lo, k_hi, cap=None):
        """[(x, run)] for every survivor whose run is full."""
        out = []
        for chunk in self.survivors(k_lo, k_hi):
            for k in chunk:
                r = self.run_length(int(k), cap=cap)
                if r >= self.n:
                    out.append((int(k), r))
        return out


# --------------------------------- gates -----------------------------------

def _filters(fam, count=6):
    """A spread of the indices that exist for `fam`, always including the
    open one."""
    top = frontier(fam) + 1
    picks = sorted({2, 3, 5, 8, 11, top - 2, top - 1, top})
    return [n for n in picks if 2 <= n <= top][-count - 2:]


def g3_table_matches_divisibility():
    """The constructed killed set must equal direct divisibility, BOTH ways,
    for both families; the Tonelli-Shanks roots are roots; and every unit
    but the forced one is refused."""
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
    # the square roots on their own, on every prime to 5000 and a few
    # residues each: squared, they are the residue, and there are as many as
    # Euler's criterion says
    roots = 0
    for q in primerange(2, 5000):
        for c in (q - 1, 2, 3, 5, q // 2):
            rs = sqrt_mod_prime(c, q)
            want = 1 if c % q == 0 or q == 2 else (
                2 if pow(c % q, (q - 1) // 2, q) == 1 else 0)
            if len(rs) != want or any(r * r % q != c % q for r in rs):
                return False, (f"G3 FAIL: Tonelli-Shanks gives {rs} for the "
                               f"square roots of {c} mod {q}")
            roots += 1
    # CLASS SPACE: the t residues q kills, mapped back through
    # x = r + unit*t, must be exactly the x residues q kills -- both
    # directions, same size; a prime of the unit kills no t at all; and the
    # class is what the ORACLE says survives (every free x mod unit is r).
    cls = 0
    for fam in FAMILIES:
        for n in _filters(fam):
            unit = forced_unit(n, fam)
            r = unit_residue(n, fam, unit)
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
    # The traps: a unit with a prime that is NOT forced there (5 and 7 leave
    # at least half their classes at every index; 30 and 30030 are the other
    # ladders' habit), and one that is not squarefree.
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
    classes = "; ".join(f"{fam} x == %d (mod %d)" % forced_class(frontier(fam) + 1, fam)
                        for fam in FAMILIES)
    return True, (f"G3 ok: constructed K(q,n,F) == direct divisibility in both "
                  f"directions at all {checked} (q < 300, n, F), with |K| equal "
                  f"to w_count and to w; this engine's own Tonelli-Shanks "
                  f"gives exactly Euler's count of square roots, each squaring "
                  f"to its residue, on {roots} (q < 5000, c) cases; in class "
                  f"space ({cls} (q, n, F) cases) the t kills map back exactly "
                  f"onto the x kills through x = r + unit*t, the unit's own "
                  f"primes kill nothing, and r is the one class the oracle "
                  f"leaves free -- {classes} at the open indices; {refused} "
                  f"inadmissible units (a prime that is not forced, 30030, "
                  f"non-squarefree) are refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, both families.

    The oracle's notion of a survivor is the definition: no value a*x^e + b
    has a prime factor q <= q2 (the value that IS q is ruled out by
    k_lo > k_floor).
    """
    checks = 0
    windows = (("A034881", 6, 128, 70_000, 400_000),
               ("A034881", 11, 64, 2_000_000, 4_000_000),
               ("A034881", 16, 32, 50_000_000, 4_000_000),
               ("A219761", 6, 128, 70_000, 400_000),
               ("A219761", 9, 64, 2_000_000, 4_000_000),
               ("A219761", 12, 32, 30_000_000, 4_000_000))
    for fam, n, q2, k_lo, span in windows:
        eng = CpuEngine(n, fam, q2=q2)
        got = set()
        for chunk in eng.survivors(k_lo, k_lo + span):
            got.update(int(x) for x in chunk)
        smalls = list(primerange(2, q2 + 1))
        want = set()
        for c0 in range(k_lo, k_lo + span, 1 << 22):
            ks = np.arange(c0, min(c0 + (1 << 22), k_lo + span), dtype=np.int64)
            ok = np.ones(ks.size, dtype=bool)
            for a, b, e in forms(fam, n):
                for q in smalls:
                    # q | a*x^e + b, tested on residues: a runs to 1e13 and an
                    # int64 product over the window would overflow
                    xe = (ks % q) ** e % q
                    ok &= (xe * (a % q) + (b % q)) % q != 0
            want.update(int(x) for x in ks[ok].tolist())
        if got != want:
            bad = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: {fam} n={n} window {k_lo}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {bad}")
        if not want:
            return False, f"G4 FAIL: {fam} n={n} window is empty -- vacuous check"
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on "
                  f"{len(windows)} populated windows ({checks} survivors; "
                  f"both families, n = 6 to each open index, the quadratic "
                  f"form included)")


# Published terms a dense CPU sweep from their predecessor affords in a gate
# (a(n-1) must clear the q2 = 1024 floor: A034881's a(8) is the first to).
G5_TERMS = {"A034881": (9, 10, 11), "A219761": (7, 8, 9)}


def g5_rederive_knowns():
    """The CPU engine finds published terms of BOTH families end-to-end, and
    FIRST: the sweep starts just above a(n-1), which is the definition's own
    floor, so the claim is about the line and not about a window."""
    found = []
    for fam, ns in G5_TERMS.items():
        for n in ns:
            q2 = 1024
            eng = CpuEngine(n, fam, q2=q2)
            lo = term(fam, n - 1) + 1
            target = KNOWN[fam][n]
            if lo <= k_floor(q2, n, fam):
                return False, f"G5 FAIL: {fam} a({n - 1}) is under the engine floor"
            hits = eng.hunt(lo, target + 1)
            if not hits or min(k for k, _ in hits) != target:
                return False, (f"G5 FAIL: {fam} least full run above a({n - 1}) "
                               f"came out {min(hits)[0] if hits else None}, "
                               f"expected {target}")
            found.append(f"{fam} a({n})")
    return True, ("G5 ok: CPU engine re-derived " + ", ".join(found) +
                  " end-to-end as FIRST occurrences above their predecessors")


def g6_run_length_matches_oracle():
    """huntlib's Miller-Rabin chain == sympy's BPSW on real candidates, and
    every published term is full at its own index in both."""
    seen = 0
    for fam in FAMILIES:
        top = frontier(fam)
        for n in _filters(fam):
            eng = CpuEngine(n, fam, q2=2048)
            xs = [3, 2910, 12345678, 10 ** 12 + 38, KNOWN[fam][top],
                  KNOWN[fam][top] + 30, KNOWN[fam][min(top, n)], 156, 18]
            for k in xs:
                a = eng.run_length(k)
                b = oracle_run_length(fam, k, n)
                if a != b:
                    return False, (f"G6 FAIL: {fam} n={n} x={k} engine run {a} "
                                   f"!= oracle run {b}")
                seen += 1
        for n in range(5, top + 1):
            eng = CpuEngine(n, fam, q2=64)
            x = KNOWN[fam][n]
            if eng.run_length(x) != n or oracle_run_length(fam, x, n) != n:
                return False, (f"G6 FAIL: {fam} a({n}) is not a full run at its "
                               f"own index in both implementations")
            # and a LATER term is full at every earlier index too: a clique
            # is a clique whatever order it is read in
            if n < top and eng.run_length(KNOWN[fam][top]) != n:
                return False, (f"G6 FAIL: {fam} a({top}) is not compatible "
                               f"with the first {n - 1} terms")
            seen += 2
    # the extra form decides alone: 18 is a term of A034881 and fails
    # A219761's x^2 + 1 (18^2 + 1 = 325), so it reads 0 there
    if CpuEngine(4, "A219761", q2=64).run_length(18) != 0:
        return False, "G6 FAIL: a failed x^2 + 1 does not read run 0"
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates; every published term is a full run at its own "
                  f"index and the newest term is full at every earlier one; "
                  f"a failed x^2 + 1 reads 0")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: the proof crossing tight to one x per (n, F), the
    quadratic form included, and the ceiling K_CEIL above it."""
    for fam in FAMILIES:
        for n in range(2, frontier(fam) + 2):
            c = k_proof(n, fam)
            fs = forms(fam, n)
            if max(value(f, c - 1) for f in fs) >= MR_VALID_BELOW:
                return False, (f"G10 FAIL: the largest deterministic x for "
                               f"({n}, {fam}) leaves the deterministic MR zone")
            if max(value(f, c) for f in fs) < MR_VALID_BELOW:
                return False, (f"G10 FAIL: the proof crossing for ({n}, {fam}) "
                               f"is not the bound: x = {c} is still deterministic")
            top = k_ceil(n, fam)
            if top != K_CEIL or top <= c:
                return False, f"G10 FAIL: the {fam} ceiling at n = {n} is {top}"
        if any(K_CEIL <= x for x in FOUND[fam].values()):
            return False, f"G10 FAIL: a {fam} find sits at or above K_CEIL"
    rows = "; ".join("%s n = %d: x < %.4g" % (f, frontier(f) + 1,
                                               k_proof(frontier(f) + 1, f))
                     for f in FAMILIES)
    below = all(k_proof(frontier(f) + 1, f) <= term(f, frontier(f))
                for f in FAMILIES)
    return True, ("G10 ok: the proof crossing IS the deterministic MR bound "
                  "(3.317e24) rearranged over every form -- a(i)*x + 1 and "
                  "x^2 + 1 -- tight to one x at every index of both families "
                  f"({rows}{', below both frontiers, so every discovery here is proved by certificate' if below else ''}); "
                  "the ceiling is huntlib.ceiling.K_CEIL = %.4g, where every "
                  "value less one is a(i)*x or x^2 and one factorization of x "
                  "proves a run (huntlib.ceiling.GATES measures that cost at "
                  "the height; launch's certificate drill proves this "
                  "project's own values there)" % K_CEIL)


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
