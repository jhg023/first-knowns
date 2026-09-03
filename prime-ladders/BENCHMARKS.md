# BENCHMARKS — prime-ladders

`python score.py` prints a SCORE only if every correctness gate is green
**and** all six frozen shapes reproduce their work fingerprints exactly.
An engine that skips work fails the fingerprint; an engine that breaks the
mathematics fails the gates. Either way it scores nothing.

The reported rate is end-to-end **k-line per second** — the quantity a hunt
is actually paid in — divided by 10⁶. The candidate rate is printed beside
it because the two say different things: line rate is what the campaign
buys, candidate rate is what the kernel does, and the wheel is the exchange
rate between them. Here that exchange rate is unusually favourable: forced
divisibility (README.md, "The mathematics of the engine") leaves
`7.1×10⁻⁷` of the line as candidates at n = 14 on the v3 unit wheel and
`4.1×10⁻⁸` at n = 18, so `2.5×10¹¹` candidates per second at the live
filter is `6.2×10¹⁸` k per second.

## The shapes

| shape | sign | filter | wheel | sieve | window | denominated in | fingerprint (count / xor) |
|-------|------|--------|-------|-------|--------|----------------|---------------------------|
| `SCORE` | +1 | n = 14 | (31], (41], (53] at unit 2310 | 65536 | period 1, from `3.2589×10¹⁹` | 64 launches (`5.40×10¹⁶` of line) | 26170 / 32987145531510950730 |
| `SCORE18` | +1 | n = 18 | (31], (41], (53] at unit 2310 | 65536 | period 1668, from `5.4359×10²²` | 64 launches (`1.63×10¹⁸` of line) | 729 / 54348831183746127314014 |
| `SCORE2L` | +1 | n = 14 | (23], (37] | 65536 | 6,656 periods from `7.0003×10¹⁷` | periods (`4.94×10¹⁶` of line) | 23680 / 22858249279285762 |
| `SCORE1L` | +1 | n = 14 | ≤ 23 | 65536 | **the same absolute window**, 221,398,528 periods | periods | 23680 / 22858249279285762 |
| `SCOREM` | −1 | n = 12 | (31], (41], (53] at unit 210 | 65536 | period 1, from `3.2589×10¹⁹` | 64 launches (`4.69×10¹⁶` of line) | 765063 / 4432308906875442260 |
| `SCORE10` | +1 | n = 10 | ≤ 13 | 4096 | 60,000,000 periods from `1.0000×10¹¹` | periods (`1.80×10¹²` of line) | 19004 / 472865539996 |

`SCORE`, `SCORE18` and `SCOREM` are denominated in kernel **launches**
because a unit-wheel period is `3.26×10¹⁹` of k line — five seconds of
device at n = 18 and two minutes at n = 14; 64 launches is 64 × 22 of the
28,080 third-level residues a period holds at n = 18 (64 of 38,610 at
n = 14), and just as reproducible a set of candidates. `SCORE18` starts
at period 1668 because that is the period the live A084700 cursor
re-denominated onto: the benchmark runs the line the hunt runs. The other
three sweep whole periods of their own k-space wheels.

`SCORE1L` is the one to understand. It sweeps the *identical absolute
window* as `SCORE2L` on the one-level wheel — 33,263× as many periods,
because `W(2L) = W(1L) × 33263` exactly (29 · 31 · 37) — and it must return
the same 23,680 survivors and the same checksum. Two different wheels
enumerating the same candidates by different arithmetic, so a bug in the
CRT lift shows up inside the benchmark rather than as a wrong answer months
later. It did return them, on the first run. The same cross-wheel check
guards the unit wheel as a gate rather than a shape (G17): the v3 wheel
must return the v2 wheel's identical survivors over a v2 period at n = 18,
which is what the cursor re-denomination rests on.

## Ledger

| date | engine | SCORE | SCORE18 | SCORE2L | SCORE1L | SCOREM | SCORE10 | battery |
|------|--------|-------|---------|---------|---------|--------|---------|---------|
| 2026-09-02 | v1 | **111,143,013,071** | — | 65,153,518,777 | 9,468,319,388 | 16,966,560,612 | 5,358,083 | 37/37 green, 31 s; score.py 59 s |
| 2026-09-02 | v2 | **202,524,485,715** | — | 93,320,802,420 | 18,817,108,326 | 34,017,742,869 | 8,526,813 | 37/37 green; every fingerprint identical to v1's |
| 2026-09-02 | v3 | 182,950,418,030 | **6,156,431,019,029** | 83,278,142,757 | 16,172,004,625 | 28,233,290,316 | 7,557,055 | 41/41 green, 42 s; score.py 2.5 min; SCORE/SCOREM re-frozen on the unit wheel, SCORE18 added, the three k-space fingerprints identical to v1's |
| 2026-09-03 | v3.1 | **247,175,538,205** | **6,173,131,954,944** | 85,373,360,028 | 16,668,608,719 | 33,965,957,033 | 7,254,701 | 41/41 green, 51 s; score.py 2.5 min; every fingerprint identical to v3's; `LIT_SURV` per filter (SCORE 1.35× and SCOREM 1.20× over the v3 row; SCORE18's filter keeps 0.28), the pool sized at runtime, back-pressure |

The v3 row is read against two different things. **At the live filter**
the paired number is what matters: on one period of the v2 wheel at
n = 18, interleaved in one process the same morning, the v2 engine ran
`3.58×10¹⁸ k/s` and v3 runs `6.16×10¹⁸` — **1.72×** (1.29× from the
wheel's 1.47× density, the rest from the constants re-swept on it;
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3). **At the opening
filters** the v3 row was slower than v2's — `SCORE` (n = 14) 0.90×,
`SCOREM` (n = 12) 0.83× — because `LIT_SURV` had been swept at n = 18
only. v3.1's per-filter table ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)
v3.1) puts `SCORE` at 1.22× v2's row and `SCOREM` level with it; what the
k-space wheel still has over the unit wheel at n = 12 is a 53× shorter
period, not rate. The three k-space shapes run v2's own constants and
read 0.82–0.92× of v2's row across the v3 and v3.1 runs — unpaired, hours
of sweeps into the GPU's day, inside the 10%-plus run-to-run band that
row already warns about.

In physical units:

| shape | line rate | candidate rate |
|-------|-----------|----------------|
| `SCORE` | `2.47×10¹⁷ k/s` | `1.75×10¹¹ /s` |
| `SCORE18` | `6.17×10¹⁸ k/s` | `2.50×10¹¹ /s` |
| `SCORE2L` | `8.54×10¹⁶ k/s` | `2.37×10¹¹ /s` |
| `SCORE1L` | `1.67×10¹⁶ k/s` | `2.09×10¹¹ /s` |
| `SCOREM` | `3.40×10¹⁶ k/s` | `1.02×10¹¹ /s` |
| `SCORE10` | `7.26×10¹² k/s` | `4.83×10⁹ /s` |

(v3.1; the v3 row read 1.83 / 61.6 / 0.833 / 0.162 / 0.282 / 0.0000756
×10¹⁷, the v2 row 2.025 / — / 0.933 / 0.188 / 0.340 / 0.0000853.)

Read the candidate column against the line column. `SCORE18` and `SCORE`
run the same wheel and the same kernel and differ 34× in line for 2× in
candidates: at n = 18 the wheel lets one candidate in `2.5×10⁷` of the
line through, at n = 14 one in `1.4×10⁶`, because every extra condition
kills one more residue per wheel prime. `SCOREM` is the A084701
campaign's *opening* filter, n = 12, where the residue tables are fuller
still (2,918,400 first-level residues at unit 210) and every value is a
smaller number; its line rate is a sixth of `SCORE`'s for that reason and
not because the sign costs anything — the two families compile to the
same kernel.

## Wall clock at the scored rate

At the v3 `6.16×10¹⁸ k/s` of `SCORE18`, the second campaign's `3.62×10²³`
of line from `5.44×10²²` to `a(18)` was 16.3 hours of sweeping; it took
15.2 (the campaign averaged `6.6×10¹⁸ k/s`, the benchmark being a paired
number taken under ambient load). The model had put `a(18)` at a median
of `1.9×10²³` (6.0 h) and a P90 of `1.0×10²⁴` (1.9 days); it landed at
2.2× the median, inside the P90.

From each family's cursor — A084700 at `4.16×10²³`, A084701 at its
ceiling `4.95×10²²`, both at filter n = 19 — the model's depths for the
open terms ([RESULTS.md](RESULTS.md)) convert to:

| term | Q1 | median | Q3 | P90 | to the ceiling |
|------|----|--------|----|-----|----------------|
| A084700 a(19) | `4.0×10²⁴`, past the ceiling | `1.2×10²⁵` | `3.1×10²⁵` | `6.2×10²⁵` | `3.317×10²⁴`, `2.9×10²⁴` of line — **2.7 days at the n = 19 rate** (22%) |
| A084700 a(20) | `1.4×10²⁶` | `5.1×10²⁶` | — | — | 2% under it |
| A084701 a(19) | `2.9×10²⁴` | `1.0×10²⁵` | `2.8×10²⁵` | `5.9×10²⁵` | `4.95×10²²`, **reached on 2026-09-03** — 0.8% of the term was under it, and it was not there |

`SCORE18` is not the n = 19 rate. The wheel is 1.87× thinner there
(`2.2×10⁻⁸` candidates per unit of line against `4.1×10⁻⁸` at n = 18),
and with its own constant (v3.1's per-filter table: `LIT_SURV` 0.12 at
n = 19) the same 64-launch shape from period 12774 runs at
**`1.23×10¹⁹ k/s`, 1.95× the n = 18 rate**, interleaved against the frozen
`SCORE18` window. With the n = 18 constant it ran at 0.37× of that rate
-- the shared-memory cliff the v3 sweep mapped, one filter past where it
swept -- which is what the A084700 campaign would have resumed at
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3.1).

For a fresh campaign at the opening filters, at the v3.1 `SCORE`
`2.47×10¹⁷ k/s`: `a(14)` through `a(16)` of A084700 lie inside period 0 of
the unit wheel (`3.26×10¹⁹`, about two minutes), and `a(17)`'s median
`2.0×10²¹` is two and a quarter hours — the first campaign found it in 33
minutes. The A084701 family's first four open terms all sat inside
period 0 as well: at `SCOREM`'s `3.40×10¹⁶ k/s` that period is about
sixteen minutes, and nothing is narrated until it closes. **That is how
the A084701 campaign of 2026-09-03 went** — the rule 5g acceptance test
run for real, with no flags. Period 0 closed seventeen minutes in (pool
sizing and ramp included) carrying `a(12)`, `a(13)`, `a(14) = a(15)` and
`a(16)`; the filter promoted to n = 17 and the campaign found `a(17)`
82 minutes in, having swept the line between at `2.3×10¹⁸ k/s` (the
v3.1 table's n = 17 rate, at unit 210), `a(18)` at 118 minutes
(`6.6×10¹⁸ k/s` at n = 18), and reached the ceiling at 152 minutes,
at `1.27×10¹⁹ k/s` over the n = 19 stretch — the rate the unit-2310
wheel gives A084700 at that filter, within noise. Every phase ran at its
benchmark's rate, which is what the defaults are for
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3.1).

The enforced ceiling is now the family's primality-proof validity bound:
`3.317×10²⁴` for A084700 (the deterministic Miller–Rabin bound on `k`
itself; past the proof crossing at `5.4×10²²` a discovery is proved by
certificate) and for A084701 its proof crossing — `9.0×10²²` at n = 12,
`4.95×10²²` at n = 19 — because its structure is on `N + 1` and huntlib
has no N+1 test (see the README for why). The first A084700 campaign
stopped at the old ceiling in 4.4 hours; the second found `a(18)` 15.2
hours in; what is left to the ceiling at n = 19 is `2.9×10²⁴` of line,
and `a(19)` is only 22% likely to be in it. The A084701 campaign reached
its ceiling in 2.5 hours with `a(19)` 99% likely above it; an N+1 route
would lift that ceiling to `3.317×10²⁴`, under which 27% of the term
lies — `3.3×10²⁴` of line, about three days at the n = 19 rate.

The three ladder projects before this one landed their finds at a pooled
optimism factor of 1.92× over their models' medians; this one's eleven
scored finds came in at 0.11–6.4× theirs, mean 2.5× and median 2.2×,
with the mean `E` at 1.27 ([README.md](README.md#the-odds-model)).
Budget two to three times the medians above before expecting a term.
