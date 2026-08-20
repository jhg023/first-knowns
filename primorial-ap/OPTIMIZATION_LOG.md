# OPTIMIZATION LOG — primorial-ap

> **Authorship disclaimer:** None of this was written by me; it was
> authored by **Claude (Anthropic's AI)** at my direction.

Every attempt: the change, the measurement, kept or rejected. Failures
included — they are the record that stops the next person retrying them.
The process this follows is [OPTIMIZATION.md](../OPTIMIZATION.md); read it
before adding to this file.

**State of the engine: v2.** v1 was built to be correct and gated, then
measured (#1–#3); #4–#7 are the optimization pass that followed, ~20× of
device rate at the campaign depth with the stream pinned bit-for-bit
throughout. The campaign configuration below #3 (depth 2048, two workers)
was chosen against v1's rates and is STALE against v2 — the re-balance is
the open item at the bottom of this file.

---

## #1 — The phase split, measured before anything was touched

**Rule 1 of OPTIMIZATION.md, and it paid immediately.** One launch of
2²⁵ wheel periods (1.0×10⁹ of p-line) at n = 16, depth 4096, timed phase by
phase with a device sync between each:

| phase | time |
|-------|------|
| bitmap clear | 0.0 ms |
| host residue setup (`base % q` for every sieve prime) | 0.0 ms |
| **mark kernel** | **137.3 ms** |
| compact kernel | 0.0 ms |
| gather + sort survivors to the host | 0.0 ms |

**The marking kernel is the entire engine.** Everything else rounds to
zero, including everything on the host side of a launch. Any optimization
that is not about marking bits is not about this engine.

Second measurement, one segment (16 launches) with classification:

| | depth 2048 | share |
|---|-----------|-------|
| sieve | 1.90 s | 76% |
| classify (72k survivors, 2 workers) | 0.61 s | 24% |

**Kept as the standing direction:** work on the mark kernel, and on
overlapping the 24%.

---

## #2 — The first depth sweep was wrong, and the reason is a clock regime

**Rejected — the numbers, not the conclusion.** The first sieve-depth sweep
was run on a card that had been idle, and reported 2.44×10¹⁰ p/s at depth
2048. A re-measurement after a 12-second soak, on the same window with the
same code, reported **8.46×10⁹** — the first numbers were inflated **2.9×**
by boost clocks the card cannot hold. The card in its sustained state sits
at 2775 MHz, 52 °C and 211 W of a 450 W limit.

This is exactly the failure OPTIMIZATION.md Rule 3 exists for, and it is
worth noting that *interleaving saved the conclusion*: because the sweep
alternated depths rather than running them in sequence, the RATIOS between
depths were right even while every absolute number was wrong, so the
configuration chosen from it survived the correction unchanged. The
absolute rates in [BENCHMARKS.md](BENCHMARKS.md) are the sustained ones.

**Kept as a rule for this project:** soak before measuring, and never
compare a number taken on a cold card with one taken on a warm one.

---

## #3 — Campaign configuration: sieve depth and the load budget

**Kept: depth 2048, two workers.** Measured at the production shape
(n = 16, p ≈ 4×10¹³), interleaved, four rounds, median, sustained card,
with the host priced at the measured 17 µs per survivor:

| sieve depth | device p/s | survivors / unit | host cores | verdict |
|-------------|-----------|------------------|-----------|---------|
| 1024 | 9.67×10⁹ | 1.99×10⁻⁵ | 3.28 | **declined** — see below |
| **2048** | **8.46×10⁹** | 4.47×10⁻⁶ | **0.64** | **chosen** |
| 4096 | 7.19×10⁹ | 1.11×10⁻⁶ | 0.14 | slower |
| 8192 | 6.65×10⁹ | 3.05×10⁻⁷ | 0.03 | slower |
| 16384 | 5.95×10⁹ | 9.14×10⁻⁸ | 0.01 | slower |
| 65536 | 5.38×10⁹ | 1.09×10⁻⁸ | 0.00 | slower |

The shape of the problem is in the first two columns: **the hunt is
device-bound at every depth worth running.** Survivors are so rare that
classifying them is a rounding error next to sieving for them, so depth is
a straight trade of marking work against host processes and the shallow end
wins. This is the opposite of the sibling project in this repo, where
deeper sieving bought speed by taking work off a saturated host — and it is
why CONVENTIONS.md rule 5c says to measure the configuration the campaign
will actually run rather than inheriting one.

**Priced and declined: depth 1024.** 14% faster, and it asks for 3.28 host
cores against 0.64 — five times the machine for a seventh of the rate, on a
program that runs for days on a desktop somebody else also uses
(CONVENTIONS.md, "Sizing a hunt so it leaves the machine usable", step 3).
It is one flag away: `--sieve-depth 1024 --workers 8`.

**Worker count** is sized from the requirement, not from the core count:
0.64 cores of demand, so 2 workers is 3.1× the need at ~32% duty. On this
host `cpu_count - 2` would have asked for sixty processes to do the work of
one.

---

## #4 — The shared-memory sub-segment mark kernel (was candidate #5)

**Kept: 3.65× at the campaign depth, 2.07× at the frozen depth,
fingerprints identical.** The v1 kernel put ~2.8×10⁹ global `atomicOr`s
per 2²⁵-period launch through L2 and was contention-bound (211 W of
450 W). v2: each block owns SUB_U wheel periods as a sub-bitmap in shared
memory, marks into it with shared atomics, and stores its
exclusively-owned word range out plain; primes too sparse to amortize the
per-block start solve stay on the old global kernel, launched after.
Interleaved A/B, soaked, per OPTIMIZATION.md Rule 3; the v1 path was kept
runnable throughout (forcing the split to 0 reproduces it exactly) and is
what "OLD" means in every ratio here.

The constants moved exactly as Rule 1's corollary says they would:
1024 threads × 64 KiB sub-segments (SUB_U 2¹⁶, dynamic shared memory)
beat the first working point (256 × 32 KiB) by another **1.33×**, and the
shared/global split landed at SUB_U/2 — the sweep was monotone toward
"put every prime you can on the shared path."

**Measured after landing: the kernel sat at a named roofline** — 2.8×10⁹
marks in 9.4 ms ≈ 0.93 shared atomics per clock per SM, the LSU issue
limit. Anything further had to REMOVE atomics, not speed them up. That is
#6.

## #5 — Three host-side leaks the phase split exposed

**Kept, all three; together ~1.4× end-to-end at the campaign depth.**
The re-measured split (Rule 1, again) showed the launch was 70% mark
kernel and **29% "gather survivors"** — which turned out to be a DEVICE
sort of a few thousand values: ~3.8 ms of pure launch overhead per
launch, independent of size. Sorting on the host (`np.sort` of the copied
array) costs 0.1 ms. Second: the per-launch `base % q` Python loop
(0.9 ms at the frozen depth) became a vectorized numpy reduction of
base = hi·2⁶⁴ + lo against a precomputed 2⁶⁴ mod q. Third: the start
solve's `(bq + R[l]) % q` hardware modulo moved to the host as a
per-(prime, lane) table computed in the same reduction.

## #6 — Pattern tables: invert the loop (OPTIMIZATION.md 2.1)

**Kept: 4.95× on the mark kernel at the campaign depth; 1.35× at the
frozen depth. The big one.** For an odd prime q the kills land in 32-bit
bitmap words with period q words, so a q-word table of masks holds every
kill the prime will ever make in any word. The mark kernel gives each
thread @K@ words to OWN in register accumulators; per tabulated prime it
is one coalesced load and one OR per word — no atomic, no shared-memory
traffic, and the final stores double as the sub-bitmap's zero-fill.
Tables are rebuilt on the device every launch (the pattern depends on
base mod q); the build is ~150k atomics against a ~1 MB table and does
not register in the launch time.

The sweep of the cutoff was monotone at the campaign depth — tabulating
EVERYTHING (q ≤ 2048) won at **4.95×** over no tables — and peaked at the
same 2048 at the frozen depth (1.35×, with q > 2048 still on the atomic
paths there). So one default serves both: TAB_MAX_Q = 2048. Above it a
table row is mostly zeros and a load per word loses to marking the rare
bits directly; the crossover is where ~4·w/q bits per q words thins out.

At the campaign depth the whole sieve is now the gather: device rate
measured **2.4–5.8×10¹¹ p/s** across ambient regimes, against v1's
0.7–2.4×10¹⁰ — the honest cross-regime statement is **20–25× device**,
and the SCORE (one number, one shape, gates green) went 5,163 → 39,772.

## #7 — Launch size, re-swept after the structure changed

**Kept: LAUNCH_U 2²⁵ → 2²⁷, worth 1.105× at the campaign depth.** With
the kernel 5× faster the fixed per-launch host work (residue tables,
survivor copy, count sync) had become ~20% of a 2 ms launch. A fixed
2²⁸-period span swept as launches of 2²⁵…2²⁸ plateaus at 2²⁷ (128 MiB
bitmap — the sub-bitmaps live in shared memory now, so L2 residency of
the global bitmap stopped mattering). 2²⁸ measured identical; 2²⁷ takes
half the memory.

## The candidate list — measured, priced, not yet attempted

Ordered by expected value. The numbers are estimates and are not evidence
(OPTIMIZATION.md: never treat the cost model as evidence).

**#8 — Overlap classification with the next segment's sieve.** In v1 this
was worth ~1.3× (8.46×10⁹ device against 5.97×10⁹ end-to-end, the gap
being the classify phase running *after* the sieve instead of beside it).
With the device ~20× faster the classify share is ~20× larger and this
stops being an optimization and becomes THE campaign bottleneck — see the
re-balance measurements below when they land. The care it needs is in the
checkpoint boundary: the cursor may only advance past a **fully
classified** segment, or the least-claim stops meaning what it says.

**#9 — Batched classification.** 17 µs per survivor is Python overhead,
not arithmetic: the values are 70-bit and one strong test on them is a
couple of microseconds. In v1 this was worth nothing (the hunt was
device-bound); at the v2 device rate the classify demand at depth 2048 is
several host cores, so this and the sieve depth together now set the
end-to-end rate and the machine budget.

**#10 — A wider wheel.** The mod-30 wheel represents 8 of every 30
integers. Mod 210 would be 48 of 210 — 14% fewer bits to mark — but
multiplies the per-(prime, residue) lane setup and the table build by
six. Probably a wash; measure only if the mark kernel is ever the
bottleneck again.

**Skip the sort — moot.** v1 considered removing the survivor sort and
declined at 0.0 ms; #5 then found the DEVICE sort was 29% of a v2 launch
and moved it to the host, which is where this item ends.
