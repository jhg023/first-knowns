# BENCHMARKS — lcm-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green AND
all seven frozen shapes reproduce their work fingerprint (survivor count +
xor of the surviving x). The rate is end-to-end **x-line per second**; the
published term is N = L(n)·x, so multiply by L(n) — 360360 at n = 15 and 16,
12252240 at n = 17 — for a rate in N.

Seven shapes because every filter here is a different line: the unit, the
wheel, the sieve depth and the period all change with n and none of them
monotonically, so one configuration would measure one opening and say
nothing about the next.

## The ledger

| date | engine | SCORE | SCOREP | SCORE16 | SCORE17 | SCORE2L | SCORE1L | SCORE9 |
|---|---|---|---|---|---|---|---|---|
| 2026-09-06 | v1 | 52,833 | 52,698 | 301,058 | 38,295 | 20,331 | 4,955 | 6.7 |
| 2026-09-06 | v1 round 2 | 53,408 | 53,340 | 309,337 | 38,219 | 20,675 | 5,037 | 6.9 |
| 2026-09-06 | v1 round 3 | 53,664 | 53,534 | 336,231 | 38,135 | 20,632 | 5,096 | 6.4 |
| 2026-09-06 | v1 round 4 | 54,030 | 54,054 | 337,058 | 40,679 | 21,093 | 4,858 | 6.8 |
| 2026-09-06 | v1 round 6 | 55,995 | 55,891 | 364,682 | 62,510 | 21,152 | 4,865 | 6.8 |
| 2026-09-06 | v1 round 7 | 55,989 | 55,991 | 365,117 | 62,494 | 21,111 | 4,851 | 6.7 |

(in units of 10⁶ x/s; SCORE9 is ~7×10⁶ x/s, a filter whose survivor density
is four orders higher.)

Round 2 moved two engine constants ( 2^35 → 2^37 and
 0.5 → 0.7) and one campaign-loop cost that the benchmark
cannot see at all:  went from 34 ms per launch to 2.5 µs, or
about 60% of a launch to 0.01% of one. The shapes pin , so the SCORE
row moves only by the tail-round change; the campaign gets the rest.

## The shapes

| shape | family | n | wheel | unit | sieve | window | fingerprint |
|---|---|---|---|---|---|---|---|
| SCORE | A078502 | 15 | {3,5,7,17,19,23,29,31,37,41,43,47} | 2 | 262144 | 96 third-level residues of the segment at period 1 | 74297 / 849661955738965598 |
| SCOREP | A074200 | 15 | same | 2 | 262144 | same | 74590 / 962011421661791124 |
| SCORE16 | A078502 | 16 | {3,5,7,19,23,29,31,37,41,43,47,53} | 34 | 131072 | 20 residues | 118075 / 21369117790222865260 |
| SCORE17 | A074200 | 17 | {3,5,7,19,23,29,31,37,41,43,47,53} | 2 | 65536 | 54 residues | 119087 / 2410739981118000456 |
| SCORE2L | A078502 | 15 | (23],(37] | 1 | 65536 | 240 periods from 94334 | 8691 / 702330747726546914 |
| SCORE1L | A078502 | 15 | ≤ 23 | 1 | 65536 | the SAME absolute window, 33263× as many periods | 8691 / 702330747726546914 |
| SCORE9 | A074200 | 9 | ≤ 13 | 1 | 4096 | 4e8 periods from 3330003 | 5537992 / 1223908228450 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint — a CRT-lift bug shows
up inside the benchmark rather than as a wrong answer months later.

The seven shapes pin `pb` and `nu` -- the segment width and the launch decomposition -- so that a tuning sweep of either cannot move the benchmark's own window (round 7 moved pb 192 to 224 and would otherwise have taken every fingerprint with it). The four campaign shapes name their wheel (a SUBSET of the primes, not a prefix -- 11 and 13 are sieved rather than wheeled at n = 15, and 17 as well from n = 17) and their depth explicitly rather than
asking the planner: the planner's answer is a default optimization is
expected to move, and a benchmark whose window moves with it is not an
anchor. G18 checks the planner still produces exactly these.

## Wall clock at the scored rates

Device only, against the modelled medians (README.md). The campaign's own
rate is the pipeline's — device and host — and is what `[STATUS]` prints.

| filter | x/s | N/s | median x | to the median | at 2.5× |
|---|---|---|---|---|---|
| n = 15 | 5.93e16 | 2.14e22 | 1.18e17 | 2.0 s | 5.0 s |
| n = 16 | 3.85e17 | 2.77e23 | 2.13e19 | 55 s | 2.3 min |
| n = 17 | 6.56e16 | 8.04e23 | 9.28e19 | **23.6 min** | 59 min |
| n = 18 | 6.75e17 | 8.27e24 | 2.89e22 | 11.9 h | 30 h |

(measured at the campaign's own planned configuration, three rounds
interleaved; against the untuned engine this project started from these are
1.420× / 1.229× / 1.754× / 1.736×.)

n = 16 is eight times the line rate of n = 15 and n = 17 because 17 is
forced there: the unit is 34 rather than 2, and the wheel reaches 47 under
the same 2^63 reduction bound. n = 17's *N* rate is the highest of the four
even though its x rate is the lowest, because L(17) is 34× L(16).

## The host side

The pool is sized at runtime from a measurement at the campaign's own filter,
not from a constant. Measured at n = 15 of A078502 on the opening
configuration: **104,000 survivors/s × 12.4 µs = 1.29 core-seconds per second
→ 3 workers** at the ×2 margin. The sieve depth is chosen (`plan_q2`) so that
this number lands near one core at every filter, which is why the depth is
131072 at n = 15 and 32768 at n = 17 — the survivor rate per candidate at a
fixed depth moves an order of magnitude between filters.
