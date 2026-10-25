# Results — cyclotomic-ladders

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

## Verified finds

**Eight terms: a(11) and a(12) of A070737 — which settle a(11) and a(12)
of A233512 — and a(48), a(60), a(66), a(78), a(80) and a(88) of A072942.**
Found 2026-10-23 to 2026-10-25 by one campaign per family — `python
launch.py` and `python launch.py --family A072942`, no flags — on engine
v2 with planner p2 ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) round 1;
the checkpoint keys and the evidence's `engine` field read `v2-p2`),
except A072942's a(60), whose campaign adopted planner p3's measured wheel
at the owner's restart (round 2; `v2-p3`). The first advance on A070737
since Don Reble and Phil Carmody's ten terms of 2002, and on A072942 since
Don Reble's a-file of February 2014, which left these ten indices below
100 as question marks — six of the ten are now settled. A233512's a(7) to
a(10) were A070737's published terms (G1d); its a(11) and a(12) are the two
finds here, the first terms beyond T. D. Noe's six of 2013, and they travel
in A070737's records under `also_settles` — A233512 is not a `--family` of
the launcher and has no line of its own.

Each evidence file was re-verified from disk on 2026-10-25 by a harness
that shares nothing with the launcher: the forms rebuilt from each entry's
%N line (Φ_k(x) for k = 1..n on A070737; Φ_d(x) for every divisor d of n on
A072942, the divisors from sympy); every value recomputed by Horner from
sympy's `cyclotomic_poly`, matched to the file and tested with sympy's
`isprime`; the factorization of x multiplied back, each factor tested
prime, and matched to `factorint`; the stopper of an A070737 run,
Φ_{n+1}(x), recomputed, composite, with the file's factor dividing it (an
A072942 solution has no stopper: every divisor's value is prime); the run,
the value count, the file name, `settles`, `oeis_terms` and `also_settles`
against the index and the integer; every certificate re-verified by
`huntlib.certificate.verify` and matched to its value; the `least_claim`
ending at the integer at its own filter, from the previous term on A070737
and from x = 3 on A072942; each ledger row matched to its file field by
field; the indices checked against the OEIS export of 2026-10-23 so that
each find continues its entry's list and none is already there; and
`huntlib.evidence.gate_names` over the directory. **8 files, 70
certificates verified, 0 failures**: 14 deterministic Miller–Rabin proofs
(the Φ₁ and Φ₂ values, under 3.317×10²⁴, of the seven terms below that
bound), 54 BLS75 Theorem 1 proofs and 2 Theorem 5 proofs (Φ₆₀ at a(60),
Φ₇₈ at a(78)) — every proof on the value less one, factored by the shape
README.md describes (x's own factorization times the run's own proved
values, whose proofs ride along as subproofs). The largest value proved is
Φ₈₀(x) at a(80), 625 digits.

**Nine values are UNPROVED**, as README.md said they might be: at a(66)
the values Φ₁₁ and Φ₂₂ (168 digits each), Φ₃₃ and Φ₆₆ (335 digits); at
a(78) Φ₃₉ (386 digits); at a(88) Φ₁₁ and Φ₂₂ (168 digits), Φ₄₄ (335 digits)
and Φ₈₈ (670 digits). Each passed the Miller–Rabin chain and sympy's BPSW
test (the harness repeated the latter), so each is a strong probable prime;
what is missing is a certificate. Φ₁₁(x) − 1 = x·Φ₂(x)·Φ₅(x)·Φ₁₀(x) and
Φ₂₂(x) − 1 = x·Φ₁(x)·Φ₅(x)·Φ₁₀(x); at n = 66 and n = 88 the indices 5 and
10 do not divide n, so Φ₅(x) and Φ₁₀(x) — 67 digits each — are outside the
run and must be factored to reach a BLS75 bound, and huntlib's bounded rho
and ECM did not do it; each other unproved value's N − 1 shape likewise
needs a value outside the run factored (or Φ₁₁'s proof as a subproof),
which the bounded search did not reach. The find stands on the three legs
(CONVENTIONS.md's protocol) and each file's `unproved` list names the
values the owner certifies by hand — an ECPP proof of a 168–670-digit
prime is routine — or that a later session proves by Codex's CYL-003 route
(the run's own factors tried first) or by factoring the two 67-digit
cofactors. The other five A072942 finds and both A070737 finds are proved
in full.

Every file also carries the three-way verification (huntlib's Miller–Rabin
chain, sympy's BPSW, a re-sieve by the CPU engine on another wheel) and a
`least_claim`. Times are the ledger's, local.

### A070737 — one campaign, 2026-10-23 22:19 to 23:56 (1.62 h on the campaign's clock)

Smallest number x such that the first n cyclotomic polynomials evaluated
at x are primes.

| n | a(n) = x | found | filter | stops at | x factored |
|---|---|---|---|---|---|
| 11 | 42,580,035,114,896,250,510 | 10-23 22:20:18 | 11 | Φ₁₂(x), divisible by 13 | 2 · 3 · 5 · 7 · 11 · 664,669 · 27,732,473,809 |
| 12 | 16,525,310,463,236,140,956,390 | 10-23 22:55:40 | 12 | Φ₁₃(x), divisible by 313 | 2 · 3 · 5 · 7 · 11 · 13 · 59 · 1,153 · 12,853 · 629,373,523 |

a(11) came about a minute after the start, as the model had priced it (a
median clock under a minute); a(12) 35 minutes later, against 30 minutes
of line at the n = 12 rate and 55 minutes to the model's median. Both
terms are multiples of the forced unit (2,310 at n = 11, 30,030 at
n = 12), as the forcing formula requires, and each settles A233512 at the
same index (`also_settles`): the chain from a(5) is strictly increasing
through both. After a(12) the filter moved to n = 13 and the owner stopped
the campaign with the first n = 13 segment open (launch 79,917 of its
600,117 — about 6.6×10²² of line swept past the boundary, which claims
nothing until the segment closes and is swept again on resume).

### A072942 — one campaign, 2026-10-23 23:57 to 2026-10-25 09:23 (the open indices in TARGETS order)

a(n) is the least x such that the cyclotomic polynomial values Phi(d,x)
are prime for all d dividing n.

| n | a(n) = x | found | values | plan | proved | x factored |
|---|---|---|---|---|---|---|
| 66 | 54,204,720,840,327,330 | 10-24 00:00:45 | 8 | p2 | 4 of 8 (Φ₁₁, Φ₂₂, Φ₃₃, Φ₆₆ unproved) | 2 · 3² · 5 · 7 · 13 · 17 · 23 · 67 · 163 · 1,549,937 |
| 78 | 11,777,724,230,620,068 | 10-24 00:03:17 | 8 | p2 | 7 of 8 (Φ₃₉ unproved) | 2² · 3³ · 7 · 79 · 24,379 · 8,089,033 |
| 88 | 55,385,037,774,343,260 | 10-24 00:05:49 | 8 | p2 | 4 of 8 (Φ₁₁, Φ₂₂, Φ₄₄, Φ₈₈ unproved) | 2² · 3² · 5 · 17 · 23 · 47 · 61 · 89 · 3,084,079 |
| 48 | 951,632,152,101,389,850 | 10-24 00:06:09 | 10 | p2 | all | 2 · 3 · 5² · 7 · 13 · 17 · 29 · 31² · 41 · 3,589,073 |
| 80 | 32,914,062,820,751,552,550 | 10-24 00:07:30 | 10 | p2 | all | 2 · 3² · 5² · 11 · 17 · 41 · 4,297 · 9,649 · 230,089 |
| 60 | 66,868,504,406,704,117,216,919,820 | 10-25 09:13:50 | 12 | p3 | all | 2² · 3 · 5 · 7⁴ · 11 · 13 · 31 · 61 · 1,716,526,976,383,969 |

Every term is a multiple of its index's forced unit — 64,722 at n = 66,
3,318 at 78, 61,410 at 88, 46,410 at 48, 230,010 at 80 and 56,786,730 at
60 — the primes q with (q − 1) dividing n. The five openings closed within
seven minutes of each other, each in seconds of line at its rate (the
0.01–0.06 h on their checkpoints is the engine's build and the
certificates), as the model had priced them. a(60) took 31.5 h on its
campaign's clock, in two runs: swept on planner p2's wheel from 2026-10-24
to x = 1.06×10²⁴ (one segment closed, a second open), the cursor was
ADOPTED onto p3's measured wheel at the owner's restart (OPTIMIZATION_LOG.md
round 2: the swept boundary re-denominated to period 475 of the new wheel,
the open segment swept again), and the find came under p3 at 1.97 times
the model's median, past the Q1 and median rungs and before Q3. After
a(60) the campaign moved to the next open index, n = 72, and the owner
stopped it nine minutes in, inside the first segment (launch 12,497 of
26,645 in period 0; the coverage cursor at x = 3), so nothing of n = 72 is
claimed and its restart sweeps the index from the start.

### The least-claim basis

Every file's `least_claim` names the line its claim rests on. On A070737
the sweep for a(n) starts AT a(n − 1), inclusive (the ladder nests), at the
filter named; a find at index n is made while the filter is n, and the
filter's line below a `carried` boundary was classified by the filter
before it with every survivor's run read to the filter + 6, so nothing
with a run of n or more was dropped there. On A072942 every index is its
own line from x = 3, with the exception zone [3, 8193] — the sieve's own
primes — classified apart from the sieve. Every sweep was at sieve depth
2¹³ with the six-condition Fermat stage on the device, in the forced
class of its filter:

| find | swept from | at filter | class |
|---|---|---|---|
| A070737 a(11) | a(10) = 13,533,264,289,711,320 | 11 | x ≡ 0 (mod 2,310) |
| A070737 a(12) | 43,552,512,473,129,529,870, carried from filter 11 | 12 | x ≡ 0 (mod 30,030) |
| A072942 a(66) | 3 | 66 | x ≡ 0 (mod 64,722) |
| A072942 a(78) | 3 | 78 | x ≡ 0 (mod 3,318) |
| A072942 a(88) | 3 | 88 | x ≡ 0 (mod 61,410) |
| A072942 a(48) | 3 | 48 | x ≡ 0 (mod 46,410) |
| A072942 a(80) | 3 | 80 | x ≡ 0 (mod 230,010) |
| A072942 a(60) | 3 | 60 | x ≡ 0 (mod 56,786,730); the line to 1.06×10²⁴ on the p2 wheel, above it on p3 |

## The finds against the model

E is the model's expected number of terms on the line from the floor (the
previous term on A070737, inclusive; x = 3 on A072942) to the find, so a
find at E sits at the 100·(1 − e^(−E))th percentile of its row; the
quantiles are model_results.json's, frozen before any campaign ran
(README.md's table; A070737's a(12) row there was priced from a(11)'s
median, and E here is taken from the actual a(11)).

| find | a(n) | frozen median | P90 | E | percentile |
|---|---|---|---|---|---|
| A070737 a(11) | 4.26×10¹⁹ | 3.7×10¹⁹ | 1.8×10²⁰ | 0.78 | 54% |
| A070737 a(12) | 1.65×10²² | 3.2×10²² | 1.5×10²³ | 0.43 | 35% |
| A072942 a(66) | 5.42×10¹⁶ | 2.0×10¹⁶ | 9.7×10¹⁶ | 1.51 | 78% |
| A072942 a(78) | 1.18×10¹⁶ | 3.1×10¹⁵ | 1.5×10¹⁶ | 1.99 | 86% |
| A072942 a(88) | 5.54×10¹⁶ | 5.5×10¹⁶ | 2.5×10¹⁷ | 0.71 | 51% |
| A072942 a(48) | 9.52×10¹⁷ | 6.9×10¹⁷ | 3.4×10¹⁸ | 0.90 | 59% |
| A072942 a(80) | 3.29×10¹⁹ | 2.1×10²⁰ | 9.8×10²⁰ | 0.17 | 15% |
| A072942 a(60) | 6.69×10²⁵ | 3.4×10²⁵ | 1.6×10²⁶ | 1.20 | 70% |

Over the eight finds E sums to 7.69 against a Gamma(8, 1) law (P = 0.50),
a mean E of 0.96: the model ran true on this project (its validation on
the 54 published terms had scored 1.24, and the projects before it 0.70 to
1.62). No find sat past its P90; one sat under its Q1 (a(80), at 15%).

## The campaigns against their rates

The A072942 n = 60 campaign averaged 5.9×10²⁰ x/s over its 31.5 h and
6.7×10²⁵ of line — between the p2 wheel's price of 5.5×10²⁰ and the p3
wheel's 6.0×10²⁰ (BENCHMARKS.md), as its line was split between them.
A070737's n = 12 line ran at 7.8×10¹⁸ x/s over its 35 minutes against the
9.2×10¹⁸ priced, with the first launch unpipelined, the promotion and
a(11)'s certificates inside that clock. The five A072942 openings and
A070737's n = 11 closed in seconds of line, so their clocks are the
engine's build and say nothing about rate. The acceptance test of
CLAUDE.md 5g (the first `[STATUS]` lines of each fresh start, read for the
pool, the rate and the rung) was the owner's to read at each start and is
not recorded here.

## The census

The host reads every run the device's Fermat stage lets through (six
conditions, so the census floor is 6); the counts are per run length, from
each checkpoint, and `near` is the number of `[NEAR]` lines (a value one
short of the open term at the time). A070737's counts span the three
filters its campaign passed; n = 60's include the part of the re-swept
open segment twice (the adoption above); n = 72's are the open segment's,
which its restart counts again.

| campaign | run 6 | 7 | 8 | 9 | 10 | 11 | 12 | near | survivors read |
|---|---|---|---|---|---|---|---|---|---|
| A070737 (n = 11 → 13) | 17,384,812 | 882,515 | 71,878 | 3,604 | 297 | 8 | 1 | 21 | 18,343,116 |
| A072942 n = 66 (closed) | 3,273 | 75 | | | | | | 75 | 3,349 |
| A072942 n = 78 (closed) | 5,589 | 105 | | | | | | 105 | 5,695 |
| A072942 n = 88 (closed) | 3,463 | 76 | | | | | | 76 | 3,549 |
| A072942 n = 48 (closed) | 126,040 | 13,580 | 683 | 39 | | | | 39 | 140,343 |
| A072942 n = 80 (closed) | 359,714 | 16,728 | 773 | 11 | | | | 11 | 377,230 |
| A072942 n = 60 (closed) | 332,763,136 | 22,930,966 | 1,642,029 | 56,649 | 1,985 | 68 | 1 | 68 | 357,394,834 |
| A072942 n = 72 (open) | 2,774,927 | 133,909 | 10,089 | 510 | 23 | 0 | | 0 | 2,919,458 |

Nothing in the census is evidenced: the evidence directory holds the eight
first occurrences and the two ledgers.

## What is open now

**PAUSED — open to others.** Nothing is running; paused 2026-10-25, with
the pause battery green (BENCHMARKS.md: 30 gates, every fingerprint
reproduced, `launch.py --selftest` 57/57).

* **A070737** is paused at x = 1.864×10²² — the carried boundary after
  a(12) — inside the filter for a(13), with the first n = 13 segment open
  (its sweep is redone on resume; nothing is lost but the hour). The model's
  median for a(13) is 1.7×10²⁵: about 10 days at the measured 1.79×10¹⁹ x/s
  (Q1 3 days, P90 7 weeks). The coverage unit there is one segment of
  4.9×10²³, 7.7 h — a find is confirmed within that of being passed, an
  expected over-sweep of about 4 h on a ten-day search (CLAUDE.md 5j). Each
  find settles A233512 at the same index while the chain stays strictly
  increasing. a(14) is years away at this rate.
* **A072942** has four open indices below 100, in TARGETS order with the
  model's median clocks at the p3 wheels: a(72) from x = 3 (2.2 days),
  a(84) (6.7 days), a(96) (9.5 days) and a(90) (11 days). `python launch.py
  --family A072942` takes them in that order; `--index` names one.
* **Owed before or on resuming:** `python launch.py --selftest` and `python
  score.py` first (CLAUDE.md rule 2); the nine hand certificates above, or
  Codex's CYL-003 route built; the `Q3_MAX` re-sweep on the measured wheels
  (OPTIMIZATION_LOG.md round 2).
