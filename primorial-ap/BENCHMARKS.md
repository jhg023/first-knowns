# BENCHMARKS — primorial-ap

> **Authorship disclaimer:** None of this was written by me; it was
> authored by **Claude (Anthropic's AI)** at my direction.

`python score.py` prints `SCORE <Mp/s>` and prints it **only** if every
correctness gate is green **and** the run reproduces a frozen work
fingerprint. An engine that skips work fails the fingerprint; an engine
that breaks correctness fails the gates. Either way it scores 0.

## The frozen shape

| | |
|---|---|
| term | n = 16 |
| sieve depth | 65536 (2¹⁶ — the *engine default*, deliberately not the campaign's 2048) |
| window | 1.611×10¹⁰ of p-line from p = 4.0×10¹³ |
| launch size | 2²⁵ wheel periods (~1.0×10⁹ of p-line) |
| **fingerprint** | **192 survivors, xor checksum 4046714554** |

The shape is pinned to the engine default rather than to the campaign
configuration on purpose. The campaign depth is a configuration decision
that has already moved once and will move again as the engine changes; the
score has to keep meaning the same thing across those moves. A deliberate
coverage change legitimately changes the fingerprint — update it in the
same commit with an [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) entry
explaining why.

## SCORE ledger

| date | engine | SCORE (Mp/s) | fingerprint | note |
|------|--------|--------------|-------------|------|
| 2026-08-20 | v1 | **5,163** | 192 / 4046714554 | first gated engine; chunked marking kernel, Barrett, mod-30 bitmap |
| 2026-08-20 | v1 | 5,095 | 192 / 4046714554 | re-run after the huntlib extraction — same fingerprint, 1.3% apart |
| 2026-08-20 | v2 | **39,772** | 192 / 4046714554 | pattern tables + shared-memory sub-segments + host fixes (OPTIMIZATION_LOG #4–#7); same fingerprint |

Two runs of an unchanged engine land 1.3% apart, which is the ambient
noise floor to judge any future A/B against. Anything smaller than that is
not a result (OPTIMIZATION.md: interleave, and take the ratio).

Card: one RTX 4090, 128 SMs, stock power limit (450 W), driver 610.88.

## Wall clock at the campaign configuration

The score is measured at the *frozen* depth. The campaign runs at
depth 8192, where the numbers are different and are the ones that matter
for planning. Re-measured 2026-08-20 against the **v2 engine**
(OPTIMIZATION_LOG #4–#7), interleaved, median, on a sustained card — see
OPTIMIZATION_LOG #2 for why that word is load-bearing. Absolute device
rates on this desktop swing ±15–30% with ambient load; the ratios are
the stable quantity.

| sieve depth | device p/s | survivors / unit | host cores | workers |
|-------------|-----------|------------------|-----------|---------|
| 2048 | 5.2×10¹¹ | 4.37×10⁻⁶ | 38.8 | impossible |
| 4096 | 2.4×10¹¹ | 1.09×10⁻⁶ | 4.5 | 8 |
| **8192 (campaign)** | **2.1×10¹¹** | 2.99×10⁻⁷ | 1.1 | 3 |
| 16384 | 1.5×10¹¹ | 8.75×10⁻⁸ | 0.23 | 2 |

Host cores are priced at the measured 16.7 µs per survivor — which is
`pow(2, p−1, p)` arithmetic on the 70-bit values, not overhead
(OPTIMIZATION_LOG #9). v1 was device-bound everywhere and the shallow
end won; v2 inverted the problem, and the campaign depth is now set by
the **load budget**: 8192 is 89% of 4096's device rate for a quarter of
its host demand.

**End-to-end, as the campaign actually runs it** (depth 8192, 3 workers,
64 launches per checkpoint segment, classification overlapped one
segment behind the device — OPTIMIZATION_LOG #8): **2.07×10¹¹ p/s**,
measured over a bounded production run to p = 6.4×10¹², **34.7× v1's
end-to-end** at 96% of the device rate.

## What each term costs

At 2.07×10¹¹ p/s end-to-end, against the model's stated quartiles:

| term | Q1 | median | Q3 | P90 |
|------|----|--------|----|-----|
| a(16) | 75 s | **3.1 min** | 6.4 min | 11 min |
| a(17) | 27 min | **1.1 h** | 2.2 h | 3.8 h |
| a(18) | 9.6 h | **24 h** | 2.0 d | 3.4 d |
| a(19) | 9.3 d | **23 d** | 47 d | 79 d |
| a(20) | 229 d | **1.5 y** | 3.1 y | 5.3 y |

v1's table said a(16) was an afternoon, a(18) five weeks, and a(19) out
of reach without a faster engine. The faster engine exists now: a(19) is
a three-week hunt at the median, and a(20) is the term that depends on
optimization work that has not been done (or on patience). The enforced
ceiling is p = 10²⁶, which is the campaign's last rung and is not a
depth anything here will reach.
