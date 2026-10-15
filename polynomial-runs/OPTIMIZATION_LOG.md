# OPTIMIZATION_LOG — polynomial-runs

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt → measurement → kept/rejected, failures included. This
project starts from primorial-runs' engine v2 and planner p1, whose own
log (and primorial-ladders', plus-two-cliques', product-cliques',
clique-ladders', factorial-ladders' and lcm-ladders' before it) holds the
rounds that produced the window sieve. What is here is what was decided
in making that engine hunt the exact-run polynomial ladders, and what has
NOT yet been measured. Harnesses were scratch scripts, not committed.

---

## Decision 1 (2026-10-08) — primorial-runs' engine, taken whole

**Why that engine.** The problem is primorial-runs' problem with the list
of shifts changed: one unknown prime p, conditions that are p plus an
additive constant, the run EXACT so every index's line starts at the
bottom, and one sweep settling every index at once. The exact-run
launcher — the taxonomy that makes a run above the filter a discovery of
its own index, the frontier that jumps over indices found early, the
carried line — is exactly what these four entries need. The REGIME is
different: a quadratic (or the quartic) kills about half of each prime's
residues once the index passes (q + 1)/2, where a primorial shift killed
at most π(q) − 1, so the wheel is strong (10⁻⁵ of the line to 59 against
10⁻⁴) and the planner's wheels come out shorter. That is primorial-
ladders' A145743 regime (m + 4k²), which this engine ran at 2.8–6.3×10¹⁷
m/s, so the engine is known to be right for it; whether its constants are
at their optimum here is Round 1's question and it has not been run.

**What changed, and what did not.**

* *changed, in the oracle:* the shift function (a polynomial's values),
  the index arithmetic (`run_of`/`index_of`: three names count the
  argument from 0 and ask for n primes, A092120 asks for m = 0..n), sparse
  known tables (a term a comment states far above the data is settled and
  skipped), the proved bound on the kill set (min(forms, (q + 1)/2) on the
  quadratics, min(forms, q − 1) on the quartic), the forced classes (5 mod
  6 on A165234, 1 mod 6 on the other three, from the first index with two
  forms; 2 alone before it), the A164926 bounds on A230663 and the
  identity behind them (G1d);
* *changed, in the CPU engine:* the last filter is the GPU tail's residue
  list (32 forms), not a ceiling on the values — the shifts are under a
  million at every filter the engine can express, so the proof crossing is
  the deterministic bound itself and no value ceiling is needed; G5 and
  the canaries read the exception zone separately, because it holds terms
  with runs past any filter (a(11) = 11 and a(29) = 29 of A165234) and
  census values whose index a smaller known term settled;
* *changed, in the launcher:* the pool reads a run and `handle` maps it to
  the index once; the comment terms are settled and the frontier steps
  over them; `also_settles` records A164926(n+1) = p − 2 when A230663's
  find has p − 2 prime, checked from the bare definition, and the bound
  A164926(n+1) > p − 2 when it does not;
* *changed, in the model:* the integrals start at 10⁴ (the exception
  zone's top). With a singular series near 10⁹ and sixteen logarithms of
  values near 10, the Bateman–Horn integrand at the very bottom of the
  line put a quarter of a(17)'s mass of A230663 below p = 9; the primorial
  ladders never saw this because their shifts put every value far above
  the bottom. The validation E's moved from a sum of 30.2 to 21.0 over 26
  draws (P = 0.80 → 0.16 under Gamma(26, 1)); the medians at the open
  indices moved by under 2%. G12's monotone-medians check was replaced by
  "finite, and the fourth open index above the first": A230663's a(17) is
  predicted below its a(16), because x(x + 3) takes the same value at x
  and at −x − 3 and the seventeenth form adds no kill under 37;
* *not changed:* one line of device code, the planner, or any tuning
  constant. Several gate windows were widened (the strong kill sets leave
  a hundredth of the survivors the primorial windows held): G21's and
  G22's device windows from 4×10⁹ to 4×10¹²–4×10¹³ of line, the resume
  drill's two-level window from 3 to 6 periods, the classification drill's
  from 160 to 1600 periods, and G9's second-budget windows moved to n = 8,
  because at the open indices no first level under 2³² keeps more than
  R1_MAX residues in this regime.

**Round 1 was owed** (OPTIMIZATION.md 3.4: every constant was tuned on
another regime) and is below: the window width and the block shape moved,
the depth constants and the wheel did not.

---

## Round 1 (2026-10-08) — the inherited constants measured in the strong-wheel regime

Method, as primorial-runs' round 1: a scratch harness through the engine
API builds one engine per arm at the campaign's own plan with one override
(a constructor argument, or a module constant set for that build only),
warms each, then times the SAME launches on every arm, every round every
arm back to back in alternating order, the device synchronised, the
survivor count and xor compared on every run; ratios are medians over
four or five rounds with [min, max]. Rates are line of the term per second
at half the modelled median's height; "E[clock]" is the model's expected
line to a CONFIRMED find (whole segments from the bottom of the line)
over the measured rate.

**The regime, read off the plan.** At A165234 n = 21 (the filter a campaign
spends its days in) the plan is the full wheel to 53 on the wide record,
and the window reaches BIT_SURV after **24 primes** (lit 24, k2 71) where
the primorial and clique regimes needed 38–40: the strong kill sets do in
24 primes what the weak ones did in 40. So the window body is a smaller
share of the kernel and the per-residue fixed work — the x0 loads, the
extraction, the in-block rounds' prologue — a larger one. Two consequences
were measured; both were inherited constants that were right where they
were tuned and wrong here.

### The block shape at the wide window (NW = 7): 1.047

The inherited preference list for a 224-period window put (8, 2) first,
because at product-cliques' n = 18* the bigger block (16, 2) compiled to 4
blocks per SM. Here it compiles to 7. A165234 n = 21, pb 224, wide, p/s
against (8, 2), the same launches, the stream identical on every arm:

| shape | blocks/SM | regs | ratio |
|---|---|---|---|
| (8, 2) — the inherited first choice | 7 | 72 | 1.000 |
| **(16, 2)** | 7 | 72 | **1.047** [1.045, 1.051] |
| (16, 1) | 7 | 64 | 1.047 [1.045, 1.051] |
| (8, 1) | 7 | 72 | 1.000 [0.997, 1.005] |
| (16, 4) | 5 | 88 | 0.883 [0.881, 0.897] |
| (32, 2) | 6 | 72 | 0.060 (every block overflows into the fallback) |

**Kept: `BLOCK_SHAPES_BY_NW[7] = ((16, 2), (16, 1), (8, 2), (8, 1))`.** The
engine still takes the first shape that reaches the occupancy floor, so a
regime where (16, 2) falls to 4 blocks gets (8, 2) as before.

### The window width: 1.118 on the narrow record, 1.020 past 224 on the wide

The planner's `CREL_WIDTH` said the candidate rate is flat from 160
periods (1.115 / 1.10 / 1.117 at 160 / 192 / 224) and stopped at 224. In
this regime it is not flat. A165234 **n = 18** (wheel to 43, narrow record,
lit 26), p/s against the plan's 160 periods, each width at its best
measured shape, the same launches on every arm:

| periods | shape | blocks/SM | ratio |
|---|---|---|---|
| 96 | (16, 4) | 6 | 0.878 |
| 128 | (16, 2) | 8 | 1.014 [1.012, 1.018] |
| 160 (the plan) | (16, 2) | 7 | 1.000 |
| 192 | (16, 1) | 6 | 1.020 [1.017, 1.022] |
| 224 | (8, 2) | 7 | 1.085 [1.081, 1.088] |
| 224 | (16, 2) | 6 | 1.096 |
| **256** | **(16, 1)** | 6 | **1.118** [1.117, 1.125] |
| 256 | (8, 1) | 7 | 1.087 [1.085, 1.090] |
| 256 | (16, 2) | 6 | 1.061 |

and A165234 **n = 21** (wheel to 53, wide record, lit 24), against 224 on
(16, 2):

| periods | shape | blocks/SM | ratio |
|---|---|---|---|
| 160 | (16, 2) | 7 | 0.934 |
| 192 | (16, 2) | 7 | 0.970 [0.968, 0.971] |
| 224 | (16, 2) | 7 | 1.000 |
| **256** | **(16, 2)** | 6 | **1.020** [1.009, 1.024] |
| 256 | (16, 1) | 6 | 1.002 [0.995, 1.004] |
| 256 | (8, 1) | 7 | 0.970 |

The two records disagree on the shape at 256 periods — (16, 1) on the
narrow record, (16, 2) on the wide — by 2–5% either way, so the wide record
has its own row (`BLOCK_SHAPES_WIDE[8]`). **Kept:** `CREL_WIDTH` re-tabulated
to this regime's curve (96 0.88, 128 1.00, 160 1.00, 192 1.02, 224 1.085,
256 1.118; the entries under 96 are the inherited ones, unmeasured here
and optimistic, which the planner never reaches at a campaign filter),
`PB_PLAN_MAX = 256` so the planner considers the engine's own widest
window, and `BLOCK_SHAPES_BY_NW[8]` for the narrow record. `PB_DEFAULT`
stays 224: it is the width of an engine built with an explicit wheel and
no pb (the gates, the three anchor shapes).

**What the planner now chooses** (every filter a campaign passes through;
the wheel did not move anywhere): 256 periods at every opening and at
every filter from n = 20 up; 128 periods at the wheel-to-47 filters
(A165234 and A230663 n = 19, A092120 n = 18), where the narrow record
clamps a wider window to 183 live periods and 128 ties 160 on the rate
with a shorter segment; 128 in place of 96 at A347537 n = 19. Paired at
that last filter, p/s against the old plan (96 periods on the wheel to 53,
(16, 4)): **128 periods 1.126** [1.123, 1.129], 160 periods (clamped to 138
live) 1.057, the wheel to 47 at 224 (clamped to 183) 1.031, at 256 0.959 —
the expected clock to a confirmed find 0.22 h against 0.24 h. The segment
at A165234 n = 20 is now 1.13 medians and at A347537 n = 20 1.32 (the
planner's own clock prefers the rate to the shorter segment there; the
selftest's 1.5x bound on the expected sweep holds), and 0.03–0.05 at every
n = 21.

**The four campaign shapes were re-frozen at the new plan** (CLAUDE.md
rule 2: a deliberate coverage change moves the fingerprint, logged here):
SCORE 4108 / 371003886694656 → 6521 / 1601343003530803, S230663 5699 /
1649929367049237 → 9120 / 682995423446552, S092120 17162 /
58088338820602686 → 27481 / 11674479549184331, S347537 7751 /
1149513797431653 → 12208 / 102828151028243808 — each the whole third
level of the segment at period 1, now 256 periods. The three anchors did
not move (they pin pb = 224 explicitly), and G9 still pins GPU to CPU on
populated windows.

### The depth constants and the launch budget: flat, kept

A165234 n = 21 on the new plan (256 periods, (16, 2), wide), four rounds,
the stream identical on every depth arm:

| arm | ratio |
|---|---|
| BIT_SURV 0.0035 (default; lit 24) | 1.000 |
| BIT_SURV 0.002 (lit 29) | 0.986 [0.983, 0.988] |
| BIT_SURV 0.006 (lit 20, 5 blocks) | 0.807 [0.799, 0.808] |
| K2_SURV4 1e-4 (default; k2 71) | 1.000 |
| K2_SURV4 3e-5 | 0.987 [0.986, 0.987] |
| K2_SURV4 3e-4 | 0.954 [0.943, 0.956] |
| q2 2^14 (the plan): 38,983 survivors on the timed launches | 1.000 |
| q2 2^13: 186,696 survivors | 1.002 [0.999, 1.004] |
| q2 2^15: 9,218 survivors | 0.999 [0.995, 1.000] |
| CAND_PER_LAUNCH_WIDE 2^37 (default) | 1.000 |
| CAND_PER_LAUNCH_WIDE 2^36 | 0.994 [0.987, 0.995] |

The depth is flat over a factor of four and twenty in survivors, so it
stays a load decision (the plan's 2^14 leaves the host at a tenth of a
core; BENCHMARKS.md). **Kept: every default.**

### Priced and declined, without implementing

* **The planner's premise.** `plan`'s objective inherits clique-ladders'
  "a find RESTARTS the sweep, so the over-sweep is thrown away". Here a
  promotion CARRIES the classified line (the next index's survivors are a
  subset of this one's), so an over-sweep of S costs S(1/r_n − 1/r_{n+1}),
  a fifth to a third of what the planner charges. Where would it change
  the plan? Only where the segment is a sizeable fraction of a median,
  which after this round is n = 20 of A165234 and A347537 (1.1–1.3
  medians) and the openings (0.3–0.8) — filters of hours and minutes, and
  the plan there already takes the widest window. Not changed: the
  objective as written is a conservative bound on the right one, and the
  filters that last days have segments of 0.03–0.05 medians, where the
  two objectives agree.
* **The wheel to 59.** Blocked by the record as before: 59#/6 = 3.2e20 is
  past the 2^63 bound on W1·W2, and the greedy subset that fits (drop 5
  and 7 to take 59) kills far less than it gives up. A two-limb offset in
  the rounds is a new engine version priced at ~2.5x on a quarter of the
  kernel (primorial-runs round 2); 59 keeps 38 of 59 classes at n = 21, a
  1.55x on candidates per unit of line, and the segment it forces is no
  obstacle here (a 32-period window on 59# is 1e22 of line, 0.035 medians
  of a(21)) — so unlike the primorial regime, the record is the only thing
  in its way. Priced on paper at 1.55 × 0.70 (the 32-period window's rate)
  / ~1.35 ≈ 0.8 at a 32-period window and better with a 2-limb window
  record; not built in this round.
* **A window past 256 periods** is the engine's own limit (NW words of a
  32-bit window, MASK and queue widths); the curve is still rising at 256
  (1.020 per step on the wide record, 1.03 on the narrow), so a 320- or
  384-period window is the next lever on the kernel and is a change to
  the record's period field and the shared-memory budget, not a constant.

### Where it stands (Part 3 of OPTIMIZATION.md)

| phase | verdict |
|---|---|
| the window body | the inherited instruction-level verdict (primorial-runs round 2: three pipes within 4% of each other at ~70%) stands on the same kernel; what moved here is its SHARE — 24 primes a window, not 40 — which is why the width and the block shape, not the body, paid |
| the per-residue fixed work (x0 loads, extraction, rounds prologue) | amortised over 256 periods and 16 second-level residues a block: 1.118 (narrow) and 1.068 (wide, (16, 2) at 256 against (8, 2) at 224) at the filters measured; the curve is still rising at the engine's widest window (declined item above) |
| the in-block rounds | K2_SURV4 flat to 3e-5, 0.954 at 3e-4; BIT_SURV at its optimum (0.986 / 0.807 either side) |
| the sieve depth | flat over 2^13–2^15 on the device; a load decision |
| launch overhead | CAND_PER_LAUNCH_WIDE flat at 2^36–2^37 |
| the campaign's plan | the wheel confirmed at A347537 n = 19 (the 53-wheel at 128 periods over the 47-wheel at 224 by 1.09 on the rate); the width re-measured at two filters and the planner's table rewritten to it |

Not done in this round: Nsight Compute on this regime's kernel (the share
of the window body at lit 24 is inferred from the width curve, not
profiled), and the shapes at widths under 128 (the planner no longer
reaches them at a campaign filter).

---

## Round 2 (2026-10-08) — Nsight Compute on the 24-prime window, and engine v2

Method: a scratch harness through the engine API builds the PLANNED engine
at a filter (the launcher's own `plan_for`), at half the modelled median's
height; CUDA events around every kernel for the device split; **Nsight
Compute 2025.4.1** (`ncu --kernel-name sieve --launch-skip 3 --launch-count
1 --set full`, the clocks locked by the tool, then `--page raw` and
`--page source --print-source sass --csv`, the per-instruction samples
split into regions at the kernel's `BAR.SYNC`s and, inside a region, by
how many times each SASS line executed); and paired A/Bs, every round every
arm back to back in alternating order after a two-second burn-in, **a
second copy of the default built as an A/A arm alongside**, the survivor
count and xor compared on every run (identical on every arm below unless
said otherwise), medians over six or seven rounds of thirty launches with
[min, max]. The A/A arm read 0.999–1.003 [0.983, 1.014] in every sweep,
and the first round of every sweep was an outlier of 1–3% either way
(the clock settling), so the medians over rounds 1.. are what is quoted.
The filters are the ones a campaign spends days in: **A165234 n = 21**
(2.8 days; the same plan at A230663 n = 21 and A092120 n = 20–21),
**A347537 n = 21** (1.4 days; a different level split, 29 window primes)
and **A092120 n = 20**.

### Measurement 1 — the device split, and the kernel before anything changed

CUDA events, 30 launches at A165234 n = 21: the sieve kernel **93.9%** of
the device, the 27 tail rounds 6.0% (the nine generated ones 3.4%), the
offset-table build 0.04%; device 99.3% of wall through the engine API;
17.3 ms a launch, 1.17×10¹⁸ p/s, 7.1×10¹² candidates a second.

**Nsight, A165234 n = 21** (72 registers, 13,928 bytes of static shared
memory): 45.05 million cycles, 15.32 billion warp instructions, IPC 2.72,
issue slots 66.9% busy. **Six blocks per SM, set by shared memory, where
the registers allow seven** — 13,605 bytes would reach them; theoretical
occupancy 50%, achieved 49.7%, 5.97 warps a scheduler with 1.83 eligible,
no eligible warp on 31.8% of cycles. The ALU pipe 69.9% (the busiest by
elapsed cycles), the LSU 74.3% (by instructions issued), the L1 data pipe
59.2% in wavefronts; L1 hit rate 91%, L2 87%, DRAM 1.9%. 8.75 warp-cycles
per issued instruction: not selected 1.67, fixed-latency wait 1.58,
math-pipe throttle 1.16, selected 1.00, **no instruction 0.98**, short
scoreboard 0.72, dispatch 0.65, branch resolving 0.44, barrier 0.28, long
scoreboard 0.21. Branch efficiency 69%. Nsight's own suggestions, for the
record: global loads using 17.5 of 32 bytes a sector with 16% of sectors
excess (the rounds' table gathers, L1-resident at 91%), shared stores 9%
bank-conflicted (the split queue entry's two stores a survivor), an L2
slice imbalance; shared loads conflict on 0.015% of wavefronts. The same
at **A347537 n = 21** (74 registers, 14,640 bytes, six blocks by registers
AND shared memory, 29 window primes): issue 65.5%, ALU 69.1%, LSU 73.7%,
**no instruction 1.55** per issue.

**Where the instructions are** (SASS by region, A165234 n = 21): the
prologue 0.9% of the executed instructions and 4.0% of the stall samples;
the window and the extraction **74.7% / 69.5%**; the five in-block rounds
24.2% / 25.8%; the push 0.2% / 0.7%. Inside the window region the
straight-line body, run once per batch of two residues, is 1,148
instructions — **574 a residue-window of 256 periods**: per window prime
(24 of them) 8 `SHF.R.W` funnel shifts, 4 `LOP3` (two words' ORs fused),
2.8 `LDS.64` (the periodic read of ceil(q/32) + 1 words, from 3 at q = 59
to 7 at q = 173), one `IMAD.HI` and ~2.8 of index arithmetic (the packed
x0 + ne add and the split of its halves) — ~17 a prime, ~410 a window, the
formulation's floor on both pipes as primorial-runs' round 2 established;
and per residue ~116 of masks on the uniform pipe (56), selects, popcounts
and control, plus the extraction: sixteen per-word push loops of 1.13
iterations each at ~10 instructions, and the warp reserve (five shuffles
and one shared atomic). So the window BODY is 58% of the kernel's
instructions and the extraction with its control 17%, against 65% / 10% on
the 40-prime windows of the primorial regime — the share round 1 inferred
from the width curve, now counted.

**And where the CODE is.** The kernel compiled to **30,160 SASS
instructions (482 KB)**, of which some 21,500 were the queue-overflow
fallback: `tail_survives` — the tail rounds' test, unrolled four primes
deep, ~450 instructions — inlined at every site a full queue can be met,
one per live word of the extraction batch (16), one per item slot of every
in-block round (36 at these queue caps), one in the push. Never executed
(zero executed instructions on every copy in the profile), and threaded
through the hot path: each ten-instruction word push is followed by 7 KB
of it. That is the `no_instruction` stall — a warp waiting on instruction
fetch, once per issued instruction here and 1.5 times at A347537 — and it
is 11.5% of the stall samples kernel-wide, 18–21% inside the rounds.

### Measurement 2 — the two levers, priced paired

| arm (A165234 n = 21 unless said) | registers / shared bytes / blocks | ratio |
|---|---|---|
| the default (v1) | 72 / 13,928 / 6 | 1.000 |
| a second default (A/A) | 72 / 13,928 / 6 | 0.999–1.003 [0.983, 1.014] |
| queue margin 3σ (the 7th block) | 72 / 13,256 / **7** | **1.0145** [1.013, 1.018] |
| queue margin 4σ | 72 / 13,448 / **7** | 1.017 [0.997, 1.020] |
| a 2 KB pad of shared memory (stays at 6 blocks: an A/A) | 72 / 15,976 / 6 | 0.998 [0.974, 1.006] |
| `tail_survives` as is but `__noinline__` | 76 / 17,096 / 5 (the chooser fell back to the u32 entry) | 0.983 |
| the fallback as a plain loop, still INLINED | 72 / 13,928 / 6 | 0.992 [0.985, 0.999] |
| the fallback as a plain loop behind a CALL (`tail_survives_cold`) | 72 / 13,928 / 6 | **1.034–1.036** [1.020, 1.043] (two sweeps) |
| the fallbacks compiled out (an ablation: exact only while no queue overflows, which the fingerprint checked) | **59** / 13,928 / 6 | 1.026–1.029 |
| the CALL + 3σ | 72 / 13,256 / 7 | 1.050–1.052 [1.027, 1.066] |
| **the CALL + 4σ** | 72 / 13,448 / 7 | **1.053** [1.045, 1.056] |
| the CALL, A092120 n = 20 | 72 / 13,928 / 6 | 1.035 [1.025, 1.036] |
| the CALL + 3σ, A092120 n = 20 | 72 / 13,256 / 7 | 1.050 [1.048, 1.064] |
| the CALL, A347537 n = 21 | 76 / 14,640 / 6 | **1.057** [1.049, 1.063] |
| the CALL + 3σ, A347537 n = 21 (the registers bind at six) | 76 / 13,968 / 6 | 1.064 [1.057, 1.072] |

Two things the table says beyond the ratios. The code was not the whole of
the fallback's cost: the same plain loop inlined read 0.992, and the
compiled-out ablation freed thirteen registers — the inlined cold path was
shaping the hot path's allocation and schedule, and only the call undoes
both at once (at 72 registers, which is what the chooser's block count
depends on). And the block is worth what the inherited log said: 1.5% for
the seventh, where the padding ablation on the primorial kernel priced
~3% for the sixth; the 2 KB pad did not cost a block here and read as an
A/A, so the slope below six was not re-measured.

### Engine v2: the fallback out of line, and the margin re-ranked on the compiled footprint

**FALLBACK_COLD.** `tail_survives_cold` — the same test as a plain loop
(`#pragma unroll 1`) behind a `__noinline__` call — at the sieve kernel's
four fallback sites (the two extraction paths, the rounds' generated slot,
the push); the tail kernels keep the inlined, unrolled test, where it is
the hot path. One copy in the module: **8,608 SASS instructions** for
30,160. The stream is identical (the fallback is exact either way) and the
overflow path is exercised in production at the tighter margins below, so
G14's queue-overflow drill, G16 and G20's forced-full queues now run
through the call.

**QCAP_BY_OCCUPANCY.** The sigma ladder (`QCAP_SIGMA_LADDER`, 6 down to
2.5) is ranked before the kernel is compiled, on the analytic footprint
with the queue entry of that moment — the u32 — and the split (u16 + u8)
entry is chosen afterwards on the compiled occupancy, and the ladder was
never asked again. So on every wide campaign filter the kernel sat at
13,928 bytes and six blocks with seven in reach. Now, after the entry is
decided and only where the registers allow a block more than the kernel
reached (`_reg_blocks`: 72 registers allow seven, 74 and 76 six), the
non-queue bytes are read off the compiled footprint — the analytic
prediction less its 256-byte slack was exact at every filter checked —
the ladder is re-run on the real entry size, and the roomiest margin that
predicts a block more is compiled and kept if the compiled occupancy
confirms it (one extra compile; a margin that does not confirm reverts).
At A165234 n = 21 it chooses 4σ (13,448 bytes, seven blocks); at A347537
n = 21 nothing is tried. A tighter margin means the overflow fallback runs
on about one block in 16,000 at 4σ — a few items through the cold loop, in
the ratios above.

**After, by Nsight at A165234 n = 21:** 41.35 million cycles for 45.05
(**−8.2%** at the tool's locked clock; 1.053 paired at the campaign's),
14.30 billion instructions for 15.32 (the hot path itself shortened:
sixteen item slots a round for seventeen, and the allocation freed), seven
blocks, achieved occupancy 58.1%, 2.20 eligible warps a scheduler for
1.83, no instruction **0.72** per issue for 0.98, issue slots 67.8%, and
the pipes higher and closer together: ALU 74.1%, LSU 79.2%, the L1 data
pipe 64.3%; 10.3 warp-cycles per issue with not-selected 2.25 and
math-throttle 1.76 — more warps waiting on the same two pipes.

**Priced at every filter the campaign passes through** (v2 through the
engine API, about a second of real launches each, BENCHMARKS.md's table
rewritten): the day-long filters read 1.02–1.07 of their round-1 readings
(A165234 n = 21 1.255×10¹⁸ p/s for 1.18, n = 20 0.946 for 0.884; A230663
n = 21 0.920 for 0.868; A092120 n = 20 1.243 for 1.18; A347537 n = 20
1.417 for 1.32 and n = 21 1.972 for 1.93), the 128-period filters 1.00–1.02,
the openings of seconds within noise (the call costs two registers there,
and at n = 16 a block the rate does not see: the SCORE shape read
7.1–7.5×10¹⁶ p/s on both engines in six interleaved readings of its own
method), and the 90-day A092120 n = 21 0.98. One-second readings scatter
±5% — round 1's reading at A347537 n = 21 was 5% above this round's paired
default there — so the paired ratios above are the measurement and the
table is the price.

**The batteries:** `score.py` 29/29 with all seven fingerprints reproduced
(the first run after the change took 6 m 21 s — every v2 kernel compiled
once into CuPy's on-disk cache — and the next 1 m 25 s); `launch.py
--selftest` 58/58 in 178 s with v1 declared a predecessor the cursor
policy ACCEPTS (the line and its units are unchanged). SCORE 71,289.

### Priced and declined, without implementing

* **The quad window layout at 256 periods.** `WINDOW_QUAD` is gated to
  windows of 4–7 words, so the 8-word window round 1 moved every campaign
  filter to runs on the pairs table with the minimal periodic read: 2.8
  `LDS.64` a prime, where a quad table would make it ~1.9 (an `LDS.128`
  and an `LDS.32` for 5 words, 128 + 64 for 6) — 0.9 fewer a prime, 2.4%
  of the kernel's instructions, on the LSU that is now at 79%. The table is
  twice the pairs table: +3.5 KB at A165234 n = 21, 13,448 → 17,000 bytes,
  **five blocks for seven**, which this round prices at 1.5% a block —
  the loads would have to be worth 3% to break even where primorial-runs
  measured them at 1%. Extending the gate is a `window_reads` emitter
  change plus G14; not done at this price.
* **The extraction's per-word loops** (sixteen a batch at 1.13 iterations,
  ~13% of the window region): the ballot-and-straight-line variant
  (`EXTRACT_ONEBIT`) measured 0.93–0.96 on the primorial kernel at the same
  0.11 survivors a lane-word, and nothing in this profile changes the
  arithmetic; a predicated first push without the ballot saves about four
  instructions a word on paper, ~1.5% of the kernel, against a branchier
  loop. Not built.
* **The hot path's own code** is now 138 KB and `no_instruction` is still
  0.72 per issue; the window body is unrolled over two residues and 24
  primes (1,062 instructions, 17 KB) and the rounds over 16 item slots. A
  one-residue batch halves the window body's code and measured 0.98 in
  round 1 (`xe = 1` at 256 periods, wide); the rounds' unroll is what keeps
  their survivors in one register mask. The lever is spent at this
  structure.
* **Pre-shifted tables, the funnel shifts on the FMA pipe, CRT pairs for
  the periodic primes:** primorial-runs round 2's prices stand, and the
  LSU is 79% now rather than 69%.
* **A 384-period window** (the curve was still rising at 256 in round 1):
  the period rides a byte in both queue entries and the wide record, so
  it is a new record format; the fixed work it would amortise is the ~116
  instructions a residue above, a fifth of the window region.
* **The wheel to 59:** as round 1, the 2^63 bound on the product of the
  levels; a two-limb offset in the rounds.
* **The one-launch SCORE shape** read 0.38 of its last ledger row in one
  battery and 1.00 in the next (its 26 ms is mostly launch overhead and
  6,500 survivors through Python); the ledger says so. Not a change.

### Where it stands (Part 3 of OPTIMIZATION.md), after engine v2

| phase | share (instructions / stall samples) | verdict |
|---|---|---|
| the window body (24 primes, straight-line) | 58% / ~40% | at the formulation's floor on the ALU (8 funnel shifts and 4 fused ORs a prime for 8 words) and the LSU (the minimal periodic read, 2.8 loads a prime); the three pipes at 74 / 79 / 64% after v2, within the ~2x roofline test of each; the one restructure with headroom (quads, 0.9 loads a prime) costs two blocks, priced above |
| the extraction and its control | 17% / ~30% | sixteen per-word loops at 1.13 iterations; the straight-line variant priced 0.93–0.96 elsewhere and ~1.5% on paper here |
| the in-block rounds | 24% / 22% | 13.5 instructions and one gather a prime-test in packs; K2_SURV4 and BIT_SURV re-swept flat in round 1; their code now one copy a slot |
| the prologue and its barrier | 1% / 8.5% | one barrier per block-pass; the samples are warps waiting at it |
| the tail rounds | 6% of the device | 27 rounds, nine generated; CAND_PER_LAUNCH_WIDE flat (round 1) |
| the occupancy | — | seven blocks where the registers allow, chosen on the compiled footprint; the seventh measured 1.5% |
| the code | — | 8,608 SASS instructions for 30,160; `no_instruction` 0.72 per issue for 0.98 |

What this round did NOT do: time the campaign's own segment loop over
hours (rule 0a); re-sweep BIT_SURV and K2_SURV4 on the v2 kernel (both
were flat over a factor of three on v1 in round 1, and the kernel's
instruction stream is the same); or Nsight at the 128-period filters
(minutes, not days).

## Round 3 (2026-10-13) — the wheel to 59 through SIX CLASSES mod 210: 1.31x on the device at A347537 n = 21, measured; the segment is the price; NOT shipped

Method, as rounds 1 and 2: a scratch harness through the engine API (not
committed), every arm built at the campaign's own constants, warmed, then
the SAME launches timed on every arm, every round every arm back to back in
alternating order, the device synchronised, the survivor count and xor of
each arm's launches compared on every run (identical on every run below),
a second copy of the default built as an A/A arm, medians over rounds 1..
with [min, max]. Rates are p-line per second at p ~ 2.95e23, where the
campaign stands (coverage cursor 2.921e23 at the time of writing).

### The lever the record was hiding

The wheel to 59 was declined in rounds 1 and 2 on the period bound: the
product of the levels must stay under 2^63, the full wheel to 53 in the
class 1 (mod 6) already has W' = 5.43e18, and 59#/6 = 3.2e20 is far past
it. The bound is on the PERIOD of the class-space wheel, and the class-space
wheel leaves the forced primes 2 and 3 OUT of that period (the device sweeps
t with p = 1 + 6t). Nothing in the arithmetic requires a prime left out of
the period to be FORCED. A prime that leaves several classes can be left
out just the same -- if the campaign sweeps every class it leaves. On
A347537, at every filter from n = 6 up, 5 leaves p three classes (2, 3, 4)
and 7 two (1, 2), so with 2, 3, 5 and 7 all outside the period the term
lies in one of SIX classes modulo 210,

    p = 37, 43, 79, 127, 163 or 169 (mod 210),

the device sweeps t with p = r0 + 210 t for each of the six r0, and the
period no longer carries the factor 35. The wheel {11..59} then has
W' = 9,156,001,667,401,012,567 < 2^63 (the wheel to 53 times 59/35), and
the engine's own planner (`wheel_candidates(21, A347537, 210)`) finds its
split under the second first-level budget:

    (11, 13, 17, 19, 23, 43, 47) × (29, 31, 37) × (41, 53, 59)
    4,209,408 × 4,845 × 34,320 = 6.999e14 residues per class
    W1 = 2,147,003,287 < 2^32,  W2 = 4,264,549,441 < 2^32

What it buys, exactly. The six classes modulo 210 ARE the residues the old
wheel kept at 5 and 7, so moving those primes outside the period changes
nothing in the candidates; the whole change is 59 inside the wheel, which
kills 19 of its 59 residues at n = 21 (w(59) = 19) and keeps 40. Candidates
per unit of the p-line fall by exactly 40/59: 3.2217e-6 (one class mod 6 on
the wheel to 53) -> 2.1842e-6 (six classes mod 210 on the wheel to 59),
0.678. The ratio does not depend on how many classes 5 and 7 leave; the
class count is what the segment pays (below).

What the engine needs for it: nothing in the kernel. `killed_residues`
already carries every kill set through t = (killed - r0) * 210^-1 (mod q) for
any r0 and any squarefree unit, the primes of the unit kill no t, and the
kernel source does not depend on r0 at all (the kill sets reach the device
as tables -- the window patterns, the round tables, the tail masks and the
generated tail's tables -- and the inline masks as scalar parameters), so
ONE compiled module serves all six classes. The one refusal is
`assert_unit`, which is right to refuse: a unit is a coverage claim, and
with a partial unit the claim is made by the CALLER, which must sweep every
class. The harness admitted unit 210 with an explicit class; a launcher
version would make the class list the claim.

### Correctness, checked the way the gates check a production wheel

All on the harness, before any timing:

* the six classes are the same at n = 6, 10, 17, 20, 21, 22 and 25;
  a(17)..a(20) of this project each lie in one of them, and so do all
  4,315 census values held in the live checkpoint's pending list (702 /
  682 / 748 / 730 / 706 / 747 per class);
* G17-style, the same absolute periods, two arithmetics: the unit-6
  wheel {5,7,11,13,17} × {19,23} × {29} and the union of the six unit-210
  class engines on {11,13,17} × {19,23} × {29} (the same W =
  6,469,693,230) return the IDENTICAL stream -- at n = 10 with the sieve
  to 32768 (143 survivors over two periods; 40 window primes, 168 round
  primes, 12 tail rounds, so the whole per-candidate route runs in class
  space), at n = 21 with the sieve to 64 (40,856 survivors over four
  periods at p ~ 3e23: the live kill sets) and at n = 17 to 512 (326
  survivors); a 300-sample of each passes the CPU engine's one-at-a-time
  test;
* G9-style, the six classes == the dense CPU sieve, which knows nothing
  of classes: n = 21 over [1e15, +3e8) (505 survivors) and n = 17 over
  [a(17) - 1e8, +2e8) (1,007 survivors, a(17) among them); and each of
  a(17)..a(20) is the one survivor of its class engine over [p - 1, p + 1)
  at its own filter;
* the production wheel: each class's three levels have exactly
  prod(q - w(q)) residues, W1 and W2 under 2^32 with W1 W2 = W', and
  3,000 sampled CRT recombinations per class give values p = r0 + 210 t
  that survive every prime to 59 (direct divisibility of all 21 forms);
  the G14 window chain (x0 table, per-block offset, borrow, pattern word,
  through the quad/pairs layout) says killed exactly when the value is on
  3,840 sampled bits at two launch bases, one past 1e25; and END TO END:
  three census values the live campaign classified (runs 13, 13 and 14 at
  p ~ 2.99-3.00e23, in three different classes) were each located to their
  (t, s, u) index and period, and the ONE launch of the six-class engine
  that covers that index (launch 1,177,871 / 109,115 / 310,341 of the
  window's 1,338,480) returned each of them among its 612-686 survivors.

### Measured, paired and interleaved

The plan (unit 6, {5..17,23,29,41} × {19,31,37} × {43,47,53}, sieve 2^15,
256 periods, wide, (16, 2), 76 registers, 6 blocks per SM) against the
six-class engine on {11..59} (the split above, sieve 2^15 -- the same depth
the planner derives for it -- wide, (16, 2), 76 registers, 6 blocks per SM,
32 window primes for 29, 507 MB of tables per class of which 256 MB is x0)
at three window widths; 25 launches × 7 rounds; a class engine's line
divided by SIX, because six classes must sweep it:

| arm | ms / launch | candidates / s | p / s | ratio | survivors / launch |
|---|---|---|---|---|---|
| the plan | 19.93 | 6.90e12 | 2.140e18 | 1.000 | 415 |
| the plan again (A/A) | 19.94 | 6.89e12 | 2.139e18 | 1.001 [0.991, 1.010] | 415 |
| **six classes, 256 periods** | 22.61 | 6.08e12 | **2.781e18** | **1.306 [1.295, 1.311]** | 641 |
| six classes, 128 periods (70 regs, 7 blocks) | 26.69 | 5.15e12 | 2.357e18 | 1.102 [1.090, 1.115] | 649 |
| six classes, 64 periods (82 regs, 5 blocks) | 36.26 | 3.79e12 | 1.735e18 | 0.811 [0.809, 0.820] | 622 |

and, in a second sweep of four rounds, the classes 37, 169, 79 and 127 at
256 periods each against the plan: 1.318 / 1.310 / 1.310 / 1.315
(22.57-22.63 ms a launch; the classes are interchangeable, as they must
be: the same counts, the same survival, one kernel). The 1.306 decomposes
as 1.475 (40/59 fewer candidates per unit of line) × 0.88 (the candidate
rate: 32 window primes for 29, 59 having left the window for weaker
primes -- OPTIMIZATION.md 2.8's second price of a wheel prime, as in every
wheel change here). Survivors per unit of line are unchanged (the sieve
depth is), so the host sees 1.31x the survivors a second, 28,000 for
21,000: about 0.3 of a core either way.

### The price is the segment, and it decides the question

A window of 256 periods is 4.922e23 of p (8.343e21 on the plan: 59x), it is
49 hours of device for the six classes together, and a find is only known to
be the least once its window closes in EVERY class. Priced with the model
(`poly_model.expected`, conditional on a(21) above the cursor 2.921e23: the
model puts P(found by now) at 0.54, the conditional median at 8.35e23, the
expected remaining line at 1.01e24), each design sweeping whole segments
from the cursor at its measured rate, the clock to a CONFIRMED find being
the sum over segments of the segment's time times P(a(21) at or past its
start):

| design | segment | E[clock to a confirmed a(21)] | ratio | of which over-sweep |
|---|---|---|---|---|
| the plan | 8.34e21 (1.1 h) | 5.49 d | 1.000 | 0.5 h |
| six classes, 256 periods | 4.92e23 (48.9 h) | 5.34 d | 1.029 | 27.5 h |
| six classes, 128 periods | 2.46e23 (29.0 h) | 5.61 d | 0.980 | 15.4 h |
| six classes, 64 periods | 1.23e23 (19.7 h) | 7.17 d | 0.766 | 10.2 h |
| a(22) from a carried line of 5e23 (illustrative; conditional median 1.57e25): the plan | | 194 d | 1.000 | 0.5 h |
| a(22), six classes, 256 periods | | 150 d | 1.297 | 24.7 h |

Two readings of the a(21) row, and both are true. On the planner's own
objective -- the clock to a CONFIRMED find -- the six classes are a wash for
a(21) from where the campaign stands: the expected 27 hours of over-sweep
eat the 1.31x. But this is round 1's "planner's premise" item again: a
promotion CARRIES the classified line, so the over-swept line is a(22)'s
line swept at a(21)'s rate, and its net cost is only the rate gap between
the two filters (1.15x on this engine's own table, A092120 n = 20 -> 21), a
tenth of the 27 hours -- which makes the six classes about 1.26x to a(21)
counted that way, and 1.30x on a(22) and every term after it, where a
49-hour window is 1% of the search. The lever is worth 1.30 on the hunt the
campaign will spend its next months in, and nothing on the one it is in
today.

**Disposition (the owner's rule, CLAUDE.md 5j, stated on this result):
over-sweep is not bought unless its expected hours are a small fraction of
the hours the rate saves on the remaining search to the term in question.
For a(21) from the cursor that is 27 h against 1.3 days -- DECLINED: the
campaign stays on the unit-6 plan for a(21). For a(22) it is 25 h against 44
days (2%) -- admissible, and the six-class plan is the priced option for
the a(22) hunt, to be taken at the owner's word once a(21) has landed and
the launcher work below is done.** Nothing here moves the current campaign.

### Not shipped, and what shipping takes

A launcher version (v3) and a planner version (p2); the engine needs no
change beyond letting a caller name the class list in place of a forced
unit:

* the class list becomes a dimension of the campaign: for each window, the
  six classes in turn (or six engines interleaved), the work cursor
  (period, class, launch), the coverage cursor advancing only when the
  last class closes the window; `[STATUS]` and `--status` say which class
  of six the window is in, and the heartbeat's rate is six classes' line
  over six classes' time;
* the unit-6 cursor is ADOPTED, never accepted: the covered p re-denominated
  onto the new period by floor (2.921e23 -> period 151 of W = 1.923e21,
  2.903e23; 1.8e21 re-swept, 0.4% of a window) through
  `checkpoint.CursorPolicy(adopt=...)`, the census floor set under the
  overlap, a DISCOVERY inside it an alarm (the free cross-check between the
  two wheels), the pending list carried;
* the plan's objective learns the class count: the segment it prices is
  the window's line and the device time is six classes' -- and the
  six-class option must LOSE at every opening (a 49-hour window against a
  search of seconds), which the objective as written gives for free;
* the tables: six engines are 3.0 GB of device memory, or one engine whose
  class tables (x0, res1x, the pattern, round and tail tables: ~300 MB) are
  swapped once per class per window, every eight hours;
* the gates: G9 in class space with a PARTIAL unit (the six classes against
  the dense sieve, as the harness did), G13/G14/G20 at the six-class plan, a
  resume drill across a class boundary, `event_kind` unchanged, the
  acceptance test off the first `[STATUS]` lines, and a frozen shape at the
  live filter (none exists at n = 21 today);
* the other three families get the same six classes mod 210 (A165234:
  p = 1, 4 mod 5 and 1, 2, 4 mod 7; A230663: 3, 4 and 1, 5, 6; A092120: 2, 3
  and 1, 2, 4), their plans sit at the same bound and the wheel to 59 fits
  the same way, with MORE to gain -- candidates × 0.644 / 0.644 / 0.627 at
  n = 21 (w(59) = 21, 21, 22) -- unmeasured on the device.

### Priced and declined

* **59 and 61 together** in the classes mod 210: W' = 5.59e20, past 2^63.
  **11 outside the period too** (24 classes mod 2310) with 59 and 61: W' =
  5.08e19, past it as well. The bound admits exactly {11..59}; a wheel past
  59 is the two-limb offset of rounds 1-2, still ~2.5x on a quarter of the
  kernel.
* **64-period windows**: 0.81 on the device and 0.77 on the clock. The
  window can be narrowed to shorten the segment, and the rate goes first.
* **Sweeping the six classes to shorten the over-sweep** by any launch
  order: none exists -- coverage is contiguous only at the end of a whole
  window of all classes, whichever order the launches run in.

## Round 4 (2026-10-14) — doubly-focused enumeration BUILT ON THE DEVICE and measured against the plan at A347537 n = 21: 0.069 of the engine at its best configuration; the per-candidate test is the price, and it is structural; DECLINED

The question was whether doubly-focused enumeration (Bernstein; Wooding
and Williams, ANTS 2006; Sorenson, arXiv:1001.3316 §4) — the wheel
extended past 53 WITHOUT lengthening the coverage unit, the candidates of
[L, L + H) enumerated as p = L + Mm·u − Mp·v over two coprime moduli with
0 ≤ Mm·u − Mp·v < H — can beat the window sieve at the campaign's own
coverage unit, H = 256 periods of the plan's wheel = 8.343e21. It was
built on the GPU, verified three ways, and timed paired and interleaved
against the plan engine on the live unit (period 11779, p = 3.8387e23).
**It cannot: the best configuration measured 0.069 of the plan, and an
instruction accounting backed by Nsight Compute puts the ceiling of the
approach, under every assumption in its favour, below half the plan.**
Scratch harness only, not committed (rule 9); the method is here.

### What was built

Three CuPy raw kernels, on the two-axis representation above (Mp carries 2
and 3; the u axis is restricted mod every prime of Mp, the v axis mod every
prime of Mm; every other prime to q2 = 32768 is tested per candidate):

* **gen**: the sorted survivors of each axis in a range, enumerated as
  c = r + P·i over a small sub-wheel P (2·3·5·11 on u, 7·13 on v: 12 and 8
  residues) with the side's remaining primes applied as 32-bit kill
  patterns per word of i (a q-word table per residue and prime); two
  passes (count, prefix-sum, write) so the lists come out SORTED with no
  sort — a launch of 2e6 v's needs 2e6 u's over the sliding u-range;
* **join**: a warp per run of v's; per v the exact u-interval (a double
  estimate corrected by 128-bit compares of Mm·u against Mp·v and H), the
  pack constants Cq(v) = (L − Mp·v) mod Q lane-parallel into shared memory,
  then the lanes take the u's of the interval and sieve p through the
  stage-1 packs — pairs of primes with Q < 2^16 (89·97 … 163·167) then
  singles to 400, each a 64-bit Barrett reduction of u by Q, one
  multiply-add with Cq(v), a 32-bit reduction and a Q-bit mask in shared
  memory — with per-lane early exit and a ballot-driven refill of dead
  lanes from the u stream (staged through a 64-entry ring per warp,
  coalesced loads issued one stage ahead, in the `join2` variant), the
  survivors buffered per warp and flushed with one global atomic per 32;
* **stage2**: the stage-1 survivors (2.85e-3 of the candidates) tested
  through packs of three primes under 2^31 to 32768 with per-prime masks
  in a global bitmap, early exit, one atomic per warp.

The output is (u, v) pairs; the host rebuilds p in Python integers. Stage
costs on the live unit at the through-83 partition (2·3·5·11·19·41·43·53·
59·61·73·79 against 7·13·17·23·29·31·37·47·67·71·83, Mp = 1.216e16, Mm =
2.196e16): 297 candidates per v, 3.51 stage-1 tests per candidate, 29
stage-2 tests per stage-1 survivor; gen 3% of the time, join 77%, stage 2
20%.

### Correctness, before any timing

* P1, a dense reference: moduli through 37 (so the v axis is small enough
  to run whole), [1e23 + 12345, +1e9): the join's RAW output == the CPU
  engine's dense sieve through 37, 23,666 values, identical sorted lists;
  stage 1 (packs 41..400) on +1e10 == the CPU sieve through 400, 6
  values; stage 2 to 2000 == the CPU sieve, both empty. Every value's v
  reconstructs inside [0, Mm).
* P2, the production moduli at FULL depth against the OTHER arithmetic:
  on [3.8387e23, +3.35e18) (256 periods of a wheel-to-43 engine), the DFE
  over v < Mm/1000 returned 43 survivors at q2 = 32768 and the GPU
  engine's survivors of that window with the same v filter are the same
  43; a 200-sample passes the CPU engine's one-at-a-time test, and the
  engine's other survivors all have v ≥ Mm/1000.
* The staged-ring variant first dropped 12% of the candidates (its ring
  was carried across v's while the next v starts ~300 entries behind the
  consumer); fixed by restarting the ring at every v, re-verified on P1.

### Measured, paired and interleaved

The plan engine (unit 6, {5..17,23,29,41} × {19,31,37} × {43,47,53}, sieve
2^15, 256 periods, wide, 76 registers, 6 blocks/SM) timed over 25 of its
launches of the live segment (the exact line of each launch summed, not
launches × a nominal count), the DFE over a v-range sized to ~0.25 s
(its line is H × the v's processed over |S_v|, exactly), a second plan
engine as the A/A arm, every round every arm back to back in rotating
order, 5 rounds (3 on the last three rows), medians with [min, max]:

| DFE arm (depth, variant) | cand/v | tests per cand | tests per warp-iteration | DFE p/s | plan p/s | ratio | A/A |
|---|---|---|---|---|---|---|---|
| 83, `join` (refill from global, an atomic a survivor) | 297 | 3.51 | 17.8 | 1.11e17 | 2.01e18 | **0.055** [0.050, 0.055] | 1.007 |
| 83, `join2` (staged ring) | 297 | 3.51 | 17.8 | 9.6e16 | 1.96e18 | 0.049 [0.047, 0.052] | 1.023 |
| 83, `join2`, pairs only to 131 | 297 | 3.96 | 18.2 | 9.6e16 | 1.99e18 | 0.048 [0.048, 0.053] | 1.028 |
| 83, `join2` + survivors buffered per warp | 297 | 3.51 | 17.8 | 8.0e16 | 2.01e18 | 0.040 [0.039, 0.040] | 1.012 |
| 83, the same, 128 v's per warp | 297 | 3.51 | 17.8 | 7.1e16 | 1.87e18 | 0.038 [0.038, 0.039] | 1.046 |
| **79**, balanced partition (Mp 2.22e15, Mm 1.45e15) | 2,191 | 3.30 | 28.8 | 1.28e17 | 1.86e18 | **0.069** [0.068, 0.070] | 1.014 |
| 89, balanced partition (Mm 1.29e17) | 19 | 3.74 | 3.8 | 1.6e16 | 1.87e18 | 0.009 [0.008, 0.009] | 1.011 |

Three hypotheses about the join's slowness were each tried and each
read as a null (the refill's global load on the critical path: the ring
bought nothing; an atomic a survivor serialised at the L2: buffering
bought nothing; the mask footprint and occupancy: pairs to 131 bought
nothing). **Nsight Compute on `join2`** (depth 83, the second chunk, `--set
full`): 21.4 ms at the tool's clock, issue slots **54.6% busy**, IPC 2.2,
72 registers, no local-memory spills, 33.6 KB of static shared memory
(2 blocks per SM by shared memory, 3 by registers), theoretical occupancy
33%, achieved 32%, 3.85 active warps per scheduler with 0.81 eligible,
no eligible warp on 45% of cycles, 7.0 warp-cycles per issued instruction,
L1 hit 96%, memory throughput 28%. So the kernel is not stalled on
anything in particular; it is **issuing, at half the SM, about 100
warp-instructions per loop iteration** — the two ballots, the refill, the
pack record from shared, the 64-bit Barrett step on u, the multiply-add,
the 32-bit step, the mask gather, the counters and the branches — and an
iteration serves 18 tests (29 at depth 79, where the lanes stay full).

### The accounting, and why it is structural

Warp-instructions per unit of the p-line, from the measurements: the
plan engine issues at 67% (round 2's profile) for 6.5e12 wheel positions
a second, 0.13 warp-instructions a position, 4.2e-7 per unit of line.
The DFE at depth 79 spends 97 warp-instructions an iteration for 28.8
tests and 3.30 tests a candidate — 11 a candidate — at 4.4e-7 candidates
per unit of line: 4.9e-6, **11.6x the engine's**, which at 55% issue
against 67% is the measured 14x (0.069).

The structure behind it. The engine's window body tests one prime on 256
positions in 17 warp-instructions — 0.066 per position-prime — because
the positions are an arithmetic progression and a prime's kills are a
periodic bit pattern. Doubly-focused enumeration is exactly the choice to
give that up: a window of N positions with step s needs s = H/N, so at
the campaign's H a 256-period window forces the wheel to W' = 5.4e18, and
any modulus past it (here 83# = 2.67e32) makes the "windows" shorter than
one position and the survivors structureless, so every remaining prime is
a per-candidate test. The gain is 9.5x fewer candidates and 3.5 tests in
place of 24 window primes, 65x; the loss is ≥ one warp-instruction per
test against 0.066 — measured 6 per test (92x), and at the floor of this
arithmetic (the 64-bit reduction of u alone is ~16 thread-instructions;
~30 a test, every lane productive) 0.94 per test, 14x. **Even at that
floor, at 100% issue, the DFE is ~2x slower than the plan engine as it
stands.** Per-u residue tables in place of the reduction move the cost
onto the LSU, which the engine's own profile has at 79%; that is not a
route to parity either.

### Priced and declined

* **The cross-v candidate stream** (lanes refilled from the next v's
  interval so a warp never idles at the end of one): worth up to 8x at
  depth 89 (3.8 of 32 lanes) and nothing at depth 79 (28.8 of 32), so it
  lifts the deep partitions to the shallow one's 0.07 and no further.
* **Triples with Q-bit tables in L2** (0.9-3.4 MB a pack): ~2.1 tests a
  candidate for 3.5 — ≤ 1.7x, and a random L2 sector per test at a rate
  the L2 bandwidth would bind on.
* **Deeper moduli** (through 97: 0.0675 of the plan's candidates, 0.64 of
  depth 83's): needs the cross-v stream first, then ≤ 1.5x.
* **A sorted full-axis join** (both axes enumerated whole, as four
  half-wheel tables, in place of the per-v interval): the same
  per-candidate sieve; the enumeration is the cheap part in either
  formulation (gen was 3% here).
* All of it compounded, ≤ 0.2; the issue-rate ceiling above, ≤ 0.45.

**Disposition: DECLINED.** Doubly-focused enumeration keeps the coverage
unit and loses the window; on this GPU the window is worth more than the
wheel it fences in. The lever for a wheel past 53 remains round 3's six
classes mod 210 with the wheel to 59 — 1.31x on the device, paid in
segment length, priced for a(22) under rule 5j. No code, plan, constant
or campaign was changed in this round.

## Round 5 (2026-10-14) — the RANKED-SUBWHEEL window layout BUILT ON THE DEVICE and measured against the plan at A347537 n = 21: the window stage alone at 0.72-0.78 of the engine's; what it loses is the periodic read; with 59 moved into the wheel it is bound by the L2 at 0.31; DECLINED

The question was whether the window's per-prime work gets cheaper when
consecutive bits mean something else. Today a lane's window is 256
consecutive PERIODS of one wheel residue, and a prime's kills are a bit
pattern of period q read at an arbitrary bit offset — the 8 funnel shifts
a prime that round 2's profile counted as the largest single item of the
body (29.5% of the window region's executed instructions, 22% of the
kernel's). The alternative: take a few small wheel primes out of the CRT
enumeration into a SUBWHEEL M whose kept counts multiply to a multiple of 32 — 7·11·13 at n = 21 keeps 2·4·4 =
R = 32 of M = 1001 — and let a window hold the subwheel's SURVIVORS in
rank order: for the class t = t_lo + D·j of the outer wheel D = W'/M, the
kept j are those with (a + j) mod M in the kept set S (a = t_lo·D^-1 mod
M), and rank/select (rho, sigma) pack them. A prime q then kills rank z iff
T_q[z + R·h_q], T_q periodic in R·q BITS of rank, h_q the class's phase —
so the shift is R·h_q/32 = K·h_q whole WORDS (K = R/32) and the lane's
words are ANDed unshifted. The same construction admits an extra prime in
the outer wheel (59: D = 59·W'/M) WITHOUT lengthening the coverage unit —
the class's ranks inside [L, L + 256 W') are an interval, ⌊256 M / 59⌋
candidates or one more — which would buy round 3's 40/59 at round 1's
segment: the one formulation seen here that answers rule 5j directly,
and the reason it was built. (A rank-packed window is a known device in
sieving; the question was this kernel.) It was built on the GPU in seven
variants, verified exactly, and timed paired and interleaved against the
plan engine on the live segment (period 11779). **The window stage ALONE,
in its best configuration, runs at 1.11 of the engine's WHOLE pipeline —
window, extraction, in-block rounds and tail — per unit of line, which is
0.72-0.78 of the engine's window stage; the extra prime's variants, whose
tables cannot live in shared memory, sit at 0.31, exactly where 3.5 bytes
a candidate meet the L2's bandwidth.** Scratch harness only, not committed
(rule 9); the method is here.

### What was built

One CuPy raw kernel, parameterised: ONE WARP PER CLASS (an outer-wheel
residue, enumerated as two CRT levels [5,17,19,23,29,31,37] × [41,43,47,53]
(+59), 5.49e6 × 5.97e5 = 3.28e12 classes a segment; the engine's 1.05e14
residues / 32), the class's bitmap of 256·R/E bits held across the warp —
lane i the words i + 32c (LW = 1), the pair at 2i + 64c (LW = 2) or the
quad at 4i + 128c (LW = 4) — so every warp load is 32 consecutive words:
one wavefront, no bank conflicts, no alignment trick beyond storing the
table LW times shifted by a word. Tables padded past their period so no
read wraps (q + 32·WPL + K words a prime). Phases lane-parallel (lane qi
reduces the class's t_lo mod q_i and forms h_i; one shuffle a prime
broadcasts it), the per-class setup ~60 instructions against 29 × 8 word
loads. The extraction mirrors the engine's: popcount, a five-shuffle warp
prefix, the per-survivor ffs loop and one shared store a survivor into a
per-warp ring (XOR-consumed at the end so the stores stay; a running xor
of every entry is the fingerprint), or in VERIFY mode a global record of
(class, rank) the host rebuilds the integer from. With E = 1 the class's
8192 ranks tile the segments exactly (a is the same in every segment, so
each class's coverage is a fixed shift of under 32 candidates — less than a
period of W' — contiguous across segments); with E = 59 the rank interval
is computed per class and masked per word.

| variant | subwheel | R | E | window primes | words / lane | load | tables | home |
|---|---|---|---|---|---|---|---|---|
| V1 | 7·11·13 | 32 | — | 29 | 8 | LDS.32 | 43 KB | shared |
| V2 | 7·11·13 | 32 | — | 29 | 8 | LDG.32 | 43 KB | global (L1) |
| V3 | 7·11·13 | 32 | — | 29 | 8 | LDS.64, 2 copies | 87 KB | shared |
| V4 | 7·11·13 | 32 | — | 29 | 8 | LDG.128, 4 copies | 174 KB | global |
| V5 | 7·11·13·43 | 768 | 59 | 28 | 4 | LDG.32 | 353 KB | global (L2) |
| V6 | 7·11·13·17·41 | 4,992 | 59 | 28 | 22 | LDG.32 | 2.3 MB | global (L2) |
| V7 | 7·11·13·43 | 768 | 59 | 28 | 4 | LDG.128, 4 copies | 1.4 MB | global (L2) |

Correctness, before any timing, every variant: the device's survivors ==
a host reference (the same ranks, numpy modular arithmetic prime by prime)
on 108 classes scattered over the index space and on a contiguous range of
300 through the kernel's own class loop and blocks (V1-V4: 2,947 and 8,019
survivors; V5, V7: 1,722 and 4,759; V6: 11,326 and 31,360 — 0.326% of the
candidates, the engine's BIT_SURV); 300 device survivors and ~299 device
non-survivors per variant re-tested against the x-space kill sets
(`killed_residues(q, 21, A347537, 1)`, {2, 3} ∪ the wheel ∪ 59 ∪ the window)
in Python integers, 0 failures; every candidate of a sampled class in its
class and kept by the subwheel; the timed kernel's count == the verify
kernel's; the fingerprint identical on every round below.

### Measured, paired and interleaved

The plan engine (unit 6, {5..17,23,29,41} × {19,31,37} × {43,47,53}, sieve
2^15, 256 periods, wide, 76 registers, 6 blocks per SM = 24 warps) timed
over 24 of its launches of the live segment (the exact line of each
launch summed), a second copy as the A/A arm, each transposed variant over
a fixed class range sized to ~0.5 s (its line = classes × H / classes per
segment), every round every arm back to back in rotating order, medians
over rounds 1.. with [min, max]. Candidate rates are per unit of line:
the E = 59 variants generate 40/59 of the plan's candidates, so their p/s
is what counts. Rates in p-line per second.

| arm | warps / SM | regs | cand / s | p / s | ratio to the plan |
|---|---|---|---|---|---|
| the plan (window + extraction + rounds + tail) | 24 | 76 | 6.94e12 | 2.07e18 | 1.000 |
| the plan again (A/A) | 24 | 76 | 6.89e12 | 2.05e18 | 0.988 [0.972, 1.001] |
| V1, LDS.32, unroll 4, 1024 threads | 32 | 31 | 4.92e12 | 1.53e18 | 0.741 [0.734, 0.763] |
| V1, fully unrolled, 512 threads | 16 | 114 | 4.80e12 | 1.49e18 | 0.717 [0.682, 0.720] |
| V2, LDG.32 from L1, unroll 4, 1024 | 32 | 31 | 4.76e12 | 1.48e18 | 0.715 [0.705, 0.718] |
| V3, LDS.64 pairs, unroll 1, 512 | 16 | 39 | 5.43e12 | 1.68e18 | 0.813 [0.809, 0.814] |
| V3, LDS.64 pairs, unroll 1, 1024 | 32 | 39 | 6.63e12 | 2.06e18 | 0.994-1.034 (two sweeps) |
| V3, LDS.64 pairs, unroll 2, 1024 | 32 | 40 | 6.98e12 | 2.17e18 | 1.062 [1.061, 1.063] |
| **V3, LDS.64 pairs, unroll 4, 1024** | 32 | 40 | 7.34e12 | 2.28e18 | **1.106 [1.096, 1.121]**; a second copy 1.113 [1.091, 1.127] |
| V3, unroll 4, 1024, **the window body alone** (no push loop, no ring) | 32 | 40 | 8.22e12 | 2.55e18 | **1.232 [1.225, 1.304]** |
| V4, LDG.128 four copies (174 KB, past the L1) | 16 | 128 | 3.41e12 | 1.06e18 | 0.510 [0.508, 0.512] |
| V5, 59 outer, R = 768, LDG.32 | 16 | 128 | 1.42e12 | 6.51e17 | 0.310 [0.309, 0.311] |
| V5, unroll 4 | 16 | 128 | 1.50e12 | 6.87e17 | 0.327 [0.326, 0.328] |
| V5, 64 registers forced (96 B of spills) | 32 | 64 | 1.16e12 | 5.31e17 | 0.253 [0.252, 0.254] |
| V6, 59 outer, R = 4,992, LDG.32 | 16 | 128 | 1.39e12 | 6.36e17 | 0.303 [0.300, 0.303] |
| V7, 59 outer, R = 768, LDG.128 | 16 | 128 | 1.22e12 | 5.57e17 | 0.265 [0.264, 0.267] |

Reading the table. The ratios are the transposed WINDOW STAGE against the
engine's WHOLE pipeline. Round 2's SASS profile at this filter puts the
engine's window and extraction at 75% of the sieve kernel's instructions
and 69% of its stall samples, and the sieve kernel at 94% of the device:
0.65-0.70 of the engine's time per unit of line. So the best transposed
stage, at 1.11 of the pipeline, spends 0.90 of the engine's time doing what
the engine does in 0.65-0.70 — **1.29-1.39x slower on the stage it
replaces** — and the window BODY alone, with the extraction removed
entirely, spends 0.81: still 1.16-1.25x slower. The two LDS.64 arms built
from the same source differ by 0.7% (the harness's own A/A); the engine's
A/A read 0.988. The E = 1 layout buys nothing but the layout — the same
candidates, the same 29 primes, the same survivor stream — so the stage
would have to be faster than the engine's to pay at all.

### The accounting, and why it is structural

**The periodic read is what the layout loses.** The engine's pattern for a
prime q has period q BITS, so a 256-period window needs only ⌈q/32⌉ + 1
words loaded and derives the rest by the same funnel shift (WINDOW_PERIODIC,
WINDOW_READ_MIN): 2.8 LDS.64 a prime per lane-window, 5.6 data-pipe
wavefronts per prime per warp of 8192 candidates (round 2's profile: the
loads at their ideal wavefront count, the L1 data pipe at 64%). The ranked
pattern has period R·q bits = K·q WORDS — 32x longer at R = 32 — so no word
of a window is derivable from another and all eight are loaded: the
coalesced LDS.64 pair read is 256 B a warp-instruction, two wavefronts, four
instructions a prime: **8 wavefronts for 5.6, 1.43x on the pipe the
engine already has at 64%**, against the 8 funnel shifts saved on an ALU
pipe at 74%. The measured 1.29-1.39x on the stage is that ratio. The
single-word read (V1, V2) pays 8 LSU issues a prime for the engine's 2.8
and lands at 0.72-0.74, issue-bound; the quad read (V4) halves the issues
but its four copies are 174 KB, past the L1, and lands at 0.51.

**The tables grow R-fold, and shared memory is where the window lives.**
The engine's 29 patterns are 4.5 KB. The ranked tables are R·q bits a prime
plus a window of padding: 43 KB plain and 87 KB as pairs at R = 32 — the
whole SM's shared memory for one block of 32 warps where the engine runs
six — and R = 32 is the smallest subwheel that packs a word at all (7, 11,
13 keep 2, 4, 4). The extra prime needs R ≥ 768 to fill a warp's loads
(classes of 256·R/59 bits: 3,332 at R = 768, five words a lane at R = 32,
which cannot coalesce): 353 KB at R = 768, 2.3 MB at R = 4,992, L2-resident
only. Every layout reads 3.5 bytes a candidate from its tables (28-29 bits),
so at the engine's candidate rate the E = 59 variants would draw 16 TB/s
from a 5 TB/s L2 — and they measure 1.4e12 candidates a second, which is
5 TB/s: **the L2's bandwidth, to the digit**. The one way to serve those
tables from shared memory is to stage them a prime at a time with many
classes' accumulators held in registers, priced below.

### Priced and declined

* **The staged-table design for E = 59** (one prime's table at a time in
  shared memory — up to 38 KB at R = 768 — the block's 256-512 classes'
  accumulators in registers, 4-8 words a class a lane): the staging alone is
  600 wavefront-operations a prime per block, 1.2-2.3 per class-prime on
  top of the 4 the class reads, against the engine's 5.6 per 8192
  candidates — ~5.2-6.3 per 3,332: parity on the data pipe at best, at 16
  warps per SM, before the 40/59 is spent on anything, and a new kernel
  structure. Not built.
* **Lane per class with the extra prime at R = 32** (139-bit classes, five
  words a lane, a four-copy table of 60 KB in shared, the engine's own
  gathered reads): 2 LDS.128 a prime per lane are 8 wavefronts a
  warp-instruction pair for 139 candidates where the engine pays 5.6 for
  256 — 2.6x per candidate, 1.8x per unit of line after the 40/59. Dead
  on the data pipe; not built.
* **Quads at R = 32 without the extra prime**: 174 KB (V4), or 118 KB with
  per-chunk base updates — neither fits the 100 KB of shared memory, and from
  the L1 it measured 0.51.
* **A shallower ranked window** (the first 20 primes, so four copies fit in
  75 KB of shared): the nine primes dropped (149-199) pass 3.1x the
  survivors into the rounds — 24% of the kernel becoming ~75% — for a load
  width worth ≤ 1.3x on the body.
* **The subwheel 5·7·11·13 (R = 96)**: tables 3x bigger again; 52 KB plain
  with the tighter padding, 104 KB as pairs. Past the budget.

**Disposition: DECLINED.** The ranked layout removes the funnel shifts and
loses the periodic read, and on this kernel the read is worth more than
the shifts — 1.43x on the data pipe against ~0.5x on the ALU — so the
window stage is 1.3x slower with nothing bought, and the extra prime it
was built to admit at the campaign's own segment puts its tables where the
L2 binds at 0.31. The lever for a wheel past 53 remains round 3's six
classes mod 210 — 1.31x on the device, paid in segment length, priced for
a(22) under rule 5j. No code, plan, constant or campaign was changed in
this round; no battery was run (no engine file changed).

## The campaigns (2026-10-08 to 2026-10-15) — what the run measured

No engine or planner change; this is the record of the defaults under a
real campaign, one per family, no flags, engine v2 and planner p1, read
from the ledger timestamps and the checkpoints (the method: line from the
filter's first boundary to the end of the find's segment, over the wall
clock between the two ledger times; for a campaign that was not running
for part of a leg, the checkpoint's own clock, and for a stopped filter the
launches it swept as that fraction of the segment's line).

| filter | priced (BENCHMARKS.md) | campaign | ratio |
|---|---|---|---|
| A165234 n = 19 | 4.50e17 p/s | 4.61e17 | 1.02 |
| A165234 n = 20 then 22 | 9.46e17, 1.51e18 p/s | 10.08 h on the campaign's clock for 10.23 h priced | 1.01 (5.5 segments) |
| A230663 n = 19 | 3.34e17 p/s | 3.44e17 | 1.03 |
| A092120 n = 18 | 4.48e17 p/s | 4.57e17 | 1.02 |
| A092120 n = 20 | 1.24e18 p/s | 1.27e18 | 1.02 (54% of one segment) |
| A347537 n = 19 | 6.07e17 p/s | 6.03e17 | 0.99 |
| A347537 n = 20 | 1.42e18 p/s | 1.44e18 | 1.01 |
| A347537 n = 21 | 1.97e18 p/s | 2.03e18 on the campaign's clock | 1.03 (65 segments, 74.3 h) |

**Kept:** every default. The loop's wall clock matched the device price at
every filter swept whole, so the two things rounds 1 and 2 left unmeasured
because an agent does not start a campaign — the segment loop's own cost
per unit of line (OPTIMIZATION.md 2.14) and the substance of rule 5g's
no-flags acceptance test — are measured now, and both read clean. The
first `[STATUS]` lines themselves were not kept.

**The model was right.** E over the nineteen finds sums to 18.60 (mean
0.98, P = 0.49 under Gamma(19, 1)): neither the lateness of most families
here nor primorial-runs' earliness. BENCHMARKS.md's "budget 1.5–2×" was
not needed; every term the price table put inside a day landed inside a
day, and A347537's a(21), priced at 1.4 days to its median from the bottom,
took 3.1 days at 2.3 medians.

**The live filters, priced at the pause.** Round 1's table ends at n = 21,
and two campaigns promoted past it: A165234 n = 22 reads 1.51×10¹⁸ p/s
(1.18× its n = 21 at the same p) and A347537 n = 22 3.42×10¹⁸ (1.69×), each
three alternated rounds of 1.5 s through the engine API against the n = 21
engine (BENCHMARKS.md). The larger jump on A347537 comes with a shallower
sieve in its n = 22 plan (2^14 where n = 21 planned 2^15) and twice the
survivors a second; it was not taken apart further.

**Gaps the run exposed, none fixed at the pause:**

* *The README's model tables had drifted from `model_results.json`.* The
  prediction tables for A165234, A230663 and A092120 carried figures from
  an earlier run of the model (A230663's a(17) stated below its a(16)),
  while the file and BENCHMARKS.md's clocks carried the committed model's.
  The finds were scored on the file; the README now carries it.
* *The campaign shapes are frozen at the published openings.* With the
  finds in hand the four campaign shapes (n = 16, 16, 16, 17) are no
  longer any campaign's opening; a shape at each live filter is owed
  (rule 5g), and the finds into the oracle's `FOUND` move the drill filters
  with them.
* *The wheel A/B was repeated nowhere past A165234 n = 21*, and every
  live filter plans that same full wheel to 53 (BENCHMARKS.md, "What is
  still owed").
* *For the two a(22) hunts, round 3's six classes mod 210* are the priced
  option under rule 5j — weeks of remaining search, where a 49-hour segment
  is a few percent — and they need launcher v3; they are unmeasured at
  n = 22, where the plan's own sieve depth already moved.
