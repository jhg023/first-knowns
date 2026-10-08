# OPTIMIZATION_LOG — primorial-runs

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt → measurement → kept/rejected, failures included. This
project starts from primorial-ladders' engine v1 and planner p1, whose own
log (and plus-two-cliques', product-cliques', clique-ladders',
factorial-ladders' and lcm-ladders' before it) holds the rounds that
produced the window sieve. What is here is what was measured and decided
in making that engine hunt the exact-run primorial shift ladders.
Harnesses were scratch scripts, not committed; each measurement below gives
enough of its method to rewrite one in ten minutes.

---

## Decision 1 (2026-10-05) — primorial-ladders' engine, taken whole

**Why that engine.** The problem is primorial-ladders' A115786 with the
list of shifts changed: one unknown prime p, and conditions that are p
plus an additive constant built from the primorials. The regime is the
same too. A primorial is 0 modulo q from prime(n) ≥ q on, so on all three
entries a prime q kills at most 1 + min(n, π(q) − 1) residues — psq(n) is
0 from there, the residue p itself kills, and pps(n) and pssq(n) stop
moving — and the wheel is weak: the primes to 59 keep 1.6×10⁻⁴ of the line
on A257466, 4.7×10⁻⁴ on A257467 and about 3×10⁻⁴ on A258035 (primorial-
ladders: 2.4×10⁻⁴). What has to be paid is candidates, and the window
sieve is the engine in this repository with the highest candidate rate.

**What changed, and what did not.** The kernel never sees a form: it
consumes the residues each prime kills, built from
`runs_search.killed_residues`, which is {minus each constant mod q} over
`runs_reference.constants`. So:

* *changed, in the oracle:* the shift function (`shift_k`: pps, psq, pssq),
  the definition of a term (a prime whose run is **exactly** its index),
  the floor (2 at every index: the sequences are not monotone), the
  published tables, and the erratum on A258035 (README, "The problem");
* *changed, in the CPU engine:* the domain and run-length readers follow
  the oracle; the exception zone is [2, sieve depth] at every filter and
  its walk adds 2 and 3 to the forced class; a measured ceiling on the
  values and the last index under it (Measurement 1);
* *changed, in the launcher:* the classification reads every survivor's
  run to its end, a run longer than the filter is a discovery of its own
  index while the filter stays, the frontier is the index below the lowest
  open one and can jump over indices found early, and a stopper with no
  factor found is recorded with its failed base-2 strong probable-prime
  test;
* *changed, in the model:* the intensity of a run of exactly n is that of
  at least n less that of at least n + 1, every index integrated from the
  bottom of the line;
* *not changed:* one line of device code, the planner, or any tuning
  constant. The gate families were re-pointed (the sparsest killed sets,
  A257467's, take the place the per-index family had), one parity window
  was deepened from a sieve of 32 to 64 because A257467's sparser kills
  overflowed the survivor buffer in one launch there, and G9 then passed on
  29 populated windows (749,295 survivors).

**The exact run costs the device nothing.** The condition that the next
shifted value is *not* prime cannot be sieved and is not: a sieve at
filter n is exactly the sieve of the monotone problem "a run of at least
n". The exactness is paid on the host, and only by survivors whose run
reaches the filter.

---

## Measurement 1 (2026-10-05) — the ceiling on the values (rule 5h)

**Why it is owed.** The term never comes near huntlib's 10⁴⁰ here: the
open terms are below 10²⁴. What grows is the shift — psq(20) = (71#)² is
3.1×10⁵³ — and a discovery of a run of n needs a certificate for every
value up to p plus its n-th shift. A value here has no multiplier × term
± 1 structure, so N − 1 and N + 1 are numbers like any other and each
value is proved by `huntlib.certificate.prove`'s own bounded search. Rule
5h asks for that search to be measured at the height rather than assumed
from the 10⁴⁰ default, which was measured for structured values.

**Method.** `huntlib.ceiling.subproof_rate(height, samples=12,
seed=20261005)`: twelve random primes just above each height (the next
prime after height plus a random tenth of it), each handed to
`certificate.prove` with its default effort and the proof re-verified by
`certificate.verify`; the count proved and the slowest single proof. CPU
only, one process.

| height | proved by the first search | slowest | all twelve |
|---|---|---|---|
| 10⁴⁵ | 11 of 12 | 2.75 s | 6.6 s |
| 10⁵⁰ | 12 of 12 | 1.34 s | 5.9 s |
| 10⁵⁵ | 12 of 12 | 1.79 s | 10.7 s |
| 10⁶⁰ | 12 of 12 | 1.96 s | 13.5 s |
| 10⁶⁵ | 10 of 12 | 2.28 s | 14.5 s |

**Decision.** `runs_search.V_CEIL = 10⁶⁰`, exclusive, on the values; a
family is hunted to the last index whose shift is under it (`n_max`: 36 on
A257466, 21 on A257467 and on A258035, where psq(22) = (79#)² = 1.0×10⁶¹ passes it). The
first search is not certain at any height (one miss in twelve at 10⁴⁵), so
the launcher retries a miss once with 200 ECM curves, and a value still
unproved is written as `unproved` in the evidence rather than hidden: the
find then stands on its three verification legs and the certificate is
owed by hand. 10⁶⁵ is where the first search starts to miss twice in
twelve; raising the ceiling there is the same measurement with the retry
included, and no campaign priced here reaches it.

**Not measured:** the retry's own success rate at 10⁶⁰, and the cost of a
factor witness for a composite stopper of that size (the launcher's
bounded effort is trial division, rho and 200 ECM curves, after which it
records the failed base-2 strong probable-prime test instead).

---

## Round 1 (2026-10-05) — the inherited engine measured on this problem

The kernel is primorial-ladders' engine v1 unchanged, so the question of
this round was not "what is slow" but "is anything inherited now wrong":
the killed sets are different (the squared families' are sparser), the
filters a campaign will spend days in are different, and every constant
was tuned elsewhere (OPTIMIZATION.md 3.4). Harnesses were scratch scripts:
`ab.py` builds one engine per arm at the campaign's own plan with one
override (a constructor argument or a module constant set for that build
only), then times every arm back to back each round on the same launches
at half the modelled median's height, device synchronised, and compares
the survivor streams; ratios are medians over six rounds with [min, max].

**Every filter priced** (BENCHMARKS.md, "Every opening, and the filters
after it, priced"): 22 filters across the three families. The filters that
last days are A257466's n = 21 (4.4 days to the median), A257467's n = 19
(2.5 days) and A258035's n = 19 (5.5 days); the sweeps below are at
A257467's n = 19, the sparsest killed sets and the slowest line.

**The sieve depth is not a throughput knob.** A257467 n = 19, paired:

| depth | device | ratio | survivors/s | host, core-s/s | stream |
|---|---|---|---|---|---|
| 2^16 (the plan) | 5.82e15 p/s | 1.000 | 14,999 | 0.17 | — |
| 2^15 | 5.81e15 | 0.998 [0.994, 1.002] | 54,552 | 0.59 | superset |
| 2^17 | 5.79e15 | 0.994 [0.992, 1.000] | 4,351 | 0.05 | subset |
| 2^14 | 5.82e15 | 0.997 [0.995, 1.008] | 214,692 | 2.21 | superset |

Flat to 0.6% over a factor of eight in depth and a factor of fifty in
survivors: the tail rounds cost nothing next to the window sieve. A knob
that flat is spent on the machine (CONVENTIONS.md, sizing rule 3), and the
plan's depth already asks for a fifth of a core. **Kept.**

**The window and round constants are at their optimum here too.** Same
filter, identical survivor streams on every arm:

| arm | ratio |
|---|---|
| BIT_SURV 0.0035 (default) | 1.000 |
| BIT_SURV 0.007 | 0.920 [0.910, 0.922] |
| BIT_SURV 0.002 | 0.996 [0.989, 1.000] |
| K2_SURV4 0.0003 (default 0.0001) | 0.980 [0.971, 0.984] |
| R2_DROP 0.35 (default 0.5) | 0.992 [0.979, 0.992] |
| LIT_MAX 48 (default 40) | 0.997 [0.985, 1.016] |
| window 224 periods (plan: 160) | 0.885 [0.871, 0.890] |
| window 128 periods | 0.936 [0.918, 0.939] |
| CAND_PER_LAUNCH4 2^38 (default 2^37) | 1.008 [0.993, 1.019] |
| CAND_PER_LAUNCH4 2^36 | 1.006 [0.989, 1.022] |
| XE1_REGS 64 (the extraction batch forced to one residue) | 1.001 [0.993, 1.007] |
| QWORD_BY_OCCUPANCY off | 0.998 [0.995, 1.002] |
| MASK_HOIST on (primorial-ladders' rejected arm) | 0.981 [0.974, 0.988] |

**Kept: every default.** Nothing above the noise in the direction of a
change; the launch size is flat both ways and stays.

**The planner's wheel, measured rather than modelled.** The plan is priced
on CREL constants, which are a cost model, so at the filter where the
choice is worth most -- A257466's n = 21, where the planner takes the
wheel to 53 on the wide record with a segment of half a median -- the
candidates were built and timed, paired over five rounds, and the model's
expected line to a CONFIRMED find (whole segments from the bottom of the
line) divided by each measured rate:

| wheel, window | device | segment / median | expected clock to a confirmed find |
|---|---|---|---|
| 12 primes to 47, 160 | 1.50e16 p/s | 0.00024 | 442 h |
| 12 primes to 47, 224 | 1.54e16 | 0.00034 | 432 h |
| 13 primes to 47, 160 | 1.96e16 | 0.010 | 338 h |
| **14 primes to 53, 160, wide (the plan)** | **2.55e16** | 0.53 | **289 h** |
| 14 primes to 53, 224, wide | 2.70e16 | 0.74 | 284 h |

The plan is 1.17x the best narrow wheel on the clock (1.30x on rate, less
the over-sweep of a half-median segment). The 224-period window reads 2%
better on the clock for a segment of three quarters of a median; that is
inside one session's noise and the planner's own tie rule takes the
shorter segment. **Kept.**

**Nsight Compute, one sieve launch at A257467 n = 19** (`ncu --set full`
on the fourth launch of a scratch harness that runs the planned engine):
33.7 ms; 72 registers a thread, seven blocks per SM with the registers and
the shared memory both binding at seven; achieved occupancy 58.06% of a
theoretical 58.33%; 2.69 instructions executed per active cycle; issue
slots 66.05% busy; compute and memory throughput both 85.5% of their
busiest pipe; L1 hit rate 82%, L2 98%; branch efficiency 71%. That is the
profile primorial-ladders measured for the same kernel at its own n = 19
(issue slots 66%, seven blocks, the window sieve at about 12.5
instructions a prime and window), on tables a third sparser: the kernel is
doing the same work per candidate here, and the difference between the
families is how many candidates a unit of line holds, which is the wheel's
business and not the kernel's.

### Priced and declined, without implementing

* **The wheel to 53 on A257467.** Its sparse killed sets leave so many
  residues per prime that the level splitter admits no wheel past 47 at
  n = 19 or n = 20 (`wheel_candidates` ends there), where A257466 takes 53
  at n = 21. 53 keeps at least 37 of its 53 classes there, so the wheel
  would hold 1.43x fewer candidates per unit of line, about 1.3x after the
  wide record's 0.91. At n = 19 its segment would be four medians, which
  no plan should take; it could only pay at n = 20, whose median is 74
  days away at today's rate. Not built: a splitter change for a filter no
  campaign priced here reaches.
* **A deeper or shallower sieve to move the host.** Flat (above); the
  host is a fifth to a half of a core at every filter that lasts.

### Where it stands (Part 3 of OPTIMIZATION.md)

| phase | verdict |
|---|---|
| the window sieve and extraction | the inherited verdict, re-checked on this problem: instruction-bound at the formulation's floor (primorial-ladders round 1 and plus-two-cliques round 2 hold the instruction-level pass); the same Nsight profile here, and every constant that feeds it re-swept flat at this problem's slowest filter |
| the in-block and tail rounds | K2_SURV4 and R2_DROP re-swept flat; the depth they serve is flat over 8x |
| launch overhead | CAND_PER_LAUNCH4 flat at 2^36-2^38 |
| host | 0.05-0.6 core-s per second at every filter past a minute; the pool is sized from a measurement at the filter |
| the campaign's plan | the wheel and window at the 4-day filter confirmed by measurement, 1.17x over the next choice |

No change to the engine or the planner came out of this round, and that is
the result: the engine arrived tuned for this regime because the regime is
primorial-ladders' (weak wheel, candidates are what is paid for). What the
round did NOT do: time the campaign's own segment loop over hours (rule
0a: the campaign is the owner's to start), or sweep at A258035's n = 19,
whose wheel differs from both others' -- the first thing to measure if that
family is the one hunted to its days-long filter.

---

## Round 2 (2026-10-05) — Nsight Compute at the days-long filters, and the quad window

Method as round 1: scratch harnesses through the engine API, the planned
engine at the filter, the same launches on every arm, every round every
arm back to back, the survivor count and xor compared on every run; the
median ratio over rounds with [min, max]. Nsight Compute (`ncu --set full`,
one sieve launch, the fourth of a scratch run; clocks locked by the tool at
2.01 GHz) and its per-instruction SASS counters, split by region at the
kernel's barriers and loop back-edges. The filters are the three a
campaign spends days in: **A257467 n = 19** (2.5 days), **A257466 n = 21**
(4.4 days, the wide record) and **A258035 n = 19** (5.5 days; never
measured before this round).

### Measurement 2 — the device split and the kernel, before anything changed

CUDA events around every kernel, 20-30 launches at each filter: the sieve
kernel is 95.3-95.8% of the device, the generated tail rounds 2.4-2.9%,
the generic tail 1.7-1.9%, the offset-table build 0.1%; device 99.4-99.6%
of wall through the engine API. Rates 5.77e15 / 2.56e16 / 1.03e16 p/s
(4.6 / 5.3 / 5.0e12 candidates a second), BENCHMARKS.md's table.

**Nsight, A257467 n = 19** (72 registers, 12,272 bytes of shared memory,
7 blocks per SM by registers and by shared memory alike, 58% occupancy):
69.9 million cycles, 23.4 billion warp instructions, IPC 2.69, issue slots
66% busy. **The LSU is the busiest pipe by instruction issue, at 85% of
its peak** (`l1tex__lsuin_requests`); the ALU pipe is at 71% of its cycles,
the shared-memory data path (`lsu_writeback`) at 74% with 6.51 billion
wavefronts, the FMA pipe at 18%. Warps stalled per issue: not selected
2.36, math-pipe throttle 1.71, wait 1.48, short scoreboard 0.97, dispatch
0.92, barrier 0.47, MIO throttle 0.45; no eligible warp on 33% of cycles.
Branch efficiency 71%. The same at A257466 n = 21 on the wide record (64
registers, 8 blocks): ALU 70%, issue 67%, the same stall profile.

**Where the instructions are** (SASS, by region): the window body 65.4% of
the executed instructions and 53.8% of the stall samples; the extraction
loops inside the residue loop 10.4% / 15.8%; the in-block rounds and the
tail push 22.8% / 20.7%; the prologue and its barrier 1.4% / 9.7%. Per
prime and 160-period window the window body is **13 instructions**: half
an IADD3 (the packed x0 + ne add), half a LOP3 and half a SHF (splitting
the packed halves), one IMAD.HI (the word index, fed straight into the
load's `.X8` scaling), **three LDS.64**, five SHF.R.W funnel shifts and
2.5 LOP3 (two words' ORs fused per LOP3) -- 11 for a periodic prime (one
LDS.128). The validity masks the inherited log counted as 35 instructions
a window now run on the uniform datapath (USEL/USHF/UISETP) and cost the
ALU nothing. Kernel-wide opcode mix: SHF.R.W 21%, LOP3 15%, LDS.64 10%,
IADD3 6%, IMAD.HI 6%, SHF.R.U32.HI 4%, IMAD.WIDE 4% (the rounds' Barrett
packs), BRA 3%, BSYNC/BSSY 3.4%, LDG 1.7% (the rounds' table gathers),
STS 1.5% (two stores per extracted survivor, the split queue entry).

So the window loop is at the floor of its formulation on BOTH pipes
(INNOVATION.md's verdict rule): one funnel shift and half an OR per output
word on the ALU, six words of pattern per five output words on the data
path, and the per-prime fixed cost already on the FMA and uniform pipes.
What the profile pointed at was the one mismatch between the two: three
LSU instructions a prime for six words that the data path moves in six
wavefronts whether they arrive as three 8-byte loads or as a 16-byte and
an 8-byte one.

### Measurement 3 — the padding ablation (blocks per SM priced on this kernel)

A `volatile __shared__` pad of 2, 4 and 6 KB added to the sieve kernel and
nothing else, at A257467 n = 19 on the quad kernel below (6 blocks per SM
without the pad), seven rounds of 40 launches: **5 blocks 0.975 / 0.970**
(two pads), **4 blocks 0.929**. The rate stops tracking blocks above five,
as the inherited log said, and a block below six is worth about 3%.

### The quad window (engine v2): kept

**WINDOW_QUAD_ALL.** Every window group's table laid out as overlapping
quads (entry w = words w..w+3, 16 bytes), so a prime whose window never
wraps reads entry w as one LDS.128 and the first half of entry w + 4 as one
LDS.64: two LSU instructions a prime instead of three, the same six
wavefronts, a table 4x the plain pattern (2x the pairs table: +2.4 KB at
A257467 n = 19, +1.8 KB at A257466 n = 21). Nsight on it at A257467 n = 19:
LSU issue **85% -> 69%**, shared loads 2.81 -> 2.06 billion, ALU 71%, the
data path still 74% with the same 6.5 billion wavefronts -- and **69.4
million cycles against 69.6**: the issue slots the quads freed were not
the limit, the data path and the ALU together are. Paired, seven rounds:
1.012 at A257467 n = 19 (7 -> 6 blocks), 0.986 at A257466 n = 21 (8 -> 7),
1.003 at A258035 n = 19 (7 blocks kept by switching to the split queue
entry).

**WINDOW_READ_MIN.** On a quad table a periodic prime reads only the
words it needs, ceil(Q / 32) + 1 -- three (an LDS.64 and an LDS.32) for
32 < Q <= 64 where the quad read four, five (an LDS.128 and an LDS.32) for
96 < Q <= 128 where the pairs read six -- and derives the rest by the
constant funnel shifts it always did. Ten wavefronts fewer per residue
and window at A257467 n = 19 (243 -> 233; 6.34 billion in the profile,
68.6 million cycles). The emitter handles three to eight words read, so
the 224-period window (eight words a prime) is covered too.

**The two together against the inherited kernel, eleven rounds of 30
launches, the stream identical on every run:**

| filter | engine v2: every quad, minimal reads (the default) | the same with the quad trim (WINDOW_QUAD_KEEP = True, below) |
|---|---|---|
| A257467 n = 19 | **1.0097** [1.0040, 1.0142] (6 blocks) | 1.0055 [1.0005, 1.0114] (7 blocks) |
| A257466 n = 21 | **1.0102** [0.9959, 1.0163] (7 blocks) | 1.0135 [1.0022, 1.0208] (8 blocks) |
| A258035 n = 19 (seven rounds) | **1.0146** [0.998, 1.028] (7 blocks, split entry) | 1.0048 [0.971, 1.019] |

Small, consistent, and what the profile said was available: the kernel's
three pipes are now 69 / 71 / 73% busy (LSU issue, ALU, data path) with
the window at the formulation's floor on each. The fingerprints are
unchanged (the stream is), G14 reads the quad and the partial reads through
`window_words` at every position of every group, and G18 confirms the
occupancy at every opening (5-8 blocks).

**Two bugs the gates caught on the way, for the record.** (1) The group
lines of the kernel source were generated once per engine while the quad
chooser re-laid the tables between compiles; a kernel compiled from stale
table offsets returned 13,350 survivors for 13,359 on the 30-launch
fingerprint window. Fixed by regenerating the lines in every compile; the
fingerprint, not a gate, caught it. (2) The layout fallback built a pairs
table for an engine on the PLAIN table (G14's last case, `lds64=False`):
G14 failed on the first window bit it checked.

### Tried and rejected (prices)

* **WINDOW_QUAD_KEEP** -- hand the groups the quads added back to the
  pairs table, smallest modulus kept, until the compiled occupancy is what
  the periodic quads alone reach (two to four compiles per engine). Eleven
  rounds against every quad: **0.996** at A257467 n = 19 (7 blocks against
  6) and **1.003** at A257466 n = 21 (8 against 7). A wash: the block it
  buys back is worth what the loads it gives up cost. Left as the A/B arm.
* **EXTRACT_ONEBIT** -- a ballot per word, and a straight-line push for the
  five-in-six words where no lane holds two survivors (the `while (a)`
  loop's BSSY/BSYNC and loop control gone): **0.954 / 0.933 / 0.962** at
  the three filters. The ballot and its branch cost more than the loop
  control they replace. Left as the A/B arm.
* **The u32 queue entry at 6 blocks against the split entry at 7** (the
  chooser's decision at A257467 n = 19, QWORD_BY_OCCUPANCY off): 0.994.
  One shared store fewer per survivor is worth the block, no more.
* **The depth constants, re-swept on the new kernel** (rule 3.4). At
  A257466 n = 21 (the first sweep ever at that filter): BIT_SURV 0.0025
  0.980 (lit 34, 72 registers), 0.005 0.958 (6 blocks); K2_SURV4 3e-5
  0.994, 3e-4 0.966. At A257467 n = 19: BIT_SURV 0.0025 0.995, 0.005
  0.993; K2_SURV4 3e-4 0.983. **Kept.**
* **The shape, at A257466 n = 21** (never swept there): xe = 1 0.972,
  spb = 8 0.939; pb = 192 1.007 and **pb = 224 1.048 on the rate** -- the
  planner's own table already says so (CREL_WIDTH), and it takes 160
  because the 224-period segment is three quarters of a median against
  half, 2% apart on the clock to a confirmed find (round 1). Kept.

### Priced and declined, without implementing

* **The next wheel prime, 59, at A257466 n = 21** -- 1.4x fewer candidates
  per prime added (59 keeps 42 of 59 classes there; 61 and 67 the same
  again), the biggest lever in OPTIMIZATION.md's catalogue. The record is
  not what stops it here (a two-limb offset in the rounds would cost ~2.5x
  on 23% of the kernel): **the segment is.** W' = 59#/6 = 1.9e20 makes a
  32-period window 6e22 of line, six medians of a(21), against the
  53-wheel's 0.53 at 160 periods; the exact-run terms sit too close to
  the wheel's period for a longer one, at every filter a campaign reaches
  this year. The same arithmetic rules out 53 at A257467 n = 19 (four
  medians, round 1).
* **Pre-shifted tables** (the pattern at all 32 alignments, no funnel
  shifts): five LDS.32 a prime for an LSU at 85%, and 50 KB of tables.
  Dead on the LSU before the shared memory is counted.
* **The funnel shifts on the FMA pipe** (IMAD.WIDE by 2^(31 - s) on a
  one-bit-offset table, the high and low halves OR-ed): the multiplier is
  one ALU instruction a prime, which is what it saves on two words; a
  wash on paper, on the pipe the profile says is co-binding.
* **CRT pairs for the eight periodic primes** (four windows instead of
  eight): +2.4 KB of pairs tables, a block per SM at every filter, against
  11% of the window's work. About 1.02 at best, priced from Measurement 3.
* **A denser bit** (two candidates a bit, a wider logical word): no such
  operation on this GPU; the per-candidate cost of the window is one
  thirty-second of a shift and a fifth of a load, both at their floors.

### Where it stands (Part 3 of OPTIMIZATION.md)

| phase | share | verdict |
|---|---|---|
| the window body | 65% | at the formulation's floor on the ALU (one funnel shift and half an OR a word) and the data path (six words of pattern per five); LSU issue taken from 85% to 69% by the quad layout, and the three pipes now within 4% of each other at ~70%; the rest is latency at 24-28 warps per SM, which the padding ablation prices at ~3% a block |
| the extraction loops | 10% (16% of stalls) | nine instructions a survivor and four a word; the straight-line variant measured 0.93-0.96 |
| the in-block rounds and the push | 23% | eight instructions and one gather a prime-test, balanced across the three pipes; K2_SURV4 and R2_DROP re-swept flat on the new kernel |
| the prologue and its barrier | 1.4% (10% of stalls) | one barrier per block-pass; smaller blocks would halve the queues and the warps with them |
| the tail rounds | 4-5% of the device | generated for the first nine; CAND_PER_LAUNCH4 re-swept flat in round 1 |
| host | 0.2-0.5 core-s a second | the pool is sized from a measurement at the filter |

### A note on the engine file

During this round a scratch script truncated `runs_gpu.py` to zero bytes
(a Python `open(path, "w")` with an invalid `newline` argument truncates
before it raises; the project was not yet under version control). The file
was reconstructed from the bytecode cache of its last good import (every
function's code, constants, docstrings and line numbers) and the sibling
engine it was copied from (the text), by compiling the candidate and
comparing it with the cache code object by code object until all 136
matched, line numbers included; the comments in the gate region that still
described the sibling's sequences were then reworded. The fingerprints,
G14, G18 and G20 passed on the reconstruction before this round's fix to
the quad chooser was re-applied, and `score.py` after it.

---

## The campaigns (2026-10-05 to 2026-10-08) — what the run measured

No engine or planner change; this is the record of the defaults under a
real campaign, one per family, no flags, read from the ledger timestamps
and the checkpoints (the method: line from the filter's first boundary to
the end of the find's segment, over the wall clock between the two ledger
times; for a campaign that was not running for part of a leg, the
checkpoint's own clock).

| filter | priced (BENCHMARKS.md) | campaign | ratio |
|---|---|---|---|
| A257466 n = 18 | 1.07e16 p/s | 1.04e16 | 0.97 |
| A257466 n = 19 | 1.44e16 p/s | 1.42e16 | 0.99 |
| A257466 n = 20 | 1.89e16 p/s | 2.03e16 | 1.08 (one segment) |
| A257467 n = 17 | 3.29e15 p/s | 3.23e15 | 0.98 |
| A257467 n = 18 | 4.54e15 p/s | 4.72e15 | 1.04 |
| A257467 n = 19 | 6.03e15 p/s | ~6.2e15 on the campaign's clock | 1.03 |
| A258035 n = 17 | 7.53e15 p/s | 7.68e15 | 1.02 |
| A258035 n = 18 | 8.24e15 p/s | 8.41e15 | 1.02 (134 segments, 14.2 h) |

**Kept:** every default. The wall clock of the loop matched the device
price at every filter swept whole, so the two things round 1 left
unmeasured because an agent does not start a campaign — the segment loop's
own per-launch cost (OPTIMIZATION.md 2.14) and the no-flags acceptance test
of rule 5g — are measured now, and both read clean: no `predictions()` in
the loop, no pool binding, the heartbeat's rate the pipeline's.

**The model ran early, not late.** E over the eighteen finds sums to 12.68
(mean 0.70, P = 0.093), against a repository record of 1.5–2× late; the
pricing table's "budget 1.5–2×" was the wrong direction here, and the
terms the model put inside a week (A257467's a(19), A258035's a(18)) came
in 18 and 14 hours. A257466's a(20), priced at 5.6 h to its median, landed
in the first segment of its filter after 81 minutes.

**Gaps the run exposed, none fixed at the pause:**

* *The launcher's version string did not follow the engine.* `ENGINE_VERSION`
  in the launcher reads `v1` while the kernel is round 2's quad window (v2
  in BENCHMARKS.md's ledger), so the checkpoint keys and every evidence
  file's `engine` field say `v1`. Harmless for the cursors — v2 returns the
  identical stream, so a key change was not needed to protect them — but a
  reader matching evidence to the ledger will find the names disagree.
  Decide the rule (a stream-identical change keeps the key, stated in the
  launcher) or bump it, before a resume.
* *A258035's n = 19 wheel was never swept for the planner's choice.* Round
  1 confirmed the plan's wheel by measurement at A257466's n = 21 only;
  A258035's n = 19 plan (to 41, then 47 and 53 on a 145-period window) has
  the engine constants swept (round 2) and the wheel priced on CREL only.
  It is the filter a resume of that family would spend its week in.
* *The campaign shapes are frozen at the published openings.* With the
  finds in hand the three campaign shapes (n = 16, 15 and 11) are no longer
  any campaign's opening; a shape at each live filter is owed (rule 5g),
  and the finds into the oracle's `FOUND` moves the drill filters with it.

