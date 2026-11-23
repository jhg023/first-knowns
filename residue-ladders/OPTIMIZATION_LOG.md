# OPTIMIZATION LOG — residue-ladders (A002226, A002227, A002228, A060363, A060364)

> **Authorship disclaimer:** As with the rest of this project, this log
> and the code it describes were authored by **Claude (Anthropic's AI)**
> at the repository owner's direction.

Every attempt: change, measurement, kept or rejected. Rates are in p per
second of line swept. All measurements on one RTX 4090, 2026-11-21, from
scratch harnesses that import the engines; no campaign was run. Harnesses
swept known line (below 2^42) or benchmark and validation windows at the
day-long heights, which are counted and never classified against a
frontier.

## Round 0 — the targets, the design, and a bias found before the model

**Targets named first (CLAUDE.md rule 3b).** Per family, the first open
term whose median clock is a day or more — its day-long filter:

| entry | day-long filter | median p | median clock |
|---|---|---|---|
| A002226 | a(21) | 8.5·10^16 | 2.7 d |
| A002227 | a(17) | 6.2·10^16 | 28 h |
| A002228 | a(14) | 1.7·10^17 | 45 h |
| A060363 | a(13) | 1.6·10^17 | 35 h |
| A060364 | a(12) | 4.3·10^17 | 69 h |

The engine's configuration does not follow the frontier (a find moves only
the census floor, applied after the work is done), so a "filter" here is a
height: the exponent is 56 to 59 bits there against 42 at the opening.
Every measurement below that names no other height was taken on the SCORE
window (A002226, 2^30 candidates from p = 8.5·10^16); the round's shipped
ratios were re-measured at all five heights. The opening (p = 2^42, minutes
of clock) is checked by its frozen shapes, not optimized.

### 0.1 The design: no sieve for the property

Whether p_i is a residue mod p is a congruence on a prime of the cyclotomic
field above p (Eisenstein reciprocity), not on p. In the integers the only
sieve is for primality, so the engine is: a small-prime sieve, one modular
power per survivor (2 as a residue, which is also the compositeness test),
then the run on the few that pass. A sieve in the cyclotomic field was
prototyped later the same day (round 4).

### 0.2 The prototype's phase split

Prototype: one thread per 64-candidate word testing 256 primes by a
multiply-high remainder; a prefix sum and an expand kernel to list the
survivors; the first test writing a flag per survivor; a device
compaction; the run kernel; a device filter. One launch of 2^22 words at
p = 5·10^16 on the quintic line, 9.3 ms, 2.90·10^11 p/s:

| phase | ms | share |
|---|---|---|
| sieve | 0.79 | 8% |
| prefix sum, offsets | 0.12 | 1% |
| expand | 0.99 | 10% |
| first test (9.5·10^9 modular powers/s) | 5.32 | 55% |
| compaction | 0.74 | 8% |
| run | 1.40 | 14% |
| filter and read-back | 0.27 | 3% |

12.08 sieve survivors per word against 4.1 primes: 2.9 modular powers per
prime. Single readings of the sieve depth: 64 primes 2.74·10^11, 256
primes 2.90·10^11, 1024 primes 2.61·10^11 (the per-word sieve costs a
remainder per prime per word).

### 0.3 The published terms are late: a Chebyshev bias, measured

The first model — each of the first n primes a residue independently, one
prime of the class in (power)^n — failed its validation on the published
terms: the 51 exposures between consecutive distinct terms average 1.69
where independence gives 1 (Kolmogorov–Smirnov 0.341 against 0.190). Before
fitting anything the engine was suspected and cleared, and the bias was
located:

- **Device = CPU on every high run.** 7th-power line, p from 10^8 to
  3.1·10^9, floor 4: 9,776 primes (8,432 of run 4, 1,147 of run 5, 175,
  20, 1, 1), identical lists, against 10,002 expected at independence.
- **The device census, p from 10^8 to 3·10^10** (observed over expected at
  independence, runs ≥ 1, 2, ...): quintic 1.000, 1.000, 1.000, 0.997,
  0.991, 0.982, 0.982; 7th power 1.000, 1.000, 0.998, 0.987, 0.975, 0.968.
- **One residue condition, quintic class below 4·10^7** (608,253 primes;
  every power taken in Python): averaged over the first 24 primes the
  count is 88.6 below the 121,650.6 expected. The explicit formula
  predicts (1 − 1/5) times the square root of the height over four times
  its logarithm, 72.3: the prime ideals of degree two of the field — over
  the primes that are 4 mod 5 — have every integer as a quintic residue and
  are charged against the class of primes with a trivial symbol.
- **Conditions on several primes at once** (all subsets of the first 24
  primes, same data): the deficit is 54.4 for pairs (0.22% of
  expectation), 23.4 for triples (0.48%), 9.2, 3.5 and 1.3 for sets of
  four, five and six (0.95%, 1.8%, 3.4%) — it falls per character as the
  product of the primes grows, far faster than the uniform 90 the formula
  gives if every character carried the full bias. Subsets of the first
  eight primes show it (84.9, 44.3, 19.6 for pairs, triples, fours);
  subsets of the last eight do not (−23, −18, −4).
- **The leading primes, below 2·10^7**: 2,477 primes of run ≥ 3 against
  2,540.7, 451 of run ≥ 4 against 508.1, 91 against 101.6, 13 against 20.3.

So the lateness is arithmetic and concentrated exactly where a first
occurrence lives — small primes, low heights relative to (power)^n — and no
closed form is claimed for it there. The model carries one fitted
constant, LATE = 0.59 (maximum likelihood over the 51 exposures, standard
error 0.08; earlier half of the terms 0.52, later half 0.67), with which
the same test passes (0.149). Gate M1 requires both the failure and the
pass.

## Round 1 — the sieve and the compaction

### 1.1 A deep block sieve in local memory — REJECTED (0.63x to 0.72x)

Cost model: the sieve was 8% and 2.9 modular powers were spent per prime,
so sieve deeper and cheaper — one thread per 64 words (4,096 candidates)
holding its block in a local array, marking the multiples of each prime
(about 3,800 marks and 3,500 remainders per block for the primes to
32,768, a third of the per-word sieve's instructions at twelve times the
depth), survivors appended in the same kernel. The model said 1.3x to 1.6x.

Measured by phase on the SCORE window, one launch of 2^22 words (stream
identical): at 256 primes the sieve kernel 5.50 ms, the first test 5.90,
the run 1.77 — 13.3 ms against the prototype's 9.6, **0.72x**; at 3,072
primes the sieve 9.88, the first test 3.79 (8.76 survivors a word), the
run 1.42 — 15.2 ms, **0.63x**. The first test did shrink with the depth,
as modelled; the sieve ate it twice over. Knocking parts out of the sieve
kernel (256 primes, ms): full 4.66; without the output writes 3.90;
without the marking 2.48; without marking or output 0.08. **The marking is
the cost**: 1.2·10^8 read-modify-writes of thread-local memory in 3.8 ms.
With 512 bytes of block per thread the local arrays of the threads
resident on a multiprocessor exceed its first-level cache. The instruction
count was right and irrelevant.

(The paired end-to-end run of this engine read 0.596 at 256 primes, 0.538
at 1,024, 0.495 at 3,072, 0.471 at 6,000, 0.437 at 12,000 and 0.391 at
24,000 against the prototype — the right ordering, but taken at floor 3
and so carrying the host-sort distortion of 1.3 below, about 1.5x against
the new engine. The phase sums are the ratios to quote.)

### 1.2 A register sieve, compaction in the kernels, the test as a square root — SHIPPED (1.20x)

- **Sieve**: one thread per four words (256 candidates) held in four
  registers; the primes below 64 by pattern, a larger prime marks its at
  most four multiples by selects. No local memory. Per (word, prime) it
  costs about half the per-word sieve.
- **Compaction in the kernels**: the sieve thread reserves its survivors'
  slots with one atomic add and writes them; the first test appends the
  candidates that pass; the run kernel appends those at the floor. The
  prefix sum, the expand kernel, the flag array, the device compaction and
  the filter are gone; the order is restored on the host for the handful
  that reach it.
- **The first test as a square root**: 2^((p−1)/10) ≡ ±1 on the quintic
  line instead of 2^((p−1)/5) ≡ 1 — one squaring fewer in 57, and a
  stronger compositeness test (83 composites among the first 65,536
  candidates of the five lines pass it with the sieve off, against 149
  before; gate P5).

Phase split, one launch of 2^22 words on the SCORE window, 512 primes:
sieve with output 1.71 ms (21%), first test 4.72 (57%), run 1.63 (20%),
read-back 0.14 — 8.26 ms against the prototype's 9.6.

Paired and interleaved against the prototype, stream identical, at every
family's day-long height (floor 6, 5, 4, 4, 4; 7 to 9 rounds of 2^30
candidates):

| entry, height | prototype (p/s) | 384 primes | 512 primes | 768 primes |
|---|---|---|---|---|
| A002226, 8.5·10^16 | 3.10·10^11 | 1.180 | **1.196** | 1.156 |
| A002227, 6.2·10^16 | 4.86·10^11 | 1.193 | **1.204** | 1.149 |
| A002228, 1.7·10^17 | 8.70·10^11 | 1.197 | **1.208** | 1.144 |
| A060363, 1.6·10^17 | 1.05·10^12 | 1.206 | **1.205** | 1.142 |
| A060364, 4.3·10^17 | 1.37·10^12 | 1.203 | **1.200** | 1.123 |

Depth sweep on the SCORE window: 128 primes 1.037, 256 1.133, 384 1.180,
512 1.196, 768 1.156, 1,024 1.101, 2,048 0.942. One constant, 512, for all
five families: no cliff on either side, and 384 ties it within the noise.

### 1.3 A trap in the first A/B: the benchmark's floor

The first paired run of 1.2 read **0.75x**. The harness asked for floor 3,
which hands the host 138,000 survivors a launch, and the new engine sorts
its output on the host: 5 ms of `argsort` per 8 ms launch. A campaign's
floor at the day-long filters hands over nothing in a thousand launches
(below). At floor 6 the same engines read 1.196x. The frozen shapes'
floors were moved to about one prime of the class in 10^4 for the same
reason; a shape that hands the host more than a campaign does measures the
host.

### 1.4 The launch size

SCORE window, 512 primes, against 2^22 words: 2^20 0.902, 2^21 0.966, 2^23
1.026, 2^24 1.040. **2^23 shipped** (about 0.7 GB of device buffers).
2^24 declined: 1.4% more for twice the memory and a 20 ms first-test
kernel on a device the desktop shares — 1.4% of the 2.7-day median to
a(21) of A002226 is 55 minutes.

## Round 2 — the first test under Nsight Compute

**Profile** (`ncu --set full`, kernel `rl_test2`, one launch of 2^22 words
on the SCORE window from a scratch harness; 44 passes): duration 5.31 ms;
compute throughput 79%, memory throughput 4%; executed IPC 2.34; issue
slots busy 58.4%, **no eligible warp 41.6% of the time**; warp cycles per
issued instruction 20.1, of which 6.9 stalled waiting on the execution
pipe; the ALU the busiest pipe at 61.6%; occupancy 97.8% of a theoretical
100% (12 warps a scheduler, 30 registers a thread). The kernel is not
memory-bound and not occupancy-bound: each warp carries one chain of
dependent wide multiplies and waits on it.

### 2.1 Two candidates per thread, squarings interleaved — SHIPPED (1.02x to 1.04x)

Two independent chains per warp. A shorter exponent starts at 1, whose
squares stay 1 until its own leading bit, so a pair that straddles a power
of two needs no special case. Paired and interleaved against round 1's
engine, stream and fingerprints identical: 1.027 at the SCORE window (21
rounds), 1.016 on A002227 at 6.2·10^16, 1.034 on A002228 at 1.7·10^17,
1.031 on A060363 at 1.6·10^17, 1.038 on A060364 at 4.3·10^17 (15 rounds
each). Smaller than the idle issue slots suggested: the stall is the ALU
pipe's capacity more than the chain's latency. The profile of the changed
kernel was not taken.

## Round 3 — the Codex review: RSL-005, and what it opened

Codex's static review of engine v1 (2026-11-21,
[codex-reviews/](codex-reviews/README.md)) proposed a shorter first power
(RSL-005). This round tested it and every arm it suggested, re-measured the
phase split, and found two larger things beside it.

**Targets named first (rule 3b)**: the day-long filters of round 0 —
A002226 a(21) at 8.5·10^16 (the SCORE window, where every arm below was
measured unless it names another height), A002227 a(17) at 6.2·10^16,
A002228 a(14), A060363 a(13), A060364 a(12) — and the shipped engine was
re-measured at all five and at the five openings. The round's own result
moved one of them: see 3.6.

**Phase split first**, one launch of 2^23 words on the SCORE window (ms):
sieve 3.20, first test 10.88, run 3.50 — 17.7 with the phase barriers in.
The first test is 61% and the run 20%.

### 3.1 The first test as 2^(−j), started five squarings in — SHIPPED (RSL-005)

The review's identity, rechecked before use. With t = j + 64, k the bit
length of t less 6, h = ⌈t/2^k⌉ (32 to 64) and b = h·2^k − t (0 ≤ b <
2^k): the word 2^(64−h) is already the Montgomery form of 2^(−h); k
Montgomery squarings, each followed by a doubling where the matching bit
of b is set, take the exponent to −t; and the Montgomery form of 2^(−t) is
2^(−j) itself, compared with 1 and N − 1 as it stands. 2^(−j) ≡ ±1 exactly
when 2^j ≡ ±1, for any odd N, so the raw pass stream is the same on
composites too (gate P7 checks it on every candidate of thirty windows,
42 of the passes composite). 47 squarings for 52 at the SCORE height, and
no remainder: the kernel never needs 2^64 mod N. One k per thread, taken
from the larger of its two exponents, with h computed per lane — a lane
with a shorter exponent has a smaller h and nothing is padded (the review's
warning about squaring the shorter lane's seed).

### 3.2 Lazy reduction below 2^60 — SHIPPED (the largest single arm)

Listed in v1's "Unsearched" at "a few percent by instruction count". While
every candidate of a launch is below 2^60 a Montgomery square of a < 4N is
returned as hi − mh + N, in (0, 2N) (hi < 16N²/2^64 < N), and a doubling of
that is below 4N again: the squaring loop of the first test has no
conditional subtraction at all. A launch that reaches 2^60 runs the same
kernels canonically; gate P1 puts a window on each side of the boundary,
the lazy one against 2^60 where the bound is tightest.

### 3.3 The run in stages — SHIPPED (not in the review)

The run kernel did 6.8·10^8 Montgomery products in 3.5 ms where the first
test did 4.8·10^9 in 10.9: less than half as efficient per product. The
cause is warp divergence: four threads in five leave the loop at the base
3, and a warp idles until its last thread is done — with 32 threads it
almost always reads on to the base 5 and usually to 7. So the bases are
taken one per kernel, each appending its passes for the next: `rl_base3`
(two candidates per thread, lazy, the multiplication by 3 as two
additions), then the base 5 through `rl_run` restricted to one base, then
`rl_run` from 7. A stage is used only below the floor (gate P8: the stream
at floors 2 to 5 is the floor-1 stream, which runs none, filtered). Run
phases after: 0.71 + 0.23 + 0.19 ms for 3.50.

### 3.4 The arms, paired and interleaved

All on the SCORE window with launches of 2^23 words; every run of every arm
compared with v1's survivors, and all fourteen arms compared with v1's raw
stream (index, run, sieve and pass counts) on 2,800 launches of 4,096 words
at floors 1 to 4 and ten heights from the line's first candidate to the
ceiling — no difference.

Against v1 (9 rounds):

| arm | ratio |
|---|---|
| 3.1 alone (canonical) | 1.092 |
| 3.1 + 3.2 | 1.215 |
| 3.3 alone, one stage / two stages | 1.126 / 1.143 |
| 3.1 + 3.2 + 3.3 (two stages) | 1.423 |

Then against the combined arm (21 and 25 rounds, quartiles in brackets):

| change | ratio | |
|---|---|---|
| the first test written over lane arrays (unrolled) instead of twice by hand | 1.084 [1.072, 1.099] | **shipped** — the same source to the eye; the compiler's code differs |
| one lane a thread instead of two | 0.880 | two stand |
| three lanes / four lanes | 1.004 / 0.982 | declined |
| a square from three 32-bit products instead of the two 64-bit operations | 0.927 [0.903, 0.940] | declined |
| the seed through one Montgomery reduction (h to 128, one squaring fewer) | 0.988 | declined |
| the Newton inverse with its first two steps in 32 bits | 1.004 | declined (noise; simpler without) |
| exponent bits left-aligned and a shift-free doubling | 0.979 [0.974, 0.983] | declined |
| 2^64 mod N from the launch's quotient (RSL-005's second proposal) in the run kernels | 0.998 | declined: the first test takes no remainder now, and these kernels are 11% of a launch |
| one stage instead of two | 0.980 | two stand |
| the canonical kernels instead of the lazy ones | 0.844 | lazy stands |
| blocks of 64 / 128 / 192 / 512 threads in the first test | 1.003 / 1.002 / 1.002 / 0.996 | 256 stands |

The instruction count misled in both directions again (the hand square and
the aligned bits lose; the array form wins for no visible reason).

**Constants re-swept on the new engine** (21 rounds, against 512 primes and
2^23 words): 192 primes 0.926, 256 0.958, 320 0.983, 384 1.003, 448 1.002,
640 0.975 — 512 stands, no cliff. On the shipped engine, 41 rounds at each
of the five day-long shapes (SCORE, then A002227 at 4.5·10^17, A002228,
A060363, A060364), against 512: 320 primes 0.970, 0.982, 0.992, 0.994,
1.003; 384 primes 0.963, 0.999, 1.003, 1.015, 1.017; 448 primes 0.988,
1.004, 1.005, 1.003, 1.008 — one constant for the five families, a tie
above the quintic line and the best there. Launch size: 2^22 0.955, **2^24
1.032 [1.018, 1.069]**, and at every height (below).

### 3.5 The launch of 2^24 words — SHIPPED

Declined in 1.4 at +1.4% for twice the buffers and a 20 ms first-test
kernel. On this engine it is worth 1.5% to 7% at every shape (the fixed
cost of a launch is 150 to 240 microseconds, and each kernel's ramp is paid
once per launch), and its longest kernel, the first test, is about 12 ms —
v1's was 11 at 2^23. Price: about 1.6 GB of device buffers for 0.7.
`--gpu-yield-ms` and `--gentle` are unchanged.

| shape (15 and 11 rounds, against v1) | 2^23 words | 2^24 words |
|---|---|---|
| SCORE, A002226 at 8.5·10^16 | 1.479 | 1.587 |
| A002227 at 6.2·10^16 | 1.459 | 1.513 |
| A002228 at 1.7·10^17 | 1.419 | 1.440 |
| A060363 at 1.6·10^17 | 1.396 | 1.435 |
| A060364 at 4.3·10^17 | 1.381 | 1.425 |
| the openings at 2^42, in the same order | 1.541, 1.484, 1.353, 1.373, 1.370 | 1.623, 1.505, 1.451, 1.432, 1.425 |

### 3.6 Engine v2 as integrated — the ratios that ship

The project's `residue_gpu.py` against the copy of v1 taken before the
port, paired and interleaved on 2^30 candidates (15 rounds at the day-long
heights, 9 at the openings), survivors identical on every run:

| shape | v1 (p/s) | v2 (p/s) | ratio |
|---|---|---|---|
| SCORE: A002226, 8.5·10^16 | 3.745·10^11 | 5.861·10^11 | **1.576** [1.556, 1.613] |
| A002227, 4.5·10^17 (its a(18)) | 5.806·10^11 | 8.766·10^11 | **1.528** [1.458, 1.540] |
| A002227, 6.2·10^16 (its a(17)) | 6.134·10^11 | 9.192·10^11 | 1.506 [1.468, 1.509] |
| A002228, 1.7·10^17 | 1.051·10^12 | 1.524·10^12 | **1.445** [1.425, 1.479] |
| A060363, 1.6·10^17 | 1.247·10^12 | 1.781·10^12 | **1.417** [1.392, 1.479] |
| A060364, 4.3·10^17 | 1.672·10^12 | 2.419·10^12 | **1.447** [1.366, 1.478] |
| openings at 2^42, A002226 to A060364 | | | 1.622, 1.552, 1.494, 1.474, 1.370 |

The gain falls with the power because the sieve, unchanged, is a larger
share where fewer primes pass the first test. Phase split of the shipped
arrangement (2^23 words, SCORE window, ms): sieve 2.98, first test 5.88,
the base 3 0.71, the base 5 0.23, the run 0.19, read-back 0.13 — first test
58%, sieve 29%.

**The day-long filter of A002227 moved.** At v2's rate the median clock of
its a(17) is 20 hours; the first term of a day or more is a(18), median
4.5·10^17, 6.2 days. `DAY_A002227` was re-frozen there (BENCHMARKS.md), the
ratio above measured there, and the model's rate for the family is that
shape's. The other four keep their filters (42 h, 31 h, 24 h, 48 h).

**The fingerprints were re-frozen, deliberately, twice over**: one launch
of 2^24 words covers the 2^30 candidates that two of 2^23 did, so the
per-launch entries change; and each survivor is now one word that binds its
run to its prime (RSL-008: the XOR of p ^ run·2^56 is unchanged when two
primes exchange their runs; gate P6 plants it). The survivors themselves
did not change: for all ten windows v1 reproduced its frozen fingerprint
and v2 returned the identical primes, runs, sieve count and pass count
before the new values were written.

**Nsight Compute, the new first test** (`rl_test2_lazy`, one launch of 2^22
words on the SCORE window; `--set full`, 44 passes): 3.21 ms for v1's 5.31;
compute throughput 88%, memory 6%; executed IPC 2.06; issue slots busy
51%, no eligible warp 49%; 19.0 warp cycles per issued instruction, 8.9 of
them stalled on the execution pipe; the ALU the busiest pipe at 46%; 42
registers a thread (30 in v1), theoretical occupancy 83% (five blocks of
256 threads a multiprocessor instead of six). Occupancy is not what binds:
blocks of 128 and 192 threads restore it and change nothing (3.4).

## The loop

*(Measured on engine v1; see "Not re-measured" below.)* The campaign loop
against its own device time, driven by a scratch harness
over known line with a scratch checkpoint (a fresh campaign to p =
4.39·10^12, every published term rediscovered):

| entry | wall | device | launches | host | wall/device, last stretch (p from 2·10^12) |
|---|---|---|---|---|---|
| A002226 | 12.1 s | 9.8 s | 834 | 2.3 s (71,986 survivors) | 1.042 (4.17·10^11 p/s) |
| A002227 | 6.9 s | 6.0 s | 593 | 0.9 s (34,255) | — |
| A060364 | 2.8 s | 2.0 s | 248 | 0.8 s (29,240) | 1.021 (1.95·10^12 p/s) |

The host's share is the opening: while the floor climbs through the
published terms a launch hands over up to 3,000 primes, and the launches
are cut to that budget. Nothing in the loop calls the odds model (the
ladder is cached on the frontier; the wiring drill counts one build for
fifty reads).

**Host paths, priced by counted rate (CLAUDE.md rule 5k).** The one
per-item host step is the verification of a survivor: Miller–Rabin and the
run re-read, 60 microseconds at p = 8.5·10^16 (2,278 survivors timed; 19
to 25 at 10^12), none slower than 0.4 ms. At the day-long filters the
device hands over nothing: counted over 8 launches at each campaign floor,
0 survivors, and from the counted density of run ≥ 3 —

- A002226 host verification at the a(21) filter (floor 16): never in 1,000
  windows (0 of 1,000), 6.03e-05 s each -> 0% of 0.0171 s windows (274,975
  primes of run ≥ 3 per launch, times 5^−13: 0.2 per 1,000 launches)
- A002227 at the a(17) filter (floor 13): never in 1,000 windows, 0% of
  0.0129 s windows (94,675 times 7^−10)
- A002228 at the a(14) filter (floor 11): never in 1,000 windows, 0% of
  0.0109 s windows (22,347 times 11^−8)
- A060363 at the a(13) filter (floor 10): never in 1,000 windows, 0% of
  0.0106 s windows (13,265 times 13^−7)
- A060364 at the a(12) filter (floor 9): never in 1,000 windows, 0% of
  0.0104 s windows (5,729 times 17^−6)

Over a whole term's stretch the host is handed about (power)^depth primes
— 3,125, 2,401, 1,331, 2,197, 4,913 — a fraction of a second against
hours. The canary stretch is the exception and is bounded: 3.8% of the
last 5.7 seconds of the quintic opening.

**A find's confirmations** (timed on a(15) of A002226 and on a prime of
the SCORE window): the independent leg 1 ms, the re-derivation 25 ms. Slow
by design, declared to the host-cost monitor, and nowhere near a launch.

## The launcher and the model after the Codex review

The review's other findings are about the campaign, not the engine. Each
was checked against the source first; all four launcher findings were real.

- **RSL-003, Ctrl+C saved nothing.** `Campaign.run` removed its boundary
  callback in a `finally`, which runs while the interrupt unwinds — before
  `shutdown.graceful` catches it. The callback now stays registered through
  an interrupt and is removed on a normal return or any other exception.
  The interrupt drill stops a campaign in its fourth segment: the file held
  the first segment's cursor (the periodic save is throttled to the
  heartbeat), the callback writes the third boundary, and a run resumed
  from it ends in the state of an uninterrupted one. **Not changed, and the
  owner's to decide**: `huntlib.checkpoint.load` reads a missing live file
  with a `.bak` beside it as "no checkpoint" (a stop between the two
  renames of a save — about a millisecond in each save, so of the order of
  3·10^-5 per hard stop at a save every 30 seconds — would restart a
  campaign at the line's first candidate), and hl-records' launcher has the
  same `finally` (PAUSED; not touched from here).
- **RSL-001, the interval is exact.** `--to` is read as an integer by
  `decimal` (a float cannot hold one above 2^53) and is inclusive; a window
  classifies exactly its indices and discards the padding of the device's
  last word; where that padding would cross 2^63 the launch is moved back
  to end on the last candidate. v1 left 12, 36, 52, 44 and 3 candidates of
  the five lines unswept under the ceiling while reporting it reached.
  `raw_window` had the matching fault and a find's confirmation windows
  reached past the ceiling; both are clipped. Gate P0 sweeps the last 1,000
  and the last 37 candidates of each line against the CPU engine; the drill
  starts every family 0 to 63 candidates below 2^63.
- **RSL-002, a find is published at the boundary.** The three confirmations
  run where the prime is met and the frontier moves at once; the evidence
  file, the ledger row and the `[DISCOVERY]` line wait for the canary and
  parity checks of the segment. An alarm leaves nothing public. A ledger
  that already gives one of the indices to another prime halts the run.
- **RSL-004, a run of 40 is a lower bound.** A prime that fills the cap
  halts the campaign instead of reaching a witness builder that indexed
  past its list. Not extended past 40 primes: over the whole line below
  2^63 the expectation of such a prime is under 10^-10. A composite does
  fill it — 4406163138721 = 9433 · 14149 · 33013, a Carmichael number, is a
  device survivor of run 40 in the frozen window OPEN_A002226 — and the
  host's primality proof drops it before anything reads its run.
- **RSL-007, the forecasts.** They start at `residue_model.origin`: the
  last published term or the bound the entry states above it (v1 put 5.8%
  of A002227's a(13) and 0.5% of A060363's a(9) on intervals stated
  empty). The fit counts those two intervals as exposure without an event
  (0.5912 for 0.5919). And the fitted rate is now judged against the right
  null: for a rate estimated from the same 51 values the 5% point of the
  Kolmogorov–Smirnov distance is 0.149 and the 1% point 0.176 (20,000
  simulated samples), so the measured 0.149 is p = 0.05 — marginal, where
  the fixed-distribution cutoff 0.190 had called it a pass.
  `model_results.json` was reissued; no campaign had run.

**Not re-measured: the loop.** The table below is v1's. The loop's code
path is unchanged except for the exact window and the publication step, the
host is handed the same primes, and the device is 1.4 to 1.6 times faster,
so the opening stretch's wall/device ratio (1.02 to 1.04) should be read as
1.03 to 1.06 until the owner's first run says. The agent's harness for it
drives the campaign class and was not run again.

## Round 4 — RSL-006: a sieve in the cyclotomic field, prototyped

The review's research item, for A002226 only. Verified, built as a scratch
prototype on the device, and measured. **Not an engine**: nothing of it is
in the tree, and no line was swept with it that a campaign has not.

**The mathematics, as checked.** In Z[ζ], ζ a primitive fifth root of
unity, every prime p ≡ 1 mod 5 is the norm of an element α = c_0 + c_1ζ +
c_2ζ² + c_3ζ³ (class number one). Normalised to be congruent to a rational
integer mod (1 − ζ)² — Σc_i ≢ 0 and Σ i·c_i ≡ 0 mod 5 — Eisenstein's law
makes "q is a quintic residue mod p" a condition on (c_0, c_1, c_2, c_3)
mod q, for every prime q ≠ 5. So the residue conditions can be sieved, in
four coordinates, with one table per prime q.

- *The review's box* (X = 2·10^6): the prime norms of the admitted
  elements are exactly the 13 primes below X of which 2, 3, 7, 13 and 17
  are quintic residues; each prime has 34 to 64 representatives in it.
- *A smaller region* (this round's): with A and B the absolute values of α
  under ζ → e^(2πi/5) and ζ → e^(4πi/5), the elements with 1 ≤ A/B < φ and
  the first embedding in the closed first quadrant hold **one** generator
  per prime — measured 1.000 (13 of 13, each once) — because the real unit
  φ moves A/B by φ², the Galois map ζ → ζ² exchanges A and B, and ±1 with
  complex conjugation move the first embedding through the four quadrants.
  Counts per unit of norm: 3.398 in 1 ≤ A/B < φ² (3.40 predicted from the
  class-number formula), 0.4255 in the region (0.425), 0.0681 normalised
  (0.068) — against 0.1 candidates per unit of p on the integer line.
- *The tables*: for q = 2, 3, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43,
  47, 53 (inert, split and of degree two), the symbol computed in Z[ζ]/(q)
  agrees with Euler's criterion on every one of 381,134 normalised elements
  of prime norm below 4·10^5.

**The prototype.** One device thread per line in c_0, for (c_1, c_2, c_3)
in the 550 classes mod 30 that the conditions at 2, 3 and 5 leave non-empty
(of 27,000). A line's c_0 interval comes from the region's bounds in double
precision, widened; its 64 points a word are sieved by bit patterns — the
30-periodic one, then 7, 11, 13 held in registers (a q-bit pattern rotated
and replicated by one multiplication, no memory touched per word), further
primes loaded only for a word that survives. Survivors are appended; the
host takes the exact norm in integers, proves primality and reads the run.

| measurement | result |
|---|---|
| every prime of run ≥ 11 in [2^20, 2^42), 22 shells of ratio 2 | **717 of 717 identical** to engine v2's stream; 0.6 s of device against 6.2 s |
| the shell [2^41, 2^42) | 167 ms: 1.3·10^13 p/s, 19 times v2 at that height |
| a slice (5 of 550 classes) of the shell [8.5·10^16, 1.7·10^17), tables to 53 | 9.02 s, so 992 s for the shell: **8.57·10^13 p/s, 146 times** v2's 5.86·10^11 (40 hours for the same shell) |
| completeness at the day-long height: every prime of run ≥ 11 in [8.5·10^16, 8.504·10^16) | **5,270 of 5,270 identical** to engine v2 (runs 11: 4,208; 12: 867; 13: 151; 14: 33; 15: 9; 16: 1; 18: 1) |

The window of the last row holds a prime of run 18, so a(16), a(17) and
a(18) of A002226 are below 8.504·10^16 — an upper bound from a validation
window, not a term.

**What the prototype does not do, with prices.**
- Its c_0 intervals are the region's crude bounds: over a shell of ratio 2
  it sieves 0.018 lattice points per unit of norm where the region holds
  0.0087 on those classes — 2.1 times the necessary words; and a thin
  shell costs what a thick one does (the 4·10^13 window above took 421 s,
  against 69 s for v2 on the same window). An engine needs the exact
  interval from the norm's quartic in c_0, which also makes the shell's
  thickness a free choice.
- Rejecting lines outside the region is about a tenth of the shell
  (1.8·10^12 threads at 1.7·10^17).
- At a campaign's floor (11 at the open frontier) the tables stop at 31 and
  leave about 6·10^8 elements per shell of ratio 2 at 8.5·10^16: the device
  must take their norms and run the integer kernels on them (the base 5 and
  the compositeness test) — a twentieth of a second of the first test per
  992 s shell, by its measured rate. The prototype instead used tables to
  53 for its timing and left the norms to the host.
- A shell is a coverage unit: a find is confirmed when the shell that holds
  it closes (rule 5j). At 146 times the rate a shell of ratio 2 at the
  day-long filter is minutes, against hours saved; to be priced with the
  engine's own shell size.
- Double precision carries the geometry; exactness lives in the integer
  norm. Above 2^63 the norm needs two words on the device or the host —
  the coordinates do not (they are 3·10^4 at 10^17).

**Disposition.** RSL-006 is real and is the largest lever this project has
measured: on the quintic line the shell to a(21)'s median is 17 minutes of
device time on an untuned prototype, and 2^63 is about a day and a half
rather than 190. A production engine is a second device engine for
A002226 with its own parity gates (against the integer engine, which stays
the engine of the other four families and the referee of this one), a
completeness proof written beside the code, and a campaign whose unit is a
shell. It is a project of its own, and — since any test of it at an open
height finds terms — the owner's to direct.

## Unsearched, with prices

- **The field sieve as an engine (quintic line)**: round 4. 146 times on
  the prototype; the exact interval is worth up to 2.1 times more on top.
- **The same idea for the 7th-power line** needs Z[ζ_7]: six coordinates,
  two independent real units, lines of about 600 points at 10^17. Not
  examined. Beyond it (degrees 10, 12, 16) the lines are a few points long.
- **The sieve kernel** is now 29% of a launch and was not touched: 512
  primes against 384 is a tie at every height (3.4), so a cheaper sieve per
  prime is what would move it. Not attempted; a sieve at no cost would be
  1.4 times.
- **A deeper sieve by a block in local memory**: 0.39 to 0.72 times (1.1).
- **The first test's remaining stall** is the execution pipe (round 3's
  profile): no arm of 3.4 that rearranged its instructions paid.
- **Three stages instead of two** (the base 7 in its own kernel): the run
  kernel after two stages is 0.19 ms of 10.1. Under 1%.
- **A launch of 2^25 words**: 3 GB of buffers and a 23 ms kernel; not
  measured.
