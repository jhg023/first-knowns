# BENCHMARKS — decimal-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all seven frozen shapes reproduce their work fingerprint (survivor count +
xor of the surviving x). The rate is end-to-end **x-line per second** — the
published term is x itself (A305740's k, A153431's m) — divided by 10^6.
**The SCORE of a commit is the SCORE row**: A305740 at n = 18, the filter
where the days are.

Seven shapes because the plan is per filter: one at each family's opening
filter, one at each family's long leg, and three x-space anchors whose
shapes no planner change can move.

## The ledger

| date | engine | SCORE (A305740 n = 18) | SCORE153 (A153431 n = 17) | SCORE13 | SCORE14 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|---|---|
| 2026-09-24 | round 1 with the first A305740 n = 18 plan (the one that did not reproduce) — OVERCOUNTED | (3,989,061) | — | — | — | — | — | — |
| 2026-09-24 | round 1: tuple window, BIT_SURV .0035, the first MEASURED_PLANS — OVERCOUNTED | (4,174,442) | (9,200,224) | 3,851 | (215,988) | 23,508 | 9,700 | 9.30 |
| 2026-09-24 | exact launch counts; MEASURED_PLANS re-measured on them (the wide record at A305740 n = 18); the campaign shapes re-frozen | 4,390,644 | 9,319,592 | 3,837 | 132,490 | 23,859 | 9,852 | 10.08 |
| 2026-09-24 | the per-block setup on every thread (OPTIMIZATION_LOG.md Measurement 14) | 4,574,567 | 9,410,462 | 4,450 | 135,054 | 24,498 | 10,054 | 9.47 |
| 2026-09-24 | the live words counted as they are written (Measurement 14) | 4,604,978 | 9,556,289 | 4,536 | 136,046 | 24,788 | 10,024 | 10.26 |
| 2026-09-24 | the round-window rows stored word-major (Measurement 14) | 4,669,310 | 9,575,047 | 4,556 | 135,558 | 24,857 | 10,009 | 10.11 |
| 2026-09-24 | the extraction visits only the nonzero words (Measurement 14) | 4,715,490 | 9,696,121 | 4,832 | 138,806 | 24,427 | 10,375 | 10.22 |
| 2026-09-24 | the window depth per filter (.0045 at A305740 n = 18, 19; Measurement 14) | 4,797,071 | 9,664,243 | 4,815 | 138,480 | 23,885 | 10,377 | 10.05 |
| 2026-09-24 | the narrow in-block rounds share the u64 reduction (Measurement 14) | 4,802,120 | 9,863,075 | 4,974 | 141,048 | 24,684 | 10,480 | 10.05 |
| 2026-09-25 | the same engine, read on the day (before the launch-accounting fix) | 4,399,184 | 8,976,311 | 4,603 | 131,945 | 23,118 | 10,075 | 10.09 |
| 2026-09-25 | the launch-counted shapes stop queueing launch L + 1; the wide setup in one step | 5,155,827 | 10,579,870 | 5,003 | 160,905 | 24,376 | 10,410 | 9.63 |
| 2026-09-25 | the same engine, read on the day (before Measurement 16) | 5,090,238 | 10,442,833 | 4,950 | 158,004 | 24,528 | 10,331 | 9.98 |
| 2026-09-25 | **a block walks TBL = 8 t-blocks after one setup; the reservation bit-sliced; the queue entry one packed u32 (Measurement 16)** | **5,309,965** | **10,728,021** | 5,008 | 160,585 | 25,087 | 11,443 | 9.16 |
| 2026-09-28 | the same engine, read on the day (before Measurement 17) | 5,076,644 | 9,724,889 | 4,816 | 151,542 | 23,020 | 11,209 | 8.16 |
| 2026-09-28 | **5 blocks per SM: the x0 table in pairs, the row's words in registers; the overflow fallbacks out of the hot loops; the small-prime tail kernel (Measurement 17)** | **5,889,263** | **11,614,452** | 5,460 | 173,979 | 27,154 | 12,105 | 8.23 |
| 2026-09-29 | the same engine, read on the day the finds were written up (the hunt stopped; see below) | 5,644,766 | 11,057,682 | 5,565 | 178,352 | 29,468 | 12,774 | 9.09 |

(in units of 10^12 x/s: SCORE is 5.89e18 k/s.) **The 2026-09-29 row is
the second of two readings minutes apart on an unchanged tree.** The first
read six of the seven shapes at 0.61–0.77× this one — SCORE 4,330,149,
SCORE153 7,690,012, and the x-space anchors SCORE2L and SCORE1L, which no
engine or plan change can move, at 0.61× and 0.63× (SCORE9, microsecond
launches, read 1.06×) — with the GPU otherwise idle but shared with desktop
applications; a drop across every heavy shape on code that did not change is
the machine, not the engine. Both runs passed every gate and
reproduced all seven fingerprints. The 2026-09-28 rows are
single readings three hours apart on a day other GPU clients moved absolute
rates by up to 10% between runs; the comparable numbers are Measurement 17's
paired ratios against the engine it replaced -- **1.098 at A305740 n = 18,
1.076 at A153431 n = 17, 1.06–1.14 at every campaign filter** -- and on
SCORE9's own shape, interleaved, 1.106 (its two single readings above are
inside its usual swing). The gates behind the last row ran as score.py's
list in two parts (rule 0), then the seven shapes. The 2026-09-25 rows are
single readings an hour apart; the interleaved ratios of Measurement 16 are
the comparable numbers (1.040 on SCORE, 1.024 on SCORE153), and SCORE9's
drop there is its barrier per t-block where a block has almost no work, as
in the 2026-09-24 setup row. **Every launch-counted
reading before 2026-09-25 (SCORE, SCORE153, SCORE14) is UNDERCOUNTED** by
L/(L + 1): the sweep generator runs one launch ahead, so stopping it after
L launches left launch L + 1 on the device and the timer's synchronize
charged it to the work -- 16/17 on SCORE and SCORE153, 8/9 on SCORE14,
measured at 1.061 and 1.122 against the predicted 1.0625 and 1.125
(same engine, old against new work function, interleaved). The fingerprints were right
throughout. The last row's rise over the row before it is that correction
plus the one-step wide setup (1.008x, paired) plus the day's clock: the two
rows are single readings twenty minutes apart. **The parenthesised
readings are overcounted**: `score.py` credited every launch with a full
`cand_per_launch` while the last first-level chunk of each unit is partial,
1.12× too high on those shapes (OPTIMIZATION_LOG.md Measurement 12). The
fingerprints were right throughout. The x-space anchors (SCORE13, SCORE2L,
SCORE1L, SCORE9) are not launch-counted and were never affected. SCORE14's
drop is the new plan's different shape (a different wheel and window), not a
slower engine: at the campaign's own configuration A153431 n = 14 runs 1.035×
the old plan. SCORE9's drop in the last row is real and expected: the
parallel setup adds one barrier per block, which costs where a block has
almost no work (n = 9, microsecond launches; no campaign runs there). The
score harness restarts its sweep on every run, and a
power-capped GPU turns that into several percent from run to run, so a
ledger row is a single reading. **The comparable number is the paired
steady-state ratio at the campaign's own configuration against the inherited
engine and plan, exact counts: about 1.33× at A305740 n = 18 (3.84e18 →
5.11e18 k/s) and 1.27× at A153431 n = 17 (8.30e18 → 1.05e19 m/s).**

## The shapes

| shape | family | n | wheel (levels) | unit | sieve | window | work | fingerprint |
|---|---|---|---|---|---|---|---|---|
| SCORE | A305740 | 18 | {3,23,29,31,47,59},{11,13,43,53},{61,67} (the plan) | 2261 | 262144 | 224, WIDE | 16 launches of (tchunk 19456, nu 1) at period 1000 | 21219 / 633403670445840895464015 |
| SCORE153 | A153431 | 17 | {3,5,11,13,23,29,31},{43,47,59},{61,67} (the plan) | 4522 | 262144 | 256, narrow | 16 launches of (18048, 1) at period 1000 | 8163 / 119430980700175536911810 |
| SCORE13 | A305740 | 13 | {3,11,13,17,19,23,29},{31},{43} (the plan) | 7 | 2^20 | 192, narrow | 40 segments from period 1120 | 126079 / 1240139239024586 |
| SCORE14 | A153431 | 14 | {3,5,11,13,17,19,23,29},{31,43},{47} (the plan) | 14 | 262144 | 256, narrow | 8 launches of (451584, 2) at period 1120 | 30533 / 485706402864992910 |
| SCORE2L | A305740 | 15 | (23],(37] | 1 | 65536 | 224 | 240 periods from 94334 | 15297 / 698556166393375796 |
| SCORE1L | A305740 | 15 | ≤ 23 | 1 | 65536 | 224 | the SAME absolute window, 33263× as many periods | 15297 / 698556166393375796 |
| SCORE9 | A153431 | 9 | ≤ 13 | 1 | 4096 | 224 | 4e8 periods from 3330003 | 3346661 / 4216072310568 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint — a CRT-lift bug shows
up inside the benchmark. The four campaign shapes name their plan
explicitly and `_families_stay_apart` asserts each is exactly what
`MEASURED_PLANS` gives the campaign there, so a planner change must
re-freeze them in the same commit. The earlier campaign shapes are in the
git history with their fingerprints: SCORE 7091 / 13945529258291053458715
(narrow, the 11-prime wheel at 256), SCORE153 21408 /
35389071529342728132182, SCORE14 26320 / 823058254671027244.

## Wall-clock at the measured rates

Steady-state rates of the campaign's own configuration, on exact launch
counts (one continuous sweep; OPTIMIZATION_LOG.md Measurement 12), and the
device time to each term's modelled median from the previous term's:

| filter | x/s | to the median |
|---|---|---|
| A305740 n = 13 / 14 / 15 / 16 / 17 | 5.01e15 / 1.86e16 / 7.64e16 / 4.02e17 / 1.19e18 | < 1 s / 1 s / 10 s / 4 min / 1.7 h |
| **A305740 n = 18** | **5.11e18** | **46 h** (about 7 h less if A153431 a(17) is settled first) |
| A305740 n = 19 | 9.44e18 | 57 days |
| A153431 n = 14 / 15 / 16 | 1.61e17 / 8.65e17 / 2.65e18 | 8 s / 3 min / 72 min |
| **A153431 n = 17** | **1.05e19** | **36 h** |
| A153431 n = 18 | 2.04e19 | 42 days |

These are the rates the table was built with, before Measurements 16 and
17; at the long legs those multiply them by 1.040 × 1.098 (A305740 n = 18)
and 1.024 × 1.076 (A153431 n = 17), paired -- about 5.8e18 k/s and 1.16e19
m/s -- and every "to the median" above shrinks in proportion.

`python score.py`: 26 gates and seven fingerprints in about 2.5 min;
`python launch.py --selftest`: 49/49 in about 245 s (a little longer the first
run after a kernel-source or plan change, when NVRTC compiles every
configuration cold). On 2026-09-28, with other clients on the GPU, the same
battery took ~360 s before Measurement 17 and 339 s after it (cold compiles
included), run in parts; on 2026-09-29, warm, 289 s in three parts (15 / 8 /
26 gates in 39 / 168 / 82 s), 49/49.

**What the campaigns actually ran at** (RESULTS.md "The campaigns against
their benchmarks"): A153431 n = 15 and 16 at 8.4e17 and 2.61e18 m/s against
8.65e17 and 2.65e18 here; A305740 n = 17 at 1.10e18 k/s against 1.19e18;
and A305740's a(18) leg at about 5.2e18 k/s on average over roughly 90
hours, across Measurements 16 and 17 (5.11e18 when it began, SCORE 5.89e18
when it ended).
