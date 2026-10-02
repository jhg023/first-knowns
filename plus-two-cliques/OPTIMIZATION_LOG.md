# OPTIMIZATION_LOG — plus-two-cliques

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt → measurement → kept/rejected, failures included. This
project starts from product-cliques' engine v2 and planner p3, whose own log
holds the rounds that produced them (the pairs window, the live words in
registers, the packed round reductions, the re-fit width curve). What is
here is what was measured and decided in making that engine hunt the +2
cliques. Harnesses were scratch scripts, not committed; each measurement
below gives enough of its method to rewrite one in ten minutes.

---

## Decision 1 (2026-10-01) — product-cliques, with the constant changed

**Why that engine.** The two problems have the same shape: a greedy clique
whose conditions at index n are products of the candidate with the
sequence's own earlier terms, so the filter is state, a find restarts the
sweep, and a wrong term would poison every later one. product-cliques
carries every piece of machinery that shape needs, and its engine takes its
problem as *killed residues per prime* and nothing else.

**What changed, and where.** The killed residue of a term a(i) modulo q is
−2·a(i)⁻¹ instead of −a(i)⁻¹, which is `killed_residues` in the CPU engine
and the oracle's walk and nothing in the kernel. Two consequences reached
further than that:

* **The class.** At a(n) ≡ 0 every value is 2, not 1, so residue 0 survives
  every *odd* prime, and 2 kills the even a(n). The forced class is
  3 (mod 6), the first nonzero class this engine has swept. The host map
  from the device's index to a(n) was always general (`unit_residue`), and G9, G13, G15 and G17
  now pin a nonzero class end to end.
* **The offset.** A083519 is offset 0. The oracle's `KNOWN`, `terms`,
  `frontier`, `register`, `nforms` and the run length all count from each
  family's %O offset, the run is in OEIS index units (a full run at index n
  is n in both families), and the pool's form list carries the offset with
  the multipliers. G1c and the offset drill pin it.

There is no extra form here (A219761's a(n)² + 1 has no counterpart), so the
quadratic machinery of product-cliques (Tonelli–Shanks, two kills per prime)
was removed rather than left untested.

## Measurement 1 (2026-10-01) — the ceiling, and why it is 10³⁰ and not 10⁴⁰

Rule 5h's default rests on a structure this project does not have. Every
value here is N = a(i)·a(n) + 2, so N − 1 = a(i)·a(n) + 1 and N + 1 =
a(i)·a(n) + 3 are numbers like any other: nothing is factored for free, and
product-cliques' route (one factorization of the term proves a whole run)
does not exist. Each value is proved on its own by a bounded certificate
search: `huntlib.certificate.prove`, which factors N − 1 and N + 1 with trial
division, rho and 24 ECM curves (8 splits) and closes BLS75 Theorem 1, 5 or
15, with a subproof for a large prime cofactor. The ceiling is therefore
where that search stops landing, and rule 5h asks for the measurement.

**Method.** Random primes of this project's shape, N = a(i)·a(n) + 2 with a(n) ≡ 3
(mod 6) and the two factors of similar size, at each digit count. Each was
put through `prove(N)`, then, where that returned nothing, through one retry
with 200 ECM curves and 16 splits, and every proof was re-verified.

| digits of N | default search proves | worst default | retry proves the misses | retry time |
|---|---|---|---|---|
| 45 | 20 of 20 | 1.1 s | — | — |
| 50 | 20 of 20 | 1.5 s | — | — |
| 51 | 55 of 60 | 2.0 s | 5 of 5 | 2.2–9.6 s |
| 53 | 88 of 90 | 2.2 s | 2 of 2 | 1.6 s |
| 55 | 45 of 46 | 1.9 s | 1 of 1 | 2.4 s |
| 57 | 29 of 30 | 3.0 s | 1 of 1 | 2.6 s |
| 58 | 44 of 45 | — | 1 of 1 | 10.7 s |
| 60 | 27 of 30 | 2.4 s | 3 of 3 | 2.2–10.9 s |
| 62 | 22 of 25 | — | 1 of 3 | 4.8–18.8 s |
| 65 | 16 of 20 | 2.4 s | 2 of 4 | 1.4–16.9 s |

So the two-stage search proves **every one of 341 values from 45 to 60
digits**, the worst in about 22 s, and loses 2 of 25 at 62 digits and 2 of 20
at 65. A find's largest value is about a(n−1)·a(n), roughly a(n)²/30 at the
model's term ratio, so at a(n) = 10³⁰ it is about 59 digits, the top of the
measured zone. **`plus2_search.K_CEIL_PLUS2 = 10³⁰`**, on both families.
huntlib's 10⁴⁰ would put a find's top values near 80 digits, where the
search does not land. The hunt's reach this season is about 10²³, values of
about 45 digits.

**Priced and declined: a full factorization as the fallback.** huntlib's
`factor_full` (the bounded chain, then sympy's factorint) on a worst-case
N − 1, a balanced semiprime, takes 7.0 / 17.5 s at 41 digits, 13.3 / 4.0 s at
44, 4.4 / 45.2 s at 47 and 89.7 / 11.6 s at 50 (two seeds each). It is
unbounded, and slower where the ECM retry works, so the retry is the
fallback (`launch.certify_value`), and a value both searches miss goes to
the evidence file's `unproved` list.

The certificate drill proves both frontier terms' values (all under the
deterministic bound), the top value past each open index's crossing, a
59-digit value at the ceiling in each family with the recursion exercised,
and a 53-digit value the first search misses, by the retry (found by a
scratch scan; both searches are deterministic, so it stays the case that
needs the retry, and the drill fails rather than passing vacuously if
huntlib ever proves it first).

## Measurement 2 (2026-10-01) — every opening, and the filters after it, priced (5c, 5g)

A scratch harness registered the model's stand-in terms in its own process,
built the PLANNED engine at each filter exactly as the campaign builds it
(`launch.plan_for`, `seg_cap = pb`), warmed it on the segment after the
modelled median, and timed the launches of the segment holding the median
(up to 4 s). It counted the candidates of each launch EXACTLY from the
launch decomposition (the last first-level chunk is partial, and counting
every launch as full overstates the rate), counted survivors, timed
`launch.sprp_run` on 1,500 of them, and divided the model's `expected_sweep`
by the measured rate. The table is in BENCHMARKS.md. The headline, on the
planner shipped here (p2):

* **A083518**: a(14)–a(16)* under 2 s each, a(17)* 36 s, a(18)* 15 min,
  a(19)* **6.3 h**, a(20)* 7.6 days, a(21)* 9 months. Device 0.9–5.5e16
  a(n)-line/s past the openings; host 0.26–2.2 core-s/s.
* **A083519**: a(11)–a(15)* under 5 s each, a(16)* 80 s, a(17)* 31 min,
  a(18)* **12.5 h**, a(19)* 15 days. Host 0.17–1.5 core-s/s.

The survey that chose these entries priced the hunt at 2.5e12 candidates a
second *after the full wheel to 59*, and put A083518's a(20) near 4 days.
The planner here reaches 3.7–4.1e12 candidates a second, but on the wheel to
47 at the hour filters (wheel density about 1.55e-4 against the survey's
6e-5), so the line rates came out about half the survey's. The full wheel to
53 is what round 1 below recovers.

## Gates re-cut for this problem (2026-10-01)

The gates were inherited with product-cliques' indices, heights and units.
A034881 opened at 16 and A219761 at 12; A083518 opens at 14 and A083519 at
11, offset 0. Every case was re-pointed at indices that exist. These needed
more than that:

* **G16** (the third level's overflow and chunking) overflowed the 2^20
  survivor buffer at its inherited q2 = 128: at n = 13 (twelve conditions)
  one launch kept 1.8 million survivors. It now sieves to 512 (95,215
  survivors).
* **The resume drill** classified 12.4 million survivors across its seams
  (26 s) at q2 = 128, so its three-level and seam engines now sieve to 1024
  (297,004 survivors, 9 s). The classification drill's window held 54,433
  survivors (70 s) and now holds 5,471 (15 periods instead of 150).
* **The protocol drill's** "an earlier term satisfies every condition of a
  later index" is false here, because there is no self condition. An
  earlier term is joined to every other term, so it fails at most its own
  square plus two, and the drill now asserts exactly that run.
* **The certificate drill** was rewritten. Its inherited route (BLS75
  Theorem 1 with R = 1 on one factorization of the term) does not exist here
  (Measurement 1). It now checks any BLS75 route, re-verified and refused at
  N + 2, and exercises the retry.
* **The rediscovery run drill is bounded before the open index.** It runs
  `Campaign.run` from DRILL_N, finds a(n) and a(n+1), and stops before the
  filter of n + 2 (a drill-only `stop_n`). product-cliques' drill had no such
  bound, and its A219761 run (DRILL_N = 10) swept one segment of filter 12,
  then the open index, at a segment of 0.76 medians: a drill could have
  found the real a(12). Here that is impossible by construction. A083519's
  drill opens at a(9), whose predecessor a(8) = 419,925 sits under the
  planned depth there (2^20), so the drill campaign opens at the engine
  floor, 2^20 + 1, as `x_floor` says. No real frontier is ever under a sieve
  depth.
* **New gates**: G1c (every index rebuilt from the %S and %O lines), the
  offset drill (the writer's half: evidence header, file name, headline,
  open index, run), and G2c's mod-5 classes and last digits against the two
  %C lines.

## Battery and score (2026-10-01)

`python launch.py --selftest`: **51/51 ALL GREEN in 181 s** before round 1
and **in 188 s** after it. `python score.py`: every gate green, all five
fingerprints reproduced, **SCORE 1,098,430,812** (1.10e15 a(n)-line/s at
A083518's opening, a single launch), in 2 min 14 s.

---

## Round 1 (2026-10-01) — the inherited constants re-swept on this project's filters

Every measurement below was taken through the engine API at this project's
filters. The model's stand-in terms were registered in a scratch process,
and the planned engine was built at the filter with `seg_cap = pb`. Each arm
took the same number of launches (30 or 40) from the start of the segment
holding the modelled median, over three interleaved rounds, with medians
reported and an A/A arm last. Candidates were counted exactly, and the
survivor count and xor were compared on every run wherever two arms share a
launch decomposition; they agreed on every run. A ratio is line per second
against the planned arm. Where an arm changes the segment, the comparison
is the expected clock to a confirmed find. A starred filter is a stand-in.

### The window and round depths, the widths, the block shapes

| arm | A083518 n = 19* | A083518 n = 20* | A083519 n = 18* |
|---|---|---|---|
| planned (BIT_SURV 0.0035, K2_SURV4 1e-4, 160 periods, the shape table) | 1.000 | 1.000 | 1.000 |
| A/A | 0.997 | 0.995–1.000 | 0.998 |
| BIT_SURV 0.0025 / 0.005 | 0.974 / 0.978 | 0.957 / 0.971 | 1.003 / 1.001 |
| K2_SURV4 5e-5 / 3e-4 | 0.976 / 0.977 | 0.986 / 0.982 | 1.004 / 0.987 |
| 128 / 192 / 224 periods | 0.899 / 0.918 / 0.833 (clock 6.98 / 7.02 / 7.74 h against 6.38) | 0.914 / 0.925 / — | 0.920 / 0.953 / — |
| block shape (16, 1) / (8, 2) / xe = 1 | 0.980 / 0.893 / 0.980 | 0.974 / — / — | 1.002 / — / — |
| sieve depth one rung shallower / deeper | 1.004 / 0.988 | 1.003 / 0.997 | 1.004 / 0.994 |

and at A083518 n = 19*: R2_DROP 0.35 / 0.7 = 0.982 / 0.953, TAIL_ROUND_DROP
0.5 / 0.85 = 0.993 / 0.990, CAND_PER_LAUNCH4 2^36 / 2^38 = 0.989 / 1.004
(A/A 0.996). **Every inherited constant stands.** Nothing beats the planned
arm by more than its A/A spread. The depth ties go to the depth the planner
takes (the deeper of two ties asks less of the host), and 2^38 ties 2^37 for
twice the queues.

**A083519 n = 17* compiles to 102 registers and 4 blocks per SM** (its window
sits at LIT_MAX, and xe = 1 needs 104), the one configuration off the
5-block plateau. Bringing it back costs nothing and gains nothing: a 38-prime
window (88 registers, 5 blocks) reads 1.004, BIT_SURV 0.005 (90, 5) 1.005,
xe = 1 0.984, (8, 2) 0.913, A/A 1.003. The padding ablation's "8% a block"
does not hold at this filter, and it is a 31-minute filter, so nothing was
changed.

### The plan against its neighbours

| filter | planned | the neighbours, on the expected clock |
|---|---|---|
| A083518 n = 19* | to 47 × 160 | one prime shorter (to 43) 0.86 (7.45 h against 6.38); 53 for 43 0.84 (7.60 h); 29 moved into the first level 1.002; the full wheel to 53 wide 0.17 (38 h: its segment is 20 medians here) |
| A083518 n = 20* | (p1) to 47 × 160 | **the full wheel to 53, wide, × 160: 1.099 (186.0 h against 204.5)**; × 192 1.089, × 128 1.000, × 96 0.96, × 64 0.78; 53 for 43, narrow: 0.89; 29 moved into the first level 1.006 |
| A083518 n = 21* | (p1) to 47 × 160 | the full wheel to 53, wide, × 224: 1.15 (6,818 h against 7,863); × 160 / × 192 tie it (0.993 / 1.003) |
| A083519 n = 18* | to 47 × 160 | one prime shorter 0.78 (16.5 h against 12.85); 53 for 43 0.90; 53 for 41 0.88 |
| A083519 n = 19* | (p1) to 47 × 160 | **the full wheel to 53, wide, × 160: 1.214 (367 h against 446)**; × 192 a tie (1.006), × 128 0.89 |

### Change 1 — a second first-level budget, and the full wheel to 53 (planner p2)

**Why the planner could not take it.** The full wheel to 53 over the class
3 (mod 6) has W' = 5.4e18. The kernel needs W1 and W2 each under 2^32, so W1
must be past about 1.3e9: most of the small primes in the first level. At
A083518 n = 20* that is 9.3 million first-level residues, past
R1_MAX = 2^21, and the candidate never reached the planner's ranking.

**Why not raise R1_MAX.** product-cliques priced exactly this and declined
it, because the planner prefers the largest first level and re-splits
everything. Measured here, in planned configurations: at 2^22 A083518's
plans do not move and A083519's move from n = 13 (29 into the first level).
At 2^23 A083518's move from n = 17, and the full 53 wheel is still not a
candidate at n = 20* (8.45 million residues needed). At 2^24 every filter
from A083518's opening moves, and the full wheel to 53 is taken at the three
multi-day filters, but on the largest split that fits (16.7 million
residues). Moving 29 into the first level measured a tie (1.002 and 1.006).

**What shipped.** `R1_MAX_BIG = 2^24` is offered only to a wheel no split
under R1_MAX admits at all (`wheel_candidates`), and takes the SMALLEST
first level that splits it (`_split_levels(..., smallest=True)`). Every plan
R1_MAX could make is unchanged: the openings, every hour filter and both
frozen shapes. The new candidates are the long wheels nothing else reaches,
and the planner takes the full wheel to 53 at A083518 n = 20* and 21* and
A083519 n = 19*, on exactly the split measured above:
{5..23, 37} × {29, 31, 41} × {43, 47, 53}. **1.10× / 1.15× / 1.21× on the
expected clock at the three filters**, measured against the p1 plan. Device
memory is 2.9 / 2.3 / 1.3 GiB, against 0.2 GiB for the wheel to 47.

The wide 53 configuration was swept on its own at A083518 n = 20*. Shape
(16, 2) read 0.969 (128 registers, 4 blocks), CAND_PER_LAUNCH_WIDE 2^39
1.005, BIT_SURV 0.005 0.941, K2_SURV4 3e-4 0.925 and 5e-5 0.567, A/A 1.003,
so the planned configuration stands there too. (One run of this sweep held
eight such engines at once, about 24 GiB, and read an A/A of 0.196. Device
memory had run out, and the run was thrown away. Keep a 53-wheel A/B to
about five engines.)

### Change 2 — the first-level chunk capped at gridDim.y (a bug G9 found)

G9's new window with 11.4 million first-level residues in a one-level wheel
failed with CUDA_ERROR_INVALID_VALUE. The sieve's grid is (second level,
first-level chunk, segments × third level), and a chunk's blocks ride
gridDim.y, which CUDA caps at 65,535. The engine sized a chunk only by its
launch budget. Under R1_MAX no chunk came near the cap, and the planned
53-wheels happen to be chunked by their budget, but nothing guaranteed it.
`GpuEngine` now caps the chunk at 65,535 × tpb residues. No configuration
under R1_MAX changes. G9 runs a first level of 11.4 million residues on the
narrow record and forced onto the wide one, against the CPU engine.

### Termination table (OPTIMIZATION.md Part 3), after round 1

The kernel is product-cliques' v2 unchanged, and the kill sets have the
same size distribution (one residue per term per prime, at most (q + 1)/2
plus exceptions), so its phase split was not re-measured here. Its verdicts
are inherited and marked so: the window sieve is at the shared-load issue
roofline (product-cliques round 1 measured 0.455 loads a clock per SM, and
the window at about 0.44 after the pairs table), the in-block rounds are
latency-bound, and extraction and the tail rounds are flat in their
constants. What round 1 here re-established on this project's filters is
that every constant those verdicts rest on is still at its optimum. A
structural verdict is only valid against the structure it was made on, and
the next round here should re-measure the split rather than re-read it.

### Priced and unbuilt, best first

1. **A find truncates its segment.** The rest of the find's segment is
   swept and thrown away (product-cliques' Priced and unbuilt 2). Here the
   planner takes long segments at A083518's filters, and the over-sweep is
   **8.5% / 8.2% / 9.6% / 12% of the expected sweep at n = 17* / 18* / 19* /
   20***: `expected_sweep` at the planned segment against a segment of one.
   At A083519's it is under 2% (segments are 0.06–0.07 medians). Truncation
   would also let the planner take longer segments for rate. To ship it, the
   launcher has to narrow the remaining launches of a segment to the find's
   period the moment a find is classified, keep the bound in the cursor (a
   resumed truncated segment must know it), and carry it through the
   promotion and rediscovery drills. It changes the coverage claim, so it is
   the owner's to green-light. Worth about 0.5 h on A083518's a(19) and
   about 0.7 days on its a(20).
2. **The planner's price of the wide record.** At A083518 n = 20* the wide
   53 wheel runs 0.877 of the narrow 47 wheel's candidates a second, where
   the model (CREL_WIDE 0.91 × the 34/38 window-depth factor) says 0.814. The
   planner picks the right plan anyway at the three filters it changed, so
   no re-fit was made. A re-fit would need the wide-record curve measured
   across widths here.

---

## Round 2 (2026-10-01/02) — engine v2: everything that is not the window

Round 1 inherited its phase verdicts. This round measured them first, on
this project's own stand-in filters, and found the time somewhere the
inherited table did not put it. Method as round 1 (scratch harnesses
through the engine API, stand-ins registered in a scratch process, the
planned engine at the filter, EXACT candidates per launch, the same launches
for every arm, three or four interleaved rounds, medians, an A/A arm last,
the survivor count and xor compared on every run of every arm that claims
the same stream). New this round: **Nsight Compute 2025.4.1** (`ncu`, no
elevated rights needed on this machine) on one sieve launch, including
per-instruction warp-stall sampling over the real SASS.

### Measurement 3 — where the time is, before anything changed

**The device.** CUDA events around every kernel: the sieve kernel is 93% of
the device at A083518 n = 19* (narrow, the wheel to 47) and n = 20* (wide,
the wheel to 53), the tail rounds the other 7%, and instrumented wall =
plain wall to 1%.

**Inside the sieve kernel, by differential ablation** (OPTIMIZATION.md 3.3):
the window doubled (every group read again at r ± Q, the same bits, stream
identical), the rounds removed (`nq0` times a runtime zero), the extraction
removed too (its count times a runtime zero):

| filter | window doubled | rounds removed | + extraction removed | so: window / rounds / extraction / rest |
|---|---|---|---|---|
| A083518 n = 19* | 0.629 | 1.450 | 1.584 | 59% / 31% / 6% / 4% |
| A083518 n = 20* (wide) | 0.652 | 1.348 | 1.503 | 53% / 26% / 8% / 13% |

**What binds, by Nsight Compute** (n = 19*): L1TEX LSU input requests at
**86% of peak** (the peak is half an instruction a clock per SM), data-pipe
wavefronts 75%, ALU pipe 63%, issue 60%, five blocks per SM (register-bound
at 88), no spills. Every window `LDS.64` costs exactly its ideal 1.99
wavefronts and the `ne` broadcasts their ideal 2: **no bank conflict
anywhere**. Per warp-residue (32 lanes × 160 periods) the kernel issues 172
LSU instructions, 124 of them the window's (114 `LDS.64`, 10 `LDS.128`).

**The window is at the shared-memory floor.** For `LDS.64` the issue limit
(0.5 a clock) and the data limit (128 bytes a clock) coincide at two clocks
a load, and a 160-period window needs six words a lane (five plus the
shift): 24 bytes a lane a prime, delivered at the ideal wavefront count.
Fewer bytes would need pre-shifted tables (32 copies, ~75 KB a block) or
fewer primes (the wheel, which the segment length bounds).

**The rounds were the surprise.** Splitting the sampled SASS at its
`BAR.SYNC`s: the five in-block rounds hold 27% of the warp samples and 26.5%
of the executed instructions. A round test was ~18 instructions: its share
of the pack's 64-bit step, a 32-bit step, two compare-and-subtracts, a
64-bit table address, the load, and three to fold the bit. Stalls in the
rounds: fixed-latency `wait` 24-30%, `barrier` 11-27%, instruction fetch
9-12%.

### Change 1 — the narrow rounds lazy: 1.027-1.030x (`ROUND_LAZY`)

Neither reduction is corrected. The pack step leaves rm = offset −
⌊offset·mg/2^64⌋·M in [0, 2M) (the floor-magic bound of REDUCE_MAX's
comment, with 2M < 2^32 because M < 2^31), the 32-bit step leaves r in
[0, 2q), and the round table holds three periods, so the lookup at g2p + r
(g2p = base mod q, below q) needs no correction either; the kill bit is
OR-ed unmasked and tested once. 1.0275 (A/A 0.995), stream identical. **G21**
emulates every pack of the A083518 opening and of a shallow engine with
inline groups bit for bit, reads the engine's own tripled tables, trips on
a pack modulus past 2^31 (2,385,788,087 breaks the chain on a constructed
offset), and pins lazy == corrected on the device.

### Change 2 — one u32 per queue entry: 1.015x more (`QWORD`)

The inherited split (u16 index + u8 period) paid two shared stores per
extracted survivor and two loads per round item; it was taken in an older
kernel because its 3.1 KB was a block per SM. Here registers set the
occupancy, so the fourth byte is free: 1.0456 with Change 1 against 1.0302
without. Narrow record only: on the wide record the round rows already take
3 KB and the byte costs the sixth block (0.95).

### Change 3 — x0 and ne packed two groups to a word: 1.03x more narrow, 1.06-1.08x wide (`NEPACK`)

x0 < Q, ne < Q and Q < 2^15, so one 32-bit add of two packed halves (bw
riding as bw·0x10001) forms two window positions; the low half is masked,
the high half shifted, and each funnel shift takes its own low five bits.
x0 registers 38 → 19: **88 → 72 registers and the sixth block** at n = 19*
(1.0734 cumulative against v1), 86 → 80 and the sixth block at the wide
n = 20*; the `ne` loads halve (one 16-byte broadcast per eight groups). G14
reads the packed table back through `x0_table`.

### Change 4 — the block offsets built once per launch: 1.022x / 1.031x / 1.047x (`PRE_TABLE`)

A block's `ne` (one per window group) and, wide, its `ne2` (one per round
group) depend on its second-level residue, its third-level residue and the
launch base, and **not** on its first-level chunk: every one of a launch's
853 (n = 19*) to 1,401 (n = 20*) t-blocks recomputed the same rows, on 16
threads, two 64-bit reductions a group, 38 groups narrow and 124 wide, while
the rest of the block waited at the barrier. Priced first by injection:
doubling the prologue on a runtime-zero offset (values unchanged) cost 4.1%
at n = 19*, same occupancy. (The wide injections blew the registers to
130-144 and three blocks, so they are not measurements; the wide prologue
kept a 104-entry register row, which is itself why its registers sat at 80.)
`nebuild` now writes each (z, s) row once per launch from the same generated
formula (`_ne_code`, one derivation for both emitters), and a block copies
its rows into shared memory sixteen bytes at a time. **1.022 at n = 19*,
1.031 at n = 20* (wide registers 80 → 72), 1.047 at A083519 n = 19***,
stream identical. Taken wherever the launch's table fits `PRE_TABLE_MAX`
entries (0.3-1.4 million at every campaign configuration); the batched
x-space gate wheels keep the in-block prologue, so both paths stay
exercised. **G22** reads the device table back and compares it with the
definition row for row (narrow, wide with window-coordinate rounds, and a
launch batching 188 segments: sg > 0), at a base past 2^66, and pins the
device stream table == prologue.

### Change 5 — xe kept at 2 unless 1 buys a block (`XE1_REGS`)

The inherited rule kept xe = 1 whenever it needed fewer registers. Since
Change 4 the wide prologue no longer sets the register peak, and xe = 1 at
72 registers against xe = 2 at 80, the same blocks, read **0.983 at A083518
n = 20*, 0.986 at A083519 n = 19*, 0.968 at A083519 n = 17*** -- the
registers bought nothing and the batch cost 1.4-3.2%. (They tie at A083519
n = 16* and xe = 1 wins 1.8% at A083518 n = 17*, a filter of seconds.) xe = 1
is now kept only where it gains a block, or where xe = 2 reaches 96
registers (product-cliques' case, 0.917 / 0.926).

### Change 6 — the wide launch budget back to 2^37 (`CAND_PER_LAUNCH_WIDE`)

Re-swept after Change 4 (Rule 1's corollary): a wide launch at 2^38 holds
a tail queue of ~27 million items (~240 MB) that streams through DRAM past
the 72 MB L2. 2^37 against 2^38, paired: **1.014 [1.012, 1.019] at A083518
n = 20*, 1.014 [1.011, 1.017] at A083519 n = 19*, 1.011 [1.005, 1.014] at
A083518 n = 21***; 2^36 reads 1.008 at n = 20*. Half the queue memory. The
narrow 2^37, re-swept at n = 19*: 2^36 1.007, 2^35 0.997, 2^38 0.982, a tie,
kept. It halves a wide launch, so the cursor key moves (`w37`) and a v1
cursor taken mid-segment at a wide filter would count launches in the wrong
unit; no v1 campaign was ever started (no checkpoint exists), so
`PREVIOUS_ENGINES` is empty.

### Round 2 result: v2 against the v1 code path, paired, the same plan and stream

The v1 arm is the same source with the mechanisms off. Same wheel, same
window, the same launch decomposition on the narrow record (the wide one's
launches are half v1's: Change 6), candidates counted exactly per arm, so
the clock ratio is the rate ratio; the absolute clocks are this session's (a desktop GPU's absolute
rate moves with ambient load; the ratio is the stable quantity).

| filter | registers / blocks v2 (v1) | device, a(n)-line/s | expected clock to a confirmed find | v2 / v1 |
|---|---|---|---|---|
| A083518 n = 17* | 75 / 6 (92 / 5) | 9.5e15 | 34 s | **1.093** [1.087, 1.096] |
| A083518 n = 18* | 72 / 6 (88 / 5) | 1.67e16 | 14 min | **1.125** [1.118, 1.131] |
| A083518 n = 19* | 72 / 6 (88 / 5) | 2.68e16 | **5.9 h** | **1.108** [1.099, 1.112] |
| A083518 n = 20* (wide) | 80 / 6 (86 / 5) | 3.97e16 | **7.1 days** | **1.101** [1.095, 1.106] |
| A083518 n = 21* (wide) | 72 / 7 (86 / 5) | 6.18e16 | 8.2 months | **1.149** [1.147, 1.153] |
| A083519 n = 16* | 75 / 6 (92 / 5) | 2.57e16 | 76 s | **1.109** [1.105, 1.115] |
| A083519 n = 17* | 72 / 6 (102 / 4) | 4.61e16 | 29 min | **1.128** [1.122, 1.131] |
| A083519 n = 18* | 72 / 6 (88 / 5) | 7.24e16 | **11.5 h** | **1.112** [1.107, 1.117] |
| A083519 n = 19* (wide) | 80 / 5 (86 / 5) | 1.15e17 | **14.0 days** | **1.108** [1.103, 1.112] |

Kernel-only and campaign-loop are one number here, as in round 1: device =
wall to 1% at both n = 19* and n = 20*, and nothing in the host path
changed. The campaign-loop A/B proper is the owner's, in the first
`[STATUS]` lines.

**The plan, re-checked against its neighbours on the v2 engine** (expected
clock, plan / neighbour): A083518 n = 19*: 192 periods 0.901 and 224 0.884
(both clamp to 179 live periods), 128 0.926. n = 20*: the narrow wheel to
47 0.946 (it read 0.977 before Change 4, which helped the wide record more),
192 periods 0.944, 224 0.961. A083519 n = 18*: 192 0.901, 128 0.900, the
wheel to 43 0.762. A083519 n = 19*: 192 0.998, the narrow wheel to 47 0.910.
**Every plan stands**; PLAN_VERSION stays p2.

**After round 2, Nsight Compute at n = 19***: LSU input requests 86% of peak,
data-pipe wavefronts 78%, ALU 69%, issue 66%, cycles 76.1M against v1's
83.8M for the same launch (1.10x under the profiler's locked clocks). The
sieve kernel 92% of the device, the tail rounds 8%.

### Measured and not taken

| idea | result | reading |
|---|---|---|
| STREAMING in-block rounds: per-warp queues, a round run on 32 items whenever its input holds 32, deepest first, ballot pushes, no block barriers, a flush at the block's end | **0.927** (90 registers, 5 blocks); 0.993 at 32 residues a block; 0.888 / 0.938 with a 6-block launch bound (80 registers) | the barriers and latency it removes were not what the rounds cost; their cost is their instructions and loads |
| warp prefix by ballots for counts under 2^2 / 2^3 / 2^4 (the shuffles count as LSU requests) | 0.979 / 0.989 / 0.990 | the shuffles were not the cost |
| the round item loop unrolled 1 / 2 (instruction-fetch stalls 9-12% in the rounds) | 0.981 / 0.976; the push loop too 0.979 | the full unroll's ILP is worth more than its code size |
| window-coordinate rounds on the narrow record | 0.827 (130 registers, 3 blocks) | as in product-cliques |
| the wide rounds' table word OR-ed unmasked | 0.9995 | the compiler already folds it |
| the wide round rows emitted word by word (register pressure at A083519 n = 19*) | 1.004 (still 90 registers before Change 4) | |
| the prologue spread over every thread, 8 per residue | 0.976 | superseded by Change 4 |
| the window tables copied into shared memory 16 bytes at a time | 1.000 | |
| TAIL ROUNDS BY PACKS: a 64-bit step per pack of three, lazy 32-bit steps, periodic masks for 3q <= 4096 | 0.982; 0.9925 with two packs a step, the loop unrolled and an all-lazy variant | the tail's first round is not arithmetic-bound (Nsight: issue 68%, L1 42%, DRAM 42% -- its queue, ~13.5 million u64 items a launch, is past the 72 MB L2) |
| block shapes on v2 at n = 19*: (16, 4) / (8, 2) / (8, 4) / (32, 2) | 0.865 / 0.890 / 0.847 / 0.955 | (16, 2) stands |
| a 7-block launch bound (shared memory caps at 6) | 0.954 | |
| the sixth block at A083519 n = 19* (queue margin 2.5 sigma: 6 blocks; 4 sigma: 5) | 1.002 / 1.002 | the occupancy curve is flat there |
| the occupancy curve on v2, n = 19* (padding ablation) | 6 → 5 blocks 0.971, 6 → 4 0.932 | a seventh block is worth ~1.5% at most |
| constants re-swept on v2 at n = 19*: BIT_SURV 0.0025 / 0.005; K2_SURV4 5e-5 / 2e-4; R2_DROP 0.35 / 0.65; TAIL_ROUND_DROP 0.5 / 0.85; tail UNROLL 8 / 2; TAIL_TPB 128; TAIL_FILL 2^20 | 1.000 / 0.960 (5 blocks); 1.000 / 0.991; 0.987 / 0.985; 0.995 / 0.993; 1.005 / 1.002; 0.999; 0.996 | flat; unchanged |

### Priced and unbuilt, best first (replaces round 1's list)

1. **A find truncates its segment** -- re-priced, lower than round 1 said.
   A launch sweeps EVERY period of the segment for its residue chunk, so
   narrowing the launches left after a find to the find's period saves only
   what a narrower window costs less: by the width curve the remaining
   launches cost 0.69 of a full one on average (a find's period uniform in
   the segment), about 16% of the find's segment. **About 10 minutes of
   A083518's a(19)* (2.8%) and 6 hours of its a(20)* (3.5%)**, under 1% at
   A083519's filters, whose segments are 0.06-0.07 medians. It needs a
   second, narrower engine for the rest of the segment and the truncation
   in the cursor and the drills, and it changes what a segment claims: the
   owner's to green-light.
2. **Carrying the over-swept line into the next filter** -- sound (the old
   filter's survivors past the find, re-tested against the one new
   condition, are exactly the new filter's there, since the new condition
   list contains the old one), but it recovers that line at the NEXT
   filter's rate on a search about 40 times longer: about **22 minutes of
   A083518's a(20)* (0.2%)**. Declined on the price.
3. **The tail's queue traffic.** The tail is ~8% of the device at every
   filter, its arithmetic is not the limit (packs above), and its first
   round reads and rewrites ~13.5 million u64 items a launch from DRAM. A
   smaller item (the in-block index does not fit 32 bits: t, s and the
   period need 40) or a deeper in-block cut (K2_SURV4 measured flat) are the
   directions; neither is priced yet.
4. **The planner's price of the wide record.** At A083518 n = 20* the wide
   53-wheel runs 0.847 of the narrow 47-wheel's candidates a second where the
   model says ~0.96; every plan still measures right, so no re-fit.

### Termination table (OPTIMIZATION.md Part 3), after round 2

A083518 n = 19*, the planned configuration, v2: the sieve kernel 92% of the
device, the tail rounds 8%.

| phase | share of the device | verdict |
|---|---|---|
| the window | ~55% | **roofline**: the shared-memory data path at its ideal wavefronts, 24 bytes a lane a prime, LSU issue 86% of peak; the representation hunt priced pre-shifted tables (32 copies, ~75 KB a block), CRT pairs (product-cliques: 1.007 / 1.027), quad loads (data-path bound) and register-resident patterns (ALU 3x the loads they replace) |
| in-block rounds | ~25% | Changes 1-2 cut their instructions and loads; a test is now seven instructions and a load. Streaming without barriers 0.93-0.99, window coordinates 0.83, the occupancy curve flat above six blocks. Unsearched: a two-prime CRT round table (L1 is 28 KB at this carveout and a tripled pair table is 20 KB) |
| extraction | ~5-7% | one u32 store per survivor-word (Change 2); ballots 0.98-0.99 |
| prologue and the rest | ~6% | the offset table (Change 4); the pattern copy measured flat |
| tail rounds | ~8% | constants flat, packs 0.98-0.99; bound by its DRAM queue traffic, unpriced (item 3) |
| host, the loop off-device | 0% | device = wall |

### Battery and score (2026-10-02)

`python launch.py --selftest`: **53/53 ALL GREEN in 200 s** (51 + G21 +
G22), after the last change. `python score.py`: every gate green, **all five
fingerprints reproduced bit for bit** (SCORE 6511 / 110145145451837, S083519 31882 /
81801758003166, SCORE2L = SCORE1L 137965 / 699912790830580669, SCORE9
5957470 / 13208176851254), **SCORE 1,306,929,787** (and 1,401,656,436 one
run earlier, before Change 6, which leaves the narrow shapes alone) against
v1's 1,098,430,812. The opening shape is a single launch of a few hundredths of a
second read once, and such readings move ~10% between runs, so the 1.19-1.28x
is not a measurement of anything; the paired table above is the one that
transfers. Wide device memory at the day filters: 2.75 / 2.15 / 1.14 GiB
at A083518 n = 20* / 21* and A083519 n = 19* (v1: 2.94 / 2.34 / 1.33).

---

## Round 3 (2026-10-02) — engine v3: measured where the campaign stood

The A083518 campaign had been started on engine v2 and stood inside the
first segment of the filter for a(20), so this round measured THAT filter, on
its real terms, and not a stand-in: the wheel {5, 7, 11, 13, 17, 23, 29, 37}
× {19, 31, 43} × {47, 53, 59} (the wheel to 59 less 41) on the wide record,
160 periods, sieve to 2^16; 15,079,680 × 5,643 × 53,922 residues, 5,392,200
launches of 2^37 candidates a segment, a window of 38 primes and in-block
rounds to prime index 125. It is not the configuration round 2 profiled
(narrow, to 47), and the profile was not the same either. Method as rounds 1
and 2 — scratch harnesses through the engine API, EXACT candidates per
launch, the same launches for every arm (30 or 40 from launch 209,600 of the
live segment), an A/A arm last, the survivor count and xor compared on every
run of every arm — with one change: **the ratio is taken per round, each
arm against the reference arm of the same round, and the median of those is
reported.** Ambient load on this desktop moved whole rounds by 3–8% in this
session (one sweep's A/A arm read 0.98 with a ±4% spread on per-arm
medians); paired per round, the A/A arm reads 0.998–1.002 and the quartiles
sit within ±0.3%. Nsight Compute 2025.4.1 on one sieve launch
(`ncu --kernel-name sieve --launch-skip 2 --launch-count 1 --set full`, then
`--page raw` and `--page source --print-source sass --csv` for the
per-instruction stall samples, split into phases at the kernel's
`BAR.SYNC`s).

### Measurement 4 — the live filter on v2, before anything changed

**The launch** (CUDA, a sync after every kernel): the sieve kernel 90.5%,
the 27 tail rounds 9.4% (the nine with one lane per item 5.3%), `nebuild`
0.1%; 33–36 ms a launch, 3.8–4.0e12 candidates a second.

**The sieve kernel, by Nsight Compute.** 80 registers, 16,096 bytes of
shared memory, **five blocks per SM where the registers allow six** (16,096
+ 1,024 reserved, six times, is 102,720 against 102,400: 54 bytes).
The L1TEX data pipe at **87.2% of its peak in LSU wavefronts** — shared
loads 67.8, shared stores 4.1, global loads 9.0 — and LSU input requests at
87.4%; ALU pipe 61.7%, issue slots 56%. L1 hit rate **67.7%**, 23% of the
global-load sectors excess. Stalls over the whole kernel: memory-IO throttle
15.8%, short scoreboard 14.0%, fixed-latency wait 13.7%, not selected 13.3%,
long scoreboard 8.3%, math-pipe throttle 7.8%.

**Per phase** (share of the warp-stall samples / of the executed
instructions): the prologue 5.0 / 1.5, the window and the extraction 70.1 /
80.4, the five in-block rounds 23.5 / 18.0 (their first stall long
scoreboard, 29%: global-load latency), the push to the tail queue 1.4.

**The LSU budget of one block** (10,220 warp-instructions): the window's
`LDS.64` 7,314 (71.5%; 3 a prime a residue a warp); the rounds 1,610 (15.8%),
of them 1,048 global loads — one a test from the round patterns and 148
sixteen-byte gathers of the per-residue rows `x0r`, **27 sectors a request**;
the extraction's stores 717 (7.0%; two a survivor on the split queue entry);
the block offsets (`ne`, five 16-byte broadcasts a residue a warp, 3.8
wavefronts each) and `d2` 384; the prologue 132; `x0` 80. A load costs about
max(2 × requests, wavefronts) clocks of the SM, and that model reproduces the
87%.

**What was different from round 2's profile**, and where the round went:
the wide record's rounds ran in the window's coordinates, and their
per-residue rows were the largest table on the device (3.1 of 4.3 GiB),
the worst-coalesced load in the kernel and 3.3 KB of every block's shared
memory — the 54 bytes and more.

### Change 1 — a window prime below the window's width repeats inside it: 1.019 (`WINDOW_PERIODIC`)

The window of a sieve prime q is 160 consecutive bits of a pattern of period
q, so for q ≤ 96 the bits from 96 on are bits the window has already read.
Three words are READ (two 64-bit loads from the pairs table, not three) and
funnel-shifted by the position; word i ≥ 3 is the 32 bits at offset 32·i − q
of the words already formed: one funnel shift by a constant. The same five
shifts a prime, one shared load fewer, for **eight of the 38 window primes
here (41, 61, 67, 71, 73, 79, 83, 89)**: 114 loads a residue a warp become
106, and the registers 80 → 72. `window_plan` is the one derivation the
emitter and the gate share; the rule (2·loads − 1 ≥ ⌈q/32⌉ words read, q >
32) takes two loads off a small prime at 224 periods. **1.019** on v2 and
again on top of Change 2.

### Change 2 — the wide record's rounds on the narrow record's arithmetic: 1.052 (`ROUND_FOLD`, with `QWORD`)

A wide candidate is (offp, jj), its offset inside a period and its period,
because offp + jj·W' passes the word. But a round test only needs it modulo
a pack of primes, M < 2^31, and **offp + jj·(W' mod M)** is congruent to it
and below 2^63 + 2^8·2^31 < 2^64. So the wide rounds are the narrow record's
lazy Barrett packs (round 2, Change 1) with one multiply-add a pack; the
launch base rides the table index exactly as it does there. Retired with the
window-coordinate rounds: the `x0r` rows (device memory **4.32 → 1.40 GiB**
at the live filter), the round pattern table, the per-launch `jb2` table, and
the round slots of every block's offset rows (288 → 80 bytes a row, 3.3 KB of
shared memory). That buys the sixth block *and* the u32 queue entry the wide
record could not afford (round 2, Change 2).

| arm, against v2 at the live filter | registers / shared / blocks | paired |
|---|---|---|
| the sixth block alone (queue margin 5σ / 4σ) | 80 / 15,904 / 6 | 1.007 / 1.008 |
| the u32 queue entry alone | 80 / 18,080 / 5 | 1.017 |
| folded rounds, split queue entry | 72 / 12,768 / 7 | 1.046 [1.040, 1.050] |
| folded rounds, u32 queue entry | 72 / 14,752 / 6 | **1.052** [1.048, 1.056] |
| + Change 1 | 72 / 14,752 / 6 | **1.0725** [1.068, 1.077] (A/A 0.999) |

A folded test is about twice the instructions of a window-coordinate one
(13.5 against 7: the 64-bit pack step is four `IMAD.WIDE` a test), which is
what it trades for the rows.

### Measurement 5 — the profile moved

Nsight Compute again, on Changes 1 and 2: 72.8M cycles for the launch that
took 80.3M; LSU wavefronts 87 → **76%** of peak, LSU requests 87.4 → 84.8%,
ALU 61.7 → **69.5%**, issue slots 56 → 65%, L1 hit rate 67.7 → **78.8%**. The
stalls changed places: memory-IO throttle 15.8 → 2.8%, long scoreboard 8.3 →
2.7%, **math-pipe throttle 7.8 → 15.3%**, not selected 20.4%, dispatch 8.9%.
The kernel is no longer bound by the shared-memory data path alone; the ALU
is throttling beside it. By differential ablation on that engine (the window
formed twice at a runtime-zero offset, stream identical: 0.638; the rounds'
input count times a runtime zero: 1.396; the extraction's too: 1.526): **the
window 57% of a launch, the in-block rounds about 19, the tail 9, the
extraction 6, the rest 9.**

### Change 3 — the first tail rounds generated, with literal primes: 1.020 (`TAIL_LITERAL`)

Nsight Compute on the first tail round (`--kernel-name tailround1`): 426 µs,
312 million warp-instructions for 13.65 million items against 17 primes —
**43 instructions and three gathers a test** (the prime and its 64-bit magic,
its period row, its mask), issue slots 67% busy, DRAM 45%. The generic test
is right for the deep rounds, a few thousand items against hundreds of
primes; the first nine here hold 13.6 million items down to 0.74 million
against 17 to 51 primes each. Those rounds are now generated per engine:
lazy packs (M < 2^30, the launch base mod M added to the pack remainder from
a per-launch table, below 3M < 2^32), a lazy 32-bit step and one bit from a
table stored twice over per prime, and **one shared atomic per warp** for the
push (a ballot prefix) where the generic round takes one per survivor. A
round is generated while it expects 2^19 items and holds at most 64 primes.
Four rounds 1.011, **nine 1.020** [1.019, 1.023]; the rounds' own time 1.79 →
1.02 ms of a launch.

### Change 4 — a periodic prime's three words in one 16-byte load: 1.008 (`WINDOW_QUAD`)

Entry e of such a prime's table is words e..e + 3, on a 16-byte boundary,
and the table is cut to the entries a position below 2q can reach, which
makes it *smaller* than the pairs table it replaces (14,752 → 14,552 bytes
of shared memory). One `LDS.128` for two `LDS.64`, the same wavefronts: 1.008
[1.005, 1.008] (A/A 0.999).

### Round 3 result: v3 against the v2 code path, paired, the same plan, launches and stream

The v2 arm is the same source with the four mechanisms off. The live filter
is on its real terms; the starred ones are stand-ins regenerated this
session (each the first candidate at or above the model's median for its
index, in the class 3 (mod 6), whose conditions have no prime factor under
300 — not round 2's stand-ins, so the plans and absolute rates of starred
rows are not comparable with round 2's table). Launches from the middle of
the segment after the floor's, about a second an arm, six to eight rounds.

| filter | plan | registers / blocks v3 (v2) | device memory v3 (v2), GiB | device, a(n)-line/s | candidates/s | v3 / v2 |
|---|---|---|---|---|---|---|
| **A083518 n = 20** (live) | to 59 less 41, WIDE, × 160 | 72 / 6 (80 / 5) | 1.40 (4.32) | 4.63e16 | 4.53e12 | **1.103** [1.097, 1.111] |
| A083518 n = 21* | WIDE, × 224 | 72 / 7 (72 / 7) | 0.91 (2.66) | 5.74e16 | 5.32e12 | **1.120** [1.118, 1.125] |
| A083519 n = 14* | narrow, × 160 | 72 / 5 | 0.35 | 1.05e16 | 2.98e12 | 1.044 [1.030, 1.048] |
| A083519 n = 16* | narrow, × 160 | 72 / 6 | 0.23 | 4.38e16 | 3.78e12 | 1.060 [1.056, 1.065] |
| A083519 n = 17* | narrow, × 160 | 72 / 6 | 0.23 | 5.55e16 | 4.29e12 | 1.051 [1.043, 1.058] |
| A083519 n = 18* | narrow, × 160 | 72 / 6 (72 / 6) | 0.22 | 8.90e16 | 3.97e12 | 1.051 [1.045, 1.055] |
| A083519 n = 19* | WIDE, × 160 | 72 / 6 (80 / 5) | 0.49 (1.23) | 1.45e17 | 4.38e12 | **1.108** [1.085, 1.112] |

The stream is identical on every run of every row. A083519's opening
(n = 11) is one launch of 47 million candidates and reads a tie inside ±30%.
The narrow rows gain from Changes 1, 3 and 4 only. At the live filter the
model's expected line to a confirmed find is 2.58e22, so the expected device
clock is **155 h (6.4 days) on v3 against 171 h on v2** at this session's
rates — the ratio is the stable quantity.

**After round 3, Nsight Compute at the live filter:** 71.4M cycles (v2:
80.3M), LSU wavefronts 77.7% of peak, LSU requests 82.0%, ALU 71.0%, issue
slots 66%, L1 hit rate 79.5%; 72 registers, 14,552 bytes, six blocks (shared
memory now allows six and the registers seven). The launch: the sieve kernel
91.9%, the tail 8.0% (the nine generated rounds 3.3%, the eighteen deeper
ones about 3% net of the sync each was timed with).

### The cursor: a v2 campaign resumes under v3 at its launch

v3 kept v2's plan and launch decomposition and returns the identical stream
launch for launch (compared at seven filters, the live one included, and by
the five fingerprints), so the v2 key is ACCEPTED (`PREVIOUS_ENGINES =
("v2",)`). The launcher used to drop the work cursor of any inherited key
(a rule from a lineage whose launch units had changed), which here would
have re-swept 209,513 launches — two hours — of the live segment for
nothing. It now compares the stored units (periods a segment, launches a
segment) with the engine's, keeps the launch index when they match and
re-sweeps the segment when they do not, under any key; the inherited-cursor
drill builds campaigns on checkpoints of each kind. `--status` reads the
live v2 checkpoint under v3 and reports the same cursor.

### Measured and not taken

All at the live filter, against the engine as it stood (paired; the A/A arm
0.998–1.002 unless noted).

| idea | result | reading |
|---|---|---|
| a pair's words OR-ed into the accumulator together (3.0 → 2.5 `LOP3` a prime) | **0.992** | the compiler's own interleaving of loads and shifts is worth more than the instructions |
| the live-word masks built once per thread instead of rebuilt from `nv` every pass (~45 uniform-datapath instructions and five selects a pass) | **0.977**; with the above 0.9575 | the uniform datapath is free here; five more live registers are not |
| the extraction's first survivor of a word without a loop (a predicated store, the `while` kept for the rare second bit) | **0.9825** | the divergent loop is cheaper than the peeled form the compiler makes of it. (A variant storing to a per-lane sink ran 0.973 and returned a wrong stream: not a measurement.) |
| primes 97–113 from one 16-byte load of a table with an entry every sixteen bits (the fourth word part read, part derived) | 0.994, stream identical, +584 bytes of shared | three more ALU instructions a prime outweigh two loads once the ALU throttles |
| the block offsets: one 16-byte load a residue in place of five (timing-only ablation, wrong positions, same kill rates) | 1.003 | every `ne` optimization (bytes for u16, a global broadcast, `d2` in the row) is priced at under 0.4% |
| window depth 35 / 41 / 44 primes (38 planned); BIT_SURV 0.0045 | 0.990 / 0.982 / 0.979; 0.989 | stands |
| K2_SURV4 2e-4 / 5e-5 / 2e-5 / 1e-5 (1e-4 planned), before Change 3; 4e-4 / 2e-4 / 5e-5 after it | 0.984 / 1.001 / 0.979 / 0.938; 0.976 / 0.994 / 0.993 | stands; cheaper tail tests did not move the boundary |
| R2_DROP 0.35 / 0.65 | 0.983 / 0.987 | stands |
| TAIL_ROUND_DROP 0.5 / 0.85 before Change 3; 0.5 / 0.8 after | 0.993 / 0.995; 0.992 / 0.991 | stands |
| the deep tail rounds fewer and longer (survival to 0.5 / 0.3 / 0.15 / 0.05 / 0 of the round's start once the queue is under TAIL_FILL) | 0.9975 / 0.997 / 0.989 / 0.973 / 0.940 | their cost is not the launches |
| TAIL_FILL and the generated rounds' threshold at 2^17 items | 1.005 [1.001, 1.007] | a tie; not taken |
| block shapes on v3: xe 1 / spb 32 / spb 8 / xe 4 | 0.981 / 0.965 (4 blocks) / 0.950 (7 blocks) / 0.915 (with the two rejects above) | (16, 2) stands; a seventh block is not worth a shape |
| queue margin 4σ | 1.000 | 6σ kept |
| window width 128 / 192 / 224, candidates a second against 160 | 0.920 / 1.022 / 1.043 on the shape the table takes at 224, (8, 1) at 7 blocks; **1.067 on (16, 2)** and 1.060 on (16, 1), 5 blocks | see "Priced and unbuilt" 1 |

### Priced and unbuilt, best first (replaces round 2's list)

1. **The planner's width curve and the 224-period block shape are stale on
   v3.** With a small prime's loads no longer growing with the window, 224
   periods on (16, 2) runs 1.067 of 160 in candidates a second at the live
   filter, where CREL_WIDTH says 1.002 and BLOCK_SHAPES_BY_NW's row takes a
   shape that reads 1.043. On the expected clock it is a tie there (the
   segment is 1.40× as long: 2.73e22 of expected line against 2.58e22, so
   0.992 of the clock), and a plan change would discard the live segment's
   209,513 launches, so the plan stays p2. The curve and row 7 are owed a
   re-fit when a filter is next planned at a longer search — where a longer
   segment costs less, it is worth up to 6%.
2. **A find truncates its segment** — unchanged from round 2: about 3% of
   the day filters, and the owner's to green-light.
3. **The in-block rounds' pack step.** A folded or narrow test spends about
   four of its 13.5 instructions on the 64-bit step of its pack (26
   `IMAD.WIDE` an item in round 1). The rounds are 19% of a launch.
   Unsearched: the representation hunt on that step (the offset as its two
   32-bit halves, so that a pack is two 32-bit steps and a multiply).
4. **The deep tail rounds** (eighteen kernels, about 3% of a launch):
   merging them measured negative; generating them needs literal kernels
   with several lanes per item. Unpriced.
5. **The planner's price of the wide record** (CREL_WIDE 0.91) was measured
   on the window-coordinate rounds; the folded rounds changed what the wide
   record costs. Every plan measured still stands, so no re-fit.

### Termination table (OPTIMIZATION.md Part 3), after round 3

The live filter, A083518 n = 20, v3: the sieve kernel 92% of the device, the
tail 8%.

| phase | share of a launch | verdict |
|---|---|---|
| the window | ~57% | LSU requests 82% and wavefronts 78% of peak, with the ALU at 71% and its throttle the first stall. Changes 1 and 4 took what the pattern's period gives (one load in place of three for a prime up to 96); the next step of that idea measured 0.994 and two instruction diets 0.992 and 0.977; the width is a tie on the clock (item 1) |
| in-block rounds | ~19% | Change 2; R2_DROP and K2_SURV4 flat on the new rounds. Unsearched: the pack step (item 3) |
| tail rounds | 8% | Change 3 on the nine rounds that hold the items; the deep ones flat in their constants and negative merged |
| extraction | ~6% | the peeled first bit 0.98; one store a survivor since Change 2 |
| prologue, reservation, block offsets | ~9% | the offsets priced at under 0.4%; the rest unsearched and under 5% each |
| host, the loop off-device | 0% | nothing in the host path changed |

### Battery and score (2026-10-02, engine v3)

`python launch.py --selftest`: **54/54 ALL GREEN in 188 s** on the finished
tree (53 + the inherited-cursor drill; G14, G20, G21 and G22 extended).
`python score.py`: every gate green, **all five fingerprints reproduced bit
for bit** (SCORE 6511 / 110145145451837, S083519 31882 / 81801758003166,
SCORE2L = SCORE1L 137965 / 699912790830580669, SCORE9 5957470 /
13208176851254), **SCORE 1,334,560,664** on the finished tree (1,350,704,201
one run earlier: the opening shape is a single launch read once, as before)
in 2 min 21 s.

Three things for whoever works here next. **The first battery after a
kernel change compiles every kernel** and ran 353 s, over the five-minute
cap; run the engine gates in two halves first (a scratch runner over
`plus2_gpu.GATES`) and the battery after, on a warm cache. **The working
tree's files are CRLF** and a patch script that matches multi-line strings
must normalise them. **Take ratios per round**, not between per-arm medians
(above).

## The campaigns (2026-10-02), and the pause

The owner ran both families on 2026-10-02: A083518 on engine v2 from 00:59
to 09:22 (a(14)–a(19), then 1.96 h into the filter for a(20)) and A083519
on engine v3 from 11:29 to 18:21 (a(11)–a(18), then 25 min into the filter
for a(19)). RESULTS.md has every find, every leg and the census. What the
campaigns measured that the harnesses had not:

* **The campaign loop runs at the engine's rate on A083518.** Its filter for
  a(20) ran at 4.1e16 a(n)-line/s on v2 against the stand-in price of 4.0e16
  (and v3's 4.6e16 measured at that real filter in round 3); the a(19) leg
  ran at 0.84× its price with the segment's over-sweep and the verification
  inside the leg. Nothing host-side binds: the pool sat at one or two
  workers with no HOST-BOUND fragment.
* **A083519 ran at about 0.67× its v3 stand-in price on every filter past
  the openings** (1.9e16, 3.3e16, 5.9e16, 9.7e16 on the filters for a(16),
  a(17), a(18), a(19) against 4.4e16, 5.6e16, 8.9e16, 1.5e17), on the same
  wheels the stand-ins had planned. The GPU was shared with the desktop
  throughout. Whether that is the machine or something in the narrow plans
  at the real terms is NOT measured, and it is the first measurement a
  resume owes: a paired A/B of the planned engine on the live filter
  (n = 19, wheel to 53, wide) against the campaign's own first `[STATUS]`
  lines, both on the same stream. The project's two campaign-vs-price
  ratios (A083518 1.04, A083519 0.67) differ by more than the ambient-load
  band alone usually explains.
* **The model held.** Fourteen draws, E summing to 13.15 (mean 0.94,
  P = 0.44); every term inside the model's P90.

The project is **PAUSED** (2026-10-02). Nothing about the engine changed at
the pause; the battery and the score stand as in "Battery and score" above.

## Open

1. **Frozen shapes at the live filters.** Rule 5g owes a shape at every
   filter a campaign opens. Both campaigns now stand at wide filters with no
   frozen shape (A083518 n = 20, A083519 n = 19). A segment there is 45 h of
   device, so a shape cannot be a whole segment as the openings' are: it
   needs a launch-denominated shape (the first few hundred launches of the
   open segment), and the oracle has to know the terms the filter is built
   from. That is the next item: the finds into `FOUND`, with `open_n` and
   the offset drill taught that the oracle's frontier may stand past the
   published list (today the drill asserts they are equal, which is why the
   table was left empty at the pause).
2. **The A083519 0.67×** (above): a paired measurement at its live filter
   before any tuning there.
3. **Round 3's priced items** — the planner's width curve on v3 first.
