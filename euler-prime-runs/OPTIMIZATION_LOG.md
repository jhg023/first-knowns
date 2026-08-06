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

Frozen at v3: **1.90e14 p/s median** (SCORE 189,738,385). Height-flat
(1.708e14 at 1e18 pre-v3 check; fingerprint window 1e16).

Cost accounting at v3: ~5.9e10 candidates/s of wheel survivors
(3.1e-4 of p-space), ~2.5 expected stage-1 Barrett tests per
candidate before kill. Host-side MR load is negligible (~3.6e-13 of
p-space reaches MR; ~6.5k survivors per 1.8e19).

## TODOs (unpriced, try only with gates green)

- Multi-period threads with incremental residues (r += M mod q per
  period, conditional subtract): amortizes offset load + first Barrett;
  needs register budget for ~170 stage-1 residues -> likely a partial
  (first-16-primes) variant. Expected <= 1.5x.
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
