# OPTIMIZATION_LOG — power-ladders

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

Every attempt, with its measurement and its verdict, the rejected ones
included (OPTIMIZATION.md Rule 6). Rates are line per second of the term —
m/s on A229626, A229630 and A229902, q/s on A229627 — measured paired and
interleaved (Rule 3) by scratch harnesses that build the engines in one
process and sweep the same line from each family's frontier term; ratios
are medians over three or four rounds with [min, max]. Absolute rates on
this desktop move up to ~25% between processes (two score runs an hour
apart read 248 M and 221 M with every shape, the Fermat-free anchors
included, ~10% apart), so only ratios are quoted as results.

The harnesses (session scratchpad, not committed — CLAUDE.md rule 9), so
the next person can rewrite them in ten minutes:

* **ab.py** — `ab.py repo fam n launches rounds "name:KEY=VAL,eng.kw=VAL"
  ...`: builds one engine per configuration (module constants set for the
  build and restored after; `eng.` keys are `GpuEngine` keywords), then
  alternates them round by round over `launches` launches from the first
  period above the frontier term, reporting line/s medians and ratios.
  Engines built in one process share the GPU (7-11 GB for four).
* **prof.py** — per-kernel device time by CUDA events wrapped around every
  kernel the launch enqueues (sieve, tail rounds, generated tail rounds,
  each Fermat stage), plus the wall clock, so the phases are checked to sum
  to it (Rule 1).
* **rates.py** — the campaign engine (planned, Fermat stage on, segment =
  window) at named filters, from the model's floor for each.
* **Nsight Compute** — `ncu.bat --kernel-name sieve --launch-skip 2
  --launch-count 1 --set full -f --export rep python ncu_target.py repo
  A229626 10 4`, then `--import rep.ncu-rep --page details`, `--page raw
  --csv` (metrics by name) and `--page source --print-source sass --csv`
  (per-instruction samples and executions), split at every `BAR.SYNC` and
  counted by full opcode name (`sass_split.py`, `sass_ops.py`). The
  procedure is OPTIMIZATION.md Rule 1a.

## Engine v1 = polynomial-runs' engine v2, taken whole (2026-10-15)

The window sieve, the lazy narrow rounds, the folded wide rounds, the
generated tail rounds and the two survivor records, with the kill sets
replaced (the k-th roots of the multiplier's inverse, by a discrete
logarithm — power_search) and the tail's residue list resized to them: a
prime kills up to gcd(k, l − 1) residues per power form, 41 of 601 at
n = 12 of A229626 and n(n+1)/2 by the proved bound, so the list is sized per
engine from the primes it holds (`nres`, a multiple of 16 up to
NRES_MAX = 128; G10 pins the bound to the last expressible index, 15).
Primes that kill nothing — 2 on the three ladders of twice a power less one, 19 on A229902
— are left out of the sieve.

## Round 0 — the regime, measured before anything was tuned

**The first read was 6.4×10⁹ candidates a second** at A229626's opening
(n = 10), against the 10¹¹–10¹² the inherited engine runs at, with 98.8%
of the device in the sieve kernel and 18.8 s per launch. Two causes, found
in that order:

1. **A starved shared queue.** The inherited window stops at LIT_MAX = 40
   primes, where a strong kill set has left 0.35% of a tile; here each prime
   kills about one residue per form (n/l of the line), so 40 primes leave
   **2.7%** — 3,500 survivors of a 131,072-candidate tile against a queue
   of 1,920 — and every block took the in-block overflow fallback, which
   tests the whole tail per candidate. Window depth, paired at A229626
   n = 10 after the guard below: **100 primes 1.000**, 80 0.965, 60 0.784,
   40 0.610, 120 0.886 (register cliff: 255 registers, 2 blocks). The
   sieve kernel went from 9.4 s to 0.35 s a launch (17x). **LIT_MAX 40 →
   100.** And **STARVE_GUARD**: a block shape whose queues hold fewer
   entries than the tile's MEAN survivors halves its second-level residues
   per block until they fit (overflow had been "harmless" because it was
   rare; here it was the rule). With the guard, a 60-prime window reads
   0.78 instead of 0.04.
2. **The host.** 4×10⁻⁵ of the candidates survive a sieve to 2¹⁶ — about
   10⁷ values a second at that rate, at ~20 µs each in Python. No sieve
   depth fixes that: survival falls as (ln 89 / ln Q)^n, so 2²⁰ only
   reaches 1.3×10⁻⁵ and 2³² ~10⁻⁷. **The DEVICE FERMAT STAGE** (power_gpu
   `_PRP`, gated by G23): every survivor's leading forms — q itself on
   A229627, then the k = 1..6 values — Fermat-tested to base 2 on the
   device, one kernel per form over the previous one's compacted queue,
   multi-limb Montgomery (CIOS, 32-bit limbs, unrolled per limb count; the
   limb count compiled per form from the top of the segment). A failed
   Fermat test is a proof of compositeness, so nothing whose leading six
   forms are prime is dropped; the host re-reads every run. Host traffic
   fell to 1–4 thousand values a second (one or two cores), and the sieve
   depth became a DEVICE decision: at A229626 n = 10, with the stage on, a
   sieve to 2¹³ ran 1.26x one to 2¹⁶ (**PRP_Q2 = 8192**, replacing the
   host-load rule `plan_q2` inherited).

After round 0: **4.4×10¹¹ candidates a second** at A229626 n = 10 (69x the
first read), split sieve 49% / tail 38% / Fermat stage 13%.

## Round 1 — the global queue, and the in-block rounds (2026-10-15)

**The variance said it first**: at A229902 n = 10 the 256-period window
read 4.6×10¹⁴ m/s in one round and 1.7×10¹⁴ in the next, on the same line.
The global tail queue holds `cand × surv[k2]` entries and is capped at
Q3_MAX = 2²⁸; the weak sieve leaves 2–3×10⁻³ there, 1.95–3.8×10⁸ entries a
2³⁷-candidate launch, so A229626 and A229627 sat exactly at the cap and
A229902 40% past it — every overflowed candidate running the whole tail in
the fallback, the launch time swinging with which warps met a full queue.

* **Q3_GUARD**: a launch whose expected first-round entries pass
  Q3_FILL = 0.75 of the cap is cut — a batch of windows first, then the
  third-level residues per launch, then the first-level chunk.
* **K2_ROUND_PRIMES_MAX 128 → 64**: the in-block rounds stop 64 primes past
  the window. Each round prime past the window removes only ~n/l of what
  is left, so the in-block test is paid by many and kills few; with the
  queue guarded, the global tail does that work cheaper. Paired against the
  shipped 128 without the guard: **A229626 n = 10 1.039 [1.034, 1.043],
  A229627 n = 9 1.020, A229902 n = 10 2.33 [2.25, 2.34]**. At A229626: 96
  read 1.011, 32 0.70 and 0 (no in-block rounds) 0.145 — the queue cliff
  again, which is why the guard comes first.
* **Re-swept after the change (Rule 3.4), all flat**: the sieve depth
  (A229626 n = 10: 2¹³ 1.000, 2¹² 0.975, 2¹⁴ 0.938, 2¹¹ 0.855); the window
  depth (88 primes 0.98–0.99, 112 0.84 at A229626 and 0.998 at A229902);
  the planner's window width (A229626: its 128 = 0.998 of 128, 192 0.925,
  256 0.982; A229627: its 256 = 1.008 of 256, 192 0.979, 128 0.971 — the
  plan is within noise of the best at both); CAND_PER_LAUNCH4 2³⁶ / 2³⁸
  0.995 / 1.013 under the guard (kept 2³⁷: the smaller footprint).
* **A first A/B at A229627 read the new depth at 0.825**; repeated cleanly
  with three arms and four rounds it was **1.020**. That run's control arm
  had read 24% above its own later medians. Recorded because it is the
  failure Rule 3 describes, and the decision was made on the repeat.

## Round 2 — Nsight Compute on the sieve kernel and the tail (2026-10-15)

Profile of the sieve kernel at A229626 n = 10 (one launch, `--set full`):
**LSU pipe at 97.8% of its issue peak**, L1/TEX throughput 97.8%, issue
slots 46.7% busy, ALU 52%, occupancy 25% (3 blocks of 4 warps: both the
168 registers and the shared memory limit it), stalls led by MIO throttle.
Split at the barriers: **segment 1 — the window loop — is 72% of the
kernel's samples and every one of its 4.4×10⁹ shared loads**; the
generated in-block rounds are 20%. The census of the window loop's SASS:
501 `LDS` (32-bit) — five per window prime, the plain table read a word at a
time — 426 `LOP3`, 400 `SHF.R.W` (four funnel shifts a prime), 25
`LDS.128` (the block offsets). Neither the pairs table (29 KB) nor the quad
table fits the 16 KB the layout allows for a 100-prime window, and pairs
plus the queues would pass the 48 KB of static shared memory.

* **WINDOW_ALIGN (tried, declined, kept as a gated arm).** The plain table
  read from aligned entries — A = 2: three `LDS.64` for the five words
  NW = 4 needs, the one used SELECTED by (r ≫ 5) mod 2; A = 4: two
  `LDS.128` — same table, padded by 2A words a group (INNOVATION.md §1.1,
  "word size and limb shape"). Paired: **A = 2 0.974 / 0.997 / 0.997**
  (A229626, A229627, A229902), **A = 4 0.906 / 0.910 / 0.948**. The
  profile says why: at A = 2 the LSU fell from 97.8% to 66.6% and the
  shared loads from 4.2×10⁹ to 2.5×10⁹, but 4.3×10⁹ `SEL`s arrived and
  issue went to 55.5% — the bound moved to the ALU and issue, at 12 warps a
  SM. The window is balanced between its two pipes at this occupancy: the
  floor of THIS formulation, with the levers that remain priced below.
  G9 runs three windows on the plain table at whatever WINDOW_ALIGN says
  (all three settings green), and G14 emulates the aligned read.
* **The tail rounds** (one generic round, Nsight Compute): IPC 2.75,
  issue 69% busy, ALU 56%, occupancy 80%, its loads 98% L1 hits — a
  healthy kernel doing a lot of work: ~852 tail primes, tested generically
  (the prime, its magic, its period row and its mask loaded per test).
  **TAIL_LITERAL 16 → 32, TAIL_LITERAL_ITEMS 2¹⁹ → 2¹⁰,
  TAIL_LITERAL_PRIMES 64 → 1024**: every tail round but the last generated
  with its primes as literals (lazy Barrett packs, one bit from a doubled
  table). Paired: 128 primes a round 1.085, 256 primes / 2¹⁶ items 1.120
  (A229626 n = 10); **1024 / 2¹⁰ / 32 rounds: 1.18 at A229626, 1.166
  [1.160, 1.168] at A229627 n = 9, 1.263 [1.211, 1.329] at A229902
  n = 10**; generating everything (4096 / 1 / 64) no better (1.164,
  1.289); shorter rounds (TAIL_ROUND_DROP 0.5, 0.6) 0.853 and 0.946.
  **TAIL_LITERAL_TOTAL = 2048**: NVRTC takes ~20 s a thousand literal
  primes (A229626 n = 10 generates 752; the gates' deep sieves would have
  generated tens of thousands, and the first score run after the change
  died at the five-minute cap in G14).
* **SIEVE_MIN_BLOCKS = 3, decided on the compiled kernel.** The register
  allocation of this body moves 168 ↔ 220 between near-identical sources:
  with the 64-prime rounds, A229630 n = 9 compiled to 220 registers and 2
  blocks (G18 caught it). `__launch_bounds__(128, 3)` gives 168 and 3
  blocks with an 8-byte spill: **1.045 [1.040, 1.056]**. Applied only where
  the unbounded compile's register file holds fewer than 3 blocks, kept
  only if it spills at most SIEVE_SPILL_OK = 16 bytes, and decided FIRST,
  before the queue margin (decided after, the margin had already been
  sized for the 220-register kernel and shared memory held it at 2 blocks).
  A229626 n = 9 spills 8 bytes under a bound it does not need, and does not
  get one. G18 accepts a spill only under an applied bound.
* **The kernel module cache key now carries** the window alignment, the
  launch bound and the tail rounds' boundaries — the generated rounds bake
  their primes in, and two engines differing only in TAIL_ROUND_DROP
  could otherwise have shared a module (found while reading the key, not
  by a failure: the A/Bs above happened to differ in a keyed field).

## Round 3 — the Fermat stage (2026-10-15)

After rounds 1–2 the split at A229626 n = 10 is sieve 52% / generated tail
28% / Fermat stage 18% / generic tail 2% (A229902 n = 10: 48 / 28 / 20 /
3), the phases summing to the wall clock.

* **PRP_RMOD_FAST**: R mod N (R = 2^(32·NL)) was 32·NL modular doublings of
  1 — a quarter of the k = 2 stage. 2^b mod N for b the bit length of N is
  2^b − N (N ≥ 2^(b−1)), the complement of N in b bits plus one, and the
  32·NL − b < 32 doublings to R follow. Exact (G23: the stage against
  Python's pow on 16,007 values at 2–17 limbs). **1.018 [1.016, 1.020]**
  on the whole pipeline at A229626 n = 10.
* **Re-swept, flat**: PRP_TPB 256 1.004, PRP_GRID 8192 1.004.

## Round 4 — a written review, priced at the day-long filters (2026-10-16)

**Target** (OPTIMIZATION.md Rule 0a, written the same day): A229626 n = 12
(19 days median), A229902 n = 12 (35 days), A229627 and A229630 n = 11 (2.3
and 2.7 days). Rounds 0–3 were all measured at the openings, whose terms
take seconds to minutes. A review of the source proposed four changes; each
was priced at those filters before anything was built.

* **The Fermat stage's limbs from the exact top value — BUILT.** The stage
  compiled each form for bitlen(c) + k·bitlen(x_max) + 1 bits, which runs
  up to k + 2 bits over the largest value at the top of the segment.
  `_prp_limbs` now sizes from the bit length of c·x_max^k + d plus the one
  bit of headroom the modular doublings need (every value
  N < 2^(32·NL − 1), the invariant the old bound always kept). Priced by
  sampling 4,000 heights log-uniformly between each term's Q1 and P90:
  k = 1 and 2 **never** carry a spare limb at the day-long filters. k = 3
  to 6 do on 9–32% of heights, at 1.02–1.08 on that form's
  exponentiations when they do (A229902 n = 12 k = 3: 32%, 1.08). k ≥ 3
  sees a minority of the stage's work, and the stage was 18–20% of the
  device at n = 10, so this is about 0.2–0.6% of the pipeline. That figure
  is a price; the gain was not measured. The review's own example, k = 1
  near 2^61, is A229626 n = 11 (a 2.4-hour term), where k = 1 carried a
  spare limb on 48% of heights (1.43 on that form); the day-long filters
  never reach that range. Exact, and strictly less work: G23 now drills
  the tight case at every family on k = 1, 2, 4 at 3, 5 and 9 limbs. That
  is a batch topped by the largest x whose value fits, its top value at
  32·NL − 1 bits. The sizing must be exactly that limb count, with x + 1
  one limb more, and the device must agree with Python's pow.
* **The census counted at the drain, not held to the segment's end —
  BUILT.** Every run of 6 or more was held as a value until the segment
  closed. That included runs whose successor was already settled, which
  can only ever increment a count, since the frontier only rises at a
  segment's end. Every checkpoint of the segment copied the list.
  Measured on the live checkpoint at A229626 n = 11 (152,246 values held,
  5.8 MB): a save took **0.31 s, against 0.002 s with the list empty**
  (five repeats; the snapshot another 0.02 s, which sat outside the
  save-cost timer and is now inside it). The adaptive interval holds saves
  to 2% of the main loop, and the sweep is double-buffered: the device
  runs the one launch already enqueued, about 46 ms there, and then waits.
  So a save is device time lost, about 2% at n = 11 across most of each
  segment. A229630 n = 11 (432 values a second, segments of a few minutes)
  is the same case. At A229626 n = 12 a segment holds about 24,000 values
  (239 a second over about 100 s), and the save crosses the interval's
  40 ms floor only near the segment's end: about 0.3%. Also a price, not
  measured. Census runs are now counted as they drain, and only NEAR runs
  and finds are held; the wiring drill drives all four kinds through the
  drain.
* **Packed offsets on the plain-table path — DECLINED for now, priced
  unbuilt.** NEPACK requires the paired tables (`lds64`), though the
  16-bit proof does not depend on them. A packed/plain branch of the
  emitter would cut the long-lived offset registers and restore the
  block-offset table. Unmeasured, and a new emitter branch, not a sizing
  change. Owed first: whether the day-long filters' PLANNED engines take
  the plain path at all, then a register/occupancy census of both arms
  there.
* **A dedicated semiprime predicate for A229630 — DECLINED as a rate
  lever.** The host is not the binding side (432 values a second at n = 11
  against a pool sized from a measurement), so a cheaper classification
  buys load, not line. **A correctness note for whoever takes it:**
  `is_semiprime_fast` rejects anything `mr_is_prime` passes, and above the
  deterministic bound 3.317×10²⁴ that rejects a semiprime that is a strong
  pseudoprime to the bases (huntlib's own regression case,
  1287836182261 × 2575672364521). A229630's m stays below 10²¹ through
  a(11), and a(12) is years away at these rates, so this is unreachable in
  any campaign in view. It is owed before the family is run past 3.3×10²⁴.

## Round 5 — A229630's semiprime domain, in the wheel (2026-10-19)

**Target**: A229630 n = 11, the live filter. The campaign stopped at
m = 5.56×10¹⁹, past a(11)'s first quartile; the model put the expected line
to a confirmed find at 2.8×10²⁰ from there, 131 h at the v1 engine's device
rate. A
written review proposed the lever; everything below was built and measured
here.

**The mathematics.** A semiprime m divisible by two distinct primes p and q
IS pq, and one divisible by p² IS p². The wheel's primes are at most 89,
so above SEMI_FLOOR = 89² = 7,921 a semiprime has at most ONE prime factor
among them. Whether p divides m is a property of m's wheel class, so the
classes with two or more "zeros" across the wheel's primes hold no term
and need not be enumerated. And 2, which kills nothing on 2·m^k − 1 and so
never had a wheel slot, earns one: an even semiprime is 2p, with no other
wheel factor. G24a checks the theorem on all 43,118 semiprimes in
(7,921, 200,000], and that 83·89 below the floor fails it. Every engine
floor on A229630 is now at least SEMI_FLOOR (power_search.k_floor), and the
host covers the integers below it as the exception zone.

"At most one zero" is not a product of per-level sets. It is the union of
three disjoint ones, with zero counts (≤ 1, 0, 0), (0, 1, 0) and (0, 0, 1)
at levels (1, 2, 3). Each is a GpuEngine over restricted residue tables
(`zeros`), on the same period and segment. The KERNEL IS UNTOUCHED, so
every gate on it still speaks for the branches. `SemiprimeEngine` runs the
branches in turn inside each segment, and its launch index runs through
them in order. The cursor means what it always meant, and a segment closes
when the last branch has swept it. One engine fix came with it: a level is
present by its MODULUS, not by having more than one residue. At n = 9 the
second level is 47 alone, and the branch with a zero there keeps the
single residue 0.

Classes kept, against the v1 plan's wheel at each filter:

| filter | v1 plan's wheel | 2 joins | kept | branches' shares |
|---|---|---|---|---|
| 9 | {3..31 less 19, 29},{47},{73} | level 1 | 28.3% (3.54x) | 0.990 / 0.007 / 0.004 |
| 10 | {3..31 less 19, 29},{47,73},{89} | level 1 | 26.6% (3.77x) | 0.986 / 0.011 / 0.003 |
| 11 | {3..23},{31,41,47},{73,89} | level 1 | 24.3% (4.12x) | 0.965 / 0.028 / 0.007 |
| 12 | {3..31 less 29},{41,43,47},{73,89} | level 2 (level 1 is 3.5×10⁹) | 22.8% (4.38x) | 0.973 / 0.020 / 0.007 |

**The plan (p2, A229630 only).** The v1 plan's levels with 2 in the first
level whose bounds admit it, and HALF the window: 128 periods of the
doubled wheel. A segment is then the same 1.108×10¹⁹ of line at n = 11,
the coverage unit the owner chose to keep (CLAUDE.md 5j).

**Measured** (scratch harness `ab_n11.py`): seconds per segment, estimated
per branch from 10–16 evenly spaced positions × a 6–8-launch burst timed in
steady state, Fermat stage on, survivor fingerprint checked identical on
every round, arms interleaved. At n = 11, on the live segment's line (v1
period 1286 = period 643):

| arm | seconds a segment | rate | values/s to the host |
|---|---|---|---|
| v1 plan | 17,900–18,700 | 5.9–6.2×10¹⁴ m/s | 348–361 |
| semiprime wheel | 4,850–5,280 | 2.10–2.29×10¹⁵ m/s | 316–351 |

**3.69x, median of six paired rounds, [3.46, 3.85].** That is the density
(4.118x) times the width curve's price of a 128-period window against 256
(1/1.118 = 0.894 → 3.68), so the branches cost nothing beyond their
candidates. The host sees the same values per second: the stream falls by
the same factor per unit of line that the rate rises. At n = 12 the ratio
was 3.94 [3.91, 3.97] over two rounds, and at n = 10 (a check, rule 3b)
3.84 [3.80, 3.87].

**Exactness at the production configuration** (`exact_n11.py`). On the live
segment's line, for three third-level classes (two zero-free, one with a
zero), the v1 engine's stream with the Fermat stage on, filtered by
`semi_wheel_ok`, equals the branches' stream: 470, 482 and 98 survivors,
1,050 in all, no duplicates. Each one sampled passes the CPU sieve and
the CPU Fermat chain. S229630 covers a whole n = 9 segment, and its stream
is the v1 plan's over the same segment filtered: 2,899 of 10,276. G24 pins
the stream to the CPU engine filtered on seven populated windows. They
cover three levels with 2 in the first and in the second, two levels, one,
the wide record, past 2⁶⁴, at the ceiling, and from 7,922, plus the Fermat
stage on top. G24 also pins the launch cursor split at every branch
boundary.

**The cursor (launch.py, ADOPTS).** The new plan runs at once from the
start of the stored segment, floored into its own period with the clip at
the claim. The live checkpoint's segment was open at launch 102,694 of
196,020, so that segment is re-swept on the new engine and its census
counts the part already swept twice; the log says so. That is the owner's
call (2026-10-19). As first built, an open segment was finished on its old
engine, rebuilt exactly, to keep the census exact. That held the 3.7x back
for the segment's open half, about 2.5 h at the old rate, against about
1.5 h for the whole segment on the new one. The first restart ran on the old
engine with nothing in `[STATUS]` to say so. `_adoption_drill` runs a closed
and an open segment at A229630's opening.

**Device memory**: 6.6 GB at n = 11 against 2.5 GB, because each branch
holds its own queues and tables. Not binding on this card. Sharing the
queues between branches (they never run at once) is priced, unbuilt.

**G18 found a kernel at 2 blocks.** n = 9's first branch, at 128 periods,
compiled xe = 2 to 228 registers. The xe = 1 fallback never re-tried the
launch bound that xe = 2 had declined for its spill; xe = 1 under the bound
is 168 registers, 3 blocks, 8 bytes spilled. The fallback now re-tries it.
A kernel already at the floor cannot gain a block that way, so G18 shows
every other configuration unchanged. Branches holding under 10% of a
segment's candidates (SEMI_OCC_SHARE) are reported rather than held to the
floor.

**Declined, priced:**

* **A 224-period window on the doubled wheel**, narrow, clamped to 212
  live periods, making the unit 1.66x: **0.97 [0.93, 1.00]**, measured
  paired. No gain, and a longer unit. A 256-period window would need the
  wide record: the width curve × CREL_WIDE prices it at 1.02 for a unit 2x
  longer. Declined unmeasured (5j).
* **Excluding multiples of 4** (4 | m only for m = 4): 4.59x against 4.12x
  in density, but 4 in the first modulus doubles the period again. Keeping
  the span needs a 64-period window, which the width curve prices at 0.84
  of 128, about 0.94 overall. At 128 periods the unit doubles: about 11%
  more rate on a ~40 h search (about 4 h saved) against 0.7 h more expected
  over-sweep, a 17% ratio. That is the owner's threshold to call (5j).
  Unbuilt: the wheel takes primes, not a prime power.
* **Residue 0 of every sieve prime in the classes with a wheel zero.** There
  m = ℓp with p a prime past the sieve, so no sieve prime may divide m
  either (above 89 × 8,192). That is 79% of the first branch's first-level
  classes (mostly the even ones) and all of the other two. The window
  primes would kill about 30% more there, the Fermat stage is ~20% of the
  device, so about 1.05. It needs those classes split out as branches of
  their own, with window tables of their own. Unbuilt.

**Expected clock to a confirmed a(11)** from the cursor, over the model's
2.8×10²⁰ of line, at the device rates measured here: about 35 h at
2.25×10¹⁵ m/s, against 131 h at 6.0×10¹⁴ m/s on the v1 plan. The v1
campaign itself averaged 5.2×10¹⁴ m/s of wall clock, so read 35 h as the
floor. Re-sweeping the open segment's swept half adds about 0.7 h, for
about 36 h.

## Round 6 — the cofactor sieve on A229630 (2026-10-20)

**Target**: A229630 n = 11, the live filter, from the cursor at m =
5.563×10¹⁹ (the semiprime wheel had run its first half hour there). A
written review of the round-5 source proposed four changes; each was
checked here, and the one built was measured here.

**The phase split first** (Rule 1; `prof_n11.py`, CUDA events around every
kernel of every branch, 6 positions × 6 launches, weighted by each branch's
launches per segment). On the p2 engine, on the live segment: the sieve
kernel 57.8% (the window and the in-block rounds), the generated tail
rounds 17.3%, the Fermat stage 16.5%, the generic last tail round 8.4%.
The device time is 0.998 of the wall clock. So 42% of the device is
downstream of the sieve kernel, and the in-block rounds sit inside it.
Round 5 priced the lever below at about 1.05 because it counted the Fermat
stage alone.

**The mathematics.** In a class with a wheel zero, m = p·r′ for ONE wheel
prime p (round 5's theorem), and r′ of a semiprime is a prime. Once m
passes p times the sieve depth, r′ is past every sieve prime, so no sieve
prime may divide m. The engine's kill set for each sieve prime is
therefore killed_residues plus residue 0 in those classes. It is a table
change, not code: every table the engine holds is built from one function,
`engine_kills`, at construction. The bound that makes it a theorem is
SEMI_TOP × q2 = 89 × 8,192 = 729,088 at the campaign's depth, now in
`power_search.k_floor` beside SEMI_FLOOR. G24a checks it on every
semiprime from there to 2×10⁵ at q2 = 512 (34,146 of them), for the whole
of 2..89 as the wheel and for the n = 11 plan's subset. It also checks
that the floor is needed: 89 × 509 sits under it with both factors.

**Densities, exact, from the engine's own prime order** (`dens_n11.py`):
the classes with a zero are **79.35%** of the candidates at n = 11. The
extra kills keep **57.6%** of them through the window's 100 primes, 53.4%
through the in-block rounds and **40.13%** to the Fermat stage. Overall,
33.6% fewer survivors leave the window and 47.5% fewer reach the Fermat
stage. Weighted by the phase split, assuming each stage's cost follows its
input, that came to 1.28–1.31. That figure was a hypothesis (Rule 2).

**Built as four branches.** Round 5's (≤ 1, 0, 0) branch mixes zero-free
classes, which may not take the kills, with one-zero ones. It is split
into (0, 0, 0) and (1, 0, 0). The kernel is untouched, and the branch with
no zero keeps exactly round 5's tables. `GpuEngine(cofactor=True)` is
refused anywhere but a branch whose every class has exactly one zero, on
A229630. The kernel cache key carries the flag, because an inline group
bakes its kill set into the source. The planner's `window_depth` knows the
flag too. The kills reach the survival target before LIT_MAX (93 primes at
n = 11, 98 at n = 10, 86 at n = 12), and G18 pins the planner to the
engine.

**G18 found a kernel at 2 blocks.** At n = 9 the zero-free branch is small
(217,728 first-level residues), so the queue guard's halving left it
nu = 27 third-level residues a launch. NU is a literal the sieve divides
blockIdx.z by. At 27 it compiled to 254 registers and 2 blocks a SM, and
the launch bound spilled 24 bytes, past SIEVE_SPILL_OK. At nu = 8, 16 or
32 the same branch is 168 registers, 3 blocks and 8 bytes. The semiprime
branches now round their planned nu DOWN to a power of two (`nu_pow2`),
so every budget and guard still holds. Other families are not touched:
their nu sets their campaigns' launch cursors.

**Measured** (scratch harnesses `ab_cof.py` / `ab_p3.py`: seconds per
segment from stratified launch samples per branch, Fermat stage on, arms
interleaved, each arm's fingerprint checked identical on every round), on
the live segment (period 642 of the semiprime wheel):

| arm | seconds a segment | rate | values/s to the host |
|---|---|---|---|
| p2 (round 5) | 4,748–4,849 | 2.29–2.33×10¹⁵ m/s | 346–353 |
| cofactor sieve (prototype, kill sets patched in) | 3,657–3,751 | 2.96–3.03×10¹⁵ m/s | 229–235 |
| p2, the repo's run | 5,346–5,391 | 2.06×10¹⁵ m/s | |
| p3, the repo's engine (`nu_pow2` in) | 4,119–4,125 | 2.69×10¹⁵ m/s | 212 |

**1.30x: the prototype 1.299 [1.293, 1.313] and the repo's p3 1.302
[1.298, 1.307], medians of three paired rounds each**, which is the cost
model's figure. The second pair ran about 10% low on both arms, which is
ambient. The values the host classifies per unit of line fall to 0.52,
the Fermat-entry density, so the host's load falls with them.

**The split on p3** (same harness, same segment): the sieve kernel 69.1%
(2,878 s a segment, against 2,827 on p2: the window's cost is per
candidate and did not move, and the in-block rounds are a small part of
it), the generated tail 14.2% (845 → 593 s), the Fermat stage 11.3%
(808 → 471 s) and the generic round 5.3% (410 → 222 s). A229630's next
lever is the window's, not the survivors'.

**At the other filters (CLAUDE.md 5g)**, same harness: **n = 12** (the
promotion after a(11), at m = 10²⁰) **1.28 [1.273, 1.287]**, 7.8×10¹⁵ m/s,
every branch at 3 blocks. **n = 10** (a filter of minutes, a check under
rule 3b) **1.09 [1.085, 1.093]**, 1.27×10¹⁵ m/s. Its segments are about 11 s
and its minor branches 1–3 launches, so the sample is coarse; the one-zero
half gains about 1.18 there. Faster everywhere, no cliff. G18 compiles
every branch of every opening to 3 blocks.

**Exactness at the production configuration** (`exact_cof.py`): on the
live segment, for 21 third-level classes (14 zero-free at level 3, 7 with
a zero there), p2's stream with the Fermat stage on, filtered by
`semi_cofactor_ok`, equals the prototype's stream: 3,798 of 7,371
survivors kept, with no duplicates. For 12 more classes (8 and 4) it
equals the repo engine's (`exact_repo.py`): 2,112 of 4,187. Each one sampled passes the CPU sieve and the CPU
Fermat chain. G24 pins the stream to the CPU engine filtered by both
conditions on seven populated windows; the filter removed 48,227 there.
G14 checks every table of a cofactor branch against the definition written
out: the window chain, the in-block and prefix groups, and now the inline
groups' masks as the emitter produced them, where it had rebuilt them
from killed_residues.

**The cursor**: plan p3 (launch.py PLAN_VERSIONS) runs on the same period
and segment as p2. The launches inside a segment are counted over
different branches, though, so a p2 cursor is ADOPTED like a p1 one, at
once. An open segment is re-swept and its census counts the swept part
twice. The live checkpoint was open at launch 16,255 of 47,742, about 20
minutes at the new rate. `_adoption_drill` now runs both plans, closed and
open.

**The review's other three, priced:**

* **Excluding 4 and 9 (and every p²) by masks, without growing the
  wheel.** Exact density at n = 11: 4 | m in 10.32% of the candidates,
  9 | m in 6.88% more; with every wheel prime's square, 21.75%. All of it
  lies in the classes with a zero, so it stacks with the cofactor sieve
  (overall Fermat-entry density 0.525 → 0.438). It cannot go in the window
  tables, which need the period invertible modulo the prime, and 2 and 3
  divide it. It can go per candidate: a composite in-block modulus (36,
  inline), or a test at extraction. Either way it is emitter work in the
  cofactor branches, with the queue sizing told its true per-branch
  density. Priced from p3's split: it removes about 19% of what leaves the
  window, and 31% of the device is downstream of the sieve kernel, so
  about 1.05–1.06. That is ~1.5 h of a(11)'s ~27 h. The version that also
  saves window work gives the classes with their zero at 2 a period of 2W:
  only m ≡ 2 (mod 4) is enumerated, in 64-period windows (the width curve's
  0.84), the same line a segment. That is about 1.09 for 2 alone, but it
  needs branches on different periods inside one segment, and an odd
  segment start then splits a period. **Unbuilt, priced for the owner.**
* **Fermat-testing the cofactor r′ = m/p first in the one-zero branches**
  (r′ must be prime). After the cofactor sieve, r′ is prime with
  probability about 0.37, so 63% of those branches' Fermat entries would
  die on a two-limb test before k = 1. About 1.03, plus host load.
  Unbuilt.
* **Montgomery squaring**: already priced (~1.03 at an 18% Fermat share,
  now smaller). Unbuilt.
* **A229902**: the packed offsets and the periodic read on the plain-table
  path (round 4's priced-unbuilt item), and its n = 12 wheel. They belong
  to an A229902 round at its day-long filter (n = 12, 35 days median),
  measured there. Not this round.

**The score shapes** (BENCHMARKS.md). S229630 still covers a whole n = 9
segment, and its p3 stream is p2's over it filtered by `semi_cofactor_ok`:
1,439 of 2,899, checked value by value (`freeze_cof.py`, after p2's stream
reproduced the old fingerprint). S229630L is now 16 launches of the first
branch (16 + 32 + 1 + 1), about the old shape's 51. Its rate against round
5's reading (2.34 against 2.20×10¹⁵ m/s, 1.07) is NOT the engine's ratio.
The unit changed, and it is four sweeps from the segment's start, each
paying an unpipelined first launch, a cost the steady-state A/B excludes.
The paired 1.30 is the record (Rule 4).

**Expected clock to a confirmed a(11)** from the cursor, over the model's
2.8×10²⁰ of line: about 27 h at 2.93×10¹⁵ m/s (round 5's measured
2.25×10¹⁵ m/s × 1.30), against 35 h on p2, plus about 0.3 h to re-sweep
the open segment.

## Round 7 — Nsight Compute at the day-long filters (2026-10-20)

**Target**: A229630 n = 11 on plan p3, the live filter, on the live
segment (period 642), the dominant branch (1, 0, 0) + cofactor, 70% of the
device. Every phase above 5% was profiled (`ncu_target.py`: that branch
built exactly as SemiprimeEngine builds it, 4 launches from mid-segment;
`--set full`, one launch of each kernel; `rawpick.py` and `sass_census.py`
read the raw metrics and the SASS split at BAR.SYNC). Then the bounds it
named were attacked, paired, at every family's day-long filter.

| phase (per 138 ms launch) | bound, measured | headroom |
|---|---|---|
| sieve kernel, 69% (the window loop is 82% of its samples) | **LSU issue 98.4%** (`sm__inst_executed_pipe_lsu`; lsuin requests 98.0%). The data pipe moves only 54% of its peak in wavefronts. Stall: MIO throttle | ALU 51%, issue 44%, 0.71 eligible warps a scheduler at 12 warps a SM (3 blocks: registers and shared memory both). Bank conflicts 1.9% of shared-load wavefronts (the "44%" hint is about stores, 2.6% of the traffic) |
| the window loop's SASS | **5.0 `LDS` (32-bit) per prime per window**, 4.2 `LOP3`, 4.0 `SHF.R.W`, 1.2 `IADD3`: the plain table read a word at a time, as round 2 found at A229626 n = 10 | |
| generated tail rounds, 14% | **FMA-heavy pipe 81%** (the Barrett products); stall math-pipe throttle | issue 62%, occupancy 80%, L1 hits 95%; DRAM 59% busy (the global queue), not binding |
| Fermat stages k = 1–3 (13.9 ms) | FMA-heavy 68–79% (Montgomery products), ALU 57–67% | issue 58–63% |
| Fermat stages k = 4–6 (3.6 ms) | **nothing**: issue 46%, 8%, 0.5%. Too few values per launch (one candidate a thread, a serial exponentiation): latency tails with the GPU nearly idle | ~2.6 ms a launch, ≤ 2% |
| generic last tail round, 5% (7.25 ms) | nothing at peak: long-scoreboard stalls on its per-test table loads (prime, magic, period row, mask) | issue 55% |

**The window's bound, attacked from both sides** (`ab_x.py`: shipped p3
against p3 with module constants set, every branch, survivors identical
round by round):

* **More warps: 4 blocks a SM** (SIEVE_MIN_BLOCKS 4, its spill allowed):
  128 registers, 328–408 bytes spilled. **0.951 [0.947, 0.953].** Local
  memory traffic is LSU instructions, so the spill lands on the pipe that
  is full.
* **Fewer LSU instructions: WINDOW_ALIGN = 2** (three aligned `LDS.64`
  instead of five `LDS`): **1.057 [1.053, 1.057]**. The profile of the
  changed kernel: `LDS.64` 3.0 per prime plus **5.1 `SEL`**, LSU 98.4% →
  72.9%, **ALU 51% → 85%** (now the full pipe), issue 44% → 59%, eligible
  warps 0.71 → 1.09; the sieve kernel 134.0 → 121.9 ms under the profiler.
  Round 2 measured the same arm at **0.974 / 0.997 / 0.997** at the
  OPENINGS (A229626 n = 10 and its siblings) and declined it. That was the
  minutes-long filter (OPTIMIZATION.md Rule 0a); at the day-long ones:

  | filter | WINDOW_ALIGN = 2 against 1 |
  |---|---|
  | A229630 n = 11 (live, p3) | **1.057** [1.053, 1.057] |
  | A229627 n = 12 (live, q = 2.86×10²¹) | **1.089** [1.089, 1.090] |
  | A229626 n = 12 (live, m = 2.70×10¹⁹; 19 days) | **1.032** [1.031, 1.033] |
  | A229902 n = 12 (m = 4.3×10²¹, its Q1; 35 days) | **1.005** [1.005, 1.012] |

* **WINDOW_ALIGN = 4** (two `LDS.128`) at A229630 n = 11: **0.954**
  [0.930, 0.966].
* **The window depth, re-swept on WINDOW_ALIGN = 2** (Rule 3.4: the
  cofactor kills and the aligned read both changed a window prime's
  worth): LIT_MAX 80 **0.995**; the cofactor branches at 100 (BIT_SURV
  0.001) **0.986**; the planner's 93 is the optimum. Flat.

**Verdict: not optimal.** The shipped WINDOW_ALIGN = 1 left 1.03–1.09 at
three of the four day-long filters and was neutral at the fourth. It is an
existing gated arm: G9 runs the plain table at whatever WINDOW_ALIGN says
and G14 emulates the aligned read. It changes no survivor and no launch
decomposition, so no cursor moves. Its price at the openings is round 2's
0.97–1.0 on filters of seconds to minutes.

**SHIPPED: WINDOW_ALIGN = 2** (owner: "do whatever is fastest"). Checked
first at the filters the campaigns promote into next (CLAUDE.md 5g):
**A229630 n = 12 1.067 [1.065, 1.073]** (five rounds; a first three-round
run swung 0.88–1.13 with the arms slow in alternate rounds, ambient, and
was repeated), **A229902 n = 11 1.004** [1.002, 1.014]. **The flip found a
bug, through G22**: the pairs table's fit was computed from the window
table AFTER the aligned read's padding, so at A = 2 an engine whose pairs
table fits was pushed onto the plain path, which is slower and leaves G22
with no offset table to check. The layout is now decided on the unpadded
table, and the table is rebuilt padded only for the plain path: an engine
on the pairs table compiles exactly as before. Every day-long filter above
was on the plain table in both arms, so its ratio stands. Gates: G9, G14,
G18, G22 and the rest per gate (the first compile of every configuration,
in four capped runs), then `launch.py --selftest` 61/61 green (216 s
warm) and `score.py` exit 0 with every fingerprint reproduced. S229630L
read 2.51×10⁹ against 2.34×10⁹ the round before (1.07). SCORE and the
other openings' shapes moved 0.97–1.02, the price above. The anchors read
~10% high that run, which is ambient. Expected clock to a confirmed
A229630 a(11) from the cursor: about 25 h (2.8×10²⁰ of line at
3.1×10¹⁵ m/s), against 27 h after round 6 and 35 h after round 5.

**What remains, priced (none of it measured yet):**

* the aligned window is now ALU-bound on its selects: the pairs table in
  dynamic shared memory (round 2's priced lever) removes them at a block a
  SM; a 64-bit-lane funnel is the representation-hunt alternative
  (INNOVATION.md Part 1, owed on this loop);
* the tail rounds sit at the multiply pipe: the representation hunt on the
  Barrett pack (32-bit packs where M fits, products per prime) is owed;
* the Fermat tails: run stages k ≥ 4 on a second stream, overlapped with
  the next launch's sieve, or batch them across launches: ≤ 2–4%;
* Montgomery squaring on the stages that are multiply-bound: ~1.02 now;
* generating the last tail round too (the planner never generates the
  round that ends at the last prime): its 5%, at the 1.17–1.26 generation
  bought the other rounds, ~1–2%.

## Where it stands — the termination table (OPTIMIZATION.md Part 3)

(Round 7's table, at A229630 n = 11, supersedes this one for the
day-long filters: there the window's WINDOW_ALIGN = 2 verdict below is
reversed and shipped. This table stays as the record of the openings.)

A229626 n = 10, engine v1 as shipped: 5.8×10¹¹ candidates a second,
2.4–2.6×10¹⁴ m/s; the device time is the wall clock to 0.1%.

| phase | share | verdict |
|---|---|---|
| sieve kernel: the window | ~38% | **bound by the shared-load pipe and the ALU together, at 12 warps a SM** — measured from both sides: the aligned read cut the LSU by a third and moved the bound to issue (0.97–1.0); 88 and 112 window primes 0.98 and 0.84; 60 and 40 0.78 and 0.61. Lever priced, unbuilt: the pairs table in DYNAMIC shared memory (29 KB of tables + 14 KB of queues: two blocks a SM, not three) — the trade of a third of the warps for no selects and three loads a prime is unmeasured |
| sieve kernel: in-block rounds | ~10% | K2_ROUND_PRIMES_MAX re-swept (64), generated code, the global queue guarded |
| generated tail rounds | 28% | coverage swept to its end (everything generated: no better); TAIL_ROUND_DROP swept; the depth swept (2¹³). Unprofiled since generation: **owed** an Nsight Compute pass on `tailgen` |
| Fermat stage | 18–20% | R mod N fixed (1.018). Priced, unbuilt: a dedicated Montgomery SQUARING (every step of the exponentiation is a square; a symmetric product is ~NL²/2 multiplies against NL², ~25% of the product half — ~1.03 overall at 18%); a native 64-bit path for the one- and two-limb k = 1 stage |
| generic tail round (the last) | 2–3% | below 5% |
| host | ~0.5 core | 1–4 thousand values a second; the pool is sized from a measurement |

**Priced options not built** (Rule 5b — the owner decides what to spend):

1. **Pairs/quads in dynamic shared memory** (above). Unmeasured; the one
   lever that removes window loads without adding selects.
2. **Montgomery squaring in the Fermat stage**, ~1.03.
3. **The partially forced classes of A229627** (OPTIMIZATION.md §2.15): 5
   and 7 each leave q two classes (1 and 4 mod 5, 1 and 6 mod 7), so four
   classes mod 210 free 5 and 7 from the period for the next wheel prime.
   Unmeasured here; the price is the 4x longer coverage unit against rule
   5j, and A229627's a(11) is a ~2-day search.
4. **A Fermat stage on more forms** (CENSUS_FLOOR 6 → 7): the k = 6 stage
   is 0.3% of the device; the host's 1–4 thousand values a second would
   fall 6–7x. Not a rate lever; a load lever, if the pool ever binds.

## Measurements at every filter the campaigns pass (CLAUDE.md 5g)

The campaign engine (planned, Fermat stage on, segment = window), from the
model's floor for the filter, three interleaved rounds (rates.py):

| family | filter | wheel | window | record | rate | to the host |
|---|---|---|---|---|---|---|
| A229626 | 10 (open) | to 89, unit 1 | 128 | narrow | 2.36×10¹⁴ m/s | 1,985/s |
| A229626 | 11 | to 89 | 256 | narrow | 4.98×10¹⁴ m/s | 845/s |
| A229626 | 12 | to 89 | 256 | wide | 1.49×10¹⁵ m/s | 239/s |
| A229627 | 9 (open) | to 47, 1 (mod 6) | 256 | narrow | 2.68×10¹⁵ q/s | 992/s |
| A229627 | 10 | to 89 | 256 | narrow | 8.46×10¹⁵ q/s | 278/s |
| A229627 | 11 | to 89 | 256 | wide | 1.67×10¹⁶ q/s | 62/s |
| A229630 | 9 (open) | to 73, unit 1 | 256 | narrow | 6.60×10¹³ m/s | 4,239/s |
| A229630 | 10 | to 89 | 256 | narrow | 2.35×10¹⁴ m/s | 1,749/s |
| A229630 | 11 | to 89 | 256 | narrow | 4.98×10¹⁴ m/s | 432/s |
| A229902 | 10 (live) | to 83, 0 (mod 10) | 256 | narrow | 1.23×10¹⁵ m/s | 1,488/s |
| A229902 | 11 | to 83 | 256 | narrow | 2.72×10¹⁵ m/s | 636/s |
| A229902 | 12 | to 83 | 256 | narrow | 4.58×10¹⁵ m/s | 248/s |

(A229902's opening filter, n = 9, lasts one segment: its first segment
holds a(8) = a(9).) G18 compiles every one of these to 3 blocks a SM with
no spill but the bounded one.
