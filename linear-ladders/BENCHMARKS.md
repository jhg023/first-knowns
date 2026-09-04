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
`6.4×10⁻⁹` of the line as candidates at A088250's opening filter and
`5.9×10⁻¹⁰` at n = 17, so a candidate rate of `2.4×10¹¹` per second is a
line rate of `4.0×10²⁰` k per second — 60× the prime ladders' live rate
from the same kernel.

## The shapes

| shape | family | filter | wheel | sieve | window | denominated in | fingerprint (count / xor) |
|-------|--------|--------|-------|-------|--------|----------------|---------------------------|
| `SCORE` | A088250 | n = 15 | (37], (47], (59] at unit 30030 | 65536 | period 1, from `1.9228×10²¹` | 24 launches (`2.76×10¹⁹` of line) | 56165 / 247205394479927860656 |
| `SCORE17` | A088250 | n = 17 | (37], (47], (59] at unit 30030 | 65536 | period 1, from `1.9228×10²¹` | 64 launches (`1.63×10²⁰` of line) | 3957 / 2153040604752053900382 |
| `SCOREM` | A125838 | n = 15 | (37], (47], (59] at unit 30030 | 65536 | period 1, from `1.9228×10²¹` | 8 launches (`8.76×10¹⁸` of line) | 146036 / 4331048872519602054736 |
| `SCORE2L` | A088250 | n = 15 | (23], (37] | 65536 | 6,656 periods from `7.0003×10¹⁷` | periods (`4.94×10¹⁶` of line) | 123 / 706879083926370176 |
| `SCORE1L` | A088250 | n = 15 | ≤ 23 | 65536 | **the same absolute window**, 221,398,528 periods | periods | 123 / 706879083926370176 |
| `SCORE10` | A088250 | n = 10 | ≤ 13 | 4096 | 60,000,000 periods from `1.0000×10¹¹` | periods (`1.80×10¹²` of line) | 1786 / 1835032199166 |

The three unit-wheel shapes are denominated in kernel **launches** because
a unit-wheel period is `1.92×10²¹` of k line — a minute of device at n = 15
and four at A125838's opening. Below c = 17 forms a launch is one
third-level residue of the wheel (`R1 × R2` exceeds any launch budget:
`7.3×10⁹` candidates at n = 15, `2.05×10¹⁰` at A125838's opening), so 24
launches at `SCORE` are 24 of the 1,672 residues a period holds and 8 at
`SCOREM` are 8 of 1,755; at n = 17 a launch is two residues (`1.5×10⁹`
candidates) and 64 launches are 128 of 1,512. Each is a reproducible set
of candidates and about a second of device. The k-space shapes sweep whole
periods of their own wheels.

`SCORE1L` is the one to understand. It sweeps the *identical absolute
window* as `SCORE2L` on the one-level wheel — 33,263× as many periods,
because `W(2L) = W(1L) × 33263` exactly (29 · 31 · 37) — and it must return
the same 123 survivors and the same checksum. Two different wheels
enumerating the same candidates by different arithmetic, so a bug in the
CRT lift shows up inside the benchmark rather than as a wrong answer months
later. It did return them, on the first run. The same cross-wheel check
guards the production unit wheel as a gate rather than a shape (G17): v1's
unit wheel must return the k-space wheel (23],(37],(47]'s identical 1,304
survivors over one of its periods at n = 15, and the v2 wheel must return
the identical 799 survivors as *both* over `[10⁶, 3.26×10¹⁹)` at n = 17.

## Ledger

| date | engine | SCORE | SCORE17 | SCOREM | SCORE2L | SCORE1L | SCORE10 | battery |
|------|--------|-------|---------|--------|---------|---------|---------|---------|
| 2026-09-03 | v1 | 22,213,403,242,865 | 309,319,190,496,309 | 7,131,893,874,253 | 3,368,117,521,997 | 41,199,194,529 | 8,632,986 | 41/41 green, 75 s; score.py 76 s |
| 2026-09-03 | **v2** | **30,826,035,115,578** | **404,629,246,197,708** | **8,416,469,598,948** | 4,332,707,571,725 | 40,288,865,686 | 7,830,573 | 42/42 green, 88 s; score.py 97 s |
| 2026-09-04 | v3 | 28,054,713,983,765 | 372,003,148,777,901 | 7,678,166,804,168 | 3,926,953,287,006 | 37,327,360,412 | 7,427,414 | 44/44 green, 120 s; score.py ~110 s |

The v3 row is **v2's engine at every fingerprint** — v3 changed the
ceiling, the certificate routes and the resume policy and touched no
kernel, wheel or sieve constant (OPTIMIZATION_LOG.md v3) — so its
numbers are the ambient band and not a ratio: the same afternoon's
pre-change run of v2 on the same desktop scored 28,518,537,703,981 /
376,557,197,309,340 / 7,771,393,268,663, 1.6% above the v3 row and
8–9% under the ledger's v2 row, with every fingerprint identical across
all three runs.

The v2 row's three unit-wheel shapes are **new shapes** (the wheel is a
deliberate coverage change, so their windows and fingerprints moved) and
its numbers are not the v1 row's ratio: the paired, same-line comparisons
the change stands on are 1.27× at c = 15, 1.50× at 16, 1.20× at 17 and
1.32× at 18 forms, within 5% at 14 ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)
v2). The three k-space shapes are the same windows and fingerprints as
v1's; their movement (1.29×, 0.96×, 0.90×, unpaired) is the ambient band —
paired, the one v2 change that touches them (the prefix byte cap) is
1.003–1.007×. The v1 engine had itself scored 21,407,278,511,282 /
294,871,274,161,029 / 7,571,590,933,335 / 3,404,003,626,419 /
42,088,614,730 / 8,736,750 an hour before its ledger row, every
fingerprint identical: a 4–6% band between two unpaired runs is the
ambient load OPTIMIZATION.md rule 3 warns about, and the reason every
comparison in the log is paired.

In physical units (v2):

| shape | line rate | candidate rate |
|-------|-----------|----------------|
| `SCORE` | `3.07×10¹⁹ k/s` | `1.96×10¹¹ /s` |
| `SCORE17` | `3.99×10²⁰ k/s` | `2.37×10¹¹ /s` |
| `SCOREM` | `8.40×10¹⁸ k/s` | `1.57×10¹¹ /s` |
| `SCORE2L` | `4.33×10¹⁸ k/s` | `1.84×10¹¹ /s` |
| `SCORE1L` | `3.96×10¹⁶ k/s` | `1.14×10¹⁰ /s` |
| `SCORE10` | `7.78×10¹² k/s` | `7.78×10⁸ /s` |

Read the candidate column against the line column. `SCORE17` and `SCORE`
run the same wheel and the same kernel and differ 13× in line for 1.2× in
candidates: at n = 17 the wheel lets one candidate in `1.7×10⁹` of the
line through, at n = 15 one in `1.6×10⁸`, because every extra condition
kills one more residue per wheel prime. `SCOREM` is a -1 family's
*opening* filter, where the forms are `r·k − 1` for `r = 2..15` — one
condition fewer than A088250 at the same n — so its wheel is 2.9× denser
and its line rate a quarter; the sign itself costs nothing (the two
w-classes compile to the same kernel source), and its lower candidate rate
is the sixth prefix group that filter's survival curve asks for.

## Wall clock at the scored rate

The per-filter rates measured for every opening the launcher has
(OPTIMIZATION_LOG.md v2, all at the production wheel with the shipped
constants) convert the model's depths ([README.md](README.md#the-odds-model))
into wall clock. For A088250, from its frontier:

| term | Q1 | median | Q3 | P90 | at the filter's rate |
|------|----|--------|----|-----|----------------------|
| a(15), at n = 15 (`3.0×10¹⁹ k/s`) | `7.1×10¹⁹` | `2.0×10²⁰` | `4.9×10²⁰` | `9.7×10²⁰` | median **7 s**, P90 32 s — but inside period 0 (`1.92×10²¹`, 64 s per period) with 96% probability, so narrated when that period closes, about a minute in |
| a(16), at n = 16 (`1.4×10²⁰ k/s`) | `6.5×10²¹` | `2.3×10²²` | `6.2×10²²` | `1.3×10²³` | median **2.8 min**, P90 16 min |
| a(17), at n = 17 (`4.0×10²⁰ k/s`) | `4.7×10²³` | `1.7×10²⁴` | `4.5×10²⁴` | `9.2×10²⁴` | median **1.2 h**; the ceiling `3.317×10²⁴` is 2.3 h away and holds 68% of the term |
| a(18), at n = 18 (`1.4×10²¹ k/s`) | `6.0×10²⁵` | | | | 4% under the ceiling |

So the whole A088250 campaign, opening to ceiling, was budgeted at about
**two and a half hours** of device at the scored rates (three and a half
on v1), returning `a(15)`, `a(16)` and — with 68% probability — `a(17)`,
then stopping at the ceiling with `a(18)` almost certainly above it. **It
ran on 2026-09-03 in 1.26 h and did exactly that** ([RESULTS.md](RESULTS.md)):
every filter at its benchmark's rate, and the whole shorter than the
budget because `a(17)` landed at half its median and the remaining line
went at the n = 18 rate. The siblings, from their own frontiers at their
own opening rates (OPTIMIZATION_LOG.md v2), with the expected number of
terms under each ceiling:

| family | opening rate | to the ceiling at the opening rate | terms expected under the ceiling |
|---|---|---|---|
| A125838 (n = 15) | `8.4×10¹⁸ k/s` | `2.2×10²³`: 7.3 h at the opening rate, far less after the promotions (each ~3–4×). **Ran 2026-09-03 in 17 min**: a(15), a(16), a(17) and a(18) found, a(19) > `1.73×10²³` ([RESULTS.md](RESULTS.md)) | a(15), a(16), a(17); a(18) 13% |
| A125839 (n = 16) | `8.4×10¹⁸ k/s` | `2.1×10²³`: 7 h at the opening rate. **Ran 2026-09-03 in 15 min**: a(16), a(17), a(18) found, a(19) > `1.73×10²³` | a(16), a(17), a(18); a(19) 18% |
| A173750 (n = 16) | `3.0×10¹⁹ k/s` | `3.3×10²⁴`: hours, mostly at n = 18 (`1.4×10²¹`). **Ran 2026-09-03 in 37 min**: a(16), a(17) and a(18) = a(19) found, a(20) > `3.32×10²⁴` | a(16), a(17); a(18) 66% |
| A164326 (n = 15) | `1.25×10¹⁹ k/s` | `1.1×10²³`: 2.4 h at the opening rate. **Ran 2026-09-03 in 14 min**: a(15), a(16) found, a(17) > `1.0×10²³` | a(15), a(16); a(17) 16% |
| A164325 (n = 16) | `3.75×10¹⁹ k/s` | `3.3×10²⁴`: hours, mostly at n = 17. **Ran 2026-09-03 in 60 min**: a(16), a(17), a(18) found, a(19) > `3.32×10²⁴` | a(16); a(17) 85% |
| A088651 (n = 16) | `1.44×10²⁰ k/s` | `2.1×10²³`: **24 min**. **Ran 2026-09-04 in 12 min**: a(16) found, a(17) > `1.94×10²³` | a(16) 96%; a(17) 15% |

Those were the v2 ceilings: the −1 families' proof crossings (no N+1
certificate existed) and the deterministic bound on k for the +1
families. **v3 raised every ceiling to `10⁴⁰`** (README.md; the N+1 route
and the recursion in huntlib.certificate, the measured budget in
huntlib.ceiling), and each campaign resumes from its v2 cursor at the
filter after its frontier. The resumed filters, priced on the campaign's
own next launches (OPTIMIZATION_LOG.md v3, Measurement 1):

| family | resumes at | device | the campaign's own rate at that filter (RESULTS.md) | next filter |
|---|---|---|---|---|
| A088250 | n = 18 | `1.39×10²¹ k/s` | `1.49×10²¹` | n = 19 `2.8×10²¹`, n = 20 `6.3×10²¹` |
| A173750 | n = 20 | `2.86×10²¹` | `3.0×10²¹` | n = 21 `6.3×10²¹` (c = 20, swept 2026-09-04) |
| A164325 | n = 19 | `1.78×10²¹` | `1.82×10²¹` | n = 20 `3.7×10²¹` (c = 20, odd wheel) |
| A125838 | n = 19 | `7.05×10²⁰` | `7.2×10²⁰` | n = 20: 19 forced, A088250's n = 19 wheel |
| A125839 | n = 19 | `2.51×10²⁰` | `2.7×10²⁰` | n = 20: the `2..n` n = 19 wheel, `7.2×10²⁰` |
| A164326 | n = 17 | `1.85×10²⁰` | `1.95×10²⁰` | n = 18 `5×10²⁰` (A164325's n = 18) |
| A088651 | n = 17 | `3.77×10²⁰` | `3.9×10²⁰` | n = 18: A088250's n = 18 wheel, `1.45×10²¹` |

Budget two to three times the medians before expecting a term: this
repository's finds land at 1.9–2.5× their medians on average.

**The later filters of the `2..n` and `3..n` families are slower than
A088250's at the same form count, and that is the wheel, not the
kernel.** Those families force each small prime one or two filters later
(`2..n` forces `q` from `n = q + 1`, `3..n` from `q + 2`), so at the
filters where the prime `n` or `n − 1` is not yet forced it keeps two or
three residues in the wheel instead of one. Measured paired against
A088250 at the same form count (OPTIMIZATION_LOG.md v2, "What the
campaigns measured"): A125839 n = 18 `6.5×10¹⁹ k/s` (0.50× of A088250's
n = 16), A125839 n = 19 `2.4×10²⁰` (0.66× of n = 17); A125838's n = 17
and n = 19 are the same two wheels (`7.2×10¹⁹` and `7.2×10²⁰` in its
campaign). Its n = 18 has every prime forced and runs at A088250's n = 17
rate. The odd families (`A164325`, `A164326`) have their own wheels from
n = 17 on for a different reason: the odd multipliers `1, 3, …, 33` cover
only 16 nonzero residues modulo 19, 23, 29 and 31 where `1..17` cover 17,
so their first wheel level is 81,900 residues to A088250's 40,320 —
paired, A164326 at n = 17 is `1.8×10²⁰ k/s` (0.49× of A088250's n = 17)
and A164325 at n = 18 `4.9×10²⁰` (0.48× of n = 18). Their openings are
in Measurement 7.
