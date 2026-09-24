# RESULTS — clique-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Twenty-six terms across all six families, and twenty-two more riding on
them in the five derived entries: forty-eight new terms across eleven
entries.** Found 2026-09-19/20 by one campaign per family, `python
launch.py --family F`, no flags, engine v1 with planner p2. The first advance on A093483
since September 2012, on A119751 and A119752 since March 2008, on A133761
since 2015, on A037100 since 2019 and on A103828 since 2021.

Each evidence file was re-verified from disk on 2026-09-24 by a harness
that shares nothing with the launcher: the prefix matched to the OEIS data
plus this project's earlier finds, a(n) > a(n−1), every condition
a(n) + a(i) + 1 (and the family's extra form: 2x + 1, parity, or x prime)
re-tested with sympy's `isprime`, every value's certificate re-verified by
`huntlib.certificate.verify` and matched to its value, the riders' affine
maps recomputed, and each ledger matched to its files. 26 files, 472
certificates, all green. Every value sits below the deterministic
Miller–Rabin bound (the largest term is 5.6e21), so every certificate is
`deterministic-mr` and nothing is `unproved`.

Every file also carries the three-way verification (huntlib's Miller–Rabin
chain, sympy's BPSW, a re-sieve by the CPU engine at a different depth), the
oracle's re-derivation against the whole prefix, and a `least_claim`: the
sweep from a(n−1) + 1 to a(n) under the filter of index n, its wheel, sieve
depth and forced class. Times below are the ledger's, local.

### A093483 (`hard,nice`) — from a(17) = 252,534,792,143,648; riders A180565 = 2·a + 1

| n | a(n) | found | A180565(n) |
|---|---|---|---|
| 18 | 20,197,821,613,482,044 | 09-19 17:36:07 | 40,395,643,226,964,089 |
| 19 | 496,236,770,583,288,008 | 09-19 17:36:26 | 992,473,541,166,576,017 |
| 20 | 40,922,105,898,791,188,184 | 09-19 17:40:31 | 81,844,211,797,582,376,369 |
| 21 | 217,741,095,176,373,431,678 | 09-19 17:53:45 | 435,482,190,352,746,863,357 |

### A103828 — from a(18) = 2,504,509,324,460,255,499; riders A115760 = 2·a + 1, A128933 = a + 1

| n | a(n) | found | A115760(n) | A128933(n) |
|---|---|---|---|---|
| 19 | 9,280,267,468,530,688,839 | 09-19 17:56:25 | 18,560,534,937,061,377,679 | 9,280,267,468,530,688,840 |
| 20 | 99,700,077,030,751,405,599 | 09-19 18:06:45 | 199,400,154,061,502,811,199 | 99,700,077,030,751,405,600 |
| 21 | 4,584,245,071,483,320,696,489 | 09-19 21:39:24 | 9,168,490,142,966,641,392,979 | 4,584,245,071,483,320,696,490 |

A128933 lists only a(1)..a(13); its a(14)..a(18) are A103828's published
terms plus one, and are owed before these three can be entered.

### A037100 — from a(18) = 20,116,294,396,883,346

| n | a(n) | found |
|---|---|---|
| 19 | 537,430,040,678,506,086 | 09-19 21:51:22 |
| 20 | 1,028,739,281,939,216,454 | 09-19 21:51:52 |
| 21 | 140,672,999,403,766,760,844 | 09-19 22:06:37 |

### A119752 (`hard`) — from a(14) = 4,566,262,987,328; rider A120403 = a + 1

| n | a(n) | found | A120403(n) |
|---|---|---|---|
| 15 | 15,305,753,028,218 | 09-19 22:07:51 | 15,305,753,028,219 |
| 16 | 2,983,350,905,767,598 | 09-19 22:07:55 | 2,983,350,905,767,599 |
| 17 | 41,359,986,802,266,218 | 09-19 22:08:03 | 41,359,986,802,266,219 |
| 18 | 205,227,497,465,261,258 | 09-19 22:08:13 | 205,227,497,465,261,259 |
| 19 | 281,488,937,353,667,828 | 09-19 22:08:58 | 281,488,937,353,667,829 |
| 20 | 23,912,359,356,224,311,448 | 09-19 22:18:26 | 23,912,359,356,224,311,449 |

### A119751 (`hard`) — from a(14) = 4,565,283,812,559; rider A113875 = 2·a + 1

| n | a(n) | found | A113875(n) |
|---|---|---|---|
| 15 | 165,212,185,250,919 | 09-19 22:47:34 | 330,424,370,501,839 |
| 16 | 33,878,521,528,835,559 | 09-19 22:47:40 | 67,757,043,057,671,119 |
| 17 | 328,405,650,703,961,949 | 09-19 22:47:52 | 656,811,301,407,923,899 |
| 18 | 3,209,510,605,531,592,769 | 09-19 22:48:24 | 6,419,021,211,063,185,539 |
| 19 | 107,500,822,738,659,006,789 | 09-19 22:58:00 | 215,001,645,477,318,013,579 |
| 20 | 5,566,439,406,842,300,763,219 | 09-20 18:53:05 | 11,132,878,813,684,601,526,439 |

### A133761 — from a(16) = 3,544,413,963,914,171

| n | a(n) | found |
|---|---|---|
| 17 | 25,284,564,216,344,171 | 09-20 20:47:21 |
| 18 | 869,041,642,876,230,611 | 09-20 20:47:36 |
| 19 | 18,555,242,233,114,651,271 | 09-20 20:52:24 |
| 20 | 1,206,761,188,144,986,057,371 | 09-20 21:47:20 |

Evidence: `evidence/<entry>_a<n>_<a(n)>.json`, one per term, and one
ledger per family, `evidence/a<number>_discoveries.json`.

## What was open, and what a find was worth (as written before the run)

| entry | frontier | open | settles for free |
|---|---|---|---|
| A093483 (`hard,nice`) | a(17) = 252,534,792,143,648 (Don Reble, 2012) | a(18) | A180565(n) = 2·a(n) + 1 |
| A103828 | a(18) = 2,504,509,324,460,255,499 (Don Reble, 2021) | a(19) | A115760(n) = 2·a(n) + 1; A128933(n) = a(n) + 1 |
| A037100 | a(18) = 20,116,294,396,883,346 (Don Reble, 2019) | a(19) | — |
| A119752 (`hard`) | a(14) = 4,566,262,987,328 (Donovan Johnson, 2008) | a(15) | A120403(n) = a(n) + 1 |
| A119751 (`hard`) | a(14) = 4,565,283,812,559 (Donovan Johnson, 2008) | a(15) | A113875(n) = 2·a(n) + 1 |
| A133761 | a(16) = 3,544,413,963,914,171 (Don Reble, 2015) | a(17) | — |

No entry carries a published bound at its open index and none has a b-file;
the floor for a(n) is a(n−1) itself, because the definition says
a(n) > a(n−1). A128933 lists only 13 of A103828's 18 terms, so five of its
terms are already owed by the literature before this project finds one.

**A caveat on what the early terms are worth.** Every *open* term is seconds
of device at its modelled median. A119751 and A119752 stand where they do
because nobody returned to them after 2008 — Don Reble took their sibling
A103828 to 2.5e18 on a CPU in 2021. The hunt proper is the last two or three
terms each campaign reaches, and the census discipline below applies to all
of it.

## The odds, stated before the run

From `model_results.json` (Bateman–Horn, validated at mean E = 1.03 over 49
published terms; README.md). **Only the first term of each family is the
model's real answer** — the form list of every later index depends on terms
nobody has, and those rows are projections over stand-in terms.

| family | open term | median | P90 | device time to the median |
|---|---|---|---|---|
| A093483 | a(18) | 4.7e16 | 3.9e17 | 0.7 s |
| A103828 | a(19) | 7.7e18 | 2.8e19 | 30 s |
| A037100 | a(19) | 7.1e17 | 5.0e18 | 16 s |
| A119752 | a(15) | 4.4e13 | 2.8e14 | one segment |
| A119751 | a(15) | 8.4e13 | 5.9e14 | one segment |
| A133761 | a(17) | 1.1e17 | 7.9e17 | 1 s |

Projected beyond them, each term costs about 1.5 decades more than the last:
everything to about 1e21 inside an hour per family, a term near 1e22–1e23 at
a day or so. Read every depth as a floor.

## The census

Counted, not narrated (CONVENTIONS.md). The **run** of a survivor is in
index units: 0 if the family's extra form fails, else 1 + the number of
leading conditions x + a(1) + 1, x + a(2) + 1, … that are prime — "x is
compatible with the first r − 1 terms". Runs of 8 and up are counted per
length in the checkpoint and printed in every 30-second `[STATUS]` line; a
run one short of the open index gets a single `[NEAR]` line and is verified
as a health check, with a factor witness skipped; only a full run above
a(n−1) is a `[DISCOVERY]`, and only a discovery gets a file.

Two things differ from the other ladders here. A run cannot exceed the
filter, so there are no riders and a find settles exactly one index. And
when a find lands, the survivors of its segment that lie *past* it are
dropped uncounted: they were classified without the condition the find
creates, and they are swept again, and counted once, under the new filter.

## In progress

**PAUSED.** Nothing is running. Each family's checkpoint sits at the filter
of its open index, and no coverage above its last find has been claimed: a
find restarts the sweep at itself, and none of the six campaigns closed a
segment past its last term before it stopped. So the floor for each open
term is the definition's, a(n) > a(n−1):

| entry | open | floor | filter | campaign time so far |
|---|---|---|---|---|
| A093483 | a(22) | a(21) = 2.18e20 | n = 22 | 0.88 h |
| A103828 | a(22) | a(21) = 4.58e21 | n = 22 | 3.92 h |
| A037100 | a(22) | a(21) = 1.41e20 | n = 22 | 0.27 h |
| A119752 | a(21) | a(20) = 2.39e19 | n = 21 | 0.66 h |
| A119751 | a(21) | a(20) = 5.57e21 | n = 21 | 5.31 h |
| A133761 | a(21) | a(20) = 1.21e21 | n = 21 | 1.14 h |

Whoever resumes runs `python launch.py --selftest` and `python score.py`
first (CLAUDE.md rule 2), then, as the owner:

```bash
python launch.py                    # A093483 from a(22)
python launch.py --family A119752   # or A103828, A037100, A119751, A133761
```

Owed before the next session: the finds into the oracle's `FOUND` and a
frozen shape per family on the wide record at the live filter
(OPTIMIZATION_LOG.md "Open, priced, unbuilt" 1a), and the model rerun on the
real prefix for the open terms, whose table above is projection.
