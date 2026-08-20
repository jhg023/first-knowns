# BENCHMARKS -- dickson-ladders

SCORE convention: `python score.py` prints a score ONLY if every
correctness gate is green and the frozen work fingerprint -- exact
survivor count plus xor checksum of the surviving j -- reproduces
exactly. Skipped work scores 0; broken mathematics scores 0.

**Three frozen shapes.** All are measured with the one production engine,
all are checked on every run.

| name | filter | wheel | window (j) | k-line window | fingerprint (count / xor) | frozen |
|------|--------|-------|------------|----------------|---------------------------|--------|
| `SCORE` | n = 10 | 2,310 | [1e12, +2^32) | [2.31e15, +9.92e12) | 1,213 / 1,003,170,806,905 | 2026-08-18, v1 |
| `SCORE12` | n = 12 | 30,030 | [6e11, +2^32) | [1.80e16, +1.29e14) | 292 / 2,752,794,123 | 2026-08-18, v1 |
| `SCORE13` | n = 13 | 30,030 | [7e16, +2^38) | [2.10e21, +8.26e15) | 2,739 / 70,000,110,051,605,722 | 2026-08-18, v2, cross-checked against v1 bit for bit |

Why three: the first two disagree about what matters (the n = 12 shape
has ~4x fewer survivors per candidate and 13x more k-line per candidate,
so a change that helps one and hurts the other shows up as a split
verdict instead of an average). The third exists because the v2 engine
crosses a 2^32 window in about a millisecond -- one launch -- and on that
window two identical configurations read anywhere from 0.5x to 2.3x of
each other. `SCORE13` is the **production configuration** for the a(13)
campaign, sited at the model's a(13) median, 64x wider (16 launches at
the production LAUNCH), and it is the shape every tuning verdict in
OPTIMIZATION_LOG.md was taken on. The frozen 2^32 shapes were not
amended (a shape that stops resolving a change gets a sibling, not an
edit); they still pin the v1 fingerprints and they still score.

The rate reported is **end-to-end k-line per second** (span x W / wall),
which is what the hunt is paid in -- not candidates per second, which
flatters a wider wheel for free.

## v2 (2026-08-18, RTX 4090): the current baseline

| shape | rate | SCORE | paired v2/v1 |
|-------|------|-------|--------------|
| `SCORE` (n = 10) | 4.77e15 k/s (2.06e12 candidates/s) | 4,768,286,861 | 464x (min 449, max 542) -- single launch, flattered |
| `SCORE12` (n = 12) | 7.47e16 k/s (2.49e12 candidates/s) | 74,691,839,136 | 551x (min 399, max 640) -- single launch, flattered |
| `SCORE13` (n = 13) | **1.63e17 k/s** (5.43e12 candidates/s) | **163,185,339,779** | **913x** (min 627, max 915; 16 launches) |

The v2 engine: stage 1a bit-sieve over the first NS primes (NS derived
from a survival target: 16 at n = 13, 23 at n = 10), stage 1b geometric
compaction rounds with a one-Barrett-plus-one-bit-probe test, a
warp-per-candidate kernel for the sparse deep rounds, launches of 2^34
candidates replayed as CUDA graphs and double-buffered across two
streams, host classification pipelined in a process pool one segment
behind the device. Every step and every reject is in OPTIMIZATION_LOG.md.

The same shapes' rates swing by up to 2x between captures of identical
code on this desktop (a dozen GPU-using applications share the card);
absolutes above are one capture, the paired ratios are the results.

## v1 baseline (2026-08-18, RTX 4090), for the ratio

| shape | rate | SCORE |
|-------|------|-------|
| `SCORE` (n = 10) | 6.54e12 k/s (2.83e9 candidates/s) | 6,538,383 |
| `SCORE12` (n = 12) | 8.78e13 k/s (2.93e9 candidates/s) | 87,833,496 |
| `SCORE13` (n = 13, measured on v1 for the cross-check) | 1.94e14 k/s (6.46e9 candidates/s) | 193,892,821 |

## Wall-clock at the v2 rate

Against the model's predictions (README, stated before the run). Two
rates apply: the device rate above, and the **end-to-end** rate with host
classification, which at n = 10 is host-bound on this 32-core machine
(2.45e15 k/s measured, 0.38x of GPU-only) and at n = 13 is 94% of
GPU-only (1.22e17 k/s measured in the same harness; the table uses the
scored 1.63e17 for the device and notes the end-to-end figure).

| target | depth | filter | wall-clock (end-to-end) | was, at v1 |
|--------|-------|--------|-------------------------|------------|
| a(10) Q1 | 5.22e14 | n = 10 | 0.2 s | 1.3 min |
| **a(10) median** | **1.68e15** | n = 10 | **0.7 s** | 4.3 min |
| a(10) P90 | 8.67e15 | n = 10 | 3.5 s | 22 min |
| a(11) Q1 | 2.12e16 | n = 10 | 9 s | 54 min |
| **a(11) median** | **7.18e16** | n = 10 | **29 s** | 3.1 h |
| a(11) P90 | 3.78e17 | n = 10 | 2.6 min | 16 h |
| **a(12) median** | **1.83e19** | n = 12 | **~4 min** (device rate; host ~65% of it, hidden) | 2.4 days |
| a(13) Q1 | 6.34e20 | n = 13 | 1.1 h | 38 days |
| **a(13) median** | **2.14e21** | n = 13 | **3.6 h** (3.9 h end-to-end) | 128 days |
| a(13) Q3 | 5.50e21 | n = 13 | 9.4 h | |
| a(13) P90 | 1.09e22 | n = 13 | 19 h | 1.8 years |

a(13) has moved from "not reachable" to an afternoon; the P90 is under a
day. (The "was" column uses v1's measured SCORE13 rate, 1.94e14 k/s; the
README's original "~9 months" used the SCORE12 rate, and v1 happened to
run 2.2x faster per candidate at n = 13 than at n = 12.) The brief that
opened OPTIMIZATION_LOG.md (9x for a month, 56x for five days) is closed
at 913x on the production shape.

## Measurement hygiene (inherited, not rediscovered)

The sibling project in this repository established these the expensive
way; they are binding here from the start:

- **Absolute scores on this machine swing by up to 2x between captures
  of identical code** under ambient desktop GPU load. Quote paired,
  interleaved ratios; treat any single absolute number as a rough level,
  not a result.
- **Interleave every A/B and re-check the fingerprint on every run.**
  Sequential sweeps invent cliffs that are not there. This session's A/B
  harness also required each configuration's survivor list to be
  identical run to run, which is what caught a scaffolding bug (two
  double-buffer slots aliased to one) before it could be timed.
- **Re-sweep tuning constants after any structural change.** Optima move:
  NS went 32 -> 24 -> 16 in one day as stage 1b got cheaper twice.
- A benchmark shape stated in absolute units silently drifts as the
  engine's natural work unit grows underneath it. When a shape can no
  longer resolve a change, it gets a **sibling, not an edit** -- which is
  exactly what happened to `SCORE` and `SCORE12` on 2026-08-18.
- Time with `perf_counter`, not `time.time()`: a fast engine crosses a
  frozen window in under the wall clock's resolution (this bit huntlib
  once and is fixed there).

## v3 (2026-08-18, RTX 4090): the campaign, priced separately from the engine

v3 changed the engine barely at all (two re-swept constants) and the
CAMPAIGN a great deal, so the two are reported separately. **The SCORE
shapes measure the engine.** They deliberately do not move when the
campaign is re-configured, which is the point of freezing them -- and it
is why the table below is nearly flat while the hunt got 28x faster.

| shape | final capture | paired v3/v2 |
|-------|---------------|--------------|
| `SCORE` (n = 10) | 5,216,285,202 | 1.42x, paired spread 0.57-2.04 -- **does not resolve** |
| `SCORE12` (n = 12) | 51,519,020,515 | 0.83x, paired spread 0.57-2.04 -- **does not resolve** |
| `SCORE13` (n = 13) | 97,184,320,989 | **1.046x** (min 1.036, max 1.084) |

The two 2^32 shapes are now pure noise between identical configurations
(OPTIMIZATION.md 2.13); `SCORE13` is the anchor and the PAIRED number is
1.046x, which is the sum of RATIO 4 -> 2 and T_MAX 1024 -> 2048.

**Read the ratio, not the absolute, and here is why in this project's own
numbers.** `SCORE13` was captured six times on 2026-08-18 -- once before
the engine change and five times after -- and came out 104.5e9, 108.2e9,
98.6e9, 97.2e9, 107.3e9 and 97.2e9, for a change a paired A/B puts at
1.046x. The
absolutes span 11%, straddle the baseline in both directions, and would
support any conclusion you like; the machine spent the day running its own
experiments alongside a desktop compositor. Only measurements where both
arms alternate inside one process are worth anything here -- which is
OPTIMIZATION.md Rule 3, restated in this project's own data. The frozen
fingerprints reproduced on every one of those runs.

`score.py` now pins each shape's sieve depth (65536) explicitly rather than
inheriting the engine default, because the campaign no longer runs at the
default depth. A frozen shape should not be able to drift because a
constant moved elsewhere.

### What the campaign is worth, which is not what SCORE is worth

The hunt is paid in k-line per second **end-to-end**, device and host
together, at the configuration it actually runs. Per 1e18 of k-line at
k ~ 1e19:

| configuration | device | host | workers | end-to-end |
|---------------|--------|------|---------|------------|
| v2 (filter 11, wheel 2310, q2 65536, all-bases) | 142.3 s | 3,308 core-s | 8 | 413 s = **2.42e15 k/s** |
| v3 (filter 12, wheel 30030, q2 262144, two-pass) | 14.78 s | 25.6 core-s | 4 | 14.78 s = **6.77e16 k/s** |

**27.9x**, on half the host processes, with the device now the binding
side rather than idling 60% of the time. The live v2 campaign logged
2.35e15 k/s, which brackets the v2 row above.

Rungs at the v3 rate, from `model_results.json`: a(12) median 1.83e19 is
about **4.5 minutes** of sweep and its P90 9.51e19 about **23 minutes**;
a(13) median 2.14e21 is about **8.8 hours** and its P90 1.09e22 about
**45 hours**. At the v2 rate those were 2.2 hours, 11 hours, 10 days and
50 days.

## v4 (2026-08-19, RTX 4090): the fold

The engine folds its first sieve prime into candidate generation
(OPTIMIZATION_LOG.md v4): j = 17u + r over the five surviving offsets at
n = 13, identical survivor stream (G17), same kernels walking a line
3.4x thinner. **Paired and interleaved at the campaign shape (n = 13,
q2 = 262144, 2^41-j window, streams compared every round):
v4/v3 = 2.387x (min 2.138, max 2.439)** -- 2.31e17 k/s folded against
9.64e16 k/s unfolded on an idle machine, 4.3 s of device per 1e18 of
k-line. Constants re-swept after the change: NS derivation confirmed
(the 20-24 plateau is flat), RATIO 2 and LAUNCH 2^34 stay, pinned T 4096
inverted to 0.979x and is closed.

| shape | capture | note |
|-------|---------|------|
| `SCORE` (n = 10) | 1,230,573,335 | a folded pass through a 2^32 window is 5-7 ragged EAGER launches: the shape's absolute collapsed further and resolves nothing (OPTIMIZATION.md 2.13). Fingerprint reproduces, which is the job it still does |
| `SCORE12` (n = 12) | 16,466,591,056 | same |
| `SCORE13` (n = 13) | 214,673,527,566 | ~0.94 launches per offset -- eager, no double-buffer overlap -- and still 2.2x the pre-fold capture. Engine A/Bs are judged on campaign-shaped windows now (the paired 2.387x above) |

The fold also extends the enforced reach 17x, to k = 2.04e24 (the u64
quantity on the device is u, not j), which moves a(14) from "past the
ceiling at its median" to E = 4.41 (98.8%) inside the reach. At the v4
rate the remaining a(13) tail (cursor k = 1.10e22 to P95-ish depths) is
hours, and the a(14) median 1.68e23 is about **8.5 days** of sweep --
the P90 8.55e23 about **43 days** -- where the pre-fold engine would
have hit its ceiling at 1.20e23 with a(14) still at 42% odds.

**Measured against a real campaign.** The v3 configuration then found
a(12) = 55,119,263,286,518,170,740 at k = 5.51e19 after **9 min 45 s** of
wall clock, and was stopped at k = 8.73e19 after 13.5 min (33,199,184
survivors classified). That is 1.08e17 k/s end-to-end including the
prelude, the [NEAR]/[DISCOVERY] verifications and the filter switch --
1.6x the 6.77e16 k/s of the A/B row above, which was measured at filter
12 on a machine also running the old campaign. The projection above said
4.5 minutes to a(12)'s median; the sweep passed it at about **3 minutes**
and the find itself sat 3.0x past the median, at 9 min 45 s. The
projection was conservative on rate; the wait past the median is the
model's variance, not the benchmark's.

The v4 configuration was then measured against a real campaign the same
way: it found a(13) = 12,094,123,415,384,869,458,600 at k = 1.209e22 on
2026-08-19, **58 minutes after the fold's commit landed** -- 1.12e21 of
k-line beyond the crash point the campaign resumed from, with the
prelude, a run-12 [NEAR] verification and the discovery's own four-way
verification inside the same wall clock. That implies at least 2.5e17 k/s
end-to-end, above the paired capture's 2.31e17 absolute -- expected, and
not a discrepancy: the interleaved A/B shares the device between its two
arms, and its result is the ratio, never the absolute. The campaign then
swept on to k = 1.57e22 and was paused 2026-08-20 with a(14) the next
open term.
