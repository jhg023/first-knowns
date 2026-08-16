# BENCHMARKS -- euler-prime-runs

SCORE convention: `python score.py` prints SCORE = end-to-end Mp/s on
the frozen benchmark shape, ONLY if all gates are green and the work
fingerprint (survivor count 178, xor checksum 120489734542316 on
[1e16, 1e16+5e14)) reproduces exactly. Skipped work scores 0.

**Engine unification (2026-08-15).** There is now one production engine
spanning the whole range, so BOTH frozen shapes are measured with it:
SCORE on the low window [1e16, +5e14) and SCORE128 on the high window
[2.3e20, +5e14). The workloads and both fingerprints are unchanged --
only the engine being measured changed.  The low window's fingerprint was
frozen from the u64-only kernel, since retired, so reproducing it IS the
standing proof that the current engine still agrees with it there. Ledger rows dated before 2026-08-15 measured the u64-only kernel
on the low shape and are kept as history; do not read them as the same
quantity as current SCORE values.

A side effect worth *less* than it first appeared: the two shapes are the
same span swept by the same engine four orders of magnitude apart, so SCORE
vs SCORE128 looks like a **height-flatness measurement**.  It is, but only
to the precision this machine can resolve, which is poor.  Captures of the
same code on the same shapes:

| SCORE (1e16) | SCORE128 (2.3e20) | gap |
|--------------|-------------------|-----|
| 6.716e15 | 6.715e15 | 0.01% |
| 6.331e15 | 6.545e15 | 3.4% |
| 1.044e16 | 1.062e16 | 1.7% |
| 7.674e15 | 1.252e16 | 63% (harness artifact, fixed -- see below) |
| 7.694e15 | 8.253e15 | 7.3% |

Run-to-run variance on ONE configuration spans 6.5e15 to 1.25e16, which is
larger than any gap in the table, so **these numbers do not resolve a height
effect at all** -- they are consistent with flat and could not detect a 20%
tilt.  The earlier claim of "flat to 0.01%" was a single lucky capture quoted
as precision.  The u64 engine's height-flatness (0.8% across three heights)
was established differently, by interleaved A/B on one engine.

The 63% outlier was a real defect in the harness, not load: the warmup swept
a token 1e12 window, so the engine's multi-GB queue allocation landed inside
the *timed* region of whichever benchmark ran first, while the second found
the blocks already pooled.  The warmup now covers the measured window.  The
work and both fingerprints are unchanged; only an allocation moved out of the
stopwatch.

| date | engine | SCORE | notes |
|------|--------|-------|-------|
| 2026-08-05 | v1 baseline | 44,550,000 (est.) | pre-score.py measurement, 4.46e13 p/s |
| 2026-08-05 | v3 (frozen) | 189,738,385 | Barrett + 29# wheel + 2D grid + L2 masks |
| 2026-08-06 | v4 | 343,361,199 | multi-period threads + incremental first-16 stage-1 residues; measured under ambient desktop GPU load (see variance note) |
| 2026-08-06 | v4 (re-frozen, idle GPU) | **512,819,184** | same engine, quiet-GPU capture; matches the 9-hour production average (~5.0e14 p/s) and interleaved harness runs (5.12e14) |
| 2026-08-06 | v1-128 | 248,019,330 | phase-2 128-bit path, one-kernel design, window [2.3e20, +5e14), fingerprint 178 survivors / checksum 133625321009290; captured under desktop load (u64 SCORE read 323,531,367 in the same battery). Paired A/B: 0.77x the u64 kernel |
| 2026-08-06 | v2-128 (frozen) | **362,319,437** | two-phase compaction (stage-1a hot kernel + queued cold kernel; see OPTIMIZATION_LOG). Same fingerprint, bit-identical stream. Same-battery pair: SCORE128 362,319,437 vs u64 SCORE 323,394,817 -- **the 128 path is now 1.13x the proven u64 engine** (paired A/B median 1.135, min 1.111 over 12 rounds) |
| 2026-08-15 | v4: 31# wheel, sieve depth 28, round size 16 | SCORE **7,694,248,260** / SCORE128 **8,252,670,019** | folding 31 into the wheel: 2.07x fewer candidates for an identical survivor set, both frozen fingerprints reproduced, 12 gates green. **The load-bearing number is the paired ratio 1.374x, not any comparison of these absolutes against the rows below** -- run-to-run variance here is ~2x on identical code (see the table above), so cross-row absolute arithmetic is exactly what Rule 3 in ../OPTIMIZATION.md warns against. Composition: the wheel alone was 1.121x, sieve depth re-swept 24 -> 28 took it to 1.212x, and the round size then had to move 8 -> 16 for a further 1.134x |
| 2026-08-16 | v6: one grid slice, 32-bit residue seeding, 32-bit stage-2 reduction | SCORE **11,327,935,354** / SCORE128 **10,308,201,234** | 13 gates green, both frozen fingerprints reproduced. **The load-bearing number is the paired ratio 1.055x** against the row below it, measured in one process over 7 interleaved rounds. Composition: 1.022 x 1.015 x 1.014. Note SCORE and SCORE128 differ by 9.9% here on identical code, which is the variance note at the top of this file doing its job -- do not read it as a height effect |
| 2026-08-15 | v3-128, single-engine tree | SCORE **6,330,661,788** / SCORE128 **6,544,948,396** | retired engines deleted; both frozen shapes now measured with the one production engine, both fingerprints reproduced, 12 gates green. Engine mathematics identical to the row below -- this row differs only in what the tree contains and which engine the SCORE column refers to |
| 2026-08-16 | v5: stage-2 bit probe, balanced sieve grid, 32-bit stage-1b reductions, launch bound 3, round size 24 | SCORE **9,961,108,420** / SCORE128 **10,302,529,513** | 13 gates green (G15 new), both frozen fingerprints reproduced. **The load-bearing number is the paired ratio 1.294x** measured in one process against the engine this row replaces, not any arithmetic across these absolutes -- run-to-run variance here is ~2x on identical code. Composition: 1.165 x 1.066 x 1.048 x 1.028 x 1.023, none of them individually interesting |
| 2026-08-16 | v7: value-form queue, baked stage-1b round kernels, 32-bit off-split in stages 1b and 2, marched pattern table, offset chunking; NINC 26, ROUND 16, launch bound 2 | SCORE **13,198,517,241** / SCORE128 **13,433,035,057** | 13 gates green (G13 extended to the offset axis, G15 to the off-split and the stage-1b bitset), both frozen fingerprints reproduced. **The load-bearing number is the paired ratio 1.3293x** against the row above, measured in one process over 7 interleaved rounds on a steady-state 2e16 window, not any arithmetic across these absolutes. Composition: 1.084 x 1.058 x 1.043 x 1.037 x 1.023 x 1.020 x 1.019 x 1.010. An earlier battery on the same engine modulo two changes since measured neutral and reverted read SCORE **15,425,906,583** / SCORE128 **13,497,010,536** -- a 17% swing on the low shape and 0.5% on the high one, which is the variance note at the top of this file doing its job |
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
this machine produced a 31% "cliff" that does not exist -- see
OPTIMIZATION_LOG.md). Ratios, each from one battery:

| change | ratio | note |
|--------|-------|------|
| 31# wheel + sieve depth 24 -> 28 + round size 8 -> 16 | **1.374x** | 2.07x fewer candidates for an identical survivor set. Only 1.121x on the wheel alone: folding 31 into the wheel takes it OUT of the sieve, costing the sieve its strongest killer (31 kills 52% of candidates, its replacement 149 only 11%), so the queue per unit p-line grew 1.41x until the depth came back up. The round size then moved because the wheel shifted work into stage 1b, 17% -> 35% of GPU time |
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

v4 applies the measured 1.374x ratio to that 7.76e15, projecting
**1.07e16 p/s**; to be replaced by a realized average once the leg runs.

| target | P(a(19) by then) | v4 (proj.) | v3 (measured) | leg-1 engine |
|--------|------------------|-----------|---------------|--------------|
| 5.40e20 (a19 Q1) | 25% | 4.6 h | 6 h | 3.7 days |
| 8.37e20 (a19 median) | 50% | **12.4 h** | 17 h | 10.0 days |
| 1e21 | 59% | 0.69 days | 0.95 days | 13.5 days |
| 1.46e21 (a19 Q3) | 75% | 1.19 days | 1.6 days | 23.0 days |
| 2e21 | 85% | 1.78 days | 2.4 days | 34.5 days |
| 5e21 (leg cap) | 98% | **5.0 days** | 6.9 days | 97.6 days |

Cumulative **19.4x** over the engine that swept leg 1 (5.5e14 -> 1.07e16).
For scale: re-sweeping the entire range from 0 to 5e21 now costs ~5.4
days, and the enforced 1e24 ceiling is ~3.0 years of single-GPU wall (it
was ~58 years).

## Phase 3 (2026-08-16): the cheap tests

Same discipline: interleaved paired ratios, frozen fingerprint re-checked on
every run, measured on a steady-state 2e16 window at 6.1e20 (24 launches, so
no single-launch flattery). Ratios, all from one battery:

| change | ratio | note |
|--------|-------|------|
| stage-2 kill test: 17-iteration scan -> one bit probe | **1.165x** | every stage-2 prime exceeds max(x^2+x), so "q divides some p+x^2+x" is just "p mod q == 0, or q - p mod q is of the form x^2+x". Cold kernel 170 -> 55 ms |
| sieve grid balance: T derived from PPL | **1.066x** | the y-slices were 2048/2048/**132**, and per-thread setup is paid in full by every slice however short. Derived rather than tuned, since PPL moves with the wheel and with n |
| 32-bit reductions in stage 1b | **1.048x** | only `off mod q` genuinely needs 64 bits; k never has to be formed, and kq*dM + oq fits a u32 for every stage-1 and stage-2 prime |
| sieve `__launch_bounds__` 4 -> 3 blocks/SM | **1.028x** | at 4 the compiler is capped at 64 registers and spills 24 B/thread; at 2 and 0 the spill is already gone and only occupancy is being sold (~0.998x) |
| round size 16 -> 24 | **1.023x** | the optimum moved *again* once stage-1b primes got cheaper -- and reversed direction: 24 measured 0.984x before that change |
| **paired total, previous engine vs this one** | **1.294x** | one process, 7 interleaved rounds, both reproducing the frozen fingerprint on identical work |

The paired 1.294x is the load-bearing number, and it is deliberately *less*
than the product of the rows above (1.37x): those were measured against
different baselines and two of them overlap. Cross-row absolute arithmetic
against the ledger below is exactly what Rule 3 in ../OPTIMIZATION.md warns
against -- run-to-run variance on this machine is ~2x on identical code.

Rejected on measurement: the folded pattern table (**0.685x** -- 24x smaller
tables, but it trades one load for two, and within L1 the sieve turns out to
care only about load count); bigger launches (**1.009x** for 2.1 GB of queue,
after the grid-balance fix took away what they were buying); removing the
mid-chain host round-trips (**0.995x**, confirming the earlier 0.2%);
ROUND_GRID 2048..16384 (flat within 0.2%).

The measurement lesson of this round is in OPTIMIZATION_LOG.md: two of the
three sieve ablations were invalid -- one let the compiler hoist the very
loads it was pricing, the other inverted the survivor bitmap and priced the
extraction loop instead. The valid one showed that gather *divergence* inside
L1 is free, which is what killed the folded table.

### Wall-clock after this round

The realized v4 production rate was **1.03e16 p/s** (measured from the leg's
own near-miss timestamps over interleaved 1 h and 6 h windows, which agree to
3%, not from the projection). Applying the paired 1.294x projects
**1.33e16 p/s** for v5, to be replaced by a realized average once the leg
resumes.

Conditional on the sweep being clean to the 6.12e20 frontier where the leg
stopped, and on run EXACTLY 19 (E_19 - E_20, which is what actually settles a
term -- about 12% of run->=19 events overshoot into run-21 and do not):

| target | P(a(19) by then) | v5 (proj.) | v4 (realized) |
|--------|------------------|-----------|---------------|
| 8.58e20 (a19 Q1) | 25% | 5.1 h | 6.6 h |
| 1.00e21 | 36% | 8.2 h | 10.5 h |
| 1.25e21 (a19 median) | 50% | **13.5 h** | 17.4 h |
| 2.00e21 | 74% | 29.0 h | 37.5 h |
| 2.07e21 (a19 Q3) | 75% | 30.4 h | 39.3 h |
| 5.00e21 (leg cap) | 96% | **3.81 days** | 4.93 days |

Cumulative **25.1x** over the engine that swept leg 1 (5.5e14 -> 1.33e16).
Re-sweeping the whole range 0 to 5e21 now costs ~4.3 days, the a(20)
conditional median (1.06e22) is ~8.7 days out, and the enforced 1e24 ceiling
is ~2.4 years of single-GPU wall (it was ~58 years, then ~3.0).

## Phase 5 (2026-08-16): the compaction rounds, and what the sieve is bound by

Paired ratio **1.3293x**, one process, 7 interleaved rounds over a
steady-state 2e16 window at 6.11e20 (24 launches, so no single-launch
flattery), both frozen fingerprints re-checked and the window's own survivor
list required to be identical on every run. Composition, each measured
against the baseline it was taken on:

| change | ratio |
|--------|-------|
| baked per-prime literals in the stage-1b round kernels | 1.084 |
| queue carries `off` rather than its index (no 240 MB gather per round) | 1.058 |
| ROUND re-sweep 24 -> 16 | 1.043 |
| 32-bit `off mod q` split, stage 1b | 1.037 |
| 32-bit `off mod q` split, stage 2 | 1.023 |
| NINC re-sweep 28 -> 26 | 1.020 |
| marched (visit-order) pattern table | 1.019 |
| sieve launch bound 3 -> 2 | 1.010 |

Measured and NOT kept, because both landed inside the noise floor: the same
off-split applied to the sieve's residue seeding (1.006x) and hoisting the
extraction loop's edge mask under a branch (0.999x). They are the same
finding twice, and it is the load-bearing one -- **the sieve does not care
about arithmetic.** Together with the gather-spread probe (17.3 sectors per
warp-load down to 1.0 is worth only 1.53x), that pins the dominant phase to
load COUNT from both directions.

Phase split after this round: bit-sieve 78.2%, compaction rounds 15.9%
(was 28.0%), cold stage-2 kernel 5.9%, host 1.8%.

### Wall-clock after this round

The realized v6 production rate was **1.232e16 p/s** over a 10 h leg.
Applying the paired 1.3293x projects **1.64e16 p/s**, to be replaced by a
realized average once the leg resumes.

Conditional on the sweep being clean to the 1.056e21 frontier where the leg
stopped, and on run EXACTLY 19:

| target | v7 (proj.) | v6 (realized) |
|--------|-----------|---------------|
| 1.25e21 | 3.3 h | 4.4 h |
| 2.00e21 | 16.0 h | 21.3 h |
| 5.00e21 (leg cap) | **2.79 days** | 3.71 days |

Cumulative **~30x** over the engine that swept leg 1 (5.5e14 -> 1.64e16).
Re-sweeping the whole range 0 to 5e21 now costs ~3.5 days and the enforced
1e24 ceiling is ~1.9 years of single-GPU wall (it was ~58 years, then ~3.0,
then ~2.4).

**The next wheel is priced but not taken.** 37# is worth **1.85x on the
sieve** at production launch shape -- the Phase-4 verdict of 0.75x was a
consequence of the queue budget capping the launch's period count, which
offset chunking removes. It measures **0.58x on the frozen 5e14 shape**,
which holds 2,494 periods of the 31# wheel but only 68 of the 37# one. The
blocker is the benchmark's shape rather than the engine's, and re-cutting a
frozen anchor is a human decision; see OPTIMIZATION_LOG.md for the fit.

## Phase 4 (2026-08-16): the per-thread term

The previous round's paired ratio is now confirmed in production, which is
the check that matters: the overnight leg swept 6.1152e20 -> 1.0557e21 in
10.0 h at a realized **1.232e16 p/s**, against 1.33e16 projected from the
paired 1.294x. 93% -- the A/B transferred.

Same discipline as always: interleaved paired ratios, frozen fingerprint
re-checked every run, steady-state 2e16 window at 6.1e20.

| change | ratio | note |
|--------|-------|------|
| one grid y-slice (T target 2048 -> 4096) | **1.022x** | T is derived from PPL, so this resolves to a single full slice at the production launch size and halves the thread count. A flat T sweep had measured "T=4096" at 1.004x the round before -- but that was before T was derived, so the same nominal value still produced two slices with a 132-period tail. The knob had not been tested; a differently-shaped knob with the same name had |
| 32-bit residue seeding in the sieve | **1.015x** | predicted ~4% from the Barrett count and delivered 1.5%, which is itself the finding: the per-thread term is mostly thread setup and the offset load, not arithmetic |
| 32-bit reduction in cold stage 2 | **1.014x** | the transformation left priced-but-unbuilt at ~1.5% the round before; it came in at exactly that |
| **paired total vs the previous engine** | **1.055x** | one process, 7 interleaved rounds, both reproducing the frozen fingerprint |

Noise floor, measured rather than assumed: T targets 3000 and 4096 resolve
to the *same* derived T=4288, and those two identical configurations
differed by **0.3%** in one battery. So 0.5% gaps in this ledger are not
results and 1.4% gaps are.

Rejected: **the 37# wheel**, the last named candidate-count lever. It would
generate 1.85x fewer candidates, but its period is 37x longer, so a launch
holds 37x fewer periods and the sieve's per-thread setup is amortized over
far fewer of them. Fitting `sieve = a + b/T` from a forced-T sweep in the
existing engine (T = 192/256/640/1088/2176 -> 810.9/664.9/411.0/335.1/293.6
ms, giving 239 ms + 109449/T) prices it at **0.75x** with today's queue
budget and 0.95x with 6 GB; it needs 32 GB of buffers plus a 4.8 GB offset
table to reach 1.41x. Priced without building any of it.

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
