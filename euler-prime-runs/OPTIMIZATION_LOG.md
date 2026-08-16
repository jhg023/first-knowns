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
| CRT-combining sieve primes into one table | **rejected on measurement** | see the table-cliff section below: three pairs cost 53 KB to save 3 loads of 28, and the cliff starts before 86 KB |
| the 37# wheel | 5.99e8 offsets = **4.8 GB** of VRAM | generates 37/(37-17) = 1.85x fewer candidates AND removes a prime from the sieve. 4.8 GB is affordable on a 24 GB card alongside the 2.5 GB of queues, so the old "16x over budget" decline is a statement about the budget constant, not about the hardware. The real costs are table build time and a fallback for every gate parameter. Biggest single item left |
| stage-2 compaction rounds | not implemented, bounded at 7.4% | the standing verdict "rare-and-deep, at most one lane per warp, already optimal" is **stale**: it described the pre-compaction design, where stage 2 sat behind all of stage 1. The cold kernel is now fed by the compaction chain, so every lane entering it runs stage 2 -- mean depth 109 over 6,370 primes, with a much larger warp-max |
| `_R_MIX32` extended to the cold kernel's stage-2 loop | not implemented, ~1.5% | same transformation, same preconditions; G15 already checks the u32 bound for stage-2 primes |

### The sieve's table is pinned from both sides (and CRT pairing is dead)

The top remaining sieve lever was CRT-combining pairs of sieve primes into
one table indexed by r mod (q1*q2): one load instead of two for each pair,
which is the only thing this kernel was shown to care about. The open
question was how much table that buys, since the pairs multiply -- 3 pairs
is 53 KB, all 14 is 1.26 MB, against 21.5 KB today.

Answered by a differential ablation rather than by building it. The
existing table was spread over PAD times the memory by storing entry i at
index i*PAD: identical load count, identical access pattern, identical
RESULTS (every variant reproduced the frozen fingerprint) -- only the
footprint moves.

| table | ratio |
|-------|-------|
| 21.5 KB (PAD=1, production) | 1.000 |
| 86 KB (PAD=4) | **0.624** |
| 172 KB (PAD=8) | **0.142** |
| 1.38 MB (PAD=64) | **0.092** |

So the cliff is between 21.5 KB and 86 KB, and it is a cliff, not a slope:
7x by 172 KB. CRT pairing needs 53 KB for three pairs -- to save 3 loads of
28 -- and lands in it. **Rejected without implementation, on a measurement.**

Put beside the earlier result, the sieve is now pinned from both directions
and the two together are much sharper than either alone:

- at fixed footprint, address spread is free (0.993x confining a warp's 32
  lanes to a single 32-byte sector), so only load COUNT matters;
- at fixed load count, footprint is brutal past L1.

Which retires the whole family of "restructure the table" ideas: the folded
form went smaller and lost by adding a load (0.685x), CRT pairing removes
loads and loses on footprint, and shrinking further at constant load count
gains nothing because 21.5 KB is already resident. The sieve's pattern
table is at its optimum, and the remaining levers on that phase are the
ones that reduce work rather than rearrange it -- NINC (a measured interior
peak) and the wheel.

That leaves the **37# wheel** as the only unpriced item on the dominant
phase: 1.85x fewer candidates AND one fewer sieve prime, for a 5.99e8-entry
offset table (4.8 GB). Note it does not interact with the cliff above --
the offset table is streamed, not gathered.

### Split after this round

| phase | share | verdict |
|-------|-------|---------|
| bit-sieve stage 1a | 66.3% | pinned from both sides: at fixed footprint only load COUNT matters (divergence is free, 0.993x at one sector), and at fixed load count the footprint cliff starts before 86 KB (0.62x) and reaches 0.14x by 172 KB. The table is therefore at its optimum -- W=128 (0.25x), the folded form (0.685x) and CRT pairing each die on one side or the other. Only lever left on this phase: the 37# wheel |
| stage-1b compaction rounds | 26.4% | 1.048x from #15, round size re-swept to 24 (1.023x), grid insensitive |
| cold kernel (stage 2) | 7.4% | 3.1x from #13; two priced items left, both bounded by the share |
| host + syncs | 2.5% | measured; removing them is 0.995x |

Not done -- three of the four phases still have named levers with prices on
them.

---

## Phase 4 (2026-08-16): the per-thread term, and the 37# wheel priced out

The overnight leg validated the previous round in production: 6.1152e20 ->
1.0557e21 in 10.0 h, a realized **1.232e16 p/s** against the 1.33e16 the
paired 1.294x had projected -- 93%, so the benchmark ratio transferred.

Starting profile: sieve 66.3%, rounds 26.4%, cold 7.4%.  Only one lever was
left named on the dominant phase, so it got priced first.

### Pricing the 37# wheel without building it

The wheel is the classic candidate-count lever (section 2.8): folding 37 in
generates 37/(37-17) = 1.85x fewer candidates for an identical survivor set,
and removes a prime from the sieve.  The worry was memory -- 5.99e8 offsets,
4.8 GB -- but the real obstacle turned out to be somewhere else entirely, and
it was measurable in the CURRENT engine.

A 37x longer period means a launch covering the same p-line holds 37x fewer
periods, so each thread gets fewer periods to amortize its setup over.  How
much does that cost?  Fit it: force T down and measure the sieve alone.

| T | 192 | 256 | 640 | 1088 | 2176 |
|---|-----|-----|-----|------|------|
| sieve ms | 810.9 | 664.9 | 411.0 | 335.1 | 293.6 |

    sieve = 239 ms (pattern loop) + 109449/T ms (per-thread)

so the per-thread term is **17.4% of the sieve at T=2176** and 42% by T=640.
Combining that with the 1.85x candidate saving and the queue budget the
wheel would need (its s1a_rate rises to 1.76e-3, since the sieve loses 37 and
gains 173):

| queue per buffer | PPL | T | sieve | overall |
|---|---|---|---|---|
| 1.8 GB (today) | 178 | 192 | 1.511 | **0.75x** |
| 3 GB | 305 | 320 | 1.085 | **0.95x** |
| 8 GB | 813 | 832 | 0.692 | 1.27x |
| 16 GB | 1627 | 1664 | 0.569 | 1.41x |

The wheel is a LOSS at any queue we can afford and needs 32 GB of buffers
plus the 4.8 GB table to reach 1.41x.  **Rejected** -- and note the stated
reason is neither "4.8 GB is too big" (it is affordable) nor a projection,
but a fitted curve from the existing engine.

### What that measurement was actually worth

The same fit named a phase nobody had looked at: **per-thread setup, 17.4% of
the dominant kernel**.  Two things came out of attacking it.

| # | change | ratio | verdict |
|---|--------|-------|---------|
| 18 | **one y-slice**: T is derived from PPL, so raising the target 2048 -> 4096 makes gy 2 -> 1 at the production PPL, halving the thread count | **1.022x** | KEPT |
| 19 | **32-bit residue seeding** in the sieve (`_SIEVE_INIT32`), same split as `_R_MIX32`: only off mod q needs 64 bits, since the host passes k_base mod q and the thread adds its own kp0 + tb | **1.015x** | KEPT, gated (G15) |
| 20 | **32-bit reduction in cold stage 2** (`_S2_RED_MIX32`), the transformation left priced-but-unbuilt last round | **1.014x** | KEPT, gated (G15) |
| -- | **paired total vs bb72e2d, same process, 7 rounds** | **1.055x** | both reproduce the frozen fingerprint on identical work |

#18 is worth dwelling on.  A flat T sweep in the previous round had measured
T=4096 at 1.004x and moved on -- but that was before T became derived, so
T=4096 still produced gy=2 with a 132-period tail slice.  Once T is derived,
the same nominal value resolves to a single full slice and is worth 1.022x.
**The knob had not been tested; a differently-shaped knob with the same name
had been.**

Note also that #19 returned 1.015x where the Barrett count predicted ~4%.
That gap is informative: the per-thread term is mostly NOT arithmetic -- it is
thread setup and the offset load -- which is why #18 (halving the number of
threads) beat #19 (making each one cheaper), and which independently confirms
the wheel verdict above.

### A bug the fingerprint caught

#19's first version put the (k_base mod q) upload where it already lived --
after the sieve launch, since only stage 1b had needed it.  The sieve then
read the *previous* launch's table.  Count came back 183 against the frozen
178, i.e. it was under-killing, and the A/B refused to report a rate.  Two
minutes to find, and the discipline that caught it is the cheap one: the
fingerprint is checked on every run, not at the end.

### Constants, re-swept after all of the above

| constant | swept | result |
|----------|-------|--------|
| NINC | 26/28/30 | 0.992/**1.000**/0.996 -- still the interior peak |
| ROUND | 20/24/28 | 1.005/**1.000**/0.994 -- 20 and 24 are inside the noise floor, kept 24 |

The noise floor is now measured rather than assumed: T=3000 and T=4096
resolve to the *same* derived T=4288, and those two identical configurations
differed by 0.3% in the same battery.  So 0.5% gaps are not results and 1.4%
gaps are.

### Split after this round

| phase | share | verdict |
|-------|-------|---------|
| bit-sieve stage 1a | 66.6% | pattern loop is at 239 ms with the table pinned from both sides (see Phase 3); the per-thread term is now down to ~9% of the kernel and is mostly thread setup, not arithmetic. The wheel -- the only remaining candidate-count lever -- is priced out above |
| stage-1b compaction rounds | 27.4% | 32-bit reductions taken (Phase 3), round size re-swept, grid insensitive |
| cold kernel (stage 2) | 6.0% | 3.1x from the bit probe, 1.014x more from the 32-bit reduction. Compaction remains unbuilt, now bounded by a 6% phase |
| host + syncs | 2.2% | measured |

---

## Phase 5 (2026-08-16): what the sieve is actually bound by, and the phase nobody had baked

Re-measured split before touching anything (Rule 1): **65.8 / 28.0 / 6.3 / 1.3**,
close enough to the recorded 66.6/27.4/6.0/2.2 that no verdict was stale on
share alone.  Two of them were stale on *evidence*, which is worse.

### First: two experiments that told the sieve what it is not

The sieve's verdict said "bound by load COUNT", inherited from Phase 3's
gather-masking ablation.  Before spending anything on the dominant phase,
that got tested from both sides.

| experiment | result | what it rules out |
|---|---|---|
| **marched pattern table** -- store each prime's words in VISIT order, so the index sequence becomes stride-1 and the per-prime `r += dmw; if (r >= q) r -= q` disappears from the inner loop (dmw is invertible mod q, so `G[m] = pat[m*dmw mod q]` is exact; costs T/W-1 rows of tail padding) | **1.007x**, later 1.019x | removing ~2 of ~6 instructions per prime per pattern word bought nothing measurable, so the pattern loop is **not instruction-issue bound** |
| **gather-spread probe** -- `off = offs[i & ~m]`, so groups of lanes share an offset and therefore all 26 pattern addresses.  Load count, table footprint and the per-lane survivor density (hence extraction and push counts) are all unchanged; only distinct sectors per warp-load moves, 17.3 -> 1.0 | **1.53x at ONE sector**, and non-monotone in between (16 lanes 1.21x, 8 lanes 1.14x, 4 lanes 1.07x, 2 lanes 1.00x) | collapsing the gather 17x wins only 1.53x, so it is **not sector-throughput bound** either.  A warp-cooperative redesign that got 18 sectors down to 8 would be worth ~1.2x on the phase at best, against a much worse setup amortization -- **priced and declined** |

The marched table is kept (it is 1.019x against the same engine once the
other changes landed, with disjoint min/max across 7 interleaved rounds) but
the reason it matters is the negative result: it redirected the whole session
away from the sieve and onto the phase that had never been touched.

### The ledger

Interleaved medians over a steady-state 2e16 window at 6.11e20 (24 launches),
every run re-checking the frozen 128 fingerprint AND that the window's own
survivor list is identical.

| # | change | ratio | verdict |
|---|--------|-------|---------|
| 21 | **queue carries `off`, not its index**.  A stage-1a survivor is the pair (off, kp); the queue stored the offset's INDEX, so every compaction round and the cold kernel gathered `offs[i]` back out of a 240 MB table -- one scattered read per entry per round, for a value the sieve already had in a register.  Pack `off` itself, shifted by a KSHIFT derived from M and refused if a launch could overflow it | **1.058x** | KEPT |
| 22 | **baked stage-1b round kernels** (catalogue 2.5, applied to a phase that had never had it).  The round loop read six warp-uniform values per prime out of global arrays; five are properties of the prime, so they become literals and the loop is unrolled into one kernel per round | **1.084x** | KEPT |
| 23 | **32-bit `off mod q` in stage 1b**.  `off = oa*2^s + ob` with s derived so `oa*(2^s mod q) + ob < 2^32` for the widest prime in the stage; one `__umulhi` replaces `__umul64hi` plus a 64-bit multiply, subtract and two 64-bit conditional subtracts, with oa/ob computed once per candidate | **1.037x** on top | KEPT, gated (G15) |
| 24 | NINC re-sweep after (22): 22/24/26/28/30 -> 1.000/0.998/**1.020**/0.976/0.960 | **1.020x** | KEPT: NINC 28 -> 26 |
| 25 | ROUND re-sweep after (24): 8/12/16/20/24/34 -> 0.938/0.988/**1.000**/0.983/0.959/0.918 | **1.043x** | KEPT: ROUND 24 -> 16 |
| 26 | the same off-split in the cold kernel's stage 2 (its own s: those primes reach 65521, so the product has 64x less room) | **1.023x** | KEPT, gated (G15) |
| 27 | marched pattern table (above) | **1.019x** | KEPT |
| 28 | sieve `__launch_bounds__` 3 -> 2 blocks/SM: 2/3/4/0 -> 1.000/0.990/0.972/0.995 | **1.010x** | KEPT.  The optimum tracks register demand, and NINC 28 -> 26 freed two live residues |
| -- | **paired total, HEAD engine vs this one, same process, 7 rounds** | **1.3293x** | both reproduce both frozen fingerprints on identical work |

Here the product of the rows (1.332) and the paired figure (1.329) agree to
0.2%, unlike Phase 3 where they diverged by 6% -- these changes touch
different phases and barely overlap.  Quote the paired one anyway: agreement
is a property of this particular set, not a licence to multiply.

Both re-sweeps moved **down**, and both for the same reason: (22) and (23)
made a stage-1b prime 2.4x cheaper, so handing work back to stage 1b became
the better trade.  That is Rule 1's corollary for the fifth time in this
project, and it is worth 1.06x on its own -- pure loss if nobody re-sweeps.

### Offset chunking: an enabler, deliberately neutral

`QUEUE_BUDGET` used to cap **PPL**, which made the launch's *period count* a
function of the memory budget.  Since T is derived from PPL, that is what
priced the 37# wheel at 0.75x in Phase 4: a longer period leaves each thread
too few periods to amortize its setup over.  The coupling was never
necessary.  A launch is now cut along the **offset** axis instead -- each
chunk runs its own sieve -> rounds -> cold chain over the launch's whole
period range, with its own stage-1a counter -- so PPL is set purely by
LAUNCH_SPAN and the queue is bounded by how many offsets are in flight.

At the production wheel this resolves to exactly one chunk, so it is a
no-op by construction, which is the point: it is gated (G13 now sweeps chunk
sizes down to 4093 -- 7,300 chains for a single window -- and requires one
identical stream) before anything depends on it.

### The 37# wheel: re-priced, and the verdict inverted

Phase 4 declined the next wheel at **0.75x**, from a fitted `sieve = a + b/T`
curve, because the queue budget forced PPL down and T with it.  With
chunking that constraint is gone, so the same technique was re-run on the
axis that actually moves now -- the WINDOW size.  Sweeping the window in the
current engine and timing the sieve alone:

| periods | 67 | 134 | 268 | 623 | 1246 | 2493 | 4228 |
|---|---|---|---|---|---|---|---|
| pattern words per thread | 2 | 3 | 5 | 10 | 20 | 39 | 67 |
| ms per 1e9 sieve threads | 78.3 | 106.5 | 159.6 | 225.6 | 444.1 | 858.0 | 1444.1 |

    f(words) = 36.3 + 21.0*words        (per-thread setup is 2.5% at 67 words)

Repeated on a second battery: `f = 31.5 + 21.5*words`, 2.1% -- the intercept
is the noisy term, as it should be at 2.5% of the total, and neither fit
changes a conclusion below.

The 37# wheel has 20x the offsets and 37x the period, so its cost against
the 31# wheel is `20 * f(w37) / (launches * f(w31))`:

| window | 31# | 37# | 37# sieve cost |
|---|---|---|---|
| production / steady-state (many full launches) | 24 launches x 67 words | 1 x 43 | **0.54x -- a 1.85x WIN** |
| the frozen 5e14 benchmark shape | 1 launch x 39 words | 1 x **2** | **1.7-1.8x -- a 0.55-0.58x loss** |

So the Phase-4 verdict is inverted: at production shape the wheel is
**1.85x on a phase that is 78% of GPU time**, i.e. ~1.5x overall, and the
blocker is no longer the engine at all.  It is the **benchmark shape**: a
5e14 window holds 2,494 periods of the 31# wheel but only 68 of the 37#
wheel, which is two pattern words per thread against 20x as many threads, so
95% of a thread's work there would be prologue and block padding.

**Not shipped.**  This repo optimizes under the score, and a change that
raises production throughput ~1.5x while halving SCORE is not something an
engine should decide for itself -- the frozen shapes are the cross-generation
anchor and amending one is a human call.  What has changed is that the item
now has a measured price on both sides and a named blocker, instead of a
model-based "it is a loss".  If the frozen windows are ever re-cut wide
enough to hold a few thousand periods of the wider wheel, this is the single
biggest item left in the project.

### Re-derived, not inherited

| item | Phase 2/3 verdict | re-measured now | verdict |
|------|-------------------|-----------------|---------|
| the sieve's queue push | "the whole push is 10% of the sieve", so no warp aggregation | **11.8%** (register-counter ablation, extraction and __ffsll chain untouched).  It grew because NINC 28 -> 26 multiplies the queue by 1.24 | still declined, now on a current number: ~2.2 survivors per warp-block, so aggregating 2.2 atomics into 1 plus ballot/popc/prefix is roughly break-even |
| pattern width W=128 | 0.252x | **0.188x** | REJECTED again, at a completely different profile |
| bigger launches | 1.009x | flat (PPL 4228/8456/16912 -> 1.000/0.998/0.998) | no lever |
| T | flat | flat (2048/4096/8192 -> 1.000/1.007/1.009; the last two derive the same T=4288, which re-measures the noise floor at 0.2%) | no lever |

### Measured and NOT kept

Both of these are the same finding twice, and it is the useful one: the
sieve does not care about arithmetic.

| attempt | ratio | why it was tempting |
|---------|-------|---------------------|
| the off-split applied to the sieve's residue SEEDING as well (the last 64-bit multiply in the prologue) | **1.006x** -- inside the noise floor | it is the identical transformation that paid 1.037x in stage 1b and 1.023x in stage 2.  It does not pay here because the prologue is now 2.1% of the kernel, and Phase 4 had already shown that term is thread setup rather than arithmetic |
| building the extraction loop's edge mask under a (warp-uniform, almost always false) branch instead of on every pattern word | **0.9985x** | ~6 unconditional ALU ops per word against ~100 in the pattern loop.  Removed again: a neutral variant is a code path with no measurement behind it |

### One more idea for the sieve, and the number that killed it

If a 64-period block is already entirely killed, the remaining primes' ORs
cannot change it -- and blocks saturate fast: 13% are dead after 8 sieve
primes, 47% after 12, 90% after 24.  Guarding each OR with
`if (acc[0] != ~0ULL)` is an exact identity (the fingerprint reproduces) and
would cut the expected load count from 26 to **14.4**.

| guarded from prime | 0 (all 26) | 4 | 8 | 12 | none |
|---|---|---|---|---|---|
| ratio | **0.818** | 0.862 | 0.901 | 0.944 | 1.000 |

Monotone in the number of guards at ~1.3% each, with **no** credit for the
loads skipped.  So the guard is a branch, the branch is taken whenever ANY
lane of the warp is still alive (which is essentially always), and the loads
are not skipped at the warp level at all -- while the branch itself costs far
more than the ALU ops this session has shown the sieve to ignore.

Put together with the two probes above, the dominant phase is now
characterised rather than merely labelled:

- **ALU is free.** Three separate reductions in per-word or per-thread
  arithmetic measured 1.007x, 1.006x and 0.999x.
- **Branches are not.** ~1.3% each, per prime per pattern word.
- **Sectors are about half of it.** Collapsing 17.3 sectors per warp-load to
  1.0 is worth 1.53x, about what you would expect if half the kernel is L1
  sector work and the rest is issue and latency.  A warp-cooperative layout
  (one offset per warp, lanes on consecutive pattern words) would reach ~8.5
  sectors, worth ~1.33x on that half -- but it pays 32 redundant prologues
  per offset, +8% at the current 2.5% prologue share, netting **~1.1-1.2x for
  a full kernel rewrite**.  Priced, declined, and the number is soft because
  the probe was non-monotone.
- **Load COUNT is the binding term**, and the only lever that reduces it
  without touching anything else is generating fewer candidates.

Which is the wheel, priced above at 1.85x and blocked by the benchmark shape.

### Constants, re-swept after all of the above

| constant | swept | result |
|----------|-------|--------|
| NINC | 22/24/26/28/30 | 1.000/0.998/**1.020**/0.976/0.960 -- moved 28 -> 26 |
| ROUND | 8/12/16/20/24/34 | 0.938/0.988/**1.000**/0.983/0.959/0.918 -- moved 24 -> 16 |
| sieve launch bound | 2/3/4/0 | **1.000**/0.990/0.972/0.995 -- moved 3 -> 2 |
| T | 2048/4096/8192 | 1.000/1.007/1.009 -- flat (4096 and 8192 derive the SAME T=4288, so their 0.2% gap re-measures the noise floor) |
| PPL | 4228/8456/16912 | **1.000**/0.998/0.998 -- flat; chunking makes bigger launches affordable and they buy nothing |
| ROUND_GRID / COLD_GRID | 1024/4096/16384 | 0.999/**1.000**/0.999 -- the grid-stride loops still do not care |
| block size | 128/256/512 | 0.988/**1.000**/0.956 -- 256 stands.  Never swept in this generation, and it could not have been swept safely before: the block size is baked into the sieve's `__launch_bounds__`, so it is now taken from the same snapshot the launcher uses rather than being a literal that a knob could desync |

The block sweep is also a Rule 3 cautionary tale in miniature.  Its first run
reported **block512 at 1.068x** -- a 7% win that does not exist.  The machine
changed regime a third of the way through (every configuration's minimum was
~0.86 s against medians of ~1.30 s), so the median mixed two populations.
Re-run over 9 rounds, the last five are internally consistent and put 512 at
0.956x.  Interleaving is necessary but not sufficient: check that the spread
within a configuration is small before believing the spread between them.

### The gate battery: 9m51s -> 1m33s, and Rule 1 again

Not an engine change, but it gates every engine change, so it belongs here.

I was asked to speed the battery up and produced three plausible candidates
by reading the code -- memoize `build_wheel`, fix G10's pure-Python
enumeration loop, parallelise the CPU gates.  Timing each gate individually
took two minutes and showed all three were nearly irrelevant:

| gate | wall | share |
|---|---|---|
| **G6 GPU vs CPU parity** | **525.7 s** | **89.0%** |
| G13 slicing independence | 37.4 s | 6.3% |
| everything else combined | 27.5 s | 4.7% |

G10, one of my three, is 2.0 s -- 0.3% of the battery.  This is the same
error the Phase-1 review made about the cold path and the same one Rule 5a
describes: an unmeasured review is a hypothesis list, and mine was
mis-ranked in a way that two minutes of measurement fixed.

G6 sweeps seven windows with the numpy reference, which is single-threaded
*by design* and may not be optimized -- its slowness and its independence are
what the parity gate measures.  So the parallelism went **outside** it: the
seven cases are cut into 24 contiguous sub-windows, swept one process per
sub-window, while the parent runs the GPU sweeps concurrently.
`euler_search.py`'s engine is untouched.  G6: **525.7 -> 75.8 s (6.9x)**.

The gate got *stronger* in passing.  The reference now arrives as a
concatenation of sub-windows while the GPU still sweeps each window unsplit,
so a boundary bug on either side breaks it -- which unsplit-vs-unsplit could
not catch.  Every reported coverage count is unchanged, which is the
invariant to check when making a gate faster: sizes [29,2,1,1,2,1,2], G13's
384 comparisons over 105,460+4,297 survivors, G14's 2,080 checks, G15's
161+6,370 primes.

`build_wheel` was memoized as well (a pure function that builds and sorts up
to a 4e7-element array, called forty-odd times per battery; the cached array
is marked read-only so a mutating caller fails loudly).  Worth a few percent,
which is roughly what the measurement predicted and nothing like what my
guess did.

### Split after this round

| phase | share | verdict |
|-------|-------|---------|
| bit-sieve stage 1a | 78.2% | Phase 3's "bound by load COUNT" attacked from three sides and still standing: **ALU is free** (1.007x / 1.006x / 0.999x from three separate arithmetic reductions), **sectors are ~half of it** (17.3 -> 1.0 buys 1.53x; a warp-cooperative rewrite reaching ~8.5 nets ~1.1-1.2x after its 32x redundant prologues -- priced, declined), and **skipping the redundant loads is impossible** (a saturation guard is a branch, taken whenever any lane is alive: 0.818x).  Table still pinned from both sides (W=128 0.188x, folded form 0.685x, CRT pairing dead on the footprint cliff).  Queue push re-priced at 11.8%, still break-even to aggregate.  One lever removes loads -- the wheel: **1.85x, blocked by the benchmark shape**, priced above |
| stage-1b compaction rounds | 15.9% | was 28.0%.  Baked per-prime literals (1.084x) and the 32-bit off-split (1.037x) cut it 2.39x, then NINC and ROUND both moved DOWN in response (1.020x, 1.043x) |
| cold kernel (stage 2) | 5.9% | 32-bit off-split with its own split point (1.023x).  Compaction still unbuilt, still bounded by a 6% phase |
| host + syncs | 1.8% | the round counters went into one array zeroed once per chain instead of one fill per round, which took host time back from 4.7% to 1.8% after ROUND 24 -> 16 tripled the round count |

Three of the four rows still carry named levers with prices on them.

## Phase 6a (2026-08-16): a third frozen benchmark shape

Not an engine change -- **zero lines of engine touched, and that is the
point.**  Phase 5 ended with the biggest remaining lever (the 37# wheel,
1.85x on 78% of GPU time) declined for a reason that was not about the
engine: the frozen 5e14 shape can no longer resolve it, and this repo
optimizes under the score.  ../OPTIMIZATION.md 2.13 says what to do about
that -- price both sides, name the shape as the blocker, and leave the
decision to a human, because the anchor that makes scores comparable across
engine generations is not something an optimization pass gets to amend.

The decision came back as **add a shape, never amend one**, which is the
resolution that keeps both properties:

| shape | window | 31# periods | 37# periods | role |
|-------|--------|-------------|-------------|------|
| `SCORE` | [1e16, +5e14) | 2,494 | 68 | cross-generation anchor, frozen from the retired u64 kernel |
| `SCORE128` | [2.3e20, +5e14) | 2,494 | 68 | cross-generation anchor, frozen from the retired first-128 path |
| `SCORE_WIDE` | [6.11e20, +2e16) | 99,720 | **2,696** | resolves the wheel; production-shaped |

`BENCH_LO/BENCH_SPAN/FINGERPRINT_*` and the `128` pair are byte-for-byte
unchanged and both still reproduce -- verified in the same battery that froze
the new one.  All three are checked on every run; a mismatch on any of them
still scores 0.

Why this window and not another:

- **24 launches** at the current PPL, so it cannot be flattered by a launch
  size collapsing the whole window into one launch (Rule 4, which is exactly
  how the old 18.31x turned out to be a 14x).
- It is the window Phase 5's A/B sweeps already ran on -- every ratio in that
  ledger was measured here, with its survivor list checked run to run -- so it
  arrives with a track record rather than as a fresh unknown.
- **2,696 periods of the 37# wheel**, the same order as the 2,494 the older
  shapes hold of the 31# wheel, so it resolves the next wheel as well as they
  resolved the last one.
- In the a(19) hunt's own zone, so it is production-shaped, not synthetic.

Frozen on a green tree: 13 gates, **6,996 survivors / checksum
71330844491704598**.  Same battery: SCORE 16,307,051,103 / SCORE128
16,325,330,842 / SCORE_WIDE 16,662,037,996 -- the three within 2.2%.

I nearly wrote that down as "the tightest same-code spread this machine has
produced".  The next battery, same code, same session, minutes later, read
20,917,761,353 / 25,643,824,896 / 19,283,048,101 -- a **33% spread**.  So the
2.2% was a capture, not a measurement, which is the identical error
BENCHMARKS.md already carries a correction for ("flat to 0.01%" was one lucky
capture quoted as precision).  It is worth recording that the trap caught me
inside the same file that documents it: absolute scores on this machine are
for the ledger and the fingerprint check, and **nothing** may be concluded
from arithmetic across them.  Ratios come from interleaved pairs.

`score.py`'s three benchmark functions now share one `_bench(lo, span, runs)`
body.  Three copies of a timing loop that could drift apart is three shapes
that could be timed differently, which is a way to game one of them.

**What this unblocks, and what it does not.**  It makes the 37# wheel
measurable.  It does not make it a win -- that still has to be shown, on this
shape and on a paired interleaved A/B at production shape.  And `SCORE` and
`SCORE128` are *expected* to fall ~0.6x if the wheel lands: that is the
granularity effect above, priced in advance, and it is why the prediction is
recorded here before the measurement rather than after it.
