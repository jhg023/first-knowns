# BENCHMARKS -- euler-prime-runs

SCORE convention: `python score.py` prints SCORE = end-to-end Mp/s on
the frozen benchmark shape, ONLY if all gates are green and the work
fingerprint (survivor count 178, xor checksum 120489734542316 on
[1e16, 1e16+5e14)) reproduces exactly. Skipped work scores 0.

| date | engine | SCORE | notes |
|------|--------|-------|-------|
| 2026-08-05 | v1 baseline | 44,550,000 (est.) | pre-score.py measurement, 4.46e13 p/s |
| 2026-08-05 | v3 (frozen) | 189,738,385 | Barrett + 29# wheel + 2D grid + L2 masks |
| 2026-08-06 | v4 (frozen) | **343,361,199** | multi-period threads + incremental first-16 stage-1 residues (2.5x vs v3 in same-day A/B; measured under ambient desktop GPU load, so conservative) |

Wall-clock at SCORE (n=17 production, v4):

| depth | time |
|-------|------|
| 1e16  | ~29 s |
| 1e17  | ~5 min |
| 1e18  | ~49 min |
| 1.8e19 (u64 cap) | ~15 h |

Height-flatness: 1e16 / 1e18 / 1.7e19 windows agree within 0.8%.

Model milestones at this rate: E(a17)=1 at 2.6e17 (~13 min in),
P(a17) = 88% by ~49 min, ~100% by cap; P(a18) = 78% by cap.

Note (2026-08-06): after the public-repo refactor (shared code moved to
../huntlib), the full gate battery re-ran green and the benchmark
fingerprint (survivors 178, checksum 120489734542316) reproduced
exactly. The timing measured during that verification (9.8e13 p/s) was
taken while a production hunt shared the GPU and is not a SCORE entry;
the frozen SCORE stands from the uncontended pre-hunt measurement.
