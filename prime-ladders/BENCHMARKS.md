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

The v3 row is read against two different things. **At the live filter**
the paired number is what matters: on one period of the v2 wheel at
n = 18, interleaved in one process the same morning, the v2 engine ran
`3.58×10¹⁸ k/s` and v3 runs `6.16×10¹⁸` — **1.72×** (1.29× from the
wheel's 1.47× density, the rest from the constants re-swept on it;
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3). **At the opening
filters** the unit wheel is slower: `SCORE` (n = 14) is 0.90× v2's row
and `SCOREM` (n = 12) 0.83× — the first-level table is 300× larger there
(856,800 residues against 2,800), a launch is half the size, and
`LIT_SURV` tuned for n = 18 costs 15% at n = 12. Those filters are passed
in the first period of a campaign (`a(14)` lies in period 0 of either
wheel), and the price is recorded rather than hidden. The three k-space
shapes run v2's own constants and read 0.86–0.89× of v2's row — unpaired,
an hour of sweeps into the GPU's day, inside the 10%-plus run-to-run band
that row already warns about.

In physical units:

| shape | line rate | candidate rate |
|-------|-----------|----------------|
| `SCORE` | `1.83×10¹⁷ k/s` | `1.29×10¹¹ /s` |
| `SCORE18` | `6.16×10¹⁸ k/s` | `2.50×10¹¹ /s` |
| `SCORE2L` | `8.33×10¹⁶ k/s` | `2.31×10¹¹ /s` |
| `SCORE1L` | `1.62×10¹⁶ k/s` | `2.03×10¹¹ /s` |
| `SCOREM` | `2.82×10¹⁶ k/s` | `8.48×10¹⁰ /s` |
| `SCORE10` | `7.56×10¹² k/s` | `5.03×10⁹ /s` |

(v3; the v2 row read 2.025 / — / 0.933 / 0.188 / 0.340 / 0.0000853 ×10¹⁷.)

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

At the v3 `6.16×10¹⁸ k/s` of `SCORE18`, from the A084700 cursor at
`5.44×10²²`, the model's depths for the open term ([RESULTS.md](RESULTS.md))
convert to:

| term | Q1 | median | Q3 | P90 | to the ceiling |
|------|----|--------|----|-----|----------------|
| A084700 a(18) | `5.7×10²²`, 7 min | **`1.9×10²³`, 6.0 h** | `5.0×10²³`, 20 h | `1.0×10²⁴`, 1.9 days | `3.317×10²⁴`, **6.1 days** (99.4%) |
| A084700 a(19) | `2.8×10²⁴`, 5.2 days | `1.0×10²⁵`, past the ceiling | — | — | — |

For a fresh campaign at the opening filters, at the v3 `SCORE`
`1.83×10¹⁷ k/s`: `a(14)` through `a(16)` of A084700 lie inside period 0 of
the unit wheel (`3.26×10¹⁹`, about three minutes), and `a(17)`'s median
`2.0×10²¹` is three hours — the first campaign found it in 33 minutes. The
A084701 family's first four open terms all sit inside period 0 as well.

The enforced ceiling is now the family's primality-proof validity bound:
`3.317×10²⁴` for A084700 (the deterministic Miller–Rabin bound on `k`
itself; past the proof crossing at `5.4×10²²` a discovery is proved by
certificate) and `9.0×10²²` at n = 12 for A084701 (its proof crossing;
see the README for why). The first campaign stopped at the old A084700
ceiling in 4.4 hours; the new one is six days of sweeping at n = 18.

The three ladder projects before this one landed their finds at a pooled
optimism factor of 1.92× over their models' medians; this one's four
finds came in at 0.9–2.8× theirs, mean 1.27×. Budget two to three times
the medians above before expecting a term.
