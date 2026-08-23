# RESULTS — shift-ladders (A130003, A110096)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

**None yet.** The engine, the gate battery and the benchmark are green and
no production sweep has been run; starting one is the owner's command
(CLAUDE.md rule 0a). This file is the shape the first find will be
recorded in, and it is here from the first commit so that nothing about
the format is decided under the excitement of a discovery.

## The frontier

| | A130003 (b = 4) | A110096 (b = 2) |
|---|---|---|
| Last published term | `a(18) = 1,158,174,141,556,287` | `a(16) = 143,924,005,810,811,655` |
| Found by | Jens Kruse Andersen, **Jun 08 2007** | Bert Dobbelaere, Apr 24 2021 |
| Searched-empty bound inherited | none — the frontier is the term itself | none |
| **Open, and next** | `a(19)` | `a(17)` |
| Upper bound | none published, at any open `n` | none published, at any open `n` |

Neither entry carries a published bound of any kind, so the floor for each
next term is monotonicity alone — which is free, because the conditions
nest: `a(n+1) ≥ a(n)`.

Each frontier term stops at exactly one composite, and gate G1 asserts
both on every run:

    1158174141556287 + 4^19 = 1158449019463231   (composite)
     143924005810811655 + 2^17 = 143924005810942727   (composite)

## What a find will look like

A survivor `m` with run length `r` is classified against the live frontier
(`event_kind` in `launch.py`, drilled in the selftest):

| run | class | what happens |
|-----|-------|--------------|
| `r > frontier` | **DISCOVERY** | settles `a(frontier+1) … a(r)` at once; verified three ways plus a factor witness for the composite that stops the run; one evidence JSON; logged once |
| `r == frontier` | **NEAR** | one condition short of the open term — one line with its campaign ordinal, verified by the cheap legs as an engine health check, never evidenced |
| `8 ≤ r < frontier` | **CENSUS** | counted in the `[STATUS]` heartbeat, never narrated |
| `r < 8` | — | not even counted |

Because the conditions nest, a single find can settle several terms at
once, each logged once and all evidenced under the first. Both sequences
say how often that happens: A130003's `a(10) = 4503` settled five terms,
and A110096 has riders at six indices out of sixteen. The model puts the
chance of an extra condition at about 0.4 per step — much higher than in
this repo's square ladders, because the values are all the same size here
(`m + b^k ≈ m` for every `k`) instead of growing with `i²`.

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

The census is worth reading even when nothing is found: it is what
distinguishes a broken engine from a long wait. square-ladders spent a day
with an overdue term and the question was settled without stopping the
hunt, by comparing counts per run length against the same model's
intensity folded with the sieve's own retention — 86,531 classified
survivors at 1.02× prediction. Expect to do the same here.

## In progress

Nothing is running, and nothing has been swept. Both campaigns start at
their published frontiers:

| | starts at | first open term | model median | v1 wall clock |
|---|---|---|---|---|
| A130003 | `1.16×10¹⁵` | `a(19)` | `5.75×10¹⁶` | ~3 h |
| A110096 | `1.44×10¹⁷` | `a(17)` | `2.03×10²⁰` | ~3 h |

at the v1 engine's measured `5.2×10¹² m/s` (base 4) and `2.1×10¹⁶ m/s`
(base 2) — see [BENCHMARKS.md](BENCHMARKS.md). Those medians are floors:
this repo's first-occurrence models run late by about 3× (README, "The odds
model"), so budget 6-9 hours per headline term and do not read a term that
has not arrived on the median as evidence of a fault.

The terms after those are where the v1 engine runs out of road —
A130003 `a(20)` is ~3 days and A110096 `a(18)` ~10 days at v1 rates, both
of which the first optimization is expected to cut by more than an order
of magnitude ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)).
