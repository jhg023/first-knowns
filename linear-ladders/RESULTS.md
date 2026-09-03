# RESULTS — linear-ladders (A088250 and its cluster)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

## Verified finds

All three below come from the single A088250 campaign of 2026-09-03: the
v2 engine with no flags, from `k = 10⁶` to the family's ceiling in 1.26 h
of wall clock (started 17:59, stopped 19:15 at the last whole wheel period
under `3.317×10²⁴`). Each evidence file was re-verified from disk before
this page was written: every value re-tested with sympy's BPSW, the run
re-derived from the bare definition (`lladder_reference.run_length`), the
stopper's factor re-multiplied, every certificate re-verified by
`huntlib.certificate.verify`, the derived claims re-derived, and the
least-claim basis read back. Model figures are from `lladder_model`, each
scored from the frontier that was known when the search for that term
began.

### A088250 a(15) = 1,555,360,041,314,493,173,760 — 2026-09-03, 18:00

- **run 15**: `r·k + 1` is prime for `r = 1..15`; the 15th value is
  `15·k + 1 = 23,330,400,619,717,397,606,401`.
- **stopper**: `16·k + 1 = 24,885,760,661,031,890,780,161 = 19 ×
  1,309,776,876,896,415,304,219`, so the run is exactly 15.
- **certificates**: all 15 values under the deterministic Miller–Rabin
  bound (`k` is under the proof crossing `k_proof(15) = 2.21×10²³`), all
  `deterministic-mr`, all re-verified.
- **also settles**: `A202778(15) = 1,555,360,041,314,493,173,760` (the run
  is exact) and `A071576(15) = 777,680,020,657,246,586,880`.
- **model**: from `a(14)`, median `1.98×10²⁰`, P90 `9.69×10²⁰`; the find
  is at `k / median = 7.9`, `E = 3.24` — beyond the P90, the latest of the
  three against its model.
- **when**: 65 s into the campaign, at the close of period 0, exactly as
  the README's first-lines paragraph predicted.
- `k = 2¹² · 3 · 5 · 7 · 11 · 13 · 17 · 1213 · 1226410699`.
- evidence: `evidence/A088250_a15_1555360041314493173760.json`

### A088250 a(16) = 87,117,680,854,368,555,070,680 — 2026-09-03, 18:10

- **run 16**: `r·k + 1` prime for `r = 1..16`; the 16th value is
  `16·k + 1 = 1,393,882,893,669,896,881,130,881`.
- **stopper**: `17·k + 1 = 1,481,000,574,524,265,436,201,561 = 9199 ×
  160,995,822,863,818,397,239`.
- **certificates**: 16 `deterministic-mr` (`k` under the crossing
  `k_proof(16) = 2.07×10²³`), all re-verified.
- **also settles**: `A202778(16) = k` and
  `A071576(16) = 43,558,840,427,184,277,535,340`.
- **model**: from `a(15)`, median `2.83×10²²`, P90 `1.37×10²³`;
  `k / median = 3.1`, `E = 1.65`.
- **when**: 11 min in.
- `k = 2³ · 3² · 5 · 7 · 11² · 13 · 17 · 19 · 67 · 52957 · 19176809`.
- evidence: `evidence/A088250_a16_87117680854368555070680.json`

### A088250 a(17) = 1,048,124,771,278,912,649,231,910 — 2026-09-03, 18:49

- **run 17**: `r·k + 1` prime for `r = 1..17`; the 17th value is
  `17·k + 1 = 17,818,121,111,741,515,036,942,471`.
- **stopper**: `18·k + 1 = 18,866,245,883,020,427,686,174,381 = 23 ×
  820,271,560,131,322,942,877,147`.
- **certificates**: `k` is **past the proof crossing** `k_proof(17) =
  1.95×10²³`, so the classification that found it was a strong
  probable-prime chain and the discovery is proved by certificate: the
  three values under the bound (`r = 1, 2, 3`) by `deterministic-mr`, the
  other fourteen by **BLS75 Theorem 1** on `N − 1 = r·k`, `k` factored
  once, every prime factor under the bound. All 17 re-verified from
  scratch, twice: by the launcher before the file was written and from
  disk for this page. The first find in this repository's linear-ladder
  cluster to need the certificate route.
- **also settles**: `A202778(17) = k` and
  `A071576(17) = 524,062,385,639,456,324,615,955`.
- **model**: from `a(16)`, median `1.98×10²⁴`, Q1 `6.95×10²³`;
  `k / median = 0.53`, `E = 0.41` — early.
- **when**: 50 min in.
- `k = 2 · 3² · 5 · 7 · 11 · 13 · 17² · 19 · 71 · 3593 · 8305568963`.
- evidence: `evidence/A088250_a17_1048124771278912649231910.json`

Across the three finds the model's `E` averages 1.77 and `k / median`
runs 7.9, 3.1, 0.53 (geometric mean 2.3): the same "intensity right,
first occurrence late" pattern the repository's other ladder projects
recorded, one draw at a time.

### A bound: A088250 a(18) > 3,316,761,604,016,016,802,395,750

After `a(17)` the campaign promoted its filter to `n = 18` and swept on to
the last whole wheel period under the engine ceiling, `k =
3,316,761,604,016,016,802,395,750 = 1725 × 1.92×10²¹`, classifying every
survivor and finding no run of 18. So **no `k < 3.3168×10²⁴` has
`r·k + 1` prime for all `r = 1..18`**, the first bound of any kind on
A088250 at an open index. The claim is sound above the proof crossing
too: past `k_proof(18) = 1.84×10²³` the seven-base chain is a
probable-prime test, and a composite that passed it could only *lengthen*
a run, never hide one — a true run of 18 would have passed every test and
been claimed. The model, from `a(17)`, had put `a(18)` under the ceiling
with 2.1% and puts its median at `2.2×10²⁶`, 66× the ceiling; reaching it
needs the ceiling raised (a certificate that recurses into the factors of
`k`; priced in [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)), not more
sweeping.

Each find is a **first occurrence**: every `k` from `K_START = 10⁶` to the
find swept and every survivor classified in `k` order, and below `K_START`
the claim rests on monotonicity (`a(14) = 1.14×10¹⁹`). The least-claim
basis is written into every evidence file: `swept_from`, `swept_to`, the
wheel period `W = 1,922,760,350,154,212,639,070` (the product of the
primes to 59, the unit included), the unit 30030, the sieve depth 65536
and the monotone floor, under the engine key
`a088250-v2-u30030-p137-p247-p359-q265536-seg32`.

## The census

Counts per run length from the A088250 checkpoint, as printed in every
`[STATUS]` line (the finds themselves are included at their run lengths):

    8: 9269   9: 3424   10: 1251   11: 443   12: 146   13: 70   14: 26
    15: 4   16: 1   17: 1        near 8        survivors 47,258,905

Eight values reached the settled frontier and no further while a term was
open (`[NEAR]` lines); everything shorter is a count and nothing else.

## The campaign against its benchmark (the rule 5g acceptance test)

From the evidence timestamps and the checkpoint, per filter:

| filter | line swept | wall clock | campaign rate | benchmark ([BENCHMARKS.md](BENCHMARKS.md)) |
|---|---|---|---|---|
| n = 15 (period 0) | `1.92×10²¹` | 65 s, pool sizing included | `3.0×10¹⁹ k/s` | `3.07×10¹⁹` |
| n = 16 | `8.5×10²²` | 10.1 min | `1.4×10²⁰` | `1.38×10²⁰` |
| n = 17 | `9.6×10²³` | 39.2 min | `4.1×10²⁰` | `3.99×10²⁰` |
| n = 18 | `2.27×10²⁴` | 25.4 min | `1.49×10²¹` | `1.45×10²¹` |

Every phase ran at its benchmark's rate with no flags. The whole campaign
took 1.26 h against the 2.5 h budgeted at the medians, because `a(17)`
landed at half its median and the remaining line was swept at the n = 18
rate.

## In progress

| family | frontier | open next | median | under the ceiling |
|---|---|---|---|---|
| A088250 | **a(17) = 1,048,124,771,278,912,649,231,910 (this project, 2026-09-03)** | a(18) > `3.3168×10²⁴` (swept empty to the ceiling) | `2.2×10²⁶` | 0% — the campaign is at its ceiling |
| A173750 | a(15) = 4,646,092,391,146,085,880 (Resta, 2017) | a(16) | `1.9×10²⁰` | a(16), a(17): ~100%; a(18) 66% |
| A125838 | a(14) = 8,047,290,924,923,250 (Resta, 2017) | a(15) | `2.3×10¹⁸` | a(15)–a(17): ~100%; a(18) 13% (ceiling `1.8×10²³`, the crossing) |
| A125839 | a(15) = 45,187,548,280,664,790 (Resta, 2017) | a(16) | `2.7×10¹⁸` | a(16)–a(18): ~100%; a(19) 18% |
| A164325 | a(15) = 10,718,654,377,787,155,800 (Resta, 2017) | a(16) | `4.9×10²¹` | a(16): ~100%; a(17) 85%; a(18) 9% |
| A164326 | a(14) = 68,086,992,545,221,650 (Resta, 2017) | a(15) | `6.2×10¹⁹` | a(15), a(16): ~100%; a(17) 16% |
| A088651 | a(15) = 53,792,264,108,455,702,830 (J. K. Andersen, 2008) | a(16) | `2.3×10²²` | a(16) 96%; a(17) 15% |

The six siblings open at the index after their published frontier, inside
period 0 of the wheel, clipped at `k = 10⁶`; their medians are the odds
model's pre-run predictions (`model_results.json`). Read every median as a
floor: this repository's finds, these three included, have landed at about
2× their medians on average. Where each campaign stands is read with
`python launch.py --status --family <name>`; the hunt itself is the
owner's command ([README.md](README.md#running-it)).
