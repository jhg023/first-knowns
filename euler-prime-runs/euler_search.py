# euler_search.py -- CPU engine for the A164926 Euler-ladder hunt.
#
# Pipeline (independent of the oracle; gated against it):
#   wheel   : p restricted to residues mod prod(wheel primes) that survive the
#             n forbidden classes of every wheel prime.  This engine runs 23#
#             or 29#; the GPU picks the largest that fits (best_wheel), which
#             at n=17 is 37# and is carried factored (wheel_jtab).  The
#             survivor set does not depend on the wheel -- it only decides
#             which primes are tested by generation rather than by sieving --
#             and that difference is exactly what the G6 parity gate measures
#   stage 1 : bitmask kill by primes 29..Q1 (numpy, compress-as-you-go)
#   stage 2 : kill by primes Q1..Q2 via the exact 17-value divisibility test
#   MR      : deterministic 7-base Miller-Rabin (valid < 3.317e24) on the
#             n values; survivors get their EXACT run computed
# The engine only ever *proposes*; launch.py's three-way verification
# (sympy + this MR + fresh window re-sieve) decides.
#
# Correctness floor: sieve assumes every value x^2+x+p > Q2, so the engine
# refuses p < P_FLOOR; [2, P_FLOOR) belongs to the oracle low-pass.
#
# ONE reference engine, spanning the whole range to P_CEIL = 1e24.  It is
# what the GPU is pinned against (G6, bit-for-bit on populated windows at
# seven heights), it is checked itself against direct big-integer trial
# division on mini-windows (G10) and against the oracle on small windows
# (G4), and it is the third leg of the discovery protocol -- where the
# launcher runs it on the 23# wheel while production runs 29#, so the
# re-sieve differs from the GPU in both arithmetic and alignment at every
# height.
#
# It is the SLOW, obviously-correct side of the pair on purpose: plain
# numpy `%` on (k, off) pairs, never Barrett, never sharing code with the
# GPU.  That independence is what the parity gate measures, so do not
# optimize this file.
#
# ASCII only.

import functools

import numpy as np
from sympy import primerange

import sys as _sys
import pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown  # noqa: E402
from huntlib.primes import MR_BASES, mr_is_prime  # noqa: E402

from euler_reference import A21_UPPER, KNOWN, run_length

WHEEL_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23]
WHEEL_PRIMES_29 = WHEEL_PRIMES + [29]
WHEEL_PRIMES_31 = WHEEL_PRIMES_29 + [31]
WHEEL_PRIMES_37 = WHEEL_PRIMES_31 + [37]
M_WHEEL = 223092870                     # product of WHEEL_PRIMES
M_WHEEL_29 = 6469693230                 # product incl. 29
M_WHEEL_31 = 200560490130               # product incl. 31
M_WHEEL_37 = 7420738134810              # product incl. 37
Q1 = 1024                               # stage-1 prime bound
Q2 = 65536                              # stage-2 prime bound
P_FLOOR = 100_000                       # engine floor (> Q2 guard is at 65536;
                                        # floor at 1e5 keeps a safety margin)

# Offset-table budget for automatic wheel selection.  Folding one more prime q
# into the wheel generates a factor ~q/(q-r_q) fewer candidates for a
# MATHEMATICALLY IDENTICAL survivor set -- the wheel only decides which primes
# are tested by generation rather than by sieving, so the union of tested
# primes, and therefore the result, is unchanged.  What stops it is memory:
# the table is n-dependent and grows fast as n shrinks (at n=17 the 31# table
# is 2.99e7 offsets / 240 MB; at n=5 it is 5.4e8 / 4.3 GB).  So pick the
# largest wheel that fits and let small n fall back, rather than capping
# everything at the smallest common denominator.
WHEEL_BUDGET_OFFS = 50_000_000          # ~400 MB as u64

# ...but the NEXT wheel does not have to be materialized at all, and that is
# what lets the budget stop being the ceiling on how wide a wheel can get.
# 37# has 20x the offsets of 31# (5.99e8 / 4.8 GB at n=17, 1.7e10 at n=5), and
# none of them need to exist: the offsets of the wheel base*q are exactly
# {off + j*M_base}, and WHICH j survive q depends on off only through
# off mod q.  So the whole table is the base table plus a q x nj byte table of
# admissible j (wheel_jtab), and the GPU generates one CHUNK of offsets at a
# time from those two.  Wheels at or above this prime are carried that way.
FACTORED_FROM = 37


def forbidden(q, n):
    """Residues r mod q killed: q | x^2+x+p for some x < n when p = r."""
    return {(-(x * x + x)) % q for x in range(n)}


def wheel_offset_count(n, wheel_primes):
    """Exact admissible-offset count, without building the table."""
    cnt = 1
    for q in wheel_primes:
        cnt *= q - len(forbidden(q, n))
    return cnt


def wheel_base(wheel_primes):
    """The primes whose offset table is actually BUILT for this wheel.

    Wheels below FACTORED_FROM carry a real table and this is the identity.
    37# carries the 31# table plus a 37 x nj admissible-j table, so its base
    is 31#.  ONE place decides this, and the engine, best_wheel and the gates
    all ask it -- a derived quantity computed in two places will eventually
    disagree, and this project has already shipped that bug once
    (../OPTIMIZATION.md 2.9).
    """
    wheel_primes = list(wheel_primes)
    return (wheel_primes[:-1] if wheel_primes[-1] >= FACTORED_FROM
            else wheel_primes)


def wheel_jtab(n, base_primes, q):
    """Admissible-j table for folding one more prime q into an existing wheel.

    Let M_b = prod(base_primes).  Every residue mod q*M_b that is admissible
    for base_primes can be written off + j*M_b for exactly one admissible base
    offset off < M_b and one j in [0, q).  q divides no base prime, so M_b is
    invertible mod q and j -> (off + j*M_b) mod q is a bijection; hence
    off + j*M_b is killed by q exactly when

        off + j*M_b == -(x^2 + x)   (mod q)   for some x < n,

    which depends on off only through off mod q, and leaves exactly
    q - |F_q(n)| admissible j for EVERY base offset.

    That count is computed, never assumed.  It is 20 at (q=37, n=17) because
    the 17 values x^2+x are distinct mod 37 -- but at n=21 they are not
    (20^2+20 == 16^2+16 mod 37) and it is 18.  A hardcoded 20 would silently
    generate offsets that the wheel forbids.

    Returns (jtab, nj) with jtab[r*nj + t] = the t-th admissible j for a base
    offset with off mod q == r.  Pure Python ints, no numpy, no cleverness:
    that this enumerates exactly build_wheel(n, base_primes + [q]) is G16.
    """
    q = int(q)
    Mb = 1
    for b in base_primes:
        Mb *= int(b)
    if Mb % q == 0:
        raise ValueError("q=%d already divides the base wheel period" % q)
    F = forbidden(q, n)
    jtab, nj = [], None
    for r in range(q):
        good = [j for j in range(q) if (r + j * Mb) % q not in F]
        if nj is None:
            nj = len(good)
        elif len(good) != nj:               # impossible; the bijection above
            raise ValueError(               # makes it q - |F| for every r
                "admissible-j count not uniform at q=%d n=%d: %d vs %d"
                % (q, n, len(good), nj))
        jtab.extend(good)
    return jtab, nj


def wheel_factored_slice(n, base_primes, q, a0=0, count=None):
    """Flat indices [a0, a0+count) of the factored wheel, materialized.

    This is EXACTLY the arithmetic the device kernel performs for one offset
    chunk, written out once in Python where it can be read and gated:

        flat index a  ->  i = a // nj,  t = a % nj
                      ->  off = base[i] + jtab[(base[i] % q)*nj + t] * M_base

    A SLICE, not the whole thing, because the whole thing is the point: at
    (31#, 37) it is 5.99e8 offsets / 4.8 GB, which is why nothing materializes
    it -- not production, not the gates.  Slices are how the production wheel
    stays testable, and they are also the unit the device works in, so gating
    the slice gates the real mechanism rather than a convenience copy.

    Offsets come out in flat-index order, which is NOT sorted.  Nothing needs
    it to be: the chunks partition the flat index either way, and the engine
    sorts its survivors.
    """
    base, Mb = build_wheel(n, base_primes)
    jtab, nj = wheel_jtab(n, base_primes, q)
    total, M = int(base.size) * nj, Mb * int(q)
    a0 = int(a0)
    count = total - a0 if count is None else min(int(count), total - a0)
    if count <= 0:
        return np.empty(0, dtype=np.uint64), M
    a = np.arange(a0, a0 + count, dtype=np.int64)
    b = base[a // nj]
    jt = np.array(jtab, dtype=np.uint64)
    off = b + jt[(b % np.uint64(q)).astype(np.int64) * nj
                 + (a % nj)] * np.uint64(Mb)
    return off, M


def wheel_factored_offsets(n, base_primes, q):
    """The whole factored wheel, materialized.  Gates, at SMALL q only.

    Only ever called where the directly-built wheel also fits, because its
    only purpose is to be compared against one (G16).  At (31#, 37) use
    wheel_factored_slice.
    """
    return wheel_factored_slice(n, base_primes, q)


def best_wheel(n, budget=WHEEL_BUDGET_OFFS):
    """The largest wheel whose MATERIALIZED table fits `budget` entries.

    The budget applies to what is built, not to what is swept -- which is why
    37# is reachable at all: its base is the 31# table (2.99e7 at n=17), and
    the 5.99e8 offsets it stands for are generated a chunk at a time and never
    stored.
    """
    for wp in (WHEEL_PRIMES_37, WHEEL_PRIMES_31, WHEEL_PRIMES_29,
               WHEEL_PRIMES):
        if wheel_offset_count(n, wheel_base(wp)) <= budget:
            return wp
    return WHEEL_PRIMES


def build_wheel(n, wheel_primes=None, chunk_bytes=1 << 26):
    """Admissible offsets mod prod(wheel_primes) via CRT lifting (numpy).

    Lifting is chunked over the new prime's residue classes so peak memory
    stays near chunk_bytes instead of q * len(offs) * 8; the result is the
    same set, built in pieces, and is sorted at the end either way.

    MEMOIZED.  This is a pure function of its arguments that builds and sorts
    up to a 4e7-element array, and the gate battery calls it forty-odd times
    -- every engine construction on both sides, G3, G14, G15 and the direct
    trial-division helper.  The cached array is marked read-only so that a
    caller which mutated it would fail loudly rather than corrupt every
    later caller; every current caller only reads, copies or converts it.
    """
    return _build_wheel(n, tuple(wheel_primes or WHEEL_PRIMES), chunk_bytes)


@functools.lru_cache(maxsize=None)
def _build_wheel(n, wheel_primes, chunk_bytes):
    offs = np.array([0], dtype=np.uint64)
    m = 1
    for q in wheel_primes:
        F = np.fromiter(sorted(forbidden(q, n)), dtype=np.int64)
        per = max(1, int(chunk_bytes // max(offs.nbytes, 1)))
        parts = []
        for j0 in range(0, q, per):
            j = np.arange(j0, min(j0 + per, q), dtype=np.uint64)
            lift = (offs[None, :] + (j * np.uint64(m))[:, None]).ravel()
            keep = ~np.isin((lift % np.uint64(q)).astype(np.int64), F)
            parts.append(lift[keep])
        offs = parts[0] if len(parts) == 1 else np.concatenate(parts)
        m *= q
    offs.sort()
    offs.flags.writeable = False
    return offs, m


def stage_primes(after=23):
    s1 = np.array([q for q in primerange(after + 1, Q1)], dtype=np.uint64)
    s2 = np.array([q for q in primerange(Q1, Q2)], dtype=np.uint64)
    return s1, s2


def mr_run_length(p, cap=100):
    x = 0
    while x < cap and mr_is_prime(x * x + x + p):
        x += 1
    return x


# ------------------------- the (k, off) representation ----------------------
#
# p is never materialized in a machine word.  Every candidate is carried as
# the pair (k, off) with p = k*M + off, off < M, and every sieve test needs
# only
#     p mod q = ((k mod q) * (M mod q) + (off mod q)) mod q
# which is u64-safe for any p below the ceiling (k < 2^48, products < 2^32).
# Exact p values exist only as host-side Python ints.  This is why there is
# no 2^64 boundary anywhere in the search and no second engine to switch to
# at one -- see ../OPTIMIZATION.md section 2.7.

P_CEIL = 10**24
# Enforced value ceiling of the search.  Everything the engines
# and the MR chain touch (values x^2+x+p <= p + 10100 at run cap 100)
# stays a factor >3 below huntlib's deterministic-MR validity bound
# 3.317e24 (Sorenson-Webster 7-base).  Raising this is a new engine
# version: new gates, new fingerprint, log entry.


class CpuEngine:
    """The CPU reference engine: streams pre-MR survivors of [lo, hi) with
    lo/hi/survivors as exact Python ints, valid up to P_CEIL.

    The independent implementation of the residue arithmetic -- plain numpy
    `%` on (k, off) pairs, where the GPU twin uses Barrett magic-multiply.
    The two must never share code; G6 compares their output streams, and
    that comparison is only worth anything because they are written
    differently.  Yields sorted lists of Python ints."""

    def __init__(self, n, wheel_primes=None):
        self.n = n
        self.wheel_primes = wheel_primes or WHEEL_PRIMES_29
        self.offs, self.M = build_wheel(n, self.wheel_primes)
        self.s1, self.s2 = stage_primes(after=self.wheel_primes[-1])
        self.luts = {}
        for q in self.s1:
            lut = np.zeros(int(q), dtype=bool)
            lut[list(forbidden(int(q), n))] = True
            self.luts[int(q)] = lut
        self.xx = [x * x + x for x in range(n)]

    def survivors_pre_mr(self, lo, hi, chunk_periods=16):
        """Yield sorted lists of survivor p (Python ints) in [lo, hi)."""
        lo, hi = int(lo), int(hi)
        if lo < P_FLOOR:
            raise ValueError("engine floor is %d" % P_FLOOR)
        if hi > P_CEIL:
            raise ValueError("engine ceiling is %d" % P_CEIL)
        M = int(self.M)
        k0, k1 = lo // M, hi // M + 1
        s_lo = lo - k0 * M            # p >= lo  <=>  k > k0 or off >= s_lo
        kh, s_hi = hi // M, hi % M    # p < hi   <=>  k < kh or (k == kh and off < s_hi)
        for kc in range(k0, k1, chunk_periods):
            ks = np.arange(kc, min(kc + chunk_periods, k1), dtype=np.uint64)
            K = np.repeat(ks, self.offs.size)
            O = np.tile(self.offs, ks.size)
            keep = (((K < np.uint64(kh)) | ((K == np.uint64(kh)) & (O < np.uint64(s_hi))))
                    & ((K > np.uint64(k0)) | (O >= np.uint64(s_lo))))
            K, O = K[keep], O[keep]
            # stage 1: compress after each prime
            for q in self.s1:
                qq = np.uint64(q)
                Mq = np.uint64(M % int(q))
                r = ((K % qq) * Mq + (O % qq)) % qq
                dead = self.luts[int(q)][r.astype(np.int64)]
                K, O = K[~dead], O[~dead]
                if K.size == 0:
                    break
            if K.size == 0:
                continue
            # stage 2: exact divisibility of the n values
            alive = np.ones(K.size, dtype=bool)
            for q in self.s2:
                qq = np.uint64(q)
                Mq = np.uint64(M % int(q))
                r = ((K % qq) * Mq + (O % qq)) % qq
                dead = np.zeros(K.size, dtype=bool)
                for xx in self.xx:
                    dead |= (r + np.uint64(xx)) % qq == 0
                alive &= ~dead
            K, O = K[alive], O[alive]
            if K.size:
                yield sorted(int(k) * M + int(o)
                             for k, o in zip(K.tolist(), O.tolist()))

    def hunt(self, lo, hi, cap=100):
        """All (p, exact_run) with run >= n in [lo, hi), ascending."""
        out = []
        for chunk in self.survivors_pre_mr(lo, hi):
            for p in chunk:
                if all(mr_is_prime(p + xx) for xx in self.xx):
                    out.append((p, mr_run_length(p, cap=cap)))
        return out


# ------------------------------- gates -------------------------------------

def g3_wheel_property(trials=4000, seed=1):
    """Wheel admissibility == 'no wheel prime divides any of the n values'.

    The 37# case comes through the FACTORED enumeration, which is the form
    production actually runs -- so this gate tests the offsets the engine
    generates, not a table it never builds.  n=21 is included there on
    purpose: it is the n where the x^2+x values collide mod 37 and nj is 18
    rather than 20, i.e. the case a hardcoded count would get wrong.
    """
    rng = np.random.default_rng(seed)
    for wp in (WHEEL_PRIMES, WHEEL_PRIMES_29):
        for n in (9, 13, 17):
            offs_arr, m = build_wheel(n, wp)
            offs = set(offs_arr.tolist())
            for p in rng.integers(P_FLOOR, 10**7, trials).tolist():
                direct = all(all((p + x * x + x) % q for x in range(n))
                             for q in wp)
                if direct != ((p % m) in offs):
                    return False, f"G3 FAIL at n={n}, p={p}, wheel={wp[-1]}"
    # 37#: the production wheel, tested WITHOUT materializing it.  Two
    # directions, because only one of them is the dangerous one -- a
    # generator that emits an inadmissible offset merely wastes work, while
    # one that DROPS an admissible offset loses survivors, and G6 cannot see
    # that (it compares against a 29#-wheel reference, so a hole in the 37#
    # wheel removes the same p from both sides of nothing).
    import random
    for n in (17, 21):
        base, Mb = build_wheel(n, WHEEL_PRIMES_31)
        jtab, nj = wheel_jtab(n, WHEEL_PRIMES_31, 37)
        M, total = Mb * 37, int(base.size) * nj
        rr = random.Random(seed + n)
        # (a) everything the flat-index arithmetic emits is admissible, at
        #     slices spread across the index -- including the last one, where
        #     a chunk runs short
        for a0 in (0, total // 3 + 1, total - 400):
            offs_arr, m = wheel_factored_slice(n, WHEEL_PRIMES_31, 37, a0, 400)
            if m != M or offs_arr.size != 400:
                return False, f"G3 FAIL n={n}: slice at {a0} is {offs_arr.size}"
            for o in offs_arr.tolist():
                p = int(o) + M * rr.randrange(10**8, 10**9)
                if not all(all((p + x * x + x) % q for x in range(n))
                           for q in WHEEL_PRIMES_37):
                    return False, (f"G3 FAIL n={n}: generated offset {o} is"
                                   f" NOT 37#-admissible (p={p})")
        # (b) and it emits ALL of them: for a real base offset, admissibility
        #     of off + j*M_base is exactly "j is in the table", both ways
        for _ in range(trials // 2):
            o0 = int(base[rr.randrange(base.size)])
            row = set(jtab[(o0 % 37) * nj:(o0 % 37 + 1) * nj])
            j = rr.randrange(37)
            p = o0 + j * Mb + M * rr.randrange(10**8, 10**9)
            direct = all(all((p + x * x + x) % q for x in range(n))
                         for q in WHEEL_PRIMES_37)
            if direct != (j in row):
                return False, (f"G3 FAIL n={n} wheel=37: base {o0} j={j}"
                               f" admissible={direct} but in-table={j in row}")
    return True, ("G3 ok: wheel==direct divisibility; 23#/29# from built"
                  " tables at n=9,13,17, and 37# from the FACTORED generator"
                  " at n=17,21 in both directions (no offset it emits is"
                  " inadmissible, no admissible offset is missing)")


def g16_factored_wheel():
    """The factored enumeration == the directly built wheel, as a SET.

    The 37# wheel is never materialized in production -- the device generates
    off = base[i] + jtab[(base[i] mod q)*nj + t] * M_base one chunk at a time.
    That is a different construction from build_wheel's CRT lifting, and
    nothing else in the battery would notice if it enumerated a slightly
    different set: G6 compares the GPU against a 29#-wheel reference, and the
    survivor set is wheel-independent, so a wheel that dropped admissible
    offsets would drop survivors on BOTH sides of nothing and simply lose
    them.  So it is checked here, directly, where both sides are cheap.

    Cheap means a small q.  The mechanism at (31#, 37) is the same code with
    different constants, and its direct table is 4.8 GB, so the equality is
    checked at (23#, 29) and (29#, 31) -- a few million entries, and the
    (29#, 31) tables are the ones the engine builds anyway.  What is checked
    AT (31#, 37) is what a smaller q cannot stand in for: the count, and that
    the flat index partitions (chunk c's slice concatenated with chunk c+1's
    is the slice over their union, with no offset repeated).  G3 covers the
    (31#, 37) offsets against divisibility itself, in both directions.

    Compared as sorted arrays: the factored order is the flat-index order and
    is deliberately not sorted.
    """
    cases = [(WHEEL_PRIMES, 29, (9, 13, 17, 21)),
             (WHEEL_PRIMES_29, 31, (13, 17))]
    checked = 0
    for base, q, ns in cases:
        for n in ns:
            got, m = wheel_factored_offsets(n, base, q)
            want, mw = build_wheel(n, base + [q])
            if m != mw:
                return False, (f"G16 FAIL n={n} q={q}: period {m} vs {mw}")
            if got.size != want.size:
                return False, (f"G16 FAIL n={n} q={q}: {got.size} offsets"
                               f" factored vs {want.size} built")
            g = np.sort(got)
            if not np.array_equal(g, want):
                bad = int(np.argmax(g != want))
                return False, (f"G16 FAIL n={n} q={q}: first difference at"
                               f" index {bad}: {int(g[bad])} vs"
                               f" {int(want[bad])}")
            checked += int(got.size)
    # (31#, 37): the production wheel.  nj is COMPUTED, not assumed -- pin
    # both values, including the n where the x^2+x values collide mod 37.
    for n, want_nj in ((13, 24), (17, 20), (21, 18)):
        if wheel_jtab(n, WHEEL_PRIMES_31, 37)[1] != want_nj:
            return False, (f"G16 FAIL: nj(37, n={n}) != {want_nj}")
    for n in (17,):
        bs, _ = build_wheel(n, WHEEL_PRIMES_31)
        _, nj = wheel_jtab(n, WHEEL_PRIMES_31, 37)
        total = int(bs.size) * nj
        if total != wheel_offset_count(n, WHEEL_PRIMES_37):
            return False, (f"G16 FAIL n={n}: factored count {total} !="
                           f" {wheel_offset_count(n, WHEEL_PRIMES_37)}")
        # the chunk partition: adjacent slices join up, and nothing repeats
        for a0, c1, c2 in ((0, 1000, 1000), (total // 2 - 7, 999, 1001),
                           (total - 1500, 700, 800)):
            s1, M = wheel_factored_slice(n, WHEEL_PRIMES_31, 37, a0, c1)
            s2, _ = wheel_factored_slice(n, WHEEL_PRIMES_31, 37, a0 + c1, c2)
            whole, _ = wheel_factored_slice(n, WHEEL_PRIMES_31, 37, a0,
                                            c1 + c2)
            joined = np.concatenate([s1, s2])
            if not np.array_equal(joined, whole):
                return False, (f"G16 FAIL n={n}: chunk split at {a0}+{c1}"
                               " does not rejoin")
            if np.unique(whole).size != whole.size:
                return False, f"G16 FAIL n={n}: repeated offset near {a0}"
            if int(whole.max()) >= M:
                return False, f"G16 FAIL n={n}: offset >= period near {a0}"
            checked += int(whole.size)
    return True, ("G16 ok: factored enumeration == built wheel over"
                  f" {checked:,} offsets at q=29 (n=9..21) and q=31"
                  " (n=13,17); at q=37 the count matches, adjacent chunks"
                  " rejoin with no repeats, and nj is 24/20/18 at n=13/17/21")


def g4_engine_vs_oracle():
    """Survivor (p, run) lists match the oracle exactly on windows.

    Run on the 23# wheel rather than production's 29#: the survivor set is
    wheel-independent (the wheel only decides which primes are tested where),
    so this also checks that claim -- and G6 covers the production wheel.
    """
    from euler_reference import oracle_search
    for n, lo, hi in ((5, 100000, 400000), (6, 100000, 400000), (7, 100000, 1200000)):
        eng = CpuEngine(n, wheel_primes=WHEEL_PRIMES).hunt(lo, hi)
        eng_ge = sorted(p for p, r in eng)
        ora = sorted(oracle_search(lo, hi, n, exact=False))
        if eng_ge != ora:
            return False, f"G4 FAIL n={n}: engine {len(eng_ge)} vs oracle {len(ora)}"
        for p, r in eng:
            if run_length(p) != r:
                return False, f"G4 FAIL n={n}: run({p}) engine={r}"
    return True, "G4 ok: engine survivor sets == oracle on 3 windows (n=5,6,7)"


def g5_rediscover(ns=(9, 11, 12)):
    """Engine re-finds a(n) as the FIRST run-exactly-n survivor above floor.

    A least-claim drill, not just a hit: everything below the known value
    must classify as a shorter run.  On the 23# wheel, as G4.
    """
    for n in ns:
        target = KNOWN[n]
        hits = CpuEngine(n, wheel_primes=WHEEL_PRIMES).hunt(P_FLOOR, target + 1000)
        firsts = [p for p, r in hits if r == n]
        if not firsts or firsts[0] != target:
            return False, f"G5 FAIL n={n}: first={firsts[:1]}, expected {target}"
    return True, f"G5 ok: a(n) rediscovered for n={ns}"


def _direct_survivors(lo, hi, n):
    """Fourth implementation for mini-windows: wheel-admissible p tested
    by DIRECT big-int trial division over every prime in (29, Q2), pure
    Python, no numpy, no residue tricks.  Slow; tiny ranges only."""
    from sympy import primerange as _pr
    qs = [int(q) for q in _pr(30, Q2)]
    offs, M = build_wheel(n, WHEEL_PRIMES_29)
    out = []
    k0, k1 = lo // M, hi // M + 1
    for k in range(k0, k1):
        base = k * M
        for off in offs.tolist():
            p = base + int(off)
            if not (lo <= p < hi):
                continue
            alive = True
            for q in qs:
                if any((p + x * x + x) % q == 0 for x in range(n)):
                    alive = False
                    break
            if alive:
                out.append(p)
    return sorted(out)


def g10_above_cap():
    """The reference engine is pinned two further independent ways:
    (a) mini-window parity against direct big-int trial division at
    2.35e20 and at the P_CEIL zone; (b) end-to-end rediscovery of the
    Waldvogel-Leikauf run-21 literature value at 2.345e20."""
    for lo, span in ((235 * 10**18, 6 * 10**6),
                     (P_CEIL - 6 * 10**6, 6 * 10**6)):
        hi = lo + span
        direct = _direct_survivors(lo, hi, 17)
        eng = sorted(p for chunk in
                     CpuEngine(17).survivors_pre_mr(lo, hi)
                     for p in chunk)
        if direct != eng:
            return False, (f"G10 FAIL [{lo},{hi}): direct {len(direct)}"
                           f" vs engine {len(eng)}")
    lo, hi = A21_UPPER - 10**7, A21_UPPER + 10**7
    hits = CpuEngine(17).hunt(lo, hi)
    good = [(p, r) for p, r in hits if p == A21_UPPER and r == 21]
    if not good:
        return False, f"G10 FAIL: A21 upper value not rediscovered ({hits})"
    return True, ("G10 ok: reference engine == direct big-int trial division"
                  " on 2 mini-windows (2.35e20, ceiling); Waldvogel-Leikauf"
                  " run-21 value rediscovered end-to-end")


def selftest(fast=False):
    gates = [g3_wheel_property, g16_factored_wheel, g4_engine_vs_oracle,
             g5_rediscover, g10_above_cap]
    ok = True
    for g in gates:
        good, msg = g()
        print(("PASS " if good else "FAIL ") + msg)
        ok = ok and good
    return ok


# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    import sys
    sys.exit(_shutdown.graceful(lambda: 0 if selftest() else 1))
