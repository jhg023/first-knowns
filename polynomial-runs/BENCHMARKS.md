# BENCHMARKS — polynomial-runs

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all seven frozen shapes reproduce their work fingerprint (survivor count +
xor of the surviving terms). The rate is end-to-end **line of the term per
second** — p/s on all four entries — and the published term is the swept
integer itself, so there is nothing to multiply by.

Seven shapes because a launcher owes a shape at every opening it has
(CLAUDE.md 5g): four campaign shapes, one per family at its lowest open
index, each the planned configuration there, and three anchors.

## The ledger

| date | engine / plan | SCORE | S230663 | S092120 | S347537 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|---|---|
| 2026-10-08 | v1 (primorial-runs' engine v2, taken whole) / p1, first reading, 160-period campaign shapes | **64,817** | 52,972 | 137,567 | 197,601 | 56,599 | 9,579 | 53.4 |
| 2026-10-08 | v1 / p1 with round 1's width table and block-shape rows; the four campaign shapes re-frozen at 256 periods (OPTIMIZATION_LOG.md round 1); all seven fingerprints reproduced | **71,565** | 56,185 | 127,450 | 206,673 | 53,205 | 9,792 | 51.2 |

The four campaign shapes are a single launch each, so a reading is mostly
launch overhead and moves between runs; the fingerprints do not move at
all. Round 1's change is worth 1.05–1.12 at the filters a campaign spends
its hours in (paired, interleaved; the log), which the one-launch shapes
cannot resolve either way — the two ledger rows differ by ambient load as
much as by the change.

## The shapes

| shape | family | n | class | wheel | sieve | window | fingerprint |
|---|---|---|---|---|---|---|---|
| SCORE | A165234 | 16 | 5 (mod 6) | {5..29},{31},{37} | 2^15 | all 21 third-level residues of the segment at period 1, 256 periods | 6521 / 1601343003530803 |
| S230663 | A230663 | 16 | 1 (mod 6) | {5..23},{29,31},{37} | 2^15 | all 21 third-level residues of the segment at period 1, 256 periods | 9120 / 682995423446552 |
| S092120 | A092120 | 16 | 1 (mod 6) | {5..29},{31,37},{41} | 2^16 | all 24 third-level residues of the segment at period 1, 256 periods | 27481 / 11674479549184331 |
| S347537 | A347537 | 17 | 1 (mod 6) | {5..29},{31,37},{43} | 2^17 | all 28 third-level residues of the segment at period 1, 256 periods | 12208 / 102828151028243808 |
| SCORE2L | A165234 | 17 | dense line | (23],(37] | 65536 | 240 periods from 94334 | 624 / 3399412268315720 |
| SCORE1L | A165234 | 17 | dense line | ≤ 23 | 65536 | the SAME absolute window, 33263× as many periods | 624 / 3399412268315720 |
| SCORE9 | A092120 | 9 | dense line | ≤ 13 | 4096 | 1e8 periods from 3330003 | 202174 / 3963986673996 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint. SCORE9 is
survivor-heavy, so it weighs the survivor path where the others weigh
line. The campaign shapes name their wheel, class, depth, window and
launch decomposition explicitly rather than asking the planner; the
launcher's selftest fails if a shape and the campaign's plan at that
opening ever disagree.

All seven were frozen on 2026-10-08 on engine v1, after the GPU/CPU parity
gate G9 passed on populated windows; the four campaign shapes were
re-frozen the same day when round 1 moved the planner's window from 160 to
256 periods at every opening (OPTIMIZATION_LOG.md round 1: a deliberate
coverage change, the old fingerprints recorded there). The anchors pin
their own width and did not move.

## The plan at every opening and the filters above it

Planner p1 with round 1's width table and block-shape rows, through the
engine API (2026-10-08). Every filter exists, so these are real plans on
real constants; the wheel is the greedy subset by value, so "{5..29,37}"
is every prime from 5 to 29 and then 37. The wheel is the same at every
filter as before round 1; what moved is the window (256 periods wherever
the record admits it, 128 at the wheel-to-47 filters where a wider window
is clamped to 183 live periods, and 128 in place of 96 at A347537 n = 19).

| filter | wheel (levels) | sieve | window | record |
|---|---|---|---|---|
| A165234 n = 16 | {5..29},{31},{37} | 2^15 | 256 | narrow |
| A165234 n = 17 | {5..29},{31,37},{41} | 2^16 | 256 | narrow |
| A165234 n = 18 | {5..29},{31,37},{41,43} | 2^16 | 256 | narrow |
| A165234 n = 19 | {5..29},{31,37,41},{43,47} | 2^15 | 128 | narrow |
| A165234 n = 20 | {5..23,37},{29,31,41},{43,47,53} | 2^15 | 256 | wide |
| A165234 n = 21 | {5..23,37},{29,31,41},{43,47,53} | 2^14 | 256 | wide |
| A230663 n = 16 | {5..23},{29,31},{37} | 2^15 | 256 | narrow |
| A230663 n = 17 | {5..23},{29,31},{37,41} | 2^16 | 256 | narrow |
| A230663 n = 18 | {5..23},{29,31,37},{41,43} | 2^16 | 256 | narrow |
| A230663 n = 19 | {5..23},{29,31,37},{41,43,47} | 2^15 | 128 | narrow |
| A230663 n = 20 | {5..23,37},{29,31,41},{43,47,53} | 2^15 | 128 | wide |
| A230663 n = 21 | {5..23,37},{29,31,41},{43,47,53} | 2^14 | 256 | wide |
| A092120 n = 16 | {5..29},{31,37},{41} | 2^16 | 256 | narrow |
| A092120 n = 17 | {5..29},{31,37},{41,43} | 2^16 | 256 | narrow |
| A092120 n = 18 | {5..29},{31,37,41},{43,47} | 2^15 | 128 | narrow |
| A092120 n = 20 | {5..23,37},{29,31,41},{43,47,53} | 2^14 | 256 | wide |
| A092120 n = 21 | {5..23,37},{29,31,41},{43,47,53} | 2^14 | 256 | wide |
| A347537 n = 17 | {5..29},{31,37},{43} | 2^17 | 256 | narrow |
| A347537 n = 18 | {5..29},{31,37},{41,43} | 2^16 | 256 | narrow |
| A347537 n = 19 | {5..29},{31,37,43},{47,53} | 2^16 | 128 | narrow |
| A347537 n = 20 | {5..19,29,53},{23,31,37},{41,43,47} | 2^15 | 256 | wide |
| A347537 n = 21 | {5..17,23,29,41},{19,31,37},{43,47,53} | 2^15 | 256 | wide |

## Every opening, and the filters after it, priced

Engine v1 with round 1's planner table and shape rows, through the engine
API (2026-10-08, after the change): the planned engine at each filter,
warmed, then about a second of real launches timed with the device
synchronised, survivors counted, a 2,000-survivor sample classified on one
core with the launcher's own run reader, and the model's median for that
index (from the bottom of the line) divided by the measured rate. The
clocks are one session's on a desktop GPU and they are model medians:
budget 1.5–2× (this repository's record on first occurrences; primorial-
runs' came early). "segment / median" is the planned segment's line over
the modelled median. A filter the entries settle in a comment (A092120
n = 19, A347537 n = 16) is priced because the campaign passes through it,
but nothing is hunted there.

| filter | plan p1 (wheel × window, record, sieve, block shape) | segment / median | device, p/s | candidates/s | survivors/s | host, core-s/s | the model's median over the rate |
|---|---|---|---|---|---|---|---|
| A165234 n = 16 | {5..37} × 256, narrow, 2^15, (8, 1) | 0.31 | 7.68e16 | 6.5e12 | 263,423 | 2.38 | **0.08 s** |
| A165234 n = 17 | {5..41} × 256, narrow, 2^16, (16, 1) | 0.44 | 1.40e17 | 6.6e12 | 48,840 | 0.47 | **1.3 s** |
| A165234 n = 18 | {5..43} × 256, narrow, 2^16, (16, 1) | 0.58 | 2.65e17 | 6.6e12 | 27,093 | 0.32 | **22 s** |
| A165234 n = 19 | {5..47} × 128, narrow, 2^15, (16, 2) | 0.38 | 4.43e17 | 5.7e12 | 43,790 | 0.47 | **7.9 min** |
| A165234 n = 20 | {5..53} × 256, wide, 2^15, (16, 2) | 1.13 | 8.84e17 | 6.3e12 | 26,971 | 0.29 | **2.3 h** |
| A165234 n = 21 | {5..53} × 256, wide, 2^14, (16, 2) | 0.03 | 1.18e18 | 7.2e12 | 46,654 | 0.48 | **2.8 days** |
| A230663 n = 16 | {5..37} × 256, narrow, 2^15, (16, 1) | 0.57 | 5.66e16 | 6.6e12 | 268,380 | 2.37 | **0.06 s** |
| A230663 n = 17 | {5..41} × 256, narrow, 2^16, (16, 1) | 0.81 | 1.02e17 | 6.7e12 | 49,804 | 0.52 | **0.9 s** |
| A230663 n = 18 | {5..43} × 256, narrow, 2^16, (16, 1) | 0.84 | 2.13e17 | 6.6e12 | 26,907 | 0.33 | **19 s** |
| A230663 n = 19 | {5..47} × 128, narrow, 2^15, (16, 2) | 0.61 | 3.37e17 | 5.8e12 | 42,877 | 0.43 | **6.4 min** |
| A230663 n = 20 | {5..53} × 128, wide, 2^15, (16, 2) | 0.89 | 6.05e17 | 5.7e12 | 24,082 | 0.29 | **2.2 h** |
| A230663 n = 21 | {5..53} × 256, wide, 2^14, (16, 2) | 0.05 | 8.68e17 | 7.3e12 | 47,652 | 0.50 | **2.2 days** |
| A092120 n = 16 | {5..41} × 256, narrow, 2^16, (16, 1) | 0.44 | 1.39e17 | 6.6e12 | 48,919 | 0.49 | **1.3 s** |
| A092120 n = 17 | {5..43} × 256, narrow, 2^16, (16, 1) | 0.58 | 2.63e17 | 6.6e12 | 26,565 | 0.34 | **22 s** |
| A092120 n = 18 | {5..47} × 128, narrow, 2^15, (16, 2) | 0.38 | 4.42e17 | 5.7e12 | 42,822 | 0.44 | **7.9 min** |
| A092120 n = 19 | {5..53} × 256, wide, 2^15, (16, 2) | settled (a(19) = 163) | 9.11e17 | 6.5e12 | 27,685 | 0.28 | — |
| A092120 n = 20 | {5..53} × 256, wide, 2^14, (16, 2) | 0.03 | 1.18e18 | 7.2e12 | 46,823 | 0.47 | **2.8 days** |
| A092120 n = 21 | {5..53} × 256, wide, 2^14, (16, 2) | 0.001 | 1.45e18 | 7.8e12 | 19,821 | 0.21 | **90 days** |
| A347537 n = 16 | {5..37} × 256, narrow, 2^16, (16, 1) | settled (a(16) known) | 9.71e16 | 4.9e12 | 142,624 | 1.50 | — |
| A347537 n = 17 | {5..37,43} × 256, narrow, 2^17, (16, 1) | 0.59 | 2.06e17 | 5.7e12 | 29,917 | 0.31 | **0.7 s** |
| A347537 n = 18 | {5..43} × 256, narrow, 2^16, (16, 1) | 0.85 | 3.56e17 | 5.9e12 | 44,355 | 0.52 | **11 s** |
| A347537 n = 19 | {5..37,43,47,53} × 128, narrow, 2^16, (16, 2) | 0.70 | 6.23e17 | 5.1e12 | 22,105 | 0.24 | **3.9 min** |
| A347537 n = 20 | {5..53} × 256, wide, 2^15, (16, 2) | 1.32 | 1.32e18 | 5.5e12 | 44,656 | 0.48 | **1.3 h** |
| A347537 n = 21 | {5..53} × 256, wide, 2^15, (16, 2) | 0.04 | 1.93e18 | 6.2e12 | 19,500 | 0.23 | **1.4 days** |

("{5..37,43}" is every prime from 5 to 37 and then 43: the wheel is the
greedy subset by value, and a prime it declines is sieved instead.) The
device runs 5.1–7.8e12 candidates a second; the families differ in LINE
rate at the same index because their kill sets differ, and the 128-period
filters run 0.8–0.9 of the candidate rate of the 256-period ones (the
narrow record clamps a wider window there; A230663 n = 20 takes 128 for
the segment, 0.89 of a median against 1.78). The host needs 0.2–0.5 of a
core at every filter past a minute (one worker, ramped), 1.5–2.4 at the
two cheapest openings, which last well under a second.

## What round 1 measured, and what is still owed (rule 5g)

Measured on 2026-10-08 through the engine API (OPTIMIZATION_LOG.md round
1; method there): the window width and block shape at A165234 n = 18 and
n = 21, the planner's wheel against its neighbours at A347537 n = 19, and
the depth constants, sieve depth and launch budget at A165234 n = 21. The
per-filter price table is the section below.

Still owed before a campaign's rate is read as a measurement:

* a paired A/B of the planner's wheel against its neighbours at the OTHER
  day-long filters (A230663 n = 21, A092120 n = 20–21, A347537 n = 21) —
  every one of them plans the same full wheel to 53 at 256 periods on the
  wide record that A165234 n = 21 does, and the planner's own model puts
  the wheel to 47 at 1.3–1.5x the clock there, so the measurement at
  A165234 n = 21 is expected to carry, but it has not been repeated;
* Nsight Compute on this regime's kernel (24-prime windows);
* the no-flags acceptance test, read off the first `[STATUS]` lines of
  each family's campaign.

The same engine measured 2.8×10¹⁷ m/s at n = 19 and 6.3×10¹⁷ m/s at n = 20
on primorial-ladders' A145743 (m + 4k², the same kill-set regime); here
A165234 runs 2.6×10¹⁷ p/s at n = 18 and 1.18×10¹⁸ p/s at n = 21.
