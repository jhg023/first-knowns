# BENCHMARKS -- dickson-ladders

SCORE convention: `python score.py` prints a score ONLY if every
correctness gate is green and the frozen work fingerprint -- exact
survivor count plus xor checksum of the surviving j -- reproduces
exactly. Skipped work scores 0; broken mathematics scores 0.

**Two frozen shapes (2026-08-18, v1 kernel).** Both are measured with the
one production engine, both are checked on every run.

| name | filter | wheel | window (j) | k-line window | fingerprint (count / xor) |
|------|--------|-------|------------|----------------|---------------------------|
| `SCORE` | n = 10 | 2,310 | [1e12, +2^32) | [2.31e15, +9.92e12) | 1,213 / 1,003,170,806,905 |
| `SCORE12` | n = 12 | 30,030 | [6e11, +2^32) | [1.80e16, +1.29e14) | 292 / 2,752,794,123 |

Why two: they disagree about what matters. The n = 12 shape has ~4x
fewer survivors per candidate and 13x more k-line per candidate, so a
change that helps one and hurts the other shows up as a split verdict
instead of an average. The sibling project needed three shapes before it
could see a wheel change honestly; starting with two is the cheap version
of that lesson.

The rate reported is **end-to-end k-line per second** (span x W / wall),
which is what the hunt is paid in -- not candidates per second, which
flatters a wider wheel for free.

## v1 baseline (2026-08-18, RTX 4090)

| shape | rate | SCORE |
|-------|------|-------|
| `SCORE` (n = 10) | 6.54e12 k/s (2.83e9 candidates/s) | 6,538,383 |
| `SCORE12` (n = 12) | 8.78e13 k/s (2.93e9 candidates/s) | 87,833,496 |

A separate capture of the same code minutes earlier read 7.14e12 and
9.05e13 -- a 9% spread from ambient load alone, on a quiet machine. Treat
the absolutes as levels and the paired ratios as results.

Candidate throughput is essentially identical across the two filters
(2.8-2.9e9/s) -- the kernel's cost is per candidate and barely depends on
n, so the whole 13x difference in k-line rate is the wheel. That is the
first thing this benchmark says and it is worth saying out loud: on this
problem, **line rate is bought with wheels, not with instructions**.

## Wall-clock at the v1 rate

Against the model's predictions (README, stated before the run):

| target | depth | filter | wall-clock |
|--------|-------|--------|-----------|
| a(10) Q1 | 5.22e14 | n = 10 | 1.3 min |
| **a(10) median** | **1.68e15** | n = 10 | **4.3 min** |
| a(10) P90 | 8.67e15 | n = 10 | 22 min |
| a(11) Q1 | 2.12e16 | n = 10 | 54 min |
| **a(11) median** | **7.18e16** | n = 10 | **3.1 h** |
| a(11) P90 | 3.78e17 | n = 10 | 16 h |
| **a(12) median** | **1.83e19** | n = 12 | **2.4 days** |
| **a(13) median** | **2.14e21** | n = 13 | **~9 months** |

a(10) through a(12) are reachable with the v1 kernel as written. a(13) is
not, and that gap is the entire optimization brief -- see
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) for what is priced and what
has been measured.

## Measurement hygiene (inherited, not rediscovered)

The sibling project in this repository established these the expensive
way; they are binding here from the start:

- **Absolute scores on this machine swing by up to 2x between captures
  of identical code** under ambient desktop GPU load. Quote paired,
  interleaved ratios; treat any single absolute number as a rough level,
  not a result.
- **Interleave every A/B and re-check the fingerprint on every run.**
  Sequential sweeps invent cliffs that are not there.
- **Re-sweep tuning constants after any structural change.** Optima move.
- A benchmark shape stated in absolute units silently drifts as the
  engine's natural work unit (here: the wheel) grows underneath it. When
  a shape can no longer resolve a change, it gets a **sibling, not an
  edit** -- the frozen fingerprints above are never amended to make a
  change look good.
