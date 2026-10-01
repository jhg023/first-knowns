# OPTIMIZATION_LOG — product-cliques

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt → measurement → kept/rejected, failures included. This
project starts from clique-ladders' engine v1 and planner p2, whose own log
holds the rounds that produced them (the forced class, the restart after a
find, the plan by expected clock, the deeper sieve, the block shape by
window width); what is here is what was measured and decided in making that
engine hunt a different object. Harnesses were scratch scripts, not
committed; each measurement below says enough of its method to rewrite one
in ten minutes.

---

## Decision 1 (2026-09-29) — build on clique-ladders, and change one thing

**Why that engine.** The two problems have the same shape: a greedy clique
whose conditions at index n are built from the sequence's own terms, so the
filter is state, a find restarts the sweep, and a wrong term would poison
every later one. clique-ladders already carries every piece of machinery
that shape needs — `register`, the restart in `follow_frontier`, the
promotion and rediscovery-run drills, the planner priced in expected clock to
a confirmed find — and its engine takes its problem as *killed residues per
prime* and nothing else. Its forms were `(a, b)` pairs, the code's
`a*x + b` with a ∈ {1, 2}; the product forms are (a(i), 1), the same shape
with large multipliers,
which a sieve that sees only residues does not notice.

**What changed.** A219761's a(n)² + 1 is not linear: it kills the square
roots of −1 modulo q, two residues when q ≡ 1 (mod 4). So a form became a
triple `(a, b, e)`, the code's `a*x**e + b`, the oracle walks residues with
`pow(r, e, q)` and takes square roots from sympy, the CPU engine builds them
with its own Tonelli–Shanks (so the two stay independent), and the one
change the GPU engine needed is that a prime can kill **one more residue
than there are forms**: the tail's per-prime residue list is sized from
`maxkills` (the forms' degrees summed) instead of the form count, and the
list-size ceiling raises on `maxkills`. The kernel is untouched.

**What stayed as it was, deliberately.** Every tuning constant — the block
shapes by window width, the survival targets (5e-8, and 1e-8 from 17 forms),
the relative-rate table the planner prices windows with (CREL_WIDTH), the
compaction depths, the queue margins — is clique-ladders', measured on its
filters. (Round 1, below, re-swept every one of them on this project's
filters and moved five.) The fingerprints this project froze are its own.

## Measurement 1 (2026-09-29) — the ceiling, and why it is rule 5h's best case

Every value less one is a(i)·a(n) or a(n)², so the route is the
repository's usual one: factor a(n) once, add the prefix term's factors
(each prefix term factored once when found, memoised in `launch.factor_int`),
and prove the value by BLS75 Theorem 1 with R = 1. `huntlib.ceiling`'s gate
measures the worst factorization at 1e40 in seconds, so the ceiling is
`K_CEIL` = 1e40 with no project measurement owed. What the project owes is
its own values at the height, and `_certificate_drill` proves them (3.8 s):

* both frontier terms on every value — A034881's a(15) already has one past
  the deterministic bound (a(15)·a(14) + 1 = 2.9e26: Theorem 1), the rest
  deterministic;
* just past each form's own crossing at each open index: the top product
  form in both families and A219761's a(n)² + 1;
* at the ceiling, both families: a worst-case term (6 × two 20-digit
  primes), which for A219761 is taken on a(n)² + 1 — an 80-digit value
  proved on N − 1 = a(n)² — and a term with a 34-digit prime factor, whose
  certificate carries a subproof that cannot be stripped.

The proof crossing is low here — a(n) ≈ 1.8e11 at A034881's open index,
below its frontier, because the largest multiplier is a(15) = 1.8e13 — so
the certificate route is the normal path, not an edge case.

## Measurement 2 (2026-09-29) — every opening, and the filters after it, priced (5c, 5g)

A scratch harness registered the model's stand-in terms in its own process,
built the PLANNED engine at each filter (`GpuEngine(n, fam, unit=6)` through
`plan`), timed the launches of the segment holding the modelled median
(warmed on the next segment; a 4 s cap), counted survivors, classified
1,500 of them with `launch.sprp_run`, and divided the model's
`expected_sweep` by the measured rate. The table is in BENCHMARKS.md; the
headline:

* **A034881**: a(16) about a second, a(17)* 93 s, a(18)* 0.57 h, a(19)*
  15.4 h, a(20)* 547 h. Device 2.2–6.7e16 a(n)-line/s as the planned wheel
  grows from 41 to 53; host 0.17–0.66 core-s/s past the opening.
* **A219761**: a(12)–a(14) under a second each, a(15)* 13 s, a(16)* 5 min,
  a(17)* 2.1 h, a(18)* 57 h, a(19)* 2,070 h. Host 0.22–1.33 core-s/s.

So a night of each family buys a(16)–a(19) and a(12)–a(17), with A219761's
a(18) in two or three days more. The first version of the harness
mis-counted the warm-up launch into the work cursor (1.5× on the rate of a
two-launch segment; fixed by warming on the next segment) — noted because
the same slip would flatter any single-launch filter.

## Gates re-cut for this problem (2026-09-29)

The gates were inherited with clique-ladders' indices, heights and units,
which do not all exist here (A219761 stops at 12, and no prime but 2 and 3
is ever forced, so the unit-30 cases have no counterpart). Every case was
re-pointed at indices and classes that exist; four needed more than that:

* **G17** (four wheels, one stream over one period) used the wheel to 43.
  Here a small prime keeps about half its classes rather than a third —
  product forms kill at most (q + 1)/2, product_reference G2d — so that
  period is 1.6e12 candidates, and an engine asked for one period of a
  32-period segment sweeps the whole segment: the gate did not finish in
  290 s. Moved to the wheel to 41 (period 3.0e14): 13.7 s warm, the same four
  arithmetics over the same kind of window.
* **G18** (every opening compiles to the tuned occupancy) failed at
  A219761 n = 10, a filter only the rediscovery drill runs: ten conditions
  need 43 window primes to reach the window's survival target, against 38 at
  the opening, and the literal code for them compiles to 122 registers and
  4 blocks per SM (the bar is 5). The bar now applies at each family's open
  index — A034881 n = 16 compiles to 6 blocks, A219761 n = 12 to 5 — and the
  two drill filters below it are held to everything else (no spills, the
  carveout, the window tables' size) with their occupancy reported. No
  campaign runs n = 10: its prefix is published and the campaign only
  climbs.
* **G20**'s round drill needs four compaction queues to exercise the aliased
  ping-pong buffers. At clique-ladders' q2 = 64 these kill sets gave three
  (survival halves less often when a prime kills half its classes, not most
  of them); q2 = 128 gives six.
* **G11** (the model against the knowns) tests the law, not a band — see
  README "The odds model": the twelve draws sum to 5.79 (P = 0.016 low), a
  band sized for 49 draws would fail a correct model on twelve one time in
  five.

And one gate was written for this problem: **G2d**, the involution bound
(no prime past 3 is ever forced), whose first version claimed that two terms
never share an orbit of r → −r⁻¹ modulo q. The gate refuted it on the first
run: 1·6 + 1 = 7 is prime and IS q. The statement now allows exactly the
pairs whose product plus one equals q (eleven of them, all among the first
six terms) and checks "never forced" directly.

## Battery and score (2026-09-29)

`python launch.py --selftest`: **49/49 ALL GREEN in 166 s** (run first in
three parts while the gates were being re-cut, 43 + 44 + 92 s warm; a cold
kernel cache adds about a minute). `python score.py`: every gate green, all five fingerprints
reproduced, **SCORE 11,590,820,351** (1.16e16 a(n)-line/s at A034881's
opening).

---

## Round 1 (2026-09-29) — engine v2 and planner p3: the window is bound by shared-load ISSUE

Every measurement below was taken on this project's own filters through the
engine API: the model's stand-in terms registered in a scratch process
(`ref.register(fam, i, model.stand_in(fam, i))`), the planned engine built
at the filter with `seg_cap = pb`, launches swept at the modelled median,
one warm-up arm first and an A/A arm last, a FIXED launch count per arm,
3–4 interleaved rounds, medians, and the survivor count and xor compared on
every run wherever two arms share a launch decomposition (they agreed on
every run of every arm that shipped). A starred filter is a stand-in.
Rates are exact: a harness that counted every launch as full overstated a
segment whose last first-level chunk is partial by up to 1.75x — noted
because the first reading of this round (a 1.65x "win" for a narrower
window at n = 18*) was exactly that.

### Measurement 3 — where the hours are, and the phase split

The inherited plan, per launch (CUDA events; instrumented wall = plain wall
to 1%): the sieve kernel is **89–91%** of device at A034881 n = 18*, 19* and
A219761 n = 17*, 18*, the tail rounds the rest, and device = wall (1.00:
the loop off-device is nothing, as in clique-ladders' Measurement 9). Inside
the kernel at A034881 n = 19*, by differential ablation (OPTIMIZATION.md
3.3):

| part | share of the kernel | how |
|---|---|---|
| the window sieve | **53%** | every window group emitted twice, the copy reading the same bits at the pattern's other period (r ± Q), stream identical |
| the in-block rounds' items | 22% | `nq0` forced to zero through a never-true compare |
| extraction | 5% | the q0 count forced to zero |
| prologue, x0 loads, the rest | 19% | the remainder; the prologue itself is free (its `ne` computation replaced by a cheap stand-in: 1.014) |

### Measurement 4 — what binds the window (INNOVATION.md Part 2)

**The SASS.** NVRTC → PTX → `ptxas -arch=sm_89` → `nvdisasm`. The window
loop body is 466 instructions per residue at 29 primes: per prime 5 `LDS`,
4 `SHF.R.W.U32` (the funnels), 2 `LOP3` (the ORs — ptxas does fuse them
three-input), 1 `IADD3` (x0 + ne + bw), and three ops of index arithmetic
(`SHF`, a `LOP3` for the word address, a `LOP3` for `r & 31`, which the
wrapping funnel shift makes redundant).

**The pipes, measured on this RTX 4090** (conflict-free microbenchmark, 8
independent streams a thread, ~2.78 GHz under load): `LDS.32` 1.26e9 and
`LDS.64` 1.23e9 warp-instructions per SM per second — **0.455 a clock,
whatever the width** — and `LDS.128` 0.56e9 (there the 128 B/clk data path
binds). So a shared load costs its ISSUE, and a 64-bit load moves twice the
data for the same price.

**The window is bound by exactly that.** Injected into the real kernel,
kept live by a runtime zero, stream unchanged: one more 32-bit shared load
per prime **+15.7%**, one more 64-bit load the same (1.117 against 1.120),
one more ALU op **+2.5%**. Removing the redundant mask (−29 instructions of
466) read 0.993: ALU is not the limit. (A first injection read +2.8% for a
load: it re-read a word already loaded and the compiler merged the two.
Check that an injected load is a new address.)

### Change 1 — the window from a table of OVERLAPPING PAIRS: 1.145–1.149x (`WINDOW_LDS64`)

Entry e of a prime's table is (word e, word e + 1) of its pattern, so the
NW + 1 words a window needs, starting at ANY word, are ceil((NW + 1) / 2)
aligned 64-bit loads — 3 in place of 5 at NW = 4 — for twice the table. The
index arithmetic is unchanged and the shift wraps, so there is no select.
**1.145 / 1.149 / 1.149** at A034881 n = 19*, 18* and A219761 n = 17*,
stream identical; the loop drops to 397 instructions and 3 loads a prime.

Tried first and rejected: 64-bit loads from the PLAIN table with a word
select on an odd start — **0.985**. Five `SEL` and a predicate a prime made
the loop 644 instructions and ALU-bound. The representation, not the load
width, was the lever.

The pairs table is taken where it fits the window tables' budget
(`PAT_BYTES_MAX`, 16 KB): every campaign configuration (5–7 KB), not the
shallow x-space gate wheels, whose deep windows passed the 48 KB static
limit doubled — **G14 caught that** (`ptxas: uses too much shared data`).
G14 now checks the window chain through BOTH layouts and fails if the
dispatch leaves either unchecked (it did, once the window cap below made
every gate table fit: a case is now forced onto the plain layout).

### Change 2 — the word index on the multiply pipe: 1.013x (`WINDOW_ADDR_MUL`)

`__umulhi(r, 2^27)` (one `IMAD.HI`) for `r >> 5` and its mask (two INT
ops). 1.013 at n = 19*. Small, because ALU was never the limit; kept
because it is free.

### Change 3 — the width curve moved, and the block shapes with it: 1.11x more at 160 periods

A window of NW words now costs ceil((NW + 1) / 2) loads a prime, so the
ODD word counts fill their last pair and 128 periods, the inherited optimum,
is a trough. Candidates/s against 128, paired, each width at its best shape:

| periods | 32 | 64 | 96 | 128 | 160 | 192 | 224 |
|---|---|---|---|---|---|---|---|
| v2 (A034881 n = 18*, 19*; A219761 n = 18*) | 0.70 | 0.82–0.87 | 0.975 | 1.000 | **1.11–1.12** | 1.10 | 1.117 |
| the inherited curve (clique-ladders) | 0.665 | 0.858 | 0.952 | 1.000 | 0.985 | 1.02 | 1.06 |

But only at the right block shape: the fallback shape for five words, (8, 1),
read **0.997** of 128 where (16, 2) read **1.114** (A219761 n = 18*). Rows
5–7 of `BLOCK_SHAPES_BY_NW` are this project's: NW 5 (16,2) — (16,1) 0.97,
(16,4) 0.975, (32,1) 0.971, (8,2) 0.91, (32,2) 0.90; NW 6 (16,1) — (8,2)
0.945, (8,1) 0.933; NW 7 (8,2) — (16,2) 1.009 at 4 blocks, (8,1) 0.995.
`CREL_WIDTH` re-fit to the new curve; a narrow window the record CLAMPS
(157 live periods of 160 at n = 19*) is priced as a full window for its
live periods, `CREL_WIDTH[pb] * pv / pb` (measured 1.122 against 128; the
inherited constant for the clamp said 0.981); `CREL_WIDE` 0.93 → 0.91
(the same 160-period window forced wide at n = 19*: 1.025 against 1.122).
Every filter now plans 160 periods on the wheel it planned before (planner
p3).

### Change 4 — the depths: BIT_SURV 0.007 → 0.0035, K2_SURV4 3e-4 → 1e-4

A window prime a third cheaper moves the window/round boundary deeper, and
a deeper window also shrinks the in-block queues (sized from the survival
at `lit`), which on a 160-period window is the fifth block per SM:

| (BIT_SURV, K2_SURV4) | A034881 n = 19*, 128 periods | A219761 n = 18*, 160 periods |
|---|---|---|
| (0.007, 3e-4), inherited | 1.000 | 1.000 (4 blocks) |
| (0.005, 3e-4) / (0.005, 1e-4) | 1.011 / -- | -- / 1.079 (4 blocks) |
| **(0.0035, 3e-4)** | **1.023** | 1.123 |
| **(0.0035, 1e-4)** | -- | **1.148** |
| (0.0025, 3e-4) / (0.0025, 1e-4) | 0.997 (102 registers, 4 blocks) / -- | -- / 1.093 (106 registers, 4 blocks) |
| (0.0018, 3e-4) | 0.967 | -- |

and then K2_SURV4 at n = 19* on BIT_SURV 0.0035: 3e-4 / 1e-4 / 5e-5 / 3e-5 /
1.5e-5 = 1.000 / 1.024 / 1.026 / 1.009 / 0.998. Deeper than 0.0035 the window loses even with the
registers capped to keep its block (`__launch_bounds__`: 0.962 at lit 44,
0.863 at lit 50) — so packing the x0 residues two to a register, which
would only buy that deeper window, is declined on this measurement.

**Two caps, both found by gates.** G18 failed at A219761's opening:
twelve conditions reach 0.0035 only far down the prime list, and the kernel
compiled to 106 registers and 4 blocks. So the window stops at `LIT_MAX` =
40 primes (the hour filters take 38–39). G14 then failed at a ten-
condition gate filter whose rounds reached 1e-4 only past q = 16,000 — two
thousand generated round tests — so the in-block rounds stop at
`K2_ROUND_PRIMES_MAX` = 128 primes past the window (98–99 at the hour
filters). And the capped window left one shallow gate configuration a first
queue of 33 items a thread, past the rounds' 32-bit survivor mask: the
queues are now capped at 32 × tpb entries (overflow is the harmless
in-block fallback, G14's forced-overflow drill).

### Change 5 — the narrow rounds reduce once per pack of primes: 1.015x (`ROUND_MOD32`)

One 64-bit Barrett step to M = the product of up to three consecutive round
primes (M < 2^31), then a 32-bit step per prime; both are the
one-conditional-subtraction reduction with the floor magic, exact for every
numerator below the word. A third of the rounds' arithmetic gone for
**1.015** (packs of two: 1.008): the rounds are latency-bound, not
multiply-bound. G20's round drill runs it (q2 = 128: packs of three,
inline groups mixed in) against the CPU engine.

### Change 6 — the live words stay in registers: 1.054x (`EXTRACT_REGS`)

The inherited kernel stored each residue's live words to a shared buffer
and read them back twice (the count, the extraction): 5 stores and 10 loads
a residue in a kernel bound by shared-load issue. Unrolled over the XE
residues, they stay in registers. **1.054** at n = 19* (xe = 1: 1.027; xe =
4: 0.944 at 104 registers), stream identical, 5 KB of shared memory a block
freed (19.2 → 14.0 KB). It does not buy a sixth block: capping the kernel at
80 registers for one reads 0.930, and so do bigger blocks (0.945–0.962).

**XE is now chosen by registers**, because it costs NW registers per extra
residue and no shared memory: free at n = 19* (88 registers either way;
xe = 2 wins by 2.3%), a loss where the window sits at `LIT_MAX` (A034881
n = 16 and 17*: 96 registers against 87 and 91, xe = 1 at **0.917 and 0.926**
of the clock), a tie at A219761 n = 17* and 18*. An engine not told its xe
compiles xe = 1 as well and keeps it when it needs fewer registers.

### Measured and not taken

| idea | result | reading |
|---|---|---|
| window-coordinate rounds on the NARROW record (`ROUND_WINDOW_NARROW`) | **0.957**; 0.909 with the deeper window | its rows cost a block per SM; as in clique-ladders round 2, narrow keeps Barrett rounds |
| pairs of window primes CRT-combined (`bit_group_max` 3000 / 6000) | 1.007 / 1.027 (the second only by changing the block shape) | a pair's table spans all 32 banks; priced before pairs, dominated after |
| 16-byte (quad) window tables | priced at 7.0 clk a prime against pairs' 6.7 (NW = 5) from the pipe table | `LDS.128` is data-path bound at 4 wavefronts |
| the residue loop unrolled by 2 | 1.002 | |
| `__launch_bounds__` for a 6th block | 0.930 | the spill and lost ILP cost more than the warps return |
| balanced first-level chunks (no small last launch) | 0.995 / 0.991 | the small launch's fixed cost is noise |
| the prologue precomputed | ≤ 1.014 if free | its latency is hidden behind other blocks |
| constants re-swept on v2 at n = 19*: `CAND_PER_LAUNCH4` 2^36 / 2^38, `TAIL_ROUND_DROP` 0.5 / 0.85, `UNROLL` 2 / 8, `R2_DROP` 0.35 / 0.7 | 0.996 / 1.007, 0.994 / 0.992, 1.006 / 1.011, 0.994 / 0.987 | flat; unchanged |
| the sieve depth 2^15 / 2^16 / 2^18 against the planned 2^17 | 0.993 / 1.012 / 1.000 (survivors 105,075 / 32,778 / 3,903 against 11,147) | flat on the device; the planned depth stays (the host is 0.1–0.3 core-s/s) |

### The plan, paired against its neighbours (expected clock to a confirmed find)

| filter | plan p3 | the neighbours, as a multiple of the plan's clock |
|---|---|---|
| A034881 n = 16 (open) | to 37 × 160 | 128 periods 0.93–1.02, 224 periods 0.935; the wheel to 41 1.027, to 31 1.453 (at 2–4 s of device: launch overhead, not rate) |
| A034881 n = 19* | to 53 × 160 (157 live) | 128 periods 1.095; 224 clamped 1.36; the wheel one prime shorter 1.307; 47 for 53 1.028 |
| A219761 n = 17* | to 47 × 160 | 128 periods 1.017, 96 1.026, one prime shorter 1.065 |
| A219761 n = 18* | to 47 × 160 | 128 periods 1.078, 192 1.057, one prime shorter 1.317, 53 for 47 1.026 |

### Round 1 result

Old engine and old plan against new, paired, expected device clock to a
confirmed find at each filter the campaigns pass through (the old arm is v2
with every new flag off, the inherited constants and the p2 plan named
explicitly — the v1 code path, kept runnable for exactly this):

| filter | v1 / p2 | v2 / p3 | ratio |
|---|---|---|---|
| A034881 n = 16 (open) | 5.1 s | 4.1 s | 1.27 |
| A034881 n = 17* | 97 s | 69 s | 1.46 |
| A034881 n = 18* | 0.57 h | 0.43 h | 1.34 |
| A034881 n = 19* | 15.3 h | **10.7 h** | **1.43** |
| A034881 n = 20* | 543 h | 375 h | 1.45 |
| A219761 n = 16* | 4.9 min | 3.9 min | 1.26 |
| A219761 n = 17* | 2.03 h | **1.57 h** | 1.29 |
| A219761 n = 18* | 55.4 h | **39.3 h** | **1.41** |

Kernel-only and campaign-loop are the same number here: the loop was
measured at 1.00 of the device (Measurement 3) and nothing in this round
touched the host path. The campaign-loop A/B proper is the owner's, in the
first `[STATUS]` lines of a campaign — no agent starts one.

`python launch.py --selftest`: **49/49 ALL GREEN in 249 s** (the first run
after the kernel changed; every new configuration compiled cold once), and
**49/49 in 205 s** warm after the last change. `python score.py`: every
gate green, all five fingerprints reproduced, **SCORE 12,843,855,387** and,
after the last change, **13,931,799,430** — on the RE-FROZEN opening shape
(160 periods), so compare the anchors, which did not move: SCORE2L 5,422 →
7,028 and 6,518, SCORE1L 2,812 → 3,075 and 3,073, SCORE9 4.50 → 4.35 and
3.08. Single readings move ~10%, and SCORE9 (8.1 million survivors) is
host-bound; paired on its own shape it is a tie, 1.005.
Before re-freezing, all five v1 fingerprints were reproduced bit for bit by
v2 at the v1 windows; the two new campaign fingerprints were computed by
the v2 and the v1 code paths alike.

**What the gates caught this round**, all fixed before the result above:
G14 twice (the doubled table past the 48 KB static limit; the rounds run
away at few conditions), G14 once more (a queue past the 32-item mask) and
G14's own new check (the plain layout unchecked); G18 (106 registers at
A219761's opening); `_families_stay_apart` (the benchmark shapes no longer
the plan — re-frozen); and `_rediscovery_run_drill`, which bounded its run
"just past a(12)" and was overtaken by the 160-period segment at n = 13,
which reached the published a(13) and found it, correctly. The drill now
accepts further finds that are exactly the next published terms, in order,
evidenced like the others, and says so.

### Termination table (OPTIMIZATION.md Part 3), after round 1

A034881 n = 19*, the planned configuration: sieve kernel ~93% of device,
tail rounds ~7%.

| phase | share of wall | verdict |
|---|---|---|
| the window sieve (+ prologue, x0) | ~65% | **roofline**: bound by shared-load issue (0.455/clk/SM measured) at ~0.44/clk after pairs; 3 loads for 5 words is the pair table's floor, a quad table prices worse (`LDS.128` data-path bound), pre-shifted tables are 32x the memory. The one lever left on it is fewer window primes per candidate, which is the wheel's (below) |
| in-block rounds | ~19% | latency-bound: a third of its arithmetic removed returned 1.015; window-coordinate rounds lose a block (0.957). Unsearched: a two-prime CRT table for the round primes (half the table loads at L2 latency) |
| extraction | ~7% | registers (Change 6); what is left is the queue stores themselves |
| tail rounds | ~7% | flat in its constants and in the depth |
| host, the loop off-device | 0% | device = wall |

### Priced and unbuilt, best first

1. **The full wheel to 53 at A034881 n = 20*: 1.23x** (0.813 of the plan's
   clock: 3.67M first-level residues on the wide record, 160 periods). The
   one thing keeping it out of the plan is `R1_MAX` = 2^21. Raising it to
   2^22 was tried and REVERTED this round, because it also (a) re-splits
   the wheel at every other filter (29 into the first level — a tie at
   n = 19*, 1.011, but a change to both frozen opening shapes) and (b)
   makes the planner take the full wheel at A219761 n = 18*, where it
   measured **1.26x slower**: the wide engine there falls back to an (8, 2)
   block at 104 registers (the window-coordinate rounds' rows take shared
   memory), and even at the better (16, 1) it only reaches 1.021 of the
   current plan (its segment is 0.9 medians). To ship: the wide record's
   shape rule re-swept, `CREL_WIDE` split by `rwin`, then R1_MAX = 2^22 with
   the plans re-checked at every filter. Device memory 1.44 GB against
   0.21 GB (the rounds' rows are 0.73 GB of it). A034881 a(20) is a
   multi-week filter, not a night's.
2. **A find truncates its segment** (the rest of the find's segment swept
   only up to the find's period — the engine's `sweep(j0, jf + 1, u_from)`
   already does it): saves about a quarter segment, **~8% at A219761
   n = 17*** (its segment is 0.75 medians; 6 minutes of a night), ~1% at
   A034881 n = 19*, nothing at A219761 n = 18*. Needs the truncation in the
   cursor (a resumed truncated segment must know its bound) and in the
   promotion and rediscovery drills.
3. **Choosing xe (and the shape) by measurement at each build**, instead of
   by register count: the register rule matches five of five filters
   measured; a timed choice would catch the next one it does not.

## Open

1. **Frozen shapes past the openings.** Rule 5g owes a shape at every
   filter a campaign opens; the filters after a find are planned from the
   real term and did not exist when the shapes were frozen. Since the hunt
   (2026-09-29 to 10-01, RESULTS.md) the live filters are **A034881 n = 20**
   and **A219761 n = 19**, both real now. Add one shape per family before
   either is resumed, and re-check the plan against its neighbours there
   (the ten-minute harness of the table above). The real filters plan
   differently from their stand-ins (`launch.plan_for` with the finds
   registered in a scratch process, 2026-10-01): A034881 n = 20 takes the
   wheel to 53 without 43, where the stand-in took the full wheel to 47.
   So Priced and unbuilt item 1, the full wheel to 53 at A034881 n = 20*,
   has to be re-priced on the real filter, against a plan that already
   carries 53.
2. **A219761 n = 18 ran at 0.72× its stand-in price** (5.8e16 a(n)-line/s
   over the 43 h leg against 8.0e16 priced at n = 18*), while A034881's
   n = 18 and 19 legs ran 1.1× theirs. The real filter planned the wheel to
   53 without 43, and the stand-in had planned the full wheel to 47. Not yet
   measured: pair the two plans at the real n = 18 filter. If the plan is
   the cause, the planner mis-picks the wheel there. Item 1 of Priced and
   unbuilt records the same failure for R1_MAX at A219761 n = 18*, where
   the full wheel to 53 measured 1.26x slower.
3. **The single-launch openings** (A219761 n = 12–14) are milliseconds to
   seconds and measure launch overhead, not rate; not worth an engine
   change.
