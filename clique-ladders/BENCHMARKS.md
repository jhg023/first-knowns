# BENCHMARKS — clique-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all nine frozen shapes reproduce their work fingerprint (survivor count + xor
of the surviving x). The rate is end-to-end **x-line per second**, and the
published term is x itself, so there is nothing to multiply by.

Nine shapes because a launcher owes a shape at every opening it has
(CLAUDE.md 5g), and here a family has exactly **one** opening: its open
index. The filter after it does not exist until a term is found. So there
are six campaign shapes — one per family, each the planned configuration at
that family's open index — and three anchors.

## The ledger

| date | engine / plan | SCORE | S103828 | S037100 | S119752 | S119751 | S133761 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-19 | v1 / p1 (factorial-ladders' v3 + the form list as state + the forced-class map) | 52,881 | 141,713 | 31,005 | 12,513 | 19,422 | 94,835 | 10,193 | 4,978 | 4.25 |
| 2026-09-19 | v1 / p1, the block shape following the window's width — **the same nine shapes** | 54,406 | 139,574 | **39,785** | 12,332 | 19,524 | 93,596 | 10,275 | 4,974 | 4.20 |
| 2026-09-19 | v1 / **p2** — five campaign shapes RE-FROZEN at the new plan (below) | **63,037** | 160,248 | 57,272 | 10,487 | 19,664 | 108,699 | 10,046 | 4,968 | 4.18 |
| 2026-09-20 | v1 / p2, round 2: the in-block queues ping-pong (every shape); the rounds in the window's coordinates (WIDE record only -- no shape here is wide, see OPTIMIZATION_LOG.md round 2) | 63,231 | 162,836 | 58,360 | 11,609 | 20,142 | 110,340 | 10,348 | 4,994 | 4.11 |

(in units of 10¹² x/s: SCORE is 6.30e16 x/s.) **Read the third row against
the second only in its last four columns.** The five re-frozen shapes cover
different candidates at a different sieve depth and over four times as many
launches, so their numbers are not ratios of an engine; S119751 and the
three anchors did not move and read flat, which is the comparison across
the re-freeze. The second row is the one that compares engines on fixed
shapes: the block shape is worth 1.28× on the one shape that ran a
32-period window and 1.03× on SCORE (128 periods), and nothing elsewhere
(224-period shapes keep the inherited shape). What the round was worth to
the *campaign* is a clock, not a rate, and it is in the next table and in
OPTIMIZATION_LOG.md round 1. A campaign shape is a few tenths of a second,
so a single reading moves ~10% between runs; the fingerprints do not move
at all.

## The shapes

| shape | family | n | class | wheel | sieve | window | fingerprint |
|---|---|---|---|---|---|---|---|
| SCORE | A093483 | 18 | 2 (mod 6) | {5..29},{31,37},{41} | 2^17 | 16 third-level residues of the 128-period segment at period 1 | 6056 / 45373809339410856 |
| S103828 | A103828 | 19 | 9 (mod 30) | {7..29},{31,37},{41,43} | 2^16 | 16 residues, 224 periods | 10423 / 1622921865908186999 |
| S037100 | A037100 | 19 | 0 (mod 6) | {5..29},{31,37},{41} | 2^16 | 8 residues, 224 periods | 6920 / 16859153692801908 |
| S119752 | A119752 | 15 | 2 (mod 6) | {5..23},{29},{31} | 2^17 | the whole segment (18 residues) at 128 periods | 3948 / 621344468468060 |
| S119751 | A119751 | 15 | 9 (mod 30) | {7..29},{31} | 2^17 | the whole 224-period segment | 3949 / 527123306958529 |
| S133761 | A133761 | 17 | 11 (mod 30) | {7..29},{31,37},{41} | 2^17 | 16 residues, 224 periods | 7122 / 53488743232834886 |
| SCORE2L | A037100 | 15 | x space | (23],(37] | 65536 | 240 periods from 94334 | 59938 / 1037504555151628 |
| SCORE1L | A037100 | 15 | x space | ≤ 23 | 65536 | the SAME absolute window, 33263× as many periods | 59938 / 1037504555151628 |
| SCORE9 | A093483 | 9 | x space | ≤ 13 | 4096 | 4e8 periods from 3330003 | 10505565 / 9428818188514 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint — a CRT-lift bug shows
up inside the benchmark rather than as a wrong answer months later.

The campaign shapes name their wheel, class, depth, window and launch
decomposition explicitly rather than asking the planner, so a tuning pass
cannot move a benchmark's window — and `_families_stay_apart` (selftest)
fails if a shape and the campaign's plan at that opening ever disagree, so
a *planner* change cannot leave them behind either. The five shapes that
moved on 2026-09-19 were each reproduced on a second engine built with the
inherited block shape and the smallest queue margin before being frozen;
their p1 fingerprints were SCORE 12424 / 23400388398881646, S103828 8558 /
3423877434236519882, S037100 8647 / 155337493955370392, S119752 3870 /
618645133278286 and S133761 4900 / 22624213393984414. **A find does not
move a fingerprint**: a shape names its index, and the form list of an
index never changes once it exists. What a find does is open a *new*
filter, and rule 5g then owes a shape at it.

## Every opening, priced (CLAUDE.md 5c and 5g)

The planned configuration through the engine API — real launches swept and
timed on a far window, their survivors counted:

| family | opens at | device | survivors/s | modelled median | device to it | one segment |
|---|---|---|---|---|---|---|
| A093483 | n = 18, mod 6, wheel to 41 × 128 | 6.7e16 x/s | 16,000 | 4.7e16 | 0.7 s | 0.6 s |
| A103828 | n = 19, mod 30, wheel to 43 × 224 | 1.7e17 | 28,000 | 7.7e18 | 45 s | 17 s |
| A037100 | n = 19, mod 6, wheel to 41 × 224 | 6.5e16 | 22,000 | 7.1e17 | 11 s | 1.0 s |
| A119752 | n = 15, mod 6, wheel to 31 × 128 | 9.4e15 | 49,000 | 4.4e13 | one segment (ms) | 3 ms |
| A119751 | n = 15, mod 30, wheel to 31 × 224 | 1.6e16 | 54,000 | 8.4e13 | one segment (ms) | 3 ms |
| A133761 | n = 17, mod 30, wheel to 41 × 224 | 1.2e17 | 19,000 | 1.1e17 | 1.0 s | 0.6 s |

The device runs 3.0–3.4e12 candidates a second at the four openings whose
launches are tens of milliseconds, and 1.9–2.0e12 at the two n = 15
openings, where a whole segment is one 3 ms launch.

**Every open term is seconds of device.** What the hunt costs is the terms
after them. Those filters do not exist yet, but the model's stand-ins do,
and the same measurement on them (A093483; every row past the first is a
PROJECTION on a stand-in filter, and the clock is the model's expected line
to a *confirmed* find over the measured rate):

| filter | plan p2 | device | segment / median | expected clock to a confirmed find | the inherited plan |
|---|---|---|---|---|---|
| n = 18 | to 41 × 128 | 6.7e16 x/s | 0.83 | 2.4 s | the same plan; 6.4e16 |
| n = 19* | to 43 × 128 | 1.3e17 | 0.73 | 45 s | to 43 × 160 |
| n = 20* | to 43 × 224 | 1.6e17 | 0.07 | **12 min** | to 47 × 64: 12.7 min |
| n = 21* | to 47 × 128 | 2.4e17 | 0.07 | **3.4 h** | to 53 × 32, wide: 5.6 h |
| n = 22* | to 53 × 224, wide | 3.9e17 | 0.20 | 69 h | the same plan |

Rule 5g's re-pricing at every promotion is what the launcher's `size_pool`
does at runtime for the host; the *plan* at a new filter is derived from the
real term the moment it lands, and OPTIMIZATION_LOG.md ("Open", item 3) says
how to check it there.

## The host side

The pool is sized at runtime from a measurement at the campaign's own
filter, never from a constant, and re-sized at every promotion. Since round
1 the sieve is planned a rung or two deeper wherever that measured free
(from 17 forms up: 0.3–0.6% of device), so the openings ask for 16–28,000
survivors a second at 9–18 µs each — **0.2–0.4 core-seconds per second, one
worker** — where the inherited depth asked for 1.0–1.3 and a pool of three.
The launcher's whole host path measured 1.000 of the device alone at either
depth (OPTIMIZATION_LOG.md, Measurement 6). The 2x + 1 families cost more
per survivor (17 µs) because their first test is on a number twice the size.
