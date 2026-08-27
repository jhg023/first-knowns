# RESULTS — shift-ladders (A130003, A110096)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

**Four, from the campaigns of 2026-08-23/24** — two on each family, and on
A130003 they are the first terms anyone has found since Jens Kruse
Andersen's `a(18)` in **June 2007**, nineteen years ago.

### A130003 (`b = 4`)

#### `a(19) = 13,268,589,982,417,023`

    m = 13268589982417023
    m + 4^k is prime for k = 1 .. 19
    stopped by m + 4^20 = 13269689494044799 = 941 * ...

#### `a(20) = 6,120,156,516,528,136,867`

    m = 6120156516528136867
    m + 4^k is prime for k = 1 .. 20
    stopped by m + 4^21 = 6120160914574647971 = 5581 * ...

### A110096 (`b = 2`)

#### `a(17) = 305,948,728,878,647,722,725`

    m = 305948728878647722725
    m + 2^k is prime for k = 1 .. 17
    stopped by m + 2^18 = 305948728878647984869 = 19 * ...

#### `a(18) = 760,056,834,873,121,351,995`

    m = 760056834873121351995
    m + 2^k is prime for k = 1 .. 18
    stopped by m + 2^19 = 760056834873121876283 = 157 * ...

Both A110096 terms are **above 2⁶⁴** — `16.6×` and `41.2×` it. Carrying
candidates as `(m, off)` from the first commit is what put them in range,
and it cost nothing to do it that way at the start (OPTIMIZATION.md 2.7);
square-ladders retrofitted the same property and paid for it twice.

All four survived all four verification legs below, and every primality
decision in all four is a **proof**, not a probable-prime call: the largest
value anywhere in the set is `760,056,834,873,121,614,139`, which is
`4,364×` below huntlib's deterministic Miller-Rabin bound of `3.317×10²⁴`,
so the certificates read `deterministic-mr` throughout (gate G10). The
exact integers, all values `m + b^k`, the certificates and the factor
witnesses are in [`evidence/`](evidence/).

Nothing has been submitted anywhere. These are records; what happens to
them is the owner's decision (CLAUDE.md rule 5).

## The frontier

| | A130003 (b = 4) | A110096 (b = 2) |
|---|---|---|
| Last published term | `a(18) = 1,158,174,141,556,287` | `a(16) = 143,924,005,810,811,655` |
| Found by | Jens Kruse Andersen, **Jun 08 2007** | Bert Dobbelaere, Apr 24 2021 |
| Searched-empty bound inherited | none — the frontier was the term itself | none |
| **Found here** | `a(19)`, `a(20)` | `a(17)`, `a(18)` |
| **Open, and next** | `a(21)`, searched-empty below `8.95×10¹⁸` | `a(19)`, searched-empty below `3.62×10²¹` |
| Upper bound | none published, at any open `n` | none published, at any open `n` |

Neither entry carried a published bound of any kind, so the floor for each
term was monotonicity alone — which is free, because the conditions nest:
`a(n+1) ≥ a(n)`. The OEIS export was re-pulled on 2026-08-26 and both
entries still end where they did: eighteen terms and sixteen.

Each of the old frontier terms stops at exactly one composite, and gate G1
asserts both on every run:

    1158174141556287 + 4^19 = 1158449019463231   (composite)
     143924005810811655 + 2^17 = 143924005810942727   (composite)

## What a find looked like

A survivor `m` with run length `r` is classified against the live frontier
(`event_kind` in `launch.py`, drilled in the selftest):

| run | class | what happens |
|-----|-------|--------------|
| `r > frontier` | **DISCOVERY** | settles `a(frontier+1) … a(r)` at once; verified three ways plus a factor witness for the composite that stops the run; one evidence JSON; logged once |
| `r == frontier` | **NEAR** | one condition short of the open term — one line with its campaign ordinal, verified by the cheap legs as an engine health check, never evidenced |
| `8 ≤ r < frontier` | **CENSUS** | counted in the `[STATUS]` heartbeat, never narrated |
| `r < 8` | — | not even counted |

The two campaigns classified **15,457 values at run 8 or longer** — 13,073
at base 4 and 2,384 at base 2. Four of them were discoveries and seven
were `[NEAR]`, one condition short of the open term (4 at base 4, 3 at
base 2); every one of the rest was counted and nothing else.

**No find carried a rider.** All four settled exactly one term, and that is
what the model expects at these depths rather than a surprise. A rider
needs `m + b^(n+1)` prime at the value that *stopped* at `n` — and that
value was never sieved, because the campaign's filter was `n`. So its
chance is roughly `S(n+1)/S(n) / log m`, which is 0.19, 0.16, 0.06 and 0.12
at the four finds: **0.52 riders expected over the four, and a 57% chance
of exactly none.** The 0.4-per-step figure this file carried before the
sweep is the *small-`m`* regime that produced the historical riders — it is
0.38 at A130003's `a(10) = 4503` and 0.95 at A110096's `a(4) = 15`. Riders
are a property of the depth, and this hunt is four to eighteen orders of
magnitude past the ones that made them common.

## Verification every claim must survive

1. **huntlib's Miller-Rabin.** Deterministic here, not probabilistic, and
   by construction rather than by luck: the enforced ceiling *is* the
   `3.317×10²⁴` bound rearranged, `k_ceil(n, b) = MR_VALID_BELOW − bⁿ`, so
   no `m` the engine can reach has a value outside the deterministic zone
   (gate G10 pins it tight to one `m`, per `(n, b)`). This project proves
   its primes.
2. **sympy's BPSW** — an independent implementation, and it must agree on
   the run length exactly, not merely on primality.
3. **A re-derivation by different machinery** — the CPU engine, which
   marks the dense `m` line and uses no wheel at all, must agree that the
   `m` survives a sieve at a different depth from the campaign's.
4. **A factor witness for the stopper.** The value at `k = r+1` must be
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
--status` prints them, per family.

Both campaigns' final tallies, against what the *same* Bateman-Horn
intensity predicts once the sieve's own retention is folded in — a run-`r`
survivor also needs its values at `k = r+1 … n` free of factors below
65536, and each family's filter `n` rose as its own finds landed, so the
prediction is summed over the three windows each campaign actually ran:

| run | A130003 counted | model | ratio | | A110096 counted | model | ratio |
|-----|-----------------|-------|-------|---|-----------------|-------|-------|
| 8 | 6,847 | 7,000 | 0.98 | | 1,364 | 1,385 | 0.98 |
| 9 | 3,247 | 3,284 | 0.99 | | 614 | 587 | 1.05 |
| 10 | 1,568 | 1,542 | 1.02 | | 216 | 249 | 0.87 |
| 11 | 731 | 725 | 1.01 | | 102 | 106 | 0.97 |
| 12 | 369 | 341 | 1.08 | | 41 | 45 | 0.91 |
| 13 | 166 | 161 | 1.03 | | 31 | 19 | 1.62 |
| 14 | 77 | 76 | 1.01 | | 9 | 8.1 | 1.11 |
| 15 | 36 | 36 | 1.00 | | 1 | 3.5 | 0.29 |
| 16 | 18 | 17 | 1.06 | | 4 | 1.5 | 2.70 |
| 17 | 5 | 8.1 | 0.62 | | 1 | 1.0 | 0.98 |
| 18 | 3 | 3.9 | 0.78 | | 1 | 0.1 | 14.7 |
| 19 | 5 | 2.0 | 2.51 | | | | |
| 20 | 1 | 1.5 | 0.67 | | | | |
| **pooled** | **13,073** | **13,198** | **0.991** | | **2,384** | **2,404** | **0.992** |

Both pooled ratios are within 1% of 1, on 13,073 and 2,384 events. Read as
conditional probabilities the base-4 column is sharper still: the measured
fraction of run-`r` survivors that go on to reach `r+1` is 0.474, 0.483,
0.466, 0.505, 0.450, 0.464, 0.468, 0.500 for `r = 8 … 15`, flat across two
and a half orders of magnitude of sample size and sitting on the 0.47 the
model predicts. The rows below 10 counts are Poisson noise and are printed
rather than hidden.

There is a third check hiding in the same numbers. The sieve should have
handed the classifier `5.78×10⁶` candidates at base 4 and `2.40×10⁶` at
base 2; if each extends with probability 0.470 and 0.424, the fraction
reaching run 8 should be `0.470⁸ = 2.38×10⁻³` and `0.424⁸ = 1.05×10⁻³`.
Measured: `13,073 / 5.78×10⁶ = 2.26×10⁻³` and
`2,384 / 2.40×10⁶ = 9.93×10⁻⁴`. The device's survivor count, the host's
classification and the model's intensity agree to within 5% on a quantity
none of them shares machinery for.

This is the census earning its keep, and it is why it is counted rather
than narrated. In square-ladders it settled an overdue term without
stopping the hunt; here it does the opposite job. Two of the four finds
below landed early, at quantiles 0.24 and 0.04, and the census is what says
that is a property of the *waiting time* rather than an intensity that is
too low — a model under-counting hits by the 1.5× the four finds suggest
would have shown up in 15,457 counted values long before it showed up in
four, and it does not: the counts land at 0.991 and 0.992.

## How the finds scored

Each find is scored at the quantile it landed on, measured from the floor
the search for it actually started at — the previous term, since neither
sequence carries a published bound.

| term | found at | live median | E at the find | quantile |
|------|----------|-------------|---------------|----------|
| A130003 `a(19)` | `1.33×10¹⁶` | `5.75×10¹⁶` | 0.278 | 0.243 |
| A130003 `a(20)` | `6.12×10¹⁸` | `1.64×10¹⁸` | 1.426 | 0.760 |
| A110096 `a(17)` | `3.06×10²⁰` | `2.03×10²⁰` | 0.899 | 0.593 |
| A110096 `a(18)` | `7.60×10²⁰` | `1.97×10²²` | 0.042 | 0.041 |

Two early, one late, one on the nose. Pooled as Poisson exposure the four
finds cost **2.64 expected hits for 4 actual**, an optimism factor of
**0.66×** with an exact 95% interval of **[0.30, 2.43]** — which contains
1, and is the first point estimate in this repository that sits *below*
it (euler-prime-runs measured 1.9, dickson-ladders 2.26, square-ladders
3.66). On its own evidence this model is not measurably wrong in either
direction, and the census above says why that is worth believing rather
than a coincidence: the intensity is right to 1%.

That is a real disagreement with the sibling projects, and it is scored
against them in [README.md](README.md#the-odds-model) rather than papered
over. Do not read it as a licence to trust the medians: four draws cannot
separate 0.66× from 2×, and pooled over the eleven first occurrences the
three ladder projects have now scored between them, the optimism factor is
still **2.06×**, still excluding 1.

## What the campaign cost

| | A130003 (b = 4) | A110096 (b = 2) |
|---|---|---|
| started | 2026-08-23 15:53 | 2026-08-24 09:20 |
| stopped | 2026-08-24 09:19 | 2026-08-24 09:58 |
| **wall clock** | **17.44 h** | **38.2 min** |
| first find | `a(19)` at **117 s** | `a(17)` at **9.5 min** |
| second find | `a(20)` at **12.04 h** | `a(18)` at **15.8 min** |
| line swept | `8.95×10¹⁸` | `3.62×10²¹` |
| end-to-end rate | `1.42×10¹⁴ m/s` | `1.58×10¹⁸ m/s` |

**Four terms for 18.1 hours of one GPU**, on two sequences that had stood
for nineteen and five years. `a(19)` of A130003 arrived 117 seconds into
the campaign, which is what a nineteen-year-old frontier with no published
bound below it looks like once the engine is right.

The end-to-end rates are **not** the engine's rates, and the gap is the
open item of this project: at the configurations each campaign was left in,
the device measures `5.08×10¹⁴` and `5.21×10¹⁸ m/s`, so the campaigns ran
at 29% and 41% of what the kernel does. Per launch that is a fixed 29.5 and
29.8 ms unaccounted for by the sieve, the classifier or the checkpoint —
identical on two families whose launches differ by four orders of magnitude
in line. The budget and the one candidate that fits it are in
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

## In progress

Nothing is running. Both campaigns are paused where the owner stopped
them:

| | A130003 (b = 4) | A110096 (b = 2) |
|---|---|---|
| cursor | `m = 8,945,717,917,245,419,310` | `m = 3,616,316,383,800,763,212,570` |
| filter now | `n = 21` | `n = 19` |
| open term | `a(21)` | `a(19)` |
| odds it should have appeared already | 5.0% | 1.8% |

From those cursors, at each campaign's own measured rate and at the device
rate the same configuration reaches when nothing else is running:

| | `a(21)` of A130003 | | | `a(19)` of A110096 | | |
|---|---|---|---|---|---|---|
| | depth | campaign | device | depth | campaign | device |
| Q1 | `2.84×10¹⁹` | 37 h | 11 h | `1.52×10²³` | 19 h | 8 h |
| median | `8.45×10¹⁹` | 144 h | 41 h | `5.82×10²³` | 76 h | 31 h |
| Q3 | `2.41×10²⁰` | 443 h | 127 h | `1.68×10²⁴` | 220 h | 89 h |
| P90 | `5.51×10²⁰` | 1036 h | 297 h | `3.64×10²⁴` | 477 h | 194 h |

**A110096 is close to running out of range, and A130003 is not.** The
enforced ceiling is the primality-proof bound, `k_ceil(n, b) = 3.317×10²⁴ −
bⁿ`, and the model puts `a(19)` of A110096 below it with probability
**88.5%** — but `a(20)` with probability **19%**, and `a(21)` with **2%**.
A130003 is comfortable by comparison: `a(21)`, `a(22)` and `a(23)` sit
below the ceiling with probability 100%, 100% and 99.8%. So the base-2
family has roughly one more term in it before the ceiling has to be lifted,
and lifting it means wiring huntlib's BLS75 certificates into the
verification path in place of deterministic Miller-Rabin — the machinery is
already built and gated, it is simply not on this path. That is a decision
for whoever resumes, not a defect.

Neither term is overdue: the model gave each only a 5.0% and 1.8% chance
of having appeared by the cursor, so both campaigns were stopped early on
their own ladders rather than stalled on them. And every depth above is the
model's own, from a family of models this repository has caught running
about 2× hot pooled across eleven finds — so read them as floors rather
than forecasts, while noting that this project's own four finds are the
ones that argue the other way.
