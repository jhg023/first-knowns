# Results — prime-power-sums

> **Authorship disclaimer:** None of the code or analysis in this project
> was written by me; all of it was authored by **Claude (Anthropic's AI)**
> at my direction.

## Verified finds

**None.** No production sweep has been run. The four implementations,
the odds model and the full gate battery are built and green, and after
the v2 optimization pass the campaign is **startable** — the nearest
target is about eleven days of wall clock rather than 8.7 years. Starting
it is the owner's call; the pipeline does not start itself. See
[BENCHMARKS.md](BENCHMARKS.md) for what each target costs and
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) for how the rate was got.

This section will carry, per find, in discovery order: the exact integers
(the index *k* and prime(*k*)), the sequences it extends, the
verification legs that passed, the quotient witness, the evidence file
path, and the model quantile the find landed at.

## Census

The census is **counted, not narrated** (CONVENTIONS.md). During a run the
per-family counts appear in the 30-second `[STATUS]` heartbeat as
`census 1:… 7:… 9:… 11:… 12:… 13:… 17:… 19:…`, keyed by the power *m*, and
they are persisted in the checkpoint. There are no per-value census files
and there never will be: the evidence directory holds first occurrences
only.

Two classes below discovery are defined for this project:

- **NEAR** — a new value of the census family
  ([A233264](https://oeis.org/A233264) / [A233265](https://oeis.org/A233265),
  *m* = 12, *e* = 1) beyond its published frontier. Real, but that pair
  runs to thousands of terms because the *e* = 1 obstruction inverts into
  a free congruence; extending it is data entry, not discovery. One log
  line with its campaign ordinal, engine-verified only, never evidenced.
- **CENSUS** — a census-family hit below that frontier, or a rediscovery
  of a published term. Counted in `[STATUS]`; a rediscovery also gets one
  `[CANARY-GOLD]` line, because a stream that cannot find what is known
  may not report what is unknown.

The census family is carried on purpose: it produces hits in every
segment, so a stream that has gone wrong announces itself in seconds
rather than in weeks.

## Standing corrections

One published value is flagged and **not** corrected by this project —
OEIS edits are the owner's call, never the pipeline's.

**A233555(18) = 1701962315686097.** The prime-reported table of a family
must satisfy a_val(*n*) = prime(a_idx(*n*)). Across all seven families the
ratio a_val(*n*) / [*k*(ln *k* + ln ln *k*)] runs smoothly from 0.89 to
0.98; at this one position it reads 1.430, between neighbours of 0.972 and
0.975. Against A131277(18) = 34390023299149 the expected value is
≈1.157×10¹⁵, not 1.702×10¹⁵ — and 1701962315686097 is exactly
prime(5×10¹³), which is the family's own published `a(19) > 5*10^13`
search limit, carried in A233555's comments as
`a(19) > 1701962315686097` and submitted the same day (Bruce Garner,
7 Jan 2022) as its a(18).

The reading is that a search limit was entered where a term belongs. The
project pins it with oracle gate G1c, which **fails if a future export
changes it**, so a silent correction is noticed rather than absorbed. The
*m* = 17 sweep passes *k* = 3.44×10¹³ within its first hours and will
produce the correct value as a by-product; at that point the owner has a
verified number and can decide what to do with it.

## In progress

Nothing is running. The state the next session inherits:

- Six files, four documents, fifteen gates plus five drills, **all green**
  (`python launch.py --selftest`).
- **SCORE 58,754** (Mp/s of prime line on the frozen from-scratch window,
  fingerprint 147/5908722711111303797 — the same fingerprint v1 produced,
  held bit-for-bit through the whole optimization pass).
- Campaign-height rate: **3.3×10¹⁰ p/s at p = 3×10¹⁶**, against v1's
  3.3×10⁷ there. The nearest target (m = 11 Q1, prime line 3.3×10¹⁶) is
  about **11 days**; new ground on five of the seven families begins after
  about **six**.
- The instruction-count ceiling for this algorithm on this device is about
  3,000× the v1 score, and v2 is at 618× of it — the arithmetic is in
  BENCHMARKS.md so the next pass knows what is left before it starts.
- No checkpoint, no evidence files, no campaign clock.
