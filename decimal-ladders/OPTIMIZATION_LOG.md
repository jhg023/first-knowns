# OPTIMIZATION_LOG — decimal-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt → measurement → kept/rejected, failures included. The process
is [OPTIMIZATION.md](../OPTIMIZATION.md) and [INNOVATION.md](../INNOVATION.md).
The engine is inherited (clique-ladders' kernel, itself factorial-ladders'
v3 on lcm-ladders' v1 window sieve), so every constant started stale; this
file says which were re-measured here and what moved.

Harness method (scratchpad only, rule 9; rewritable in ten minutes): build
engines through the engine API with explicit plans or module-constant
overrides (`_MODCACHE` cleared between arms, kernel-source ablations applied
by a `cupy.RawModule` wrapper in the harness, never in the engine); run each
arm as ONE continuous `sweep` across segments far above the campaign floor
for 3–5 s, the rate taken over the second half; a 3 s warm-up arm first;
arms rotated over 2 rounds; survivor sets compared across arms that cover
the same candidates. **Read "Measurement 3" before trusting any short-arm
number from another project on this GPU.**

---

## v1 (2026-09-24) — the build

The kernel needed no mathematical change: every problem-specific quantity
enters through `killed_residues` (K(q,n,F) = { −10^−j mod q }). What the
regime changed, and the two bugs the first battery found, are in
Measurements 1–2 and the notes under them.

### Measurement 1 — the regime

* w(q,n,F) = min(|J|, ord_q(10)). The primes with 10 as a primitive root
  kill |J| residues (≈ the linear ladders' law); the small-order primes are
  weak and saturate at their order (3: 1, 11: 2, 37: 3, 101: 4, 41: 5,
  13 and 7: 6, 73: 8, 53: 13, 31: 15). 2 and 5 kill nothing for A305740;
  for A153431 the x + 1 form makes 2 forced and 5 a one-residue prime.
* **Forcing is by primitive roots**: 7 from six forms, 17 from sixteen, 19
  from eighteen — so the unit grows with the filter (A305740 7 → 119 → 2261,
  A153431 14 → 238 → 4522), the period changes at those promotions, and the
  forced class is always 0 (x ≡ 0 makes every form ≡ 1).
* The model validates (G11): pooled mean E = 1.63 over 14 draws (A305740
  2.06 over 7, A153431 1.20 over 7), spread 0.00–5.38.
* Medians (chained from the published frontiers): A305740 a(13) 2.6e14,
  a(14) 9.9e15, a(15) 7.8e17, a(16) 1.0e20, a(17) 7.5e21, **a(18) 8.6e23**,
  a(19) 4.7e25; A153431 a(14) 1.3e18, a(15) 1.6e20, a(16) 1.2e22,
  **a(17) 1.4e24**, a(18) 7.5e25.

### Two engine hazards the first battery caught

1. **A list-valued wheel level could be dropped in silence.** The inherited
   `GpuEngine` tested `p2 > p1` to decide whether level 2 exists — a
   lexicographic comparison when the levels are lists. A level whose
   smallest prime sat below level 1's would have been dropped from the wheel
   *and* (the sieve being the complement of the named wheel) from the sieve.
   Nothing planned here produced one, but the planner's non-contiguous
   splits make it reachable. Replaced by an explicit presence test, and the
   engine now **refuses any wheel whose built prime set is not the named
   set** (the ceiling drill builds the empty-middle-level shape and requires
   the refusal).
2. **The in-block round mask.** A shallow gate configuration planned a round
   queue of 4,416 entries (35 items per thread) and the kernel raised (the
   survivors of a round ride one 32-bit mask per thread). Queue capacities
   are now capped at 32 × tpb — overflow is harmless by design (the item runs
   its tail on the spot, G14 and G20 force it).

### Measurement 2 — the inherited engine at this project's filters (the baseline)

Steady-state (method above), the inherited planner's own plan:

| filter | plan (inherited planner p2) | x/s | candidates/s |
|---|---|---|---|
| A305740 n = 18 | wheel to 67 (12 primes), WIDE, 224 | 3.83e18 | 2.06e12 |
| A153431 n = 17 | wheel to 67 (12 primes), narrow, 224 | 8.52e18 | 2.42e12 |

At those rates A305740 a(18)'s median is 62 h of device and A153431
a(17)'s 44 h. Phase split (CUDA events): the sieve kernel 86–90%, the tail
rounds 10–14%; inside the sieve kernel by ablation (steady): the window
65–69%, extraction 7–9%, in-block rounds 17–19%.

---

## Round 1 (2026-09-24)

### Measurement 3 — THE GPU IS POWER-CAPPED, AND SHORT A/B ARMS LIE

Under this kernel the RTX 4090 sits at its power limit (448 W of 450 W,
`clocks_event_reasons` = SW power cap) at 2.70–2.76 GHz. The first harness
here ran each arm as a burst of ~1 s with host set-up between bursts, the
way several earlier projects' harnesses did — and on a power-capped GPU the
idle gaps let the clock boost, so an arm's rate depended on its launch
shape rather than its kernel. Two conclusions it produced were **wrong and
were reversed** by the steady harness (one continuous sweep per arm, the
rate over its second half):

| question | short arms said | steady-state says |
|---|---|---|
| launch budget 2^35 vs 2^37 (A153431 n = 17) | 2^35 **1.08×** | 2^35 **0.95×**; 2^37 best at all four hour-scale filters (2^36 0.90–0.98, 2^35 0.89–0.97, and 0.73 at A153431 n = 16) |
| A305740 n = 18: narrow 11-prime wheel vs the planned wide 12-prime wheel | narrow **1.09×** | narrow **0.96×** (the wide plan's longer launches were charged more set-up per burst) |

A 25-second burn confirmed the first reversal directly (2.10e12 against
2.03e12 cand/s). Every ratio below is steady-state; OPTIMIZATION.md Rule 3's
"interleave" is necessary on this GPU and not sufficient.

### Measurement 4 — where the wide record costs (A305740 n = 18)

On the SAME 11-prime wheel, the wide record at 224 periods reads **0.80** of
the narrow one (clique-ladders measured 0.93 on its filters); on the SAME
record (narrow, 64 periods), the 12-prime wheel's candidates cost 29% more
than the 11-prime wheel's (41 window primes against 38, 2.09M first-level
residues against 0.11M, 104 registers against 88). Forcing 5 blocks per SM
with `__launch_bounds__` (96 registers, 32 bytes spilled) reads **0.992–0.999**
— occupancy at 4 blocks costs nothing here. `LAUNCH_MIN_BLOCKS` stays 0,
and **G18's floor is lowered to 4 blocks per SM** on that measurement (every
fastest configuration below runs at 4).

### Measurement 5 — the window loop, read in SASS (INNOVATION.md Part 2)

NVRTC → PTX → `ptxas -arch=sm_89` → `nvdisasm` (wheels unpacked in the
scratchpad). The window block of one second-level residue at A153431 n = 17
(38 window primes, NW = 7): **952 instructions — 305 `LDS`, 266
`SHF.R.W.U32` (the funnel shifts), 209 `LOP3.LUT`** (the compiler already
fused a fifth of the 266 ORs), 40 `IADD3`, 38 `SHF.R.U32.HI` — i.e. per prime
per 224 candidates: 8 loads, 7 shifts, ~5.5 ORs, ~2 index ops.

### Measurement 6 — THE WINDOW AS OVERLAPPING VECTOR TUPLES: 1.08–1.14×, kept (`WINDOW_VEC` = 2)

The invariant of the window loop is "the pattern is a bit string stored as
32-bit words; a window is NW + 1 words funnel-shifted". Alternative
representations of the same bits (INNOVATION.md §1.1, word size and limb
shape), each checked survivor-for-survivor against the scalar kernel:

| representation | loads per prime | shared | A153431 n = 17 | A305740 n = 18 |
|---|---|---|---|---|
| 32-bit words (inherited) | 8 `LDS` | 1× | 1.000 | 1.000 |
| 2 word-shifted copies, `uint2` loads from the copy the alignment picks | 4 `LDS.64` | 2× | 1.061 | 1.097 |
| **overlapping tuples: element m = (word m, word m + 1), the window is elements w, w + 2, w + 4, w + 6 — no copy to select, no multiply** | 4 `LDS.64` | 2× | **1.085** | **1.143** |
| overlapping 4-tuples (`uint4`) | 2 `LDS.128` | 4× | 0.888 | 0.975 |
| 4-tuples with `__launch_bounds__(128, 4)` and the queue margin cut to 2.5 / 1.5 | 2 `LDS.128` | 4× | 0.907 / 0.831 | 0.695 / 0.633 |
| 4-tuples read through L1 (`PAT_SHARED` off), carveout 100 / 75 | 2 `LDG.128` | — | 0.841 / 0.838 | 0.814 / 0.814 |
| 2-tuples through L1, carveout 75 | 4 `LDG.64` | — | 0.870 | 0.783 |

The 2-tuple layout costs a block at A153431 n = 17 (5 → 4) and wins anyway.
4-tuples lose on shared memory (30.5 KB a block, 3 blocks) and registers
(128–130). G14's window-chain check reads word w at u32 index `vec·w` of
the group's region, so it checks the layout the kernel reads.

**The loop is now at a named roofline.** Differential ablation (timing only,
extraction starved so the kill count cannot move the downstream work):
confining every window to the first 4 words of its table — no bank
conflicts, same instructions — reads **1.003**, so conflicts cost nothing;
and at 4.1–4.7e12 window-only candidates/s the loop issues ~0.38 warp-wide
`LDS.64` per clock per SM, 256 bytes each, **≈75% of the SM's 128 B/clock
shared-memory bandwidth**. Instructions are not what binds: fusing two
groups' ORs into three-input `LOP3`s (`WINDOW_PAIR`) reads **0.999 / 1.003**.
Only fewer BYTES can help, and the one byte-reducing lever — CRT-pairing
window primes so one window serves two (`bit_group_max`) — pays for its
larger tables in occupancy: 3000 / 6000 / 10000 read 1.000 / 1.004 / 0.710
(A153431 n = 17) and 1.003 / 0.912 / 0.675 (A305740 n = 18). Declined.

### Measurement 7 — the constants, re-swept on the new window

The window got cheaper per prime, so the window/rounds balance point moved:

| knob | values | A153431 n = 17 | A305740 n = 18 | verdict |
|---|---|---|---|---|
| `BIT_SURV` | .01 / .007 / .005 / **.0035** / .0025 / .0018 / .0012 | 0.83 / 0.92 / 0.98 / **1.000** / 0.988 / 0.927 / 0.869 | 0.75 / 0.94 / 0.98 / **1.000** / 0.929 / 0.896 / 0.870 | **moved .007 → .0035** (1.087 / 1.063 over .007) |
| `K2_SURV4` | .0006 / **.0003** / .00015 | 0.981 / 1.000 / 1.007 | 0.993 / 1.000 / 0.873 | unchanged |
| `R2_DROP` | .4 / **.5** / .6 | 0.997 / 1.000 / 0.998 | 0.989 / 1.000 / 0.974 | unchanged |
| `TAIL_ROUND_DROP` | .5 / **.7** / .85 | flat (±0.3%) | flat | unchanged |
| `CAND_PER_LAUNCH4` | 2^35 / 2^36 / **2^37** / 2^38 | 0.95 / 0.98 / 1.000 / — | 0.89 / 0.91 / 1.000 / 0.96 | unchanged (Measurement 3) |
| `MASK_BITS` | 512 / 1024 / 2048 / **4096** | 0.926 / 0.974 / 0.999 / 1.000 | 0.933 / 0.973 / 1.000 / 1.000 | unchanged |
| `UNROLL` | 2 / **4** / 8 | 0.994 / 1.000 / 0.997 | 0.997 / 1.000 / 1.002 | flat |
| `ROUND_WINDOW` on the narrow record | off / on | 1.000 / 0.994 | (A305740 n = 17) 1.000 / 0.973 | off (clique's verdict holds) |
| `X0_SHARED` | off / on | 1.000 / 0.816 | (n = 17) 1.000 / 0.599 | off |
| block shape at 224 | (8, 1) / (16, 1) | 1.000 / 0.975 | (n = 17) 1.000 / 0.964 | unchanged |
| `ROUND_WINDOW` on the wide record | on / off | — | 1.000 / 0.839 | on |

### Measurement 8 — the plan at every filter, MEASURED (`MEASURED_PLANS`)

The inherited planner ranks (wheel, window) pairs by a rate model calibrated
on clique-ladders' kernel; here it was wrong in every factor it carries (the
width curve is steeper, the wide record costs 0.80 not 0.93, and 1/lit does
not predict the rate). So the plan at every filter a campaign opens at or
promotes into is chosen by measurement: the Pareto frontier of (period,
density) wheels the kernel can split (not only greedy prefixes) × windows
of 128–256, the model's best eight or nine, each run steady-state, ranked by
MEASURED expected clock to a confirmed find (expected sweep to the close of
the find's segment × density / candidate rate). `plan()` returns the table
entry for those filters and the model's pick elsewhere; the depth is still
`plan_q2`'s and the record still the engine's.

| filter | measured best | x/s | the model's pick, measured |
|---|---|---|---|
| A305740 n = 13 | to 43 (9 primes), 192 | 3.9e15 | 1.21× slower |
| A305740 n = 14 | to 47 (10), 192 | 1.8e16 | 1.06× |
| A305740 n = 15 | to 53 (11), 192 | 9.1e16 | 1.08× |
| A305740 n = 16 | to 61 (10, no 11), 224 | 3.7e17 | 1.07× |
| A305740 n = 17 | to 67 (11, no 11), 224 | 1.14e18 | 1.05× |
| **A305740 n = 18** | **to 67 (11: keeps 11, drops 53), 256, narrow** — corrected, Measurement 10 | **~4.5e18** | 1.08× (wide, 224) |
| A305740 n = 19 | to 71 (12), 256, wide | 8.7e18 | 1.00× |
| A153431 n = 14 | to 59 (11), 224 | 2.8e17 | 1.68× |
| A153431 n = 15 | to 61 (11), 256 | 8.3e17 | 1.02× |
| A153431 n = 16 | to 61 (12), 224 | 3.15e18 | (the model's pick) |
| **A153431 n = 17** | **to 61 (12), 256** | **1.01e19** | 1.01× |
| A153431 n = 18 | to 67 (12), 224 | 1.89e19 | (the model's pick) |

Differences under ~1% between the top entries are inside the noise; the
table takes the measured best either way.

**SUPERSEDED by Measurement 12.** Every rate in this table (and in
Measurements 3, 4, 6, 7, 10 and 11) was computed as launches ×
`cand_per_launch`, which overcounts by 1.12–1.30× and differently per
launch geometry. Comparisons between arms of the SAME geometry stand;
comparisons across geometries (this table above all) did not.

### Measurement 9 — every opening priced through the campaign's own path (5g)

The campaign's `calibrate()` on a scratch checkpoint promoted to each filter
(run() never called; a 1-second cold measurement, so its rate is below the
steady figure — it sizes the pool, not the ETA):

| filter | survivors/s | µs each | core-s/s | pool |
|---|---|---|---|---|
| A305740 13 / 14 / 15 / 16 / 17 / 18 / 19 | 73k / 32k / 82k / 96k / 17k / 7.9k / 11k | 12–21 | 1.50 / 0.52 / 1.08 / 1.34 / 0.20 / 0.10 / 0.15 | 4 / 2 / 3 / 3 / 1 / 1 / 1 |
| A153431 14 / 15 / 16 / 17 / 18 | 87k / 109k / 17k / 22k / 8.8k | 12–13 | 1.16 / 1.42 / 0.21 / 0.26 / 0.11 | 3 / 3 / 1 / 1 / 1 |

The segment loop, off-device (OPTIMIZATION.md 2.14): `check_rungs` +
`ladder` + `next_rung` 12 µs, `mark_boundary` 2.3–2.8 µs, the cursors and the
proof-crossing check 1.4–2.1 µs, `status_line` 7–10 µs, against launches of
44–131 ms. A ladder REBUILD (one per find, ~0.6 s of model integrals) is the
only model cost and it is not in the loop. **The launcher's host path
(`_submit` → pool → `_drain` → back-pressure, driven from a scratch harness
on a far window with one worker) runs at 0.992 (A153431 n = 17) and 0.994
(A305740 n = 18) of the device alone, with no host wait.** The loop is the
device.

### Measurement 10 — the n = 18 entry did not reproduce, and was corrected

The first search at A305740 n = 18 picked a wheel to 67 without 11 (4.86e18
in its run). Repeat runs, three and four rotated rounds with the median
taken, did not reproduce it: the consistent winner keeps 11 and drops 53
(`(3,11,13,23,29,31),(43,47,59),(61,67)` at 256, narrow), about 4.8% ahead
of the first entry in the same run. The absolute rates drift about 10%
between runs (the clocks sat ~3% lower later in the night), while the
comparisons inside one run stayed consistent, so the table holds the
repeated winner and the SCORE shape was re-frozen to it (BENCHMARKS.md).
The same-run ratio against the inherited engine and plan at n = 18 is
**1.18×** (3.84e18 → 4.51e18 k/s). What the first single run shows: **a
plan search at the long leg needs at least three rotated rounds**
(a scratch harness, three rotated rounds, median).

### Measurement 11 — the rest of the leftovers, each priced

Steady harness, paired against the shipped configuration at A305740 n = 18
and A153431 n = 17:

| attempt | ratio | verdict |
|---|---|---|
| x0 through `ld.global.cg` / `.cs` | 1.00 | nothing to buy |
| the level-1 residue in the hot path (`res1x`) | 1.00 | declined |
| two-bit level-2 kill (`g2bits`) hot | not comparable: it changes the kill density | invalid ablation, recorded so it is not repeated |
| a single round table instead of per-level tables | 0.97 | declined |
| tail rounds on a second stream, overlapped | 1.000 | removed (`TAIL_STREAM`) |
| queue depth 32768–65536 | ≤ 1.012, costs host | declined |
| `__launch_bounds__` min blocks 5 | 0.99 | removed (`LAUNCH_MIN_BLOCKS`) |
| cycles per launch 2^35 / 2^36 / 2^38 | flat | unchanged |
| the round window on the narrow record | 0.97–0.99 | removed (`ROUND_WINDOW_NARROW`) |
| window pairs (`WINDOW_PAIR`) | ≤ 1.004, costs occupancy | removed |
| window x2 unroll | registers blow up | invalid ablation |

`BIT_SURV` = 0.0035 was re-checked at A305740 n = 17 and A153431 n = 16
and holds. G21 was added to the battery: the tuple window at vec 1 / 2 / 4
× windows 160 / 224 / 256, narrow and wide, against the CPU engine, so the
declined widths stay proved correct in case a later GPU changes the price.

### Measurement 12 — THE RATE WAS OVERCOUNTED, AND IT CHOSE THE PLANS

A launch of the window engine covers `tchunk` first-level residues of one
unit, and R1 is not a multiple of `tchunk`: at A305740 n = 18 on the narrow
wheel R1 = 110,880 = 6 × 18,048 + 2,592, so every seventh launch is 14% of a
full one. Every harness here, `score.py`, and the launcher's `calibrate()`
credited each launch with the full `cand_per_launch`. The overcount is 1.14×
for that geometry and 1.30× for the wide record on the same wheel (its launch
budget is twice the narrow one's: 3 × 36,096 + 2,592) — so every cross-
geometry comparison was biased, toward the narrow record and toward short
launches. Found because the wide record read 1.083× the narrow one on the
same wheel, where Measurement 4 had it at 0.80.

Fixed in the engine: `GpuEngine.launch_cum` is the exact prefix sum of each
launch's candidates in `_sweep`'s order, `line_between(u0, u1)` the line they
cover; `progress_k`, `calibrate()` and `score.py` read it, and the harness
does the same. Fingerprints are unaffected (the work is unchanged); SCORE
fell from an overcounted 4.17e18 to an honest one (3.7e18 on the old shape).

**The plan search, re-run on exact counts** (the same Pareto shortlist, the
wide record's model penalty lowered from 0.76 to 0.90 and the best wide
candidates forced into it; three rotated rounds, median):

| filter | new plan | x/s | over the old entry, same run |
|---|---|---|---|
| A305740 n = 13 / 14 | unchanged | 3.86e15 / 1.70e16 | (within 0.4%) |
| A305740 n = 15 | to 53 (11), **224** | 7.19e16 | 1.027× |
| A305740 n = 16 | to 61 (11, with 11), 224 | 3.70e17 | 1.038× |
| A305740 n = 17 | to 61 (12, with 11), 224 | 1.13e18 | 1.089× |
| **A305740 n = 18** | **to 67 (12), 224, WIDE** — the inherited planner's own pick | **4.66e18** | **1.134×** |
| A305740 n = 19 | unchanged (to 71, wide) | 8.72e18 | — |
| A153431 n = 14 | to 47 (11), 256 | 1.51e17 | 1.035× |
| A153431 n = 15 | to 59 (11), 224 | 8.12e17 | 1.028× |
| A153431 n = 16 | to 67 (12), 256 | 2.52e18 | 1.052× |
| **A153431 n = 17** | **to 67 (12), 256, narrow** | **9.93e18** | 1.015× |
| A153431 n = 18 | to 67 (13), 256, WIDE | 1.92e19 | 1.086× |

A153431 n = 17's wide 13-prime wheels run faster (1.05–1.06e19 m/s) and lose
anyway: one segment is 24–30% of the expected sweep, and a find's segment
has to close. **Against the inherited engine and plan, same run, exact
counts: 1.214× at A305740 n = 18 (3.84e18 → 4.66e18) and 1.196× at A153431
n = 17 (8.30e18 → 9.92e18).** The four campaign benchmark shapes were
re-frozen at the new plans (BENCHMARKS.md).

Re-swept on the new plans and exact counts: `CAND_PER_LAUNCH_WIDE` 2^36 /
2^37 / **2^38** / 2^39 read 0.968 / 0.985 / 1 / 1.005 and `CAND_PER_LAUNCH4`
2^36 / **2^37** / 2^38 / 2^39 read 0.987 / 1 / 1.006 / 1.009 (declined:
launches twice as long for under 1%); `TAIL_FILL` 2^12 … 2^23 flat within
0.5% at the default; `BIT_SURV` and `lit` directly (49–54) within ±1.5%
with register effects mixed in; `K2_SURV4` .0002 / **.0003** / .00045 /
.0006 read 0.999 / 1 / 0.962 / 0.991. Nothing moved.

Openings re-priced through `calibrate()` (Measurement 9's method, the
ladder warmed first — a cold first `ladder()` inside the timing loop reads
300 µs per launch and is the one model build a find costs, not a
per-launch cost): pools A305740 4 / 2 / 3 / 2 / 1 / 1 / 1 and A153431
2 / 3 / 1 / 1 / 1, the loop's rung check 5–7.5 µs per launch.

### Measurement 13 — where the rest of the time goes, and what is left

The phase split of the A305740 n = 18 plan (ablations, exact counts): window
61%, extraction 7%, in-block rounds 18%, tail rounds 14% (CUDA events: the
sieve kernel 93.5 ms and 31 tail kernels 15.1 ms per launch; the first
fifteen, one lane per item over queues of 81M down to 0.5M, take 11.5 ms and
stream ~5 GB of queue).

**The window is bound by neither shared-memory wavefronts nor the integer
pipe alone.** Removing every funnel shift (timing only) buys 1.090; a LOP3
in its place 1.067; replacing the four tuple loads with arithmetic LOSES
(0.975); bank conflicts cost nothing (Measurement 6). It is bound by
instruction issue in the mix; the per-candidate instruction count is the
lever, and the priced ways to cut it (4-tuples, CRT pairs, pre-shifted
copies) cost more in shared memory than they save.

A real 5th block per SM (spb 4, `__launch_bounds__(128, 5)`, 17.9 KB) reads
0.917 against spb 4's 0.914 at 4 blocks: occupancy is not the lever
either. Window 128 with its own block shape reads 1.01–1.02 against 256 on
the narrow plan; windows above 256 would need a ninth period bit in the
queue entry, priced from that curve at under 2% and declined.

**Declined with a price:**

- **A 13-prime wheel at A305740 n = 19** (adding 53: 24.5% fewer
  candidates). The wide record would take W' = 1.6e19 (the one-subtraction
  step is exact to 2^64, G19), but no split exists under the two u32 level
  moduli: W1 would have to lie in [3.8e9, 4.3e9] and no subset of the
  thirteen primes has that product, and relaxing the R2 / R3 grid limits
  does not change that. A u64 second level or a fourth level is a new
  engine version for a 61-day leg; the bound was left at 2^63, where the
  gates exercise it.
- **Capping the find's segment at the find's period.** A find has to close
  its segment (candidates arrive out of order), but only periods at or below
  the find's matter after it: capping the remaining launches there halves
  the expected overshoot. At A305740 n = 18 the segment is 7% of the
  expected sweep, so this is ~1.7% there and 0.25% at A153431 n = 17, for a
  sweep generator whose period range changes mid-segment and a new coverage
  claim at the cursor. Declined on the risk.

### Measurement 14 — THE PER-BLOCK SETUP ON EVERY THREAD: 1.01–1.16×, kept

Where the sieve kernel's time goes, by deletion (timing only; CUDA events
per launch at A305740 n = 18): the whole kernel 97.1 ms; window-only 68.0;
the window groups deleted as well 17.6; and the block's setup deleted on top
of that 10.4. **The setup — ne[ss][g], the per-block offset of every window
and round-window group — cost 7.3 ms of a 113 ms launch.** The inherited
kernel compiled it per group into the SPB = 8 leading threads (two u64
Barrett steps and two reductions per group, ~125 groups), with a quarter
of a warp's lanes live while the rest of the block waited at the barrier.
(The same deletions explain a puzzle: the window-only kernel was barely
faster at 14 window primes than at 53 and SLOWER at 1, because every prime
the window drops becomes a round-window group whose setup is serial.)

Now the (ss, group) pairs are spread over all TPB threads after one barrier,
each group's (Q, Barrett magic, Dinv) read from a small table and its
destination from a second (bit 31 marks a round-window group, with its
jmod2 index and u16 slot). The arithmetic is the same one-subtraction step,
exact for every u64 (G19), so the offsets are identical; every frozen
fingerprint reproduced before the serial path was deleted, and the battery
is green on the parallel one. Same run, exact counts:

| filter | parallel / serial |
|---|---|
| A305740 n = 13 / 14 / 15 / 16 / 17 | 1.157 / 1.042 / 1.018 / 1.034 / 1.021 |
| **A305740 n = 18** | **1.039** |
| A305740 n = 19 | 1.018 |
| A153431 n = 14 / 15 / 16 | 1.020 / 1.026 / 1.010 |
| **A153431 n = 17** | **1.014** |
| A153431 n = 18 | 1.016 |

The x-space anchor SCORE9 (n = 9, microsecond launches) reads 0.86: one
more barrier per block where there is almost no work per block; no campaign
runs there. Re-swept after the change: the block shape ((8, 1) still best;
(16, 1) 0.984 / 0.974 and (4, 1) 0.935 / 0.943 at the two long legs) and
the plans at both long legs (both hold; the nearest rivals 1.007 and
1.013).

**Against the inherited engine and plan** (its rate measured earlier the
same night in the same exact-count harness, since the serial setup is no
longer in the tree to pair against): **A305740 n = 18 3.84e18 → 4.83–4.85e18
k/s (≈1.26×); A153431 n = 17 8.30e18 → 1.005–1.01e19 m/s (≈1.21×).**

**The live words counted as they are written** (the extraction counted
them by re-reading the seven words of the row from `sal`; now the count is
accumulated in the loop that writes them): 1.015× at A305740 n = 18 and
1.016× at A153431 n = 17, same run, every fingerprint reproduced. Kept.
**The round-window rows stored word-major** (`x0r` on the device as word w
of every first-level row, then word w + 1, where it was row-major at 176
bytes a row: a round reads two or three words of a row, so row-major
spread one round's reads for a block's 128 rows over 22.5 KB of lines and
word-major keeps them in ~4 KB): 1.014× at A305740 n = 18 and 1.010× at
A153431 n = 18 (the narrow record has no round-window rows), every
fingerprint reproduced. Kept. **The extraction visits only the nonzero
words** (a mask of which live words are nonzero is built as they are
written, and the push loop walks its set bits — ~0.7 words a row — where
it re-read all NW from `sal`): 1.008× at A305740 n = 18 and 1.007× at
A153431 n = 17, ranges disjoint, every fingerprint reproduced. Kept.
**The window depth re-swept on the final kernel, and made per-filter**
(`BIT_SURV_BY_FILTER`): the optimum split — `BIT_SURV` .0035 / .004 /
.0045 / .005 read 1 / 1.016 / 1.019 / 0.995 at A305740 n = 18 and .0045
1.015 at n = 19, but .0045 reads 0.971 at A153431 n = 17, 0.965 at
A153431 n = 18 (wide too, so it is not the record) and 0.991 at A305740
n = 17. The depth moves in whole primes and a different prime leaves the
window at each filter; it never changes the survivor set. .0045 at
A305740 n = 18 and 19, .0035 everywhere else (checked at the hour-scale
filters too: .0045 / .0028 read 1.002 / 0.957 at A153431 n = 16 and
0.991 / 0.985 at A305740 n = 16); the planner's
`window_depth` reads the same table (G18 caught the first version, where
it did not). `K2_SURV4` re-checked at n = 18 on the new depth: .0002 /
**.0003** / .00045 read 0.994 / 1 / 0.979.
**The narrow in-block rounds share the u64 reduction**
(`_chunked_round_body`): each test reduced the 64-bit offset with its own
u64 Barrett step; now the offset is reduced once per chunk of up to three
primes to R = offp mod P (P their product, < 2^31) and each prime takes R
mod q by a 32-bit one-subtraction step, exact for every R < 2^32 by the
same argument as the u64 step. 1.021× at A153431 n = 17 and 1.025× at
A305740 n = 17 (the wide record's rounds are the round-window form and
do not reduce), every fingerprint reproduced. Kept. **The same in the
tail's one-lane rounds** (a pair table: the u64 offset reduced once per two
primes whose product is under 2^31, each residue by the 32-bit step; every
fingerprint reproduced): 0.993 at A305740 n = 18 and 0.983 at A153431 n =
17. The tail is latency on its loads, not arithmetic, and the pair table
is one more load per two primes. Declined and removed.

Also priced after Measurement 13 and declined: the extraction buffer kept
in registers when XE = 1 (0.20×: 255 registers, the dynamic-indexing trap
v4 recorded); one merged tail round from the first 32-lane round on (0.994,
and 0.967–0.990 merging earlier: the rounds' growing lanes per item earn
their launches); the x0 and res1x table loads removed outright (0.991 /
0.995: they cost nothing); spb 16 with a tighter queue margin to reach 4
blocks (the queues barely shrink and overflow costs 0.83 / 0.37).

And after it, on the new kernel: the round-window rounds re-measured on
both records — on the wide record they are worth more than before (off:
0.885 at A305740 n = 18, 0.913 at A153431 n = 18), on the narrow record
they are still not worth taking (1.003 at A153431 n = 17, 0.981 at A305740
n = 17; every narrow frozen shape reproduced its fingerprint with them on,
so the path is sound, only not faster); `R2_DROP` .35 / **.5** / .65 / .8
read 0.977 / 1 / 0.987 / 0.926; `TAIL_TPB` 64 / 128 / **256** / 512 within
0.8%. **The block's pattern copy** (10 KB from global into shared, once per
block, 1.15M blocks a launch at A305740 n = 18) was priced by doing it
twice — a valid ablation, the survivors unchanged — at ~1.2 ms of a 109 ms
launch: persistent blocks that copy once would buy about 1%, for a
restructure of the whole kernel around a block loop. Declined. The in-block
rounds are 20.4 ms of the sieve kernel's 93 (extraction 6.8, window-only
65.7): by instruction count they are ~5 ms of work, so they are latency on
the dependent x0r-row and pattern-word loads with 16 warps a SM to hide it;
the priced levers (depth, drop point, the round-window form) are all at
their optimum. **The wide record's period term computed instead of looked
up** (jj·(W′ mod q) + base mod q, reduced with the test's own magic, in
place of a divergent load from the 20 MB per-launch `jb` table — the wide
tail is 17% of the sieve kernel's time against the narrow 14%): fingerprint
reproduced, 0.993 at A305740 n = 18 and 0.990 at A153431 n = 18. The table
reads are L1 hits; the arithmetic costs more. Declined. **Threads per
block** on the final kernel (A305740 n = 18): 256 × spb 8 reads 1.003 (two
blocks of 8 warps: the same 16 warps a SM), 256 × spb 4 0.936, 64 × spb 16
0.808; 128 × 8 stays (a tie goes to the shape the gates and every other
filter were measured on). **The wide launch budget on the final kernel**:
2^38 / 2^39 / 2^40 read 1 / 1.005 / 0.537 — 2^39 halves the per-launch
fixed cost of the late tail rounds for 0.5% and twice the queue memory, and
2^40 falls off a cliff (the first tail queue reaches its cap and the
overflow runs the in-kernel fallback). Unchanged.

**The launcher on the final kernel** (Measurement 9's method, exact counts):
the host path (`_submit` → pool → `_drain` → back-pressure, one worker)
runs at 0.996 of the device alone at A153431 n = 17 and 0.990 at A305740
n = 18, with no host wait. The loop is still the device.

### Measurement 15 — THE SIBLING'S FLOOR (the campaign, not the kernel)

If x had an A305740 run of n or more, y = 10x would meet A153431's
condition at index n − 1 (10^k·y + 1 = 10^(k+1)·x + 1 for k = 0..n − 1), so
A153431(n − 1) ≤ 10x: **A305740(n) ≥ ⌈A153431(n − 1)/10⌉**, a theorem
(decl_reference G2d checks it on every published index). `launch.x_floor`
now takes it: once A153431(n − 1) is settled — published, in `FOUND`, or a
verified first occurrence in `evidence/` — A305740's sweep for a(n) starts
there, the evidence records the bound under `least_claim.sibling_floor`
(what it rests on and why), and the odds model conditions on it (the ladder,
`P(a(n))`, the start-of-run predictions). The relation bounds A153431 from
above, so A153431 gets nothing back. A new drill (`_sibling_floor_drill`)
checks the theorem on the published terms, the floor from the published
terms and from a scratch evidence record, and that neither family's other
sequence moves it.

**What it is worth is an ORDER:** the saving is exactly (sibling floor −
own floor) / rate, and it exists only if A153431 is hunted first. At the
model's chained medians and the measured rates: A305740 n = 17 0.26 h, **n =
18 ≈ 7.4 h** (floor 7.5e21 → 1.36e23 at 4.85e18 k/s, ~15% of the leg), n =
19 ≈ 208 h. Today it moves only A305740 a(14)'s floor (to 4.3e15, from
A153431's published a(13)): seconds. This is the part of the declined joint
sweep that needs no shared coverage claim: a floor from a settled term, not
a cursor from a running campaign.

**The other half, priced and left for later: A153431's class 0 mod 10.** The
same relation read the other way: a y ≡ 0 (mod 10) that meets A153431's
condition at index n is 10x with an A305740 run of n + 1, so once
A305740(n + 1) is settled, A153431's sweep at filter n can drop the class
y ≡ 0 mod 5 (a quarter of its candidates — 2 is forced, 5 already kills 4)
below Y0 = 10·A305740(n + 1), and need never pass Y0 (Y0 itself is a hit).
At the medians that is ~25% of A153431's n = 17 leg (~9 h) when A305740 is
hunted first, which would make the order indifferent (7 h one way, 9 h the
other). It is a CONDITIONAL kill set for 5 in all three engines and their
parity gates, a capped sweep, and a discovery that can rest on the sibling;
priced at an afternoon with its gates, not taken in the last hours of this
round.

**The selftest takes 286 s**, inside the five-minute cap by 14 seconds.
A `timeout 295` run that also paid a cold start was killed before it
finished. Its next rise has to come out of the battery, not out of the cap.

### Measurement 16 — THE SIEVE KERNEL IN NSIGHT COMPUTE, and three changes it pointed at: 1.024–1.067×, kept (2026-09-25)

One launch of `sieve` and one of `tailround1` at A305740 n = 18 (the frozen
SCORE window, the engine API with `-lineinfo`, one warm sweep unprofiled),
`--set full`, attributed by source line. Device time over a 16-launch sweep:
`sieve` **84.8%**, `tailround1` 11.9%, the other tail rounds 3.4%.

**`sieve` is at the hardware's limit on the LSU pipe**: 86% of peak LSU
issue, ALU 72%, issue slots 59%, L2 19%, DRAM 2%, 4 blocks per SM
(register-bound at 106). Shared loads are 8.6e9 warp instructions a launch
at 1.95 wavefronts each with 3.1M bank conflicts in total -- the window's
four LDS.64 per prime per row, conflict-free; what binds is how many there
are. By stall samples: window 38% (and 88% of the shared wavefronts),
in-block rounds 22.5% (87% of the L2 traffic, long scoreboard on the x0r
rows), extraction 15%, per-block setup 11% (barrier waits, the pattern
copy, the offsets), `warp_reserve` 8% (its five dependent shuffles: short
scoreboard 78%). `tailround1` issues 0.66 a cycle, fixed-latency waits
first -- the tail's levers were already flat.

Stall samples are not savings: the three changes below were estimated at
3–8% each from their shares and measured at a fraction of that, because
the pipe that binds is the LSU and none of them touches the window.
Measured in scratch copies of this engine, interleaved with the shipped one
in the same process, every frozen fingerprint reproduced on every run; at
the two promotion filters (no frozen shape) the variant's sorted survivor
list was required to EQUAL the shipped engine's on every run.

| change | A305740 n = 18 |
|---|---|
| `warp_reserve` bit-sliced: four independent ballots and one `__reduce_add_sync`, the shuffle chain kept as the fallback when a lane holds 16 or more | **1.0025** |
| the queue entry one packed u32 again (it was u16 + u8 to free a 6th block; the kernel is register-bound at 4, so the byte bought nothing and cost a second store and load) -- still 4 blocks, 21.9 → 23.8 KB | **1.0055** |
| a block walks `TBL` t-blocks after one setup (the setup is the s-block's alone) -- TBL 2 / 4 / 8 / 16 / 32 / 64 | 1.010 / 1.017 / **1.027** / 1.027 / 1.028 / 1.029 |

All three at TBL = 8 (4 rounds each, medians):

| filter | TBL = 8 | TBL = 32 |
|---|---|---|
| **A305740 n = 18 (live)** | **1.0395** | 1.0401 |
| A153431 n = 17 (live) | **1.0243** | 1.0252 |
| A305740 n = 13 (opening) | **1.0156** | 1.0066 |
| A153431 n = 14 (opening) | **1.0120** | 0.9934 |
| A305740 n = 19 (promotion) | **1.0669** | — |
| A153431 n = 18 (promotion) | **1.0464** | — |
| SCORE2L / SCORE1L | 1.055 / 1.104 | — |
| SCORE9 (x-space anchor, no campaign) | 0.960 | — |

**Kept, TBL = 8**: 32 is no faster at the long legs and loses at both
openings, where too few blocks are left to fill the device. SCORE9's loss
is the same one Measurement 14 recorded -- one more barrier per t-block
where a block has almost no work. The shipped version sizes the queues at
four bytes an entry (`qbytes`), where the scratch copy measured above still
planned at three; the shipped engine read 1.0022 against it, stream
identical. **Re-swept on the new kernel (rule 3a), interleaved:** the
window depth holds -- `BIT_SURV_BY_FILTER` at A305740 n = 18 .0035 /
**.0045** / .0055 read 0.983 / 1 / 0.976, and `BIT_SURV` at A153431 n = 17
.0028 / **.0035** / .0045 read 0.961 / 1 / 0.994; the block shape holds --
spb 4 / **8** / 16 read 0.944 / 1 / 0.831 (16 drops to 2 blocks). The
battery is 49/49 green and now takes **244 s** (it was 286), the frozen
fingerprints unchanged. Not done: the in-block rounds' x0r rows staged or
prefetched, the tail rounds, the window itself -- the profile and the
measurements above put the first at latency already tuned (Measurement 14),
the second flat, and the third at the LSU limit.

### Measurement 17 — THE FIFTH BLOCK, AND THE TAIL'S BRANCHES: 1.06–1.14× at every campaign filter, kept (2026-09-28)

The owner stopped the A305740 n = 18 campaign (cursor 1.415e24, past a(18)'s
median) for this round. A fresh Nsight profile of one `sieve` launch at that
filter (the campaign's own engine, `-lineinfo`, SASS-level counters) and a
duration pass over every kernel of a launch:

* **Device time: `sieve` 85%, the 31 tail kernels 15%.**
* **`sieve`: 209.4M cycles, 63.7e9 warp-instructions; LSU issue 81.6%, L1
  data-pipe wavefronts 78.5%, ALU 76%, issue slots 60%.** By stall samples:
  the window 51%, the extraction 17.5%, the four in-block rounds 21%, their
  pushes and fallbacks 5.5%, the per-block setup 3%.
* **The window is at its roofline three ways at once.** Per prime-row: four
  `LDS.64` (8 cycles of LSU issue at 0.5 a cycle an SM), 8 shared wavefronts
  (each `LDS.64` costs exactly its ideal 2.00 -- no conflicts, no address
  trick left), and 14.5 ALU ops (7 funnel shifts, 3.5 three-input ORs, 4 of
  index; ~7.25 cycles at 2 a cycle). Cutting one pipe alone buys little,
  which is what Measurements 6 and 13 found from the other side. The `ne`
  broadcasts cost 2.25 wavefronts per `LDS.128`, 7% of the window's.
* **The rest ran at ~40% issue efficiency against the window's ~75%**: the
  extraction a divergent loop (3.05 nonzero-word iterations and 4.36 push
  iterations per warp-row for ~1 survivor a lane) and 172 instructions a
  warp-row; the rounds long-scoreboard on the x0r rows; and 3% of all stall
  samples were instruction-fetch misses -- the kernel was 15,530 SASS
  instructions, because each round's push is unrolled MAXIT times and every
  copy inlined a whole unrolled `tail_survives` (~460 instructions) for an
  overflow that never happens in production.
* **The tail's first round costs ~42 instructions per warp-test**, six of
  them branches and reconvergence: the residue-list branch for primes above
  MASK_BITS and the guard on the round's end around every unrolled test.

What was kept, each measured in a scratch copy of the engine interleaved
with the shipped one in one process (harness as above, 3-second arms,
PAIRED ratios per round -- other GPU clients moved absolute rates by up to
10% between runs today, so ratios of medians are quoted only beside them),
the frozen fingerprint reproduced on every run and, at filters without one,
the variant's sorted survivor list equal to the shipped engine's:

| change | A305740 n = 18 |
|---|---|
| the extraction at XE = 1 (every campaign shape): the nonzero-word mask 32 bits, the row's queue tag and D fixed for it, no `/NW`, no `d2` reload per word | **1.022** [1.017, 1.025] |
| the funnel shift takes the position unmasked (`__funnelshift_r` shifts by its low five bits; the `& 31` was an ALU op per prime-row) | 1.007 [1.006, 1.014] |
| the x0 table in PAIRS (PK2): groups 2p and 2p + 1 in one u32, `ne` as u16, one add for two positions (each below 2Q + 1 < 2^16, nothing carries) -- half the x0 loads and `ne` loads, **106 → 72 registers** | 1.004 [1.004, 1.008] |
| the row's words kept in REGISTERS for its extraction (XE = 1), picked by a 3-level select tree: no `sal` buffer, 7 stores and ~3 loads a row fewer, 3.5 KB of shared a block freed -- **5 blocks per SM** (19,408 bytes against the 19,456 line) | 1.027 over the three above (5 rounds: 1.038 → 1.066 against the shipped engine) |
| the overflow fallbacks out of the hot loops: the round pushes mark an overflowing item and call ONE out-of-line `tail_survives_cold` after their unrolled loop, the final push calls it, the extraction (inside the row loop, where a call site would force the packed x0 to survive it) takes a compact non-unrolled inline copy | 1.029 [1.017, 1.035] (as a call everywhere; see below) |
| the tail rounds whose primes -- including the ones an unguarded test reaches past the round -- are all ≤ MASK_BITS take a branch-free kernel (`tailsmall`): the mask bit is exact there, and the unrolled tests run past the round's end unguarded (a prime past it kills only what the next round would) | 1.030 [1.000, 1.062] |

The fallback went through three shapes. As a call from every site it was
1.029× at n = 18, but the call ABI took registers to 96–104 and six of the
twelve campaign configurations back to 4 blocks. Compact inline copies
everywhere (no call, 72 registers) read 0.977 of the call version. With
`__launch_bounds__(128, 5)` the call version held 5 blocks everywhere and
read 1.018–1.034 over the compact one, but spilled 8–24 bytes at five filters
-- on the HOT path, 5 `LDL`/`STL` a row, from the call site in the row loop.
The shipped split (call after the rounds' loops and in the final push,
compact inline in the extraction) holds 5 blocks at every campaign
configuration with 74–96 registers and no spills, and sits within the noise
of the launch-bounded version (paired 1.005–1.013 either way across runs).

**Production against the engine it replaced, interleaved, survivor streams
identical on every run** (paired medians, 3–8 rounds):

| filter | ratio |
|---|---|
| A305740 n = 13 (opening) | 1.139 [1.102, 1.161] |
| **A305740 n = 18 (live)** | **1.098** [1.076, 1.136] |
| A305740 n = 19 (promotion) | 1.063 [1.038, 1.091] |
| A153431 n = 14 (opening) | 1.088 [1.044, 1.143] |
| **A153431 n = 17 (long leg)** | **1.076** [1.036, 1.162] |
| A153431 n = 18 (promotion) | 1.110 [1.052, 1.120] |

Under Nsight the sieve kernel went 209.4M → 181.9M cycles (−13%) and 63.7e9
→ 56.4e9 instructions; the end-to-end gain is smaller because the tail is
15% of the launch and the card is at its 450 W cap (a denser kernel draws more
per cycle and clocks lower).

**A gate caught a bug in the first version** (OPTIMIZATION.md Rule 6). The
small-prime tail kernel was first taken for a round whose OWN primes were all
≤ MASK_BITS. But its unguarded tests reach up to LPI·UNROLL − 1 primes past
the round, and the sieve primes are ordered by killing power, not size, so
those can be above MASK_BITS -- where a mask bit is only a filter, and taking
it as a kill drops a survivor. G17's coarser wheel at A153431 n = 17 returned
81 survivors against the stream's 84. The rule now covers the primes past the
end; at every campaign configuration it selects exactly the rounds the first
rule did (10 of 31 at A305740 n = 18), so the measurements above stand. The
scratch A/Bs' survivor-list comparisons had passed: twelve launches at a
campaign filter never reached a round boundary near 4096.

**A side effect caught before it shipped**: `OCC_MIN_BLOCKS4` (now 5, G18's
floor) was also the block-shape chooser's threshold, and at 5 the narrow
windows (NW ≤ 4, where only the drills run) fell through to one-row blocks,
which would have left the buffered extraction (XE > 1) unexercised. The
chooser has its own `SHAPE_MIN_BLOCKS = 4`.

**Measured and declined** (same harness, A305740 n = 18 unless named):

| attempt | ratio | why |
|---|---|---|
| in-block rounds, two items per step with clamped loads (ILP) | 0.964 | warps with no valid item in a pair's second slot run it anyway; the rounds' stalls are 27% long scoreboard, the rest issue |
| the round's queue entries held in registers for the push | 0.959 | 136 registers, 3 blocks |
| the valid-period mask hoisted per kernel | 0.999 | the uniform datapath already absorbs it |
| the round push walking the set bits of `alive_z` | 0.9995 | the push was never the cost |
| `sal` aliased onto the round-1 queue's buffer (2.5 KB freed) | 0.985; 0.943 with PK2 | not found; superseded by keeping the words in registers |
| guard-free generic tail rounds (primes above MASK_BITS) | 1.004 | noise |
| MASK_BITS 8192 / 16384, so more rounds take the small kernel | 1.016 [0.90, 1.03] / 0.994 | not resolvable; 4096 stays |
| the small kernel's unroll 2 / 8 | 0.992 / 0.988 | 4 stays |
| 6 blocks per SM: spb 4 (74 registers, 15.0 KB) | 0.964 | the 6th block does not pay for halving the rows each block's setup, x0 loads and rounds are spread over |

**Re-swept on the new kernel (rule 3a), interleaved -- nothing moved:**
`BIT_SURV_BY_FILTER` at n = 18 .0035 / **.0045** / .0055 / .007 read 0.987 /
1 / 0.977 (4 blocks: the larger queues) / 0.970; `K2_SURV4` .0002 /
**.0003** / .00045 read 0.986 / 1 / 0.979; `R2_DROP` .40 / **.50** / .62
read 0.977 / 1 / 0.971; `TBL` 4 / **8** / 16 read 0.995 / 1 / 0.998.

**SCORE9's single reading after the change (7.29 against 8.16 that
morning) is noise**: interleaved on its own shape the new engine is 1.106×
the old (1.608 s against 1.779 s for its 4e8 periods, fingerprint exact).

What the gates carry: G21 now also runs, against the CPU engine at
q2 = 8192, the packed-pair window over 5 and 6 groups (the last group of an
odd count alone), the extraction from registers (XE = 1) and from shared
memory (XE > 1), and both tail kernels, and requires all six to have run;
G14 reads the window chain through the packed x0 table; G18's floor is 5
blocks; the forced-overflow drills (G14, G16, G20) run every relocated
fallback. The battery is 49/49 green on the final tree, run in three parts
(19 / 8 / 22 in 113 / 199 / 95 s, every kernel compiling cold for the new
source), and all seven frozen fingerprints reproduce.

### Priced and declined

1. **The joint sweep of both families.** A305740's filter n + 1 is
   A153431's condition at n on y = 10x (decl_reference G2d), so one sweep of
   y at C_n classifies both — A153431 needs all four surviving classes mod 5,
   A305740 only the class 0. At the long legs (both C_17) the A153431 sweep
   to its median, 1.36e24, would cover A305740's y-line from 7.5e22 to
   1.36e24 for nothing: ≈9% of the two legs' COMBINED device time at the
   medians, and only if both run. Declined: the campaigns run one family at
   a time from separate checkpoints, the overlap depends on where each find
   lands, and a shared coverage claim across two sequences is a new
   checkpoint design with its own failure modes.
2. **A 128-bit within-period offset (wheels past W' = 2^63).** The window
   phase does not care how long the period is; only the per-candidate route
   reduces the offset. But a longer wheel is blocked by the SEARCH, not the
   word: at A305740 n = 18 the next wheel prime would make one 224-period
   segment ~8e24, ten medians. Nothing to buy.
3. **Word-aligned pattern copies at 8-bit shifts, 32-way shifted copies.**
   Shared memory ×4 / ×32; Measurement 6 prices ×4 at 0.83–0.91.
4. **A 288-period window (NW = 9).** The window's loads per output word fall
   from 4/7 to 5/9 (−2.7%) and every per-row cost is spread over 9 words
   instead of 7: ~3–5% on paper. But the queues grow with the tile and the
   patterns by 64 bits a prime, ~2.7 KB of shared a block, and A305740
   n = 18 sits 48 bytes under the 5-block line (Measurement 17): the 5th
   block is worth more. It would also need a ninth period bit in the tail's
   u8 `jj`. Declined (2026-09-28).
5. **A153431's class 0 mod 10, NOW.** Measurement 15's "other half" was
   priced as waiting on A305740(n + 1) being settled. It does not have to
   wait for a term, only for COVERAGE: a y = 10x below Y0 meeting A153431's
   condition at n = 17 is an x below Y0/10 with an A305740 run of 18, and the
   A305740 campaign has swept filter 18 from a(17) = 2.19e22 (no x below it
   has a run of 17) to 1.415e24 (checkpoint, 2026-09-28) without one. So
   A153431's filter-17 sweep may drop the class y ≡ 0 (mod 5) -- a quarter
   of its candidates -- everywhere below 1.415e25, ten times its median:
   **1.33× on the whole A153431 a(17) leg**, the largest lever this project
   has left. What it costs is not code but a CLAIM: a find would rest on
   another campaign's cursor (its evidence citing the A305740 checkpoint and
   engine), which is the shared-coverage design the joint sweep (1) was
   declined for. The owner's call; not built.

   **Update, 2026-09-29: the objection has lapsed.** A305740 a(18) =
   1,705,184,924,533,540,483,774,741 is found and verified (RESULTS.md), so
   the lever now rests on a settled TERM, not a cursor: Y0 = 10·a(18) =
   1.7052e25 meets A153431's condition at n = 17 (so A153431(17) ≤ Y0, and
   the sweep need never pass it), and every y ≡ 0 (mod 10) below Y0 is
   excluded by a(18)'s own least claim — a verified first occurrence in
   `evidence/`, the same kind of fact Measurement 15's sibling floor
   already takes. What is left is the code: a conditional kill set for 5 in
   all three engines and their parity gates, the capped sweep, and a
   `least_claim` that names the term it rests on. Still 1.33× on the whole
   A153431 a(17) leg — ~8 hours at the model's median (1.5e24, 1.4 days of
   device at ~1.16e19 m/s), ~1.7 days at P90 — and more if A153431 lands
   as late as its last three terms did (4.3–5.9× their medians). Priced at
   an afternoon with its gates; not built, because the project paused on
   2026-09-29 before the next campaign.

### Termination table (OPTIMIZATION.md Part 3), as it stands

| phase | share | verdict |
|---|---|---|
| the campaign's plan | — | **optimization**: measured per filter on exact counts (Measurement 12), 1.03–1.13× over the first table at seven filters; the wheel is bounded by the segment at n = 18 and by the u32 level moduli at n = 19 (Measurement 13) |
| the window sieve | ~53% of the sieve kernel | **roofline, three ways** (Measurement 17): per prime-row four `LDS.64` at exactly their ideal 2 wavefronts (8 cycles of LSU issue = 8 of shared bandwidth) against ~7 cycles of ALU; the shift mask (1.007×) and the `ne` loads halved (PK2) were the slack. Only fewer BYTES per output word can move it: 288-period windows (−2.7% loads) cost the 5th block, 4-tuples, CRT pairs and shifted copies cost shared memory (Measurements 6, 13, 17) |
| in-block rounds | ~30% | latency on the x0r rows (long scoreboard 27%) and issue; two items per step priced at 0.964, the entries in registers at 0.959, x0r staging has no shared memory to live in (48 bytes of margin at n = 18); depth and split re-swept flat (Measurement 17) |
| extraction | ~14% | **optimization**: one row at a time from registers (no shared buffer), the mask 32 bits, the tag hoisted -- 1.022× and, with PK2, the 5th block (Measurement 17); the reservation bit-sliced (1.0025) and the queue entry one packed u32 (1.0055) (Measurement 16) |
| per-block setup | ~3% | **optimization**: on every thread, 1.01–1.16× (Measurement 14); one u64 step on the wide record, 1.008×; paid once per TBL = 8 t-blocks, 1.027× (Measurement 16); TBL re-swept flat (Measurement 17) |
| occupancy | — | **5 blocks per SM at every campaign configuration** (Measurement 17), 96 registers and 19,456 bytes the lines; a 6th (spb 4) reads 0.964 |
| tail rounds | ~15% of the device | **optimization**: rounds whose primes are all ≤ MASK_BITS (83% of the tests at n = 18) on a branch-free, guard-free kernel, 1.030× (Measurement 17); mask width, unroll, drop point, lanes per item, warp-aggregated queue reservation flat; the generic rounds guard-free 1.004 |
| host / loop | 0.6–0.8% of device | Measurement 9 |

Result so far, steady, the campaign's own configuration against the baseline
(Measurement 2), on EXACT launch counts (Measurements 12 and 14): **A305740
n = 18 3.84e18 → 5.11e18 k/s (≈1.33×); A153431 n = 17 8.30e18 → 1.05e19 m/s
(≈1.27×).** (The 1.18× / 1.19× stated here before Measurement 12, and an
earlier 1.27×, came from the overcounted harness.) **Measurement 16 adds
1.040× at A305740 n = 18 and 1.024× at A153431 n = 17 (interleaved, same
process): SCORE 5.09e18 → 5.31e18 k/s, SCORE153 1.044e19 → 1.073e19 m/s
on the day.** **Measurement 17 adds 1.098× at A305740 n = 18 and 1.076× at
A153431 n = 17 (paired, interleaved against the engine it replaced; 1.06–1.14×
at every campaign filter): SCORE 5.31e18 → 5.89e18 k/s, SCORE153 1.073e19 →
1.161e19 m/s as single readings on the day.**
