# OPTIMIZATION_LOG — shift-ladders

Every attempt: the change, the measurement, kept or rejected. Failures
included — they are the record that stops the next person retrying them.
Read [OPTIMIZATION.md](../OPTIMIZATION.md) first; its rules are binding
here, and two of them shaped this engine before a line of it was written.

## v1 — the first engine (2026-08-23)

**What it is.** A flat residue table for the primes up to `p1`, built by
CRT lifting; one thread per candidate; a Barrett magic-multiply reduction
and one bitmap lookup per remaining prime, bailing out at the first kill.
Candidates carried as `(m, off)` with the base folded per prime on the
host. Correctness first: five gates and drills of its own, a bit-for-bit
parity gate against the CPU engine on six populated windows, and five
frozen benchmark fingerprints.

**Two OPTIMIZATION.md rules were applied at design time, not after:**

- **2.7, carry `(m, off)`.** No machine word bounds this search from the
  first commit. square-ladders retrofitted this and its second ceiling
  raise cost a campaign stretch; here the enforced ceiling has never been
  anything but the primality-proof bound.
- **Choose the wheel that fits at every parameter the battery runs.** `p1`
  is per base (23 at b = 4, 37 at b = 2) because the two wheels differ in
  density by 3,000×, and the flat table's size limit is enforced
  (`RES_MAX`) rather than discovered.

### Measured during the v1 build

**1. The per-launch base fold: 6,533 big-int divisions → one numpy step.
KEPT.** Measured directly: **0.357 ms per launch** against **0.034 ms** for
the numpy step form — 10.5×. 0.357 ms is 13% of a production launch and
**99.5%** of a coarse-wheel one.

**2. Launch size: fixed 64 periods → sized from the wheel. KEPT, and
re-swept.** Both families plateau at about **2²⁹ candidates per launch**.
Worth 1.15× at base 4 and 1.43× at base 2 against the fixed 64.

**A rule was broken and then repaired.** Changes 1 and 2 were first made in
a single edit and measured together — the "an A/B that varies two things
credits the interesting one" failure. They were then separated.

**3. Absolute rates swing 30-50% run to run; ratios do not.** The same
production shape measured 3.5 to 6.4 ×10¹² m/s across one session.
**No A/B on this project may be read off two separate `score.py` runs.**

---

## v2 — the bit-plane wheel and a compacted test loop (2026-08-23)

**End to end, interleaved and paired against v1, fingerprint checked on
every run, median of seven per-round ratios:**

| shape | v1 | v2 | ratio | [min, max] |
|---|---|---|---|---|
| `SCORE` (b = 4 production) | 445.1 ms | 5.37 ms | **82.9×** | [69.6, 98.5] |
| `SCORE1L` | 1905.6 ms | 40.87 ms | **46.6×** | [42.7, 52.6] |
| `SCORE2` (b = 2 production) | 532.6 ms | 10.84 ms | **49.1×** | [46.1, 54.3] |
| `SCORE4W` | 306.9 ms | 5.20 ms | **58.4×** | [35.1, 63.9] |
| `SCORE10` | 141.6 ms | 19.60 ms | **7.2×** | [6.5, 7.7] |

**`SCORE` sustained, over a multi-launch span at the launch size a campaign
actually runs, is 3.03×10⁸** against 3.40×10⁸ on the frozen window — about
74× rather than 83×. The two differ for one reason and it is worth naming
up front: **the frozen window is 8,192 periods, which is a QUARTER of one
production launch**, so anything sized from `per_launch` is under-exercised
by it. That cost this session a wrong conclusion, below.

**Every frozen fingerprint is reproduced unchanged**, which is the whole
reason a wheel change is a safe change: folding a prime into the wheel
removes candidates and never survivors, so the frozen count and xor still
apply and say so (OPTIMIZATION.md 2.8).

### Round 0 — measure the split before touching anything (Rule 1)

Differential ablation on the v1 kernel: every variant runs the same
data-dependent tests with the survivor store made unreachable-but-not-
foldable, so downstream work is identical across variants and only the loop
moves.

| shape | generation | per test | effective early-exit depth | lane mean | tax |
|---|---|---|---|---|---|
| `SCORE` | 1.270 ms = **7.7%** | 1.091 ms/depth | **13.96** | 2.78 | **5.02×** |
| `SCORE2` | 1.462 ms = **6.2%** | 1.077 ms/depth | **20.66** | 3.02 | **6.84×** |

So v1 was 92% test loop, and five sixths of that was a warp waiting on its
own deepest lane. Two levers, and they multiply.

### Round 0b — what one test costs (Rule 3.3, priced before building)

Branchless at a fixed depth so the instruction mix is identical and only
the spelling of one test changes:

| variant | ps per candidate-test | ratio |
|---|---|---|
| v1: separate `pq`/`magic`/`bmoff` arrays, 64-bit remainder, two conditional subtractions | 2.184 | 1.000 |
| one `uint4`, 32-bit remainder, ONE conditional subtraction, base folded into a DOUBLED bitmap | **1.054** | **2.07×** |
| the same with four independent Barrett chains | 1.076 | 2.03× |

The third row is the useful negative: `UNROLL` buys nothing where there is
no early exit to hide, which is why it survives only inside the tail loops.

### The change: the wheel became a bit plane over the period index

`m = j*W + r` is killed by `q` exactly when

    (j + Binv_q * r) mod q  in  Binv_q * K(q),     Binv_q = W^-1 mod q

which — once `r` is fixed — is a condition on **`j` alone**, periodic with
period `q`. So a group of primes above the flat wheel has a fixed
surviving-`j` set mod their product, held as a bit plane, and **one 32-bit
load plus one `and` filters thirty-two consecutive periods**. That is
OPTIMIZATION.md 2.1 applied to the *wheel* rather than to the sieve.

Two properties make it the right shape for this problem specifically:

- The shift is **additive**, so the killed set for every residue is a
  translate of one fixed set. `cr` — one u32 per residue per group — is the
  entire per-residue state, and the launch base folds into one more scalar
  per group.
- **`W` does not change.** The plane primes never enter the modulus, so
  `sweep(j0, j1)` still means `[j0*W, j1*W)`, coverage still advances every
  launch, the checkpoint's period unit is the one v1 stored (hence
  `INHERITS`, not `REDENOMINATE`), and the frozen windows are the same
  windows. **The factored multi-level wheel v1 planned instead would have
  multiplied `W` by 2.8e9** — a period of 6.1e17 against an `a(19)` median
  of 5.75e16, so the coverage claim would have advanced in steps ten times
  wider than the entire hunt. That plan is superseded, and the reason is
  worth keeping: the priced-14× item in v1's log was priced against the
  wrong constraint.

### Measured, in the order they were taken

Every row is interleaved and paired, fingerprint re-checked on every run.
Where a ratio is quoted per shape the order is SCORE / SCORE2 / SCORE4W /
SCORE10.

| # | change | measured | verdict |
|---|---|---|---|
| 1 | bit-plane wheel + one compaction round + the packed test, against v1 | 11.2 / 2.8 / 22.7 / 2.4 | **KEPT** (first cut) |
| 2 | adaptive block tile: split `TPB*WPT` work items as `rpb × wact` so a short launch spreads over residues instead of masking off threads | SCORE2 47.2 → 29.1 ms | **KEPT** |
| 3 | compaction rounds cut from the SURVIVAL CURVE instead of two fixed depths | 1.16 / 1.12 / 1.18 / 1.36 | **KEPT** |
| 4 | plane budget 2²⁰ → **2²⁶** bits (merges 29..43 into one plane) | best or within noise on both production shapes | **KEPT** |
| 5 | `p2` DERIVED from a cost model per configuration | picks 79 / 113 / 47 / 101 — all inside the measured plateaus | **KEPT** |
| 6 | block work items `TPB*WPT`: 256 → **1024** | 1.54 / 1.29 / 1.64 / 1.18 | **KEPT** |
| 7 | the tail in its own kernel over a global queue | 1.078 / 1.315 / 0.974 / 1.073 | **KEPT** |
| 8 | hand over to that tail earlier (`tail_surv` 0.03 → **0.10**) | 1.070 / 1.082 / 1.072 / 1.087 | **KEPT** |
| 9 | the tail kernel runs a compaction chain of its OWN (`tail2_surv` = 0.01) | 1.203 / 1.012 / 0.984 / 1.151 | **KEPT** |
| 10 | vectorise the per-launch base fold: `(lo·W) mod Q = ((W mod Q)·(lo mod Q)) mod Q` | **1.93×** on SCORE (9.95 → 5.16 ms) | **KEPT** |
| 11 | global tail queue ceiling 2²³ → **2²⁶** | 1.19× at production launch size | **KEPT** — and see the correction below |

Row 8 and row 9 are the same fact from two sides, and it is the one worth
carrying to another project: **compaction pays where the block is full and
costs where it is not.** A sieve block that has whittled itself to a
percent of its candidates has more idle warps than working ones, so the
deep rounds belong in the tail kernel, whose blocks are always full.

Row 10 is the biggest single factor in this session after the wheel itself,
and it is embarrassing in the useful way: v1's log had already identified
the base fold as a fixed cost and already fixed it *once*, by computing it
in full per SWEEP and stepping it per launch. What nobody re-measured is
that at v2's speed the remaining per-sweep fold — 6,519 Python big-int
divisions — is **4.4 ms against a 5.5 ms launch, 44% of the wall clock of
the frozen SCORE window.** Writing it as `((W mod Q)·(lo mod Q)) mod Q`,
exact in u64 for any `lo` because both factors are under 2³², makes it one
vectorised numpy step and removes the per-sweep cost entirely (measured
residual: 0.12 ms). Rule 1's corollary, third time in this repo.

### The correction: I got the tail queue wrong, and the benchmark is why

Row 11 replaces an earlier verdict in this same session, and the mistake is
worth more than the fix.

Swept **on the frozen windows**, every tail-queue capacity from 2²³ up
measured identical, and 2²³ measured *better* (1.073 / 1.000 / 0.968). I
took that as a Rule 7 result — same throughput, less machine — and shipped
2²³, handing back 190 MiB.

It was wrong. The queue is sized from `per_launch`, and `SCORE`'s window is
**a quarter of one production launch**, so on the benchmark the queue is
never more than a quarter full and *no* capacity in that range can bind.
Re-measured on a span several real launches wide:

| per_launch | q3cap | need | rate |
|---|---|---|---|
| 32,768 | 2²³ (8.4e6) | 3.2e7 | 2.72×10⁸ |
| 32,768 | 2²⁶ (6.7e7) | 3.2e7 | **3.03×10⁸** |
| 16,384 | 2²⁶ | 1.6e7 | 3.09×10⁸ |
| 8,192 | 2²⁶ | 8.0e6 | 1.22×10⁸ |
| 4,096 | 2²³ | 4.0e6 | 0.67×10⁸ |

So at the launch size a campaign runs, 2²³ overflows 79% of the tail into
the in-block fallback and costs **1.19×** — while the score says nothing is
wrong, because the score cannot reach the configuration. That is
OPTIMIZATION.md 2.13 in the flesh, from the side it is usually missed: not
"the frozen window has outgrown the engine", but "the frozen window was
never big enough to exercise a quantity the engine sizes from the launch".

The countermeasure that ships is not a bigger benchmark — the frozen shape
is an anchor and an optimization pass does not get to move it — but an
engine that **says so**: `_pick_q3cap` sets `q3_short` when the ceiling
binds, and `config()` reports it, so a campaign that is in this state can
be seen to be.

At `b = 2` the same sweep is flat to 3% across every combination, because
that family's overflow is genuinely cheap — so its ceiling does bind
(`q3_short` is true at 713 MiB held) and it costs about 3%. Halving its
`per_launch` would hand back 256 MiB for nothing measurable, and is not
done automatically only because the identical change costs `b = 4` 14%.
Priced, and left where a reader can act on it.

### Rejected, with numbers

| attempt | measured | why it was tempting, and why it lost |
|---|---|---|
| **64-bit plane words** (halve the load count per period) | **0.927 / 0.887 / 0.793 / 1.014** at matched tile size | the load count halves but a warp's 32 eight-byte loads are 256 B against L1's 128 B/cycle, so each load costs two cycles instead of one — and `__funnelshift_r` is ONE instruction where the 64-bit combine is a shift, a shift, an or and a uniform branch. Nothing was saved and something was spent |
| **the queue holds the offset** instead of the block index (8 bytes, no rebuild per round) | **1.110 / 0.895 / 0.970 / 0.979** | the rounds rebuild `off` with a 64-bit multiply every time, so removing it looks free. It is not: the shared queue is 4× bigger, that costs resident blocks per SM, and occupancy is worth more here than the rebuild |
| **CRT-combined test units** — "killed by 79 or by 83" as one reduction and one lookup | **~1.00** overall; 1.10 / 1.00 / 1.02 / 0.93 at 2¹³, and **0.76 on SCORE4W at 2¹⁵** | it paid 1.19× in square-ladders, whose test loop is longer. Here the round chain is only two to five units deep before the tail takes over, so the saving lands on a phase that is already small — and the wider caps walk straight into the L1 cliff. Kept at 2¹³, where it is neutral to mildly positive, rather than removed, because the mechanism costs nothing at that size |
| **ordering the residue table by the biggest plane's shift** — a host-side sort, zero cost on the device, aimed straight at the plane reads' locality | **1.079 / 1.006 / 1.021 / 0.989**, then **0.946 / 1.014** on a 21-round confirmation | the mechanism is real: one block is one residue, a block reads a contiguous run of each plane at an offset that is random in the residue, so the ~2,000 blocks resident at any moment touch 2,000 unrelated windows of a 7 MB plane where sorted they would touch 2,000 adjacent ones. It measures **nothing** — `SCORE`'s 1.079 inverted to 0.946 on repetition, which is what a 12-23% noise floor does to a 2% effect. Removed rather than kept: a change that cannot be measured is not a change to ship, however good the story is |
| raising the global tail queue (row 10 above) | 0.877 / 1.003 / 0.952 | see above — the smaller budget ships |

### A bug the gates would not have caught, caught by re-reading

When the block tile became adaptive, `_pick_launch` started rounding
`per_launch` up to a whole block tile — sensible for the DERIVED value, and
silently destructive for an EXPLICIT one. Every gate that forces a launch
split passes `per_launch` explicitly, so G15's "18 periods in one launch
against six" became two identical single-launch sweeps, and the resume
drill's three-way split became one. **Both gates stayed green and both had
stopped checking anything.** The fix is four lines: an explicit
`per_launch` is honoured exactly, only the derived one is rounded. There is
no gate that catches a gate going vacuous; what caught it was reading the
new code against what the old gates assumed.

### Two process notes, both of them mistakes caught in flight

**Rule 4 was broken once and repaired.** The first 64-bit-plane A/B changed
the plane word width *and* doubled the block's period span, because the
tile is `TPB * WPT * wordbits`. It read 0.94 / 0.87 / 1.16 / 1.02 — a
muddle. Re-run with `WPT` halved so the tile was identical, the answer was
clean and negative. A word-width change is a shape change unless you hold
the shape.

**The noise floor is 12-23%, and it was measured twice rather than assumed
once.** In the
test-unit sweep, `unit_q_max = 1` and `unit_q_max = 2⁹` are the *same
binary* at every `p2` this engine picks (no pair of test primes has a
product under 512), and they measured 1.000 against 1.119. Later, `-maxrregcount` 96 and 128
compiled to the identical binary and measured **1.052 against 1.295** on
the same shape in the same sweep. Everything in the tables above under
about 1.10 is therefore reported with that in mind, and every decision that
turned on less than that was taken on the geometric mean across four shapes
and seven to nine interleaved rounds, never on one number. The changes that
carry this engine — the wheel, the packed test, the base fold, the queue —
are 1.9x to 40x and are not in that zone at all.

## Where it stands: the termination test (OPTIMIZATION.md Part 3)

Phase split on the shipped engine, `SCORE`, CUDA events around each of the
two kernels; the within-sieve shares are from the stage-truncation
measurement at the same schedule and are quoted to one significant figure
because that is what they are worth.

| phase | share | verdict |
|---|---|---|
| generation — the bit-plane reads | ~50% | **optimized, with one measured lever left that this pass may not pull.** Two loads, a funnel shift and an `and` per 32 periods per plane. The plane COUNT is minimised by the budget sweep (2²⁶) and by deriving `p2`; widening the word to 64 bits to halve the load count was built and measured **0.90×** — a warp's 32 eight-byte loads are two L1 cycles, and the 32-bit funnel is one instruction against three. The lever that is left is `p1`, and it is **1.198× measured** — see below. The per-word warp scan that rides along with generation is separately unsearched |
| the early-exit tail, in its own kernel | 23.9% | **optimized.** Moved out of the sieve block (1.08-1.32×) because a block that has whittled itself to a percent of its candidates has more idle warps than working ones, then given its OWN compaction chain (1.08× geometric mean) because its blocks, unlike the sieve block's tail, are always full. Its schedule was swept separately from the sieve's |
| compaction rounds, in the block | ~13% | **optimized.** Boundaries cut from the survival CURVE, swept as fractions (1.07-1.09× over the previous schedule); CRT-combining the test units — the thing that paid 1.19× in square-ladders — measured **~1.00 here** and is kept only at the size where it is free |
| extract & queue | ~12% | **bounded by the same quantity generation is.** One warp-aggregated shared atomic per `WPT` words behind a five-step shuffle prefix scan (~1.6 instructions per word amortized), plus an `ffs` loop that costs ~6 instructions per CANDIDATE and is skipped entirely for the 75% of words that are empty. Both terms are charged per WORD, and the word count is `R/W` — the flat table's density, which is exactly the quantity `p1` moves and which already carries the priced 1.198× below. So this phase does not have a lever of its own; it has generation's. Ceiling if the scan were free: ~1.05× |
| host + syncs | <0.1% | **structurally done.** The per-sweep base fold was the last of it and is now one vectorised numpy step; measured residual 0.12 ms per sweep against a 5.5 ms launch |

Three of the five rows carry a lever. The table's job is to keep what
remains visible and priced, not to certify completion.

### Re-swept after the last structural change (Rule 3.4)

Every tuning constant here was first swept before the tail kernel, its own
compaction chain, the vectorised base fold and the queue correction landed,
so all of them were stale. Re-swept, interleaved, seven rounds:

| constant | candidates | result |
|---|---|---|
| block tile `TPB x WPT` | 64x8, 64x16, 128x4, **128x8**, 128x16, 256x4, 256x8 | **unchanged.** 128x8 is best or tied on three shapes; `SCORE2` prefers 128x4 by 1.12 and 64x8 by 1.09, which does not survive the geometric mean (1.005 and 0.983) |
| round schedule `(ratio, tail, tail2)` | ratio 0.5/0.65/0.8, tail 0.05/0.10/0.20, tail2 0.003/0.01/0.03 | **unchanged.** (0.65, 0.10, 0.01) is best or tied everywhere; the one apparent improvement (tail 0.20, 1.44x on `SCORE4W`) is a confound — raising `tail` moves the model's `p2` pick, so that row is a different wheel, and on the two production shapes it reads 0.95 and 0.90 |
| the tile's SHAPE — capping `wact` so a block covers 2, 4 or 8 residues instead of one, at a launch long enough not to force it | 512 / 256 / 128 words | **unchanged**, geometric means 0.993 / 0.974 / 1.028. A separate axis from the tile's size (which the row above covers) and worth checking separately, because at the production launch the block covers exactly one residue and nothing forces that. It does not matter |

| the plane byte budget | 2¹⁷ / 2¹⁹ / 2²¹ / 2²³ / **2²⁶** bits | **unchanged**, geometric means 0.86 / 0.94 / 0.97 / 0.92 / 1.00. This one was swept against a MECHANISM rather than out of duty — the production planes total 12 MB, which is L2-resident but nowhere near L1, and if the plane reads were L2-latency-bound then shrinking them until they fit L1 should have paid. It does not: a smaller budget means MORE groups, and the extra group's loads cost more than the latency they save. The `ng * GEN_W / 32` term in the cost model is the right shape |

Four constants re-swept and none moved is a weaker result than the case
study's four-that-moved, and it is reported as such rather than dressed up:
what it says is that this engine's remaining headroom is not in its
constants. It is in the two things the phase table names — `p1`, worth a
measured 1.198x behind the frozen-shape question, and whatever the plane
reads are really waiting on — and on that second one, three separate
attacks (a smaller plane budget, a larger register budget, a
locality-ordered residue table) have now all measured 1.00, which is
itself worth knowing before a fourth is attempted.

### What the kernel is actually bound by, and one hypothesis killed

Not instruction issue, and not L1. At the production shape the sieve kernel
uses 46 registers with no spills, which is **92% occupancy** (1,408 of
1,536 threads per SM), and it issues about 3×10¹² thread-instructions per
second against the card's 4.2×10¹³ — **7%** — while touching about 4% of
L1's sector throughput. A kernel at 92% occupancy using 7% of issue is
latency-bound on its dependent chains, and the resource that decides how
many independent plane loads can be in flight at once is the register file.
That is a testable statement rather than a comfortable one, so it was
tested: `-maxrregcount` at 48 / 64 / 80 / 96 / 128, which moves the sieve
kernel between 47 and 56 registers and the tail kernel between 48 (with
spills to local) and 76.

**It does nothing.** Geometric means across the four shapes: 0.89 at 48,
0.97 at 64, 1.03 at 80, 0.97 at 96, 1.01 at 128 — and the two settings that
*look* like wins on `SCORE` (1.253 at 80 and 1.295 at 128) are not, because
**96 and 128 compile to the identical binary** (56 and 76 registers, byte
for byte) and measured **1.052 and 1.295 against each other.** That is a
23% spread between two runs of the same code, measured inside the sweep
that was supposed to be reading a 25% effect, and it is the most useful
number this experiment produced.

So the hypothesis is dead: whatever latency this kernel is waiting on is
not bounded by how many independent loads a thread can hold in flight.
What is left is the dependent chain *inside* one test — the uint4 load, the
64-bit multiply-high that needs it, the bitmap load that needs that, and
the branch that needs the bitmap — which no register budget shortens. The
knob was removed rather than shipped at a default of "compiler's choice",
because a knob whose every setting measures 1.00 is a dead code path
(OPTIMIZATION.md rule 0), and the evidence for the verdict belongs here.

### The one lever left in the dominant phase, and why it is not pulled here

Generation costs `ng` plane reads per 32 periods **per residue of the flat
table**, so its cost per unit of m line is proportional to `R/W` — the flat
table's density — and **not to `p2` at all**. Raising `p1` from 23 to 29
halves that density (7.05×10⁻³ → 3.65×10⁻³) while leaving the *total* wheel
where it was: the model still picks a wheel to 79, it just draws the line
between table and planes in a different place.

Measured on an absolute-m window both configurations can cover, streams
compared, three interleaved rounds:

| `p1` | R | W | wheel | rate | | held |
|---|---|---|---|---|---|---|
| 23 | 1,572,480 | 2.23×10⁸ | ≤ 79 | 3.008×10⁸ | 1.000 | 394 MiB |
| **29** | 23,587,200 | 6.47×10⁹ | ≤ 79 | **3.602×10⁸** | **1.198×** | 1015 MiB |

29 is also the last step available: `p1 = 31` would need 613 million flat
residues against `RES_MAX`'s 33.5 million, and at `b = 2` the next step
(41) needs 129 million, so that family is already at its top.

**It was priced, put to the owner, and taken.** What follows is the record
of the question and of what the answer cost; the rule below is why it was a
question rather than a commit.

**The rule, and why it applies.** `p1`
sets `W`; `W` is the unit every frozen benchmark window is expressed in and
the unit the coverage cursor counts in. Moving it changes what `SCORE`'s
8,192 periods *are*, so the fingerprints move, so the anchor that makes
scores comparable across engine generations moves — and OPTIMIZATION.md
2.13 is explicit that this is not a change an optimization pass gets to
make on its own. The cursor half is free right now (no campaign has run, so
there is no cursor to re-denominate, and `CursorPolicy`'s `adopt` handles
it when there is); the benchmark half is the owner's call. Both options are
real:

- **amend the frozen shapes** — re-express the five windows at `p1 = 29`,
  re-freeze the fingerprints, and note the discontinuity in this ledger;
  the campaign gets 1.198× and the score keeps meaning "the production
  configuration";
- **accept the ceiling** — keep `p1 = 23`, and the engine runs at 83% of
  what the same code would do, with the score continuing to measure exactly
  what the campaign runs.

Shipping `p1 = 29` in production while the benchmark stayed at 23 is the
one option that is *not* on the table: `SCORE` would stop describing the
configuration the hunt actually runs, which is the property the whole
benchmark exists to have.

**The owner chose to amend the frozen shapes.** What that cost:

- **`SCORE` and `SCORE1L` re-frozen.** They are the only two shapes whose
  windows are counted in periods of the b = 4 flat wheel. New window
  `[1.000001e15, +2.649986e13)` — `j0 = 154,567`, 4,096 periods at
  `W = 6,469,693,230`; fingerprint **73 / 1038246173448745**. `SCORE1L`
  covers the *identical absolute window* at `p1 = 13`
  (`j0 = 33,300,069,047`, 882,446,336 periods, because
  `W(29) = W(13) × 215,441` exactly) and reproduces that fingerprint, so
  the benchmark's own cross-check survives the move intact. The old pair
  (7 / 998631924604311) is kept in BENCHMARKS.md; the two generations'
  SCOREs are not directly comparable and the ledger says so.
  `SCORE2`, `SCORE4W` and `SCORE10` are untouched — their `p1` did not
  move, so their windows and fingerprints did not either.
- **The new window is FOUR launches wide**, deliberately, and this turned
  out to be worth as much as the speedup. The old one was a quarter of a
  launch, which is what let the tail queue be mis-tuned invisibly. Widening
  it cut the benchmark's OWN noise from **31% to 2.4%** across three
  `score.py` runs (and `SCORE1L`, at 27 launches, to **0.2%**), while the
  three shapes still inside one launch still swing 23-33%. A benchmark that
  cannot reach a second launch is not only blind to per-launch tuning; it
  is a worse instrument for everything else too, because a partial launch's
  fixed costs are charged to it in full and they are the noisy part.
- **The launch sizing had to be re-derived, and this is the interesting
  part.** `R` goes up 15× and `W` up 29×, so at an unchanged `per_launch`
  a launch would hold 29× the work and the global tail queue would overflow
  by a factor of twenty. `per_launch` is now derived from a **slot** target
  (`R × per_launch`, `CAND_SLOTS`) rather than floored at one block tile,
  and `RPB_MAX` went 8 → 32 so that a launch short in *periods* still fills
  a block by covering more *residues*. Both families now use all 1,024 of
  a block's work items, and `b = 2` — which was quietly running with its
  tail queue at the ceiling — stopped being short as a side effect, worth
  **1.26×** on `SCORE2` (1.21e12 → 1.53e12) that has nothing to do with
  `p1` at all.
- **The cursor policy split per base.** Base 4 now **adopts** its two
  `p1 = 23` keys — different `W`, so only the coverage claim carries over
  and `load` floors it into the new periods — while base 2 **inherits** its
  v1 key, `p1` there never having moved. A new drill puts the *other*
  family's policy in front of every key it declares, because
  `drills.standard` only exercises the base the selftest was run for and
  the two now declare different classes of old key. 30/30.

**Measured, both engines over a COMMON ABSOLUTE WINDOW with the two streams
compared to each other** (a period-indexed A/B would be comparing two
different spans now):

| family | v1 | v2 | ratio |
|---|---|---|---|
| A130003, `b = 4` | 4.17×10¹² m/s | **3.54×10¹⁴ m/s** | **84.8×** [84.7, 85.5] |
| A110096, `b = 2` | 2.90×10¹⁶ m/s | **1.29×10¹⁸ m/s** | **44.6×** [41.9, 47.4] |

## The campaign, measured (2026-08-24) — and the biggest lever is not the kernel

Two campaigns ran (RESULTS.md): base 4 for 17.44 h to `m = 8.95×10¹⁸`, base
2 for 38.2 min to `m = 3.62×10²¹`, four terms between them. This section is
what they measured about the *campaign*, which OPTIMIZATION.md 5c says to
price separately from the engine and which this project had not done.

**The campaigns ran at 29% and 41% of the kernel.** Both figures compare
each family's own last stretch — the filter it was actually running at the
end — against the same configuration measured here on a free GPU, over
whole launches (the campaign's unit), interleaved between the families,
median of four:

| | campaign | device, same configuration | share |
|---|---|---|---|
| A130003, `n = 21` at the cursor | `1.45×10¹⁴ m/s` | `5.08×10¹⁴ m/s` | 29% |
| A110096, `n = 19` at the cursor | `2.12×10¹⁸ m/s` | `5.21×10¹⁸ m/s` | 41% |

**The phase split, per launch, before anything was concluded** (Rule 1 —
and it is the whole of this finding):

| | A130003, `n = 21` | A110096, `n = 19` |
|---|---|---|
| one launch is | 1,024 periods = `6.63×10¹²` of line | 16,384 periods = `1.22×10¹⁷` of line |
| survivors per launch | 1.4 | 22.2 |
| device (sieve + tail + readback) | 13.05 ms | 23.33 ms |
| host classification of them | 0.11 ms | 1.30 ms |
| checkpoint, amortised over its 16-launch segment | 0.45 ms | 0.45 ms |
| **the campaign actually took** | **45.59 ms** | **57.38 ms** |
| **unaccounted** | **31.98 ms** | **32.30 ms** |

Read the last row twice. Two families whose launches differ by **four
orders of magnitude in line swept** and **16× in survivors classified** lost
**the same ~32 ms per launch**. That is not a cost that scales with the
work — it is a per-launch constant, and it holds the whole 2.3-3.4×.

Both campaigns were started as plain `python -u launch.py` and
`python -u launch.py --base 2`, so no throttle was in play: `gpu_yield_ms`
defaults to 0 and the `time.sleep` in the inner loop never executes. The
32 ms is real overhead.

**IT IS `check_rungs`, AND IT IS THE PROGRESS LADDER REBUILDING ITSELF
FROM THE ODDS MODEL ONCE PER SEGMENT.**

    Campaign.ladder()   -> model.predictions(b, frontier, frontier_m,
                                             n_ahead=3, ceiling=...)
                        -> 3 terms x 4 quantiles = 12 quantile() calls
                        -> 90 bisection steps each
                        -> 1,080 calls to expected()
                        -> 1,080 numerical integrals, 3,000 points,
                           over up to 21 linear forms

One `expected()` is **0.509 ms**, so the arithmetic closes before the
stopwatch does: 1,080 × 0.509 = **550 ms**. Measured, minimum of twelve:

| | `model.predictions()` | per launch, over a 16-launch segment |
|---|---|---|
| base 4, frontier `a(20)`, `n = 21` | **578 ms** | **36.1 ms** |
| base 2, frontier `a(18)`, `n = 19` | **541 ms** | **33.8 ms** |

against the 31.98 and 32.30 ms the budget could not place. It accounts for
113% and 105% of the gap, which is as close as two independently measured
quantities get here, and the whole budget now reconciles to within 9% and
3%:

| | predicted launch | measured launch |
|---|---|---|
| base 4 | 13.61 + 36.1 = **49.7 ms** | 45.59 ms |
| base 2 | 25.08 + 33.8 = **58.9 ms** | 57.38 ms |

So a 17-hour base-4 campaign spent about **four fifths of its wall clock**
recomputing a progress ladder whose only output is a `[RUNG]` line on the
rare segment that crosses one. The heartbeat pays for it a second time:
`status_line` calls `next_rung`, which builds the same ladder again, every
30 seconds.

**What it is not**, each eliminated by its own measurement rather than by
argument, and all four checks are worth keeping:

- **not the sieve** — the device row is the kernel doing exactly what the
  campaign asked it for, at the campaign's own filter and depth;
- **not the host classifier** — 0.11 ms and 1.30 ms, 0.2% and 2.3% of the
  campaign's launch. The v1-era sizing claim in `launch.py` ("this hunt
  needs no worker pool") was made at 85× less device throughput and is
  re-checked here at v2: still right, with two orders of magnitude of
  margin. It is the one load claim in this project that survived the
  engine change without re-sweeping, and now it has been re-swept;
- **not the checkpoint** — an fsynced `checkpoint.save` with a `.bak`
  rotation measures 7.2 ms [7.0, 7.4] over 20 writes, once per 16 launches;
- **not `time.sleep` granularity** — checked before the flags were known,
  in case `--gentle`'s 2 ms had become a Windows 15.6 ms timer quantum.
  `sleep(0.002)` returns in 2.52 ms [2.02, 2.75] here. It had not, and the
  flag was not used anyway.

### The fix, priced but NOT applied

**Memoise the ladder on the frontier it was derived from.** `ladder()`
depends on exactly `(b, frontier(), frontier_m(), filter_n())`, and all
four move only when a discovery lands — a handful of times per campaign,
against tens of thousands of segments. Cache on that tuple and invalidate
when it changes.

This does not weaken the rule the recompute was there to enforce.
CONVENTIONS.md wants a ladder that cannot aim at a retired depth, and a
cache **keyed on the frontier itself** cannot go stale by construction —
the frontier moving *is* the invalidation. What is being removed is not the
guarantee, it is 1,080 numerical integrals per segment recomputing an
identical answer.

Priced from the budget above:

| | now | with the ladder cached | on `a(21)` / `a(19)` at the median |
|---|---|---|---|
| base 4 | `1.45×10¹⁴ m/s` | `4.87×10¹⁴ m/s` — **3.35×** | 6.0 d → **1.8 d** |
| base 2 | `2.12×10¹⁸ m/s` | `4.85×10¹⁸ m/s` — **2.29×** | 3.2 d → **1.4 d** |

and both landing figures agree with the free-GPU device rates measured
independently (`5.08×10¹⁴`, `5.21×10¹⁸`), which is the check that the
budget has nothing else hiding in it.

It is **not applied here** because it changes the campaign hot path and
belongs in a commit that A/Bs it against a real segment loop, with the
owner's call on the caching contract — not in a documentation pass. **Do
not touch the kernel before this lands.** At base 4 it is worth 3.35×,
and the largest measured item left inside the engine is 5%.

Two process notes this cost, both of them rules already written down:

- **OPTIMIZATION.md Rule 1, "measure the phase split first", applies to the
  CAMPAIGN and not only to the kernel.** This project measured its kernel's
  phase split in exquisite detail (§ Round 0) and never once timed a
  segment. Every optimization in this log before this entry was aimed at
  13.05 ms while 32 ms sat beside it, unlooked at.
- **A per-launch cost that does not scale with the work is the signature to
  look for.** Two families that agree to 1% on an absolute overhead while
  disagreeing by 10⁴ on everything else is not a coincidence; it named the
  suspect class (host, per launch, work-independent) before the suspect.

### `--gentle`'s advertised price is not reproduced

The help text says "about a third of the rate". The yield measures 2.5 ms
against a 13.05 ms base-4 device launch — about a fifth, and it would be
5% of the campaign's launch as the campaign actually ran. The help text is
left alone rather than overwritten: the two numbers may be measuring
different things, and replacing someone's measurement with a
differently-scoped one is how a log stops being evidence. Re-measure it
deliberately once the ladder is cached, then change both.

Neither campaign used it. Both were started as plain `python -u launch.py`.

**A structural fact the campaign settled, in the engine's favour: a higher
filter is faster.** The same 4,096-period window at the base-4 cursor:

| filter | rate | |
|---|---|---|
| `n = 19` | `4.34×10¹⁴ m/s` | |
| `n = 20` | `4.90×10¹⁴ m/s` | 1.13× |
| `n = 21` | `5.32×10¹⁴ m/s` | 1.23× |

`w(q,n,b) = min(n, ord_q(b))` grows with `n`, so a longer ladder kills more
of the line per prime and the wheel gets denser rather than the test loop
longer. **Every term this project finds makes the next one cheaper per unit
line.** That is the opposite of the usual, and it means `a(22)`'s cost
should be priced at its own filter and not extrapolated from `a(21)`'s.

## Priced and not done

- **A second wheel level below the plane wheel.** `p1` sets `W` and hence
  the unit of the coverage cursor, so raising it re-denominates every
  checkpoint (`REDENOMINATE`, not `INHERITS`) and buys only what the planes
  already buy more cheaply. Not worth the cursor churn.
- **A deeper sieve (`q2` above 65536).** The classification host cost is
  about a tenth of one core at the v2 rate, so nothing is host-bound and a
  deeper sieve would buy nothing the campaign can spend. Re-price if the
  survivor path ever becomes the constraint.
- **Overlapping the host's per-launch table update with the device.** The
  update is ~0.2 ms against a ~27 ms production launch — 0.7%, and the
  double buffer would have to be right across the interrupt path. Priced,
  declined, and the price is written down.
- **`b = 2`'s launch size against its tail queue.** At `per_launch` 8,192
  instead of 32,768 that family holds 457 MiB instead of 713 and measures
  the same rate to 3%. It is not done automatically only because the
  identical change costs `b = 4` 14%, and a per-base override would be a
  constant where this engine derives everything else. A reader who wants
  the 256 MiB back can pass `per_launch` and lose nothing measurable.
- **The extract stage's warp scan**, above — the one phase over 5% with no
  verdict of its own.

## Declined

Everything in "Rejected, with numbers" above, each with the measurement
that settled it. Nothing has been declined here on a projection.
