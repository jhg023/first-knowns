# BENCHMARKS — primorial-runs

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all six frozen shapes reproduce their work fingerprint (survivor count + xor
of the surviving terms). The rate is end-to-end **line of the term per
second** — p/s on all three entries — and the published term is the swept
integer itself, so there is nothing to multiply by.

Six shapes because a launcher owes a shape at every opening it has
(CLAUDE.md 5g): three campaign shapes, one per family at its lowest open
index, each the planned configuration there, and three anchors.

## The ledger

| date | engine / plan | SCORE | S257467 | S258035 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|---|
| 2026-10-05 | v1 (primorial-ladders' engine v1, taken whole) / p1, first reading | **4,730** | 1,009 | 149 | 1,120 | 2,042 | 7.50 |
| 2026-10-05 | the same engine and plan, second reading later in the same session, all six fingerprints reproduced | **1,525** | 1,030 | 148 | 1,116 | 2,030 | 6.91 |
| 2026-10-05 | v2 (every window prime on a quad table, minimal reads; OPTIMIZATION_LOG.md round 2) / p1, all six fingerprints reproduced | **1,572** | 1,052 | 137 | 1,126 | 2,061 | 6.46 |
| 2026-10-08 | v2 / p1, unchanged: the reading at the pause, after the three campaigns; all six fingerprints reproduced | **1,129** | 1,052 | 150 | 1,171 | 2,064 | 6.70 |

Engine v2 is worth 1.010 / 1.010 / 1.015 at the three days-long filters
(A257467 n = 19, A257466 n = 21, A258035 n = 19; paired, eleven rounds),
which the one-launch campaign shapes and the launch-bound anchors cannot
resolve: the ledger moves with ambient load, the fingerprints do not.

The three campaign shapes are a single launch each, hundredths of a second,
so a reading is mostly launch overhead and moves between runs; the
fingerprints do not move at all. The openings are cheap — each of those
terms is seconds away — and what the engine does at the filters a campaign
spends its hours in is the table below, not the SCORE.

## The shapes

| shape | family | n | class | wheel | sieve | window | fingerprint |
|---|---|---|---|---|---|---|---|
| SCORE | A257466 | 16 | 5 (mod 6) | {5..23},{29},{43} | 2^16 | 30 third-level residues (all of them) of the segment at period 1, 160 periods | 895 / 93971724717869 |
| S257467 | A257467 | 15 | 1 (mod 6) | {5..23},{29,31},{37} | 2^17 | 1 third-level residue of the segment at period 1, 160 periods | 1744 / 757665500541774 |
| S258035 | A258035 | 11 | 1 (mod 6) | {5,7,11,13,19,23}, one level | 2^20 | the whole first segment at period 1 | 3391 / 1136741374497 |
| SCORE2L | A257466 | 17 | dense line | (23],(37] | 65536 | 24 periods from 94334 | 687 / 699994667787293129 |
| SCORE1L | A257466 | 17 | dense line | ≤ 23 | 65536 | the SAME absolute window, 33263× as many periods | 687 / 699994667787293129 |
| SCORE9 | A258035 | 9 | dense line | ≤ 13 | 4096 | 1e8 periods from 3330003 | 1317082 / 2898241567362 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint, so a CRT-lift bug
shows up inside the benchmark rather than as a wrong answer months later.
SCORE9 is survivor-heavy (1,317,082 survivors), so it weighs the survivor
path where the others weigh line.

The campaign shapes name their wheel, class, depth, window and launch
decomposition explicitly rather than asking the planner, so a tuning pass
cannot move a benchmark's window; the launcher's selftest fails if a shape
and the campaign's plan at that opening ever disagree. **A find does not
move a fingerprint**: a shape names its index, and an index's form list
never changes. What a find does is open a new filter, and rule 5g then owes
a shape at it.

All six were frozen on 2026-10-05 on engine v1, after the GPU/CPU parity
gate G9 passed on 29 populated windows (749,295 survivors).

## Every opening, and the filters after it, priced

Engine v1, planner p1, through the engine API (2026-10-05): the planned
engine at each filter, warmed, then at least a second of real launches
timed with the device synchronised, survivors counted, a 3,000-survivor
sample classified on one core, and the model's median for that index (from
the bottom of the line) divided by the measured rate. Every filter exists
here, so these are real plans on real constants. "segment / median" is the
planned segment's line over the modelled median (the over-sweep a find
costs, which the planner trades against rate). The clocks are one session's
on a desktop GPU whose rate moves with ambient load, and they are model
medians: budget 1.5-2x, which is this repository's record on first
occurrences. A line rate counted over part of a segment is a launch count
times the segment's line per launch, not a measured line.

| filter | plan p1 | segment / median | device, p/s | candidates/s | survivors/s | host, core-s/s | the model's median over the rate (and Q3) |
|---|---|---|---|---|---|---|---|
| A257466 n = 16 | {5..23,29,43} x 160, 2^16 | 0.038 | 4.86e15 | 5.0e12 | 48,069 | 0.56 | **0.24 s** (0.8 s) |
| A257466 n = 17 | {5..23,29,43,47} x 160, 2^16 | 0.079 | 7.54e15 | 5.5e12 | 27,624 | 0.31 | **3.5 s** (11 s) |
| A257466 n = 18 | {5..23,29,37,43,47} x 160, 2^15 | 0.13 | 1.07e16 | 5.6e12 | 53,843 | 0.51 | **55 s** (2.8 min) |
| A257466 n = 19 | {5..37,43,47} x 160, 2^15 | 0.17 | 1.44e16 | 5.7e12 | 30,966 | 0.34 | **16 min** (50 min) |
| A257466 n = 20 | {5..47} x 160, 2^15 | 0.26 | 1.89e16 | 5.4e12 | 16,712 | 0.19 | **5.6 h** (16.6 h) |
| A257466 n = 21 | {5..53} x 160 wide, 2^14 | 0.53 | 2.60e16 | 5.4e12 | 46,453 | 0.45 | **4.4 days** (12.8 days) |
| A257466 n = 22 | {5..53} x 224 wide, 2^14 | 0.025 | 2.86e16 | 5.9e12 | 23,027 | 0.24 | **117 days** |
| A257467 n = 15 | {5..37} x 160, 2^17 | 0.62 | 2.14e15 | 4.1e12 | 82,926 | 1.07 | **0.9 s** (2.3 s) |
| A257467 n = 16 | {5..37} x 160, 2^17 | 0.024 | 2.37e15 | 4.5e12 | 32,815 | 0.37 | **21 s** (53 s) |
| A257467 n = 17 | {5..37,47} x 160, 2^17 | 0.041 | 3.29e15 | 4.5e12 | 17,172 | 0.18 | **6.9 min** (17 min) |
| A257467 n = 18 | {5..37,43,47} x 160, 2^16 | 0.056 | 4.54e15 | 4.6e12 | 28,126 | 0.32 | **2.6 h** (6.4 h) |
| A257467 n = 19 | {5..47} x 160, 2^16 | 0.075 | 6.03e15 | 4.7e12 | 15,546 | 0.17 | **2.5 days** (6.1 days) |
| A257467 n = 20 | {5..47} x 160, 2^15 | 0.0024 | 6.40e15 | 4.9e12 | 27,521 | 0.30 | **74 days** |
| A258035 n = 11 | {5,7,11,13,19,23} x 160, 2^20 | 0.14 | 1.97e12 | 1.1e10 | 192 | 0.04 | **under 0.01 s** |
| A258035 n = 12 | {5..23} x 160, 2^19 | 0.10 | 2.68e13 | 9.6e10 | 2,232 | 0.13 | **0.01 s** |
| A258035 n = 13 | {5..29} x 160, 2^18 | 0.12 | 6.84e14 | 1.7e12 | 48,441 | 1.35 | **0.01 s** |
| A258035 n = 14 | {5..31} x 160, 2^17 | 0.16 | 2.21e15 | 3.9e12 | 117,060 | 1.94 | **0.09 s** |
| A258035 n = 15 | {5..37} x 160, 2^16 | 0.21 | 3.76e15 | 4.6e12 | 161,069 | 1.73 | **1.5 s** (3.9 s) |
| A258035 n = 16 | {5..41} x 160, 2^17 | 0.31 | 5.29e15 | 4.8e12 | 30,540 | 0.34 | **30 s** (75 s) |
| A258035 n = 17 | {5..41,47} x 160, 2^16 | 0.48 | 7.53e15 | 4.9e12 | 46,340 | 0.54 | **10.5 min** (26 min) |
| A258035 n = 18 | {5..41,47} x 224, 2^16 | 0.021 | 8.24e15 | 5.4e12 | 19,314 | 0.22 | **5.1 h** (12.5 h) |
| A258035 n = 19 | {5..41,47,53} x 145, 2^15 | 0.022 | 1.04e16 | 4.9e12 | 34,934 | 0.38 | **5.5 days** (13.5 days) |

("{5..37,43,47}" is every prime from 5 to 37, then 43 and 47: the wheel is
the greedy subset by value, and a prime it declines is sieved instead.)

The device runs 4.5-5.9e12 candidates a second wherever a segment is more
than a launch. The three families differ in LINE rate at the same index
because their wheels differ: every squared primorial from prime(n) >= q is
0 modulo q, the residue p itself already kills, so A257467's primes kill
fewer classes and its wheel keeps about twice the line A257466's does
(6.0e15 against 1.4e16 p/s at n = 19). The host figures are what the pool
is sized from at runtime (ceil(need x 2) workers, ramped): one to four
workers everywhere here, and one or two at every filter that lasts more
than a minute. A258035's openings at n = 11-13 are launch-bound (a
millisecond a launch on a wheel of a few thousand residues) and cost
hundredths of a second; their line rate is not a meaningful number.

**The acceptance test (rule 5g) was the campaigns themselves**, each
started fresh by the owner with no flags; the section below reads them
against this table. What remains unmeasured is noted there.

## The campaigns against this table (2026-10-05 to 2026-10-08)

One campaign per family, no flags. A find is confirmed when its segment
closes, so each rate is the line from the filter's first boundary to the
end of the find's segment over the leg's wall clock, the build, the pool's
sizing and the verification included (RESULTS.md, "The campaigns against
their benchmarks", has every leg).

| filter | priced above | the campaign | ratio |
|---|---|---|---|
| A257466 n = 18 | 1.07e16 p/s | 1.04e16 p/s over 74 s (10 segments) | 0.97 |
| A257466 n = 19 | 1.44e16 p/s | 1.42e16 p/s over 5.6 min (2 segments) | 0.99 |
| A257466 n = 20 | 1.89e16 p/s | 2.03e16 p/s over 80.6 min (1 segment) | 1.08 |
| A257467 n = 17 | 3.29e15 p/s | 3.23e15 p/s over 2.6 min (9 segments) | 0.98 |
| A257467 n = 18 | 4.54e15 p/s | 4.72e15 p/s over 3.95 h (28 segments) | 1.04 |
| A257467 n = 19 | 6.03e15 p/s | 6.2e15 p/s over ~17.7 h on the campaign's clock (4 segments; 4.05e15 on 27 h of wall clock, nine of them not running) | 1.03 |
| A258035 n = 17 | 7.53e15 p/s | 7.68e15 p/s over 24.8 min (5 segments) | 1.02 |
| A258035 n = 18 | 8.24e15 p/s | 8.41e15 p/s over 14.17 h (134 segments) | 1.02 |

Every filter swept whole that lasted more than a minute ran at 0.97–1.08×
its price, on three families, three wheels and segments of one to 134: the
segment loop's wall clock is the device's time at every filter a campaign
spends its hours in, and the pool bound nowhere. The filters of seconds
(A257466 n = 16–17, A257467 n = 15–16, A258035 n = 11–16) are the engine's
build, the pool's sizing and the exception zone, not a rate, and the two
stopped filters (A257466 n = 21, A258035 n = 19) swept 1.4% and 2.3% of a
segment, too little to read. Not in the table and owed before a resume
(rule 5g): a frozen shape at each live filter (A257466 n = 21, A257467
n = 20, A258035 n = 19 — priced above, fingerprinted nowhere), and a paired
sweep of the planner's wheel at A258035's n = 19, whose 145-period window
on the wheel to 53 was confirmed by measurement at A257466's n = 21 only.
