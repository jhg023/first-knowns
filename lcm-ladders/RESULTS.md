# RESULTS — lcm-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

**Which number to submit.** A078502 calls its term N and A074200 calls its
term m, and this page writes each in its own letter. The engine sweeps the
quotient of the term by lcm(1..n) at filter n (N/lcm(1..n), m/lcm(1..n)),
which is never the term; the depths, medians and rates below that are in
that quotient say so. The evidence files follow each entry's own letter,
and their `oeis_terms` field is literally what to submit (README.md, "Which
number goes in the OEIS").

## Verified finds

**Nine terms on eight integers — a(15) through a(19) of A078502 and a(15)
through a(18) of A074200 — and, riding on them, a(15)–a(19) of A093554 and
a(15)–a(18) of A093553: eighteen new terms across four entries.** Seven were
found 2026-09-06 by one campaign per family, engine v1 (round 8), no flags;
A074200's a(17) and a(18) were found 2026-09-19 by that family's campaign
resumed from its checkpoint, on engine v2 — a(18) on the wide survivor
record, the first find it has produced. The first advance on A078502 since
January 2003 and on A074200 since February 2004; the two rider entries had
never been extended.

Each evidence file was re-verified from disk before this page was written,
by a harness that shares nothing with the launcher: the term rebuilt as
lcm(1..n) times the file's quotient, every value (N/k − 1 for A078502,
m/k + 1 for A074200) rebuilt and re-tested with sympy's BPSW, the run
re-derived from the bare definition on the term
(`lcml_reference.run_length_N`, divisibility included), the stopper's
factor re-multiplied, every certificate re-verified by
`huntlib.certificate.verify` and matched to its own value, the ledger
matched to the files, the riders' shift and the least-claim floor read
back. 6 files, 98 certificates, all green on 2026-09-18; the four A074200
files again on 2026-09-19 with the two new ones, 66 certificates, all green.
Model figures are from `lcml_model`, each scored in the quotient at the
find's own filter from the term before it.

### A078502 — one campaign, 2026-09-06, 09:51–12:01

`python launch.py`, from a(13) = a(14) = 7,272,877,497,848,202,240. Forms
(N − k)/k = N/k − 1 = (lcm(1..n)/k)·(N/lcm(1..n)) − 1, so past the
deterministic bound the certificate route is BLS75 Theorem 15 on the value
plus one, N/k, with N factored once per find. Every term is also **A093554
at the same index, minus one**.

#### a(15) = 143,479,704,870,546,258,614,400 — 09:52:06

- **run 15**: (N − k)/k prime for k = 1..15; the largest value is N − 1 =
  143,479,704,870,546,258,614,399 and the smallest N/15 − 1 =
  9,565,313,658,036,417,240,959. **stopper** N/16 − 1 =
  8,967,481,554,409,141,163,399 = 17 × 527,498,914,965,243,597,847.
- 15 `deterministic-mr` certificates: the last find here under the bound.
- **also settles**: A093554(15) = 143,479,704,870,546,258,614,399.
- **model**: from a(14), median N/lcm(1..15) = 1.18e17 at filter 15;
  find / median = 3.37, E = 1.62. 21 seconds in, pool sizing included.
- N = 2⁷ · 3² · 5² · 7 · 11 · 13 · 101 · 49276804353013 (N/lcm(1..15) =
  398,156,579,172,345,040, with lcm(1..15) = 360360).
- evidence: `evidence/A078502_a15_143479704870546258614400.json`

#### a(16) = 123,117,690,451,783,381,321,968,000 — 10:00:22

- **run 16**: the smallest value is N/16 − 1 =
  7,694,855,653,236,461,332,622,999. **stopper** N/17 − 1 =
  7,242,217,085,399,022,430,703,999 = 17 × 426,012,769,729,354,260,629,647.
- **certificates**: every value is past the deterministic bound; all 16 by
  **BLS75 Theorem 15**, every prime factor of N under the bound.
- **also settles**: A093554(16) = 123,117,690,451,783,381,321,967,999.
- **model**: from a(15), median N/lcm(1..16) = 2.25e19; find / median =
  7.6, E = 3.03 — the latest of the six against its model. 8.6 minutes in.
- N = 2⁷ · 3³ · 5³ · 7 · 11 · 13 · 17 · 23 · 2184319 · 333357181.
- evidence: `evidence/A078502_a16_123117690451783381321968000.json`

#### a(17) = 1,003,795,564,977,176,937,562,396,800 — 10:17:21

- **run 17**: the smallest value is N/17 − 1 =
  59,046,797,939,833,937,503,670,399. **stopper** N/18 − 1 =
  55,766,420,276,509,829,864,577,599 = 19 × 2,935,074,751,395,254,203,398,821.
- 17 BLS75 Theorem 15 certificates.
- **also settles**: A093554(17) = 1,003,795,564,977,176,937,562,396,799.
- **model**: from a(16), median N/lcm(1..17) = 1.21e20; find / median =
  0.68, E = 0.49. 25.6 minutes in.
- N = 2⁷ · 3⁴ · 5² · 7 · 11 · 13 · 17 · 1697 · 134105143175921.
- evidence: `evidence/A078502_a17_1003795564977176937562396800.json`

#### a(18) = a(19) = 52,270,101,840,951,834,355,676,160,000 — 11:57:47

- **run 19, found while a(18) was open**: 19 divides N and (N − k)/k is prime
  for every k = 1..19, so this one N settles two terms at once — a **rider**,
  as the published a(13) = a(14) is. The smallest value is N/19 − 1 =
  2,751,057,991,629,043,913,456,639,999. **stopper** N/20 − 1 =
  2,613,505,092,047,591,717,783,807,999 = 233 ×
  11,216,760,051,706,402,222,248,103.
- 19 BLS75 Theorem 15 certificates. Evidenced once, under a(18), with
  `settles = [18, 19]`.
- **also settles**: A093554(18) = A093554(19) =
  52,270,101,840,951,834,355,676,159,999.
- **model**: from a(17), a(18)'s median N/lcm(1..18) = 2.95e22;
  find / median = 0.145, E = 0.165 — early, and it carried a(19) with it.
  a(19) is not scored: it was never searched for. 2.10 hours in.
- N = 2¹³ · 3⁴ · 5⁴ · 7² · 11 · 13² · 17 · 19 · 23 · 59 · 251 · 12576703.
- evidence: `evidence/A078502_a18_52270101840951834355676160000.json`

`E` averages 1.33 over the four searched terms; find / median 3.37, 7.6,
0.68, 0.145.

**No bound past a(19).** The filter moved to n = 20 and the campaign was
stopped by hand 3 minutes 20 seconds later, inside the first n = 20 segment
(period 88, launch 3,801; 335 pending survivors in the checkpoint). No
segment closed, so nothing is claimed beyond monotonicity: a(20) ≥ a(19).

### A074200 — one campaign, 2026-09-06 12:02–12:51, resumed 2026-09-19

`python launch.py --family A074200`, from a(14) =
2,918,756,139,031,688,155,200. Forms (m + k)/k = m/k + 1 =
(lcm(1..n)/k)·(m/lcm(1..n)) + 1, certificate route BLS75 Theorem 1 on the
value less one, m/k. Every term is also **A093553 at the same index, plus
one**.

#### a(15) = 174,563,969,955,955,530,350,400 — 12:02:35

- **run 15**: (m + k)/k prime for k = 1..15; the largest value is m + 1 =
  174,563,969,955,955,530,350,401 and the smallest m/15 + 1 =
  11,637,597,997,063,702,023,361. **stopper** m/16 + 1 =
  10,910,248,122,247,220,646,901 = 17 × 641,779,301,308,660,038,053.
- 15 `deterministic-mr` certificates.
- **also settles**: A093553(15) = 174,563,969,955,955,530,350,401.
- **model**: from a(14), median m/lcm(1..15) = 1.46e17; find / median =
  3.32, E = 1.75. 21 seconds in.
- m = 2⁶ · 3² · 5² · 7 · 11 · 13 · 12110387526081941.
- evidence: `evidence/A074200_a15_174563969955955530350400.json`

#### a(16) = 10,316,338,205,727,668,643,809,280 — 12:04:47

- **run 16**: the smallest value is m/16 + 1 =
  644,771,137,857,979,290,238,081. **stopper** m/17 + 1 =
  606,843,423,866,333,449,635,841 = 19 × 31,939,127,571,912,286,822,939.
- **certificates**: m straddles the bound — 13 `deterministic-mr` and 3
  **BLS75 Theorem 1** (k = 1, 2, 3, the values above 3.317e24).
- **also settles**: A093553(16) = 10,316,338,205,727,668,643,809,281.
- **model**: from a(15), median m/lcm(1..16) = 2.26e19; find / median =
  0.63, E = 0.49. 2.5 minutes in.
- m = 2¹¹ · 3³ · 5 · 7² · 11 · 13 · 17 · 37 · 61 · 9349 · 14845133.
- evidence: `evidence/A074200_a16_10316338205727668643809280.json`

#### a(17) = 3,806,845,688,410,765,173,753,259,680 — 2026-09-19 02:14:01

- The n = 17 sweep took three sittings: 47 minutes on 2026-09-06 to period
  14,622 (no a(17) below m = 2.4017e27, the bound this page carried for
  thirteen days), 18 minutes on 2026-09-19 under engine v1 to period 20,446,
  and 11 minutes under engine v2, which **adopted** the v1 cursor — the
  coverage claim kept, the open segment re-swept from its start
  (OPTIMIZATION_LOG.md round 10). The n = 17 plan is identical in both
  engines, so the line is one line.
- **run 17**: (m + k)/k prime for k = 1..17; the largest value is m + 1 =
  3,806,845,688,410,765,173,753,259,681 and the smallest m/17 + 1 =
  223,932,099,318,280,304,338,427,041. **stopper** m/18 + 1 =
  211,491,427,133,931,398,541,847,761 = 3 ×
  70,497,142,377,977,132,847,282,587.
- 17 **BLS75 Theorem 1** certificates: every value is past the
  deterministic bound.
- **also settles**: A093553(17) = 3,806,845,688,410,765,173,753,259,681.
- **model**: from a(16), median m/lcm(1..17) = 9.77e19 at filter 17;
  find / median = 3.18, E = 1.62 — a 20% event, late and not missing. 76
  minutes of sweep at n = 17 in all.
- m = 2⁵ · 3² · 5 · 7² · 11 · 13² · 17 · 149 · 8089 · 1416437074991
  (m/lcm(1..17) = 310,706,098,510,212,432,482, with lcm(1..17) = 12252240).
- evidence: `evidence/A074200_a17_3806845688410765173753259680.json`

#### a(18) = 246,823,048,779,050,778,944,771,141,280 — 2026-09-19 09:15:49

- **The first find on engine v2's wide survivor record**: at n = 18 the
  campaign promoted itself onto the wheel to 61 (period 4.82e19 of the
  quotient m/lcm(1..18), unit 114), which no u64 launch offset can carry,
  with no flag. It sits in the second 224-period segment, at period 417.
- **run 18**: the smallest value is m/18 + 1 =
  13,712,391,598,836,154,385,820,618,961. **stopper** m/19 + 1 =
  12,990,686,777,844,777,839,198,481,121 = 109 ×
  119,180,612,640,777,778,341,270,469 — 19 divides m, so this is a composite
  and not a divisibility stop.
- 18 BLS75 Theorem 1 certificates.
- **also settles**: A093553(18) = 246,823,048,779,050,778,944,771,141,281.
- **model**: from a(17), median m/lcm(1..18) = 3.05e22 at filter 18;
  find / median = 0.66, E = 0.51. 7.03 hours after a(17).
- m = 2⁵ · 3³ · 5 · 7 · 11 · 13 · 17 · 19 · 41 · 329387 · 13085039992819
  (m/lcm(1..18) = 20,145,136,626,367,976,708,322, with lcm(1..18) =
  12252240).
- evidence: `evidence/A074200_a18_246823048779050778944771141280.json`

`E` averages 1.09 over the four; find / median 3.32, 0.63, 3.18, 0.66.

#### A bound: A074200 a(19) > 511,330,427,374,470,630,698,663,892,000

After a(18) the filter moved to n = 19 (lcm(1..19) = 232792560, unit 6, the
wheel to 61 again) and the sweep ran 4.35 hours more before it was stopped
by hand: two segments closed, to period 865 of the n = 19 wheel,
m/lcm(1..19) = 2,196,506,741,342,896,141,950, m =
511,330,427,374,470,630,698,663,892,000, every survivor below it classified
and none reaching 19. So **no m < 5.1133e29 has (m + k)/k prime for all
k = 1..19**, and A093553(19) exceeds it by one. Above the deterministic
bound the classification is a seven-base strong probable-prime chain, which
can only *lengthen* a run, never hide one, so the bound stands. The model
puts 2% of a(19)'s mass under this cursor: the search has barely started.

### The least-claim basis

Each find is a **first occurrence**: every quotient from the previous term's
quotient at that filter swept at the filter's forced unit and every survivor
classified in quotient order, with monotonicity in the term the floor
below. The basis is in every evidence file — `swept_from_x`,
`swept_from_N` / `swept_to_N` (`_m` in an A074200 file), the filter, the
wheel period, the sieve depth, the unit and the monotone floor — under the
engine keys
`a078502-v1-p1-seg32-pbd224-cpl37` and `a074200-v1-p1-seg32-pbd224-cpl37`,
and `a074200-v2-p2-seg32-pbd224-cpl37` for a(17) and a(18). a(17)'s line was
swept under both A074200 keys; they plan the identical wheel, unit and depth
at n = 17, and the v2 sweep began at the v1 coverage boundary.
The unit changes with the filter (2, 34, 2, 114 at n = 15..18) because the
forcing here is sporadic (README.md), and each is a coverage claim the
engines derive and refuse to be handed.

## The finds against the model

| | A078502 | A074200 | both |
|---|---|---|---|
| terms | 5 on 4 integers (+ 5 of A093554) | 4 (+ 4 of A093553) | **9** (18 with the riders) |
| searched draws | 4 | 4 | 8 |
| mean E | 1.33 | 1.09 | **1.21** |
| find / median | 0.145–7.6 | 0.63–3.32 | geometric mean 1.35 |
| certificates | 67: 15 `deterministic-mr`, 52 BLS75 thm 15 | 66: 28 `deterministic-mr`, 38 BLS75 thm 1 | 133 |
| campaign clock | 2.16 h | 12.66 h (4.35 h of it at n = 19) | 14.82 h |

Against the 1.12 of G11's twelve published terms, a disjoint set: the
intensity is right, the individual draws scatter over a factor of fifty,
and the pooled first occurrence came at 1.35× its median — inside the
1.9–2.5× the README told the reader to budget.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the evidence timestamps and the checkpoints, per filter, no flags. The
line is in the quotient of the term by lcm(1..n) at that filter, and so are
the rates; a promotion re-denominates it (A078502's a(16) sits at a quotient
N/lcm(1..16) = 1.7e20 on the n = 16 line and N/lcm(1..17) = 1.0e19 on the
n = 17 line).

| family, filter | line swept | wall clock | campaign rate | the engine there ([BENCHMARKS.md](BENCHMARKS.md)) |
|---|---|---|---|---|
| A078502 n = 15 | 2.0e17 | 21 s, pool sizing included | — | 2 s of device |
| A078502 n = 16 | 1.71e20 | 8.3 min | 3.44e17 per second of the quotient | 3.85e17 |
| A078502 n = 17 | 7.19e19 | 17.0 min | 7.05e16 | 6.63e16 |
| A078502 n = 18 | 4.18e21 | 100.4 min | 6.94e17 | 6.75e17 |
| A074200 n = 15 | 2.4e17 | 21 s | — | 2 s of device |
| A074200 n = 16 | 1.41e19 | 132 s, the engine rebuild included | — | one segment |
| A074200 n = 17 | 1.95e20 | 47.0 min | 6.93e16 | 6.63e16 |
| A074200 n = 17, resumed, engine v1 | 7.81e19 | 18.0 min | 7.2e16 | 6.97e16 (paired, 2026-09-19) |
| A074200 n = 17, resumed, engine v2 | 3.90e19 | 11.2 min, start-up, adoption re-sweep, pool sizing and the certificates included | — | 7.01e16 |
| A074200 n = 18, engine v2, wide record | 2.16e22 | 7.03 h | **8.54e17** | 8.22e17 (v1 measured 7.17e17 beside it) |
| A074200 n = 19, engine v2, wide record | 1.55e21 (two segments and 72% of a third) | 4.35 h | **9.87e16** | 9.54e16 (v1 7.78e16) |

Every timed phase is inside 11% of its benchmark, on both sides of it. The
n = 18 phase is the first on the wheel to 61: on engine v1 at the 6.94e17
A078502's n = 18 phase ran at, the same line is 8.65 hours.

## The census

Counts per run length from each checkpoint, as printed in every `[STATUS]`
line (the finds included; A078502's rider is the single 18 — a filter-18
sweep caps a run at 18, and its nineteenth value was decided afterwards, on
N):

    A078502   8: 34731  9: 11069  10: 3496  11: 1090  12: 328  13: 133
              14: 55  15: 16  16: 3  17: 2  18: 1  19: 0
                                           near 14   survivors 744,699,973
    A074200   8: 89135  9: 27706  10: 8653  11: 2777  12: 815  13: 264
              14: 78  15: 30  16: 13  17: 2  18: 1
                                           near 11   survivors 2,136,170,010

The counts are of *sieve survivors at the filter then running*, capped at
that filter, so they are comparable within a campaign and not across
filters. 2.88 billion survivors
were classified across the two campaigns.

## What is open now

**The project is PAUSED with both families at a term priced in weeks or
more.**

| entry | frontier (all this project's) | open next | searched empty below | resumes at | median from there | at the campaign's rate |
|---|---|---|---|---|---|---|
| A074200 | **a(18) = 246,823,048,779,050,778,944,771,141,280** | a(19) | m = 5.1133e29 | n = 19, period 865 | m/lcm(1..19) ≈ 9.4e22 (m ≈ 2.2e31) | **about 11 days** at 9.87e16 per second of m/lcm(1..19) |
| A093553 | the same integers + 1 | a(19) | + 1 | — rides A074200 | | |
| A078502 | **a(18) = a(19) = 52,270,101,840,951,834,355,676,160,000** | a(20) | — (no segment closed at n = 20) | n = 20, period 88 | N/lcm(1..20) = 1.48e25 (N = 3.4e33) | about a year |
| A093554 | the same integers − 1 | a(20) | | — rides A078502 | | |

**A074200's a(19)** has 2% of its modelled mass under the cursor. From
there, at the 9.87e16 per second of m/lcm(1..19) its n = 19 phase ran at,
the model puts it inside a day with probability **10%**, inside three with
22%, inside a week with **39%** and inside two with 56%.
`python launch.py --family A074200` continues from the checkpoint with no
flags.

**A078502 is priced out.** The rider took a(19) with it, and a(20) opens on
the n = 20 line with a median of N/lcm(1..20) = 1.5e25, N = 3.4e33 — four
orders past a(18)'s median in N. Engine v2 measured n = 20 at last (4.7e17
per second of N/lcm(1..20), 1.27× v1 there: OPTIMIZATION_LOG.md round 10),
which makes that median about a year of device. Its v1 checkpoint is
adopted by engine v2 on resume.

**Whoever resumes runs `python launch.py --selftest` and `python score.py`
first** (CLAUDE.md rule 2). Where each campaign stands is read with
`python launch.py --status` and `--status --family A074200`, which touch
nothing; the cursor they print is the quotient of the term by lcm(1..n) at
the current filter, and the term is lcm(1..n) times it.

## The OEIS entries

Nothing is submitted from inside the pipeline (CLAUDE.md rule 5); the owner
submitted these. The 2026-09-29 export of A078502 lists a(15)–a(18) in its
data and carries a b-file whose SHA-256 is that of this repository's
`evidence/b078502.txt`, so its a(19) is this project's; A074200 lists
a(15)–a(18). All nine equal the integers in the evidence files, entered
Sep 19 2026, and both entries link this repository. A093554 and A093553
still end at a(14): their a(15)–a(19) and a(15)–a(18), in `also_settles`
of the evidence files, are not yet entered.
