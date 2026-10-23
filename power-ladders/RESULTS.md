# RESULTS — power-ladders

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

## Verified finds

**Eleven terms: a(10) and a(11) of A229626, and a(9) through a(11) of
A229627, of A229630 and of A229902.** Found 2026-10-15 to 2026-10-23 by one
campaign per family — `python launch.py`, `python launch.py --family
A229627`, `--family A229630` and `--family A229902`, no flags — on engine
v1 with planner p1 ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) rounds 1–4;
the checkpoint keys and the evidence's `engine` field read `v1-p1`), except
A229630's a(11), which its campaign found on plan p3, the semiprime wheel
with the cofactor sieve (rounds 5 and 6; `v1-p3`). The first advance on
A229630 since Charles R Greathouse IV's of October 2013, and on A229626,
A229627 and A229902 since Tyler Busby's of January 2023.

Each evidence file was re-verified from disk on 2026-10-23 by a harness
that shares nothing with the launcher: the forms rebuilt from each entry's
%N line (2·m^k − 1 for k = 1..n on A229626 and A229630, q prime and
2·q^k − 1 on A229627, 19·m^k + 1 on A229902); every value recomputed,
matched to the file and tested with sympy's `isprime`; the domain
re-derived (q prime by `isprime`, m a semiprime by `factorint`, matching
the file's two factors, and A229902's m ≡ 0 (mod 10)); the term's
factorization — the basis of every certificate — multiplied back with each
factor tested prime; the stopper, the value at k = n + 1, recomputed,
composite, with the file's factor dividing it; the run, the value count,
the file name, `settles` and `oeis_terms` against the index and the
integer; every certificate re-verified by `huntlib.certificate.verify` and
matched to its value; the `least_claim` holding the integer with a filter
at most n and a floor that is a(n − 1); each ledger row matched to its
file; the indices checked against the OEIS data (the 2026-10-20 export) so
that each family's finds continue its list and none is already there, bar
A229902's a(9), which is its listed a(8) by construction; and
`huntlib.evidence.gate_names` over the directory. **11 files, 114
certificates, all green**: 15 deterministic Miller–Rabin proofs (the values
under 3.317×10²⁴ — the k = 1 and k = 2 values of the smallest terms and
A229627's q itself), 72 BLS75 Theorem 15 proofs on the 2·m^k − 1 and
2·q^k − 1 values (the value plus one is 2·m^k, completely factored) and 27
Theorem 1 proofs on the 19·m^k + 1 values (the value less one is 19·m^k).
The largest value proved is A229627's 2·q^11 − 1 at a(11), 232 digits; its
stopper has 253. Nothing is `unproved`.

Every file also carries the three-way verification (huntlib's Miller–Rabin
chain, sympy's BPSW, a re-sieve by the CPU engine on another wheel), the
stopper with a prime factor, and a `least_claim`. Times are the ledger's,
local. The ladders nest, so every find is a floor for the next index of its
family and the finds arrive in index order.

### A229626 — one campaign, 2026-10-15 23:14 to 10-16 23:39 (14.89 h on the campaign's clock)

Smallest m such that 2·m^k − 1 is prime for k = 1, 2, …, n.

| n | a(n) = m | found | filter | stops at | m factored |
|---|---|---|---|---|---|
| 10 | 10,680,411,518,375,521 | 10-15 23:14:49 | 10 | 2·m^11 − 1, divisible by 157 | 13 · 17 · 48,327,653,929,301 |
| 11 | 26,985,725,415,370,251,655 | 10-16 23:37:49 | 11 | 2·m^12 − 1, divisible by 3,535,209,047 | 5 · 23 · 31² · 2,503 · 83,177 · 1,172,867 |

a(10) came in the campaign's first minute, as the model had priced it
(a median clock of 44 s). The campaign's clock reads 14.89 h against about
24 h of wall clock from the first find to the stop, so it was not running
for part of 10-16. After a(11) the filter moved to n = 12 and the owner
stopped the campaign at the boundary of the segment that held a(11), with
nothing of the n = 12 line swept (831 launches of the open segment's
3,762,990, which claim nothing).

### A229627 — one campaign, 2026-10-17 01:58 to 10-18 13:13 (35.25 h)

Smallest prime q such that 2·q^k − 1 is prime for k = 1, 2, …, n.

| n | a(n) = q | found | filter | stops at |
|---|---|---|---|---|
| 9 | 915,805,778,084,569 | 10-17 01:58:23 | 9 | 2·q^10 − 1, divisible by 17 |
| 10 | 691,680,697,554,493,219 | 10-17 02:00:37 | 10 | 2·q^11 − 1, divisible by 389 |
| 11 | 1,002,522,190,109,444,576,389 | 10-18 05:44:17 | 11 | 2·q^12 − 1, divisible by 22,807 |

The entry's comment "a(9) > 3·10¹³ (Tyler Busby, Jan 14 2023)" stands:
a(9) is 9.2×10¹⁴, and the campaign's own sweep from a(8) = 1,095,265,755,949
is what the claim rests on. After a(11) the filter moved to n = 12, one
segment of it closed (q = 1.9063×10²¹ to 2.8594×10²¹), and the owner
stopped the campaign at launch 58,303 of the next segment's 174,096.

### A229630 — one campaign, 2026-10-18 13:24 to 10-22 15:23 (92.35 h on the campaign's clock)

Smallest semiprime m such that 2·m^k − 1 is prime for k = 1, 2, …, n.

| n | a(n) = m | found | filter | plan | stops at | m = p·q |
|---|---|---|---|---|---|---|
| 9 | 687,860,415,949 | 10-18 13:24:25 | 9 | p1 | 2·m^10 − 1, divisible by 577 | 7 · 98,265,773,707 |
| 10 | 228,902,892,109,166,911 | 10-18 13:39:41 | 10 | p1 | 2·m^11 − 1, divisible by 97 | 17 · 13,464,876,006,421,583 |
| 11 | 727,008,393,707,791,166,119 | 10-22 13:36:43 | 11 | p3 | 2·m^12 − 1, divisible by 127 | 751 · 968,053,786,561,639,369 |

**a(9) is A229626's a(9)**: the least m with a run of nine, 687,860,415,949,
is 7 times a prime, so the least semiprime with a run of nine is the same
integer — which is why the campaign met it 15 minutes in, at the 0.6th
percentile of the model's row (the model's semiprime density does not know
that the unrestricted a(9) is a semiprime). The n = 11 line was swept on
plan p1 (the v1 wheel) from a(10) to m = 5.563×10¹⁹, where the owner
stopped it on 2026-10-19 for round 5; the campaign then adopted plan p2
(the semiprime wheel, 3.69x) and on 2026-10-20 plan p3 (the cofactor
sieve, 1.30x more), each adoption re-sweeping the open segment from its
start on the new plan (rounds 5 and 6, and OPTIMIZATION.md 2.15), and found
a(11) on p3. Its evidence file's `least_claim` therefore starts at the
adoption boundary, 55,630,773,412,498,058,775: the file's `carried` note
calls the line below it "classified by the previous filter", the
launcher's wording for a carried boundary, and here that line was
classified by the previous *plan* at the same filter, n = 11 — the claim
is the same. After a(11) the filter moved to n = 12 and the owner stopped
the campaign at the boundary of the segment that held a(11), with the open
n = 12 segment at launch 75,465 of 518,608.

The campaign's clock reads 92.35 h against 98 h of wall clock from the
first find to the stop; the difference is the two adoption restarts.

### A229902 — one campaign, 2026-10-22 15:23 to 10-23 09:39 (18.26 h)

Smallest m such that 19·m^k + 1 is prime for k = 1, 2, …, n.

| n | a(n) = m | found | filter | stops at | m factored |
|---|---|---|---|---|---|
| 9 | 1,944,616,927,560 | 10-22 15:23:49 | 9 | 19·m^10 + 1, divisible by 23 | 2³ · 3 · 5 · 41 · 157 · 2,517,499 |
| 10 | 314,565,633,745,874,820 | 10-22 15:27:53 | 10 | 19·m^11 + 1, divisible by 71 | 2² · 3² · 5 · 449 · 1,803,101 · 2,158,601 |
| 11 | 132,690,560,686,109,203,240 | 10-23 03:34:14 | 11 | 19·m^12 + 1, divisible by 80,002,679 | 2³ · 5 · 251 · 953 · 13,867,986,677,227 |

**a(9) = a(8)**, the published term: its run is nine, so the first segment
of the campaign, which starts AT a(8), recorded it — as README.md said it
would — with BLS75 Theorem 1 certificates for all nine values (the largest
112 digits). That claim rests on Busby's a(8) being the least m with a run
of eight, exactly as every extension of a published term rests on the term
below it; the campaign does not re-sweep below a(8). The comment "10
divides all terms" holds on the three (it is a theorem from n = 4 on,
README.md). After a(11) the filter moved to n = 12, three segments of it
closed (m = 1.3324×10²⁰ to 2.4285×10²⁰), and the owner stopped the
campaign at launch 26,885 of the next segment's 78,000.

### The least-claim basis

Every file's `least_claim` names the line its claim rests on: swept from
the family's frontier term (inclusive — the ladders nest, so a(n) ≥
a(n − 1) and the sweep for a(n) starts AT a(n − 1)), at the filter named,
with the wheel, class, sieve depth (2¹³ throughout) and Fermat stage (six
conditions on the device throughout) it was swept at. A find at index n is
made while the filter is n, and the filter's line below a `carried`
boundary was classified by the filter before it with every survivor's run
read to the filter + 6, so nothing with a run of n or more was dropped
there. The floors, in each entry's own letter:

| find | swept from | at filter | class |
|---|---|---|---|
| A229626 a(10) | a(9) = 687,860,415,949 | 10 | unit 1 |
| A229626 a(11) | 14,227,037,550,485,760, carried from filter 10 | 11 | unit 1 |
| A229627 a(9) | a(8) = 1,095,265,755,949 | 9 | q ≡ 1 (mod 6) |
| A229627 a(10) | 3,411,686,086,448,640, carried from filter 9 | 10 | q ≡ 1 (mod 6) |
| A229627 a(11) | 1,083,366,679,723,317,990, carried from filter 10 | 11 | q ≡ 1 (mod 6) |
| A229630 a(9) | a(8) = 79,235,997,091 | 9 | unit 1 |
| A229630 a(10) | 159,854,354,499,840, carried from filter 9 | 10 | unit 1 |
| A229630 a(11) | 55,630,773,412,498,058,775, the plan adoption boundary (above) | 11 | the semiprime wheel's four branches |
| A229902 a(9) | a(8) = 1,944,616,927,560, the first segment | 9 | m ≡ 0 (mod 10) |
| A229902 a(10) | 7,997,022,243,210, carried from filter 9 | 10 | m ≡ 0 (mod 10) |
| A229902 a(11) | 338,328,809,811,632,640, carried from filter 10 | 11 | m ≡ 0 (mod 10) |

## The finds against the model

E is the model's expected number of terms on the line from a(n − 1)
(inclusive) to the find, so a find at E sits at the 100·(1 − e^(−E))th
percentile of its row; the quantiles are model_results.json's, frozen
before any campaign ran (README.md's table).

| find | a(n) | frozen median | P90 | E | percentile |
|---|---|---|---|---|---|
| A229626 a(10) | 1.07×10¹⁶ | 1.04×10¹⁶ | 5.46×10¹⁶ | 0.70 | 51% |
| A229626 a(11) | 2.70×10¹⁹ | 4.31×10¹⁸ | 2.18×10¹⁹ | 2.69 | 93% |
| A229627 a(9) | 9.16×10¹⁴ | 1.34×10¹⁶ | 6.96×10¹⁶ | 0.10 | 10% |
| A229627 a(10) | 6.92×10¹⁷ | 7.08×10¹⁸ | 3.56×10¹⁹ | 0.13 | 12% |
| A229627 a(11) | 1.00×10²¹ | 3.26×10²¹ | 1.59×10²² | 0.29 | 25% |
| A229630 a(9) | 6.88×10¹¹ | 5.34×10¹⁴ | 2.89×10¹⁵ | 0.006 | 0.6% |
| A229630 a(10) | 2.29×10¹⁷ | 2.63×10¹⁷ | 1.36×10¹⁸ | 0.63 | 47% |
| A229630 a(11) | 7.27×10²⁰ | 1.18×10²⁰ | 5.92×10²⁰ | 2.68 | 93% |
| A229902 a(9) | = a(8) | — | — | 0 | the free term |
| A229902 a(10) | 3.15×10¹⁷ | 1.17×10¹⁷ | 5.85×10¹⁷ | 1.45 | 76% |
| A229902 a(11) | 1.33×10²⁰ | 4.34×10¹⁹ | 2.12×10²⁰ | 1.60 | 80% |

Over the ten searched finds E sums to 10.26 against a Gamma(10, 1) law
(P = 0.57), a mean E of 1.03: the model ran true on this project (its
validation on the sixteen published terms had scored 0.75, and the three
projects before it 0.70 to 1.62). Two finds sat past their P90 (the
a(11)s of A229626 and A229630), three under their Q1 (A229627's three,
early every time, and A229630's a(9), which is the unrestricted a(9)).

## The campaigns against their rates

The campaigns' average rates off the checkpoints — line from the family's
floor to the cursor over the campaign's clock, so an average across every
filter each passed — against BENCHMARKS.md's prices at the filter that
carried the most line: A229626 5.04×10¹⁴ m/s against 4.98×10¹⁴ at n = 11;
A229627 2.25×10¹⁶ q/s against 1.67×10¹⁶ at n = 11, most of its line being
n = 12, which was not priced; A229630 2.20×10¹⁵ m/s, between p1's
5.0×10¹⁴ and p3's 3.1×10¹⁵ at n = 11, as its line was; A229902 3.70×10¹⁵
m/s against 2.72×10¹⁵ at n = 11 and 4.58×10¹⁵ at n = 12, its line split
between them. The campaigns ran at their prices. The acceptance test of
CLAUDE.md 5g (the first `[STATUS]` lines of each fresh start, read for the
pool, the rate and the rung) was the owner's to read at each start and is
not recorded here.

## The census

The host reads every run the device's Fermat stage lets through (six
conditions, so the census floor is 6); the counts are per run length,
from each checkpoint, and `near` is the number of `[NEAR]` lines (a value
one short of the open term at the time). A229630's counts include the
parts of the two re-swept open segments twice (the adoptions above).

| family | run 6 | 7 | 8 | 9 | 10 | 11 | near | survivors read |
|---|---|---|---|---|---|---|---|---|
| A229626 | 20,654,736 | 1,098,718 | 51,135 | 2,108 | 90 | 1 | 104 | 21,806,788 |
| A229627 | 6,534,651 | 316,977 | 13,388 | 479 | 16 | 1 | 12 | 6,865,512 |
| A229630 | 14,057,233 | 694,540 | 29,915 | 1,190 | 40 | 1 | 49 | 90,037,135 |
| A229902 | 20,757,539 | 1,045,205 | 46,143 | 1,858 | 58 | 1 | 87 | 21,850,804 |

The run-11 count in each row is the family's a(11). Nothing in the census
is evidenced: the evidence directory holds the eleven first occurrences
and the four ledgers.

## What is open now

**PAUSED — open to others.** Nothing is running. All four campaigns were
stopped by the owner inside the filter for their next term, a(12), and the
classification reads every survivor's run to its end, so when the filter
for a(12) has swept to the cursor every open index of the family exceeds
it: a(n) for every n ≥ 12 is above the bound in its row.

| entry | frontier (this project's) | open next | searched empty to | filter | median from the cursor | P90 | at the rate | P(found) in a day / a week / 30 days |
|---|---|---|---|---|---|---|---|---|
| A229626 | **a(11) = 26,985,725,415,370,251,655** | a(12) | m > 27,037,605,571,656,084,405 | n = 12, wheel to 89, wide record | 2.60×10²¹ | 1.24×10²² | 20 days at 1.49×10¹⁵ m/s (BENCHMARKS.md, n = 12) | 6% / 26% / 61% |
| A229627 | **a(11) = 1,002,522,190,109,444,576,389** | a(12) | q > 2,859,378,460,971,729,016,320 | n = 12, wheel to 89, wide record | 2.17×10²⁴ | 1.03×10²⁵ | 4.1 years at 1.67×10¹⁶ q/s — the n = 11 price; n = 12 was never priced | 0% / 1% / 3% (21% in a year) |
| A229630 | **a(11) = 727,008,393,707,791,166,119** | a(12) | m > 731,642,078,343,359,683,500 | n = 12, plan p3 (semiprime wheel, cofactor sieve) | 7.63×10²² | 3.62×10²³ | 9 months at 3.1×10¹⁵ m/s — the n = 11 price; n = 12 was measured only as a ratio (1.28 on p2, round 6) | 1% / 3% / 11% (57% in a year) |
| A229902 | **a(11) = 132,690,560,686,109,203,240** | a(12) | m > 242,849,440,082,476,227,000 | n = 12, wheel to 83, m ≡ 0 (mod 10) | 1.47×10²² | 6.77×10²² | 37 days at 4.58×10¹⁵ m/s (BENCHMARKS.md, n = 12) | 3% / 17% / 45% |

(`power_model` read 2026-10-23 in a scratch process from each checkpoint's
coverage cursor, nothing written. "At the rate" is the line from the
cursor to the median over the device rate at that filter from
OPTIMIZATION_LOG.md's table of every filter the campaigns pass, where the
filter was priced; the two that were not are stated at the price one
filter below, which the campaign's rate exceeds. The probabilities are the
model's, read straight: it scored a mean E of 1.03 on the eleven finds.)

**Two of the open terms are weeks, two are the better part of a year or
more**; that is where the project stopped. A229626's a(12) and A229902's
a(12) are the ones a resume would go for, at 20 and 37 days to their
medians; A229630's a(12) is about nine months and A229627's about four
years, and every index past those is years to decades.

**Resuming.** `python launch.py` (A229626), and `--family A229627`,
`--family A229630` or `--family A229902`, continue from the cursors above
with census, finds and the open segment's position intact. **Whoever
resumes runs `python launch.py --selftest` and `python score.py` first**
(CLAUDE.md rule 2). Owed before any of the four is offered again:

- the eleven finds into the oracle's `FOUND` (power_reference.py, empty
  at the pause), so that G1b re-derives them from the definition and a
  fresh clone opens at the new frontier rather than at a(9), a(8), a(8)
  and a(8). The benchmark shapes, the drill filters and the end-to-end
  drills are keyed to each family's open index, so this moves them and was
  not done at the pause. Until it is, the frontier lives in the
  checkpoints (and in this file), and a fresh clone without them
  re-derives every term, which costs the 161 hours above;
- a frozen benchmark shape at each live filter (CLAUDE.md 3b, 5g): n = 12
  on all four families — the live shapes frozen so far are S229630L at
  n = 11 and S229902L at n = 10 (BENCHMARKS.md);
- a price for A229627 at n = 12 and for plan p3 on A229630 at n = 12:
  round 7 measured ratios there, never a rate, and the clock column above
  stands on the n = 11 prices;
- the A229902 round at its day-long filter that round 4 priced and round
  6 deferred (the packed-and-periodic plain window table, about 1.09, and
  the wheel to 131 at n = 12, about 1.16, both unbuilt), now that a(12) is
  the live term;
- the model rerun from the new frontiers written into model_results.json
  (the file holds the predictions frozen before any run, which stay as
  the record; the predictions a resume prices from are the ones above).

## The OEIS entries

What to submit, in each entry's own letter — the integer under `m` or `q`
in the evidence file, `oeis_terms` giving the index:

- **A229626** (m): a(10) = 10680411518375521, a(11) = 26985725415370251655.
- **A229627** (q): a(9) = 915805778084569, a(10) = 691680697554493219,
  a(11) = 1002522190109444576389; consistent with the comment a(9) > 3·10¹³.
- **A229630** (m): a(9) = 687860415949 (= A229626(9), a semiprime),
  a(10) = 228902892109166911, a(11) = 727008393707791166119.
- **A229902** (m): a(9) = 1944616927560 (= a(8): the published term's run
  is nine), a(10) = 314565633745874820, a(11) = 132690560686109203240.

Every value of every find is proved (BLS75 Theorem 15 on the value plus
one for the three 2·m^k − 1 and 2·q^k − 1 ladders, Theorem 1 on the value
less one for A229902, from one factorization of the term), and every
stopper carries a prime factor, so each claim can be confirmed with a few
lines of any bignum system — no trust in this codebase required.
