# OPTIMIZATION_LOG — square-ladders

Every attempt, its measurement, and whether it was kept. The rejections
matter as much as the wins: they are what stops the next person spending a
day re-deriving a dead end. Read [OPTIMIZATION.md](../OPTIMIZATION.md)
first; this file is the project-specific ledger.

All measurements are from harnesses that import the **engine** and call it
on a chosen window. None of them is the campaign (CLAUDE.md rule 0a).

---

## v1 — the baseline, 2026-08-21

`SCORE 10,768,681` (1.077×10¹³ k/s), 22 gates green.

One-level wheel over the primes to 23 (`W = 223,092,870`, 1,088,640
residues), candidates tested against a packed forbidden-residue bitmap by
Barrett magic-multiply with early exit, survivors compacted by `atomicAdd`.

The one design decision made before any measurement, and the reason the
engine looks the way it does: **test, do not mark.** A marking sieve of
depth 65536 pays `Σ w(q)/q ≈ 22` marks per candidate. Testing with early
exit pays the expected number of primes tried before the first kill, and
since `w(q,n) = 16` for `q ≥ 37`, the first prime kills 16/29 = 55% of
candidates and the expectation is about two. That is a ~10× structural
difference and it decided the architecture.

---

## Measurement 1 — the phase split (do this first)

OPTIMIZATION.md rule 1. Three variants compiled from one source, run
interleaved, at `n=16, p1=23, q2=65536`, 4000 wheel blocks at `k = 1e15`:

| variant | ms | candidates/s | share |
|---------|----|--------------|-------|
| full kernel | 73.27 | 5.94e10 | 100% |
| generation only (test loop removed) | 7.82 | 5.57e11 | **11%** |
| full, RES load replaced by arithmetic | 73.31 | 5.94e10 | 100% |

**Generation is 11%, the Barrett test loop is 89%, and the RES table load
is free** — replacing it with a synthetic value changed nothing, so the
1,088,640-entry table is entirely cache-resident and its size is not a
cost.

That reading decided everything after it. A cheaper test loop can save at
most 89%. A wheel prime *removes the candidate*, saving 100% of it —
including the generation the wider wheel makes slightly more expensive.
**The lever is fewer candidates, not faster tests.**

---

## Measurement 2 — the wheel sweep

| wheel | candidates per unit line | k/s | candidates/s |
|-------|--------------------------|-----|--------------|
| ≤ 13 | 3.356e-2 | 1.09e12 | 3.66e10 |
| ≤ 17 | 1.776e-2 | 2.60e12 | 4.63e10 |
| ≤ 19 | 9.353e-3 | 5.91e12 | 5.52e10 |
| ≤ 23 | 4.880e-3 | 1.11e13 | 5.40e10 |

Candidate throughput is flat at ~5×10¹⁰ across the range while the k-line
rate rises almost exactly with the wheel's density. Extrapolating says go
wider — and the next stop, the primes to 31, is where a one-level wheel
stops being possible: 261 million residues mod 2.0×10¹¹, about 2 GB, read
from DRAM instead of cache. The primes to 37 would be 5.5×10⁹ residues,
~44 GB.

## Measurement 3 — sieve depth is nearly free

`q2` from 4096 to 262144 at `p1=23` measured 1.110e13, 1.128e13, 1.111e13,
1.120e13 k/s — a 64× depth change inside 2%, which is the early exit
behaving as designed: the deep primes are reached by so few candidates that
their cost vanishes. **Depth is therefore a host-side decision, not a
device one**, and the campaign runs 65536 because it makes the host side
unmeasurably small (1.083e-11 survivors per unit line).

---

## v2 — the factored wheel. KEPT: 3.9×

Measured as `SCORE / SCORE1L` **inside a single run**, on the same window
with the same sieve depth: **3.84× and 3.94×** over three runs, against
**3.95×** from the interleaved A/B below. Quoting `SCORE 10,768,681 →
42,988,406` instead would be a cross-run comparison of two absolute
numbers, and this project has already caught that card moving 1.5× between
runs of an identical binary with no code change (BENCHMARKS.md ledger). The
ratio is the claim.

The wheel is stored as two tables and recombined per candidate by CRT:

    x = RES1[t] + W1 * ( (RES2[s] - RES1[t]) * W1^-1  mod W2 )

with `W1` the primes to 23 (1,088,640 residues) and `W2` the primes in
(23, 37] (5,040 residues). `W1`, `W2` and `W1⁻¹ mod W2` are baked into the
generated source as literals, so every `% W2` is a compile-time
multiply-shift rather than a division. The candidates mod `W1·W2` are
enumerated exactly and none of the 5.5×10⁹ of them is ever stored.

Interleaved A/B, same window, same sieve depth, fingerprints checked
identical:

| variant | candidates per unit line | k/s | vs one-level |
|---------|--------------------------|-----|--------------|
| one-level ≤ 23 | 4.880e-3 | 7.41e12 | 1.00× |
| factored (23, 31] | 1.303e-3 | 1.91e13 | 2.58× |
| **factored (23, 37]** | 7.394e-4 | 2.93e13 | **3.95×** |

Note candidates/s *falls* (5.4e10 → 2.2e10) while k/s nearly quadruples.
Both are expected and they are the same fact: the candidates the wider
wheel removes are precisely the ones that used to die at the first or
second Barrett test, so the survivors that remain are more expensive each.
The gain is real because it is measured in k-line, which is what the hunt
is paid in.

**A measurement mistake worth recording.** The first A/B reported the three
variants disagreeing on the survivor fingerprint (71, 71, 74). They were
all correct: each engine floors `k // W` with its own `W`, so a shared `j0`
is three *different* absolute windows. Aligning `k0` to a common multiple
of every `W` made them identical. The frozen benchmark now states this in
its own docstring, and every shape's `k0` is an exact multiple of its
wheel.

---

## Priced and REJECTED — do not retry

- **A wider one-level wheel (primes to 29 or 31).** `W ≥ 2^32` forces a u64
  residue table and 131 MB (p1=29) or 2 GB (p1=31) of DRAM traffic per
  pass, against a table that currently costs nothing because it is
  cache-resident (measurement 1: the RES load is free). The factored wheel
  gets the same density with two cache-resident tables. `wheel()` now
  refuses a one-level table above `RES_MAX = 2^24` rather than dying of
  out-of-memory — it silently killed two gate batteries before that guard
  existed.
- **A third wheel level, (37, 41].** `W2` would be 1,363,783 with 126,000
  residues, and the kernel maps the second level to `gridDim.y`, which CUDA
  caps at 65535. Refused by the constructor with that message. Getting past
  it means moving `j` out of `gridDim.z` and packing two levels into `x`,
  which is a real redesign; the modelled gain from (23,37] → (23,41] is
  about 1.6× and it is the best remaining lever. **Not attempted.**
- **A shallower sieve to cut device work.** Measurement 3: depth is inside
  2% from 4096 to 262144. There is nothing to win, and going shallower
  costs the host three orders of magnitude more survivors.
- **Marking instead of testing.** ~22 marks per candidate against ~2 tests.
  Not implemented, priced at roughly 10× worse, and the CPU engine marks
  precisely so that the two engines stay independent for the parity gate.

## Measurement 4 — tpb and segment size, re-swept on the v2 geometry

Both constants were set on the v1 geometry, where a wheel block was 33,263x
smaller. Interleaved, production config, fingerprints identical throughout:

| tpb | k/s | vs 256 |
|-----|-----|--------|
| 64 | 2.757e13 | 0.952x |
| 128 | 2.837e13 | 0.980x |
| **256** | **2.896e13** | **1.000x** |
| 512 | 2.772e13 | 0.957x |
| 1024 | 2.085e13 | 0.720x |

**256 was already optimal** and stays. Nothing to win; recorded so nobody
sweeps it again. The fall at 1024 is register pressure -- the kernel holds
the Barrett state and the CRT temporaries live across the whole test loop.

Segment size, at tpb = 256:

| blocks per launch | k/s | wall per segment |
|-------------------|-----|------------------|
| 1 | 2.874e13 | 0.3 s |
| 2 | 2.921e13 | 0.5 s |
| 4 | 2.892e13 | 1.0 s |
| 8 | 2.880e13 | 2.1 s |
| 16 | 2.886e13 | 4.1 s |

**Flat -- 1.6% across a 16x range.** Per-launch overhead is already
negligible, so `SEG_BLOCKS` is not a throughput knob. CONVENTIONS.md step 3
says a tie gets spent on the machine, and here the relevant cost is crash
exposure: `SEG_BLOCKS = 4 -> 2`, halving what an interrupt or a power cut
costs to ~0.5 s, against a checkpoint fsync of ~3 ms (0.6% overhead). This
is the case the rule exists for -- a sweep that measured only throughput
would have called all five settings equal and picked any of them.

## Open, in rough order of expected value

1. **Two-pass compaction between prime batches.** The test loop's cost is
   the *max* over a warp, not the mean: ~55% of lanes exit at the first
   prime while a few run to `q2`, so a warp is mostly idle lanes. Testing a
   first batch, compacting survivors, then testing the rest would convert
   divergence into coalesced work. This is the largest untested idea and
   the phase split says it plays against the 89%.
2. **The (23, 41] wheel**, once the grid mapping is redesigned (above).
3. **Re-sweep `SEG_BLOCKS` and `tpb`** — both were set on the v1 geometry
   and the block is now 33,263× larger. `tpb` has never been swept at all.

*(All three were taken up in v3 below; the section is kept as written so
the record shows what was expected against what was measured. Item 1 was
the largest idea and it was: 1.49×. But the two "cheap plumbing" items
around it were worth more together than it was — 1.29 × 1.48 × 1.11 ×
1.29 from the test body alone — which is Rule 5's "the total is a product,
not a max" happening again in the same project that wrote it down.)*

---

## Measurement 5 — what the test loop is *bound* by

OPTIMIZATION.md §2.12: buy information about the binding resource before
buying more attempts at the phase. Two differential probes, each adding
work to the loop body without changing a single result — the fingerprint
was checked on every run — with `zmask`, a kernel argument equal to zero,
carrying the added value into the output so nothing could be eliminated.

| probe | +1 | +2 | +4 | +8 |
|-------|----|----|----|----|
| extra ALU (3 instructions per unit) | 0.968× | 0.923× | 0.836× | **0.703×** |
| extra hot-region bitmap loads | 0.932× | 0.917× | — | 0.879× |

The ALU cost is **linear**: 24 added instructions cost 42% of the wall
clock, so one instruction per test is ~1.0 ms of the 913 ms window and a
divergent test is about **48 instruction slots**. The loop is
**issue-bound**. Loads are ~3% each, so all four together are ~12% of it.
That verdict is what made "fewer instructions per test" and "fewer tests
per warp" *both* real levers, and they multiply.

**The first version of the ALU probe was invalid, and is recorded because
it was convincing.** It iterated `acc = acc*A + C`, which is affine, so
nvcc composes any number of them into one `imad` with folded constants —
+2, +4 and +8 all measured 0.943 / 0.947 / 0.942, a flat line that says
"not issue-bound" as clearly as the real probe says the opposite.
Replacing it with a non-affine xorshift-multiply produced the table above.
This is exactly OPTIMIZATION.md §3.3's rule: an ablation must change one
thing, and "the compiler cannot fold this" is part of what has to be
checked.

## Measurement 6 — divergence, modelled and then calibrated

`S(j)` is the probability a candidate survives the first `j` sieve primes,
so a lane needs `Σ S(j)` tests and a warp runs to `Σ [1 − (1 − S(j))³²]`:

    E[tests per LANE] = 3.072      E[depth per WARP] = 16.056
    divergence tax    = 5.227×

A branchless prefix of `K` primes computes the identical survivor set, so
its cost is a closed form and the prediction is falsifiable. Measured
against it (U=1 tail, fingerprint green throughout):

| K | 0 | 4 | 8 | 12 | 16 | 24 |
|---|---|---|----|----|----|----|
| predicted | 1.000 | 1.000 | 0.991 | 0.927 | 0.820 | 0.620 |
| measured | 1.000 | 1.060 | 1.116 | 1.105 | 1.039 | 0.846 |

The **shape** holds — flat, then degrading — but the model under-predicts
throughout, because a branchless prefix also buys ILP that the divergent
loop cannot have. Fitting `cost = a·(branchless tests) + b·(divergent
tests) + c` gives **a = 35.6, b = 48.4 ms per warp-test, c = 146 ms
fixed**, and reproduces K = 4 / 12 / 16 to within 0.6%. So a branchless
test costs **0.735** of a divergent one, and the honest re-price of one
compaction round is ~1.7×, not the 1.82× the pure warp-test model claimed.

---

## v3 — cheaper tests, compacted warps. KEPT: 4.0×

Headline, **interleaved inside one run** against the v2 kernel compiled
verbatim, same window, fingerprint `303/999990048677220` checked on every
run of both: **4.014×** (per-round 3.893, 4.014, 4.016, 4.079, 3.962,
4.054, 4.007 — v2 1029.5 ms, v3 256.5 ms end-to-end through
`survivors_j`). Every one of the four frozen shapes rose and none fell:
`SCORE` ×4.09, `SCORE1L` ×3.14, `SCORE10` ×2.61, `SCORE16W` ×3.03.

Nine changes, each measured interleaved and each leaving the survivor
stream bit-identical:

| change | measured |
|--------|----------|
| remainder correction in 32 bits (`r32`) | **1.2935×** |
| + per-prime `uint4`: one 128-bit uniform load, not three loads | **1.4847×** cumulative |
| one conditional subtraction instead of two | **1.1142×** on top |
| ILP unroll `UNROLL = 4` of the divergent tail | **1.2870×** on top |
| 6 sieve primes baked as literals (kill set a `u64` immediate for q < 64) | **1.1119×** at U=4 |
| algebraic split-CRT generation (the A/C tables) | **1.0432×** |
| launch base hoisted out of the per-candidate arithmetic | **1.0839×** cumulative with it |
| shared-memory compaction, JPT = 8 | **1.4911×** |
| constants re-swept after the restructure: LIT 10→6, tpb 256→128 | **1.663× / 1.033×** |

The three worth recognising in another problem:

**32-bit arithmetic under a stated ceiling.** `k − qhat·q` is in `[0, 2q)`
< 2¹⁷ and arithmetic mod 2³² is exact for a value that small, so the
64-bit multiply, subtract and conditional subtractions are all 32-bit for
free. And **one** conditional subtraction is enough, provably: with
`M = floor(2⁶⁴/q)` and `k < 2⁶³` the Barrett error term is under ½, so
`qhat` is `floor(k/q)` or one less. `K_CEIL = 9e18 < 2⁶³ = 9.223e18` is
what makes it true, and the engine now asserts that rather than assuming
it. Worth 1.29× and 1.11× — out of a ceiling that was already written
down and had simply never been *spent*.

**The CRT was arithmetic where it could be algebraic.** Generation computed
`d = (r2 + W2 − r1 % W2) % W2` then `m = (d·INV) % W2` — three
modulo-by-literal sequences and a 64-bit multiply per candidate. But
`m = (r2·INV − r1·INV) mod W2`, and each half depends on one table index
alone, so `A[t] = (−r1·INV) mod W2` goes into the first-level table and
`C[s] = (r2·INV) mod W2` into the second, and the kernel does one add and
one conditional subtract. The `r2` residues stopped being needed on the
device at all.

**Compaction that never leaves the block.** The textbook fix for a 5.2×
divergence tax is a global survivor queue and a second kernel, which drags
in chunked launches, a device buffer budget and a coarser checkpoint. The
cheap form: each thread takes JPT candidates, runs the branchless literal
prefix on all of them, pushes survivors to a **shared-memory** queue, and
after one `__syncthreads` the whole block chews that queue with every lane
alive. A JPT=8, tpb=128 block compacts 1,024 candidates into ~36
survivors — a full warp where an uncompacted warp carried one lane. It
cannot overflow by construction (a block pushes at most one entry per
candidate it owns, and the queue holds exactly JPT·tpb), and the launcher
never learns it exists. **1.4911×**, for no change outside the kernel.

The re-sweep line is Rule 1's corollary biting again, and in the usual
direction — *against* the obvious guess. `LIT = 10` was optimal without
compaction and `LIT = 6` with it (1.663×), because compaction makes the
tail cheap and you want to reach it sooner; `tpb` had been swept to 256 on
the v2 geometry and is 128 on this one.

### Constants, re-swept on the v3 geometry

| LIT (J=8) | 2 | 3 | 4 | 5 | **6** | 8 | 10 | 14 | 18 |
|---|---|---|---|---|---|---|---|---|---|
| | 1.000 | 1.140 | 1.219 | 1.273 | **1.288** | 1.223 | 1.180 | 0.976 | 0.805 |

| JPT (L=6, tpb=128) | 4 | **8** | 12 | 16 |
|---|---|---|---|---|
| | 0.959 | **1.000** | 0.956 | 0.865 |

| tpb (L=6, J=8) | 64 | **128** | 256 | 512 |
|---|---|---|---|---|
| | 0.900 | **1.000** | 0.963 | 0.929 |

| UNROLL (L=6, J=8, tpb=128) | 1 | 2 | 3 | **4** | 6 | 8 |
|---|---|---|---|---|---|---|
| | 1.000 | 1.174 | 1.237 | **1.248** | 1.246 | 1.234 |

`UNROLL` is flat past 4 and `JPT` past 8; both are set at the knee, not at
the peak of the noise.

### Phase split, re-measured on the cheap test body

The v2 split (generation 11%, test loop 89%) was stale the moment the test
body got 2.2× cheaper. Differential ablation — the test loop replaced by a
data-dependent comparison that kills essentially every candidate, so the
atomic traffic and the generation are unchanged and nothing hoists:

| | generation | test loop |
|---|---|---|
| before the algebraic CRT | 68.4 ms — **16.3%** | 83.7% |
| after | 62.2 ms — **15.3%** | 84.7% |

## Priced and REJECTED in v3 — do not retry

- **A test body with no 64-bit multiply at all.** `k mod q = (B mod q +
  r1 mod q + (W1 mod q)·m) mod q` with `B` uniform per launch: two 32-bit
  Barretts instead of one `__umul64hi` plus a 32-bit correction. Measured
  **1.4016×** against the packed `uint4` body's **1.4847×** on the same
  run. The second 32-bit Barrett costs more than the 64-bit multiply-high
  it removes (`__umulhi` is one instruction, but the reduction around it is
  four), and it additionally needs a per-launch `B mod q` table and one
  wheel block per launch. Rejected on the number.
- **Computing the launch base once per block into shared memory.**
  `gridDim.z = 1` is 2.6% faster than `gridDim.z = 4`, and the obvious
  suspect was the per-thread `W·blockIdx.z` multiply. Hoisting it into
  shared memory — free, since the kernel already has a `__syncthreads` —
  measured **0.9707×** against the unhoisted **0.9734×**. The gap is not
  the multiply; it is the z-dimension itself, and it is left unexplained
  and unfixed. `CAND_PER_LAUNCH` sizes `gridDim.z` from the work instead,
  so the production shape gets one wheel block per launch and lands on the
  fast side anyway.
- **`W1` as a `u32` literal** so the widening multiply is 32×32. Measured
  **1.0010×** — nvcc had already narrowed it. Nothing there.
- **JPT = 16 (0.865×), tpb = 512 (0.929×), LIT = 18 (0.976×), LIT = 24
  (0.805×), UNROLL = 8 (0.988× of UNROLL 4).** All swept, all lost.

## Open after v3, in rough order of expected value

1. **A second compaction round.** The warp-test model puts one round at
   1.82× and two at **2.50×** (best split K = 3 then 10); the first round
   measured 1.49× against a predicted 1.7×, so a second is worth pricing
   at perhaps 1.2–1.3×. The shared queue already exists; a second round is
   a few more branchless tests on the queue and a second compaction into
   it.
2. **The (23, 43] wheel — 2.10× modelled, and both published blockers turn
   out to be softer than they looked.** The `gridDim.y` cap does **not**
   need the `(t,s)` flattening the v2 log describes: `R2 = 3,402,000`
   residues can be chunked on the host in slices of 65,535 exactly the way
   the `j` dimension already is, which is a loop and an offset argument.
   The real obstacle is different and was not previously stated: a wheel
   block becomes **1.3×10¹⁶** of k line, and coverage is contiguous in `k`
   only at block boundaries, because candidates come out in `(t, s)` order
   and not in `k` order. A least-`k` claim therefore has to complete the
   block containing the find — and `a(16)`'s modelled median is
   2.18×10¹⁵, well inside the *first* block, so proving `a(16)` would cost
   1.3×10¹⁶ of line instead of 2.2×10¹⁵. Against a 2.10× rate gain that is
   a net **~2.9× loss** on time-to-`a(16)`. Two ways out, both unbuilt:
   **stage the wheel with the frontier** ((23,37] is well matched below
   ~10¹⁷ and (23,43] above it, and the launcher already moves its filter
   as a `[STAGE]`), or **sweep in `k` order** — `x ∈ [m·W1, (m+1)·W1)`, so
   a k-window is an `m`-range, and with the `C` table sorted the
   qualifying `s` for each `t` form one contiguous cyclic run findable by
   binary search. The second is the general fix and would also keep the
   checkpoint fine-grained.
3. **Re-measure the phase split, again.** Generation is 15.3% and rising
   as the test loop keeps getting cheaper; the next round should re-derive
   it before choosing anything — Rule 1's corollary has now moved an
   optimum in this project three times.
4. **Re-sweep `SEG_BLOCKS`.** Set to 2 on the v2 geometry for crash cost,
   against a segment that is now 4× faster.
