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
