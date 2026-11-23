# BENCHMARKS — residue-ladders

> **Authorship disclaimer:** As with the rest of this project, this
> document and the code it describes were authored by **Claude
> (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every correctness gate is green
AND each frozen shape reproduces its work fingerprint. The rate is p of
line swept per second on the device, end to end (sieve, first test, runs,
read-back), in units of 10^6 p/s. Absolute numbers on one machine swing
with ambient load; judge changes by paired, interleaved A/B
(OPTIMIZATION_LOG.md), never by two readings. `python score.py
--bench-only` runs no gate and prints RATE lines, never a SCORE.

## The ledger

All on one RTX 4090.

| date | engine | SCORE (10^6 p/s) | notes |
|---|---|---|---|
| 2026-11-21 | **v2**: the first test as 2^(−j) from a five-squaring start (RSL-005 of the Codex review), lazy reduction below 2^60, the run in stages (the base 3 and the base 5 in kernels of their own), launches of 2^24 words | **561,064** | 21 gates + fingerprints; selftest 44 rows ALL GREEN. Paired against v1 on the SCORE window: **1.576x** [1.556, 1.613]; 1.42x to 1.53x at the other four day-long shapes, 1.37x to 1.62x at the openings (OPTIMIZATION_LOG.md 3.6). Fingerprints re-frozen (below) |
| 2026-11-21 | v1: register sieve of 512 primes, in-kernel compaction, the first test as a square root, two candidates per thread, launches of 2^23 words | 360,221 | 19 gates + fingerprints; selftest 38 rows ALL GREEN (355,310 on the morning of the v2 round) |
| 2026-11-21 | v1 before round 2 (one candidate per thread) | 346,190 | same fingerprints |
| 2026-11-21 | prototype (per-word sieve of 256 primes, separate expand and compaction passes, launches of 2^22 words) | — (never frozen) | 3.10·10^11 p/s on the SCORE window in the paired A/B that v1 before round 2 won 1.196x |

## The shapes

Ten frozen shapes, each one launch of 2^24 words (2^30 candidates) of the
production engine at its defaults. The DAY shapes sit at the median of
each family's day-long filter (README, "The model"); the OPEN shapes at
p = 2^42, where the published terms end.

| shape | entry | p at the start | rate (p/s), v2, 2026-11-21 | count | checksum |
|---|---|---|---|---|---|
| SCORE | A002226 | 8.5·10^16 | 5.611·10^11 | 4419 | 16547262922577478245 |
| DAY_A002227 | A002227 | 4.5·10^17 | 8.449·10^11 | 3587 | 6643457071710258490 |
| DAY_A002228 | A002228 | 1.7·10^17 | 1.568·10^12 | 4155 | 16705191370555841580 |
| DAY_A060363 | A060363 | 1.6·10^17 | 1.880·10^12 | 2092 | 9212120557217098240 |
| DAY_A060364 | A060364 | 4.3·10^17 | 2.487·10^12 | 689 | 10453202450027593136 |
| OPEN_A002226 | A002226 | 2^42 | 7.216·10^11 | 6069 | 2988142512882649909 |
| OPEN_A002227 | A002227 | 2^42 | 1.106·10^12 | 5182 | 16555203898948143278 |
| OPEN_A002228 | A002228 | 2^42 | 1.909·10^12 | 5587 | 11204242592085098805 |
| OPEN_A060363 | A060363 | 2^42 | 2.316·10^12 | 2834 | 12018774250256998754 |
| OPEN_A060364 | A060364 | 2^42 | 3.163·10^12 | 914 | 7447129349846053348 |

`DAY_A002227` moved with engine v2: at its rate the median clock of a(17)
of A002227 (6.2·10^16) is 20 hours, so the family's day-long filter is
a(18), median 4.5·10^17. On the old window the paired ratio is 1.506
(6.134·10^11 to 9.192·10^11 p/s); on the new one 1.528.

The rate falls with height only through the length of the exponent: 22%
from 2^42 to 8.5·10^16 on the quintic line. It rises with the power because
the line thins: one integer in ten is a candidate of the quintic line, one
in thirty-four of the last.

**The fingerprint** of a shape is every device survivor at the shape's
floor (run 6, 5, 4, 4, 4 for the five families: about one prime of the
class in 10^4, a few thousand per launch) as one 64-bit word that binds the
run to its prime — (p + run·B)·A mod 2^64, folded, for two fixed odd
constants — plus, per launch, the number of sieve survivors and a digest of
the number of candidates that passed the first test. A missed prime, a
changed run, a skipped launch or a skipped stage moves the count or the
checksum, and so do two primes exchanging their runs, which the earlier
form p XOR (run · 2^56) did not see (finding RSL-008 of the Codex review;
gate P6 plants the exchange). The sieve count belongs to the sieve depth: a
deliberate change of the number of sieve primes re-freezes the shapes with
the survivor part unchanged.

## The freeze

Re-frozen 2026-11-21 for engine v2 on a green tree, for two deliberate
reasons: one launch of 2^24 words now covers the 2^30 candidates that two
launches of 2^23 did (so the per-launch entries differ), and the survivor
word changed form (above). **The survivors did not change**: on the nine
windows that kept their place, engine v1 first reproduced its frozen
fingerprint, and engine v2 then returned the identical primes and runs, the
same total of sieve survivors and the same total of first-test passes;
on the new `DAY_A002227` window the two engines' survivors were likewise
compared.

The expectation was established independently of the engine being scored:
the CPU engine (numpy sieve, every power in Python integers, Miller–Rabin)
swept the first 2^24 candidates of every shape at its floor, and the device
stream there, host-filtered, is identical —

| shape | primes at the floor in the first 2^24 candidates (device = CPU) | longest run there | primes in the whole window | longest run of a prime |
|---|---|---|---|---|
| SCORE | 73 | 8 | 4417 | 11 |
| DAY_A002227 (4.5·10^17) | 67 | 6 | 3585 | 9 |
| DAY_A002228 | 65 | 5 | 4153 | 8 |
| DAY_A060363 | 34 | 5 | 2090 | 6 |
| DAY_A060364 | 10 | 4 | 687 | 6 |
| OPEN_A002226 | 105 | 9 | 6066 | 12 |
| OPEN_A002227 | 77 | 8 | 5180 | 9 |
| OPEN_A002228 | 87 | 5 | 5585 | 8 |
| OPEN_A060363 | 35 | 5 | 2832 | 6 |
| OPEN_A060364 | 5 | 4 | 912 | 6 |

— on top of gate P1's parity at floor 1 at every height from the line's
first candidate to the ceiling. Every device survivor of the ten windows
was proved prime or composite on the host, and its run re-read with plain
integer arithmetic: all are prime but one. `OPEN_A002226` holds
4406163138721 = 9433 · 14149 · 33013, a Carmichael number of the quintic
line, which passes the first test and every one of the 40 bases on the
device (run 40); a campaign's host drops it at the primality proof. The
longest run of a prime in any window is below its family's frontier (15,
12, 10, 8, 9).

## Wall clock

Device time from the line's first candidate at the SCORE ledger's rates;
the model's medians (README) give the terms.

| entry | to 10^15 | to 10^16 | to 10^17 | to 10^18 | to the ceiling 2^63 |
|---|---|---|---|---|---|
| A002226 | 30 min | 5.0 h | 2.1 d | 21 d | 190 d |
| A002227 | 20 min | 3.3 h | 33 h | 14 d | 126 d |
| A002228 | 11 min | 1.8 h | 18 h | 7.4 d | 68 d |
| A060363 | 9 min | 1.5 h | 15 h | 6.2 d | 57 d |
| A060364 | 7 min | 1.1 h | 11 h | 4.6 d | 43 d |

The campaign loop ran at 1.02 to 1.04 of its device time on the last
stretch of the published line with engine v1 (OPTIMIZATION_LOG.md, "The
loop"); it was not re-measured on v2, whose device is 1.4 to 1.6 times
faster under the same host work.

**Not an engine, for scale**: a scratch prototype of a sieve in the
cyclotomic field swept the quintic line's shell from 8.5·10^16 to
1.7·10^17 at 8.57·10^13 p/s, 146 times the SCORE shape's rate, and agreed
with this engine on every prime it was compared on (OPTIMIZATION_LOG.md
round 4).
