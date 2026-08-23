# RESULTS — square-ladders (A089761)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

Three, from the campaign of 2026-08-21/23 — the first terms of A089761
found by anyone since Donovan Johnson's `a(11)` in September 2008, and the
first that break the five-term plateau.

### `a(16) = 15,737,271,507,027,492`

    k = 15737271507027492
    k*i^2 + 1 is prime for i = 1 .. 16
    stopped by k*17^2 + 1 = 4548071465530945189 = 317 * ...

### `a(17) = 125,811,821,444,034,258`

    k = 125811821444034258
    k*i^2 + 1 is prime for i = 1 .. 17
    stopped by k*18^2 + 1 = 40763030147867099593 = 109 * ...

### `a(18) = 109,927,810,420,106,024,208`

    k = 109927810420106024208
    k*i^2 + 1 is prime for i = 1 .. 18
    stopped by k*19^2 + 1 = 39683939561658274739089 = 643991 * 61621283177279

This one is `5.96 × 2⁶⁴`. No engine before **v4** could address it at all:
v3.4 carried `k` in a machine word and would have stopped at `9×10¹⁸`,
**twelve times short of it**, at a limit that is a property of C and not of
the mathematics. Carrying candidates as `(k, off)` is what put it in range;
the wheel to 47 is what made the range affordable.

All three survived all four verification legs below, and every primality
decision in all three is a **proof**, not a probable-prime call: each value
is under huntlib's deterministic Miller-Rabin bound — the largest, at
`a(18)`, is `3.56×10²²` against the bound's `3.32×10²⁴` — so the
certificates read `deterministic-mr` throughout (gate G10). The exact
integers, all values `k*i^2+1`, the certificates and the factor witnesses
are in [`evidence/`](evidence/).

Nothing has been submitted anywhere. These are records; what happens to
them is the owner's decision (CLAUDE.md rule 5).

## The frontier

| | |
|---|---|
| Last published term | `a(15) = 861,066,640` |
| Last term anyone *searched* for, before this | `a(11)`, Donovan Johnson, Sep 27 2008 — the same integer |
| Searched-empty bound this project inherited | `a(16) > 1.4×10¹³`, Max Alekseyev |
| **Found here** | `a(16)`, `a(17)`, `a(18)` — above |
| **Open, and next** | `a(19)`, searched-empty below `1.10×10²⁰` |
| Upper bound | none published, at any open `n` |

The plateau is the whole story of this sequence's frontier, so it is worth
stating exactly. `k = 861,066,640` was found as `a(11)`. It then satisfied
`i = 12, 13, 14, 15` with no further search, which is why five published
terms share one value. Its run stops at exactly one composite:

    861066640 * 16^2 + 1 = 220433059841 = 47 * 149 * 31476947

That factorization — checkable on a calculator — is the entire reason
`a(16)` was open for eighteen years, and gate G1 asserts it on every run:
the champion reaches exactly 15, and its 16th value is composite.

## What a find will look like

A survivor `k` with run length `r` is classified against the live frontier
(`event_kind` in `launch.py`, drilled in the selftest):

| run | class | what happens |
|-----|-------|--------------|
| `r > frontier` | **DISCOVERY** | settles `a(frontier+1) … a(r)` at once; verified three ways plus a factor witness for the composite that stops the run; one evidence JSON; logged once |
| `r == frontier` | **NEAR** | one condition short of the open term — one line with its campaign ordinal, verified by the cheap legs as an engine health check, never evidenced |
| `8 ≤ r < frontier` | **CENSUS** | counted in the `[STATUS]` heartbeat, never narrated |
| `r < 8` | — | not even counted |

Because the conditions nest, a single find can settle several terms at
once, each logged once and all evidenced under the first. The odds of that
are modest and were stated honestly in advance — about 0.14 per extra
condition, so roughly **1.16 terms per find in expectation** — and that is
how it played out: `a(16)`, `a(17)` and `a(18)` arrived as three separate
finds, each settling exactly one term, none riding on another.

## Verification every claim must survive

1. **huntlib's Miller-Rabin.** Deterministic here, not probabilistic —
   and since v4 that is true BY CONSTRUCTION rather than by luck: the
   enforced ceiling *is* the `3.317×10²⁴` bound rearranged,
   `k_ceil(n) = (MR_VALID_BELOW - 2)/n² + 1`, so no `k` the engine can
   reach has a value outside the deterministic zone (gate G10 pins it
   tight to one `k`, per `n`). This project proves its primes.
2. **sympy's BPSW** — an independent implementation, and it must agree on
   the run length exactly, not merely on primality.
3. **A re-derivation by different machinery** — the CPU engine, which
   marks the dense `k` line and uses no wheel at all, must agree that the
   `k` survives the sieve.
4. **A factor witness for the stopper.** The value at `i = r+1` must be
   composite, with a factor exhibited, because that is what bounds the
   claim to exactly `r`. Trial division, then bounded rho, then bounded
   ECM — nothing in the path runs unbounded.

Any disagreement between the legs is an engine bug by definition and halts
the campaign with exit 2. Nothing is ever submitted anywhere from inside
the pipeline; the evidence directory is written and a human decides
(CLAUDE.md rule 5).

## Census

Counts per run length live in the checkpoint and in the 30-second
`[STATUS]` heartbeat, never as per-value listings. `python launch.py
--status` prints them. The campaign's final tally, over the line above
`a(17)` where the filter stood at `n = 18`, against what the same
Bateman-Horn intensity predicts once the sieve's own retention is folded
in (a run-`r` survivor also needs its values at `i = r+1 … 18` free of
factors below 65536):

| run | counted | model | ratio |
|-----|---------|-------|-------|
| 8 | 51,633 | 50,784 | 1.02 |
| 9 | 20,977 | 20,389 | 1.03 |
| 10 | 8,385 | 8,153 | 1.03 |
| 11 | 3,419 | 3,249 | 1.05 |
| 12 | 1,281 | 1,291 | 0.99 |
| 13 | 488 | 511 | 0.95 |
| 14 | 228 | 202 | 1.13 |
| 15 | 86 | 80 | 1.08 |
| 16 | 22 | 31 | 0.70 |
| 17 | 12 | 12.3 | 0.97 |
| **8-17 pooled** | **86,531** | **84,703** | **1.022** |

This is the census earning its keep. It is not decoration: for most of a
day `a(18)` was overdue and the only question that mattered was whether
the engine could still find one, and this table answers it without
stopping the hunt. Read as conditional probabilities it is sharper still —
the fraction of run-`r` survivors that go on to reach `r+1` is 0.403,
0.399, 0.398, 0.383, 0.395, 0.417, 0.347, 0.289, 0.371 for `r = 8 … 16`,
flat across four orders of magnitude of sample size and sitting on the
0.392 the model predicts. An engine losing long runs cannot produce that
table; a wrong intensity cannot either.

## How `a(18)` was actually paid for

`a(18)` cost **20.7 hours** of v5 sweeping, over `1.00×10²⁰` of line from
the v4 cursor at `9.65×10¹⁸` — an end-to-end **`1.35×10¹⁵ k/s`**, with the
instantaneous rate ranging `0.8-1.9×10¹⁵` between a machine in use and a
machine left alone overnight. (The pre-v5 stretch that produced `a(16)`
and `a(17)` was 13.5 h, so the campaign totals 34.2 h across three engine
versions.)

It arrived at **40× the live ladder's median and 6.9× its P90** — 2.3×
past P99 — which is most of the story of this campaign and is scored in
[README.md](README.md#the-odds-model). Two things kept that from looking
like an engine fault: the census table above, and the fact that every one
of the 15 one-short `[NEAR]` values was verified as it appeared.

## In progress

Nothing is running. The cursor stands at
`k = 110,065,090,703,139,672,390`, with **`a(19)` open** and the campaign
paused there by the owner.

From that cursor, at `1.35×10¹⁵ k/s`:

| `a(19)` | depth | sweeping time |
|---|---|---|
| Q1 | `1.71×10²⁰` | 12 h |
| median | `2.72×10²⁰` | 33 h |
| Q3 | `4.82×10²⁰` | 77 h |
| P90 | `8.23×10²⁰` | 147 h |

Those are the model's own numbers, and this project's model has now been
caught running `3.7×` hot ([README.md](README.md#the-odds-model)), so read
them as a floor rather than a forecast. The engine's ceiling at `n = 19`
is `k_ceil(19) = 9.19×10²¹` — 1,869 h of sweeping away, and the model puts
`a(19)` below it with probability > 99.9%, so this ladder does not run out
of range before it runs out of patience.
