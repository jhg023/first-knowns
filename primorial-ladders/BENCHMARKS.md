# BENCHMARKS — primorial-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all six frozen shapes reproduce their work fingerprint (survivor count + xor
of the surviving terms). The rate is end-to-end **line of the term per
second** — p/s on the primorial entries, m/s on A145743 — and the published
term is the swept integer itself, so there is nothing to multiply by.

Six shapes because a launcher owes a shape at every opening it has
(CLAUDE.md 5g): three campaign shapes, one per family at its open index,
each the planned configuration there, and three anchors.

## The ledger

| date | engine / plan | SCORE | S115786 | S145743 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|---|
| 2026-10-02 | v1 (plus-two-cliques' engine v3, taken whole; the extraction batch and the queue entry decided on this problem's compiled occupancy, OPTIMIZATION_LOG.md round 1) / p1 | **2,223** | 2,564 | 11,154 | 773 | 1,407 | 9.40 |
| 2026-10-05 | v1 / p1, unchanged: the reading at the pause, after the three campaigns; all six fingerprints reproduced | **2,086** | 2,399 | 10,382 | 732 | 1,318 | 8.82 |

(in units of 10¹² line/s: SCORE is 2.22e15 p/s.) The three campaign
shapes are a single launch or a few of them, hundredths of a second, so a
reading is mostly launch overhead and moves between runs; the fingerprints
do not move at all. What the engine does at the filters a campaign spends
its hours in is the table below, not the SCORE.

## The shapes

| shape | family | n | class | wheel | sieve | window | fingerprint |
|---|---|---|---|---|---|---|---|
| SCORE | A115785 | 16 | 1 (mod 6) | {5..23},{29,31},{47} | 2^17 | 2 third-level residues of the first segment above 53# + 2^17 (160 periods of 9.43e12) | 476 / 4435445385692368 |
| S115786 | A115786 | 17 | 5 (mod 6) | {5..23},{29,31},{47} | 2^16 | 2 third-level residues of the segment at period 1 | 493 / 491914220257447 |
| S145743 | A145743 | 14 | 1 (mod 6) | {5..23},{29} | 2^17 | the whole first segment at period 1 (160-period windows batched) | 3537 / 189173167754451 |
| SCORE2L | A115786 | 17 | dense line | (23],(37] | 65536 | 24 periods from 94334 | 922 / 114412237886258 |
| SCORE1L | A115786 | 17 | dense line | ≤ 23 | 65536 | the SAME absolute window, 33263× as many periods | 922 / 114412237886258 |
| SCORE9 | A145743 | 9 | dense line | ≤ 13 | 4096 | 4e8 periods from 3330003 | 4052672 / 11896430721506 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint, so a CRT-lift bug
shows up inside the benchmark rather than as a wrong answer months later.
SCORE9 is survivor-heavy (4,052,672 survivors), so it weighs the survivor
path where the others weigh line.

The campaign shapes name their wheel, class, depth, window and launch
decomposition explicitly rather than asking the planner, so a tuning pass
cannot move a benchmark's window. `_families_stay_apart` (selftest) fails
if a shape and the campaign's plan at that opening ever disagree. **A find
does not move a fingerprint**: a shape names its index, and an index's form
list never changes. What a find does is open a new filter, and rule 5g then
owes a shape at it.

All six were frozen on 2026-10-02 on engine v1 before round 1, after the
GPU/CPU parity gate G9 passed on 29 populated windows (635,683 survivors);
round 1's engine reproduced all six bit for bit.

## Every opening, and the filters after it, priced (CLAUDE.md 5c and 5g)

Engine v1 after round 1, planner p1, through the engine API: 40 real
launches of the planned engine at each filter, timed with the device
synchronised, survivors counted, and the model's expected line to a
*confirmed* find (from the index's own floor, in whole segments) divided by
the measured rate. Every filter exists here, so these are real plans on
real constants, not stand-ins; "segment / median" is the planned segment's
line over the modelled median (the over-sweep a find costs, which the
planner trades against rate). The absolute clocks are one session's on a
desktop GPU whose rate moves with ambient load; the expected clocks are
model medians, and A115785's model runs 2.4× optimistic on its known terms.

| filter | plan p1 | segment / median | device, line/s | candidates/s | survivors/s | host, core-s/s | expected clock to a confirmed find |
|---|---|---|---|---|---|---|---|
| A115785 n = 16 | {5,7,11,13,17,19,23,29,31,47} x 160, 2^17 | 0.031 | 4.59e+15 p/s | 5.6e+12 | 22,482 | 0.26 | **15.87 s** (40 launches, 16 a segment) |
| A115785 n = 17 | {5,7,11,13,17,19,23,29,31,37,47} x 160, 2^16 | 0.04 | 6.61e+15 p/s | 5.6e+12 | 34,198 | 0.38 | **5.3 min** (40 launches, 416 a segment) |
| A115785 n = 18 | {5,7,11,13,17,19,23,29,31,37,43,47} x 160, 2^16 | 0.056 | 9.27e+15 p/s | 5.7e+12 | 18,406 | 0.21 | **1.9 h** (40 launches, 10912 a segment) |
| A115785 n = 19 | {5,7,11,13,17,19,23,29,31,37,41,43,47} x 160, 2^15 | 0.073 | 1.28e+16 p/s | 5.8e+12 | 35,891 | 0.40 | **43.8 h** (40 launches, 327360 a segment) |
| A115785 n = 20 | {5,7,11,13,17,19,23,29,31,37,41,43,47} x 160, 2^15 | 0.0023 | 1.11e+16 p/s | 5e+12 | 13,355 | 0.15 | **66.1 days** (40 launches, 327360 a segment) |
| A115786 n = 17 | {5,7,11,13,17,19,23,29,31,47} x 160, 2^16 | 0.12 | 5.03e+15 p/s | 6.1e+12 | 26,703 | 0.29 | **6.62 s** (40 launches, 16 a segment) |
| A115786 n = 18 | {5,7,11,13,17,19,23,29,31,37,47} x 160, 2^15 | 0.15 | 7.21e+15 p/s | 6.1e+12 | 47,937 | 0.42 | **2.0 min** (40 launches, 416 a segment) |
| A115786 n = 19 | {5,7,11,13,17,19,23,29,31,37,43,47} x 160, 2^15 | 0.26 | 1e+16 p/s | 6.1e+12 | 27,699 | 0.29 | **36.7 min** (40 launches, 10912 a segment) |
| A115786 n = 20 | {5,7,11,13,17,19,23,29,31,37,41,43,47} x 160, 2^15 | 0.42 | 1.35e+16 p/s | 6.1e+12 | 16,227 | 0.17 | **11.6 h** (40 launches, 327360 a segment) |
| A115786 n = 21 | {5,7,11,13,17,19,23,29,31,37,41,43,47} x 160, 2^14 | 0.016 | 1.11e+16 p/s | 5e+12 | 26,212 | 0.26 | **14.2 days** (40 launches, 327360 a segment) |
| A145743 n = 14 | {5,7,11,13,17,19,23,29} x 160, 2^17 | 0.29 | 1.46e+15 m/s | 6.6e+11 | 15,242 | 0.33 | **0.01 s** (40 launches, 1 a segment) |
| A145743 n = 15 | {5,7,11,13,17,19,23,29,31} x 160, 2^16 | 0.31 | 1.97e+16 m/s | 4.6e+12 | 135,569 | 2.06 | **0.02 s** (40 launches, 1 a segment) |
| A145743 n = 16 | {5,7,11,13,17,19,23,29,31,37} x 160, 2^15 | 0.52 | 4.86e+16 m/s | 6.4e+12 | 258,851 | 3.07 | **0.16 s** (40 launches, 2 a segment) |
| A145743 n = 17 | {5,7,11,13,17,19,23,29,31,37,41} x 160, 2^16 | 0.56 | 7.73e+16 m/s | 5.1e+12 | 37,669 | 0.41 | **3.61 s** (40 launches, 24 a segment) |
| A145743 n = 18 | {5,7,11,13,17,19,23,29,31,37,41,43} x 160, 2^16 | 0.69 | 1.39e+17 m/s | 4.8e+12 | 19,327 | 0.22 | **1.1 min** (40 launches, 575 a segment) |
| A145743 n = 19 | {5,7,11,13,17,19,23,29,31,37,41,43,47} x 160, 2^15 | 0.81 | 2.81e+17 m/s | 4.8e+12 | 35,923 | 0.38 | **21.9 min** (40 launches, 14784 a segment) |

The device runs 5–6×10¹² candidates a second wherever a segment is more
than a launch; where it is one launch (A145743's opening), the filter is
launch-bound and costs seconds, and the line rate is not a meaningful
number. The host figures are what the pool is sized from at runtime
(ceil(need × 2) workers, ramped): one or two workers everywhere here, a
classification costing 10–20 µs.

## The campaigns against this table (2026-10-02 to 2026-10-05)

One campaign per family, no flags. A find is confirmed when its segment
closes, so each rate is the line to the end of the find's segment over the
leg's wall clock, the build, the pool's sizing and the verification
included.

| filter | priced above | the campaign | ratio |
|---|---|---|---|
| A115785 n = 18 | 9.27e15 p/s | 9.2e15 p/s over 8.15 h | 0.99 |
| A115785 n = 19 | 1.28e16 p/s | 1.29e16 p/s over 4.25 h | 1.01 |
| A115786 n = 19 | 1.00e16 p/s | 9.8e15 p/s over 5.04 h | 0.98 |
| A115786 n = 20 | 1.35e16 p/s | 1.32e16 p/s over 4.14 h | 0.98 |
| A145743 n = 19 | 2.81e17 m/s | 3.5e17 m/s over 18.5 min (one segment) | 1.25 |
| A145743 n = 20 | not priced | 6.3e17 m/s over 39.2 h | — |

The expected clocks were the model's and the terms did not keep to them
(RESULTS.md, "The finds against the model"); the rates held. Not in the
table above and owed before a resume (rule 5g): A145743 at n = 20 and
n = 21, which this document never priced because a(19) was modelled at 22
minutes; a frozen shape at each live filter (A115785 n = 20, A115786
n = 21, A145743 n = 21); and a line-denominated measurement at the two
filters the primorial campaigns were stopped in, which read 1.36e16 and
1.4e16 p/s against 1.11e16 on a count of launches.
