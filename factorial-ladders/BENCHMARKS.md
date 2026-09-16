# BENCHMARKS — factorial-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all eight frozen shapes reproduce their work fingerprint (survivor count +
xor of the surviving x). The rate is end-to-end **x-line per second**, and
the published term is x itself, so there is nothing to multiply by.

Eight shapes because the plan is per filter — the kill sets grow with n and
the period the search can afford grows with the modelled median — so one
configuration would measure one filter and say nothing about the next.

## The ledger

| date | engine | SCORE | SCOREP | SCORE16 | SCORE18 | SCORE11 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|---|---|---|
| 2026-09-16 | v1 (inherited) | 125,567 | 125,244 | 79,477 | 171,921 | 724 | 19,439 | 8,137 | 5.8 |
| 2026-09-16 | v2 (2^64 bound: 179-period window; shapes re-frozen) | **164,784** | 150,728 | 104,178 | 227,223 | 485* | 18,996 | 8,091 | 6.05 |
| 2026-09-16 | v3 (the wide record where the wheel demands it; wheel 53 from n = 18; SCORE16/18 re-frozen at the plan) | **163,157** | 163,829 | 82,419** | **257,634** | 723* | 19,126 | 7,109 | 5.41 |

(in units of 10¹² x/s: SCORE is 1.648e17 x/s, 2.51e12 candidates/s. The v1 row's campaign shapes were 64-period segments and are not comparable with v2's 179-period shapes; the paired engine ratio at the campaign's own configuration is 1.194x at n = 17, 1.088x at n = 18 and 1.069x at n = 16, OPTIMIZATION_LOG.md round 2. **SCORE16's v3 shape is a different wheel (43, the plan there) and not comparable with the v2 row; SCORE18's is the wheel to 53 on the wide record against v2's wheel to 47, and the paired engine ratio at n = 18 is 1.19x before the launch budget and 1.43x against v1 with it. The x-space anchors read 0.997 / 0.988 for v3 against v2 when paired; the scored readings moved 10% between runs of the same shape this session. *SCORE11 is 0.04 s of device per run and its single runs span 3x; paired it is unchanged.)

## The shapes

| shape | family | n | wheel | unit | sieve | window | fingerprint |
|---|---|---|---|---|---|---|---|
| SCORE | A177013 | 17 | {5,7,11,13,17,19,23,29,31,37,41,43,47} | 6 | 65536 | 4 third-level residues of the 179-period segment at period 1 | 237557 / 2767396319084044674 |
| SCOREP | A177014 | 17 | same | 6 | 65536 | same | 236826 / 80766670185484481804 |
| SCORE16 | A177013 | 16 | {5..29},{31,37},{41,43} (the plan at n = 16) | 6 | 131072 | 16 residues, 224 periods | 41918 / 3250799516093442686 |
| SCORE18 | A177014 | 18 | {5,7,11,13,17,23,29,31},{19,37,41},{43,47,53} (the plan at n = 18, non-contiguous, WIDE record) | 6 | 65536 | 4 residues, 160 periods | 97259 / 7392165076669389529082 |
| SCORE11 | A177013 | 11 | {5,7,11,13,17,19,23,31} | 6 | 2^20 | 4480 periods from period 1 (W = 6.9e9) | 6008 / 28122740176000 |
| SCORE2L | A177013 | 15 | (23],(37] | 1 | 65536 | 240 periods from 94334 | 13912 / 4097233734626840 |
| SCORE1L | A177013 | 15 | ≤ 23 | 1 | 65536 | the SAME absolute window, 33263× as many periods | 13912 / 4097233734626840 |
| SCORE9 | A177014 | 9 | ≤ 13 | 1 | 4096 | 4e8 periods from 3330003 | 5709215 / 2391121983764 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint — a CRT-lift bug shows
up inside the benchmark rather than as a wrong answer months later.

The campaign shapes follow the plan: SCORE and SCOREP were re-frozen on
2026-09-16 at engine v2's 179-period window (v1's fingerprints, at 64
periods, are in OPTIMIZATION_LOG.md round 2), and SCORE16 and SCORE18 the
same day at engine v3's plan — the wheel to 43 at n = 16 and the wheel to
53 on the wide record at n = 18 (their v2 shapes are in round 3). SCORE11
and the three x-space shapes are the anchors across both changes. The five
campaign shapes pin `pb` (192 at the wheel to 47, where the u64 record
admits 179 periods; 224 at the wheel to 43; 160 at the wheel to 53) and
`nu` — the segment width and the launch decomposition — so that
a tuning sweep of either cannot move the benchmark's own window, and name
their wheel and depth explicitly rather than asking the planner: the
planner's answer is a default optimization is expected to move, and a
benchmark whose window moves with it is not an anchor. G18 checks the
planner still produces exactly these.

## Wall clock at the scored rates

Device only, against the modelled medians (README.md). The campaign's own
rate is the pipeline's — device and host — and is what `[STATUS]` prints.
The scored rates are 10–15% under the harness rates in OPTIMIZATION_LOG.md
Measurement 4 (the shapes are four third-level residues, a fraction of a
segment, so they carry more per-launch overhead than the campaign does).

| filter | wheel, window, record | x/s | median x | to the median | at 2.5× |
|---|---|---|---|---|---|
| n = 11 | {5..23}, 128, narrow | 7.9e14 | 3.4e10 | one segment (< 1 s) | — |
| n = 16 | to 43, 224, narrow | 8.2e16 | 3.1e18 | 38 s (one segment) | 1.6 min |
| n = 17 | to 47, 179, narrow | 1.6e17 | 1.4e20 | **15 min** | 37 min |
| n = 18 | to 53, 160, **wide** | 3.0e17 | 6.0e21 | **5.6 h** | 14 h |
| n = 19 | to 53, 224, **wide** | ~3.8e17 (paired, round 3) | 2.8e23 | 8.5 days | — |

n = 12 to 15 lie between the first two rows: each is seconds. So a night
reaches a(17) on both families, a(18) is most of a day each, and a(19) is
about nine days on the wheel to 53.

## The host side

The pool is sized at runtime from a measurement at the campaign's own
filter, not from a constant. At the full wheel the survivor rates are
62,000–91,000 per second at 12–15 µs each: 0.8–1.4 core-seconds per second,
two or three workers at the ×2 margin. At the opening filter the sieve
ladder's top binds and the measurement reads 137,000/s × 52 µs = 7 cores —
for the quarter of a second that one segment lasts (OPTIMIZATION_LOG.md,
open item 3).
