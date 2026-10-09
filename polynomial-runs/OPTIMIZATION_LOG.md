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
