# INNOVATION — finding the optimizations the checklist cannot

> **Authorship disclaimer:** As with every project here, this document and
> all the code it describes were authored by **Claude (Anthropic's AI)** at
> the repository owner's direction.

[OPTIMIZATION.md](OPTIMIZATION.md) is the process: measure the split, model
it, sweep the catalogue, re-sweep the constants, and stop only when every
phase has a verdict. It is good at finding *engineering* levers — batching,
compaction, launch shape, baked constants — because those are on its
checklist. It is bad at one thing, and the failure is on record:

**An earlier engine, 2026-09-08.** Four optimization sessions took a
modular-ladder engine 6.3x, then 1.1x, then 1.4x, and ended with the residue
ladder's inner step declared "the floor of this formulation" and the
"better algorithm" question closed by a correct proof that the *number* of
ladder steps is optimal. Both statements were true. Neither examined the
cost of *one* step under a different choice of coordinates. An outside
review did: it scaled the whole p-adic value by 2⁶⁴ instead of one digit,
so that one Montgomery reduction's by-product became the carry the old
step computed with an exact division and two more reductions. Two
reductions a step instead of three, **1.34–1.46x on the ladder, 1.18–1.24x
on the campaign loop**, bit-identical stream. The same session, taking the
new step apart at the instruction level, found another height-dispatched
variant worth 1.12x on the ladder. The owner's response was the rule this
file exists to keep:

> These are the types of optimizations you need to investigate. You need to
> be innovative. The default command should always be the fastest.

So: before any inner loop in this repository is called optimal, it gets
the two passes below, and the experiments they produce are run, not
modelled. This is the companion to Part 3 of OPTIMIZATION.md — a phase's
verdict of "roofline" or "structural optimum" is **not admissible** until
both passes have been done on it and their results are in the log with
prices, including the negative ones.

---

## Part 1 — The representation hunt

An inner step has an *invariant*: what the state represents. Everything
about its cost follows from that choice, and the choice is usually the one
the first author made on day one. Before declaring the step at its floor:

### 1.1 Write the invariant down, then enumerate its alternatives

For that engine's ladder the state was "`x = x0 + p·x1 (mod p²)`, `x0`
canonical, plus a Montgomery copy of `x0`". The alternatives that had to be
priced — and were not, for four sessions — are generic:

- **What is scaled.** Montgomery form on one digit, on the whole value, on
  neither. (The win: `U + p·V ≡ R·47^e (mod p²)` — the whole value
  scaled, so `T = c·U²`'s reduction `Z = (T + m·p)/R` gives `T = Z·R − m·p`
  *exactly* and `m` is the carry into the high digit for free.)
- **Which by-product of one operation is another's input.** A reduction's
  multiplier, a product's high word, a comparison's predicate. Every
  by-product that is currently discarded is a candidate.
- **Which digits are canonical and which are lazy**, and *by how much*: the
  slack bits between the modulus and the word (`p < 2⁵⁸` in a 64-bit word
  is six bits; `p/R < 2⁻⁶`) decide which conditional subtracts are needed.
  Bounds that close at the ceiling may close *without a correction* lower
  down — a height-dispatched variant (`p < 2⁵⁶` here: the set-bit step
  loses two compare-subtracts and a carry, 96 → ~65 instructions).
- **What quantity is tracked.** The value, or its derivative, logarithm,
  ratio to something known, or difference from the previous state.
- **How constants ride.** Folded into a product (`c·U < 47p` fits, so the
  base multiply costs one `IMAD`), or as a separate step; signed digits,
  windows, precomputed tables — each priced against the fold.
- **Word size and limb shape.** 64-bit words with 32-bit partial products,
  30-bit carry-save limbs, FP32 24-bit limbs, FP64 — priced on the
  *measured* pipe table (Part 2), not on a mental model of the GPU.

For each alternative write one line: "tried, ratio", "priced at X,
declined because Y", or "does not apply because Z". The ladder's list, for
the record: whole-value scaling **1.34–1.46x, shipped**; slack-bit variant
below 2⁵⁶ **1.12x ladder / 1.03x segment, shipped**; signed digits (a −1
digit is a division by 47 in p-adic form, dearer than the set-bit step it
replaces) declined; 2-bit window (47³ does not fit beside the square)
declined; 30-bit carry-save limbs (a wash on partial products) declined;
FP32/FP64 limbs (Part 2's pipe table) dead.

### 1.2 Paper bounds, then a bit-exact emulation, then the kernel

The order matters and is not negotiable:

1. **Derive every bound on paper**: word overflow of every product, the
   lazy range of every digit after every kind of step, the sign and range
   of every reduction input. Write them as inequalities in `p/R`.
2. **Write a host emulation that asserts all of them** — every lazy bound,
   every word bound, the exactness of each reduction, and the invariant
   itself after every step (`(U + pV) mod p² == R·47^E mod p²`, with `E`
   tracked as the exponent). Run it against the oracle on primes at every
   height to the ceiling, both tail settings, every base, the known
   primes; and **prove the bound is real** by requiring that some prime
   *above* a dispatch height trips an assertion (G18/G20 pattern). An
   emulation that only checks the final answer has not tested the bounds.
3. **Only then the kernel**, checked residue for residue against the
   shipped kernel on a full production window (millions of primes), plus
   an oracle sample; then a device gate against the oldest parity engine
   on populated windows on both sides of every dispatch height; then the
   frozen fingerprint.

This is how the emulation caught nothing in the prototype's arithmetic
and would have caught anything — and how the fold-free variant's bound
was shown to be *exactly* `2⁵⁶` (2.6M residues wrong above it, none
below).

### 1.3 Time it where the hunt runs, not where it is convenient

A kernel-only benchmark overstates: **1.34x on the ladder was 1.21x on the
segment**, and **1.12x on the ladder was 1.03x** once the walker overlapped
the ladder with the next segment's sieve, because the segment is nearer
`max(ladder, sieve)` than their sum. Report both numbers, always; the
campaign loop is the deliverable (OPTIMIZATION.md Rule 1: the campaign
loop is the one nobody times).

---

## Part 2 — The instruction-level pass

"Issue-bound at ~85% of the INT roofline" was written in the v4 log from
an instruction-count *model*. The real numbers were different, and the
difference is where the experiments come from.

### 2.1 Get the real SASS

NVRTC → `ptxas` → `nvdisasm`, with the `nvidia-cuda-nvcc` and
`nvidia-cuda-nvdisasm` pip wheels **downloaded and unpacked into a scratch
directory** (`pip download --no-deps`, then unzip — nothing installed):

```bash
python -c "..."   # nvrtc.compileProgram(-arch=compute_89) -> getPTX
ptxas -arch=sm_89 -O3 k.ptx -o k.cubin
nvdisasm -c k.cubin > k.sass
```

Then, per basic block of the hot loop (labels `.L_x_N` in the dump),
count opcodes *by full name*. For the v6 ladder's clear-bit step (59
instructions): 19 `IMAD.WIDE.U32` (the products and reductions), 6 `IMAD`
(cross terms), **11 `IMAD.X` / `IMAD.MOV` / `IMAD.IADD`** — adds and moves
the compiler put on the multiply pipe to balance — and 23 ALU ops
(`IADD3`, `ISETP`, `SEL`, `SHF`). Two thirds of the step is bookkeeping,
not arithmetic. You cannot see this from CUDA C, and you cannot fix the
compiler's pipe assignment from CUDA C either — but you can see which
pipe is full, which is the question that matters.

### 2.2 Measure the pipes on the actual GPU

A 40-line microbenchmark (8 independent chains per thread, 1,024 threads
per SM, a never-true compare on the result so nothing is elided — and
check that no rate exceeds one warp-instruction per clock per partition,
because a rate that does means the compiler strength-reduced your loop).
RTX 4090, warp-instructions per clock per SM partition:

| `IMAD.WIDE.U32` | `IMAD` | `FFMA` | 4 wide + 4 `FFMA` | 4 wide + 4 `IADD3` |
|---|---|---|---|---|
| 0.34 (~2.9 clk) | 0.49 (2 clk) | 0.89–0.97 (1 clk) | 15.1 clk vs 11.8 for the wides alone: **no overlap** | 12.7 vs 11.8: **overlaps** |

Two facts this table settles that a mental model gets wrong: a 64-bit
partial product costs ~1.5 32-bit ones, and it **occupies the FP32 pipe**,
so the "idle FP32 lanes" of an integer kernel are not a spare resource on
this GPU. The FP32-limb idea is dead by measurement, not by opinion.

### 2.3 One experiment per hypothesis, parity-checked, interleaved

With the pipe table in hand, every hypothesis becomes a variant kernel
that compiles from the same source with a template flag, checks every
residue against the shipped kernel, and is timed interleaved (9 rounds ×
20 launches, medians). The set that was run on the v6 step:

| hypothesis | experiment | result |
|---|---|---|
| the FP32 pipe has headroom | inject a dummy `FFMA` chain of 4 / 8 / 16 per step, kept live by a never-true compare | 0.99 / 0.98–1.00 / 0.92x — a few are free, an offloaded product (~40) is not |
| two 32-bit reduction rounds beat one 64-bit round | `redc32`, then `redc32` returning its multiplier | 0.93x, 0.95x — the compiler's `__umul64hi` form is better |
| a square needs three partial products, not four | `sqr64` on clear steps | 0.998–1.02x, noise |
| the set-bit step's canonicalisation is unnecessary below a height | fold-free variant with the bounds re-derived at `p/R < 2⁻⁸` | **1.12–1.14x**, exact below 2⁵⁶, wrong above — shipped with a dispatch |
| the ladder is latency-bound at the co-residency cap | grid 768 / 1536 / full | 1.00–1.04x / 1.03–1.07x / 1.04–1.08x alone; `sweep()` still prefers the cap |

Two of five paid, one of them shipped. That is the normal hit rate, and it
is why the experiments must be *cheap* (each of these is 20–60 lines and
a few minutes on the GPU) and why a cost model that has been wrong before
(OPTIMIZATION.md Rule 2; here it had been wrong twice) does not get to veto
a thirty-minute experiment.

### 2.4 The ablation that deletes work

OPTIMIZATION.md 3.3 already says it; it applies at the instruction level
too. The fold-free variant *is* an ablation that turned out to be correct
below a height. Before pricing any bookkeeping, delete it in a
timing-only kernel and measure — then ask whether the deletion can be
made *right* under some condition (a height, a parity, a segment
property) that can be dispatched on.

---

## Part 3 — The mechanism, as a ladder

Every optimization in this repository climbs this, in order, and the log
records which rung it stopped on:

1. **Hypothesis**, written as one sentence with a predicted ratio and the
   mechanism (which pipe, which bound, which by-product).
2. **Paper bounds** for any arithmetic change (§1.2).
3. **Host emulation with asserted bounds and a tripwire** (§1.2) — a gate
   that needs no GPU, so it runs anywhere, including with a hunt live.
4. **Variant kernel**, residue-for-residue parity against the shipped
   kernel on a production window; oracle samples.
5. **Kernel-only A/B**, interleaved, at every height the hunt passes
   through (the ratio often moves with height: 1.34x below `2⁶⁴/141`,
   1.46x above).
6. **Campaign-loop A/B** — the walker, consecutive segments, records
   compared exactly on every run (§1.3).
7. **Gates**: a new gate for the new mechanism (its bounds, its dispatch
   on both sides, its parity to the oldest engine, the frozen fingerprint),
   the walker gate extended, the full battery green.
8. **The default flips.** Once 5–7 hold, the plain command runs the new
   engine; the previous one stays reachable by flag for A/B. A verified
   win behind a flag is a win the hunt does not get.
9. **Constants re-swept** after the structural change (OPTIMIZATION.md
   3.4) — expect them flat or moved, and say which.
10. **Log**: the ratio at each rung, the declined items with prices, and
    the levers left. The next session starts from that table.

A hunt that is live is not a reason to skip rungs 1–3; it is a reason to
do them now and queue 4–9 for the next window.

---

## Part 4 — Rules of evidence

- **"The floor of this formulation" is a lever, not a conclusion.** Every
  time that phrase (or "issue-bound", or "at the roofline") appears in a
  log, Part 1 and Part 2 of this file are owed on that phase before the
  verdict stands. A structural argument about the *number* of operations
  says nothing about the *cost of one*.
- **An outside review of this code gets the same treatment as our own
  work, in both directions.** Check its hash manifest against the files
  on disk; run its harness and fix what does not run (the prototype's
  example commands used even lower bounds the sieve rejects); re-derive
  its mathematics; write *your own* emulation rather than trusting its
  validator; then give it exactly the credit its paired numbers earn. It
  claimed no speedup and had never compiled for a GPU; it was worth 1.2x.
- **Two numbers per result**: kernel-only and campaign-loop. One without
  the other is a hypothesis.
- **Negative results are results.** The pipe table and the five variants
  above cost an hour and closed four hypotheses permanently for this
  architecture; the next session must not re-run them. Write them in the
  log with the same care as the wins (OPTIMIZATION.md Rule 6).
- **Cheap first.** A dummy-work injection, a deleted-work ablation, a
  grid sweep, a microbenchmark: each is minutes. Build the expensive
  version of an idea only after the cheap experiment says the mechanism
  is real.

---

## Part 5 — Checklist, per inner loop, before its verdict is written

- [ ] the invariant is written down, and §1.1's six alternatives each
      have a one-line disposition (tried / priced / does not apply)
- [ ] real SASS of the hot loop, opcodes counted per step by full name,
      with the pipe each belongs to
- [ ] the pipe rates measured on this GPU (or the table above cited, with
      the GPU named)
- [ ] the saturated pipe identified; one experiment per hypothesis run,
      parity-checked, interleaved, negatives included
- [ ] every arithmetic change has paper bounds, an asserting emulation and
      a tripwire for its dispatch height
- [ ] kernel-only and campaign-loop ratios both reported, at every height
      the hunt passes through
- [ ] the default runs the fastest gate-green engine; the old one is a flag
- [ ] the log carries the rung each idea stopped on, with its price

Case file: `euler-prime-runs/OPTIMIZATION_LOG.md` for the engineering
ladder OPTIMIZATION.md is built on.
