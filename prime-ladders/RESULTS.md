# RESULTS — prime-ladders (A084700, A084701)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

**Twelve terms across the two families, from three campaigns.** Five of
**A084700**: four found on **2026-09-02** by the first campaign — the v2
engine, k-space wheel (23], (37], (47], sieve 65536 — in 4.4 hours of
device from `k = 10⁶` to the proof ceiling of the time, `5.44×10²²`, and
`a(18)` on **2026-09-03** by the second — the v3 engine, unit wheel
(31], (41], (53] at unit 2310, sieve 65536 — 15.2 hours in from where the
first stopped. Seven of **A084701**, `a(12)` through `a(18)`, found on
**2026-09-03** by that family's one campaign — the v3.1 engine, unit
wheel (31], (41], (53] at unit 210, sieve 65536 — in 2.5 hours of device
from `k = 10⁶` to the family's proof ceiling, `4.95×10²²`, which is where
it stopped. They are the first new terms of either sequence since Phil
Carmody's A084700 `a(13)` of March 2004 and Wilson and Reble's A084701
`a(11)` of June 2003. Each is a **first occurrence**: every `k` from
`K_START = 10⁶` to the find was swept and every survivor classified in
`k` order, and below `K_START` the claim rests on monotonicity
(`a(13) = 1.6×10¹⁴` for A084700, `a(11) = 3.9×10¹²` for A084701). Every
value `prime(i)·k ± 1` of the first four A084700 finds and of all seven
A084701 terms is under huntlib's deterministic Miller–Rabin bound
(`3.317×10²⁴`), so each of those certificates *is* the seven-base test
(`deterministic-mr`); A084700's `a(18)` has values past the bound from
`i = 5` on, and those fourteen are proved by BLS75 Theorem 1 on the
factorization of `N − 1 = prime(i)·k` (`bls75-thm1`). Every stopper —
the composite at `i = run + 1` that bounds the claim to exactly `run` — is
exhibited with a factor.

All eleven finds (A084701's `a(14)` and `a(15)` are one find: one `k`
settled both) passed the same four legs: huntlib's Miller–Rabin chain,
sympy's BPSW on the run length, a from-scratch re-sieve on a different
wheel and sieve depth (the CPU engine, no wheel, sieve 4096), and the
stopper composite with its witness. Before this file was written, every
evidence file was re-verified from disk with sympy alone: each value
re-formed from `k` and re-tested, each certificate checked against the
bound, each stopper's factor re-divided.

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
- **model**: `E = 1.43` (from `a(15)`), `k / median = 2.81` — one of the
  two finds (with `a(18)`) that landed late.
- evidence: [`evidence/A084700_a16_161515890673488267840.json`](evidence/A084700_a16_161515890673488267840.json)

### A084700 a(17) = 2,446,970,377,116,913,184,460 — 02:39

- **run 17**; the 17th value is `59·k + 1 = 144,371,252,249,897,877,883,141`.
- **stopper**: `61·k + 1 = 149,265,193,004,131,704,252,061 = 23 × …`.
- **model**: `E = 0.66` (from `a(16)`), `k / median = 0.94`.
- evidence: [`evidence/A084700_a17_2446970377116913184460.json`](evidence/A084700_a17_2446970377116913184460.json)

### A084700 a(18) = 416,266,897,501,398,851,227,320 — 2026-09-03, 09:34

- **run 18**; the 18th value is
  `61·k + 1 = 25,392,280,747,585,329,924,866,521`.
- **stopper**: `67·k + 1 = 27,889,882,132,593,723,032,230,441 =
  526,730,075,953 × 52,949,097,471,097`.
- **certificates**: the values at `i = 1..4` are under the deterministic
  bound (`deterministic-mr`); the fourteen from `i = 5` on are past it,
  and each carries a BLS75 Theorem 1 certificate on `N − 1 = prime(i)·k`
  with `k = 2³ · 3 · 5 · 7 · 11 · 13 · 17 · 277 · 32,843 · 22,407,068,503`
  factored once — every prime factor far under the bound, so every
  certificate is one level deep — all eighteen re-verified from scratch
  before the file was written (`certificates_verified: true`,
  `unproved: []`). The first find of this project to need the
  certificate route.
- **model**: `E = 1.21` at the find (from `a(17)`), `k / median = 2.21` —
  late, like `a(16)`; over the line the second campaign actually swept,
  from `5.44×10²²`, `E = 0.94`.
- **campaign**: found 15.2 hours in, `3.62×10²³` of line from the first
  campaign's stop at `6.6×10¹⁸ k/s` on average, 157,100,174 survivors
  classified; the campaign closed the find's period and stopped at
  `k = 4.1629×10²³`.
- evidence: [`evidence/A084700_a18_416266897501398851227320.json`](evidence/A084700_a18_416266897501398851227320.json)

The least-claim basis of the four 2026-09-02 files: `swept_from = 10⁶`,
`swept_to = k`, wheel `W = 614,889,782,588,491,410`, sieve depth 65536,
monotone floor `161,082,438,032,880`, under the engine key
`a084700-v2-p123-p237-p347-q265536-seg128`. The `a(18)` file carries the
same `swept_from` and floor under the v3 key
`a084700-v3-u2310-p131-p241-p353-q265536-seg128`, wheel
`W = 32,589,158,477,190,044,730` (the unit wheel's period in `k`), sieve
depth 65536; the line below `5.4377×10²²` was swept by the v2 wheel and
adopted onto the v3 period, with `1.84×10¹⁹` of overlap re-swept as a
cross-check ([README.md](README.md)). The ledger
[`evidence/a084700_discoveries.json`](evidence/a084700_discoveries.json)
carries all five.

**How the A084700 finds scored against the model.** Pooled, the five
sit at `E = 0.79, 0.74, 1.43, 0.66, 1.21` — mean 0.97 against the Exp(1)
mean of 1 — and at `1.22, 1.10, 2.81, 0.94, 2.21` times their medians,
mean 1.66×. That is inside the three earlier ladder projects' pooled
optimism of 1.92× [1.12, 3.60]: three of the five arrived at or near the
median, and two (`a(16)`, `a(18)`) at two to three times it.

### A084701 a(12) = 43,708,752,888,360 — 2026-09-03, 11:00

- **run 12**: `prime(i)·k − 1` is prime for `i = 1..12`; the 12th value is
  `37·k − 1 = 1,617,223,856,869,319`.
- **stopper**: `41·k − 1 = 1,792,058,868,422,759 = 3,191 × 561,597,890,449`.
- **model**: `E = 1.37` at the find (from `a(11)`), `k / median = 2.16`.
- evidence: [`evidence/A084701_a12_43708752888360.json`](evidence/A084701_a12_43708752888360.json)

### A084701 a(13) = 2,276,961,234,558,570 — 11:00

- **run 13**; the 13th value is `41·k − 1 = 93,355,410,616,901,369`.
- **stopper**: `43·k − 1 = 97,909,333,086,018,509 = 11 × …`.
- **model**: `E = 2.85` (from `a(12)`), `k / median = 6.44` — past its
  P90 of `1.7×10¹⁵`.
- evidence: [`evidence/A084701_a13_2276961234558570.json`](evidence/A084701_a13_2276961234558570.json)

### A084701 a(14) = a(15) = 165,784,683,394,437,030 — 11:00

- **run 15, found while `a(14)` was open**: one `k` settles both terms,
  evidenced once under `a(14)` with `settles: [14, 15]` — the family's
  third rider pair after `a(2)` on `a(1)` and `a(6)`, `a(7)` on `a(5)`.
  The 15th value is `47·k − 1 = 7,791,880,119,538,540,409`.
- **stopper**: `53·k − 1 = 8,786,588,219,905,162,589 = 13 × …`.
- **model**: `E = 2.67` (from `a(13)`), `k / median = 6.17` for `a(14)` —
  past its P90 of `1.3×10¹⁷`; `a(15)` was never searched for on its own
  and casts no vote.
- evidence: [`evidence/A084701_a14_165784683394437030.json`](evidence/A084701_a14_165784683394437030.json)

### A084701 a(16) = 16,739,777,598,441,148,020 — 11:00

- **run 16**; the 16th value is `53·k − 1 = 887,208,212,717,380,845,059`.
- **stopper**: `59·k − 1 = 987,646,878,308,027,733,179 = 839 × …`.
- **model**: `E = 0.32` (from `a(15)`), `k / median = 0.32` — early.
- **campaign**: the four finds above all lie inside period 0 of the unit
  wheel (`3.26×10¹⁹` of line) and were classified in `k` order when it
  closed, seventeen minutes after the campaign started; the filter went
  from `n = 12` to `n = 17` at that close.
- evidence: [`evidence/A084701_a16_16739777598441148020.json`](evidence/A084701_a16_16739777598441148020.json)

### A084701 a(17) = 9,050,934,616,476,845,605,590 — 12:05

- **run 17**; the 17th value is
  `59·k − 1 = 534,005,142,372,133,890,729,809`.
- **stopper**: `61·k − 1 = 552,107,011,605,087,581,940,989 = 23 × …`.
- **model**: `E = 1.87` (from `a(16)`), `k / median = 4.25`.
- **campaign**: 82 minutes in, at the `n = 17` filter, having swept
  `9.0×10²¹` of line from period 0 at `2.3×10¹⁸ k/s`.
- evidence: [`evidence/A084701_a17_9050934616476845605590.json`](evidence/A084701_a17_9050934616476845605590.json)

### A084701 a(18) = 23,562,434,281,685,500,120,920 — 12:42

- **run 18**; the 18th value is
  `61·k − 1 = 1,437,308,491,182,815,507,376,119` — 25 digits, and still
  under the deterministic bound, so every one of the eighteen
  certificates is the seven-base test itself (`deterministic-mr`,
  `certificates_verified: true`, `unproved: []`).
- **stopper**: `67·k − 1 = 1,578,683,096,872,928,508,101,639 =
  17 × 92,863,711,580,760,500,476,567`.
- **model**: `E = 0.09` (from `a(17)`), `k / median = 0.11` — under its
  Q1 of `7.2×10²²`.
- **campaign**: 118 minutes in, at the `n = 18` filter, `1.45×10²²` of
  line from `a(17)` at `6.6×10¹⁸ k/s`; the campaign then promoted to
  `n = 19` and swept the remaining `2.59×10²²` of line to the family's
  ceiling at `1.27×10¹⁹ k/s`, reaching it 34 minutes later.
- evidence: [`evidence/A084701_a18_23562434281685500120920.json`](evidence/A084701_a18_23562434281685500120920.json)

The least-claim basis of all six A084701 files: `swept_from = 10⁶`,
`swept_to = k`, wheel `W = 32,589,158,477,190,044,730` (the unit wheel's
period in `k`, at unit 210), sieve depth 65536, monotone floor
`3,894,254,360,010`, under the engine key
`a084701-v3-u210-p131-p241-p353-q265536-seg128`. The ledger
[`evidence/a084701_discoveries.json`](evidence/a084701_discoveries.json)
carries all six.

**How the A084701 finds scored against the model.** The six finds sit at
`E = 1.37, 2.85, 2.67, 0.32, 1.87, 0.09` — mean 1.53 — and at
`2.16, 6.44, 6.17, 0.32, 4.25, 0.11` times their medians. Two landed past
their P90 (`a(13)`, `a(14)`) and one under its Q1 (`a(18)`); pooled with
A084700's five, the eleven scored finds have mean `E` 1.27 against the
Exp(1) mean of 1, ratios to the median from 0.11 to 6.4, mean 2.5× and
median 2.2× ([README.md](README.md#the-odds-model)).

## The census

Counts per run length from the checkpoint's `census` table at the end of
the second campaign (2026-09-03), as printed in every `[STATUS]` line. A
run one short of the open term is a `[NEAR]` line with its ordinal;
everything shorter is a count and nothing else.

| run | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| count | 34,634 | 12,239 | 4,463 | 1,522 | 555 | 198 | 87 | 21 | 8 | 2 | 1 |

189,404,539 survivors were classified over `[10⁶, 4.1629×10²³)` —
32,304,365 by the first campaign, to `5.4377×10²²`, and 157,100,174 by
the second. The nine `[NEAR]` values are the run-14 to run-17 values that
arrived while each of those was the open term: eight in the first
campaign and one run-17 in the second (the run-18 count of 1 is `a(18)`
itself). Counts below the frontier of the moment are the census; the
frontier moved five times across the two campaigns, so the columns mix
census values counted at different filters.

**A084701**, from its checkpoint at the end of its campaign (2026-09-03):

| run | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| count | 378,622 | 159,368 | 66,928 | 28,053 | 17,784 | 2,187 | 119 | 18 | 6 | 1 | 1 |

568,720,817 survivors were classified over `[10⁶, 4.9503×10²²)`, three
times A084700's count over a line eight times shorter, because the
opening filter `n = 12` passes 34× more survivors per unit of line than
`n = 14` and the whole of period 0 was swept at it. The 61 `[NEAR]`
values are the run-16 and run-17 values that arrived while each of those
was the open term (the run-17 and run-18 counts of 1 are `a(17)` and
`a(18)` themselves; the run-14 and run-15 counts include the values
that reached those runs inside period 0 after `a(14) = a(15)` had
settled them). The frontier moved six times, at five period closes, so
these columns too mix census values counted at different filters.

## In progress — paused 2026-09-03, one family at its ceiling

**A084701 is at its ceiling.** Its campaign started on 2026-09-03 at
10:44 with no flags — the v3.1 defaults, a pool sized from a
measurement at `n = 12`, unit 210 — closed period 0 at 11:00 with
`a(12)`, `a(13)`, `a(14) = a(15)` and `a(16)` in it, found `a(17)` at
12:05 and `a(18)` at 12:42, and at 13:16 finished the last wheel period
under the family's enforced ceiling, `k_ceil(19, −1) = 4.9508×10²²` — the
deterministic Miller–Rabin bound rearranged for `prime(19)·k − 1` — and
stopped, at **`k = 49,502,931,726,851,677,944,870`** (`4.9503×10²²`,
period 1519 of the unit wheel, `5.2×10¹⁸` short of the ceiling, less
than one period). From `a(18)` the model puts `a(19)` at Q1 `2.9×10²⁴`,
median `1.0×10²⁵`, Q3 `2.8×10²⁵`, P90 `5.9×10²⁵`: **0.8% of the term lay
under the ceiling** (`E = 0.008` over the line swept for it), and none of
it was found there. The family is out of ceiling, not out of engine. Its
values' structure is on `N + 1 = prime(i)·k`, completely factored once
`k` is, so a BLS75 N+1 certificate would prove a discovery past the
crossing exactly as the N−1 route does for A084700 — but huntlib has no
N+1 test, and adding one is a new engine version with a certificate
drill at that height. With it the ceiling would be `3.317×10²⁴`, the
bound on `k` itself, under which 27% of `a(19)` lies (`a(20)`: 2%,
median `5.1×10²⁶`). A resumed `--sign -1` campaign today prints its
banner, finds no period left under the ceiling, and stops.

**A084700 is paused with `a(19)` open.** The first campaign stopped at
`k = 5.4377×10²²` on 2026-09-02 at 06:30,
not on a find but on the engine ceiling of the time — the deterministic
Miller–Rabin bound rearranged for `prime(18)·k + 1`, which the model gave
a 24% chance of holding `a(18)`. The v3 engine ([README.md](README.md))
raised the A084700 ceiling to `3.317×10²⁴` and proves a discovery past
the old crossing by BLS75 Theorem 1 certificate, and the second campaign
resumed from that cursor — **adopted** onto the unit wheel, period 88434
of `6.15×10¹⁷` becoming period 1668 of `3.26×10¹⁹`, floored, with
`1.84×10¹⁹` of overlap re-swept as a cross-check — and found `a(18)` 15.2
hours in, on 2026-09-03 at 09:34. It closed that period and stopped at
**`k = 416,293,910,387,625,631,381,020`** (`4.1629×10²³`, period 12774 of
the unit wheel), with the filter promoted to `n = 19`.

`a(19)` is a different proposition. From `a(18)` the model puts it at Q1
`4.0×10²⁴`, median `1.2×10²⁵`, Q3 `3.1×10²⁵`, P90 `6.2×10²⁵` — and the v3
ceiling is `3.317×10²⁴`, the deterministic bound on `k` itself, so
**only 22% of the term's mass lies under it** (`a(20)`: 2%). Past the
ceiling a prime factor of `k` could itself need a subproof, which
huntlib carries but this engine does not assume: raising it is a new
engine version with gates at that height. When `a(18)` landed, the
constant swept at `n = 18` sat on a shared-memory cliff at `n = 19`, 0.4×
the `n = 18` line rate; the per-filter table shipped the same day (v3.1)
runs `n = 19` at `1.2×10¹⁹ k/s`, twice the `n = 18` rate
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), [BENCHMARKS.md](BENCHMARKS.md)).

| family | frontier | open next | the campaign stands at |
|---|---|---|---|
| A084700 (`--sign +1`) | `a(18) = 416,266,897,501,398,851,227,320` (this project, 2026-09-03) | `a(19)` — model Q1 `4.0×10²⁴`, median `1.2×10²⁵`, P90 `6.2×10²⁵`; 22% under the ceiling | `k = 4.1629×10²³`, period 12774 under the v3 key, filter `n = 19` |
| A084701 (`--sign -1`) | `a(18) = 23,562,434,281,685,500,120,920` (this project, 2026-09-03) | `a(19)` — model Q1 `2.9×10²⁴`, median `1.0×10²⁵`, P90 `5.9×10²⁵`; 0.8% under the ceiling, and not found there | `k = 4.9503×10²²`, period 1519 under the v3 key at unit 210, filter `n = 19` — **at the ceiling**, `4.9508×10²²`; nothing left to sweep |

The odds model's pre-run predictions are in [README.md](README.md#the-odds-model)
and `model_results.json`.
