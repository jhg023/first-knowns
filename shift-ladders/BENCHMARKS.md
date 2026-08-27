# BENCHMARKS — shift-ladders

`python score.py` prints a SCORE only if every correctness gate is green
**and** all five frozen shapes reproduce their work fingerprints exactly.
An engine that skips work fails the fingerprint; an engine that breaks the
mathematics fails the gates. Either way it scores nothing.

The reported rate is end-to-end **m-line per second** — `blocks × W /
wall`, the quantity a hunt is actually paid in — divided by 10⁶. The
candidate rate is printed beside it because the two say different things:
line rate is what the campaign buys, candidate rate is what the kernel
does, and the wheel is the exchange rate between them.

## The shapes

| shape | base | filter | flat wheel | sieve | window | launches | fingerprint (count / xor) |
|-------|------|--------|-----------|-------|--------|----------|---------------------------|
| `SCORE` | 4 | n = 19 | ≤ 29 | 65536 | 4,096 periods from `1.000001×10¹⁵` | 4 | 73 / 1038246173448745 |
| `SCORE1L` | 4 | n = 19 | ≤ 13 | 65536 | **the same absolute window**, 882,446,336 periods | 27 | 73 / 1038246173448745 |
| `SCORE2` | 2 | n = 17 | ≤ 37 | 65536 | 2,048 periods from `1.0018×10¹⁵` | ½ | 59 / 17289912876387275 |
| `SCORE4W` | 4 | n = 19 | ≤ 13 | 1024 | 10,000,000 periods from `1.0000×10¹⁵` | ⅓ | 5014 / 694483282552 |
| `SCORE10` | 4 | n = 10 | ≤ 13 | 4096 | 2,000,000 periods from `1.0000×10¹⁵` | ¹⁄₁₇ | 58213 / 999951251185409 |

The `flat wheel` column is the **residue table's** top, which is what sets
`W` and therefore what the window means. The wheel goes further than that —
bit planes over the period index carry it to 47-113 depending on the
configuration — but those primes do not enter `W`, so a change to *them*
leaves every window and every fingerprint alone. That is the property that
makes a plane change safe under a frozen benchmark: folding a prime into
the wheel removes candidates, never survivors.

`p1` is the exception, and it moved once: 23 → 29 at base 4, for a measured
1.198×. `SCORE` and `SCORE1L` were re-frozen for it (see the ledger); the
other three shapes do not use that wheel and were not touched.

`SCORE1L` is the one to understand. It sweeps the *identical absolute
window* as `SCORE` on a coarser flat wheel — 215,441× as many periods,
because `W(29) = W(13) × 215,441` exactly — and it must return the same 73
survivors and the same checksum. Two different wheels enumerating the same
candidates by different arithmetic, so a bug in the CRT lift or in a bit
plane shows up inside the benchmark rather than as a wrong answer months
later.

**The `launches` column is load-bearing and it is new.** A window narrower
than one launch cannot exercise anything the engine sizes *per launch* —
and that is not hypothetical: the global tail queue was tuned on exactly
that blind spot and shipped 1.19× slow before a multi-launch measurement
caught it. `SCORE`'s window was widened to four launches when it was
re-frozen, and the effect on the benchmark's own quality is the clearest
result in this file:

| shape | window vs one launch | spread over 3 `score.py` runs |
|---|---|---|
| `SCORE` (old, 8,192 periods at `W(23)`) | ¼ | **31%** |
| `SCORE` (new, 4,096 periods at `W(29)`) | 4× | **2.4%** |
| `SCORE1L` (new) | 27× | **0.2%** |
| `SCORE2` | ½ | 23% |
| `SCORE4W` | ⅓ | 33% |

The three that still sit inside one launch are the three that still swing
by a quarter or more. They are left alone because they under-report rather
than over-report — the sustained `b = 2` rate measures ~1.9×10¹⁸ against
`SCORE2`'s 1.5×10¹⁸ — and because moving a frozen anchor is not a thing an
optimization pass does on its own. Recorded here so the next person can see
the margin.

## Ledger

### v2 — 2026-08-23, the bit-plane wheel, a compacted test loop, `p1` = 29

| shape | rate | candidates/s | SCORE (median of 3) | spread |
|-------|------|--------------|---------------------|--------|
| `SCORE` | 3.57×10¹⁴ m/s | 2.21×10¹⁰ | **356,942,342** | 2.4% |
| `SCORE1L` | 5.53×10¹³ m/s | 3.27×10¹⁰ | 55,293,477 | 0.2% |
| `SCORE2` | 1.53×10¹⁸ m/s | 9.19×10⁹ | **1,530,341,835,472** | 23% |
| `SCORE4W` | 4.66×10¹³ m/s | 2.76×10¹⁰ | 46,634,780 | 33% |
| `SCORE10` | 2.80×10¹² m/s | 8.50×10⁸ | 2,801,972 | 2% |

**Against v1, measured over a COMMON ABSOLUTE WINDOW** with the two
survivor streams compared to each other — a period-indexed A/B would be
comparing different spans now that `W` has moved:

| family | v1 | v2 | ratio |
|---|---|---|---|
| A130003, `b = 4` | 4.17×10¹² m/s | **3.54×10¹⁴ m/s** | **84.8×** [84.7, 85.5] |
| A110096, `b = 2` | 2.90×10¹⁶ m/s | **1.29×10¹⁸ m/s** | **44.6×** [41.9, 47.4] |

**The candidate column means something different from v1's.** v1's
candidates were the flat wheel's residues; v2's are what survives the bit
planes as well, which is about a hundredth as many. Read the ratio of the
rate and candidate columns as the wheel's exchange rate and nothing else.

The old `SCORE` / `SCORE1L` shape, for the record, since its number is not
comparable to the new one: 8,192 periods from `j0 = 4,482,439` at
`W(23) = 223,092,870` (and 60,858,368 from `j0 = 33,300,039,331` at
`W(13)`), fingerprint **7 / 998631924604311**, on which v1 scored
4,461,600 and the v2 engine at `p1 = 23` scored 319,266,425.

### v1 — 2026-08-23, the first engine (flat wheel table, Barrett test loop)

| shape | rate | candidates/s | run-to-run spread | SCORE |
|-------|------|--------------|-------------------|-------|
| `SCORE` | 4.46×10¹² m/s | 3.15×10¹⁰ | **51%** | **4,461,600** |
| `SCORE1L` | 1.07×10¹² m/s | 3.58×10¹⁰ | 13% | 1,066,100 |
| `SCORE2` | 3.06×10¹⁶ m/s | 2.22×10¹⁰ | 20% | 30,611,000,000 |
| `SCORE4W` | 1.01×10¹² m/s | 3.38×10¹⁰ | 11% | 1,007,900 |
| `SCORE10` | 4.61×10¹¹ m/s | 1.55×10¹⁰ | 12% | 460,960 |

v1's `SCORE` did not resolve to better than about ±25%, because its 12.6 MB
residue table was streamed once per launch and made the production shape
bandwidth-sensitive where the coarse-wheel shapes were not.

## What the benchmark predicted, and what the campaign did

From each family's published frontier to each open term's model median.
This table was written **before** the sweep and is left exactly as it was,
so the prediction can be read against the outcome below it:

| target | from | median | line to sweep | v1 | **v2** |
|--------|------|--------|---------------|----|--------|
| A130003 `a(19)` | `1.16×10¹⁵` | `5.75×10¹⁶` | `5.6×10¹⁶` | 3.5 h | **2.6 min** |
| A130003 `a(20)` | " | `1.42×10¹⁸` | `1.4×10¹⁸` | 87 h | **1.1 h** |
| A130003 `a(21)` | " | `4.73×10¹⁹` | `4.7×10¹⁹` | 122 d | **1.5 d** |
| A110096 `a(17)` | `1.44×10¹⁷` | `2.03×10²⁰` | `2.0×10²⁰` | 1.8 h | **2.2 min** |
| A110096 `a(18)` | " | `1.74×10²²` | `1.7×10²²` | 6.6 d | **3.1 h** |
| A110096 `a(19)` | " | `5.67×10²³` | `5.7×10²³` | 214 d | **4.3 d** |

at 3.57×10¹⁴ m/s for `b = 4` and 1.53×10¹⁸ m/s for `b = 2` — the scored
rates, which for `b = 2` is the conservative one (its sustained rate over
several launches measures ~1.9×10¹⁸).

**What actually happened**, 2026-08-23/24 ([RESULTS.md](RESULTS.md)):

| term | predicted at the median | found at | wall clock into the campaign |
|------|------------------------|----------|------------------------------|
| A130003 `a(19)` | 2.6 min | `1.33×10¹⁶` | **117 s** |
| A130003 `a(20)` | 1.1 h | `6.12×10¹⁸` | **12.04 h** |
| A110096 `a(17)` | 2.2 min | `3.06×10²⁰` | **9.5 min** |
| A110096 `a(18)` | 3.1 h | `7.60×10²⁰` | **15.8 min** |

Four terms for 18.1 h of one GPU. Where a row missed it missed for two
separable reasons, and both are scored rather than averaged: the depth the
term actually sat at is in [README.md](README.md#the-odds-model), and the
rate the campaign actually ran at is here.

### The campaign rate is not the scored rate

Measured end to end from each checkpoint's own `elapsed` and swept `m`:

| | line swept | wall clock | end-to-end | last stretch | same configuration, free GPU |
|---|---|---|---|---|---|
| A130003 (`b = 4`) | `8.95×10¹⁸` | 17.44 h | `1.42×10¹⁴ m/s` | `1.45×10¹⁴` (n = 21) | `5.08×10¹⁴ m/s` (n = 21 at the cursor) |
| A110096 (`b = 2`) | `3.62×10²¹` | 38.2 min | `1.58×10¹⁸ m/s` | `2.12×10¹⁸` (n = 19) | `5.21×10¹⁸ m/s` (n = 19 at the cursor) |

The campaigns bought **29% and 41%** of what the kernel does in the same
configuration, and that gap was larger than anything left in the kernel.
Measured per launch — the campaign's own unit — it was a fixed **32.0 ms
and 32.3 ms** on two families whose launches differ by four orders of
magnitude in line swept, and it was traced: **`check_rungs` rebuilt the
whole progress ladder from the odds model once per segment**, 1,080
numerical integrals at 0.509 ms each — 578 ms and 541 ms, or 36.1 and
33.8 ms per launch. A 17-hour base-4 campaign spent about four fifths of
its wall clock recomputing an answer that changes only when a term is
found.

**FIXED.** The ladder is cached on the frontier
(`huntlib.rungs.LiveLadder`). Measured paired and interleaved on the real
segment loop, median of three rounds:

| | campaign | after | ratio |
|---|---|---|---|
| A130003 (`b = 4`, n = 21) | `1.45×10¹⁴ m/s` | **`5.05×10¹⁴ m/s`** | **3.47×** |
| A110096 (`b = 2`, n = 19) | `2.12×10¹⁸ m/s` | **`5.12×10¹⁸ m/s`** | **2.42×** |

landing on the free-GPU device rates measured independently
(`5.08×10¹⁴`, `5.21×10¹⁸`), which is the check that nothing else was
hiding in the budget. The segment loop is now **94.7% and 89.8% device**:

| per launch | base 4, n = 21 | base 2, n = 19 |
|---|---|---|
| sweep (device) | 12.44 ms — 94.7% | 21.33 ms — 89.8% |
| classify | 0.17 ms — 1.3% | 1.84 ms — 7.8% |
| checkpoint | 0.52 ms — 3.9% | 0.57 ms — 2.4% |
| rungs | **0.00 ms** | **0.00 ms** |
| **total** | **13.13 ms** | **23.75 ms** |

The budget, the two further candidates measured at 1.00 and declined, and
the drills that keep the cache honest are in
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

One thing the campaign settled in the engine's favour: **a higher filter is
faster**, monotonically. At the base-4 cursor the same 4,096-period window
sweeps at `4.34 / 4.90 / 5.32 ×10¹⁴ m/s` at `n = 19 / 20 / 21`, because a
longer killed set removes more of the line per prime. Every term this
project finds makes the next one cheaper per unit line — the opposite of
the usual, and worth knowing before pricing `a(22)`.

### Where the next terms sit

From the cursors each campaign is paused at, at the **post-fix** rate, with
the pre-fix column kept so the change is legible:

| target | from | median | line to sweep | old rate | **now** |
|--------|------|--------|---------------|----------|---------|
| A130003 `a(21)` | `8.95×10¹⁸` | `8.45×10¹⁹` | `7.6×10¹⁹` | 6.0 d | **1.7 d** |
| A130003 `a(22)` | " | `1.93×10²¹` | `1.9×10²¹` | 153 d | 44 d |
| A110096 `a(19)` | `3.62×10²¹` | `5.82×10²³` | `5.8×10²³` | 3.2 d | **1.3 d** |
| A110096 `a(20)` | " | `2.07×10²⁵` | `2.1×10²⁵` | 113 d | 47 d — and only 19% of it is under the engine's ceiling |

at `5.05×10¹⁴ m/s` for `b = 4` and `5.12×10¹⁸ m/s` for `b = 2`, both
measured on the segment loop rather than on the benchmark.

Two things this table is not. It is not a forecast: the medians are the
model's, and this repo's ladder models run about 2× late pooled over eleven
finds, so multiply before expecting a term (README, "The odds model"). And
it is no longer far from what the hardware can do — the loop is 90-95%
device now, so the next real gain would have to come out of the kernel,
where the largest measured item left is 5%.

Wall clock of the tools themselves, so they can be planned against the
five-minute rule: `launch.py --selftest` ~60 s, `score.py` ~90 s.
