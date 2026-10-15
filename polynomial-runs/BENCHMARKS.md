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
| 2026-10-08 | **v2** / p1: the queue-overflow fallback out of line and the queue margin re-ranked on the compiled footprint, from the Nsight Compute profile (OPTIMIZATION_LOG.md round 2); all seven fingerprints reproduced | **71,289** | 51,448 | 122,113 | 195,971 | 57,622 | 9,115 | 42.1 |
| 2026-10-15 | v2 / p1, unchanged: the battery at the pause, after the campaigns (RESULTS.md); all seven fingerprints reproduced | **69,871** | 22,781 | 125,207 | 214,295 | 29,677 | 8,985 | 48.5 |

The four campaign shapes are a single launch each, so a reading is mostly
launch overhead and moves between runs; the fingerprints do not move at
all. Round 1's change is worth 1.05–1.12 at the filters a campaign spends
its hours in (paired, interleaved; the log), which the one-launch shapes
cannot resolve either way — the two ledger rows differ by ambient load as
much as by the change. Round 2's is worth 1.05–1.06 at the day-long
filters (paired, interleaved, an A/A arm alongside; the log) and is
likewise invisible here: the SCORE shape read 0.38 of its last row in one
battery and 1.00 in the next, and 7.1–7.5×10¹⁶ p/s on both engines in six
interleaved readings of its own method.

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
| A165234 n = 22 (live at the pause) | {5..23,37},{29,31,41},{43,47,53} | 2^14 | 256 | wide |
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
| A347537 n = 22 (live at the pause) | {5..17,23,37,41},{19,29,31},{43,47,53} | 2^14 | 256 | wide |

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
| A165234 n = 16 | {5..37} × 256, narrow, 2^15, (8, 1) | 0.31 | 7.35e16 | 6.2e12 | 256,222 | 2.38 | **0.08 s** |
| A165234 n = 17 | {5..41} × 256, narrow, 2^16, (16, 1) | 0.44 | 1.43e17 | 6.8e12 | 51,393 | 0.47 | **1.3 s** |
| A165234 n = 18 | {5..43} × 256, narrow, 2^16, (16, 1) | 0.58 | 2.66e17 | 6.7e12 | 27,479 | 0.32 | **22 s** |
| A165234 n = 19 | {5..47} × 128, narrow, 2^15, (16, 2) | 0.38 | 4.50e17 | 5.8e12 | 44,107 | 0.47 | **7.7 min** |
| A165234 n = 20 | {5..53} × 256, wide, 2^15, (16, 2) | 1.13 | 9.46e17 | 6.7e12 | 28,877 | 0.29 | **2.2 h** |
| A165234 n = 21 | {5..53} × 256, wide, 2^14, (16, 2) | 0.03 | 1.26e18 | 7.6e12 | 49,852 | 0.48 | **2.7 days** |
| A230663 n = 16 | {5..37} × 256, narrow, 2^15, (16, 1) | 0.57 | 5.66e16 | 6.7e12 | 270,628 | 2.37 | **0.06 s** |
| A230663 n = 17 | {5..41} × 256, narrow, 2^16, (16, 1) | 0.81 | 1.03e17 | 6.7e12 | 50,802 | 0.52 | **0.9 s** |
| A230663 n = 18 | {5..43} × 256, narrow, 2^16, (16, 1) | 0.84 | 2.15e17 | 6.7e12 | 27,480 | 0.33 | **19 s** |
| A230663 n = 19 | {5..47} × 128, narrow, 2^15, (16, 2) | 0.61 | 3.34e17 | 5.7e12 | 42,558 | 0.43 | **6.5 min** |
| A230663 n = 20 | {5..53} × 128, wide, 2^15, (16, 2) | 0.89 | 6.15e17 | 5.8e12 | 24,722 | 0.29 | **2.1 h** |
| A230663 n = 21 | {5..53} × 256, wide, 2^14, (16, 2) | 0.05 | 9.20e17 | 7.7e12 | 50,371 | 0.50 | **2.1 days** |
| A092120 n = 16 | {5..41} × 256, narrow, 2^16, (16, 1) | 0.44 | 1.37e17 | 6.5e12 | 48,814 | 0.49 | **1.3 s** |
| A092120 n = 17 | {5..43} × 256, narrow, 2^16, (16, 1) | 0.58 | 2.70e17 | 6.8e12 | 28,015 | 0.34 | **21 s** |
| A092120 n = 18 | {5..47} × 128, narrow, 2^15, (16, 2) | 0.38 | 4.48e17 | 5.8e12 | 44,122 | 0.44 | **7.8 min** |
| A092120 n = 19 | {5..53} × 256, wide, 2^15, (16, 2) | settled (a(19) = 163) | 9.44e17 | 6.7e12 | 28,576 | 0.28 | — |
| A092120 n = 20 | {5..53} × 256, wide, 2^14, (16, 2) | 0.03 | 1.24e18 | 7.5e12 | 49,758 | 0.47 | **2.7 days** |
| A092120 n = 21 | {5..53} × 256, wide, 2^14, (16, 2) | 0.001 | 1.43e18 | 7.7e12 | 19,647 | 0.21 | **91 days** |
| A347537 n = 16 | {5..37} × 256, narrow, 2^16, (16, 1) | settled (a(16) known) | 1.00e17 | 5.1e12 | 144,417 | 1.50 | — |
| A347537 n = 17 | {5..37,43} × 256, narrow, 2^17, (16, 1) | 0.59 | 2.05e17 | 5.7e12 | 30,193 | 0.31 | **0.7 s** |
| A347537 n = 18 | {5..43} × 256, narrow, 2^16, (16, 1) | 0.85 | 3.53e17 | 5.8e12 | 44,193 | 0.52 | **11 s** |
| A347537 n = 19 | {5..37,43,47,53} × 128, narrow, 2^16, (16, 2) | 0.70 | 6.07e17 | 5.0e12 | 21,208 | 0.24 | **4.0 min** |
| A347537 n = 20 | {5..53} × 256, wide, 2^15, (16, 2) | 1.32 | 1.42e18 | 5.9e12 | 47,590 | 0.48 | **1.2 h** |
| A347537 n = 21 | {5..53} × 256, wide, 2^15, (16, 2) | 0.04 | 1.97e18 | 6.4e12 | 20,205 | 0.23 | **1.4 days** |

("{5..37,43}" is every prime from 5 to 37 and then 43: the wheel is the
greedy subset by value, and a prime it declines is sieved instead.) The
device runs 5.0–7.7e12 candidates a second; the families differ in LINE
rate at the same index because their kill sets differ, and the 128-period
filters run 0.8–0.9 of the candidate rate of the 256-period ones (the
narrow record clamps a wider window there; A230663 n = 20 takes 128 for
the segment, 0.89 of a median against 1.78). The host needs 0.2–0.5 of a
core at every filter past a minute (one worker, ramped), 1.5–2.4 at the
two cheapest openings, which last well under a second. The device
columns were re-read on engine v2 (2026-10-08, one second of launches a
filter; the host column is round 1's, that path did not change): the
day-long filters read 1.02–1.07 of round 1's readings, the rest within the
±5% that one-second readings scatter — the paired ratios in the log (1.05
at A165234 n = 21 and A092120 n = 20, 1.06 at A347537 n = 21, with an A/A
arm alongside) are the measurement of the change.

## The campaigns against these prices, and the live filters at the pause

The four campaigns of 2026-10-08 to 10-15 ran with no flags. Read from the
ledger timestamps and the checkpoints (RESULTS.md, "The campaigns against
their benchmarks", has the table and the method), **every filter they swept
whole for more than two minutes ran at 0.99–1.03× its device price above**
on the campaign's own clock: A165234 n = 19 1.02, n = 20 and 22 together
1.01; A230663 n = 19 1.03; A092120 n = 18 1.02, and n = 20 1.02 over the
54% of a segment it swept; A347537 n = 19 0.99, n = 20 1.01, and n = 21
1.03 over 65 segments and 74 hours (2.03×10¹⁸ p/s against 1.97). The
segment loop adds nothing the kernel does not, and the pool never bound.

Two of the filters the campaigns stopped in had never been priced, because
round 1's table ends at n = 21. Read on 2026-10-15 through the engine API,
the planned engine at each family's cursor, warmed, three rounds of 1.5 s
of launches alternated with the n = 21 engine at the same p:

| filter | device, p/s | against n = 21 at the same p | survivors/s |
|---|---|---|---|
| A165234 n = 22 | 1.51e18 | 1.18 [1.17, 1.18] (n = 21 read 1.28e18, priced 1.26e18) | 20,600 |
| A347537 n = 22 | 3.42e18 | 1.69 [1.67, 1.71] (n = 21 read 2.03e18, priced 1.97e18) | 42,200 |

One-second readings, not a frozen shape: a fingerprinted shape at each live
filter is still owed (below).

## What rounds 1 and 2 measured, and what is still owed (rule 5g)

Measured on 2026-10-08 through the engine API (OPTIMIZATION_LOG.md rounds
1 and 2; method there): the window width and block shape at A165234
n = 18 and n = 21, the planner's wheel against its neighbours at A347537
n = 19, the depth constants, sieve depth and launch budget at A165234
n = 21; then Nsight Compute on the 24- and 29-prime windows at A165234 and
A347537 n = 21 before and after engine v2, and the two levers it found
(the fallback out of line, the seventh block) paired at A165234 n = 21,
A092120 n = 20 and A347537 n = 21. The per-filter price table is the
section above.

Still owed before a resumed campaign is offered (the acceptance test's
substance — every filter at its price, the pool not binding — was read off
the four campaigns above; their first `[STATUS]` lines were not kept):

* a paired A/B of the planner's wheel against its neighbours at the OTHER
  day-long filters (A230663 n = 21, A092120 n = 20–21, A347537 n = 21) and
  now at the live n = 22 filters — every one of them plans the same full
  wheel to 53 at 256 periods on the wide record that A165234 n = 21 does,
  and the planner's own model puts the wheel to 47 at 1.3–1.5x the clock
  there, so the measurement at A165234 n = 21 is expected to carry, but it
  has not been repeated;
* a frozen, fingerprinted shape at each live filter: A165234 n = 22,
  A230663 n = 21, A092120 n = 20, A347537 n = 22.

The same engine measured 2.8×10¹⁷ m/s at n = 19 and 6.3×10¹⁷ m/s at n = 20
on primorial-ladders' A145743 (m + 4k², the same kill-set regime); here
A165234 runs 2.7×10¹⁷ p/s at n = 18 and 1.26×10¹⁸ p/s at n = 21.
