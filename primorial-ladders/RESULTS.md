# RESULTS — primorial-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Fifteen terms: a(16)–a(19) of A115785, a(17)–a(20) of A115786 and
a(14)–a(20) of A145743.** Found 2026-10-02 to 2026-10-05 by one campaign per
family, `python launch.py`, `python launch.py --family A115786` and
`python launch.py --family A145743`, no flags, on engine v1 with planner p1.
The first advance on A115785 and A115786 since Jens Kruse Andersen's terms
of February 2006, and on A145743 since Donovan Johnson's a(12)–a(13) of
November 2008.

Each evidence file was re-verified from disk on 2026-10-05 by a harness that
shares nothing with the launcher: the indices matched to the OEIS data (the
2026-10-05 export, keyed by each entry's %O offset) so that each family's
finds continue its published list without a gap; every condition recomputed
from the bare definition — p − prime(k)#, p + prime(k)# or m + 4·k² for
every k = 1..n — and tested with sympy's `isprime`, with p itself prime on
the primorial entries and m composite on A145743 (the file's witness
divides it); the forced class (p ≡ 1 and p ≡ 5 (mod 6), m ≡ 1 (mod 6));
the stopper at index n + 1 (a composite whose stored factor divides it, or
on A115785 a value below 2); every value's certificate re-verified by
`huntlib.certificate.verify` and matched to its value; the `least_claim`
range matched to the floor of its index; and each ledger matched to its
files. **14 files, 255 certificates, all green**: 233 deterministic
Miller–Rabin below 3.317e24 and 22 BLS75 Theorem 1 on a completely factored
N − 1. Nothing is `unproved`. The largest value proved by certificate is
p + prime(20)# at A115786's a(20), 27 digits.

Every file also carries the three-way verification (huntlib's Miller–Rabin
chain, sympy's BPSW, a re-sieve by the CPU engine on another wheel) and a
`least_claim`. Times below are the ledger's, local; a *leg* is the wall
clock from the previous find (or the campaign's start) to this one, its
verification and the promotion to the next filter included.

### A115785 — one campaign, 2026-10-02 20:28 to 10-03 10:50 (14.37 h)

Smallest prime p such that p − prime(k)# is prime for every k = 1..n. Each
index is its own line from prime(n)# + 2, so the table gives the term and
how far above its primorial it sits.

| n | a(n) | a(n) − prime(n)# | found | leg |
|---|---|---|---|---|
| 16 | 32,702,642,630,899,786,669 | 1.13e17 above 53# | 10-02 20:28:54 | 30 s |
| 17 | 1,923,178,323,603,035,931,703 | 4.18e17 above 59# | 10-02 20:30:04 | 70 s |
| 18 | 117,558,515,835,200,358,637,393 | 2.70e20 above 61# | 10-03 04:39:13 | 8.15 h |
| 19 | 7,858,467,306,309,706,402,625,473 | 1.46e20 above 67# | 10-03 08:53:56 | 4.25 h |

Every term lies within 0.4% above its primorial, as every published term
from a(13) does. a(19) is past the deterministic Miller–Rabin bound: p and
its values for k = 1..18 are proved by BLS75 Theorem 1, and
p − prime(19)#, the one value under the bound, by the deterministic test.
After a(19) the campaign moved to 71# + 2, covered the exception zone on
the host, and swept the filter for a(20) for 1.95 h — 317,291 of the
327,360 launches of its first segment — before the owner stopped it at
10:50:40 with that cursor saved.

### A115786 — one campaign, 2026-10-03 10:51 to 20:09 (9.29 h), from a(16) = 29,065,965,967,667

Smallest prime p such that p + prime(k)# is prime for every k = 1..n.

| n | a(n) | found | leg |
|---|---|---|---|
| 17 | 123,718,092,985,601 | 10-03 10:51:46 | 4 s |
| 18 | 238,468,632,242,449,727 | 10-03 10:52:27 | 41 s |
| 19 | 177,832,544,931,278,338,301 | 10-03 15:54:44 | 5.04 h |
| 20 | 276,111,714,233,825,559,827 | 10-03 20:03:19 | 4.14 h |

a(20) is only 1.55× a(19): the filter for a(20) found its term inside its
second segment. After a(20) the campaign swept the filter for a(21) for six
minutes, 16,611 of the 327,360 launches of a segment, and was stopped by
the owner at 20:09:16.

### A145743 — one campaign, 2026-10-03 20:09 to 10-05 17:33 (39.50 h on the campaign's clock), from a(13) = 91,450,844,347

Smallest composite number m such that m + 4·k² is prime for every
k = 1..n.

| n | a(n) | found | leg |
|---|---|---|---|
| 14 | 955,236,815,527 | 10-03 20:09:39 | under 10 s |
| 15 | 118,059,306,695,257 | 10-03 20:09:44 | 5 s |
| 16 | 48,192,095,115,862,063 | 10-03 20:09:52 | 8 s |
| 17 | 48,192,095,115,862,063 | (the same integer) | — |
| 18 | 754,953,104,966,780,647 | 10-03 20:10:08 | 16 s |
| 19 | 306,052,304,501,173,404,673 | 10-03 20:28:37 | 18.5 min |
| 20 | 86,871,442,473,592,036,108,753 | 10-05 17:32:42 | 45.07 h of wall clock |

**a(16) = a(17)**: m + 4·17² is prime as well and m + 4·18² is divisible by
71, so one integer settles two indices, as 143473 settles a(8)–a(10) in the
published list. It is one evidence file,
`A145743_a16_48192095115862063.json`, whose `oeis_terms` lists both. Every
value in this family is under the deterministic bound. The entry's comment
"There is no further term up to 5\*10^8" was already behind its own a(12);
the campaign swept from a(13) + 1 and relied on nothing. The checkpoint's
clock reads 39.50 h against 45.40 h of wall clock between the first line
and the stop, so the campaign was not running for about six of the hours in
a(20)'s leg. After a(20) it swept the filter for a(21) for a minute and
was stopped by the owner at 17:33:51.

Evidence: `evidence/<entry>_a<n>_<a(n)>.json`, one per discovery, and one
ledger per family, `evidence/a<number>_discoveries.json`.

**What the early terms are worth.** A115785's a(16)–a(17), A115786's
a(17)–a(18) and A145743's a(14)–a(18) took under four minutes between them.
They stood since 2006 and 2008 because nobody returned to these entries,
not because they were hard. The hunt proper was six terms: a(18) and a(19)
of A115785, a(19) and a(20) of A115786, and a(19) and a(20) of A145743.

### The least-claim basis

On A115785 each file's `least_claim` is the sweep from prime(n)# + 2 — the
least p for which p − prime(n)# can be prime — to a(n) under the filter of
index n, with the 2¹⁵–2¹⁷ integers of the exception zone above the floor
classified one at a time on the host. On the other two it is the sweep
from a(n−1) + 1: the line up to the end of the segment the previous term
was found in was classified by the previous filter with every survivor's
run read to that filter plus six, and the new filter's own sweep starts at
that boundary (`swept_from`, with `carried` saying so). Every term is in
its forced class, which is a theorem (README, "the mathematics of the
engine"). The wheel and the sieve depth were planned per filter:

| entry | n | wheel primes past 2 and 3 | sieve depth |
|---|---|---|---|
| A115785 | 16 | to 31, and 47 | 2^17 |
| A115785 | 17 | to 37, and 47 | 2^16 |
| A115785 | 18 | to 47, without 41 | 2^16 |
| A115785 | 19 | to 47 | 2^15 |
| A115786 | 17 | to 31, and 47 | 2^16 |
| A115786 | 18 | to 37, and 47 | 2^15 |
| A115786 | 19 | to 47, without 41 | 2^15 |
| A115786 | 20 | to 47 | 2^15 |
| A145743 | 14 | to 29 | 2^17 |
| A145743 | 15 | to 31 | 2^16 |
| A145743 | 16 (and 17) | to 37 | 2^15 |
| A145743 | 18 | to 43 | 2^16 |
| A145743 | 19 | to 47 | 2^15 |
| A145743 | 20 | to 53 | 2^15 |

(A prime the wheel declines is not skipped: it is sieved instead.) The
stopper bounds each run from above: on A115786 and A145743 the value at
index n + 1 is composite and its factor is in the file (401, 39847, 335477
and 181; 53, 131, 71, 96221, 43 and 2739181), and on A115785 the value
p − prime(n+1)# is negative, which is why a term of that entry can never
settle a second index. G9 pins the GPU stream to the CPU engine bit for bit
on 29 populated windows, and every find was re-sieved by the CPU engine on
another wheel.

## The finds against the model

`E` is the number of hits the model expected between the floor the sweep
started at (prime(n)# + 2 on A115785, a(n−1) + 1 elsewhere) and the term
that occurred. If the intensity is right it is a draw of Exp(1), mean 1.
The medians are the model's from that same floor; on the two monotone
families the table written before the run (README, `model_results.json`)
conditioned every row on the published frontier term, the only floor it
had, so its later rows are replaced here by medians from the real term
before each.

| A115785 | E | quantile | offset above prime(n)# / median offset |
|---|---|---|---|
| a(16) | 1.57 | 0.79 | 2.32 |
| a(17) | 0.21 | 0.19 | 0.30 |
| a(18) | 4.23 | 0.99 | 6.36 |
| a(19) | 0.08 | 0.08 | 0.11 |

| A115786 | E | quantile | a(n) / median | | A145743 | E | quantile | a(n) / median |
|---|---|---|---|---|---|---|---|---|
| a(17) | 0.03 | 0.03 | 0.01 | | a(14) | 0.30 | 0.26 | 0.27 |
| a(18) | 0.60 | 0.45 | 0.80 | | a(15) | 0.83 | 0.56 | 1.38 |
| a(19) | 4.97 | 0.99 | 19.7 | | a(16) | 3.81 | 0.98 | 16.6 |
| a(20) | 0.21 | 0.19 | 0.50 | | a(18) | 0.27 | 0.24 | 0.24 |
| | | | | | a(19) | 1.26 | 0.72 | 2.67 |
| | | | | | a(20) | 4.34 | 0.99 | 16.1 |

(a(17) of A145743 is not a draw: it was not searched for.) Pooled over the
fourteen draws, **E sums to 22.72, a mean of 1.62**, at P = 0.980 under its
Gamma(14, 1) law: the terms came later than the intensity says, as the
published terms did (G11: 33.3 over 21). Per family the means are 1.52
(A115785, four draws, P = 0.86), 1.45 (A115786, four, P = 0.83) and 1.80
(A145743, six, P = 0.96). The scatter is what moved the clocks: four of
the fourteen draws landed at the 98th–99th percentile — a(18) of A115785
took 8.15 h where the table had priced 1.9 h, a(19) of A115786 5 h where
it had priced 37 min, and a(20) of A145743 came at sixteen times its
median — and a(19) of A115785, priced at 44 h and budgeted at a week, came
in 4.25 h at the 8th percentile. Before the run the README read A115785
as 2.4× late and A115786 as early (mean 0.47 over seven published draws);
the new draws do not separate the families, and all three are best read
as about 1.5–2× late.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the ledger timestamps and the checkpoints, per filter, no flags. A
find is confirmed when its segment closes, so the line of a leg runs to the
end of the find's segment; the leg's wall clock also holds the engine's
build, the pool's sizing, the exception zone and the find's verification.
For a filter a campaign was stopped in, the line is the launches swept as a
fraction of the segment, which is a launch count and not a measured line.

| family, filter | line swept | wall clock | campaign rate | the engine at that filter ([BENCHMARKS.md](BENCHMARKS.md)) |
|---|---|---|---|---|
| A115785 n = 16, 17 | 1.1e17 and 4.2e17 above the floors | 30 s and 70 s | — | 16 s and 5.3 min expected |
| A115785 n = 18 | 2.7e20 | 8.15 h | 9.2e15 p/s | 9.27e15 p/s |
| A115785 n = 19 | 1.97e20 (two segments) | 4.25 h | 1.29e16 p/s | 1.28e16 p/s |
| A115785 n = 20, stopped in segment 1 | 0.97 of a segment of 9.84e19, by launches | 1.95 h | 1.36e16 p/s | 1.11e16 p/s |
| A115786 n = 17, 18 | to 2.4e17 | 4 s and 41 s | — | 7 s and 2 min expected |
| A115786 n = 19 | 1.78e20 | 5.04 h | 9.8e15 p/s | 1.00e16 p/s |
| A115786 n = 20 | 1.97e20 (two segments) | 4.14 h | 1.32e16 p/s | 1.35e16 p/s |
| A115786 n = 21, stopped in its first segment | 0.051 of a segment of 9.84e19, by launches | 6 min | 1.4e16 p/s | 1.11e16 p/s |
| A145743 n = 14..18 | to 7.5e17 | 34 s for five terms | — | seconds each |
| A145743 n = 19 | 3.9e20 | 18.5 min | 3.5e17 m/s | 2.81e17 m/s |
| A145743 n = 20 | 8.86e22 (seventeen segments of 5.21e21) | 39.2 h on the campaign's clock | 6.3e17 m/s | not priced |

The filters that were priced and swept whole ran at 0.98–1.01× their
price on the primorial entries, and A145743's n = 19 at 1.25× (one
segment, launch-bound at its edges). Two things the table shows and does
not settle. **The two stopped filters read 1.2–1.3× above their price**,
on a launch fraction: launches are not equal shares of a segment's line
elsewhere in this repository (a partial segment counted in launches has
overstated the line by 1.1–1.3×), so that is probably the accounting and
not the engine, and neither campaign claims coverage from it. **A145743's
n = 20 was never priced**: BENCHMARKS.md stops at n = 19 for that family,
because the model's clock to a(19) was 22 minutes and a(20) was not
expected to take two days. The campaign's own sizing ran it (the pool is
measured at the filter at every promotion), and the rate it held is the
only measurement at that filter.

## The census

Counts per run length from each checkpoint, as printed in every `[STATUS]`
line (the finds themselves are included at their run lengths). A run is
the number of leading conditions k = 1, 2, … that hold for a survivor of
the sieve.

    A115785   8: 56736  9: 20751  10: 7468  11: 2745  12: 1037  13: 384
              14: 119  15: 49  16: 13  17: 9  18: 1  19: 1
                                           near 8    survivors 1,195,560,323
    A115786   8: 122802  9: 49898  10: 20076  11: 8157  12: 3395  13: 1371
              14: 569  15: 223  16: 105  17: 31  18: 18  19: 1  20: 1
                                           near 17   survivors 743,181,031
    A145743   8: 575313  9: 206572  10: 74475  11: 27090  12: 9797  13: 3506
              14: 1225  15: 420  16: 179  17: 60  18: 26  19: 11  20: 1
                                           near 17   survivors 3,583,800,098

A run one short of the open term got a `[NEAR]` line and was verified as a
health check; everything shorter is a count and nothing else. Each extra
condition costs a factor of about 2.4–3 through run 15 on all three
families. These are counts of *sieve survivors*, not densities: a filter-n
sieve removes a candidate whose later conditions have a small factor, so
the counts are comparable within a campaign and not across filters, and on
A115785 each filter's counts come from a different line (a run of 18 above
61# and a run of 18 above 67# are not the same event: the second is a
near miss).

## What is open now

**PAUSED — open to others.** Nothing is running. All three campaigns were
stopped by the owner inside the filter for their next term, minutes to two
hours after their last find.

| entry | frontier (this project's) | open next | searched empty | filter | median from the cursor | P90 | at the open filter's rate | P(found) in a day / a week / 30 days |
|---|---|---|---|---|---|---|---|---|
| A115785 | **a(19) = 7,858,467,306,309,706,402,625,473** | a(20) | nothing claimed above 71# + 2 | n = 20, wheel to 47 | 4.32e22 above 71# | 1.47e23 above 71# | 45 days at 1.11e16 p/s | 2% / 11% / 37% |
| A115786 | **a(20) = 276,111,714,233,825,559,827** | a(21) | a(21) > 374,467,877,596,391,268,690 | n = 21, wheel to 47 | 6.74e21 | 3.63e22 | 6.6 days at 1.11e16 p/s | 15% / 51% / 86% |
| A145743 | **a(20) = 86,871,442,473,592,036,108,753** | a(21) | a(21) > 89,033,580,959,683,202,202,360 | n = 21, wheel to 53 | 3.59e23 | 1.43e24 | 5.0 days at 6.3e17 m/s | 16% / 60% / 93% |

(`primorial_model` rerun 2026-10-05 in a scratch process, nothing written.
"Days" is the line from the cursor to the median over the rate in the last
column: the benchmark's at n = 20 and n = 21 on the primorial entries, and
on A145743 the rate the campaign held at n = 20, the nearest measurement
there is. The probabilities are the model's and it has run 1.5–2× late on
these families, so they are optimistic. A115785's
a(21) is above 73# with a median offset of 1.45e24, years at this rate.)

**The two bounds are coverage, not work in flight.** On the monotone
families the classification reads every survivor's run past the filter, so
the segment a find lands in is settled for the next index too, and the
coverage cursor stands at its end: a(21) of A115786 is greater than
3.7447e20 and a(21) of A145743 greater than 8.9034e22. The launches swept
past those cursors (16,611 and 2,882 of a segment) and A115785's 317,291
are saved as the work cursor and claim nothing until their segment closes.

**Each open term is a week or more**, A115785's months; that is why the
project stopped here. A115786's a(21) and A145743's a(21) are the two a
resume would go for.

**Resuming.** `python launch.py`, `python launch.py --family A115786` and
`python launch.py --family A145743` continue from the cursors above with
census and finds intact. **Whoever resumes runs `python launch.py
--selftest` and `python score.py` first** (CLAUDE.md rule 2). Owed before
any of the three is offered again:

- the fifteen finds into the oracle's `FOUND`, so that G1b re-derives them
  from the definition and a fresh clone opens at the new frontier rather
  than at a(16), a(17) and a(14). The benchmark shapes and the end-to-end
  drills are keyed to each family's open index, so this moves them and was
  not done at the pause. Until it is, the frontier lives in the checkpoints
  (and in this file), and a fresh clone without them re-derives every term,
  which costs the 63 hours above;
- a frozen benchmark shape at each live filter (rule 5g): A115785 n = 20,
  A115786 n = 21, A145743 n = 21 — and a priced row for A145743 at n = 20
  and n = 21, which BENCHMARKS.md does not have;
- a paired measurement at those filters in line swept rather than launches,
  which settles the 1.2–1.3× the stopped filters read;
- a look at A145743's rung list: its checkpoint records `a(21) Q1` as
  passed with the coverage cursor at 8.90e22, where the model run from
  that cursor puts the first quartile of a(21) at 1.84e23. The label was
  not traced at the pause; if it was logged against the ladder of an
  earlier frontier, the real rung will pass without its `[RUNG]` line.

Where each campaign stands is read with `python launch.py --status` (add
`--family A115786` or `--family A145743`), which touches nothing.

## The OEIS entries

None of the fifteen terms is entered yet: the 2026-10-05 export still ends
A115785 at a(15) (revision #13), A115786 at a(16) (#12) and A145743 at
a(13) (#3). Nothing is submitted from inside the pipeline (CLAUDE.md rule
5). `oeis_terms` in each evidence file is what to submit, keyed by the
entry's own index; all three entries are offset 1. Notes for the
submission: A145743's a(16) and a(17) are the same integer and are entered
twice, as a(8)–a(10) are; its comment "There is no further term up to
5\*10^8" is superseded; and the two bounds above (a(21) > 3.7447e20 on
A115786, a(21) > 8.9034e22 on A145743) are the first at an open index of
either entry.
