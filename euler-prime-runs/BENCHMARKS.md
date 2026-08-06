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
