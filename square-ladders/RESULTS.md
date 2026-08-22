# RESULTS — square-ladders (A089761)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

Two, from the campaign of 2026-08-21/22 — the first terms of A089761 found
by anyone since Donovan Johnson's `a(11)` in September 2008, and the first
that break the five-term plateau.

### `a(16) = 15,737,271,507,027,492`

    k = 15737271507027492
    k*i^2 + 1 is prime for i = 1 .. 16
    stopped by k*17^2 + 1 = 4548071465530945189 = 317 * ...

### `a(17) = 125,811,821,444,034,258`

    k = 125811821444034258
    k*i^2 + 1 is prime for i = 1 .. 17
    stopped by k*18^2 + 1 = 40763030147867099593 = 109 * ...

Both survived all four verification legs below, and every primality
decision in both is a **proof**, not a probable-prime call: each value is
under huntlib's deterministic Miller-Rabin bound, so the certificates read
`deterministic-mr` throughout (gate G10). The exact integers, all values
`k*i^2+1`, the certificates and the factor witnesses are in
[`evidence/`](evidence/).

Nothing has been submitted anywhere. These are records; what happens to
them is the owner's decision (CLAUDE.md rule 5).

## The frontier

| | |
|---|---|
| Last published term | `a(15) = 861,066,640` |
| Last term anyone *searched* for, before this | `a(11)`, Donovan Johnson, Sep 27 2008 — the same integer |
| Searched-empty bound this project inherited | `a(16) > 1.4×10¹³`, Max Alekseyev |
| **Found here** | `a(16)`, `a(17)` — above |
| **Open, and next** | `a(18)`, searched-empty below `7.25×10¹⁸` |
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
how it played out: `a(16)` and `a(17)` arrived as two separate finds, each
settling exactly one term, neither riding on the other.

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
--status` prints them.

## In progress

Nothing is running. The cursor stands at `k = 7,246,150,428,712,325,130`
after 13.5 hours, with `a(18)` open and its first two rungs (Q1, median)
passed without a find.

That is not a surprise and it is not bad luck — it is where the v3.4
engine ran out of addressable range. Conditioned on `a(18) > 7.25×10¹⁸`,
the model puts its median at `1.35×10¹⁹` and its **Q3 at `2.11×10¹⁹`,
which is past `2⁶⁴`**. The v4 engine (see
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)) exists because of that number:
its ceiling is the primality-proof bound `1.02×10²²`, not a machine word,
so the hunt now ends when the term is found rather than when the engine
gives out.

From the current cursor, at the measured end-to-end campaign rate of
`1.49×10¹⁴ k/s`:

- `a(18)` — median **11.7 h**, Q3 25.8 h, P90 2.0 days, P99 5.0 days
- `a(19)` — Q1 `1.71×10¹⁹`, median `6.98×10¹⁹`; both now inside the
  engine's range, where under v3.4 neither was
