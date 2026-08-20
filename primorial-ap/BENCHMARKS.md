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
depth 2048, where the numbers are different and are the ones that matter
for planning. All measured 2026-08-20, interleaved, four rounds, median,
on a **sustained** card — see OPTIMIZATION_LOG #2 for why that word is
load-bearing.

| sieve depth | device p/s | survivors / unit | host cores | workers |
|-------------|-----------|------------------|-----------|---------|
| 1024 | 9.67×10⁹ | 1.99×10⁻⁵ | 3.28 | 8 |
| **2048 (campaign)** | **8.46×10⁹** | 4.47×10⁻⁶ | 0.64 | 2 |
| 4096 | 7.19×10⁹ | 1.11×10⁻⁶ | 0.14 | 1 |
| 8192 | 6.65×10⁹ | 3.05×10⁻⁷ | 0.03 | 1 (inline) |
| 16384 | 5.95×10⁹ | 9.14×10⁻⁸ | 0.01 | 1 (inline) |
| 65536 (scored) | 5.38×10⁹ | 1.09×10⁻⁸ | 0.00 | 1 (inline) |

Host cores are priced at the measured 17 µs per survivor classification.
This hunt is device-bound at every depth worth running, which is why the
shallow end wins — the opposite of the sibling project in this repo.

**End-to-end, as the campaign actually runs it** (depth 2048, 2 workers,
16 launches per checkpoint segment): **5.97×10⁹ p/s**, measured over a
bounded run to p = 8×10¹¹. The 30% gap to the device rate is the
sieve/classify serialization — OPTIMIZATION_LOG #3.

## What each term costs

At 5.97×10⁹ p/s end-to-end, against the model's stated quartiles:

| term | Q1 | median | Q3 | P90 |
|------|----|--------|----|-----|
| a(16) | 44 min | **1.8 h** | 3.7 h | 6.2 h |
| a(17) | 15 h | **1.6 d** | 3.2 d | 5.4 d |
| a(18) | 14 d | **34 d** | 70 d | 118 d |
| a(19) | 324 d | **2.2 y** | 4.5 y | 7.5 y |

The enforced ceiling is p = 10²⁶, which is the campaign's last rung and is
not a depth anything here will reach.
