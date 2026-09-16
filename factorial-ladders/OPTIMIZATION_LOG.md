# OPTIMIZATION_LOG — factorial-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt, its measurement and its verdict — including the rejects and
the things rejected without implementing, with their prices. The process is
[OPTIMIZATION.md](../OPTIMIZATION.md); the rule that matters most here is
its corollary to Rule 1: **a constant tuned before a structural change is
stale after it**, and this project inherited its engine from a problem with
a different wheel, so every constant started stale and is listed below as
either re-measured here or still inherited.

All ratios are medians of three interleaved rounds, paired (OPTIMIZATION.md
Rule 3), at the configuration named. Absolute rates move ~30% with ambient
load; the ratio is the stable quantity.

---

## v1 (2026-09-16) — the engine as inherited, and what the regime moved

The engine is lcm-ladders' v1 window sieve (itself linear-ladders' v4) with
the multiplier list swapped to k!. Everything problem-specific enters
through `killed_residues`, so the kernel needed no mathematical change.
What the regime changed:

### Measurement 1 — the wheel: strong per prime, and bounded by 2^63

`w(q,n) = #distinct(1!..min(n,q−1)! mod q)`. Per small prime the wheel keeps
0.4–0.6 of the line (11 keeps 0.545 at every n ≥ 10: only 5 of 1!..10! are
distinct mod 11), against the lcm ladders' 0.9 and the linear ladders'
1/(q−1). Only 2 and 3 are ever forced (Wilson), so the unit is 6 at every
filter and the wheel's period is 6·∏(wheel primes). The full wheel to 47 has
W′ = 1.02e17, and the Barrett tail's one-conditional-subtraction bound
`(PV + 1)·W′ + q2 < 2^63` then admits **89 periods** of window, not the
224 the constant asks for. Below n = 16 the period cap from the modelled
median (`search_period_cap`, median/4) is what binds, and the planner takes
a shorter wheel: {5..23, 31} at n = 11, growing one prime per filter to the
full wheel at n = 16.

**Kept as the design premise.** The one thing it forces is the question
Measurement 3 answers: at n = 17, is the full wheel with an 89-period window
better than the wheel to 43 with 224?

### Measurement 2 — the sieve-depth ladder is capped at 2^20

`plan_q2` takes the smallest depth whose analytic survival is under
`SURV_TARGET = 5e-8`, and the ladder's top otherwise. At n = 11 the survival
through every prime to 2^20 is still 1.2e-6 (eleven forms, and the wheel is
short), so the planner returns the top at n = 11..13. lcm-ladders' ladder
ran to 2^24, which here would be 1.07 million tail primes × 512 bytes of
mask = **550 MB of device memory** for filters whose whole hunt is seconds.
Capped at 2^20 (82 k primes, 42 MB). The host pool is sized from a
measurement at the filter regardless, so a survivor rate above the target at
those filters costs cores for a minute, not coverage.

### A hazard the gates caught: the empty middle level

`_split_levels` chooses the three CRT levels of a wheel; the short wheels
of the opening filters made it return `((5..23), (), (31,))` — an empty
second level with a non-empty third. `GpuEngine` builds levels in order and
drops a third level behind an absent second, **and** `self.primes` is the
complement of all three levels, so 31 would have been in neither the wheel
nor the sieve: untested, silently, at the campaign's opening filter. G13
(which builds every planned wheel level by level on the host) failed on a
non-invertible W1 mod W2. The splitter now normalises that shape to a
two-level wheel. The same latent shape is in lcm-ladders' `_split_levels`,
where no filter reaches it; its gates were not run (CLAUDE.md rule 2).

### A gate's wall clock

G4 (CPU survivors against the definition) multiplied object-dtype arrays by
18! over 4-million-element windows: 66 s. The same test on residues in int64
is 21 s. The definition is unchanged — q | m·x + s is decided mod q.

### Measurement 3 — the window at the full wheel: 89 and 64 tie, 32 and the shorter wheel lose

The question Measurement 1 raised, measured paired at n = 17 of A177013
(three interleaved rounds of ~4 s, unit 6, sieve 65536, planned depths):

| configuration | x/s | ratio | segment | over-sweep at the a(17) median |
|---|---|---|---|---|
| wheel to 47, 89-period window (the 2^63 bound's own) | 1.426e17 | **1.000** | 5.4e19 | 39% |
| wheel to 47, 64-period window | 1.426e17 | **1.000** | 3.9e19 | 28% |
| wheel to 43, 224-period window | 1.288e17 | 0.903 | 2.9e18 | 2% |
| wheel to 47, 32-period window | 1.105e17 | 0.775 | 2.0e19 | 14% |

The full wheel wins on rate, by 1.11x over the wheel to 43 even with a
window a third as wide — the extra prime keeps 0.70 of the line, and the
window sieve's cost per prime does not fall much below 64 periods. And 64
ties 89 exactly. The segment is the coverage unit (CONVENTIONS.md "Two
cursors"), so a find is only known to be the least once its segment closes
and costs up to one of them in over-sweep: at 89 periods that is 39% of the
a(17) median, at 64 it is 28%, for the same rate. **Kept: the full wheel,
with a window the reduction bound cuts rounded DOWN to a whole 32-bit word
(89 → 64).** A window the constant sets in full is left alone (224 at the
short wheels).

The honest accounting at the median: the wheel to 43 pays 1.107x of the
median in device time and ~1% in over-sweep; the full wheel at 64 pays
1.000x and an expected 14% (half a segment). Equal at the median, and the
full wheel pulls ahead as the term lands later — at the 2.5x the repo
budgets it is 1.06x against 1.11x — and it wins outright at n = 18, where a
segment is 0.6% of the median. The way to have both is item 2 below.

### Measurement 4 — the planned rate at every filter of the first night

Same harness, the campaign's own planned configuration (unit 6, planned
wheel and depth), three rounds of ~3 s each:

| filter | wheel | q2 | window | x/s | survivors/s | median | device to the median |
|---|---|---|---|---|---|---|---|
| n = 11 (opening) | {5..23, 31} | 2^20 | 224 | 7.57e14 | 170,000 | 3.4e10 | < 1 s (one segment) |
| n = 16 | {5..47} | 131072 | 64 | 9.38e16 | 62,000 | 3.1e18 | 33 s |
| n = 17 | {5..47} | 65536 | 64 | 1.43e17 | 67,000 | 1.4e20 | 16.7 min |
| n = 18 | {5..47} | 32768 | 64 | 2.04e17 | 91,000 | 6.0e21 | 8.2 h |

The survivor rates are what the pool is sized from at runtime; at 12–15 µs
per survivor they are 0.8–1.4 core-seconds per second, two or three
workers. n = 11's 170,000/s is the ladder top binding (Measurement 2), and
it lasts one segment.

### The constants: inherited, and what was re-swept

| constant | value | status |
|---|---|---|
| `PB_DEFAULT` | 224 | inherited; at n ≥ 16 the 2^63 bound cuts the window and it is rounded down to 64 (Measurement 3, a measured tie) |
| `QUEUE_BYTES_MAX` | 20 KB | inherited |
| `CAND_PER_LAUNCH4` | 2^37 | inherited |
| `BIT_SURV`, `K2_SURV4`, `R2_DROP` | 0.007, 0.0003, 0.5 | inherited |
| `TAIL_ROUND_DROP` | 0.7 | inherited |
| `SURV_TARGET` | 5e-8 | inherited; the pool is measured, so it prices machine, not coverage |
| `Q2_LADDER` | 2^12..2^20 | **changed** (Measurement 2) |
| `PV_MIN`, `WHEEL_TOP`, `CAMPAIGN_PERIOD_MARGIN` | 32, 89, 4 | inherited; the greedy stops before 53 at every filter |

Rule 5g's corollary applies in full: none of the inherited constants has
been re-swept at this project's filters yet, and the first optimization
pass owes a phase split at n = 16, 17 and 18 before it touches any of them.

---

## v2 / Round 2 (2026-09-16) — the phase split, the bound that was never 2^63, and the window it was hiding

### Measurement 5 — the phase split at the three filters that cost the night

CUDA events around every kernel of 24 launches at the campaign's own
planned configuration (64-period window, engine v1), interleaved with the
same launches un-instrumented; medians of three rounds. Instrumented wall
equalled production wall to 0.3% at every filter, so nothing overlaps here
and the split can be read directly:

| | n = 16 | n = 17 | n = 18 |
|---|---|---|---|
| per launch (2^37 candidates) | 69.9 ms | 64.7 ms | 51.4 ms |
| the sieve kernel (window + extraction + in-block rounds) | **91.4%** | **92.5%** | **93.8%** |
| all tail rounds | 8.6% | 7.5% | 6.2% |
| device / wall | 99.8% | 99.8% | 99.8% |
| survivors/s | 58,800 | 66,100 | 87,700 |
| host, per survivor (`sprp_run` to n + 8) | 12.5 µs | 12.0 µs | 11.5 µs |
| host, core-seconds per second | 0.74 | 0.79 | 1.01 |

So the window kernel is the phase, the host needs one core with a pool of
two or three, and the tail rounds are under a tenth. Every verdict below is
from the production path.

### Measurement 6 — the reduction bound is 2^64, not 2^63

The window on the full wheel was cut by `(PV + 1)·W′ + q2 < 2^63`, the
stated exactness bound of the tail's one-conditional-subtraction Barrett
step, inherited through three projects. **The bound of that arithmetic is
the word.** With `mg = floor(2^64/q) = (2^64 − ρ)/q`, `ρ = 2^64 mod q < q`,
and `off = a·q + b`:

    off·mg / 2^64 = a + b/q − off·ρ/(q·2^64),

and the last term is under `ρ/q < 1` for every `off < 2^64`, so the floor
is `a` or `a − 1`, the remainder is `b` or `b + q`, and one conditional
subtraction is exact. Nothing in the kernel needs more: the offset is a
u64 in the survivor record, the queue and `off_of`, and every other use of
it (the in-block rounds' `__umul64hi(off, mg)`, the tail's `TEST`) is this
same reduction.

Emulated bit for bit (the u32 wrapping subtraction the device does) at
every prime of the ladder to 2^20 — 82,023 primes × 68 offsets in
[2^63, 2^64), edges included, with and without the base fold: **0
mismatches**; and at `2^64 + 12345 mod 65521` the same computation returns
12345 for 62970 — the tripwire, so the bound is real and it is 2^64. G19
carries the emulation, the tripwire, a device parity across window widths
on the full wheel where offsets pass 2^63, and the clamp at exactly the
bound. `REDUCE_MAX = 1 << 64`; the full wheel now admits **179 periods**.

### Measurement 7 — the window at the full wheel, measured at last

Paired and interleaved, three rounds of 20 launches, the planned wheel and
depth, engine v2 (exact at every width shown; the survivor stream over the
same 179 absolute periods was identical at every width, 24,021 / 13,041 /
44,522 survivors at the three filters):

| window (periods) | 64 | 96 | 128 | 160 | 179 |
|---|---|---|---|---|---|
| n = 17 | 1.000 | 1.111 | 1.124 | 1.168 | **1.194** |
| n = 18 | 1.000 | — | 1.084 | 1.096 | 1.088 |
| n = 16 | 1.000 | — | — | 1.056 | 1.069 |

160 against 179 (five words against six with the last 19/32 live), five
rounds at n = 17: **1.050**. **Kept: the bound's own 179, no round-down**
(v1's round-down rested on a tie between 89 and 64 under the old bound).
The segment is now 1.1e20 of line, a fifth of a(17)'s median, and that
over-sweep is what the launcher change below turns from waste into work.

### Measurement 8 — past 2^64 (timing-only ablation): a wider record buys nothing here

With the bound forced past 2^64 the offset wraps and the kills of the
periods past 179 are random — statistically the same load on the rounds
and the tail, so the timing is fair and the survivors are wrong. At n = 17:
192 / 224 / 256 periods read **1.000 / 0.975 / 0.967**. The window has
stopped paying by 179 on this wheel, so the "wider survivor record" item
inherited from lcm-ladders is worth nothing as a window lever; what it
still buys is a *wheel* prime (below).

### Measurement 9 — the queue margin was chasing an occupancy registers forbid

At pb = 179 the kernel is 10–15 KB of shared memory, so the shared-memory
prediction says 8–9 blocks per SM while 78–88 registers allow 5–6, and the
chooser took the SMALLEST margin (2.5 at n = 18) to reach a number it could
not have. Measured at n = 18: 2.5 / 3.0 / 6.0 read 1.000 / 0.999 / 0.993 —
flat, so the margin is free, and a margin is overflow safety (the in-block
fallback is 0.67x when it is the rule). **The chooser now compiles, reads
the occupancy actually reached, and re-takes the largest margin whose
prediction still reaches it** (one recompile; a revert is a cache hit).
n = 18 now runs sigma 5.0 at 6 blocks per SM; n = 16 and 17 keep 2.5 and
3.0, where the shared prediction is what binds.

### Measurement 10 — every constant, re-swept at the new window (n = 17, 179 periods)

Rule 1's corollary: the window is a structural change. Paired, interleaved,
three rounds unless stated; **bold** is the shipped value.

| knob | values | ratios | verdict |
|---|---|---|---|
| `EXTRACT_EVERY` at NW = 5 | **1** / 2 / 4 | 1.000 / 1.010 / 0.994 | noise; 1 |
| `BIT_SURV` | .012 / **.007** / .004 / .002 | 0.901 / 1.000 / 0.984 / 0.866 | unchanged |
| `K2_SURV4` | .001 / **.0003** / .0001 | 0.953 / 1.000 / 1.007 | unchanged |
| `spb` | 4 / **8** / 16 | 0.910 / 1.000 / 0.968 | unchanged |
| `tpb` | 64 / **128** / 256 | 0.912 / 1.000 / 1.067 → five rounds **1.004**; n = 18 0.984; n = 16 0.996 | the 1.067 was noise; 128 |
| `spb` at tpb = 256 | 4 / 8 / 16 | 0.932 / 1.000 / 0.159 | (for the record) |
| `TAIL_ROUND_DROP` | .5 / **.7** / .8 | 0.994 / 1.000 / 0.995 | flat |
| `R2_DROP` | .7 / **.5** / .35 | 0.883 / 1.000 / 0.958 | unchanged |
| `CAND_PER_LAUNCH4` | 2^36 / **2^37** / 2^38 | 0.936 / 1.000 / 1.026 → five rounds 1.055 (n = 17), 1.014 (n = 18) | **declined**: +500 MB of device queues and a checkpoint interval twice as coarse for an interval that straddles 1 at n = 18; re-price after the next structural change |
| `PAT_SHARED` | **True** / False | 1.000 / 0.926 | unchanged |
| `X0_SHARED` | **False** / True | 1.000 / 0.860 | unchanged |
| `BIT_GROUP_MAX` | **1** / 600 | 1.000 / 1.004 | unchanged |

Nothing moved. The window was the constant that mattered, and it was not a
constant — it was a bound.

### The launcher: a promotion carries the classified line

A find is only known to be the least once its segment closes, so a find
costs up to one segment of over-sweep — and at 179 periods a segment is a
fifth of a(17)'s median. v1 then re-swept that over-sweep: `follow_frontier`
put the new filter's cursor at the find. But every survivor of the closed
segment was classified to run n + 8, and the filter-(n + 1) sieve keeps a
subset of the filter-n sieve's survivors (K(q, n) ⊆ K(q, n + 1)), so no x
below the old boundary can be a(n + 1) without having been found as a rider.
The new filter now resumes at the end of the classified line, floored onto
its own period (`cover_x`, carried in the checkpoint and in the evidence's
`least_claim`); the claim's floor is still the find. Priced at the campaign's
own rates: **11 minutes at n = 16 → 17 and 9 at 17 → 18**, and at 15 → 16
the 224-period segment of the wheel to 43 reaches 2.9e18, most of a(16)'s
median, which the n = 16 sweep no longer repeats. `_promotion_drill` asserts
the landing period is the floor of the classified line, the clip is gone
past the floor, and the carried coverage round-trips.

### Round 2 result

Device rate at the campaign's own configuration, v2 against v1, from the
paired sweeps above (Measurement 7, the 179 column):

| filter | v1 | v2 | ratio | median | device to the median |
|---|---|---|---|---|---|
| n = 16 | 9.5e16 | 1.02e17 | 1.069 | 3.1e18 | 30 s (one segment: 18 min) |
| n = 17 | 1.38e17 | 1.65e17 | **1.194** | 1.4e20 | 14 min |
| n = 18 | 2.09e17 | 2.28e17 | 1.088 | 6.0e21 | 7.3 h |

The four campaign benchmark shapes were re-frozen at the planner's window
(OPTIMIZATION.md 2.13; the x-space anchors SCORE11, SCORE2L, SCORE1L and
SCORE9 are untouched): SCORE 85011 / 5307414496822302746 → 237557 /
2767396319084044674, SCOREP 84789 / 14859928121148689406 → 236826 /
80766670185484481804, SCORE16 113004 / 45101136010290950814 → 315001 /
4287120428541611542, SCORE18 86713 / 17201059566049407390 → 242137 /
8189509089178047674. SCORE 129,965 -> **164,784** (1.268x), SCOREP 130,278 -> 150,728, SCORE16 83,029 -> **104,178** (1.255x), SCORE18 164,899 -> **227,223** (1.378x), the same session's v1 run as the base; the anchors SCORE2L / SCORE1L / SCORE9 read 18,996 / 8,091 / 6.05 against 19,120 / 7,749 / 6.35 (flat). SCORE11 read 485 against 795 in the two score.py runs, which is the shape, not the engine: it is 0.04 s of device per run, and paired over five rounds the chooser's own margin (4.0) is the fastest of 2.5 / 4.0 / 6.0 / auto at 8.74e14 x/s, with single runs of that shape spanning 2.8e14 to 8.9e14. 45/45 green in 252 s.

### Measurement 11 -- the segment loop's wall clock, off-device

The measurement neither a benchmark nor a gate can make (OPTIMIZATION.md
2.14): the campaign's own per-launch methods, timed on a scratch checkpoint
at the opening filter and at n = 17, against one launch of device (279 ms
at n = 11, one launch per segment; 83 ms at n = 17, 12,936 launches per
segment):

| per launch | n = 11 | n = 17 |
|---|---|---|
| `check_rungs` + `ladder()` + `next_rung` | 5.1 us | 7.8 us |
| `state()` + `mark_boundary` | 4.7 us | 5.9 us |
| `status_line` (the heartbeat, every 30 s) | 7.1 us | 10.0 us |
| `k_min`, `swept_k`, `u_progress`, `check_proof_crossing`, `_drain` | 2.9 us | 4.0 us |
| **total, excluding the save** | **18.9 us (0.01%)** | **26.1 us (0.03%)** |
| `save()` (rate-limited to once per 2 s) | 1.11 ms | 1.03 ms |

Nothing to find: the loop is the device. The inherited `lru_cache` on
`plan_for` and `x_floor` is what keeps it there (lcm-ladders' Measurement 9
was 34 ms per launch before it).

### Termination table (OPTIMIZATION.md Part 3), as it stands

| phase | share | verdict |
|---|---|---|
| the sieve kernel (window + extraction + in-block rounds) | 91–94% | **unsearched at the instruction level in this project.** Its window is now at the bound's width; its constants are fresh; lcm-ladders' round 9 reached "bound by the latency of its load chain" on the same kernel at NW = 7 (rooflines at ~26%, the accumulator chain 0.998x when split, occupancy at its limit) — but that verdict is inherited, not re-derived, and INNOVATION.md's two passes have not been run here. The levers left are priced below |
| all tail rounds | 6–9% | compaction rounds, drop point re-swept flat (0.5–0.8), lanes per item and block size inherited flat |
| host classification | 0.7–1.0 core-s per s | 12 µs per survivor, pool sized at runtime; the device binds with two or three workers |
| the campaign loop, off-device | **0.03% of a launch** | timed on a scratch checkpoint at n = 11 and n = 17 (Measurement 11): `check_rungs` 3.3 us, `ladder()` 1.6, `state()` 2.9, `mark_boundary` 3.0, `status_line` 10, `_drain` 1.0 -- 26 us per launch against 65-83 ms of device; `save()` 1.0 ms, rate-limited to once per 2 s (0.04%). The inherited `plan_for`/`x_floor` cache holds here |

---

## Open, priced, unbuilt

Written down so the next pass starts from evidence (OPTIMIZATION.md Rule 6):

1. **INNOVATION.md's two passes on the window loop** — the phase is 92% and
   its verdict is inherited. The representation hunt: the window is NW
   words of a periodic bit pattern per prime, gathered by `r >> 5` and
   funnel-shifted by `r & 31` (7 shared loads + 6 funnel shifts + 6 ORs per
   prime per 179 candidates, 31 primes); the instruction-level pass wants
   the real SASS and the pipe the loop saturates. Two candidates from the
   inherited log, unpriced here: a 64-bit pattern word (4 loads + 3
   two-instruction shifts per prime: ~1.1x best case on the phase), and two
   first-level residues per thread for ILP (register pressure is the
   warning, lcm-ladders Measurement 12).
2. **The wheel to 53 at n ≥ 19**, through the split survivor record. keep(53)
   is ~0.72 at n = 18, so 1.39x fewer candidates; the period ×53 is 3.2e19,
   which the over-sweep margin admits only from n = 19 (median 2.8e23: 8,750
   periods) — at n = 18 a 64-period segment would be a third of the median
   and the density gain would be spent on over-sweep. It needs W′ = 5.4e18,
   past the u64 offset the record carries (the within-period offset and the
   period index emitted separately; the in-block rounds and the tail then
   reduce `off_p mod q + j·(W′ mod q)`, one more multiply-reduce per test on
   a phase worth 6–9%), and a non-contiguous level split ({5..23, 37} ×
   {29, 31, 41, 43, 47, 53} is the one that keeps both moduli under 2^32;
   `_split_levels` searches contiguous cuts only). Priced at ~1.2–1.3x on
   a(19)'s 17-day leg; not worth it at n = 17 or 18. 59 is dead: its period
   overflows the u64 within-period offset itself.
3. **`CAND_PER_LAUNCH4` = 2^38**: 1.055 / 1.014 at n = 17 / 18 for +500 MB
   and a checkpoint interval twice as coarse (Measurement 10). Re-price after
   the next structural change; ship it if it clears 3% at both filters.
4. **The early filters as a single segment, and the host they ask for** (v1
   item 3, unchanged): the sieve ladder's top binds at n = 11..13 for a
   quarter of a second of the machine per filter. Watch the first `[STATUS]`
   lines rather than tune blind.
