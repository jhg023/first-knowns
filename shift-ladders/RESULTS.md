# RESULTS — shift-ladders (A130003, A110096)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

**Six.** Four from the campaigns of 2026-08-23/24 — two on each family,
and on A130003 the first terms anyone has found since Jens Kruse Andersen's
`a(18)` in **June 2007**, nineteen years ago — A110096's `a(19)` from the
campaign of **2026-08-27**, the first run on the re-optimised engine, and
A130003's `a(21)` from the resumed base-4 campaign on **2026-09-01**.

### A130003 (`b = 4`)

#### `a(19) = 13,268,589,982,417,023`

    m = 13268589982417023
    m + 4^k is prime for k = 1 .. 19
    stopped by m + 4^20 = 13269689494044799 = 941 * ...

#### `a(20) = 6,120,156,516,528,136,867`

    m = 6120156516528136867
    m + 4^k is prime for k = 1 .. 20
    stopped by m + 4^21 = 6120160914574647971 = 5581 * ...

#### `a(21) = 285,661,075,490,357,310,517`  — 2026-09-01

    m = 285661075490357310517
    m + 4^k is prime for k = 1 .. 21
    stopped by m + 4^22 = 285661093082543354933
                        = 67 * 271 * 353 * 44568938923273

Twenty-one digits, `15.5×` above `2⁶⁴`, and the third term this project has
put on a sequence whose published frontier had not moved since 2007. It is
the deepest of the base-4 finds by a factor of 47 and it came in **late** —
at `3.4×` its own live median, quantile 0.786 — which is the first draw
this family has produced that agrees with the rest of the repository rather
than arguing against it (see [below](#how-the-finds-scored)).

### A110096 (`b = 2`)

#### `a(17) = 305,948,728,878,647,722,725`

    m = 305948728878647722725
    m + 2^k is prime for k = 1 .. 17
    stopped by m + 2^18 = 305948728878647984869 = 19 * ...

#### `a(18) = 760,056,834,873,121,351,995`

    m = 760056834873121351995
    m + 2^k is prime for k = 1 .. 18
    stopped by m + 2^19 = 760056834873121876283 = 157 * ...

#### `a(19) = 564,052,872,977,379,795,315,735`  — 2026-08-27

    m = 564052872977379795315735
    m + 2^k is prime for k = 1 .. 19
    stopped by m + 2^20 = 564052872977379796364311
                        = 29 * 68902187 * 282285656160457

Twenty-four digits, and `15 mod 30` as the lemma in
[README.md](README.md#the-mathematics-of-the-engine) requires of every
A110096 term above the exception zone. All three A110096 terms are **above
2⁶⁴** — `16.6×`, `41.2×` and `30,577×` it. Carrying candidates as
`(m, off)` from the first commit is what put them in range, and it cost
nothing to do it that way at the start (OPTIMIZATION.md 2.7);
square-ladders retrofitted the same property and paid for it twice.

All six survived all four verification legs below, and every primality
decision in all six is a **proof**, not a probable-prime call — but the
margin is no longer comfortable. The largest value anywhere in the set is
now `564,052,872,977,379,795,840,023`, which is `5.88×` below huntlib's
deterministic Miller-Rabin bound of `3.317×10²⁴`, where before `a(19)` it
was `4,364×`. The certificates still read `deterministic-mr` throughout
(gate G10); one more term on this family will not. The exact integers, all
values `m + b^k`, the certificates and the factor witnesses are in
[`evidence/`](evidence/).

Nothing has been submitted anywhere. These are records; what happens to
them is the owner's decision (CLAUDE.md rule 5).

## The frontier

| | A130003 (b = 4) | A110096 (b = 2) |
|---|---|---|
| Last published term | `a(18) = 1,158,174,141,556,287` | `a(16) = 143,924,005,810,811,655` |
| Found by | Jens Kruse Andersen, **Jun 08 2007** | Bert Dobbelaere, Apr 24 2021 |
| Searched-empty bound inherited | none — the frontier was the term itself | none |
| **Found here** | `a(19)`, `a(20)`, `a(21)` | `a(17)`, `a(18)`, `a(19)` |
| **Open, and next** | `a(22)`, searched-empty below `2.86×10²⁰` | `a(20)`, searched-empty below `5.64×10²³` |
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

The four campaigns classified **140,976 values at run 8 or longer** —
100,919 at base 4 and 40,057 at base 2. Six of them were discoveries and
ten were `[NEAR]`, one condition short of the open term (5 at base 4, 5 at
base 2); every one of the rest was counted and nothing else.

**No find carried a rider.** All six settled exactly one term, and that is
what the model expects at these depths rather than a surprise. A rider
needs `m + b^(n+1)` prime at the value that *stopped* at `n` — and that
value was never sieved, because the campaign's filter was `n`. So its
chance is roughly `S(n+1)/S(n) / log m`, which is 0.19, 0.16, 0.06, 0.12,
0.10 and 0.15 at the six finds: **0.76 riders expected over the six, and a
44% chance of exactly none.** The 0.4-per-step figure this file carried before the
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

**The table below is the 2026-08-23/24 campaigns.** The third and fourth
campaigns' counts are added after it and are NOT scored against the model:
the model column here was computed for the windows and filters those two
campaigns ran, and re-deriving it for further windows at different filters
is work that has not been done. Counting it and saying so is the whole
convention.

Those two campaigns' final tallies, against what the *same* Bateman-Horn
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

### The third campaign (A110096, 2026-08-27)

37,673 classified values in 10.17 hours, sweeping `3.62×10²¹` to
`5.64×10²³` at filter `n = 19`. The right-hand column is the cumulative
tally the checkpoint carries; the extension ratio is `c(r+1) / c(r)`,
printed only where the denominator is 30 or more.

| run | this campaign | cumulative | extends |
|-----|---------------|------------|---------|
| 8 | 23,836 | 25,200 | 0.367 |
| 9 | 8,741 | 9,355 | 0.376 |
| 10 | 3,288 | 3,504 | 0.354 |
| 11 | 1,163 | 1,265 | 0.332 |
| 12 | 386 | 427 | 0.456 |
| 13 | 176 | 207 | 0.312 |
| 14 | 55 | 64 | 0.236 |
| 15 | 13 | 14 | — |
| 16 | 11 | 15 | — |
| 17 | 1 | 2 | — |
| 18 | 2 | 3 | — |
| 19 | 1 | 1 | — |

Pooled over `r = 8 … 14` the extension ratio is **0.367**, against
the **0.424** the first two campaigns measured on this family. The fall is
expected and is roughly the right size: an extension needs one more prime,
so the probability goes as `1 / log m`, and this campaign's line sits two
orders of magnitude higher — `log(5.6×10²³) / log(3.6×10²¹) = 1.10`, and
`0.424 / 1.10 = 0.385` against 0.367 measured. That is a 5%
agreement on a quantity nothing here shares machinery for, but it is not a
clean test: the filter also moved from 17 to 19 between the campaigns, and
the filter changes the sieve retention that the ratio also contains. It is
recorded as a consistency check, not as a validation.

### The fourth campaign (A130003, 2026-08-27 to 2026-09-01)

87,846 classified values in 67.9 hours of sweeping, from `8.95×10¹⁸` to
`2.86×10²⁰` at filter `n = 21` — **6.7× the classification the first
base-4 campaign produced**, and 1.65× what the other three campaigns
produced between them. Same rule as above: the extension ratio is printed
only where the denominator is 30 or more.

| run | this campaign | cumulative | extends |
|-----|---------------|------------|---------|
| 8 | 50,170 | 57,017 | 0.428 |
| 9 | 21,449 | 24,696 | 0.438 |
| 10 | 9,384 | 10,952 | 0.413 |
| 11 | 3,874 | 4,605 | 0.452 |
| 12 | 1,752 | 2,121 | 0.403 |
| 13 | 706 | 872 | 0.411 |
| 14 | 290 | 367 | 0.459 |
| 15 | 133 | 169 | 0.376 |
| 16 | 50 | 68 | 0.480 |
| 17 | 24 | 29 | — |
| 18 | 9 | 12 | — |
| 19 | 3 | 8 | — |
| 20 | 1 | 2 | — |
| 21 | 1 | 1 | — |

Pooled over `r = 8 … 15` the extension ratio is **0.429**, against the
**0.470** the first base-4 campaign measured. The fall is the same `1/log m`
effect the base-2 pair showed and it is the right size:
`log(2.86×10²⁰) / log(8.95×10¹⁸) = 1.079`, and `0.470 / 1.079 = 0.435`
against 0.429 measured — 1.4% on a quantity nothing here shares machinery
for. The same caveat applies: the filter also moved (the first campaign ran
`n = 19`, then 20, then 21; this one ran at 21 throughout), and the filter
changes the sieve retention the ratio also contains. A consistency check,
not a validation.

The row that is not a ratio is run 21: **one value in 87,846**, which is
`a(21)` itself, and run 20 recorded **one** more — the campaign's single
`[NEAR]`, one condition short of the open term, counted and logged on one
line and never evidenced.

This is the census earning its keep, and it is why it is counted rather
than narrated. In square-ladders it settled an overdue term without
stopping the hunt; here it does the opposite job. Two of the six finds
below landed early, at quantiles 0.24 and 0.04, and the census is what says
that is a property of the *waiting time* rather than an intensity that is
too low — a model under-counting hits by the 1.5× those two suggest would
have shown up in 15,457 counted values long before it showed up in two,
and it does not: the counts land at 0.991 and 0.992. The two newest finds
landed at quantiles 0.493 and 0.786, which is the waiting time coming back
to the middle on its own.

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
| A110096 `a(19)` | `5.64×10²³` | `5.82×10²³` | 0.679 | **0.493** |
| A130003 `a(21)` | `2.86×10²⁰` | `8.45×10¹⁹` | 1.543 | **0.786** |

`a(19)` of A110096 landed on the median — quantile 0.493, against the 0.500
a correct model gives, and 3% below its own predicted depth, the closest
call this repository has scored. `a(21)` then landed **late**, at 3.4× its
median and quantile 0.786, which is the first draw this project has
produced that looks like the ones its siblings keep producing.

Two early, two late, two on the nose. Pooled as Poisson exposure the six
finds cost **4.87 expected hits for 6 actual**, an optimism factor of
**0.81×** with an exact (Garwood) 95% interval of **[0.37, 2.21]**. It
still contains 1, and it is still the only point estimate in this
repository that sits *below* it (euler-prime-runs measured 1.9,
dickson-ladders 2.26, square-ladders 3.66) — but the sixth draw moved it
from 0.66× to 0.81×, which is a fifth of the way to the siblings on one
term. Six draws are what six draws are worth. The census above says why
the point estimate is worth believing at all rather than being a
coincidence: the intensity is right to 1%.

The disagreement with the sibling projects is smaller than it was and it is
scored against them in [README.md](README.md#the-odds-model) rather than
papered over. Do not read it as a licence to trust the medians: six draws
still cannot separate 0.81× from 2×, and pooled over the **thirteen** first
occurrences the three ladder projects have now scored between them the
optimism factor is **1.92×**, 95% interval **[1.12, 3.60]** — still
excluding 1, and now on a sample large enough that the interval is
tightening rather than merely moving.

## What the campaign cost

| | A130003 (b = 4) | A110096 (b = 2) | A110096 again (b = 2) | A130003 again (b = 4) |
|---|---|---|---|---|
| started | 2026-08-23 15:53 | 2026-08-24 09:20 | 2026-08-27 01:37 | 2026-08-27 12:05 |
| stopped | 2026-08-24 09:19 | 2026-08-24 09:58 | 2026-08-27 11:49 | 2026-09-01 04:04 |
| **sweep clock** | **17.44 h** | **38.2 min** | **10.17 h** | **67.93 h** |
| first find | `a(19)` at **117 s** | `a(17)` at **9.5 min** | `a(19)` at **10.1 h** | `a(21)` at **67.9 h** |
| second find | `a(20)` at **12.04 h** | `a(18)` at **15.8 min** | — | — |
| line swept | `8.95×10¹⁸` | `3.62×10²¹` | `5.60×10²³` | `2.77×10²⁰` |
| end-to-end rate | `1.42×10¹⁴ m/s` | `1.58×10¹⁸ m/s` | **`1.53×10¹⁹ m/s`** | **`1.13×10¹⁵ m/s`** |

**Six terms for 96.2 hours of one GPU**, on two sequences that had stood
for nineteen and five years. `a(19)` of A130003 arrived 117 seconds into
the first campaign, which is what a nineteen-year-old frontier with no
published bound below it looks like once the engine is right.

**The fourth column is a sweep clock, not a calendar.** Its 67.93 h is the
figure the base-4 checkpoint carries — time actually spent sweeping,
accumulated across the several runs the stretch took — against a calendar
gap of 112 h between the start and the find. The difference is not idle
GPU: two of those runs were ended by a checkpoint save that `os.replace`
could not land because another process held a handle on the file, which on
Windows fails a rename outright. Neither death was corruption and the
cursor was intact one segment behind each time, so nothing was lost but the
restarts. That is what CLAUDE.md rule 5d and `drills.lock_drill` were
written for, and after the fix a save that cannot land defers instead of
ending the campaign.

Those end-to-end rates were **not** the engine's rates: the campaigns ran
at 29% and 41% of what the kernel does in the same configuration. The cause
was neither the kernel nor the verification — it was `check_rungs`
rebuilding the progress ladder from the odds model once per segment, 1,080
numerical integrals for an answer that changes only when a term is found,
and **roughly four fifths of the 17-hour base-4 campaign went into it.**
It has since been fixed (the ladder is cached on the frontier), measured at
**3.47× and 2.42×** on the real segment loop. A second pass then found the
engine's wheel top four primes short at base 4 and six at base 2 — the cost
model priced a bit-plane read at four times what it costs — and took base
2's flat table to `p1 = 41`, for a further **1.537× and 2.380×**
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)).

**The third campaign is the check on all of that, and it beat the
projection.** Predicted `1.07×10¹⁹ m/s`; measured `1.53×10¹⁹` end to end
over 10.17 hours and `5.60×10²³` of line — **9.7×** the campaign that found
`a(17)` and `a(18)` three days earlier, and 1.43× the projection itself.
The projection was conservative because it discounted the engine rate by a
device share measured on the OLD configuration, where the launch was eight
times shorter in periods and the per-launch host costs were charged against
a smaller launch. The first four terms were found the slow way, at a
nineteenth and a twenty-fifth of what the engine now does.

**The fourth campaign is the same check at base 4, and it also came in
above its projection.** Its first minutes measured `8.20×10¹⁴ m/s`; over
67.93 h and `2.77×10²⁰` of line it sustained **`1.13×10¹⁵ m/s`** —
**1.38×** the opening measurement and **7.97×** the campaign that found
`a(19)` and `a(20)`.

That end-to-end figure is derived from the checkpoint (`elapsed` against
swept `m`), so it was checked against the engine directly before being
published: a bare device loop at this exact configuration, timed over eight
launches at each end of the window the campaign swept, measures
`1.20×10¹⁵ m/s` at `m ≈ 8.95×10¹⁸` and `1.24×10¹⁵` at `m ≈ 2.85×10²⁰`. The
campaign ran at **92%** of that, and the missing 8% is the host — the
classification pool, the checkpoint writes and the verifications — which is
what a campaign that is *not* the thing to optimise next looks like. It is
also `1.43×` the `7.92×10¹⁴` the paired A/B harness reports for the same
configuration, and that gap is the harness rather than the engine: it runs
two engines alive in one process and alternates arms, which is exactly the
setup OPTIMIZATION.md Rule 3 keeps for its *ratios* and warns against
reading absolutes from.

## Where it stands

**Both families are PAUSED.** A130003 stopped at the find, with its cursor
at `m = 285,661,108,252,160,470,830` — eleven seconds and one launch past
`a(21)` — and A110096 stopped at `m = 5.64×10²³` on 2026-08-27. Each
resumes from its own checkpoint under its own config key with the filter
already promoted to the term it would be hunting.

**A130003's next term is a month of GPU, not a day.** `a(22)` at the
measured `1.13×10¹⁵ m/s`, with the depths re-derived from `a(21)`:

| | `a(22)` of A130003 | |
|---|---|---|
| | depth | **at `1.13×10¹⁵ m/s`** |
| Q1 | `1.15×10²¹` | **8.9 days** |
| median | `3.22×10²¹` | **30.1 days** |
| Q3 | `8.74×10²¹` | **86.6 days** |
| P90 | `1.94×10²²` | **195.8 days** |

That is the cost of the term this project just bought: each extra condition
costs a further factor of about `log m` of line, and the last three finds
on this family sat at `1.3×10¹⁶`, `6.1×10¹⁸` and `2.9×10²⁰`. The proof
ceiling is no longer far away here either — `a(22)` and `a(23)` sit below
it with probability 100% and 99.8%, but `a(24)` is **54.6%**, so base 4 has
about two terms of room left before it meets the same wall base 2 already
has.

**A110096 has run out of ceiling, not out of engine.** With `a(19)` found
at `5.64×10²³`, the enforced bound `k_ceil(n, b) = 3.317×10²⁴ − bⁿ` is only
`5.9×` above the largest value already proved, and the model puts `a(20)`
below it with probability **13.4%** and `a(21)` with **1.4%**:

| term | Q1 | median | Q3 | P90 | P(below the ceiling) |
|------|----|--------|----|-----|----------------------|
| A110096 a(20) | `7.39×10²⁴` | **`2.39×10²⁵`** | `6.45×10²⁵` | `1.36×10²⁶` | **13.4%** |
| A110096 a(21) | `2.08×10²⁶` | **`7.89×10²⁶`** | `2.25×10²⁷` | `4.85×10²⁷` | **1.4%** |

At `1.53×10¹⁹ m/s` the median of `a(20)` is about **18 days** of sweeping,
and seven times out of eight the term is not there to be found: the engine
would refuse the line before reaching it. Continuing that family means
wiring huntlib's BLS75 certificates into the verification path in place of
deterministic Miller-Rabin — the machinery is already built and gated, it
is simply not on this path. That is a decision for the owner, not a defect,
and it is now the *only* thing standing between this engine and `a(20)`.

Every depth above is the model's own, from a family of models this
repository has caught running about 2× hot pooled across thirteen finds —
so read them as floors rather than forecasts. This project's own six finds
are still the ones that argue the other way, at 0.81×, but by less than
they did: the sixth landed at quantile 0.786, and the `a(22)` medians above
would be nearer their Q3s if the pooled 1.92× is the real number.
