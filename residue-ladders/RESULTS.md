# RESULTS — residue-ladders (A002226, A002227, A002228, A060363, A060364)

> **Authorship disclaimer:** As with the rest of this project, this
> document and the code it describes were authored by **Claude
> (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Twenty terms: a(16) through a(20) of A002226, a(13) through a(17) of
A002227, a(11) through a(13) of A002228, a(9) through a(12) of A060363 and
a(10) through a(12) of A060364** — fifteen primes, three of which settle
more than one index (a prime of run r settles every open index up to r).
Found 2026-11-22 to 2026-11-23 (UTC) by one campaign per family on engine
v2, each from the first candidate of its line with the entry's published
terms rediscovered in order as canaries. The first advance on A060363
since Don Reble's terms of 2001, and on the other four since Sergey
Paramonov's of April 2024; A002227's a(13) honours that entry's comment
a(13) > 2^42.

Each evidence file was re-verified from disk on 2026-11-23 by a harness
that shares nothing with the engines, the oracle or the launcher (sympy
for primality and for the list of primes, Python integers for every
power): p prime and p − 1 divisible by twice the power; the run recomputed
by Euler's criterion over the first primes and matched to the file; the
root given for each of the first n primes raised to the power and matched
to that prime; the stopper recomputed — the next prime, its symbol matched
to the file and not 1; the Lucas certificate multiplied back to p − 1,
each factor prime and the whole matched to sympy's `factorint`, and the
primitive root's order checked at every factor; `settles` contiguous from
one past the previous term's run (the published frontier, for the first
find) to this one's, and `oeis_terms`, the index and the file name matched
to the integer; the `least_claim` running from the first candidate of the
line to p; each ledger row equal to its file but for the ledger's own time
and label; and every index checked against the OEIS export of 2026-11-21,
so that each find continues its entry's list and none is already there.
Each entry's last published term was also recomputed and has run exactly
its index, so none settled a further index for free. **15 files, 20 terms,
0 failures.**

Every file also carries the three confirmations README.md describes (the
device stream with the host's Miller–Rabin proof and its re-read of the
run; sympy, the oracle's run, the roots, the symbol and the certificate;
a device re-sweep at another alignment and sieve depth, and the CPU
engine on the 16,384 candidates around p) and a `least_claim`: every
integer of the line below p was taken in order by the campaign from the
first one, and none of the primes among them has a run reaching the
index. Times below are the files' `found_utc`.

### A002226 — 2026-11-22, 1.20 h on the campaign's clock

Smallest prime p such that first n primes (p_1=2, ..., p_n) are quintic
residues mod p.

| n | a(n) = p | found (UTC) | run | stops at | p − 1 factored |
|---|---|---|---|---|---|
| 16 | 10,241,565,507,851 | 11-22 00:17:59 | 16 | 59 | 2 · 5² · 181 · 353 · 3,205,849 |
| 17 | 18,473,408,327,791 | 11-22 00:18:11 | 17 | 61 | 2 · 3² · 5 · 13 · 15,789,237,887 |
| 18 | 19,285,164,029,171 | 11-22 00:18:12 | 18 | 67 | 2 · 5 · 13 · 41 · 997 · 3,629,117 |
| 19, 20 | 2,333,727,996,299,111 | 11-22 01:18:28 | 20 | 73 | 2 · 5 · 233,372,799,629,911 |

a(16), a(17) and a(18) came within 13 seconds of each other, all below
2·10^13, well inside the bound of 8.504·10^16 that a validation window had
set before the campaign. One prime of run 20 settles a(19) and a(20).
Stopped at p = 2.7555×10^15, with a(21) open.

### A002227 — 2026-11-22 to 11-23, 16.01 h

Smallest prime p such that first n primes (p_1=2, ..., p_n) are 7th power
residues mod p.

| n | a(n) = p | found (UTC) | run | stops at | p − 1 factored |
|---|---|---|---|---|---|
| 13 | 19,510,606,221,947 | 11-22 01:24:07 | 13 | 43 | 2 · 7 · 17 · 47 · 547 · 1,697 · 1,879 |
| 14, 15, 16 | 88,438,418,479,321 | 11-22 01:25:13 | 16 | 59 | 2³ · 3 · 5 · 7 · 13 · 5,417 · 1,495,063 |
| 17 | 25,634,091,808,728,901 | 11-23 07:36:04 | 17 | 61 | 2² · 3³ · 5² · 7 · 23 · 593 · 99,442,859 |

One prime of run 16 settles a(14), a(15) and a(16). Stopped at p =
4.7549×10^16, with a(18) open.

### A002228 — 2026-11-22, 33 seconds

Smallest prime p such that first n primes (p_1=2, ..., p_n) are 11th power
residues mod p.

| n | a(n) = p | found (UTC) | run | stops at | p − 1 factored |
|---|---|---|---|---|---|
| 11, 12, 13 | 7,282,475,885,851 | 11-22 01:27:34 | 13 | 43 | 2 · 3 · 5² · 11 · 317 · 359 · 38,783 |

One prime of run 13, less than twice the last published term, settles
three indices. Stopped 33 seconds into the campaign at p = 5.9176×10^13,
with a(14) open.

### A060363 — 2026-11-22, 3.09 h

Smallest prime p such that first n primes (p_1=2, ..., p_n) are 13th power
residues mod p.

| n | a(n) = p | found (UTC) | run | stops at | p − 1 factored |
|---|---|---|---|---|---|
| 9 | 4,502,169,075,457 | 11-22 01:28:19 | 9 | 29 | 2⁸ · 3² · 13 · 150,312,803 |
| 10 | 14,272,424,321,923 | 11-22 01:28:23 | 10 | 31 | 2 · 3² · 13 · 197 · 309,610,489 |
| 11 | 494,048,446,485,491 | 11-22 01:32:13 | 11 | 37 | 2 · 5 · 13 · 461 · 28,697 · 287,269 |
| 12 | 14,088,806,484,746,579 | 11-22 03:28:11 | 12 | 41 | 2 · 13 · 59 · 661 · 108,223 · 128,389 |

Stopped at p = 2.1644×10^16, with a(13) open.

### A060364 — 2026-11-22, 17.84 h

Smallest prime p such that first n primes (p_1=2, ..., p_n) are 17th power
residues mod p.

| n | a(n) = p | found (UTC) | run | stops at | p − 1 factored |
|---|---|---|---|---|---|
| 10 | 129,355,619,456,629 | 11-22 04:34:37 | 10 | 31 | 2² · 3³ · 17 · 13,487 · 5,223,929 |
| 11 | 8,346,235,378,563,923 | 11-22 05:25:32 | 11 | 37 | 2 · 7 · 17 · 239 · 146,728,936,721 |
| 12 | 157,501,866,829,901,147 | 11-22 21:53:25 | 12 | 41 | 2 · 7 · 17 · 59 · 109 · 102,903,521,957 |

Stopped at p = 1.6197×10^17, with a(13) open.

## The finds against the model

The model's predictions were stated before any sweep (README.md, from each
entry's origin, with the fitted constant LATE = 0.59). Where each find
fell, as the model's own probability that the term lies at or below it
from that origin, and as the exposure from the previous distinct term
(the published last term, or the entry's stated bound, for the first
find), which the fitted model draws from an exponential of mean 1/LATE =
1.69 and independence from one of mean 1:

| entry | n | a(n) = p | model's P(a(n) ≤ p) | p / predicted median | exposure |
|---|---|---|---|---|---|
| A002226 | 16 | 1.024·10^13 | 0.21 | 0.41 | 0.39 |
| | 17 | 1.847·10^13 | 0.09 | 0.16 | 0.09 |
| | 18 | 1.929·10^13 | 0.02 | 0.03 | 0.002 |
| | 19, 20 | 2.334·10^15 | 0.41, 0.10 | 0.75, 0.14 | 0.88 |
| A002227 | 13 | 1.951·10^13 | 0.40 | 0.78 | 0.87 |
| | 14, 15, 16 | 8.844·10^13 | 0.32, 0.05, 0.01 | 0.57, 0.08, 0.01 | 0.54 |
| | 17 | 2.563·10^16 | 0.26 | 0.42 | 0.50 |
| A002228 | 11, 12, 13 | 7.282·10^12 | 0.02, 0.002, < 0.001 | 0.07, 0.006, < 0.001 | 0.04 |
| A060363 | 9 | 4.502·10^12 | 0.52 | 1.05 | 1.23 |
| | 10 | 1.427·10^13 | 0.16 | 0.24 | 0.20 |
| | 11 | 4.940·10^14 | 0.34 | 0.59 | 0.68 |
| | 12 | 1.409·10^16 | 0.56 | 1.19 | 1.34 |
| A060364 | 10 | 1.294·10^14 | 0.07 | 0.10 | 0.12 |
| | 11 | 8.346·10^15 | 0.22 | 0.35 | 0.42 |
| | 12 | 1.575·10^17 | 0.23 | 0.36 | 0.41 |

**The fitted model ran late.** Of the twenty indices, two were settled past
their predicted medians, both on A060363; the fifteen exposures have mean
0.51, every one is below the fitted mean of 1.69, and thirteen are below 1.
Their Kolmogorov–Smirnov distance from the fitted exponential is 0.461,
against a 5% critical value of about 0.34 for fifteen values (the constant
was not refitted on them): the finds reject LATE = 0.59. From the
independent exponential, rate 1, their distance is 0.281, and they do not
reject it. The README had expected LATE to drift toward 1 with height; the
finds sit at independence or ahead of it, which is consistent with the
deficit that made the published terms late being a feature of the low
heights where those lie. No
re-fit has been made, and the forecasts below are still the fitted model's:
they are probably late.

## The campaigns against their rates

Line swept over clock: 6.38·10^11 p/s on A002226, 8.25·10^11 on A002227,
1.95·10^12 on A060363 and 2.52·10^12 on A060364, against the benchmark's
5.61·10^11, 8.45·10^11, 1.88·10^12 and 2.49·10^12 at each family's day-long
height (A002226's campaign ran below 3·10^15, where each power is a few
squarings shorter). A002228's 33 seconds are too short to read a rate from.

## The census

The host's counts of the primes it proved, per run length, from the census
floor to the frontier; each length is counted from the moment it entered
the census window, which rises with the frontier, so the lower lengths
cover part of the line only, and the canaries and finds are among them.
Near misses are the primes met one short of the open term at the time.

| entry | census (run: primes) | near misses | device survivors | composites dropped by the host | parity checks |
|---|---|---|---|---|---|
| A002226 | 16: 119 · 17: 25 · 18: 4 · 19: 0 · 20: 1 | 88 | 66,783 | 433 | 205 |
| A002227 | 14: 256 · 15: 33 · 16: 5 · 17: 2 | 117 | 31,715 | 816 | 2,663 |
| A002228 | 11: 0 · 12: 1 · 13: 1 | 151 | 10,345 | 47 | 1 |
| A060363 | 10: 342 · 11: 26 · 12: 2 | 182 | 22,841 | 351 | 529 |
| A060364 | 10: 130 · 11: 7 · 12: 1 | 109 | 30,257 | 515 | 3,059 |

## What was established before the campaigns

- **All 54 published terms are reproduced**: prime, of the right class,
  with run at least their index, and with run exactly their index wherever
  the next term is larger (oracle gate G3); 24 of them rebuilt from scratch
  below 2.5·10^7 by the oracle (G2); every one found, first of its run, by
  the CPU engine and by the GPU engine in a window around it (S3, P4).
- **The benchmark windows hold no term.** The ten frozen shapes (2^30
  candidates each, at 2^42 and at each family's day-long height) are
  counted, not classified. Every device survivor in them was proved prime
  or composite on the host: the longest run of a prime is 12, 9, 8, 6, 6
  at 2^42 and 11, 9, 8, 6, 6 at the day-long heights, below every open
  index. One survivor is composite: 4406163138721 = 9433 · 14149 · 33013,
  a Carmichael number of the quintic line that passes all 40 bases on the
  device and is removed by the primality proof.

## What is open now

Nothing is running. Each campaign resumes from its checkpoint (gitignored;
the owner's) at the cursor below; without it a campaign starts again from
the first candidate of its line and re-derives every term above on the
way, at the cost of the line already swept (38 hours over the five). From
each cursor, at the measured rate, the fitted
model's medians (late, as above):

| entry | searched empty to p = | open | median p | median clock |
|---|---|---|---|---|
| A002226 | 2.7555×10^15 | a(21) | 8.8·10^16 | 1.8 d |
| A002227 | 4.7549×10^16 | a(18) | 5.1·10^17 | 6.3 d |
| A002228 | 5.9176×10^13 | a(14) | 1.7·10^17 | 1.3 d |
| A060363 | 2.1644×10^16 | a(13) | 1.9·10^17 | 1.0 d |
| A060364 | 1.6197×10^17 | a(13) | 8.1·10^18 | 37 d |

A060364's a(13) has its upper quartile above the ceiling of 2^63. A
resume owes `python launch.py --selftest` and `python score.py` first
(CLAUDE.md rule 2). The quintic field sieve of OPTIMIZATION_LOG.md round 4
(146 times the quintic line's rate in a scratch prototype) is the lever
for A002226 past a(21); it is not built.
