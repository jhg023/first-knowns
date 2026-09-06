"""lcml_gpu.py -- the GPU engine for the lcm ladders.

The same mathematics a third time, in CuPy, and shaped so that nothing it
shares with the CPU engine could hide a bug in either.

WHAT THE KERNEL DOES (v4, the WINDOW sieve).  The CPU engine materialises
the dense k line and marks arithmetic progressions into it.  This engine
never forms the line.  It carries a wheel index and reconstitutes

    k = W*j + x,        x congruent to a residue that no wheel prime kills

and then sieves the candidates of a fixed residue x across a SEGMENT of
PB consecutive wheel periods at once (64 or 128, `pb_for`).  For a fixed
x the candidates of consecutive periods form an arithmetic progression
modulo every sieve prime q with an invertible step (Wp mod q: q is above
the wheel and not in the unit), so "which of the PB periods does q kill"
depends on x mod q alone and is a PB-bit WINDOW into a periodic bit
pattern stored once per prime (`window_patterns`):

    Dinv = (Wp mod q)^-1,   r'' = x * Dinv mod q,
    q | W*(j0 + j) + x  - kr   <=>   (r'' + j) mod q  in  { kr * Dinv }

One window is NW + 1 aligned 32-bit loads and NW funnel shifts for 32*NW
candidates, and r'' is linear in the CRT decomposition of x, so per group
per residue it is one add of a per-thread table value (x0), a per-block
value (ne, the launch base folded in as j0 mod q because Wp*Dinv == 1) and
the CRT borrow.  The sieve primes below BIT_SURV survival (~0.7%) are
tested this way; the survivors are extracted from the live words into a
shared queue as (residue, period) and take the PER-CANDIDATE route -- the
in-block compaction ROUNDS (single-prime Barrett tests against packed
tables, halving the queue each round down to K2_SURV4) and then the
global TAIL ROUNDS over queues with several lanes per item, both as in
v1-v3.  Every push into a queue is ONE shared atomic per warp
(`warp_reserve`).  What made v3's kernel slow was ~12 instructions per
candidate per prefix group; what makes this one fast is ~10 per prime per
64 candidates, and what bounds it is the latency of its load chain, not
issue (OPTIMIZATION_LOG.md v4, where every variant that did not pay is
also recorded).

Everything problem-specific enters through `killed_residues(q, n, fam,
unit)`: the wheel tables, the window patterns, the x0 table, the round
tables, the tail's masks and residue lists and the survival curve the
compaction points are derived from are all built from that one function,
so the same code sieves all seven families and both signs.

UNIT SPACE.  Every candidate at the campaign filters is a multiple of a
forced modulus (lcml_search.forced_unit), so the device sweeps
k' = k / unit with the kill sets K'(q) = unit^-1 * K(q,n,F) mod q and the
unit's own primes left out of the wheel.  Everything the device touches is
in k'; `self.W` (the period), the survivors and every bound check are in
k, and `_collect` is the one place the unit is multiplied back in.
`unit = 1` is the k-space engine, and the gate battery runs it on wheels a
dense CPU sieve can follow.  `assert_unit` refuses a unit that is not
forced at the filter, which is the one way this could thin the line.

THE SEGMENT IS THE COVERAGE UNIT.  `sweep(j0, j1)` covers periods [j0, j1)
in segments of `seg_periods` (PB, or several PB-windows batched on a
small wheel), each segment in `launches_per_segment` launches of a
first-level chunk x a few third-level residues x every second-level
residue x every period of the segment; the cursor it yields is (segment
start, launches done), and a partial last segment is masked by period.
A window may start inside period 0: `sweep` and `survivors_j` take
`k_min` and the host drops every survivor below it, which is exact.

CEILINGS, stated and enforced (CONVENTIONS.md "Numeric hygiene"):
  * k < k_ceil(n, F) = huntlib.ceiling.K_CEIL = 1e40 for every family and
    both signs (lcml_search, G10; v3): a discovery is proved by a BLS75
    certificate on N - s = m*k, and the ceiling is where that
    certificate's worst case was measured to cost seconds.
  * (seg_periods + 1) * W' + q2 < 2^63 = REDUCE_MAX on the DEVICE period
    W' (k' units): the largest offset the Barrett tail reduces is a
    segment plus one period wide, and one conditional subtraction is exact
    only below 2^63.  That is what caps the window at 128 periods on the
    unit wheel.
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
unit space, including above 2^64, hard against the 1e40 ceiling, and a
CLIPPED PERIOD 0), G13 (the production wheel constants of every family's
opening), G14 (the generation tables, the derived compaction depths, the
round tables, THE WINDOW CHAIN -- x0, ne, borrow, pattern word -- against
killed_residues on sampled candidates, and the queue-overflow fallback),
G15 (the (k, off) representation: the stream is invariant under the launch
decomposition and under a split inside a segment, the tail's masks and
residue lists, and the folded scalars), G16 (the third level: the global
tail queue's overflow, chunking, and the power-of-two queue index), G17
(the production unit wheel, v1's wheel and a k-space wheel return
identical survivors over the same absolute windows), G18 (every campaign
configuration compiles to the occupancy the engine was tuned at, no
spills, the carveout pinned and the window tables inside their cap).
"""

import pathlib as _pathlib
import sys as _sys
from functools import lru_cache as _lru_cache

import math

import numpy as np
from sympy import primerange

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from huntlib import shutdown as _shutdown                      # noqa: E402
from huntlib.gpu import barrett_magics                         # noqa: E402
from huntlib.primes import MR_VALID_BELOW                      # noqa: E402
from lcml_reference import (FAMILIES, FOUND, KNOWN, family,  # noqa: E402
                               forbidden_k_residues, nforms, sign,
                               wheel_residues)
from lcml_search import (Q2_DEFAULT, CpuEngine, assert_unit,  # noqa: E402
                            forced_unit, k_ceil, k_floor, killed_residues)

# THE X-SPACE WHEEL (unit = 1).  Kept as the defaults of this class because
# the x-space benchmark shapes and most of the gates run on it; the
# CAMPAIGN runs the unit wheel `wheel_plan` chooses below.
P1_DEFAULT = 23              # first-level wheel: the primes up to here
P2_DEFAULT = 37              # second-level wheel: the primes in (P1, P2]
# THIRD-level wheel: the primes in (P2, P3].  47 IS THE LAST ONE, and not
# by choice: m is a u32 and W1*m is what the one-conditional-subtraction
# reduction bounds, so the combined second modulus must stay under 2^32.
# Primes to 47 make it 2.76e9; adding 53 makes it 1.46e11.  The engine
# raises rather than wrapping.
P3_DEFAULT = 47
# THE WHEEL IS RE-CHOSEN AT EVERY FILTER, AND THAT IS THE DIFFERENCE.
#
# The linear ladders could bake one wheel into the launcher: their unit was
# 30030 there from n = 15 and only ever grew, and w(q,n) = min(n, q-1) meant the
# residue counts moved smoothly.  Here neither holds.  The unit is 2 at
# n = 15, 34 at n = 16 (17 = n + 1 is forced), 2 again at n = 17, 114 at
# n = 18; and the kill counts jump by a factor of q at every filter where a
# prime enters L(n) (w(17, 16) = 16 but w(17, 17) = 1).  So the residues
# kept per level, the period W', how many periods fit under 2^63 and hence
# the window width are all different at every opening -- in both
# directions.  A constant carried one filter forward is simply wrong, which
# is why `wheel_plan` computes it and `launch.py` never stores one.
#
# What the plan has to satisfy, all enforced in GpuEngine.__init__:
#   W1 < 2^32 (the first-level residue type is baked into the kernel),
#   W2 < 2^32 and W1*W2 < 2^63 (the one-subtraction reduction),
#   R2, R3 <= 65535 (they ride gridDim.y and .z),
#   (PV + 1) W' + q2 < 2^63 with PV >= PV_MIN (the window has to be worth
#   having: a wheel that admits eight periods spends the whole window
#   mechanism on eight bits).
# and what it optimizes is candidates per unit of line, which is
# prod(w-kept)/W' -- lower is better.
PV_MIN = 32
# The first-level table is R1 entries and the x0 table is R1 per window
# group, so R1 is the memory the plan spends.  2^21 is ~50 MB of x0 at 12
# groups; the plan will take a denser wheel over a bigger table only when it
# actually buys candidates.
R1_MAX = 1 << 21
# The largest prime the wheel will consider.  Above this the value density is
# far below what is already in and the enumeration gets slower for nothing.
WHEEL_TOP = 89

# THE SIEVE DEPTH IS PLANNED TOO, AND IT IS A LOAD DECISION.
#
# q2 trades device time against HOST time, and the sweep that measures only
# throughput cannot see the second (OPTIMIZATION.md rule 7).  Measured at
# n = 15 of A078502, three interleaved rounds at pb = 192, with the host
# classification cost measured separately at 17 us per survivor:
#
#   q2       device x/s   ratio   survivors/s   host cores needed
#   32768    5.433e16     1.000   7.02e5        12
#   65536    5.439e16     1.001   2.69e5         4.6
#   131072   5.330e16     0.981   1.07e5         1.8
#   262144   5.282e16     0.972   4.52e4         0.77
#   1048576  3.837e16     0.706   6.66e3         0.11
#
# The device rate is FLAT over a factor of eight in q2 while the host cost
# moves 16x, so "fastest" does not decide this and the load budget does
# (CONVENTIONS.md "Sizing a hunt", step 3: when two settings tie on
# throughput take the one that asks for less machine).  What the depth is
# chosen from is therefore the SURVIVOR RATE, and the target is set where
# two workers keep up with margin.
#
# It cannot be a constant, because the survivor rate per candidate at a
# fixed q2 moves an order of magnitude between filters -- 4.8e-8 at n = 15
# and 1.3e-8 at n = 17, since w(q,n) = n for every q above the wheel and n
# is in the exponent.  A q2 tuned at one opening is 4x wrong at the next.
# So the campaign plans it: the smallest depth whose ANALYTIC survival is
# under the target.  At n = 15 that picks 131072 (0.981x, 1.8 cores) and at
# n = 17 it picks 32768, which is that filter's device peak (1.000x, 1.8
# cores) -- the same host load at both, which is the point.
SURV_TARGET = 5e-8
Q2_LADDER = tuple(1 << e for e in range(12, 25))


@_lru_cache(maxsize=None)
def plan_q2(n, fam, unit, wheel, target=SURV_TARGET, ladder=Q2_LADDER):
    """The smallest depth in `ladder` whose analytic survivors-per-candidate
    is at or under `target`; the deepest rung if none reaches it.

    Analytic, not measured: survival through the sieve is a deterministic
    product over the primes involved (OPTIMIZATION.md 2.6), and it matched
    the measured survivor rate to better than 2% at every opening here.
    """
    from lcml_reference import w_closed
    fam = family(fam)
    unit = int(unit)
    # w_closed, not len(killed_residues): they are equal for every q that
    # does not divide the unit (lcml_reference G2b proves the closed form
    # against both the residue count and direct divisibility, and G3 proves
    # the unit does not change the SIZE), and the closed form is a division
    # where the other is n modular inversions.  And primerange is walked
    # LAZILY, rung by rung -- materialising the primes to the top of the
    # ladder is 1.07 million of them, three seconds, on every engine build.
    wset = frozenset(int(q) for q in wheel)
    surv = 1.0
    prev = 1
    for d in ladder:
        if d <= prev:
            continue
        for q in primerange(prev + 1, d + 1):
            if unit % q and q not in wset:
                surv *= 1.0 - w_closed(q, n) / q
        prev = d
        if surv <= target:
            return d
    return ladder[-1]


# HOW LONG A PERIOD MAY BE AGAINST THE SEARCH IT IS PART OF.
#
# A period's candidates come out in (t, s, u, j) order, so the x line is
# contiguous only at a period boundary and a find is only known to be the
# LEAST once its period closes (CONVENTIONS.md "Two cursors").  A find
# therefore costs up to one period of over-sweep.  The wheel plan wants the
# longest period it can have -- a denser wheel IS a longer period -- so
# something has to say when that stops paying, and the honest answer is the
# length of the search: four periods to the modelled median keeps the
# over-sweep under a quarter of the hunt at the tightest filter.
#
# This is what square-ladders' v2 log rejected a wheel for and re-priced two
# terms later, when the same period had become 0.13% of the remaining hunt.
# It is a per-filter quantity for the same reason everything else here is.
CAMPAIGN_PERIOD_MARGIN = 4.0


@_lru_cache(maxsize=None)
def search_period_cap(n, fam, margin=CAMPAIGN_PERIOD_MARGIN):
    """The longest period (in x) a plan at filter n may have, or None.

    Derived from the odds model's median for that term, measured from the
    PUBLISHED frontier -- which is stable (it does not move as the campaign
    finds terms) and conservative (a find above the median raises the next
    term's floor and so its median, making a longer period MORE affordable,
    never less).  Cached, because a `quantile` is ~90 numerical integrals
    and the answer changes only with the filter (OPTIMIZATION.md 2.14).
    """
    import lcml_model as _model
    from lcml_reference import KNOWN
    fam = family(fam)
    front = KNOWN[fam][max(KNOWN[fam])]
    med = _model.quantile(fam, n, _model.floor_for(fam, n, front), 0.5)
    return None if med is None else med / float(margin)


def _wheel_primes(p1, p2, p3):
    """The wheel's prime SET from three levels, each an int bound or a list."""
    out = []
    lo = 1
    for lv in (p1, p2, p3):
        if lv is None:
            continue
        if isinstance(lv, int):
            out += [q for q in primerange(lo + 1, lv + 1)]
            lo = lv
        else:
            out += [int(q) for q in lv]
    return tuple(sorted(set(out)))


@_lru_cache(maxsize=None)
def _wheel_value(n, fam, unit, top=WHEEL_TOP):
    """[(q, keep(q))] for every prime the wheel could take, where
    keep(q) = (q - w(q,n))/q is the fraction of x that prime lets through."""
    from lcml_reference import w_closed
    unit = int(unit)
    return tuple((q, (q - w_closed(q, n)) / q)
                 for q in primerange(2, top + 1) if unit % q)


def _split_levels(qs, r1_max):
    """Partition the sorted primes `qs` into three CRT levels satisfying every
    bound the kernel's arithmetic rests on, or None.

    The levels are contiguous in the sorted subset -- that is what the CRT
    lifting builds -- so this is a search over two cut points.  It takes the
    split with the largest first level inside R1_MAX: the first level is one
    thread per residue, so a small R1 starves the launch's x dimension.
    """
    m = len(qs)
    best = None
    for i in range(1, m + 1):
        W1 = R1 = 1
        for q, k in qs[:i]:
            W1 *= q
            R1 *= q - int(round(q * (1 - k)))
        if W1 >= 1 << 32 or R1 > r1_max:
            break
        for j in range(i, m + 1):
            W2a = R2 = 1
            for q, k in qs[i:j]:
                W2a *= q
                R2 *= q - int(round(q * (1 - k)))
            if R2 > 65535 or W2a >= 1 << 32:
                break
            W2b = R3 = 1
            for q, k in qs[j:]:
                W2b *= q
                R3 *= q - int(round(q * (1 - k)))
            if R3 > 65535 or W2b >= 1 << 32:
                continue
            if W2a * W2b >= 1 << 32 or W1 * W2a * W2b >= 1 << 63:
                continue
            cand = (R1, -abs(R2 - R3))
            if best is None or cand > best[0]:
                best = (cand, i, j)
    if best is None:
        return None
    i, j = best[1], best[2]
    return (tuple(q for q, _ in qs[:i]), tuple(q for q, _ in qs[i:j]),
            tuple(q for q, _ in qs[j:]))


@_lru_cache(maxsize=None)
def wheel_plan(n, fam, unit, pv_min=PV_MIN, r1_max=R1_MAX, top=WHEEL_TOP,
               max_period=None):
    """([level 1], [level 2], [level 3]): the wheel at filter n of family F.

    THE WHEEL IS A SUBSET OF THE PRIMES, NOT A PREFIX OF THEM, and in this
    project that is worth between 1.2x and 1.8x.  Every prime in the wheel
    multiplies the PERIOD by q and the candidate density by
    keep(q) = (q - w(q,n))/q, and here those two are wildly out of step,
    because w(q,n) = floor(n/q^e) makes the small primes nearly blind.  At
    n = 17 the primes 11, 13 and 17 keep 0.909, 0.923 and 0.941 of the line
    -- they kill almost nothing -- while costing a factor of 2,431 in
    period; 47 and 53 keep 0.638 and 0.679 for a factor of 2,491.  A PREFIX
    wheel cannot make that trade: to reach 19 it must take 11, 13 and 17,
    and then the period bound stops it before 47.

    So the subset is chosen by VALUE DENSITY, -log(keep(q)) / log(q), taken
    greedily while the period still fits every bound.  Measured against the
    prefix wheel this replaced, in candidates per unit of line: 1.36x at
    n = 15, 1.20x at 16, 1.82x at 17, 1.72x at 18 and 19.

    The bounds, all enforced:
      * W1 < 2^32, W2 < 2^32, W1*W2 < 2^63 (the kernel's arithmetic);
      * R2, R3 <= 65535 (they ride gridDim.y and .z), R1 <= r1_max;
      * (pv_min + 1) W' + q2 < 2^63 (the Barrett tail's one conditional
        subtraction);
      * `max_period`, the caller's statement of how long a period may be
        against the search it is part of.  A find is only known to be the
        LEAST once its period closes, so it costs up to one period of
        over-sweep -- and at n = 15 the modelled median is only nine
        periods in, which is why that filter takes a shorter wheel than
        n = 17 does.
    """
    fam = family(fam)
    unit = int(unit)
    vals = _wheel_value(n, fam, unit, top)
    cap = (REDUCE_MAX - Q2_DEFAULT) // (int(pv_min) + 1)
    if max_period is not None:
        cap = min(cap, max(1, int(max_period) // unit))
    order = sorted(vals, key=lambda z: math.log(z[1]) / math.log(z[0]))
    best = None
    for k in range(1, len(order) + 1):
        sel = sorted(order[:k])
        W, dens = 1, 1.0
        for q, keep in sel:
            W *= q
            dens *= keep
        if W > cap:
            continue
        lv = _split_levels(sel, r1_max)
        if lv is None:
            continue
        if best is None or (dens, -W) < best[0]:
            best = ((dens, -W), lv)
    if best is None:
        raise ValueError(f"no admissible wheel at n = {n} of {fam} with unit "
                         f"{unit}: PV_MIN = {pv_min}, the 2^63 reduction "
                         f"bound and max_period = {max_period} leave nothing")
    return best[1]
TPB_DEFAULT = 128            # threads per block
# Independent Barrett chains in the queue tail.
UNROLL = 4
# Survivors buffered per launch.  The gate battery runs coarse wheels and
# shallow sieves where a launch of 2^30 candidates can keep hundreds of
# thousands; the engine RAISES on overflow rather than dropping, so this is
# a budget, not a bound.
HIT_CAP = 1 << 20
RES_MAX = 1 << 24            # refuse a one-level wheel table bigger than this
LIT_INLINE_Q = 64            # below this, a group's kill set is a u64 literal
# The budgets G14 checks the two group lists against: the window groups
# (single primes, so far under this) and the in-block round groups.
LIT_GROUP_MAX = 1 << 19
K2_GROUP_MAX = 1 << 14
# How much margin the shared queues carry over their ANALYTIC occupancy.
# Overflow is HARMLESS, not impossible -- a candidate that does not fit runs
# its tail on the spot -- so this is a tuning constant and G14 proves the
# fallback by forcing it.
#
# IT IS ALSO SPENDING BLOCKS PER SM, WHICH IS WHY IT CHOOSES ITSELF.  The
# queues are two thirds of this kernel's shared memory, shared memory is what
# caps its occupancy, and a padding ablation (a dummy shared array, nothing
# else changed) measured the rate tracking blocks per SM almost linearly:
# 5 / 4 / 3 / 2 blocks read 1.000 / 0.920 / 0.820 / 0.589.  So a margin that
# costs a block costs about 8%, and at n = 16 of A078502 the inherited 6.0
# did exactly that -- 20,044 bytes and 4 blocks against 18,508 and 5, worth
# a measured 1.073x.
#
# `_pick_sigma` therefore takes the LARGEST margin in QCAP_SIGMA_LADDER that
# still reaches the best blocks-per-SM any of them reaches.  Never smaller
# than it has to be: 1.5 at n = 16 reads 0.825x of 3.0, because then the
# queues really do overflow and the in-block fallback becomes the rule.
# This is OPTIMIZATION.md 2.11 once more -- a budget that binds on one axis
# was silently setting a shape parameter -- caught this time on purpose.
QCAP_SIGMA = 6.0
QCAP_SIGMA_LADDER = (6.0, 5.0, 4.0, 3.0, 2.5)
# Shared memory the device gives an SM, and what the driver reserves per
# block on top of a kernel's static request.  Queried where possible.
SMEM_PER_SM_DEFAULT = 100 << 10
SMEM_BLOCK_RESERVE = 1 << 10
# The analytic footprint below is within ~70 bytes of what the compiler
# reports (checked at four filters); this is the slack that keeps a
# borderline case on the safe side.
SMEM_SLACK = 256
# THE SHARED/L1 CARVEOUT OF THE SIEVE KERNEL, PINNED at 100% shared.  v2
# pinned 50% because the v3 kernel's group tables lived in L1 and the
# driver's occupancy heuristic moved the split under them (0.2-0.3x).  The
# v4 kernel's tables live in shared memory and it measured indifferent to
# the split (0.99-1.04x at 25, 50, 75 and 100; OPTIMIZATION_LOG.md v4) --
# but at 50% a 128-period block of 14-15 KB fits the 64 KB only three or
# four times (the driver reserves 1 KB per block), and at 100% the
# register file sets the occupancy (5-7 blocks).  Stated, not inherited.
# The tail-round kernels are not pinned and keep the driver's choice.
CARVEOUT_PCT = 100
# Ceiling on the GLOBAL tail queue, in candidates; overflow takes the
# in-block fallback, so it costs correctness nothing -- but it costs
# 0.67x when it is the rule rather than the exception: at c = 14 on the
# 59-wheel a launch's round-2 survivors are 1.6e8, over the v1 cap of 2^26,
# and the fallback serialises a 6,500-prime tail inside the sieve block.
# 2^28 lets the analytic size win everywhere (2 x 1.3 GB of queue at that
# opening, a tenth of that from c = 15 on).
Q3_MAX = 1 << 28
# THE TAIL RUNS AS COMPACTION ROUNDS (OPTIMIZATION.md 2.2).  Its items are
# rare-and-deep, so the tail sweeps its queue in rounds over prime ranges
# chosen from the survival curve: every round starts with every lane
# alive, and a lane that dies waits at most to the end of its round.
# TAIL_ROUND_DROP is the survival a round is allowed to lose before the
# survivors are compacted into the next queue.  Each round is one kernel
# launch over a global queue with one item per thread and ONE global
# atomic per block for the push.
# 0.7, not the linear ladders' 0.5.  Swept paired: at n = 15 of A078502
# 0.9/0.8/0.7/0.6/0.5 read 1.000/1.034/1.041/1.037/1.027 and at n = 17 of
# A074200 1.000/1.070/1.079/1.089/1.079 -- a broad plateau over 0.6-0.8 whose
# far side (0.9, one round for the whole tail) is a real loss.  Against the
# inherited 0.5 it is 1.014x at n = 15 and 1.000x at n = 17: small, and taken
# because it is free.
TAIL_ROUND_DROP = 0.7
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
# exceeds them pays a synchronous read.  A c = 14 launch on the 59-wheel
# returns ~15,000 (2.2% of wall in a synchronous read at 2^13).
PRE_COPY = 1 << 15

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
    # A prime of the unit is dropped from the modulus below, which is only
    # sound if that prime is FORCED at this filter -- otherwise the wheel
    # covers a thinner line than it claims and no parity gate against an
    # engine using the same wheel could see it.  GpuEngine checks its own
    # unit, but `wheel` is called directly by the gates and by the A/B
    # harnesses, and the sporadic forcing here (unit 34 at n = 16, 2 either
    # side) makes an off-by-one filter the easiest mistake in the project.
    assert_unit(n, fam, unit)
    # `p1` may be an explicit SEQUENCE of primes rather than an upper bound:
    # the wheel here is a SUBSET of the primes, not a prefix (wheel_plan says
    # why), so a level is a list.  An int keeps the old meaning, which is what
    # the gates and the x-space benchmark shapes use.
    qs = ([q for q in p1 if unit % q] if not isinstance(p1, int)
          else [q for q in primerange(lo + 1, p1 + 1) if unit % q])
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


def _table_bytes(Q, reps):
    """Bytes a group of modulus Q occupies: reps*Q bits, or none inline."""
    return 0 if Q < LIT_INLINE_Q else ((reps * Q + 31) // 32) * 4


def lit_groups(primes, nlit, budget=LIT_GROUP_MAX, start=0, cap_bytes=None,
               reps=1):
    """Group primes[start:nlit] into CRT-combined test groups.

    "Killed by 59 or by 61" is a function of k mod (59*61) alone, so a
    group of primes costs ONE reduction and ONE bitmap lookup instead of
    one of each per prime.  Groups are grown greedily while the product
    stays under `budget` -- and, with `cap_bytes`, while the tables of
    the groups so far stay under it: a prime that would grow the current
    group's table past what is left starts a new group instead.  That is
    what lets the modulus budget be large enough for the first triple
    without a second, far bigger, triple forming behind it.
    """
    groups, cur, prod, total = [], [], 1, 0
    for i in range(start, nlit):
        q = primes[i]
        if cur and (prod * q > budget
                    or (cap_bytes is not None
                        and total - _table_bytes(prod, reps)
                        + _table_bytes(prod * q, reps) > cap_bytes)):
            groups.append(cur)
            cur, prod = [], 1
        total += _table_bytes(prod * q, reps) - _table_bytes(prod, reps)
        cur.append(i)
        prod *= q
    if cur:
        groups.append(cur)
    return groups


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
            fold = ("" if Q < LIT_INLINE_Q else
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
        single = hoist is not None
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
        elif hoist is not None:
            # the table's word offset folds into the load's immediate, so
            # the residue is shifted and masked as it is: one instruction
            # fewer per group per candidate (1.02x, OPTIMIZATION_LOG.md v2)
            assert off_bits % 32 == 0
            lines.append(head + f"kill |= ({table}[{off_bits // 32}u + "
                                f"(r >> 5)] >> (r & 31)) & 1u; }}")
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


def _occupancy(kernel, tpb):
    """What a compiled sieve kernel would reach on this device: registers,
    static shared bytes, and the resident blocks per SM at `tpb`."""
    import cupy as cp
    a = kernel.attributes
    try:
        blocks = int(cp.cuda.driver.occupancyMaxActiveBlocksPerMultiprocessor(
            kernel.kernel.ptr, int(tpb), 0))
    except Exception:                       # noqa: BLE001 -- an old CuPy
        blocks = -1
    return {"num_regs": int(a.get("num_regs", -1)),
            "smem_bytes": int(a.get("shared_size_bytes", -1)),
            "local_bytes": int(a.get("local_size_bytes", -1)),
            "blocks_per_sm": blocks}


def _set_carveout(kernel, pct):
    """Pin the kernel's preferred shared/L1 carveout (percent shared)."""
    import cupy as cp
    cp.cuda.driver.funcSetAttribute(
        kernel.kernel.ptr,
        cp.cuda.driver.CU_FUNC_ATTRIBUTE_PREFERRED_SHARED_MEMORY_CARVEOUT,
        int(pct))


def _qcap(tile, surv, sigma=QCAP_SIGMA):
    """Queue capacity from the ANALYTIC survival, plus sigma of margin."""
    import math
    mean = tile * surv
    sd = math.sqrt(max(tile * surv * (1.0 - surv), 0.0))
    want = int(math.ceil(mean + sigma * sd))
    want = min(max(want, 32), tile)
    return ((want + 31) // 32) * 32


# ---- v4: the period-window engine -----------------------------------------
#
# THE INVERSION (OPTIMIZATION.md 2.1).  v1-v3 tested candidates one at a
# time: per candidate, per prefix group, a reduction and a table bit.  A
# candidate is `(t, s, u)` in period j -- k' = Wp*j + off(t, s, u) -- and
# for a FIXED residue the candidates of consecutive periods form an
# arithmetic progression modulo every sieve prime q (step Wp mod q, which
# is invertible: q is above the wheel and not in the unit).  So "which of
# the next P periods does q kill" is a function of (off mod q) alone, and
# it is a P-bit WINDOW into a periodic pattern:
#
#     with  D = Wp mod q,  Dinv = D^-1 mod q,  r'' = off * Dinv mod q,
#     q | (off + j*Wp) - kr   <=>   (r'' + j) mod q  in  C_q = { kr*Dinv }
#
# so bit j of the window at position r'' of the pattern "bit p set iff
# p mod q in C_q" says whether period j0 + j is killed by q.  One window is
# two 64-bit loads and two funnel shifts for 64 candidates, against ~12
# instructions PER CANDIDATE per group before; and r'' itself is linear in
# the decomposition off = (r1_t + W1*A_t) - W1*D_s + Wp*bw, so it is
# x0[t] + ne[s] + bw with x0 a table per first-level residue (launch-
# independent: the launch base folds into ne as j0 mod q, because
# Wp*Dinv == 1) and ne per second-level residue computed once per block.
#
# The survivors of the window sieve (~0.5% at c = 15) are extracted bit by
# bit into the block's shared queue as (s, tid, j) and take the per-
# candidate route from there: in-block COMPACTION ROUNDS over single-prime
# Barrett tests (the same generated tests round 2 always ran, now several
# rounds deep, because the global tail's cost per entrant is the thing the
# whole design has to keep away from), then the global tail rounds,
# unchanged.  Nothing in the arithmetic of a kill changed: the same
# killed_residues, the same Barrett tail, the same (k, off) split with the
# base folded on the host.  G9 pins the stream against the CPU engine and
# G19 pinned it bit for bit against the v3 engine on the production
# wheels before v3 was retired.

# Periods per segment: the WIDTH of the window, in bits, a multiple of 32.
# It is also the COVERAGE UNIT -- the launcher's cursor advances a segment at
# a time and a find over-sweeps at most one.
#
# 192 HERE, NOT 128, AND THE TWO CONSTANTS MOVED TOGETHER.  The linear
# ladders shipped 64 below c = 16 and 128 above.  Swept at this project's
# openings that costs 1.22x at n = 15 (64 -> 128), and 128 was not the end
# of it: 192 measured 0.14x, which looked like a hard cliff and is in fact a
# SHARED QUEUE OVERFLOW.  A wider window puts more live words in shared
# memory, QUEUE_BYTES_MAX capped what was left for the queues, q1cap fell
# 1280 -> 768, and every block took the in-block fallback -- the documented
# 0.67x failure, worth 7x when it is the rule rather than the exception.
# Raising the queue budget to 20 KB inverts the verdict: 192 is then 1.066x
# over 128 and 256 is 0.992x.  That is OPTIMIZATION.md 2.11 exactly -- a
# budget that binds on one axis was silently setting a shape parameter --
# and it is why the two constants are documented next to each other.
# Measured paired at n = 15, A078502, three interleaved rounds:
#   pb    64: 4.170e16 x/s    128: 5.037e16    192: 5.371e16    256: 4.996e16
# 1.288x over the inherited (64, 12 KB) pair.
PB_DEFAULT = 192
PB_BY_C = {}


def pb_for(c):
    return PB_BY_C.get(int(c), PB_DEFAULT)


# The live words of this many second-level residues are buffered before an
# extraction pass; the buffer is EXTRACT_EVERY * NW * TPB words of shared.
# Keyed by the window's word count: at NW = 2 four residues (16 KB of
# buffer would cost a block per SM), at NW = 4 one (measured, same log).
EXTRACT_EVERY_BY_NW = {2: 4, 4: 1}
# Window-sieve depth and the in-block rounds, as SURVIVAL FRACTIONS.  The
# window sieve costs ~10 instructions per prime per 64 candidates whatever
# the prime kills, and a per-candidate single-prime test ~15 per entrant,
# so the crossover is where 15 * survival = 10 / 64: about 1%.  The
# in-block rounds then halve the survivors per round (R2_DROP) down to
# K2_SURV4, where the global tail takes over.
BIT_SURV = 0.007
K2_SURV4 = 0.0003
R2_DROP = 0.5
# Second-level residues per block in v4 (one first-level residue per thread).
SPB4 = 8
# Candidate budget per launch: sets the first-level chunk and the third-level
# residues per launch, and with them how much of the tail rounds' fixed
# latency each launch has to amortise (OPTIMIZATION.md 2.4).
#
# 2^37, not the linear ladders' 2^35.  Swept paired at three openings:
#
#   cand/launch   2^35    2^36    2^37    2^38    2^40    2^41
#   n = 15        1.000   1.024   1.034   1.042   0.650   0.350
#   n = 17        1.000     --    1.082   1.077     --      --
#   n = 16        1.000     --    1.048   1.053     --      --
#
# monotone to 2^38 and then a cliff: past there the analytic size of the
# GLOBAL tail queue passes Q3_MAX and every launch takes the in-block
# fallback (the documented 0.67x, worth 0.35x when it is the rule).  2^37
# and 2^38 tie inside the noise at every opening, so this takes the one that
# asks for less machine: 500 MB of device buffers against 1 GB.
CAND_PER_LAUNCH4 = 1 << 37
# Groups in the window sieve are SINGLE primes by default: a pair's pattern
# table is 1-9 KB and its gather touches every sector, where a single's
# fits in two to five sectors and costs the L1 one wavefront.
BIT_GROUP_MAX = 1
# The x0 table holds (r1 + W1*A) * Dinv mod Q per first-level residue per
# group; u16 while every group modulus fits.
X0_DTYPE_MAX16 = 1 << 16
# The shared queues of one block may total this many bytes (see __init__).
# 20 KB, not the linear ladders' 12: at PB_DEFAULT = 192 the window's live
# words leave 12 KB too little, every block overflows into the in-block
# fallback and the engine runs at 0.14x.  Swept at n = 15: 12 KB 7.07e15,
# 20 KB 5.40e16, 28 KB 5.36e16 -- flat once it fits, so this is sized to fit
# and no larger (shared memory is what sets blocks per SM).
QUEUE_BYTES_MAX = 20 << 10
# The v4 kernel's occupancy floor for G18.  The window kernel compiles to
# 80-96 registers and 10-15 KB of shared memory, 5-6 blocks per SM, and
# that IS its optimum: forcing 8 blocks with launch bounds spilled 72 bytes
# to local memory and ran 0.93x (OPTIMIZATION_LOG.md v4).  What G18 must
# catch is a configuration that falls off that plateau -- 3 blocks, or a
# spill -- not one that fails to reach a v3 number.
# Raised from 4 to 5 once the queue margin began choosing itself: every
# campaign configuration now reaches 5 blocks per SM (n = 19 reaches 7,
# register-limited), and the padding ablation prices a lost block at about
# 8%, so a regression to 4 is worth catching.
OCC_MIN_BLOCKS4 = 5
# The window tables of one block (shared memory), bytes.
PAT_BYTES_MAX = 16 << 10
# Largest modulus of a CRT-combined group in the in-block rounds (1: single
# primes, doubled tables of 2q bits).
K2_GROUP_MAX4 = 1
# Items per thread per iteration of an in-block round: independent test
# chains the compiler overlaps.  The rounds were latency-bound at 1 (a
# round is ~450 items for 128 threads, each a dependent chain of a shared
# load, a global load and a dozen Barrett tests), and hid behind nothing.
ROUND_ILP = 1
# The window pattern tables live in SHARED memory (copied once per block,
# 4-7 KB): a shared load has a fixed ~30-clock latency where an L1 gather
# does not, and the sieve is bound by the latency of its loads with a
# handful in flight per warp, not by issue.
PAT_SHARED = True
# The per-thread x0 residues (one per window group) as a register array or
# in shared memory: NG registers per thread against NG*TPB*2 bytes of
# shared per block.
X0_SHARED = False


def window_patterns(n, fam, primes, groups, Wp, nw, unit=1):
    """(u64 table, offsets, Dinv per group) for the window sieve.

    For group g with modulus Q = prod(q in g): pattern bit p is set iff
    (p mod q) in C_q for some q in g, C_q = { kr * Dinv_Q mod q : kr in
    killed_residues(q) } with Dinv_Q = (Wp mod Q)^-1 mod Q.  Stored as
    32-bit words -- word w holds bits [32w, 32w + 32) -- so a window of NW
    words at bit position r is words r >> 5 .. (r >> 5) + NW, each pair
    funnel-shifted by r & 31, for r in [0, 2Q) (the residue arrives
    unreduced from x0 + ne + bw, each below Q).  32-bit words, not 64: a
    warp-wide 64-bit shared load costs two data-path cycles whatever the
    addresses, and the window sieve is bound by that pipe (OPTIMIZATION_LOG.md
    v4).  G14 checks every bit of every table against killed_residues.
    """
    fam = family(fam)
    tabs, offs, dinvs = [], [], []
    off = 0
    for g in groups:
        qs = [primes[i] for i in g]
        Q = 1
        for q in qs:
            Q *= q
        dinv = pow(int(Wp) % Q, -1, Q)
        nbits = 2 * Q + 32 * nw + 96
        nwords = (nbits + 31) // 32 + 1
        idx = np.arange(nwords * 32, dtype=np.int64)
        bits = np.zeros(idx.size, dtype=bool)
        for q in qs:
            c = np.array(sorted({(kr * dinv) % q
                                 for kr in killed_residues(q, n, fam, unit)}),
                         dtype=np.int64)
            bits |= np.isin(idx % q, c)
        words = np.packbits(bits, bitorder="little").view(np.uint32)
        tabs.append(words)
        offs.append(off)
        dinvs.append(dinv)
        off += int(words.size)
    table = np.concatenate(tabs) if tabs else np.zeros(1, dtype=np.uint32)
    return table, offs, dinvs


_SRC4 = r"""
#define W1C  %(w1)du
#define W2C  %(w2)du
#define WC   %(w)dULL
#define TWOLEVEL %(two)d
#define THREELEVEL %(three)d
#define NU   %(nu)d
#define SPB  %(spb)d
#define TPB  %(tpb)d
#define PB   %(pb)d
#define PV   %(pv)d
#define NW   %(nw)d
#define LOGP %(logp)d
#define LITN %(lit)d
#define K2   %(k2)d
#define NG   %(ng)d
#define NG4  %(ng4)d
#define UNROLL %(unroll)d
#define RILP %(rilp)d
#define PATSH %(patsh)d
#define X0SH %(x0sh)d
#define NPAT %(npat)d
#define XE %(xe)d
%(qcaps)s
#define LOGTPB %(logtpb)d
#define LOGSPB %(logspb)d
#define QTYPE %(qtype)s
#define X0TYPE %(x0type)s
#define MASK_BITS %(mask_bits)d
#define MASK_WORDS (MASK_BITS / 32)
#define NRES %(nres)d
#define TTPB %(ttpb)d

/* WHAT THE QUEUES HOLD: the candidate's INDEX in the block -- (ss, tid)
   and the period j inside the segment -- packed as ((ss*TPB + tid) << LOGP)
   | j.  Shared memory is what this kernel is short of. */
/* THE QUEUE ENTRY IS THREE BYTES, not four.  It is (ss*TPB + tid) << LOGP
   | j -- 18 bits at spb = 8, tpb = 128, pb = 192 -- so a u32 held it and the
   queues were two thirds of this kernel's shared memory.  Split into a u16
   index and a u8 period it is three bytes, which frees ~3.1 KB: the 6th
   block per SM, priced at about a twelfth by the padding ablation
   (OPTIMIZATION_LOG.md round 4).  The PACKED form is rebuilt on read, so
   off_of and every round test are untouched. */
#define QIDX(SS) ((unsigned short)(((SS) * TPB) + threadIdx.x))
#define QGET(QI, QJ, P) ((((unsigned int)(QI)[P]) << LOGP) \
                         | (unsigned int)(QJ)[P])

/* One test against prime IDX (unchanged from v3): the uint4 record
   (magic_lo, magic_hi, q, base mod q), the prime's MASK_BITS-bit mask and,
   rarely, its residue list.  ONE conditional subtraction is exact below
   2^63 (the reduced quantity is the offset within the launch, bounded by
   the engine to keep (segments*PB + 1)*Wp + q2 under it). */
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

#define M_OF(A, D) (((A) >= (D)) ? ((A) - (D)) : ((A) - (D) + W2C))

/* ONE shared atomic per WARP per push, not one per survivor: a same-address
   shared atomic from k active lanes serialises k-deep, and the extraction
   below pushes from ~half the lanes of every warp on every step.  Each
   lane brings its count; the warp prefix-sums it (five shuffles), lane 0
   reserves the range, and every lane writes at base + its prefix.  All 32
   lanes must be present, so callers keep dead lanes in the loop with a
   count of zero rather than branching them out. */
__device__ __forceinline__ int warp_reserve(int* counter, const int cnt,
                                            int* my_base)
{
    const int lane = threadIdx.x & 31;
    int pre = cnt;
#pragma unroll
    for (int d = 1; d < 32; d <<= 1) {
        const int v = __shfl_up_sync(0xFFFFFFFFu, pre, d);
        if (lane >= d) pre += v;
    }
    const int total = __shfl_sync(0xFFFFFFFFu, pre, 31);
    int base = 0;
    if (lane == 0 && total > 0) base = atomicAdd(counter, total);
    base = __shfl_sync(0xFFFFFFFFu, base, 0);
    *my_base = base + pre - cnt;
    return total;
}

/* Rebuild a candidate from its queue entry.  The thread that dequeues is
   not the thread that queued, so D lives in shared. */
__device__ __forceinline__ unsigned long long off_of(
        const unsigned int qi, const unsigned long long base, const int t_lo,
        const uint2* __restrict__ res1x, const unsigned int* d2)
{
    /* LOGP bits, not PB - 1: the queue entry packs the period index into
       the low LOGP bits (QIDX shifts the residue index left by LOGP), and
       PB - 1 is only the right mask when PB is a POWER OF TWO.  At PB = 192
       it is 0b10111111, which clears bit 6 of every period index above 63 --
       the candidate is rebuilt at the wrong period, survives, and the stream
       gains entries.  The linear ladders never saw it because 32/64/128 were
       the only widths they ran; here the measured optimum is 192.  G9 caught
       it as +18 survivors in 2e6 of line at n = 9. */
    const unsigned int j = qi & ((1u << LOGP) - 1u);
    const unsigned int rest = qi >> LOGP;
    const int tid = rest & (TPB - 1);
    const uint2 e1 = res1x[t_lo + blockIdx.y * TPB + tid];
    unsigned long long off = base + (unsigned long long)e1.x
                           + (unsigned long long)j * WC;
#if TWOLEVEL
    const int ss = rest >> LOGTPB;
    off += (unsigned long long)W1C * M_OF(e1.y, d2[ss]);
#endif
    return off;
}

extern "C" __global__ void sieve(
        const int R1, const int R2, const int np_,
        const unsigned int* __restrict__ pmask,
        const uint4* __restrict__ pres,
        unsigned long long* out, int* nout, const int cap,
        unsigned long long* q3, int* n3, const int q3cap,
        const uint4* __restrict__ pk,
        const uint2* __restrict__ res1x,
        const X0TYPE* __restrict__ x0tab,
        const unsigned int* __restrict__ res2c,
        const unsigned int* __restrict__ res2d, const int u0,
        const int t_lo, const int nper,
        const unsigned int* __restrict__ jmod,
        const unsigned int* __restrict__ gpat,
        const unsigned int* __restrict__ g2bits%(gparams)s)
{
%(qdecl)s
    __shared__ int q3b;
    __shared__ unsigned int d2[SPB];
    __shared__ __align__(16) unsigned int ne[SPB][NG4];
    __shared__ unsigned int sal[XE * NW * TPB];
#if X0SH
    __shared__ X0TYPE sx0[NG * TPB];
#endif
#if PATSH
    __shared__ unsigned int spat[NPAT];
    for (int i = threadIdx.x; i < NPAT; i += TPB) spat[i] = gpat[i];
#define pat spat
#else
#define pat gpat
#endif
    if (threadIdx.x == 0) { %(qzero)s }

    /* gridDim.z = segment * NU + u.  The segment's first period is
       sg * PV after the launch base (PV <= PB live periods per window);
       `nper` periods are live in the launch, so the last segment may be
       partial. */
    const int sg = blockIdx.z / NU;
    const unsigned long long base = WC * (unsigned long long)(sg * PV);
    const int nv = min(PV, nper - sg * PV);
    /* s-blocks ride gridDim.x and t-blocks gridDim.y: consecutive blocks
       then share their first-level chunk, so an SM's successive blocks find
       the chunk's x0 rows and res1x in its L1 */
    const int s0 = blockIdx.x * SPB;
    const int tb = blockIdx.y;
    (void)s0;
#if THREELEVEL
    const unsigned int cb = res2d[u0 + (int)(blockIdx.z %% NU)];
#endif
    if ((int)threadIdx.x < SPB) {
        const int ss = threadIdx.x;
        unsigned int dcur = 0u;
#if TWOLEVEL
        unsigned int c = res2c[min(s0 + ss, R2 - 1)];
#if THREELEVEL
        const unsigned long long cc = (unsigned long long)c + cb;
        c = (unsigned int)(cc >= (unsigned long long)W2C ? cc - W2C : cc);
#endif
        dcur = W2C - c;
#endif
        d2[ss] = dcur;
        const unsigned int shift = (unsigned int)sg * PV;
%(blockpre)s
    }
    __syncthreads();
#if TWOLEVEL
    const int nss = min(SPB, R2 - s0);
#else
    const int nss = 1;
#endif
    const int t = t_lo + tb * TPB + (int)threadIdx.x;
    /* a lane past R1 (the last block of a chunk) stays in the loop with an
       empty window, so the warp-wide push sees all 32 lanes */
    const bool live = t < R1;
    {
        const int tt = live ? t : R1 - 1;
        const uint2 e1 = res1x[tt];
#if X0SH
#pragma unroll
        for (int g = 0; g < NG; ++g) sx0[g * TPB + threadIdx.x] = x0tab[g * R1 + tt];
#define X0(G) ((unsigned int)sx0[(G) * TPB + threadIdx.x])
#else
        unsigned int x0[NG];
#pragma unroll
        for (int g = 0; g < NG; ++g) x0[g] = x0tab[g * R1 + tt];
#define X0(G) x0[G]
#endif
        for (int s1 = 0; s1 < nss; s1 += XE) {
        const int s2 = min(s1 + XE, nss);
        for (int ss = s1; ss < s2; ++ss) {
            const unsigned int dd = d2[ss];
            const unsigned int bw = (e1.y < dd) ? 1u : 0u;
            unsigned int acc[NW];
#pragma unroll
            for (int i = 0; i < NW; ++i) acc[i] = 0u;
%(groups)s
            /* the survivors: the live words go to shared memory and are
               extracted AFTER the sieve loop.  A data-dependent loop here
               cost 4x (OPTIMIZATION_LOG.md v4): it stopped the compiler
               overlapping one residue's loads with the next's. */
#pragma unroll
            for (int i = 0; i < NW; ++i) {
                const int lo = nv - 32 * i;
                const unsigned int vm = lo >= 32 ? 0xFFFFFFFFu
                                     : (lo <= 0 ? 0u : ((1u << lo) - 1u));
                sal[((ss - s1) * NW + i) * TPB + threadIdx.x] = live ? (~acc[i] & vm) : 0u;
            }
        }
        /* phase 2: extraction.  ONE warp-wide reservation for the whole
           block of XE residues: the reservation is a shuffle chain and a
           shared atomic, ~300 clocks of dependent latency, and doing it per
           word was most of the kernel's stall time (OPTIMIZATION_LOG.md v4). */
        int cnt = 0;
        for (int ss = s1; ss < s2; ++ss)
#pragma unroll
            for (int i = 0; i < NW; ++i)
                cnt += __popc(sal[((ss - s1) * NW + i) * TPB + threadIdx.x]);
        int p;
        const int total = warp_reserve(&qn0, cnt, &p);
        if (total == 0) continue;
        const bool fits = (p + cnt <= Q0CAP);
        for (int ss = s1; ss < s2; ++ss) {
            const unsigned int dd = d2[ss];
#pragma unroll
            for (int i = 0; i < NW; ++i) {
                unsigned int a = sal[((ss - s1) * NW + i) * TPB + threadIdx.x];
                /* the hot loop: the fallback for a full queue is rare and
                   lives outside it (1.10x, OPTIMIZATION_LOG.md v4) */
                const unsigned short qb = QIDX(ss);
                if (fits) {
                    while (a) { qi0[p] = qb;
                                qj0[p] = (unsigned char)(32u * i + __ffs(a) - 1);
                                ++p; a &= a - 1u; }
                    continue;
                }
                while (a) {
                    const int b = __ffs(a) - 1;
                    a &= a - 1u;
                    const unsigned int j = 32u * i + b;
                    if (p < Q0CAP) { qi0[p] = QIDX(ss);
                                     qj0[p] = (unsigned char)j; }
                    else {
                        unsigned long long off = base + e1.x
                                               + (unsigned long long)j * WC;
#if TWOLEVEL
                        off += (unsigned long long)W1C * M_OF(e1.y, dd);
#endif
                        if (tail_survives(off, np_, LITN, pk, pmask, pres))
                            EMIT(off)
                    }
                    ++p;
                }
            }
        }
        }
    }
    __syncthreads();
    const int nq0 = min(qn0, Q0CAP);

    /* The in-block compaction rounds: single-prime Barrett tests over the
       previous round's queue, each round packing its survivors into the
       next.  Generated per configuration. */
%(rounds2)s
    if (threadIdx.x == 0) q3b = (nqR > 0) ? atomicAdd(n3, nqR) : 0;
    __syncthreads();
    for (int idx = threadIdx.x; idx < nqR; idx += TPB) {
        const unsigned long long off = off_of(
            QGET(qiR, qjR, idx), base, t_lo, res1x, d2);
        const int p = q3b + idx;
        if (p < q3cap) q3[p] = off;
        else if (tail_survives(off, np_, K2, pk, pmask, pres)) EMIT(off)
    }
}
%(tailrounds)s
"""


class GpuEngine:
    """Wheel-generated candidates; the sieve primes below the bit-sieve depth
    tested 64 periods at a time through window tables, the rest per
    candidate in compaction rounds (v4)."""

    def __init__(self, n, fam, p1=None, p2=None, p3=None,
                 q2=None, tpb=TPB_DEFAULT, cpt=None, spb=None,
                 jpt=None, lit=None, k2=None, qcap_sigma=QCAP_SIGMA,
                 nu=None, unit=1, pb=None, tchunk=None, bit_group_max=None):
        import cupy as cp
        self.cp = cp
        self.n = int(n)
        self.fam = family(fam)
        self.s = sign(self.fam)
        self.unit = assert_unit(self.n, self.fam, unit)
        if spb is None:
            spb = SPB4
        self.nforms = nforms(self.fam, self.n)
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
        # THE DEFAULT IS THE PLANNED WHEEL, AT THIS FILTER AND THIS UNIT
        # (CLAUDE.md 5g).  A caller that names p1 gets exactly what it named
        # -- the gates do, and so does every A/B -- but `GpuEngine(n, fam,
        # unit=u)` must be the fastest correct engine for that opening, not
        # a wheel that happened to suit a different one.  The unit alone
        # changes the answer: 47 fits under the 2^63 reduction bound at
        # n = 16 (unit 34) and does not at n = 15 (unit 2).
        if p1 is None:
            p1, p2, p3 = wheel_plan(
                self.n, fam, self.unit,
                max_period=search_period_cap(self.n, fam))
        # ... and so is the sieve depth, from the survivor rate the host can
        # absorb.  Planned AFTER the wheel, because what the sieve has left
        # to kill is what the wheel did not -- and the wheel is a SUBSET of
        # the primes, so "what it did not" is a set difference and not a
        # threshold.
        if q2 is None:
            q2 = plan_q2(self.n, fam, self.unit, _wheel_primes(p1, p2, p3))
        self.p1, self.p2, self.p3 = p1, p2, p3
        self.q2, self.tpb = q2, tpb
        self.pb = int(pb if pb is not None else pb_for(self.nforms))
        if self.pb % 32 or self.pb < 32 or self.pb > 256:
            raise ValueError(f"pb = {self.pb} must be a multiple of 32 in "
                             f"[32, 256]: the window is NW 32-bit words")
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
        self.W = self.unit * self.Wp
        # THE PERIODS A SEGMENT HOLDS, PV <= PB.  The Barrett tail reduces
        # off + j*W' for j below the segment's live periods, and one
        # conditional subtraction is exact only below 2^63, so
        # (PV + 1) W' + q2 < 2^63 bounds PV: 128 on the unit wheel
        # (W' = 6.5e16), 13 on the k-space wheel to 47 (W' = 6.2e17) the
        # gates run.  Bits past PV in the window are masked off; the word
        # count follows PV, so a wheel that admits few periods gets a
        # 32-bit window rather than an idle 128-bit one.
        maxp = (REDUCE_MAX - self.q2) // self.Wp - 1
        if maxp < 1:
            raise ValueError(
                f"one wheel period is W' = {self.Wp}, and 2 W' + q2 is not "
                f"below 2^63: the kernel's single conditional subtraction is "
                f"only exact there, so this wheel needs a new reduction "
                f"(CONVENTIONS.md numeric hygiene)")
        self.pv = int(min(self.pb, maxp))
        if pb is None:
            self.pb = max(32, ((self.pv + 31) // 32) * 32)
        self.nw = self.pb // 32
        self.logp = (self.pb - 1).bit_length()

        w2 = np.uint64(self.W2)
        r1u = res1.astype(np.uint64)
        res1x = np.empty((self.R1, 2), dtype=np.uint32)
        res1x[:, 0] = r1u.astype(np.uint32)
        if self.R2 > 1:
            a = (r1u % w2) * np.uint64(self.inv) % w2
            A = (w2 - a) % w2
            res1x[:, 1] = A.astype(np.uint32)
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
            A = np.zeros(self.R1, dtype=np.uint64)
            res1x[:, 1] = 0
            self.d_res2c = cp.zeros(1, dtype=np.uint32)
            self.d_res2d = cp.zeros(1, dtype=np.uint32)
        self.d_res1x = cp.asarray(res1x.ravel())

        # THE SIEVE PRIMES ARE THE COMPLEMENT, not a tail.  The wheel is a
        # SUBSET of the primes (wheel_plan), so a prime it declined -- 11, 13
        # and 17 at n = 17, which kill under a tenth of the line each -- is
        # sieved here instead.  Taking "everything above the wheel's largest
        # prime" would silently drop them and thin the line.
        _wset = set(int(q) for q in _wheel_primes(p1, p2, p3))
        self.wheel_set = tuple(sorted(_wset))
        self.primes = [q for q in primerange(2, q2 + 1)
                       if self.unit % q and q not in _wset]
        if not self.primes:
            raise ValueError("no sieve primes above the wheel")
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

        self.lit_target, self.k2_target = BIT_SURV, K2_SURV4
        self.lit = (depth_for(self.lit_target) if lit is None
                    else min(lit, len(self.primes)))
        self.k2 = (max(self.lit, depth_for(self.k2_target)) if k2 is None
                   else min(max(k2, self.lit), len(self.primes)))
        # the window-sieve groups: single primes unless told otherwise
        bgm = BIT_GROUP_MAX if bit_group_max is None else int(bit_group_max)
        self.groups = lit_groups(self.primes, self.lit, budget=max(bgm, 1))
        # round 2's groups (per candidate): single primes, doubled tables
        self.groups2 = lit_groups(self.primes, self.k2, budget=K2_GROUP_MAX4,
                                  start=self.lit)
        # the in-block rounds: a split wherever survival has halved since
        # the round began (R2_DROP), no group straddling a round
        splits = [0]
        if self.groups2:
            start = self.surv[self.lit]
            for gi, g in enumerate(self.groups2):
                if self.surv[g[-1] + 1] <= start * R2_DROP and \
                        gi + 1 < len(self.groups2):
                    splits.append(gi + 1)
                    start = self.surv[g[-1] + 1]
        splits.append(len(self.groups2))
        self.rounds2 = [self.groups2[a:b] for a, b in zip(splits, splits[1:])
                        if b > a]
        self.bounds2 = [self.lit]
        for r in self.rounds2:
            self.bounds2.append(r[-1][-1] + 1)
        if not self.groups2:
            self.bounds2 = [self.lit]

        # THE TAIL'S TABLES (unchanged from v3)
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
        self._wmod = np.array([self.Wp % q for q in self.primes],
                              dtype=np.uint64)
        self.d_pres = cp.asarray(pres.ravel())
        self.d_pmask = cp.asarray(pmask.ravel())
        self.d_pk = cp.asarray(pk.ravel())
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

        # THE WINDOW TABLES and the per-residue x0 table
        (self._pat, self.pat_offs, self.dinvs) = window_patterns(
            n, fam, self.primes, self.groups, self.Wp, self.nw, unit=self.unit)
        self.d_pat = cp.asarray(self._pat)
        self.gmods = []
        for g in self.groups:
            Q = 1
            for i in g:
                Q *= self.primes[i]
            self.gmods.append(Q)
        v = r1u + np.uint64(self.W1) * A.astype(np.uint64)   # < 2^63 + 2^32
        x0 = np.empty((len(self.groups), self.R1), dtype=np.uint64)
        for gi, (Q, dinv) in enumerate(zip(self.gmods, self.dinvs)):
            x0[gi] = (v % np.uint64(Q)) * np.uint64(dinv) % np.uint64(Q)
        self.x0_dtype = (np.uint16 if max(self.gmods, default=1) < X0_DTYPE_MAX16
                         else np.uint32)
        self.d_x0 = cp.asarray(x0.astype(self.x0_dtype).ravel())
        self.d_jmod = cp.zeros(max(len(self.groups), 1), dtype=np.uint32)
        self._jmod = np.zeros(max(len(self.groups), 1), dtype=np.uint32)

        # geometry: one first-level residue per thread, SPB second-level
        # residues per block, PB periods per segment
        self.spb = 1 << (max(1, min(spb, self.R2)).bit_length() - 1)
        self.jpt = 1
        self.logtpb = self.tpb.bit_length() - 1
        self.logspb = self.spb.bit_length() - 1
        if (1 << self.logtpb) != self.tpb or (1 << self.logspb) != self.spb:
            raise ValueError(
                f"tpb={self.tpb} and spb={self.spb} must both be powers of "
                f"two: the shared queues store a candidate's (ss, tid, j) "
                f"index rather than its offset, and it is unpacked by shifts")
        self.tile = self.tpb * self.spb * self.pb       # candidates per block
        # launch shape: segments (of PB periods) x third-level residues x a
        # first-level chunk, under the candidate budget and the 2^63
        # reduction bound
        per_u_seg = self.R1 * self.R2 * self.pv
        budget = CAND_PER_LAUNCH4
        if nu is not None:
            self.nu = max(1, min(int(nu), self.R3))
        else:
            self.nu = max(1, min(self.R3, 65535, budget // max(per_u_seg, 1)))
        if tchunk is not None:
            self.tchunk = max(self.tpb, min(int(tchunk), self.R1))
        elif per_u_seg > budget:
            want = max(1, budget // (self.R2 * self.pv))
            self.tchunk = max(self.tpb, min(self.R1, (want // self.tpb) * self.tpb))
        else:
            self.tchunk = self.R1
        self.tchunk = ((self.tchunk + self.tpb - 1) // self.tpb) * self.tpb
        if self.nu < self.R3 or self.tchunk < self.R1:
            self.nseg = 1
        else:
            self.nseg = max(1, min(65535 // self.nu,
                                   budget // max(self.R * self.pv, 1)))
        while ((self.nseg * self.pv + 1) * self.Wp + self.q2 >= REDUCE_MAX
               and self.nseg > 1):
            self.nseg //= 2
        assert (self.nseg * self.pv + 1) * self.Wp + self.q2 < REDUCE_MAX
        self.seg_periods = self.nseg * self.pv
        self.n_tchunks = -(-self.R1 // self.tchunk)
        self.n_uchunks = -(-self.R3 // self.nu)
        self.launches_per_segment = self.n_tchunks * self.n_uchunks
        # the old name, for callers that price a launch: periods per launch
        self.per_launch = self.seg_periods

        # The shared queues are sized from the analytic survival, and CAPPED
        # in bytes: a gate configuration with two sieve primes above its
        # wheel keeps half its 65,536-candidate tile, and a queue that size
        # would be the whole shared memory of the SM.  Overflow is harmless
        # (the candidate runs its tail on the spot), so the cap costs a
        # shallow gate configuration speed and production nothing (its
        # queues are a few hundred entries).
        # three bytes per entry: a u16 index array and a u8 period array
        qbytes = 3

        def _caps(sig):
            caps = [_qcap(self.tile, self.surv[b], sig) for b in self.bounds2]
            while sum(caps) * qbytes > QUEUE_BYTES_MAX:
                caps = [max(32, ((c // 2 + 31) // 32) * 32) for c in caps]
                if all(c == 32 for c in caps):
                    break
            return caps

        # everything in shared that is NOT the queues, analytically (the
        # kernel is not compiled yet, and compiling once per candidate
        # margin would cost more than the margin is worth)
        ng_ = max(len(self.groups), 1)
        ng4_ = ((ng_ + 3) // 4) * 4
        xe_ = min(EXTRACT_EVERY_BY_NW.get(self.nw, 1), self.spb)
        nonq = (xe_ * self.nw * tpb * 4                      # sal
                + self.spb * ng4_ * 4                        # ne
                + self.spb * 4                               # d2
                + (int(self._pat.size) * 4 if PAT_SHARED else 0)
                + (ng_ * tpb * (2 if self.x0_dtype == np.uint16 else 4)
                   if X0_SHARED else 0)
                + (len(self.bounds2) + 2) * 4                # queue counters
                + SMEM_SLACK)
        try:
            import cupy as _cp
            per_sm = int(_cp.cuda.Device().attributes[
                "MaxSharedMemoryPerMultiprocessor"])
        except Exception:                       # noqa: BLE001
            per_sm = SMEM_PER_SM_DEFAULT
        best = None
        for sig in QCAP_SIGMA_LADDER:
            if sig > qcap_sigma:
                continue                        # never above what was asked
            caps = _caps(sig)
            tot = nonq + sum(caps) * qbytes
            blocks = per_sm // (tot + SMEM_BLOCK_RESERVE)
            cand = (blocks, sig)
            if best is None or cand > best[0]:
                best = (cand, caps, sig, tot, blocks)
        self.qcaps = best[1] if best else _caps(qcap_sigma)
        self.qcap_sigma_used = best[2] if best else qcap_sigma
        self.smem_predicted = best[3] if best else 0
        self.blocks_predicted = best[4] if best else 0
        self.q1cap = self.qcaps[0]
        self.q2cap = self.qcaps[-1] if len(self.qcaps) > 1 else 1
        cand = self.tchunk * self.R2 * self.nu * self.seg_periods
        self.cand_per_launch = cand
        self.rounds, self.round_cap, self.round_lpi = [], [], []
        b = self.k2
        np_ = len(self.primes)
        while True:
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

        # ---- the generated source
        ng = len(self.groups)
        ng4 = max(4, ((ng + 3) // 4) * 4)
        glines, blockpre = [], []
        for gi, (Q, dinv) in enumerate(zip(self.gmods, self.dinvs)):
            mg = (1 << 64) // Q
            red = (f"unsigned int r = (unsigned int)xx - "
                   f"(unsigned int)__umul64hi(xx, {mg}ULL) * {Q}u; "
                   f"if (r >= {Q}u) r -= {Q}u; ")
            # ne[ss][g] = (j0 + sg*PB - E_s) mod Q, E_s = (W1*D_s mod Q)*Dinv mod Q
            red2 = (f"r = (unsigned int)xx - "
                    f"(unsigned int)__umul64hi(xx, {mg}ULL) * {Q}u; "
                    f"if (r >= {Q}u) r -= {Q}u; ")
            blockpre.append(
                f"        {{ unsigned long long xx = (unsigned long long){self.W1}u"
                f" * (unsigned long long)dcur; {red}"
                f"xx = (unsigned long long)r * {dinv}ULL; {red2}"
                f"const unsigned int bs = (jmod[{gi}] + shift) % {Q}u; "
                f"ne[ss][{gi}] = (bs + {Q}u - r) % {Q}u; }}")
            off = self.pat_offs[gi]
            # ne for four groups at a time: one 16-byte shared load
            if gi % 4 == 0:
                glines.append(f"            {{ const uint4 n4_{gi // 4} = "
                              f"*(const uint4*)&ne[ss][{gi}];")
            nesel = ["x", "y", "z", "w"][gi % 4]
            body = [f"            {{ const unsigned int r = X0({gi}) + n4_{gi // 4}.{nesel} + bw; "
                    f"const unsigned int* T = pat + {off}u + (r >> 5); "
                    f"const unsigned int sh = r & 31u; "
                    f"unsigned int w0 = T[0], w1;"]
            for i in range(self.nw):
                body.append(f" w1 = T[{i + 1}]; "
                            f"acc[{i}] |= __funnelshift_r(w0, w1, sh); w0 = w1;")
            body.append(" }")
            if gi % 4 == 3 or gi == len(self.gmods) - 1:
                body.append(" }")
            glines.append("".join(body))
        r2_src, g2table, self.gdesc2 = lit_prefix(
            n, fam, self.primes, self.groups2, table="g2bits", indent=8,
            pname="g2p", unit=self.unit)
        self.d_g2bits = cp.asarray(g2table)
        self.gdesc = []
        r2_lines = r2_src.split("\n") if self.groups2 else []
        assert len(r2_lines) == len(self.groups2)
        R = len(self.rounds2) if self.groups2 else 0
        qcaps_src = "\n".join(f"#define Q{i}CAP {c}"
                               for i, c in enumerate(self.qcaps))
        qdecl = "\n".join(f"    __shared__ unsigned short qi{i}[Q{i}CAP];\n"
                           f"    __shared__ unsigned char qj{i}[Q{i}CAP];\n"
                           f"    __shared__ int qn{i};"
                           for i in range(len(self.qcaps)))
        qzero = " ".join(f"qn{i} = 0;" for i in range(len(self.qcaps)))
        rounds_src, g0 = [], 0
        for r in range(1, R + 1):
            g1 = g0 + len(self.rounds2[r - 1])
            kend = self.bounds2[r]
            body = " \\\n".join(ln.strip() for ln in r2_lines[g0:g1])
            # RILP items per thread per iteration, their test chains
            # independent so the compiler overlaps the latencies; the push
            # is one atomic per warp (warp_reserve)
            # every thread walks its items (at most MAXIT{r} of them, the
            # queue's capacity over TPB), keeps the survivors in registers,
            # and the warp reserves ONCE per round
            maxit = -(-self.qcaps[r - 1] // self.tpb)
            rounds_src.append(f"""#define ROUND{r}(OFF, KILL) {{ const unsigned long long off = (OFF); \\
        unsigned int kill = 0u; \\
        {body} \\
        (KILL) = kill; }}
    {{
        enum {{ MAXIT = {maxit} }};
        unsigned int alive_z = 0u;           /* bit z: item z*TPB + tid survived */
#pragma unroll
        for (int z = 0; z < MAXIT; ++z) {{
            const int idx = z * TPB + (int)threadIdx.x;
            if (idx < nq{r-1}) {{
                const unsigned long long oz = off_of(
                    QGET(qi{r-1}, qj{r-1}, idx), base, t_lo, res1x, d2);
                unsigned int kl;
                ROUND{r}(oz, kl)
                alive_z |= kl ? 0u : (1u << z);
            }}
        }}
        int p;
        const int total = warp_reserve(&qn{r}, __popc(alive_z), &p);
        if (total > 0) {{
#pragma unroll
            for (int z = 0; z < MAXIT; ++z) {{
                if ((alive_z >> z) & 1u) {{
                    const int _z = z * TPB + (int)threadIdx.x;
                    const unsigned int qi = QGET(qi{r-1}, qj{r-1}, _z);
                    if (p < Q{r}CAP) {{ qi{r}[p] = qi{r-1}[_z];
                                     qj{r}[p] = qj{r-1}[_z]; }}
                    else {{
                        const unsigned long long oz = off_of(qi, base, t_lo, res1x, d2);
                        if (tail_survives(oz, np_, {kend}, pk, pmask, pres)) EMIT(oz)
                    }}
                    ++p;
                }}
            }}
        }}
    }}
    __syncthreads();
    const int nq{r} = min(qn{r}, Q{r}CAP);""")
            g0 = g1
        rounds_src.append(f"    const int nqR = nq{R};\n"
                          f"    unsigned short* const qiR = qi{R};\n"
                          f"    unsigned char* const qjR = qj{R};")
        gparams = "".join(f",\n        const unsigned long long g2p{i}"
                          for i in range(len(self.gdesc2)))
        # The kernel source depends on the family only through the killed
        # sets, and those depend on (n, sign) -- both families share every
        # w(q,n), so the SIGN is the whole of the family in this key.
        key = ("v4", n, self.s,
               self.unit, self.W1, self.W2, q2, tpb, self.spb, self.pb, self.pv,
               self.lit, self.k2, self.R3, self.nu, MASK_BITS, self.nres,
               tuple(self.round_lpi), TAIL_TPB, tuple(self.qcaps),
               tuple(self.bounds2), tuple(map(tuple, self.groups)),
               tuple(map(tuple, self.groups2)), str(self.x0_dtype),
               PAT_SHARED, int(self._pat.size),
               EXTRACT_EVERY_BY_NW.get(self.nw, 1), X0_SHARED)
        fill = {"w1": self.W1, "w2": self.W2, "w": self.Wp,
                "two": 1 if self.R2 > 1 else 0, "lit": self.lit,
                "three": 1 if self.R3 > 1 else 0, "nu": self.nu,
                "k2": self.k2, "tpb": tpb, "spb": self.spb, "pb": self.pb,
                "nw": self.nw, "logp": self.logp, "ng": max(ng, 1),
                "pv": self.pv,
                "ng4": ng4, "rilp": ROUND_ILP,
                "patsh": 1 if PAT_SHARED else 0, "x0sh": 1 if X0_SHARED else 0,
                "npat": int(self._pat.size),
                "xe": min(EXTRACT_EVERY_BY_NW.get(self.nw, 1), self.spb),
                "logtpb": self.logtpb, "logspb": self.logspb,
                "qtype": ("unsigned short" if self.tile <= 65536
                          else "unsigned int"),
                "x0type": ("unsigned short" if self.x0_dtype == np.uint16
                           else "unsigned int"),
                "unroll": UNROLL, "qcaps": qcaps_src,
                "qdecl": qdecl, "qzero": qzero,
                "rounds2": "\n".join(rounds_src),
                "groups": "\n".join(glines),
                "blockpre": "\n".join(blockpre),
                "gparams": gparams,
                "mask_bits": MASK_BITS, "nres": self.nres,
                "ttpb": TAIL_TPB,
                "tailrounds": "".join(
                    _TAILROUND % {"lpi": l}
                    for l in sorted(set(self.round_lpi)))}
        if key not in _MODCACHE:
            src = _SRC4 % fill
            mod = cp.RawModule(code=src, options=("-std=c++14",),
                               backend="nvrtc")
            # pin FIRST, then measure: the occupancy the API reports depends
            # on the carveout attribute, and CuPy hands the same compiled
            # function to every engine with identical source, so an
            # unpinned query can read another engine's pin (G18 once read 3
            # and 5 blocks for one configuration in two processes)
            _set_carveout(mod.get_function("sieve"), CARVEOUT_PCT)
            occ = _occupancy(mod.get_function("sieve"), tpb)
            _MODCACHE[key] = (mod, dict(occ, body=0, carveout=CARVEOUT_PCT))
        mod, self.occupancy = _MODCACHE[key]
        self.k_sieve = mod.get_function("sieve")
        self.k_tails = {l: mod.get_function(f"tailround{l}")
                        for l in set(self.round_lpi)}
        self.k_tail = self.k_tails[self.round_lpi[0]]

    # ------------------------------------------------------------- geometry
    def j_of(self, k):
        return int(k) // self.W

    def density(self):
        return self.R / float(self.W)

    def bytes_held(self):
        n = (self.d_res1x.nbytes + self.d_pres.nbytes + self.d_pk.nbytes
             + self.d_pmask.nbytes + sum(b.nbytes for b in self.d_out)
             + self.d_res2c.nbytes + self.d_res2d.nbytes + self.d_pat.nbytes
             + self.d_x0.nbytes + self.d_g2bits.nbytes
             + sum(q.nbytes for q in self.d_q3))
        return int(n)

    def config(self):
        return {"n": self.n, "fam": self.fam, "s": self.s, "p1": self.p1,
                "p2": self.p2, "p3": self.p3, "q2": self.q2,
                "unit": self.unit, "W": int(self.W), "Wp": int(self.Wp),
                "R": int(self.R), "R1": self.R1, "R2": self.R2,
                "R3": self.R3, "nu": self.nu, "per_launch": self.per_launch,
                "pb": self.pb, "pv": self.pv, "nseg": self.nseg,
                "tchunk": self.tchunk,
                "seg_periods": self.seg_periods,
                "launches_per_segment": self.launches_per_segment,
                "cand_per_launch": int(self.cand_per_launch),
                "lit": self.lit, "k2": self.k2, "groups": self.groups,
                "groups2": self.groups2, "rounds2": len(self.rounds2),
                "q1cap": self.q1cap, "q2cap": self.q2cap, "qcaps": self.qcaps,
                "bounds2": self.bounds2, "q3cap": self.q3cap,
                "rounds": self.rounds, "round_lpi": self.round_lpi,
                "pat_bytes": int(self.d_pat.nbytes),
                "x0_bytes": int(self.d_x0.nbytes),
                "body": self.occupancy["body"],
                "num_regs": self.occupancy["num_regs"],
                "smem_bytes": self.occupancy["smem_bytes"],
                "blocks_per_sm": self.occupancy["blocks_per_sm"],
                "carveout": self.occupancy["carveout"],
                "qcap_sigma": self.qcap_sigma_used,
                "smem_predicted": self.smem_predicted,
                "blocks_predicted": self.blocks_predicted}

    # ---------------------------------------------------------------- sieve
    def _launch_base(self, base):
        """Fold an absolute launch base (k', a Python int) into the tables:
        base mod q per tail prime, base mod Q per round-2 group, and
        j0 mod Q per window group (j0 = base / Wp: Wp*Dinv == 1 mod Q)."""
        j = int(base) // self.Wp
        if j < (1 << 64):
            bmod = (self._wmod * (np.uint64(j) % self._qs)) % self._qs
        else:
            bmod = np.array([(int(w) * (j % int(q))) % int(q)
                             for w, q in zip(self._wmod, self._qs)],
                            dtype=np.uint64)
        self._pk[:, 3] = bmod.astype(np.uint32)
        self.d_pk.set(self._pk.ravel())
        for gi, Q in enumerate(self.gmods):
            self._jmod[gi] = j % Q
        self.d_jmod.set(self._jmod)
        return group_params(self.gdesc2, base)

    def _check_window(self, j0, j1, k_min):
        ceil = k_ceil(self.n, self.fam)
        if j1 * self.W > ceil:
            raise ValueError(f"k {j1 * self.W} past the enforced ceiling "
                             f"{ceil}")
        floor = k_floor(self.q2, self.n, self.fam)
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
        out = []
        for _, _, surv in self.sweep(j0, j1, k_min=k_min):
            out.extend(surv)
        return sorted(out)

    def progress_k(self, jn, un):
        """A k for the heartbeat inside a segment: progress, not coverage."""
        return int(jn * self.W + self.seg_periods * self.W * un
                   // max(self.launches_per_segment, 1))

    def sweep(self, j0, j1, u_from=0, k_min=None):
        """Yield (j_next, u_next, survivors) after every kernel launch.

        `(j_next, u_next)` is a RESUMABLE cursor: `u_next` counts the
        launches done inside the segment that starts at period `j_next`,
        and `u_next == 0` means the stronger thing -- every k below
        `j_next * W` has been swept, so the coverage claim may advance.
        A segment is `seg_periods` periods (PB per window times the
        segments a launch batches); the last one in a window is partial.
        """
        j0, j1, u_from = int(j0), int(j1), int(u_from)
        clip = self._check_window(j0, j1, k_min)
        return self._sweep(j0, j1, u_from, clip)

    def _sweep(self, j0, j1, u_from, clip):
        gy = (self.R2 + self.spb - 1) // self.spb
        pending = None
        jg = j0
        while jg < j1:
            nper = min(self.seg_periods, j1 - jg)
            base = self.Wp * jg
            drained = self._collect(pending, clip)
            pending = None
            gps = self._launch_base(base)
            if drained is not None:
                yield drained
            nl = self.launches_per_segment
            li = 0
            for u0 in range(0, self.R3, self.nu):
                nu_l = min(self.nu, self.R3 - u0)
                for t_lo in range(0, self.R1, self.tchunk):
                    li += 1
                    if li <= u_from:
                        continue
                    nt = min(self.tchunk, self.R1 - t_lo)
                    gx = (nt + self.tpb - 1) // self.tpb
                    gz = -(-nper // self.pv) * nu_l
                    cur = (jg + nper, 0) if li == nl else (jg, li)
                    b = self._buf = self._buf ^ 1
                    self._enqueue(b, gx, gy, gz, nper, u0, t_lo, gps)
                    done = self._collect(pending, clip)
                    pending = (base, b, cur)
                    if done is not None:
                        yield done
            u_from = 0
            jg += nper
        done = self._collect(pending, clip)
        if done is not None:
            yield done

    def _enqueue(self, b, gx, gy, gz, nper, u0, t_lo, gps):
        np_ = np.int32(len(self.primes))
        self.d_n[b].fill(0)
        self.d_n3.fill(0)
        self.k_sieve((gy, gx, gz), (self.tpb,),
                     (np.int32(self.R1), np.int32(self.R2), np_,
                      self.d_pmask, self.d_pres,
                      self.d_out[b], self.d_n[b], np.int32(HIT_CAP),
                      self.d_q3[0], self.d_n3, np.int32(self.q3cap),
                      self.d_pk, self.d_res1x, self.d_x0, self.d_res2c,
                      self.d_res2d, np.int32(u0), np.int32(t_lo),
                      np.int32(nper), self.d_jmod, self.d_pat,
                      self.d_g2bits, *gps))
        R = len(self.rounds)
        for r, (fr, to) in enumerate(self.rounds):
            qi, qo = self.d_q3[r & 1], self.d_q3[(r + 1) & 1]
            ci = self.round_cap[r] if r else min(self.round_cap[0], self.q3cap)
            co = self.round_cap[r + 1] if r + 1 < R else 1
            lpi = self.round_lpi[r]
            grid = max(1, -(-ci // (self.tail_tpb // lpi)))
            self.k_tails[lpi]((grid,), (self.tail_tpb,),
                              (qi, self.d_n3[r:r + 1], np.int32(ci),
                               qo, self.d_n3[r + 1:r + 2], np.int32(co),
                               np.int32(fr), np.int32(to), np_,
                               self.d_out[b], self.d_n[b], np.int32(HIT_CAP),
                               self.d_pk, self.d_pmask, self.d_pres))
        self.d_n[b].get(out=self._h_n[b], blocking=False)
        self.d_out[b][:self._pre].get(out=self._h_out[b], blocking=False)
        self._ev[b].record()
        self._flush.done

    def _collect(self, pending, clip=0):
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
            surv = sorted(v for v in (self.unit * (base + int(o))
                                      for o in offs.tolist())
                          if v >= clip)
        return jn, un, surv

    def survivors_k(self, k_lo, k_hi):
        k_lo, k_hi = int(k_lo), int(k_hi)
        j0, j1 = k_lo // self.W, (k_hi - 1) // self.W + 1
        k_min = k_lo if j0 * self.W <= k_floor(self.q2, self.n, self.fam) else None
        return [k for k in self.survivors_j(j0, j1, k_min=k_min)
                if k_lo <= k < k_hi]


# --------------------------------- gates -----------------------------------

def g7_wheel_matches_oracle():
    """The CRT-lifted wheel == the oracle's brute-force walk of the period,
    for several families; and the CRT recombination reproduces the
    one-level wheel exactly."""
    fams = ("A078502", "A074200")
    for fam in fams:
        for n, p1 in ((5, 7), (9, 11), (15, 11), (15, 13), (16, 13)):
            W, res = wheel(n, fam, p1)
            Wo, reso = wheel_residues(fam, n, p1)
            if W != Wo or list(res) != list(reso):
                return False, (f"G7 FAIL: {fam} n={n} p1={p1}: lifted "
                               f"{len(res)} residues mod {W}, oracle "
                               f"{len(reso)} mod {Wo}")
        for n, p1, p2 in ((15, 7, 13), (15, 11, 17), (9, 7, 11)):
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
        # The unit is 2 at n = 15 and 17, 34 at 16, 114 at 18 -- a different
        # wheel at every filter, which is why each is walked separately.
        for n, p1, unit in ((15, 13, 2), (16, 13, 34), (17, 17, 2),
                            (18, 13, 114)):
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
        for n, p1, p2, unit in ((15, 11, 13, 2), (16, 13, 19, 34),
                                (18, 11, 13, 114)):
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
    # and a unit the forcing lemma grants at ONE filter only: 34 at n = 16.
    # Walking it at n = 15 and n = 17 must NOT be attempted -- assert_unit
    # refuses -- which is the property that keeps a carried-forward wheel
    # from silently thinning the line.
    for n in (15, 17):
        try:
            wheel(n, "A078502", 13, unit=34)
            return False, (f"G7 FAIL: a unit-34 wheel was built at n = {n}, "
                           f"where 17 is not forced")
        except ValueError:
            pass
    return True, ("G7 ok: CRT-lifted wheel == oracle period walk at (n,p1) = "
                  "(5,7), (9,11), (15,11), (15,13), (16,13) for both "
                  "families; the two-level CRT recombination == the one-level "
                  "wheel at three (p1,p2] splits; in unit space the x' wheel "
                  "== the oracle's divisibility on x = unit*x' at every "
                  "campaign unit (2 at n = 15 and 17, 34 at 16, 114 at 18) "
                  "and recombines across two levels; and the unit-34 wheel is "
                  "REFUSED at the filters either side of 16, where 17 is not "
                  "forced")


def g8_wheel_partitions_the_period():
    """Kept + killed == the whole period, and the count is the formula.

    The direction that matters is the second one: a wheel that DROPS a
    residue it should have kept loses candidates silently, and no parity
    gate against another engine using the same wheel could ever see it.
    """
    from lcml_reference import w as w_formula
    cases = []
    for fam in FAMILIES:
        cases += [(fam, 15, 13, 1, 1), (fam, 15, 23, 1, 1), (fam, 12, 23, 1, 1),
                  (fam, 16, 19, 1, 1), (fam, 15, 37, 23, 1),
                  (fam, 15, 31, 23, 1), (fam, 16, 47, 37, 1)]
    # The production levels, in unit space, at EVERY filter the campaign can
    # open at or promote into -- and the unit is re-derived per filter,
    # because it changes in both directions here (2, 34, 2, 114, 6, 30).
    for fam in FAMILIES:
        n0 = max(KNOWN[fam]) + 1
        for n in range(n0, n0 + 6):
            unit = forced_unit(n, fam)
            for lv in wheel_plan(n, fam, unit,
                                 max_period=search_period_cap(n, fam)):
                if lv:
                    cases.append((fam, n, lv, 1, unit))
    for fam, n, p1, lo, unit in cases:
        W, res = wheel(n, fam, p1, lo=lo, unit=unit)
        qs = ([q for q in p1 if unit % q] if not isinstance(p1, int)
              else [q for q in primerange(lo + 1, p1 + 1) if unit % q])
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
                  f"{len(cases)} (family, n, level, unit) cases: x-space "
                  f"levels for both families, and the PLANNED production "
                  f"levels at every filter n = 15..20 of both families, each "
                  f"at that filter's own forced unit (2, 34, 2, 114, 6, 30) "
                  f"-- the unit and the level split are re-derived per "
                  f"filter, never carried")


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
    from lcml_search import k_proof
    ceil_17 = k_proof(17, "A078502")           # 2.7e17, a crossing the hunt passes
    ceil = k_ceil(15, "A078502")               # 1e40, the enforced ceiling
    W19 = 9_699_690
    cases = (
        # fam, n, p1, p2, p3, q2, x_lo, span, unit
        #
        # q2 = 32 throughout, and the spans are 1e7-4e7 rather than the
        # linear ladders' 4e8: this project's wheel is ~2,400x weaker at
        # n = 15, so a window a fortieth of the width holds more survivors
        # than theirs did.  That is the same fact as the weak small primes,
        # and it is what makes a dense CPU sieve affordable as the reference.
        ("A078502", 9, 13, None, None, 32, 2 * 10 ** 9, 2 * 10 ** 7, 1),
        ("A074200", 9, 13, None, None, 32, 2 * 10 ** 9, 2 * 10 ** 7, 1),
        ("A078502", 15, 13, None, None, 32, 10 ** 12, 10 ** 7, 1),
        ("A074200", 15, 13, 23, None, 32, 10 ** 12, 10 ** 7, 1),
        ("A078502", 15, 11, 19, 23, 32, 10 ** 12, 10 ** 7, 1),
        ("A074200", 17, 13, 23, None, 32, 9 * 10 ** 14, 2 * 10 ** 7, 1),
        ("A078502", 16, 13, 19, 23, 32, 9 * 10 ** 14, 2 * 10 ** 7, 1),
        # PERIOD 0, clipped at the engine floor: the campaign's first window,
        # and the one place a wheel offset can be wrong without any other
        # window noticing
        ("A078502", 9, 13, 19, None, 32, 1, W19 - 1, 1),
        ("A074200", 15, 13, 19, None, 32, 1, W19 - 1, 1),
        # UNIT SPACE: the device sweeps x' = x / unit and the host multiplies
        # back; the CPU engine still marks the dense x line, so the forcing
        # lemma is checked here as well as the fold.  EVERY campaign unit
        # appears -- 2 at n = 15 and 17, 34 at 16, 114 at 18, 6 at 19 -- and
        # a unit is only ever used at the filter that forces it.
        ("A078502", 15, 13, 19, None, 32, 10 ** 12, 10 ** 7, 2),
        ("A074200", 15, 13, 19, 23, 32, 10 ** 12, 10 ** 7, 2),
        ("A078502", 16, 13, 19, 23, 32, 10 ** 12, 2 * 10 ** 7, 34),
        ("A074200", 16, 13, 23, None, 32, 10 ** 12, 2 * 10 ** 7, 34),
        ("A078502", 17, 13, 19, 23, 32, 10 ** 15, 2 * 10 ** 7, 2),
        ("A074200", 18, 13, 23, None, 32, 10 ** 15, 2 * 10 ** 7, 114),
        ("A078502", 19, 11, 17, 23, 32, 10 ** 15, 4 * 10 ** 7, 6),
        # ABOVE 2^64, and past the PROOF CROSSING at n = 17 (2.7e17), which
        # this campaign passes early: both engines are Python ints there.
        ("A074200", 17, 13, 19, 23, 32, ceil_17 + 10 ** 12, 2 * 10 ** 7, 2),
        ("A078502", 15, 13, 19, None, 32, 10 ** 21, 10 ** 7, 2),
        # HARD AGAINST THE 1e40 CEILING, on both signs and both units: the
        # base is a 133-bit Python int on both engines
        ("A078502", 15, 13, 19, 23, 32, ceil - 10 ** 9, 10 ** 7, 2),
        ("A074200", 16, 13, 19, 23, 32, ceil - 10 ** 9, 2 * 10 ** 7, 34),
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
                  f"wheels in x space AND in unit space at every campaign "
                  f"unit (2, 34, 114, 6), both families, filters n = 9 to 19, "
                  f"heights 2e9 -> {ceil:.3g} with windows ABOVE 2^64 and "
                  f"past the n = 17 proof crossing ({ceil_17:.3g}), two hard "
                  f"against the 1e40 ceiling on both signs; and period 0 "
                  f"clipped at the engine floor on both families")


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
    from lcml_reference import forced_primes, w as w_formula
    cases = [("A078502", 15, 23, 37, 47, 1), ("A078502", 16, 23, 37, 47, 1),
             ("A074200", 15, 23, 37, 47, 1), ("A074200", 16, 23, 37, None, 1)]
    # EVERY opening the campaign can start at or promote into, at the wheel
    # the planner actually picks there and at that filter's own forced unit
    # -- both re-derived per filter, because both change in both directions.
    for fam in FAMILIES:
        n0 = max(KNOWN[fam]) + 1
        for n in range(n0, n0 + 6):
            unit = forced_unit(n, fam)
            p1, p2, p3 = wheel_plan(n, fam, unit,
                                    max_period=search_period_cap(n, fam))
            cases.append((fam, n, p1, p2, p3, unit))
            # and one alternative -- a PREFIX split of the same filter, so
            # the gate is not merely re-checking the planner's own
            # arithmetic and the two wheel shapes are both exercised
            cases.append((fam, n, 19 if unit % 19 else 17, 31, 43, unit))
    for fam, n, p1, p2, p3, unit in cases:
        W1, r1 = wheel(n, fam, p1, unit=unit)
        if not p2:
            p2 = p1
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
        qs = ([q for q in _wheel_primes(p1, p2, p3) if unit % q]
              if not isinstance(p1, int) else
              [q for q in primerange(2, (p3 or p2) + 1) if unit % q])
        want = 1
        for q in qs:
            want *= q - w_formula(q, n, fam)
        if r1.size * r2.size * r3.size != want:
            return False, (f"G13 FAIL: {fam} n={n} ({p1},{p2},{p3}] unit "
                           f"{unit}: {r1.size}*{r2.size}*{r3.size} != {want}")
        # the kill check is in K SPACE, on k = unit*x, against the k-space
        # killed set: the unit's own primes included, which must never
        # kill a multiple of the unit
        top = max(qs)
        killed = {q: set(killed_residues(q, n, fam)) for q in qs}
        forced = 1
        for q in forced_primes(fam, n, upto=top + 1):
            if q in qs or unit % q == 0:
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
                  f"x-space (23,37,47] at n = 15, 16 of both families, and "
                  f"the PLANNED production wheel plus one alternative split "
                  f"at every filter n = 15..20 of both families, each at that "
                  f"filter's own forced unit; "
                  f"3000 sampled CRT residues per configuration recombine to "
                  f"all three levels, survive every wheel prime IN K SPACE "
                  f"(k = unit*x) and are multiples of every forced prime; "
                  f"W1, W2 under 2^32 and W1*W2 under 2^63")


def g14_engine_mechanisms():
    """The generation tables, the derived compaction depths, the CRT-combined
    group tables, and the queue-overflow fallback -- each against its own
    definition, at the production configurations G9 cannot reach."""
    rng = np.random.default_rng(20260904)
    cases = (("A078502", 15, 23, 37, None, 65536, 1),
             ("A078502", 16, 23, 37, 47, 65536, 1),
             ("A074200", 15, 23, 37, 47, 65536, 1),
             ("A078502", 15, 23, 31, None, 4096, 1),
             # the unit wheels the campaigns run
             ("A078502", 15, 19, 31, 43, 131072, 2),
             ("A078502", 17, 19, 31, 43, 32768, 2),
             ("A074200", 15, 19, 31, 43, 131072, 2),
             ("A074200", 16, 23, 37, 47, 131072, 34),
             ("A078502", 18, 23, 37, 47, 32768, 114),
             # and v1's, whose fingerprints the cross-wheel gate rests on
             ("A074200", 17, 19, 29, 41, 65536, 2))
    for fam, n, p1, p2, p3, q2, unit in cases:
        W1, r1 = wheel(n, fam, p1, unit=unit)
        if p2 is None:
            p2 = p1
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

        # THE WINDOW CHAIN (v4) against the DEFINITION: for sampled
        # candidates (t, s, u) in sampled periods of sampled segments, the
        # bit the kernel would read -- x0[g][t] + ne(s, u) + bw, then the
        # pattern word -- must say "killed by q" exactly when the value's
        # residue is in killed_residues(q).  Every table the device holds
        # for the window sieve is exercised, at two launch bases including
        # one above 2^64.
        pat = eng.cp.asnumpy(eng.d_pat)
        x0 = eng.cp.asnumpy(eng.d_x0).astype(np.int64).reshape(len(eng.groups), eng.R1)
        r1x = eng.cp.asnumpy(eng.d_res1x).reshape(eng.R1, 2).astype(np.int64)
        c2 = eng.cp.asnumpy(eng.d_res2c).astype(np.int64)
        d2 = eng.cp.asnumpy(eng.d_res2d).astype(np.int64)
        W1, W2, Wp, PB = int(eng.W1), int(eng.W2), int(eng.Wp), eng.pb
        kill = {q: set(killed_residues(q, n, fam, unit)) for q in primes}
        nchk = 0
        for j0 in (7, 10 ** 25 // Wp * Wp // Wp):
            for sg in (0, min(3, eng.nseg - 1)):
                for t, sx, u, j in zip(rng.integers(0, eng.R1, 60).tolist(),
                                       rng.integers(0, eng.R2, 60).tolist(),
                                       rng.integers(0, eng.R3, 60).tolist(),
                                       rng.integers(0, PB, 60).tolist()):
                    r1, A = int(r1x[t, 0]), int(r1x[t, 1])
                    if eng.R2 > 1:
                        c = int(c2[sx])
                        if eng.R3 > 1:
                            c = (c + int(d2[u])) % W2
                        D = W2 - c
                        bw = 1 if A < D else 0
                        off = r1 + W1 * (A - D + (W2 if bw else 0))
                    else:
                        D, bw, off = 0, 0, r1
                    kp = Wp * (j0 + sg * PB + j) + off
                    for gi, (g, Q, dinv) in enumerate(zip(eng.groups, eng.gmods,
                                                          eng.dinvs)):
                        q = primes[g[0]]
                        E = ((W1 * D) % Q) * dinv % Q
                        ne = ((j0 % Q) + sg * PB - E) % Q
                        r = int(x0[gi, t]) + ne + bw
                        if not 0 <= r < 2 * Q:
                            return False, (f"G14 FAIL: {fam} n={n} window residue "
                                           f"{r} is not in [0, 2Q) for Q={Q}")
                        p = r + j
                        bit = (int(pat[eng.pat_offs[gi] + (p >> 5)]) >> (p & 31)) & 1
                        want = 1 if (kp % q) in kill[q] else 0
                        if bit != want:
                            return False, (f"G14 FAIL: {fam} n={n} unit {unit}: the "
                                           f"window bit for q={q} at (t,s,u,j)="
                                           f"({t},{sx},{u},{j}), base period "
                                           f"{j0 + sg * PB}, says {bit} but "
                                           f"k'={kp} mod {q} = {kp % q} is "
                                           f"{'killed' if want else 'kept'}")
                        nchk += 1
        if nchk < 1000:
            return False, "G14 FAIL: too few window bits checked -- vacuous"

    # The queues are sized from the survival rate rather than the worst
    # case, so overflow is POSSIBLE -- and the whole design rests on it
    # being harmless.  FORCED: an engine whose queues hold 32 entries
    # against a block that owns thousands takes the fallback for nearly
    # every candidate, and its stream must be identical.
    ref = GpuEngine(15, "A078502", p1=13, p2=23, p3=None, q2=128)
    tiny = GpuEngine(15, "A078502", p1=13, p2=23, p3=None, q2=128,
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

    prod = GpuEngine(15, "A078502", unit=2)
    if not 0 < prod.q1cap <= prod.tile or not 0 < prod.q2cap <= prod.tile:
        return False, (f"G14 FAIL: production queue capacities "
                       f"({prod.q1cap}, {prod.q2cap}) are not within "
                       f"(0, tile = {prod.tile}]")
    if prod.d_pat.nbytes > PAT_BYTES_MAX:
        return False, (f"G14 FAIL: the production window tables are "
                       f"{prod.d_pat.nbytes} bytes, over PAT_BYTES_MAX")
    return True, (f"G14 ok: the split A/C/D generation tables reproduce the "
                  f"one-table CRT on 20000 sampled triples at ten "
                  f"configurations including k-space (23,37,47] and the "
                  f"production unit wheels (..37],(37,47],(47,59] at unit "
                  f"the campaign units (2 at n = 15 and 17, 34 at n = 16, "
                  f"114 at n = 18); the compaction "
                  f"depths derive from the survival curve (A078502 n = 15: "
                  f"window sieve to prime index {prod.lit}, in-block rounds "
                  f"to {prod.k2}); the window groups and the round groups "
                  f"cover their prime ranges exactly once in order, every "
                  f"round table agrees with killed_residues on EVERY residue "
                  f"of its modulus, and the WINDOW CHAIN -- the x0 table, "
                  f"the per-block ne, the borrow and the pattern word -- "
                  f"says killed exactly when the value is, on 240 sampled "
                  f"(t, s, u, period) candidates per configuration at two "
                  f"launch bases (one above 2^64); production queues hold "
                  f"{prod.q1cap} and {prod.q2cap} of a {prod.tile}-candidate "
                  f"block, its window tables {prod.d_pat.nbytes} bytes; and "
                  f"with the queues forced to 32 the survivor stream is "
                  f"IDENTICAL ({len(a)} survivors)")


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
    # the same window under two launch decompositions -- 64-period
    # segments batched into launches against 32-period segments cut into
    # first-level chunks of one block -- and split at a period that is not
    # a segment boundary, so the partial-segment mask is exercised
    eng = GpuEngine(15, "A078502", p1=13, p2=23, p3=None, q2=512)
    engb = GpuEngine(15, "A078502", p1=13, p2=23, p3=None, q2=512, pb=32,
                     tchunk=TPB_DEFAULT, nu=1)
    j0 = eng.j_of(10 ** 12)
    one = eng.survivors_j(j0, j0 + 600)
    many = engb.survivors_j(j0, j0 + 600)
    parts = (engb.survivors_j(j0, j0 + 250)
             + engb.survivors_j(j0 + 250, j0 + 600))
    if not one:
        return False, "G15 FAIL: the base-shift window is empty -- vacuous"
    if one != many or one != sorted(parts):
        return False, (f"G15 FAIL: the stream depends on the launch base: "
                       f"{len(one)} survivors in {eng.seg_periods}-period "
                       f"segments vs {len(many)} in {engb.seg_periods}-period "
                       f"segments of {engb.launches_per_segment} launches, "
                       f"{len(parts)} split at a non-segment period -- the "
                       f"fold is not base-invariant")
    # and in UNIT space, where the base the device folds is in k' and the
    # survivors come back multiplied: same invariance, and every survivor
    # a multiple of the unit that the k-space engine also keeps
    engu = GpuEngine(15, "A078502", p1=19, p2=23, p3=None, q2=512, unit=2)
    engub = GpuEngine(15, "A078502", p1=19, p2=23, p3=None, q2=512, unit=2,
                      pb=32, tchunk=TPB_DEFAULT, nu=1)
    ju = engu.j_of(10 ** 12)
    oneu = engu.survivors_j(ju, ju + 600)
    manyu = engub.survivors_j(ju, ju + 600)
    partsu = (engub.survivors_j(ju, ju + 250)
              + engub.survivors_j(ju + 250, ju + 600))
    if not oneu:
        return False, "G15 FAIL: the unit base-shift window is empty -- vacuous"
    if oneu != manyu or oneu != sorted(partsu):
        return False, (f"G15 FAIL: with unit 2 the stream depends on the "
                       f"launch base: {len(oneu)} vs {len(manyu)} vs "
                       f"{len(partsu)} split")
    if any(k % 2 for k in oneu):
        return False, "G15 FAIL: a unit-space survivor is not a multiple of the unit"
    presu = engu.cp.asnumpy(engu.d_pres).reshape(len(engu.primes), engu.nres)
    for i in np.random.default_rng(5).integers(0, len(engu.primes), 20).tolist():
        q = engu.primes[i]
        kr = killed_residues(q, 15, "A078502", 2)
        if sorted(presu[i][:len(kr)].tolist()) != kr:
            return False, (f"G15 FAIL: with unit 2, prime {q}'s residue "
                           f"list is not the unit-space killed set")

    pres = eng.cp.asnumpy(eng.d_pres).reshape(len(eng.primes), eng.nres)
    pmask = eng.cp.asnumpy(eng.d_pmask).reshape(len(eng.primes),
                                                 eng.mask_words)
    rng = np.random.default_rng(4)
    for i in rng.integers(0, len(eng.primes), 40).tolist():
        q = eng.primes[i]
        kr = killed_residues(q, 15, "A078502")
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
                 k_ceil(15, "A078502") - eng.W, 10 ** 30):
        base -= base % eng.W
        gps = eng._launch_base(base)
        got = eng._pk[:, 3].astype(np.int64)
        want = np.array([base % q for q in eng.primes], dtype=np.int64)
        if not np.array_equal(got, want):
            i = int(np.flatnonzero(got != want)[0])
            return False, (f"G15 FAIL: at base {base:.4g} the fold for prime "
                           f"{eng.primes[i]} is {got[i]}, not "
                           f"{want[i]} = base mod q")
        jm = eng.cp.asnumpy(eng.d_jmod).astype(np.int64)
        for gi, Q in enumerate(eng.gmods):
            if int(jm[gi]) != (base // eng.Wp) % Q:
                return False, (f"G15 FAIL: window group {gi} (modulus {Q}) at "
                               f"base {base:.4g}: the folded period is "
                               f"{int(jm[gi])}, not j0 mod Q")
        descs = list(eng.gdesc2)
        gtab = (eng.cp.asnumpy(eng.d_g2bits), eng.cp.asnumpy(eng.d_g2bits))
        for gi, ((kind, Q, payload), gp) in enumerate(zip(descs, gps)):
            tab = gtab[1]
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
                  f"decomposition ({len(one)} survivors over 600 periods in "
                  f"{eng.seg_periods}-period segments, in 32-period segments "
                  f"of one-block launches, and split at a period inside a "
                  f"segment; and {len(oneu)} in unit space, every one a "
                  f"multiple of the unit, with the residue lists the unit-space "
                  f"killed sets); the tail's residue lists and {MASK_BITS}-bit "
                  f"masks are exactly killed_residues (mod MASK_BITS) on 40 "
                  f"sampled primes, exact below MASK_BITS; and every "
                  f"per-prime and per-group fold is exactly (base mod "
                  f"modulus) at six bases up to 1e30 -- so nothing on the "
                  f"device is bounded by k")


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
    n, fam, p1, p2, p3, q2 = 15, "A078502", 13, 17, 19, 128
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
    """The production unit wheel == a differently-split wheel == a coarser
    wheel == an x-space wheel, on the line.

    G9 proves the unit machinery on wheels a dense CPU sieve can follow;
    this pins the wheel the campaign actually runs against three others over
    the SAME absolute window.  Four wheels enumerating the same candidates by
    different arithmetic must return the identical survivor stream.
    Coverage is what a fingerprint cannot see, so this is the gate the
    production wheel's claim stands on.

    THE WINDOW IS ONE PRODUCTION PERIOD, and that is affordable here for the
    reason everything else in this project is expensive: the wheel is weak,
    so its period is short.  One period at n = 15 is 1.31e16 of x, 5.5e11
    candidates and about a quarter-second of device -- where the linear
    ladders' production period was 1.9e21 of k.  (The gate this replaced
    swept 47 periods and handed ~1.2 million survivors to a one-at-a-time
    CPU test: an hour, not a gate.)

    The four wheels, all over the same window:
      * the PLANNED production wheel, (..19],(19,31],(31,43] at the filter's
        unit -- what the campaign runs;
      * the SAME prime set split differently, (..23],(23,31],(31,43] -- so a
        CRT-lift bug that depends on where the levels break shows up;
      * a COARSER wheel, (..17],(17,29],(29,41], whose period is 43x shorter,
        so it covers the window in 43 periods and sieves 43 in its TAIL
        instead of its wheel -- the one that proves the wheel/sieve boundary
        is not load-bearing;
      * an X-SPACE wheel (unit = 1) over primes to 43, whose period is the
        same 1.31e16 because the unit's primes are in it instead.
    """
    out = []
    for n, fam in ((15, "A078502"), (17, "A074200")):
        unit = forced_unit(n, fam)
        # pb = 32, not the production 192, and only so the gate FITS: the
        # window is one period, a segment is `pb` periods, and an engine
        # asked for one period of a 192-period segment does a full segment's
        # launches for 1/192 of the work (30 s against 1 s).  The stream does
        # not depend on pb -- G15 proves invariance under the launch
        # decomposition and the pb sweep returned identical survivor sets at
        # 32, 64, 128, 160, 192, 224 and 256 -- and the production width is
        # exercised by G9 and G18, which use the default.
        kw = dict(q2=Q2_DEFAULT, pb=32)
        prod = GpuEngine(n, fam, p1=19, p2=31, p3=43, unit=unit, **kw)
        alt = GpuEngine(n, fam, p1=23, p2=31, p3=43, unit=unit, **kw)
        coarse = GpuEngine(n, fam, p1=17, p2=29, p3=41, unit=unit, **kw)
        xsp = GpuEngine(n, fam, p1=23, p2=37, p3=43, unit=1, **kw)
        j = 700
        lo, hi = j * prod.W, (j + 1) * prod.W
        if xsp.W != prod.W:
            return False, (f"G17 FAIL: the x-space wheel's period {xsp.W} is "
                           f"not the unit wheel's {prod.W}, so the window is "
                           f"not one period of both")
        a = prod.survivors_j(j, j + 1)
        if not a:
            return False, f"G17 FAIL: {fam} n={n} period {j} is empty -- vacuous"
        for name, eng in (("the same primes split (..23],(23,31],(31,43]", alt),
                          ("the coarser (..17],(17,29],(29,41]", coarse),
                          ("an x-space wheel over primes to 43", xsp)):
            got = eng.survivors_k(lo, hi)
            if got != a:
                sa, sg = set(a), set(got)
                return False, (f"G17 FAIL: {fam} n={n} over [{lo:.4g}, "
                               f"{hi:.4g}) the production wheel keeps "
                               f"{len(a)} survivors and {name} {len(got)}: "
                               f"diff {sorted(sa ^ sg)[:4]}")
        if any(k % unit for k in a):
            return False, (f"G17 FAIL: {fam} n={n}: a survivor is not a "
                           f"multiple of the forced unit {unit}")
        # and a sample of them passes the CPU engine's own one-at-a-time test
        cpu = CpuEngine(n, fam, q2=Q2_DEFAULT)
        step = max(1, len(a) // 200)
        if not all(cpu.survives(k) for k in a[::step]):
            return False, (f"G17 FAIL: {fam} n={n}: a survivor fails the CPU "
                           f"engine's x-space test")
        out.append(f"{fam} n={n} unit {unit}: {len(a)} survivors over one "
                   f"period ({prod.W:.3g} of x)")
    return True, ("G17 ok: four wheels, four arithmetics, one stream -- the "
                  "planned production wheel, the same prime set split at a "
                  "different level, a coarser wheel covering the window in 43 "
                  "of its own periods (so 43 moves from the wheel into the "
                  "sieve), and an x-space wheel of the same period, all "
                  "return the IDENTICAL survivors over one production period "
                  "at " + "; ".join(out) + " -- every survivor a multiple of "
                  "that filter's forced unit, and a 200-point sample passes "
                  "the CPU engine's one-at-a-time test")


def g18_every_opening_compiles_to_occupancy():
    """Every campaign opening (and the filter after it), and every filter
    a RESUMED campaign runs or promotes into next (the frontier's successor
    and the two after it), compiles to the occupancy the engine was tuned
    at, with the carveout pinned and the prefix tables inside their cap.

    A kernel is not a configuration until it has compiled: the register
    allocation of this body varies 50 to 117 between near-identical
    configurations, and 5 blocks per SM instead of 9 is 0.8x with every
    fingerprint green.  This is the 5g check for a cost no fingerprint
    can see (OPTIMIZATION_LOG.md v2).
    """
    import cupy as cp
    rows = []
    for fam in FAMILIES:
        n0 = max(KNOWN[fam]) + 1
        # EVERY filter this campaign can open at or promote into, up to four
        # past the frontier -- and each is built the way the campaign builds
        # it, with NO wheel named, so what compiles here is exactly what runs
        # (the unit, the wheel split, the window width and the sieve depth
        # are all planned per filter and all four differ between filters).
        ns = list(range(n0, n0 + 4))
        if FOUND[fam]:                         # the resumed filter and next two
            nr = max(FOUND[fam]) + 1
            ns += [n for n in (nr, nr + 1, nr + 2) if n not in ns]
        for n in ns:
            unit = forced_unit(n, fam)
            eng = GpuEngine(n, fam, unit=unit)
            c = eng.config()
            if c["blocks_per_sm"] < OCC_MIN_BLOCKS4:
                return False, (f"G18 FAIL: {fam} n={n} unit {unit} compiles "
                               f"to {c['num_regs']} registers, "
                               f"{c['smem_bytes']} bytes of shared memory and "
                               f"{c['blocks_per_sm']} blocks per SM, under "
                               f"OCC_MIN_BLOCKS4 = {OCC_MIN_BLOCKS4}")
            got = cp.cuda.driver.funcGetAttribute(
                cp.cuda.driver.CU_FUNC_ATTRIBUTE_PREFERRED_SHARED_MEMORY_CARVEOUT,
                eng.k_sieve.kernel.ptr)
            if got != CARVEOUT_PCT or c["carveout"] != CARVEOUT_PCT:
                return False, (f"G18 FAIL: {fam} n={n}: the sieve kernel's "
                               f"carveout is {got}, not {CARVEOUT_PCT}")
            if eng.d_pat.nbytes > PAT_BYTES_MAX:
                return False, (f"G18 FAIL: {fam} n={n}: window tables of "
                               f"{eng.d_pat.nbytes} bytes exceed PAT_BYTES_MAX")
            if eng.occupancy["local_bytes"] > 0:
                return False, (f"G18 FAIL: {fam} n={n}: the sieve kernel "
                               f"spills {eng.occupancy['local_bytes']} bytes "
                               f"to local memory")
            rows.append(f"{fam} n={n}: {c['num_regs']} regs, "
                        f"{c['smem_bytes'] >> 10} KB, "
                        f"{c['blocks_per_sm']} blocks/SM, "
                        f"{len(c['groups'])} window groups, "
                        f"unit {unit}, wheel ({eng.p1},{eng.p2},{eng.p3}), "
                        f"q2 {eng.q2}, pb {eng.pb}")
    return True, (f"G18 ok: all {len(rows)} campaign configurations (four "
                  f"filters past each family's frontier, plus its resumed "
                  f"filter and the two after it, each PLANNED the way the "
                  f"campaign plans it) compile to >= "
                  f"{OCC_MIN_BLOCKS4} blocks per SM with no spills, the "
                  f"carveout pinned at {CARVEOUT_PCT}% and the window tables "
                  f"under {PAT_BYTES_MAX >> 10} KB: " + "; ".join(rows))


GATES = [g7_wheel_matches_oracle, g8_wheel_partitions_the_period,
         g13_production_wheel_constants, g14_engine_mechanisms,
         g9_gpu_matches_cpu, g15_k_off_representation,
         g16_third_level_mechanisms, g17_unit_wheel_matches_k_wheel,
         g18_every_opening_compiles_to_occupancy]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
