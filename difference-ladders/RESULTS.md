# Results — difference-ladders

Every verified term this project has found, the evidence behind it, and the
state of each line. Integers are exact; every value is in the evidence
file named. Letters are each entry's own (CLAUDE.md 5i): b on A216666 and
A216668, m on A229073.

## Verified finds

Eighteen new terms over the three entries: eight read off the runs at
published terms without a sweep (2026-11-23), and ten found by the owner's
two campaigns on 2026-11-24 (UTC), 14.64 hours on A216666's clock and 2.78
hours on A216668's.

| sequence | a(n) | integer | how | evidence |
|---|---|---|---|---|
| A216666 | a(9) | b = 8,631,333,707,125,241 | campaign, about 4 minutes in | [A216666_a9_8631333707125241.json](evidence/A216666_a9_8631333707125241.json) |
| A216666 | a(10) | b = 4,706,913,956,767,150,128 | campaign, 9.6 hours in | [A216666_a10_4706913956767150128.json](evidence/A216666_a10_4706913956767150128.json) |
| A216668 | a(12) … a(17) | b = 288,975,248,496 | free: the run at the published a(11) is exactly 17 | [A216668_a12_288975248496.json](evidence/A216668_a12_288975248496.json) |
| A216668 | a(18) … a(23) | b = 28,883,337,280,604,081 | campaign, 50 minutes in: its run is exactly 23 | [A216668_a18_28883337280604081.json](evidence/A216668_a18_28883337280604081.json) |
| A229073 | a(8) | m = 30,717,523,795 | free: A216666's a(7) = 30,717,523,794 has a run of exactly 7 | [A229073_a8_30717523795.json](evidence/A229073_a8_30717523795.json) |
| A229073 | a(9) | m = 55,779,743,836 | free: A216666's a(8) = 55,779,743,835 has a run of exactly 8 | [A229073_a9_55779743836.json](evidence/A229073_a9_55779743836.json) |
| A229073 | a(10) | m = 8,631,333,707,125,242 | rides: A216666's a(9) has a run of exactly 9 | A216666's a(9) record, `also_settles` |
| A229073 | a(11) | m = 4,706,913,956,767,150,129 | rides: A216666's a(10) has a run of exactly 10 | A216666's a(10) record, `also_settles` |

A216666 had not moved since Jean-Louis Charton's a(8) of October 2012
(Tyler Busby's "a(9) > 10^11" of February 2023 was the only line added
since), A216668 since Charton's a(11) of October 2012, and A229073 since
Eric M. Schmidt's a(7) of September 2013. A229073's two riders have no file
of their own: an A216666 find that also settles A229073 is one record, which
carries the rider under `also_settles` as `{"sequence": "A229073", "n": …,
"m": …}`, with m = b + 1.

**Re-verified from disk (2026-11-24).** An independent harness, sympy only
(no engine, launcher or huntlib code), read the three campaign records back
and recomputed every value (b+1)^p − b^p from b, the run by sympy's BPSW (9,
10 and 23, as recorded), each stopper (its factor dividing the value, or
the failed base-2 Fermat test), each of A216668's composite witnesses, the
`oeis_terms` map, and A229073's definition at m = b + 1 for both riders: 0
failures.

### A216666 a(9) = 8,631,333,707,125,241 and a(10) = 4,706,913,956,767,150,128

* **a(9)**: the values at p = 2 … 23 are prime (17 to 352 digits), and the
  value at p = 29 (448 digits) is composite — 59 divides it — so the run is
  exactly 9. b = 7 · 19628107 · 62820509.
* **a(10)**: the values at p = 2 … 29 are prime (19 to 525 digits), and the
  value at p = 31 (562 digits) is composite — 38069 divides it — so the run
  is exactly 10. b = 2^4 · 3 · 7 · 11 · 13 · 97962744687961.

Both runs are exact, so both finds settle A229073 too: its a(10) is
a(9) + 1 = 8,631,333,707,125,242 and its a(11) is a(10) + 1 =
4,706,913,956,767,150,129 (the argument is the free terms', below).
**The least-claim:** the campaign swept A216666's line from the published
a(8) = 55,779,743,835 inclusive (so Busby's 10^11 lies inside the sweep), at
filter 9, where every b whose run is 9 or more was read; a(9) is the first.
The filter then climbed to 10 and swept on from 8,711,225,049,246,720 — the
line between a(9) and there had been classified by filter 9 with runs read
to 15 — to the first b of run 10. **Verification:** huntlib's thirteen-base
Miller–Rabin chain, sympy's BPSW agreeing on the run, the CPU engine's
re-sieve at another wheel, and the stopper's factor. **Certificates:** at
a(9), p = 2 deterministically, p = 3, 5, 7 and 13 by BLS75 Theorem 1, p = 11
and 19 by Theorem 5; **p = 17 (257 digits) and p = 23 (352 digits) are
UNPROVED**. At a(10), the same routes for the same p (the certificates from
p = 5 up carry a BLS75 subproof for the 26-digit prime factor
67442607737360060191771921 of their N − 1, past the deterministic bound);
**p = 17, 23 and 29 (300, 413 and 525 digits) are UNPROVED**. Unlike the free terms' unproved values,
these rest on no published term: they are strong probable primes to
thirteen bases and BPSW, and await a general prover (APR-CL or ECPP).

### A216668 a(18) through a(23) = 28,883,337,280,604,081

At b = 28,883,337,280,604,081 the conditions read, for the primes p in
order:

* **prime, as asked** (2^p − 1 prime) at p = 2, 3, 5, 7, 13, 17, 19, 31 and
  61 — values of 17 to 990 digits;
* **composite, as asked** (2^p − 1 composite) at p = 11, 23, 29, 37, 41, 43,
  47, 53, 59, 67, 71, 73, 79 and 83 — each with a prime factor (397, 47,
  8353, 149 and 83 at 11 to 41; 107, 76819, 5897, 569 and 167 at 53, 59, 67,
  71 and 83) or, at p = 43, 47, 73 and 79 (693 to 1,286 digits, no factor
  under 2^17), the failed base-2 Fermat test;
* and at **p = 89** the value (1,451 digits) is **composite** — it fails the
  base-2 Fermat test — where 2^89 − 1 is prime: the run stops at exactly 23.

So a(18), a(19), a(20), a(21), a(22) and a(23) are all
28,883,337,280,604,081; the README had put a(19) to a(23) equal to a(18) at
about 98.5%, and they were. b = 11 · 103 · 277 · 63659 · 1445699.
**The least-claim:** the campaign swept A216668's line from a(17) =
288,975,248,496 inclusive at filter 18, where every b whose run is 18 or more
was read; this b is the first, and the conditions nest, so a(19) … a(23) are
at least a(18), which runs to 23. **Verification:** as above, with each
composite condition witnessed. **Certificates:** p = 2 deterministically,
p = 3, 5, 7 and 13 by Theorem 1, p = 19 by Theorem 5; **p = 17, 31 and 61
(265, 496 and 990 digits) are UNPROVED** — strong probable primes to
thirteen bases and BPSW, awaiting a general prover.

### A216668 a(12) through a(17) = 288,975,248,496 (free)

At b = 288,975,248,496 the conditions read, for the primes p in order:

* **prime, as asked** (2^p − 1 prime) at p = 2, 3, 5, 7, 13, 17, 19 and 31 —
  values of 12 to 346 digits;
* **composite, as asked** (2^p − 1 composite) at p = 11, 23, 29, 37, 41, 43,
  47, 53 and 59 — each with a prime factor: 683, 47, 59, 149, 83, 13331,
  1693, 709 at 11 to 47 and 59, and at p = 53 (598 digits, no factor under
  2^17) the failed base-2 Fermat test;
* and at **p = 61** the value (690 digits) is **composite** — 9883 divides
  it — where 2^61 − 1 is prime: the run stops at exactly 17.

So a(12), a(13), a(14), a(15), a(16) and a(17) are all 288,975,248,496.
The least-claim needs no sweep: a b whose run is at least 12 has a run of
at least 11, so a(n) ≥ a(11) for n ≥ 12, and a(11) itself runs to 17.
**Verification:** huntlib's thirteen-base Miller–Rabin over all seventeen
conditions (primes passing, composites failing), sympy's BPSW agreeing on
the run length (exactly 17, read to 18), the CPU engine's re-sieve at
another depth, and the stopper's factor. **Certificates:** the values at
p = 2 and 3 deterministically (under 3.3·10²⁴), p = 5, 7 and 13 by BLS75
Theorem 1, p = 19 by Theorem 5; **p = 17 (185 digits) and p = 31 (346
digits) are UNPROVED** — no N − 1 route exists for them (the factored part
of N − 1 is a quarter and a fifth of it), and no general prover is
installed. Those two values are the same two values Charton's published
a(8) through a(11) already rest on (their run reaches p = 31 too); what
this record adds is the composite side, p = 37 to 61, and every one of
those is witnessed.

### A229073 a(8) = 30,717,523,795 and a(9) = 55,779,743,836 (free)

A229073's a(n) is the least m whose m − 1 has an A216666 run of exactly
n − 1. Every such m − 1 has a run of at least n − 1, so it is at least
A216666's a(n − 1); and when A216666's a(n − 1) itself has a run of exactly
n − 1, it is that term plus one. At A216666's a(7) = 30,717,523,794 the
values at p = 2 … 17 are prime and the value at p = 19 (191 digits) is
composite; at a(8) = 55,779,743,835 the values at p = 2 … 19 are prime and
the value at p = 23 (238 digits) is composite. Both stoppers have no prime
factor under 2^17 and none that huntlib's bounded rho and 40-curve ECM
found; the failed base-2 Fermat test is the witness, recorded in the file
(anyone can rerun 2^(N−1) mod N). **Certificates:** p = 2, 3
deterministically, p = 5, 7 and 13 by Theorem 1, p = 11 (and p = 19 at
a(9)) by Theorem 5; **p = 17 is UNPROVED** at both (170 and 174 digits) —
again exactly the value the published A216666 a(7) and a(8) rest on.
Each record carries m under `m`, A216666's b = m − 1 beside it, and
`oeis_terms` `{"8": 30717523795}` and `{"9": 55779743836}`.

### The least-claim basis

The free terms follow from published terms by the nesting of the conditions
(A216668) or by the definition of an exact run (A229073), as above; the
published terms themselves are the literature's: A216666's a(7), a(8) and
A216668's a(11) by Jean-Louis Charton (2012). The oracle re-derives every
published term below 460,000 from the bare definition (G2: A216666's
a(1)–a(5) and A216668's a(1)–a(7); G1d: A229073's a(1)–a(6)), and the GPU
stream rediscovers A216666's a(6), a(7) and a(8) and A216668's a(7) and
a(8) from their floors as canaries — so A216666's a(7) and a(8), on which
A229073's free terms rest, are re-derived here as FIRST occurrences, not
only taken from the literature. A216668's a(9) to a(11) are not re-swept
(a(11) is 2.5·10¹¹ of line above a(10)).

The campaign terms rest on their sweeps: every b from the floor named in
each record was in the stream of a GPU engine pinned bit for bit to the
independent CPU engine on populated windows to the 10⁴⁰ ceiling (G9), with
the campaigns' value-selected sieve set gated the same way (G24); every b
whose run reached the census floor of 6 was classified on the host; and a
find was published only at the close of the segment holding it, so
nothing below it was still in flight.

## The finds against the model

The model's predictions were stated before any campaign (README.md and
`model_results.json`). Where each find fell, as the model's probability
that the term lies at or below it, searched from the term before (the
published a(8) of A216666, the found a(9) for a(10), and a(17) of A216668),
and as the exposure E over that stretch, which the model draws from an
exponential of mean 1:

| entry | n | a(n) = b | model's P(a(n) ≤ b) | b / predicted median | E |
|---|---|---|---|---|---|
| A216666 | 9 | 8.631·10^15 | 0.73 | 2.35 | 1.31 |
| A216666 | 10 | 4.707·10^18 | 0.48 | 0.93 | 0.66 |
| A216668 | 18 | 2.888·10^16 | 0.88 | 4.37 | 2.10 |

A216668's a(19) to a(23) came with a(18), as the model gave at about 98.5%,
and carry no exposure of their own. **The model ran a little late.** The
three exposures have mean 1.36; their sum, 4.07, has a Gamma(3, 1) upper
tail of 0.23, so three finds cannot reject it. With the nine published
terms of its validation (G11: E sums to 13.3, also late), twelve exposures
sum to 17.4 against a Gamma(12, 1) law: an upper tail of 0.07 — late on
this cluster, not significantly. No re-fit has been made; the forecasts
below are the model's as built.

## The campaigns against their rates

Line swept over the campaign's clock, from the find times in the ledgers
and the work cursors in the checkpoints, against the benchmark at each
filter (BENCHMARKS.md):

| filter | line | clock | rate (b/s) | benchmark | ratio |
|---|---|---|---|---|---|
| A216666 n = 10 | 8.71·10^15 → a(10) | 9.5 h | 1.37·10^14 | 1.44·10^14 | 0.95 |
| A216666 n = 11 | 37.7% of the segment [4.995·10^18, 1.454·10^19) | 5.0 h | 1.98·10^14 | 1.99·10^14 | 1.00 |
| A216668 n = 18 | a(17) → a(18) | 50 min | 9.7·10^12 | 1.07·10^13 | 0.91 |
| A216668 n = 24 | 21.2% of the segment [2.62·10^16, 8.65·10^17) | 1.95 h | 2.5·10^13 | 2.39·10^13 | 1.06 |

The n = 10 and n = 18 clocks include the start-up, the find's certificates
and the segment's close; the n = 11 and n = 24 rates read the work cursor,
which counts launches of equal line. A216666's a(9) came about 4 minutes
in, start-up included, too short to read a rate from. Both day-long
filters run at their benchmark rates.

## The census

The host's counts of the values it classified, per run length, from the
census floor (6) to the frontier; each length is counted from the moment
it entered the census window, so the lower lengths cover part of the line
only, and the finds are among them. Near misses are values met one short
of the open term at the time.

| entry | census (run: values) | near misses | device survivors |
|---|---|---|---|
| A216666 (with A229073) | 6: 4,144,861 · 7: 112,943 · 8: 2,794 · 9: 50 · 10: 1 | 111 | 120,324,959 |
| A216668 | 6: 39,354,704 · 7: 1,166,058 · 8: 177 · 9: 163 · 10: 30,929 · 11: 1 · 12: 1 · 13: 2 · 14: 5 · 15: 1 · 16: 2 · 17: 478 · 18–22: 0 · 23: 1 | 233 | 40,953,954 |

A216668's census jumps from 10 to 17 because the conditions at p = 37 to
59 ask for composites, which almost every value is: a b whose value at
p = 31 is prime almost always runs to 17, and stops at p = 61, where a prime
is asked. The few at 11 to 16 are b with a prime value where a composite
was asked.

## What is open now

**PAUSED** — nothing is running. Each campaign resumes from its checkpoint
(gitignored; the owner's) inside the segment it was working; without the
checkpoint a campaign starts again from its published floor and re-derives
every term above on the way, at the cost of the line already swept (17.4
hours over the two). Coverage advances a whole segment at a time, so "searched empty to"
is the start of the segment in progress, and the work beyond it is not
yet a claim. From each coverage cursor, at the measured rate, the model's
quantiles:

| entry | searched empty to b = | open | Q1 | median | Q3 | P90 |
|---|---|---|---|---|---|---|
| A216666 | 5.0307×10^18 | a(11) (and A229073's a(12)) | 1.03×10²¹ (60 d) | 3.19×10²¹ (6.1 months) | 7.77×10²¹ (15 months) | 1.49×10²² (2.4 years) |
| A216668 | 2.9029×10^16 | a(24) | 9.18×10¹⁸ (4.4 d) | 2.85×10¹⁹ (14 d) | 6.95×10¹⁹ (34 d) | 1.33×10²⁰ (64 d) |

A216666's segment in progress, [4.995·10^18, 1.454·10^19), is 37.7%
worked and closes about 8.3 hours after a resume; A216668's,
[2.62·10^16, 8.65·10^17), is 21.2% worked. A216668's a(24) asks for the
value at p = 89 to be prime (2^89 − 1 is prime); a(25) to a(27) ask only
for composites (p = 97, 101 and 103) and will very likely equal it, and
a(28) asks for a prime again at p = 107. A216666's a(12) is out of reach
(README.md).

**OEIS submission list (for the owner; nothing is submitted from here):**

* A216666: a(9) = 8631333707125241, a(10) = 4706913956767150128;
* A216668: a(12)–a(17) = 288975248496, a(18)–a(23) = 28883337280604081;
* A229073: a(8) = 30717523795, a(9) = 55779743836, a(10) =
  8631333707125242, a(11) = 4706913956767150129.

The unproved values above are strong probable primes. The free terms' rest
on values the published terms already depend on; the campaign terms' are
new (p = 17 and 23 at A216666's a(9), p = 17, 23 and 29 at its a(10), and
p = 17, 31 and 61 at A216668's a(18)). Prove them first if the submission
should claim proofs.
