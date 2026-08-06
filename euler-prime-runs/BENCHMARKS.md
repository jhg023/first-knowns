# BENCHMARKS -- euler-prime-runs

SCORE convention: `python score.py` prints SCORE = end-to-end Mp/s on
the frozen benchmark shape, ONLY if all gates are green and the work
fingerprint (survivor count 178, xor checksum 120489734542316 on
[1e16, 1e16+5e14)) reproduces exactly. Skipped work scores 0.

| date | engine | SCORE | notes |
|------|--------|-------|-------|
| 2026-08-05 | v1 baseline | 44,550,000 (est.) | pre-score.py measurement, 4.46e13 p/s |
| 2026-08-05 | v3 (frozen) | **189,738,385** | Barrett + 29# wheel + 2D grid + L2 masks |

Wall-clock at SCORE (n=17 production):

| depth | time |
|-------|------|
| 1e16  | ~53 s |
| 1e17  | ~9 min |
| 1e18  | ~1.5 h |
| 1.8e19 (u64 cap) | ~26 h |

Height-flatness: 1e16 vs 1e18 windows agree within 1.5%.

Model milestones at this rate: E(a17)=1 at 2.6e17 (~23 min in),
P(a17) = 88% by 1.5 h, ~100% by cap; P(a18) = 78% by cap.

Note (2026-08-06): after the public-repo refactor (shared code moved to
../huntlib), the full gate battery re-ran green and the benchmark
fingerprint (survivors 178, checksum 120489734542316) reproduced
exactly. The timing measured during that verification (9.8e13 p/s) was
taken while a production hunt shared the GPU and is not a SCORE entry;
the frozen SCORE stands from the uncontended pre-hunt measurement.
