"""ap_search.py -- the CPU engine for A053647.

An independent fast implementation of the same mathematics as the GPU
engine, and the permanent other half of the parity gate.  It is independent
in three ways that matter:

  * arithmetic: plain Python/numpy `%` and slice-strided kills, never the
    GPU's Barrett magic-multiply;
  * shape: it sieves a FLAT array of p-offsets, one entry per integer, with
    the mod-30 wheel applied as a tiled mask; the GPU sieves a BITMAP whose
    index is (wheel period, lane) and never represents a non-coprime p at
    all;
  * construction: the killed residues here are `(-j * P(n)) % q` computed
    directly in Python integers; the GPU derives the same set by a residue
    WALK (start at 0, subtract P(n) mod q, n times) with no multiplication
    and no Python integers anywhere.

If the two engines agreed because they shared a subroutine the parity gate
would be theatre.  They share nothing but the answer.

REPRESENTATION.  Candidates are carried as `(base, offset)` with
p = base + offset, base a Python integer and offset a u64 -- so one engine
spans the whole range and there is no second engine waiting at 2^64
(OPTIMIZATION.md 2.7), even though p passes 2^64 around a(21) and the
VALUES p + j*P(n) pass it at a(16).  Nothing on either side of the
device boundary ever holds p itself.

WHY THE ENGINE REFUSES TO SIEVE BELOW ITS OWN DEPTH.  A value p + j*P(n)
can BE the prime q that would otherwise kill it, and the definition counts
that as prime.  Above p = q2 no value can be as small as any sieve prime,
so the exception cannot arise; below it, it can.  Rather than carry a
special case through both engines, both refuse, and `launch.py`'s low pass
covers [2, floor) against the oracle instead -- a few seconds, once, and
the least-claim stays contiguous from 2.

PRIMALITY NOTE.  The values are p + j*P(n) <= p + (n-1)*P(n), which is
about 4.9e20 at a(16) and 2.0e24 at a(18) -- all below huntlib's
deterministic Miller-Rabin bound of 3.317e24, so a positive there is a
PROOF and this project needs no certificate for its first three open
terms.  At a(19) the values reach 1.4e26 and it does; that is what
huntlib.certificate is for, and g10 below pins exactly where the crossing
happens so no future edit can assume determinism it does not have.

Gates here: G3 (constructed residue table == the oracle's direct
divisibility, both directions), G4 (CPU survivors == oracle survivors on
populated windows), G5 (CPU re-derives a(11) and a(12) end-to-end as FIRST
occurrences), G10 (numeric hygiene at the Miller-Rabin bound).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.primes import (MR_VALID_BELOW, mr_is_prime,       # noqa: E402
                            sprp_base2)
from ap_reference import (KNOWN, P_FLOOR, W0, difference,       # noqa: E402
                          forbidden_residues)

Q2_DEFAULT = 1 << 16          # sieve depth (primes tested by the engines)
P_CEIL = 10**26               # enforced: the last rung of every campaign
BLOCK = 1 << 23               # p-offsets per numpy block

# The census floor: chains at or above this depth are COUNTED per length in
# the checkpoint and shown in every [STATUS] line; below it nothing is
# recorded anywhere.  Six, from the measured distribution at the production
# shape (n = 16, q2 = 4096, p ~ 4e13, 6617 classified survivors):
#
#     depth >= 4   1 per 6.0e7 of p-line        depth >= 8   1 per 6.0e9
#     depth >= 5   1 per 1.9e8                  depth >= 10  1 per 6.0e9
#     depth >= 6   1 per 5.0e8                  (each step ~0.32 of the last)
#
# so the floor sits where an event is still frequent enough to be a useful
# health readout (~40 a second at the campaign rate) and already far too
# frequent to narrate -- which is exactly the line CONVENTIONS.md draws
# between counting and logging.
DEPTH_FLOOR = 6

# A chain PROVED shorter than the census floor never has to be resolved
# exactly, which is what lets the cheap first pass below do 99.8% of the
# work.  Tied to the floor deliberately: raising one without the other
# would either record an inexact depth or pay for exactness nobody reads.
DEPTH_EXACT_FROM = DEPTH_FLOOR

_WHEEL = np.array([all(r % q for q in (2, 3, 5)) for r in range(W0)],
                  dtype=bool)


class CpuEngine:
    """Flat segmented sieve over p, carried as (base, offset)."""

    def __init__(self, n, q2=Q2_DEFAULT):
        self.n = int(n)
        self.q2 = int(q2)
        self.d = difference(n)
        # 2, 3 and 5 are the wheel; every other prime below q2 can still
        # kill.  For q | P(n) the n killed residues collapse to {0}, which
        # the formula produces on its own -- no special case.
        self.primes = [q for q in primerange(7, q2)]
        self.forb = {q: sorted({(-j * self.d) % q for j in range(self.n)})
                     for q in self.primes}
        self.forbset = {q: frozenset(v) for q, v in self.forb.items()}
        self.floor = max(P_FLOOR, self.q2)

    # ---------------------------------------------------------------- sieve
    def survivors(self, base, span, block=BLOCK):
        """Yield uint64 arrays of offsets o with base + o surviving the sieve.

        `base` and `span` are Python integers; the offsets are u64 and the
        caller re-forms p = base + o.  Both ends are half-open: [base,
        base + span).
        """
        base, span = int(base), int(span)
        if base < self.floor:
            raise ValueError(
                f"the engine refuses to sieve below max(P_FLOOR, q2) = "
                f"{self.floor}: down there a value can BE the sieve prime "
                f"that kills it (see the module docstring)")
        if base + span > P_CEIL:
            raise ValueError(f"p {base + span} is past the enforced ceiling "
                             f"{P_CEIL}")
        off = 0
        while off < span:
            size = min(block, span - off)
            b = base + off
            phase = b % W0
            reps = size // W0 + 2
            alive = np.tile(_WHEEL, reps)[phase:phase + size].copy()
            for q in self.primes:
                bm = b % q
                for f in self.forb[q]:
                    start = (f - bm) % q
                    if start < size:
                        alive[start::q] = False
            idx = np.nonzero(alive)[0]
            if idx.size:
                yield (idx + off).astype(np.uint64)
            off += size

    def survives(self, p):
        """True iff the sieve keeps p -- the residue table consulted
        directly, one candidate at a time, in Python integers.

        The same decision `survivors` makes by strided marking, without
        forming any array and at ANY depth.  This is the leg a verification
        uses when it re-derives a find on a DIFFERENT sieve depth from the
        campaign's: membership of one p is all such a check ever needs, and
        answering exactly that avoids handing a windowed sieve a range it
        was never sized for.
        """
        p = int(p)
        if any(p % q == 0 for q in (2, 3, 5)):
            return False
        return all(p % q not in self.forbset[q] for q in self.primes)

    # ------------------------------------------------------------- classify
    def chain_depth(self, p, cap=None):
        """How many of p, p + P(n), ... are prime, from j = 0, exactly
        wherever it counts.

        Two passes, and the first one is legitimate because a strong test
        has an ASYMMETRIC verdict: a failure is a PROOF of compositeness, a
        pass is only evidence.  So a base-2-only chain (one modular
        exponentiation per value instead of seven) yields a rigorous UPPER
        BOUND on the depth -- it can stop too late, never too early.  If
        that bound lands below DEPTH_EXACT_FROM the true depth is below it
        too, proved, and nothing that gets recorded depends on which of
        0, 1, 2 it was.  If the bound reaches DEPTH_EXACT_FROM the chain is
        redone with the full huntlib base set and the exact value returned.

        Every depth this project writes down still comes from the full base
        set.  What the cheap pass buys is that ~93% of survivors are
        dismissed at one exponentiation instead of seven, because the
        commonest survivor is one whose p is composite.
        """
        p = int(p)
        cap = self.n if cap is None else int(cap)
        j = 0
        while j < cap and sprp_base2(p + j * self.d):
            j += 1
        if j < DEPTH_EXACT_FROM:
            return j                    # proved short; nothing records it
        j = 0
        while j < cap and mr_is_prime(p + j * self.d):
            j += 1
        return j

    def hunt(self, base, span, min_depth=None):
        """[(p, depth)] for every survivor whose chain reaches min_depth."""
        want = self.n if min_depth is None else int(min_depth)
        out = []
        for chunk in self.survivors(base, span):
            for o in chunk.tolist():
                p = int(base) + int(o)
                dep = self.chain_depth(p)
                if dep >= want:
                    out.append((p, dep))
        return out


# --------------------------------- gates -----------------------------------

def g3_table_matches_divisibility():
    """The engine's residue table must equal direct divisibility, BOTH ways.

    One direction stops the engine from emitting a candidate it should have
    killed; the other stops it from killing one it should have kept, which
    is the failure a parity gate against another engine using the same
    construction could never see.
    """
    for n in (12, 16, 19):
        eng = CpuEngine(n, q2=400)
        for q in eng.primes:
            built = set(eng.forb[q])
            direct = forbidden_residues(q, n)
            if built != direct:
                return False, (f"G3 FAIL: n={n} q={q} built={sorted(built)} "
                               f"direct={sorted(direct)}")
            for r in built:            # and the kill really is a kill
                if not any((r + j * eng.d) % q == 0 for j in range(n)):
                    return False, (f"G3 FAIL: n={n} q={q} residue {r} kills "
                                   f"nothing")
            want = 1 if eng.d % q == 0 else n
            if len(built) != want:
                return False, (f"G3 FAIL: n={n} q={q} has {len(built)} killed "
                               f"residues, expected {want}")
    return True, ("G3 ok: the engine's killed residues == direct "
                  "divisibility in both directions, every prime 7 <= q < 400 "
                  "at n = 12, 16, 19, with |F| = 1 exactly for q | P(n)")


def g4_cpu_matches_oracle():
    """CPU survivor set == the oracle's, on POPULATED windows.

    The oracle's notion of a survivor is the definition: no value
    p + j*P(n) has a prime factor below q2 (except where the value is that
    prime, which cannot happen above the engine floor).
    """
    checks = 0
    for n, q2, base, span in ((8, 1024, 10**4, 2 * 10**5),
                              (13, 2048, 10**6, 4 * 10**5),
                              (16, 4096, 10**7, 2 * 10**6)):
        eng = CpuEngine(n, q2=q2)
        got = set()
        for chunk in eng.survivors(base, span):
            got.update(base + int(o) for o in chunk.tolist())
        want = {p for p in range(base, base + span)
                if all(p % q for q in (2, 3, 5))
                and _oracle_survivor(p, n, q2)}
        if got != want:
            diff = sorted(got ^ want)[:4]
            return False, (f"G4 FAIL: n={n} window {base}+{span}: "
                           f"{len(got)} engine vs {len(want)} oracle, "
                           f"symmetric difference {diff}")
        if not want:
            return False, f"G4 FAIL: n={n} window is empty -- vacuous check"
        checks += len(want)
    return True, (f"G4 ok: engine survivors == oracle survivors on 3 "
                  f"populated windows ({checks} survivors, n = 8, 13, 16)")


def _oracle_survivor(p, n, q2):
    """The definition, spelled out -- no engine involved."""
    d = difference(n)
    for q in primerange(7, q2):
        for j in range(n):
            if (p + j * d) % q == 0:
                return False
    return True


def g5_rederive_knowns():
    """The CPU engine finds a(11) and a(12) end-to-end, and finds them FIRST.

    Least-claim drills, not mere hits: the engine has to produce the known
    value as the SMALLEST p its sweep accepts, from the floor up.
    """
    for n in (11, 12):
        eng = CpuEngine(n, q2=4096)
        hits = eng.hunt(eng.floor, KNOWN[n] - eng.floor + 1)
        firsts = [p for p, dep in hits if dep >= n]
        if not firsts or min(firsts) != KNOWN[n]:
            return False, (f"G5 FAIL: least p with a full chain came out "
                           f"{min(firsts) if firsts else None}, expected "
                           f"{KNOWN[n]}")
    return True, ("G5 ok: CPU engine re-derived a(11) = %d and a(12) = %d "
                  "end-to-end as FIRST occurrences from the floor"
                  % (KNOWN[11], KNOWN[12]))


def g10_values_and_the_mr_bound():
    """Numeric hygiene: state the bound, and prove we know where it fails.

    The deterministic Miller-Rabin bound is a property of the VALUES, and
    for this problem the largest value is about (n-1)*P(n) -- essentially
    independent of p, because P(n) dwarfs every p this hunt will reach.  So
    the crossing happens at a particular TERM INDEX, not at a particular
    depth, and this gate pins which one.
    """
    top = {}
    for n in range(15, 24):
        top[n] = (n - 1) * difference(n)
    det = [n for n in top if top[n] < MR_VALID_BELOW]
    if max(det) != 18:
        return False, (f"G10 FAIL: deterministic MR was expected to cover "
                       f"through a(18); it covers through a({max(det)})")
    if top[19] < MR_VALID_BELOW:
        return False, "G10 FAIL: a(19) values were expected past the bound"
    # and a term inside the range really is provable outright
    p = KNOWN[15]
    if not all(mr_is_prime(v) for v in
               (p + j * difference(15) for j in range(15))):
        return False, "G10 FAIL: a(15)'s values do not pass deterministic MR"
    return True, ("G10 ok: the largest value (n-1)*P(n) stays below "
                  "huntlib's deterministic MR bound (3.317e24) through "
                  "a(18) (2.0e24) and passes it at a(19) (1.4e26) -- so "
                  "a(16)-a(18) are PROVED by the engine chain and a(19) up "
                  "needs huntlib.certificate")


GATES = [g3_table_matches_divisibility, g4_cpu_matches_oracle,
         g10_values_and_the_mr_bound, g5_rederive_knowns]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
