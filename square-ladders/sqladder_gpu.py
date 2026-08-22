"""sqladder_gpu.py -- the GPU engine for A089761.

The same mathematics a third time, in CuPy, and shaped so that nothing it
shares with the CPU engine could hide a bug in either.

WHAT THE KERNEL DOES.  The CPU engine materialises the dense k line and
marks arithmetic progressions into it.  This engine never forms the line
at all.  It carries a wheel index and reconstitutes

    k = W*j + x,        x congruent to a residue that no wheel prime kills

Each candidate is then TESTED, not marked: for each prime q above the
wheel the kernel reduces k mod q by Barrett magic-multiply and reads one
bit out of a packed table of the forbidden residues, BAILING OUT at the
first kill.  That early exit is the whole performance argument.  w(q,n) is
16 out of every q for q >= 37 (sqladder_reference), so the first prime
tested kills a large fraction and the expected number of tests per
candidate is three, against the ~22 marks per candidate a marking sieve of
the same depth would pay.

THE WHEEL IS FACTORED (v2, worth 3.9x).  A wheel is a table of the
surviving residues mod W, and that table grows as fast as W does: primes
to 23 give 1,088,640 residues mod 223,092,870 (4.4 MB, comfortably
cache-resident), while primes to 31 would give 261 million residues mod
2.0e11 -- 2 GB, read from DRAM, and the wheel would cost more than it
saves.  So the wheel is stored as TWO tables and combined per candidate by
CRT:

    x = RES1[t] + W1 * ( (RES2[s] - RES1[t]) * W1^-1  mod W2 )

with W1 the primes up to P1 and W2 the primes in (P1, P2].  The residues
mod W1*W2 are enumerated exactly, none stored: 5,040 entries beside the
1,088,640 give the wheel of primes up to 37, which is 6.6x fewer
candidates per unit of k line than primes to 23, out of two tables that
still fit in cache.

THE TEST LOOP IS ISSUE-BOUND, AND THE WARP PAYS THE MAX (v3, worth 6.5x).
Adding 24 independent instructions to the loop body costs 42% of the wall
clock, so the kernel is bound by instruction ISSUE -- which makes both
"fewer instructions per test" and "fewer tests per warp" real levers, and
they multiply.  v3 takes both:

  * The reduction is 32-bit where it can be.  k - qhat*q lies in [0, 2q)
    < 2^17, and arithmetic mod 2^32 is exact for a value that small, so
    the 64-bit multiply, subtract and conditional subtractions all become
    32-bit.  ONE conditional subtraction suffices, and that is a theorem
    rather than a hope: with M = floor(2^64/q) and x < 2^63,

        x*M/2^64 = x/q - x*s/(q*2^64)   where s = 2^64 mod q < q,

    so the error term is under 1/2, qhat > x/q - 3/2, and qhat is
    therefore floor(x/q) or one less.  In v3.4 x was the absolute k, and
    that is precisely what capped the campaign at 9e18; in v4 x is the
    OFFSET (below), bounded by W * per_launch, so the theorem holds at
    every height and REDUCE_MAX enforces it against the wheel instead of
    against the mathematics.  (huntlib's shared snippet keeps two
    subtractions because it does not get to assume a bound; this engine
    does, and states it.)

  * The per-prime constants are one uint4 (magic_lo, magic_hi, q, boff),
    so a test issues ONE 128-bit uniform load instead of three loads.

  * The first LIT primes are baked into the generated source as literals
    (OPTIMIZATION.md 2.5) and CRT-COMBINED in groups.  "Killed by 41 or by
    43" is a function of k mod (41*43) alone, so a group of primes costs
    one reduction and one bitmap lookup rather than one of each per prime,
    and the production prefix is six primes in THREE tests.  Group size is
    bounded by LIT_GROUP_MAX, and that bound is the whole subtlety: the
    combined table has to stay in L1, and the cliff is sharp -- 1.19x at
    1 KB, 1.18x at 33 KB, but 0.25x at 76 KB and 0.39x at 536 KB.  This is
    the same idea OPTIMIZATION.md 2.10 records as REJECTED in
    euler-prime-runs, and it pays here for a reason worth naming: that
    kernel was bound by load COUNT, this one by instruction ISSUE, so
    trading instructions for a load is the right way round.

  * The generation CRT is algebraic, not arithmetic.  m = ((r2 - r1)*INV)
    mod W2 = (r2*INV - r1*INV) mod W2, and each half is a function of one
    table index, so A[t] = (-r1*INV) mod W2 goes in the first-level table
    and C[s] = (r2*INV) mod W2 in the second, and generation becomes one
    add and one conditional subtract.  The r2 residues are then never
    needed on the device at all.

  * Divergence is compacted inside the CUDA block, TWICE.  A lane needs
    3.07 tests but a warp of 32 runs to the deepest of them, 16.06 -- a
    5.23x tax.  So each thread takes JPT candidates, runs the branchless
    prefix on all of them, and pushes the survivors to a SHARED-memory
    queue; after one __syncthreads the whole block chews that queue with
    every lane alive, and then does it again at K2.  A JPT=16, TPB=128
    block compacts 2,048 candidates to ~194 and then to ~24, which are
    full warps where an uncompacted warp would have carried one lane.
    None of it leaves the kernel: the launcher never learns it exists.

    The queues are sized from the ANALYTIC survival plus QCAP_SIGMA sigma
    rather than from the worst case, because a queue big enough for "every
    candidate survives" costs shared memory and shared memory costs blocks
    per SM -- sizing both for that case measured 0.83x.  So overflow is
    possible, and it is made HARMLESS instead of impossible: a candidate
    that does not fit runs its tail on the spot, uncompacted, which is the
    same arithmetic and so the same answer.  Capacity is a tuning constant,
    not a correctness bound, and G14 proves it by forcing the path.

    The survivors leave in queue order rather than in candidate order.
    `survivors_j` sorts, and the frozen work fingerprint is a count plus
    an xor, so neither depends on the order.

  * The two compaction depths are DERIVED, not hardcoded.  They were swept
    as counts on the production shape -- 6 primes before the first, 16
    before the second -- but a count is the wrong thing to carry to another
    configuration: what the sweep found is a SURVIVAL FRACTION, and a
    coarser wheel kills candidates faster, so a fixed depth there tests
    past the point where anything is left to kill.  LIT_SURV and K2_SURV
    are the fractions; the depths follow per configuration, and on the
    production shape they reproduce 6 and 16 exactly.

WHY THIS IS NOT dickson-ladders' ENGINE.  A247965 forces its k to be a
multiple of the wheel modulus -- one candidate residue per period, R = 1 --
so its engine can walk j alone and needs no residue table at all.  Here
half the nonzero residues survive each small prime, R is millions, and the
two problems need different machinery however similar they read.  The
proof of the difference is in sqladder_reference's docstring.

THE (k, off) REPRESENTATION, AND WHY THE CEILING MOVED (v4).  v3.4 carried
the absolute k in a u64 and reduced IT, so the one-subtraction theorem
above put a hard cap at 9e18 -- a machine word masquerading as a limit of
the problem.  The a(16)/a(17) campaign ran into it with a(18) still open,
and at that point the modelled Q3 for a(18) was already past 2^64, so no
choice of word size would have been enough (OPTIMIZATION.md 2.7: do not
grow a second engine at the machine-word boundary).

So the device stopped seeing k at all.  A candidate is the pair
(base, off) with k = base + off: `base` is the launch's absolute floor, a
PYTHON INT of any size that never leaves the host, and `off` is the
position within the launch, under W * per_launch.  What the device needs
is k mod q, and

    k mod q = (off + base) mod q,

so the base contribution is folded ONCE PER LAUNCH into the two things
each test already reads, and never added per candidate:

  * per prime, the bitmap holds the killed pattern TWICE (2q bits) and the
    uint4's boff slot carries `2q-block base + base mod q`; since
    off mod q < q, the sum indexes the right copy with no reduction.
  * per CRT group, the base arrives as a kernel SCALAR -- rotated mask for
    an inline group, shifted table index for a table group (lit_prefix).

The hot loop therefore issues exactly what v3.4 issued, which is the point:
an issue-bound kernel cannot afford a representation that costs
instructions.  The price is paid in memory (50.6 MB of bitmap instead of
25.3 MB) and in ~6,500 vectorised host modulos per launch, both far off the
critical path.  G15 is the proof: the same window sieved with the launch
base moved returns the identical absolute stream.

CEILINGS, stated and enforced (CONVENTIONS.md "Numeric hygiene"):
  * k < k_ceil(n) = (MR_VALID_BELOW - 1) / n^2, the PRIMALITY-TEST
    VALIDITY BOUND and nothing else -- 1.02e22 at n = 18.  Every value
    k*i^2+1 below it is under huntlib's DETERMINISTIC Miller-Rabin bound
    (G10): this project proves its primes.  No machine word appears in it.
  * W * per_launch + q2 < 2^63 = REDUCE_MAX, which is what keeps the
    Barrett reduction within ONE conditional subtraction of exact (above).
    A bound on the WHEEL AND THE BATCHING, both of which the engine picks;
    per_launch is halved until it holds.
  * W1 < 2^32, so the first-level table is u32.
  * W2 < 2^32 and W1*W2 < 2^63.

Gates here: G7 (both wheel constructions == the oracle's brute-force period
walk), G8 (the wheel partitions the period: the count is the formula and no
kept residue is killed), G9 (GPU survivor stream == CPU survivor stream,
bit for bit, on populated windows at three heights and three filters,
one-level AND two-level, including above 2^64), G13 (the production
wheel constants), G14 (the v3 mechanisms: the A/C generation tables, the
derived compaction depths, the CRT-combined prefix and round-2 group
tables, and the queue-overflow fallback, forced and checked identical),
G15 (the v4 representation: base-shift invariance, the doubled bitmap and
the folded group scalars).
"""

import pathlib as _pathlib
import sys as _sys

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.gpu import barrett_magics                         # noqa: E402
from sqladder_reference import K_FLOOR, wheel_residues
from sqladder_search import (Q2_DEFAULT, CpuEngine, k_ceil,
                             killed_residues)

P1_DEFAULT = 23              # first-level wheel: the primes up to here
P2_DEFAULT = 37              # second-level wheel: the primes in (P1, P2]
# THIRD-level wheel: the primes in (P2, P3].  A prime put into the wheel
# removes S(q) = prod_{q' < q}(1 - w(q')/q') tests from every unit of k
# line, and at n = 18 the three primes 41, 43, 47 are 72% of all the tests
# the engine does -- they are the largest terms of that sum and they were
# out of reach only because their residues will not fit in one table.
# Three levels put them in two tables of 4,560 and 16,675.
#
# 47 IS THE LAST ONE, and not by choice: m is a u32 and W1*m is what the
# one-conditional-subtraction reduction bounds, so the combined second
# modulus must stay under 2^32.  Primes to 47 make it 2.76e9; adding 53
# makes it 1.46e11.  The engine raises rather than wrapping.
P3_DEFAULT = 47
TPB_DEFAULT = 256            # threads per block   (re-swept every version)
# Second-level residues per BLOCK.  k = base + r1 + W1*m with
# m = A[t] + C[s], so for a fixed t the quantity base + r1 does not
# depend on s at all: one res1x load, one `t` computation, one bounds
# check and one 64-bit add serve SPB candidates instead of one.
# Generation is issue-bound (OPTIMIZATION_LOG measurement E10), so
# that is exactly the currency it is paid in -- 1.126x.  Forced to 1
# on a one-level wheel, where there is no second level to spread over.
SPB_DEFAULT = 8
# CANDIDATES PER THREAD, from which JPT (first-level residues per thread)
# follows as CPT // SPB.  This is the invariant, and shipping JPT instead
# is the same mistake the compaction depths taught: with SPB forced to 1
# on a one-level wheel, a JPT of 4 leaves four candidates per thread where
# the production shape has 32, and that measured 0.843x of that shape's
# own optimum.  32 is the optimum on BOTH -- production reaches it as
# 4x8, a one-level wheel as 32x1.
CPT_DEFAULT = 32
# WHERE THE TWO COMPACTION POINTS GO.  They were swept as counts on the
# production shape -- 6 primes before the first compaction, 16 before
# the second -- but a count is the wrong thing to carry to another
# configuration, because what the sweep actually found is a SURVIVAL
# FRACTION.  A coarser wheel kills candidates faster (w(q,n) is
# min(n,(q-1)/2), so a smaller n or a smaller wheel means a steeper
# curve), and testing to a fixed DEPTH there is testing past the point
# where anything is left to kill.  Shipping the counts cost the two
# coarse-wheel benchmark shapes 22% each, which is exactly what a
# four-shape benchmark is for.
#
# So the constants are the fractions, and the depths are derived per
# configuration: the first compaction goes where about 9.5% of
# candidates are left, the second where about 1.2% are.  On the
# production shape that reproduces 6 and 16 exactly.
# Re-swept on the three-level wheel: the optimum is the first compaction
# at ~10% survival on BOTH wheels, and 0.11 is the target that lands there
# on each (two-level: 5 primes, 0.092; three-level: 7 primes, 0.103).  The
# neighbours are 0.94x and 0.29x -- see the L1 note on LIT_GROUP_MAX for
# why going SHALLOWER is the catastrophic direction.
LIT_SURV = 0.11              # first compaction point: survival target
# Re-swept once the tail moved into its own kernel, and it moved a long
# way: 0.012 (19 primes) is 0.98x of 0.0057 (25 primes).  The direction is
# the interesting part -- a CHEAPER tail wants MORE compaction before it,
# not less, because what the second round now saves is not divergent block
# work but entries written to and read back from a global queue.
K2_SURV = 0.0057             # second compaction point: survival target
UNROLL = 4                   # independent Barrett chains in the queue tail
HIT_CAP = 1 << 16            # survivors buffered per launch
RES_MAX = 1 << 24            # refuse a one-level wheel table bigger than this
LIT_INLINE_Q = 64            # below this, a group's kill set is a u64 literal
# Largest modulus a CRT-combined prefix group may reach, and the total
# table budget that goes with it.  This is the knob that keeps the
# combined tables in L1, and the cliff is sharp -- but it is NOT where the
# v3 sweep put it, and re-reading that sweep is what unlocked 1.11x here.
# It measured "1.19x at 1 KB, 1.18x at 33 KB" and concluded the win was
# flat, so it shipped 1 KB.  What it had actually measured is that a
# budget of 8192 and a budget of 262144 produce THE SAME GROUPING at that
# geometry -- pairs either way, because a third prime needs a modulus of
# 82861 -- so the two points were the same binary.  On the wheels this
# engine runs now the budget really does change the grouping (three primes
# per group instead of two, one fewer test on EVERY candidate) and it is
# worth 1.11x on the two-level wheel and 1.08x on the three-level one.
#
# The cliff is real and it is an L1 CARVEOUT budget, not a table budget:
# an SM has 128 KB shared with L1, the resident blocks' queues take their
# cut of it FIRST, and whatever is left has to hold the group tables.
# Measured at n = 18 on the three-level wheel: 69 KB of tables against
# 9.5 KB of queues per block is the optimum; 147 KB of tables is 0.34x,
# and 61 KB of tables against 14.6 KB of queues is 0.29x -- the same
# cliff reached from the other side, which is why the byte budget below
# is a guard on the SUM and not on either half.
LIT_GROUP_MAX = 1 << 18
GROUP_BYTES_MAX = 96 << 10
# Copies of each HOISTED group's pattern.  v4 stores every table twice so a
# launch can reach `(off + base) mod Q` with a bare add; the hoisted prefix
# does not need that, because it folds the base into its per-residue value
# once per first-level residue instead (see lit_prefix).  One copy halves
# the prefix tables, 50 KB to 25 KB, and L1 is the resource this kernel is
# actually short of.  Left as a constant because it is exactly the knob the
# L1 cliff is measured against: 2 is v4's behaviour and still works here.
HOIST_TABLE_REPS = 1
# The same budget for round 2's groups.  They sit on a much smaller
# population -- the queue, not every candidate -- so they can afford a
# bigger table before the L1 cliff bites.  Re-swept on the three-level
# wheel, where the round-2 range is longer (it starts at 83 now, not 61):
# 8192 is 0.96x, 32768 is 1.03x, 65536 is 1.04x.
K2_GROUP_MAX = 1 << 16

# How much margin the shared queues carry over their ANALYTIC occupancy.
# Survival through a prefix is an exact product over the primes involved
# (OPTIMIZATION.md 2.6), so the mean is known and the count is a sum of
# near-independent Bernoullis; six standard deviations of headroom makes
# the overflow path essentially never taken.  It does not have to be
# "never", though, and that is the point of the design: overflow is
# HARMLESS, not impossible -- a candidate that does not fit runs its tail
# on the spot, uncompacted, which is the same arithmetic and so the same
# answer.  The capacity is therefore a tuning constant and not a
# correctness bound, and G14 proves it by forcing the path.
QCAP_SIGMA = 6.0

# How much candidate work a single launch should carry.  It sets how many
# wheel blocks go in gridDim.z, and it exists because the two ends of the
# range are 7 orders of magnitude apart: one production wheel block is
# 5.5e9 candidates and wants a launch to itself, while a gate shape whose
# wheel is 30,030 wide has 1,008 candidates per block and would otherwise
# pay 200,000 launches for one benchmark.  Measured flat to within 2.6%
# across the range (OPTIMIZATION_LOG, measurement 6).
CAND_PER_LAUNCH = 1 << 30

# Ceiling on the GLOBAL tail queue, in candidates.  One launch's round-2
# survivors are about 1.2% of its candidates, which at production is 5.8e7
# and 465 MB; this caps the allocation and the overflow path takes any
# excess, so it costs correctness nothing.
Q3_MAX = 1 << 26
TAIL_BLOCKS_PER_SM = 64

# The one-conditional-subtraction reduction is exact only below 2^63.  In
# v3.4 that was a bound on k, and it is what capped the campaign at 9e18.
# In v4 the reduced quantity is the OFFSET within a launch, so the bound
# is on W * per_launch -- a property of the WHEEL AND THE BATCHING, which
# the engine chooses, and not of k, which the mathematics chooses.  Checked
# per engine in __init__ (a module constant cannot see W).
REDUCE_MAX = 1 << 63

_MODCACHE = {}


def wheel(n, p1, lo=1):
    """(W, RES): residues mod W = prod(lo < q <= p1) that no such q kills.

    Built by CRT lifting -- one prime at a time, each existing residue
    lifted to the q classes above it and the killed ones dropped.  The
    oracle builds the same set by walking the whole period; G7 pins them
    together.  Lifting is what makes a million-entry table cheap: the work
    is sum(R_i * q_i), not W.

    Refuses rather than thrashes.  The table has prod(q - w(q,n)) entries,
    which grows fast enough that one careless argument is an out-of-memory
    death rather than a slow gate: primes to 37 in ONE level would be 5.5e9
    residues, about 44 GB.  That is the whole reason the engine factors the
    wheel into two levels, so asking for it in one is a mistake worth
    naming (it cost a gate battery two silent kills before this check
    existed).
    """
    W, count = 1, 1
    for q in primerange(lo + 1, p1 + 1):
        count *= q - len(killed_residues(q, n))
    if count > RES_MAX:
        raise ValueError(
            f"a one-level wheel over ({lo}, {p1}] at n={n} would hold "
            f"{count:,} residues (> RES_MAX = {RES_MAX:,}); factor it into "
            f"two levels instead -- that is what P2 is for")
    res = np.zeros(1, dtype=np.int64)
    for q in primerange(lo + 1, p1 + 1):
        bad = np.array(killed_residues(q, n), dtype=np.int64)
        cand = (res[None, :] + W * np.arange(q, dtype=np.int64)[:, None])
        cand = cand.ravel()
        res = np.sort(cand[~np.isin(cand % q, bad)])
        W *= q
    return W, res


def lit_groups(primes, nlit, budget=LIT_GROUP_MAX, start=0):
    """Group primes[start:nlit] into CRT-combined test groups.

    "Killed by 41 or by 43" is a function of k mod (41*43) alone, so a
    group of primes costs ONE reduction and ONE bitmap lookup instead of
    one of each per prime.  Groups are grown greedily while the product
    stays under `budget`, and the budget is what keeps the combined tables
    L1-resident: measured, the win is 1.19x at 1 KB and 1.18x at 33 KB, but
    it INVERTS to 0.39x at 536 KB and 0.25x at 76 KB.  See the header.
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


def lit_prefix(n, primes, groups, table="gbits", indent=12, pname="gp",
               hoist=None):
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
    borrow decides which), one subtract and one conditional add -- three
    32-bit instructions where v4 issued a 64-bit multiply-high and its
    correction.  The measurement that forced this: 71% of the prefix was
    the arithmetic and only 29% the table lookups.

    Round 2 does NOT get this form and cannot: it reads offsets back out of
    a shared queue, where the decomposition has been thrown away.

    Every modulus and magic number is a compile-time literal
    (OPTIMIZATION.md 2.5), so a group test loads nothing but its own bit.
    A group whose modulus is under LIT_INLINE_Q needs no table at all --
    the entire forbidden set is a 64-bit immediate.

    The table for a group is the OR of its primes' forbidden sets lifted to
    the product modulus, which is exactly "killed by at least one of them",
    so the survivor set is identical to testing them one at a time; G14
    checks that against killed_residues directly.

    v4: the reduced quantity is `off`, not the absolute k, so what a group
    has to look up is `(off + base) mod Q` rather than `off mod Q`.  The
    base contribution is NOT added per candidate -- it is folded into the
    thing the test already reads, once per launch, on the host:

      * a table group stores its pattern TWICE (2Q bits), so the launch
        passes `2Q-block base + (base mod Q)` and `b = param + r` lands in
        the right copy with no reduction.  The tables are 1-2 KB, so the
        doubling is nowhere near the L1 cliff LIT_GROUP_MAX guards.
      * an inline group's kill set is a u64 immediate, and rotating a
        64-bit mask is free ON THE HOST, so the launch passes the ROTATED
        mask and the test is unchanged.

    Either way the group's base arrives as a kernel SCALAR PARAMETER -- the
    constant bank, not a load -- so the prefix issues exactly the
    instructions v3.4 issued.  `descs` tells the engine what to compute per
    launch: (kind, Q, payload).
    """
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
            # The launch base folds in HERE, once per first-level residue,
            # which is why a hoisted group's table does not have to be
            # stored twice the way v4's per-prime bitmap is.  Halving them
            # is what buys the L1 room for wider groups.
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
            for u in killed_residues(qs[0], n):
                mask |= 1 << u
            lines.append(head + f"kill |= (unsigned int)(({pname}{gi} >> r) "
                                f"& 1ULL); }}")
            descs.append(("inline", Q, mask))
            continue
        # ONE copy of the pattern when the base is folded per residue
        # (hoisted groups), TWO when the test has to reach it with a bare
        # add (round 2, which gets no decomposition to fold into).
        single = hoist is not None and HOIST_TABLE_REPS == 1
        reps = (0,) if single else (0, Q)
        tab = np.zeros((len(reps) * Q + 31) // 32, dtype=np.uint32)
        idx = np.arange(Q)
        for q in qs:
            bad = np.array(killed_residues(q, n), dtype=np.int64)
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

    `base` is the absolute k at offset 0 of the launch -- an arbitrary
    Python int, which is the whole point: it never reaches the device.
    """
    out = []
    for kind, Q, payload in descs:
        gb = int(base) % Q
        if kind == "inline":
            m = ((payload >> gb) | (payload << (Q - gb))) & ((1 << Q) - 1)
            out.append(np.uint64(m))
        elif kind == "modq":
            # a hoisted group folds the base into its per-residue value, so
            # what it wants is the residue itself and its table is one copy
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
#define Q1CAP %(q1cap)d
#define Q2CAP %(q2cap)d
#define LOGTPB %(logtpb)d
#define LOGSPB %(logspb)d
#define QTYPE %(qtype)s

/* WHAT THE QUEUES HOLD.  Not the candidate -- its INDEX in the block, which
   is (jj, ss, threadIdx.x) and so fits in log2(tile) = 13 bits where the
   offset needs 60.  The queues are 87%% of this kernel's shared memory and
   shared memory is what it is really short of: an SM divides 128 KB between
   shared and L1, the resident blocks take their cut first, and the group
   tables have to live in what is left.  Every collapse measured while
   tuning this kernel -- 0.36x at cpt 64, 0.29x at cpt 128, 0.33x at wider
   groups -- is that budget, not arithmetic.  Four bytes per queued
   candidate instead of sixteen is what buys them back. */
#define QIDX(JJ, SS) ((QTYPE)(((JJ) * SPB + (SS)) * TPB + threadIdx.x))

/* One test against the packed per-prime uint4 (magic_lo, magic_hi, q,
   boff).  The remainder correction is 32-bit: the true value of
   off - qhat*q is in [0, 2q) < 2^17 and arithmetic mod 2^32 is exact for
   it, and ONE conditional subtraction is enough below 2^63 (see the
   module docstring).

   v4: what is reduced is the OFFSET within the launch, never the absolute
   k.  The launch base enters through e.w, which the host set to
   `2q-block base + (base mod q)`; the bitmap holds each prime's pattern
   TWICE, so `e.w + r` lands in the right copy and the residue
   `(off + base) mod q` is read without ever adding the two.  Same
   instruction count as v3.4, and off < W*per_launch keeps the
   one-subtraction proof intact whatever k itself has grown to. */
#define TEST(IDX, DST) { \
    const uint4 e = pk[IDX]; \
    const unsigned long long mg = ((unsigned long long)e.y << 32) | e.x; \
    unsigned int r = (unsigned int)off \
                   - (unsigned int)__umul64hi(off, mg) * e.z; \
    if (r >= e.z) r -= e.z; \
    const unsigned int b = e.w + r; \
    DST |= (bits[b >> 5] >> (b & 31)) & 1u; }

/* The compacted tail: every lane entering this is alive, so the early
   exit costs what it should.  UNROLL independent Barrett chains hide the
   dependent-chain latency the divergent version could not. */
__device__ __forceinline__ bool tail_survives(
        const unsigned long long off, const int np_, const int from,
        const uint4* __restrict__ pk, const unsigned int* __restrict__ bits)
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
        const int p = atomicAdd(&qn, 1); \
        if (p < Q1CAP) qk[p] = QIDX(JJ, SS); \
        else if (tail_survives(off, np_, LITN, pk, bits)) EMIT(off) \
    } }

/* One candidate of the inner loop: the borrow out of `A - D` is what
   decides m, and it is ALSO what decides which of the two precomputed
   group residues the hoisted prefix reads, so it is computed once and
   handed to both.  See lit_prefix's `hoist`. */
#define STEP(A, DD, SS, JJ) { \
    const unsigned int _d = (DD); \
    const unsigned int _bw = ((A) < _d); \
    const unsigned int _m = _bw ? ((A) - _d + W2C) : ((A) - _d); \
    CAND(b0 + (unsigned long long)W1C * _m, _bw, SS, JJ) }

/* m = A[t] + C[s] reduced mod W2, taken from D = W2 - C rather than from
   C, because `A + C` is NOT a quantity a u32 can hold once there is a
   third wheel level: W2 is then 2.76e9 and a sum of two residues overflows,
   after which the old min-trick silently keeps the wrong branch.  A - D
   never overflows; when it borrows, adding W2 back wraps to exactly A + C,
   which is below W2 in precisely that branch.  Three instructions either
   way, so the block stores D and never C. */
#define M_OF(A, D) (((A) >= (D)) ? ((A) - (D)) : ((A) - (D) + W2C))

/* Rebuild a candidate from its block index.  The generator's own arithmetic
   run backwards: the thread that dequeues is not the thread that queued, so
   D has to be readable by any of them and lives in shared. */
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
        const unsigned int* __restrict__ bits,
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
       impossible worst case: a queue big enough for "every candidate
       survives" costs shared memory, and shared memory costs blocks per
       SM.  Overflow is made harmless instead of impossible -- a candidate
       that does not fit runs its tail on the spot, uncompacted, which is
       the same arithmetic and so the same answer.  G14 forces that path
       and checks the stream is unchanged. */
    __shared__ QTYPE qk[Q1CAP];
    __shared__ QTYPE qk2[Q2CAP];
    __shared__ int qn;
    __shared__ int qn2;
    __shared__ int q3b;
    if (threadIdx.x == 0) { qn = 0; qn2 = 0; }
    __syncthreads();

    /* gridDim.z carries the wheel-period offset from the launch base AND,
       when there is a third wheel level, that level's residue: z = period *
       NU + u.  With NU == 1 the compiler folds both operations away and
       this is exactly the line v4 emitted.  The engine only ever batches
       periods when the whole third level fits in one launch, so u0 is zero
       whenever the quotient can be non-zero. */
    const unsigned long long base = WC
                                  * (unsigned long long)(blockIdx.z / NU);
    const int tbase = blockIdx.x * (blockDim.x * JPT) + threadIdx.x;
    /* The block's per-second-level-residue data, all of it in SHARED and
       built by SPB threads: D = W2 - C, which the generator subtracts and
       which off_of has to be able to read for ANY ss (the thread that
       dequeues is not the thread that queued it), and the hoisted prefix's
       precomputed group residues, which may NOT go in registers -- held per
       thread they cost 72 registers, three resident blocks per SM instead
       of five, and 0.79x.  This kernel is bound by OCCUPANCY, not by
       instruction issue, so a block preamble spends shared, never
       registers.  Declared unconditionally because off_of takes it either
       way; a one-level wheel has SPB == 1 and this is four bytes. */
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
    const int n1 = min(qn, Q1CAP);

    /* Second compaction round: primes LITN..K2, CRT-combined the same way
       the prefix is, branchless over the compacted queue, survivors packed
       again.  Combining these was worth 1.06x and moved K2 from 12 to 16 --
       cheaper tests buy more of them. */
    for (int idx = threadIdx.x; idx < n1; idx += TPB) {
        const unsigned int qi = qk[idx];
        const unsigned long long off = off_of(qi, base, res1x, d2);
        unsigned int kill = 0u;
%(round2)s
        if (!kill) {
            const int p = atomicAdd(&qn2, 1);
            if (p < Q2CAP) qk2[p] = (QTYPE)qi;
            else if (tail_survives(off, np_, K2, pk, bits)) EMIT(off)
        }
    }
    __syncthreads();
    const int n2 = min(qn2, Q2CAP);

    /* THE TAIL DOES NOT RUN HERE.  A block reaches this point with about
       1.2%% of its candidates left -- ~98 of them against TPB threads --
       so five warps in eight sit idle while the block waits on the single
       deepest early-exit chain among the survivors.  Measured, that cost
       32%% of the kernel for 4%% of its lookups.  So the survivors are
       appended to a GLOBAL queue and swept by a second kernel that has one
       item per lane and the whole device in flight.
       One atomic per BLOCK, not per item: qn2 is already the count. */
    if (threadIdx.x == 0) q3b = (n2 > 0) ? atomicAdd(n3, n2) : 0;
    __syncthreads();
    for (int idx = threadIdx.x; idx < n2; idx += TPB) {
        const unsigned long long off = off_of(qk2[idx], base, res1x, d2);
        const int p = q3b + idx;
        /* the same bargain the shared queues make: capacity is a tuning
           constant, and overflow is HARMLESS -- the candidate runs its
           tail on the spot, which is the same arithmetic */
        if (p < q3cap) q3[p] = off;
        else if (tail_survives(off, np_, K2, pk, bits)) EMIT(off)
    }
}

/* The tail, as its own kernel: every lane holds a candidate, the grid is
   sized to the device rather than to a block's leftovers, and a long
   early-exit chain stalls one lane instead of a whole block.  `n3` is read
   on the DEVICE, so no host round trip separates the two kernels. */
extern "C" __global__ void tailsweep(
        const unsigned long long* __restrict__ q3, const int* __restrict__ n3,
        const int q3cap,
        unsigned long long* out, int* nout, const int cap,
        const int np_, const uint4* __restrict__ pk,
        const unsigned int* __restrict__ bits)
{
    const int n = min(*n3, q3cap);
    const int stride = gridDim.x * blockDim.x;
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    /* A plain grid-stride loop, and deliberately so.  A warp here still
       runs to the deepest early-exit chain among its 32 items, and the
       obvious fix -- persistent LANES, each holding a position rather than
       a loop so a dead candidate is replaced without waiting for its
       neighbours -- was built and measured 0.95x: it costs the UNROLL
       independent Barrett chains that hide this loop's load latency, and
       that is worth more here than the divergence it removes.  Priced and
       rejected; do not rebuild it. */
    for (; i < n; i += stride) {
        const unsigned long long off = q3[i];
        if (tail_survives(off, np_, K2, pk, bits)) EMIT(off)
    }
}
"""


def _qcap(tile, surv, sigma=QCAP_SIGMA):
    """Queue capacity from the ANALYTIC survival, plus sigma of margin.

    The count of survivors in a block is a sum of `tile` near-independent
    Bernoulli(surv), so its mean and standard deviation are both known
    exactly (OPTIMIZATION.md 2.6).  Rounded up to a multiple of 32 and
    never larger than the block's own candidate count, which is a bound
    that always holds.
    """
    import math
    mean = tile * surv
    sd = math.sqrt(max(tile * surv * (1.0 - surv), 0.0))
    want = int(math.ceil(mean + sigma * sd))
    want = min(max(want, 32), tile)
    return ((want + 31) // 32) * 32


class GpuEngine:
    """Wheel-generated candidates, Barrett-tested against a bitmap."""

    def __init__(self, n, p1=P1_DEFAULT, p2=P2_DEFAULT, p3=P3_DEFAULT,
                 q2=Q2_DEFAULT,
                 tpb=TPB_DEFAULT, cpt=CPT_DEFAULT, spb=SPB_DEFAULT,
                 jpt=None, lit=None, k2=None, qcap_sigma=QCAP_SIGMA,
                 nu=None):
        import cupy as cp
        self.cp = cp
        self.n, self.p1, self.p2, self.p3 = n, p1, p2, p3
        self.q2, self.tpb = q2, tpb

        self.W1, res1 = wheel(n, p1)
        if self.W1 >= 1 << 32:
            raise ValueError(
                f"first-level wheel modulus {self.W1} needs more than u32; "
                f"the residue type is baked into the kernel, so raising P1 "
                f"past this is a new engine version with a new fingerprint")
        self.R1 = int(res1.size)

        if p2 and p2 > p1:
            W2a, res2 = wheel(n, p2, lo=p1)
            self.R2 = int(res2.size)
            if self.R2 > 65535:
                raise ValueError(
                    f"second-level wheel has {self.R2} residues; the kernel "
                    f"maps them to gridDim.y, which CUDA caps at 65535")
            wheel_top = p2
        else:
            W2a, res2, self.R2 = 1, None, 1
            wheel_top = p1
        # THE THIRD LEVEL.  Its residues ride gridDim.z beside the wheel
        # period, and its own modulus multiplies into W2, so the kernel's
        # inner loop is untouched: a candidate is still base + r1 + W1*m.
        if p3 and p3 > wheel_top and self.R2 > 1:
            W2b, res3 = wheel(n, p3, lo=wheel_top)
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
        if self.R2 > 1:
            if self.W2 >= 1 << 32 or self.W1 * self.W2 >= 1 << 63:
                raise ValueError(
                    f"second-level wheel {self.W1}*{self.W2} exceeds the "
                    f"enforced u32/2^63 limits -- m is a u32 and W1*m is "
                    f"the quantity the one-subtraction reduction bounds, so "
                    f"this is where the wheel stops (at n = 18 the last "
                    f"prime that fits is 47)")
            self.W = self.W1 * self.W2
            self.R = self.R1 * self.R2 * self.R3
            self.inv = pow(self.W1 % self.W2, -1, self.W2)
        else:
            self.inv = 0
            self.W, self.R = self.W1, self.R1

        # The generation tables.  m = ((r2 - r1)*inv) mod W2 splits into one
        # term per index: A[t] = (-r1*inv) mod W2, and r2 -- the residue mod
        # the WHOLE second modulus -- splits again by CRT across the second
        # and third levels, because CRT lifting is linear:
        #
        #   r2 = EA*r2a + EB*r2b (mod W2),  EA = W2b*(W2b^-1 mod W2a), etc.
        #
        # so C[s] = r2a*KA mod W2 and D[u] = r2b*KB mod W2 with KA = EA*inv,
        # KB = EB*inv, and the kernel adds three reduced numbers instead of
        # storing their R2a*R3 combinations.  That is what keeps a wheel of
        # 8.3e13 residues in two tables of 4,560 and 16,675.
        #
        # uint64 is exact throughout: every factor is reduced mod its own
        # modulus first, and the widest product here is r2b*KB < W2b*W2.
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

        self.primes = [q for q in primerange(wheel_top + 1, q2 + 1)]
        if not self.primes:
            raise ValueError("no sieve primes above the wheel")
        # survival through each prefix, exactly: an ordered product over
        # the primes involved, which is what both the compaction depths and
        # the queue capacities are sized from (OPTIMIZATION.md 2.6)
        surv, self.surv = 1.0, []
        for q in self.primes:
            self.surv.append(surv)
            surv *= 1.0 - len(killed_residues(q, n)) / q
        self.surv.append(surv)

        def depth_for(target):
            for i, sv in enumerate(self.surv):
                if sv <= target:
                    return i
            return len(self.primes)

        self.lit = (depth_for(LIT_SURV) if lit is None
                    else min(lit, len(self.primes)))
        self.k2 = (max(self.lit, depth_for(K2_SURV)) if k2 is None
                   else min(max(k2, self.lit), len(self.primes)))
        # Grow the groups greedily, then shrink the modulus budget until
        # the tables fit GROUP_BYTES_MAX.  A cap on the modulus alone is
        # the wrong shape for an L1 budget -- the same cap builds 1 KB at
        # one filter and 500 KB at another -- and this engine now runs
        # wheels far enough apart for that to matter.
        reps = HOIST_TABLE_REPS if self.R2 > 1 else 2
        self.groups = _fit_groups(self.primes, self.lit, LIT_GROUP_MAX, 0,
                                  GROUP_BYTES_MAX, reps=reps)
        left = GROUP_BYTES_MAX - _group_bytes(self.primes, self.groups, reps)
        self.groups2 = _fit_groups(self.primes, self.k2, K2_GROUP_MAX,
                                   self.lit, max(left, 0))

        # Packed forbidden-residue bitmap, 2q bits per prime: each pattern
        # is stored TWICE so that a launch can shift a prime's window by
        # `base mod q` with an ADD to the table offset and no reduction.
        # That is what keeps the absolute k off the device (module
        # docstring, "the (k, off) representation"); it costs 50.6 MB
        # instead of 25.3 MB and no instructions at all.
        offs, tot = [], 0
        for q in self.primes:
            offs.append(tot)
            tot += 2 * q
        bits = np.zeros((tot + 31) // 32, dtype=np.uint32)
        for o, q in zip(offs, self.primes):
            for u in killed_residues(q, n):
                for b in (o + u, o + q + u):
                    bits[b >> 5] |= np.uint32(1) << np.uint32(b & 31)

        # the per-prime constants, one uint4 per prime: a test is one
        # 128-bit uniform load instead of three.  Slot .w is rewritten per
        # launch (offs + base mod q); `_boff` keeps the base copy.
        magic = barrett_magics(self.primes)
        pk = np.empty((len(self.primes), 4), dtype=np.uint32)
        pk[:, 0] = (magic & np.uint64(0xFFFFFFFF)).astype(np.uint32)
        pk[:, 1] = (magic >> np.uint64(32)).astype(np.uint32)
        pk[:, 2] = np.array(self.primes, dtype=np.uint32)
        pk[:, 3] = np.array(offs, dtype=np.uint32)
        self._pk = pk
        self._boff = np.array(offs, dtype=np.uint64)
        self._qs = np.array(self.primes, dtype=np.uint64)
        # W mod q per prime, so a launch's `base mod q` is one vectorised
        # multiply-and-reduce over 6,542 primes rather than 6,542 big-int
        # divisions: base = W*j, so base mod q = (W mod q)*j mod q.
        self._wmod = np.array([self.W % q for q in self.primes],
                              dtype=np.uint64)
        self.d_pk = cp.asarray(pk.ravel())
        self.d_bits = cp.asarray(bits)
        # TWO survivor buffers, because the host classifies what the sieve
        # returns and that work is 8% of a device second at this rate.  A
        # launch is enqueued BEFORE the previous launch's survivors are
        # handed to the caller, so the caller's classification runs while
        # the device is busy.  The readback of launch i-1 still syncs on
        # i-1 alone -- i is not enqueued yet -- so no stream juggling is
        # needed for it, only two buffers.
        self.d_out = [cp.empty(HIT_CAP, dtype=np.uint64) for _ in range(2)]
        self.d_n = [cp.zeros(1, dtype=np.int32) for _ in range(2)]
        self._buf = 0
        self._flush = cp.cuda.Stream.null
        self.d_n3 = cp.zeros(1, dtype=np.int32)

        # a one-level wheel has no second level to spread a block over,
        # so the candidates per thread come back from SPB into JPT
        # rounded DOWN to a power of two: the queues index candidates by
        # (jj, ss, tid) and unpack ss with a shift
        self.spb = 1 << (max(1, min(spb, self.R2)).bit_length() - 1)
        self.jpt = jpt if jpt is not None else max(1, cpt // self.spb)
        self.tile = self.tpb * self.jpt * self.spb   # candidates per block
        # The queues hold a candidate's block index, decoded by shifts, so
        # both factors of that index have to be powers of two.
        self.logtpb = self.tpb.bit_length() - 1
        self.logspb = self.spb.bit_length() - 1
        if (1 << self.logtpb) != self.tpb or (1 << self.logspb) != self.spb:
            raise ValueError(
                f"tpb={self.tpb} and spb={self.spb} must both be powers of "
                f"two: the shared queues store a candidate's (jj, ss, tid) "
                f"index rather than its offset, and it is unpacked by shifts")
        # gridDim.z is ONE budget shared by the wheel periods a launch
        # batches and the third-level residues it carries, z = period*NU + u,
        # so the split is forced rather than chosen: periods may be batched
        # only when the WHOLE third level fits in one launch, since otherwise
        # z / NU is not the period.  With no third level NU is 1 and this is
        # the v4 arithmetic exactly.
        cand_per_u = self.R1 * self.R2
        self.nu = max(1, min(self.R3, 65535,
                             CAND_PER_LAUNCH // max(cand_per_u, 1)
                             if nu is None else nu))
        self.per_launch = (1 if self.nu < self.R3 else
                           max(1, min(65535 // self.nu,
                                      CAND_PER_LAUNCH // self.R)))
        # v4's one-subtraction bound: the largest quantity the kernel ever
        # reduces is the offset of the last candidate in a launch, plus a
        # prime's worth of slack from the folded base.  Trimming the batch
        # is the fix if a very wide wheel ever reaches it -- not a cap on k.
        # (per_launch + 1) and not per_launch: the hoisted prefix reduces
        # `b0 + W1*A`, whose b0 already carries the batch and whose second
        # term reaches W1*W2 = W, so the largest reduced quantity is one
        # wheel period wider than the largest offset.
        while ((self.per_launch + 1) * self.W + self.q2 >= REDUCE_MAX
               and self.per_launch > 1):
            self.per_launch //= 2
        if (self.per_launch + 1) * self.W + self.q2 >= REDUCE_MAX:
            raise ValueError(
                f"one wheel block is W = {self.W}, and W + q2 is not below "
                f"2^63: the kernel's single conditional subtraction is only "
                f"exact there, so this wheel needs a new reduction "
                f"(CONVENTIONS.md numeric hygiene)")

        self.q1cap = _qcap(self.tile, self.surv[self.lit], qcap_sigma)
        self.q2cap = (_qcap(self.tile, self.surv[self.k2], qcap_sigma)
                      if self.k2 > self.lit else 1)
        # The GLOBAL tail queue, sized the same analytic way one launch at a
        # time, and capped: overflow is harmless (the block runs that
        # candidate's tail inline), so this is a memory budget, not a bound.
        cand = self.R1 * self.R2 * self.nu * self.per_launch
        self.q3cap = min(Q3_MAX,
                         max(1024, _qcap(cand, self.surv[self.k2],
                                         qcap_sigma)))

        # The prefix gets the DECOMPOSED form whenever there is a second
        # level to decompose against; round 2 never can (it reads offsets
        # back out of the queue).
        if self.R2 > 1:
            (prefix_src, gtable, self.gdesc,
             pdecl, blockpre, jjpre) = lit_prefix(
                n, self.primes, self.groups, pname="gp",
                hoist=(self.W1, self.W))
        else:
            prefix_src, gtable, self.gdesc = lit_prefix(
                n, self.primes, self.groups, pname="gp")
            pdecl = blockpre = jjpre = ""
        self.d_gbits = cp.asarray(gtable)
        r2_src, g2table, self.gdesc2 = lit_prefix(
            n, self.primes, self.groups2, table="g2bits", indent=8,
            pname="g2p")
        self.d_g2bits = cp.asarray(g2table)
        # Each group's base arrives as a kernel SCALAR (the constant bank),
        # so the prefix issues what v3.4 issued -- see lit_prefix.
        gparams = "".join(
            f",\n        const unsigned long long {p}{i}"
            for p, d in (("gp", self.gdesc), ("g2p", self.gdesc2))
            for i in range(len(d)))
        # inside the BODY macro every line has to end in a continuation
        prefix_m = "\n".join(ln + " \\" for ln in prefix_src.split("\n"))

        key = (n, self.W1, self.W2, q2, tpb, self.jpt, self.spb,
               self.lit, self.k2, self.R3, self.nu,
               self.q1cap, self.q2cap, tuple(map(tuple, self.groups)),
               tuple(map(tuple, self.groups2)))
        if key not in _MODCACHE:
            src = _SRC % {"w1": self.W1, "w2": self.W2, "w": self.W,
                          "two": 1 if self.R2 > 1 else 0, "lit": self.lit,
                          "three": 1 if self.R3 > 1 else 0, "nu": self.nu,
                          "k2": self.k2, "jpt": self.jpt, "tpb": tpb,
                          "spb": self.spb,
                          "logtpb": self.logtpb, "logspb": self.logspb,
                          "qtype": ("unsigned short" if self.tile <= 65535
                                    else "unsigned int"),
                          "unroll": UNROLL, "q1cap": self.q1cap,
                          "q2cap": self.q2cap, "prefix_m": prefix_m,
                          "pdecl": pdecl, "blockpre": blockpre,
                          "jjpre": jjpre,
                          "round2": r2_src, "gparams": gparams}
            _MODCACHE[key] = cp.RawModule(code=src, options=("-std=c++14",),
                                          backend="nvrtc")
        self.k_sieve = _MODCACHE[key].get_function("sieve")
        self.k_tail = _MODCACHE[key].get_function("tailsweep")
        self.d_q3 = cp.empty(self.q3cap, dtype=np.uint64)
        # Blocks in the tail sweep, as a multiple of the SM count.  Swept:
        # 8x per SM is 1.000, 64x is 1.025 and it is flat from there to
        # 256x, so this is the knee.  It oversubscribes deliberately -- the
        # loop is latency-bound per item, so what fills the device is items
        # in flight, not a single wave.
        self.tail_grid = TAIL_BLOCKS_PER_SM * cp.cuda.runtime.\
            getDeviceProperties(cp.cuda.Device().id)["multiProcessorCount"]

    # ------------------------------------------------------------- geometry
    def j_of(self, k):
        """The wheel block a k lives in."""
        return int(k) // self.W

    def density(self):
        """Candidates per unit of k line -- what the wheel is worth."""
        return self.R / float(self.W)

    def bytes_held(self):
        n = (self.d_res1x.nbytes + self.d_bits.nbytes + self.d_pk.nbytes
             + sum(b.nbytes for b in self.d_out)
             + self.d_res2c.nbytes + self.d_res2d.nbytes
             + self.d_gbits.nbytes + self.d_g2bits.nbytes
             + self.d_q3.nbytes)
        return int(n)

    # ---------------------------------------------------------------- sieve
    def _launch_base(self, base):
        """Fold an absolute launch base into the tables, on the host.

        This is the whole of v4.  `base` is a Python int of any size; what
        reaches the device is `base mod q` per prime (slot .w of the uint4,
        pointing into the doubled bitmap) and `base mod Q` per CRT group
        (the gp/g2p scalars).  Both are bounded by their modulus, so the
        device arithmetic never learns how large k has become.

        base mod q is computed as (W mod q)*(j mod q) mod q rather than by
        dividing a big int 6,542 times: both factors are under 2^16, so the
        product is exact in u64 for any j whatsoever.
        """
        j = int(base) // self.W
        if j < (1 << 64):
            bmod = (self._wmod
                    * (np.uint64(j) % self._qs)) % self._qs
        else:
            # j outgrows u64 only on a wheel far too narrow to hunt with,
            # where the modulo cannot be vectorised.  Kept exact anyway:
            # a gate runs here, and a gate that quietly went wrong at the
            # top of the range is the failure this whole version is about.
            bmod = np.array([(int(w) * (j % int(q))) % int(q)
                             for w, q in zip(self._wmod, self._qs)],
                            dtype=np.uint64)
        self._pk[:, 3] = (self._boff + bmod).astype(np.uint32)
        self.d_pk.set(self._pk.ravel())
        return (group_params(self.gdesc, base)
                + group_params(self.gdesc2, base))

    def survivors_j(self, j0, j1):
        """Sorted list of surviving k (Python ints) with k // W in [j0, j1).

        Ints, not a u64 array: above 2^64 there is no numpy dtype for the
        answer, and the survivors are a handful per launch, so the exact
        values are assembled on the host where bigness is free.
        """
        cp = self.cp
        j0, j1 = int(j0), int(j1)
        ceil = k_ceil(self.n)
        if j1 * self.W > ceil:
            raise ValueError(f"k {j1 * self.W} past the enforced ceiling "
                             f"{ceil}")
        if j0 * self.W <= max(K_FLOOR, self.q2):
            raise ValueError(
                "engines refuse to run at or below max(K_FLOOR, q2): the "
                "wheel argument has an exception zone there and a kill by q "
                "needs value > q")
        out = []
        for _, _, surv in self.sweep(j0, j1):
            out.extend(surv)
        return sorted(out)

    def sweep(self, j0, j1, u_from=0):
        """Yield (j_next, u_next, survivors) after every kernel launch.

        `(j_next, u_next)` is a RESUMABLE cursor and `u_next == 0` means the
        stronger thing: every k below `j_next * W` has been swept, so the
        coverage claim may advance.  The two differ because a third wheel
        level makes candidates come out in (t, s, u) order rather than in k
        order, and only a whole period is contiguous in k -- so work is
        resumable per launch (a crash costs one), while COVERAGE is only
        ever claimed per period.  With no third level the two coincide and
        every launch ends a period, which is what v4 did.

        The bounds are checked EAGERLY, here, and the launches are a
        separate generator: a `yield` in this body would defer every check
        to the first `next()`, and a caller that built the iterator and
        never consumed it would sail past the ceiling in silence.  The CPU
        engine carries the same split for the same reason, and the ceiling
        drill is what catches it.
        """
        j0, j1, u_from = int(j0), int(j1), int(u_from)
        ceil = k_ceil(self.n)
        if j1 * self.W > ceil:
            raise ValueError(f"k {j1 * self.W} past the enforced ceiling "
                             f"{ceil}")
        if j0 * self.W <= max(K_FLOOR, self.q2):
            raise ValueError(
                "engines refuse to run at or below max(K_FLOOR, q2): the "
                "wheel argument has an exception zone there and a kill by q "
                "needs value > q")
        return self._sweep(j0, j1, u_from)

    def _sweep(self, j0, j1, u_from):
        cp = self.cp
        gx = (self.R1 + self.tpb * self.jpt - 1) // (self.tpb * self.jpt)
        gy = (self.R2 + self.spb - 1) // self.spb
        pending = None
        for lo in range(0, j1 - j0, self.per_launch):
            n_l = min(self.per_launch, j1 - j0 - lo)
            base = self.W * (j0 + lo)
            # _launch_base rewrites the folded tables, so the launch it
            # belongs to must not be enqueued while an older one is still
            # reading them -- drain first.
            drained = self._collect(pending)
            pending = None
            gps = self._launch_base(base)
            if drained is not None:
                yield drained
            for u0 in range(u_from, self.R3, self.nu):
                nu_l = min(self.nu, self.R3 - u0)
                nxt = u0 + nu_l
                cur = ((j0 + lo + n_l, 0) if nxt >= self.R3
                       else (j0 + lo, nxt))
                # Read the PREVIOUS launch first: that copy waits on it
                # alone, because this launch has not been enqueued yet.
                done = self._collect(pending)
                b = self._buf = self._buf ^ 1
                self.d_n[b].fill(0)
                self.d_n3.fill(0)
                self.k_sieve((gx, gy, n_l * nu_l), (self.tpb,),
                             (np.int32(self.R1),
                              np.int32(self.R2),
                              np.int32(len(self.primes)), self.d_bits,
                              self.d_out[b], self.d_n[b], np.int32(HIT_CAP),
                              self.d_q3, self.d_n3, np.int32(self.q3cap),
                              self.d_pk, self.d_res1x, self.d_res2c,
                              self.d_res2d, np.int32(u0),
                              self.d_gbits, self.d_g2bits, *gps))
                # the queue count is read on the DEVICE, so these two chain
                # back to back with no host round trip between them
                self.k_tail((self.tail_grid,), (self.tpb,),
                            (self.d_q3, self.d_n3, np.int32(self.q3cap),
                             self.d_out[b], self.d_n[b], np.int32(HIT_CAP),
                             np.int32(len(self.primes)), self.d_pk,
                             self.d_bits))
                pending = (base, b, cur)
                # FLUSH.  A launch is asynchronous but on WDDM it is also
                # BATCHED: the driver holds it in a user-mode command buffer
                # until something forces a submit, so without this the
                # device does not start until the host next blocks -- and
                # the host's classification, which is what the double buffer
                # exists to overlap, runs against an IDLE device.  Measured
                # on a 19 ms kernel: spin 9.5 ms on the host, then sync, and
                # the sync still takes 19.0 ms without the query and 9.3 ms
                # with it.  A stream query costs microseconds and is the
                # documented way to flush.
                self._flush.done
                # ...and only now hand the caller the previous launch, so
                # whatever it does with the survivors runs against a busy
                # device rather than an idle one
                if done is not None:
                    yield done
            u_from = 0
        done = self._collect(pending)
        if done is not None:
            yield done

    def _collect(self, pending):
        """(j_next, u_next, survivors) for an enqueued launch, or None."""
        if pending is None:
            return None
        base, b, (jn, un) = pending
        cnt = int(self.d_n[b].get()[0])
        if cnt > HIT_CAP:
            raise RuntimeError(
                f"survivor buffer overflow: {cnt} > {HIT_CAP}; the "
                f"window is too wide or the sieve too shallow")
        surv = []
        if cnt:
            # offsets from the device; the absolute k is made here
            offs = self.cp.asnumpy(self.d_out[b][:cnt])
            surv = sorted(base + int(o) for o in offs)
        return jn, un, surv

    def survivors_k(self, k_lo, k_hi):
        """Same stream, clipped to an arbitrary half-open k window."""
        k_lo, k_hi = int(k_lo), int(k_hi)
        j0, j1 = k_lo // self.W, (k_hi - 1) // self.W + 1
        return [k for k in self.survivors_j(j0, j1) if k_lo <= k < k_hi]


# --------------------------------- gates -----------------------------------

def g7_wheel_matches_oracle():
    """The CRT-lifted wheel == the oracle's brute-force walk of the period.

    Small p1 only: the oracle walks all W residues, which is the point --
    it is the definition, and it is why p1 stops at 13 here.  The
    second-level construction is checked the same way, over its own prime
    range, plus the CRT recombination itself.
    """
    for n, p1 in ((5, 7), (10, 11), (16, 11), (16, 13), (19, 13)):
        W, res = wheel(n, p1)
        Wo, reso = wheel_residues(n, p1)
        if W != Wo or list(res) != list(reso):
            return False, (f"G7 FAIL: n={n} p1={p1}: lifted {len(res)} "
                           f"residues mod {W}, oracle {len(reso)} mod {Wo}")
    # the CRT recombination must reproduce the one-level wheel exactly
    for n, p1, p2 in ((16, 7, 13), (16, 11, 17), (10, 7, 11)):
        W1, r1 = wheel(n, p1)
        W2, r2 = wheel(n, p2, lo=p1)
        inv = pow(W1 % W2, -1, W2)
        got = sorted(int(a) + W1 * (((int(b) - int(a)) * inv) % W2)
                     for a in r1 for b in r2)
        Wf, ref_res = wheel(n, p2)
        if W1 * W2 != Wf or got != [int(v) for v in ref_res]:
            return False, (f"G7 FAIL: CRT recombination at n={n} "
                           f"({p1},{p2}]: {len(got)} vs {len(ref_res)}")
    return True, ("G7 ok: CRT-lifted wheel == oracle period walk at "
                  "(n,p1) = (5,7), (10,11), (16,11), (16,13), (19,13); the "
                  "two-level CRT recombination == the one-level wheel at "
                  "three (p1,p2] splits")


def g8_wheel_partitions_the_period():
    """Kept + killed == the whole period, and the count is the formula.

    The direction that matters is the second one: a wheel that DROPS a
    residue it should have kept loses candidates silently, and no parity
    gate against another engine using the same wheel could ever see it.
    """
    from sqladder_reference import w as w_formula
    for n, p1, lo in ((16, 13, 1), (16, 23, 1), (11, 23, 1), (19, 19, 1),
                      (16, 37, 23), (16, 31, 23), (17, 37, 23)):
        W, res = wheel(n, p1, lo=lo)
        want = 1
        for q in primerange(lo + 1, p1 + 1):
            want *= q - w_formula(q, n)
        if res.size != want:
            return False, (f"G8 FAIL: n={n} ({lo},{p1}]: {res.size} "
                           f"residues, formula says {want}")
        if len(set(res.tolist())) != res.size:
            return False, f"G8 FAIL: n={n} ({lo},{p1}]: duplicate residues"
        for q in primerange(lo + 1, p1 + 1):
            bad = set(killed_residues(q, n))
            if np.isin(res % q, np.array(sorted(bad), dtype=np.int64)).any():
                return False, (f"G8 FAIL: n={n} ({lo},{p1}]: a kept residue "
                               f"is killed by q={q}")
    return True, ("G8 ok: the wheel is exactly prod(q - w(q,n)) residues, "
                  "duplicate-free, none of them killed by a wheel prime, at "
                  "(n,p1) = (16,13), (16,23), (11,23), (19,19) and at the "
                  "SECOND-level ranges (23,37], (23,31], (23,37] at n=17")


def g9_gpu_matches_cpu():
    """GPU survivor stream == CPU survivor stream, bit for bit.

    Populated windows at three filters and four heights, the last of them
    hard against the enforced ceiling, because a reduction that is correct
    at 1e12 and wrong at 1e22 is exactly the bug a mid-range parity gate
    cannot see.  Since v4 that top height is ABOVE 2^64, so this gate is
    also what proves the (k, off) split does what it claims: the CPU side
    is Python ints all the way up, and the GPU side is arithmetic that has
    no word wide enough to hold the answers it is producing.

    BOTH wheel paths are covered -- the one-level kernel the
    frozen fingerprints are pinned to, and the two-level CRT kernel the
    campaign runs -- because they generate the same candidates by
    different arithmetic.  An empty-vs-empty comparison is vacuous and is
    refused.
    """
    # The two-level cases are chosen so the COMBINED modulus stays small
    # enough that a dense CPU sieve can cover a populated window: a wheel
    # block of the production split (23, 37] is 7.4e12 of k line, which no
    # dense array can hold.  The kernel is the same code at every split --
    # only W1, W2 and W1^-1 change -- so these exercise its arithmetic in
    # full, and G13 pins the production constants themselves.
    ceil16 = k_ceil(16)
    cases = ((10, 13, None, None, 256, 2 * 10 ** 9, 4 * 10 ** 6),
             (16, 13, None, None, 128, 10 ** 12, 2 * 10 ** 7),
             (16, 17, None, None, 256, 9 * 10 ** 14, 10 ** 8),
             (16, 23, None, None, 64, ceil16 - 3 * 223_092_870, 3 * 10 ** 7),
             (16, 13, 23, None, 128, 10 ** 12, 2 * 10 ** 7),
             (16, 13, 17, None, 256, 9 * 10 ** 14, 10 ** 8),
             (16, 11, 23, None, 64, ceil16 - 3 * 223_092_870, 3 * 10 ** 7),
             # THREE-level: the v5 kernel, at splits small enough that a
             # dense CPU sieve can still follow a populated window
             (10, 11, 13, 17, 256, 2 * 10 ** 9, 4 * 10 ** 6),
             (16, 11, 13, 17, 64, 10 ** 12, 2 * 10 ** 7),
             (16, 13, 17, 19, 128, 9 * 10 ** 14, 4 * 10 ** 7),
             (16, 17, 19, 23, 256, ceil16 - 3 * 223_092_870, 3 * 10 ** 7))
    total = 0
    for n, p1, p2, p3, q2, k_lo, span in cases:
        eng = GpuEngine(n, p1=p1, p2=p2, p3=p3, q2=q2)
        got = eng.survivors_k(k_lo, k_lo + span)
        cpu = CpuEngine(n, q2=q2)
        want = [k for c in cpu.survivors(k_lo, k_lo + span) for k in c]
        if got != want:
            gs, ws = set(got), set(want)
            return False, (f"G9 FAIL: n={n} p1={p1} p2={p2} p3={p3} q2={q2} "
                           f"at k~{k_lo:.3g}: GPU {len(got)} vs CPU "
                           f"{len(want)}, diff {sorted(gs ^ ws)[:4]}")
        if not got:
            return False, (f"G9 FAIL: n={n} p1={p1} p2={p2} p3={p3} at "
                           f"k~{k_lo:.3g} is empty -- vacuous parity check")
        total += len(got)
    return True, (f"G9 ok: GPU stream == CPU stream on {len(cases)} populated "
                  f"windows ({total} survivors) -- one-level, two-level AND "
                  f"three-level wheels, filters n = 10, 16, heights 2e9 -> "
                  f"{ceil16:.3g}, the top windows ABOVE 2^64")


def g13_production_wheel_constants():
    """The baked CRT constants of the configurations the campaign runs.

    G9 proves the two-level KERNEL is right, but only at splits whose
    combined wheel a dense CPU sieve can follow.  The production split is
    bigger than that by four orders of magnitude, and what differs there
    is not code but three literals compiled into the source: W1, W2 and
    W1^-1 mod W2.  This gate checks those literals directly, on the host,
    against the definition -- so nothing about the production engine rests
    on a configuration that was never examined.
    """
    rng = np.random.default_rng(20260821)
    from sqladder_reference import w as w_formula
    for n, p1, p2, p3 in ((16, 23, 37, None), (16, 23, 31, None),
                          (17, 23, 37, None), (18, 23, 37, 47)):
        W1, r1 = wheel(n, p1)
        W2a, r2 = wheel(n, p2, lo=p1)
        if p3:
            W2b, r3 = wheel(n, p3, lo=p2)
            EA = W2b * pow(W2b % W2a, -1, W2a)
            EB = W2a * pow(W2a % W2b, -1, W2b)
        else:
            W2b, r3, EA, EB = 1, np.zeros(1, dtype=np.int64), 1, 0
        W2 = W2a * W2b
        if W2 >= 1 << 32:
            return False, (f"G13 FAIL: n={n} ({p1},{p2},{p3}]: W2 = {W2} "
                           f"needs more than a u32, which is the bound that "
                           f"stops the wheel at 47")
        inv = pow(W1 % W2, -1, W2)
        if W1 % W2 * inv % W2 != 1:
            return False, f"G13 FAIL: n={n} ({p1},{p2}]: W1^-1 is wrong"
        top = p3 or p2
        want = 1
        for q in primerange(2, top + 1):
            want *= q - w_formula(q, n)
        if r1.size * r2.size * r3.size != want:
            return False, (f"G13 FAIL: n={n} ({p1},{p2},{p3}]: "
                           f"{r1.size}*{r2.size}*{r3.size} != {want}")
        killed = {q: set(killed_residues(q, n))
                  for q in primerange(2, top + 1)}
        ts = rng.integers(0, r1.size, 4000)
        ss = rng.integers(0, r2.size, 4000)
        us = rng.integers(0, r3.size, 4000)
        for t, sx, u in zip(ts.tolist(), ss.tolist(), us.tolist()):
            a, b = int(r1[t]), int(r2[sx])
            c = int(r3[u])
            bc = (EA * b + EB * c) % W2           # the CRT of the two halves
            x = a + W1 * (((bc - a) * inv) % W2)
            if not 0 <= x < W1 * W2:
                return False, f"G13 FAIL: n={n} CRT value {x} out of range"
            if x % W1 != a or x % W2a != b or (p3 and x % W2b != c):
                return False, (f"G13 FAIL: n={n} CRT value {x} does not "
                               f"recombine to ({a}, {b}, {c})")
            for q, bad in killed.items():
                if x % q in bad:
                    return False, (f"G13 FAIL: n={n} ({p1},{p2},{p3}]: CRT "
                                   f"value {x} is killed by q={q}")
    return True, ("G13 ok: the wheel constants (W1, W2a, W2b, W1^-1 and the "
                  "two CRT lifts) are exact at (n,p1,p2,p3) = (16,23,37,-), "
                  "(16,23,31,-), (17,23,37,-) and the production "
                  "(18,23,37,47); 4000 sampled CRT residues per config "
                  "recombine to all THREE levels and survive every wheel "
                  "prime; and W2 is checked under 2^32, which is the bound "
                  "that stops the wheel at 47")


def g14_v3_mechanisms():
    """The three v3 mechanisms, each against its own definition.

    G9 would catch any of these end-to-end, but only where a dense CPU
    sieve can follow -- and the split-CRT tables and the literal prefix are
    exactly the things whose PRODUCTION values G9 cannot reach.  So each is
    checked here on the host, at the production configuration, against the
    definition it is supposed to implement.

      A/C tables   A[t] + C[s] (mod W2) must be the m the one-table CRT
                   would have computed, for every sampled pair -- and the
                   reconstructed k must be the same integer.
      literals     the baked 64-bit kill mask and bit offset of each
                   literal-prefix prime must agree with killed_residues and
                   with the packed bitmap the table path reads.
      queue        the shared queue holds JPT*TPB and a block owns exactly
                   JPT*TPB candidates, so "cannot overflow" is arithmetic,
                   not optimism.
    """
    rng = np.random.default_rng(20260822)
    cases = ((16, 23, 37, None, 65536), (17, 23, 37, None, 65536),
             (16, 23, 31, None, 4096), (18, 23, 37, 47, 65536))
    for n, p1, p2, p3, q2 in cases:
        W1, r1 = wheel(n, p1)
        W2a, r2 = wheel(n, p2, lo=p1)
        if p3:
            W2b, r3 = wheel(n, p3, lo=p2)
            # the CRT lift of the two second-level halves, exactly as the
            # engine builds it: r2 = EA*r2a + EB*r2b (mod W2)
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
        for t, s, u in zip(rng.integers(0, r1.size, 3000).tolist(),
                           rng.integers(0, r2.size, 3000).tolist(),
                           rng.integers(0, r3.size, 3000).tolist()):
            m_split = (int(A[t]) + int(C[s]) + int(D[u])) % W2
            if max(int(A[t]), int(C[s]), int(D[u])) >= W2:
                return False, (f"G14 FAIL: n={n}: a split table entry is "
                               f"not reduced mod W2, so the kernel's single "
                               f"conditional subtract is not enough")
            # the ONE-TABLE reference: the residue mod the whole second
            # modulus, recombined from its two halves by CRT
            r2u = (EA * int(r2[s]) + EB * int(r3[u])) % W2
            m_ref = ((r2u - int(r1[t])) * inv) % W2
            if m_split != m_ref:
                return False, (f"G14 FAIL: n={n} ({p1},{p2},{p3}]: "
                               f"A[{t}]+C[{s}]+D[{u}] gives m={m_split}, "
                               f"CRT says {m_ref}")
            x = int(r1[t]) + W1 * m_split
            if x % W1 != int(r1[t]) or x % W2a != int(r2[s]):
                return False, (f"G14 FAIL: n={n}: reconstructed x does not "
                               f"recombine to its own residues")
            if p3 and x % W2b != int(r3[u]):
                return False, (f"G14 FAIL: n={n}: the THIRD level's residue "
                               f"is not the one reconstructed")

        eng = GpuEngine(n, p1=p1, p2=p2, p3=p3, q2=q2)
        primes = eng.primes

        # The compaction depths are DERIVED from the survival curve, not
        # carried over as counts from the shape they were swept on, so the
        # gate checks the derivation rather than two magic numbers: each
        # depth is the first one at or under its target, and the one before
        # it is not.  (Shipping the counts instead cost the coarse-wheel
        # benchmark shapes 22% each.)
        for name, depth, target in (("LIT", eng.lit, LIT_SURV),
                                    ("K2", eng.k2, K2_SURV)):
            if depth > len(primes):
                return False, f"G14 FAIL: n={n}: {name} past the sieve"
            if eng.surv[depth] > target and depth < len(primes):
                return False, (f"G14 FAIL: n={n}: {name}={depth} leaves "
                               f"{eng.surv[depth]:.4f} alive, over the "
                               f"{target} target")
            if depth > 0 and eng.surv[depth - 1] <= target and \
                    depth > eng.lit:
                return False, (f"G14 FAIL: n={n}: {name}={depth} is deeper "
                               f"than it needs to be -- {depth - 1} already "
                               f"leaves {eng.surv[depth - 1]:.4f}")

        for tag, groups, table_src, budget, lo, hi in (
                ("prefix", eng.groups,
                 lit_prefix(n, primes, eng.groups), LIT_GROUP_MAX,
                 0, eng.lit),
                ("round 2", eng.groups2,
                 lit_prefix(n, primes, eng.groups2, table="g2bits"),
                 K2_GROUP_MAX, eng.lit, eng.k2)):
          src, table, _descs = table_src
          if [i for g in groups for i in g] != list(range(lo, hi)):
            return False, (f"G14 FAIL: n={n}: the {tag} grouping "
                           f"{groups} does not cover primes "
                           f"[{lo}, {hi}) exactly once, in order")
          off_bits = 0
          for g in groups:
              qs = [primes[i] for i in g]
              Q = 1
              for q in qs:
                  Q *= q
              if Q > budget:
                  return False, (f"G14 FAIL: n={n}: {tag} group {qs} has "
                                 f"modulus {Q} over the {budget} budget that "
                                 f"keeps the combined table in L1")
              if f"* {Q}u;" not in src or \
                      f"__umul64hi(off, {(1 << 64) // Q}ULL)" not in src:
                  return False, (f"G14 FAIL: n={n}: modulus {Q} or its magic "
                                 f"is not baked into the {tag} source")
              # every residue mod Q must agree with "killed by some q in g"
              want = np.zeros(Q, dtype=bool)
              for q in qs:
                  bad = np.array(killed_residues(q, n), dtype=np.int64)
                  want |= np.isin(np.arange(Q) % q, bad)
              if Q < LIT_INLINE_Q:
                  mask = 0
                  for u in killed_residues(qs[0], n):
                      mask |= 1 << u
                  got = np.array([(mask >> u) & 1 for u in range(Q)], bool)
              else:
                  # v4 stores the pattern TWICE so a launch can shift it by
                  # base mod Q with an add; BOTH copies are checked, because
                  # a half-written second copy is invisible at base 0 and
                  # wrong everywhere else.
                  b = off_bits + np.arange(2 * Q)
                  got2 = ((table[b >> 5] >> (b & 31)) & 1).astype(bool)
                  if not np.array_equal(got2[:Q], got2[Q:]):
                      return False, (f"G14 FAIL: n={n}: the {tag} table for "
                                     f"{qs} is not periodic with period "
                                     f"{Q} -- the doubled copy differs")
                  got = got2[:Q]
                  off_bits += ((2 * Q + 31) // 32) * 32
              if not np.array_equal(got, want):
                  return False, (f"G14 FAIL: n={n}: the {tag} table for "
                                 f"{qs} (modulus {Q}) disagrees with "
                                 f"killed_residues at "
                                 f"{int(np.flatnonzero(got != want)[0])}")

    # The queues are sized from the survival rate rather than the worst
    # case, so overflow is POSSIBLE -- and the whole design rests on it
    # being harmless.  A silent drop there would lose a survivor, which is
    # to say it could lose a discovery, so the path is not argued but
    # FORCED: an engine whose queues hold 32 entries against a block that
    # owns thousands takes the fallback for nearly every candidate, and its
    # stream must be identical to the properly-sized engine's.
    ref = GpuEngine(16, p1=13, p2=23, p3=None, q2=128)
    tiny = GpuEngine(16, p1=13, p2=23, p3=None, q2=128,
                     qcap_sigma=-1e9)
    if tiny.q1cap > 32 or (tiny.k2 > tiny.lit and tiny.q2cap > 32):
        return False, (f"G14 FAIL: the forced-overflow engine still has "
                       f"room ({tiny.q1cap}, {tiny.q2cap}) -- the drill "
                       f"would not exercise the fallback")
    lo, span = 10 ** 12, 4 * 10 ** 8
    a, b = ref.survivors_k(lo, lo + span), tiny.survivors_k(lo, lo + span)
    if not a:
        return False, "G14 FAIL: the overflow drill window is empty"
    if a != b:
        return False, (f"G14 FAIL: the queue-overflow fallback changed the "
                       f"stream: {len(a)} survivors properly sized, "
                       f"{len(b)} with the queues forced full")

    prod = GpuEngine(16)
    if not 0 < prod.q1cap <= prod.tile or not 0 < prod.q2cap <= prod.tile:
        return False, (f"G14 FAIL: production queue capacities "
                       f"({prod.q1cap}, {prod.q2cap}) are not within "
                       f"(0, tile = {prod.tile}]")
    return True, (f"G14 ok: the split A/C generation tables reproduce the "
                  f"one-table CRT on 12000 sampled triples at "
                  f"(n,p1,p2,p3) = (16,23,37,-), (17,23,37,-), (16,23,31,-) "
                  f"and the production (18,23,37,47); the compaction "
                  f"depths derive from the survival curve (production "
                  f"LIT={prod.lit}, K2={prod.k2}); the CRT-combined prefix "
                  f"and round-2 groups cover their prime ranges exactly "
                  f"once in order, stay inside their modulus budgets, and "
                  f"every group's table agrees with killed_residues on "
                  f"EVERY residue of its modulus; production queues hold "
                  f"{prod.q1cap} and {prod.q2cap} of a {prod.tile}-candidate "
                  f"block (analytic occupancy {prod.tile * prod.surv[prod.lit]:.0f}"
                  f" and {prod.tile * prod.surv[prod.k2]:.0f}); and with the "
                  f"queues forced to 32 so the overflow path runs for nearly "
                  f"every candidate, the survivor stream is IDENTICAL "
                  f"({len(a)} survivors)")


def g15_k_off_representation():
    """The v4 split: the base is folded, not carried, and folding is exact.

    G9 already shows the whole engine agrees with the CPU above 2^64.  This
    gate isolates the three mechanisms that make that possible, because a
    fold that is wrong only for some bases would pass a parity check taken
    at one height and lose survivors everywhere else.

      1. BASE-SHIFT INVARIANCE.  The same absolute window, sieved with the
         launch batching forced to different sizes, is covered from
         different bases with different folded tables -- and must return
         the identical stream.  This is the property the whole design
         rests on and the one a fixed-base test cannot see.
      2. The doubled bitmap really is periodic with period q, per prime.
         The second copy is what lets `boff + base mod q + r` skip a
         reduction; a half-built copy is invisible at base 0.
      3. The folded values are the residues they claim to be, for primes
         and for CRT groups, at bases chosen to be nastier than any the
         campaign will meet -- including above 2^64.
    """
    # 1. base-shift invariance
    eng = GpuEngine(16, p1=13, p2=23, p3=None, q2=512)
    j0 = eng.j_of(10 ** 12)
    eng.per_launch = 1
    one = eng.survivors_j(j0, j0 + 6)
    eng.per_launch = 6
    many = eng.survivors_j(j0, j0 + 6)
    if not one:
        return False, "G15 FAIL: the base-shift window is empty -- vacuous"
    if one != many:
        return False, (f"G15 FAIL: the stream depends on the launch base: "
                       f"{len(one)} survivors in 6 launches vs {len(many)} "
                       f"in 1 -- the fold is not base-invariant")

    # 2. the doubled bitmap is periodic, per prime
    bits = eng.cp.asnumpy(eng.d_bits)
    rng = np.random.default_rng(4)
    for i in rng.integers(0, len(eng.primes), 40).tolist():
        q = eng.primes[i]
        o = int(eng._boff[i])
        b = o + np.arange(2 * q)
        pat = ((bits[b >> 5] >> (b & 31)) & 1).astype(bool)
        if not np.array_equal(pat[:q], pat[q:]):
            return False, (f"G15 FAIL: prime {q}'s bitmap is not periodic "
                           f"with period q -- the doubled copy differs")
        want = np.zeros(q, dtype=bool)
        want[killed_residues(q, 16)] = True
        if not np.array_equal(pat[:q], want):
            return False, (f"G15 FAIL: prime {q}'s bitmap disagrees with "
                           f"killed_residues")

    # 3. the fold is the residue it claims to be, at absurd bases
    for base in (0, eng.W, 10 ** 12, 2 ** 64 + 12345, k_ceil(16) - eng.W,
                 10 ** 30):
        base -= base % eng.W                      # launches start on a block
        gps = eng._launch_base(base)
        got = eng._pk[:, 3].astype(np.int64) - eng._boff.astype(np.int64)
        want = np.array([base % q for q in eng.primes], dtype=np.int64)
        if not np.array_equal(got, want):
            i = int(np.flatnonzero(got != want)[0])
            return False, (f"G15 FAIL: at base {base:.4g} the fold for prime "
                           f"{eng.primes[i]} is {got[i]}, not "
                           f"{want[i]} = base mod q")
        # and the group scalars: reading the table at r must answer
        # "is (off + base) killed", for every residue of the modulus
        descs = list(eng.gdesc) + list(eng.gdesc2)
        gtab = (eng.cp.asnumpy(eng.d_gbits), eng.cp.asnumpy(eng.d_g2bits))
        for gi, ((kind, Q, payload), gp) in enumerate(zip(descs, gps)):
            tab = gtab[0 if gi < len(eng.gdesc) else 1]
            if kind == "modq":
                # A HOISTED group folds the base into its per-residue value
                # (lit_prefix, `hoist`), so its table is one copy and its
                # scalar is the residue itself -- there is no second copy to
                # index into and the claim to check is exactly that.
                if int(gp) != base % Q:
                    return False, (f"G15 FAIL: hoisted group {gi} (modulus "
                                   f"{Q}) at base {base:.4g}: scalar "
                                   f"{int(gp)} is not base mod Q = "
                                   f"{base % Q}")
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
                  f"base ({len(one)} survivors, 1 launch vs 6); the doubled "
                  f"bitmap is periodic and matches killed_residues on 40 "
                  f"sampled primes; and every per-prime and per-group fold "
                  f"is exactly (base mod modulus) at six bases up to 1e30 -- "
                  f"so nothing on the device is bounded by k")


def _tab_bit(tab, off_bits, u):
    b = int(off_bits) + int(u)
    return bool((tab[b >> 5] >> (b & 31)) & 1)


def g16_v5_mechanisms():
    """The three things v5 added that nothing else can see fail.

    G9 proves the whole pipeline against a dense CPU sieve, but only at
    splits it can follow, and only in the configuration the engine happens
    to CHOOSE.  Each of these is a place where a wrong answer would be
    silent -- fewer survivors, not different ones -- so each is forced.

      1. THE GLOBAL TAIL QUEUE OVERFLOWS HARMLESSLY.  Its capacity is sized
         from the analytic survival, so overflow is possible by design and
         has to cost nothing but speed: a candidate that does not fit runs
         its tail in the block that produced it.  Forced by setting the
         capacity to zero, which sends EVERY candidate down the fallback.
      2. THE THIRD LEVEL CHUNKS WITHOUT MOVING THE STREAM.  gridDim.z
         carries the third-level residue, so a launch covers only part of
         it and the host loops; a chunking that dropped or repeated a
         residue would quietly change coverage.  Checked against nu forced
         to 1, 2 and 3 against the unchunked engine.
      3. THE QUEUES INDEX CANDIDATES, and the index is unpacked by shifts,
         so tpb and spb must be powers of two.  Checked by construction:
         asking for a non-power raises rather than silently mis-decoding.
    """
    n, p1, p2, p3, q2 = 16, 13, 17, 19, 128
    lo, span = 9 * 10 ** 14, 4 * 10 ** 7
    ref = GpuEngine(n, p1=p1, p2=p2, p3=p3, q2=q2)
    want = ref.survivors_k(lo, lo + span)
    if not want:
        return False, "G16 FAIL: the drill window is empty -- vacuous"

    flood = GpuEngine(n, p1=p1, p2=p2, p3=p3, q2=q2)
    flood.q3cap = 0                    # every tail runs in the sieve block
    if flood.survivors_k(lo, lo + span) != want:
        return False, ("G16 FAIL: with the global tail queue forced to zero "
                       "the survivor stream changed -- the overflow "
                       "fallback is not the same arithmetic")

    for nu in (1, 2, 3):
        e = GpuEngine(n, p1=p1, p2=p2, p3=p3, q2=q2, nu=nu)
        if e.nu != min(nu, e.R3):
            return False, f"G16 FAIL: nu={nu} was not honoured ({e.nu})"
        if e.survivors_k(lo, lo + span) != want:
            return False, (f"G16 FAIL: chunking the third level at nu={nu} "
                           f"changed the stream")

    for bad in (dict(tpb=192), dict(spb=6, cpt=24)):
        try:
            GpuEngine(n, p1=p1, p2=p2, p3=p3, q2=q2, **bad)
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


GATES = [g7_wheel_matches_oracle, g8_wheel_partitions_the_period,
         g13_production_wheel_constants, g14_v3_mechanisms,
         g9_gpu_matches_cpu, g15_k_off_representation, g16_v5_mechanisms]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
