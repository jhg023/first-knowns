# Optimization log — prime-power-sums

> **Authorship disclaimer:** None of this work was done by me; all of it
> was authored and measured by **Claude (Anthropic's AI)** at my
> direction.

Every attempt: change, measurement, kept or rejected. Failures included —
they are the record that stops the next person retrying them. The process
rules are in [OPTIMIZATION.md](../OPTIMIZATION.md); the two that bind
hardest here are *measure the phase split before touching code* and
*never treat the cost model as evidence*.

## v1, 2026-08-21 — first light, and the gap it revealed

The engine was built for correctness first: three kernels, an
unnormalized limb prefix, a Montgomery divisibility test. It is green on
twelve gates and five drills and scores **95 Mp/s**.

Then it was measured at production height, which is the measurement that
matters (CLAUDE.md rule 5c), and the answer is uncomfortable:

| | rate |
|---|---|
| end-to-end at p = 10¹² | 1.20×10⁸ p/s |
| end-to-end at p = 10¹⁶ | 3.25×10⁷ p/s |
| sieve kernel alone | 3.3×10⁸ p/s |
| **needed for the nearest target (m = 11 Q1)** | ~1.2×10¹¹ p/s for a ~3-day run |

**About three orders of magnitude short.** The campaign is not startable
and the project's status says so. This entry exists so the next pass
starts from a number rather than from an intuition.

### Not trusted: the first phase-split harness

A micro-harness timing each kernel separately returned several
sub-resolution readings (0.0 ms for `pow_limbs` at m = 1 and for
`test_hits`) and is **rejected as a measurement**. The end-to-end and
sieve-only figures above are trustworthy because they are wall-clock over
hundreds of milliseconds.

## v2, 2026-08-21 — the optimization pass

**SCORE 95 → 58,754 Mp/s (618×)**, fingerprint 147/5908722711111303797
held bit-for-bit throughout. Production height 3.25×10⁷ → 3.50×10¹⁰ line/s
at p = 10¹⁶ (**1,077×**). Full battery green.

### The phase split, first, and it inverted the plan

v1's log named "never materialize the prefix" as the largest suspect, and
that was right, but for the wrong reason. Once the fused design existed,
CUDA-timed variants of the *same kernel* — compiled with each stage
removed and a keep-alive on the accumulator so nothing is dead-code
eliminated — say:

| stage | share of the sweep |
|---|---|
| **powering** (p^m for eight families, both walks) | **~50%** |
| the divisibility test | ~23% |
| the warp scan and the look-back | ~25% |

The test was the thing v1's architecture was built around — Montgomery
reduction, the odd-only coverage, the 48-limb width — and it is the
*smallest* term. The powering is the bill.

### What paid, in the order it paid

**1. Limb widths sized to the height, at codegen time — the single
biggest kernel change.** v1 walked 48 limbs for every family at every
height because `LIMBS` was a constant. v2 generates its source per run:
family (m, e) gets exactly `ceil((m·log2 p_hi + log2 k_hi)/32)` words, p^j
gets exactly `ceil(j·log2 p_hi/32)`, and every loop bound is a
compile-time constant the compiler unrolls into registers. At the score
window that is 83 words instead of 8 × 48 = 384.

**2. The power chain chosen by SHARED cost, enumerated exactly.** Eight
families share one addition chain. A per-exponent DP that prices p^m as
`cost(a) + cost(b) + mul(a,b)` double-counts everything a and b already
share, and here it chose to build a p¹⁸ nothing else wanted (65 word
multiplies) instead of p¹⁹ = p¹⁷·p² (28). The intermediates live in a
small set, so the *exponent set* is enumerated exactly — 2¹¹ subsets, a
tenth of a second in Python, cached. **195 → 137** word multiplies at the
score window; 881 → 543 at p = 3.3×10¹⁶.

**3. A Montgomery Horner that needs neither a division nor R².** v1 did,
per candidate, 48 sixty-four-bit `%` operations plus a 128-iteration
doubling loop to build 2¹²⁸ mod k. v2 runs the sum bottom-up,
`A_j = w_j + A_{j-1}·2⁻⁶⁴ (mod k)`, one REDC per limb, and never converts
back: k is odd (ODD_ONLY, which the obstruction gives for free), so
X·2⁻⁶⁴ᴸ ≡ 0 exactly when X ≡ 0. The accumulator is deliberately left
**unreduced between limbs** — `hi` carries weight 1 in that recurrence, so
folding it by k when it would overflow costs two instructions and changes
no residue. That is what removes the last division. Two multiplies per
limb; the per-candidate setup is one Newton inverse.

**4. A decoupled look-back for the prefix.** A warp owns a tile of
32 × RUN consecutive primes, scans it internally with carry-propagating
shuffles, publishes its aggregate, and sums predecessors 32 at a time
until it meets a published inclusive prefix. A segment is three launches
and the running state never leaves the device.

**5. The sieve's small/large prime split — 2.9 ms of a 4.0 ms window.**
One thread per prime is the obvious shape and it is catastrophic: the
thread that draws q = 3 marks a third of the sub-segment by itself while
its 255 neighbours mark sixteen positions each and wait. Splitting primes
by how much work they carry — the block walks a small prime in disjoint
contiguous chunks, a large prime gets a thread — took marking from
**0.347 to 0.154 ms**. Sending *every* prime down the cooperative path is
far worse (9 ms): it pays a 64-bit division and a block-wide pass per
prime. The optimum is about four multiples per thread, and it was found by
sweeping, not by reasoning.

**6. Primes bigger than a sub-segment get their own pass.** They cannot
hit one twice, so the per-block loop over them is pure overhead: at
p = 10¹⁵ that was 512 blocks × 1.95×10⁶ base primes of 64-bit division,
**20 ms of a 24 ms segment**. Each now gets a thread and walks the whole
segment into the global bitmap; consecutive base primes do near-identical
work, so a grid-stride loop over a sorted list is balanced for free.
Sieve at p = 10¹⁵: **20 ms → 1.1 ms**.

**7. `np.searchsorted` against a uint32 array with a PYTHON int.** numpy
upcasts the whole array to int64 first. At p = 10¹⁶ that is 5.8×10⁶ base
primes copied twice per segment: **17.6 ms of a 20 ms segment** — more
than every kernel in the engine put together, in a line that reads like a
lookup. Cached. This is the single largest item in the whole pass and it
is not in a kernel.

**8. The segment length, which is the campaign's biggest lever.** At
p = 10¹⁶, 2²⁶ → 2²⁸ is **2.4×**: the per-segment costs (the base-prime
pass, the buffers, the look-back chains) amortize over four times the
line. 2³⁰ gives it back — the bitmap stops fitting the cache. SEG_DEFAULT
= 2²⁸.

**9. Host overhead, which was 0.65 ms of a 1.8 ms window.** Buffers
cached instead of allocated per segment; the per-segment device
synchronization removed entirely (n and k₀ live in device memory and the
tile count is derived on device); count/scan/compact fused into one
decoupled-look-back kernel; the state and the index share one buffer so
the whole resumable state comes back in a single transfer; limb packing
via `int.to_bytes` rather than a shift-and-mask loop. **0.65 → 0.21 ms.**

### Measured and REJECTED — do not retry these

- **Splitting the eight families across two sweep passes** to relieve
  register pressure (255 registers, spilling at height). **0.47×.** Each
  half costs nearly what all eight cost together, because the p¹⁹ chain is
  the whole bill and the other seven ride on it. This also settles a
  tempting intuition: the families are nearly free relative to the
  deepest one.
- **A persistent grid** (device-sized launch, warps drawing tiles in a
  loop) instead of one warp per tile: **11% slower**, and it buys nothing
  the tighter prime bound does not already buy.
- **Marking bytes instead of bits** in the sieve, to avoid shared-memory
  atomics. Worth **+3%** on the score window and **0.43×** at production:
  a byte tile costs eight times the shared memory of a bit tile for the
  same span, so it collapses occupancy, and every prime bigger than a tile
  falls through to the global-memory pass which has no locality at all.
  Dynamic shared memory (up to 96 KB) does not rescue it.
- **Sweeping straight off the sieve bitmap**, with no compacted prime
  array and no compaction kernel — the tile becomes a fixed span of bitmap
  words and the starting index rides in the same scan as the sums, two
  extra accumulator words. Correct first try, and **0.79×**: the bit
  extraction pushes the sweep from 168 to 254 registers, and the occupancy
  lost costs more than the 0.12 ms kernel and 96 MB of traffic it saves.
- **`--maxrregcount` and `__launch_bounds__`** at 96/112/128/160
  registers, and (128,3), (128,4), (64,8), (256,2): every one is neutral
  or worse. The kernel is work-bound, not occupancy-bound; forcing
  occupancy only buys spills.
- **Multiply-accumulating the leaf powers straight into the accumulator**,
  so p^19 never needs its own 32-word buffer. Correct, and **neutral** at
  both heights (0.999x on the score window, 0.995x at p = 10^16) --
  spilling actually rose from 96 to 160 bytes. The accumulator is 166 of
  255 registers at height on its own; removing one temporary does not
  change which side of the cliff the kernel is on.
- **A binary power chain** instead of the cost-chosen one: 231 multiplies
  against 137, 167 registers against 168, 4% slower. Depth is not what
  binds here.
- **Analytic seeding (Lucy_Hedgehog prefix recurrence).** Unchanged from
  v1's pricing: the run-up below the lowest live frontier is ~0.1% of the
  campaign and walking it buys the 124-term canary battery.
- **Widening coverage to even k.** Unchanged from v1: provably free to
  omit for every e = 0 family, and it would buy only the even terms of a
  data-entry-class sequence.

### A number that was wrong, and the bug behind it

An intermediate measurement of **1.2×10¹¹ line/s at p = 10¹²** was
recorded and even reached a commit message. It is **wrong**. It came from
a build in which reverting the persistent grid had left
`nwarp = min(ntile, device_warps)` capping the launch, so any geometry
with more tiles than the device holds warps dropped the tail of the line —
deterministically, silently, and invisibly to the battery, because every
gate shape had fewer tiles than that. The honest figure at that height is
**4.07×10¹⁰**. G15 now carries a shape with ~2,900 tiles for exactly this
reason, and the episode is the reason this log says what it says about
gates that only ever see agreement.

### Where the time goes now

Score window, 1.040 ms best of fifteen (seg 2²⁶, run 128, tpb 128,
subw 1024):

| stage | ms | share |
|---|---|---|
| sieve: marking | 0.201 | 19% |
| sieve: count/scan/compact (one kernel) | 0.138 | 13% |
| the sweep | 0.486 | 47% |
| host | 0.214 | 21% |

### What is left, and the ceiling

The next pass's candidates, unpriced: PTX carry chains
(`mad.lo.cc`/`madc.hi.cc`) for the schoolbook rows, which the C form
costs about three instructions per word multiply against a possible two;
a wheel-30 sieve representation (about 45% fewer marks and 47% fewer
positions to scan); and a bucket sieve, which is what the large-prime pass
really wants at p ≳ 10¹⁷.

None of them changes the order of magnitude, and it is worth writing down
why. On this device (128 SMs × 64 INT32 lanes × 2.535 GHz ≈ 2.08×10¹³
integer instructions per second) the frozen window's 3,957,808 primes each
need, with nothing wasted: 137 word multiplies for the shared power chain
(provably the cheapest exponent set at that height), 83 accumulator words
of carry-propagating addition, and ~42 sixty-four-bit Montgomery limbs for
the odd half of the candidates. That is **~1,250 integer instructions per
prime**, or ~0.24 ms for the window at 100% of the device's issue rate,
before the sieve and before a single launch. **A ~3,000× score is the
instruction-count ceiling for this algorithm on this hardware**, and v2 is
at 618× of it — roughly half the device's issue rate, at 168 registers and
25% occupancy, which is what a register-heavy straight-line kernel gets.
