# OPTIMIZATION LOG — hl-records (A331940)

> **Authorship disclaimer:** As with the rest of this project, this log
> and the code it describes were authored by **Claude (Anthropic's AI)**
> at the repository owner's direction.

Every attempt: change, measurement, kept or rejected. Rates are in k per
second of line swept (odd and even k both counted; only odd k cost work).
All measurements on one RTX 4090, 2026-11-11, from scratch harnesses that
import the engine; no campaign was run. Benchmark windows above 3·10^6
were tabulated and filtered, never classified.

## Round 0 — the design, the engine as built, and what is unsearched

**Target named first (OPTIMIZATION.md Rule 0a).** The model's first open
term with a median clock of a day or more is a(23), median k = 2.65·10^11;
the clock from 10^11 to 10^12 is two weeks. Every measurement below that
names no other height was taken on the window [3·10^11 + 1, + 2^23), the
SCORE shape.

### 0.1 The design decision: tabulate class numbers, by three squares

The handoff proposed a periodic count of reduced forms with small leading
coefficient as a prune. Priced before building (README, "The rigorous
prune"): the forms with leading coefficient ≤ L number ≈ 0.61·L(1, χ)·L
against a bound of 0.064·sqrt(4k − 1), so pruning a typical k needs
L ≈ 0.2·sqrt(k) and costs ~0.1·sqrt(k)/L(1, χ) increments per k in a
sieve that touches every k; and it leaves every k with L(1, χ) < ~0.4 to
an exact class number on the host. **Rejected as a prune.** Counting all
forms costs h/2 increments per k; counting sums of three odd squares
costs H/2 — the same count — with 3× fewer (x, y) rows than (a, b) rows,
no division on the hot path, no special case for small leading
coefficients (a form sieve needs a separate dense path for a < ~4000),
and it returns the exact class number of every k, so the survivors are
the 25 per million that could matter instead of a few percent. **Built:**
the GPU engine is the three-squares tabulation; the forms sieve is the
CPU parity engine.

Other routes priced and declined: the theta-series / approximate
functional equation per k (≈ 4·sqrt(k) character values per k against
0.3·sqrt(k) adds); FFT cubing of the theta series (O(log) per k, but
needs the whole prefix in memory — 10^12 coefficients — and is not
resumable by window); baby-step giant-step lower bounds on the class
number (O(k^(1/4)) form compositions per k, wins only above ~10^12 and
needs a fallback whenever the chosen form has small order).

### 0.2 The measured rate law (the engine as built: window 2^22 of m, 8 y per thread, blocks of 256)

| k | s per window | k/s | × sqrt(k/10^10) | atomic adds/s |
|---|---|---|---|---|
| 10^8 | 0.162 | 5.17·10^7 | 5.17·10^6 | 6.9·10^10 |
| 10^9 | 0.497 | 1.69·10^7 | 5.33·10^6 | 7.0·10^10 |
| 10^10 | 1.565 | 5.36·10^6 | 5.36·10^6 | 7.0·10^10 |
| 10^11 | 4.956 | 1.69·10^6 | 5.35·10^6 | 7.0·10^10 |
| 3·10^11 | 8.827 | 9.50·10^5 | 5.21·10^6 | 6.8·10^10 |
| 10^12 | 16.30 | 5.15·10^5 | 5.15·10^6 | 6.7·10^10 |

The rate is 5.2·10^6·sqrt(10^10/k) k/s to within 4% over four decades:
the cost is one atomic add per representation, ~0.3·sqrt(k) per odd k,
at a flat 7·10^10 adds/s. Later runs the same afternoon read 8.8–8.9·10^5
at 3·10^11 (ambient, −7%); the model's clocks use 4.8·10^6.

### 0.3 Phase split at 3·10^11 (sums to wall clock)

| phase | share | verdict |
|---|---|---|
| host plan (rows, prefix) | 0.015 s of 9.5 (0.2%) | below 5% |
| tabulation kernel | 9.5 s (99.7%) | see 0.4: bound by the adds |
| survivor kernel + fetch | < 0.01 s | below 5% |
| host classification (campaign loop) | 0.34% of wall | below 5% |

Campaign loop against device, same windows, classification on (against a
dummy record so nothing is narrated), health sampling on: wall/device =
**1.032 at 3·10^11** (three windows, 28.6 s against 27.7 s; one second of
it is the model's one-time table, built before the loop in a real run)
and 1.24 at 10^8 (24 windows; 8.7% is host classification at 377
survivors/s and 230 µs each, the rest the same one-time table). The
opening band lasts seconds, so its 9% is priced and left (Rule 0a).

### 0.4 Ablations of the tabulation kernel (timing only, wrong on purpose)

| variant | time | ratio | reading |
|---|---|---|---|
| shipped (`atomicAdd` per representation) | 9.38 s | 1.000 | |
| plain `cnt[idx] += w` (racy; a load and a store) | 21.96 s | 0.427 | the atomic is the CHEAP form of this update, not a tax on it |
| walk only (adds folded into a register, one store per (x, y)) | 0.705 s | 13.3 | 92.5% of the kernel is the memory traffic of the adds; rows, square roots and the z walk are 7.5% |

So the kernel is bound by the rate of atomic adds into an L2-resident
table. **Not yet a roofline verdict**: no Nsight Compute profile has been
taken (owed, Rule 1a) and INNOVATION.md's two passes have not been run on
this loop, so the row above reads "bound by add traffic, unsearched below
that".

### 0.5 Constant sweeps at 3·10^11 (paired, interleaved, sum of counters re-checked every run)

| constant | values → ratio to the default | kept |
|---|---|---|
| window (log2 of m) | 20: 1.006, 21: 1.005, **22: 1.000**, 23: 0.965; 24: 0.19 at 10^10 (64 MiB falls out of L2) | 22 — flat from 20, fewest launches |
| y per thread | 1: 0.992, 2: 0.997–1.010, 4: 0.985, **8: 1.000**, 16: 0.987, 32: 0.988, 64: 0.999 | 8 — flat |
| threads per block | 128: 0.984, **256: 1.000**, 512: 0.987 | 256 — flat |

Nothing here is a lever: every setting inside the L2 window is within
noise (±1.5%). The one cliff is the window outgrowing L2.

### 0.6 Host sizing (CONVENTIONS "Sizing a hunt")

Device seconds and host core-seconds per 10^9 of k: 1,120 s and 3.8 s at
3·10^11; 27 s and 2.9 s at 10^8. The host's need is 0.003 of a core at
the day-long height. Classification is therefore inline, and the pool is
**one** below-normal-priority worker whose only job is the sampled
independent recount (one analytic class number every 20 s; 0.42 s each at
3·10^11, a 2% duty). `--workers` does not exist because there is nothing
to throttle; `--gpu-yield-ms` and `--gentle` idle the device.

### 0.7 Levers left, priced, not built

| lever | price | status |
|---|---|---|
| A wheel on (1 − 4k | 3) = −1, i.e. k ≡ 2 (mod 3) | 77% of the adds are in the other two classes: ~4.3x, so 10^12 in ~4 days instead of 16; with 5 and 7 as well, roughly 20x | **not provable unconditionally** (README section 3). Provable under GRH from explicit L(1, χ) bounds with the sign at 3 fixed — the derivation is not written. It would make every least-k claim conditional on GRH: **the owner's decision** |
| Localising the adds (shared-memory sub-tables, or bucketing indices before adding) | unknown; the ablation says at most 13x is in the memory traffic and the L2 cliff says locality matters. A sub-window narrow enough for shared memory meets each (x, y) row at most once, so the row scan (0.014·(4k − 1) rows per window) would have to be amortised another way | unsearched — the first thing to profile |
| Nsight Compute profile + INNOVATION passes on the z walk | an afternoon | owed before any "roofline" claim |
| Direct enumeration of forms on the device, for the third confirmation above k = 10^12 | ~0.04·(4k − 1) modular tests per find, seconds on the device against 2.4 hours in NumPy at the ceiling | not built; the NumPy enumeration (0.8 s at k = 10^9, 15 s at 1.8·10^10, ~14 min at 10^12) covers every find a campaign will reach, and above 10^12 the evidence says the leg was skipped |
| A faster 34-digit leg: own series / continued fractions for erfc and E1, or precision falling with the argument | MPFR's erfc and incomplete gamma are 120 and 183 µs a call at 230 bits and are 95% of the leg (25 s at k = 10^8, 76 s at 10^9, ~40 min at 10^12); 3-4x looks available | declined for now: about a dozen finds a campaign, two or three hours in all against sixteen days |
| Cheaper host tier 1 (vectorised Legendre tables) | 8.7% of wall at 10^8, 0.3% at 3·10^11 | declined: the band it helps lasts seconds |
| Using the published class-number tabulations (Jacobson, Ramachandran and Williams to 10^11; Mosunov and Jacobson to 2^40) | their data would settle every record with 4k − 1 < 2^40 without a sweep, if obtainable | not pursued: the published tables give extreme L(1, χ), not C, and this engine re-derives the range to 2.7·10^11 in about 2.3 days |

### 0.8 Bugs the gates caught while building

- The oracle's bucketed enumeration stepped b over even values (the wrong
  parity for an odd discriminant); G1 failed against the literal count at
  D = −35, and G2 produced 34 "records". Fixed before anything else was
  built on it.
- The discovery drill assumed one find per stop; 239621 and 247757 share
  a window, and the stop is taken at the window boundary, so a run
  confirms both. The drill now asserts the real rule (stop after this
  run's own find; never at a resumed run's opening segment).
- Two rows of the literature table as printed do not reproduce (a
  misprinted discriminant and transposed digits); gate S4 carries the
  corrected values, flagged.

## Round 1 — engine v2: a class-group prefilter in front of the tabulation (2026-11-11)

**Target named first (Rule 0a).** At engine v1's rate the first open term
with a median clock of a day or more was a(23), median k = 2.65·10^11, so
the round was measured on the window [3·10^11 + 1, + 2^23) and every
result re-checked at 10^12. The round moved the clock: at engine v2's rate
a(23)'s median is 7.9 hours in, **a(24)'s (7.2·10^11) is 1.4 days and
a(25)'s (1.9·10^12) 6.3 days**, so the SCORE shape is now the window at
10^12 and the next round is measured there. Every number below names its
height; rates are k per second of line swept. One RTX 4090, scratch
harnesses that import the engine, no campaign run.

**Result.** Paired, interleaved, the survivor list compared entry for entry
on every run:

| shape | v1 | v2 | ratio | survivors |
|---|---|---|---|---|
| [10^12 + 1, + 2^23) | 17.47 s, 4.80·10^5 k/s | 2.56 s, 3.28·10^6 k/s | **6.83** | 105, identical |
| [3·10^11 + 1, + 2^23) | 9.57 s, 8.77·10^5 k/s | 1.31 s, 6.42·10^6 k/s | **7.32** | 105, identical |
| [10^8 + 1, + 4·2^23) | 0.766 s, 4.38·10^7 k/s | 0.507 s, 6.62·10^7 k/s | **1.51** | 448, identical |

### 1.1 What the kernel was bound by, settled by ablation (3·10^11)

Round 0 left the tabulation "bound by add traffic, unsearched below that".
Timing-only variants of the v1 kernel on the SCORE window, interleaved,
medians:

| variant | 2^22 window | 2^20 | 2^19 | 2^18 | 2^17 |
|---|---|---|---|---|---|
| atomic add per representation (v1) | 9.449 s | 2.393 | 1.225 | 0.664 | 0.582 |
| walk only | 0.683 | 0.601 | 0.604 | 0.534 | 0.532 |
| walk + one bit test per representation (1% of bits set), no add | 6.136 | 0.805 | 0.603 | 0.534 | 0.548 |
| walk + bit test + add where the bit is set (1% / 10%) | 6.574 / 7.348 | 0.939 / 1.044 | 0.743 / 0.747 | 0.611 / 0.609 | 0.573 / 0.580 |

Three readings, each of which the engine now stands on:

- **A load costs as much as an add.** Reading one bit per representation
  from a 512 KiB bitmap (L2) costs two thirds of the atomic it would save.
  A filter on the tabulation pays only if the bitmap is in the SM's L1
  cache: free at 64 KiB (2^19 counters), partly at 128 KiB, not above.
- **The walk-only time does not depend on the window**: 0.53–0.68 s from
  2^17 to 2^22. It is a cost per pair of larger squares, of which a window
  of any size up to 2^22 meets about 1.65·10^10. Pairs per thread swept 1,
  4, 8, 32, 128: 0.593 / 0.592 / 0.592 / 0.594 / 0.598 s — per pair, not
  per thread.
- **That per-pair cost was two double-precision square roots.** A
  single-precision root with the same integer correction loops: walk only
  0.586 → 0.166 s at 2^19 (3.5×), counters identical; with the atomic adds
  9.001 → 8.819 s (1.02×). The GeForce FP64 pipe (1/64 of FP32) was the
  bound of everything that was not an add.

So the adds are 92% of v1 and a representation that is only walked costs
about 1/14 of one that is added: the lever is to **not add**, which means
deciding most k without their count.

### 1.2 The design decision: prove a lower bound of the class number instead of counting it

The survivor rule drops k whenever T = 3H(4k − 1) is large enough, and it
is monotone in T; any proved lower bound of h(1 − 4k) that reaches the
threshold drops k without a count. Round 0 priced lower bounds from forms
with small leading coefficient (does not prune) and from class-group
orders ("wins only above ~10^12") from a cost model. Measured instead, in
a Python emulation against exact class numbers at 3·10^11 (the device's
full tabulation of the same window), 4,000–6,000 consecutive odd k each:

| prover | k left to tabulate | cost per k |
|---|---|---|
| order of one prime form by baby-step giant-step, genus factor from the primes ≤ 251 dividing 4k − 1, retries by the order of a power | 24.4% | 470 prime steps + 129 general compositions |
| the same with the EXACT number of prime factors (trial division to the cube root, then a square test and a base-2 strong-probable-prime test on the cofactor) and membership in the base form's subgroup | 4.45% (4 partners) / 1.48% (8 partners, index cap 32) | 400 + 110 |
| the shipped decision: bounds (1)–(3) of hlc_search.py, 8 split primes, a second base when the first has small order, index cap 16 | **0.35%** | 587 + 123 |
| the same without the membership test (the cheaper form of bound (3) only) | 4.10% | 472 + 139 |
| + bound (4) for 4k − 1 with a square factor (measured on the device, 2^22 window) | **0.28%** (from 0.41%) | — |

No survivor was dropped in any variant, and every claimed bound was below
the exact class number (asserted per k). Two findings that decided the
design: the genus factor needs the exact number of prime factors (a third
of the first-pass failures were prime factors above 251 counted as one),
and two flagged k in three had a square factor — for those the rule's own
quantity H(4k − 1) exceeds h(1 − 4k) by an exactly known factor, which
bound (4) hands back.

The cost model said 10^7–10^8 k/s for the device. **Measured: 1.7·10^7
k/s for pass 1 on the first kernel that compiled** (0.25 s per window at
3·10^11, against 9 s for the tabulation it replaces), with every one of
1,500 orders equal to the reference's. The model's verdict of round 0 was
wrong by the margin Rule 2 warns about.

### 1.3 The engine as shipped

Per window of 2^22 consecutive odd k (hlc_gpu.py has the arithmetic):

1. `pre1`: per k, the setup (trial division by the 1,295 odd primes to
   the cube root at 3·10^11 — one multiplication by the prime's inverse
   mod 2^64 and a compare each — cofactor test, the bound, the split
   primes), then the order of the first split prime's form: a table of
   ≤ 128 giant steps built by general compositions, walked by prime-form
   steps (one byte-table inverse and one multiplication by the inverse of
   the prime mod 2^64 each). 49,152 resident threads, each with a
   256-slot table in global memory keyed by the exact form.
2. `pre2` mode 0 on the 29% whose base form has small order: bound (2),
   then the cheap form of bound (3) for each partner; mode 1 on the 3%
   still undecided: bound (3) itself, a membership test in the base
   form's subgroup by the same table.
3. the 2.2% left go round once more with the second split prime as base.
4. `tabf`: the three-squares walk in sub-windows of 3·2^18 counters,
   testing one bit per representation and adding only for flagged k.
5. `classify` on the flagged counters; the host as before.

At 3·10^11: 4,194,304 k in; 1,235,521 past pass 1's bound; 129,511 to
membership; 92,851 to the second base; **11,675 tabulated (0.28%)**; 105
survivors, the v1 list.

### 1.4 Phase split of the v2 window (sums to wall clock)

| phase | 3·10^11 (1.292 s) | 10^12 (2.530 s) | verdict |
|---|---|---|---|
| prefilter pass 1 (both bases) | 0.248 s, 19.2% | ~0.36 s, 14% | 1.6 |
| prefilter pass 2 | 0.149 s, 11.5% | ~0.23 s, 9% | 1.6 |
| compaction between launches (CuPy) | 0.003 s | — | below 5% |
| planning the sub-windows (on the device) | 0.007 s | — | below 5% |
| flagged tabulation kernels | 0.884 s, 68.4% | 1.940 s, 77% | 1.5 |
| rule + fetch | < 0.001 s | — | below 5% |
| host classification (the campaign's `handle`, ~100 survivors a window) | 0.028 s, 2.1% of wall | 0.028 s, 1.1% | below 5% |

The 10^12 column's prefilter total (0.589 s) is measured; its split
between the passes is the 3·10^11 proportion. Campaign loop against
device: wall/device = 1.02 at 3·10^11 and 1.01 at 10^12; 1.06 at 10^8 and
10^10, bands that last seconds and minutes.

### 1.5 The flagged tabulation: Nsight Compute, and one experiment per hypothesis

`ncu --set full` on one sub-window launch at 3·10^11 (the production
engine through a scratch target): **compute-bound, not memory-bound** —
IPC 2.77, issue slots 72.6% busy, L1 hit rate 99.64%, memory pipes 21%
busy, 8.8 active warps per scheduler, 24.75 of 32 lanes active. The SASS
census by instruction counts: the representation loop is 17 instructions
at 23.6 lanes (39% of the warp-instructions: three of them the divergence
scaffolding of the conditional add, two re-materialised constants); the
loop that steps the starting square down between consecutive pairs is 6
instructions at **7.1 lanes** (19%); the 20-step binary search for the
thread's row is ~10%.

Each hypothesis as a compile-time toggle of the same kernel, one
sub-window of 2^19 at 3·10^11 with the real flags, five interleaved
rounds, the sum of the flagged counters checked on every run (baseline
0.163 s):

| change | ratio | |
|---|---|---|
| row search from a hint per 2^14 threads | **1.094** | shipped |
| step-down in closed form (float estimate from below, exact check, exact loop for the remainder) | 0.876 | declined: the straight-line float path costs more than the divergent loop saves |
| OR the bits in the loop, walk a pair again when one was set | 0.724 | declined: a third of the warp-pair iterations re-walk |
| both of those with the hint | 0.722 | declined |
| select the last hit and count hits (no branch on the bit); one hit added after the pair, two re-walk | 1.036 on the hint | shipped |
| the same with the walk's increment as the loop variable | **1.114** on the hint | shipped |
| pairs per thread 2 / 3 / 4 / 6 / 8 / 16 (final loop) | 1.224 / 1.229 / 1.209 / 1.152 / 1.114 / 0.992 | 4 shipped (2 and 3 tie; 4 asks for half the threads) |
| threads per block 128 / 256 / 512 at 4 pairs | 1.208 / 1.209 / 1.164 | 256 |

Shipped together: 0.163 → 0.123 s per sub-window (1.33×). The first
attempt bundled the hint, the closed form and the re-walk and measured
1.83 s a window against 1.30 — the toggles are how that was untangled, and
the cost model had the sign of two of the three wrong.

**One launch for the whole window, block-synchronised phases** (each
thread keeps its pairs' positions in registers, the block sweeps the
window in phases of 2^19 counters with a barrier between them so the
bits being read stay in L1, one 1024-thread block per SM): built, gated
green, and measured 4.24 s against 1.30 (0.31×). Phase width / block:
2^19/1024 4.50 s, 2^22/1024 5.41, 2^16/1024 5.90, 2^18/512 2.89, 2^17/256
3.61. The barrier idles the SM while one warp finishes its phase.
**Declined, removed.**

**The starting square without a square root** (the excess over the
window's start grows by a known amount per pair and the root steps down
while it can): 1.20 s → 1.31 s a window in two sittings in which the v1
reference moved 8.74 → 9.45 s. A wash to within the ambient drift, kept
(it is the form the loop toggles were measured on); not separated by a
paired run.

**Sub-window size** (full window, three interleaved rounds, ratio to 2^19
= 0.963 s at 3·10^11 and 2.256 s at 10^12):

| counters (KiB of bits) | 2^18 (32) | 720,896 (88) | **786,432 (96)** | 851,968 (104) | 917,504 (112) | 983,040 (120) | 2^20 (128) |
|---|---|---|---|---|---|---|---|
| 3·10^11 | 0.716 | 1.084 | **1.072** | 1.103 | 0.700 | 0.431 | 0.374 |
| 10^12 | — | — | **1.172** | 1.253 | 0.687 | — | — |

The cliff is between 104 and 112 KiB of bitmap. Shipped 786,432: a step
and a half below it. 851,968 is priced at 1.03× more at 3·10^11 and
1.07× at 10^12 on the tabulation (about three hours of the 1.9 days from
3·10^11 to 10^12) and declined for sitting on the last step before a
0.69× cliff on a constant that is a property of the card's cache.

### 1.6 The prefilter: per-launch split, Nsight Compute, sweeps

Per launch at 3·10^11 (sums to the prefilter's 0.400 s):

| launch | items | time | per item |
|---|---|---|---|
| pass 1, first base | 4,194,304 | 0.243 s | 58 ns |
| pass 2 mode 0 | 1,235,521 | 0.033 s | 27 ns |
| pass 2 mode 1 (membership) | 129,511 | 0.076 s | 587 ns |
| pass 1, second base | 92,851 | 0.007 s | 71 ns |
| pass 2 mode 0, second base | 55,800 | 0.004 s | 63 ns |
| pass 2 mode 1, second base | 24,130 | 0.036 s | 1,500 ns |

The setup alone (pass 2 handed an order so large that bound (2) drops at
once): 0.0109 s, 2.6 ns per k — 4.5% of pass 1; with 53 trial primes
instead of 1,295, 0.0029 s. The trial division is not a lever.

`ncu` on pass 1: IPC 1.52, issue slots 37% busy, no eligible warp on 61%
of cycles, **9.7 of 32 lanes active**, 102 registers a thread, L1 hit rate
82%, L2 91%. Pass 1 is divergence-bound: the lanes of a warp are in
different data-dependent branches of the composition, the extended Euclid
and the reduction.

Sweeps at 3·10^11, three interleaved rounds, the flags compared bit for
bit on every run (baseline 0.399 s):

| knob | ratio | kept |
|---|---|---|
| resident threads 32,768 / **49,152** / 98,304 / 196,608 (blocks of 256) | 0.785 / 1.000 / 0.910 / 1.013 | 49,152 (the tie asks for four times the table memory) |
| general compositions priced at 3 / **5** / 8 / 12 prime steps | 1.017 / 1.000 / 0.945 / 0.872 | 5 (flat from 3) |
| pass 1 handed its k in the order of their step counts (a setup-only pass, then a sort) | 1.008 at 3·10^11, 1.003 at 10^12 | declined, removed: the divergence is inside the steps, not between step counts |
| pass 2's membership walks in the order of their job size | 0.845 at 3·10^11, 0.805 at 10^12 | declined, removed: the long jobs end up alone on a few warps |

### 1.7 Who is still tabulated (3·10^11, 2^20 consecutive odd k, before bound (4))

4,192 flagged (0.400%). By h(1 − 4k) over the bound to prove: below 1
(no lower bound can drop them — the survivors and their neighbours) 249;
1–1.25: 219; 1.25–1.5: 614; 1.5–2: 1,920; 2–4: 1,089; above 4: 101. With
9 | 4k − 1: 1,956; with any square factor: 2,668. Residue of 4k − 1 mod 3
(2^22 window, 17,016 flagged): 9,931 / 6,269 / 816 for 0 / 1 / 2. So 94%
of the flagged k have a class number above the bound and an unlucky
group; bound (4) took the count from 17,016 to 11,675. It no longer
matters for speed — the flagged adds are 0.03 s of the window — but it
sets the price of two levers in 1.8.

### 1.8 Termination table at the day-long height (10^12), and the levers left

| phase | share at 10^12 | verdict |
|---|---|---|
| flagged tabulation: the representation loop | ~51% | optimized 1.33× this round (1.5); compute-bound at IPC 2.8, ~12 instructions a representation at 74% lane occupancy, against a floor of ~10 at 32 lanes — within 2× of the instruction roofline, and not below it: every representation of every k in the window is still visited to find the 0.3% that are flagged. **Not a floor of the problem** — see the levers |
| flagged tabulation: per pair of larger squares | ~25%, growing like k | the pair scan is repeated in each of 5.33 sub-windows because the bitmap must fit L1; the one-launch arrangement that would amortise it was built and lost (0.31×). Unsearched below that: see the third lever |
| prefilter pass 1 | ~14% | divergence-bound (9.7 of 32 lanes); two levers priced below, neither built |
| prefilter pass 2 | ~9% | membership walks at the longest lane's length; ordering them measured 0.81–0.85 |
| host | 1% | below 5% |

Levers left, priced, not built (Rule 5b — the order is a recommendation):

| lever | price | status |
|---|---|---|
| **Order of the SQUARE of the base form, by steps of the squared prime** | for the 96% of k with two or more prime factors the bound that matters is on the order of the square, half the size: table and walk both shrink by √2, the decision is unchanged (it is bound (2) applied first). By the step counts 0.71× of pass 1 and of the membership walks: ~0.1 s of the 1.3 s window at 3·10^11, ~0.15 s of 2.5 s at 10^12 (**~6%: about 3 hours of the 2.3 days to 10^12**) | not built; needs byte tables of inverses modulo the squares of the primes to 13 and a fallback of two prime steps above |
| A prime-form step with a fixed, branch-free reduction | pass 1's walk half runs at 9.7 lanes of 32; if a straight-line step took that to ~20 the prefilter would lose a quarter of its time (~0.1 s a window) | not built; the step-down experiment in 1.5 (0.876) says not to trust this model before a toggle measures it |
| A folded 96 KiB bitmap over the whole 2^22 window, exact bitmap on a hit | the pair scan once instead of 5.33 times, the loop ~1.5× dearer (a 2% hit rate at warp level): by the measured pair and representation costs 1.10 s against 0.90 at 3·10^11 and 2.07 against 1.93 at 10^12 — **slower in the band that runs for days** — and 7.4 s against 10.4 at 10^13 | declined on the price for this band; the lever for a campaign past ~3·10^12 |
| Tabulate one residue class of 4k − 1 mod 3 less | a representation of 4k − 1 ≡ 2 (mod 3) has exactly one square divisible by 3, and those are 4/9 of all representations; if the prefilter left NO flagged k in that class the walk could skip them: 1.8× on the tabulation (~0.4 s of 1.3 at 3·10^11). Today 816 of 17,016 flagged k are in it (before bound (4)) | not built: it needs a third prover that empties the class (or a fallback pass when it does not), and stays unconditional only because each k in the class is dropped by its own proof |
| Exact class numbers of the flagged k by the analytic formula on the device, no tabulation at all | ~2·10^6 character values and two transcendental functions per flagged k; at 11,675 flagged a window an estimated 0.3 s against today's 0.9 s walk at 3·10^11, FP64-bound, and it scales like the prefilter rather than the walk | not built, and **the owner's decision**: a survivor's count would then be a rounded floating-point sum, not a count |
| Baby-step table in shared memory, one k per warp | removes the L2 traffic of the tables (L1 hit rate 82% in pass 1) | not priced beyond the profile; behind the two divergence levers |
| Rider of round 0: the GRH-conditional wheel | unchanged, and now worth less: it would remove 77% of a tabulation whose adds are 0.3% of what they were | the owner's decision, as before |

Round 0's 0.7 list, resolved: "localising the adds" — settled by not
adding (1.2); "Nsight Compute profile + INNOVATION passes" — done for the
flagged tabulation (1.5: the representation alternatives are the rows of
its table, each tried or priced) and profiled for pass 1 (1.6), whose
instruction-level pass is the second lever above and is **owed**.

### 1.9 Constants and their freshness (3.4)

Swept after the last structural change, at 3·10^11 and where marked at
10^12: sub-window size (both), pairs per thread, block size, prefilter
threads, the composition price. Not re-swept this round: the window of
2^22 (it no longer holds the adds: its size now only sets how many
launches a window costs), and the full tabulation's own 8 pairs per
thread (the gates' path).

### 1.10 Bugs and hazards the round turned up

- **A latent false alarm in v1's health check.** The campaign sampled
  a counter of "the last window" every 20 seconds, but a find's recount
  overwrites that buffer with a window of 37; a sample taken after a
  recount would have compared a stale counter with the analytic class
  number and halted the campaign. The engine now knows whether its
  buffers still hold the window (`sample()` returns None otherwise), and
  the health check alternates between a tabulated count and a k the
  prefilter dropped (its analytic count must be dropped by the rule too).
- The device kernels matched the reference on their first run; the
  parity gate (P5) and the stream gate (P6) were written before any
  timing was believed.
- A rule-8 reminder: a `python -` here-document hung the shell twice in
  this session and had to be stopped by hand; the harnesses are files.

### Method notes (so the harnesses can be rewritten in ten minutes)

- Kernel variants: the shipped source with the two adds turned into a
  macro (atomic add / fold into a register with one never-true store /
  bit test) and compile-time toggles for the row search, the step-down
  and the loop; one window or sub-window, a warm launch, then N
  interleaved rounds, medians; the sum of counters asserted equal on
  every run.
- Prefilter emulation: Python integers, Cohen's Algorithm 5.4.7, a
  dictionary of baby steps; exact class numbers from the device's full
  tabulation of the same window through `h_from_t3`; asserts that no
  dropped k is a survivor and that every bound is below the class number.
- Paired engine runs: the v1 module imported from a copy beside the v2
  module, the same windows alternately, the survivor arrays compared.
- Nsight Compute: `ncu --kernel-name tabf|pre1 --launch-skip 1|2
  --launch-count 1 --set full` on a 20-line target that builds the
  production engine and runs three sub-windows (or one 2^20 prefilter);
  `--page details`, and `--page source --print-source sass --csv` reduced
  to per-instruction share of samples, of warp-instructions and lanes.

## Round 2 — the Codex review tested: engine v3 (2026-11-11)

**Where the hunt is, and the target named first (Rule 0a).** The owner's
first campaign ran the same day and stopped at k = 12,557,746,177 with
a(12)..a(30) found (a(30) = 11410046357, C = 9.32896; the literature's
k = 21425625701 bounds a(31)). From that checkpoint, at engine v2's rate
law, the model's first open term with a median clock of a day or more was
a(35), median k = 7.5·10^11, 35 hours in, with a(36) at 2.0·10^12; the
whole clock to the ceiling was 107 days and was spent above 10^12. So the
round was measured on the SCORE window at 10^12 and on 3·10^12, with
3·10^11 and 10^10 (the cursor's own decade) alongside; every number below
names its height. Paired and interleaved throughout, the survivor stream
compared on every run, one RTX 4090, scratch harnesses that import the
engine; no campaign was run. The Codex review is
[codex-reviews/2026-11-11-static-review.md](codex-reviews/2026-11-11-static-review.md);
its finding IDs are used below.

**Result.** Paired against engine v2 (its module rebuilt from a copy):

| shape | v2 | v3 | ratio | k left by the prefilter |
|---|---|---|---|---|
| [10^10 + 1, + 2^23) | 0.386 s | 0.137 s | 2.81 | 9,337 → 4,082 |
| [3·10^11 + 1, + 2^23) | 1.298 s | 0.316 s | 4.11 | 11,675 → 5,182 |
| [10^12 + 1, + 2^23) | 2.496 s | 0.461 s | **5.41** | 12,013 → 5,303 |
| [3·10^12 + 1, + 2^23) | 5.323 s | 0.714 s | **7.45** | 12,196 → 5,395 |

Shipped: HLC-003 (the sparse exact count, which replaces the flagged
tabulation), HLC-001 (local Euler factors in the rule), HLC-002 (the
prefilter in the fundamental discriminant's class group), HLC-006 (the
contract changes they need) and a re-swept thread count. Declined with
prices: HLC-004 in two forms, three prefilter-stage variants. Deferred:
HLC-005, and HLC-003's confirmation enumerator.

### 2.1 The v2 window at the target heights, and who is flagged

| k | prefilter | flagged tabulation | window | flagged | 4k − 1 mod 3 = 0 / 1 / 2 | with p² \| 4k − 1 |
|---|---|---|---|---|---|---|
| 3·10^11 | 0.401 s | 0.895 s | 1.294 s | 11,675 | 5,208 / 5,736 / 731 | 5,537 |
| 10^12 | 0.565 | 1.924 | 2.493 | 12,013 | 5,520 / 5,770 / 723 | 5,810 |
| 3·10^12 | 0.881 | 4.457 | 5.318 | 12,196 | 5,566 / 5,870 / 760 | 5,811 |

The tabulation was 77–84% of the window, and its cost did not depend on
how many k were flagged: it visits every representation in the window to
find the 0.3% it needs (round 1.5). Exact class numbers of 3,000 sampled
flags at 10^12 (from the flagged counters): with 4k − 1 ≡ 0 (mod 3) (3
ramified) none has h below the bound it needs, h/need quartiles 1.88 /
2.22 / 2.68, 77% of them with a square factor; ≡ 2 (3 split), quartiles
3.16 / 3.89 / 4.66; ≡ 1 (3 inert), 1.61 / 1.85 / 2.17, and the 28 below 1
are the survivors. All 105 survivors are in the inert class. So almost
every flagged k has a class number well above its bound and was flagged
because two prime forms could not prove it — a case for exact work on
the flagged k alone.

### 2.2 HLC-003: the sparse exact count (shipped)

**The count.** The reduced forms (a, b, c) of discriminant 1 − 4k have
odd a ≤ sqrt((4k − 1)/3), and for each a the b are the roots of
b² ≡ 1 − 4k (mod a), each as its odd representative in (−a, a]; the form
is reduced iff c ≥ a (b ≥ 0 when c = a). For a ≤ A = isqrt(4k − 1)/2,
4a² < 4k − 1 forces c > a for every root, so those a contribute 3·N(a),
N(a) the number of square roots of 1 − 4k modulo a: multiplicative,
N(p^e) = 1 + ((1 − 4k)|p) for p ∤ 4k − 1 and closed forms for p | 4k − 1
(hlc_gpu.py's header). No root is computed there — one Legendre symbol
per prime p ≤ A and a smallest-prime-factor table. The band
A < a ≤ sqrt((4k − 1)/3) needs the roots: Tonelli–Shanks, Hensel, the
closed forms, CRT. This is the review's modular-root enumerator with the
roots replaced by their number wherever the reduction condition allows
it; every prefix of phase A is a lower bound of T, so the rule may drop k
after any chunk of a.

**Checked before building** (a NumPy prototype): phase A plus the band
equals the three-squares count on 180 discriminants at k = 10^6, 10^7 and
3·10^8. On 300 flags at 10^12, phase A alone decided all 298 that were not
survivors, after a median 0.48 / 0.57 / 0.26 of the range a ≤ A for the
classes 0 / 1 / 2 mod 3 (P90 0.63 / 0.69 / 0.33). Only survivors reach
phase B: about 1% of what the prefilter leaves.

**Built** as two kernels, one k per block of 256 threads taken from a
queue: `spa` (the characters as shared-memory bits, the multiplicative
sum in 32 chunks, the rule after each) and `spb` (the band). Exact on the
first build: equal to the three-squares count on 16,384 discriminants in
windows from k = 1 to the ceiling (gate P7 adds 26 neighbourhoods of
constructed ones: 4k − 1 = 3a², divisible by 3^15, by 5^8, by p², p³, p⁴
up to p = 65537). Survivor
streams identical to v2 at 10^8, 10^10, 3·10^11, 10^12, 3·10^12.

| k | v2 window | with the sparse count | ratio | the sparse phase | to phase B |
|---|---|---|---|---|---|
| 10^10 | 0.386 s | 0.183 s | 2.10 | 0.006 s | 111 of 9,337 |
| 3·10^11 | 1.299 | 0.435 | 2.99 | 0.031 | 108 of 11,675 |
| 10^12 | 2.496 | 0.658 | 3.79 | 0.091 | 108 of 12,013 |
| 3·10^12 | 5.317 | 1.046 | 5.08 | 0.166 | 109 of 12,196 |

The sparse phase costs 0.09 s where the walk cost 1.92 s at 10^12: a
flagged k now costs ~7 µs of exact counting. Chunks (the sparse phase
alone at 10^12, five interleaved rounds): 4: 0.881, 8: 1.000, 16: 1.072,
**32: 1.128**, re-swept after 2.5–2.6 at 16 / 64 / 128: 1.006 / 1.006 /
1.004 — flat; resident blocks 512 / 1024 / 2048 flat. The flagged walk
(`tabf`, `tab_flagged`) was removed (CLAUDE.md rule 3); the full walk
`tab` stays for the gates, the recount, floor 0 and the band below
PRE_MIN_N.

### 2.3 HLC-001: the local Euler factors in the rule (shipped)

E(k) ≤ (π²/8)·Q(k) with Q the product over p ≤ 251 of 1 (inert),
1 − 1/p² (p | 4k − 1), 1 − 2/(p(p − 1)) (split) — a proved bound, no GRH,
no truncation (hlc_search.py states it). It enters the rule's right side
(π·sqrt(4k − 1)·Q), the prefilter's bound and phase A's test, as one IEEE
expression in both engines, padded by 1 + 2^−40. Paired on top of 2.2:

| k | window, Q = 1 | with Q | ratio | prefilter ratio | k left | survivors |
|---|---|---|---|---|---|---|
| 10^10 | 0.184 s | 0.159 s | 1.16 | 1.18 | 9,337 → 6,153 | 109 → 97 |
| 3·10^11 | 0.430 | 0.361 | 1.19 | 1.17 | 11,675 → 7,874 | 105 → 93 |
| 10^12 | 0.642 | 0.530 | 1.21 | 1.19 | 12,013 → 8,052 | 105 → 93 |
| 3·10^12 | 1.018 | 0.807 | 1.26 | 1.25 | 12,196 → 8,146 | 104 → 91 |

The raw stream shrinks; the census, near events and records cannot (the
rule drops only k with C ≤ the floor). Checked on its own terms: on 13
windows from k = 3·10^5 to 3·10^12 the host classified every k the
local rule removes — 143 of them, the largest C 7.45085 against the floor
7.5 — and the census bins of the two streams were identical on every
window. Gate S9 keeps that check (53 removals on three CPU windows,
largest C/floor 0.9927).

### 2.4 The prefilter after 2.2–2.3, per launch (10^12)

| launch | items | time | per item |
|---|---|---|---|
| pass 1, first base | 4,194,304 | 312.6 ms | 75 ns |
| pass 2 mode 0 | 1,020,133 | 29.6 | 29 ns |
| pass 2 mode 1 (membership) | 90,687 | 83.1 | 916 ns |
| pass 1, second base | 73,648 | 8.6 | 117 ns |
| pass 2 mode 0, second base | 41,064 | 2.0 | 48 ns |
| pass 2 mode 1, second base | 16,145 | 44.4 | 2,749 ns |
| prefilter | 4,194,304 | 481.8 | 115 ns |
| sparse count | 8,052 | 51.0 | 6.3 µs |

The prefilter is now ~90% of the window and pass 1 ~60%.

### 2.5 HLC-004: the order of the base form's square (declined, both forms)

Pass 1 searched ord(f) up to need/2^(t−2); bound (2) only needs
ord(f²) up to need/2^(t−1), half the target, and gives the IDENTICAL
decision (whatever bound (1) dropped, bound (2) drops in pass 2 — the
flags were compared bit for bit at six heights and never differed).

- **Steps by the squared prime form** (p², B, ·): a composition with
  r = a^−1 (B − b)/2 mod p², the inverse from the byte table and one Hensel
  step, exact division by p²; two prime steps when p | a. Ratios 0.898 /
  0.912 / 0.830 / 0.858 / **0.900** / 0.940 at k = 3·10^5 / 10^8 / 10^10 /
  3·10^11 / 10^12 / 3·10^12. Half of all reduced forms have 3 | a when the
  base prime is 3 (a third for 5, a quarter for 7), so nearly every warp
  runs both paths.
- **Prime steps, table lookups at even exponents only** (the least even
  E with f^E = 1 is 2·ord(f²); no divergence): 0.960 / 0.973 / **1.003** /
  1.024 at 10^10 / 3·10^11 / 10^12 / 3·10^12 — a wash at the target. The
  walk is bound by the compositions, not the lookups.

The log's earlier estimate (~6%, round 1.8) priced step counts and missed
the divergence. Declined; the code is removed.

### 2.6 Late prefilter stages against the sparse count (declined)

A flag now costs ~6 µs of counting instead of a share of a walk, so each
late stage was re-priced by skipping it and counting what it would have
decided (streams identical, whole windows):

| variant | 10^10 | 10^12 | 3·10^12 |
|---|---|---|---|
| shipped | 1.000 | 1.000 | 1.000 |
| no membership walks on the second base | 1.067 | 0.985 | 0.981 |
| none on the first base | 1.024 | 0.923 | 0.917 |
| none on either | 0.984 | 0.622 | 0.558 |
| one base | 0.977 | 0.717 | 0.661 |

The shipped pipeline wins at the day-long heights. The 1.07 at 10^10 is a
band that lasts minutes (Rule 3b): declined, priced.

### 2.7 HLC-002: the prefilter in the fundamental discriminant (shipped)

**Priced first.** At 10^12 the 18.9% of k whose 4k − 1 has a square
factor take 18.3% of pass 1 (56 of 307 ms), and descending to the
fundamental discriminant −d, 4k − 1 = d·f², cuts their order
target to a third at the median (BSGS steps ×0.54 on the mean).

**Built** as the review's decision-preserving form: 4k − 1 = d·f² from
the trial division (a square cofactor goes to f, anything else to d), t
the primes of d, S(f) the exact Hurwitz conductor factor, and k dropped
when the rule drops the lower count 3·L·S(f) for a proved L ≤ h(−d) — the
count is exactly 3·h(−d)·S(f) for d > 3; d = 3 is always counted. Every
bound of round 1 is applied in the group of −d. It replaces bound (4),
which was the part of S(f) visible from the group of 1 − 4k. The
characters in Q stay those of 1 − 4k. The CPU reference changed with it
(P5 parity bit for bit,
now also on 16 neighbourhoods of constructed conductors: a prime square
beyond the trial division with d = 3, 11, 19, …; odd exponents ≥ 3; four
square primes; S8 checks every claimed bound against the counted h(−d)).

| k | before | with the descent | ratio | prefilter ratio | k left |
|---|---|---|---|---|---|
| 10^10 | 0.157 s | 0.145 s | 1.080 | 1.074 | 6,153 → 4,082 |
| 3·10^11 | 0.362 | 0.336 | 1.076 | 1.063 | 7,874 → 5,182 |
| 10^12 | 0.530 | 0.490 | 1.081 | 1.046 | 8,052 → 5,303 |
| 3·10^12 | 0.806 | 0.762 | 1.058 | 1.014 | 8,146 → 5,395 |

Streams identical on every run.

### 2.8 Constants re-swept after the structural change (10^12 unless named)

| constant | values → ratio to the default | kept |
|---|---|---|
| general compositions priced in prime steps (RATIO) | 3: 1.012, 4: 1.008, **5: 1.000**, 7: 0.993, 10: 0.964 | 5 (flat from 3) |
| resident prefilter threads | 32,768: 0.839, **49,152: 1.000**, 57,344: 1.075, 65,536: 1.080, 73,728: 0.842, 81,920: 0.873, 98,304: 0.943 | see below |
| the same at 3·10^12 / 3·10^11 / 10^10 | 57,344: 1.076 / 1.066 / 1.062; 65,536: 1.059 / 1.100 / 1.006; 73,728: 0.837 / 0.860 / 0.767 | **57,344** |
| sparse chunks | 16: 1.006, **32: 1.000**, 64: 1.006, 128: 1.004 | 32 |

65,536 is full occupancy at pass 1's register count (512 threads a SM in
blocks of 128) and one step past it is a 0.84 cliff; 57,344 (448 a SM)
ties it at the day-long heights, wins at 10^10, holds 16 MiB less of
tables and sits a step below the cliff — the round-1.5 precedent. Round 1
had swept 32,768 / 49,152 / 98,304 / 196,608 and never tried a value
between 49,152 and 98,304.

### 2.9 The engine as shipped, and where the clock now goes

Three consecutive windows at each height (two at the top two), the phase
split summing to the window:

| k | s per window | k/s | prefilter | sparse count | k left |
|---|---|---|---|---|---|
| 10^8 | 0.062 | 1.36·10^8 | 0.060 | 0.002 | 0.054% |
| 10^9 | 0.090 | 9.33·10^7 | 0.089 | 0.002 | 0.076% |
| 10^10 | 0.139 | 6.05·10^7 | 0.134 | 0.004 | 0.097% |
| 10^11 | 0.239 | 3.51·10^7 | 0.230 | 0.009 | 0.114% |
| 3·10^11 | 0.317 | 2.64·10^7 | 0.301 | 0.015 | 0.123% |
| 10^12 | 0.478 | 1.76·10^7 | 0.439 | 0.038 | 0.126% |
| 3·10^12 | 0.726 | 1.16·10^7 | 0.651 | 0.073 | 0.130% |
| 9.9·10^12 | 1.192 | 7.04·10^6 | 1.039 | 0.149 | 0.137% |

`hlc_model.RATE_POINTS` carries this law. From the campaign's cursor the
model now puts a(35)'s median (7.5·10^11) 8 hours in, **a(36)'s
(2.0·10^12) 31 hours in — the first term whose median clock is a day or
more** — and a(37)'s (5.4·10^12) five days in; the whole remaining sweep
to the ceiling is 11.7 days (107 at v2). So the SCORE shape moves to
3·10^12 (score.py; the 10^12 shape is kept beside it), and the next round
is measured there. The model has run early so far: over the 6.28·10^9 odd
k swept, the census holds 731 / 165 / 25 / 3 values of C above 8.5 /
8.75 / 9.0 / 9.25 against 517 / 93 / 14 / 1.6 modelled, which is why
19 terms came below 1.14·10^10 where 8 were expected.

### 2.10 HLC-006: what the contract change needed

- **The rule.** survivor_mask, the device's classify, the prefilter's
  bound and phase A's test all carry Q(k); gate P0 compares Q's tables,
  P6 the production stream against the new rule on every counter, S9
  the removals against the host's rigorous C.
- **The cursor.** The key is `engine=v3-classgroup-sparse-count|...|rule=
  p251-local`. A v2 or v1 cursor covers the same line (the rules differ
  only in which k with C ≤ the floor they hand to the host), so it is
  accepted as it stands; on inheriting one, the launcher rewrites the key
  and moves the old raw survivor count to `survivors_by_rule` so the two
  rules' counts are never added. A migration drill in the selftest runs a
  v2 cursor through it and resumes.
- **The health check** compares a dropped k against the new rule
  (survivor_mask), and a counted k against the analytic class number as
  before; "counted" now means counted to the end by the sparse count.
- **The fingerprints** carry the survivors, two digests of the exact
  counts, their number, and the number and position sum of the k the
  prefilter left; re-frozen after the gates were green (BENCHMARKS.md).

### 2.11 Deferred, with prices

| item | price | status |
|---|---|---|
| HLC-003's confirmation enumerator (the discovery protocol's leg 3 by modular roots on the CPU) | the direct enumeration costs 16 s at k = 2·10^10, 80 s at 10^11, 10 min at 7.5·10^11 and is skipped above 10^12; about 16 minutes over the finds the model expects to the ceiling, against an analytic leg of ~4 hours over the same finds | deferred: the analytic leg is the larger latency, and the independence of leg 3 needs care now that the engine itself counts forms by leading coefficient |
| HLC-005, published class numbers (LMFDB) | the relevant files are 205–819 GB compressed; v3 sweeps everything below 2^38 (k ≈ 2.7·10^11) in about 2.5 hours | deferred, as the review advised; no data downloaded |
| Overlapping host classification with the next window | the campaign loop through `launch.Campaign` over 30 windows runs at 1.057× device time at 10^12 and 1.077× at 3·10^12 (1.01 under v2); classification of ~90 survivors a window is 4.3% / 3.6% of the wall clock, the rest one-time costs | not built: windows must still be classified in order before the checkpoint boundary advances past them, and a find's confirmation must stay ordered against later survivors — a launcher change with its own drills |
| Overlapping the three confirmations with the sweep | the sweep waits while a find is confirmed: ~4 hours of an ~12-day sweep to the ceiling (3%), more in the bands where finds are dense; the device floor does not depend on the record, so the windows could continue while a worker confirms | not a Codex finding; not built |
| Raising K_CEIL | the arithmetic is safe to 4k − 1 < 2^46 (k < 1.76·10^13); the ceiling 10^13 was set from v2's cost (107 days), which v3 cuts to ~12 | the owner's decision; the gates would move with it |

### 2.12 Method notes

- Every A/B: whole production windows (survivors()), two to five
  interleaved rounds, medians, the survivor arrays compared on every run
  (identical, or the new stream inside the old with every removal
  classified, for HLC-001).
- The old engines for the paired tables: the module copied before each
  change and imported under another name (importlib) beside the working
  one.
- The sparse identity: a NumPy N(a) sieve (Euler's criterion vectorised
  per prime, the multiplicative sieve by slices) and a brute-force band
  against the device's three-squares counts.
- HLC-004 and the stage variants were compile-time or subclass toggles of
  the same engine; the flags were compared bit for bit on every run.

### 2.13 The census-edge stall, found in the owner's first engine-v3 run, and the fix

**What the owner saw.** Resumed with engine v3 at k = 1.2557·10^10, the
campaign's segments stopped closing for ~7.5 minutes at a time: `k` frozen
inside one window, the rate decaying, the stall report naming the segment
("sweeping from k = …"), and `host 95.7% of wall` when the segment finally
closed.

**Diagnosis.** Not the device. One survivor in each stalled window —
k = 12763724651 and k = 12885017267 — had C in [7.4999963, 7.5000011] at
the last prime tier (2^20), straddling the census floor 7.5, so
`classify` returned UNRESOLVED and `Campaign._resolve` computed C to 30
digits by Cohen's route for that k *and for the record*: about four
minutes each at this height, about forty at 10^12. Both have
C ≈ 7.4999987, below the floor; the next tier, 2^22, settles each in
0.2 s. The bug is not new with v3: the v2 run's 71-minute clock held about
six minutes of device time and nineteen confirmations, so it very likely
paid the same; the faster device made it dominant.

**The count** (CONVENTIONS.md "A rare host path is priced by its rate"):
the cheap classifier over the 78,549 survivors of 900 windows from the
cursor sent 2 past 2^20 — once in 450 windows, at 2 × 240 s, **seven times
the device time** of 0.151 s windows. The density argument had said once
in 700 windows; the 30-window loop measurement of 2.11, at 10^12, had read
1.057 because its windows held none.

**The fix** (`hlc_search.E_bounds`, `P_TIERS`; `launch._resolve`):

- the tail past P is bounded over the primes, not every integer prime to
  6: |log of the product past P| ≤ 1.0001·(1 + 3/P)·(P(2) − Σ_{p≤P} 1/p²),
  P(2) = 0.45224742… the prime zeta value (recomputed in gate S10 by
  Möbius inversion of log ζ) — 4.9× tighter than 1/(3(P − 8)) at 2^20,
  about 6× at 2^26;
- the truncated product is exp of an exactly rounded sum of logarithms
  (`math.fsum`), so its rounding allowance is ~10⁻¹⁵ however many primes
  it covers. The old product was multiplied out with a fixed 10⁻¹¹, which
  the 82,025 multiplications below 2^20 could exceed in the worst case — a
  latent gap in the rigour, closed;
- tiers 199, 9973, 2^20, 2^22, 2^24, 2^26, 2^28, the last four vectorised
  (2^28 by a segmented sieve); widths at C = 8.25: 1.25·10⁻², 1.6·10⁻⁴,
  1.06·10⁻⁶, 2.4·10⁻⁷, 5.6·10⁻⁸, 1.3·10⁻⁸, 3.0·10⁻⁹; times 0.02 / 0.08 /
  0.34 / 1.3 / 5.4 s for the last five;
- `_resolve` reads the record's stored 34 digits instead of recomputing
  them (half of every fallback), and names itself to the heartbeat;
- the canary checks keep 2^20 (`P_CHECK`, ample for 5 and 7 decimals);
- `huntlib.hostcost` is wired in: every survivor is classified inside a
  `HostCost` item, the deep tiers and the analytic route are counted as
  named paths in `[STATUS]`, a step over 5 s gets a `[WARN]` naming its k,
  and a discovery's verification is marked expected. Gate S10 and the
  launcher's slow-step drill pin it.

**Measured after** (the same 900 windows at the cursor; 400 windows at
10^12 against a dummy record, so nothing ahead of the campaign is learned):

| | k = 1.26·10^10 | k = 10^12 |
|---|---|---|
| settled at P = 199 | 74,002 of 78,549 (94.2%; 86.7% before) | 33,326 of 35,284 (94.5%; 87.0% before) |
| at 9973 | 4,493 | 1,929 |
| at 2^20 | 54 | 29 |
| past 2^20 | 0 (2 before) | 0 (0 before) |
| host classification a window | 8.7 ms, 6.1% of device (21.5 ms, 14.3% before) | 14.3 ms, 3.2% (26.8 ms, 6.0% before) |

The deep tiers are too rare to count in 900 windows, so their rates come
from the measured straddle density (54 survivors straddled a cut at the
2^13 tier's width of 1.6·10⁻⁴ in 900 windows: ~370 per unit of C per
window over all the cuts), scaled by each tier's width:

| path | reached | cost | at 1.26·10^10 | at 10^12 | at 3·10^12 |
|---|---|---|---|---|---|
| tier 2^22 | once in ~2,500 windows | 0.08 s | 0.02% | — | — |
| tier 2^24 | ~11,000 | 0.34 s | 0.02% | — | — |
| tier 2^26 | ~48,000 | 1.3 s | 0.02% | — | — |
| tier 2^28 | ~210,000 | 5.4 s | 0.02% | — | — |
| analytic route (one C at 30 digits) | ~900,000 | 240 s / 2,400 s / 4,200 s | 0.19% | 0.6% | 0.64% |

Under 1% everywhere to the ceiling, against ~700% before. The first-tier
gain (94% settled at P = 199 instead of 87%) is a side effect of the tail
bound and halves the host's ordinary classification cost.

**Caught by the new drills, before any run.** (1) The status line reused
the name `tail` for the host-cost fragment, overwriting the model's tail
probability on the next line: a live run would have dropped `P(a(n) by
now)` silently and then failed every heartbeat line once a step was slow
(the heartbeat logs a failed line as `[WARN]` and carries on). The
slow-step drill calls `status_line()` itself and failed on it. (2) An exact
tie with the record (`same_constant`) can never separate from it, and the
new tiers made such a k walk all seven of them (7 s) before the tie test at
the end; the test now runs at the first tier whose interval meets the
record, and the tie is binned by the record's own interval. The discovery
protocol's leg 1 stays at 2^20 (`P_CHECK`), as in the nineteen evidence
records already written; at 2^28 it had added 5 s to every confirmation
and 90 s to the selftest.

## Round 3 — engine v4: the confirmations split over a pool, the ceiling from 10^13 to 10^18 (2026-11-12)

Two owner directives after the second campaign run (a(31) and a(32)
confirmed at k = 21072785801 and 21425625701, 372 s and 364 s each, the
device idle while they ran): make the verification of a candidate record
faster, and raise the engine's limit from 10^13 "to much higher (ideally
infinite)". Neither is a filter's speed (rule 3b): the first is a host
path paid once per find, priced at the find's height (a(32)); the second
is correctness, priced by what it costs the windows below the old
ceiling (3·10^12, the SCORE shape, and 10^13) and measured where it is
new (3·10^13 to 10^15). Scratch harnesses import the engines; no campaign
was run, and the owner stopped the hunt before any GPU work.

### 3.1 Where a find's three confirmations go (a(32), one core)

| part | cost |
|---|---|
| leg 2's approximate functional equation: 1,624,257 terms at 229 bits (34 digits + 30 guard) | 213–217 µs a term, **~350 s** |
| — of which MPFR `gamma_inc(0, x)` (E1, for the even s; x = π j²/d is the code's argument of the j-th term) | 123 µs a term (~200 s); 11 µs at x < 1, 257 µs at x ≥ 40 |
| — of which MPFR `erfc(√x)` | 82 µs a term (~133 s) |
| — exp, the recurrences, the sums | ~10 µs a term |
| leg 2's Euler products (fixed) | 1.1 s |
| leg 3's enumeration of forms | 16 s (2.11's figure at 2·10^10) |
| leg 3's device recount (three squares, a window of 37) | 2.9 s at 10^13; 0.2 s at 10^12 |

`-eint(-x)` in place of `gamma_inc(0, x)` gives the identical value at the
same cost (212 vs 213 µs a term): declined.

### 3.2 Shipped: the CPU legs as chunks over a short-lived pool

Both legs are sums, so they split. Per-worker cost with W processes each
running 2,500 strided terms of a(32)'s AFE (spawn excluded):

| W | µs a term, per worker | efficiency | a(32)'s AFE |
|---|---|---|---|
| 1 | 217.0 | 1.00 | 353 s |
| 4 | 218.0 | 1.00 | 88 s |
| 8 | 224.3 | 0.97 | 46 s |
| 12 | 227.7 | 0.95 | 31 s |
| 16 | 254.5 | 0.85 | 26 s |

What shipped (`hlc_search._afe_chunk`, `_hp_plan` / `_hp_tasks` /
`_hp_finish`, `verify_find(pool=, workers=)`; `launch.confirm_workers`,
`confirm_pool`; `huntlib.pool.burst`, `wait`, `burst_drill`):

- the AFE as 4W interleaved chunks (term j ≡ c + 1 mod 4W, so every chunk
  sees the same mix of x and the early workers take up the ramp's slack);
  each term computed exactly as before and truncated to the grid
  2^−(bits+32) of the first term, the chunk returning INTEGER sums: the
  total is exact in the grid, so the digits do not depend on W
  (truncation over N terms is below 2^−(bits+32−log2 N) of Lam(s), far
  inside the 30 guard digits); χ(j) by `gmpy2.kronecker` per term, so a
  chunk holds no table that grows with d;
- the enumeration in W chunks of a of equal work (cuts at A·sqrt(i/W));
- the device recount runs in the launcher's process while the pool works;
- the pool: one process per 20 s of the legs' measured single-core cost
  (`confirm_seconds`: AFE terms × 2.2·10^−4 s + 4k × 1.9·10^−10 s below
  ENUM_MAX_N), at most 12 (`--verify-workers` caps it); ramped by spacing
  the first W real submissions 0.35 s apart; terminated at once on any
  exception (`huntlib.pool.burst`). a(11) stays in one process, a(32)
  takes 12;
- the census-edge resolve (2.13) uses the same route and pool.

Checked: a(12)'s published C, 8.250961003113580563239461025116241, by one
process (17.8 s) and by four (6.5 s), the two mpf values bit-identical;
gates S3 and S6; the launcher's confirmation drill (a(11) on three
processes gives the in-process evidence, JSON-identical).

**A bug the new drill caught before any run:** on Windows a blocking
`future.result()` is not interruptible, so Ctrl+C during a confirmation
would have been held until a chunk finished — the burst drill measured
60.4 s for a 60-second chunk. Waits are now sliced (0.25 s): 0.5–0.8 s.

Not measured: a find confirmed end to end through the launcher (no run
since). At a(32)'s height the table projects ~31 s for the AFE, plus the
ramp (~4 s for 12) and the enumeration's share: ~35 s where 364 s was
spent, and 40 minutes at 10^12 become ~3.5.

**Priced, not built:** adaptive per-term precision. The j-th term carries
~j e^−x/x, so it needs ~1.44x fewer bits for the same absolute error, and
MPFR's special functions are slowest at large x. With precision bits +
log2 j − 1.44x + slack: 1.22× / 1.38× / 1.56× at slack 0 / −20 / −40,
worst summed error 1·10^−65 / 2·10^−59 / 6·10^−54 of Lam(s) against the
~10^−36 that 34 digits need. It needs a written error bound before it
ships; with the pool it would take a(32) from ~35 s to ~25 s.

### 3.3 What held engine v3 at 2^46, and engine v4

| part | v3 | where it ends | v4 |
|---|---|---|---|
| form-table key (the prefilter's giant steps) | a·2^24 + (b mod 2^24), one u64 with the generation and index | injective only while a < 2^23, i.e. 4k − 1 < 3·2^46 (k ≈ 5.3·10^13): past it two forms could share a key and a hit would claim an order the group does not have — **unsound**, not just wrong | below 3·2^46 unchanged; above, a 16-byte slot keyed a·2^32 + (b mod 2^32), read in one load |
| prime-form step residues | float quotient | exact while a < 2^23 | 32-bit multiply-high quotient, exact for every u32 (and equal below) |
| trial division | primes to 41,400 | the cube root of 2^46 | to 1.7·10^6 (2^62's), each window to its own |
| bound attempted | PRE_NEED_MAX 2^22 | reached near k ≈ 9·10^14 | 2^28 (no k below 1.76·10^13 needs more than 6·10^5) |
| characters in the sparse count | a bitmap of every prime below isqrt((4k − 1)/3), in shared memory | 48 KB = 389,120 primes: k ≈ 2.3·10^13 | that bitmap as far as it fits; past it one Euler criterion per prime, at most one such prime per a |
| sparse tables | built for 2^46 at start | — | v3's size at start, grown on demand (doubling) to isqrt(2^62/3); built in u32, vectorised, identical at v3's size |
| the walk | float root, one grid, u32 counters | grid at 2^31 blocks (k ≈ 8·10^13; 3·10^13 for the recount) | double root, launched in pieces; refuses past 2^53, where T can pass 2^32 (the recount then says it was skipped) |
| the rule's RHO_LARGE | two primes past 251 | 257²·263²·269² = 3.3·10^14 | the window's: v3's below 2^46, three primes by 2^62 |
| the rule's RHO_MIN | 0.33 | true minimum 0.3394 below 2^46 but 0.3235 at 2^62 — 0.33 would be **unsound** above 1.24·10^16 | the window's: 0.33 while valid, 0.32 above |
| products elsewhere | | | checked to 2^62: composition's C < 2^62, Gauss reduction's products are differences of c's, CRT and Barrett products < 2^62, b² + 4k − 1 < 2^63 (`hlc_gpu.py`'s header) |

The cursor: below 2^46 the stream is v3's, so a v3 checkpoint is accepted
as it stands, survivor count included (`KEY_V3`; the migration drill).

### 3.4 Engine v4 against engine v3 (the v3 module from a copy)

Identity: survivors, both digests, the counted number and the prefilter's
flags identical on [10^8 + 1, + 2^16 m), [10^10 + 1, + 2^18), [10^12 + 1,
+ 2^18), a whole window at 3·10^12 and [10^13 − 2^20, + 2^19); exact counts
of every counter on four windows and the 26 constructed corners. The two
new paths FORCED where v3's are exact — wide keys at every height, and
characters on the fly past the 128th prime — change nothing on any of
them.

Speed, whole production windows, seven interleaved rounds, medians, the
stream checked identical on every run:

| | v3 | v4 | v4, wide keys forced | v4, on the fly past 128 primes |
|---|---|---|---|---|
| 3·10^12 | 0.7160 s | 0.7135 s (1.004) | 0.9520 s (0.752) | 0.8316 s (0.861) |
| 10^13 | 1.1434 s | 1.1361 s (1.006) | 1.4473 s (0.790) | 1.3407 s (0.853) |

So v4 costs nothing below the old ceiling; the wide keys will cost ~0.76×
from k ≈ 5.3·10^13 (3.6), and the characters on the fly, which in
production start past the 389,120th prime, much less than the forced
figure.

### 3.5 The rate law past 10^13 (v4, floor 7.5)

| k | s per window | prefilter | sparse + classify | k counted |
|---|---|---|---|---|
| 9.9·10^12 | 1.185 | 1.039 | 0.147 | 0.136% |
| 3·10^13 | 2.147 | 1.813 | 0.334 | 0.140% |
| 10^14 (wide) | 4.660 | 3.945 | 0.715 | 0.147% |
| 3·10^14 | 8.093 | 6.490 | 1.603 | 0.148% |
| 10^15 | 14.758 | 11.174 | 3.584 | 0.154% |

The exponent is 0.50 from 10^14: the giant-step table is full (128
steps) and the prime steps go like the bound, sqrt(k). `hlc_model`'s rate
law carries these points; its clock puts 10^13 at 11.7 days, 5.3·10^13 at
143, 10^14 at 396, 10^15 at 37 years and 10^18 near a million years. The
walk: 1.68 s for a window at 10^13, linear in k; a whole window at 10^14
was 174 s (two launches), which froze SCORE_1E14 (BENCHMARKS.md).

### 3.6 Priced, not built

| item | price | status |
|---|---|---|
| a cheaper wide form table | 0.76× on the window from k ≈ 5.3·10^13 (143 days of sweep from zero). A one-word slot to a < 2^28 (k < 5.4·10^16) is possible if each thread's table is cleared per n instead of tagged by generation (key 57 bits + index 7); or a separate 2-byte meta array (10 bytes a slot instead of 16) | not built: measure both at 10^14 when the cursor nears 3·10^13 |
| a larger giant-step table | the prefilter goes like sqrt(k) once sp = 128 binds (from ~3·10^11); more steps cost L1/L2 per thread | the constant to re-sweep at the next day-long height (rule 3b) |
| adaptive AFE precision | 1.38×–1.56× on leg 2 (3.2) | needs its error bound written first |
| sparse tables near the ceiling | 4–5 GB of host memory to build at 2^62 | centuries away; a device-side build if ever needed |

### 3.7 Gates and drills

S0 checks the per-window constants at the 24 heights where they move; P0
checks both engines' copies at the 9 heights between 2^46 and 2^62 and
the refusals (a window past 2^62, a walk past 2^53); P3 adds two analytic
class numbers at 10^14 against the sparse count; P5 adds a window at
9·10^13 (wide keys); P6 adds one at 9·10^13, its walk in two launches;
P7 adds one at 6·10^13; **P8 is new**: 4k − 1 = d·f² constructed at
k ≈ 10^15 and 10^16 (f a prime past the bitmap, 3^18 dividing it, d = 3)
counted to 3h(−d)S(f) exactly, the Hurwitz relation on their neighbours,
the production stream equal to the rule on those exact counts (18
survivors at floor 2.0), the prefilter at k ≈ 10^18 equal to the
reference, and the forced paths. The launcher gained the confirmation
drill and the burst drill; the migration drill inherits a v3 cursor
whole.

**Result.** `launch.py --selftest` ALL GREEN, 44 checks in 190 s (41 in
108 s before); `score.py` reproduces all four engine-v3 fingerprints
unchanged and the new SCORE_1E14: **SCORE 11,921** (11,665 on v3 the same
morning, the ambient swing), SCORE_1E12 18,417, SCORE_3E11 26,595,
SCORE_OPEN 136,952, SCORE_1E14 1,810. The owner's live checkpoint (v3's
key, k = 29905387521, 33 terms) is read as inherited by `--status`
without being written.

## Round 4 — the profile after the Codex round and engine v4 (2026-11-12)

**Target named first (Rule 0a).** The owner's overnight engine-v4 run left
the cursor at k = 8.03·10^11 with a(33) the frontier (C = 9.62408). From
there the model at v4's rate law puts a(34)'s median (1.02·10^12) 3 hours
in, a(35)'s (1.66·10^12) 15 hours, **a(36)'s (3.19·10^12) 48 hours — the
first term whose median clock is a day or more — and a(37)'s (7.42·10^12)
7.4 days**. So the round was measured at 3·10^12 (the SCORE shape) and at
7.4·10^12, with 1.6·10^12 alongside and 10^8, 10^10, 10^12 and 10^14 as
the checks of the short bands and the wide-key path. One RTX 4090, idle
(no hunt running); scratch harnesses that import `hlc_gpu`; no campaign
run. B and C below shipped the same day as **engine v4.1** on the owner's
go (4.7).

### 4.1 Phase split of the v4 window (CUDA events around every launch; sums to the wall clock within 1%)

| launch (items at 3·10^12) | 1.6·10^12 | 3·10^12 | 7.4·10^12 |
|---|---|---|---|
| pass 1, first base (4,194,304) | 0.330 s, 58.4% | 0.410 s, 56.3% | 0.567 s, 51.8% |
| pass 1, second base (62,626) | 0.011, 1.9% | 0.013, 1.8% | 0.018, 1.6% |
| pass 2 mode 0, first base (940,068) | 0.026, 4.5% | 0.027, 3.7% | 0.030, 2.7% |
| **pass 2 mode 1 (membership), first base (58,060)** | 0.079, 14.0% | 0.101, 13.9% | 0.185, 16.9% |
| pass 2 mode 0, second base (31,695) | 0.002, 0.3% | 0.002, 0.3% | 0.002, 0.2% |
| **pass 2 mode 1 (membership), second base (10,547)** | 0.069, 12.2% | 0.096, 13.2% | 0.164, 14.9% |
| sparse count, phase A (5,527) | 0.037, 6.6% | 0.061, 8.4% | 0.108, 9.8% |
| sparse count, phase B (94) | 0.008, 1.4% | 0.012, 1.6% | 0.019, 1.7% |
| CuPy, host, synchronisation | 0.003, 0.6% | 0.006, 0.8% | 0.003, 0.3% |
| window | 0.564 s | 0.727 s | 1.095 s |

### 4.2 Nsight Compute (3·10^12, `--set full`, one launch of the second window)

| kernel | registers | grid | achieved occupancy (theoretical) | lanes of 32 | IPC | SM active / elapsed | top stalls |
|---|---|---|---|---|---|---|---|
| `pre1`, first base | 80 | 448 × 128 (0.58 wave) | 28.4% (50%) | 8.23 | 1.68 | 0.93 | wait 36%, long scoreboard 22% |
| `pre2` mode 1, first base | 86 | 448 × 128 | 18.4% | **2.37** | 1.34 | **0.63** | — |
| `pre2` mode 1, second base | 86 | **83** × 128 (45 SMs get no block) | 6.1% | **2.53** | 0.57 | **0.35** | — |
| `spa` | 40 | 1,024 × 256 | 81.1% (83%) | 17.81 | 1.63 | 0.95 | long scoreboard 58% |

- **Pass 1** issues on 39% of cycles, with no eligible warp on 57%. The SASS
  census: the giant-step walk (`tget`, `cheap`, `reduce`) holds 52% of the
  stall samples at **5.8 lanes**. Inside it, `fdiv_near`'s general quotient
  takes the compiler's 32-bit division path and the 64-bit division
  subroutine (84 instructions around a `MUFU.RCP`) about 1.08·10^8
  warp-level calls each, one lane at a time; the subroutine alone is 9.9%
  of the warp-instructions. The table probes of `tget` (the generation
  test right after each load) hold ~19% of the samples, and their
  warp-level counts fall only slowly with the probe index (3.1, 2.8, 2.5,
  2.2, 1.9·10^8): a lookup pays the longest probe chain among its ~10 live
  lanes. Local memory is 51.5% of the L1 sectors (the frames of the
  `__noinline__` `compose` and `fpow`, whose outputs are references; 99.5%
  of it hits L1); `compose` is ~20% of the warp-instructions at 13.5
  lanes. The register count is now 80 (six blocks a SM), where round 2.8
  swept the thread count at four.
- **Membership** runs one job a thread, a job being up to (partners) ×
  (need2 − 1 ≤ 15) walks of `s` prime steps, so each launch lasts as long
  as its longest job: 2.4 lanes of 32, the SMs busy 63% and 35% of the
  launch, the second base's 83 blocks leaving 45 SMs empty. Its
  thread-instructions are 4.6% of pass 1's; its time was 48% of pass 1's.
- **The sparse count** is occupied and convergent enough; 58% of its
  stalls are the dependent smallest-prime-factor loads of `nroots`
  (the `spf` table; L1 hit rate 36%, L2 99.8%).

### 4.3 Experiments (whole production windows, interleaved; the prefilter's flags compared bit for bit on two windows first, the survivor stream and the digest on every run)

**Resident prefilter threads, re-swept** (3·10^12, six rounds, ratio to
57,344): 65,536 0.998, 81,920 0.969, 98,304 0.964 (one full wave at six
blocks a SM), 114,688 0.834, 131,072 0.884. **Stays at 57,344.** More warps
buy nothing because every resident thread brings its own 2 KB table:
latency hiding loses to cache footprint.

**B. The quotient of `fdiv_near` by a float estimate.** Past the ±2 fast
path, `floorf(__fdividef(num, den))` when its magnitude is below 2^20,
made exact by the remainder (`while r < 0: q -= 1, r += den; while r >=
den: q += 1, r -= den`); the 64-bit division only past 2^20. Exact by the
loop invariant. **1.060–1.071 at 3·10^12** (two sittings), **1.050–1.086 at
7.4·10^12**, 1.082 at 10^12, 1.015 at 10^10. Pass 1 alone: 0.406 → 0.376 s
at 3·10^12; the subroutine's calls in pass 1 fall from 2.4·10^8 to
1.5·10^7.

**C. Membership's search sized by the base form's known order.** Mode 1
asks whether w = (g²)^e lies in ⟨f²⟩ by a baby-step giant-step discrete
logarithm in ⟨f⟩, and sized that search with `steps(need1)`, exponents up
to need1 − 1. But pass 1 hands pass 2 the EXACT order m1 < need1 of f (the
least hit of its own search), and every element of ⟨f⟩ is f^−u for exactly
one u in [0, m1). So `steps(m1 + 1)` (s·sp ≥ m1) finds a hit if and only if
w ∈ ⟨f⟩. Every hit gives an exponent in the same residue class mod m1, so
the parity verdict (m1 odd, or the exponent even) is the one the longer
search reached: the decision is unchanged, and each walk is m1/need1 as
long. Membership 0.192 → 0.056 s a window at 3·10^12, 0.345 → 0.072 s at
7.4·10^12. **Whole window: 1.246 at 3·10^12, 1.369 at 7.4·10^12**, 1.193 at
10^12, 1.143 at 10^10. This is a reduction of the search, of the kind
CODEX_REVIEWS.md asks a review to find; the 2026-11-11 review did not list
it.

**D = B + C** (paired against the tree's engine):

| k | ratio | rounds, per-round range |
|---|---|---|
| 10^8 (SCORE_OPEN's height) | 1.135 | 6 |
| 10^10 | 1.153 | 6, 1.148–1.163 |
| 10^12 | 1.292 | 6, 1.263–1.334 |
| **3·10^12 (a(36), SCORE)** | **1.318** | 8, 1.303–1.349 |
| **7.4·10^12 (a(37))** | **1.408–1.500** | two sittings of 4 and 6 |
| 10^14 (wide keys) | 1.354 | 3, 1.313–1.354 |

Flags identical at all six heights; streams identical on every run.

**A table of 512 slots** (load factor 0.25 instead of 0.5, 4 KB a thread;
both hash shifts widened), on D: **0.817 at 3·10^12, 0.849 at 7.4·10^12.
Declined.** The probe chains are shorter, but the footprint doubles, and
the footprint binds.

**Clock** (the model at v4's rate law, divided by D's measured ratios,
log-linear between heights), from the cursor: a(35)'s median 14.6 → 11.2
hours, **a(36)'s 48.4 → 37.0 hours, a(37)'s 176 → 130 hours**, 10^13 273 →
199 hours.

### 4.4 Where the clock goes with D

| | 3·10^12 (0.541 s) | 7.4·10^12 (0.768 s) |
|---|---|---|
| pass 1, first base | 0.376 s, 69% | 0.523 s, 68% |
| membership, both bases | 0.052 s, 10% | 0.072 s, 9% |
| sparse count, phases A + B | 0.072 s, 13% | 0.124 s, 16% |
| everything else | 0.04 s, 8% | 0.05 s, 7% |

### 4.5 Status, and the levers priced, not built (Rule 5b)

B and C shipped as engine v4.1 (4.7). What is left:

| lever | price | status |
|---|---|---|
| fingerprint table for pass 1: 32-bit slots (a hash of the form and the index), 1 KB a thread, one 32-byte read a lookup, every fingerprint hit verified against the exact form | pass 1 is 69% of the window after D; doubling the footprint cost 0.82–0.85, and halving it is the opposite move, unmeasured | not built: a table cleared per k (no generation tag), the verification path, and gates for both |
| one membership job per warp: one table built by 32 lanes, each lane walking a 32nd of the baby steps from its own offset | after C, ~10% of the window at 2.4 lanes with a tail; recovering three quarters of it is ~1.07× | not built |
| the sparse count's N(a) by a segmented multiplicative sieve in shared memory per chunk of a, in place of a dependent smallest-prime-factor chain per a | phase A is 11–14% of the window after D, 58% of its stalls on that chain; halving it is ~1.06× | not built |
| `compose` without a stack frame (inlined, or its outputs by value) | 51.5% of pass 1's L1 sectors are local; `compose` is ~20% of pass 1's instructions | untested; the cheapest of these to measure (one toggle) |
| the giant-step count for mode 1 apart from pass 1 | a membership job makes many walks against one table, so its best table is larger than pass 1's | re-sweep after C ships |

### 4.6 Method notes

- Phase split: on a constructed `GpuEngine`, each `RawKernel` attribute
  (`_pre1`, `_pre2`, `_spa`, `_spb`) replaced by a callable that records
  CUDA events around the launch and labels it from its arguments (base,
  mode); `_k1` / `_k2` wrapped to count items; `perf_counter` around
  `survivors()` with device synchronisation.
- Variants: the source text from `hlc_gpu.source()` patched (each old text
  asserted to occur exactly once) before constructing a `GpuEngine`; the
  table-size variant also widens both hash shifts and reallocates `tbl`.
- Nsight Compute: call `ncu.exe` from `target/windows-desktop-win7-x64/`
  directly, not `ncu.bat` (cmd reads the `|` of a `--kernel-name
  regex:^(pre2|spa|spb)$` as a pipe). `--launch-skip 6 --launch-count 6
  --set full` on a target that sweeps one warm window and one more (~80 s);
  pass 1 alone with `--kernel-name pre1 --launch-skip 2 --launch-count 1`
  (~2 minutes). SASS census: split at `CALL` targets; stall samples,
  warp-instructions and thread-instructions summed per region and per
  opcode; the `CALL` lines' execution counts locate the division
  subroutine's callers.

### 4.7 Shipped: engine v4.1

`hlc_gpu.py`: `fdiv_near` takes the float estimate of B; `pre2` mode 1
calls `steps(m1 + 1, …)` in place of `steps(need1, …)`, which is C, and
the CPU reference's `_in_squares` was already sized by the order
(`s = isqrt(m) + 1`), so the device now agrees with the reference's own
sizing. `ENGINE_VERSION` is "v4.1"; the cursor key stays v4's because the
line, the stream and the rule are identical, so the owner's checkpoint
(k = 8.03·10^11) resumes as it stands and runs v4.1 from its first window.

- The shipped text against v4 rebuilt from it by reverse patch: the
  prefilter's flags bit for bit on two windows at 3·10^12, streams
  identical, 1.301× (six rounds).
- `launch.py --selftest`: **ALL GREEN, 44 checks in 183 s** (P5's decision
  against the reference bit for bit to 9·10^13 and at constructed
  conductors, P6's stream against the rule on every counter to 9·10^13).
- `score.py`: all five frozen fingerprints reproduced unchanged; **SCORE
  17,104** (11,921 at round 3), SCORE_1E12 24,711, SCORE_3E11 35,370,
  SCORE_OPEN 165,520, SCORE_1E14 2,600. score.py keeps the best of three
  runs; the paired medians below are the claim.
- The rate law re-measured paired at all twelve heights (BENCHMARKS.md):
  1.15–1.17× to 10^10, 1.27× to 10^12, 1.35× at 3·10^12, 1.44–1.46× at
  9.9·10^12–3·10^13, 1.32 / 1.29 / 1.23× at 10^14 / 3·10^14 / 10^15.
  `hlc_model.RATE_POINTS` carries it. From the cursor, a(36)'s median is
  37 hours in (48 at v4) and a(37)'s 5.4 days (7.4); 10^13 is 8.5 days
  from zero (11.7), 10^14 288 (396).
- Not run: the no-flags acceptance test (a campaign: the owner's).

## Paused (2026-11-14)

The owner's v4.1 run from k = 8.03·10^11 found a(34) = 3314787117221
(C = 9.67330) on 2026-11-14 and was stopped at k = 4,149,500,444,673:
62.8 hours of campaign clock from k = 1 over engines v2, v3, v4 and v4.1,
and 23 new terms (RESULTS.md). The project is PAUSED — open to others. No
engine changed after round 4; engine v4.1 is what a resume runs.

**What a resume should read first.**
- **The model's far tail is heavy at these heights, and its re-fit is
  owed.** The census over all 2.07·10^12 odd k below the pause matches
  the model to 2% through C = 8.5 and then runs at 0.94 / 0.85 / 0.67 /
  0.44 / 0.24 of the modelled count in the bins from 8.50 to 9.75 (11
  values against 45 in the last; RESULTS.md, "The census"). a(34) came at
  the law's 99.97th percentile. Below 6.28·10^9 the same comparison had
  run the other way (25 values above 9.0 against 14). Rule 3b's target is
  named from the model's clocks, so re-fit the tail to the census before
  naming the next day-long filter: as it stands the model puts a(35)'s
  median at 4.51·10^12 (7.3 h from the pause), a(36)'s at 5.60·10^12 and
  a(37)'s at 8.21·10^12 (3.9 days); scaled to the census's last bin, a(35)'s
  median is about 5.6·10^12 (31 h).
- **a(35) ≤ 7514981191031**, Fung and Williams' value with C = 9.6758115
  (one of the model's ANCHORS), 3.2 days of sweep from the pause at v4.1's
  rate. So the next filter's clock is bounded whatever the model says, and
  the heights at which round 4 measured (3·10^12 and 7.4·10^12) bracket it.
- **The levers left are round 4.5's**, unchanged: the first pass of the
  prefilter (~69% of the window at 3·10^12, bound by its tables' cache
  footprint), the membership launches' layout, the sparse count's factor
  lookups, the wide form table from k ≈ 5.3·10^13, and overlapping host
  classification and confirmations with the sweep.
- **Run first, per CLAUDE.md rule 2:** `python launch.py --selftest` and
  `python score.py` (both green at the commit that published this project,
  2026-11-14).
