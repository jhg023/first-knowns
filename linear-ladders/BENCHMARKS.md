# BENCHMARKS — linear-ladders

`python score.py` prints a SCORE only if every correctness gate is green
**and** all six frozen shapes reproduce their work fingerprints exactly.
An engine that skips work fails the fingerprint; an engine that breaks the
mathematics fails the gates. Either way it scores nothing.

The reported rate is end-to-end **k-line per second** — the quantity a hunt
is actually paid in — divided by 10⁶. The candidate rate is printed beside
it because the two say different things: line rate is what the campaign
buys, candidate rate is what the kernel does, and the wheel is the exchange
rate between them. Here that exchange rate is extreme: forced divisibility
by every prime to 13 (README.md, "The mathematics of the engine") leaves
`8.6×10⁻⁹` of the line as candidates at A088250's opening filter and
`8.3×10⁻¹⁰` at n = 17, so a candidate rate of `2.5×10¹¹` per second is a
line rate of `2.9×10²⁰` k per second — 47× the prime ladders' live rate
from the same kernel.

## The shapes

| shape | family | filter | wheel | sieve | window | denominated in | fingerprint (count / xor) |
|-------|--------|--------|-------|-------|--------|----------------|---------------------------|
| `SCORE` | A088250 | n = 15 | (31], (41], (53] at unit 30030 | 65536 | period 1, from `3.2589×10¹⁹` | 64 launches (`7.96×10¹⁸` of line) | 16439 / 37540909221740710330 |
| `SCORE17` | A088250 | n = 17 | (31], (41], (53] at unit 30030 | 65536 | periods 1–2, from `3.2589×10¹⁹` | 2 periods (`6.52×10¹⁹` of line) | 1601 / 28544938847964392360 |
| `SCOREM` | A125838 | n = 15 | (31], (41], (53] at unit 30030 | 65536 | period 1, from `3.2589×10¹⁹` | 64 launches (`2.79×10¹⁸` of line) | 46093 / 8927501652700787704 |
| `SCORE2L` | A088250 | n = 15 | (23], (37] | 65536 | 6,656 periods from `7.0003×10¹⁷` | periods (`4.94×10¹⁶` of line) | 123 / 706879083926370176 |
| `SCORE1L` | A088250 | n = 15 | ≤ 23 | 65536 | **the same absolute window**, 221,398,528 periods | periods | 123 / 706879083926370176 |
| `SCORE10` | A088250 | n = 10 | ≤ 13 | 4096 | 60,000,000 periods from `1.0000×10¹¹` | periods (`1.80×10¹²` of line) | 1786 / 1835032199166 |

`SCORE` and `SCOREM` are denominated in kernel **launches** because a
unit-wheel period is `3.26×10¹⁹` of k line — 1.5 s of device at n = 15 and
4.5 s at A125838's opening; 64 launches is 64 × 130 of the 34,048
third-level residues a period holds at n = 15 (64 × 50 of 37,323 for
A125838), and just as reproducible a set of candidates. `SCORE17` is
denominated in whole periods because a period at n = 17 is only 26
launches (a tenth of a second): two periods are 52 launches. The k-space
shapes sweep whole periods of their own wheels.

`SCORE1L` is the one to understand. It sweeps the *identical absolute
window* as `SCORE2L` on the one-level wheel — 33,263× as many periods,
because `W(2L) = W(1L) × 33263` exactly (29 · 31 · 37) — and it must return
the same 123 survivors and the same checksum. Two different wheels
enumerating the same candidates by different arithmetic, so a bug in the
CRT lift shows up inside the benchmark rather than as a wrong answer months
later. It did return them, on the first run. The same cross-wheel check
guards the production unit wheel as a gate rather than a shape (G17): the
unit wheel must return the k-space wheel (23],(37],(47]'s identical 1,304
survivors over one of its periods at n = 15.

## Ledger

| date | engine | SCORE | SCORE17 | SCOREM | SCORE2L | SCORE1L | SCORE10 | battery |
|------|--------|-------|---------|--------|---------|---------|---------|---------|
| 2026-09-03 | v1 | **22,213,403,242,865** | **309,319,190,496,309** | **7,131,893,874,253** | 3,368,117,521,997 | 41,199,194,529 | 8,632,986 | 41/41 green, 75 s; score.py 76 s |

(The same engine scored 21,407,278,511,282 / 294,871,274,161,029 /
7,571,590,933,335 / 3,404,003,626,419 / 42,088,614,730 / 8,736,750 an hour
earlier on the same day, every fingerprint identical: a 4–6% band between
two unpaired runs is the ambient load OPTIMIZATION.md rule 3 warns about,
and the reason every comparison in the log is paired.)

In physical units:

| shape | line rate | candidate rate |
|-------|-----------|----------------|
| `SCORE` | `2.22×10¹⁹ k/s` | `1.90×10¹¹ /s` |
| `SCORE17` | `3.09×10²⁰ k/s` | `2.58×10¹¹ /s` |
| `SCOREM` | `7.13×10¹⁸ k/s` | `1.75×10¹¹ /s` |
| `SCORE2L` | `3.37×10¹⁸ k/s` | `1.43×10¹¹ /s` |
| `SCORE1L` | `4.12×10¹⁶ k/s` | `1.18×10¹⁰ /s` |
| `SCORE10` | `8.63×10¹² k/s` | `8.62×10⁸ /s` |

Read the candidate column against the line column. `SCORE17` and `SCORE`
run the same wheel and the same kernel and differ 14× in line for 1.3× in
candidates: at n = 17 the wheel lets one candidate in `1.2×10⁹` of the
line through, at n = 15 one in `1.2×10⁸`, because every extra condition
kills one more residue per wheel prime. `SCOREM` is a -1 family's
*opening* filter, where the forms are `r·k − 1` for `r = 2..15` — one
condition fewer than A088250 at the same n — so its wheel is 2.9× denser
and its line rate a third; the sign itself costs nothing (the two w-classes
compile to the same kernel source).

## Wall clock at the scored rate

The per-filter rates measured for every opening the launcher has
(OPTIMIZATION_LOG.md, all at the production wheel with the shipped
constants) convert the model's depths ([README.md](README.md#the-odds-model))
into wall clock. For A088250, from its frontier:

| term | Q1 | median | Q3 | P90 | at the filter's rate |
|------|----|--------|----|-----|----------------------|
| a(15), at n = 15 (`2.1×10¹⁹ k/s`) | `7.1×10¹⁹` | `2.0×10²⁰` | `4.9×10²⁰` | `9.7×10²⁰` | median **9 s**, P90 46 s; inside period 0 (`3.26×10¹⁹`, 1.5 s per period) with 96% probability |
| a(16), at n = 16 (`8.0×10¹⁹ k/s`) | `6.5×10²¹` | `2.3×10²²` | `6.2×10²²` | `1.3×10²³` | median **4.8 min**, P90 27 min |
| a(17), at n = 17 (`2.9×10²⁰ k/s`) | `4.7×10²³` | `1.7×10²⁴` | `4.5×10²⁴` | `9.2×10²⁴` | median **1.6 h**; the ceiling `3.317×10²⁴` is 3.1 h away and holds 68% of the term |
| a(18) | `6.0×10²⁵` | | | | 4% under the ceiling |

So the whole A088250 campaign, opening to ceiling, is about **three and a
half hours** of device at the scored rates, and it is expected to return
`a(15)`, `a(16)` and — with 68% probability — `a(17)`, then stop at the
ceiling with `a(18)` almost certainly above it. The siblings, from their
own frontiers at their own opening rates (OPTIMIZATION_LOG.md), with the
expected number of terms under each ceiling:

| family | opening rate | to the ceiling at the opening rate | terms expected under the ceiling |
|---|---|---|---|
| A125838 (n = 15) | `7.6×10¹⁸ k/s` | `2.2×10²³`: 8.1 h at the opening rate, far less after the promotions (each ~3×) | a(15), a(16), a(17); a(18) 13% |
| A125839 (n = 16) | `7.8×10¹⁸ k/s` | `2.1×10²³`: 7.4 h at the opening rate | a(16), a(17), a(18); a(19) 18% |
| A173750 (n = 16) | `2.4×10¹⁹ k/s` | `3.3×10²⁴`: hours, mostly at n = 18 | a(16), a(17); a(18) 66% |
| A164326 (n = 15) | `1.0×10¹⁹ k/s` | `1.1×10²³`: 3 h at the opening rate | a(15), a(16); a(17) 16% |
| A164325 (n = 16) | `2.7×10¹⁹ k/s` | `3.3×10²⁴`: hours, mostly at n = 17 | a(16); a(17) 85% |
| A088651 (n = 16) | `8.8×10¹⁹ k/s` | `2.1×10²³`: **39 min** | a(16) 96%; a(17) 15% |

Every -1 family's ceiling is its proof crossing — the deterministic
Miller–Rabin bound rearranged for its largest form — because its values'
structure is on `N + 1`, for which huntlib has no certificate; the +1
families run to the bound on k itself with BLS75 certificates past their
crossings (README.md). Budget two to three times the medians above before
expecting a term: this repository's finds land at 1.9–2.5× their medians
on average.
