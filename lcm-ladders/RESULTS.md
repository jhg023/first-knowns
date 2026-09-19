# RESULTS — lcm-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

**Notation.** A078502 calls its term N and A074200 calls its term m; this
page writes both as N, with N = L(n)·x, L(n) = lcm(1..n), and x the variable
the engine sweeps at filter n. The evidence files follow each entry's own
letter, and their `oeis_terms` field is literally what to submit
(README.md, "Notation").

## Verified finds

**Seven terms on six integers — a(15) through a(19) of A078502 and a(15),
a(16) of A074200 — and, riding on them, a(15)–a(19) of A093554 and a(15),
a(16) of A093553: fourteen new terms across four entries**, found
2026-09-06 by one campaign per family, engine v1 (round 8), no flags. The
first advance on A078502 since January 2003 and on A074200 since February
2004; the two rider entries had never been extended.

Each evidence file was re-verified from disk before this page was written,
by a harness that shares nothing with the launcher: N rebuilt as L(n)·x,
every value N/i ∓ 1 rebuilt and re-tested with sympy's BPSW, the run
re-derived from the bare definition on N (`lcml_reference.run_length_N`,
divisibility included), the stopper's factor re-multiplied, every
certificate re-verified by `huntlib.certificate.verify` and matched to its
own value, the ledger matched to the files, the riders' shift and the
least-claim floor read back. 6 files, 98 certificates, all green. Model
figures are from `lcml_model`, each scored in x at the find's own filter
from the term before it.

### A078502 — one campaign, 2026-09-06, 09:51–12:01

`python launch.py`, from a(13) = a(14) = 7,272,877,497,848,202,240. Forms
N/k − 1 = (L/k)·x − 1, so past the deterministic bound the certificate
route is BLS75 Theorem 15 on V + 1 = N/k, N factored once per find. Every
term is also **A093554 at the same index, minus one**.

#### a(15) = 143,479,704,870,546,258,614,400 — 09:52:06

- **run 15**: (N − k)/k prime for k = 1..15; the largest value is N − 1 =
  143,479,704,870,546,258,614,399 and the smallest N/15 − 1 =
  9,565,313,658,036,417,240,959. **stopper** N/16 − 1 =
  8,967,481,554,409,141,163,399 = 17 × 527,498,914,965,243,597,847.
- 15 `deterministic-mr` certificates: the last find here under the bound.
- **also settles**: A093554(15) = 143,479,704,870,546,258,614,399.
- **model**: from a(14), median x = 1.18e17 at filter 15; x / median = 3.37,
  E = 1.62. 21 seconds in, pool sizing included.
- N = 2⁷ · 3² · 5² · 7 · 11 · 13 · 101 · 49276804353013 (x =
  398,156,579,172,345,040 at L(15) = 360360).
- evidence: `evidence/A078502_a15_143479704870546258614400.json`

#### a(16) = 123,117,690,451,783,381,321,968,000 — 10:00:22

- **run 16**: the smallest value is N/16 − 1 =
  7,694,855,653,236,461,332,622,999. **stopper** N/17 − 1 =
  7,242,217,085,399,022,430,703,999 = 17 × 426,012,769,729,354,260,629,647.
- **certificates**: every value is past the deterministic bound; all 16 by
  **BLS75 Theorem 15**, every prime factor of N under the bound.
- **also settles**: A093554(16) = 123,117,690,451,783,381,321,967,999.
- **model**: from a(15), median x = 2.25e19; x / median = 7.6, E = 3.03 —
  the latest of the six against its model. 8.6 minutes in.
- N = 2⁷ · 3³ · 5³ · 7 · 11 · 13 · 17 · 23 · 2184319 · 333357181.
- evidence: `evidence/A078502_a16_123117690451783381321968000.json`

#### a(17) = 1,003,795,564,977,176,937,562,396,800 — 10:17:21

- **run 17**: the smallest value is N/17 − 1 =
  59,046,797,939,833,937,503,670,399. **stopper** N/18 − 1 =
  55,766,420,276,509,829,864,577,599 = 19 × 2,935,074,751,395,254,203,398,821.
- 17 BLS75 Theorem 15 certificates.
- **also settles**: A093554(17) = 1,003,795,564,977,176,937,562,396,799.
- **model**: from a(16), median x = 1.21e20; x / median = 0.68, E = 0.49.
  25.6 minutes in.
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
- **model**: from a(17), a(18)'s median x = 2.95e22; x / median = 0.145,
  E = 0.165 — early, and it carried a(19) with it. a(19) is not scored: it
  was never searched for. 2.10 hours in.
- N = 2¹³ · 3⁴ · 5⁴ · 7² · 11 · 13² · 17 · 19 · 23 · 59 · 251 · 12576703.
- evidence: `evidence/A078502_a18_52270101840951834355676160000.json`

`E` averages 1.33 over the four searched terms; x / median 3.37, 7.6, 0.68,
0.145.

**No bound past a(19).** The filter moved to n = 20 and the campaign was
stopped by hand 3 minutes 20 seconds later, inside the first n = 20 segment
(period 88, launch 3,801; 335 pending survivors in the checkpoint). No
segment closed, so nothing is claimed beyond monotonicity: a(20) ≥ a(19).

### A074200 — one campaign, 2026-09-06, 12:02–12:51

`python launch.py --family A074200`, from a(14) =
2,918,756,139,031,688,155,200. Forms N/k + 1 = (L/k)·x + 1, certificate
route BLS75 Theorem 1 on V − 1 = N/k. Every term is also **A093553 at the
same index, plus one**.

#### a(15) = 174,563,969,955,955,530,350,400 — 12:02:35

- **run 15**: (N + k)/k prime for k = 1..15; the largest value is N + 1 =
  174,563,969,955,955,530,350,401 and the smallest N/15 + 1 =
  11,637,597,997,063,702,023,361. **stopper** N/16 + 1 =
  10,910,248,122,247,220,646,901 = 17 × 641,779,301,308,660,038,053.
- 15 `deterministic-mr` certificates.
- **also settles**: A093553(15) = 174,563,969,955,955,530,350,401.
- **model**: from a(14), median x = 1.46e17; x / median = 3.32, E = 1.75.
  21 seconds in.
- N = 2⁶ · 3² · 5² · 7 · 11 · 13 · 12110387526081941.
- evidence: `evidence/A074200_a15_174563969955955530350400.json`

#### a(16) = 10,316,338,205,727,668,643,809,280 — 12:04:47

- **run 16**: the smallest value is N/16 + 1 =
  644,771,137,857,979,290,238,081. **stopper** N/17 + 1 =
  606,843,423,866,333,449,635,841 = 19 × 31,939,127,571,912,286,822,939.
- **certificates**: N straddles the bound — 13 `deterministic-mr` and 3
  **BLS75 Theorem 1** (k = 1, 2, 3, the values above 3.317e24).
- **also settles**: A093553(16) = 10,316,338,205,727,668,643,809,281.
- **model**: from a(15), median x = 2.26e19; x / median = 0.63, E = 0.49.
  2.5 minutes in.
- N = 2¹¹ · 3³ · 5 · 7² · 11 · 13 · 17 · 37 · 61 · 9349 · 14845133.
- evidence: `evidence/A074200_a16_10316338205727668643809280.json`

`E` averages 1.12 over the two; x / median 3.32, 0.63.

#### A bound: A074200 a(17) > 2,401,654,123,277,503,083,571,982,400

After a(16) the filter moved to n = 17 and the sweep ran 47 minutes more, to
the segment boundary at period 14,622 of the n = 17 wheel: x =
196,017,554,608,586,110,260, N = L(17)·x = 2,401,654,123,277,503,083,571,982,400,
every survivor below it classified and none reaching 17. So **no
N < 2.4017e27 has (N + k)/k prime for all k = 1..17** — the first bound of
any kind on A074200 at an open index, and A093553(17) exceeds it by one.
Above the deterministic bound the classification is a seven-base strong
probable-prime chain, which can only *lengthen* a run, never hide one, so
the bound stands. From a(16) the model had put a(17) under this cursor with
68%; it is late, not missing (below).

### The least-claim basis

Each find is a **first occurrence**: every x from the previous term's x at
that filter swept at the filter's forced unit and every survivor classified
in x order, with monotonicity in N the floor below. The basis is in every
evidence file — `swept_from_x`, `swept_from_N` / `swept_to_N` (`_m` in an
A074200 file), the filter, the wheel period, the sieve depth, the unit and
the monotone floor — under the engine keys
`a078502-v1-p1-seg32-pbd224-cpl37` and `a074200-v1-p1-seg32-pbd224-cpl37`.
The unit changes with the filter (2, 34, 2, 114 at n = 15..18) because the
forcing here is sporadic (README.md), and each is a coverage claim the
engines derive and refuse to be handed.

## The finds against the model

| | A078502 | A074200 | both |
|---|---|---|---|
| terms | 5 on 4 integers (+ 5 of A093554) | 2 (+ 2 of A093553) | **7** (14 with the riders) |
| searched draws | 4 | 2 | 6 |
| mean E | 1.33 | 1.12 | **1.26** |
| x / median | 0.145–7.6 | 0.63–3.32 | geometric mean 1.32 |
| certificates | 67: 15 `deterministic-mr`, 52 BLS75 thm 15 | 31: 28 `deterministic-mr`, 3 BLS75 thm 1 | 98 |
| campaign clock | 2.16 h | 0.82 h | 2.98 h |

Against the 1.12 of G11's twelve published terms, a disjoint set: the
intensity is right, the individual draws scatter over a factor of fifty,
and the pooled first occurrence came at 1.3× its median — inside the
1.9–2.5× the README told the reader to budget.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the evidence timestamps and the checkpoints, per filter, no flags. The
line is in x at that filter; a promotion re-denominates it (a(16) sits at
x = 1.7e20 on the n = 16 line and 1.0e19 on the n = 17 line).

| family, filter | line swept | wall clock | campaign rate | the engine there ([BENCHMARKS.md](BENCHMARKS.md)) |
|---|---|---|---|---|
| A078502 n = 15 | 2.0e17 | 21 s, pool sizing included | — | 2 s of device |
| A078502 n = 16 | 1.71e20 | 8.3 min | 3.44e17 x/s | 3.85e17 |
| A078502 n = 17 | 7.19e19 | 17.0 min | 7.05e16 | 6.63e16 |
| A078502 n = 18 | 4.18e21 | 100.4 min | 6.94e17 | 6.75e17 |
| A074200 n = 15 | 2.4e17 | 21 s | — | 2 s of device |
| A074200 n = 16 | 1.41e19 | 132 s, the engine rebuild included | — | one segment |
| A074200 n = 17 | 1.95e20 | 47.0 min | 6.93e16 | 6.63e16 |

Every timed phase is inside 11% of its benchmark, on both sides of it.

## The census

Counts per run length from each checkpoint, as printed in every `[STATUS]`
line (the finds included; A078502's rider is the single 18 — a filter-18
sweep caps a run at 18, and its nineteenth value was decided afterwards, on
N):

    A078502   8: 34731  9: 11069  10: 3496  11: 1090  12: 328  13: 133
              14: 55  15: 16  16: 3  17: 2  18: 1  19: 0
                                           near 14   survivors 744,699,973
    A074200   8: 17557  9: 5955  10: 2047  11: 740  12: 222  13: 87
              14: 27  15: 12  16: 4
                                           near 7    survivors 191,382,197

The counts are of *sieve survivors at the filter then running*, capped at
that filter, so they are comparable within a campaign and not across
filters. 936 million survivors
were classified across the two campaigns.

## What is open now

**The project is PAUSED — and one of its two families was stopped with its
next term an hour away.**

| entry | frontier (all this project's) | open next | searched empty below | resumes at | median from there | at the campaign's rate |
|---|---|---|---|---|---|---|
| A074200 | **a(16) = 10,316,338,205,727,668,643,809,280** | a(17) | N = 2.4017e27 | n = 17, period 14,622 | x = 3.73e20 (N = 4.6e27) | **43 minutes** |
| A093553 | the same integers + 1 | a(17) | + 1 | — rides A074200 | | |
| A078502 | **a(18) = a(19) = 52,270,101,840,951,834,355,676,160,000** | a(20) | — (no segment closed at n = 20) | n = 20, period 88 | x = 1.48e25 (N = 3.4e33) | most of a year |
| A093554 | the same integers − 1 | a(20) | | — rides A078502 | | |

**A074200 is the cheap one.** From its cursor, at the 6.9e16 x/s its n = 17
phase ran at, the model puts a(17) inside one hour with probability **61%**,
inside three with **92%** and inside a nine-hour night with 99.8%; a(18)
would follow at a median of about 12 hours (n = 18 runs ten times the line
rate of n = 17: 3 and 19 are forced there, unit 114). `python launch.py --family
A074200` continues from the checkpoint with no flags.

**A078502 is priced out.** The rider took a(19) with it, and a(20) opens on
the n = 20 line with a median of x = 1.5e25, N = 3.4e33 — four orders past
a(18)'s median in N. At the
n = 18 rate that is most of a year; the n = 20 rate has never been measured
(rule 5g: price it before offering the campaign there).

**Whoever resumes runs `python launch.py --selftest` and `python score.py`
first** (CLAUDE.md rule 2). Where each campaign stands is read with
`python launch.py --status` and `--status --family A074200`, which touch
nothing; the cursor they print is x at the current filter, and N = L(n)·x.
