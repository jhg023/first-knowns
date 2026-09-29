# RESULTS — decimal-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

**Letters.** A305740's term is **k** (its exponent m); A153431's term is
**m** (its exponent k). Every find below, every evidence file and every log
line uses the entry's own letter for the term; `oeis_terms` in an evidence
file is what to submit (README "Notation").

## Verified finds

**Nine terms: a(13) through a(18) of A305740 and a(14) through a(16) of
A153431**, found 2026-09-24/29 by one campaign per family, `python launch.py
--family F`, no flags. A305740 had stood at a(12) since Giovanni Resta's
June 2018 term, A153431 at a(13) since Don Reble's July 2022 terms.

Each evidence file was re-verified from disk on 2026-09-29 by a harness
that shares nothing with the launcher: the published prefix read from the
OEIS data (A305740 through a(12), A153431 through a(13), both unchanged),
every value rebuilt as 10^j·x + 1 and re-tested with sympy's `isprime`, the
run re-derived from the bare definition (exactly n, the next exponent
composite), the stopper's factor re-divided, every certificate re-verified
by `huntlib.certificate.verify` AND by a from-scratch BLS75 Theorem 1 check
(factors proved prime by sympy, F | V − 1, F > √V, the Fermat and gcd
conditions per prime), each find above its predecessor, the forced unit
dividing it, and each ledger matched to its files. **9 files, 141
certificates (40 `deterministic-mr`, 101 BLS75 Theorem 1), all green;
nothing is `unproved`.** Every file also carries the launcher's three-way
verification (huntlib's Miller–Rabin chain, sympy's BPSW, a re-sieve by the
CPU engine on a different wheel) and a `least_claim`.

Model figures are from `decl_model`, each scored from the floor the sweep
for that term actually started at (the previous term, or the sibling's
floor where it was higher — see "The least-claim basis" below). Times are
the ledger's, local, in discovery order.

### A153431 — one campaign, 2026-09-24, to 17:17

`python launch.py --family A153431`, from a(13) = 43,000,687,652,274,618 —
run first, as the README recommended, so that each term it settled would
raise A305740's floor. Forms m·10^k + 1, k = 0..n: n + 1 values per run.
Stopped by the owner right after a(16), 8.38 hours of campaign clock.

#### a(14) = 5,947,629,516,975,297,508 — 09-24 08:55:11

- **run 14**: m·10^k + 1 prime for k = 0..14; the top value is
  594,762,951,697,529,750,800,000,000,000,001 (33 digits). **stopper**
  m·10^15 + 1 = 19 × 313,033,132,472,384,079,368,421,052,631,579.
- 15 certificates: 6 `deterministic-mr`, 9 BLS75 Theorem 1.
- **model**: from a(13), median 1.25e18; m / median = 4.75, E = 2.30 (the
  90th percentile).
- m = 2² · 7 · 17² · 1103 · 803333 · 829501.
- swept from a(13) at unit 14, filter 14, sieve 2^18.
- evidence: `evidence/A153431_a14_5947629516975297508.json`

#### a(15) = 740,560,706,756,591,347,900 — 09-24 09:09:46

- **run 15**: the top value is
  740,560,706,756,591,347,900,000,000,000,000,001 (36 digits). **stopper**
  m·10^16 + 1 = 19 × 389,768,793,029,784,919,947,368,421,052,631,579.
- 16 certificates: 4 `deterministic-mr`, 12 BLS75 Theorem 1.
- **model**: from a(14), median 1.74e20; m / median = 4.26, E = 2.15 (88th
  percentile).
- m = 2² · 5² · 7² · 13 · 17 · 23 · 59 · 631 · 798662153. **It ends in 0,
  so a(15)/10 is A305740's a(16)** (below).
- swept from a(14) at unit 238, filter 15; 14.6 minutes after a(14).
- evidence: `evidence/A153431_a15_740560706756591347900.json`

#### a(16) = 76,993,117,812,161,143,387,438 — 09-24 17:17:01

- **run 16**: the top value is
  769,931,178,121,611,433,874,380,000,000,000,000,001 (39 digits).
  **stopper** m·10^17 + 1 = 19 ×
  405,226,935,853,479,702,039,147,368,421,052,631,579.
- 17 certificates: 2 `deterministic-mr`, 15 BLS75 Theorem 1.
- **model**: from a(15), median 1.31e22; m / median = 5.89, E = 2.87 (94th
  percentile).
- m = 2 · 7 · 17 · 38749 · 5106559 · 1634880811.
- swept from a(15) at unit 238, filter 16; 8.12 hours after a(15).
- evidence: `evidence/A153431_a16_76993117812161143387438.json`

### A305740 — one campaign, 2026-09-24 17:54 to 2026-09-29 03:13

`python launch.py --family A305740`, from a(12) = 54,717,848,613,610, with
A153431's three terms already in `evidence/`, so the sweeps for a(14)
through a(17) started at the sibling's floor. Forms 10^m·k + 1, m = 1..n.
a(14) through a(16) within 113 seconds of a(13), a(17) 3.6 hours later,
a(18) after about 90 more hours of campaign clock (93.64 hours in all).
Stopped by the owner right after a(18).

#### a(13) = 565,988,659,871,355 — 09-24 17:54:35

- **run 13**: 10^m·k + 1 prime for m = 1..13; the top value is
  5,659,886,598,713,550,000,000,000,001 (28 digits). **stopper**
  10^14·k + 1 = 269 × 210,404,706,271,879,182,156,133,829.
- 13 certificates: 9 `deterministic-mr`, 4 BLS75 Theorem 1.
- **model**: from a(12), median 2.61e14; k / median = 2.17, E = 1.47 (77th
  percentile).
- k = 3² · 5 · 7 · 523 · 601 · 5716379.
- swept from a(12) at unit 7, filter 13, sieve 2^20 (no sibling floor:
  A153431(12) / 10 is below a(12)).
- evidence: `evidence/A305740_a13_565988659871355.json`

#### a(14) = 44,425,047,432,820,299 — 09-24 17:54:46

- **run 14**: the top value is 4,442,504,743,282,029,900,000,000,000,001
  (31 digits). **stopper** 10^15·k + 1 = 19 ×
  2,338,160,391,201,068,368,421,052,631,579.
- 14 certificates: 7 `deterministic-mr`, 7 BLS75 Theorem 1.
- **model**: from the sibling's floor 4.30e15, median 1.69e16; k / median =
  2.64, E = 1.83 (84th percentile).
- k = 3 · 7 · 17 · 29 · 101 · 42485458783.
- swept from ⌈A153431(13)/10⌉ = 4,300,068,765,227,462 (the published a(13))
  at unit 7, filter 14.
- evidence: `evidence/A305740_a14_44425047432820299.json`

#### a(15) = 1,425,893,521,857,802,536 — 09-24 17:55:05

- **run 15**: the top value is
  1,425,893,521,857,802,536,000,000,000,000,001 (34 digits). **stopper**
  10^16·k + 1 = 401 × 35,558,441,941,591,085,685,785,536,159,601 (the
  cofactor is prime).
- 15 certificates: 6 `deterministic-mr`, 9 BLS75 Theorem 1.
- **model**: from the sibling's floor 5.95e17, median 1.70e18; k / median =
  0.84, E = 0.53 (41st percentile).
- k = 2³ · 3 · 7 · 11 · 17 · 23 · 743 · 2655947939.
- swept from ⌈A153431(14)/10⌉ = 594,762,951,697,529,751 (this project's
  a(14)) at unit 7, filter 15.
- evidence: `evidence/A305740_a15_1425893521857802536.json`

#### a(16) = 74,056,070,675,659,134,790 — 09-24 17:56:28

- **run 16**: the top value is
  740,560,706,756,591,347,900,000,000,000,000,001 — the same integer as
  A153431 a(15)'s, because **k = A153431(15)/10 exactly**: the sibling's
  floor was itself a solution (the least claim's `swept_from_k` and
  `swept_to_k` are the same integer).
  **stopper** 10^17·k + 1 = 19 ×
  389,768,793,029,784,919,947,368,421,052,631,579, again A153431 a(15)'s.
- 16 certificates: 4 `deterministic-mr`, 12 BLS75 Theorem 1.
- **model**: not a draw. It is A153431 a(15)'s event read through the shift
  (an A153431 term that ends in 0 IS 10 × an A305740 term one index up), so
  it is scored there and not twice.
- k = 2 · 5 · 7² · 13 · 17 · 23 · 59 · 631 · 798662153.
- least claim: nothing below ⌈A153431(15)/10⌉ can have a run of 16, and
  this is that number.
- evidence: `evidence/A305740_a16_74056070675659134790.json`

#### a(17) = 21,858,781,309,925,220,643,647 — 09-24 21:30:20

- **run 17**: the top value is
  2,185,878,130,992,522,064,364,700,000,000,000,000,001 (40 digits).
  **stopper** 10^18·k + 1 = 19 ×
  1,150,462,174,206,590,560,191,947,368,421,052,631,579.
- 17 certificates: 2 `deterministic-mr`, 15 BLS75 Theorem 1.
- **model**: from the sibling's floor 7.70e21, median 1.86e22; k / median =
  1.18, E = 0.88 (59th percentile). Against the table stated before the
  run, which chained from medians with no sibling floor, 2.9× its 7.5e21.
- k = 3 · 7² · 17 · 89 · 73664161 · 1334176957.
- swept from ⌈A153431(16)/10⌉ = 7,699,311,781,216,114,338,744 at unit 119,
  filter 17, sieve 2^19; 3.56 hours after a(16), 1.10e18 k/s.
- evidence: `evidence/A305740_a17_21858781309925220643647.json`

#### a(18) = 1,705,184,924,533,540,483,774,741 — 09-29 03:13:06

- **run 18**: the top value is
  1,705,184,924,533,540,483,774,741,000,000,000,000,000,001 (43 digits).
  **stopper** 10^19·k + 1 = 61 ×
  279,538,512,218,613,194,061,432,950,819,672,131,147,541.
- 18 certificates, **all BLS75 Theorem 1**: every value is past the
  deterministic Miller–Rabin bound (the smallest, 10·k + 1, is 1.7e25), and
  each is proved by the one factorization of k, since V − 1 = 2^m·5^m·k.
- **model**: from a(17), median 8.95e23; k / median = 1.90, E = 1.16 (69th
  percentile); 1.99× the 8.6e23 stated before the run.
- k = 7 · 11 · 13 · 17 · 19 · 23 · 29 · 313 · 269189 · 93844193.
- swept from a(17) at unit 2261 (the forced 7 · 17 · 19), filter 18, sieve
  2^18, on the WIDE survivor record; the first 2.33e22 rests on filter 17's
  classified line, carried across the promotion. About 90 hours of campaign
  clock (101.7 of wall clock) at an average of 5.2e18 k/s, across the engine
  changes of Measurements 16 and 17, each of which reproduced every frozen
  fingerprint under an unchanged checkpoint key.
- evidence: `evidence/A305740_a18_1705184924533540483774741.json`

Evidence: `evidence/<entry>_a<n>_<term>.json`, one per term, and one ledger
per family, `evidence/a305740_discoveries.json` and
`evidence/a153431_discoveries.json` (the same records plus a label and a
timestamp).

### The least-claim basis

Each find is a **first occurrence**: every x from the floor to the find was
swept at the forced unit and every survivor classified in x order. Three
things set the floor, and every evidence file names which one it used:

* **Monotonicity.** The conditions nest, so a(n) ≥ a(n − 1)
  (`monotone_floor`).
* **The carried line.** A find at filter n is the floor of filter n + 1, and
  the classified line up to the end of the find's segment carries across the
  promotion: K(q, n) ⊆ K(q, n + 1), so every filter-(n + 1) survivor is a
  filter-n survivor, and each of those was already run to n + 8
  (`covered_by_previous_filter_to`).
* **The sibling's floor** (A305740 only). If k had an A305740 run of n, then
  y = 10k would meet A153431's condition at index n − 1, so
  A305740(n) ≥ ⌈A153431(n − 1)/10⌉ (`sibling_floor`, which names the
  A153431 term it rests on). A305740's a(14) rests on the published
  A153431(13); its a(15), a(16) and a(17) on this project's A153431 a(14),
  a(15) and a(16) — so those three claims are only as good as A153431's,
  which is why they were hunted first.

The proof crossing is low (k = 3.3e7 at n = 17 and 3.3e6 at n = 18), so
almost all of both sweeps classified by a thirteen-base strong probable-prime
chain rather than a proof. The searched-empty claims are sound there for the
reason every ladder project in this repository gives: a composite that
passes the chain can only *lengthen* a run, never hide one, so a true run of
n would have passed every test, been claimed, and then been proved by
certificate — as all nine were.

### The two entries, read together

The README's two relations (gated as `decl_reference` G2d) hold on every
new index and did work in this hunt:

* **Nesting**: A305740(n) ≤ A153431(n), with equality exactly when
  A305740(n) + 1 is prime. At n = 14, 15, 16 the A305740 term is the smaller
  by factors of 134, 519 and 1040; none of the six A305740 finds has k + 1
  prime, so none settled A153431 (`also_settles` is empty on all six).
* **The shift**: A153431(n − 1) ≤ 10·A305740(n). It gave A305740 its floors
  (above), was an **equality** at n = 16 — A153431's a(15) ends in 0 — and
  now bounds the open A153431 term from above:

  **A153431(17) ≤ 10·A305740(18) = 17,051,849,245,335,404,837,747,410**,
  because m = 10·A305740(18) turns A153431's eighteen forms m·10^0 + 1 …
  m·10^17 + 1 into A305740's eighteen, 10^1·A305740(18) + 1 …
  10^18·A305740(18) + 1, all prime. (It is not A153431(18): the next value
  is A305740 a(18)'s composite stopper.) Every multiple of 10 below that bound is
  excluded too, by A305740 a(18)'s own least claim — which is the class-0
  lever in OPTIMIZATION_LOG.md ("Priced and declined" 5).

## The finds against the model

| | A305740 | A153431 | both |
|---|---|---|---|
| terms | 6: a(13)–a(18) | 3: a(14)–a(16) | **9** |
| searched draws | 5 (a(16) is A153431 a(15)'s event) | 3 | 8 |
| mean E | 1.17 | 2.44 | **1.65** |
| x / median, range | 0.84–2.64, geometric mean 1.61 | 4.26–5.89, geometric mean 4.92 | geometric mean **2.45** |
| certificates | 93: 28 `deterministic-mr`, 65 BLS75 thm 1 | 48: 12 `deterministic-mr`, 36 BLS75 thm 1 | 141 |
| campaign clock | 93.64 h | 8.38 h | 102.0 h |

`E` is the number of hits the model expected between the floor the sweep
started at and the term that occurred; if the intensity is right it is
Exp(1), mean 1. Pooled over the eight searched draws it is **1.65**, next
to the 1.63 of G11's validation on the published terms (a disjoint set) —
the model's usual optimism, and the README's caution to budget 1.9–2.5× the
median was about right in the aggregate (2.45×). **The split between the
families is the finding:** A305740's five draws score 1.17, near right, and
A153431's three all landed late — the 88th, 90th and 94th percentiles, 4.3–5.9×
their medians. Three draws summing to E = 7.3 or more has probability
about 2% under the model, so A153431's intensity at n = 14–16 looks about
twice too high; three draws cannot say whether that is the model or the
luck, and G11's A153431 knowns (mean 1.20 over 7) do not show it. Read
A153431's open-term depths as floors by more than the usual margin.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the ledger timestamps and the checkpoints, per filter, no flags:

| family, filter | line swept | wall clock | campaign rate | the engine at that filter ([BENCHMARKS.md](BENCHMARKS.md)) |
|---|---|---|---|---|
| A153431 n = 14 | 5.9e18 | about a minute, pool sizing included | — | seconds, as priced |
| A153431 n = 15 | 7.3e20 | 14.6 min | 8.4e17 m/s | 8.65e17 |
| A153431 n = 16 | 7.6e22 | 8.12 h | 2.61e18 | 2.65e18 |
| A305740 n = 13..16 | 8.7e17 above the floors | 113 s from the first find to the fourth | — | seconds each |
| A305740 n = 17 | 1.42e22 (from the sibling's floor) | 3.56 h | 1.10e18 k/s | 1.19e18 |
| A305740 n = 18 | 1.68e24 | about 90 h of campaign clock | ~5.2e18 average | 5.11e18 at the start of the leg, 5.31e18 after Measurement 16, 5.89e18 (`SCORE`) after Measurement 17 |

Every leg ran at or near its benchmark's rate; A305740's n = 17 leg read
0.93× its figure. The n = 18 leg's average sits between the engine it
started on and the one it finished on.

## The census

Counts per run length from each checkpoint, as printed in every `[STATUS]`
line (the finds themselves are included at their run lengths):

    A305740   8: 645990  9: 194241  10: 57030  11: 16050  12: 4363  13: 1223
              14: 340  15: 68  16: 15  17: 7  18: 1
                                           near 10   survivors 4,676,513,612
    A153431   8: 69336  9: 21684  10: 6521  11: 1939  12: 554  13: 138
              14: 33  15: 12  16: 1
                                           near 19   survivors 799,847,363

A run one short of the open term got a `[NEAR]` line and was verified as a
health check; everything shorter is a count and nothing else. 5.5 billion
survivors were classified across the two campaigns. Each extra rung costs a
factor of about 3.2–3.7 through run 14 on both families. The short lengths
are counts of *sieve survivors*, not densities: a filter-n sieve removes an
x with a short run whenever one of its later forms has a small factor, so
they are comparable within a campaign and not across filters. A305740 swept
22× the line A153431 did.

## What is open now

**PAUSED — open to others.** Nothing is running. Both campaigns stopped
right after a find, so each open term's only coverage is the classified line
carried from the find's segment:

| entry | frontier (this project's) | open next | searched empty below | resumes at | median from the bound | at the current engine | P(found) in a day / a week / 30 days |
|---|---|---|---|---|---|---|---|
| A305740 | **a(18) = 1,705,184,924,533,540,483,774,741** | a(19) | k = 1.7633e24 | filter 19, unit 2261, period 2541 | 4.9e25 | 51 days at ~1.07e19 k/s | 2% / 13% / 36% |
| A153431 | **a(16) = 76,993,117,812,161,143,387,438** | a(17), and **a(17) ≤ 1.7052e25** | m = 7.7996e22 | filter 17, unit 4522, period 798 | 1.5e24 | 1.4 days at ~1.16e19 m/s | 40% / 91% / 99.9% |

(The rates are the wall-clock table's times Measurements 16 and 17's paired
factors at those filters; the probabilities are `decl_model` from the bound,
which for A153431 the section above says to discount.)

**A153431's a(17) is the cheap one.** By the model it is a day and a half of
device at the median and a week at P90; at the late landing its last three
terms showed, a week or two. It cannot take longer than the upper bound
above: 1.7052e25 at 1.16e19 m/s is 17 days, whatever the model says. The
class-0 lever — skipping every m ≡ 0 (mod 10) below that bound, a quarter of
the candidates — now rests on a settled term rather than a running cursor
and is worth 1.33× on that whole leg (OPTIMIZATION_LOG.md "Priced and
declined" 5); it is not built.

**A305740's a(19) is the expensive one**: about seven weeks at the median.
A153431 a(18), once found, would raise its floor to ⌈A153431(18)/10⌉.

**Resuming.** Nothing new is needed to be correct: `python launch.py
--family A153431` and `python launch.py --family A305740` continue from the
cursors above, census and finds intact. **Whoever resumes runs `python
launch.py --selftest` and `python score.py` first** (CLAUDE.md rule 2).
Owed before either is offered again: the nine finds into the oracle's
`FOUND` (so G1b re-derives them from the definition and a fresh clone opens
at the new frontier rather than at a(12) and a(13)); a frozen benchmark
shape at A305740's live filter, n = 19 (rule 5g: `SCORE` is n = 18); and the
model rerun on the new frontier — `model_results.json` is the table stated
before the run and stays as the record.

Where each campaign stands is read with `python launch.py --status --family
A305740` and `python launch.py --status --family A153431`, which touch
nothing.
