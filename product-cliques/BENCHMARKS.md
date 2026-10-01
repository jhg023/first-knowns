# BENCHMARKS — product-cliques

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all five frozen shapes reproduce their work fingerprint (survivor count + xor
of the surviving candidates). The rate is end-to-end **line of the candidate
a(n) per second** (a(n)-line/s), and the published term is the candidate
itself, so there is nothing to multiply by.

Five shapes because a launcher owes a shape at every opening it has
(CLAUDE.md 5g), and here a family has exactly **one** opening: its open
index. The filter after it does not exist until a term is found. So there
are two campaign shapes — one per family, each the planned configuration at
that family's open index — and three anchors.

## The ledger

| date | engine / plan | SCORE | S219761 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|
| 2026-09-29 | v1 / p2 (clique-ladders' v1 and planner, the residue lists sized from the forms' degrees) | **11,591** | 734 | 5,422 | 2,812 | 4.50 |
| 2026-09-29 | v2 / p3 (round 1: the pairs window, live words in registers, packed round reductions, deeper window; plans re-fit to the new width curve) | **13,932**† | 827† | 6,518 | 3,073 | 3.08 |
| 2026-10-01 | the same engine, read on the day the finds were written up (the hunt stopped) | 12,996 | 823 | 7,151 | 3,078 | 4.29 |

(in units of 10¹² a(n)-line/s: SCORE is 1.39e16 a(n)-line/s, 2.8e12
candidates a second.) A campaign shape is a few tenths of a second, so a
single reading moves ~10% between runs; the fingerprints do not move at all.
The 2026-10-01 row is one reading on an unchanged tree, every gate green and
all five fingerprints reproduced, with a CPU-only survey running beside it;
SCORE read 0.93× the 2026-09-29 figure and SCORE2L 1.10×, inside that
spread.

† RE-FROZEN SHAPES: both campaign shapes moved from 224 and 128 periods to
the 160 that p3 plans at both openings (same wheel, depth, class and
residues), so SCORE and S219761 are not comparable across the two rows.
Before re-freezing, v2 reproduced all five v1 fingerprints bit for bit at
the v1 windows. The anchors compare directly, but a single reading moves
~10% between runs, and SCORE9 far more (8.1 million survivors: it is
host-bound, and read 4.35 and 3.08 on identical code the same afternoon);
PAIRED on the same shapes, SCORE2L and SCORE1L read 1.20–1.30x and 1.09x and
SCORE9 1.005. What round 1 is worth is a clock at each filter, in
the table below and in OPTIMIZATION_LOG.md round 1 (1.27–1.46x).

## The shapes

| shape | family | n | class | wheel | sieve | window | fingerprint |
|---|---|---|---|---|---|---|---|
| SCORE | A034881 | 16 | 0 (mod 6) | {5..23},{29,31},{37} | 2^17 | the whole 160-period segment at period 1 (23 third-level residues) | 10038 / 248427346659006 |
| S219761 | A219761 | 12 | 0 (mod 6) | {5..23},{29} | 2^20 | the whole segment at period 1 (160-period windows batched to 24,000 periods) | 12684 / 83794772919816 |
| SCORE2L | A034881 | 15 | dense line | (23],(37] | 65536 | 240 periods from 94334 | 128075 / 701845450336393192 |
| SCORE1L | A034881 | 15 | dense line | ≤ 23 | 65536 | the SAME absolute window, 33263× as many periods | 128075 / 701845450336393192 |
| SCORE9 | A219761 | 9 | dense line | ≤ 13 | 4096 | 4e8 periods from 3330003 | 8133377 / 13567447286892 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint — a CRT-lift bug shows
up inside the benchmark rather than as a wrong answer months later. SCORE9
is survivor-heavy (8.1 million survivors) and carries the quadratic form, so
it weighs the survivor path where the others weigh line.

The campaign shapes name their wheel, class, depth, window and launch
decomposition explicitly rather than asking the planner, so a tuning pass
cannot move a benchmark's window — and `_families_stay_apart` (selftest)
fails if a shape and the campaign's plan at that opening ever disagree, so a
*planner* change cannot leave them behind either. **A find does not move a
fingerprint**: a shape names its index, and the form list of an index never
changes once it exists. What a find does is open a *new* filter, and rule 5g
then owes a shape at it.

All five were frozen on 2026-09-29, after the GPU/CPU parity gate G9 passed
on 24 populated windows (238,530 survivors). The two campaign shapes were
re-frozen the same day at the 160-period window planner p3 takes at both
openings (they were 224 and 128 periods, fingerprints 13989 /
1591770134300866 and 12654 / 83679488777088 — both reproduced by engine v2
before the move); the new fingerprints were computed by the v2 and the v1
code paths alike.

## Every opening, and the filters after it, priced (CLAUDE.md 5c and 5g)

Engine v2, planner p3 (OPTIMIZATION_LOG.md round 1), through the engine
API: real launches swept and timed at the modelled median, their survivors
counted, 1,500 of them classified by the launcher's own `sprp_run`, and the
model's expected line to a *confirmed* find over the measured rate. Rows
marked * are on STAND-IN filters (the model's stand-in terms registered in a
scratch process only): the filter a real find will open is planned from the
real term the moment it lands, and will differ. The last column is the
same quantity for v1 / p2, measured the same way (paired, round 1) where it
was, and from the table this one replaced otherwise.

| filter | plan p3 | segment / median | device, a(n)-line/s | host | expected clock to a confirmed find | v1 / p2 |
|---|---|---|---|---|---|---|
| A034881 n = 16 | to 37 × 160, 2^17 | 0.02 | 1.7e16 (SCORE) | 1.8 core-s/s | 4 s | 5 s |
| A034881 n = 17* | to 41 × 160, 2^17 | 0.05 | 3.1e16 | 1.2 | 65 s | 97 s |
| A034881 n = 18* | to 43 × 160, 2^17 | 0.06 | 5.0e16 | 0.47 | 25 min | 34 min |
| A034881 n = 19* | to 53 × 160 (157 live), 2^17 | 0.07 | 8.1e16 | 0.25 | **10.5 h** | 15.3 h |
| A034881 n = 20* | to 47 × 160, 2^16 | < 0.01 | 1.0e17 | 0.33 | 364 h | 543 h |
| A219761 n = 12 | to 29 × 160, 2^20 | 0.76 | 3.6e14 (S219761) | 1.1 | 10 ms | < 1 s |
| A219761 n = 13* | to 37 × 160, 2^20 | 0.82 | 2.4e15 | 2.3 | 0.05 s | 0.3 s |
| A219761 n = 14* | to 41 × 160, 2^19 | 1.00 | 7.5e15 | 2.4 | 0.5 s | 0.7 s |
| A219761 n = 15* | to 41 × 160, 2^18 | 0.70 | 1.7e16 | 1.4 | 9.5 s | 13 s |
| A219761 n = 16* | to 47 × 160, 2^17 | 0.86 | 2.8e16 | 2.2 | 3.8 min | 4.9 min |
| A219761 n = 17* | to 47 × 160, 2^18 | 0.75 | 5.5e16 | 0.40 | **1.5 h** | 2.0 h |
| A219761 n = 18* | to 47 × 160, 2^17 | 0.02 | 8.0e16 | 0.59 | **39 h** | 55 h |
| A219761 n = 19* | to 47 × 160, 2^16 | < 0.01 | 1.0e17 | 0.66 | 1,330 h | 2,070 h |

The device runs 3.1–4.6e12 candidates a second wherever a segment is tens of
launches (2.2–3.0e12 on v1); the filters whose whole segment is one to four
launches (A219761 n = 12 to 14) are launch-bound and cost under a second. The
host figures are what a pool is sized from at runtime (ceil(need × 2)
workers, ramped): a worker or two at every filter that runs for hours, up to
five for the seconds A219761 n = 13 to 16 last (a classification there is
24–47 µs, a(n)² + 1 being twice as wide; A034881's is 13–17 µs).

**What the campaigns actually ran at** (RESULTS.md "The campaigns against
their benchmarks"): the line from a(n−1) to a(n) over each long leg's wall
clock was 5.5e16 a(n)-line/s at A034881 n = 18 against 5.0e16* above, 9.0e16
at A034881 n = 19 against 8.1e16*, and 5.8e16 at A219761 n = 18 against
8.0e16*. The real A219761 n = 18 filter planned the wheel to 53 without 43,
where its stand-in had planned the full wheel to 47, and its leg ran at
0.72× the stand-in's price. That gap is not yet measured. The live filters,
A034881 n = 20 and A219761 n = 19, have no frozen shape and no measured
price yet. Both are owed before either family is resumed (rule 5g).
