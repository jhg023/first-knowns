# OPTIMIZATION — how to make a hunt fast without making it wrong

> **Authorship disclaimer:** As with every project here, this document and
> all the code it describes were authored by **Claude (Anthropic's AI)** at
> the repository owner's direction.

Every project in this repository is a search whose value depends on two
things at once: it has to be **fast** (or the frontier never moves) and it
has to be **right** (or the frontier is a fiction). Those pull against each
other, and the whole point of the gate discipline in
[CONVENTIONS.md](CONVENTIONS.md) is to let you push hard on speed without
being able to quietly break correctness.

This file is the companion to that: the *process* for optimizing a hunt,
and a catalogue of the optimizations that have actually paid, with the
measured numbers and — just as important — the ones that did not.

Case study throughout: `euler-prime-runs`, whose engine went from 5.5×10¹⁴
to ~1.07×10¹⁶ p/s — **~19x**, of which 14.1x was measured in production
from the restructure and ×1.374 came from a wider wheel *plus the two
tuning constants that change invalidated* — with a survivor stream that is
bit-identical to the engine it replaced. See that project's
`OPTIMIZATION_LOG.md` for the full ledger.

> **Read this first.** The recurring failure here is not a bad
> optimization — it is a review that **stops too early** and reports "not
> much left" on code that still has 16x in it. It has happened more than
> once. The countermeasures are [Rule 1](#rule-1-measure-the-split-before-you-optimize-anything)
> (measure, never infer), [Rule 5](#rule-5-you-may-not-stop-because-you-ran-out-of-ideas)
> (why one pass structurally under-finds), and above all
> [Part 3, the termination test](#part-3--the-termination-test): you are
> done when every phase above 5% has an optimization, a named roofline, or
> a structural proof of optimality — **not** when you run out of ideas.
> Speedups here are products of several unexciting-looking factors, so
> "nothing big left" is compatible with 10x remaining.

---

## Part 1 — The process

### Rule 0: the gates come first, and they are not negotiable

Optimization in this repo is only meaningful because of a specific
property: **the fast engine must produce the identical stream to the slow
one, and there is a gate that proves it.** Before optimizing anything,
make sure you have:

- a frozen **work fingerprint** (exact result count + checksum on a fixed
  window) that any change must reproduce bit-for-bit;
- a **parity gate** against an independent implementation on *populated*
  windows;
- the engine you are replacing, **still runnable, for the duration of the
  change**, so "same stream" is something you demonstrate rather than
  assert.

If you have those, you can be aggressive. If you don't, build them first —
every hour spent here is repaid the first time a "harmless" change turns
out not to be.

**On that third item: it is a scaffold, not a permanent fixture.** Keep the old engine
while you migrate, add a gate that pins new against old bit-for-bit, get it
green, and commit that. **Then delete it.** The proof lives in the git
history at the commit where the gate passed; a dead module in the working
tree is worse than no module, because the tree stops being the answer to
"what would run if someone started this from zero" — and that question has
to have exactly one answer.

What must survive the deletion is the *independent* reference — the slow,
differently-written implementation the fast one is gated against (here: the
numpy engine against the CUDA one). That is not a previous version, it is
the other half of the parity gate, and it is permanent. When retiring an
engine, check what its gates were carrying and re-point that coverage
somewhere before it goes; if a gate's only purpose was comparing old to new,
it retires with the engine, and the docs should say so rather than leaving a
gate number dangling.

### Rule 1: measure the split before you optimize anything

The single highest-value action is usually a two-minute measurement, not a
code change.

In `euler-prime-runs` the optimization log confidently stated that the cold
path was 80% of runtime. It had been true — of an engine design that had
since been replaced. Nobody re-measured. The stale note also contained an
arithmetic impossibility (a per-candidate cost that implied 127 ms of work
inside a 96 ms launch), which is the kind of thing that survives for months
because nobody multiplies it out. CUDA events around the two kernels took
two minutes and showed the *hot* kernel at **83.4%** — the opposite
conclusion, and it redirected the entire effort.

Practical form: wrap each phase in timers, print the percentages, and check
that the phases sum to the wall-clock. If they don't, you don't understand
the pipeline yet.

**Corollary — re-measure after every accepted change.** Optima move, and in
the case study they moved **four times in one session**:

| constant | moved | why |
|----------|-------|-----|
| sieve depth | 28 | original balance |
| | -> 24 | compaction rounds made stage 1b ~3.5x cheaper, so it was worth handing work back to it |
| | -> 28 | a wider wheel pushed the sieve's prime range up, costing it its strongest killer |
| round size | 8 -> 16 | the wheel shifted work into stage 1b (17% -> 35% of GPU time) |

Three of the four were worth 1.06x–1.13x each and two moved in the direction
opposite to the obvious guess. Individually they look like rounding error;
together they are **1.3x**, and every one of them is pure loss if nobody
re-sweeps. Any constant tuned before a structural change is stale after it.

### Rule 2: build a cost model, then let it be wrong

Write down the instruction/memory cost per unit of work and see whether it
explains the measured time. This is worth doing even though it will
sometimes mislead you, because it tells you *where the budget goes*.

In the case study the model said: ~241 warp-instruction slots per
warp-period, of which 48 went to unconditionally stepping state for primes
the average candidate never reached, and the early-exit test chain cost 9.2
warp-iterations against a per-lane mean of 2.2 — a 4.2x divergence tax. Both
numbers pointed at the same restructure, and both were confirmed.

Then it mispredicted, twice, in opposite directions:

- widening the pattern word to 128 bits "should" have halved the gather
  count. It ran at **0.25x**.
- warp-aggregating a single-address atomic "should" have mattered because
  the rate was near the hardware limit. The whole queue push turned out to
  be **10%** of the kernel.

Use the model to generate candidates and to price things you decide *not*
to do. Never use it as evidence that something worked.

### Rule 3: measure paired and interleaved, or don't bother

Ambient load on a desktop GPU moves absolute rates by up to ~30% minute to
minute. A sequential sweep will hand you cliffs that do not exist: one
NINC sweep in the case study reported a 31% jump between adjacent values,
which vanished under interleaving.

The discipline that works:

- every round measures **every** candidate configuration back to back;
- report the **median per configuration** over rounds, plus min/max;
- the **ratio** is the stable quantity, not the absolute rate — quote
  ratios when comparing across sessions or engine generations;
- **re-check the fingerprint on every single run.** A measurement from a
  configuration that got the wrong answer is not a data point.

### Rule 4: separate the engine change from the shape change

If a change alters both how the engine works and how the benchmark is
driven, report them separately or you will fool yourself.

Case study: the headline SCORE128 ratio was 18.3x, but the frozen window is
77,285 periods, and raising the launch size to 131,072 made the whole
window a *single launch* — flattering the number. Measured properly:
**10.29x from the engine** at an unchanged launch shape, ×1.395 from the
launch size in steady state = **~14x sustained**. Production later came in
at 14.1x. The 18.3x was real but not transferable, and saying so is the
difference between a benchmark and a claim.

### Rule 5: you may not stop because you ran out of ideas

**This is the rule that gets broken, and it is expensive.** The observed
failure pattern, more than once: an optimization pass reports "nothing much
left here", the same code is examined again later, and a ~16x speedup falls
out. Not because the second pass was cleverer — because the first one
stopped searching before it had earned the right to.

"I don't see any more optimizations" is **not a finding**. It is a
statement about the search, not about the code. Absence of ideas is not
evidence of absence of headroom, and it must never be reported as if it
were. See [Part 3](#part-3--the-termination-test) for what you have to be
able to show before you are allowed to say "done".

Why a single pass structurally under-finds — three compounding reasons:

1. **The profile moves under you.** Every accepted change redistributes the
   time, and options that were worthless become dominant. In the case
   study the stage-1b compaction round was a footnote worth "maybe, if the
   cold path turns out to matter" *before* the sieve landed; afterwards it
   was **1.684x**, the second-biggest win of the day. A pass that ranks
   opportunities against the *current* profile cannot see it.
2. **The total is a product, not a max.** 4.47 × 1.684 × 1.395 × 1.058 ≈
   11x from four changes, none of which is the "one big win". Stopping
   after the biggest single item leaves most of the speedup on the table,
   and each factor individually looks unexciting enough to skip.
3. **Optima move.** Constants re-tuned after a structural change gave
   another 1.058x, and the *direction* was counter-intuitive (a tuning
   parameter went **down**, not up). Nobody finds that by inspection.

So the process is inherently multi-round: measure, change one thing,
re-measure everything, repeat. **Plan for rounds until the profile is flat**
rather than for "an optimization pass".

### Rule 5a: an unmeasured review is a hypothesis list, not a finding

The case study's first pass was deliberately read-only, because a hunt was
running and benchmarking would have stolen GPU cycles. That was a
reasonable call, and it produced a *bad* review — not wrong exactly, but
mis-ranked and under-scoped in a way that measurement fixed within minutes:

| first pass (model-based) | reality (measured) |
|---|---|
| ranked a register-caching tweak **first** at 1.5–1.9x | never implemented; superseded before it was worth doing |
| ranked the bit-sieve **second** at "3–5x" | it was the main event, **4.47x**, and should have led |
| compaction rounds: a footnote, "only if the cold path measures large" | **1.684x** |
| launch size: bundled into "cheap plumbing, 1.0–1.3x" | **1.395x** |
| "the atomic could be at the hardware limit" | 10% of the kernel — a non-issue |
| wider pattern word: predicted a win | **0.25x** |

The mechanism of the error is worth naming: the model had a free parameter
(gather-replay cost), and it was tuned until the model matched the measured
total. A model fitted to the number it is trying to explain has no
predictive power left, and it will confidently rank the wrong things.

If you cannot measure yet, say so explicitly, label the output a
**hypothesis list with estimated ceilings**, and ask for a measurement
window. Do not let it read as a conclusion. Ten minutes of profiling
outranks any amount of code reading.

### Rule 5b: report priced options; the stop decision is the owner's

The case study's first pass ended with "worth doing at all? optimization
won't change that outcome much" — reasoning from the *then-current* hunt
plan, before any measurement, and it was wrong. A 14x speedup does not just
finish the current leg sooner; it changes which legs are worth running at
all (here: the default depth went from 10²¹ to 5×10²¹, and a(20) moved from
"decades of single-GPU wall" to a season).

The asymmetry that makes under-searching feel safe: **wasted optimization
effort is visible, a missed optimization is invisible.** You simply run 14x
slower forever and nobody sees the counterfactual. Correct for it
deliberately by biasing toward searching more than feels necessary, and by
never silently dropping a candidate.

So: enumerate every candidate with a price and a risk, recommend an order,
and let the owner decide what to spend. "Probably not worth it" is a
recommendation, never a reason to leave an item out of the list.

Genuine stopping *is* legitimate — but only against **evidence**, and the
bar is higher than it looks. The stop I originally offered as the good
example in this very section was: "the wider wheel is worth ~1.45x, declined
because the offset table is 4.3 GB at the parameters the gate battery runs,
so production would use a configuration the parity gates cannot exercise."

It was wrong, and it was later implemented for 1.212x (§2.8). The blocker
was real at exactly one parameter and dissolved into a dozen lines of budget
logic; the rest of the reason did not survive re-reading. So the cautionary
tale and the worked example are the same item.

What a genuine decline looks like, from the same session:

- **the wider pattern word: measured 0.25x.** A number, from running it.
- **warp-aggregating the queue atomic: the whole push is 10% of the
  kernel**, established by compiling a variant with the push deleted and
  timing it. Priced in five minutes, declined on the price.
- **compacting the rare-and-deep final stage: ~0 by construction**, because
  its per-warp cost already equals the perfectly-packed cost.

The pattern: a real decline cites a measurement or a structural argument,
not a projection and not an obstacle you have not tried to remove. If your
reason is "it would be hard" or "it might break X", that is a task, not a
verdict.

### Rule 6: write down what failed

The `OPTIMIZATION_LOG.md` in each project records every attempt with its
measurement and verdict, **including the rejects and the things rejected
without implementation, with their prices.** This is the artifact that stops
the next person (or the next model) from re-running a dead end, and it is
the only reason anyone can trust a claim like "the atomic is not the
bottleneck."

Also write down the *bugs the gates caught*. In the case study, two came
from the A/B harness rather than the kernels — a tuning knob changed after
construction desynced a compiled kernel from its launch geometry, and a
buffer went unallocated. The fingerprint and a memory fault caught them
immediately. The lesson recorded: tuning scaffolding needs the same
discipline as the arithmetic.

---

## Part 2 — The catalogue

Optimizations that have paid, ordered roughly by how much they returned.
Each is described so it can be recognised in a *new* problem, not just
recalled in this one.

### 2.1 Invert the loop: test many candidates per unit of work

**Recognise it when:** the inner loop walks candidates one at a time,
maintaining per-candidate state, and the per-candidate test is a lookup
whose result is a function of a small amount of state.

The dominant win in the case study (**4.47x** on its own). A sieve that
asked "is *this* candidate killed by prime q?" became one that asked "which
of the next 64 candidates are killed by prime q?" — because the answer for a
whole block is a function of (q, block-start residue) alone, so it can be
precomputed into a bitmask on the host and OR-ed in one instruction.

The general shape: **find the quantity your inner loop recomputes per
candidate that is actually periodic, tabulate it, and process a block per
step.** Then survivors come out of the complement of the accumulator with a
find-first-set loop.

What it buys, all at once:
- state maintenance drops by the block width (64x here);
- table lookups drop by roughly the block width over the mean test depth;
- the inner loop becomes **branch-free over candidates**, which kills
  divergence (below) rather than merely reducing it.

Costs to check: table size must stay cache-resident, and the block
boundaries at the edges of a window need masking — which is exactly where
the bugs live, so gate those cases explicitly.

### 2.2 Kill warp divergence with iterated compaction

**Recognise it when:** lanes in a warp run an early-exit loop with a
long tail — the mean exit depth is small but the *maximum over the warp* is
large, so most lanes sit idle while one grinds on.

Worth **1.684x** in the case study. The stage with mean exit depth 13.85 had
a warp-max of 80.4 — a 5.8x tax. Fix: process the loop in **rounds** of ~8
steps, and between rounds compact the survivors into a new queue so every
round restarts with all lanes alive. Keep the counts on the device so the
rounds chain without host round-trips.

The diagnostic is a one-liner you can compute before writing any code:
mean = Σ S(j), warp-max = Σ [1 − (1 − S(j))³²], where S(j) is survival to
depth j. The ratio is your available win.

**Know when it does not apply.** In the same pipeline, the final stage had
mean depth 109 but was entered by only 5.7×10⁻³ of the queue — so at most
one lane per warp was ever in it, and the per-warp cost already equalled the
perfectly-packed cost. There was no divergence to recover and compacting it
would have gained nothing. Compaction pays where *many* lanes are active
with *different* exit depths; rare-and-deep stages are already optimal.

### 2.3 Two-phase compaction: split hot from cold

**Recognise it when:** a small fraction of candidates trigger a long tail of
extra work inside the same kernel, serialising the warp.

The predecessor of 2.2, and the earlier generation's big win (0.77x → 1.13x
relative to a simpler engine). Hot kernel does the cheap common test and
pushes survivors to a queue; a second kernel processes the queue one item
per thread with every lane busy. 2.2 is this idea applied repeatedly.

### 2.4 Make the batch bigger

**Recognise it when:** per-launch fixed costs (kernel ramp, tail effect,
host round-trips) are a visible fraction of a short kernel.

Worth **1.395x** in steady state. Cheap to try, so try it early — but
measure it on a window wide enough to need several launches, or you are
measuring the launch away entirely (Rule 4).

### 2.5 Bake constants into generated kernel source

**Recognise it when:** the kernel reads loop-invariant values from arrays
that are identical in every thread, burning registers to hold them.

Generate the kernel text with the moduli, magic numbers, and table offsets
as literals. Costs nothing, frees registers (3 per tracked prime in the case
study), and lets the compiler fold addressing arithmetic. Worth doing as
part of any restructure. Keep the generator's output printable so a human
can read the emitted source.

### 2.6 Exact, analytic buffer sizing

**Recognise it when:** an intermediate queue is sized by guesswork with a
fudge factor, and overflow is either fatal or — worse — silent.

Survival through a sieve stage is a deterministic product over the primes
involved. Compute it on the host and size the buffer from it: the case
study's analytic rate matched the measured occupancy to four significant
figures (5.6940e-04 vs 5.6943e-04). Then buffers can grow on demand, small
test windows stop reserving production-sized memory, and the overflow check
becomes a real invariant rather than a hope.

Related invariant worth engineering: make the *impossible* case impossible.
Sizing both ping-pong queues identically means "each round's output ≤ its
input ≤ capacity", so a mid-chain overflow — which would silently lose
results — cannot occur, and only the first stage needs checking.

### 2.7 One engine for the whole range

**Recognise it when:** you are about to write a second engine because
values outgrew a machine word.

Do not. Carry each candidate as the pair `(k, off)` with `value = k·M +
off`, and every modular test becomes `((k mod q)·(M mod q) + off mod q) mod
q`, which stays single-word-safe far beyond the point where the value
itself does not. The exact value only ever needs to exist on the host.

The case study learned this the expensive way: it built a u64 engine, hit
2⁶⁴, built a second engine, and then ran two phases, two checkpoints, two
canary preludes, a deliberately re-covered seam and an `--engine` flag for
weeks before unifying — during which the *default* invocation silently ran
the capped engine. The (k, off) representation was valid from the beginning.
**Start here**, pick the ceiling from your primality-test validity bound,
enforce it as a constant, and gate at it.

Unifying afterwards is worth doing anyway, and it pays twice. Measuring the
same span at two heights becomes a free height-flatness check — though in
the case study that check turned out to be much weaker than it first looked:
run-to-run variance on one configuration exceeded every gap between the two
heights, so it could not have detected a 20% tilt. The tight-looking first
capture was luck quoted as precision (BENCHMARKS.md carries the correction). And the verification leg gets *stronger*
rather than weaker: the alternate-alignment re-sieve had been running a
different wheel only below the old cap, because that happened to be the
engine available there; with one engine it runs a different wheel at every
height by choice.

Retire the superseded engines when you unify (Rule 0): the moment there is
only one code path, "what runs if you start from zero" and "what is in the
tree" are the same statement, which is the actual goal.

### 2.8 Wheels, and their limit

**Recognise it when:** candidate generation dominates and the wheel's prime
set is smaller than it could be.

Folding one more prime q into the wheel generates a factor of ~q/(q−r)
fewer candidates for a mathematically identical result set — so the frozen
fingerprint still applies, which makes it unusually safe.

The limit is memory: the offset table size depends on the search parameters,
and in the case study the table that is a comfortable 240 MB at the
production parameter is 4.3 GB at the smallest parameter the gate battery
runs on. The fix is a **budget**, not a veto — select the largest wheel whose
table fits, per parameter, so production gets the big wheel and the small-n
gates fall back. Worth **1.212x** here, once the sieve depth was re-tuned
(below).

I first declined this at "~1.45x, blocked by gate coverage", reasoning that
production would run a wheel the parity gates could not exercise. That was
wrong twice over, and both errors are instructive. The gates *do* exercise
the production wheel — the parity gate runs four cases at the production
parameter — and two other gates already ran a *different* wheel than
production on purpose. So the blocker was memory at one parameter, which a
budget solves. **A decline is only as good as its stated reason, and stated
reasons need re-examining, not inheriting.**

The second error was the estimate. 2.07x fewer candidates predicted ~1.45x;
the measured result was **1.121x** until the sieve depth was re-swept.
Folding a prime into the wheel *removes it from the sieve*, so the sieve's
range shifts upward and it loses its strongest killer — here 31, which kills
52% of candidates, replaced at the top end by 149, which kills 11%. The queue
per unit of work grew 1.41x and ate most of the win. Raising the sieve depth
from 24 to 28 primes recovered it: **1.212x**. This is Rule 1's corollary
biting for the third time in one session — a wheel change is a structural
change, and every constant tuned around it was stale the moment it landed.

### 2.9 Things that did not pay (measured, in this codebase)

| attempt | result | why it was tempting |
|---------|--------|---------------------|
| wider pattern word (128/256-bit) | **0.25x / 0.31x** | halves gather count; but the multi-word accumulator's data-dependent extraction defeats it |
| warp-aggregated single-address atomic | not worth doing: whole push is **10%** of the kernel | the raw atomic rate looked close to the hardware limit |
| removing per-launch host syncs | **0.2%** of GPU time | "obviously" a pipeline bubble |
| compacting the rare-and-deep final stage | ~0 by analysis | it is 24% of a phase and 109 steps deep, so it looks like the tail |
| shared memory for lookup tables | worse at every block size | tables are small and L2-resident already |
| larger thread blocks (512, 1024) | worse | more parallelism per block "should" help |

The first four are the instructive ones: each was priced with a
five-minute experiment (compile a variant with the suspect work deleted and
time it) rather than an afternoon of implementation.

---

## Part 3 — The termination test

You are finished optimizing when you can produce this table, **not** when
you run out of ideas. Anything less and the honest report is "I have not
finished searching", with what remains unexamined.

### 3.1 Every phase is accounted for

Measure the phase split so the phases sum to wall-clock, then for **every
phase above 5%** write one line of one of these three kinds:

- **an optimization**, with a measured or ablation-priced ratio;
- **a roofline**, i.e. this phase is within ~2x of a hardware limit you
  name and computed — instruction throughput, memory bandwidth, atomic
  throughput, occupancy;
- **a structural argument for optimality**, e.g. "no divergence to recover:
  entered by 5.7e-3 of the queue, so at most one lane per warp is active
  and the per-warp cost already equals the perfectly-packed cost".

A phase with none of the three is **unsearched, not optimal**. That is the
whole test. "It looks tight" is not one of the three.

Worked example — the case study's final state, which is what let it stop:

| phase | share | verdict |
|-------|-------|---------|
| bit-sieve stage 1a | 48.1% | ~90% pattern work by ablation (deleting the queue push moved it only 10%); the candidate-count lever was taken (§2.8, 1.212x), and the next wheel prime (37) needs a 6.0e8-offset table, ~16x over budget |
| stage-1b compaction rounds | 34.6% | divergence recovered 5.8x -> ~1x. Grew from 17.3% when the wheel moved work here, so the round size was re-swept against the new balance: peak moved 8 -> 16, worth **1.134x**. That factor was found *because this row visibly grew* — nothing looked broken, the engine was simply leaving 13% on the floor |
| cold stage-2 kernel | 17.3% | structurally optimal: rare-and-deep, so at most one lane per warp is active and the per-warp cost already equals the perfectly-packed cost |
| host + syncs | <1% | measured 0.2%, priced and declined |

The table earned its keep immediately: filling in the rounds row exposed a
1.134x that no amount of staring at the code would have suggested, because
the code was not wrong — it was tuned for a balance that no longer existed.
That is the whole argument for a per-phase verdict over a judgement call.

And note what the table still does *not* say: "done". The shares above are
from the profile *before* the round-size change, so they have already moved
again, and the next re-profile is the next round's first action. The table's
job is to keep remaining work **visible and priced**, not to certify
completion.

### 3.2 Every catalogue entry has been applied to every phase

Do not rely on inspiration; sweep [Part 2](#part-2--the-catalogue)
mechanically. For each phase × each transformation, the answer is "tried it,
here is the ratio", "does not apply, here is why", or "priced at X,
declined because Y". Inspiration finds the first idea; the checklist finds
the fourth one, and the fourth one is where the product 1.68 × 1.40 × 1.06
lives.

### 3.3 The cheap ablation has been run for every suspicion

Before implementing anything, price it by **deleting the suspect work and
timing the result** — a deliberately-wrong kernel is a five-minute
experiment and it is definitive. This is how the case study established
that the atomic was 10% (not the bottleneck it looked like) without writing
any aggregation code, and it is how "I think X is slow" becomes a number.

### 3.4 The constants have been re-swept since the last structural change

If any tuning constant was last swept before the most recent accepted
change, it is stale and the search is not complete. Re-sweep, interleaved.
Expect directions to surprise you.

### 3.5 One more round found nothing

The profile is flat, a full catalogue sweep produced no new priced
candidate, and the constants are fresh. **Then** you may stop — and the
report is the table above plus the declined items with their prices, so the
next pass starts from evidence instead of from scratch.

---

## Part 4 — Checklist for a new project

Design, before writing the engine:

- [ ] candidates carried as `(k, off)`, single-word-safe past the value's
      word size (§2.7); ceiling derived from the primality bound and
      enforced as a constant
- [ ] the largest wheel whose offset table fits at **every** parameter the
      gates will run, not just the production one (§2.8)
- [ ] frozen benchmark shape + work fingerprint from the first gated engine
- [ ] previous engine versions retained as parity references

Then, in this order:

- [ ] measure the phase split; confirm the phases sum to wall-clock (Rule 1)
- [ ] cost-model the dominant phase; compute mean vs warp-max exit depth
      (Rule 2, §2.2)
- [ ] can the inner loop be inverted to process a block per step? (§2.1)
- [ ] compaction: split hot/cold, then iterate it in rounds (§2.3, §2.2)
- [ ] cheap knobs: batch size, baked constants, buffer sizing (§2.4–2.6)
- [ ] re-sweep every tuning constant — the optima moved (Rule 1 corollary)
- [ ] price what you are not doing, and write down why (Rules 5, 6)

Before committing, per CONVENTIONS:

- [ ] full gate battery green, **including a new gate for the new
      mechanism** — for a block-structured sieve that means the block/window
      boundary cases and the split-equals-whole resume property, on
      *populated* windows
- [ ] frozen fingerprints reproduce bit-for-bit
- [ ] `OPTIMIZATION_LOG.md` updated with attempts, rejects and prices
- [ ] `BENCHMARKS.md` ledger row with the SCORE, and the paired ratio if the
      benchmark shape changed
- [ ] SCORE in the commit message
