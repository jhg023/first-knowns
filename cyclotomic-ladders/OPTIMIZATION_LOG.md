# Optimization log — cyclotomic-ladders

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

Every attempt → measurement → kept/rejected, failures included. Read
[OPTIMIZATION.md](../OPTIMIZATION.md) and [INNOVATION.md](../INNOVATION.md)
before adding a round; CLAUDE.md 3b says where a round is measured: at the
filter whose term takes days, never at the opening.

## Round 0 — the engine as built, nothing measured (2026-10-23)

**The target of every later round (rule 3b).** A070737's a(13): the model
puts it at a median of 1.7×10²⁵ from a(12)'s own median (3.2×10²²), with
P10 1.5×10²⁴ and P90 7.7×10²⁵ — days at any rate this engine is likely to
run; a(11) and a(12) are minutes and under an hour. On A072942 the
day-long indices are 60 (median 3.4×10²⁵), 72 (1.6×10²⁶), 84 (1.8×10²⁵),
96 (3.4×10²⁵) and 90 (1.0×10²⁵); 48, 66, 78, 80 and 88 are minutes. So
the SCORE shape sits at A070737 n = 13 and the A072942 shapes at those
five indices; the openings are checked, not optimized.

**What was built.** power-ladders' engine v1 (round 7) and planner p1
taken whole: polynomial-runs' window sieve (wheel to 89 in up to three
levels, the strongest 100 sieve primes through bit-pattern windows,
in-block compaction rounds, generated tail rounds) with the device Fermat
stage, every constant as that project left it. What changed is the
mathematics the kernel is handed: the killed set of a prime q is the set
of residues whose multiplicative order modulo q is one the filter's
cyclotomic indices ask for (cyclotomic_search.killed_residues, from a
primitive root), the Fermat stage forms each value by Horner from the
cyclotomic coefficients, and the forced classes are x ≡ 0 modulo every
prime q with q − 1 dividing the index (A072942) or q ≤ n + 1 (A070737).
power-ladders' semiprime wheel and cofactor sieve were not carried: both
families here are plain lines.

**What this means for the constants.** Every planner and kernel constant —
BIT_SURV, LIT_MAX, K2_SURV4, K2_ROUND_PRIMES_MAX, PRP_Q2, the block shapes,
the queue margins, CREL_WIDTH, PB_DEFAULT, the tail-round constants — was
swept on another project's filters and is a HYPOTHESIS here. The regime
differs: a prime kills about one residue per form on average (as on the
power ladders) but up to q − 1 where q − 1 is smooth, so the wheel is
stronger than the power ladders' (the primes to 59 keep 1.6×10⁻⁷ of the
line at A070737 n = 13 and 1.9×10⁻⁹ at A072942 n = 60) and the units are
far larger (30,030 and 56,786,730 against power-ladders' 1, 6 and 10).
Nothing has been measured. In particular:

* the phase split (window / in-block rounds / tail / Fermat stage) at
  A070737 n = 13 and A072942 n = 60 is unknown;
* PRP_Q2 = 8192 was chosen where ten power forms left 10⁻⁵ of the
  candidates at 2²⁰; here thirteen cyclotomic forms leave about 2×10⁻⁶ of
  the post-wheel candidates at 2¹⁶, so the sieve depth that balances the
  tail against the Fermat stage is probably different;
* the Fermat stage's first forms are degree 1, 1, 2, 2, 4, 2 (Φ₁ to Φ₆) —
  cheaper than 2m^k − 1 at k = 4..6 — so CENSUS_FLOOR = 6 forms on the
  device may be more or fewer than pays;
* the per-index lines of A072942 start at x = 3, so their first segment
  is clipped and the planner's expected-sweep pricing from a floor of 3
  has not been checked against a measured segment time;
* the window-table budget below, and the layout it leaves the campaign
  engines on.

**The one engine rule added here, and why (2026-10-23).** The window
stage takes the strongest killers first, and on these ladders the
strongest killers are LARGE primes: a prime q with q − 1 a multiple of
the index kills every nonzero residue (199 kills a third of the line at
A072942 n = 66; 5743 is still among the hundred strongest there), so a
100-prime window holds primes to 1,300 at A070737 n = 11 and to 6,000 at
the A072942 openings. power-ladders' window primes were the smallest
hundred above the wheel and its tables 15–18 KB; here a 100-prime window
is 17.6 KB at A070737 n = 11 but 35–40 KB at A072942, and with the
in-block queues on top the sieve kernel passed the 48 KB static
shared-memory limit and did not compile at n = 66, 78, 80 and 88 (53–62
KB asked), while n = 84 and 96 compiled at 2 blocks per SM. So the
window now stops at the survival target, at LIT_MAX, or where its plain
table would pass `WINDOW_TABLE_BYTES` = 20 KB, whichever comes first —
one rule (`window_plain_bytes`) for the planner and the engine, pinned
to each other and to the built table by G18. It is a bound chosen so
that every opening compiles at the 3 blocks per SM the engine was tuned
at, not a measured optimum. What it leaves at each opening (lit = window
primes; pat = the device table; smem = the kernel's shared memory):

| opening | wheel | lit | pat (KB) | smem (KB) | blocks/SM |
|---|---|---|---|---|---|
| A070737 n = 11 | (13,17,19,23,29,31),(37,41),(43) | 100 | 17.2 | 27.5 | 3 |
| A070737 n = 12 | (17,19,23,29,31),(37,41,43),(61,73) | 100 | 17.8 | 29.3 | 3 |
| A070737 n = 13 | (23,29,31,37,43),(17,19,41,53),(61,73), pb 128 | 88 | 13.5 | 25.6 | 3 |
| A072942 n = 66 | (5,11,13,19,31),(89) | 72 | 20.6 | 30.6 | 3 |
| A072942 n = 78 | (5,11,13,19,31,37),(53) | 70 | 20.9 | 28.7 | 3 |
| A072942 n = 88 | (7,11,13,17,29),(41),(67) | 74 | 21.3 | 29.7 | 3 |
| A072942 n = 48 | (11,19,31,37),(41,61),(73) | 93 | 21.5 | 29.0 | 3 |
| A072942 n = 80 | (7,13,19,29,31),(37,61),(71) | 79 | 21.2 | 27.5 | 3 |
| A072942 n = 60 | (17,19,23,29),(37,41,43),(71,73) | 90 | 21.0 | 28.3 | 3 |
| A072942 n = 72 | (11,17,23,29,31),(41,43),(61,67) | 81 | 20.8 | 29.2 | 3 |
| A072942 n = 84 | (11,17,19,23,31),(37,41,61),(71,73) | 79 | 21.1 | 28.0 | 3 |
| A072942 n = 96 | (11,19,23,29,31),(37,41,43),(61,73) | 77 | 20.4 | 28.8 | 3 |
| A072942 n = 90 | (5,13,37,67,71),(17,23,41),(43,61,73) | 77 | 21.3 | 32.0 | 3 |

Every wheel is a SUBSET wheel (the primes it declines, 5 or 7 or 13, go to
the sieve), many are split out of size order (A070737 n = 13 puts 17 and
19 in the second level under a first level from 23), and the sieve depth
is PRP_Q2 = 8192 everywhere. Two consequences the next session must
weigh, neither measured:

* **Every campaign engine runs the PLAIN window layout.** The pairs
  table (and with it the packed x0, the per-launch offset table and the
  periodic read — power-ladders' round-7 wins) is taken only where it
  fits `PAT_BYTES_MAX` = 16 KB, i.e. a plain table under 8 KB; the
  windows here are 13–22 KB plain. A window of fewer, smaller primes
  (the plain table under 8 KB is about 45 primes at A070737 n = 11)
  would take the pairs path and lose window depth; which is faster is a
  measurement, at the day-long filters.
* **The host side is heavier than on the power ladders.** The wiring
  drill's live sizing at A070737 n = 11 (the planned engine, the Fermat
  stage on six forms) measured 12,100 survivors a second reaching the
  host at 323 µs each: 3.9 core-seconds per second, a pool of 8 at the
  2x margin. Six device forms of degree 1, 1, 2, 2, 4, 2 kill less than
  power-ladders' six forms did, and the host's first form is Phi_7
  (degree 6) at 100 digits. The Fermat stage's form count (CENSUS_FLOOR)
  and the sieve depth are the levers, measured together.
* **On A072942 the survival target is not reached inside the window**:
  the windows leave 0.4–2.5 % of the wheel's candidates (BIT_SURV is
  0.35 %), so the in-block rounds and the tail carry more than they did
  on the power ladders. The phase split will say how much.

**What the next session owes first** (OPTIMIZATION.md Rule 1a, CLAUDE.md
3b, 5g): the phase split with timers at A070737 n = 13 and A072942 n = 60
on the planned engines; Nsight Compute on the sieve kernel there; a paired
A/B of PRP_Q2 (2¹¹ to 2¹⁶) and of the Fermat stage's form count; the
window width and block shape re-swept on these kill sets; then the
BENCHMARKS.md rates and the acceptance test of 5g, which is the owner's to
run.

## Round 1 — engine v2, planner p2: measured at the day-long filters (2026-10-23)

**Target (rule 3b).** A070737 n = 13 — a(13), whose median the model puts
at 1.6×10²⁵ from a(12)'s median, 10–13 days at the rates below — and
A072942's n = 60, 72, 84, 96 and 90 (15 hours to 11 days each). Every
A/B below was measured at A070737 n = 13 with the planned engine at
a(12)'s median (3.1×10²²) and, where it says so, at A072942 n = 60 and 90
at x = 3 (the first segment, where each index spends its first hours; the
n = 60 split was also taken at its Q1, 1.1×10²⁵, and did not differ). The
openings were checked, not optimized (the 5g table at the end). Rates are
x/s on both entries, medians over three interleaved rounds of eight
launches each after one unpipelined launch, every arm's survivor stream
compared exactly on every round over the periods every arm covers, with
[min, max] of the per-round ratios; an A/A control arm read 0.99–1.00 at
n = 13 and 0.96–1.03 at n = 60, so a ratio inside 3% at n = 60 is noise.

**The harnesses** (session scratchpad, not committed — CLAUDE.md rule 9),
so the next person can rewrite them in ten minutes: `prof.py` (the planned
campaign engine at a filter, CUDA events around every kernel a launch
enqueues — the sieve, each tail round, each Fermat form, nebuild — and the
wall clock, checked to sum); `ncu_target.py` (the same engine, four
launches, a `KEY=VAL,eng.kw=VAL` spec applied to the build, for `ncu.bat
--kernel-name sieve --launch-skip 2 --launch-count 1 --set full`), with
`rawpick.py` (the pipes, stalls and occupancy by metric name from `--page
raw --csv`) and `sass_census.py` (`--page source --print-source sass
--csv` split at every `BAR.SYNC`, opcodes counted by full name, weighted
by executions); `ab.py` (one engine per arm, module constants set for the
build and restored, `eng.` keywords to GpuEngine, the launch decomposition
pinned across arms — `eng.tchunk`, with Q3_MAX raised so the tail-queue
guard does not move it — arms swept round by round from the same period,
streams compared below the common window); `freeze.py` (every score.py
shape's fingerprint, rate and decomposition); `rates.py` (the 5g table);
`survcurve.py` (the window's survival and table bytes by depth);
`tailinfo.py` (items and tests per tail round from the survival curve).

### The baseline, measured (engine v1, planner p1)

| filter | x/s | candidates/s | ms/launch | sieve kernel | generated tail | generic tail | Fermat stage | to the host |
|---|---|---|---|---|---|---|---|---|
| A070737 n = 13 at 3.1×10²² | 1.38×10¹⁹ | 1.15×10¹² | 119 | 78.3% | 14.1% | 2.3% | 5.4% | 1,660/s |
| A070737 n = 12 at 3.6×10¹⁹ | 7.2×10¹⁸ | 9.0×10¹¹ | 76 | 68.2% | 19.1% | 4.2% | 8.6% | 4,230/s |
| A070737 n = 11 at 1.35×10¹⁶ | 5.6×10¹⁷ | 1.08×10¹² | 64 | 68.3% | 17.3% | 8.9% | 5.7% | 12,570/s |
| A072942 n = 60 at 3 and at 1.1×10²⁵ | 4.47×10²⁰ | 7.5×10¹¹ | 91 | 58.6% | 21.0% | 6.6% | 13.9% | 2,570–3,730/s |

The device time was 99.8% of the wall clock everywhere (the harness runs
no host classification; the campaign loop's wall clock is the owner's
acceptance test, owed). Every campaign engine ran the PLAIN aligned window
(the pairs table did not fit PAT_BYTES_MAX), 168 registers, 3 blocks per
SM — registers and shared memory both at the limit — and A072942 n = 60
had been cut to 4 second-level residues per block by the starve guard.

**Nsight Compute on the v1 sieve kernel at n = 13** (111.5 ms under the
profiler): ALU pipe 84.8% of peak, LSU 72.8%, issue slots 58%, IPC 2.33,
occupancy 25% (12 warps), 1.07 eligible warps a scheduler, stalls led by
`wait` (1.00) and `not_selected` (0.83). Split at the barriers, the window
loop was 84.7% of the executed instructions and 77% of the samples; per
prime per window (128 candidates): 3.0 `LDS.64`, **5.1 `SEL`**, 5.2
`LOP3` (the two OR-accumulations the compiler already fuses into one
three-input `LOP3`, plus the select bit, the shift mask and the address
mask), 4.0 `SHF.R.W`, 1.2 `IADD3`, 1.0 `SHF.R.U32.HI` — 19.4 instructions,
of which the five selects of the aligned plain read are 26%. The in-block
rounds were 9.7% + 3.1% (FMA pipe 50% of their instructions: the Barrett
products). The prologue — sixteen threads computing 88 block offsets
serially while the block waited — was 2.2% of the instructions and 7.5% of
the stall samples.

### What was built

* **WINDOW_HALF: the window pattern holds one period** (`window_patterns`,
  `window_plain_bytes`, the emitters and `window_words`). The position
  r = x0 + ne + bw lies in [0, 2Q), and the inherited table stored the
  pattern over [0, 2Q + window + margin); here the window primes are large
  (to 1,300 at n = 13, to 6,000 at the A072942 openings), so 2Q was most of
  the table and the table decided the layout. Now the pattern covers
  [0, Q + window + margin) and the kernel reduces the position with ONE
  unsigned min, `r = min(r0, r0 - Q)` (exact: r0 ≥ Q gives r0 − Q < r0,
  r0 < Q wraps past 2³² − Q). The pairs table then fits at every filter
  (9.3 KB at n = 13, 22.8 KB at n = 60), and with it the packed x0/ne
  (NEPACK — 96 registers, from 168), the per-launch offset table
  (PRE_TABLE — the prologue gone) and the periodic quads for the small
  primes. G14 reads the kernel's window through the reduction and checks
  it against the plain pattern at r mod Q; G9 pins the stream; the
  window-coordinate rounds (the A/B arm) keep their two-period pattern,
  which G22 found when the first cut halved theirs too.
* **NEPACK and PRE_TABLE on every layout**, not only the pairs table (the
  plain aligned read now takes the packed halves through `_nepack_lines`).
* **WINDOW_QUAD_ALL off**: every group on quads is 24.4 KB at n = 13, a
  block lost and half the residues a block.
* **PRP_BY_DEGREE**: the Fermat stage tests its six forms by degree (a
  stable sort), so Phi_6 (degree 2) comes before Phi_5 (degree 4) on both
  families — the same conjunction, Codex's experiment D.
* **TAIL_LITERAL_LAST**: the last tail round is generated too, its
  survivors pushed to the survivor buffer with one global atomic per warp;
  the inherited rule left the round ending at the last prime generic, and
  here it is the biggest round of the tail.
* **The constants re-swept** (below): BIT_SURV 0.0035 → 0.0065,
  WINDOW_TABLE_BYTES 20 KB → 12 KB of the halved pattern, PAT_BYTES_MAX
  16 KB → 24 KB, CREL_WIDTH re-measured (160 periods 1.06 over 128; the
  planner now takes 160 at A070737 n = 12 and 13).
* **score.py**: the campaign shapes are 16 launches at a PINNED launch
  decomposition and width (SHAPE_TCHUNK: tchunk, nu, pb, frozen beside the
  fingerprint), the complete workload CYL-008 asks for; a whole third-level
  residue was 115 launches at n = 13 and 177 at A072942 n = 96. The v1
  fingerprints of the same shapes (where the plan did not move) are
  reproduced by v2; the v1 readings are in BENCHMARKS.md.

### The measurements, in order

Ratios are against the first arm of each table unless said otherwise.
`n = 13` is A070737 at 3.1×10²²; `n = 60` and `n = 90` are A072942 at
x = 3. "Blocks" are blocks per SM.

**1. The layout (n = 13, 128 periods, 88 window primes).** The reference
arm here is the plain aligned read WITH the packed x0 and the offset table
(the decoupling above), which alone reads 1.05 over v1's 1.38×10¹⁹.

| arm | registers, blocks | table | ratio |
|---|---|---|---|
| plain aligned, two-period pattern (NEPACK + PRE_TABLE) | 96, 4 | 13.8 KB | 1.000 (1.44×10¹⁹) |
| halved pattern, pairs, quads on every group | 96, 3 (spb 8) | 24.4 KB | 0.982 [0.973, 0.990] |
| **halved pattern, pairs, periodic quads** | **96, 4** | **14.3 KB** | **1.139 [1.129, 1.144]** |
| halved pattern, pairs, no quads | 96, 4 | 14.5 KB | 1.133 [1.124, 1.133] |
| halved pattern, plain aligned | 96, 5 | 9.2 KB | 0.902 [0.892, 0.908] |

So 1.19 over v1 from the layout alone (1.64×10¹⁹). The reduction costs
about 10% on the plain read (two instructions on a loop the selects had
left ALU-bound) and nothing on the pairs read, where it buys the layout.
The two-period pattern ON the pairs table, which now fits at n = 13
(14.6 KB, 3 blocks): 0.972 [0.965, 0.981] against the halved one.

**2. The width (`CREL_WIDTH`), on the pairs layout.** n = 13 (88 primes,
against 128 periods): 160 **1.058** [1.029, 1.060]; 192 (the narrow record
clamps it to 178 live periods, xe 1, 3 blocks) 1.029; 8 residues a block at
128 periods (5 blocks) 0.982. n = 60 (90 primes, against 256): 128 0.930,
160 0.986, 192 0.968, 224 0.990, 256 1.000; the A/A arm 1.004 [0.958,
1.028]. Three 64-bit loads serve five words as well as four, which is the
step to 160 at both filters; past it the curve is flat within the noise.
The wide record at n = 13: 224 periods **0.927** (32.6 KB, 3 blocks), 256
periods **1.021** [1.007, 1.028] — declined: a 1.6x longer coverage unit
for 2%, under CLAUDE.md 5j (an expected half-segment of over-sweep grows
from 1.5% to 2.5% of the median search, hours against hours).

**3. The window depth (`BIT_SURV`), forced per arm.** n = 13 at 160
periods: lit 48 0.921, 56 0.917, **64 1.000**, 76 0.995, 88 0.976, 100
0.878 (3 blocks), 112 0.828; n = 60 at 256 periods: lit 40 0.867, 52
0.877, 64 1.000, 76 0.999, 90 1.024 (noisy). A window prime here kills
2–3% of what is left for the same three loads and ten ALU instructions a
window as a prime that kills a third, while an in-block round test is
about eleven instructions per SURVIVING candidate — so the window should
stop where the round test is the cheaper one, well above 0.35%. 0.0065 is
64 primes at n = 13 (surv 6.5×10⁻³) and 87 at n = 60 (6.4×10⁻³), where
both curves are flat.

**4. The table budgets (n = 60, 256 periods).** Against the halved plain
read at 100 window primes (the inherited 20 KB budget on the halved table
admitted them): pairs at 68 primes (WINDOW_TABLE_BYTES 8 KB) 1.044; pairs
at 90 primes (12 KB, PAT_BYTES_MAX 24 KB) **1.052**; pairs at 100 primes
(32 KB tables, 2 residues a block) 1.005; the two-period plain read at 90
primes (v1's layout with the packed x0) 1.002. So WINDOW_TABLE_BYTES =
12 KB of the halved pattern and PAT_BYTES_MAX = 24 KB: the pairs table of
every opening's window fits (G18).

**5. The in-block rounds' depth (`K2_ROUND_PRIMES_MAX`).** n = 13: 48
0.989, 32 0.970, 96 0.948, 128 0.814; n = 60: 48 0.942, 96 0.939 (A/A
0.994). 64 stays. Deeper in-block rounds lose far more than their tests
cost: the round code is unrolled per prime, and `no_instruction` is
already 0.68 of the sieve kernel's stall cycles.

**6. The rounds in the window's coordinates** (ROUND_WINDOW_NARROW, an
inherited A/B arm): 0.963 [0.948, 0.968] at 16 residues a block (the rows
cost a block), 0.981 at 8 residues and 5 blocks. Declined again.

**7. The tail round length (`TAIL_ROUND_DROP`), n = 13:** 0.6 0.979, 0.8
0.981, 0.5 0.946. 0.7 stays.

**8. The sieve depth (`PRP_Q2`).** The cost model said a shallower sieve
should pay — the last tail rounds spend more per item than the Fermat
test they save (134 primes at about 15 instructions a test against 6.7% of
a Phi_1 test at about 10,000). Measured, with the stream check off (the
host receives more census values at a shallower depth): n = 13: 6144
0.975, 4096 0.941, 3072 0.883, 2048 0.753, 12288 0.992, 16384 0.979;
n = 90: 6144 0.939, 12288 0.988, 16384 1.018 [1.009, 1.019]. 8192 stays
at both — the model mispredicted (OPTIMIZATION.md Rule 2); the host's
stream at 4096 would also have been 1.7x the values a second.

**9. CRT-combined in-block round tables** (K2_GROUP_MAX4 2²⁰, 2²¹, 2²²:
pairs of primes to one table of 2q₁q₂ bits, tripled for the lazy
reduction, 24 MB in L2): **0.356 / 0.303 / 0.299**. The L2 gather per test
costs far more than the multiply it removes. Declined.

**10. The Fermat stage by degree** (PRP_BY_DEGREE): n = 13 **1.009**
[1.001, 1.015], n = 90 **1.013** [1.000, 1.022]. Shipped: exact, same set.

**11. The last tail round generated** (TAIL_LITERAL_LAST): n = 13
**1.031** [1.016, 1.031], n = 90 **1.072** [1.055, 1.078], n = 60
**1.048** [1.032, 1.069]. Shipped.

### Where it stands

| filter | v1 x/s | v2 x/s | ratio | ms/launch | sieve kernel | generated tail | Fermat stage | to the host |
|---|---|---|---|---|---|---|---|---|
| A070737 n = 13 at 3.1×10²² | 1.38×10¹⁹ | **1.80×10¹⁹** | **1.31** | 45.7 | 66.2% | 25.5% | 8.1% | 2,080/s |
| A072942 n = 60 at 3 | 4.47×10²⁰ | **5.5–6.1×10²⁰** | **1.23–1.37** | 72–74 | 51.6% | 30.4% | 17.9% | 4,560/s |

(The n = 60 readings in one afternoon spanned 10%, which is ambient; the
paired ratios above are the record.) The device is still 99.8% of the
wall clock in the harness. At n = 13 the window loop is now 43% of the
device, the per-candidate route (in-block rounds 21%, tail 25%) 46%, the
Fermat stage 8%. `python score.py` on the result: exit 0, 30 gates green,
every frozen fingerprint reproduced, **SCORE 16,558,034,426,419** (the
n = 13 shape at 1.66×10¹⁹ x/s; BENCHMARKS.md has every shape). That first
battery after the kernel change took about nine minutes, compiling every
configuration into the kernel cache; a warm one is the usual two to three.

**Nsight Compute on the v2 sieve kernel at n = 13** (64 window primes,
160 periods, 36.7 ms under the profiler): ALU 65.8%, LSU 74.4%, FMA
12.4%, IPC 2.37, 16 warps a SM (4 blocks: 96 registers would allow 5,
22.5 KB of shared memory allows 4), 1.19 eligible warps a scheduler;
stalls `wait` 1.28, `not_selected` 1.01, `math_pipe_throttle` 0.80,
`no_instruction` 0.68, `dispatch` 0.62, `short_scoreboard` 0.57. The
window loop is 66.5% of the executed instructions, **17 per prime per
window of 160 candidates** (0.106 a candidate, from 0.152): 5.0
`SHF.R.W`, 3.5 `LOP3`, 3.0 `LDS.64`, 2.1 `IADD3`, 1.1 `IMNMX.U32`, 1.1
`IMAD.HI.U32`, 0.55 `SHF.R.U32.HI`. Neither pipe is saturated; the loop
is latency- and issue-bound at 16 warps. The in-block rounds are 19.0% +
12.9% of the kernel at **10.6 instructions a prime-test** (2.1
`IMAD.WIDE.U32` for the pack reductions and the offset rebuild, 1.4
`IMAD`, 1.2 `IADD3`, 1.0 each of `SHF`, `IMAD.HI`, `LDG`, `SHF.R.W`,
0.7 `LOP3`). A generated tail round (round 2, 1.5 ms): 48 registers, 80%
occupancy, IPC 2.45, ALU 50%, LSU 57%, FMA 26%, the first stall
`math_pipe_throttle` (3.77) then `not_selected` (3.35) — the 64-bit
Barrett products on the heavy multiply pipe; L1 hit rate 96%.

### The termination table (OPTIMIZATION.md Part 3), A070737 n = 13

| phase | share of the device | verdict |
|---|---|---|
| sieve kernel: the window loop | ~43% | 17 instructions a prime-window, each accounted for: 5 funnel shifts (one per output word, the floor of the 32-bit funnel), 2.5 ORs (two primes to a `LOP3`, already fused), 3 loads (three 64-bit loads for six words — five used — the pairs floor at this width), 3.5 for the position (the packed add shared by two primes, the half's extraction, the min and its subtraction) and 2 for the address. Width swept (160 best under the narrow record, wide 256 1.02 and declined under 5j), depth swept (64), table halved, layout swept, two-period pattern 0.972. **Levers left**: the 64-bit funnel (INNOVATION.md Part 1, unbuilt); quads for every group where a block is not lost (0.98 here, the block was) |
| sieve kernel: the in-block rounds | ~21% | 10.6 instructions a prime-test, the lazy Barrett packs (one 64-bit reduction per three primes, a 32-bit one per prime, a table bit); depth swept (64, 128 reads 0.81), window-coordinate rounds 0.96–0.98, CRT-paired tables 0.30–0.36. **Lever left**: none priced under 1.03 |
| generated tail rounds | ~25% | multiply-pipe-bound (`math_pipe_throttle` first), 10–15 instructions a test, the same packs; round length swept (0.7), the last round generated (1.03–1.07), depth swept (8192 at both filters, shallower 0.94–0.98, deeper 0.98–1.02) |
| Fermat stage | ~8% (18% at n = 60) | one kernel a form over the compacted queue, by degree (1.01); priced, unbuilt: Montgomery squaring (the product half is ~60% of a stage at NL = 3; a symmetric product saves a third of it: ~1.02 at n = 13, ~1.04 at n = 60) |
| nebuild, the first launch of a segment, host | < 1% | — |

**Priced, declined, or left for the owner:**

* **The wide record at 256 periods** (n = 13): 1.021 for a coverage unit
  1.6x longer; under 5j the expected over-sweep (2.5% of the median
  search) is not a small fraction of the 2% it buys. Declined.
* **A fifth block a SM** (8 residues a block, n = 13): 0.982; occupancy is
  not what binds the window loop (1.19 eligible warps, IPC 2.37).
* **CENSUS_FLOOR 6 → 7** (a seventh form on the device): the host sees
  2,000 values a second at n = 13 and 4,500 at n = 60 — about one core —
  so this is a load lever, not a rate lever, as on the power ladders.
* **Codex CYL-002** (negation-folded tables for even A072942 indices):
  the generic tail round, where the mask-or-list scan lived, is now
  generated at every campaign filter, and the generated tables' [0, 2q)
  bits are L1-resident (hit rate 96%), so the fold would buy bits nobody
  is short of for one correction per test. Not built. The subgroup
  construction of the kill sets (one gcd, one generator) changes
  construction time only; the engines build in 0.5–2 s. Not built.
* **Codex CYL-003** (known-factor-first certificates at n = 78) and
  **CYL-001** (divisor floors) change what a discovery costs and where a
  line starts (≤ 1.5×10⁻⁶ of the search), not the rate. Left to a later
  session; the ledger says so.
* **The campaign loop's wall clock** (OPTIMIZATION.md Rule 1): the
  harness's device time is 99.8% of its wall clock, but the campaign adds
  the pool, the checkpoint and the heartbeat; the acceptance test of 5g
  (each family fresh, no flags, the first `[STATUS]` lines read) is the
  owner's to run and is owed before any campaign.

### At every filter the campaigns pass (CLAUDE.md 5g)

The campaign engine (planned, Fermat stage on, segment = window) from each
filter's floor, six launches after two unpipelined (`rates.py`), one
reading each:

| family | filter | wheel | window | layout | registers, blocks | x/s | ms/launch | to the host |
|---|---|---|---|---|---|---|---|---|
| A070737 | 11 (open) | (13..31),(37,41),(43), unit 2310 | 256, 73 primes | pairs | 102, 4 | 1.02×10¹⁸ | 44 | 18,600/s |
| A070737 | 12 | (17..31),(37,41,43),(61,73), 30030 | 160, 81 | pairs | 96, 3 | 9.2×10¹⁸ | 63 | 5,100/s |
| A070737 | 13 | (23..43),(17,19,41,53),(61,73), 30030 | 160, 64 | pairs | 96, 4 | 1.79×10¹⁹ | 46 | 2,000/s |
| A072942 | 66 (open) | (5,11,13,19,31),(89), 64722 | 256, 73 | pairs | 96, 3 | 5.7×10¹⁶ | 11 | 4,700/s |
| A072942 | 78 | (5,11,13,19,31,37),(53), 3318 | 256, 73 | pairs | 96, 3 | 7.1×10¹⁵ | 99 | 3,500/s |
| A072942 | 88 | (7,11,13,17,29),(41),(67), 61410 | 160, 75 | pairs | 96, 3 | 6.7×10¹⁶ | 97 | 2,300/s |
| A072942 | 48 | (11,19,31,37),(41),(73), 46410 | 256, 77 | pairs | 120, 3 | 1.9×10¹⁷ | 45 | 38,500/s |
| A072942 | 80 | (7,13,19,29,31),(37,61),(71), 230010 | 256, 79 | pairs | 98, 3 | 8.2×10¹⁷ | 72 | 6,800/s |
| A072942 | 60 | (17,19,23,29),(37,41,43),(71,73), 56786730 | 256, 87 | pairs | 100, 3 | 6.1×10²⁰ | 72 | 4,600/s |
| A072942 | 72 | (11,17,23,29,31),(41,43),(61,67), 140100870 | 256, 81 | pairs | 96, 3 | 8.1×10²⁰ | 85 | 4,900/s |
| A072942 | 84 | (11,17,19,23,31),(37,41,61),(71,73), 3404310 | 256, 74 | pairs | 96, 3 | 3.0×10¹⁹ | 76 | 3,400/s |
| A072942 | 96 | (11,19,23,29,31),(37,41,43),(61,73), 4501770 | 256, 77 | pairs | 105, 3 | 3.8×10¹⁹ | 89 | 4,900/s |
| A072942 | 90 | (5,13,17,23,37),(41,43,61),(71,73), 272118 | 256, 62 | pairs | 92, 3 | 1.04×10¹⁹ | 62 | 2,200/s |

Every opening is on the pairs layout and compiles to 3 or 4 blocks a SM
(G18), no cliff: against the v1 readings of the same shapes the openings
moved 1.25–1.8 (n = 11 1.8, n = 12 1.28, n = 60 1.37, n = 72 1.31,
n = 84 1.27, n = 90 1.35, n = 96 1.25). The host's load is one core at
the day-long filters (2,000–5,000 values a second at ~0.3–0.5 ms) and a
few at the A072942 openings (38,500/s at n = 48 for a few seconds); the
pool is sized from a measurement at the campaign's own filter regardless.

## Round 2 — planner p3: the wheel primes above 89, measured (2026-10-24)

**Target (rule 3b).** A072942's five day-long indices — 60, 72, 84, 96
and 90 — where Codex's CYL-011
(codex-reviews/2026-10-24-long-index-followup.md) proposed exchanging a
weak small wheel prime for a strong one above the planner's `WHEEL_TOP` =
89: on these ladders a prime q kills gcd(n, q − 1) residues, so 181 kills
90 of its 181 classes at n = 90 and 193 kills 96 of 193 at n = 96, and the
planner never saw them. The owner's n = 60 hunt was paused (one segment
closed, j = 256, u = 6431) and the GPU idle while this round ran. Every
measurement below is at the campaign's own configuration (the planned
engine, Fermat stage on six forms, q2 = 8192, pb = 256, the engine's own
launch decomposition) from x = 3 (the first segment) and, for the
candidates that survived, at the model's median height.

**Verified first, on the CPU** (`check_wheels.py`): w(q, n) = gcd(n, q − 1)
for every prime to 2000 at the five indices (the engine's kill count
against Codex's formula); every proposed row's level moduli, residue
counts and the kernel's bounds (W1 < 2³², W2 < 2³², W1·W2 < 2⁶³, R2, R3 ≤
65535, R1 ≤ R1_MAX, 257 W' + q2 < 2⁶⁴); and Codex's density reductions
and period ratios, reproduced to four decimals on all nine rows. Six more
wheels were generated by the planner itself with its universe raised to
200 and 300 (`plan_top.py`: `plan(n, fam, unit, top=T)`), and measured
alongside where they differed from Codex's.

**The harnesses** (session scratchpad, not committed — CLAUDE.md rule 9):
`wheels.py` (the candidate wheels as explicit three-level lists);
`ab_wheel.py` (one campaign engine per arm, `GpuEngine(p1=list, p2=list,
p3=list)`, interleaved rounds from the same x, 10–20 launches each after
one unpipelined; the line of each launch counted from its EXACT candidate
count, since the last first-level chunk of every third-level residue is
partial; every survivor an arm emits re-derived on the CPU — in the class,
`CpuEngine.survives` at 8192, `fermat2` on the stage's six forms; the
arms' survivors per unit of line compared, which only agree at equal
heights since six Fermat tests pass as (1/ln x)⁶); `parity_wheel.py`
(EXACT coverage parity of a wheel's campaign engine against the CPU
engine at the production depth: the CPU's dense t line over 2×10⁷ t in
segment 1, each sieve survivor mapped to the one launch of the segment
that holds it — its first-level residue's chunk and its third-level
residue's chunk in `_sweep`'s order — that launch alone enqueued at the
campaign's own decomposition with the Fermat stage off and `HIT_CAP`
raised to 2²⁵, its survivors filtered to the window on the device, and
the two sets required equal); `prof_wheel.py` (CUDA events around every
kernel, device seconds per 10²⁰ x by phase); `oversweep.py` (CLAUDE.md
5j: the expected sweep to a confirmed find from the model's survival
curve, conditional on the cursor, at the plan's rate times the measured
ratio, against half a segment of over-sweep).

**The accounting trap, found again.** The first A/B at n = 72 read the
Codex wheel at **1.30** — launches × `cand_per_launch`, with the wheel's
first level 363,825 residues in chunks of 90,880, so the fifth chunk of
every third-level residue holds 305 residues and was charged a full launch
(decimal-ladders' partial-launch overcount, 2026-09-24). With the exact
count per launch the same runs read 1.06, and the survivors per unit of
line of the two arms agreed (they had not). `score.py`'s 16-launch shapes
carried the same denomination and are fixed this round (below).

### The measurements

x/s against the planned wheel, medians over three interleaved rounds of
10 launches at x = 3 (20 at n = 90 and n = 60, and at every median-height
run), [min, max] of the per-round ratios; "segment" is the new coverage
unit against the planned one; "parity" is `parity_wheel.py`'s launches
matched exactly / run; the hours are `oversweep.py`'s at the median-height
ratio from x = 3 (the expected sweep to a confirmed find at the planned
wheel is 100 h at n = 72, 295 h at n = 84, 438 h at n = 96, 31 h at
n = 60 and 497 h at n = 90).

| index | wheel (levels) | − / + primes | candidates | segment | window primes | x = 3 | median | parity | hours saved; over-sweep | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 72 | plan (11,17,23,29,31),(41,43),(61,67) | | 1 | 9.99×10²³ (0.36 h) | 81 | 1 (A/A 0.9996 [0.997, 1.001]) | 1 | 795/795 | | |
| 72 | **c72** (17,31,41,61),(11,181),(97,109) | −23,29,43,67 +97,109,181 | 0.655 | 1.00x | 82 | **1.060** [1.047, 1.075] | **1.070** [1.061, 1.073] | 863/863 | 6.5 h; 3% | **shipped** |
| 72 | p72_200 (11,17,29,31,41),(61,97),(109,181) | −23 +97,109,181 | 0.564 | 28.9x (9.3 h) | 81 | 1.111 [1.101, 1.125] | — | 836/836 | 5.3 h; 87% | declined (5j) |
| 84 | plan (11,17,19,23,31),(37,41,61),(71,73) | | 1 | 1.06×10²⁴ (10.0 h) | 74 | 1 (A/A 1.001 [0.991, 1.001]) | 1 | 572/572 | | |
| 84 | **c84** (11,17,19,31,37),(61,71),(113,127) | −23,41,73 +113,127 | 0.731 | 0.21x (2.0 h) | 80 | **1.071** [1.053, 1.072] | **1.042** [1.037, 1.043] | 509/509 | 15.8 h; 6% | **shipped** (= the planner's pick at top 200) |
| 96 | plan (11,19,23,29,31),(37,41,43),(61,73) | | 1 | 1.45×10²⁴ (10.6 h) | 77 | 1 | 1 | | | |
| 96 | **c96bal** (11,19,29,31),(37,41,61),(73,193) | −23,43 +193 | 0.640 | 0.20x (1.9 h) | 78 | **1.099** [1.084, 1.099] | **1.074** [1.071, 1.080] | 597/597 | 34.2 h; 3% | **shipped** (= the planner's pick at top 300) |
| 96 | c96aggr (19,37,41,193),(11,31,241),(61,73) | −23,29,43 +193,241 | 0.594 | 1.62x (15.9 h) | 78 | 1.086 [1.068, 1.086] | — | — | 31.7 h; 25% | declined (dominated) |
| 96 | p96_200 (11,19,29,31,37),(41,43,61),(73,193) | −23 +193 | 0.550 | 8.4x (81.6 h) | 77 | 1.096 [1.077, 1.103] | — | — | −0.5 h | declined (5j) |
| 90 | plan (5,13,17,23,37),(41,43,61),(71,73) | | 1 | 3.65×10²² (1.0 h) | 62 | 1 (A/A 0.9985 [0.997, 1.000]) | | | | |
| 90 | c90bal (5,13,17,37,181),(41,61),(73,271) | −23,43,71 +181,271 | 0.497 | 0.70x | 79 | **0.969** [0.965, 0.974] | — | 87/87 | −15.8 h | declined |
| 90 | c90short (5,13,37,41,61),(73,271),(181) | −17,23,43,71 +181,271 | 0.564 | 0.041x (2.5 min) | 80 | 0.967 [0.959, 0.969] | — | — | −16.5 h | declined |
| 90 | c90aggr (5,13,37,41,61),(73,541),(181,271) | −17,23,43,71 +181,271,541 | 0.470 | 22x (22 h) | 79 | 0.982 [0.966, 0.983] | — | — | −20 h | declined |
| 90 | p90_200 (5,13,17,73,151),(37,41,43),(61,181) | −23,71 +151,181 | 0.514 | 16.7x (17 h) | 78 | 0.977 [0.960, 0.977] | — | — | −20 h | declined |
| 90 | p90_300 (5,13,37,73,181),(17,41,61),(151,271), pb 224 | −23,43,71 +151,181,271 | 0.399 | 92x (91 h) | 78 | 1.001 [0.985, 1.001] | — | — | −48 h | declined |
| 60 | plan (17,19,23,29),(37,41,43),(71,73) | | 1 | 1.06×10²⁴ (0.54 h) | 87 | 1 | 1 | | | live cursor |
| 60 | **p60_200** (17,19,29,37),(41,101),(151,181) | −23,43,71,73 +101,151,181 | 0.762 | 0.54x (0.27 h) | 91 | **1.093** [1.087, 1.094] | **1.073** [1.072, 1.074] | 408/408 | 2.2 h (1.7 h from the cursor); 6% (8%) | **shipped**, the live cursor adopted (below) |
| 60 | c60bal (17,19,29,37),(41,181),(101,241) | −23,43,71,73 +101,181,241 | 0.714 | 0.86x | 91 | 1.081 [1.074, 1.082] | 1.074 [1.074, 1.075] | 466/466 | 2.2 h; 10% | second |
| 60 | c60short (17,19,37,41),(43,181),(71,73) | −23,29 +181 | 0.849 | 0.27x | 91 | 1.069 [1.068, 1.071] | 1.051 [1.047, 1.052] | 479/479 | 1.7 h; 4% | third |
| 60 | p60_300 (17,19,37,41),(101,151),(181,241) | −23,29,43,71,73 +101,151,181,241 | 0.664 | 4.5x (2.2 h) | 91 | 1.095 [1.088, 1.097] | — | — | 1.8 h; 61% | declined (5j) |

Every arm's survivors were re-derived on the CPU (0 false of 4,542 to
23,157 per arm); the n = 90 ratios were taken twice (10 and 20 launches a
round, and the profile harness with the arms reversed: 0.958–0.969 for
c90bal). A ratio at x = 3 is the campaign's first hours; the median-height
ratio is its days, and it is lower at 84 and 96 because the Fermat stage's
limb count grows with x and the stage is per survivor per x, so the sieve
kernel — where the whole gain lives — is a smaller share there.

**Where the gain is** (`prof_wheel.py`, 20 launches, device seconds per
10²⁰ x, planned → measured wheel): n = 72 sieve kernel 0.0626 → 0.0526,
generated tail 0.0418 → 0.0424, Fermat stage 0.0232 → 0.0238; n = 84
1.686 → 1.455, 1.030 → 1.089, 0.669 → 0.637; n = 96 1.225 → 1.031,
0.906 → 0.894, 0.503 → 0.450; n = 60 (p60_200) 0.0933 → 0.0836, 0.0561 →
0.0536, 0.0327 → 0.0287; **n = 90 (c90bal) 5.00 → 3.24, 2.83 → 4.27, 1.74
→ 1.60**. The tail rounds and the Fermat stage are per survivor per unit
of line, and the final predicate is wheel-independent, so a wheel cannot
move them: a 1.37–1.56x reduction in candidates buys 10–16% of the sieve
kernel's 45–52% share — the Amdahl bound CYL-011 itself stated — and at
n = 90 it buys less than it costs: 181 and 271 are the sieve's two
strongest killers there (each kills half the line), the window needs 17
more primes without them (62 → 79) and the tail behind them kills less per
round, so every surviving candidate travels further: the tail's seconds
per unit of line rise 1.5x and eat the sieve kernel's 1.5x saving.

**The planner's cost model mispredicted every one of them** (its
clock-objective ratio against the measured median-height ratio): c72
1.51 / 1.07, c84 1.28 / 1.04, c96bal 1.56 / 1.07, c90bal 1.58 / 0.97,
c60bal 1.34 / 1.07, p60_200 1.26 / 1.07. It prices the window's depth
(crel ∝ 1/lit) but neither the sieve kernel's share nor the tail behind a
wheel that holds the sieve's best killers (OPTIMIZATION.md Rule 2: the
model generates candidates and is not evidence). Raising `WHEEL_TOP`
would therefore have shipped p72_200 (1.11 on the rate, a 29x longer
segment, 87% of its saving back in over-sweep) and at n = 90 p90_300
(1.00, 92x). So the measured wheels are a **per-filter table**
(`cyclotomic_gpu.MEASURED_WHEELS`) that `plan` returns at the campaign's
own arguments; every other filter is planned as before.

**Shipped (planner p3).** `MEASURED_WHEELS` at A072942 n = 60, 72, 84
and 96 with the width each was measured at; `launch.PLAN_VERSION` = p3,
and the cursor policy ACCEPTS a p2 cursor wherever the plan did not move
(the live A070737 n = 13 cursor and the closed indices) and ADOPTS one at
a moved index (below). `score.py`: D60, D72, D84 and D96 now stand at the
measured wheels (frozen after the parity above and the CPU re-derivation
of every emitted survivor: D72 3668 / 48140159372603435368684, D84 3143 /
289269573103394776183992, D96 6383 / 235076235038982124538322, D60 5500 /
513110205094724911442778; their decompositions pinned at tchunk 105728, 90880, 48000
and 3200 — the tail-queue guard sizes a launch on these wheels at half the
candidates, since more of the wheel's candidates reach the tail), the p2
workloads kept as D60p2, D72p2, D84p2 and D96p2 with their p2 fingerprints
(one engine reproducing both wheels' streams over the same line), and
every launch-denominated shape's rate now counts the EXACT candidates of
its launches (`launch_candidates`; a partial chunk is no longer charged a
full launch). `python score.py`: exit 0, 30 gates green, every fingerprint
reproduced, and `python launch.py --selftest` ALL GREEN — the readings are
in BENCHMARKS.md.

**n = 60: the live cursor, adopted (the owner's word, 2026-10-24).**
p60_200 measured 1.073–1.093 with a segment half as long, and from the
live cursor (x = 1.0589×10²⁴, one segment closed under p2, 6,431 launches
into the second) saves 1.7 h of an expected 31 h to a confirmed find at 8%
over-sweep. The campaign there had a cursor denominated in the p2 wheel's
periods, which the launcher refuses by design (CLAUDE.md 5d); it now
ADOPTS it (`Campaign.adopt_cursor`; the p2 key sits in the policy's
`adopt` at every moved index): the one claim that carries over is the
swept boundary k, re-denominated onto W = 2.2275×10²¹ with flooring —
period 475, 8.1×10²⁰ of swept line given back (1.5 s) — and the work
cursor inside the old segment is dropped, so the segment at 475 is swept
from its start in the new wheel's launches (the old segment's 6,431
launches, about 8 minutes of device time, are swept again; the census
they counted is counted once more, as power-ladders' A229630 adoption
was); finds, pending values, rungs, census, near and survivor counts are
carried. `--status` says what the next start will do with such a cursor.
Drilled in the selftest on a synthetic p2 cursor at n = 60 (one segment
closed, a partial second; and a cursor still under one period) and checked
on a copy of the live checkpoint: period 475, launch 0, 1.0580×10²⁴ swept.
The owner's next start of n = 60 is the real adoption; nothing here
started it.

**Priced and declined this round.** Every n = 90 exchange (above). The
aggressive 96 and 90 rows and the planner's long-segment picks, under
CLAUDE.md 5j. A shorter width for the shipped wheels (pb 128: the
planner's own model prices it 10–15% under 256, and the segments are
already 2 h). **Codex CYL-012** (enumerating a stronger wheel's survivors
inside bounded intervals): not pursued — the profiles above put the sieve
kernel at 45–52% of the device and a wheel's entire density gain at
10–16% of it, while the other half (the tail and the Fermat stage) is per
survivor per unit of line and out of any wheel's reach, so no wheel-side
representation, however it completes its intervals, approaches the
6.5–11x the hardest medians would need; what that needs is a cheaper
survivor path, which is another round's question. **The launch size on
the measured wheels** (the Q3 guard halves `tchunk` because more
candidates reach the tail): a re-sweep of `Q3_MAX` is the one constant
not re-swept after this structural change (rule 3a); launch size measured
1–2% elsewhere in this repository.

## Pause (2026-10-25): what the campaigns measured

The owner ran both campaigns 2026-10-23 to 10-25 (RESULTS.md: eight
terms), and the project was paused on 2026-10-25. What those runs
measured, for whoever resumes:

* **The adoption ran as drilled.** The n = 60 cursor, written under the
  p2 wheel (x = 1.0589×10²⁴, one segment closed, 6,431 launches into the
  second), was adopted onto p3's wheel at the owner's restart, and a(60) =
  6.687×10²⁵ came under p3 on 2026-10-25 09:13 after 31.5 h on the
  campaign's clock — an average 5.92×10²⁰ x/s over the whole line, between
  the p2 price (5.5×10²⁰) and the p3 price (6.0×10²⁰) as the line was
  split. One line swept once cannot read the 1.07–1.09 as a separate
  number; the paired A/Bs above remain the record.
* **The openings ran at their prices.** A070737's a(11) about a minute
  after the start, a(12) 35 minutes later (7.8×10¹⁸ x/s over the n = 12
  line against 9.2×10¹⁸, with the unpipelined first launch, the promotion
  and a(11)'s certificates inside the clock); A072942's five openings each
  in seconds of line.
* **The certificate route left nine values unproved** at n = 66, 78 and
  88 (Φ₁₁, Φ₂₂, Φ₃₃, Φ₆₆; Φ₃₉; Φ₁₁, Φ₂₂, Φ₄₄, Φ₈₈), as README.md said it
  might: the 67-digit Φ₅(x) and Φ₁₀(x) outside those runs did not factor
  in huntlib's budget. A certificate-cost item (Codex CYL-003), not a rate
  item; RESULTS.md names the values.
* **The coverage unit at A070737 n = 13** is one segment of 160 periods,
  4.9×10²³ of line — 7.7 h at 1.79×10¹⁹ x/s, so an expected over-sweep of
  about 4 h on a ten-day median search (1.6%, inside CLAUDE.md 5j).
* **The pause battery** (2026-10-25, no code change since round 2): SCORE
  16,162,789,126,690, 30 gates green, every fingerprint reproduced;
  `launch.py --selftest` 57/57 in 255 s — BENCHMARKS.md's third ledger
  row. The headline's 0.966 of the 10-24 reading is ambient (one reading
  against a median of three).
* **Owed to a resumer, in order:** the two batteries first (CLAUDE.md rule
  2); the `Q3_MAX` re-sweep on the measured wheels (round 2's last
  paragraph); the nine hand certificates or the CYL-003 route; and, if
  a(13) of A070737 is the target, a phase split under a live n = 13
  segment — the SCORE shape sits at that filter, but no campaign segment of
  it has closed yet.

## Priced and declined

See round 1's table and round 2's last paragraph. Candidates a reviewer may still want to price
(codex-reviews/): sharing one sieve between two A072942 indices whose
divisor sets overlap (60 and 90 share 1, 2, 3, 5, 6, 10, 15, 30; Codex's
CYL-010 puts the forced-class overlap at 1/3984 and defers it), and a
certificate route for the out-of-run cyclotomic values at n = 66, 78 and
88 cheaper than a 65–70-digit factorization (CYL-003 proves one for
Phi_13 and Phi_26 at n = 78 from the run's own factors).
