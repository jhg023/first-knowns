# RESULTS — factorial-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Sixteen terms on fourteen integers — a(11) through a(18) of both A177013
and A177014 — and, riding on the second, a(11) through a(18) of A226935:
twenty-four new terms across three entries**, found 2026-09-16/18 by one
campaign per family, engine v3, no flags. Both entries had stood at ten
terms since May 2010 and A226935 had never been extended.

Each evidence file was re-verified from disk before this page was written,
by a harness that shares nothing with the launcher: every value rebuilt as
k!·x ∓ 1 and re-tested with sympy's BPSW, the run re-derived from the bare
definition (`fladder_reference.run_length`), the stopper's factor
re-multiplied, every certificate re-verified by `huntlib.certificate.verify`
and matched to its own N, the ledger matched to the files, the least-claim
basis read back, and A226935's own recurrence run from x + 1 on every
A177014 find. 14 files, 205 certificates, all green. Model figures are from
`fladder_model`, each scored from the term before it — the frontier that was
known when the search for that term began.

### A177013 — one campaign, 2026-09-16, 14:01–20:26

`python launch.py`, from a(10) = 3,240,034,842. The first six terms landed
inside the first 66 seconds, as the README's wall-clock table had said they
would; a(17) at 24 minutes and a(18) at 5.75 hours. Forms k!·x − 1, so the
certificate route past the proof crossing is BLS75 Theorem 15 on
N + 1 = k!·x, x factored once per find.

#### a(11) = 83,398,005,540 — 14:01:38

- **run 11**: k!·x − 1 prime for k = 1..11; the 11th value is
  3,328,981,507,539,071,999. **stopper** 12!·x − 1 =
  39,947,778,090,468,863,999 = 73 × 547,229,836,855,737,863.
- 11 `deterministic-mr` certificates (x under the crossing 8.3e16).
- **model**: from a(10), median 3.37e10; x / median = 2.47, E = 1.39.
- x = 2² · 3³ · 5 · 3259 · 47389.
- evidence: `evidence/A177013_a11_83398005540.json`

#### a(12) = 7,740,678,645,990 — 14:01:42

- **run 12**: the 12th value is 3,707,797,456,515,043,583,999. **stopper**
  13!·x − 1 = 48,201,366,934,695,566,591,999 = 67 ×
  719,423,387,085,008,456,597.
- 12 `deterministic-mr` certificates.
- **model**: from a(11), median 1.59e12; x / median = 4.86, E = 2.18.
- x = 2 · 3² · 5 · 29 · 151 · 4001 · 4909.
- evidence: `evidence/A177013_a12_7740678645990.json`

#### a(13) = 476,382,545,091,120 — 14:01:48

- **run 13**: the 13th value is 2,966,444,017,039,342,135,295,999, the
  largest this family certified by the deterministic test. **stopper**
  14!·x − 1 = 41,530,216,238,550,789,894,143,999 = 6,029 ×
  6,888,408,730,892,484,639,931.
- 13 `deterministic-mr` certificates (x just under the crossing 5.3e14).
- **model**: from a(12), median 7.30e13; x / median = 6.52, E = 2.97 — the
  latest of the sixteen against its model.
- x = 2⁴ · 3 · 5 · 5779 · 343472447.
- evidence: `evidence/A177013_a13_476382545091120.json`

#### a(14) = 985,173,408,688,560 — 14:01:54

- **run 14**: the 14th value is 85,885,734,305,147,893,788,671,999.
  **stopper** 15!·x − 1 = 1,288,286,014,577,218,406,830,079,999 = 67 ×
  19,228,149,471,301,767,266,120,597.
- **certificates**: x is past the proof crossing (3.8e13 at n = 14), so
  this is the project's first find proved by certificate: 12
  `deterministic-mr`, 2 **BLS75 Theorem 15**.
- **model**: from a(13), median 3.14e15; x / median = 0.31, E = 0.17 —
  only 2.07 × a(13).
- x = 2⁴ · 3 · 5 · 7 · 13 · 17 · 19 · 23 · 6071971.
- evidence: `evidence/A177013_a14_985173408688560.json`

#### a(15) = 107,596,829,892,570,252 — 14:02:02

- **run 15**: the 15th value is 140,701,616,528,570,312,179,700,735,999.
  **stopper** 16!·x − 1 = 2,251,225,864,457,124,994,875,211,775,999 =
  54,437 × 41,354,701,112,425,831,601,212,627.
- 10 `deterministic-mr`, 5 BLS75 Theorem 15.
- **model**: from a(14), median 6.74e16; x / median = 1.60, E = 0.97.
- x = 2² · 3 · 13 · 31 · 2889781 · 7699247 — no 5, no 7, no 11: nothing
  past 3 is forced on these ladders (README.md).
- evidence: `evidence/A177013_a15_107596829892570252.json`

#### a(16) = 744,858,063,184,134,930 — 14:02:38

- **run 16**: the 16th value is
  15,584,508,752,384,283,395,431,587,839,999. **stopper** 17!·x − 1 =
  264,936,648,790,532,817,722,336,993,279,999 = 41 ×
  6,461,869,482,695,922,383,471,633,982,439.
- 10 `deterministic-mr`, 6 BLS75 Theorem 15.
- **model**: from a(15), median 3.57e18; x / median = 0.21, E = 0.19.
  66 seconds in, at the close of the first n = 16 segment.
- x = 2 · 3 · 5 · 23 · 2843 · 379706098979.
- evidence: `evidence/A177013_a16_744858063184134930.json`

#### a(17) = 159,027,369,950,870,799,240 — 14:25:11

- **run 17**: the 17th value is
  56,564,036,214,696,348,457,263,551,447,039,999. **stopper** 18!·x − 1 =
  1,018,152,651,864,534,272,230,743,926,046,719,999 = 461 ×
  2,208,574,082,135,649,180,543,913,071,684,859.
- 7 `deterministic-mr`, 10 BLS75 Theorem 15.
- **model**: from a(16), median 1.48e20; x / median = 1.07, E = 0.73.
  23.6 minutes in, at the close of the first n = 17 segment (the README had
  said 14 minutes to the median; the segment is 179 periods, 1.1e20, and a
  find is known to be the least only when its segment closes).
- x = 2³ · 3 · 5 · 232117 · 5709310748131.
- evidence: `evidence/A177013_a17_159027369950870799240.json`

#### a(18) = 1,639,203,889,936,938,872,760 — 19:46:40

- **run 18**: the 18th value is
  10,494,795,883,259,311,979,025,056,275,169,279,999. **stopper** 19!·x − 1
  = 199,401,121,781,926,927,601,476,069,228,216,319,999 = 67 ×
  2,976,136,145,998,909,367,186,209,988,480,840,597.
- 6 `deterministic-mr`, 12 BLS75 Theorem 15; every prime factor of x under
  the deterministic bound, so no subproof.
- **model**: from a(17), median 6.70e21; x / median = 0.24, E = 0.22 —
  early in x, and still 5.75 hours in: the n = 18 segment is 160 periods of
  the wheel to 53, 5.2e21 wide, and the find was narrated at its close.
- x = 2³ · 3³ · 5 · 127 · 3359 · 26953 · 132004393.
- evidence: `evidence/A177013_a18_1639203889936938872760.json`

`E` averages **1.10** over the eight; x / median runs 2.47, 4.86, 6.52, 0.31,
1.60, 0.21, 1.07, 0.24.

#### A bound: A177013 a(19) > 5,409,800,307,213,547,425,180

After a(18) the filter moved to n = 19 and the campaign ran 40 minutes more
before it was stopped by hand. Its coverage cursor stands at period 166 of
the wheel to 53, x = 5,409,800,307,213,547,425,180, the close of the n = 18
segment that held a(18) — every survivor in it run on to n + 8 and none
reaching 19. So **no x < 5.4098e21 has k!·x − 1 prime for all k = 1..19**,
the first bound of any kind on A177013 at an open index. The work cursor is
13% of the way through the first n = 19 segment (launch 24,444 of 181,350;
its 24,856 pending survivors are in the checkpoint), which a resume picks up
and which claims nothing until that segment closes.

### A177014 — one campaign, 2026-09-16 20:27 to 2026-09-18 17:45

`python launch.py --family A177014`, from a(9) = a(10) = 228,698,250. Forms
k!·x + 1, so the certificate route is BLS75 Theorem 1 on N − 1 = k!·x. Every
term is also **A226935 at the same index, plus one**: the chain
p(i) = i·p(i−1) − (i−1) from p(1) = x + 1 was re-run on each find for this
page and is prime, and equal to i!·x + 1, at every link.

The campaign died once, at 26.8 hours, on a `[NEAR]` value whose stopper took
the ECM leg of the witness chain (a sympy ground-type integer reaching
`random.Random`; [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), "Incident").
No coverage was lost — the cursor was one save behind — and it was resumed
on the fixed tree on 2026-09-18; a(18) landed 5.3 hours into the resumed leg.

#### a(11) = 133,493,208,618 — 2026-09-16, 20:27:26

- **run 11**: k!·x + 1 prime for k = 1..11; the 11th value is
  5,328,621,709,762,982,401. **stopper** 12!·x + 1 =
  63,943,460,517,155,788,801 = 17 × 3,761,380,030,420,928,753.
- 11 `deterministic-mr` certificates.
- **also settles**: A226935(11) = 133,493,208,619.
- **model**: from a(10), median 2.40e10; x / median = 5.57, E = 2.13.
- x = 2 · 3 · 7 · 11² · 26267849.
- evidence: `evidence/A177014_a11_133493208618.json`

#### a(12) = 946,564,216,260 — 20:27:32

- **run 12**: the 12th value is 453,405,774,091,286,016,001. **stopper**
  13!·x + 1 = 5,894,275,063,186,718,208,001 = 173 ×
  34,070,954,122,466,579,237.
- 12 `deterministic-mr` certificates.
- **also settles**: A226935(12) = 946,564,216,261.
- **model**: from a(11), median 1.73e12; x / median = 0.55, E = 0.42.
- x = 2² · 3 · 5 · 13 · 421 · 2882527.
- evidence: `evidence/A177014_a12_946564216260.json`

#### a(13) = a(14) = a(15) = 63,877,984,659,108 — 20:27:36

- **run 15, found while a(13) was open**: k!·x + 1 is prime for every
  k = 1..15, so this one x settles three terms at once — a **rider**, as the
  published a(9) = a(10) is. The 15th value is
  83,531,603,218,212,749,343,744,001. **stopper** 16!·x + 1 =
  1,336,505,651,491,403,989,499,904,001 = 12,239 ×
  109,200,559,808,105,563,322,159.
- 13 `deterministic-mr`, 2 **BLS75 Theorem 1**. Evidenced once, under
  a(13), with `settles = [13, 14, 15]`.
- **also settles**: A226935(13) = A226935(14) = A226935(15) =
  63,877,984,659,109.
- **model**: from a(12), a(13)'s median 5.51e13; x / median = 1.16,
  E = 0.77. a(14) and a(15) are not scored: they were never searched for.
  (The model had put a(15)'s median at 6.2e16, a thousand times higher.)
- x = 2² · 3² · 43 · 773 · 1223 · 43649.
- evidence: `evidence/A177014_a13_63877984659108.json`

#### a(16) = 2,356,745,767,044,800,940 — 20:28:12

- **run 16**: the 16th value is
  49,309,696,503,311,764,750,404,894,720,001. **stopper** 17!·x + 1 =
  838,264,840,556,300,000,756,883,210,240,001 = 97 ×
  8,641,905,572,745,360,832,545,187,734,433.
- 9 `deterministic-mr`, 7 BLS75 Theorem 1.
- **also settles**: A226935(16) = 2,356,745,767,044,800,941.
- **model**: from a(15), median 3.11e18; x / median = 0.76, E = 0.57.
- x = 2² · 3² · 5 · 17 · 47 · 16386773515817.
- evidence: `evidence/A177014_a16_2356745767044800940.json`

#### a(17) = 118,296,999,554,873,123,520 — 20:50:03

- **run 17**: the 17th value is
  42,076,755,523,146,478,128,422,926,417,920,001. **stopper** 18!·x + 1 =
  757,381,599,416,636,606,311,612,675,522,560,001 = 41 ×
  18,472,721,936,991,136,739,307,626,232,257,561.
- 7 `deterministic-mr`, 10 BLS75 Theorem 1.
- **also settles**: A226935(17) = 118,296,999,554,873,123,521.
- **model**: from a(16), median 1.55e20; x / median = 0.77, E = 0.57.
  23 minutes in, at the close of the first n = 17 segment.
- x = 2⁶ · 3³ · 5 · 83 · 164961233203471.
- evidence: `evidence/A177014_a17_118296999554873123520.json`

#### a(18) = 30,911,690,086,525,348,609,590 — 2026-09-18, 17:45:30

- **run 18**: the 18th value is
  197,908,191,809,582,777,136,987,780,618,731,520,001, the largest integer
  this project has certified. **stopper** 19!·x + 1 =
  3,760,255,644,382,072,765,602,767,831,755,898,880,001 = 853,091 ×
  4,407,801,329,966,056,101,403,915,680,456,011.
- 4 `deterministic-mr`, 14 BLS75 Theorem 1; the largest prime factor of x,
  4,332,991,322,790,253, is under the deterministic bound, so no subproof.
- **also settles**: A226935(18) = 30,911,690,086,525,348,609,591.
- **model**: from a(17), median 6.57e21, P90 3.32e22; x / median = 4.71,
  E = 2.19 — at the 89th percentile, 19 × its sibling's a(18), and 32.1
  campaign hours in against the 5.6 the median had priced.
- x = 2 · 3² · 5 · 31 · 2557 · 4332991322790253.
- evidence: `evidence/A177014_a18_30911690086525348609590.json`

`E` averages **1.11** over the six searched terms; x / median 5.57, 0.55,
1.16, 0.76, 0.77, 4.71.

#### A bound: A177014 a(19) > 31,481,127,088,965,583,209,180

The campaign was stopped at the close of the segment that held a(18): the
filter has moved to n = 19 and both cursors stand at period 966, x =
31,481,127,088,965,583,209,180, with nothing pending. Every survivor below
it was run on to n + 8 and none reached 19, so **no x < 3.1481e22 has
k!·x + 1 prime for all k = 1..19** — and therefore A226935(19) >
31,481,127,088,965,583,209,181.

### The least-claim basis, and why the bounds hold above the crossing

Each find is a **first occurrence**: every x from the published frontier to
the find swept at unit 6 and every survivor classified in x order, with
monotonicity (a(n) ≥ a(n − 1)) the floor below. The basis is written into
every evidence file — `swept_from_x`, `covered_by_previous_filter_to` (a
promotion carries the classified line, README.md "One line"), `swept_to_x`,
the wheel period, the sieve depth and the monotone floor — under the engine
keys `a177013-v3-p2-seg32-pbd224-cpl37w38` and
`a177014-v3-p2-seg32-pbd224-cpl37w38`.

The proof crossing is very low here (x = 5.2e8 at n = 18), so almost all of
both sweeps classified by a seven-base strong probable-prime chain rather
than a proof. The searched-empty claims are sound there for the reason every
ladder project in this repository gives: a composite that passes the chain
can only *lengthen* a run, never hide one, so a true run of n would have
passed every test, been claimed, and then been proved by certificate — as
all sixteen were.

## The finds against the model

| | A177013 | A177014 | both |
|---|---|---|---|
| terms | 8 on 8 integers | 8 on 6 integers (+ 8 of A226935) | **16** (24 with the rider entry) |
| searched draws | 8 | 6 | 14 |
| mean E | 1.10 | 1.11 | **1.10** |
| x / median, range | 0.21–6.52 | 0.55–5.57 | geometric mean **1.24** |
| certificates | 116: 81 `deterministic-mr`, 35 BLS75 thm 15 | 89: 56 `deterministic-mr`, 33 BLS75 thm 1 | 205 |
| campaign clock | 6.42 h | 32.13 h | 38.6 h |

`E` is the number of hits the model expected between the previous term and
the one that occurred; if the intensity is right it is Exp(1), mean 1. Over
the 14 searched draws it is 1.10, against 1.20 on the 8 published terms G11
validates on — a disjoint set. The README's caution that finds land at
1.9–2.5× their medians was, this time, pessimistic in the aggregate (1.24×)
and right about the one that cost the time: A177014's a(18), at 4.7×.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the evidence timestamps and the checkpoints, per filter, no flags:

| family, filter | line swept | wall clock | campaign rate | the engine at that filter ([BENCHMARKS.md](BENCHMARKS.md)) |
|---|---|---|---|---|
| A177013 n = 11..16 | 3.0e18 | 66 s, pool sizing and six promotions included | — | seconds each, as priced |
| A177013 n = 17 | 2.20e20 | 22.6 min | 1.62e17 x/s | 1.6e17 (`SCORE`) |
| A177013 n = 18 | 5.19e21 | 5.36 h | 2.69e17 | 2.6e17 scored / 3.0e17 harness (`SCORE18`) |
| A177013 n = 19 | 9.8e20 (work cursor, not yet coverage) | 40 min | 4.1e17 | ~3.8e17 (paired, round 3) |
| A177014 n = 11..16 | 2.9e18 | ~50 s | — | seconds each |
| A177014 n = 17 | 2.20e20 | 21.9 min | 1.68e17 | 1.6e17 (`SCOREP`) |
| A177014 n = 18 | 3.126e22 | 31.7 h, across the crash and the resume | 2.73e17 | 2.6e17 / 3.0e17 (`SCORE18`) |

Every phase ran at its benchmark's rate. A177014's n = 18 figure includes
the 26.8 hours before the incident fix, when each `[NEAR]` value paid for a
witness nobody reads with the device idle, and still reads inside the
benchmark's band.

## The census

Counts per run length from each checkpoint, as printed in every `[STATUS]`
line (the finds themselves are included at their run lengths; A177014's
rider is the single 15 that is also its a(13) and a(14)):

    A177013   8: 226873  9: 75090  10: 23701  11: 7026  12: 2055  13: 645
              14: 175  15: 49  16: 12  17: 4  18: 1
                                           near 14   survivors 1,034,826,249
    A177014   8: 910335  9: 288974  10: 88585  11: 26024  12: 7467  13: 2083
              14: 547  15: 159  16: 28  17: 9  18: 1
                                           near 15   survivors 4,760,882,494

A run one short of the open term got a `[NEAR]` line and was verified as a
health check; everything shorter is a count and nothing else. 5.8 billion
survivors were classified across the two campaigns, and every one of them
is in exactly one of these counts. Each extra rung costs a factor of 3.0 to
3.8 on both families, rising slowly with the length as the model's
1/log(k!·x) does. The short lengths are counts of *sieve survivors*, not
densities: a filter-n sieve removes an x with a short run whenever one of
its later forms has a small factor, so they are comparable within a
campaign and not across filters. A177014 swept 5.8× the line A177013 did
and carries 3.6–4.0× its counts.

## What is open now

**a(19) on all three entries, and the project is PAUSED there.**

| entry | frontier (all this project's) | open next | searched empty below | resumes at | median from the bound | at ~3.8e17 x/s |
|---|---|---|---|---|---|---|
| A177013 | **a(18) = 1,639,203,889,936,938,872,760** | a(19) | 5.4098e21 | n = 19, period 166 (13% into its segment) | 3.0e23 | 9 days |
| A177014 | **a(18) = 30,911,690,086,525,348,609,590** | a(19) | 3.1481e22 | n = 19, period 966 | 3.6e23 | 10 days |
| A226935 | **a(18) = 30,911,690,086,525,348,609,591** | a(19) | 3.1481e22 (+ 1) | — rides A177014 | — | — |

**Why it stops here rather than at a wall.** Nothing is in the way: the
ceiling is 1e40 and the deeper bound is 3.1e22; the certificate route works
on both signs and nine of the fourteen files are proved by it; both
campaigns resume from their checkpoints with no flags, census and finds
intact. What changed is the price. From its bound, at the n = 19 rate, the
model puts a(19) inside a nine-hour night with probability **5%** (A177013)
and **4%** (A177014), inside a day with 12% and 9%, inside a week with 44%
and 41% — against a night that was worth seven terms per family when the
project started. Read the medians as floors: this project's own finds landed
at 0.21× to 6.5× theirs.

**What a resumed campaign would need.** Nothing new to be correct:
`python launch.py` and `python launch.py --family A177014` continue from
the cursors above. **Whoever resumes runs `python launch.py --selftest` and
`python score.py` first** (CLAUDE.md rule 2). To be *worth* resuming it
wants an engine factor, and [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)
("Open, priced, unbuilt") prices the candidates: INNOVATION.md's two passes
on the window loop, which is 92% of the device and whose verdict is still
inherited, and the wide record's own cost at n ≥ 18. With the finds entered
in the oracle's `FOUND`, G18 compiles the n = 19, 20 and 21 plans for both
families on every battery, so a find at n = 19 promotes into a configuration
that has been built — but it has not been priced (rule 5g: sweep n = 20
before the campaign is offered there).

Where each campaign stands is read with `python launch.py --status` and
`python launch.py --status --family A177014`, which touch nothing.
