# RESULTS — square-ladders (A089761)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

**None yet.** No production sweep has been run. The engine, the gate
battery and the odds model are complete and green; the campaign is the
owner's to start (CLAUDE.md rule 0a).

## The frontier, as this project inherits it

| | |
|---|---|
| Last published term | `a(15) = 861,066,640` |
| Last term anyone *searched* for | `a(11)`, Donovan Johnson, Sep 27 2008 — the same integer |
| Searched-empty bound | `a(16) > 1.4×10¹³`, Max Alekseyev |
| Upper bound | none published, at any open `n` |

The plateau is the whole story of this sequence's frontier, so it is worth
stating exactly. `k = 861,066,640` was found as `a(11)`. It then satisfied
`i = 12, 13, 14, 15` with no further search, which is why five published
terms share one value. Its run stops at exactly one composite:

    861066640 * 16^2 + 1 = 220433059841 = 47 * 149 * 31476947

That factorization — checkable on a calculator — is the entire reason
`a(16)` is open, and gate G1 asserts it on every run: the champion reaches
exactly 15, and its 16th value is composite.

## What a find will look like

A survivor `k` with run length `r` is classified against the live frontier
(`event_kind` in `launch.py`, drilled in the selftest):

| run | class | what happens |
|-----|-------|--------------|
| `r > frontier` | **DISCOVERY** | settles `a(frontier+1) … a(r)` at once; verified three ways plus a factor witness for the composite that stops the run; one evidence JSON; logged once |
| `r == frontier` | **NEAR** | one condition short of the open term — one line with its campaign ordinal, verified by the cheap legs as an engine health check, never evidenced |
| `8 ≤ r < frontier` | **CENSUS** | counted in the `[STATUS]` heartbeat, never narrated |
| `r < 8` | — | not even counted |

Because the conditions nest, a single find can settle several terms — a run
of 18 would settle `a(16)`, `a(17)` and `a(18)` together, each logged once
and all evidenced under the first. The odds of that are modest and stated
honestly: at `k ≈ 2×10¹⁵` each extra condition rides with probability about
0.14, so one find yields **1.16 terms in expectation**. Plan on `a(16)`;
treat `a(17)` as a bonus.

## Verification every claim must survive

1. **huntlib's Miller-Rabin.** Deterministic here, not probabilistic: at
   the enforced ceiling the largest value is `2.3×10²¹`, under the
   `3.317×10²⁴` bound (gate G10). This project proves its primes.
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
--status` prints them.

## In progress

Nothing is running. The reachable ladder, at the reproducible production
rate of 2.86×10¹³ k/s and against the model stated in
[README.md](README.md):

- `a(16)` — median **76 s**, P90 9.2 min
- `a(17)` — median **34 min**, P90 4.4 h
- `a(18)` — median **19.3 h**, Q3 2.6 days; its P90 sits above the engine
  ceiling

Sweeping the engine's entire enforced range (`k < 9×10¹⁸`) takes about
**3.6 days**, after which `a(16)`, `a(17)` and `a(18)` are each either
found or bounded below `9×10¹⁸` — a bound that would itself be new, since
none is published at any open `n`.
