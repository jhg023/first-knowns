# OPTIMIZATION_LOG — primorial-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt → measurement → kept/rejected, failures included. This
project starts from plus-two-cliques' engine v3 and planner p2, whose own
log (and product-cliques', clique-ladders', factorial-ladders' and
lcm-ladders' before it) holds the rounds that produced the window sieve.
What is here is what was measured and decided in making that engine hunt
the primorial shift ladders. Harnesses were scratch scripts, not committed;
each measurement below gives enough of its method to rewrite one in ten
minutes.

---

## Decision 1 (2026-10-02) — the window sieve, with the constants changed

**Why that engine, and not shift-ladders'.** The problem's shape is
shift-ladders' — one unknown, n conditions that differ by an additive
constant — but its *regime* is lcm-ladders'. On the primorial families a
prime q ≤ prime(n) kills at most 1 + min(n, π(q) − 1) residues (every
primorial from prime(k) ≥ q is 0 mod q, so every later form kills the same
residue 0 that p itself kills), where shift-ladders' base-4 wheel kills
min(n, ord_q(4)) — close to q − 1 at most small primes. So the wheel here
is weak (the primes to 59 keep 2.4×10⁻⁴ of the line at every index, where
shift-ladders' base-4 wheel to 103 kept 1.4×10⁻⁵), the candidate count per
unit of line is what has to be paid, and what matters is candidates per
second. The window sieve tests a prime against 64–160 periods of one
residue in one load and a few funnel shifts, and plus-two-cliques measured
it at 2.3×10¹² candidates/s against shift-ladders' ~10¹² packed
per-candidate tests/s — on forms with the same count of killed residues
per prime (one per form) and the same forced class (one class mod 6). It
was taken whole.

**What changed, and where.** The killed residue of a form x + c modulo q
is −c mod q, which is `killed_residues` in the CPU engine and the oracle's
walk and nothing in the kernel. The kernel never sees a form, only the
residues each prime kills. Three consequences reached further:

* **The class.** Modulo 3, p and p ∓ 2 leave one class: 1 (mod 6) on
  A115785, 5 (mod 6) on A115786; on A145743 the forms 4k² kill 2 (mod 3)
  from k = 1 and 0 (mod 3) from k = 3, so its class is 1 (mod 6) from
  n = 3. The engine sweeps t with x = r + 6t; G3, G9, G13, G15 and G17 pin
  the classes end to end.
* **The line.** A115785's a(n) is at least prime(n)# + 2 (p − prime(n)# is
  a prime) and every published term lies within 2% above it from a(13) on,
  so each index is its own line starting at the primorial, past 2⁶⁴ from
  n = 16 (53# = 3.3×10¹⁹). The engine already carried candidates as
  (base, offset) with the base a Python int; the launcher's floor, zone and
  promotion are where the per-index line is handled (Decision 2).
* **The domain.** A145743's m must be composite, which no sieve expresses:
  the classification gives a prime m a run of 0, deciding compositeness
  with the deterministic test only where the run reaches the census floor
  (a composite that passes the base-2 screen is rare but exists).

The prefix machinery of the clique projects (the oracle's `register`, the
stand-in terms of the model, hiding terms from the oracle in drills) is
gone: every form is known at every index, so the campaign can be planned,
priced and benchmarked at every filter it will promote through, in
advance.

## Decision 2 (2026-10-02) — two kinds of promotion, and the exception zone

**A115785 restarts; the others carry.** After a find of a(n) on A115785
the next line starts at prime(n+1)# + 2, prime(n+1) times further out:
the rest of the old segment is on a retired line and is dropped
uncounted. On A115786 and A145743 the conditions nest, and the
classification reads every survivor's run to the filter plus `RUN_AHEAD`
(6), so everything the old filter swept past the find was classified
against the new filter's conditions already: the new filter resumes at
the old segment's end, re-denominated by floor into its own period with
the clip at the old boundary. Drilled on scratch files in every family
with the real published term as the find (`_promotion_drill`), and
end-to-end by the real loop finding two published terms in a row
(`_rediscovery_run_drill`).

**The exception zone.** A kill by q proves nothing unless the value
exceeds q, so the device starts at prime(n)# + q2 on A115785 (q2 elsewhere,
far under any frontier). The zone between the definition's floor and the
engine's is classified one integer at a time on the host at every filter
start, through the same taxonomy as a device survivor; the checkpoint
records which filter's zone is done. It is not vacuous: A115785's
a(5) = 3463 lies inside its zone at depth 4096 (`_zone_drill`).

## Measurement 1 (2026-10-02) — the ceiling: huntlib's 10⁴⁰, measured

Rule 5h's default rests on a structure this project does not have. A value
p ∓ prime(k)# has no multiplier × term ± 1 structure, so N ∓ 1 is a number
like any other and each value is proved on its own by `huntlib.certificate
.prove`'s bounded search (trial division, rho, 24 ECM curves; BLS75
Theorem 1, 5 or 15; a subproof for a large prime cofactor), then one retry
at 200 curves. The rule asks for the honest ceiling to be measured.

**Method.** Random primes at each height (the next prime above
height + a random offset under height/7), through `prove`, then the retry
where that returned nothing, each proof re-verified.

| height | first search | with the retry | worst first | mean |
|---|---|---|---|---|
| 10²⁵ | 12 / 12 | 12 / 12 | 0.2 s | 0.02 s |
| 10³⁰ | 12 / 12 | 12 / 12 | 0.4 s | 0.05 s |
| 10³⁵ | 12 / 12 | 12 / 12 | 0.2 s | 0.08 s |
| 10⁴⁰ | 10 / 10 | 10 / 10 | 0.4 s | 0.24 s |

A 40-digit value needs its N − 1 or N + 1 factored past N^(1/3) ≈ 10^13.3
for Theorem 5, which trial division to 2¹⁷ and a bounded rho hand over
nearly always. So the ceiling is **huntlib's K_CEIL = 10⁴⁰ on every
family**, where plus-two-cliques had to stop at 10³⁰ because its values
were the *square* of the term (59 digits at 10³⁰). The selftest's
certificate drill proves four values of a find's own shape per family at
the height (A115785's on its line above 101#, 39 digits; the others' at
10⁴⁰) with the recursion exercised and the subproof shown unstrippable.
A115785's line leaves the ceiling between n = 26 (101# = 2.3×10³⁸) and
n = 27 (103# = 2.4×10⁴⁰), which is where that campaign ends.

The proof crossing — where classification stops being a proof — is
3.317×10²⁴ less the largest constant, which is 3.317×10²⁴ to five figures
on every family (the shift is additive). On A115785 the campaign crosses
it between n = 19 (67# = 7.9×10²⁴, already past) and n = 18 (61# =
1.2×10²³): from a(19) on, every discovery's values are proved by
certificate. It is a `[MILESTONE]`, never a stop.

---

## Round 1 (2026-10-02) — measured where the campaign will spend its days

Method, as plus-two-cliques' rounds: scratch harnesses through the engine
API, the planned engine at the filter, the same launches for every arm,
three or four interleaved rounds with the survivor count and xor compared
on every run, the median of the per-round ratios against the base arm
reported with its range. Absolute rates are one session's on a desktop
GPU; one round in four read 1.12–1.34 on every arm at once (ambient load),
which the pairing removes. The filter is **A115785 n = 19**, the first one
that campaign will spend days in (its a(19) is hunted above 67# =
7.86×10²⁴ with a modelled median 1.35×10²¹ further out), with the three
openings re-checked where a decision changed.

### Measurement 2 — the device split, before anything changed

CUDA events around every kernel, 40 launches of the planned engine at each
family's live filter:

| filter | wheel, depth | device, line/s | candidates/s | sieve kernel | tail rounds (27–29 of them) | wall over device |
|---|---|---|---|---|---|---|
| A115785 n = 16 | {5..23},{29,31},{47}, 2¹⁷ | 4.24e15 p/s | 5.13e12 | 93.4% | 6.5% | 1.03 |
| A115785 n = 19 | {5..23},{29,31,37},{41,43,47}, 2¹⁵ | 1.16e16 p/s | 5.23e12 | 95.6% | 4.3% | 1.03 |
| A115786 n = 17 | {5..23},{29,31},{47}, 2¹⁶ | 4.72e15 p/s | 5.72e12 | 94.1% | 5.8% | 1.04 |
| A145743 n = 14 | {5..23},{29}, 2¹⁷ | 1.21e16 m/s | 5.46e12 | 90.5% | 9.4% | 1.05 |

The sieve kernel is the device, and the host is 3–5% of the wall. The
candidate rate is 5.1–5.7×10¹² a second — above the 2.3×10¹² the inherited
engine measured on its own problem, where every form was a product with a
term of the sequence and the rounds' survivors ran deeper.

### Measurement 3 — the sieve kernel, by Nsight Compute (A115785 n = 19)

One launch, `--set full`, then the per-instruction stall samples split at
the kernel's barriers (`--page source --print-source sass --csv`):

* **Throughput.** Compute (SM) 77.5%, L1/TEX 77.5%, L2 3.7%, DRAM 0.9%.
  ALU pipe 75.6% (the busiest by elapsed cycles), LSU 77.5% (by
  instructions). Issue slots 66% busy, IPC 2.64; no eligible warp on 34% of
  cycles, 7.0 active and 2.2 eligible warps per scheduler, 10.5 warp-cycles
  per issued instruction.
* **Occupancy.** 64 registers, 12,984 bytes of static shared memory: seven
  blocks per SM by shared memory where the registers allow eight (the
  queues are 8.2 KB of the 13: ping-pong buffers of 1344 and 704 u32
  entries at sigma 6, the window tables 3.7 KB, the offset rows 1 KB).
* **Where the samples are.** The window sieve and the extraction, 75.3%
  of the stall samples and 76.6% of the executed instructions; the five
  in-block rounds 16.8% / 22.2%; the prologue 6.8% / 1.0%; the push to the
  tail 1.0%.
* **The window loop, per prime and 160-period window** (SASS, 30 window
  groups, NW = 5): one `IADD3` per pair of primes (x0 + ne + bw, packed),
  one `LOP3`/`SHF` to split the half and one `IMAD.HI` for the word index
  per prime, three `LDS.64` (two, or one `LDS.128`, for the nine periodic
  primes), five `SHF.R.W` funnel shifts and 2.5 `LOP3` — the compiler fuses
  two words' ORs into one three-input `LOP3`. About 12.5 instructions a
  prime; 590 per warp-window measured, of which ~375 are the primes, ~35
  the per-window validity masks recomputed inside the loop, the rest the
  extraction (8.8 survivors a thread) and loop overhead.
* **Opcode mix of the window region:** SHF 29%, LOP3 19%, LDS 13%, IMAD
  10%, IADD3 7%, ISETP 5%, BRA 4%, SEL 4%.
* **Nsight's own suggestions**, for the record: global loads using 18.5 of
  32 bytes a sector (the in-block rounds' gathers from the tripled kill
  tables, which are L1-resident at an 89% hit rate), 1.2-way bank conflicts
  on 11% of shared stores (the queue pushes), an L2 slice imbalance. None
  is the window.

So the kernel at this filter is bound by instruction issue on the ALU and
LSU pipes together, with a third of its cycles latency-stalled at seven
warps per scheduler, and three quarters of its instructions are the window
sieve at ~12.5 instructions per prime-window, of which the five funnel
shifts and 2.5 ORs are the floor of this formulation (one `SHF.R.W` per
32-bit word is one instruction, and the ORs are already fused).

### Sweep 1 — the inherited constants, re-swept at A115785 n = 19

Paired, interleaved, 30 launches an arm, three rounds; the stream
identical across arms (same pb):

| arm | compiled | ratio | verdict |
|---|---|---|---|
| xe = 2 (the extraction batch) | 74 regs, 6 blocks | **1.037–1.038** (three sweeps) | kept: the inherited rule took xe = 1 for the seventh block |
| spb = 8 | 64 regs, 8 blocks | 0.992 | declined |
| spb = 8, xe = 2 | 72 regs, 7 blocks | 1.012 | below xe = 2 alone |
| pb = 224 (clamped to 179) | 6 blocks | 0.911 per unit of line | declined; the planner's 160 stands |
| pb = 128 | 8 blocks | 0.981 | declined |
| QWORD off (u16 + u8 queue entries) | 64 regs, 8 blocks | 1.007 | within noise here; see sweep 2 |
| BIT_SURV 0.002 (window 36 primes) | with xe = 2 | 1.011, i.e. ~0.974 net of xe | declined |
| BIT_SURV 0.0055 (26 primes) | with xe = 2 | 0.974 | declined |
| K2_SURV4 3e-5 / 3e-4 | | 0.994 / 0.970 | declined |
| CAND_PER_LAUNCH4 2³⁶ / 2³⁸ | | 0.993 / 1.006 | declined (noise) |
| TAIL_ROUND_DROP 0.5 / 0.85 | | 1.007 / 0.974 | declined (noise / loss) |
| q2 = 2¹⁶ against the planned 2¹⁵ | | 0.998 | a tie on the device; the planner's depth stands |

Every inherited constant but the extraction batch is still at its optimum
on this problem. The batch is the one place the inherited rule got the
trade wrong: xe = 1 was taken because it *gains a block* (seven against
six), and here the block is worth less than the batch.

### Sweep 2 — the extraction batch and the queue entry at every live filter

The same A/B at the other openings and a promotion filter (xe = 2, and
xe = 2 with the three-byte queue entry), four rounds:

| filter | xe = 2 | xe = 2 + split entry | compiled |
|---|---|---|---|
| A115785 n = 16 | 1.006 | **1.033** | 74 → 72 regs, 6 → 7 blocks |
| A115786 n = 17 | 1.008 (the default was xe = 2 already) | 1.011 | 8 blocks either way |
| A115786 n = 19 | 0.995 (default xe = 2) | **1.013** | 7 → 8 blocks |
| A145743 n = 14 | 1.088 [0.996, 1.132] (default xe = 2; a one-launch segment, noisy) | 1.091 | 8 blocks |

Two rule changes, both decided on the COMPILED occupancy (`primorial_gpu`
XE1_REGS and QWORD_BY_OCCUPANCY):

1. **xe = 1 is taken only where it gains a block AND xe = 2 is
   register-heavy** (≥ 96 registers, product-cliques' case), not where it
   gains a block alone.
2. **The queue entry is a u32 unless the u16 + u8 split reaches a block
   more.** At 64 registers the registers allow eight blocks and the queues'
   8 KB of shared memory seven; the split buys the eighth where it is the
   shared memory that binds, and costs the 1.5% plus-two-cliques measured
   for the word where it is not.

The new default against the inherited one, paired, four rounds, at every
live filter:

| filter | inherited default | new default | ratio |
|---|---|---|---|
| A115785 n = 19 | xe = 1, u32 entry, 64 regs, 7 blocks | xe = 2, split entry, 72 regs, 7 blocks | **1.057** [1.051, 1.071] |
| A115785 n = 16 | xe = 1, u32, 7 blocks | xe = 2, split, 7 blocks | 1.015 [1.00, 1.035] |
| A115786 n = 17 | xe = 1 (forced), 8 blocks | xe = 2, u32, 8 blocks | 1.011 |
| A145743 n = 14 | xe = 1 (forced), 8 blocks | xe = 2, u32, 8 blocks | 1.004 (noise: one launch a segment) |

### Tried and rejected — the validity masks hoisted (MASK_HOIST)

The five masks that clip the window's last words to the live periods
depend on nv and `live` alone, and the compiler recomputes them inside
every window (about 35 of the window's 590 instructions). Computed once
per thread before the residue loop: **0.978** at xe = 2 (four rounds,
stream identical), while gaining a block (74 → 72 registers). The five
live registers cost the compiler's schedule of the loop more than the
instructions saved. Left in as the A/B arm (`MASK_HOIST = False`).

### Priced and declined, without implementing

* **Quad tables for every window prime** (two loads a prime instead of
  three). The pairs table doubles the plain one and quads would quadruple
  it: ~11 KB of shared memory against 3.7, which costs two blocks per SM
  before it saves a load, and the kernel is ALU-bound as much as
  LSU-bound. Taken for the nine periodic primes only, as inherited.
* **Pairs of window primes in one CRT group.** A pair's table is 1–9 KB and
  halves the shifts per prime; thirty primes' worth does not fit the
  shared memory that already caps occupancy. product-cliques measured the
  single-prime groups better for the same reason.
* **A tabulated per-residue window** (the five words per prime at every
  residue position, no shifts): 2 KB a prime, 60 KB a filter, in L1 or L2
  as gathers — trades five `SHF` for five loads in a kernel whose LSU is as
  busy as its ALU. plus-two-cliques measured the per-word-select variant at
  0.985.
* **Forcing eight blocks with launch bounds** at xe = 2 (72 → 64
  registers): plus-two-cliques measured a forced occupancy spilling and
  running 0.93.

### Where it stands (Part 3 of OPTIMIZATION.md)

| phase | share | verdict |
|---|---|---|
| the window sieve and extraction | 75% | instruction-bound at ~12.5 instructions a prime-window, of which 7.5 (five funnel shifts, 2.5 fused ORs) are the floor of this formulation; the loads are at their ideal count (Nsight, this round and plus-two-cliques' round 2); the one restructure with headroom (fewer loads per prime) costs the occupancy it would gain |
| the in-block rounds | 17% | inherited lazy packs; K2_SURV4 and R2_DROP re-swept flat |
| prologue, push, tail rounds | 8% | one launch's fixed costs; CAND_PER_LAUNCH4 re-swept flat |
| host | 3–5% of wall | the pool is sized from a measurement at the filter |

Engine v1 is therefore plus-two-cliques' v3 with its extraction batch
and queue entry decided on this problem's compiled occupancy. One more
round of the catalogue found nothing above the noise; the next lever is
not a constant.

---

## The campaigns (2026-10-02 to 2026-10-05) — what the run measured

No engine or planner change; this is the record of the defaults under a
real campaign, read from the ledger timestamps and the checkpoints (the
method: line from the previous find's segment end to the end of the find's
segment, over the wall clock between the two ledger times).

| filter | priced (BENCHMARKS.md) | campaign | ratio |
|---|---|---|---|
| A115785 n = 18 | 9.27e15 p/s | 9.2e15 | 0.99 |
| A115785 n = 19 | 1.28e16 p/s | 1.29e16 | 1.01 |
| A115786 n = 19 | 1.00e16 p/s | 9.8e15 | 0.98 |
| A115786 n = 20 | 1.35e16 p/s | 1.32e16 | 0.98 |
| A145743 n = 19 | 2.81e17 m/s | 3.5e17 | 1.25 (one segment) |
| A145743 n = 20 | — | 6.3e17 m/s over 39.2 h | not priced |

**Kept:** every default. The wall clock of the loop matched the device
price at every filter swept whole, so no per-launch cost outside the
kernel is hiding in the segment loop (OPTIMIZATION.md 2.14).

**Gaps the run exposed, none fixed at the pause:**

* *A filter the campaign reached was never priced.* The table stopped at
  A145743's n = 19 because the model put a(19) at 22 minutes; a(20) then
  took 39 h at a filter with no benchmark row and no swept constants.
  Price one filter past where the model says the night ends: the model
  runs late (mean E 1.62 over these fourteen finds).
* *The stopped filters read fast on a launch count.* A115785's n = 20 and
  A115786's n = 21 read 1.36e16 and 1.4e16 p/s from launches swept over
  wall clock, against 1.11e16 priced. A fraction of a segment counted in
  launches is not a line measurement; measure it paired, through the
  engine API, before quoting either number.
* *A rung label that may have outlived its ladder.* A145743's checkpoint
  lists `a(21) Q1` as passed at a coverage cursor of 8.90e22, below the
  1.84e23 the model gives from there. Not traced; the suspect is a label
  logged against the ladder of the previous frontier and never cleared at
  the promotion.
