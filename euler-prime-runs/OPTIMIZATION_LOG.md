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

Frozen at v4: **3.43e14 p/s median** (SCORE 343,361,199). Height-flat
(3.40e14 at 1e18, 3.43e14 at 1.7e19; fingerprint window 1e16).

Note on the v4 ratio: interleaved same-day A/B gave v3 = 1.36e14 and
v4 = 3.42e14 (2.5x) under identical ambient desktop GPU load; the
frozen v3 SCORE (1.90e14) was taken uncontended, so the ledger ratio
(1.8x) understates the kernel change. The v4 SCORE above was recorded
under the ambient load and is, if anything, conservative: the
restarted production hunt sustained 5.0e14 p/s at p ~ 2e18 during a
quiet-desktop window (~2.6x uncontended v3), matching the v3
contention discount (1.36/1.90 = 0.72) applied in reverse. A
same-night re-freeze attempt (hunt stopped, full battery green)
reproduced 3.44e14 with the desktop workload active -- the discount
is display contention, not drift; the frozen entry stands as the
loaded-desktop floor.

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
MR load is negligible (~3.6e-13 of p-space reaches MR; ~6.5k survivors
per 1.8e19).

## TODOs (unpriced, try only with gates green)

- Sort stage-1 primes by measured kill rate instead of ascending q
  (near-identical ordering; expected ~1%).
- Persistent-kernel + device-side segment loop to cut launch overhead
  (launches are 8192 periods = 5.3e13 p; overhead already amortized;
  expected small).
- Batch MR on GPU (Montgomery 64-bit): only relevant if Q2 is lowered
  or a wider survivor stream is wanted (e.g. n=16 census mode).
- 128-bit value path for p > 1.8e19 (phase 2 -- a(19)/a(20) tails and
  the Waldvogel-Leikauf zone at 2.3e20). Requires new G6 ceiling
  windows and a 128-bit MR (or 3-limb) host path.
