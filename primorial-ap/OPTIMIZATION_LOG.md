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

## #8 — The overlap: the pool classifies one segment behind the device

**Kept: end-to-end 1.84×10¹¹ → measured through the real launcher, and
2.07×10¹¹ once the segment grew to match (below) — 96% of the device
rate, against 71% for v1's serialized sieve-then-classify.** The device
now runs one segment ahead of the classified cursor: while the main
thread blocks in segment i's device sync, the worker processes classify
segment i−1. The checkpoint discipline is the point, not a detail: the
cursor advances ONLY in `_finalize`, past a fully classified segment, so
an interrupt loses in-flight device work and never classified coverage —
and a discovery drops the in-flight segment, which was sieved for a term
that no longer needs hunting.

Same measurement, second knob: at the v2 rate a checkpoint segment of 16
launches lasted 0.3 s, so the fsync'd save had become per-segment glue.
SEG_LAUNCHES 16 → 64 (a ~1.3 s segment, still a trivial crash cost) was
**+12% end-to-end**. Measured on bounded production runs (`--to`), which
also rediscovered the canary and verified a live depth-15 NEAR in
passing.

## #9 — Classification measured, and the re-balance it forces

**The 17 µs per survivor is NOT Python overhead.** Measured on 4,368
real survivors at the production shape: 16.7 µs per `chain_depth`, of
which a single `pow(2, p−1, p)` on the 70-bit value is 6–7 µs and the
mean survivor takes 1.7 chain tests. The v1 candidate list guessed
"vectorize away 5×" — wrong premise, recorded here so nobody rebuilds
it: the cost is bignum modular exponentiation in CPython, and no
batching removes it.

That number and the v2 device curve force the campaign configuration to
move (the depth table lives in `launch.py`): **depth 2048, the device's
favorite, now demands ~39 host cores of classification.** The kept
configuration is depth 8192 × 3 workers — 89% of depth-4096's device
rate for a quarter of its host, 1.1 measured cores of demand, and the
overlap (#8) hides all of it. Priced and declined:

- **depth 4096 + 8 workers: ~+14% end-to-end for 4× the host.** One flag
  away; the load budget says no as a default.
- **gmpy2's powmod (~2–4× on the classify): declined** — a new
  dependency is the owner's call, and at the kept depth it buys nothing
  (the classify is already hidden).
- **a device base-2 sprp prefilter on p: declined on the measured
  arithmetic.** It first looked like a 3× host cut (it removes the ~53%
  of survivors whose p is composite). It is not, and the reason is the
  classify cost's own shape: a p-composite survivor costs ONE 7 µs test,
  while a p-passing survivor averages 1.7 more tests on values that are
  ~65 bits — past u64, so the device cannot touch them at n = 16. The
  filter therefore removes only 23% of host work (16.7 → 12.9 µs per
  sieve survivor), leaving depth 4096 at ~3.5 cores — still 4× the
  budget for the same +14%. A new gated primality kernel for a 23% host
  cut that the overlap already hides was not worth its correctness
  surface.

## The termination table (OPTIMIZATION.md Part 3), campaign configuration

Depth 8192, LAUNCH_U 2²⁷, one launch ≈ 19–20 ms device:

| phase | share | verdict |
|-------|-------|---------|
| gather (tabulated q ≤ 2048) | ~55% of mark | ~1.0×10¹⁰ coalesced table loads per launch at ~2.6/clk/SM — within ~2× of L1 transaction throughput. The cutoff is bracketed from both sides: TAB 4096 measured 0.71–0.95× at every depth tried (a q > 2048 table row is mostly zeros, so the load is wasted) |
| shared atomics (2048 < q ≤ 8192) | ~45% of mark | **at the shared-atomic LSU roofline**: 3.1×10¹¹ marks/s ≈ 0.96/clk/SM. The only lever is fewer atomics, i.e. more tables — measured slower (row above) |
| compact | 0.4% | below the 5% bar |
| host glue (residue tables, D2H, sort, checkpoint) | ~4% end-to-end | measured as the gap between 2.07×10¹¹ end-to-end and 2.15×10¹¹ device |

Remaining candidates, priced: **a wider wheel (mod 210)** — 14% fewer
bits against a 6× larger lane setup and table build, argued a wash and
never measured, so it is a hypothesis, not a verdict; SEG_LAUNCHES past
64 (~2%, against checkpoint granularity); the sprp prefilter, declined
on measured arithmetic (#9). The closing re-sweep (Rule 3.4/3.5) of
TARGET_MARKS_SH at the final design measured 1.000 over 11 interleaved
rounds and THREADS 512 at 0.81, so the constants are fresh and the last
round found nothing — which is the state OPTIMIZATION.md Part 3 requires
before stopping, and the state this file hands to the next pass.

**Skip the sort — moot.** v1 considered removing the survivor sort and
declined at 0.0 ms; #5 then found the DEVICE sort was 29% of a v2 launch
and moved it to the host, which is where this item ends.
