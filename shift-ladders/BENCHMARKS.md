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

## Wall clock at the scored rate

From each family's published frontier to each open term's model median:

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

Two things this table is not. It is not a forecast: the medians are the
model's, and this repo's first-occurrence models run about 3× late, so
multiply by 2-3 before expecting a term (README, "The odds model"). And it
is not the ceiling of what the hardware can do — see OPTIMIZATION_LOG.md
for the phase table, and for the hypotheses that were built and measured at
1.00.

What it *is* is a change in which legs are worth running. At v1, `a(21)` of
A130003 was four months of wall clock and A110096's `a(19)` most of a year;
at v2 every open term either model has a prediction for — three apiece —
sits inside a week at the median, and the two published frontiers are two
and a half minutes away. Even at 3× the median, which is what this repo's
models have actually done, the whole table is a fortnight.

Wall clock of the tools themselves, so they can be planned against the
five-minute rule: `launch.py --selftest` ~60 s, `score.py` ~90 s.
