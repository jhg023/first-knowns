"""clique_search.py -- the CPU engine for the clique ladders.

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
  * construction: the killed set K(q,n,F) is built here algebraically, one
    modular inverse per form; the oracle builds it by walking every residue
    and testing divisibility.  G3 pins the two against each other.

If both engines agreed because they shared a subroutine, the parity gate
would be theatre.  They share the answer and nothing else.

Representation.  Candidates are Python integers here and (x, off) pairs on
the GPU -- x = base + off with base a host-side big int and off < W, so no
machine word bounds the search (OPTIMIZATION.md 2.7, from the first commit).

WHAT IS SWEPT.  x itself, the published term, on ONE line for every filter.
The forced primes pin x to a single CLASS, x == r (mod u), and r is
generally not 0 (x == 2 mod 6 for A093483, 9 mod 30 for A103828), so where
the other ladders sweep the multiples of a unit this one sweeps a class:
the GPU engine runs t with x = r + u*t and the host maps back.  This engine
marks the dense x line and knows nothing of r or u, which is what makes the
parity gate a check of the forcing as well as of the sieve.  u is DERIVED
per filter (`forced_unit`) -- it grows as the sequence does -- and a unit
whose primes are not all forced is refused (`assert_unit`), because a unit
is a coverage claim.

THE FORM LIST IS STATE.  The conditions at index n are built from
a(1..n-1) (clique_reference.forms), so an engine for index n can only be
built once a(n-1) is known, and a campaign registers each find with the
oracle (clique_reference.register) before it builds the next engine.

Primality note.  huntlib's Miller-Rabin is DETERMINISTIC below
MR_VALID_BELOW = 3.317e24.  The largest value at x is 2x + 1 for the two
families that carry that form and x + a(n-1) + 1 < 2x + 1 for the others, so
the PROOF CROSSING k_proof(n, F) is about 1.66e24 and 3.3e24 -- ABOVE every
term this campaign can reach in weeks (the modelled a(22) sit at 3e23-2e24),
so for once the classification IS the proof for nearly the whole hunt.

Past the crossing the values have no structure: V - 1 = x + a(i) is just an
integer, not m*k.  That is the case CLAUDE.md 5h carves out, and the honest
limit is measured rather than assumed: `huntlib.ceiling.subproof_rate`
proves 12 of 12 random primes at every height from 1e25 to 1e40 in under
half a second each (OPTIMIZATION_LOG.md, Measurement 1), because a 40-digit
V - 1 factors completely by rho and ECM in well under the certificate
budget.  So the ceiling is huntlib.ceiling.K_CEIL = 1e40 here too, G10
re-measures the rate at it on every battery, and a value that cannot be
proved is reported in the evidence file's `unproved` list rather than
hidden.

Gates here: G3 (constructed killed set == oracle divisibility, both
directions, every family, in x space and in class space; a unit that is
not forced -- or not squarefree -- is refused), G4 (CPU survivors ==
the oracle's definition of a survivor on populated windows), G5 (CPU
re-derives published terms of every family end-to-end as FIRST occurrences
above their predecessor), G6 (engine run lengths == sympy BPSW, every
published term full at its own index), G10 (numeric hygiene: the crossing
tight to one x, the measured ceiling above it).
"""

import pathlib as _pathlib
import sys as _sys
from functools import lru_cache as _lru_cache

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import ceiling as _ceiling                        # noqa: E402
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.ceiling import K_CEIL                             # noqa: E402
from huntlib.primes import MR_VALID_BELOW, mr_is_prime         # noqa: E402
from clique_reference import (FAMILIES, FOUND, KNOWN, extra,   # noqa: E402
                              family, forbidden_k_residues, forms, frontier,
                              run_length as oracle_run_length, term, terms, w,
                              w_count)

Q2_DEFAULT = 65536           # sieve depth (primes the engines test)

# The largest prime the forcing search runs over (the log and the documents
# name the forced class; nothing in the engines depends on it).
UNIT_UPTO = 64


def k_proof(n, fam):
    """Where the CLASSIFICATION stops being a proof at index n -- the
    deterministic Miller-Rabin bound rearranged over every form.

    Below this x every value a*x + b is under MR_VALID_BELOW, so every
    primality decision the hunt makes is a PROOF.  EXCLUSIVE: k_proof - 1 is
    the largest x whose every value stays under the bound (G10 pins both
    halves).
    """
    return min((MR_VALID_BELOW - 1 - b) // a + 1 for a, b in forms(fam, n))


def k_ceil(n, fam):
    """The enforced ceiling on x: huntlib.ceiling.K_CEIL.  The values here
    are unstructured, so this is rule 5h's EXCEPTION, justified by a
    measurement (module docstring) that G10 repeats.  EXCLUSIVE."""
    family(fam)
    int(n)
    return K_CEIL


def k_floor(q2, n, fam):
    """The smallest x the engines will sweep (EXCLUSIVE).

    A kill by q is only a proof of compositeness when the value EXCEEDS q.
    Every form's value is at least x (x + a(i) + 1, 2x + 1, x itself), so a
    sieve to q2 is valid from the first x > q2, at every filter.
    """
    family(fam)
    int(n)
    return int(q2)


def killed_residues(q, n, fam, unit=1):
    """K(q,n,F) = { -b * a^-1 mod q : (a, b) in forms(F, n), q not | a }.

    The algebraic construction -- one modular inverse per form -- as opposed
    to the oracle's walk over every residue.  Deduplicated rather than
    counted.

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


# The prefix a(1..n-1) never changes once it exists (clique_reference.register
# refuses to), so everything derived from (n, F) alone may be cached.
@_lru_cache(maxsize=None)
def _forms(n, fam):
    return tuple(forms(fam, n))


def _xkills(q, n, fam):
    return {(-b * pow(a, -1, q)) % q for a, b in _forms(n, fam) if a % q}


def _free(q, n, fam):
    """The residues of x mod q that no form kills."""
    return sorted(set(range(q)) - _xkills(int(q), int(n), family(fam)))


def forced_unit(n, fam, upto=UNIT_UPTO):
    """The product of the primes FORCED at index n -- those q that leave x
    exactly one residue class.

    Derived per filter and never stored: it GROWS as the sequence does (a
    prime becomes forced the moment a new term fills its last class but
    one), it differs between families (6 for A093483 at its open index, 30
    for A103828), and a unit is a coverage claim.
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
        self.shifts = [t + 1 for t in terms(self.fam, self.n)]
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
                f"exceeds q, and the smallest value is about x")
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
        definition, clique_reference): 0 if an extra form fails, else 1 + the
        leading shift forms that are prime.  Full is n.  A proof below
        k_proof(n, F), a thirteen-base strong probable-prime chain above it."""
        k = int(k)
        cap = self.n if cap is None else min(int(cap), self.n)
        for a, b in self.extra:
            if not mr_is_prime(a * k + b):
                return 0
        r = 1
        for c in self.shifts:
            if r >= cap or not mr_is_prime(k + c):
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
    for every family; and every unit but 1 is refused."""
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
                    if not any((a * u + b) % q == 0 for a, b in fs):
                        return False, (f"G3 FAIL: {fam} n={n} q={q} residue "
                                       f"{u} kills nothing")
                checked += 1
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
    # The traps: a unit with a prime that is NOT forced there (7 leaves two
    # or three classes at every open index; 210 and 30030 are the linear
    # ladders' habit), and one that is not squarefree.
    refused = 0
    for fam in FAMILIES:
        n = frontier(fam) + 1
        u = forced_unit(n, fam)
        for unit in (7, 7 * u, 30030, 4, 2 * u, 67):
            try:
                assert_unit(n, fam, unit)
                return False, f"G3 FAIL: unit {unit} accepted for {fam} n={n}"
            except ValueError:
                refused += 1
    classes = "; ".join(f"{fam} x == %d (mod %d)" % forced_class(frontier(fam) + 1, fam)
                        for fam in FAMILIES)
    return True, (f"G3 ok: constructed K(q,n,F) == direct divisibility in both "
                  f"directions at all {checked} (q < 300, n, F), with |K| equal "
                  f"to w_count and to w; in class space ({cls} (q, n, F) cases) "
                  f"the t kills map back exactly onto the x kills through "
                  f"x = r + unit*t, the unit's own primes kill nothing, and r "
                  f"is the one class the oracle leaves free -- {classes} at "
                  f"the open indices; {refused} inadmissible units (a prime "
                  f"that is not forced, 30030, non-squarefree) are refused")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on populated windows, every family.

    The oracle's notion of a survivor is the definition: no value a*x + b has
    a prime factor q <= q2 (the value that IS q is ruled out by
    k_lo > k_floor).
    """
    checks = 0
    windows = (("A093483", 6, 128, 70_000, 400_000),
               ("A093483", 18, 32, 50_000_000, 4_000_000),
               ("A103828", 12, 64, 2_000_000, 4_000_000),
               ("A037100", 19, 32, 30_000_000, 4_000_000),
               ("A119752", 15, 32, 30_000_000, 4_000_000),
               ("A119751", 9, 64, 2_000_000, 4_000_000),
               ("A133761", 17, 32, 30_000_000, 4_000_000))
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
            for a, b in forms(fam, n):
                for q in smalls:
                    # q | a*x + b, tested on residues: b runs to 1e18 and an
                    # int64 product over the window would overflow
                    ok &= ((ks % q) * (a % q) + (b % q)) % q != 0
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
                  f"{len(windows)} populated windows ({checks} survivors; all "
                  f"six families, n = 6 to 19)")


# Published terms a dense CPU sweep from their predecessor affords in a gate.
G5_TERMS = {"A093483": (9, 10, 11, 12), "A103828": (8, 9, 10, 11),
            "A037100": (8, 9, 10, 11), "A119752": (9, 10, 11),
            "A119751": (8, 9, 10), "A133761": (7, 8, 9)}


def g5_rederive_knowns():
    """The CPU engine finds published terms of EVERY family end-to-end, and
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
            xs = [3, 2910, 12345678, 10 ** 12 + 39, KNOWN[fam][top],
                  KNOWN[fam][top] + 30, KNOWN[fam][min(top, n)]]
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
    return True, (f"G6 ok: engine run lengths == sympy BPSW on {seen} "
                  f"candidates; every published term is a full run at its own "
                  f"index and the newest term is full at every earlier one")


def g10_values_stay_inside_the_mr_bound():
    """Numeric hygiene: the proof crossing tight to one x per (n, F), and the
    ceiling -- rule 5h's exception, so MEASURED here on every battery: random
    unstructured primes at the ceiling must all be proved."""
    for fam in FAMILIES:
        for n in range(2, frontier(fam) + 2):
            c = k_proof(n, fam)
            fs = forms(fam, n)
            if max(a * (c - 1) + b for a, b in fs) >= MR_VALID_BELOW:
                return False, (f"G10 FAIL: the largest deterministic x for "
                               f"({n}, {fam}) leaves the deterministic MR zone")
            if max(a * c + b for a, b in fs) < MR_VALID_BELOW:
                return False, (f"G10 FAIL: the proof crossing for ({n}, {fam}) "
                               f"is not the bound: x = {c} is still deterministic")
            top = k_ceil(n, fam)
            if top != K_CEIL or top <= c:
                return False, f"G10 FAIL: the {fam} ceiling at n = {n} is {top}"
        if any(K_CEIL <= x for x in FOUND[fam].values()):
            return False, f"G10 FAIL: a {fam} find sits at or above K_CEIL"
    ok, n, worst = _ceiling.subproof_rate(K_CEIL // 3, samples=8)
    if ok != n or worst > _ceiling.CERT_BUDGET_S:
        return False, (f"G10 FAIL: at the ceiling only {ok} of {n} random "
                       f"unstructured primes were proved (slowest {worst:.1f} "
                       f"s) -- the ceiling is not justified at K_CEIL")
    lo = min(k_proof(frontier(f) + 1, f) for f in FAMILIES)
    hi = max(k_proof(frontier(f) + 1, f) for f in FAMILIES)
    return True, ("G10 ok: the proof crossing IS the deterministic MR bound "
                  "(3.317e24) rearranged over every form, tight to one x at "
                  "every index of every family -- x < %.4g where 2x + 1 is a "
                  "form, %.4g elsewhere, above every term the campaign can "
                  "reach in weeks; the ceiling is huntlib.ceiling.K_CEIL = "
                  "%.4g, the values are UNSTRUCTURED there, and %d of %d "
                  "random primes at it were proved by certificate just now "
                  "(slowest %.2f s)" % (lo, hi, K_CEIL, ok, n, worst))


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
