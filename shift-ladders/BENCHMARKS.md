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

`SCORE1L` is the one to understand. It sweeps the *identical absolute
window* as `SCORE` on a coarser wheel — 7,429× as many periods, because
`W(23) = W(13) × 7429` — and it must return the same seven survivors and
the same checksum. Two different wheels enumerating the same candidates by
different arithmetic: a bug in the CRT lift shows up inside the benchmark
rather than as a wrong answer months later. It is also the reason both
windows are stated as period indices; comparing two engines over
almost-the-same window produces a disagreement between two engines that
are both right, which has cost this repository a day before.

## Ledger

### v1 — 2026-08-23, the first engine (flat wheel table, Barrett test loop)

Medians of three interleaved rounds, every fingerprint checked on every
run, machine otherwise idle:

| shape | rate | candidates/s | run-to-run spread | SCORE |
|-------|------|--------------|-------------------|-------|
| `SCORE` | 4.46×10¹² m/s | 3.15×10¹⁰ | **51%** | **4,461,600** |
| `SCORE1L` | 1.07×10¹² m/s | 3.58×10¹⁰ | 13% | 1,066,100 |
| `SCORE2` | 3.06×10¹⁶ m/s | 2.22×10¹⁰ | 20% | 30,611,000,000 |
| `SCORE4W` | 1.01×10¹² m/s | 3.38×10¹⁰ | 11% | 1,007,900 |
| `SCORE10` | 4.61×10¹¹ m/s | 1.55×10¹⁰ | 12% | 460,960 |

Read across the candidate column rather than the rate column: every shape
sits between 1.5×10¹⁰ and 3.6×10¹⁰ candidates/s, and the four orders of
magnitude between `SCORE` and `SCORE2` are **entirely the wheel**. That is
the single most important fact about this project's cost model, and it is
why the campaign numbers below are quoted per family.

**`SCORE` does not resolve to better than about ±25%, and that is a
property of the engine rather than of the machine.** Its residue table is
12.6 MB — the flat wheel at p1 = 23 — and the kernel streams it once per
launch, so the production shape is bandwidth-sensitive in a way the
coarse-wheel shapes (8 KB of residues, comfortably resident) are not; they
repeat to 11%. Two consequences, both binding: **a change of less than
~25% in `SCORE` alone is not evidence of anything**, and any A/B on this
project must be interleaved and paired with the fingerprint re-checked on
every run (OPTIMIZATION.md rule 3) rather than read off two separate score
runs. The same table is one of the reasons the factored wheel is the first
optimization on the list.

## Wall clock at the scored rate

What the v1 engine buys, from each family's published frontier to each
open term's model median:

| target | from | median | line to sweep | v1 wall clock |
|--------|------|--------|---------------|---------------|
| A130003 `a(19)` | `1.16×10¹⁵` | `5.75×10¹⁶` | `5.6×10¹⁶` | **3.5 h** |
| A130003 `a(20)` | " | `1.42×10¹⁸` | `1.4×10¹⁸` | 87 h |
| A130003 `a(21)` | " | `4.73×10¹⁹` | `4.7×10¹⁹` | 122 d |
| A110096 `a(17)` | `1.44×10¹⁷` | `2.03×10²⁰` | `2.0×10²⁰` | **1.8 h** |
| A110096 `a(18)` | " | `1.74×10²²` | `1.7×10²²` | 6.6 d |
| A110096 `a(19)` | " | `5.67×10²³` | `5.7×10²³` | 214 d |

Two things this table is not. It is not a forecast: the medians are the
model's, and this repo's first-occurrence models run about 3× late, so
multiply by 2-3 before expecting a term (README, "The odds model"). And it
is not the ceiling of what the hardware can do: v1 is the correctness-first
engine and the first optimization is priced at roughly 14× on base 4
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)), which is what moves `a(20)`
and `a(18)` from "a fortnight" to "an afternoon".

Wall clock of the tools themselves, so they can be planned against the
five-minute rule: `launch.py --selftest` ~25 s, `score.py` ~1 min.
