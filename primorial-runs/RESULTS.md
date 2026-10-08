# RESULTS — primorial-runs

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Eighteen terms: a(16)–a(20) of A257466, a(15)–a(19) of A257467 and
a(11)–a(18) of A258035.** Found 2026-10-05 to 2026-10-08 by one campaign per
family, `python launch.py`, `python launch.py --family A257467` and
`python launch.py --family A258035`, no flags, on engine v2 (the quad
window, [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) round 2) with planner
p1 — the checkpoint keys and the evidence's `engine` field read `v1`, the
launcher's version string not having been bumped for a change that leaves
the survivor stream identical. The first advance on any of the three since
Fred Schneider's own terms of
May to July 2015. On A258035 two of the eighteen are a correction rather
than an extension: the entry's listed a(11) and a(12) are its a(12) and
a(13) (below, "The erratum, confirmed").

Each evidence file was re-verified from disk on 2026-10-08 by a harness that
shares nothing with the launcher: the shifts pps, psq and pssq rebuilt from
the entries' definitions and checked against the entries' own small values;
the indices matched to the OEIS data (the 2026-10-08 export, keyed by each
entry's %O offset) so that each family's finds continue its list without a
gap; every value p + pps(1), …, p + pps(n) (psq and pssq on the other two)
recomputed and tested with sympy's `isprime`, p itself prime, and the run
read to its end from the bare definition and required to be **exactly** n;
the forced class (p ≡ 5 (mod 6) on A257466, p ≡ 1 (mod 6) on the other
two); the stopper at index n + 1 composite with the file's factor dividing
it; every value's certificate re-verified by `huntlib.certificate.verify`
and matched to its value, and the file's route counts to the certificates;
the `least_claim` range holding p, its filter at most n, its chain of
`swept_from` boundaries; each ledger matched to its files; and
`huntlib.evidence.gate_names` over the directory. **18 files, 309
certificates, all green**: 248 deterministic Miller–Rabin below 3.317e24,
58 BLS75 Theorem 1 on a completely factored N − 1 and 3 BLS75 Theorem 15 on
N + 1 with Lucas sequences. Nothing is `unproved`. The largest value proved
by certificate is p + psq(19) at A257467's a(19), 50 digits, by Theorem 15
with a 46-digit prime factor of N + 1 proved by its own Theorem 1 subproof.

Every file also carries the three-way verification (huntlib's Miller–Rabin
chain, sympy's BPSW, a re-sieve by the CPU engine on another wheel), the
stopper with a prime factor, and a `least_claim`. Times below are the
ledger's, local; a *leg* is the wall clock from the previous find (or the
campaign's start) to this one, the find's verification and the promotion to
the next filter included. **Every index's line starts at p = 2**, so the
terms are not floors for one another and a campaign's finds need not arrive
in index order (A258035's did not).

### A257466 — one campaign, 2026-10-05 22:34 to 10-06 00:47 (2.22 h)

Smallest prime p such that p + pps(1), …, p + pps(n) are all prime but
p + pps(n+1) is not, pps(n) the partial primorial sum.

| n | a(n) | found | leg | certificates |
|---|---|---|---|---|
| 16 | 7,614,454,456,747,601 | 10-05 22:34:22 | 8 s | 17 deterministic |
| 17 | 74,002,299,244,461,449 | 10-05 22:34:34 | 12 s | 18 deterministic |
| 18 | 847,950,953,314,167,809 | 10-05 22:35:48 | 74 s | 19 deterministic |
| 19 | 3,983,224,502,210,626,331 | 10-05 22:41:26 | 5.6 min | 19 deterministic, 1 BLS75 |
| 20 | 9,588,149,987,699,367,569 | 10-06 00:02:02 | 80.6 min | 19 deterministic, 2 BLS75 |

a(20) is only 2.4× a(19) and came in the first segment of its filter, at
the 7th percentile of the model's row. From a(19) on, the values at the top
of a run pass the deterministic bound (p + pps(19) is 8.0×10²⁴) and are
proved by BLS75 Theorem 1. After a(20) the campaign moved to the filter for
a(21) — the wheel to 53 on the wide record, a segment of 5.21×10²¹ — and
swept 113,323 of that segment's 7,862,580 launches in 45 minutes before the
owner stopped it at 00:47:18 with the coverage cursor at the end of a(20)'s
segment.

### A257467 — one campaign, 2026-10-06 00:47 to 10-07 07:47 (21.67 h on the campaign's clock)

Smallest prime p such that p + psq(1), …, p + psq(n) are all prime but
p + psq(n+1) is not, psq(n) the square of the primorial.

| n | a(n) | found | leg | certificates |
|---|---|---|---|---|
| 15 | 1,259,136,191,998,777 | 10-06 00:47:42 | seconds | 12 deterministic, 4 BLS75 |
| 16 | 44,356,817,686,613,317 | 10-06 00:48:05 | 23 s | 12 deterministic, 5 BLS75 |
| 17 | 509,682,898,193,066,953 | 10-06 00:50:41 | 2.6 min | 12 deterministic, 6 BLS75 |
| 18 | 67,450,871,725,109,583,937 | 10-06 04:47:56 | 3.95 h | 12 deterministic, 7 BLS75 |
| 19 | 418,446,268,390,828,120,903 | 10-07 07:46:57 | 26.98 h of wall clock | 12 deterministic, 8 BLS75 |

On this entry the shift alone passes the deterministic bound from the
twelfth (psq(12) = (37#)² is 5.5×10²⁵), so every find has its values from
p + psq(12) up proved by certificate whatever its height; a(18) and a(19) each needed
Theorem 15 (N + 1) on values whose N − 1 would not factor. The checkpoint's
clock reads 21.67 h against 30.99 h of wall clock between the first find
and the stop, so the campaign was not running for about nine of the hours
in a(19)'s leg; on the campaign's clock that leg is about 17.7 h. The owner
stopped it at 07:47:08, ten seconds after a(19) was confirmed, with the
coverage cursor at the end of a(19)'s segment and nothing swept at the
filter for a(20).

### A258035 — one campaign, 2026-10-07 18:48 to 10-08 09:28 (14.66 h)

Smallest prime p such that p + pssq(1), …, p + pssq(n) are all prime but
p + pssq(n+1) is not, pssq(n) the partial sum of the squares of the
primorials. Opened at index 11, below the entry's listed frontier, because
of the erratum (README, "The problem").

| n | a(n) | found | leg | certificates |
|---|---|---|---|---|
| 12 | 1,368,737,917 | 10-07 18:48:41 | 5 s — found first, at filter 11 | 12 deterministic, 1 BLS75 |
| 11 | 23,569,356,649 | 10-07 18:48:42 | with a(12) | 12 deterministic |
| 13 | 4,428,230,508,349 | 10-07 18:48:48 | 6 s | 12 deterministic, 2 BLS75 |
| 14 | 148,038,201,790,597 | 10-07 18:48:55 | 7 s | 12 deterministic, 3 BLS75 |
| 15 | 516,263,599,230,919 | 10-07 18:48:58 | 3 s | 12 deterministic, 4 BLS75 |
| 16 | 89,602,906,856,207,413 | 10-07 18:49:20 | 22 s | 12 deterministic, 5 BLS75 |
| 17 | 9,415,720,461,823,814,053 | 10-07 19:14:07 | 24.8 min | 12 deterministic, 6 BLS75 |
| 18 | 438,392,474,524,896,220,603 | 10-08 09:24:37 | 14.17 h | 12 deterministic, 7 BLS75 |

The table is in discovery order. The campaign's first find, one second
before its a(11), was a prime with a run of **12** met while sweeping at
filter 11 — the entry's listed a(11), recorded as a discovery of a(12)
while the filter stayed at 11; a(11) then landed in the same segment and
the filter moved to 13, skipping the index found early. **a(12) < a(11)**
is the non-monotonicity the entry's own a(9), a(10) and a(11) already show.
An earlier campaign on this family the same day, discarded with its
evidence before this one was started from p = 2, had found the same
a(11)–a(16). After a(18) the campaign swept 8,745 of the 387,600 launches
of the first segment at the filter for a(19) and was stopped by the owner
at 09:28:23, four minutes after the find, with the coverage cursor at the
end of a(18)'s segment.

Evidence: `evidence/<entry>_a<n>_<a(n)>.json`, one per discovery, and one
ledger per family, `evidence/a<number>_discoveries.json`.

**What the early terms are worth.** A257466's a(16)–a(19), A257467's
a(15)–a(17) and A258035's a(11)–a(17) took about 35 minutes between them,
most of it a(17) of A258035. They stood since 2015 because nobody returned
to these entries with a sieve, not because they were hard. The hunt proper
was four terms: a(20) of A257466 (81 minutes), a(18) and a(19) of A257467
(4 and about 18 hours) and a(18) of A258035 (14 hours).

### The erratum, confirmed

The README stated before the run, from the oracle's gate G1, that
A258035's listed a(11) = 1,368,737,917 has a run of exactly 12 and its
listed a(12) = 4,428,230,508,349 a run of exactly 13 under the entry's own
definition. The sweep from p = 2 settles what they are:

- **a(11) = 23,569,356,649**, the first prime whose run is exactly 11. It
  is larger than the listed value, which the sweep met first: 1,368,737,917
  is the first prime with a run of **at least** 11 (its run is 12, so it is
  a(12)), which is what the entry's author appears to have computed for
  that index — the clause "p + pssq(n+1) is not prime" dropped.
- **a(12) = 1,368,737,917** and **a(13) = 4,428,230,508,349**: the two
  listed integers, each at the index one higher than it is listed at.

The listed a(0)–a(10) all have exactly the run of their index (re-checked
from the definition by the harness above). The correction is in the
evidence like any discovery: `A258035_a11_23569356649.json`,
`A258035_a12_1368737917.json` and `A258035_a13_4428230508349.json`, each
with its `oeis_terms` saying which index the integer belongs at.

### The least-claim basis

Every file's `least_claim` is the sweep from p = 2: the campaign started
there, and the line below each filter's `swept_from` was classified by the
earlier filters, each at an index at most the find's, with every survivor's
run read to its end — so every prime below a(n) with a run of at least the
filter in force where it lies had its exact run read, and none was n. The
exception zone, [2, sieve depth] at the opening filter, was classified one
at a time on the host before the first launch. Every term is in its forced
class, which is a theorem (README, "The mathematics of the engine"). The
wheel and the sieve depth were planned per filter:

| entry | n | wheel primes past 2 and 3 | sieve depth |
|---|---|---|---|
| A257466 | 16 | to 23, 29, and 43 | 2^16 |
| A257466 | 17 | to 23, 29, 43, 47 | 2^16 |
| A257466 | 18 | to 23, 29, 37, 43, 47 | 2^15 |
| A257466 | 19 | to 37, 43, 47 | 2^15 |
| A257466 | 20 | to 47 | 2^15 |
| A257467 | 15, 16 | to 37 | 2^17 |
| A257467 | 17 | to 37, and 47 | 2^17 |
| A257467 | 18 | to 37, 43, 47 | 2^16 |
| A257467 | 19 | to 47 | 2^16 |
| A258035 | 11 (and 12) | 5, 7, 11, 13, 19, 23 | 2^20 |
| A258035 | 13 | to 29 | 2^18 |
| A258035 | 14 | to 31 | 2^17 |
| A258035 | 15 | to 37 | 2^16 |
| A258035 | 16 | to 41 | 2^17 |
| A258035 | 17, 18 | to 41, and 47 | 2^16 |

(A prime the wheel declines is not skipped: it is sieved instead.) The
stopper bounds each run from above: the value at index n + 1 is composite
and a prime factor of it is in the file — 6143, 2311, 8783, 389 and 433 on
A257466; 173, 31799, 1607, 12,139,764,160,229 and 1381 on A257467; 8,485,619,
1723, 71, 13,237,599,962,863, 773, 887, 179 and 1213 on A258035 — so no
find's run is longer than its index. G9 pins the GPU stream to the CPU
engine bit for bit on 29 populated windows, and every find was re-sieved by
the CPU engine on another wheel.

## The finds against the model

`E` is the number of primes with a run of exactly n the model expected
between p = 2 and the a(n) that occurred; if the intensity is right it is
a draw of Exp(1), mean 1. The medians are the ones the README stated before
the run (`model_results.json`), every index from the bottom of the line.

| A257466 | E | quantile | a(n) / median | | A257467 | E | quantile | a(n) / median |
|---|---|---|---|---|---|---|---|---|
| a(16) | 2.11 | 0.88 | 6.45 | | a(15) | 0.51 | 0.40 | 0.65 |
| a(17) | 1.29 | 0.73 | 2.79 | | a(16) | 0.63 | 0.47 | 0.89 |
| a(18) | 0.87 | 0.58 | 1.44 | | a(17) | 0.33 | 0.28 | 0.37 |
| a(19) | 0.31 | 0.27 | 0.28 | | a(18) | 0.99 | 0.63 | 1.58 |
| a(20) | 0.07 | 0.07 | 0.03 | | a(19) | 0.29 | 0.25 | 0.32 |

| A258035 | a(11) | a(12) | a(13) | a(14) | a(15) | a(16) | a(17) | a(18) |
|---|---|---|---|---|---|---|---|---|
| E | 0.96 | 0.01 | 0.44 | 0.55 | 0.12 | 0.45 | 1.17 | 1.58 |
| quantile | 0.62 | 0.01 | 0.36 | 0.42 | 0.11 | 0.37 | 0.69 | 0.79 |
| a(n) / median | 1.60 | 0.00 | 0.53 | 0.73 | 0.09 | 0.57 | 1.98 | 2.92 |

Pooled over the eighteen draws, **E sums to 12.68, a mean of 0.70**, at
P = 0.093 under its Gamma(18, 1) law: the terms came *earlier* than the
intensity says, where every other family in this repository has run late
(primorial-ladders: mean 1.62 over fourteen). Per family the means are
0.93 (A257466, five draws, P = 0.50), 0.55 (A257467, five, P = 0.14) and
0.66 (A258035, eight, P = 0.16). The published terms had scored 1.05 over
nineteen (G11), so the model is not biased by a factor the data can see; the
two squared entries ran early and A257466 on its median. Three draws sit at
or below the 10th percentile — a(20) of A257466 at 0.03 of its median (81
minutes against a priced 5.6 h), a(12) of A258035 at 0.01 (the listed
integer, which the README had placed at the 1.5% point of that row), and
a(15) of A258035 at 0.09 — and one at the 88th: a(16) of A257466, at 6.45
medians, which cost nothing at a filter that runs 5×10¹⁵ p/s. The campaigns
confirm the README's reading that the exact-run model has no systematic
lateness built in; what it has is the usual Exp(1) scatter, a factor of 3
either way at the quartiles.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the ledger timestamps and the checkpoints, per filter, no flags. A
find is confirmed when its segment closes, so the line of a leg runs from
the filter's `swept_from` to the end of the find's segment (the next
filter's `swept_from`, or the coverage cursor for the last); the leg's wall
clock also holds the engine's build, the pool's sizing, the exception zone
and the find's verification.

| family, filter | line swept | wall clock | campaign rate | the engine at that filter ([BENCHMARKS.md](BENCHMARKS.md)) |
|---|---|---|---|---|
| A257466 n = 16, 17 | 7.7e15 and 6.7e16 | 8 s and 12 s | — | 0.2 s and 3.5 s expected |
| A257466 n = 18 | 7.74e17 (10 segments) | 74 s | 1.04e16 p/s | 1.07e16 p/s |
| A257466 n = 19 | 4.79e18 (2 segments) | 5.6 min | 1.42e16 p/s | 1.44e16 p/s |
| A257466 n = 20 | 9.83e19 (1 segment) | 80.6 min | 2.03e16 p/s | 1.89e16 p/s |
| A257466 n = 21, stopped in segment 1 | 113,323 of 7,862,580 launches | 45 min | — | 2.60e16 p/s |
| A257467 n = 15, 16 | to 4.5e16 | seconds and 23 s | — | 0.9 s and 21 s expected |
| A257467 n = 17 | 5.02e17 (9 segments) | 2.6 min | 3.23e15 p/s | 3.29e15 p/s |
| A257467 n = 18 | 6.72e19 (28 segments) | 3.95 h | 4.72e15 p/s | 4.54e15 p/s |
| A257467 n = 19 | 3.93e20 (4 segments) | 26.98 h wall; ~17.7 h on the campaign's clock | 4.05e15 wall; ~6.2e15 running | 6.03e15 p/s |
| A258035 n = 11..16 | to 9.9e16 | 44 s for six terms | — | under a minute |
| A258035 n = 17 | 1.14e19 (5 segments) | 24.8 min | 7.68e15 p/s | 7.53e15 p/s |
| A258035 n = 18 | 4.29e20 (134 segments of 224 periods) | 14.17 h | 8.41e15 p/s | 8.24e15 p/s |
| A258035 n = 19, stopped in segment 1 | 8,745 of 387,600 launches | 3.8 min | — | 1.04e16 p/s |

**Every filter swept whole that lasted more than a minute ran at
0.97–1.08× its price**, on all three families and on segments from one to
134 — the campaign's wall clock is the device's time, so no per-launch cost
outside the kernel hides in the segment loop (the measurement rule 5g's
checklist asked for before the first campaign, and which BENCHMARKS.md had
listed as owed). The one leg that reads slow, A257467's n = 19 at 0.67× on
wall clock, is the leg the campaign was not running for nine hours of; on
the checkpoint's own clock it is 1.03×. The two stopped filters swept too
little of a segment to measure. The filters of seconds are the engine's
build and the pool's sizing, not a rate. The pool bound nowhere: the host
figures priced in BENCHMARKS.md are a fifth to half a core at every filter
that lasts, the pool is sized from a measurement at each filter as the
campaign reaches it, and a device that held its priced rate for 14 and 18
hours was not being throttled by its host.

## The census

Counts per run length from each checkpoint, as printed in every `[STATUS]`
line (the finds themselves are included at their run lengths). A run is
the number of leading shifts whose value is prime, read to its end for
every survivor of the sieve whose run reaches the filter plus a few.

    A257466   8: 22347  9: 9358  10: 3997  11: 1674  12: 745  13: 279  14: 134
              15: 66  16: 32  17: 8  18: 3  19: 2  20: 1
                                            near 7    survivors 234,513,605
    A257467   8: 404425  9: 176669  10: 81477  11: 32903  12: 11603  13: 3597
              14: 1008  15: 247  16: 47  17: 11  18: 1  19: 1
                                            near 10   survivors 1,434,950,055
    A258035   8: 295384  9: 127972  10: 58687  11: 23973  12: 8547  13: 2596
              14: 763  15: 194  16: 38  17: 10  18: 1
                                            near 16   survivors 1,084,784,999

A run one short of the open term got a `[NEAR]` line and was verified as a
health check; everything shorter is a count and nothing else. Each extra
condition costs a factor of 2.0–2.7 on A257466 through run 16, and on the
two squared entries a factor that grows with the run, 2.2 at run 9 to about
4 at run 16, because there each new value is a constant-sized number far
larger than p and its chance of being prime falls with the shift. These are
counts of *sieve survivors*, not densities: a filter-n sieve removes a
candidate whose later conditions have a small factor, so the counts are
comparable within a campaign and not across filters, and a run counted at
an index already settled is census, not a near miss (A257466's two runs of
19 are a(19) and one more prime with that exact run, counted).

## What is open now

**PAUSED — open to others.** Nothing is running. All three campaigns were
stopped by the owner inside the filter for their next term, seconds to 45
minutes after their last find.

| entry | frontier (this project's) | open next | searched empty | filter | median from the cursor | P90 | at the open filter's priced rate | P(found) in a day / a week / 30 days |
|---|---|---|---|---|---|---|---|---|
| A257466 | **a(20) = 9,588,149,987,699,367,569** | a(21) | every a(n), n ≥ 21, is > 103,916,373,257,455,048,290 | n = 21, wheel to 53 wide | 1.07e22 | 6.49e22 | 4.7 days at 2.60e16 p/s | 21% / 59% / 91% |
| A257467 | **a(19) = 418,446,268,390,828,120,903** | a(20) | every a(n), n ≥ 20, is > 461,167,336,941,368,557,500 | n = 20, wheel to 47 | 4.27e22 | 1.94e23 | 76 days at 6.40e15 p/s | 2% / 9% / 28% |
| A258035 | **a(18) = 438,392,474,524,896,220,603** | a(19) | every a(n), n ≥ 19, is > 440,747,276,254,476,331,140 | n = 19, wheel to 41, 47, 53 | 5.99e21 | 2.48e22 | 6.2 days at 1.04e16 p/s | 13% / 54% / 92% |

(`runs_model` rerun 2026-10-08 in a scratch process from each coverage
cursor, nothing written. "Days" is the line from the cursor to the median
over the device rate BENCHMARKS.md priced at that filter — which the
campaigns reproduced at every filter they swept whole. The probabilities
are the model's; it ran early on these eighteen finds and on the median
over the published ones, so they are read straight, with the Exp(1)
scatter above.)

**The three bounds are coverage, not work in flight, and each bounds
every open index of its family at once.** The classification reads every
survivor's run to its end, so when the filter for a(n) has swept to the
cursor, every prime below it with a run of n or more has had its exact run
read: a(21), a(22), … of A257466 all exceed 1.0392×10²⁰, a(20), a(21) of
A257467 exceed 4.6117×10²⁰, and a(19), a(20), a(21) of A258035 exceed
4.4075×10²⁰. The launches swept past those cursors (113,323 and 8,745 of a
segment) are saved as the work cursor and claim nothing until their segment
closes.

**Two of the open terms are a week, the third months**; that is why the
project stopped here. A257466's a(21) and A258035's a(19) are the two a
resume would go for. A257467's a(20) is 76 days to its median at the only
wheel its sparse killed sets admit (OPTIMIZATION_LOG.md, round 1), and its
a(21) — the last index under the ceiling on the values — is years.

**Resuming.** `python launch.py`, `python launch.py --family A257467` and
`python launch.py --family A258035` continue from the cursors above with
census and finds intact. **Whoever resumes runs `python launch.py
--selftest` and `python score.py` first** (CLAUDE.md rule 2). Owed before
any of the three is offered again:

- the eighteen finds into the oracle's `FOUND`, so that G1b re-derives them
  from the definition and a fresh clone opens at the new frontier rather
  than at a(16), a(15) and a(11). The benchmark shapes, the drill filters
  and the end-to-end drills are keyed to each family's open index, so this
  moves them and was not done at the pause. Until it is, the frontier lives
  in the checkpoints (and in this file), and a fresh clone without them
  re-derives every term, which costs the 39 hours above;
- a frozen benchmark shape at each live filter (rule 5g): A257466 n = 21,
  A257467 n = 20, A258035 n = 19 — each is priced in BENCHMARKS.md's table
  and none is a fingerprinted shape;
- a paired measurement at A258035's n = 19, whose wheel (to 41, then 47 and
  53 on a 145-period window) differs from both other families' and was
  swept for the engine's constants only in round 2's quad A/B, never for
  the planner's choice (round 1 confirmed the plan at A257466's n = 21
  only).

Where each campaign stands is read with `python launch.py --status` (add
`--family A257467` or `--family A258035`), which touches nothing.

## The OEIS entries

None of the eighteen terms is entered yet: the 2026-10-08 export still ends
A257466 at a(15), A257467 at a(14) and A258035 at its listed a(12). Nothing
is submitted from inside the pipeline (CLAUDE.md rule 5). `oeis_terms` in
each evidence file is what to submit, keyed by the entry's own index; all
three entries are offset 0. Notes for the submission: A258035's data line
needs a **correction**, not only an extension — a(11) becomes
23,569,356,649, the listed 1,368,737,917 and 4,428,230,508,349 move to
a(12) and a(13), and a(14)–a(18) follow; the existing terms a(0)–a(10) and
the entry's worked example for a(3) are right as they stand. The three
bounds above (every open index of A257466 above 1.0392×10²⁰, of A257467
above 4.6117×10²⁰, of A258035 above 4.4075×10²⁰) are the first at an open
index of any of the three entries.
