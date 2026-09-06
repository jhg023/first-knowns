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
| SCORE | A078502 | 15 | (..19],(19,31],(31,43] | 2 | 131072 | 500 third-level residues of the segment at period 1 | 154760 / 1717515042281197424 |
| SCOREP | A074200 | 15 | same | 2 | 131072 | same | 154612 / 2377031453654844854 |
| SCORE16 | A078502 | 16 | (..23],(23,37],(37,47] | 34 | 131072 | 128 residues | 111412 / 112270611949917918142 |
| SCORE17 | A074200 | 17 | (..19],(19,31],(31,43] | 2 | 32768 | 384 residues | 213382 / 1379323101368620150 |
| SCORE2L | A078502 | 15 | (23],(37] | 1 | 65536 | 240 periods from 94334 | 8691 / 702330747726546914 |
| SCORE1L | A078502 | 15 | ≤ 23 | 1 | 65536 | the SAME absolute window, 33263× as many periods | 8691 / 702330747726546914 |
| SCORE9 | A074200 | 9 | ≤ 13 | 1 | 4096 | 4e8 periods from 3330003 | 5537992 / 1223908228450 |

SCORE2L and SCORE1L cover the identical absolute window with different
arithmetic and must return the identical fingerprint — a CRT-lift bug shows
up inside the benchmark rather than as a wrong answer months later.

The four campaign shapes name their wheel and depth explicitly rather than
asking the planner: the planner's answer is a default optimization is
expected to move, and a benchmark whose window moves with it is not an
anchor. G18 checks the planner still produces exactly these.

## Wall clock at the scored rates

Device only, against the modelled medians (README.md). The campaign's own
rate is the pipeline's — device and host — and is what `[STATUS]` prints.

| filter | x/s | N/s | median x | to the median | at 2.5× |
|---|---|---|---|---|---|
| n = 15 | 5.62e16 | 2.03e22 | 1.18e17 | 2.1 s | 5.3 s |
| n = 16 | 3.51e17 | 2.53e23 | 2.13e19 | 61 s | 2.5 min |
| n = 17 | 4.26e16 | 5.22e23 | 9.28e19 | 36 min | 1.5 h |
| n = 18 | 4.46e17 | 5.46e24 | 2.89e22 | 18.0 h | 45 h |

(measured at the campaign's own planned configuration, three rounds
interleaved; against the untuned engine this project started from these are
1.345× / 1.122× / 1.139× / 1.147×.)

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
