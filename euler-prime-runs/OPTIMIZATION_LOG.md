# OPTIMIZATION_LOG -- euler-prime-runs (attempt -> measurement -> verdict)

Benchmark shape: n=17 filter, [1e16, 1e16 + span), GPU, RTX 4090,
CuPy 14.1.1. Rates are end-to-end (kernel + survivor readback).

| # | change | rate (p/s) | vs prev | verdict |
|---|--------|-----------|---------|---------|
| 0 | v1: 23# wheel (u32 offs), plain u64 `%` mods, 1D grid (per-thread div/mod for indexing), shared-mem stage-1 masks | 4.46e13 | -- | baseline, gated |
| 1 | v2: fold 29 into wheel (period 6.47e9, ~1M u64 offsets), Barrett magic-multiply for ALL mods, 2D grid (blockIdx.y = period, no indexing div) | 1.70e14 | 3.8x | KEPT, gated (G6 incl. 1.7e19 ceiling window) |
| 2 | v3: drop per-block shared-mask copy; stage-1 masks read from global (11 KB, L2-resident) | 1.92e14 | +12% | KEPT, gated |
| 3 | block 512 / 1024 (both variants) | 1.85e14 / 1.33e14 | worse | rejected |
| 4 | shared masks at block 512/1024 | 1.69e14 / 1.02e14 | worse | rejected |
| 5 | v4: multi-period threads (T=2048 periods/thread), first-16 stage-1 residues stepped incrementally (r += M mod q, cond. subtract; one Barrett per prime per T periods), Barrett fallback for the ~0.3% passing all 16 | 3.43e14 | 2.5x same-day (1.8x vs frozen v3 SCORE; see note) | KEPT, gated |

Frozen at v4: **5.13e14 p/s median on an idle GPU** (SCORE
512,819,184; first captured under ambient desktop load as 3.43e14 /
SCORE 343,361,199 -- see the variance note in BENCHMARKS.md).
Height-flat (0.8% spread across 1e16 / 1e18 / 1.7e19), confirmed in
production by the phase-1 sweep average (~5.0e14 over 9 h).

Note on the v4 ratio: interleaved same-day A/B gave v3 = 1.36e14 and
v4 = 3.42e14 (2.5x) under identical ambient desktop GPU load; the
frozen v3 SCORE (1.90e14) was taken uncontended, so the ledger ratio
(1.8x) understates the kernel change. The v4 SCORE above was recorded
under the ambient load and is, if anything, conservative: the
restarted production hunt sustained 5.0e14 p/s at p ~ 2e18 during a
quiet-desktop window (~2.6x uncontended v3), matching the v3
contention discount (1.36/1.90 = 0.72) applied in reverse. After the
phase-1 sweep completed, an idle-GPU window allowed a clean capture:
5.13e14 (SCORE 512,819,184), now the frozen entry; the loaded-desktop
readings (3.43-3.47e14) are documented in BENCHMARKS.md's variance
note.

v4 sweep (all parity-clean vs the v3 stream, bench + 1.7e19 windows):
rate rises with T and plateaus at T=1024..4096 (T=32: 2.16x, T=128:
2.36x, T=2048: 2.53x); NINC=16 is the register sweet spot (NINC=8:
2.30x, 12: 2.34x, 14: 2.41x, 18: 2.31x, 24: 1.58x -- spills); block
128/256 tie, 512 worse. First 16 stage-1 primes (31..101) carry ~99.7%
of stage-1 kills at n=17, so the Barrett fallback path is cold.

Cost accounting at v4: ~5.9e10 candidates/s of wheel survivors
(3.1e-4 of p-space), ~2.5 expected stage-1 tests per candidate before
kill -- now an add + compare-subtract + L2 bitmask load each, with the
Barrett multiply amortized to once per prime per 2048 periods. Host-side
MR load is negligible (~3.6e-13 of p-space reaches MR; ~6.5M survivors
per 1.8e19, confirmed by the live campaign counter: 8.4e5 at 2.4e18).

## TODOs (unpriced, try only with gates green)

- Sort stage-1 primes by measured kill rate instead of ascending q
  (near-identical ordering; expected ~1%).
- Persistent-kernel + device-side segment loop to cut launch overhead
  (launches are 8192 periods = 5.3e13 p; overhead already amortized;
  expected small).
- Batch MR on GPU (Montgomery 64-bit): only relevant if Q2 is lowered
  or a wider survivor stream is wanted (e.g. n=16 census mode).

## Phase 2 (2026-08-06): 128-bit value path -- implemented

The last TODO of phase 1 (128-bit path for p > 1.8e19) landed as a new
engine version per the numeric-hygiene rule: kernel `ladder_filter128`
+ `GpuEngine128` / `CpuEngine128`, ceiling P128_CEIL = 1e24 (enforced;
values stay >3x under the 3.317e24 MR validity bound), gates G9-G12
(overlap parity vs the proven u64 engines, direct trial-division
parity on mini-windows at 2.35e20 and the ceiling, a(18) +
Waldvogel-Leikauf run-21 end-to-end rediscoveries), own frozen
fingerprint (SCORE128, window [2.3e20, +5e14), 178 survivors).

The v4 insight carried over for free: the incremental stage-1a
residues never depended on p's magnitude, so the hot loop is
unchanged; the cold fallback pays 3 Barretts per prime (k mod q,
off mod q, recombine) instead of 1.

### v1-128 -> v2-128: closing the 23% gap (same day)

The one-kernel v1-128 measured 0.77x the u64 kernel (paired
interleaved A/B). The hunt for the missing 23% is a lesson in
measuring before believing:

| attempt | result | verdict |
|---------|--------|---------|
| hoist (k, off) window bounds out of the period loop (per-thread t-range; interior has NO bounds checks) | 0.784x | kept (right thing, wrong bottleneck) |
| NINC sweep 10/12/14/16 on the 128 kernel | 16 best | no change |
| `__launch_bounds__(256,4)`: regs 72 -> 64, zero spill (matches v4's 4 blocks/SM) | 0.815x | kept, still not it |
| `#pragma unroll 4` / compile-time loop bound | no effect | rejected |
| STRIPPED experiment: both kernels with the cold path deleted | both run 2.7e15 p/s, EQUAL | the smoking gun |

The stripped run showed the hot loops were never the problem: the
cold path (stage 1b + stage 2) consumed ~80% of runtime in BOTH
kernels through warp serialization -- one lane survives stage 1a and
31 lanes idle while it grinds up to ~6.5k primes; the 128 path's
3-Barrett cold arithmetic just stretched that serial section 1.3x,
which is exactly the observed ratio.

v2-128 therefore splits the work (two-phase compaction): the hot
kernel does stage 1a only and enqueues surviving (offset, period)
pairs (packed u64, 512 MB queue, ~5.2e7 per 8192-period launch); a
second kernel processes the queue one candidate per thread with every
lane busy. Survivor set bit-identical (SCORE128 fingerprint
reproduced; boundary torture windows vs CPU-128 all equal). Paired
A/B after: **1.13x the u64 kernel** (median 1.135, min 1.111, 12
rounds) -- the 128-bit path is now FASTER than the proven u64 engine.
Cold kernel: 30 regs. Certified by the full battery: same-battery
pair SCORE 323,394,817 / SCORE128 362,319,437 (ambient desktop load;
the ratio, not the absolute rates, is the stable quantity).

Phase-2 TODO (optimize under SCORE128, gates green):
- The same compaction restructure would lift the u64 engine too (its
  cold path is the same 80%); that is a v5 u64-engine candidate, kept
  out of scope while phase 2 runs.
- Cold-kernel tail: sort/partition the queue by kill depth or stage
  the s1/s2 tables through shared memory; the cold phase still costs
  ~2.5 ns per queued candidate.

## Phase 2 v3-128 (2026-08-15): the bit-sieve, and a stale cost model

Baseline for this session, one battery, ambient desktop load:
SCORE 352,982,740 / SCORE128 422,725,375. Final, full battery green:
SCORE 305,864,144 / **SCORE128 6,341,803,579**. The controlled
decomposition (v2 and v3 measured back to back at the same 8192-period
launch shape) is **10.29x from the engine**, 1.395x more from the launch
size in steady state, so **~14x sustained**; the frozen window shows
18.31x only because it collapses to one launch. See BENCHMARKS.md.

### The cost model was wrong, and cheap to check

The note above -- "the cold phase costs ~2.5 ns per queued candidate" --
is arithmetically impossible against production wall-clock: 5.1e7 queued
candidates per launch x 2.5 ns = 127 ms, but a whole 8192-period launch
took 96 ms. The 80%-cold finding it descends from describes the
**one-kernel v1-128**, which is exactly what the v2 compaction split
fixed; nobody re-measured the split afterwards. CUDA events around the
two kernels on the SCORE128 window settled it in two minutes:

| phase | ms | share |
|-------|----|-------|
| hot stage-1a (`ladder_stage1_128`) | 1103.6 | **83.4%** |
| host sync gap between the kernels | 2.7 | 0.2% |
| cold stage-1b + stage-2 (`ladder_cold_128`) | 217.3 | 16.4% |

So the hot kernel, not the cold one, was the target -- and an
instruction count explains it. Per warp-period (32 candidates, one
period) the measured budget is ~241 warp-instruction slots, of which 48
go to stepping all MP_NINC residues *unconditionally* even though the
average candidate dies at test 2.2, and the early-exit mask chain costs
9.20 warp-iterations (mean 2.20 per lane: a 4.2x warp-divergence tax),
each carrying a 32-way scattered L1 gather.

### The ledger

| # | change | vs prev | verdict |
|---|--------|---------|---------|
| 6 | **v3-128 bit-sieve stage 1a**: per prime, OR one precomputed W-bit kill pattern per W periods and read survivors out of the complement with `__ffsll`, instead of stepping residues and testing candidates one at a time | SCORE128 422.7M -> 1,889.8M = **4.47x**; hot kernel 1103.6 -> 45.7 ms (**24x**), flipping the split to 16/83 hot/cold | KEPT, gated (G13) |
| 7 | launch size, steady-state A/B over [2.3e20, +2e15) (38 -> 3 launches): ppl 8192/16384/32768/65536/131072 | 1.000 / 1.162 / 1.280 / 1.353 / **1.395** | KEPT: PPL=131072 |
| 8 | **iterated compaction over stage 1b**: rounds of R primes, survivors forwarded to a second queue, counts kept on the device. ROUND 0/4/8/16/32 | 1.000 / 1.568 / **1.684** / 1.638 / 1.531 | KEPT: ROUND=8 |
| 9 | NINC re-sweep after (8): 16/20/24/28 | 1.000 / 1.126 / **1.143** / 1.095; 24 beats 28 by 1.058x at production ppl | KEPT: NINC 28 -> 24 |
| 10 | pattern width W=128 / W=256 (multi-word accumulator, one 16 B `ulonglong2` gather instead of two 8 B) | **0.252x / 0.314x** | REJECTED |
| 11 | warp-aggregated queue atomic | diagnostic first: replacing the push with a register counter made the sieve 94.95 -> 85.20 ms, so the whole push is **10%** of the sieve. Not worth hand-rolled ballot/popc aggregation | REJECTED (now priced) |
| 12 | removing the two per-launch blocking `.get()` syncs | measured at 0.2% of GPU time | REJECTED (now priced) |

Interior optima and how they moved: an extra sieve prime costs one OR
plus one stepped residue per W periods and multiplies the cold queue by
(q-17)/q, so NINC has an interior optimum -- and it is not stable across
the other changes. Against the single-shot cold path NINC=28 won
(16/24/26/28/32 -> 1.000/1.363/1.387/1.434/1.349); the compaction rounds
then made that path ~3.5x cheaper and the optimum fell to 24. Anything
tuned before (8) had to be re-swept after it.

Why W=128 lost, since the prediction was the opposite: the multi-word
accumulator turns `acc` into an array whose extraction loop carries
data-dependent control flow, and the win from halving the gather count
is not worth whatever that costs (register pressure or a local-memory
spill). Recorded rather than explained -- the point of this ledger.

Why stage 2 is NOT split into its own compacted kernel, despite being
24% of the cold phase and 109 tests deep per entering lane: it is
entered by 5.69e-3 of the queue, so at most one lane per warp is ever in
it. Per-warp cost is 19.3 iterations against 32 x 0.62 = 19.8 for the
same work perfectly packed -- there is no divergence waste to recover.
Stage 1b is the opposite case (mean 13.85 tests per lane, warp-max 80.4,
5.8x waste), which is why (8) pays there and only there.

### Final split (NINC=24, ROUND=8, W=64, PPL=131072)

| phase | share |
|-------|-------|
| bit-sieve stage 1a | 64.3% |
| stage-1b compaction rounds | 17.3% |
| cold kernel (stage 2) | 18.4% |

The sieve is dominant again and is ~90% pattern work (per #11), so the
next real lever is generating fewer candidates, i.e. a wider wheel.

### The 31# wheel: attempted after all, 1.212x (and the decline was wrong)

Folding 31 into the wheel generates **2.07x fewer candidates** for a
mathematically identical survivor set -- the union of tested primes is
unchanged, so both frozen fingerprints still reproduce bit-for-bit, which
makes this an unusually safe change to a hot path.

| step | result |
|------|--------|
| 31# wheel, sieve depth left at 24 | **1.121x** -- most of the 2.07x eaten |
| diagnosis: sieve range shifts 31..139 -> 37..149, losing its strongest killer (31 kills 52%, 149 kills 11%); queue per unit p-line grew 1.41x | -- |
| re-sweep sieve depth on the new wheel: 24/26/28/30/32/36 | 1.110 / 1.152 / **1.212** / 1.159 / 1.160 / 0.874 |
| KEPT: 31# wheel + NINC 24 -> 28 | **1.212x**, both fingerprints exact, streams identical |

**Then the round size moved too.** The wheel shifted work into stage 1b
(17.3% -> 34.6% of GPU time), so the compaction round size tuned against the
old balance was stale by construction. Re-swept: 4/6/8/12/16/20/24/32 ->
0.769/0.922/1.000/1.088/**1.134**/1.128/1.121/1.081, peak moving 8 -> 16.
Worth another **1.134x**, for **1.374x** from this round of work and
**19.4x** cumulative over the engine that swept leg 1.

That one was found only because the termination table in ../OPTIMIZATION.md
requires a verdict per phase: the rounds row had visibly grown, which is what
prompted the re-sweep. Without the table it would have been invisible --
nothing looked broken, the engine was simply leaving 13% on the floor.

Mechanics: `best_wheel(n)` picks the largest wheel whose offset table fits a
budget (50M offsets), so n=13/17 get 31# and n=5/9 fall back to 29# --
the table is 2.99e7 offsets at n=17 but 5.4e8 at n=5.  `build_wheel` is now
chunked over the new prime's residue classes so peak memory stays bounded
(verified byte-identical to the previous builder at n=5,6,7,9,13,17 on both
existing wheels).  The launch size became a **span** rather than a period
count, since the 31# period is 31x longer and 131072 of them would want a
17 GB queue; PPL is derived from that span and capped by a queue budget.

The cursor was converted, not reused: the config key now carries the wheel,
so a cursor from a different wheel is rejected rather than silently
misinterpreted (next_k is denominated in periods, and the period changed by
31x).  New next_k = floor(old_depth / M_31) -- floor, so the seam OVERLAPS by
up to one period (1.75e11 of p-line, 0.063 expected survivors) rather than
risking a gap, following the same convention as the old u64 seam.

### Incident: the wheel change shipped with a cursor desync (2026-08-15)

The first production start after the 31# wheel landed began at 1.168e19
instead of the 3.62e20 frontier, and had to be stopped. Root cause, and it
is embarrassing in a useful way: **two places computed the wheel
independently.**

- `launch.py`'s engine factory still pinned `wheel_primes=WHEEL_PRIMES_29`,
  left over from when the wheel was fixed. So production ran the 29# wheel.
- `ckpt_key()` derived the wheel from `best_wheel(n)` -- 31#.

The key therefore MATCHED and the cursor loaded, but `next_k` counts wheel
PERIODS, and 1,804,941,739 periods of 31# got read as periods of 29#:
1,804,941,739 x 6.47e9 = 1.168e19. Exactly where it started.

The wasted sweep was the cheap part. The dangerous part was that `next_k`
then advanced in 29# units inside a file whose `M` field said 31#: after
three minutes it read as 4.06e20, PAST the true 3.62e20 frontier. Resuming
after fixing the wheel would have skipped ~4.4e19 of never-swept range and
put a silent GAP in the exhaustive-coverage claim -- the one thing this
whole apparatus exists to prevent.

Fixes, in order of value:

1. `check_cursor()`: the cursor's `M` must equal the engine's `M`, or the
   campaign refuses to start. This does not depend on anyone having derived
   the key correctly, which is precisely why it is the fix that matters --
   it converts the worst failure class here into a refusal to run. Verified
   against the exact bad state.
2. The engine is now the single source of truth for the wheel: no override
   in the launcher, and `ckpt_key`/`fresh_ckpt` take the engine and read
   `eng.wheel_primes` / `eng.M` off it. `fresh_ckpt` had a hardcoded
   `M = 6469693230` too, and `status()` a hardcoded fallback -- both were
   the same latent bug waiting for a second wheel to exist.
3. `status()` now prints the period and `next_k` alongside the position, so
   a desync is visible rather than inferred.

Cleanup: 15 duplicate near-miss entries (runs 13/14/15/16 = 10/3/1/1) were
removed from the census -- the re-swept band lies below the old frontier, so
every sighting in it was a second recording of a phase-1 find. Counters and
the survivor total were restored to the pre-incident values, the cursor was
reset to 3.62e20 in 31# periods, and `canaries_done` was cleared because the
prelude had run on the wrong wheel. No run-17/18 fell in the band, so no
evidence JSON was duplicated; coverage never had a gap, only an overlap.

The generalisable lesson, now in ../OPTIMIZATION.md: a derived quantity
computed in two places will eventually disagree, and a checkpoint key that
*describes* the configuration is not the same as an assertion that the
configuration MATCHES. Write the assertion.

### Why the original decline was wrong (kept as the record)

The original entry read: "not implemented because the offset table is
n-dependent and explodes for the small n the gate battery runs on ...
production would then run a wheel that G6/G13 cannot exercise at their
working n, which trades a factor of 1.45 for a hole in the parity gates."

Both halves were wrong. G6 runs **four cases at n=17**, so it does exercise
the production wheel; and G4/G5 already run a different wheel from production
deliberately, so "production uses a wheel some gates don't" was never the
hole it was described as. The real constraint was memory at one parameter,
which a per-n budget solves in a dozen lines. The estimate was wrong too:
1.45x predicted, 1.121x delivered until the sieve depth was re-swept, then
1.212x.

Left here in full because a wrong decline is the most expensive kind of log
entry -- it stops the next person from looking. A decline needs a reason that
survives re-reading, and this one did not.

### Two robustness bugs the gates caught (both mine, both in tuning paths)

- Changing the class attribute `T` after construction desynced the
  compiled kernel (T is a literal) from the launch geometry (`gy`). The
  frozen fingerprint failed instantly: count 43 instead of 178. The
  engine now snapshots NINC/T/PPL/ROUND onto the instance in `__init__`.
- The second ping-pong queue was allocated only when the *mutable*
  round schedule was non-empty, so sizing the queues while the schedule
  happened to be empty left a later round writing to a null pointer
  (`cudaErrorIllegalAddress`). Allocation is now keyed off the ROUND
  snapshot, with an explicit guard on the mismatch.

Both were introduced by A/B harness scaffolding rather than by the
kernels, which is its own lesson: the tuning knobs need the same
discipline as the arithmetic.

### Engine unification (same day): deleting the 64-bit boundary

Not a throughput change -- a complexity change, and the one that should
have been made at the start of phase 2 rather than after it.

The project had grown two engines and two campaigns: a u64 kernel capped
at 1.8e19 and a 128-bit path above it, selected by `--engine gpu128`,
with separate checkpoints, separate canary preludes, a deliberately
re-covered seam at the cap, and a default `python launch.py` that quietly
ran the *capped* engine. None of that was ever necessary. The 128 path's
representation -- carry the candidate as (k, off) with p = k*29# + off and
reduce every test to ((k mod q)*(M mod q) + off mod q) mod q -- is exactly
as valid at 1e5 as at 1e23. It was written to survive 2^64 and happens to
span everything.

So the campaign now has one engine, one cursor, no engine flag, and no
seam; the GPU is always used. What changed:

- `--engine` defaults to the production GPU engine and spans
  [1e5, 1e24). The old engine selectors are gone rather than deprecated:
  a flag that still parses is still a thing to explain.
- One cursor (`campaign_checkpoint.json`), migrated from the phase-2 file
  under the SAME config key -- so the migrated cursor still has to pass
  huntlib's key check, and the 3.62e20 already covered stays valid. A
  fresh campaign starts at 0, because there is no longer a cap to start
  above.
- One canary prelude covering a(14)/a(15)/a(18) and the run-21 value,
  i.e. spanning both sides of 2^64 in one pass -- the boundary is no
  longer special and the prelude is what proves it.
- The verification re-sieve got *stronger*: it now always runs the numpy
  reference engine on the **23# wheel** while production runs 29#, so the
  alternate-alignment leg differs in both arithmetic and wheel at every
  height. Previously that only held below the u64 cap, where a 23# engine
  happened to be the one available.
- Both frozen benchmark shapes are now measured with the one engine,
  which makes SCORE vs SCORE128 a height-flatness check: flat to within a
  few percent across four orders of magnitude (captures 0.01% and 3.4%
  apart; the spread is ambient load, so the tighter one was luck and is
  not the number to quote).

The u64 kernel and the pre-bit-sieve 128 path were first made
unreachable, then **deleted outright** once their equivalence gate had run
green and been committed. Keeping them as parked references was the wrong
call: it left the working tree ambiguous about what would run from zero,
which is the question the tree has to answer. The equivalence evidence is
in the git history at the commit where the gate passed, which is where a
one-time migration proof belongs.

Gates retired with them: G9 (the two CPU engines against each other) and
G11 (the two GPU engines against each other) had no meaning once one side
of each pair was gone, and the old G13 (new engine vs old engine) was a
migration gate by construction. Their coverage was re-pointed before the
deletion, not dropped: G6 absorbed G11's CPU-vs-GPU cases and now runs
seven heights to the ceiling, G13 was rebuilt to prove slicing-
independence (which needs no second engine, because boundary bugs make
the answer depend on the slicing), and G14 pins the tables to the
divisibility definition directly. What stays permanently is the
independent numpy engine -- not a previous version, the other half of the
parity gate.

Generalized into ../OPTIMIZATION.md as the design rule to apply *before*
writing an engine, not after (section 2.7).

### Note on measurement method

One sequential (non-interleaved) NINC sweep reported 3.57e15 p/s at
NINC=26 against 2.72e15 at NINC=27 -- a 31% "cliff" that does not exist.
Interleaved rounds put 26 at 1.387x and 28 at 1.434x. Ambient desktop
GPU load moves the absolute rate by up to ~30% minute to minute (see
BENCHMARKS.md), so every number in the ledger above is a per-candidate
median over interleaved rounds, and every measurement re-checks the
frozen fingerprint before it counts as a data point.

---

## Phase 3 (2026-08-16): the cheap tests, and two ablations that lied

Starting point: the engine from the 31# wheel work, and the termination
table in ../OPTIMIZATION.md section 3.1 -- which flagged *itself* as stale,
because its shares predated the round-size change. Re-measuring first
(Rule 1) was again the highest-value action: the split had moved from the
recorded 48.1/34.6/17.3 to **54.7/25.0/20.3**, and the phase that had grown
was the one whose verdict line read "structurally optimal".

### The ledger

All ratios are per-candidate medians over interleaved rounds in ONE process,
every run re-checking the frozen 128 fingerprint, over a steady-state window
of 2e16 at 6.1e20 (24 launches, so no single-launch flattery).

| # | change | ratio | verdict |
|---|--------|-------|---------|
| 13 | **stage-2 kill test by bitset**: the scan over the n values of x^2+x asks a membership question about a set that never changes, and every stage-2 prime exceeds max(x^2+x), so no residue wraps -- rr dies iff rr == 0 or q - rr is itself of the form x^2+x. A 17-iteration loop becomes one bounds test and one bit probe | **1.165x** | KEPT, gated (G15). Cold kernel 170 -> 55 ms, its share 20.3% -> 7.6% |
| 14 | **balance the sieve grid**: blockIdx.y slices T periods and the last slice takes the remainder, but per-thread setup (NINC Barrett reductions) is paid in full by every slice. PPL=4228 with T=2048 gave slices of 2048/2048/**132**. Derive T from PPL instead: gy = round(PPL/T_target), T = ceil(PPL/gy) rounded up to W -- 2176, slices 2176/2052 | **1.066x** | KEPT. Derived, not tuned, because PPL moves with the wheel, with n and with LAUNCH_SPAN |
| 15 | **32-bit reductions in stage 1b** (`_R_MIX32`): of the three 64-bit Barretts per candidate-prime, only `off mod q` needs 64 bits. k never has to be formed -- the host knows k_base mod q and kp is the low half of the queue entry -- and the recombination kq*dM + oq stays under 2^32 for every stage-1 and stage-2 prime | **1.048x** | KEPT, gated (G15) |
| 16 | **sieve `__launch_bounds__` 4 -> 3 blocks/SM**: at 4 the compiler is held to 64 registers and spills 24 B/thread | **1.028x** | KEPT. 2 and 0 both give ~0.998x: below 3 the spill is already gone and only occupancy is being sold |
| 17 | ROUND re-sweep after #15: 16/20/24/28/34 | 1.000/1.016/**1.023**/1.009/0.978 | KEPT: ROUND 16 -> 24 |
| -- | **paired total, HEAD engine vs this one, same process, 7 rounds** | **1.294x** | both reproduce the frozen fingerprint on identical work |

The paired 1.294x is the load-bearing number and it is *less* than the
product of the rows (1.37x), because the individual ratios were measured
against different baselines and #14 overlaps the launch-size lever. Quote
the paired figure.

### Two ablations that lied, and the one that did not

This is the part worth reading. Pricing by deleting the suspect work
(section 3.3) is only definitive if the deletion leaves the rest of the
kernel doing the same thing, and twice it did not:

| ablation | reported | why it was wrong |
|----------|----------|------------------|
| replace the pattern gather with `pat[po]` (literal index) | sieve 400 -> **26 ms**, "the gather is 81% of the kernel" | the index is loop-invariant, so the compiler hoisted all 28 loads out of the loop. It measured a kernel with no loads at all, not one with cheap loads |
| replace it with `acc from r_j` (no memory access at all) | **2.99x SLOWER** | acc fills with garbage, the survivor bitmap inverts, and the extraction loop then runs on nearly every bit. It measured the extraction path, not the gather |
| confine the index with a mask: `pat[po + (r & 3)]` vs `& 15`, `& 63`, full q | **0.993 / 1.008 / 1.020 / 1.000** | valid: every variant keeps 28 data-dependent loads, so nothing hoists, and the survivor pattern is equally garbage in all four. Only the address spread changes |

The valid one is decisive and counter-intuitive: **within L1, gather
divergence is free.** Confining all 32 lanes of a warp to a single 32-byte
sector is worth nothing at all. So the sieve is bound by load *count*, not
by sector replays, and the rule for this kernel is: never trade one load
for two, however much smaller the table gets.

Which is exactly what the next attempt did.

### Rejected: the folded pattern table (0.685x)

`pat[r]` has bit u set iff (r + u*dm) mod q is forbidden, so consecutive
residues are not independent -- if r' = r + dm then pat[r'] is pat[r]
shifted by one. Writing r = s*dm (dm is invertible mod q, since q is not a
wheel prime) makes that exact: pat[r] bit u = b[s+u], where
b[m] = [(m*dm) mod q in F]. Every one of the q patterns is then a 64-bit
*window* into a single periodic bit-string, so prime q needs
ceil((q+63)/64) words instead of q. The whole table goes from **22,032
bytes to 904**, and the cursor gets cheaper too: stepping r by W*dm is
stepping s by W, and s0 = k + off*dm^-1 (mod q).

Measured **0.685x**, at every launch bound tried. The 24x smaller table
bought nothing, because sector spread was never the constraint, and
extracting a window that straddles a word boundary costs a second load --
28 loads became 56. Implemented, gated (it reproduced the frozen
fingerprint exactly, so the mathematics was right), measured, deleted.

The prediction that motivated it was mine, and it was the same error the
cost model made in Phase 2: reasoning about bytes and cache residency when
the machine was counting instructions.

### Priced and declined

| item | price | why not |
|------|-------|---------|
| bigger launches (PPL 4228 -> 9000) | **1.009x** for +2.1 GB of queue | it measured 1.041x *before* #14. Most of what a bigger launch bought was the grid tail, which #14 fixes for free; re-measured after, the lever is nearly gone. A constant worth paying for became one that was not, without the code changing |
| removing the mid-chain host round-trips | **0.995x** | confirms Phase 2's 0.2% finding at the new profile. The grid-striding cold kernel that removes them was kept anyway, because it makes the launch chain uniform, but it is NOT a speedup and is not counted in the 1.294x |
| ROUND_GRID 2048/4096/8192/16384 | 1.002/1.000/1.002/1.000 | the grid-stride loop is insensitive; never swept before, now it has been |
| NINC re-sweep, twice (24/26/28/30/32) | 0.987/0.996/**1.000**/0.931/0.870 | 28 is a genuine interior peak and stayed there through every other change this session. Re-swept again after #15: 26/28/30 -> 0.996/1.000/1.002 |
| T sweep 1024/2048/4096 at fixed PPL | 0.929/1.000/1.004 | flat -- which is what showed the PPL gain was launch overhead rather than T, and pointed at #14 |
| CRT-combining sieve primes into one table | not implemented, ~10% | halves the load count, the only thing the sieve cares about. But it stays L1-resident for at most 3-4 pairs (37*41 + 43*47 + 53*59 = 6,665 entries = 53 KB), so it buys 3 loads of 28; past that the table leaves L1, where divergence stops being free. Worth trying next, and the pairs must be the SMALLEST primes |
| the 37# wheel | 5.99e8 offsets = **4.8 GB** of VRAM | generates 37/(37-17) = 1.85x fewer candidates AND removes a prime from the sieve. 4.8 GB is affordable on a 24 GB card alongside the 2.5 GB of queues, so the old "16x over budget" decline is a statement about the budget constant, not about the hardware. The real costs are table build time and a fallback for every gate parameter. Biggest single item left |
| stage-2 compaction rounds | not implemented, bounded at 7.4% | the standing verdict "rare-and-deep, at most one lane per warp, already optimal" is **stale**: it described the pre-compaction design, where stage 2 sat behind all of stage 1. The cold kernel is now fed by the compaction chain, so every lane entering it runs stage 2 -- mean depth 109 over 6,370 primes, with a much larger warp-max |
| `_R_MIX32` extended to the cold kernel's stage-2 loop | not implemented, ~1.5% | same transformation, same preconditions; G15 already checks the u32 bound for stage-2 primes |

### Split after this round

| phase | share | verdict |
|-------|-------|---------|
| bit-sieve stage 1a | 66.3% | load-count bound, and divergence is free (0.993x at one sector). NINC is an interior peak; W=64 beats 128 (0.25x, Phase 2) and beats the folded form (0.685x). Levers left: CRT pairs (~10%) and the 37# wheel |
| stage-1b compaction rounds | 26.4% | 1.048x from #15, round size re-swept to 24 (1.023x), grid insensitive |
| cold kernel (stage 2) | 7.4% | 3.1x from #13; two priced items left, both bounded by the share |
| host + syncs | 2.5% | measured; removing them is 0.995x |

Not done -- three of the four phases still have named levers with prices on
them.
