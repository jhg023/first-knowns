# OPTIMIZATION_LOG — square-ladders

Every attempt, its measurement, and whether it was kept. The rejections
matter as much as the wins: they are what stops the next person spending a
day re-deriving a dead end. Read [OPTIMIZATION.md](../OPTIMIZATION.md)
first; this file is the project-specific ledger.

> **OPEN ITEM FOR WHOEVER RESUMES THIS PROJECT — before any new
> optimization work.** `Campaign.ladder()` (launch.py) calls
> `model.predictions(...)`, and `check_rungs` calls it once per period,
> `next_rung` again on every rung crossing, and the heartbeat again every
> 30 s. **That call measures 473 ms here.** In `shift-ladders` the
> identical shape, at a much shorter segment, consumed about four fifths of
> a 17-hour campaign and its removal was worth **3.47x** (that project's
> OPTIMIZATION_LOG.md, "The campaign, measured"; OPTIMIZATION.md 2.14; now
> binding in CONVENTIONS.md, "The model is EXPENSIVE, and the segment loop
> may not call it").
>
> This project is probably saved by arithmetic rather than by design -- its
> period is long enough that 473 ms is a small fraction of a segment -- but
> that is a coincidence of `W`, not a property anyone chose, and it would
> not survive a wheel change. **Measure wall clock per unit of line against
> device time per unit of line before resuming**, then swap `ladder()` to
> `huntlib.rungs.LiveLadder` (three lines; the frontier is the first
> argument of `get` by signature, so a rung still retires with its term).
>
> Written from `shift-ladders`. **No code here was touched and this
> project's gates were NOT run** (CLAUDE.md rule 2). Resuming already
> requires `python launch.py --selftest` and `python score.py` first --
> note that huntlib's two ladder gates now ride in `drills.standard()`, so
> the battery's count here will go up by two.

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

---

## v3.1 — the second compaction round. KEPT: 1.21×

Cumulative against v2, interleaved in one run with the fingerprint checked
on every run of both: **4.721×** (per-round 4.580, 4.670, 4.779, 4.790,
4.687, 4.721, 4.742 — v2 1030.4 ms, v3.1 218.3 ms). `SCORE 136,117,250`.

**It measured 0.818× first, and the reason it did is the whole lesson.**
Chewing queue 1 with a branchless block of primes 6..12 and packing the
survivors into a second queue lost 18%, monotonically worse as K2 grew,
with registers climbing 40 → 96. The obvious reading — "the population is
already below a block, so there is nothing left to compact" — was wrong.
Shrinking queue 2 from 1024 entries to 256 turned the same change into
**1.068×**. What the first measurement actually varied was not "one round
versus two" but "8 KB of shared memory versus 16 KB", and at tpb=128 that
is 12 blocks per SM versus 6. The A/B changed two things and attributed
the result to the interesting one.

That reframed queue 1 too. It held JPT·TPB entries so that a block in
which *every* candidate survived the literal prefix would still fit —
1,024 slots for an expected 97. The fix is not a bigger buffer or a
smaller one, it is a different contract: **if the queue is full, run that
candidate's tail on the spot, uncompacted.** Identical arithmetic,
identical answer, no packing. Capacity stops being a correctness bound and
becomes a tuning constant, and the queues are then sized from the
*analytic* survival — an exact product over the primes involved (§2.6) —
plus six standard deviations. Production holds 288 and 96 of a
2,048-candidate block against analytic occupancies of 194 and 47.

Overflow being possible rather than impossible is a claim that has to be
proved, not asserted, because a silently dropped survivor is a silently
lost discovery. **G14 forces the path**: an engine whose queues hold 32
entries takes the fallback for nearly every candidate, and its stream must
be — and is — identical to the properly sized engine's, 2,172 survivors
bit-for-bit.

| step | measured |
|------|----------|
| second round, both queues at worst-case size | **0.818×** |
| same, queue 2 at 256 | 1.068× |
| queue 1 from 1024 → 128 with the safe fallback, one round | 1.016× |
| second round with both queues sized (Q1=256, K2=12, Q2=64) | **1.169×** |
| JPT re-swept: 8 → 16 | 1.045× |
| **all of it, against shipped v3** | **1.209×** |

### Constants, re-swept again on the two-round geometry

| K2 (LIT=6) | 10 | 11 | **12** | 13 | 14 | 16 |
|---|---|---|---|---|---|---|
| | 0.941 | 0.991 | **1.000** | 0.992 | 0.979 | 0.906 |

| JPT (tpb=128) | 4 | 8 | **16** | 24 | 32 |
|---|---|---|---|---|---|
| | 0.880 | 1.000 | **1.045** | 1.056 | 1.045 |

`UNROLL` is flat across 3 / 4 / 6 / 8 (1.210 / 1.209 / 1.207 / 1.215) and
stays at 4. `JPT` = 24 measured 1.1% above 16 and was **not** taken: at
JPT=24 the analytic queue occupancy is 291 against a 6σ cap of 384, which
is 5.7σ of margin where JPT=16 has 14σ, and 1.1% is inside this card's
run-to-run spread. LIT stayed at 6 (LIT=5 and 4 within 1%, LIT=8 at
0.874×).

**One rejection here is worth keeping because it shows the fallback
working.** `JPT=32, tpb=256` measured **0.505×** — a block owning 8,192
candidates with a queue of 448 against an analytic occupancy of 777, so
the overflow path ran for 42% of survivors. The answer was still exactly
right; it was just the uncompacted engine doing nearly half the work. A
capacity that is a tuning constant fails by getting slower, which is the
failure mode worth having.

---

## Measurement 7 — the phase split, a third time

Nested differential ablation on v3.1: four kernels, each a *prefix* of the
real one, so every stage is a difference and nothing downstream changes.
Each truncated variant keeps its queue live (thread 0 folds the last entry
and the count into the output counter) so nvcc cannot delete the writes.

| stage | ms | share | (v3, one round) |
|-------|----|-------|-----------------|
| generation | 58.4 | **27.8%** | 15.3% |
| literal prefix + queue 1 | 89.7 | **42.7%** | — |
| round 2 + queue 2 | 14.1 | 6.7% | — |
| early-exit tail | 48.1 | 22.9% | — |

The split has moved twice now and it moved a *lot*: the phase that was 11%
of v1 and 15% of v3 is 28% of v3.1, purely because everything around it got
cheaper. And the biggest single phase is the literal prefix — six
branchless reductions run on *every* candidate.

## v3.2 — CRT-combine the prefix. KEPT: 1.19×

"Killed by 41 or by 43" is a function of `k mod 1763` alone, so a *group*
of primes costs one reduction and one bitmap lookup instead of one of each
per prime. Six tests become three, against a table of 981 bytes.

Cumulative against v2, interleaved in one run: **5.735×** (per-round 5.691,
4.949, 5.761, 5.715, 5.720, 5.792, 5.771 — v2 1038.1 ms, v3.2 181.0 ms).
`SCORE 162,963,133`.

**This idea is recorded as REJECTED in OPTIMIZATION.md §2.10**, from
euler-prime-runs, and re-reading *why* is what made it worth trying here.
That kernel was bound by load COUNT and already had a 21.5 KB table, so
combining bought one load at the price of a much larger table and measured
0.62× at 86 KB. This kernel is the opposite on both counts: bound by
instruction ISSUE (measurement 5), with a prefix that issues **zero** loads
because each `q < 64` kill set is a 64-bit immediate. Trading ~10
instructions per prime for ~9 instructions plus one load per group is the
right way round here and the wrong way round there. A decline is only as
good as its stated reason, and the reason has to be re-read against the
*current* kernel, not inherited.

The size cliff §2.10 warns about is real, and sharp:

| grouping | table | ratio |
|----------|-------|-------|
| 6 singles (v3.1) | 0 B | 1.000 |
| **3 pairs** (41·43, 47·53, 59·61) | **981 B** | **1.189** |
| 2 triples (41·43·47, 53·59·61) | 33.4 KB | 1.184 |
| triple + 3 singles | 10.1 KB | 1.135 |
| 3 triples (prefix of 9) | 75.8 KB | **0.246** |
| quad + pair (41·43·47·53, 59·61) | 536.5 KB | **0.394** |

Between 33 KB and 76 KB the change inverts — the tables fall out of L1.
`LIT_GROUP_MAX = 8192` bounds a group's *modulus*, which is what keeps them
inside, and it is expressed as a modulus rather than a byte count so that
every configuration the gates run gets a sensible grouping automatically
(the `n=10, q2=4096` shape groups as 17·19·23, 29·31, 37).

`SCORE16W` rose **2.3×** where the others rose ~1.2×: it runs a coarse
wheel and a shallow sieve, so a much larger share of its work is the prefix
this change makes cheap. That is the four-shape benchmark doing its job.

Constants re-swept once more: the prefix stays at 6 primes (4 is 0.944, 5
is 0.964, 7 is 0.969, 8 is 1.138 against 3 pairs' 1.189) and `K2` stays at
12 (10 is 0.958, 14 is 0.994, 16 is 0.922).

### Termination test (OPTIMIZATION.md Part 3.1)

Every phase above 5% of v3.1, with a verdict. This is the table that says
what is *left*, not that nothing is.

| phase | share | verdict |
|-------|-------|---------|
| literal prefix | 42.7% | attacked: CRT-combined 6 primes into 3 tests, **1.19×**, with the table cliff located (inverts between 33 and 76 KB). Depth re-swept and unchanged. Not yet re-split after the change |
| generation | 27.8% | **unsearched since the algebraic CRT (1.043×)**. Now the second-largest phase and the least examined. Its `res1x` table is re-read once per second-level residue — 44 GB per wheel block, ~830 GB/s of L2 — so whether it is issue-bound or bandwidth-bound is not known, and a padding ablation would settle it in five minutes |
| early-exit tail | 22.9% | partly attacked: `UNROLL` swept (flat past 4), reached earlier by the second compaction round. The CRT-combining above has **not** been tried here, and its first few primes are the ones that matter |
| round 2 + queue 2 | 6.7% | attacked: it *is* the second compaction round, 1.21×. `K2` swept both ways around 12. Combining its primes untried |

Nothing here is finished; three of four rows carry a named, unpriced lever.

---

## v3.3 — combine round 2 too, and stop hardcoding the depths. KEPT: 1.13×

Cumulative against v2, interleaved in one run: **6.481×** (per-round 6.243,
6.583, 6.496, 6.487, 6.170, 6.529, 6.465 — v2 1020.6 ms, v3.3 157.5 ms).
`SCORE 184,801,999`.

Round 2 is branchless over primes LIT..K2, which is the same shape the
prefix combining paid 1.19× on, and 67·71, 73·79, 83·89 all fit a budget.
Combining it was **1.06×** — and then moved `K2` from 12 to **16**, worth
another 1.06×, because cheaper tests buy more of them (Rule 1's corollary,
for the sixth time in this project). Two small generation changes came with
it: hoisting the `t < R1` bounds check out of the JPT loop, since it is
false only in the last block of the x grid (**1.007×**), and replacing
`if (m >= W2) m -= W2` with `min(m, m - W2)` on unsigned wraparound.

| change | measured |
|--------|----------|
| bounds-guard hoist | 1.0065× |
| min-subtract (alone) | 0.9947× |
| both | 1.0155× |
| CRT-combined round 2 | 1.0580× |
| all three | 1.0753× |
| + `K2` 12 → 16, round-2 budget 16384 | **1.1128×** on top |

Round-2 budget swept separately from the prefix's: 16384 beats 8192 by
1.06× and 65536 only ties it, so it sits at the knee. `K2` past 16 loses
(18 is 0.997×, 20 is 0.979×, 24 is 0.975×).

**Then it broke two of the four benchmark shapes, and that is the part
worth reading.** `SCORE10` and `SCORE16W` both fell ~22%. The cause was not
the change but the *constants*: `LIT` and `K2` had been swept as **counts**
on the production shape and shipped as counts. But what a sweep of that
kind actually finds is a **survival fraction**, and the fraction is not
transferable as a depth — `w(q,n) = min(n, (q-1)/2)`, so a coarser wheel or
a smaller `n` gives a much steeper survival curve, and testing to a fixed
*depth* there means testing long past the point where anything is left to
kill. Production reaches 1.2% survival at prime 16; `SCORE16W` reaches it
at prime 8.

So the constants became the fractions — `LIT_SURV = 0.095`,
`K2_SURV = 0.012` — and the depths are derived per configuration. On the
production shape that reproduces the swept 6 and 16 exactly; `SCORE1L` gets
(4, 10), `SCORE10` (5, 13), `SCORE16W` (4, 8). Swept directly on a
resolvable window, `SCORE16W`'s true optimum is (4, 10) and the derived
(4, 8) is **0.9984** of it — so the rule is right to within noise, on a
shape it was not tuned on.

**And the 22% was not real either.** Sweeping `SCORE16W` on a *big* window
(4,000,000 blocks, all 20 configurations agreeing on 38,505 survivors)
showed a flat plateau, not a cliff. The 22% came from the benchmark window
itself, which is the next entry.

## The benchmark shape has become the blocker for two of four shapes

OPTIMIZATION.md §2.13, arriving on schedule. The frozen windows are
absolute spans of the k line, and the engine has got 6.5× faster
underneath them:

| shape | window | wall at the v3.3 rate | spread over 5 runs |
|-------|--------|----------------------|--------------------|
| `SCORE` | 2.97×10¹³ | 0.16 s | **1.1%** |
| `SCORE1L` | 2.97×10¹³ | 0.82 s | **0.6%** |
| `SCORE10` | 6.01×10⁹ | ~1.8 ms | **26%** |
| `SCORE16W` | 3.06×10¹⁰ | ~2.3 ms | **13%** |

Two milliseconds is per-launch overhead and a host round-trip, not kernel
time, so those two rows have stopped measuring the engine. It shows up as
`SCORE16W` reading 18.4 / 17.5 / 15.8 / 14.3 / 12.4 across runs of
binaries whose real difference on a resolvable window is under 1%.

**Not changed, deliberately.** Widening those windows moves their frozen
fingerprints, and the anchor that makes scores comparable across engine
generations is not something an optimization pass gets to re-cut (§2.13).
The two shapes still do their more important job perfectly — they are
correctness cross-checks, and their fingerprints have been exact through
every change in v3. What is lost is only their *rate* number. Priced for
whoever decides: ×100 on both windows would put them at ~0.2 s each and
cost about 0.4 s on a `score.py` run, and it is a deliberate re-freeze
with a log entry, not a silent one.

---

## v3.4 — one generation setup, eight candidates. KEPT: 1.13×

Cumulative against v2, interleaved in one run on a 24-block window (six
times the frozen one, because v3 is now fast enough that the frozen window
is short enough for clock ramp to show): **7.505×**, per-round 7.20–7.68
over eight of nine rounds with one 5.375 outlier, both engines agreeing on
the same 1,939 survivors every time. `SCORE ~207,468,780`.

E10 had settled that generation is issue-bound, so the lever is
instructions — and there is a structural one. `k = base + r1 + W1·m` with
`m = A[t] + C[s]`, so for a fixed `t` the quantity `base + r1` **does not
depend on s at all**. Give a block SPB second-level residues instead of
one, hold its `c2` values in registers, and a single `res1x` load, a single
`t` computation, a single bounds check and a single 64-bit add serve SPB
candidates:

    for jj in JPT:
        e1 = res1x[t]                  <- once per SPB candidates
        b0 = base + e1.x               <- once per SPB candidates
        for ss in SPB:
            k = b0 + W1 * min(m, m - W2)   where m = e1.y + c2[ss]

Measured at **constant candidates per thread**, so the block growing is not
doing the work: SPB = 1 / 2 / 4 / 8 / 16 gives 1.000 / 1.040 / 1.046 /
**1.067** / 1.054. Then `tpb` moved back from 128 to **256** — a
restructure of the block moves the block-size optimum, which is Rule 1's
corollary for the seventh time here — and the pair together is **1.126×**
against shipped v3.3 (JPT=4, SPB=8, tpb=256; neighbours 1.049 at tpb=128,
1.010 at tpb=512, 1.069 at SPB=4).

**And then it cost `SCORE1L` 16%, for the same reason the depths did.**
A one-level wheel has no second level, so SPB collapses to 1 — and `JPT=4`
then leaves **four** candidates per thread where production has 32. Swept
directly on that shape, `JPT=4, tpb=256` measured **0.843×** of its own
optimum, which is `JPT=32` — that is, 32 candidates per thread, exactly
what production runs as 4×8. So the shipped constant is `CPT_DEFAULT = 32`
candidates per thread and `JPT = CPT // SPB` follows. This is the third
time in v3 that a constant swept on one shape turned out to be the wrong
*quantity* to carry (compaction depths → survival fractions; queue capacity
→ analytic occupancy; JPT → candidates per thread), and all three were
caught by the same thing: a benchmark with four shapes rather than one.

`tpb` is left at production's 256 even though `SCORE1L` prefers 128 by 7%
at the same candidates-per-thread; there is no principled rule to derive it
from, production is what the hunt runs, and the price is written down here.

## Open after v3.4, in rough order of expected value

0. **The phase split, re-measured on v3.4 — and it has moved again.**
   Nested differential ablation, 24-block window, 1,939 survivors every
   run:

   | phase | v3.1 | v3.4 |
   |-------|------|------|
   | generation | 27.8% | **9.6%** |
   | CRT-combined prefix + queue 1 | 42.7% | **57.6%** |
   | round 2 + queue 2 | 6.7% | 10.3% |
   | early-exit tail | 22.9% | 22.4% |

   The SPB amortisation did to generation exactly what it was built to do
   — 27.8% down to 9.6% — and the prefix is now well over half the kernel.

1. **Reduce the prefix from `(b0 mod Q, m)` instead of from `k`.
   Unmeasured, and the best-looking lever left.** The prefix is three
   CRT-group tests per candidate, each a full 64-bit Barrett reduction of
   `k`. But the SPB restructure already hands the kernel `k` in two
   pieces, `k = b0 + W1·m`, with `b0` fixed for the whole inner loop:

       k mod Q = (b0 mod Q + (W1 mod Q)·m) mod Q

   so `b0 mod Q` can be formed **once per jj**, amortised over SPB
   candidates, leaving one 32-bit multiply-add and one 32-bit Barrett per
   candidate per group. The `__umul64hi` — five or six instructions on its
   own — leaves the inner loop entirely. Exact, because `(W1 mod Q)·m` is
   congruent to `W1·m` mod Q whether or not `m` is reduced, and it fits in
   u32 (`Q ≤ 8192`, `m < W2 = 33263`, so the sum is under 2.8×10⁸); the
   32-bit Barrett then leaves the remainder in `[0, 2Q)`, one conditional
   subtraction, the same theorem one word narrower. Guard needed:
   `Q · W2 < 2^32` must be asserted, since a wider second-level wheel
   would break it. Estimated 1.1–1.2× on a phase worth 57.6%; a harness
   for it is written but was not run.

2. **CRT-combine the tail's first primes.** Unchanged from below — the
   tail is 22.4% and the same trick has paid twice already.
3. **The tail's group table, in detail.** Its per-prime data is a runtime
   table rather than literals, so combining needs a group table for the
   first few tail primes and a fall-through to the plain loop. Only the
   first few matter, because of the early exit.

4. **A third compaction round is probably closed, and unmeasured.** After
   round 2 the block holds ~47 survivors against 128 threads, so a third
   round has fewer items than the block has lanes and cannot fill a warp
   that is not already full — §2.2's "rare-and-deep stages are already
   optimal", one level up. That is an argument, not a measurement, and it
   should be priced before it is believed: the same argument was made
   about round 2 and was wrong, for reasons that turned out to be about
   shared memory rather than about populations.
5. **The (23, 43] wheel — 2.10× modelled, and both published blockers turn
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
6. **(Superseded by item 0.)** It was 15.3% generation / 84.7%
   test loop on the one-round v3, and the test loop has since got another
   1.21× cheaper, so generation is now the larger share it has ever been.
   The next round should re-derive it before choosing anything — Rule 1's
   corollary has now moved an optimum in this project **five** times
   (sieve depth, LIT twice, tpb, JPT), and three of those moves were in
   the direction opposite to the obvious guess.
7. **`SEG_BLOCKS` — re-swept, and done for now.** Flat from 1 to 16 blocks
   on v3 (0.4% across a 16× range), so still not a throughput knob. Set to
   8 to hold the SEGMENT DURATION near half a second, which is what the
   crash cost and the `--gpu-yield-ms` price are both denominated in. It
   will need revisiting the next time the engine gets materially faster:
   at v3.1's rate the segment is 0.44 s, so a 20 ms yield is 4.6% rather
   than the 3.9% it was when the constant was chosen.

---

## v4 — (k, off): the ceiling stops being a machine word, 2026-08-22

`SCORE 203,738,256`, 25 gates green (G15 is new).

**This is not a speedup and was never going to be.** It is the entry that
OPTIMIZATION.md 2.7 exists to force, arrived at the way that section says
it usually is — too late, with a campaign already parked against the wall.

### What went wrong, stated plainly

v3.4 carried the absolute `k` in a u64 and reduced *it*. The
one-conditional-subtraction Barrett theorem needs the reduced quantity
under `2⁶³`, so the engine enforced `K_CEIL = 9×10¹⁸` — and that number
was a **machine word wearing the costume of a mathematical bound**. The
docstring, the gate and the ceiling drill all faithfully enforced it; none
of them asked whether it was the right quantity to bound. It is exactly the
mistake 2.7 describes, and this project made it after that section was
written.

The bill came due when the a(16)/a(17) campaign stopped at
`k = 7.246×10¹⁸` with `a(18)` still open. Priced against the live odds
model, conditioned on `a(18) > 7.246×10¹⁸`:

| reachable ceiling | needs | P(find a(18)) |
|---|---|---|
| `9×10¹⁸` (v3.4, as shipped) | nothing | **19.1%** |
| `2⁶³ = 9.223×10¹⁸` | a one-line constant edit | 21.1% |
| `2⁶⁴ = 1.845×10¹⁹` | two-subtract Barrett, a real engine change | 68.5% |
| `1.02×10²²` (v4) | the (k, off) representation | **~100%** |

The middle row is the trap. `a(18)`'s modelled **Q3 is 2.11×10¹⁹ — already
past 2⁶⁴**, so no choice of machine word is enough, and an engine built to
reach `2⁶⁴` would have been a second engine at the word boundary that then
needed a third. Priced and **REJECTED** for exactly that reason.

### The mechanism, and why it is free

`k = base + off`: `base` is the launch's absolute floor, a Python int on
the host that never reaches the device; `off < W·per_launch` is what the
kernel reduces. Since `k mod q = (off + base) mod q`, the base contribution
is folded **once per launch** into the two things each test already reads,
never added per candidate:

* per prime, the bitmap stores the killed pattern **twice** (2q bits) and
  the uint4's `boff` slot carries `2q-block base + base mod q`; because
  `off mod q < q`, the sum indexes the right copy with no reduction;
* per CRT group, the base arrives as a kernel **scalar parameter** — a
  rotated u64 mask for an inline group, a shifted table index for a table
  group. The constant bank, not a load.

So the issue-bound test loop issues **exactly what v3.4 issued**. That was
the design constraint: this kernel is bound by instruction ISSUE (v3's
finding, worth 6.5×), so a representation costing even one instruction per
test would have shown up as several percent.

**Measured, interleaved, twelve rounds alternating which engine goes
first, fingerprint `303/999990048677220` checked on every run of both:**
v3.4 median 140.7 ms, v4 143.2 ms — **0.982×, a 1.8% fee.** It is not
zero because the doubled bitmap is 50.6 MB against 25.3 MB and the L2 feels
it. 1.8% of throughput for 1,138× of reachable range.

The `2⁶³` bound did not disappear, it moved onto a quantity the engine
CHOOSES rather than one the mathematics hands it: `W·per_launch + q2 <
REDUCE_MAX`, with `per_launch` halved until it holds. A ceiling on the
wheel and the batching is a ceiling one can always pay off.

### What the ceiling is now

`k_ceil(n) = (MR_VALID_BELOW - 2) // n² + 1` — the **primality-proof
validity bound and nothing else**, which is what 2.7 says to pick. At
n = 18 that is `1.024×10²²`. G10 was rewritten to pin both halves per n:
the largest sweepable `k` still proves, and one more `k` would not. A
ceiling derived by formula fails by one or not at all, and the first
version of this change was indeed off by one (an inclusive/exclusive slip
caught by G10 at n = 1).

### Things worth not re-deriving

* **Doubling the CRT group tables is free; doubling the main bitmap is
  not.** The group tables are 1–2 KB and the L1 cliff LIT_GROUP_MAX guards
  is at ~76 KB with the sweep still flat at 33 KB, so there was no need to
  halve LIT_GROUP_MAX to pay for the second copy — that was considered and
  is unnecessary. The 25.3 → 50.6 MB main bitmap is where the whole 1.8%
  lives.
* **Rotating the group tables on the host per launch instead of passing
  scalars** was costed and **REJECTED**: a bit-level roll of ~1.8 MB per
  launch at ~28 launches/s lands in the same millisecond range as the
  launch itself, against zero for a scalar parameter.
* **Loading `base mod q` as a separate u32 array** and adding it in `TEST`
  was **REJECTED**: it puts a load and an add back into the hot loop that
  v3 spent 6.5× removing. The doubled bitmap buys the same result with
  memory, which is the resource this kernel is not short of.
* `base mod q` is computed as `(W mod q)·(j mod q) mod q`, vectorised over
  6,542 primes — both factors under 2¹⁶, so the product is exact in u64
  **for any j whatsoever**. Not `(W·j) mod q`, which overflows on a narrow
  wheel at large j.
* The checkpoint **migrates** rather than restarting: v4 covers the same
  line as v3.4 by the same wheel and sieve depth, and the four frozen
  fingerprints plus G9/G15 pin the stream as identical, so the a(16)/a(17)
  cursor carries over. `huntlib.checkpoint.load` grew an `accept` list for
  this, and it warns on every migration. A change to the WHEEL or the
  SIEVE DEPTH must never be listed there — those move coverage.

---

## v5 — the wheel reaches 47. KEPT: 4.31x end to end, 2026-08-22

`SCORE3L 1,212,461,925` (the production configuration, new shape),
`SCORE 261,712,890`, 27 gates green (G16 is new).

Measured against the committed v4 engine, both loaded in one process,
interleaved, nine paired rounds at the live cursor, with the ratio taken
INSIDE each round:

| | v4 | v5 | |
|---|---|---|---|
| device only | 2.67e14 k/s | 1.21e15 k/s | **4.514x** |
| end to end, classification in both | 2.63e14 k/s | 1.13e15 k/s | **4.306x** |

Per-round ratios 4.16–4.38, so the spread is a few percent and not the
30% ambient swing that makes sequential sweeps lie.

### Measurement 8 — where the tests actually are (do this before anything)

The whole entry follows from one identity. Let
`S(q) = prod_{q' < q} (1 - w(q')/q')` be the fraction of the k line that
reaches prime q. Then the density of candidates after a wheel to `p2` is
`S(next prime after p2)`, and the survival from there to q telescopes, so

    TESTS PER UNIT OF K LINE  =  sum over primes q > p2 of S(q).

Two things fall straight out of it. The value of putting a prime **into**
the wheel is exactly its own term `S(p)` — not a modelled ratio, a
subtraction. And the terms are enormously front-loaded. At n = 18 with the
v4 wheel (23, 37]:

| primes | tests/line | share |
|--------|-----------|-------|
| 41..47 | 1.262e-3 | **72.15%** |
| 53..61 | 2.853e-4 | 16.30% |
| 67..97 | 1.504e-4 | 8.59% |
| 101..199 | 4.45e-5 | 2.54% |
| 211..65536 | 7.1e-6 | 0.42% |

**Three primes were 72% of every test the engine did**, and the engine
stopped one short of them. Everything below is a consequence.

### v5a — the third wheel level. KEPT: 3.51x

41, 43 and 47 were out of the wheel for one reason: their residues do not
fit in a table. `(23, 47]` is 76,038,000 of them, and the engine's
second-level table is indexed by `gridDim.y`.

CRT lifting is linear, so the second level can be **factored again**:

    r2 = EA*r2a + EB*r2b (mod W2),   EA = W2b*(W2b^-1 mod W2a),  etc.

so `C[s] = r2a*KA mod W2` and `D[u] = r2b*KB mod W2` with `KA = EA*inv`,
`KB = EB*inv`, and a candidate is `m = (A[t] + C[s] + D[u]) mod W2` out of
two tables of **4,560 and 16,675** instead of one of 76 million. The
third-level residue rides `gridDim.z` beside the wheel-period index
(`z = period*NU + u`), the block combines its own `C + D` once, and **the
inner loop is byte-for-byte what v4 issued**. 8.28e13 candidates per period
from 8.8 MB of tables -- the same residues as a plain sorted list would
be 662 TB, and that compression is also exactly why candidates do not come
out in k order (see "What it costs").

**47 is the last prime, and not by choice.** `m` is a u32, so the combined
second modulus must stay under 2^32: primes to 47 make it 2.756e9, primes
to 53 make it 1.46e11. Widening `m` does not help either — `W1*m` is the
quantity the one-conditional-subtraction reduction bounds, so `W < 2^63`,
and the product of the primes to 53 is 3.26e19. No arrangement of levels
moves either bound, because both are functions of the PRIME SET and not of
the split. Dropping small primes to buy 53 was priced and loses: the wheel
wants its smallest primes most. G13 asserts the u32 bound rather than
documenting it.

Density 6.69e-4 -> 1.346e-4 candidates per k, and 72% of the tests gone.

### What it costs, and why it is worth it anyway

A wheel period is now **6.15e17 of k line** and about ten minutes, and
candidates come out in `(t, s, u)` order rather than in k order, so **only
a whole period is contiguous in k**. The launcher therefore tracks two
cursors, and they are two different claims:

* `boundary` — the k below which the line is swept. Moves one period at a
  time. A discovery is only the LEAST k once its period closes, so finds
  are held (in the CHECKPOINT, so a crash in that window does not lose
  them) and narrated in k order at the period end.
* `(j, u)` — resumable per launch. A crash costs one checkpoint interval,
  which is what rule 5d asks for, not one period.

The over-sweep at a find is at most one period: ten minutes against a
wheel worth 3.5x. The v2 log rejected this wheel for exactly this reason
and was right at the time — `a(16)`'s modelled median sat inside the FIRST
block, so proving it would have cost 1.3e16 of line instead of 2.2e15. At
the a(18) frontier the same 6.15e17 is 0.13% of the remaining hunt. The
blocker did not get solved; it got outgrown, and that is worth writing down
because the same rejection will look wrong again at the next frontier.

### v5b — the constants, re-swept on the new wheel. KEPT: 1.12x

Rule 1's corollary for the eighth time in this project, and one of these
was not a re-sweep but a re-READ:

* **`LIT_GROUP_MAX` 8192 -> 2^18. 1.11x on the two-level wheel, 1.08x on
  the three-level one.** The v3 sweep recorded "1.19x at 1 KB and 1.18x at
  33 KB, so the win is flat" and shipped 1 KB. Those two points **compile
  to the same grouping**: a third prime in a group needs a modulus of
  82,861, so both budgets produced pairs and the sweep measured one binary
  twice. It was never flat; it was never tested. On the wheels this engine
  runs the budget really does change the grouping — three primes per group,
  one fewer lookup on EVERY candidate.
* `LIT_SURV` 0.095 -> **0.11**, which lands on 5 primes on the two-level
  wheel and 7 on the three-level one. Neighbours 0.94x and 0.93x.
* `K2_SURV` 0.012 -> **0.0057** (19 primes -> 25). The direction is the
  interesting part and it only makes sense after v5d: a CHEAPER tail wants
  MORE compaction in front of it, because what round 2 now saves is not
  divergent block work but entries written to and read back from a global
  queue.
* `K2_GROUP_MAX` 2^14 -> 2^16 (1.04x). `tpb` 256, `cpt` 32, `spb` 8,
  `UNROLL` 4, tail grid — all re-swept, all unmoved (UNROLL and the tail
  grid measured flat to 0.2% across 8x ranges).

### v5c — the prefix reduction, hoisted out of the inner loop. KEPT: 1.04x

E11 (below) said 71% of the prefix was arithmetic and 29% lookups, so the
target was the 64-bit multiply-high. A candidate is `off = b0 + W1*m` with
`m = A - D` (plus W2 when that borrows), b0 and A fixed for a whole inner
loop and D fixed for the whole block, so

    off mod Q = ((b0 + W1*A) mod Q - (W1*D) mod Q [+ W mod Q]) mod Q

and every 64-bit reduction leaves the per-candidate path: one per block per
group, one per first-level residue, each amortised over SPB candidates.
What is left is a select between two precomputed values (the borrow picks
which), a subtract and a conditional add — three 32-bit instructions where
v4 issued `__umul64hi` and its correction.

**It is worth 1.04x, and getting there taught more than the number.** The
first version measured **0.98x** and the register count did not move: nvcc
had answered by REMATERIALISING the precomputed values back into the loop
rather than spending registers on them. Told to hold them
(`__launch_bounds__`), it used 72 registers, dropped from five resident
blocks per SM to three, and measured **0.79x**. The values only pay from
SHARED memory, where they cost no registers at all.

That is the finding: **this kernel is bound by OCCUPANCY, not by
instruction issue.** v3 measured issue-bound and was right then; six
structural changes later it is not, and every collapse in this round traces
to the same budget — an SM divides 128 KB between shared and L1, the
resident blocks take their cut of it FIRST, and the group tables have to
live in what is left. 0.29x at a shallower compaction point (queues grew),
0.36x at cpt 64 and 0.29x at cpt 128 (queues grew), 0.33x at wider groups
(tables grew). One budget, three faces.

Since the base now folds into the per-residue value, a hoisted group's
table no longer needs the second copy v4 gives everything else
(`HOIST_TABLE_REPS`). Measured 1.000x on its own — 69 KB was already inside
L1 — but it halves the tables and it is what would buy room if the cliff
ever moved.

### v5d — the queues hold an INDEX, and the tail is its own kernel

**Queues: 1.02x.** A candidate's identity inside a block is `(jj, ss,
threadIdx.x)`, which is 13 bits where its offset is 60. The queues are 87%
of this kernel's shared memory and shared memory is the resource it is
short of, so they store the index and `off_of` runs the generator's
arithmetic backwards to rebuild the candidate. 9.5 KB per block -> 2.4 KB.

**Tail: 1.06x.** Round 2 leaves about 1.2% of a block's candidates — ~98
against 256 threads — so five warps in eight idled while the block waited
on the single deepest early-exit chain among the survivors. Measured, that
was **32% of the kernel for 4% of its lookups**. The survivors now go to a
GLOBAL queue (one atomic per block, not per item — `qn2` is already the
count) and a second kernel sweeps it with one item per lane and the whole
device in flight. Capacity is sized from the analytic survival and overflow
is harmless in the usual way: the block runs that candidate's tail on the
spot. G16 forces it.

### v5e — the launch flush. KEPT: 1.08x end to end

The host classifies survivors and at the v5 rate that is 2.6 ms against a
32 ms launch — 8% of a core, and it was costing 7.1% of the RATE because it
ran while the device was idle. The engine already enqueued the next launch
before handing back the previous one's survivors, and it made no
difference: `next()` took the same 30.5 ms whether the host had just done
3 ms of work or none.

**On WDDM a launch is asynchronous but BATCHED.** The driver holds it in a
user-mode command buffer until something forces a submit, so the device did
not start until the host next blocked. Isolated on a 19 ms kernel: spin
9.5 ms on the host, then synchronise, and the synchronise still takes
19.0 ms — with a stream query after the launch it takes 9.3 ms. One
`cudaStreamQuery` per launch, microseconds, and classification went from
7.1% of the rate to **0.0%** (paired, nine rounds).

This is why the hunt still has no worker pool. The share was 2% at the v4
rate and would have grown with the engine; instead the work moved off the
critical path, which asks the machine for nothing.

---

## Measurement E11 — inside the prefix: arithmetic or lookups?

With round 2, the tail and the queue push removed so `kill` feeds nothing,
three builds differing only in the prefix, on the production shape:

| | median | delta |
|---|---|---|
| generation only | 0.0601 s | |
| + the reduction, no table lookup | 0.2679 s | +0.208 (69 ms/group) |
| + the lookup (the real prefix) | 0.3510 s | +0.083 (28 ms/group) |

**71% arithmetic, 29% lookups.** That is what pointed at v5c, and it is
also what rules OUT the obvious alternative: if the lookups were the wall,
halving them would pay even at the cost of divergence, and it does not
(see the rejects).

## Measurement E12 — the phase split, re-measured twice

Nested differential ablation, production shape, warmed under load:

| phase | v4 | v5 |
|-------|----|----|
| generation | 10.9% | 8.6% |
| prefix | 53.0% | **40.7%** |
| queue 1 | 10.6% | 10.2% |
| round 2 | 11.4% | 21.2% |
| tail | 14.1% | 19.3% |

Round 2 grew because `K2_SURV` moved it 6 primes deeper, which is a trade
it wins. The tail's share is now mostly the second kernel (10.7% of the
total on its own), not idle lanes.

## Priced and REJECTED in v5 — do not retry

* **Warp-aggregated queue pushes. 0.887x.** One shared atomic per warp
  instead of one per surviving candidate (ballot / popcount / shuffle),
  the textbook fix for a sparse push. It is 1.128x SLOWER here, and it
  even lowered the register count (72 -> 44) while losing. Same-address
  shared atomics are already aggregated in the LSU; the ballot and the
  forced convergence cost more than they save.
* **Early exit between prefix groups. 0.906x.** Guarding groups 2 and 3
  with `if (!kill)` would cut lookups per candidate from 3.0 to 1.45. The
  divergence costs more, and nvcc predicates the guard rather than
  branching, so the load issues anyway. v3's branchless prefix stands.
* **Persistent LANES in the tail kernel. 0.95x.** Each lane holding a
  POSITION rather than a loop, so a dead candidate is replaced without
  waiting for its neighbours — the standard cure for exactly the
  divergence this phase has. It costs the UNROLL independent Barrett
  chains that hide the loop's load latency, and that is worth more.
* **Wider CRT groups (6 primes in 2 groups, 67 KB of tables). 0.33x.**
  The L1 budget above. Halving the tables first (`HOIST_TABLE_REPS`) did
  not buy enough room.
* **Bigger blocks: cpt 64 -> 0.92x, cpt 128 -> 0.90x, tpb 512 -> 0.85x.**
  Even after the index queue cut shared memory 3.8x, which is what had
  made them 0.36x before. The tail queue would fill better; it does not
  pay for the occupancy.
* **`__launch_bounds__` to buy registers for the hoisted prefix.**
  0.82x at 4 blocks/SM, 0.79x at 3, and forcing 5 or 6 spills to local.
  nvcc's own choice is the best of them.
* **The L1/shared carveout preference.** Measured 1.08x once, on a run
  where the device was contended and running at a third of its normal
  rate, and 1.00x every time on an idle one. Not shipped. Recorded because
  the first measurement had a 0.6% spread across nine rounds and looked
  entirely solid — a paired ratio protects against drift WITHIN a run, not
  against a run taken in a different regime (rule 3, again).
* **Sieve depth 32768 instead of 65536. 1.026x for 3x the host load** and
  a re-freeze of every fingerprint. Depth is still nearly free; the deep
  primes are 0.42% of the tests.
* **A host worker pool.** Would recover the 7.1% the flush recovered for
  nothing, and would ask for cores. Superseded, not merely declined.

## Open after v5, in rough order of expected value

0. **Nothing on this list is worth more than about 1.1x, and that is the
   finding.** The wheel is capped at 47 by arithmetic, so candidates per
   unit of k line is FIXED at 1.346e-4; the prefix that every one of them
   pays is three group tests that cannot be merged (L1) or skipped
   (divergence); and the device is measured **99.9% busy** across a sweep,
   so there is no gap to reclaim either.

   The prefix is also at its INFORMATION floor, which is the part worth
   stating. Its three CRT-combined lookups cover seven primes, and an
   early-exit test of those same seven would need
   `1 + 0.66 + 0.46 + ... = 2.9` tests on average. Three branchless
   lookups against a floor of 2.9: the grouping has already bought back
   everything the divergence tax would have cost, and there is nothing
   between the engine and the arithmetic any more.

   What a further 2x needs is a different enumeration, and item 3 prices
   it honestly rather than optimistically.

1. **Overlap the tail kernel with the next launch** — two streams and a
   double-buffered global queue. Bounded above by the tail kernel's whole
   cost, 10.7%, and probably far below it: the sieve kernel already
   saturates the SMs, so concurrency only fills gaps rather than creating
   capacity. Costs 224 MB more and a synchronisation dance. Unmeasured.
2. **Round 2 cannot be hoisted, and this is why.** The hoisted form needs
   `(b0 + W1*A) mod Q` for the candidate's OWN `(thread, jj)`, and round 2
   is read by a different thread than the one that queued it — so it would
   have to do the same 64-bit reduction it was trying to avoid. Storing
   the residues per (thread, jj, group) is 256*4*9*2 values. Closed.
3. **Past 47 needs a different engine — a k-WINDOWED sweep — and it is
   worth much less than its throughput suggests.** The wheel is capped
   because `off` spans a whole wheel period. If a launch covered a
   contiguous k window instead, `off` would be bounded by the WINDOW, and
   the wheel could grow to 61 or beyond: 3.09x fewer candidates and 2.41x
   fewer tests per unit of line.

   It is buildable. For each `(t, s, u)` the qualifying residues of the
   last level form one contiguous run in a sorted table (their k values
   INCREASE along it), so it is a binary search per triple, inside the
   kernel because the results are far too large to store. The levels stay
   small — 4,560 / 16,675 / 61,705 to reach 61.

   **The reason it is not the answer is the window, and this is the number
   to remember.** The search is amortised over the candidates a triple
   yields, which is `window x density / triples`, so a big window is needed
   to make it cheap: at 61 the break-even is a window near `1e19`, where a
   triple yields ~5-10 candidates and the search costs ~1.7 probes each.
   But **candidates still come out in index order inside the window**, so
   the window IS the coverage granularity — and `1e19` is 2.3 hours of
   over-sweep at a find where v5's whole period is ten minutes. Shrinking
   the window to fix that puts the search cost straight back: at `1e18` a
   triple yields half a candidate and the binary search alone doubles the
   per-candidate cost.

   Priced against time-to-discovery rather than throughput, at the a(18)
   frontier: about **1.75x**, not 3x — a rate 3x higher minus half a
   window of over-sweep. Against a full engine rewrite, a dynamic-grid
   load-balancing problem, and a new gate suite for the one property this
   project cannot get wrong. **Priced and NOT started**; the right moment
   for it is a frontier where the target is many windows away, not one.

4. **`CKPT_LAUNCHES` holds the half-second interval** and will need
   raising the next time the engine gets materially faster, for the reason
   the old `SEG_BLOCKS` comment gives.
5. **SCORE1L pays 12% for machinery production gains from** — the split
   tail costs it 3.9% and the index queue 1.3%, measured on that shape
   directly. Its launches are 6 ms where production's are 32 ms, so the
   tail kernel's fixed cost lands five times harder. Kept anyway:
   production is what the hunt runs, and the price is written here. Its
   more important job, returning SCORE's fingerprint from different
   arithmetic, is untouched.
