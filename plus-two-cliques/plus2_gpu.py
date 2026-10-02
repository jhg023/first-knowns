"""plus2_gpu.py -- the GPU engine for the +2 product cliques.

The same mathematics a third time, in CuPy, and shaped so that nothing it
shares with the CPU engine could hide a bug in either.

WHAT THE KERNEL DOES (v4, the WINDOW sieve).  The CPU engine materialises
the dense x line and marks arithmetic progressions into it.  This engine
never forms the line.  It carries a wheel index and reconstitutes

    x = W*j + r,        r congruent to a residue that no wheel prime kills

and then sieves the candidates of a fixed residue r across a SEGMENT of
PB consecutive wheel periods at once (`pb_for`).  For a fixed r the
candidates of consecutive periods form an arithmetic progression modulo
every sieve prime q with an invertible step (Wp mod q: q is above the wheel
and not in the unit), so "which of the PB periods does q kill" depends on
r mod q alone and is a PB-bit WINDOW into a periodic bit pattern stored
once per prime (`window_patterns`):

    Dinv = (Wp mod q)^-1,   r'' = r * Dinv mod q,
    q | W*(j0 + j) + r  - kr   <=>   (r'' + j) mod q  in  { kr * Dinv }

One window is ceil((NW + 1) / 2) aligned 64-bit loads from a table of
overlapping word pairs (v2; NW + 1 32-bit loads in v1) and NW funnel shifts
for 32*NW candidates, and r'' is linear in the CRT decomposition of r, so
per group per residue it is one add of a per-thread table value (x0), a
per-block value (ne, the launch base folded in as j0 mod q because
Wp*Dinv == 1) and the CRT borrow.  The sieve primes down to BIT_SURV
survival (0.35%) are tested this way; the survivors are extracted from the
live words (held in registers) into a shared queue as (residue, period) and
take the PER-CANDIDATE route -- the in-block compaction ROUNDS (Barrett
tests against packed tables, halving the queue each round down to
K2_SURV4) and then the global TAIL ROUNDS over queues with several lanes
per item.  Every push into a queue is ONE shared atomic per warp
(`warp_reserve`).

Everything problem-specific enters through `killed_residues(q, n, fam,
unit)`: the wheel tables, the window patterns, the x0 table, the round
tables, the tail's masks and residue lists and the survival curve the
compaction points are derived from are all built from that one function,
so the same code sieves every family -- and the same code sieved
product-cliques' a(n)*a(i) + 1, whose kill sets differ from these only in
the constant (-a(i)^-1 there, -2*a(i)^-1 here).

THIS PROJECT'S v1 IS product-cliques' ENGINE v2 AND PLANNER p3, TAKEN WHOLE
(2026-10-01).  The kernel is not touched: it never sees a form, only the
residues each prime kills, so changing the constant from one to two is a
change to `killed_residues` and nothing here.  What DID change, and is
gated here rather than assumed, is the class: x == 3 (mod 6), not 0, so the
host map x = r0 + unit*t runs with r0 != 0 for the first time (G9, G13,
G15, G17 pin it).  Product-cliques' engine history, for the record of where
the constants came from: v1 was clique-ladders' v1 (factorial-ladders' v3
window sieve, the 2^64 reduction bound, the wide survivor record, subset
wheels, planner p2 by expected clock to a confirmed find) with the tail's
residue list sized from `maxkills`; and its v2 (round 1, 2026-09-29;
product-cliques/OPTIMIZATION_LOG.md) was measured on that project's
filters: the window is read
from a table of OVERLAPPING PAIRS in 64-bit shared loads (WINDOW_LDS64 --
the window loop is bound by shared-load ISSUE on this GPU, and a pair costs
what a word costs), its word index taken on the multiply pipe
(WINDOW_ADDR_MUL), its live words kept in registers for the extraction
(EXTRACT_REGS), the narrow rounds reduced once per pack of primes
(ROUND_MOD32), the window and round depths re-swept (BIT_SURV, K2_SURV4,
with LIT_MAX and K2_ROUND_PRIMES_MAX bounding them where few conditions
would run them away), and the planner's width curve and block shapes
re-measured, which moved every plan to 160-period windows.  The constants
were RE-SWEPT on this project's own filters (OPTIMIZATION_LOG.md round 1),
and a comment that quotes another project's filter ("at n = 21 of A093483",
"A078502", "n = 19* of A034881") is that number's provenance, not a claim
about this project.

ENGINE v2 (round 2, 2026-10-01) is this project's own, measured on its own
filters with Nsight Compute and ablations before anything changed: the sieve
kernel is bound by LSU issue (85-86% of peak) with the window's loads exactly
at their ideal wavefront count, so everything changed is outside the window
-- the narrow rounds' reductions lazy over tripled tables (ROUND_LAZY), one
u32 per queue entry on the narrow record (QWORD), the window's x0 and ne
packed two groups to a word (NEPACK: 88 -> 72 registers, a sixth block), the
block offsets built once per launch instead of once per block (PRE_TABLE),
and xe kept at 2 unless 1 buys a block (XE1_REGS).  The SAME survivor
stream: every fingerprint reproduced, and G21 and G22 pin the two new
mechanisms.  1.09-1.15x on the expected clock at every filter the campaigns
spend hours or days in (OPTIMIZATION_LOG.md round 2).

ENGINE v3 (round 3, 2026-10-02) was measured where the campaign stood: the
live filter, A083518 n = 20 on its real terms (the wheel to 59 less 41, the
wide record).  Nsight Compute on v2 there: the LSU data pipe at 87% of its
peak in wavefronts, five blocks per SM for want of 54 bytes of shared
memory, and the wide rounds' per-residue rows the largest table on the
device and the worst-coalesced load in the kernel.  Four changes, the SAME
survivor stream on the same plan and the same launches: a window prime up to
96 repeats inside the window, so three of its five words are read and two
are funnel shifts of those (WINDOW_PERIODIC), from one 16-byte load
(WINDOW_QUAD); the wide record's rounds run the narrow record's lazy Barrett
packs with the period folded into each pack's numerator (ROUND_FOLD), which
retires 3 GB of rows and buys the sixth block and the u32 queue entry; and
the first tail rounds are generated with their primes as literals
(TAIL_LITERAL).  1.10x at the live filter, 1.04-1.12x at every filter
measured (OPTIMIZATION_LOG.md round 3); G14, G20, G21 and G22 pin the new
mechanisms.

CLASS SPACE.  The forced primes pin x to ONE residue class, x == r (mod u)
(plus2_search.forced_class).  Here the class is x == 3 (mod 6) from
A083518's index 4 and A083519's index 3 -- x odd, because a*x + 2 == x
(mod 2), and x == 0 (mod 3), because the terms kill both other classes; no
prime past 3 is ever forced (plus2_reference G2c, G2d) -- and the
machinery sweeps a general class: the
device runs t with x = r0 + unit*t, the kill sets carried through the map
(K'(q) = (K(q,n,F) - r0) * unit^-1 mod q) and the unit's primes left out of
the wheel.  Everything the device touches is in t; `self.W` (the period),
the survivors and every bound check are in x, and `_collect` is the one
place the map is applied.  Because 0 <= r0 < unit, x < j*W exactly when
t < j*W' (r0 + unit*t < unit*j*W' iff t < j*W' - r0/unit, and r0/unit is in
[0, 1)), so the periods of x and of t share their boundaries and no cursor
changes meaning -- with r0 = 3 as much as with product-cliques' 0.  `unit = 1` is the x-space engine, and the gate battery
runs it on wheels a dense CPU sieve can follow.  `assert_unit` refuses a
unit with a prime that is not forced at the filter, or not squarefree,
which is the one way this could thin the line.

ONE LINE, A FILTER THAT IS STATE.  The published term is x itself, so every
filter sweeps the same line.  But the form list at index n is built from
a(off..n-1) (plus2_reference.forms; off is the entry's %O offset, 0 in
A083519), so an engine exists only for an index
whose prefix is known -- building one past it raises -- and the kernel
cache is keyed on the FAMILY as well as n, because the kill sets are
literals in the kernel source.  K(q,n) is a subset of K(q,n+1); the wheel,
the class, the period and the window are all PLANNED per filter
together (`plan`: `wheel_candidates` x the window widths, with `plan_q2`
per wheel) and never stored -- chosen to minimise the expected clock to a
CONFIRMED find, because a find restarts the sweep and the rest of its
segment is thrown away.

THE SEGMENT IS THE COVERAGE UNIT.  `sweep(j0, j1)` covers periods [j0, j1)
in segments of `seg_periods` (PB, or several PB-windows batched on a
small wheel), each segment in `launches_per_segment` launches of a
first-level chunk x a few third-level residues x every second-level
residue x every period of the segment; the cursor it yields is (segment
start, launches done), and a partial last segment is masked by period.
A window may start inside period 0: `sweep` and `survivors_j` take
`k_min` and the host drops every survivor below it, which is exact.

CEILINGS, stated and enforced (CONVENTIONS.md "Numeric hygiene"):
  * x < k_ceil(n, F) = plus2_search.K_CEIL_PLUS2 = 1e30 for both families
    (G10) -- MEASURED, not rule 5h's default: no value here has multiplier x
    term +- 1 structure, so a discovery is proved by a bounded certificate
    search on N -+ 1, and 1e30 is the last height at which that search was
    measured to land on a find's largest values (OPTIMIZATION_LOG.md
    Measurement 1).
  * THE SURVIVOR RECORD, in one of two forms the engine chooses at build
    time from the wheel and window it is handed (v3).  NARROW: the u64
    offset within the launch, exact while (seg_periods + 1) * W' + q2 <
    2^64 = REDUCE_MAX -- one conditional subtraction after the Barrett
    step is exact for EVERY u64 (the bound is 2^64, not the 2^63 the
    engine shipped with: OPTIMIZATION_LOG.md round 2, the paper bound, the
    bit-exact emulation and the tripwire in G19), which admits 179
    periods on the wheel to 47 (W' = 1.0e17).  WIDE: (within-period
    offset, period), bounded by W' + q2 < 2^64 alone, so the wheel may be
    longer than any u64 window admits -- the wheel to 53 (W' = 5.4e18)
    from n = 18.  The wide record costs 5-6% where the narrow one would do
    (round 3), so it is taken only where the wheel demands it (`wide`,
    WIDE_MIN_PV); G19 pins the two records to each other on one wheel and
    G20 the wide 53-wheel to the narrow 47-wheel over one 53-period.
  * W1 < 2^32, so the first-level table is u32; W2 < 2^32 and
    W1*W2 < 2^63.
  * the unit is forced at the filter (assert_unit), or the engine
    refuses to build; the filter's MAXKILLS (one per form here) fits the
    NRES_MAX-slot residue list.

Gates here: G7 (both wheel constructions == the oracle's brute-force
period walk, in x space and in class space), G8 (the wheel partitions the period: the
count is the formula and no kept residue is killed), G9 (GPU survivor
stream == CPU survivor stream, bit for bit, on populated windows at several
heights, filters and families, one-, two- and three-level, x space and
class space (3 mod 6), including above 2^64, hard against the 1e30
ceiling, and a CLIPPED PERIOD 0), G13 (the production wheel constants of every filter),
G14 (the generation tables, the derived compaction depths, the round
tables, THE WINDOW CHAIN -- x0, ne, borrow, pattern word -- against
killed_residues on sampled candidates, and the queue-overflow fallback; and, v3,
the window's words as the KERNEL forms them -- the periodic plan, on pairs
and on quads -- equal to the plain pattern at every position of every group),
G15 (the (x, off) representation: the stream is invariant under the launch
decomposition and under a split inside a segment, the tail's masks and
residue lists, and the folded scalars), G16 (the third level: the global
tail queue's overflow, chunking, and the power-of-two queue index), G19
(the 2^64 reduction bound: a bit-exact host emulation with a tripwire past
2^64, the stream identical across window widths where offsets pass 2^63,
and the clamp exactly at the bound), G20 (a non-contiguous level split on
both records == the CPU engine, and at every open index the planned wheel
takes the wide record exactly when no u64 window admits its period), G17
(the production unit wheel, a differently split one, a coarser one and an
x-space wheel return identical survivors over the same absolute windows),
G18 (every campaign configuration compiles to the occupancy the engine was
tuned at, no spills, the carveout pinned and the window tables inside their
cap), G21 (the lazy narrow rounds: a bit-exact host emulation of every pack,
the engine's own tripled tables, a tripwire past the 2^31 pack bound, and
the device stream lazy == corrected; v3: the wide record's folded packs and
the generated tail rounds' packs emulated the same way, each with its own
tripwire, and the device stream folded == window rounds and generated ==
generic tail rounds), G22 (the per-launch offset table ==
the definition row for row, narrow, wide and batched, and the device stream
with the table == with the in-block prologue).
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
from plus2_reference import (FAMILIES, FOUND, KNOWN, family,  # noqa: E402
                              forbidden_k_residues, frontier, maxkills,
                              nforms,
                              term, w_count, wheel_residues)
from plus2_search import (Q2_DEFAULT, CpuEngine, assert_unit,  # noqa: E402
                           forced_unit, k_ceil, k_floor, killed_residues,
                           unit_residue)

# The two families the mechanism gates run on: FA = A083518, offset 1, the
# deeper prefix (open index 14); FB = A083519, OFFSET 0, open index 11 -- so
# every FA case names an index <= 14 and every FB case one <= 11.  Both force
# the unit 6, in the class 3, from FA's n = 4 and FB's n = 3.
FA, FB = "A083518", "A083519"

# THE X-SPACE WHEEL (unit = 1).  Kept as the defaults of this class because
# the x-space benchmark shapes and most of the gates run on it; the
# CAMPAIGN runs the class-space wheel `plan` chooses below.
P1_DEFAULT = 23              # first-level wheel: the primes up to here
P2_DEFAULT = 37              # second-level wheel: the primes in (P1, P2]
# THIRD-level wheel: the primes in (P2, P3].  47 IS THE LAST ONE, and not
# by choice: m is a u32 and W1*m is what the one-conditional-subtraction
# reduction bounds, so the combined second modulus must stay under 2^32.
# Primes to 47 make it 2.76e9; adding 53 makes it 1.46e11.  The engine
# raises rather than wrapping.
P3_DEFAULT = 47
# THE WHEEL IS RE-CHOSEN AT EVERY FILTER, and stored nowhere.
#
# The forced class is 3 (mod 6) at every index a campaign runs, and the
# kill sets grow with every term: K(q,n) is a subset of
# K(q,n+1), so the residues kept per level, the period W' and how many
# periods fit under 2^64 all change from filter to filter.  And the SEARCH
# changes: a find is only known to be the least once its SEGMENT closes,
# and a segment longer than the search over-sweeps more than its wheel
# buys, so the early filters run short wheels and the long ones arrive as
# the modelled search outgrows their periods.  `plan` prices that trade
# and `launch.py` never stores one.
#
# What the plan has to satisfy, all enforced in GpuEngine.__init__:
#   W1 < 2^32 (the first-level residue type is baked into the kernel),
#   W2 < 2^32 and W1*W2 < 2^63 (the one-subtraction reduction),
#   R2, R3 <= 65535 (they ride gridDim.y and .z),
#   (PV + 1) W' + q2 < 2^64 with PV >= PV_MIN (the window has to be worth
#   having: a wheel that admits eight periods spends the whole window
#   mechanism on eight bits).
# and what it optimizes is the expected clock to a confirmed find (`plan`);
# candidates per unit of line, prod(w-kept)/W', is one factor of that.
PV_MIN = 32
# The narrow record is kept whenever it admits this many periods: past it
# the window is worth under 2% (179 -> 224 measured 1.00-1.02x) while the
# wide record costs 5-6% (OPTIMIZATION_LOG.md round 3).
WIDE_MIN_PV = 128
# The first-level table is R1 entries and the x0 table is R1 per window
# group, so R1 is the memory the plan spends.  2^21 is ~50 MB of x0 at 12
# groups; the plan will take a denser wheel over a bigger table only when it
# actually buys candidates.
R1_MAX = 1 << 21
# ... AND A SECOND BUDGET, ONLY FOR A WHEEL THAT NO SPLIT UNDER R1_MAX ADMITS
# (plus-two-cliques round 1, 2026-10-01).  The full wheel to 53 has W' =
# 5.4e18, so W1 and W2 can both stay under 2^32 only if W1 is past ~1.3e9 --
# most of the small primes in the first level -- and that is 8.45 million
# first-level residues at n = 20* of A083518: past 2^21, and past 2^23.
# Measured there, paired, against the planned wheel to 47 (OPTIMIZATION_LOG.md
# round 1): 1.225x on the line, 1.097x on the expected clock to a confirmed
# find.  RAISING R1_MAX instead is what product-cliques priced and declined
# (its round 1, "Priced and unbuilt" 1), because the planner then prefers the
# largest first level EVERYWHERE and re-splits wheels that were fine (here:
# every filter from A083518's opening, ties at best where measured).  So the
# budget below applies only where R1_MAX admits no split of a wheel at all,
# every plan R1_MAX could make is the plan it made, and the new candidates
# are the long wheels nothing else can reach.  Its tables are ~1 GB of
# device memory at 8.45M residues (G9 runs a first level of this size
# against the CPU engine).
R1_MAX_BIG = 1 << 24
# The largest prime the wheel will consider.  Above this the value density is
# far below what is already in and the enumeration gets slower for nothing.
WHEEL_TOP = 89

# THE SIEVE DEPTH IS PLANNED TOO, AND IT IS A LOAD DECISION.
#
# q2 trades device time against HOST time, and the sweep that measures only
# throughput cannot see the second (OPTIMIZATION.md rule 7).  lcm-ladders
# measured the device rate FLAT over a factor of eight in q2 while the host
# cost moved 16x, so "fastest" does not decide this and the load budget does
# (CONVENTIONS.md "Sizing a hunt", step 3: when two settings tie on
# throughput take the one that asks for less machine).  What the depth is
# chosen from is therefore the SURVIVOR RATE, and the target is set where
# two workers keep up with margin.  Inherited from that project; the pool
# is sized from a MEASUREMENT at each filter regardless (launch.py), so a
# target that is wrong here costs machine, not coverage.
#
# It cannot be a constant, because the survivor rate per candidate at a
# fixed q2 moves an order of magnitude between filters -- w(q,n) ~ n for
# every q well above the wheel and n is in the exponent.  So the campaign
# plans it: the smallest depth whose ANALYTIC survival is under the target,
# and the ladder's top if none reaches it.  THE LADDER STOPS AT 2^20: at
# n = 11..13 the survival never reaches the target (1.2e-6 at n = 11 even
# at 2^20), and the tail's per-prime tables are 512 bytes each, so 2^24
# would be 550 MB of masks for filters that are seconds of work anyway.
SURV_TARGET = 5e-8
# ... AND FIVE TIMES DEEPER WHERE DEPTH WAS MEASURED TO BE FREE.  The rule
# above says a tie on throughput goes to the setting that asks for less
# machine, and the inherited target stopped at "two workers keep up".  Swept
# here at six filters of 17 to 21 forms (the open indices of A093483 and
# A103828, stand-in filters n = 17 to 22; paired, interleaved, three rounds;
# OPTIMIZATION_LOG.md round 1), the device pays 0.3-0.6% for the rung or two
# that take the survivors under 1e-8 per candidate:
#
#   A093483 n = 18   2^15 -> 2^17   0.995   4.6e-8 -> 5.4e-9 survivors/cand
#   A103828 n = 19   2^15 -> 2^16   0.997   2.8e-8 -> 8.9e-9
#   A093483 n = 20   2^14 -> 2^16   0.994   4.3e-8 -> 3.4e-9
#   A093483 n = 21   2^14 -> 2^15   0.998   2.8e-8 -> 7.0e-9
#   A119752 n = 17   2^16 -> 2^17   0.997   2.3e-8 -> 8.0e-9
#   A093483 n = 22   2^14 -> 2^16   0.994   1.7e-8 -> 1.1e-9 (wide record)
#
# which is 130,000 survivors a second becoming 15-25,000: 1.3 core-seconds
# per second and a pool of three becoming 0.2 and ONE worker, for days.  The
# whole pipeline measured 1.000 of the device at either depth, so this buys
# machine, not rate.  NOT below 17 forms: there an octave of depth removes
# less (the survival falls as (ln d / ln 2d)^forms) and the launches are
# milliseconds, so the tail's extra rounds are a visible fraction of each --
# 0.948 per rung at n = 15 of A119752 (15 forms), for filters that last one
# segment.  Deeper still is priced and declined: 2^18-2^19 costs 1-3% to
# take the last worker inline.
SURV_TARGET_DEEP = 1e-8
DEEP_FROM_FORMS = 17
Q2_LADDER = tuple(1 << e for e in range(12, 21))


@_lru_cache(maxsize=None)
def plan_q2(n, fam, unit, wheel, target=None, ladder=Q2_LADDER):
    """The smallest depth in `ladder` whose analytic survivors-per-candidate
    is at or under `target` (by default SURV_TARGET_DEEP from
    DEEP_FROM_FORMS conditions up, SURV_TARGET below); the deepest rung if
    none reaches it.

    Analytic, not measured: survival through the sieve is a deterministic
    product over the primes involved (OPTIMIZATION.md 2.6), and it matched
    the measured survivor rate to better than 2% at every opening here.
    """
    fam = family(fam)
    unit = int(unit)
    if target is None:
        target = (SURV_TARGET_DEEP if nforms(fam, n) >= DEEP_FROM_FORMS
                  else SURV_TARGET)
    # w_count, not len(killed_residues): they are equal for every q that
    # does not divide the unit (plus2_reference G2b proves the count
    # against both the residue count and direct divisibility, and G3 proves
    # the unit does not change the SIZE), and the count is n multiplications
    # where the other is n modular inversions.  And primerange is walked
    # LAZILY, rung by rung, never materialised to the top of the ladder.
    #
    # THE WALK IS SHARED BETWEEN WHEELS.  `plan` prices a dozen candidate
    # wheels per filter, and a walk per wheel to the top of the ladder was
    # 3-6 s of planning at the filters whose survival never reaches the
    # target (82,000 primes x n multiplications, a dozen times).  The
    # survival through EVERY prime outside the unit is walked once per
    # (filter, rung) and a wheel's own primes are divided back out -- each
    # factor is at least 1/q, never zero, at an admissible filter.
    wheel_keep = [(int(q), 1.0 - w_count(int(q), n, fam) / int(q))
                  for q in wheel if unit % int(q)]
    for i, d in enumerate(ladder):
        surv = _rung_survival(n, fam, unit, tuple(ladder), i)
        for q, keep in wheel_keep:
            if q <= d:
                surv /= keep
        if surv <= target:
            return d
    return ladder[-1]


_RUNGS = {}


def _rung_survival(n, fam, unit, ladder, i):
    """prod(1 - w(q,n)/q) over every prime q <= ladder[i] outside the unit,
    extended lazily one rung at a time and kept per (filter, ladder)."""
    got = _RUNGS.setdefault((int(n), fam, int(unit), ladder), [])
    while len(got) <= i:
        lo = ladder[len(got) - 1] if got else 1
        surv = got[-1] if got else 1.0
        for q in primerange(lo + 1, ladder[len(got)] + 1):
            if unit % q:
                surv *= 1.0 - w_count(q, n, fam) / q
        got.append(surv)
    return got[i]


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
    unit = int(unit)
    return tuple((q, (q - w_count(q, n, fam)) / q)
                 for q in primerange(2, top + 1) if unit % q)


def _split_rest(rest, W1, R1):
    """The best contiguous (level 2, level 3) cut of the sorted `rest`
    behind a first level of modulus W1 and R1 residues, as
    ((R1, -|R2 - R3|), level2, level3), or None."""
    m = len(rest)
    best = None
    for j in range(0, m + 1):
        W2a = R2 = 1
        for q, k in rest[:j]:
            W2a *= q
            R2 *= q - int(round(q * (1 - k)))
        if R2 > 65535 or W2a >= 1 << 32:
            break
        W2b = R3 = 1
        for q, k in rest[j:]:
            W2b *= q
            R3 *= q - int(round(q * (1 - k)))
        if R3 > 65535 or W2b >= 1 << 32:
            continue
        if W2a * W2b >= 1 << 32 or W1 * W2a * W2b >= 1 << 63:
            continue
        cand = (R1, -abs(R2 - R3))
        if best is None or cand > best[0]:
            best = (cand, tuple(q for q, _ in rest[:j]),
                    tuple(q for q, _ in rest[j:]))
    return best


def _split_levels(qs, r1_max, smallest=False):
    """Partition the sorted primes `qs` into three CRT levels satisfying every
    bound the kernel's arithmetic rests on, or None.

    The levels are CONTIGUOUS in the sorted subset when a contiguous split
    satisfies the bounds -- a search over two cut points, taking the split
    with the largest first level inside R1_MAX (the first level is one
    thread per residue, so a small R1 starves the launch's x dimension).
    When no contiguous split does, the first level may be ANY subset (the
    CRT lift only needs coprime moduli; contiguity was a convention): the
    wheel to 53 at unit 6 has W' = 5.4e18, and the only way to hold both
    W1 and W2 under 2^32 is {5..23, 37} x {29, 31, 41} x {43, 47, 53}
    (OPTIMIZATION_LOG.md round 3).  Contiguous first, so the splits of the
    wheels the campaign measured do not move.

    `smallest` takes the SMALLEST first level instead, and is what the
    second budget (R1_MAX_BIG) asks for: a wheel that needs it has millions
    of first-level residues whichever split it takes, which saturates the
    launch already, and every further residue is x0-table memory (one entry
    per window group) for nothing.  At n = 20* of A083518 the largest split
    is 16.7 million residues and the smallest 8.45 million.
    """
    rank = (lambda c: (-c[0], c[1])) if smallest else (lambda c: c)
    m = len(qs)
    best = None
    for i in range(1, m + 1):
        W1 = R1 = 1
        for q, k in qs[:i]:
            W1 *= q
            R1 *= q - int(round(q * (1 - k)))
        if W1 >= 1 << 32 or R1 > r1_max:
            break
        got = _split_rest(qs[i:], W1, R1)
        if got is not None and (best is None
                                or rank(got[0]) > rank(best[0])):
            best = (got[0], i, len(qs[:i]) + len(got[1]))
    if best is None:
        # the subset search: a DFS over first-level subsets under 2^32
        # (pruned on the product, so a few thousand of the 2^m), each with
        # the contiguous cut of what it leaves
        found = None

        def dfs(idx, chosen, W1, R1):
            nonlocal found
            if chosen:
                rest = [qk for t, qk in enumerate(qs) if t not in chosen]
                got = _split_rest(rest, W1, R1)
                if got is not None and (found is None
                                        or rank(got[0]) > rank(found[0])):
                    found = (got[0], tuple(qs[t][0] for t in sorted(chosen)),
                             got[1], got[2])
            for t in range(idx, m):
                q, k = qs[t]
                W1n = W1 * q
                R1n = R1 * (q - int(round(q * (1 - k))))
                if W1n >= 1 << 32 or R1n > r1_max:
                    continue
                dfs(t + 1, chosen + [t], W1n, R1n)
        dfs(0, [], 1, 1)
        if found is None:
            return None
        _c, l1, l2, l3 = found
        if not l2 and l3:
            l2, l3 = l3, ()
        return (l1, l2, l3)
    i, j = best[1], best[2]
    # An EMPTY MIDDLE LEVEL with a non-empty third is the same wheel as a
    # two-level split, and GpuEngine builds levels in order -- a third level
    # behind an absent second is dropped from the wheel AND left out of the
    # sieve (self.primes is the complement of all three levels), so those
    # primes would go untested.  The search reaches this shape at the short
    # wheels of the opening filters (n = 11: (5..23), (), (31,)); normalise
    # it here rather than teach three call sites to expect it.  G13 builds
    # every planned wheel level by level and failed on the raw shape.
    if j == i and j < m:
        j = m
    return (tuple(q for q, _ in qs[:i]), tuple(q for q, _ in qs[i:j]),
            tuple(q for q, _ in qs[j:]))


@_lru_cache(maxsize=None)
def wheel_candidates(n, fam, unit, r1_max=R1_MAX, top=WHEEL_TOP,
                     r1_big=R1_MAX_BIG):
    """Every wheel the kernel admits at filter n of family F, as
    (([level 1], [level 2], [level 3]), W', density), shortest first.

    THE WHEEL IS A SUBSET OF THE PRIMES, NOT A PREFIX OF THEM (inherited
    from lcm-ladders, where it was worth 1.2-1.8x).  Every prime in the
    wheel multiplies the PERIOD by q and the candidate density by
    keep(q) = (q - w(q,n))/q, and the two need not move together: here a
    small prime saturates near (q - 1)/2 kept classes (no two terms may sum
    to -1 mod q) while a prime above 2n keeps q - n + 1, so the order of
    value is close to the order of size but is not assumed to be.

    So the subsets are the GREEDY ones by value density,
    -log(keep(q)) / log(q): the best k primes for every k whose period
    fits the bounds.  Which of them the campaign runs is `plan`'s decision,
    because a longer wheel is also a longer segment.

    The bounds, all enforced:
      * W1 < 2^32, W2 < 2^32, W1*W2 < 2^63 (the kernel's arithmetic);
      * R2, R3 <= 65535 (they ride gridDim.y and .z), R1 <= r1_max;
      * W' < 2^63: the record bounds the PERIOD alone (the wide record, v3),
        and W' + q2 < 2^64 is checked where the depth is known.
    """
    fam = family(fam)
    unit = int(unit)
    vals = _wheel_value(n, fam, unit, top)
    order = sorted(vals, key=lambda z: math.log(z[1]) / math.log(z[0]))
    out = []
    for k in range(1, len(order) + 1):
        sel = sorted(order[:k])
        Wp, dens = 1, 1.0
        for q, keep in sel:
            Wp *= q
            dens *= keep
        if Wp >= 1 << 63:
            break
        lv = _split_levels(sel, r1_max)
        if lv is None and r1_big > r1_max:
            # the second budget: only a wheel r1_max cannot split at all
            lv = _split_levels(sel, r1_big, smallest=True)
        if lv is not None:
            out.append((lv, Wp, dens))
    return tuple(out)


# THE PLAN IS PRICED IN EXPECTED CLOCK TO A CONFIRMED FIND (planner p2).
#
# The inherited planner maximised candidate DENSITY under a hard cap
# (segment <= one modelled median) and then took the widest window the cap
# left.  Both halves were priced in factorial-ladders, where a promotion
# CARRIES the classified line, so an over-sweep is the next filter's work
# done early.  Here a find RESTARTS the sweep (the new index has a condition
# the old filter never tested), so everything past the find in its segment
# is thrown away -- and, separately, density is not rate: the candidate rate
# falls to two thirds at a 32-period window.  Measured on stand-in filters
# (OPTIMIZATION_LOG.md round 1): at n = 21 of A093483 the old plan took the
# wheel to 53 on a 32-period window, 1.62e17 x/s with a segment of 0.92
# medians, where the wheel to 47 at 128 periods runs 2.36e17 x/s with a
# segment of 0.07 -- 1.46x in rate and a find confirmed 1.7 hours sooner.
#
# So a plan is now the (wheel, window) minimising
#
#     plus2_model.expected_sweep(segment)  x  density(wheel) / crel
#
# -- the expected line swept until the segment holding a(n) closes, times
# the device seconds per unit of line -- over every greedy wheel subset the
# kernel's bounds admit and every window width.  `crel`, the relative
# candidate rate, is MEASURED, paired and interleaved on clique-ladders'
# filters (n = 19 of A093483, A103828 and A037100 on the wheels to 41 and
# 43, n = 20 to 22 of A093483 on the wheels to 43, 47 and 53), and has three
# factors:
#   * the window's WIDTH (CREL_WIDTH): two thirds at 32 periods, flat from
#     96 since the block shape follows the width (BLOCK_SHAPES_BY_NW);
#   * the window's DEPTH, 1 / lit: the kernel is the window sieve and its
#     cost is per prime, and a wheel that takes 47 takes the sieve's
#     strongest killer, so the window needs a prime or two more to reach
#     BIT_SURV (OPTIMIZATION.md 2.8's second price of a wheel prime).
#     Measured 0.90 for 27 groups against 25 and 0.935 for 27 against 26;
#     the first version of this model left it out and mis-ranked the wheel
#     to 47 over the wheel to 43 at n = 20 by 6%;
#   * the RECORD: the wide record costs 0.90-0.96 across widths once the
#     depth is separated out (CREL_WIDE).
# The cost model GENERATES the plan; the evidence that a plan is right is
# the paired measurement of it against its neighbours at every opening
# (same log).
#
# RE-MEASURED ON THE PAIRS WINDOW (product-cliques round 1, 2026-09-29), and
# the curve changed shape: a window of NW words costs ceil((NW + 1) / 2)
# loads a prime, so the ODD word counts are the cheap ones and 128 periods,
# the inherited optimum, is now a trough.  Candidates/s against 128, each
# width at its BLOCK_SHAPES_BY_NW shape, paired, at n = 18* and 19* of
# A034881 and n = 18* of A219761:
#   32 0.70   64 0.82-0.87   96 0.975   128 1.000   160 1.11-1.12
#   192 1.10   224 1.117
# (the inherited curve, for the record: 0.665 / 0.858 / 0.952 / 1.000 /
# 0.985 / 1.02 / 1.06).  A window the narrow record CLAMPS (pv live periods
# of pb) costs a full window for pv periods: CREL_WIDTH[pb] * pv / pb --
# 160 periods clamped to 157 at n = 19* measured 1.122 (the formula says
# 1.09; the inherited constant said 0.981).  The wide record, same window,
# same filter: 1.025 against 1.122, CREL_WIDE 0.91.
CREL_WIDTH = {32: 0.70, 64: 0.84, 96: 0.975, 128: 1.000, 160: 1.115,
              192: 1.10, 224: 1.117}
CREL_WIDE = 0.91


def window_depth(n, fam, unit, wheel, target=None):
    """How many sieve primes the window takes on `wheel`: the strongest
    killers outside the wheel and the unit, until the analytic survival is
    at or under BIT_SURV -- the engine's own rule (GpuEngine.lit), on the
    primes under 1024, which is where every window prime lives (G18 pins
    the two to each other at every planned configuration)."""
    fam = family(fam)
    unit = int(unit)
    target = BIT_SURV if target is None else float(target)
    wset = frozenset(int(q) for q in wheel)
    keeps = sorted(((q - w_count(q, n, fam)) / q, q)
                   for q in primerange(2, 1024)
                   if unit % q and q not in wset)
    surv = 1.0
    for i, (keep, _q) in enumerate(keeps):
        if surv <= target or i >= LIT_MAX:
            return i
        surv *= keep
    return min(len(keeps), LIT_MAX)


def _record_for(Wp, q2, pb):
    """(wide, pv): the record and the live periods GpuEngine takes for a
    window of `pb` periods on a wheel of period Wp -- the one rule, shared
    by the planner and the engine."""
    maxp = (REDUCE_MAX - int(q2)) // int(Wp) - 1
    wide = pb > maxp and maxp < WIDE_MIN_PV
    return wide, (int(pb) if wide else int(min(pb, maxp)))


@_lru_cache(maxsize=None)
def plan(n, fam, unit, r1_max=R1_MAX, top=WHEEL_TOP, r1_big=R1_MAX_BIG):
    """(p1, p2, p3, q2, pb): the wheel, the sieve depth and the window at
    filter n of family F, chosen together (see above).  Pure and cached: a
    function of the prefix a(1..n-1) alone, so a resumed campaign derives
    the identical plan, and the launcher still asserts W and the segment on
    load (OPTIMIZATION.md 2.9)."""
    import plus2_model as _model
    fam = family(fam)
    unit = int(unit)
    floor_x = term(fam, int(n) - 1)
    best = None
    for lv, Wp, dens in wheel_candidates(n, fam, unit, r1_max, top,
                                         r1_big):
        q2 = plan_q2(n, fam, unit, _wheel_primes(*lv))
        if Wp + q2 >= REDUCE_MAX:
            continue
        lit = window_depth(n, fam, unit, _wheel_primes(*lv))
        W = unit * Wp
        start = (floor_x // W) * W
        for pb in range(PV_MIN, PB_DEFAULT + 1, 32):
            wide, pv = _record_for(Wp, q2, pb)
            if pv < 1 or pb - pv >= 32:
                continue            # a whole dead word: the width below
            crel = CREL_WIDTH[pb] * pv / pb
            if wide:
                crel *= CREL_WIDE
            crel /= max(lit, 1)
            line = _model.expected_sweep(fam, n, floor_x, start, pv * W)
            clock = line * dens / crel
            # ties go to the shorter segment: a find is confirmed sooner
            cand = (clock, pv * W)
            if best is None or cand < best[0]:
                best = (cand, lv, q2, pb)
    if best is None:
        raise ValueError(f"no admissible plan at n = {n} of {fam} with unit "
                         f"{unit}: the kernel's bounds leave no wheel")
    (p1, p2, p3), q2, pb = best[1], best[2], best[3]
    return p1, p2, p3, q2, pb


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

# THE ONE-CONDITIONAL-SUBTRACTION REDUCTION IS EXACT FOR EVERY u64, so the
# bound is the word: 2^64, not the 2^63 this engine shipped with (and its
# three predecessors carried) -- which halved the window on the full wheel
# for nothing.  Paper bound (OPTIMIZATION_LOG.md round 2): with
# mg = floor(2^64 / q) = (2^64 - rho) / q, rho = 2^64 mod q in [0, q), and
# off = a*q + b,
#     off * mg / 2^64 = a + b/q - off*rho/(q*2^64),
# and the last term is below rho/q < 1 for every off < 2^64, so
# floor(off * mg / 2^64) is a or a - 1 and off - q*floor(...) is b or b + q:
# below 2q, one conditional subtraction is exact.  G19 emulates it bit for
# bit at every prime of the ladder on offsets up to 2^64 - 1, shows it
# WRONG at 2^64 + x (the bound is real), and pins the stream across window
# widths on the full wheel where offsets above 2^63 occur.
# The reduced quantity is the OFFSET within a launch, so the bound is on
# W' * per_launch -- a property of the WHEEL AND THE BATCHING, which the
# engine chooses, and not of k.  Checked per engine in __init__.
REDUCE_MAX = 1 << 64

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
    # the wheel here is a SUBSET of the primes, not a prefix (wheel_candidates says
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
               hoist=None, unit=1, wide=False, reps3=False):
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
    (THREE times with `reps3`, for the lazy narrow rounds, whose remainder
    is not corrected below Q) and the launch passes `2Q-block base +
    (base mod Q)`; an inline
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
            # the in-block rounds.  WIDE: the candidate is (offp, jj), and
            # the group's per-launch table jb2[gi*PV + jj] = (jj*W' + base)
            # mod Q is added after the Barrett step -- the base and the
            # period both leave the per-candidate arithmetic, and the
            # doubled table (or a conditional subtraction for an inline
            # mask) absorbs the sum, which is below 2Q.  Narrow: v2's form,
            # the base folded on the host into the scalar parameter.
            head = (" " * indent + "{ unsigned int r = (unsigned int)offp - "
                    f"(unsigned int)__umul64hi(offp, {mg}ULL) * {Q}u; "
                    f"if (r >= {Q}u) r -= {Q}u; "
                    + (f"r += jb2[{gi} * PV + jj]; " if wide else ""))
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
            if hoist is None and wide:
                lines.append(head + f"if (r >= {Q}u) r -= {Q}u; "
                                    f"kill |= (unsigned int)(({mask}ULL >> r) "
                                    f"& 1ULL); }}")
            else:
                lines.append(head + f"kill |= (unsigned int)(({pname}{gi} >> r) "
                                    f"& 1ULL); }}")
            descs.append(("inline", Q, mask))
            continue
        single = hoist is not None
        # THREE copies for the lazy narrow rounds (ROUND_LAZY): the lookup
        # is at base + r with base < Q and the uncorrected r < 2Q
        reps = (0,) if single else ((0, Q, 2 * Q) if reps3 else (0, Q))
        tab = np.zeros((len(reps) * Q + 31) // 32, dtype=np.uint32)
        idx = np.arange(Q)
        for q in qs:
            bad = np.array(killed_residues(q, n, fam, unit), dtype=np.int64)
            b = np.nonzero(np.isin(idx % q, bad))[0]
            for rep in reps:
                br = b + rep
                np.bitwise_or.at(tab, br >> 5,
                                 (np.uint32(1) << (br & 31)).astype(np.uint32))
        if hoist is None and wide:
            lines.append(head + f"const unsigned int b = {off_bits}u + r; "
                                f"kill |= ({table}[b >> 5] >> (b & 31)) "
                                f"& 1u; }}")
            descs.append(("table", Q, off_bits))
        elif hoist is None:
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
        const unsigned char* __restrict__ qinj,
        const int* __restrict__ nin, const int incap,
        unsigned long long* __restrict__ qout,
        unsigned char* __restrict__ qoutj, int* nqout, const int outcap,
        const int from, const int to, const int np_,
        unsigned long long* out, unsigned char* outj, int* nout,
        const int cap,
        const uint4* __restrict__ pk, const unsigned int* __restrict__ pmask,
        const uint4* __restrict__ pres, const unsigned int* __restrict__ jb)
{
    enum { LPI = %(lpi)d, IPB = TTPB / %(lpi)d };
    __shared__ unsigned long long sq[IPB];
    __shared__ unsigned char sqj[IPB];
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
        const unsigned long long offp = qin[i];
#if WIDE
        const unsigned int jj = qinj[i];
#else
        const unsigned int jj = 0u;
#endif
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
            if (last) EMIT(offp, jj)
            else { const int p = atomicAdd(&sn, 1); sq[p] = offp;
#if WIDE
                   sqj[p] = (unsigned char)jj;
#endif
            }
        }
    }
    if (last) return;
    __syncthreads();
    if (threadIdx.x == 0) sbase = (sn > 0) ? atomicAdd(nqout, sn) : 0;
    __syncthreads();
    for (int j = threadIdx.x; j < sn; j += TTPB) {
        const int p = sbase + j;
        const unsigned long long offp = sq[j];
#if WIDE
        const unsigned int jj = sqj[j];
        if (p < outcap) { qout[p] = offp; qoutj[p] = (unsigned char)jj; }
#else
        const unsigned int jj = 0u;
        if (p < outcap) qout[p] = offp;
#endif
        else if (tail_survives(offp, jj, np_, to, pk, pmask, pres, jb))
            EMIT(offp, jj)
    }
}
"""

# A GENERATED TAIL ROUND (TAIL_LITERAL): the generic round's shape with
# one item per thread, its tests literal packs, its push one atomic a warp.
_TAILGEN = r"""
extern "C" __global__ void tailgen%(r)d(
        const unsigned long long* __restrict__ qin,
        const unsigned char* __restrict__ qinj,
        const int* __restrict__ nin, const int incap,
        unsigned long long* __restrict__ qout,
        unsigned char* __restrict__ qoutj, int* nqout, const int outcap,
        const int np_,
        unsigned long long* out, unsigned char* outj, int* nout,
        const int cap,
        const uint4* __restrict__ pk, const unsigned int* __restrict__ pmask,
        const uint4* __restrict__ pres, const unsigned int* __restrict__ jb,
        const unsigned int* __restrict__ g3bits,
        const unsigned int* __restrict__ tb)
{
    enum { IPB = TTPB };
    __shared__ unsigned long long sq[IPB];
    __shared__ unsigned char sqj[IPB];
    __shared__ int sn;
    __shared__ int sbase;
    const int n = min(*nin, incap);
    if (blockIdx.x * IPB >= n) return;
    if (threadIdx.x == 0) sn = 0;
    __syncthreads();
    const int i = blockIdx.x * IPB + (int)threadIdx.x;
    unsigned long long offp = 0ULL;
    unsigned int jj = 0u;
    bool alive = false;
    if (i < n) {
        offp = qin[i];
#if WIDE
        jj = qinj[i];
#endif
        unsigned int kill = 0u;
%(packs)s
        alive = !(kill & 1u);
    }
    {
        /* one shared atomic per warp: the survivors' ballot is their prefix */
        const unsigned int lane = threadIdx.x & 31u;
        const unsigned int am = __ballot_sync(0xFFFFFFFFu, alive);
        int wb = 0;
        if (lane == 0u && am) wb = atomicAdd(&sn, __popc(am));
        wb = __shfl_sync(0xFFFFFFFFu, wb, 0);
        if (alive) {
            const int p = wb + __popc(am & ((1u << lane) - 1u));
            sq[p] = offp;
#if WIDE
            sqj[p] = (unsigned char)jj;
#endif
        }
    }
    __syncthreads();
    if (threadIdx.x == 0) sbase = (sn > 0) ? atomicAdd(nqout, sn) : 0;
    __syncthreads();
    for (int j = threadIdx.x; j < sn; j += TTPB) {
        const int p = sbase + j;
        const unsigned long long op = sq[j];
#if WIDE
        const unsigned int jq = sqj[j];
        if (p < outcap) { qout[p] = op; qoutj[p] = (unsigned char)jq; }
#else
        const unsigned int jq = 0u;
        if (p < outcap) qout[p] = op;
#endif
        else if (tail_survives(op, jq, np_, %(to)d, pk, pmask, pres, jb))
            EMIT(op, jq)
    }
}
"""

# THE PERIOD TABLES, built on the device once per launch (v3): row i of
# `out` is (j * wmod[i] + bmod[i]) mod q[i] for j < pv -- what a test adds
# after its Barrett step to turn "offp mod q" into "(offp + j*W' + base)
# mod q".  For the tail primes wmod is W' mod q and bmod is base mod q; for
# the in-block round groups the same with the group modulus Q.  A 64-bit
# modulo per entry, a few million entries, microseconds.
_JBUILD = r"""
extern "C" __global__ void jbuild(
        const int rows, const int pv,
        const unsigned int* __restrict__ q,
        const unsigned int* __restrict__ wmod,
        const unsigned int* __restrict__ bmod,
        unsigned int* __restrict__ out)
{
    const int idx = blockIdx.x * blockDim.x + (int)threadIdx.x;
    if (idx >= rows * pv) return;
    const int i = idx / pv;
    const int j = idx - i * pv;
    const unsigned long long v = (unsigned long long)j * wmod[i] + bmod[i];
    out[idx] = (unsigned int)(v % q[i]);
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
# ladders shipped 64 below c = 16 and 128 above.  Swept at lcm-ladders'
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
# 224 SINCE ROUND 7, and the move is Rule 1's corollary rather than a new
# idea: the subset wheel of round 6 is a structural change, so every constant
# tuned before it was stale after it.  Re-swept at three filters:
#   pb        128     160     192     224     256
#   n = 15     --      --    1.000   1.008   0.976
#   n = 16     --      --    1.000   1.013   0.881
#   n = 17    1.000   1.061  1.102   1.125   1.123
# 224 wins at all three and 256 falls off at two of them.
PB_DEFAULT = 224
PB_BY_C = {}


def pb_for(c):
    return PB_BY_C.get(int(c), PB_DEFAULT)


# THE BLOCK SHAPE FOLLOWS THE WINDOW'S WIDTH: (spb, xe) = second-level
# residues per block, and how many of them have their live words buffered
# (XE * NW * TPB words of shared) before one extraction pass.  The two set
# how much per-thread and per-block fixed work -- the x0 loads, the
# warp-wide reservation -- a block amortises, and a NARROW window amortises
# it over few periods unless the block holds more residues.  The inherited
# pair (spb 8; xe 4 at NW = 2 and 1 elsewhere) was tuned at NW = 2 and
# NW >= 5 only, and clique-ladders' planner lands on every width.  Swept
# here paired and interleaved, the survivor stream identical at every
# setting (OPTIMIZATION_LOG.md round 1), candidates/s against (8, 1):
#
#   NW 1 (pb  32)  (32,8) 1.20-1.28  (32,4) 1.18-1.26  (16,8) 1.22  (8,8) 1.09
#   NW 2 (pb  64)  (16,8) 1.05-1.07  (16,4) 1.04       (8,4) 1.00 (inherited)
#   NW 3 (pb  96)  (16,4) 1.13       (16,2) 1.11       (8,4) 1.06  (8,2) 1.04
#   NW 4 (pb 128)  (16,2) 1.05       (8,2) 1.02        (16,1) 1.01-1.02
#   NW 5+          (8,1): (16,2) ties at 160; at 192 spb 16 reads 0.97 / 0.89
#
# IT IS A PREFERENCE LIST, NOT A PAIR, because a bigger block is more shared
# memory and shared memory is what sets blocks per SM: the engine takes the
# first shape whose predicted occupancy reaches OCC_MIN_BLOCKS4 (a lost
# block is ~8%, more than any row above buys).  G18 caught exactly that the
# first time this table went in as a pair: (16, 2) at n = 17 of A133761 is
# 20,788 bytes and 4 blocks.
#
# What it buys beyond the rate: the candidate rate is now nearly FLAT from
# 96 periods up (3.10 / 3.23 / 3.07 / 3.18e12 at 96 / 128 / 160 / 179), so a
# shorter segment has stopped costing throughput -- which is what the
# planner's segment decision turns on.
#
# ROWS 5 TO 7 ARE product-cliques' (2026-09-29, its round 1), and
# they exist because the PAIRS window (WINDOW_LDS64) made the odd widths the
# fast ones -- 5 words cost three 64-bit loads, the same as 4 -- and the
# fallback shape (8, 1) hid it: 160 periods read 0.997 of 128 on (8, 1) and
# 1.114 on (16, 2) at n = 18* of A219761.  Candidates/s, stream identical:
#   NW 5 (160, A219761 n = 18*)  (16,2) 1.000  (16,1) 0.97  (16,4) 0.975
#                                (32,1) 0.971  (8,2) 0.91   (32,2) 0.90
#   NW 6 (192, A034881 n = 18*)  (16,1) 0.994 of 160  (8,2) 0.945  (8,1) 0.933
#   NW 7 (224, A034881 n = 18*)  (8,2) 1.005 of 160   (16,2) 1.009 at 4 blocks
BLOCK_SHAPES_BY_NW = {
    1: ((32, 8), (32, 4), (16, 8), (8, 8), (8, 1)),
    2: ((16, 8), (16, 4), (8, 4)),
    3: ((16, 4), (16, 2), (8, 4), (8, 2), (8, 1)),
    4: ((16, 2), (8, 2), (16, 1), (8, 1)),
    5: ((16, 2), (16, 1), (8, 2), (8, 1)),
    6: ((16, 1), (8, 2), (8, 1)),
    7: ((8, 2), (16, 2), (8, 1)),
}
# Window-sieve depth and the in-block rounds, as SURVIVAL FRACTIONS.  The
# window sieve costs a fixed price per prime per residue whatever the prime
# kills, a per-candidate round test a price per entrant, so the boundary is
# where the two cross; the in-block rounds then halve the survivors per round
# (R2_DROP) down to K2_SURV4, where the global tail takes over.
#
# 0.0035 AND 1e-4 HERE (product-cliques round 1), not the inherited 0.007 and
# 3e-4.  The pairs window made a window prime a third cheaper, which moves
# the boundary deeper, and a deeper window also SHRINKS the in-block queues
# (they are sized from the survival at `lit`), which on a 160-period window
# is the difference between 4 and 5 blocks per SM.  Paired, stream identical:
#   A219761 n = 18*, 160 periods:  (0.007, 3e-4) 1.000 [4 blocks]
#       (0.0035, 3e-4) 1.123   (0.0035, 1e-4) 1.148   (0.005, 1e-4) 1.079
#       [4 blocks]   (0.0025, 1e-4) 1.093 [106 registers, 4 blocks]
#   A034881 n = 19*, 128 periods:  BIT_SURV 0.007 / 0.005 / 0.0035 / 0.0025
#       / 0.0018 = 1.000 / 1.011 / 1.023 / 0.997 / 0.967; then K2_SURV4
#       3e-4 / 1e-4 / 5e-5 / 3e-5 / 1.5e-5 = 1.000 / 1.024 / 1.026 / 1.009
#       / 0.998.
# Deeper than 0.0035 the window's x0 residues (one register per prime) take
# the kernel past 100 registers and a block -- and even with the registers
# capped to keep the block, a deeper window reads 0.962 (lit 44) and 0.863
# (lit 50) at n = 18* of A219761.  So the window is also CAPPED in primes
# (LIT_MAX): at a filter of few conditions 0.0035 is reached only far down
# the list (A219761's opening, twelve conditions, compiled to 106 registers
# and 4 blocks, which G18 caught), and 40 is where the registers stay
# under the fifth block.  Never binds at the hour filters (lit 38-39).
BIT_SURV = 0.0035
LIT_MAX = 40
K2_SURV4 = 0.0001
R2_DROP = 0.5
# ... and the in-block rounds stop at most this many primes past the window,
# whatever K2_SURV4 asks: every round prime is a line of generated code, and
# at a filter of few conditions (A219761 n = 10, ten forms, a gate filter)
# 1e-4 is reached only past q = 16,000 -- two thousand round tests.  Never
# binds where a campaign runs: k2 - lit is 98-99 at n = 19* of A034881 and
# n = 18* of A219761.
K2_ROUND_PRIMES_MAX = 128
# Second-level residues per block where BLOCK_SHAPES_BY_NW has no row (one
# first-level residue per thread).
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
# ... and 2^38 on the WIDE record, where a launch also pays for its period
# tables (two device builds and their host inputs) and the tail rounds cost
# a third more: measured 1.109x at n = 18 on the wheel to 53 (three
# interleaved rounds, intervals [2.696, 2.709] against [2.989, 2.993]e17),
# against 1.055 / 1.014 with straddling intervals on the narrow record at
# n = 17 / 18, where 2^37 stays (OPTIMIZATION_LOG.md round 3).  The price
# is ~500 MB more of device queues and a checkpoint interval of ~5 s.
# ... BACK TO 2^37 IN ENGINE v2 (this project's round 2): the optimum moved
# once the per-launch offset table took the period tables' share of a
# launch's fixed cost, and a wide launch's tail queue at 2^38 (27 million
# items, ~240 MB) streams through DRAM past the 72 MB L2.  Paired, candidates
# a second, 2^37 against 2^38: 1.014 [1.012, 1.019] at A083518 n = 20*,
# 1.014 [1.011, 1.017] at A083519 n = 19*, 1.011 [1.005, 1.014] at A083518
# n = 21*; 2^36 reads 1.008 at n = 20*.  Half the queue memory too.  (The
# narrow 2^37 re-swept on v2 at n = 19*: 2^36 1.007, 2^35 0.997, 2^38 0.982 --
# a tie, kept.)
CAND_PER_LAUNCH_WIDE = 1 << 37
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
# THE IN-BLOCK ROUNDS' QUEUES PING-PONG BETWEEN TWO PHYSICAL BUFFERS.  Round r
# reads queue r - 1 and writes queue r, and queue r - 2 is dead by then, so
# queue r lives in queue r - 2's storage: two buffers (the two largest caps)
# instead of one per round.  The LOGICAL capacities, the overflow fallback
# and the stream are untouched; what moves is shared memory, which is what
# sets blocks per SM.  False keeps one buffer per round (the A/B's other arm).
# Measured 2026-09-20 at the six live filters, interleaved, stream identical:
# 3.0-3.4 KB freed and one more block per SM everywhere; 1.022 / 1.012 / 1.009
# / 1.005 / 1.004 where that is the 6th block and 0.997 where it is the 7th
# (A/A noise 0.15%).  The rate stops tracking blocks per SM at six -- the
# padding ablation's 8% a block is the price BELOW five -- so this is worth
# about half a percent on its own; it ships because it is what pays for the
# ne2 rows of ROUND_WINDOW without losing a block.
QUEUE_PINGPONG = True
# THE IN-BLOCK ROUNDS IN THE WINDOW'S COORDINATES.  A round test was a 64-bit
# Barrett step on the candidate's REBUILT offset -- __umul64hi and a multiply
# per prime per item, priced by doubling them (timing-only): one extra copy
# of every round Barrett chain costs 9-10% of the wall and two cost 20%, so
# they are throughput on the multiply pipe, not latency hidden behind a load.
# The window sieve never needs that arithmetic, because in ITS coordinates a
# candidate (t, ss, j) sits at pattern bit x0[t] + ne[ss] + bw + j of a table
# indexed in periods; the queue entry still holds (t, ss, j), so the rounds
# can use the same coordinates: a u16 load from a per-residue row, a shared
# load and two adds, no multiply.  bw rides bit 15 of the queue index.
#
# ON THE WIDE RECORD ONLY, BY MEASUREMENT (2026-09-20, interleaved, the stream
# identical on every run).  The rows are read 16 bytes at a time -- eight u16
# slots a word, each round starting on a word -- because the first version,
# one u16 load per test, ran 0.87x: this kernel is bound by load COUNT.
#   wide   (n = 22 of A093483 / A103828 / A037100):  1.077 / 1.092 / 1.078,
#          1.10 with the ping-pong queues -- the wide test paid TWO loads a
#          prime (jb2 and the bit table) and now pays one;
#   narrow (n = 20 of A119751, n = 21 of A119752):   0.90-0.91 / 1.006 -- the
#          narrow test paid one load a prime already, so the rows are loads
#          ADDED, and they cost more than the multiplies they remove.
# So `rwin` is the record's: wide takes the window coordinates, narrow keeps
# the Barrett rounds.  K2_SURV4 and R2_DROP re-swept on the new rounds at
# n = 22 of A103828: 1e-4 / 3e-4 tie (1.000), 1e-3 0.93, 3e-5 0.70; R2_DROP
# .35 / .5 / .7 = 0.96 / 1.00 / 0.84 -- unchanged.  G20 pins the mechanism
# (and the ping-pong queues, and the forced-overflow path with bw in the
# index) against the CPU engine on a populated window.
ROUND_WINDOW = True
# ... and still not on the narrow record here: forced on at n = 19* of
# A034881 (product-cliques round 1) it read 0.957 (its rows cost a block per
# SM) and 0.909 with the deeper window.  The A/B arm.
ROUND_WINDOW_NARROW = False
# The window pattern tables live in SHARED memory (copied once per block,
# 4-7 KB): a shared load has a fixed ~30-clock latency where an L1 gather
# does not, and the sieve is bound by the latency of its loads with a
# handful in flight per warp, not by issue.
PAT_SHARED = True
# THE WINDOW IS READ FROM A TABLE OF OVERLAPPING PAIRS (product-cliques
# round 1, 2026-09-29): entry e of a prime's table is (word e, word e + 1) of
# its pattern, so the NW + 1 words a window needs, starting at ANY word, are
# ceil((NW + 1) / 2) aligned 64-bit shared loads -- 3 in place of 5 at NW = 4
# and 5 alike, 4 in place of 8 at NW = 7 -- for twice the table.
#
# Why that pays, measured here and not assumed: on this GPU a shared load
# costs its ISSUE, ~0.455 warp-instructions per clock per SM whether it moves
# 4 or 8 bytes a lane (a conflict-free microbenchmark: LDS.32 1.26e9 and
# LDS.64 1.23e9 per SM per second at ~2.78 GHz; LDS.128 half that, where the
# 128 B/clk data path binds), and the window loop is bound by exactly that:
# one more 32-bit load per prime costs +15.7% of the kernel, one more ALU op
# +2.5%, one more 64-bit load the same as a 32-bit one (1.117 vs 1.120).
# Stream identical on every run.  1.145 / 1.149 / 1.149 at n = 19* and 18*
# of A034881 and n = 17* of A219761, at the inherited widths -- and it moves
# the width curve (CREL_WIDTH, BLOCK_SHAPES_BY_NW rows 5-7): an ODD word
# count now fills its last pair.
# Tried first and rejected: 64-bit loads from the plain table with a
# per-word select on the odd start, 0.985 -- five SELs and a predicate per
# prime made the loop ALU-bound (644 instructions against 466).  False keeps
# the 32-bit window (the A/B arm; G14 reads either through pat_word_index).
WINDOW_LDS64 = True
# The window's word index as __umulhi(r, 2^27) (the multiply pipe, an
# IMAD.HI) instead of r >> 5 and a mask (two INT ops): 1.013 at n = 19*.
WINDOW_ADDR_MUL = True
# THE NARROW ROUNDS' TESTS REDUCE ONCE PER PACK OF PRIMES: one 64-bit Barrett
# step to M = the product of up to ROUND_PACK_MAX consecutive round primes
# (M < 2^31), then a 32-bit step per prime (_round_mod32).  1.015 at
# n = 19* (packs of 2: 1.008): the rounds are latency-bound, not
# multiply-bound, so a third of their arithmetic returns little.
ROUND_MOD32 = True
ROUND_PACK_MAX = 3
# THE WINDOW'S LIVE WORDS STAY IN REGISTERS FOR THE EXTRACTION (XREG): the
# XE residues' windows are unrolled and their live words and survivor count
# kept in registers, where the inherited kernel stored them to a shared
# buffer (`sal`) and read them back twice -- 5 stores and 10 loads per
# residue in a kernel bound by shared-load issue.  1.054 at n = 19* of
# A034881 (xe = 1: 1.027; xe = 4: 0.944, 104 registers), stream identical,
# and 5 KB of shared memory per block freed (19.2 -> 14.0 KB).  The freed
# memory does not buy a sixth block: the kernel is at 88 registers, and
# capping it at 80 for six blocks reads 0.930.  False is the A/B arm.
EXTRACT_REGS = True
# The per-thread x0 residues (one per window group) as a register array or
# in shared memory: NG registers per thread against NG*TPB*2 bytes of
# shared per block.
X0_SHARED = False
#
# ---- engine v2 (plus-two-cliques round 2, 2026-10-01) ----------------------
# Measured at A083518 n = 19* (the planned narrow wheel to 47, 160 periods)
# by ablation and Nsight Compute before anything was changed: the sieve
# kernel is 93% of the device, and inside it the window 58%, the in-block
# rounds 28%, extraction 8%, the rest 6%.  The kernel is bound by LSU ISSUE
# (l1tex lsuin requests at 85-86% of peak; ALU pipe 63-68%, issue 60-65%),
# and the window's own loads are exactly at their ideal wavefront count --
# 24 bytes a lane a prime, no conflict to recover.  So round 2 cut what is
# NOT the window: instructions and loads in the rounds, shared stores in the
# extraction, and registers (OPTIMIZATION_LOG.md round 2).
#
# THE NARROW ROUNDS' TESTS ARE LAZY (ROUND_LAZY): neither reduction is
# corrected.  The pack step leaves rm = offp - floor(offp*mg/2^64)*M in
# [0, 2M) and the 32-bit step r = rm - floor(rm*m/2^32)*q in [0, 2q) (the
# floor-magic bound of REDUCE_MAX's comment, with 2M < 2^32 because M < 2^31),
# and the round table is stored THREE times over (3q bits a prime), so the
# lookup at g2p + r -- g2p = base mod q below q -- needs no correction
# either; and the kill bit is OR-ed unmasked and tested once (`kill & 1`).
# Two compare-and-subtracts a test, one a pack and an AND a test gone:
# 1.027-1.030 at n = 19*, stream identical.  G21 emulates the chain bit for
# bit and trips on a pack past 2^31.  Narrow record only: the wide record's
# rounds are in the window's coordinates (ROUND_WINDOW) and never reduce.
ROUND_LAZY = True
# THE SHARED QUEUES HOLD ONE u32 PER ENTRY (QWORD), the packed
# ((ss*TPB + tid) << LOGP) | j that every reader rebuilds anyway, where the
# inherited split was a u16 index and a u8 period: one shared store per
# extracted survivor in place of two, one load per round item in place of
# two.  The split was taken in an older kernel because the 3.1 KB it saved
# was a block per SM; at 72 registers the registers and not the queues set
# the occupancy, so the byte is free.  1.015 on top of ROUND_LAZY at n = 19*.
# NOT on the wide record while its rounds ran in the window's coordinates
# (QWORD_WIDE): there the round rows (ne2) took 3 KB and the fourth byte cost
# the sixth block, 0.95.  Engine v3's folded rounds (ROUND_FOLD) carry no
# such rows, so the wide record takes the u32 entry with them: 1.017 at the
# live filter at equal blocks, and 1.006 over the seventh block it displaces.
QWORD = True
QWORD_WIDE = False
# THE WINDOW'S x0 AND ne ARE PACKED TWO GROUPS TO A 32-BIT WORD (NEPACK).
# x0 < Q, ne < Q and Q < 2^15, so x0 + ne + bw < 2^16 in each half and ONE
# add forms two window positions (bw rides as bw * 0x10001); the low half is
# masked out, the high half shifted down, and each half's funnel shift reads
# its own low five bits.  It halves the x0 registers (38 -> 19 at n = 19*,
# 88 -> 72 registers: the SIXTH block per SM) and the ne loads (one 16-byte
# broadcast per eight groups, not four).  1.03 on top of the two above at
# n = 19*; 1.06-1.08 at the wide n = 20* (86 -> 80 registers, 5 -> 6
# blocks), stream identical.  G14 reads the packed table back through
# `x0_table`.
NEPACK = True
# THE BLOCK OFFSETS ARE BUILT ONCE PER LAUNCH, NOT ONCE PER BLOCK (PRE_TABLE).
# A block's ne (one per window group) and, on the wide record, its ne2 (one
# per round group) depend on its second-level residue s, its third-level u
# and the launch base -- and NOT on its first-level chunk, so every one of
# the ~850-1400 t-blocks of a launch recomputed the same rows: 16 threads,
# two 64-bit reductions a group, 38 groups narrow and 124 wide, while the
# rest of the block waited at the barrier.  `nebuild` computes each
# (s, z) row once per launch from the same generated formulas, and a block
# copies its SPB rows into shared memory sixteen bytes at a time.  Taken
# where the launch's table fits PRE_TABLE_MAX entries (every campaign
# configuration: 0.3-1.4 million) and the window is packed (NEPACK).
PRE_TABLE = True
PRE_TABLE_MAX = 1 << 25
#
# ---- engine v3 (round 3, 2026-10-02), measured at the LIVE filter ----------
# A083518 n = 20 on its real terms: the wheel to 59 less 41, the wide record,
# 160 periods, 5.4 million launches a segment.  Nsight Compute first, on the
# v2 kernel there: the L1TEX data pipe at 87% of its peak in LSU wavefronts
# (the window's 64-bit loads 68% of them), FIVE blocks per SM where the
# registers allow six (16,096 bytes of shared memory, 54 too many), and the
# wide rounds in the window's coordinates paying for their per-residue rows:
# a 3.1 GB table read in 16-byte gathers at 27 sectors a request, an L1 hit
# rate of 68%, and global-load latency the rounds' first stall.  What follows
# is what those numbers pointed at; the same survivor stream on the same plan
# and launches, 1.10x at the live filter (OPTIMIZATION_LOG.md round 3).
#
# A WINDOW PRIME BELOW THE WINDOW'S WIDTH REPEATS INSIDE IT (WINDOW_PERIODIC).
# The pattern of a prime q has period q, so the window's bits from q on are
# its own first bits again: a prime with 32 < q <= 96 needs only the first
# three words READ (two 64-bit loads, not three at 160 periods) and the rest
# are constant funnel shifts of words already in registers -- the same five
# shifts a prime, one shared load fewer.  Eight of the live filter's 38
# window primes (41, 61 to 89): 1.019, registers 80 -> 72.  `window_plan` is
# the one derivation the emitter and G14's emulation share.  False reads every
# word (the A/B arm).
WINDOW_PERIODIC = True
# THE WIDE RECORD'S IN-BLOCK ROUNDS ON THE NARROW RECORD'S ARITHMETIC
# (ROUND_FOLD): lazy Barrett packs, the period folded into each pack's
# numerator as jj * (W' mod M) -- see _round_mod32.  It retires the
# window-coordinate rounds' per-residue rows (4.3 -> 1.4 GiB of device memory
# at the live filter) and their slots in every block's offset rows (3.3 KB of
# shared memory: the sixth block, and room for the u32 queue entry the wide
# record could not afford, QWORD).  1.052 at the live filter with both, 1.046
# without the queue word (seven blocks); L1 hit rate 68% -> 79%.  False keeps
# the rounds in the window's coordinates (ROUND_WINDOW), the A/B arm, which
# G20 and G22 still pin.
ROUND_FOLD = True
# A PERIODIC GROUP READS ITS WORDS IN ONE 16-BYTE LOAD (WINDOW_QUAD): entry e
# of its table is words e..e + 3, so the three words a prime up to 96 needs
# read are one LDS.128 in place of two LDS.64 -- and the table is cut to the
# entries a position below 2Q can reach, which makes it smaller than the
# pairs table it replaces (200 bytes of shared memory back).  1.008.
WINDOW_QUAD = True
# THE FIRST TAIL ROUNDS ARE GENERATED, WITH THEIR PRIMES AS LITERALS
# (TAIL_LITERAL).  A tail round's test is generic -- the prime, its 64-bit
# magic, its period row and its mask all loaded, ~43 instructions and three
# gathers a prime (Nsight Compute, round 3) -- which is right for the deep
# rounds, a few thousand items against hundreds of primes, and wasteful for
# the first ones, millions of items against a couple of dozen primes each.
# Those get the in-block rounds' test instead: one lazy 64-bit Barrett step
# per PACK of primes (M < 2^30), the launch base added to the pack remainder
# from a per-launch table (below 3M < 2^32), a lazy 32-bit step per prime and
# one bit from a table stored twice over; and their survivors are pushed with
# ONE shared atomic per warp (a ballot prefix) instead of one per survivor.
# A round is generated while it expects at least TAIL_LITERAL_ITEMS items a
# launch and holds at most TAIL_LITERAL_PRIMES primes, up to TAIL_LITERAL
# rounds; 0 keeps every round generic (the A/B arm).  Nine rounds at the live
# filter (13.6 million items down to 0.74 million): 1.020, and 1.011 with
# only the first four.  G21 emulates every pack and trips on a modulus whose
# tripled remainder passes the word.
TAIL_LITERAL = 16
TAIL_LITERAL_ITEMS = 1 << 19
TAIL_LITERAL_PRIMES = 64
TAIL_PACK_MAX = 1 << 30
# xe = 2 compiled to this many registers or more lost to xe = 1 in
# product-cliques (96 against 87 and 91: 0.917 / 0.926 of the clock).
XE1_REGS = 96


def window_plan(Q, nw, periodic=None):
    """(loads, steps): how the window's NW words are formed for a group of
    modulus Q on the pairs table.  `loads` 64-bit loads give 2*loads words;
    step i is ("read", i) -- the funnel shift of words i and i + 1 by the
    position's low five bits -- or ("rep", k, c): the 32 bits at offset
    32*k + c of the words already formed, which is the same window Q bits
    earlier (WINDOW_PERIODIC).  A derived word needs only words below it
    (32 < Q), and its source starts at a bit >= 0 (32*i >= Q for the first
    derived word), so the chain never reads a word it has not formed."""
    periodic = WINDOW_PERIODIC if periodic is None else periodic
    full = (int(nw) + 2) // 2
    loads = full
    if periodic and Q > 32:
        need = -(-int(Q) // 32)             # words that must be READ
        loads = min(full, (need + 2) // 2)  # 2*loads - 1 >= need
    steps = []
    for i in range(int(nw)):
        if i < 2 * loads - 1:
            steps.append(("read", i))
        else:
            d = 32 * i - int(Q)
            steps.append(("rep", d >> 5, d & 31))
    return loads, steps


def pairs_table(pat, offs, quad=None):
    """The window tables as OVERLAPPING PAIRS: entry e of a group's table is
    (word e, word e + 1) of its pattern, so a window starting at ANY word is
    read by 8-byte-aligned loads.  Returns (u32 table, per-group offset in
    u32 words -- always even).  A group in `quad` ({group: entries}) is
    stored as overlapping QUADS instead, entry e = words e..e + 3 on a
    16-byte boundary, for that many entries (WINDOW_QUAD)."""
    ends = list(offs[1:]) + [int(pat.size)]
    parts, out_offs, at = [], [], 0
    quad = quad or {}
    for gi, (a, b) in enumerate(zip(offs, ends)):
        P = pat[a:b]
        if gi in quad:
            m = int(quad[gi])
            if P.size < m + 3:
                raise ValueError("quad table past its pattern")
            if at % 4:
                parts.append(np.zeros(4 - at % 4, dtype=np.uint32))
                at += 4 - at % 4
            pr = np.empty(4 * m, dtype=np.uint32)
            for k in range(4):
                pr[k::4] = P[k:k + m]
            parts.append(pr)
            out_offs.append(at)
            at += 4 * m
            continue
        m = P.size - 1
        pr = np.empty(2 * m, dtype=np.uint32)
        pr[0::2] = P[:-1]
        pr[1::2] = P[1:]
        parts.append(pr)
        out_offs.append(at)
        at += 2 * m
    table = (np.concatenate(parts) if parts
             else np.zeros(2, dtype=np.uint32))
    return table, out_offs


def window_patterns(n, fam, primes, groups, Wp, nw, unit=1, align=1):
    """(u64 table, offsets, Dinv per group) for the window sieve.

    For group g with modulus Q = prod(q in g): pattern bit p is set iff
    (p mod q) in C_q for some q in g, C_q = { kr * Dinv_Q mod q : kr in
    killed_residues(q) } with Dinv_Q = (Wp mod Q)^-1 mod Q.  Stored as
    32-bit words -- word w holds bits [32w, 32w + 32) -- so a window of NW
    words at bit position r is words r >> 5 .. (r >> 5) + NW, each pair
    funnel-shifted by r & 31, for r in [0, 2Q) (the residue arrives
    unreduced from x0 + ne + bw, each below Q).  The words are what this
    builds; the DEVICE layout is `pairs_table`'s where it fits (v2): the
    inherited note that a 64-bit shared load costs twice a 32-bit one is
    true of the data path and not of this kernel, which is bound by load
    ISSUE, where the two cost the same (OPTIMIZATION_LOG.md round 1).  G14
    checks every bit of every table, through either layout, against
    killed_residues.
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
        nwords = -(-nwords // align) * align
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
#define NG2 %(ng2)d
#define RWIN %(rwin)d
#define PATSH %(patsh)d
#define X0SH %(x0sh)d
#define NPAT %(npat)d
#define XE %(xe)d
#define XREG %(xreg)d
%(qcaps)s
#define LOGTPB %(logtpb)d
#define LOGSPB %(logspb)d
#define QTYPE %(qtype)s
#define X0TYPE %(x0type)s
#define MASK_BITS %(mask_bits)d
#define MASK_WORDS (MASK_BITS / 32)
#define NRES %(nres)d
#define TTPB %(ttpb)d
#define WIDE %(wide)d
#define QWORD %(qword)d
#define NGX  %(ngx)d
#define PRET %(pret)d
#define NROW %(nrow)d
#define NG8C %(ng8c)d

/* THE RECORD DISPATCHES (engine v3).  WIDE = 0: a candidate past the window
   sieve is its u64 offset within the LAUNCH -- the segment's first period,
   the period and the residue folded together, the launch base folded on
   the host into base-mod-q per prime and into the round tables' scalars --
   which is exact while (segments*PB + 1)*W' + q2 < 2^64.  WIDE = 1: the
   candidate is (offp, jj), its WITHIN-PERIOD offset (< W' < 2^63) and its
   period inside the window, and every test adds the per-launch table entry
   (jj*W' + base) mod q after its Barrett step -- no u64 ever holds jj*W',
   so the wheel is not bounded by the window.  The wide record costs 5-6%%
   where the narrow one would do (the per-candidate route pays one more
   dependent term per test, OPTIMIZATION_LOG.md round 3), so the engine
   takes it only where the wheel demands it: 1.19x at n = 18 and 1.24x at
   n = 19 on the wheel to 53. */
#if WIDE
#define WITHJ(P, J) (P)
#define PERIOD_TERM(IDX) jb[(IDX) * PV + (jj)]
#define EMIT(P, J) { const int _p = atomicAdd(nout, 1); \
                     if (_p < cap) { out[_p] = (P); \
                                     outj[_p] = (unsigned char)(J); } }
#else
#define WITHJ(P, J) ((P) + base + (unsigned long long)(J) * WC)
#define PERIOD_TERM(IDX) e.w
#define EMIT(P, J) { const int _p = atomicAdd(nout, 1); \
                     if (_p < cap) out[_p] = (P); }
#endif

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
#if RWIN
#define BWBIT(B) ((unsigned short)((B) ? 0x8000u : 0u))
#else
#define BWBIT(B) ((unsigned short)0)
#endif
/* ... OR FOUR (engine v2, QWORD): the packed u32 itself, one shared store per
   extracted survivor and one load per round item, where the split pays two
   of each; the register file, not the queues, sets the occupancy since the
   window's x0 are packed (NEPACK).  The wide record keeps the split. */
#if QWORD
#define QGET(QI, QJ, P) ((QI)[P])
#define QPUT(QI, QJ, P, IDX, J) ((QI)[P] = (((unsigned int)(IDX)) << LOGP) \
                                          | (unsigned int)(J))
#define QCOPY(QI2, QJ2, P2, QI1, QJ1, P1, V) ((QI2)[P2] = (V))
typedef unsigned int QIT;
typedef unsigned int QJT;
#else
#define QGET(QI, QJ, P) ((((unsigned int)(QI)[P]) << LOGP) \
                         | (unsigned int)(QJ)[P])
#define QPUT(QI, QJ, P, IDX, J) { (QI)[P] = (IDX); \
                                  (QJ)[P] = (unsigned char)(J); }
#define QCOPY(QI2, QJ2, P2, QI1, QJ1, P1, V) { (QI2)[P2] = (QI1)[P1]; \
                                               (QJ2)[P2] = (QJ1)[P1]; }
typedef unsigned short QIT;
typedef unsigned char QJT;
#endif

/* One test against prime IDX: the uint4 record (magic_lo, magic_hi, q,
   base mod q -- the last is what the host folds and jb is built from), the
   per-launch table jb[IDX*PV + jj] = (jj*W' + base) mod q, the prime's
   MASK_BITS-bit mask and, rarely, its residue list.  THE CANDIDATE IS
   (offp, jj) -- engine v3: its within-period offset offp = r1 + W1*M
   (< W' < 2^63, a u64 the one-conditional-subtraction Barrett step reduces
   exactly, G19) and its period jj inside the window -- so no u64 ever holds
   jj*W', the window is not bounded by the word and the wheel is not bounded
   by the window (OPTIMIZATION_LOG.md round 3). */
#define TEST(IDX, DST) { \
    const uint4 e = pk[IDX]; \
    const unsigned long long mg = ((unsigned long long)e.y << 32) | e.x; \
    unsigned int r = (unsigned int)offp \
                   - (unsigned int)__umul64hi(offp, mg) * e.z; \
    if (r >= e.z) r -= e.z; \
    r += PERIOD_TERM(IDX); \
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
        const unsigned long long offp, const unsigned int jj, const int np_,
        const int from,
        const uint4* __restrict__ pk, const unsigned int* __restrict__ pmask,
        const uint4* __restrict__ pres, const unsigned int* __restrict__ jb)
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

/* Rebuild a candidate's WITHIN-PERIOD offset from its queue entry; the
   period is JOF(qi).  The thread that dequeues is not the thread that
   queued, so D lives in shared. */
#define JOF(QI) ((QI) & ((1u << LOGP) - 1u))
__device__ __forceinline__ unsigned long long offp_of(
        const unsigned int qi, const int t_lo,
        const uint2* __restrict__ res1x, const unsigned int* d2)
{
    /* LOGP bits, not PB - 1: the queue entry packs the period index into
       the low LOGP bits (QIDX shifts the residue index left by LOGP), and
       PB - 1 is only the right mask when PB is a POWER OF TWO.  At PB = 192
       it is 0b10111111, which clears bit 6 of every period index above 63 --
       the candidate is rebuilt at the wrong period, survives, and the stream
       gains entries.  G9 caught it as +18 survivors in 2e6 of line at n = 9. */
    const unsigned int rest = qi >> LOGP;
    const int tid = rest & (TPB - 1);
    const uint2 e1 = res1x[t_lo + blockIdx.y * TPB + tid];
    unsigned long long off = (unsigned long long)e1.x;
#if TWOLEVEL
    const int ss = (rest >> LOGTPB) & (SPB - 1);   /* bit 15 is bw (RWIN) */
    off += (unsigned long long)W1C * M_OF(e1.y, d2[ss]);
#endif
    return off;
}

extern "C" __global__ void sieve(
        const int R1, const int R2, const int np_,
        const unsigned int* __restrict__ pmask,
        const uint4* __restrict__ pres,
        unsigned long long* out, unsigned char* outj, int* nout,
        const int cap,
        unsigned long long* q3, unsigned char* q3j, int* n3, const int q3cap,
        const uint4* __restrict__ pk,
        const uint2* __restrict__ res1x,
        const X0TYPE* __restrict__ x0tab,
        const unsigned int* __restrict__ res2c,
        const unsigned int* __restrict__ res2d, const int u0,
        const int t_lo, const int nper,
        const unsigned int* __restrict__ jmod,
        const unsigned int* __restrict__ gpat,
        const unsigned int* __restrict__ g2bits,
        const unsigned int* __restrict__ jb,
        const unsigned int* __restrict__ jb2,
        const uint4* __restrict__ x0r,
        const unsigned int* __restrict__ jmod2,
        const unsigned int* __restrict__ patr,
        const unsigned short* __restrict__ netab%(gparams)s)
{
%(qdecl)s
    __shared__ int q3b;
    __shared__ unsigned int d2[SPB];
#if PRET
    /* the block's rows of the launch's offset table (PRE_TABLE): window
       groups first, then the round slots */
    __shared__ __align__(16) unsigned short nerow[SPB][NROW];
#define ne16 nerow
#define NE2ROW(SS) ((const unsigned int*)&nerow[SS][NG8C])
#else
#if RWIN
    __shared__ __align__(16) unsigned int ne2[SPB][NG2];
#define NE2ROW(SS) (ne2[SS])
#endif
%(nedecl)s
#endif
#if !XREG
    __shared__ unsigned int sal[XE * NW * TPB];
#endif
#if X0SH
    __shared__ X0TYPE sx0[NG * TPB];
#endif
#if PATSH
    __shared__ __align__(16) unsigned int spat[NPAT];
    for (int i = threadIdx.x; i < NPAT; i += TPB) spat[i] = gpat[i];
#define pat spat
#else
#define pat gpat
#endif
    if (threadIdx.x == 0) { %(qzero)s }

    /* gridDim.z = segment * NU + u (WIDE: one window per launch, so
       gridDim.z = u and sg is 0).  The segment's first period is sg * PV
       after the launch base; `nper` periods are live in the launch, so the
       last segment may be partial. */
#if WIDE
    const int sg = 0;
#else
    const int sg = blockIdx.z / NU;
#endif
    const unsigned long long base = WC * (unsigned long long)(sg * PV);
    const int nv = min(PV, nper - sg * PV);
    (void)base;
    /* s-blocks ride gridDim.x and t-blocks gridDim.y: consecutive blocks
       then share their first-level chunk, so an SM's successive blocks find
       the chunk's x0 rows and res1x in its L1 */
    const int s0 = blockIdx.x * SPB;
    const int tb = blockIdx.y;
    (void)s0;
#if THREELEVEL
    const unsigned int cb = res2d[u0 + (int)(blockIdx.z %% NU)];
#endif
#if PRET
    {
        const unsigned short* src_ = netab
            + (unsigned long long)blockIdx.z * (unsigned long long)R2 * NROW;
        for (int i_ = threadIdx.x; i_ < SPB * (NROW / 8); i_ += TPB) {
            const int ss_ = i_ / (NROW / 8);
            const int w_ = i_ - ss_ * (NROW / 8);
            const int s_ = min(s0 + ss_, R2 - 1);
            ((uint4*)nerow[ss_])[w_] =
                ((const uint4*)(src_ + (unsigned long long)s_ * NROW))[w_];
        }
    }
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
        unsigned int x0[NGX];
#pragma unroll
        for (int g = 0; g < NGX; ++g) x0[g] = x0tab[g * R1 + tt];
#define X0(G) x0[G]
#endif
#if XREG
        /* THE LIVE WORDS STAY IN REGISTERS (XREG): the XE residues' windows
           are unrolled, their live words and the survivor count kept in
           registers, and the extraction reads them there -- no round trip
           through shared memory, whose load issue is what this kernel is
           bound by (product-cliques round 1). */
        for (int s1 = 0; s1 < nss; s1 += XE) {
        unsigned int lw[XE][NW];
        unsigned int dds[XE];
        int cnt = 0;
#pragma unroll
        for (int sx = 0; sx < XE; ++sx) {
            const int ss = s1 + sx;
            dds[sx] = 0u;
#pragma unroll
            for (int i = 0; i < NW; ++i) lw[sx][i] = 0u;
            if (ss < nss) {
            const unsigned int dd = d2[ss];
            dds[sx] = dd;
            const unsigned int bw = (e1.y < dd) ? 1u : 0u;
            unsigned int acc[NW];
#pragma unroll
            for (int i = 0; i < NW; ++i) acc[i] = 0u;
%(groups)s
#pragma unroll
            for (int i = 0; i < NW; ++i) {
                const int lo = nv - 32 * i;
                const unsigned int vm = lo >= 32 ? 0xFFFFFFFFu
                                     : (lo <= 0 ? 0u : ((1u << lo) - 1u));
                lw[sx][i] = live ? (~acc[i] & vm) : 0u;
                cnt += __popc(lw[sx][i]);
            }
            }
        }
        int p;
        const int total = warp_reserve(&qn0, cnt, &p);
        if (total == 0) continue;
        const bool fits = (p + cnt <= Q0CAP);
#pragma unroll
        for (int sx = 0; sx < XE; ++sx) {
            const int ss = s1 + sx;
            const unsigned int dd = dds[sx];
#pragma unroll
            for (int i = 0; i < NW; ++i) {
                unsigned int a = lw[sx][i];
                const unsigned short qb = QIDX(ss) | BWBIT(e1.y < dd);
                if (fits) {
                    while (a) { QPUT(qi0, qj0, p, qb, 32u * i + __ffs(a) - 1);
                                ++p; a &= a - 1u; }
                    continue;
                }
                while (a) {
                    const int b = __ffs(a) - 1;
                    a &= a - 1u;
                    const unsigned int j = 32u * i + b;
                    if (p < Q0CAP) { QPUT(qi0, qj0, p,
                                          QIDX(ss) | BWBIT(e1.y < dd), j); }
                    else {
                        unsigned long long offp = e1.x;
#if TWOLEVEL
                        offp += (unsigned long long)W1C * M_OF(e1.y, dd);
#endif
                        offp = WITHJ(offp, j);
                        if (tail_survives(offp, j, np_, LITN, pk, pmask,
                                          pres, jb))
                            EMIT(offp, j)
                    }
                    ++p;
                }
            }
        }
        }
#else
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
                const unsigned short qb = QIDX(ss) | BWBIT(e1.y < dd);
                if (fits) {
                    while (a) { QPUT(qi0, qj0, p, qb, 32u * i + __ffs(a) - 1);
                                ++p; a &= a - 1u; }
                    continue;
                }
                while (a) {
                    const int b = __ffs(a) - 1;
                    a &= a - 1u;
                    const unsigned int j = 32u * i + b;
                    if (p < Q0CAP) { QPUT(qi0, qj0, p,
                                          QIDX(ss) | BWBIT(e1.y < dd), j); }
                    else {
                        unsigned long long offp = e1.x;
#if TWOLEVEL
                        offp += (unsigned long long)W1C * M_OF(e1.y, dd);
#endif
                        offp = WITHJ(offp, j);
                        if (tail_survives(offp, j, np_, LITN, pk, pmask,
                                          pres, jb))
                            EMIT(offp, j)
                    }
                    ++p;
                }
            }
        }
        }
#endif
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
        const unsigned int qv = QGET(qiR, qjR, idx);
        const unsigned int jj = JOF(qv);
        const unsigned long long offp = WITHJ(offp_of(qv, t_lo, res1x, d2), jj);
        const int p = q3b + idx;
        if (p < q3cap) { q3[p] = offp;
#if WIDE
                         q3j[p] = (unsigned char)jj;
#endif
        }
        else if (tail_survives(offp, jj, np_, K2, pk, pmask, pres, jb))
            EMIT(offp, jj)
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
                 nu=None, unit=1, pb=None, tchunk=None, bit_group_max=None,
                 wide=None, seg_cap=None, xe=None, lds64=None):
        import cupy as cp
        self.cp = cp
        self.n = int(n)
        self.fam = family(fam)
        self.s = 0                  # no sign here; kept for config()
        self.unit = assert_unit(self.n, self.fam, unit)
        self.nforms = nforms(self.fam, self.n)
        # A prime kills at most one residue per form (every form is linear
        # here): the residue list is sized from maxkills, which counts them
        self.maxkills = maxkills(self.fam, self.n)
        if self.maxkills > NRES_MAX:
            raise ValueError(
                f"a filter of {self.nforms} conditions can kill up to "
                f"{self.maxkills} residues per prime, and the tail's residue "
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
        planned = p1 is None
        if planned:
            # the wheel, the depth and the window are chosen TOGETHER, by
            # expected clock to a confirmed find (`plan`)
            p1, p2, p3, q2_planned, pb_planned = plan(self.n, fam, self.unit)
            if q2 is None:
                q2 = q2_planned
            if pb is None:
                pb = pb_planned
        # A caller that names its wheel still gets the depth planned for it:
        # what the sieve has left to kill is what the wheel did not -- and
        # the wheel is a SUBSET of the primes, so "what it did not" is a set
        # difference and not a threshold.
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
        # x = r0 + unit*t: the forced CLASS, not the multiples of a unit
        # (plus2_search.killed_residues).  r0 < unit, so the periods of x
        # and of t share their boundaries: every candidate below j*W has
        # t below j*W' and vice versa.
        self.r0 = unit_residue(self.n, self.fam, self.unit)
        # THE RECORD, AND THE PERIODS A SEGMENT HOLDS.  Narrow (v2): the
        # candidate past the window sieve is a u64 offset within the launch,
        # exact while (PV + 1) W' + q2 < 2^64 -- 179 periods on the full
        # wheel to 47.  Wide (v3): (offp, jj), the within-period offset and
        # the period index, bounded by W' + q2 < 2^64 alone, so the window
        # is free and the wheel may be longer than a u64 window admits.  The
        # wide record costs 5-6% where the narrow one would do (round 3),
        # so: narrow whenever it admits at least WIDE_MIN_PV periods (the
        # window past that is worth under 2%), clamping the window to what
        # it admits; wide only where the wheel demands it.  `wide` forces
        # either (the gates and the A/Bs do).
        if self.Wp + self.q2 >= REDUCE_MAX:
            raise ValueError(
                f"one wheel period is W' = {self.Wp}, and W' + q2 is not "
                f"below 2^64: the within-period offset would not fit the "
                f"record (CONVENTIONS.md numeric hygiene)")
        maxp = (REDUCE_MAX - self.q2) // self.Wp - 1
        if wide is None:
            wide, _pv = _record_for(self.Wp, self.q2, self.pb)
        self.wide = bool(wide)
        # the wide record's in-block rounds as lazy Barrett packs with the
        # period folded per pack (ROUND_FOLD), or in the window's coordinates
        self.fold = bool(ROUND_FOLD and self.wide and ROUND_MOD32
                         and ROUND_LAZY)
        if self.wide:
            self.pv = int(self.pb)
        else:
            if maxp < 1:
                raise ValueError(
                    f"the narrow record needs 2 W' + q2 < 2^64 and W' = "
                    f"{self.Wp}: this wheel needs the wide record")
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
        # SUBSET of the primes (wheel_candidates), so a prime it declined -- 11, 13
        # and 17 at n = 17, which kill under a tenth of the line each -- is
        # sieved here instead.  Taking "everything above the wheel's largest
        # prime" would silently drop them and thin the line.
        _wset = set(int(q) for q in _wheel_primes(p1, p2, p3))
        self.wheel_set = tuple(sorted(_wset))
        _sv = [q for q in primerange(2, q2 + 1)
               if self.unit % q and q not in _wset]
        # ORDERED BY KILLING POWER, strongest first -- not by size.  Since
        # the wheel became a SUBSET, the primes it declined (11, 13 and 17)
        # are in this list and are its WEAKEST members: each keeps over nine
        # tenths of the line.  In increasing order they would be the first
        # three the window sieve tests, and the window costs the same per
        # prime whatever it kills, so the survival target would be reached
        # several primes later than it needs to be.  The survivor SET does
        # not depend on the order (every prime is tested), so this is free.
        _sv.sort(key=lambda q: ((q - len(killed_residues(q, n, fam,
                                                         self.unit))) / q, q))
        self.primes = _sv
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
        self.lit = (min(depth_for(self.lit_target), LIT_MAX) if lit is None
                    else min(lit, len(self.primes)))
        self.k2 = (min(max(self.lit, depth_for(self.k2_target)),
                       self.lit + K2_ROUND_PRIMES_MAX) if k2 is None
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
        self.nres = 16 if self.maxkills <= 16 else NRES_MAX
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
        self.d_outj = [cp.empty(HIT_CAP if self.wide else 1, dtype=np.uint8)
                       for _ in range(2)]
        self.d_n = [cp.zeros(1, dtype=np.int32) for _ in range(2)]
        self._pre = min(PRE_COPY, HIT_CAP)
        self._h_n, self._h_out, self._h_outj, self._ev = [], [], [], []
        for _ in range(2):
            pn = cp.cuda.alloc_pinned_memory(4)
            po = cp.cuda.alloc_pinned_memory(8 * self._pre)
            pj = cp.cuda.alloc_pinned_memory(self._pre)
            self._h_n.append(np.frombuffer(pn, dtype=np.int32, count=1))
            self._h_out.append(np.frombuffer(po, dtype=np.uint64,
                                             count=self._pre))
            self._h_outj.append(np.frombuffer(pj, dtype=np.uint8,
                                              count=self._pre))
            self._ev.append(cp.cuda.Event(block=False, disable_timing=True))
        # the period tables' static inputs: q and W' mod q per tail prime
        self.d_q = cp.asarray(self._qs.astype(np.uint32))
        self.d_wmod = cp.asarray(self._wmod.astype(np.uint32))
        self.d_bmod = cp.zeros(len(self.primes), dtype=np.uint32)
        self._buf = 0
        self._flush = cp.cuda.Stream.null

        # THE WINDOW TABLES and the per-residue x0 table
        (self._pat, self.pat_offs, self.dinvs) = window_patterns(
            n, fam, self.primes, self.groups, self.Wp, self.nw, unit=self.unit)
        # the pairs table is twice the plain one: taken only where it fits
        # the window tables' shared-memory budget (every campaign
        # configuration here, 5-7 KB; not the shallow x-space gate wheels,
        # whose deep windows would pass the 48 KB static limit doubled)
        self.lds64 = bool(WINDOW_LDS64
                          and 8 * (int(self._pat.size) - len(self.pat_offs))
                          <= PAT_BYTES_MAX)
        if lds64 is not None:           # the gates force either layout
            self.lds64 = bool(lds64)
        if self.lds64:
            self._patdev, self.pat_offs_dev = pairs_table(self._pat,
                                                          self.pat_offs)
        else:
            self._patdev, self.pat_offs_dev = self._pat, list(self.pat_offs)
        self.d_pat = cp.asarray(self._patdev)
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
        # NEPACK: two groups to a u32 word, group 2k in the low half and
        # 2k + 1 in the high half; every half-sum x0 + ne + bw < 2Q <= 2^16
        self.nepack = bool(NEPACK and self.lds64 and not X0_SHARED
                           and self.x0_dtype == np.uint16
                           and max(self.gmods, default=1) < 1 << 15)
        # the periodic window (WINDOW_PERIODIC) rides the packed pairs window
        self.periodic = bool(WINDOW_PERIODIC and self.nepack)
        # WINDOW_QUAD: the groups whose plan READS three words (two loads),
        # with the entries a position r < 2Q can index
        self._quad = {}
        if self.periodic and WINDOW_QUAD:
            for gi, Q in enumerate(self.gmods):
                nl_, st_ = window_plan(Q, self.nw, True)
                if nl_ == 2 and st_[-1][0] == "rep":
                    self._quad[gi] = ((2 * Q - 1) >> 5) + 1
            if self._quad:
                self._patdev, self.pat_offs_dev = pairs_table(
                    self._pat, self.pat_offs, quad=self._quad)
                self.d_pat = cp.asarray(self._patdev)
        if self.nepack:
            self.ngx = (len(self.groups) + 1) // 2
            xp = np.zeros((self.ngx, self.R1), dtype=np.uint64)
            xp[:] = x0[0::2]
            xp[:len(self.groups) // 2] |= x0[1::2] << np.uint64(16)
            self.d_x0 = cp.asarray(xp.astype(np.uint32).ravel())
        else:
            self.ngx = len(self.groups)
            self.d_x0 = cp.asarray(x0.astype(self.x0_dtype).ravel())
        self.d_jmod = cp.zeros(max(len(self.groups), 1), dtype=np.uint32)
        self._jmod = np.zeros(max(len(self.groups), 1), dtype=np.uint32)

        # geometry: one first-level residue per thread, SPB second-level
        # residues per block, PB periods per segment.  The residues per
        # block and the extraction batch follow the WINDOW'S WIDTH
        # (BLOCK_SHAPES_BY_NW): a narrow window needs a bigger block to
        # amortise the same fixed work.
        shapes = BLOCK_SHAPES_BY_NW.get(self.nw, ((SPB4, 1),))
        if spb is not None or xe is not None:
            # a caller that names either gets exactly that (the A/Bs do)
            shapes = ((spb if spb is not None else shapes[0][0],
                       xe if xe is not None else shapes[0][1]),)
        self.jpt = 1
        self.logtpb = self.tpb.bit_length() - 1
        if (1 << self.logtpb) != self.tpb:
            raise ValueError(
                f"tpb={self.tpb} must be a power of two: the shared queues "
                f"store a candidate's (ss, tid, j) index rather than its "
                f"offset, and it is unpacked by shifts")

        def _set_shape(shape):
            want_spb, want_xe = shape
            self.spb = 1 << (max(1, min(int(want_spb), self.R2)).bit_length() - 1)
            self.xe = max(1, min(int(want_xe), self.spb))
            self.logspb = self.spb.bit_length() - 1
            self.tile = self.tpb * self.spb * self.pb   # candidates per block
        _set_shape(shapes[0])
        # launch shape: segments (of PB periods) x third-level residues x a
        # first-level chunk, under the candidate budget and the 2^63
        # reduction bound
        per_u_seg = self.R1 * self.R2 * self.pv
        budget = CAND_PER_LAUNCH_WIDE if self.wide else CAND_PER_LAUNCH4
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
        # A CHUNK'S BLOCKS RIDE gridDim.y, WHICH CUDA CAPS AT 65535 (the grid
        # is (second-level, first-level chunk, segments x third level)).
        # Under R1_MAX = 2^21 no chunk came near it; a first level from the
        # second budget can (9.6 million residues of a one-level wheel is
        # 75,000 blocks), so the chunk is capped -- found by G9's window past
        # R1_MAX, as CUDA_ERROR_INVALID_VALUE.  No configuration under
        # R1_MAX changes: their chunks are all far below the cap.
        self.tchunk = min(self.tchunk, 65535 * self.tpb)
        if self.wide:
            # ONE window per launch: the period index rides the record as a
            # u8 inside the window, so a wide launch never batches windows
            self.nseg = 1
        elif self.nu < self.R3 or self.tchunk < self.R1:
            self.nseg = 1
        else:
            self.nseg = max(1, min(65535 // self.nu,
                                   budget // max(self.R * self.pv, 1)))
        # THE PLANNED SEGMENT IS THE WINDOW: a campaign engine is built with
        # seg_cap = its planned window, so a launch never batches several
        # windows into one segment (v2 swept 514,080 periods per segment at
        # n = 11 -- 3,400 medians -- because the batching multiplied the
        # capped window by 65535/nu).  A gate or an x-space benchmark that
        # names its own wheel keeps the batching: its launches would be
        # microseconds otherwise.
        if seg_cap is not None:
            self.nseg = max(1, min(self.nseg, int(seg_cap) // self.pv))
            while ((self.nseg * self.pv + 1) * self.Wp + self.q2 >= REDUCE_MAX
                   and self.nseg > 1):
                self.nseg //= 2
        if not self.wide:
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
        # four bytes per entry, the packed u32 (QWORD; narrow record), or
        # three: a u16 index array and a u8 period array (the wide record)
        self.qword = bool(QWORD and (QWORD_WIDE or not self.wide or self.fold))
        qbytes = 4 if self.qword else 3

        def _held(caps):
            """Entries of queue storage a block holds: every queue, or the
            two buffers they alternate between (QUEUE_PINGPONG)."""
            if QUEUE_PINGPONG and len(caps) > 2:
                return max(caps[0::2]) + max(caps[1::2])
            return sum(caps)

        def _caps(sig):
            # never more than 32 items per thread: a round keeps its
            # survivors in ONE 32-bit mask per thread (MAXIT); a queue that
            # fills takes the harmless in-block fallback
            caps = [min(_qcap(self.tile, self.surv[b], sig), 32 * self.tpb)
                    for b in self.bounds2]
            while _held(caps) * qbytes > QUEUE_BYTES_MAX:
                caps = [max(32, ((c // 2 + 31) // 32) * 32) for c in caps]
                if all(c == 32 for c in caps):
                    break
            return caps

        # everything in shared that is NOT the queues, analytically (the
        # kernel is not compiled yet, and compiling once per candidate
        # margin would cost more than the margin is worth)
        ng_ = max(len(self.groups), 1)
        ng4_ = ((ng_ + 3) // 4) * 4

        def _nonq():
            return ((0 if EXTRACT_REGS else self.xe * self.nw * tpb * 4)  # sal
                    + (self.spb * (((ng_ + 7) // 8) * 8) * 2 if self.nepack
                       else self.spb * ng4_ * 4)              # ne
                    + self.spb * 4                           # d2
                    + (self.spb * (len(self.groups2) + 40) * 2   # ne2
                       if ROUND_WINDOW and ((self.wide and not self.fold)
                                            or ROUND_WINDOW_NARROW) else 0)
                    + (int(self._patdev.size) * 4 if PAT_SHARED else 0)
                    + (ng_ * tpb * (2 if self.x0_dtype == np.uint16 else 4)
                       if X0_SHARED else 0)
                    + (len(self.bounds2) + 2) * 4            # queue counters
                    + SMEM_SLACK)
        try:
            import cupy as _cp
            per_sm = int(_cp.cuda.Device().attributes[
                "MaxSharedMemoryPerMultiprocessor"])
        except Exception:                       # noqa: BLE001
            per_sm = SMEM_PER_SM_DEFAULT
        # the ladder, ranked by the shared-memory PREDICTION: most blocks
        # first, and the largest margin among equals
        def _rank():
            nonq_ = _nonq()
            out = []
            for sig in QCAP_SIGMA_LADDER:
                if sig > qcap_sigma:
                    continue                    # never above what was asked
                caps = _caps(sig)
                tot = nonq_ + _held(caps) * qbytes
                blocks = per_sm // (tot + SMEM_BLOCK_RESERVE)
                out.append(((blocks, sig), caps, sig, tot, blocks))
            out.sort(key=lambda z: z[0], reverse=True)
            if not out:
                out = [((0, qcap_sigma), _caps(qcap_sigma), qcap_sigma, 0, 0)]
            return out

        # THE BLOCK SHAPE: the first of the width's preference list whose
        # predicted occupancy reaches the floor; the roomiest if none does
        # (BLOCK_SHAPES_BY_NW says why a lost block outweighs a shape)
        ranked, best_shape = None, None
        for shape in shapes:
            _set_shape(shape)
            got = _rank()
            if best_shape is None or got[0][4] > ranked[0][4]:
                ranked, best_shape = got, shape
            if got[0][4] >= OCC_MIN_BLOCKS4:
                ranked, best_shape = got, shape
                break
        _set_shape(best_shape)

        def _take(choice):
            (_c, self.qcaps, self.qcap_sigma_used, self.smem_predicted,
             self.blocks_predicted) = choice
            self.q1cap = self.qcaps[0]
            self.q2cap = self.qcaps[-1] if len(self.qcaps) > 1 else 1
        _take(ranked[0])
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
        # THE GENERATED TAIL ROUNDS (TAIL_LITERAL): the leading rounds that
        # expect a queue worth generating for and are short enough to unroll
        self.tail_lit = []
        if TAIL_LITERAL:
            for r, (b_, e_) in enumerate(self.rounds):
                if (self.round_lpi[r] != 1 or e_ >= np_
                        or e_ - b_ > TAIL_LITERAL_PRIMES
                        or cand * self.surv[b_] < TAIL_LITERAL_ITEMS
                        or len(self.tail_lit) >= int(TAIL_LITERAL)):
                    break
                self.tail_lit.append(r)
        self._tail_tables()
        self.q3caps = [self.q3cap,
                       self.round_cap[1] if len(self.rounds) > 1 else 1]
        self.d_q3 = [cp.empty(c, dtype=np.uint64) for c in self.q3caps]
        self.d_q3j = [cp.empty(c if self.wide else 1, dtype=np.uint8)
                      for c in self.q3caps]
        # the period tables (v3): one row of pv entries per tail prime and
        # per in-block-round group, rebuilt on the device every launch
        self.d_jb = cp.empty(len(self.primes) * self.pv, dtype=np.uint32)
        self.d_n3 = cp.zeros(len(self.rounds) + 1, dtype=np.int32)

        # ---- the generated source
        ng = len(self.groups)
        ng4 = max(4, ((ng + 3) // 4) * 4)
        glines, blockpre = [], []
        # (row position, statements, value) of every block offset: what the
        # in-block prologue writes to ne/ne2, or `nebuild` to the table row
        self._ne_src = []
        for gi, (Q, dinv) in enumerate(zip(self.gmods, self.dinvs)):
            st, val = self._ne_code(Q, dinv, f"jmod[{gi}]")
            self._ne_src.append((gi, st, val))
            blockpre.append(
                f"        {{ {st}"
                + (f"ne16[ss][{gi}] = (unsigned short)({val}); }}"
                   if self.nepack else
                   f"ne[ss][{gi}] = {val}; }}"))
            off = self.pat_offs[gi]
            # ne for four groups at a time: one 16-byte shared load
            if gi % 4 == 0:
                glines.append(f"            {{ const uint4 n4_{gi // 4} = "
                              f"*(const uint4*)&ne[ss][{gi}];")
            nesel = ["x", "y", "z", "w"][gi % 4]
            if self.lds64:
                # the PAIRS table: entry e is words (e, e + 1) of the
                # pattern, so the window's words w .. w + NW (w = r >> 5)
                # are entries w, w + 2, ... -- every load 8-byte aligned,
                # no select; the shift wraps, so r needs no mask
                off2 = self.pat_offs_dev[gi]
                nl = (self.nw + 2) // 2
                wexpr = ("__umulhi(r, 134217728u)" if WINDOW_ADDR_MUL
                         else "(r >> 5)")
                body = [f"            {{ const unsigned int r = X0({gi}) + n4_{gi // 4}.{nesel} + bw; "
                        f"const uint2* T2 = (const uint2*)(pat + {off2}u) + {wexpr}; "
                        + " ".join(f"const uint2 v{k} = T2[{2 * k}];" for k in range(nl))]
                words = []
                for k in range(nl):
                    words += [f"v{k}.x", f"v{k}.y"]
                for i in range(self.nw):
                    body.append(f" acc[{i}] |= __funnelshift_r({words[i]}, {words[i + 1]}, r);")
                body.append(" }")
            else:
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
        if self.nepack:
            glines = self._nepack_lines()
        # the narrow Barrett rounds are LAZY (ROUND_LAZY): their tables are
        # tripled and neither reduction is corrected (_round_mod32)
        self.lazy = bool(ROUND_LAZY and ROUND_MOD32
                         and (not self.wide or self.fold)
                         and not (ROUND_WINDOW and ROUND_WINDOW_NARROW))
        r2_src, g2table, self.gdesc2 = lit_prefix(
            n, fam, self.primes, self.groups2, table="g2bits", indent=8,
            pname="g2p", unit=self.unit, wide=self.wide and not self.fold,
            reps3=self.lazy)
        self.d_g2bits = cp.asarray(g2table)
        # the rounds in the window's coordinates (ROUND_WINDOW): the window's
        # own tables, built for the round primes -- a pattern in periods, the
        # per-residue row x0r[t][g] (t-major: an item reads one short row)
        # and j0 mod Q per launch
        self.rwin = bool(ROUND_WINDOW and ((self.wide and not self.fold)
                                          or ROUND_WINDOW_NARROW) and self.groups2
                         and self.spb * self.tpb <= 1 << 15
                         and max(int(Q) for Q in self._g2q_list()) < 1 << 15)
        # slot of every round group: 8 u16 slots per 16-byte word, each
        # round starting on a word, so a round reads ceil(groups / 8) words
        # of the residue row and as many of the block's ne2 row
        self.slot2, s_ = [], 0
        for rnd in self.rounds2:
            s_ = -(-s_ // 8) * 8
            for _g in rnd:
                self.slot2.append(s_)
                s_ += 1
        self.ns8 = max(1, -(-s_ // 8))
        if self.rwin:
            (patr, self.patr_offs, dinvs2) = window_patterns(
                n, fam, self.primes, self.groups2, self.Wp, self.nw,
                unit=self.unit)
            g2q = self._g2q_list()
            x0r = np.zeros((self.R1, self.ns8 * 4), dtype=np.uint32)
            for gi, (Q, dinv) in enumerate(zip(g2q, dinvs2)):
                sl = self.slot2[gi]
                x0r[:, sl // 2] |= (((v % np.uint64(Q)) * np.uint64(dinv)
                                     % np.uint64(Q)).astype(np.uint32)
                                    << np.uint32(16 * (sl & 1)))
            self.d_patr = cp.asarray(patr)
            self.d_x0r = cp.asarray(x0r.ravel())
            self._dinvs2 = dinvs2
        else:
            self.patr_offs, self._dinvs2 = [], []
            self.d_patr = cp.zeros(1, dtype=np.uint32)
            self.d_x0r = cp.zeros(4, dtype=np.uint32)
        self._jmod2 = np.zeros(max(len(self.groups2), 1), dtype=np.uint32)
        self.d_jmod2 = cp.zeros(max(len(self.groups2), 1), dtype=np.uint32)
        self._ng8 = max(8, ((len(self.groups) + 7) // 8) * 8)
        if self.rwin:
            for gi, (Q, dinv) in enumerate(zip(self._g2q_list(), self._dinvs2)):
                st, val = self._ne_code(Q, dinv, f"jmod2[{gi}]")
                self._ne_src.append((self._ng8 + self.slot2[gi], st, val))
                blockpre.append(
                    f"        {{ {st}nv[{self.slot2[gi]}] = {val}; }}")
            blockpre.insert(len(blockpre) - len(self.groups2),
                            f"        unsigned int nv[{self.ns8 * 8}]; "
                            f"for (int i_ = 0; i_ < {self.ns8 * 8}; ++i_) "
                            f"nv[i_] = 0u;")
            blockpre.append(
                f"        for (int i_ = 0; i_ < {self.ns8 * 4}; ++i_) "
                f"ne2[ss][i_] = nv[2 * i_] | (nv[2 * i_ + 1] << 16);")
        self._g2q = np.array([Q for _k, Q, _p in self.gdesc2] or [1],
                             dtype=np.uint32)
        self.d_g2q = cp.asarray(self._g2q)
        self.d_g2w = cp.asarray(np.array([self.Wp % int(Q) for Q in self._g2q],
                                         dtype=np.uint32))
        self.d_g2b = cp.zeros(len(self._g2q), dtype=np.uint32)
        self.d_jb2 = cp.empty(len(self._g2q) * self.pv, dtype=np.uint32)
        self.gdesc = []
        # PRE_TABLE: the launch's offset rows, one per (z, s)
        self.nrow = self._ng8 + (self.ns8 * 8 if self.rwin else 0)
        self.gz_max = (1 if self.wide else self.nseg) * self.nu
        self.pre_table = bool(PRE_TABLE and self.nepack
                              and self.gz_max * self.R2 * self.nrow
                              <= PRE_TABLE_MAX)
        if self.pre_table:
            blockpre = []
            self.d_netab = cp.empty(self.gz_max * self.R2 * self.nrow,
                                    dtype=np.uint16)
        else:
            self.d_netab = cp.zeros(8, dtype=np.uint16)
        r2_lines = r2_src.split("\n") if self.groups2 else []
        assert len(r2_lines) == len(self.groups2)
        R = len(self.rounds2) if self.groups2 else 0
        def _compile():
            """Generate the source for the CURRENT queue caps and
            compile it (cached by its full configuration key)."""
            qcaps_src = "\n".join(f"#define Q{i}CAP {c}"
                                   for i, c in enumerate(self.qcaps))
            # queue i's storage: its own, or (QUEUE_PINGPONG) the buffer of
            # queue i - 2, which round i - 1 has finished reading.  A buffer
            # is sized for the largest queue that will ever live in it.
            pp = QUEUE_PINGPONG and len(self.qcaps) > 2
            qd = []
            for i in range(len(self.qcaps)):
                if pp and i >= 2:
                    qd.append(f"#define qi{i} qi{i - 2}\n"
                              f"#define qj{i} qj{i - 2}\n"
                              f"    __shared__ int qn{i};")
                else:
                    held = (max(self.qcaps[i::2]) if pp else self.qcaps[i])
                    if self.qword:
                        # one u32 per entry; qj aliases qi so the macros
                        # that name both read and write the one array
                        qd.append(f"    __shared__ unsigned int qi{i}[{held}];\n"
                                  f"#define qj{i} qi{i}\n"
                                  f"    __shared__ int qn{i};")
                    else:
                        qd.append(f"    __shared__ unsigned short qi{i}[{held}];\n"
                                  f"    __shared__ unsigned char qj{i}[{held}];\n"
                                  f"    __shared__ int qn{i};")
            qdecl = "\n".join(qd)
            qzero = " ".join(f"qn{i} = 0;" for i in range(len(self.qcaps)))
            rounds_src, g0 = [], 0
            # lazy tests OR their table word unmasked: bit 0 is the verdict
            lazy_and = " & 1u" if self.lazy else ""
            for r in range(1, R + 1):
                g1 = g0 + len(self.rounds2[r - 1])
                kend = self.bounds2[r]
                body = " \\\n".join(ln.strip() for ln in r2_lines[g0:g1])
                if ROUND_MOD32 and (not self.wide or self.fold) and not self.rwin:
                    body = " \\\n".join(self._round_mod32(g0, g1))
                if self.rwin:
                    words = sorted({self.slot2[gi] // 8
                                    for gi in range(g0, g1)})
                    lanes = "xyzw"

                    def _rtest(gi):
                        return (f"{{ const unsigned int r = ((s{self.slot2[gi] // 8}"
                                f"{lanes[(self.slot2[gi] % 8) // 2]} >> "
                                f"{16 * (self.slot2[gi] & 1)}) & 0xFFFFu) + (JB); "
                                f"kill |= (patr[{self.patr_offs[gi]}u + (r >> 5)] >> "
                                f"(r & 31u)) & 1u; }}")

                    def _rword(w):
                        return (f"const uint4 xw{w} = (XR)[{w}]; const uint4 nw{w} = "
                                f"*(const uint4*)&(N2)[{4 * w}]; "
                                + " ".join(
                                    f"const unsigned int s{w}{l} = xw{w}.{l} + nw{w}.{l};"
                                    for l in lanes))
                    body = " \\\n".join(
                        [_rword(w) for w in words]
                        + [_rtest(gi) for gi in range(g0, g1)])
                    macro = (f"#define ROUND{r}(XR, N2, JB, KILL) {{ "
                             f"unsigned int kill = 0u; \\\n            {body} "
                             f"\\\n            (KILL) = kill; }}")
                    walk = (f"const unsigned int rs = qv >> LOGP;\n"
                            f"                    const uint4* xr = x0r + "
                            f"(unsigned long long)(t_lo + (int)blockIdx.y * TPB "
                            f"+ (int)(rs & (TPB - 1))) * {self.ns8}ULL;\n"
                            f"                    const unsigned int* n2 = "
                            f"NE2ROW((rs >> LOGTPB) & (SPB - 1));\n"
                            f"                    const unsigned int jb_ = "
                            f"JOF(qv) + ((rs >> 15) & 1u);\n"
                            f"                    unsigned int kl;\n"
                            f"                    ROUND{r}(xr, n2, jb_, kl)")
                else:
                    macro = (f"#define ROUND{r}(OFF, JJ, KILL) {{ const "
                             f"unsigned long long offp = (OFF); \\\n"
                             f"            const unsigned int jj = (JJ); \\\n"
                             f"            unsigned int kill = 0u; \\\n"
                             f"            {body} \\\n"
                             f"            (KILL) = kill{lazy_and}; }}")
                    walk = (f"const unsigned long long oz = WITHJ(offp_of(qv, "
                            f"t_lo, res1x, d2), JOF(qv));\n"
                            f"                    unsigned int kl;\n"
                            f"                    ROUND{r}(oz, JOF(qv), kl)")
                # the push is one atomic per warp (warp_reserve);
                # every thread walks its items (at most MAXIT{r} of them, the
                # queue's capacity over TPB), keeps the survivors in registers,
                # and the warp reserves ONCE per round
                maxit = -(-self.qcaps[r - 1] // self.tpb)
                if maxit > 32:
                    # alive_z is ONE 32-bit mask per thread: a 33rd item
                    # would shift past the word and be dropped silently.
                    # QUEUE_BYTES_MAX keeps every shipped shape far under
                    # this (17-22 at the largest tiles); a bigger block is
                    # a wider mask, not a constant to raise.
                    raise ValueError(
                        f"in-block round {r} would walk {maxit} items per "
                        f"thread (queue {self.qcaps[r - 1]} / tpb {self.tpb}) "
                        f"and the survivor mask holds 32")
                rounds_src.append(f"""{macro}
        {{
            enum {{ MAXIT = {maxit} }};
            unsigned int alive_z = 0u;           /* bit z: item z*TPB + tid survived */
    #pragma unroll
            for (int z = 0; z < MAXIT; ++z) {{
                const int idx = z * TPB + (int)threadIdx.x;
                if (idx < nq{r-1}) {{
                    const unsigned int qv = QGET(qi{r-1}, qj{r-1}, idx);
                    {walk}
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
                        if (p < Q{r}CAP) {{ QCOPY(qi{r}, qj{r}, p, qi{r-1}, qj{r-1}, _z, qi); }}
                        else {{
                            const unsigned long long oz = WITHJ(offp_of(qi, t_lo, res1x, d2), JOF(qi));
                            if (tail_survives(oz, JOF(qi), np_, {kend}, pk, pmask, pres, jb))
                                EMIT(oz, JOF(qi))
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
                              f"    QIT* const qiR = qi{R};\n"
                              f"    QJT* const qjR = qj{R};")
            # The kernel source depends on the family through the killed
            # sets, which are literals in it, and those depend on (family, n)
            # and nothing else: the prefix a(1..n-1) never changes once it
            # exists.  So the FAMILY is in this key (the inherited engine
            # keyed on the sign, which was the whole of a family there).
            key = ("v5", self.wide, n, self.fam,
                   self.unit, self.W1, self.W2, q2, tpb, self.spb, self.pb, self.pv,
                   self.lit, self.k2, self.R3, self.nu, MASK_BITS, self.nres,
                   tuple(self.round_lpi), TAIL_TPB, tuple(self.qcaps),
                   tuple(self.bounds2), tuple(map(tuple, self.groups)),
                   tuple(map(tuple, self.groups2)), str(self.x0_dtype),
                   PAT_SHARED, int(self._patdev.size),
                   self.xe, X0_SHARED, UNROLL, QUEUE_PINGPONG, self.rwin,
                   self.lds64, WINDOW_ADDR_MUL, ROUND_MOD32, ROUND_PACK_MAX,
                   EXTRACT_REGS, self.lazy, self.qword, self.nepack,
                   self.pre_table, self.nrow, self.periodic, self.fold,
                   tuple(self.tail_lit), TAIL_PACK_MAX,
                   tuple(sorted(self._quad.items())))
            gparams = ("" if self.wide and not self.fold else
                       "".join(f",\n        const unsigned long long g2p{i}"
                               for i in range(len(self.gdesc2))))
            fill = {"w1": self.W1, "w2": self.W2, "w": self.Wp,
                    "wide": 1 if self.wide else 0, "gparams": gparams,
                    "two": 1 if self.R2 > 1 else 0, "lit": self.lit,
                    "three": 1 if self.R3 > 1 else 0, "nu": self.nu,
                    "k2": self.k2, "tpb": tpb, "spb": self.spb, "pb": self.pb,
                    "nw": self.nw, "logp": self.logp, "ng": max(ng, 1),
                    "pv": self.pv,
                    "ng4": ng4,
                    "patsh": 1 if PAT_SHARED else 0, "x0sh": 1 if X0_SHARED else 0,
                    "npat": int(self._patdev.size),
                    "xe": self.xe, "xreg": 1 if EXTRACT_REGS else 0,
                    "logtpb": self.logtpb, "logspb": self.logspb,
                    "qtype": ("unsigned short" if self.tile <= 65536
                              else "unsigned int"),
                    "x0type": ("unsigned int" if self.nepack
                               else "unsigned short" if self.x0_dtype == np.uint16
                               else "unsigned int"),
                    "qword": 1 if self.qword else 0,
                    "ngx": max(self.ngx, 1),
                    "pret": 1 if self.pre_table else 0,
                    "nrow": self.nrow, "ng8c": self._ng8,
                    "nedecl": ("    __shared__ __align__(16) unsigned short "
                               f"ne16[SPB][{max(8, ((ng + 7) // 8) * 8)}];"
                               if self.nepack else
                               "    __shared__ __align__(16) unsigned int "
                               "ne[SPB][NG4];"),
                    "unroll": UNROLL, "qcaps": qcaps_src,
                    "ng2": self.ns8 * 4,
                    "rwin": 1 if self.rwin else 0,
                    "qdecl": qdecl, "qzero": qzero,
                    "rounds2": "\n".join(rounds_src),
                    "groups": "\n".join(glines),
                    "blockpre": "\n".join(blockpre),
                        "mask_bits": MASK_BITS, "nres": self.nres,
                    "ttpb": TAIL_TPB,
                    "tailrounds": "".join(
                        _TAILROUND % {"lpi": l}
                        for l in sorted(set(self.round_lpi))) + _JBUILD
                        + self._tailgen_src()
                        + (self._nebuild_src() if self.pre_table else "")}
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
            self.k_tailgen = {r: mod.get_function(f"tailgen{r}")
                              for r in self.tail_lit}
            self.k_jbuild = mod.get_function("jbuild")
            self.k_nebuild = (mod.get_function("nebuild") if self.pre_table
                              else None)

        _compile()
        # THE SHARED-MEMORY PREDICTION IS NOT THE OCCUPANCY when something
        # else caps it -- at pb = 179 the kernel is 10-15 KB of shared, so
        # the prediction says 8 or 9 blocks per SM while 78-88 registers
        # allow 5 or 6, and the chooser above would take the SMALLEST margin
        # to reach a number it cannot have (n = 18 read sigma 2.5 for 5
        # blocks that 6.0 reaches just the same: 0.993-1.000x, round 2).  A
        # margin buys overflow safety (the in-block fallback is 0.67x when
        # it is the rule), and it is free whenever it does not cost a block:
        # so once the kernel has compiled, take the LARGEST margin whose
        # prediction still reaches the occupancy actually achieved, and
        # keep it only if it really does (one recompile; a revert is a
        # cache hit).
        # XE BY REGISTERS (XREG): with the live words in registers the
        # extraction batch costs no shared memory, only NW registers per
        # extra residue -- worth 2.3% at n = 19* of A034881, where it is
        # free (88 registers either way), and a loss where it is not: at
        # n = 16 and 17* the window sits at LIT_MAX and xe = 2 compiles to 96
        # registers against 87 and 91, and xe = 1 reads 0.917 and 0.926 of
        # its clock; at n = 17* and 18* of A219761 they tie.  So an engine
        # not told its xe compiles xe = 1 as well and keeps it when it needs
        # fewer registers (one compile, cached).
        # ... BUT ONLY WHERE THE REGISTERS COST SOMETHING (engine v2, round
        # 2): since PRE_TABLE the wide prologue no longer sets the register
        # peak, and xe = 1 at 72 registers against xe = 2 at 80, both six
        # blocks (five at A083519 n = 19*, where shared memory also binds),
        # read 0.983 at A083518 n = 20*, 0.986 at A083519 n = 19* and 0.968
        # at A083519 n = 17* -- the registers bought nothing and the batch
        # cost 1.4-3.2%.  (They tie at A083519 n = 16* and xe = 1 wins 1.8%
        # at A083518 n = 17*, a filter of seconds.)  So xe = 1 is kept where
        # it gains a block, or where xe = 2 reaches XE1_REGS registers, the
        # product-cliques case above.
        if EXTRACT_REGS and xe is None and self.xe > 1:
            before = (self.xe, dict(self.occupancy))
            self.xe = 1
            _compile()
            gains_block = (self.occupancy["blocks_per_sm"]
                           > before[1]["blocks_per_sm"])
            heavy = before[1]["num_regs"] >= XE1_REGS
            if not ((gains_block or heavy)
                    and self.occupancy["num_regs"] < before[1]["num_regs"]
                    and self.occupancy["blocks_per_sm"]
                    >= before[1]["blocks_per_sm"]):
                self.xe = before[0]
                _compile()
        actual = self.occupancy["blocks_per_sm"]
        if 0 < actual < self.blocks_predicted:
            first = ranked[0]
            better = [c for c in ranked if c[2] > first[2] and c[4] >= actual]
            if better:
                _take(max(better, key=lambda z: z[2]))
                _compile()
                if self.occupancy["blocks_per_sm"] < actual:
                    _take(first)
                    _compile()

    def tail_packs(self, r):
        """[(prime indices, M)] of generated tail round r: consecutive primes
        packed while the product stays under TAIL_PACK_MAX and ROUND_PACK_MAX
        primes -- the one place the cut is made (the emitter and G21 share
        it).  M < 2^30 keeps the lazy pack remainder plus the launch base,
        below 3M, inside the u32 the 32-bit step reads."""
        b, e = self.rounds[r]
        out, i = [], b
        while i < e:
            pack, M = [i], self.primes[i]
            while (i + len(pack) < e and len(pack) < ROUND_PACK_MAX
                   and M * self.primes[i + len(pack)] < TAIL_PACK_MAX):
                pack.append(i + len(pack))
                M *= self.primes[pack[-1]]
            if M >= TAIL_PACK_MAX:
                raise ValueError(f"tail prime {M} does not fit a pack")
            out.append((pack, M))
            i += len(pack)
        return out

    def _tail_tables(self):
        """The generated tail rounds' tables: every prime's kill pattern
        over [0, 2q) (the lazy remainder's range), one after another on word
        boundaries, and the per-pack moduli the launch base is folded by."""
        cp = self.cp
        self._tl_packs = {r: self.tail_packs(r) for r in self.tail_lit}
        self._tl_off, words, off = {}, [], 0
        self._tl_mods, self._tl_slot = [], {}
        for r in self.tail_lit:
            for pack, M in self._tl_packs[r]:
                self._tl_slot[(r, pack[0])] = len(self._tl_mods)
                self._tl_mods.append(M)
                for i in pack:
                    q = self.primes[i]
                    kr = np.array(killed_residues(q, self.n, self.fam,
                                                  self.unit), dtype=np.int64)
                    u = np.arange(2 * q)
                    bits = np.isin(u % q, kr)
                    nw_ = (2 * q + 31) // 32
                    tab = np.zeros(nw_ * 32, dtype=bool)
                    tab[:2 * q] = bits
                    words.append(np.packbits(tab, bitorder="little")
                                 .view(np.uint32))
                    self._tl_off[i] = off
                    off += nw_ * 32
        self.d_g3bits = cp.asarray(np.concatenate(words) if words
                                   else np.zeros(1, dtype=np.uint32))
        self._tb = np.zeros(max(len(self._tl_mods), 1), dtype=np.uint32)
        self.d_tb = cp.zeros(max(len(self._tl_mods), 1), dtype=np.uint32)

    def _tailgen_src(self):
        """The generated tail rounds' kernels (TAIL_LITERAL)."""
        out = []
        for r in self.tail_lit:
            lines = []
            for pack, M in self._tl_packs[r]:
                mg = (1 << 64) // M
                xs = (f"(offp + (unsigned long long)jj * {self.Wp % M}ULL)"
                      if self.wide else "offp")
                tests = []
                for i in pack:
                    q = self.primes[i]
                    tests.append(
                        f"{{ const unsigned int r = rm - __umulhi(rm, "
                        f"{(1 << 32) // q}u) * {q}u; const unsigned int b = "
                        f"{self._tl_off[i]}u + r; "
                        f"kill |= g3bits[b >> 5] >> (b & 31); }}")
                lines.append(
                    f"        {{ const unsigned long long xp = {xs}; "
                    f"const unsigned int rm = (unsigned int)xp - "
                    f"(unsigned int)__umul64hi(xp, {mg}ULL) * {M}u + "
                    f"tb[{self._tl_slot[(r, pack[0])]}]; "
                    + " ".join(tests) + " }")
            out.append(_TAILGEN % {"r": r, "packs": "\n".join(lines),
                                   "to": self.rounds[r][1]})
        return "".join(out)

    def _nepack_lines(self):
        """The window groups' source when x0 and ne are packed two groups
        to a word (NEPACK): one add forms both positions, the low half is
        masked out and the high half shifted down, and each half's funnel
        shift takes its own low five bits.  Only for the pairs table."""
        ng = len(self.gmods)
        lanes = "xyzw"
        npair = (ng + 1) // 2
        out = []
        for k in range(npair):
            if k % 4 == 0:
                # ne for EIGHT groups at a time: one 16-byte shared load
                out.append(f"            {{ const uint4 n8_{k // 4} = "
                           f"*(const uint4*)&ne16[ss][{8 * (k // 4)}];")
            body = [f"            {{ const unsigned int sm = x0[{k}] + "
                    f"n8_{k // 4}.{lanes[k % 4]} + bw * 0x10001u;"]
            for half, gi in ((0, 2 * k), (1, 2 * k + 1)):
                if gi >= ng:
                    continue
                off2 = self.pat_offs_dev[gi]
                head = (" { const unsigned int r = sm & 0xFFFFu; "
                        "const unsigned int sh = sm; " if half == 0 else
                        " { const unsigned int r = sm >> 16; "
                        "const unsigned int sh = r; ")
                nl, steps = window_plan(self.gmods[gi], self.nw, self.periodic)
                if gi in self._quad:
                    b = [head + f"const uint4 q4 = ((const uint4*)(pat + "
                         f"{off2}u))[__umulhi(r, 134217728u)];"]
                    words = ["q4.x", "q4.y", "q4.z", "q4.w"]
                else:
                    b = [head + f"const uint2* T2 = (const uint2*)(pat + {off2}u) + "
                         f"__umulhi(r, 134217728u); "
                         + " ".join(f"const uint2 v{j} = T2[{2 * j}];"
                                    for j in range(nl))]
                    words = []
                    for j in range(nl):
                        words += [f"v{j}.x", f"v{j}.y"]
                for i, st in enumerate(steps):
                    if st[0] == "read":
                        src = (f"__funnelshift_r({words[i]}, "
                               f"{words[i + 1]}, sh)")
                    elif st[2]:
                        src = (f"__funnelshift_r(b{st[1]}, b{st[1] + 1}, "
                               f"{st[2]}u)")
                    else:
                        src = f"b{st[1]}"
                    b.append(f" const unsigned int b{i} = {src}; "
                             f"acc[{i}] |= b{i};")
                b.append(" }")
                body.append("".join(b))
            body.append(" }")
            if k % 4 == 3 or k == npair - 1:
                body.append(" }")
            out.append("".join(body))
        return out

    def _ne_code(self, Q, dinv, jm):
        """(C statements, value) of one block offset: ne = (j0 mod Q +
        sg*PV - E) mod Q with E = ((W1 * D) mod Q) * Dinv mod Q, D the
        block's second-level complement (`dcur`).  The one derivation the
        in-block prologue and `nebuild` both emit."""
        mg = (1 << 64) // Q
        red = (f"unsigned int r = (unsigned int)xx - "
               f"(unsigned int)__umul64hi(xx, {mg}ULL) * {Q}u; "
               f"if (r >= {Q}u) r -= {Q}u; ")
        red2 = (f"r = (unsigned int)xx - "
                f"(unsigned int)__umul64hi(xx, {mg}ULL) * {Q}u; "
                f"if (r >= {Q}u) r -= {Q}u; ")
        st = (f"unsigned long long xx = (unsigned long long){self.W1}u"
              f" * (unsigned long long)dcur; {red}"
              f"xx = (unsigned long long)r * {dinv}ULL; {red2}"
              f"const unsigned int bs = ({jm} + shift) % {Q}u; ")
        return st, f"(bs + {Q}u - r) % {Q}u"

    def _nebuild_src(self):
        """The per-launch offset table kernel (PRE_TABLE): thread (z, s)
        writes row z*R2 + s -- the window groups' ne at 0..NG8C, the round
        slots at NG8C + slot (padding slots zero)."""
        used = {pos for pos, _st, _v in self._ne_src}
        lines = [f"    {{ {st}row[{pos}] = (unsigned short)({val}); }}"
                 for pos, st, val in self._ne_src]
        lines += [f"    row[{pos}] = 0;" for pos in range(self._ng8, self.nrow)
                  if pos not in used]
        body = "\n".join(lines)
        return (r"""
extern "C" __global__ void nebuild(
        const int R2, const int GZ, const int u0,
        const unsigned int* __restrict__ res2c,
        const unsigned int* __restrict__ res2d,
        const unsigned int* __restrict__ jmod,
        const unsigned int* __restrict__ jmod2,
        unsigned short* __restrict__ out)
{
    const int idx = blockIdx.x * blockDim.x + (int)threadIdx.x;
    if (idx >= R2 * GZ) return;
    const int z = idx / R2;
    const int s = idx - z * R2;
#if WIDE
    const int sg = 0;
#else
    const int sg = z / NU;
#endif
    unsigned int dcur = 0u;
#if TWOLEVEL
    unsigned int c = res2c[s];
#if THREELEVEL
    const unsigned int cb = res2d[u0 + z % NU];
    const unsigned long long cc = (unsigned long long)c + cb;
    c = (unsigned int)(cc >= (unsigned long long)W2C ? cc - W2C : cc);
#endif
    dcur = W2C - c;
#endif
    const unsigned int shift = (unsigned int)sg * PV;
    (void)jmod2;
    unsigned short* row = out + (unsigned long long)idx * NROW;
""" + body + "\n}\n")

    def x0_table(self):
        """The window's x0 table as (groups, R1) integers, unpacked from the
        device layout whichever it is (G14 reads the chain through it)."""
        raw = self.cp.asnumpy(self.d_x0).astype(np.int64)
        if not self.nepack:
            return raw.reshape(len(self.groups), self.R1)
        xp = raw.reshape(self.ngx, self.R1)
        out = np.empty((len(self.groups), self.R1), dtype=np.int64)
        out[0::2] = xp & 0xFFFF
        out[1::2] = (xp >> 16)[:len(self.groups) // 2]
        return out

    def _round_mod32(self, g0, g1):
        """The narrow record's round tests for groups g0..g1-1 (single
        primes) with ONE 64-bit Barrett step per PACK of consecutive primes
        whose product M is under 2^31, and a 32-bit one per prime:
        offp mod q = (offp mod M) mod q.  Both steps are the one-conditional-
        subtraction reduction with the floor magic, exact for every
        numerator below the word (the paper bound in REDUCE_MAX's comment,
        at 2^32 for the second); M < 2^31 keeps 2M inside the u32."""
        qs = self._g2q_list()
        out = []
        for pack, M in self.round_packs(g0, g1):
            mg = (1 << 64) // M
            # LAZY (ROUND_LAZY): rm in [0, 2M) and r in [0, 2q), both left
            # uncorrected, the tripled table absorbing base + r < 3q; an
            # inline group's mask holds one period, so a pack with one keeps
            # both corrections
            lazy = self.lazy and all(self.gdesc2[gi][0] != "inline"
                                     for gi in pack)
            # THE WIDE RECORD FOLDS ITS PERIOD INTO THE PACK (ROUND_FOLD):
            # the candidate is offp + jj*W' + base, and offp + jj*(W' mod M)
            # is congruent to its first two terms modulo every prime of the
            # pack and below 2^63 + 2^8 * 2^31 < 2^64 -- so one multiply-add
            # a pack puts the wide rounds on the narrow record's arithmetic
            # (the base rides the table index, g2p, exactly as it does there)
            xs = (f"(offp + (unsigned long long)jj * {self.Wp % M}ULL)"
                  if self.fold else "offp")
            head = (f"{{ const unsigned long long xp = {xs}; "
                    f"unsigned int rm = (unsigned int)xp - "
                    f"(unsigned int)__umul64hi(xp, {mg}ULL) * {M}u; "
                    + ("" if lazy else f"if (rm >= {M}u) rm -= {M}u;"))
            tests = []
            for gi in pack:
                q = qs[gi]
                if len(pack) == 1:
                    red = "const unsigned int r = rm; "
                else:
                    red = (f"unsigned int r = rm - __umulhi(rm, "
                           f"{(1 << 32) // q}u) * {q}u; "
                           + ("" if lazy else f"if (r >= {q}u) r -= {q}u; "))
                if self.gdesc2[gi][0] == "inline":
                    tests.append(f"{{ {red}kill |= (unsigned int)((g2p{gi} "
                                 f">> r) & 1ULL); }}")
                elif lazy:
                    tests.append(f"{{ {red}const unsigned int b = "
                                 f"(unsigned int)g2p{gi} + r; "
                                 f"kill |= g2bits[b >> 5] >> (b & 31); }}")
                else:
                    tests.append(f"{{ {red}const unsigned int b = "
                                 f"(unsigned int)g2p{gi} + r; "
                                 f"kill |= (g2bits[b >> 5] >> (b & 31)) & 1u; }}")
            out.append(head + " " + " ".join(tests) + " }")
        return out

    def round_packs(self, g0, g1):
        """[(group indices, M)]: round groups g0..g1-1 cut into PACKS of up
        to ROUND_PACK_MAX consecutive single primes whose product M stays
        under 2^31 -- the one place the cut is made (_round_mod32 emits it,
        G21 emulates it).  M < 2^31 is what keeps a lazy pack remainder,
        below 2M, inside the u32 the 32-bit step reads."""
        qs = self._g2q_list()
        out, i = [], g0
        while i < g1:
            pack, M = [i], qs[i]
            while (i + len(pack) < g1 and len(pack) < ROUND_PACK_MAX
                   and M * qs[i + len(pack)] < 1 << 31):
                pack.append(i + len(pack))
                M *= qs[pack[-1]]
            out.append((pack, M))
            i += len(pack)
        return out

    # ------------------------------------------------------------- geometry
    def _g2q_list(self):
        """The modulus of every in-block round group, in order."""
        out = []
        for g in self.groups2:
            Q = 1
            for i in g:
                Q *= self.primes[i]
            out.append(Q)
        return out

    def window_words(self, pat, gi, r):
        """The NW words of window group gi at pattern position r, formed from
        the DEVICE table `pat` (a host copy of d_pat) exactly as the kernel
        forms them: the words its plan READS, through its layout -- plain,
        pairs or quads -- funnel-shifted by the position's low five bits,
        and the words it DERIVES by constant funnel shifts of those
        (`window_plan`).  G14 reads every bit it checks through this.
        `pat` is a uint64 array and `r` a position or an array of them."""
        M32 = np.uint64(0xFFFFFFFF)
        r = np.asarray(r, dtype=np.int64)

        def fun(lo, hi, s):
            # a 32-bit funnel shift; at s = 0 the high word shifts out whole
            s = np.asarray(s, dtype=np.uint64) & np.uint64(31)
            return ((lo >> s) | (hi << (np.uint64(32) - s))) & M32

        w = r >> 5
        if not self.lds64:
            off = self.pat_offs[gi]
            return [fun(pat[off + w + i], pat[off + w + i + 1], r)
                    for i in range(self.nw)]
        loads, steps = window_plan(self.gmods[gi], self.nw, self.periodic)
        off = self.pat_offs_dev[gi]
        if gi in self._quad:
            words = [pat[off + 4 * w + k] for k in range(4)]
        else:
            words = []
            for j in range(loads):
                words += [pat[off + 2 * (w + 2 * j)],
                          pat[off + 2 * (w + 2 * j) + 1]]
        b = []
        for i, st in enumerate(steps):
            if st[0] == "read":
                b.append(fun(words[i], words[i + 1], r))
            elif st[2]:
                b.append(fun(b[st[1]], b[st[1] + 1], st[2]))
            else:
                b.append(b[st[1]])
        return b

    def pat_word_index(self, gi, w):
        """Where word w of window group gi's pattern sits in the DEVICE
        table (d_pat): at its offset plus w, or -- the pairs table -- as the
        first half of entry w (G14 reads every checked bit through this)."""
        if gi in self._quad:
            return self.pat_offs_dev[gi] + 4 * int(w)
        if self.lds64:
            return self.pat_offs_dev[gi] + 2 * int(w)
        return self.pat_offs[gi] + int(w)

    def j_of(self, k):
        return int(k) // self.W

    def density(self):
        return self.R / float(self.W)

    def bytes_held(self):
        n = (self.d_res1x.nbytes + self.d_pres.nbytes + self.d_pk.nbytes
             + self.d_pmask.nbytes + sum(b.nbytes for b in self.d_out)
             + self.d_res2c.nbytes + self.d_res2d.nbytes + self.d_pat.nbytes
             + self.d_x0.nbytes + self.d_g2bits.nbytes
             + sum(q.nbytes for q in self.d_q3) + sum(q.nbytes for q in self.d_q3j)
             + self.d_jb.nbytes + self.d_jb2.nbytes
             + self.d_x0r.nbytes + self.d_patr.nbytes
             + self.d_netab.nbytes
             + sum(b.nbytes for b in self.d_outj))
        return int(n)

    def config(self):
        return {"n": self.n, "fam": self.fam, "s": self.s, "p1": self.p1,
                "p2": self.p2, "p3": self.p3, "q2": self.q2,
                "unit": self.unit, "W": int(self.W), "Wp": int(self.Wp),
                "R": int(self.R), "R1": self.R1, "R2": self.R2,
                "R3": self.R3, "nu": self.nu, "per_launch": self.per_launch,
                "pb": self.pb, "pv": self.pv, "nseg": self.nseg,
                "spb": self.spb, "xe": self.xe,
                "wide": self.wide,
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
        j0 mod Q per window group (j0 = base / Wp: Wp*Dinv == 1 mod Q);
        then build the period tables jb / jb2 on the device (v3)."""
        j = int(base) // self.Wp
        if j < (1 << 64):
            bmod = (self._wmod * (np.uint64(j) % self._qs)) % self._qs
        else:
            bmod = np.array([(int(w) * (j % int(q))) % int(q)
                             for w, q in zip(self._wmod, self._qs)],
                            dtype=np.uint64)
        self._pk[:, 3] = bmod.astype(np.uint32)
        self.d_pk.set(self._pk.ravel())
        if self.tail_lit:
            for k, M in enumerate(self._tl_mods):
                self._tb[k] = int(base) % M
            self.d_tb.set(self._tb)
        self.d_bmod.set(bmod.astype(np.uint32))
        for gi, Q in enumerate(self.gmods):
            self._jmod[gi] = j % Q
        self.d_jmod.set(self._jmod)
        if self.rwin:
            for gi, Q in enumerate(self._g2q_list()):
                self._jmod2[gi] = j % Q
            self.d_jmod2.set(self._jmod2)
        if not self.wide:
            return group_params(self.gdesc2, base)
        g2b = np.array([int(base) % int(Q) for Q in self._g2q], dtype=np.uint32)
        self.d_g2b.set(g2b)
        self._build_jtables()
        return group_params(self.gdesc2, base) if self.fold else ()

    def _build_jtables(self):
        """jb[i][j] = (j*W' + base) mod q_i for every tail prime, jb2 the
        same per in-block-round group, for j below the window (device)."""
        rows = len(self.primes)
        tot = rows * self.pv
        self.k_jbuild((-(-tot // 256),), (256,),
                      (np.int32(rows), np.int32(self.pv), self.d_q,
                       self.d_wmod, self.d_bmod, self.d_jb))
        rows2 = len(self._g2q)
        tot2 = rows2 * self.pv
        self.k_jbuild((-(-tot2 // 256),), (256,),
                      (np.int32(rows2), np.int32(self.pv), self.d_g2q,
                       self.d_g2w, self.d_g2b, self.d_jb2))

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
        if self.pre_table:
            tot = self.R2 * gz
            self.k_nebuild((-(-tot // 128),), (128,),
                           (np.int32(self.R2), np.int32(gz), np.int32(u0),
                            self.d_res2c, self.d_res2d, self.d_jmod,
                            self.d_jmod2, self.d_netab))
        self.k_sieve((gy, gx, gz), (self.tpb,),
                     (np.int32(self.R1), np.int32(self.R2), np_,
                      self.d_pmask, self.d_pres,
                      self.d_out[b], self.d_outj[b], self.d_n[b],
                      np.int32(HIT_CAP),
                      self.d_q3[0], self.d_q3j[0], self.d_n3,
                      np.int32(self.q3cap),
                      self.d_pk, self.d_res1x, self.d_x0, self.d_res2c,
                      self.d_res2d, np.int32(u0), np.int32(t_lo),
                      np.int32(nper), self.d_jmod, self.d_pat,
                      self.d_g2bits, self.d_jb, self.d_jb2,
                      self.d_x0r, self.d_jmod2, self.d_patr,
                      self.d_netab, *gps))
        R = len(self.rounds)
        for r, (fr, to) in enumerate(self.rounds):
            qi, qo = self.d_q3[r & 1], self.d_q3[(r + 1) & 1]
            qij, qoj = self.d_q3j[r & 1], self.d_q3j[(r + 1) & 1]
            ci = self.round_cap[r] if r else min(self.round_cap[0], self.q3cap)
            co = self.round_cap[r + 1] if r + 1 < R else 1
            lpi = self.round_lpi[r]
            grid = max(1, -(-ci // (self.tail_tpb // lpi)))
            if r in self.k_tailgen:
                self.k_tailgen[r]((grid,), (self.tail_tpb,),
                                  (qi, qij, self.d_n3[r:r + 1], np.int32(ci),
                                   qo, qoj, self.d_n3[r + 1:r + 2],
                                   np.int32(co), np_,
                                   self.d_out[b], self.d_outj[b], self.d_n[b],
                                   np.int32(HIT_CAP),
                                   self.d_pk, self.d_pmask, self.d_pres,
                                   self.d_jb, self.d_g3bits, self.d_tb))
                continue
            self.k_tails[lpi]((grid,), (self.tail_tpb,),
                              (qi, qij, self.d_n3[r:r + 1], np.int32(ci),
                               qo, qoj, self.d_n3[r + 1:r + 2], np.int32(co),
                               np.int32(fr), np.int32(to), np_,
                               self.d_out[b], self.d_outj[b], self.d_n[b],
                               np.int32(HIT_CAP),
                               self.d_pk, self.d_pmask, self.d_pres,
                               self.d_jb))
        self.d_n[b].get(out=self._h_n[b], blocking=False)
        self.d_out[b][:self._pre].get(out=self._h_out[b], blocking=False)
        if self.wide:
            self.d_outj[b][:self._pre].get(out=self._h_outj[b],
                                           blocking=False)
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
            if self.wide:
                js = (self._h_outj[b][:cnt] if cnt <= self._pre
                      else self.cp.asnumpy(self.d_outj[b][:cnt]))
                Wp = self.Wp
                # the record is (within-period offset, period): the value
                # is rebuilt here, in Python ints, the one place it exists
                surv = sorted(v for v in (self.r0 + self.unit * (base + int(o)
                                                       + int(j) * Wp)
                                          for o, j in zip(offs.tolist(),
                                                          js.tolist()))
                              if v >= clip)
            else:
                surv = sorted(v for v in (self.r0 + self.unit * (base + int(o))
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
    for both families; and the CRT recombination reproduces the one-level
    wheel exactly."""
    fams = (FA, FB)
    for fam in fams:
        top = frontier(fam) + 1
        for n, p1 in ((5, 7), (9, 11), (11, 11), (11, 13), (top, 13)):
            W, res = wheel(n, fam, p1)
            Wo, reso = wheel_residues(fam, n, p1)
            if W != Wo or list(res) != list(reso):
                return False, (f"G7 FAIL: {fam} n={n} p1={p1}: lifted "
                               f"{len(res)} residues mod {W}, oracle "
                               f"{len(reso)} mod {Wo}")
        for n, p1, p2 in ((11, 7, 13), (11, 11, 17), (9, 7, 11)):
            W1, r1 = wheel(n, fam, p1)
            W2, r2 = wheel(n, fam, p2, lo=p1)
            inv = pow(W1 % W2, -1, W2)
            got = sorted(int(a) + W1 * (((int(b) - int(a)) * inv) % W2)
                         for a in r1 for b in r2)
            Wf, ref_res = wheel(n, fam, p2)
            if W1 * W2 != Wf or got != [int(v) for v in ref_res]:
                return False, (f"G7 FAIL: {fam} CRT recombination at n={n} "
                               f"({p1},{p2}]: {len(got)} vs {len(ref_res)}")
        # UNIT SPACE: the x' wheel == a brute-force walk of ITS period
        # checked against the ORACLE's x-space divisibility on x = unit*x'
        # -- the definition, not the engines' construction -- and the CRT
        # recombination holds with a unit too.  The unit is 6 at every
        # filter here; each filter is still walked separately, because the
        # kill sets are not the same from one to the next.
        for n, p1, unit in ((9, 13, 6), (11, 13, 6), (top - 1, 13, 6),
                            (top, 17, forced_unit(top, fam)), (2, 7, 2)):
            if forced_unit(n, fam) % unit:
                return False, (f"G7 FAIL: unit {unit} is not forced at n = "
                               f"{n}; the case list is wrong")
            W, res = wheel(n, fam, p1, unit=unit)
            qs = [q for q in primerange(2, p1 + 1) if unit % q]
            Wo = 1
            for q in qs:
                Wo *= q
            killed = {q: forbidden_k_residues(q, n, fam) for q in qs}
            reso = [r for r in range(Wo)
                    if all((unit_residue(n, fam, unit) + unit * r) % q
                           not in killed[q] for q in qs)]
            if W != Wo or list(res) != reso:
                return False, (f"G7 FAIL: {fam} n={n} p1={p1} unit={unit}: "
                               f"lifted {len(res)} residues mod {W}, oracle "
                               f"walk {len(reso)} mod {Wo}")
        for n, p1, p2, unit in ((11, 11, 13, 6), (top - 1, 13, 19, 6),
                                (top, 11, 13, 6)):
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
    # a unit that nothing forces here -- 30, the linear ladders' habit, and
    # 10 -- must NOT be attempted at any filter: assert_unit refuses, which
    # is the property that keeps a carried-in wheel from silently thinning
    # the line; so must a unit that is forced but not squarefree.
    for n, unit in ((11, 42), (14, 14), (13, 12), (1, 6), (14, 30)):
        try:
            wheel(n, FA, 13, unit=unit)
            return False, (f"G7 FAIL: a unit-{unit} wheel was built at n = "
                           f"{n}, where it is not admissible")
        except ValueError:
            pass
    return True, ("G7 ok: CRT-lifted wheel == oracle period walk at (n,p1) = "
                  "(5,7), (9,11), (11,11), (11,13) and each open index, for "
                  "both families (the offset-0 A083519 included); the two-level "
                  "CRT recombination == the one-level wheel at three (p1,p2] "
                  "splits; in CLASS space the t wheel == the oracle's "
                  "divisibility on x = r + unit*t at unit 6, at each family's "
                  "own forced unit at its open index, and at unit 2 at n = 2, "
                  "and recombines across two levels; and the units 42, 14, "
                  "12, 30 and 6-at-n=1 are REFUSED, since a prime of each is not "
                  "forced there (or it is not squarefree)")


def g8_wheel_partitions_the_period():
    """Kept + killed == the whole period, and the count is the formula.

    The direction that matters is the second one: a wheel that DROPS a
    residue it should have kept loses candidates silently, and no parity
    gate against another engine using the same wheel could ever see it.
    """
    from plus2_reference import w as w_formula
    cases = []
    for fam in FAMILIES:
        top = frontier(fam) + 1
        mid = min(15, top - 1)
        cases += [(fam, mid, 13, 1, 1), (fam, mid, 23, 1, 1),
                  (fam, 10, 23, 1, 1), (fam, top, 19, 1, 1),
                  (fam, mid, 37, 23, 1), (fam, mid, 31, 23, 1),
                  (fam, top, 47, 37, 1)]
    # The production levels, in unit space, at EVERY filter the campaign can
    # open at or promote into over its first night -- the unit is the same
    # 6 at each, the kill sets are not, so each filter's split is its own.
    for fam in FAMILIES:
        n0 = frontier(fam) + 1
        for n in range(n0 - 3, n0 + 1):
            unit = forced_unit(n, fam)
            for lv in plan(n, fam, unit)[:3]:
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
                  f"levels for every family, and the PLANNED production "
                  f"levels at each family's open index and the three before "
                  f"it, in its forced class -- the level split is re-derived "
                  f"per filter, never carried")


def g9_gpu_matches_cpu():
    """GPU survivor stream == CPU survivor stream, bit for bit.

    Populated windows at several filters and heights, both families, one-,
    two- and three-level wheels, the top windows hard against the enforced
    ceilings and ABOVE 2^64 (the CPU side is Python ints all the way up),
    and a CLIPPED PERIOD 0 -- the window every campaign here starts in.  An
    empty-vs-empty comparison is vacuous and is refused.
    """
    from plus2_search import k_proof
    cross_a = k_proof(14, FA)           # 4.3e13: A083518's open index
    cross_b = k_proof(11, FB)           # 3.9e14: A083519's open index
    ceil = k_ceil(14, FA)               # 1e30, the enforced ceiling
    W19 = 9_699_690
    cases = (
        # fam, n, p1, p2, p3, q2, x_lo, span, unit
        #
        # q2 = 32 throughout; the wheel here keeps about half of the line
        # per small prime, so a 1e7-4e7 window at q2 = 32 holds hundreds to
        # thousands of survivors, which is what makes a dense CPU sieve
        # affordable as the reference.
        (FA, 9, 13, None, None, 32, 2 * 10 ** 9, 2 * 10 ** 7, 1),
        (FB, 8, 13, None, None, 32, 2 * 10 ** 9, 2 * 10 ** 7, 1),
        (FA, 13, 13, None, None, 32, 10 ** 12, 10 ** 7, 1),
        (FB, 10, 13, 23, None, 32, 10 ** 12, 10 ** 7, 1),
        (FA, 13, 11, 19, 23, 32, 10 ** 12, 10 ** 7, 1),
        (FB, 11, 13, 23, None, 32, 9 * 10 ** 14, 2 * 10 ** 7, 1),
        (FA, 14, 13, 19, 23, 32, 9 * 10 ** 14, 2 * 10 ** 7, 1),
        # PERIOD 0, clipped at the engine floor: the campaign's first window,
        # and the one place a wheel offset can be wrong without any other
        # window noticing (from x = 64: the floor is q2 = 32 here, because
        # the smallest value is a(off)*x + 2 -- 3x + 2 in A083518, x + 2 in
        # A083519, whose a(0) = 1)
        (FA, 9, 13, 19, None, 32, 64, W19 - 64, 1),
        (FB, 10, 13, 19, None, 32, 64, W19 - 64, 1),
        # CLASS SPACE: the device sweeps x = 3 + 6t and the host maps back;
        # the CPU engine still marks the dense x line, so the forcing -- and
        # the class's nonzero residue, which product-cliques never had -- is
        # checked here as well as the fold, at filters from 9 to each open
        # index.
        (FA, 11, 13, 19, None, 32, 10 ** 12, 10 ** 7, 6),
        (FB, 10, 13, 19, 23, 32, 10 ** 12, 10 ** 7, 6),
        (FA, 14, 13, 19, 23, 32, 10 ** 12, 2 * 10 ** 7, 6),
        (FB, 11, 13, 23, None, 32, 10 ** 12, 2 * 10 ** 7, 6),
        (FA, 12, 13, 19, 23, 32, 10 ** 15, 2 * 10 ** 7, 6),
        (FB, 9, 13, 23, None, 32, 10 ** 15, 2 * 10 ** 7, 6),
        (FA, 14, 11, 17, 23, 32, 10 ** 15, 4 * 10 ** 7, 6),
        # ABOVE 2^64, and past each open index's PROOF CROSSING: both
        # engines are Python ints
        (FB, 11, 13, 19, 23, 32, cross_b + 10 ** 12, 2 * 10 ** 7, 6),
        (FA, 14, 13, 19, 23, 32, cross_a + 10 ** 13, 2 * 10 ** 7, 6),
        (FA, 13, 13, 19, None, 32, 10 ** 21, 10 ** 7, 6),
        (FB, 11, 13, 19, None, 32, 10 ** 22, 10 ** 7, 6),
        # SUBSET WHEELS -- the shape the campaign actually runs.  A prime the
        # wheel declines (11 here) must be sieved instead, and the survivor
        # stream must be the same as a dense CPU sieve that knows nothing
        # about either.
        (FA, 13, [5, 7, 13, 17, 19], [23, 29], None, 32,
         10 ** 12, 10 ** 7, 6),
        (FB, 11, [5, 7, 13, 17], [19, 23], [29], 32,
         10 ** 15, 2 * 10 ** 7, 6),
        # HARD AGAINST THE 1e30 CEILING, both families: the base is a
        # 100-bit Python int on both engines
        (FA, 14, 13, 19, 23, 32, ceil - 10 ** 9, 10 ** 7, 6),
        (FB, 11, 13, 19, 23, 32, ceil - 10 ** 9, 2 * 10 ** 7, 6),
        # A FIRST LEVEL PAST R1_MAX -- the second budget (R1_MAX_BIG), which
        # the long wheels of the expensive filters take (9.3 million first-
        # level residues for the wheel to 53 at n = 20* of A083518): eight
        # primes in the first level here, millions of residues, on the
        # narrow record and forced onto the wide one, in a sieve deep enough
        # that the window takes dozens of groups (x0 indexed past 2^24)
        (FA, 14, [5, 7, 11, 13, 17, 19, 23, 29], None, None, 256,
         10 ** 15, 2 * 10 ** 7, 6),
        (FA, 14, [5, 7, 11, 13, 17, 19, 23, 29], [31], None, 256,
         10 ** 15, 2 * 10 ** 7, 6, True),
    )
    total, big = 0, []
    for case in cases:
        fam, n, p1, p2, p3, q2, k_lo, span, unit = case[:9]
        wide = case[9] if len(case) > 9 else None
        eng = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit,
                        wide=wide)
        if wide is not None and eng.wide != wide:
            return False, f"G9 FAIL: the record came up {eng.wide}, asked {wide}"
        if eng.R1 > R1_MAX:
            big.append(f"{eng.R1:,} first-level residues "
                       f"({'wide' if eng.wide else 'narrow'})")
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
    if len(big) < 2:
        return False, ("G9 FAIL: no window ran a first level past R1_MAX -- "
                       "the second budget is unpinned")
    return True, (f"G9 ok: GPU stream == CPU stream on {len(cases)} populated "
                  f"windows ({total} survivors) -- one-, two- and three-level "
                  f"wheels in x space AND in the class 3 (mod 6), SUBSET "
                  f"wheels that decline 11 to the sieve, both families (the "
                  f"offset-0 A083519 included), filters n = 8 to each open "
                  f"index, heights 2e9 -> {ceil:.3g} with windows ABOVE "
                  f"2^64 and past the proof crossings ({cross_a:.3g}, "
                  f"{cross_b:.3g}), two hard against the 1e30 ceiling, "
                  f"period 0 clipped at the engine floor, and first levels "
                  f"past R1_MAX (the second budget): {'; '.join(big)}")


def g13_production_wheel_constants():
    """The baked CRT constants of the configurations the campaigns run.

    G9 proves the multi-level KERNEL is right, but only at splits whose
    combined wheel a dense CPU sieve can follow.  The production split is
    bigger than that by orders of magnitude, and what differs there is not
    code but literals compiled into the source: W1, W2 and W1^-1 mod W2.
    This gate checks those literals directly, on the host, against the
    definition, for the filters every family will actually run.
    """
    rng = np.random.default_rng(20260916)
    from plus2_reference import forced_primes, w as w_formula
    cases = [(FA, 13, 23, 37, 47, 1), (FA, 14, 23, 37, 47, 1),
             (FB, 10, 23, 37, 47, 1), (FB, 11, 23, 37, None, 1)]
    # EVERY opening the campaign can start at or promote into over its first
    # night, at the wheel the planner actually picks there and at the unit
    # -- both re-derived per filter.
    for fam in FAMILIES:
        n0 = frontier(fam) + 1
        for n in range(n0 - 3, n0 + 1):
            unit = forced_unit(n, fam)
            p1, p2, p3 = plan(n, fam, unit)[:3]
            cases.append((fam, n, p1, p2, p3, unit))
            # and one alternative -- a PREFIX split of the same filter, so
            # the gate is not merely re-checking the planner's own
            # arithmetic and the two wheel shapes are both exercised
            cases.append((fam, n, 19, 31, 43, unit))
    for fam, n, p1, p2, p3, unit in cases:
        W1, r1 = wheel(n, fam, p1, unit=unit)
        # a planned wheel may be one- or two-level at the opening filters
        # (the period cap keeps it short); an absent level is modulus 1
        if p2:
            W2a, r2 = wheel(n, fam, p2, lo=p1, unit=unit)
        else:
            W2a, r2 = 1, np.zeros(1, dtype=np.int64)
        if p3:
            W2b, r3 = wheel(n, fam, p3, lo=p2 or p1, unit=unit)
            EA = W2b * pow(W2b % W2a, -1, W2a) if W2a > 1 else 0
            EB = W2a * pow(W2a % W2b, -1, W2b)
        else:
            W2b, r3, EA, EB = 1, np.zeros(1, dtype=np.int64), 1, 0
        W2 = W2a * W2b
        if W2 >= 1 << 32 or W1 >= 1 << 32 or W1 * W2 >= 1 << 63:
            return False, (f"G13 FAIL: {fam} n={n} ({p1},{p2},{p3}] unit "
                           f"{unit}: W1 = {W1}, W2 = {W2} exceed the u32 / "
                           f"2^63 bounds the kernel's arithmetic rests on")
        inv = pow(W1 % W2, -1, W2) if W2 > 1 else 0
        if W2 > 1 and W1 % W2 * inv % W2 != 1:
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
        # the kill check is in X SPACE, on x = unit*x', against the x-space
        # killed set: the unit's own primes included, which must never
        # kill a multiple of the unit
        top = max(qs)
        killed = {q: set(killed_residues(q, n, fam)) for q in qs}
        forced = 1
        for q in forced_primes(fam, n, upto=top + 1):
            if q in qs or unit % q == 0:
                forced *= q
        r0 = unit_residue(n, fam, unit)
        fclass = unit_residue(n, fam, forced)
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
                if (r0 + unit * x) % q in bad:
                    return False, (f"G13 FAIL: {fam} n={n} ({p1},{p2},{p3}] "
                                   f"unit {unit}: x = {unit}*{x} is killed by "
                                   f"q={q}")
            if (r0 + unit * x) % forced != fclass:
                return False, (f"G13 FAIL: {fam} n={n}: a wheel residue x = "
                               f"{r0} + {unit}*{x} is not == {fclass} (mod "
                               f"{forced}), the class every forced prime "
                               f"pins x to at this filter")
    return True, (f"G13 ok: the wheel constants (W1, W2a, W2b, W1^-1 and the "
                  f"two CRT lifts) are exact at {len(cases)} configurations: "
                  f"x-space (23,37,47] at n = 10..14 of both families, and "
                  f"the PLANNED production wheel plus a prefix alternative "
                  f"at each family's open index and the three before it, in "
                  f"its forced class; 3000 sampled CRT residues per "
                  f"configuration recombine to all three levels, survive "
                  f"every wheel prime IN X SPACE (x = r + unit*t) and lie in "
                  f"the class every forced prime pins x to; "
                  f"W1, W2 under 2^32 and W1*W2 under 2^63")


def g14_engine_mechanisms():
    """The generation tables, the derived compaction depths, the CRT-combined
    group tables, and the queue-overflow fallback -- each against its own
    definition, at the production configurations G9 cannot reach."""
    rng = np.random.default_rng(20260904)
    layouts = set()
    nwin = nderived = nquad = 0
    cases = ((FA, 13, 23, 37, None, 65536, 1),
             (FA, 14, 23, 37, 47, 65536, 1),
             (FB, 11, 23, 37, 47, 65536, 1),
             (FA, 13, 23, 31, None, 4096, 1),
             # the unit wheels the campaigns run (class 3 mod 6)
             (FA, 13, 19, 31, 43, 131072, 6),
             (FA, 14, 19, 31, 43, 32768, 6),
             (FB, 10, 19, 31, 43, 131072, 6),
             (FB, 11, 23, 37, 47, 131072, 6),
             (FA, 12, 23, 37, 47, 32768, 6),
             (FB, 9, 19, 29, 41, 65536, 6))
    # the first case once more on the PLAIN window table: the dispatch takes
    # the pairs table wherever it fits, which is every case here
    for ci, (fam, n, p1, p2, p3, q2, unit) in enumerate(cases + cases[:1]):
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

        eng = GpuEngine(n, fam, p1=p1, p2=p2, p3=p3, q2=q2, unit=unit,
                        lds64=False if ci == len(cases) else None)
        primes = eng.primes
        if any(unit % q == 0 for q in primes):
            return False, (f"G14 FAIL: {fam} n={n} unit {unit}: a prime of "
                           f"the unit is in the sieve")
        for name, depth, target in (("LIT", eng.lit, eng.lit_target),
                                    ("K2", eng.k2, eng.k2_target)):
            if depth > len(primes):
                return False, f"G14 FAIL: {fam} n={n}: {name} past the sieve"
            capped = ((name == "K2"
                       and depth == eng.lit + K2_ROUND_PRIMES_MAX)
                      or (name == "LIT" and depth == LIT_MAX))
            if eng.surv[depth] > target and depth < len(primes) and not capped:
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
                        f"__umul64hi(offp, {(1 << 64) // Q}ULL)" not in src:
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
        pat = eng.cp.asnumpy(eng.d_pat).astype(np.uint64)
        x0 = eng.x0_table()
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
                        # read as the KERNEL reads it: the plan's words
                        bit = (int(eng.window_words(pat, gi, r)[j >> 5])
                               >> (j & 31)) & 1
                        want = 1 if (kp % q) in kill[q] else 0
                        if bit != want:
                            return False, (f"G14 FAIL: {fam} n={n} unit {unit}: the "
                                           f"window bit for q={q} at (t,s,u,j)="
                                           f"({t},{sx},{u},{j}), base period "
                                           f"{j0 + sg * PB}, says {bit} but "
                                           f"x'={kp} mod {q} = {kp % q} is "
                                           f"{'killed' if want else 'kept'}")
                        nchk += 1
        if nchk < 1000:
            return False, "G14 FAIL: too few window bits checked -- vacuous"
        layouts.add(eng.lds64)
        # THE WINDOW'S WORDS AS THE KERNEL FORMS THEM (v3): at EVERY position
        # r in [0, 2Q) of every group, the words the plan reads from the
        # device table and the words it derives from those (a prime up to 96
        # repeats inside the window; its table may hold quads) are the plain
        # pattern's bits r .. r + 32 NW - 1.  The plain pattern is the host
        # table the chain above just checked against killed_residues.
        plain = eng._pat.astype(np.uint64)
        m32 = np.uint64(0xFFFFFFFF)
        for gi, Q in enumerate(eng.gmods):
            _nl, steps = window_plan(Q, eng.nw, eng.periodic)
            nderived += sum(1 for st in steps if st[0] == "rep")
            nquad += 1 if gi in eng._quad else 0
            po = eng.pat_offs[gi]
            rr = np.arange(2 * Q, dtype=np.int64)
            ww = rr >> 5
            ss = (rr & 31).astype(np.uint64)
            got_w = eng.window_words(pat, gi, rr)
            for i in range(eng.nw):
                want_w = ((plain[po + ww + i] >> ss)
                          | (plain[po + ww + i + 1] << (np.uint64(32) - ss))
                          ) & m32
                if not np.array_equal(got_w[i], want_w):
                    bad = int(np.flatnonzero(got_w[i] != want_w)[0])
                    return False, (f"G14 FAIL: {fam} n={n}: word {i} of the "
                                   f"window of group {gi} (modulus {Q}) as "
                                   f"the kernel forms it differs from the "
                                   f"plain pattern at position {bad}")
            nwin += 2 * Q
    # the window chain above was read through BOTH table layouts: the pairs
    # table (every campaign configuration) and the plain one (the shallow
    # x-space wheels, whose tables would not fit doubled)
    if WINDOW_LDS64 and layouts != {True, False}:
        return False, (f"G14 FAIL: the window chain was checked only on the "
                       f"{'pairs' if True in layouts else 'plain'} table "
                       f"layout; the dispatch leaves the other unchecked")
    if (WINDOW_PERIODIC and not nderived) or (WINDOW_QUAD and not nquad):
        return False, (f"G14 FAIL: no configuration here derives a window "
                       f"word ({nderived}) or reads a quad table ({nquad}) -- "
                       f"the periodic window is unchecked")

    # The queues are sized from the survival rate rather than the worst
    # case, so overflow is POSSIBLE -- and the whole design rests on it
    # being harmless.  FORCED: an engine whose queues hold 32 entries
    # against a block that owns thousands takes the fallback for nearly
    # every candidate, and its stream must be identical.
    ref = GpuEngine(13, FA, p1=13, p2=23, p3=None, q2=128)
    tiny = GpuEngine(13, FA, p1=13, p2=23, p3=None, q2=128,
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

    prod = GpuEngine(14, FA, unit=6)
    if not 0 < prod.q1cap <= prod.tile or not 0 < prod.q2cap <= prod.tile:
        return False, (f"G14 FAIL: production queue capacities "
                       f"({prod.q1cap}, {prod.q2cap}) are not within "
                       f"(0, tile = {prod.tile}]")
    if prod.d_pat.nbytes > PAT_BYTES_MAX:
        return False, (f"G14 FAIL: the production window tables are "
                       f"{prod.d_pat.nbytes} bytes, over PAT_BYTES_MAX")
    return True, (f"G14 ok: the split A/C/D generation tables reproduce the "
                  f"one-table CRT on 20000 sampled triples at ten "
                  f"configurations including x-space (23,37,47] and class-"
                  f"space (3 mod 6) wheels at n = 9 to 14; the compaction "
                  f"depths derive from the survival curve ({FA} n = 14: "
                  f"window sieve to prime index {prod.lit}, in-block rounds "
                  f"to {prod.k2}); the window groups and the round groups "
                  f"cover their prime ranges exactly once in order, every "
                  f"round table agrees with killed_residues on EVERY residue "
                  f"of its modulus, and the WINDOW CHAIN -- the x0 table, "
                  f"the per-block ne, the borrow and the pattern word -- "
                  f"says killed exactly when the value is, on 240 sampled "
                  f"(t, s, u, period) candidates per configuration at two "
                  f"launch bases (one above 2^64); the window's words as "
                  f"the kernel forms them -- {nderived} of them DERIVED from "
                  f"the words read, {nquad} groups on quad tables -- equal "
                  f"the plain pattern at all {nwin:,} positions of every "
                  f"group; production queues hold "
                  f"{prod.q1cap} and {prod.q2cap} of a {prod.tile}-candidate "
                  f"block, its window tables {prod.d_pat.nbytes} bytes; and "
                  f"with the queues forced to 32 the survivor stream is "
                  f"IDENTICAL ({len(a)} survivors)")


def g15_k_off_representation():
    """The (x, off) split: the base is folded, not carried, and folding is
    exact.

      1. BASE-SHIFT INVARIANCE: the same absolute window sieved with the
         launch batching forced to different sizes must return the
         identical stream.
      2. The doubled bitmap is periodic with period q, per prime.
      3. The folded values are the residues they claim to be, for primes
         and CRT groups, at bases up to 1e30 -- including above 2^64.
    """
    # the same window under two launch decompositions -- 224-period
    # segments batched into launches against 32-period segments cut into
    # first-level chunks of one block -- and split at a period that is not
    # a segment boundary, so the partial-segment mask is exercised
    # the segment-batched narrow engine, a wide engine of one-block
    # launches, and a narrow one of one-block launches: one stream
    eng = GpuEngine(13, FA, p1=13, p2=23, p3=None, q2=512)
    engb = GpuEngine(13, FA, p1=13, p2=23, p3=None, q2=512, pb=32,
                     tchunk=TPB_DEFAULT, nu=1, wide=True)
    engn = GpuEngine(13, FA, p1=13, p2=23, p3=None, q2=512, pb=32,
                     tchunk=TPB_DEFAULT, nu=1, wide=False)
    if eng.wide or not engb.wide or engn.wide:
        return False, "G15 FAIL: the record modes are not what was asked"
    j0 = eng.j_of(10 ** 12)
    one = eng.survivors_j(j0, j0 + 600)
    many = engb.survivors_j(j0, j0 + 600)
    parts = (engb.survivors_j(j0, j0 + 250)
             + engn.survivors_j(j0 + 250, j0 + 600))
    if not one:
        return False, "G15 FAIL: the base-shift window is empty -- vacuous"
    if one != many or one != sorted(parts):
        return False, (f"G15 FAIL: the stream depends on the launch base: "
                       f"{len(one)} survivors in {eng.seg_periods}-period "
                       f"segments vs {len(many)} in {engb.seg_periods}-period "
                       f"segments of {engb.launches_per_segment} launches, "
                       f"{len(parts)} split at a non-segment period -- the "
                       f"fold is not base-invariant")
    # and in CLASS space, where the base the device folds is in t and the
    # survivors come back as x = 3 + 6t: same invariance, and every
    # survivor in the forced class
    engu = GpuEngine(13, FA, p1=19, p2=23, p3=None, q2=512, unit=6)
    engub = GpuEngine(13, FA, p1=19, p2=23, p3=None, q2=512, unit=6,
                      pb=32, tchunk=TPB_DEFAULT, nu=1)
    ju = engu.j_of(10 ** 12)
    oneu = engu.survivors_j(ju, ju + 600)
    manyu = engub.survivors_j(ju, ju + 600)
    partsu = (engub.survivors_j(ju, ju + 250)
              + engub.survivors_j(ju + 250, ju + 600))
    if not oneu:
        return False, "G15 FAIL: the unit base-shift window is empty -- vacuous"
    if oneu != manyu or oneu != sorted(partsu):
        return False, (f"G15 FAIL: with unit 6 the stream depends on the "
                       f"launch base: {len(oneu)} vs {len(manyu)} vs "
                       f"{len(partsu)} split")
    if engu.r0 != 3 or any(k % 6 != engu.r0 for k in oneu):
        return False, ("G15 FAIL: a class-space survivor is not in the forced "
                       "class 3 (mod 6)")
    presu = engu.cp.asnumpy(engu.d_pres).reshape(len(engu.primes), engu.nres)
    for i in np.random.default_rng(5).integers(0, len(engu.primes), 20).tolist():
        q = engu.primes[i]
        kr = killed_residues(q, 13, FA, 6)
        if sorted(presu[i][:len(kr)].tolist()) != kr:
            return False, (f"G15 FAIL: with unit 6, prime {q}'s residue "
                           f"list is not the unit-space killed set")

    pres = eng.cp.asnumpy(eng.d_pres).reshape(len(eng.primes), eng.nres)
    pmask = eng.cp.asnumpy(eng.d_pmask).reshape(len(eng.primes),
                                                 eng.mask_words)
    rng = np.random.default_rng(4)
    for i in rng.integers(0, len(eng.primes), 40).tolist():
        q = eng.primes[i]
        kr = killed_residues(q, 13, FA)
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

    seg_one = eng.seg_periods
    eng = engb                     # the wide engine carries the tables
    for base in (0, eng.W, 10 ** 12, 2 ** 64 + 12345,
                 k_ceil(13, FA) - eng.W, 10 ** 29):
        base -= base % eng.W
        eng._launch_base(base)
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
        # THE PERIOD TABLES (v3, wide record): every entry the device built
        # for this launch must be (j*W' + base) mod modulus, per tail prime
        # and per round group -- the base above 2^64 and at 1e30 included,
        # so the fold is a Python int on the host and a u32 on the device
        if not eng.wide:
            raise AssertionError("G15's fold engine must use the wide record")
        jb = eng.cp.asnumpy(eng.d_jb).reshape(len(eng.primes), eng.pv)
        jb2 = eng.cp.asnumpy(eng.d_jb2).reshape(len(eng._g2q), eng.pv)
        for i in rng.integers(0, len(eng.primes), 25).tolist():
            q = eng.primes[i]
            for j in (0, 1, eng.pv - 1, int(rng.integers(0, eng.pv))):
                if int(jb[i, j]) != (j * eng.Wp + base) % q:
                    return False, (f"G15 FAIL: at base {base:.4g} the period "
                                   f"table for prime {q}, period {j}, is "
                                   f"{int(jb[i, j])}, not (j W' + base) mod q")
        for gi, Q in enumerate(eng._g2q.tolist()):
            for j in (0, eng.pv - 1, int(rng.integers(0, eng.pv))):
                if int(jb2[gi, j]) != (j * eng.Wp + base) % Q:
                    return False, (f"G15 FAIL: at base {base:.4g} the period "
                                   f"table for round group {gi} (modulus {Q}), "
                                   f"period {j}, is {int(jb2[gi, j])}")
        # and a round group's table still answers for every residue of
        # its modulus (the doubled copy is what absorbs table + r < 2Q)
        tab = eng.cp.asnumpy(eng.d_g2bits)
        for gi, (kind, Q, payload) in enumerate(eng.gdesc2):
            if kind != "table":
                continue
            for r in range(Q):
                for j in (0, eng.pv - 1):
                    b = int(payload) + int(jb2[gi, j]) + r
                    hit = bool((tab[b >> 5] >> (b & 31)) & 1)
                    if hit != _tab_bit(tab, payload, (r + j * eng.Wp + base) % Q):
                        return False, (f"G15 FAIL: group {gi} (modulus {Q}) "
                                       f"at base {base:.4g}, r={r}, j={j}: "
                                       f"the doubled table does not answer "
                                       f"for (offp + j W' + base) mod Q")
    return True, (f"G15 ok: the survivor stream is INVARIANT under the launch "
                  f"decomposition ({len(one)} survivors over 600 periods in "
                  f"{seg_one}-period segments, in 32-period segments "
                  f"of one-block launches, and split at a period inside a "
                  f"segment; and {len(oneu)} in class space, every one in "
                  f"the forced class 3 (mod 6), with the residue lists the class-space "
                  f"killed sets); the tail's residue lists and {MASK_BITS}-bit "
                  f"masks are exactly killed_residues (mod MASK_BITS) on 40 "
                  f"sampled primes, exact below MASK_BITS; and every "
                  f"per-prime fold is exactly base mod q and every period "
                  f"table entry exactly (j W' + base) mod modulus, per tail "
                  f"prime and per round group, at six bases up to the 1e30 "
                  f"ceiling -- so "
                  f"nothing on the device is bounded by x")


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
    n, fam, p1, p2, p3, q2 = 13, FA, 13, 17, 19, 512
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
    this pins a full-size unit wheel against three others over the SAME
    absolute window.  Four wheels enumerating the same candidates by
    different arithmetic must return the identical survivor stream.
    Coverage is what a fingerprint cannot see, so this is the gate the
    production wheel's claim stands on.

    THE WINDOW IS ONE PERIOD of the wheel to 41 at unit 6 -- 3.0e14 of x
    and about 4e10 candidates.  (clique-ladders used the wheel to 43; here a
    small prime keeps about half its classes rather than a third -- product
    forms kill at most (q + 1)/2, plus2_reference G2d -- so that period is
    1.6e12 candidates, and an engine asked for one period of a 32-period
    segment sweeps the whole segment: minutes a family.)

    The four wheels, all over the same window:
      * the wheel (..19],(19,31],(31,41] at unit 6;
      * the SAME prime set split differently, (..23],(23,31],(31,41] -- so a
        CRT-lift bug that depends on where the levels break shows up;
      * a COARSER wheel, (..17],(17,29],(29,37], whose period is 41x
        shorter, so it covers the window in 41 periods and sieves 41 in its
        TAIL instead of its wheel -- the one that proves the wheel/sieve
        boundary is not load-bearing;
      * an X-SPACE wheel (unit = 1) over primes to 41, whose period is the
        same 3.0e14 because the unit's primes are in it instead.
    """
    out = []
    for n, fam in ((13, FA), (11, FB)):
        unit = forced_unit(n, fam)
        # pb = 32, not the production width, and only so the gate FITS: the
        # window is one period, a segment is `pb` periods, and an engine
        # asked for one period of a 224-period segment does a full segment's
        # launches for 1/224 of the work.  The stream does not depend on pb
        # (G15 proves invariance under the launch decomposition), and the
        # production width is exercised by G9 and G18, which use the default.
        kw = dict(q2=Q2_DEFAULT, pb=32)
        prod = GpuEngine(n, fam, p1=19, p2=31, p3=41, unit=unit, **kw)
        alt = GpuEngine(n, fam, p1=23, p2=31, p3=41, unit=unit, **kw)
        coarse = GpuEngine(n, fam, p1=17, p2=29, p3=37, unit=unit, **kw)
        xsp = GpuEngine(n, fam, p1=23, p2=37, p3=41, unit=1, **kw)
        j = 500
        lo, hi = j * prod.W, (j + 1) * prod.W
        if xsp.W != prod.W:
            return False, (f"G17 FAIL: the x-space wheel's period {xsp.W} is "
                           f"not the unit wheel's {prod.W}, so the window is "
                           f"not one period of both")
        a = prod.survivors_j(j, j + 1)
        if not a:
            return False, f"G17 FAIL: {fam} n={n} period {j} is empty -- vacuous"
        for name, eng in (("the same primes split (..23],(23,31],(31,41]", alt),
                          ("the coarser (..17],(17,29],(29,37]", coarse),
                          ("an x-space wheel over primes to 41", xsp)):
            got = eng.survivors_k(lo, hi)
            if got != a:
                sa, sg = set(a), set(got)
                return False, (f"G17 FAIL: {fam} n={n} over [{lo:.4g}, "
                               f"{hi:.4g}) the production wheel keeps "
                               f"{len(a)} survivors and {name} {len(got)}: "
                               f"diff {sorted(sa ^ sg)[:4]}")
        if prod.r0 != 3 or any(k % unit != prod.r0 for k in a):
            return False, (f"G17 FAIL: {fam} n={n}: a survivor is not in the "
                           f"forced class 3 (mod {unit})")
        # and a sample of them passes the CPU engine's own one-at-a-time test
        cpu = CpuEngine(n, fam, q2=Q2_DEFAULT)
        step = max(1, len(a) // 200)
        if not all(cpu.survives(k) for k in a[::step]):
            return False, (f"G17 FAIL: {fam} n={n}: a survivor fails the CPU "
                           f"engine's x-space test")
        out.append(f"{fam} n={n} unit {unit}: {len(a)} survivors over one "
                   f"period ({prod.W:.3g} of x)")
    return True, ("G17 ok: four wheels, four arithmetics, one stream -- the "
                  "class-space wheel to 41, the same prime set split at a "
                  "different level, a coarser wheel covering the window in 41 "
                  "of its own periods (so 41 moves from the wheel into the "
                  "sieve), and an x-space wheel of the same period, all "
                  "return the IDENTICAL survivors over one period at "
                  + "; ".join(out) + " -- every survivor in the forced class 3 "
                  "(mod 6), and "
                  "a 200-point sample passes the CPU engine's one-at-a-time "
                  "test")


def g18_every_opening_compiles_to_occupancy():
    """Every campaign opening -- each family's open index, the one filter a
    campaign can open at, and the filter a RESUMED campaign runs -- compiles
    to the occupancy the engine was tuned at, with the carveout pinned and
    the prefix tables inside their cap; and the two filters below it, which
    only the rediscovery drills run, compile without spills or oversized
    tables and have their occupancy REPORTED.

    Why the drill filters are held to less: a filter with fewer conditions
    needs more window primes to reach BIT_SURV, and the literal code for
    them costs registers (product-cliques' A219761 n = 10 compiled to 122
    registers and 4 blocks per SM).  No campaign runs those filters (their
    prefix is published; a campaign opens at its family's open index and
    only climbs), so what they cost is seconds of a drill, not a night of a
    hunt.  Filters above the opening do not exist until a term
    lands, so they are compiled at runtime by the promotion; the log records
    the occupancy each promotion compiled to.

    A kernel is not a configuration until it has compiled: the register
    allocation of this body varies 50 to 117 between near-identical
    configurations, and 5 blocks per SM instead of 9 is 0.8x with every
    fingerprint green.  This is the 5g check for a cost no fingerprint
    can see.
    """
    import cupy as cp
    rows = []
    for fam in FAMILIES:
        n0 = frontier(fam) + 1
        # THE ONE FILTER THIS CAMPAIGN CAN OPEN AT -- the form list of any
        # later index does not exist until the term before it does -- and
        # the two before it, which are the rediscovery filters the canary
        # runs; each built the way the campaign builds it, with NO wheel
        # named, so what compiles here is exactly what runs.  (frontier()
        # counts this project's FOUND terms, so a resumed campaign's open
        # filter is the one compiled.)
        ns = [n0 - 2, n0 - 1, n0]
        for n in ns:
            unit = forced_unit(n, fam)
            eng = GpuEngine(n, fam, unit=unit)
            c = eng.config()
            if n == n0 and c["blocks_per_sm"] < OCC_MIN_BLOCKS4:
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
            # the planner prices a wheel by the window depth it implies; that
            # number has to be the engine's own, or the plan is priced on a
            # kernel that does not run
            want = window_depth(n, fam, unit, eng.wheel_set)
            if want != eng.lit:
                return False, (f"G18 FAIL: {fam} n={n}: the planner prices a "
                               f"window of {want} primes and the engine "
                               f"builds {eng.lit}")
            rows.append(f"{fam} n={n}{' (open)' if n == n0 else ' (drill)'}: "
                        f"{c['num_regs']} regs, "
                        f"{c['smem_bytes'] >> 10} KB, "
                        f"{c['blocks_per_sm']} blocks/SM, "
                        f"{len(c['groups'])} window groups, "
                        f"unit {unit}, wheel ({eng.p1},{eng.p2},{eng.p3}), "
                        f"q2 {eng.q2}, pb {eng.pb}")
    return True, (f"G18 ok: each family's open index -- the one filter a "
                  f"campaign can open at, PLANNED the way the campaign plans "
                  f"it -- compiles to >= {OCC_MIN_BLOCKS4} blocks per SM, and "
                  f"it and the two drill filters below it compile with no "
                  f"spills, the carveout pinned at {CARVEOUT_PCT}% and the "
                  f"window tables under {PAT_BYTES_MAX >> 10} KB: "
                  + "; ".join(rows))


def g19_reduction_bound_is_the_word():
    """REDUCE_MAX = 2^64: one conditional subtraction after the u64 Barrett
    step is exact for EVERY u64 offset, the bound is real (not slack), and
    the stream is identical across window widths on the full wheel where
    offsets pass 2^63.

      1. Host emulation, bit for bit as the device computes it (the u32
         wrapping subtraction of TEST), at every 97th prime of the ladder
         plus its ends, on the edge offsets 2^63 - 1, 2^63, 2^64 - q,
         2^64 - 1 and 64 random offsets in [2^63, 2^64) each, with and
         without the base fold.
      2. THE TRIPWIRE: at 2^64 + x the same computation is WRONG.  A bound
         that nothing trips is a bound nobody has tested (INNOVATION.md 1.2).
      3. Device: the full wheel to 47 at n = 14, the first launch (a
         t-chunk of one block, u = 0) over the SAME 256 absolute periods
         swept at pb = 64 (four segments) and at pb = 256 (one segment):
         identical, non-empty, and the segment's line provably passes
         2^64 (256 W' > 2^64) -- which the v3 record (offp, jj) carries
         and a u64 offset could not.
      4. The bound the record leaves is on the PERIOD: W' + q2 < 2^64, and
         an engine whose period breaks it is refused.
    """
    rng = np.random.default_rng(19)
    qs = [int(q) for q in primerange(5, Q2_LADDER[-1] + 1)]
    qs = qs[::97] + [qs[0], qs[-1], 65521, 1048573]
    M64 = (1 << 64) - 1
    M32 = 0xFFFFFFFF

    def device(off, q, mg):
        """TEST's arithmetic on a wrapped u64 `off`: exact iff off < 2^64."""
        w = off & M64
        hi = (w * mg) >> 64
        r = ((w & M32) - ((hi & M32) * q & M32)) & M32
        return r - q if r >= q else r
    bad = 0
    for q in qs:
        mg = (1 << 64) // q
        ew = int(rng.integers(0, q))
        offs = ([(1 << 63) - 1, 1 << 63, (1 << 64) - q, (1 << 64) - 1]
                + [int(v) for v in rng.integers(1 << 63, 1 << 64, size=64,
                                                dtype=np.uint64,
                                                endpoint=False)])
        for off in offs:
            r = device(off, q, mg)
            r2 = r + ew
            if r2 >= q:
                r2 -= q
            if r != off % q or r2 != (off + ew) % q:
                bad += 1
    if bad:
        return False, (f"G19 FAIL: the emulated one-subtraction Barrett "
                       f"reduction is wrong on {bad} offsets below 2^64")
    q, mg = 65521, (1 << 64) // 65521
    off = (1 << 64) + 12345
    if device(off, q, mg) == off % q:
        return False, ("G19 FAIL: the emulated reduction is RIGHT at 2^64 + x "
                       "-- the tripwire did not trip, so the bound is untested")
    tripped = device(off, q, mg)
    # 3. device parity across widths where offsets pass 2^63
    W47 = ([5, 7, 11, 13, 17, 19, 23, 29], [31, 37, 41], [43, 47])
    sets, pvs = {}, {}
    span = 256
    for pb in (64, 256):
        eng = GpuEngine(14, FA, p1=W47[0], p2=W47[1], p3=W47[2],
                        q2=1024, unit=6, pb=pb, tchunk=TPB_DEFAULT, nu=1,
                        wide=(pb == 256))
        pvs[pb] = eng.pv
        got, j = [], 1
        while j < 1 + span:
            seg = min(eng.seg_periods, 1 + span - j)
            it = eng.sweep(j, j + seg)
            for _, _, sv in it:
                got.extend(sv)
                break                       # the first launch only
            it.close()
            j += seg
        sets[pb] = sorted(got)
    if pvs[256] != 256 or pvs[64] != 64 or 256 * eng.Wp <= (1 << 64):
        return False, (f"G19 FAIL: the full wheel took pv = {pvs[256]} at "
                       f"pb = 256 (expected 256), or 256 periods of W' = "
                       f"{eng.Wp} do not pass 2^64 -- the window does not "
                       f"exercise the split record")
    if not sets[64]:
        return False, "G19 FAIL: the cross-width window is empty -- vacuous"
    if sets[64] != sets[256]:
        a, b = set(sets[64]), set(sets[256])
        return False, (f"G19 FAIL: pb = 64 ({len(a)} survivors) and pb = 256 "
                       f"({len(b)}) disagree over the same 256 periods: diff "
                       f"{sorted(a ^ b)[:4]}")
    # 4. the record's own bound: a period that does not fit it is refused
    class _Fake:
        pass
    try:
        _saved = globals()["REDUCE_MAX"]
        globals()["REDUCE_MAX"] = eng.Wp          # W' + q2 >= this
        try:
            GpuEngine(14, FA, p1=W47[0], p2=W47[1], p3=W47[2],
                      q2=1024, unit=6, pb=64, tchunk=TPB_DEFAULT, nu=1,
                      wide=True)
            return False, ("G19 FAIL: a period past the record's bound was "
                           "not refused")
        except ValueError:
            pass
    finally:
        globals()["REDUCE_MAX"] = _saved
    return True, (f"G19 ok: the u64 Barrett reduction with one conditional "
                  f"subtraction is bit-exact on {len(qs)} primes x 68 offsets "
                  f"in [2^63, 2^64) (edges included, base fold included), "
                  f"WRONG at 2^64 + 12345 mod 65521 ({tripped} for "
                  f"{off % q}: the bound is 2^64 and it is real), the full "
                  f"wheel's first launch over 256 periods is identical "
                  f"with the NARROW record at pb = 64 (four u64 launches) "
                  f"and the WIDE record at pb = 256 (a line of "
                  f"{256 * eng.Wp:.3e} > 2^64, carried as (offset, period)): "
                  f"{len(sets[64])} survivors; and a period past the wide "
                  f"record's own bound (W' + q2 >= 2^64) is refused")


def g20_wide_wheel_matches_narrow_wheel():
    """A NON-CONTIGUOUS level split, on both records, == the CPU engine; and
    the planned wheel to 53 comes up wide and non-contiguous by itself.

    The two things engine v3 added for the wheel to 53 -- the split record
    and a first level that is a subset rather than a prefix -- cannot be
    pinned on the 53-wheel itself (a period is 3.3e19 of line, and a sweep
    of ANY number of periods through a 160-wide window costs a whole
    segment: ten minutes a side; run once by hand on 2026-09-16 against the
    47-wheel and identical, OPTIMIZATION_LOG.md round 3).  So the split is
    pinned where a dense CPU sieve can follow: a small wheel in the shape of
    the 53-wheel's split -- first level a subset, not a prefix -- in unit
    space at n = 11 of A083519, on the narrow record and on the wide record (forced:
    this period admits a u64 window), against the CPU engine over a
    populated window.  The 53-wheel's own tables are pinned by G8, G13 and
    G14 on the planned configuration, and its record by the promotion
    drill through the campaign's own build path.
    """
    n, fam, unit = 11, FB, 6
    NC = ([5, 11, 17, 23], [7, 13], [19])          # a subset first level
    x_lo, span = 10 ** 15, 3 * 10 ** 7
    cpu = CpuEngine(n, fam, q2=32)
    want = [k for c in cpu.survivors(x_lo, x_lo + span) for k in c]
    if not want:
        return False, "G20 FAIL: the CPU window is empty -- vacuous"
    got = {}
    for wide in (False, True):
        eng = GpuEngine(n, fam, p1=NC[0], p2=NC[1], p3=NC[2], q2=32, unit=unit,
                        wide=wide)
        if eng.wide != wide:
            return False, f"G20 FAIL: the record came up {eng.wide}, asked {wide}"
        if sorted(NC[0])[-1] < min(NC[1] + NC[2]) or eng.W1 != 5 * 11 * 17 * 23:
            return False, "G20 FAIL: the split under test is not non-contiguous"
        got[wide] = eng.survivors_k(x_lo, x_lo + span)
        if got[wide] != want:
            a, b = set(got[wide]), set(want)
            return False, (f"G20 FAIL: the non-contiguous split on the "
                           f"{'wide' if wide else 'narrow'} record gives "
                           f"{len(got[wide])} survivors, the CPU engine "
                           f"{len(want)}: diff {sorted(a ^ b)[:4]}")
    # THE ROUNDS IN THE WINDOW'S COORDINATES (ROUND_WINDOW) run on the wide
    # record only, so the wide engine above must be shown to TAKE them, deep
    # enough to have rounds at all (q2 = 32 leaves none): the same split at
    # q2 = 128 with the window cut short by hand, so the primes past it go through
    # three in-block rounds -- four queues, which is what makes the ping-pong
    # buffers alias -- on the narrow record (Barrett rounds), on the wide
    # record (window rounds) and on the wide record with the queues forced
    # full (the overflow path, which must unpack bw from the queue index),
    # each against the CPU engine.
    # q2 = 128, not clique-ladders' 64: a prime here kills at most about half
    # its residues (plus2_reference G2d), so survival halves less often
    # and six primes past the window gave only two rounds (three queues)
    span2 = 3 * 10 ** 8
    cpu2 = CpuEngine(n, fam, q2=128)
    want2 = [k for c in cpu2.survivors(x_lo, x_lo + span2) for k in c]
    if not want2:
        return False, "G20 FAIL: the round drill's CPU window is empty"
    # ENGINE v3: the wide record's rounds are the FOLDED Barrett packs by
    # default (ROUND_FOLD) and the window rounds are the A/B arm, so both are
    # built here, each with its queues sized and forced full, and each
    # against the CPU engine.
    global ROUND_FOLD
    keep_fold = ROUND_FOLD
    kinds = set()
    try:
        for wide, sig, fold in ((False, QCAP_SIGMA, True),
                                (True, QCAP_SIGMA, True), (True, -1e9, True),
                                (True, QCAP_SIGMA, False),
                                (True, -1e9, False)):
            ROUND_FOLD = fold
            eng = GpuEngine(n, fam, p1=NC[0], p2=NC[1], p3=NC[2], q2=128,
                            unit=unit, wide=wide, lit=2, qcap_sigma=sig)
            if (eng.fold != (wide and fold)
                    or eng.rwin != (wide and not fold and ROUND_WINDOW)
                    or len(eng.qcaps) < 4):
                return False, (f"G20 FAIL: the round drill's engine (wide = "
                               f"{wide}, fold asked {fold}) came up with fold "
                               f"= {eng.fold}, rwin = {eng.rwin} and "
                               f"{len(eng.qcaps)} queues -- it would not "
                               f"exercise the rounds it is here for")
            if sig < 0 and max(eng.qcaps) > 32:
                return False, "G20 FAIL: the forced-overflow engine has room"
            kinds.add((wide, eng.fold, eng.rwin, sig < 0))
            got2 = eng.survivors_k(x_lo, x_lo + span2)
            if got2 != want2:
                return False, (f"G20 FAIL: the in-block rounds on the "
                               f"{'wide' if wide else 'narrow'} record (fold "
                               f"= {eng.fold}, rwin = {eng.rwin}, queues "
                               f"{eng.qcaps}) give {len(got2)} survivors, the "
                               f"CPU engine {len(want2)}: diff "
                               f"{sorted(set(got2) ^ set(want2))[:4]}")
    finally:
        ROUND_FOLD = keep_fold
    if len(kinds) != 5:
        return False, f"G20 FAIL: the round drill built {sorted(kinds)}"
    # THE RECORD IS THE ENGINE'S CHOICE, FROM THE PLAN IT IS HANDED: at every
    # family's open index the planned wheel comes up wide exactly when no u64
    # window admits its period, and narrow otherwise.  Which it is depends on
    # the modelled search (`plan`), so it is asserted as a rule and
    # reported, not pinned to one wheel.
    rows = []
    for f in FAMILIES:
        m = frontier(f) + 1
        u = forced_unit(m, f)
        *lv, q2, pb = plan(m, f, u)
        e = GpuEngine(m, f, p1=lv[0], p2=lv[1], p3=lv[2], q2=q2, unit=u,
                      pb=pb, seg_cap=pb)
        # the u64 offset admits `fits` whole periods of this wheel: narrow
        # whenever that is a window worth having (WIDE_MIN_PV) or the whole
        # planned window, clamped to it; wide only when neither
        fits = ((1 << 64) - q2) // e.Wp - 1
        needs = fits < pb and fits < WIDE_MIN_PV
        if e.wide != needs or e.seg_periods != (pb if needs else min(pb, fits)):
            return False, (f"G20 FAIL: {f} n = {m}: the planned wheel {lv} at "
                           f"{pb} periods (W' = {e.Wp:.4g}) came up "
                           f"{'wide' if e.wide else 'narrow'} with "
                           f"{e.seg_periods}-period segments")
        rows.append(f"{f} n={m} unit {u} wheel to {max(_wheel_primes(*lv))} "
                    f"x{pb}: {'wide' if e.wide else 'narrow'}")
    return True, (f"G20 ok: the non-contiguous split {NC} in the class 3 "
                  f"(mod 6), {fam} n = {n}, "
                  f"returns the CPU engine's {len(want)} survivors over "
                  f"[{x_lo:.3g}, +{span:.3g}) on the narrow record AND on the "
                  f"wide record; the in-block rounds return the CPU engine's "
                  f"{len(want2)} at q2 = 128 as Barrett rounds (narrow), as "
                  f"FOLDED Barrett rounds (wide, v3) and as window rounds "
                  f"(wide, the A/B arm), each of the wide kinds also with "
                  f"its queues forced full; and at every open index the planned wheel "
                  f"takes the wide record exactly when no u64 window admits "
                  f"its period -- " + "; ".join(rows))


def g21_lazy_rounds_are_exact():
    """ROUND_LAZY (engine v2): the narrow rounds' uncorrected reductions and
    tripled tables are exact, and the bound they rest on is real.

      1. Host emulation, bit for bit as the device computes it (u32 wrapping
         subtractions), of EVERY pack of every in-block round of the planned
         A083518 opening and of a shallow gate engine whose rounds hold
         inline (q < 64) groups: the pack remainder rm is below 2M and
         congruent to the offset, the per-prime remainder r below 2q and
         congruent, and the ENGINE'S OWN round table read at g2p + r (g2p =
         the table offset plus base mod q, the launch fold) answers
         "killed" exactly when (offset + base) mod q is in killed_residues
         -- on the edge offsets 0, 1, M - 1, M, 2^63 - 1, 2^63, 2^64 - M,
         2^64 - 1 and 48 random u64, at bases 0, a random one and one past
         2^64.  Every pack modulus is under 2^31.
      2. Every table group of the lazy engine holds THREE periods, each
         equal to the kill pattern on every residue.
      3. THE TRIPWIRE: a pack modulus past 2^31 makes the lazy remainder
         overflow the u32 on a constructed offset, and the emulated test
         then reads the wrong residue.  The 2^31 bound is the one the
         builder enforces, and it is not slack (INNOVATION.md 1.2).
      4. Device: the lazy engine and the corrected one return the
         IDENTICAL stream over a populated window with five in-block
         rounds.
      5. ROUND_FOLD (engine v3): the wide record's packs take the numerator
         offp + jj*(W' mod M).  Emulated the same way on a wide engine, for
         within-period offsets up to 2^63 - 1 (the largest a wheel may have)
         and periods up to 255: the numerator stays below 2^64, the
         remainders stay lazy-exact, and the table read at g2p + r answers
         "killed" exactly when (offp + jj*W' + base) mod q is.  THE
         TRIPWIRE: an offset past 2^64 - 255*(W' mod M) wraps the numerator
         and the test reads the wrong residue, so W' < 2^63 is not slack.
      6. TAIL_LITERAL (engine v3): every pack of every generated tail round
         of a narrow and a wide engine, emulated: the lazy pack remainder
         plus the launch base mod M stays inside the u32 (below 3M, M <
         2^30), the per-prime remainder below 2q, and the engine's own
         doubled table answers "killed" exactly when the value is.  THE
         TRIPWIRE: a pack modulus past 2^32 / 3 overflows the sum on a
         constructed offset and base.
      7. Device: folded rounds == window rounds on the wide record, and
         generated tail rounds == generic ones, narrow and wide, with the
         tail queues sized and forced to overflow -- identical streams.
    """
    rng = np.random.default_rng(21)
    M64, M32 = (1 << 64) - 1, 0xFFFFFFFF

    def pack_rm(off, M):
        mg = (1 << 64) // M
        hi = ((off & M64) * mg) >> 64
        return ((off & M32) - ((hi & M32) * M & M32)) & M32

    def prime_r(rm, q):
        return (rm - (((rm * ((1 << 32) // q)) >> 32) * q & M32)) & M32

    checked, engines = 0, []
    p1, p2, p3, q2, pb = plan(14, FA, forced_unit(14, FA))
    engines.append(GpuEngine(14, FA, p1=p1, p2=p2, p3=p3, q2=q2,
                             unit=forced_unit(14, FA), pb=pb, seg_cap=pb))
    # a two-prime window, so round 1 starts below 64 and packs inline groups
    engines.append(GpuEngine(13, FA, p1=13, p2=23, p3=None, q2=4096, lit=2))
    saw_inline = False
    for eng in engines:
        if not eng.lazy:
            return False, (f"G21 FAIL: the {eng.fam} n={eng.n} engine is not "
                           f"lazy -- the gate would test the corrected path")
        tab = eng.cp.asnumpy(eng.d_g2bits).astype(np.int64)
        qs = eng._g2q_list()
        g0 = 0
        for rnd in eng.rounds2:
            g1 = g0 + len(rnd)
            for pack, M in eng.round_packs(g0, g1):
                if M >= 1 << 31:
                    return False, (f"G21 FAIL: a pack modulus {M} is not "
                                   f"under 2^31")
                inline = any(eng.gdesc2[gi][0] == "inline" for gi in pack)
                saw_inline |= inline
                offs = ([0, 1, M - 1, M, (1 << 63) - 1, 1 << 63,
                         (1 << 64) - M, (1 << 64) - 1]
                        + [int(v) for v in rng.integers(0, 1 << 64, size=48,
                                                        dtype=np.uint64)])
                for off in offs:
                    rm = pack_rm(off, M)
                    if not inline:
                        if rm >= 2 * M or rm % M != off % M:
                            return False, (f"G21 FAIL: lazy pack remainder "
                                           f"{rm} for offset {off} mod {M}")
                    for gi in pack:
                        q = qs[gi]
                        kind, Q, payload = eng.gdesc2[gi]
                        r = rm if len(pack) == 1 else prime_r(rm, q)
                        if inline:
                            continue        # the corrected path, as before
                        if r >= 2 * q or r % q != off % q:
                            return False, (f"G21 FAIL: lazy remainder {r} "
                                           f"for offset {off} mod {q}")
                        kill = set(killed_residues(q, eng.n, eng.fam,
                                                   eng.unit))
                        for base in (0, int(rng.integers(0, 1 << 62)),
                                     (1 << 64) + int(rng.integers(0, 1 << 40))):
                            b = int(payload) + base % q + r
                            got = (int(tab[b >> 5]) >> (b & 31)) & 1
                            want = 1 if (off + base) % q in kill else 0
                            if got != want:
                                return False, (
                                    f"G21 FAIL: {eng.fam} n={eng.n}: the lazy "
                                    f"test of q={q} at offset {off}, base "
                                    f"{base} reads {got}, the definition "
                                    f"says {want}")
                            checked += 1
            g0 = g1
        # 2. three periods per table group
        for gi, (kind, Q, payload) in enumerate(eng.gdesc2):
            if kind != "table":
                continue
            kill = set(killed_residues(Q, eng.n, eng.fam, eng.unit))
            b = int(payload) + np.arange(3 * Q)
            got = (tab[b >> 5] >> (b & 31)) & 1
            want = np.array([1 if (u % Q) in kill else 0
                             for u in range(3 * Q)])
            if not np.array_equal(got, want):
                return False, (f"G21 FAIL: round table of {Q} does not hold "
                               f"three periods of its kill pattern")
    if checked < 10000:
        return False, f"G21 FAIL: only {checked} lazy tests emulated -- vacuous"
    if not saw_inline:
        return False, ("G21 FAIL: no pack with an inline group was "
                       "emulated -- the mixed pack is unchecked")
    # 3. the tripwire: three consecutive primes whose product passes 2^31
    trip = None
    trio = [q for q in primerange(1291, 2000)]
    for k in range(len(trio) - 2):
        qa, qb, qc = trio[k:k + 3]
        M = qa * qb * qc
        if not (1 << 31) <= M < (1 << 32):
            continue
        rho = (1 << 64) % M
        bmin = (1 << 32) - M
        for b in (bmin, bmin + 1, bmin + 7):
            off = (((1 << 64) - 1 - b) // M) * M + b
            if b < (off * rho) >> 64:
                rm = pack_rm(off, M)
                if any(prime_r(rm, q) % q != off % q for q in (qa, qb, qc)):
                    trip = (M, off)
                    break
        if trip:
            break
    if trip is None:
        return False, ("G21 FAIL: no pack modulus past 2^31 broke the lazy "
                       "chain -- the tripwire did not trip, so the bound is "
                       "untested")
    # 4. device: lazy and corrected rounds, the same stream
    global ROUND_LAZY
    keep = ROUND_LAZY
    streams = {}
    try:
        for lz in (True, False):
            ROUND_LAZY = lz
            eng = GpuEngine(13, FA, p1=13, p2=23, p3=None, q2=4096)
            streams[lz] = (eng.lazy, len(eng.rounds2),
                           eng.survivors_k(10 ** 12, 10 ** 12 + 4 * 10 ** 9))
    finally:
        ROUND_LAZY = keep
    if not streams[True][0] or streams[False][0]:
        return False, "G21 FAIL: the device A/B did not toggle the lazy path"
    if streams[True][1] < 2 or not streams[True][2]:
        return False, (f"G21 FAIL: the device window has {streams[True][1]} "
                       f"rounds and {len(streams[True][2])} survivors -- "
                       f"vacuous")
    if streams[True][2] != streams[False][2]:
        return False, (f"G21 FAIL: lazy rounds {len(streams[True][2])} "
                       f"survivors, corrected {len(streams[False][2])}")
    # 5. the wide record's folded packs (ROUND_FOLD), emulated
    global ROUND_FOLD, TAIL_LITERAL, TAIL_LITERAL_ITEMS, TAIL_FILL
    keep_fold, keep_tl = ROUND_FOLD, TAIL_LITERAL
    keep_items, keep_fill = TAIL_LITERAL_ITEMS, TAIL_FILL
    WIDE_SPLIT = dict(p1=[5, 11, 17, 23], p2=[7, 13], p3=[19], q2=4096,
                      unit=6, wide=True)
    folded = fold_trip = 0
    # SIX ENGINES serve items 5 to 7: a narrow and a wide one built so that
    # their first tail rounds ARE generated (a gate window's queues are far
    # under the campaign's thresholds, so the thresholds are zeroed), the
    # same two with every queue forced full, and the same two on the A/B
    # arms -- generic tail rounds, and window rounds on the wide record.
    NARROW = dict(p1=13, p2=23, p3=None, q2=4096)
    try:
        ROUND_FOLD, TAIL_LITERAL = True, 16
        TAIL_LITERAL_ITEMS, TAIL_FILL = 0, 0
        ta = GpuEngine(13, FA, **NARROW)
        weng = GpuEngine(11, FB, **WIDE_SPLIT)
        ta_full = GpuEngine(13, FA, qcap_sigma=-1e9, **NARROW)
        w_full = GpuEngine(11, FB, qcap_sigma=-1e9, **WIDE_SPLIT)
        ROUND_FOLD, TAIL_LITERAL = False, 0
        ta0 = GpuEngine(13, FA, **NARROW)
        w0 = GpuEngine(11, FB, **WIDE_SPLIT)
    finally:
        ROUND_FOLD, TAIL_LITERAL = keep_fold, keep_tl
        TAIL_LITERAL_ITEMS, TAIL_FILL = keep_items, keep_fill
    if not (weng.fold and weng.lazy and weng.wide) or weng.rwin:
        return False, "G21 FAIL: the wide engine did not take the folded rounds"
    wtab = weng.cp.asnumpy(weng.d_g2bits).astype(np.int64)
    wqs = weng._g2q_list()
    Wp = int(weng.Wp)
    g0 = 0
    for rnd in weng.rounds2:
        g1 = g0 + len(rnd)
        for pack, M in weng.round_packs(g0, g1):
            if any(weng.gdesc2[gi][0] == "inline" for gi in pack):
                continue
            wM = Wp % M
            for offp in ([0, 1, Wp - 1, (1 << 63) - 1]
                         + [int(v) for v in rng.integers(0, 1 << 63, size=12)]):
                for jj in (0, 1, weng.pv - 1, 255):
                    xp = offp + jj * wM
                    true = offp + jj * Wp
                    if xp >= 1 << 64:
                        return False, (f"G21 FAIL: the folded numerator "
                                       f"passes 2^64 at offp = {offp}")
                    rm = pack_rm(xp, M)
                    if rm >= 2 * M or rm % M != true % M:
                        return False, (f"G21 FAIL: folded pack remainder {rm} "
                                       f"for ({offp}, {jj}) mod {M}")
                    for gi in pack:
                        q = wqs[gi]
                        _kind, _Q, payload = weng.gdesc2[gi]
                        r = rm if len(pack) == 1 else prime_r(rm, q)
                        if r >= 2 * q or r % q != true % q:
                            return False, (f"G21 FAIL: folded remainder {r} "
                                           f"for ({offp}, {jj}) mod {q}")
                        kill = set(killed_residues(q, weng.n, weng.fam,
                                                   weng.unit))
                        for base in (0, (1 << 66) + 12345):
                            b = int(payload) + base % q + r
                            got = (int(wtab[b >> 5]) >> (b & 31)) & 1
                            if got != (1 if (true + base) % q in kill else 0):
                                return False, (
                                    f"G21 FAIL: the folded test of q={q} at "
                                    f"(offp, jj) = ({offp}, {jj}), base "
                                    f"{base} reads {got}")
                            folded += 1
            # the tripwire: a numerator that wraps the word
            if wM and not fold_trip:
                offp = (1 << 64) - 1
                xp = (offp + 255 * wM) & M64
                if pack_rm(xp, M) % M != (offp + 255 * wM) % M:
                    fold_trip = M
        g0 = g1
    if folded < 2000 or not fold_trip:
        return False, (f"G21 FAIL: {folded} folded tests emulated, tripwire "
                       f"{fold_trip} -- the folded packs are unchecked")
    # 6. the generated tail rounds (TAIL_LITERAL), emulated on the narrow and
    # the wide engine
    tails = tl_rounds = 0
    for eng in (ta, weng):
        if not eng.tail_lit:
            return False, (f"G21 FAIL: the {eng.fam} n={eng.n} engine "
                           f"generated no tail round")
        tl_rounds += len(eng.tail_lit)
        g3 = eng.cp.asnumpy(eng.d_g3bits).astype(np.int64)
        Wp = int(eng.Wp)
        for r_ in eng.tail_lit:
            for pack, M in eng.tail_packs(r_):
                if M >= TAIL_PACK_MAX or 3 * M > 1 << 32:
                    return False, f"G21 FAIL: a tail pack modulus {M} is too big"
                wM = Wp % M
                offs = ([0, 1, M - 1, M, (1 << 63) - 1]
                        + [int(v) for v in rng.integers(0, 1 << 63, size=10)])
                if not eng.wide:
                    offs += [(1 << 64) - M, (1 << 64) - 1]
                for offp in offs:
                    for jj in ((0, 1, eng.pv - 1, 255) if eng.wide else (0,)):
                        xp = offp + jj * wM
                        true = offp + jj * Wp
                        for base in (0, M - 1, (1 << 66) + 98765):
                            tot = pack_rm(xp, M) + base % M
                            if tot >= 3 * M or tot > M32:
                                return False, (f"G21 FAIL: tail pack sum "
                                               f"{tot} for modulus {M}")
                            for i in pack:
                                q = eng.primes[i]
                                r = prime_r(tot, q)
                                if r >= 2 * q or r % q != (true + base) % q:
                                    return False, (
                                        f"G21 FAIL: tail remainder {r} for "
                                        f"({offp}, {jj}) + {base} mod {q}")
                                kill = set(killed_residues(q, eng.n, eng.fam,
                                                           eng.unit))
                                b = eng._tl_off[i] + r
                                got = (int(g3[b >> 5]) >> (b & 31)) & 1
                                if got != (1 if (true + base) % q in kill
                                           else 0):
                                    return False, (
                                        f"G21 FAIL: the generated tail test "
                                        f"of q={q} at ({offp}, {jj}), base "
                                        f"{base} reads {got}")
                                tails += 1
    if tails < 5000:
        return False, f"G21 FAIL: only {tails} tail tests emulated -- vacuous"
    # the tripwire: a pack modulus past 2^32 / 3, where the lazy remainder
    # (b + M) plus a base of M - 1 passes the word
    tl_trip = None
    duo = [q for q in primerange(38000, 46300)]
    for k in range(len(duo) - 1):
        M = duo[k] * duo[k + 1]
        if not (1 << 32) // 3 < M < (1 << 31):
            continue
        rho = (1 << 64) % M
        bmin = (1 << 32) - 2 * M + 1
        if not 0 <= bmin < min(rho, M):
            continue
        for b in (bmin, bmin + 1, bmin + 5):
            off = (((1 << 64) - 1 - b) // M) * M + b
            if b < (off * rho) >> 64 and pack_rm(off, M) == b + M:
                tot = (pack_rm(off, M) + (M - 1)) & M32     # as the u32 holds it
                want = (off + M - 1) % duo[k]
                if prime_r(tot, duo[k]) % duo[k] != want:
                    tl_trip = (M, off)
                    break
        if tl_trip:
            break
    if tl_trip is None:
        return False, ("G21 FAIL: no tail pack modulus past 2^32 / 3 broke "
                       "the chain -- the 2^30 bound is untested")
    # 7. device: each new mechanism against its A/B arm, identical streams
    lo_n, sp_n = 10 ** 12, 4 * 10 ** 9
    lo_w, sp_w = 10 ** 15, 4 * 10 ** 9
    if ta0.tail_lit or w0.tail_lit or w0.fold or not w0.rwin or \
            not (ta_full.tail_lit and w_full.tail_lit and w_full.fold) or \
            max(w_full.qcaps) > 32:
        return False, "G21 FAIL: the v3 device A/B did not toggle its arms"
    ref_ = (None, None, None, None, ta.survivors_k(lo_n, lo_n + sp_n),
            weng.survivors_k(lo_w, lo_w + sp_w))
    if not ref_[4] or not ref_[5]:
        return False, "G21 FAIL: a v3 device window is empty -- vacuous"
    for tag_, en, ew in (("the A/B arms (generic tail rounds, window rounds)",
                          ta0, w0),
                         ("every queue forced full", ta_full, w_full)):
        got = (en.survivors_k(lo_n, lo_n + sp_n),
               ew.survivors_k(lo_w, lo_w + sp_w))
        if got != (ref_[4], ref_[5]):
            return False, (f"G21 FAIL: the stream with {tag_} is "
                           f"{len(got[0])}/{len(got[1])} survivors, the v3 "
                           f"engine's {len(ref_[4])}/{len(ref_[5])}")
    return True, (f"G21 ok: {checked:,} lazy round tests emulated bit for bit "
                  f"over every pack of the A083518 opening and of a shallow "
                  f"engine with inline groups (remainders below 2M and 2q, "
                  f"the engine's own tripled tables read at base + r, edges "
                  f"to 2^64 - 1, bases past 2^64), every table three periods "
                  f"of its kill pattern, every pack modulus under 2^31; a "
                  f"modulus of {trip[0]:,} (past 2^31) breaks the chain at "
                  f"offset {trip[1]} (the bound is real); and lazy and "
                  f"corrected rounds return the identical stream on the "
                  f"device ({len(streams[True][2])} survivors through "
                  f"{streams[True][1]} in-block rounds); v3: {folded:,} "
                  f"FOLDED tests of the wide record emulated (offsets to "
                  f"2^63 - 1, periods to 255, the numerator under 2^64, and "
                  f"a wrapped one wrong at pack {fold_trip:,}); {tails:,} "
                  f"GENERATED tail tests over {tl_rounds} rounds of a narrow "
                  f"and a wide engine (pack sum under 3M, the engine's "
                  f"doubled tables; a modulus of {tl_trip[0]:,}, past "
                  f"2^32 / 3, breaks the chain); and on the device folded == "
                  f"window rounds and generated == generic tail rounds, "
                  f"narrow and wide, with the queues sized and forced full "
                  f"({len(ref_[4])} and {len(ref_[5])} survivors)")


def _ne_rows_ok(eng, j0, u0, rng, tag):
    """Build the launch table at period j0 and third-level chunk u0 and
    compare its rows with the definition -- every row of a table up to
    50,000 rows, 4,000 sampled rows plus the first and last of a larger
    one; returns (ok, msg, rows checked)."""
    cp = eng.cp
    eng._launch_base(int(eng.Wp) * int(j0))
    gz = eng.gz_max
    tot = eng.R2 * gz
    eng.k_nebuild((-(-tot // 128),), (128,),
                  (np.int32(eng.R2), np.int32(gz), np.int32(u0),
                   eng.d_res2c, eng.d_res2d, eng.d_jmod, eng.d_jmod2,
                   eng.d_netab))
    cp.cuda.Stream.null.synchronize()
    tab = cp.asnumpy(eng.d_netab[:tot * eng.nrow]).astype(np.int64)
    tab = tab.reshape(tot, eng.nrow)
    rows = (np.arange(tot) if tot <= 50000 else
            np.unique(np.concatenate([[0, tot - 1],
                                      rng.integers(0, tot, 4000)])))
    z, sx = rows // eng.R2, rows % eng.R2
    sg = np.zeros_like(z) if eng.wide else z // eng.nu
    u = u0 + z % eng.nu
    W1, W2 = int(eng.W1), int(eng.W2)
    if eng.R2 > 1:
        c = cp.asnumpy(eng.d_res2c).astype(np.int64)[sx]
        if eng.R3 > 1:
            c = (c + cp.asnumpy(eng.d_res2d).astype(np.int64)[u]) % W2
        D = W2 - c
    else:
        D = np.zeros_like(rows)
    pos = [(gi, Q, dv) for gi, (Q, dv) in enumerate(zip(eng.gmods, eng.dinvs))]
    if eng.rwin:
        pos += [(eng._ng8 + eng.slot2[gi], Q, dv) for gi, (Q, dv)
                in enumerate(zip(eng._g2q_list(), eng._dinvs2))]
    for p_, Q, dv in pos:
        Q, dv = int(Q), int(dv)
        E = ((W1 % Q) * (D % Q) % Q) * dv % Q
        want = (int(j0) % Q + sg * eng.pv - E) % Q
        got = tab[rows, p_]
        if not np.array_equal(got, want):
            k = int(np.flatnonzero(got != want)[0])
            return False, (f"G22 FAIL: {tag}: row {int(rows[k])} position "
                           f"{p_} (modulus {Q}) holds {int(got[k])}, the "
                           f"definition {int(want[k])} at base period {j0}"), 0
    return True, "", int(rows.size)


def g22_offset_table_matches_definition():
    """PRE_TABLE (engine v2): the launch's block-offset table built by
    `nebuild` is, row for row, the definition the in-block prologue
    computed -- ne = (j0 mod Q + sg*PV - E) mod Q, E = ((W1 D) mod Q) Dinv
    mod Q -- for the window groups and the window-coordinate round slots,
    at a base past 2^64 and a small one, on a narrow engine (the planned
    A083518 opening), a wide engine with window-coordinate rounds (a
    non-contiguous split) and a narrow engine that batches several
    segments into one launch (sg > 0); and the device stream is IDENTICAL
    with the table and with the in-block prologue, narrow and wide."""
    rng = np.random.default_rng(22)
    cases = []
    cases.append(("A083518 n=14 planned", GpuEngine(14, FA, unit=6)))
    # the wide record twice: its rounds folded (v3: the rows hold the window
    # groups alone) and in the window's coordinates (the A/B arm: the rows
    # carry a slot per round group)
    global ROUND_FOLD
    keep_fold = ROUND_FOLD
    try:
        ROUND_FOLD = True
        cases.append(("A083519 n=11 wide split, folded rounds",
                      GpuEngine(11, FB, p1=[5, 11, 17, 23], p2=[7, 13],
                                p3=[19], q2=4096, unit=6, wide=True)))
        ROUND_FOLD = False
        cases.append(("A083519 n=11 wide split",
                      GpuEngine(11, FB, p1=[5, 11, 17, 23], p2=[7, 13],
                                p3=[19], q2=4096, unit=6, wide=True)))
    finally:
        ROUND_FOLD = keep_fold
    cases.append(("A083518 n=14 batched",
                  GpuEngine(14, FA, p1=[5, 7, 11, 13, 17], p2=[19, 23],
                            p3=[29], q2=65536, unit=6, pb=64)))
    rows, saw = 0, set()
    for tag, eng in cases:
        if not eng.pre_table:
            return False, (f"G22 FAIL: {tag} does not take the table -- the "
                           f"gate would check nothing")
        if tag.endswith("wide split") and not eng.rwin:
            return False, f"G22 FAIL: {tag} has no window-coordinate rounds"
        if tag.endswith("folded rounds") and (eng.rwin or not eng.fold
                                              or eng.nrow != eng._ng8):
            return False, f"G22 FAIL: {tag} still carries round slots"
        if tag.endswith("batched") and eng.gz_max < 2:
            return False, f"G22 FAIL: {tag} launches one segment -- sg > 0 unchecked"
        saw.add((eng.wide, eng.rwin, eng.gz_max > 1))
        for j0 in (7, (1 << 66) // int(eng.Wp) + 3):
            for u0 in sorted({0, max(0, eng.R3 - eng.nu)}):
                ok, msg, nr = _ne_rows_ok(eng, j0, u0, rng, tag)
                if not ok:
                    return False, msg
                rows += nr
    # the stream, table against prologue
    global PRE_TABLE
    keep = PRE_TABLE
    streams = {}
    try:
        for pt in (True, False):
            PRE_TABLE = pt
            a = GpuEngine(14, FA, p1=[5, 7, 11, 13, 17], p2=[19, 23],
                          p3=[29], q2=4096, unit=6, pb=64)
            b = GpuEngine(11, FB, p1=[5, 11, 17, 23], p2=[7, 13], p3=[19],
                          q2=4096, unit=6, wide=True)
            # ... and, on the prologue arm, the wide record with window
            # rounds, whose prologue also computes the round slots (with
            # the table they are pinned to the CPU engine by G20)
            cs, crw = None, False
            if not pt:
                ROUND_FOLD = False
                try:
                    c = GpuEngine(11, FB, p1=[5, 11, 17, 23], p2=[7, 13],
                                  p3=[19], q2=4096, unit=6, wide=True)
                finally:
                    ROUND_FOLD = keep_fold
                cs = c.survivors_k(10 ** 15, 10 ** 15 + 4 * 10 ** 9)
                crw = c.rwin and not c.pre_table and not b.rwin
            streams[pt] = (a.pre_table, b.pre_table,
                           a.survivors_k(10 ** 13, 10 ** 13 + 2 * 10 ** 11),
                           b.survivors_k(10 ** 15, 10 ** 15 + 4 * 10 ** 9),
                           cs, crw)
    finally:
        PRE_TABLE = keep
    if (streams[True][0], streams[True][1]) != (True, True) or \
            streams[False][0] or streams[False][1]:
        return False, "G22 FAIL: the device A/B did not toggle the table"
    if not streams[False][5]:
        return False, ("G22 FAIL: the wide A/B did not build one engine with "
                       "folded rounds and one with window rounds")
    if not streams[True][2] or not streams[True][3]:
        return False, "G22 FAIL: an A/B window is empty -- vacuous"
    if streams[True][2:4] != streams[False][2:4] or \
            streams[True][3] != streams[False][4]:
        return False, (f"G22 FAIL: table and prologue disagree: "
                       f"{len(streams[True][2])}/{len(streams[True][3])} "
                       f"against {len(streams[False][2])}/"
                       f"{len(streams[False][3])}/{len(streams[False][4])} "
                       f"survivors")
    return True, (f"G22 ok: the launch offset table equals the definition on "
                  f"{rows:,} rows (every window group and every "
                  f"window-coordinate round slot) at bases 7 and past 2^66, "
                  f"on the planned A083518 opening, a wide engine with "
                  f"folded rounds, the same with window-coordinate rounds, "
                  f"and a launch batching several "
                  f"segments; and the device stream is IDENTICAL with the "
                  f"table and with the in-block prologue "
                  f"({len(streams[True][2])} survivors narrow, "
                  f"{len(streams[True][3])} wide, the two kinds of wide "
                  f"round agreeing)")


GATES = [g7_wheel_matches_oracle, g8_wheel_partitions_the_period,
         g13_production_wheel_constants, g14_engine_mechanisms,
         g9_gpu_matches_cpu, g15_k_off_representation,
         g16_third_level_mechanisms, g17_unit_wheel_matches_k_wheel,
         g18_every_opening_compiles_to_occupancy,
         g19_reduction_bound_is_the_word,
         g20_wide_wheel_matches_narrow_wheel,
         g21_lazy_rounds_are_exact,
         g22_offset_table_matches_definition]

# Ctrl+C is a normal exit everywhere in this repo (CONVENTIONS.md
# "Stopping a run"): one path out, no traceback, exit 130.
if __name__ == "__main__":
    def _gates():
        for g in GATES:
            ok, msg = g()
            print(("PASS " if ok else "FAIL ") + msg)
    _sys.exit(_shutdown.graceful(_gates) or 0)
