# RESULTS — prime-ladders (A084700, A084701)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

Four terms of **A084700**, all found on **2026-09-02** by the first
campaign — the v2 engine, k-space wheel (23], (37], (47], sieve 65536 —
in 4.4 hours of device from `k = 10⁶` to the proof ceiling of the time,
`5.44×10²²`. They are the first new terms of the sequence since Phil
Carmody's `a(13)` of March 2004. Each is a **first occurrence**: every `k`
from `K_START = 10⁶` to the find was swept and every survivor classified
in `k` order, and below `K_START` the claim rests on monotonicity
(`a(13) = 1.6×10¹⁴`). Every value `prime(i)·k + 1` of every find is under
huntlib's deterministic Miller–Rabin bound (`3.317×10²⁴`), so each of its
certificates *is* the seven-base test (`deterministic-mr`), and every
stopper — the composite at `i = run + 1` that bounds the claim to exactly
`run` — is exhibited with a factor.

All four passed the same four legs: huntlib's Miller–Rabin chain, sympy's
BPSW on the run length, a from-scratch re-sieve on a different wheel and
sieve depth (the CPU engine, no wheel, sieve 4096), and the stopper
composite with its witness.

### A084700 a(14) = 24,581,646,307,811,670 — 02:06

- **run 14**: `prime(i)·k + 1` is prime for `i = 1..14`; the 14th value is
  `43·k + 1 = 1,057,010,791,235,901,811`.
- **stopper**: `47·k + 1 = 1,155,337,376,467,148,491 = 4,545,727 × …`.
- **model**: `E = 0.79` at the find (from `a(13)`), `k / median = 1.22`.
- evidence: [`evidence/A084700_a14_24581646307811670.json`](evidence/A084700_a14_24581646307811670.json)

### A084700 a(15) = 1,183,192,161,007,235,610 — 02:06

- **run 15**; found two seconds after `a(14)`, in the same wheel period.
- **stopper**: `53·k + 1 = 62,709,184,533,383,487,331 = 29 × …`.
- **model**: `E = 0.74` (from `a(14)`), `k / median = 1.10`.
- evidence: [`evidence/A084700_a15_1183192161007235610.json`](evidence/A084700_a15_1183192161007235610.json)

### A084700 a(16) = 161,515,890,673,488,267,840 — 02:09

- **run 16**.
- **stopper**: `59·k + 1 = 9,529,437,549,735,807,802,561 = 1,087 × …`.
- **model**: `E = 1.43` (from `a(15)`), `k / median = 2.81` — the one
  find of the four that landed late.
- evidence: [`evidence/A084700_a16_161515890673488267840.json`](evidence/A084700_a16_161515890673488267840.json)

### A084700 a(17) = 2,446,970,377,116,913,184,460 — 02:39

- **run 17**; the 17th value is `59·k + 1 = 144,371,252,249,897,877,883,141`.
- **stopper**: `61·k + 1 = 149,265,193,004,131,704,252,061 = 23 × …`.
- **model**: `E = 0.66` (from `a(16)`), `k / median = 0.94`.
- evidence: [`evidence/A084700_a17_2446970377116913184460.json`](evidence/A084700_a17_2446970377116913184460.json)

The least-claim basis of every file: `swept_from = 10⁶`, `swept_to = k`,
wheel `W = 614,889,782,588,491,410`, sieve depth 65536, monotone floor
`161,082,438,032,880`, under the engine key
`a084700-v2-p123-p237-p347-q265536-seg128`. The ledger
[`evidence/a084700_discoveries.json`](evidence/a084700_discoveries.json)
carries all four.

**How they scored against the model.** Pooled, the four finds sit at
`E = 0.79, 0.74, 1.43, 0.66` — mean 0.91 against the Exp(1) mean of 1 —
and at `1.22, 1.10, 2.81, 0.94` times their medians. This family did
*not* run late the way the three earlier ladder projects did (pooled
optimism 1.92×); three of the four arrived at or before the median.

## The census

Counts per run length from the checkpoint's `census` table at the end of
the first campaign, as printed in every `[STATUS]` line. A run one short
of the open term is a `[NEAR]` line with its ordinal; everything shorter
is a count and nothing else.

| run | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 |
|---|---|---|---|---|---|---|---|---|---|---|
| count | 9,078 | 3,340 | 1,323 | 503 | 182 | 62 | 36 | 7 | 2 | 1 |

32,304,365 survivors were classified over `[10⁶, 5.4377×10²²)`; the eight
`[NEAR]` values are the run-14, run-15, run-16 and run-17 values that
arrived while each of those was the open term (the run-17 count of 1 is
`a(17)` itself). Counts below the frontier of the moment are the census;
the frontier moved four times during the run, so the columns mix census
values counted at different filters.

## In progress

The first campaign stopped at **`k = 54,377,163,033,430,649,351,940`**
(`5.4377×10²²`) on 2026-09-02 at 06:30, not on a find but on the **engine
ceiling of the time**: the deterministic Miller–Rabin bound rearranged for
`prime(18)·k + 1`, which the model gave a 24% chance of holding `a(18)`.
That is where the v3 engine takes over ([README.md](README.md)): the
A084700 ceiling is now `3.317×10²⁴` (99.4% for `a(18)` by the model), a
discovery past the old crossing is proved by a BLS75 Theorem 1
certificate on `N − 1 = prime(i)·k`, and the wheel runs in unit space to
53. The v2 cursor is **adopted**: period 88434 of `6.15×10¹⁷` becomes
period 1668 of `3.26×10¹⁹`, floored, with `1.84×10¹⁹` of overlap re-swept
as a cross-check.

| family | frontier | open next | the campaign stands at |
|---|---|---|---|
| A084700 (`--sign +1`) | `a(17) = 2,446,970,377,116,913,184,460` (this project, 2026-09-02) | `a(18)` — model Q1 `5.7×10²²`, median `1.9×10²³`, P90 `1.0×10²⁴` | `k = 5.4377×10²²`, resuming under the v3 key |
| A084701 (`--sign -1`) | `a(11) = 3,894,254,360,010` (Wilson/Reble, Jun 2003) | `a(12)` | not started; opens at period 0, clipped at `k = 10⁶` |

The odds model's pre-run predictions are in [README.md](README.md#the-odds-model)
and `model_results.json`.
