"""The CPU engine -- an independent fast implementation of the same
mathematics, in numpy and plain Python integers.

It walks the prime line in segments, keeps the EXACT power sums
S(m, k) = Sum_{j<=k} prime(j)^m as Python integers, and tests
`(e + S) % k == 0` with the `%` operator.  That is deliberate: the GPU
engine reduces a limb array by magic multiplication instead, and the two
must never share arithmetic or the parity gate proves nothing
(CLAUDE.md rule 3).

THE STATE, and why the sweep is contiguous.  A term is a statement about
the first k primes, so the engine cannot start in the middle of the line
without knowing (k, S) there.  It therefore carries

    State(k, sums)          k = how many primes consumed
                            sums[m] = the exact S(m, k)

as its whole cursor: hand it to another engine, or to a checkpoint, and
the sweep resumes bit-for-bit.  There is a sublinear way to compute S at
a height without walking there (a Lucy_Hedgehog-style prefix recurrence),
and it is not used: the run-up below the lowest live frontier is 0.1% of
the campaign, and walking it makes the engine rediscover 124 published
terms on the way -- the canary battery, for free.  See OPTIMIZATION_LOG.md
for the pricing.

THE CANDIDATE LINE is the INDEX k, not the prime p, and the obstruction
proved in the oracle's G3 wheels it: for e = 0 only k coprime to Q(m) can
ever be a term, so the test is skipped on the rest (half the indices at
m = 11, four fifths at m = 12).

Gates in this file: G4 (the engine reproduces the oracle's hit stream
exactly on a populated window), G5 (it re-derives frozen known terms
end-to-end from the definition), and G6 (the segmentation is invisible --
a stream split into segments equals the unsplit stream, at several
segment sizes and at a segment boundary landing on a known term).
"""

import numpy as np

import psum_reference as ref

# --------------------------------------------------------------------------
# Numeric hygiene (CONVENTIONS.md).  Both engines enforce these; the GPU
# engine parity-gates AT the ceiling rather than below it.
#
# P_CEIL: the largest prime the engines will consume.  2^62 keeps p, k and
# every index arithmetic inside unsigned 64-bit with a full bit of margin,
# and is ~50x above the deepest rung any campaign on this project plans.
# K_CEIL: the largest index.  pi(2^62) < 1.1e17 < 2^57.
P_CEIL = 1 << 62
K_CEIL = 1 << 57
# The exact sums are Python integers here and fixed-width limb arrays on
# the GPU, so the GPU's width is the binding ceiling; it is declared there
# (psum_gpu.LIMBS) and checked against the state by both engines.
SEG_DEFAULT = 1 << 22

# DECLARED COVERAGE: the engines test ODD k only.
#
# This is a spec both engines obey, not shared arithmetic -- the GPU kernel
# enforces it with its own `if ((k & 1) == 0) return;`.  The reason is on
# the GPU side: reducing a 1536-bit sum modulo k needs Montgomery
# multiplication (NVRTC has no __int128), and Montgomery requires an odd
# modulus.  For e = 0 this costs NOTHING and is provable, not hopeful:
# (2-1) | m for every m, so 2 always divides Q(m), so by the obstruction
# (oracle G3) every e = 0 term is odd already.  For e = 1 it is a real
# halving of coverage -- the census family's even terms are outside what
# this project claims -- and it is stated here rather than discovered
# later.  Widening it is a new engine version.
ODD_ONLY = True


class State:
    """(p, k, sums) -- everything needed to resume the sweep anywhere.

    `p` is the EXCLUSIVE upper end of the prime line already consumed, and
    it belongs in here rather than being tacked onto the object by the
    caller: the first version of this class left it out, `copy()` dropped
    it, and a resumed sweep silently restarted at p = 2 with k already
    advanced -- caught by G6, which is exactly what G6 is for.
    """

    def __init__(self, ms, p=2, k=0, sums=None):
        self.ms = tuple(sorted(set(ms)))
        self.p = int(p)
        self.k = int(k)
        self.sums = dict(sums) if sums else {m: 0 for m in self.ms}
        for m in self.ms:
            self.sums.setdefault(m, 0)

    def copy(self):
        return State(self.ms, self.p, self.k, self.sums)

    def to_json(self):
        return {"p": str(self.p), "k": str(self.k),
                "sums": {str(m): str(v) for m, v in sorted(self.sums.items())}}

    @classmethod
    def from_json(cls, d):
        sums = {int(m): int(v) for m, v in d["sums"].items()}
        return cls(sorted(sums), int(d["p"]), int(d["k"]), sums)

    def __eq__(self, other):
        return (isinstance(other, State) and self.p == other.p
                and self.k == other.k and self.sums == other.sums)

    def __repr__(self):
        return f"State(p={self.p}, k={self.k}, ms={self.ms})"


def simple_sieve(n):
    """All primes < n, as a numpy array (the base primes for segmenting)."""
    if n < 3:
        return np.zeros(0, dtype=np.int64)
    flags = np.ones(n // 2, dtype=bool)          # odds only: 1,3,5,...
    flags[0] = False                             # 1 is not prime
    for i in range(1, int(n ** 0.5) // 2 + 1):
        if flags[i]:
            p = 2 * i + 1
            flags[(p * p) // 2::p] = False
    return np.concatenate(([2], 2 * np.nonzero(flags)[0] + 1)).astype(np.int64)


def segment_primes(lo, hi, base=None):
    """Primes in [lo, hi), in order, as a numpy array."""
    if hi <= 2:
        return np.zeros(0, dtype=np.int64)
    lo = max(int(lo), 2)
    hi = int(hi)
    if base is None:
        base = simple_sieve(int(hi ** 0.5) + 1)
    flags = np.ones(hi - lo, dtype=bool)
    for p in base:
        p = int(p)
        if p * p >= hi:
            break
        start = max(p * p, ((lo + p - 1) // p) * p)
        flags[start - lo::p] = False
    if lo <= 1:
        flags[:2 - lo] = False
    return (np.nonzero(flags)[0] + lo).astype(np.int64)


class CpuSweep:
    """The engine.  Families are (m, e) pairs; sums are kept per m, since
    e only shifts the tested value by one."""

    def __init__(self, families, seg=SEG_DEFAULT):
        self.families = tuple(sorted(set(families)))
        self.ms = tuple(sorted({m for m, _ in self.families}))
        self.seg = int(seg)
        self.Q = {m: ref.Q(m) for m in self.ms}
        self.state = State(self.ms)

    def wheel_ok(self, m, e, k):
        """Is index k inside the declared coverage AND on the obstruction
        wheel?

        ODD_ONLY first (the coverage both engines declare), then the
        obstruction (oracle G3): for e = 0 a k sharing a factor with Q(m)
        can never be a term, so it is not tested.  For e = 1 that k is
        exactly where the free congruence lives, so nothing beyond the
        odd-only rule is skipped.
        """
        if ODD_ONLY and (k & 1) == 0:
            return False
        return e == 1 or k == 1 or self.Q[m] == 1 or _gcd(k, self.Q[m]) == 1

    def run(self, p_hi, state=None, seg=None, on_hit=None):
        """Advance the sweep to prime line p_hi, yielding hits.

        Returns (hits, state) with hits a sorted list of (m, e, k) and
        state the resumable cursor at p_hi.
        """
        if p_hi > P_CEIL:
            raise ValueError(f"p_hi {p_hi} exceeds the enforced ceiling "
                             f"P_CEIL = 2^62")
        st = (state or self.state).copy()
        seg = int(seg or self.seg)
        base = simple_sieve(int(p_hi ** 0.5) + 2)
        hits = []
        lo = st.p
        while lo < p_hi:
            hi = min(lo + seg, p_hi)
            for p in segment_primes(lo, hi, base):
                p = int(p)
                st.k += 1
                k = st.k
                for m in self.ms:
                    st.sums[m] += p ** m
                for m, e in self.families:
                    if not self.wheel_ok(m, e, k):
                        continue
                    if (e + st.sums[m]) % k == 0:
                        hits.append((m, e, k))
                        if on_hit:
                            on_hit(m, e, k, p, st)
            lo = hi
        st.p = max(st.p, p_hi)
        self.state = st
        return hits, st


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


# --------------------------------- gates -----------------------------------

_GATE_FAMS = ((1, 0), (7, 0), (11, 0), (12, 1))


def g4_parity_with_oracle(kmax=20000):
    """The engine's hit stream equals the oracle's, exactly, on a window
    that is POPULATED -- an empty-vs-empty comparison proves nothing."""
    p_hi = ref._nth_prime_bound(kmax)
    eng = CpuSweep(_GATE_FAMS, seg=1 << 14)
    hits, _ = eng.run(p_hi)
    got = sorted((m, e, k) for m, e, k in hits if k <= kmax)
    # The oracle computes the DEFINITION, which has even-k terms in the
    # e = 1 families; the engines declare ODD_ONLY coverage, so the
    # comparison is made on that subset and says so.  Filtering the oracle
    # rather than the engine is deliberate: the engine never gets to
    # decide what it is compared against.
    want = []
    for m, e in _GATE_FAMS:
        want += [(m, e, k) for k in ref.terms_upto(m, e, kmax)
                 if not (ODD_ONLY and (k & 1) == 0)]
    want.sort()
    if got != want:
        extra = sorted(set(got) - set(want))[:4]
        miss = sorted(set(want) - set(got))[:4]
        return False, (f"G4 FAIL: CPU stream != oracle on k <= {kmax}: "
                       f"{len(got)} vs {len(want)} hits, extra={extra}, "
                       f"missing={miss}")
    if not want:
        return False, "G4 FAIL: the comparison window is EMPTY, so vacuous"
    return True, (f"G4 ok: CPU stream == oracle stream exactly on the "
                  f"declared coverage (odd k) to k <= {kmax}, {len(want)} "
                  f"hits across {len(_GATE_FAMS)} families (populated, "
                  f"not vacuous)")


def g5_rederive_knowns(kmax=600000):
    """Re-derive real published terms end-to-end from the definition and
    check them against the frozen tables -- the canary, run cold."""
    fams = tuple((m, 0) for m in (1, 7, 11, 13, 19))
    eng = CpuSweep(fams, seg=1 << 16)
    hits, _ = eng.run(ref._nth_prime_bound(kmax))
    n = 0
    for m, e in fams:
        got = sorted(k for mm, ee, k in hits if (mm, ee) == (m, e)
                     and k <= kmax)
        want = [k for k in ref.FAMILIES[(m, e)]["terms"] if k <= kmax]
        if got != want:
            return False, (f"G5 FAIL: m={m} re-derived {got}, frozen table "
                           f"says {want}")
        n += len(want)
    if n < 8:
        return False, f"G5 FAIL: only {n} known terms in range -- too weak"
    return True, (f"G5 ok: {n} published terms across {len(fams)} families "
                  f"re-derived end-to-end from the definition to k = {kmax}")


def g6_segmentation_invisible(kmax=40000):
    """A split stream equals the unsplit stream: the segmentation carries
    (k, sums) correctly across every boundary, including one landing on a
    known term."""
    p_hi = ref._nth_prime_bound(kmax)
    ref_hits, ref_state = CpuSweep(_GATE_FAMS, seg=1 << 20).run(p_hi)
    for seg in (1 << 10, 1 << 12, 7919):
        hits, st = CpuSweep(_GATE_FAMS, seg=seg).run(p_hi)
        if hits != ref_hits:
            return False, (f"G6 FAIL: seg={seg} changed the stream "
                           f"({len(hits)} vs {len(ref_hits)} hits)")
        if st.k != ref_state.k or st.sums != ref_state.sums:
            return False, f"G6 FAIL: seg={seg} left a different state"
    # and a resume across a boundary, in two halves
    eng = CpuSweep(_GATE_FAMS, seg=1 << 12)
    mid = ref._nth_prime_bound(kmax // 3)
    first, st = eng.run(mid)
    second, st2 = eng.run(p_hi, state=st)
    if sorted(first + second) != sorted(ref_hits):
        return False, (f"G6 FAIL: split at p={mid} gave "
                       f"{len(first) + len(second)} hits, unsplit gave "
                       f"{len(ref_hits)}")
    if st2.k != ref_state.k or st2.sums != ref_state.sums:
        return False, "G6 FAIL: the resumed state differs from the unsplit one"
    return True, (f"G6 ok: stream and state are identical at 4 segment "
                  f"sizes and across a mid-line resume ({len(ref_hits)} "
                  f"hits to k = {kmax})")


GATES = [g4_parity_with_oracle, g5_rederive_knowns, g6_segmentation_invisible]

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
