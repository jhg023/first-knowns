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

> **SUPERSEDED 2026-08-27 (second pass).** The table below was measured on
> the v2 engine at `p2 = 79`, and both its shares and its verdicts are
> stale: re-ablated at the production configuration, generation is 38%
> rather than ~50%, `extract & queue` is 16% rather than ~12%, the tail is
> 5.7% rather than 23.9%, and 14.5% of a launch is block dispatch and
> prologue, which this table has no row for at all. The current table is at
> the end of this file, "The termination test, re-derived". Kept here
> because the *reasoning* in its rows is still the record of what was tried
> and why — but a share or a verdict read out of it is out of date.

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

### The fix, APPLIED 2026-08-27 — 3.47x and 2.42x

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

**Measured, not projected.** A paired, interleaved A/B of the REAL segment
loop — `Campaign`'s own inner loop against a scratch checkpoint, three
segments per arm, three rounds, arms alternating within each round:

| | rebuild (before) | cached (after) | ratio |
|---|---|---|---|
| base 4 | `1.274×10¹⁴ m/s` (51.9 ms/launch) | `3.788×10¹⁴` (17.5 ms) | — |
| base 2 | `5.186×10¹⁷ m/s` (58.6 ms/launch) | `1.098×10¹⁸` (27.9 ms) | — |

That arm ran at the *published* frontier (filter 19 / 17, a fresh scratch
checkpoint), which is the wrong configuration for a resume. Re-run with the
checkpoint seeded so the frontier is this project's own, at the filters a
resume actually uses, 12 segments each:

| | campaign, as it ran | after | ratio |
|---|---|---|---|
| base 4, n = 21 | `1.453×10¹⁴ m/s` | **`5.046×10¹⁴ m/s`** | **3.47×** |
| base 2, n = 19 | `2.119×10¹⁸ m/s` | **`5.119×10¹⁸ m/s`** | **2.42×** |

Two independent corroborations that the budget has nothing else in it:
the "before" arm reproduces the campaign's own launch times (51.9 vs 45.6
ms, 58.6 vs 57.4 ms), and the "after" rates land on the free-GPU device
rates measured separately (`5.08×10¹⁴`, `5.21×10¹⁸`). The loop is now
**94.7% and 89.8% device**:

| per launch | base 4, n = 21 | base 2, n = 19 |
|---|---|---|
| sweep | 12.44 ms — 94.7% | 21.33 ms — 89.8% |
| classify | 0.17 ms — 1.3% | 1.84 ms — 7.8% |
| checkpoint | 0.52 ms — 3.9% | 0.57 ms — 2.4% |
| rungs | **0.00 ms** | **0.00 ms** |

`a(21)` at the median goes 6.0 d → **1.7 d**, `a(19)` 3.2 d → **1.3 d**.

**A measurement artefact worth recording, because it nearly shipped as a
finding.** The first split run after the fix showed `rungs` at 26.8
ms/launch and looked like the cache had not worked. It had: the run was
four segments long, and the ONE-TIME build (1,755 ms at a fresh frontier
with 7 rungs already behind the cursor) smeared across them at 429 ms each
and read as a steady per-segment cost. Printing the rebuild counter settled
it in one line — 1 build, then 0.0 ms forever. **A one-time cost divided by
a short run is indistinguishable from a recurring one**; measure the
steady state, and count the events rather than inferring them from a mean.

**The drills that keep it honest.** A cache without a test for its
invalidation is how the dickson-ladders incident comes back.
`huntlib.rungs.gate_live_ladder` proves 51 reads at a standing frontier
cost 1 build, that a find costs exactly one more and moves the aim from
a(12) to a(13) with no retired rung served from cache, and that
`frontier_m`, the filter and `invalidate()` each force a rebuild on their
own. The campaign-wiring drill proves the same on this launcher's own
wiring: 75 ladder reads at a standing frontier cost **zero** rebuilds, and
setting a find moves the frontier, costs exactly one rebuild, and takes the
aim off `a(19)`.

**And those gates were not running anywhere.** `huntlib.rungs.GATES` — the
ladder-retirement drill written *because* of dickson-ladders, and kept in
huntlib expressly because the rule is repo-wide — was included by exactly
one project's `score.py` and by no launcher at all. It is now part of
`drills.standard()`, so every project gets both ladder gates: this battery
went 30 → 32.

### Measured alongside it and DECLINED, with numbers

Both were swept in the same session, so nobody re-runs them.

**1. Precomputing `b**k` in the run-length classifier. REJECTED, 0.993x /
1.001x.** The classifier is `while mr_is_prime(m + b ** (r+1))`, and the
exponentiation looked like free money at base 2 where classification is
7.8% of the launch. Measured on real survivors from each resume window
(72 and 182 of them, five paired rounds): 65.5 -> 66.0 us per survivor at
base 4 and 70.9 -> 70.8 at base 2. It is **entirely Miller-Rabin**; the
`b**k` is noise. The only thing that would move this row is a cheaper
primality test or taking classification off the critical path, and at
1.3% / 7.8% neither is worth the machine (CONVENTIONS.md, sizing).

**2. Raising base 4's `per_launch` 1024 -> 2048. DECLINED, 1.025x
[0.986, 1.118].** OPTIMIZATION.md's re-sweep rule applies here because the
filter moved 19 -> 21, so the derived launch size was re-swept at the
resume configuration, interleaved, fingerprint (survivor count) checked on
every run:

| `per_launch` | rate | vs best | `q3_short` | memory |
|---|---|---|---|---|
| 256 | `2.72×10¹⁴` | 0.473x | False | — |
| 512 | `4.12×10¹⁴` | 0.716x | False | — |
| **1024 (derived)** | `5.40×10¹⁴` | 0.938x | False | 678 MiB |
| 2048 | `5.51×10¹⁴` | 0.972x | False | 852 MiB |
| 4096 | `5.76×10¹⁴` | **1.000x** | **True** | 1015 MiB |
| 8192 | `5.24×10¹⁴` | 0.951x | True | 1015 MiB |
| 16384 | `5.30×10¹⁴` | 0.962x | True | 1015 MiB |

The peak at 4096 is only 1.07x over the derived value and it sits **past
the tail queue's ceiling** (`q3_short = True`), the regime this log already
prices at ~19% and the launcher prints a warning about; beyond it the curve
turns over. So the only safe step is 2048, and a paired 10-round A/B put it
at **1.025x, range [0.986, 1.118]** — an interval containing 1 — for
+174 MiB. Declined under the load rule ("when two settings tie on
throughput take the one that asks for less machine"), and because a
per-base constant is exactly what this engine derives everything else to
avoid. Base 2's derived 16384 **is** its optimum, so nothing to do there.

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

Both are now repo-wide rules rather than one project's scar tissue:
CONVENTIONS.md "The model is EXPENSIVE, and the segment loop may not call
it" and the wall-clock clause in the sizing procedure, OPTIMIZATION.md
§2.14 and the campaign-loop clause under Rule 1, and a line in CLAUDE.md's
new-project checklist. `square-ladders` has the same shape — a `ladder()`
that calls `model.predictions` (473 ms there) from `check_rungs` — and is
saved only by a very long period; its log carries a note and its gates were
NOT run here (CLAUDE.md rule 2).

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

## 2026-08-27 — the wheel top was DERIVED, and the constant that derived it was 4x wrong

Two campaigns were about to resume. This pass swept what the previous one
had not, and the headline is a single mis-measured number.

**`p2` had never been swept.** Four constants were re-swept after the last
structural change (the table above); every one of them is a PINNED
constant. `p2` — the bit-plane wheel's top, and the largest single term in
the cost model — is DERIVED by `pick_p2` from `model_cost`, and a derived
value hides its own error: every gate stays green and every fingerprint
reproduces, because `p2` removes candidates and never survivors. The
benchmark then reports, faithfully, the rate the wrong pick produces.

Swept empirically at both resume configurations, arms **order-rotated**
inside each round (the first pass showed rates climbing monotonically with
POSITION in a round, which would have credited whatever ran last), survivor
stream compared across arms every round:

| `p2` at `b = 4`, `n = 21` | ratio | | `p2` at `b = 2`, `n = 19` | ratio |
|---|---|---|---|---|
| 79 (shipped, derived) | 1.000 | | 89 (shipped, derived) | 1.000 |
| 97 | 1.220 | | 109 | 1.373 |
| **103** | **1.313** | | 127 | 1.513 |
| 107 | 1.162 | | **131** | **1.578** |
| 113 | 1.220 | | 137 | 1.409 |
| | | | 151 | 1.282 |

Both plateaus are broad and both start four to six primes past where the
model stopped. **`GEN_W` — the modelled cost of one plane read per 32
periods, in units of one packed test — was 3.80 and measures 0.95**, fitted
by least squares in log rate over 15 measured (p2, rate) pairs across both
shapes. Overpricing a plane read by 4x is exactly a wheel that stops early.
The fit tracks the measured curve to a few percent, and it was checked
against a THIRD, very different configuration so it is not two shapes wide:
at `n = 10, p1 = 13` (the `SCORE10` regime, survivor-dominated) `p2` is
flat from 101 to 167 and the new pick costs 0.991x.

**The plane budget had only ever been swept BELOW its own default.** The
old sweep ran 2^17 / 2^19 / 2^21 / 2^23 / 2^26 and stopped at 2^26 because
that was the shipped value. At a FIXED `p2 = 103` the budget is worth
**1.311 / 1.202 = 1.09x**: 2^28 packs (29, 103] into 4 groups where 2^26
needs 5, and the group it saves costs more than the 27.6 MiB of L2 it
spends. The counterweight is real but further out — at 2^30 the b = 4 wheel
wants 119.5 MiB and stops being L2-resident.

**`UNIT_Q_MAX` was stale for a reason worth naming: the test-unit list
STARTS at `p2`.** Moving the wheel top makes it a different list, so the
old optimum was measured against an object that no longer exists. 2^15
measures **1.115x [1.051, 1.185]** at b = 4 — at 2^15 the first units
become PAIRS instead of singletons — and 1.04x [0.97, 1.04] at b = 2.
2^18 is still the L1 cliff at 1.018x, so the cap moved two steps, not off.

### `p1` = 41 at base 2 — and the comment that said it could not be

The code said b = 2 was already at its ceiling: "41 would want 129 million
residues" against `RES_MAX`. **That is an n-DEPENDENT number and the
campaign had moved past it.** `w(41,n,2) = min(n, ord_41(2)) = min(n, 20)`,
so 41 keeps `41 - w` residues: 24 of them at the `n = 17` the comment was
written at, but **22** at the `n = 19` the hunt now runs — 44.5 million,
not 129. And it only shrinks from here, because `w` grows with `n` and
every future filter is larger. `RES_MAX` went 2^25 to 2^26 to admit it; it
still refuses that family's n = 17 wheel and still refuses `p1 = 47`
(36 billion), which is what the guard is for.

`R/W` falls `2.72e-7` to `1.46e-7` — a **1.864x** cut in the phase that is
paid per residue — for 1.5 GiB of device tables and a ~34 s wheel lift at
startup. Measured on a common ABSOLUTE window at a common `p2 = 131`
(a period-indexed A/B compares two different spans once `p1` moves), and
the two streams agree on all 958 survivors:

| | rate | ratio |
|---|---|---|
| `p1 = 37`, `per_launch` 16,384 | `8.62×10¹⁸ m/s` | 1.000 |
| `p1 = 41`, `per_launch` 1,024 | **`1.21×10¹⁹`** | **1.398x** |
| `p1 = 41`, `per_launch` 2,048 | `1.15×10¹⁹` | 1.336x (`q3_short`) |
| `p1 = 41`, `per_launch` 512 | `8.49×10¹⁸` | 1.051x |

Base 4 has no such step, and the arithmetic says why: a prime buys density
`(q - w)/q` and costs `(q - w)` TIMES the residue count, so the primes
worth adding are those with a small SURVIVING set. At b = 4, `p1 = 31`
keeps 26 residues (`ord_31(4) = 5`) — 613 million of them, 16 GiB of
tables, for 1.19x. Declined on the numbers, not on the ceiling.

### The launch size was a constant standing in for a queue

`per_launch` was derived from `CAND_SLOTS`, a target on `R × per_launch`.
The quantity that actually binds is the **tail queue**: `q3` holds
`R · per_launch · d2 · S_tail` entries, so it moves with the WHEEL — and
when `p2` moved, `d2` fell 3x and the queue emptied. 4,096 periods at
b = 4 had been measured at 1.07x **and rejected** by the previous pass
because it reported `q3_short` at the old `d2`; the same setting is now
comfortably inside the queue, and the derivation could not see it, because
a slot target does not know what a queue holds.

`_pick_launch` now takes the largest power of two that BOTH the slot guard
and the tail queue allow; `CAND_SLOTS` is raised 2^35 to 2^37 and demoted
to a guard. It derives 4,096 at b = 4 (was 1,024) and 2,048 at b = 2 (was
16,384 at `p1 = 37`) — and the b = 2 value is the interesting one, because
deriving against the slot count alone would have picked 2,048 at
`p1 = 41` too, where the table above shows it is SHORT. The rule now stops
one power of two before `q3_short` rather than reporting it and running.

### End to end, and what it cost the benchmark

Paired, order-rotated, streams compared, at the configuration each campaign
actually resumes at:

| family | before this pass | after | ratio |
|---|---|---|---|
| A130003, `b = 4`, `n = 21` | `5.15×10¹⁴ m/s` | **`7.92×10¹⁴`** | **1.537x** [1.437, 1.607] |
| A110096, `b = 2`, `n = 19` | `5.63×10¹⁸ m/s` | **`1.34×10¹⁹`** | **2.380x** [2.247, 2.466] |

Three of the five frozen shapes were re-frozen, and only one of the three
is the `p1` reason this project already had a precedent for:

- **`SCORE2`** — `p1` moved 37 to 41, so `W` moved, so the window is a
  different window. Its filter moved 17 to 19 with it (`RES_MAX` refuses
  the n = 17 table at `p1 = 41`), which also makes it describe the campaign
  as it now runs rather than as it ran before two finds.
- **`SCORE` and `SCORE1L`** — and this one is new. **The derived
  `per_launch` reached 4,096, so the 4,096-period window that had been four
  launches wide became exactly ONE, silently, with its fingerprint still
  reproducing.** A window is not four launches wide; it is four launches
  wide *at a launch size the engine derives*, and the engine is entitled to
  re-derive it. Both were widened 4x at the same `j0`, and the cross-check
  survived intact: `SCORE` and `SCORE1L` return the identical
  255 / 1106501012061793 over the identical absolute window at wheels
  215,441 periods apart.

The old fingerprints are recorded in `score.py` and BENCHMARKS.md.
`SCORE4W` and `SCORE10` use neither wheel, were not touched, and reproduce
unchanged — which is the whole point of a `p2` change under a frozen
benchmark.

### Re-swept in the same session and NOT moved

All at the new `p2`, because that is what the re-sweep rule is for.

| constant | candidates | result |
|---|---|---|
| block tile `TPB x WPT` | 64x8, **128x8**, 128x16, 256x4, 256x8 | **unchanged.** 128x8 best or tied; 256x4 reads 0.843, 64x8 0.899, 128x16 0.982 |
| round schedule `(ratio, tail, tail2)` | ratio 0.5 / **0.65** / 0.8, tail 0.05 / **0.10** / 0.20, tail2 0.003 / **0.01** | **unchanged.** 0.5 reads 0.942; 0.8, tail 0.05 and tail2 0.003 all sit inside noise of 1.00. tail 0.20 reads 1.056 but takes the launch PAST the tail queue (`q3_short`), the regime this log already prices at ~19% |

### Rejected, with numbers

- **Fewer plane groups.** `p2 = 67` at 2^28 gives `ng = 2` with 12.9 MiB of
  planes — half the generation loads — and measures **0.729x**. Generation
  is cheaper per load than the model believed (that is the `GEN_W`
  finding), so trading candidates for loads runs the wrong way.
- **Plane budget 2^30.** Picks `ng = 2` at `p2 = 71` and 119.5 MiB, which
  crosses this card's L2. Not carried to a verdict: 2^28 dominates it in
  the model and keeps its planes resident, so 2^28 shipped.
- **A CRT-factored two-level residue table**, to escape `RES_MAX`
  altogether. Both `res` and the per-residue plane shift are LINEAR in the
  residue (`cr_g(r) = (W^-1 mod Q_g) · r mod Q_g`), so a two-level table
  costs `R_a + R_b` instead of `R_a · R_b` and the memory wall disappears
  entirely. It dies at the other end: `per_launch` is `~CAND_SLOTS / R`, so
  at b = 4's `p1 = 31` (613M residues) a launch would cover 32 periods —
  ONE plane word per residue — and the per-residue setup, which currently
  amortises over 128 words, would dominate. The measured shape of that
  penalty is in the `p1 = 41` table above: 512 periods reads 1.051x where
  1,024 reads 1.398x. Priced and declined.

## 2026-08-27 (second pass) — the phase table was wrong, and the noise floor is 11%

A pass aimed at four leads from a static reading of the engine. **None of
them is a throughput win**, and the two most useful things it produced are
a corrected phase table and a number nobody had measured: how well this
harness can actually resolve a ratio.

### The measurement that should have come first: what an identical kernel measures

Three arms, **byte-identical kernels** behind different comments, paired
and order-rotated over the production window at the live base-4 cursor:

| arm | median | ratio vs the first | per-round range |
|---|---|---|---|
| shipped | 1035.30 ms | 1.0000 | — |
| identical copy 1 | 1049.22 ms | 1.0214 | [0.8851, 1.1127] |
| identical copy 2 | 1051.02 ms | 1.0120 | [0.8825, 1.1091] |

**+-11% per round between two copies of the same binary**, at a window of
32 launches (1.05 s per measurement) where a longer window did not help —
so the noise is not launch granularity, it is the card, on a timescale
shorter than a single arm. The median over 11 rounds is good to about
+-2.5%; over 60 balanced rounds, to about +-0.6%. Every ratio below is
quoted against a control arm measured **in the same run**, and anything
inside the control's band is reported as unmeasured rather than as a
result. The log already had one instance of this (two identical binaries
reading 1.052 and 1.295 apart under `-maxrregcount`); it is now a standing
part of the harness instead of an anecdote.

The practical consequence: **this project cannot see a 2% change**, and
several of the small items below sit under that. Saying so is cheaper than
shipping them and believing the number.

### Round 0 — the phase split, measured, and it is not what the model says

Two independent differential ablations (OPTIMIZATION.md 3.3), on the
production configuration at the live cursor rather than on a benchmark
shape. **Prefix arms**: the kernel truncated one phase later each time,
registers pinned so occupancy is constant, every sink consuming only
DEFINED values through a `__syncthreads_or` ballot every thread must reach.
**Duplication arms**: the whole pipeline with the plane reads run two and
three times over the same addresses — `mask &= X` is idempotent, so the
survivor stream is unchanged and the fingerprint checks the arm, which a
truncated kernel can never do.

| phase | modelled | **measured** |
|---|---|---|
| block launch — an EMPTY kernel at the production grid | not modelled | **6.2%** |
| prologue — `res` read + the per-group plane shift | not modelled | **8.3%** |
| generation — the plane reads | 67.1% | **38.1%** |
| extract & queue | 3.1% | **16.1%** |
| compaction rounds | 16.6% | **25.6%** |
| tail-queue push | — | 0.7% |
| early-exit tail kernel | 13.2% | **5.7%** |
| sum of phases against wall clock | | **100.7%** |

The phases sum to the launch, which is Rule 1's check that the pipeline is
understood. The model is wrong in composition, not in ranking: generation
still dominates, but it is 38% and not 67%, `extract` is **five times**
the modelled figure, the tail is a third of it, and **14.5% of the launch
is block launch plus prologue, for which `model_cost` has no term at all.**
`GEN_W`, `EXTRACT` and `ROUNDC` price only what is per-residue and
per-candidate; a cost that scales with the BLOCK COUNT is invisible to
them. That is not a bug in `pick_p2` — the terms it trades are the ones it
has — but it means the phase table in this file must come from ablation
and never from `model_cost`.

The duplication arms agree and add something: one extra pass of the plane
reads costs **20.4%** of the launch and a second **26.4%**, against the
prefix arm's 38.1% for the first pass. Extra passes run cache-warm, so
they are a lower bound — and the gap between 20% and 38% is the price of
the first touch, i.e. generation is paying for MEMORY LATENCY, not for
instructions. That reading is what the next item then confirmed the hard
way.

### THE FIRST VERSION OF THE ABLATION WAS ANTI-EVIDENCE

Worth recording because it is exactly the failure OPTIMIZATION.md 3.3
warns about and it still happened. The first prefix sink consumed shared
arrays that nothing in the truncated kernel had written. Reads of
never-written shared memory are undefined, so nvcc was free to call the
whole expression undefined and **delete the loop being priced**: shared
fell 1560 B to 532 B, registers 44 to 22, and "generation" measured 8.3%
of the launch — it was timing an empty kernel over 2.95 million blocks.
The same run also reported the tail-queue push as **-6.5%**, work that
made the kernel faster, which is the tell that should stop a reading being
believed. Two rules came out of it, both now enforced in the harness:

- every value a sink consumes must be **defined**, and every buffer a
  phase writes must be **read back**, or the stores are dead and go away;
- the sink must be a **ballot every thread reaches**
  (`__syncthreads_or(_s == magic)`), not an `if (arg < 0)` guard — nvcc
  will sink the whole phase inside an untaken branch.

### Rejected, with numbers

**The warp shuffle for the second plane load — 0.773x [0.729, 0.813].**
The clearest result of the pass, and the only one outside the control
band on every one of 13 rounds. Generation loads `B[0]` and `B[1]` per
group to funnel-shift across a non-aligned bit offset. The index
arithmetic makes the second load redundant: with `idx = threadIdx.x +
i*TPB`, `rl = idx >> logw` and `wrd = idx & (wact-1)`, a warp holds 32
consecutive words of the SAME residue whenever `wact >= 32`, so `B[1]` of
lane L is `B[0]` of lane L+1 and `__shfl_down_sync` replaces it — 2 loads
per group becoming ~1.03, in the phase that is 38% of the launch. It is
**23% slower.** The second load is an L1 hit on the line the neighbour
lane is already pulling, and it is independent; a shuffle is a
warp-synchronising instruction on the dependent path. Removing a free load
to add a serialising one runs the wrong way.

That makes **four** independent attacks on generation's load count that
have now failed — 64-bit plane words (0.90x), the saturation guard
(0.818x), the locality-ordered residue table (~1.00), and this (0.773x).
Read together with the duplication arms above, the verdict is no longer
"bound by load count" but **bound by the latency of the first touch**, and
the corollary is that any change which trades a load for an instruction on
the dependent chain will lose. Do not attempt a fifth.

**`Q3_MAX` 2^26 -> 2^27, and the `tail_surv` x `per_launch` sweep it
unblocks — no.** The premise was that the tail queue's ceiling was capping
two knobs at once, and that `tail_surv = 0.20` had measured 1.056x last
pass *while overflowing into the in-block fallback*, so it had been
declined on the overflow rather than on its merits. Both halves turn out
to be wrong. Swept at `p2` PINNED (raising `tail_surv` moves the model's
`p2` pick, which is the confound this log caught once already), streams
identical, all arms with the queue actually large enough:

| `tail_surv` | q3 need | short? | ratio | | `per_launch` | ratio |
|---|---|---|---|---|---|---|
| 0.03 | 11.8M | no | **0.836** | | 4096 (derived) | 1.0000 |
| 0.05 | 19.4M | no | **0.915** | | 8192 | 1.0125 |
| **0.10** (shipped) | 31.3M | no | 1.0000 | | | |
| 0.15 | 48.8M | no | 0.969 | | | |
| 0.20 | 80.0M | no | 0.985 / 1.008 | | | |
| 0.35 | 134.6M | yes | 0.969 / 0.942 | | | |

Everything from 0.10 to 0.20 is inside the control band on two independent
sweeps that disagree about the sign; 0.03 and 0.05 are genuinely worse,
which is the schedule doing its job. **The shipped 0.10 stands**, and
`Q3_MAX` stays at 2^26 rather than spending 512 MiB of ceiling and 371 MiB
of queue to reach a setting that measures nothing.

And the premise about `per_launch` was simply mis-read: at the production
wheel the derived launch is capped by **`CAND_SLOTS`** (which allows 5,826
periods, so 4,096) and not by the tail queue (which allows 8,777). Raising
`Q3_MAX` does not move it. 8,192 was reachable all along by raising
`CAND_SLOTS`, and it reads 1.0125 — i.e. 1.2% slower.

**Hoisting the tile-edge tests (`full` flag) — 0.990, unmeasured.** A
block whose tile lies entirely inside the launch needs neither the `nyb`
clamp nor its select, which is every block but the last in production. It
buys nothing measurable and costs a branch. Not shipped.

### Kept — all three neutral on throughput, and kept for what they cost off the clock

None of these is a speedup and none is presented as one. What they buy is
memory, engine-construction time and one less table to be wrong about,
which is the currency OPTIMIZATION.md Rule 7 is about.

**`crv` does not exist any more — 360 MiB at base 4, 688 MiB at base 2.**
The per-residue plane shift is exactly linear in the residue,

    cr_g(r) = (W^-1 mod Q_g) * r  mod  Q_g

because `W^-1 mod Q_g` reduces to `W^-1 mod q` at every q in the group,
which is the CRT reconstruction `plane_shifts` performs. (The identity was
already in this log, used to price a two-level residue table; it was never
used for the table it makes redundant.) So the block prologue computes it
from `res` — which it already reads — and one baked constant per group,
instead of streaming `R * NG` u32 from HBM once per launch. Verified
against `plane_shifts` on 11 groups across four wheels and both bases,
every residue.

Throughput **0.9985 [0.95, 1.12] at base 4** and **0.979 at base 2** —
neutral, and the reason is the phase table: 360 MiB per 33 ms launch is
10.7 GB/s against ~1000 GB/s available, so it was never bandwidth. It is
a memory saving, not a speed one.

**The prologue's `switch (g)` had to go with it.** Base 2 first measured
a real ~2% REGRESSION, and the cause was structural: the prologue walked
`nrl * NG` items with `g` fastest and dispatched on it, so a warp covered
every group at once and ran all `NG` case bodies serially. That was
survivable when a case body was one modulo; it is not when the case
computes the plane shift. Restructured to one straight-line pass per
group, with `Q`, `W^-1` and the plane offset as literals and `g` gone from
the runtime entirely, base 2 moves from **0.982 to 1.020** and base 4 is
unchanged within the control band.

**`key0` is `idx << 5`.** The key packs `(rl, wrd, bit)` as
`(rl << (logw+5)) | (wrd << 5) | bit`, and `wact = 1 << logw`, so `rl` and
`wrd` are the disjoint high and low parts of `idx` and the first two terms
collapse. Four ALU ops become one on a path every thread walks `WPT` times
whether or not its word holds a candidate. Measured **1.0144 against a
control at 1.0009** over 60 balanced rounds — the only kept item that
reads above its control, and still only just. The DECODE is untouched, and
G16 now pins encode against decode over every tile shape `logw = 0..10`
rather than arguing the identity.

**The wheel cache is keyed on the effective `w` vector, not on `n`.** The
wheel depends on the filter only through `w(q,n,b) = min(n, ord_q(b))`, so
once `n` passes every ord below `p1` the table stops changing: at
`b = 4, p1 = 29` the largest is `ord_29(4) = 14`, and `wheel(n, 4, 29)` is
**byte-identical for every n >= 14**. Keyed on `n`, every discovery
rebuilt 23.6 million residues for a table already in hand. Base 2 at
`p1 = 41` genuinely changes until `n >= 36` (`ord_37(2) = 36`), which is
why the key is the vector and not a per-base special case. G8 pins both
halves.

Together with `crv`, what a discovery costs in GPU idle:

| | device tables | engine rebuild at the next filter |
|---|---|---|
| base 4, `n = 21 -> 22` | 855 -> **495 MiB** | 20.0 -> **11.1 s** |
| base 2, `n = 20 -> 21` | 1340 -> **652 MiB** | 26.6 -> **13.2 s** |

`plane_shifts` over 23.6M residues x 4 groups was 8.5 s of every rebuild
on its own. It stays in the module as the host-side reference G16 checks
the kernel's constant and expression against.

### End to end, HEAD against this pass

Paired in ONE process with both engines alive, streams compared every
round, and a byte-identical control arm in the same run:

| | HEAD | new | control (== new) | reading |
|---|---|---|---|---|
| base 4, `n = 21`, 60 rounds | 1.0000 | 1.0033 | 0.9947 | **1.00** |
| base 2, `n = 20`, 39 rounds | 1.0000 | 1.0113 | 1.0289 | **1.02** |

The control arms differ from their own twin by 0.9% and 1.8%, which is the
resolution. **The honest statement is that this pass is throughput-neutral
on both families**, and what it delivers is 360/688 MiB, 9/13 seconds per
discovery, and the four declines above with their prices.

### Settled by static argument, so nobody re-opens them

Three items that need no measurement and are recorded so they stay closed:

- **`ng = 3` at `p2 = 103` is architecturally impossible**, not merely
  expensive. It needs ~1.9 GB per plane, past both `PLANE_TOTAL_MAX` and
  the **u32 bit index** the kernel uses to address `gbits`, which caps all
  planes together at 512 MiB. `build_planes` already refuses on both.
- **Early-exiting the 4th plane load when the mask is already zero never
  fires.** 61% of individual words are dead after three groups, but the
  branch is warp-wide and `P(all 32 lanes dead) ~ 8e-7`. This is the same
  arithmetic that made the saturation guard 0.818x: per-lane redundancy is
  not warp-level redundancy.
- **The kill bitmap's 2x doubling (24 MiB) is free, not a cache cost.**
  99% of all tests land in the first **101 units = 0.05 MiB**; the other
  48 MiB is cold. The hot working set is the 27.6 MiB of planes plus
  ~0.2 MiB of bitmap, so "the working set now exceeds L2" is **FALSE** and
  the doubling is not a thing to undo.

### The termination test, re-derived (OPTIMIZATION.md 3.1)

Shares are the ablation above, on the production configuration at the live
cursor. Every verdict here was re-derived against THIS split, not
inherited from the one it replaces — the previous table's rows were
written against a profile that no longer exists.

| phase | share | verdict |
|---|---|---|
| generation — the plane reads | 38.1% | **bound by the latency of the first touch, established by four failed attacks on the load count** (64-bit words 0.90x, saturation guard 0.818x, locality-ordered residues ~1.00, warp shuffle **0.773x**) and confirmed positively by the duplication arms: a cache-warm extra pass costs 20.4% where the first costs 38.1%. The plane COUNT is minimised by the budget (2^28) and by `pick_p2`. No lever left that this log can name |
| compaction rounds, in the block | 25.6% | **at its schedule optimum, newly re-measured.** The chain starts at 0.99 candidates per thread and falls to 0.10 by round 4, which looks like the argument for handing over earlier — and `tail_surv` 0.15/0.20 measure inside the control band while 0.03/0.05 are clearly worse. The boundary is where it should be. UNSEARCHED: whether the last two rounds, which run on 34 and 13 items against 128 threads, should exist at all as ROUNDS rather than as a shorter chain |
| extract & queue | 16.1% | **five times the modelled figure, and now the phase with the most unexplained cost.** `key0` was four ALU ops and is now one (1.014). What remains is a five-step shuffle prefix scan per thread and an `ffs` loop over the 12% of words that are non-empty. The scan is charged per THREAD, not per candidate, so it does not shrink with the wheel. This is the row to attack next |
| prologue — `res` + the plane shift | 8.3% | **`crv` removed (neutral, -360/-688 MiB) and the group switch removed with it** (base 2: 0.982 -> 1.020). What is left is one `res` read plus `NG` straight-line plane shifts per block |
| block launch — an empty kernel at this grid | 6.2% | **UNSEARCHED, and it was not in the previous table at all.** A launch dispatches 2.95M blocks of 1024 work items; an empty kernel over that grid is 2.0 ms of a 32.7 ms launch. The knob is `TPB * WPT`, last swept at 1024 work items — but that sweep was reading throughput, and it could not separate this cost from occupancy. Bigger blocks need `mine[WPT]` in registers, which is why `WPT = 16` reads 0.982 |
| tail kernel | 5.7% | **optimized**, and a third of the share the previous table gave it |
| tail-queue push | 0.7% | negligible |

Two rows carry named work: `extract & queue` at 16.1%, and the 6.2% block
launch that nothing has ever looked at. Neither is a certification of
completion — but both are now under the 11% the harness can resolve, which
is itself the finding: **the next real gain on this engine will not be
visible to this measurement setup.** A pass that wants to move it needs a
tighter clock than paired wall time on a desktop card, or a change big
enough not to need one.

## 2026-09-01 — the fourth campaign: 92% device, and the A/B's absolute column is 1.5x low

No engine work in this entry. It records what the campaign that found
A130003 `a(21)` measured, because two of the numbers above are predictions
it tested.

**The two passes' combined claim held, and then some.** The base-4 campaign
that found `a(21)` swept `2.77×10²⁰` of line in 67.93 h of sweep clock for
an end-to-end **`1.13×10¹⁵ m/s`** — **7.97×** the 17-hour campaign that
found `a(19)` and `a(20)` at `1.42×10¹⁴`. The two passes predicted
`3.47 × 1.537 = 5.33×` between them; the balance is the filter, which rose
from 19/20 to 21 over the same stretch, and a higher filter is faster here
(`4.34 / 4.90 / 5.32 ×10¹⁴` at `n = 19 / 20 / 21`, BENCHMARKS.md). Those
two together price at `6.5×` against `7.97×` measured, so a residual of
about 1.2× is unattributed and is left that way rather than assigned to the
nearest available cause.

**The campaign is 92% device, measured rather than modelled.** The
end-to-end rate above comes from the checkpoint (`elapsed` against swept
`m`), so it was checked against the engine directly: a bare device loop at
the production configuration, eight launches timed at each end of the
window the campaign actually swept, measures

| height | line rate | per launch |
|---|---|---|
| `m ≈ 8.95×10¹⁸` (the resume cursor) | `1.203×10¹⁵ m/s` | 22.0 ms |
| `m ≈ 2.85×10²⁰` (at the find) | `1.243×10¹⁵ m/s` | 21.3 ms |

The campaign ran at **92%** of that, flat across a 32× range of height. The
missing 8% is the whole host side — the classification pool, the checkpoint
writes, the verifications — which settles the question rule 5c asks: on
this family, at this configuration, **there is no campaign-level lever
left**. The 3.47× that the ladder cache bought was the last one, and what
remains is the kernel, where the termination test above says the next gain
is below what this measurement setup can resolve.

**And the A/B harness's absolute column is 1.5x low.** `7.92×10¹⁴ m/s` is
what the paired arm reports for this exact configuration, against
`1.20×10¹⁵` measured on a bare loop. That is the harness: it runs both
engines alive in one process and alternates arms, which is precisely what
OPTIMIZATION.md Rule 3 asks for — a stable **ratio** under an ambient load
that moves absolutes by tens of percent — and its ratios have now predicted
two campaigns correctly. The error is only in reading a throughput off it.
Two things follow, and they are the reason this is written down: a campaign
that beats the A/B is not an anomaly needing an explanation, and any
projection built by discounting the A/B's absolute by a device share is
conservative twice over. Both of the last two campaigns beat such a
projection (1.43× at base 2, 1.38× at base 4); one cause explains both.

**`score.py` demonstrated the same thing on itself in the same session, and
it is in this repository's git history where anyone can check it.** The
engine is byte-identical between the 2026-08-28 commit and this one — no
`.py` file changed — and `SCORE` reads **1,045,694,664** there against
**693,874,911** here, a **1.51×** swing, with all five frozen fingerprints
reproducing on both runs. That is the whole argument for fingerprints: the
invariant is the survivor stream, the number beside it is a measurement of
a busy desktop card on a particular afternoon. A SCORE that moves without a
fingerprint moving is not a regression, and neither is one that improves.

## Priced and not done

- ~~**A second wheel level below the plane wheel.**~~ SETTLED 2026-08-27,
  and against its own reasoning: raising `p1` does NOT buy what the planes
  buy, because the planes leave `R/W` alone and `p1` halves it. Base 2 took
  the step (37 -> 41, 1.398x) and paid the cursor churn, which `adopt`
  handles. The factored two-level table that would remove `RES_MAX`
  entirely is priced and declined above.
- **A deeper sieve (`q2` above 65536).** The classification host cost is
  about a tenth of one core at the v2 rate, so nothing is host-bound and a
  deeper sieve would buy nothing the campaign can spend. Re-price if the
  survivor path ever becomes the constraint.
- **Overlapping the host's per-launch table update with the device.** The
  update is ~0.2 ms against a ~27 ms production launch — 0.7%, and the
  double buffer would have to be right across the interrupt path. Priced,
  declined, and the price is written down.
- ~~**`b = 2`'s launch size against its tail queue.**~~ SETTLED 2026-08-27:
  `_pick_launch` now derives against the tail queue itself, so neither
  family needs a per-base override and both land on their measured
  optimum (4,096 and 2,048).
- **The extract stage's warp scan** — now re-measured at **16.1%**, five
  times what `model_cost` prices it at, and the largest phase with no
  verdict. `key0` took four ALU ops out of it for 1.014; the five-step
  shuffle prefix scan is charged per THREAD rather than per candidate, so
  it does not shrink as the wheel deepens. This is the row to attack next.
- **Block dispatch, 6.2% of a launch** (2.95M blocks; an empty kernel over
  that grid is 2.0 ms of 32.7 ms). Never measured before this pass and not
  in any earlier phase table. The knob is `TPB * WPT`, and the reason it
  cannot simply go up is `mine[WPT]` in registers — `WPT = 16` reads 0.982.
  Unsearched.
- **A cost-model term for what scales with the BLOCK COUNT.** `GEN_W`,
  `EXTRACT` and `ROUNDC` price only per-residue and per-candidate work, so
  `model_cost` cannot see 14.5% of the launch. `pick_p2` trades the terms
  it has and lands inside its measured plateau, so this is not urgent —
  but it is why the phase table in this file must come from ablation.
- **A tighter clock.** The harness resolves +-11% per round and about
  +-0.6% on a 60-round median (measured, above). Every remaining named
  item is smaller than that. A pass that wants to move this engine needs
  either a better measurement than paired wall time on a desktop card, or
  a change large enough not to need one.

## Declined

Everything in "Rejected, with numbers" above, each with the measurement
that settled it, plus the three items settled by static argument in the
2026-08-27 second pass (`ng = 3` at `p2 = 103`, the early-exit plane load,
and the kill bitmap's doubling). Nothing has been declined here on a
projection.
