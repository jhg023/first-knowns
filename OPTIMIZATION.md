# OPTIMIZATION — how to make a hunt fast without making it wrong

> **Authorship disclaimer:** This document and all the code it describes
> were authored by **Claude (Anthropic's AI)** at the repository owner's
> direction; the repository as a whole is developed with Claude and with
> ChatGPT through Codex (see README.md).
>
> The review-workflow note below was added by Codex on 2026-10-20.

**Static mathematical review precedes implementation when requested.**
[CODEX_REVIEWS.md](CODEX_REVIEWS.md) defines Codex's independent review
role and the `codex-reviews/` reports. Codex never uses the GPU or runs
project code for a review. The profiling, A/B, and gate requirements in
this document govern Claude's later implementation and validation, not
the creation of a static report. A proved search-space reduction and an
unmeasured runtime hypothesis must remain distinguishable.

Every project in this repository is a search or an exact computation whose
value depends on two things at once: it has to be **fast** (or the frontier
never moves) and it has to be **right** (or the frontier is a fiction). Those pull against each
other, and the whole point of the gate discipline in
[CONVENTIONS.md](CONVENTIONS.md) is to let you push hard on speed without
being able to quietly break correctness.

This file is the companion to that: the *process* for optimizing a hunt,
and a catalogue of the optimizations that have actually paid, with the
measured numbers and — just as important — the ones that did not.

Case study throughout: `euler-prime-runs`, whose engine went from 5.5×10¹⁴
to ~1.7×10¹⁶ p/s — **~32x**, of which 14.1x was measured in production
from the restructure, ×1.374 came from a wider wheel *plus the two tuning
constants that change invalidated*, and ×1.294, ×1.055 then ×1.329 from three
later rounds of small ones — with a survivor stream that is bit-identical to
the engine it replaced. See that project's `OPTIMIZATION_LOG.md` for the full
ledger.

Those last three rounds are worth noticing: each came *after* a session that
had already re-swept every constant and reported the profile flat. The 1.294x
was five changes worth 1.165 / 1.066 / 1.048 / 1.028 / 1.023; the 1.329x was
eight worth 1.084 / 1.058 / 1.043 / 1.037 / 1.023 / 1.020 / 1.019 / 1.010 —
not one of which looked like anything on its own, and two of which were
re-sweeps of constants that had just been declared optimal.

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
> "nothing big left" is compatible with 10x remaining. And a verdict of
> "roofline" or "floor of this formulation" on an inner loop is not
> admissible until [INNOVATION.md](INNOVATION.md)'s two passes — the
> representation hunt and the instruction-level pass — have been run on
> it: an earlier engine carried that verdict through four sessions with 1.2x
> still in the step.
>
> **And all of it is done at the filter that runs for days**
> ([Rule 0a](#rule-0a-optimize-the-filter-that-runs-for-days-not-the-one-that-closes-in-minutes)),
> never at the opening that closes in minutes: that is where the campaign's
> clock is, and the opening's phase split is a different engine's.

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

### Rule 0a: optimize the filter that runs for days, not the one that closes in minutes

*(Owner directive 2026-10-16, every project; CLAUDE.md rule 3b.)*

A campaign is a sequence of filters, and its clock is not spread evenly
over them: the odds model puts the openings' terms minutes away and the
later ones days or weeks away. What an optimization buys the campaign is
the clock it takes off each filter, `clock(filter) × (1 − 1/speedup)`,
summed — so the filters that run for days carry essentially all of it. At
power-ladders' clocks, 5% on A229626 n = 12 (a 19-day median) is ~22 hours;
50% on A229626 n = 10 (44 seconds) is 15 seconds.

The opening is nevertheless where optimization keeps landing, for reasons
that have nothing to do with the hunt: it is where the cursor sits when a
project is built, it is the filter rule 5g puts a frozen shape at first,
it is fast to measure and short enough for a quick A/B, and it is the
filter the first phase split happened to be taken at. None of those make
it the filter that matters, and **its phase split is not the long filter's
phase split**. A later filter is a different configuration — a longer
window, a wider record, a deeper wheel or sieve, a different survivor
density and a different host load — and the phases move with it.

So, in order:

1. **Name the target.** Per family, the filter carrying the campaign's
   expected clock: the odds model's quantiles divided by the measured rate
   at that filter (the README's clock column), taking the first filter
   whose median clock is a day or more, and weighting by clock where
   several are. Write it at the head of the round in the log.
2. **Measure there, and only there.** Every phase split (Rule 1), Nsight
   Compute profile (Rule 1a), A/B (Rule 3), constant sweep and termination
   table (Part 3) is taken with that filter's PLANNED engine at a height
   inside its search — the model's Q1 or the cursor, never its floor if
   the floor is a different regime. The engine API takes any start, so
   this costs a scratch harness exactly as the opening does, inside rule
   0's five minutes, and never a campaign (CLAUDE.md 0a).
3. **A ratio from a short filter is a hypothesis.** It may suggest what
   to try; it ships when it reproduces at the day-long filter. Every
   number in a log names the filter it was measured at.
4. **The SCORE shape sits at the day-long filter**, so that "optimize
   under the score" optimizes the hunt. The openings keep their frozen
   shapes for rule 5g; the headline is the long filter. Moving an existing
   project's headline there is a shape change, logged with the paired
   ratio in BENCHMARKS.md (§2.13: the owner has made that decision for
   this case).
5. **Price options in the long filter's hours.** A priced, unbuilt lever
   (Rule 5b) states what it is worth at the day-long filter in hours
   saved on that term's expected search, because that is the unit the
   owner decides in.

The short filters are not abandoned: rule 5g still requires the default to
be correct and free of cliffs there, the pool not to bind and the
acceptance test to be run. That is a check, not a target. Per-filter
constants come from the per-filter table, so a short filter loses nothing
a table can save it; where a structural choice cannot be made per filter,
the day-long filter decides and the minutes it costs the short one are
priced and logged.

**The case that wrote it:** power-ladders (2026-10-15) ran rounds 0 to 3,
its Nsight Compute profile and its termination table at A229626 n = 10 —
median clock 44 seconds — with A229627 n = 9 (5 seconds) and A229902
n = 10 (95 seconds) alongside, and froze its SCORE shape there. Its
campaigns' clock is at A229626 a(12) (19 days median, P90 95), A229902
a(12) (35 days, P90 168) and the a(11)s of A229627 and A229630 (2.3 and
2.7 days): a 256-period window rather than 128, a wide record at A229626
n = 12, an eighth of the opening's host load. Those filters' rates were
measured (the project's 5g table); their phase split never was, so the
termination table that project published describes a filter its campaign
leaves in under a minute.

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

**This applies to the scaffolding too, not just the engine.** Asked to speed
up the case study's gate battery, I read the code and produced three
plausible candidates. Timing each gate took two minutes and showed the
battery was *one* gate at 89%, and that one of my three candidates was 0.3%
of the runtime. The fix — parallelising that gate's reference sweeps across
processes, without touching the deliberately-slow reference itself — took the
battery from 9m51s to 1m33s. Anything you run on every change is worth
measuring on the same terms as the thing it measures.

**AND IT APPLIES TO THE CAMPAIGN LOOP, WHICH IS THE ONE NOBODY TIMES.**
Everything above is about the kernel and the battery. The segment loop —
sweep, classify, checkpoint, report progress — sits between them and gets
measured by nobody, because a benchmark measures the engine, a gate
measures correctness, and neither one ever runs a segment.

`shift-ladders` measured its kernel's phase split in exquisite detail and
never once timed a segment. Its campaigns ran at **29% and 41% of their own
kernel** through a 17-hour hunt. The cause was `check_rungs`, rebuilding
the progress ladder from the odds model once per segment: 12 quantile
bisections × 90 steps = **1,080 numerical integrals, 578 ms**, for an
answer that changes only when a term is found. Four fifths of the campaign.
The kernel was 13 ms per launch; the thing sitting beside it was 32 ms; and
every optimization in that project's log until then was aimed at the 13.

The measurement that catches this is not a profiler. It is:

    device seconds per unit of line   vs   WALL-CLOCK seconds per unit of
                                           line, in the campaign's own
                                           configuration, at the campaign's
                                           own filter

If those differ by more than a few percent, the difference is yours to find
and it is not in the kernel. Then time one segment, step by step. See
§2.14, which is that story with the numbers.

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

### Rule 1a: profile the dominant kernel with Nsight Compute — it is installed

The phase split (Rule 1) says WHICH kernel; Nsight Compute (`ncu`, 2025.4
on this machine — `ncu.bat` in its install directory on Windows) says what
that kernel is bound by, instruction by instruction, and it is the
measurement every recent round here started from. Four projects used it
before this section existed, each with its procedure written only in its
own log: plus-two-cliques round 3 (the LSU data pipe at 87% of peak, five
blocks a SM for want of 54 bytes of shared memory), primorial-ladders round
1 (the window and extraction 75% of samples, ~12.5 instructions per
prime-window against a floor of 7.5), polynomial-runs round 2 (seven tenths
of the sieve kernel's code was a never-executed fallback inlined through the
hot path: a warp stalled on instruction fetch once per issued instruction —
moved out of line, 1.05–1.06x), and power-ladders round 2 (the window at
97.8% of the LSU's issue peak; the tail kernel healthy at IPC 2.75).

**Profile a harness, never a campaign** (CLAUDE.md 0a, and Rule 0's five
minutes). The target is twenty lines in the scratchpad that build the
PLANNED engine of the filter in question and run a handful of launches:

    ncu --kernel-name sieve --launch-skip 2 --launch-count 1 --set full \
        -f --export rep  python target.py <repo> <family> <n> 4

`--launch-skip` passes the warm-up launches (the first compiles and fills
the caches); `--launch-count 1` profiles one; `--set full` replays that
launch ~45 times to collect every section, so keep the profiled kernel to
tens of milliseconds and the whole run inside the cap. `--kernel-name
regex:tailround` selects a family of generated kernels. Check `nvidia-smi`
first: a profile on a GPU that is running the owner's hunt measures the
hunt, and steals its time.

**Read it three ways:**

1. `ncu --import rep.ncu-rep --page details` — Speed of Light (which unit
   is near its peak), occupancy and what limits it (registers, shared
   memory, warps), the warp-stall reasons, the memory tables (bank
   conflicts, sectors per request).
2. `--page raw --csv` — every metric by name, for the ones the summary
   rounds away: `sm__inst_executed_pipe_lsu` (LSU issue against its peak),
   `l1tex__data_pipe_lsu_wavefronts_mem_shared` (the shared-memory DATA
   pipe), `smsp__sass_inst_executed_op_shared_ld`, and the
   `smsp__pcsamp_warps_issue_stalled_*` family (MIO throttle = the LSU
   instruction queue is full).
3. `--page source --print-source sass --csv` — per-instruction stall
   samples and execution counts. NVRTC kernels carry no line info, so this
   is SASS only: split it at every `BAR.SYNC` (the phases of a block-
   structured kernel fall between barriers) and count each segment's
   opcodes by FULL name (`LDS` vs `LDS.64` vs `LDS.128` — the width is the
   finding). That census is what showed power-ladders' window reading its
   table a 32-bit word at a time, five loads a prime, because the pairs
   table did not fit.

**What it will tell you wrong, and how to catch it:**

* **A unit near 100% names a candidate bound, not a proven one.** Attack
  it from two directions before believing it (§2.12). power-ladders cut
  the window's shared loads 40% (aligned 64-bit reads: LSU issue 97.8% →
  66.6%) and the rate did not move (0.97–1.0): the selects it added took
  the bound to the ALU and the issue slots, at twelve warps a SM. The
  profile of the CHANGED kernel is what said so.
* **The "Est. Speedup" hints are heuristics.** "Uncoalesced global loads,
  41%" on a gather that hits L1 98% of the time is not 41% of anything;
  measure the ablation (§3.3).
* **A profiled launch is slower than a real one** (clocks are locked and
  the launch is replayed), so compare variants under ncu with each other,
  never with a wall clock; the rate claim is still a paired A/B (Rule 3).
* **The first profile after a kernel change pays the compile** (NVRTC
  into CuPy's cache) — budget for it against the five-minute cap.

### Rule 1b: profile CPU code with timers on the same inputs — there is no `ncu` for the interpreter

Rule 1a is for GPU kernels. A CPU engine — an exact counter in Python,
a host classification pool — gets the same discipline with different
instruments, and the instruments are cheap:

- **the phase split by category**, with timers around every category
  and route on the SAME chosen inputs, so routes are compared paired;
- **representation and allocation measurements** — set against bitset,
  bytearray fill against big-integer construction, cache against no
  cache — each a variant timed on the same inputs with the count
  checked, exactly as a variant kernel is;
- **the end-to-end shape**, which is where process spawn, IPC, ledger
  validation, receipt and checkpoint writes with fsync live; they are
  invisible to an in-process benchmark;
- **peak memory**, measured, not estimated, when a structure scales with
  the universe (a bitset universe over root subsets grows with
  choose(q, r));
- **a worker-count sweep** of the end-to-end pipeline, interleaved, with
  the committed core-seconds beside the wall clock so the parallel
  efficiency is a number and the default pool is chosen from it under
  CONVENTIONS.md "Sizing a hunt".

What it will tell you wrong: a per-call time on a sample of nodes is not
a campaign rate — the per-node cost varies several-fold with the frontier
size within one depth, and a seeded sample over-represents wide branches;
state the sample and its spread with every projection.

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

### Rule 7: a sweep that measures only throughput cannot see a constraint that is not throughput

Every knob is swept against the SCORE, so every knob gets tuned as though
throughput were the only cost. Some are not free in a currency the
benchmark can read — host memory, machine responsiveness, spawn storms,
power transients, thermals, the operator's ability to keep using their
desktop — and the sweep will happily take the extreme end of the range.

dickson-ladders sized its classification pool this way: the sweep read
host/GPU ratios of 1.34 / 0.77 / 0.69 / 0.61 at 16 / 32 / 48 / 60 workers,
concluded "more is better", and shipped `cpu_count - 4`. That is 60
processes on a 64-thread machine against a workload that needs five cores
— an appetite that scales with the host instead of with the work, and is
therefore largest exactly where it is least needed. **No gate could have
caught it**: every fingerprint was green and the SCORE was the best it had
ever been, because the cost was in a currency the benchmark does not
measure. What settled it was measuring what the pipeline actually needed
(86 µs per survivor × ~3×10⁵ survivors per segment = 26 core-seconds
against 5.4 s of device time per segment) and sizing from that.

So: for any knob that consumes a *machine* resource rather than a device
one, size it from the requirement plus margin and state the requirement in
the log. If the sweep's optimum sits at the end of the range you allowed,
that is not a result — it is a sign the real constraint is somewhere the
benchmark cannot see. And when a campaign is meant to run unattended for
days, the machine staying usable *is* a requirement — budgeted up front
like any other, by the procedure in CONVENTIONS.md, "Sizing a hunt so it
leaves the machine usable".

The other half of the rule: **say what the safe setting costs.** The
replacement default (8 workers) leaves that pipeline host-bound with the
device idle 60% of the time — about 2.5x on the table. That is the right
default anyway, because an unusable machine costs more than the
throughput, but it only stays the right default if the price is written
down next to it.
A safety margin nobody has priced is indistinguishable from a bug.

Corollary, learned the same day: **an instrumented path is not the
production path.** The first attempt to size this pool timed a launch
through the engine's `profile` hook — which runs kernels eagerly with CUDA
events between them, disabling the graph replay production actually uses —
and overstated device time by ~3x, which inverted the conclusion about
which side was binding. When a campaign is running, take the phase split
from *it*: sample worker CPU duty and `nvidia-smi --query-gpu=utilization.gpu`
over the same window.

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
the capped engine. The `(k, off)` representation was valid from the beginning.
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

**There is a second limit, and it is not memory.** A wheel with a longer
period puts *fewer periods* in a launch of the same span, and if your kernel
amortizes any per-thread setup over the periods a thread walks, that setup
gets divided by a smaller number. In the case study the next wheel up (37#)
would generate 1.85x fewer candidates — the usual win — but 37x fewer periods
per launch, and the sieve's per-thread setup is 17.4% of the kernel at the
production T. Priced by fitting `sieve = a + b/T` from a forced-T sweep in the
*existing* engine, it comes out a **0.75x loss** at the queue budget that
fits, and needs 32 GB of buffers to reach 1.41x. Declined.

So before folding in another prime, check both:

- does the offset table still fit, at **every** parameter the gates run?
- does a launch still hold enough periods to amortize per-thread setup? If
  the kernel has a `a + b/T` shape, fit a and b first — the answer is a
  number, and it costs one sweep of an existing knob.

The second question is the one that is easy to miss, because the wheel's
benefit (fewer candidates) and its cost (fewer periods per thread) are both
proportional to the same factor, so they can cancel — or invert.

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

### 2.9 Resumable state must assert its own configuration

**Recognise it when:** a checkpoint stores a *position* whose meaning depends
on a tuning parameter — a period count, a block index, a chunk number.

A wheel change in the case study made the period 31x longer, so a cursor
counting periods meant something 31x different. The key string named the
wheel, which felt like enough. It was not: the wheel was computed in two
places (the launcher pinned one, the key derived another), they disagreed,
the key check *passed*, and the position was read against the wrong period.
The sweep restarted 31x too low, and the cursor then advanced in the wrong
units — which, resumed after a fix, would have skipped ~4e19 of unswept
range and put a silent gap in an exhaustive-coverage claim.

Two rules fall out, both cheap:

- **Derive configuration in exactly one place** and have everything else ask
  that object for it. Two independent derivations of the same quantity are a
  disagreement waiting for its second implementation to exist.
- **Store the unit next to the number, and assert it on load.** A key that
  *describes* the configuration is documentation; `stored_period ==
  engine_period or refuse` is an assertion. Only the second one stops the
  failure, because it does not depend on the description being right.

Worth doing before you need it: the check is three lines, and the class of
bug it catches is the one that silently invalidates results rather than
crashing.

### 2.10 Things that did not pay (measured, in this codebase)

| attempt | result | why it was tempting |
|---------|--------|---------------------|
| wider pattern word (128/256-bit) | **0.25x / 0.31x** | halves gather count; but the multi-word accumulator's data-dependent extraction defeats it |
| folding the pattern table 24x smaller (22 KB -> 904 B) by storing each prime's periodic bit-string once instead of one 64-bit window per residue | **0.685x** | the mathematics was exact and the table became trivially cache-resident -- but a window that straddles a word boundary needs two loads, and this kernel is bound by load COUNT, so 28 loads became 56. Table size was never the constraint |
| CRT-combining pairs of sieve primes into one table (halving the load count, the only thing that kernel was shown to care about) | **rejected without implementing**, on a differential ablation | the pairs multiply, so 3 pairs is 53 KB against 21.5 KB today. Padding the EXISTING table to the same footprints (same loads, same results, same fingerprint) measured 0.62x at 86 KB and 0.14x at 172 KB, so the win was already spent before the first line was written |
| the next wheel up (1.85x fewer candidates, the usual big lever) | first **rejected at 0.75x**, then re-priced at **1.85x** once the constraint behind the 0.75x was removed -- see 2.11 | the "0.75x" was real *given a queue budget that capped the launch's period count*. Cutting the launch along a different axis dissolved that, and the verdict inverted |
| skipping provably-redundant loads with `if (acc != all_ones)` -- an exact identity that would cut the expected load count 26 -> 14.4 | **0.818x**, monotone at ~1.3% per guard with zero credit for the skipped loads | 47% of blocks are already saturated by the 12th of 26 primes, so nearly half the loads are dead weight. But the guard is a BRANCH, and a warp takes it whenever *any* lane is still alive -- which is essentially always. Per-lane redundancy is not warp-level redundancy |
| warp-aggregated single-address atomic | not worth doing: whole push is **10%** of the kernel | the raw atomic rate looked close to the hardware limit |
| removing per-launch host syncs | **0.2%** of GPU time | "obviously" a pipeline bubble |
| compacting the rare-and-deep final stage | ~0 by analysis | it is 24% of a phase and 109 steps deep, so it looks like the tail |
| shared memory for lookup tables | worse at every block size | tables are small and L2-resident already |
| larger thread blocks (512, 1024) | worse | more parallelism per block "should" help |
| packing a SUBWHEEL's survivors into the window by RANK (7·11·13 keep 2·4·4 = 32 of 1001, so a prime's shift is whole words and the funnel shifts go; and an extra wheel prime at the same coverage unit) | **0.72-0.78x of the window stage** without the extra prime, **0.31x** with it (polynomial-runs round 5, built on the device in seven variants) | the 8 funnel shifts a prime were the largest item of the window body. But the pattern's period grows R-fold in WORDS, so the periodic read (2.8 loads for 8 words) is lost and every word is loaded -- 1.43x the data-pipe wavefronts on a pipe at 64% -- and the tables grow R-fold: 43-87 KB at R = 32 (one block per SM for six), and past shared memory the moment the extra prime needs R >= 768 to fill a warp, where 3.5 bytes a candidate meet the L2's 5 TB/s |

The first four are the instructive ones: each was priced with a
five-minute experiment (compile a variant with the suspect work deleted and
time it) rather than an afternoon of implementation.


### 2.11 When a budget caps a *shape* parameter, find another axis to cut

**Recognise it when:** a memory budget is enforced by shrinking something
that also controls how the work is shaped — batch size, tile size, launch
span — so the budget silently sets a tuning constant.

In the case study, a queue budget capped the launch's **period count**. But
the periods-per-thread T is derived from that, and per-thread setup is
amortized over T. So the memory budget was secretly setting the arithmetic
efficiency, and a wider wheel — which makes each period 37x wider — was
measured at 0.75x and declined on a fitted curve.

The fix was one question: *does the queue actually have to scale with the
launch's period count?* It did not. The launch is a rectangle of
(offsets x periods), and the queue scales with the product; cutting it into
**offset chunks** bounds the queue by how many offsets are in flight and
leaves the period count free. Each chunk runs the full pipeline over the
launch's whole period range. At the parameters where the old code ran, this
resolves to exactly one chunk — a deliberate no-op, gated before anything
depended on it — and the wheel's verdict then inverted from 0.75x to
**1.85x on a phase worth 78% of runtime**.

Generalisable: when you decline something because a constant is too small,
check whether that constant is *forced* or merely *conventional*. A budget
that binds on one axis is not a budget that binds on the work.

### 2.12 A negative measurement is a result; spend it

Two of the case study's most valuable experiments in its fifth round
returned ~1.00x:

- the visit-order pattern table (removing 2 of ~6 instructions per prime per
  pattern word): **1.007x**;
- collapsing a warp's 26 gathers from 17.3 distinct 32-byte sectors to 1:
  **1.53x**, and non-monotonically.

Neither is a speedup worth reporting. Together they *prove* the dominant
kernel is bound by load COUNT — not by issue rate, not by address spread —
and that proof is what redirected the session onto a phase that had never
been touched, which then returned 2.39x. The rule: when a phase resists,
buy information about *what it is bound by* before buying more attempts at
it, and prefer experiments whose negative outcome is as informative as their
positive one.

The corollary for [Part 3](#part-3--the-termination-test): a phase whose
verdict is "bound by X" should have X attacked from at least two directions
before the verdict is trusted, because the cheapest way to be wrong is to
inherit a plausible one.

### 2.13 The benchmark shape can become the blocker

**Recognise it when:** a frozen benchmark window is expressed in absolute
units (a span, a byte count, a row count) while the engine's natural work
unit grows underneath it.

The case study's frozen shape is a 5e14-wide window of the number line. It
was frozen when the engine's period was 6.47e9, so the window held 77,285
periods. Two wheel changes later the period is 2.01e11 and it holds 2,494 —
still plenty. The *next* wheel would make it hold **68**, which is two
pattern words per thread against 20x as many threads, so the same change
that is worth 1.85x in production measures 0.58x on the benchmark.

That is not the engine being wrong and not the benchmark being wrong: a
5e14 window genuinely is a bad shape for that wheel. But it means the
benchmark can no longer resolve the change, and "optimize under the score"
then stops being a neutral rule and starts picking the answer.

The discipline that follows: **do not ship it and do not quietly ship it
either.** Price both sides, name the shape as the blocker, and leave the
decision — amend the frozen shape, or accept the ceiling — to a human,
because changing the anchor that makes scores comparable across engine
generations is not a change an optimization pass gets to make. Record the
period count the frozen window holds, so the next person can see the margin
shrinking before it bites.

### 2.14 Never call the odds model from the segment loop

**The rule.** A campaign's inner loop may not evaluate an odds model. The
model's answer changes only when the frontier moves — a handful of times in
a campaign — and computing it is between two and three orders of magnitude
more expensive than anything else in the loop. Derive it once per frontier
and cache it on the frontier.

**What it cost.** `shift-ladders`, first campaign, 2026-08-23/24. Per
launch, at the filters each family was actually running:

| | A130003 (base 4), n = 21 | A110096 (base 2), n = 19 |
|---|---|---|
| device (sieve + tail + readback) | 13.05 ms | 23.33 ms |
| host classification | 0.11 ms | 1.30 ms |
| checkpoint, over its 16-launch segment | 0.45 ms | 0.45 ms |
| **the campaign actually took** | **45.59 ms** | **57.38 ms** |
| **unaccounted** | **31.98 ms** | **32.30 ms** |

The same ~32 ms on two families whose launches differ by **four orders of
magnitude in line swept** and 16× in survivors classified. That signature —
an absolute per-launch constant that two wildly different configurations
agree on to 1% — named the suspect class (host, per launch, independent of
the work) before it named the suspect.

It was `Campaign.ladder()` → `model.predictions(n_ahead=3)`: 3 terms × 4
quantiles = 12 `quantile()` calls, 90 bisection steps each, **1,080
`expected()` calls**, each a 3,000-point numerical integral over up to 21
linear forms. One `expected()` is 0.509 ms, so 1,080 × 0.509 = 550 ms
predicted against 578 ms and 541 ms measured. Called once per segment from
`check_rungs`, and again every 30 s by the heartbeat's `status_line` →
`next_rung`.

**The fix, measured paired and interleaved on the real segment loop:**

| | before | after | ratio |
|---|---|---|---|
| A130003 (base 4, n = 21) | `1.45×10¹⁴ m/s` | `5.05×10¹⁴ m/s` | **3.47×** |
| A110096 (base 2, n = 19) | `2.12×10¹⁸ k/s` | `5.12×10¹⁸ k/s` | **2.42×** |

and both land on the free-GPU device rates measured independently
(`5.08×10¹⁴`, `5.21×10¹⁸`), which is the check that nothing else is hiding
in the budget. The loop is now 95% / 90% device. (Each rate is per second
of that entry's own term: m for A130003, "4^k + m"; k for A110096, whose
name gives the term no letter and whose programs test k + 2^i.)

**Use `huntlib.rungs.LiveLadder`.** It rebuilds only when the key moves and
**takes the frontier as the first argument of `get` by signature**, so a
cached ladder cannot outlive the frontier it came from. That matters
because the reason these ladders were being rebuilt every time was a real
rule — a rung retires with its term (CONVENTIONS.md), learned from
`dickson-ladders` advertising `next a(12) P90` for hours after finding
a(12). **Deriving live and deriving repeatedly are not the same
requirement**, and conflating them is what cost the 3.47×. `gate_live_ladder`
drills both halves: reads at a standing frontier cost zero rebuilds, and a
find costs exactly one and moves the aim.

**The trap generalises past ladders.** Anything in a segment loop whose
inputs change only on a find is the same bug: re-derived ETAs, re-read
model files, re-computed singular series, a `predictions()` call inside a
`[STATUS]` line. The tell is always the same — cost per launch that does
not scale with the work.

**Two things measured at the same time and declined**, so nobody re-runs
them: precomputing `b**k` in the run-length classifier, **0.993× / 1.001×**
(the classifier is entirely Miller-Rabin; the exponentiation is noise); and
raising base 4's `per_launch` 1024 → 2048, paired over 10 rounds,
**1.025× [0.986, 1.118]** for +174 MiB — an interval straddling 1, declined
under the load rule. The measured optimum, 4096 at 1.07×, sits past the
tail queue's ceiling and is not a regime to ship a campaign in.

### 2.15 Enumerate what the period cannot hold: the classes of a partially forced prime

**Recognise it when:** the wheel sits at its period bound (`W' < 2^63`
here, the within-period offset of the wide record), the next prime up is
worth its usual `q/(q−w)`, and the SMALLEST primes in the wheel leave the
term only a few residue classes each — `w(q)` close to `q`. The wheel to 59
had been declined twice in `polynomial-runs` on the period bound alone.

**The idea.** A class-space engine already leaves the FORCED primes out of
its period: it sweeps `t` with `term = r0 + U·t` for the one class the
forced unit `U` leaves, and the period `W'` is the product of the wheel
primes without `U`'s. Nothing in that arithmetic needs the unit to be
forced. A prime that leaves several classes can be moved outside the period
exactly the same way, provided the campaign sweeps EVERY class it leaves —
the class list becomes the coverage claim in place of the unit. Each class
is its own sweep with its own tables (the kill sets carried through
`t = (killed − r0)·U^-1 mod q`, as for the forced unit), and the period loses the
factor of those primes, which is room for the next prime up.

**The measured case** (polynomial-runs, A347537 at n = 21, 2026-10-13; its
`OPTIMIZATION_LOG.md` round 3 has the method and the checks): 5 leaves the
term three classes and 7 two, so with 2, 3, 5 and 7 outside the period the
term is in one of six classes mod 210, the wheel {11..59} has `W' =
9.16e18 < 2^63` where 59#/6 did not fit, and the planner's own split
machinery admits it. The classes mod 5 and 7 are exactly the residues the
old wheel kept, so the whole gain is the new prime: candidates per unit of
line × 40/59. Paired and interleaved against the plan, with an A/A arm:
**1.306 [1.295, 1.311]** on the device at 256 periods (1.475 from the
candidates × 0.88 from a window of 32 primes for 29 — 2.8's second price,
every time), 1.10 at 128 periods, 0.81 at 64. The kernel did not change:
one compiled module serves all six classes, each a 507 MB table set.

**The price is the segment, and it is the whole decision.** The coverage
unit is a window of `pb` periods over every residue of every class, so it
grows by (new unit / old unit) × (new period / old period) — 35 × 59/35 =
**59x** here (8.3e21 → 4.9e23 of line, 1 hour → 49 hours of device for the
six classes together) — and a find is confirmed only when its window closes
in every class. Price it with the model's expected clock to a CONFIRMED
find, conditional on the term being past the cursor (the planner's
objective), and separately with the over-swept line credited to the next
filter where a promotion carries the classified line. At the cursor the
hunt stood at, the strict clock read 1.03 (an expected 27 hours of
over-sweep against a five-day remaining search), the carried-line clock
~1.26, and the next term, with a search of months, 1.30. So the lever is
worth its device ratio on a long hunt and nothing on a short one, and the
same six-class option must lose at every opening filter — which an
objective that prices the segment gives for free. **The owner's rule
(CLAUDE.md 5j, 2026-10-13): over-sweep is not bought unless its expected
hours are a small fraction of the hours the rate saves on the remaining
search to that term.** So the disposition is per term, not per engine: 27 h
against 1.3 days on a(21) from the cursor is a decline; 25 h against 44
days on a(22) (2%) is admissible, and it is the owner's call to take it.

**The recipe.** (1) For each small wheel prime list the classes it leaves;
the product over the primes moved out is the class count `C`. (2) Check the
new period fits the bound and that the split machinery admits it (`R1`,
`R2`, `R3`, `W1`, `W2`). (3) The candidate ratio is `(q' − w(q'))/q'` for the
prime admitted and nothing else — the enumerated classes are free. (4)
Parity: the union of the `C` class engines == the dense CPU sieve on a
small wheel of the SAME absolute period; the production wheel checked
G13/G14-style and end to end on values the live campaign already
classified (locate each to its `(t, s, u)` and run that one launch). (5)
Time it paired; then price the segment as above before deciding. (6)
Shipping is a launcher version: the class as a campaign dimension, the
cursor ADOPTED (floored) across the change, `C` table sets or a table swap
per class per window, gates for the partial unit, a frozen shape at the
live filter.

**Where else it applies.** The other three polynomial-runs families (the
same six classes mod 210, candidates × 0.63–0.64, unmeasured). The
primorial regime (primorial-runs, primorial-ladders) has the same period
block but weak kill sets: 5 and 7 leave 4 and 6 classes (24 sweeps for a
smaller `(q − w)/q`), so price the segment first. Not where the candidate
prime kills little (decimal-ladders' 5) and not where the record already
reaches the wheel wanted (plus-two-cliques' wheel to 59, lcm-ladders' 61).

### 2.16 A fallback priced as rare must be guarded by the MEAN

**Recognise it when:** a queue or buffer is sized from an analytic
survival with a margin, overflow takes a slow path that is "harmless
because it is rare", and the engine is moved to a problem whose survival
curve is different. The margin was set on the old curve; on the new one the
MEAN load can sit past the cap, and then the slow path is the kernel.

**The measured cases** (power-ladders, round 0 and round 1). The window
sieve's shared queue was sized for a strong sieve that leaves 0.35% of a
tile; the power ladders' weak kill sets (one residue per condition) left
2.7% — 3,500 survivors against 1,920 slots — and every block tested the
whole tail per candidate in the fallback: **9 s a launch, 17x slow**. Its
global tail queue, capped at 2²⁸ entries, held exactly its expected load at
two openings and 40% past it at a third, where the launch time swung 2x
between identical launches with which warps met a full queue: **2.33x**
once guarded. The tell, both times, is variance: a deterministic kernel
whose time varies between identical launches is meeting a capacity.

**The fix is a guard, not a margin**: compare the cap with the expected
load where the configuration is chosen, and change the configuration
(smaller tiles; fewer residues per launch) until the mean fits with room
(STARVE_GUARD, Q3_GUARD). A margin is a guess about variance; a guard is a
statement about the mean, and it travels to the next regime.

### 2.17 Move the classification onto the device when the host cannot follow

**Recognise it when:** the survivors of the best sieve the device can run
still arrive faster than the host can classify them — by orders of
magnitude, not by a pool's worth — and the first values each survivor is
classified on are small enough for a few-limb modular exponentiation.

power-ladders' ten conditions, each killing about one residue per prime,
leave 10⁻⁵ of the candidates past a sieve to 2²⁰ (and 10⁻⁷ past 2³²: the
survival falls only as a power of 1/ln of the depth), millions of values a
second at ~20 µs each in Python. But 2·m − 1 is a two-limb number at every
frontier the hunt will see. So the device Fermat-tests each survivor's
leading conditions (base 2, multi-limb Montgomery, one kernel per condition
over the previous one's compacted queue, the limb count compiled per
condition), and only values whose leading SIX conditions pass reach the
host: 1–4 thousand a second. What makes it safe is one-sidedness — a failed
Fermat test is a proof of compositeness, so the stage can drop nothing that
should have reached the host, and the host re-reads every run anyway (its
gate pins the arithmetic to Python's `pow` and the stream to the CPU sieve
filtered by a CPU Fermat chain). What it buys besides the host: **the sieve
depth becomes a device decision**, priced by what a tail prime saves in
Fermat work against what its test costs — 2¹³ ran 1.26x 2¹⁶ there.

---

## Part 3 — The termination test

You are finished optimizing when you can produce this table, **not** when
you run out of ideas. Anything less and the honest report is "I have not
finished searching", with what remains unexamined.

The table is taken at the filter that runs for days (Rule 0a), and its
heading names that filter. A table taken at an opening that closes in
minutes is not a termination test for the campaign.

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
whole test. "It looks tight" is not one of the three. And for an inner
loop, "roofline" and "structural optimum" are only admissible after
[INNOVATION.md](INNOVATION.md)'s representation hunt and instruction-level
pass have been run on that loop and logged with prices.

Worked example — the case study's final state, which is what let it stop:

| phase | share | verdict |
|-------|-------|---------|
| bit-sieve stage 1a | 78.2% | bound by load COUNT, established by *failing* to move it three other ways: ALU is free (1.007x / 1.006x / 0.999x from three arithmetic reductions); sectors are ~half of it (17.3 -> 1 = **1.53x**, so a warp-cooperative rewrite reaching ~8.5 nets only ~1.1-1.2x after its redundant prologues); and the redundant loads cannot be skipped, because a saturation guard is a branch and the warp takes it whenever any lane is alive (**0.818x**, monotone at ~1.3% per guard). Table pinned from both sides as before. Queue push re-priced at 11.8%, still break-even to aggregate. The one lever that removes loads is the wheel: **1.85x at production launch shape**, blocked by the benchmark window, priced below |
| stage-1b compaction rounds | 15.9% | was 28.0%. Per-prime literals in a generated per-round kernel (**1.084x**) and a 32-bit `off mod q` via an off-split (**1.037x**) cut it 2.39x; NINC and ROUND then both moved DOWN in response (1.020x, 1.043x) |
| cold stage-2 kernel | 5.9% | the same off-split with its own split point (**1.023x**). Compaction still unbuilt, still bounded by a 6% phase |
| host + syncs | 1.8% | round counters consolidated into one array zeroed once per chain rather than one fill per round, after ROUND 24 -> 16 tripled the round count |

The table earned its keep twice. In the first session, filling in the rounds
row exposed a 1.134x that no amount of staring at the code would have
suggested, because the code was not wrong — it was tuned for a balance that
no longer existed. That is the whole argument for a per-phase verdict over a
judgement call.

In the second session it did something better: it exposed a **stale
verdict**. The cold stage-2 row above used to read "structurally optimal:
rare-and-deep, so at most one lane per warp is active." That was true of the
design where stage 2 sat behind all of stage 1 — and it stopped being true
the moment compaction rounds began feeding that kernel, because then every
lane entering it runs stage 2. Nobody re-derived it; it was inherited from
one profile to the next, and it was sitting on a 3.1x.

So a verdict is not permanent, and this is the failure mode the table is
most prone to. **A structural argument is only valid against the structure
that existed when you made it.** When a phase's share moves, re-derive its
verdict rather than re-reading it — an inherited "optimal" is exactly as
dangerous as an inherited constant, and harder to notice, because a stale
constant merely costs you a factor while a stale verdict stops you looking.

And note what the table still does *not* say: "done". Three of its four rows
carry named levers with prices on them. The table's job is to keep remaining
work **visible and priced**, not to certify completion.

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

**But an ablation is only valid if it changes one thing.** A wrong-answer
kernel is allowed to compute nonsense; it is *not* allowed to change how
much work the rest of the kernel does, and it is not allowed to hand the
compiler an optimization the real kernel cannot have. Both happened in the
case study, in the same afternoon, and both produced confident numbers that
were off by more than an order of magnitude:

| ablation | reported | what actually happened |
|---|---|---|
| replace a divergent table gather with a **constant index** | "the gather is 81% of the kernel" | the index became loop-invariant, so the compiler hoisted all 28 loads out of the loop. It priced a kernel with *no loads*, not one with cheap loads |
| replace the gather with **pure arithmetic** (no memory at all) | 3x *slower* | the accumulator filled with garbage, which inverted the survivor bitmap downstream, so the extraction loop ran on nearly every bit. It priced the extraction path |

The fix is a **differential** ablation: keep the instruction mix and the
downstream work identical across variants, and change only the property
under test. Here that meant masking the index to 4 / 16 / 64 entries versus
the full table — every variant still issues the same number of
data-dependent loads, so nothing hoists and the garbage is equally garbage;
only the address spread moves. That version answered the question in one
run: **within L1, gather divergence is free** (0.993x at one sector), so the
kernel is bound by load *count*.

The same technique is the cheapest way to **price an optimization you have
not written**. Before building a change that would make some resource bigger
or smaller, first make *that resource* bigger or smaller in the existing code
and measure. In the case study the candidate was combining pairs of sieve
primes into one table -- one load instead of two, known to be the only thing
that kernel cared about -- at the cost of a much larger table. Rather than
implement it, the existing table was padded to the same footprints (entry i
stored at index i*PAD: same load count, same access pattern, same results,
fingerprint still exact). It measured 0.62x at 86 KB and 0.14x at 172 KB, so
the win was already spent before a line of it was written. An hour of
implementation replaced by five minutes of padding -- and unlike a
projection, the answer is a number.

Checklist before believing an ablation:

- did the deleted work feed an address or a branch the compiler can now
  fold? (make the replacement data-dependent)
- does the variant change how many items reach the *next* stage? (compare
  per-kernel times, not wall-clock, and sanity-check the survivor counts)
- is the variant's instruction count comparable, or did you delete a load
  *and* five ALU ops and attribute all of it to the load?

An ablation that fails these is not weak evidence, it is *anti*-evidence: it
will point confidently at the wrong phase, and the resulting "optimization"
gets built before anyone re-checks.

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
- [ ] frozen benchmark shape + work fingerprint from the first gated engine,
      the SCORE shape at the filter that runs for days (Rule 0a)
- [ ] previous engine versions retained as parity references

Then, in this order:

- [ ] name each family's day-long filter from the model's clocks; every
      measurement below is made there, with its planned engine (Rule 0a)
- [ ] measure the phase split; confirm the phases sum to wall-clock (Rule 1)
- [ ] profile the dominant kernel with Nsight Compute (Rule 1a): what it is
      bound by, and the SASS census of the phase that carries it — or,
      for CPU code, the category timers, representation variants,
      end-to-end shape, memory and worker sweep of Rule 1b
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
