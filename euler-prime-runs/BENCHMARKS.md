# BENCHMARKS -- euler-prime-runs

SCORE convention: `python score.py` prints SCORE = end-to-end Mp/s on
the frozen benchmark shape, ONLY if all gates are green and the work
fingerprint (survivor count 178, xor checksum 120489734542316 on
[1e16, 1e16+5e14)) reproduces exactly. Skipped work scores 0.

| date | engine | SCORE | notes |
|------|--------|-------|-------|
| 2026-08-05 | v1 baseline | 44,550,000 (est.) | pre-score.py measurement, 4.46e13 p/s |
| 2026-08-05 | v3 (frozen) | 189,738,385 | Barrett + 29# wheel + 2D grid + L2 masks |
| 2026-08-06 | v4 | 343,361,199 | multi-period threads + incremental first-16 stage-1 residues; measured under ambient desktop GPU load (see variance note) |
| 2026-08-06 | v4 (re-frozen, idle GPU) | **512,819,184** | same engine, quiet-GPU capture; matches the 9-hour production average (~5.0e14 p/s) and interleaved harness runs (5.12e14) |
| 2026-08-06 | v1-128 | 248,019,330 | phase-2 128-bit path, one-kernel design, window [2.3e20, +5e14), fingerprint 178 survivors / checksum 133625321009290; captured under desktop load (u64 SCORE read 323,531,367 in the same battery). Paired A/B: 0.77x the u64 kernel |
| 2026-08-06 | v2-128 (frozen) | **362,319,437** | two-phase compaction (stage-1a hot kernel + queued cold kernel; see OPTIMIZATION_LOG). Same fingerprint, bit-identical stream. Same-battery pair: SCORE128 362,319,437 vs u64 SCORE 323,394,817 -- **the 128 path is now 1.13x the proven u64 engine** (paired A/B median 1.135, min 1.111 over 12 rounds) |
| 2026-08-15 | v3-128 (frozen) | **6,341,803,579** | bit-sieve stage 1a + stage-1b compaction rounds; NINC=24, ROUND=8, W=64, PPL=131072. Same fingerprint (178 / 133625321009290), bit-identical stream (G13, G14). Full battery green; same-battery u64 SCORE 305,864,144, so the 128 path is now **20.7x the u64 engine**. Shape note: SCORE128 takes the engine's default launch size, raised 8192 -> 131072, so the 77,285-period window is now ONE launch (see score.py header) |

Decomposing that ledger jump, one battery, all three points measured
back to back with the fingerprint checked every run:

| config | p/s | SCORE128 | vs v2 |
|--------|-----|----------|-------|
| v2-128, ppl=8192 | 3.4649e14 | 346,492,141 | 1.00x |
| v3-128, ppl=8192 (same shape) | 3.5652e15 | 3,565,160,182 | **10.29x** |
| v3-128, ppl=131072 (production default) | 6.3456e15 | 6,345,583,830 | **18.31x** |

So **10.29x is the engine change** at an unchanged launch shape, and the
rest comes from the bigger launch. The 1.78x that the launch size is
worth *here* flatters it: the frozen window is 77,285 periods, which at
ppl=131072 collapses to a single launch. Measured in steady state over
[2.3e20, +2e15), where every config does several launches, the same
change is worth 1.395x. The honest sustained figure is therefore
**~14x** (10.29 x 1.395), and 18.31x is a benchmark-window artifact.

## Phase 2 v3-128 (2026-08-15): the bit-sieve

Tuning is all measured, always as an interleaved paired ratio with the
frozen fingerprint re-checked on every single run (a sequential sweep on
this machine produced a 31% "cliff" that does not exist — see
OPTIMIZATION_LOG.md). Ratios, each from one battery:

| change | ratio | note |
|--------|-------|------|
| bit-sieve stage 1a replaces per-candidate testing | **4.47x** | hot kernel 1103.6 -> 45.7 ms; split flips to 16/83 hot/cold |
| launch size 8192 -> 131072 periods | **1.395x** | steady-state, 38 -> 3 launches, identical streams |
| stage-1b compaction rounds, R=8 | **1.684x** | R = 0/4/8/16/32 -> 1.000/1.568/1.684/1.638/1.531 |
| sieve depth NINC 28 -> 24 | **1.058x** | the optimum moved once rounds made the cold path cheaper |

Rejected on measurement: pattern width W=128 / W=256 (0.252x / 0.314x),
warp-aggregated queue atomics (the whole queue push is 10% of the sieve),
removing the per-launch host syncs (0.2% of GPU time), splitting stage 2
into its own compacted kernel (no divergence to recover: <= 1 lane per
warp is ever in it).

Phase split after tuning (NINC=24, ROUND=8, W=64, PPL=131072): bit-sieve
stage 1a 64.3%, compaction rounds 17.3%, cold stage-2 kernel 18.4%.

**Fingerprints are unchanged**, which is the whole claim: 178 survivors /
checksum 133625321009290 on [2.3e20, +5e14) still reproduce bit-for-bit,
so the engine got faster without the work changing. Cross-generation
comparisons quote the paired ratio because absolute rates on this machine
move up to ~30% with ambient desktop load (variance note below).

Wall-clock at SCORE (n=17 production, v4, idle GPU):

| depth | time |
|-------|------|
| 1e16  | ~20 s |
| 1e17  | ~3.2 min |
| 1e18  | ~33 min |
| 1.8e19 (u64 cap) | ~9.7 h |

Height-flatness: 1e16 / 1e18 / 1.7e19 windows agree within 0.8%.

Model milestones at this rate: E(a17)=1 at 2.6e17 (~8 min in),
P(a17) = 88% by ~33 min, ~100% by cap; P(a18) = 78% by cap.

Phase-2 wall-clock (v2-128, from the 1.8e19 cap): the leg-1 depth
3.2e20 -- past the Waldvogel-Leikauf zone and the run>=19 E=1 point --
was projected at ~6.1 days at the idle 5.7e14 p/s and completed
2026-08-14 in 152.1 h (~6.3 days), a realized production average of
5.5e14 p/s across the whole leg.

Phase-2 wall-clock (v3-128, from the 3.62e20 frontier). **Measured, not
projected**: a production run of [3.6004e20, 3.62e20) on 2026-08-15
reported 76.0-79.2e14 p/s across eight steady-state heartbeats, median
**7.76e15 p/s** -- 14.1x the 5.5e14 the v2 engine averaged over leg 1,
and 98% of the 7.9e15 predicted from the paired benchmark ratio. The
sustained decomposition above therefore holds in production.

| target | P(a(19) by then) | v3 | was (v2) |
|--------|------------------|----|----------|
| 5.40e20 (a19 Q1) | 25% | 6 h | 3.7 days |
| 8.37e20 (a19 median) | 50% | **17 h** | 10.0 days |
| 1e21 | 59% | 0.95 days | 13.5 days |
| 1.46e21 (a19 Q3) | 75% | 1.6 days | 23.0 days |
| 2e21 | 85% | 2.4 days | 34.5 days |
| 5e21 (leg cap) | 98% | **6.9 days** | 97.6 days |

For scale: re-sweeping the entire range from 0 to 5e21 now costs ~7.5
days, and the engine's enforced 1e24 ceiling is ~4 years of single-GPU
wall (it was ~58 years).

Note (2026-08-06): after the public-repo refactor (shared code moved to
../huntlib), the full gate battery re-ran green and the benchmark
fingerprint (survivors 178, checksum 120489734542316) reproduced
exactly. The timing measured during that verification (9.8e13 p/s) was
taken while a production hunt shared the GPU and is not a SCORE entry;
the frozen SCORE stands from the uncontended pre-hunt measurement.

Variance note (2026-08-06): the same frozen v4 benchmark shape
measured 3.43e14, 3.47e14, 4.67e14, and 5.13e14 across one day on one
machine -- concurrent desktop/display GPU activity fluctuates minute
to minute and can shave up to ~30% off the CUDA rate (the frozen v3
engine showed the identical discount: 1.36e14 measured under load vs
its 1.90e14 idle SCORE). Call-shape and height effects were ruled out
by interleaved A/B (aligned production segments at 2e18 vs the bench
window at 1e16 agree to 0.1%). The re-frozen SCORE above is the
idle-GPU capture, cross-confirmed by the phase-1 production sweep
itself: 1.6e19 of p-line in ~9 hours end-to-end. Idle-GPU speedup
over frozen v3: 2.70x (loaded same-day A/B: 2.5x).
