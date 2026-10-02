# BENCHMARKS — plus-two-cliques

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all five frozen shapes reproduce their work fingerprint (survivor count + xor
of the surviving candidates). The rate is end-to-end **line of the candidate
a(n) per second** (a(n)-line/s), and the published term is the candidate
itself, so there is nothing to multiply by.

Five shapes because a launcher owes a shape at every opening it has
(CLAUDE.md 5g), and here a family has exactly **one** opening: its open
index. The filter after it does not exist until a term is found. So there are
two campaign shapes, one per family, each the planned configuration at that
family's open index, and three anchors.

## The ledger

| date | engine / plan | SCORE | S083519 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|
| 2026-10-01 | v1 (product-cliques' engine v2, the first-level chunk capped at gridDim.y) / p2 (product-cliques' p3 plus the second first-level budget) | **1,098** | 502 | 525 | 754 | 5.99 |
| 2026-10-02 | v2 (lazy narrow rounds, u32 queue entries, packed window offsets, the per-launch offset table, wide launches 2^37; OPTIMIZATION_LOG.md round 2) / p2 | **1,307** | 545 | 543 | 825 | 6.01 |
| 2026-10-02 | v3 (the periodic window on quad loads, the wide record's folded rounds, generated tail rounds; OPTIMIZATION_LOG.md round 3) / p2 | **1,335** | 556 | 591 | 878 | 6.16 |
| 2026-10-02 | v3 / p2, unchanged: the score at the pause, after the two campaigns | **1,346** | 559 | 594 | 852 | 6.16 |

(in units of 10¹² a(n)-line/s: v3's SCORE is 1.33e15 a(n)-line/s, 2.3e12
candidates a second, and one run earlier it read 1,351; v2's read 1,402 one
run before the row above.) Both campaign shapes are a single launch of a few
hundredths of a second, because at the openings a segment is one launch, so a
reading is mostly launch overhead and moves between runs; the fingerprints do
not move at all, and v2 reproduced all five bit for bit. What the engine does
at the filters a campaign spends its hours in is the table below, not the
SCORE: there v2 measured **1.09-1.15x** against the v1 code path, paired,
on the same plan and the same stream, and v3 **1.04-1.12x** against v2's
(1.10x at the filter the A083518 campaign stands at), all five fingerprints
reproduced again.

## The shapes

| shape | family | n | class | wheel | sieve | window | fingerprint |
|---|---|---|---|---|---|---|---|
| SCORE | A083518 | 14 | 3 (mod 6) | {5..23},{31} | 2^19 | the first segment at period 1 (11,360 periods: 160-period windows batched) | 6511 / 110145145451837 |
| S083519 | A083519 | 11 | 3 (mod 6) | {5..23} | 2^20 | the first segment at period 1 (466,080 periods) | 31882 / 81801758003166 |
| SCORE2L | A083518 | 14 | dense line | (23],(37] | 65536 | 24 periods from 94334 | 137965 / 699912790830580669 |
| SCORE1L | A083518 | 14 | dense line | ≤ 23 | 65536 | the SAME absolute window, 33263× as many periods | 137965 / 699912790830580669 |
| SCORE9 | A083519 | 9 | dense line | ≤ 13 | 4096 | 4e8 periods from 3330003 | 5957470 / 13208176851254 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint, so a CRT-lift bug shows
up inside the benchmark rather than as a wrong answer months later. SCORE9 is
survivor-heavy (5,957,470 survivors), so it weighs the survivor path where
the others weigh line. The anchors are not product-cliques' windows. Its
SCORE2L window at n = 13 here keeps 4.67 million survivors and took 39 s a
run, so both anchors moved to n = 14 and a tenth of the periods.

The campaign shapes name their wheel, class, depth, window and launch
decomposition explicitly rather than asking the planner, so a tuning pass
cannot move a benchmark's window. `_families_stay_apart` (selftest) fails if
a shape and the campaign's plan at that opening ever disagree, so a *planner*
change cannot leave them behind either. **A find does not move a
fingerprint**: a shape names its index, and the form list of an index never
changes once it exists. What a find does is open a *new* filter, and rule 5g
then owes a shape at it.

All five were frozen on 2026-10-01 after the GPU/CPU parity gate G9 passed
on 26 populated windows (455,957 survivors), with the chunk cap and the
second budget in place. Neither changes either opening's plan or
decomposition. Engine v2 (2026-10-02) reproduced all five bit for bit, and
engine v3 (2026-10-02) again; nothing was re-frozen.

## Every opening, and the filters after it, priced (CLAUDE.md 5c and 5g)

Engine v2, planner p2, through the engine API (OPTIMIZATION_LOG.md round 2):
real launches swept and timed at the modelled median, interleaved with the v1
code path on the same launches, with EXACT candidate counts per launch, their
survivors counted, 1,500 of them classified by the launcher's own `sprp_run`,
and the model's expected line to a *confirmed* find divided by the measured
rate. Rows marked * are on STAND-IN filters: the model's stand-in terms are
registered in a scratch process only. The filter a real find opens is planned
from the real term the moment it lands, and will differ. "Segment / median"
is the planned segment's line over the modelled median: the over-sweep a find
costs, which the planner trades against rate. The rows from a filter of
seconds down were priced on v1 (round 1) and not re-priced: they are launch
overhead, not rate.

| filter | plan p2 | segment / median | device, a(n)-line/s | candidates/s | host, core-s/s | expected clock to a confirmed find | v2 / v1 |
|---|---|---|---|---|---|---|---|
| A083518 n = 14 | {5..23},{31} × 160, 2^19 | 0.36 | one launch | | 1.6 | 0.01 s (v1) | |
| A083518 n = 15* | {5..23},{29},{31} × 160, 2^18 | 0.29 | one launch | | 0.42 | 0.5 s (v1) | |
| A083518 n = 16* | {5..23},{29,31},{37} × 160, 2^17 | 0.30 | 5.4e15 (v1) | 3.1e12 (v1) | 2.2 | 1.6 s (v1) | |
| A083518 n = 17* | {5..23},{29,31},{37,43} × 160, 2^17 | 0.34 | 9.5e15 | 3.6e12 | 0.97 | 34 s | 1.093 |
| A083518 n = 18* | {5..23},{29,31,37},{41,43} × 160, 2^17 | 0.33 | 1.67e16 | 4.0e12 | 0.48 | 14 min | 1.125 |
| A083518 n = 19* | to 47 × 160, 2^17 | 0.38 | 2.68e16 | 4.2e12 | 0.27 | **5.9 h** | 1.108 |
| A083518 n = 20* | to 53, WIDE, × 160, 2^16 | 0.47 | 3.97e16 | 4.1e12 | 0.38 | **171 h** (7.1 days) | 1.101 |
| A083518 n = 21* | to 53, WIDE, × 224, 2^15 | 0.011 | 6.18e16 | 4.6e12 | 0.58 | 5,992 h | 1.149 |
| A083519 n = 11 | {5..23} × 160, 2^20 | 0.96 | one launch | | 0.61 | < 0.01 s (v1) | |
| A083519 n = 12* | {5..23},{31} × 160, 2^20 | 1.65 | one launch | | 0.17 | 0.03 s (v1) | |
| A083519 n = 13* | {5..23},{29},{31} × 160, 2^20 | 1.32 | one launch | | 0.25 | 0.14 s (v1) | |
| A083519 n = 14* | {5..23},{29,31},{37} × 160, 2^19 | 1.35 | 9.5e15 (v1) | 2.3e12 (v1) | 1.1 | 0.25 s (v1) | |
| A083519 n = 15* | {5..23},{29,31},{37} × 160, 2^17 | 0.042 | 1.4e16 (v1) | 3.0e12 (v1) | 1.5 | 4 s (v1) | |
| A083519 n = 16* | {5..23},{29,31},{37,43} × 160, 2^17 | 0.052 | 2.57e16 | 3.7e12 | 0.92 | 76 s | 1.109 |
| A083519 n = 17* | {5..23},{29,31,37},{43,47} × 160, 2^18 | 0.060 | 4.61e16 | 3.9e12 | 0.23 | 29 min | 1.128 |
| A083519 n = 18* | to 47 × 160, 2^17 | 0.064 | 7.24e16 | 4.0e12 | 0.26 | **11.5 h** | 1.112 |
| A083519 n = 19* | to 53, WIDE, × 160, 2^16 | 0.073 | 1.15e17 | 4.0e12 | 0.34 | **337 h** (14.0 days) | 1.108 |

"To 47" is {5..23},{29,31,37},{41,43,47}, the full wheel to 47 over the class
3 (mod 6). "To 53" is {5..23, 37},{29,31,41},{43,47,53} on the wide survivor
record: 9.3 million first-level residues at A083518 n = 20* and 3.2 million at
A083519 n = 19*, holding 2.75 and 1.14 GiB of device memory. The device runs
3.6–4.5e12 candidates a second wherever a segment is tens of launches. Where
it is one launch (the openings, A083519 n = 12 and 13), the filter is
launch-bound and costs under a second, and the line rate is not a meaningful
number. The host figures are what a pool is sized from at runtime
(ceil(need × 2) workers, ramped). That is four workers at A083518's opening
and two or three for the minutes the early filters last, then one or two at
every filter that runs for hours. A classification costs 11–15 µs past the
openings and 40–130 µs at them, where survivors are rare and each carries
the full chain. The absolute clocks are one session's: a desktop GPU's rate
moves with ambient load, and in the session that measured v2 the v1 path
priced A083518 n = 19* at 6.5 h, not round 1's 6.3 h. The v2 / v1 column,
paired and interleaved on the same launches, is the stable quantity.

The planned configuration was paired against its neighbours at the four
hour filters (OPTIMIZATION_LOG.md round 1), and again on the v2 engine at
the four hour and day filters (round 2). Every alternative tied or lost,
except the full wheel to 53 at the multi-day filters, which is the plan.

## Engine v3 against v2, and the filter the campaign stands at

Round 3 (OPTIMIZATION_LOG.md) was measured at the filter the A083518
campaign had reached on its REAL terms, n = 20, which the stand-in row above
could only approximate: the real a(19) plans the wheel to 59 less 41, where
the stand-in planned the wheel to 53. Paired and interleaved against the v2
code path on the same plan and the same launches, the stream compared on
every run. Starred rows are stand-ins regenerated in that session (not the
ones the table above was priced on, so their plans and absolute rates are
not comparable with it).

| filter | plan p2 | device, a(n)-line/s | candidates/s | device memory, GiB | v3 / v2 |
|---|---|---|---|---|---|
| **A083518 n = 20** | {5..17, 23, 29, 37},{19, 31, 43},{47, 53, 59}, WIDE, × 160, 2^16 | 4.63e16 | 4.5e12 | 1.40 (v2 4.32) | **1.103** |
| A083518 n = 21* | WIDE, × 224 | 5.74e16 | 5.3e12 | 0.91 (2.66) | 1.120 |
| A083519 n = 14* | narrow, × 160 | 1.05e16 | 3.0e12 | 0.35 | 1.044 |
| A083519 n = 16* | narrow, × 160 | 4.38e16 | 3.8e12 | 0.23 | 1.060 |
| A083519 n = 17* | narrow, × 160 | 5.55e16 | 4.3e12 | 0.23 | 1.051 |
| A083519 n = 18* | narrow, × 160 | 8.90e16 | 4.0e12 | 0.22 | 1.051 |
| A083519 n = 19* | WIDE, × 160 | 1.45e17 | 4.4e12 | 0.49 (1.23) | 1.108 |

At A083518's filter n = 20 a segment is 160 periods, 7.5e21 of a(n)-line and
5,392,200 launches (about 45 hours of device on v3), and the model's
expected line to a *confirmed* a(20) from a(19) is 2.58e22: **about 155
hours of device on v3 against 171 on v2** at that session's rates. The
campaign was 209,513 launches into the first segment when v3 was gated, and
resumes there (the v2 cursor is accepted at its launch).

## The campaigns against these prices

The owner's two campaigns of 2026-10-02 (RESULTS.md, "The campaigns against
their benchmarks") ran A083518 on engine v2 at 1.4e16 a(n)-line/s on the
filter for a(18), 2.3e16 on the filter for a(19) and 4.1e16 on the filter
for a(20), against 1.7e16*, 2.7e16* and 4.0e16* above: 0.84–1.04× the
stand-in prices, the real n = 20 filter planning the wheel to 59 without 41.
A083519 on engine v3 ran 1.9e16, 3.3e16, 5.9e16 and 9.7e16 on the filters
for a(16) through a(19), against v3's 4.4e16*, 5.6e16*, 8.9e16* and 1.5e17*:
about 0.67× at every one, on the same wheels the stand-ins had planned. The
GPU was shared with the desktop throughout, and the cause of the 0.67× is
not measured; a paired measurement at the live filters is owed (RESULTS.md,
"What is open now"). Campaign rates are the line between finds over the
leg's wall clock, verification and promotion included, so they understate
the engine somewhat. The project is **PAUSED** with both open filters wide,
and no shape is frozen at either (rule 5g owes one; a segment there is 45 h
of device, so the shape will have to be launch-denominated).
