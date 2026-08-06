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
