# BENCHMARKS — square-ladders

The number this project is judged on is `SCORE`, printed by `score.py` and
only if every correctness gate is green **and** all four frozen shapes
reproduce their work fingerprints exactly. An engine that skips work fails
the fingerprint and scores 0; an engine that breaks the mathematics fails
the gates and scores 0.

The rate is **end-to-end k-line per second** — `blocks × W / wall` — which
is what the hunt is actually paid in, divided by 1e6.

## The frozen shapes

Four, because one configuration is not a benchmark. Every `k0` is an exact
multiple of that shape's wheel modulus; it has to be, since each engine
floors `k // W` with its own `W`, so a shared cursor is a different
absolute window per wheel.

| shape | filter | wheel | sieve | window | fingerprint |
|-------|--------|-------|-------|--------|-------------|
| `SCORE` | n = 16 | factored (23, 37], W = 7,420,738,134,810 | 65536 | `[9.9438e14, +2.9683e13)` | 303 / 999990048677220 |
| `SCORE1L` | n = 16 | one-level ≤ 23, W = 223,092,870 | 65536 | the **same** window | 303 / 999990048677220 |
| `SCORE10` | n = 10 | one-level ≤ 13, W = 30,030 | 4096 | `[2.0e9, +6.006e9)` | 2931 / 2555483804 |
| `SCORE16W` | n = 16 | one-level ≤ 17, W = 510,510 | 1024 | `[1.0e15, +3.0631e10)` | 581 / 999980563688462 |

`SCORE` and `SCORE1L` cover the **same stretch of line with the same sieve
depth**, so they must return the identical fingerprint — and they do. The
two kernels enumerate the same candidates by different arithmetic (a stored
residue table versus a per-candidate CRT recombination), so a bug in the
factored wheel's baked constants is caught inside the benchmark itself
rather than by a gate somewhere else.

`SCORE10` disagrees with `SCORE` about what matters: a 250× narrower wheel
and a shallow sieve mean far more survivors per unit of line, so it weighs
candidate throughput where `SCORE` weighs line throughput. A change that
helps one and hurts the other is visible instead of averaged away.

## The ledger

| date | engine | SCORE (Mk/s) | SCORE1L | SCORE10 | SCORE16W | note |
|------|--------|--------------|---------|---------|----------|------|
| 2026-08-21 | v1, one-level wheel ≤ 23 | 10,768,681 | — | 830,430 | 4,050,809 | first green battery; `SCORE` was then the one-level shape |
| 2026-08-21 | **v2, factored wheel (23, 37]** | **28,576,161 – 42,988,406** | 7,265,536 – 11,195,714 | 638,515 – 643,702 | 2,450,722 – 2,526,485 | **3.9×** against `SCORE1L` in the same run |
| 2026-08-21 | **v3, cheap tests + block compaction** | **129,397,475** | 25,231,327 | 1,671,119 | 8,223,863 | **4.014×** against v2 interleaved in one run |
| 2026-08-21 | **v3.1, second compaction round** | **136,117,250** | 26,623,079 | 2,417,096 | 8,502,831 | **4.721×** against v2, **1.209×** against v3 |
| 2026-08-21 | **v3.2, CRT-combined prefix** | **162,963,133** | 36,251,384 | 3,123,895 | 17,523,227 | **5.735×** against v2, **1.19×** against v3.1 |
| 2026-08-21 | **v3.3, combined round 2 + derived depths** | **184,801,999** | 36,289,650 | *see below* | *see below* | **6.481×** against v2, **1.13×** against v3.2 |

The v3 rows' claim is the ratio, not the number. v2's kernel was compiled
verbatim from the source it had at commit time and run back to back with
the live engine on the `SCORE` window, seven rounds each, the frozen
fingerprint `303/999990048677220` checked on every run of both: v2
1029.5 ms / v3 256.5 ms, **4.014×**, per-round 3.893–4.079; then v2
1030.4 ms / v3.1 218.3 ms, **4.721×**, per-round 4.580–4.790; then
v2 1038.1 ms / v3.2 181.0 ms, **5.735×**, per-round 5.691–5.792
with one 4.949 outlier; then v2 1020.6 ms / v3.3 157.5 ms, **6.481×**,
per-round 6.170–6.583.

**`SCORE10` and `SCORE16W` stopped resolving at v3.3**, and their cells
are left blank rather than filled with a number that does not mean
anything. Their frozen windows are 6.0×10⁹ and 3.1×10¹⁰ of k line, which at
the v3.3 rate is under 2.5 milliseconds each — per-launch overhead and a
host round-trip, not kernel time. Over five runs of one binary they spread
**26%** and **13%**, against 1.1% for `SCORE` and 0.6% for `SCORE1L`.
See OPTIMIZATION_LOG.md, “The benchmark shape has become the blocker”:
the windows are NOT re-cut here, because the anchor that makes scores
comparable across engine generations is not an optimization pass's to
change, and both shapes still do their more important job — their
fingerprints have been exact through every change.

`SCORE16W` was the row to look at for v3.2, while it still resolved: it
rose **2.3×**, far more than the others, because it runs a coarse wheel and
a shallow sieve, so a larger share of its work is the prefix that change
makes cheap. That is the four-shape benchmark doing its job — a change that
helps one shape far more than another is visible instead of averaged away.

On the v3 row: the same session measured v2 at `SCORE` 31,634,366, which is
inside the v2 range above and near its top — so the 4.5× one would get by
dividing the two ledger rows is the ambient swing flattering the
comparison, and 4.014× is the honest figure. All four shapes rose and none
fell there: `SCORE` ×4.09, `SCORE1L` ×3.14, `SCORE10` ×2.61, `SCORE16W`
×3.03, measured against that session's own v2 baseline run. `SCORE10` and
`SCORE16W` moved where they had not under v2, and should have: v3 changes
the test loop and the compaction, which every shape uses, rather than the
wheel, which only two of them do.

**The absolute number moves with the machine; the ratio does not.** Three
runs of the identical v2 binary produced `SCORE` 42,988,406 once and
28,614,468 / 28,576,161 on the two reproducible repeats — a 1.5× spread
with no code change between them, the card sitting at 2535 MHz of a 3120
MHz maximum on the later pair. That is the ~30% ambient swing
OPTIMIZATION.md rule 3 exists to warn about, and it is why this ledger
quotes a range rather than a headline.

It happened again on v3.2, and harder. One `score.py` run read **280,149,693**
against a reproducible cluster of **162,277,567 / 162,762,345 /
163,021,130** on the three runs immediately after it — same binary, same
argument, nothing changed between them, all gates green and all four
fingerprints exact in every case. That is a **1.72×** spread on a correct
run, wider than the 1.5× v2 saw. The ledger records the reproducible
figure, not the lucky one, and the outlier is written down here because a
benchmark that only ever reports its best sample is not a benchmark.

What does *not* move is `SCORE / SCORE1L`, measured inside a single run on
the same window: **3.84× and 3.94×** across those three runs, against
3.95× from the interleaved A/B. That is the honest statement of what the
factored wheel bought. Any future comparison should be made the same way —
two shapes in one run — and never between a number in this table and a
number measured on another day.

`SCORE10` and `SCORE16W` did not rise with v2, and should not have: both
are pinned to one-level wheels the change does not touch. Their job is to
stay comparable.

## Rates that are not the score

Measured on the campaign's own shape at campaign height, which is the
number the hunt is priced on (CLAUDE.md rule 5c). All rate probes call the
engine API directly on a chosen window; none of them is the campaign.

| wheel | W | candidates per unit line | k/s | candidates/s |
|-------|---|--------------------------|-----|--------------|
| ≤ 13 | 30,030 | 3.356e-2 | 1.09e12 | 3.66e10 |
| ≤ 17 | 510,510 | 1.776e-2 | 2.60e12 | 4.63e10 |
| ≤ 19 | 9,699,690 | 9.353e-3 | 5.91e12 | 5.52e10 |
| ≤ 23 | 223,092,870 | 4.880e-3 | 1.11e13 | 5.40e10 |
| **(23, 31]** | 200,560,490,130 | 1.303e-3 | **1.91e13** | 2.49e10 |
| **(23, 37]** | 7,420,738,134,810 | 7.394e-4 | **2.93e13** | 2.16e10 |

Read across: candidates per second *falls* as the wheel widens, because the
candidates a wider wheel removes are exactly the ones that used to die at
the first Barrett test. The k-line rate is what rises, and it is what the
hunt is paid in.

Sieve depth is nearly free, which is the early exit doing its job:

| sieve depth q2 | k/s (wheel ≤ 23) | survivors per unit line |
|----------------|------------------|--------------------------|
| 4096 | 1.110e13 | 1.052e-9 |
| 16384 | 1.128e13 | ~1.0e-10 |
| 65536 | 1.111e13 | 1.083e-11 |
| 262144 | 1.120e13 | ~1.4e-12 |

A 64× deeper sieve costs under 2% and buys three orders of magnitude fewer
survivors for the host. The campaign runs 65536 because the host side is
then unmeasurably small; there is no reason to go shallower.

## What the campaign costs at this rate

At the v3.3 production rate of **1.85×10¹⁴ k/s** (`score.py` 1.848, the
interleaved A/B 1.885) — against the odds model's quantiles:

| target | Q1 | median | Q3 | P90 |
|--------|----|--------|----|-----|
| a(16) | 2.9 s | **12 s** | 37 s | 1.4 min |
| a(17) | 1.1 min | **5.3 min** | 17 min | 40 min |
| a(18) | 40 min | **3.0 h** | 9.5 h | *past the ceiling* |

The engine's whole enforced range — everything below `K_CEIL = 9×10¹⁸` — is
**13.5 hours** of sweeping, down from 3.6 days under v2. That is the useful
way to state the budget here: this is not a hunt that needs a stopping
rule, it is a hunt that can be run to its own ceiling **overnight**, at
which point `a(16)`, `a(17)` and `a(18)` are either found or bounded below
`9×10¹⁸`.

That last sentence is also the reason the `(23, 43]` wheel is not
obviously worth having any more, even though it models at 2.10×: see
`OPTIMIZATION_LOG.md`, "Open after v3", item 2. A wheel that wide makes one
block 1.3×10¹⁶ of line, and since coverage is contiguous in `k` only at
block boundaries, the whole of `a(16)` — modelled median 2.18×10¹⁵ — would
sit inside the first block and cost 6× more line to *prove* than to find.

`a(18)`'s P90 (1.46×10¹⁹) and all of `a(19)` sit above the ceiling. Raising
it is a new engine version with new gates and a new fingerprint
(CONVENTIONS.md "Numeric hygiene"); the arithmetic has room — values stay
deterministic to `k = 1.3×10²²` — but nothing about that is free and it is
not done.

## Load

There is no host worker pool, by construction. A segment is twelve wheel
blocks (8.90×10¹³ of line, ~0.55 s of device time) and yields about 960
survivors, each costing a handful of 64-bit Miller-Rabin tests —
milliseconds of host work per second of device work. Nothing to ramp, no
core count to size. Segment size is chosen for crash cost, not throughput,
and it was **re-swept on v3**: the rate is flat from 1 to 16 blocks per
segment (1.158–1.163×10¹⁴ k/s, 0.4% across a 16× range), with the split
sweep's fingerprint identical at every setting.

It went from 2 blocks to 8 and then to 12, and the reason is the interesting part. What
was actually chosen in v2 was a **segment duration** of about half a
second — that is what an interrupt costs to redo, and it is also the
denominator that prices `--gpu-yield-ms`. v3 made a block 4× faster, so
leaving the constant at 2 would have quietly cut the segment to 0.13 s and
turned a 20 ms yield from 4% of the rate into **16%**, and `--gentle`'s
40 ms into **31%** — a documented price becoming false with no code change
near it, and no benchmark able to see it (OPTIMIZATION.md rule 7). At 8
12 blocks the segment is 0.48 s at the v3.3 rate, an interrupt costs about
half a second,
the checkpoint fsync is under 1% overhead, and the throttles cost what
their help text says: `--gpu-yield-ms 20` is about 3.7% of the rate and
`--gentle` (40 ms) about 7.3%. The constant has now moved twice for the
same reason — it is pinned to a DURATION, so every engine speedup has to
raise the block count to keep it — and that is the constant working as
intended rather than churning. The engine holds 0.03 GiB of VRAM (34.6 MB: an 8.7 MB
first-level residue table, a 25.3 MB forbidden-residue bitmap, and 0.6 MB
of everything else).
