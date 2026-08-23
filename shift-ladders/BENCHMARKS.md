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

| shape | base | filter | wheel | sieve | window | fingerprint (count / xor) |
|-------|------|--------|-------|-------|--------|---------------------------|
| `SCORE` | 4 | n = 19 | ≤ 23 | 65536 | 8,192 periods from `1.0000×10¹⁵` | 7 / 998631924604311 |
| `SCORE1L` | 4 | n = 19 | ≤ 13 | 65536 | **the same absolute window**, 60,858,368 periods | 7 / 998631924604311 |
| `SCORE2` | 2 | n = 17 | ≤ 37 | 65536 | 2,048 periods from `1.0018×10¹⁵` | 59 / 17289912876387275 |
| `SCORE4W` | 4 | n = 19 | ≤ 13 | 1024 | 10,000,000 periods from `1.0000×10¹⁵` | 5014 / 694483282552 |
| `SCORE10` | 4 | n = 10 | ≤ 13 | 4096 | 2,000,000 periods from `1.0000×10¹⁵` | 58213 / 999951251185409 |

The `wheel` column is the **flat residue table's** top, which is what sets
`W` and therefore what the window means. From v2 the wheel goes further
than that — bit planes over the period index carry it to 47-113 depending
on the configuration — but those primes do not enter `W`, so **every window
above still describes the same span of the m line it described in v1, and
every fingerprint is the same fingerprint.** That is the property that
makes a wheel change safe to make under a frozen benchmark: folding a prime
into the wheel removes candidates, never survivors.

`SCORE1L` is the one to understand. It sweeps the *identical absolute
window* as `SCORE` on a coarser flat wheel — 7,429× as many periods,
because `W(23) = W(13) × 7429` — and it must return the same seven
survivors and the same checksum.

## Ledger

### v2 — 2026-08-23, the bit-plane wheel and a compacted test loop

Medians of interleaved paired rounds against v1, every fingerprint checked
on every run, machine otherwise idle:

| shape | rate | candidates/s | SCORE | v1 | **ratio** |
|-------|------|--------------|-------|----|-----------|
| `SCORE` | 3.19×10¹⁴ m/s | 1.98×10¹⁰ | **319,266,425** | 4,461,600 | **82.9×** |
| `SCORE1L` | 4.31×10¹³ m/s | 2.55×10¹⁰ | 43,086,561 | 1,066,100 | 46.6× |
| `SCORE2` | 1.20×10¹⁸ m/s | 7.20×10⁹ | **1,198,913,847,806** | 30,611,000,000 | 49.1× |
| `SCORE4W` | 4.88×10¹³ m/s | 2.89×10¹⁰ | 48,761,874 | 1,007,900 | 58.4× |
| `SCORE10` | 2.84×10¹² m/s | 8.63×10⁸ | 2,842,848 | 460,960 | 7.2× |

The ratio column is the median of seven **per-round** ratios measured back
to back in one session, not two score runs divided (OPTIMIZATION.md rule 3);
the SCORE column is what `score.py` printed on the same machine the same
afternoon. `SCORE10` is the outlier and it is the shape that says so on
purpose: at `n = 10` the survival curve is shallow, so 93% of that shape's
time is in the tail and the wheel has much less to remove.

**The candidate column now means something different from v1's.** v1's
candidates were the flat wheel's residues; v2's are what survives the bit
planes as well, which is about a hundredth as many. Read the ratio of the
two columns as the wheel's exchange rate and nothing else.

**`SCORE` sustained is 3.03×10⁸, not 3.19×10⁸**, and the gap is the one
thing in this file a reader should not skip. The frozen `SCORE` window is
8,192 periods, which is **a quarter of one production launch** at the v2
engine, so every quantity the engine sizes from `per_launch` is
under-exercised by it — and one of them, the global tail queue, was
mis-tuned on exactly that blind spot before the sustained measurement
caught it (OPTIMIZATION_LOG.md, "The correction"). The engine now reports
`q3_short` in `config()` when that ceiling binds, because the score cannot.

Run-to-run spread is 10-15% on these shapes, measured rather than assumed:
in one sweep two configurations that compile to the *same binary* measured
1.000 and 1.119 apart. Nothing here that turns on less than about 1.10 was
decided on a single number.

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
bandwidth-sensitive where the coarse-wheel shapes were not. v2's planes are
a few hundred KB and that particular noise source is gone; what is left is
ordinary clock drift.

## Wall clock at the scored rate

What the v2 engine buys, from each family's published frontier to each open
term's model median, at the **sustained** rate:

| target | from | median | line to sweep | v1 | **v2** |
|--------|------|--------|---------------|----|--------|
| A130003 `a(19)` | `1.16×10¹⁵` | `5.75×10¹⁶` | `5.6×10¹⁶` | 3.5 h | **3.1 min** |
| A130003 `a(20)` | " | `1.42×10¹⁸` | `1.4×10¹⁸` | 87 h | **1.3 h** |
| A130003 `a(21)` | " | `4.73×10¹⁹` | `4.7×10¹⁹` | 122 d | **1.8 d** |
| A110096 `a(17)` | `1.44×10¹⁷` | `2.03×10²⁰` | `2.0×10²⁰` | 1.8 h | **1.8 min** |
| A110096 `a(18)` | " | `1.74×10²²` | `1.7×10²²` | 6.6 d | **2.5 h** |
| A110096 `a(19)` | " | `5.67×10²³` | `5.7×10²³` | 214 d | **3.5 d** |

at 3.03×10¹⁴ m/s for `b = 4` and 1.87×10¹⁸ m/s for `b = 2`, both measured
over a multi-launch span rather than read off a benchmark window.

**One measured 1.198x is deliberately not in these numbers.** Raising `p1`
from 23 to 29 halves the flat table's density and so halves the cost of the
dominant phase; it is measured, it is the last step `RES_MAX` allows, and
it is left unshipped because `p1` sets `W` and `W` is the unit every window
in the table above is expressed in. Amending the frozen shapes is a
human's call, not an optimization pass's (OPTIMIZATION.md 2.13); both
options are set out in OPTIMIZATION_LOG.md.

Two things this table is not. It is not a forecast: the medians are the
model's, and this repo's first-occurrence models run about 3× late, so
multiply by 2-3 before expecting a term (README, "The odds model"). And it
is not the ceiling of what the hardware can do — see OPTIMIZATION_LOG.md
for what is still priced and unbuilt.

What it *is* is a change in which legs are worth running. At v1, `a(21)` of
A130003 was four months of wall clock and A110096's `a(19)` was most of a
year; at v2 every open term the odds model has a prediction for — three
apiece — sits inside a week at the median, and the two published frontiers
are three minutes and two minutes away. Even at 3× the median, which is
what this repo's models have actually done, the whole of that table is a
fortnight.

Wall clock of the tools themselves, so they can be planned against the
five-minute rule: `launch.py --selftest` ~45 s, `score.py` ~70 s.
