# RESULTS — linear-ladders (A088250 and its cluster)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

**None yet.** The project was built and gated on 2026-09-03; no campaign
has been run. When a find lands it will appear here after its evidence
file has been re-verified from disk (the protocol re-run independently,
every value re-tested with sympy, the stopper's factor re-multiplied), in
this shape:

> ### A088250 a(15) = … — date, time
> - **run 15**: `r·k + 1` is prime for `r = 1..15`; the 15th value is
>   `15·k + 1 = …`.
> - **stopper**: `16·k + 1 = … = p × …`.
> - **certificates**: which route each value took (`deterministic-mr`
>   under the bound, `bls75-thm1` past it), all re-verified.
> - **also settles**: `A202778(15) = k` (the exact-run version, if the run
>   is exactly 15), `A071576(15) = k/2`.
> - **model**: `E` at the find, `k / median`.
> - evidence: `evidence/A088250_a15_<k>.json`

Each find is a **first occurrence**: every `k` from `K_START = 10⁶` to the
find swept and every survivor classified in `k` order, and below `K_START`
the claim rests on monotonicity (every family's frontier is far above it).
The least-claim basis is written into every evidence file: `swept_from`,
`swept_to`, the wheel period `W = 32,589,158,477,190,044,730` (the product
of the primes to 53, the unit included), the unit, the sieve depth 65536
and the monotone floor, under the engine key.

## The census

Counts per run length from each family's checkpoint, as printed in every
`[STATUS]` line. A run one short of the open term is a `[NEAR]` line with
its ordinal; everything shorter is a count and nothing else. No campaign
has run, so there is no census yet.

## In progress — built 2026-09-03, no campaign run

Every family opens at the index after its published frontier, inside
period 0 of the wheel, clipped at `k = 10⁶`. The odds model's pre-run
predictions (`model_results.json`, [README.md](README.md#the-odds-model))
put the next terms and their chances under each family's ceiling at:

| family | frontier | open next | median | under the ceiling |
|---|---|---|---|---|
| A088250 | a(14) = 11,429,352,906,540,438,870 (Resta, 2017) | a(15) | `2.0×10²⁰` | a(15), a(16): ~100%; a(17) 68%; a(18) 4% (ceiling `3.317×10²⁴`) |
| A173750 | a(15) = 4,646,092,391,146,085,880 (Resta, 2017) | a(16) | `1.9×10²⁰` | a(16), a(17): ~100%; a(18) 66% |
| A125838 | a(14) = 8,047,290,924,923,250 (Resta, 2017) | a(15) | `2.3×10¹⁸` | a(15)–a(17): ~100%; a(18) 13% (ceiling `1.8×10²³`, the crossing) |
| A125839 | a(15) = 45,187,548,280,664,790 (Resta, 2017) | a(16) | `2.7×10¹⁸` | a(16)–a(18): ~100%; a(19) 18% |
| A164325 | a(15) = 10,718,654,377,787,155,800 (Resta, 2017) | a(16) | `4.9×10²¹` | a(16): ~100%; a(17) 85%; a(18) 9% |
| A164326 | a(14) = 68,086,992,545,221,650 (Resta, 2017) | a(15) | `6.2×10¹⁹` | a(15), a(16): ~100%; a(17) 16% |
| A088651 | a(15) = 53,792,264,108,455,702,830 (J. K. Andersen, 2008) | a(16) | `2.3×10²²` | a(16) 96%; a(17) 15% |

Read every median as a floor: this repository's finds have landed at
1.9–2.5× their medians on average. Where each campaign stands is read with
`python launch.py --status --family <name>`; the hunt itself is the
owner's command ([README.md](README.md#running-it)).
