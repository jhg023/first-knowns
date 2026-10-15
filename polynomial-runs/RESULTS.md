# RESULTS — polynomial-runs

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Nineteen terms: a(16)–a(21) of A165234, a(16)–a(20) of A230663,
a(16)–a(18) of A092120 and a(17)–a(21) of A347537.** Found 2026-10-08 to
2026-10-15 by one campaign per family, `python launch.py`,
`python launch.py --family A230663`, `--family A092120` and
`--family A347537`, no flags, on engine v2 with planner p1
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) rounds 1 and 2; the checkpoint
keys and the evidence's `engine` field read `v2-p1`). The first advance on
A092120 since Jens Kruse Andersen's of October 2008, on A165234 and A230663
since Daniel Suteu's of December 2024, and on A347537 since Bert
Dobbelaere's of May 2026.

Each evidence file was re-verified from disk on 2026-10-15 by a harness
that shares nothing with the launcher: the polynomials rebuilt from each
entry's %N line (2x² + p and x² + 3x + p for x = 0..n−1, p + 4m² for
m = 0..n, k⁴ + k³ + k² + k + p for k = 0..n−1); every value recomputed,
matched to the file and tested with sympy's `isprime`, p itself prime and
in its forced class (p ≡ 5 (mod 6) on A165234, p ≡ 1 (mod 6) on the other
three); the stopper — the value at x = n (m = n + 1 on A092120, k = n on
A347537) — composite, with the file's factor dividing it; the run field
and the value count against the index; the file name, `settles` and
`oeis_terms` against the integer; every value's certificate re-verified by
`huntlib.certificate.verify` and matched to its value; the `least_claim`
holding p, its filter at most n, and its `swept_from` boundary standing on
every lower open index found below it; each ledger matched to its files;
A230663's rider claims re-derived from the bare definition of A164926; the
indices checked against the OEIS data (the 2026-10-15 export, keyed by each
entry's %O offset) so that each family's finds continue its list and none
is already there; and `huntlib.evidence.gate_names` over the directory.
**19 files, 350 certificates, all green.** Every value of every find is
below 3.317×10²⁴ (the largest, p + 20⁴ + 20³ + 20² + 20 at A347537's
a(21), is 5.5×10²³), so every certificate is a deterministic Miller–Rabin
proof and nothing is `unproved`.

Every file also carries the three-way verification (huntlib's Miller–Rabin
chain, sympy's BPSW, a re-sieve by the CPU engine on another wheel), the
stopper with a prime factor, and a `least_claim`. Times below are the
ledger's, local; a *leg* is the wall clock from the previous find (or the
campaign's start) to this one, the find's verification and the promotion
to the next filter included. **Every index's line starts at p = 2**, so the
terms are not floors for one another and a campaign's finds need not
arrive in index order — two of the four did not.

### A165234 — one campaign, 2026-10-08 21:38 to 10-09 09:44 (10.42 h on the campaign's clock)

Least prime p such that 2x² + p is prime for x = 0..n−1 and composite for
x = n.

| n | a(n) | found | leg | filter |
|---|---|---|---|---|
| 16 | 1,137,967,817,134,079 | 10-08 21:38:59 | seconds | 16 |
| 18 | 55,195,219,699,044,611 | 10-08 21:39:09 | 10 s — found first, at filter 17 | 17 |
| 17 | 642,965,702,649,556,679 | 10-08 21:39:14 | 5 s | 17 |
| 19 | 535,093,320,640,267,373,531 | 10-08 21:59:10 | 19.9 min | 19 |
| 21 | 1,718,639,236,717,627,483,289 | 10-09 02:04:12 | 4.08 h — found first, at filter 20 | 20 |
| 20 | 10,595,142,219,289,312,569,299 | 10-09 04:27:43 | 2.39 h | 20 |

The table is in discovery order, and it is twice out of index order:
**a(18) < a(17)** and **a(21) < a(20)**. a(18) and a(21) each came at the
6th and 4th percentile of their rows (below, "The finds against the
model") and were met while the filter was still at the index below,
recorded as discoveries of a later index with the filter unmoved. After
a(20) the filter moved to n = 22, skipping the index found early, swept
three whole segments of 8.34×10²¹ to p = 4.2236×10²², and was 47% through
the fourth (160,438 of its 341,775 launches) when the owner stopped it at
09:44:26. The checkpoint's clock reads 10.42 h against 12.09 h of wall
clock from the first find to the stop, so the campaign was not running for
about 1.7 h of the legs after a(19).

### A230663 — one campaign, 2026-10-09 18:33 to 19:52 (1.32 h)

Least prime p such that x² + 3x + p is prime for x = 0..n−1 but not for
x = n.

| n | a(n) | found | leg | filter |
|---|---|---|---|---|
| 16 | 57,204,849,284,656,039 | 10-09 18:33:21 | seconds | 16 |
| 17 | 97,079,155,423,260,379 | 10-09 18:33:32 | 11 s | 17 |
| 18 | 15,197,452,440,079,259,719 | 10-09 18:34:57 | 85 s | 18 |
| 20 | 234,505,015,943,235,329,419 | 10-09 18:46:31 | 11.6 min — found first, at filter 19 | 19 |
| 19 | 1,568,805,168,304,652,737,369 | 10-09 19:51:07 | 64.6 min | 19 |

**a(20) is A164926(21) + 2**, the upper bound the README stated before the
run: 234,505,015,943,235,329,417 is A164926's a(21) (J. Waldvogel and Peter
Leikauf, 2009), and x² + 3x + (that + 2) = (x+1)² + (x+1) + that, so the
bound was always a candidate. The model put P(a(20) at or below it) at
0.12; the sweep proves no smaller prime has the run. After a(19) the filter
moved to n = 21 and the owner stopped the campaign at 19:52:03, 56 seconds
later, with 2,663 of the first segment's 512,512 launches swept.

### A092120 — one campaign, 2026-10-09 22:36 to 23:47 (1.17 h)

The first prime p such that p + 4m² is prime for m = 0..n but composite for
m = n + 1 (offset 0).

| n | a(n) | found | leg | filter |
|---|---|---|---|---|
| 16 | 121,599,916,198,138,753 | 10-09 22:36:47 | seconds | 16 |
| 17 | 29,212,993,482,338,347,147 | 10-09 22:38:48 | 2.0 min | 17 |
| 18 | 262,534,077,967,707,789,937 | 10-09 22:47:24 | 8.6 min | 18 |

a(16) is 1.2×10¹⁷, just past the entry's "all other terms after a(15) are
greater than 10^17". After a(18) the filter moved to n = 20 — a(19) = 163 is
the entry's own comment term — and swept 209,319 of the first segment's
384,384 launches in 59.6 minutes before the owner stopped it at 23:47:01.
That work is saved as the work cursor, with 13,882 survivors pending
classification, and claims nothing until the segment closes.

### A347537 — one campaign, 2026-10-09 23:47 to 10-15 07:39 (75.95 h on the campaign's clock)

The smallest prime p such that k⁴ + k³ + k² + k + p is prime for k = 0..n−1
but not for k = n.

| n | a(n) | found | leg | filter |
|---|---|---|---|---|
| 17 | 171,238,593,045,439,537 | 10-09 23:47:39 | seconds | 17 |
| 18 | 554,900,609,019,297,067 | 10-09 23:47:54 | 15 s | 18 |
| 19 | 21,156,574,635,417,749,893 | 10-09 23:50:42 | 2.8 min | 19 |
| 20 | 5,509,795,577,578,397,486,929 | 10-10 01:27:23 | 96.7 min | 20 |
| 21 | 545,605,440,824,324,681,493,499 | 10-15 07:39:21 | 126.2 h of wall clock; 74.3 h on the campaign's clock | 21 |

a(21) took 65 whole segments of 8.34×10²¹ at the filter for it, the one
long leg of the project. The campaign was not running for about 52 of the
126 hours between a(20) and a(21). The owner stopped it at 07:39:28, seven
seconds after the find, with nothing swept at the filter for a(22).

Evidence: `evidence/<entry>_a<n>_<a(n)>.json`, one per discovery, and one
ledger per family, `evidence/a<number>_discoveries.json`.

**What the early terms are worth.** A165234's a(16)–a(19), A230663's
a(16)–a(18) and a(20), A092120's a(16)–a(18) and A347537's a(17)–a(19)
took about 50 minutes between them. They stood since 2008 and 2024 because
nobody returned to these entries with a sieve, not because they were hard.
The hunt proper was five terms: A165234's a(20) and a(21) (one filter,
6.5 h of wall clock), A230663's a(19) (76 minutes at its filter),
A347537's a(20) (97 minutes) and a(21) (74 hours).

### The least-claim basis

Every file's `least_claim` is the sweep from p = 2: the campaign started
there, and the line below each filter's `swept_from` was classified by the
earlier filters, each at an index at most the find's, with every
survivor's run read to its end — so every prime below a(n) with a run of
at least the filter in force where it lies had its exact run read, and
none was a(n)'s. The exception zone, [2, sieve depth] at the opening
filter, was classified one at a time on the host before the first launch.
Every term is in its forced class, which is a theorem (README, "The
mathematics of the engine"). The wheel and the sieve depth at every filter
are the plan in [BENCHMARKS.md](BENCHMARKS.md) ("The plan at every opening
and the filters above it"); a prime the wheel declines is sieved instead.

The stopper bounds each run from above: the value one past the run is
composite and a prime factor of it is in the file — 541, 281, 43, 71, 41
and 79 at A165234's a(16)–a(21); 61, 43, 229, 297,592,363 and 101 at
A230663's a(16)–a(20); 107, 89 and 79 at A092120's a(16)–a(18); 359, 59,
29, 31 and 66,417,443 at A347537's a(17)–a(21) — so no find's run is
longer than its index. G9 pins the GPU stream to the CPU engine bit for bit
on populated windows, and every find was re-sieved by the CPU engine on
another wheel.

### A230663 and A164926

A find of A230663(n) settles A164926(n+1) = p − 2 when p − 2 is prime, and
otherwise proves A164926(n+1) > p − 2 (README, "A230663 and A164926 are
one problem, shifted"). **Nothing new rides on these five.** Only a(20)'s
p − 2 is prime, and it is A164926's a(21), already in that entry. The
other four give A164926(17) > 5.72×10¹⁶, A164926(18) > 9.71×10¹⁶,
A164926(19) > 1.52×10¹⁹ and A164926(20) > 1.57×10²¹, each below what is
already known: the entry lists a(17) to a(19), and euler-prime-runs swept
A164926's a(20) empty to 3.744×10²¹. Each bound is in its file as
`derived_bound`.

## The finds against the model

`E` is the number of primes with a(n)'s exact run that the model expected
between p = 2 and the a(n) that occurred; if the intensity is right it is a
draw of Exp(1), mean 1. The medians are `model_results.json`'s, written
before the run, every index from the bottom of the line.

| A165234 | E | quantile | a(n) / median | | A230663 | E | quantile | a(n) / median |
|---|---|---|---|---|---|---|---|---|
| a(16) | 0.29 | 0.25 | 0.19 | | a(16) | 3.30 | 0.96 | 17.3 |
| a(17) | 1.42 | 0.76 | 3.59 | | a(17) | 0.70 | 0.50 | 1.01 |
| a(18) | 0.06 | 0.06 | 0.01 | | a(18) | 1.49 | 0.77 | 3.82 |
| a(19) | 1.20 | 0.70 | 2.56 | | a(19) | 2.99 | 0.95 | 12.1 |
| a(20) | 0.86 | 0.58 | 1.43 | | a(20) | 0.13 | 0.12 | 0.05 |
| a(21) | 0.04 | 0.04 | 0.01 | | | | | |

| A092120 | E | quantile | a(n) / median | | A347537 | E | quantile | a(n) / median |
|---|---|---|---|---|---|---|---|---|
| a(16) | 0.56 | 0.43 | 0.68 | | a(17) | 0.78 | 0.54 | 1.25 |
| a(17) | 1.76 | 0.83 | 5.04 | | a(18) | 0.24 | 0.21 | 0.14 |
| a(18) | 0.79 | 0.55 | 1.26 | | a(19) | 0.23 | 0.21 | 0.15 |
| | | | | | a(20) | 0.64 | 0.47 | 0.87 |
| | | | | | a(21) | 1.14 | 0.68 | 2.28 |

Pooled over the nineteen draws, **E sums to 18.60, a mean of 0.98**, at
P = 0.49 under its Gamma(19, 1) law: the model's intensity is right on
these entries, with neither the lateness most families here have shown
(primorial-ladders, mean 1.62) nor primorial-runs' earliness (0.70). Per
family the means are 0.64 (A165234, six draws, P = 0.19), 1.72 (A230663,
five, P = 0.93), 1.04 (A092120, three, P = 0.60) and 0.61 (A347537, five,
P = 0.19), every one inside the scatter of its own count; the published
terms had scored 0.81 over 26 (G11). The scatter is the usual Exp(1)
scatter, wide at both ends: A165234's a(18) and a(21) and A230663's a(20)
at or below the 12th percentile, A230663's a(16) and a(19) at the 96th and
95th — 17 and 12 medians, which at the filters they lie in cost seconds and
an hour.

A note on the medians. A165234's row n + 1 and A092120's row n have the
same median to four figures (1.79×10¹⁷, 5.79×10¹⁸, 2.09×10²⁰): for odd q,
multiplication by 2 is a bijection, so {2x² : x = 0..n} and {4m² : m = 0..n}
kill the same number of residues of every prime, and the two families'
singular series agree. Before this revision the README's prediction tables
for A165234, A230663 and A092120 had been copied from an earlier run of the
model and did not match `model_results.json` (A230663's a(17), for one, was
stated below its a(16)); they now carry the file's figures, and BENCHMARKS.md
always had.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the ledger timestamps and the checkpoints, per filter, no flags. A
find is confirmed when its segment closes, so the line of a leg runs from
the filter's `swept_from` to the end of the find's segment (the next
filter's `swept_from`, or the coverage cursor for the last); the leg's wall
clock also holds the engine's build, the pool's sizing and the find's
verification. The prices are BENCHMARKS.md's device column, engine v2,
and for the two filters at n = 22 the reading of 2026-10-15 (below, "What
is open now").

| family, filter | line swept | clock | campaign rate | the engine at that filter |
|---|---|---|---|---|
| A165234 n = 16, 17 | to 7.03e17 | seconds and 15 s | — | 0.08 s and 1.3 s expected |
| A165234 n = 19 | 5.51e20 | 19.9 min | 4.61e17 p/s | 4.50e17 p/s (1.02) |
| A165234 n = 20, then 22 | 1.67e22 (2 segments), then 2.50e22 (3) and 47% of a fourth | 10.08 h on the campaign's clock (11.75 h wall) | — | 10.23 h priced at 9.46e17 and 1.51e18 p/s (1.01) |
| A230663 n = 16, 17 | to 1.37e17 | seconds and 11 s | — | 0.06 s and 0.9 s expected |
| A230663 n = 18 | 1.67e19 | 85 s | 1.97e17 p/s | 2.15e17 p/s (0.92, the build inside) |
| A230663 n = 19 | 1.57e21 | 76.2 min | 3.44e17 p/s | 3.34e17 p/s (1.03) |
| A230663 n = 21, stopped in segment 1 | 2,663 of 512,512 launches | 56 s | — | 9.20e17 p/s |
| A092120 n = 16 | to 1.56e17 | seconds | — | 1.3 s expected |
| A092120 n = 17 | 3.01e19 | 2.0 min | 2.49e17 p/s | 2.70e17 p/s (0.92, the build inside) |
| A092120 n = 18 | 2.36e20 | 8.6 min | 4.57e17 p/s | 4.48e17 p/s (1.02) |
| A092120 n = 20, stopped in segment 1 | 209,319 of 384,384 launches, 4.5e21 | 59.6 min | 1.27e18 p/s | 1.24e18 p/s (1.02) |
| A347537 n = 17, 18 | to 3.58e18 | seconds and 15 s | — | 0.7 s and 11 s expected |
| A347537 n = 19 | 1.01e20 | 2.8 min | 6.03e17 p/s | 6.07e17 p/s (0.99) |
| A347537 n = 20 | 8.34e21 (1 segment) | 96.7 min | 1.44e18 p/s | 1.42e18 p/s (1.01) |
| A347537 n = 21 | 5.42e23 (65 segments) | 74.3 h on the campaign's clock (126.2 h wall) | 2.03e18 p/s | 1.97e18 p/s (1.03) |

**Every filter that ran for more than two minutes swept at 0.99–1.03× its
price** on the campaign's own clock, on all four families and on legs from
a partial segment to sixty-five whole ones — the segment loop adds nothing
the kernel does not (the measurement rule 5g's checklist asks for before a
first campaign, which BENCHMARKS.md had listed as owed). The two legs at
0.92 are a minute or two long and carry the engine's build and the pool's
sizing; the filters of seconds are nothing but those. A092120's partial
segment is read as 54% of the segment's line in its 59.6 minutes, which
assumes the launches are equal in line. Two campaigns' clocks fall short of
their wall clocks (A165234 by 1.7 h, A347537 by 52 h): the campaign was not
running for that time, and the checkpoint's clock is the one the rate is
read on. The pool bound nowhere: BENCHMARKS.md prices the host at a fifth to
half a core at every filter that lasts, and a device that held its priced
rate for 74 hours was not being throttled by its host. What the record
cannot show is the first `[STATUS]` lines themselves, which were not kept;
the rates above are the acceptance test's substance, read off the evidence
instead.

## The census

Counts from each checkpoint, as printed in every `[STATUS]` line, keyed by
the INDEX whose exact run the prime has — the index whose term it would be
(the finds themselves are included). Every survivor of the sieve has its
run read to its end; indices from 8 up are counted.

    A165234   8: 164019  9: 59901  10: 22090  11: 7813  12: 3032  13: 1096
              14: 397  15: 162  16: 70  17: 31  18: 11  19: 3  20: 1  21: 1
              29: 1 (p = 29)               near 9    survivors 948,455,311
    A230663   8: 65708  9: 25639  10: 10130  11: 3993  12: 1555  13: 633
              14: 227  15: 90  16: 40  17: 12  18: 8  19: 1  20: 1
              39: 1 (p = 43)               near 15   survivors 205,732,021
    A092120   8: 4983  9: 2116  10: 924  11: 346  12: 155  13: 71  14: 32
              15: 15  16: 5  17: 1  18: 1  19: 1 (p = 163)
                                           near 3    survivors 204,513,741
    A347537   8: 801599  9: 279766  10: 97846  11: 34386  12: 11902  13: 4139
              14: 1497  15: 532  16: 165  17: 67  18: 24  19: 11  20: 6  21: 1
                                           near 9    survivors 5,833,877,567

The comment terms A165234's a(29) = 29, A230663's a(39) = 43 and A092120's
a(19) = 163 are counted where the host's exception zone met them. A prime
one condition short of the open term got a `[NEAR]` line and was verified
as a health check; everything else below the open term is a count and
nothing more. Successive counts fall by a factor of 2.2–2.9 on all four.
These are counts of *sieve survivors*, not densities: a filter-n sieve
removes a candidate whose later conditions have a small factor, so the
counts are comparable within a campaign and not across filters, and the
low indices are counted almost entirely on the opening filters' line.

## What is open now

**PAUSED — open to others.** Nothing is running. All four campaigns were
stopped by the owner inside the filter for their next term.

| entry | frontier (this project's) | open next | searched empty | filter | median from the cursor | P90 | at the open filter's rate | P(found) in a day / a week / 30 days |
|---|---|---|---|---|---|---|---|---|
| A165234 | **a(21) = 1,718,639,236,717,627,483,289**, with a(20) = 10,595,142,219,289,312,569,299 | a(22) | every open a(n), n ≥ 22, is > 42,235,549,386,438,297,970,080 (a(29) = 29 is the comment's) | n = 22, wheel to 53 wide | 1.20e25 | 8.05e25 | 91 days at 1.51e18 p/s | 3% / 12% / 29% |
| A230663 | **a(20) = 234,505,015,943,235,329,419**, with a(19) = 1,568,805,168,304,652,737,369 | a(21) | every open a(n), n ≥ 21, is > 1,590,719,867,556,427,277,670 (a(39) = 43 is the comment's) | n = 21, wheel to 53 wide | 1.86e23 | 1.26e24 | 2.3 days at 9.20e17 p/s | 33% / 75% / 97% |
| A092120 | **a(18) = 262,534,077,967,707,789,937**, and the comment's a(19) = 163 | a(20) | every a(n), n ≥ 20, is > 266,247,275,860,816,780,530 | n = 20, wheel to 53 wide | 2.98e23 | 2.10e24 | 2.8 days at 1.24e18 p/s | 31% / 71% / 95% |
| A347537 | **a(21) = 545,605,440,824,324,681,493,499** | a(22) | every a(n), n ≥ 22, is > 550,724,189,106,034,565,892,270 | n = 22, wheel to 53 wide | 1.59e25 | 9.47e25 | 52 days at 3.42e18 p/s | 3% / 15% / 38% |

(`poly_model` rerun 2026-10-15 in a scratch process from each coverage
cursor, nothing written. "Days" is the line from the cursor to the median
over the device rate at that filter: BENCHMARKS.md's for A230663 n = 21 and
A092120 n = 20, and for the two filters at n = 22, which the campaigns
reached and no table had priced, a reading of 2026-10-15 through the engine
API — the planned engine at the cursor's period, warmed, three rounds of
1.5 s of launches alternated with the n = 21 engine at the same p: A165234
n = 22 1.51×10¹⁸ p/s, 1.18× its n = 21 (which read 1.28×10¹⁸, its price
1.26); A347537 n = 22 3.42×10¹⁸ p/s, 1.69× its n = 21 (which read
2.03×10¹⁸, its campaign 2.03). The probabilities are the model's, read
straight: it scored a mean of 0.98 on the nineteen finds.)

**The four bounds are coverage, not work in flight, and each bounds every
open index of its family at once.** The classification reads every
survivor's run to its end, so when the filter for a(n) has swept to the
cursor, every prime below it with a run reaching that filter has had its
exact run read: every open index of A165234 from a(22) exceeds
4.2236×10²² (its a(29) = 29 sits in the exception zone, where the host met
it), of A230663 from a(21) exceeds 1.5907×10²¹ (its a(39) = 43 likewise), of
A092120 from a(20) exceeds 2.6625×10²⁰, and of A347537 from a(22) exceeds
5.5072×10²³. The
launches swept past those cursors (47% of a segment on A165234, 54% on
A092120, a sliver on A230663) are saved as the work cursor and claim nothing
until their segment closes.

**Two of the open terms are days, two are months**; that is where the
project stopped. A230663's a(21) and A092120's a(20) are about two and a
half days each to their medians and are the ones a resume would go for.
A165234's a(22) and A347537's a(22) are 91 and 52 days, and every index
past those is years.

**Resuming.** `python launch.py` (A165234), and `--family A230663`,
`--family A092120` or `--family A347537`, continue from the cursors above
with census, finds and pending survivors intact. **Whoever resumes runs
`python launch.py --selftest` and `python score.py` first** (CLAUDE.md rule
2). Owed before any of the four is offered again:

- the nineteen finds into the oracle's `FOUND`, so that G1b re-derives them
  from the definition and a fresh clone opens at the new frontier rather
  than at a(16), a(16), a(16) and a(17). The benchmark shapes, the drill
  filters and the end-to-end drills are keyed to each family's open index,
  so this moves them and was not done at the pause. Until it is, the
  frontier lives in the checkpoints (and in this file), and a fresh clone
  without them re-derives every term, which costs the 89 hours above;
- a frozen benchmark shape at each live filter (rule 5g): A165234 n = 22,
  A230663 n = 21, A092120 n = 20, A347537 n = 22 — none is a fingerprinted
  shape, and the two at n = 22 are priced only by the one reading above;
- the paired A/B of the planner's wheel against its neighbours at those
  filters, still owed from rounds 1 and 2 (BENCHMARKS.md, "What is still
  owed"): every one plans the full wheel to 53 at 256 periods on the wide
  record, measured against its neighbours at A165234 n = 21 only;
- for the month-long hunts, the six classes mod 210 with the wheel to 59
  ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) round 3): 1.31× on the device
  at A347537 n = 21, paid in a segment 59× as long. Under CLAUDE.md rule 5j
  it is admissible for an a(22) whose remaining search is weeks — the case
  priced there was 25 h of over-sweep against 44 days saved — and it is the
  owner's call; it needs a launcher v3 and is unmeasured at n = 22 and on
  the other three families.

Where each campaign stands is read with `python launch.py --status` (add
`--family A230663`, `A092120` or `A347537`), which touches nothing.

## The OEIS entries

None of the nineteen terms is entered yet: the 2026-10-15 export still ends
A165234, A230663 and A092120 at a(15) and A347537 at a(16), with the
comment terms A165234's a(29) = 29, A230663's a(39) = 43 and A092120's
a(19) = 163 as before. Nothing is submitted from inside the pipeline
(CLAUDE.md rule 5). `oeis_terms` in each evidence file is what to submit,
keyed by the entry's own index; A092120 is offset 0 and the other three
offset 1. Notes for the submission:

- each data line continues without a gap: A165234 through a(21),
  A230663 through a(20) and A347537 through a(21). The terms are not
  monotone — A165234's a(18) < a(17) and a(21) < a(20), A230663's
  a(20) < a(19) — which the entries' own data already shows lower down;
- A092120's data continues at a(16), past the entry's "all other terms after
  a(15) are greater than 10^17", which the new a(16) = 1.2×10¹⁷ confirms,
  and with a(16)–a(18) known the comment's a(19) = 163 now joins the data
  line too: a(0)–a(19) without a gap, a(20) open;
- A230663's a(20) equals A164926(21) + 2, which a comment on either entry
  may want to say.

The four bounds above (every open index of A165234 above 4.2236×10²², of
A230663 above 1.5907×10²¹, of A092120 above 2.6625×10²⁰, of A347537 above
5.5072×10²³) are the first at an open index of A347537 and replace the
entries' own "no other terms less than 10^12", "all other terms >
128865958933" and "greater than 10^17" on the other three.
