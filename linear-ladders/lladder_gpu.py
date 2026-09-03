"""lladder_gpu.py -- the GPU engine for the linear ladders.

The same mathematics a third time, in CuPy, and shaped so that nothing it
shares with the CPU engine could hide a bug in either.

WHAT THE KERNEL DOES.  The CPU engine materialises the dense k line and
marks arithmetic progressions into it.  This engine never forms the line
at all.  It carries a wheel index and reconstitutes

    k = W*j + x,        x congruent to a residue that no wheel prime kills

Each candidate is then TESTED, not marked: for each prime q above the
wheel the kernel reduces k mod q by Barrett magic-multiply and reads one
bit out of a packed table of the forbidden residues -- CRT-combined
group tables in the block, a per-prime mask in the tail -- BAILING OUT at
the first kill.  That early exit is the whole performance argument: w(q,n)
is the maximum min(c, q - 1) out of every q above the forced primes, so
the first prime tested kills a large fraction and the expected number of
tests per candidate is small, against the ~c*ln ln q2 marks per candidate
a marking sieve of the same depth would pay.

THIS IS prime-ladders' v3.1 ENGINE, AND WHY IT TRANSFERS.  The kernel
knows nothing about the forms: everything problem-specific enters through
`killed_residues(q, n, fam, unit)` -- the wheel tables, the per-prime
masks and residue lists, the CRT-combined prefix groups and the survival
curve the compaction points are derived from are all built from that one
function.  prime-ladders kills k by { -s * prime(i)^-1 }, this project by
{ -s * m^-1 } over the family's multipliers, and the same code sieves
both.  Two things are different here, and both are gifts:

  * FORCED DIVISIBILITY IS STRONGER.  Consecutive multipliers cover the
    nonzero residues of 2..13 by n = 12 for the 1..n family
    (lladder_reference G2c), so at A088250's opening filter n = 15 the
    unit is 30030 (against prime-ladders' 2310 at n = 14) and every wheel
    prime above it kills the maximum min(15, q - 1) residues: the wheel
    (..31],(31,41],(41,53] at unit 30030 has 14,336 x 572 x 34,048
    residues per period of 3.26e19 -- 8.6e-9 of the line, 83x thinner than
    prime-ladders' opening wheel.  A candidate rate in the 1e11/s range is
    then a LINE rate in the 1e19-1e20 k/s range.
  * THE SIGN COSTS NOTHING.  K(q,n,-1) = -K(q,n,+1), so a family and its
    sign twin have identical table SIZES, identical survival curves and
    identical generated kernel source; only the table CONTENTS differ, and
    those are device arrays.  One compiled module serves both.

THE FACTORED WHEEL, THE ISSUE-BOUND TEST LOOP, THE (k, off) REPRESENTATION
and the compaction design are square-ladders' v5 as re-tuned by
prime-ladders v2/v3 (tail compaction rounds with lanes per item, the
in-block round split, the pipelined loop, the unit wheel); their
OPTIMIZATION_LOG.md files hold the measurements that shaped each of them.
The short version of what is in here:

  * the wheel is THREE tables combined per candidate by CRT
    (x = RES1[t] + W1 * ((RES2[s] - RES1[t]) * W1^-1 mod W2), with the
    second modulus itself split by CRT across two tables), so a wheel of
    1e8 residues is stored in tables of thousands;
  * the reduction is 32-bit where it can be, one conditional subtraction
    suffices below 2^63 (a theorem, stated in the TEST macro), the
    per-prime constants are one uint4, and the first primes above the
    wheel are baked into the generated source as CRT-combined literals;
  * divergence is compacted inside the CUDA block, into shared-memory
    queues sized from the ANALYTIC survival plus QCAP_SIGMA sigma, and the
    deep tail runs as compaction ROUNDS over global queues, a round too
    small to fill the device giving every item several LANES; every
    queue's overflow is HARMLESS by construction (the candidate runs its
    tail on the spot), and G14/G16 force those paths and check the stream;
  * a candidate is the pair (base, off) with k = base + off: `base` is the
    launch's absolute floor, a PYTHON INT that never leaves the host, and
    `off < W' * per_launch` is the only thing the device reduces.  The
    base is folded once per launch into the per-prime records (slot .w)
    and the group scalars, so no machine word bounds the search.  G15
    proves the stream does not depend on where the launch base was put.

UNIT SPACE.  Every candidate at the campaign filters is a multiple of a
forced modulus (lladder_search.forced_unit), so the device sweeps
k' = k / unit with the kill sets K'(q) = unit^-1 * K(q,n,F) mod q and the
unit's own primes left out of the wheel.  Everything the device touches is
in k'; `self.W` (the period), the survivors and every bound check are in
k, and `_collect` is the one place the unit is multiplied back in.
`unit = 1` is the k-space engine, and the gate battery runs it on wheels a
dense CPU sieve can follow.  `assert_unit` refuses a unit that is not
forced at the filter, which is the one way this could thin the line.

A WINDOW MAY START INSIDE PERIOD ZERO.  A production period is 3.26e19 of
k line and every family's frontier -- 1e19 at most -- sits INSIDE the first
one, as do the modelled medians of the next term of each.  `sweep` and
`survivors_j` take `k_min`: the device sieves the whole period and the
host DROPS every survivor below k_min before anyone sees it.  That is
exact -- a survivor above k_min is a survivor of a sieve whose every prime
is below k_min, so "q divides the value" still means "composite" -- and it
costs nothing on the device.  G9 pins the clipped period-0 stream against
the CPU engine.

CEILINGS, stated and enforced (CONVENTIONS.md "Numeric hygiene"):
  * k < k_ceil(n, F) = the PRIMALITY-PROOF VALIDITY BOUND of the family
    (lladder_search, G10).  For the -1 families it is the deterministic
    Miller-Rabin bound rearranged for m_max*k - 1, 2.2e23 at n = 15: every
    decision there is a proof.  For the +1 families it is that bound on k
    ITSELF, 3.317e24: below the proof crossing the classification is a
    proof, above it a discovery is proved by a BLS75 certificate on
    N - 1 = m*k (launch.py certify_run), one level deep while every factor
    of k is under the bound.  No machine word appears in either.
  * W' * per_launch + q2 < 2^63 = REDUCE_MAX, on the DEVICE period W'
    (k' units), which is what keeps the Barrett reduction within ONE
    conditional subtraction of exact.
  * W1 < 2^32, so the first-level table is u32; W2 < 2^32 and
    W1*W2 < 2^63.
  * the unit is forced at the filter (assert_unit), or the engine
    refuses to build; the filter's form count fits the NRES_MAX-slot
    residue list.

Gates here: G7 (both wheel constructions == the oracle's brute-force
period walk, several families), G8 (the wheel partitions the period: the
count is the formula and no kept residue is killed), G9 (GPU survivor
stream == CPU survivor stream, bit for bit, on populated windows at several
heights, filters and families, one-, two- and three-level, k space and
unit space, including above 2^64 and a CLIPPED PERIOD 0), G13 (the
production wheel constants of every family's opening), G14 (the generation
tables, the derived compaction depths, the CRT-combined prefix and round-2
group tables, and the queue-overflow fallback), G15 (the (k, off)
representation: base-shift invariance, the tail's masks and residue lists,
and the folded group scalars), G16 (the third level: the global tail
queue's overflow, chunking, and the power-of-two queue index), G17 (the
production unit wheel returns a k-space wheel's identical survivors over a
k-space period at the opening filter).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.gpu import barrett_magics                         # noqa: E402
from lladder_reference import (FAMILIES, KNOWN, family,         # noqa: E402
                               forbidden_k_residues, nforms, sign,
                               wheel_residues)
from lladder_search import (Q2_DEFAULT, CpuEngine, assert_unit,  # noqa: E402
                            forced_unit, k_ceil, k_floor, killed_residues)

# THE K-SPACE WHEEL (unit = 1).  Kept as the defaults of this class because
# the k-space benchmark shapes and most of the gates run on it; the
# CAMPAIGN runs the unit wheel below.
P1_DEFAULT = 23              # first-level wheel: the primes up to here
P2_DEFAULT = 37              # second-level wheel: the primes in (P1, P2]
# THIRD-level wheel: the primes in (P2, P3].  In k space 47 IS THE LAST
# ONE, and not by choice: m is a u32 and W1*m is what the
# one-conditional-subtraction reduction bounds, so the combined second
# modulus must stay under 2^32.  Primes to 47 make it 2.76e9; adding 53
# makes it 1.46e11.  The engine raises rather than wrapping.
P3_DEFAULT = 47
# THE UNIT WHEEL (launch.py UNIT/P1/P2/P3).  The forcing lemma makes every
# candidate a multiple of 30030 at every family's opening filter (510510
# for A088651), so the device sweeps k' = k / unit and the primes of the
# unit leave the wheel: (..31] is then 17*19*23*29*31 = 6.7e6 (u32),
# (31, 41] and (41, 53] together 1.6e8 (u32), and 53 fits where in k space
# nothing did.  The measurements are in OPTIMIZATION_LOG.md.
TPB_DEFAULT = 128            # threads per block (prime-ladders v2: 128 over 256 by 1.09x)
# TUNING CONSTANTS COME IN TWO SETS, one per wheel family, because a
# constant tuned against one geometry is wrong for the other (Rule 3a):
# the k-space wheels keep prime-ladders v2's measured values and the unit
# wheel takes the ones swept HERE, at THIS project's densities
# (OPTIMIZATION_LOG.md); `unit > 1` selects.
#
# Second-level residues per BLOCK.  k = base + r1 + W1*m with
# m = A[t] + C[s], so for a fixed t the quantity base + r1 does not
# depend on s at all: one res1x load, one `t` computation, one bounds
# check and one 64-bit add serve SPB candidates instead of one.  Forced to
# 1 on a one-level wheel, where there is no second level to spread over.
SPB_DEFAULT = 8              # k-space wheels
SPB_UNIT = 16
# CANDIDATES PER THREAD, from which JPT (first-level residues per thread)
# follows as CPT // SPB.
CPT_DEFAULT = 32             # k-space wheels
CPT_UNIT = 64
# WHERE THE TWO COMPACTION POINTS GO, as SURVIVAL FRACTIONS rather than
# prime counts, so the depths follow each configuration's own survival
# curve: the first compaction where about this fraction of candidates is
# left, the second where about K2_SURV are.  A coarser wheel or a smaller
# filter kills faster, and a fixed count there would test past the point
# where anything is left to kill.
LIT_SURV = 0.19              # k-space wheels
K2_SURV = 0.015
# THE UNIT WHEEL'S PREFIX COMPACTION POINT IS FILTER-SENSITIVE, and not
# monotonically: prime-ladders measured its optimum at 0.12 for n = 12-15,
# 0.28 at 16-18 and 0.12 again at 19, a shared-memory cliff deciding where
# the prefix's compaction lands against the queue budget for that filter's
# survival curve.  Here the survival curve is a function of the NUMBER OF
# FORMS c (every wheel and sieve prime kills min(c, q - 1) residues, whatever
# the family), so the table is keyed by c rather than by n -- A088250 at
# n = 15, A173750 at n = 16 and A125839 at n = 17 are the same curve -- and
# it is what was MEASURED here, interleaved, at the campaign's own wheel
# and unit, the fingerprint identical across every variant
# (OPTIMIZATION_LOG.md): 0.12 wins at c <= 15 by 1.13-1.25x over 0.28,
# 0.28 wins at c = 16 and 17 by 1.05-1.14x over 0.12, 0.19 and 0.28 tie at
# c = 18, and 0.40 is a 6x cliff from c = 17 on.  A form count past the
# table's end takes the last entry (CLAUDE.md 5g: a constant swept at one
# filter is re-swept one filter later, because the campaign promotes itself
# there).
LIT_SURV_UNIT_BY_C = {8: 0.12, 9: 0.12, 10: 0.12, 11: 0.12, 12: 0.12,
                      13: 0.12, 14: 0.12, 15: 0.12,
                      16: 0.28, 17: 0.28,
                      18: 0.19, 19: 0.19, 20: 0.19}
K2_SURV_UNIT = 0.008


def lit_surv_unit(c):
    """The unit wheel's prefix compaction point for c forms (measured)."""
    c = int(c)
    if c in LIT_SURV_UNIT_BY_C:
        return LIT_SURV_UNIT_BY_C[c]
    keys = sorted(LIT_SURV_UNIT_BY_C)
    return LIT_SURV_UNIT_BY_C[keys[-1] if c > keys[-1] else keys[0]]


# INTERMEDIATE COMPACTION POINTS between the prefix and the global push, as
# survival fractions.  Each split packs the survivors into a fresh shared
# queue so the next groups run on live candidates only; a split costs one
# __syncthreads and one queue, and its value is the dead candidates it
# stops testing.  One split (prime-ladders v2b: 1.16x, a second buys
# nothing).
R2_SPLITS = (0.03,)
UNROLL = 4                   # independent Barrett chains in the queue tail
# Survivors buffered per launch.  The gate battery runs coarse wheels and
# shallow sieves where a launch of 2^30 candidates can keep hundreds of
# thousands; the engine RAISES on overflow rather than dropping, so this is
# a budget, not a bound.
HIT_CAP = 1 << 20
RES_MAX = 1 << 24            # refuse a one-level wheel table bigger than this
LIT_INLINE_Q = 64            # below this, a group's kill set is a u64 literal
# Largest modulus a CRT-combined prefix group may reach, and the total
# table budget that goes with it -- the knob that keeps the combined
# tables in L1.  square-ladders measured the cliff (0.34x at 147 KB of
# tables against 96 KB) and the budget is a guard on the SUM of tables and
# queues, not on either half.
LIT_GROUP_MAX = 1 << 18
GROUP_BYTES_MAX = 96 << 10
# Copies of each HOISTED group's pattern: one, because the hoisted prefix
# folds the base into its per-residue value and does not need the doubled
# table the per-prime bitmap uses.
HOIST_TABLE_REPS = 1
# The same budget for round 2's groups, which sit on the queue rather than
# on every candidate and can afford a bigger table.
K2_GROUP_MAX = 1 << 14

# How much margin the shared queues carry over their ANALYTIC occupancy.
# Overflow is HARMLESS, not impossible -- a candidate that does not fit
# runs its tail on the spot -- so this is a tuning constant and G14 proves
# the fallback by forcing it.
QCAP_SIGMA = 6.0

# How much candidate work a single launch should carry: it sets how many
# wheel blocks (and third-level residues) go in gridDim.z.  A tuning
# constant (OPTIMIZATION.md 2.4).
CAND_PER_LAUNCH = 1 << 30

# Ceiling on the GLOBAL tail queue, in candidates; overflow takes the
# in-block fallback, so it costs correctness nothing.
Q3_MAX = 1 << 26
TAIL_BLOCKS_PER_SM = 64
# THE TAIL RUNS AS COMPACTION ROUNDS (OPTIMIZATION.md 2.2).  Its items are
# rare-and-deep, so the tail sweeps its queue in rounds over prime ranges
# chosen from the survival curve: every round starts with every lane
# alive, and a lane that dies waits at most to the end of its round.
# TAIL_ROUND_DROP is the survival a round is allowed to lose before the
# survivors are compacted into the next queue.  Each round is one kernel
# launch over a global queue with one item per thread and ONE global
# atomic per block for the push.
TAIL_ROUND_DROP = 0.5
TAIL_TPB = 256
# LANES PER ITEM in a tail round.  The deep rounds hold a few thousand
# items against thousands of primes each: one thread per item is a serial
# chain of dependent loads on an otherwise empty device.  So a round whose
# expected item count would leave the device under TAIL_FILL threads gets
# 2, 4, ... 32 lanes per item, each lane testing every LPI-th prime and the
# lanes voting after every batch.  Same tests, a chain LPI times shorter.
TAIL_FILL = 1 << 19
# THE TAIL'S PER-PRIME TABLES.  A test in the tail is "is (off + base) mod
# q one of the w(q,n) <= c residues q kills".  Each prime carries a MASK of
# MASK_BITS bits over r mod MASK_BITS: for q <= MASK_BITS that IS the exact
# kill pattern, and above it a clear bit is still a proof of survival while
# a set bit -- about c in MASK_BITS -- goes to the exact residue LIST.
MASK_BITS = 4096
NRES_MAX = 32                # residue-list slots; the form count may not exceed it
# Survivors read back per launch WITHOUT waiting for the next launch: the
# first PRE_COPY entries of the survivor buffer are copied asynchronously
# into pinned host memory behind each launch, and only a launch that
# exceeds them pays a synchronous read.
PRE_COPY = 1 << 13

# The one-conditional-subtraction reduction is exact only below 2^63.  The
# reduced quantity is the OFFSET within a launch, so the bound is on
# W' * per_launch -- a property of the WHEEL AND THE BATCHING, which the
# engine chooses, and not of k.  Checked per engine in __init__.
REDUCE_MAX = 1 << 63

_MODCACHE = {}


def wheel(n, fam, p1, lo=1, unit=1):
    """(W, RES): residues mod W = prod(lo < q <= p1, q not | unit) that no
    such q kills -- in UNIT space, i.e. residues of k' = k / unit.

    Built by CRT lifting -- one prime at a time, each existing residue
    lifted to the q classes above it and the killed ones dropped.  The
    oracle builds the same set by walking the whole period; G7 pins them
    together, in k space and in unit space.

    A prime of the unit is left OUT of the modulus: it kills no k' at all
    (killed_residues), so including it would multiply the table by q for
    nothing.

    Refuses rather than thrashes: the table has prod(q - w(q,n)) entries,
    and one careless argument is an out-of-memory death rather than a slow
    gate.
    """
    fam = family(fam)
    unit = int(unit)
    qs = [q for q in primerange(lo + 1, p1 + 1) if unit % q]
    W, count = 1, 1
    for q in qs:
        count *= q - len(killed_residues(q, n, fam, unit))
    if count > RES_MAX:
        raise ValueError(
            f"a one-level wheel over ({lo}, {p1}] at n={n} would hold "
            f"{count:,} residues (> RES_MAX = {RES_MAX:,}); factor it into "
            f"two levels instead -- that is what P2 is for")
    res = np.zeros(1, dtype=np.int64)
    for q in qs:
        bad = np.array(killed_residues(q, n, fam, unit), dtype=np.int64)
        cand = (res[None, :] + W * np.arange(q, dtype=np.int64)[:, None])
        cand = cand.ravel()
        res = np.sort(cand[~np.isin(cand % q, bad)])
        W *= q
    return W, res


def lit_groups(primes, nlit, budget=LIT_GROUP_MAX, start=0):
    """Group primes[start:nlit] into CRT-combined test groups.

    "Killed by 59 or by 61" is a function of k mod (59*61) alone, so a
    group of primes costs ONE reduction and ONE bitmap lookup instead of
    one of each per prime.  Groups are grown greedily while the product
    stays under `budget`.
    """
    groups, cur, prod = [], [], 1
    for i in range(start, nlit):
        q = primes[i]
        if cur and prod * q > budget:
            groups.append(cur)
            cur, prod = [], 1
        cur.append(i)
        prod *= q
    if cur:
        groups.append(cur)
    return groups


def _group_bytes(primes, groups, reps=2):
    """Bytes the packed tables of these groups occupy: reps*Q bits each."""
    tot = 0
    for g in groups:
        Q = 1
        for i in g:
            Q *= primes[i]
        if Q >= LIT_INLINE_Q:
            tot += ((reps * Q + 31) // 32) * 4
    return tot


def _fit_groups(primes, nlit, budget, start, cap=GROUP_BYTES_MAX, reps=2):
    """Greedy groups under `budget`, halved until they fit `cap` bytes."""
    while True:
        groups = lit_groups(primes, nlit, budget, start)
        if budget <= 1 or _group_bytes(primes, groups, reps) <= cap:
            return groups
        budget //= 2


def lit_prefix(n, fam, primes, groups, table="gbits", indent=12, pname="gp",
               hoist=None, unit=1):
    """(CUDA source, packed table, group descriptors) for CRT-combined tests.

    With `hoist = (W1, W)` the group tests are emitted in the DECOMPOSED
    form, which is what the prefix runs.  A candidate is
    `off = b0 + W1*m`, `m = A - D` (plus W2 when that borrows), with b0 and
    A fixed for a whole inner loop and D fixed for the whole block, so

        off mod Q = ((b0 + W1*A) mod Q  - (W1*D) mod Q  [+ W mod Q]) mod Q

    and every 64-bit reduction moves OUT of the per-candidate path: one per
    block per group for `(W1*D) mod Q`, one per first-level residue for
    `(b0 + W1*A) mod Q`, amortised over SPB candidates apiece.  What is
    left per candidate is a select between the two precomputed values (the
    borrow decides which), one subtract and one conditional add.

    Round 2 does NOT get this form and cannot: it reads offsets back out of
    a shared queue, where the decomposition has been thrown away.

    Every modulus and magic number is a compile-time literal
    (OPTIMIZATION.md 2.5).  A group whose modulus is under LIT_INLINE_Q
    needs no table at all -- the entire forbidden set is a 64-bit
    immediate.  The table for a group is the OR of its primes' forbidden
    sets lifted to the product modulus, which is exactly "killed by at
    least one of them"; G14 checks that against killed_residues directly.

    The reduced quantity is `off`, not the absolute k, so what a group has
    to look up is `(off + base) mod Q`.  The base contribution is folded
    once per launch, on the host: a table group stores its pattern TWICE
    and the launch passes `2Q-block base + (base mod Q)`; an inline
    group's mask is ROTATED on the host.  Either way the group's base
    arrives as a kernel SCALAR PARAMETER.  `descs` tells the engine what
    to compute per launch: (kind, Q, payload).
    """
    fam = family(fam)
    lines, words, descs, off_bits = [], [], [], 0
    decl, blockpre, jjpre = [], [], []
    for gi, g in enumerate(groups):
        qs = [primes[i] for i in g]
        Q = 1
        for q in qs:
            Q *= q
        mg = (1 << 64) // Q
        red = (f"unsigned int r = (unsigned int)xx - "
               f"(unsigned int)__umul64hi(xx, {mg}ULL) * {Q}u; "
               f"if (r >= {Q}u) r -= {Q}u; ")
        if hoist is None:
            head = (" " * indent + "{ unsigned int r = (unsigned int)off - "
                    f"(unsigned int)__umul64hi(off, {mg}ULL) * {Q}u; "
                    f"if (r >= {Q}u) r -= {Q}u; ")
        else:
            W1, W = hoist
            decl.append(f"    __shared__ unsigned int pd{gi}[SPB]; "
                        f"unsigned int x0_{gi}, x1_{gi};")
            blockpre.append(
                f"            {{ const unsigned long long xx = "
                f"(unsigned long long){W1}u * (unsigned long long)dcur; "
                + red + f"pd{gi}[ss] = r; }}")
            fold = ("" if Q < LIT_INLINE_Q or HOIST_TABLE_REPS != 1 else
                    f"r += (unsigned int){pname}{gi}; "
                    f"if (r >= {Q}u) r -= {Q}u; ")
            jjpre.append(
                f"            {{ const unsigned long long xx = b0 + "
                f"(unsigned long long){W1}u * (unsigned long long)e1.y; "
                + red + fold + f"x0_{gi} = r; r += {W % Q}u; "
                f"x1_{gi} = (r >= {Q}u) ? r - {Q}u : r; }}")
            head = (" " * indent
                    + f"{{ const unsigned int a = BW ? x1_{gi} : x0_{gi}; "
                      f"const unsigned int e = pd{gi}[SS]; "
                      f"unsigned int r = a - e; "
                      f"if (a < e) r += {Q}u; ")
        if Q < LIT_INLINE_Q:
            mask = 0
            for u in killed_residues(qs[0], n, fam, unit):
                mask |= 1 << u
            lines.append(head + f"kill |= (unsigned int)(({pname}{gi} >> r) "
                                f"& 1ULL); }}")
            descs.append(("inline", Q, mask))
            continue
        single = hoist is not None and HOIST_TABLE_REPS == 1
        reps = (0,) if single else (0, Q)
        tab = np.zeros((len(reps) * Q + 31) // 32, dtype=np.uint32)
        idx = np.arange(Q)
        for q in qs:
            bad = np.array(killed_residues(q, n, fam, unit), dtype=np.int64)
            b = np.nonzero(np.isin(idx % q, bad))[0]
            for rep in reps:
                br = b + rep
                np.bitwise_or.at(tab, br >> 5,
                                 (np.uint32(1) << (br & 31)).astype(np.uint32))
        if hoist is None:
            lines.append(head + f"const unsigned int b = "
                                f"(unsigned int){pname}{gi} + r; "
                                f"kill |= ({table}[b >> 5] >> (b & 31)) "
                                f"& 1u; }}")
            descs.append(("table", Q, off_bits))
        elif HOIST_TABLE_REPS == 1:
            lines.append(head + f"const unsigned int b = {off_bits}u + r; "
                                f"kill |= ({table}[b >> 5] >> (b & 31)) "
                                f"& 1u; }}")
            descs.append(("modq", Q, off_bits))
        else:
            lines.append(head + f"const unsigned int b = "
                                f"(unsigned int){pname}{gi} + r; "
                                f"kill |= ({table}[b >> 5] >> (b & 31)) "
                                f"& 1u; }}")
            descs.append(("table", Q, off_bits))
        words.append(tab)
        off_bits += tab.size * 32
    table = (np.concatenate(words) if words
             else np.zeros(1, dtype=np.uint32))
    if hoist is None:
        return "\n".join(lines), table, descs
    return ("\n".join(lines), table, descs, "\n".join(decl),
            "\n".join(blockpre), "\n".join(jjpre))


def group_params(descs, base):
    """The per-launch scalar for each group: the base folded into its test.

    `base` is the absolute k' at offset 0 of the launch -- an arbitrary
    Python int, which is the whole point: it never reaches the device.
    """
    out = []
    for kind, Q, payload in descs:
        gb = int(base) % Q
        if kind == "inline":
            m = ((payload >> gb) | (payload << (Q - gb))) & ((1 << Q) - 1)
            out.append(np.uint64(m))
        elif kind == "modq":
            out.append(np.uint64(gb))
        else:
            out.append(np.uint64(payload + gb))
    return out


_SRC = r"""
#define W1C  %(w1)du
#define W2C  %(w2)du
#define WC   %(w)dULL
#define TWOLEVEL %(two)d
#define THREELEVEL %(three)d
#define NU   %(nu)d
#define SPB  %(spb)d
#define LITN %(lit)d
#define K2   %(k2)d
#define JPT  %(jpt)d
#define TPB  %(tpb)d
#define UNROLL %(unroll)d
%(qcaps)s
#define LOGTPB %(logtpb)d
#define LOGSPB %(logspb)d
#define QTYPE %(qtype)s
#define MASK_BITS %(mask_bits)d
#define MASK_WORDS (MASK_BITS / 32)
#define NRES %(nres)d
#define TTPB %(ttpb)d

/* WHAT THE QUEUES HOLD.  Not the candidate -- its INDEX in the block, which
   is (jj, ss, threadIdx.x) and so fits in log2(tile) bits where the offset
   needs 60.  Shared memory is what this kernel is short of: an SM divides
   128 KB between shared and L1, the resident blocks take their cut first,
   and the group tables have to live in what is left. */
#define QIDX(JJ, SS) ((QTYPE)(((JJ) * SPB + (SS)) * TPB + threadIdx.x))

/* One test against prime IDX: the uint4 record (magic_lo, magic_hi, q,
   base mod q), the prime's MASK_BITS-bit mask and, rarely, its residue
   list.  The remainder correction is 32-bit: the true value of
   off - qhat*q is in [0, 2q) < 2^17 and arithmetic mod 2^32 is exact for
   it, and ONE conditional subtraction is enough below 2^63: with
   M = floor(2^64/q) and x < 2^63, x*M/2^64 = x/q - x*s/(q*2^64) where
   s = 2^64 mod q < q, so the error term is under 1/2 and qhat is
   floor(x/q) or one less.

   What is reduced is the OFFSET within the launch, never the absolute k;
   the launch base enters as `base mod q` in slot .w, folded in with one
   add and one conditional subtraction.  The mask word is one 4-byte read
   inside the prime's own MASK_BITS/8-byte record -- warp-uniform prime,
   so one or two sectors serve the whole warp.  For q <= MASK_BITS the bit
   is the exact answer; above it a clear bit is a proof of survival and a
   set bit is checked against the residue list, NRES slots padded with a
   value no residue can equal.  Both branches are warp-uniform. */
#define TEST(IDX, DST) { \
    const uint4 e = pk[IDX]; \
    const unsigned long long mg = ((unsigned long long)e.y << 32) | e.x; \
    unsigned int r = (unsigned int)off \
                   - (unsigned int)__umul64hi(off, mg) * e.z; \
    if (r >= e.z) r -= e.z; \
    r += e.w; \
    if (r >= e.z) r -= e.z; \
    const unsigned int mword = pmask[(IDX) * MASK_WORDS \
                                     + ((r >> 5) & (MASK_WORDS - 1))]; \
    if ((mword >> (r & 31u)) & 1u) { \
        if (e.z <= MASK_BITS) { DST |= 1u; } \
        else { \
            const uint4* rp = pres + (IDX) * (NRES / 4); \
            unsigned int hit = 0u; \
            _Pragma("unroll") \
            for (int w = 0; w < NRES / 4; ++w) { \
                const uint4 v = rp[w]; \
                hit |= (v.x == r) | (v.y == r) | (v.z == r) | (v.w == r); } \
            DST |= hit; } } }

/* Test primes [from, np_) with early exit; the tail rounds call this on
   their own prime range, the in-block overflow fallbacks on everything
   left.  UNROLL independent Barrett chains hide the dependent-chain
   latency. */
__device__ __forceinline__ bool tail_survives(
        const unsigned long long off, const int np_, const int from,
        const uint4* __restrict__ pk, const unsigned int* __restrict__ pmask,
        const uint4* __restrict__ pres)
{
    int i = from;
    for (; i + UNROLL <= np_; i += UNROLL) {
        unsigned int kill = 0u;
#pragma unroll
        for (int z = 0; z < UNROLL; ++z) TEST(i + z, kill)
        if (kill) return false;
    }
    for (; i < np_; ++i) {
        unsigned int kill = 0u;
        TEST(i, kill)
        if (kill) return false;
    }
    return true;
}

#define EMIT(K) { const int _p = atomicAdd(nout, 1); \
                  if (_p < cap) out[_p] = (K); }


/* One candidate, start to finish: run the CRT-combined prefix on it and
   either queue it or -- if the queue is full -- finish it on the spot.  A
   macro, because the loop nest below is written twice: once with bounds
   checks and once, for every block but the last, without. */
#define CAND(K, BW, SS, JJ) { \
    const unsigned long long off = (K); \
    unsigned int kill = 0u; \
%(prefix_m)s
    if (!kill) { \
        const int p = atomicAdd(&qn0, 1); \
        if (p < Q0CAP) qk0[p] = QIDX(JJ, SS); \
        else if (tail_survives(off, np_, LITN, pk, pmask, pres)) EMIT(off) \
    } }

/* One candidate of the inner loop: the borrow out of `A - D` is what
   decides m, and it is ALSO what decides which of the two precomputed
   group residues the hoisted prefix reads, so it is computed once and
   handed to both. */
#define STEP(A, DD, SS, JJ) { \
    const unsigned int _d = (DD); \
    const unsigned int _bw = ((A) < _d); \
    const unsigned int _m = _bw ? ((A) - _d + W2C) : ((A) - _d); \
    CAND(b0 + (unsigned long long)W1C * _m, _bw, SS, JJ) }

/* m = A[t] + C[s] reduced mod W2, taken from D = W2 - C rather than from
   C, because `A + C` is NOT a quantity a u32 can hold once there is a
   third wheel level.  A - D never overflows; when it borrows, adding W2
   back wraps to exactly A + C. */
#define M_OF(A, D) (((A) >= (D)) ? ((A) - (D)) : ((A) - (D) + W2C))

/* Rebuild a candidate from its block index.  The thread that dequeues is
   not the thread that queued, so D has to be readable by any of them and
   lives in shared. */
__device__ __forceinline__ unsigned long long off_of(
        const unsigned int qi, const unsigned long long base,
        const uint2* __restrict__ res1x,
        const unsigned int* d2)
{
    const int tid = qi & (TPB - 1);
    const int rest = qi >> LOGTPB;
#if TWOLEVEL
    const int jj = rest >> LOGSPB;
#else
    const int jj = rest;
#endif
    const uint2 e1 = res1x[blockIdx.x * (TPB * JPT) + jj * TPB + tid];
    unsigned long long off = base + (unsigned long long)e1.x;
#if TWOLEVEL
    const unsigned int dd = d2[rest & (SPB - 1)];
    off += (unsigned long long)W1C * M_OF(e1.y, dd);
#endif
    return off;
}

/* No base0.  The launch's absolute base is a Python int on the host; what
   the device gets is the per-prime and per-group folding of it (pk.w, the
   gp/g2p scalars), so nothing here is bounded by k. */
extern "C" __global__ void sieve(
        const int R1, const int R2,
        const int np_,
        const unsigned int* __restrict__ pmask,
        const uint4* __restrict__ pres,
        unsigned long long* out, int* nout, const int cap,
        unsigned long long* q3, int* n3, const int q3cap,
        const uint4* __restrict__ pk,
        const uint2* __restrict__ res1x,
        const unsigned int* __restrict__ res2c,
        const unsigned int* __restrict__ res2d, const int u0,
        const unsigned int* __restrict__ gbits,
        const unsigned int* __restrict__ g2bits%(gparams)s)
{
    /* Sized from the analytic survival plus QCAP_SIGMA sigma, NOT from the
       impossible worst case.  Overflow is made harmless instead of
       impossible -- a candidate that does not fit runs its tail on the
       spot, uncompacted, which is the same arithmetic and so the same
       answer.  G14 forces that path and checks the stream is unchanged. */
%(qdecl)s
    __shared__ int q3b;
    if (threadIdx.x == 0) { %(qzero)s }
    __syncthreads();

    /* gridDim.z carries the wheel-period offset from the launch base AND,
       when there is a third wheel level, that level's residue: z = period *
       NU + u.  The engine only ever batches periods when the whole third
       level fits in one launch, so u0 is zero whenever the quotient can be
       non-zero. */
    const unsigned long long base = WC
                                  * (unsigned long long)(blockIdx.z / NU);
    const int tbase = blockIdx.x * (blockDim.x * JPT) + threadIdx.x;
    /* The block's per-second-level-residue data, all of it in SHARED and
       built by SPB threads: D = W2 - C, and the hoisted prefix's
       precomputed group residues, which may NOT go in registers (held per
       thread they cost occupancy, and this kernel is bound by OCCUPANCY).
       Declared unconditionally because off_of takes it either way. */
    __shared__ unsigned int d2[SPB];
#if TWOLEVEL
#if THREELEVEL
    const unsigned int cb = res2d[u0 + (int)(blockIdx.z %% NU)];
#endif
    const int s0 = blockIdx.y * SPB;
%(pdecl)s
    if ((int)threadIdx.x < SPB) {
        const int ss = threadIdx.x;
        unsigned int c = res2c[min(s0 + ss, R2 - 1)];
#if THREELEVEL
        /* both are already reduced, but their sum is not a u32 quantity */
        const unsigned long long cc = (unsigned long long)c + cb;
        c = (unsigned int)(cc >= (unsigned long long)W2C ? cc - W2C : cc);
#endif
        const unsigned int dcur = W2C - c;
        d2[ss] = dcur;
%(blockpre)s
    }
    __syncthreads();
    const int nss = min(SPB, R2 - s0);
    const bool full = (tbase + (JPT - 1) * TPB < R1) && (nss == SPB);
#else
    const bool full = (tbase + (JPT - 1) * TPB < R1);
#endif

    /* The bounds checks are false only in the last block of each grid
       dimension, so they are hoisted: one test for the whole nest instead
       of one per candidate. */
    if (full) {
#pragma unroll
        for (int jj = 0; jj < JPT; ++jj) {
            const uint2 e1 = res1x[tbase + jj * TPB];
            const unsigned long long b0 = base + (unsigned long long)e1.x;
%(jjpre)s
#if TWOLEVEL
#pragma unroll
            for (int ss = 0; ss < SPB; ++ss)
                STEP(e1.y, d2[ss], ss, jj)
#else
            CAND(b0, 0u, 0, jj)
#endif
        }
    } else {
        for (int jj = 0; jj < JPT; ++jj) {
            const int t = tbase + jj * TPB;
            if (t < R1) {
                const uint2 e1 = res1x[t];
                const unsigned long long b0 = base
                                            + (unsigned long long)e1.x;
%(jjpre)s
#if TWOLEVEL
                /* unrolled with a guard rather than looped to nss: SS
                   indexes a register array and has to stay a compile-time
                   constant, or the array lands in local memory */
#pragma unroll
                for (int ss = 0; ss < SPB; ++ss)
                    if (ss < nss) STEP(e1.y, d2[ss], ss, jj)
#else
                CAND(b0, 0u, 0, jj)
#endif
            }
        }
    }
    __syncthreads();
    const int nq0 = min(qn0, Q0CAP);

    /* The in-block compaction rounds: primes LITN..K2 in CRT-combined
       groups, each round branchless over the previous round's queue and
       packing its survivors into the next.  Generated per configuration. */
%(rounds2)s
    /* THE TAIL DOES NOT RUN HERE.  The survivors are appended to a GLOBAL
       queue and swept by a second kernel that has one item per lane and
       the whole device in flight.  One atomic per BLOCK, not per item. */
    if (threadIdx.x == 0) q3b = (nqR > 0) ? atomicAdd(n3, nqR) : 0;
    __syncthreads();
    for (int idx = threadIdx.x; idx < nqR; idx += TPB) {
        const unsigned long long off = off_of(qkR[idx], base, res1x, d2);
        const int p = q3b + idx;
        /* the same bargain the shared queues make: capacity is a tuning
           constant, and overflow is HARMLESS */
        if (p < q3cap) q3[p] = off;
        else if (tail_survives(off, np_, K2, pk, pmask, pres)) EMIT(off)
    }
}

/* ONE TAIL ROUND, generated once per lanes-per-item value in use: LPI
   lanes hold one item of the incoming queue, test it against primes
   [from, to) LPI at a time with early exit on a vote, and the block
   pushes its survivors to the outgoing queue with ONE global atomic.  The
   last round (to == np_) emits survivors instead.  `nin` is read on the
   DEVICE, so no host round trip separates the rounds; the grid is sized
   from the queue CAPACITY, so blocks past the live count return at once.
   Overflow of the outgoing queue is harmless in the usual way: that item
   finishes its tail on the spot. */
%(tailrounds)s
"""

_TAILROUND = r"""
extern "C" __global__ void tailround%(lpi)d(
        const unsigned long long* __restrict__ qin,
        const int* __restrict__ nin, const int incap,
        unsigned long long* __restrict__ qout, int* nqout, const int outcap,
        const int from, const int to, const int np_,
        unsigned long long* out, int* nout, const int cap,
        const uint4* __restrict__ pk, const unsigned int* __restrict__ pmask,
        const uint4* __restrict__ pres)
{
    enum { LPI = %(lpi)d, IPB = TTPB / %(lpi)d };
    __shared__ unsigned long long sq[IPB];
    __shared__ int sn;
    __shared__ int sbase;
    const int n = min(*nin, incap);
    if (blockIdx.x * IPB >= n) return;
    if (threadIdx.x == 0) sn = 0;
    __syncthreads();
    const bool last = (to >= np_);
    const int i = blockIdx.x * IPB + (int)threadIdx.x / LPI;
    const int l = (int)threadIdx.x & (LPI - 1);
    /* the lanes of one item vote together: a contiguous group of LPI
       lanes inside the warp */
    const unsigned int gm = (LPI == 32) ? 0xFFFFFFFFu
        : (((1u << LPI) - 1u) << ((threadIdx.x & 31u) & ~(unsigned)(LPI - 1)));
    if (i < n) {
        const unsigned long long off = qin[i];
        bool alive = true;
        for (int b0 = from; b0 < to; b0 += LPI * UNROLL) {
            unsigned int kill = 0u;
#pragma unroll
            for (int z = 0; z < UNROLL; ++z) {
                const int idx = b0 + z * LPI + l;
                if (idx < to) TEST(idx, kill)
            }
            if (LPI == 1 ? (kill != 0u) : __any_sync(gm, kill)) {
                alive = false; break; }
        }
        if (alive && l == 0) {
            if (last) EMIT(off)
            else { const int p = atomicAdd(&sn, 1); sq[p] = off; }
        }
    }
    if (last) return;
    __syncthreads();
    if (threadIdx.x == 0) sbase = (sn > 0) ? atomicAdd(nqout, sn) : 0;
    __syncthreads();
    for (int j = threadIdx.x; j < sn; j += TTPB) {
        const int p = sbase + j;
        const unsigned long long off = sq[j];
        if (p < outcap) qout[p] = off;
        else if (tail_survives(off, np_, to, pk, pmask, pres)) EMIT(off)
    }
}
"""


def _qcap(tile, surv, sigma=QCAP_SIGMA):
    """Queue capacity from the ANALYTIC survival, plus sigma of margin."""
    import math
    mean = tile * surv
    sd = math.sqrt(max(tile * surv * (1.0 - surv), 0.0))
    want = int(math.ceil(mean + sigma * sd))
    want = min(max(want, 32), tile)
    return ((want + 31) // 32) * 32


class GpuEngine:
    """Wheel-generated candidates, Barrett-tested against packed tables."""

    def __init__(self, n, fam, p1=P1_DEFAULT, p2=P2_DEFAULT, p3=P3_DEFAULT,
                 q2=Q2_DEFAULT,
                 tpb=TPB_DEFAULT, cpt=None, spb=None,
                 jpt=None, lit=None, k2=None, qcap_sigma=QCAP_SIGMA,
                 nu=None, unit=1):
        import cupy as cp
        self.cp = cp
        self.n = int(n)
        self.fam = family(fam)
        self.s = sign(self.fam)
        # THE UNIT: the device sweeps k' = k / unit.  Every wheel, table,
        # fold and offset below is in k' space; the period the HOST sees
        # (self.W), the survivors it receives and every bound it checks
        # are in k.  `assert_unit` refuses a unit that is not forced at
        # this filter -- the one way this could thin the line.
        self.unit = assert_unit(self.n, self.fam, unit)
        # the tuning set of this wheel family (see the constants above)
        if cpt is None:
            cpt = CPT_UNIT if self.unit > 1 else CPT_DEFAULT
        if spb is None:
            spb = SPB_UNIT if self.unit > 1 else SPB_DEFAULT
        self.nforms = nforms(self.fam, self.n)
        self.lit_target = (lit_surv_unit(self.nforms) if self.unit > 1
                           else LIT_SURV)
        self.k2_target = K2_SURV_UNIT if self.unit > 1 else K2_SURV
        if self.nforms > NRES_MAX:
            raise ValueError(
                f"a filter of {self.nforms} conditions can kill up to "
                f"{self.nforms} residues per prime, and the tail's residue "
                f"list holds NRES_MAX = {NRES_MAX} slots: a longer ladder is a "
                f"new engine version with a wider record, not a constant to "
                f"raise")
        if self.nforms < 1:
            raise ValueError(f"filter n = {n} of {self.fam} imposes no "
                             f"condition; nothing to sieve for")
        self.p1, self.p2, self.p3 = p1, p2, p3
        self.q2, self.tpb = q2, tpb
        fam = self.fam

        self.W1, res1 = wheel(n, fam, p1, unit=self.unit)
        if self.W1 >= 1 << 32:
            raise ValueError(
                f"first-level wheel modulus {self.W1} needs more than u32; "
                f"the residue type is baked into the kernel, so raising P1 "
                f"past this is a new engine version with a new fingerprint")
        self.R1 = int(res1.size)

        if p2 and p2 > p1:
            W2a, res2 = wheel(n, fam, p2, lo=p1, unit=self.unit)
            self.R2 = int(res2.size)
            if self.R2 > 65535:
                raise ValueError(
                    f"second-level wheel has {self.R2} residues; the kernel "
                    f"maps them to gridDim.y, which CUDA caps at 65535")
            wheel_top = p2
        else:
            W2a, res2, self.R2 = 1, None, 1
            wheel_top = p1
        if p3 and p3 > wheel_top and self.R2 > 1:
            W2b, res3 = wheel(n, fam, p3, lo=wheel_top, unit=self.unit)
            self.R3 = int(res3.size)
            if self.R3 > 65535:
                raise ValueError(
                    f"third-level wheel has {self.R3} residues; they ride "
                    f"gridDim.z, which CUDA caps at 65535")
            wheel_top = p3
        else:
            W2b, res3, self.R3 = 1, None, 1
        self.W2 = W2a * W2b
        self.W2a, self.W2b = W2a, W2b
        self.wheel_top = wheel_top
        if self.R2 > 1:
            if self.W2 >= 1 << 32 or self.W1 * self.W2 >= 1 << 63:
                raise ValueError(
                    f"second-level wheel {self.W1}*{self.W2} exceeds the "
                    f"enforced u32/2^63 limits -- m is a u32 and W1*m is "
                    f"the quantity the one-subtraction reduction bounds, so "
                    f"this is where the wheel stops")
            self.Wp = self.W1 * self.W2
            self.R = self.R1 * self.R2 * self.R3
            self.inv = pow(self.W1 % self.W2, -1, self.W2)
        else:
            self.inv = 0
            self.Wp, self.R = self.W1, self.R1
        # Wp is the DEVICE period, in k'; W is the period in k, which is
        # what the cursor counts, the coverage claim is made in, and every
        # ceiling and floor is checked against.
        self.W = self.unit * self.Wp

        # The generation tables: m = ((r2 - r1)*inv) mod W2 splits into one
        # term per index, A[t] = (-r1*inv) mod W2, and r2 splits again by
        # CRT across the second and third levels (CRT lifting is linear),
        # so the kernel adds three reduced numbers instead of storing their
        # R2a*R3 combinations.  uint64 is exact throughout.
        w2 = np.uint64(self.W2)
        r1u = res1.astype(np.uint64)
        res1x = np.empty((self.R1, 2), dtype=np.uint32)
        res1x[:, 0] = r1u.astype(np.uint32)
        if self.R2 > 1:
            a = (r1u % w2) * np.uint64(self.inv) % w2
            res1x[:, 1] = ((w2 - a) % w2).astype(np.uint32)
            if self.R3 > 1:
                ka = W2b * pow(W2b % W2a, -1, W2a) % self.W2
                kb = W2a * pow(W2a % W2b, -1, W2b) % self.W2
            else:
                ka, kb = 1, 0
            ka = np.uint64(ka * self.inv % self.W2)
            c = (res2.astype(np.uint64) % np.uint64(W2a)) * ka % w2
            self.d_res2c = cp.asarray(c.astype(np.uint32))
            if self.R3 > 1:
                kbi = np.uint64(kb * self.inv % self.W2)
                d = (res3.astype(np.uint64) % np.uint64(W2b)) * kbi % w2
                self.d_res2d = cp.asarray(d.astype(np.uint32))
            else:
                self.d_res2d = cp.zeros(1, dtype=np.uint32)
        else:
            res1x[:, 1] = 0
            self.d_res2c = cp.zeros(1, dtype=np.uint32)
            self.d_res2d = cp.zeros(1, dtype=np.uint32)
        self.d_res1x = cp.asarray(res1x.ravel())

        self.primes = [q for q in primerange(wheel_top + 1, q2 + 1)
                       if self.unit % q]
        if not self.primes:
            raise ValueError("no sieve primes above the wheel")
        # survival through each prefix, exactly: an ordered product over
        # the primes involved, which is what both the compaction depths and
        # the queue capacities are sized from (OPTIMIZATION.md 2.6)
        surv, self.surv = 1.0, []
        for q in self.primes:
            self.surv.append(surv)
            surv *= 1.0 - len(killed_residues(q, n, fam, self.unit)) / q
        self.surv.append(surv)

        def depth_for(target):
            for i, sv in enumerate(self.surv):
                if sv <= target:
                    return i
            return len(self.primes)

        self.lit = (depth_for(self.lit_target) if lit is None
                    else min(lit, len(self.primes)))
        self.k2 = (max(self.lit, depth_for(self.k2_target)) if k2 is None
                   else min(max(k2, self.lit), len(self.primes)))
        reps = HOIST_TABLE_REPS if self.R2 > 1 else 2
        self.groups = _fit_groups(self.primes, self.lit, LIT_GROUP_MAX, 0,
                                  GROUP_BYTES_MAX, reps=reps)
        left = GROUP_BYTES_MAX - _group_bytes(self.primes, self.groups, reps)
        self.groups2 = _fit_groups(self.primes, self.k2, K2_GROUP_MAX,
                                   self.lit, max(left, 0))
        # The in-block rounds, as group-index boundaries: a split falls
        # after the first group whose end survival is at or below its
        # fraction, so no group straddles a round.  `bounds2` holds the
        # PRIME-index boundary of each round, lit first and k2 last.
        splits = [0]
        for frac in sorted(R2_SPLITS, reverse=True):
            g = splits[-1]
            while g < len(self.groups2) and \
                    self.surv[self.groups2[g][-1] + 1] > frac:
                g += 1
            if splits[-1] < g < len(self.groups2):
                splits.append(g)
        splits.append(len(self.groups2))
        self.rounds2 = [self.groups2[a:b] for a, b in zip(splits, splits[1:])]
        self.bounds2 = [self.lit] + [self.groups2[b][0] if b < len(self.groups2)
                                     else self.k2 for b in splits[1:]]
        if self.groups2:
            self.bounds2[-1] = self.k2

        # THE TAIL'S TABLES: one uint4 per prime (magic_lo, magic_hi, q,
        # base mod q), one MASK_BITS-bit mask per prime with bit
        # (u mod MASK_BITS) set for every killed residue u -- the exact
        # pattern for q <= MASK_BITS -- and one residue list of NRES u32
        # per prime for the primes above it.  Slot .w is rewritten per
        # launch (base mod q); the rest is built once.  Nothing here is
        # bounded by k.
        if MASK_BITS < 64 or MASK_BITS & (MASK_BITS - 1):
            raise ValueError(f"MASK_BITS = {MASK_BITS} must be a power of two "
                             f">= 64: the mask index is r mod MASK_BITS")
        self.nres = 16 if self.nforms <= 16 else NRES_MAX
        self.mask_words = MASK_BITS // 32
        magic = barrett_magics(self.primes)
        pk = np.zeros((len(self.primes), 4), dtype=np.uint32)
        pk[:, 0] = (magic & np.uint64(0xFFFFFFFF)).astype(np.uint32)
        pk[:, 1] = (magic >> np.uint64(32)).astype(np.uint32)
        pk[:, 2] = np.array(self.primes, dtype=np.uint32)
        pres = np.full((len(self.primes), self.nres), 0xFFFFFFFF,
                       dtype=np.uint32)
        pmask = np.zeros((len(self.primes), self.mask_words), dtype=np.uint32)
        for i, q in enumerate(self.primes):
            kr = killed_residues(q, n, fam, self.unit)
            if len(kr) > self.nres:
                raise ValueError(f"prime {q} kills {len(kr)} residues, over "
                                 f"the {self.nres}-slot list")
            pres[i, :len(kr)] = kr
            for u in kr:
                um = u % MASK_BITS
                pmask[i, um >> 5] |= np.uint32(1) << np.uint32(um & 31)
        self._pk = pk
        self._qs = np.array(self.primes, dtype=np.uint64)
        # W mod q per prime, so a launch's `base mod q` is one vectorised
        # multiply-and-reduce over the primes rather than one big-int
        # division each: base = W*j, so base mod q = (W mod q)*j mod q.
        self._wmod = np.array([self.Wp % q for q in self.primes],
                              dtype=np.uint64)
        self.d_pres = cp.asarray(pres.ravel())
        self.d_pmask = cp.asarray(pmask.ravel())
        self.d_pk = cp.asarray(pk.ravel())
        # TWO survivor buffers: launch i+1 is on the device BEFORE launch
        # i's survivors are read back, so the device never waits for the
        # host.  The readback itself is asynchronous -- count and the first
        # PRE_COPY survivors are copied into PINNED host memory behind each
        # launch and an event marks when they landed -- because a plain
        # `.get()` on the null stream would queue behind the next launch
        # and wait for it too.
        self.d_out = [cp.empty(HIT_CAP, dtype=np.uint64) for _ in range(2)]
        self.d_n = [cp.zeros(1, dtype=np.int32) for _ in range(2)]
        self._pre = min(PRE_COPY, HIT_CAP)
        self._h_n, self._h_out, self._ev = [], [], []
        for _ in range(2):
            pn = cp.cuda.alloc_pinned_memory(4)
            po = cp.cuda.alloc_pinned_memory(8 * self._pre)
            self._h_n.append(np.frombuffer(pn, dtype=np.int32, count=1))
            self._h_out.append(np.frombuffer(po, dtype=np.uint64,
                                             count=self._pre))
            self._ev.append(cp.cuda.Event(block=False, disable_timing=True))
        self._buf = 0
        self._flush = cp.cuda.Stream.null

        # a one-level wheel has no second level to spread a block over,
        # so the candidates per thread come back from SPB into JPT
        self.spb = 1 << (max(1, min(spb, self.R2)).bit_length() - 1)
        self.jpt = jpt if jpt is not None else max(1, cpt // self.spb)
        self.tile = self.tpb * self.jpt * self.spb   # candidates per block
        self.logtpb = self.tpb.bit_length() - 1
        self.logspb = self.spb.bit_length() - 1
        if (1 << self.logtpb) != self.tpb or (1 << self.logspb) != self.spb:
            raise ValueError(
                f"tpb={self.tpb} and spb={self.spb} must both be powers of "
                f"two: the shared queues store a candidate's (jj, ss, tid) "
                f"index rather than its offset, and it is unpacked by shifts")
        # gridDim.z is ONE budget shared by the wheel periods a launch
        # batches and the third-level residues it carries, z = period*NU + u,
        # so periods may be batched only when the WHOLE third level fits in
        # one launch.
        cand_per_u = self.R1 * self.R2
        self.nu = max(1, min(self.R3, 65535,
                             CAND_PER_LAUNCH // max(cand_per_u, 1)
                             if nu is None else nu))
        self.per_launch = (1 if self.nu < self.R3 else
                           max(1, min(65535 // self.nu,
                                      CAND_PER_LAUNCH // self.R)))
        # the one-subtraction bound: the largest quantity the kernel ever
        # reduces is one wheel period wider than the largest offset (the
        # hoisted prefix reduces b0 + W1*A, whose second term reaches W)
        while ((self.per_launch + 1) * self.Wp + self.q2 >= REDUCE_MAX
               and self.per_launch > 1):
            self.per_launch //= 2
        if (self.per_launch + 1) * self.Wp + self.q2 >= REDUCE_MAX:
            raise ValueError(
                f"one wheel block is W' = {self.Wp}, and W' + q2 is not below "
                f"2^63: the kernel's single conditional subtraction is only "
                f"exact there, so this wheel needs a new reduction "
                f"(CONVENTIONS.md numeric hygiene)")

        # one shared queue per round boundary: queue 0 holds the prefix's
        # survivors, queue r those of in-block round r, the last feeds the
        # global push
        self.qcaps = [_qcap(self.tile, self.surv[b], qcap_sigma)
                      for b in self.bounds2]
        if self.k2 <= self.lit:
            self.qcaps = [self.qcaps[0]]
        self.q1cap = self.qcaps[0]
        self.q2cap = self.qcaps[-1] if len(self.qcaps) > 1 else 1
        cand = self.R1 * self.R2 * self.nu * self.per_launch
        self.q3cap = min(Q3_MAX,
                         max(1024, _qcap(cand, self.surv[self.k2],
                                         qcap_sigma)))

        # The tail's rounds: prime-index boundaries from the survival curve,
        # each round ending where the survival since its start has fallen
        # to TAIL_ROUND_DROP, the last at the sieve's end.  Every round has
        # its own analytic capacity (its input's expected count plus
        # margin), its lanes-per-item from that count, and two global
        # queues ping-pong between rounds; one counter per round boundary,
        # zeroed together once per launch.
        self.rounds, self.round_cap, self.round_lpi = [], [], []
        b = self.k2
        np_ = len(self.primes)
        while True:
            # at least one round, even an empty one: a configuration whose
            # in-block rounds already reach the sieve's end still needs
            # the round that EMITS its global queue
            e = b + 1
            while e < np_ and self.surv[e] > self.surv[b] * TAIL_ROUND_DROP:
                e += 1
            e = min(e, np_)
            self.rounds.append((b, e))
            items = cand * self.surv[b]
            self.round_cap.append(
                min(Q3_MAX, max(1024, _qcap(cand, self.surv[b], qcap_sigma))))
            lpi = 1
            while lpi < 32 and items * lpi < TAIL_FILL:
                lpi *= 2
            self.round_lpi.append(lpi)
            b = e
            if b >= np_:
                break
        self.q3cap = self.round_cap[0]
        self.tail_tpb = TAIL_TPB
        self.q3caps = [self.q3cap,
                       self.round_cap[1] if len(self.rounds) > 1 else 1]
        self.d_q3 = [cp.empty(c, dtype=np.uint64) for c in self.q3caps]
        self.d_n3 = cp.zeros(len(self.rounds) + 1, dtype=np.int32)

        if self.R2 > 1:
            (prefix_src, gtable, self.gdesc,
             pdecl, blockpre, jjpre) = lit_prefix(
                n, fam, self.primes, self.groups, pname="gp",
                hoist=(self.W1, self.Wp), unit=self.unit)
        else:
            prefix_src, gtable, self.gdesc = lit_prefix(
                n, fam, self.primes, self.groups, pname="gp", unit=self.unit)
            pdecl = blockpre = jjpre = ""
        self.d_gbits = cp.asarray(gtable)
        r2_src, g2table, self.gdesc2 = lit_prefix(
            n, fam, self.primes, self.groups2, table="g2bits", indent=8,
            pname="g2p", unit=self.unit)
        self.d_g2bits = cp.asarray(g2table)
        # one generated line per group, sliced into rounds
        r2_lines = r2_src.split("\n") if self.groups2 else []
        assert len(r2_lines) == len(self.groups2)
        R = len(self.rounds2) if self.groups2 else 0
        qcaps_src = "\n".join(f"#define Q{i}CAP {c}"
                               for i, c in enumerate(self.qcaps))
        qdecl = "\n".join(f"    __shared__ QTYPE qk{i}[Q{i}CAP];\n"
                           f"    __shared__ int qn{i};"
                           for i in range(len(self.qcaps)))
        qzero = " ".join(f"qn{i} = 0;" for i in range(len(self.qcaps)))
        rounds_src, g0 = [], 0
        for r in range(1, R + 1):
            g1 = g0 + len(self.rounds2[r - 1])
            kend = self.bounds2[r]
            body = "\n".join(r2_lines[g0:g1])
            rounds_src.append(f"""    for (int idx = threadIdx.x; idx < nq{r-1}; idx += TPB) {{
        const unsigned int qi = qk{r-1}[idx];
        const unsigned long long off = off_of(qi, base, res1x, d2);
        unsigned int kill = 0u;
{body}
        if (!kill) {{
            const int p = atomicAdd(&qn{r}, 1);
            if (p < Q{r}CAP) qk{r}[p] = (QTYPE)qi;
            else if (tail_survives(off, np_, {kend}, pk, pmask, pres)) EMIT(off)
        }}
    }}
    __syncthreads();
    const int nq{r} = min(qn{r}, Q{r}CAP);""")
            g0 = g1
        rounds_src.append(f"    const int nqR = nq{R};\n"
                          f"    QTYPE* const qkR = qk{R};")
        rounds2_src = "\n".join(rounds_src)
        gparams = "".join(
            f",\n        const unsigned long long {p}{i}"
            for p, d in (("gp", self.gdesc), ("g2p", self.gdesc2))
            for i in range(len(d)))
        prefix_m = "\n".join(ln + " \\" for ln in prefix_src.split("\n"))

        # The generated SOURCE does not depend on the sign: every kill
        # pattern is either a device array or a launch scalar, and w(q,n)
        # -- hence the survival curve, the compaction depths and the group
        # moduli -- is sign-independent (lladder_reference G2c).  So a
        # family and its sign twin share one compiled module; the key
        # carries the w-class (kind, rungs_from) and every derived
        # quantity, and G9 runs several families through it.
        key = (n, FAMILIES[fam]["kind"], FAMILIES[fam]["rungs_from"],
               self.unit, self.W1, self.W2, q2, tpb, self.jpt, self.spb,
               self.lit, self.k2, self.R3, self.nu, MASK_BITS, self.nres,
               tuple(self.round_lpi), TAIL_TPB,
               tuple(self.qcaps), tuple(self.bounds2),
               tuple(map(tuple, self.groups)),
               tuple(map(tuple, self.groups2)))
        if key not in _MODCACHE:
            src = _SRC % {"w1": self.W1, "w2": self.W2, "w": self.Wp,
                          "two": 1 if self.R2 > 1 else 0, "lit": self.lit,
                          "three": 1 if self.R3 > 1 else 0, "nu": self.nu,
                          "k2": self.k2, "jpt": self.jpt, "tpb": tpb,
                          "spb": self.spb,
                          "logtpb": self.logtpb, "logspb": self.logspb,
                          "qtype": ("unsigned short" if self.tile <= 65535
                                    else "unsigned int"),
                          "unroll": UNROLL, "qcaps": qcaps_src,
                          "qdecl": qdecl, "qzero": qzero,
                          "rounds2": rounds2_src, "prefix_m": prefix_m,
                          "pdecl": pdecl, "blockpre": blockpre,
                          "jjpre": jjpre,
                          "round2": r2_src, "gparams": gparams,
                          "mask_bits": MASK_BITS, "nres": self.nres,
                          "ttpb": TAIL_TPB,
                          "tailrounds": "".join(
                              _TAILROUND % {"lpi": l}
                              for l in sorted(set(self.round_lpi)))}
            _MODCACHE[key] = cp.RawModule(code=src, options=("-std=c++14",),
                                          backend="nvrtc")
        self.k_sieve = _MODCACHE[key].get_function("sieve")
        self.k_tails = {l: _MODCACHE[key].get_function(f"tailround{l}")
                        for l in set(self.round_lpi)}
        self.k_tail = self.k_tails[self.round_lpi[0]]

    # ------------------------------------------------------------- geometry
    def j_of(self, k):
        """The wheel block a k lives in."""
        return int(k) // self.W

    def density(self):
        """Candidates per unit of k line -- what the wheel is worth."""
        return self.R / float(self.W)

    def bytes_held(self):
        n = (self.d_res1x.nbytes + self.d_pres.nbytes + self.d_pk.nbytes
             + self.d_pmask.nbytes
             + sum(b.nbytes for b in self.d_out)
             + self.d_res2c.nbytes + self.d_res2d.nbytes
             + self.d_gbits.nbytes + self.d_g2bits.nbytes
             + sum(q.nbytes for q in self.d_q3))
        return int(n)

    def config(self):
        return {"n": self.n, "fam": self.fam, "s": self.s, "p1": self.p1,
                "p2": self.p2, "p3": self.p3, "q2": self.q2,
                "unit": self.unit, "W": int(self.W), "Wp": int(self.Wp),
                "R": int(self.R), "R1": self.R1, "R2": self.R2,
                "R3": self.R3, "nu": self.nu, "per_launch": self.per_launch,
                "lit": self.lit, "k2": self.k2, "groups": self.groups,
                "groups2": self.groups2, "q1cap": self.q1cap,
                "q2cap": self.q2cap, "qcaps": self.qcaps,
                "bounds2": self.bounds2, "q3cap": self.q3cap,
                "rounds": self.rounds, "round_lpi": self.round_lpi}

    # ---------------------------------------------------------------- sieve
    def _launch_base(self, base):
        """Fold an absolute launch base into the tables, on the host.

        `base` is a Python int of any size, in k' (the device's units);
        what reaches the device is `base mod q` per prime (slot 3 of the
        record) and `base mod Q` per CRT group (the gp/g2p scalars).  Both
        are bounded by their modulus, so the device arithmetic never
        learns how large k has become.
        """
        j = int(base) // self.Wp
        if j < (1 << 64):
            bmod = (self._wmod
                    * (np.uint64(j) % self._qs)) % self._qs
        else:
            bmod = np.array([(int(w) * (j % int(q))) % int(q)
                             for w, q in zip(self._wmod, self._qs)],
                            dtype=np.uint64)
        self._pk[:, 3] = bmod.astype(np.uint32)
        self.d_pk.set(self._pk.ravel())
        return (group_params(self.gdesc, base)
                + group_params(self.gdesc2, base))

    def _check_window(self, j0, j1, k_min):
        """The eager bounds checks shared by survivors_j and sweep.

        Without `k_min` the window must start above the engine floor.  With
        it the window may start anywhere -- period 0 included -- and every
        survivor below k_min is dropped on the host; what is required is
        then that k_min itself is above the floor, since that is where the
        sieve's argument holds.  Returns the effective clip (k_min, or 0
        when none is needed).
        """
        ceil = k_ceil(self.n, self.fam)
        if j1 * self.W > ceil:
            raise ValueError(f"k {j1 * self.W} past the enforced ceiling "
                             f"{ceil}")
        floor = k_floor(self.q2)
        if k_min is None:
            if j0 * self.W <= floor:
                raise ValueError(
                    f"engines refuse to run at or below max(K_FLOOR, q2 + 1) "
                    f"= {floor}: the wheel argument has an exception zone "
                    f"there and a kill by q needs value > q; pass k_min to "
                    f"start inside the first period")
            return 0
        k_min = int(k_min)
        if k_min <= floor:
            raise ValueError(
                f"k_min = {k_min} is at or below max(K_FLOOR, q2 + 1) = "
                f"{floor}: survivors there are not survivors, so the clip "
                f"may not start under the engine floor")
        return k_min

    def survivors_j(self, j0, j1, k_min=None):
        """Sorted list of surviving k (Python ints) with k // W in [j0, j1),
        and k >= k_min if one is given.

        Ints, not a u64 array: above 2^64 there is no numpy dtype for the
        answer, and the survivors are a handful per launch, so the exact
        values are assembled on the host where bigness is free.
        """
        out = []
        for _, _, surv in self.sweep(j0, j1, k_min=k_min):
            out.extend(surv)
        return sorted(out)

    def sweep(self, j0, j1, u_from=0, k_min=None):
        """Yield (j_next, u_next, survivors) after every kernel launch.

        `(j_next, u_next)` is a RESUMABLE cursor and `u_next == 0` means the
        stronger thing: every k below `j_next * W` has been swept, so the
        coverage claim may advance.  The two differ because a third wheel
        level makes candidates come out in (t, s, u) order rather than in k
        order, and only a whole period is contiguous in k.

        The bounds are checked EAGERLY, here, and the launches are a
        separate generator: a `yield` in this body would defer every check
        to the first `next()`.
        """
        j0, j1, u_from = int(j0), int(j1), int(u_from)
        clip = self._check_window(j0, j1, k_min)
        return self._sweep(j0, j1, u_from, clip)

    def _sweep(self, j0, j1, u_from, clip):
        gx = (self.R1 + self.tpb * self.jpt - 1) // (self.tpb * self.jpt)
        gy = (self.R2 + self.spb - 1) // self.spb
        pending = None
        for lo in range(0, j1 - j0, self.per_launch):
            n_l = min(self.per_launch, j1 - j0 - lo)
            base = self.Wp * (j0 + lo)           # in k': the device's units
            # _launch_base rewrites the folded tables, so the launch it
            # belongs to must not be enqueued while an older one is still
            # reading them -- drain first.
            drained = self._collect(pending, clip)
            pending = None
            gps = self._launch_base(base)
            if drained is not None:
                yield drained
            for u0 in range(u_from, self.R3, self.nu):
                nu_l = min(self.nu, self.R3 - u0)
                nxt = u0 + nu_l
                cur = ((j0 + lo + n_l, 0) if nxt >= self.R3
                       else (j0 + lo, nxt))
                # THIS launch goes to the device before the PREVIOUS one is
                # read back, so the device always has work queued.
                b = self._buf = self._buf ^ 1
                self._enqueue(b, gx, gy, n_l, nu_l, u0, gps)
                done = self._collect(pending, clip)
                pending = (base, b, cur)
                if done is not None:
                    yield done
            u_from = 0
        done = self._collect(pending, clip)
        if done is not None:
            yield done

    def _enqueue(self, b, gx, gy, n_l, nu_l, u0, gps):
        """Enqueue one launch: counters zeroed, the sieve, the tail rounds,
        the asynchronous readback of its survivors, and the WDDM flush."""
        np_ = np.int32(len(self.primes))
        self.d_n[b].fill(0)
        self.d_n3.fill(0)
        self.k_sieve((gx, gy, n_l * nu_l), (self.tpb,),
                     (np.int32(self.R1), np.int32(self.R2), np_,
                      self.d_pmask, self.d_pres,
                      self.d_out[b], self.d_n[b], np.int32(HIT_CAP),
                      self.d_q3[0], self.d_n3, np.int32(self.q3cap),
                      self.d_pk, self.d_res1x, self.d_res2c,
                      self.d_res2d, np.int32(u0),
                      self.d_gbits, self.d_g2bits, *gps))
        R = len(self.rounds)
        for r, (fr, to) in enumerate(self.rounds):
            qi, qo = self.d_q3[r & 1], self.d_q3[(r + 1) & 1]
            ci = self.round_cap[r]
            co = self.round_cap[r + 1] if r + 1 < R else 1
            lpi = self.round_lpi[r]
            grid = max(1, -(-ci // (self.tail_tpb // lpi)))
            self.k_tails[lpi]((grid,), (self.tail_tpb,),
                              (qi, self.d_n3[r:r + 1], np.int32(ci),
                               qo, self.d_n3[r + 1:r + 2], np.int32(co),
                               np.int32(fr), np.int32(to), np_,
                               self.d_out[b], self.d_n[b], np.int32(HIT_CAP),
                               self.d_pk, self.d_pmask, self.d_pres))
        # the readback rides the same stream, straight into pinned memory,
        # and the event says when it has landed
        self.d_n[b].get(out=self._h_n[b], blocking=False)
        self.d_out[b][:self._pre].get(out=self._h_out[b], blocking=False)
        self._ev[b].record()
        # FLUSH: on WDDM a launch is batched in a user-mode command buffer
        # until something forces a submit; a stream query is the documented
        # way to flush, and without it the host's classification runs
        # against an IDLE device.
        self._flush.done

    def _collect(self, pending, clip=0):
        """(j_next, u_next, survivors) for an enqueued launch, or None.

        Waits on THAT launch's readback event -- not on the stream, which
        by now carries the launch after it."""
        if pending is None:
            return None
        base, b, (jn, un) = pending
        self._ev[b].synchronize()
        cnt = int(self._h_n[b][0])
        if cnt > HIT_CAP:
            raise RuntimeError(
                f"survivor buffer overflow: {cnt} > {HIT_CAP}; the "
                f"window is too wide or the sieve too shallow")
        surv = []
        if cnt:
            if cnt <= self._pre:
                offs = self._h_out[b][:cnt]
            else:
                offs = self.cp.asnumpy(self.d_out[b][:cnt])
            # back to k: the one place the unit is multiplied in
            surv = sorted(v for v in (self.unit * (base + int(o))
                                      for o in offs.tolist())
                          if v >= clip)
        return jn, un, surv

    def survivors_k(self, k_lo, k_hi):
        """Same stream, clipped to an arbitrary half-open k window.

        Starts inside period 0 when it has to (k_lo above the floor is all
        the sieve needs), so a gate can compare a window that no whole
        period could reach."""
        k_lo, k_hi = int(k_lo), int(k_hi)
        j0, j1 = k_lo // self.W, (k_hi - 1) // self.W + 1
        k_min = k_lo if j0 * self.W <= k_floor(self.q2) else None
        return [k for k in self.survivors_j(j0, j1, k_min=k_min)
                if k_lo <= k < k_hi]


# --------------------------------- gates -----------------------------------

def g7_wheel_matches_oracle():
    """The CRT-lifted wheel == the oracle's brute-force walk of the period,
    for several families; and the CRT recombination reproduces the
    one-level wheel exactly."""
    fams = ("A088250", "A125838", "A164326")
    for fam in fams:
        for n, p1 in ((5, 7), (10, 11), (15, 11), (15, 13), (16, 13)):
            W, res = wheel(n, fam, p1)
            Wo, reso = wheel_residues(fam, n, p1)
            if W != Wo or list(res) != list(reso):
                return False, (f"G7 FAIL: {fam} n={n} p1={p1}: lifted "
                               f"{len(res)} residues mod {W}, oracle "
                               f"{len(reso)} mod {Wo}")
        for n, p1, p2 in ((15, 7, 13), (15, 11, 17), (10, 7, 11)):
            W1, r1 = wheel(n, fam, p1)
            W2, r2 = wheel(n, fam, p2, lo=p1)
            inv = pow(W1 % W2, -1, W2)
            got = sorted(int(a) + W1 * (((int(b) - int(a)) * inv) % W2)
                         for a in r1 for b in r2)
            Wf, ref_res = wheel(n, fam, p2)
            if W1 * W2 != Wf or got != [int(v) for v in ref_res]:
                return False, (f"G7 FAIL: {fam} CRT recombination at n={n} "
                               f"({p1},{p2}]: {len(got)} vs {len(ref_res)}")
        # UNIT SPACE: the k' wheel == a brute-force walk of ITS period
        # checked against the ORACLE's k-space divisibility on k = unit*k'
        # -- the definition, not the engines' construction -- and the CRT
        # recombination holds with a unit too
        for n, p1, unit in ((15, 19, 30030), (16, 23, 30030), (10, 13, 2310)):
            if forced_unit(n, fam) % unit:
                continue                 # not forced here: nothing to check
            W, res = wheel(n, fam, p1, unit=unit)
            qs = [q for q in primerange(2, p1 + 1) if unit % q]
            Wo = 1
            for q in qs:
                Wo *= q
            killed = {q: forbidden_k_residues(q, n, fam) for q in qs}
            reso = [r for r in range(Wo)
                    if all((unit * r) % q not in killed[q] for q in qs)]
            if W != Wo or list(res) != reso:
                return False, (f"G7 FAIL: {fam} n={n} p1={p1} unit={unit}: "
                               f"lifted {len(res)} residues mod {W}, oracle "
                               f"walk {len(reso)} mod {Wo}")
        for n, p1, p2, unit in ((15, 19, 29, 30030), (16, 23, 31, 30030)):
            if forced_unit(n, fam) % unit:
                continue
            W1, r1 = wheel(n, fam, p1, unit=unit)
            W2, r2 = wheel(n, fam, p2, lo=p1, unit=unit)
            inv = pow(W1 % W2, -1, W2)
            got = sorted(int(a) + W1 * (((int(b) - int(a)) * inv) % W2)
                         for a in r1 for b in r2)
            Wf, ref_res = wheel(n, fam, p2, unit=unit)
            if W1 * W2 != Wf or got != [int(v) for v in ref_res]:
                return False, (f"G7 FAIL: {fam} CRT recombination with unit "
                               f"{unit} at n={n} ({p1},{p2}]: {len(got)} vs "
                               f"{len(ref_res)}")
    # and the A088651 unit, 510510, at its opening filter
    W, res = wheel(16, "A088651", 23, unit=510510)
    qs = [q for q in primerange(2, 24) if 510510 % q]
    Wo = 1
    for q in qs:
        Wo *= q
    killed = {q: forbidden_k_residues(q, 16, "A088651") for q in qs}
    reso = [r for r in range(Wo) if all((510510 * r) % q not in killed[q]
                                        for q in qs)]
    if W != Wo or list(res) != reso:
        return False, "G7 FAIL: the A088651 unit-510510 wheel != oracle walk"
    return True, ("G7 ok: CRT-lifted wheel == oracle period walk at (n,p1) = "
                  "(5,7), (10,11), (15,11), (15,13), (16,13) for A088250, "
                  "A125838 and A164326; the two-level CRT recombination == "
                  "the one-level wheel at three (p1,p2] splits; in unit space "
                  "the k' wheel == the oracle's divisibility on k = unit*k' "
                  "at units 2310 and 30030 (and 510510 for A088651 at "
                  "n = 16) and recombines across two levels")


def g8_wheel_partitions_the_period():
    """Kept + killed == the whole period, and the count is the formula.

    The direction that matters is the second one: a wheel that DROPS a
    residue it should have kept loses candidates silently, and no parity
    gate against another engine using the same wheel could ever see it.
    """
    from lladder_reference import w as w_formula
    cases = []
    for fam in ("A088250", "A173750", "A164326"):
        cases += [(fam, 15, 13, 1, 1), (fam, 15, 23, 1, 1), (fam, 12, 23, 1, 1),
                  (fam, 16, 19, 1, 1), (fam, 15, 37, 23, 1),
                  (fam, 15, 31, 23, 1), (fam, 16, 47, 37, 1)]
    # the production levels, in unit space, at each family's opening filter
    # and the two after it
    for fam in FAMILIES:
        n0 = max(KNOWN[fam]) + 1
        unit = forced_unit(n0, fam)
        for n in (n0, n0 + 1, n0 + 2):
            cases += [(fam, n, 31, 1, unit), (fam, n, 41, 31, unit),
                      (fam, n, 53, 41, unit)]
    for fam, n, p1, lo, unit in cases:
        W, res = wheel(n, fam, p1, lo=lo, unit=unit)
        qs = [q for q in primerange(lo + 1, p1 + 1) if unit % q]
        want = 1
        for q in qs:
            want *= q - w_formula(q, n, fam)
        if res.size != want:
            return False, (f"G8 FAIL: {fam} n={n} ({lo},{p1}] unit {unit}: "
                           f"{res.size} residues, formula says {want}")
        if len(set(res.tolist())) != res.size:
            return False, f"G8 FAIL: {fam} n={n} ({lo},{p1}]: duplicate residues"
        for q in qs:
            bad = set(killed_residues(q, n, fam, unit))
            if np.isin(res % q, np.array(sorted(bad), dtype=np.int64)).any():
                return False, (f"G8 FAIL: {fam} n={n} ({lo},{p1}] unit {unit}: "
                               f"a kept residue is killed by q={q}")
    return True, (f"G8 ok: the wheel is exactly prod(q - w(q,n)) residues, "
                  f"duplicate-free, none of them killed by a wheel prime, on "
                  f"{len(cases)} (family, n, level, unit) cases: k-space "
                  f"levels for three families and the production levels "
                  f"(..31], (31,41], (41,53] at every family's opening unit, "
                  f"at its opening filter and the two after it")


def g9_gpu_matches_cpu():
    """GPU survivor stream == CPU survivor stream, bit for bit.

    Populated windows at several filters and heights, several families,
    one-, two- and three-level wheels, the top windows hard against the
    enforced ceilings and ABOVE 2^64 (the CPU side is Python ints all the
    way up), and a CLIPPED PERIOD 0 -- the window every campaign here
    starts in.  An empty-vs-empty comparison is vacuous and is refused.

    The windows are wide because survivors are sparse: forced divisibility
    alone leaves one k in 30030 at n = 15.
    """
    ceil_p = k_ceil(15, "A088250")             # 3.3e24, the +1 ceiling
    ceil_m = k_ceil(15, "A125838")             # 2.2e23, a -1 crossing
    W23 = 223_092_870
    fl = k_floor(128) + 1
    cases = (
        # fam, n, p1, p2, p3, q2, k_lo, span, unit
        # (the n = 15/16/17 windows run a sieve to 32 or 64: at those
        # filters the sieve is so strong that a depth of 128 leaves 0.2
        # survivors in 4e8 of line, and a dense CPU sieve wide enough to
        # populate that would cost the battery a minute per window)
        ("A088250", 10, 13, None, None, 256, 2 * 10 ** 9, 4 * 10 ** 7, 1),
        ("A088250", 15, 13, None, None, 32, 10 ** 12, 4 * 10 ** 8, 1),
        ("A125838", 12, 17, None, None, 128, 9 * 10 ** 14, 2 * 10 ** 8, 1),
        ("A088250", 15, 23, None, None, 32, ceil_p - 5 * W23, 6 * 10 ** 8, 1),
        ("A088250", 15, 13, 23, None, 32, 10 ** 12, 4 * 10 ** 8, 1),
        ("A164326", 15, 13, 17, None, 32, 9 * 10 ** 14, 4 * 10 ** 8, 1),
        ("A088250", 15, 11, 23, None, 32, ceil_p - 5 * W23, 6 * 10 ** 8, 1),
        ("A088250", 10, 11, 13, 17, 256, 2 * 10 ** 9, 4 * 10 ** 7, 1),
        ("A125839", 12, 11, 13, 17, 64, 10 ** 12, 10 ** 8, 1),
        ("A173750", 16, 13, 17, 19, 32, 9 * 10 ** 14, 4 * 10 ** 8, 1),
        ("A088250", 15, 17, 19, 23, 32, ceil_p - 5 * W23, 6 * 10 ** 8, 1),
        # PERIOD 0, clipped at the engine floor: the campaign's first window
        ("A088250", 10, 13, 23, None, 128, fl, W23 - fl, 1),
        ("A164326", 12, 13, 23, None, 128, fl, W23 - fl, 1),
        # UNIT SPACE: the device sweeps k' = k / unit and the host
        # multiplies back; the CPU engine still marks the dense k line, so
        # the forcing lemma is checked here as well as the fold -- one-,
        # two- and three-level unit wheels, several families and units, at
        # heights up to the +1 ceiling (3.3e24, above 2^64), a -1 crossing,
        # and period 0 clipped at the floor
        ("A088250", 10, 13, None, None, 128, 2 * 10 ** 9, 4 * 10 ** 7, 2310),
        ("A088250", 15, 19, 23, 29, 32, 10 ** 12, 4 * 10 ** 8, 30030),
        ("A088250", 15, 19, 23, None, 32, ceil_p - 5 * 10 ** 9, 6 * 10 ** 8,
         30030),
        ("A088250", 17, 19, 23, 29, 32, ceil_p - 10 ** 13, 2 * 10 ** 9, 30030),
        ("A125838", 15, 19, 23, 29, 32, 9 * 10 ** 14, 4 * 10 ** 8, 30030),
        ("A125838", 15, 19, 23, None, 32, ceil_m - 10 ** 12, 6 * 10 ** 8, 30030),
        ("A164325", 16, 19, 23, 29, 32, 10 ** 12, 8 * 10 ** 8, 30030),
        ("A088651", 16, 19, 23, 29, 32, 10 ** 12, 10 ** 9, 510510),
        ("A088250", 15, 17, 19, 23, 32, fl, 30030 * 7429 - fl, 30030),
    )
    total = 0
    for fam, n, p1, p2, p3, q2, k_lo, span, unit in cases:
        eng = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit)
        got = eng.survivors_k(k_lo, k_lo + span)
        cpu = CpuEngine(n, fam, q2=q2)
        want = [k for c in cpu.survivors(k_lo, k_lo + span) for k in c]
        if got != want:
            gs, ws = set(got), set(want)
            return False, (f"G9 FAIL: {fam} n={n} p1={p1} p2={p2} p3={p3} "
                           f"q2={q2} unit={unit} at k~{k_lo:.3g}: GPU "
                           f"{len(got)} vs CPU {len(want)}, diff "
                           f"{sorted(gs ^ ws)[:4]}")
        if not got:
            return False, (f"G9 FAIL: {fam} n={n} p1={p1} p2={p2} p3={p3} "
                           f"unit={unit} at k~{k_lo:.3g} is empty -- vacuous "
                           f"parity check")
        total += len(got)
    return True, (f"G9 ok: GPU stream == CPU stream on {len(cases)} populated "
                  f"windows ({total} survivors) -- one-, two- and three-level "
                  f"wheels in k space AND in unit space (2310, 30030, "
                  f"510510), six families, filters n = 10 to 17, heights 2e9 "
                  f"-> {ceil_p:.3g} with the top windows ABOVE 2^64 and one "
                  f"against a -1 crossing, and period 0 clipped at the "
                  f"engine floor on both")


def g13_production_wheel_constants():
    """The baked CRT constants of the configurations the campaigns run.

    G9 proves the multi-level KERNEL is right, but only at splits whose
    combined wheel a dense CPU sieve can follow.  The production split is
    bigger than that by orders of magnitude, and what differs there is not
    code but literals compiled into the source: W1, W2 and W1^-1 mod W2.
    This gate checks those literals directly, on the host, against the
    definition, for the filters every family will actually run.
    """
    rng = np.random.default_rng(20260903)
    from lladder_reference import forced_primes, w as w_formula
    cases = [("A088250", 15, 23, 37, 47, 1), ("A088250", 16, 23, 37, 47, 1),
             ("A125838", 15, 23, 37, 47, 1), ("A164325", 16, 23, 37, None, 1)]
    for fam in FAMILIES:
        n0 = max(KNOWN[fam]) + 1
        unit = forced_unit(n0, fam)
        for n in (n0, n0 + 1, n0 + 2, n0 + 3):
            cases.append((fam, n, 31, 41, 53, unit))
    for fam, n, p1, p2, p3, unit in cases:
        W1, r1 = wheel(n, fam, p1, unit=unit)
        W2a, r2 = wheel(n, fam, p2, lo=p1, unit=unit)
        if p3:
            W2b, r3 = wheel(n, fam, p3, lo=p2, unit=unit)
            EA = W2b * pow(W2b % W2a, -1, W2a)
            EB = W2a * pow(W2a % W2b, -1, W2b)
        else:
            W2b, r3, EA, EB = 1, np.zeros(1, dtype=np.int64), 1, 0
        W2 = W2a * W2b
        if W2 >= 1 << 32 or W1 >= 1 << 32 or W1 * W2 >= 1 << 63:
            return False, (f"G13 FAIL: {fam} n={n} ({p1},{p2},{p3}] unit "
                           f"{unit}: W1 = {W1}, W2 = {W2} exceed the u32 / "
                           f"2^63 bounds the kernel's arithmetic rests on")
        inv = pow(W1 % W2, -1, W2)
        if W1 % W2 * inv % W2 != 1:
            return False, f"G13 FAIL: {fam} n={n} ({p1},{p2}]: W1^-1 is wrong"
        top = p3 or p2
        qs = [q for q in primerange(2, top + 1) if unit % q]
        want = 1
        for q in qs:
            want *= q - w_formula(q, n, fam)
        if r1.size * r2.size * r3.size != want:
            return False, (f"G13 FAIL: {fam} n={n} ({p1},{p2},{p3}] unit "
                           f"{unit}: {r1.size}*{r2.size}*{r3.size} != {want}")
        # the kill check is in K SPACE, on k = unit*x, against the k-space
        # killed set: the unit's own primes included, which must never
        # kill a multiple of the unit
        killed = {q: set(killed_residues(q, n, fam))
                  for q in primerange(2, top + 1)}
        forced = 1
        for q in forced_primes(fam, n, upto=top + 1):
            forced *= q
        ts = rng.integers(0, r1.size, 3000)
        ss = rng.integers(0, r2.size, 3000)
        us = rng.integers(0, r3.size, 3000)
        for t, sx, u in zip(ts.tolist(), ss.tolist(), us.tolist()):
            a, b = int(r1[t]), int(r2[sx])
            c = int(r3[u])
            bc = (EA * b + EB * c) % W2
            x = a + W1 * (((bc - a) * inv) % W2)
            if not 0 <= x < W1 * W2:
                return False, f"G13 FAIL: {fam} n={n} CRT value {x} out of range"
            if x % W1 != a or x % W2a != b or (p3 and x % W2b != c):
                return False, (f"G13 FAIL: {fam} n={n} CRT value {x} does not "
                               f"recombine to ({a}, {b}, {c})")
            for q, bad in killed.items():
                if (unit * x) % q in bad:
                    return False, (f"G13 FAIL: {fam} n={n} ({p1},{p2},{p3}] "
                                   f"unit {unit}: k = {unit}*{x} is killed by "
                                   f"q={q}")
            if (unit * x) % forced:
                return False, (f"G13 FAIL: {fam} n={n}: a wheel residue k = "
                               f"{unit}*{x} is not a multiple of {forced}, "
                               f"which forced divisibility requires at this "
                               f"filter")
    return True, (f"G13 ok: the wheel constants (W1, W2a, W2b, W1^-1 and the "
                  f"two CRT lifts) are exact at {len(cases)} configurations: "
                  f"k-space (23,37,47] at n = 15, 16 and the production unit "
                  f"wheel (..31],(31,41],(41,53] at every family's opening "
                  f"unit for its opening filter and the three after it; "
                  f"3000 sampled CRT residues per configuration recombine to "
                  f"all three levels, survive every wheel prime IN K SPACE "
                  f"(k = unit*x) and are multiples of every forced prime; "
                  f"W1, W2 under 2^32 and W1*W2 under 2^63")


def g14_engine_mechanisms():
    """The generation tables, the derived compaction depths, the CRT-combined
    group tables, and the queue-overflow fallback -- each against its own
    definition, at the production configurations G9 cannot reach."""
    rng = np.random.default_rng(20260904)
    cases = (("A088250", 15, 23, 37, None, 65536, 1),
             ("A088250", 16, 23, 37, 47, 65536, 1),
             ("A125838", 15, 23, 37, 47, 65536, 1),
             ("A088250", 15, 23, 31, None, 4096, 1),
             # the unit wheels the campaigns run
             ("A088250", 15, 31, 41, 53, 65536, 30030),
             ("A088250", 17, 31, 41, 53, 65536, 30030),
             ("A125838", 15, 31, 41, 53, 65536, 30030),
             ("A164325", 16, 31, 41, 53, 65536, 30030),
             ("A088651", 16, 31, 41, 53, 65536, 510510))
    for fam, n, p1, p2, p3, q2, unit in cases:
        W1, r1 = wheel(n, fam, p1, unit=unit)
        W2a, r2 = wheel(n, fam, p2, lo=p1, unit=unit)
        if p3:
            W2b, r3 = wheel(n, fam, p3, lo=p2, unit=unit)
            EA = W2b * pow(W2b % W2a, -1, W2a)
            EB = W2a * pow(W2a % W2b, -1, W2b)
        else:
            W2b, r3, EA, EB = 1, np.zeros(1, dtype=np.int64), 1, 0
        W2 = W2a * W2b
        inv = pow(W1 % W2, -1, W2)
        w2u, r1u = np.uint64(W2), r1.astype(np.uint64)
        a = (r1u % w2u) * np.uint64(inv) % w2u
        A = ((w2u - a) % w2u).astype(np.int64)
        ka = np.uint64(EA * inv % W2)
        kb = np.uint64(EB * inv % W2)
        C = ((r2.astype(np.uint64) % np.uint64(W2a)) * ka % w2u
             ).astype(np.int64)
        D = ((r3.astype(np.uint64) % np.uint64(W2b)) * kb % w2u
             ).astype(np.int64)
        for t, sx, u in zip(rng.integers(0, r1.size, 2000).tolist(),
                            rng.integers(0, r2.size, 2000).tolist(),
                            rng.integers(0, r3.size, 2000).tolist()):
            m_split = (int(A[t]) + int(C[sx]) + int(D[u])) % W2
            if max(int(A[t]), int(C[sx]), int(D[u])) >= W2:
                return False, (f"G14 FAIL: {fam} n={n}: a split table entry "
                               f"is not reduced mod W2")
            r2u = (EA * int(r2[sx]) + EB * int(r3[u])) % W2
            m_ref = ((r2u - int(r1[t])) * inv) % W2
            if m_split != m_ref:
                return False, (f"G14 FAIL: {fam} n={n} ({p1},{p2},{p3}]: "
                               f"A[{t}]+C[{sx}]+D[{u}] gives m={m_split}, "
                               f"CRT says {m_ref}")
            x = int(r1[t]) + W1 * m_split
            if x % W1 != int(r1[t]) or x % W2a != int(r2[sx]):
                return False, (f"G14 FAIL: {fam} n={n}: reconstructed x does "
                               f"not recombine to its own residues")
            if p3 and x % W2b != int(r3[u]):
                return False, (f"G14 FAIL: {fam} n={n}: the THIRD level's "
                               f"residue is not the one reconstructed")

        eng = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit)
        primes = eng.primes
        if any(unit % q == 0 for q in primes):
            return False, (f"G14 FAIL: {fam} n={n} unit {unit}: a prime of "
                           f"the unit is in the sieve")
        for name, depth, target in (("LIT", eng.lit, eng.lit_target),
                                    ("K2", eng.k2, eng.k2_target)):
            if depth > len(primes):
                return False, f"G14 FAIL: {fam} n={n}: {name} past the sieve"
            if eng.surv[depth] > target and depth < len(primes):
                return False, (f"G14 FAIL: {fam} n={n}: {name}={depth} leaves "
                               f"{eng.surv[depth]:.4f} alive, over the "
                               f"{target} target")
            if depth > 0 and eng.surv[depth - 1] <= target and \
                    depth > eng.lit:
                return False, (f"G14 FAIL: {fam} n={n}: {name}={depth} is "
                               f"deeper than it needs to be")

        for tag, groups, table_src, budget, lo, hi in (
                ("prefix", eng.groups,
                 lit_prefix(n, fam, primes, eng.groups, unit=unit),
                 LIT_GROUP_MAX, 0, eng.lit),
                ("round 2", eng.groups2,
                 lit_prefix(n, fam, primes, eng.groups2, table="g2bits",
                            unit=unit),
                 K2_GROUP_MAX, eng.lit, eng.k2)):
            src, table, _descs = table_src
            if [i for g in groups for i in g] != list(range(lo, hi)):
                return False, (f"G14 FAIL: {fam} n={n}: the {tag} grouping "
                               f"{groups} does not cover primes [{lo}, {hi}) "
                               f"exactly once, in order")
            off_bits = 0
            for g in groups:
                qs = [primes[i] for i in g]
                Q = 1
                for q in qs:
                    Q *= q
                if Q > budget:
                    return False, (f"G14 FAIL: {fam} n={n}: {tag} group {qs} "
                                   f"has modulus {Q} over the {budget} budget")
                if f"* {Q}u;" not in src or \
                        f"__umul64hi(off, {(1 << 64) // Q}ULL)" not in src:
                    return False, (f"G14 FAIL: {fam} n={n}: modulus {Q} or "
                                   f"its magic is not baked into the {tag} "
                                   f"source")
                want = np.zeros(Q, dtype=bool)
                for q in qs:
                    bad = np.array(killed_residues(q, n, fam, unit),
                                   dtype=np.int64)
                    want |= np.isin(np.arange(Q) % q, bad)
                if Q < LIT_INLINE_Q:
                    mask = 0
                    for u in killed_residues(qs[0], n, fam, unit):
                        mask |= 1 << u
                    got = np.array([(mask >> u) & 1 for u in range(Q)], bool)
                else:
                    b = off_bits + np.arange(2 * Q)
                    got2 = ((table[b >> 5] >> (b & 31)) & 1).astype(bool)
                    if not np.array_equal(got2[:Q], got2[Q:]):
                        return False, (f"G14 FAIL: {fam} n={n}: the {tag} "
                                       f"table for {qs} is not periodic with "
                                       f"period {Q} -- the doubled copy "
                                       f"differs")
                    got = got2[:Q]
                    off_bits += ((2 * Q + 31) // 32) * 32
                if not np.array_equal(got, want):
                    return False, (f"G14 FAIL: {fam} n={n}: the {tag} table "
                                   f"for {qs} (modulus {Q}) disagrees with "
                                   f"killed_residues at "
                                   f"{int(np.flatnonzero(got != want)[0])}")

    # The queues are sized from the survival rate rather than the worst
    # case, so overflow is POSSIBLE -- and the whole design rests on it
    # being harmless.  FORCED: an engine whose queues hold 32 entries
    # against a block that owns thousands takes the fallback for nearly
    # every candidate, and its stream must be identical.
    ref = GpuEngine(15, "A088250", p1=13, p2=23, p3=None, q2=128)
    tiny = GpuEngine(15, "A088250", p1=13, p2=23, p3=None, q2=128,
                     qcap_sigma=-1e9)
    if tiny.q1cap > 32 or (tiny.k2 > tiny.lit and tiny.q2cap > 32):
        return False, (f"G14 FAIL: the forced-overflow engine still has "
                       f"room ({tiny.q1cap}, {tiny.q2cap}) -- the drill "
                       f"would not exercise the fallback")
    lo, span = 10 ** 12, 2 * 10 ** 10
    a, b = ref.survivors_k(lo, lo + span), tiny.survivors_k(lo, lo + span)
    if not a:
        return False, "G14 FAIL: the overflow drill window is empty"
    if a != b:
        return False, (f"G14 FAIL: the queue-overflow fallback changed the "
                       f"stream: {len(a)} survivors properly sized, "
                       f"{len(b)} with the queues forced full")

    prod = GpuEngine(15, "A088250", p1=31, p2=41, p3=53, unit=30030)
    if not 0 < prod.q1cap <= prod.tile or not 0 < prod.q2cap <= prod.tile:
        return False, (f"G14 FAIL: production queue capacities "
                       f"({prod.q1cap}, {prod.q2cap}) are not within "
                       f"(0, tile = {prod.tile}]")
    return True, (f"G14 ok: the split A/C/D generation tables reproduce the "
                  f"one-table CRT on 18000 sampled triples at nine "
                  f"configurations including k-space (23,37,47] and the "
                  f"production unit wheels (..31],(31,41],(41,53] at unit "
                  f"30030 (A088250 n = 15, 17; A125838 n = 15; A164325 "
                  f"n = 16) and 510510 (A088651 n = 16); the compaction "
                  f"depths derive from the survival curve (A088250 n = 15: "
                  f"LIT={prod.lit}, K2={prod.k2}); the CRT-combined prefix "
                  f"and round-2 groups cover their prime ranges exactly once "
                  f"in order, stay inside their budgets, and every group's "
                  f"table agrees with killed_residues on EVERY residue of "
                  f"its modulus; production queues hold {prod.q1cap} and "
                  f"{prod.q2cap} of a {prod.tile}-candidate block; and with "
                  f"the queues forced to 32 the survivor stream is IDENTICAL "
                  f"({len(a)} survivors)")


def g15_k_off_representation():
    """The (k, off) split: the base is folded, not carried, and folding is
    exact.

      1. BASE-SHIFT INVARIANCE: the same absolute window sieved with the
         launch batching forced to different sizes must return the
         identical stream.
      2. The doubled bitmap is periodic with period q, per prime.
      3. The folded values are the residues they claim to be, for primes
         and CRT groups, at bases up to 1e30 -- including above 2^64.
    """
    eng = GpuEngine(15, "A125838", p1=13, p2=23, p3=None, q2=512)
    j0 = eng.j_of(10 ** 12)
    eng.per_launch = 1
    one = eng.survivors_j(j0, j0 + 600)
    eng.per_launch = 6
    many = eng.survivors_j(j0, j0 + 600)
    if not one:
        return False, "G15 FAIL: the base-shift window is empty -- vacuous"
    if one != many:
        return False, (f"G15 FAIL: the stream depends on the launch base: "
                       f"{len(one)} survivors in 600 launches vs {len(many)} "
                       f"in 100 -- the fold is not base-invariant")
    # and in UNIT space, where the base the device folds is in k' and the
    # survivors come back multiplied: same invariance, and every survivor
    # a multiple of the unit that the k-space engine also keeps
    engu = GpuEngine(15, "A125838", p1=19, p2=23, p3=None, q2=512, unit=30030)
    ju = engu.j_of(10 ** 12)
    engu.per_launch = 1
    oneu = engu.survivors_j(ju, ju + 600)
    engu.per_launch = 6
    manyu = engu.survivors_j(ju, ju + 600)
    if not oneu:
        return False, "G15 FAIL: the unit base-shift window is empty -- vacuous"
    if oneu != manyu:
        return False, (f"G15 FAIL: with unit 30030 the stream depends on the "
                       f"launch base: {len(oneu)} vs {len(manyu)}")
    if any(k % 30030 for k in oneu):
        return False, "G15 FAIL: a unit-space survivor is not a multiple of the unit"
    presu = engu.cp.asnumpy(engu.d_pres).reshape(len(engu.primes), engu.nres)
    for i in np.random.default_rng(5).integers(0, len(engu.primes), 20).tolist():
        q = engu.primes[i]
        kr = killed_residues(q, 15, "A125838", 30030)
        if sorted(presu[i][:len(kr)].tolist()) != kr:
            return False, (f"G15 FAIL: with unit 30030, prime {q}'s residue "
                           f"list is not the unit-space killed set")

    pres = eng.cp.asnumpy(eng.d_pres).reshape(len(eng.primes), eng.nres)
    pmask = eng.cp.asnumpy(eng.d_pmask).reshape(len(eng.primes),
                                                 eng.mask_words)
    rng = np.random.default_rng(4)
    for i in rng.integers(0, len(eng.primes), 40).tolist():
        q = eng.primes[i]
        kr = killed_residues(q, 15, "A125838")
        row = pres[i]
        if sorted(row[:len(kr)].tolist()) != kr or \
                not (row[len(kr):] == 0xFFFFFFFF).all():
            return False, (f"G15 FAIL: prime {q}'s residue list disagrees "
                           f"with killed_residues")
        got = set()
        for wi in range(eng.mask_words):
            wv = int(pmask[i, wi])
            for bit in range(32):
                if (wv >> bit) & 1:
                    got.add(32 * wi + bit)
        want = {u % MASK_BITS for u in kr}
        if got != want:
            return False, (f"G15 FAIL: prime {q}'s mask is not the set of "
                           f"its killed residues mod {MASK_BITS}")
        if q <= MASK_BITS and len(got) != len(kr):
            return False, (f"G15 FAIL: prime {q} <= MASK_BITS but its mask "
                           f"is not exact")

    for base in (0, eng.W, 10 ** 12, 2 ** 64 + 12345,
                 k_ceil(15, "A125838") - eng.W, 10 ** 30):
        base -= base % eng.W
        gps = eng._launch_base(base)
        got = eng._pk[:, 3].astype(np.int64)
        want = np.array([base % q for q in eng.primes], dtype=np.int64)
        if not np.array_equal(got, want):
            i = int(np.flatnonzero(got != want)[0])
            return False, (f"G15 FAIL: at base {base:.4g} the fold for prime "
                           f"{eng.primes[i]} is {got[i]}, not "
                           f"{want[i]} = base mod q")
        descs = list(eng.gdesc) + list(eng.gdesc2)
        gtab = (eng.cp.asnumpy(eng.d_gbits), eng.cp.asnumpy(eng.d_g2bits))
        for gi, ((kind, Q, payload), gp) in enumerate(zip(descs, gps)):
            tab = gtab[0 if gi < len(eng.gdesc) else 1]
            if kind == "modq":
                if int(gp) != base % Q:
                    return False, (f"G15 FAIL: hoisted group {gi} (modulus "
                                   f"{Q}) at base {base:.4g}: scalar "
                                   f"{int(gp)} is not base mod Q")
                continue
            for r in range(Q):
                if kind == "inline":
                    hit = bool((int(gp) >> r) & 1)
                else:
                    b = int(gp) + r
                    hit = bool((tab[b >> 5] >> (b & 31)) & 1)
                if hit != bool((int(payload) >> ((r + base) % Q)) & 1
                               if kind == "inline"
                               else _tab_bit(tab, payload, (r + base) % Q)):
                    return False, (f"G15 FAIL: group {gi} (modulus {Q}) at "
                                   f"base {base:.4g}, r={r}: the folded "
                                   f"scalar does not answer for "
                                   f"(off + base) mod Q")
    return True, (f"G15 ok: the survivor stream is INVARIANT under the launch "
                  f"base ({len(one)} survivors, 600 launches vs 100; and "
                  f"{len(oneu)} in unit space, every one a multiple of 30030, "
                  f"with the residue lists the unit-space killed sets); the "
                  f"tail's residue lists and {MASK_BITS}-bit masks are "
                  f"exactly killed_residues (mod MASK_BITS) on 40 sampled "
                  f"primes, exact below MASK_BITS; and every per-prime and "
                  f"per-group fold is exactly (base mod modulus) at six "
                  f"bases up to 1e30 -- so nothing on the device is bounded "
                  f"by k")


def _tab_bit(tab, off_bits, u):
    b = int(off_bits) + int(u)
    return bool((tab[b >> 5] >> (b & 31)) & 1)


def g16_third_level_mechanisms():
    """The three things the third level adds that nothing else can see fail.

      1. THE GLOBAL TAIL QUEUE OVERFLOWS HARMLESSLY -- forced by setting the
         capacity to zero, which sends EVERY candidate down the fallback.
      2. THE THIRD LEVEL CHUNKS WITHOUT MOVING THE STREAM: nu forced to 1,
         2 and 3 against the unchunked engine.
      3. THE QUEUES INDEX CANDIDATES by shifts, so tpb and spb must be
         powers of two: a non-power raises rather than mis-decoding.
    """
    n, fam, p1, p2, p3, q2 = 15, "A088250", 13, 17, 19, 128
    lo, span = 9 * 10 ** 14, 4 * 10 ** 10
    ref = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2)
    want = ref.survivors_k(lo, lo + span)
    if not want:
        return False, "G16 FAIL: the drill window is empty -- vacuous"

    flood = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2)
    flood.q3cap = 0
    if flood.survivors_k(lo, lo + span) != want:
        return False, ("G16 FAIL: with the global tail queue forced to zero "
                       "the survivor stream changed -- the overflow "
                       "fallback is not the same arithmetic")

    for nu in (1, 2, 3):
        e = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, nu=nu)
        if e.nu != min(nu, e.R3):
            return False, f"G16 FAIL: nu={nu} was not honoured ({e.nu})"
        if e.survivors_k(lo, lo + span) != want:
            return False, (f"G16 FAIL: chunking the third level at nu={nu} "
                           f"changed the stream")

    for bad in (dict(tpb=192), dict(spb=6, cpt=24)):
        try:
            GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, **bad)
        except ValueError:
            pass
        else:
            if bad.get("tpb"):
                return False, (f"G16 FAIL: tpb={bad['tpb']} is not a power "
                               f"of two and was accepted")
    return True, (f"G16 ok: the global tail queue's overflow fallback leaves "
                  f"the stream IDENTICAL with the capacity forced to zero "
                  f"({len(want)} survivors); chunking the third level at "
                  f"nu = 1, 2, 3 against R3 = {ref.R3} does not move it; and "
                  f"a non-power-of-two tpb raises rather than mis-decoding "
                  f"the queue index")


def g17_unit_wheel_matches_k_wheel():
    """The production unit wheel == a k-space wheel, on the line.

    G9 proves the unit machinery on wheels a dense CPU sieve can follow;
    this pins the wheel the campaigns actually run -- (..31],(31,41],(41,53]
    at unit 30030, a period of 3.26e19 -- against the k-space wheel
    (23],(37],(47] (period 6.15e17) over one k-space period at A088250's
    opening filter n = 15, at a height inside the first unit period, where
    the campaign opens.  Two wheels enumerating the same candidates by
    different arithmetic must return the identical survivor stream, and
    every survivor must also pass the CPU engine's one-at-a-time k-space
    test at the campaign's sieve depth.  Coverage is what a fingerprint
    cannot see, so this is the gate the production wheel's claim stands on.
    """
    n, fam = 15, "A088250"
    kw = GpuEngine(n, fam, p1=23, p2=37, p3=47, q2=Q2_DEFAULT)
    uw = GpuEngine(n, fam, p1=31, p2=41, p3=53, q2=Q2_DEFAULT, unit=30030)
    jk = 18                              # 1.1e19 of k: A088250's frontier sits in period 18
    lo, hi = jk * kw.W, (jk + 1) * kw.W
    a = kw.survivors_j(jk, jk + 1)
    b = uw.survivors_k(lo, hi)
    if not a:
        return False, "G17 FAIL: the k-space period is empty -- vacuous"
    if a != b:
        sa, sb = set(a), set(b)
        return False, (f"G17 FAIL: over [{lo:.4g}, {hi:.4g}) the k-space "
                       f"wheel keeps {len(a)} survivors and the unit wheel "
                       f"{len(b)}: diff {sorted(sa ^ sb)[:4]}")
    cpu = CpuEngine(n, fam, q2=Q2_DEFAULT)
    if not all(cpu.survives(k) for k in b):
        return False, "G17 FAIL: a survivor fails the CPU engine's k-space test"
    if any(k % 30030 for k in b):
        return False, "G17 FAIL: a survivor is not a multiple of 30030"
    return True, (f"G17 ok: the unit wheel (..31],(31,41],(41,53] at unit "
                  f"30030 returns the IDENTICAL {len(a)} survivors as the "
                  f"k-space wheel (23],(37],(47] over k-space period {jk} "
                  f"[{lo:.4g}, {hi:.4g}) at n = 15, every one a multiple of "
                  f"30030 that the CPU engine's k-space test also keeps -- "
                  f"the unit wheel's density is "
                  f"{kw.density() / uw.density():.3f}x thinner for the same "
                  f"line")


GATES = [g7_wheel_matches_oracle, g8_wheel_partitions_the_period,
         g13_production_wheel_constants, g14_engine_mechanisms,
         g9_gpu_matches_cpu, g15_k_off_representation,
         g16_third_level_mechanisms, g17_unit_wheel_matches_k_wheel]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
